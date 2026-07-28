# DETAIL DESIGN — pluto-rx2-8way

Every number a component value depends on, with its equation. A value in the
schematic with no line here is UNJUSTIFIED (canon S5). Decisions live in
`decisions/`; the shape lives in `ARCHITECTURE.md`.

**M-IMPORT grades are stated inline.** MEASURED = touched or read from a
machine-readable source; CITED = a vendor document with figure/page; ESTIMATED
= derived or inferred, **and it carries an error bar**; OWED = nobody has it.

---

## 1. Stackup constants — everything downstream is pinned to these

Stackup `JLC04161H-7628` (ADR-0003): L1→L2 prepreg **h = 0.2104 mm**,
**Dk = 4.4** (CITED, JLC's controlled-impedance stackup table, quoted at
1 GHz), copper **t = 35 µm**.

**Method: Hammerstad-Jensen with the thickness correction** — closed form, not
a field solve.

```
Δw    = (t/π)·(1 + ln(2h/t))        = (0.035/π)·(1 + ln 12.02)  = 0.0388 mm
w_eff = w + Δw
u     = w_eff / h
ε_eff = (εr+1)/2 + (εr−1)/2 · (1 + 12/u)^(−1/2)
Z0    = 120π / ( √ε_eff · [ u + 1.393 + 0.667·ln(u + 1.444) ] )        (u > 1)
```

| w | w_eff | u | ε_eff | **Z0** |
|---|---|---|---|---|
| 0.35 mm | 0.3888 | 1.848 | 3.321 | 51.3 Ω |
| **0.36 mm** | **0.3988** | **1.895** | **3.328** | **50.5 Ω** |
| 0.365 mm | 0.4038 | 1.919 | 3.331 | 50.1 Ω |
| 0.37 mm | 0.4088 | 1.943 | 3.335 | 49.7 Ω |

**`RF50` min_width = 0.36 mm.** At Dk 4.2 (FR-4's Dk falls with frequency;
the 4.4 figure is quoted at 1 GHz and the band runs to 6 GHz) the same line is
**51.6 Ω** — so the design sits inside ±3.2 % across the plausible Dk range,
comfortably inside JLC's ±10 % impedance tolerance. **This must still be
re-confirmed against JLCPCB's own impedance calculator for the exact ordered
stackup before release** (`CHECKLIST.md`, canon M6).

Derived constants, used everywhere below:

| constant | value | from |
|---|---|---|
| ε_eff | **3.328** | table above |
| propagation delay `t_pd = √ε_eff / c` | **6.09 ps/mm** | 1.8242 / 299.792 mm·ps⁻¹ |
| guide wavelength at 6 GHz `λg = λ0/√ε_eff` | **27.41 mm** | 50 mm / 1.8242 |
| **λg/20 at 6 GHz** (fence pitch, lumped bound) | **1.37 mm** | |
| λg/12 at 6 GHz | 2.28 mm | |

**Microstrip loss.** Dielectric and conductor terms computed separately:

```
α_d = 27.3 · (εr/√ε_eff) · ((ε_eff−1)/(εr−1)) · tanδ / λ0     [dB per unit λ0]
    = 27.3 · 2.411 · 0.685 · 0.02 / 50 mm                    = 0.0180 dB/mm  @6 GHz
R_s = √(π f µ0 / σ)  = 0.0202 Ω/□   @6 GHz, σ = 5.8e7 S/m
α_c ≈ R_s/(Z0·w) · 8.686 · k_rough  = 0.00975 · 1.85          = 0.0180 dB/mm  @6 GHz
```

with `tanδ = 0.02` (ESTIMATED for FR-4 at GHz, ±0.005) and a roughness factor
`k_rough = 1.85` (ESTIMATED, ±0.35 — standard-profile foil).

| f | α_d | α_c | **total** |
|---|---|---|---|
| 70 MHz | 0.00021 | 0.0020 | **0.0022 dB/mm** |
| 6 GHz | 0.0180 | 0.0180 | **0.036 dB/mm** |

(α_d scales as f, α_c as √f.) The 6 GHz figure carries roughly a ±20 %
uncertainty from the two estimated inputs; it is used for BUDGETS, and the
board's real per-path loss is a MEASURED release artifact (ADR-0006), not this
number.

**CTRL trace, 0.20 mm:** `w_eff = 0.2388`, `u = 1.135`, `ε_eff = 3.200`,
**Z0 = 67 Ω** (both the wide-line and narrow-line Hammerstad forms give 66.7
and 66.8 Ω — they agree at this u, which is the check).

**USB pair, 0.28 mm / 0.18 mm gap:** single-ended `Z0 = 57.4 Ω`;
`Z_diff ≈ 2·Z0·(1 − 0.48·e^(−0.96·s/h))` = **90.6 Ω** (ESTIMATED — a
closed-form approximation, not a field solve; the binding requirement for USB
full speed on a <30 mm run is the solid reference, not the impedance).

---

## 2. RF chain budget

**Radial arm length** (ADR-0007): `U_SW` RF pad at r ≈ 2.15 mm from the die
centre, jack centre pin at r = 20.0 mm ⇒ **17.85 mm per arm**, identical on all
nine by construction. Delay `17.85 × 6.09` = **108.7 ps**; loss
`17.85 × 0.036` = **0.643 dB at 6 GHz**, `× 0.0022` = **0.039 dB at 70 MHz**.

**SMA launch loss.** The vendor publishes VSWR ≤ 1.35 DC–6 GHz and NO
insertion loss (CITED / OWED). Mismatch loss alone is
`−10·log10(1 − |Γ|²)` with `|Γ| = 0.35/2.35 = 0.149` ⇒ **0.097 dB**. Used as
**0.10 dB per launch, and it is a LOWER BOUND** — the dissipative term is
unpublished.

### Ordinary element paths (elements 1–7), antenna jack → Pluto RX2

`total = 2 × 0.10 (launches) + 2 × arm + IL_switch`

| port | IL_switch max @4–6 GHz | **total @6 GHz** | IL_switch max @10–100 MHz | **total @70 MHz** |
|---|---|---|---|---|
| RF1 | 1.9 dB | **3.39 dB** | 0.9 dB | **1.18 dB** |
| RF2 / RF7 | 2.3 dB | **3.79 dB** | 1.0 dB | **1.28 dB** |
| RF3 / RF6 | 2.2 dB | **3.69 dB** | 1.0 dB | **1.28 dB** |
| RF4 / RF5 | 2.2 dB | **3.69 dB** | 1.1 dB | **1.38 dB** |

**Element-to-element amplitude spread is 0.40 dB at 6 GHz and 0.20 dB at
70 MHz, ALL of it inside the die** — the arms are equal, so the board
contributes nothing to the spread. That is the point of the star.

**Element-to-element PHASE spread** is the die's, and it is published with
min/typ/max (Table 3, PDF p8): at 6 GHz RF4−RF1 is **−35.8 / −26.3 / −16.9°**,
RF3−RF1 −11.2 / −5.7 / −0.3°, RF2−RF1 −9.4 / −2.8 / +3.8°. The board's own
contribution is the length spread, ≈0 by construction. **These windows are the
vendor bound the measured table (ADR-0006) is checked against.**

### The reference path (element 8, tapped), antenna jack → Pluto RX2

`0.10 (launch) + 0.163 (4.52 mm to the pickoff node) + 20.26 (pickoff, tap
relative to a plain port) + 0.373 (10.37 mm tap arm) + 1.9 (RF8) + 0.643
(RFC arm) + 0.10 (launch)`

= **23.54 dB at 6 GHz**, **21.43 dB at 70 MHz**.

### The RX1 through path, antenna jack → Pluto RX1

`0.10 + 0.163 + IL_pickoff + 0.366 (10.17 mm to J_RX1) + 0.10`

= **1.17 dB at 6 GHz** (IL_pickoff 0.437), **0.664 dB at 70 MHz**
(IL_pickoff 0.432). **This is the number the whole pickoff decision exists to
minimise** — a resistive splitter would have made it 6.7 dB.

### Interference budget

Power-summing the seven deselected ports from the guaranteed-minimum isolation
column (Table 3, PDF p5), and noting that the tapped element leaks 20 dB down
and effectively drops out of the sum:

| dwell | Σ leakage @4–6 GHz | wanted | **SIR** | worst-case Δφ = `asin(10^(−SIR/20))` |
|---|---|---|---|---|
| ordinary element (RF3 selected) | −23.9 dB | −2.2 dB | **+21.7 dB** | **4.75°** |
| **the reference (RF8 selected)** | −23.4 dB | −22.16 dB | **+1.2 dB** | **60.1°** |

The full five-band reference-dwell table, the four candidate tap values and
why none of them fixes it, are in `decisions/0002` (spec tension **T3**).

---

## 3. The RX1 resistive pickoff — `R_T1`, `R_T2` = 220 Ω each

Circuit: the antenna jack, the RX1-out jack and the series arm meet at ONE
node. `Z0 = 50 Ω`, arm `Rs = R_T1 + R_T2 = 440 Ω`, `Rp = Rs + Z0 = 490 Ω`.

```
IL_main  = 20·log10(1 + Z0/(2·Rp))   = 20·log10(1.051020)      = 0.4324 dB
tap|out  = 20·log10(Z0/Rp)           = 20·log10(0.102041)      = −19.825 dB
tap|port = tap|out − IL_main                                    = −20.257 dB
Z_in     = Z0 ∥ Rp = 45.37 Ω → Γ = −0.04855 → RL               = 26.28 dB (VSWR 1.104)
```

**Two tap definitions, both published, because quoting the wrong one is a
0.43 dB error:** `tap|out` is what RX1 and RX2 see relative to each other;
`tap|port` is what element 8 delivers to the switch relative to elements 1–7,
and it is the one the §2 SIR arithmetic uses.

### Parasitic tilt

An 0402 wrap-around chip has `C = 0.0392 pF, L = 0.1209 nH` — **CITED for the
class** (Vishay TN 60107, Table 1, p1) and **ESTIMATED for this thick-film
part at 0.04 ± 0.02 pF**, because Uniroyal publishes no HF data. Two in series
halve it: **C_eff = 0.0196 pF**.

Modelling the arm as `Z_arm = R/(1 + jωRC)` and `Zp = Z_arm + Z0`:

| f | single 470 Ω arm (rejected alternate) | **split 2 × 220 Ω (chosen)** |
|---|---|---|
| DC | −20.341 dB | **−19.825 dB** |
| 1 GHz | −20.285 (+0.056) | **−19.812 (+0.013)** |
| 2 GHz | −20.116 (+0.225) | **−19.775 (+0.050)** |
| 3 GHz | −19.851 (+0.490) | **−19.713 (+0.112)** |
| 4 GHz | −19.505 (+0.836) | **−19.628 (+0.197)** |
| **6 GHz** | **−18.650 (+1.691)** | **−19.394 (+0.431)** |

**The tilt scales essentially linearly with C_p, so the ± 0.02 pF bar is the
number that matters:**

| arm | tilt @6 GHz, C_nom | over the bar | **width of the unknown** |
|---|---|---|---|
| single 470 Ω | +1.691 dB | +0.509 … +3.240 dB | **2.73 dB** |
| **split 2 × 220 Ω** | **+0.431 dB** | **+0.117 … +0.950 dB** | **0.83 dB** |

**Main line, the half that costs RX1 sensitivity, is flat**: 0.4324 dB at DC →
**0.4373 dB at 6 GHz** (+0.005 dB); RL 26.28 → 25.84 dB.

### Value selection

| Rs | tap\|port | IL_main | RL | reference SIR @4–6 GHz | verdict |
|---|---|---|---|---|---|
| 440 Ω (2 × 220) | −20.26 dB | **0.432 dB** | 26.3 dB | +1.2 dB | **CHOSEN — user-confirmed** |
| 220 Ω (`R_T2` → 0 Ω) | −15.42 dB | 0.769 dB | 21.4 dB | +6.1 dB | the zero-board-cost BOM alternate |
| 100 Ω | −10.88 dB | 1.339 dB | 16.9 dB | +10.6 dB | rejected — 0.9 dB of permanent RX1 loss |
| 0 Ω (bare T) | −3.52 dB | 3.522 dB | 9.5 dB | +18.0 dB | rejected — unmatched, 9.5 dB RL |

**450 Ω, the value the original arithmetic used, is not stocked** — not E24,
not E96, not E192. 2 × 220 = 440 Ω is JLC Basic on both parts.

**Sourcing, MEASURED 2026-07-28:** C25091 (`0402WGF2200TCE`, 220 Ω ±1 %,
62.5 mW) is `base` with **995,162** in the JLCPCB assembly library. Note the
trap: its **LCSC RETAIL product page reads stock 0 the same day** — two
different pools, and a PCBA order allocates from the assembly pool.

---

## 4. Control plane

**Line impedance** 67 Ω (§1). **PE42482A-X digital absolute maximum 3.6 V**
on a 3.3 V rail — 300 mV of headroom (CITED, Table 1, PDF p2).

### Series termination `R_S1..R_S4` = 47 Ω

Requirement `Z_drv + R_S ≥ Z_line` so the far-end reflection cannot exceed the
rail. RP2040 pad impedance is a firmware-selected quantity, **ESTIMATED
25 ± 10 Ω at the 12 mA setting** (M-IMPORT: no document held by this project).

```
far-end peak = 2 · V_DD · Z_line / (Z_line + Z_drv + R_S)
```

| R_S | Z_drv = 15 Ω | Z_drv = 25 Ω | Z_drv = 250 Ω |
|---|---|---|---|
| 0 Ω | 5.40 V ✗ | 4.81 V ✗ | 1.36 V |
| 33 Ω | 3.63 V ✗ (0.03 V over) | 3.54 V (62 mV margin) | 1.30 V |
| **47 Ω** | **3.43 V ✓** | **3.18 V ✓** | 1.24 V |

`R_S ≥ 67 − 25 = 42 Ω` ⇒ **47 Ω (E24)**. At 47 Ω the bound holds across the
whole estimated range, **in copper rather than in a firmware register**.
Time constant against ~15 pF of trace + pin: `47 × 15p` = **0.7 ns**, 0.016 %
of the 4267 ns blanking allowance.

**A `1 kΩ + 1 nF` RC is REJECTED**: `τ = 1 µs` ⇒ 4.6 µs to 99 %, **more than
the entire blanking allowance**.

### Pull-downs `R_PD1..R_PD4` = 10 kΩ

`V1..V4` input current ≤ 5 µA, `V_IL(max)` 0.6 V, `V_IH(min)` 1.17 V (CITED,
Table 2, PDF p3).

| R | `V = I_leak · R` | margin to V_IL | I when driven high | verdict |
|---|---|---|---|---|
| 1 kΩ | 5 mV | 99 % | 3.3 mA × 4 = 13.2 mA | rejected |
| **10 kΩ** | **50 mV** | **92 %** | **0.33 mA × 4 = 1.3 mA** | **CHOSEN** |
| 100 kΩ | 500 mV | 17 % | 0.13 mA | rejected |

**DC levels with both resistors in place:** `V_OH = 3.3 · 10000/10047` =
**3.28 V** (against V_IH 1.17 V); `V_OL = 5 µA × 10.047 kΩ` = **50 mV**
(against V_IL 0.6 V).

**Power-on default** = all four low = `V1V2V3 = 000`, `V4 = 0` ⇒ **RF1** — a
real antenna, not the mute state, and not dependent on the MCU's pad-reset
behaviour.

---

## 5. Power

### Envelope

| item | current |
|---|---|
| RP2040 (125 MHz, PIO loop) | ~50 mA worst case |
| QSPI flash (XIP) | ~5 mA |
| PE42482A-X | 200 µA max (CITED, Table 2, PDF p3) |
| 2 indicator LEDs | 3.8 mA |
| 4 pull-downs, all high | 1.3 mA |
| **typical** | **~60 mA** |
| **declared design envelope** | **0.15 A** (2.5× margin) |

### `U_LDO` — three HARD selection constraints, none of them optional

`Vin 4.75–5.25 V` (USB 2.0 device-end limits), `Vout 3.20–3.40 V`
(3.3 V ±3 %), `Iout_max 0.15 A`. `Vout_max < Vin_min` ⇒ step-down ⇒ **LINEAR
meets it**, and a switcher is rejected on RF grounds (ARCHITECTURE §3).

1. **Dropout ≤ 1.23 V at 0.15 A.** ~~1.35 V~~ — **CORRECTED 2026-07-28 at the
   stage-2 merge, and the correction is a NODE, not an arithmetic slip.**
   `4.75 − 3.40 = 1.35 V` is measured at the **USB-C VBUS pin**, and the
   regulator is not connected there: `F_IN` (`R_1max` **0.75 Ω**) and `FB_IN`
   (DCR max **0.06 Ω**) are in series ahead of it, so at 0.15 A the pass
   element sees `4.75 − 0.15 × 0.81` = **4.63 V** and the real headroom is
   **1.23 V**. The protection chain eats **9 %** of the budget it was written
   against. `power_tree.yaml` declares `vin_min: 4.63` for this reason.
   **This changed the answer, it did not merely tighten it:** AMS1117-3.3 — the
   obvious JLC-Basic default — is spec'd `1.3 V max` dropout at 0.8 A, which
   passes 1.35 V by 50 mV and **FAILS 1.23 V**.
2. **`V_IN` absolute maximum ≥ 10.3 V** (ADR-0004). ~~≥ 10 V~~ — **the
   constraint MOVED because the TVS moved.** ADR-0004 derived ≥ 10 V from a
   5.0 V-standoff part clamping at ≈9.2 V; that standoff was **rejected at
   selection** (see `D_TVS` below), and `SMBJ6.0A` clamps at **10.3 V at
   I_PP 58.3 A**. A regulator rated exactly 10 V is now **out of spec**, not
   marginal. A 6 V-rated LDO — which is most popular 3.3 V parts, including
   this repo's own ledger entry `analog-ldo-quiet-3v3` (XC6227, V_IN abs max
   **6.5 V**, Torex ETR03054-006 p4) — dies before the protection conducts;
   worse, the SMBJ6.0A's *breakdown minimum* (6.67 V) is already above it.
3. **`θ_JA ≤ 195 °C/W`.**
   `PD_max = (Vin_max − Vout_min) · Iout = (5.25 − 3.20) × 0.15` = **308 mW**.
   For `Tj ≤ 0.8 · Tj_max = 100 °C` at `Tamb = 40 °C`:
   `θ_JA ≤ 60 / 0.308` = **195 °C/W**. **A bare SOT-23-5 is DISQUALIFIED at the
   envelope**, and that is now CITED rather than asserted from a range: the
   selected part's own thermal table gives **SOT-23-5 = 256 °C/W** against
   SOT-223-3 = 62 °C/W (Microchip DS20005160B, Temperature Specifications,
   PDF p8, datum JESD51-7 named in §5.3.1 p22) — so the "200–250 °C/W"
   estimate this line used to carry was if anything *optimistic*. (At the
   ~60 mA typical, PD = 123 mW and a SOT-23-5 would be fine; the envelope is
   what the part must survive, not the typical.)

**CLOSED 2026-07-28: `U_LDO` = `MCP1755S-3302E/DB`** (Microchip, LCSC
**C638611**, SOT-223-3, JLC *extended*). Dropout **500 mV max at 300 mA** —
the datasheet maximum at the part's RATED current, i.e. the conservative
reading, against a 150 mA load; `V_IN` abs max **+17.6 V** (operating max
16.0 V, so it stays *in regulation* through a clamp event rather than merely
surviving); `θ_JA` **62 °C/W** ⇒ ΔT = 19.1 °C ⇒ Tj = **59 °C** at Ta 40 °C.
All three by 2.7× / 7.3 V / 3.1×.
`power_tree.yaml` now declares the rail and **E-TOPO PASSES**: headroom
1230 mV vs dropout 500 mV, PD 307 mW vs a 968 mW derived package rating (32 %).
**Sourcing risk, stated because it is the weakest thing about the choice:**
C638611 stock was **86** on 2026-07-28 and the tape-and-reel twin
(MCP1755ST-3302E/DB, C111176) is **stock 0**. Alternates with their
consequences are in the dossier; MIC5209-3.3YS is the closest but wants ~1 Ω
of output ESR and is the `SOT-223-3_TabPin2` footprint variant, so that swap
moves the footprint too.
**The tab is pad 4, not pad 2**, and KiCad ships both numberings. Because the
EP is internally tied to GND the wrong one still yields a *working* board —
invisible to ERC, DRC and parity, visible only as a JLC-twin PAD-MISMATCH.

### Passives

| ref | value | derivation |
|---|---|---|
| `F_IN` | PPTC 500 mA hold / 1 A trip — **`1206L050/24WR`** (C2154056) | above the 0.15 A envelope by 3.3×, below the 500 mA a USB 2.0 host advertises. **Derated hold at 50 °C is 0.38 A** (vendor rerating table) — still 2.5× the envelope, and 1.6× even at the part's +85 °C ceiling. `V_max` 24 V is the POST-TRIP standoff, which is why the 6 V variant lost |
| `D_TVS` | ~~5.0 V~~ **6.0 V standoff** unidirectional TVS — **`SMBJ6.0A`** (C83270) | **THE 5.0 V STANDOFF WAS WRONG AND THIS ROW USED TO SAY SO BACKWARDS.** It read "above `Vbus_max` 5.25 V so it never conducts": 5.0 is not above 5.25. Littelfuse defines V_R as the maximum voltage appliable *without operation*, and USB-C `vSafe5V` runs to **5.50 V**, not 5.25. Fitted leakage at 5.25 V: **≈47 µA** for the 6.0 V part against **≈1.26 mA** for the 5.0 V part (27×, and already above its rated standoff at 25 °C with no published temperature behaviour). Clamp **10.3 V at I_PP 58.3 A** drives constraint 2 above. Package chosen on **dynamic resistance, not P_PPM**: SMB 62–50 mΩ vs SMA 94–76 mΩ ⇒ 8.5–8.9 V vs 9.5–9.6 V at a 30 A ESD peak |
| `C_BULK` | 4.7 µF X5R 0805 | bulk on the clamped node |
| `C_LDI` | 1 µF X7R **0805** | regulator input. **CLOSED**: DS20005160B §4.4 p17 requires the input capacitor to be "of equivalent or higher value than the output capacitor" — 1 µF vs 1 µF meets it **at equality, the boundary of the rule**. `C_BULK` does NOT help here because `FB_IN` sits between them |
| `C_LDO` | 1 µF X7R **0805** | regulator output. **OWED-ITEM CLOSED 2026-07-28**: DS20005160B §4.4 "Output Capacitor", p17 — minimum **1 µF**, ESR **≤ 2 Ω** with no lower bound, **ceramic-stable (X7R/X5R explicitly recommended; a 1 µF X7R 0805 is ~50 mΩ)**, maximum 1000 µF. The placeholder **STANDS unchanged** — it is literally the datasheet's own test condition (`COUT = 1 µF X7R`). **The package is part of the spec**: the 1 µF floor is on *effective* capacitance at 3.3 V bias, so 0805 is required and a 1 µF X7R 0402 can derate below it. And if a future swap forces an ESR-hungry LDO, the ESR must live IN THE CAPACITOR — 1 Ω in the DC path costs 1 Ω × 0.15 A = 150 mV, dragging 3.30 V to 3.15 V, **below the 3.20 V `vout_min` floor** |
| **VBUS bypass total** | **5.7 µF** | `C_BULK + C_LDI`. **USB 2.0 §7.2.4.1 caps a device's downstream VBUS bypass at 10 µF** to bound inrush; 5.7 µF nominal (≈4.6 µF after DC derating) is what makes "no inrush limiter" a decision. The 3V3-side 0.1 µF parts do NOT count against this limit |
| `C_SW1` / `C_SW2` | 100 nF + 1 µF | `U_SW` VDD at pin 8, span ≤3 mm. IDD is 120 µA typ, so this is decoupling for control-line transients, not for load current — which is exactly why it must be AT the pad |
| `C_MCU1..4` | 100 nF each | MCU supply pins, local |
| `R_CC1` / `R_CC2` | 5.1 kΩ ±5 % | USB Type-C Rd: advertises a plain 5 V sink, which is what makes sustained overvoltage unreachable (ADR-0004) |
| `R_LED1` / `R_LED2` | 680 Ω | `(3.3 − 2.0)/680` = **1.91 mA**; E24 above the 650 Ω a 2 mA target implies |
| `Y_XTAL` + load caps | 12 MHz **`ABM8-272-T3`** (C20625731), `C = 2·(C_L − C_stray)` | **THE 15 pF STANDS AND BOTH INPUTS THAT PRODUCED IT WERE WRONG.** This row read `C_L = 12 pF` (marked OWED) and `C_stray ≈ 5 pF` ⇒ 14 ⇒ 15 pF E24. `C_L` is now **CITED at 10 pF** (Abracon drawing 456603 Rev B, p1, "Load capacitance (CL) 10 pF"), and `C_stray` is **3 pF** — the RP2040 hardware-design guide's own worked number for this exact chip, not a generic guess. `2·(10 − 3) = 14` ⇒ **15 pF E24, identical**, because the two errors cancelled. Recorded rather than quietly corrected: the next person to touch the crystal would otherwise re-derive 10 pF from a `C_stray` with no source and **under-load the oscillator**. Other crystal facts now CITED: ESR ≤ 50 Ω, C0 ≤ 3.0 pF, drive 10 µW typ / 200 µW max, ±30 ppm tolerance and ±30 ppm over temperature |

---

## 6. The timing frame

```
frame          = 7 × (8192 + 128)  +  (4096 + 128)
               = 7 × 8320 + 4224   = 58,240 + 4,224   = 62,464 samples
duration       = 62,464 / 30e6                        = 2.08213 ms
sweep rate     = 1 / 2.08213 ms                       = 480.28 Hz
buffer         = 8 × 62,464                           = 499,712 samples
               = 488 × 1024                                       (exactly)
duration       = 499,712 / 30e6                       = 16.657 ms
efficiency     = (7 × 8192 + 4096) / 62,464 = 61,440/62,464 = 98.36 %
blanking       = 128 / 30e6                           = 4.267 µs per hop
Doppler        = ±480.28/2                            = ±240 Hz unambiguous
```

**Why no other buffer works.** With seven full dwells and one half dwell the
ideal frame is `15X/2`, which carries a factor of **3**. `500,000 = 2⁵·5⁶` and
`524,288 = 2¹⁹` have none, so **no dwell length divides either buffer evenly**.
499,712 works only because the 128-sample blank moves the frame off `15X/2`.

**Blanking budget** (ADR-0005), against 4267 ns:

| term | FIR bypassed | 128-tap FIR |
|---|---|---|
| PIO write → pin, parallel | 8 ns | 8 ns |
| PE42482A-X settle to 0.05 dB, **max** (CITED, Table 3, PDF p9) | 1400 ns | 1400 ns |
| AD9363 analog baseband settle | ~75 ns | ~75 ns |
| AD9363 RX digital chain group delay (ESTIMATED) | ~700 ns | ~4900 ns |
| **total** | **2183 ns → 1.95× margin** | **6383 ns → FAILS by 1.5×** |

---

## 7. Thermal

| part | dissipation | θ_JA | ΔT | note |
|---|---|---|---|---|
| `U_SW` | 0.66 mW (200 µA × 3.3 V) + ≤41 mW of RF at the +20 dBm hot-switch ceiling | 63 °C/W (CITED, Table 4, PDF p9) | **≤2.6 °C** | thermally a non-event. **The exposed pad is there for RF ground, not for heat** — Table 8 calls it "ground for proper operation" |
| `U_MCU` | ~165 mW | ~40 °C/W | ~6.6 °C | |
| `U_LDO` | **308 mW at the envelope**, 123 mW typical | **62 °C/W** (MCP1755S SOT-223-3, CITED, DS20005160B p8, datum JESD51-7 named §5.3.1 p22) against ≤195 required | **19.1 °C** ⇒ Tj 59 °C at Ta 40 | the only real thermal item on the board — see §5 constraint 3. The same table gives SOT-23-5 at **256 °C/W**, which is the primary-source confirmation that the disqualification in §5 is right |

---

## 8. Value index — every component value, and where it comes from

| ref | value | source |
|---|---|---|
| `R_T1`, `R_T2` | 220 Ω ±1 % (C25091) | §3 — tap ratio, main-line IL and RL are all set by this one number |
| `R_S1..R_S4` | 47 Ω ±5 % | §4 — `R_S ≥ Z_line − Z_drv,min` |
| `R_PD1..R_PD4` | 10 kΩ ±5 % | §4 — leakage offset vs `V_IL` margin |
| `R_CC1`, `R_CC2` | 5.1 kΩ ±5 % | §5 — USB Type-C Rd |
| `R_LED1`, `R_LED2` | 680 Ω | §5 — 1.91 mA |
| `C_SW1` / `C_SW2` | 100 nF / 1 µF | §5 |
| `C_BULK` | 4.7 µF | §5 — with `C_LDI`, under the USB 10 µF cap |
| `C_LDI` / `C_LDO` | 1 µF X7R 0805 / 1 µF X7R 0805 | §5 — CLOSED: DS20005160B §4.4 p17, min 1 µF, ESR ≤ 2 Ω, ceramic-stable. 0805 because the floor is on EFFECTIVE capacitance at 3.3 V bias |
| `C_MCU1..4` | 100 nF | §5 |
| XTAL load caps | 15 pF | §5 — CLOSED: `C_L` 10 pF CITED, `C_stray` 3 pF; `2·(10−3)=14` ⇒ 15 pF E24. Same answer as the old `2·(12−5)`, from two corrected inputs |
| `F_IN` | `1206L050/24WR` (C2154056) | §5 — 0.50 A hold / 1.00 A trip, 0.38 A derated at 50 °C |
| `D_TVS` | `SMBJ6.0A` (C83270) | §5 — **6.0 V** standoff, clamp 10.3 V. The 5.0 V standoff conducts at VBUS max |
| `U_LDO` | `MCP1755S-3302E/DB` (C638611) | §5 — SOT-223-3; 500 mV / +17.6 V / 62 °C/W against 1.23 V / 10.3 V / 195 °C/W |
| `U_SW` | PE42482A-X (C5121458) | the D-SPEC sourcing spike, `journal/02_parts.md` |
| `J_ANT*`, `J_RX*` | KH-SMA-KE-Z (C504007) | ditto |
| RF50 track | 0.36 mm | §1 |
| CTRL track | 0.20 mm | §1 |
| USB pair | 0.28 / 0.18 mm | §1 |
| PWR track | 0.40 mm | IR drop and robustness, not ampacity — 0.15 A on 0.40 mm × 35 µm is a ~2 °C rise |
| via fence pitch | ≤1.37 mm | §1 — λg/20 at 6 GHz |
| radial arm | 17.85 mm, all nine | §2 / ADR-0007 |

## 9. What is OWED, so a reader does not mistake absence for completeness

| owed | consequence if it stays owed |
|---|---|
| ~~the `U_LDO` dossier~~ | **CLOSED 2026-07-28** — `MCP1755S-3302E/DB`; E-TOPO now grades a real rail and PASSES (headroom 1230 mV vs 500, PD 307 mW vs 968) |
| ~~the RP2040, QSPI flash, crystal, USB-C and TVS/PPTC dossiers~~ | **CLOSED 2026-07-28** — all nine written; S-VER, P-ESC 13/13 and P-LAYOUT 8/8 all grade them |
| ~~`QFN-24_4x4_P0.5_EP2.7_PE42482` and `SMA_Vertical_5.08sq_D1.4`~~ | **CLOSED 2026-07-28** — both authored from the vendor land drawings into `03_src/lib/pluto_rx2_8way.pretty/`, 48 geometry + 6 silk/courtyard properties verified independently. **A THIRD footprint became owed in their place**: the stock KiCad `USB_C_Receptacle_HRO_TYPE-C-31-M-12` disagrees with the vendor's RECOMMEND P.C.B LAYOUT by up to **0.375 mm** on pad-centre-to-alignment-hole, confirmed against a second HRO sheet two years apart |
| RP2040 pad output impedance (ESTIMATED 25 ± 10 Ω) | §4's table is derived from an estimate; 47 Ω holds across the whole bar, which is why the estimate is tolerable |
| the AD9363 RX digital-chain group delay (ESTIMATED ~0.7 µs / ~4.9 µs) | §6's margin is 1.95× on an estimated term; a bench measurement at bring-up is a CHECKLIST item |
| SMA launch dissipative loss (vendor publishes none) | §2's 0.10 dB per launch is a LOWER bound |
| port-to-port isolation across ten SMA barrels | bounds the AoA leakage budget from below, independently of the switch. The §4 dark-frame state exists to measure it |
