# Social preview

`runwai-social-preview.png` — 1280×640, the image GitHub shows when a link to this
repository is unfurled in Slack, on X, or in a chat window.

**This is runwAI's own branding, which is why it lives under `.runwai/`.** A project built
from this template is not called runwAI and does not want this card; the directory goes
when `.runwai/` goes, and takes six npm packages out of the adopter's bill of materials
with it. If you want a card of your own, this is a working example to copy, not a file to
edit in place.

## Uploading it is a setting at GitHub, not a file

Committing the PNG does nothing on its own. Nothing in a repository can set its own social
preview, and a template that claims otherwise is lying to you:

**Settings → General → Social preview → Edit → Upload an image**, and pick
`runwai-social-preview.png`.

GitHub's limits are 1 MB and a recommended 1280×640; this file is ~61 KB.

## Regenerating it

```bash
cd .runwai/social-preview
npm install
npx playwright install chromium
npm run render
```

If you are somewhere that already ships a Chromium and cannot download another — a sandbox,
a locked-down CI image — skip the `playwright install` and point at the one you have:

```bash
CHROMIUM_PATH=/path/to/chromium npm run render
```

That stages the two brand faces out of `node_modules`, renders `social-preview.html` in
headless Chromium at exactly 1280×640, and overwrites the PNG. Same input, same bytes out —
the versions in `package.json` are pinned for that reason.

The fonts are Google Fonts under the SIL Open Font License, pulled from pinned
[Fontsource](https://fontsource.org) packages rather than vendored as binaries here. They
land in `fonts/`, which is ignored.

## Where the design comes from

The card is the DeepCivic design system, so runwAI unfurls looking like the rest of the
work it belongs to. The tokens in `social-preview.html` are copied from that system's
`:root` set — the same values the bushfire replay app uses in its `deepcivic-theme.css`:

| Token | Value | Used for |
| :--- | :--- | :--- |
| `--background` | `#c8ef35` | The signature lime page |
| `--foreground` | `#18182a` | Navy ink — wordmark, borders, the filled chip |
| `--card` | `#1a1a24` | The dark card, on lime — the house bento pattern |
| `--accent` | `#7b6ff0` | Purple: the wordmark's offset shadow, and one report row |
| `--accent-secondary` | `#e05548` | Coral, sparingly — the eyebrow pip, one report row |
| `--font-display` | Barlow Condensed 900 | Wordmark and eyebrow |
| `--font-sans` | Inclusive Sans | Everything else |

Two deliberate departures from the house wordmark treatment:

- **The name keeps its own casing.** DeepCivic sets wordmarks in uppercase; `runwAI`
  uppercased is `RUNWAI`, which throws away the capitalised *AI* that the name is built on.
- **The letterspacing is opened to `0.025em`** and the offset shadow scaled to 6px. At
  152px the condensed 900 lowercase closes up into a wall of vertical strokes otherwise.

The right-hand card is the four rows of `security-report.md`, because that report is the
artefact this repository exists to produce — and it carries the caveat that goes with it
rather than implying a clean bill of health.

Everything that matters sits inside a 40pt safe border, per GitHub's template, so nothing
is lost when a client crops the card.

## Editing it

`social-preview.html` is the source; the PNG is a build output. Change the HTML, re-render,
and commit both. Line breaks in the tagline are explicit `<br />` — the canvas is a fixed
size, so the rag is composed rather than left to the text wrapper.
