# usb-hub-3s — detail design (every value derived)

Sources: LM5116 SNVS499I (cached 02_parts/LM5116MHX/), IP6559 V1.4
(02_parts/IP6559-C/), TPS2556/7 SLVS931B, TPS2513 datasheet. Manufacturer
worked designs adopted per canon M6; deviations derived below.

## 1. Input protection chain (ADR 0001)

- **F1**: MINI blade fuse 20 A + THT holder. Worst input ≈ 15.5 A
  (100 W PD + 30 W USB-A at Vin 9.0 V, eff 0.93). 20 A > 15.5 × 1.25 margin
  on I²t-slow blade curve; wiring/pours sized 16 A continuous.
- **Q1** reverse-polarity P-FET: drain = VBAT_F (battery side), source = VIN,
  body diode conducts battery→load at first contact, then Vgs ≈ −VIN (−8.8
  to −12.6 V) enhances it. R100 100 kΩ gate→GND; D5 BZT52C12 zener S→G
  clamps |Vgs| ≤ 12 V (spike margin; abs max ±20 V). FET: ≥30 V, Rds(on)
  ≤ 5 mΩ @ Vgs −10 V, Id ≥ 30 A, DFN5x6/PowerPAK. Dissipation ≤ 15.5² ×
  5 mΩ = 1.2 W — pour + thermal vias (R-THERM).
- **D1** SMBJ15A across VIN after Q1: standoff 15 V > 12.6 V; clamp ≤ 24.4 V
  < IP6559 VIN abs 34 V, < FET 30 V.
- **Bulk**: 2 × 100 µF ≥ 35 V low-impedance electrolytic/polymer at VIN entry
  (IP6559 BOM asks ≥35 V electrolytic; LM5116 input filter separate below).

## 2. Board UVLO (ADR 0001, amended here — single mechanism)

LM5116's precision UVLO pin is the board's ONE undervoltage authority:

- Threshold 1.215 V rising, pin hysteresis 0.1 V, pin pull-up 5 µA (DS §6.3.3).
- Divider R_uv_top = 49.9 kΩ 1% (VIN→UVLO), R_uv_bot = 6.98 kΩ 1% (UVLO→GND):
  K = 56.88/6.98 = 8.149, Rt∥Rb = 6.12 kΩ → 5 µA offset 30.6 mV.
  V_rise = 8.149 × (1.215 − 0.0306) = **9.65 V**;
  V_fall = 8.149 × (1.115 − 0.0306) = **8.84 V** (2.95 V/cell). ✓
- IP6559 EN chain: 5VA presence gates the PD stage. R101 10 kΩ 5VA→EN(GPIO18),
  R102 10 kΩ EN→GND → EN = 2.5 V when 5VA up (≤ VCCIO 3.3 V, above logic
  high), 0 V when down; the 10 kΩ pull-down overrides the chip's weak internal
  pull-up when 5VA is absent. Consequence (documented): any LM5116 shutdown
  (UVLO, hiccup) also disables the C port — protective, accepted.
- Residual standby below UVLO ≈ IP6559 200 µA + LM5116 standby + dividers
  (~56 µA + ~1.1 mA/…): dividers dominate: 12.6/56.9k = 221 µA (UVLO divider)
  — total ≈ 0.5 mA. ORDER_README: do not store the pack connected.

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
| Cout | 4 × 100 µF 6.3 V X6S/X7R 1812 (or 5×) | TI design 5×100 µF; ESR path verified in TI curves |
| Q2/Q3 | NFET 30–40 V, Rds ≤ 8 mΩ @4.5 V, Qg ≤ 30 nC, SO-8/DFN5x6 | TI used Si7850DP 60 V (Vin 60); ours ≤12.6 V |
| CS filter | CS/CSG routed Kelvin to Rs; R 0Ω pair per TI fig | |

Duty 5/12.6–5/9 = 0.40–0.56 — well inside limits.

## 4. USB-A port channel × 3 (ADR 0002)

- **TPS2557DRBR** per port: IN = 5VA, OUT = VBUSAn, EN = 5VA (always on),
  FAULT float (no MCU), ILIM: IOSmin = 127981/R^1.0708, IOSmax = 99038/R^0.947
  (DS §10.2.1.2.2). **RILIM = 36.5 kΩ 1%** → IOS = 2.72–3.29 A:
  passes 2.5 A burst, protects at ~3 A. ✓
- **TPS2513DBVR** (dual channel): U4 serves ports 1+2 (DP1/DM1→J2,
  DP2/DM2→J3), U6 serves port 3 (DP1/DM1→J4; DP2/DM2 no-connect flags).
  IN = 5VA + 0.1 µF each.
- Per port: Cout = 22 µF 10 V X5R + 0.1 µF on VBUSAn; USBLC6-2SC6 ESD array
  (I/O1 = D+, I/O2 = D−, VBUS pin = VBUSAn, GND) at the connector.
- Port copper: VBUSAn ≥ 3 A → 1 mm floor + pour.

## 5. USB-C PD stage — IP6559-C (ADR 0003/0004), Fig. 8+9 adopted

| Item | Value | Derivation |
|---|---|---|
| R_s_in (R1) | 5 mΩ 1% ≤100 ppm alloy 1206+ | DS Fig.8/BOM; input CC limit datasheet-nominal |
| R_s_out (R4) | 5 mΩ 1% ≤100 ppm alloy 1206+ | DS; output limits 3 A@5/9/12 V, 5 A@20 V |
| Sense filters | R5, R6 10 Ω + C9, C10 1 µF | DS Fig.8 (CSP2/CSN2, CSP1/CSN1) |
| PCIN/PCON | direct taps at the shunt outer ends | DS §13.5 Kelvin rule |
| Q4(HG2)/Q5(LG2)/Q6(HG1)/Q7(LG1) | NFET 30–40 V, Rds ≤ 5 mΩ @10 V, Ciss ≤ 2 nF, DFN5x6 | DS MOSFET Selection (10 mΩ recommended, lower for 100 W; Vbr ≥ 1.2×Vmax(20 V out)) |
| Gate R | 0 Ω 0603 × 4 (tuning slots per DS Fig.7) | reserved footprints |
| Snubbers | R2, R3 2 Ω + C5, C6 1 nF at LX2, LX1 | DS Fig.8 |
| BST | C3, C4 100 nF 16 V (BST2–LX2, BST1–LX1) | DS Fig.8 |
| T1, T2 | SMAJ30A on LX2, LX1 → GND | DS "30V TVS" Fig.7/8 |
| L1 | 10 µH ± 20%, Isat ≥ 15.5 A, DCR < 10 mΩ | I_L(peak)boost = 20×5/(9×0.95) + 9×11/(2×20×250k×10µ) = 12.7 A; ×1.2 (DS rule) |
| Cin (stage) | 100 µF ≥35 V electro + 100 nF (C1/C2) + 2×10 µF 25 V ceramic | DS BOM + ripple Irms ≈ 5 A |
| Cout | 100 µF 25 V polymer (C7) + 100 nF (C8) | DS BOM |
| Q8 path NFET | 30 V, ≤5 mΩ, DFN5x6; D=VOUT_PD, S=VBUSC, G=VOUT2G | DS Fig.8 (port-2 path used in single-C) |
| VOUTI | tie at VOUT_PD (C7 bank) | DS pin 10 |
| VOUT2 | 10 Ω to VBUSC | DS Fig.9 (sense after path FET) |
| C14 | 2 × 10 µF 25 V X7R 1210 on VBUSC | DS BOM (10 µF) + margin at 20 V bias |
| D3 | SMAJ24A VBUSC→GND | 24 V standoff > 21 V PPS max |
| VCC5V / VCCIO | 2.2 µF each (C11/C12) | DS BOM |
| R7 (GPIO0) | 0603 1% footprint, **DNP** | ADR 0004 (variant-default 100 W PDO set) |
| NTC (GPIO0/NTC) | not used (R7 slot only) | power derating opt-out; OTP internal 150 °C |
| EN (GPIO18) | R101/R102 divider from 5VA | §2 above |

### Vconn / e-marker switch (DS Fig. 9)

5VA → D2 (SS210/B5819W schottky) → VCONN5V → C_vconn 1 µF.
CC1 switch: Q9 P-FET (AO3401A): S = VCONN5V, D = CC1, gate 10 kΩ pull-up
(R103) to VCONN5V, gate pulled low by Q10 (2N7002, gate ← GPIO22 with 10 kΩ
pull-down R104). CC2 switch: Q11/Q12 mirror, driven by GPIO21 (R105/R106).
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

Functional: XT60 "3S LIPO 9-12.6V IN" + polarity marks; fuse "20A"; each
USB-A "5V 2A (2.5A burst)"; USB-C "PD 5V-20V 5A MAX"; refdes everywhere
(F.SilkS + F.Fab copy).
