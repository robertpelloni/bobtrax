#!/usr/bin/env python3
"""
Bobtrax Autonomous AI Mixing Assistant

Purpose:
Translates conversational natural language mixing requests (e.g. "Make the kick punchy",
"Cut muddy low-mids on vocals", "Glue the master bus") into concrete Open Sound Control (OSC)
mixing moves.

Capabilities:
1. Dynamic Track Discovery: Extracts active track lists from session files (LMMS .mmp/.mmpz,
   Ardour .ardour XML), environment variables (`BOBTRAX_TRACKS`), or fallback schemas.
2. Dual-Engine Architecture:
   - Primary: LLM API Inference (OpenAI GPT-4o, Groq, or Local Llama.cpp / Ollama endpoints).
   - Fallback: Intelligent Acoustic Rule-Based DSP Heuristic Engine that functions completely
     offline without external API keys or network access.
3. Strict Safety Clamping: Enforces boundary limits on thresholds, EQ frequencies, gains,
   and compressor ratios prior to OSC packet transmission.
"""

import argparse
import json
import logging
import os
import re
import sys
import xml.etree.ElementTree as ET

try:
    from pythonosc.udp_client import SimpleUDPClient
    HAS_OSC = True
except ImportError:
    HAS_OSC = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import session_memory
    memory_hub = session_memory.SessionMemory()
except Exception:
    memory_hub = None

OSC_BRIDGE_IP = "127.0.0.1"
OSC_BRIDGE_PORT = 8000

DEFAULT_TRACKS = ["kick", "snare", "hihat", "bass", "synth", "vocals", "master"]

# Safe Boundaries for OSC Controls
PARAM_BOUNDARIES = {
    "compressor/threshold": (-60.0, 0.0),
    "compressor/ratio": (1.0, 20.0),
    "compressor/attack": (0.1, 500.0),
    "compressor/release": (10.0, 2000.0),
    "eq/low_shelf": (-24.0, 24.0),
    "eq/high_shelf": (-24.0, 24.0),
    "eq/low_cut": (20.0, 1000.0),
    "eq/high_cut": (1000.0, 20000.0),
    "saturation/drive": (0.0, 10.0),
    "limiter/gain": (-24.0, 24.0),
    "fader": (-90.0, 12.0)
}

AVAILABLE_OSC_SCHEMA = """
Valid OSC Address Patterns:
1. /track/{track}/compressor/threshold (Float: -60.0 to 0.0 dB)
2. /track/{track}/compressor/ratio (Float: 1.0 to 20.0)
3. /track/{track}/compressor/attack (Float: 0.1 to 500.0 ms)
4. /track/{track}/compressor/release (Float: 10.0 to 2000.0 ms)
5. /track/{track}/eq/low_shelf (Float: -24.0 to 24.0 dB)
6. /track/{track}/eq/high_shelf (Float: -24.0 to 24.0 dB)
7. /track/{track}/eq/high_cut (Float: 1000.0 to 20000.0 Hz)
8. /track/{track}/saturation/drive (Float: 0.0 to 10.0)
9. /track/{track}/limiter/gain (Float: -24.0 to 24.0 dB)
10. /track/{track}/fader (Float: -90.0 to 12.0 dB)
"""


def discover_session_tracks(session_path=None):
    """
    Auto-discovers session tracks from:
    1. Environment variable BOBTRAX_TRACKS
    2. Provided session file (.ardour XML, .mmp LMMS XML)
    3. Default archetype track list
    """
    env_tracks = os.environ.get("BOBTRAX_TRACKS")
    if env_tracks:
        tracks = [t.strip().lower() for t in env_tracks.split(",") if t.strip()]
        if tracks:
            logging.info(f"Discovered {len(tracks)} tracks from BOBTRAX_TRACKS environment variable.")
            return tracks

    if session_path and os.path.exists(session_path):
        try:
            # Parse Ardour session XML
            if session_path.endswith(".ardour") or session_path.endswith(".xml"):
                tree = ET.parse(session_path)
                root = tree.getroot()
                tracks = []
                for route in root.findall(".//Route"):
                    name = route.attrib.get("name")
                    if name and not route.attrib.get("master"):
                        tracks.append(re.sub(r'[^a-zA-Z0-9_-]', '', name).lower())
                if tracks:
                    logging.info(f"Discovered {len(tracks)} tracks from Ardour session XML: {tracks}")
                    return tracks
            # Parse LMMS session XML (.mmp)
            elif session_path.endswith(".mmp"):
                tree = ET.parse(session_path)
                root = tree.getroot()
                tracks = []
                for track in root.findall(".//track"):
                    name = track.attrib.get("name")
                    if name:
                        tracks.append(re.sub(r'[^a-zA-Z0-9_-]', '', name).lower())
                if tracks:
                    logging.info(f"Discovered {len(tracks)} tracks from LMMS session file: {tracks}")
                    return tracks
        except Exception as e:
            logging.warning(f"Failed to parse session file '{session_path}': {e}")

    return DEFAULT_TRACKS


def clamp_parameter(osc_path, value):
    """Clamps parameter values strictly within valid acoustic ranges."""
    for param_key, (min_val, max_val) in PARAM_BOUNDARIES.items():
        if param_key in osc_path:
            clamped = max(min_val, min(max_val, float(value)))
            if clamped != value:
                logging.debug(f"Clamped {osc_path} from {value} to {clamped}")
            return clamped
    return float(value)


def heuristic_dsp_rules(prompt_text, available_tracks):
    """
    Intelligent offline rule-based acoustic DSP engine.
    Translates colloquial audio engineering jargon into exact OSC moves.
    """
    p = prompt_text.lower()
    moves = []

    def best_track(candidates):
        for c in candidates:
            for t in available_tracks:
                if c in t:
                    return t
        return candidates[0] if candidates else None

    # Kick Drum rules
    if "kick" in p:
        track = best_track(["kick", "bd", "drums"])
        if "punch" in p or "tight" in p or "thump" in p:
            moves.append((f"/track/{track}/eq/low_shelf", 3.5))
            moves.append((f"/track/{track}/compressor/threshold", -14.0))
            moves.append((f"/track/{track}/compressor/ratio", 4.0))
            moves.append((f"/track/{track}/compressor/attack", 25.0))
        if "boom" in p or "sub" in p:
            moves.append((f"/track/{track}/eq/low_shelf", 5.0))
        if "box" in p or "mud" in p or "cut" in p:
            moves.append((f"/track/{track}/eq/high_cut", 6500.0))

    # Snare Drum rules
    if "snare" in p or "clap" in p:
        track = best_track(["snare", "clap", "drums"])
        if "crack" in p or "snap" in p or "bright" in p:
            moves.append((f"/track/{track}/eq/high_shelf", 3.0))
            moves.append((f"/track/{track}/compressor/threshold", -12.0))
            moves.append((f"/track/{track}/compressor/ratio", 3.5))
        if "compress" in p or "fat" in p:
            moves.append((f"/track/{track}/compressor/threshold", -16.0))
            moves.append((f"/track/{track}/compressor/ratio", 4.0))

    # Bass rules
    if "bass" in p or "sub" in p and "kick" not in p:
        track = best_track(["bass", "sub", "808"])
        if "duck" in p or "sidechain" in p:
            moves.append((f"/track/{track}/compressor/threshold", -18.0))
            moves.append((f"/track/{track}/compressor/ratio", 6.0))
            moves.append((f"/track/{track}/compressor/attack", 5.0))
        if "fat" in p or "warm" in p:
            moves.append((f"/track/{track}/eq/low_shelf", 2.5))
            moves.append((f"/track/{track}/saturation/drive", 3.0))
        if "tight" in p or "cut" in p:
            moves.append((f"/track/{track}/eq/low_cut", 35.0))

    # Vocal rules
    if "vocal" in p or "vox" in p or "lead" in p:
        track = best_track(["vocal", "vox", "lead"])
        if "air" in p or "clarity" in p or "bright" in p or "presence" in p:
            moves.append((f"/track/{track}/eq/high_shelf", 4.0))
            moves.append((f"/track/{track}/compressor/threshold", -15.0))
            moves.append((f"/track/{track}/compressor/ratio", 2.8))
        if "mud" in p or "clean" in p or "cut" in p:
            moves.append((f"/track/{track}/eq/low_cut", 85.0))
            moves.append((f"/track/{track}/eq/low_shelf", -2.5))
        if "warm" in p:
            moves.append((f"/track/{track}/saturation/drive", 2.0))

    # Synth / Keys rules
    if "synth" in p or "pad" in p or "piano" in p or "keys" in p:
        track = best_track(["synth", "pad", "piano", "keys"])
        if "wide" in p or "bright" in p:
            moves.append((f"/track/{track}/eq/high_shelf", 2.5))
        if "warm" in p or "analog" in p:
            moves.append((f"/track/{track}/saturation/drive", 4.2))

    # Master / 2-Bus Glue rules
    if "master" in p or "glue" in p or "buss" in p or "bus" in p or not moves:
        track = best_track(["master", "bus", "main"])
        if "glue" in p or "compress" in p:
            moves.append((f"/track/{track}/compressor/threshold", -8.0))
            moves.append((f"/track/{track}/compressor/ratio", 2.0))
            moves.append((f"/track/{track}/compressor/attack", 30.0))
        if "warm" in p or "saturat" in p:
            moves.append((f"/track/{track}/saturation/drive", 1.8))
        if "loud" in p or "limit" in p:
            moves.append((f"/track/{track}/limiter/gain", 3.0))

    # Relative gain / fader adjustments using Track Agent-Memory state
    if "fader" in p or "volume" in p or "level" in p or "boost" in p or "cut" in p:
        target_name = best_track(available_tracks)
        current_fader = 0.0
        if memory_hub and target_name in memory_hub.tracks:
            current_fader = memory_hub.tracks[target_name].fader

        # Parse relative dB delta if present
        db_match = re.search(r'([+-]?\d+(?:\.\d+)?)\s*(?:db)?', p)
        delta = float(db_match.group(1)) if db_match else 2.0
        if "lower" in p or "reduce" in p or "cut" in p:
            delta = -abs(delta)
        else:
            delta = abs(delta)

        new_fader = current_fader + delta
        moves.append((f"/track/{target_name}/fader", new_fader))

    # Natural Language Undo / Revert handling
    if "undo" in p or "revert" in p:
        if memory_hub:
            reverted = memory_hub.undo_last_action()
            if reverted:
                logging.info(f"Reverted {len(reverted)} moves from previous action.")
                return [(p, clamp_parameter(p, v)) for p, v in reverted]

    # Fallback default if nothing matched
    if not moves:
        track = available_tracks[0] if available_tracks else "master"
        moves.append((f"/track/{track}/eq/high_shelf", 1.5))
        moves.append((f"/track/{track}/compressor/threshold", -10.0))

    final_moves = [(path, clamp_parameter(path, val)) for path, val in moves]

    # Record action in session memory
    if memory_hub:
        try:
            memory_hub.record_action("ai_mixing_assistant", prompt_text, final_moves)
        except Exception:
            pass

    return final_moves


def parse_prompt_to_mix_moves(prompt_text, api_key=None, base_url=None, session_path=None):
    """
    Parses user prompt into mixing moves.
    Attempts LLM inference if credentials exist, falling back to offline acoustic heuristic engine.
    """
    available_tracks = discover_session_tracks(session_path)
    logging.info(f"Targeting active session tracks: {available_tracks}")

    # Check if OpenAI is available and configured
    use_llm = HAS_OPENAI and (api_key or os.getenv("OPENAI_API_KEY") or os.getenv("GROQ_API_KEY") or base_url)

    if use_llm:
        try:
            client_kwargs = {}
            if api_key:
                client_kwargs['api_key'] = api_key
            elif not base_url and not os.getenv("OPENAI_API_KEY") and not os.getenv("GROQ_API_KEY"):
                client_kwargs['api_key'] = "local-key"
            if base_url:
                client_kwargs['base_url'] = base_url
                if 'api_key' not in client_kwargs:
                    client_kwargs['api_key'] = "local-key"

            client = OpenAI(**client_kwargs)

            sys_prompt = (
                "You are Bobtrax, an elite autonomous mixing engineer. "
                "Translate the user's natural language mixing request into an exact array of OSC moves. "
                f"\nActive Session Tracks: {', '.join(available_tracks)}"
                f"\nAllowed OSC Schema:\n{AVAILABLE_OSC_SCHEMA}"
                "\nRespond ONLY with valid JSON array: [{\"path\": \"/track/...\", \"value\": 1.0}]"
            )

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": prompt_text}
                ],
                temperature=0.2,
                timeout=8.0
            )

            content = response.choices[0].message.content.strip()
            logging.debug(f"LLM Response: {content}")

            data = json.loads(content)
            if isinstance(data, dict):
                for val in data.values():
                    if isinstance(val, list):
                        data = val
                        break

            if isinstance(data, list):
                parsed = []
                for item in data:
                    p = item.get("path")
                    v = item.get("value")
                    if p and v is not None:
                        parsed.append((p, clamp_parameter(p, v)))
                if parsed:
                    return parsed
        except Exception as e:
            logging.warning(f"LLM inference unavailable or timed out ({e}). Falling back to acoustic heuristic engine.")

    # Offline Heuristic DSP Fallback
    logging.info("Executing Offline Acoustic Heuristic DSP Engine...")
    return heuristic_dsp_rules(prompt_text, available_tracks)


def apply_mix_moves(moves, client):
    """Transmits validated OSC mixing moves to the central OSC Bridge."""
    for osc_path, value in moves:
        logging.info(f"OSC Move Dispatched -> {osc_path} : {value}")
        if client:
            try:
                client.send_message(osc_path, float(value))
            except Exception as e:
                logging.error(f"Failed to transmit OSC {osc_path}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Bobtrax Autonomous AI Mixing Assistant")
    parser.add_argument("prompt", type=str, nargs="?", help="Natural language mixing instruction")
    parser.add_argument("--session", type=str, default=None, help="Path to DAW session file (.ardour or .mmp)")
    parser.add_argument("--osc-ip", default=OSC_BRIDGE_IP, help="Target OSC Bridge IP")
    parser.add_argument("--osc-port", type=int, default=OSC_BRIDGE_PORT, help="Target OSC Bridge port")
    parser.add_argument("--llm-url", type=str, default=None, help="Custom LLM API URL")
    parser.add_argument("--api-key", type=str, default=None, help="LLM API Key")
    parser.add_argument("--dry-run", action="store_true", help="Parse moves without sending OSC")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    if not args.prompt:
        parser.print_help()
        sys.exit(0)

    moves = parse_prompt_to_mix_moves(
        args.prompt,
        api_key=args.api_key,
        base_url=args.llm_url,
        session_path=args.session
    )

    print("\n--- Calculated Mixing Moves ---")
    for path, val in moves:
        print(f"  {path} => {val}")

    if not args.dry_run and HAS_OSC:
        client = SimpleUDPClient(args.osc_ip, args.osc_port)
        apply_mix_moves(moves, client)
        print("\nAll mixing moves successfully transmitted to OSC Bridge.")
    elif args.dry_run:
        print("\nDry-run active. OSC transmission skipped.")
    else:
        print("\npython-osc not installed. OSC transmission simulated.")


if __name__ == "__main__":
    main()
