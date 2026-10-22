---
title: Never assert what you have not checked
impact: HIGH
impactDescription: The failure mode behind both of this repository's known error classes
tags: honesty, verification, quality
---

## Never assert what you have not checked

**Impact: HIGH**

Fluent output about something nobody verified is the characteristic failure of AI-assisted
work, and this repository has two documented instances: fabricated ISM control IDs, and a
62-entry inventory of repository slugs in which several projects did not exist.

Both looked like competent work. Neither was checked.

If you cannot verify something, mark it unverified and say why. That is always cheaper than
a confident guess, because a wrong claim costs whoever finds it far more than an admitted
gap costs you.

**Incorrect:**

```markdown
All 35 ISM control IDs have been verified against the June 2026 release.
```

...written without opening the snapshot.

**Correct:**

```markdown
All 35 ISM control IDs verified against controls/ism-snapshot.json on 2026-07-25.
Nine tool versions could not be confirmed and are recorded with no version at all.
```

The same discipline applies to anything with a `verified` field: nothing may claim it
without a `verification_source` and a `verified_on` date.

Enforced by: `.runwai/tools/validate_registry.py` for control verification claims; convention
elsewhere.

Reference: [docs/architecture.md](../../docs/architecture.md)
