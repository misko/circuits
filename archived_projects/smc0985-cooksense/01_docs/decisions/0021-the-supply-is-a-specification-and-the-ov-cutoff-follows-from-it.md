# ADR-0021 — the supply envelope becomes a COMMISSION FACT (4.85–5.25 V),
# and the eFuse OV cutoff is re-derived from it

status: accepted
date: 2026-07-28
tags: protection, topology

## Context

Two independent defects on this board had one root cause, and it was an
omission rather than a mistake.

**BRIEF §3.5 commissions "keyed 2-pin Micro-Fit 5V SELV >=2A (pref 3A)" and
states NO TOLERANCE.** Everything downstream then had to guess a corner, and
the two things that guessed guessed differently:

- **`power_tree.yaml` guessed LOW** (`vin_min: 4.5`, a ±10 % brick) and E-TOPO
  has FAILED since v1.5 — headroom 4.500 − 3.399 = 1101 mV against the AMS1117's
  cited 1300 mV dropout, short 199 mV. The file said, correctly, that raising
  the number to make a gate pass would be fitting a number to a gate.
- **`ORDER_README` §0 guessed HIGH** and told the buyer to hold ≥ 4.85 V, as a
  *mitigation*. So the gate graded a supply the order document forbade. Two
  homes for one fact, and the one the gate read was the one nobody was allowed
  to buy — the v1.6 adversarial audit said exactly this (Sec. E part 1).
- **`R_OVT` 100 k / `R_OVB` 15 k guessed nothing at all.** Ratio 0.130435
  against SLVSE57C's `V_OVLO(R)` 1.13/1.20/1.27 V puts the eFuse's OV cutoff at
  **9.200 V nominal, 8.492–9.933 V worst case**, on a rail feeding thirteen
  DIP05-1A72-13L reed coils rated **7.5 V max** and a `D_TVS` SMBJ5.0A whose
  `V_BR` **starts at 6.40 V**. At the 9.996 V top corner the TVS passes ≈6.6 A
  and dissipates ≈66 W: a 600 W *transient* part asked to be a DC regulator.
  Both v1.7 red-team lenses found this independently. It is a P0.

And the OVLO could not be fixed without the supply decision. At the declared
`vin_max` **5.5 V** the admissible divider window is

    k  in  ( V_OVLO(R)max / 6.40 ,  V_OVLO(R)min / 5.50 )
        =  ( 1.27/6.40 , 1.13/5.50 )  =  ( 0.198437 , 0.205455 )  — 1.0354× wide

which is narrower than the spread of any real divider once temperature is
carried. **The v1.7 pass reported this correctly and for the wrong reason**, and
the correction matters because the wrong reason would mislead the next reader:
it took the ±1 % spread as (1.01/0.99)² = 1.0408×, which is the spread of a
ratio of two INDEPENDENT resistors. A DIVIDER has `RB` in both numerator and
denominator:

    k = RB/(RT+RB),  r = RT/RB
    k_max/k_min = (1.01/0.99) · (1.01r + 0.99)/(0.99r + 1.01) = **1.0322×** at r ≈ 3.83

so on tolerance alone a ±1 % divider *did* fit at 5.5 V, with 0.3 % to spare.
What actually kills it is the term neither lens carried: **±100 ppm/°C TCR over
−20…+70 °C is another ±0.45 % per leg**, taking the spread to 1.0472× — wider
than the 1.0354× window. The conclusion stands; the algebra behind it did not.

## Options

- **Keep the loose envelope and change the TVS to SMBJ6.0A** (`V_R` 6.0,
  `V_BR` min 6.67 V). Opens the window to 1.1122× and would fit easily.
  REJECTED for this revision: `V_C` rises 9.2 → 10.3 V, which moves an abs-max
  requirement onto the LDO and the eFuse, and it is a protection-device swap on
  a board whose reviewers have not seen it. Recorded as the standing candidate
  for the SMBJ5.0A stand-off finding below, not taken here.
- **Keep the loose envelope and use 0.1 % thin-film legs.** Fits arithmetically.
  REJECTED: it buys margin by buying an exotic part for a problem that a
  one-line specification solves, and it leaves E-TOPO failing.
- **`R_OVB` 15 k → 22 k** (v1.7 layout lens). **REFUTED**: latest trip 7.223 V,
  above the TVS's 6.40 V — it moves the defect rather than removing it.
- **`R_OVT` 100 k → 57.6 k** (v1.7 topology lens). **REFUTED at 5.5 V**: puts
  the EN pin at 1.1545 V against a 1.13 V minimum threshold, i.e. it
  nuisance-trips inside the declared envelope. (At 5.25 V it would work — it is
  arithmetically equivalent to the choice below — but it is refuted as
  proposed, and changing the TOP leg needlessly moves the resistor that also
  sets the divider's source impedance.)
- **SPECIFY THE SUPPLY, then re-derive.** Chosen.

## Decision

**1. `J_PWR` is specified at 4.850 – 5.250 V DC SELV, ≥ 2 A, measured at the
connector under full load. This is a COMMISSION FACT** (BRIEF D11), binding on
`power_tree.yaml`, ARCHITECTURE.md, the ORDER_README (as a REQUIREMENT of the
order, not advice) and every derived envelope. A ±10 % or generic ±5 % adapter
is **out of specification**; buy ±3 % or a 5.1 V-nominal unit.

**2. `R_OVB` 15 k → 26.1 k; `R_OVT` stays 100 k; BOTH legs become ±0.5 % and
BOTH are code-pinned** (C270658 / C407739 — the same UNI-ROYAL thick-film family
the board already uses, one tolerance grade tighter; stock read live 2026-07-28:
9643 / 227). An auto-picked passive code is a snapshot of a catalog; this pair
sets a protection threshold, and the board has already paid once for a
value-authored safety passive resolving to the wrong code (`R_OS`, v1.2 BOM
defect).

    k_nom = 26.1/126.1 = 0.206979   ->  trip = 1.20/0.206979 = **5.798 V nominal**

inside the 5.5–6 V that `02_parts/TPS259573DSGR` (gotcha 2), ARCHITECTURE.md and
BRIEF §3.5 all state the intent to be.

**WORST CASE**, over −20…+70 °C, both legs at ±0.5 % tolerance **plus** ±100
ppm/°C × 45 °C = ±0.45 % drift (so ±0.95 % each), with SLVSE57C's `I_EN` = ±0.1 µA
across the 20.698 kΩ source impedance (±2.07 mV):

| corner | value | bound it must clear | margin |
|---|---|---|---|
| EARLIEST possible trip `(1.13 − 2.07 mV)/k_max` | **5.3682 V** | spec ceiling 5.250 V — must NOT nuisance-trip | **+118 mV** |
| LATEST guaranteed trip `(1.27 + 2.07 mV)/k_min` | **6.2394 V** | SMBJ5.0A `V_BR` min **6.40 V** @ 25 °C | **+161 mV** |
| same, against the TVS's own temperature coefficient | **6.2394 V** | `V_BR` min at −20 °C = 6.40 × (1 − 0.041 %/°C × 45) = **6.2819 V** | **+43 mV** |
| same | **6.2394 V** | DIP05-1A72-13L coil **7.5 V max** ×13 | **+1261 mV** |

and the *energy* form of the TVS bound, which is the one that actually says
whether the part is sacrificial. Littelfuse publishes two points for SMBJ5.0A —
`I_R` 800 µA at `V_R` 5.00 V and `I_T` 10 mA at `V_BR` 6.40 V — so an
exponential fit (k = ln(10/0.8)/1.40 = 1.804 /V) gives, at the LATEST trip:

    25 °C : 7.5 mA -> 47 mW        -20 °C : 9.3 mA -> 58 mW

against the ≈6.6 A / 66 W the as-built 100 k/15 k divider allows. **The TVS
never leaves its blocking region before the eFuse cuts off.**

±1 % legs would still clear every HARD limit (earliest 5.3260 V, latest
6.2893 V, TVS ≤ 64 mW) and lose only the −20 °C strict-`V_BR` form, by 7 mV — so
a ±1 % substitution is degraded-but-safe rather than a defect. ±0.5 % is chosen
because the margin costs one tolerance grade.

**3. E-TOPO is re-derived at the LDO's OWN node, not at `J_PWR`.** The v1.6
audit's finding was that "hold ≥ 4.85 V" is written at the wrong node, and its
92 mV series-drop figure was an ESTIMATE with no cited term in it. Replaced with
datasheet maxima:

| element | worst case | citation |
|---|---|---|
| F1 `MF-MSMF200/16X` | **70.0 mΩ** | Bourns *MF-MSMF Series – PTC Resettable Fuses*, Electrical Characteristics, `R1Max` column (`RMin` 0.020) |
| `Q_REV` AO3401A | **73.5 mΩ** | AOS AO3401A Rev 3.1 EC table: `RDS(on)` max 60 mΩ @ V_GS −4.5 V / 25 °C, scaled by that table's OWN hot ratio (V_GS −10 V row: 50 → 75 mΩ, 25 → 125 °C = 1.50×) interpolated to a 70 °C junction (1.225×) |
| `U_EFUSE` TPS259573 | **47.0 mΩ** | TI SLVSE57C, "ON-RESISTANCE (IN − OUT)", `RON` MAX, VIN 4–18 V, TJ −40…85 °C |
| total | **190.5 mΩ** | |

At a 0.50 A worst-case simultaneous board draw (0.30 A logic + 0.15 A coil rail
+ 0.02 A `5V_STOP` + ~1.3 mA of TVS leakage, rounded up):

    drop      = 0.50 × 0.1905          =  95.2 mV
    vin_min   = 4.850 − 0.0952         =  4.754 V  at 5V_PROTECTED
    headroom  = 4.754 − 3.399          =  1355 mV   vs dropout 1300 mV  -> PASS +55 mV
    PD        = (5.250 − 3.201) × 0.3  =  615 mW    vs 1200 mW          -> 51 %

**E-TOPO now PASSES.** It still passes at 0.60 A (+37 mV) and with the eFuse's
−40…125 °C row (+53 mV), so the verdict does not hinge on the one interpolated
term. The 1300 mV figure is still the datasheet's **0.8 A** number applied to a
**0.3 A** rail: the true margin is larger by an amount nobody has measured, and
the bring-up measurement that retires that OWED fact (VIN−VOUT at U_LDO at
I_OUT = 0.3 A, three temperatures) is **unchanged and still required**.

## Consequences

- **The order document changes character.** ORDER_README §0 stops being "here is
  a gap and here is how to live with it" and becomes a REQUIREMENT with an
  acceptance measurement. `TP_5VP` (which probes `5V_PROTECTED` directly) gets
  the measurable form: **≥ 4.754 V at full load**, which removes the
  unquantified series drop from the buyer's argument entirely.
- **A supply outside 4.85–5.25 V voids the analysis, and the failure is
  two-sided.** Below 4.754 V at the LDO the 3V3 rail can leave regulation
  (fail-safe: logic browns out, `WD_OK` drops, the coil rail dies). Above
  5.3682 V the eFuse can cut off (fail-safe: the board loses power). Neither is
  a cooking hazard; both are "the machine stops".
- **OVLO recovery is hysteretic, and after a genuine over-voltage a power cycle
  may be needed.** `V_OVLO(F)` is 1.03/1.10/1.17 V, ≈92 % of the rising
  threshold, so a part that trips at 5.80 V re-enables near 5.32 V. If the
  supply settles back to 5.0 V the part re-enables; if it settles just under its
  own trip point it may stay off. Removing input power always clears it. This
  goes in ORDER_README.
- **BOM: +1 line, 0 new refs.** `R_OVT` leaves the shared 100 kΩ C25741 group
  for its own ±0.5 % line; `R_OVB` changes value and code within its own line.
- **RE-VERIFY on any reversal**: `power_topology.py` (E-TOPO), the three
  `part_value` invariants below, `bom_source_check` (M-BOM), `jlc_stock_check`
  (A-STOCK — C407739 is the thin one at 227), and ORDER_README §0/§5.2.

## What is NOT fixed, and is named rather than hidden

**`D_TVS` SMBJ5.0A is operated ABOVE its rated stand-off voltage even under the
NEW spec.** Littelfuse defines `V_R` as "maximum voltage that can be applied to
the TVS WITHOUT OPERATION", and `V_R` = 5.0 V against a 5.25 V ceiling. Using
the same two-point fit, worst-case leakage is ≈**1.26 mA at 5.25 V** (25 °C),
versus ≈1.97 mA at the old 5.5 V ceiling — **tightening the spec IMPROVES this
by ~36 % but does not resolve it**, and the vendor publishes no
leakage-vs-temperature curve, so a part above its stand-off at 25 °C has no
published behaviour at 70 °C. The fix is `SMBJ6.0A` (`V_R` 6.0, `V_BR` min
6.67 V, leakage ≈47 µA at 5.25 V — 27× better), which also widens the OVLO
window; its cost is `V_C` 9.2 → 10.3 V, which must be re-checked against the
AMS1117 and eFuse abs-max ratings before it is taken. **Declared gap, next
electrical revision.** This is the same finding the fleet already paid for on
pluto-rx2-8way (`02_parts/SMBJ6.0A/part.yaml`, D-SPEC finding); it is recorded
here because the arithmetic is identical and the answer is the same.

## Invariants emitted (E-INV / E-ADR)

- `part_value` `R_OVT` = `100k` and `R_OVB` = `26.1k` — the OV setpoint is
  computed from exactly these two numbers, and every topology assert on this
  divider stays green at any value.
- `series_chain` `5V_RPP → R_OVT → EF_OVLO → R_OVB → GND` — the divider is
  ACROSS the input rail with the tap at the EN/OVLO pin, so a "simplification"
  that re-homes either leg is caught.
