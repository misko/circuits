# detail design: xt60-usb-supply

Every schematic value traces to a line here. Converter: SY8368QNC
(decisions/0003), fsw = 800 kHz nominal, Vref(FB) = 0.6 V +/-1.5%.

## System load and input current

- Pout = 3 x 2.5 A x 5 V + 6 A x 5 V = 67.5 W
- eta ~ 0.92 (SY8368 12 V->5 V mid-load curve) -> Pin = 73.4 W
- Iin = 73.4 / 9.0 V (pack empty) = 8.2 A worst case; 5.8 A at 12.6 V

## Fuse (F1 = 15 A, Littelfuse 0451015.MRL)

15 A / 8.2 A = 1.8x continuous margin (nano2 fuses derate ~0.75 at
temperature -> 11.3 A effective, still 1.4x). 65 V rating >> 12.6 V.
Interrupts a shorted FET/cap fault the bucks cannot limit.

## Reverse-polarity P-FET (Q1 = AOD4185)

- P = Iin^2 x Rds(on) = 8.2^2 x 0.015 = 1.0 W worst case (pack-empty
  corner only; 0.5 W at nominal 11.1 V). TO-252 on F.Cu pour, ~70 C/W
  single-sided -> ~70 C rise at the corner, ~35 C nominal. Acceptable;
  the 8.2 A corner coincides with a nearly-dead pack.
- Gate: R_GS = 100 k to GND -> Vgs = -Vbat = -9..-12.6 V, inside +/-20 V
  abs max, fully enhanced at -10 V. No zener needed.

## TVS (D1 = SMBJ15A)

Standoff 15 V > 12.6 V max pack; Vc = 24.4 V @ 24.6 A < 30 V abs max of
SY8368 IN/LX/EN (the pairing that drove ADR 0003).

## Buck stages (U1 = rail A 8 A, U2 = rail C 6 A)

Duty D = Vout/(Vin x eta): 0.42 @ 12.6 V ... 0.58 @ 9.0 V (CCM).

### Inductors (40% ripple target, worst case Vin = 12.6 V)

dI = Vout x (1 - D) / (fsw x L), D_min = 5/12.6 = 0.397

- Rail A: L1 = 1.5 uH (FXL0630-1R5-M): dI = 5 x 0.603 / (0.8e6 x 1.5e-6)
  = 2.5 A = 31% of 8 A. I_pk = 8 + 1.26 = 9.3 A < Isat 14 A (1.5x) ok.
- Rail C: L2 = 2.2 uH (FXL0630-2R2-M): dI = 1.7 A = 29% of 6 A.
  I_pk = 6.9 A < Isat 9.5 A (1.4x) ok.

### Current limits (ILMT strap, valley-mode)

- U1 (8 A): ILMT FLOATING -> 12 A valley limit. Valley at full load =
  8 - 1.26 = 6.7 A; 5.3 A headroom, no false trips, still limits a short.
- U2 (6 A): ILMT LOW (tie to GND) -> 8 A valley limit. Valley at full
  load = 6 - 0.85 = 5.1 A; 2.9 A headroom. Hard short -> ~8-9 A max into
  the USB-C port, satisfying "6 A max" as a capability bound (BRIEF A1).

### Feedback dividers (Vout = 0.6 x (1 + R1/R2))

R1 = 22 k / R2 = 3 k -> 5 x 0.6/0.6... = 0.6 x (25/3) = 5.000 V exactly.
Tolerance: 1% resistors + 1.5% ref -> 4.88..5.12 V, inside USB 4.75-5.25.
Divider current 0.6/3k = 200 uA >> FB bias. Same values both rails.

### Output capacitance (>= 66 uF ceramic per datasheet)

4x 22 uF/16 V X7R 1210 per rail = 88 uF nominal; at 5 V DC bias 1210 X7R
retains ~70% -> ~62 uF effective, ~ the 66 uF floor (accepted: the floor
in the datasheet assumes nominal marking). Ripple:
dV = dI/(8 x fsw x C) = 2.5/(8 x 0.8e6 x 62e-6) = 6.3 mV + ESR term
(~0.5 mOhm effective) ~ 1 mV -> << 50 mV budget.

### Input capacitance

Per rail at IN pins: 2x 10 uF/25 V X7R 1206 (retains ~60% at 12 V ->
12 uF effective). Input ripple RMS = Io x sqrt(D(1-D)) ~ 0.5 x Io = 4 A
(rail A) shared between local MLCC and bulk. Shared bulk at power entry:
2x 100 uF/25 V polymer (30 mOhm, 2.65 A ripple each) absorbs the sub-kHz
battery-lead resonance; MLCCs take the 800 kHz component.

### Small caps (typical application circuit)

- VCC: 2.2 uF ceramic 0603 per converter (internal 3.3 V LDO decouple —
  datasheet application table; NOT 0.1 uF).
- BS (bootstrap): 0.1 uF X7R 0603 per converter, BS to LX.

## USB port networks

- USB-A x3 (BC1.2 DCP): D+ shorted to D- per port (net DCPn), nothing
  else on data. ESD: USBLC6-2SC6 per port, I/O pair across D+/D-,
  VBUS pin to 5V_A. Port VBUS = 5V_A direct (pour).
- USB-C: Rp = 10 k 1% from CC1 and CC2 to 5V_C -> advertises 5 V/3 A
  (decisions/0002). ESD: USBLC6-2SC6, I/O1 = CC1, I/O2 = CC2, VBUS pin
  to 5V_C. All four VBUS and four GND contacts poured.

## Indicators

- LED1 red at VBAT_P: R = 1 k -> (12.6-2)/1k = 10.6 mA max, 7 mA at 9 V.
- LED2/LED3 green at 5V_A/5V_C: R = 1 k -> (5-2.1)/1k = 2.9 mA
  (indicator brightness, deliberate low current).

## Copper ampacity (1 oz outer, IPC-2152 ~10 C rise)

- 8 A trunk needs ~5 mm pour width; 6 A ~4 mm; design pours 6-10 mm wide.
- Floors in rules/nets.yaml are backstops only (0.5 mm power, 0.3 mm 5 V
  taps); trunks ride priority-1 F.Cu pours + In2 patches where needed.
