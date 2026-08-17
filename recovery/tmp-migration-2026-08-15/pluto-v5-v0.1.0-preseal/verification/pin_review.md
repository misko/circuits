subject: Pluto RX2 8-Way v5 exact final pin/pad/footprint review 4cf5c818
date: 2026-08-13
reviewer: Codex independent exact-artifact physical-pin reviewer
independence: independent-from-design-author; prior verdicts were not used as evidence
context-given: exact board, schematic/netlists, manufacturer documents, part dossiers, fabrication rules, assembly contract, and corrected J11 physical-role declaration
review_stage: exact-final
review_kind: pin
source_commit: 4cf5c818684e4c39f594b50a567fb086b9cf6f13
board_sha256: 39251c24d4b3cc878824f26c48178cbc4a4d418fa528045c6c13f2308e017acd
schematic_sha256: 1abd0c209be27ac602f55f8e81cf25e4e98bb3a99a2fb76494fc8bbfcf20603b
circuit_json_sha256: c66c3e1a242d03f9312fa4fc03ac90634af704041461446e9e955232c3163f63
bom_sha256: 7b01a6d1fa70ae7187c5ada14a963894acca97fa4a7c893df6eba447d8a06c65
cpl_sha256: 0eab823cfe6eaa8c087d7cc429334f524a9d6e60f3751d02567c3b340d3415e1
assembly_contract_sha256: b85a19f96355d42f2cc2b60d8d00e74551c035e6117c2d25b1f7ff7c37b4b341
j11_part_yaml_sha256: 2d52cf9d0fc1b8b4d59cee5bf9bce12a57739263e92408e7cf79433b2837ebb8
j11_series_print_sha256: ef2961377445b9ad10762ea27519e7b59e5cbb5847dc0058d8e35c0d97c446a3
j11_footprint_print_sha256: caa205b92560423f3b0aea9c69d6c38340d1b7f01b0655092994450e935edcb3
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
p0_findings: 0
p1_findings: 0
p2_findings: 0

# Exact final pin/pad/footprint review

## Verdict and narrow rebind

**SOUND / DO-NOT-ORDER.** P0/P1/P2 findings: **0/0/0**. No physical
pin-map, winding, polarity, gender/role, land, paste/mask, drill, via-process,
connector-orientation, mounting/launch or THT-process defect was found. The
only source-data delta from reviewed commit `3ecf08ab` corrects J11's dossier
`mates:` from a cable-family phrase to the schema's physical role `plug`, adds
the explicit FFSD cable-receptacle note, and updates status/changelog prose.
The schematic, board, netlist, rules, BOM, CPL and build artifacts are
byte-identical.

## Independent J11 plug-role closure

- Samtec's exact Rev-FX series print calls FTSH a **double vertical SMT
  terminal strip** and depicts exposed 0.41-mm square posts in the contact
  area. Its option table states `-K: KEYING OPTION FOR MATING WITH FFSD`.
  Thus this board-side male header is physically the plug; the keyed FFSD
  cable end is its receptacle. The corrected `mates: plug` value expresses
  physical role, while the added note preserves the exact compatible cable
  family. No inference from footprint or prose alone was used.
- The exact 105-01-L-DV-K-P-TR option string remains consistent: five
  positions per row/ten contacts, -01 3.05-mm posts, -L plating, double-
  vertical SMT tails, -K FFSD keying, -P pick-and-place pad, and -TR packaging.
- Independent P-ESC now grades all 13/13 dossiers with zero problems. The
  machine gate validates the closed `plug|receptacle` vocabulary; the human
  drawing read above validates that `plug` is the correct value.
- The electrical and land conclusions are unchanged: top-view odd/even
  numbering gives 1 VTref/3V3, 2 SWDIO, 3/5 GND, 4 SWCLK, 6/7/8 NC,
  9 GNDDetect/GND and 10 NRST. Pin 1 and keying are not mirrored. Samtec Rev-H
  requires 0.74 x 2.79-mm lands, 1.27-mm column pitch and 4.065-mm row spacing;
  the exact board matches. No via lies in any J11 land; the nearest is
  1.9675 mm from pad 3's centre.

## Independent machine and netlist evidence

- Fresh P-PINMAP grades 15 multi-pin references and 127 physical pin
  identities: every identity reaches schematic and footprint and every
  collapse is explicit and manufacturer-evidenced.
- Exact-board DRC reports 0 violations, 0 unconnected items and 0 schematic-
  parity issues. Fresh and retained schematic netlists remain equal to the
  board over 22 nets, 131 connected nodes and 24 explicit no-connects.
- P-LAND grades 62 of 161 copper pads with zero failure; all graded pads carry
  same-net tracks no wider than their feasible escape. P-PADSEP grades 12,971
  inter-footprint copper-pad pairs and 17,058 paste-to-foreign-copper pairs
  with no overlap or intrusion. Advanced-tier preflight remains 0 FAIL/0 WARN.

## Part-group findings

| group | exact independent result | verdict |
|---|---|---|
| J1 USB4105 | GCT component-side order, 12 physical contact lands/four explicit logical collapses, four shell stakes, two NPTH locators, CC1/CC2 separation, VBUS/GND identities and south-edge datum match. | PASS |
| J2-J10 SMA | Pad 1 is the RF net and pads 2-5 GND; Amphenol Rev-C land/drill grid and outward 11.6-mm mating-face datum match. | PASS |
| J11 FTSH-105 | Samtec drawing establishes male terminal-strip plug, keyed mating to FFSD receptacle, correct option code, winding, pin-1/key orientation, lands and clear mating volume. | PASS |
| U1 PE42482 | pSemi CCW RF1-RF8/RFC, GND, LS, VDD and V1-V4 identities match; pin 20 is open, pad 25 GND and pulls establish ALL_OFF. | PASS |
| U2 STM32C011F4P6 | Official local ST Rev5 confirms TSSOP20 winding: 4=3V3, 5=GND, 6=NRST, 7-10=SW_V1..4, 18=SWDIO, 19=SWCLK; unused pins are explicit opens. | PASS |
| U3/U4 | TI top views match U3 IN/GND/EN/NC/OUT and U4 NC/NC/IO1/GND/IO2; CC channels are neither swapped nor shorted. | PASS |
| power/passives/mechanical | D1 cathode pad 1 is VBUS_PROTECTED and anode pad 2 GND; F1/rails/control/NRST passives match. H1-H4 are clear 3.20-mm NPTH holes. | PASS |

## Land, via and assembly closure

- J1 shell slots, locators, paste and edge datum; J2-J10 paste-free THT
  land/drill geometry; J11 land/paste geometry; U1 exposed-pad paste windows;
  and ordinary SMD lands remain unchanged and manufacturer-consistent.
- Via-process grading covers all 638 vias: nine protected filled/capped
  0.45/0.25-mm U1-pad-25 sites, 629 untreated 0.45/0.20-mm ordinary sites,
  zero partial site and drill-disjoint process families. The final-chain guard
  remains zero router-created SMD-land vias.
- The machine-readable JLC THT wave/manual declaration names J2-J10 and has
  dated evidence. A-POP passes all 29 CPL rows with an explicit pre-release
  manifest set; final paperwork still requires the generated MANIFEST
  `not_assembled:` line.

## Order blockers

- The uploader must echo exact C429844 for every J2-J10 row as accepted
  wave/manual THT assembly; refusal requires a separate hand-solder population
  contract and CPL.
- Hard-stop on any mismatch in line-by-line BOM/CPL allocation,
  JLC04161H-7628 stackup/impedance, the complete U1 0.25-mm fill/cap family,
  J11 pin-1/key orientation and accessible mating volume, critical
  D1/J1/U1/SMA previews, or stock allocation.
- Exact plotted RF_FAB review and first-article VNA measurements remain open.

The corrected J11 role declaration is now both schema-valid and drawing-true.
No P0, P1 or P2 physical pin/pad finding remains on this exact final artifact.
