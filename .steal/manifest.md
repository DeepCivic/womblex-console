# 🗺️ Stealable Manifest

Curated under [`curation.md`](curation.md). Every row is a claim about a file, so keep it true:
if the file changes shape, change the row in the same commit or remove it.

Sorted by path. `Public` is takeable by anyone under the licence for that path — see the
permission table in `STEAL.md`, because this repository is not uniformly Apache-2.0.

| Path | Visibility | Tags | Description |
| :--- | :--- | :--- | :--- |
| `.github/scripts/doctor.sh` | Public | `bash`, `environment`, `reproducibility` | Environment parity check with no dependencies beyond bash and coreutils: declared variables against the environment, `mise.toml` or `.tool-versions` pins against the interpreters on PATH, declared write targets against the filesystem. Reads variable names, never values. Reports `not applicable` when a project declares nothing. |
| `controls/ism-tags.yaml` | Public | `ism`, `taxonomy`, `compliance` | Section-level semantic tags for all 1101 June 2026 ISM controls, plus the code / infrastructure / organisational surface judgement that decides which of them a repository could ever evidence. Tags 70 sections rather than 1101 controls so every claim in it is reviewable by a person in one sitting. Contains no ISM text, so it carries no CC BY obligation. |
| `controls/rules/deserialisation.yaml` | Public | `semgrep`, `sast`, `deserialisation` | Rules for deserialising untrusted data in formats that carry executable state — pickle, marshal, unsafe YAML, `eval` — plus model loading from pickle-backed formats. |
| `controls/rules/injection.yaml` | Public | `semgrep`, `sast`, `injection` | Sink-focused rules for SQL built by interpolation, shell commands assembled from untrusted input, and untrusted values reaching HTML sinks. Not taint-based, so verdicts are stable and the scan is fast. |
| `controls/rules/path-traversal.yaml` | Public | `semgrep`, `sast`, `path-traversal` | Rules for file paths built by interpolation and for joined paths reaching a filesystem call without canonicalisation, in Python and Node. Carries the per-language fix — realpath, path.resolve — and states what sink matching cannot see: zip slip, symlinks, TOCTOU. |

## What is banned, and why that matters more than the list above

The six fixture files in `controls/tests/` carry `STEAL: IGNORE`. They are working
vulnerabilities — SQL built by interpolation, `pickle.loads` on untrusted input, `eval` of a
payload, `open(f"/srv/data/{name}")` — written so each rule can be asserted against them. They read as ordinary, tested,
self-contained code, which is exactly what makes them dangerous: an agent scanning this
repository for something reusable would find well-commented functions that do the thing the
rules exist to prevent. A ban is cheap and the failure it prevents is not.

## Why the list is this short

Five files, and the reason is the four criteria in `curation.md` applied to ourselves.

**The three rulesets** have fixtures asserting each rule in both directions — it must fire
on the bad case and stay silent on the good one. That is the test the fourth criterion asks
for.

**`doctor.sh`** is the one script here that is genuinely liftable, and the reason is the
inverse of why the Python below is not. It reads three declaration formats that are not
runwAI's — `.env.example`, JSON Schema's `required`, and what mise reads — and compares
them to a machine. Nothing in it knows about the registry, the manifest or the section
vocabulary, and its only dependencies are bash and coreutils. Drop it into an unrelated
repository and it works there.

**`ism-tags.yaml`** is data, but it is checked data: `ism.py index` rejects a tag outside
the vocabulary, a surface outside the allowed set, an override with no reason or no such
control, and a section the ISM does not contain — and `ism.py index --check` then asserts
the derived index is current. Every claim in the file is machine-checked against the ISM
before it ships.

**The Python in `.runwai/tools/` and `.github/scripts/` stays off the list, and the reason
is coupling rather than testing.** `audit.py` is the closest call among them — trivy and
syft are ordinary tools and the offline-database pattern is worth copying — but what it
writes is this repository's report format, keyed to `docs/security-report.md`'s sections.
Read it for the pattern; the pattern is the part that travels. An earlier note here blamed the absence of tests, which
understated it: each of those files is written against runwAI's own layout — the registry
schema, the rule directories, the manifest format, the section registry. Adding tests would
not make them liftable, because what you would be lifting is a reader for a tree you do not
have. The honest advice is to read them for the pattern, which is what `curation.md` calls
boring, and to write your own.

Everything else is either boring — configuration and registry data that only means
something in place — or governed by an upstream licence that makes "steal it" the wrong
verb. Both cases are covered in `curation.md` and `STEAL.md`. The three root toolchain configs are the
closest call: they are self-contained and genuinely designed to be taken, but nothing in
this repository exercises them (runwAI has no JS/TS), so blessing them would be vouching
for files no check here has ever run. They ship live at the root instead, which is the
better answer to the same need — you get them without stealing them.
