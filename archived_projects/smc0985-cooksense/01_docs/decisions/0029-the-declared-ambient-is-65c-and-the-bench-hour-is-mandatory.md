# ADR-0029 — the declared operating ambient is 65 °C, the bench hour is
# MANDATORY, and narrowing a declaration is not allowed to relax a gate

---
id: 0029
date: 2026-07-30
status: accepted
---

tags: power, thermal, dropout, envelope, gates, bench-obligation
relates: ADR-0026 (the ceiling is a junction temperature at a DECLARED
ambient — this ADR chooses the ambient it left open), ADR-0027 (the dropout
half and the board's own copper), ADR-0028 (both margins as curves over
ambient; **its Decision 6 deliberately did not take this decision — this is
the decision it deferred**), ADR-0021 (the supply is a specification),
ADR-0014 (OPEN item 2 — the board's own thermal zone is undeclared)
amends: `01_docs/BRIEF.md` (D12 + the thermal-envelope fact-lock row),
`03_src/cooksense/rules/power_tree.yaml` (the declared-envelope block),
`06_build/staging/cooksense-v1.7/ORDER_README.md` (§0-T and §7b)

## Context

ADR-0028 published both of the 3V3 rail's margins as curves over ambient,
established that they bind in DIFFERENT places, and then **refused to declare an
envelope**, on the ground that an operating restriction on a product belongs to
whoever owns the enclosure and is not an arithmetic result. Its Decision 6 says
so explicitly and its Decision 7 recommends a rung.

**The user has now taken that decision** (2026-07-30, binding): narrow the
declared ambient to **65 °C** AND add a **mandatory bench gate** to
`ORDER_README.md`. Options (b) tab-vias, (c) a switching regulator and (d) seal
at 75 °C on the bench gate alone were considered and **not chosen**; 75 °C stays
reopenable for free once bench data exists.

Two facts made 65 °C the rung rather than 55 or 75:

1. **The board is THERMALLY limited, not dropout-limited.** The dropout margin
   moves **−0.31 mV/K** — copper is 42 % of the series sum at 0.393 %/K, so 62 K
   of ambient moves it by 19 mV, less than the connector-contact term alone.
   Ambient is the wrong knob for the dropout and the right knob for the
   junction, which moves 1 °C per °C.
2. **65 °C is the BRIEF's own `stop` rung** (`enclosure <=50 / 55 / 65 / 75` —
   preferred / warn / stop / HARD). Choosing it invents no fact and asks the
   integrator for nothing the commission did not already contemplate. It also
   sits below `F1`'s −40…+85 °C operating ceiling with room, which 75 °C does
   not once the board-rise term is carried.

## Options

**(a) NARROW THE DECLARED AMBIENT TO 65 °C — CHOSEN.** Costs one row in the
BRIEF's fact-lock, one block in `power_tree.yaml`, one section in
`ORDER_README.md`, and an operating restriction the integrator must honour.
Zero engineering, zero BOM, zero copper. Buys the thermal margin outright.

**(d) A MANDATORY BENCH GATE IN `ORDER_README.md` — ALSO CHOSEN, and it is the
half that attacks the dropout.** The dropout problem is an EVIDENCE problem, not
a design problem: the whole comparison is a **1300 mV figure ds1117 publishes
only at 0.8 A, applied to a 0.2 A rail**. One bench hour retires four of the six
un-citables. This repo has precedent for a mandatory bench obligation in an
ORDER_README — pod-v2's continuity check and usb-hub's 5 A-hot check are both
order-paperwork gates of exactly this shape, and ADR-0027's heater-stagger
constraint is already one on this very board (§7a-3).

**(b) REDUCE THE DROP — NOT DONE THIS REVISION, ONE ITEM RECOMMENDED FOR THE
NEXT.** 6 more vias in the EXISTING `U_LDO` tab pad (2 → 8 × 0.15 mm) is
**−18.0 °C/W and +8.4 °C of junction margin with NO BOM, schematic, netlist or
feature change** — the cheapest item in ADR-0028's whole options table. It is
**RECOMMENDED as the next-copper-revision improvement**, beside ADR-0027's
deferred 5 V pour (+28.1 mV); together those two retire both margins by
construction. It is not done here because v1.7's fab set is otherwise invariant
and a copper edit re-opens routing, DRC and a full material-change re-gate.

**(c) REPLACE THE LDO WITH A SWITCHING REGULATOR — REJECTED FOR v1.7.** It kills
both problems (43 °C of thermal margin; the dropout question stops existing) and
costs a cell respin, a new switching-noise question beside eight ADC channels and
a thermocouple front end, and a full re-verification. **Spending a respin before
the one-hour measurement is spending it blind.** It remains the right answer for
a v2 if the bench hour says so.

**(e) SEAL AT 75 °C ON THE BENCH GATE ALONE — REJECTED.** This was ADR-0028's
option (d) taken without (a). Rejected because at 75 °C the honest junction
margin is **3.3…6.4 °C** and 20–59 % of the published 7.92 °C is consumed by a
term the published form does not carry. A margin that thin should not be shipped
on a promise of a future measurement.

## Decision

**1. THE DECLARED OPERATING AMBIENT FOR THIS BOARD IS 65 °C.** It is recorded in
`BRIEF.md` as **D12** and as a `thermal envelope` fact-lock row, in
`power_tree.yaml`'s declared-envelope block, and in `ORDER_README.md` §0-T. The
BRIEF's enclosure `75` rung is retained as the **SURVIVE corner** — the
temperature the board must not be destroyed by — and is no longer the corner the
margin is declared at.

**2. THE NUMBERS AT 65 °C, DERIVED HERE RATHER THAN ROUNDED.** MEASURED (by me,
`/usr/bin/python3`, from the CITED constants only — ds1117 `θ_JA` 90 °C/W
(SOT-223 package figure), `T_J(max)` 125 °C, `I_q(max)` 11 mA — and
`power_tree.yaml`'s own graded keys `vin_max` 5.250 / `vout_min` 3.201 /
`iout_max_A` 0.200):

```
  PD_pass = (5.250 - 3.201) x 0.200        = 409.800 mW
  PD_q    = 5.250 x 0.011                  =  57.750 mW   (inside the same package)
  rise    = (409.800 + 57.750) mW x 90 C/W =  42.0795 C
  Tj(65)  = 65 + 42.0795                   = 107.0795 C
  margin  = 125 - 107.0795                 =  17.9205 C   <- CITABLE FORM
```

**AND THE PUBLISHED FORM IS NOT THE HONEST ONE, AT EITHER AMBIENT.** `θ_JA` is a
junction-to-**ambient-air** figure measured with only the device under test
dissipating, and ds1117's own Thermal Considerations says *"additional heat
sources mounted near the device must be considered."* This board's other
**0.958 W** (12 reed relay coils at 0.705 W dominate) raises the copper the tab
sinks into by a DERIVED **+1.55…+4.65 °C** (ADR-0028, from the v1.7 re-gate-3
layout lens's thermal network across h = 18…6 W/m²K):

| Ta | CITABLE margin (published form) | + board rise, h=18 | h=10 | h=6 |
|---|---|---|---|---|
| 55 °C | 27.92 °C | 26.37 | 25.13 | 23.27 |
| **65 °C — DECLARED** | **17.92 °C** | **16.37** | **15.13** | **13.27** |
| 70 °C | 12.92 | 11.37 | 10.13 | 8.27 |
| 75 °C — SURVIVE corner | 7.92 | 6.37 | 5.13 | 3.27 |
| 80 °C | 2.92 | 1.37 | 0.13 | **−1.73 FAIL** |

**THE HONEST JUNCTION MARGIN AT THE DECLARED 65 °C IS 13.3…16.4 °C**, with
**15.1 °C** at the layout lens's central h = 10. The 7.92 °C the release used to
publish at 75 °C was wrong REGARDLESS of the envelope decision — not because the
arithmetic was wrong but because the form omits a term that is 20–59 % of it —
and the honest figure at 75 °C is **3.3…6.4 °C**. Both rows are published above
with their derivation rather than a rounded reassurance, which is the whole
point of the table.

Citable ambient ceiling, unchanged by this decision because it is a property of
the part and not of the declaration: **Ta ≤ 82.92 °C** on the published form,
**78.3…81.4 °C** carrying the board rise. The declared 65 °C sits inside the
honest ceiling by **13.3…16.4 °C**.

**3. THE DROPOUT MARGIN AT 65 °C IS +19.5 mV WORST CASE, AND NARROWING BOUGHT
+1.4 mV OF IT.** INHERITED from ADR-0028's ladder (MEASURED by its author with
an independent nodal model whose control reproduces `V(U_LDO.3) = 4.7281 V` /
`1329.1 mV` exactly; **NOT re-derived by me** — I do not hold ADR-0027's two
transfer resistances decomposed into their copper and component parts):

| Ta | no connector | **2 × 10 mΩ (CITED Micro-Fit max)** | 2 × 30 mΩ (aged, INHERITED) |
|---|---|---|---|
| 75 °C (the old declaration) | +26.2 mV | **+18.1 mV** | +2.0 mV |
| **65 °C — DECLARED** | **+27.6 mV** | **+19.5 mV** | **+3.4 mV** |

**The slope is the headline, not the row: −0.31 mV/K.** 75 → 65 buys +1.4 mV,
which is nothing, and that is exactly why the decision is (a) AND (d) rather
than (a) alone. The typical case is +497 mV; the distance between +19.5 and
+497 is the corner stack, and the single largest term in it is a dropout figure
specified at four times this rail's current.

**4. `pdiss_max_mw` IS DELIBERATELY LEFT AT 497 — THE 75 °C DERATING — SO THAT
NARROWING A DECLARATION CANNOT RELAX A GATE.** This is the load-bearing
structural choice in this ADR and it is stated plainly because the opposite is
the tempting one.

`rails[3V3].pdiss_max_mw` is the ONLY graded home this file has for a thermal
derating (`power_topology.py` reads it; G-ORPHAN fails any key no gate reads,
and the contract template that would carry a first-class `ambient_c:` row lives
in `skills/`). At the newly declared 65 °C the arithmetically correct derating
is **608 mW** — `(125−65)/90 × 1000 − 5.250 × 11 = 608.92`, floored. Moving the
key there would be defensible and it is **NOT DONE**, because:

* the gate was never red. `PD = 409.8 mW` against 497 is **82.5 %** and E-TOPO
  PASSES; against 608 it would be 67.4 %. **Nothing is rescued by the change**,
  so the only thing it would buy is a looser ceiling — and this repo's canon is
  that it has ratchet FLOORS and no CEILINGS. Narrowing a declared envelope must
  not be a mechanism for weakening a machine gate, or the envelope becomes a
  knob someone reaches for when a gate goes red.
* holding 497 keeps the gate enforcing `Tj ≤ 125 °C` at the **SURVIVE** corner
  (75 °C), which is strictly stronger than enforcing it at the declared corner.
* it keeps ADR-0026's `LDO_IOUT_MAX` and ADR-0028's `LDO_TJ_WORKED_EXAMPLE` and
  `LDO_TA_MAX_CITED` regenerating **unchanged and true**, with no edit to any
  accepted ADR. `01_docs/decisions/` is append-only and only `status:` may move;
  a bound that had to be rewritten to accommodate this decision would be an edit
  to an accepted decision record, and the decision does not require one.

**The consequence, said out loud so it is not discovered later:**
`power_tree.yaml` now carries a derating computed at 75 °C beside a declaration
of 65 °C, and that is intentional, not drift. The file says so at the key, and
the bound below regenerates the 65 °C figures from the same graded keys so the
declared corner is machine-checked too.

**5. THE MANDATORY BENCH GATE, AS WRITTEN INTO `ORDER_README.md` §7b.** Six
measurements, one sitting, before the board is trusted above bench conditions.
It is MANDATORY — not advisory — and it is the gate that retires the un-citables
this rail has been arguing about for five passes:

| # | measurement | retires |
|---|---|---|
| B1 | `F1` (MF-MSMF200/8X) resistance vs temperature, 23 → 85 °C in an oven or on a hotplate, 4-wire | **`F1` R-vs-T.** Bourns publishes NONE; every ambient above 23 °C currently rests on inverting their `Ihold` derating table under a named assumption |
| B2 | `J_PWR` Micro-Fit contact resistance in THIS build — these crimps, this wire gauge, after ≥5 mating cycles, both legs, 4-wire across the mated pair | **Micro-Fit contact resistance in THIS build.** 10 mΩ/contact is a specification MAXIMUM; the aged ≤60 mΩ allowance is INHERITED from a document this tree could not fetch |
| B3 | **AMS1117-3.3 dropout at 0.2 A** — sweep `V_IN` down at the rail's real load until `V_OUT(3V3)` leaves regulation; record `V_IN − V_OUT` at 0.2 A and at 0.4 A | **the figure that dominates everything.** ds1117 publishes dropout ONLY at 0.8 A, has no dropout-vs-load curve, and says only that it *"decreases at lower load currents"*. If it is anywhere near the 300–500 mV a 1 A LDO typically shows at a quarter load, the margin goes from +19.5 mV to ~+800 mV and **options (b) and (c) both become unnecessary** |
| B4 | `θ_JA` on THIS mounting — `U_LDO` tab rise above a known ambient at the rail's real total load, thermocouple on the tab | **`θ_JA` on this mounting.** 90 °C/W is the PACKAGE figure; the layout lens's independent network gives 81.6…92.3 °C/W, i.e. 90 is central-to-slightly-optimistic, not conservative |
| B5 | `ΔT_board` — board copper temperature near `U_LDO` with all 12 reed coils energised vs all coils off, same ambient | **the board's own rise.** +1.55…+4.65 °C is a MODEL OUTPUT, not a measurement, and it is 20–59 % of the thermal margin |
| B6 | SOT-223 thermal time constant — step the load and log the tab rise to steady state | **the SOT-223 thermal time constant** (ADR-0027 Decision 4). Without it no transient excursion on this package is bounded by any cited number |

**PASSING B1–B6 MAY REOPEN 75 °C.** That is the point of writing them down: the
75 °C envelope is not refuted, it is UNPROVEN, and it is reopenable for free
against measured data — a documentation-only supersede, no copper, no BOM. The
`ORDER_README` section says so in those words.

**6. WHAT THIS ADR DOES NOT DO.** It does not supersede ADR-0026, ADR-0027 or
ADR-0028 — each of their decisions stands, and ADR-0028 Decision 6 explicitly
reserved this choice for whoever owns the enclosure rather than deciding it
wrongly. It changes no copper (`04_kicad/cooksense.kicad_pcb` md5
`9f4fd5fae810f40a52b1035df727243c`, unmoved through all three re-gate rounds and
DRC 0/0/0), no netlist, no BOM and no CPL. **It is a DECLARATION change plus an
order-paperwork obligation.**

## Consequences

**What is now true that was not.** The board has a declared operating ambient
with a margin published at that ambient in BOTH forms — citable 17.92 °C and
honest 13.3…16.4 °C — and the term that makes the two differ is named rather
than folded in. The un-citables have a dated, mandatory home in the order
paperwork instead of living in an ADR's OWED list where nobody at bring-up
would read them.

**What this commits us to.** An operating restriction the integrator must
honour (`TH_ENCLOSURE` is already one of the eight monitored ADC channels, so
the board can see its own violation); a bench hour before the board is trusted
above bench conditions; and the tab-via item carried into the next copper
revision's work order.

**What breaks if reversed.** Restoring a 75 °C declaration re-publishes a
7.92 °C margin whose honest value is 3.3…6.4 °C, at an ambient where `F1` sits
10 °C from its own operating ceiling and where the aged-contact dropout row is
+2.0 mV. Moving `pdiss_max_mw` to 608 turns the envelope into a gate-relaxation
mechanism, which is the failure mode Decision 4 exists to refuse.

**Still OWED, named so silence is not read as coverage** (canon M-OWED): every
item in the B1–B6 table until the bench session is done, plus ADR-0028's
`J_LOADCELL.1` 5 V draw and `D_ESD_IN`'s stand-off derating (a v-next BOM
change, ADR-0028 Decision 5).

**MEASURED CORRECTION TO AN INHERITED CLAIM, recorded because it changed what
this pass had to do.** The seal brief for this pass carried, as fact, that two
`EVIDENCE PATH MISMATCH` findings were document defects in ADR-0025's and
`DISPOSITIONS.md`'s bodies. **They are not.** MEASURED (by me, by re-running
`release_freshness_check.py` with `--releases-root` pointed at the project's
real `07_releases/`): both named directories are REAL sibling releases, and the
checker resolves siblings against `release_dir.parent`, which for a STAGING
directory is `06_build/staging/`. The documents are correct; the invocation was
under-specified. Two of the three declared "freshness blockers" required no edit
at all, and the same defect had also manufactured a phantom
`STOCK-INSUFFICIENT` + `ORDER-DECL-FALSE` pair by failing to find
`03_src/rules/assembly.yaml` from a staging path. **A gate run against staging
must be told where the releases root and the assembly file are, or it invents
findings about the archive's own correct contents.**

**Owed skill patch — the class, not this instance. NOT IMPLEMENTED; `skills/` is
outside this board's partition.** Filed with P15–P19 in
`06_build/staging/cooksense-v1.7/verification/owed_skill_patches.md`:

* **P20 — a declared ENVELOPE needs a graded home that is not a derating.**
  `power_tree.yaml` can express "the ceiling handed to the gate" but cannot
  express "the ambient the product is declared for", so Decision 4 had to choose
  between a correct declaration and an unrelaxed gate. The checkable form: a
  first-class `rails[].ambient_c:` read by `power_topology.py`, which DERIVES
  `pdiss_max_mw` from it and refuses a hand-typed value that disagrees — with a
  separate `survive_ambient_c:` so a ratchet at the harder corner is sayable
  instead of being a comment.
* **P21 — `release_freshness_check.py` must not silently resolve a STAGING
  directory's siblings against its staging parent.** Running it pre-seal is the
  documented, mandated workflow ("everything runs against the PRE-SEAL STAGING
  archive"), and in that exact workflow three of its checks look for
  `release_dir.parent` siblings and `release_dir.parent.parent/03_src` and find
  neither. The checkable form: when the release dir is not under a
  `07_releases/`, the tool RESOLVES the owning project (or refuses), rather than
  emitting findings that name the archive's own correct content as foreign.

**THE BOUND THIS ADR PUBLISHES, DECLARED SO IT IS REGENERATED RATHER THAN
TYPED** (canon M-BOUND). It reads `03_src/cooksense/rules/power_tree.yaml`
itself, so it cannot drift from the file it describes, and it is deliberately
the DECLARED-corner twin of ADR-0028's `LDO_TJ_WORKED_EXAMPLE`, which stays at
the SURVIVE corner and is not touched.

<!-- bound: LDO_TJ_DECLARED_AMBIENT -->
```yaml
id: LDO_TJ_DECLARED_AMBIENT
claim: >-
  The AMS1117-3.3 junction temperature at THIS BOARD'S DECLARED OPERATING
  AMBIENT of 65 C, re-derived from the only keys power_topology.py reads for
  this rail -- rails[3V3].vin_max, rails[3V3].vout_min, rails[3V3].iout_max_A
  -- with the CITED ds1117 SOT-223 theta_JA of 90 C/W and the CITED AMS1117
  quiescent current of 11 mA max burning Vin_max x Iq inside the same package.
  The command re-derives the ambient, PD, Tj and the margin to Tj_max 125 C
  from those keys and diffs all four against the file's own
  `declared_envelope_example:` line, ALSO asserting that the declared ambient
  in that line is 65 C -- so restoring a 75 C declaration, or letting the
  example drift from the graded keys, prints 999 instead of a temperature and
  fails B-REGEN. This is the CITABLE form and it is deliberately the OPTIMISTIC
  one: it omits the board's other 0.958 W, which the v1.7 re-gate-3 layout lens
  derives at +1.55...+4.65 C and which moves the honest margin to 13.3...16.4 C.
  That term is a model output rather than a citation, so it is NAMED in the
  table above and not folded into a graded value.
relation: "<="
value: 107.08
unit: C
corner: worst_case
command: /usr/bin/python3 -c "import re;p='projects/smc0985-cooksense/03_src/cooksense/rules/power_tree.yaml';t=open(p).read();s=t.split(chr(10)+'rails:',1)[1].split(chr(10)+'linear_rails:')[0];g=lambda k:float(re.search('^    '+k+':\s*([0-9.]+)',s,re.M).group(1));vi=g('vin_max');vo=g('vout_min');io=g('iout_max_A');w=dict(x.split('=') for x in re.search('declared_envelope_example:\s(.+)',s).group(1).split());ta=float(w['ta_C']);pd=(vi-vo)*io*1000;tj=ta+(pd/1000+vi*0.011)*90;mg=125-tj;ok=abs(ta-65.0)<1e-9 and abs(float(w['iout_A'])-io)<5e-4 and abs(float(w['pd_mW'])-pd)<0.05 and abs(float(w['tj_C'])-tj)<0.005 and abs(float(w['margin_C'])-mg)<0.005;print(round(tj,4) if ok else 999.0)"
governs:
  evaluate: /usr/bin/python3 -c "print(125.0 - {value})"
  budget: ">= 0"
  unit: C
  note: >-
    The margin to the CITED ds1117 Tj_max of 125 C at the DECLARED ambient.
    17.92 C citable. It does NOT include the board's other 0.958 W
    (+1.55...+4.65 C, DERIVED), which takes the honest margin to 13.3...16.4 C
    -- still positive at every h in the lens's range, which is the property the
    envelope decision was taken to obtain and the property 75 C did not have.
tolerance: 0.01
tolerance_why: >-
  `value` is the file's own published Tj rounded to two decimals from an exact
  107.0795 C, so 0.01 C is one unit in the last declared place. It is 1327x
  smaller than the 13.27 C worst honest margin the bound has to rule on and
  1000x smaller than the 10 C step between the declared ambient and the survive
  corner it must not be confused with, so it cannot mask either a drift back to
  75 C or a future recurrence of the worked-example defect.
grade: CITED
requires:
  - projects/smc0985-cooksense/03_src/cooksense/rules/power_tree.yaml
```
