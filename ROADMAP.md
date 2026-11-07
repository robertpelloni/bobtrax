# Roadmap

## Phase 1: Foundation & Documentation (Current)
- [x] Establish universal LLM instructions.
- [x] Document all submodules, their versions, and project structure.
- [x] Set up comprehensive tracking files (VISION, MEMORY, TODO, IDEAS).

## Phase 2: Integration & Infrastructure
- [x] Implement `bobui` as the universal launcher and interface layer. (bobtrax_launcher Qt app)
- [x] Establish inter-process communication (IPC) or shared state between the DAWs if applicable. (Foundation set via osc_bridge.py)
- [x] Set up automated build pipelines for all submodules.

## Phase 3: AI & Advanced Features
- [x] Implement AI mixing assistant. (Complete with OpenAI/local LLM support and OSC bridge execution)
- [x] Implement stem separation capabilities within `bobui` / `gui_launcher.py`. (Demucs integration with CLI wrapper)
- [x] Port core audio engines to WebAssembly for browser-based collaboration. (Analysis complete, PoC running for LMMS/Zrythm, wasm_host server active)

## Phase 4: Cross-DAW Omni-Plugin Bridge & Autonomous Autopilot
- [x] Scaffold Rust `omni_plugin_bridge` with shared audio buffer IPC and Unix domain sockets.
- [x] Unify complete ecosystem into single-page Omni-Dashboard with System Tray management.
- [x] Integrate automated dependency diagnostics and build orchestrator (`build.sh`).
- [x] Implement headless VST3/CLAP hosting process for real-time plugin buffer streaming. (Scaffolded with PROCESS_AUDIO streaming in omni_plugin_bridge and bobui_bridge)
