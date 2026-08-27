# contract: 01_docs/reports/

**Purpose** — durable, human-readable engineering investigations: issue
analysis, characterization summaries, option studies, postmortems and design
proposals that read cleanly in a text editor or on GitHub.

**Authority boundary** — a report explains and connects evidence. It does not
replace a part dossier, rule YAML, CAD source, gate receipt, ADR, release
manifest or physical measurement record. An accepted design choice is copied
into its owning source/ADR and independently regraded. A report cited by a
release is copied into that immutable release and hash-bound there.

## Allowed

| Pattern | What | Rule |
|---|---|---|
| `contracts.md` | this file | hand-edited only with the skill-owned template |
| `<date>-<slug>.md` | one dated Markdown report | filename remains strict `YYYY-MM-DD-<lower-kebab-slug>.md`; schema-1 frontmatter; report id equals filename stem; sections and evidence grades below |
| `assets/**` | report-specific PNG, JPEG, SVG or CSV evidence | immutable once cited; provenance and meaning stated in the report; no executables or opaque archives |

## Required frontmatter

```yaml
---
schema: 1
kind: pcb-human-report
report_id: YYYY-MM-DD-<slug>
title: Human title
subtitle: One-line scope
project: <project-folder-name>
date: YYYY-MM-DD
status: DRAFT | REVIEWED | SUPERSEDED
evidence_status: INCOMPLETE | MIXED | MEASURED
---
```

`date` must match the filename prefix. `REVIEWED` means the report was checked
as a faithful synthesis; it does not promote any design/readiness claim.
`MEASURED` is allowed only when every material conclusion is supported by
physical or instrument evidence. A proposal with outstanding measurements is
`INCOMPLETE`, even when its calculations are sound.

## Required report shape

1. `Executive conclusion` — the decision-relevant result first.
2. `Question and scope` — exact system boundary and excluded questions.
3. `Evidence boundary` — subject/release identities and what remains untested.
4. `Findings` — tables/figures with every material claim labelled:
   **MEASURED**, **DATASHEET**, **CITED**, **INFERRED**, **PROPOSED**, or
   **OWED**.
5. `Recommendations` — prioritized actions with benefit and tradeoff.
6. `Validation plan` — measurements that can falsify the conclusions.
7. `Source register` — primary sources and exact local evidence paths.

## Markdown rules

- Use ordinary GitHub-Flavored Markdown with relative links for repository
  evidence and HTTPS links for external primary sources.
- Prefer tables for matrices and comparisons. Put units in headings.
- Keep images project-local; do not hotlink an image whose bytes can change.
- Include alt text that states what the image proves or illustrates.
- Do not embed raw HTML, scripts, data URIs or generated binary copies.

## Forbidden

- Datasheet PDFs: retain them under the exact `02_parts/<MPN>/` dossier.
- Raw instrument data: keep it in the owning verification/evidence directory;
  the report links and summarizes it.
- Generated plots with no source/provenance.
- A report-only design requirement, waiver, release verdict or measured claim.
- PDF-only reports, duplicate rendered documents, remote image hotlinks and
  embedded HTML.

## Validate

- `python3 skills/pcb-design/scripts/project_report_audit.py <report.md>` from
  the repository root;
- filename, frontmatter `report_id`, `date` and project folder agree;
- every local Markdown link and image resolves to a tracked ordinary file;
- required sections and evidence vocabulary are present;
- `status: REVIEWED` never implies the product or proposal passed a gate;
- `evidence_status: MEASURED` has no material **PROPOSED** or **OWED** claim.

## Repair

- Broken link: point to the owning evidence; never copy it merely to silence a
  link check.
- Accepted proposal: update the owning source and ADR; do not silently treat
  report prose as implementation authority.
- Material new evidence: write a new dated report or explicitly supersede the
  old one; never overwrite historical measured evidence without a trace.
