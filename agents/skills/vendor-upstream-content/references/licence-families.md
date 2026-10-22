# Licence families

Reference for the vendoring workflow. Practical guidance for this repository, not legal
advice — if a case is genuinely unclear, ask rather than guess.

## Permissive — vendor freely

| SPDX | Requires | Notes |
| :--- | :--- | :--- |
| `MIT` | Retain copyright notice and licence text | The common case |
| `BSD-2-Clause`, `BSD-3-Clause` | Retain notice; 3-clause adds a no-endorsement term | |
| `Apache-2.0` | Retain notice; **state significant changes**; `NOTICE` file if present | Includes a patent grant |
| `ISC` | Retain notice | Functionally MIT |

Copy the upstream licence text to `LICENSE-UPSTREAM` beside the vendored files and record
the SPDX identifier. For Apache-2.0, note at the top of the vendored file that it was
modified, if it was.

## Dual-licensed

`MIT OR Apache-2.0` (biome, and most of the Rust ecosystem) means you choose one. Record
the string exactly as upstream declares it and note which you rely on if it matters.

## Share-alike — do not copy prose

| SPDX | Problem |
| :--- | :--- |
| `CC-BY-SA-4.0` | Derivative works must be licensed alike |
| `GPL-2.0`, `GPL-3.0` | Copyleft; propagates to linked work |
| `AGPL-3.0` | Copyleft extending to network use |
| `MPL-2.0` | File-level copyleft — modified files stay MPL |

The obligation lands on whoever adopts this template, not just on us, which is why these
are refused by default rather than case-by-case.

**Encountered here:** the OWASP LLM Top 10 is CC BY-SA 4.0. We cite category identifiers
(LLM01–LLM10) and link the source; all surrounding prose is ours. Facts and short
identifiers are not protected expression. See
[`agents/knowledge/llm-security-guardrails.md`](../../../knowledge/llm-security-guardrails.md).

A share-alike source can still be `referenced` — read it, cite it, write your own words.
What you cannot do is paste it.

## No licence at all

A repository with no licence file is **all rights reserved** by default. Popularity is not
permission. Do not vendor from it; reference it instead, or ask upstream.

Watch for the British spelling `LICENCE` — one of this repository's ten recorded sources
uses it, and a filename match that only looks for `LICENSE` will wrongly conclude the
project has none.

## Content vs code

`llms.txt` is a published *specification*. Implementing a spec is not copying an
implementation, so a file written to conform to it is our own work regardless of how the
spec or its reference implementation is licensed. Same for a `biome.json` written against
biome's published schema, or a `promptfooconfig.yaml` against promptfoo's.

This distinction is why several sources in `.runwai/docs/provenance.md` are recorded as
`referenced` with no obligation despite our files resembling theirs in shape: what they
share is an interface, not expression.
