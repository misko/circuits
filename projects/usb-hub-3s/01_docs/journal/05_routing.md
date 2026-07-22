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

## 2026-07-22 (v1.1) — start
- did: fresh KRT route over the re-floorplanned cell (v1.0 promoted chain retired); race 2
- result: run1: 0 violations, 7 opens = the tap-owned J5 nets (expected) BUT 4/33 taps FAILED (all long U1 pour-net pin runs: PCIN/PCON/VOUTI+VIO) + 3 zones_intersect (KiCad flags SAME-net same-priority overlaps - v1.0's P3-union precedent re-learned)
- next: reserve chip-pin tap lanes (v1.0 lesson re-learned the hard way), fix zone priorities

## 2026-07-22 (v1.1) — iterate 2
- did: restored/added 5 reserved lanes (U1.24->C46.1, U1.15 west lane+drop, both v1.0 west-col via sites for U1.10/12); retargeted VIN_S tap to C46.1 (the pour carries on from the cap pad); LX1 union rects -> priority 3; VIN strip P3 over pool
- result: run2: 0 violations, 8 opens = 6 tap-owned + VCC5V/VCCIO NEW (sig-wave starvation: east-col channel eaten by earlier waves + C20 body)
- next: promote VCC5V/VCCIO to the emk wave (routes 3rd), C20 east +0.9mm

## 2026-07-22 (v1.1) — iterate 3 (STUCK pattern named on taps)
- did: run3 route clean (0 viol, 6 tap-owned opens) but taps again 4/33 FAIL (U1.15/U1.10 long runs + BOTH LX1 spur legs). Measured the corridors: KRT HUGS lane edges (LG1 at y69.9, QG7 at y70.6 around a 0.55mm lane -> free channel 0.40 < 0.51 needed for a threaded 0.25 tap). Threading long chip-pin taps through the escape field is structurally fragile.
- result: diagnosis = these four are FIXED-GEOMETRY connections, not routing problems. Fix: deterministic seed stubs (03_src/add_seed_stubs.py, explicit segments+vias with collision-REFUSAL, like via_farms) + keepout corridors WITH crossing gaps (QG7 gate gap at x62.3-63.0, sense gap at x64.9-66.0) so KRT traffic crosses on the opposite layer of each emitted run
- next: emit stubs post-taps, re-route (4th), full chain to DRC

## 2026-07-22 (v1.1) — iterate 4 (post-back: placement, not lanes)
- did: run4 exposed the real cause - the NE escape corner hosted THREE gate parts whose nets cross every candidate stub path (R29's QG5 6.9mm detour, C22's LX pad far from LX copper, R31 pad order forcing QG7 across the spur). D-ADJ fix: R29 -> center alley (66.5,74.5) QG5 1.9mm; C22 -> ON the LX1 finger (BST1 is the routable side); R31 rot 270 (LG1 north / QG7 south, 1.8mm drop); R30/R17 shuffled west; LX1 finger extended [57.6,67.9,61.3,71.9] to absorb R17.1+C22.2. Seed stubs simplified to 3 runs; lanes re-sized per the w/2+0.28 hug rule with named crossing gaps (QG7, HG1, sense pair, C25 pad)
- result: regenerated board AUDIT PASS, 0 courtyard overlaps, all 8 pad orientations verified by measurement; route 5 in flight
- next: import -> taps -> seed stubs -> farms -> stitch -> DRC gate

## 2026-07-22 (v1.1) — tier-0/1 grind attempt (handoff: D-ADJ + re-route)
- did: grind_driver cycle 1 ran rebuild_all.sh (taps: 29/29 OK; seed_stubs: 0/3 refused collision). Escalation: clearance (127 quick-check zone-clearance findings on unfilled board). Root cause diagnosis: the promoted route (03_src/route/final_chain.kicad_pcb, timestamp 07:02) predates placement fixes from iterate 4 (timestamp 01:27→07:02, journal says "route 5 in flight"). Route does not carry the new crossing gaps (QG7 gate x62.3-63.0, sense x64.9-66.0) required for LX1 + VOUT_PDS/VOUT_PD stubs to thread. Detailed refusals: LX1 blocked by LG2 track, VOUT_PDS blocked by HG1, VOUT_PD blocked by SNS_OUT_N. These are NOT tap routing failures (taps succeeded); these are seed-stub placement failures caused by route geometry mismatch.
- result: DRC remains 19 violations / 88 unconnected (unfilled zones, GND plane fragmentation). Auto-fix mechanisms (zones_intersect_same_net, unconnected_zone_islands, tap_reattempt, seed_stubs) cannot proceed on a route that lacks the structural support for stubs. This is D-BACK material (placement decision rippled forward, route must regenerate).
- next: HANDOFF — needs Tier-2 frontier judgment to re-run KRT route with updated placement geometry (the gap definition and the parts now placed on the alley / finger extensions)

## 2026-07-22 — HANDOFF at routing gate
**State:** Tier-1 grind completed; escalation identified and root-caused. Placement changes from iterate 4 are stable (AUDIT PASS); route stale (predates D-ADJ changes). Auto-fixes cannot proceed.

**Escalation class:** zones_intersect (same-net priority bump) and unconnected_zone_islands blocked by route geometry that cannot accommodate seed stubs. Cannot fill → cannot heal islands.

**Next step (Tier-2):** KRT re-route with updated placement. Config to pass:
- 03_src/route.yaml: update keepout corridors to reflect new parts on center alley (R29), LX1 finger extension (C22/R17), and R31 rotation
- Run KRT with the new crossing gaps explicitly defined (QG7 gate gap x62.3-63.0, sense pair gap x64.9-66.0, HG1 gap)
- Import → taps → seed_stubs → via_farms → stitch → DRC
- Expected outcome: stubs place cleanly; zones heal; 0/0/0 gate

**Open hypotheses:** the new part placement may require fine-tuning of the gap boundaries; HG1 stub may also need a dedicated gap if gate crossing fails; tap reattempt will re-run with the new geometry if needed.

## 2026-07-22 — v1.1 SUPERSEDED BY SCOPE FINDING (stop routing)
- finding: USB-C output is 5V ONLY (user-confirmed 2026-07-22). Battery is
  9-12.6V, so Vout(5V) < Vin(min 9V) ALWAYS → step-down buck suffices. The
  IP6559 BUCK-BOOST (+ Q4-Q7 + 30V-FET/TVS coordination + compact hot-loop
  congestion + 16A input trunk) exists ONLY to support >5V PDOs (5-20V) that
  the spec never required. The congested PD cell blocking this routing grind
  is over-engineering, not a real constraint.
- decision: STOP finishing v1.1's buck-boost PD cell. The correct board is a
  5V-only v2.0: two step-down bucks (or one shared) + a simple 5V/5A PD source
  controller (still needed for the 5A/e-marker advertisement, NOT a boost).
  Input drops ~16A -> ~7A (55W total). Routes easily, cheaper, cooler.
- root-cause / harvest: D-SPEC pinned current ("5A compliant") but not the
  OUTPUT VOLTAGE RANGE; topology (buck vs buck-boost) was interpreted, not
  DERIVED from Vin-vs-Vout. New E-TOPO gate + power_tree.yaml in flight to
  make this a mechanical commission-stage check.
