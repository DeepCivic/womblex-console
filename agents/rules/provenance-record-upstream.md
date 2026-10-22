---
title: Vendored content carries its upstream commit and licence
impact: CRITICAL
impactDescription: Unattributed vendored content is a licensing defect that propagates
tags: provenance, licensing, vendoring
---

## Vendored content carries its upstream commit and licence

**Impact: CRITICAL**

Vendoring means the content lives here. That is a deliberate trade: it makes a check
installable and auditable at a pinned version, and it obliges us to carry the upstream
licence and provenance for every file we copy.

runwAI is Apache-2.0. Vendored content keeps its own licence, and we cannot relicense it.
This matters downstream: anyone adopting this template inherits whatever obligations we
failed to record.

Record the full 40-character commit SHA. A branch or a tag is not a pin — both move.

**Incorrect:**

```yaml
provenance:
  origin: vendored
  upstream:
    repo: example/rules
    commit: main          # a branch is not a pin
```

**Correct:**

```yaml
provenance:
  origin: derived
  upstream:
    repo: calcom/cal.com
    commit: "3894f37e14eae5082770f35ff1fde72110c0e6b6"  # pragma: allowlist secret
    license: MIT
    resolved: true
```

...with `LICENSE-UPSTREAM` beside the vendored files.

Watch for share-alike licences. CC BY-SA content — the OWASP LLM Top 10, for instance —
places a copyleft obligation on whatever file receives its prose. Cite and paraphrase such
sources; do not copy them.

Resolve a SHA with `git ls-remote https://github.com/owner/repo HEAD`. The git protocol
reaches any public repository even where `api.github.com` is scoped to this one.

Enforced by: `.runwai/tools/validate_registry.py`, which rejects a non-SHA commit, missing upstream
licence, or `vendored_files` without a `LICENSE-UPSTREAM`.

Reference: [.runwai/docs/provenance.md](../../.runwai/docs/provenance.md),
[decision 1](../../.runwai/decisions.yaml)
