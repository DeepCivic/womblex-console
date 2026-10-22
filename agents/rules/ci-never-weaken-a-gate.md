---
title: Never weaken a check to make CI green
impact: HIGH
impactDescription: A verifier with a blind spot reports success over the gap
tags: ci, checks, integrity
---

## Never weaken a check to make CI green

**Impact: HIGH**

When a check fails, fix the finding. Do not lower the threshold, add a blanket
suppression, drop `--error`, or narrow the scan path so the failure disappears.

A check that has been quietly weakened is worse than no check: it still produces a green
tick and the appearance of coverage, but the thing it claims to look at is no longer being
looked at. The failure has a known shape — a check-ID verifier once shipped here whose
regex `CKV[A-Z_]*_[0-9]+` could not match `CKV_K8S_19`, so three Kubernetes checks were
silently skipped by the very verifier meant to catch bad IDs. It was removed with the
capability it served rather than fixed. The pattern is written down here rather than
pointed at, so that it outlives both the code and any file this project later deletes.

If you genuinely cannot fix a finding, say so explicitly and leave the run red. An honest
red build is a working check.

**Incorrect:**

```yaml
- name: Semgrep
  run: semgrep scan --config ... .   # --error dropped so findings stop failing the job
  continue-on-error: true
```

**Correct:**

```yaml
- name: Semgrep
  run: semgrep scan --error --metrics=off --config ... .
```

...and if a specific finding is a genuine false positive, suppress *that finding* at the
line with a named reason, leaving the gate intact.

Note that `pre-commit` is bypassable with `--no-verify`, which is exactly why the `posture`
workflow re-scans the full history for secrets rather than trusting the hook ran.

One thing this rule does **not** cover: `posture` runs its semgrep pass without `--error`
on purpose, and that is not a weakening. It never had an `--error` to drop. Deciding in
advance that a workflow reports is design; removing enforcement after it went red is the
thing prohibited here.

Enforced by: review. Nothing mechanically prevents weakening a workflow, which is why this
rule is written down.

Reference: [docs/architecture.md](../../docs/architecture.md)
