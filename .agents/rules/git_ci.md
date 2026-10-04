---
trigger: "git-ci"
description: "Rules for git hygiene and continuous integration"
---

# Git & CI Guidelines

1. **Clean Tracking**:
   - Never stage `*.pt`, `*.onnx`, `*.mp4`, `*.sqlite*`, `.env`, or dataset folders.
2. **Quality Gates**:
   - `make check` must exit code 0 before tagging or finishing a phase.
3. **Changelog & Roadmap**:
   - Every phase completion must be recorded in `CHANGELOG.md` and checked off in `docs/ROADMAP.md`.
