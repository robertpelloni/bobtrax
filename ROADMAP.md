# Roadmap

## Phase 1: Foundation & Documentation (Current)
- [x] Establish universal LLM instructions.
- [x] Document all submodules, their versions, and project structure.
- [x] Set up comprehensive tracking files (VISION, MEMORY, TODO, IDEAS).

## Phase 2: Integration & Infrastructure
- [x] Implement `bobui` as the universal launcher and interface layer. (bobtrax_launcher Qt app)
- [x] Establish inter-process communication (IPC) or shared state between the DAWs if applicable. (Foundation set via osc_bridge.py)
- [x] Set up automated build pipelines for all submodules.

## Phase 3: AI & Advanced Features
- [ ] Implement AI mixing assistant.
- [ ] Implement stem separation capabilities within `bobui`.
- [ ] Port core audio engines to WebAssembly for browser-based collaboration.
