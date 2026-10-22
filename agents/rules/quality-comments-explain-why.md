---
title: Comments explain why, not what
impact: MEDIUM
tags: quality, comments
---

## Comments explain why, not what

**Impact: MEDIUM**

A comment restating the code is noise that rots. A comment capturing the reasoning survives
refactoring and stops the next person reintroducing a bug you already fixed.

The comments worth writing here are the ones recording a trap someone already fell into.

**Incorrect:**

```python
# Get the registry
registry = load_yaml(registry_path, report)
```

**Correct:**

```python
# Assert the scheme rather than trusting the constant. urlopen honours file: and
# other schemes, so a future edit that dropped the https prefix would turn this
# into a local file read driven by inventory data.
scheme = urllib.parse.urlparse(url).scheme
```

The second one is load-bearing: delete it and someone eventually "simplifies" the guard
away.

Enforced by: convention only.

Reference: [AGENTS.md](../../AGENTS.md)
