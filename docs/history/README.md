# Historical PCB pipeline documents

These files are retained as dated context, not as instructions. They explain
the observations and proposals that shaped the current pipeline, including
claims that were later corrected or implemented.

For current work, start with the repository [`README.md`](../../README.md),
the [`pcb-design` skill](../../skills/pcb-design/SKILL.md), and its
[`execution graph`](../../skills/pcb-design/references/execution-graph.md).
Track unfinished work in [`improvements.md`](../../improvements.md).

## Retained documents

| Document | Historical role | Current authority |
|---|---|---|
| [`2026-07-30-resume-state.md`](2026-07-30-resume-state.md) | Snapshot of four concurrent agents and then-current board work | Git status/log and each active project's `01_docs/STATUS.md` |
| [`2026-08-02-fix-pcb-design.md`](2026-08-02-fix-pcb-design.md) | Parts and schematic workflow proposal | `skills/pcb-design/`, `skills/kicad-pcb/`, and executable gates |
| [`2026-08-02-routing-industry-plan.md`](2026-08-02-routing-industry-plan.md) | Routing remediation proposal | `skills/kicad-pcb/references/` and routing gates |
| [`2026-08-02-routing-investigation.md`](2026-08-02-routing-investigation.md) | Measurements and rationale behind routing work | `skills/kicad-pcb/references/routing-pipeline.md` and routed references |

Git history preserves earlier versions. References inside these documents to
their former root filenames, old project paths, or superseded commands are
historical evidence and must not be interpreted as current repository layout.
