---
title: A check runs by default only if its tooling binds to the project environment
impact: HIGH
impactDescription: A check the machine cannot run must say so, not fail silently or read as clean
tags: ci, checks, determinism, honesty
---

## A check runs by default only if its tooling binds to the project environment

**Impact: HIGH (a check the machine cannot run must say so, not fail silently or read as clean)**

**The test is mechanical: can `make setup` install this check's tooling into `.venv/`?**

If yes, the check is on by default. Python packages pin into the project's own environment,
so `semgrep`, `detect-secrets` and `pre-commit` run on every session on any machine. A check
that needs no install at all — `doctor` is bash and coreutils — passes the test trivially
and is on by default too.

If no, the check is **environment-constrained** and is **off by default**. The dependency
audit is the standing example: `trivy` and `syft` are architecture-specific release
binaries rather than packages, so they install into their own directory, and the advisory
database is about a gigabyte pulled from a container registry that corporate and cloud
networks routinely block. Whether that check can run at all is a fact about the machine, and
a session must never assume it ran.

Use the mechanical test rather than asking how important the check is. Importance is exactly
the argument that keeps a constrained check switched on, where it then fails on a third of
the machines that adopt the template — and a check that fails for environmental reasons
teaches its reader to ignore the output, which costs more than the check was worth.

**Off by default is a claim about the machine, never about the risk.** Three things must
hold, and the third is the one that is easy to lose:

1. The default run says what did not run, in a sentence the reader can act on.
2. It says what that leaves **unknown** — not "no findings", which is what an absent check
   silently produces.
3. Turning it on is one documented command, and naming the target is itself the opt-in.

**Incorrect** — the check is off, and off is indistinguishable from clean:

```make
first-session: setup hook check verify
	@$(MAKE) audit || true      # exits 2 when the scanners are absent; `|| true` eats it
```

The reader sees a step that ran and a session that continued. Nothing told them their
dependency posture is unmeasured, and `|| true` turned "could not run" into no signal at
all.

**Correct** — the check is off, and off is louder than the swallowed exit code was:

```make
CHECK_MODE ?= default

first-session: setup hook check verify
	@if [ "$(CHECK_MODE)" = "full" ]; then \
	  $(MAKE) --no-print-directory audit || true; \
	else \
	  printf '%s\n' \
	    "Dependency audit: NOT RUN — environment-constrained, so it is off by default." \
	    "  So you do not yet know whether the packages you depend on carry known" \
	    "  vulnerabilities. That is not the same as knowing they carry none." \
	    "  Turn it on:  make setup-audit-tools && make setup-audit-dbs && make audit"; \
	fi
```

### This is not the rule against weakening a gate

[ci-never-weaken-a-gate](ci-never-weaken-a-gate.md) prohibits moving or softening a check
*after* it goes red. Classifying a check by what its tooling needs is design, decided in
advance, and it is the same carve-out that rule already makes for `posture` running semgrep
without `--error`.

Two facts keep the distinction clean, and both must be true before a check is moved into the
constrained set:

- **It was never a gate.** The dependency audit blocks nothing, is not on the commit hook,
  and must not be — a CVE published overnight is not a reason a commit cannot be saved.
- **The change makes it louder, not quieter.** Before the mode existed the audit exited 2
  and `|| true` discarded it. After it, the default run states plainly that no vulnerability
  scan happened. If a proposed "off by default" reduces what the reader is told, it is a
  weakening wearing this rule as a costume.

CI is a separate machine and the constraint does not apply there. A runner has the
architecture, the egress and the disk, so `.github/workflows/posture.yml` installs the
scanners and downloads the database as ordinary steps. Do not carry the local default into
CI: the reason for the default is the adopter's laptop and their employer's proxy, neither
of which is a runner.

Enforced by: review. Nothing mechanically checks that a check sits in the right mode — the
`.venv/` test is applied by whoever adds the check, which is why it is written down as a
test with one answer rather than as a matter of judgement.

Reference: [agents/running-the-checks.md](../running-the-checks.md) for the current
classification, and [docs/architecture.md](../../docs/architecture.md) for the invariant the
honesty requirements descend from.
