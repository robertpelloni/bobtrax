# Changelog

All notable changes to this project will be documented in this file.

## [1.0.33] - 2026-11-04
### Added
- Cross-DAW Session Importer engine in `session_importer.py` for direct ingestion of Ardour XML (`.ardour`), LMMS XML (`.mmp`), and universal JSON manifests into `session_memory.py`.
- Interactive "Import Session..." dialog in `gui_launcher.py` with automatic mixer strip re-rendering.
- Unit test coverage for the complete session export and import cycle in `tests/test_ecosystem.py`.

## [1.0.32] - 2026-11-04
### Added
- Continuous Background System Health Watchdog daemon in `health_watchdog.py` probing HTTP, TCP, UDP, and Unix socket endpoints with self-healing capabilities.
- Live "WATCHDOG: Active" status badge and automatic background monitoring thread in `gui_launcher.py`.
- Automated test coverage for watchdog diagnostic probes in `tests/test_ecosystem.py`.

## [1.0.50] - 2026-03-30
### Added
- Multi-DAW Session Broadcast Bus (`broadcast_track_update`) in `bobui_bridge.py` dispatching simultaneous low-latency binary frames and normalized OSC to member DAWs.
- Connected channel strip fader and mute/solo callbacks in `gui_launcher.py` to `broadcast_track_update`.
- Automated unit test coverage `test_bobui_broadcast_track_update` in `tests/test_ecosystem.py` (25/25 tests passing).

## [1.0.49] - 2026-03-30
### Added
- Session State Minimal Diff Calculation & Patch Application (`compute_state_diff`, `apply_state_diff`) in `session_memory.py`.
- Exposed incremental patch synchronization in `bobui_bridge.py` and added "Sync Diff to Base" button in `gui_launcher.py`.
- Automated unit test coverage `test_session_state_diff_and_patch` in `tests/test_ecosystem.py` (24/24 tests passing).

## [1.0.48] - 2026-03-30
### Added
- Low-latency binary track state serialization (`serializeTrackStateBinary`, `deserializeTrackStateBinary`) in native C++ `BobUISessionBridge`.
- Python fast-sync binary encoder (`fast_sync_track_state`) in `bobui_bridge.py`.
- Automated unit test coverage `test_fast_sync_binary_state` in `tests/test_ecosystem.py` (23/23 tests passing).

## [1.0.47] - 2026-03-30
### Added
- Session Track Role Re-Inference and Consistency Check (`audit_session_consistency`, `reclassify_track_roles`) in `session_memory.py`.
- Exposed session consistency audit in `bobui_bridge.py` and added "Audit Consistency" tool button in `gui_launcher.py`.
- Automated unit test coverage `test_session_consistency_audit` in `tests/test_ecosystem.py` (22/22 tests passing).

## [1.0.46] - 2026-03-30
### Added
- Background Session Auto-Save Daemon (`enable_auto_save`, `disable_auto_save`) in `session_memory.py` periodically persisting state and broadcasting manifests.
- Auto-Save toggle checkbox and clean shutdown handling in OmniDashboard (`gui_launcher.py`).
- Automated unit test coverage `test_session_auto_save_lifecycle` in `tests/test_ecosystem.py` (21/21 tests passing).

## [1.0.45] - 2026-03-30
### Added
- Checkpoint metadata inspector `get_checkpoint_details` in `session_memory.py`.
- Interactive Checkpoint Restore dialog and "Restore Checkpoint..." browser in `gui_launcher.py`.
- Automated unit test coverage `test_checkpoint_metadata_details` in `tests/test_ecosystem.py` (20/20 tests passing).

## [1.0.44] - 2026-03-30
### Added
- Cross-DAW Session Manifest Auto-Sync (`sync_session_manifest_to_bridge`) in `session_memory.py` pushing track architectures to the Omni-Plugin Host over IPC (`SYNC_MANIFEST`).
- Interactive "Sync to Bridge" button in the Track Agent-Memory Hub section of `gui_launcher.py`.
- Automated unit test coverage `test_session_manifest_bridge_sync` in `tests/test_ecosystem.py` (19/19 tests passing).

## [1.0.43] - 2026-03-30
### Added
- Extended native C++ `BobUISessionBridge` (`saveCheckpoint`, `restoreCheckpoint`, `undoLastAction`) in `bobui_bridge/bobui_session_bridge.hpp` / `.cpp`.
- Python BobUI Bridge checkpoint and undo helpers (`create_session_checkpoint`, `restore_session_checkpoint`, `undo_session_action`) in `bobui_bridge.py`.
- Automated unit test coverage `test_bobui_checkpoint_and_undo` in `tests/test_ecosystem.py` (18/18 tests passing).

## [1.0.42] - 2026-03-30
### Added
- Comprehensive BobUI Architecture & Cross-DAW Integration Specification in `bobui/BOBUI_INTEGRATION.md` detailing shared audio buffers, preset repository, asset caching, and member DAW integration points.
- Linked integration documentation in `Manual.md` and verified documentation integrity via `generate_docs.py`.

## [1.0.41] - 2026-03-30
### Added
- Out-of-process audio DSP buffer streaming protocol (`PROCESS_AUDIO <frames> <gain>`) in Rust `omni_plugin_bridge`.
- Python buffer streaming method `process_audio_buffer` in `bobui_bridge.py`.
- Interactive "Probe DSP Block" test button in OmniDashboard (`gui_launcher.py`).
- Automated unit test coverage `test_audio_buffer_processing_fallback` in `tests/test_ecosystem.py` (17/17 tests passing).

## [1.0.40] - 2026-03-30
### Added
- Multi-DAW Heartbeat Registration and Active Tracking (`register_daw`, `get_active_daws`) in `session_memory.py`.
- Dynamic DAW status indicators (ACTIVE / STANDBY) for Ardour, LMMS, MusE, and Zrythm inside OmniDashboard (`gui_launcher.py`).
- Automated unit test coverage `TestDawRegistration` in `tests/test_ecosystem.py` (16/16 tests passing).

## [1.0.39] - 2026-03-30
### Added
- Native C++ session management bridge (`bobui_bridge/bobui_session_bridge.hpp`, `bobui_bridge/bobui_session_bridge.cpp`) supporting Ardour and LMMS XML import/export.
- High-level BobUI session helpers (`export_session_from_bobui`, `import_session_to_bobui`) in `bobui_bridge.py`.
- Automated unit test suite `TestBobUISessionManagement` in `tests/test_ecosystem.py` (15/15 tests passing).

## [1.0.38] - 2026-03-30
### Added
- Multi-parameter Omni-Plugin preset manager (`PLUGIN_PRESETS` and `apply_plugin_preset`) in `session_memory.py`.
- Interactive preset browser dropdown and "Apply Preset" dispatcher in OmniDashboard (`gui_launcher.py`).
- Automated unit test coverage `test_plugin_preset_application` in `tests/test_ecosystem.py` (14/14 tests passing).

## [1.0.37] - 2026-03-30
### Added
- Real-Time Audio Envelope & Waveform History Sparkline visualization inside `gui_launcher.py` Canvas VU meter.
- Explicit meter routing helper `emit_meter_packet` in `osc_bridge.py` dispatching `[METER]` telemetry over UDP.
- Automated unit test suite `TestWaveformTelemetry` in `tests/test_ecosystem.py` (13/13 tests passing).

## [1.0.36] - 2026-03-30
### Added
- Native C++ BobUI Omni-Plugin Bridge Adapter (`bobui_bridge/bobui_omni_adapter.hpp`, `bobui_bridge/bobui_omni_adapter.cpp`) implementing POSIX Unix domain socket client communication with the Rust Omni-Plugin Host.
- Python Gateway for BobUI Bridge (`bobui_bridge.py`) providing high-level `BobUIBridge` and `verify_omni_connection`.
- Unit test coverage `TestBobUIBridgeSync` in `tests/test_ecosystem.py` (12/12 unit tests passing).

## [1.0.35] - 2026-03-30
### Added
- Real-Time Omni-Plugin Bridge Live IPC synchronizer in `omni_plugin_bridge/src/lib.rs` and `omni_plugin_bridge/src/bin/omni_host.rs` supporting thread-safe synchronized parameter maps and command streaming (`SET`, `GET_ALL`).
- Inter-DAW plugin parameter sync methods (`sync_plugin_parameter`, `_send_omni_ipc`) in `session_memory.py`.
- Interactive Omni-Plugin Live Sync controls in `gui_launcher.py` with Cutoff and Drive sliders and real-time OSC & IPC broadcast.
- Automated unit test suite additions in `tests/test_ecosystem.py` for plugin parameter synchronization (11/11 tests passing).

## [1.0.34] - 2026-03-30
### Added
- System-level dependency integration and discovery in `build.sh` for PCRE2, Harfbuzz, Freetype, Libjpeg, Libpng, DoubleConversion, Mesa/GL, and X11 extensions (`libxrandr-dev`, `libxinerama-dev`, `libxcursor-dev`, `libxi-dev`).
- Custom self-created developer audit tool `/home/jules/self_created_tools/audit_ecosystem.py` verifying full end-to-end repository health, unit tests, cargo tests, and documentation synchronization.
- Build stabilization investigation for `bobui` submodule identifying upstream CMake include paths and Qt library bootstrapping requirements.

## [1.0.31] - 2026-11-04
### Added
- Cross-DAW Session Exporter engine in `session_exporter.py` generating Ardour XML (`.ardour`), LMMS XML (`.mmp`), and universal JSON arrangement manifests.
- "Export Session..." dialog in `gui_launcher.py` under the Track Agent-Memory Hub.
- Automated test cases for session export formats in `tests/test_ecosystem.py`.

## [1.0.30] - 2026-11-04
### Added
- Snapshot Checkpoints (`save_checkpoint()`, `restore_checkpoint()`) and Undo action history (`undo_last_action()`) in `session_memory.py`.
- Natural language undo/revert handling in `ai_assistant/mixing_assistant.py`.
- Interactive "Save Snapshot" and "Undo Last Move" buttons in `gui_launcher.py`.
- Automated test case for checkpoints and undo in `tests/test_ecosystem.py`.

## [1.0.29] - 2026-11-04
### Added
- Unified Python ecosystem test suite in `tests/test_ecosystem.py` covering SessionMemory, AI mixing heuristic rules, stem separation simulation, and WASM host headers.
- Integrated automated test discovery (`python3 -m unittest discover tests`) into `build.sh` verification pipeline.
- Sourced and non-destructive documentation auditing utility in `generate_docs.py`.

## [1.0.28] - 2026-11-04
### Added
- Interactive Multi-Track Console Channel Strips in `gui_launcher.py`: vertical fader sliders (-60dB to +6dB), mini VU meters, and Mute (M) / Solo (S) buttons for each active session track.
- Real-time OSC fader level and mute/solo state broadcasting into `osc_bridge.py`.
- Helper methods `set_fader()`, `toggle_mute()`, and `toggle_solo()` in `session_memory.py`.

## [1.0.27] - 2026-11-04
### Added
- Bidirectional WebSocket gateway connection in WebAssembly Collaboration Portal (`wasm_launcher/index.html`) allowing browser users to command ecosystem transport and monitor incoming telemetry.
- Built-in WebAudio test synthesizer with real-time Canvas oscilloscope visualization.
- "Probe Web Gateway" diagnostic tool in `gui_launcher.py`.

## [1.0.26] - 2026-11-04
### Added
- Stereo Canvas-based VU / Peak Level Meter in `gui_launcher.py` with dynamic color gradient (green/yellow/red) and dBFS readout.
- Live metering packet parsing (`[METER] /track/master/meter:<val>`) in the background UDP telemetry listener.
- Metering event forwarding in `osc_bridge.py` and peak level state tracking in `session_memory.py`.

## [1.0.25] - 2026-11-04
### Added
- Standalone headless plugin host binary `omni_host` (`omni_plugin_bridge/src/bin/omni_host.rs`) that starts an IPC Unix socket server and processes audio buffer blocks across DAWs.
- Enhanced "Test Bridge IPC" in `gui_launcher.py` to probe the standalone host and report real-time audio buffer latency (< 1.2ms).

## [1.0.24] - 2026-11-04
### Added
- Real-time IPC telemetry streaming from `osc_bridge.py` forward-broadcasting all routed and raw packets to `127.0.0.1:8005`.
- Asynchronous UDP telemetry background listener in `gui_launcher.py` live-updating the system telemetry console.
- Quick macro presets in MUSE Command Palette ("Mute All", "Reset Faders", "Solo Vox") with multi-track dispatch.

## [1.0.23] - 2026-11-04
### Changed
- Executed targeted automated builds for `muse`, `zrythm`, and `bobui`.
- Isolated compilation logs for all submodules in `logs/build_muse.log`, `logs/build_zrythm.log`, and `logs/build_bobui.log`.
- Documented exact platform library and compiler requirements:
  - `muse`: Requires Extra CMake Modules (`ECM`).
  - `zrythm`: Requires GCC 14+ compiler.
  - `bobui`: Requires resolving `BobUI6::BundledPcre2` in QtBase fork.
- Maintained 100% test pass rate for `omni_plugin_bridge`, `session_memory.py`, and `verify_bobtrax.py`.

## [1.0.22] - 2026-11-04
### Added
- Automated revision header synthesis (`libs/ardour/revision.cc`) inside `build.sh` to unblock Ardour's Waf configure step.
- Isolated per-submodule build logging (`logs/build_<submodule>.log`) with clean console telemetry.
- Targeted diagnostic runs for `--only-ardour` and `--only-lmms`.

## [1.0.21] - 2026-11-04
### Added
- Created `session_memory.py` implementing the Track Agent-Memory Hub with persistent JSON state storage, track metadata roles, fader gains, parameter maps, and chronological AI action history.
- Integrated `session_memory.py` into `osc_bridge.py` to auto-record real-time track parameter modifications.
- Integrated `session_memory.py` into `ai_assistant/mixing_assistant.py` for state-aware relative fader adjustments and history recording.
- Added visual "Track Agent-Memory & Dynamic State Hub" inspector panel to `gui_launcher.py`.

## [1.0.20] - 2026-11-04
### Changed
- Executed full automated multi-submodule build orchestration (`./build.sh --all`).
- Documented precise compiler and dependency diagnostics across all 5 submodules in `MEMORY.md` and `DEPLOY.md`:
  - `bobui`: `BobUI6::BundledPcre2` dependency issue in QtBase fork.
  - `ardour`: Waf revision generator requiring `git describe` tags to create `libs/ardour/revision.cc`.
  - `lmms`: Requires `Qt5Config.cmake` (5.15.0+).
  - `muse`: Requires KDE Extra CMake Modules (`ECM`).
  - `zrythm`: Requires GCC 14+ (environment currently has GCC 13.3).
  - `omni_plugin_bridge`: 100% build and test success in Rust.
  - Subsystem verification tool passes all tests.

## [1.0.19] - 2026-11-04
### Added
- Dynamic DAW session track discovery in `ai_assistant/mixing_assistant.py` supporting Ardour XML (`.ardour`), LMMS XML (`.mmp`), and environment variable overrides (`BOBTRAX_TRACKS`).
- Offline Acoustic Heuristic DSP Rule Engine in `mixing_assistant.py` that translates natural language mixing moves to concrete OSC parameters completely offline without external API keys.
- Parameter boundary validation and safe clamping on all generated OSC mixing paths.
- "Scan DAW Session" button and track inspection tools in the Omni-Dashboard (`gui_launcher.py`).

## [1.0.18] - 2026-11-04
### Added
- Complete single-page redesign of the Bobtrax Omni-Dashboard (`gui_launcher.py`) with high-value prioritization, live service status badges, quick transport shortcuts, and comprehensive safe ToolTip annotations.
- Full System Tray integration using `pystray` with graceful fallback for headless displays, providing background daemon controls (Show/Hide, Start All Servers, Stop All Servers, Open Browser, Quit Bobtrax).
- Background server lifecycle controls for WebAssembly Collaboration Server (`wasm_host.py`), Central OSC Bridge (`osc_bridge.py`), and WebSocket-to-OSC Gateway (`osc_web_wrapper.py`).
- Standalone helper module `wasm_host.py` with CORS/SharedArrayBuffer headers for browser audio worklets.
- Standalone helper module `stem_separator.py` wrapping Demucs with model selection, GPU toggle, and high-fidelity simulated fallback.
- Added user manual `Manual.md` detailing end-to-end operation of all ecosystem components.
- Automated dependency diagnostics (`./build.sh --check-deps`) and submodule build orchestration in `build.sh`.

### Changed
- Refactored `omni_plugin_bridge/src/lib.rs` to remove unused `UnixStream` import, ensuring clean compiler output during `cargo test`.
- Corrected `.gitignore` to allow required Python helper tools.
- Updated all governance documents (`MEMORY.md`, `HANDOFF.md`, `ROADMAP.md`, `TODO.md`, `DEPLOY.md`, `IDEAS.md`).

## [1.0.16] - 2026-06-30
### Added
- Created `build_wasm.sh` to compile core audio engines (LMMS) to WebAssembly via Emscripten.
- Added `wasm_launcher/index.html` to serve as a browser-based frontend for interacting with the WASM engines.
- Created `WasmAudioEngine.cpp` in `lmms/src/core` with Emscripten `--bind` exports and updated CMake logic.
- Implemented `wasm_host.py` and `wasm_panel.py` in `bobui/src/bobtrax_launcher` to allow `bobui` to spawn a local web server for the WebAssembly frontend.


## [1.0.15] - 2026-04-16
### Added
- Added stem separation wrapper using Demucs in bobui/src/bobtrax_launcher/stem_separator.py.

## [1.0.13] - 2026-04-16
### Changed
- Rewrote `mixing_assistant.py` to remove hardcoded mixing templates. It now utilizes the `openai` python package to ping remote APIs (or local APIs via `--llm-url`) to autonomously parse user intent into JSON arrays of OSC moves.
- Added dynamic system prompt logic to `mixing_assistant.py` to inject current track state and OSC schema.
- Marked off LLM Phase 3 tasks as completed in `TODO.md`.

## [1.0.9] - 2026-04-16
### Changed
- Configured Ardour's native OSC control surface to connect to `127.0.0.1:8000` via user configuration (`~/.config/ardour6/config`).

## [1.0.12] - 2026-04-16
### Changed
- Conclusively verified Ardour's native OSC surface configuration defaults perfectly to `osc_bridge.py` via `127.0.0.1:8000` without manual config interventions.
- Checked off the final Phase 2 TODO item.

## [1.0.11] - 2026-04-16
### Added
- Initiated Phase 3 by adding `ai_assistant/mixing_assistant.py`. This script serves as a foundational proof-of-concept for translating natural language prompts into OSC mixing commands.
- Updated `ROADMAP.md` and added concrete next-step tasks to `TODO.md` regarding LLM integration.

## [1.0.10] - 2026-04-16
### Added
- Created `bobtrax_launcher` within `bobui` source tree. This is a native Qt/C++ GUI launcher that replaces the interim python scripts.
- Integrated `bobtrax_launcher` into `bobui/src/CMakeLists.txt`.
- Marked the 'bobui universal launcher' milestone complete in `ROADMAP.md`.

## [1.0.9] - 2026-04-13
### Changed
- Verified Ardour's native OSC surface configuration defaults map perfectly to the central `osc_bridge.py` port `8000`.
- Marked the final Phase 2 TODO item as completed.

## [1.0.8] - 2026-04-13
### Added
- Implemented `osc_web_wrapper.py`, a WebSocket server that bridges web payloads (JSON) to OSC messages sent to the central `osc_bridge.py` hub.
- Checked off the WebSocket wrapper task in `TODO.md`.

## [1.0.7] - 2026-04-13
### Added
- Added `INCOMING_MAP` and `OUTGOING_MAP` dictionary routing logic to `osc_bridge.py` to seamlessly translate specific DAW OSC paths into standard commands across the ecosystem.
- Checked off the OSC translation mapping task in `TODO.md`.

## [1.0.6] - 2026-04-12
### Added
- Added `osc_bridge.py` as a foundational proof-of-concept for unified DAW IPC via Open Sound Control.
- Checked off the IPC task in `ROADMAP.md` and created translation tasks in `TODO.md`.

## [1.0.5] - 2026-04-12
### Added
- Added `gui_launcher.py`, a Tkinter-based visual launcher for DAWs.
- Updated `ROADMAP.md` and `TODO.md` marking build pipelines and agent instructions as complete.

## [1.0.4] - 2026-04-11
### Added
- Added `launcher.py` as an interim unified entry point to launch compiled DAWs.
- Checked off UI analysis and wrapper comment tasks in `TODO.md`.

## [1.0.3] - 2026-04-11
### Added
- Added GitHub Actions workflow (`ci.yml`) to automatically check submodule health and compile them.

## [1.0.2] - 2024-04-10
### Added
- Consolidated build script (`build.sh`) for compiling all submodules seamlessly.

## [1.0.1] - 2024-04-10
### Added
- Comprehensive project documentation including AGENTS.md, VISION.md, ROADMAP.md, and more.
- Unified LLM instructions references across model-specific files.
- Documented submodule versions and project structure.
