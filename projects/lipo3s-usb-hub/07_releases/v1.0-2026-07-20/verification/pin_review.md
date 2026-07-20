# Fresh-context pin review — lipo3s-usb-hub v1.0

Three independent fresh-context agents (no design context) derived the expected pinout
from the datasheet FIGURES and judged every board net electrically, per
`kicad-pcb/references/pin-review-protocol.md`. Dossiers: `06_build/pin_review/`.
All three verdicts: **PASS**.

## Group 1 — XT60 input polarity + reverse-polarity FETs (J1, Q1, Q2) — PASS

- **J1 XT60PW-M**: verified from the footprint geometry itself (canonical
  AMASS_XT60PW-M, no mirror/rotation on the model): pad 1 sits under silk "−", pad 2
  under silk "+". Board binds **pad 1 → GND, pad 2 → VBATT_RAW**. The dangerous
  reversed-XT60 case is ruled out. PASS.
- **Q1/Q2 CSD18543Q3A** (FET pinout from SLPS432 Top View: 1/2/3 = Source, 4 = Gate,
  5–8+EP = Drain): Q1 source → VBATT_F (battery side), Q2 source → VSW (load side),
  both drains common at **FE_MID** (correct back-to-back common-drain reverse block),
  both gates driven by U1 (DG_FE, HG_FE). PASS.

## Group 2 — buck controller + ideal-diode front-end (U2 LM5145, U1 LM74800) — PASS

- **U2 LM5145** (VQFN-20, pinout from Fig 6-1 / Table 6-1, winding CCW, not mirrored):
  all 21 pads PASS — VIN(20)→VSW, SW(19)→SW_A, HO/LO gate drives, BST/VCC/FB/COMP/EN/
  RT/SS/ILIM correct, PGND/AGND + center EP(21)→GND, PGOOD(10)→PGOODA_RAW. Pin 15 "EP"
  is datasheet-isolated → floating correct; pin 8 SYNCIN=GND selects diode-emulation
  (DCM), valid.
- **U1 LM74800-Q1** (WSON-12, not mirrored): all pins PASS — DGATE/HGATE→DG_FE/HG_FE,
  anode/VSNS→VBATT_F, OUT→VSW, VS + cathode→FE_MID, OV/EN ladder→FE_OV/FE_EN/FE_LAD,
  CAP→FE_CAP.
  - **U1 exposed pad (pad 13) floating is CORRECT and REQUIRED**: datasheet Table 6-1
    RTN thermal pad — "Leave exposed pad floating. Do NOT connect to GND plane." Our
    board pad 13 has no net = compliant. (This resolves the gen_tscircuit parity note
    about U1.13 — it is a supposed-to-float thermal pad, not an error.)
- Advisory (satisfied): U3's EN is driven by U2's open-drain PGOOD_A — a pull-up
  exists (R21 20k from 5V_C to PGOODA_RAW), so the sequencing works.

## Group 3 — USB-C source + per-port limiter (J5 USB4105, U4 TPS2557) — PASS

- **J5 USB4105-GF-A** (16-pin, pinout from GCT drawing): all 17 pads PASS — four VBUS
  (A4/A9/B4/B9)→5V_C, four GND + shell→GND, **CC1(A5) / CC2(B5) not swapped**, D+/D−
  pairs (A6/A7/B6/B7) shorted to DCPC, SBU (A8/B8) floating.
  - **CC direction verified as SOURCE**: R19/R20 (10k) pull CC1/CC2 UP to 5V_C (Rp),
    not down to GND (Rd) — correct source advertising 3 A default. The
    source-vs-sink-inversion bug class is ruled out.
- **U4 TPS2557** (VSON-8, not mirrored): all pins PASS — IN(2/3)→5V_A, EN(4, active-high)
  →5V_A (permanently enabled), ILIM(5)→ILIM1 (24.3k→GND, ~2.5A, within TI 20k–187k
  range), OUT(6/7)→VBUS1, GND(1)+EP(9)→GND, FAULT(8) open-drain floating. Current flows
  IN→OUT (not reversed).
  - Advisory (documented): the USB4105 datasheet rates VBUS pins **5.0 A collectively**;
    the 6 A capability is ~20% over the connector's VBUS rating. Mitigated — advertised
    current is 3 A (compliant loads stay ≤3 A), 6 A is headroom across 4 VBUS + 4 GND
    pads. Recorded in ORDER_README and DETAIL_DESIGN as a derating consideration.

## Verdict

All three groups PASS. No pin swaps, no mirrored footprints, no CC source/sink
inversion, no reversed current paths, correct XT60 polarity. Two advisories (USB-C
6A-vs-5A connector derating; already-satisfied PGOOD pull-up) documented, neither a
blocker.
