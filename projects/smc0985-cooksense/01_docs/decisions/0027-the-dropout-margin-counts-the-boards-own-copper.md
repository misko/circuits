# ADR-0027 — the dropout margin counts the BOARD'S OWN COPPER, and the
# coincident heater peak is a declared constraint rather than a rounded number

status: **accepted**
date: 2026-07-30
tags: power, topology, dropout, sourcing-of-numbers
relates: ADR-0021 (the supply is a specification — this is the number that
ruling was made to produce), ADR-0026 (the load half of the same rail),
ADR-0004 (the switched sensor rails), ADR-0018 (the J_MODE front end)
amends: `03_src/cooksense/rules/power_tree.yaml`,
`03_src/cooksense/rules/electrical_invariants.yaml`

## Context

This is the THIRD load-bearing sum on ONE rail found to be missing a term, and
the third in a row that survived DRC 0/0/0, `policy_audit` FAIL=0 and a green
`E-TOPO`. None of the three is copper. The board's md5 has not moved
(`9f4fd5fae810f40a52b1035df727243c`) across any of them.

1. **The LOAD omitted four switched rails** — closed by ADR-0026.
2. **The CEILING was a 25 °C figure on a 50–75 °C board** — closed by ADR-0026.
3. **The SERIES RESISTANCE omitted the board.** `rails[3V3].vin_min: 4.754` was
   `4.850 − 0.50 A × (F1 70.0 + Q_REV 73.5 + eFuse 47.0 = 190.5 mΩ)`, under the
   sentence *"Every resistance is a datasheet MAXIMUM."* The board itself was
   not in the list, and **MEASURED, no 5 V net on this board has a zone
   anywhere** — the only four filled zones are `GND` on F.Cu (2701.43 mm²),
   B.Cu (7385.83), In1.Cu (8465.52) and `3V3` on In2.Cu (8420.03) — so the
   TRACKS ARE THE ENTIRE CONDUCTOR of the 5 V chain.

The v1.7 re-gate-2 topology lens found (3) and measured 109.0 mΩ of omitted
copper by a Dijkstra minimum-resistance walk. **That number is re-measured
here, by a different method, and it is 137.79 mΩ — the finding is WORSE than
the lens stated, not better.** Both differences are named in §Options.

## The two errors point in OPPOSITE directions and were NOT allowed to cancel

This is the whole reason this ADR exists as a separate decision rather than a
one-line edit. The rail carried two errors at once:

| # | error | direction | worth |
|---|---|---|---|
| (i) | the board's copper was in no sum | the real drop is **LARGER** | **−52 mV** |
| (ii) | `0.50 A` was a rounded guess, not a budget | the real current is **SMALLER** | **+26 mV** |

`vin_min: 4.754` was *approximately right for the wrong reasons* — it was
silently paying for the omitted copper with an inflated current, and nothing
anywhere checked that the two happened to nearly cancel. **They do not cancel
exactly, and at the file's own literal reading — 0.50 A of load at the LDO —
the true answer is −13.1 mV, a FAIL.** Prior to this pass, `power_tree.yaml`
recorded that `vin_min` was *"deliberately NOT re-derived"* because *"a
conservative `vin_min` is the conservative direction"*. That statement is true
of the current half in isolation and false of the pair.

## Method — MEASURED, and how

Every figure below is produced by an **exact DC nodal solve of the whole 5 V
chain**, not by a path walk:

- `04_kicad/cooksense.kicad_pcb` (md5 `9f4fd5fae810f40a52b1035df727243c`,
  byte-identical to the staged `source/cooksense.kicad_pcb`) opened read-only
  into a scratch copy with `/usr/bin/python3` + `pcbnew`;
- every track segment on `5V_IN` / `5V_FUSED` / `5V_RPP` / `5V_PROTECTED`
  becomes a graph edge with `R = ρL/(wt)`; every via a plated barrel; every pad
  a node found by `PAD.GetEffectiveShape(layer).Collide()`; the three cited
  component resistances are bridges, with **both eFuse IN pads tied** because
  the package bonds them;
- the real load currents are injected **at the pads they actually sit on**, and
  `G·v = i` is solved. Shared trunk copper is therefore charged the SUM of the
  currents crossing it and each branch only its own — an apportionment no
  single lumped resistance can express.
- Corner: copper `1.72e-8 Ω·m` at 20 °C × 1.216 at **75 °C** (α = 3.93e-3/K —
  the same ambient the thermal half is graded at); outer copper 35 µm; via
  barrels 0.15 mm drill × 1.6 mm at **18 µm** plated-hole copper, the spec
  floor rather than the 25 µm typical.

**MEASURED, at that corner:**

| segment | two-terminal R |
|---|---|
| `J_PWR.1 → F1.1` (`5V_IN`, 0.500 mm F.Cu, 22.120 mm, 0 vias) | **26.29 mΩ** |
| `F1.2 → Q_REV.3` (`5V_FUSED`) | **7.17 mΩ** |
| `Q_REV.2 → U_EFUSE.3/4` (`5V_RPP`) | **24.07 mΩ** |
| `U_EFUSE.5 → U_LDO.3` (`5V_PROTECTED`, the LDO branch) | **80.25 mΩ** |
| **copper sum** | **137.79 mΩ** |
| + the three cited components | 190.5 mΩ |
| **`J_PWR.1 → U_LDO.3` total** | **328.29 mΩ** |

Of that total, **248.04 mΩ is TRUNK shared by every `5V_PROTECTED` load** and
80.25 mΩ is the LDO's own branch. The transfer resistances that matter —
`dV(U_LDO.3)/dI` — are **328.292 mΩ** for the LDO's own current and
**274.885 mΩ** for every other load's, and because the network is linear those
two numbers reproduce the full solve exactly by superposition. That is what the
bound block below regenerates.

**The load side, itemised at the pad each load sits on:**

| pad | load | current |
|---|---|---|
| `U_LDO.3` | `iout_max_A` 0.200 + Iq max 11 mA | 0.211 A |
| `Q_COIL.2` | `5V_KEY_RELAY` | 0.150 A |
| `R_STOPRAIL.1` | `5V_STOP` | 0.020 A |
| `J_LOADCELL.1` | cook-loadcell 5 V — **UN-DERIVED, bounded** | 0.020 A |
| `D_TVS.1` | SMBJ5.0A leakage at 5.25 V | 0.0013 A |
| `R_HSG.2`, `R_OVT.1` | gate pull-up + OVLO divider | 0.0001 A |
| | **total** | **0.4024 A** |

**`J_LOADCELL.1` is a real 5 V load that no revision of this file had ever
carried.** MEASURED from the netlist: `J_LOADCELL.1` is on `5V_PROTECTED` while
only `J_LOADCELL.2` (`3V3`) was ever budgeted. Board D is not in this repo, so
its draw is **not derived and is not claimed** — 0.020 A is a bound. It is also
not load-bearing, and that is stated as a MEASURED insensitivity rather than a
hope: the declared case still passes with this term at anything up to
**125.9 mA**.

## Options

**A. Re-derive `vin_min` downward at the new load and leave the copper out.**
REJECTED — this is the trap the previous pass explicitly warned about, and it
would have produced `4.850 − 0.4024 × 0.1905 = 4.773`, a **better** margin than
the incumbent on a **more** wrong basis.

**B. Adopt the lens's 109.0 mΩ.** REJECTED, and the disagreement is recorded
rather than averaged. The lens took the two eFuse IN-pad routes as DISJOINT
parallel branches (`18.64 ‖ 17.47 → 9.00 mΩ`); they share their trunk, so the
parallel formula over-credits by ≈9 mΩ. It also allowed 0.5 mΩ per via, and a
0.15 mm drill barrel at 18 µm plating is **3.5 mΩ**, 7× that. Re-run inside this
solver *with the lens's own 0.5 mΩ/via*, the copper is 117.8 mΩ, which splits
the gap between the two causes. **What makes the lens credible anyway, and is
recorded as the reason its finding was accepted rather than re-litigated: its
`5V_IN` figure — the one segment with NO vias — is 25.87 mΩ and reproduces here
at 25.87 mΩ at its own 70 °C corner.**

**C. Pour a 5 V zone to cut the copper term.** REJECTED for this release: it is
copper, the board is at DRC 0/0/0 with an unchanged md5, and the honest budget
PASSES without it. Recorded as next-revision work beside ADR-0026's tab-pour
item, which is the same shape of answer to a different half of the same rail.

**D. Re-derive `vin_min` with BOTH terms corrected, carrying each explicitly.**
**CHOSEN.**

**E. On the coincident dual-heater peak: round it away, invent the 0.2 A
dropout figure, or declare a constraint?** **CHOSEN: declare the constraint.**
See Decision 3.

## Decision

1. **`rails[3V3].vin_min` = 4.728 V** (`V(U_LDO.3)` MEASURED at 4.7281,
   rounded DOWN), replacing 4.754. `E-TOPO`, `RAW_EXIT=0`:
   `headroom 1329 mV (Vin_min 4.728 − Vout_max 3.399) vs dropout 1300 mV →
   PASS`. **+29 mV, not the +55 mV that was declared.**

   The full ladder, so the margin is a curve and not a single number:

   | case | I_board | V(`U_LDO.3`) | headroom | vs 1300 |
   |---|---|---|---|---|
   | declared: `iout_max_A` 0.200 + Iq | 0.4024 A | 4.7281 V | 1329.1 mV | **+29.1** |
   | true worst continuous, 0.1169 A of 3V3 | 0.3191 A | 4.7555 V | 1356.5 mV | +56.5 |
   | realistic operating (typicals) | 0.1304 A | 4.8102 V | 1411.2 mV | +111.2 |
   | the OLD 0.50 A basis, apportioned | 0.4824 A | 4.7008 V | 1301.8 mV | +1.8 |
   | the OLD 0.50 A basis, LUMPED at the LDO | 0.5000 A | 4.6859 V | 1286.9 mV | **−13.1 FAIL** |
   | **break-even whole-board current** | **0.4910 A** | 4.6990 V | 1300.0 mV | 0 |

2. **The file's stated robustness envelope is DELETED because it is FALSE, not
   re-argued.** `power_tree.yaml` claimed *"It still passes at 0.60 A (+37 mV)
   … so the verdict does not hinge on the one interpolated term (Q_REV)."*
   MEASURED, 0.60 A of whole-board current gives **−35.8 mV**. The verdict now
   **does** hinge on Q_REV's interpolated 73.5 mΩ, because +29 mV is smaller
   than that single term's own uncertainty — which is exactly the inversion the
   re-gate-2 lens named, and it is recorded here rather than softened.

3. **THE TWO SHT45 HEATERS ARE NEVER FIRED COINCIDENTALLY AT THE 200 mW
   LEVEL.** Sensirion's ≤10 % duty limit (SHT4x D1 §4.9 / Table 9) is a
   PER-SENSOR limit; whether the two pulses OVERLAP is this system's choice,
   and it is the only choice on this rail the copper-counted budget cannot
   absorb. MEASURED:

   | case | I_board | headroom | vs 1300 |
   |---|---|---|---|
   | continuous, declared | 0.4024 A | 1329.1 mV | +29.1 |
   | PEAK, both heaters @200 mW coincident (≤1.1 s) | 0.4990 A | 1297.4 mV | **−2.6 FAIL** |
   | PEAK, heaters STAGGERED, one at a time | 0.4090 A | 1327.0 mV | **+27.0 PASS** |

   −2.6 mV is 0.2 % of a dropout figure ds1117 specifies at `IOUT = 0.8 A` on a
   rail drawing 0.30 A, and whose General Description says dropout *decreases
   at lower load currents* — so this is very probably not a physical failure.
   **It is declared as a constraint anyway, because the alternative is to
   invent the low-current dropout figure this file has refused to invent since
   v1.5.** A constraint costs a firmware line; an invented number costs the
   next reader. The constraint lands in `power_tree.yaml` under `iout_max_A`
   and in `ORDER_README.md` §7 (first power / bring-up).

4. **ADR-0026's +3.8 °C heater excursion is CORRECTED, in the honest
   direction.** That figure was `θ_JC × ΔP` with `θ_JC = 15 °C/W`, i.e. the
   ADIABATIC-BOARD limit, valid only while the tab's thermal mass has not
   responded. A 1.1 s pulse in a SOT-223 is not clearly inside that regime, and
   the steady-state answer is `θ_JA × ΔP = 90 × 0.198 = +17.8 °C`, which would
   put `Tj` at 134.9 °C. **ds1117 publishes no thermal time constant, so the
   excursion is NOT BOUNDED BY ANY CITED NUMBER and must not be claimed at
   +3.0 °C.** Decision 3 removes the question instead of answering it:
   staggered, the peak is +6.6 mA over the declaration (+0.0135 W), i.e.
   +0.2 °C adiabatic / +1.2 °C steady state, and `Tj` stays at 117.1–118.3 °C.

5. **The 11.8 mA load delta ADR-0026 left OWED is CLOSED, and closed UPWARD.**
   Every resistor on the board (87) was enumerated from the netlist with BOTH
   endpoint nets and each pull-down's far node traced to its driver. Three
   terms were genuinely absent, all of the same shape — **current that leaves a
   3V3-POWERED OUTPUT rather than the 3V3 NET, which a "which pads are on net
   `3V3`" sweep cannot see**:

   | term | path | current |
   |---|---|---|
   | A″ pull-downs on 3V3-powered outputs | 16 × 100 kΩ + `R_GPB3PD` 10 kΩ | **0.884 mA** |
   | C′ the J_MODE **return** leg | `U_AND3.4 → J_MODE.3 → DPDT → J_MODE.4 → R_COILENPD 680 Ω` | **4.999 mA** |
   | C″ the contactor opto LED | `U_CAND2.4 → R_OPTOLED 330 Ω → U_OPTO.1` | **7.270 mA** |

   The lens was right about three of its four; this file was right that
   `R_TEMPOK` was already inside block B. **The sweep also found one NEITHER
   count had** — `R_GPB3PD`, 10 kΩ on the MCP23017's spare GPB3 output,
   0.340 mA — so the closed sum **116.859 mA** sits ABOVE the lens's 115.5,
   not between the two counts. Explicitly EXCLUDED with a reason:
   `R_HOSTAUTHPD` / `R_MCUENPD` / `R_KRSTPD` / `R_STOPPD` (100 kΩ) and
   `R_WDPETPD` (1 kΩ, 3.3 mA) hang off `J_PI.15/.16/.33/.37/.11` and are
   sourced from **the Pi's** 3V3, not ours.

6. **`iout_max_A` STAYS 0.20 A**, and that is a result rather than an
   omission. `116.859 × 1.5 = 175.3 mA`, still under 0.200 and still inside the
   0.2429 A ceiling ADR-0026's `LDO_IOUT_MAX` bound publishes. So ADR-0026's
   dissipation half is UNTOUCHED — PD 410 mW / 82 %, `Tj` 117.08 °C, 7.92 °C of
   margin, all re-derived here — which is the point: **the load correction went
   UP by 13.2 mA and did not move the declaration, so the dropout
   re-derivation cannot have been paid for out of the thermal budget.**

7. **The documentation-only `linear_rails:` envelopes are corrected too.**
   `5V_PROTECTED.vout_min` 4.754 → **4.750** (MEASURED at `U_EFUSE.5`), and
   `5V_KEY_RELAY` / `5V_STOP` `vin_min` 4.754 → **4.702** (MEASURED at
   `Q_COIL.2` / `R_STOPRAIL.1`). **`5V_PROTECTED` is not one node**: at the
   declared load its members span 48 mV of track.

8. **An invariant is emitted, and it is the endpoint of the measured path.**
   `U_LDO.3` on `5V_PROTECTED` was asserted by nothing. ADR-0001 already pins
   `5V_IN → F1 → 5V_FUSED → Q_REV → 5V_RPP` and `U_EFUSE.5` on
   `5V_PROTECTED`; the LDO's own input pin was the one link in the chain this
   ADR measures that no gate held. Re-homing it (to `5V_RPP`, ahead of the
   eFuse, say) would invalidate every number above while leaving `E-TOPO`
   green.

## Consequences

**The rail PASSES HONESTLY, at every current, with one declared constraint.**
+29.1 mV at the declared worst case and +56.5 mV at the true one, against a
fully-stacked corner: lowest sanctioned supply × highest-trimmed LDO output ×
a 0.8 A dropout figure applied at a 0.2 A rail × every series resistance at its
maximum × every load at its datasheet maximum × a 1.5 design margin on the load
× copper at 75 °C at the minimum plated-barrel thickness.

**+29 mV IS THIN, AND IT MAKES AN ALREADY-OWED MEASUREMENT LOAD-BEARING.**
At +55 mV the bench dropout measurement was worth taking; at +29 mV it is the
only thing between a computed pass and a known margin. It is the same G4 bench
session that owes `θ_JA` on this mounting and the `V_IN − V_OUT` this file
already owed — **one session retires all three, and it is now the highest-value
hour on this board.**

**What is still UN-DERIVED on this rail after this pass, named so silence is
not read as coverage:**

- **`J_LOADCELL.1`** — Board D's 5 V draw. Bounded at 20 mA, insensitive to
  125.9 mA. The only genuinely un-derived term in the trunk sum.
- **the AMS1117 dropout at 0.2 A** — ds1117 publishes it only at 0.8 A and
  has no dropout-vs-load curve. OWED (unchanged).
- **`θ_JA` on this mounting** — 90 °C/W is the package figure, deliberately not
  the mounting figure. OWED (unchanged; the layout lens independently derived
  ~87 °C/W, which makes 90 conservative but is not a measurement of this
  board).
- **the SOT-223 thermal time constant** — see Decision 4. There is no cited
  number, and Decision 3 is what makes its absence affordable.
- **the LTV-817 `V_F`** — `02_parts/LTV-817S-TA1/part.yaml` records `ctr`,
  `vceo` and `viso` and no forward voltage at all. Term C″ is BOUNDED at a
  1.0 V floor (below any plausible LTV-817 drop, hence the conservative
  direction for a load budget), not cited.
- **the nine on-board logic ICC maxima and the four sensor-rail figures** —
  INHERITED from the citations in `power_tree.yaml`. The DEVICE COUNTS behind
  them are re-MEASURED here from the netlist and all eleven match.

**What breaks if reversed.** Restoring `vin_min: 4.754` re-grades the rail on a
series resistance that omits 42 % of itself. Removing the heater constraint
puts the coincident peak at −2.6 mV of dropout headroom and an unbounded
junction excursion. Removing terms A″/C′/C″ returns the load sum to 88.7 % of
its cited value and re-opens the delta ADR-0026 left OWED.

**Owed skill patch — the class, not this instance.** `E-TOPO` derives its
dropout verdict from a `vin_min` the board author types, and there is nothing
anywhere that asks whether that number counted the copper between the connector
and the pin. A `vin_min` declared for a rail whose input net has NO ZONE is the
checkable case: the gate could refuse it, or require a `series_mohm:` term with
a regenerable provenance. Filed with the others in
`06_build/staging/cooksense-v1.7/verification/owed_skill_patches.md` (P14);
**not implemented — `skills/` is outside this board's partition.**

**THE BOUND THIS ADR PUBLISHES, DECLARED SO IT IS REGENERATED RATHER THAN
TYPED** (canon M-BOUND). The whole decision rests on one inequality: how much
whole-board current this chain can carry before the LDO's input falls to
`Vout_max + dropout_max`. Because the network is linear, the two MEASURED
transfer resistances reproduce the full nodal solve exactly by superposition,
so the bound is a closed form over measured constants rather than a re-run of
`pcbnew`.

<!-- bound: LDO_DROPOUT_IBOARD_MAX -->
```yaml
id: LDO_DROPOUT_IBOARD_MAX
claim: >-
  Largest WHOLE-BOARD current the J_PWR -> F1 -> Q_REV -> U_EFUSE -> U_LDO.3
  chain may carry before V(U_LDO.3) falls to Vout_max 3.399 V plus the cited
  ds1117 maximum dropout of 1.300 V, with the ADR-0021 supply floor of 4.850 V
  at the connector, the board's OWN routed copper counted alongside the three
  cited protection-device resistances, and each load charged the trunk it
  actually crosses. Constants are the two MEASURED transfer resistances
  dV(U_LDO.3)/dI at 75 C / 35 um outer / 18 um plated barrels -- 328.292 mOhm
  for the LDO's own current, 274.885 mOhm for every other 5V_PROTECTED load --
  and I_O = 0.1914 A, the declared sum of those other loads (coil rail 0.150 +
  5V_STOP 0.020 + load-cell bound 0.020 + TVS leakage 0.0013 + 0.0001).
relation: "<="
value: 0.4910
unit: A
corner: worst_case
command: /usr/bin/python3 -c "R_L=0.328292; R_O=0.274885; I_O=0.1914; print((4.850-3.399-1.300-I_O*R_O)/R_L+I_O)"
governs:
  evaluate: /usr/bin/python3 -c "I={value}; R_L=0.328292; R_O=0.274885; I_O=0.1914; print((4.850-(I-I_O)*R_L-I_O*R_O-3.399)*1000)"
  budget: ">= 1300"
  unit: mV
chosen: 0.4024
chosen_why: >-
  The DECLARED worst-case whole-board current -- iout_max_A 0.200 + the LDO's
  own Iq max 11 mA, plus the four other 5V_PROTECTED loads above. It clears the
  bound by 88.6 mA, and the true simultaneous worst case (0.3191 A) clears it
  by 172 mA.
tolerance: 0.0001
tolerance_why: >-
  `value` is rounded DOWN to four decimals from an exact 0.49109083 A, so it can
  only ever understate the ceiling. 0.0001 A is one unit in the last declared
  place and 886x smaller than the 0.0886 A gap to `chosen` (0.4024 A), the value
  the bound has to rule on.
grade: CITED
requires:
  - projects/smc0985-cooksense/03_src/cooksense/rules/power_tree.yaml
  - projects/smc0985-cooksense/04_kicad/cooksense.kicad_pcb
```

Re-derived at the corner it declares: at the bound itself the headroom is
exactly 1300.0 mV, and at the chosen declaration (0.4024 A) it is 1329.1 mV.
**The bound sits on its own budget edge and nowhere else** — and it is the
number the deleted "*still passes at 0.60 A*" claim got wrong by 109 mA.
