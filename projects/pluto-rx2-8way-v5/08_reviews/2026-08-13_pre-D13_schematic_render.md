subject: Pluto RX2 8-Way v5 delivered schematic readability
date: 2026-08-13
reviewer: Codex exact-PDF human readability review
review_stage: pre-route
review_kind: schematic_render
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
schematic_pdf_sha256: 9f2778643675c639b5026482a8624ce2373c41b05425572ba60dd800999e6cf3
netlist_sha256: 51d52ddd49ab551677b656a7593c6fd0162ec5595a6c26ac6bfdbdda12c22ced
exact_netlist_sha256: 12e7039b3e2d185b53187ecdd53acec655969aa1b19b32cdc53c2af2d16ecf21
parts_sha256: af89e5d5be339883a97cdef1d523433c4ccda1cf6b645d0935b0498ef83f1b40
design_rules_sha256: 426089542e30284dddd34c08b222e3402510bcb7612a2c4f65b6bcf20e4094f2
circuit_json_sha256: 37c7a0083c4736f9ee5e63f3891537d3c187ccd01384c7002db584576c63cfd3
kicad_schematic_sha256: 572849a8ea53b9fc3ef4d92d6dba5bb692d0779e9a4002090b3cfaacaacd517a
schematic_checkpoint_sha256: 0130a38cd1d074450eb5e3a8a087550fc6698900d21ec75282c5e58cb005707e
authoring_source_sha256: 873f6598254556541fef9be544c0b88ca0628fa011834ff4940601ba771f711b

# Pre-route human schematic render review

## Verdict

**SOUND / DO-NOT-ORDER.**  I rendered and visually inspected all four pages of
the exact PDF bound above at 180 dpi, and inspected the corrected MCU page
again at 200 dpi.  All 33 components are present.  Every page title, component
identity, value, connected endpoint, intentional open and safety boundary
needed to understand the schematic is visible and legible.  No blocking
overlap, clipping, false connection or misleading pin label remains.

The first candidate PDF failed this human review because U2's unused pin
function names did not match ST DS13866 even though all connected nets and
machine pin-map assertions passed.  That PDF was discarded.  The exact PDF
named here was fully regenerated after correcting the source labels.

## Page-by-page inspection

- **Page 1 — USB-C power only:** J1 visibly keeps CC1 and CC2 separate, marks
  all six D+/D-/SBU contacts as NC, and joins all VBUS and ground/shell
  contacts correctly.  U4, the independent 5.1 kOhm Rd resistors, the
  `VBUS_RAW -> F1 -> VBUS_PROTECTED` path, D1 polarity, C1, U3, C2 and `3V3`
  are readable.  The heading explicitly says 5 V sink and no USB data.
- **Page 2 — RF switch core:** U1's RFC/RF1-RF8, ground/EP, VDD, LS, V1-V4
  names and physical pin numbers are visible.  The all-off bias is traceable:
  R3 goes from `3V3` to `SW_V4`, while R4-R6 take `SW_V1/SW_V2/SW_V3` to GND.
  C4 is separately visible.  The long net runs do not cross another signal or
  create an ambiguous junction.  The heading openly states receive-only and
  user-accepted extended 5.9 GHz operation.
- **Page 3 — RF interfaces:** J2 is distinctly labelled `RF_COMMON`.  J3-J10
  are labelled `RF_ANT1` through `RF_ANT8` in numeric order.  For every SMA,
  RF pin 1 and four separately numbered ground pins are readable.  The sparse
  arrangement makes the one-common/eight-throw boundary immediately clear.
- **Page 4 — autonomous control:** U2 is legibly identified as
  STM32C011F4P6.  The final symbol shows the correct DS13866 pin functions,
  including PC14/PC15, PA8, PA11/PA9, PA12/PA10 and PB6 on the unused pins.
  `VDD_VDDA`, `VSS_VSSA`, `PF2_NRST`, PA0-V1 through PA3-V4, PA13-SWDIO and
  PA14-BOOT0-SWCLK are readable with their physical numbers.  TP1-TP5,
  C3/C5/C6 and their net labels are unambiguous.  The heading identifies the
  generated fast20-v1 profile and direct Raspberry Pi/ST-LINK SWD boundary.

No page is missing.  The exact Circuit JSON digest prefix printed on every
page agrees across the document.  The PDF is a human topology view, not proof
of future PCB geometry or assembled behavior, so the order verdict remains
DO-NOT-ORDER.  Blocking readability findings: none.
