# Status and known limits

What is present in the template, and what is honestly known about it.
`.runwai/tools/report.py` checks four of the counts below — agent rules, agent skills,
recorded decisions and vendored sources. **Everything else here, including the control and
fidelity counts, is maintained by hand against `controls/registry.yaml` and nothing verifies
it.** Say which, rather than claiming the counts are checked: an unchecked number sheltering
under a blanket claim is how the fidelity split below shipped wrong and stayed wrong.

## Present

| | |
| :--- | :--- |
| Controls mapped | 36 (6 `direct`, 24 `partial`, 6 `supporting`) |
| ISM release | June 2026 — **all 36 controls verified against the snapshot**, 0 fabricated IDs |
| Controls with a mechanism behind them | 9 of 36. The rest are mapped with nothing running, and `docs/security-report.md` says so in those words |
| Rule tests | 14 rules across 3 rulesets, each asserted on both a failing and a passing case |
| Dependency audit | trivy 0.72.0 and syft 1.50.0, pinned by release checksum. Offline against a downloaded database snapshot; reports per ecosystem, `not applicable` where no manifest exists. Environment-constrained, so **off by default** locally (decision 18) and unconditional in CI |
| Environment check | `make doctor`, bash and coreutils only. Deliberately **not** a control: it checks reproducibility, not security, so it is absent from the registry |
| AI helper layer | `AGENTS.md`, 12 agent rules, 1 skill — structure derived from upstream, licences verified |
| Adopter toolchain configs | 3, live at the root. Unexercised here: runwAI has no JS/TS |
| Vendored sources | 10, each pinned to a resolved 40-character commit SHA |
| Where checks run | `pre-commit` locally, which is the only thing that stops anything and is bypassable; `posture` in CI, which reports. No merge gate, by design |
| Secret scanning | detect-secrets, pinned, on the commit hook and again over the whole tree in the CI `secrets` job. No reachable-history walk — that leg of RWA-0010 is unmapped and the registry note says so |

## Limits, deliberately visible

**Most mappings are `partial`.** The ISM is not a CI specification. Of 36 controls only 6
are `direct` — the tool enforces exactly what the control requires. `partial` means it
covers part of it; `supporting` means it produces evidence but does not satisfy the
control. Only `direct` mappings should be described to an assessor as enforced. See
[`../../docs/ism-verification.md`](../../docs/ism-verification.md).

**Six tools are unpinned.** cosign and hadolint ship as GitHub release binaries whose
versions have not been confirmed; coverage, branch-protection-audit, codeowners-audit and
lockfile-registry-audit name work nobody has written. All are recorded with **no version
at all** rather than a guessed one — pinning a scanner to a version nobody checked is the
same class of error as citing an unverified control ID. None of them runs anywhere, so no
check depends on the missing pins.

Two left the list by being resolved and one by being replaced. trivy and syft are now
pinned to a version, a platform asset and a SHA-256 read from each release's own
checksums file, because RWA-0031 needed them to actually run. grype is simply gone: it was
named for the dependency-scanning leg and never ran, and trivy does that job now. gitleaks
went the same way earlier, replaced by keyhog — and keyhog has since been removed too,
leaving detect-secrets as the sole secret scanner. See [`pinning.md`](pinning.md).

**The AI helper layer is derived, not original.** `AGENTS.md`, `agents/` and the root
toolchain configs are adapted from a small set of upstream projects, each recorded with
a resolved commit SHA and its upstream licence in [`provenance.md`](provenance.md). This
replaced a 62-entry research inventory: ten sources that were actually used and verified,
instead of sixty-two that were not.

**The three root toolchain configs are unexercised.** runwAI is Python, YAML and Markdown,
so nothing here runs Biome, Playwright or promptfoo: a mistake inside one of those configs
fails no check in this repository. They ship live at the root regardless, because that is
where the adopter's tools read them and a file nobody knows to copy is a file nobody uses
([decision 2](../decisions.yaml)). What is enforced is that
each parses, declares an exact version, and agrees with the version table in `README.md`;
`playwright.config.ts` is additionally in scope for our own semgrep rulesets. Run them in a
real project before relying on them.

**The commit-time gate is heavier than its design intends.** The stated shape is fast
checks on save and the full set at the merge boundary, with a leaked credential the one
thing worth stopping a commit for. `pre-commit` today runs seven blocking hooks — SAST, the
registry self-check, ISM verification, the ISM index check, the helper-layer check and a
report-freshness check alongside the secret scan — which makes saving your work the
heaviest gate rather than the lightest. That is a gate placed in the wrong place, not a
weakened one: nothing was moved after it failed. Rebalancing it is
[`backlog.yaml`](../backlog.yaml) id_5.

## Verification discipline

This repository's history contains two classes of error, both of which look like competent
work until checked. Plausible ISM control IDs that were never read — four mappings in the
original draft were disproved by reading the authoritative text. And repository slugs
asserted without resolution — a 62-entry inventory was deleted rather than verified, several
entries being fabricated.

The pattern in both is fluent output about something nobody checked. If a claim cannot be
verified, say so and mark it unverified. That is always the cheaper outcome.
