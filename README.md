# bobtrax

bobtrax is a meta-repository that aggregates four open-source DAWs as git
submodules under one umbrella, plus Python glue code of its own. Per
`VISION.md`, the ambition is a "universal music production ecosystem" —
shared assets/plugins and AI-assisted workflows across the engines. What
exists today is the aggregation and early experiments, not the unified
ecosystem.

**Version:** 1.0.83

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
- `session_memory.py` (~52 KB), `session_exporter.py`,
  `session_importer.py` — session state, checkpoint bundles, mix
  stashing/recovery, timeline markers and cues
- `osc_bridge.py` / `osc_web_wrapper.py` — OSC bridging experiments
- `bobui_bridge.py` / `bobui_bridge/` — bridge to the BobUI tree
- `omni_plugin_bridge/`, `ai_assistant/` — early bridge/assistant
  experiments
- `stem_separator.py` — stem separation experiment
- `wasm/`, `wasm_launcher/`, `build_wasm.sh` and the `WASM_*.md` /
  `WEBASSEMBLY.md` notes — a WebAssembly port investigation
- `health_watchdog.py` — service health monitoring
- `generate_docs.py` — documentation generator for the repo's many
  agent-facing docs (`MEMORY.md`, `HANDOFF.md`, `PROJECT_STRUCTURE.md`, …)

## Status

Experiment / aggregation workspace, actively developed through November
2026 (last commit 2026-11-12; recent work is session features: timeline
markers, transition dry-run simulation, checkpoint export/import, mix
stashing). The DAWs are upstream projects with their own releases and
support channels — bobtrax itself ships nothing.
