# Deployment Instructions

Currently, the project is a collection of submodules. Deployment involves cloning the repository and initializing all submodules.

## Steps
1. `git clone --recursive <repository_url>`
2. `git submodule update --init --recursive`
3. Build each submodule according to its respective build instructions (usually CMake or Waf depending on the DAW).
4. Run `bobui` to launch the unified interface (pending full implementation).

## WebAssembly Deployment
The WebAssembly deployment is documented in the `WASM_PORT_PLAN.md` and `WASM_ANALYSIS.md` documents.
1. Use `build_wasm.sh` to fetch Emscripten and compile `bobui` and `lmms`.
2. The initial launcher is served via `wasm_launcher/index.html`.
3. Use the `bobui` python web server to host the WASM assets.
