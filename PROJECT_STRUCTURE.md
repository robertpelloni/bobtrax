# Project Structure & Submodules

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
