# ADR-0025 — the DOOR CHANNEL IS DELETED, `J_ESTOP` stays POPULATED behind a
# REMOVABLE SHORTING PLUG, and the plug's housing is KEYED because the plug is
# itself a new hazard

status: **accepted**
date: 2026-07-29
tags: scope, safety, connectors, topology, brief-amendment
extends: ADR-0019 (restrictive defaults), ADR-0024 (pod-mateable inputs)
relates: ADR-0011 (safety-chain corrections), ADR-0018 (J_MODE keying), ADR-0013
amends: `01_docs/BRIEF.md` §3 / §11 / §12 — see **The brief amendment**, below.

## Context

### The scope fact, corrected

An earlier pass described this board as driving a mains contactor. **It does
not.** The brief's own scope line is a PROHIBITION list:

> Research prototype: no custom board may connect to the magnetron, HV circuit,
> convection-heater power, fan mains, OEM door interlocks, OEM thermal cutoffs,
> or internal mains.

`cooksense` is a **keypad-emulation system**: 18 buttons on a confirmed 6×3
matrix off the membrane tail, pressed by reed relays, **with the OEM controller
and the OEM safety systems left in control.** The one thing the board asserts
about itself physically is that the keypad contact domain is isolated from SELV
logic — which is why the `keypad_isolation_6mm` DRU repair landed in the same
pass as this ADR and is the higher-ranked defect of the two.

Note what the prohibition list already implies: **`J_DOOR` could never have been
fed from an OEM door interlock.** Any door signal was always going to be a
custom sensor the researcher adds. `J_ESTOP` was always going to be a
user-supplied button.

### The user decision, 2026-07-29

The user has **no access to the appliance's door signal and no access to an
E-stop signal**, and no expectation of obtaining a door signal. The resolution is
a **hybrid** of the options this ADR costed while `proposed`, and it is
deliberately ASYMMETRIC between the two connectors:

- **`J_DOOR` is REMOVED ENTIRELY** — from the netlist, not marked
  not-assembled. `DOOR_OK` leaves the logic. **That is a brief amendment and it
  is written out in full below rather than done silently.**
- **`J_ESTOP` STAYS POPULATED**, satisfied by a **removable shorting plug**, and
  `ESTOP_OK` STAYS. The point is REVERSIBILITY: if a real E-stop is obtained
  later it is fitted in place of the plug, with no copper revision.

The asymmetry is the design, not a split of the difference. The two connectors
differ in exactly one respect that matters: **one of them might one day have a
real signal, and the other will not.**

## THE MEASUREMENT that governed everything: what the two inputs read UNFITTED

Derived from `06_build/netlists/cooksense.net` — the netlist, not the intent.
Measured and not assumed, because the two possible answers need OPPOSITE
responses: RESTRICTIVE means the board is inert (safe, non-functional);
PERMISSIVE would mean unfitted safety inputs are silently satisfied, a NEW defect
worse than the one being removed.

### The front end is a NON-INVERTING buffer, not an inverter

`U_SCHM` is an **SN74HC14** (`C6820`, hex Schmitt INVERTER) and each field input
passes through **TWO cascaded stages**, so polarity is preserved:

| input | stage 1 | intermediate | stage 2 | output |
|---|---|---|---|---|
| `ESTOP_RAW` | `.1` (1A) | `ESTOP_NI` `.2`→`.3` | (2A→2Y) | **`ESTOP_OK` `.4`** |
| `MODE_RAW` | `.5` (3A) | `MODE_NI` `.6`→`.9` | (4A→4Y) | `MODE_AUTO_HW` `.8` |
| `DOOR_RAW` | `.11` (5A) | `DOOR_NI` `.10`→`.13` | (6A→6Y) | **`DOOR_OK` `.12`** |

**A single-inverter reading would have flipped the answer to PERMISSIVE. It is
two.** That subtlety decided the safe branch, and it is the one fact here most
likely to be re-derived wrongly by a reader in a hurry.

### The unfitted node voltage

With the connector body absent, `ESTOP_RAW_IN` carries only `R_ESTOPPD` 470 Ω to
GND and `D_ESTOP` (`PESD5V0S1BA`, reverse leakage ≤ 1 µA), and `R_ESTOPS` 680 Ω
carries only the HC14 input current (I_I ≤ ±1 µA, SCLS085L §6.5):

    V(ESTOP_RAW) ≤ (1 µA × 470 Ω) + (1 µA × 680 Ω) = 0.470 mV + 0.680 mV
                 = **1.15 mV**, against V_T−(min) 0.500 V at V_CC = 2.0 V

`DOOR_RAW` was identical. Both were LOW by a margin of ~435×. **The pull-downs
are what make this true and they must not be removed.**

    ⇒ ESTOP_OK = LOW      ⇒ DOOR_OK = LOW      **RESTRICTIVE, both.**

### What LOW propagates to — traced, three independent stops

    KEY_RELAY_ALLOWED = U_AND3(AND1, AND2, FAULT_LATCH_CLEAR)          (C22046)
      AND1            = U_AND1(MODE_AUTO_HW, WD_OK, ESTOP_OK)          (C22046)
      AND2            = U_AND2(TEMP_OK, MCU_RELAY_ENABLE, HOST_AUTH)   (C22046)
    FAULT_SET_N       = U_FAULTAND(WD_OK, ESTOP_OK, TEMP_OK)           (C22046)
      FAULT           = U_LATCHA NAND(FAULT_SET_N, FAULT_LATCH_CLEAR)  (C8185)
      FAULT_LATCH_CLEAR = U_LATCHB NAND(REARM_PULSE_N, FAULT)          (C8185)
    OS_CLR_N          = U_OSCLR(DOOR_OK, STOP_REQ_N, 3V3)              (C22046)
                        → U_ONESHOT.3 = R1_N, active-low reset        (C133954)

1. **`ESTOP_OK` LOW ⇒ `AND1` LOW ⇒ `KEY_RELAY_ALLOWED` LOW.** The key-relay rail
   is never authorised.
2. **`ESTOP_OK` LOW ⇒ `FAULT_SET_N` LOW ⇒ the NAND SR latch sets `FAULT` and
   holds `FAULT_LATCH_CLEAR` LOW.** The set input is CONTINUOUSLY asserted, so no
   `REARM_PULSE_N` can ever clear it. That drives `U_AND3` pin 6 LOW as well — a
   SECOND, independent term of the same AND.
3. **`DOOR_OK` LOW ⇒ `OS_CLR_N` LOW ⇒ `U_ONESHOT` R1_N held asserted.** The PRESS
   one-shot is permanently in reset, so `PRESS_TIMED` can never rise and
   `U_ULNB.3` never drives a key relay.

**VERDICT: the board was RESTRICTIVE, not permissive — provably, permanently
INERT, and LOUD rather than silent** (`FAULT` readable at `TP_FAULT` and through
`R_FAULTSER` to the expander). Safe, and completely non-functional. That is what
needed resolving.

### The correction this measurement forces on the option set

`DOOR_OK` was **NEVER a term of `KEY_RELAY_ALLOWED`.** The brief's normative
chain (`BRIEF.md`:82) is

    KEY_RELAY_ALLOWED = MODE_AUTO_HW AND WD_OK AND ESTOP_OK AND TEMP_OK
                        AND MCU_RELAY_ENABLE AND HOST_AUTH_OK AND FAULT_LATCH_CLEAR

and contains no door term. `DOOR_OK` fed **exactly one gate input, `U_OSCLR.1`**,
plus `R_DOOROKPD` and `R_DOOROKSER`→GPB3 telemetry. The framing handed to this
pass said "`DOOR_OK` leaves the `KEY_RELAY_ALLOWED` chain"; **it was not in it.**
The electrical footprint of removing the door is therefore ONE AND input, and the
brief amendment is correspondingly narrow. Stated because it changes the size of
the change: this is not surgery on the seven-term chain.

## The honest framing, stated rather than assumed — and it is MADE, not used

An E-stop on a button-presser, with the OEM controller and OEM safety systems in
control, **may not be a safety barrier at all.** The board's only actuator is a
reed relay across a membrane keypad contact; the OEM STOP/CLEAR key, the OEM door
interlock and the OEM thermal cutoffs are all still in the loop and all outside
this board. On that reading, `ESTOP_OK` and `DOOR_OK` are *interlocks on a
keystroke*, and the appliance's real safety chain is untouched by them.

**The argument is made here so it can be examined. It is NOT used as licence to
delete a term.** Where it lands, term by term:

- **It does NOT justify deleting `ESTOP_OK`, and `ESTOP_OK` is not deleted.** An
  E-stop that stops the *board* from issuing further keystrokes is a real if
  narrow property, and it is the ONLY fast way to stop an autonomous agent from
  continuing to poke buttons on a running appliance. That is worth a connector.
  On this revision `ESTOP_OK` gains authority rather than losing it (D2).
- **It is not what justifies deleting `DOOR_OK` either.** What justifies that is
  simpler and needs no framing: **there is no door signal and there never will
  be one.** A permission with no possible source is not a weakened barrier, it is
  a constant — and this board measured it as permanently DENIED. The door term was
  not protecting anything; it was preventing everything.
- **What the framing DOES buy is the right to stop treating the door's removal as
  a safety loss.** The appliance's real door interlock is the OEM one, it is
  untouched, and the brief forbids this board from going near it. A custom reed
  would have duplicated, at lower integrity, a barrier the OEM already enforces.
  Deleting it removes a *pretence* of a barrier, not a barrier.

**The load-bearing distinction: the door term goes because it has no source; the
E-stop term stays because it has one — a plug today and possibly a real button
tomorrow. Neither decision rests on the framing.**

## Decision

### D1 — `J_DOOR` and its whole front end are REMOVED FROM THE NETLIST

Out: `J_DOOR`, `R_DOORPD`, `R_DOORS`, `D_DOOR`, `R_DOOROKPD`. Nets
`DOOR_RAW_IN`, `DOOR_RAW`, `DOOR_NI`, `DOOR_OK`, `DOOR_OK_EXP` cease to exist.

**Removal and not DNP, and the reason is MEASURED.**
`03_src/cooksense/fix_silk_placement.py` contains no reference to `dnp`,
`exclude_from_bom`, or any population field (grepped). A part marked
not-assembled still has a footprint and still gets a designator placed.
**Marking these parts DNP changes the BOM and the CPL and leaves the stage-1b
`FATAL: no clear silk position for ['R_DOORPD']` exactly where it is.** Only
netlist removal frees the SE pocket.

### D2 — the freed AND input takes a REAL TERM: `OS_CLR_N = ESTOP_OK · STOP_REQ_N`

`U_OSCLR.1` was `DOOR_OK`. It is now `ESTOP_OK`. Three reasons, in order:

1. **It is what the brief already commissions and the board did not have.**
   `BRIEF.md`:89 — "E-stop: external mushroom, two NC contacts — A monitored **+
   hardware key-relay inhibit**". Until now `ESTOP_OK` gated the coil RAIL
   (`U_AND1.6`) and SET the fault latch (`U_FAULTAND.3`) but **could not clear an
   in-flight PRESS pulse.** Now it can. Brief conformance goes UP on this pass.
2. **The fail direction is preserved exactly.** Stop (3) above — `OS_CLR_N` LOW ⇒
   `U_ONESHOT` R1_N held asserted — still exists, same polarity, from the same
   470 Ω pull-down. **Removing the door channel removes no stop.**
3. **It avoids the move this ADR rejected.** Tying a freed safety AND input to
   `3V3` at the gate is O4′, which is O3 relocated (see Options). **There is no
   permissive tie-off anywhere in this change.**

**The cost, stated:** the three stops now share ONE root, `U_SCHM` stages 1–2.
The diversity `DOOR_OK` provided is gone. That is unavoidable — there is one
field permission left — and the fault-latch stop remains logically independent of
the one-shot stop downstream of that root. A dead `U_SCHM` is covered by
`R_ESTOPOKPD` (ADR-0019), which is now load-bearing for a **fourth** consumer.

### D3 — `U_SCHM` stages 5 and 6 become SPARE: inputs TIED, outputs OPEN

`pin11` (5A) and `pin13` (6A) → GND; `pin10` (5Y) and `pin12` (6Y) omitted from
the connections map. Per SCLS085L / SCEA043 an unused HC input must be tied to a
rail (a floating one self-oscillates and draws supply current) and an unused
output must not be. **GND rather than 3V3** for a reason beyond convention: on
the two live stages of this same part LOW is the RESTRICTIVE level, so a future
edit that re-uses the stage inherits the safe default. Precedent for omitting an
unused output pin: `U_ONESHOT` pin5 (Q2), already on this board. The netlist
exports both as explicit NO-CONNECTs.

### D4 — `R_DOOROKSER` is RENAMED `R_GPB3PD` and REPOINTED, not deleted

GPB3's readback net is gone, so the pin is spare — which is exactly where
ADR-0020's lesson gets applied a seventh time. Left **open** it is a floating
CMOS input with an indeterminate readback, on a board whose entire ADR-0019
premise is that permission-adjacent pins have deterministic levels. **Hard-tied**
to GND it is a 25 mA bidirectional I/O one I2C write (`IODIRB.3=0, OLATB.3=1`)
away from driving into a dead short. Through the **same 10 kΩ on the same
`C60490` line** it is a deterministic 0 with the mis-write limited to 330 µA.

### D5 — `J_ESTOP` MOVES FROM JST GH-5 TO JST SH-3, AND THE PLUG IS WHY

`J_ESTOP` becomes **`SM03B-SRSS-TB` / `C160403`** (genuine JST; LCSC stockCount
**52 323** read live 2026-07-29; KiCad footprint ships in-tree;
`escape_check --style connector --pitch 1.0` passes on **all five tiers**, floor
`jlc_2layer_default`, measured 2026-07-29 — the GH/ZH precedents were 1.25 and
1.50 mm and did **not** cover 1.00 mm).

**Pinout: 1 = GND, 2 = 3V3, 3 = `ESTOP_RAW_IN`. The shorting plug bridges 2–3.**

#### D5a — the question that had to be answered FIRST, because it could have invalidated the plan

**Does a real E-stop harness need FOUR circuits?** `BRIEF.md`:89 asks for a
"4-pin locking connector". If it does, keying to a 3-circuit housing forecloses
the very reversibility that justifies keeping `J_ESTOP` at all, and the plan is
self-defeating.

**It does not, and the reason is already in this board's history.** The brief's 4
pins existed because contact B was originally on the same housing. **v1.3 P0-2
moved contact B off permanently** — until v1.2 `J_ESTOP` carried `ESTOP_RAW`
(SELV) on pin 2 and `CONTACTOR_C` (isolated secondary) on pin 3, **adjacent pads
on a 1.25 mm-pitch GH, 0.650 mm apart, in ONE field harness**, which reduced the
LTV-817S's 5 kV barrier to 0.65 mm at the connector and made a single
contaminated harness a common-cause failure across the isolation boundary. The
brief itself says contact B "interrupts the external contactor loop **outside
Board A**". A real mushroom E-stop therefore wires **contact A to `J_ESTOP` 2–3
and contact B to `J_ISOLOOP`'s screw terminals** — *exactly* the harness split
the board has had since v1.3. The surviving GH-5 used only 3 of its 5 circuits
(3V3, sense, GND ×3).

**3 circuits is the FULL requirement, not a compromise.** A 4-circuit SH was
checked rather than assumed and **exists**: `SM04B-SRSS-TB` / **`C160404`, stock
17 438**, footprint in-tree, same 1.00 mm pitch and therefore the same keying. It
is rejected only because the 4th circuit has nothing to carry and costs 1.000 mm
of a 1.198 mm east-column slack budget. **The trade is recorded so a future
revision can take it in one line if a harness ever wants a shield conductor.**

#### D5b — the second question: does keeping `J_ESTOP` POPULATED reopen the cross-plug path?

**Yes — and worse than "reopen". The plug creates a hazard the board never had,
and this measurement is what decided the housing.**

With `J_DOOR` gone the 1.25 mm GH family is `J_RH_AMBIENT`(5), `J_RH_EXHAUST`(5),
`J_THERM_A`(8), `J_THERM_B`(8), `J_KEY_MATRIX`(10). Had `J_ESTOP` stayed GH-5,
**its shorting plug — a small anonymous 2-wire bridge living loose on the board —
could be fitted into all four sensor-pod housings, where pin 1 is a SWITCHED 3V3
SENSOR RAIL and pin 2 is GND. A 1–2 bridge there is a DEAD SHORT whose only limit
is an AO3401A's R_DS(on).** The object that exists purely to satisfy a safety
input would have become the board's most damaging single mis-plug. ADR-0024's
argument — J_ESTOP is safe against a pod cross-plug *because* pins 3/4/5 are GND
— says nothing about this direction: **it is the plug that travels, not the pod.**

#### D5c — the keying, measured in BOTH directions

**INTO `J_ESTOP` — hard interference; nothing on this board can enter it.** The
SH-3 side-entry shroud is B = 5.0 mm wide × 2.9 mm tall (eSH p.3,
`SM03B-SRSS-TB` A=2.0 B=5.0):

| plug | size (vendor drawing) | vs the 5.0 × 2.9 cavity | verdict |
|---|---|---|---|
| `GHR-05V-S` | 7.50 × 4.15 (eGH p.2) | −2.50 W, −1.25 H | **BLOCKED** |
| `ZHR-4` (= `J_MODE`) | 7.50 × 3.40 (eZH p.2) | −2.50 W, −0.50 H | **BLOCKED** |
| `GHR-08V-S` / `GHR-10V-S` | wider still | — | **BLOCKED** |
| `XHP-5` (`J_LOADCELL`) | 2.50 mm pitch, far larger | — | **BLOCKED** |

**OUT OF `J_ESTOP` — bounded by PITCH OFFSET, not by latching.** An
`SHR-03V-S-B` plug is 6.0 × 2.8 mm (eSH p.2) and **CAN** be pushed loosely into a
GH or ZH shroud. It cannot latch — but "cannot latch" is not a safety claim, so
the claim has to rest on contact alignment:

| foreign family | posts at | vs SH circuits 0 / 1.0 / 2.0 → offsets |
|---|---|---|
| GH 1.25 mm | 0 / 1.25 / 2.50 / … | **0 / 0.25 / 0.50** |
| ZH 1.50 mm | 0 / 1.50 / 3.00 / … | **0 / 0.50 / 1.00** |

**Circuit 3 is ≥ 0.50 mm off every post in every foreign family, against a
~0.30 mm post. It is the one circuit that can never engage anywhere else — so the
sense node lives on circuit 3 and the plug bridges 2–3, and the short CANNOT BE
COMPLETED in any other housing on this board.** Had the sense been on circuit 1
with a 1–2 bridge, that is precisely the 0 / 0.25 mm pair — the pair that MIGHT
engage, and the rail-to-GND pair of D5b. Belt and braces: even if 2–3 *did*
engage a GH-5 pod, posts 2/3 there are GND and `SDA_*` — a stuck bus,
recoverable, not a rail short. **GND on circuit 1 is also deliberate: circuit 1 is
the circuit MOST likely to engage in a foreign shroud, and a ground landing is
the restrictive outcome in every cell.**

#### D5d — the full cross-mate matrix, re-run against every remaining housing

Pitch census of the board after this revision; every LCSC figure a live catalog
read, 2026-07-29:

| housing | part | LCSC | pitch | ckts | family size |
|---|---|---|---|---|---|
| `J_ESTOP` | SM03B-SRSS-TB | C160403 | **1.00** | 3 | **1 — UNIQUE** |
| `J_RH_AMBIENT`, `J_RH_EXHAUST` | SM05B-GHS-TB | C189896 | 1.25 | 5 | 5 (GH) |
| `J_THERM_A`, `J_THERM_B` | SM08B-GHS-TB | C265111 | 1.25 | 8 | 5 (GH) |
| `J_KEY_MATRIX` | SM10B-GHS-TB | C2683602 | 1.25 | 10 | 5 (GH) |
| `J_MODE` | S4B-ZR-SM4A-TF | C485354 | 1.50 | 4 | 1 |
| `J_LOADCELL` | B5B-XH-A | C157991 | 2.50 | 5 | 1 |
| `J_PWR` | 43650-0224 | C587657 | 3.00 | 2 | 1 |
| `J_ISOLOOP` | KF350-3.5-4P | — | 3.50 screw | 4 | 1, not pluggable |
| `J_PI` | 2×20 header | C35165 | 2.54 | 40 | 1 |
| `J_TC` | PCC-SMP-K | — | thermocouple jack | 2 | 1 |
| `CN1` (interposer) | 10FDZ-BT | — | ZIF flex | 10 | 1 |

**1.00 mm appears exactly once on this board.** The residual cross-mateable
family is the five GH housings — and after this revision **not one of them is a
safety input**: four sensor pods plus the keypad ribbon. Swapping `J_RH_AMBIENT`
↔ `J_RH_EXHAUST` remains possible and remains a *data-labelling* error (identical
pinout structure, both switched rails); a GH-5 pod plug part-seated in a GH-8 or
GH-10 shroud is the pre-existing residual ADR-0024 already covers. **Zero cells
in which a cross-plug reaches a permission.**

#### D5e — the shorting plug is BUILDABLE, and the objection that demoted SH does not apply to it

- housing: `SHR-03V-S-B` / `C268100` — **LCSC stock 0**. Stocked SH-compatible
  equivalents: `HDGC1002H-3P` C2909166 (2 153), `HC-1.0-3Y` C2962274 (1 625),
  `A1002H-3P` C338906 (515).
- contacts: `SSH-003T-P0.2-H` / **`C263995`, stock 167 600** (JST-genuine, listed
  for SH and APSH; `SSH-003T-P0.2` / C160231, stock 164 418, also live).
- the plug is a **~5 mm crimped bridge carrying 3.3 V / 470 Ω = 7.0 mA**, and
  7 mA is an order of magnitude above the ~1 mA dry-circuit threshold, so the
  contacts get real wetting current.

**The SH wire-gauge objection is real and it is NOT about the plug.** SH takes
AWG #32–28 at 0.4–0.8 mm insulation OD — the narrowest on this board, and the
sole reason SH ranked *second* in the original spike
(`01_docs/learnings/label_ownership_se_corner.md`). That objection was about a
metre-long **field run** to a mushroom button, where #28 is electrically trivial
at 7 mA but mechanically fragile. **It has no force against a 5 mm bridge, which
is what the board ships needing.** For a future field harness the ORDER_README
calls for an in-enclosure splice from a #28 pigtail to #24/#26 field cable.
**That is the one honest cost of the keying and it is stated rather than buried.**

### D6 — a HAZARD-CAPTION RESERVE MAY NOT EVICT ITS OWN OWNER

Adding `J_ISOLOOP` to `OWNERSHIP_FIX` (the point of D1 — see The prize) made a
latent contradiction in `fix_silk_placement.py` reachable, and the first rebuild
after the change hit it immediately:

    FATAL: no clear silk position for ['J_ISOLOOP']

PASS D0 arms a 2.6 mm hazard-caption reserve around `J_ISOLOOP` at
x[188.975, 201.825] y[85.075, 104.925] and **evicts every silk label inside it,
forbidding the band** so an evictee cannot be re-placed straight back in (that
`forbid=` is load-bearing — on v1.7 `D_DOOR` was evicted, landed 0.5 mm away
still inside, and `ISO 30V` then had no site at 11.086 mm). But the loop ran over
`sorted(fps)` **including `J_ISOLOOP` itself**, whose courtyard
x[191.555, 199.245] y[87.655, 102.345] is **WHOLLY INSIDE the reserve** — so every
position from which its designator could be nearer its own part than any other
was forbidden to it, while `need_owner` was simultaneously required.
**Unsatisfiable by construction**, and the pass reported the unsatisfiability
rather than degrading, which is why the repair is one guard clause.

**The reserve's purpose is unchanged and is not weakened.** It exists so that
OTHER parts' designators cannot squat the band where the NOT-SELV hazard captions
print. `J_ISOLOOP`'s own designator is in the same class as those captions — it is
part of what identifies the 30 V terminal, and its sitting 0.141 mm from a
humidity header through five sealed releases is the defect this pass exists to
close. **Measured safe rather than assumed:** with the designator left in place at
x[192.809, 197.791] y[86.438, 87.562], all three captions still find sites —
`ISO 30V` rot 90 at x[191.45, 192.05], `NOT SELV` rot 90 at x[198.2, 198.8],
`1C2L3L4E` at y 101.0 — and none overlaps that box in x. Captions are placed in
PASS E *after* the eviction loop and go through ordinary collision avoidance, so
if a future placement change does make them collide, PASS E says so rather than
silently dropping a hazard warning.

**This is the second time in two passes that this corner produced a defect of the
same shape: a rule that cleared a region by checking the wrong occupancy.** The
floorplan cleared the SE pocket by checking COURTYARDS and missed three
designators; the reserve cleared its band by checking FOREIGNNESS and missed that
the owner is not foreign.

## What this closes, and what it costs

| closed | how |
|---|---|
| the `J_ISOLOOP` 30 V NOT-SELV label-ownership **P0** | `J_DOOR`'s courtyard leaves; `J_ISOLOOP` added to `OWNERSHIP_FIX`; D6 makes it reachable |
| the stage-**1b/7 silk FATAL** | the triple-booked SE pocket loses 3 of 4 occupants |
| the **east-column squeeze** | 0.628 mm aggregate slack → **15.153 mm** |
| the **cross-plug / transposition** class on safety inputs | no safety input is in a multi-member family any more |
| the **plug-as-hazard** that keeping `J_ESTOP` created | SH-3 keying, both directions measured (D5c) |
| an **S-COUNT gap** nothing had caught | `R_ESTOPS` and `C_EFIN` were missing from `manifest.yaml` |
| the **ISO→SELV moat's tightest term** | `J_DOOR`'s GND tab was 2.126 mm against a 2.0 mm rule, with 0.04 mm of pour reach either side; it is gone |

| cost | size |
|---|---|
| brief amendment | the "Door:" clause plus two word-level mentions (below) |
| stop diversity | 3 stops now share one root (`U_SCHM` stages 1–2) |
| a third crimp system on the harness bench | deliberate — ADR-0018 made the identical trade |
| future E-stop field harness needs a #28→#26 splice | ORDER_README step |
| `J_DOOR` is not reversible without a copper revision | accepted: there is no door signal to reverse to |

### THE PRIZE, MEASURED

`label_ownership_se_corner.md` proves all four directions out of `J_ISOLOOP`'s
courtyard were closed, and that the one candidate pocket
`x[191.555, 193.755] y[82.795, 87.155]` lost to `J_DOOR`. Re-measured at that
pocket's centre (192.655, 84.975), nearest `J*`/`F*`/`TP*` courtyard:

| footprints present | nearest | 2nd nearest | ownership margin |
|---|---|---|---|
| all (v1.7) | **`J_DOOR` 1.100 mm** | `J_ISOLOOP` 2.680 mm | J_ISOLOOP LOSES |
| `J_DOOR` removed | **`J_ISOLOOP` 2.680 mm** | `J_ESTOP` 8.769 mm | **+6.089 mm** |

`MIN_OWNERSHIP_MARGIN_MM` is 1.5. **Removing `J_DOOR` alone makes the 30 V
NOT-SELV isolated-contactor terminal's designator OWNABLE with 4× the required
margin** — the render-lens P0 declared unfixable without a part change.
`OWNERSHIP_FIX` named only `("J_DOOR","J_ESTOP","J_MODE")`, **so `J_ISOLOOP` had
to be ADDED or nothing would even try**; it now reads
`("J_ESTOP","J_ISOLOOP","J_MODE")`.

### The two corrections this ADR made to the hypothesis it was given

1. **NOT-ASSEMBLED does not free one micron of silk** (D1). The 1b/7 FATAL is a
   placement failure, not a BOM one.
2. **The "4.1 × 6.1 mm and holding nothing" pocket held THREE designators.**
   Measured on the sealed v1.6 board against `floorplan.yaml`'s own pocket
   `x[189.6, 193.7] y[73.2, 79.3]`:

   | designator silk | bbox | inside the "empty" pocket? |
   |---|---|---|
   | `J_ESTOP` | x[187.978, 192.022] y[77.266, 78.494] | **YES** |
   | `J_DOOR` | x[189.149, 192.851] y[75.146, 76.374] | **YES** |
   | `R_DOORPD` | x[189.038, 190.162] y[75.223, 80.177] | **YES** |
   | `R_ESTOPPD` | x[184.486, 185.714] y[69.906, 75.294] | no |
   | `R_STOPRAIL` | x[194.926, 199.074] y[82.539, 83.461] | no |

   **TRIPLE-BOOKED before ADR-0024 anchored two more 0402s into it.** The reusable
   finding, sharpened: **a floorplan comment that clears a region by checking
   COURTYARDS has checked the wrong layer.** Silk is a placement resource with its
   own occupancy — and D6 is the same lesson a second time.

## The brief amendment — stated in full, not implied

`01_docs/BRIEF.md` is immutable; corrections live in the decision register and in
ADRs. This ADR is the correction. **Three edits, and no more:**

1. **§3, the "Door:" clause is WITHDRAWN in full:**
   > ~~Door: external NC reed + EOL (or 3-wire Hall), 4-pin connector; open =>
   > abort sequence, release PRESS+selectors, no new START.~~

   Reason: no door signal exists or will exist. The appliance's door interlock is
   the OEM one and the brief's own scope line forbids this board from touching it.
   A custom reed would have duplicated an OEM barrier at lower integrity. **The
   ABORT BEHAVIOUR IS NOT WITHDRAWN** — `STOP_REQ_N` still clears the PRESS
   one-shot, and as of D2 so does `ESTOP_OK`.
2. **§3's input list**: "door/E-stop/Manual-Auto/arc/airflow inputs" → the word
   *door* is struck. (arc/airflow were already declared out of scope.)
3. **§12's firmware contract**: "Manual/Auto + door/E-stop enforcement" → the
   word *door* is struck.

**§11's master connector table already deviated** (`J_ESTOP` has been 5-pin GH,
not 4-pin, since v1.0) and now reads 3-pin SH per D5a; `J_DOOR 4-pin` is struck.

**NOT amended, and this is the important half: `BRIEF.md`:82's normative safety
chain is UNCHANGED, term for term.** It never contained a door term.
`BRIEF.md`:89's E-stop clause is UNCHANGED and is *better served* than before
(D2).

## Options — the full costed set, and why the hybrid won

### O1 — Leave it inert. No change. **REJECTED.**
Maximally safe, completely non-functional, fails the brief's purpose entirely.
Recorded for completeness.

### O2 — Populate BOTH connectors, close BOTH with shorting plugs. **ADOPTED for `J_ESTOP`, REJECTED for `J_DOOR`.**
Zero schematic change; fail direction stays RESTRICTIVE when a plug falls out;
reversible. **Adopted for `J_ESTOP` (D5)**, where reversibility has a subject.
**Rejected for `J_DOOR`**, where it does not: it would keep a footprint, a
courtyard, three passives and a designator on the board — and therefore keep the
`J_ISOLOOP` 30 V P0, the 1b/7 FATAL and the tight ISO moat — to preserve the
option of fitting a signal the user has said does not exist. It also keeps two
identical GH-5 housings, i.e. the transposition hazard, in exchange for nothing.

### O3 — Unpopulated connectors + on-board 0 Ω links from `3V3`. **REJECTED, and this rejection STANDS unchanged.**
Exactly the defect the scope reduction was supposed to avoid: **unfitted safety
inputs silently satisfied, on the board itself**, in a way that no longer
distinguishes "bypassed" from "sensed" and that fights any future real harness.
No resistor defends it and the fail direction becomes **PERMISSIVE**. *Do not
re-propose.*

### O4 — Remove `DOOR_OK` and `ESTOP_OK` from the logic. **ADOPTED for `DOOR_OK` only.**
Not reversible without a copper revision. Adopted for the door because there is
nothing to reverse to. **Rejected for the E-stop** on exactly that asymmetry: an
E-stop button is a thing a researcher can buy this afternoon.

  **O4′ — tie the freed AND inputs to `3V3` at the gate. REJECTED** as O3
  relocated; it inherits O3's objection. **D2 is what replaces it:** the freed
  input gets a real term, not a rail.

### O5 — Remove the FOOTPRINTS. **ADOPTED for `J_DOOR`.**
Where the measured value is. `O2 + O5` is incoherent *for the same connector*
(O5 removes the connector O2 needs) — which is precisely why the resolution is
**per-connector** rather than per-option: **O4+O5 on `J_DOOR`, O2 on `J_ESTOP`,
plus D5's keying, which no single option had.**

### O6 (new, and the plug forced it) — key `J_ESTOP` out of every family. **ADOPTED (D5).**
The `proposed` version of this ADR said "DO NOT pursue the ZH-3/SH-3 keyed
connector change — the hazard is closed by scope." **That was correct while both
connectors were unpopulated and became WRONG the moment `J_ESTOP` stayed
populated**, for the reason in D5b: with only one connector left to protect, the
*plug* becomes the travelling object. The retained sourcing spike turned out to
be the answer to a question nobody had asked yet — which is the argument for
retaining measured spikes even after their motivating hazard closes.

## Consequences

- **`R_ESTOPPD` (470 Ω) MUST SURVIVE.** It is the sole reason the unfitted state
  measures 1.15 mV instead of floating. A floating HC14 input is indeterminate
  and self-oscillating, and would void the whole measurement above. Its twin
  `R_DOORPD` went with the door; the `part_value` E-INV on the survivor now
  carries **two independent reasons** for the same number, and says so.
- **ADR-0024's 470 Ω choice and the corrected bound `R_pd ≤ 559.3 Ω` survive
  unchanged.** 560 Ω — the only standard value under the withdrawn 592 — gives
  0.7007 V and fails by 0.7 mV. The value and the bound are still what makes a
  FUTURE fitted harness safe. **A superseded reason is evidence, not litter.**
- **ADR-0024 Decision A (`J_DOOR.4` = GND) is UNREACHABLE but not retracted.** It
  removed a real path and un-blocked door EOL supervision. Its five `J_DOOR.*`
  pinout asserts are deleted with the part; the ten `J_RH_*` asserts carry the
  denominator argument forward, and the class is now closed MECHANICALLY (D5)
  rather than by a pinout rule.
- **`R_ESTOPS` / `D_ESTOP` survive** — a real E-stop harness is still a field
  cable, so the series element and the clamp still have their jobs.
- **`MODE_RAW` / `J_MODE` are untouched.** ADR-0018's mechanical key and
  ADR-0024's named residual (`MODE_RAW` has no ESD device) both stand.
- **Machine-checked, and RED-VERIFIED against the immutable sealed v1.6 netlist**
  (`07_releases/cooksense-v1.6-2026-07-27/source/cooksense.net`), the archived
  pre-fix input:
  - `rebuild_schematic.sh` stage 4/4 now carries **17 node-count asserts + 5
    MUST-NOT-EXIST asserts**. A node-count table is structurally blind to a net
    that should have been deleted, and "the door channel is gone" is the whole
    change — so `DOOR_RAW_IN`/`DOOR_RAW`/`DOOR_NI`/`DOOR_OK`/`DOOR_OK_EXP` are
    asserted NEGATIVELY. New netlist **22/22**; sealed v1.6 **5/22**, with
    `DOOR_RAW`/`DOOR_NI`/`DOOR_OK` reported as `STILL EXISTS` and `ESTOP_OK` as
    `6 nodes, expected 8`.
  - `electrical_invariants.yaml` gains **7 ADR-0025 asserts** — `U_OSCLR.1` on
    `ESTOP_OK`; `R_GPB3PD` value + both pins; all three `J_ESTOP` pins. New
    netlist **E-INV OK 167/167**; against sealed v1.6 **all 7 fail with the right
    message**, e.g. `U_OSCLR.1 is on net 'DOOR_OK', invariant requires
    'ESTOP_OK'` and `J_ESTOP.3 is on net 'GND', invariant requires
    'ESTOP_RAW_IN'`.
- **A `node_level` assert could NOT be written for the unfitted node, and that is
  a GATE LIMITATION, not a modelling choice.** `_grade_node_level`'s `released`
  branch requires a series-RESISTIVE path from the net to a declared supply rail
  in order to compute a divider; a node whose only DC path is a **pull-down to
  GND** — which is every restrictive-default node on this board, including
  `ESTOP_RAW`, `OS_CLR_N` and `GPB3_SPARE` — returns `UNREACHED`. The code already
  special-cases the mirror image ("no resistive path to GND ⇒ pulled to the
  rail"). **Reported as an owed skill patch, not patched here.** The netlist-level
  MUST-NOT-EXIST and node-count asserts are what carry this change instead, and
  they are strictly stronger for a deletion.
- **`R_ESTOPS` and `C_EFIN` were MISSING from `manifest.yaml`** — the AUTHOR's
  declared intent, the one source that catches a silent `tsci` drop.
  `count_parity.py` compares the SYMMETRIC DIFFERENCE and would have caught both;
  it had not run since ADR-0024 because the build has been dying at stage 1b/7.
  **Declared now.** Declared components 241 → **239** (−4: `J_DOOR`, `R_DOORPD`,
  `D_DOOR`, `R_DOOROKPD`; +2 previously undeclared; `R_DOORS` was never declared
  at all; `R_DOOROKSER`→`R_GPB3PD` is a rename). The header's "235 components"
  arithmetic was stale by 6 and is corrected against the entry count, which is
  ground truth.
- **Separately noted, NOT in this ADR's scope and NOT fixed here: `C265111`
  (`SM08B-GHS-TB`, `J_THERM_A`/`J_THERM_B`) reads LCSC stockCount 0 on a fresh
  read 2026-07-29.** No part was swapped. It is an A-STOCK matter for the seal
  gate and it is recorded here so the order desk does not discover it.
- **What must be re-verified on the BUILT board, not inherited:** the ISO→SELV
  copper margin (its binding neighbour is no longer `J_DOOR`'s GND tab — the ISO
  scan measures it), `fix_silk_placement`'s own RESIDUAL line for the `J_ISOLOOP`
  ownership margin, `policy_waivers` P-SILK-FN's re-stated 22-ref denominator and
  its pass-B leads, that waiver's hazard-caption rivals (measured against
  `J_DOOR`), ORDER_README §10 and §2a, and **the four-lens battery in full, run
  FRESH.**
- **ORDER_README owes a LOUD step: the board does not function without the
  shorting plug.** With `J_ESTOP` open the board is inert by design (all three
  stops assert). That is correct, and it is also indistinguishable from a dead
  board to a bring-up technician who has not read this — so it belongs in the
  build instructions, not only here.
