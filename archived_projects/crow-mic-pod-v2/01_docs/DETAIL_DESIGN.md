# DETAIL_DESIGN — crow-mic-pod-v2 component derivation

Every value derived here. Single +5V_AUDIO supply, audio band 20 Hz–20 kHz
(crow calls ~1–8 kHz). VMID = 2.5V virtual ground. Values are E24/E12 1%
where the ratio matters (gain, divider), 5% elsewhere. See ADR-0002 for the
gain topology and the D1 assumption (doc's exact table unseen).

## Nets

5V_AUDIO, GND_AUDIO, 5V_BEEP, BEEP_SWITCHED_RETURN, AUDIO_P, AUDIO_N,
VMIC_F, MIC_OUT, VMID, INP (U1A +in node), INA (U1A −in node), OUTA,
INB (U1B −in node), OUTB. (TSX authors leading-digit rails N-prefixed:
N5V_AUDIO, N5V_BEEP → canon_net → 5V_AUDIO, 5V_BEEP.)

## Microphone bias (AOM-5024L-HD-R, MK1)

| Ref | Value | Role | Derivation |
|---|---|---|---|
| R_mf (R1) | 100 Ω | RC filter series R, 5V_AUDIO→VMIC_F | with C_mf: fc = 1/(2π·100·100µ) = 16 Hz — attenuates rail noise into bias |
| C_mf (C1) | 100 µF | RC filter cap, VMIC_F→GND | low-ESR; bias node is quiet, PSRR-critical |
| R_bias (R2) | 3.9 kΩ | mic drain bias, VMIC_F→MIC_OUT | electret Idss ~0.5 mA → ~1.95V drop; drain sits ~2.8V, good headroom (confirm Idss from datasheet) |

MIC_OUT = electret drain (+ terminal); electret − terminal → GND_AUDIO.
Signal AC-coupled out at MIC_OUT.

## Input coupling & bias to the amp

| Ref | Value | Role | Derivation |
|---|---|---|---|
| C_in (C2) | 1 µF | AC couple MIC_OUT→INP | with R_inbias: fc = 1/(2π·100k·1µ) = 1.6 Hz |
| R_inbias (R3) | 100 kΩ | bias INP to VMID | high-Z so it doesn't load the coupling; sets U1A +in DC = 2.5V |

## VMID virtual ground (2.5V)

| Ref | Value | Role | Derivation |
|---|---|---|---|
| R_vm1 (R4) | 22 kΩ | 5V_AUDIO→VMID | divider top |
| R_vm2 (R5) | 22 kΩ | VMID→GND_AUDIO | divider bottom → 2.50V |
| C_vm (C3) | 10 µF | VMID→GND bypass | source impedance 11k ∥ → AC-solid; fc≈1.4 Hz |

## Stage A — U1A non-inverting, gain +1.5 (hot leg)

U1A: +in(pin3)=INP, −in(pin2)=INA, out(pin1)=OUTA.

| Ref | Value | Role | Derivation |
|---|---|---|---|
| R_fa (R6) | 10 kΩ | feedback OUTA→INA | AC gain = 1 + R_fa/R_ga = 1 + 10/20 = **1.5** |
| R_ga (R7) | 20 kΩ | gain-set INA→(Cga)→VMID | 1% for gain accuracy |
| C_ga (C4) | 10 µF | DC-block in gain leg | DC gain = 1 → OUTA DC = VMID; fc = 1/(2π·20k·10µ) = 0.8 Hz |

OUTA = VMID + 1.5·Vsig.

## Stage B — U1B inverting, gain −1 (cold leg, generates balance)

U1B: +in(pin5)=VMID, −in(pin6)=INB, out(pin7)=OUTB.

| Ref | Value | Role | Derivation |
|---|---|---|---|
| R_inb (R8) | 10 kΩ | OUTA→INB | inverting input R |
| R_fb (R9) | 10 kΩ | feedback OUTB→INB | gain = −R_fb/R_inb = **−1** → OUTB = 2·VMID − OUTA = VMID − 1.5·Vsig |

**Differential result:** AUDIO_P − AUDIO_N = OUTA − OUTB = 3·Vsig →
**3 V/V differential** (G2). Symmetric ±1.5 swing on each leg maximizes
single-5V headroom and matches leg impedances for CMRR.

## Output network (short-circuit + cable-cap isolation, DC block)

| Ref | Value | Role | Derivation |
|---|---|---|---|
| R_outa (R10) | 100 Ω | OUTA series to line | isolates op-amp from cable C; short-circuit limit |
| C_outa (C5) | 10 µF | DC block OUTA→AUDIO_P | blocks 2.5V bias from cable; fc into ~10k central = 1.6 Hz |
| R_outb (R11) | 100 Ω | OUTB series to line | matched to R_outa |
| C_outb (C6) | 10 µF | DC block OUTB→AUDIO_N | matched to C_outa |

## Op-amp supply decoupling (U1)

| Ref | Value | Role |
|---|---|---|
| C_d1 (C7) | 100 nF | HF decouple at U1 pin8 (V+), <3 mm |
| C_d2 (C8) | 10 µF | bulk decouple at U1 |

U1 pin4 (V−) = GND_AUDIO.

## Rail bulk at RJ45 entry

| Ref | Value | Role |
|---|---|---|
| C_b1 (C9) | 10 µF | 5V_AUDIO bulk near J1 pins 4/5 |
| C_b2 (C10) | 100 nF | 5V_AUDIO HF near J1 |

## ESD (D1, TPD2E2U06DRLR)

2-channel bidirectional array at J1. Ch1: AUDIO_P (J1 pin1) ↔ GND_AUDIO.
Ch2: AUDIO_N (J1 pin2) ↔ GND_AUDIO. GND pad → GND_AUDIO. Working voltage
6V > audio swing; placed hard against J1's audio tails. (Exact pin→channel
map from research/part.yaml.)

## Calibration transducer (LS1, CMT-8504-100-SMT-TR) + clamp

- LS1(+) → 5V_BEEP (J1 pin3); LS1(−) → BEEP_SWITCHED_RETURN (J1 pin6).
- D2 (SS14): cathode → 5V_BEEP, anode → BEEP_SWITCHED_RETURN. Freewheel
  path for the inductive kick when central opens the low-side switch:
  current continues LS1(−)→D2 anode→cathode→5V_BEEP. 40V/1A Schottky ≫ the
  ~5V/150 mA load. **KiCad D_SMA: pad 1 = cathode (band)** — pad 1 → 5V_BEEP.
- D3 (SMAJ6.0A, DNP): cathode → 5V_BEEP, anode → BEEP_SWITCHED_RETURN.
  6.0V standoff > 5V rail; alternate over-clamp, unpopulated. Pad 1 =
  cathode → 5V_BEEP.

Beep pair isolated from analog GND on the pod (G8).

## Test points (south edge)

TP_5VA(5V_AUDIO), TP_GND(GND_AUDIO), TP_AUDIOP(AUDIO_P), TP_AUDION(AUDIO_N),
TP_5VBEEP(5V_BEEP), TP_BEEPRET(BEEP_SWITCHED_RETURN), TP_VMID(VMID).

## Refdes ↔ role map (authoring manifest source)

U1 OPA1678IDR · MK1 AOM-5024L-HD-R · LS1 CMT-8504-100-SMT-TR · J1 RJHSE-5384
D1 TPD2E2U06DRLR · D2 SS14 · D3 SMAJ6.0A(DNP)
R1 100R · R2 3.9k · R3 100k · R4 22k · R5 22k · R6 10k · R7 20k · R8 10k ·
R9 10k · R10 100R · R11 100R
C1 100µ · C2 1µ · C3 10µ · C4 10µ · C5 10µ · C6 10µ · C7 100n · C8 10µ ·
C9 10µ · C10 100n
TP1..TP7 · H1..H4 (M3 mounting)

## Component-count sanity

7 specialty parts (U1, MK1, LS1, J1, D1, D2, D3) + 11 R + 10 C + 7 TP +
4 mounting holes. ~35 BOM lines (holes excluded from BOM).
