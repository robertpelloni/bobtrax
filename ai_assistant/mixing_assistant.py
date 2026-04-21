#!/usr/bin/env python3
"""
Bobtrax Autonomous AI Mixing Assistant

Purpose:
This script fulfills Phase 3 of the Bobtrax Roadmap. It acts as a local
LLM prompt translator. A user provides natural language like "Make the kick punchy"
and this assistant sends the prompt to an LLM backend (OpenAI, Local Llama.cpp, etc.)
along with a dynamic system prompt containing the currently available OSC schema and
track list.

The LLM returns a structured JSON payload of explicit mixing moves (e.g., EQ cuts,
Compression thresholds). These are parsed and routed as OSC packets into
`osc_bridge.py` so the currently open DAWs (Ardour, LMMS, etc.) apply the mixing
moves in real time.

Dependencies:
`pip install python-osc openai`
"""

import argparse
import json
import logging
import sys
import os

try:
    from pythonosc.udp_client import SimpleUDPClient
except ImportError:
    print("Warning: Missing python-osc dependency.")
    HAS_OSC = False
else:
    HAS_OSC = True

try:
    from openai import OpenAI
except ImportError:
    print("Warning: Missing openai dependency.")
    HAS_OPENAI = False
else:
    HAS_OPENAI = True

OSC_BRIDGE_IP = "127.0.0.1"
OSC_BRIDGE_PORT = 8000

# Placeholder for future dynamic DAWs state discovery.
# In a robust implementation, the assistant would query `osc_bridge.py`
# for the currently open session's track list.
MOCK_AVAILABLE_TRACKS = ["kick", "snare", "hihat", "bass", "synth", "vocals", "master"]

# Schema of valid operations the LLM is allowed to touch.
# This guides the LLM to output ONLY compatible OSC endpoints.
AVAILABLE_OSC_SCHEMA = """
Valid OSC Address Patterns for Bobtrax Ecosystem:
1. /track/{track_name}/compressor/threshold (Float: -60.0 to 0.0 dB)
2. /track/{track_name}/compressor/ratio (Float: 1.0 to 20.0)
3. /track/{track_name}/eq/low_shelf (Float: -24.0 to 24.0 dB)
4. /track/{track_name}/eq/high_cut (Float: 20.0 to 20000.0 Hz)
5. /track/{track_name}/saturation/drive (Float: 0.0 to 10.0)
6. /track/{track_name}/limiter/gain (Float: -24.0 to 24.0 dB)
"""

def generate_system_prompt():
    """Builds the comprehensive instruction set for the LLM."""
    tracks_str = ", ".join(MOCK_AVAILABLE_TRACKS)
    return (
        "You are Bobtrax, an elite AI mixing assistant for a multi-DAW open-source ecosystem. "
        "Your job is to translate a user's natural language mixing request into an exact array of Open Sound Control (OSC) moves. "
        f"\n\nCurrently active tracks in the session: {tracks_str}"
        f"\n\nAvailable OSC schema you are permitted to use:\n{AVAILABLE_OSC_SCHEMA}"
        "\n\nYou MUST respond ONLY with valid JSON in the following format, with no markdown formatting or conversational text:"
        "\n["
        "\n  {\"path\": \"/track/kick/compressor/threshold\", \"value\": -15.5},"
        "\n  {\"path\": \"/track/snare/eq/low_shelf\", \"value\": 3.0}"
        "\n]"
    )

def parse_prompt_to_mix_moves(prompt_text, api_key=None, base_url=None):
    """
    Sends the user prompt and system constraints to the LLM backend.
    Parses the returned JSON into a list of tuples: (osc_path, float_value).
    """
    logging.info(f"Analyzing prompt via LLM: '{prompt_text}'")

    if not HAS_OPENAI:
        logging.error("OpenAI package not installed. Cannot perform LLM inference.")
        return []

    # Initialize client. Allows overriding base_url for local models like LM Studio or Ollama.
    client_kwargs = {}
    if api_key:
        client_kwargs['api_key'] = api_key
    elif not base_url:
        # If no key and no custom URL, assume they have OPENAI_API_KEY in env
        if not os.getenv("OPENAI_API_KEY") and not os.getenv("GROQ_API_KEY"):
            logging.warning("No API key provided and no local base_url specified.")

    if base_url:
        client_kwargs['base_url'] = base_url
        if 'api_key' not in client_kwargs:
            client_kwargs['api_key'] = "local-placeholder"

    try:
        client = OpenAI(**client_kwargs)

        response = client.chat.completions.create(
            model="gpt-4o", # Can be overridden or mapped to a local model name if base_url is set
            messages=[
                {"role": "system", "content": generate_system_prompt()},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.2,
            response_format={ "type": "json_object" } # Force JSON if supported
        )

        content = response.choices[0].message.content
        logging.debug(f"LLM Raw Response: {content}")

        # Parse the JSON response
        moves_dict = json.loads(content)

        # The LLM might wrap the array in a dict key like {"moves": [...]} depending on the model,
        # but our prompt requests a raw array. We handle both just in case.
        if isinstance(moves_dict, dict):
            # Try to find the first list value
            for val in moves_dict.values():
                if isinstance(val, list):
                    moves_dict = val
                    break

        if not isinstance(moves_dict, list):
            logging.error("LLM did not return a valid list of moves.")
            return []

        parsed_moves = []
        for move in moves_dict:
            path = move.get("path")
            val = move.get("value")
            if path and val is not None:
                parsed_moves.append((path, float(val)))

        return parsed_moves

    except Exception as e:
        logging.error(f"LLM API Call failed: {e}")
        return []

def apply_mix_moves(moves, client):
    """
    Iterates over the generated array of mixing moves and sends them
    to the central OSC bridge to be distributed to the DAWs.
    """
    for osc_path, value in moves:
        logging.info(f"Applying move: {osc_path} -> {value}")
        if client:
            try:
                client.send_message(osc_path, value)
            except Exception as e:
                logging.error(f"Failed to send {osc_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Bobtrax Autonomous AI Mixing Assistant")
    parser.add_argument("prompt", type=str, help="Natural language mixing instruction")
    parser.add_argument("--osc-ip", default=OSC_BRIDGE_IP, help="Target osc_bridge IP")
    parser.add_argument("--osc-port", type=int, default=OSC_BRIDGE_PORT, help="Target osc_bridge port")
    parser.add_argument("--llm-url", type=str, default=None, help="Custom LLM API Base URL (e.g., http://localhost:1234/v1 for LM Studio)")
    parser.add_argument("--api-key", type=str, default=None, help="LLM API Key (defaults to OPENAI_API_KEY env var)")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    if not HAS_OSC:
        logging.error("Cannot broadcast mix moves. Install python-osc.")
        sys.exit(1)

    osc_client = SimpleUDPClient(args.osc_ip, args.osc_port)

    moves = parse_prompt_to_mix_moves(args.prompt, api_key=args.api_key, base_url=args.llm_url)
    if moves:
        apply_mix_moves(moves, osc_client)
        print("Mixing complete.")
    else:
        print("No mixing moves generated.")

if __name__ == "__main__":
    main()
