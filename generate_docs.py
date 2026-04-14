import os

docs = {
    "VERSION.md": "1.0.1\n",

    "CHANGELOG.md": """# Changelog
All notable changes to this project will be documented in this file.

## [1.0.1] - 2024-04-10
### Added
- Comprehensive project documentation including AGENTS.md, VISION.md, ROADMAP.md, and more.
- Unified LLM instructions references across model-specific files.
- Documented submodule versions and project structure.
""",

    "AGENTS.md": """# Agents Instructions
Please refer to `docs/UNIVERSAL_LLM_INSTRUCTIONS.md` for the core universal instructions for all LLM agents.
This file serves as a pointer to the main instruction set to ensure consistency across all models.
""",

    "CLAUDE.md": """# Claude Instructions
Please refer to `docs/UNIVERSAL_LLM_INSTRUCTIONS.md` for the core universal instructions for all LLM agents.

## Claude Specifics
- Claude is the Architect, Planner, and Documentation Lead.
- Specialized in large-scale refactoring and holistic system understanding.
- Focus on maintaining detailed documentation and ensuring deep comprehension of the system architecture.
""",

    "GEMINI.md": """# Gemini Instructions
Please refer to `docs/UNIVERSAL_LLM_INSTRUCTIONS.md` for the core universal instructions for all LLM agents.

## Gemini Specifics
- Gemini focuses on Speed, Performance Analysis, Large Context Operations (full-repo scans), and complex Scripting.
- Best utilized for sweeping codebase changes and running complex python automation scripts.
""",

    "GPT.md": """# GPT Instructions
Please refer to `docs/UNIVERSAL_LLM_INSTRUCTIONS.md` for the core universal instructions for all LLM agents.

## GPT Specifics
- GPT focuses on Code Generation, Unit Testing, and specific algorithm implementation.
- Excellent at writing robust test coverage and fixing isolated logical bugs.
""",

    "copilot-instructions.md": """# Copilot Instructions
Please refer to `docs/UNIVERSAL_LLM_INSTRUCTIONS.md` for the core universal instructions for all LLM agents.

## Copilot Specifics
- Focus on contextual autocompletion and inline documentation.
- Maintain consistent code style and immediately apply docstrings as defined in the universal instructions.
""",

    "VISION.md": """# Project Vision: Bobtrax

## The Ultimate Goal
Bobtrax is envisioned to be a Universal Music Production Ecosystem, rather than just a collection of DAWs.
The core foundational idea is to unify the world's most powerful open-source audio workstations (Ardour, LMMS, MusE, Zrythm) under a single cohesive umbrella, enhanced by `bobui`.

## Core Foundational Ideas
- **Seamless Integration:** Allowing assets, plugins, and potentially sessions to be shared or bridged across different underlying engines.
- **AI-Enhanced Workflows:** Integrating autonomous agents for mixing, stem separation, and intelligent arrangement.
- **Community & Ecosystem:** Enabling real-time collaboration and decentralized asset discovery.

We will continue to iterate on these concepts, expanding the capabilities of open-source music production, aiming for maximum user satisfaction, delight, and productivity.
""",

    "MEMORY.md": """# Memory & Observations

- **Submodules:** The project relies heavily on git submodules for its core engines (Ardour, LMMS, MusE, Zrythm) and UI layer (bobui).
- **Design Preferences:**
  - Strong emphasis on comprehensive, extreme-detail documentation.
  - All LLM interactions must be documented, and instructions must be strictly followed.
  - Version numbers must be synchronized across the project and maintained in a single `VERSION.md` file.
  - Code should be commented in-depth explaining the *why* and *how*.
""",

    "DEPLOY.md": """# Deployment Instructions

Currently, the project is a collection of submodules. Deployment involves cloning the repository and initializing all submodules.

## Steps
1. `git clone --recursive <repository_url>`
2. `git submodule update --init --recursive`
3. Build each submodule according to its respective build instructions (usually CMake or Waf depending on the DAW).
4. Run `bobui` to launch the unified interface (pending full implementation).
""",

    "ROADMAP.md": """# Roadmap

## Phase 1: Foundation & Documentation (Current)
- [x] Establish universal LLM instructions.
- [x] Document all submodules, their versions, and project structure.
- [x] Set up comprehensive tracking files (VISION, MEMORY, TODO, IDEAS).

## Phase 2: Integration & Infrastructure
- [ ] Implement `bobui` as the universal launcher and interface layer.
- [ ] Establish inter-process communication (IPC) or shared state between the DAWs if applicable.
- [ ] Set up automated build pipelines for all submodules.

## Phase 3: AI & Advanced Features
- [ ] Implement AI mixing assistant.
- [ ] Implement stem separation capabilities within `bobui`.
- [ ] Port core audio engines to WebAssembly for browser-based collaboration.
""",

    "TODO.md": """# TODO

- [ ] Consolidate build scripts for all 5 submodules into a single `build.sh` or `Makefile`.
- [ ] Analyze `bobui` for incomplete features and wire them up to launch the respective DAWs.
- [ ] Add deep-dive comments to existing wrapper scripts (if any).
- [ ] Ensure all LLM instructions files are consistently respected by each agent.
- [ ] Implement CI/CD to auto-check submodule health and compile them.
""",

    "HANDOFF.md": """# Handoff Document

## Session Summary
- Analyzed the `bobtrax` repository, which is a collection of music production submodules (ardour, bobui, lmms, muse, zrythm).
- Generated and populated a comprehensive suite of documentation files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `GPT.md`, `copilot-instructions.md`, `VISION.md`, `MEMORY.md`, `DEPLOY.md`, `CHANGELOG.md`, `VERSION.md`, `ROADMAP.md`, `TODO.md`, `PROJECT_STRUCTURE.md`) as requested by the user.
- Updated `IDEAS.md` to reflect advanced features.
- Prepared the project for the next AI agent in the chain.

## Next Steps for the Next Agent
- Review `TODO.md` and select a feature to implement (e.g., building a unified build script or enhancing `bobui`).
- Continuously update these markdown files as the project evolves.
- Follow the universal LLM instructions for all operations.
""",

    "PROJECT_STRUCTURE.md": """# Project Structure & Submodules

This document outlines the overall project directory structure, code layout, and all linked submodules.

## Directory Structure
```
bobtrax/
├── docs/                      # Global documentation and universal LLM instructions
├── ardour/                    # [Submodule] Ardour DAW
├── bobui/                     # [Submodule] Bobtrax UI/Launcher
├── lmms/                      # [Submodule] LMMS DAW
├── muse/                      # [Submodule] MusE Sequencer
├── zrythm/                    # [Submodule] Zrythm DAW
├── AGENTS.md                  # Pointer to universal LLM instructions
├── CHANGELOG.md               # Version history
├── CLAUDE.md                  # Claude-specific instructions
├── copilot-instructions.md    # GitHub Copilot instructions
├── DEPLOY.md                  # Deployment/Build instructions
├── GEMINI.md                  # Gemini-specific instructions
├── GPT.md                     # GPT-specific instructions
├── HANDOFF.md                 # Handoff notes between LLM sessions
├── IDEAS.md                   # Creative ideas for project expansion
├── MEMORY.md                  # LLM memory and observations
├── PROJECT_STRUCTURE.md       # This file
├── README.md                  # Project overview
├── ROADMAP.md                 # Long-term feature roadmap
├── TODO.md                    # Short-term tasks and bugs
└── VERSION.md                 # Single source of truth for project version
```

## Submodules

### Ardour
- **URL:** `https://github.com/Ardour/ardour`
- **Path:** `ardour/`
- **Commit:** `bcfb9e28ddddb52981efc1441e8bdf8a09934a6a`
- **Description:** A digital audio workstation.

### BobUI
- **URL:** `https://github.com/robertpelloni/bobui`
- **Path:** `bobui/`
- **Commit:** `270d54ed387ad53fdaab77d0ad3b274b4dd94199`
- **Description:** The Qt-based user interface and base layer for the bobtrax ecosystem.

### LMMS
- **URL:** `https://github.com/LMMS/lmms`
- **Path:** `lmms/`
- **Commit:** `6f50f90b9cc424df0ebdcae6fe53e894033ad24f`
- **Description:** A free, cross-platform music creation software.

### MusE
- **URL:** `https://github.com/muse-sequencer/muse`
- **Path:** `muse/`
- **Commit:** `daad0ee13620d22ed04cbe60db4dd3092bea817c`
- **Description:** A MIDI/Audio sequencer with recording and editing capabilities.

### Zrythm
- **URL:** `https://github.com/zrythm/zrythm`
- **Path:** `zrythm/`
- **Commit:** `f2b07dcda3c6c147b16b4d8861dbc01cf36cf980`
- **Description:** A highly automated and intuitive digital audio workstation.
"""
}

for filename, content in docs.items():
    with open(filename, "w") as f:
        f.write(content)

print("Documentation files generated successfully.")
