# detail design: usb-hub-3s-v3 — the math

**Written 2026-07-25 for release v1.5-2026-07-25.** This document was MISSING
until now, although three sealed `02_parts/*/part.yaml` files have cited its
section numbers as authority since 2026-07-21 (audit finding PCBA-7):

    02_parts/AON6403/part.yaml:27          -> sec.1
    02_parts/LM5116MHX-NOPB/part.yaml:48   -> sec.2
    02_parts/USBLC6-2SC6/part.yaml:25      -> sec.5

Those three sections are therefore written first and in full. **Section 5 also
records a DEVIATION**: the citation in `USBLC6-2SC6/part.yaml` describes a
design this board does not implement, and the part it names is not the part
fitted — see sec.5.3.

**Rules of this file** (01_docs/contracts.md): every component value that came
from a calculation gets the equation, the inputs, the result, and the chosen
E-series value. A value in the schematic with no line here is UNJUSTIFIED.

**Sources.** Equation numbers `(n)` are TI's own, from **LM5116 datasheet
SNVS499I** (Feb 2007, rev. Nov 2023), section 7.2.2, read 2026-07-25 from
`02_parts/LM5116MHX-NOPB/SNVS499I.pdf`. The buck cell is TI's **5 V / 7 A
worked design** (Figure 7-1 + Table 7-1, pp. 21-22) adopted per canon M6, with
four values re-derived for THIS board's envelope (marked **[re-derived]**).
Part limits are quoted from `02_parts/<MPN>/part.yaml`, each of which records
the datasheet page it was read from.

**Envelope** (`03_src/rules/power_tree.yaml`): V_IN 9.0-12.6 V (3S LiPo),
two independent LM5116 synchronous bucks, 5VA ≤ 6 A (3 × USB-A) and 5VC ≤ 5 A
(1 × USB-C, Pi-dedicated). Board `usb_hub_3s_v2`, 130.1 × 92.1 mm, 4 layer.

---

## sec.1 — Input protection cell (F1 → Q1 → D2 → D1 → C1/C2 → VIN)

Cited by `02_parts/AON6403/part.yaml:27`.

    XT60 (J1) --> F1 10A MINI blade --> VBAT_F --> Q1 (AON6403 P-FET) --> VIN
                                                     |                    |
                                                 R1 100k              D1 SMBJ15A
                                                 D2 BZT52C12          C1,C2 100uF/35V

### 1.1 Q1 — reverse-polarity pass element (AON6403, P-channel)

Wiring: **D(pad 5) = VBAT_F** (battery side), **S(pads 1-3) = VIN** (load
side), **G(pad 4) = RPP_G**.

A P-channel body diode conducts **drain → source**, i.e. VBAT_F → VIN. So:

- **Correct polarity.** The body diode conducts on first contact and brings VIN
  up. R1 (100 kΩ) then holds the gate at GND, so
  `Vgs = V_G − V_S = 0 − V_IN = −9.0 … −12.6 V` — fully enhanced, and the body
  diode is shorted out by the channel.
- **Reversed pack.** VBAT_F sits below GND, so the body diode (which needs
  V_D > V_S) is reverse-biased and **blocks**. The gate is held at GND by R1
  and the source sits near GND through the load, so `Vgs ≈ 0` — the channel is
  off too. Blocking stress `|V_DS| ≤ 12.6 V` against **V_DS = 30 V** rated.

**Conduction loss.** R_DS(on) ≤ **4.3 mΩ** at Vgs = −4.5 V (worse than the
actual −9 … −12.6 V drive, so conservative). At the 7.12 A worst-case trunk
(sec.6): `P = 7.12² × 4.3 mΩ =` **0.218 W**, spread into the input pour with
thermal vias (R-THERM waiver).

### 1.2 D2 — the gate clamp, and why it is not optional

AON6403 gate rating is **Vgs = ±20 V**. In normal operation `|Vgs| ≤ 12.6 V`,
which is inside the rating — so at first glance D2 looks redundant. It is not:

`D1` (SMBJ15A) clamps a VIN transient at up to **V_CL = 24.4 V @ I_PP 24.6 A**
(`02_parts/SMBJ15A/part.yaml`). During that event the source (VIN) is at 24.4 V
while R1 holds the gate at GND, giving `Vgs = −24.4 V` — **4.4 V beyond the
gate rating**, which is a gate-oxide failure, not a derating discussion.

D2 = **BZT52C12**, a 12 V zener with **cathode on VIN (the source)** and
**anode on RPP_G (the gate)**. Above 12 V of source-to-gate differential it
conducts and holds `|Vgs| ≈ 12 V`. R1 sets the clamp current:

    I_R1 = (V_IN − V_Z) / R1 = (24.4 − 12) / 100 kΩ = 124 uA

— negligible for a SOD-123 zener, and negligible as a standing loss at normal
V_IN (12.6 V < 12 V + a diode, so it barely conducts at all in steady state).

R1 = 100 kΩ is the same value used for the Q6 gate pull-up (R30); the choice is
"high enough that the zener leg costs nothing, low enough that the gate cannot
float" — at 100 kΩ the gate is pulled down against Q1's ~1 µA I_GSS with a
100 mV error.

### 1.3 D1 — input TVS, and its POSITION

`D1` sits on **VIN, i.e. AFTER Q1**, not on VBAT_F. This is deliberate and was
the v1.0 defect (`INV-D1-PLACEMENT`, ADR-0001): with the TVS ahead of the
blocking element, a reversed pack forward-biases the TVS into a dead short
across the battery through a 10 A fuse. Behind Q1's blocking body diode, a
reversal is non-destructive.

Standoff **15.0 V** > 12.6 V max pack ✓. V_BR **16.7-18.5 V @ 1 mA**, so it is
clear of the operating rail. Downstream survivability at V_CL = 24.4 V:

| part on VIN | rating | 24.4 V clamp |
|---|---|---|
| LM5116 VIN | 100 V | ✓ huge |
| Q2-Q5 AON6354 | V_DS 30 V, V_spike 36 V (10 µs) | ✓ |
| Q1 AON6403 | V_DS 30 V | ✓ |
| C1/C2 polymer | **35 V** | ✓ |
| C9-C12 / C24-C27 MLCC | **50 V** | ✓ |
| Q1 gate | ±20 V | **✗ without D2** — see 1.2 |

### 1.4 C1 / C2 — input bulk

2 × **100 µF / 35 V polymer aluminium** (KNM2100UF35V149EC0055, C2982822) at
the entry, `pin 1 = VIN (+)`, `pin 2 = GND`. 35 V on a 12.6 V rail = 36 % of
rating, and it survives the 24.4 V D1 clamp corner (1.3).

> **THESE PARTS ARE POLARIZED AND THIS IS WHERE v1.4 DIED.** Sealed v1.4
> placed both at CPL 270.0 where the measured correct value is 90.0 —
> 180° reversed, directly across the pack. See
> `08_reviews/2026-07-25_v1.4_pcba-audit_assembly.md` PCBA-1. JLC's own library
> silk draws a **“+” over its pad 1** (two crossed filled polygons centred at
> −2.706, 1.518) and a **“−” over pad 2**; our pad 1 is on VIN. Both agree, and
> the CPL now says 90.0.

---

## sec.2 — The LM5116 buck cells (buck-A → 5VA, buck-C → 5VC)

Cited by `02_parts/LM5116MHX-NOPB/part.yaml:48` (for 2.9, UVLO).

Both cells are structurally identical (`Buck` component in
`03_tscircuit/src/usb_hub_3s_v2.tsx`); only the FB top resistor differs.
Refdes are given as **buck-A / buck-C**.

### 2.1 Switching frequency — R2 / R11 = 12.4 kΩ

TI eq. **(7)**:

    R_T = ( 1/f_SW − 450 ns ) / 284 pF

    f_SW = 250 kHz  ->  R_T = (4.000 us − 0.450 us) / 284 pF = 12.5 kOhm

Nearest standard **12.4 kΩ** → back-solving, `f_SW = 1/(12.4 kΩ × 284 pF +
450 ns) = 1/(3.5216 µs + 0.450 µs) =` **251.8 kHz**. Used as 250 kHz
throughout. Same value as TI's worked design (R9 = 12.4 kΩ).

Duty cycle: `D = V_OUT/V_IN` → 5VC runs **42.5 %** at 12.6 V and **59.5 %** at
9.0 V. Both far from the LM5116's minimum on-time and from 100 %.

### 2.2 Output inductor — L1 / L2 = 6.8 µH  **[re-derived]**

TI eq. **(8)**, solved for ripple with the chosen part:

    I_PP = V_OUT / (L × f_SW) × ( 1 − V_OUT / V_IN(max) )

    I_PP = 5 / (6.8 uH × 250 kHz) × (1 − 5/12.6) = 2.941 × 0.6032 = 1.774 A

TI's example used 6 µH for a 7 A / 60 V design (40 % ripple). We use **6.8 µH**
(Sunlord MWSA1206S-6R8MT, C408523) because V_IN(max) is 12.6 V rather than
60 V, and because 6.8 µH is the stocked molded part with the needed saturation
margin. Resulting ripple:

| | I_PP @ V_IN 12.6 V | as % of full load | I_PP @ V_IN 9.0 V |
|---|---|---|---|
| buck-A (6 A) | 1.774 A | **29.6 %** | 1.307 A |
| buck-C (5 A) | 1.774 A | **35.5 %** | 1.307 A |

Both inside TI's recommended 20-40 % band, at the high-V_IN corner where ripple
is worst.

**Saturation and rms** (`02_parts/MWSA1206S-6R8MT/part.yaml`: I_sat(−20 %)
**15.2 A**, I_sat(−30 %) 19 A, I_rms 10-12 A, DCR ≤ **13.5 mΩ**):

    steady-state peak, buck-A = 6 + 1.774/2 = 6.89 A      < 15.2 A  ✓
    steady-state peak, buck-C = 5 + 1.774/2 = 5.89 A      < 15.2 A  ✓
    fault peak = the current limit I_LIM = 11.0 A (2.5)   < 15.2 A  ✓
    rms, buck-A = 6 A                                     < 10 A    ✓

DCR loss: `6² × 13.5 mΩ =` **0.486 W** (buck-A), `5² × 13.5 mΩ =` 0.338 W
(buck-C).

### 2.3 Output capacitance — 4 × 100 µF/10 V per rail

C14-C17 (5VA) and C29-C32 (5VC): **GRM32ER61A107ME20L**, 100 µF **10 V** X5R
1210 (C84455). `part.yaml` records the measured DC-bias derating: **≈ 45 µF
effective at 5 V**, so `C_OUT = 4 × 45 =` **180 µF**.

TI eq. **(15)**, with ESR = 2 mΩ per cap / 4 in parallel = **0.5 mΩ**:

    dV_OUT = I_PP × sqrt( ESR² + (1 / (8 × f_SW × C_OUT))² )
           = 1.774 A × sqrt( (0.5 mOhm)² + (1/(8 × 250k × 180u))² )
           = 1.774 A × sqrt( 0.25 + 7.717 ) mOhm
           = 1.774 A × 2.822 mOhm
           = 5.0 mV p-p

5 mV on a 5 V rail = 0.1 %. The 10 V rating (raised from 6.3 V in v1.1) puts
5 V at 50 % of rating rather than 79 %, which is what buys the 45 µF instead of
a much worse number.

### 2.4 Input capacitance — 4 × 10 µF/50 V + 100 nF per rail

C9-C13 (buck-A) and C24-C28 (buck-C): **GRM32ER71H106KA12L**, 10 µF **50 V**
X7R 1210 (C77102) — `part.yaml` records **≈ 8 µF effective at 12.6 V** bias, so
`C_IN = 4 × 8 =` **32 µF** per cell, plus a 100 nF 0603 at the FET drain.

TI eq. **(17)**:

    dV_IN = I_OUT / (4 × f_SW × C_IN)
    buck-A: 6 / (4 × 250 kHz × 32 uF) = 0.188 V
    buck-C: 5 / (4 × 250 kHz × 32 uF) = 0.156 V

**2.08 %** of the 9.0 V low rail (buck-A) and 1.73 % (buck-C). The 50 V rating
(raised from 25 V in v1.1) is what keeps effective C at 8 µF rather than
collapsing under 12.6 V bias.

### 2.5 Current limit — RS1 / RS2 = 10 mΩ

`VCCX` is tied to GND on both cells (pin 17 → `net.GND`), so **V_CS(TH) =
0.11 V** (TI's stated value for VCCX = 0 V).

TI eq. **(10)** — the limit itself:

    I_LIM = V_CS(TH) / R_S = 0.11 V / 10 mOhm = 11.0 A  (valley-referenced peak)

TI eq. **(11)** — the constraint R_S must satisfy, at V_IN(min) = 9.0 V:  **[re-derived]**

    R_S <= V_CS(TH) / [ I_O + V_OUT/(2 × L × f_SW) × (1 + V_OUT/V_IN(min)) ]

    common term: 5/(2 × 6.8u × 250k) × (1 + 5/9) = 1.4706 × 1.5556 = 2.2876 A
    buck-A: R_S <= 0.11 / (6 + 2.2876) = 0.11 / 8.2876 = 13.3 mOhm   ✓ 10 mOhm
    buck-C: R_S <= 0.11 / (5 + 2.2876) = 0.11 / 7.2876 = 15.1 mOhm   ✓ 10 mOhm

Shunt = **25121WF100MT4E**, 10 mΩ 1 % **1 W** 2512 (C127692).
`P = 6² × 10 mΩ =` **0.36 W** (buck-A), 0.25 W (buck-C) — both inside 1 W.
CS/CSG reach the shunt as a Kelvin pair through 0 Ω links (R9/R10, R18/R19) so
no shared trunk copper enters the sense loop.

### 2.6 Ramp capacitor — C3 / C18 = 330 pF  **[re-derived]**

TI eq. **(13)**, with g_m = 5 µA/V (ramp generator) and A = 10 V/V (current
sense amplifier gain):

    C_RAMP = g_m × L / (A × R_S) = (5 uA/V × 6.8 uH) / (10 V/V × 10 mOhm)
           = 3.4e-11 / 0.1 = 340 pF

Next lower standard value: **330 pF** (C0G, ≤5 %). This is exactly why our
value differs from TI's 270 pF — TI's L was 6 µH, ours is 6.8 µH. Placed hard
against RAMP(5)/AGND per the datasheet layout section.

### 2.7 Soft start — C6 / C21 = 10 nF

TI eq. **(23)**:

    t_SS = C_SS × 1.215 V / 10 uA = 10 nF × 1.215 / 10 uA = 1.215 ms

TI eq. **(22)** requires `t_SS > V_OUT × C_OUT / (I_LIM − I_OUT)`:

    buck-A: 5 × 180 uF / (11 − 6) = 180 us    <<  1.215 ms  ✓
    buck-C: 5 × 180 uF / (11 − 5) = 150 us    <<  1.215 ms  ✓

### 2.8 VCC, bootstrap and boot diode — 1 µF, 1 µF, 1N4148WS

`C_VCC` = **1 µF** (TI: "no smaller than 0.47 µF", 1 µF selected).
`C_HB` = **1 µF** (TI eq. (21): `C_HB ≥ Q_g/ΔV_HB`, and TI's guidance "at least
0.1 µF, typically <5 % droop on VCC"; 1 µF gives ≪1 % droop against the
AON6354 gate charge).
The LM5116 has **no internal boot diode** — D3/D4 = 1N4148WS (C2128) from VCC
to HB is REQUIRED, not optional (`part.yaml` gotcha, from the ledger).
`VCCX` unused → tied to GND, never left open (`part.yaml` gotcha).

### 2.9 UVLO — R6/R7 and R15/R16 = 49.9 kΩ / 6.98 kΩ  **[re-derived]**

**This is the section `02_parts/LM5116MHX-NOPB/part.yaml:48` cites.**

The UVLO pin has a **1.215 V rising threshold, 0.1 V of pin hysteresis, and a
5 µA pull-up into the pin**. That 5 µA is not a rounding detail — it moves the
threshold by 250 mV, and omitting it is what produced the "9.90 V" figure that
appears in the v1.0 red-team report.

Rising, at the threshold the divider bottom carries `1.215/6.98 k = 174.07 µA`,
of which 5 µA is supplied internally, so only 169.07 µA flows through R_top:

    V_IN(rise) = 1.215 V + 169.07 uA × 49.9 kOhm = 1.215 + 8.437 = 9.652 V

Falling, threshold `1.215 − 0.100 = 1.115 V`, bottom current
`1.115/6.98 k = 159.74 µA`, minus the same 5 µA → 154.74 µA:

    V_IN(fall) = 1.115 V + 154.74 uA × 49.9 kOhm = 1.115 + 7.722 = 8.836 V

**9.65 V rise / 8.84 V fall** — matching the values recorded in `part.yaml`.
(Naive divider-only arithmetic gives 9.90 V / 9.09 V, which is wrong by 250 mV.)

**Accepted deviation (RT-T3, P2).** The board is specified 9-12.6 V and silked
"9-12.6V XT60 IN", but it will not cold-start below **9.65 V**. Accepted
because a 3S LiPo at 9.65 V is already at ~3.22 V/cell: the UVLO doubles as
deep-discharge protection. Recorded in ORDER_README section 6 and in
`08_reviews/2026-07-22_v1.0_redteam_topology.md` RT-T3.

### 2.10 Compensation — 18 kΩ + 3.3 nF + 100 pF

R5/R14 = **18 kΩ** (COMP → CMZ), C4/C19 = **3.3 nF** (CMZ → FB), C5/C20 =
**100 pF** (COMP → FB). Adopted **unchanged** from TI's worked design
(Table 7-1: R10 = 18 kΩ, C6 = 3300 pF, C5 = 100 pF) — same controller, same
250 kHz, same 5 V output, and the emulated-ramp current-mode loop's
compensation depends on `L/R_S` which sec.2.6 already matched via C_RAMP.
Loop response is a **bench-verified item** (ORDER_README gate Q3: scope both
SW nodes through startup, shutdown and 0→5 A→0 load steps).

### 2.11 Feedback dividers — the two rails' setpoints

TI eq. **(24)**: `V_OUT = 1.215 V × (1 + R_top/R_bot)`, with R_bot = 1.21 kΩ
(C5126242) on both rails for a ~1 mA divider current.

| rail | R_top | R_bot | V_OUT |
|---|---|---|---|
| **5VA** | R3 = **3.92 kΩ** ±0.1 % (C728591) | R4 = 1.21 kΩ ±1 % | `1.215 × (1 + 3.92/1.21)` = **5.151 V** |
| **5VC** | R12 = **4.12 kΩ** ±0.1 % (C2984354) | R13 = 1.21 kΩ ±1 % | `1.215 × (1 + 4.12/1.21)` = **5.352 V** |

**Why the two differ.** Both loops sense their own LOCAL output (v1.2 fix — the
v1.1 post-eFuse sense caused FB-integrator runaway). 5VC is deliberately set
**+0.2 V high** to pay for the Q6 + F2 delivery drop so the connector still
delivers ≥5.0 V at 5 A (sec.4). 5VA is **not** raised, because the USB-A window
ceiling is 5.25 V and a proportional bump would push its no-load corner to
5.35 V — over the port limit. The local-sense principle is shared; the value is
set by each rail's own window.

**Both R_top parts are ±0.1 %, on purpose.** R12 is the part that killed v1.2:
the code was omitted, tscircuit value-resolved "4.12k" to C2933210 =
FRC0603F3741TS = **3.74 kΩ**, and 5VC regulated to 4.97 V. The LCSC code is now
BAKED in the TSX for both. **DO-NOT-USE C2933210.**

---

## sec.3 — USB-A port cells (×3)

Each port: **TPS2557** current-limited switch → **USBLC6-2SC6** ESD array →
KH-AF90DIP-112 receptacle, with **TPS2513A** (U6, U7) providing the BC1.2 DCP
charging advertisement (one dual-channel chip serves two ports; 2 chips, 3
ports used, channel 2 of U7 floats with no-connect flags).

**Current limit.** R20/R21/R22 = **36.5 kΩ** 1 % on ILIM. From
`02_parts/TPS2557DRBR/part.yaml` (verified against SLVS931B):
`I_OS(min) = 127981 / R(kΩ)^1.0708 mA`

    I_OS(min) = 127981 / 36.5^1.0708 = 127981 / 47.10 = 2717 mA = 2.72 A
    I_OS range (part.yaml, verified): 2.72 - 3.29 A

against a **2 A continuous / 2.5 A burst** per-port spec — the limit sits above
the working load and below the connector's ratings. Three ports × 2 A = **6 A**
= buck-A's declared `iout_max_A` exactly.

**Decoupling.** 100 nF at IN (C35/C36/C37, datasheet pin-table requirement),
22 µF at OUT (C38/C39/C40, C29277) + 100 nF (C41/C42/C43).

**EN is ACTIVE HIGH** on the TPS2557 (the TPS2556 is the active-low twin) and
is tied to 5VA — the ports come up with the rail. `FAULT` is open-drain and
unused, left floating with a no-connect flag.

---

## sec.4 — Rail worst-case corners and the Pi delivery margin

Worst-case output, `V_OUT = V_ref × (1 + R_top/R_bot)` with V_ref ±1.5 %,
R_top ±0.1 %, R_bot ±1 %:

| rail | nominal | worst MIN | worst MAX |
|---|---|---|---|
| **5VC** | **5.352 V** | `1.215×0.985 × (1 + (4.12×0.999)/(1.21×1.01))` = **5.227 V** | `1.215×1.015 × (1 + (4.12×1.001)/(1.21×0.99))` = **5.479 V** |
| **5VA** | 5.151 V | 5.032 V | 5.273 V |

*(the inner parentheses are load-bearing: R_top and R_bot each carry their own
tolerance factor before the division)*

**The ±1 % on R_bot matters** and was omitted from the v1.3 paperwork
(DISPOSITIONS EXT13-3): Vref-only arithmetic gives 5.272-5.432 V for 5VC, a
window 165 mV narrower than the truth. `03_src/rules/power_tree.yaml` carried
the Vref-only 5.27/5.43 pair until v1.5 and now declares 5.227/5.479.

**E-MARGIN, the Pi rail.** Delivery path 5VC → Pi, modelled in
`03_src/rules/power_tree.yaml`:

    Q6 AON6403 R_DS(on)      ~4.3 mOhm
    F2 SMD2920-700 PPTC      18 mOhm cold (R1max) / ~31 mOhm hot at 5 A
    board pours + vias       ~12 mOhm  MEASURED (see below) -- was a ~3 mOhm guess
    USB-C connector          ~5 mOhm  (VBUS pins A4/B4/A9/B9 in parallel)
    0.3-0.5 m 5 A cable      ~45 mOhm  (REQUIRED, ORDER_README section 5)
    -------------------------------------
    total                    ~97 mOhm  ->  IR at 5 A = 485 mV

    headroom      = V_5VC(min) − V_UV(Pi) = 5.227 − 4.63       = 597 mV
    raw IR drop   = 97 mOhm x 5 A                              = 485 mV
    E-MARGIN need = raw IR x 1.20 derate (power_topology.py)   = 582 mV
                                              ->  PASS, slack = 15 mV

**The board-copper term is MEASURED, not estimated** (v1.5 layout red-team
RL-2, `08_reviews/2026-07-25_v1.5_redteam_layout.md`). Numerical mesh solve,
0.3 mm cells over F.Cu + B.Cu + vias, solver validated against analytic bars
and found to read 10-20 % LOW:

    5VC   L2.2 -> Q6 tab     2.198 mOhm
    PMID  Q6.S -> F2.1       4.914 mOhm
    VBUSC F2.2 -> J5         2.209 mOhm
                  total   >= 9.32 mOhm   (true ~10.4-11.6; carried as 12)

**Three figures have been published for this one margin — use 15 mV.** Each
revision removed an optimistic assumption and none of them changed the
hardware: **157 mV** (Vref-only corner, no derate, 3 mΩ board) → **69 mV**
(tolerance-inclusive corner + the gate's 1.20 derate, 3 mΩ board) → **15 mV**
(the same, plus the measured board copper).
`power_topology.py` grades `headroom >= ir_budget x (1 + margin)` with `margin`
defaulting to **0.20**, so 582 mV is the number that decides the gate.
`03_src/rules/power_tree.yaml` now declares `ir_budget_mohm: 97`; E-MARGIN
re-run against it: **PASS**.

**15 mV of paper slack is not a margin to ship on.** `power_topology.py` grades E-MARGIN as
`headroom >= ir_budget x (1 + margin)` with `margin` defaulting to **0.20**, so
the number that decides the gate is 528 mV, not the raw 440 mV. Comparing
597 mV against the un-derated 440 mV gives a flattering 157 mV that appears in
the v1.4 paperwork and is not the gate's number (v1.5 fresh lens, P2-2). The
honest slack is **69 mV**.

Worst-case cable-end estimate `5.227 − 0.485 =` **4.74 V**, above the Pi's
4.63 V ±5 % undervoltage trip by ~110 mV. **This is thin, and the paper margin is not the
gate** — ORDER_README Q2/Q5 measure VBUSC at the board and at the far end of
the actual cable, hot, at 5 A. Note that Q5's acceptance floor (≥4.80-4.85 V)
sits *above* this 4.74 V paper estimate **deliberately**: the estimate is the
quadruple-worst corner (Vref low AND R13 high AND F2 fully hot AND a marginal
cable), while Q5 is a REQUIREMENT ON THE DELIVERED SYSTEM — if the measurement
lands below the floor the answer is a shorter/better cable, or the documented
setpoint mitigation, not a re-labelled pass. Mitigation: R12 4.12 k → 4.22 k
(5VC → 5.453 V), spending D5/no-load-OV margin.

---

## sec.5 — Port protection and ESD

**This is the section `02_parts/USBLC6-2SC6/part.yaml:25` cites as the
authority for the C-port ESD choice.**

### 5.1 USB-C VBUS chain (discrete, SECONDARY — ADR-0002, BRIEF A3/D3)

    5VC --> Q6 (AON6403 P-FET, reverse-block, ENABLE-GATED) --> PMID
        --> F2 (SMD2920-700 PPTC, 7 A hold, 16 V) --> VBUSC --> J5
                                                       |
                                          D5 (SMBJ6.0A uni-dir TVS) --> GND

- **Over-current** = F2. 7 A hold (not 6 A): a 6 A part derates to ~4.8 A at
  50 °C, below the 5 A continuous load. 7 A derates to ~5.6 A > 5 A ✓.
  V_max 16 V covers a buck-fail-high to V_IN.
- **Reverse-current / master-off** = Q6. Body diode anode = D = 5VC, cathode =
  S = PMID, so it BLOCKS PMID → 5VC when Q6 is off. Q7 (BSS138) inverts ENKILL
  onto the gate; R30 (100 kΩ) pulls the gate to its own source (PMID) when Q7
  is off. OFF-state back-feed leaves `Vgs ≈ −(1 µA × 100 kΩ) = −0.1 V`, far
  below AON6403 V_GS(th) → Q6 stays off. R30 at 100 kΩ costs
  `5.35 V / 100 kΩ =` **54 µA** when on (the v1.2 wrong-part 3.09 kΩ cost
  1.7 mA).
- **Over-voltage** = D5, and it is **best-effort, not a cutoff**. V_WM 6.0 V
  clears the 5.479 V no-load corner by **521 mV**; V_BR 6.67-8.15 V @ 1 mA;
  V_CL ~10.3 V at full I_PP — which is **above** the Pi's VBUS ceiling. On a
  buck high-side short D5 clamps and F2 must trip to end the exposure: a
  crowbar, not a guaranteed cutoff. Accepted for a supervised prototype with a
  replaceable Pi. Escalation boundary, verbatim: *"add active OVP if the system
  becomes unattended, hard-access, carries valuable storage, or powers
  expensive SDR"*.

### 5.2 Data-line ESD

All four USB ports use **USBLC6-2SC6** (C7519): U8/U9/U10 on the three USB-A
ports, **U12 on the USB-C port**. Pass-through pairs 1-6 (D+) and 3-4 (D−),
GND on pin 2, and the V_BUS transil on pin 5 tied to that port's VBUS rail.
`R27` (0 Ω) shorts DPC to DMC as the BC1.2 DCP advertisement on the C port;
R28/R29 (10 kΩ) are the CC1/CC2 Rp pull-ups to VBUSC, advertising a 3 A source
(the Pi takes 5 A via `PSU_MAX_CURRENT=5000`, not via PD — ADR-0001).

### 5.3 **DEVIATION — U12 on the C rail runs above the USBLC6's characterized standoff**

`02_parts/USBLC6-2SC6/part.yaml:25` states:

> "VBUS pin rated 5.25V - usable on USB-A ports ONLY; NOT on the 20V C port
> (DETAIL_DESIGN sec.5: C port uses LESD5D5.0 bidirectional diodes)"

**Three things about that sentence are now false**, and this section replaces
it as the authority:

1. There is **no 20 V C port**. v3 removed the TPS25740A PD cell (ADR-0001);
   the C port is a plain 5 V rail.
2. **LESD5D5.0 is not fitted.** The board fits **U12 = USBLC6-2SC6, C7519** —
   the same part as the three USB-A ports.
3. **5.25 V is not an absolute maximum.** Read from the ST datasheet directly
   (USBLC6-2, Doc ID 11265 Rev 5, `02_parts/USBLC6-2SC6/USBLC6-2SC6_ST.pdf`
   p.2, 2026-07-25): **Table 1 "Absolute ratings" contains no V_BUS voltage
   limit at all** — only V_PP, T_stg, T_j and T_L. 5.25 V is the **test
   condition** at which Table 2 specifies leakage `I_RM` (typ 10 nA, **max
   150 nA**). The real device limit is **V_BR = 6 V minimum at I_R = 1 mA**.

**Measured exceedance** (sec.4 corners against the datasheet numbers):

| | value | vs V_RM 5.25 V | vs V_BR min 6.0 V |
|---|---|---|---|
| 5VC nominal (U12) | **5.352 V** | **+102 mV** | −648 mV |
| 5VC worst static corner (U12) | **5.479 V** | **+229 mV** | **−521 mV** |
| 5VA worst static corner (U8/U9/U10) | 5.273 V | +23 mV | −727 mV |

**Failure mode, stated precisely.** At 5.479 V the V_BUS transil is at least
521 mV below its *minimum* 1 mA breakdown knee, so it does not clamp and does
not conduct meaningfully. The exposure is **elevated reverse leakage above the
characterized point**, worsened by temperature (datasheet Figure 4: leakage
rises ~30× from T_j 25 °C to 125 °C) — bounded at roughly
`150 nA × 30 ≈ 4.5 µA ≈ 25 µW`. Negligible against a 5 A rail, and it does not
enter the E-OFF quiescent budget because VBUSC collapses when Q6 opens.

**Note that U8/U9/U10 are in the same class**, an order of magnitude smaller:
their nominal 5.151 V is comfortably under 5.25 V but the worst static corner
5.273 V is +23 mV over it. Same mechanism.

**Decision: ACCEPT + MEASURE** (user decision 2026-07-25).

- **R12 is NOT changed.** Lowering 5VC spends the E-MARGIN headroom the Pi rail
  needs: sec.4's low corner leaves only **15 mV** of slack once the gate's own
  1.20 derate and the MEASURED board copper are applied (597 mV headroom vs
  582 mV required). Trading a 229 mV
  leakage-regime exceedance for undervoltage on the load is the wrong trade.
- Bench gate **Q1 now RECORDS the measured VBUSC and VBUSA values** rather than
  only passing/failing them, so the real exceedance on real hardware is a
  number in the record and not an inference from corners.
- The derating ships as an **evidence-backed waiver in the v1.5 MANIFEST**
  (canon M4: the measurement, not a rationale).

### 5.4 Ordering note — U12 conducts before D5 in the declared fault case

An honest consequence of 5.3, recorded rather than left to be discovered:

    U12 V_BUS transil V_BR  = 6.00 V min       (ST Table 2)
    D5 SMBJ6.0A       V_BR  = 6.67 - 8.15 V    (02_parts/SMBJ6.0A/part.yaml)

So on a **slow** VBUSC rise, U12's V_BUS transil enters breakdown **before** D5
does. U12 is a SOT-23-6 ESD array characterized for 8/20 µs surges, not for
continuous conduction, so in that window it is effectively a sacrificial
first-responder.

This does not affect normal operation (the 5.479 V top corner is 521 mV below
U12's V_BR minimum, sec.5.3) and it does not change the accepted posture: a
buck high-side short is *already* declared as protected only on a best-effort
basis (5.1, ADR-0002). It is recorded so that a future revision adding active
OVP knows U12 is part of what the current design would spend, and so nobody
reads "D5 protects VBUSC" as covering U12. Filed as PCBA-15 (P2, recorded).

---

## sec.6 — Worst-case input current and fuse sizing

Both rails simultaneously at maximum — which this board's own use case reaches
(three charging ports plus a Pi):

    P_out = 5.151 V × 6 A  +  5.352 V × 5 A  =  30.91 + 26.76  =  57.67 W
    P_in  = P_out / eff    =  57.67 / 0.90    =  64.08 W
    I_in(max) = P_in / V_IN(min) = 64.08 / 9.0 = 7.12 A

**F1 = 10 A MINI (ATM) blade fuse** (holder Keystone 3568, C5249699; element
user-fitted). `7.12 / 10 =` **71 % of nominal rating** at the worst corner —
inside the ~75 % continuous derating blade fuses are normally held to, but
without much room at elevated ambient. Two things bound the risk: this corner
requires both rails at absolute maximum *and* a nearly-flat pack, and the
element is a user-fitted consumable that can be re-rated without a board
change. **Recorded, not waived** — thermal behaviour at the F1 clips is part of
ORDER_README gate Q4 (thermal soak at full load).

At the nominal 12.6 V full-charge corner the same power draws `64.08 / 12.6 =`
**5.09 A**, i.e. 51 % of the fuse rating.

---

## sec.7 — Value → source traceability

| value | refdes | source |
|---|---|---|
| 12.4 kΩ (R_T) | R2, R11 | TI eq. (7) @ 250 kHz; = TI Table 7-1 R9 |
| 6.8 µH | L1, L2 | TI eq. (8) **[re-derived]** for V_IN(max) 12.6 V; sec.2.2 |
| 10 mΩ | RS1, RS2 | TI eq. (10)/(11) **[re-derived]** for 6 A / 9.0 V; sec.2.5 |
| 330 pF (C_RAMP) | C3, C18 | TI eq. (13) **[re-derived]** for L = 6.8 µH; sec.2.6 |
| 10 nF (C_SS) | C6, C21 | TI eq. (22)/(23); = TI Table 7-1 C3 |
| 18 kΩ + 3.3 nF + 100 pF | R5/C4/C5, R14/C19/C20 | TI Table 7-1 R10/C6/C5, adopted unchanged; sec.2.10 |
| 49.9 kΩ / 6.98 kΩ | R6/R7, R15/R16 | LM5116 UVLO **[re-derived]** incl. the 5 µA pull-up; sec.2.9 |
| 3.92 kΩ / 1.21 kΩ | R3 / R4 | TI eq. (24) for 5.151 V; sec.2.11 |
| 4.12 kΩ / 1.21 kΩ | R12 / R13 | TI eq. (24) for 5.352 V; sec.2.11 + sec.4 |
| 4 × 100 µF/10 V | C14-C17, C29-C32 | TI eq. (15) with measured 45 µF effective; sec.2.3 |
| 4 × 10 µF/50 V | C9-C12, C24-C27 | TI eq. (17) with measured 8 µF effective; sec.2.4 |
| 1 µF (C_VCC, C_HB) | C8/C7, C23/C22 | TI 7.2.2.8 / 7.2.2.9 + eq. (21); sec.2.8 |
| 100 kΩ | R1 | Q1 gate pulldown + D2 clamp current; sec.1.2 |
| 100 kΩ | R30 | Q6 gate pull-up; sec.5.1 |
| 100 kΩ | R8, R17 | LM5116 EN pull-up to VIN (ENKILL bus); E-OFF budget |
| 12 V zener | D2 | Vgs clamp vs the 24.4 V D1 corner; sec.1.2 |
| SMBJ15A | D1 | 15 V standoff > 12.6 V; sec.1.3 |
| SMBJ6.0A | D5 | 6.0 V standoff > 5.479 V corner; sec.5.1 |
| 36.5 kΩ | R20-R22 | TPS2557 I_OS 2.72-3.29 A; sec.3 |
| 10 kΩ | R28, R29 | USB-C CC Rp, 3 A source advertisement; sec.5.2 |
| 2.2 Ω + 1 nF | R34/C53, R35/C54 | SW-node RC snubber, populate-by-default, tune on bench (gate Q3) |
| 10 A MINI blade | F1 | 7.12 A worst-case trunk = 71 % of rating; sec.6 |
