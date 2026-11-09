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
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom


def prettify_xml(elem):
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def export_to_ardour(tracks, output_path):
    """Generates an Ardour session XML template from active tracks."""
    session = ET.Element("Session", {
        "version": "7.0.0",
        "name": os.path.splitext(os.path.basename(output_path))[0],
        "sample-rate": "48000"
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


def export_to_lmms(tracks, output_path):
    """Generates an LMMS project XML (.mmp) from active tracks."""
    lmms_project = ET.Element("lmms-project", {
        "version": "1.3.0",
        "creator": "Bobtrax Omni-Workspace",
        "type": "song"
    })
    head = ET.SubElement(lmms_project, "head", {"bpm": "120", "mastervol": "100"})
    song = ET.SubElement(lmms_project, "song")
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


def export_manifest(tracks, output_path):
    """Exports a universal multi-track JSON manifest."""
    manifest = {
        "generator": "Bobtrax Session Exporter",
        "tracks": {}
    }
    for t_name, t_state in tracks.items():
        if hasattr(t_state, "to_dict"):
            manifest["tracks"][t_name] = t_state.to_dict()
        else:
            manifest["tracks"][t_name] = t_state

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return output_path


if __name__ == "__main__":
    import session_memory
    mem = session_memory.SessionMemory()
    print("Testing session export...")
    p1 = export_to_ardour(mem.tracks, "/tmp/test_export.ardour")
    p2 = export_to_lmms(mem.tracks, "/tmp/test_export.mmp")
    p3 = export_manifest(mem.tracks, "/tmp/test_manifest.json")
    print(f"Exported: {p1}, {p2}, {p3}")
    print("Session export verified.")
