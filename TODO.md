# TODO

- [x] Consolidate build scripts for all 5 submodules into a single `build.sh` or `Makefile`.
- [x] Analyze `bobui` for incomplete features and wire them up to launch the respective DAWs. (Interim CLI launcher created as bobui is currently QtBase.)
- [x] Add deep-dive comments to existing wrapper scripts (if any).
- [x] Ensure all LLM instructions files are consistently respected by each agent.
- [x] Implement CI/CD to auto-check submodule health and compile them.
- [ ] Configure Ardour to connect its native OSC control surface to `127.0.0.1:8000` via default template config.
- [x] Investigate/implement OSC translation mapping because different DAWs use different OSC paths (e.g. `/ardour/transport_play` vs `/muse/play`).
- [ ] Expose an HTTP/WebSocket wrapper on top of `osc_bridge.py` so `bobui` can command the DAWs via web technologies if desired.
