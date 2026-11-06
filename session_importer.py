#!/usr/bin/env python3
"""
Bobtrax Cross-DAW Session Importer & Ingestion Engine

Parses project files from foreign DAWs and ingests track structures,
faders, and mute/solo states directly into the Track Agent-Memory Hub:
1. Ardour Session XML (.ardour)
2. LMMS Project XML (.mmp)
3. Universal Multi-Track Manifest (.json)
"""

import json
import logging
import os
import re
import sys
import xml.etree.ElementTree as ET


def import_from_ardour(path, memory_hub=None):
    """Imports routes, gain controls, and mute/solo from an Ardour session XML file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Ardour session file not found: {path}")

    tree = ET.parse(path)
    root = tree.getroot()
    imported_tracks = {}

    for route in root.findall(".//Route"):
        name = route.attrib.get("name", "")
        if not name or route.attrib.get("flags") == "MasterOut" or name.lower() == "master":
            continue

        clean_name = re.sub(r'[^a-zA-Z0-9_-]', '', name).lower()
        muted = route.attrib.get("muted") == "1"
        soloed = route.attrib.get("soloed") == "1"

        # Find gain control if available
        fader = 0.0
        control = route.find(".//Control[@name='gaincontrol']")
        if control is not None and "value" in control.attrib:
            try:
                fader = float(control.attrib["value"])
            except ValueError:
                pass

        imported_tracks[clean_name] = {
            "fader": fader,
            "muted": muted,
            "soloed": soloed
        }

        if memory_hub:
            t = memory_hub.get_or_create_track(clean_name)
            t.fader = fader
            t.muted = muted
            t.soloed = soloed
            t.update_parameter("fader", fader)

    if memory_hub:
        memory_hub._save()

    return imported_tracks


def import_from_lmms(path, memory_hub=None):
    """Imports instrument tracks and states from an LMMS project XML (.mmp) file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"LMMS project file not found: {path}")

    tree = ET.parse(path)
    root = tree.getroot()
    imported_tracks = {}

    for track in root.findall(".//track"):
        name = track.attrib.get("name", "")
        if not name or name.lower() == "master":
            continue

        clean_name = re.sub(r'[^a-zA-Z0-9_-]', '', name).lower()
        muted = track.attrib.get("muted") == "1"
        soloed = track.attrib.get("solo") == "1"

        imported_tracks[clean_name] = {
            "fader": 0.0,
            "muted": muted,
            "soloed": soloed
        }

        if memory_hub:
            t = memory_hub.get_or_create_track(clean_name)
            t.muted = muted
            t.soloed = soloed

    if memory_hub:
        memory_hub._save()

    return imported_tracks


def import_from_manifest(path, memory_hub=None):
    """Imports session structure from a universal JSON arrangement manifest."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Manifest file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    imported_tracks = data.get("tracks", {})
    if memory_hub:
        for t_name, t_data in imported_tracks.items():
            t = memory_hub.get_or_create_track(t_name)
            t.fader = t_data.get("fader", 0.0)
            t.muted = t_data.get("muted", False)
            t.soloed = t_data.get("soloed", False)
            t.parameters = t_data.get("parameters", {})
        memory_hub._save()

    return imported_tracks


def main():
    print("=== Testing Bobtrax Cross-DAW Session Importer ===")
    import session_exporter
    import session_memory

    mem = session_memory.SessionMemory()
    tmp_ardour = "/tmp/probe_importer.ardour"
    tmp_lmms = "/tmp/probe_importer.mmp"
    tmp_manifest = "/tmp/probe_importer.json"

    # Export probe files
    session_exporter.export_to_ardour(mem.tracks, tmp_ardour)
    session_exporter.export_to_lmms(mem.tracks, tmp_lmms)
    session_exporter.export_manifest(mem.tracks, tmp_manifest)

    # Ingest back
    tracks1 = import_from_ardour(tmp_ardour)
    tracks2 = import_from_lmms(tmp_lmms)
    tracks3 = import_from_manifest(tmp_manifest)

    print(f"Imported from Ardour  : {len(tracks1)} tracks")
    print(f"Imported from LMMS    : {len(tracks2)} tracks")
    print(f"Imported from Manifest: {len(tracks3)} tracks")

    assert len(tracks1) >= 6
    assert len(tracks2) >= 6
    assert len(tracks3) >= 7
    print("=== Cross-DAW Session Importer verified successfully! ===")


if __name__ == "__main__":
    main()
