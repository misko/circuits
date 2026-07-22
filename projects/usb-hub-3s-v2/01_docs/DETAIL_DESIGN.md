# usb-hub-3s-v2 — Detail Design (component derivations)

Values are the v1-proven LM5116 5 V/7 A buck reused verbatim on BOTH rails
(6 A and 5 A both fit inside the 7 A design point — ADR-0010) plus the new
TPS25740A PD cell (ADR-0004-v2). Datasheet refs in `02_parts/*`.

## 1. Input trunk & protection (ADR-0001)

- Worst-case input current: Sum Pout = 6 A·5 V + 5 A·5 V = 55 W; at Vin_min
  9.0 V, eff 0.9 → **I_in = 6.8 A** (power_topology.py). v1 was ~15.5 A.
- Fuse F1: 10 A MINI blade (6.8/10 = 68 % < 75 % blade-practice). Holder
  Keystone 3568 (C5249699), hand-solder; blade fuse separate.
- Q1 reverse-polarity P-FET AON6403 (Vgs ±20 V, Rds ~7 mΩ): P = 6.8²·0.007 =
  **0.32 W**. R1 100 k gate pulldown; D2 BZT52C12 Vgs clamp.
- D1 TVS SMBJ15A on VIN (standoff 15 V > 12.6 V; clamp ≤ 24.4 V < LM5116 100 V).
- Bulk C1/C2 2× 100 µF/35 V polymer at entry.

## 2. Buck A & Buck C (identical, LM5116 5 V) — v1 §2 math

Both rails: Vout = 5 V, Vin 9–12.6 V, fsw ~ set by RT.
- RT (R2/R11) = 12.4 k → ~ per LM5116 fsw eqn (v1-proven ~230 kHz class).
- FB divider Vout = Vref·(1 + Rtop/Rbot), LM5116 Vref = 1.215 V: Rtop 3.74 k
  (R3/R12), Rbot 1.21 k (R4/R13) → 1.215·(1 + 3.74/1.21) = 1.215·4.091 =
  **4.97 V ≈ 5.0 V**. ✓ (v1-proven values.)
- Slope/RAMP: C 330 pF (C3/C18) on RAMP; slope comp per v1.
- Compensation: R 18 k (R5/R14) + C 3.3 nF (C4/C19) type-II zero, 100 pF
  (C5/C20) hf pole — v1-proven for 5 V/100 µF-out.
- Soft-start: 10 nF (C6/C21) on SS.
- UVLO divider (R6/R15 49.9 k, R7/R16 6.98 k): rising ~9.65 V, falling
  ~8.84 V, 0.8 V hysteresis (2.95 V/cell cutoff). EN pull-up R8/R17 100 k.
- Current sense: RS1/RS2 10 mΩ 2512; LM5116 CS limit ≈ Vcs_th/Rs. Kelvin via
  0 Ω R9/R10 (buck A), R18/R19 (buck C). At 6 A the shunt drops 60 mV / 0.36 W.
- Power FETs Q2/Q3 (buck A), Q4/Q5 (buck C): AON6354 (30 V, logic-level).
- Inductor L1/L2 6.8 µH: ripple ΔI = (Vin−Vout)·D/(fsw·L); Vout/Vin duty; peak
  < the LM5116 CS limit — v1-verified at 7 A, so 6 A/5 A have extra margin.
- Boot: 1N4148WS (D3/D4) VCC→HB + 1 µF boot cap (C7/C22) + 1 µF VCC (C8/C23).
- Input caps 4× 10 µF/25 V 1210 + 100 nF per buck; output 4× 100 µF/6.3 V 1210.

## 3. USB-A ports ×3 (carried from v1 §3)

- TPS2557 (U3–U5) current limit: RILIM 36.5 k → ILIM window ~2.7–3.3 A (DS
  eqn); covers 2 A continuous + 2.5 A burst with headroom, and the window max
  stays under the 6 A buck-A budget (3 ports × worst-case ILIM must not exceed
  6 A simultaneously — the 2 A continuous rating is the design point; ADR/T1).
- Cin 100 nF (C35–37), Cout 22 µF 0805 (C38–40), Chf 100 nF (C41–43).
- USBLC6 (U8–U10) D+/D- ESD; KH-AF90DIP-112 receptacles (J2–J4).
- DCP: two TPS2513A (U6 ports 1+2, U7 port 3) advertise DCP/Apple modes.

## 4. USB-C PD cell (ADR-0004-v2, TPS25740A SLVSDG8B)

- Bias/straps (part.yaml `strap_config_5v_5a`): EN9V→DVDD (5 V-only), HIPWR
  R23 100 k→GND (5 A), PSEL R24 100 k→GND (65 W), PCTRL/GD→VAUX, VDD→GND.
  DVDD 0.22 µF (C45), VAUX 0.1 µF (C46), VTX 0.1 µF (C47), VPWR 0.1 µF (C44).
- Sense Rs (RS3) 5 mΩ 2512 between 5VC (VPWR) and RSNS (ISNS Kelvin). OCP trip
  ~5.8–6.8 A with 5 mΩ (DS) — above the 5 A contract, below the buck-C ceiling.
- Path FETs Q6/Q7 AON6354 back-to-back (common source PDSRC=GDNS, common gate
  PDGATE via R25 10 Ω from GDNG). Reverse-blocking for the receptacle + VBUS
  bulk (Fig 19). At 5 A: 2×Rds ≈ 2×~10 mΩ = 0.5 W across the pair.
- VBUS bulk C49/C50 2× 10 µF + C51 100 nF (>10 µF receptacle inrush spec);
  C_PDIN C48 10 µF on the 5VC feed. Discharge R26 120 Ω VBUS→DSCG.
- CC1/CC2 direct to J5 (built-in ±8 kV ESD; no external TVS).
- Data: DPC/DMC to U12 USBLC6 ESD; R27 0 Ω BC1.2 DCP short (non-PD fallback).
- **Transient window (part.yaml gotcha):** buck-C output must stay inside
  ~[3.9, 5.8] V through transients or the TPS25740A faults (fast-OVP 5.8–6.3 V,
  slow-UVP 3.5–3.9 V). Verify buck-C load-step response at routing/bring-up.

## 5. Fab tier (ADR-0011)

jlc_4layer_advanced, forced solely by the TPS25740A VQFN-24 0.5 mm (via-in-pad
EP escape). Every other multi-pin part escapes at standard/2-layer.
