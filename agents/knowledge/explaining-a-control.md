# Explaining a control in plain language

How to answer `/explain RWA-0021` (or an ISM ID). It is usually asked because IT, a
reviewer or an assessor put a compliance question to someone who builds products rather
than compliance. The command exists so that detail stays out of the way until the moment
it is needed, then arrives grounded rather than recalled.

## Ground rules

1. **Read, never recall.** Every factual sentence traces to a field in
   `controls/registry.yaml` or, for unmapped ISM IDs, `controls/ism-snapshot.json`.
   Never quote control text from memory: the registry's `ism_text` is verbatim and
   verified against the snapshot; memory is neither. This repository's own history
   contains fluent, fabricated control IDs — that is why this rule exists.
2. **Plain language first.** No ISM vocabulary and no registry field names in the
   answer. If a term from either would help, translate it instead of using it.
3. **Explain, never adjudicate.** This command produces understanding and fix
   instructions — never a pass/fail verdict. Verdicts belong to the pinned checks.

## Answer shape, by default

Three short parts, in this order:

- **What it means for this project.** Read the tree before answering. A control about
  database queries in a project with no database is *not applicable* — say so, and say
  that not applicable is not a pass.
- **What runs here.** From `mechanism`, `implementation` and `mapping_fidelity`:
  an `implementation` block means a real gate — name it in plain words ("checked when
  you commit", "reported in CI, blocks nothing"). No block means mapped with nothing
  running — say that, never imply coverage. Translate `mapping_fidelity`: `direct`
  means the check enforces what the control asks, `partial` means some of it,
  `supporting` means it produces evidence only.
- **What to do, if anything.** Fix instructions concrete enough for an agent to
  execute — "replace X with Y in `file.py`" — then offer to do it. If the entry's
  `notes` record false-positive classes or alternative paths (a password manager
  satisfies RWA-0012 with no hashing code at all), fold that in: it changes the advice.

## Hidden until asked

Only on request: the verbatim `ism_text` and ISM IDs, tool names and pinned versions,
and the verification receipt — `verification_source`, `verified_on`, and the registry's
`ism_release` block, which carries the upstream source and version an assessor will
want (the ISM release, and the snapshot's SHA-256).

## Look-ups

- `RWA-XXXX` — the entry in `controls/registry.yaml`.
- An ISM ID — search the registry's `ism_ids`. If no entry claims it, quote it verbatim
  from `controls/ism-snapshot.json` and say plainly: in the baseline, not mapped here,
  nothing checks it.
- A topic rather than an ID ("what does the ISM say about backups?") —
  `controls/ism-index.json` is the semantic index; start there.
- An ID in neither place — say it does not exist. Never invent a control ID.
- "How do I prove the checks actually work?" — `python3 .github/scripts/verify.py`,
  the verification receipts. Run it and relay its verdict rather than re-deriving it.

## Never

- Never describe anything as compliant, or a green check as satisfying a control.
- Never describe the commit hook as preventing a merge — `--no-verify` walks past it,
  and merge blocking is branch protection, a setting at the forge.
- Never require the user to understand the ISM, or runwAI's vocabulary, to act on the
  answer.
