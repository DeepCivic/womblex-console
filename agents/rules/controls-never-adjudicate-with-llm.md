---
title: Never put a model in a control's decision path
impact: CRITICAL
impactDescription: The load-bearing invariant of the entire repository
tags: determinism, invariant, enforcement
---

## Never put a model in a control's decision path

**Impact: CRITICAL**

An LLM may author a check. It may never adjudicate one. If you ask a model "is this
code secure?" you can get different answers to the same question, and a rule that changes
its mind is not a rule — it is a coin flip with good grammar.

Enforcement must be an ordinary program, pinned to an exact version, returning an exit
code. Same tree in, same verdict out, forever.

**Incorrect (a model decides whether the control passes):**

```yaml
tools:
  - name: security-reviewer
    class: llm-judge
    version: "claude-x"
```

**Correct (a pinned tool with a fixed ruleset decides):**

```yaml
tools:
  - name: semgrep
    class: sast
    version: "1.171.0"
    verified_version: true
```

A probabilistic tool can still be useful — it just cannot block on its own. To gate on one,
wrap it in a `deterministic_assertion`: a reproducible check over the stochastic run, such
as "the response schema still holds and no secret pattern appeared in output".

Enforced by: `.runwai/tools/validate_registry.py`, which rejects the tool classes `llm-judge`,
`llm-review`, `ai-review`, `model-adjudication` and `human-attestation` by name, and fails
any probabilistic control that is `blocking` without an assertion.

Reference: [docs/architecture.md](../../docs/architecture.md)
