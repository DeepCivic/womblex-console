#!/usr/bin/env python3
"""runwAI self-check: validates the control registry.

This is runwAI enforcing its own core invariant on itself. It is deliberately
deterministic: no network, no LLM, no clock-dependent behaviour. Same tree in,
same verdict out, same exit code.

Exit codes:
    0  all checks passed (warnings may still be printed)
    1  one or more checks failed
    2  the validator could not run (missing dependency or unreadable input)

Usage:
    python3 .runwai/tools/validate_registry.py [--repo-root PATH] [--strict]

--strict additionally fails on warnings, which is what CI uses once the pending
verification work in .runwai/docs/pinning.md and docs/ism-verification.md is complete.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("FATAL: PyYAML is required. pip install pyyaml==6.0.3", file=sys.stderr)
    raise SystemExit(2)

# A tool class that adjudicates by asking a model is never acceptable as
# enforcement. Listed explicitly so the prohibition is greppable rather than
# implied by the schema's enum.
FORBIDDEN_TOOL_CLASSES = {
    "llm-judge",
    "llm-review",
    "ai-review",
    "model-adjudication",
    "human-attestation",
}

# Anything that is not an exact version. An unpinned scanner is a
# non-deterministic control: its ruleset can change under you.
FLOATING_VERSION = re.compile(r"(latest|^\*$|^[\^~>=<]|\.x$|^v?\d+$|^v?\d+\.\d+$)", re.I)

SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
CONTROL_ID = re.compile(r"^RWA-[0-9]{4}$")
ISM_ID = re.compile(r"^ISM-[0-9]{4}$")

# What schemas/control.schema.json used to assert. Kept as data rather than a JSON Schema
# because there is one document to check and a schema directory was two files of machinery
# guarding two files of content.
REQUIRED_FIELDS = ("id", "ism_ids", "title", "domain", "mechanism", "enforcement",
                   "blocking", "tools", "verification_status")
ENUMS = {
    "mechanism": {"pre-commit", "posture"},
    "enforcement": {"deterministic", "probabilistic"},
    "mapping_fidelity": {"direct", "partial", "supporting"},
    "verification_status": {"verified", "unverified", "disproved"},
}

# Only two places exist, and both are in the tree. A mechanism naming somewhere else is a
# claim about machinery this repository does not carry, which is the error this validator
# exists to catch: `pr-gate` and `release-gate` were both accepted here long after the
# workflows behind them stopped being something runwAI installs.
MECHANISMS = {"pre-commit", "posture"}

# `posture` reports and blocks nothing, by design and not by accident. Listed explicitly so
# the prohibition is greppable rather than implied, in the same spirit as
# FORBIDDEN_TOOL_CLASSES above.
NON_BLOCKING_MECHANISMS = {"posture"}


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, where: str, msg: str) -> None:
        self.errors.append(f"{where}: {msg}")

    def warn(self, where: str, msg: str) -> None:
        self.warnings.append(f"{where}: {msg}")


def load_yaml(path: Path, report: Report) -> dict | None:
    try:
        with path.open(encoding="utf-8") as fh:
            return yaml.safe_load(fh)
    except FileNotFoundError:
        report.error(str(path), "file not found")
    except yaml.YAMLError as exc:
        report.error(str(path), f"invalid YAML: {exc}")
    return None


def check_tool(tool: dict, where: str, report: Report) -> None:
    name = tool.get("name", "<unnamed>")
    cls = tool.get("class", "")
    install = tool.get("install", "")
    version = tool.get("version")

    # INVARIANT: no model may adjudicate a control.
    if cls in FORBIDDEN_TOOL_CLASSES:
        report.error(
            where,
            f"tool '{name}' declares forbidden enforcement class '{cls}'. "
            "An LLM or a human attestation may advise, but may never be a control's "
            "enforcement mechanism.",
        )

    if install == "unavailable":
        if version:
            report.error(
                where,
                f"tool '{name}' is marked install: unavailable but carries a version. "
                "Either pin it properly or drop the version.",
            )
        else:
            report.warn(
                where,
                f"tool '{name}' is not pinned (install: unavailable), so any control "
                "relying on it is not yet reproducible. See .runwai/docs/pinning.md.",
            )
        return

    if not version:
        report.error(where, f"tool '{name}' has no version and is not marked unavailable")
        return

    if FLOATING_VERSION.search(version):
        report.error(
            where,
            f"tool '{name}' version '{version}' is a floating specifier. "
            "Exact pins only: a mutable ruleset makes the control non-deterministic.",
        )

    if not tool.get("verified_version", False):
        report.warn(
            where,
            f"tool '{name}' version '{version}' has not been confirmed to exist in "
            f"its {install} registry",
        )


def check_structure(ctl: dict, where: str, report: Report) -> None:
    """The field-level rules control.schema.json used to carry."""
    for field in REQUIRED_FIELDS:
        if field not in ctl:
            report.error(where, f"missing required field '{field}'")
    if not CONTROL_ID.match(str(ctl.get("id", ""))):
        report.error(where, f"id '{ctl.get('id')}' is not RWA-NNNN")
    ism_ids = ctl.get("ism_ids") or []
    if not ism_ids:
        report.error(where, "claims no ISM IDs")
    for ism in ism_ids:
        if not ISM_ID.match(str(ism)):
            report.error(where, f"'{ism}' is not an ISM-NNNN identifier")
    for field, allowed in ENUMS.items():
        value = ctl.get(field)
        if value is not None and value not in allowed:
            report.error(where, f"{field} '{value}' is not one of {sorted(allowed)}")
    if not isinstance(ctl.get("tools"), list) or not ctl.get("tools"):
        report.error(where, "has no tools; a control with no mechanism named is not a control")


def check_implementation(ctl: dict, root: Path, where: str, report: Report) -> bool:
    """A control either has a live mechanism here or it does not. Returns True if it does.

    Absent is a legitimate state and the security report renders it as "mapped, nothing
    runs". What is not legitimate is claiming one that is not there: a mechanism that does
    not exist, or a file the repository does not contain, would put a control in the
    report's "has a check behind it" row on no evidence.
    """
    impl = ctl.get("implementation")
    if impl is None:
        return False
    if impl.get("gate") not in MECHANISMS:
        report.error(
            where,
            f"implementation names '{impl.get('gate')}', which is not one of "
            f"{sorted(MECHANISMS)}. Those are the only two places a check runs in this "
            "repository.",
        )
    for rel in impl.get("files", []) or []:
        if not (root / rel).is_file():
            report.error(where, f"implementation names '{rel}', which is not in the tree")
    prov = impl.get("provenance") or {}
    origin = prov.get("origin")
    if origin not in {"original", "vendored", "derived"}:
        report.error(where, f"implementation provenance origin '{origin}' is not recognised")
    # INVARIANT: vendored content carries its upstream licence, or it does not ship.
    if origin in {"vendored", "derived"}:
        upstream = prov.get("upstream") or {}
        if not upstream.get("license"):
            report.error(where, "vendored implementation records no upstream licence")
        if not SHA1_RE.match(str(upstream.get("commit", ""))):
            report.error(where, "vendored implementation has no full 40-character upstream SHA; "
                                "a branch or tag is not a pin")
    return True


def check_control(ctl: dict, root: Path, report: Report) -> bool:
    cid = ctl.get("id", "<no id>")
    where = f"controls/registry.yaml[{cid}]"
    check_structure(ctl, where, report)

    enforcement = ctl.get("enforcement")
    blocking = ctl.get("blocking")
    assertion = ctl.get("deterministic_assertion")

    # INVARIANT: nothing routed to a reporting mechanism may claim it blocks. This is the
    # cheapest lie the registry could tell — one word, no code change — and it is the exact
    # shape of the claim the whole repository is built to refuse.
    if ctl.get("mechanism") in NON_BLOCKING_MECHANISMS and blocking:
        report.error(
            where,
            f"mechanism '{ctl.get('mechanism')}' reports and blocks nothing, so this "
            "control cannot declare blocking: true. Nothing in this repository prevents a "
            "merge; that is branch protection, which a template cannot install.",
        )

    # INVARIANT: a probabilistic control may not block unless a reproducible
    # assertion has been written that makes its verdict stable.
    if enforcement == "probabilistic" and blocking and not assertion:
        report.error(
            where,
            "probabilistic enforcement cannot be blocking without a "
            "deterministic_assertion. A stochastic target means a green run does not "
            "predict the next run, so the gate would be flaky and its verdict "
            "meaningless.",
        )

    if enforcement == "deterministic" and assertion:
        report.warn(
            where,
            "deterministic control carries a deterministic_assertion, which is "
            "redundant and suggests the enforcement class is mislabelled",
        )

    for tool in ctl.get("tools", []):
        check_tool(tool, where, report)

    implemented = check_implementation(ctl, root, where, report)

    # INVARIANT: 'verified' is a claim that requires a receipt.
    if ctl.get("verification_status") == "verified":
        if not ctl.get("verification_source"):
            report.error(where, "claims verification_status: verified with no verification_source")
        if not ctl.get("verified_on"):
            report.error(where, "claims verification_status: verified with no verified_on date")
    else:
        report.warn(where, f"ISM IDs {ctl.get('ism_ids')} are unverified")

    return implemented


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", type=Path)
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    args = parser.parse_args()

    root = args.repo_root.resolve()
    report = Report()

    registry_path = root / "controls" / "registry.yaml"
    registry = load_yaml(registry_path, report)

    control_count = 0
    implemented = 0
    if registry is not None:
        where = str(registry_path.relative_to(root))
        controls = registry.get("controls", []) or []
        control_count = len(controls)
        if not controls:
            report.error(where, "declares no controls")

        ids = [c.get("id") for c in controls]
        for dup in sorted({i for i in ids if ids.count(i) > 1}):
            report.error(where, f"duplicate control id '{dup}'")

        for ctl in controls:
            if check_control(ctl, root, report):
                implemented += 1

        release = registry.get("ism_release", {})
        if release.get("verification_status") == "verified" and not release.get(
            "verification_source"
        ):
            report.error(where, "ism_release claims verified with no verification_source")

    # ---- output -------------------------------------------------------------
    for w in report.warnings:
        print(f"WARN  {w}")
    for e in report.errors:
        print(f"ERROR {e}")

    print(
        f"\nrunwai-selfcheck: {control_count} controls, {implemented} with a mechanism, "
        f"{len(report.errors)} errors, {len(report.warnings)} warnings"
    )

    if report.errors:
        print("FAILED")
        return 1
    if args.strict and report.warnings:
        print("FAILED (strict: warnings are errors)")
        return 1
    print("PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
