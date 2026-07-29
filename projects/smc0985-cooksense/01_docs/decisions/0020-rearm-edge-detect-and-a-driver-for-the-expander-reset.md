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

---

## CORRECTION, 2026-07-28 — DECISION B'S HEADLINE CLAIM WAS FALSE IN ITS OWN CASE

*Appended, not edited. Decision B above stands exactly as it was written; this
section records that it was wrong, why, and what makes it true. The claim is
kept verbatim because a decision that quietly loses its false sentence teaches
nobody anything.*

**The claim.** Decision B ends: *"the expander's outputs cannot persist across a
watchdog timeout or a brown-out."*

**It was false the moment this ADR landed, and this ADR is what made it false.**
The v1.7 red-team topology lens found it; the lead confirmed it from the
netlist; it was a **P0** and it blocked the seal.

`WD_OK` carries THREE things, and Decision B only counted two:

| node | what it is | drive |
|---|---|---|
| `U_WD.1` | TPS3823-33 `RESET_N` — the intended driver | push-pull, `V_OL` specified only at `I_OL` = 1.2 mA, abs-max ±5 mA (SLVS165O §6.5, §6.2) |
| `U_EXP.18` | MCP23017 `RESET_N` — what Decision B added | input, ~1 µA |
| **`U_EXP.8`** | **MCP23017 GPB7 — a BIDIRECTIONAL I/O rated 25 mA** | **output when the host writes `IODIRB.7 = 0`** |

One I²C write — `IODIRB.7 = 0, OLATB.7 = 1` — therefore drives the board's
most-consumed permission HIGH against a supervisor output that no datasheet
bounds at that current. The watchdog term vanishes from `U_AND1.3` (coil rail),
`U_CAND1.1` (contactor), `U_FAULTAND.1` (fault latch) and `U_OENAND.2` ('595
output-enable) **at once**.

**And it is SELF-SUSTAINING, which is the part that makes it a P0 rather than a
P1.** The only mechanism that can stop the drive is the expander's own RESET —
which Decision B had just wired to this very net. RESET asserts only below
`V_IL` = 0.2 × V_DD = **0.660 V** (DS20001952C D031). If the contention leaves
the node above 0.660 V, the expander is never reset, GPB7 keeps driving, and
`WD_OK` stays permissive **until the 3V3 rail is removed**. Decision B put the
reset on the one net whose defeat disables the reset.

**v1.6 did not have this defect and v1.7 introduced it**, measured on both
netlists: in v1.6 `U_EXP.18` sat on `EXP_RST_N`, a driverless net. The defect is
not that GPB7 shares `WD_OK` (it always did — that is the watchdog readback);
it is that Decision B then made the *recovery path* depend on the same node.

**THE FIX — `R_WDOKSER`, 10 kΩ (C60490, an existing BOM line), in series to
`U_EXP.8` AND NOTHING ELSE.** `U_EXP.18` and all five gate inputs stay on the
RAW net, so Decision B's reset path is untouched, and `R_WDOKPD` (100 kΩ down)
remains `WD_OK`'s only default.

    TPS3823-33 V_OL <= 0.4 V at I_OL = 1.2 mA   =>  guaranteed sink R <= 333.3 ohm
    GPB7 at 3.3 V through 9.90k (10k, -1%) into 333.3 || 100k = 332.2 ohm
      V(WD_OK) = 3.3 x 332.2 / (9900 + 332.2)                     =  0.107 V
      + 21 uA of aggregate input leakage (4 x LVC +-5 uA, MCP +-1 uA) x 332.2
                                                                  =  0.114 V

| threshold | value | margin |
|---|---|---|
| MCP23017 `RESET` `V_IL` = 0.2 × V_DD (DS20001952C D031) | 0.660 V | **546 mV** |
| SN74LVC1G11 / 1G00 `V_IL` at V_CC 2.7–3.6 V (SCES487I) | 0.800 V | **686 mV** |

Contention current = 3.3/10232 = **0.323 mA**: 27 % of the `V_OL` spec point and
6.5 % of the ±5 mA abs max. **So the forced-high node now falls below the reset
threshold, the expander IS reset, GPB7 returns to an input (IODIR POR =
`0xFF`), and the drive ends. Decision B's claim is true as of the sealed v1.7 —
because of this resistor, not because of the wiring alone.**

**What this correction does NOT claim.** (a) The reverse case — the host driving
GPB7 *low* — is bounded only by a `V_OH` spec taken at 30 µA, so no worst-case
node voltage can be computed from the datasheet. It is left as an unbounded but
**fail-safe** direction: it pulls `WD_OK` toward RESTRICTIVE for all five
consumers, and if it reaches 0.660 V it resets the expander and self-clears.
(b) The **degenerate GPB7 readback** (ORDER_README §7a-3, raised independently
by the v1.7 pin review) is **NOT repaired**: `U_EXP.18` still sits on `WD_OK`,
so the expander is in reset exactly when `WD_OK` reads 0. Use the `IODIR`-readback
replacement §7a-3 specifies. An earlier disposition said this fix "repairs the
readback for free"; it does not, and that sentence is withdrawn here.

## Invariants emitted by this correction

- `part_value` `R_WDOKSER` = `10k` — the whole bound is this number. At 0 Ω the
  P0 returns with every topology assert still green.
- `pin_on_net` `U_EXP.8` = `WD_OK_EXP` — GPB7 is on the FAR side of the
  resistor; a "simplification" that reunites the nets restores the defect.
- `pin_on_net` `U_EXP.18` = `WD_OK` (already present, ADR-0020) — the reset must
  stay on the RAW net or the fix defeats itself.
- `pin_on_net` `U_ONESHOT.9` = `REARM_N` and `U_ONESHOT.12` = `REARM_PULSE_N` —
  the edge-detect is wired through section 2 and not bypassed.
- `pin_on_net` `U_ONESHOT.11` = `WD_OK` — the reset-hold that makes the
  power-up property a guarantee.
- `pin_on_net` `U_EXP.18` = `WD_OK` — the expander reset HAS a driver.
- `part_value` `C_OS2` = `1uF` and `R_OS2` = `10k` — t_w = 7 ms is computed
  from exactly these two numbers.
- `part_value` `R_REARMPU` = `100k` (carried from v1.6).
