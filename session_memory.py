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
        self.checkpoints = {}
        self.omni_socket_path = DEFAULT_OMNI_SOCKET
        self.omni_synced_params = {}
        self._load()
        self._initialized = True

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

    def undo_last_action(self):
        """Reverts parameter changes introduced by the most recent AI mixing action."""
        if not self.action_history:
            return []
        last_action = self.action_history.pop()
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
