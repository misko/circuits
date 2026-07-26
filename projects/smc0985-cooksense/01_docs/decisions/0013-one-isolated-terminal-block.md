# ADR-0013 — ONE isolated terminal block (J_ISOLOOP), not two

status: accepted
date: 2026-07-25
tags: isolation, safety, placement, connectors, bom

## Context

v1.3 opened with a correct fix and closed it with a worse defect.

The correct fix (P0-2, layout/topology lens): until v1.3 the opto-isolated
30 V contactor loop shared J_ESTOP's 1.25 mm-pitch JST-GH housing with
ESTOP_RAW — isolated secondary and SELV on **adjacent pads, 0.650 mm apart, in
one field harness**. One damaged or contaminated harness was a common-cause
failure straight across the LTV-817S barrier. So the loop was moved off J_ESTOP
onto its own 3.5 mm-pitch KF350 screw terminal, `J_ESTOPLOOP`, beside the
existing 2-pole `J_CONTACTOR`.

The defect that created (P0-A): that made **five** connectors on the east edge,
and the east edge does not hold five. The anchors were written anyway and
`J_ESTOPLOOP [196,84,90]` landed **inside** `J_DOOR [197,84,90]` — 1.300 x
0.600 mm of overlapping pad copper, shorting CONTACTOR_C / CONTACTOR_LOOP to
3V3, GND and DOOR_RAW. The connector added to fix the isolation defect built a
strictly worse version of it. (Caught by the new P-COLLIDE generator gate,
canon P11, and independently by `kicad-cli` DRC as 6 `shorting_items`.)

The east-edge budget is arithmetic, not taste. Measured on the built
footprints, the usable column runs from H4's courtyard bottom (54.547) to the
south board edge (102.000) — 47.453 mm. Five connectors need 47.750 mm of
courtyard **plus** the courtyard gap that buys the `ISO_CONTACTOR` rule's
2.0 mm copper moat. There is no ordering of five bodies that fits, so this was
never a placement bug to nudge; it was an interface decision.

Three options were put up. Two were rejected by the user: moving a SELV
connector off the east edge (it changes which enclosure face a harness exits),
and growing the board (the enclosure had just been settled at ~195 x 92 mm).

## Decision

**Merge `J_ESTOPLOOP` and `J_CONTACTOR` into ONE 4-pole isolated terminal
block, `J_ISOLOOP` (KF350-3.5-4P, C42400616).** (User decision, 2026-07-25.)

```
  pole 1  LOOP_OUT   CONTACTOR_C      opto collector  -> E-stop pole B in
  pole 2  LOOP_RET   CONTACTOR_LOOP   E-stop pole B out
  pole 3  CTR_A      CONTACTOR_LOOP   -> contactor circuit
  pole 4  CTR_B      CONTACTOR_E      contactor circuit return -> opto emitter
```

**Why merging is isolation-NEUTRAL OR BETTER, which is the whole argument.**
Both connectors already carried **only** isolated-domain nets — there was never
a SELV pole on either one. Combining them therefore removes nothing from the
barrier and adds nothing across it. What it does change is how many boundaries
have to be defended: one isolated body with **one** 2.0 mm moat and **one** pour
keepout, instead of two adjacent bodies each needing their own, with a SELV
housing (J_DOOR) still in the column. Fewer boundaries is fewer places to get it
wrong, and the moat is the thing v1.2 measured at 0.199 mm.

Two secondary consequences, both good:

- **Field wiring improves.** The whole isolated loop lands on one block, so an
  installer never has to know that two adjacent housings are the same circuit.
- **Poles 2 and 3 are deliberately two screws on one net**, not one screw with
  two wires landed in it. On a safety interlock a single loosening screw must
  not be able to drop both the E-stop return *and* the contactor feed. This is
  asserted (`electrical_invariants.yaml`, `J_ISOLOOP.3 -> CONTACTOR_LOOP`) so a
  future re-pin cannot silently turn the interlock into a permanent closed loop.

3.5 mm pitch is retained: it holds connector-level creepage on the isolated
side at 3.5 mm nominal, against the 0.650 mm it had inside J_ESTOP's GH housing.

## Consequences

**The column is at capacity and the four anchors are SOLVED, not chosen.** The
packing is one-dimensional, so connector order cannot change the answer:

```
    H4 courtyard bottom                            54.547
  + J_MODE / J_ESTOP / J_DOOR courtyards         3 x 10.790
  - (J_DOOR courtyard sits 0.545 south of its GND shell tab)     -0.545
  + ISO_CONTACTOR moat                             2.000
  + J_ISOLOOP pad column (2 x 5.25 + pad dia)     12.700
  + copper-to-board-edge (board rule)              0.300
  ------------------------------------------------------
                                                 101.372   vs the edge at 102.000
```

0.628 mm of aggregate slack, to be spent across five margins at once.

That 0.628 exists only because the **KF350-3.5-4P footprint uses a 2.20 mm pad,
not the 2P's 2.60 mm** (annular ring 0.50 mm against JLCPCB's 0.15 mm THT
floor). At 2.60 the same solve lands at ~0.05 mm on *every* margin
simultaneously — a number nobody can defend on a mains-adjacent interlock. The
pad is the only lever on this board that costs nothing external, and it also
raises pole-to-pole copper gap from 0.90 to 1.30 mm, which on a 30 V isolated
block is the right direction. A predecessor solve that kept the 2.60 pad reached
0.028 mm aggregate slack and still measured **1.702 mm** on the moat.

The moat is **2-D, not vertical**. J_DOOR's binding copper is its east GND shell
tab (pad `MP`, x[197.0,199.7]), not its signal pads, which sit at
x[194.3,196.0] and are 4.1 mm clear. J_ISOLOOP is therefore pulled 1.70 mm west
of the SELV column so its pad column x[194.20,196.40] clears the tab in x and
buys the rest back diagonally. West is bounded by J_RH_EXHAUST's courtyard.

MEASURED margins at the accepted anchors (J_MODE 60.00, J_ESTOP 70.88,
J_DOOR 81.76 — all rot 90 at x197.0 — and J_ISOLOOP [195.30, 95.00, 90]):

| constraint | rule | measured | margin |
|---|---|---|---|
| H4 courtyard -> J_MODE courtyard | no overlap | 0.058 | +0.058 (H4 is the wall) |
| J_MODE -> J_ESTOP courtyard | no overlap | 0.090 | +0.090 |
| J_ESTOP -> J_DOOR courtyard | no overlap | 0.090 | +0.090 |
| J_DOOR -> J_ISOLOOP courtyard | no overlap | 0.500 | +0.500 |
| J_ISOLOOP -> J_RH_EXHAUST courtyard | no overlap | 0.160 | +0.160 |
| J_ISOLOOP.4 -> J_DOOR.MP[GND] copper | 2.000 (`opto_isolation_2mm`) | 2.126 | +0.126 |
| J_ISOLOOP.1 copper -> south board edge | 0.300 | 0.650 | +0.350 |
| J_ISOLOOP body south face | must not overhang | 102.000 | flush |

**J_MODE does not move at all** (H4's courtyard is a hard wall 0.058 mm north of
it); J_ESTOP moves north 1.12 mm and J_DOOR north 2.24 mm. Anything that grows
in this column — a bigger connector, a wider courtyard, H4 moving south — takes
the moat below 2.0 mm, and the `opto_isolation_2mm` DRU rule will say so.

**The pour keepout that could not be written before.** The moat has to be pour
GEOMETRY, not just a rule: a pour fills to its own clearance (0.200 mm) and
would sit 0.2 mm from isolated pads no matter what the DRU says — v1.2 measured
82 violations, worst 0.199 mm. `iso_moat_block` and `iso_moat_opto`
(`floorplan.yaml`) are the 2.0 mm outward offset of the isolated copper, denying
pours on all four layers, with the matching User.2 rects in `route.yaml` keeping
SELV *tracks* out (the `iso` wave runs on User.4 so it is never blocked by its
own moat). The block rect's north edge, 86.65, is the tight one: it is exactly
J_ISOLOOP.4's pad top minus 2.0 mm, and J_DOOR's south GND shell tab ends at
86.61 — so the pour still reaches and bonds that tab, with 0.04 mm to spare.

**BOM / assembly.** 223 components -> 222. J_ISOLOOP is THT and JLCPCB stocks no
KF350 4P line (measured stockCount 0 on C42400616 / C9900026363 / C9900148443,
2026-07-25; control query C474892 = 9987 the same minute), so it is declared
`not_assembled: not_in_catalog` and hand-soldered — the 14th such part after
J_TC and the twelve Standex relays. The same audit found J_LOADCELL and J_PI had
been CPL placement rows on v1.0 and v1.1 despite being pure THT on an SMT-only
order (measured: 5/5 and 40/40 plated drilled pads, F.Paste on none); they are
now declared `process_incompatible`.

**Silk.** There is no silk site at the block, and that is measured, not assumed:
scanning for a free F.SilkS box against pads, existing silk and every courtyard
(silk under a body is silk nobody reads) puts the nearest visible site for
"ISOLATED 30V" 41.9 mm away. The SE corner is saturated. The warning therefore
goes in the north safety-caption stack beside the ADR-0012 enclosure lines, and
names the corner so a reader can find the block; the pole legend lives in the
ORDER_README. Two captions placed at the block first were pushed clean off the
south edge by the nudge search (y104.19-106.31) — worse than nothing, because
they print nowhere and still count as done.

## Alternatives rejected

- **Move a SELV connector (J_DOOR or J_MODE) off the east edge.** Rejected by
  the user: it changes which enclosure face that harness exits.
- **Grow the board.** Rejected: the enclosure had just been settled at ~195 x 92.
- **Keep the 2.60 mm pad and squeeze.** Measured: 0.028 mm aggregate slack,
  courtyards butted at ~0.01 mm, and the moat still short at 1.702 mm.
- **Slide J_RH_EXHAUST west to widen the diagonal.** It would work (each 1.0 mm
  west buys ~0.44 mm of budget) but it moves an external interface on the south
  face to buy margin the pad change buys for free.
