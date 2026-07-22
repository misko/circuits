# lipo3s-usb-hub — detail design math

Every component value with its derivation and margin. The topology (LM74800 ideal
diode + dual LM5145 synchronous buck + TPS2557 per-port switch) is the independently
selected conservative answer for this envelope; the LM5145 buck stage, FET, inductor,
frequency and compensation network are a proven power-stage design (SPF power board /
usb-power-3s lineage, DRC/audit/bring-up reviewed 2026-07). New/derived values (buck-B
ILIM, TPS2557 ILIM, UVLO ladder) are derived below and FLAGGED for bench verification
at bring-up.

## Input envelope

3S LiPo: 3.0 V/cell (empty) … 4.2 V/cell (full) → **9.0–12.6 V**; a hot-off-charger
pack can momentarily read ~4.3 V/cell → **~12.9 V abs-max** for headroom. All input-side
parts (fuse holder, XT60, FETs, LM74800, input caps, D1) are rated ≥ 25–30 V.

## Buck stages (both: LM5145, fsw = 606 kHz via RT = 16.5 k)

- L = 3.3 µH (MWSA1005S-3R3MT: Isat 16 A, Irms 13 A, DCR 10 mΩ)
- Ripple, worst at Vin = 12.6: ΔIL = Vout·(Vin−Vout)/(Vin·L·fsw)
  - Rail A (6 A):   5.08·7.52/(12.6·3.3µ·606k) ≈ 1.52 A → Ipk 6.8 A ≪ 16 A ✓
  - Rail B (7.5 A): same ΔIL → Ipk 8.3 A ≪ 16 A ✓; Irms 7.5 A < 13 A ✓
- Output setpoint: Vout = 0.8·(1 + RFB1/RFB2) = 0.8·(1 + 20k/3.74k) = **5.078 V**
  (targets ≥ 4.9 V at each port after trace + switch drop at full load)
- Output bank per rail: 4× 47 µF 10 V X7R (≈ 25 µF each at 5 V DC bias → ~100 µF)
  + 220 µF polymer (15 mΩ ESR) → Ceff ≈ 200–250 µF. Rail B carries +25 % current;
  transient sag scales but stays within the 50 mV design target — verify by load step.
- Input caps per stage: 3× 10 µF 50 V X7R + 100 nF, placed tight to the half-bridge.
- Compensation (identical plant both rails): RC1 13 k, CC1 8.2 nF, CC2 39 pF,
  CC3 1.2 nF, RC2 4.64 k → crossover fc ≈ 60 kHz; ESR zero (~48 kHz, 15 mΩ polymer)
  partially cancelled by the RC2·CC3 pole. Disposition: acceptable; verify by load
  step at bring-up (contingency RC2 → 2.74 k if phase margin low).
- Soft start: CSS 47 nF ≈ 4 ms. VCC decouple 2.2 µF. Bootstrap 100 nF.
- ILIM (valley-current sense, RILIM anchored at verified 348 Ω ↔ 6.3 A wc-min):
  - Rail A (USB-C): **RA2 = 348 Ω** → ~6.3 A wc-min — protects the 6 A port. ✓ verified value
  - Rail B (USB-A bank): **RB2 = 432 Ω** → 6.3·432/348 ≈ 7.8 A wc-min (linear scale;
    FLAG: verify against SNVSAI4 valley-current eq. at bring-up). Margin over the 7.5 A
    bank draw is intentionally thin — this limit IS the bank's aggregate backstop.
  - CILIM = 18 pF both.

## Per-port current limit (TPS2557, USB-A ×3)

TPS2557 fixed-mode current-limit switch (auto-retry, thermal shutdown, reverse-current
block). IOS(mA) ≈ 61050 / RILIM(kΩ), power-law fit through the verified point
(20 kΩ ↔ 3.05 A) matching the SLVS931B curve shape.
**RILIM = 24.3 kΩ → IOS ≈ 2.51 A** (satisfies "2.5 A max" with the datasheet's ±
current-limit band). FLAG: confirm against SLVS931B eq. 1 at bring-up; acceptance
band 2.3–2.8 A. Each port has 100 nF input + 22 µF output (1206) bulk. Open-drain
FAULT (pad 8) left floating — no MCU to read it (see ADR-0004).

## Front-end (LM74800-Q1 + 2× CSD18543Q3A common-drain)

- Reverse-polarity: back-to-back FETs (common drain at FE_MID) block current in either
  direction until the controller drives the gates — a reversed pack cannot energize the
  board. Q1 = battery-side (source on VBATT_F), Q2 = load-side (source on VSW).
- Conduction loss: RDS(on) path ≈ 2 × 8 mΩ → ~1.1 W at 8.2 A worst case, spread over two
  SON-8 packages with thermal pads on the VBATT_F / FE_MID pours — acceptable.
- UVLO/OV ladder (LM74800 EN and OV thresholds = 1.231 V):
  `VBATT_F ─ R1 887k ─ [EN] ─ R2 52.3k ─ [OV] ─ R3 82.5k ─ GND`, T = 1021.8 k
  - EN rising:  1.231·T/(R2+R3) = 1.231·1021.8/134.8 = **9.33 V** (≈ 3.11 V/cell) ✓
  - OV trip:    1.231·T/R3      = 1.231·1021.8/82.5  = **15.25 V** (charger/fault ceiling)
  - Falling hysteresis is the LM74800's internal EN hysteresis. FLAG: measure actual
    off-voltage at bring-up; target ≥ 8.7 V (2.9 V/cell over-discharge floor).
  - Ladder current: 12.6/1.02 M ≈ 12 µA — negligible standby battery drain.
- FE decouple: FE_CAP 100 nF, FE_MID 100 nF, HG_FE gate cap 47 nF, FE_EN filter 2.2 µF.

## USB-C source (no PD controller)

CC1, CC2 each pulled to 5V_C through **10 kΩ** (Rp advertising the legacy default 3.0 A
source current — the maximum advertisable WITHOUT a PD/BMC controller). The 6 A copper +
regulator headroom serves loads that draw beyond the advertised value on a fixed-5 V
source (e.g. single-board computers); see ADR-0003. D+/D− pairs (A6/A7, B6/B7) shorted →
legacy BC1.2 DCP for A-to-C cables. SBU1/SBU2 (A8/B8) unused (power-only).

## USB-A DCP strapping

Each port: D+ shorted to D− through direct copper (≤ 200 Ω per BC1.2) → attached
devices detect a Dedicated Charging Port and draw to their own max. No ESD arrays: no
data crosses the board, and VBUS is clamped by the rail TVS. See ADR-0005.

## Protection summary

| Layer | Element | Threshold |
|---|---|---|
| catastrophic overcurrent | F1 ATO blade | 15 A |
| reverse polarity | LM74800 + b2b FETs | blocks either direction |
| battery under-voltage | FE EN ladder | on 9.33 V / off ~8.8 V |
| charger over-voltage | FE OV ladder | 15.25 V |
| input transient | D1 SMBJ16A | 16 V standoff / ~26 V clamp |
| rail clamp | D2, D3 SMBJ5.0A | on 5V_A, 5V_C |
| per-A-port limit | TPS2557 ×3 | 2.51 A + thermal + reverse block |
| USB-C path limit | buck-A valley OCP | ~6.3 A wc-min |

## Indicators

Green LED (KT-0805G, ~2.7 Vf) + 1 kΩ from each 5 V rail → ~2.3 mA each (D4 on 5V_A,
D5 on 5V_C).

## Bench-verify checklist (bring-up FLAGS collected)

1. Rail-B ILIM (432 Ω) valley-current limit vs SNVSAI4 — target ~7.8 A wc-min.
2. TPS2557 IOS (24.3 kΩ) vs SLVS931B eq. 1 — acceptance band 2.3–2.8 A.
3. FE off-voltage (falling UVLO) — target ≥ 8.7 V.
4. Both rails: load-step transient sag ≤ 50 mV at rated current; phase margin.
