---
title: Rule Title Here
impact: MEDIUM
impactDescription: Optional short description of the impact
tags: tag1, tag2
---

## Rule Title Here

**Impact: MEDIUM (optional impact description)**

Brief explanation of the rule and why it matters. State the consequence of getting it
wrong, not just the instruction — an agent that understands the failure mode will apply
the rule to cases this file did not anticipate.

**Incorrect (what is wrong with it):**

```yaml
# Bad example
```

**Correct (what makes it right):**

```yaml
# Good example
```

Enforced by: `.runwai/tools/validate_registry.py` — or "convention only", if nothing checks it.
State this honestly; an unenforced rule that claims enforcement is worse than one that
admits it relies on review.

Reference: [Link to the relevant doc or ADR](../../docs/architecture.md)
