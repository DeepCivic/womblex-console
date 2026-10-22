# runwAI Maintainer Guide

**This is the maintainer's entry point, and it is loaded deliberately, not by default.**
`AGENTS.md` at the root speaks only to the adopter's agent (decision 11): a maintainer
session says so — it opens with `#maintainer`, or states in as many words that the subject
is the template rather than a product built from it — and starts here.
[`README.md`](README.md) indexes what else is in this directory.

## Purpose
runwAI delivers two value streams:
- **AI coding scaffolding**: AGENTS.md and live toolchain configs at expected paths
- **Honest security posture reporting**: Small set of deterministic checks with transparent coverage reporting

The security report is a calibration instrument - its value is truthfulness about actual coverage, not scan results.

## Core Principles
1. **Determinism**: No AI in security decision path - same input = same output
2. **Honest coverage**: Never imply more coverage than exists (14 rules, not 100+)
3. **"You shouldn't need to know what to ask for"**: Critical knowledge lives in AGENTS.md for agents to read unprompted

## Load-Bearing Components
| Component | Critical? | Why |
|-----------|-----------|-----|
| controls/registry.yaml | Yes | Report honesty depends on verified implementation |
| security_report.py | Yes | Primary output artifact |
| .pre-commit-config.yaml | Yes | Only enforcement mechanism |
| AGENTS.md/agents/ | Yes | Unprompted knowledge delivery |
| ISM baseline | No | Method works with any framework |

## Key Decisions
- No merge gates (honest about limitations - enforcement is branch protection)
- Files ship live at correct paths (no copy steps)
- Vendor only permissive content (no share-alike obligations)
- Small honest coverage > broad misleading coverage
- The full log, argued: [`decisions.yaml`](decisions.yaml)

## Change Evaluation
A change is good if:
- Makes the report more truthful
- Sharpens distinctions in coverage reporting
- Adds verifiable receipts for claims

A change is bad if:
- Inflates coverage numbers without actual checks
- Adds checks faster than honesty layer can describe them
- Introduces gate-shaped workflows that can't be enforced

## ALWAYS
- Update AGENTS.md in root if appropriate; its audience is the adopter's agent, and only
  that — maintainer instruction belongs here, never there
- Update README.md in root if appropriate; audience is the template-user
- Keep root .md files concise
- Leave `CLAUDE.md` as a one-line `@AGENTS.md` import. Claude Code reads that filename and
  not `AGENTS.md`; content in the bridge is a second guide to keep in step
- Keep the first-session step list in AGENTS.md and README.md's verification checklist in
  step, and in their own registers: imperative for the agent, "so you can tell whether your
  agent actually did it" for the human. Duplication here is deliberate (decision 16)

The test: Would a stranger form an accurate belief about security posture from the report? Everything exists to make the answer "yes."

## Do

- Run `python3 .runwai/tools/validate_registry.py` and `python3 .runwai/tools/ism.py verify` before
  concluding your work is finished
- Copy ISM control text **verbatim** from `controls/ism-snapshot.json`, never from memory
- Pin every tool to an exact version; if you cannot confirm a version exists, set
  `install: unavailable` and omit the version entirely
- Be pessimistic with `mapping_fidelity` — `partial` unless the tool enforces exactly what
  the control requires
- Assert every new rule in both directions in `controls/tests/`: it must fire on the bad
  case and stay silent on the good one. Name the fixture after the ruleset so
  `semgrep --test` pairs them
- Document a rule's known false-positive classes in a comment at the top of its rule file
- Make a new check **report `not applicable`** when the project has nothing for it to scan,
  distinctly from a pass. A check with no subject matter has found nothing, not nothing wrong
- Record `upstream.repo`, `upstream.commit` (full 40-char SHA) and `upstream.license` under
  the control's `implementation.provenance` for any vendored content, with a
  `LICENSE-UPSTREAM` beside the files
- Before finalising a commit, check whether any file you touched carries a `STEAL:` comment
  and update `.steal/manifest.md` in the *same* commit — path, two or three tags, one line
  of description, table sorted by path. See [`.steal/curation.md`](../.steal/curation.md);
  `validate_helpers.py` fails the build when a blessed file has no row

## Don't

- Never invent an ISM control ID, a tool version, or a commit SHA. An unverified ID in an
  assessor-facing document is worse than no document.
- Never mark something `verified` without a `verification_source` and a `verified_on` date
- Never describe a passing build as compliant. 36 of 1101 controls are mapped, most
  `partial`; the honest claim is which checks ran and what they found
- Never claim content is vendored without recording its upstream licence
- Never scan `controls/tests/` with a normal scan — the fixtures contain deliberate
  vulnerabilities and are excluded in `.semgrepignore`

## Boundaries

### Always do
- Run both self-checks before pushing
- Read the control in `controls/ism-snapshot.json` before mapping a tool to it
- Update a control's `notes` and `mapping_fidelity` in the same commit that changes what it
  enforces

### Ask first
- Changing the structural rules in `.runwai/tools/validate_registry.py` — they are the
  enforcement surface now that `schemas/` is gone
- Adding a dependency, or changing a pinned version
- Changing an upstream pin, or re-resolving vendored content to a newer commit
- Deleting files, or relaxing any check in `.github/workflows/`

### Never do
- Commit secrets, API keys or `.env` files
- Put a model in a control's decision path
- Record a version, SHA or control ID you have not confirmed
- Force push or rebase shared branches

## Project structure

```
controls/registry.yaml        ISM control -> mechanism -> tool -> implementation
controls/ism-snapshot.json    All 1101 June 2026 ISM controls (CC BY 4.0)
controls/ism-tags.yaml        Our semantic tags. Edit here, then regenerate the index
controls/ism-index.json       Generated join of the three. Never edit by hand
docs/security-report.md       The posture readout. Generated; blocks nothing
docs/dependencies.md          The bill of materials. Generated by audit.py; committed,
                                because "made available to consumers" is half of ISM-1730
.github/scripts/              Its generator, verify.py, audit.py and doctor.sh.
                                Adopter-facing, so NOT in .runwai/
.audit-cache/                 The audit's scanners, database snapshot and raw output.
                                Gitignored; rebuilt by the two setup-audit targets
Makefile                      The adopter's first session as deterministic targets.
                                Wraps agents/running-the-checks.md; adds nothing
controls/rules/               The semgrep rulesets. Fourteen rules, three files
controls/.secrets.baseline    detect-secrets' baseline. Not at the root: the hook passes
                                the path explicitly, so nothing reads it there
Makefile pins TRIVY_/SYFT_    The dependency scanners are release binaries, so the pin is
                                a version plus a per-architecture SHA-256. A tag alone
                                would let the asset behind it change
controls/tests/               Fixtures asserting each rule in both directions
docs/setup.md                 How this project is set up, as built. Keep it true.
agents/                       Rules, commands, knowledge base, skills
STEAL.md                      The taking path, addressed to the taker
.steal/                       Its index (manifest.md) and protocol (curation.md).
                                Removable by the adopter as a pair — validate_helpers
                                treats both-gone as a decision, one-gone as an error
CLAUDE.md                     `@AGENTS.md` and nothing else. The bridge that makes the
                                guide reachable by Claude Code, which reads this filename
biome.json, playwright.config.ts, promptfooconfig.yaml
                              The adopter's toolchain, shipped live. Inert here by
                                subject matter — runwAI has no JS/TS — never by design.
.runwai/                     runwAI's own record. Not the adopter's. Not in llms.txt.
.runwai/tools/               The self-checks. Deterministic, offline, no LLM. Maintainer
                                only — the template is not a Python project.
.runwai/decisions.yaml       Why the template is shaped this way. Structured, not ADRs.
.runwai/docs/                runwAI's own long-form record: provenance, pinning, status,
                                and report.md, the self-check readout. Maintainer-facing,
                                unlike docs/security-report.md. report.md is generated
.runwai/social-preview/      The card GitHub unfurls for this repository. runwAI's own
                                branding, so it is not the adopter's — and its six npm
                                packages leave their bill of materials with the directory
```

## Verification discipline

This repository's history contains two classes of error, both of which look like competent
work until checked:

1. **Plausible-looking ISM control IDs that were never read.** Four mappings in the original
   draft were disproved by reading the authoritative text.
2. **Repository slugs asserted without resolution.** A 62-entry research inventory was
   deleted rather than verified; several entries turned out to be fabricated.

The pattern in both is the same: fluent output about something nobody checked. If you cannot
verify a claim, say so and mark it unverified. That is always the cheaper outcome.

Read the relevant record before changing anything that looks arbitrary — it probably is not.
The template's reasoning is in [`decisions.yaml`](decisions.yaml); this project's configured
state is in [`../docs/setup.md`](../docs/setup.md).
