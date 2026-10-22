---
name: vendor-upstream-content
description: >-
  Vendor a file, ruleset or config from an upstream repository into runwAI with a
  resolved commit SHA and a verified licence. Use when adding third-party content to
  controls/rules/, the agent helper layer or the root toolchain configs, when adopting a
  newer upstream commit, or when asked where something came from.
---

# Vendor upstream content

Bring third-party content into this repository so it is pinned, auditable and correctly
attributed. Structure follows `calcom/cal.com`'s `agents/skills/<name>/SKILL.md` plus
`references/` convention (MIT, `3894f37e`).

## When to use this

- Adding a ruleset, config or template derived from another project
- Updating vendored content to a newer upstream commit
- Answering "where did this file come from, and what licence is it under?"

## Do not use this for

Content written here from scratch. That is `origin: original` and must **not** carry an
upstream block — the validator rejects a control that claims both.

## Procedure

### 1. Resolve the commit

```bash
git ls-remote https://github.com/owner/repo HEAD
```

Record the full 40-character SHA. A branch or tag is not a pin; both move under you.

Use the git protocol, not `api.github.com` — the REST API is scoped to this repository and
returns 403 for other repos. If `ls-remote` prompts for a password, the repository does not
exist or is private; that is a "not found", not an access failure.

### 2. Read the licence from the tree

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/owner/repo /tmp/vendor
git -C /tmp/vendor sparse-checkout set --no-cone '/LICENSE*' '/COPYING*' '/LICENCE*'
```

Never record a licence from memory. Match filenames loosely — `LICENSE`, `LICENSE.md`,
`LICENSE-APACHE`, `COPYING` and the British `LICENCE` all occur.

**Stop if it is share-alike.** CC BY-SA and GPL-family licences impose obligations on
whatever receives the content, and by extension on every repository adopting this template.
Cite and paraphrase instead, and record the derivation as `referenced`.

### 3. Fetch only what you need

```bash
git -C /tmp/vendor sparse-checkout set --no-cone '/path/to/file'
```

Vendor the narrowest useful unit. A whole upstream tree carried into this repository is
maintenance debt with no offsetting benefit.

### 4. Record provenance

For a control, under `implementation.provenance` in `controls/registry.yaml`:

```yaml
provenance:
  origin: derived          # or: vendored
  upstream:
    repo: owner/repo
    commit: "0123456789abcdef0123456789abcdef01234567"  # pragma: allowlist secret
    path: path/to/file
    license: MIT
    resolved: true
  verified_on: "2026-07-25"
vendored_files:
  - files/thing.yaml
```

...with the upstream licence text saved beside it as `LICENSE-UPSTREAM`.

For helper-layer or template content, add a row to
[`.runwai/docs/provenance.md`](../../../.runwai/docs/provenance.md) instead.

### 5. Verify

```bash
python3 .runwai/tools/validate_registry.py
python3 .runwai/tools/validate_helpers.py
```

## Choosing a derivation level

| Level | Applies when | Obligation |
| :--- | :--- | :--- |
| `vendored` | Files copied essentially unchanged | Attribution + `LICENSE-UPSTREAM` |
| `derived` | Upstream structure and some wording survive | Attribution + `LICENSE-UPSTREAM` |
| `structure` | Only layout or naming convention copied | Courtesy attribution |
| `referenced` | Pointing at it, or implementing a published spec | None |

Copyright covers expression, not ideas — copying a file taxonomy is not copying a file.
Record the level anyway; it is cheap now and settles the question later.

## Overlap

Two controls should not vendor the same `upstream.repo` and path. If duplication is
genuinely warranted, set `provenance.overlap_approved: true` with an `overlap_reason`. The
validator enforces this.

## References

- [`references/licence-families.md`](references/licence-families.md) — what each licence
  permits, and which ones to refuse
- [`../../rules/provenance-record-upstream.md`](../../rules/provenance-record-upstream.md)
- [`../../rules/provenance-pin-exactly.md`](../../rules/provenance-pin-exactly.md)
