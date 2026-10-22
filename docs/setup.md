# How this project is set up

**This file is as-built, not a proposal.** It describes what is actually configured in this
repository right now — what runs, what was removed, and why. When you change the setup,
change this file in the same commit so it stays true. It is the first thing an agent should
read after `AGENTS.md` when it needs to know what it is working inside.

It arrives describing runwAI as it ships. Everything below is accurate on day one and
becomes yours as your agent adapts it.

## What runs, and when

| When | What happens | Does it stop you? |
| :--- | :--- | :--- |
| While you build | Nothing | No |
| On commit | Secret scan and SAST on what you staged, plus structural self-checks | Yes — this is the only place anything stops |
| On push and pull request | The same checks again, plus the dependency audit, the environment check, and `docs/security-report.md` | No, never |

**Nothing here prevents a merge.** The commit hook is the only thing that stops an action,
and `git commit --no-verify` walks past it. CI reports. If you want a failing check to
actually block a merge, switch on branch protection for this repository and require the
`posture` jobs — that is a setting at your forge, and no template can turn it on for you.

The last row is the point of the repository. It answers "how does what I have built compare
to a security baseline?" and it blocks nothing, so it is safe to ignore until you want it.

## What checks your code

| Control | Mechanism | Covers |
| :--- | :--- | :--- |
| RWA-0010 | `detect-secrets`, pinned, at commit time and over the whole tree in CI | Credentials before they enter history, then every tracked file on each push |
| RWA-0003, RWA-0020, RWA-0021 | `controls/rules/injection.yaml` | SQL, shell and HTML sink injection |
| RWA-0022, RWA-0074 | `controls/rules/deserialisation.yaml` | pickle, marshal, unsafe YAML, `eval`, pickled model loading |
| RWA-0027 | `controls/rules/path-traversal.yaml` | File paths built by interpolation, and joined paths opened without canonicalisation |
| RWA-0031, RWA-0032 | `trivy` 0.72.0 and `syft` 1.50.0, pinned, in CI and on `make audit` — **off by default locally** | Known vulnerabilities in third-party packages, and the bill of materials at `docs/dependencies.md` |

Fourteen rules and one dependency audit. That is the whole of it, and it is deliberate — a
first release defends a small surface honestly rather than a large one badly. Every other
control in `controls/registry.yaml` is mapped with nothing running, and
`docs/security-report.md` says so in those words.

The audit is reported under its own heading, apart from the code findings: a clean
codebase on a vulnerable dependency is not secure, and the two have to be separable for
the report to say so. It runs in CI and on demand, never on the commit hook, and it scans
offline against a downloaded database snapshot whose date the report records — so the
same lockfiles and the same snapshot always give the same verdict.

Its two halves fail independently. The bill of materials needs `syft` alone, so a network
that blocks the vulnerability database still produces `docs/dependencies.md`; the report
then says a scan did not run, in those words, rather than showing an empty finding list
that reads like a clean result.

**It is also the one check that is off by default here.** `make setup` binds every other
tool into `.venv/`, but `trivy` and `syft` are release binaries rather than packages, and
the advisory database is about a gigabyte from a registry many corporate networks block —
so whether the audit can run is a fact about your machine, and `make first-session` does
not assume it. It prints `NOT RUN` with what that leaves unknown and the command that turns
it on:

```bash
make setup-audit-tools && make setup-audit-dbs && make audit
```

Naming any of those is the opt-in, and `make first-session CHECK_MODE=full` attempts the
audit inline. CI is unaffected — a runner has the architecture, the egress and the disk, so
`.github/workflows/posture.yml` installs the scanners and downloads the database on every
push. **Off by default is a statement about the machine, never about the risk:** until the
audit runs, your dependency posture is unknown rather than clean, and
`docs/security-report.md` says so under **Dependency posture**. The rule that decides which
checks are treated this way is `agents/rules/ci-check-modes.md`.

## Where the toolchain is installed

`make setup` installs the pinned tools into `.venv/` in this directory rather than into the
machine's Python. That is not a style preference: installing globally fails outright on
Debian and Ubuntu images, either because a distribution-managed package cannot be replaced
or because pip refuses to touch an externally-managed environment, and both failures land
on the first command of the first session where they are least interpretable. Every `make`
target puts `.venv/bin` on `PATH` itself — and `.audit-cache/bin`, where the two audit
binaries land, for the same reason. To run the commands in `agents/running-the-checks.md` by
hand, do it once per shell:

```bash
export PATH="$PWD/.venv/bin:$PWD/.audit-cache/bin:$PATH"
```

`.venv/` is gitignored and disposable — the pins that decide its contents live in the
`Makefile`. Deleting it breaks the installed commit hook until `make setup && make hook`
runs again. The targets still work with no venv at all, which is how CI runs them with its
pins installed globally.

`make doctor` sits beside them and is **not** a control. It compares the environment this
project declares to the one it is running in; that is a reproducibility check, not a
security one, so it is deliberately absent from `controls/registry.yaml`. Putting it there
would inflate the coverage count without adding coverage.

None of it is taken on trust: `python3 .github/scripts/verify.py` proves each rule catches
its committed vulnerable examples and stays silent on the safe ones, and CI re-proves it on
every push. See `agents/running-the-checks.md`.

## The toolchain configs, and deleting the ones you do not need

Three configs ship at the root. They do three unrelated jobs, and **most projects need
fewer than three.** Deleting one you will not use is the correct action, not a compromise —
a config nobody runs is a file that rots and misleads the next reader.

| File | Job | Delete it when |
| :--- | :--- | :--- |
| `biome.json` | Formatting and linting for JavaScript and TypeScript | There is no JS/TS here, or you use a different formatter |
| `playwright.config.ts` | Browser and end-to-end tests | There is no browser UI to test |
| `promptfooconfig.yaml` | Deterministic evals for prompts and agent tools | Nothing here calls a language model |

Deleting one is three edits in the same commit: the file, its row in `README.md`'s
toolchain table, and its entry in `llms.txt`. A self-check fails on any left behind, so you
will be told rather than left with a dangling reference. Record the removal below.

## The agent guide, and the bridge to it

`AGENTS.md` is the canonical guide and the file every agent should read first. `CLAUDE.md`
is one line — `@AGENTS.md` — because Claude Code reads that filename and does not read
`AGENTS.md`; without the bridge, the guide is invisible to it. Keep the bridge as an import.
Copying the guide's content into it would give you two files to keep in step, which is the
drift the single canonical file exists to avoid. Claude-specific instructions go below the
import.

## The reuse layer

`STEAL.md` and `.steal/` are a protocol for publishing units of code other people can lift:
a file is blessed with an inert `STEAL:` comment, `.steal/manifest.md` indexes it, and a
self-check fails the build when the two disagree. **Whether this repository has it is your
call, and your agent is instructed to ask rather than assume** — it depends on whether you
want anything here reused, which nothing in the tree can tell it.

It ships present and inert: nothing is blessed until someone writes a marker, and it blocks
nothing either way. Removing it means deleting both `STEAL.md` and `.steal/` in one commit,
plus their entries in `llms.txt` and every link into them — `make check` names the links, so
nobody has to remember them. The self-check treats both-gone as a decision and one-gone as an
error, so a half-removal reports itself. Record the choice below.

## What was removed from the template

Nothing yet. Record deletions here as your agent makes them, with a line saying why, so a
later reader does not spend an afternoon looking for a directory that was removed on
purpose.

## What this repository cannot tell you

The ISM governs a system: the people who run it, where it is hosted, who is allowed near
it. This repository sees code and a pipeline. Of 1101 controls, 694 are organisational and
no repository can evidence them. A green build here is not compliance and must never be
described as such.
