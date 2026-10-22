---
title: Document a rule's false-positive classes
impact: HIGH
impactDescription: Undocumented noise gets the whole ruleset suppressed within a month
tags: testing, documentation, quality
---

## Document a rule's false-positive classes

**Impact: HIGH**

Every rule file must state at the top what it **cannot** tell you and where it is
known to misfire. This is not optional politeness.

A rule whose false positives are undocumented gets suppressed wholesale by developers
within a month, and a suppressed rule is a control that reports green while enforcing
nothing — strictly worse than not having the rule, because it also produces a compliance
claim.

**Incorrect:**

```markdown
## Limits
Some false positives are possible.
```

**Correct:**

```markdown
## Known false-positive classes

- **Parameterised queries built through a helper.** The rule matches f-strings reaching
  `execute()`; a helper that safely interpolates a table name will be flagged. Suppress
  with `# nosemgrep: runwai-python-sql-string-building` and a comment naming the reason.
- **Test fixtures.** Deliberately vulnerable code in `tests/` matches. Exclude the path
  rather than weakening the rule.

## What this cannot tell you
Nothing about stored procedures, ORM-level injection, or any language outside Python
and JavaScript.
```

Note that fixtures confirm a rule does what its author intended. They say nothing about
false-positive rates on real code — that requires running the ruleset over a substantial
codebase and recording what came back.

Enforced by: `.runwai/tools/validate_registry.py` checks the README exists; its contents are
convention.

Reference: [.runwai/contributing.md](../../.runwai/contributing.md)
