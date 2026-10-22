# Knowledge base

Background an agent needs before working on the helper layer, the vendoring workflow, or
the adopter-facing configs at the root. Loaded on demand, not on every request.

## Everything ships live

| Tree | Status | Audience |
| :--- | :--- | :--- |
| `AGENTS.md`, `agents/`, `llms.txt` | **Live.** Describes this repository. | Agents working *here*, and an adopter who keeps them |
| `biome.json`, `playwright.config.ts`, `promptfooconfig.yaml` | **Live.** The adopter's toolchain, at the path each tool reads. | Repositories built *from* here |
| `.runwai/` | **Ours.** How the template was built. | Anyone working on runwAI itself |

There is no inert tree, and nothing here waits to be copied into place. A file that only
works once someone knows to copy it is a reference rather than a working file, and the user
who needs it most is the least likely to know it exists.

runwAI is Python, YAML and Markdown, so `biome.json` lints nothing *here*. That makes those
three configs **unexercised, not inert**: they are correct for the adopter and a no-op for
us, and `.runwai/tools/validate_helpers.py` checks the part of them that can still be checked — that
they parse, pin an exact version, and agree with the version README.md documents.

The one thing genuinely at risk from shipping live is a second `AGENTS.md`, which is a trap:
an agent reading the wrong file follows instructions for a codebase that does not exist. So
there is exactly one, at the root, and it speaks only to the adopter's agent — maintainer
instruction lives in `.runwai/MAINTAINERS.md`, loaded deliberately by a session that says
it is maintaining the template (decision 11).

See [decision 1](../.runwai/decisions.yaml) for what
gets copied in versus written here, and
[decision 2](../.runwai/decisions.yaml) for why nothing
ships as a template of a file.

## The vendoring workflow

This repository's premise is a *vendored* library: content lives here, pinned, rather than
being fetched at use time. That buys auditability and costs us the obligation to carry
provenance for everything we copy.

### The three derivation levels

Different levels carry different obligations, so record which one applies:

| Level | What it means | Obligation |
| :--- | :--- | :--- |
| `derived` | Upstream structure *and some upstream wording* survive | Attribution + `LICENSE-UPSTREAM` |
| `structure` | Layout or naming convention copied; all prose ours | Courtesy attribution only |
| `referenced` | We point at it, or implement its published spec | None |

Copyright protects expression, not ideas. Copying a *file taxonomy* is not copying a file.
Record all three anyway — the record is cheap and settles the question later.

### Steps

```bash
# 1. Resolve the commit. Never record a branch or tag: both move.
git ls-remote https://github.com/owner/repo HEAD

# 2. Read the licence from the tree, do not recall it.
git clone --depth 1 --filter=blob:none --sparse https://github.com/owner/repo /tmp/x
git -C /tmp/x sparse-checkout set --no-cone '/LICENSE*' '/COPYING*'

# 3. Copy what you need, and record repo + commit + licence in
#    .runwai/docs/provenance.md (or implementation.provenance in controls/registry.yaml).
```

Licence filenames vary. `LICENSE`, `LICENSE.md`, `LICENSE-APACHE`, `COPYING`, and the
British `LICENCE` all occur in practice — one of the ten sources recorded here uses the
last of those. Match loosely or you will conclude a project has no licence when it does.

### Licence families you will meet

| Family | Examples among our sources | What it permits |
| :--- | :--- | :--- |
| MIT | cal.com, promptfoo, nanochat, llms-txt-hub | Copy freely; retain the notice |
| Apache-2.0 | continue, backstage, vercel/ai, llms-txt | Copy freely; retain notice and state changes |
| **CC BY-SA 4.0** | OWASP LLM Top 10 | **Share-alike** — copied prose infects the receiving file |

The share-alike case is the one that bites. Copying OWASP text into a helper file would
place a copyleft obligation on that file and on everyone adopting this template. Cite the
identifiers, link the source, write your own sentences.

Dual licences (`MIT OR Apache-2.0`, as biome uses) mean you pick one. Record the string as
the upstream declares it.

## Network access, precisely

Not obvious, and getting it wrong produces confident false claims about being blocked:

| Path | Works? |
| :--- | :--- |
| `git` protocol to any public GitHub repo | **Yes** — `ls-remote`, clone, sparse checkout |
| `api.github.com/repos/{owner}/{repo}` | No — 403 for anything but this repository |
| `api.github.com/search/*` | No — unavailable entirely |
| `raw.githubusercontent.com` | No — blocked at CONNECT |
| PyPI, npm registry | **Yes** — direct, not proxied |

So: resolve SHAs with `git ls-remote`, never the REST API. A tool written against
`api.github.com/repos/` will report a blockage that does not exist — which is exactly what
happened to the retired inventory's verifier.

There is no repository search. Finding a slug means guessing and testing it with
`ls-remote`; a repository that does not exist prompts for a password rather than returning
a clean 404, so treat an auth prompt as "not found".

## Pinning tool versions

```bash
curl -s https://pypi.org/pypi/<pkg>/json | python3 -c "import json,sys; print(json.load(sys.stdin)['info']['version'])"
curl -s https://registry.npmjs.org/<pkg>  | python3 -c "import json,sys; print(json.load(sys.stdin)['dist-tags']['latest'])"
```

Both registries are reachable, so npm- and PyPI-distributed tools can be pinned and
verified now. GitHub *release binaries* are different: `git ls-remote --tags` shows a tag,
but a tag is not a confirmed release artifact. Do not set `verified_version: true` on the
strength of a tag alone.

If you cannot confirm a version, record none. See
[provenance-pin-exactly](rules/provenance-pin-exactly.md).

## Why the inventory was deleted

`docs/backlog-inventory.yaml` held 62 researched repository slugs, none resolved, several
fabricated. It was replaced by `.runwai/docs/provenance.md`: ten sources, each with a
resolved SHA and a licence read from the upstream tree.

The lesson is worth keeping even though the file is gone — a long list of unverified
references reads as thoroughness and functions as noise. One checked entry is worth sixty
plausible ones. See [decision 1](../.runwai/decisions.yaml).
