# Changelog
All notable changes to this project will be documented in this file.

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
