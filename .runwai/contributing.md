# Contributing to runwAI

Read [`docs/architecture.md`](../docs/architecture.md) first. The core invariant — AI may do
the setup work, controls must be deterministic — is enforced by
`.runwai/tools/validate_registry.py`, so a contribution that violates it fails CI rather than
review.

## Before you start

```bash
pip install pre-commit==4.6.1
pre-commit install
```

Run both self-checks before pushing:

```bash
python3 .runwai/tools/validate_registry.py
python3 .runwai/tools/ism.py verify
```

## Adding a check

There is no capability directory. A check is a rule file plus its fixtures, and the control
record in `controls/registry.yaml` that says where it runs and where it came from.

```
controls/rules/<name>.yaml       the ruleset
controls/tests/<name>.py|js      annotated fixtures, named to match
```

1. **The control record** gains an `implementation` block: the `gate` that runs it, the
   `files` that carry it, and a `provenance` block. `validate_registry.py` checks the gate
   is real and every named file is in the tree, so a control cannot reach the security
   report's "has a check behind it" row on a claim nobody verified. A control without the
   block is mapped and nothing runs, which the report states in those words.

2. **Fixtures must assert every rule in both directions.** Semgrep pairs a rules directory
   with a parallel fixture directory by basename, so `controls/rules/injection.yaml` needs
   `controls/tests/injection.py`:

   ```python
   # ruleid: runwai-python-sql-string-building
   cur.execute(f"SELECT * FROM users WHERE id = {user_id}")

   # ok: runwai-python-sql-string-building
   cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
   ```

   The `ok:` cases matter more than the `ruleid:` ones. A rule that flags
   `cur.execute("SELECT 1")` teaches developers to ignore the scanner.

   ```bash
   semgrep --test --metrics=off --config controls/rules controls/tests
   ```

3. **Document the false-positive classes at the top of the rule file.** This is not
   optional politeness. A rule whose false positives are undocumented gets suppressed
   wholesale within a month, and a suppressed rule is a control that reports green while
   enforcing nothing.

## Adding a control

Every control in `controls/registry.yaml` needs:

- **A `direct`, `partial` or `supporting` `mapping_fidelity`.** Be pessimistic. `direct`
  means the tool enforces what the control actually requires; if it covers a subset, say
  `partial` and state the gap in `notes`. Only `direct` mappings get described to an
  assessor as enforced.

- **Verbatim `ism_text` for every claimed ID.** Copy it from
  `controls/ism-snapshot.json`, not from memory or from another document.
  `.runwai/tools/ism.py verify` fails on any drift, which is what stops a control outliving the
  wording it was mapped against.

- **Exactly pinned tools.** No `latest`, `*`, `^`, `~` or bare major tags. If you cannot
  confirm a version exists, set `install: unavailable` and **omit the version** — do not
  guess. See [`.runwai/docs/pinning.md`](docs/pinning.md).

- **Honest `enforcement`.** If the tool's verdict can change between runs on identical
  input, it is `probabilistic` and cannot block unless you write a
  `deterministic_assertion` explaining what reproducible check makes it gateable. Look at
  RWA-0071 for the pattern: the assertion replays a fixed committed corpus offline rather
  than asking whether the model behaved.

### Do not map a control you have not read

The most common error in this repository's history was citing plausible-looking ISM IDs
without checking them. Four mappings in the original draft were disproved by reading the
authoritative text — ISM-1601 turned out to be about Microsoft's attack surface reduction
rules, which has nothing to do with container hardening. Read the control in
`controls/ism-snapshot.json` before mapping a tool to it.

## Vendoring third-party content

If `provenance.origin` is `vendored` or `derived`, you must record:

- `upstream.repo` as `owner/repo`
- `upstream.commit` as a **full 40-character SHA** — a branch or tag is not a pin
- `upstream.license` as an SPDX identifier
- `LICENSE-UPSTREAM` alongside the vendored files

The validator rejects vendored content without an upstream licence. runwAI is
Apache-2.0; vendored content keeps its own licence and we cannot relicense it.

## Overlap policy

Two controls should not vendor the same `upstream.repo` and path. If duplication is
genuinely warranted, set `provenance.overlap_approved: true` with an `overlap_reason`.
The validator enforces this. It implements the original backlog's rule that overlap be
negligible and only introduced with approval.

## Contributing to the AI helper layer

`AGENTS.md`, `agents/`, `llms.txt`, `.runwai/` and the root toolchain configs sit outside
`controls/` and are checked by `.runwai/tools/validate_helpers.py` instead of
`validate_registry.py`. It is stdlib-only and offline, so it runs before anything is
installed:

```bash
python3 .runwai/tools/validate_helpers.py
```

It fails on a link to a file that does not exist, a rule whose section prefix is not
declared in `agents/rules/_sections.md`, a rule missing frontmatter or not linked from
`agents/README.md`, a root config that does not parse or whose pinned version disagrees
with the table in `README.md`, and an ADR without a `**Status:**` line. Each of those is a
way this layer rots silently.

**Adding a rule.** Copy `agents/rules/_template.md` to `agents/rules/{section}-{name}.md`,
fill in the frontmatter, and add it to the index in `agents/README.md`. Explain the
*consequence* of getting it wrong, not just the instruction — a rule whose failure mode is
understood gets applied to cases the file did not anticipate. State honestly what enforces
it, or say "convention only".

**Adding something for the adopter.** Put it where its tool already looks — a command in
`.claude/commands/`, a skill in `agents/skills/`, a config at the root — never in a
directory they have to find and copy from. If it cannot run against this repository, say so
where they read it, record the upstream version it was written against, and add whatever
check is still possible: parsing and version agreement, at minimum. Unexercised is
acceptable and must be stated; inert is not. See
[decision 2](decisions.yaml).

**Keep `AGENTS.md` short.** It is loaded on every request. Anything long or situational
belongs in `agents/rules/` or `agents/knowledge/`, reached by link.

`.claude/commands/*.md` are thin pointers into `agents/`, never copies. Restating
instructions there guarantees the two drift apart.

`report.md` is generated. Run `python3 .runwai/tools/report.py` and commit the result; do not edit
it by hand. It is timestamp-free so that a diff means the tree actually changed.

## Vendoring for the helper layer

Same discipline as a check, recorded in `.runwai/docs/provenance.md` rather than a
the control's `implementation.provenance`. The full procedure is in
[`agents/skills/vendor-upstream-content/SKILL.md`](../agents/skills/vendor-upstream-content/SKILL.md).

Two things catch people out:

- **Resolve SHAs with `git ls-remote`, not `api.github.com`.** The REST API is scoped to
  this repository and returns 403 elsewhere, with no repository search. The git protocol
  reaches any public repository. A tool written against the REST API reports a blockage
  that does not exist.
- **Refuse share-alike sources.** CC BY-SA and copyleft obligations propagate to everyone
  adopting this template, not just to us. Cite and paraphrase instead, and record the
  derivation as `referenced`. See
  [`agents/skills/vendor-upstream-content/references/licence-families.md`](../agents/skills/vendor-upstream-content/references/licence-families.md).

Read the licence from the upstream tree rather than from memory, and match filenames
loosely — `LICENSE`, `LICENSE.md`, `LICENSE-APACHE`, `COPYING` and the British `LICENCE`
all occur in practice.

## Commit and PR expectations

- Every job in the `posture` workflow must be green before you merge. **Nothing enforces
  this** — the repository has no branch protection, so merging red is possible and is on
  you. ISM-2032 requires automated testing to complete without warnings, alerts or errors;
  runwAI maps that control as `supporting` precisely because a convention is not a
  mechanism, and pretending otherwise is the failure this repository is about.
- If a change alters what a control enforces, update the control's `notes` and
  `mapping_fidelity` in the same commit.
- If a change resolves a pending pin, move its row in `.runwai/docs/pinning.md`.
