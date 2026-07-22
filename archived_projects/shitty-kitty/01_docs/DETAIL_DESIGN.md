# DETAIL_DESIGN — shitty-kitty (every derived value, with its equation)

## Worst-case input current (sizes F1, Q1, J1)

- 5V rail: 2A max (buck limit) -> P = 5V x 2A / eta(0.88 @12Vin, AP63205
  DS fig) = 11.4W -> **0.95A @ 12V**.
- Motor: NEMA17 1A RMS/phase, chopper. Copper loss 2 x I^2 x R(2 Ohm typ)
  = 4W + mechanical/iron ~1W -> 5W / 0.9 -> **0.46A @ 12V**.
- Total steady worst **~1.5A**; F1 = 2A hold / 4A trip (SMD1812P200TF16).
  Nuisance-trip guard: host budget capped 1.5A (ADR-0004).
- Q1 AOD4185: P = I^2 x RDSon = 2^2 x 0.015 = **60mW** — no heatsinking.
  |Vgs| = 12V < 20V abs max -> no gate zener (R1 100k G-S pulldown).

## TVS coordination (ADR-0001)

SMBJ16A: standoff 16V > 12.6V max brick; clamp Vc(max) 26V @ Ipp 23.1A.
Downstream abs-max: TMC2209 VS 29V, AP63205 32V, electrolytics 25V surge
tolerant short-term. 26V < 29V — coordinated.

## Buck (AP63205WU-7, fixed 5V, fs = 1.1MHz)

- D = 5/12 = 0.417.
- Ripple: dI = Vout x (1-D) / (L x fs) = 5 x 0.583 / (10uH x 1.1MHz)
  = **0.27A** (13% of 2A — in the DS 10-30% window).
- I_L_peak = 2 + 0.27/2 = **2.13A** < L1 Isat 3.5A (SWPA6045S100MT).
- C_out: 2 x 22uF/25V X5R 0805 (C45783; DC-bias derated ~2x15uF = 30uF
  >= DS-recommended 22uF min). dV_ripple = dI/(8 x fs x C) ~ 1mV.
- C_in: 2 x 4.7uF/25V X5R (C1779) + 100uF/25V electrolytic bulk shared
  with the 12V rail. BST: 100nF (DS standard). EN: tied to VIN via 100k
  (always-on when 12V present).

## LDO (AMS1117-3.3)

P = (5 - 3.3) x 0.4A (ESP32 WiFi peak + logic) = **0.68W**. SOT-223 on
3V3 pour, theta_ja ~60C/W -> +41C rise, Tj < 70C ambient 30C. In 4.7uF /
out 22uF (AMS1117 wants >=22uF tantalum-class ESR; X5R 22uF verified on
esp32-laser-timing bring-up).

## TMC2209 current setting (sense resistors)

I_RMS(max) = (V_fs / (R_sense + 20mOhm)) x 1/sqrt(2), V_fs = 0.325V
(vsense=0). R_sense = 0.15 Ohm -> I_RMS(max) = 1.35A >= 1.0A target with
35% headroom; firmware sets IRUN via UART. P_Rsense = I^2 x R = 0.15W
-> 1206 (0.25W) OK; 1% tolerance. Driver dissipation ~2 x 1^2 x 0.17
(RDSon HS+LS avg) ~ 0.7W -> QFN EP on GND pour + 9 thermal vias.
MS1=MS2=GND (UART addr 0); SPREAD=GND (StealthChop default); CLK=GND
(internal clock); VREF unconnected (UART current control); PDN_UART:
ESP TX -1k- PDN, ESP RX direct (half-duplex standard scheme).
ENN: 10k pull-up to 3V3 = MOTOR DISABLED AT BOOT (ADR-0002).
VS bulk: 100uF/25V electrolytic + 100nF at pins; 5VOUT: 2.2uF (DS);
VCP: 100nF (DS).

## MPR121 x4 (per DS application circuit)

- REXT = 75k 1% to VSS (sets charge current reference) — one per chip.
- VREG: 100nF to VSS; VDD: 100nF each (VDD = VREG tied to 3V3? NO —
  VDD=3V3, VREG is the internal regulator output, cap only).
- ADDR straps: U3=GND (0x5A), U4=3V3 (0x5B), U5=SDA (0x5C), U6=SCL (0x5D).
- IRQ: open-drain, 10k pullup to 3V3 each, own GPIO each.
- Electrodes: 6 used per chip (ELE0-5); ELE6-11 unconnected (DS-allowed,
  disabled by firmware config).
- I2C: 4.7k pullups (bus load 5 devices, 400kHz OK).

## Passives summary (all 0805 Basic unless noted)

| Value | Use | Qty class |
|---|---|---|
| 100nF C49678 | per-IC decoupling (every VDD pin), VCP, BST, endstop RC | many |
| 1uF C28323 | EN RC, VREG-adjacent, accel | few |
| 2.2uF (25V) | TMC 5VOUT | 1 (C19110 Extended 2.2uF/25V — see BOM) |
| 4.7uF/25V C1779 | buck in x2, LDO in | 3 |
| 22uF/25V C45783 | buck out x2, LDO out, 3V3 at module | 4 |
| 100uF/25V C2836443 | 12V bulk x2 (entry + TMC VS) | 2 (elec, Extended) |
| 100R C17408 | (spare/series uses) | few |
| 1k C17513 | LEDs, TMC UART mix, endstop series | few |
| 4.7k C17673 | I2C pullups | 2 |
| 5.1k C27834 | USB-C CC1/CC2 | 2 |
| 10k C17414 | EN, ENN, IRQ x4, endstop, BOOT-adjacent | many |
| 100k C149504 | Q1 gate pulldown, buck EN tie | 2 |
| 0.15R 1% 1206 | TMC sense x2 | 2 (code at BOM stage) |

## Electrode geometry note

Foil pads on the lid (off-board) connect via J3/J4 harness; on-board
stubs header->MPR121 kept < 20mm, 0.25mm width, >=0.3mm gap, In1 GND
under. Ring assignment: U3=IN1-6, U4=IN7-12, U5=OUT1-6, U6=OUT7-12.
