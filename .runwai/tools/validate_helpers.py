#!/usr/bin/env python3
"""runwAI self-check for the AI helper layer.

Checks the structure of AGENTS.md, agents/, llms.txt, .runwai/ and the adopter-facing
toolchain configs at the root. Like the other self-checks it is deliberately deterministic:
no network, no LLM, no clock-dependent behaviour. Same tree in, same verdict out, same exit
code.

Stdlib only, so it runs before anything is installed.

What it enforces, and why each one is a real failure mode:

  * Every relative link in a live helper file resolves. A confident index pointing at a
    missing page is worse than no index: an agent follows it and reports the project as
    broken.
  * Every rule file uses a section prefix declared in agents/rules/_sections.md, and has
    parseable frontmatter with title and impact. An unknown prefix means the rule is
    invisible to anything that groups by section.
  * Every rule file is linked from agents/README.md. A rule nobody linked is a file nobody
    reads.
  * The root toolchain configs parse, declare an exact version, and agree with the version
    README.md documents. These ship live for the adopter but run against nothing here, so
    version drift between a config and its documentation is the one failure mode that would
    otherwise reach an adopter unnoticed. Deleting a config the project does not need is
    expected and passes; deleting it while leaving its README row or llms.txt entry
    behind does not.
  * Every record in .runwai/decisions.yaml carries a title, a status and a date, and no
    id is used twice. Ids are cited from commit messages, so a duplicate makes a citation
    ambiguous after the fact.
  * The steal manifest agrees with the tree: every row points at a file that exists, every
    file blessed with a STEAL marker has a row, and the table is sorted. A manifest is a
    set of claims about files, and a claim nobody rechecks is exactly the failure mode
    AGENTS.md warns about — fluent output about something nobody verified.

Exit codes:
    0  all checks passed (warnings may still be printed)
    1  one or more checks failed
    2  the validator could not run

Usage:
    python3 .runwai/tools/validate_helpers.py [--repo-root PATH] [--strict] [PATH ...]

Positional paths narrow the STEAL marker sweep to those files and nothing else; every
other check here always runs against the whole tree. Pre-commit passes the staged files so
that a commit does not pay to re-read a tree it did not touch. The `posture` workflow, and
report.py, invoke it with no paths — that whole-tree run is the authoritative one.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# [text](target) — the target group stops at whitespace or the closing paren.
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")

# "## 3. Code Quality (quality)" -> "quality"
SECTION_ID = re.compile(r"^##\s+\d+\.\s+.+?\(([a-z0-9-]+)\)\s*$", re.M)

# A rule filename: {section}-{name}.md. Files starting with _ are meta, not rules.
RULE_FILE = re.compile(r"^(?!_)([a-z0-9]+)-[a-z0-9-]+\.md$")

# All of docs/, not just docs/adr/. The narrower set left docs/architecture.md unchecked,
# where two links still pointed at docs/adr/0001 months after TODO-11 moved that record to
# .runwai/decisions/ — a confident cross-reference to a page that was not there, in the
# document that explains the repository's own rules.
#
# README.md is in the set because the first-session instructions promise it is: AGENTS.md
# tells the setup agent that deleting the reuse layer means clearing every link `make check`
# names, and README.md links into STEAL.md and .steal/ twice. Left out, the front door was
# the one file where a deletion could leave a dangling link and the check would still say
# PASSED — the worst place to have one, and a promise the tool was not keeping.
LIVE_LINK_ROOTS = (
    "AGENTS.md", "CLAUDE.md", "README.md", "llms.txt", "agents", "docs", ".runwai",
    "STEAL.md", ".steal",
)

# A blessing under .steal/curation.md's protocol: a comment line whose whole purpose is the marker —
# an optional comment leader in whatever syntax the host language uses, then STEAL:, then a
# description. Anchored to the line start so that prose *about* the protocol is not mistaken
# for a blessing. That distinction is not hypothetical: the first run of this check flagged
# AGENTS.md and README.md for explaining the convention.
STEAL_MARKER = re.compile(
    r"^[ \t]*(?://+|#+|\*+|/\*+|<!--|--|;+)?[ \t]*STEAL:[ \t]*(?!IGNORE\b)\S", re.M
)

# A manifest row: | `path` | Visibility | tags | description |
STEAL_ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|", re.M)

# Directories with nothing to bless and a great many files to walk.
STEAL_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "dist"}

# Markdown is documentation, not an export. Every file that teaches the convention has to
# show the marker to teach it, and a fenced example is indistinguishable from a blessing
# once the line-start anchor is applied. Nothing in Markdown is stealable as a unit anyway.
STEAL_SKIP_SUFFIXES = {".md"}

# Toolchain configs that ship live at the root, each mapped to the pattern that extracts
# the version it declares about itself.
#
# runwAI is Python, YAML and Markdown, so none of these runs against this repository —
# which is exactly why the declared version is checked against the version README.md
# documents. A config and its documentation drifting apart is the failure mode that a
# directory of never-copied templates used to hide behind, and it is the one thing about
# an unexercised config that can still be checked deterministically and offline.
ROOT_CONFIGS: dict[str, re.Pattern[str]] = {
    "biome.json": re.compile(r"https://biomejs\.dev/schemas/([0-9][0-9A-Za-z.\-]*)/schema\.json"),
    "playwright.config.ts": re.compile(r"@playwright/test@([0-9][0-9A-Za-z.\-]*)"),
    "promptfooconfig.yaml": re.compile(r"promptfoo@([0-9][0-9A-Za-z.\-]*)"),
}

# A row of README.md's toolchain table: | `file` | `package` | version | licence |
# The version group must start with a digit, so a floating specifier never satisfies it.
CONFIG_ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*([0-9][0-9A-Za-z.\-]*)\s*\|", re.M)


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, where: str, msg: str) -> None:
        self.errors.append(f"{where}: {msg}")

    def warn(self, where: str, msg: str) -> None:
        self.warnings.append(f"{where}: {msg}")


def read(path: Path, report: Report) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        report.error(str(path), f"unreadable: {exc}")
        return None


def frontmatter(text: str) -> dict[str, str] | None:
    """Parse the leading --- block as flat key: value pairs.

    Deliberately not YAML: keeping this stdlib-only means the check runs before any
    dependency is installed, and rule frontmatter is flat by convention anyway.
    """
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    out: dict[str, str] = {}
    for line in text[3:end].splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        out[key.strip()] = value.strip()
    return out


def iter_markdown(root: Path) -> list[Path]:
    """Every live helper file whose links should resolve.

    Files named _*.md are skeletons (_template.md, _sections.md) and are skipped: their
    placeholder links point at names the author will choose, so checking them would only
    ever produce a false failure.
    """
    files: list[Path] = []
    for rel in LIVE_LINK_ROOTS:
        target = root / rel
        if target.is_file():
            files.append(target)
        elif target.is_dir():
            files.extend(
                sorted(
                    p for p in target.rglob("*.md")
                    if p.is_file() and not p.name.startswith("_")
                )
            )
    return files


def check_links(root: Path, report: Report) -> int:
    checked = 0
    for path in iter_markdown(root):
        text = read(path, report)
        if text is None:
            continue
        where = str(path.relative_to(root))
        for target in MD_LINK.findall(text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            # Strip any anchor; the file is what we can verify.
            clean = target.split("#", 1)[0]
            if not clean:
                continue
            resolved = (path.parent / clean).resolve()
            checked += 1
            if not resolved.exists():
                report.error(where, f"link target does not exist: {target}")
    return checked


def check_rules(root: Path, report: Report) -> int:
    rules_dir = root / "agents" / "rules"
    if not rules_dir.is_dir():
        report.error("agents/rules", "directory is missing")
        return 0

    sections_path = rules_dir / "_sections.md"
    sections_text = read(sections_path, report)
    if sections_text is None:
        return 0
    sections = set(SECTION_ID.findall(sections_text))
    if not sections:
        report.error("agents/rules/_sections.md", "declares no sections; expected '## N. Name (id)' headings")
        return 0

    index_text = read(root / "agents" / "README.md", report) or ""
    linked = {t.split("#", 1)[0] for t in MD_LINK.findall(index_text)}

    count = 0
    for path in sorted(rules_dir.glob("*.md")):
        name = path.name
        if name.startswith("_"):
            continue
        where = f"agents/rules/{name}"
        match = RULE_FILE.match(name)
        if not match:
            report.error(where, "filename must be {section}-{name}.md, lowercase and hyphenated")
            continue
        count += 1

        prefix = match.group(1)
        if prefix not in sections:
            report.error(
                where,
                f"section prefix '{prefix}' is not declared in _sections.md "
                f"(declared: {', '.join(sorted(sections))})",
            )

        text = read(path, report)
        if text is None:
            continue
        fm = frontmatter(text)
        if fm is None:
            report.error(where, "missing or unterminated --- frontmatter block")
            continue
        for field in ("title", "impact"):
            if not fm.get(field):
                report.error(where, f"frontmatter is missing '{field}'")

        if f"rules/{name}" not in linked:
            report.error(
                where,
                "is not linked from agents/README.md. A rule nobody linked is a rule "
                "nobody reads.",
            )
    return count


def check_root_configs(root: Path, report: Report) -> int:
    """Assert the live toolchain configs parse, pin a version, and match the docs."""
    readme = read(root / "README.md", report)
    if readme is None:
        return 0
    documented = {name: version for name, _package, version in CONFIG_ROW.findall(readme)}

    count = 0
    for name, version_pattern in ROOT_CONFIGS.items():
        path = root / name
        if not path.is_file():
            # Absent is a legitimate outcome, not a failure. AGENTS.md tells the setup agent
            # to delete the configs this project does not need — a promptfoo config in a
            # repository that never calls a model is a file that rots and misleads. What is
            # checked is that a deletion was completed: the README row has to go too, and
            # the reverse direction below catches a row left behind.
            if name in documented:
                report.error(
                    "README.md",
                    f"documents '{name}', which is not in the tree. If it was deleted "
                    "deliberately, remove its row here and its entry in llms.txt, then "
                    "note it in docs/setup.md.",
                )
            continue
        text = read(path, report)
        if text is None:
            continue
        count += 1

        if name.endswith(".json"):
            try:
                json.loads(text)
            except json.JSONDecodeError as exc:
                report.error(name, f"is not valid JSON: {exc}")

        found = version_pattern.search(text)
        if found is None:
            report.error(
                name,
                "declares no exact version. A config that does not name the version it was "
                "written against is a floating pin by omission.",
            )
            continue

        declared = found.group(1)
        if name not in documented:
            report.error(
                "README.md",
                f"'{name}' ships live but is not in the toolchain table. An adopter cannot "
                "pin what nothing documents.",
            )
        elif documented[name] != declared:
            report.error(
                name,
                f"declares version {declared}, but README.md documents {documented[name]}. "
                "Nothing here runs this config, so the documented version is the only thing "
                "an adopter has to go on.",
            )

    # The reverse direction: a documented file that is not in the tree and is not one of
    # the known configs handled above.
    for name in sorted(documented):
        if name not in ROOT_CONFIGS and not (root / name).exists():
            report.error("README.md", f"documents '{name}', which is not present")
    return count


def check_decisions(root: Path, report: Report) -> int:
    """Assert every record in .runwai/decisions.yaml is identified, dated and resolved.

    Read line by line rather than with a YAML parser, for the same reason rule frontmatter
    is: this check runs before anything is installed. The structure it needs is shallow —
    a list of records, each opening with `- id:` — so a parser buys nothing here.

    The old Markdown form is rejected outright rather than ignored. A half-migrated log
    where some records are files and some are entries is worse than either shape, because
    an agent that finds the directory stops looking for the file.
    """
    legacy = root / ".runwai" / "decisions"
    if legacy.exists():
        report.error(
            ".runwai/decisions",
            "still exists. The log is .runwai/decisions.yaml now; a directory left "
            "beside it is a second source of truth. See decision 3.",
        )

    path = root / ".runwai" / "decisions.yaml"
    text = read(path, report)
    if text is None:
        report.error(".runwai/decisions.yaml", "is missing")
        return 0

    ids: list[str] = []
    current: str | None = None
    fields: set[str] = set()

    def close(record: str | None, seen: set[str]) -> None:
        if record is None:
            return
        for field in ("title", "status", "date"):
            if field not in seen:
                report.error(
                    ".runwai/decisions.yaml", f"decision {record} has no '{field}'"
                )

    for line in text.splitlines():
        start = re.match(r"^  - id:\s*(\S+)", line)
        if start:
            close(current, fields)
            current = start.group(1)
            ids.append(current)
            fields = set()
            continue
        field = re.match(r"^    ([a-z_]+):", line)
        if field and current is not None:
            fields.add(field.group(1))
    close(current, fields)

    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        report.error(".runwai/decisions.yaml", f"duplicate decision id '{dup}'")

    return len(ids)


def steal_candidates(root: Path, paths: list[Path] | None) -> list[Path]:
    """The files to sweep for a STEAL marker.

    The whole tree when nothing is passed. That is how `posture` and report.py invoke it,
    and it is the run whose verdict is authoritative: it is the only one that sees a marker
    added by a commit that skipped the hook.

    Given an explicit set, only those files. A marker cannot appear in a file a commit did
    not touch, so re-reading the rest of the tree is work that cannot change the answer —
    and in an adopter's repository, rather than this one, "the rest of the tree" is their
    entire codebase being read from disk on every commit.
    """
    if paths is None:
        return sorted(root.rglob("*"))

    seen: set[Path] = set()
    unique: list[Path] = []
    for given in paths:
        candidate = root / given
        if candidate not in seen:
            seen.add(candidate)
            unique.append(candidate)
    return unique


def check_steal(root: Path, report: Report, paths: list[Path] | None = None) -> int:
    """Assert the steal manifest describes the tree it claims to describe.

    STEAL.md defines a missing manifest as a valid state meaning "nothing is safe to
    steal", so an absent manifest is not an error here. A manifest that disagrees with the
    tree is, in both directions: a row pointing at a file that no longer exists sends an
    agent to lift something that is not there, and a blessed file with no row is invisible
    to the only index anyone reads.

    ``paths`` narrows only the marker sweep. The manifest-side checks never narrow: an
    unsorted table and a row pointing at a deleted file are properties of the whole
    manifest, they cost one file read to recheck, and narrowing them would mean a commit
    that touches nothing under .steal/ stops noticing that the manifest went wrong.
    """
    protocol = root / "STEAL.md"
    steal_dir = root / ".steal"
    if not protocol.is_file():
        # Removing the reuse layer is a legitimate outcome, not a failure. A closed-source
        # repository has nobody to publish reusable units to, and AGENTS.md tells the setup
        # agent to ask rather than assume. What is not legitimate is half of it: a protocol
        # with no index, or an index with nothing governing it, is the confident-index
        # failure the rest of this file exists to catch. So both gone is a decision, and one
        # gone is an error — the same shape as check_root_configs, where an absent config is
        # fine and a README row left behind is not.
        if steal_dir.exists():
            report.error(
                "STEAL.md",
                "is missing while .steal/ is still here. Removing the reuse layer means "
                "removing both in one commit, plus their llms.txt entries and every link "
                "into them — the link check above names any it finds, so run this again "
                "and finish the list it prints. Keeping it means restoring STEAL.md, which "
                "ships live at the root beside LICENSE.",
            )
        return 0

    manifest = root / ".steal" / "manifest.md"
    if not manifest.is_file():
        return 0

    text = read(manifest, report)
    if text is None:
        return 0
    listed = STEAL_ROW.findall(text)

    for rel in listed:
        if not (root / rel).exists():
            report.error(
                ".steal/manifest.md",
                f"lists '{rel}', which is not present. A manifest row is a claim about a "
                "file; the file has to be there.",
            )

    if listed != sorted(listed):
        report.error(
            ".steal/manifest.md",
            "table is not sorted by path. .steal/curation.md requires it so that two "
            "agents enriching the same manifest produce the same diff.",
        )

    indexed = set(listed)
    for path in steal_candidates(root, paths):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if path.suffix in STEAL_SKIP_SUFFIXES or STEAL_SKIP_DIRS.intersection(path.parts):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue  # binary or unreadable: nothing to bless in it
        if STEAL_MARKER.search(content) and rel not in indexed:
            report.error(
                rel,
                "carries a STEAL marker but has no row in .steal/manifest.md. Blessing a "
                "file without indexing it means nobody finds it.",
            )
    return len(listed)


def check_llms_txt(path: Path, where: str, report: Report) -> None:
    """Assert the llmstxt.org structure: exactly one H1, then a blockquote summary.

    Guidance written as `# note` is itself an H1, which silently breaks the file it is
    explaining. That is not hypothetical: it was the first defect this check found, in the
    llms.txt skeleton that has since been retired in favour of the live file.
    """
    text = read(path, report)
    if text is None:
        return
    # Strip HTML comments first: guidance inside them is not content.
    stripped = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    h1s = re.findall(r"^# .+$", stripped, re.M)
    if len(h1s) != 1:
        report.error(
            where,
            f"must have exactly one H1, found {len(h1s)}. Put commentary in an HTML "
            "comment; a line starting with '#' is a heading.",
        )
    if not re.search(r"^> ", stripped, re.M):
        report.error(where, "has no blockquote summary after the H1")


def check_entry_points(root: Path, report: Report) -> None:
    for rel in ("AGENTS.md", "llms.txt", "agents/README.md", ".runwai/docs/provenance.md"):
        if not (root / rel).is_file():
            report.error(rel, "is missing")

    check_llms_txt(root / "llms.txt", "llms.txt", report)

    # Vendored helper structure must carry the upstream licence it was derived under.
    if not (root / "agents" / "LICENSE-UPSTREAM").is_file():
        report.error(
            "agents/LICENSE-UPSTREAM",
            "is missing. The agents/ layout is derived from an upstream project and must "
            "carry its licence.",
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", type=Path)
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help=(
            "files to limit the STEAL marker sweep to, as pre-commit passes its staged "
            "files. Every other check still runs against the whole tree. Omit for the "
            "authoritative whole-tree sweep."
        ),
    )
    args = parser.parse_args()

    root = args.repo_root.resolve()
    if not (root / "AGENTS.md").exists() and not (root / "agents").exists():
        print("FATAL: no helper layer found; is --repo-root correct?", file=sys.stderr)
        return 2

    report = Report()
    check_entry_points(root, report)
    links = check_links(root, report)
    rules = check_rules(root, report)
    configs = check_root_configs(root, report)
    decisions = check_decisions(root, report)
    stealable = check_steal(root, report, args.paths or None)

    for w in report.warnings:
        print(f"WARN  {w}")
    for e in report.errors:
        print(f"ERROR {e}")

    print(
        f"\nrunwai-helpers: {rules} rules, {decisions} decisions, {configs} root configs, "
        f"{stealable} stealable, {links} links checked, {len(report.errors)} errors, "
        f"{len(report.warnings)} warnings"
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
