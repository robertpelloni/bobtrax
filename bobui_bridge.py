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
import sys

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


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SOCKET_PATH
    alive = verify_omni_connection(path)
    print(f"Omni Bridge Host at {path}: {'ALIVE' if alive else 'DISCONNECTED'}")
