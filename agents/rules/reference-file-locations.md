---
title: Key file locations
impact: LOW
tags: reference
---

## Key file locations

**Impact: LOW**

| What | Where |
| :--- | :--- |
| Control registry (single source of truth) | `controls/registry.yaml` |
| ISM control text, 1101 controls | `controls/ism-snapshot.json` |
| Rulesets | `controls/rules/` |
| Rule fixtures | `controls/tests/` |
| Structural rules for the registry | `.runwai/tools/validate_registry.py` |
| Registry self-check | `.runwai/tools/validate_registry.py` |
| Helper-layer self-check | `.runwai/tools/validate_helpers.py` |
| ISM verification | `.runwai/tools/ism.py` |
| Report generator | `.runwai/tools/report.py` |
| The only check that stops anything, and it is local | `.pre-commit-config.yaml` |
| CI, which reports and blocks nothing | `.github/workflows/posture.yml` |
| Security report generator | `.github/scripts/security_report.py` |
| Scan exclusions | `.semgrepignore` |
| Your project's setup, as built | `docs/setup.md` |
| Template decisions, backlog, provenance | `.runwai/` (runwAI's own; not the adopter's) |
| Helper provenance | `.runwai/docs/provenance.md` |

Reference: [docs/architecture.md](../../docs/architecture.md)
