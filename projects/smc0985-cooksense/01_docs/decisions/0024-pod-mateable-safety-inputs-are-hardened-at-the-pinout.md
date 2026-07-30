# ADR-0024 — every pod-mateable safety input is hardened AT THE PINOUT, and
# ADR-0018's 680 Ω does not transfer to a 3.3 V Schmitt

status: accepted
date: 2026-07-29
tags: protection, topology, connectors, safety
extends: ADR-0018 (which closed this class on ONE net and did not carry it)
supersedes-in-part: v1.7 pin-review FRESH-LENS finding C1

## The defect this closes

`J_DOOR` pin 4 was `DOOR_RAW`. On the two POD housings that are the SAME PART —
`C189896` / `SM05B-GHS-TB`, so physically cross-mateable — pin 4 is `SCL_*`, a
line a sensor pod holds HIGH through its own module pull-up. On `J_ESTOP` pin 4
is GND. **`J_DOOR` alone put a safety sense node on the one pin a cross-mated
pod actively drives.**

An SHT45 pod harness cross-plugged into `J_DOOR` powers up normally from pin 1
(real 3V3) and lands its pulled-up SCL wire on `DOOR_RAW` against `R_DOORPD`:

| injected pull-up | source of the value | V(`DOOR_RAW`) at `R_DOORPD` = 10 kΩ |
|---|---|---|
| 10 kΩ | `DETAIL_DESIGN.md:114`, "SHT pods carry module 10k pullups" | 3.3 · 10/20 = **1.650 V** |
| 2.2 kΩ | **this board's own I2C pull-up value** (`R_SCLA`/`R_SDAA`…), and the value ADR-0018's own injection table already declares as the worst case | 3.3 · 10/12.2 = **2.705 V** |

`U_SCHM` is an SN74HC14 on **3V3**, and SCLS085L §5.5 specifies thresholds only
at V_CC = 2.0 / 4.5 / 6.0 V — **there is no guaranteed 3.3 V row.** Every
available reading condemns it, which is why the conclusion needs no
interpolation to be safe:

| bound | value | verdict |
|---|---|---|
| V_T+ **MIN**, 4.5 V row (the mildest bar) | 1.550 V | 1.650 V already exceeds it ⇒ a CONFORMING part *may* read the door CLOSED |
| V_T+ **MAX**, interpolated to 3.3 V (a model) | 2.348 V | 2.705 V exceeds even that ⇒ at the 2.2 kΩ corner it is a **GUARANTEED HIGH** |

`DOOR_OK` = **door CLOSED with no door attached**, on the interlock of a cooking
appliance. The fresh lens computed 1.650 V and graded it QUESTION; re-derived
from the netlist with this board's own pull-up value it is **1.055 V worse than
that and crosses from "permitted" to "guaranteed".**

## What ADR-0018 already knew, and the exact shape of what it missed

ADR-0018 closed this hazard class on `COIL_EN_IN` in v1.7, with a two-layer
remedy: a MECHANICAL KEY (J_MODE leaves the JST-GH family) as the primary, and a
680 Ω pull-down **at the connector pin** plus a 680 Ω series element as the
second layer. Its own 20-cell cross-plug matrix then recorded, in writing:

| class | v1.6 | v1.7 |
|---|---|---|
| ? driven into the threshold band | 4 | **4 — pod → J_DOOR/J_ESTOP, untouched** |

**Those four untouched cells are this ADR.** The remedy was known, proven on
this board, published with its arithmetic, and left applied to one of three
field-fed safety inputs. That is the third time this exact shape has appeared
here (ADR-0020 computed a remedy and applied it to one of six expander pins;
ADR-0023's dossier carried the hot-corner R_ON on one of eleven pads), so the
generalisation step is treated as part of the fix, not as follow-up.

## Decision A — `J_DOOR` pin 4 becomes GND. Remove the path, do not attenuate it.

`J_DOOR` = 1:`3V3`, 2:`DOOR_RAW_IN`, 3:GND, **4:GND**, 5:GND — pin-identical to
`J_ESTOP`, which was already safe against the pod cross-plug *and only because
its pin 4 is GND*.

**Pin 4 was not carrying the harness.** The door harness is 3V3 on pin 1 → Form-A
reed → pin 2 (ORDER_README §10.1). Pins 2 and 4 being ONE net is also what made
door EOL supervision unimplementable as built (v1.7 topology P1), so this removes
a redundancy that only ever cost.

**THE COMPLETE ENUMERATION, and the denominator is stated.** Four `C189896`
housings ⇒ **12 ordered cross-plug pairs**. `J_MODE` is excluded and the
exclusion is mechanical, not a judgement (ADR-0018 C: a 4.15 mm GHR-05V-S plug
cannot enter a 3.70 mm ZH shroud). Post-fix pinouts:

```
J_DOOR        1=3V3          2=DOOR_RAW_IN   3=GND    4=GND    5=GND
J_ESTOP       1=3V3          2=ESTOP_RAW_IN  3=GND    4=GND    5=GND
J_RH_AMBIENT  1=3V3_SW_RHA   2=GND           3=SDA_A  4=SCL_A  5=SHIELD_DRAIN
J_RH_EXHAUST  1=3V3_SW_RHE   2=GND           3=SDA_B  4=SCL_B  5=SHIELD_DRAIN
```

A pod harness SOURCES current on pin 1 (VDD, a load) and pins 3/4 (pulled up
through the module); it SINKS on pin 2 (GND) and pin 5 (shield).

| cross-plug | what lands where | verdict |
|---|---|---|
| pod → `J_DOOR` | pod pins 3,4 (pulled up) → GND; pod pin 2 (GND) → `DOOR_RAW_IN` | `DOOR_RAW_IN` becomes the pod's own ground and sits **0.235 mV** above real GND (SHT45 measurement current 500 µA max × `R_DOORPD` 470 Ω; the pod's two module pull-ups return to real GND through pins 3/4, not through this node) ⇒ door reads **OPEN**. RESTRICTIVE |
| pod → `J_ESTOP` | same | `ESTOP_RAW_IN` LOW ⇒ E-stop reads **ASSERTED**. RESTRICTIVE |
| door harness → `J_RH_*` | reed between `3V3_SW_RH*` and GND | shorts a switched sensor rail when the door shuts; rail dies, and a 3V3 droop trips the TPS3823 ⇒ `WD_OK` LOW. LOUD and RESTRICTIVE |
| E-stop harness → `J_RH_*` | NC contact between `3V3_SW_RH*` and GND | same, shorted while NOT pressed. LOUD |
| pod ↔ pod | ambient/exhaust transposed | silent measurement transposition (both SHT45 @ 0x44 on different buses). Carried, unchanged — a measurement defect, not a permission defect |
| `J_DOOR` ↔ `J_ESTOP` | both are pin-1-2 dry contacts | **NOT CLOSED BY THIS ADR.** See "What this does not do" |

**ZERO cells remain in which a cross-plug asserts a permission.** ADR-0018's
four `?` cells go to 0.

## Decision B — the second layer, with the value RE-DERIVED, not copied

`DOOR_RAW` and `ESTOP_RAW` are SPLIT at a series element, exactly ADR-0018's
ordering:

    J_DOOR.2 ── DOOR_RAW_IN ──┬── R_DOORPD 470R ── GND
                              ├── D_DOOR (PESD5V0S1BA) ── GND
                              └── R_DOORS 680R ── DOOR_RAW ── U_SCHM.11 (5A)

**680 Ω DOES NOT TRANSFER, AND THAT IS THE FINDING.** Carrying the *pattern* is
right; carrying the *value* would have looked like the proven remedy and would
not have closed the case:

    680R worst case: 3.3 · 686.8/(686.8 + 2178) = 0.791 V   (R +1%, injection −1%)

ADR-0018's receiver is a 2N7002 whose `V_GS(th)` **MIN is 1.000 V**, so 0.791 V
clears it by 209 mV. This receiver's bar is its LOWEST possible switching point,
and `V_T+` rises monotonically with V_CC, so SCLS085L's **V_CC = 2.0 V row
bounds V_T+(min) at 3.3 V from below with no interpolation: 0.700 V.** 0.791 V
**exceeds it.**

| pull-down | injected 2.2 kΩ | injected 10 kΩ | vs V_T+(min) 0.700 V |
|---|---|---|---|
| 10 kΩ (v1.7) | 2.705 V | 1.650 V | FAIL by 2.005 V |
| 680 Ω (ADR-0018's value) | **0.791 V** | 0.221 V | **FAIL by 91 mV** |
| **470 Ω (chosen)** | **0.591 V** (0.608 V at the rail ceiling **3.399 V**, `power_tree.yaml` 3V3 `vout_max`) | 0.151 V | **PASS, +92 mV** |

General bound: V ≤ 0.700 V ⇒ **R_pd ≤ 559 Ω at the WORST-CASE corner.**

**CORRECTED 2026-07-29 by an independent re-derivation, and the correction is the
same error this ADR was written about.** The bound first published here was
`R_pd ≤ 592 Ω`, which is the **NOMINAL** corner (3.300 V, 2200 Ω exactly, R_pd at
0 % tolerance) — sitting as the one-line takeaway of an ADR whose entire argument
is worst-case, and directly above a row that correctly quotes the rail ceiling.
Re-solved at the corner the rest of the section uses (rail **3.399 V**, injection
**2178 Ω** = 2.2 kΩ −1 %, R_pd **+1 %**):

| corner | bound on R_pd |
|---|---|
| nominal 3.300 V / 2200 Ω / ±0 % — **what 592 Ω was** | 592.3 Ω |
| **worst case 3.399 V / 2178 Ω / +1 % — the governing bound** | **559.3 Ω** |

**Why a 33 Ω error mattered.** 470 Ω is unaffected (+91.7 mV, unchanged), so the
board is not wrong — but **560 Ω is the next standard value a future pass reaches
for under a 592 Ω ceiling, and at the worst-case corner it produces 0.7007 V and
FAILS by 0.7 mV.** The published bound permitted exactly one value, and that value
does not clear. Re-derived: 549 Ω passes by 10.3 mV, 511 Ω by 48.9 mV, 499 Ω by
61.3 mV. **A bound stated at a corner the decision does not use is a remedy copied
without re-deriving it — the failure mode this ADR names in its own title.**

Also reconciled while re-deriving: the 680 Ω row's **0.791 V** is toleranced
resistors against a NOMINAL 3.300 V rail. At the same 3.399 V ceiling the row
above and below both use, 680 Ω gives **0.8149 V — FAIL by 115 mV, not 91 mV.**
The conclusion is unchanged and strictly stronger; the 91 mV figure quoted
elsewhere in this tree is the nominal-rail number and should be read as a floor.

Cost, measured (the CURRENT corner is R_pd LOW, 470 Ω −1 % = 465.3 Ω, the
opposite corner from the voltage bound above — both are used deliberately):
3.399/465.3 =
**7.31 mA** and **24.8 mW** in a 62.5 mW 0402 (40%), per input, ×2 = 14.6 mA on
3V3. **Bonus that was not designed for**: 7 mA is an order of magnitude above the
~1 mA dry-circuit threshold, so the reed and the E-stop contact now get real
wetting current instead of a microamp trickle through 10 kΩ.

`R_DOORS`/`R_ESTOPS` = 680 Ω on the EXISTING `C137948` line. **They contribute
ZERO to the rejection arithmetic** — the HC14 input draws no DC, so the series
element drops zero volts, which is ADR-0018's own trick and is stated here
because a reader who assumes the series resistor does the rejecting will size the
pull-down wrong next time. Their job is the other half of ADR-0018 decision D:
keep the field pin off the logic pin, and limit current into the HC14's own input
clamp (abs max ±20 mA, SCLS085L §5.1) after `D_DOOR` has clamped — the
PESD5V0S1BA's clamping voltage is far above the HC14's V_CC+0.5 V input abs-max,
so without a series element the ESD device protects the connector and not the
receiver.

`C25117` = 0402WGF4700TCE, 470 Ω ±1%, **BASE library, stock 1 834 632** (live
catalog read 2026-07-29) — the same UNI-ROYAL `0402WGF…TCE` family the board
already carries, so no new feeder class.

### Why the PULL-DOWN polarity is kept — derived, not inherited

The tempting "industrial" answer is a pull-UP with the contact to GND. **It is
wrong here, and the reason is the pod's GND pin.** A cross-mated pod always lands
its GND pin — a ZERO-ohm sink — on one of these pins.

- **Pull-DOWN reference:** the pod's GND pin drives the node to the RESTRICTIVE
  level, and only its finite-impedance signal pins can push permissive — which
  attenuation CAN defend. This is the design.
- **Pull-UP reference:** the pod's GND pin drives the node to the PERMISSIVE
  level through zero ohms, and ADR-0018's own closing sentence already says no
  resistor defends a zero-ohm source. Re-homing the sense to pin 2 does not help
  — every pin the pod's GND can reach is a pin it can short.

The pull-down is not a convention on this board; it is load-bearing.

### Why `MODE_RAW` is EXCLUDED from decision B, with its residual named

`MODE_RAW` is the third field-fed input on `U_SCHM` and it keeps its 10 kΩ. It is
on `J_MODE`, whose cross-plug path ADR-0018 decision C removed MECHANICALLY, so
attenuation there would buy nothing and cost 7 mA. Fitting it anyway "for
symmetry" would be a remedy copied without re-deriving whether it applies — the
same error, mirrored.

**RESIDUAL, named rather than quietly carried:** `MODE_RAW` has **no ESD device
at all**, while `DOOR_RAW`, `ESTOP_RAW` and `COIL_EN_IN` each have one. It is not
fixed in this revision because the `J_MODE` front-end strip is 2.475 mm wide and
fully spoken for (floorplan.yaml, "J_MODE FRONT END"), so adding parts there is a
placement pass in the most saturated corner of the board — and this revision's
placement budget is owed to the label-ownership blocker. Carried as an owed item,
with its cost stated.

## What this does NOT do — stated, because ADR-0018's withdrawn claim is the precedent

1. **`J_DOOR` ↔ `J_ESTOP` transposition is NOT closed.** Same part, same plug,
   0.090 mm courtyard gap, and both harnesses are electrically identical 2-wire
   dry contacts on pins 1–2, so a swapped pair mates perfectly and looks right.
   Traced: `ESTOP_OK` feeds `U_AND1.6` **and** `U_FAULTAND.3` (the latch SET);
   `DOOR_OK` feeds only `U_OSCLR.1`. Swapped, an E-stop press holds the PRESS
   one-shot cleared and pole B still breaks the isolated loop at `J_ISOLOOP`, so
   the contactor still opens — **but `ESTOP_OK` stays high, no fault latches, and
   the coil rail stays up**: release the button and everything resumes with no
   deliberate re-arm. It is a loss of the LATCHING property, not a defeat of the
   stop. **The remedy is a mechanical key, i.e. ADR-0018 decision C applied
   again, and it is a part change plus an east-column repack — not silk and not a
   resistor.** Recorded as the open blocker it is.
2. **A hard short of `DOOR_RAW_IN` to 3V3 still reads the door closed.** No
   resistor value defends a zero-ohm source. Decision A is what makes the
   realistic case unreachable; decision B bounds the mis-built-harness case.
3. **The door is still UNSUPERVISED.** A jumper across the reed reads "closed"
   undetectably. Full EOL supervision needs three distinguishable levels, i.e.
   an analog read, and all 8 MCP3208 channels and all 4 comparator channels are
   used. Unchanged by this ADR; removing pin 4 from `DOOR_RAW` does not make it
   worse, and the "pins 2 and 4 are one net" obstruction the v1.7 topology lens
   named is gone.

## The checks this emits — and the one it CANNOT emit, measured

**LANDED (E-INV):**

- `pin_on_net` on **all 20 pins of the four `C189896` housings**. This is the
  structural property decision A rests on, and it is the assert that would have
  caught the original defect: `J_DOOR.4` = `GND`, not `DOOR_RAW`.
- `pin_on_net` `J_DOOR.2` = `DOOR_RAW_IN`, `J_ESTOP.2` = `ESTOP_RAW_IN` — the
  connector pin is on the INPUT side of the series element, never on the logic
  pin (the ADR-0018 form).
- `part_value` `R_DOORPD` = `470`, `R_ESTOPPD` = `470` — the numbers the whole
  rejection bound is computed from. A silent decade change would move a published
  safety figure while every existence assert stayed green; that is exactly how
  `R_WDPETPD` and `R_OPENT` were nearly shipped wrong.
- `part_value` `R_DOORS` = `680`, `R_ESTOPS` = `680`.
- `part_value` `R_SDAA`/`R_SCLA`/`R_SDAB`/`R_SCLB` = `2.2k` — **not an I2C
  assert.** 2.2 kΩ is the declared worst-case injection value in both this ADR's
  table and ADR-0018's, so it is a SAFETY number and it must not drift silently.
- `net_has_part` `DOOR_RAW_IN`/`ESTOP_RAW_IN` diode ≥ 1 — the ESD device is on
  the connector side of the series element, where it can do its job.

**NOT LANDED, AND THE REASON IS A CHECKER GAP, NOT A DESIGN DOUBT.** The natural
assert is `node_level`: "with a 2.2 kΩ pull-up injected at `J_DOOR.2`, the node
reads logic-LOW at `U_SCHM.11`". `electrical_invariants.py` cannot express it,
and the reason was established by reading the checker rather than by guessing:

- `driver_state: contended` computes `V = vsup · rd/(ra + rd)` from
  `r_on_ohm_max` on the aggressor and defender PINS, resolved through
  `_load_part_electrical()`, which joins a dossier to a component by **LCSC code
  or MPN taken from the netlist `value` field**. On this pipeline a RESISTOR's
  netlist `value` is its RESISTANCE (`"10kΩ"`, verified in
  `06_build/netlists/cooksense.net`), never a code — so **no resistor dossier can
  ever resolve**, and neither the injected pull-up nor the pull-down can be named
  as aggressor or defender.
- `driver_state: released` computes the divider by walking `_resistive_path()`
  from the net to a **declared supply rail**. A correctly designed pull-down-only
  safety input has NO on-board resistive path to any rail — and must not have
  one — so the grade comes back UNREACHED.

Three ways to force it were considered and **rejected as worse than the gap**:
(a) fitting a real 2.2 kΩ pull-up to 3V3 on `DOOR_RAW_IN` so the divider becomes
on-board — this materialises the worst case but converts an open `R_DOORPD` from
"indeterminate" into "**definitely permissive**", i.e. it degrades the design to
make a gate gradable; (b) declaring `r_on_ohm_max` on a resistor dossier equal to
its own resistance — duplicates a design value into a part fact, which is the
`R_WDPETPD` failure mode; (c) declaring the pull-down's resistance on the
CONNECTOR's dossier — the same, with the value even further from its source.

**OWED SKILL PATCH (reported, not applied — a sibling is live in `skills/`):**
`node_level` needs an explicit off-board form, e.g.

    driver_state: injected
    injected: {at_pin: J_DOOR.2, through_ohm: 2200, from_rail: 3V3}

so a cross-plug worst case becomes a first-class grade. This is the same shape as
the already-recorded `P-ADJ` patch ("needs a per-INSTANCE budget form"): the
schema is one field short of being able to state the truth. Until it exists, the
arithmetic in this ADR is held by `part_value` on every term of it plus
`pin_on_net` on the structure — which is strictly more than a comment, and is
honestly less than the outcome assert ADR-0007 asks for.

---

# ADDENDUM 2026-07-29 — the SCOPE under this ADR shrank. What survives, and what
# is now MOOT. (Append-only: nothing above is edited. See ADR-0025.)

**USER DECISION, 2026-07-29: neither `J_DOOR` nor `J_ESTOP` is installed in this
build.** No access to those signals. Two of the four cross-mateable `C189896`
housings therefore leave the assembly, and this ADR's premise — a pod harness
being cross-plugged into a door or E-stop connector — has no housing to happen
in. The consequence is worked in **ADR-0025**, which is `proposed` and awaiting a
user decision; this addendum records only what happens to THIS ADR's claims. A
superseded reason is evidence, so nothing here is deleted.

## STILL TRUE, and load-bearing

- **Decision A (`J_DOOR.4` = GND) stands on its own merits.** It removed a real
  path AND removed the "pins 2 and 4 are one net" obstruction that made door EOL
  supervision unimplementable (v1.7 topology P1). Neither depends on cross-plug.
- **`R_DOORPD` / `R_ESTOPPD` = 470 Ω stands, and is now load-bearing for a
  DIFFERENT reason than it was chosen for.** With the connector body absent it is
  the ONLY thing holding the node: measured in ADR-0025,
  `V ≤ (1 µA × 470 Ω) + (1 µA × 680 Ω) = 1.15 mV` against V_T−(min) 0.500 V. A
  floating HC14 input would be indeterminate and self-oscillating. **These two
  resistors must survive every option in ADR-0025.**
- **The corrected worst-case bound `R_pd ≤ 559.3 Ω` stands** (and the 592 Ω
  nominal-corner figure remains withdrawn, with the reason: **560 Ω, the only
  standard value under 592 Ω, gives 0.7007 V and FAILS by 0.7 mV**). 470 Ω is
  unaffected at +91.7 mV. This correction must survive with the ADR because it
  governs any FUTURE fitted harness, and because the error it records — a bound
  quoted at a corner the decision does not use — is the failure this ADR is named
  after.
- **The pull-DOWN polarity derivation stands.** It is about what a zero-ohm sink
  can reach, and applies to any harness ever fitted here.
- **The `MODE_RAW` exclusion and its named residual stand.** `J_MODE` IS
  installed; ADR-0018's mechanical key and the "no ESD device on `MODE_RAW`" owed
  item are unaffected by this scope change.

## NOW MOOT — not wrong, unreachable

- **The 12-ordered-pair cross-plug enumeration collapses to 2** (the two pod
  housings against each other). Every row of the matrix that names `J_DOOR` or
  `J_ESTOP` is unreachable, including the door/E-stop-harness-into-`J_RH_*` rows,
  because those harnesses do not exist in this build.
- **"What this does NOT do" #1 — the `J_DOOR` ↔ `J_ESTOP` transposition — is
  CLOSED BY SCOPE.** With no housings fitted there is nothing to swap. The
  mechanical key it called for (ADR-0018 decision C applied again) is **NOT to be
  pursued**, and neither is the ZH-3 (`C72591`) / SH-3 (`C160403`) sourcing spike
  recorded in `01_docs/learnings/label_ownership_se_corner.md` — that data is
  retained as a measured spike, not as an open action.
- **"What this does NOT do" #2 and #3** (a hard 3V3 short reads the door closed;
  the door is unsupervised) are unreachable for the same reason.
- **Decision B's `R_DOORS` / `R_ESTOPS` = 680 Ω lose both of their stated jobs**
  — keeping the field pin off the logic pin, and limiting current into the HC14
  input clamp after `D_DOOR` clamps — because both are about a field harness. So
  are `D_DOOR` / `D_ESTOP`. They are removable under ADR-0025's O4+O5 and must be
  KEPT under O2. **Warning, measured: marking them not-assembled does NOT free
  their silk slot** — `fix_silk_placement.py` has no population awareness — so
  DNP does not fix the stage-1b `FATAL: no clear silk position for ['R_DOORPD']`.
  See ADR-0025 "Correction 1".
- **The owed `node_level: injected` skill patch is no longer needed FOR THIS
  BOARD**, since there is no injection path. It remains owed as a general
  checker-schema gap and is reported, not withdrawn.

## And one thing this ADR got blamed for that it did not cause alone

The stage-1b silk FATAL was traced to this ADR putting `R_DOORS`/`R_ESTOPS` into
the floorplan pocket `x[189.6, 193.7] y[73.2, 79.3]` that `floorplan.yaml:365`
calls *"4.1 x 6.1mm and holding nothing"*. Re-measured on the sealed v1.6 board:
that pocket already contained **`J_ESTOP`'s designator** (x[187.978, 192.022]
y[77.266, 78.494]) **and `J_DOOR`'s** (x[189.149, 192.851] y[75.146, 76.374]),
before this ADR added anything. The pocket was never empty; the comment measured
courtyards and the occupancy was on silk. ADR-0024 landed two 0402s in a slot
that was already triple-booked.
