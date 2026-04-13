#!/usr/bin/env python3
"""
Bobtrax OSC Bridge / Router

This script acts as the foundational Inter-Process Communication (IPC) layer
for the Bobtrax ecosystem. Extensive codebase analysis revealed that Ardour,
MusE, and potentially others natively support OSC (Open Sound Control).

Purpose:
To act as a central hub/router. When one DAW sends a transport command
(e.g., play, stop, rewind), this bridge catches it, translates it to a
standardized 'Bobtrax' namespace, and broadcasts the native equivalents to
all other registered DAWs in the ecosystem, effectively creating a
"Shared State" between isolated audio workstations.

Status:
Implementation of OSC Translation Mapping.
Requires `python-osc` package.
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

# Known default OSC ports for the DAWs
DAW_CLIENTS = {
    'ardour': ('127.0.0.1', 3819),
    'muse': ('127.0.0.1', 5000),
    'lmms': ('127.0.0.1', 5001)   # Speculative/Future
}

# Translation dictionary.
# Key: The incoming OSC address from a specific DAW
# Value: A standardized internal action name
INCOMING_MAP = {
    '/transport_play': 'play',       # Ardour
    '/transport_stop': 'stop',       # Ardour
    '/muse/play': 'play',            # MusE (Hypothetical standard)
    '/muse/stop': 'stop'             # MusE
}

# Translation dictionary.
# Key: The standardized internal action name
# Value: A dictionary of how to tell each DAW to perform that action
OUTGOING_MAP = {
    'play': {
        'ardour': '/transport_play',
        'muse': '/muse/play'
    },
    'stop': {
        'ardour': '/transport_stop',
        'muse': '/muse/stop'
    }
}

# Global clients map: { daw_name : SimpleUDPClient }
clients = {}

def broadcast_handler(address, *args):
    """
    Catches incoming OSC messages, checks for translations, and routes them.
    """
    logging.info(f"Received message on {address} with arguments: {args}")

    action = INCOMING_MAP.get(address)

    if action:
        logging.info(f"Translated '{address}' to standard action '{action}'")
        outgoing_commands = OUTGOING_MAP.get(action, {})

        for daw_name, target_address in outgoing_commands.items():
            client = clients.get(daw_name)
            if client:
                try:
                    # In a robust implementation, we would omit sending back to the originator.
                    # Since we don't strictly know the originator by IP/Port alone easily here,
                    # we broadcast to all. DAWs usually ignore redundant play commands.
                    client.send_message(target_address, args)
                    logging.debug(f"Broadcasted '{target_address}' to {daw_name} ({client._address}:{client._port})")
                except Exception as e:
                    logging.error(f"Failed to broadcast to {daw_name} - {e}")
    else:
        logging.debug(f"No translation found for {address}. Broadcasting raw address.")
        # Fallback: Just broadcast the raw address to everyone
        for daw_name, client in clients.items():
            try:
                client.send_message(address, args)
            except Exception as e:
                logging.error(f"Failed raw broadcast to {daw_name} - {e}")

def setup_clients():
    """Initializes UDP clients for broadcasting."""
    if not HAS_OSC: return {}
    active_clients = {}
    for name, (ip, port) in DAW_CLIENTS.items():
        client = SimpleUDPClient(ip, port)
        active_clients[name] = client
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
