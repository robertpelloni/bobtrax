#!/usr/bin/env python3
"""
Bobtrax Cross-DAW Session Exporter & Interchange Engine

Exports Track Agent-Memory states into native project formats:
1. Ardour Session XML (.ardour)
2. LMMS Project XML (.mmp)
3. Universal Multi-Track Manifest JSON
"""

import json
import os
import time
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom


def prettify_xml(elem):
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def export_to_ardour(tracks, output_path, markers=None):
    """Generates an Ardour session XML template from active tracks and timeline markers."""
    session = ET.Element("Session", {
        "version": "7.0.0",
        "name": os.path.splitext(os.path.basename(output_path))[0],
        "sample-rate": "48000"
    })

    if markers:
        locations = ET.SubElement(session, "Locations")
        for idx, m in enumerate(markers):
            pos_samples = int(m.get("position", 0.0) * 48000)
            ET.SubElement(locations, "Location", {
                "id": str(1000 + idx),
                "name": m.get("name", f"Marker_{idx}"),
                "start": str(pos_samples),
                "end": str(pos_samples),
                "flags": "IsMark",
                "locked": "no"
            })

    routes = ET.SubElement(session, "Routes")

    # Master Bus
    ET.SubElement(routes, "Route", {
        "name": "Master",
        "default-type": "audio",
        "flags": "MasterOut",
        "muted": "0",
        "soloed": "0"
    })

    for t_name, t_state in tracks.items():
        if t_name == "master":
            continue
        fader = getattr(t_state, "fader", 0.0) if hasattr(t_state, "fader") else t_state.get("fader", 0.0)
        pan = getattr(t_state, "pan", 0.0) if hasattr(t_state, "pan") else t_state.get("pan", 0.0)
        muted = getattr(t_state, "muted", False) if hasattr(t_state, "muted") else t_state.get("muted", False)
        soloed = getattr(t_state, "soloed", False) if hasattr(t_state, "soloed") else t_state.get("soloed", False)
        frozen = getattr(t_state, "frozen", False) if hasattr(t_state, "frozen") else t_state.get("frozen", False)

        route = ET.SubElement(routes, "Route", {
            "name": t_name.capitalize(),
            "default-type": "audio",
            "muted": "1" if muted else "0",
            "soloed": "1" if soloed else "0",
            "frozen": "1" if frozen else "0"
        })
        controls = ET.SubElement(route, "Controls")
        ET.SubElement(controls, "Control", {
            "name": "gaincontrol",
            "value": str(fader)
        })
        ET.SubElement(controls, "Control", {
            "name": "pancontrol",
            "value": str(pan)
        })

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(prettify_xml(session))
    return output_path


def export_to_lmms(tracks, output_path, markers=None):
    """Generates an LMMS project XML (.mmp) from active tracks and timeline markers."""
    lmms_project = ET.Element("lmms-project", {
        "version": "1.3.0",
        "creator": "Bobtrax Omni-Workspace",
        "type": "song"
    })
    head = ET.SubElement(lmms_project, "head", {"bpm": "120", "mastervol": "100"})
    song = ET.SubElement(lmms_project, "song")

    if markers:
        timeline = ET.SubElement(song, "timeline")
        for idx, m in enumerate(markers):
            ET.SubElement(timeline, "marker", {
                "name": m.get("name", f"Marker_{idx}"),
                "pos": str(int(m.get("position", 0.0) * 192)),
                "type": m.get("type", "cue")
            })

    trackcontainer = ET.SubElement(song, "trackcontainer")

    for t_name, t_state in tracks.items():
        if t_name == "master":
            continue
        pan = getattr(t_state, "pan", 0.0) if hasattr(t_state, "pan") else t_state.get("pan", 0.0)
        muted = getattr(t_state, "muted", False) if hasattr(t_state, "muted") else t_state.get("muted", False)
        soloed = getattr(t_state, "soloed", False) if hasattr(t_state, "soloed") else t_state.get("soloed", False)
        frozen = getattr(t_state, "frozen", False) if hasattr(t_state, "frozen") else t_state.get("frozen", False)

        ET.SubElement(trackcontainer, "track", {
            "name": t_name.capitalize(),
            "type": "0",  # Instrument track
            "pan": str(int(pan * 100)),
            "muted": "1" if muted else "0",
            "solo": "1" if soloed else "0",
            "frozen": "1" if frozen else "0"
        })

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(prettify_xml(lmms_project))
    return output_path


def export_manifest(tracks, output_path, markers=None):
    """Exports a universal multi-track JSON manifest with arrangement markers."""
    manifest = {
        "generator": "Bobtrax Session Exporter",
        "tracks": {},
        "markers": markers or []
    }
    for t_name, t_state in tracks.items():
        if hasattr(t_state, "to_dict"):
            manifest["tracks"][t_name] = t_state.to_dict()
        else:
            manifest["tracks"][t_name] = t_state

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return output_path


def export_session_diff_patch(checkpoint_a, checkpoint_b, output_path, mem=None):
    """Exports a structured JSON diff patch comparing two checkpoints or checkpoint vs live state."""
    import session_memory
    target_mem = mem or session_memory.SessionMemory()
    diffs = target_mem.compare_session_snapshots(checkpoint_a, checkpoint_b)

    patch_payload = {
        "generator": "Bobtrax Session Diff Exporter",
        "timestamp": time.time(),
        "time_str": time.strftime("%Y-%m-%d %H:%M:%S"),
        "base_checkpoint": checkpoint_a,
        "compare_checkpoint": checkpoint_b or "[Live Current State]",
        "diff_count": len(diffs),
        "differences": diffs
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(patch_payload, f, indent=2)
    return patch_payload


def export_checkpoint_bundle(checkpoint_names=None, output_path=None, mem=None):
    """Packages multiple snapshot checkpoints and their lineages into a portable bundle file."""
    import session_memory
    target_mem = mem or session_memory.SessionMemory()

    cps_to_export = checkpoint_names or list(target_mem.checkpoints.keys())
    bundle_data = {
        "generator": "Bobtrax Checkpoint Bundle Exporter",
        "timestamp": time.time(),
        "time_str": time.strftime("%Y-%m-%d %H:%M:%S"),
        "checkpoint_count": len(cps_to_export),
        "checkpoints": {}
    }

    for name in cps_to_export:
        if name in target_mem.checkpoints:
            cp_data = target_mem.checkpoints[name]
            bundle_data["checkpoints"][name] = {
                "timestamp": cp_data.get("timestamp"),
                "time_str": cp_data.get("time_str"),
                "tag": cp_data.get("tag", "milestone"),
                "parent_checkpoint_id": cp_data.get("parent_checkpoint_id"),
                "lineage": target_mem.get_checkpoint_lineage(name),
                "snapshot": cp_data.get("snapshot", {})
            }

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(bundle_data, f, indent=2)

    return bundle_data


if __name__ == "__main__":
    import session_memory
    mem = session_memory.SessionMemory()
    print("Testing session export...")
    p1 = export_to_ardour(mem.tracks, "/tmp/test_export.ardour")
    p2 = export_to_lmms(mem.tracks, "/tmp/test_export.mmp")
    p3 = export_manifest(mem.tracks, "/tmp/test_manifest.json")
    print(f"Exported: {p1}, {p2}, {p3}")
    print("Session export verified.")
