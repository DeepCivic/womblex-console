# Security report

_Generated 2026-07-29 14:52 UTC by `.github/scripts/security_report.py`. Do not edit by hand._

**This is not a compliance claim, and must not be shown to an assessor as one.** It records which automated checks ran over this repository and what they found. The ISM governs a whole system — the people who run it, where it is hosted, who is allowed near it. A repository is a small part of that.

## What ran

| Control | What it covers | Where it runs |
| :--- | :--- | :--- |
| `RWA-0003` | SAST, DAST and SCA on software artefacts | pre-commit — `controls/rules/injection.yaml` |
| `RWA-0010` | Block secrets at commit time | pre-commit — its own config |
| `RWA-0020` | Input validation and output encoding | pre-commit — `controls/rules/injection.yaml` |
| `RWA-0021` | Parameterised queries, minimal database error disclosure | pre-commit — `controls/rules/injection.yaml` |
| `RWA-0022` | Validate before deserialising | pre-commit — `controls/rules/deserialisation.yaml` |
| `RWA-0027` | Path traversal and unsafe file operations | pre-commit — `controls/rules/path-traversal.yaml` |
| `RWA-0031` | Consume SBOMs of third-party components | posture — `.github/scripts/audit.py` |
| `RWA-0032` | Produce and publish an SBOM | posture — `.github/scripts/audit.py`, `docs/dependencies.md` |
| `RWA-0074` | AI model storage format and inference rate limiting | pre-commit — `controls/rules/deserialisation.yaml` |

Scanned: not recorded

## Findings

**No scanner output was supplied to this run.** This section reports nothing, which is not the same as nothing found. A report generated without its scanners is a coverage statement only.

## Dependency posture

No known vulnerabilities in 1 audited ecosystem (node), across 10 packages. That means no advisory was recorded against these versions in the database snapshot named below — not that the packages are safe.

**Not applicable:** dotnet, go, java, php, python, ruby, rust. No manifest for these was found, so they were not scanned and are not a pass.

Scanned with trivy 0.72.0 against a vulnerability database snapshot of 2026-07-29T13:35:00.267410209Z. The database is a pinned input rather than a live service, so the same lockfiles and the same snapshot always yield this same verdict — and when a verdict changes, the snapshot date says whether the code or the advisories moved. The bill of materials is `docs/dependencies.md`.

**A dependency audit reports and blocks nothing.** It is not on the commit hook: a CVE published overnight is not a reason a commit cannot be saved.

## Where this sits against the ISM

The June 2026 ISM has 1101 controls. This repository can say something about a small number of them.

| | Controls | What it means |
| :--- | ---: | :--- |
| Has a check behind it | 13 | A pinned tool in this repository is wired to this control |
| Mapped, nothing runs | 40 | Recorded as in scope, with no check behind it yet |
| Unassessed | 701 | Evidence could live in code or infrastructure. Nothing here looks at it |
| Out of scope | 347 | People, policy, premises and process. No repository can evidence these |

**A check being wired is not a check having run.** The first row counts controls with a mechanism attached, not controls verified on this commit. A check whose subject matter is absent — no Python or JavaScript in the tree for the rules to read — has not run, and reads identically here to one that ran and found nothing. The column below says where each would run.

**Nothing here prevents a merge.** The checks run on the developer's machine before a commit, where they are bypassable, and in CI afterwards, where they report. Enforcing that a red check stops a merge is branch protection — a setting on the repository itself, which no template can install for you.

**Unassessed is not the same as reachable.** A control whose evidence lives in deployed infrastructure — ISM-0260 requires all web access to pass through web proxies — sits in that row because it is not organisational, not because runwAI could check it. Reading that row as a to-do list would overstate what any repository-level tool can do.

### The controls that are checked

| ISM | Via | Where it runs | What the ISM asks for |
| :--- | :--- | :--- | :--- |
| `ISM-0402` | RWA-0003 | pre-commit | Software is comprehensively tested for vulnerabilities using SAST, DAST and SCA prior to its initial release, any subsequent release, and pe… |
| `ISM-1240` | RWA-0020, RWA-0027 | pre-commit | Validation and sanitisation are performed on all input received over the internet by software. |
| `ISM-1241` | RWA-0020 | pre-commit | Output encoding is performed on all output produced by web applications. |
| `ISM-1276` | RWA-0021 | pre-commit | Parameterised queries or stored procedures, instead of dynamically generated queries, are used by software for database interactions. |
| `ISM-1278` | RWA-0021 | pre-commit | Software is designed or configured to provide as little error information as possible about the structure of databases. |
| `ISM-1730` | RWA-0032 | posture | A software bill of materials is produced and made available to consumers of software. |
| `ISM-2016` | RWA-0027 | pre-commit | Validation and sanitisation are performed on all input received over a local network by software. |
| `ISM-2028` | RWA-0003 | pre-commit | All software artefacts are tested to detect known weaknesses using static application security testing (SAST), dynamic application security … |
| `ISM-2030` | RWA-0010 | pre-commit | Scanning is used during commits to identify plain text or encoded secrets and keys, which are then blocked from being stored in the authorit… |
| `ISM-2054` | RWA-0031 | posture | If a software bill of materials is available for imported third-party software components, it is used during software development to ensure … |
| `ISM-2058` | RWA-0022 | pre-commit | Data sources and serialised data inputs are validated before being deserialised. |
| `ISM-2072` | RWA-0074 | pre-commit | AI models are stored in a non-executable file format that does not allow arbitrary code execution. |
| `ISM-2090` | RWA-0074 | pre-commit | Rate limiting is applied to inference queries for AI models. |

### Mapped, but nothing runs yet

Recorded as in scope with no mechanism behind them. Listed rather than hidden, because a control that is silently absent looks identical to one that passed.

- `ISM-0400` (RWA-0005) — Development, testing, staging and production environments
- `ISM-0471` (RWA-0060) — Using cryptographic algorithms
- `ISM-0479` (RWA-0060) — Using symmetric cryptographic algorithms
- `ISM-1080` (RWA-0061) — Using cryptographic algorithms
- `ISM-1139` (RWA-0041) — Configuring Transport Layer Security
- `ISM-1181` (RWA-0040) — Network segmentation and segregation
- `ISM-1270` (RWA-0040) — Network environment
- `ISM-1272` (RWA-0040) — Network environment
- `ISM-1369` (RWA-0041) — Configuring Transport Layer Security
- `ISM-1402` (RWA-0012) — Protecting credentials
- `ISM-1422` (RWA-0001) — Authoritative source for software
- `ISM-1424` (RWA-0023) — Web security policy response headers
- `ISM-1453` (RWA-0041) — Configuring Transport Layer Security
- `ISM-1552` (RWA-0023) — Web application interactions
- `ISM-1604` (RWA-0050) — Functional separation between operating environments
- `ISM-1605` (RWA-0050) — Functional separation between operating environments
- `ISM-1606` (RWA-0051) — Functional separation between operating environments
- `ISM-1781` (RWA-0041) — Network encryption
- `ISM-1811` (RWA-0042) — Performing and retaining backups
- `ISM-1816` (RWA-0001) — Authoritative source for software
- `ISM-1848` (RWA-0051) — Functional separation between operating environments
- `ISM-1917` (RWA-0062) — Transitioning to post-quantum cryptography
- `ISM-1924` (RWA-0070) — Prompt injection
- `ISM-1990` (RWA-0062) — Using post-quantum cryptographic algorithms
- `ISM-2029` (RWA-0030) — Software artefacts
- `ISM-2032` (RWA-0002) — Build solution
- `ISM-2041` (RWA-0025) — Secure software development
- `ISM-2044` (RWA-0011) — Secure software development
- `ISM-2055` (RWA-0035) — Software build provenance
- `ISM-2056` (RWA-0036) — Software build provenance
- `ISM-2057` (RWA-0024) — Software input handling
- `ISM-2059` (RWA-0026) — Software input handling
- `ISM-2061` (RWA-0004) — Software security testing
- `ISM-2063` (RWA-0023) — Secure web application design and development
- `ISM-2073` (RWA-0062) — Transitioning to post-quantum cryptography
- `ISM-2082` (RWA-0033) — Cryptographic bill of materials
- `ISM-2083` (RWA-0034) — Cryptographic bill of materials
- `ISM-2085` (RWA-0072) — Secure artificial intelligence application development
- `ISM-2094` (RWA-0071) — Sensitive data exposure and improper output
- `ISM-2103` (RWA-0073) — Data collection, retention and use

---

Control text is © Commonwealth of Australia, released under CC BY 4.0. runwAI is not an ASD publication and carries no ASD endorsement.
