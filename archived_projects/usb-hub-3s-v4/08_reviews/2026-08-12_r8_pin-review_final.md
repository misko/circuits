subject: usb-hub-3s-v4 routed r8 pin/process review
date: 2026-08-12
reviewer: pin-review
context-given: zero-context
source_commit: cc8368ffbb7b93cf8f4b567534e8537df792d638
board_sha256: 6da6560dd325ef8d9f21ef0dcc99f238e1cb2dd1ec60a76bd4db000ec8c3355b
design_verdict: DEFECTIVE
order_verdict: DO-NOT-ORDER

# Scope and exact artifacts

This is an independent routed-board PIN/PROCESS review of
`04_kicad/usb_hub_3s_v4.kicad_pcb`. Entry SHA-256 was
`6da6560dd325ef8d9f21ef0dcc99f238e1cb2dd1ec60a76bd4db000ec8c3355b`.
The promoted route input was independently hashed as
`03_src/route/r8.kicad_pcb` =
`8ea0f50681d48c34c6e5f300cc8842f144937cd92fb118cad6a546d19acf173f`.
Inputs were the exact saved board, exported netlist, live `02_parts/` dossiers,
live rules, and machine reports in `06_build/`. Journals, STATUS, prior
`08_reviews/`, and prior human conclusions were not used as evidence.

# Coverage denominator

- Board census measured directly with pcbnew: 95 footprints, 379 pads, and 183
  vias.
- Functional pin/process denominator: 35 refs = 23 active/protection/connector
  refs (`U1-U9`, `Q1`, `D1-D6`, `J1-J5`, `F1`, `SW1`) plus 12 test points
  (`TP1-TP12`). All 35 were extracted from the board and their physical pad/net
  assignments were inspected.
- Independent authority closure: 18/23 functional refs have a locally vendored,
  byte-hash-bound or inherently board-owned/non-polar identity sufficient for
  this pass. Five refs are not independently closed: `U4-U6` (one selected
  TPS2559 part), `U9` (TPS259827O), and `D1` (SMBJ15A). These are findings, not
  silent omissions.
- Machine identity denominator: a fresh `pin_map_check.py` run graded 17
  multi-pin refs / 192 declared physical pin identities and returned
  `P-PINMAP PASS`. This is consistency evidence only, not datasheet authority.
- Via-process denominator: a fresh `via_process_check.py` run graded 183/183
  vias: 65 protected `0.500/0.200 mm` fill+capped vias, 104 ordinary
  `0.600/0.300 mm` vias, 14 ordinary `0.700/0.300 mm` vias, zero partial
  protection, and drill-disjoint process families; `V-PROCESS PASS`.
- Declared high-current via-boundary denominator: a fresh
  `via_ampacity_check.py` run graded 4/4 banks and returned `A-VIA PASS`:
  `U9 OUT -> 5VA` 14 x 0.30 mm holes = 11.76 A credited / 8.00 A required;
  each `U4/U5/U6 5VA` input bank = four 0.30 mm plus one 0.20 mm hole =
  3.91 A credited / 2.849 A required. The cited basis is TI SLVA959B Table
  3-1 at 10 C rise, with no capacity credit for fill material.

# Exact observations

- Reverse-polarity path as saved: `Q1` pads 5-8 are `VBAT_FUSED`, pads 1-3 are
  `VIN`, and pad 4 is `RPP_GATE`; `D5` pad 1 is `VIN` and pad 2 is
  `RPP_GATE`. This agrees with the local SHA-bound DMP3013SFV-7 and
  BZT52C12-7-F pin authorities. `D1` is pad 1 `VIN`, pad 2 `GND`, but its
  selected dossier has no SHA-bound local PDF (finding PIN-P0-03).
- `U1`/`U2` package lands preserve their numbered perimeter and exposed ground
  lands. `U3` has pins 1-20 plus duplicated same-number pad 21 on `GND`;
  `U9` has pins 1-24 plus split pad 25 on `5VA_RAW` and pad 26 on `GND`.
  `U4-U6` each have pins 1-10 plus exposed pad 11 on `GND`.
- USB-C is physically power-only: all four J5 VBUS contacts are `VBUSC`; all
  four GND contacts and four shell stakes are `GND`; A5=`CC1` and B5=`CC2`;
  A6/B6, A7/B7, and A8/B8 terminate only on explicit unconnected nets. CC1
  and CC2 remain separate, pass the connector-side three-pad `D6`, and reach
  `U3`; no USB D+/D- data path leaves J5.
- USB-A contacts are 1=`VBUSAx`, 2=`DM_Ax`, 3=`DP_Ax`, 4=`GND`, with both
  shell/mechanical PTH lands on `GND`. Their D+/D- nets terminate locally in
  the USBLC6 clamps and TPS2513A charge-signature controllers; they do not form
  an upstream USB data link.
- Connector mechanics are represented: J2-J4 each retain two 2.26 mm shell
  PTHs; J5 retains four grounded shell PTHs and two unplated locator holes;
  J1 retains two 1.30 mm PTH contacts; F1 retains two physical holes per fused
  electrical terminal. No connector mechanical pad was silently assigned to a
  signal net.
- Test points are one-pad identities and cover `VIN`, `5VA`, `5VC_RAW`,
  `VBUSC`, `EN_BUS`, `PG_A`, `PG_C`, `FAULT_C`, `FAULT_A1`, `FAULT_A2`,
  `FAULT_A3`, and `GND` exactly once each (`TP1-TP12`).
- Existing exact-board DRC evidence records zero violations, zero unconnected
  items, and zero schematic-parity items. Its pipeline command finished with
  return code 0. This corroborates connectivity but does not resolve the
  independent authority findings below.

# Findings

| ID | Severity | Finding | Exact evidence / required closure |
|---|---|---|---|
| PIN-P0-01 | P0 | The selected TPS2559 power-switch pinout and pin-1/package winding cannot receive the mandatory independent datasheet review from the supplied artifact set. This affects all three 2.849 A USB-A branches (`U4-U6`). | `02_parts/TPS2559DRCR/part.yaml` declares SHA-256 `d1b12fd...c57707`, but the part directory contains no PDF. The saved board uses C206199/Texas_DRC0010J with pins 2-5 on `5VA`, pin 6 `ILIM_Ax`, pins 7-9 `VBUSAx`, pin 10 `FAULT_Ax`, and pad 11 `GND`. P-PINMAP proves internal agreement only. Vendor the exact SHA-matching SLVSCL5A PDF and independently re-check the top-view winding, pin 1, every power pin, EN, ILIM, FAULT, and exposed pad. |
| PIN-P0-02 | P0 | The aggregate high-current eFuse `U9` lacks a SHA-bound local datasheet, so its RGE0024 pin-1 orientation, perimeter mapping, and split IN/GND PowerPAD identities are not independently reproducible from the allowed artifacts. | `02_parts/TPS259827ONRGET/part.yaml` has neither a `sha256` field nor a vendored PDF. The saved board has pin 25=`5VA_RAW` and pin 26=`GND`, with IN/OUT perimeter banks, and machine gates are internally green. Vendor and hash the exact SLVSEI3D authority, then independently re-check the top-view winding and especially pads 25/26 before order. |
| PIN-P0-03 | P0 | The unidirectional input TVS `D1` polarity is not independently anchored to a local SHA-bound authority. A reversed TVS is a destructive power-path defect class, so board/dossier agreement is insufficient. | Board: `D1.1=VIN`, `D1.2=GND`; dossier: SMBJ15A cathode=1/anode=2, but `02_parts/SMBJ15A/part.yaml` has `sha256: null` and no local PDF. Vendor/hash the exact Littelfuse series sheet and re-grade package band/pad 1 versus copper and CPL orientation. |
| PIN-P1-01 | P1 | Four active-looking module pins remain unexplained as explicit board NCs in the supplied pin authority: `U1.4 SW`, `U1.6 VCC`, `U2.2 SW`, and `U2.7 VCC` are on generated unconnected nets. | The saved board and netlist agree, and the TPSM PDFs are SHA-bound locally, but this time-bounded pass did not close the manufacturer instruction that these named pins must float rather than connect. Re-review the exact pin-functions table and record the required NC disposition before replacing this verdict. |
| PIN-P1-02 | P1 | `J1`'s +/− assignment is board-owned because the terminal manufacturer does not define contact polarity, but its dossier authority is not locally SHA-bound. | Saved board: pad 1=`BAT_POS`, pad 2=`GND`; part dossier states the vendor positions are non-polar and requires square pad-1 plus oversized operator-facing polarity silk. The electrical assignment is observed, but the exact drawing/marking evidence must be archived and rechecked at fabrication preview. |
| PIN-P2-01 | P2 | The 65 filled/capped 0.20 mm-drill sites and 118 ordinary sites are process-disjoint in the board metadata, but metadata is not fabrication execution. | Preserve the exact generated Type-VII order remark and verify the fabricator quote/stack-up acknowledges copper fill and cap for every protected family. Cross-section coupons and assembly inspection remain required. |

# Verdict

`DEFECTIVE / DO-NOT-ORDER`. No contradictory physical pad/net assignment was
found in the identities that could be independently closed, and the via/process
and declared via-boundary machine gates are green. The three P0 authority gaps
nevertheless prevent the mandatory independent check of high-current active
pin-1/winding/PowerPAD identities and destructive TVS polarity. Internal
netlist/board agreement cannot substitute for that check.

Loaded first-article validation remains required even after these findings are
closed: four-wire rail/drop measurements at the declared planes, simultaneous
USB loading, current-limit/fault timing, CC attach/detach behavior, loaded via
and package thermal rise, current sharing across U9 and U4-U6 lands/via banks,
converter/startup waveforms, connector heating, and destructive inspection or
coupon cross-section of filled/capped via-in-pad processing. This review does
not authorize an order.
