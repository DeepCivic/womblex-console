"""Deployment files: the image, the compose service and the frontend CI job."""
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from womblex_console.cli import build_parser

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCKERFILE = (REPO_ROOT / "Dockerfile").read_text()


def _ui_service() -> dict:
    return yaml.safe_load((REPO_ROOT / "docker-compose.yml").read_text())["services"]["ui"]


class TestImage:
    """The container is only correct if it agrees with the CLI and the app.

    Nothing else in the suite reads the deployment files, so a renamed flag or
    a second run source would otherwise surface as a container that exits 1 in
    someone's compose stack.
    """

    def test_entrypoint_parses_against_the_real_cli(self) -> None:
        match = re.search(r"^ENTRYPOINT (\[.*\])$", DOCKERFILE, re.MULTILINE)
        assert match, "Dockerfile has no JSON-form ENTRYPOINT"
        entrypoint = json.loads(match.group(1))
        assert entrypoint[0] == "womblex-console"

        args = build_parser().parse_args(entrypoint[1:])  # SystemExit if a flag is gone
        # Loopback is the CLI default, and inside a container it would refuse
        # every request arriving via the published port.
        assert args.host == "0.0.0.0"
        assert args.port == 8080

    def test_entry_point_is_declared(self) -> None:
        pyproject = (REPO_ROOT / "pyproject.toml").read_text()
        assert 'womblex-console = "womblex_console.cli:main"' in pyproject

    def test_frontend_builder_stage_runs_a_real_package_script(self) -> None:
        match = re.search(r"^RUN npm run (\S+)$", DOCKERFILE, re.MULTILINE)
        assert match, "Dockerfile has no `npm run <script>` build step"
        scripts = json.loads((REPO_ROOT / "ui" / "package.json").read_text())["scripts"]
        assert match.group(1) in scripts

    def test_final_stage_copies_the_builder_stages_declared_output(self) -> None:
        """`vite.config.ts`'s adapter output dir must match what the Dockerfile COPYs out."""
        vite_config = (REPO_ROOT / "ui" / "vite.config.ts").read_text()
        assert "pages: 'build'" in vite_config
        assert "COPY --from=frontend-builder /app/ui/build /app/ui/build" in DOCKERFILE


class TestCompose:
    def test_ui_service_is_read_only_with_tmpfs(self) -> None:
        ui = _ui_service()
        assert "womblex-console" in ui["image"]
        assert ui["read_only"] is True
        # A store-backed read stages the manifest through a temp dir.
        assert "/tmp" in ui["tmpfs"]

    def test_ui_service_resolves_exactly_one_run_source(self) -> None:
        """Two sources make resolve_settings raise, so the container would exit 1."""
        env = _ui_service()["environment"]
        assert "WOMBLEX_STORE_URI" in env
        assert "WOMBLEX_UI_OUTPUT_ROOT" not in env

    def test_ui_service_advertises_the_queue_and_ingest_it_reads(self) -> None:
        env = _ui_service()["environment"]
        assert "WOMBLEX_DB_DSN" in env and "WOMBLEX_INGEST_URI" in env

    def test_store_credentials_are_store_specific_and_ambient_ones_default_empty(self) -> None:
        """Setting AWS_ACCESS_KEY_ID is process-global and would clobber an
        instance role, so it passes through only when the operator sets it."""
        env = _ui_service()["environment"]
        assert env["WOMBLEX_S3_ACCESS_KEY_ID"] == "${WOMBLEX_S3_ACCESS_KEY_ID:-}"
        assert env["AWS_ACCESS_KEY_ID"] == "${AWS_ACCESS_KEY_ID:-}"
        assert env["AWS_SECRET_ACCESS_KEY"] == "${AWS_SECRET_ACCESS_KEY:-}"

    def test_no_bundled_backends(self) -> None:
        """The console points at an existing deployment; it starts none of its own."""
        services = yaml.safe_load((REPO_ROOT / "docker-compose.yml").read_text())["services"]
        assert set(services) == {"ui"}


class TestFrontendCi:
    """The frontend CI job must call scripts that still exist — otherwise a
    rename silently stops linting or building the SPA.
    """

    def test_frontend_job_runs_declared_package_scripts(self) -> None:
        workflow = yaml.safe_load((REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text())
        frontend = workflow["jobs"]["frontend"]
        scripts = json.loads((REPO_ROOT / "ui" / "package.json").read_text())["scripts"]
        run_steps = [
            step["run"] for step in frontend["steps"]
            if step.get("working-directory") == "ui" and "run" in step
        ]
        assert run_steps, "no step in the frontend job runs anything in ui/"
        for run in run_steps:
            match = re.match(r"npm (run )?(\S+)$", run.strip())
            assert match, f"unrecognised frontend CI step: {run!r}"
            script = match.group(2)
            if script not in ("ci", "audit"):  # not package.json scripts
                assert script in scripts, f"ui/package.json has no {script!r} script"
