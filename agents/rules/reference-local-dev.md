---
title: Local development setup
impact: LOW
tags: reference, setup
---

## Local development setup

**Impact: LOW**

```bash
pip install pre-commit==4.6.1
pre-commit install
```

Then run the gates locally before pushing. The commands, their exit codes and what each
one covers are in [`../running-the-checks.md`](../running-the-checks.md) — one canonical
list, so a path that moves is corrected in one place.

```bash
pre-commit run --all-files
```

The self-checks need `pyyaml==6.0.3` and `jsonschema==4.26.0`, and they live in
`.runwai/tools/`. They are deliberately offline: no network, no clock dependence, no
model. Same tree in, same verdict out.

`--strict` turns warnings into failures. CI will move to it once the pending pins in
`.runwai/docs/pinning.md` are complete; until then warnings are expected and are not a broken
build.

Reference: [.runwai/contributing.md](../../.runwai/contributing.md)
