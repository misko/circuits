subject: usb-hub-3s-v4 exact placed board 0245323bcef5
date: 2026-08-11
reviewer: Codex root, layout/thermal/power-integrity pass using exact pad coordinates and official TI/GCT layout sources
independence_limit: same task owns design and review; mechanical gates and direct pad-distance reconstruction are separate instruments, but external-human independence remains a declared process boundary
review_stage: pre-route
review_kind: layout
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
board_sha256: 0245323bcef57d6d4327ae8ce5b545bee50512851d02c08ed59ac8ace8707137
design_rules_sha256: d527db4303161f3501ebcdcff57e3314318bf79599a4915bec429f4cd0d887dd

# Pre-route layout review

## Verdict and construction

The exact track-free board is SOUND to proceed to routing. It measures 130 x
90 mm, has four copper layers, four M3 holes, three non-collinear global
fiducials and a 1.2 mm ENIG JLC advanced stack. Board-level via intent requires
resin filling and copper capping. U1/U2 contribute sixteen 0.30 mm drills at
4:1 nominal aspect ratio; U3/U4-U6 contribute twenty-four 0.20 mm drills at
6:1. All 40 are true board vias, not footprint PTH holes. Two internal
uninterrupted GND zones are declared. These are manufacturing/layout contracts,
not proof of filled routed copper.

Stage 4 regenerated the placement with bounded launch-rule areas, explicit
power islands and validated simple zone polygons. TP1, TP3 and TP4 moved onto
their VIN, 5VC_RAW and VBUSC copper respectively; TP2 remains on the 5VA
back-plane island. In-memory refill confirms those four test lands are inside
their intended copper. All measured critical component adjacencies remain
unchanged; the new exact board/rule hashes bind them.

The pre-route full-severity DRC found and closed the top J2/H2/FID2 courtyard
collision, two silk contacts, 24 drill-floor contradictions, five library
resolution warnings and J5's 0.1944 mm locator-hole corner. H2 now clears J2
by 0.10 mm in x, FID2 is unobstructed, and J5's exact relieved corner exceeds
the project 0.25 mm hole-clearance floor. The earlier self-intersecting VIN
polygon was rejected by the new simple-polygon gate and replaced by a simple
outline that fills across the protected input cell. Only seven unbonded
power-zone islands remain before the explicit tap stage; no other violation
class and no schematic-parity finding remains.

The advanced tier is justified by U3's 0.50 mm WQFN pitch and direct
filled/capped thermal-via fields, not by routing density or USB data. Ordinary
process would make the exposed-land via-in-pad/stencil result unnecessarily
risky.

The post-tap cheap check also measured the two auxiliary module launches. U1.5
can drop immediately to a collision-clear 1.0 mm B.Cu branch; U2.5 is boxed in
by its adjacent 0.50 mm-pitch lands and therefore retains a 0.30 mm, 2.60 mm
F.Cu branch wholly inside its named scoped rule area before joining the
5VC_RAW pour. Neither is treated as the rail's trunk conductor.

U5/U6 output-pad escapes are likewise explicit source geometry: each affected
2 A port uses two parallel 0.50/0.20 mm filled/capped via-in-pad drops and
0.8 mm B.Cu joins from pins 6/7 into its port plane. Seeding them before KRT
prevents control traces from consuming the only inter-layer path.

## Measured critical adjacency

- U1 TPSM63610: both VIN capacitor lands are 2.35/2.36 mm from the matching VIN
  lands; BOOT resistor ends are 2.69/2.70 mm from their pins; RT is 1.99 mm;
  SPSP is 2.71 mm; the high feedback leg is 2.06 mm from FB and the low leg is
  3.85 mm. The output capacitor bank is on the physical VOUT side. These
  replace the first legal-but-electrically-poor arrangement found by render and
  pad-coordinate review.
- U2 TPSM63604: both VIN bypass lands are 1.60 mm from their matching VIN
  lands; BOOT ends are 2.49 mm; RT is 2.07 mm; feedback legs are 3.10/3.45 mm.
  The three 47 uF `5VC_RAW` capacitors form the bridge from U2's VOUT side into
  the U3 input side.
- U3 TPS25810: the nearest 47 uF bank land is 3.70 mm from an input land and
  the 100 nF bypass is 2.75 mm away. The 100 k 0.1% REF resistor is symmetric
  at 2.81 mm from both REF and REF_RTN and lies inside the quiet reference
  keepout. The output bulk capacitor is on the VBUS side.
- J5/D6: connector-to-clamp distances are exactly 2.657 mm on both CC1 and CC2.
  The paths are therefore symmetric at placement and reach the clamp before
  U3. Actual routed length/ground-via quality remains a Stage 4 obligation.
- U4-U6 repeated USB-A switches: input bypass is 2.10 mm, ILIM 3.40 mm and
  output bulk 3.86 mm from the corresponding switch land in each cell. The
  passive receptacle body forces each D2-D4 clamp just below its connector
  courtyard; connector-to-clamp D+/D- spans are about 8-10 mm and still precede
  the local signature controller. They are charging-identification nets, not
  high-speed USB routes.

## Feasibility gates

Placement gates pass with the tightest pad-to-outline margin 2.03 mm at J5.SH,
worst cut demand 6 nets versus capacity 200 tracks, and zero courtyard/body or
envelope-to-foreign-pad findings across all 76 assembled components.
P-PADSEP passes 295 component copper pads and 41,136 inter-footprint pad pairs
at the 0.09 mm advanced floor; the 40 thermal primitives are correctly counted
as vias instead of package pads. Placement policy passes all three applicable
layout/precedent/adjacency rows; RF and critical signal routing are explicitly
not applicable because the board carries no USB data.

No routed copper, current-density, neckdown, feedback-takeoff, thermal-spread,
zone-island or DRC conclusion is claimed here. Those are Stage 4/5 gates, so
the order verdict remains DO-NOT-ORDER.

design_verdict: SOUND
order_verdict: DO-NOT-ORDER
