#!/usr/bin/env python3
"""
Bobtrax Web/WebSocket to OSC Wrapper

Purpose:
To provide a bridge between modern web technologies (HTML/JS/React) and
the low-latency audio ecosystem of Bobtrax. This script opens a WebSocket
server. When it receives a JSON payload like `{"action": "play"}`, it
translates it into an OSC message (`/transport_play` or similar) and sends
it to the central `osc_bridge.py` hub.

This fulfills the final Phase 2 TODO:
"Expose an HTTP/WebSocket wrapper on top of osc_bridge.py so bobui can
command the DAWs via web technologies if desired."

Requires:
`pip install websockets python-osc`
"""

import asyncio
import json
import argparse
import logging

try:
    import websockets
    from pythonosc.udp_client import SimpleUDPClient
except ImportError:
    print("Warning: Missing dependencies. Run 'pip install websockets python-osc'")
    HAS_DEPS = False
else:
    HAS_DEPS = True

# We assume osc_bridge.py is running on localhost:8000 by default.
OSC_BRIDGE_IP = "127.0.0.1"
OSC_BRIDGE_PORT = 8000

osc_client = None

async def handle_client(websocket, path):
    """
    Handles incoming WebSocket connections.
    Expects JSON payload: {"action": "play"} or {"action": "stop"}
    """
    logging.info(f"Client connected from {websocket.remote_address}")

    try:
        async for message in websocket:
            logging.debug(f"Received JSON: {message}")

            try:
                data = json.loads(message)
                action = data.get("action")

                if action:
                    # In Bobtrax, the osc_bridge.py INCOMING_MAP dictates the entry keys.
                    # As defined in osc_bridge.py:
                    # '/transport_play': 'play'
                    # '/transport_stop': 'stop'
                    # So we send the raw OSC path that the bridge recognizes.
                    if action == "play":
                        osc_path = "/transport_play"
                    elif action == "stop":
                        osc_path = "/transport_stop"
                    else:
                        logging.warning(f"Unknown action requested: {action}")
                        continue

                    logging.info(f"Routing action '{action}' -> OSC '{osc_path}'")
                    osc_client.send_message(osc_path, 1.0)

                    await websocket.send(json.dumps({"status": "success", "action": action}))
                else:
                    await websocket.send(json.dumps({"status": "error", "message": "Missing 'action' key"}))

            except json.JSONDecodeError:
                logging.error("Received malformed JSON")
                await websocket.send(json.dumps({"status": "error", "message": "Invalid JSON payload"}))

    except websockets.exceptions.ConnectionClosed:
        logging.info("Client disconnected")

async def start_server(ws_ip, ws_port):
    logging.info(f"WebSocket server starting on ws://{ws_ip}:{ws_port}")
    async with websockets.serve(handle_client, ws_ip, ws_port):
        await asyncio.Future()  # run forever

def main():
    parser = argparse.ArgumentParser(description="Bobtrax Web-to-OSC Wrapper")
    parser.add_argument("--ws-ip", default="127.0.0.1", help="WebSocket server IP")
    parser.add_argument("--ws-port", type=int, default=8765, help="WebSocket server port")
    parser.add_argument("--osc-ip", default=OSC_BRIDGE_IP, help="Target osc_bridge IP")
    parser.add_argument("--osc-port", type=int, default=OSC_BRIDGE_PORT, help="Target osc_bridge port")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    if not HAS_DEPS:
        logging.error("Exiting due to missing dependencies.")
        sys.exit(1)

    global osc_client
    osc_client = SimpleUDPClient(args.osc_ip, args.osc_port)
    logging.info(f"OSC Output configured to target bridge at {args.osc_ip}:{args.osc_port}")

    try:
        asyncio.run(start_server(args.ws_ip, args.ws_port))
    except KeyboardInterrupt:
        logging.info("WebSocket server stopped by user.")

if __name__ == "__main__":
    main()
