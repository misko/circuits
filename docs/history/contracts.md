# contract: docs/history/

**Purpose** — frozen, non-authoritative context retained to explain how the
current PCB pipeline evolved. Current commands, ownership, and status live in
the root README, owning skills, accepted ADRs, executable gates, and project
status beacons.

**Mutability** — historical bodies are immutable after relocation. Correct a
current procedure in its owning reference; do not revise history until it
appears current. A new historical document requires a dated filename, a
prominent non-authoritative banner, and an index entry.

## Allowed

| Pattern | What |
|---|---|
| `README.md` | history index and authority boundary |
| `2026-07-30-resume-state.md` | dated repository state snapshot |
| `2026-08-02-fix-pcb-design.md` | historical PCB workflow proposal |
| `2026-08-02-routing-industry-plan.md` | historical routing remediation proposal |
| `2026-08-02-routing-investigation.md` | historical routing measurements and rationale |
| `contracts.md` | this contract |

## Audit

- Every retained document is indexed by `README.md` with its original role
  and current authority owner.
- Every historical body begins with a prominent historical/non-authoritative
  banner.
- Internal statements about old filenames, locations, statuses, and commands
  remain evidence of the document as written; they are not forward guidance.
- Unresolved work is represented in root `improvements.md`, not inferred from
  this directory.
