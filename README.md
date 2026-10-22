# bobtrax

bobtrax is a meta-repository that aggregates four open-source DAWs as git
submodules under one umbrella, plus a small amount of Python glue code of its
own. Per `VISION.md`, the ambition is a "universal music production
ecosystem" — shared assets/plugins and AI-assisted workflows across the
engines. What exists today is the aggregation and early experiments, not the
unified ecosystem.

## Submodules

| Path | Upstream |
|---|---|
| `ardour/` | https://github.com/Ardour/ardour |
| `lmms/` | https://github.com/LMMS/lmms |
| `muse/` | MusE sequencer |
| `zrythm/` | Zrythm DAW |
| `bobui/` | https://github.com/robertpelloni/bqt (the BQt/BobUI tree) |

The submodule directories are empty until initialized:

```bash
git clone https://github.com/robertpelloni/bobtrax
cd bobtrax
git submodule update --init
```

Each DAW then builds by its own upstream instructions; `build.sh` is a
helper for the aggregate tree.

## Original code in this repo

- `gui_launcher.py` / `launcher.py` — a launcher front-end for the suite
- `osc_bridge.py` / `osc_web_wrapper.py` — OSC bridging experiments
- `omni_plugin_bridge/`, `ai_assistant/` — early bridge/assistant experiments
- `wasm/`, `wasm_launcher/`, `build_wasm.sh` and the `WASM_*.md` /
  `WEBASSEMBLY.md` notes — a WebAssembly port investigation
- `generate_docs.py` — documentation generator for the repo's many
  agent-facing docs (`MEMORY.md`, `HANDOFF.md`, `PROJECT_STRUCTURE.md`, …)

## Status

Experiment / aggregation workspace. Submodule pointers and docs were last
touched by automated agent commits (latest October 2026); the DAWs are
upstream projects with their own releases and support channels — bobtrax
itself ships nothing. (The README this replaces ended with ~135 repeated
`<!-- Break loop N -->` HTML comments, a bot artifact, now removed.)
