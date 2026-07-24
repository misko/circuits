subject: crow-recorder-central-v2 v1.1 staging (pre-seal, pre-LV-fix bytes)
date: 2026-07-24
reviewer: pin-review (zero-context sub-agent, Fable 5 medium)
context-given: release-archive-only + 01_docs design docs + 02_parts + curated (journals/STATUS/08_reviews excluded)
verdict: PASS

NOTE (board lead): the LV-strap finding below was filed P2-escalates-P0
pending a datasheet check; the check was done pre-seal (XU316-1024-TQ128 ds
v2.0.0 §4.4/§4.8/§15.1) and CONFIRMED P0 — straps are IOB-bank pins, AMR
VDDIO+0.5 = 2.3V, not 3.3V-tolerant. Escalated to PR2-P0-1 and fixed
(float-strap) before seal; see DISPOSITIONS.md. Body VERBATIM below.

---

All checks complete. Findings below.

## Pin review — crow_recorder_central_v2 v1.1 (staged), netlist vs part.yaml

Everything measured from `source/crow_recorder_central_v2.net` (sexpr-parsed, ref.pin -> net) and `source/crow_recorder_central_v2.kicad_pcb` (pcbnew), against `02_parts/*/part.yaml`.

**Verified-correct (measured, not assumed):**

| Item | Measured result |
|---|---|
| U1 supplies | 0V9 on exactly the 15 core-VDD pins {5,11,14,18,39,45,50,54,68,85,95,104,105,106,113}; VDDIOL{10,17}/VDDIOR{72,89}/VDDIOT{109,121}=3V3; VDDIOB18{35,56}=1V8; VSS 30 + EP 129=GND; PLL_AVDD 41 via L_pll from 0V9, PLL_AGND 42=GND; MIPI_VDD18(24)/VDD09(27)=GND (tie-if-unused per yaml) |
| U1 USB | 59=USB_DN, 60=USB_DP (matches yaml); 61=USB_VDD33 (FB_u33 from 3V3), 62=USB_VDD18 (FB_u18 from 1V8); pin 55 NC unconnected; VBUS sensed on GPIO 23 via R_vb1/R_vb2 divider |
| U1 QSPI vs W25Q16 | CS pin2->U5.1, CLK pin4->U5.6, D0 127->U5.5(DI), D1 128->U5.2(DO), D2 1->U5.3(WP), D3 3->U5.7(HOLD); U5.8 VCC=3V3=VDDIOL. All six hardcoded boot pins correct |
| U1 RST/JTAG/xtal | 38=RST_N (R_rst pull to 1V8, correct bank level), 36/37/44/51=TDI/TDO/TMS/TCK, 33/34=XOUT/XIN with Rf/Rd/CL1-2/Y1 |
| U2/U3 PCM1865 | All 30 pins match yaml incl. the clock trap: MCLK lands on SCKI(15) via buffered branches (U4 NC7NZ34: 1Y->MCLK_B1->R_mck1->U2.15, 2Y->MCLK_B2->R_mck2->U3.15); XI(10)=GND, XO(9) open; AD(25): U2=GND(0x4A), U3=3V3(0x4B); MD0(26)=GND (I2C); AVDD=3V3A, DVDD/IOVDD=3V3 split correct; diff inputs ADC1-8 P/M on the right P/M pads |
| U7/U8 AP61102 | U7: FB1(1), GND(2), VIN=5V(3), SW1(4), EN=5V(5), PG_3V3(6). U8: FB2/GND/5V/SW2, EN(5)=PG_3V3 (sequencing per ADR-0005), PG(6) NC. R_pg pulls PG_3V3 to 3V3 (open-drain pull-up present) |
| U9 TLV70018 | IN(1)=3V3, GND(2), EN(3)=3V3, NC(4) open, OUT(5)=1V8 |
| U10 XC6227 | CE(1)=5V (active-high tie), VSS(2)=GND, NC(3) open, VIN(4)=5V, VOUT(5)=3V3A |
| Q1 AO3401A | G(1)=GATE_RPP (RG1 to GND), S(2)=5V, D(3)=VIN_RAW — matches the confirmed as-built orientation exactly |
| Q2 AO3400A | G(1)=BEEP_G (R_bg1/R_bg2/C_bg slow-edge RC), S(2)=GND, D(3)=BEEP_RETURN |
| D1 SMAJ5.0A | K(1)=VIN_RAW, A(2)=GND — correct unidirectional orientation; input chain J1.1(TIP)->JACK_IN->F_IN->VIN_RAW |
| D_USB TPD4EUSB30 | D1+(1)=USB_DP, D1-(2)=USB_DN, GND(3,8)=GND, NC pins 4-7,9,10 open |
| J2 USB-C | DP on 4 and 12, DN on 5 and 13; VBUS 2,7,10,15; GND 1,8,9,16,17; CC1(3)/CC2(11) separate nets each with own 5.1k Rd to GND |
| J3-J10 RJ45 | All 8 ports: 1=AUDIOnP, 2=AUDIOnM, 3=PLUS5V_BEEP, 6=BEEP_RETURN, 4&7=P5VA_n (per-port fused F1-F8 from 5V), 5&8=GND, shield(13)=GND |
| U1 EP thermal vias | Exactly 16 vias within EP footprint, all net GND, all 0.30mm/0.15mm — matches datasheet 14.4 spec |

**Findings:**

| Finding | Severity | Evidence |
|---|---|---|
| LV strap pins tied hard to 3V3: U1.40/43/52 (LV_L_N/LV_T_N/LV_R_N) = net 3V3, no series R. These pins sit on bank IOB, whose supply (VDDIOB18) part.yaml states is "1.8V FIXED, AMR 1.98V". part.yaml says only "tie HIGH(or float)=3V3 mode" without stating the legal HIGH level. If the strap pins inherit the IOB bank abs-max, a hard 3.3V tie is an overstress; if they are strap-tolerant, this is fine. Mode selection itself is consistent (VDDIOL/R/T all = 3V3). | P2 (escalates to P0 if datasheet limits strap-high to IOB levels) | Netlist U1.40=3V3, U1.43=3V3, U1.52=3V3 (direct net membership); part.yaml pins 40/43/52 "bank IOB", limits.vddiob18 "AMR 1.98". Recommend one datasheet check (Fig.2 / strap electrical spec) before seal — outside what the provided part facts can settle |
| U7 (3V3 buck) EN tied to VIN (U7.5=5V) → PFM at light load, not forced-PWM | P2 (accepted deviation, not a defect) | ADR-0005 amendment explicitly documents and accepts this (analog rail comes from U10 LDO; U8 core buck IS in forced-PWM via EN=PG_3V3). However 01_docs/DETAIL_DESIGN.md line 15 still claims "EN: forced-PWM ... for lower ripple" — stale doc line vs as-built |
| U1.58 USB_ID unconnected | P2 (informational) | Netlist U1.58 = unconnected; yaml calls it OTG ID input, no tie requirement stated; device-only USB |

No P0/P1 pin-binding defects found: every mandated pin->net read matches its part.yaml fact.

**PIN REVIEW: PASS** — all critical bindings (U1 supplies/USB/QSPI/RST, U2/U3 clock-trap and address straps, buck SW/FB/EN, LDOs, Q1/Q2 polarity, D1/D_USB orientation, J1/J2/J3-J10 pinouts, 16x GND EP vias) measured correct against part facts. One pre-seal follow-up recommended: confirm from the XU316 datasheet that LV_x_N straps tolerate a hard 3.3V tie (P2 above); plus the one stale DETAIL_DESIGN.md forced-PWM sentence.