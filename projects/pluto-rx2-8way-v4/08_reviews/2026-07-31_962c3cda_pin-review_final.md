# Final fresh-context pin review — Pluto RX2 8-way v4

**Source commit:** `962c3cdaeba5070d5b668bf01a70a4ccc6498c51`
**Review date:** 2026-07-31
**Overall verdict: PASS**

The requested connector, active/module, control, power, and LED pins agree with the independently read vendor artifacts and with the executable TSX, exported/fresh schematic netlists, sealed schematic, and sealed board pads. No winding, pin-1, power, control, RF-port, ground/EP, or LED-polarity failure was found. Prior review/disposition material was not used as evidence.

## Provenance and method

- Fresh-context procedure: `skills/kicad-pcb/references/pin-review-protocol.md`, read in full before the audit.
- Git: `HEAD` was exactly `962c3cdaeba5070d5b668bf01a70a4ccc6498c51`. The reviewed `02_parts`, `03_tscircuit`, `04_kicad`, and `06_build` trees had no worktree delta from that commit.
- RP2040-Zero sources:
  - vendor schematic `02_parts/RP2040-Zero/RP2040_Zero.pdf`, SHA-256 `bab8e6fecb8b1da565392a7510eaa8921529c4121f43a0505f708a06f1c1362e`;
  - vendor top/bottom pinout image `RP2040-Zero-details-7.jpg`, SHA-256 `b2fc91157b61b92ba29fad8cbd0307baf1a924b93e906a3780642691a85f921a`;
  - vendor dimension/image cross-check `RP2040-Zero-details-size.jpg`, SHA-256 `42245fe55e0cb9a97fb0538029322cc03d31b4a1ef672b37b89cd93e6b3cc5b9`.
- PE42482 source: `02_parts/PE42482A-X/DOC-75785-4.pdf`, SHA-256 `794579f2973d31c9d8bbe44bfd3656ae95027ff13ab79a0ceaede2a680cc9ec1`; Figure 22/Table 8 on PDF p20 and package Figure 23 on p21 were rendered and read independently. Truth-table/LS behavior was checked on p10.
- SMA source: `02_parts/KH-SMA-KE-Z/KH-SMA-KE-Z-2021-08-10.pdf`, SHA-256 `05257621aa124d9a077a47230c4ffc0030b23477c0e5c5e694abffa5f8daee08`; drawing sheet 2/2 was rendered and read.
- LED source: `02_parts/KT-0603R/HUBEI-KENTO-KT-0603R-RevA.0-2018-12-06.pdf`, SHA-256 `a3bac1cc9c59cb306ad03512945cce12c87bb54252abc223b796e1d20d41d4a1`; package/polarity drawing on PDF p2 was rendered and read.
- Implementation evidence: `03_tscircuit/src/pluto_rx2_8way_v4.tsx`, `06_build/netlists/pluto_rx2_8way_v4.net`, `04_kicad/pluto_rx2_8way_v4.kicad_sch`, `04_kicad/pluto_rx2_8way_v4.kicad_pcb`, the three project-local footprints, and the committed `06_build/pin_audit/*.md` dossiers.
- `pin_audit.py` was rerun read-only to temporary directories. The fab BOM reproduced the committed U_SW and ten SMA dossiers byte-for-byte and produced the LED_ST dossier; the module pin-review BOM reproduced U_MCU byte-for-byte.
- The committed exported netlist versus sealed board passed: 24/24 nets, 114/114 connected nodes, 16/16 no-connects, zero discrepancies. A fresh `kicad-cli` netlist export from the sealed schematic produced the same 24-net/114-node/16-no-connect parity result.

## Per-part verdicts

| Part | Vendor/package fact independently derived | Board/TSX result | Verdict |
|---|---|---|---|
| U_MCU | Top view, USB-C up: pad 1 is top-right GP0 and numbering winds **CW** to pad 23 at top-left; 23 castellated pads | Footprint/dossier are CW with the same corner and complete 1–23 map | **PASS** |
| U_SW | Top view: pin-1 dot at top-left; 1–6 down left, 7–12 across bottom, 13–18 up right, 19–24 across top; EP required | Footprint/dossier are **CCW**, 24 leads plus pad 25 EP, with matching pin-1 corner | **PASS** |
| J_ANT1 | Centre conductor is RF; four corner posts are shield/ground | `1=ANT1`; `2..5=GND` | **PASS** |
| J_ANT2 | Centre conductor is RF; four corner posts are shield/ground | `1=ANT2`; `2..5=GND` | **PASS** |
| J_ANT3 | Centre conductor is RF; four corner posts are shield/ground | `1=ANT3`; `2..5=GND` | **PASS** |
| J_ANT4 | Centre conductor is RF; four corner posts are shield/ground | `1=ANT4`; `2..5=GND` | **PASS** |
| J_ANT5 | Centre conductor is RF; four corner posts are shield/ground | `1=ANT5`; `2..5=GND` | **PASS** |
| J_ANT6 | Centre conductor is RF; four corner posts are shield/ground | `1=ANT6`; `2..5=GND` | **PASS** |
| J_ANT7 | Centre conductor is RF; four corner posts are shield/ground | `1=ANT7`; `2..5=GND` | **PASS** |
| J_ANT8 | Centre conductor is RF; four corner posts are shield/ground | `1=RX1_MAIN`; `2..5=GND` | **PASS** |
| J_RX1 | Centre conductor is RF; four corner posts are shield/ground | `1=RX1_MAIN`; `2..5=GND` | **PASS** |
| J_RX2 | Centre conductor is RF; four corner posts are shield/ground | `1=RX2_OUT`; `2..5=GND` | **PASS** |
| LED_ST | Physical chamfer/marked end is cathode; KiCad footprint pad 1 is that marked end | `1=K=GND`; `2=A=LED_STAT_A` | **PASS** |

For the SMA footprint, the vendor drawing does not number the four equivalent ground posts. Therefore the dossier's computed winding is not a vendor-verifiable property and is electrically immaterial; centre-versus-corner identity is the applicable pin check, and all four corner pads are GND in every instance.

## Pin findings

### U_MCU — VERDICT: PASS

- U_MCU pins 1–4 (GP0–GP3): expected consecutive GPIO outputs driving PE42482 V1–V4 in order vs `SEL_V1..SEL_V4` through `R_S1..R_S4` to U_SW pins 9–12 — **MATCH**.
- U_MCU pin 5 (GP4): expected status-LED control GPIO vs `LED_STAT` feeding `R_LED` and then LED_ST anode — **MATCH**.
- U_MCU pin 21 (3V3): expected on-module RT9013 3V3 output feeding the carrier vs `3V3_MOD`, then `FB_3V3.1`; `FB_3V3.2` creates filtered `3V3` for U_SW pin 8 — **MATCH**.
- U_MCU pin 22 (GND): expected module ground vs `GND` — **MATCH**.
- U_MCU pin 23 (5V/VSYS/VBUS): expected no carrier connection because the module USB-C is the sole 5 V entry vs explicit no-connect — **MATCH**.
- U_MCU pins 6–20: expected unused carrier GPIO pads vs explicit no-connects — **MATCH**.
- U_MCU on-module WS2812: vendor schematic/pinout expect `VDD=3V3`, `VSS=GND`, and `DIN=GP16`; these are internal to the module and GP16 is not a carrier pad — **MATCH**.
- U_MCU package: expected 23 castellations, pad 1 at top-right and CW numbering in top view vs 23 footprint pads in that exact geometry; board rotation 180 degrees is a legal rotation, not a mirror — **MATCH**.

### U_SW — VERDICT: PASS

- U_SW pin 1 (LS): expected a firm RF ground for non-complemented truth-table selection vs `GND` — **MATCH**.
- U_SW pins 3, 5, 7, 14, 16, 18, 21, 23 (GND): expected ground vs `GND` on every pin — **MATCH**.
- U_SW pin 8 (VDD): expected nominal 3.3 V supply vs filtered `3V3` — **MATCH**.
- U_SW pins 9–12 (V1–V4): expected four digital control inputs vs `SW_V1..SW_V4`, each reached from the correspondingly numbered U_MCU GPIO path and each pulled down — **MATCH**.
- U_SW pins 2/4/6/13/15/17/24 (RF2/RF3/RF4/RF5/RF6/RF7/RF1): expected antenna-port RF nets vs `ANT2/ANT3/ANT4/ANT5/ANT6/ANT7/ANT1` — **MATCH**.
- U_SW pin 19 (RF8): expected eighth RF input vs `RX1_TAP`, reached from the RX1 main line through the two-resistor 440-ohm tap chain — **MATCH**.
- U_SW pin 22 (RFC): expected common/output RF port vs `RX2_OUT` to J_RX2 pad 1 — **MATCH**.
- U_SW pin 20 (NC): datasheet permits GND or open vs `GND` — **MATCH**.
- U_SW pin 25 (exposed ground pad): expected present and grounded for operation vs 2.75 mm square copper pad on `GND` — **MATCH**.
- U_SW package: expected 24 leads, six per side, pin-1 top-left, CCW top-view winding, plus EP vs board footprint/dossier — **MATCH**.

### Connectors — VERDICT: PASS

- J_ANT1 pin 1 (RF): expected centre RF conductor to PE42482 RF1 vs `ANT1 -> U_SW.24` — **MATCH**; pins 2–5 expected shield posts vs `GND` — **MATCH**.
- J_ANT2 pin 1 (RF): expected centre RF conductor to PE42482 RF2 vs `ANT2 -> U_SW.2` — **MATCH**; pins 2–5 expected shield posts vs `GND` — **MATCH**.
- J_ANT3 pin 1 (RF): expected centre RF conductor to PE42482 RF3 vs `ANT3 -> U_SW.4` — **MATCH**; pins 2–5 expected shield posts vs `GND` — **MATCH**.
- J_ANT4 pin 1 (RF): expected centre RF conductor to PE42482 RF4 vs `ANT4 -> U_SW.6` — **MATCH**; pins 2–5 expected shield posts vs `GND` — **MATCH**.
- J_ANT5 pin 1 (RF): expected centre RF conductor to PE42482 RF5 vs `ANT5 -> U_SW.13` — **MATCH**; pins 2–5 expected shield posts vs `GND` — **MATCH**.
- J_ANT6 pin 1 (RF): expected centre RF conductor to PE42482 RF6 vs `ANT6 -> U_SW.15` — **MATCH**; pins 2–5 expected shield posts vs `GND` — **MATCH**.
- J_ANT7 pin 1 (RF): expected centre RF conductor to PE42482 RF7 vs `ANT7 -> U_SW.17` — **MATCH**; pins 2–5 expected shield posts vs `GND` — **MATCH**.
- J_ANT8 pin 1 (RF): expected eighth/RX1 antenna main-line node vs `RX1_MAIN`, shared with J_RX1 and feeding the RF8 tap chain — **MATCH**; pins 2–5 expected shield posts vs `GND` — **MATCH**.
- J_RX1 pin 1 (RF): expected Pluto RX1 continuation of the eighth antenna main line vs `RX1_MAIN`, shared with J_ANT8 — **MATCH**; pins 2–5 expected shield posts vs `GND` — **MATCH**.
- J_RX2 pin 1 (RF): expected Pluto RX2 output from switch common vs `RX2_OUT -> U_SW.22/RFC` — **MATCH**; pins 2–5 expected shield posts vs `GND` — **MATCH**.
- All ten connectors: expected five D1.4 holes on the vendor 5.08 mm square pattern vs one centre plus four corner THT pads, with no missing pad — **MATCH**.

### LED_ST — VERDICT: PASS

- LED_ST physical cathode: expected at the vendor's chamfered/marked terminal-2 end; KiCad deliberately calls the same physical end pad 1/K vs footprint F.Fab chamfer and silk bar at pad 1 — **MATCH PHYSICALLY** despite the vendor/KiCad integer reversal.
- LED_ST pin 1 (K): expected ground return vs `GND` in TSX, netlist, schematic, and board — **MATCH**.
- LED_ST pin 2 (A): expected ballasted drive vs `LED_STAT_A`, reached from U_MCU GP4/pad 5 through `R_LED` — **MATCH**.
- LED_ST control/power path: expected active-high GPIO source through series resistance, not a direct rail connection vs `U_MCU.5/GP4 -> LED_STAT -> R_LED -> LED_STAT_A -> LED_ST.2/A -> LED_ST.1/K -> GND` — **MATCH**.

## Non-blocking source-hygiene observations

These do not change the pin verdict because the executable mappings and all fab-of-record electrical artifacts agree, but they should be corrected before future reuse:

1. Two TSX comments call the module's 5 V pad “pad 1.” The executable `pinLabels`/`connections`, vendor artifacts, part dossier, schematic, netlist, board, and pin audit correctly identify **pad 23** as 5 V and pad 1 as GP0. This is a prose-only contradiction adjacent to a high-risk mirror mapping.
2. `RP2040-Zero/part.yaml` records `datasheet.local: RP2040_Zero-20211012.pdf`, while the committed matching-hash artifact and pin-audit path are `RP2040_Zero.pdf`. The bytes/hash are verified; the local filename field is stale.
3. A diagnostic comparison of promoted `03_src/route/r5.kicad_pcb` to the sealed board reports 129/130 pad nodes equal, with only `C_BULK.1` carrying stale `3V3_MOD` metadata in r5 versus the correct filtered `3V3` on the sealed board. This is outside every reviewed pin above; both the committed and freshly exported schematic netlists agree with the sealed board at 24/24 nets. It is recorded here so that route-source metadata is not mistaken for a clean whole-board parity result.

## Final decision

**PASS.** The requested pin scope contains no FAIL or QUESTION. In particular, the RP2040-Zero is not mirrored, the PE42482 has the correct pin-1 corner/CCW winding and grounded EP, every SMA centre/shield assignment is correct, VDD and select controls land on the intended filtered/control nets, and LED_ST's physical cathode is on board pad 1/GND with its anode driven through the ballast from GP4.
