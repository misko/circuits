# 05 — Routing (KRT waves + taps + stitch) to DRC 0/0/0

Final state (2026-07-21): `kicad-cli pcb drc --severity-all --refill-zones
--schematic-parity` = **0 violations / 0 unconnected / 0 parity** on
`04_kicad/usb_hub_3s.kicad_pcb`. Chain promoted to
`03_src/route/final_chain.kicad_pcb` (= `06_build/route/r7.kicad_pcb`),
`route.final` set (canon M3).

## Shape of the solution

- 7 KRT waves (`gate, qfngate, emk, sense, dataa, datac, sig`) over a
  track-free generated board; all pour-fed power nets EXCLUDED from KRT
  (end-of-wave reconciliation rips pour-fed multi-pad nets it deems
  incomplete — observed destroying LX1+LG1 after a 13/13 route).
- 38 tap connections (joinpath / via_hop / plane) close everything KRT
  cannot attach: the J5 alphanumeric pad row (KRT cannot attach to A1..B12
  at all), QFN pour-pin drops, plane drops (via-in-pad POFV, advanced
  tier), and pour-island bonders.
- Stitch: dedupe(0.28)/normalize/micro/dangling/T-split, pad_rescue
  (GND→In1, VIN→In2 via-in-pad), fill, island_rescue, late dedupe +
  hole_to_hole, prune. Rules regenerated LAST (pcbnew saves clobber
  netclasses), then the .kicad_pro min_text_height 0.45 patch, then DRC.

## Acceptance criteria used at route time

`route` output is accepted when the only failed pads are J5's (taps close
those); any non-J5 failure is a placement/keepout defect, not a router
tuning problem.

## The last five DRC items and what actually fixed them

1. **LX1 U1.18 (the buck-boost BST-return pin) to the west pour.** The
   sense river (SNS_OUT_P/N, C25 at y71.5, PATH_G's x62.1 vertical wall,
   HG1/BST1 diagonals on B) walled every corridor on BOTH layers between
   y67.5 and y86. Zone fingers died by clearance-shaving (fill sliver <
   min width); free-route taps died by 0.005 mm margins. Fix: a reserved
   KRT keepout runway `[58.6,72.7]-[68.15,73.5]` plus tap
   `U1.18 -> Q6.3` (a same-net PAD target — no fill-void lottery at the
   endpoint). PATH_G rerouted around it fine.
2. **R14.1 (VIN sense top) plane drop.** CC2's B.Cu diagonal ran 0.27 mm
   under the pad — every via site failed, which is also why stitch
   pad_rescue silently skipped this pad. Fix: keepout box over the pad
   neighborhood + explicit plane tap to `[75.17,63.6]`.
3. **VBUSC pocket at J5 A4/B9.** CC/data tap stubs fence a 1.1 mm² fill
   pocket around the A4/B9 VBUS pads. Fix: bonder tap
   `J5.A4 -> [111.85,106.8]` threading the NPTH gap (scoped floor
   `j5_bond`, min 0.19, why-note records it carries only the A4/B9 pin
   share).
4. **VOUT_PDS rendezvous via dangling.** Both legs arrived on B.Cu so the
   shared via had no F-side copper. Fix: 0.6×0.6 F.Cu VOUT_PDS patch at
   the rendezvous.
5. **NPTH hole clearance (twice).** pcb_toolkit probed holes at track
   clearance (0.13) while the tier's min_hole_clearance is 0.2 — taps
   passed 0.14 mm from J5's alignment NPTHs and DRC rejected them. Fixed
   in `pcb_toolkit.collides` (hole probes now use max(clr, 0.2)).

Also fixed en route: `drop_dangling` stitch pass removed tracks between
its own sweeps and re-read the board in the same interpreter — the
intra-pass SWIG poisoning the driver's barrier cannot see. Rewritten to
fixpoint on a Python-side model, one removal batch at the end.

## Numbers

- Board: 110×90 mm, 4 layer (In1=GND, In2=VIN), advanced tier
  (0.25/0.15 POFV vias), 112 components.
- DRC trajectory: 648/41 → 6/4 → 0/3 → 2/2 → 7/0 → **0/0/0**.
- Taps: 38/38 routed; stitch gate clean; audit PASS
  (13 polarity / 22 proximity / 4 edge / 116 silk).
