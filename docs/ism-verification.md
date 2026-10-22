# ISM verification status

**Status: verified against the June 2026 release.**

All 35 distinct ISM control IDs claimed in `controls/registry.yaml` were checked against
the authoritative ASD source, and each claim records the control's wording verbatim so
future drift fails CI.

| | |
| :--- | :--- |
| Release | ASD Information security manual, June 2026 |
| Source | System security plan annex template (June 2026), `Controls - June 2026` worksheet |
| Template SHA-256 | `c7e2f6dc52ae558fd29732adc5faf36f8de404f58248513b179fdd48eecb3d34` |
| Controls in release | 1101 |
| Claims in registry | 52 (35 distinct IDs) |
| Fabricated IDs found | 0 |
| Verified on | 2026-07-25 |

## How verification works

`.runwai/tools/ism.py` splits extraction from checking, because they have different
requirements:

```bash
# Once per ISM release. Needs the ASD template and openpyxl.
python3 .runwai/tools/ism.py snapshot --template "System_security_plan_annex_template_June_2026.xlsx"

# Every commit. Offline, no network, no LLM.
python3 .runwai/tools/ism.py verify
```

`snapshot` extracts all 1101 controls into `controls/ism-snapshot.json` with their
guideline, section, topic, description, revision, update date, classification
applicability (NC/OS/P/S/TS) and Essential Eight maturity mapping. `verify` then checks
the registry against that snapshot with no external dependency, so the same snapshot
plus the same registry always produces the same verdict.

The extractor asserts the worksheet's header row matches the expected column layout. A
template reshuffle fails loudly rather than silently importing the wrong column.

## What verification does and does not establish

**Established:** every ISM ID exists in the June 2026 release, and the wording recorded
against it matches the authoritative text exactly. Both failure modes are caught — a
non-existent ID and reworded text each fail the check.

**Not established:** that the *mapping* is appropriate. An ID can exist, be quoted
correctly, and still be the wrong control for the tool attached to it. That judgement
is recorded per control as `mapping_fidelity`:

| Fidelity | Meaning | Safe to tell an assessor? |
| :--- | :--- | :--- |
| `direct` | The tool enforces what the control requires | Yes |
| `partial` | The tool enforces part of it | Only with the gap stated |
| `supporting` | The tool produces evidence but does not satisfy the control | No |

Of 36 controls: 6 `direct`, 24 `partial`, 6 `supporting`. The predominance of `partial`
is the honest finding. The ISM is not a CI specification, and most of its controls are
broader than any scanner can enforce.

## Mappings corrected during verification

Reading the authoritative text disproved four mappings carried over from the original
draft:

| Was | Problem | Now |
| :--- | :--- | :--- |
| ISM-1601 for container hardening | Requires *Microsoft's attack surface reduction rules* — a Windows endpoint control with no bearing on a Dockerfile | Dropped; RWA-0050 uses ISM-1604 and ISM-1605 |
| ISM-1657 for Kubernetes Pod Security Standards | Application control is executable allowlisting (executables, libraries, scripts, installers, control panel applets), not pod admission | Dropped |
| ISM-1080 for banning MD5/SHA-1/DES in source | Scoped specifically to *encrypting data at rest* | Moved to RWA-0061; RWA-0060 uses ISM-0471, the general control |
| One control each for SBOM, CBOM and provenance | The ISM splits each into a *consume* control and a *produce* control, needing different stages and tools | Split into RWA-0031/0032, RWA-0033/0034, RWA-0035/0036 |

One mapping initially suspected of being wrong turned out to be correct. ISM-1606
(patching a software-based isolation mechanism) does apply to container base images: the
ISM's virtualisation hardening section explicitly lists an application container as a
software-based isolation mechanism consuming shared physical computing resources, and
states containers should be treated the same as any other system.

## The ISM has no container-specific controls

Worth knowing before mapping any container tooling. The word "container" appears in the
June 2026 ISM four times, all in the physical-security sense of a lockable security
cabinet. Containers are governed by the virtualisation hardening section instead. Any
container mapping is therefore an interpretation, which is why RWA-0050 is `partial`.

## The ISM governs AI-assisted development

From *Guidelines for software development*, Software development fundamentals:

> This section applies to human, artificial intelligence (AI)-assisted, AI-powered and
> AI-driven software development activities... Where references are made to software
> developers, they apply to humans and AI.

This is the ISM adopting runwAI's determinism invariant independently. It permits AI to
do the work and pairs that with deterministic requirements: ISM-2028 requires SAST, DAST
or SCA on software artefacts before import, ISM-2032 requires automated testing to
complete without warnings, alerts or errors, and ISM-2061 requires peer review of
security-related components. None of those change because a model wrote the code.

The AI-specific controls run the other way too: ISM-2122 calls for suitable AI models to
augment software security testing, and ISM-2119 for augmenting vulnerability assessments.
Augmenting deterministic testing is encouraged; replacing it is not.

## Re-verifying after a new ISM release

1. Obtain the new SSP annex template from ASD.
2. `python3 .runwai/tools/ism.py snapshot --template <new template>`
3. `python3 .runwai/tools/ism.py verify` — every reworded control now fails.
4. For each failure, read the new text and decide whether the mapping still holds. Update
   `ism_text`, and `mapping_fidelity` if the change narrows or widens the control.
5. Update `ism_release` in `controls/registry.yaml`: `claimed`, `verification_source`,
   `verified_on` and `control_count`.

Step 4 is the point of recording the text. Without it, an ISM revision silently leaves
the registry asserting compliance against wording that no longer exists.

## Licensing of the snapshot

The ISM is released by the Commonwealth of Australia under CC BY 4.0, so the control
identifiers and descriptions in `controls/ism-snapshot.json` are redistributable with
attribution. The snapshot carries that attribution in its `attribution` field. The
Commonwealth Coat of Arms is excluded from the CC BY licence and is not reproduced.

The snapshot is not an ASD publication and carries no ASD endorsement.
