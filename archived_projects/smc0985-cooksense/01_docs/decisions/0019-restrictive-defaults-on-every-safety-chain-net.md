# ADR-0019 — A restrictive default on every safety-chain net, with the
# direction DERIVED per net rather than blanket-fitted (v1.7)

status: accepted
date: 2026-07-28
tags: protection

## The defect this closes

v1.6 §2 measured, from the netlist: of the **18** nets feeding a
permission/gating input on this board, **7 carry a pull and 11 carry none** —
`WD_OK`, `ESTOP_OK`, `MODE_AUTO_HW`, `DOOR_OK`, `AND1`, `AND2`, `CTR_SAFE`,
`FAULT`, `FAULT_SET_N`, `FAULT_LATCH_CLEAR`, `STOP_REQ_N`.

Every one is driven by exactly one **push-pull CMOS output**, so the pull does
nothing while the board is healthy and everything when the driver is absent —
unfitted, tombstoned, cracked, or dead. Measured single-part cases:

- **`U_SCHM` dead** (SN74HC14, SOIC-14) floats `ESTOP_OK` + `MODE_AUTO_HW` +
  `DOOR_OK` **simultaneously** — the E-stop can read clear with the mushroom
  pressed, and `U_EXP.2/3/4` sample the SAME floating nets, so software has no
  independent cross-check.
- **`U_LATCHB` dead** (SOT-23-5) floats `FAULT_LATCH_CLEAR` into BOTH
  `U_AND3.6` (coil rail) and `U_CAND2.3` (external contactor).
- **`U_WD` dead** floats `WD_OK` into five CMOS inputs.

And the asymmetry that makes it urgent, found by the v1.6 re-verification:
all four permissions are read back on MCP23017 port B (`GPB7/2/1/3`), and
DS20001952C §3.5.7 says one `GPPU` bit pulls a pin up with **100 kΩ**. POR is
`0x00`, so the default is safe — but **one register write converts the
indeterminate float into a deterministic PERMISSIVE on all four at once**, and
**there is no software way to add a pull-DOWN.** The register can only make the
default worse. Hardware is the only place a pull-DOWN can exist.

## The question the user posed: which of the 11, and why not blanket-fit?

The test applied here is **not** "is this net a permission". It is:

> *If this net's only driver is absent, what does the CONSUMER do with the
> undriven level, and which level is RESTRICTIVE at that consumer?*

Applying it net by net gives a result a blanket pull-down would have got
**wrong**, which is the evidence that it was derived:

| # | net | driver | consumer(s) | restrictive level | default fitted |
|---|---|---|---|---|---|
| 1 | `WD_OK` | `U_WD.1` | `U_AND1.3`, `U_CAND1.1`, `U_FAULTAND.1`, `U_OENAND.2` | LOW (supervisor not OK) | `R_WDOKPD` 100 k **DOWN** |
| 2 | `ESTOP_OK` | `U_SCHM.4` | `U_AND1.6`, `U_CAND1.3`, `U_FAULTAND.3` | LOW (E-stop pressed) | `R_ESTOPOKPD` 100 k **DOWN** |
| 3 | `MODE_AUTO_HW` | `U_SCHM.8` | `U_AND1.1` | LOW (not in AUTO) | `R_MODEHWPD` 100 k **DOWN** |
| 4 | `DOOR_OK` | `U_SCHM.12` | `U_OSCLR.1` | LOW (door open) | `R_DOOROKPD` 100 k **DOWN** |
| 5 | `AND1` | `U_AND1.4` | `U_AND3.1` | LOW | `R_AND1PD` 100 k **DOWN** |
| 6 | `AND2` | `U_AND2.4` | `U_AND3.3` | LOW | `R_AND2PD` 100 k **DOWN** |
| 7 | `CTR_SAFE` | `U_CAND1.4` | `U_CAND2.1` | LOW | `R_CTRSAFEPD` 100 k **DOWN** |
| 8 | `FAULT_LATCH_CLEAR` | `U_LATCHB.4` | `U_AND3.6`, `U_CAND2.3`, `U_LATCHA.2` | LOW (latch not cleared) | `R_FLCPD` 100 k **DOWN** |
| 9 | `STOP_REQ_N` | `U_STOPINV.4` | `U_OSCLR.3` | LOW (STOP asserted ⇒ one-shot held clear) | `R_STOPREQNPD` 100 k **DOWN** |
| 10 | `FAULT_SET_N` | `U_FAULTAND.4` | `U_LATCHA.1` (/S) | **LOW = ASSERTED** (fault SET) | `R_FSETNPD` 100 k **DOWN** |
| 11 | `FAULT` | `U_LATCHA.4` | `U_LATCHB.2` | **HIGH** | `R_FAULTPU` 100 k **UP to 3V3** |

**Row 11 is the proof.** `FAULT` is Q of the /S-/R NAND latch and its only
consumer is `U_LATCHB.B`. A blanket pull-DOWN there would be **actively
harmful**: with `U_LATCHA` dead and `FAULT` pulled low,
`FAULT_LATCH_CLEAR` = NAND(`REARM_N`=1, `FAULT`=0) = **1 = PERMISSIVE** at both
`U_AND3.6` and `U_CAND2.3`. Pulled HIGH, the same dead part gives
`FAULT_LATCH_CLEAR` = 0 = restrictive. One of the eleven runs the other way,
and it is the one a habit would have got backwards.

**Row 10 is the second proof.** `FAULT_SET_N` is an ACTIVE-LOW net and it gets
a pull-DOWN, i.e. its default is **ASSERTED**. That is the opposite of the
convention this board applies to the other active-low line in the same latch:
`REARM_N` is active-low and is pulled **UP** (`R_REARMPU`, deasserted). Both are
right, because the derivation is over *which level is restrictive at the
consumer*, not over the net's name: for `FAULT_SET_N` the asserted state blocks
the machine, for `REARM_N` the asserted state permits it.

**Why the seven intermediates get one too, and are not "just" internal nodes.**
The distinction between a permission and an intermediate node is real for
*diagnosis* (a permission is read back by the expander; an intermediate node is
invisible to software) but it is **not** a reason to leave the intermediate
undefended, because the failure is identical in kind and the AND-chain does not
re-derive it. If `U_AND1` is missing, `AND1` floats and `U_AND3` can still
publish `KEY_RELAY_ALLOWED` = 1 from `AND2` · `FAULT_LATCH_CLEAR` alone — the
pull-downs on `MODE_AUTO_HW`/`WD_OK`/`ESTOP_OK` do nothing about it, because
they defend `U_AND1`'s INPUTS and the dead part is `U_AND1` itself. Every rung
of a cascade needs its own default or the cascade has a hole one part wide.
This board already accepted exactly that argument once, at pin review Q4, for
`R_DECUPD`/`R_DECDPD` ("floating CMOS inputs stay out-of-spec: belt AND
braces"); it was simply never applied to the safety permissions themselves.

**A bonus the derivation buys, not designed for.** With `FAULT` pulled UP and
`FAULT_LATCH_CLEAR` pulled DOWN, the NAND latch's exit from its forbidden state
(Q = /Q = 1, when both inputs release together) is **biased toward SET**, i.e.
toward restrictive, instead of being a race.

## Value and cost

100 kΩ, `C25741` (0402WGF1003TCE, JLC **basic** library) — the identical code
the board's existing 22 pull resistors already use, so **zero new BOM lines and
zero new feeders**. Standing current against a live driver is 3.3 V/100 kΩ =
33 µA per net, invisible to a push-pull CMOS output. Eleven 0402 placements.

## Invariants emitted (E-INV / E-ADR)

`net_has_part … part_type: resistor, min: 1` on all eleven nets, plus
`pin_on_net` asserts pinning the DIRECTION of the two that run against habit:
`R_FAULTPU.2` on `3V3` (the pull-UP) and `R_FSETNPD.2` on `GND`. Direction is
the property that was derived and therefore the property worth checking —
`net_has_part` alone would pass a pull-down soldered onto `FAULT`.
