#!/usr/bin/env python3
"""
Bobtrax Continuous Background Health Watchdog & Self-Healing Daemon

Periodically probes all core ecosystem services:
1. Central OSC Bridge (127.0.0.1:8000 UDP)
2. WebSocket Gateway (127.0.0.1:8765 TCP/WS)
3. WebAssembly Collaboration Server (127.0.0.1:8080 HTTP)
4. Omni-Plugin Bridge Unix Domain Socket (/tmp/bobtrax_omni_bridge.sock)

Provides real-time health telemetry and optional auto-healing restarts.
"""

import argparse
import http.client
import logging
import os
import socket
import sys
import time

SERVICES = {
    "osc_bridge": {"type": "udp", "host": "127.0.0.1", "port": 8000, "name": "OSC Bridge"},
    "osc_web": {"type": "tcp", "host": "127.0.0.1", "port": 8765, "name": "WebSocket Gateway"},
    "wasm_host": {"type": "http", "host": "127.0.0.1", "port": 8080, "name": "WASM Host"},
    "omni_bridge": {"type": "unix", "path": "/tmp/bobtrax_omni_bridge.sock", "name": "Omni-Plugin Bridge"}
}


def check_tcp_service(host, port, timeout=1.0):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def check_http_service(host, port, timeout=1.0):
    try:
        conn = http.client.HTTPConnection(host, port, timeout=timeout)
        conn.request("GET", "/")
        resp = conn.getresponse()
        conn.close()
        return resp.status in [200, 301, 302, 404]
    except Exception:
        return False


def check_udp_service(host, port, timeout=1.0):
    # UDP is connectionless; check if socket can be created and bound or written to
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        sock.sendto(b"/ping\x00\x00\x00,\x00\x00\x00", (host, port))
        sock.close()
        return True
    except Exception:
        return False


def check_unix_socket(path):
    if not os.path.exists(path):
        return False
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        sock.connect(path)
        sock.close()
        return True
    except Exception:
        return False


class HealthWatchdog:
    def __init__(self, services=None, auto_heal=False, on_restart=None):
        self.services = services or SERVICES
        self.auto_heal = auto_heal
        self.on_restart = on_restart
        self.last_status = {}

    def probe_all(self):
        results = {}
        for key, conf in self.services.items():
            stype = conf.get("type")
            if stype == "http":
                is_alive = check_http_service(conf["host"], conf["port"])
            elif stype == "tcp":
                is_alive = check_tcp_service(conf["host"], conf["port"])
            elif stype == "udp":
                is_alive = check_udp_service(conf["host"], conf["port"])
            elif stype == "unix":
                is_alive = check_unix_socket(conf["path"])
            else:
                is_alive = False

            results[key] = {
                "name": conf.get("name", key),
                "alive": is_alive,
                "timestamp": time.time()
            }

            if not is_alive and self.auto_heal and self.on_restart:
                logging.warning(f"Watchdog: Service '{key}' is down. Triggering self-healing restart...")
                try:
                    self.on_restart(key)
                except Exception as e:
                    logging.error(f"Failed self-healing for '{key}': {e}")

        self.last_status = results
        return results

    def get_summary(self):
        alive_count = sum(1 for v in self.last_status.values() if v.get("alive"))
        total = len(self.last_status)
        return f"{alive_count}/{total} services active"


def main():
    parser = argparse.ArgumentParser(description="Bobtrax Health Watchdog Daemon")
    parser.add_argument("--check-once", action="store_true", help="Probe services once and exit")
    parser.add_argument("--interval", type=int, default=5, help="Probe interval in seconds")
    args = parser.parse_args()

    watchdog = HealthWatchdog()
    if args.check_once:
        print("=== Bobtrax System Health Diagnostic ===")
        status = watchdog.probe_all()
        for k, v in status.items():
            tag = "ONLINE" if v["alive"] else "OFFLINE"
            print(f"• {v['name']:<24}: {tag}")
        print(f"\nSummary: {watchdog.get_summary()}")
        sys.exit(0)

    print(f"Watchdog daemon started. Probing every {args.interval}s...")
    try:
        while True:
            watchdog.probe_all()
            print(f"[{time.strftime('%H:%M:%S')}] Health: {watchdog.get_summary()}")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nWatchdog terminated cleanly.")


if __name__ == "__main__":
    main()
