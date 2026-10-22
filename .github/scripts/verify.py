#!/usr/bin/env python3
"""Prove the security checks work — runwAI's verification receipts.

Answers one question for someone with no security background: do the checks this
repository claims to run actually catch what they claim to catch, right now, on this
machine? It proves it the only honest way — by showing them known-bad input:

  * every active rule fires on committed, deliberately vulnerable fixtures and stays
    silent on the safe ones beside them (semgrep --test over controls/tests/)
  * every rule has at least three vulnerable cases and one safe case, so a rule with
    no test cannot pass silently
  * a second run returns identical verdicts, which is determinism made checkable
  * the secret scanner catches a fake credential generated at run time, scanned the
    way the commit hook scans, and passes the clean file beside it

Every input is committed and pinned — the rules, the fixtures, the scanner versions —
so a tampered setup fails here visibly. What nothing here can do is force the checks
to run: `git commit --no-verify` walks past the hook, and nothing in this repository
blocks a merge. The output says so every time, whatever the verdict.

Stdlib only; shells out to the pinned scanners and reads their pins from
.pre-commit-config.yaml so there is one source of truth for versions.

Exit codes, house convention:
    0  everything verified
    1  a verification failed
    2  could not run — a scanner is missing (the output says what to install)
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ANSI = re.compile(r"\x1b\[[0-9;]*m")
ANNOTATION = re.compile(r"(?:#|//)\s*(ruleid|ok):\s*([A-Za-z0-9_-]+)")
RULE_ID = re.compile(r"^  - id:\s*(\S+)", re.M)
RULEID_FLOOR = 3
OK_FLOOR = 1

# The fake credential is assembled at run time so this file never contains a string a
# secret scanner would flag. The value is AWS's documented example access key.
CANARY = "AKIA" + "IOSFODNN7EXAMPLE"


def run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    try:
        proc = subprocess.run(  # nosec B603 - fixed argv, no shell, no user input
            cmd, cwd=cwd, capture_output=True, text=True, timeout=600
        )
    except FileNotFoundError:
        return -1, ""
    except (OSError, subprocess.SubprocessError) as exc:
        return -2, f"{type(exc).__name__}"
    return proc.returncode, ANSI.sub("", proc.stdout + proc.stderr)


def pinned_versions(root: Path) -> dict[str, str]:
    text = (root / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    return {
        name: m.group(1)
        for name, pattern in (
            ("semgrep", r"semgrep==([0-9.]+)"),
            ("detect-secrets", r"detect-secrets==([0-9.]+)"),
        )
        if (m := re.search(pattern, text))
    }


def inventory(root: Path) -> tuple[dict[str, dict[str, int]], list[str]]:
    """Per-rule ruleid/ok counts from the fixtures, plus any problems found."""
    problems: list[str] = []
    rules: dict[str, dict[str, int]] = {}
    for rule_file in sorted((root / "controls" / "rules").glob("*.yaml")):
        for rid in RULE_ID.findall(rule_file.read_text(encoding="utf-8")):
            rules[rid] = {"ruleid": 0, "ok": 0}
    if not rules:
        problems.append("no rules found under controls/rules/ — nothing to verify")
        return rules, problems

    for fixture in sorted((root / "controls" / "tests").iterdir()):
        if not fixture.is_file():
            continue
        for kind, rid in ANNOTATION.findall(fixture.read_text(encoding="utf-8")):
            if rid not in rules:
                problems.append(
                    f"{fixture.name} asserts '{rid}', which is not a rule in "
                    "controls/rules/ — a test for a check that does not exist"
                )
                continue
            rules[rid][kind] += 1

    for rid, counts in sorted(rules.items()):
        if counts["ruleid"] < RULEID_FLOOR:
            problems.append(
                f"{rid} has {counts['ruleid']} vulnerable test case(s); the floor is "
                f"{RULEID_FLOOR}. A rule this thinly tested can rot without anything "
                "noticing — add cases to controls/tests/"
            )
        if counts["ok"] < OK_FLOOR:
            problems.append(
                f"{rid} has no safe test case. A rule never shown a safe case could "
                "be flagging everything — add one to controls/tests/"
            )
    return rules, problems


def semgrep_suite(root: Path) -> tuple[int, str]:
    """One `semgrep --test` run; returns (exit code, its final summary line)."""
    code, out = run(
        ["semgrep", "--test", "--config", "controls/rules", "controls/tests"], root
    )
    if code < 0:
        return code, out
    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    summary = next(
        (ln for ln in reversed(lines) if re.match(r"^\d+/\d+", ln)),
        lines[-1] if lines else "no output",
    )
    return code, summary


def canary_scan(root: Path) -> tuple[str, str]:
    """Returns (verdict, detail): the scanner must flag the canary and pass a clean file."""
    if shutil.which("detect-secrets-hook") is None:
        return "missing", "detect-secrets-hook is not on PATH"
    with tempfile.TemporaryDirectory() as tmp:
        bad = Path(tmp) / "canary.txt"
        bad.write_text(f"aws_access_key_id = {CANARY}\n", encoding="utf-8")
        clean = Path(tmp) / "clean.txt"
        clean.write_text("nothing secret lives on this line\n", encoding="utf-8")
        bad_code, _ = run(["detect-secrets-hook", str(bad)], root)
        clean_code, _ = run(["detect-secrets-hook", str(clean)], root)
    if bad_code == 1 and clean_code == 0:
        return "pass", "flagged the fake credential, passed the clean file"
    if bad_code == 0:
        return "fail", "a known fake credential was NOT flagged — the scanner is not working"
    if clean_code != 0:
        return "fail", f"a clean file was flagged (exit {clean_code}) — the scanner is misfiring"
    return "fail", f"unexpected scanner exits (canary {bad_code}, clean {clean_code})"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", type=Path)
    parser.add_argument(
        "--no-install-check",
        action="store_true",
        help="skip the commit-hook check; for CI, where a checkout has no hooks",
    )
    args = parser.parse_args()
    root = args.repo_root.resolve()
    if not (root / "controls" / "rules").is_dir():
        print("FATAL: no controls/rules/ directory; is --repo-root correct?", file=sys.stderr)
        return 2

    failed: list[str] = []
    missing: list[str] = []
    pins = pinned_versions(root)
    out: list[str] = ["runwAI verification — do the security checks actually work?", ""]

    # -- rule receipts ---------------------------------------------------------
    rules, problems = inventory(root)
    total_bad = sum(c["ruleid"] for c in rules.values())
    total_ok = sum(c["ok"] for c in rules.values())

    if shutil.which("semgrep") is None:
        # `make setup` rather than a bare pip install: it installs the pin into .venv/,
        # which is the only form that works on a distro-managed Python. A remedy line that
        # fails when followed is worse than none — it teaches the reader the check is broken.
        missing.append(
            f"semgrep: make setup  (installs semgrep=={pins.get('semgrep', '<pinned>')}), "
            'then: export PATH="$PWD/.venv/bin:$PATH"'
        )
        out += ["Rule receipts:", "  COULD NOT RUN  semgrep is not installed", ""]
    else:
        version = run(["semgrep", "--version"], root)[1].strip().splitlines()[-1]
        first_code, first_summary = semgrep_suite(root)
        second_code, second_summary = semgrep_suite(root)
        suite_ok = first_code == 0
        deterministic = (first_code, first_summary) == (second_code, second_summary)

        out.append(f"Rule receipts (semgrep {version}):")
        if suite_ok:
            out.append(
                f"  PASS  every rule fired on its vulnerable cases and stayed silent "
                f"on the safe ones ({first_summary})"
            )
            out.append(
                f"        {len(rules)} rules, {total_bad} vulnerable cases, "
                f"{total_ok} safe cases:"
            )
            for rid, c in sorted(rules.items()):
                out.append(f"          {rid}: {c['ruleid']} vulnerable, {c['ok']} safe")
        else:
            failed.append("rule suite")
            out.append(
                f"  FAIL  a rule did not behave as asserted ({first_summary}). "
                "Run `semgrep --test --config controls/rules controls/tests` to see which."
            )
        if problems:
            failed.append("fixture floor")
            out.append("  FAIL  the fixtures are thinner than the rules claim:")
            out += [f"        - {p}" for p in problems]
        else:
            out.append(
                f"  PASS  every rule has at least {RULEID_FLOOR} vulnerable and "
                f"{OK_FLOOR} safe case(s) committed"
            )
        if deterministic:
            out.append("  PASS  a second run returned identical verdicts")
        else:
            failed.append("determinism")
            out.append(
                f"  FAIL  two runs disagreed ({first_summary!r} vs {second_summary!r}) "
                "— a check that changes its mind is not a control"
            )
        if pins.get("semgrep") and pins["semgrep"] not in version:
            out.append(
                f"  NOTE  semgrep {version} is running but the hook pins "
                f"{pins['semgrep']}; verdicts are only guaranteed for the pin"
            )
    out.append("")

    # -- secret-scan receipt ---------------------------------------------------
    verdict, detail = canary_scan(root)
    out.append("Secret-scan receipt (detect-secrets):")
    if verdict == "pass":
        out.append(f"  PASS  {detail}")
    elif verdict == "missing":
        missing.append(
            f"detect-secrets: make setup  (installs "
            f"detect-secrets=={pins.get('detect-secrets', '<pinned>')}), "
            'then: export PATH="$PWD/.venv/bin:$PATH"'
        )
        out.append(f"  COULD NOT RUN  {detail}")
    else:
        failed.append("secret scan")
        out.append(f"  FAIL  {detail}")
    out.append("")

    # -- the hook --------------------------------------------------------------
    if not args.no_install_check:
        out.append("Commit hook:")
        hook = root / ".git" / "hooks" / "pre-commit"
        if hook.is_file() and "pre-commit" in hook.read_text(encoding="utf-8", errors="replace"):
            out.append("  PASS  installed — the checks above run when you commit")
        else:
            failed.append("commit hook")
            out.append(
                "  FAIL  not installed — nothing will run when you commit.\n"
                "        Install it: make setup && make hook"
            )
        out.append("")

    # -- verdict and the honesty block -----------------------------------------
    if failed:
        out.append(f"VERIFICATION FAILED: {', '.join(failed)}. Details above, with fixes.")
        code = 1
    elif missing:
        out.append("COULD NOT VERIFY — install the missing scanner(s) and run this again:")
        out += [f"  {m}" for m in missing]
        code = 2
    else:
        out.append("All verification tests passed.")
        code = 0

    demonstrated = (
        f"  The {len(rules)} active rules and the secret scanner demonstrably catch the\n"
        "  cases they claim to. That is not broad coverage, and it does not mean the\n"
        "  code in this repository is secure — it means the checks work."
        if code == 0
        else "  A pass here would mean the checks demonstrably work on known cases —\n"
        "  never that the code is secure, and never broad coverage."
    )
    out += [
        "",
        "What that means — and what it does not:",
        demonstrated,
        "  Nothing forces them to run: `git commit --no-verify` walks past the hook,",
        "  and nothing in this repository can block a merge.",
        "  Every input to this verification is committed and pinned, so tampering",
        "  with a rule or a fixture changes this result visibly.",
    ]
    print("\n".join(out))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
