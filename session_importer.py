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
import time
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
        frozen = route.attrib.get("frozen") == "1"

        # Find gain and pan controls if available
        fader = 0.0
        pan = 0.0
        gain_ctrl = route.find(".//Control[@name='gaincontrol']")
        if gain_ctrl is not None and "value" in gain_ctrl.attrib:
            try:
                fader = float(gain_ctrl.attrib["value"])
            except ValueError:
                pass

        pan_ctrl = route.find(".//Control[@name='pancontrol']")
        if pan_ctrl is not None and "value" in pan_ctrl.attrib:
            try:
                pan = float(pan_ctrl.attrib["value"])
            except ValueError:
                pass

        imported_tracks[clean_name] = {
            "fader": fader,
            "pan": pan,
            "muted": muted,
            "soloed": soloed,
            "frozen": frozen
        }

        if memory_hub:
            t = memory_hub.get_or_create_track(clean_name)
            t.fader = fader
            t.pan = pan
            t.muted = muted
            t.soloed = soloed
            t.frozen = frozen
            t.update_parameter("fader", fader)
            t.update_parameter("pan", pan)

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
        frozen = track.attrib.get("frozen") == "1"
        pan_raw = track.attrib.get("pan", "0")
        try:
            pan = float(pan_raw) / 100.0
        except ValueError:
            pan = 0.0

        imported_tracks[clean_name] = {
            "fader": 0.0,
            "pan": pan,
            "muted": muted,
            "soloed": soloed,
            "frozen": frozen
        }

        if memory_hub:
            t = memory_hub.get_or_create_track(clean_name)
            t.pan = pan
            t.muted = muted
            t.soloed = soloed
            t.frozen = frozen
            t.update_parameter("pan", pan)

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


def import_checkpoint_bundle(bundle_path, mem=None, overwrite_existing=True):
    """Imports packaged checkpoints and branch lineages from a JSON bundle into session memory."""
    import session_memory
    target_mem = mem or session_memory.SessionMemory()

    with open(bundle_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cps = data.get("checkpoints", {})
    imported_count = 0

    for name, cp_info in cps.items():
        if name in target_mem.checkpoints and not overwrite_existing:
            continue

        target_mem.checkpoints[name] = {
            "timestamp": cp_info.get("timestamp", time.time()),
            "time_str": cp_info.get("time_str", time.strftime("%Y-%m-%d %H:%M:%S")),
            "tag": cp_info.get("tag", "imported_bundle"),
            "parent_checkpoint_id": cp_info.get("parent_checkpoint_id"),
            "snapshot": cp_info.get("snapshot", {})
        }
        imported_count += 1

    target_mem._save()
    return {
        "status": "success",
        "bundle_generator": data.get("generator"),
        "checkpoints_imported": imported_count,
        "total_checkpoints_in_session": len(target_mem.checkpoints)
    }


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
