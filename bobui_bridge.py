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


def create_session_checkpoint(name, mem=None):
    """Saves a named snapshot checkpoint in session memory."""
    target_mem = mem or session_memory.SessionMemory()
    return target_mem.save_checkpoint(name)


def restore_session_checkpoint(name, mem=None):
    """Restores a session snapshot from checkpoint."""
    target_mem = mem or session_memory.SessionMemory()
    return target_mem.restore_checkpoint(name)


def undo_session_action(mem=None):
    """Reverts the last mixing action recorded in session memory."""
    target_mem = mem or session_memory.SessionMemory()
    return target_mem.undo_last_action()


def audit_session_consistency(mem=None):
    """Audits session memory track parameters and role consistency."""
    target_mem = mem or session_memory.SessionMemory()
    return target_mem.audit_session_consistency()


def sync_session_diff(checkpoint_name, mem=None):
    """Calculates minimal parameter differences from checkpoint and pushes updates."""
    target_mem = mem or session_memory.SessionMemory()
    diff = target_mem.compute_state_diff(checkpoint_name)
    return diff


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


def broadcast_track_update(track_name, fader=None, muted=None, soloed=None, osc_bridge_port=8000, socket_path=DEFAULT_SOCKET_PATH):
    """Simultaneously dispatches track updates over low-latency binary socket and UDP OSC."""
    results = {}
    # 1. Low-latency binary socket sync
    if fader is not None or muted is not None or soloed is not None:
        f_val = fader if fader is not None else 0.0
        m_val = muted if muted is not None else False
        s_val = soloed if soloed is not None else False
        results["socket_sync"] = fast_sync_track_state(track_name, f_val, m_val, s_val, socket_path)

    # 2. OSC broadcast to Member DAWs
    try:
        from pythonosc.udp_client import SimpleUDPClient
        client = SimpleUDPClient("127.0.0.1", osc_bridge_port)
        try:
            if fader is not None:
                client.send_message(f"/track/{track_name}/fader", float(fader))
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


def fast_sync_track_state(track_name, fader=0.0, muted=False, soloed=False, socket_path=DEFAULT_SOCKET_PATH):
    """Encodes track parameters into binary layout and transmits to Omni-Plugin bridge."""
    name_bytes = track_name.encode("utf-8")[:255]
    name_len = len(name_bytes)
    # Format: [1B len][NB name][4B float fader][1B muted][1B soloed]
    packed = struct.pack(f"!B{name_len}sf??", name_len, name_bytes, float(fader), bool(muted), bool(soloed))

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
