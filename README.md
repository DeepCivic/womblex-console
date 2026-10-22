# runwAI

A template repository for people building software with an AI agent. It gives you two
things:

1. **Practical scaffolding for AI coding** — an agent guide the agent reads on its own, a
   set of engineering rules, and live toolchain configs at the paths their tools already
   look for.
2. **A way to understand your project's security posture** — a small set of ordinary,
   pinned checks, and a generated report that says in plain language what ran, what it
   found, and what nobody looked at.

You are not a security engineer and should not have to become one to ship. Nothing here
asks you to learn a framework, and the report is written for someone who will never read
one.

## Quick start

**First, take a copy.** On GitHub, **Use this template → Create a new repository**, then
clone it. That step is GitHub's, not ours — everything after it is one step.

**Then, one step.** Open your new repository with your AI agent and tell it:

> Read `AGENTS.md`, then set this repository up for me and tell me what it will and will
> not check.

Everything else — installing the hook, working out which of the root configs your project
actually needs, offering to delete the maintainers' directory, explaining what the checks
cover and what they cannot — is the agent's job, and `AGENTS.md` instructs it to do that
without being asked. **You do not need to read the rest of this file to start.**

<details>
<summary><strong>What that first session should look like</strong></summary>

So you can tell whether your agent actually did it. It should, without further prompting:

1. Tell you in a few sentences what you now have, and what it will and will not check
2. Run `make first-session` — install the commit hook, run every check once over
   everything, and prove the checks catch what they claim
3. Ask what you are building, then delete the root configs you do not need
4. Offer to delete `.runwai/`, the maintainers' directory, and prune what refers to it —
   including telling you, before deleting, that some of the rules it ships stop being
   mechanically enforced when it goes
5. **Ask whether you want other people to be able to reuse pieces of this**, and keep or
   remove `STEAL.md` and `.steal/` on your answer — not on its own guess
6. Record what it did in [`docs/setup.md`](docs/setup.md)
7. **Rewrite `AGENTS.md` to describe your project rather than this template**, and say that
   it has
8. Tell you — unprompted — that nothing here can block a merge, that a green report is not
   compliance, that the dependency audit did **not** run and what one command turns it on,
   and that you can ignore the control identifiers entirely

If it did none of that and simply waited for instructions, say *"follow the first-session
steps in `AGENTS.md`"*. Needing to ask is a defect here; the fallback should not be
necessary.

</details>

<details>
<summary><strong>The same thing by hand</strong></summary>

```bash
make first-session
```

That runs the session's mechanical steps in order, each pinned to an exact version:
`make setup` (install the toolchain), `make hook`, `make check` (everything, over the
whole tree), `make verify` (prove the rules catch what they claim), `make doctor`
(environment, and not allowed to abort the session), then `make report`. Run them
individually when you want one. Or `/selfcheck`, which runs every check and reports what
failed. The full list, with exit codes, is in
[`agents/running-the-checks.md`](agents/running-the-checks.md). Every check is offline
and deterministic — no network, no clock dependence, no model. Three targets touch the
network and they are the only ones: `make setup`, and `make setup-audit-tools` and
`make setup-audit-dbs`, which fetch the pinned dependency scanners and the vulnerability
database the audit then runs against offline.

**One check is missing from that list on purpose.** `make audit` — which asks whether the
packages you depend on carry known vulnerabilities — needs two programs that cannot be
installed alongside everything else, and about a gigabyte of vulnerability database from a
network some employers block. So it is **off by default**, and the first session tells you
so rather than quietly skipping it. Until you run it your dependency posture is *unknown*,
which is not the same as clean. Turning it on is one command, once per machine:

```bash
make setup-audit-tools && make setup-audit-dbs && make audit
```

`make setup` installs into a `.venv/` folder inside the project rather than into your
machine's Python, so setting this up changes nothing else on your computer and every
`make` target finds it without being told — including the two audit programs above, which
land in `.audit-cache/bin/`. To run the underlying commands by hand, put them on your
`PATH` once per shell with `export PATH="$PWD/.venv/bin:$PWD/.audit-cache/bin:$PATH"`.

</details>

**You should not have to know what to ask for.** That is the design constraint, and it is
the one most easily lost. Someone who does not know that a check can be irrelevant to what
they are building cannot think to ask an agent about it — so that knowledge lives in
[`AGENTS.md`](AGENTS.md), where the agent reads it without being prompted. If using this
repository well depends on you knowing the right question, that is a defect here, not a gap
in you.

The same constraint is why nothing here waits to be copied into place. Every file you
receive arrives as the working thing it claims to be, in the location its tool already
looks.

## When the checks run, and what stops you

| Moment | What happens | Does it stop you? |
| :--- | :--- | :--- |
| While you are building | Nothing. Write code, try things, break things | No |
| You save your work | The checks run on what you staged | Yes |
| You push, or open a pull request | The same checks again, plus the report | No |

**Nothing here can prevent a merge, and it will not pretend otherwise.** The commit hook is
the only thing in this repository that stops an action, and `git commit --no-verify` walks
straight past it. CI reports.

If you want a failing check to actually block a merge, turn on branch protection for your
repository and require the `posture` jobs. That is a setting at GitHub, not a file — which
is exactly why no template can switch it on for you, and why one that claims to is lying.

## What actually checks your code

| Control | Mechanism | Covers |
| :--- | :--- | :--- |
| RWA-0010 | `detect-secrets` at commit time, and over the whole tree in CI | Credentials before they enter history, then every tracked file on each push |
| RWA-0003, 0020, 0021 | `controls/rules/injection.yaml` | SQL, shell and HTML sink injection |
| RWA-0022, 0074 | `controls/rules/deserialisation.yaml` | pickle, marshal, unsafe YAML, `eval`, pickled model loading |
| RWA-0027 | `controls/rules/path-traversal.yaml` | File paths built by interpolation, and joined paths opened without canonicalisation |
| RWA-0031, 0032 | `trivy` and `syft`, in CI and on `make audit` — off by default locally | Known vulnerabilities in the packages you depend on, and the bill of materials listing them |

**Fourteen rules and one dependency audit, and that is the whole of it.** A first release
defends a small surface honestly rather than a large one badly. Every other control in
`controls/registry.yaml` is mapped with nothing running, and `docs/security-report.md`
says exactly that rather than implying coverage.

The rules read the code you wrote. The audit reads the packages it depends on, and the two
are reported separately on purpose — clean code sitting on a vulnerable dependency is not
secure, and a report that pooled them would let it look that way. It never blocks a
commit, and it names every ecosystem it did not scan rather than counting silence as a
pass. It runs on every push in CI, where the machine can always support it; locally it is
off until you turn it on, and the report says so rather than leaving the section blank.

**And you do not have to take the fourteen on trust.** `python3 .github/scripts/verify.py`
proves each rule fires on committed, deliberately vulnerable examples and stays silent on
the safe ones beside them — twice, requiring identical verdicts — and that the secret
scanner catches a fake credential. Its output is written for someone who has to convince
IT that the checks actually work, and it is equally plain about what a pass does not mean.

**No model is ever the check.** An AI can write the code, and wrote most of this
repository. But if you ask a model "is this code secure?", you can get different answers to
the same question, and a rule that changes its mind is not a rule. So every check here is
an ordinary, boring program pinned to an exact version: give it the same code twice and it
returns the same verdict twice, forever. That invariant is enforced mechanically rather
than by convention, and argued in full in [`docs/architecture.md`](docs/architecture.md).

## Reading the security report

[`docs/security-report.md`](docs/security-report.md) is generated, blocks nothing, and is
the artefact this repository exists to produce. It sorts every control into four rows, and the distinctions are the
whole value:

| Row | What it means |
| :--- | :--- |
| Has a check behind it | Something in this repository is wired to it |
| Mapped, nothing runs | Recorded as in scope, with nothing behind it yet |
| Unassessed | Evidence could exist in code or infrastructure. Nothing here looks |
| Out of scope | People, policy, premises. No repository can evidence these |

The controls come from the Australian Government's Information Security Manual, used as a
requirements baseline while building this template — a ready-made list of what a security
review asks about, rather than one invented here. **You do not need any ISM obligation for
this to be useful.** Ignore the control identifiers and the four rows still tell you what is
checked and what is not.

When someone does ask you about a specific control — IT, a reviewer, an assessor — tell
your agent: `/explain RWA-0021`. It answers in plain language from the control registry,
says what actually runs here and what to do about it, and keeps the ISM detail back until
you ask for it.

**A green report is not compliance.** It means the code you wrote did not trip a set of
automated checks. Nobody should tell an assessor otherwise.

## What this does not require

runwAI has to be useful to a project that has none of the following, and must not break
because one is missing:

| You may not have | What runwAI does about it |
| :--- | :--- |
| Any compliance obligation | The control mapping is a lens, not a requirement. Ignore it and everything else works |
| Any infrastructure code | Nothing here scans it, and the report says so rather than implying coverage |
| Containers, a cloud account, a release process | No check here depends on one existing |
| Any security knowledge | The agent is instructed to explain findings in plain terms, unprompted |

**A check with nothing to look at is *not applicable*, not a failure.** A tool that fails a
project for not having Terraform teaches its user to switch the tool off, and a switched-off
check is indistinguishable from a passing one.

## The toolchain configs

These three ship **live**, at the root, where each tool already looks. There is nothing to
copy and nothing to find: tell your agent what you are building and it edits them in place
— or deletes the ones you do not need, which is the correct action rather than a
compromise.

| File | Package | Version | Licence |
| :--- | :--- | :--- | :--- |
| `biome.json` | `@biomejs/biome` | 2.5.5 | MIT OR Apache-2.0 |
| `playwright.config.ts` | `@playwright/test` | 1.62.0 | Apache-2.0 |
| `promptfooconfig.yaml` | `promptfoo` | 0.121.19 | MIT |

Pin those exact versions when you install them. The version above is the one each file was
*written against*, not a claim that newer releases are incompatible — check the upstream
changelog when you bump, and change this table in the same commit, because a self-check
fails the build if a config and this table disagree.

Nothing in this repository exercises them — runwAI is Python, YAML and Markdown — so run
them in your own project before relying on them.

## Where things are

This root is busier than most repositories you have seen, and on purpose: nothing here
waits in a starter directory to be copied into place, so every file sits live where its
tool — or its reader — already looks. What looks unusual is doing a job, and your agent's
first session trims it to what your project actually needs.

```
controls/           The control library: the registry, the fourteen semgrep rules and
                      the fixtures asserting each one in both directions
docs/               setup.md — how this project is set up, as built; your agent keeps
                      it true — security-report.md, your posture readout, and
                      dependencies.md, the bill of materials. The last two are
                      generated and block nothing; the report is the artefact this
                      repository exists to produce
Makefile            The first session's mechanical steps as pinned, deterministic
                      targets: `make first-session`
AGENTS.md           Agent entry point — the obligations your agent reads unprompted
CLAUDE.md           An `@AGENTS.md` import and nothing else. Claude Code reads this
                      filename and not the other one, so without the bridge the guide
                      above is invisible to it
agents/             Rules, the canonical command list, knowledge and skills. Yours
llms.txt            Machine-readable index (llmstxt.org convention)
STEAL.md            The fast path for anyone — or any agent — taking code from here.
                      Your agent asks in the first session whether you want it at all
biome.json, playwright.config.ts, promptfooconfig.yaml
                    Your toolchain, shipped live at the root
.runwai/           The maintainers' directory: notes and the template's own self-check
                      readout, kept by the people who build runwAI itself. Nothing you
                      build depends on it, and deleting the whole folder breaks nothing
                      in your project
```

Everything except that last one describes *your* repository and comes with you.

## Documentation

- [`docs/setup.md`](docs/setup.md) — how this project is configured right now: what runs,
  what was removed, what it cannot tell you
- [`AGENTS.md`](AGENTS.md) — how an agent should work in this repository
- [`agents/README.md`](agents/README.md) — index of agent rules, commands, skills and
  knowledge
- [`docs/architecture.md`](docs/architecture.md) — the invariant, what determinism means
  precisely, provenance and licensing rules
- [`docs/ism-verification.md`](docs/ism-verification.md) — how the control text was
  verified, and how to re-verify it after a new release
- [`STEAL.md`](STEAL.md) — how to take code from here in four steps, and which paths are
  not Apache-2.0; the curation protocol behind it is
  [`.steal/curation.md`](.steal/curation.md)

## Licence

runwAI's own content is Apache-2.0 (see [LICENSE](LICENSE)). Vendored third-party content
keeps its upstream licence and runwAI does not and cannot relicense it; no share-alike
content is copied anywhere in this repository, which keeps the whole helper layer
Apache-2.0 for anyone adopting the template. Upstream, commit SHA and licence are recorded
per file, and per control under `implementation.provenance` in `controls/registry.yaml` —
[`STEAL.md`](STEAL.md) has the permission table and points at the rest.

Control text in `controls/ism-snapshot.json` is from the Australian Government's
Information Security Manual, © Commonwealth of Australia, released under CC BY 4.0. runwAI
is not an ASD publication and carries no ASD endorsement.
