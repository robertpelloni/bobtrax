# WebAssembly Port Plan for Bobtrax Core Audio Engines

## 1. Goal
To successfully port core audio processing components from the DAWs (LMMS, Zrythm) to WebAssembly (WASM), allowing browser-based collaboration via Bobtrax.

## 2. Minimal Viable Scope
Based on the repository structure, the initial minimal viable scope will focus on isolating the purely mathematical/DSP backend from the UI systems.

### Target: LMMS Core Engine
- `lmms/src/core/AudioEngine.cpp`
- `lmms/src/core/Mixer.cpp`
- `lmms/src/core/Oscillator.cpp`
- `lmms/src/core/SampleDecoder.cpp`
**Rationale:** The `lmms/src/core` directory contains a distinct boundary for audio processing that can be divorced from the Qt GUI (`lmms/src/gui`).

### Target: Zrythm Engine
- `zrythm/src/engine/`
- `zrythm/src/dsp/`
**Rationale:** Similar to LMMS, Zrythm separates its DSP code. These modules handle graph-based audio routing which is ideal for a WebAudio AudioWorklet node.

## 3. Technical Implementation Strategy

### A. Emscripten & CMake Toolchain
- **Build configuration:** We will use `emcmake cmake` with specific flags to disable GUI dependencies:
  - `-DWANT_GUI=OFF` (LMMS)
  - `-DWANT_QT5=OFF` (LMMS)
  - For Zrythm, similar flags will be injected to bypass GTK4/libadwaita requirements.
- **Exporting Functions:** Use `<emscripten/bind.h>` to bind core engine initialization, processing (tick/buffer), and teardown functions to JavaScript.

### B. WebAudio API Integration (AudioWorklet)
- The WASM module will not directly access the soundcard (like ALSA or JACK would natively).
- Instead, the WASM module will be loaded inside an `AudioWorkletProcessor`.
- A C++ function (e.g., `processAudio(float* outputBuffer, int frames)`) will be exposed via Embind. The JS `process` method will pass Float32Arrays directly into the WASM heap memory space to be filled by the C++ engine.

### C. IPC & Browser Collaboration (SharedArrayBuffer)
- Real-time parameter changes (e.g., moving a fader in BobUI which reflects in the browser) will utilize `SharedArrayBuffer` for zero-copy state sharing between the main UI thread and the AudioWorklet thread.
- Note: This requires the server to send `Cross-Origin-Opener-Policy: same-origin` and `Cross-Origin-Embedder-Policy: require-corp` headers (already supported in `bobuiwasmserver.py`).

## 4. Next Steps for Implementation
1. Create a minimal `WasmAudioEngine.cpp` wrapper inside LMMS that `#include`s the core mixer and exports a simple buffer-fill function via `<emscripten/bind.h>`.
2. Update the `build_wasm.sh` to compile this wrapper into a standalone `.js`/`.wasm` pair.
3. Write a JavaScript `AudioWorkletProcessor` that instantiates the WASM module and hooks it up to the WebAudio destination node.
