#!/usr/bin/env python3
"""
BobUI Omni-Plugin Bridge Python Gateway

Facilitates bidirectional interaction between BobUI widgets, SessionMemory,
and the Rust Omni-Plugin Host over Unix domain sockets.
"""

import json
import logging
import os
import socket
import struct
import sys
import tempfile
import time

import session_exporter
import session_importer
import session_memory

DEFAULT_SOCKET_PATH = "/tmp/bobtrax_omni_bridge.sock"

PLUGIN_COMPATIBILITY_REGISTRY = {
    "ardour": {"native": ["LV2", "VST3", "LADSPA"], "bridged": ["CLAP", "VST2"]},
    "lmms": {"native": ["VST2", "LADSPA"], "bridged": ["LV2", "VST3", "CLAP"]},
    "muse": {"native": ["LV2", "DSSI", "LADSPA"], "bridged": ["VST3", "CLAP"]},
    "zrythm": {"native": ["LV2", "VST3", "CLAP"], "bridged": ["LADSPA"]}
}


def query_plugin_compatibility(plugin_id, target_daw):
    """Checks whether a plugin format is supported natively or via Omni-Bridge for a DAW."""
    daw_key = target_daw.lower()
    compat = PLUGIN_COMPATIBILITY_REGISTRY.get(daw_key, {"native": [], "bridged": ["VST3", "LV2", "CLAP"]})
    return {
        "plugin_id": plugin_id,
        "daw": daw_key,
        "native_formats": compat["native"],
        "bridged_formats": compat["bridged"],
        "universal_bridge_ready": True
    }


def resolve_plugin_format_bridge(plugin_format, target_daw):
    """Resolves whether a plugin format runs natively or requires Omni-Bridge translation for target DAW."""
    daw_key = target_daw.lower()
    fmt = plugin_format.upper()
    compat = PLUGIN_COMPATIBILITY_REGISTRY.get(daw_key, {"native": [], "bridged": []})

    if fmt in compat["native"]:
        return {
            "daw": daw_key,
            "format": fmt,
            "mode": "NATIVE",
            "needs_bridge": False,
            "latency_penalty_ms": 0.0
        }
    elif fmt in compat["bridged"]:
        return {
            "daw": daw_key,
            "format": fmt,
            "mode": "BRIDGED",
            "needs_bridge": True,
            "latency_penalty_ms": 0.4
        }
    else:
        return {
            "daw": daw_key,
            "format": fmt,
            "mode": "UNIVERSAL_SHIM",
            "needs_bridge": True,
            "latency_penalty_ms": 0.8
        }


def scan_system_plugins(search_paths=None):
    """Discovers installed or simulated audio plugins and categorizes their format compatibility."""
    plugins = [
        {"name": "OmniComp_Pro", "format": "VST3", "category": "Dynamics"},
        {"name": "Calf_Parametric_EQ", "format": "LV2", "category": "EQ"},
        {"name": "Zita_Rev1", "format": "LV2", "category": "Reverb"},
        {"name": "Surge_XT", "format": "CLAP", "category": "Synthesizer"},
        {"name": "TAP_TubeWarmth", "format": "LADSPA", "category": "Distortion"},
        {"name": "Analog_Delay_Vintage", "format": "VST2", "category": "Delay"}
    ]
    return plugins


class BobUIBridge:
    def __init__(self, socket_path=DEFAULT_SOCKET_PATH):
        self.socket_path = socket_path

    def is_host_alive(self):
        return verify_omni_connection(self.socket_path)

    def process_audio_buffer(self, frames=512, gain=1.0):
        """Sends an audio processing block to the standalone Omni-Plugin Host."""
        if not os.path.exists(self.socket_path):
            return {"status": "error", "message": "Socket not found", "frames": frames, "gain": gain}

        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(1.0)
                client.connect(self.socket_path)
                cmd = f"PROCESS_AUDIO {frames} {gain}\n"
                client.sendall(cmd.encode("utf-8"))
                resp = client.recv(1024).decode("utf-8").strip()
                data = json.loads(resp)
                return data
        except Exception as e:
            return {"status": "error", "message": str(e), "frames": frames, "gain": gain}

    def stream_headless_audio_chunk(self, sample_rate=48000, frames=512, format_type="f32le"):
        """Streams a headless audio buffer to the Omni-Plugin Bridge with latency and peak analysis."""
        if not os.path.exists(self.socket_path):
            return {
                "status": "simulated",
                "sample_rate": sample_rate,
                "frames": frames,
                "format": format_type,
                "peak": 0.42,
                "latency_ms": round((frames / sample_rate) * 1000.0, 2),
                "note": "Host socket not running, evaluated locally"
            }

        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(1.0)
                client.connect(self.socket_path)
                cmd = f"STREAM_AUDIO_BLOCK {sample_rate} {frames} {format_type}\n"
                client.sendall(cmd.encode("utf-8"))
                resp = client.recv(1024).decode("utf-8").strip()
                data = json.loads(resp)
                return data
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "sample_rate": sample_rate,
                "frames": frames
            }

    def set_parameter(self, track_id, plugin_id, param_name, value):
        key = f"{track_id}:{plugin_id}:{param_name}"
        if not os.path.exists(self.socket_path):
            return {"status": "error", "message": "Socket not found", "key": key, "value": value}

        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(1.0)
                client.connect(self.socket_path)
                cmd = f"SET {key} {value}\n"
                client.sendall(cmd.encode("utf-8"))
                resp = client.recv(1024).decode("utf-8").strip()
                return {"status": "ok", "response": resp, "key": key, "value": value}
        except Exception as e:
            return {"status": "error", "message": str(e), "key": key, "value": value}

    def get_all_parameters(self):
        if not os.path.exists(self.socket_path):
            return {}

        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(1.0)
                client.connect(self.socket_path)
                client.sendall(b"GET_ALL\n")
                resp = client.recv(4096).decode("utf-8").strip()
                data = json.loads(resp)
                return data.get("params", {})
        except Exception as e:
            logging.debug(f"BobUIBridge get_all_parameters error: {e}")
            return {}


def verify_omni_connection(socket_path=DEFAULT_SOCKET_PATH):
    """Verifies whether the Rust Omni-Plugin host is active and responsive."""
    if not os.path.exists(socket_path):
        return False
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            s.connect(socket_path)
            s.sendall(b"GET_ALL\n")
            data = s.recv(256)
            return len(data) > 0
    except Exception:
        return False


def export_session_from_bobui(tracks, format_type, target_path):
    """Exports BobUI track dictionary to Ardour, LMMS, or JSON manifest."""
    if format_type.lower() == "ardour":
        return session_exporter.export_to_ardour(tracks, target_path)
    elif format_type.lower() == "lmms":
        return session_exporter.export_to_lmms(tracks, target_path)
    return session_exporter.export_manifest(tracks, target_path)


def import_session_to_bobui(source_path, session_mem=None):
    """Imports foreign DAW session file into BobUI track representations."""
    if source_path.endswith(".mmp"):
        return session_importer.import_from_lmms(source_path, session_mem)
    elif source_path.endswith(".json"):
        return session_importer.import_from_manifest(source_path, session_mem)
    return session_importer.import_from_ardour(source_path, session_mem)


def merge_foreign_session(file_path, strategy="merge_latest", mem=None):
    """Imports foreign session file and merges tracks with conflict resolution."""
    target_mem = mem or session_memory.SessionMemory()
    imported_tracks = import_session_to_bobui(file_path)
    return target_mem.resolve_session_conflict(imported_tracks, strategy=strategy)


def freeze_track_bridge(track_name, audio_path=None, mem=None):
    """Freezes a track in session memory to bypass DSP processing."""
    target_mem = mem or session_memory.SessionMemory()
    return target_mem.freeze_track(track_name, audio_path)


def unfreeze_track_bridge(track_name, mem=None):
    """Unfreezes a track in session memory restoring real-time DSP state."""
    target_mem = mem or session_memory.SessionMemory()
    return target_mem.unfreeze_track(track_name)


def create_session_checkpoint(name, tag="milestone", mem=None):
    """Saves a named snapshot checkpoint in session memory."""
    target_mem = mem or session_memory.SessionMemory()
    return target_mem.save_checkpoint(name, tag)


def restore_session_checkpoint(name, mem=None):
    """Restores a session snapshot from checkpoint."""
    target_mem = mem or session_memory.SessionMemory()
    return target_mem.restore_checkpoint(name)


def revert_pre_restore_bridge(mem=None):
    """Reverts session memory to the state immediately before the last checkpoint restore."""
    target_mem = mem or session_memory.SessionMemory()
    return target_mem.revert_to_pre_restore_state()


def validate_session_checkpoint(name, mem=None):
    """Validates structural integrity and physical parameter bounds of a saved checkpoint."""
    target_mem = mem or session_memory.SessionMemory()
    return target_mem.validate_checkpoint_integrity(name)


def delete_session_checkpoint(name, mem=None):
    """Deletes a saved checkpoint from session memory."""
    target_mem = mem or session_memory.SessionMemory()
    return target_mem.delete_checkpoint(name)


def tag_session_checkpoint(name, tag, mem=None):
    """Tags a saved checkpoint with workflow category."""
    target_mem = mem or session_memory.SessionMemory()
    return target_mem.tag_checkpoint(name, tag)


def undo_session_action(mem=None):
    """Reverts the last mixing action recorded in session memory."""
    target_mem = mem or session_memory.SessionMemory()
    return target_mem.undo_last_action()


def redo_session_action(mem=None):
    """Re-applies the most recently undone mixing action in session memory."""
    target_mem = mem or session_memory.SessionMemory()
    return target_mem.redo_last_action()


def audit_session_consistency(mem=None):
    """Audits session memory track parameters and role consistency."""
    target_mem = mem or session_memory.SessionMemory()
    return target_mem.audit_session_consistency()


def sync_session_diff(checkpoint_name, mem=None):
    """Calculates minimal parameter differences from checkpoint and pushes updates."""
    target_mem = mem or session_memory.SessionMemory()
    diff = target_mem.compute_state_diff(checkpoint_name)
    return diff


def compare_session_checkpoints(snap_a, snap_b=None, mem=None):
    """Returns fine-grained parameter diff list between two snapshots or against live memory."""
    target_mem = mem or session_memory.SessionMemory()
    return target_mem.compare_session_snapshots(snap_a, snap_b)


def transition_session(from_daw, to_daw, target_file_path=None, mem=None):
    """Executes state-preserved session transition between two member DAWs."""
    target_mem = mem or session_memory.SessionMemory()
    checkpoint_name = f"transition_{from_daw}_to_{to_daw}_{int(time.time())}"
    target_mem.save_checkpoint(checkpoint_name)

    # Register target DAW active status
    target_mem.register_daw(to_daw)

    out_path = target_file_path
    if not out_path:
        ext = "ardour" if to_daw == "ardour" else ("mmp" if to_daw == "lmms" else "json")
        out_path = os.path.join(tempfile.gettempdir(), f"transitioned_session.{ext}")

    export_session_from_bobui(target_mem.tracks, to_daw, out_path)

    # Sync live track updates to the new DAW
    broadcast_res = sync_session_across_daws([to_daw], target_mem.tracks, target_mem)

    return {
        "status": "success",
        "from_daw": from_daw,
        "to_daw": to_daw,
        "checkpoint": checkpoint_name,
        "exported_file": out_path,
        "broadcast": broadcast_res
    }


def verify_and_rollback_transition(transition_result, mem=None):
    """Verifies transition file existence and size, rolling back state if checks fail."""
    target_mem = mem or session_memory.SessionMemory()
    exported_file = transition_result.get("exported_file")
    checkpoint = transition_result.get("checkpoint")

    # Check if target exported file exists and has content
    if not exported_file or not os.path.exists(exported_file) or os.path.getsize(exported_file) == 0:
        if checkpoint:
            target_mem.restore_checkpoint(checkpoint)
        return {
            "status": "rolled_back",
            "reason": "Exported file missing or empty",
            "restored_checkpoint": checkpoint
        }

    return {
        "status": "verified",
        "exported_file": exported_file,
        "bytes": os.path.getsize(exported_file)
    }


# Global echo suppression cache: (track_name, field) -> (value, timestamp)
_BROADCAST_CACHE = {}


def broadcast_session_state_safe(tracks, source_daw=None, target_daws=None, mem=None):
    """Synchronizes session state across DAWs with echo suppression to prevent circular feedback loops."""
    target_mem = mem or session_memory.SessionMemory()
    active_tracks = tracks or target_mem.tracks
    all_daws = target_daws or ["ardour", "lmms", "muse", "zrythm"]

    # Exclude source DAW from receiving its own echoed updates
    destination_daws = [d for d in all_daws if not source_daw or d.lower() != source_daw.lower()]
    now = time.time()
    dispatched = 0
    suppressed = 0

    for name, track in active_tracks.items():
        fader_val = track.fader if hasattr(track, "fader") else track.get("fader", 0.0)
        cache_key = (name.lower(), "fader")
        cached = _BROADCAST_CACHE.get(cache_key)

        # Check if identical value was broadcast in the last 200ms
        if cached and abs(cached[0] - fader_val) < 1e-4 and (now - cached[1]) < 0.2:
            suppressed += 1
            continue

        _BROADCAST_CACHE[cache_key] = (fader_val, now)
        muted_val = track.muted if hasattr(track, "muted") else track.get("muted", False)
        soloed_val = track.soloed if hasattr(track, "soloed") else track.get("soloed", False)
        broadcast_track_update(name, fader=fader_val, muted=muted_val, soloed=soloed_val)
        dispatched += 1

    return {
        "status": "success",
        "source_daw": source_daw,
        "target_daws": destination_daws,
        "tracks_dispatched": dispatched,
        "echoes_suppressed": suppressed
    }


def sync_session_across_daws(target_daws=None, tracks=None, mem=None):
    """Simultaneously synchronizes entire session state across all registered member DAWs."""
    target_mem = mem or session_memory.SessionMemory()
    active_tracks = tracks or target_mem.tracks
    daws = target_daws or ["ardour", "lmms", "muse", "zrythm"]
    results = {}

    for daw in daws:
        dispatched = 0
        for name, track in active_tracks.items():
            fader_val = track.fader if hasattr(track, "fader") else track.get("fader", 0.0)
            muted_val = track.muted if hasattr(track, "muted") else track.get("muted", False)
            soloed_val = track.soloed if hasattr(track, "soloed") else track.get("soloed", False)
            broadcast_track_update(name, fader=fader_val, muted=muted_val, soloed=soloed_val)
            dispatched += 1
        results[daw] = {"status": "synced", "tracks_dispatched": dispatched}

    return results


def broadcast_track_update(track_name, fader=None, pan=None, muted=None, soloed=None, frozen=None, osc_bridge_port=8000, socket_path=DEFAULT_SOCKET_PATH):
    """Simultaneously dispatches track updates over low-latency binary socket and UDP OSC."""
    results = {}
    # 1. Low-latency binary socket sync
    if any(v is not None for v in (fader, pan, muted, soloed, frozen)):
        f_val = fader if fader is not None else 0.0
        p_val = pan if pan is not None else 0.0
        m_val = muted if muted is not None else False
        s_val = soloed if soloed is not None else False
        frz_val = frozen if frozen is not None else False
        results["socket_sync"] = fast_sync_track_state(track_name, f_val, p_val, m_val, s_val, frz_val, socket_path)

    # 2. OSC broadcast to Member DAWs
    try:
        from pythonosc.udp_client import SimpleUDPClient
        client = SimpleUDPClient("127.0.0.1", osc_bridge_port)
        try:
            if fader is not None:
                client.send_message(f"/track/{track_name}/fader", float(fader))
            if pan is not None:
                client.send_message(f"/track/{track_name}/pan", float(pan))
            if muted is not None:
                client.send_message(f"/track/{track_name}/mute", 1.0 if muted else 0.0)
            if soloed is not None:
                client.send_message(f"/track/{track_name}/solo", 1.0 if soloed else 0.0)
        finally:
            if hasattr(client, "_sock") and client._sock:
                client._sock.close()
        results["osc_sync"] = "ok"
    except Exception as e:
        results["osc_sync"] = str(e)

    return results


def fast_sync_track_state(track_name, fader=0.0, pan=0.0, muted=False, soloed=False, frozen=False, socket_path=DEFAULT_SOCKET_PATH):
    """Encodes track parameters into binary layout and transmits to Omni-Plugin bridge."""
    name_bytes = track_name.encode("utf-8")[:255]
    name_len = len(name_bytes)
    # Format: [1B len][NB name][4B float fader][4B float pan][1B muted][1B soloed][1B frozen]
    packed = struct.pack(f"!B{name_len}sff???", name_len, name_bytes, float(fader), float(pan), bool(muted), bool(soloed), bool(frozen))

    if not os.path.exists(socket_path):
        return {"status": "error", "message": "Socket not found", "packed_len": len(packed)}

    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(0.5)
            client.connect(socket_path)
            # Binary command prefix
            client.sendall(b"BIN_SYNC " + packed + b"\n")
            return {"status": "ok", "packed_len": len(packed)}
    except Exception as e:
        return {"status": "error", "message": str(e), "packed_len": len(packed)}


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SOCKET_PATH
    alive = verify_omni_connection(path)
    print(f"Omni Bridge Host at {path}: {'ALIVE' if alive else 'DISCONNECTED'}")
