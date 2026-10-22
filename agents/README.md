# runwAI agent documentation index

- **[../AGENTS.md](../AGENTS.md)** — main guide: the invariant, Do/Don't, boundaries
- **[running-the-checks.md](running-the-checks.md)** — the canonical command list
- **[knowledge-base.md](knowledge-base.md)** — domain knowledge and background
- **[rules/](rules/)** — modular engineering rules
- **[knowledge/](knowledge/)** — reference material loaded on demand
- **[skills/](skills/)** — self-contained skills with their own references

## How this layer is organised

Adapted from `calcom/cal.com` at `3894f37e` (MIT) — see
[`../.runwai/docs/provenance.md`](../.runwai/docs/provenance.md).

The structure exists so that rules are **modular** rather than piled into one prompt:

| Path | Loaded | Purpose |
| :--- | :--- | :--- |
| `../AGENTS.md` | Always | The minimum an agent must know |
| `rules/*.md` | On demand | One rule per file, named `{section}-{name}.md` |
| `knowledge/*.md` | On demand | Longer reference material |
| `skills/<name>/SKILL.md` | On demand | A task-shaped skill plus its `references/` |

Anything always-loaded costs tokens on every single request, so `AGENTS.md` stays short and
everything else is reachable by link rather than resident.

## Rules index

Sections are defined in [`rules/_sections.md`](rules/_sections.md); the section ID is the
filename prefix.

### Controls (CRITICAL)

- [controls-never-adjudicate-with-llm](rules/controls-never-adjudicate-with-llm.md) — the core invariant

### Provenance (CRITICAL)

- [provenance-pin-exactly](rules/provenance-pin-exactly.md) — exact versions, or none at all
- [provenance-record-upstream](rules/provenance-record-upstream.md) — SHA and licence for vendored content

### Quality (HIGH)

- [quality-claims-need-receipts](rules/quality-claims-need-receipts.md) — never assert what you did not check
- [quality-small-diffs](rules/quality-small-diffs.md) — keep changes reviewable
- [quality-comments-explain-why](rules/quality-comments-explain-why.md) — comment intent, not mechanics

### Testing (HIGH)

- [testing-assert-both-directions](rules/testing-assert-both-directions.md) — every rule needs a passing case
- [testing-document-false-positives](rules/testing-document-false-positives.md) — undocumented noise gets suppressed

### CI (HIGH)

- [ci-never-weaken-a-gate](rules/ci-never-weaken-a-gate.md) — fix the finding, not the check
- [ci-check-modes](rules/ci-check-modes.md) — a check runs by default only if its tooling
  binds to `.venv/`; anything else is off by default and says so

### Reference (LOW)

- [reference-file-locations](rules/reference-file-locations.md) — where things live
- [reference-local-dev](rules/reference-local-dev.md) — local setup

## Skills

- [vendor-upstream-content](skills/vendor-upstream-content/SKILL.md) — bring third-party
  content in with a resolved SHA and a verified licence

## Knowledge

- [llm-security-guardrails](knowledge/llm-security-guardrails.md) — guardrails for
  LLM-integrated code, keyed to the OWASP LLM Top 10 identifiers
- [explaining-a-control](knowledge/explaining-a-control.md) — how to answer
  `/explain RWA-XXXX`: grounded in the registry, plain language first, ISM detail
  hidden until asked

## Two layers

Everything an agent needs exists once, here, in a vendor-neutral form. On top of that sit
thin adapters at the paths a specific tool requires.

| Layer | Where | Contains |
| :--- | :--- | :--- |
| Canonical | `AGENTS.md`, `agents/` | All of it. Rules, knowledge, skills, the command list |
| Adapter | `.claude/commands/*.md` | Nothing of its own. Four pointers into `agents/` |

The adapters exist because a Claude Code slash command only works from `.claude/commands/`
— that is decision 2 applied to a vendor convention, not a second copy of the material. Add
a command by pointing it at `agents/`; never by restating instructions in it.

Two things this deliberately does not do. `agents/skills/` is canonical content reached
through `.claude/commands/vendor.md`, **not** a directory any skill runtime loads — Claude
Code reads `.claude/skills/`, which this repository does not use. And
`running-the-checks.md` is named that rather than `commands.md` so that "command" means one
thing: `.claude/commands/` holds slash commands, and shell commands live in a file that
does not claim the word.

## Attribution

The layout of this directory is derived from `calcom/cal.com` at commit `3894f37e`, MIT
licensed — see [`LICENSE-UPSTREAM`](LICENSE-UPSTREAM) and
[`../.runwai/docs/provenance.md`](../.runwai/docs/provenance.md). Their rule set was
Prisma/tRPC/Next.js specific and does not appear here; what carried over is the structure.

## Adding a rule

1. Copy [`rules/_template.md`](rules/_template.md) to `rules/{section}-{name}.md`
2. Use a section prefix that exists in `_sections.md`
3. Fill in the frontmatter: `title`, `impact`, `tags`
4. Add it to the index above

`python3 .runwai/tools/validate_helpers.py` checks that every rule file has a valid section prefix,
parseable frontmatter, and an entry in this index — so a rule that nobody linked is a build
failure rather than a file nobody reads.
