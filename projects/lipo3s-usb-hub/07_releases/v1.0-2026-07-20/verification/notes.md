# Verification notes — lipo3s-usb-hub v1.0

## Build provenance (flagship claim)

Built by the ONE-COMMAND tscircuit-native pipeline
`bash ~/.claude/skills/kicad-pcb/scripts/tsx_to_board.sh lipo3s-usb-hub` from
`tscircuit/src/lipo3s_usb_hub.tsx` — NOT schwriter2/hand-KiCad. Gate chain (each printed
by the driver): tsci build → `circuit_json_to_kicad_sch` converter → sch export netlist →
ERC 0 → generate_board placement → audit PASS → generate_rules → import promoted KRT
route r5 → route_taps → stitch_and_fill → generate_rules LAST → DRC
`--severity-all --refill-zones --schematic-parity` **0/0/0** → board_netlist_parity **0**
(303 nodes / 56 nets) vs the sealed usb-power-3s. The build root (`tscircuit/tsx_build/`)
is throwaway; its `04_kicad/lipo3s_usb_hub.kicad_pcb` was promoted to `04_kicad/` as the
fab-of-record. Re-run reproduces byte-stable gates.

## jlc_twin (exit 0)

70 OK / 172 checked; all criticals adjudicated with evidence in
`03_src/rules/twin_adjudications.yaml` (PAD-GEOM on D_SMB diodes / CP_Elec e-caps /
ATO fuse, PAD-MISMATCH on the NexFET merged-drain + fuse clip pins, NO-CAD on the Sunlord
inductor). Every adjudication cites the datasheet-conforming land pattern and notes these
are the IDENTICAL footprints the reviewed/ordered usb-power-3s shipped (board parity 0), so
the twin's post-v1.3 PAD-GEOM gate is footprint-inherited, not a TSX-authoring artifact.
Report: `twin_report.txt`; 6 twin renders shipped here.

## Dispositions

- **U1 LM74800 exposed pad (pad 13) floats** — CORRECT and REQUIRED (datasheet: "Leave
  exposed pad floating. Do NOT connect to GND plane."). The `gen_tscircuit.sh` custom
  parity flags this EP as a converter-vs-board no-connect delta; it is benign — the
  authoritative KiCad `--schematic-parity` gate reported 0, and both our board and the
  sealed reference treat pad 13 identically (parity 0). Confirmed by the pin review.

- **USB-C 6 A vs USB4105 5 A VBUS rating** — the datasheet rates the four VBUS pins
  collectively at 5.0 A; the 6 A capability is ~20% over. Mitigation: advertised current
  is 3 A (dual 10k Rp — compliant sinks stay ≤3 A); 6 A is headroom for
  non-advertisement-limited loads, shared across 4 VBUS + 4 GND pads. Documented in
  ORDER_README + DETAIL_DESIGN as a derating consideration; sustained 6 A would want a
  higher-rated receptacle in a future spin.

- **PGOOD_A sequencing pull-up** — U3's EN is driven by U2's open-drain PGOOD_A; the
  required pull-up exists (R21 20k from 5V_C). Confirmed by pin review.

## First-order S-OCCL / silk

The converter `.kicad_sch` S-OCCL and the refdes/functional silk gaps are dispositioned in
`policy_audit.md` + `03_src/rules/policy_waivers.yaml` (architectural for S-OCCL; real
next-spin defects for silk, mitigated by the ORDER_README + assembly PDF + first-power
ritual).
