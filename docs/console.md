# Womblex console

An operator and debugging utility for [Womblex](https://github.com/DeepCivic/womblex). It serves a read API and a SvelteKit single-page app over the artefacts a Womblex run writes, and lets an operator act on the deployment: the Pipeline Composer builds a config and dispatches runs into the job queue, and presets are filed into the store. Integrations use `womblex serve`, not this.

The console started life inside Womblex (`womblex ui`) and was split out so Womblex stops shipping it. It was seeded from that history, so `git log` on `src/womblex_console/` and `ui/` runs back through it.

## Documents

- [requirements.md](requirements.md): what the console must do (Requirements 15 to 21, kept from Womblex's numbering).
- [../DESIGN.md](../DESIGN.md) and [design-notes.md](design-notes.md): the design system, and the approaches that did not hold.

## Relationship to Womblex

Dependency runs one way. The console depends on a pinned Womblex release; Womblex never imports, tests or documents the console. When Womblex changes, this repository moves its pin and its imports.

The pin is in `pyproject.toml` (`womblex==…`) and `[tool.uv.sources]`, which names the Womblex commit until that release is on PyPI. To move it: edit both, run `uv lock`, and fix whatever the type check and tests then report.

Deprecating the console is archiving this repository. Nothing in Womblex changes.

## Running it

Install, then point it at exactly one run source:

```bash
uv sync --extra dev
uv run womblex-console --output-root output/          # a local run root
uv run womblex-console --store s3://womblex --dsn postgresql://…
```

The flags and their environment fallbacks:

| Flag | Environment | Meaning |
| :--- | :--- | :--- |
| `--output-root` | `WOMBLEX_UI_OUTPUT_ROOT` | Local run root: the parent of `run-*/` directories |
| `--store` | `WOMBLEX_STORE_URI` | Object-store base URI containing `runs/` |
| `--dsn` | `WOMBLEX_DB_DSN`, `DATABASE_URL` | Job queue the Dashboard reads; optional |
| `--presets-dir` | `WOMBLEX_UI_PRESETS_DIR` | Where the Composer saves presets locally; without one, saving is off |
| `--ingest` | `WOMBLEX_INGEST_URI` | Where source documents arrive; without one the Execution Controls cannot dispatch |
| `--host`, `--port` | | Bind address (default `127.0.0.1:8080`) |

The console has no authentication by design. It binds to loopback by default; exposing it is a choice the operator makes alongside whatever fronts it.

For frontend work, run `npm run dev` in `ui/` against a running `womblex-console`.

## Container image

`Dockerfile` builds the SPA and installs the locked Python set. `docker-compose.yml` runs it against an existing Womblex store and queue; it starts no Postgres or MinIO of its own:

```bash
WOMBLEX_STORE_URI=s3://womblex WOMBLEX_DB_DSN=postgresql://… docker compose up
```

Tagging `v*` publishes `ghcr.io/deepcivic/womblex-console` (`.github/workflows/publish-image.yml`).

## Checks

```bash
uv run ruff check src/ tests/
uv run mypy src/
uv run python -m pytest tests/
(cd ui && npm run lint && npm run check && npm run build)
```
