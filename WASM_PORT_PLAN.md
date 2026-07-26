# WebAssembly Port Strategy

## Goal
Port the core DSP audio engines of the Bobtrax submodules (Ardour, LMMS, MusE, Zrythm) to WebAssembly to enable real-time, browser-based decentralized collaboration.

## Architecture
- **Toolchain:** Emscripten (`emsdk`), specifically using `emcmake` and `emmake`.
- **Bindings:** `EMSCRIPTEN_BINDINGS` (`<emscripten/bind.h>`) will wrap core engine classes (e.g., `lmms::Engine`).
- **Audio Threading:** Long-term target is to utilize `AudioWorklets` for low-latency DSP processing in the browser.
- **IPC / Concurrency:** `SharedArrayBuffer` will be used for high-performance memory sharing and lock-free rings between the main browser thread UI and the AudioWorklet WASM backend.

## Submodule Porting Roadmap
1. **LMMS (Status: Initial Scaffold)**
   - Target: `lmms/src/core`
   - Compatibility: High (CMake based).
   - Next Steps: Expose full Mixer and Track API.
2. **Zrythm (Status: Planned)**
   - Target: `zrythm/src/engine` / `zrythm/src/dsp`
   - Compatibility: High (CMake/Meson, cleanly separated DSP core).
   - Next Steps: Write `WasmAudioEngine.c` wrapper.
3. **MusE (Status: Planned)**
   - Target: `muse/src/muse`
   - Compatibility: Moderate.
4. **Ardour (Status: Blocked)**
   - Target: `ardour/libs/ardour`
   - Compatibility: Low (Waf build system breaks under emconfigure; UI tightly coupled).
   - Next Steps: Requires major architectural decoupling.
