# Womblex console — Requirements

What the console must do, as user stories with testable acceptance criteria. These were Requirements 15 to 21 of Womblex's `docs/functional_requirements.md` and keep their numbers here; Womblex's document now points at this one. Every `womblex.*` name below belongs to the pinned Womblex release.

## 15. Web Console Shell, Navigation, and Deployment Modes

**As** a developer or administrator,
**I want** an optional admin and debugging console that reads the artefacts the pipeline already writes,
**so that** I can inspect and debug every run domain in one place without a separate tool or a live pipeline connection.

**Given** a console bound to a single run source (a local output root or an object-store URI)
**When** the operator launches the console and opens it in a browser
**Then** a persistent shell routes between the five console domains and serves the read API even when no frontend build is present.

**Acceptance criteria:**

- The console is an admin and debugging utility, not an integration surface: other software submits and reads work through the authenticated, owner-scoped `womblex serve` `/v1` API or reads the on-disk data contract. The console has no authentication and binds to loopback unless told otherwise.
- The console binds to exactly one run source at construction (local output root or store URI) so no endpoint can be steered to read an unmounted directory.
- A persistent top bar (global search, run selector, execution controls) and a side-nav rail route between the Dashboard, Corpus Inspector, Semantic Chunk Inspector, Pipeline Composer, and Resources Console.
- The console is a reader over persisted artefacts and never edits a stage output; its only writable surfaces are dispatch and preset saving.
- Dispatch requires a store, an ingest location, and a workflow system database to be configured; a console missing any of these still serves the full inspection surface (it simply cannot enqueue work).
- A bare install with no SvelteKit build still serves the read API; the SPA is mounted only when a build exists alongside it.

## 16. Dashboard — Queue and Stage Progress

**As** an administrator,
**I want** a run-scoped dashboard of queue state and per-stage progress,
**so that** I can monitor throughput and spot stalled jobs without touching the queue.

**Given** a selected run, with an optional job queue and the run's per-stage checkpoints
**When** the operator opens the Dashboard
**Then** it shows the run's status sentence, queue counts and per-stage completion, polling while the tab is visible.

**Acceptance criteria:**

- Queue and stage state come from what the pipeline already writes (the job queue and per-stage checkpoints); with no queue, the dashboard falls back to checkpoints.
- A run's status is one sentence built from exact per-stage counts of done, pending and failed work, shown beside the counts. The CLI (`womblex jobs --run-id`), the API and the dashboard show the same sentence.
- The sentence uses the API's status words (`pending` / `running` / `done` / `failed` / `cancelled`), plus a warning when a scheduled firing could not dispatch its stages.
- Job status is rendered with the exact values the system writes (`pending` / `running` / `done` / `failed` / `cancelled`), plus `stale` for a `running` job with no update past `stale_after_seconds` (default 900), and `skipped` for a stage whose every unit was already published for the same work (Requirement 2). A run with a skipped stage reads finished.
- A retried stage counts once: counts take its latest stage attempt, and the superseded attempt stays listed `failed`, its `retried_by` field holding the next attempt's id.
- The run record's lineage event (`womblex manifest --lineage` with `--dsn`) reports the run's real outcome (`COMPLETE`, `FAIL` or `ABORT`), not always complete; without a queue to ask, its status is `unknown`.
- The dashboard only *names* a stalled job; DBOS recovers it when its executor restarts, and the dashboard never requeues, cancels, or claims work itself.
- Polling is paused while the browser tab is hidden so a backgrounded console stops hitting the queue.
- Per-stage progress renders in the declared pipeline order rather than an ad-hoc frontend ordering.
- Batch and stage logs for the run are listed newest-first and are individually viewable.

## 17. Corpus Inspector — Document Grid and Integrity Audit

**As** a developer or administrator,
**I want** a dense, virtualised document grid with checkpoint and shard-integrity views,
**so that** I can inspect thousands of documents and confirm a run's outputs are complete and readable when debugging it.

**Given** a selected run's manifest and shard directories
**When** the operator opens the Corpus Inspector
**Then** each document appears as a row with its status, a stage-checkpoint switcher, and an on-demand shard-integrity audit.

**Acceptance criteria:**

- The grid uses real table semantics with a sticky header, row virtualisation, and an announced total row count for accessibility.
- Document status is conveyed by a status pill (icon plus label), never by row background tint alone.
- A checkpoint switcher reports which stages are present for the run, in the declared pipeline order.
- A verify-shards action runs the persistence audit, confirming required shard files exist, are readable, and match expected document counts.
- The grid supports a failed-only filter and a user-selectable density (comfortable / default / compact) persisted locally.

**TO-DO:**

- **Row virtualisation and the announced total row count are not implemented (re: "row virtualisation, and an announced total row count").** `DocumentGrid.svelte` renders a real `<table>` with a `<caption>`, `<th scope="col">` header, and a sticky header, but puts *every* row in the DOM rather than virtualising a window over them — an explicit code comment records that `aria-rowcount`/`aria-rowindex` are omitted because "every row is in the DOM here, so the browser's own count is correct … They become necessary when virtualisation lands." As built, the grid will not stay dense over thousands of rows (the story's own motivation), and there is no `aria-rowcount` announcing a total beyond the rendered window. Decide whether to (a) add windowed row virtualisation and the `aria-rowcount`/`aria-rowindex` announcement it requires, or (b) drop "virtualised" from the story and "row virtualisation, and an announced total row count" from this criterion until it is implemented. Resolve alongside the matching Requirement 21 TO-DO, which restates the same gap as an accessibility rule.

## 18. Semantic Chunk Inspector — Chunk, Entity, PII, and Money Overlays

**As** a developer,
**I want** to read a document's chunks with entity, PII, and money overlays rendered inline,
**so that** I can debug chunking quality and confirm sensitive spans are masked correctly.

**Given** a document chosen from the run's manifest
**When** the operator opens the Semantic Chunk Inspector for that document
**Then** its chunks and sidecar overlays are read per-`source_hash` and rendered as one card each.

**Acceptance criteria:**

- Chunk detail is read keyed on a single `source_hash`, pushing the predicate into the Parquet read so per-document inspection stays cheap over a corpus-wide sidecar.
- Each chunk card shows chunk index, token count, character range, and content type in a monospace, sunken well.
- Entity mentions are underlined with a hover tooltip, and PII masks (e.g., `<PERSON_n>`) are rendered as inline pills.
- Money spans surfaced by the money-annotation sidecar are rendered inline alongside entity and PII overlays.
- Overlays are read-only projections of the sidecars and never rewrite the base extracted text.

## 19. Pipeline Composer — Configuration, Validation, and Dispatch

**Paid:** Dispatching a composed pipeline launches its enabled paid stages.

**As** a developer or administrator,
**I want** to compose and validate a pipeline configuration visually and dispatch an admin run from it,
**so that** I can author correct configs and enqueue work without hand-editing YAML or re-implementing guardrails.

**Given** the served stage graph and the `WomblexConfig` JSON Schema
**When** the operator edits the config form and presses to enqueue or run downstream stages
**Then** the config is validated and dispatched through the same code paths the CLI uses, writing queue rows byte-identical to the documented commands.

**Acceptance criteria:**

- The stage graph is rendered from the served `STAGE_CONTRACTS` (nodes wired by their required-input edges); disabled stages drop to reduced opacity while keeping their edges so a broken chain reads as a gap.
- The form is rendered from `WomblexConfig`'s JSON Schema, and validation plus YAML download go through the same `WomblexConfig` construction the CLI's config loader uses — the console cannot accept a config the CLI would reject.
- Named presets are offered as starting points; operator-authored presets can be saved when a presets directory is configured, and preset saving refuses cleanly when it is not.
- Enqueuing an extraction run and dispatching downstream stages call the same enabled-stage gate and queue-enqueue paths as the equivalent CLI commands, and dispatch is idempotent per `(run_id, stage)`.
- Which downstream stages run is decided server-side (never re-derived in the frontend); the result panel reports what was dispatched in claim order, and irreversible or run-scoped stages (PII, quality) remain undispatchable.
- Runs dispatched from the console carry no owner, so through the service API they are visible to `admin` callers only.

## 20. Resources Console — Connections

**As** an administrator,
**I want** connection cards for the store, ingest, queue, and enrichment service with reachability tests,
**so that** I can confirm a deployment is wired correctly without exposing secrets.

**Given** the deployment's configured store, ingest, queue, and Isaacus connections
**When** the operator opens the Resources Console
**Then** each connection is shown as a credential-masked card with a live "Test" action.

**Acceptance criteria:**

- Four connection cards (store, ingest, queue, Isaacus) render deployment configuration, not any single run's artefacts.
- Connection strings are shown with secrets masked (never rendered in full in the DOM or a copy buffer), and each card offers a live reachability test.
- The store and ingest locations are deploy-time configuration (flags / env) and are shown read-only, as are the queue and Isaacus cards; an empty worker fleet is a normal resting state rather than an error.

## 21. Console Design System and Accessibility

**As** a developer or administrator,
**I want** the console to default to a dense, dark, state-legible design that runs with no network access and meets accessibility standards,
**so that** I can read large grids and chunk text reliably in both themes and at every density.

**Given** the console rendered in a browser, possibly air-gapped
**When** the operator uses it across themes, densities, and input methods
**Then** colour carries state (not decoration), assets are self-hosted, and every interactive element is keyboard-reachable with visible focus.

**Acceptance criteria:**

- The console defaults to a dark theme with a supported light theme, using semantic design tokens only (never hardcoded colour values).
- Colour communicates pipeline/queue state through a measured status palette, and status is never encoded by colour alone — every status carries an icon and a text label.
- Fonts and icons are self-hosted in the UI bundle with no runtime network requests, consistent with the pipeline's local-first model.
- Grids are real tables with `<th scope>` and `<caption>`, and virtualised rows announce total counts to assistive technology.
- The keyboard reaches everything the mouse does (grid arrow-key navigation, `/` to focus search, `Esc` to close drawers) with a visible focus indicator, and interactive controls keep a ≥ 44×44px hit area even at 32px density.

**TO-DO:**

- **Virtualised rows do not announce total counts (re: "virtualised rows announce total counts to assistive technology").** The `<table>`/`<th scope>`/`<caption>` half of this criterion holds (`DocumentGrid.svelte`), but the grid is not virtualised and emits no `aria-rowcount`, so there is no announced total beyond the rendered rows. This is the same gap as the Requirement 17 TO-DO, stated here as its accessibility consequence: until windowed virtualisation lands with `aria-rowcount`/`aria-rowindex`, assistive technology hears only the DOM row count. Resolve together — either implement virtualisation with the row-count announcement, or drop the "virtualised rows announce total counts" clause from both requirements.
