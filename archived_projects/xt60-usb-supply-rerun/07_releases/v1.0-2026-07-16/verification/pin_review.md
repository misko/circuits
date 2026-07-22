# Fresh-context pin review — xt60-usb-supply

Reviewer: independent agent, no design-session context. Method per
`skills/kicad-pcb/references/pin-review-protocol.md`: datasheet pinout figures
rendered with pdftoppm and read first; expectations derived from the datasheet,
then compared to the dossier. Polarized 2-pad parts checked by reading the
KiCad footprint silkscreen geometry directly plus pad nets from
`04_kicad/xt60-usb-supply.kicad_pcb` via pcbnew.

## Verdict table

| Part | MPN | Verdict |
|---|---|---|
| U1 | SY8368QNC (buck A) | PASS |
| U2 | SY8368QNC (buck C) | PASS |
| U3 | USBLC6-2SC6 (port 1 ESD) | PASS |
| U4 | USBLC6-2SC6 (port 2 ESD) | PASS |
| U5 | USBLC6-2SC6 (port 3 ESD) | PASS |
| U6 | USBLC6-2SC6 (CC ESD) | PASS |
| J2 | XY-AF90-WJDG (USB-A) | PASS (note 1) |
| J3 | XY-AF90-WJDG (USB-A) | PASS (note 1) |
| J4 | XY-AF90-WJDG (USB-A) | PASS (note 1) |
| J5 | TYPE-C-31-M-12A (USB-C) | PASS |
| J1 | XT60PW-M | PASS |
| D1 | SMBJ15A | PASS |
| CB1 | MA25V100M6x6 | PASS |
| CB2 | MA25V100M6x6 | PASS |
| LED1-3 | KT-0805G | PASS |

No FAILs. Note 1 (J2-J4) is an evidence-provenance remark, not a blocker.

## U1, U2 — SY8368QNC, QFN3x3-10 FC

Datasheet: AN_SY8368 Rev 0.9B, Pinout (top view) p.2; abs max p.3.

Datasheet-derived expectation (top view): pins 1-6 in a row across the TOP,
left-to-right 1=EN, 2=PG, 3=ILMT, 4=FB, 5=VC(C), 6=BS; pin 7 small pad upper
RIGHT (IN), pin 8 large pad lower right (IN), pin 9 center/bottom GND, pin 10
left LX. That numbering runs 1→6 L-to-R along the top then down the right
side = CW in top view. Dossier: N-side pads 1..6 in ascending x with functions
EN/PG/ILMT/FB/VCC/BS; pad 7 E at (+1.09,-0.64); pad 8 large E at (+0.96,+0.70);
pad 9 GND center/left/bottom; pad 10 LX W at (-1.01,+0.30); computed winding
CW. Exact match, no mirror. Pitch of pads 1-6 ~0.45 mm, consistent with the
p.2 figure's row.

Per-pin electrical, both instances (pairwise symmetric — every pin maps to the
same KIND of net on U1/U2):

- pin 1 EN → VBAT_P: "pull high to turn on, do not leave floating"; abs max
  for EN is 30 V (p.3), 3S max 12.6 V — OK.
- pin 2 PG → NC_U1_PG/NC_U2_PG: open-drain indicator, unused/floating — OK.
- pin 3 ILMT → GND: pin table p.2: "current limit is set to 8A ... when this
  pin is pull low" — matches the stated 8 A intent. ILMT abs max 4 V; tied to
  GND, OK.
- pin 4 FB → FB_A/FB_C: divider net, not a rail — OK.
- pin 5 VCC → VCC_A/VCC_C: internal 3.3 V LDO output, dedicated bypass net —
  OK.
- pin 6 BS → BST_A/BST_C: bootstrap net — OK.
- pins 7,8 IN → VBAT_P: input pins on the battery rail; recommended supply
  4-28 V covers 3S — OK.
- pin 9 GND (all three pad geometries) → GND — OK.
- pin 10 LX → SW_A/SW_C: switch node — OK.

VERDICT: PASS (U1), PASS (U2).

## U3, U4, U5, U6 — USBLC6-2SC6, SOT-23-6

Datasheet: Doc ID 11265 Rev 5, Figure 1 "Functional diagram (top view)", p.1.

Datasheet-derived expectation (top view): left side top-to-bottom 1=I/O1,
2=GND, 3=I/O2; right side bottom-to-top 4=I/O2, 5=VBUS, 6=I/O1 — standard
SOT-23-6, CCW winding, pin 1 top-left. All four dossiers: pads 1/2/3 on W in
descending order, 4 E bottom, 5 E middle, 6 E top, computed winding CCW.
Match, no mirror. Pins 1&6 are the same internal line (I/O1), 3&4 the same
(I/O2) — flow-through routing.

- U3: I/O1(1,6)=DCP1, I/O2(3,4)=DCP1, GND(2)=GND, VBUS(5)=5V_A — OK. Both
  I/O lines on one net is electrically valid (they are separate diode pairs
  to the same clamp rails) and matches BC1.2 DCP (D+ shorted to D-).
- U4: same structure on DCP2 / 5V_A — OK.
- U5: same structure on DCP3 / 5V_A — OK.
- U6: I/O1(1,6)=CC1, I/O2(3,4)=CC2, GND=GND, VBUS(5)=5V_C — OK. CC levels
  are ≤5 V (Rp pull-ups to 5V_C), within the VBUS clamp reference.

VERDICT: PASS (U3, U4, U5, U6).

## J2, J3, J4 — USB-A receptacles (XY-AF90-WJDG)

The dossiers say "MPN unknown / no datasheet", but the part is documented at
`02_parts/XY-AF90-WJDG/` (footprint field names the exact library footprint
used on the board, Connector_USB:USB_A_Stewart_SS-52100-001_Horizontal, and
the yaml records a pad-by-pad hole-pattern match to the Rev A drawing:
4x Dia0.92 at 2.50/2.00/2.50 mm plus 2x Dia2.30 shells 13.14 mm apart, 2.71 mm
behind the pin row — the dossier pad table shows exactly this geometry).

Expectation: USB-A standard pinout 1=VBUS, 2=D-, 3=D+, 4=GND, shell=GND.
Board nets: pin 1=5V_A, pins 2,3=DCPn (per-port shorted D+/D- — BC1.2 DCP, so
even a 2/3 transposition would be electrically nil), pin 4=GND, both SH=GND.
All three jacks identical (pairwise symmetry OK, DCP1/DCP2/DCP3 respectively).

Note 1: the XY Rev A drawing does not print pin numbers/signals on the
connector views (recorded in the part.yaml gotcha); the 1=VBUS map rests on
the USB-A standard contact order, the Stewart-datasheet-verified KiCad
library footprint, and the LCSC vendor symbol (VCC,D-,D+,GND on 1..4) — three
independent sources agreeing. Residual risk is a pin1/pin4 (VBUS/GND) end
swap, which the symmetric shell holes cannot geometrically exclude; the yaml
itself flags "sanity-check VBUS-to-shell orientation before powering". Do the
one-second meter check (shell-to-pin4 continuity) at bring-up.

VERDICT: PASS (J2, J3, J4), with the bring-up check above.

## J5 — TYPE-C-31-M-12A USB-C 16P receptacle

Datasheet: HRO drawing Rev A 2022-10-26, sheet 1: SIGNAL NAME table +stake
"RECOMMEND P.C.B LAYOUT" pad row.

Datasheet-derived expectation, pad row left-to-right (top view, component
side): A1/B12, A4/B9, B8, A5, B7, A6, A7, B6, A8, B5, B4/A9, B1/A12; signal
table: A1/B12/A12/B1=GND, A4/B9/A9/B4=VBUS, A5=CC1, B5=CC2, A6=DP1, A7=DN1,
B6=DP2, B7=DN2, A8=SBU1, B8=SBU2. Dossier x-order: -3.25 A1,B12 / -2.45 A4,B9 /
-1.75 B8 / -1.25 A5 / -0.75 B7 / -0.25 A6 / +0.25 A7 / +0.75 B6 / +1.25 A8 /
+1.75 B5 / +2.45 A9,B4 / +3.25 B1,A12. Exact positional and functional match —
not mirrored (a mirror would put CC1 at +1.25).

- GND pads (A1,A12,B1,B12) → GND — OK.
- VBUS pads (A4,A9,B4,B9) → 5V_C — OK (connector rated 6 A/20 V per note 4;
  a 5 V buck rail is fine).
- A5 CC1 → CC1, B5 CC2 → CC2, each with Rp to 5V_C (source-side advertising)
  and ESD via U6 — OK.
- A6,A7,B6,B7 (DP1,DN1,DP2,DN2) → all on DCPC: deliberate BC1.2 DCP short
  across both orientations' D pairs; only one pair mates at a time — OK.
- A8/B8 SBU → NC nets — OK (SBU unused in a 5 V source).
- 4 shield pads → GND — OK.

VERDICT: PASS.

## J1 — XT60PW-M battery connector

part.yaml evidence chain verified directly: the installed KiCad footprint
`AMASS_XT60PW-M_1x02_P7.20mm_Horizontal.kicad_mod` silkscreens "-" at
(-2.8, 2.5) beside pad 1 at (0,0) and "+" at (9.5, 2.5) beside pad 2 at
(7.2, 0) — pad 1 is the NEGATIVE blade. Board (pcbnew): J1 pad 1 = GND,
pad 2 = VBAT_RAW (positive raw battery net, pre-protection), mounting pegs
unconnected. Correct polarity — this is the exact failure mode the yaml's
gotcha warns about (shipped reversed once elsewhere), and here it is right.

VERDICT: PASS.

## D1 — SMBJ15A TVS (unidirectional)

D_SMB footprint geometry read directly: extra silkscreen bar at x=-3.66 wraps
pad 1 (x=-2.15) → pad 1 = cathode band end. Datasheet (Littelfuse SMBJ v4):
unidirectional, cathode band; for a positive-rail clamp the cathode goes to
the rail, anode to GND. Board: pad 1 = VBAT_P, pad 2 = GND. Correct. VR 15 V
> 12.6 V 3S max; clamp VC 24.4 V < SY8368 30 V abs max.

VERDICT: PASS.

## CB1, CB2 — MA25V100M6x6 polymer caps

CP_Elec_6.3x5.9 footprint geometry read directly: "+" silkscreen cross
(lines crossing at x≈-4.04) and chamfered outline corners sit on the pad-1
side (pad 1 at x=-2.8) → pad 1 = positive. Board: CB1 pad 1 = VBAT_P,
pad 2 = GND; CB2 identical. Correct; 25 V rating > 12.6 V.

VERDICT: PASS (CB1, CB2).

## LED1, LED2, LED3 — KT-0805G

LED_0805_2012Metric footprint geometry read directly: silkscreen bar at
x=-1.685 beside pad 1 (x=-0.9375) → pad 1 = cathode (KiCad LED convention).
Board: all three have pad 1 = GND (cathode to ground) and pad 2 = LEDn_A
(anode drive net through a resistor, per net naming). Correct. The part.yaml
correctly records the vendor-numbering trap (vendor terminal 1 = anode) and
keys pins to the KiCad footprint, which is what the board and CPL use.

VERDICT: PASS (LED1, LED2, LED3).

---

## Summary

15/15 part positions PASS. No FAIL, no open QUESTION. One bring-up action
carried forward from the J2-J4 finding: meter-check USB-A shell-to-pin-4
continuity (confirms VBUS/GND end orientation) before first power, since the
XY-AF90-WJDG drawing itself does not label pin signals.
