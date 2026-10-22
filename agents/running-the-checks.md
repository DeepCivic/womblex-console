# Running the checks

**The canonical list.** `AGENTS.md`, `README.md` and `agents/rules/reference-local-dev.md`
link here rather than restating these commands, because four copies of the same four
commands is four things to update when a path moves — which is exactly what happened when
the tools moved into `.runwai/tools/`.

Not to be confused with `.claude/commands/`, which are Claude Code slash commands. These
are shell commands. See "Two layers" in [README.md](README.md) for how those relate.

Every command here is offline and deterministic. None of them calls a model, and none
depends on the clock or the network — that is a property of the design, not a coincidence.

## Check modes

**A check runs by default when `make setup` can bind its tooling to `.venv/`.** That is the
whole test, and it is deliberately mechanical rather than a judgement about how important a
check is. `pre-commit`, `semgrep`, `detect-secrets` and `pyyaml` are Python packages, so pip
pins them into the project's own environment and they run on every session on any machine.
Bash and coreutils are not installed into anything, so `doctor` binds trivially and runs
everywhere too.

**A check whose tooling cannot be bound that way is environment-constrained, and
environment-constrained means off by default.** Whether it can run at all is a fact about
the machine — its architecture, its network egress, a gigabyte of free disk — so a session
must not assume it ran.

| Mode | What it covers | How it runs |
| :--- | :--- | :--- |
| `default` | Everything venv-bound or install-free: the commit hook, `check`, `verify`, `doctor`, `report`, the self-checks | `make first-session`, or any target by name |
| `full` | The above, plus the environment-constrained checks | `make first-session CHECK_MODE=full`, or the constrained target by name |

One check is environment-constrained today, and it fails the `.venv/` test because its tools
are compiled binaries from a release page, not packages:

| Check | Why it cannot bind to `.venv/` | Opt in with |
| :--- | :--- | :--- |
| The dependency audit | `trivy` and `syft` are architecture-specific release binaries, and the advisory database is ~1 GB from a container registry that corporate and cloud networks routinely block | `make setup-audit-tools && make setup-audit-dbs && make audit` |

**Off by default never means quiet, and it never means passing.** `make first-session`
prints what did not run, what that leaves unknown, and the command that turns it on;
`docs/security-report.md` states that no dependency audit output was supplied to the run.
A check that is off has measured nothing, which is a different thing from having found
nothing — the same distinction this repository draws between `not applicable` and a pass.

**Naming a constrained target is itself the opt-in.** `make audit` always runs when you ask
for it; `CHECK_MODE` governs only whether the default session attempts it. And nothing here
is a gate that moved after it went red — see
[`agents/rules/ci-check-modes.md`](rules/ci-check-modes.md) for the line between designing
where a check runs and weakening one that failed.

**CI is unaffected and runs the constrained checks unconditionally.** A GitHub runner has
the architecture, the egress and the disk, so the constraint does not apply there — see
`.github/workflows/posture.yml`, which installs the scanners and downloads the database as
ordinary steps.

## Setup

```bash
make setup                                  # the pinned toolchain, into .venv/
make hook                                   # pre-commit install
```

**The toolchain installs into `.venv/`, not into the machine's Python**, and every `make`
target puts `.venv/bin` on `PATH` for you. Running the commands on this page by hand is
the one case that needs saying so once per shell:

```bash
export PATH="$PWD/.venv/bin:$PATH"          # or: source .venv/bin/activate
```

Without it these commands run against whatever Python is on the machine, which carries
whichever versions that machine happens to have rather than the pinned ones — and for the
scanners, usually nothing at all. Two consequences worth knowing: deleting `.venv/` breaks
the installed commit hook until `make setup && make hook` runs again, and the `make`
targets still work with no venv present, which is how CI runs them with its pins installed
globally.

The self-checks additionally need `pyyaml==6.0.3` and `jsonschema==4.26.0`; `pre-commit`
installs both into its own hook environments, so the hook needs nothing extra.

The adopter-facing steps are also `Makefile` targets — `make first-session`, or `setup`,
`hook`, `check`, `verify`, `audit`, `doctor` and `report` individually. The Makefile wraps
the commands on this page and adds none of its own, so this list stays canonical.

The dependency scanners are release binaries rather than packages, so they have their own
setup targets — `setup-audit-tools` and `setup-audit-dbs`, both networked, both described
under **The dependency audit** below. Being binaries is also why the audit is
environment-constrained and off by default; see **Check modes** above. `make first-session`
runs `doctor` last and does not let it abort the session, and reports the audit as `NOT RUN`
unless `CHECK_MODE=full`.

## The self-checks

```bash
python3 .runwai/tools/validate_registry.py     # structure, determinism invariant, pinning, provenance, overlap
python3 .runwai/tools/ism.py verify            # every ISM claim against controls/ism-snapshot.json
python3 .runwai/tools/validate_helpers.py      # AGENTS.md, agents/, root configs, llms.txt, .runwai/
python3 .runwai/tools/ism.py index --check     # the semantic index matches snapshot + tags
```

`validate_helpers.py` also takes optional file paths. They narrow the STEAL marker sweep to
those files and nothing else — every other check in it still runs against the whole tree.
Pre-commit passes the staged files that way so a commit does not re-read a tree it did not
touch. **Run it with no paths when you want the answer that counts**: the whole-tree sweep
is the only one that sees a marker added by a commit that skipped the hook, and it is how
the `posture` workflow and `report.py` invoke it.

Regenerate the index after editing `controls/ism-tags.yaml`:

```bash
python3 .runwai/tools/ism.py index             # writes controls/ism-index.json
```

Exit codes are uniform across all three:

| Code | Meaning |
| :--- | :--- |
| 0 | Passed. Warnings may still have printed. |
| 1 | One or more checks failed. |
| 2 | Could not run — missing dependency or unreadable input. |

Add `--strict` to treat warnings as failures. CI moves to `--strict` once the pending pins
in `.runwai/docs/pinning.md` are complete; until then, warnings are expected.

## The checks that stop something

**Only one does, and it runs on your own machine.** `pre-commit` is the single place in
this repository where a check can prevent an action, and `--no-verify` walks past it. CI
reports; it does not block. Making a red check stop a merge is branch protection, a setting
on the repository rather than a file, and nothing here installs it.

```bash
pre-commit run --all-files             # everything the hook runs
pre-commit run runwai-semgrep --all-files    # one hook
```

Run a ruleset's fixtures, asserting each rule fires on the bad case and stays silent on the
good one:

```bash
semgrep --test --config controls/rules controls/tests
```

Scan the whole tree the way the pre-commit hook scans your staged files:

```bash
semgrep scan --error --metrics=off \
  --config controls/rules/injection.yaml \
  --config controls/rules/deserialisation.yaml \
  --config controls/rules/path-traversal.yaml \
  .
```

`--error` is what turns findings into a non-zero exit. Without it semgrep reports and exits
zero, which is the most common way a scanner ends up installed but enforcing nothing. The
`posture` workflow deliberately runs the same rulesets *without* `--error`, capturing the
findings to JSON for the report instead.

## Secret scanning

One tool, `detect-secrets`, in two places. It is `language: python` in
`.pre-commit-config.yaml` with `detect-secrets==1.5.0` in `additional_dependencies`, so
`pre-commit` installs it and there is nothing extra to set up.

- **Commit hook** — `detect-secrets-hook --baseline controls/.secrets.baseline` over the
  staged files. This is the only place a secret is *blocked*, and `--no-verify` walks past it.
- **CI** — the `secrets` job in `.github/workflows/posture.yml` runs the same tool, version
  and baseline over every tracked file, not just what one commit staged. Same corpus, so the
  local and CI verdicts cannot diverge; wider reach, so a secret in a file that arrived
  behind `--no-verify` is still caught on the next push.

Neither pass walks reachable git history, so a credential committed and later deleted is not
caught. That leg of RWA-0010 is unmapped, and the registry note for RWA-0010 says so.

To reproduce the CI scan locally, over the whole tree:

```bash
git ls-files -z \
  | grep -zvE '^(controls/\.secrets\.baseline|controls/ism-snapshot\.json|controls/ism-index\.json)$' \
  | xargs -0 detect-secrets-hook --baseline controls/.secrets.baseline
```

If a run is noisy, record what is there in the baseline rather than lowering the floor, then
review and commit the updated baseline:

```bash
detect-secrets scan --baseline controls/.secrets.baseline
```

## The verification receipts

```bash
make setup                                            # the pinned scanners it drives
python3 .github/scripts/verify.py                     # prove the checks catch what they claim
```

It finds `semgrep` and `detect-secrets-hook` on `PATH` rather than importing them, which is
why the `export PATH` line under **Setup** matters here specifically: without it the
receipts report `COULD NOT RUN` for scanners that are installed a directory away.

Adopter-facing, stdlib-only, offline. Runs every active rule against the committed
fixtures in both directions, twice (identical verdicts required); asserts the fixture
floor (three vulnerable and one safe case per rule, so an untested rule cannot pass
silently); and scans a fake credential generated at run time the way the commit hook
scans. Output is plain language with a fix per failure; exit codes follow the house
convention above. `--no-install-check` skips the commit-hook check — it is for CI,
where a checkout has no hooks. The `posture` workflow runs it on every push.

## The dependency audit

**Environment-constrained, so off by default** — its two scanners are release binaries that
cannot be installed into `.venv/`. `make first-session` reports it as `NOT RUN` rather than
attempting it; running any of the three commands below is the opt-in, and
`make first-session CHECK_MODE=full` attempts it inline. See **Check modes** above.

Two networked setup steps, then an offline scan. The database is an input rather than an
ambient service, which is what makes the verdict reproducible: refresh it and you know a
changed verdict came from the advisories, not the code.

```bash
make setup-audit-tools       # trivy 0.72.0 and syft 1.50.0, checksum-verified
make setup-audit-dbs         # the vulnerability database, once (~1 GB in .audit-cache/)
make audit                   # offline from here: --skip-db-update --offline-scan
```

`setup-audit-tools` installs into `.audit-cache/bin/`, and every `make` target puts that
directory on `PATH` for you — the same arrangement as `.venv/bin` under **Setup** above.
Running these three by hand needs it saying once per shell, and the `export` belongs
**before** `setup-audit-dbs` rather than after, because that step is trivy downloading
trivy's own database:

```bash
export PATH="$PWD/.audit-cache/bin:$PATH"   # before setup-audit-dbs, not after
```

Writes `docs/dependencies.md` (the bill of materials, committed and timestamp-free) and
`.audit-cache/audit.json` (the result the security report reads). Exit codes follow the
house convention above: `0` clean **or nothing to audit**, `1` known vulnerabilities, `2`
a scanner or the database is missing.

**The two legs fail independently.** The bill of materials needs `syft` and nothing else —
no database, no network — so a machine that cannot download the database still writes
`docs/dependencies.md` and reports `NO VULNERABILITY SCAN` for the other half. The result
JSON carries a `scan` field (`ran`, `not applicable`, `could not run`) so the report states
which happened instead of inferring it from an empty finding list, which looks identical to
a clean one.

An ecosystem with no manifest in the tree reports `not applicable` by name, never as a
pass. **This is not on the commit hook and must not be put there** — a CVE published
overnight is not a reason a commit cannot be saved. It runs in the `posture` workflow and
in `make first-session`, where it is not allowed to abort the run.

## The environment check

```bash
make doctor                  # or: bash .github/scripts/doctor.sh
```

Compares what the repository declares — `.env.example` or `config.schema.json` for
variables, `mise.toml` or `.tool-versions` for runtime pins — against the machine it is
running on. Bash and coreutils only, so it runs before anything is installed, which is
the machine most likely to be wrong.

It reads variable *names* and never their values, including from `.env`. A project that
declares nothing reports `not applicable` and exits 0. Exit codes: `0` matched or nothing
declared, `1` something declared is missing or mismatched, `2` could not run. Remedies are
printed as `mise` commands, because mise reads all three declaration formats.

## The report

```bash
python3 .runwai/tools/report.py                # writes .runwai/docs/report.md
python3 .runwai/tools/report.py --check        # fail if .runwai/docs/report.md is stale
```

`.runwai/docs/report.md` is generated, committed, and deliberately **timestamp-free**: regenerating it
on an unchanged tree produces a byte-identical file. A report carrying a timestamp produces
a diff on every run, so the diff stops carrying information and reviewers learn to ignore
the file — the same trap the `posture` workflow's secret-scan step already documents.

## The security report

```bash
python3 .github/scripts/security_report.py            # coverage only, no scanners
python3 .github/scripts/security_report.py \
  --findings semgrep.json --audit .audit-cache/audit.json \
  --scan-scope "local, changed files"
```

Writes `docs/security-report.md`. Blocks nothing and has no staleness gate — it carries a
generation timestamp instead, so a stale copy says so on its face rather than failing a
build. Run without `--findings` and it says plainly that no scanner output was supplied,
which is not the same as nothing found; the same goes for `--audit` and the **Dependency
posture** section, which is kept separate from code findings so that a clean codebase on a
vulnerable dependency cannot read as clean.

The `posture` workflow runs it on every push and pull request, publishes it to the job
summary, and uploads it as an artifact.

## Verifying an upstream source

```bash
git ls-remote https://github.com/owner/repo HEAD          # resolve a commit SHA
git ls-remote --tags --refs https://github.com/owner/repo # list release tags
```

Use the git protocol, not `api.github.com`. The REST API is scoped to this repository and
returns 403 for `/repos/{owner}/{repo}` on anything else; `/search/*` is unavailable
entirely. Git has no such restriction.

To read a file from a large upstream repository without cloning all of it:

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/owner/repo /tmp/x
git -C /tmp/x sparse-checkout set --no-cone '/AGENTS.md' '/LICENSE'
```

## Checking a tool version before pinning it

```bash
curl -s https://pypi.org/pypi/<package>/json | python3 -c "import json,sys; print(json.load(sys.stdin)['info']['version'])"
curl -s https://registry.npmjs.org/<package> | python3 -c "import json,sys; print(json.load(sys.stdin)['dist-tags']['latest'])"
```

PyPI and the npm registry are both directly reachable. A tag in `refs/tags` is **not** the
same as a confirmed release artifact — confirm the release before setting
`verified_version: true`.
