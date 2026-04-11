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
