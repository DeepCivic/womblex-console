#!/usr/bin/env python3
"""Generate docs/security-report.md: where this repository stands against the ISM.

This is the artefact runwAI exists to produce. It answers "how does what I have built
compare to the ISM?" for someone who has never read the ISM and will not start now.

WHY IT LIVES HERE AND NOT IN .runwai/tools/

Decision 3 put runwAI's own self-checks in .runwai/tools/, because the template is not a
Python project and should not read as one. This is not one of those. The self-checks
validate runwAI's structure and an adopter loses nothing by deleting them; this generator
produces the thing an adopter adopted runwAI *for*. Putting it in .runwai/ would mean the
setup agent, following AGENTS.md, prunes the feature along with the record. It is CI
machinery, so it lives with the CI.

WHAT IT WILL NOT DO

  * Claim compliance. It reports which checks ran and what they found. Passing every check
    here means the code did not trip a set of automated tests, and nothing more.
  * Report a control as satisfied on no evidence. A control with nothing behind it renders
    as unassessed, never as implemented by default and never by omission.
  * Treat "not organisational" as "reachable". A control whose evidence lives in deployed
    infrastructure nobody declares in this repository is out of reach even though its
    surface is not organisational. That distinction is drawn explicitly below, because
    collapsing it is the most flattering lie this document could tell.
  * Fail the build. It exits 0 on any input it can read.

Usage:
    python3 .github/scripts/security_report.py [--repo-root PATH] [--findings FILE ...]
                                               [--audit FILE] [--scan-scope TEXT]
                                               [--out PATH]

Exit codes:
    0  written (the normal case, including when scanners produced nothing)
    2  could not run — a required input is missing or unreadable
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("FATAL: PyYAML is required. pip install pyyaml==6.0.3", file=sys.stderr)
    raise SystemExit(2)

# Findings shown in full. Beyond this the report counts them and stops listing: a document
# that opens with four hundred findings is one nobody opens twice, which is the failure
# TODO-8 exists to measure.
FINDING_CAP = 25

SEVERITY_ORDER = {"ERROR": 0, "WARNING": 1, "INFO": 2}


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_findings(paths: list[Path]) -> tuple[list[dict], list[str]]:
    """Read semgrep --json output. Returns (findings, notes about what could not be read).

    Advisory scanning throws away the exit code, so an unreadable findings file is
    indistinguishable from a clean scan unless it is reported. Every failure to read is
    carried into the report rather than swallowed.
    """
    findings: list[dict] = []
    notes: list[str] = []
    for path in paths:
        if not path.is_file():
            notes.append(f"`{path}` was not produced, so its findings are missing here.")
            continue
        try:
            data = load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            notes.append(f"`{path}` could not be read ({type(exc).__name__}); treat this "
                         "report as incomplete rather than clean.")
            continue
        for result in data.get("results", []):
            extra = result.get("extra", {})
            findings.append({
                "rule": result.get("check_id", "(unnamed rule)"),
                "path": result.get("path", "(unknown file)"),
                "line": (result.get("start") or {}).get("line", 0),
                "severity": str(extra.get("severity", "INFO")).upper(),
                "message": " ".join(str(extra.get("message", "")).split()),
            })
    findings.sort(key=lambda f: (
        SEVERITY_ORDER.get(f["severity"], 9), f["path"], f["line"], f["rule"]
    ))
    return findings, notes


def read_audit(path: Path | None) -> tuple[dict | None, list[str]]:
    """Read audit.py's result JSON. Returns (audit, notes about what could not be read).

    A missing file is a plain statement rather than a warning, and that asymmetry with
    `--findings` is deliberate. CI always produces semgrep output, so its absence means
    something broke. The dependency audit needs a database that is downloaded separately,
    so "it did not run" is an ordinary state a local run reaches honestly.
    """
    if path is None:
        return None, []
    if not path.is_file():
        return None, []
    try:
        return load_json(path), []
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"`{path}` could not be read ({type(exc).__name__}); the dependency "
                      "section below is missing rather than clean."]


def classify(root: Path) -> tuple[dict, dict]:
    """Bucket every ISM control by how much this repository can say about it."""
    index = load_json(root / "controls" / "ism-index.json")["controls"]
    registry = load_yaml(root / "controls" / "registry.yaml")

    # A control has a mechanism here when it carries an `implementation` block naming where
    # it runs. Nothing else counts: the block is what validate_registry.py checks the files
    # of, so a control cannot reach the "has a check behind it" row on an unverified claim.
    enforced: dict[str, list[str]] = {}
    mapped: dict[str, list[str]] = {}
    via_gate: dict[str, set[str]] = {}
    for ctl in registry.get("controls", []):
        impl = ctl.get("implementation") or {}
        live = bool(impl.get("gate"))
        target = enforced if live else mapped
        for ism_id in ctl.get("ism_ids", []):
            if ism_id in index:
                target.setdefault(ism_id, []).append(ctl["id"])
                if live:
                    via_gate.setdefault(ism_id, set()).add(impl["gate"])

    # enforced wins where a control is claimed twice.
    mapped = {k: v for k, v in mapped.items() if k not in enforced}

    buckets = {"enforced": [], "mapped": [], "unassessed": [], "out_of_scope": []}
    for ism_id, record in sorted(index.items()):
        if ism_id in enforced:
            buckets["enforced"].append(ism_id)
        elif ism_id in mapped:
            buckets["mapped"].append(ism_id)
        elif record["surfaces"] == ["organisational"]:
            buckets["out_of_scope"].append(ism_id)
        else:
            buckets["unassessed"].append(ism_id)
    return buckets, {"index": index, "enforced": enforced, "mapped": mapped,
                     "gates": via_gate}


def mechanism_rows(root: Path) -> list[tuple[str, str, str]]:
    """One row per control that has something running for it."""
    registry = load_yaml(root / "controls" / "registry.yaml")
    rows = []
    for ctl in registry.get("controls", []) or []:
        impl = ctl.get("implementation") or {}
        if not impl.get("gate"):
            continue
        files = ", ".join(f"`{f}`" for f in impl.get("files", []) or []) or "its own config"
        rows.append((ctl["id"], ctl.get("title", ""), f"{impl['gate']} — {files}"))
    return rows


def build(root: Path, findings: list[dict], notes: list[str], scope: str,
          scanners_ran: bool, audit: dict | None) -> str:
    buckets, detail = classify(root)
    index = detail["index"]
    total = len(index)

    out: list[str] = []
    add = out.append

    add("# Security report")
    add("")
    add(
        f"_Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} by "
        "`.github/scripts/security_report.py`. Do not edit by hand._"
    )
    add("")
    add(
        "**This is not a compliance claim, and must not be shown to an assessor as one.** "
        "It records which automated checks ran over this repository and what they found. "
        "The ISM governs a whole system — the people who run it, where it is hosted, who is "
        "allowed near it. A repository is a small part of that."
    )
    add("")

    # ---- what ran ----------------------------------------------------------
    add("## What ran")
    add("")
    add("| Control | What it covers | Where it runs |")
    add("| :--- | :--- | :--- |")
    for cid, title, where_it_runs in mechanism_rows(root):
        add(f"| `{cid}` | {title} | {where_it_runs} |")
    add("")
    add(f"Scanned: {scope}")
    add("")

    # ---- findings ----------------------------------------------------------
    add("## Findings")
    add("")
    if notes:
        for note in notes:
            add(f"> ⚠️ {note}")
        add("")
    if not scanners_ran:
        add(
            "**No scanner output was supplied to this run.** This section reports nothing, "
            "which is not the same as nothing found. A report generated without its "
            "scanners is a coverage statement only."
        )
    elif not findings:
        add(
            "No findings. That means the rules that ran matched nothing — not that the code "
            "is secure. What each ruleset does and does not look for is documented at the top "
            "of its rule file."
        )
    else:
        counts: dict[str, int] = {}
        for f in findings:
            counts[f["severity"]] = counts.get(f["severity"], 0) + 1
        summary = ", ".join(
            f"{counts[s]} {s.lower()}" for s in sorted(counts, key=lambda s: SEVERITY_ORDER.get(s, 9))
        )
        add(f"{len(findings)} findings ({summary}), most severe first.")
        add("")
        add("| Severity | Where | Rule | What |")
        add("| :--- | :--- | :--- | :--- |")
        for f in findings[:FINDING_CAP]:
            add(f"| {f['severity']} | `{f['path']}:{f['line']}` | `{f['rule']}` | {f['message']} |")
        if len(findings) > FINDING_CAP:
            add("")
            add(
                f"{len(findings) - FINDING_CAP} further findings are not listed. Run the "
                "scanners locally for the full set — see `agents/running-the-checks.md`."
            )
    add("")

    # ---- dependency posture ------------------------------------------------
    # Kept apart from the section above on purpose. Those findings are about code written
    # here; these are about code imported from elsewhere, and a report that pooled them
    # would let a clean codebase on a vulnerable dependency read as clean.
    add("## Dependency posture")
    add("")
    if audit is None:
        add(
            "**No dependency audit output was supplied to this run.** Nothing here has "
            "looked at the third-party packages this project depends on, which is not the "
            "same as finding none."
        )
        add("")
        # The usual reason is not breakage: the audit is environment-constrained and off by
        # default locally, so this is the state an ordinary first session reaches. Naming
        # that keeps the sentence above from reading as a fault the reader has to diagnose,
        # and gives them the whole opt-in rather than the one target that needs the other
        # two to have run first.
        add(
            "The dependency audit is off by default because its scanners are release "
            "binaries that cannot be installed into `.venv/` with the rest of the "
            "toolchain. Turn it on once per machine:"
        )
        add("")
        add("```bash")
        add("make setup-audit-tools && make setup-audit-dbs && make audit")
        add("```")
    else:
        ecosystems = audit.get("ecosystems") or []
        audited = [e["name"] for e in ecosystems if e.get("status") == "audited"]
        skipped = [e["name"] for e in ecosystems if e.get("status") != "audited"]
        db = audit.get("database") or {}
        problems = audit.get("problems") or []
        dep_findings = audit.get("findings") or []

        if problems:
            for problem in problems:
                add(f"> ⚠️ The dependency audit reported: {problem}")
            add("")

        # "ran" | "not applicable" | "could not run", recorded by audit.py rather than
        # inferred here. An empty findings list reads identically whether the scan ran and
        # found nothing or never ran at all, and this section resolving that ambiguity the
        # optimistic way is exactly the flattering document this report refuses to be.
        # Older output without the field falls back to the problems list.
        scan_state = audit.get("scan") or ("could not run" if problems else "ran")

        if not audited:
            add(
                "**Not applicable.** No dependency manifest was found for any ecosystem "
                "this audit covers, so nothing was scanned. A check with no subject "
                "matter has found nothing, which is not the same as finding nothing wrong."
            )
        elif scan_state != "ran":
            add(
                f"**No vulnerability scan ran.** {len(audited)} "
                f"{'ecosystem has' if len(audited) == 1 else 'ecosystems have'} manifests "
                f"here ({', '.join(audited)}) and none of them was compared against the "
                "advisories, for the reason given above. **This is not a clean result — "
                "it is no result.** Nothing in this section says whether these dependencies "
                "carry known vulnerabilities."
            )
        elif not dep_findings:
            add(
                f"No known vulnerabilities in {len(audited)} audited "
                f"{'ecosystem' if len(audited) == 1 else 'ecosystems'} "
                f"({', '.join(audited)}), across "
                f"{audit.get('packages', 0)} packages. That means no advisory was recorded "
                "against these versions in the database snapshot named below — not that "
                "the packages are safe."
            )
        else:
            counts: dict[str, int] = {}
            for f in dep_findings:
                counts[f["severity"]] = counts.get(f["severity"], 0) + 1
            order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "UNKNOWN": 4}
            summary = ", ".join(
                f"{counts[s]} {s.lower()}" for s in sorted(counts, key=lambda s: order.get(s, 9))
            )
            add(f"{len(dep_findings)} known vulnerabilities ({summary}), most severe first.")
            add("")
            add("| Severity | Package | Advisory | Fixed in | Declared in |")
            add("| :--- | :--- | :--- | :--- | :--- |")
            for f in dep_findings[:FINDING_CAP]:
                fixed = f.get("fixed") or "no fix published"
                add(f"| {f['severity']} | `{f['package']}` {f.get('installed', '')} | "
                    f"`{f['id']}` | {fixed} | `{f['target']}` |")
            if len(dep_findings) > FINDING_CAP:
                add("")
                add(f"{len(dep_findings) - FINDING_CAP} further vulnerabilities are not "
                    "listed. Run `make audit` for the full set.")

        add("")
        if skipped:
            add(
                f"**Not applicable:** {', '.join(skipped)}. No manifest for these was "
                "found, so they were not scanned and are not a pass."
            )
            add("")
        if scan_state == "ran":
            add(
                f"Scanned with trivy {audit.get('trivy_version', 'unknown')} against a "
                f"vulnerability database snapshot of {db.get('updated_at') or 'unknown'}. "
                "The database is a pinned input rather than a live service, so the same "
                "lockfiles and the same snapshot always yield this same verdict — and when "
                "a verdict changes, the snapshot date says whether the code or the "
                "advisories moved."
            )
        else:
            # The SBOM and the scan fail independently, so this says which one you have.
            # Claiming a snapshot date for a scan that did not happen would attach a
            # provenance trail to a verdict that was never reached.
            add(
                "No database snapshot is recorded, because no scan was run against one."
            )
        add("")
        packages = audit.get("packages", 0)
        if packages:
            add(
                f"The bill of materials is `docs/dependencies.md`: {packages} packages, "
                "produced by syft, which needs neither the database nor the network. It is "
                "generated independently of the scan above, so it is present even when the "
                "scan could not run — an inventory of what is here, not a claim about it."
            )
        else:
            add(
                "No bill of materials was produced. `docs/dependencies.md`, if it is "
                "present, describes an earlier run rather than this one."
            )
        add("")
        add(
            "**A dependency audit reports and blocks nothing.** It is not on the commit "
            "hook: a CVE published overnight is not a reason a commit cannot be saved."
        )
    add("")

    # ---- ISM position ------------------------------------------------------
    add("## Where this sits against the ISM")
    add("")
    add(f"The June 2026 ISM has {total} controls. This repository can say something about "
        "a small number of them.")
    add("")
    add("| | Controls | What it means |")
    add("| :--- | ---: | :--- |")
    add(f"| Has a check behind it | {len(buckets['enforced'])} | A pinned tool in this "
        "repository is wired to this control |")
    add(f"| Mapped, nothing runs | {len(buckets['mapped'])} | Recorded as in scope, with no "
        "check behind it yet |")
    add(f"| Unassessed | {len(buckets['unassessed'])} | Evidence could live in code or "
        "infrastructure. Nothing here looks at it |")
    add(f"| Out of scope | {len(buckets['out_of_scope'])} | People, policy, premises and "
        "process. No repository can evidence these |")
    add("")
    add(
        "**A check being wired is not a check having run.** The first row counts controls "
        "with a mechanism attached, not controls verified on this commit. A check whose "
        "subject matter is absent — no Python or JavaScript in the tree for the rules to read — "
        "has not run, and reads identically here to one that ran and found nothing. The "
        "column below says where each would run."
    )
    add("")
    add(
        "**Nothing here prevents a merge.** The checks run on the developer's machine "
        "before a commit, where they are bypassable, and in CI afterwards, where they "
        "report. Enforcing that a red check stops a merge is branch protection — a setting "
        "on the repository itself, which no template can install for you."
    )
    add("")
    add(
        "**Unassessed is not the same as reachable.** A control whose evidence lives in "
        "deployed infrastructure — ISM-0260 requires all web access to pass through web "
        "proxies — sits in that row because it is not organisational, not because runwAI "
        "could check it. Reading that row as a to-do list would overstate what any "
        "repository-level tool can do."
    )
    add("")

    # ---- checked controls, in full ----------------------------------------
    add("### The controls that are checked")
    add("")
    add("| ISM | Via | Where it runs | What the ISM asks for |")
    add("| :--- | :--- | :--- | :--- |")
    for ism_id in buckets["enforced"]:
        via = ", ".join(sorted(detail["enforced"][ism_id]))
        gate = ", ".join(sorted(detail["gates"].get(ism_id, {"—"})))
        text = " ".join(index[ism_id]["description"].split())
        add(f"| `{ism_id}` | {via} | {gate} | {text[:140]}{'…' if len(text) > 140 else ''} |")
    add("")

    if buckets["mapped"]:
        add("### Mapped, but nothing runs yet")
        add("")
        add(
            "Recorded as in scope with no mechanism behind them. Listed rather than hidden, "
            "because a control that is silently absent looks identical to one that passed."
        )
        add("")
        for ism_id in buckets["mapped"]:
            via = ", ".join(sorted(detail["mapped"][ism_id]))
            add(f"- `{ism_id}` ({via}) — {index[ism_id]['topic']}")
        add("")

    add("---")
    add("")
    add(
        "Control text is © Commonwealth of Australia, released under CC BY 4.0. runwAI is "
        "not an ASD publication and carries no ASD endorsement."
    )
    add("")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", type=Path)
    parser.add_argument(
        "--findings", action="append", default=[], type=Path,
        help="semgrep --json output. Repeatable. Missing files are reported, not ignored.",
    )
    parser.add_argument(
        "--audit", default=None, type=Path,
        help="audit.py result JSON. Absent means the dependency audit did not run, which "
             "the report states rather than glossing over.",
    )
    parser.add_argument(
        "--scan-scope", default="not recorded",
        help="what the scanners looked at, so the report says which run produced it",
    )
    parser.add_argument("--out", default=None, type=Path)
    args = parser.parse_args()

    root = args.repo_root.resolve()
    required = root / "controls" / "ism-index.json"
    if not required.is_file():
        print(
            f"FATAL: {required} is missing. Run: python3 .runwai/tools/ism.py index",
            file=sys.stderr,
        )
        return 2

    findings, notes = read_findings(args.findings)
    audit, audit_notes = read_audit(args.audit)
    try:
        content = build(root, findings, notes + audit_notes, args.scan_scope,
                        bool(args.findings), audit)
    except (OSError, KeyError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"FATAL: could not build the report: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    # docs/, not the root: a root slot requires a tool or a convention reading the path
    # there, and nothing reads this one — see decision 9 in .runwai/decisions.yaml.
    out = args.out or (root / "docs" / "security-report.md")
    out.write_text(content, encoding="utf-8")
    print(f"wrote {out.name}: {len(findings)} findings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
