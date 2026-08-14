review_kind: redteam_layout
subject: Pluto RX2 8-Way v5 corrected exact routed and fenced final layout dae8320d
date: 2026-08-13
reviewer: redteam-agent (Codex GPT-5 layout, power-integrity, manufacturability lens)
independence: independent-from-design-author
context-given: exact corrected board plus current RF, power, assembly, route and manufacturing rules
source_commit: dae8320d3a5bab507a5846c7886ea719dc05ef61
board_sha256: 39251c24d4b3cc878824f26c48178cbc4a4d418fa528045c6c13f2308e017acd
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
p0_design_findings: 0
p1_design_findings: 0
p2_design_findings: 0
p1_order_controls: 1

# Corrected exact-artifact adversarial final layout review

## Verdict and exact boundary

The corrected saved board is **SOUND**. I found no P0, P1 or P2 layout,
connectivity, RF-return, power-integrity, thermal, via-process, mechanical or
manufacturability design defect. This is a fresh examination of the exact
artifact above, not an inference from the earlier board or its review.

The order verdict is **DO-NOT-ORDER**. One P1 order/process control remains in
this lens: J2-J10 are paste-free THT parts, while the current assembly source
states a conditional wave/controlled-hand-solder intention only as advisory
text. The final release must declare the selected THT process, refs and
evidence in the machine-readable form consumed by the assembly gate. Final
Gerber/drill, controlled-impedance, selective-via-process, JLC uploader/DFM,
assembly-preview and first-article evidence remain owned by their later gates.

## Fresh exact-board checks

- KiCad 10.0.4 DRC with zone refill and schematic parity reports zero
  violations, zero unconnected items and zero parity discrepancies. The saved
  board contains 242 tracks and 638 vias, with no zero-length or exact-
  duplicate segment, no coincident via site and no disconnected signal via.
  All 13 non-GND vias have copper attached on both used outer layers.
- Separate-footprint landability passes over 167 copper pads, 12,971 inter-
  footprint pad pairs and 17,058 paste-to-foreign-copper pairs at the declared
  0.09 mm manufacturing floor. All 29/29 fitted footprints resolve a native
  renderer body.
- Tier preflight is green for `jlc_4layer_advanced` with 0 FAIL and 0 WARN.
  The 1.6 mm board gives 8:1 aspect ratio for ordinary 0.20 mm drills and
  6.4:1 for the protected 0.25 mm drill family, both inside the declared 10:1
  ceiling.

## Connectivity, routing and hidden DRC-clean failure search

- RF_COMMON and RF_ANT1-RF_ANT8 are each a single 0.295 mm F.Cu route with no
  layer change or via. Fresh copper inspection found no branch, stub,
  crossover, hidden loop or stochastic meander. Length matching between
  independently selected antennas is explicitly not a requirement; the
  applicable length-match audit therefore grades zero declared groups rather
  than silently awarding a pass.
- VBUS_RAW and VBUS_PROTECTED use 0.30 mm F.Cu copper; 3V3 uses 0.25 mm F.Cu.
  The design contract is only 100 mA input hold and 20 mA 3V3 load, so the
  widths and lack of power layer changes have ample margin. Low-speed control,
  CC and SWD copper is 0.18 mm and only NRST, SWDIO and SW_V2-SW_V4 use short
  B.Cu fragments.
- A final-chain-to-current-board via-in-pad guard finds zero newly introduced
  vias inside SMD lands. A more conservative drilled-hole/SMD-shape and
  annulus/SMD intersection census finds exactly the same nine deliberate U1
  sites and no other intersection, including none at corrected J11.3.

## RF return, planes, coupling and congestion

- In1.Cu and In2.Cu each contain one continuous filled GND polygon and no
  signal track. F.Cu's eight smaller filled islands and main island all have a
  local GND via or plated ground termination; there is no floating copper
  island. B.Cu also remains one connected filled polygon.
- The exact route-aware fence passes all 18 RF flanks, with 1.3979 mm worst
  aperture against the 1.4000 mm contract. U1's alternating perimeter grounds
  feed pad 25 and its 3x3 protected via field; every SMA has its four plated
  ground posts. No digital route cuts the In1 return plane.
- The radial RF arms diverge cleanly. No avoidable long parallel aggressor,
  digital crossover, RF layer transition, fence incursion into the controlled
  gap, or mounting-hole/connector choke point was found.

## Via process, power integrity and thermal review

- The saved-board census is complete: 638 vias total. Exactly nine U1 exposed-
  pad GND vias are the protected 0.45/0.25 mm family and each is filled and
  capped; the other 629 routing, stitching, fence and return vias are ordinary
  0.45/0.20 mm holes and are neither filled nor capped. No protected geometry
  is partial or shared with the ordinary family.
- A fresh Excellon export preserves the selector: 629 plated 0.20 mm holes,
  nine plated 0.25 mm holes, four 0.60 mm plated slots, nine 1.50 mm plated
  holes, 36 1.70 mm plated holes, two 0.65 mm NPTH holes and four 3.20 mm NPTH
  mounting holes. This proves drill-family separability; only the later exact-
  fab review and uploader echo can prove that JLC accepted selective fill/cap.
- U3 worst-case dissipation is 44.825 mW against the adopted 238 mW ceiling.
  The local input/output bypass centres are 1.875 mm from U3; U1's 100 nF is
  1.22 mm from its supply, and U2's 100 nF is 2.403 mm from VDD. Each local
  return has a nearby GND via, and U1 pad 25 has nine direct protected drops.
  No power-path via, narrow high-current neck or thermal bottleneck was found.

## Mechanical and production observations

- The 90 x 65 mm outline, four 3.2 mm corner holes, nine outward-facing SMA
  interfaces, south-edge USB-C connector, keyed vertical J11, and three top
  fiducials remain accessible and collision-free in fresh native renders.
- J2-J10 use ordinary through-hole tails and therefore require a declared
  wave/selective/hand-solder flow, adequate underside clearance, and first-
  article fillet inspection. This is the P1 order control above, not a need to
  alter the reviewed pad pattern or board geometry.
- The 0.5 mm-pitch U1 QFN and its Type-VII via-in-pad field require the
  explicit JLC advanced-process order, controlled-impedance stack selection,
  assembly preview and first-article inspection already assigned to the fab
  and order gates.

No hidden DRC-clean connectivity, return-path, coupling, plane, power,
thermal, process-geometry, placement or mechanical design failure was found.
The SOUND verdict permits this exact layout to advance; it is not permission
to order until the named process and release controls are closed.
