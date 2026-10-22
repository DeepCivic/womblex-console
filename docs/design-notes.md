# Design notes — approaches and limits

Recorded so they are not rediscovered. These moved here from Womblex's `docs/decisions-dead-ends.md` when the console left it. `ui/src/app.css` is the stylesheet; `DESIGN.md` is the design system.

- **Console base tokens are a best-effort fill, not a verified match
  (`ui/src/app.css`, merge 4).** `DESIGN.md` states the console-specific
  tokens explicitly (surfaces, status fills, `--font-mono`, both themes) but
  names several base tokens — `--background`/`--foreground`/`--border` in
  light mode, `--muted-foreground` in light mode, `--ring` — as
  DeepCivic-inherited without restating their hex; that table lives in
  DeepCivic's own `DESIGN.md`, in a separate repository this one has no
  access to. The values shipped satisfy what `DESIGN.md` *does* state (the
  measured-contrast table's dark-mode figures, lime/purple never doubling as
  page background or body text, `#18182a` as the pill near-black) but are
  not verified against DeepCivic's actual values. Reconcile once that
  repository is reachable from a session here.
- **`DESIGN.md`'s light theme is underspecified, and two of its rules do not
  hold there.** The system is dark-first, and its stated rules were checked
  against the dark page; measured against the light one they break. Recorded
  because merge 5's `StatusPill` is the first component that would inherit
  the contradiction. All figures below are WCAG 2.1 ratios computed from the
  tokens `DESIGN.md` itself lists.
  - **The status-pill rule holds only in dark mode.** "A status pill or dot
    is always a solid `--status-*` fill with near-black `#18182a` text …
    identical in light and dark mode and needs no per-theme override." Over
    the *dark* fills that is exact — 4.64:1 (failed) to 13.18:1 (running),
    matching the doc's stated "4.6:1 through 13.1:1". Over the *light* fills
    the same near-black gives pending 1.47:1, warning 3.48:1, done 3.48:1,
    failed 3.53:1 — only running passes. Those light values are tuned for
    **white** text (4.94:1 to 11.88:1), so the pill does need a per-theme
    text colour, contrary to the rule. *Resolved 2026-10:* the text colour
    flips per theme (white on the light fills, near-black on the dark ones),
    with lime running near-black in both; `DESIGN.md` states the revised rule.
  - **Lime cannot be an active-nav *text* colour in light mode.** "Active
    item takes a lime left rule + lime icon" works on the dark nav
    (`#c8ef35` on `#22222e` = 11.86:1) but not the light one, where
    `--surface-raised` is `#ffffff` and the same lime computes to 1.32:1.
    The shell therefore uses lime for the 2px rule (a fill, always legible)
    and carries the active state in the label's weight and `--foreground`
    (13.72:1 dark / 17.46:1 light).
