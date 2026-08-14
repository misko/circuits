subject: Pluto RX2 8-Way v5 exact final pin/pad/footprint review 3ecf08ab
date: 2026-08-13
reviewer: Codex independent exact-artifact physical-pin reviewer
independence: independent-from-design-author; prior verdicts were not used as evidence
context-given: exact board, schematic/netlists, digest-selected manufacturer documents, part dossiers, fabrication rules, assembly contract, and authoritative findings ledger
review_stage: historical-exact-artifact
review_kind: pin
source_commit: 3ecf08abe5f44c098144abfc8cea31fc89354c59
board_sha256: 39251c24d4b3cc878824f26c48178cbc4a4d418fa528045c6c13f2308e017acd
schematic_sha256: 1abd0c209be27ac602f55f8e81cf25e4e98bb3a99a2fb76494fc8bbfcf20603b
circuit_json_sha256: c66c3e1a242d03f9312fa4fc03ac90634af704041461446e9e955232c3163f63
bom_sha256: 7b01a6d1fa70ae7187c5ada14a963894acca97fa4a7c893df6eba447d8a06c65
cpl_sha256: 0eab823cfe6eaa8c087d7cc429334f524a9d6e60f3751d02567c3b340d3415e1
assembly_contract_sha256: b85a19f96355d42f2cc2b60d8d00e74551c035e6117c2d25b1f7ff7c37b4b341
stm32_datasheet_sha256: e392b1542086b25f6bcb8856b6c0467aa3ec10e31f03bdafca74796485c531fe
stm32_part_yaml_sha256: 8b246f90e772e6552eaed3fb969388d2e20a3dac56ed70d36eaaee64b0e6ed26
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
p0_findings: 0
p1_findings: 0
p2_findings: 0

# Historical exact-board pin/pad/footprint review

## Verdict and exact-subject closure

**SOUND / DO-NOT-ORDER.** P0/P1/P2 findings: **0/0/0**. This is a
historical, non-sealing review because a later J11 dossier-schema correction
supersedes its source subject. No physical
pin-map, winding, polarity, land, paste/mask, drill, via-process,
connector-orientation, mounting/launch, or THT-process declaration defect was
found. Relative to the fully checked `770ac064` subject, the exact final commit
only closes V5-F2 in the findings ledger, removes stale research prose, and
adds its changelog record. No part dossier, design, board or build artifact
changed.

## Official ST Rev5 evidence closure

- The digest-selected U2 authority is official ST DS13866 Rev5, February
  2026, SHA-256
  `e392b1542086b25f6bcb8856b6c0467aa3ec10e31f03bdafca74796485c531fe`.
  Its metadata and content identify a 97-page ST datasheet created in February
  2026. The prior local bytes identify as Rev3 and are retained under their
  correct historical name only.
- Rev5 Figure 5 confirms the top-view TSSOP20 sequence: 1 PB7, 2 PC14,
  3 PC15, 4 VDD/VDDA, 5 VSS/VSSA, 6 PF2-NRST, 7-10 PA0-PA3,
  11-15 PA4-PA8, 16 PA11[PA9], 17 PA12[PA10], 18 PA13/SWDIO,
  19 PA14-BOOT0/SWCLK and 20 PB6. It exactly matches the dossier and U2 board
  winding.
- Rev5 Table 23 confirms BOR4 rising 2.80-3.00 V and falling 2.70-2.90 V.
  Table 40 confirms HSI48 drift of +/-1% from 0 to 85 C and -2.5/+2% from
  -40 to 125 C. Section 6.4/Table 68 confirm nominal TSSOP20 dimensions of
  6.5 x 4.4 mm at 0.65-mm pitch; Figure 35 uses 0.40-mm footprint lands on
  0.65-mm pitch. All design-consumed pin, BOR, HSI48 and package facts are
  unchanged from the earlier evidence. The final ledger correctly closes
  V5-F2 against these exact local bytes and dossier.

## Independent machine and netlist evidence

- Fresh P-PINMAP grades 15 multi-pin references and 127 physical pin
  identities; every identity reaches the schematic and footprint, and every
  collapse is explicit and manufacturer-evidenced.
- Fresh KiCad schematic export and retained converter netlist each match the
  exact board over 22 nets, 131 connected nodes and 24 explicit no-connects
  with zero discrepancy. Exact-board DRC reports 0 violations, 0 unconnected
  items and 0 schematic-parity issues.
- P-LAND grades 62 routed pads with 0 failures; all 62 carry same-net tracks no
  wider than their landable escape. P-PADSEP grades 12,971 inter-footprint
  copper-pad pairs and 17,058 paste-to-foreign-copper pairs with no overlap or
  intrusion. Advanced-tier preflight reports 0 failures and 0 warnings.
- Fresh pin-audit generation produces 15 dossiers for J1-J11 and U1-U4. D1,
  passives and mounting holes were independently graded as their own
  polarity/land/mechanical groups.

## Part-group verdicts

| part group | exact result | verdict |
|---|---|---|
| J1 USB4105 | GCT Rev-B component-side order; 12 physical contact lands, four explicit coincident GND/VBUS logical pairs, four shell stakes and two locating holes match. A5/B5 remain independent CC1/CC2; unused data/SBU are explicit opens. | PASS |
| J2-J10 SMA | Amphenol Rev-C pad 1 is the RF net and pads 2-5 are GND. The 1.50-mm signal hole, four 1.70-mm ground holes on the +/-2.54-mm grid, lands and outward mating directions match. | PASS |
| J11 FTSH-105 | Samtec top-view odd/even CCW numbering matches VTref, SWDIO, GND, SWCLK, GNDDetect and NRST; opens are explicit and pin 1 is not mirrored. | PASS |
| U1 PE42482 | pSemi top-view CCW RF1-RF8/RFC, GND, LS, VDD and V1-V4 identities match. Pin 20 is open and pad 25 is GND; passive pulls establish ALL_OFF. | PASS |
| U2 STM32C011F4P6 | Official local ST Rev5 confirms the CCW TSSOP20 winding: 4=3V3, 5=GND, 6=NRST, 7-10=SW_V1..4, 18=SWDIO, 19=SWCLK; unused pins are explicit opens. | PASS |
| U3 TPS7A2433 | TI DBV top view matches IN/GND/EN/NC/OUT = VBUS_PROTECTED/GND/VBUS_PROTECTED/open/3V3. | PASS |
| U4 TPD2E2U06 | TI DRL top view matches NC/NC/IO1/GND/IO2 = open/open/USB_CC1/GND/USB_CC2. | PASS |
| power/passives | D1 pad 1/cathode is VBUS_PROTECTED and pad 2/anode GND; F1 bridges VBUS_RAW to VBUS_PROTECTED. Rails, CC, control/default and NRST passives are correct. | PASS |

## Land, drill and process closure

- J1's 16 logical pads occupy 12 manufacturer-defined contact lands; two
  0.65-mm locators are NPTH. Four grounded shell slots use the exact plated
  drills, 1.00-mm lands and intentional front paste. Its edge datum is the
  south outline at y=85.0 mm.
- J2-J10 use one 2.40/1.50-mm signal land/drill and four 2.80/1.70-mm GND
  lands/drills, mask openings and no stencil paste. The 11.6-mm face datum is
  exact. J11 uses 0.74 x 2.79-mm lands at 1.27-mm pitch and 4.065-mm row
  spacing; no via is inside a land, and the nearest via is 1.9675 mm from pad
  3's centre.
- U1 uses 0.30 x 0.60-mm perimeter lands, a 2.75-mm exposed GND land, and four
  1.15-mm paste windows (69.95% nominal paste area). Exactly nine protected
  0.45/0.25-mm filled/capped GND vias occupy pad 25. The 0.10-mm annular ring
  and 0.50-mm hole-to-hole gap meet the saved rules.
- Final-chain-to-board guarding reports zero router-created SMD-land vias.
  Via-process grading covers all 638 vias: nine protected 0.45/0.25-mm sites,
  629 ordinary untreated 0.45/0.20-mm sites, no partial site, and
  drill-disjoint process families.
- H1-H4 are unobstructed 3.20-mm NPTH M3 holes with no plated or paste-bearing
  land.

## THT contract and order blockers

- The machine-readable JLC THT wave/manual declaration names J2-J10 and has
  dated evidence. Independent A-POP grading with an explicit empty pre-release
  manifest set passes all 29 CPL rows, including all nine paste-free THT
  connectors, with no unexplained part and 0.00050-mm worst datum error.
  Final release paperwork must include the generated MANIFEST
  `not_assembled:` line.
- The uploader must echo exact C429844 for every J2-J10 row as accepted
  wave/manual THT assembly. Refusal stops release and requires a separate
  hand-solder population contract and CPL.
- Also hard-stop on any mismatch in line-by-line BOM/CPL allocation,
  JLC04161H-7628 stackup/impedance echo, the complete U1 0.25-mm fill/cap drill
  family, J11 pin-1 orientation, D1/J1/U1/SMA previews, or stock allocation.
  Exact plotted RF_FAB review and first-article VNA measurements remain open.

No P0, P1 or P2 physical pin/pad finding remains on this exact historical
artifact.
