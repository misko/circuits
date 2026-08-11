subject: usb-hub-3s-v4 exact placed board a8404ae41e79
date: 2026-08-11
reviewer: Codex root, layout/thermal/power-integrity pass using exact pad coordinates and official TI/GCT layout sources
independence_limit: same task owns design and review; mechanical gates and direct pad-distance reconstruction are separate instruments, but external-human independence remains a declared process boundary
review_stage: pre-route
review_kind: layout
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
board_sha256: a8404ae41e79fb12a9428e40100be15e66aa58a752e795845e6920c0d083160b
design_rules_sha256: 44e0cf9caa8eb833647413b7f8af90907852b9fcee18efbc54081117af9e5cd6

# Pre-route layout review

## Verdict and construction

The exact track-free board is SOUND to proceed to routing. It measures 130 x
90 mm, has four copper layers, four M3 holes, three non-collinear global
fiducials and a 1.2 mm ENIG JLC advanced stack. Board-level via intent requires
resin filling and copper capping; each 0.30 mm exposed-land drill has a 4:1
nominal board-thickness aspect ratio. Two internal uninterrupted GND zones are
declared. These are manufacturing/layout contracts, not proof of filled routed
copper.

The advanced tier is justified by U3's 0.50 mm WQFN pitch and direct
filled/capped thermal-via fields, not by routing density or USB data. Ordinary
process would make the exposed-land via-in-pad/stencil result unnecessarily
risky.

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
P-PADSEP passes 335 copper pads, 52,952 inter-footprint pad pairs and 73,488
paste-to-foreign-copper pairs at the 0.09 mm advanced floor. Placement policy
passes all three applicable layout/precedent/adjacency rows; RF and critical
signal routing are explicitly not applicable because the board carries no USB
data.

No routed copper, current-density, neckdown, feedback-takeoff, thermal-spread,
zone-island or DRC conclusion is claimed here. Those are Stage 4/5 gates, so
the order verdict remains DO-NOT-ORDER.

design_verdict: SOUND
order_verdict: DO-NOT-ORDER
