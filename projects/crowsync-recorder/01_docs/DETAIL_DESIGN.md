# DETAIL_DESIGN — crowsync-recorder

Every schematic value with its derivation. Codec facts from PCM2900C
datasheet SBFS039 (02_parts/PCM2900CDBR/part.yaml).

## 1. Codec operating point (drives everything)

- Full-scale ADC input: **0.6 × VCCCI Vpp**, centered at 0.5 × VCCCI
  (SBFS039 electrical characteristics). VCCCI (internal regulator) ≈ 3.7 V
  (external-supply spec window 3.6–3.85 V) → **FS ≈ 2.22 Vpp = 0.785 Vrms**,
  center ≈ 1.85 V.
- ADC input impedance: 30 kΩ; inputs self-biased → external AC coupling.
- Supply: bus-powered, ~60 mA operational at VBUS = 5 V.
- Antialias: on-chip (-3 dB at 150 kHz) + digital decimation filter.

## 2. USB interface (fig 38 bus-powered configuration)

| Item | Value | Why |
|---|---|---|
| R1, R2 | 22R 1% | D+/D- series termination per fig 36/38 |
| R3 | 1k5 5% | D+ pullup to VDDI (3.3 V) — full-speed attach signature. Chip side of R1. |
| R4, R5 | 5k1 1% | CC1/CC2 Rd pulldowns — UFP sink advertisement (USB-C spec 5.1k ±10%) |
| R7 | 2R2 1% | VBUS -> pin 3 filter per fig 38; 60 mA × 2.2 Ω = 0.13 V drop, P = 8 mW |
| C11 | 1u | VBUS pin filter cap (fig 38) |
| C12 | 10u | 5 V bulk at connector (≤ 10 uF USB inrush limit) |
| C13 | 100n | 5 V HF |
| D1 | USBLC6-2SC6 | ESD: I/O1=DP_C, I/O2=DM_C, VBUS pin=VBUS_5V — decisions/0001 |
| SEL0, SEL1 | tie to VDDI | "must be set high" (SBFS039 Table 1) |
| TEST0 | tie GND; TEST1 open | Table 1 |
| HID0-2 | NC | internal pulldowns, active high — unused |

## 3. Crystal (XTI 21 / XTO 20)

- Y1: 12.000 MHz SMD3225, CL = 20 pF, ±10 ppm (YXC X322512MSB4SI).
  ±10 ppm = ±10 us/s sample-clock drift bound between PPS corrections —
  PPS-disciplined mapping removes it (host-side).
- C5 = C6 = 2 × (CL − C_stray) = 2 × (20 − 3) ≈ **33 pF** (inside the
  10–33 pF datasheet window, SBFS039 fig 38 note).
- R6 = 1M feedback across XTI/XTO (fig 38).

## 4. Codec decoupling (fig 38, note "must be < 2 uF" on 1u pins)

| Pin | Net | Cap |
|---|---|---|
| 10 VCCCI | VCCCI | C1 = 10u |
| 14 VCOM | VCOM | C2 = 10u |
| 27 VDDI | VDDI | C3 = 1u |
| 23 VCCXI | VCCXI | C4 = 1u |
| 19 VCCP2I | VCCP2I | C7 = 1u |
| 17 VCCP1I | VCCP1I | C8 = 1u |

## 5. Analog rail (U3 TPS7A2033PDBVR)

- Load: TLV9062 2 × 0.55 mA + mic 0.5 mA + bias networks ≈ 2.5 mA
  (300 mA part — margin 100×). Noise 7 uVrms typ.
- C14 = 1u in, C15 = 10u out (≥ 0.47u required each side), C16 = 100n at U2.
- EN tied to IN (always on).

## 6. Microphone channel (CH1 -> VINL)

**Bias** (PUI electret, 2-wire): 3V3A -> FB1 (600R @ 100 MHz, ferrite,
decisions/0001) -> C17 10u + C18 100n reservoir -> R8 2k2 -> MIC net.
Capsule current ≤ 0.5 mA → V_capsule = 3.3 − 0.5m × 2.2k ≈ **2.2 V**
(inside 1–10 V operating window of both capsule options). Bias-network
noise: LDO 7 uVrms further RC-filtered by (FB1+R8)·C17: fc ≈ 7 Hz.

**Protection** (A3): D2 USBLC6-2SC6 at J2/J3 (I/O1 = MIC, I/O2 = PPS,
VBUS pin = 3V3A) + R9/R14 100R series + FB1 on the bias feed.

**Preamp** (U2A, non-inverting, referenced to buffered VCOM):
- Capsule -24 dB re 1 V/Pa (ship, AOM-5024L-HD class): 63 mV/Pa.
- Design point: full scale at ~104 dB SPL (3.17 Pa peak-safe for close crow
  calls): 63 mV × 3.17 = 200 mVrms; required gain = 785/200 = 3.9.
- **Gain = 1 + Rf/Rg = 1 + 3.01k/1k = 4.01** → FS at 103.9 dB SPL.
- Alternate -44 dB capsule (6.3 mV/Pa): swap **Rf = 39k** → gain 40 → FS at
  the same 104 dB SPL (decisions/0003; Rg, Cg unchanged).
- R11 = Rf = 3k01 1% (ship) / 39k 1% (alt); R12 = Rg = 1k 1%.
- C20 (Cg) = 10u in series with Rg to GND → DC gain = 1 (VCOM_BUF passes
  unamplified); AC corner = 1/(2π·1k·10u) = **15.9 Hz** for both gains.
- Input network: C19 = 1u coupling, R10 = 100k to VCOM_BUF → corner 1.6 Hz;
  input CM = 1.85 V, inside TLV9062 rail-to-rail range at 3.3 V.
- Output headroom: center 1.85 V, swing ±1.11 V pk at FS → 0.29 V margin to
  the 3.3 V rail (RRIO sat < 50 mV). OK.
- Noise: TLV9062 10 nV/√Hz × 40 × √20k = 57 uVrms out = -83 dBFS; capsule
  self-noise dominates.
- Stability: GBW 10 MHz / gain 40 → 250 kHz closed-loop BW; C21 isolated
  from the op-amp output by R13 = 100R.
- Post-filter: R13 = 100R + C21 = 1n (fc = 1.6 MHz RF stop) then C9 = 1u
  into VINL (corner with 30k input: 5.3 Hz).

**VCOM buffer** (U2B): VCOM (pin 14) -> unity buffer -> VCOM_BUF. Loads:
R10 only (AC); DC load ≈ 1.85V/100k = 18 uA. Op-amp isolates the codec
reference from injected noise.

## 7. PPS channel (CH2 -> VINR)

- Input: 3.3 V CMOS PPS (A2). Divider to ~1 Vpp inside the 2.22 Vpp FS:
  chain R14 100R (series/protection) + R15 22k over R16 10k:
  **3.3 × 10k/(0.1k+22k+10k) = 1.028 V** ≈ 1 Vpp at VINR (A2 target).
- Load on the GNSS PPS driver: 32.1 kΩ → 103 uA. Negligible.
- C10 = 1u AC coupling into the self-biased VINR; source impedance ≈ 6.9k
  → HF corner 4.3 Hz; a 100 ms PPS pulse droops (τ = 37 ms) but the RISING
  edge arrives at full 1 V amplitude — the timing reference is the edge.

## 8. Indicators

- D3 green LED + R17 = 1k from SSPND (pin 28, high = operational):
  KT-0805G Vf ≈ 2.6–3.1 V → (3.3 − 2.8)/1k ≈ 0.5 mA — dim-but-visible
  enumeration indicator (430 mcd part at 5 mA; ~10% still obvious indoors).
- D4 green LED + R18 = 2k2 from VBUS_5V: (5 − 2.8)/2.2k ≈ 1.0 mA — power.

## 9. Worst-case input current (USB budget)

60 mA codec (op) + 2.5 mA analog + 2.5 mA LEDs + margin ≈ **70 mA** ≪ 500 mA
USB default; PCM2900C is a USB-IF-certified bus-powered device.

## 10. Passive selection rules

0603 X7R/X5R ceramics ≥ 16 V (5 V rails: ≥ 4× derating); C1/C2/C15/C17/C20
10u ≥ 10 V X5R 0603; gain/divider resistors 1%; crystal caps C0G/NP0.
