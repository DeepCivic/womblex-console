# runwAI Architecture

## What runwAI is

runwAI is a **curated set of controls**. Each control is backed by a set of
**compliance pipeline setup instructions**: everything needed to wire one technical
control into a repository, including the actual config files, not just a link to them.

Vendored means the content lives here. That is a deliberate trade: it makes a check
installable and auditable at a pinned version, and it obliges us to carry upstream
licence and provenance for every file we copy. See [Provenance and licensing](#provenance-and-licensing).

## The core invariant

> AI may perform the setup work. The controls themselves must be deterministic.

This is the load-bearing rule of the repository, so it is written as a machine check
rather than a convention. `.runwai/tools/validate_registry.py` fails the build when it is violated.

The split:

| Layer | Who/what does it | Reproducible? |
| :--- | :--- | :--- |
| **Setup** — generating configs, wiring workflows, drafting docs | An AI agent or a human, freely | Not required |
| **Enforcement** — deciding whether a given commit passes or fails | A pinned tool with a fixed ruleset, returning an exit code | **Required** |

An LLM is never in the decision path of a control. A check may be *authored* by an
agent; it may not be *adjudicated* by one.

### Determinism, defined precisely

A control is `deterministic` when the same input tree, scanned by the same pinned tool
version and ruleset, always produces the same verdict.

This definition has teeth, and it disqualifies some things that look like gates:

- **`semgrep` against a fixed ruleset** — deterministic. Same code, same rules, same finding.
- **`gitleaks` / `detect-secrets` over a diff** — deterministic.
- **`checkov` over Terraform** — deterministic.
- **`garak` fuzzing a live LLM endpoint** — **not** deterministic. The target is
  stochastic; a passing run does not mean the next run passes. Genuinely useful, but it
  cannot be enforcement on its own.
- **An LLM reviewing a diff for "security issues"** — not deterministic, and forbidden
  as an enforcement mechanism outright.

So every control declares `enforcement: deterministic | probabilistic`, and the validator
enforces:

```
enforcement: probabilistic  ⇒  blocking: false
                               (unless a deterministic_assertion wraps it)
```

A `deterministic_assertion` is the escape hatch that makes a probabilistic tool gateable:
wrap the stochastic run in a fixed, reproducible check. For prompt-injection testing, the
assertion is not "did garak find something" but "does the response schema still hold and
did no secret pattern appear in output" — a regex/schema check that is reproducible even
though the model is not.

This distinction is why the ISM 2026 AI controls are scaffolded as **advisory** here.
Marking them blocking would be dishonest about what the tooling can actually guarantee.

## Repository layout

```
controls/registry.yaml        Single source of truth: ISM control -> mechanism -> tool -> implementation
controls/ism-snapshot.json    All 1101 June 2026 ISM controls, extracted from the ASD
                                template (CC BY 4.0). Verification runs against this.
controls/rules/               The semgrep rulesets themselves
controls/tests/               Annotated fixtures asserting each rule both ways
.runwai/tools/               The self-checks. Maintainer-only, and there rather than at
                                the root so a template that is not a Python project does
                                not read as one. See decision 3.
  validate_registry.py          determinism invariant, pinning, provenance, overlap
  ism.py                        snapshot (once per release) and verify (every commit)
  validate_helpers.py           the AI helper layer, offline and stdlib-only
  report.py                     aggregates gate results into .runwai/docs/report.md
.runwai/decisions.yaml       Why the template is shaped this way
.pre-commit-config.yaml       Local checks, the only ones that stop anything
.semgrepignore                Excludes selftest fixtures, which are deliberately vulnerable
.github/workflows/posture.yml The one workflow. Reports, blocks nothing
.github/scripts/              The security report generator. Adopter-facing
docs/                         This file, the adopter's setup record, ISM verification
AGENTS.md                     Agent entry point; Do/Don't and Boundaries for this repository
agents/                       Modular rules, command reference, knowledge base, skills
biome.json, playwright.config.ts, promptfooconfig.yaml
                              Adopter toolchain configs, shipped live at the root
llms.txt                      Machine-readable index (llmstxt.org convention)
```

## Where checks run, and why none of them is a merge gate

There are two places, and `mechanism` in the registry names only those two. A value that
named anything else would be describing machinery this repository does not carry.

1. **`pre-commit`** — local, fast, and the only check here that stops anything. Secrets and
   SAST findings on the files you staged. It is bypassable with `--no-verify`, so it is
   never the whole story.
2. **`posture`** — the CI workflow. Runs the rulesets in report mode, writes
   `docs/security-report.md`, tests the rulesets against their own fixtures, re-scans the full
   history for secrets, and runs the structural self-checks. It reports; it blocks nothing.

**runwAI ships no merge gate, and will not.** Preventing a merge is branch protection: a
setting on the repository at the forge, not a file a template can carry. A template that
described itself as blocking would be claiming to install something it cannot, and the
adopter would discover the gap the first time something merged red. So the honest shape is
a local check that stops you, CI that tells you, and a report that says which of the two
produced each answer.

Two earlier values, `pr-gate` and `release-gate`, are gone. The release gate went with the
capability that fed it; evidence artefacts — SBOM, CBOM, signatures — are real work and
belong to a later version. The PR gate went because the word *gate* was the claim, and the
claim was never true: the workflow ran, nothing required it to pass, and the registry
carried `blocking: true` on twenty-three controls that blocked nothing. `validate_registry.py`
now rejects `blocking: true` on anything routed to `posture`, so the claim cannot come back
without the machinery.

`posture` running its scan without `--error` is a design decision, not a weakened check, and
the distinction is worth stating precisely because `agents/rules/ci-never-weaken-a-gate.md`
forbids the thing it resembles. The rule prohibits removing enforcement that existed;
`posture` never had an `--error` to drop, the same rulesets still run with `--error` in the
pre-commit hook, and its scanner output is captured to JSON rather than discarded. A
discarded exit code with nothing kept is what makes a silent scanner indistinguishable from
a clean one — that is the failure the rule is about, and capturing the findings avoids it.

## Tool pinning

Every tool is pinned to an exact version, and the validator rejects floating specifiers
(`latest`, `*`, `^`, `~`, bare major tags). An unpinned scanner is a non-deterministic
control by definition — its ruleset can change under you and silently alter verdicts.

CI installs scanners from PyPI at exact versions rather than depending on third-party
marketplace actions, which reduces the trusted surface to one registry and keeps the
pins verifiable in one place.

## Provenance and licensing

Because runwAI may vendor third-party content, every vendored implementation carries:

- `upstream.repo` and `upstream.commit` — the exact commit the content came from, never a
  branch name
- `upstream.license` — the SPDX identifier of the **upstream** licence
- `files/` content preserved with its upstream licence in `LICENSE-UPSTREAM`
- `verified_on` — when a human or a tool last confirmed the above

runwAI's own licence covers runwAI's own work. It does not and cannot relicense vendored
content. The validator fails any implementation with vendored files but no upstream licence.

## Overlap policy

The original backlog required overlap to be "negligible and only done with user approval."
Historically this was enforced mechanically across capability manifests; with those gone it
is review. Two controls should not vendor the same
`upstream.repo` + path, unless the later one sets `overlap_approved: true` with a reason.

This intentionally overrides the earlier "lossless, no filtering" framing of the research
inventory. Those two goals are incompatible; curation won, and the unfiltered list has since
been retired outright — see [decision 1](../.runwai/decisions.yaml).
What survives is `.runwai/docs/provenance.md`: the sources actually used, each with a
resolved commit and a verified licence.

## Verification status is explicit, never implied

Two things in this repository were asserted before they were checked: the ISM control
numbers, and the repository slugs in the research inventory. Both carry an explicit
status field, and both **default to unverified**. Nothing may claim `verified` without a
`verification_source` and a `verified_on` date; the validator enforces that.

The same rule now applies to vendored helper content: an entry in
`.runwai/docs/provenance.md` may only record `resolved: true` once its commit SHA has
actually been resolved and its licence read from the upstream tree.

Current state of each:

- **ISM control IDs — verified.** All 35 distinct IDs were checked against the June 2026
  SSP annex template published by ASD. None was fabricated. Each claim records the
  control's wording verbatim, and `.runwai/tools/ism.py verify` fails on any drift from
  `controls/ism-snapshot.json`. Four mappings were disproved by reading the
  authoritative text and corrected. See `docs/ism-verification.md`.

- **Research inventory slugs — retired, not verified.** The 62-entry list was deleted
  rather than confirmed; most of its entries were unresolvable or fabricated, and
  verifying them would have produced a well-attested list of things nobody was going to
  use. The ten sources the helper layer actually draws on were resolved to full commit
  SHAs over the git protocol and had their licences read from the upstream tree. See
  `.runwai/docs/provenance.md` and
  [decision 1](../.runwai/decisions.yaml).

  Note the access shape this depends on, because it is not obvious: `api.github.com` is
  bound to this repository and refuses `/repos/{owner}/{repo}` for anything else, but the
  **git protocol reaches any public repository**. `git ls-remote` resolves SHAs where the
  REST API returns 403. A verification tool written against the REST API will report a
  blockage that does not exist.

Verifying an ID is not the same as verifying a mapping. An ID can exist, be quoted
correctly, and still be the wrong control for the tool attached to it. That separate
judgement is recorded as `mapping_fidelity`: `direct`, `partial` or `supporting`. Only
`direct` mappings should ever be described to an assessor as enforced.

An unverified control ID in an assessor-facing document is worse than no document, so
the honest default is the strict one.
