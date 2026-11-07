# Bobtrax User Manual & Operator Guide

Welcome to **Bobtrax**, the unified open-source music production ecosystem. Bobtrax consolidates the world's most powerful digital audio workstations (Ardour, LMMS, MusE, Zrythm) with modern AI tools, cross-DAW plugin bridging, and WebAssembly browser-based collaboration.

---

## 1. Getting Started

### Prerequisites
- Python 3.10+ with `tkinter`
- Recommended Python packages:
  ```bash
  pip install python-osc websockets pystray pillow
  ```
- Submodules initialized:
  ```bash
  git submodule update --init --recursive
  ```

### Launching the Omni-Dashboard
Run the unified dashboard:
```bash
python3 gui_launcher.py
```
Or use the CLI launcher:
```bash
python3 launcher.py ardour # or lmms, muse, zrythm
```

---

## 2. Dashboard Interface Overview

The Omni-Dashboard is arranged hierarchically by workflow and utility value on a single scrollable pane:

### 1. Header & Live Global Status
- **Status Badges:** Displays real-time operational status of the System Tray (`TRAY`), WebAssembly Host (`WASM`), Central IPC Hub (`OSC BRIDGE`), and WebSocket Gateway (`WS`).
- **System Tray Icon:** Minimizes the dashboard to system tray or right-click to access quick server actions (Start/Stop servers, Open browser portal, Quit all servers).

### 2. MUSE Universal Command Palette
- **Unified Search & Command Input:** Type natural audio commands (`play`, `stop`, `tempo 128`, `record`) and press Enter to instantly route transport actions across all running DAWs.
- **Quick Transport Buttons:** Dedicated `Play`, `Stop`, and `Record` buttons dispatching immediate OSC signals.

### 3. AI Production Suite
- **AI Mixing Assistant:**
  - Type requests like *"Make the kick punchy and compress the snare"* or choose from presets (*"Punchy Kick"*, *"Vocal Clarity"*, *"Warm Master"*).
  - Click **Attach Stems Context** to link your session audio stems, providing track context to the assistant.
  - Click **Execute AI Mix** to send the prompt to the LLM (OpenAI or local endpoint like LM Studio / Ollama) and automatically transmit OSC parameter moves to DAWs.
- **Demucs Neural Stem Separator:**
  - Click **Browse Audio...** to pick any source song or mixdown (`.wav`, `.mp3`, `.flac`).
  - Choose model (`htdemucs`, `mdx_extra`, etc.) and toggle GPU CUDA acceleration.
  - Click **Run Stem Separation** to generate separate `drums.wav`, `bass.wav`, `vocals.wav`, and `other.wav` tracks.

### 4. Real-Time IPC & Collaboration Hub
- **Central OSC Bridge (`osc_bridge.py`):** Central UDP router on `127.0.0.1:8000` mapping dialects between Ardour, LMMS, MusE, and Zrythm.
- **WebSocket Gateway (`osc_web_wrapper.py`):** Listens on `ws://127.0.0.1:8765` for JSON web payloads and translates them into OSC commands.
- **WebAssembly Host (`wasm_host.py`):** Spawns an HTTP server on port 8080 with CORS and SharedArrayBuffer headers to serve browser audio worklets.
- **Start All Servers / Stop All Servers:** One-click controls to manage all background services simultaneously.

### 5. Native DAWs & Omni-Plugin Bridge
- **BobUI Architecture & Integration:** Detailed in `bobui/BOBUI_INTEGRATION.md`, outlining the core QtBase widget runtime, cross-DAW asset sharing, and POSIX C++ adapters.
- **Omni-Plugin Bridge:** Rust-based IPC wrapper (`omni_plugin_bridge`) allowing shared VST/LV2 plugins across LMMS and Ardour. Click **Test Bridge IPC** to verify the Rust test suite.
- **Native DAW Launchers:** Dedicated cards with descriptions and launch buttons for:
  - **Ardour:** Professional multitrack recording and mastering.
  - **LMMS:** Pattern-based beatmaking and synth sequencing.
  - **MusE:** MIDI/Audio workstation and arranger.
  - **Zrythm:** Automated DAW with flexible modular routing.

### 6. System Telemetry & Console Log
- Displays real-time timestamps, subprocess outputs, AI responses, and OSC telemetry.
- Includes **Clear Log** and **Copy Log** tools for debugging.

---

## 3. Server Management from System Tray
When running with a desktop notification manager, Bobtrax attaches an icon to your desktop tray:
- **Show / Hide Dashboard:** Toggle window visibility without stopping audio processing.
- **Start All Servers / Stop All Servers:** Rapid lifecycle management.
- **Open WebAssembly Portal:** Direct browser shortcut.
- **Quit Bobtrax:** Terminates all child server processes cleanly to prevent orphan background ports.
