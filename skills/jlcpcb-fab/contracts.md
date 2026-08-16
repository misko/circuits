# contract: skills/jlcpcb-fab/

**Purpose** — the JLCPCB order skill: fab export, BOM/CPL, stock checks, and
the jlc_twin geometry verification against JLC's own CAD.

## Allowed

| Pattern | What |
|---|---|
| `SKILL.md` | the small JLC adapter kernel: scope, lifecycle boundaries, invariants, and direct reference router |
| `contracts.md` | this file |
| `scripts/` | export + verification tooling (own contract) |
| `references/` | vetted data the scripts consume (own contract) |

## Audit

- Same rules as `skills/kicad-pcb/`: checkers need known-bad tests
  (jlc_twin's FETCH-FAILED regression in `tests/t1_jlc_twin.py` is the
  motivating incident — it exited 0 on 11 unverified parts), and incident
  references name boards, never `projects/...` paths.
- Detailed assembly/order, digital-twin, and staging procedures live in their
  named references; the core must route to them directly rather than restating
  their authority.
