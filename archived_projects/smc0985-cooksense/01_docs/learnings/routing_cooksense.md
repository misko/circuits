
## 2026-07-28 — v1.7 electrical revision: three failures worth a rule each

**1. A NEW ANCHOR IN A CLUSTER MOVES FLOATERS THAT NOBODY TOUCHED, AND
`route.yaml` NOTICES BEFORE YOU DO.** Adding eleven anchored 0402 pull-downs
into the AND-chain / latch cluster re-solved EIGHT unrelated floaters onto
different legalizer rings (C_AND1 5.946 mm, C_AND2 3.280, C_FAULTAND 3.280,
TP_FAULT 2.300, U_OSCLR 2.088, C_MR / U_STOPINV / U_CAND1 0.500 each). None of
them was edited. It surfaced only in the STITCH pass, as
`seed_stubs.stubs[44]: the stub placed for C_FAULTAND.1 does not reach the pin
pad` — because `route.yaml` pins that cap's two plane pads BY COORDINATE
(the task#21 M-REPRO fix). Root cause: the `near:` legalizer searches by
OCCUPANCY, so any new anchor changes the answer for every floater in the same
pocket.
- how to avoid: before a reroute, DIFF the regenerated placement against the
  previous sealed board for every ref `route.yaml` mentions by coordinate, and
  pin the ones that moved at their previous positions. It is ~20 lines of
  pcbnew and it is cheaper than a 35-minute route that dies at stitch.
- candidate-canon: yes — suggested check **P-DRIFT**: a placement-stage gate
  that fails when a ref named in `route.yaml`'s `reservations`/`seed_stubs`
  moved more than a threshold since the last sealed board.

**2. DELETING A PART LEAVES ITS COORDINATE-PINNED ROUTE ARTEFACTS BEHIND.**
ADR-0020 deletes `R_EXPRST`; `route.yaml` still carried a User.2 reservation
rect AND a deterministic seed-stub bond for `R_EXPRST.2`. `stitch` ERRORed
(`no footprint 'R_EXPRST'`) 30 minutes into the rebuild.
- how to avoid: a part deletion is a THREE-file change — tsx, manifest,
  floorplan — plus a `grep <REF> route.yaml`.
- candidate-canon: yes — the same **P-DRIFT** check should also fail on a
  `route.yaml` ref that no longer exists on the board.

**3. THE CONVERTER'S CROSS-NET GUARD CANNOT SEE A LABEL-ON-WIRE MERGE.**
`circuit_json_to_kicad_sch.py --mode layout` raises `LayoutFallback` when a
wire root joins two different PIN nets. It does NOT check whether a root
carries two different LABEL NAMES — and that is what merges at
`kicad-cli sch export netlist`. On this build tscircuit's schematic auto-layout
put the `3V3_ANALOG` global label at (275.59, 365.76) MID-SEGMENT on a `3V3`
wire (275.59, 401.32)-(275.59, 355.60); the converter dropped 3 segments,
declared success, and the exported netlist had 191 nets with no `3V3_ANALOG`
at all. `net_label_survival.py` caught it (161/162, LABEL-LOST). Shipping it
would have re-merged the analog rail into the digital one and silently undone
the v1.3 P1-1 fix.
- how to avoid: run `net_label_survival.py` at the SCHEMATIC gate, every time —
  it is seconds and it is the only gate that sees this class.
- candidate-canon: yes — PROPOSED PATCH to
  `skills/kicad-pcb/scripts/circuit_json_to_kicad_sch.py`: extend the
  short-detection block (~line 974) so that, alongside
  `root_pin_nets`, a root whose `root_label_names` set has >1 entry also raises
  `LayoutFallback`. That is the condition that actually merges nets at export,
  and with it this board would have auto-fallen back to `--mode grid` instead
  of needing a human to notice.
