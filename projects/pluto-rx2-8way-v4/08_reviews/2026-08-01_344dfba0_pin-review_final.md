subject: pluto-rx2-8way-v4 344dfba05f7160b99b56dc9722cf8be72e846c7e
date: 2026-08-01
reviewer: pin-review (fresh independent pin-correctness lens)
context-given: full-tree
design_verdict: SOUND
order_verdict: ORDER

# Fresh independent final pin review

pin_review_verdict: PASS
p0_count: 0
p1_count: 0
p2_count: 0

## Frozen subject binding

| artifact | exact identity |
|---|---|
| source commit | `344dfba05f7160b99b56dc9722cf8be72e846c7e` |
| board | `04_kicad/pluto_rx2_8way_v4.kicad_pcb` — SHA256 `4a5e69d474f5354346edbb64683edb3c69946b9ad437c1ddf49e4b126fc7f14a` |
| fabrication archive | `06_build/fab/pluto_rx2_8way_v4_gerbers.zip` — SHA256 `4f1d2fea756f86220cb8c8dc2712198f4df0d306d6cd9a174587293f8b0e494d` |
| assembly PDF | `06_build/fab/pdf/assembly.pdf` — SHA256 `0d4ea5d79919ae5924496ea726c334b349c00163d9da92def0dd88788ef4d340` |
| TSX source | `03_tscircuit/src/pluto_rx2_8way_v4.tsx` — SHA256 `a326c554089f66838de18ac35223d1cded34f618a292f429ef71b2e81e4e4fdd` |
| native schematic | `04_kicad/pluto_rx2_8way_v4.kicad_sch` — SHA256 `3e6627ab345b25f8a46042abceafa0a509b7c0a4dbd440fe54ed32ce0cfeae4f` |
| frozen netlist | `06_build/netlists/pluto_rx2_8way_v4.net` — SHA256 `3235c59975ff666887fc5ec73888a264bba0662079334fb30a4aab63de8fda41` |

The four identities supplied in the review commission were re-hashed locally and match exactly.

## Independent method

I did not use an earlier review as evidence. I rendered the manufacturers' pin figures, derived the expected winding and function map from those figures, inspected the TSX connection blocks, exported fresh XML netlists from both current native schematic copies into a temporary directory, and read the frozen board pads with `pcbnew`.

MEASURED (by this reviewer):

- The `03_tscircuit/kicad` and `04_kicad` schematic exports are identical over **130/130 `(ref,pin,net)` nodes**.
- The board agrees with that fresh schematic export over **100/100 critical subject pads**, with zero net mismatches: U_SW 25, U_MCU 23, ten SMA connectors 50, and LED_ST 2.
- The TSX blocks for U_SW, U_MCU, J_ANT1..8, J_RX1, J_RX2 and LED_ST agree with the corresponding fresh native-netlist nodes.

## Part-by-part derivation and comparison

### U_SW — PE42482A-X

Independent source: pSemi DOC-75785-4, SHA256 `794579f2973d31c9d8bbe44bfd3656ae95027ff13ab79a0ceaede2a680cc9ec1`; Figure 22 and Table 8 were rendered from PDF page 20.

- Figure 22 is a **top view**, with pin 1 on the upper-left edge and numbering **counter-clockwise**. The board footprint has the same pin-1 corner and CCW winding; it is a rotation, not a mirror.
- All 24 perimeter pins and the exposed pad are present. The board mapping matches the figure and table exactly by function: `1 LS`, `2 RF2`, `3 GND`, `4 RF3`, `5 GND`, `6 RF4`, `7 GND`, `8 VDD`, `9..12 V1..V4`, `13 RF5`, `14 GND`, `15 RF6`, `16 GND`, `17 RF7`, `18 GND`, `19 RF8`, `20 NC`, `21 GND`, `22 RFC`, `23 GND`, `24 RF1`, `25 EP/GND`.
- Electrical nets are sane and agree in TSX/schematic/netlist/board: VDD is `3V3`; V1..V4 are `SW_V1..SW_V4`; RFC is `RX2_OUT`; RF1..RF7 are their like-numbered antenna nets; RF8 is the resistive reference path `RX1_TAP`; every specified ground and the exposed pad are GND.
- Pin 1 LS is tied to GND as required for the selected truth-table convention and RF ground. Pin 20 is tied to GND; datasheet Table 8 note 2 explicitly permits either GND or no external connection, so this is not an NC violation.

VERDICT: PASS

### U_MCU — Waveshare RP2040-Zero module

Independent sources: Waveshare schematic SHA256 `bab8e6fecb8b1da565392a7510eaa8921529c4121f43a0505f708a06f1c1362e` and vendor top-view pinout image SHA256 `b2fc91157b61b92ba29fad8cbd0307baf1a924b93e906a3780642691a85f921a`.

- The vendor schematic's P1 block independently states pads `1..16 = GP0..GP15`, `17..20 = GP26..GP29`, `21 = 3V3`, `22 = GND`, `23 = VSYS/5V`.
- The vendor top-view image fixes the physical order: GP0 starts at top-right, GP0..GP8 descend the right edge, GP9..GP13 cross the bottom right-to-left, then GP14, GP15, GP26..GP29, 3V3, GND, 5V ascend the left edge. That is **clockwise in top view**. The board footprint has the same CW winding and same pin-1 corner; it is not mirrored.
- The five functional GPIO mappings agree across all artifacts: pad 1/GP0 -> `SEL_V1`, 2/GP1 -> `SEL_V2`, 3/GP2 -> `SEL_V3`, 4/GP3 -> `SEL_V4`, and 5/GP4 -> `LED_STAT`.
- Pad 21/3V3 drives `3V3_MOD`, which reaches switch supply `3V3` through FB_3V3; pad 22 is GND. Pad 23/VSYS is deliberately unconnected, consistent with the module's own USB-C being the only power entry. Pads 6..20 carry explicit generated unconnected nets, not accidental shorts.

VERDICT: PASS

### J_ANT1..J_ANT8, J_RX1, J_RX2 — KH-SMA-KE-Z

Independent source: Kinghelm KH-SMA-KE-Z drawing SHA256 `05257621aa124d9a077a47230c4ffc0030b23477c0e5c5e694abffa5f8daee08`; sheet 2/2 shows one center conductor and four 0.9 mm square flange/ground posts on a 5.08 mm square, all in five D1.4 holes.

- Each of the ten board footprints has center pad 1 on its RF net and corner pads 2..5 on GND: **50/50 connector pad-net comparisons pass**.
- J_ANT1..7 pad 1 maps to ANT1..7 respectively. J_ANT8 and J_RX1 both map to `RX1_MAIN`, which is the through path and tap junction. J_RX2 maps to `RX2_OUT`. No connector has signal and ground interchanged.
- Rotating four instances by 45 degrees changes only placement; the center-plus-fourfold-symmetric land has no mirror-numbered failure mode.

VERDICT: PASS

### LED_ST — KT-0603R polarity cross-check

The KENTO package figure independently shows manufacturer terminal 1 as positive/anode and terminal 2 as negative/cathode, with the moulded/chamfered end at the cathode. KiCad's LED convention instead names pad 1 cathode. The board consistently uses the KiCad convention: LED_ST pad 1 is GND and pad 2 is `LED_STAT_A`; TSX labels pin 1 K and pin 2 A. This numbering difference is known and does not imply a physical reversal. The frozen CPL's 0-degree placement aligns the cathode-end shapes; the actual JLC uploader preview remains the final physical-orientation confirmation.

VERDICT: PASS

## Findings

| id | severity | finding | evidence | disposition |
|---|---|---|---|---|
| PIN-P0 | P0 | None. | Independent datasheet-to-artifact review and 100/100 critical node agreement. | No action. |
| PIN-P1 | P1 | None. | No winding, power, RF, control, connector, or exposed-pad discrepancy found. | No action. |
| PIN-P2 | P2 | None. | No documentation-only pin discrepancy found. | No action. |

## Limitations

- This is an artifact pin-correctness review, not electrical continuity on assembled hardware. U_MCU is user-fitted, so first-article continuity and USB bring-up remain physical acceptance tests.
- The JLC order preview is outside this frozen tree. It must still confirm PE42482 pin 1 and the LED cathode before payment, as already required by the fabrication instructions.

## Final verdict

The manufacturer-derived pin maps, package windings, TSX source, both native schematic copies, frozen netlist and frozen board agree. There are no open pin-review findings and no pin-correctness reason to block the seal or order.
