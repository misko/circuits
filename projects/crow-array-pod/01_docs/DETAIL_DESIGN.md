# crow-array-pod — detail design (every value derived)

Values follow the source doc "Starting analog values" table (§3) verbatim
where given; derivations and margins below. Refdes are final.

## Cable interface (J1 — since v1.1: RJHSE-5384 RJ45 jack, ADR-0004)

v1.1 (A4/D11) replaced the v1.0 KF128L-3.5-8P screw terminal with an RJ45
jack; the net map is contact-for-contact unchanged (RJ45 contact n = old
terminal n = T568B pin n, straight-through to the central end):

| J1 | Net | Cat5e conductor | Silk word |
|---|---|---|---|
| 1 | AUDIO_P | orange | AUDIO+ |
| 2 | AUDIO_N | orange-white | AUDIO- |
| 3 | BEEP_5V | green | 5V BEEP |
| 4 | 5V | blue | 5V |
| 5 | GND | blue-white | GND |
| 6 | BEEP_RET | green-white | BEEP RET |
| 7 | 5V | brown | 5V |
| 8 | GND | brown-white | GND |

Plus the banner NOT ETHERNET - CUSTOM 5V PINOUT (P-SILK-FN, source §4).

## Microphone input

- R1 = 100R 5V->5VF; C1 = 100uF electro + C2 = 100n on 5VF (doc RC filter
  "100R + 100uF||100n"). Filter pole ~16 Hz; supply ripple to the bias
  string attenuated >40 dB above 1.6 kHz. Drop: (0.5+0.25) mA x 100R =
  75 mV — 5VF ~ 4.93 V.
- R2 = 3.9k 5VF->MIC (doc). Capsule operating point ~4.9 - 3.9k x 0.5mA
  ~ 2.9 V, inside the 1-10 V window, at the 3 V rated point.
- C3 = 1uF MIC->AIN coupling (doc). With R3 = 100k bias: HPF at
  1/(2π·100k·1u) = 1.6 Hz (mic itself rolls off at 20 Hz).
- R3 = 100k AIN->VMID (doc). OPA1678 bias current ~10 pA => offset ~1 uV.

## Midpoint reference

R4 = R5 = 10k divider 5VF->VMID->GND (doc), decoupled by C4 = 10uF + C5 =
100n (doc says "10uF||100n"). VMID = 2.47 V (5VF/2). Divider impedance 5k;
C4 gives a 3.2 Hz pole — VMID is quiet AC ground for R3/R7 and +IN_B.

## Amplifier (U1 OPA1678IDR, pins per 02_parts part.yaml)

- Stage A (non-inverting, x1.5, doc): +IN_A(3)=AIN, feedback R6 = 10k
  OUT_A->FB_A(2), R7 = 20k FB_A->VMID. G = 1 + 10k/20k = 1.50 exactly.
- Stage B (unity inverter around VMID, doc): +IN_B(5)=VMID, R8 = 20k
  A_OUT->FB_B(6), R9 = 20k FB_B->OUT_B(7). G = -1.00.
- Differential gain = 2 x 1.5 = 3.0 V/V (doc "approximately 3 V/V").
- Noise: R6||R7 = 6.7k -> 10.5 nV/rtHz thermal vs op-amp 4.5 nV/rtHz;
  total input-referred well under the mic's own 80 dB SNR floor.
- Supply: V+(8) = 5V with C6 = 100n at the pin + C7 = 10uF bulk; V-(4)=GND.
- R10 = R11 = 68R output isolation per leg (doc).

## Beeper path

- R12 = 0R (1206-capable 0805 fine at 150 mA) BEEP_5V->BZ_P: series swap
  point (doc "series pads to the beeper pair").
- BZ1 = CMT-8504-100-SMT-TR: (+) pad = BZ_P, (-) pad = BEEP_RET.
- D2 = SS14 populated: K = BZ_P side of the pair (clamps to the +5V_BEEP
  feed through R12=0R), A = BEEP_RET. Coil kick when the central AO3400A
  opens is clamped to 5V + 0.4 V. Ipk = 150 mA << 1 A rating; repetitive
  energy (L ~ mH, I ~ 0.15 A => ~11 uJ/chip) is negligible.
- D3 = SMAJ6.0A TVS footprint, EMPTY, in parallel (same K/A orientation).

Clamp nodes: across BZ_P/BEEP_RET (the transducer terminals), so the clamp
also covers the cable inductance seen from the pod side.

## Protection & EMI reserves

- D1 = TPD2E2U06DRLR across AUDIO_P/AUDIO_N at J1: IO1(3)=AUDIO_P,
  IO2(5)=AUDIO_N, GND(4)=GND, NC(1,2) no-connect. 1.5 pF/line — nil at
  audio. VRWM 5.5 V > 2.5 V bias + 2 Vpk signal.
- The PTC for the 5 V feed lives at the CENTRAL end (per-port
  MINISMDC050F-2 in the source §5) — see ADR-0001 for the split.
- L1 = WE-SL2 CM choke footprint EMPTY; R13/R14 = 0R bridge pads 1-4 /
  2-3 (line A / line B straight through).
- TP6 SHIELD pad (2.5 mm) + R15 0805 footprint EMPTY to GND: shield-bond
  reserve (doc §4 "start with unshielded cable; reserve shield-bonding
  pads").

## Test points

TP1 AUDIO_P, TP2 AUDIO_N, TP3 VMID (expect 2.47 V), TP4 5V, TP5 GND,
TP6 SHIELD (bond reserve). First-power ritual: 5V current < 10 mA, TP3 =
2.5 V ±2%, MIC node ~2.9 V BEFORE connecting the capsule.

## BOM cost roll-up vs the source §8 pod budget

Electronics per pod (JLC/Digi-Key mixed, qty-10 pricing, est.):
mic $4.19 + OPA1678 ~$0.92 + CMT-8504 $1.59 + TPD2E2U06 ~$0.35 + SS14
~$0.02 + RJ45 jack ~$2.14 (v1.0 terminal was ~$0.60) + passives ~$0.35 +
PCB+assembly ~$3-4
=> ~$11-12 electronics+PCB, inside the doc's $23-30 complete-pod envelope
(enclosure $7-10, gland $1-2, mechanicals $3-6 are off-board).
