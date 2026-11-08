#!/usr/bin/env python3
"""
Bobtrax Track Agent-Memory Hub

Provides persistent and in-memory tracking of active multi-DAW session state:
- Track metadata: track name, inferred role (kick, bass, vocal, master, etc.)
- Dynamic parameter values: fader levels, mute/solo states, EQ settings, compressor parameters
- Agent action history: chronological record of mixing moves performed by AI assistants
- Serialization: Saves to and restores from `.bobtrax_session_memory.json`
"""

import json
import logging
import os
import socket
import threading
import time

MEMORY_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".bobtrax_session_memory.json"))
DEFAULT_OMNI_SOCKET = "/tmp/bobtrax_omni_bridge.sock"

PLUGIN_PRESETS = {
    "Warm Tube": {
        "omni_saturation/drive": 0.45,
        "omni_saturation/warmth": 0.70,
        "omni_filter/cutoff": 14000.0
    },
    "Opto Comp": {
        "omni_compressor/threshold": -18.0,
        "omni_compressor/ratio": 3.5,
        "omni_compressor/attack": 25.0,
        "omni_compressor/release": 150.0
    },
    "Space Reverb": {
        "omni_reverb/decay": 3.2,
        "omni_reverb/damping": 0.5,
        "omni_reverb/mix": 0.28
    },
    "Clean Limiter": {
        "omni_limiter/ceiling": -0.2,
        "omni_limiter/threshold": -2.0,
        "omni_limiter/release": 50.0
    }
}


class TrackState:
    def __init__(self, name, role="generic"):
        self.name = name.lower()
        self.role = role.lower()
        self.fader = 0.0          # dB (-90 to +12)
        self.peak_level = -60.0   # dBFS
        self.muted = False
        self.soloed = False
        self.parameters = {}      # path suffix -> float value
        self.last_updated = time.time()

    def update_parameter(self, param_key, value):
        self.parameters[param_key] = float(value)
        if "fader" in param_key:
            self.fader = float(value)
        elif "meter" in param_key or "peak" in param_key:
            self.peak_level = float(value)
        self.last_updated = time.time()

    def to_dict(self):
        return {
            "name": self.name,
            "role": self.role,
            "fader": self.fader,
            "peak_level": self.peak_level,
            "muted": self.muted,
            "soloed": self.soloed,
            "parameters": self.parameters,
            "last_updated": self.last_updated
        }

    @classmethod
    def from_dict(cls, data):
        track = cls(data.get("name", "track"), data.get("role", "generic"))
        track.fader = data.get("fader", 0.0)
        track.peak_level = data.get("peak_level", -60.0)
        track.muted = data.get("muted", False)
        track.soloed = data.get("soloed", False)
        track.parameters = data.get("parameters", {})
        track.last_updated = data.get("last_updated", time.time())
        return track


class SessionMemory:
    _instance = None

    def __new__(cls, *args, **kwargs):
        # Allow creating isolated instances if custom storage_path is passed
        storage_path = kwargs.get('storage_path') or (args[0] if args else None)
        if storage_path and storage_path != MEMORY_FILE:
            instance = super(SessionMemory, cls).__new__(cls)
            instance._initialized = False
            return instance

        if not cls._instance:
            cls._instance = super(SessionMemory, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, storage_path=MEMORY_FILE):
        if getattr(self, '_initialized', False) and self.storage_path == storage_path:
            return
        self.storage_path = storage_path
        self.tracks = {}
        self.action_history = []
        self.redo_history = []
        self.checkpoints = {}
        self.omni_socket_path = DEFAULT_OMNI_SOCKET
        self.omni_synced_params = {}
        self.registered_daws = {}
        self._auto_save_thread = None
        self._auto_save_running = False
        self._load()
        self._initialized = True

    def enable_auto_save(self, interval_seconds=15.0):
        """Starts background auto-save daemon periodically persisting session memory and syncing to bridge."""
        if self._auto_save_running:
            return
        self._auto_save_running = True

        def _worker():
            while self._auto_save_running:
                time.sleep(interval_seconds)
                if not self._auto_save_running:
                    break
                try:
                    self._save()
                    self.sync_session_manifest_to_bridge()
                except Exception as e:
                    logging.debug(f"Auto-save worker error: {e}")

        self._auto_save_thread = threading.Thread(target=_worker, daemon=True)
        self._auto_save_thread.start()

    def disable_auto_save(self):
        """Stops background auto-save daemon."""
        self._auto_save_running = False
        if self._auto_save_thread:
            self._auto_save_thread = None

    def is_auto_save_active(self):
        return self._auto_save_running

    def audit_session_consistency(self):
        """Audits all tracks in session memory for fader bounds, valid roles, and parameter integrity."""
        issues = []
        for name, track in self.tracks.items():
            # Check fader bounds (-90.0 dB to +12.0 dB)
            if track.fader < -90.0 or track.fader > 12.0:
                issues.append(f"Track '{name}' fader out of bounds ({track.fader} dB). Clamping.")
                track.fader = max(-90.0, min(12.0, track.fader))
            # Verify role
            valid_roles = ["kick", "snare", "bass", "vocal", "cymbals", "synth", "master", "instrument", "generic"]
            if track.role not in valid_roles:
                new_role = self.infer_role(name)
                issues.append(f"Track '{name}' has unknown role '{track.role}'. Re-inferred to '{new_role}'.")
                track.role = new_role

        if issues:
            self._save()
        return {
            "total_tracks": len(self.tracks),
            "healthy": len(issues) == 0,
            "issues_resolved": issues
        }

    def compute_state_diff(self, checkpoint_name):
        """Calculates minimal parameter differences between active tracks and a named checkpoint."""
        if checkpoint_name not in self.checkpoints:
            return None
        snapshot = self.checkpoints[checkpoint_name]["snapshot"]
        diff = {}

        for name, track in self.tracks.items():
            if name not in snapshot:
                diff[name] = {"action": "added", "state": track.to_dict()}
                continue

            snap_track = snapshot[name]
            track_diff = {}
            if abs(track.fader - snap_track.get("fader", 0.0)) > 1e-3:
                track_diff["fader"] = track.fader
            if track.muted != snap_track.get("muted", False):
                track_diff["muted"] = track.muted
            if track.soloed != snap_track.get("soloed", False):
                track_diff["soloed"] = track.soloed

            # Parameters diff
            snap_params = snap_track.get("parameters", {})
            for p_key, p_val in track.parameters.items():
                if p_key not in snap_params or abs(p_val - snap_params[p_key]) > 1e-3:
                    if "parameters" not in track_diff:
                        track_diff["parameters"] = {}
                    track_diff["parameters"][p_key] = p_val

            if track_diff:
                diff[name] = {"action": "modified", "changes": track_diff}

        for snap_name in snapshot.keys():
            if snap_name not in self.tracks:
                diff[snap_name] = {"action": "removed"}

        return diff

    def apply_state_diff(self, diff_dict):
        """Applies an incremental patch dictionary to active session tracks."""
        applied_changes = []
        for name, change_data in diff_dict.items():
            action = change_data.get("action")
            if action == "removed":
                if name in self.tracks:
                    del self.tracks[name]
                    applied_changes.append((f"/track/{name}/removed", 1.0))
            elif action == "added":
                state = change_data.get("state", {})
                self.tracks[name] = TrackState.from_dict(state)
                applied_changes.append((f"/track/{name}/added", 1.0))
            elif action == "modified":
                changes = change_data.get("changes", {})
                track = self.get_or_create_track(name)
                if "fader" in changes:
                    track.fader = float(changes["fader"])
                    applied_changes.append((f"/track/{name}/fader", track.fader))
                if "muted" in changes:
                    track.muted = bool(changes["muted"])
                    applied_changes.append((f"/track/{name}/mute", 1.0 if track.muted else 0.0))
                if "soloed" in changes:
                    track.soloed = bool(changes["soloed"])
                    applied_changes.append((f"/track/{name}/solo", 1.0 if track.soloed else 0.0))
                for p_key, p_val in changes.get("parameters", {}).items():
                    track.update_parameter(p_key, p_val)
                    applied_changes.append((f"/track/{name}/{p_key}", float(p_val)))

        if applied_changes:
            self._save()
        return applied_changes

    def resolve_session_conflict(self, incoming_tracks, strategy="merge_latest"):
        """Merges foreign session tracks into local session memory, resolving parameter conflicts.

        Supports incoming_tracks as dict {track_name: track_obj/dict} or list of TrackState objects/dicts.

        Strategies:
        - 'merge_latest': Preserves whichever update has the newer timestamp.
        - 'overwrite_remote': Overwrites local track with foreign incoming parameters.
        - 'keep_local': Discards foreign conflicting changes and keeps local state.
        """
        if isinstance(incoming_tracks, list):
            track_items = []
            for item in incoming_tracks:
                t_name = item.name if hasattr(item, "name") else item.get("name", "unnamed")
                track_items.append((t_name, item))
        elif isinstance(incoming_tracks, dict):
            track_items = list(incoming_tracks.items())
        else:
            track_items = []

        merge_report = {
            "status": "success",
            "strategy": strategy,
            "added": [],
            "updated": [],
            "conflicts": [],
            "changes_applied": [],
            "conflicts_resolved": [],
            "merged_tracks_count": 0
        }

        for name, in_track in track_items:
            name_lower = name.lower()
            if name_lower not in self.tracks:
                # New track
                if isinstance(in_track, TrackState):
                    self.tracks[name_lower] = in_track
                else:
                    self.tracks[name_lower] = TrackState.from_dict(in_track)
                merge_report["added"].append(name_lower)
                merge_report["changes_applied"].append({
                    "track": name_lower,
                    "field": "created",
                    "old_val": None,
                    "new_val": self.tracks[name_lower].fader
                })
                continue

            local_track = self.tracks[name_lower]
            in_fader = in_track.fader if hasattr(in_track, "fader") else (in_track.get("fader", local_track.fader) if isinstance(in_track, dict) else local_track.fader)
            in_muted = in_track.muted if hasattr(in_track, "muted") else (in_track.get("muted", local_track.muted) if isinstance(in_track, dict) else local_track.muted)
            in_soloed = in_track.soloed if hasattr(in_track, "soloed") else (in_track.get("soloed", local_track.soloed) if isinstance(in_track, dict) else local_track.soloed)

            # Use last_updated as timestamp
            local_time = getattr(local_track, "last_updated", getattr(local_track, "updated_at", 0.0))
            if hasattr(in_track, "last_updated"):
                in_updated_at = in_track.last_updated
            elif hasattr(in_track, "updated_at"):
                in_updated_at = in_track.updated_at
            elif isinstance(in_track, dict):
                in_updated_at = in_track.get("last_updated", in_track.get("updated_at", 0.0))
            else:
                in_updated_at = 0.0

            has_conflict = (abs(local_track.fader - in_fader) > 1e-3 or
                            local_track.muted != in_muted or
                            local_track.soloed != in_soloed)

            if has_conflict:
                conflict_details = {
                    "track": name_lower,
                    "local": {"fader": local_track.fader, "muted": local_track.muted, "soloed": local_track.soloed, "updated_at": local_time},
                    "remote": {"fader": in_fader, "muted": in_muted, "soloed": in_soloed, "updated_at": in_updated_at}
                }
                merge_report["conflicts"].append(conflict_details)

                should_apply_remote = False
                if strategy == "overwrite_remote":
                    should_apply_remote = True
                    merge_report["conflicts_resolved"].append(f"{name_lower} -> overwritten with remote")
                elif strategy == "merge_latest":
                    if in_updated_at >= local_time:
                        should_apply_remote = True
                        merge_report["conflicts_resolved"].append(f"{name_lower} -> merged latest (remote newer)")
                    else:
                        should_apply_remote = False
                        merge_report["conflicts_resolved"].append(f"{name_lower} -> merged latest (local newer)")
                else:  # keep_local
                    should_apply_remote = False
                    merge_report["conflicts_resolved"].append(f"{name_lower} -> kept local")

                if should_apply_remote:
                    if abs(local_track.fader - in_fader) > 1e-3:
                        merge_report["changes_applied"].append({
                            "track": name_lower, "field": "fader",
                            "old_val": local_track.fader, "new_val": float(in_fader)
                        })
                        local_track.fader = float(in_fader)
                    if local_track.muted != in_muted:
                        merge_report["changes_applied"].append({
                            "track": name_lower, "field": "muted",
                            "old_val": local_track.muted, "new_val": bool(in_muted)
                        })
                        local_track.muted = bool(in_muted)
                    if local_track.soloed != in_soloed:
                        merge_report["changes_applied"].append({
                            "track": name_lower, "field": "soloed",
                            "old_val": local_track.soloed, "new_val": bool(in_soloed)
                        })
                        local_track.soloed = bool(in_soloed)

                    local_track.last_updated = max(local_time, in_updated_at, time.time())
                    merge_report["updated"].append(name_lower)

        merge_report["merged_tracks_count"] = len(self.tracks)
        self._save()
        return merge_report

    def reclassify_track_roles(self):
        """Re-evaluates role classification for every active track based on naming heuristic."""
        reclassified = {}
        for name, track in self.tracks.items():
            old_role = track.role
            new_role = self.infer_role(name)
            if old_role != new_role:
                track.role = new_role
                reclassified[name] = {"old": old_role, "new": new_role}
        if reclassified:
            self._save()
        return reclassified

    def register_daw(self, daw_name, port=None):
        """Records active DAW heartbeat and communication endpoint."""
        name = daw_name.lower()
        self.registered_daws[name] = {
            "name": name,
            "port": port,
            "last_seen": time.time(),
            "status": "connected"
        }
        self._save()
        return self.registered_daws[name]

    def get_active_daws(self, timeout=60.0):
        """Returns map of DAWs active within the timeout window."""
        now = time.time()
        return {
            k: v for k, v in self.registered_daws.items()
            if (now - v.get("last_seen", 0)) <= timeout
        }

    def infer_role(self, track_name):
        name = track_name.lower()
        if any(k in name for k in ["kick", "bd"]):
            return "kick"
        elif any(k in name for k in ["snare", "clap"]):
            return "snare"
        elif any(k in name for k in ["bass", "sub", "808"]):
            return "bass"
        elif any(k in name for k in ["vocal", "vox", "lead"]):
            return "vocal"
        elif any(k in name for k in ["hat", "cymbal", "ride", "crash"]):
            return "cymbals"
        elif any(k in name for k in ["synth", "keys", "piano", "pad"]):
            return "synth"
        elif any(k in name for k in ["master", "main", "mix"]):
            return "master"
        return "instrument"

    def get_or_create_track(self, track_name):
        track_name = track_name.lower()
        if track_name not in self.tracks:
            role = self.infer_role(track_name)
            self.tracks[track_name] = TrackState(track_name, role)
        return self.tracks[track_name]

    def record_osc_change(self, osc_path, value):
        """Parses /track/{track_name}/{parameter...} and records state."""
        parts = osc_path.strip("/").split("/")
        if len(parts) >= 3 and parts[0] == "track":
            track_name = parts[1]
            param_key = "/".join(parts[2:])
            track = self.get_or_create_track(track_name)
            track.update_parameter(param_key, value)
            self._save()

    def record_action(self, agent_name, prompt, moves):
        """Records an AI mixing action to history."""
        entry = {
            "timestamp": time.time(),
            "time_str": time.strftime("%Y-%m-%d %H:%M:%S"),
            "agent": agent_name,
            "prompt": prompt,
            "moves": moves
        }
        self.action_history.append(entry)
        # Any new action clears the forward redo history
        self.redo_history.clear()
        # Keep last 50 actions
        if len(self.action_history) > 50:
            self.action_history.pop(0)

        for path, val in moves:
            self.record_osc_change(path, val)

        self._save()

    def get_track_list(self):
        return list(self.tracks.keys())

    def set_fader(self, track_name, value):
        track = self.get_or_create_track(track_name)
        track.fader = float(value)
        track.update_parameter("fader", float(value))
        self._save()
        return track.fader

    def toggle_mute(self, track_name):
        track = self.get_or_create_track(track_name)
        track.muted = not track.muted
        self._save()
        return track.muted

    def toggle_solo(self, track_name):
        track = self.get_or_create_track(track_name)
        track.soloed = not track.soloed
        self._save()
        return track.soloed

    def save_checkpoint(self, name):
        """Creates a named snapshot of current track states and parameters."""
        snapshot = {k: t.to_dict() for k, t in self.tracks.items()}
        self.checkpoints[name] = {
            "timestamp": time.time(),
            "time_str": time.strftime("%Y-%m-%d %H:%M:%S"),
            "snapshot": snapshot
        }
        self._save()
        return name

    def restore_checkpoint(self, name):
        """Restores session memory to a previously saved checkpoint snapshot."""
        if name not in self.checkpoints:
            return False
        data = self.checkpoints[name]["snapshot"]
        self.tracks = {k: TrackState.from_dict(v) for k, v in data.items()}
        self._save()
        return True

    def list_checkpoints(self):
        return list(self.checkpoints.keys())

    def get_checkpoint_details(self, name):
        """Returns structured metadata about a specific checkpoint snapshot."""
        if name not in self.checkpoints:
            return None
        cp = self.checkpoints[name]
        return {
            "name": name,
            "timestamp": cp.get("timestamp"),
            "time_str": cp.get("time_str"),
            "track_count": len(cp.get("snapshot", {})),
            "tracks": list(cp.get("snapshot", {}).keys())
        }

    def undo_last_action(self):
        """Reverts parameter changes introduced by the most recent AI mixing action."""
        if not self.action_history:
            return []
        last_action = self.action_history.pop()
        self.redo_history.append(last_action)
        reverted_moves = []
        for path, val in last_action.get("moves", []):
            parts = path.strip("/").split("/")
            if len(parts) >= 3 and parts[0] == "track":
                track_name = parts[1]
                param_key = "/".join(parts[2:])
                # Revert faders to 0.0 or remove parameter
                track = self.get_or_create_track(track_name)
                if "fader" in param_key:
                    track.fader = 0.0
                    track.update_parameter("fader", 0.0)
                    reverted_moves.append((path, 0.0))
                elif param_key in track.parameters:
                    del track.parameters[param_key]
                    reverted_moves.append((path, 0.0))
        self._save()
        return reverted_moves

    def redo_last_action(self):
        """Re-applies the most recently undone AI mixing action."""
        if not self.redo_history:
            return []
        action = self.redo_history.pop()
        self.action_history.append(action)
        applied_moves = []
        for path, val in action.get("moves", []):
            self.record_osc_change(path, val)
            applied_moves.append((path, val))
        self._save()
        return applied_moves

    def sync_plugin_parameter(self, track_id, plugin_id, param_name, value, send_ipc=True):
        """Synchronizes an Omni-Plugin Bridge parameter across DAWs and updates session memory."""
        full_key = f"{track_id}:{plugin_id}:{param_name}"
        self.omni_synced_params[full_key] = float(value)
        track = self.get_or_create_track(track_id)
        track.update_parameter(f"plugins/{plugin_id}/{param_name}", float(value))
        self._save()

        if send_ipc:
            self._send_omni_ipc(full_key, float(value))

        return self.omni_synced_params[full_key]

    def apply_plugin_preset(self, track_id, preset_name):
        """Applies a multi-parameter plugin preset block to a track and synchronizes it."""
        params = PLUGIN_PRESETS.get(preset_name, PLUGIN_PRESETS.get("Warm Tube", {}))
        applied = {}
        for param_path, val in params.items():
            parts = param_path.split("/")
            plugin_id = parts[0]
            param_name = "/".join(parts[1:])
            self.sync_plugin_parameter(track_id, plugin_id, param_name, val)
            applied[param_path] = val
        return applied

    def sync_session_manifest_to_bridge(self):
        """Dispatches full session manifest to the Rust Omni-Plugin Host."""
        if not os.path.exists(self.omni_socket_path):
            return False
        try:
            payload = {
                "tracks": {k: t.to_dict() for k, t in self.tracks.items()},
                "active_daws": list(self.registered_daws.keys())
            }
            manifest_str = json.dumps(payload)
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.settimeout(0.5)
            client.connect(self.omni_socket_path)
            cmd = f"SYNC_MANIFEST {manifest_str}\n"
            client.sendall(cmd.encode("utf-8"))
            resp = client.recv(1024).decode("utf-8")
            client.close()
            return True
        except Exception as e:
            logging.debug(f"Omni-Plugin manifest sync error: {e}")
            return False

    def _send_omni_ipc(self, key, value):
        """Dispatches parameter change to the standalone Rust Omni-Plugin host if available."""
        if not os.path.exists(self.omni_socket_path):
            return False
        try:
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.settimeout(0.5)
            client.connect(self.omni_socket_path)
            cmd = f"SET {key} {value}\n"
            client.sendall(cmd.encode("utf-8"))
            client.close()
            return True
        except Exception as e:
            logging.debug(f"Omni-Plugin IPC send error: {e}")
            return False

    def get_summary(self):
        return {
            "total_tracks": len(self.tracks),
            "tracks": {k: t.to_dict() for k, t in self.tracks.items()},
            "recent_actions": self.action_history[-5:],
            "omni_synced_params": self.omni_synced_params
        }

    def _save(self):
        try:
            data = {
                "tracks": {k: t.to_dict() for k, t in self.tracks.items()},
                "history": self.action_history,
                "checkpoints": self.checkpoints
            }
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logging.warning(f"SessionMemory save warning: {e}")

    def _load(self):
        if not os.path.exists(self.storage_path) or os.path.getsize(self.storage_path) == 0:
            # Seed with archetypal multi-track session
            for name in ["kick", "snare", "hihat", "bass", "synth", "vocals", "master"]:
                self.get_or_create_track(name)
            self._save()
            return

        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
                for t_name, t_data in data.get("tracks", {}).items():
                    self.tracks[t_name] = TrackState.from_dict(t_data)
                self.action_history = data.get("history", [])
                self.checkpoints = data.get("checkpoints", {})
        except Exception as e:
            logging.warning(f"SessionMemory load warning: {e}")


def main():
    print("=== Testing Bobtrax Track Agent-Memory Hub ===")
    mem = SessionMemory()
    print(f"Loaded {len(mem.tracks)} tracks from session memory.")

    # Record test OSC changes
    mem.record_osc_change("/track/kick/compressor/threshold", -18.5)
    mem.record_osc_change("/track/bass/fader", -3.0)
    mem.record_action(
        agent_name="ai_mixing_assistant",
        prompt="Make the kick punchy and tighten bass",
        moves=[("/track/kick/eq/low_shelf", 3.0), ("/track/bass/compressor/threshold", -14.0)]
    )

    summary = mem.get_summary()
    print(f"Total active tracks: {summary['total_tracks']}")
    print(f"Kick parameters: {mem.tracks['kick'].parameters}")
    print(f"Bass fader: {mem.tracks['bass'].fader}")
    print(f"Action history count: {len(mem.action_history)}")
    assert len(mem.tracks) >= 7
    assert "compressor/threshold" in mem.tracks["kick"].parameters
    print("=== Track Agent-Memory Hub verified successfully! ===")


if __name__ == "__main__":
    main()
