# Deployment & Environment Setup Instructions

## 1. Prerequisites
- Linux OS (Ubuntu 22.04 / 24.04 recommended)
- Git, CMake (>= 3.20), Make, GCC/G++ (>= 14 for Zrythm, >= 11 for others), Rust (Cargo >= 1.70), Python 3.10+
- Audio libraries: ALSA, JACK, GTK3, Sndfile, FFTW3, Libsamplerate, etc.

## 2. Setup Submodules & Python Dependencies
```bash
git clone --recursive https://github.com/robertpelloni/bobtrax.git
cd bobtrax
git submodule update --init --recursive
pip install python-osc websockets pillow pystray
```

## 3. Diagnostic & Submodule Build Orchestration
Run the unified build orchestrator with system dependency verification:
```bash
chmod +x build.sh
./build.sh --check-deps
./build.sh --all
```

Targeted single-DAW compilation:
```bash
./build.sh --only-lmms     # Build LMMS (CMake)
./build.sh --only-ardour   # Build Ardour (Waf)
./build.sh --only-muse     # Build MusE (CMake)
./build.sh --only-zrythm   # Build Zrythm (CMake)
./build.sh --only-bobui    # Build BobUI (QtBase)
./build.sh --wasm          # Build WebAssembly engines (Emscripten)
```

## 4. Submodule Build Diagnostics & Requirements
Observations from automated `./build.sh --all` execution:
- **`bobui`:** Uses CMake on the custom QtBase fork. Currently blocked by `BobUI6::BundledPcre2` dependency configuration.
- **`ardour`:** Uses Waf build system. Requires git tags (`git describe`) to generate `libs/ardour/revision.cc` prior to configuration.
- **`lmms`:** Requires `Qt5Config.cmake` (`libqt5-dev` or Qt 5.15+ SDK).
- **`muse`:** Requires KDE Extra CMake Modules (`extra-cmake-modules` / `ECM`).
- **`zrythm`:** Requires GCC 14 or higher (Ubuntu 24.04 defaults to GCC 13.3; install `gcc-14` and `g++-14`).
- **`omni_plugin_bridge`:** Compiles cleanly with Cargo and 100% test pass rate.

## 5. Launching the Unified Omni-Dashboard
To start the single-page GUI dashboard with System Tray support:
```bash
python3 gui_launcher.py
```

Under headless testing environments (e.g. CI/CD or Docker):
```bash
xvfb-run -a python3 gui_launcher.py
```

## 6. WebAssembly Collaboration Deployment
1. Install Emscripten SDK (`emsdk`) and ensure `emcmake` is in your `PATH`.
2. Run `./build.sh --wasm` to compile target DSP engines.
3. Start the local collaboration server via `python3 wasm_host.py --port 8080`.
4. Open your browser to `http://localhost:8080` or use the dashboard shortcut.
