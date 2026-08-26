# ADR-0028 — the 3V3 rail has TWO margins, they bind in DIFFERENT places, and
# the ambient envelope is the user's decision rather than this document's

status: **accepted for the defect fixes and the analysis; the ENVELOPE DECISION
IS DELIBERATELY NOT TAKEN HERE** (see Decision 6)
date: 2026-07-30
tags: power, thermal, dropout, sourcing-of-numbers, gates, envelope
relates: ADR-0021 (the supply is a specification — and this ADR is about WHICH
NODE that specification names), ADR-0026 (the thermal half), ADR-0027 (the
dropout half and the copper), ADR-0014 (OPEN item 2 — the board's own thermal
zone is undeclared)
amends: `03_src/cooksense/rules/power_tree.yaml` (the dissipation worked
example), `02_parts/43650-0224/part.yaml` (`limits:`),
`02_parts/PESD5V0S1BA/part.yaml` (`limits:` — the block that did not exist)

## Context

Five successive passes have re-derived ONE rail's margin and each has landed on
a number that was optimistic for a DIFFERENT reason. The board's copper has not
moved once (`04_kicad/cooksense.kicad_pcb` md5
`9f4fd5fae810f40a52b1035df727243c`, DRC 0/0/0 at full severity, verified by
three independent parties). Nothing here is a copper finding.

**The rail model itself is now trustworthy and is NOT re-litigated.** The v1.7
re-gate-3 topology lens rebuilt the whole 5 V network from its own s-expression
reader and its own nodal solver — no `pcbnew`, no repo code — and reproduced
ADR-0027 to four decimals (copper 137.657 vs 137.79 mΩ, headroom +29.2 vs
+29.1 mV, break-even 0.4913 vs 0.4910 A). The layout lens reproduced the same
four segment figures to ≤0.19 mΩ with a third independent construction. This
ADR BUILDS ON that model; it adds the two terms it was still missing and then
asks the question none of the five passes asked:

> **at what ambient is each of the two margins actually ≥ 0, and which of them
> binds first?**

The answer is not what the file's structure suggests. **The two margins are
almost independent axes**, and the one everyone has been arguing about is the
one ambient barely moves.

## The two terms that were still missing, both optimistic, both now carried

**1. CONNECTOR CONTACT RESISTANCE.** ADR-0027's series sum starts at the PCB pad
`J_PWR.1`. **ADR-0021 Decision 1 specifies the supply "measured AT THE CONNECTOR
under full load."** Those are not the same node; what separates them is the
Micro-Fit 3.0 mating interface. CITED (Molex Micro-Fit 3.0 family literature
`987650-5984.pdf`, Electrical section, and the 43030/43031 crimp-terminal sales
drawings): **Contact Resistance 10 milliohms max.** Two contacts are in the
loop (supply leg and return leg), so **20 mΩ minimum, 8.1 mV at the declared
0.4024 A — 28 % of the whole +29.1 mV margin.** INHERITED (Molex product spec
PS-43650-001, via search summary; molex.com would not serve the PDF, NOT
re-verified): a further **≤20 mΩ change from initial** after durability /
thermal-aging / vibration / shock, i.e. up to 60 mΩ and **24.1 mV, 83 % of the
margin.**

It was absent from every sum, absent from `02_parts/43650-0224/part.yaml`
`limits:`, and — the part that matters — **absent from ADR-0027's own
UN-DERIVED list, the artifact's own control against exactly this failure.**

**AND IT HAD ALREADY BEEN FOUND ONCE.** `ORDER_README.md` §13 P1-B, the prior
round's own ladder, reads `+15.4 mV with the board copper at 20 C` / `+5.4 mV
**with the connector** at 20 C` / `−2.5 mV with the connector at 70 C`. **The
connector row WENT NEGATIVE. ADR-0027 adopted the copper half of that finding,
re-measured it upward to 137.79 mΩ, and dropped the connector half without
recording that it had.** That is the aggravating fact and it is written down
here so it is not repeated: a ladder that already contained a failing row was
replaced by a ladder that did not contain the row at all.

**2. THE TEMPERATURE BASIS OF THE COMPONENT RESISTANCES.** ADR-0027's 328.29 mΩ
derates **only the copper** to 75 °C, under a sensitivity paragraph whose two
axes are both copper and whose text reads *"so no un-cited input is
load-bearing"*. The 190.5 mΩ of components — **58.0 % of the total** — carries
no temperature statement at all:

| term | value used | the temperature it is actually specified at | grade |
|---|---|---|---|
| `F1` MF-MSMF200/8X | 70.0 mΩ (R1Max) | **23 °C.** *"Resistance — in still air @ 23 °C"*. **Bourns publishes NO resistance-vs-temperature data anywhere in the datasheet** — only an `Ihold` derating table. Operating range −40…+85 °C. | CITED value, **UN-CITED tempco** |
| `Q_REV` AO3401A | 73.5 mΩ | a **70 °C junction** (60 mΩ at 25 °C × 1.225). AOS's own 25→125 °C rows (50→75 mΩ) give **+0.5 %/K**, which IS citable and extends the term correctly to any junction. | CITED, extensible |
| `U_EFUSE` TPS259573 | 47.0 mΩ | **max over −40…85 °C.** The same EC table publishes **53 mΩ over −40…125 °C**. At Ta 75 °C the eFuse dissipates 7.6 mW, so its junction is ~75.4 °C and 47 mΩ is the correct cited row up to Ta ≈ 84 °C. | CITED, both rows |

**`F1` IS A PTC. RISING RESISTANCE WITH TEMPERATURE IS THE MECHANISM THE PART IS
SOLD FOR**, and it was silently carried at `R(75 °C) = R(23 °C)`. The layout
lens solved for the break-even and got **F1 × 1.82** with the other terms at
their hot corner, × 2.03 with everything else exactly as ADR-0027 declares it.

Citable corrections alone (copper and `Q_REV` at an 86 °C junction, eFuse on its
−40…125 °C row) take **+29.1 → +23.1 mV**, and that is before the connector.

## The MEASURED answer — both margins, as functions of ambient

Method, MEASURED (by me, `/usr/bin/python3`, my own model in the session
scratch; no repo code, no `pcbnew`): the two MEASURED transfer resistances of
ADR-0027 are decomposed into a copper part and a component part, each carried at
its own basis. Copper `R(T) = R₂₀(1 + 3.93e-3 (T−20))` with `R₂₀` back-derived
from the 75 °C solve; `Q_REV` at `60 mΩ (1 + 0.005 (T−25))`; `U_EFUSE` stepping
47→53 mΩ at an 85 °C junction; `F1` as an explicit multiplier `m` over its
23 °C R1Max; contacts as `n × R_c × I_total`. Component junctions carry their own
self-heating over the local board copper (`Q_REV` +3.0, `F1` +1.0, eFuse +0.5 °C
— all DERIVED and all small). Board copper sits at `Ta + ΔT_board`, with
`ΔT_board` the layout lens's DERIVED board-rise term. **Control: at ADR-0027's
own corner the model returns `V(U_LDO.3) = 4.7281 V`, headroom `1329.1 mV`,
reproducing the published figures exactly.**

### DROPOUT margin over the 1300 mV figure, worst case, ΔT_board = +2.79 °C

| Ta | no connector | **2 × 10 mΩ (CITED max)** | 2 × 30 mΩ (aged, INHERITED) |
|---|---|---|---|
| 23 °C | +41.0 mV | **+33.0 mV** | +16.9 mV |
| 50 °C | +31.4 | **+23.3** | +7.2 |
| 55 °C | +28.7 | **+20.7** | +4.6 |
| 65 °C | +27.6 | **+19.5** | +3.4 |
| 75 °C | +26.2 | **+18.1** | +2.0 |
| 85 °C | +22.0 | **+14.0** | **−2.1 FAIL** |

**THE HEADLINE IS THE SLOPE, NOT ANY ROW: −0.31 mV/K.** Copper is 42 % of the
sum at 0.393 %/K, so 62 K of ambient moves the dropout margin by 19 mV — less
than the connector term alone. **The dropout margin is NOT primarily an ambient
problem.** Narrowing the declared ambient from 75 °C to 55 °C buys **+2.6 mV**.
Anyone who reaches for the ambient knob to fix the dropout will find it
connected to almost nothing.

**Typical case** (nominal 5.000 V supply, nominal 3.300 V output, the ds1117
**typical** 1.100 V dropout, the true worst CONTINUOUS load 0.3191 A rather than
the ×1.5-margined declaration): **+497 mV at 75 °C with the cited connector.**
The worst case is +18 mV and the typical is +497 mV, and the whole distance
between them is the corner stack ADR-0027 lists. That is worth stating plainly
because it is the reason this rail keeps passing on the bench arithmetic while
failing to establish itself on paper.

### THERMAL margin, `Tj = Ta + ΔT_board + PD_LDO × θ_JA`, `PD_LDO` = 0.4676 W

The layout lens's P1-1: `θ_JA` is a junction-to-**ambient-air** figure measured
with only the device under test dissipating, and ds1117's own Thermal
Considerations says *"additional heat sources mounted near the device must be
considered."* The board's other **0.958 W** (12 reed relay coils 0.705 W
dominate) raises the copper the tab sinks into.

| Ta | θ_JA 90 CITED, **no board term** (as published) | + board h=10 (+2.79) | + board h=6 (+4.65) |
|---|---|---|---|
| 55 °C | 27.9 °C | 25.1 | 23.3 |
| 65 °C | 17.9 | 15.1 | 13.3 |
| 70 °C | 12.9 | 10.1 | 8.3 |
| **75 °C** | **7.92 (the declaration)** | **5.1** | **3.3** |
| 80 °C | 2.9 | 0.1 | −1.7 |

**The board-rise term costs 1.55…4.65 °C, i.e. 20–59 % of the declared 7.92 °C
margin.** With the lens's own derived `θ_JA` (81.6…92.3 °C/W across h = 18…6)
instead of the cited 90, the 75 °C margin is 2.2…10.3 °C.

### What binds — and it is NOT the dropout

| constraint | Ta ceiling, ΔT_board = +2.79 | ΔT_board = +4.65 |
|---|---|---|
| **`U_LDO` Tj ≤ 125 °C at θ_JA 90 (CITED)** | **80.1 °C** | **78.3 °C** |
| `F1` operating range −40…+85 °C (Bourns) | 82.2 °C | 80.3 °C |
| `J_PWR` 43650 −40…+105 °C (Molex) | 102.2 °C | 100.3 °C |
| `U_EFUSE` Tj −40…125 °C | 121.7 °C | 119.8 °C |
| dropout ≥ 0, F1 per the inference below, contacts 2 × 10 mΩ | 137.3 °C | 135.5 °C |
| dropout ≥ 0, same, contacts at the **aged** 2 × 30 mΩ | 81.7 °C | 79.8 °C |

**THE JUNCTION TEMPERATURE BINDS FIRST, at Ta ≈ 78–80 °C.** The declared 75 °C
is inside it by 3.3–5.1 °C. The dropout only becomes the binding constraint if
the contacts age to their allowance, and then the two bind within 2 °C of each
other.

## The three grades, stated separately, because that is the whole point

**CITABLE.** With every number traceable to a datasheet and the connector at its
CITED 10 mΩ/contact maximum, and **holding `F1` at its 23 °C R1Max**:

* **DROPOUT ≥ 0 at every ambient in the part set's own operating range.** Margin
  +33.0 mV at 23 °C falling to +14.0 mV at 85 °C (worst case); +497 mV typical.
* **THERMAL Tj ≤ 125 °C up to Ta = 82.9 °C** on the published form
  (`Tj = Ta + PD·θ_JA`, no board term — the form the release ships), and
  **Ta = 78.3…80.1 °C** once the board-rise term is included. The board term is
  DERIVED, not CITED, so **82.9 °C is the citable ceiling and it is
  known-optimistic by 2.8–4.7 °C.**

**But the honest citable statement about `F1` is stronger and worse: because
Bourns publishes no R-vs-T data at all, NO ambient above 23 °C is provable from
citations alone.** Holding `F1` flat is itself an assumption, and it is the one
the release has been making silently since v1.5.

**ASSUMPTION-BOUNDED.** *THIS IS AN ASSUMPTION AND IT IS STATED AS ONE.* Assume
the device's thermal resistance to ambient is temperature-independent. Then
Bourns' own `Ihold` derating table constrains `R(T)`, because
`Ihold(T)² · R(T) = (T_switch − T)/θ`. MEASURED (by me, from the committed
`BOURNS-MF-MSMF-SERIES.pdf`): MF-MSMF200/8X `Ihold` = 2.00 A at 23 °C and
1.29 A at 85 °C. Inverting:

| assumed polymer switching temperature | implied `R(85 °C)/R(23 °C)` |
|---|---|
| 120 °C | 0.87 |
| 125 °C | 0.94 |
| **130 °C** | **1.01** |
| 140 °C | 1.13 |
| 150 °C | 1.23 |

and in the other direction, **`m = 1.82` (the break-even) implies a switching
temperature of 278 °C** and `m = 2.00` implies 392 °C — both far above any
polymer PPTC transition and above the part's own 260 °C reflow peak. **So the
break-even multiplier is refuted by the datasheet's own derating table under the
stated assumption, and `m` is plausibly 1.0–1.15 up to 85 °C.** Grade: DERIVED,
from a CITED table, under a NAMED assumption. It is an inference on a
manufacturer's modelled specification, not a measurement, and it is written
here so that a reader can reject the assumption and still have the break-even.

At `m ≤ 1.5` (a deliberately generous bound) with the CITED connector maximum,
**dropout ≥ 0 up to Ta = 85.7 °C**, above every other constraint in the table.
At `m ≤ 1.5` **with the aged connector allowance and h = 6**, it collapses to
**Ta = 32.6 °C** — which is the honest measure of how much the aged-contact
allowance costs, and why the connector belongs in a `limits:` block rather than
in a review finding.

**UN-CITABLE — these need a bench, and there is no paper substitute:**

1. **`F1` R-vs-T for MF-MSMF200/8X.** Bourns publishes none. Everything above
   rests on an inversion of the `Ihold` table.
2. **The Micro-Fit contact resistance in THIS build** — with these crimps, this
   wire gauge, this mating cycle count. 10 mΩ is a specification maximum; the
   aged 30 mΩ is INHERITED from a document this tree could not fetch.
3. **The AMS1117 dropout at 0.2 A.** ds1117 publishes it only at 0.8 A, has no
   dropout-vs-load curve (six curves on p.6, none of them dropout), and says
   only that dropout *"decreases at lower load currents"*. **This is the one
   that dominates: the entire dropout argument is a 0.8 A number applied to a
   0.2 A rail.** OWED since v1.5.
4. **`θ_JA` on THIS mounting.** 90 °C/W is the package figure. The lens's
   independent thermal network gives 81.6…92.3 °C/W across h = 18…6, i.e. 90 is
   central-to-slightly-optimistic, not conservative. OWED.
5. **`ΔT_board`, the board's own rise** — 1.55…4.65 °C is a model output, not a
   measurement, and it is 20–59 % of the thermal margin.
6. The SOT-223 thermal time constant (ADR-0027 Decision 4, unchanged), and
   `J_LOADCELL.1`'s 5 V draw (ADR-0027, unchanged).

## Options — priced

**(a) NARROW THE DECLARED AMBIENT to what is provable.**
*Costs:* one line in `power_tree.yaml`, one in `BRIEF.md`, one in
`ORDER_README.md`, and an operating restriction the integrator must honour —
the enclosure ladder already exists (`≤50 preferred / 55 warn / 65 stop / 75
HARD`), so this is choosing a rung, not inventing one. Zero engineering.
*Buys:* the THERMAL margin, completely — 15.1 °C at 65 °C, 25.1 °C at 55 °C,
both with the board term included. **Buys almost nothing on the dropout:
+1.4 mV going 75 → 65, +2.6 mV going 75 → 55.**

**(b) REDUCE THE DROP.** MEASURED (by me, same model), each against the
CITED-connector case:

| change | buys | costs |
|---|---|---|
| 6 more vias in the EXISTING `U_LDO` tab pad (2 → 8 × 0.15 mm) | **−18.0 °C/W, +8.4 °C of junction margin** (layout lens P1-2) | a copper edit; no BOM, schematic, netlist or new feature. **The cheapest item on this page and it was never in ADR-0026's options table.** |
| `5V_IN` 0.500 → 1.500 mm | +7.05 mV | copper respin |
| LDO branch copper halved | +8.47 mV | copper respin |
| a real 5 V pour (all 5 V copper to ~30 %) | **+28.1 mV** | copper respin; ADR-0027 option C, already deferred |
| `F1` → a ~30 mΩ non-PTC 2 A fuse | **+16.1 mV**, and it DELETES the un-citable tempco entirely | a part change + re-coordination against the eFuse's ~1.7 A limit and `F1`'s role in the reverse-fault crowbar |
| `F1` deleted | +28.2 mV | **REJECTED — breaks the reverse-polarity invariant.** `D_REVCLAMP` is downstream of `F1` precisely so the crowbar current trips the polyfuse. |
| 4-circuit connector, contacts paralleled per leg | +4.0 mV cited / +12.1 mV aged | footprint change (respin) + connector change |

**(c) REPLACE THE LDO WITH A SWITCHING REGULATOR.** *Buys:* both problems, at
once. At 90 % efficiency `PD` falls 0.4676 → 0.073 W, `Tj` = 81.6 °C at Ta 75
(**43 °C of margin**, up from 3.3–5.1), and a buck needs ~0.3 V of headroom
against the 1.319 V available, so the dropout question — including the entire
un-citable 0.8 A-figure problem — **stops existing**. It also removes `F1`'s
tempco from the load-bearing path by making the path insensitive.
*Costs:* a respin of that cell — new part (D-ESC/D-LAYOUT/D-TIER all re-run),
inductor + feedback network + switching-node layout, new placement, new
routing, a fresh DRC gate, a fresh red-team pass on a MATERIAL design change,
and a new switching-noise question on a board carrying eight ADC channels and a
thermocouple front end. This is a v2 decision, not a v1.7 one.

**(d) SEAL AT 75 °C CONTINGENT ON A MANDATORY BENCH GATE in `ORDER_README.md`.**
*Costs:* nothing today; one hour at G4 bring-up; and the honesty burden of
shipping a board whose margin is computed rather than measured. This repo has
precedent — ADR-0027's heater-stagger constraint is already an
`ORDER_README` §7a-3 bench/firmware obligation, and the θ_JA + dropout
measurements are already OWED against the same session.
*Buys:* it converts items 1, 3, 4 and 5 of the UN-CITABLE list into measured
numbers in a single sitting, and item 3 is the one that dominates everything —
if dropout at 0.2 A is anywhere near the 300–500 mV a 1 A LDO typically shows at
a quarter load, the margin goes from +18 mV to ~+800 mV and **every option above
becomes unnecessary.**

## Decision

1. **The `power_tree.yaml` dissipation worked example is corrected and made
   REGENERATED rather than typed.** It computed at 0.150 A —
   `linear_rails[5V_KEY_RELAY].iout_max_A`, the SAME key
   `power_topology.py` does not read that produced this rail's round-2 P0 —
   and published `PD 307.4 mW / 62 % / Tj 107.9 °C / 17.1 °C margin` where the
   graded key gives `409.8 mW / 82.5 % / 117.08 °C / 7.92 °C`. **The published
   margin was 2.16× the true one, for four rounds, in the canonical file.**
   The corrected block carries one machine-readable `worked_example:` line and
   the bound `LDO_TJ_WORKED_EXAMPLE` below re-derives all four numbers FROM the
   graded keys, printing `999` on any drift. **Verified RED against both
   failure directions** before being accepted: reverting the line to the
   pre-fix `0.150 / 307.4 / 107.9 / 17.1` prints 999, and moving
   `rails[3V3].iout_max_A` to 0.15 while leaving the line alone also prints
   999; the restored file prints 117.0795.
2. **The `+3.8 °C` heater excursion is DELETED from `power_tree.yaml`, not
   re-argued.** ADR-0027 Decision 4 — shipped in the same directory — says of
   exactly that figure that it is *"NOT BOUNDED BY ANY CITED NUMBER and must
   not be claimed"*, and gives the steady-state alternative as +17.8 °C
   (`Tj` 134.9 °C). The deleted line was the optimistic end of an unbounded
   interval and it was being ADDED to an already-wrong `Tj`.
3. **The Micro-Fit contact resistance is recorded in
   `02_parts/43650-0224/part.yaml` `limits:`**, with the CITED 10 mΩ maximum and
   the INHERITED aged allowance graded separately, so the next sum cannot omit
   it by not knowing about it.
4. **`02_parts/PESD5V0S1BA/part.yaml` gets the `limits:` block it never had**,
   and **the placement is judged: DEFENSIBLE AS PRACTICE, UNDOCUMENTED AS A
   DECISION, AND UNDER-DERATED AS A PART.** See Decision 5.
5. **On `D_ESD_IN`'s position, plainly.** MEASURED (netlist):
   `5V_IN = {J_PWR.1, F1.1, D_ESD_IN.1}` — the clamp is directly across the
   input, ahead of the polyfuse and ahead of the eFuse, with nothing in series.
   * The PLACEMENT is **defensible**: an ESD clamp belongs at the connector so
     the strike does not traverse the board, and this board's `D_REVCLAMP`
     invariant (*"on 5V_IN the clamp current bypassed the fuse and was bounded
     only by the supply"*) is about a SUSTAINED reverse fault — a crowbar that
     must trip `F1` — not about a nanosecond ESD event. The two clamps have
     different jobs and correctly have different positions.
   * The DERATING is **not defensible as it stands**: `VRWM` is **5 V max** and
     `VBR` **min 5.5 V** against ADR-0021's **5.25 V** spec ceiling. The part is
     operated at 105 % of its stand-off, its leakage there is unspecified (a
     two-point fit between the cited 100 nA @ 5.0 V and 1 mA @ 5.5 V gives
     ≈10 µA — harmless, and nowhere written down), and its minimum breakdown is
     only 250 mV above the sanctioned supply maximum. Above ~5.5 V — the
     mis-selected-adapter case ADR-0021 exists to bound — **the first device to
     conduct on this board is a SOD-323 with no fuse, no eFuse and no series
     resistance in its path**, at a breakdown 0.9 V below `D_TVS`'s 6.40 V and
     below the eFuse's earliest guaranteed OVLO trip of 5.3682 V (and OVLO
     disconnects the LOAD, which is the wrong side of this part).
   * **DISPOSITION: a v-next part change, not a v1.7 blocker.** A 6.0 V or
     6.8 V stand-off SOD-323 (e.g. the PESD6V8 family) restores the derating at
     zero layout cost and zero copper. It is recorded here rather than fixed
     because it is a BOM change on a board whose fab set is otherwise
     invariant, and because the exposure it removes is a supply fault the OVLO
     already covers for everything downstream. **It is a real finding and it is
     not being closed by argument** — the `limits:` block now carries the
     numbers so the trade is evaluable, which is what was missing.
6. **NO AMBIENT ENVELOPE IS DECLARED HERE, AND THAT IS DELIBERATE.** The four
   options are priced above and one is recommended below; the choice belongs to
   whoever owns the enclosure, because it is an operating restriction on a
   product and not an arithmetic result. `power_tree.yaml` keeps `Ta = 75 °C`,
   the BRIEF's HARD limit, unchanged. **What this ADR refuses to do is
   re-declare a number to make a gate green** — every table above is published
   at the corner it was computed at, including the rows that fail.
7. **RECOMMENDATION: (a) narrowed to 65 °C, PLUS (d) the mandatory bench gate.
   Do (b)'s tab-via item at the next copper revision. Do not spend (c) yet.**
   Reasoning, in the order it actually matters:
   * **The two margins bind in different places, so one option cannot fix
     both.** Thermal is a 1 °C-per-°C ambient problem and (a) solves it
     outright: at 65 °C the margin is 15.1 °C **with** the board term, against
     3.3–5.1 °C at 75 °C. Dropout moves −0.31 mV/K and (a) buys it +1.4 mV,
     which is nothing.
   * **65 °C is the BRIEF's own "stop" rung**, so it invents no fact and asks
     the integrator for nothing the commission did not already contemplate. It
     also sits below the F1 operating ceiling with room, which 75 °C does not.
   * **(d) is the only option that attacks the dropout, because the dropout
     problem is an EVIDENCE problem, not a design problem.** Three of the five
     un-citables — the 0.2 A dropout, `θ_JA`, and the board rise — fall out of
     one hour with a bench supply, a load and a thermocouple, and the first of
     them is applied at 4× this rail's current. There is no paper argument that
     substitutes for it and ADR-0027 already refused to invent one.
   * **(b)'s tab-via item is 6 vias in a pad that already has 2** — no BOM, no
     schematic, no netlist, no new feature, −18.0 °C/W and +8.4 °C. It belongs
     in the next copper revision beside ADR-0027's deferred 5 V pour (+28.1 mV),
     and together those two would retire both margins by construction.
   * **(c) is the right answer for a v2 and the wrong answer for today.** It
     kills both problems (43 °C of thermal margin, dropout irrelevant) and it
     costs a cell respin, a new switching-noise question next to eight ADC
     channels and a thermocouple, and a full re-verification of a MATERIAL
     design change — to solve a margin that (d) may well show does not exist.
     **Spending a respin before the one-hour measurement is spending it
     blind.**

8. **THE REED PULL-IN INVARIANT IS RE-DERIVED AT THE ADR-0027 RAIL FLOOR, AND
   IT WAS 49 mV TOO LOOSE IN THE PERMISSIVE DIRECTION.** This is the same defect
   class as Decision 1 — a derived constant copied without a link back to its
   deriving source — landing on a SAFETY gate, and it is worth more than the
   worked example because a permissive safety gate is the one kind of stale
   number that costs something.

   ADR-0023 (2026-07-29) turned the reed pull-in margin from a table in an ADR
   into a machine invariant, deriving all three of
   `02_parts/DIP05-1A72-13L/part.yaml`'s constants —
   `defaults.vdd: 4.740`, `pins."2".v_ih_min: 4.740`, `pins."2".v_il_max: 0.540`
   — from `5V_KEY_RELAY vout_min = 4.740 V`. **ADR-0027 (2026-07-30) Decision 7
   re-derived that rail floor to 4.691 V once the board's own copper was counted,
   and nothing followed it into the dossier.** The correct budget is
   `4.691 − V_PI(+70 °C) 4.200 = 0.491 V`. MEASURED (by the second re-gate-3
   topology lens, calling the checker's `_grade_node_level` directly): all twelve
   `node_level` asserts are REACHED and PASS — so the gate as it stood would have
   **accepted a driven node at 0.540 V, i.e. a coil seeing 4.151 V against a
   4.200 V must-operate voltage.**

   **THE BOARD WAS NEVER AT RISK. THE GATE WAS THE DEFECT.** MEASURED node
   voltage is 0.056 V (TBD62083AFWG, 7.0 mA × 6.50 Ω), which is 8.8× inside even
   the corrected budget, and ADR-0023's margin table re-run at 4.691 V is
   positive at every corner: **+1.705 / +1.075 / +0.725 / +0.445 / +0.375 V at
   −20 / +25 / +50 / +70 / +75 °C** (49 mV below each of ADR-0023's rows).
   Ampere-turn cross-check at +70 °C: `4.691/(600+6.5)` = **7.734 mA** against
   `I_PI` 7.00 mA, **+10.5 %** (was +11.6 %).

   **`K_STOP` moved too, and its insensitivity claim did not survive intact.**
   `5V_STOP vout_min` went 4.754 → 4.702 in the same ADR-0027 decision, so
   `Q_STOPDRV`'s margins are **+1.662 / +1.032 / +0.682 / +0.402 V** and +0.332 V
   at +75 °C. The dossier used to say the un-cited 2N7002 `V_DS` was not
   load-bearing because "even an absurd 0.50 V leaves +0.054 V"; at 4.702 the
   same 0.50 V leaves **+0.002 V**, and the break-even `V_DS` is **0.502 V**. The
   conclusion is unchanged — a real 2N7002 at 7 mA with `V_GS` 3.3 V drops
   14–50 mV, 10–35× under the break-even — but the CUSHION is gone and the
   dossier now says so instead of carrying the old sentence.

   **ADR-0023's own tables are NOT rewritten**, because `01_docs/decisions/` is
   append-only and because its ULN2803A table is the EVIDENCE that forced the
   part change; falsifying it to a rail that did not exist on 2026-07-29 would
   destroy the record. The dossier's copy is annotated with both the old and new
   rows side by side, and at the lower rail the Darlington's rejection is
   strengthened by 49 mV, not weakened.

   **THE RULE, AND IT IS MACHINE-ENFORCED FROM NOW ON RATHER THAN ASSERTED. A
   DERIVED CONSTANT MUST NOT BE COPIED WITHOUT A LINK BACK TO THE ADR THAT
   DERIVED IT, AND THE THING IT WAS DERIVED FROM MUST BE NAMED ON THE SAME
   LINE.** Every constant in that block now names
   `5V_KEY_RELAY vout_min (power_tree.yaml, ADR-0027 Decision 7)`, so a future
   move of that rail is a `grep` away rather than a coincidence away — and the
   bound `COIL_PULLIN_BUDGET` below regenerates all three constants FROM
   `power_tree.yaml` and prints 999 if any of them drifts, so the link is now a
   gate and not a comment. **`governs.evaluate` reproduces the defect from the
   documents alone**: at the corrected 0.491 V the coil sees exactly 4.200 V and
   sits on its budget edge; at the stale 0.540 V it sees **4.151 V** and
   B-CORNER fires.

## Consequences

**What is now true that was not.** Both margins are published as curves over
ambient with every term at its own basis, the two missing terms are carried and
graded separately, the binding constraint is named (junction temperature, at
Ta ≈ 78–80 °C, not dropout), and the worked example that published a 2.16×
margin for four rounds is regenerated by a gate that goes red in both drift
directions.

**What is still OWED, named so silence is not read as coverage.** Items 1–6 of
the UN-CITABLE list. Four of the six retire in one bench session and that session
is now, unambiguously, the highest-value hour on this board — it is the same G4
session ADR-0026 and ADR-0027 both already book.

**What breaks if reversed.** Removing the connector term returns the sum to a
node the supply specification does not name. Restoring `F1` at a flat 23 °C
value re-asserts, of a PTC, the one property a PTC does not have. Re-adding the
`+3.8 °C` excursion re-publishes the optimistic end of an interval whose other
end is +17.8 °C. And restoring the worked example's 0.150 A puts a number in the
canonical file that is 2.16× the truth on the quantity this rail has now failed
on four times.

**Owed skill patches — the class, not this instance. NOT IMPLEMENTED;
`skills/` is outside this board's partition.** Filed alongside the others in
`06_build/staging/cooksense-v1.7/verification/owed_skill_patches.md`:

* **P15 — a series-resistance sum must declare its NODE.** `E-TOPO` grades a
  `vin_min` the author types and cannot ask which physical node it was measured
  at. ADR-0021 says "at the connector"; ADR-0027 solved to a PCB pad; nothing in
  the tree resolves the difference, and it is worth 8–24 mV against a 29 mV
  margin. The checkable form: a rail whose `vin_min` is declared at a connector
  must carry a `contact_mohm:` term resolved from the connector dossier's
  `limits:`, or `E-TOPO` refuses the declaration.
* **P16 — a resistance sum must declare a TEMPERATURE for every term, not just
  the copper.** 58 % of this sum was at three different unstated bases while the
  file asserted that no un-cited input was load-bearing. The checkable form:
  every term in a declared series sum carries `at_c:`, and a term whose part
  dossier publishes a tempco is re-evaluated at the rail's declared ambient.
* **P17 — `Tj = Ta + PD·θ_JA` must account for the board's OTHER dissipation.**
  The gate computes a package's own rise and calls it a junction temperature.
  The checkable form: where `power_tree.yaml` declares an ambient, the board's
  total non-subject dissipation is summed from the same file and the difference
  is either carried or explicitly waived.
* **P18 — a WORKED EXAMPLE in a graded source file must read only graded keys.**
  This is the general form of Decision 1. The checkable form: a comment block
  adjacent to a graded key that quotes a number may only quote numbers derivable
  from keys the grader reads, and the file declares which. G-ORPHAN already
  grades `linear_rails[].iout_max_A` as OWED and exits 0; a worked example that
  reads an OWED key is the reachable half of that finding.

**THE BOUNDS THIS ADR PUBLISHES, DECLARED SO THEY ARE REGENERATED RATHER THAN
TYPED** (canon M-BOUND). Both read `03_src/cooksense/rules/power_tree.yaml`
itself, so neither can drift from the file it describes.

<!-- bound: LDO_TJ_WORKED_EXAMPLE -->
```yaml
id: LDO_TJ_WORKED_EXAMPLE
claim: >-
  The junction temperature the power_tree.yaml dissipation worked example
  publishes, re-derived from the ONLY keys power_topology.py reads for this
  rail -- rails[3V3].vin_max, rails[3V3].vout_min, rails[3V3].iout_max_A --
  at the DECLARED ambient 75 C, the CITED ds1117 SOT-223 theta_JA 90 C/W, and
  the CITED AMS1117 quiescent current 11 mA max burning Vin_max x Iq inside the
  same package. The command ALSO re-derives PD, Tj and the margin to Tj_max
  125 C from those keys and diffs all four against the file's own
  `worked_example:` line; on ANY disagreement it prints 999 instead of a
  temperature, so a worked example that reads a key the grader does not is a
  B-REGEN failure rather than a comment nobody re-checks. That is the exact
  defect this bound exists for: v1.0-v1.7 computed the example at 0.150 A =
  linear_rails[5V_KEY_RELAY].iout_max_A and published Tj 107.9 C with "17.1 C
  margin" where the graded key gives 117.08 C and 7.92 C -- 2.16x.
relation: "<="
value: 117.08
unit: C
corner: worst_case
command: /usr/bin/python3 -c "import re;p='projects/smc0985-cooksense/03_src/cooksense/rules/power_tree.yaml';t=open(p).read();s=t.split(chr(10)+'rails:',1)[1].split(chr(10)+'linear_rails:')[0];g=lambda k:float(re.search('^    '+k+':\s*([0-9.]+)',s,re.M).group(1));vi=g('vin_max');vo=g('vout_min');io=g('iout_max_A');w=dict(x.split('=') for x in re.search('worked_example:\s(.+)',s).group(1).split());pd=(vi-vo)*io*1000;tj=75+(pd/1000+vi*0.011)*90;mg=125-tj;ok=abs(float(w['iout_A'])-io)<5e-4 and abs(float(w['pd_mW'])-pd)<0.05 and abs(float(w['tj_C'])-tj)<0.005 and abs(float(w['margin_C'])-mg)<0.005;print(round(tj,4) if ok else 999.0)"
governs:
  evaluate: /usr/bin/python3 -c "print(125.0 - {value})"
  budget: ">= 0"
  unit: C
  note: >-
    The margin to the CITED ds1117 Tj_max of 125 C. This is the number
    power_tree.yaml publishes and the number ADR-0026 was written to establish.
    It does NOT include the board's other 0.958 W (+1.55...+4.65 C, DERIVED,
    see the ladder above): that term is real and is named, and it is not folded
    into a graded value because it is a model output rather than a citation.
tolerance: 0.01
tolerance_why: >-
  `value` is the file's own published Tj rounded to two decimals from an exact
  117.0795 C, so 0.01 C is one unit in the last declared place. It is 792x
  smaller than the 7.92 C margin the bound has to rule on, and 918x smaller
  than the 9.18 C error the pre-fix worked example carried -- so it cannot mask
  either the defect being closed or a future recurrence of it.
grade: CITED
requires:
  - projects/smc0985-cooksense/03_src/cooksense/rules/power_tree.yaml
```

<!-- bound: LDO_TA_MAX_CITED -->
```yaml
id: LDO_TA_MAX_CITED
claim: >-
  Highest AMBIENT at which the AMS1117-3.3's junction stays at or under the
  CITED ds1117 maximum of 125 C, on the form the release actually publishes --
  Tj = Ta + PD x theta_JA with PD taken from rails[3V3]'s own graded keys and
  theta_JA the CITED SOT-223 package figure of 90 C/W. This is the CITABLE
  ceiling and it is deliberately the OPTIMISTIC one: it omits the board's other
  0.958 W, which the v1.7 re-gate-3 layout lens derives at +1.55...+4.65 C and
  which therefore moves the real ceiling DOWN to 78.3...80.1 C. The declared
  ambient is 75 C (BRIEF.md's HARD enclosure limit), inside this ceiling by
  7.9 C citable and by 3.3...5.1 C honestly. Published so that an ambient
  decision -- which this ADR deliberately does not take -- is made against a
  regenerated number rather than a remembered one.
relation: "<="
value: 82.92
unit: C
corner: worst_case
command: /usr/bin/python3 -c "import re;p='projects/smc0985-cooksense/03_src/cooksense/rules/power_tree.yaml';t=open(p).read();s=t.split(chr(10)+'rails:',1)[1].split(chr(10)+'linear_rails:')[0];g=lambda k:float(re.search('^    '+k+':\s*([0-9.]+)',s,re.M).group(1));vi=g('vin_max');vo=g('vout_min');io=g('iout_max_A');print(round(125.0-((vi-vo)*io+vi*0.011)*90.0,4))"
governs:
  evaluate: /usr/bin/python3 -c "print({value} + 42.0795)"
  budget: "<= 125"
  unit: C
  note: >-
    Tj at the published ambient ceiling. 42.0795 C is the CITED rise
    (PD_LDO 0.4676 W x theta_JA 90 C/W) at the declared keys, and it is the
    quantity LDO_TJ_WORKED_EXAMPLE regenerates independently -- so a ceiling
    published at the wrong ambient lands Tj outside 125 C here and fails
    B-CORNER from the document alone.
tolerance: 0.01
tolerance_why: >-
  `value` is rounded to two decimals from an exact 82.9205 C, so 0.01 C is one
  unit in the last declared place. It is 792x smaller than the 7.92 C distance
  to the declared 75 C ambient -- the value this ceiling has to rule on -- and
  155x smaller than the smallest board-rise correction (1.55 C) it is published
  alongside, so it cannot mask either.
grade: CITED
requires:
  - projects/smc0985-cooksense/03_src/cooksense/rules/power_tree.yaml
```

<!-- bound: COIL_PULLIN_BUDGET -->
```yaml
id: COIL_PULLIN_BUDGET
claim: >-
  Largest voltage the DRIVEN end of a DIP05-1A72-13L reed coil may sit at and
  still guarantee pull-in at the top of the declared operating envelope. It is
  ADR-0023's `node_level` invariant constant
  02_parts/DIP05-1A72-13L/part.yaml electrical.pins."2".v_il_max, and it is
  NOT a logic threshold -- node <= budget is exactly equivalent to the coil
  seeing >= V_PI(+70 C) 4.200 V, which is the datasheet's 3.500 V pull-in taken
  through its own 0.4 %/K footnote referenced to 20 C. The budget is DERIVED as
  5V_KEY_RELAY vout_min minus that pull-in, so it moves whenever the rail
  moves. The command re-reads the rail floor from power_tree.yaml, re-reads all
  three dossier constants, and prints 999 unless vdd equals the rail, v_ih_min
  equals vdd, and v_il_max equals vdd minus v_pullin_max_70C -- so a constant
  copied without a link back to what derived it is a B-REGEN failure. That is
  the defect this bound exists for -- ADR-0023 derived 0.540 V from a 4.740 V
  rail, ADR-0027 Decision 7 re-derived the rail to 4.691 V, and nothing followed
  it, leaving a SAFETY gate 49 mV too loose in the PERMISSIVE direction for one
  day. The board was never at risk (measured node 0.056 V); the gate was.
relation: "<="
value: 0.491
unit: V
corner: worst_case
command: /usr/bin/python3 -c "import re,yaml;pt=open('projects/smc0985-cooksense/03_src/cooksense/rules/power_tree.yaml').read();seg=pt.split('- name'+chr(58)+' 5V_KEY_RELAY',1)[1].split(chr(10)+'  - name')[0];rail=float(re.search('vout_min'+chr(58)+'\s*([0-9.]+)',seg).group(1));e=yaml.safe_load(open('projects/smc0985-cooksense/02_parts/DIP05-1A72-13L/part.yaml'))['electrical'];vdd=e['defaults']['vdd'];vpi=e['v_pullin_max_70C'];p2=e['pins']['2'];ok=abs(vdd-rail)<1e-9 and abs(p2['v_ih_min']-rail)<1e-9 and abs(p2['v_il_max']-(vdd-vpi))<1e-9;print(round(p2['v_il_max'],4) if ok else 999.0)"
governs:
  evaluate: /usr/bin/python3 -c "import yaml;print(round(yaml.safe_load(open('projects/smc0985-cooksense/02_parts/DIP05-1A72-13L/part.yaml'))['electrical']['defaults']['vdd']-{value},4))"
  budget: ">= 4.2"
  unit: V
  note: >-
    The voltage the COIL sees when the driven end sits exactly at the budget,
    against V_PI(+70 C) = 4.200 V. This is what reproduces the defect from the
    documents alone -- 0.491 gives exactly 4.200 and sits on the edge, while
    ADR-0023's stale 0.540 gives 4.151 V and fires B-CORNER. The MEASURED node
    on this board is 0.056 V (TBD62083AFWG, 7.0 mA x 6.50 ohm), 8.8x inside.
tolerance: 0.0005
tolerance_why: >-
  `value` is an exact difference of two three-decimal constants (4.691 - 4.200),
  so 0.0005 V is half a unit in the last declared place and exists only to
  absorb float representation. It is 98x smaller than the 0.049 V distance to
  the stale 0.540 V this bound has to rule out, and 870x smaller than the
  0.435 V distance to the measured node 0.056 V, so it cannot mask either the
  defect being closed or a recurrence of it.
grade: CITED
requires:
  - projects/smc0985-cooksense/03_src/cooksense/rules/power_tree.yaml
  - projects/smc0985-cooksense/02_parts/DIP05-1A72-13L/part.yaml
```

**No bound is published for the DROPOUT margin over ambient, and that is a
finding rather than an omission.** Two of its inputs — `F1`'s tempco and the
in-build contact resistance — are UN-CITABLE, and a third (the AMS1117 dropout
at 0.2 A) is the figure the whole comparison is against. A regenerated bound
over un-citable inputs would be a typed number wearing a command. The dropout
ladder is published as a table at the corners it was computed at, and it stays
that way until the bench session in Decision 7 retires the inputs.
