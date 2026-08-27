# Project reports

Use a project report when the output is an investigation a person should read:
characterization, issue analysis, a design alternative study, failure review,
or a proposal that crosses electrical, mechanical and manufacturing domains.
Do not use it as another home for requirements or executable design facts.

## Workflow

1. Read the nearest `01_docs/reports/contracts.md`.
2. Name the report `YYYY-MM-DD-<slug>.md` and complete its strict frontmatter.
3. Lead with the conclusion. State the exact project/release or physical article
   being discussed and separate measured results from device data and inference.
4. Prefer primary sources. Link local release evidence by relative path and
   identify immutable releases by their full directory name.
5. Use tables for comparison or leakage/coupling matrices. Include units in
   headings, not in ambiguous prose.
6. End with a falsifiable validation plan and a source register.
7. Run `python3 skills/pcb-design/scripts/project_report_audit.py <report.md>`
   and inspect the rendered Markdown on GitHub or a compatible preview.
8. If the work changes the design, separately update its ADR/source and rerun
   the owning engineering gates.

## Evidence vocabulary

| Label | Meaning |
|---|---|
| **MEASURED** | Observed on identified physical hardware or an instrument; method and retained evidence named. |
| **DATASHEET** | Exact-part manufacturer specification under stated conditions. |
| **CITED** | Primary external source that is not the exact-part data sheet. |
| **INFERRED** | Engineering conclusion derived from identified evidence; assumptions stated. |
| **PROPOSED** | Candidate change, not yet accepted or realized. |
| **OWED** | Measurement/review required before a stronger claim. |

`REVIEWED` frontmatter grades the document synthesis, not the product. Keep
`evidence_status: INCOMPLETE` whenever an important recommendation still needs
prototype or first-article evidence.

## Source discipline

Link exact local releases, receipts and retained measurements. Link external
primary sources over HTTPS. A local image must be tracked and attributable; a
web image is a mutable dependency and is not embedded. Reports remain plain
Markdown so their reasoning and edits are visible in normal code review.
