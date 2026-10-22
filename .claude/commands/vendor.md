---
description: Vendor upstream content into runwAI with a resolved SHA and verified licence
---

Follow the procedure in `agents/skills/vendor-upstream-content/SKILL.md`.

Resolve the commit with `git ls-remote` (not `api.github.com` — it is scoped to this
repository), read the licence from the upstream tree rather than from memory, refuse
share-alike sources, and record provenance under `implementation.provenance` or
`.runwai/docs/provenance.md`.

Then run `python3 .runwai/tools/validate_registry.py` and `python3 .runwai/tools/validate_helpers.py`.

$ARGUMENTS
