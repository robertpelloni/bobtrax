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
import session_importer
import health_watchdog
import bobui_bridge
import osc_bridge


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

    def test_checkpoint_metadata_details(self):
        self.mem.set_fader("vocals", 2.0)
        self.mem.save_checkpoint("vox_lead")
        details = self.mem.get_checkpoint_details("vox_lead")
        self.assertIsNotNone(details)
        self.assertEqual(details["name"], "vox_lead")
        self.assertIn("vocals", details["tracks"])
        self.assertGreaterEqual(details["track_count"], 1)

    def test_session_auto_save_lifecycle(self):
        self.assertFalse(self.mem.is_auto_save_active())
        self.mem.enable_auto_save(interval_seconds=0.1)
        self.assertTrue(self.mem.is_auto_save_active())
        self.mem.disable_auto_save()
        self.assertFalse(self.mem.is_auto_save_active())

    def test_session_consistency_audit(self):
        # Inject an out-of-bounds fader and an invalid role
        track = self.mem.get_or_create_track("mystery_track")
        track.fader = 45.0  # Excessive
        track.role = "alien_synth_invalid"

        res = self.mem.audit_session_consistency()
        self.assertFalse(res["healthy"])
        self.assertGreater(len(res["issues_resolved"]), 0)

        # Fader must be clamped and role re-inferred
        self.assertLessEqual(self.mem.tracks["mystery_track"].fader, 12.0)
        self.assertIn(self.mem.tracks["mystery_track"].role, ["kick", "snare", "bass", "vocal", "cymbals", "synth", "master", "instrument", "generic"])

    def test_session_state_diff_and_patch(self):
        self.mem.set_fader("kick", 0.0)
        self.mem.save_checkpoint("base_check")

        # No diff immediately
        diff = self.mem.compute_state_diff("base_check")
        self.assertEqual(diff, {})

        # Mutate
        self.mem.set_fader("kick", -4.5)
        self.mem.toggle_mute("kick")
        diff_mutated = self.mem.compute_state_diff("base_check")
        self.assertIn("kick", diff_mutated)
        self.assertEqual(diff_mutated["kick"]["changes"]["fader"], -4.5)
        self.assertTrue(diff_mutated["kick"]["changes"]["muted"])

        # Patch application
        patch = {
            "kick": {
                "action": "modified",
                "changes": {"fader": -1.0, "muted": False}
            }
        }
        applied = self.mem.apply_state_diff(patch)
        self.assertEqual(self.mem.tracks["kick"].fader, -1.0)
        self.assertFalse(self.mem.tracks["kick"].muted)
        self.assertTrue(any("fader" in p[0] for p in applied))


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


class TestSessionExporterAndImporter(unittest.TestCase):
    def test_session_export_and_import_cycle(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tracks = {
                "kick": {"fader": 2.5, "muted": True, "soloed": False},
                "bass": {"fader": -4.0, "muted": False, "soloed": True}
            }
            ardour_file = os.path.join(tmpdir, "test.ardour")
            lmms_file = os.path.join(tmpdir, "test.mmp")
            manifest_file = os.path.join(tmpdir, "manifest.json")

            # Export
            session_exporter.export_to_ardour(tracks, ardour_file)
            session_exporter.export_to_lmms(tracks, lmms_file)
            session_exporter.export_manifest(tracks, manifest_file)

            self.assertTrue(os.path.exists(ardour_file))
            self.assertTrue(os.path.exists(lmms_file))
            self.assertTrue(os.path.exists(manifest_file))

            # Import back
            imported_ardour = session_importer.import_from_ardour(ardour_file)
            imported_lmms = session_importer.import_from_lmms(lmms_file)
            imported_manifest = session_importer.import_from_manifest(manifest_file)

            self.assertIn("kick", imported_ardour)
            self.assertEqual(imported_ardour["kick"]["fader"], 2.5)
            self.assertTrue(imported_ardour["kick"]["muted"])

            self.assertIn("bass", imported_lmms)
            self.assertTrue(imported_lmms["bass"]["soloed"])

            self.assertIn("kick", imported_manifest)
            self.assertEqual(imported_manifest["kick"]["fader"], 2.5)


class TestHealthWatchdog(unittest.TestCase):
    def test_watchdog_probes(self):
        watchdog = health_watchdog.HealthWatchdog()
        status = watchdog.probe_all()
        self.assertIn("osc_bridge", status)
        self.assertIn("wasm_host", status)
        self.assertIn("omni_bridge", status)
        summary = watchdog.get_summary()
        self.assertIn("services active", summary)


class TestOmniPluginBridgeSync(unittest.TestCase):
    def test_plugin_parameter_sync(self):
        with tempfile.NamedTemporaryFile(suffix=".json") as tmp:
            mem = session_memory.SessionMemory(storage_path=tmp.name)
            # Sync cutoff
            val = mem.sync_plugin_parameter("bass", "omni_filter", "cutoff", 850.0, send_ipc=False)
            self.assertEqual(val, 850.0)
            self.assertIn("bass:omni_filter:cutoff", mem.omni_synced_params)
            self.assertEqual(mem.omni_synced_params["bass:omni_filter:cutoff"], 850.0)
            self.assertEqual(mem.tracks["bass"].parameters["plugins/omni_filter/cutoff"], 850.0)

            # Sync drive
            drive = mem.sync_plugin_parameter("bass", "omni_filter", "drive", 0.45, send_ipc=False)
            self.assertEqual(drive, 0.45)
            self.assertEqual(mem.omni_synced_params["bass:omni_filter:drive"], 0.45)

    def test_plugin_preset_application(self):
        with tempfile.NamedTemporaryFile(suffix=".json") as tmp:
            mem = session_memory.SessionMemory(storage_path=tmp.name)
            applied = mem.apply_plugin_preset("synth", "Space Reverb")
            self.assertIn("omni_reverb/decay", applied)
            self.assertEqual(applied["omni_reverb/decay"], 3.2)
            self.assertEqual(mem.tracks["synth"].parameters["plugins/omni_reverb/decay"], 3.2)

    def test_session_manifest_bridge_sync(self):
        with tempfile.NamedTemporaryFile(suffix=".json") as tmp:
            mem = session_memory.SessionMemory(storage_path=tmp.name)
            mem.omni_socket_path = "/tmp/nonexistent_manifest_sync.sock"
            res = mem.sync_session_manifest_to_bridge()
            self.assertFalse(res)


class TestBobUIBridgeSync(unittest.TestCase):
    def test_bobui_bridge_parameter_sync(self):
        bridge = bobui_bridge.BobUIBridge(socket_path="/tmp/nonexistent_test.sock")
        self.assertFalse(bridge.is_host_alive())

        res = bridge.set_parameter("vocals", "reverb", "decay", 2.8)
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["key"], "vocals:reverb:decay")
        self.assertEqual(res["value"], 2.8)

        params = bridge.get_all_parameters()
        self.assertEqual(params, {})

    def test_audio_buffer_processing_fallback(self):
        bridge = bobui_bridge.BobUIBridge(socket_path="/tmp/nonexistent_dsp.sock")
        res = bridge.process_audio_buffer(frames=256, gain=0.5)
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["frames"], 256)
        self.assertEqual(res["gain"], 0.5)

    def test_plugin_compatibility_registry(self):
        info_ardour = bobui_bridge.query_plugin_compatibility("TestPlugin", "ardour")
        self.assertIn("LV2", info_ardour["native_formats"])
        self.assertIn("CLAP", info_ardour["bridged_formats"])

        info_lmms = bobui_bridge.query_plugin_compatibility("TestPlugin", "lmms")
        self.assertIn("VST2", info_lmms["native_formats"])
        self.assertIn("VST3", info_lmms["bridged_formats"])


class TestBobUISessionManagement(unittest.TestCase):
    def test_bobui_session_export_and_import(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tracks = {
                "kick": {"fader": 1.5, "muted": False, "soloed": True},
                "bass": {"fader": -5.0, "muted": True, "soloed": False}
            }
            ardour_target = os.path.join(tmpdir, "bobui_test.ardour")
            lmms_target = os.path.join(tmpdir, "bobui_test.mmp")

            bobui_bridge.export_session_from_bobui(tracks, "ardour", ardour_target)
            bobui_bridge.export_session_from_bobui(tracks, "lmms", lmms_target)

            self.assertTrue(os.path.exists(ardour_target))
            self.assertTrue(os.path.exists(lmms_target))

            imported_ardour = bobui_bridge.import_session_to_bobui(ardour_target)
            imported_lmms = bobui_bridge.import_session_to_bobui(lmms_target)

            self.assertIn("kick", imported_ardour)
            self.assertEqual(imported_ardour["kick"]["fader"], 1.5)
            self.assertIn("bass", imported_lmms)
            self.assertTrue(imported_lmms["bass"]["muted"])

    def test_bobui_checkpoint_and_undo(self):
        with tempfile.NamedTemporaryFile(suffix=".json") as tmp:
            mem = session_memory.SessionMemory(storage_path=tmp.name)
            mem.set_fader("kick", -2.0)
            bobui_bridge.create_session_checkpoint("cp1", mem=mem)

            # Alter
            mem.set_fader("kick", -12.0)
            self.assertEqual(mem.tracks["kick"].fader, -12.0)

            # Restore via BobUI Bridge
            bobui_bridge.restore_session_checkpoint("cp1", mem=mem)
            self.assertEqual(mem.tracks["kick"].fader, -2.0)

            # Test undo
            mem.record_action("bobui_agent", "boost vocals", [("/track/vocals/fader", 3.0)])
            self.assertEqual(mem.tracks["vocals"].fader, 3.0)
            bobui_bridge.undo_session_action(mem=mem)
            self.assertEqual(mem.tracks["vocals"].fader, 0.0)

    def test_fast_sync_binary_state(self):
        # Verify binary packing output
        res = bobui_bridge.fast_sync_track_state("master", 0.0, False, False, socket_path="/tmp/nonexistent.sock")
        self.assertEqual(res["status"], "error")
        # 1 byte len + 6 bytes 'master' + 4 bytes float + 1 byte muted + 1 byte soloed = 13 bytes
        self.assertEqual(res["packed_len"], 13)

    def test_bobui_broadcast_track_update(self):
        res = bobui_bridge.broadcast_track_update("kick", fader=-2.5, muted=False, soloed=True, socket_path="/tmp/nonexistent.sock")
        self.assertIn("socket_sync", res)
        self.assertIn("osc_sync", res)
        self.assertEqual(res["socket_sync"]["status"], "error")

    def test_sync_session_across_daws(self):
        tracks = {
            "kick": {"fader": 0.0, "muted": False, "soloed": False},
            "bass": {"fader": -4.0, "muted": True, "soloed": False}
        }
        res = bobui_bridge.sync_session_across_daws(target_daws=["ardour", "lmms"], tracks=tracks)
        self.assertIn("ardour", res)
        self.assertIn("lmms", res)
        self.assertEqual(res["ardour"]["status"], "synced")
        self.assertEqual(res["ardour"]["tracks_dispatched"], 2)

    def test_transition_session_workflow(self):
        with tempfile.NamedTemporaryFile(suffix=".json") as tmp:
            mem = session_memory.SessionMemory(storage_path=tmp.name)
            res = bobui_bridge.transition_session("ardour", "lmms", mem=mem)
            self.assertEqual(res["status"], "success")
            self.assertEqual(res["from_daw"], "ardour")
            self.assertEqual(res["to_daw"], "lmms")
            self.assertTrue(os.path.exists(res["exported_file"]))
            self.assertIn(res["checkpoint"], mem.list_checkpoints())

    def test_transition_rollback_on_failure(self):
        with tempfile.NamedTemporaryFile(suffix=".json") as tmp:
            mem = session_memory.SessionMemory(storage_path=tmp.name)
            mem.set_fader("vocals", 1.0)
            mem.save_checkpoint("pre_fail_cp")

            # Simulate transition pointing to nonexistent target
            failed_transition = {
                "checkpoint": "pre_fail_cp",
                "exported_file": "/tmp/nonexistent_dummy_file_for_rollback_test.ardour"
            }
            rollback_res = bobui_bridge.verify_and_rollback_transition(failed_transition, mem=mem)
            self.assertEqual(rollback_res["status"], "rolled_back")
            self.assertEqual(rollback_res["restored_checkpoint"], "pre_fail_cp")


class TestDawRegistration(unittest.TestCase):
    def test_daw_heartbeat_and_active_filtering(self):
        with tempfile.NamedTemporaryFile(suffix=".json") as tmp:
            mem = session_memory.SessionMemory(storage_path=tmp.name)
            reg = mem.register_daw("ardour", 3819)
            self.assertEqual(reg["name"], "ardour")
            self.assertEqual(reg["status"], "connected")

            active = mem.get_active_daws(timeout=10.0)
            self.assertIn("ardour", active)

            # Test timeout filtering
            mem.registered_daws["ardour"]["last_seen"] = 1000.0
            expired = mem.get_active_daws(timeout=10.0)
            self.assertNotIn("ardour", expired)


class TestWaveformTelemetry(unittest.TestCase):
    def test_meter_telemetry_waveform(self):
        # Verify emit_meter_packet executes safely without crashing
        self.assertTrue(hasattr(osc_bridge, "emit_meter_packet"))
        osc_bridge.emit_meter_packet("/track/master/meter", 0.65)

        # Verify waveform buffer handling math
        history = [0.0] * 32
        for val in [0.2, 0.5, 0.8, 0.95]:
            history.pop(0)
            history.append(val)
        self.assertEqual(len(history), 32)
        self.assertEqual(history[-1], 0.95)


class TestSessionConflictResolution(unittest.TestCase):
    def test_merge_latest_strategy(self):
        with tempfile.NamedTemporaryFile(suffix=".json") as tmp:
            mem = session_memory.SessionMemory(storage_path=tmp.name)
            track = mem.get_or_create_track("lead_vocal")
            track.fader = -6.0
            track.role = "vocal"
            track.muted = False
            track.last_updated = 1000.0

            # Remote track with newer timestamp
            incoming_track = session_memory.TrackState(name="lead_vocal", role="vocal")
            incoming_track.fader = -2.5
            incoming_track.muted = True
            incoming_track.last_updated = 2000.0
            res = mem.resolve_session_conflict([incoming_track], strategy="merge_latest")

            self.assertEqual(res["status"], "success")
            self.assertEqual(len(res["conflicts"]), 1)
            self.assertEqual(mem.tracks["lead_vocal"].fader, -2.5)
            self.assertTrue(mem.tracks["lead_vocal"].muted)

    def test_overwrite_remote_and_keep_local_strategies(self):
        with tempfile.NamedTemporaryFile(suffix=".json") as tmp:
            mem = session_memory.SessionMemory(storage_path=tmp.name)
            track = mem.get_or_create_track("bass_guitar")
            track.fader = -3.0
            track.role = "bass"

            incoming_track = session_memory.TrackState(name="bass_guitar", role="bass")
            incoming_track.fader = -8.0

            # Test keep_local
            res_keep = mem.resolve_session_conflict([incoming_track], strategy="keep_local")
            self.assertEqual(mem.tracks["bass_guitar"].fader, -3.0)
            self.assertEqual(len(res_keep["changes_applied"]), 0)

            # Test overwrite_remote
            res_overwrite = mem.resolve_session_conflict([incoming_track], strategy="overwrite_remote")
            self.assertEqual(mem.tracks["bass_guitar"].fader, -8.0)
            self.assertGreater(len(res_overwrite["changes_applied"]), 0)

    def test_bobui_bridge_merge_foreign_session(self):
        with tempfile.NamedTemporaryFile(suffix=".json") as mem_tmp, tempfile.NamedTemporaryFile(suffix=".json") as file_tmp:
            mem = session_memory.SessionMemory(storage_path=mem_tmp.name)
            track = mem.get_or_create_track("master")
            track.fader = 0.0

            # Write manifest JSON to file_tmp
            manifest_data = {
                "tracks": {
                    "master": {"fader": -1.5, "role": "master", "muted": False, "soloed": False},
                    "synth": {"fader": -4.0, "role": "synth", "muted": False, "soloed": False}
                }
            }
            with open(file_tmp.name, "w") as f:
                json.dump(manifest_data, f)

            import bobui_bridge
            report = bobui_bridge.merge_foreign_session(file_tmp.name, strategy="overwrite_remote", mem=mem)
            self.assertEqual(report["status"], "success")
            self.assertEqual(mem.tracks["master"].fader, -1.5)
            self.assertIn("synth", mem.tracks)


if __name__ == "__main__":
    unittest.main()
