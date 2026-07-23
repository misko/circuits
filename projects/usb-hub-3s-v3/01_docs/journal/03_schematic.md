# Journal — 03 schematic (usb-hub-3s-v3)

## 2026-07-22 — schematic delta (drop the PD cell) + GATE GREEN
- did: v3 = v2 MINUS the USB-C PD cell (ADR-0001). Edited
  `03_tscircuit/src/usb_hub_3s_v2.tsx` (board name kept for source continuity):
  removed U1 (TPS25740A PD PHY), Q6/Q7 pass FETs, RS3 (5mR sense) and every
  PD-config passive (R23-R26, C44-C48, C51) with their nets (RSNS, PDSRC,
  PDGATE, GDNG, DSCG_N, HIPWR, PSEL, DVDD, VAUX, VTX, ISNS/VPWR, VBUSC).
  Rewired the USB-C port to the plain form: J5 VBUS pads (A4/A9/B4/B9) tie to
  the 5VC buck rail directly (VBUS == 5VC), two 10k CC Rp pull-ups (R28/R29,
  JLC C25744) advertise source-present, kept U12 data ESD + R27 DCP short +
  C49/C50 VBUS bulk. Updated manifest 112 -> 100 components; padmap unchanged.
- result: **SCHEMATIC GATE GREEN (grid mode — mandatory, layout mode net-merges
  BOOT_A/VCC_A):**
  - tsx_preflight (S8/TSX-PRE): PASS.
  - tsci build: 100 components (100 with FPID), 322 pins.
  - **ERC: 0 errors** / 289 warnings (baselined classes).
  - **count_parity (S-COUNT): manifest 100 == circuit.json 100 == kicad_sch 100
    == netlist 100.** PASS.
  - net check: 5VC = {C29-C32, C49/C50, J5.A4/A9/B4/B9, L2.2, R12.1, R28.2/R29.2,
    U11.10, U12.5}; CC1={J5.A5,R28.1}, CC2={J5.B5,R29.1}; VBUSC/RSNS/PDSRC ABSENT.
  - E-ADR invariants (ADR-0001): no PD controller on the board (U1 gone);
    J5 VBUS pins on 5VC; CC1/CC2 each on an Rp pull-up. All hold.
- sourced: 10k 0402 CC pull-up = JLC C25744 (basic part; order-day stock recheck).
- commit: 6ea428d.
- next: placement (drop PD anchors/zones, 5VC pour to J5), then route.
