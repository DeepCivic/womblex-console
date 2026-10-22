---
description: Run every runwAI self-check and report what failed
---

Run all of these and report the result of each, including warnings:

```bash
python3 .runwai/tools/validate_registry.py
python3 .runwai/tools/validate_helpers.py
pre-commit run --all-files
```

Do not weaken a check to make it pass — see `agents/rules/ci-never-weaken-a-gate.md`. If
something fails and the fix is unclear, report the failure rather than routing around it.
