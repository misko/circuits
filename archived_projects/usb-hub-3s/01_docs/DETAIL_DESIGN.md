# usb-hub-3s — detail design (every value derived)

Sources: LM5116 SNVS499I (cached 02_parts/LM5116MHX/), IP6559 V1.4
(02_parts/IP6559-C/), TPS2556/7 SLVS931B, TPS2513A SLVSBY8. Manufacturer
worked designs adopted per canon M6; deviations derived below.
Refdes in this document are the AS-BUILT netlist refdes (v1.1 doc pass,
reviews X10/X15 — the v1.0 doc used planning refdes R100–R106 that never
existed on the board).

## 1. Input protection chain (ADR 0001)

- **F1**: MINI blade fuse 20 A + THT holder (Keystone 3568 clips). Worst
  input ≈ 15.5 A (100 W PD + 30 W USB-A at Vin 9.0 V, eff 0.93); wiring/
  pours sized 16 A continuous. **Exact fuse (v1.1, X1/X13): Littelfuse
  0297020.WXNV** — 32 VDC, IR 1000 A, I²t 380 A²s; full time-current
  coordination vs load/copper/D1/Q1 in ADR-0001 Amendment v1.1
  (02_parts/0297020WXNV/part.yaml carries the quoted table).
- **Q1** reverse-polarity P-FET: drain = VBAT_F (battery side), source = VIN,
  body diode conducts battery→load at first contact, then Vgs ≈ −VIN (−8.8
  to −12.6 V) enhances it. R13 100 kΩ gate→GND; D5 BZT52C12 zener S→G
  clamps |Vgs| ≤ 12 V (spike margin; abs max ±20 V). FET: ≥30 V, Rds(on)
  ≤ 5 mΩ @ Vgs −10 V, Id ≥ 30 A, DFN5x6/PowerPAK. Dissipation ≤ 15.5² ×
  5 mΩ = 1.2 W — pour + thermal vias (R-THERM).
- **D1** SMBJ15A across VIN AFTER Q1 (v1.1: the v1.0 netlist had it on
  VBAT_F before Q1, making reverse battery a sacrificial crowbar through F1
  — review X1/X29; moved to VIN so a reversal is non-destructive, ADR 0001
  amendment): standoff 15 V > 12.6 V; clamp ≤ 24.4 V < IP6559 VIN abs 34 V,
  < FET 30 V. Hot-plug clamping is equivalent through the enhanced Q1
  (body diode conducts first contact; TVS sees the spike via Q1 either way).
- **Bulk**: 2 × 100 µF ≥ 35 V low-impedance electrolytic/polymer at VIN entry
  (IP6559 BOM asks ≥35 V electrolytic; LM5116 input filter separate below).

## 2. Board UVLO (ADR 0001, amended here — single mechanism)

LM5116's precision UVLO pin is the board's ONE undervoltage authority:

- Threshold 1.215 V rising, pin hysteresis 0.1 V, pin pull-up 5.4 µA (DS §6.3.3).
- Divider R5 = 49.9 kΩ 1% (VIN→UVLO), R6 = 6.98 kΩ 1% (UVLO→GND):
  K = 56.88/6.98 = 8.149, Rt∥Rb = 6.12 kΩ → 5.4 µA offset 33.1 mV.
  Typicals: V_rise = 8.149 × (1.215 − 0.0331) = **9.63 V**;
  V_fall = 8.149 × (1.115 − 0.0331) = **8.82 V** (2.94 V/cell).
- **Worst-case corner band (v1.1, reviews X7/X14 — SNVS499I EC table:
  threshold 1.170/1.215/1.262 V min/typ/max; hysteresis 0.1 V and pull-up
  5.4 µA are TYP-ONLY specs; resistors 1%):**
  - falling: K_min·(1.170 − 0.1 − 33 mV) = 8.007 × 1.037 = **8.30 V**
    (2.77 V/cell) … K_max·(1.262 − 0.1 − 33 mV) = 8.293 × 1.129 = **9.36 V**.
    With ±30 % engineering bounds on the untoleranced hyst/pull-up the floor
    widens to ~7.98 V (2.66 V/cell).
  - rising: 8.007 × (1.170 − 0.033) = **9.10 V** … 8.293 × (1.262 − 0.023)
    = **10.27 V**.
  - Consequence: this board protects the PACK AVERAGE at a worst-case floor
    of ~2.77 V/cell and is blind to cell imbalance. **The input REQUIRES a
    pack with its own BMS/balance protection** — silk says "PROTECTED 3S
    PACK ONLY"; ORDER_README carries the requirement.
- IP6559 EN chain: 5VA presence gates the PD stage. R21 10 kΩ 5VA→EN(pin 5),
  R22 10 kΩ EN→GND → EN = 2.5 V when 5VA up (≤ VCCIO 3.3 V, above logic
  high), 0 V when down; the 10 kΩ pull-down overrides the chip's weak internal
  pull-up when 5VA is absent. Consequence (documented): any LM5116 shutdown
  (UVLO, hiccup) also disables the C port — protective, accepted.
- Residual standby below UVLO (v1.1 correction, review X12): R9 100 kΩ holds
  LM5116 EN HIGH, so below UVLO the part is in STANDBY (VCC regulator
  RUNNING, switching disabled — SNVS499I UVLO pin description), NOT the
  10 µA EN-low shutdown. The DS does not spec standby current in this state;
  the nearest bound is IBIAS 5–7 mA (operating, no gate load). Realistic
  budget: LM5116 standby ~1–5 mA + IP6559 ~200 µA + dividers ~280 µA →
  **plausibly 1.5–5 mA, not the 0.5 mA v1.0 claimed**. A 2 Ah pack cut off
  at ~10–15 % SoC reaches deep over-discharge in DAYS. ORDER_README: measure
  the real below-UVLO drain at first power and NEVER store the pack
  connected. v2 candidate (ADR 0001 amendment): drive EN from the divider
  (true 10 µA shutdown) or a hard P-FET cutoff.

## 3. 5VA buck — LM5116 (5 V / 7 A cont, 7.5 A burst), TI 5V/7A design adopted

| Item | Value | Derivation |
|---|---|---|
| Fsw | 250 kHz | RT = (4 µs − 450 ns)/284 pF = 12.5 k → **RT 12.4 kΩ 1%** (DS eq.1) |
| L2 | 6.8 µH, Isat ≥ 12 A, DCR ≤ 12 mΩ | TI design 6 µH/16.5 A; ripple ~2.4 App at 12.6 Vin |
| Rs (R_cs) | 10 mΩ 1%, 2010/2512 | TI 7 A design value; limit ≈ 11 A peak |
| C_RAMP | 330 pF COG | gm·L/(A·Rs) = 5 µ×6.8 µ/(10×0.01) = 340 pF (DS eq.3) |
| FB divider | RFB2 3.74 kΩ / RFB1 1.21 kΩ 1% | 1.215 × 4.95/1.21 = 4.97 V (DS §7.2.2.11) |
| Comp | RCOMP 18 kΩ, CCOMP 3.3 nF, CHF 100 pF | TI design (zero 2.7 kHz) |
| CSS | 10 nF | 1.2 ms soft start (DS eq.23) |
| CHB (boot) | 1 µF 16 V + **D4 boot diode VCC→HB** | DS §7.2.2.9 + ledger gotcha (no internal boot diode) |
| VCC cap | 1 µF | DS |
| VCCX | **GND** (unused) | ledger: never open; internal 7.4 V drive, generic-FET-safe |
| DEMB | GND (diode emulation ON = no sink at light load) | forced-PWM not needed |
| Cin | 4 × 10 µF 25 V X7R 1210 + 0.1 µF | Irms ≥ Iout/2 = 3.5 A; ΔVin ≈ 7/(4·250k·20µ_eff) = 0.35 V |
| Cout | **as built: 4 × 100 µF 16 V X5R 1210 (EMK325ABJ107MM, C90143)** | v1.1 reconciliation (review X10): TI's design used 5×100 µF 6.3 V; the BOM part is 16 V X5R 1210. DC-bias derating at 5 V ≈ −35…−45 % (Taiyo Yuden EMK325 curve class) → C_eff ≈ 4 × 55–65 µF ≈ **220–260 µF**, vs TI's 6.3 V X6S at 5 V ≈ 5 × ~50 µF ≈ 250 µF — equivalent effective capacitance, higher voltage margin. Ripple/transient budget unchanged. |
| Q2/Q3 | NFET 30–40 V, Rds ≤ 8 mΩ @4.5 V, Qg ≤ 30 nC, SO-8/DFN5x6 | TI used Si7850DP 60 V (Vin 60); ours ≤12.6 V |
| CS filter | CS/CSG routed Kelvin to Rs; R 0Ω pair per TI fig | |

Duty 5/12.6–5/9 = 0.40–0.56 — well inside limits.

## 4. USB-A port channel × 3 (ADR 0002)

- **TPS2557DRBR** per port: IN = 5VA, OUT = VBUSAn, EN = 5VA (always on),
  FAULT float (no MCU), ILIM: IOSmin = 127981/R^1.0708, IOSmax = 99038/R^0.947
  (DS §10.2.1.2.2). **RILIM = 36.5 kΩ 1%** → IOS = 2.72–3.29 A:
  passes 2.5 A burst, protects at ~3 A. ✓
- **TPS2513ADBVR** (dual channel, the A variant — C473910; the non-A part
  loses the Apple 2.4 A divider mode, review X10): U6 serves ports 1+2
  (DP1/DM1→J2, DP2/DM2→J3), U7 serves port 3 (DP1/DM1→J4; DP2/DM2
  no-connect flags). IN = 5VA + 0.1 µF each.
- Per port: Cout = 22 µF 10 V X5R + 0.1 µF on VBUSAn; USBLC6-2SC6 ESD array
  (I/O1 = D+, I/O2 = D−, VBUS pin = VBUSAn, GND) at the connector.
- Port copper: VBUSAn ≥ 3 A → 1 mm floor + pour.

## 5. USB-C PD stage — IP6559-C (ADR 0003/0004), Fig. 8+9 adopted

| Item | Value | Derivation |
|---|---|---|
| R_s_in (RS2) | 5 mΩ 1% ≤100 ppm alloy 2512 | DS Fig.8/BOM; input CC limit datasheet-nominal |
| R_s_out (RS3) | 5 mΩ 1% ≤100 ppm alloy 2512 | DS; output limits 3 A@5/9/12 V, 5 A@20 V |
| Sense filters | R14, R15 10 Ω + C20 1 µF (CSP2/CSN2); R18, R19 10 Ω + C25 1 µF (CSP1/CSN1) | DS Fig.8 |
| PCIN/PCON | direct taps at the shunt outer ends | DS §13.5 Kelvin rule; **v1.1 (X19): taps are Kelvin STUBS off the shunt pad ends, routed as diff pairs away from LX** |
| Q4(HG2)/Q5(LG2)/Q6(HG1)/Q7(LG1) | see ADR 0007 (v1.1 FET/TVS coordination — 30 V AON6354 replaced) | DS MOSFET Selection + clamp coordination (reviews X3, X18) |
| Gate R | **R28(HG2→Q4.G), R29(LG2→Q5.G), R30(HG1→Q6.G), R31(LG1→Q7.G) — 0 Ω 0603, POPULATED, placed at the gates** | DS Fig.7 tuning slots; v1.1 (X4/X24 — v1.0 promised them and had none) |
| Snubbers | R16, R17 2 Ω + C23, C24 1 nF at LX2, LX1 | DS Fig.8 |
| BST | C21, C22 100 nF 16 V (BST2–LX2, BST1–LX1) | DS Fig.8 |
| D6, D7 (LX TVS) | see ADR 0007 (per-node clamp coordination replaces the blanket SMAJ30A) | reviews X3 (clamp above FET rating) |
| L1 | see ADR 0008 (Irms margin at the 100 W / low-VIN corner) | I_L(peak)boost = 20×5/(9×0.95) + 9×11/(2×20×250k×10µ) = 12.7 A; ×1.2 (DS rule); reviews X5 |
| Cin (stage, v1.1 — X18/X27) | **AT the cell**: C44 100 µF 35 V polymer + C3, C45 2×10 µF 25 V X7R 1210 + C4 100 nF on VIN; **bridge-rail HF bank**: C46, C47 2×10 µF + C48 100 nF on VIN_S–GND hard at Q4/Q5 | DS BOM + ripple Irms ≈ 5 A; ceramics on BOTH sides of RS2 keep the shunt out of the HF loop |
| Cout (stage, v1.1 — X18) | **bridge-rail HF bank**: C49, C50 2×10 µF 25 V + C51 100 nF on VOUT_PDS–GND hard at Q6/Q7; then RS3 → C26 100 µF 25 V polymer + C27 100 nF on VOUT_PD | DS BOM; same shunt-out-of-loop rule |
| Q8 path NFET | same part as Q4–Q7 (ADR 0007); D=VOUT_PD, S=VBUSC, G=VOUT2G | DS Fig.8 (port-2 path used in single-C); backfeed disposition X30 |
| VOUTI | tie at VOUT_PD (C26 bank) | DS pin 10 |
| VOUT2 | R20 10 Ω to VBUSC | DS Fig.9 (sense after path FET) |
| C28, C29 | 2 × 10 µF 25 V X7R 1210 on VBUSC | DS BOM (10 µF) + margin at 20 V bias |
| D3 | SMAJ24A VBUSC→GND — SURGE-GRADE only, not abs-max-grade (ADR 0009) | 24 V standoff > 21 V PPS max; Vbr 26.7 V > IP6559 VOUT abs 25 V |
| VCC5V / VCCIO | 2.2 µF each (C30/C31) | DS BOM |
| R25 (GPIO0) | 0603 1% footprint, **DNP** — **the DNP slot is R25; R7 is the POPULATED LM5116 CS-filter 0 Ω, never depopulate it** (X15) | ADR 0004 (variant-default 100 W PDO set) |
| NTC (GPIO0/NTC) | not used (R25 slot only) | power derating opt-out; OTP internal 150 °C; see ADR 0008 for the derating consideration |
| EN (pin 5) | R21/R22 divider from 5VA | §2 above |

### Vconn / e-marker switch (DS Fig. 9)

5VA → D2 (SS210/B5819W schottky) → VCONN5V → C32 1 µF.
CC1 switch: Q9 P-FET (AO3401A): S = VCONN5V, D = CC1, gate 10 kΩ pull-up
(R23) to VCONN5V, gate pulled low by Q10 (2N7002, gate ← GPIO22 with 10 kΩ
pull-down R24). CC2 switch: Q11/Q12 mirror, driven by GPIO21 (R26/R27).
GPIO-to-CC pairing follows DS Fig. 9 exactly (GPIO22→CC1 leg, GPIO21→CC2 leg)
— verified against the 300-dpi figure crop before TSX authoring.

DPC/DMC → J5 D+/D− (legacy BC1.2/Apple on the C port at 5 V). CC1/CC2 →
J5 CC pins direct (chip integrates Rp/PD PHY + 4 kV ESD).
ESD on J5 D+/D−: USBLC6-2SC6 is NOT usable here (its VBUS rail pin is rated
5.25 V; VBUSC reaches 20 V) — use a rail-independent 2-line bidirectional
ESD array (PESD5V0X2 / ESD-diode-pair class, chosen at parts stage) on
D+/D− only; CC pins rely on the chip's integrated 4 kV rating.
USB-A ports keep USBLC6-2SC6 (their VBUS is fixed 5 V).

## 6. Copper / ampacity floors (feed nets.yaml)

| Net class | Current | Floor (1 oz outer) | Strategy |
|---|---|---|---|
| PWR_IN (VBAT, VBAT_F, VIN) | 16 A | pours + In2 plane; 0.8 mm track floor as backstop | trunk = pour |
| SWITCH_NODE (SW_A, LX1, LX2) | 12–15 A | 1.0 mm floor; poured islands, minimal area | pour |
| PWR_RAIL (5VA, VOUT_PD) | 7 A / 5 A | 0.8 mm floor + pours | pour |
| VBUS (VBUSA1-3, VBUSC) | 3 A / 5 A | 0.8 mm | tracks + local pour |
| VCONN/config/sense | <0.1 A | 0.25 mm default | KRT |
| USB_DATA | signal | 0.25 mm, pair-routed | KRT |
| GND | return | pours + In1 plane + stitch | zones |

## 7. Silk plan

Functional: XT60 "**PROTECTED 3S PACK ONLY** 9-12.6V IN" + polarity marks
(v1.1, X14 — the board's UVLO protects the pack average only; a BMS-less
pack is not a sanctioned input); fuse "20A"; each USB-A "5V 2A (2.5A
burst)"; USB-C "PD 5V-20V 5A MAX"; refdes everywhere (F.SilkS + F.Fab
copy); board rev string "usb-hub-3s v1.1".
