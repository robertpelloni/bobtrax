# WebAssembly Compatibility Analysis of Bobtrax DAW Submodules

## Overview
This document outlines the analysis of the build systems and architectures of the four core DAW submodules within Bobtrax (Ardour, LMMS, MusE, Zrythm) to determine their viability for WebAssembly (WASM) porting via Emscripten.

## 1. LMMS (Linux MultiMedia Studio)
* **Build System**: CMake
* **Architecture**: Good separation between GUI (Qt5/Qt6) and core audio engine (`src/core`).
* **WASM Compatibility**: **High**.
  * LMMS already uses CMake which pairs perfectly with `emcmake`.
  * The GUI can be disabled via `-DWANT_GUI=OFF` and `-DWANT_QT5=OFF`.
  * *Current Status*: We have already implemented an initial `WasmAudioEngine.cpp` proof-of-concept wrapper and successfully compiled it using the `build_wasm.sh` script.

## 2. Zrythm
* **Build System**: CMake (recently migrated from Meson)
* **Architecture**: Excellent separation between DSP backend (`src/engine`, `src/dsp`) and GTK4/libadwaita frontend (`src/gui`).
* **WASM Compatibility**: **High**.
  * Zrythm's engine is heavily optimized C/C++ which compiles well to WASM.
  * Like LMMS, the UI dependencies (GTK4) are the main blockers, but the CMake configuration allows for modular building.
  * *Strategy*: Implement a similar wrapper to LMMS's `WasmAudioEngine` that hooks into Zrythm's graph-based DSP routing.

## 3. MusE
* **Build System**: CMake
* **Architecture**: Tightly coupled monolithic codebase. Heavy reliance on ALSA/JACK sequencer APIs deep within the application logic.
* **WASM Compatibility**: **Low to Medium**.
  * Emscripten does not support ALSA or JACK. The `muse2/muse` and `src/muse4` directories have deep OS-level audio threading assumptions.
  * *Strategy*: Requires significant refactoring to abstract the audio backend into a dummy/WASM interface before Emscripten can compile it without POSIX/ALSA errors.

## 4. Ardour
* **Build System**: Waf (Custom python-based build system)
* **Architecture**: Massive, complex, heavily optimized for native POSIX systems.
* **WASM Compatibility**: **Very Low**.
  * The `waf` build system is notoriously difficult to cross-compile with Emscripten compared to CMake.
  * Deep dependency on system libraries (glib, pango, native threading, direct hardware access).
  * *Strategy*: Postpone indefinitely. Focus on LMMS and Zrythm for the browser-based collaboration engine.

## Proposed Unified Strategy
1. **Focus on LMMS and Zrythm**: These two engines represent the most viable path forward for the Phase 3 goal.
2. **Build System Standardization**: The root `build_wasm.sh` will exclusively use `emcmake` to target the CMake submodules, passing flags to disable all native UI toolkits (Qt, GTK).
3. **AudioWorklet Architecture**: Create C++ wrappers (like the LMMS PoC) that expose a standardized `processAudio(float* outL, float* outR, int frames)` function via `<emscripten/bind.h>`.
4. **Browser Integration**: The `bobui` web interface (served via `bobuiwasmserver.py`) will load these `.wasm` binaries into an `AudioWorkletNode` for real-time browser playback.
