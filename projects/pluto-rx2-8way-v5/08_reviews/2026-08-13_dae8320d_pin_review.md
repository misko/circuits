subject: Pluto RX2 8-Way v5 corrected exact final pin/pad/footprint review dae8320d
date: 2026-08-13
reviewer: Codex independent exact-artifact physical-pin reviewer
independence: independent-from-design-author; prior verdicts were not used as evidence
context-given: current exact board, schematic/netlists, digest-selected manufacturer documents, part dossiers and fabrication rules
review_stage: exact-final
review_kind: pin
source_commit: dae8320d3a5bab507a5846c7886ea719dc05ef61
board_sha256: 39251c24d4b3cc878824f26c48178cbc4a4d418fa528045c6c13f2308e017acd
schematic_sha256: 1abd0c209be27ac602f55f8e81cf25e4e98bb3a99a2fb76494fc8bbfcf20603b
circuit_json_sha256: c66c3e1a242d03f9312fa4fc03ac90634af704041461446e9e955232c3163f63
bom_sha256: 7b01a6d1fa70ae7187c5ada14a963894acca97fa4a7c893df6eba447d8a06c65
cpl_sha256: 0eab823cfe6eaa8c087d7cc429334f524a9d6e60f3751d02567c3b340d3415e1
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
p0_findings: 0
p1_findings: 0
p2_findings: 0

# Corrected exact final pin/pad/footprint review

## Verdict and boundary

**SOUND / DO-NOT-ORDER.** No physical pin-map, winding, polarity, land,
paste/mask, drill, via-process, connector-orientation or mounting/launch
defect was found on the exact board above. This is a historical exact-artifact
review, not a layout-seal or order authorization. In particular, the source
assembly contract at this commit does not machine-declare the J2-J10 THT
assembly process; that separate source-coverage omission must be corrected and
renewed before seal even though the realized PTH geometry reviewed here is
sound.

## Independent machine and netlist evidence

- Fresh P-PINMAP grades 15 multi-pin references and 127 declared physical pin
  identities: every identity reaches the schematic and footprint, and every
  collapsed identity is explicit and manufacturer-evidenced.
- A fresh KiCad schematic export and the retained converter netlist each match
  the exact board over 22 nets, 131 connected nodes and 24 explicit
  no-connects with zero discrepancy. Exact-board DRC reports 0 violations,
  0 unconnected items and 0 schematic-parity issues.
- P-LAND grades 62 routed pads with 0 failures and confirms every graded pad's
  actual track is no wider than its landable escape. P-PADSEP grades 12,971
  inter-footprint copper-pad pairs and 17,058 paste-to-foreign-copper pairs
  with no overlap or paste intrusion. The advanced fabrication-tier preflight
  reports 0 failures and 0 warnings.

## Part-group verdicts

| part group | independent datasheet-to-board result | verdict |
|---|---|---|
| J1 USB4105 | GCT Rev-B component-side order, 12 physical contact lands, four explicit coincident GND/VBUS logical pairs, four shell stakes and two locating holes match. A5/B5 remain independent CC1/CC2; data and SBU contacts are explicit opens; all VBUS contacts feed VBUS_RAW and all grounds/shells feed GND. | PASS |
| J2-J10 SMA | Each exact Amphenol launch has pad 1 on its one RF net and pads 2-5 on GND. The Rev-C 1.50-mm RF hole, four 1.70-mm ground holes on the +/-2.54-mm grid, pad diameters and right-angle mating direction all match. | PASS |
| J11 FTSH-105 | Samtec's top-view odd/even two-row numbering and CCW winding match: 1 VTref/3V3, 2 SWDIO, 3/5 GND, 4 SWCLK, 6/7/8 open, 9 GNDDetect/GND and 10 NRST. The keyed mating and pin-1 sides are not mirrored. | PASS |
| U1 PE42482 | The pSemi top-view CCW 24-pin map matches every RF1-RF8/RFC, alternating ground, LS, VDD and V1-V4 identity. Pin 20 is open; pad 25 is GND. LS is grounded and R3/R4-R6 establish the intended V4-high/V1-V3-low passive ALL_OFF state. | PASS |
| U2 STM32C011F4P6 | ST's TSSOP20 top view matches the board CCW winding: 4=3V3, 5=GND, 6=NRST, 7-10=SW_V1..4, 18=SWDIO and 19=SWCLK; all unused pins are explicit opens. | PASS |
| U3 TPS7A2433 | TI's fixed DBV top view matches IN/GND/EN/NC/OUT = VBUS_PROTECTED/GND/VBUS_PROTECTED/open/3V3. | PASS |
| U4 TPD2E2U06 | TI's DRL top view matches NC/NC/IO1/GND/IO2 = open/open/USB_CC1/GND/USB_CC2; the two CC channels are neither swapped nor shorted. | PASS |
| power/passives | D1 pad 1/cathode is VBUS_PROTECTED and pad 2/anode is GND; F1 connects VBUS_RAW to VBUS_PROTECTED. C1-C5, R1-R6 and C6 carry the intended rail, CC, control/default and NRST nets. | PASS |

## Lands, mask, paste and drills

- J1 has sixteen logical SMD contact pads on twelve manufacturer-defined
  physical lands. Its two 0.65-mm locating holes are NPTH. The four grounded
  shell slots use the exact 0.60 x 1.70-mm and 0.60 x 1.40-mm plated drills,
  1.00-mm-wide lands and intentional front-paste apertures. The GCT PCB-edge
  datum resolves exactly to the south outline at y=85.0 mm.
- J2-J10 each use one 2.40-mm copper land with 1.50-mm finished drill and four
  2.80-mm grounds with 1.70-mm finished drills. They have mask openings and no
  stencil paste. All nine connector barrels face outward; the 11.6-mm
  signal-pin-to-face datum reaches the intended edge with zero error.
- J11 follows Samtec Rev-H 0.74 x 2.79-mm lands on 1.27-mm column pitch and
  4.065-mm row spacing. Every land has mask and paste. No via center lies in
  any J11 land; the nearest via to pad 3 is 1.9675 mm from the pad center and
  outside the land.
- U1 has 0.30 x 0.60-mm perimeter lands, a 2.75 x 2.75-mm exposed GND land,
  and four 1.15 x 1.15-mm paste windows (69.95% nominal EP paste area). Its
  only via-in-pad field is nine 0.45/0.25-mm GND vias, all filled and
  copper-capped. The 0.10-mm radial annular ring meets the saved-board rule,
  and the 0.75-mm grid leaves 0.50 mm hole-to-hole.
- U2/U3/U4 and the passives use ordinary F.Cu/F.Mask/F.Paste SMD lands with
  the digest-selected package dimensions. H1-H4 are four unobstructed
  3.20-mm NPTH M3 holes at (25,25), (105,25), (25,80) and (105,80); they
  contain no plated or paste-bearing land.

## Correction-specific closure

- The former ordinary GND via at `(42.50,77.50)` is absent. The exact
  final-chain-to-board guard reports **PASS: 0 router-created vias in SMD
  lands**.
- The exact via-process checker grades 638/638 item flags and 638/638 drill
  selectors. It finds exactly nine protected `0.450/0.250;cap=1;fill=1`
  U1 sites, 629 ordinary `0.450/0.200;cap=0;fill=0` sites, zero partial
  protection, and drill-disjoint process families. All 9/9 via-in-pad sites
  are the declared U1 pad-25 field.
- The generated order remark selects the complete 0.25-mm drill family for
  copper-paste fill and copper cap and explicitly excludes every ordinary
  0.20-mm routing, stitching, fence and return via.

No P0, P1 or P2 physical pin/pad finding remains on this exact artifact.
