#!/usr/bin/env python3
"""
Bobtrax WebAssembly Collaboration Server Host

Provides a standalone HTTP server serving the compiled WebAssembly audio engine
and launcher portal files (by default from ./wasm_launcher or ./wasm/wasm_launcher).
Includes CORS and SharedArrayBuffer headers needed for WebAudio / AudioWorklet execution.
"""

import argparse
import functools
import http.server
import os
import socketserver
import sys

class WasmHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler with Cross-Origin headers required for WebAssembly SharedArrayBuffer."""
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

def run_server(port=8080, directory=None):
    if not directory:
        candidate_dirs = [
            os.path.abspath(os.path.join(os.path.dirname(__file__), "wasm_launcher")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "wasm", "wasm_launcher")),
            os.path.abspath(os.path.dirname(__file__))
        ]
        for d in candidate_dirs:
            if os.path.isdir(d):
                directory = d
                break

    handler = functools.partial(WasmHandler, directory=directory)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"[WASM Host] Serving WebAssembly Collaboration Portal from '{directory}' at http://localhost:{port}")
        print("[WASM Host] Press Ctrl+C to terminate.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[WASM Host] Server shutting down cleanly...")
        finally:
            httpd.server_close()

def main():
    parser = argparse.ArgumentParser(description="Bobtrax WebAssembly Collaboration Server")
    parser.add_argument("--port", type=int, default=8080, help="Port to host server on (default: 8080)")
    parser.add_argument("--dir", type=str, default=None, help="Directory to serve (default: ./wasm_launcher)")
    args = parser.parse_args()
    run_server(port=args.port, directory=args.dir)

if __name__ == "__main__":
    main()
