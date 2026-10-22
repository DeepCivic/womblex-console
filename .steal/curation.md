# Curating the steal manifest

The protocol behind [`STEAL.md`](../STEAL.md). That file is addressed to the agent taking
code *from* this repository; this one is for the agent — or person — working *in* it,
deciding what earns a place on [`manifest.md`](manifest.md) and keeping the index true. It
works in any repository: the markers are inert comments, the manifest is plain Markdown,
and there is no tool to install and nothing to build.

## ✅ Good to steal

An item earns a manifest row only when all four hold:

1. **Whole Units**: Self-contained functions, classes, or components. No arbitrary fragments.
2. **Absolute Purity**: Deterministic. No hidden global state, no implicit side effects.
3. **Low Coupling**: Highly cohesive with minimal internal dependencies.
4. **Tested**: Accompanied by tests. Untested code is a liability.

## 😐 Boring to steal

Most of any codebase falls here. It is normal, contextual application logic.

- **Action**: Read it to understand how the app works.
- **Rule**: Do **not** add boring items to the manifest.

## ❌ Bad to steal

- Anything with hidden global state or side effects.
- Untested or unverified code.
- Files explicitly marked with `STEAL: IGNORE`.

## 🧠 How to curate

To mark a file, use a standard, inert comment directly above the export:

- **Bless (Public)**: `// STEAL: Pure exponential backoff utility.`
- **Ban**: `// STEAL: IGNORE: Niche workaround with limited reusability.`
- **Boring**: Requires no `STEAL:` action.

> 💡 **Safety Rule:** Edit the comment style (e.g. `//`, `#`, or `/** */`) to conform with
> your project's linter warnings or IDE squiggles. The marker is the word `STEAL:`, not the
> comment syntax around it.

## 🤖 Agent enrichment & validation protocol

**On Commit (Enrichment):**

1. Scan changed files for `STEAL:` comments.
2. Extract the file path, description, and infer 2–3 semantic tags (e.g. `util`, `network`).
3. Add or update the row in [`manifest.md`](manifest.md). Keep the table sorted by path —
   two agents enriching the same manifest must produce the same diff.

**On Reuse (Validation):**

1. Read the manifest to find candidates.
2. **Staleness Check**: Verify the current file content still logically matches the
   manifest description. A manifest row is a claim about a file, and a claim nobody
   rechecked is the failure mode this repository names under verification discipline
   (see [`agents/rules/quality-claims-need-receipts.md`](../agents/rules/quality-claims-need-receipts.md)).
3. Check the licence table in [`STEAL.md`](../STEAL.md), then steal the file — whole, not
   in fragments — and respect the bans. A `STEAL: IGNORE` is usually there to save you
   from something that looks reusable and is not.

In this repository the protocol is enforced, not just described:
`.runwai/tools/validate_helpers.py` fails the build when a blessed file has no manifest
row, a row points at a file that is gone, or the table is unsorted.

## 🧑 If you are not using an agent

Before sharing a utility, add `STEAL: <description>` in a comment above the export. If you
forget, an agent will prompt you on your next commit. Adding the row by hand takes about ten
seconds, and the table is plain Markdown — there is no tool to install and nothing to build.
