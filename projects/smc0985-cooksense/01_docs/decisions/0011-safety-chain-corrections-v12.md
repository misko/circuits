# ADR-0011 — Safety-chain corrections (v1.2): thermal hard-stop, latch,
# contactor gate, independent STOP rail, STOP preemption, non-retriggerable PRESS

status: accepted
date: 2026-07-24
tags: protection, topology

External review of v1.1 (2026-07-24, all findings CONFIRMED against the
sealed source) showed the hardware safety chain had five defects that
survived from v1.0 because no electrical revision ever ran. All five are
corrected here, in hardware, per ADR-0002's no-firmware rule.

## 1. Thermal hard-stop actually at ~25C (review F2) — FIXED

R_TH1=R_TH2=10k put TCAM_THRESH at 1.65V — exactly where a 10k-pullup +
10k-NTC divider sits at 25C. The 70-75C stop did not exist.

NTC is the already-committed KNTC0603/10KF3950 (02_parts: R25=10k ±1%,
B25/85=3987K — use B25/85 for the elevated range, per its part.yaml
gotcha; LCSC C2892547). New reference divider from 3V3_ANALOG:
**R_TH1=68k (top), R_TH2=10k (bottom)** → 0.4231V → trips at **74.9C**
(brief §3.14 camera HARD limit = 75C). Full math in DETAIL_DESIGN.md.
R_TH1/R_TH2 are a documented SOLDER-SELECT field (1206, like RKEY):
R_TH2 = 8.2k→81.0C · 10k→74.9C (default) · 12k→69.4C · 15k→63.0C.
New test point TP_TCTH on TCAM_THRESH. Both comparator channels (cam
A+B) share the one reference, as before. Bring-up gate: validate 60/65/
70/75C in a controlled fixture, both channels, before appliance use.

## 2. TEMP_OK absent from the fault-latch SET (review F3a) — FIXED

U_FAULTAND's third input was tied to N3V3. Now FAULT_SET_N =
WD_OK·ESTOP_OK·**TEMP_OK**: a thermal trip LATCHES (recovery = temps
below reset + manual re-arm, brief §3.6) instead of silently
self-clearing when the NTC cools.

## 3. Contactor not gated by faults (review F3b) — FIXED

CONTACTOR_REQ (expander GPA4) drove the opto directly; only the E-stop
contact-B loop could interrupt the external contactor. Now the LED drive
is CONTACTOR_DRV = CONTACTOR_REQ · WD_OK · ESTOP_OK · TEMP_OK ·
FAULT_LATCH_CLEAR (two SN74LVC1G11: U_CAND1 = WD·ESTOP·TEMP → CTR_SAFE;
U_CAND2 = CTR_SAFE·FAULT_LATCH_CLEAR·CONTACTOR_REQ → CONTACTOR_DRV). A
watchdog/thermal/E-stop/latched fault now removes contactor permission
in HARDWARE, redundantly with the E-stop's physical loop break.

## 4. K_STOP disabled by the very faults it answers (review F3c) — FIXED

K_STOP's coil shared 5V_KEY_RELAY: a WD/TEMP fault killed the rail and
the STOP relay with it — the chain could not stop a running cook.
K_STOP's coil moves to a new rail **5V_STOP** = 5V_PROTECTED through
R_STOPRAIL (0R link, own bulk cap): available whenever the board is
powered. The coil is driven by a dedicated 2N7002 (Q_STOPDRV) from
STOP_REQ with its own flyback diode — NOT via the ULN (whose COM/flyback
sits on the switched key rail).

Deliberately NOT gated by KEY_RELAY_ALLOWED, ESTOP_OK, DOOR_OK or
MODE_AUTO_HW, with reasons:
- Closing K_STOP presses the OEM's own STOP/CLEAR key — intrinsically
  safe in every state; it is the ABORT actuator (brief C9: warn → STOP;
  C10: "local STOP + contactor remain" on Pi crash — impossible if a WD
  fault also cut the STOP rail; that was exactly the v1.1 defect).
- E-stop/door faults must be able to COMMAND a stop; gating the stop
  relay off on those faults inverts the intent.
- MANUAL mode: a spurious held STOP is a held STOP key — blocks cooking,
  never starts it; and STOP_REQ has a 100k pull-down + the Pi boots with
  GPIOs as inputs, so the un-driven state is OPEN.
- The keypad-domain isolation is unchanged: same DIP05 1.5kV barrier,
  same comb geometry; only the coil-side supply net changed.

## 5. STOP did not preempt an active press (review F4) — FIXED

STOP_REQ now performs three HARDWARE actions:
(a) clears the PRESS one-shot: 1R_N = OS_CLR_N = DOOR_OK · STOP_REQ_N
    (U_OSCLR, was DOOR_OK only);
(b) disables BOTH selector decoders: DECU_G1 = DECU_G1_RAW · STOP_REQ_N,
    DECD_G1 = DECD_G1_RAW · STOP_REQ_N (U_DECUEN/U_DECDEN; the 100k
    enable pull-downs move to the RAW nets, which are the ones that
    float when SR_OE_N tri-states the 595);
(c) energizes K_STOP only (its dedicated rail + driver, §4 above).
STOP_REQ moved off the shift register to DIRECT GPIO26/phys37
(ADR-0010): it must not sit behind the frozen KEY_LATCH (§6) or a
tri-stated 595. STOP_REQ_N = U_STOPINV (1G00 as inverter). U_SR2 (whose
only used bit was STOP_REQ) is DELETED. Intended sequence (software,
now hardware-enforceable): raise STOP_REQ → PRESS clears + decoders
release U/D → wait relay release (>=1ms) → K_STOP held closed a bounded
interval → drop STOP_REQ. Encoded in the key truth table
(DETAIL_DESIGN).

## 6. PRESS bound was not hard (review F5) — FIXED

SN74LVC1G123 is RETRIGGERABLE (TI: up to 100% duty) — repeated Pi edges
could hold K_PRESS forever. Replaced by **CD74HC221M96** (TI dual
monostable, SOIC-16, LCSC C133954, JLC Extended stock 2542 @2026-07-24):
"Once triggered, the outputs are independent of further trigger inputs"
(SCHS166F p.1). Section 1: 1A_N=GND, 1B=PRESS_REQ (Schmitt), 1R_N=
OS_CLR_N, 1Q=PRESS_TIMED, 1Q_N=PRESS_TIMED_N. tw = K·Rx·Cx, K~0.7-0.75
at 3.3V: Rx=510k, Cx=1uF → ~357-383ms typ, <=436ms worst-case < 500ms
HARD (math in DETAIL_DESIGN). Known bounded caveat: R_N rising with B
held high re-fires ONE pulse (DS truth-table note) — bounded, one-hot,
documented in part.yaml; software drops PRESS_REQ on abort.
ALSO: selector addresses frozen while pressing — KEY_LATCH_G =
KEY_LATCH · PRESS_TIMED_N (U_LATCHG) feeds the 595 RCLK, so the Pi
cannot re-address U/D mid-press (review F5b). STOP is unaffected
(direct GPIO, §5).

## 7. Deterministic pulls (review "other corrections", user-scoped IN)

100k pulls hold the safe state while Pi/expander are un-driven
(boot/reset): pull-DOWN on HOST_AUTH, MCU_RELAY_ENABLE, KEY_RESET_N
(registers held cleared), RAIL_EN_A/B/RHA/RHE, CONTACTOR_REQ, STOP_REQ;
pull-UP on REARM_N (a floating re-arm must NOT clear the fault latch —
REARM_N is active-low). Existing pulls unchanged.

## 8. WD_PET floated — the watchdog never bit with the Pi absent (P0, 2026-07-25)

Found by the seal-time SAFETY-CHAIN TRUTH-TABLE review, against the v1.2
netlist at 1e47c01. §7 pulled down every *authorization* line but left the
one line the whole de-energization argument rests on floating:

    WD_PET  =  { J_PI.11, U_WD.4 }      — two nodes, no pull

`02_parts/TPS3823-33DBVR/part.yaml` pin 4: *"watchdog input; must see an
edge within t_out or RESET asserts; **if left floating the device
self-pulses (WD effectively disabled)**"*. So with J_PI unplugged, the
ribbon off, or the Pi simply powered down:

1. WDI self-pulses → the supervisor never times out → WD_OK stays HIGH.
2. The MCP23017 keeps its output latches: `CONTACTOR_REQ` retains whatever
   was last written, and `EXP_RST_N` is a 10k pull-UP to 3V3 with **no
   driver on the board** — nothing resets the expander when the host goes.
   (R_CTRREQPD is a 100k pull-down, so it loses to a driven MCP23017 output.)
3. U_CAND1 = WD_OK·ESTOP_OK·TEMP_OK holds, U_CAND2 = CTR_SAFE·
   FAULT_LATCH_CLEAR·CONTACTOR_REQ holds → CONTACTOR_DRV stays asserted →

**the external cooking contactor stays ENERGISED indefinitely.**

That is the exact inverse of the truth table's `Pi crash (WD)` row below,
and of BRIEF C10. On a cooking-safety interlock it is a burn/fire hazard,
not a nicety.

FIX: `R_WDPETPD`, 100k 0402, WD_PET → GND. WDI held at a defined LOW is
edge-free, so the fixed 0.9/1.6/2.5 s timer expires and RESET_N asserts,
which is what every downstream gate already reads. DOWN rather than UP:
both are edge-free and both bite, but a pull-UP to this board's 3V3 would
source current into an unpowered Pi through its GPIO ESD clamp — partly
back-feeding the very host whose absence this covers.

WHY IT SURVIVED FOUR GATES. It was not a missed check, it was an
UNEXPRESSED one: the de-energization intent lived in §3 and in the truth
table as PROSE, and no `electrical_invariants.yaml` assertion pinned it,
so DRC/ERC/parity/audit all agreed with each other about a board that was
wrong. The counter-measure is the §8 invariant triple below, and the
general rule it restates: **an ADR that emits no invariant is not
enforced** (canon E-ADR).

## Fault × actuator truth table (the review's core demand)

Post-fault steady state, AUTO mode, appliance mid-cycle:

| fault | key relays (U/D/PRESS) | K_STOP | contactor |
|---|---|---|---|
| — (BEFORE, v1.1) / (AFTER, v1.2) | | | |
| WD timeout | dead / dead | DEAD / **available** | live / **dropped** |
| E-stop | dead / dead | DEAD / **available** | dropped (loop) / dropped (loop+gate) |
| TEMP trip | dead / dead | DEAD / **available** | live / **dropped** |
| TEMP trip latched? | NO (self-clears on cool) / **YES** | — | — |
| door open | press aborted / press aborted | available / available | live / live (door is an abort, not a contactor fault — OEM interlocks own the door) |
| fault latched | dead / dead | DEAD / **available** | live / **dropped** |
| STOP_REQ (no fault) | live / **U/D+PRESS force-released** | available / **closed** | unaffected |
| Pi crash (WD) | dead / dead | DEAD / **available** (Pi can't drive it, but E-stop/manual path + OEM STOP key remain; contactor dropped) | live / **dropped** |

"available" = rail present, relay answers STOP_REQ. The v1.2 column is
what the seal-time SAFETY-CHAIN TRUTH-TABLE review must independently
re-derive from the netlist.

## Executable invariants (E-ADR)

Emitted citing adr 0011: U_FAULTAND.6 on TEMP_OK; contactor chain
(U_CAND1/U_CAND2 input/output pins, R_OPTOLED fed from CONTACTOR_DRV);
K_STOP coil on 5V_STOP + series chain 5V_PROTECTED→R_STOPRAIL→5V_STOP;
one-shot U_ONESHOT(HC221) Q→ULN PRESS input, R_N on OS_CLR_N,
U_OSCLR inputs DOOR_OK+STOP_REQ_N; decoder-enable gates + RAW-net
pull-downs; U_LATCHG output on KEY_LATCH_G → U_SR1.12; every §7 pull
asserted with its direction (pin_on_net to GND / N3V3).
