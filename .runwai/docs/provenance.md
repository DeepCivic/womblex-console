# AI helper layer: provenance

Every file in `AGENTS.md`, `agents/` and the root toolchain configs that was shaped by an
upstream project is recorded here, with the exact commit it was taken from and the licence
that commit carried.

This file replaces `docs/backlog-inventory.yaml`, a 62-entry research list in which no
entry had been resolved and several were fabricated. Ten sources are recorded here
instead of sixty-two, and each one is checked. Rationale in
[decision 1](../decisions.yaml).

## How to read this

The field names deliberately match the `upstream` block in
the `implementation.provenance` block in `controls/registry.yaml`, so this table can be
folded into the registry later
without rewriting it.

| Field | Meaning |
| :--- | :--- |
| `repo` | `owner/repo` on GitHub |
| `commit` | Full 40-character SHA. A branch or tag is not a pin. |
| `license` | SPDX identifier, **read from the upstream tree**, not inferred from memory |
| `resolved` | True only when both the commit and the licence were actually retrieved |

Three levels of derivation are distinguished, because they carry different obligations:

- **derived** — upstream structure and some upstream wording survive in our files.
  Requires attribution and a `LICENSE-UPSTREAM`.
- **structure** — the layout, naming convention or file taxonomy was copied; all prose is
  ours. Attribution recorded as a courtesy; no licence obligation attaches to an idea.
- **referenced** — we point at the project or follow its published specification, and
  copied nothing.

## Sources

All ten were resolved on 2026-07-25 by `git ls-remote` and a blob-filtered sparse clone.
Licences were read from each upstream tree, not assumed.

| repo | commit | license | derivation | what we took |
| :--- | :--- | :--- | :--- | :--- |
| `calcom/cal.com` | `3894f37e14eae5082770f35ff1fde72110c0e6b6` | MIT | **derived** | `AGENTS.md` skeleton (Do / Don't / Boundaries), `agents/` layout, the `{section}-{rule}.md` convention with `_sections.md` + `_template.md`, `agents/skills/<name>/SKILL.md` + `references/` |
| `continuedev/continue` | `5522c6f44ca0ac3528b37244818fbfa39b5af470` | Apache-2.0 | structure | Model-agnostic skill definitions kept separate from vendor-specific command files |
| `AnswerDotAI/llms-txt` | `8aef59184056547644e0d34aeceeeeb46fc7c2f4` | Apache-2.0 | referenced | The `llms.txt` specification itself (llmstxt.org) |
| `thedaviddias/llms-txt-hub` | `11615bcd25607b4b76b0acdb69af22d408413514` | MIT | referenced | Confirmation of how the convention is applied in practice |
| `backstage/backstage` | `4956d7ffc5b091fc14b0fd29d417b2100fb4f132` | Apache-2.0 | structure | ADRs as numbered, immutable Markdown under `docs/adr/` |
| `biomejs/biome` | `c50a8538f08795c4ffa3db03ad77945020e9920a` | MIT OR Apache-2.0 | referenced | `biome.json` is our own config against their published schema |
| `karpathy/nanochat` | `92d63d4e8bb4df75c3b71618f31ddde2378b2bcd` | MIT | structure | The `report.md` pattern: one generated Markdown file summarising a run |
| `vercel/ai` | `eb16508fc79aa18f7132852126446db69d3b1b70` | Apache-2.0 | structure | Playwright configuration shaped for streaming responses |
| `promptfoo/promptfoo` | `b16373873b095ab5abb00dbd57fd10e864d3f6fe` | MIT | referenced | `promptfooconfig.yaml` is our own file against their published schema |
| `OWASP/www-project-top-10-for-large-language-model-applications` | `020595761a4b7b0c3f9cf01a0457b78f9f1e7f9c` | **CC-BY-SA-4.0** | referenced | Category identifiers LLM01–LLM10 only |

### The OWASP licence constrains what we may copy

The OWASP LLM Top 10 is **CC BY-SA 4.0** — share-alike. Copying its prose would place a
copyleft obligation on the file that received it, and by extension on anyone who adopts
this template. `agents/knowledge/llm-security-guardrails.md` therefore cites the category
identifiers and links to the source, and every sentence around them is ours. That is a
deliberate constraint, not an oversight: it keeps the whole helper layer Apache-2.0.

### One entry that did not resolve

`software-mansion/agent-skills` **does not exist**. The organisation resolves, and so do
its other repositories (`react-native-reanimated`, `radon-ide` were both checked), so this
was a genuine absence rather than an access failure. The retired inventory had "corrected"
a malformed owner name into a slug that was never real, which is exactly the failure mode
that made the inventory worth deleting. Dropped, not substituted.

## Re-resolving these

```bash
git ls-remote https://github.com/calcom/cal.com HEAD
```

`api.github.com` is bound to this repository and returns 403 for
`/repos/{owner}/{repo}` on anything else, and `/search/*` is unavailable entirely. The
**git protocol has no such restriction**. Any tool written to re-check these should use
`git ls-remote`, not the REST API, or it will report a blockage that is not there.

A commit recorded here is a historical fact and does not go stale. Re-resolve only when
deliberately adopting newer upstream material — and if you do, update `commit`, re-read
the licence, and say so in the commit message.
