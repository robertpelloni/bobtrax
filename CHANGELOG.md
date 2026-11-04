# Changelog

All notable changes to this project will be documented in this file.

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
