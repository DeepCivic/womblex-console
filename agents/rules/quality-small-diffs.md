---
title: Keep diffs small and reviewable
impact: HIGH
impactDescription: Under ~500 lines and ~10 code files
tags: quality, review, pr
---

## Keep diffs small and reviewable

**Impact: HIGH**

Large changes are hard to review, hide defects, and are painful to revert. Aim for under
500 changed lines and under 10 code files, each change doing one thing.

Documentation, lock files and generated files do not count toward the limit.

Ways to split work that has grown too large:

1. **By layer** — schema and registry changes separately from the tooling that consumes them
2. **By control** — one control per change, with its rules and its fixtures
3. **Refactor before feature** — preparatory restructuring lands first, on its own
4. **By dependency order** — whatever must merge first, merges first

In this repository the natural seam is usually the control boundary: a control plus
its control entries, selftests and README is one coherent, reviewable unit.

Enforced by: convention only.

Reference: [.runwai/contributing.md](../../.runwai/contributing.md)
