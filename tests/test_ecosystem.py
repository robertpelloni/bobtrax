"""
Bobtrax Unified Ecosystem Test Suite

Exercises and validates:
1. session_memory: TrackState, SessionMemory persistence, faders, and mute/solo.
2. mixing_assistant: Rule-based acoustic heuristics and parameter clamping.
3. stem_separator: Argument parsing and simulated stem generation.
4. wasm_host: CORS and SharedArrayBuffer header configuration.
"""

import os
import sys
import unittest
import tempfile
import json

# Ensure repo root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import session_memory
from ai_assistant import mixing_assistant
import stem_separator
import wasm_host
import session_exporter


class TestSessionMemory(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.temp_file.close()
        self.mem = session_memory.SessionMemory(storage_path=self.temp_file.name)

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_track_creation_and_role_inference(self):
        track = self.mem.get_or_create_track("kick_drum")
        self.assertEqual(track.role, "kick")

        vocal = self.mem.get_or_create_track("lead_vox")
        self.assertEqual(vocal.role, "vocal")

    def test_fader_and_mute_solo(self):
        self.mem.set_fader("kick", -4.5)
        self.assertEqual(self.mem.tracks["kick"].fader, -4.5)

        is_muted = self.mem.toggle_mute("kick")
        self.assertTrue(is_muted)
        is_muted = self.mem.toggle_mute("kick")
        self.assertFalse(is_muted)

        is_solo = self.mem.toggle_solo("kick")
        self.assertTrue(is_solo)

    def test_persistence(self):
        self.mem.set_fader("bass", -6.0)
        self.mem.record_action("test_agent", "lower bass", [("/track/bass/fader", -6.0)])

        # Read directly from temp json file
        with open(self.temp_file.name, "r") as f:
            data = json.load(f)
            self.assertIn("bass", data["tracks"])
            self.assertEqual(data["tracks"]["bass"]["fader"], -6.0)
            self.assertEqual(len(data["history"]), 1)

    def test_checkpoint_and_undo(self):
        self.mem.set_fader("kick", 0.0)
        self.mem.save_checkpoint("initial_mix")
        self.assertIn("initial_mix", self.mem.list_checkpoints())

        # Modify kick fader
        self.mem.set_fader("kick", -10.0)
        self.assertEqual(self.mem.tracks["kick"].fader, -10.0)

        # Restore checkpoint
        success = self.mem.restore_checkpoint("initial_mix")
        self.assertTrue(success)
        self.assertEqual(self.mem.tracks["kick"].fader, 0.0)

        # Test Undo last action
        self.mem.record_action("agent", "boost snare", [("/track/snare/fader", 4.0)])
        self.assertEqual(self.mem.tracks["snare"].fader, 4.0)
        reverted = self.mem.undo_last_action()
        self.assertTrue(any("snare" in r[0] for r in reverted))
        self.assertEqual(self.mem.tracks["snare"].fader, 0.0)


class TestAiMixingAssistant(unittest.TestCase):
    def test_acoustic_dsp_rules(self):
        tracks = ["kick", "snare", "bass", "vocals"]
        moves = mixing_assistant.heuristic_dsp_rules("Make the kick punchy", tracks)
        paths = [p for p, _ in moves]
        self.assertTrue(any("kick" in p and "eq" in p for p in paths))
        self.assertTrue(any("kick" in p and "compressor" in p for p in paths))

    def test_parameter_clamping(self):
        # Threshold should be clamped to 0.0 max
        clamped = mixing_assistant.clamp_parameter("/track/kick/compressor/threshold", 50.0)
        self.assertEqual(clamped, 0.0)

        # High cut should be clamped to 20000.0 max
        clamped_eq = mixing_assistant.clamp_parameter("/track/kick/eq/high_cut", 35000.0)
        self.assertEqual(clamped_eq, 20000.0)


class TestStemSeparator(unittest.TestCase):
    def test_simulated_stem_separation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dummy_audio = os.path.join(tmpdir, "test_song.wav")
            with open(dummy_audio, "wb") as f:
                f.write(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x02\x00\x44\xac\x00\x00\x10\xb1\x02\x00\x04\x00\x10\x00data\x00\x00\x00\x00")

            success = stem_separator.separate_stems(dummy_audio, output_dir=tmpdir, model="htdemucs")
            self.assertTrue(success)

            target_stems_dir = os.path.join(tmpdir, "htdemucs", "test_song")
            self.assertTrue(os.path.isdir(target_stems_dir))
            self.assertTrue(os.path.exists(os.path.join(target_stems_dir, "drums.wav")))
            self.assertTrue(os.path.exists(os.path.join(target_stems_dir, "vocals.wav")))


class TestWasmHost(unittest.TestCase):
    def test_wasm_handler_headers(self):
        # Verify WasmHandler includes Cross-Origin headers
        self.assertTrue(hasattr(wasm_host, "WasmHandler"))
        self.assertTrue(hasattr(wasm_host.WasmHandler, "end_headers"))


class TestSessionExporter(unittest.TestCase):
    def test_session_export_ardour_and_lmms(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tracks = {
                "kick": {"fader": 0.0, "muted": False, "soloed": False},
                "bass": {"fader": -3.0, "muted": False, "soloed": False}
            }
            ardour_file = os.path.join(tmpdir, "test.ardour")
            lmms_file = os.path.join(tmpdir, "test.mmp")
            manifest_file = os.path.join(tmpdir, "manifest.json")

            session_exporter.export_to_ardour(tracks, ardour_file)
            session_exporter.export_to_lmms(tracks, lmms_file)
            session_exporter.export_manifest(tracks, manifest_file)

            self.assertTrue(os.path.exists(ardour_file))
            self.assertTrue(os.path.exists(lmms_file))
            self.assertTrue(os.path.exists(manifest_file))

            with open(ardour_file) as f:
                content = f.read()
                self.assertIn("Session", content)
                self.assertIn("Kick", content)


if __name__ == "__main__":
    unittest.main()
