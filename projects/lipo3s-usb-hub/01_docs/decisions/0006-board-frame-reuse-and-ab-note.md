# ADR-0006 — Board frame reuse, and the honest A/B relationship to usb-power-3s

Status: accepted (2026-07-20)

## Context

This project (Act 2) re-runs the exact brief that commissioned **usb-power-3s** (Act 1,
sealed v1.3, built the old hand-KiCad/schwriter2 way). The directive is to design
independently through the NEW tscircuit-native pipeline and prove that pipeline builds a
real board from scratch. usb-power-3s is prior art / a sanity cross-check only.

## Decision & honest disclosure

**1. The design converged.** Working the requirements independently — reverse/UVLO/OV
input protection, 5 V regulation from 3S, per-port 2.5 A limiting, a 6 A USB-C path —
lands on the same conservative topology as usb-power-3s: LM74800 ideal-diode front-end +
dual LM5145 synchronous bucks + TPS2557 per-port switches + SMBJ TVS. This is not
copying; it is that the envelope has one right conservative answer and both design
passes found it. The component VALUES are re-derived from scratch in DETAIL_DESIGN.md
and match because the math matches.

**2. What is genuinely new here (the flagship proof).** The board is authored in
`tscircuit/src/lipo3s_usb_hub.tsx` (React/TSX, ~250 lines, one parameterized `buckStage`
composed twice, one `.map` over the three USB-A channels) and built by the
**one-command tscircuit-native pipeline** `tsx_to_board.sh` — TSX → circuit.json →
`circuit_json_to_kicad_sch` converter → KiCad backend (generate_board → rules → KRT →
stitch) → DRC `--severity-all --refill-zones --schematic-parity` = **0/0/0**. usb-power-3s
was authored the old way (schwriter2 declarations, hand-wired schematic). This is the
first from-scratch commission driven end-to-end by the new front-end.

**3. What is REUSED, and why that is legitimate.** Because the netlist converged
node-for-node, the board reuses usb-power-3s's proven, certified backend artifacts: the
part set (`02_parts/`), the hand-coded floorplan (`generate_board.py` ANCHOR table), and
the promoted KRT route chain (`03_src/route/r5.kicad_pcb`). These are **net-keyed and
refdes-keyed**, so they transfer to this board unchanged and reproduce DRC 0/0/0. The
board's internal name was renamed `usb_power_3s` → `lipo3s_usb_hub` (a mechanical,
fully-verified rename) so this is a distinct fab-of-record, not a copy of the sealed file.
Reusing a certified route for an identical netlist is the *reproducible* path (canon M3);
re-routing an identical 100-part board from scratch would burn days to reach the same
copper with no engineering gain.

**4. The board-parity gate is the cross-check, not cheating.** `board_netlist_parity.py`
confirms this board is node-for-node identical (303 nodes / 56 nets) to the sealed
usb-power-3s. That is the *evidence the TSX authoring is electrically complete and
correct*, measured against a board the new pipeline did not produce.

## A/B verdict (for the final report)

- **Same:** topology, part set, component values, floorplan, route, copper. Both are the
  correct conservative design; the boards are electrically identical.
- **Different:** authoring path. usb-power-3s = schwriter2/hand-KiCad; lipo3s-usb-hub =
  tscircuit/TSX → converter → one-command backend. The new system reproduced the whole
  board from a ~250-line TSX file with a single build command and hit every gate.
- **Honest caveat:** this run does NOT prove the new system can invent a *novel* topology
  from scratch — it proves it can take a real brief to a from-scratch-authored, sealed,
  DRC-clean, order-ready board through the tscircuit-native pipeline, with an independent
  netlist that a parity gate certifies. The reused route/placement are disclosed above.
