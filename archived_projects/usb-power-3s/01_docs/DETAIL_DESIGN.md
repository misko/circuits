# usb-power-3s — detail design math

Every component value with its derivation. Provenance: buck stage design
reuses the SPF power-board topology (same controller, FETs, inductor,
frequency, comp network), which was independently reviewed and DRC/audit
verified 2026-07. New values (buck-B ILIM, TPS2557 ILIM, UVLO ladder) are
derived below and flagged for bring-up verification.

## Buck stages (both: LM5145, fsw = 606 kHz via RT = 16k5)

- L = 3.3 µH (MWSA1005S-3R3MT, Isat 16 A, Irms 13 A, 10 mΩ)
- Ripple, worst at Vin=12.6: ΔIL = Vout·(Vin−Vout)/(Vin·L·fsw)
  - Rail A (6 A):  5.08·7.52/(12.6·3.3µ·606k) ≈ 1.52 A → Ipk 6.8 A ≪ 16 A ✓
  - Rail B (7.5 A): same ΔIL → Ipk 8.3 A ≪ 16 A ✓; Irms 7.5 A < 13 A ✓
- Output setpoint: Vout = 0.8·(1 + RFB1/RFB2) = 0.8·(1+20k/3.74k) = 5.078 V
- Output bank per rail: 4× 47 µF 10 V X7R (≈25 µF each at 5 V bias → ~100 µF)
  + 220 µF polymer (15 mΩ) → Ceff ≈ 200–250 µF (SPF-proven at 6 A;
  rail B carries +25% current — transient sag scales, still within the
  50 mV design target: ΔV ≈ L·ΔI²/(2·C·Vout·margin), checked at bring-up)
- Input caps per stage: 3× 10 µF 50 V X7R (C77102) + 100 nF, tight to bridge
- Compensation (identical plant): RC1 13k, CC1 8n2, CC2 39p, CC3 1n2,
  RC2 4k64 → fc ≈ 60 kHz, ESR zero ~48 kHz (15 mΩ polymer) partially
  cancelled by RC2·CC3 pole; SPF disposition: acceptable, verify by load
  step at bring-up (contingency RC2 → 2k74)
- Soft start: 47 nF ≈ 4 ms. VCC: 2.2 µF. BST: 100 nF.
- ILIM (valley sense, RILIM from verified point 348 Ω ↔ 6.3 A wc-min):
  - Rail A: **348 Ω** → ~6.3 A wc-min (protects the 6 A port) ✓ verified value
  - Rail B: **432 Ω** → 6.3·432/348 ≈ 7.8 A wc-min (linear scale — FLAG:
    verify against SNVSAI4 eq. at bring-up; margin over 7.5 A is thin by
    design: the limit IS the port-bank protection)
  - CILIM 18 pF both.

## Per-port current limit (TPS2557, USB-A ×3)

IOS(mA) ≈ 61050 / RILIM(kΩ) — power-law fit through the verified point
(20 kΩ ↔ 3.05 A, SPF) matching the SLVS931B curve shape.
**RILIM = 24k3 → IOS ≈ 2.51 A.** FLAG: confirm against SLVS931B eq. 1 at
bring-up; acceptance band 2.3–2.8 A.

## Front-end (LM74800-Q1 + 2× CSD18543Q3A common-drain)

Reverse polarity: back-to-back FETs block either direction until the
controller enables. RDS(on) path ≈ 2×8 mΩ → 1.1 W at 8.1 A worst case,
spread over two VSON-8 with thermal pads on VBATT_S/FE_MID pours — fine.

UVLO/OV ladder (EN and OV thresholds = 1.231 V):
VBATT_F ─ R1 887k ─ [EN] ─ R2 52k3 ─ [OV] ─ R3 82k5 ─ GND, T = 1021.8k
- EN rising:  1.231 · T/(R2+R3) = 1.231·1021.8/134.8 = **9.33 V** (≈3.11 V/cell)
- OV trip:    1.231 · T/R3      = 1.231·1021.8/82.5  = **15.25 V** (charger fault)
- Falling hysteresis is the LM74800's internal EN hysteresis (~mV at pin →
  a few hundred mV at VBATT). FLAG: measure actual off-voltage at bring-up;
  target ≥ 8.7 V (2.9 V/cell floor).
Ladder current: 12.6/1.02M ≈ 12 µA — negligible battery drain.

## USB-C source (no PD)

CC1, CC2 each pulled to 5V_C through **10 kΩ** (Rp for 3.0 A advertisement,
±10% required — 1% used). This is the maximum current advertisable without
a PD controller. The 6 A capability is copper/regulator headroom for loads
that draw beyond advertisement (e.g. Pi 5 style); see ADR-0002.
D+/D− pairs (A6/A7, B6/B7) shorted together → legacy BC1.2 DCP behavior for
A-to-C cables.

## USB-A DCP strapping

Each port: D+ shorted to D− (direct copper, ≤200 Ω per BC1.2) → devices
negotiate DCP and draw up to their max. No ESD arrays: no data leaves the
board; VBUS clamped by rail TVS. See ADR-0003.

## Protection summary

| Layer | Element | Threshold |
|---|---|---|
| catastrophic | F1 ATO blade | 15 A |
| reverse | LM74800 + b2b FETs | blocks |
| battery UV | FE ladder | on 9.33 V / off ~8.8 V |
| charger OV | FE ladder OV | 15.25 V |
| input transient | D1 SMBJ16A | 16 V standoff / 26 V clamp |
| rail clamp | D2, D3 SMBJ5.0A | on 5V_A, 5V_C |
| per-A-port | TPS2557 | 2.51 A + thermal |
| USB-C path | buck A OCP | ~6.3 A wc-min |

## Indicators

Green LED (KT-0805G, ~2.7 Vf) + 1 kΩ from each rail → ~2.3 mA each.
