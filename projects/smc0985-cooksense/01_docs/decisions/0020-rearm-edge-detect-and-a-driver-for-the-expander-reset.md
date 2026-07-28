# ADR-0020 — `REARM_N` becomes an EDGE, and `EXP_RST_N` gets the only
# driver that makes the defeat non-persistent (v1.7)

status: accepted
date: 2026-07-28
tags: protection

## The two defects this closes

**A3-i — a held-low `REARM_N` permanently defeats the fault latch.** v1.6 §3,
netlist-verified: `REARM_N = {R_REARMPU.1, U_EXP.26 (GPA5), U_LATCHB.1}` —
**one driver**, no button, no connector pin, no test point. Held low (driven,
not pulsed): /R is asserted forever, `FAULT_LATCH_CLEAR` is forced HIGH =
permissive at `U_AND3.6` (coil rail) and `U_CAND2.3` (contactor) at all times;
with a fault also present the NAND latch sits in its **forbidden state**
(Q = /Q = 1); and `U_LATCHA` degenerates to `FAULT` = NOT(`FAULT_SET_N`), a
combinational repeater. The live terms still gate — **what is lost is MEMORY**.
A fault that clears re-permits cooking with no re-arm, which is exactly what
ADR-0011 §2 exists to prevent. ORDER_README §7 said "Pulse `REARM_N` low" and
**nothing in hardware enforced a pulse.**

**A3-ii — `EXP_RST_N` has no driver at all.** `EXP_RST_N = {R_EXPRST.1,
U_EXP.18}`. Nothing on this board can reset the expander, so its registers hold
until 3V3 drops. A held-low `REARM_N` therefore does **not** survive a 3V3
cycle but **does survive every Pi reboot**. The same retention mechanism was
already written into this board's own `electrical_invariants.yaml` — in the
`why:` for `R_WDPETPD`, about the retained `CONTACTOR_REQ` latch — and had
never been applied to `REARM_N`.

## Decision A — the edge-detect costs ZERO new ICs

`U_ONESHOT` is a **CD74HC221, a DUAL non-retriggerable one-shot, and section 2
has been unused since v1.2** (`2A_N` tied 3V3, `2B` GND, `2R_N` GND held reset,
`2CXRX` carrying a 10 kΩ to VCC and `2CX` open). Section 2 becomes the
`REARM_N` edge-detect:

| pin | was | now | why |
|---|---|---|---|
| 9 `2A_N` | `3V3` (trigger blocked) | **`REARM_N`** | `A_N` is the negative-edge trigger; only a HIGH→LOW TRANSITION fires |
| 10 `2B` | `GND` | **`3V3`** | `B` must be high to enable A-triggering |
| 11 `2R_N` | `GND` (held reset) | **`WD_OK`** | see below — this is a safety property, not a tie-off |
| 12 `2Q_N` | open | **`REARM_PULSE_N`** | the LOW pulse that now drives the latch |
| 6 `2CX` | open | `OS2_C` | Cext |
| 7 `2CXRX` | `OS2_RC` (`R_OS2` 10 k to 3V3) | unchanged | Rext, already present |

and `U_LATCHB.1` (/R) moves from `REARM_N` to **`REARM_PULSE_N`**.

Timing: `C_OS2` = 1 µF (0603, the SAME `C15849` line as `C_OS`/`C_ADCV`/the four
`C_SW*` — no new BOM line), `R_OS2` = 10 kΩ unchanged.
**t_w = K·Rx·Cx = 0.7 · 10 kΩ · 1 µF = 7.0 ms** (K = 0.7 at V_CC = 4.5 V per
CD74HC221 DS p.1; Figure 6 puts K ≈ 0.75 toward 3 V ⇒ **7.0–7.5 ms**). Bounds
that matter: ≫ the NAND latch's propagation (ns), and ≪ any human or software
timescale, so a re-arm is unambiguously an event rather than a state.

**Behaviour with `REARM_N` held low:** one 7 ms pulse, then /R returns HIGH and
**the latch has its memory back**. If a fault is still present, /S is low while
/R pulses — the latch simply returns to SET when the pulse ends, i.e. *you
cannot clear a live fault*, which is correct.

**Power-up property PRESERVED, and now guaranteed rather than argued.** At
power-up `WD_OK` is LOW for the TPS3823 reset delay (t_d = 120/200/300 ms,
SLVS165O §6.8) → `FAULT_SET_N` low → the latch is FORCED SET, so the coil rail
cannot come up after any power interruption without an explicit re-arm; and
MCP23017 `IODIR` POR is `1111 1111`, so GPA5 is an INPUT and `R_REARMPU` holds
`REARM_N` high. Wiring `2R_N` to `WD_OK` **removes the one new risk this change
could have introduced** — a '221 that emits a spurious output pulse as its own
supply comes up — because the section is held reset (`2Q_N` = HIGH = /R
deasserted) for the whole supervisor reset window. It also means a re-arm
attempt during a watchdog fault is **ignored in hardware**, which is the
behaviour the safety chain already asserts everywhere else.

`R_REARMPU` (100 kΩ UP) stays on `REARM_N`: an un-driven GPA5 still means "no
re-arm", and it is now also the resistor that guarantees no falling edge at
power-up.

## Decision B — `U_EXP.18` leaves the driverless net for `WD_OK`

`EXP_RST_N` is DELETED as a net. `U_EXP.18` (RESET_N, active low) joins
**`WD_OK`**, and `R_EXPRST` (10 kΩ pull-up) is **REMOVED**.

Removing `R_EXPRST` is not tidying, it is required: left in place it would
become a **10 kΩ pull-UP on `WD_OK`**, i.e. a pull toward PERMISSIVE on the
board's most-consumed permission, defeating ADR-0019's `R_WDOKPD` outright
(10 kΩ up beats 100 kΩ down: 3.3 · 100/110 = 3.0 V). `WD_OK`'s default is now
the 100 kΩ pull-DOWN and nothing else.

What this buys, in one sentence: **the expander's outputs cannot persist across
a watchdog timeout or a brown-out.** TPS3823 RESET_N asserts LOW on power-up,
on brown-out, and on watchdog timeout; each of those now drives MCP23017 RESET,
returning every GPIO to POR (all INPUTS) so the eleven authorization pull-downs
and `R_REARMPU` take over. This directly closes the worry ADR-0011 §8 wrote
down and could only mitigate — *"a Pi that dies … the MCP23017 keeps its
`CONTACTOR_REQ` latch"* — and it makes the A3 defeat non-persistent across a
watchdog event, not merely across a 3V3 cycle.

Loading and timing checked: `U_EXP.18` is a CMOS input (~1 µA), added to a net
already driving five CMOS inputs from a push-pull TPS3823 output; MCP23017
needs microseconds of reset width and gets ≥ 120 ms.

**The firmware consequence, which is REQUIRED and goes in ORDER_README §7a.**
The host must (1) initialise the expander only AFTER its heartbeat on `WD_PET`
is established — during Pi boot `R_WDPETPD` holds `WD_PET` static, so the
supervisor times out every ~1.6 s and will reset the expander under a
half-finished init — and (2) treat an unexpected `IODIR`/`IOCON` readback of
the POR pattern as "the expander was reset", re-initialise, and log it. The
MCP23017 has no reset-status flag, so a register readback is the only detector.

## What is NOT claimed

`REARM_N` still has exactly one driver, and it is still the same Pi the
hardware chain exists to bound (BRIEF §12 T6). This ADR removes the
*permanence* of a defeat, not the *authority* — a Pi that pulses `REARM_N`
every 7 ms can still re-arm continuously. Bounding the authority needs a
physical re-arm button on a field connector, which is a panel/UX decision and
is recorded as an open item rather than taken here.

## Invariants emitted (E-INV / E-ADR)

- `pin_on_net` `U_LATCHB.1` = `REARM_PULSE_N` — the latch's /R is the PULSE,
  never the raw line. This is the whole fix in one assert.
- `pin_on_net` `U_ONESHOT.9` = `REARM_N` and `U_ONESHOT.12` = `REARM_PULSE_N` —
  the edge-detect is wired through section 2 and not bypassed.
- `pin_on_net` `U_ONESHOT.11` = `WD_OK` — the reset-hold that makes the
  power-up property a guarantee.
- `pin_on_net` `U_EXP.18` = `WD_OK` — the expander reset HAS a driver.
- `part_value` `C_OS2` = `1uF` and `R_OS2` = `10k` — t_w = 7 ms is computed
  from exactly these two numbers.
- `part_value` `R_REARMPU` = `100k` (carried from v1.6).
