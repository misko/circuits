# ADR-0007 — multi-board project structure (cooksense is 2 fabricated boards)

Status: accepted — 2026-07-22

## Context

`smc0985-cooksense` produces TWO independently-fabricated PCBs (ADR-0001):

- **cooksense** — the A+B-merged main board (rigid, 4-layer): sensing + the
  hardware safety AND-chain + the 12-relay keypad matrix + the Pi 40-pin
  header, with an internal keypad-isolation zone.
- **interposer** — Board C: the passive keypad interposer (flex / rigid-flex),
  coupon-gated (brief G1/G2 — physical connector measurement blocks its order).

(Board D `cook-loadcell` is REUSED — referenced, not re-cut. Board E, the
optional remote sensor, is deferred out of phase 1.)

Every pipeline stage contract in this repo is written for ONE board per project
— `04_kicad/<board>.kicad_pcb`, `03_tscircuit/src/<board>.tsx`, a single
`03_src/floorplan.yaml`, one `07_releases/<ver>/`. cooksense is the repo's
FIRST project with more than one fabricated board. Nothing in the contracts
forbids it, but the layout must be chosen so (a) the SHARED generic backend
— which already takes explicit config paths and `-o <board>` outputs — drives
each board unmodified, and (b) the per-`<board>` release + gate contracts apply
once per board.

## Decision

Treat each fabricated board as a **self-contained `<board>` build inside the
one shared project**. `01_docs/` and `02_parts/` are SHARED (the part library
is board-agnostic — a part.yaml is the same fact whichever board places it);
every board-specific stage artifact is scoped by a per-board subdirectory or a
`<board>` basename:

| Stage | cooksense | interposer | shared |
|---|---|---|---|
| 01_docs | — | — | ✓ brief, ADRs, ARCHITECTURE |
| 02_parts | — | — | ✓ one part library |
| 03_tscircuit/src | `cooksense.tsx` | `interposer.tsx` | contracts, package.json |
| 03_src | `03_src/cooksense/{floorplan.yaml, route.yaml, rules/, route/, audit_board.py, rebuild_all.sh}` | `03_src/interposer/{…}` | — |
| 04_kicad | `cooksense.kicad_{sch,pcb}` | `interposer.kicad_{sch,pcb}` | — |
| 06_build | `06_build/cooksense/` | `06_build/interposer/` | `cache/` |
| 07_releases | `cooksense-v<ver>-<date>/` | `interposer-v<ver>-<date>/` | — |
| 08_reviews | `…_cooksense_….md` | `…_interposer_….md` | — |

Each board's `03_src/<board>/rebuild_all.sh` drives the shared generics against
ITS subdir config and emits ITS `<board>` outputs. Boards fab and version
INDEPENDENTLY — rigid 4-layer vs flex is two fab processes, two tiers, two order
pages, two releases.

## Consequences

- **cooksense is the critical path** (dense, safety-relevant, fully buildable to
  orderable). **interposer** designs fully but is ORDER-blocked on the coupon
  gate (G1/G2, a bench step) — it is driven to that boundary, then parked.
- The generic backend needs NO change: it already takes explicit paths + `-o`.
  The per-board `rebuild_all.sh` is the only new wiring, one per board.
- **SKILL HARVEST candidate (not yet promoted — two-strike rule):** the template
  contracts in `skills/pcb-design/templates/contracts/` are single-board. If a
  SECOND multi-board project appears, promote this per-board-subdir convention
  into the templates (and teach `contracts_audit.py` the `<board>/` nesting).
  Flagged in the parts/verify journals; do not retro-edit the templates for a
  sample size of one.

## Alternatives rejected

- **Two separate projects** (`projects/cooksense-main`, `…-interposer`):
  duplicates `01_docs/`, the shared part library, and the system-level ADRs. The
  boards are ONE system with shared decisions; splitting the docs fractures the
  decision record that ADR-0001..0006 built. Rejected.
- **One physical board doing both jobs:** impossible — the interposer is a flex
  tail terminating at the OEM membrane connector; the main board is a rigid Pi
  HAT. Different substrates (ADR-0001). Rejected.
- **Board-prefixed flat files** (`03_src/rules/cooksense_nets.yaml`): works, but
  scatters two boards' configs in one directory and forces every downstream path
  to carry the prefix. Per-board subdirs isolate cleanly and let each board keep
  the STANDARD single-board filenames the backend and contracts already expect.
  Rejected in favour of subdirs.
