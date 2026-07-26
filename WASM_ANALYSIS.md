# WebAssembly Analysis

- Latency is reasonable using the Qt launcher and the local python server, but WebAudio API latency will need to be profiled.
- Plugin compatibility is non-existent. Native VSTs cannot run in WASM.
- Asset loading is restricted due to browser sandbox limits. SharedArrayBuffer must be used.
