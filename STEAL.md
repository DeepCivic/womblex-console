# STEAL.md — how to take code from this repository

You are reading this because you — a person, or more likely their AI agent — want to lift
something from here into another project. Good: parts of this repository are built to be
taken, and this file is the fast path. No licence archaeology, no reading the whole tree.

## Take something in four steps

1. **Open [`.steal/manifest.md`](.steal/manifest.md).** It is the curated index of
   everything safe to take — path, tags, one line saying what each item is. If that file
   is missing, assume nothing here is safe to steal.
2. **Check the licence for the path you are taking**, in the table below. One licence does
   not cover this tree.
3. **Recheck the claim.** A manifest row is a claim about a file, and a claim nobody
   rechecked is how reuse goes wrong. Read the file and confirm it still matches its row
   before lifting it.
4. **Take the whole unit** — the file, with its tests where the row points at them. No
   fragments: an item is on the manifest because it is self-contained, deterministic and
   tested, and a fragment forfeits all three.

## The licence, per path

runwAI's own content is Apache-2.0, in [`LICENSE`](LICENSE). Vendored third-party content
keeps its upstream licence and runwAI does not and cannot relicense it:

| Path | Licence | Notes |
| :--- | :--- | :--- |
| Everything not listed below | Apache-2.0 | [`LICENSE`](LICENSE) |
| `agents/` | MIT | Structure derived upstream; [`agents/LICENSE-UPSTREAM`](agents/LICENSE-UPSTREAM) |
| `controls/ism-snapshot.json`, `controls/ism-source.txt` | CC BY 4.0 | © Commonwealth of Australia. Attribution required |

Per-item provenance is in [`.runwai/docs/provenance.md`](.runwai/docs/provenance.md) and in each
control's `implementation.provenance` in `controls/registry.yaml`.

## Do not take these

- **Anything marked `STEAL: IGNORE`** — above all the fixture files in `controls/tests/`.
  They are working vulnerabilities, written so each security rule can be asserted against
  them, and they read as exactly the well-commented, self-contained code an agent scanning
  for something reusable would pick up. The ban is there to save you.
- **Anything not on the manifest.** The rest of this repository is ordinary contextual
  code and configuration that only means something in place. Read it to understand how
  things work, then write your own — the manifest's closing notes say why the list is as
  short as it is.

## Want the same protocol in your repository?

The manifest stays honest because files are blessed and banned with an inert `STEAL:`
comment, an agent keeps the index in sync on every commit, and a deterministic self-check
fails the build when the two disagree. That protocol lives in
[`.steal/curation.md`](.steal/curation.md) — it works in any repository, agent or no
agent, with nothing to install.
