# ADR-0025 — `J_DOOR` and `J_ESTOP` are NOT INSTALLED, the AND chain goes
# PROVABLY INERT, and the resolution is a USER decision

status: **proposed — STOPPED FOR A USER DECISION. No copper was touched.**
date: 2026-07-29
tags: scope, safety, connectors, topology
extends: ADR-0019 (restrictive defaults), ADR-0024 (pod-mateable inputs)
relates: ADR-0011 (safety-chain corrections), ADR-0018 (J_MODE keying)

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

**Neither `J_DOOR` nor `J_ESTOP` is installed in this build.** The user has no
access to those signals.

This is a scope reduction and it cascades. Two of the four cross-mateable
`C189896` / `SM05B-GHS-TB` housings leave the board, which shrinks the whole
hazard class ADR-0024 was written about; the `J_DOOR`↔`J_ESTOP` transposition
that ADR-0024 explicitly left open becomes MOOT (nothing to cross-plug); and the
ZH-3 / SH-3 keyed-connector spike recorded in
`01_docs/learnings/label_ownership_se_corner.md` is no longer needed for that
purpose.

## THE MEASUREMENT: what `ESTOP_OK` and `DOOR_OK` actually read unfitted

Derived from `06_build/netlists/cooksense.net` — the netlist, not the intent.
This was measured and not assumed, because the two possible answers need
OPPOSITE responses: RESTRICTIVE means the board is inert (safe, non-functional);
PERMISSIVE would mean unfitted safety inputs are silently satisfied, a NEW defect
worse than the one being removed.

### The front end is a NON-INVERTING buffer, not an inverter

`U_SCHM` is an **SN74HC14** (`C6820`, hex Schmitt INVERTER) and each of the three
field inputs passes through **TWO cascaded stages**, so the polarity is preserved:

| input | stage 1 | intermediate | stage 2 | output |
|---|---|---|---|---|
| `ESTOP_RAW` | `.1` (1A) | `ESTOP_NI` `.2`→`.3` | (2A→2Y) | **`ESTOP_OK` `.4`** |
| `MODE_RAW` | `.5` (3A) | `MODE_NI` `.6`→`.9` | (4A→4Y) | `MODE_AUTO_HW` `.8` |
| `DOOR_RAW` | `.11` (5A) | `DOOR_NI` `.10`→`.13` | (6A→6Y) | **`DOOR_OK` `.12`** |

A single-inverter reading would have flipped the answer to PERMISSIVE. It is two.

### The unfitted node voltage

With the connector body absent, `DOOR_RAW_IN` carries only `R_DOORPD` 470 Ω to
GND and `D_DOOR` (`PESD5V0S1BA`, reverse leakage ≤ 1 µA), and `R_DOORS` 680 Ω
carries only the HC14 input current (I_I ≤ ±1 µA, SCLS085L §6.5):

    V(DOOR_RAW) ≤ (1 µA × 470 Ω) + (1 µA × 680 Ω) = 0.470 mV + 0.680 mV
                = **1.15 mV**, against V_T−(min) 0.500 V at V_CC = 2.0 V

`ESTOP_RAW` is identical (`R_ESTOPPD` 470 Ω, `R_ESTOPS` 680 Ω, `D_ESTOP`). Both
are LOW by a margin of ~435×. **The pull-downs are what make this true and they
must not be removed** — see Consequences.

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
2. **`ESTOP_OK` LOW ⇒ `FAULT_SET_N` LOW ⇒ the NAND SR latch sets `FAULT` HIGH and
   holds `FAULT_LATCH_CLEAR` LOW.** The set input is CONTINUOUSLY asserted, so no
   `REARM_PULSE_N` can ever clear it. That drives `U_AND3` pin 6 LOW as well —
   a SECOND, independent term of the same AND.
3. **`DOOR_OK` LOW ⇒ `OS_CLR_N` LOW ⇒ `U_ONESHOT` R1_N held asserted.** The PRESS
   one-shot is permanently in reset, so `PRESS_TIMED` can never rise and
   `U_ULNB.3` never drives a key relay.

**VERDICT: the board is RESTRICTIVE, not permissive — and it is provably,
permanently INERT. It cannot press a key, cannot energise the key-relay rail, and
sits with `FAULT` latched from power-up.** The good news inside the bad news: it
is LOUD, not silent — `FAULT` is readable at `TP_FAULT` and through `R_FAULTSER`
to the expander, so a bring-up technician sees the reason immediately.

So the outcome is the SAFE one of the two. There is no new fail-permissive
defect. But the board also does not do the one thing the brief commissions it to
do, and that needs a deliberate, documented resolution rather than a shrug.

### The honest framing, stated rather than assumed

An E-stop on a button-presser, with the OEM controller and OEM safety systems in
control, **may not be a safety barrier at all.** The board's only actuator is a
reed relay across a membrane keypad contact; the OEM STOP/CLEAR key, the OEM door
interlock and the OEM thermal cutoffs are all still in the loop and all outside
this board. On that reading, `ESTOP_OK` and `DOOR_OK` are *interlocks on a
keystroke*, and the appliance's real safety chain is untouched by them.

**That argument is stated here so it can be examined — it is NOT used as licence
to delete a term.** Against it: the brief names both permissions explicitly
(§3), ADR-0011 §3 and ADR-0019 are built on them, and an E-stop that stops the
*board* from issuing further keystrokes is a real (if narrow) property — it is
the only fast way to stop an autonomous agent from continuing to poke buttons.
Which reading governs is the user's call, not this pass's.

## Options

### O1 — Leave it inert. No change.
Board is maximally safe and completely non-functional. Zero engineering. It
fails the brief's purpose entirely. **Recorded for completeness, not viable.**

### O2 — Populate `J_DOOR` and `J_ESTOP` after all, and close them with SHORTING PLUGS.
A `GHR-05V-S` housing wired 1–2 satisfies the input; nothing else changes.
- **No schematic change, no copper change, no ADR-0024 dissolution.** The AND
  chain keeps every term the brief mandates.
- **Fail direction stays RESTRICTIVE**: plug falls out ⇒ node returns to the
  470 Ω pull-down ⇒ inert. This is the property O3 destroys.
- **The transposition hazard genuinely evaporates**: two identical housings
  carrying two identical 1–2 shorts are interchangeable, so swapping them is a
  no-op. ADR-0024's open blocker #1 closes by symmetry, not by keying.
- **Requires the user to reverse the "not installed" decision** for the
  connector bodies (not for the signals). Two `C189896` + two housings + four
  crimps.
- Cost: the two permissions become permanently satisfied by a deliberate,
  visible, removable object. That is a documented bypass, which is honest.

### O3 — Keep the connectors unpopulated and fit on-board 0 Ω links from `3V3`.
**REJECTED.** This is exactly the defect the scope reduction was supposed to
avoid: unfitted safety inputs silently satisfied, on the board itself, in a way
that no longer distinguishes "bypassed" from "sensed", and that fights any future
real harness. No resistor defends it and the fail direction becomes PERMISSIVE.

### O4 — Remove the `DOOR_OK` and `ESTOP_OK` terms from the AND chain.
The honest expression of the framing above, if the user accepts it. Cost:
- A schematic change to `U_AND1` / `U_FAULTAND` / `U_OSCLR` inputs, a re-derived
  E-INV set (`electrical_invariants.yaml` lines 228/262/389/401/746/761 all
  assert these nets), and a **brief amendment** — the chain
  `KEY_RELAY_ALLOWED = MODE_AUTO_HW AND WD_OK AND ESTOP_OK AND TEMP_OK AND
  MCU_RELAY_ENABLE AND HOST_AUTH_OK AND FAULT_LATCH_CLEAR` is normative text.
- It deletes the LATCHING property ADR-0024 traced, and the `FAULT` set path.
- It is not reversible without another copper revision.
**Cheaper variant O4′:** tie the freed AND inputs to `3V3` at the gate rather
than re-plumbing, which is O3 relocated and inherits O3's objection.

### O5 — Remove `J_DOOR` and `J_ESTOP` FOOTPRINTS from the board, and pick O2 or O4 for the logic.
Orthogonal to the logic question, and **it is where the measured value is** — see
the next section. O5 and O2 are compatible only if the signals are re-homed;
O5 + O4 is self-consistent.

## The cascade, MEASURED — and it corrects the hypothesis it was given

The working hypothesis handed to this pass was: *"if the parts are no longer
needed, the SE pocket is freed and the 1b/7 FATAL goes away at the root."* It was
to be verified before acting on. **Verified, and it is WRONG in one direction and
UNDERSTATED in another.**

### Correction 1 — NOT-ASSEMBLED does not free one micron of silk.

The stage-1b failure is `FATAL: no clear silk position for ['R_DOORPD']`. Silk is
a placement resource, and `03_src/cooksense/fix_silk_placement.py` contains **no
reference to `dnp`, `exclude_from_bom`, or any population field** (grepped). A
part marked not-assembled still has a footprint and still gets a designator
placed. **Marking `R_DOORS`/`R_ESTOPS`/`J_DOOR`/`J_ESTOP` DNP changes the BOM and
the CPL and leaves the 1b/7 FATAL exactly where it is.** Only removing them from
the netlist, or MOVING them, frees the pocket.

### Correction 2 — the "empty" pocket held TWO MORE designators than anyone counted.

Measured on the **sealed v1.6** board (`06_build/proof/keypad_iso_v18/`,
read-only copy), against the floorplan's own pocket
`x[189.6, 193.7] y[73.2, 79.3]` — commented in `floorplan.yaml:365` as
*"4.1 x 6.1mm and holding nothing"*:

| designator silk | bbox | inside the "empty" pocket? |
|---|---|---|
| `J_ESTOP` | x[187.978, 192.022] y[77.266, 78.494] | **YES** |
| `J_DOOR` | x[189.149, 192.851] y[75.146, 76.374] | **YES** |
| `R_DOORPD` (v1.7, per the journal) | x[189.038, 190.162] y[75.223, 80.177] | YES |
| `R_ESTOPPD` | x[184.486, 185.714] y[69.906, 75.294] | no |
| `R_STOPRAIL` | x[194.926, 199.074] y[82.539, 83.461] | no |

So the pocket was never one part's slot. **It is where `J_DOOR`'s and
`J_ESTOP`'s OWN designators live** — the same two labels the SE-corner
label-ownership learning is about. The reusable finding stands and gets sharper:
a floorplan comment that clears a region by checking COURTYARDS has checked the
wrong layer, and here it missed two 5-circuit connectors' names.

### Correction 3 — REMOVING the two footprints closes the `J_ISOLOOP` 30 V blocker, which no silk-only pass could.

`label_ownership_se_corner.md` proves all four directions out of `J_ISOLOOP`'s
courtyard are closed, and that the one candidate pocket
`x[191.555, 193.755] y[82.795, 87.155]` loses to `J_DOOR`. Re-measured at that
pocket's centre (192.655, 84.975), nearest `J*`/`F*`/`TP*` courtyard:

| footprints present | nearest | 2nd nearest | ownership margin |
|---|---|---|---|
| all (today) | **`J_DOOR` 1.100 mm** | `J_ISOLOOP` 2.680 mm | J_ISOLOOP LOSES |
| `J_DOOR` removed | **`J_ISOLOOP` 2.680 mm** | `J_ESTOP` 8.769 mm | **+6.089 mm** |
| both removed | **`J_ISOLOOP` 2.680 mm** | `J_RH_EXHAUST` 8.870 mm | **+6.190 mm** |

`MIN_OWNERSHIP_MARGIN_MM` is 1.5. **Removing `J_DOOR` alone makes the 30 V
NOT-SELV isolated-contactor terminal's designator OWNABLE with 4× the required
margin** — the render-lens P0 that was declared unfixable without a part change.
Removing both additionally frees `J_DOOR`'s entire courtyard
x[193.755, 200.245] y[76.365, 87.155] (10.79 mm of east column) and `J_ESTOP`'s
x[193.755, 200.245] y[65.485, 76.275], which is more east-column relief than the
ZH-3 / SH-3 spike was chasing (1.700 / 3.900 mm).

**That is the lever, and it is O5 — not DNP.**

## Decision

**NONE TAKEN. This ADR is `proposed` and this pass STOPPED here deliberately.**

Every viable resolution is either a reversal of the user's own decision (O2) or a
change to the safety AND chain the brief specifies as normative (O4), and the
governing instruction for this pass is to write the ADR and stop rather than
choose. The measurement is complete, the options are costed, and no copper was
touched.

**What is needed from the user, in one question:** with no door signal and no
E-stop signal available, do the `DOOR_OK` and `ESTOP_OK` terms stay in the chain
and get satisfied by a removable shorting plug on a populated connector (**O2**),
or do they leave the chain with a brief amendment (**O4**)? And independently:
should the `J_DOOR` / `J_ESTOP` FOOTPRINTS be removed (**O5**), given that
removing `J_DOOR` alone closes the `J_ISOLOOP` 30 V label blocker?

The recommendation, offered and not acted on: **O2 + O5 is incoherent** (O5
removes the connector O2 needs). **O4 + O5** is self-consistent and is the only
combination that closes four things at once — the transposition hazard, the
`J_ISOLOOP` 30 V misidentification, the 1b/7 silk FATAL, and the east-column
squeeze — at the cost of a brief amendment and the honest admission that an
E-stop on a keystroke-presser was never a barrier on the appliance. **O2 alone**
is the conservative choice: it costs almost nothing, keeps every brief term, and
leaves the `J_ISOLOOP` blocker open.

## Consequences

- **`R_DOORPD` / `R_ESTOPPD` (470 Ω) MUST SURVIVE ANY OPTION.** They are the sole
  reason the unfitted state measures 1.15 mV instead of floating. A floating HC14
  input is indeterminate, self-oscillating, and would make the whole measurement
  above void. If the footprints go (O5), the pull-downs must move to the HC14 end
  or the input must be tied at the gate. ADR-0024's `part_value` E-INV asserts on
  both resistors stay load-bearing.
- **ADR-0024's 470 Ω choice and its corrected `R_pd ≤ 559.3 Ω` worst-case bound
  survive unchanged** and are re-affirmed in an addendum to that ADR. The value
  and the bound are still what makes any FUTURE fitted harness safe; a superseded
  reason is evidence, not litter.
- **ADR-0024 Decision A (`J_DOOR.4` = GND) survives on its own merits.** It
  removed a real path and also un-blocked door EOL supervision. It is not
  contingent on the cross-plug argument.
- **`R_DOORS` / `R_ESTOPS` (680 Ω) lose their stated purpose under any option
  where no field harness is ever fitted** — ADR-0024 gives them two jobs (keep
  the field pin off the logic pin; limit current into the HC14 input clamp after
  `D_DOOR` clamps) and both are about a field harness. Under O2 they are still
  needed. Under O4+O5 they, and `D_DOOR`/`D_ESTOP`, are removable. **Removing
  them is what frees the pocket; DNP-ing them is not** (Correction 1).
- **`MODE_RAW` / `J_MODE` are untouched.** `MODE_AUTO_HW` is the Manual/Auto
  permission and `J_MODE` is installed; ADR-0018's mechanical key and ADR-0024's
  named residual (`MODE_RAW` has no ESD device) both stand.
- **What must be re-verified after whichever option lands:** the E-INV set
  (`electrical_invariants.yaml`: 228, 262, 389, 401, 530, 537, 746, 761, and the
  ADR-0024 block at 1122–1256), `policy_waivers.yaml:278`
  (`J_DOOR->DOOR_RAW, J_ESTOP->ESTOP_RAW`), `floorplan.yaml` 365–373 and 742–757,
  the pin-review cross-plug matrix (12 ordered pairs → 2 with two housings gone),
  ORDER_README §10 and §2a, and the four-lens battery in full. **The battery must
  be re-run FRESH after the copper settles, not inherited.**
- **What breaks if this is reversed later** (a real door or E-stop signal becomes
  available): under O2, nothing — pull the plug, fit the harness. Under O4, the
  AND terms have to be re-plumbed in copper and the brief amendment retracted.
  **O2 is reversible; O4 is not.** That asymmetry is the strongest argument for
  O2 and is stated here so the cheaper-looking option does not win by default.
