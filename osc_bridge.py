#!/usr/bin/env python3
"""
Bobtrax OSC Bridge / Router

This script acts as the foundational Inter-Process Communication (IPC) layer
for the Bobtrax ecosystem. Extensive codebase analysis revealed that Ardour,
MusE, and potentially others natively support OSC (Open Sound Control).

Purpose:
To act as a central hub/router. When one DAW sends a transport command
(e.g., play, stop, rewind), this bridge catches it and broadcasts it to
all other registered DAWs in the ecosystem, effectively creating a
"Shared State" between isolated audio workstations.

Status:
This is a Proof-of-Concept foundation. It sets up the UDP server and
routing logic. Full bi-directional binding to the specific OSC address
namespaces of Ardour and MusE will require the `python-osc` package.
"""

import argparse
import sys
import logging

try:
    from pythonosc.dispatcher import Dispatcher
    from pythonosc.osc_server import BlockingOSCUDPServer
    from pythonosc.udp_client import SimpleUDPClient
except ImportError:
    print("Warning: python-osc is not installed. Run 'pip install python-osc' to use the full bridge functionality.")
    HAS_OSC = False
else:
    HAS_OSC = True

# Known default OSC ports for the DAWs (example mappings)
# Ardour typically defaults to 3819
# MusE typically defaults to some configured port
DAW_CLIENTS = {
    'ardour': ('127.0.0.1', 3819),
    'muse': ('127.0.0.1', 5000),
    'lmms': ('127.0.0.1', 5001)   # Speculative/Future
}

# Global clients list
clients = []

def broadcast_handler(address, *args):
    """
    Catches incoming OSC messages and routes them to all registered DAWs
    except the sender (to prevent infinite loops, if sender ID was known).
    For now, it broadcasts broadly.
    """
    logging.info(f"Received message on {address} with arguments: {args}")
    for client in clients:
        try:
            client.send_message(address, args)
            logging.debug(f"Broadcasted to {client._address}:{client._port}")
        except Exception as e:
            logging.error(f"Failed to broadcast to {client._address}:{client._port} - {e}")

def setup_clients():
    """Initializes UDP clients for broadcasting."""
    if not HAS_OSC: return []
    active_clients = []
    for name, (ip, port) in DAW_CLIENTS.items():
        client = SimpleUDPClient(ip, port)
        active_clients.append(client)
        logging.info(f"Registered {name} client at {ip}:{port}")
    return active_clients

def main():
    parser = argparse.ArgumentParser(description="Bobtrax OSC Bridge - Central IPC Hub")
    parser.add_argument("--ip", default="127.0.0.1", help="The IP to listen on")
    parser.add_argument("--port", type=int, default=8000, help="The port to listen on")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    if not HAS_OSC:
        logging.error("Exiting due to missing python-osc dependency.")
        sys.exit(1)

    global clients
    clients = setup_clients()

    dispatcher = Dispatcher()
    # Map all incoming messages to the broadcast handler
    dispatcher.map("/*", broadcast_handler)

    try:
        server = BlockingOSCUDPServer((args.ip, args.port), dispatcher)
        logging.info(f"Serving on {server.server_address}")
        logging.info("Waiting for incoming OSC messages to route...")
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("Bridge stopped by user.")
    except Exception as e:
        logging.error(f"Server error: {e}")

if __name__ == "__main__":
    main()
