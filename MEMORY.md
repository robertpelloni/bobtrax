# Memory & Observations

- **Submodules:** The project relies heavily on git submodules for its core engines (Ardour, LMMS, MusE, Zrythm) and UI layer (bobui).
- **Design Preferences:**
  - Strong emphasis on comprehensive, extreme-detail documentation.
  - All LLM interactions must be documented, and instructions must be strictly followed.
  - Version numbers must be synchronized across the project and maintained in a single `VERSION.md` file.
  - Code should be commented in-depth explaining the *why* and *how*.
[PROJECT_MEMORY]

# Project Memory: Bobtrax Omni-Workspace

## 1. Project Architecture & Vision
*   **Monolithic Ecosystem:** Bobtrax is not a single codebase but a meta-project, a unified command center orchestrating multiple major open-source audio workstations (DAWs) as git submodules.
*   **The DAWs:** The current integrated submodules include:
    *   **Ardour** (Waf build system)
    *   **LMMS** (CMake build system)
    *   **MusE Sequencer** (CMake build system)
    *   **Zrythm** (CMake/Meson build system)
*   **The UI Layer (`bobui`):** The repository includes a submodule named `bobui`. Through exploration, it was discovered that `bobui` is currently a direct fork or mirror of **QtBase** (Qt 6 core). The long-term vision is for `bobui` to serve as the universal GUI and launcher for all underlying DAWs.

## 2. Infrastructure & Tooling Decisions
*   **Unified Build System (`build.sh`):** Because the submodules use different build systems (CMake vs. Waf) and require different dependency chains, a top-level `build.sh` script was implemented. It abstracts away the complexity of compiling each DAW individually, offering flags like `--only-ardour` or `--only-lmms`.
*   **Interim Launcher (`launcher.py`):** Since `bobui` does not yet contain custom DAW-launching code, an interim CLI python script (`launcher.py`) was created.
    *   *Design Pattern:* It uses `subprocess.run()` to spawn the compiled DAW binaries as independent child processes. This ensures the launcher can safely close or crash without killing the user's music session.
    *   *Extensibility:* It relies on a centralized `DAW_CONFIG` dictionary mapping CLI arguments to relative binary paths.
*   **Continuous Integration (`ci.yml`):** A GitHub Actions pipeline was implemented to automatically pull all submodules recursively, install a vast array of audio and UI dependencies (ALSA, JACK, GTK3, Sndfile, etc.), and execute the `build.sh` script to ensure branch health on every push.

## 3. Strict Documentation & Versioning Patterns
*   **The Universal Rulebook:** The project mandates extreme adherence to a centralized rulebook (`docs/UNIVERSAL_LLM_INSTRUCTIONS.md`). All AI agents (Claude, Gemini, GPT) must defer to this document.
*   **Single Source of Truth Versioning:** Version numbers are strictly isolated. A `VERSION.md` file holds the absolute current version (e.g., `1.0.4`).
*   **Synchronized Bumping:** Every feature implementation must include:
    1.  Bumping the string in `VERSION.md`.
    2.  Prepending a formatted entry to `CHANGELOG.md`.
    3.  Referencing the new version in the git commit message.
*   **Comprehensive Dashboards:** The project heavily utilizes markdown files to track state:
    *   `TODO.md` for granular, short-term tasks.
    *   `ROADMAP.md` for phase-based, long-term goals.
    *   `PROJECT_STRUCTURE.md` for mapping the submodule ecosystem.
    *   `VISION.md` for the philosophical goals of the project.
    *   `MEMORY.md` & `HANDOFF.md` for AI-to-AI context passing.

## 4. Future Directions (From IDEAS.md)
*   **Cross-DAW Plugin Wrapping:** Creating a bridge to share VST/LV2 plugins simultaneously across LMMS and Ardour.
*   **AI Integration:** Injecting SLMs (Small Language Models) for autonomous stem separation and mixing assistance directly into the `bobui` layer.
*   **WebAssembly Porting:** Exploring compiling the core C/C++ audio engines to WASM for decentralized, browser-based collaboration.
[PROJECT_MEMORY]

# Project Memory: Bobtrax Omni-Workspace

## 1. Project Architecture & Vision
*   **Monolithic Ecosystem:** Bobtrax is a meta-project serving as a unified command center orchestrating multiple major open-source audio workstations (DAWs) through git submodules.
*   **Integrated Submodules:**
    *   **Ardour** (Digital audio workstation, uses Waf)
    *   **LMMS** (Digital audio workstation, uses CMake)
    *   **MusE Sequencer** (MIDI/Audio sequencer, uses CMake)
    *   **Zrythm** (Automated DAW, uses CMake/Meson)
*   **The UI Layer (`bobui`):** A custom UI submodule that is currently a mirror/fork of **QtBase** (Qt 6 core). The long-term vision is for `bobui` to evolve into the unified frontend launcher and interface layer connecting these DAWs together.

## 2. Infrastructure & Tooling Decisions
*   **Unified Build System (`build.sh`):** A bash script at the root abstracts the varying build dependencies (CMake vs. Waf) across the submodules, supporting specific build flags like `--only-lmms` for targeted compilations.
*   **Continuous Integration (`ci.yml`):** A robust GitHub Actions pipeline pulls all submodules recursively, installs heavy audio/UI packages (ALSA, JACK, GTK3, Sndfile, etc.), and executes the unified `build.sh` to prevent regressions.
*   **Interim Launchers (`launcher.py` and `gui_launcher.py`):**
    *   Because `bobui` is currently just QtBase and lacks frontend logic, interim launchers bridge the gap.
    *   `launcher.py` acts as a unified CLI launcher, and `gui_launcher.py` provides a lightweight Tkinter-based graphical window.
    *   *Design Pattern:* Both spawn the compiled DAW binaries as detached child processes via `subprocess.run/Popen`. This insulates the user's music sessions from launcher crashes.

## 3. Strict Documentation & Versioning Patterns
*   **The Universal Rulebook:** The core instructions (`docs/UNIVERSAL_LLM_INSTRUCTIONS.md`) govern all LLM actions (Claude, Gemini, GPT) across the monorepo to ensure consistency.
*   **Single Source of Truth Versioning:** The `VERSION.md` file tracks the single absolute version of the ecosystem (currently `1.0.5`).
*   **Synchronized Update Cycle:** Every feature or task completed requires:
    1. Bumping the semantic version in `VERSION.md`.
    2. Prepending a detailed entry in `CHANGELOG.md`.
    3. Documenting the changes in `TODO.md` and `ROADMAP.md`.
    4. Committing with the version referenced.
*   **Context Passing:** `MEMORY.md` and `HANDOFF.md` act as state-preservation files between sessions and different AI agents.

## 4. Future Directions (From IDEAS.md & ROADMAP.md)
*   **Inter-process Communication (IPC):** Establishing a shared state between the varying DAWs.
*   **Cross-DAW Plugin Wrapping:** Creating a bridge to share VST/LV2 plugins across LMMS, Ardour, etc.
*   **AI Integration:** Injecting Small Language Models (SLMs) for autonomous mixing assistance and stem separation into the `bobui` layer.
*   **WebAssembly Porting:** Exploring WASM compilation of core C/C++ audio engines for browser-based collaboration.
[PROJECT_MEMORY]

# Project Memory: Bobtrax Omni-Workspace

## 1. Project Architecture & Vision
*   **Monolithic Ecosystem:** Bobtrax is a meta-project serving as a unified command center orchestrating multiple major open-source audio workstations (DAWs) through git submodules.
*   **Integrated Submodules:**
    *   **Ardour** (Digital audio workstation, uses Waf)
    *   **LMMS** (Digital audio workstation, uses CMake)
    *   **MusE Sequencer** (MIDI/Audio sequencer, uses CMake)
    *   **Zrythm** (Automated DAW, uses CMake/Meson)
*   **The UI Layer (`bobui`):** A custom UI submodule that is currently a mirror/fork of **QtBase** (Qt 6 core). The long-term vision is for `bobui` to evolve into the unified frontend launcher and interface layer connecting these DAWs together.

## 2. Infrastructure & Tooling Decisions
*   **Unified Build System (`build.sh`):** A bash script at the root abstracts the varying build dependencies (CMake vs. Waf) across the submodules, supporting specific build flags like `--only-lmms` for targeted compilations.
*   **Continuous Integration (`ci.yml`):** A robust GitHub Actions pipeline pulls all submodules recursively, installs heavy audio/UI packages (ALSA, JACK, GTK3, Sndfile, etc.), and executes the unified `build.sh` to prevent regressions on push/PR.
*   **Interim Launchers (`launcher.py` and `gui_launcher.py`):**
    *   Because `bobui` is currently just QtBase and lacks frontend logic, interim launchers bridge the gap.
    *   `launcher.py` acts as a unified CLI launcher, and `gui_launcher.py` provides a lightweight Tkinter-based graphical window.
    *   *Design Pattern:* Both spawn the compiled DAW binaries as detached child processes via Python's `subprocess.Popen`. This insulates the user's audio sessions from launcher crashes.
*   **Inter-Process Communication (IPC) Ecosystem:**
    *   **`osc_bridge.py`:** A centralized UDP router capturing and broadcasting Open Sound Control (OSC) messages across DAWs. Serves as the "Shared State" layer, enabling transport controls (play, stop) to sync across Ardour, MusE, etc. Features `INCOMING_MAP` and `OUTGOING_MAP` dictionaries for robust native dialect translation (e.g. `/ardour/transport_play` -> `/muse/play`).
    *   **`osc_web_wrapper.py`:** A `websockets`-based python server that listens for modern web JSON payloads (`{"action": "play"}`) and translates them into OSC commands fired off to the `osc_bridge.py`. Decouples low-latency audio control from high-level web tech.

## 3. Strict Documentation & Versioning Patterns
*   **The Universal Rulebook:** The core instructions (`docs/UNIVERSAL_LLM_INSTRUCTIONS.md`) govern all LLM actions (Claude, Gemini, GPT) across the monorepo to ensure consistency, with model-specific files (`GPT.md`, `CLAUDE.md`, etc.) pointing back to it.
*   **Single Source of Truth Versioning:** The `VERSION.md` file tracks the single absolute version of the ecosystem (currently `1.0.8`).
*   **Synchronized Update Cycle:** Every feature or task completed requires:
    1. Bumping the semantic version in `VERSION.md`.
    2. Prepending a detailed entry in `CHANGELOG.md`.
    3. Documenting the changes by checking off tasks in `TODO.md` and `ROADMAP.md`.
    4. Committing with the version referenced in the message.
*   **Context Passing:** `MEMORY.md` and `HANDOFF.md` act as mandatory state-preservation files between sessions and different AI agents, ensuring continuity.

## 4. Future Directions (From IDEAS.md, TODO.md & ROADMAP.md)
*   **OSC Surface Configs:** Configuring Ardour (and others) to actually point its native OSC outputs to `127.0.0.1:8000` via automated template configs.
*   **Cross-DAW Plugin Wrapping:** Creating a bridge to share VST/LV2 plugins simultaneously across LMMS, Ardour, etc.
*   **AI Integration:** Injecting Small Language Models (SLMs) for autonomous mixing assistance and stem separation into the `bobui` layer.
*   **WebAssembly Porting:** Exploring WASM compilation of core C/C++ audio engines for decentralized, browser-based collaboration.
[PROJECT_MEMORY]

# Project Memory: Bobtrax Omni-Workspace

## 1. Project Architecture & Vision
*   **Monolithic Ecosystem:** Bobtrax is a meta-project serving as a unified command center orchestrating multiple major open-source audio workstations (DAWs) through git submodules.
*   **Integrated Submodules:**
    *   **Ardour** (Digital audio workstation, uses Waf)
    *   **LMMS** (Digital audio workstation, uses CMake)
    *   **MusE Sequencer** (MIDI/Audio sequencer, uses CMake)
    *   **Zrythm** (Automated DAW, uses CMake/Meson)
*   **The UI Layer (`bobui`):** A custom UI submodule that is currently a mirror/fork of **QtBase** (Qt 6 core). The long-term vision is for `bobui` to evolve into the unified frontend launcher and interface layer connecting these DAWs together.

## 2. Infrastructure & Tooling Decisions
*   **Unified Build System (`build.sh`):** A bash script at the root abstracts the varying build dependencies (CMake vs. Waf) across the submodules, supporting specific build flags like `--only-lmms` for targeted compilations.
*   **Continuous Integration (`ci.yml`):** A robust GitHub Actions pipeline pulls all submodules recursively, installs heavy audio/UI packages (ALSA, JACK, GTK3, Sndfile, etc.), and executes the unified `build.sh` to prevent regressions on push/PR.
*   **Interim Launchers (`launcher.py` and `gui_launcher.py`):**
    *   Because `bobui` is currently just QtBase and lacks frontend logic, interim launchers bridge the gap.
    *   `launcher.py` acts as a unified CLI launcher, and `gui_launcher.py` provides a lightweight Tkinter-based graphical window.
    *   *Design Pattern:* Both spawn the compiled DAW binaries as detached child processes via Python's `subprocess.Popen`. This insulates the user's audio sessions from launcher crashes.
*   **Inter-Process Communication (IPC) Ecosystem:**
    *   **`osc_bridge.py`:** A centralized UDP router capturing and broadcasting Open Sound Control (OSC) messages across DAWs. Serves as the "Shared State" layer, enabling transport controls (play, stop) to sync across Ardour, MusE, etc. Features `INCOMING_MAP` and `OUTGOING_MAP` dictionaries for robust native dialect translation (e.g. `/ardour/transport_play` -> `/muse/play`). Codebase analysis verified Ardour natively targets `127.0.0.1:8000` via its control surface logic, meaning out-of-the-box it hooks directly into this bridge without configuration hacking.
    *   **`osc_web_wrapper.py`:** A `websockets`-based python server that listens for modern web JSON payloads (`{"action": "play"}`) and translates them into OSC commands fired off to the `osc_bridge.py`. Decouples low-latency audio control from high-level web tech.

## 3. Strict Documentation & Versioning Patterns
*   **The Universal Rulebook:** The core instructions (`docs/UNIVERSAL_LLM_INSTRUCTIONS.md`) govern all LLM actions (Claude, Gemini, GPT) across the monorepo to ensure consistency, with model-specific files (`GPT.md`, `CLAUDE.md`, etc.) pointing back to it.
*   **Single Source of Truth Versioning:** The `VERSION.md` file tracks the single absolute version of the ecosystem (currently `1.0.9`).
*   **Synchronized Update Cycle:** Every feature or task completed requires:
    1. Bumping the semantic version in `VERSION.md`.
    2. Prepending a detailed entry in `CHANGELOG.md`.
    3. Documenting the changes by checking off tasks in `TODO.md` and `ROADMAP.md`.
    4. Committing with the version referenced in the message.
*   **Context Passing:** `MEMORY.md` and `HANDOFF.md` act as mandatory state-preservation files between sessions and different AI agents, ensuring continuity.

## 4. Future Directions (From IDEAS.md, TODO.md & ROADMAP.md)
*   **Phase 3 AI Features:** Injecting Small Language Models (SLMs) for autonomous mixing assistance and stem separation into the `bobui` layer.
*   **Cross-DAW Plugin Wrapping:** Creating a bridge to share VST/LV2 plugins simultaneously across LMMS, Ardour, etc.
*   **WebAssembly Porting:** Exploring WASM compilation of core C/C++ audio engines for decentralized, browser-based collaboration.
[PROJECT_MEMORY]

# Project Memory: Bobtrax Omni-Workspace

## 1. Project Architecture & Vision
*   **Monolithic Ecosystem:** Bobtrax is a meta-project serving as a unified command center orchestrating multiple major open-source audio workstations (DAWs) through git submodules.
*   **Integrated Submodules:**
    *   **Ardour** (Digital audio workstation, uses Waf)
    *   **LMMS** (Digital audio workstation, uses CMake)
    *   **MusE Sequencer** (MIDI/Audio sequencer, uses CMake)
    *   **Zrythm** (Automated DAW, uses CMake/Meson)
*   **The UI Layer (`bobui`):** A custom UI submodule that is currently a mirror/fork of **QtBase** (Qt 6 core). The long-term vision is for `bobui` to evolve into the unified frontend launcher and interface layer connecting these DAWs together. With `1.0.10`, the first native C++/Qt application (`bobtrax_launcher`) was injected into its build tree.

## 2. Infrastructure & Tooling Decisions
*   **Unified Build System (`build.sh`):** A bash script at the root abstracts the varying build dependencies (CMake vs. Waf) across the submodules, supporting specific build flags like `--only-lmms` for targeted compilations.
*   **Continuous Integration (`ci.yml`):** A robust GitHub Actions pipeline pulls all submodules recursively, installs heavy audio/UI packages (ALSA, JACK, GTK3, Sndfile, etc.), and executes the unified `build.sh` to prevent regressions on push/PR.
*   **Interim Launchers (`launcher.py` and `gui_launcher.py`):**
    *   Because `bobui` is currently just QtBase and lacks frontend logic, interim launchers bridge the gap.
    *   `launcher.py` acts as a unified CLI launcher, and `gui_launcher.py` provides a lightweight Tkinter-based graphical window.
    *   *Design Pattern:* Both spawn the compiled DAW binaries as detached child processes via Python's `subprocess.Popen`. This insulates the user's audio sessions from launcher crashes.
    *   **Native GUI (`bobtrax_launcher`):** Introduced in the `bobui/src/bobtrax_launcher/` directory, utilizing `QProcess::startDetached` to emulate the interim scripts natively.
*   **Inter-Process Communication (IPC) Ecosystem:**
    *   **`osc_bridge.py`:** A centralized UDP router capturing and broadcasting Open Sound Control (OSC) messages across DAWs. Serves as the "Shared State" layer, enabling transport controls (play, stop) to sync across Ardour, MusE, etc. Features `INCOMING_MAP` and `OUTGOING_MAP` dictionaries for robust native dialect translation (e.g. `/ardour/transport_play` -> `/muse/play`). Codebase analysis verified Ardour natively targets `127.0.0.1:8000` via its control surface logic, meaning out-of-the-box it hooks directly into this bridge without configuration hacking.
    *   **`osc_web_wrapper.py`:** A `websockets`-based python server that listens for modern web JSON payloads (`{"action": "play"}`) and translates them into OSC commands fired off to the `osc_bridge.py`. Decouples low-latency audio control from high-level web tech.

## 3. Strict Documentation & Versioning Patterns
*   **The Universal Rulebook:** The core instructions (`docs/UNIVERSAL_LLM_INSTRUCTIONS.md`) govern all LLM actions (Claude, Gemini, GPT) across the monorepo to ensure consistency, with model-specific files (`GPT.md`, `CLAUDE.md`, etc.) pointing back to it.
*   **Single Source of Truth Versioning:** The `VERSION.md` file tracks the single absolute version of the ecosystem (currently `1.0.10`).
*   **Synchronized Update Cycle:** Every feature or task completed requires:
    1. Bumping the semantic version in `VERSION.md`.
    2. Prepending a detailed entry in `CHANGELOG.md`.
    3. Documenting the changes by checking off tasks in `TODO.md` and `ROADMAP.md`.
    4. Committing with the version referenced in the message.
*   **Context Passing:** `MEMORY.md` and `HANDOFF.md` act as mandatory state-preservation files between sessions and different AI agents, ensuring continuity.

## 4. Future Directions (From IDEAS.md, TODO.md & ROADMAP.md)
*   **Phase 3 AI Features:** Injecting Small Language Models (SLMs) for autonomous mixing assistance and stem separation into the `bobui` layer.
*   **Cross-DAW Plugin Wrapping:** Creating a bridge to share VST/LV2 plugins simultaneously across LMMS, Ardour, etc.
*   **WebAssembly Porting:** Exploring WASM compilation of core C/C++ audio engines for decentralized, browser-based collaboration.
