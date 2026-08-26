subject: pluto-rx2-8way-v4 v1.1 exact release-source pin review
reviewer: Codex GPT-5 fresh pin-correctness reviewer
independence: independent-from-design-author
source_commit: bc1fb1003cd9b7f06c70b15d973c5c018d0ff458
board_sha256: 72875d5ea92a52baa9962be3a69f4e69c1fb1ec3b9faf5ba4412934c18296bf7
design_verdict: SOUND

# Independent exact-artifact pin review

## Subject binding and method

The reviewed board is the immutable release source
`07_releases/v1.1-2026-08-01/source/pluto_rx2_8way_v4.kicad_pcb`.
The paired release schematic has SHA256
`3e6627ab345b25f8a46042abceafa0a509b7c0a4dbd440fe54ed32ce0cfeae4f`
and is byte-identical to the native schematic named by the RF contract.

I rendered and read the manufacturers' pin/package figures, generated twelve
fresh pin dossiers from the exact release board in a temporary directory, and
exported a fresh KiCad XML netlist from the exact release schematic. The fresh
netlist contains 130 nodes and the board contains 130 numbered component pads.
The switch, module, ten SMA connectors, and LED account for 100 high-risk pads;
all 100 schematic `(reference, pin, net)` tuples match the board, with zero
mismatches.

## U_SW — PE42482A-X

Primary evidence is pSemi DOC-75785-4, SHA256
`794579f2973d31c9d8bbe44bfd3656ae95027ff13ab79a0ceaede2a680cc9ec1`,
Figure 22 and Table 8 on PDF page 20.

- The manufacturer figure is a top view with pin 1 at the upper-left and
  counter-clockwise numbering. The footprint has the same pin-1 corner and
  counter-clockwise winding; it is neither mirrored nor shifted.
- All 24 perimeter pins and exposed pad 25 exist. Functions and nets agree:
  pin 1 LS is GND; RF1..RF7 reach ANT1..ANT7; RF8 reaches `RX1_TAP`; RFC
  reaches `RX2_OUT`; VDD reaches filtered `3V3`; V1..V4 reach `SW_V1..SW_V4`;
  every specified ground and exposed pad 25 reach GND.
- Pin 20 is connected to GND. Although named NC, Table 8 note 2 explicitly
  permits either GND or no external connection, so this is valid.

VERDICT: PASS

## U_MCU — Waveshare RP2040-Zero module

Primary evidence is the Waveshare schematic, SHA256
`bab8e6fecb8b1da565392a7510eaa8921529c4121f43a0505f708a06f1c1362e`,
cross-checked against the vendor top-view pinout image, SHA256
`b2fc91157b61b92ba29fad8cbd0307baf1a924b93e906a3780642691a85f921a`.

- The vendor artifacts establish the top-view clockwise physical order:
  pads 1..16 are GP0..GP15, pads 17..20 are GP26..GP29, pad 21 is 3V3,
  pad 22 is GND, and pad 23 is VSYS/5V. The release footprint has the same
  winding and corner; its 180-degree board rotation is not a mirror.
- GP0..GP3 drive `SEL_V1..SEL_V4` in order and GP4 drives `LED_STAT`.
  Pad 21 sources `3V3_MOD`, pad 22 is GND, and pad 23 is deliberately
  unconnected because the module's USB-C is the sole power entry.
- GP5..GP15 and GP26..GP29 are explicitly no-connect, with no accidental
  power, ground, or signal assignment.

VERDICT: PASS

## J_ANT1..J_ANT8, J_RX1, J_RX2 — KH-SMA-KE-Z

Primary evidence is the Kinghelm drawing, SHA256
`05257621aa124d9a077a47230c4ffc0030b23477c0e5c5e694abffa5f8daee08`,
sheet 2/2. It shows one centre conductor and four flange/ground posts on the
5.08 mm square.

- All ten instances put centre pad 1 on the intended RF net and pads 2..5 on
  GND: 50 of 50 connector pads agree.
- J_ANT1..7 reach ANT1..7. J_ANT8 and J_RX1 share `RX1_MAIN`, which is the
  intended through path and pickoff junction. J_RX2 reaches `RX2_OUT`.
- Rotating the fourfold-symmetric connector footprint does not create a
  numbered mirror condition.

VERDICT: PASS

## LED_ST polarity

The KENTO KT-0603R source document has SHA256
`a3bac1cc9c59cb306ad03512945cce12c87bb54252abc223b796e1d20d41d4a1`.
Its drawing makes the chamfered physical end the cathode. KiCad names that
same physical end pad 1/K even though the vendor calls it terminal 2. The
release consistently follows the KiCad footprint convention: pad 1/K is GND
and pad 2/A reaches `LED_STAT_A` through R_LED. This is a numbering-language
difference, not a reversed physical LED.

VERDICT: PASS

## Findings and limits

- No package-winding, pin-1, exposed-pad, RF-port, control, power, connector,
  or LED-polarity defect was found.
- This review proves artifact pin correctness, not solder-joint continuity.
  U_MCU is user-fitted, so first-article inspection, continuity, rail checks,
  and USB bring-up remain physical acceptance work.
- The assembler/uploader orientation preview remains the final independent
  check for U_SW pin 1 and LED cathode placement.

The exact v1.1 release-source pin mapping is SOUND.
