# Deployment Instructions

Currently, the project is a collection of submodules. Deployment involves cloning the repository and initializing all submodules.

## Steps
1. `git clone --recursive <repository_url>`
2. `git submodule update --init --recursive`
3. Build each submodule according to its respective build instructions (usually CMake or Waf depending on the DAW).
4. Run `bobui` to launch the unified interface (pending full implementation).

## WebAssembly Port Deployment
The core audio engines can be cross-compiled to WebAssembly for browser-based collaboration.
1. Install and activate the Emscripten SDK (`emsdk`).
2. Run `./build.sh --wasm` from the repository root to build the WASM artifacts.
3. Start the `bobui` unified interface or manually execute `bobui/src/bobtrax_launcher/wasm_host.py` to serve the `wasm_launcher/` directory locally.
4. Open the provided localhost URL in a modern web browser.
5. Note: WebAssembly SharedArrayBuffer requires secure context headers.
