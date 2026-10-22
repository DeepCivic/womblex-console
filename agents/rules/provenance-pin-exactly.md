---
title: Pin exactly, or record no version at all
impact: CRITICAL
impactDescription: An unpinned scanner is a non-deterministic control by definition
tags: pinning, determinism, provenance
---

## Pin exactly, or record no version at all

**Impact: CRITICAL**

Every tool gets an exact version. No `latest`, no `*`, no `^` or `~`, no bare major tags. A
floating specifier means the ruleset can change under you and silently alter verdicts,
which makes the control non-deterministic no matter how deterministic the tool itself is.

If you cannot confirm a version exists, **do not guess one**. Set `install: unavailable`
and omit the version. Nine tools in this repository are recorded that way deliberately.
Pinning a scanner to a version nobody checked is the same class of error as citing an
unverified control ID: it looks like diligence and it is not.

**Incorrect:**

```yaml
- name: trivy
  version: "^0.72"        # floating
- name: cosign
  version: "3.1.2"        # guessed, never confirmed
```

**Correct:**

```yaml
- name: semgrep
  install: pypi
  version: "1.171.0"
  verified_version: true

- name: cosign
  install: unavailable    # release list not reachable; no version recorded
```

Enforced by: `.runwai/tools/validate_registry.py`, which rejects floating specifiers outright and
errors if a tool marked `install: unavailable` still carries a version.

Reference: [.runwai/docs/pinning.md](../../.runwai/docs/pinning.md),
[decision 1](../../.runwai/decisions.yaml)
