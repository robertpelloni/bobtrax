# WebAssembly Port Initiative

## Objective
Port the core audio engines of the Bobtrax DAW ecosystem (Ardour, LMMS, MusE, Zrythm) to WebAssembly to facilitate real-time, decentralized browser-based music collaboration.

## Toolchain
- **Emscripten (emsdk):** The primary C/C++ to WebAssembly compiler.
- **emcmake / emmake:** Wrappers used to inject WebAssembly cross-compilation flags into the existing CMake build systems of the submodules.
- **emscripten/bind.h:** Used to write C++ wrapper classes (e.g., `WasmAudioEngine`) that expose native DSP methods (like `start()` and `stop()`) to the JavaScript runtime.

## Submodule Build Requirements & Challenges

### LMMS
- **Build System:** CMake
- **Status:** Integrated.
- **Challenges:** Requires stripping out native audio backends (ALSA, JACK) and utilizing an Emscripten-specific SDL or WebAudio backend. A wrapper `WasmAudioEngine.cpp` is injected into `lmms/src/core`.

### Zrythm & MusE
- **Build System:** CMake / Meson
- **Status:** Scaffolded wrappers.
- **Challenges:** Similar to LMMS, the UI (GTK for Zrythm) must be heavily decoupled from the DSP engine to allow the browser DOM to serve as the interface while the WASM module acts as a headless audio node.

### Ardour
- **Build System:** Waf
- **Status:** Blocked / Incompatible.
- **Challenges:** Ardour's `wscript` configuration is highly complex and fails when wrapped by `emconfigure`. It assumes a standard POSIX desktop environment. The GTK UI and audio engine are heavily intertwined. Porting Ardour requires a massive architectural rewrite to isolate `libs/ardour` into a pure headless library.

## Next Steps / Implementation
- The build pipeline has been successfully integrated via `build_wasm.sh` and the `--wasm` flag in the top-level `build.sh`.
- Future development should focus on implementing the `SharedArrayBuffer` IPC between the browser's AudioWorklet node and the WASM DSP loops to achieve low-latency playback.
