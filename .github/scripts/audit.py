#!/usr/bin/env python3
"""Audit the dependencies for known vulnerabilities, and write the bill of materials.

The checks beside this one read source files. They say nothing about the third-party
packages that source depends on, and a clean codebase sitting on a vulnerable dependency
is not secure — so a report that cannot tell those two apart is the kind of flattering
document this repository exists to refuse. This closes that gap for RWA-0031 (are the
imported components known-vulnerable?) and RWA-0032 (produce the SBOM and publish it).

WHAT MAKES THIS DETERMINISTIC

A CVE scanner is normally the least reproducible thing in a pipeline: the vulnerability
database moves under you, so the same lockfile can pass on Monday and fail on Tuesday with
no commit in between. That is not a verdict, it is a weather report.

So the database is an input here, not an ambient service. `--setup` downloads it once, into
a cache directory, and that is the only step that touches the network. Every scan after it
runs with `--skip-db-update --offline-scan` against exactly what was downloaded, and the
snapshot's own `UpdatedAt` is recorded in the output and in the report. Same lockfile plus
same database snapshot yields the same verdict, and when the verdict changes you can see
which of the two moved.

WHAT IT WILL NOT DO

  * Block. It is not on the commit hook and never should be — a CVE published overnight is
    not a reason a commit cannot be saved, and `.github/workflows/posture.yml` reports
    rather than gates. `make first-session` runs it without letting it abort the session.
  * Call a scan of nothing a pass. An ecosystem with no manifest in the tree reports `not
    applicable`, distinctly and by name. A check with no subject matter has found nothing,
    not nothing wrong.
  * Guess when it cannot run. A missing scanner or a missing database exits 2 and says what
    to install or which target to run, rather than reporting a clean tree.
  * Lose one control to the other's failure. The two legs are independent: the bill of
    materials (RWA-0032) needs syft alone, the vulnerability scan (RWA-0031) needs trivy
    and the database. A network that blocks the database still produces the SBOM, and the
    `scan` field in the JSON records which of the two actually ran, so a scan that never
    happened cannot read as a clean one.

Stdlib only; shells out to the pinned scanners. Their versions live in the Makefile, which
is where the install happens, so there is one source of truth for the pins.

Usage:
    python3 .github/scripts/audit.py --setup      # download the database (the networked step)
    python3 .github/scripts/audit.py              # scan offline, write the SBOM and the JSON

Exit codes, house convention:
    0  clean, or nothing to audit (`not applicable`)
    1  known vulnerabilities found
    2  could not run — a scanner or the database is missing (the output says which)
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

# Manifest filenames per ecosystem, and the `Type` values trivy reports for each. The
# manifests decide applicability — they are what the tree can be asked about without
# running anything — and the types are how a finding is attributed back to an ecosystem.
#
# requirements.txt is included alongside the true lockfiles. It does not pin transitively,
# so auditing it covers less than a lockfile does; covering less is still more than
# skipping the ecosystem, and the report names the file each finding came from.
ECOSYSTEMS: dict[str, tuple[tuple[str, ...], frozenset[str]]] = {
    "python": (
        ("requirements.txt", "requirements-dev.txt", "Pipfile.lock", "poetry.lock",
         "uv.lock", "pdm.lock"),
        frozenset({"pip", "pipenv", "poetry", "uv", "pdm", "python-pkg"}),
    ),
    "node": (
        ("package-lock.json", "yarn.lock", "pnpm-lock.yaml", "npm-shrinkwrap.json"),
        frozenset({"npm", "yarn", "pnpm", "node-pkg"}),
    ),
    "rust": (("Cargo.lock",), frozenset({"cargo"})),
    "go": (("go.mod", "go.sum"), frozenset({"gomod", "gobinary"})),
    "ruby": (("Gemfile.lock",), frozenset({"bundler", "gemspec"})),
    "php": (("composer.lock",), frozenset({"composer", "composer-vendor"})),
    "java": (("pom.xml", "gradle.lockfile"), frozenset({"maven", "gradle", "jar"})),
    "dotnet": (("packages.lock.json",), frozenset({"nuget", "dotnet-core"})),
}

# Walking the whole tree is the point — a lockfile three directories down is still a
# lockfile — but installed dependency trees and build outputs are not the subject.
# Auditing node_modules audits what npm already resolved from the lockfile being audited.
#
# The same set is handed to both scanners, so the manifest walk, the CVE scan and the
# bill of materials all describe the same tree. .audit-cache/ is the one that has to be
# here: it holds the pinned scanner binaries, and syft reads the Go module graph compiled
# into them — which put six hundred of trivy's own dependencies in this project's SBOM
# the first time this ran.
SKIP_DIRS = {".git", "node_modules", "vendor", ".venv", "venv", "__pycache__",
             ".audit-cache", "target", "dist", "build", ".mypy_cache", ".ruff_cache"}

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "UNKNOWN": 4}


def run(cmd: list[str], cwd: Path, timeout: int = 900) -> tuple[int, str]:
    try:
        proc = subprocess.run(  # nosec B603 - fixed argv, no shell, no user input
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
    except FileNotFoundError:
        return -1, ""
    except (OSError, subprocess.SubprocessError) as exc:
        return -2, f"{type(exc).__name__}"
    return proc.returncode, proc.stdout + proc.stderr


def find_manifests(root: Path) -> dict[str, list[str]]:
    """Which ecosystems this tree actually has something to say about."""
    wanted = {name: eco for eco, (names, _) in ECOSYSTEMS.items() for name in names}
    found: dict[str, list[str]] = {eco: [] for eco in ECOSYSTEMS}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if SKIP_DIRS.intersection(rel.parts):
            continue
        eco = wanted.get(path.name)
        if eco:
            found[eco].append(rel.as_posix())
    return {eco: sorted(paths) for eco, paths in found.items()}


def db_snapshot(cache: Path) -> dict | None:
    """The database's own identity, so a verdict can be tied to what produced it."""
    meta = cache / "db" / "metadata.json"
    if not meta.is_file():
        return None
    try:
        data = json.loads(meta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return {"updated_at": data.get("UpdatedAt", ""),
            "downloaded_at": data.get("DownloadedAt", ""),
            "version": data.get("Version", "")}


def tool_version(name: str, root: Path) -> str:
    code, out = run([name, "--version"], root, timeout=60)
    if code != 0:
        return "unknown"
    first = next((ln.strip() for ln in out.splitlines() if ln.strip()), "unknown")
    # trivy prints "Version: 0.72.0"; syft prints "syft 1.50.0". Reduce both to the
    # number, so the report reads "syft 1.50.0" rather than "syft syft 1.50.0".
    if first.startswith("Version:"):
        return first.split(":", 1)[1].strip()
    return first[len(name):].strip() if first.startswith(name) else first


def scan(root: Path, cache: Path) -> tuple[list[dict], list[str]]:
    """Trivy, offline, against the cached database. Returns (findings, problems)."""
    out_path = cache / "trivy.json"
    skips: list[str] = []
    for name in sorted(SKIP_DIRS):
        skips += ["--skip-dirs", f"./**/{name}", "--skip-dirs", f"./{name}"]
    code, out = run([
        "trivy", "fs",
        "--skip-db-update",      # the database is an input, never refreshed mid-run
        "--offline-scan",        # no API calls to resolve dependencies either
        "--scanners", "vuln",    # CVEs only: secrets are RWA-0010's job, and misconfig
                                 # would duplicate what checkov is mapped to
        "--format", "json",
        "--quiet",
        "--cache-dir", str(cache),
        "--output", str(out_path),
        *skips,
        ".",
    ], root)
    if code < 0:
        return [], ["trivy could not be executed"]
    if code != 0 or not out_path.is_file():
        tail = " ".join(out.split())[-300:]
        return [], [f"trivy exited {code} and produced no usable output: {tail}"]

    try:
        data = json.loads(out_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [], [f"trivy output could not be read ({type(exc).__name__})"]

    type_to_eco = {t: eco for eco, (_, types) in ECOSYSTEMS.items() for t in types}
    findings: list[dict] = []
    for result in data.get("Results") or []:
        eco = type_to_eco.get(result.get("Type", ""), "other")
        for vuln in result.get("Vulnerabilities") or []:
            findings.append({
                "ecosystem": eco,
                "target": result.get("Target", "(unknown)"),
                "id": vuln.get("VulnerabilityID", "(unnamed)"),
                "package": vuln.get("PkgName", "(unknown)"),
                "installed": vuln.get("InstalledVersion", ""),
                "fixed": vuln.get("FixedVersion", ""),
                "severity": str(vuln.get("Severity", "UNKNOWN")).upper(),
                "title": " ".join(str(vuln.get("Title", "")).split()),
            })
    findings.sort(key=lambda f: (
        SEVERITY_ORDER.get(f["severity"], 9), f["ecosystem"], f["package"], f["id"]
    ))
    return findings, []


def sbom(root: Path, cache: Path) -> tuple[list[dict], list[str]]:
    """Syft, over the same tree. Returns (packages, problems)."""
    if shutil.which("syft") is None:
        return [], ["syft is not installed, so no bill of materials was produced"]
    out_path = cache / "syft.json"
    excludes: list[str] = []
    for name in sorted(SKIP_DIRS):
        excludes += ["--exclude", f"./**/{name}/**", "--exclude", f"./{name}/**"]
    code, out = run(
        ["syft", "scan", "dir:.", "-o", f"syft-json={out_path}", "-q", *excludes], root
    )
    if code != 0 or not out_path.is_file():
        tail = " ".join(out.split())[-300:]
        return [], [f"syft exited {code} and produced no usable output: {tail}"]
    try:
        data = json.loads(out_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [], [f"syft output could not be read ({type(exc).__name__})"]

    packages = []
    for art in data.get("artifacts") or []:
        licences = sorted({
            lic.get("value") or lic.get("spdxExpression") or ""
            for lic in (art.get("licenses") or [])
        } - {""})
        locations = sorted({
            loc.get("path", "").lstrip("/") for loc in (art.get("locations") or [])
        } - {""})
        packages.append({
            "name": art.get("name", ""),
            "version": art.get("version", ""),
            "type": art.get("type", ""),
            "licences": licences,
            "locations": locations,
        })
    packages.sort(key=lambda p: (p["type"], p["name"].lower(), p["version"]))
    return packages, []


def write_sbom_markdown(path: Path, packages: list[dict], syft_version: str) -> None:
    """Render the SBOM as the committed, human-readable artefact.

    Deliberately timestamp-free, for the same reason .runwai/docs/report.md is: the file is
    committed, so a timestamp would produce a diff on every run and the diff would stop
    carrying information. Regenerating on unchanged lockfiles produces a byte-identical
    file, which makes a real change to the dependency set visible in review.
    """
    out: list[str] = []
    add = out.append
    add("# Dependencies")
    add("")
    add(
        "The software bill of materials for this repository, generated by "
        f"`.github/scripts/audit.py` from syft {syft_version}. Do not edit by hand — run "
        "`make audit`."
    )
    add("")
    add(
        "This file is deliberately timestamp-free: regenerating it without changing a "
        "lockfile produces a byte-identical file, so a diff here means the dependency set "
        "actually changed."
    )
    add("")
    if not packages:
        add(
            "**No third-party packages were found.** That is a statement about this tree, "
            "not a clean bill of health: a repository with no dependency manifests has "
            "nothing for a dependency audit to look at. See `docs/security-report.md` for "
            "which ecosystems reported `not applicable`."
        )
        add("")
    else:
        by_type: dict[str, int] = {}
        for pkg in packages:
            by_type[pkg["type"]] = by_type.get(pkg["type"], 0) + 1
        summary = ", ".join(f"{count} {kind}" for kind, count in sorted(by_type.items()))
        add(f"{len(packages)} packages ({summary}).")
        add("")
        add("| Package | Version | Type | Licence | Declared in |")
        add("| :--- | :--- | :--- | :--- | :--- |")
        for pkg in packages:
            licences = ", ".join(pkg["licences"]) or "not declared"
            where = ", ".join(f"`{loc}`" for loc in pkg["locations"][:2]) or "—"
            add(f"| `{pkg['name']}` | {pkg['version']} | {pkg['type']} | {licences} | {where} |")
        add("")
    add("---")
    add("")
    add(
        "A package appearing here is not a claim that it is safe. Known vulnerabilities in "
        "these packages are reported under **Dependency posture** in "
        "`docs/security-report.md`, and a licence recorded here is the one the package "
        "declares about itself."
    )
    add("")
    path.write_text("\n".join(out), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", type=Path)
    parser.add_argument(
        "--cache-dir", default=None, type=Path,
        help="where the vulnerability database lives (default: .audit-cache/)",
    )
    parser.add_argument(
        "--setup", action="store_true",
        help="download the vulnerability database. The only step here that uses the network.",
    )
    parser.add_argument("--out", default=None, type=Path, help="audit result JSON")
    parser.add_argument("--sbom", default=None, type=Path, help="the SBOM markdown")
    args = parser.parse_args()

    root = args.repo_root.resolve()
    cache = (args.cache_dir or (root / ".audit-cache")).resolve()
    out_json = args.out or (cache / "audit.json")
    sbom_md = args.sbom or (root / "docs" / "dependencies.md")

    # The two scanners are checked separately because they answer separate questions and
    # fail for separate reasons. Requiring trivy before syft would run meant a machine that
    # can reach GitHub's releases but not the database registry produced neither the scan
    # nor the bill of materials, when only the scan depends on the registry.
    have_trivy = shutil.which("trivy") is not None
    have_syft = shutil.which("syft") is not None

    if not have_trivy and not have_syft:
        print(
            "COULD NOT RUN: neither trivy nor syft is on PATH.\n"
            "  Install the pinned versions with: make setup-audit-tools\n"
            "  If you have already run that, they are in .audit-cache/bin/ and this was\n"
            "  invoked without it on PATH. Use `make audit`, which adds it, or run:\n"
            '    export PATH="$PWD/.audit-cache/bin:$PATH"',
            file=sys.stderr,
        )
        return 2

    if args.setup:
        if not have_trivy:
            print(
                "COULD NOT RUN: trivy is not on PATH, and the database is trivy's.\n"
                "  Install the pinned versions with: make setup-audit-tools\n"
                "  If you have already run that, they are in .audit-cache/bin/ and this\n"
                "  was invoked without it on PATH. Use `make setup-audit-dbs`, which adds\n"
                "  it, or run:\n"
                '    export PATH="$PWD/.audit-cache/bin:$PATH"',
                file=sys.stderr,
            )
            return 2
        cache.mkdir(parents=True, exist_ok=True)
        code, out = run(["trivy", "fs", "--download-db-only", "--cache-dir", str(cache)], root)
        if code != 0:
            print(f"COULD NOT RUN: the database download failed (exit {code}).\n{out[-500:]}",
                  file=sys.stderr)
            return 2
        snap = db_snapshot(cache) or {}
        print(f"vulnerability database ready in {cache.name}/ "
              f"(snapshot {snap.get('updated_at', 'unknown')})")
        return 0

    manifests = find_manifests(root)
    applicable = {eco: paths for eco, paths in manifests.items() if paths}

    snapshot = db_snapshot(cache)
    result = {
        "database": snapshot,
        "trivy_version": tool_version("trivy", root) if have_trivy else None,
        "syft_version": tool_version("syft", root) if have_syft else None,
        # Recorded rather than inferred. The report used to decide "no known
        # vulnerabilities" from an empty findings list, which reads identically whether the
        # scan ran and found nothing or never ran at all — the exact coverage lie this
        # repository exists to refuse. One field removes the ambiguity for every reader.
        "scan": "could not run",
        "ecosystems": [
            {
                "name": eco,
                "status": "audited" if paths else "not applicable",
                "manifests": paths,
            }
            for eco, paths in sorted(manifests.items())
        ],
        "findings": [],
        "packages": 0,
        "problems": [],
    }

    def emit(code: int, lines: list[str]) -> int:
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
        print("\n".join(lines))
        return code

    # --- the bill of materials, produced before and independently of the scan ----------
    #
    # RWA-0032 is "generate an SBOM and publish it to consumers". It needs syft and nothing
    # else — no vulnerability database, no network, no trivy — so it is produced first and
    # its failure is recorded separately. This used to run only after the database check
    # had passed, which meant a host that blocks the database download cost both controls
    # when it should only ever have cost RWA-0031.
    #
    # It is written on every path below, including "nothing to scan": a committed bill of
    # materials still listing packages from a directory somebody deleted is worse than an
    # empty one, because it is confidently wrong rather than visibly empty.
    # Written only when syft actually produced a result. An empty package list from a
    # working syft is a fact and gets written; an empty list from a syft that failed is the
    # absence of a fact, and overwriting a committed bill of materials with it would
    # destroy a good artefact on a transient scanner error.
    packages, sbom_problems = sbom(root, cache)
    if not sbom_problems:
        write_sbom_markdown(sbom_md, packages, result["syft_version"] or "unavailable")
    result["packages"] = len(packages)
    result["problems"] = list(sbom_problems)

    def sbom_lines() -> list[str]:
        if sbom_problems:
            return [f"  {p}" for p in sbom_problems]
        return [f"  Bill of materials: {len(packages)} packages written to {sbom_md}."]

    if not applicable:
        # Not a pass. Nothing was audited because there was nothing to audit, and the two
        # have to read differently or the report is describing a check that never ran.
        result["scan"] = "not applicable"
        return emit(0, [
            "Dependency audit: NOT APPLICABLE.",
            f"  No dependency manifest was found for any of the {len(ECOSYSTEMS)} "
            "ecosystems this audit covers,",
            "  so nothing was scanned. That is not the same as a clean scan.",
            *sbom_lines(),
            f"  Wrote {out_json}.",
        ])

    if not have_trivy:
        result["problems"].append("trivy is not installed, so no vulnerability scan ran")
        return emit(2, [
            "Dependency audit: NO VULNERABILITY SCAN.",
            "  trivy is not installed, so nothing was compared against the advisories.",
            "  Install the pinned scanners with: make setup-audit-tools",
            *sbom_lines(),
        ])

    if snapshot is None:
        result["problems"].append(
            "the vulnerability database is absent, so no scan ran"
        )
        return emit(2, [
            "Dependency audit: NO VULNERABILITY SCAN.",
            f"  No vulnerability database in {cache.name}/, and this audit never fetches "
            "one mid-scan —",
            "  the database is a pinned input, not an ambient service.",
            "  Download it once with: make setup-audit-dbs",
            *sbom_lines(),
        ])

    findings, problems = scan(root, cache)
    result["findings"] = findings
    result["problems"] = problems + sbom_problems
    result["scan"] = "could not run" if problems else "ran"

    lines: list[str] = []
    audited = ", ".join(sorted(applicable))
    skipped = sorted(eco for eco, paths in manifests.items() if not paths)
    counts: dict[str, int] = {}
    for f in findings:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1

    if problems:
        lines.append("Dependency audit: COULD NOT RUN.")
        lines += [f"  {p}" for p in problems]
        lines.append("  Treat this run as incomplete rather than clean.")
        code = 2
    elif findings:
        summary = ", ".join(
            f"{counts[s]} {s.lower()}"
            for s in sorted(counts, key=lambda s: SEVERITY_ORDER.get(s, 9))
        )
        lines.append(f"Dependency audit: {len(findings)} known vulnerabilities ({summary}).")
        for f in findings[:10]:
            fix = f"fixed in {f['fixed']}" if f["fixed"] else "no fix published"
            lines.append(f"  {f['severity']:<8} {f['package']} {f['installed']} "
                         f"({f['id']}, {fix}) — {f['target']}")
        if len(findings) > 10:
            lines.append(f"  ... and {len(findings) - 10} more; the full set is in {out_json}.")
        code = 1
    else:
        lines.append("Dependency audit: no known vulnerabilities.")
        lines.append("  The packages found carry no advisory in this database snapshot. "
                     "That is not")
        lines.append("  a claim that they are safe — only that nothing known was recorded "
                     "against them.")
        code = 0

    lines.append(f"  Audited: {audited}. Not applicable: {', '.join(skipped) or 'none'}.")
    lines.append(f"  Database snapshot {snapshot.get('updated_at', 'unknown')}, "
                 f"trivy {result['trivy_version']}.")
    lines += sbom_lines()
    lines.append("  This audit reports. It is not on the commit hook and blocks nothing.")
    return emit(code, lines)


if __name__ == "__main__":
    raise SystemExit(main())
