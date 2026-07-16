# PROGRESS — xt60-usb-supply

Clean-room rerun on branch `rerun-independent`. Board: 3S LiPo XT60 in,
3x USB-A (2.5 A) + 1x USB-C (6 A) out. This file is the resume point.

## Pipeline state

| Stage | State | Evidence |
|---|---|---|
| 0. Worktree + template copy | DONE | projects/xt60-usb-supply/ |
| 1. BRIEF.md (commission, hash, assumptions) | DONE | 01_docs/BRIEF.md |
| 2. Part research (JLC stock) | IN PROGRESS | background agent |
| 3. ADRs + ARCHITECTURE + DETAIL_DESIGN | todo | |
| 4. 02_parts/ part.yaml + datasheets | todo | |
| 5. rules/nets.yaml + generate_rules.py | todo | BEFORE routing |
| 6. generate_schematic.py + netlist | todo | |
| 7. generate_board.py (placement, zones, audit) | todo | |
| 8. Routing (KRT, fanout-first, hardest-first) | todo | |
| 9. DRC gate 0/0/0 (kicad-cli --severity-all --refill-zones --schematic-parity) | todo | |
| 10. JLC export + stock check + twin + pin review | todo | |
| 11. Release dir + MANIFEST | todo | |

## Key decisions so far (see decision register in BRIEF.md)

- Two independent 5 V bucks: rail 5V_A (8 A, three USB-A) + 5V_C (6 A, USB-C).
- USB-C: 5 V fixed, Rp 10k advertisement (3 A legal max), copper/connector sized 6 A.
- USB-A: BC1.2 DCP (D+ shorted D-).
- Input: fuse -> reverse-polarity P-FET -> TVS -> bucks.
- 4-layer board (In1 = GND plane).

## Gotchas already loaded (from skills; do not rediscover)

- rules generator runs LAST in rebuild chain (pcbnew saves clobber .kicad_pro netclasses).
- KRT only on track-free unfilled boards; import once into fresh base.
- XT60PW footprint pad 1 = "-" blade. Audit all 2-pad polarized parts.
- Missing footprint = hard error; parse-yields-zero = error.
- dru width compares exact nanometers.
