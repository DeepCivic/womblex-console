# Sections

This file defines every section, its ordering and its impact level. The section ID in
parentheses is the filename prefix used to group rules: a rule file must be named
`{section}-{name}.md` using one of the IDs below, or `.runwai/tools/validate_helpers.py` fails.

Adapted from the section-registry pattern in `calcom/cal.com` at `3894f37e` (MIT). Their
ten sections were app-architecture shaped — data layer, API design, performance, design
patterns, team culture — and none of those apply to a control library, so the set below is
runwAI's own.

---

## 1. Controls (controls)

**Impact:** CRITICAL
**Description:** The determinism invariant — what may and may not sit in a control's
decision path. Violations here produce compliance claims that are not true, which is the
worst failure this repository can have.

Control-to-standard mapping discipline is deliberately **not** covered by these rules. It
is owned by `controls/registry.yaml` and its own tooling, and is out of scope for the
helper layer.

## 2. Provenance (provenance)

**Impact:** CRITICAL
**Description:** Exact version pinning, upstream commit and licence recording. An unpinned
tool is a non-deterministic control by definition, and unattributed vendored content is a
licensing defect that propagates to everyone who adopts this template. This is the section
the vendoring workflow lives in.

## 3. Code Quality (quality)

**Impact:** HIGH
**Description:** Reviewable diffs, honest claims, and comments that explain intent. Includes
the rule against asserting anything that has not been checked.

## 4. Testing (testing)

**Impact:** HIGH
**Description:** Two-directional rule assertions and documented false-positive classes. A
rule that cannot distinguish good code from bad is noise, and noise gets the gate switched
off.

## 5. CI/CD (ci)

**Impact:** HIGH
**Description:** Gate integrity. The rules that stop a red build being resolved by making
the check weaker.

## 6. Reference (reference)

**Impact:** LOW
**Description:** Informational lookups — file locations and local development setup.
