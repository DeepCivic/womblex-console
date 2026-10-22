# Tool pinning status

Every control in `controls/registry.yaml` names the tools that enforce it, pinned to
an exact version. An unpinned scanner is a non-deterministic control by definition —
its ruleset can change under you and silently alter verdicts — so
`.runwai/tools/validate_registry.py` rejects floating specifiers (`latest`, `*`, `^`, `~`,
bare major tags).

## Verified pins

These versions were confirmed to exist at the time of writing. Everything except trivy and
syft is installed from PyPI directly rather than through third-party marketplace actions,
which keeps the trusted surface to one registry and the pins reviewable in one place.

| Tool | Version | Class | Controls |
| :--- | :--- | :--- | :--- |
| trivy | 0.72.0 | sca, container-scan | RWA-0031, 0051 |
| syft | 1.50.0 | sbom | RWA-0031, 0032 |
| semgrep | 1.171.0 | sast | RWA-0002, 0003, 0011, 0012, 0020–0026, 0041, 0060, 0061, 0073, 0074 |
| checkov | 3.3.8 | iac-scan, config-scan | RWA-0005, 0011, 0040, 0041, 0042, 0061 |
| detect-secrets | 1.5.0 | secret-scan | RWA-0002, 0010, 0071 |
| bandit | 1.9.4 | sast | RWA-0003, 0012, 0060 |
| cyclonedx-bom | 7.3.1 | sbom, cbom | RWA-0003, 0032, 0033, 0034, 0062 |
| sslyze | 6.3.1 | tls-scan | RWA-0041 |
| schemathesis | 4.24.2 | schema-test, dast | RWA-0072 |
| presidio-analyzer | 2.2.364 | pii-filter | RWA-0071 |
| garak | 0.15.1 | ai-fuzz | RWA-0070 |

### Secret scanning is detect-secrets alone

RWA-0010 is enforced by detect-secrets, pinned in the table above, on the commit hook and
again over the whole tree in the CI `secrets` job. keyhog was carried here for a while as
the CI scanner — a Rust binary pinned to the commit behind `v0.5.47` — and was removed: it
was one more thing baked into the template, and running one tool at one version in both
places means the local and CI verdicts cannot diverge. The cost of the removal is the
reachable-history walk keyhog did and detect-secrets does not, recorded in the RWA-0010
registry note and in [`decisions.yaml`](../decisions.yaml) (decision 19, superseding 7).

## Pending verification

These are recorded in the registry as `install: unavailable` with **no version**,
which the validator reports as a warning. They carry no invented version number
deliberately: pinning a tool to a version nobody confirmed is the same class of error
as citing an unverified control ID.

| Tool | Class | Controls | Why unpinned |
| :--- | :--- | :--- | :--- |
| cosign | signing | RWA-0035, RWA-0036 | GitHub release binary |
| hadolint | container-lint | RWA-0050 | GitHub release binary |
| coverage | coverage-gate | RWA-0024 | Language-specific; needs one ruleset per ecosystem |
| branch-protection-audit | config-scan | RWA-0001 | Forge API script, not yet written |
| codeowners-audit | config-scan | RWA-0004 | Forge API script, not yet written |
| lockfile-registry-audit | config-scan | RWA-0030 | Not yet written |

### How the trivy and syft pins were verified

Neither is on PyPI, so both receipts are recorded rather than assumed — the same discipline
every non-PyPI pin gets, and for the same reason.

| Claim | How it was checked |
| :--- | :--- |
| trivy `0.72.0`, syft `1.50.0` | Highest semver tag in `git ls-remote --tags --refs` on each upstream, sorted numerically rather than lexically |
| The releases are real | A tag is not a release. Each platform asset was requested and returned `200`: `trivy_0.72.0_Linux-64bit.tar.gz` and `syft_1.50.0_linux_amd64.tar.gz`, plus the ARM64 pair |
| The assets are pinned by content | SHA-256 for all four assets read from each release's own `checksums.txt`, recorded in the `Makefile`, and verified against the downloaded archives. A tag can be moved to point at new assets; a checksum cannot |
| Licence `Apache-2.0` | Read from `LICENSE` in each upstream tree at the pinned tag — not from the README, and not from memory |

grype left the pending table by being replaced rather than resolved: RWA-0031 uses trivy
and syft now, and nothing here names grype.

### Completing a pin

1. Confirm the release exists and note the exact tag.
2. Record the version and `verified_version: true` in `controls/registry.yaml`, and
   change `install` from `unavailable` to the real method.
3. Move the row from this section to the table above.
4. Run `python3 .runwai/tools/validate_registry.py` — the warning for that tool should clear.

Once every pin is verified, CI can move to `--strict`, which fails on warnings.

## Also pending: checkov check IDs

checkov and its allowlist were deleted by TODO-15. What follows records what the audit
found while they existed: the config listed check IDs selected
against the control text but not confirmed against checkov's own registry. **Checkov
silently ignores an unknown check ID**, so a misspelling means a control you believe is
enforced simply does not run.

An `iac` job used to verify this by diffing the claimed IDs against `checkov --list`. It
went with the workflow it lived in, and nothing verifies check IDs today. Recorded here so
that whoever reintroduces checkov reintroduces the verifier with it — and fixes the
verifier's own defect on the way in, because it had one.

**That verifier's extraction regex was `CKV[A-Z_]*_[0-9]+`, which permits no digit inside
the middle segment, so `CKV_K8S_19` never matched.** `CKV_K8S_19`, `CKV_K8S_20` and
`CKV_K8S_21` were invisible to the gate meant to catch bad IDs. The correct pattern is
`CKV[A-Z0-9_]*_[0-9]+`. It damages both sides of the comparison, so fixing only the claimed
side produces three false failures. The defect was recorded rather than fixed, because the
job that carried it was deleted with the capability it served; this paragraph is that
record now that the backlog item holding it has been closed and removed under the policy in
[`backlog.yaml`](../backlog.yaml).

## GitHub Actions pins

The workflows use `actions/checkout@v4`, `actions/setup-python@v5` and
`actions/upload-artifact@v4` — first-party actions at stable major tags. Pinning
actions to a commit SHA is stricter and worth doing if runwAI is used in an
environment where the ISM's cyber supply chain controls (ISM-1568, ISM-1787) are being
assessed against the pipeline itself.
