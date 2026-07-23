# ADR-0002 — No MCU: Pi-direct control, enforcement in hardware

status: accepted
date: 2026-07-22
tags: topology, protection

## Decision (user D1, supersedes brief §3.2/§3.4/§12.1)
No Pico/RP2350 anywhere. The Pi 5 drives the key shift registers
directly (DATA/CLOCK/LATCH + OE_N/RESET_N). ZERO firmware exists.
Every bound the brief assigned to firmware moves into logic:
- Two SN74HC238 DECODERS (U-select + D-select) between the
  register and coil drivers: one-hot BY CONSTRUCTION — two U (or
  two D) selectors closed is physically impossible (kills
  ghosting-by-bug, brief C3). See the Amendment below: the brief's
  74HC138/'139 are active-LOW and were corrected to the '238
  (active-HIGH) at the schematic stage.
- 74HC123 retriggerable ONE-SHOT gates K_PRESS: any press is
  hardware-capped <=500ms (brief §4.6) even if the Pi hangs mid-press.
- TPS3823-33 EXTERNAL watchdog supervisor: Pi daemon pets it; any
  hang drops WD_OK -> relay rail dies. Independent of all software.
- The AND-chain (brief §3.6) + discrete hardware fault latch + E-stop
  + Manual-mode physical rail cut: unchanged, all discrete.

## Accepted risk (spec-tension T6, user explicitly waived security)
A buggy/rogue Pi can press VALID keys rapidly — equivalent to a human
mashing the keypad, which the OEM controller + its interlocks are
designed to survive. Defense-in-depth loses one software layer and
gains a stronger hardware layer (decoder one-hot).

## Executable invariants (E-ADR — due at schematic gate)
This ADR must emit into 03_src/cooksense/rules/electrical_invariants.yaml
once refdes exist: (1) series_chain for the relay-rail authorization path
(rail reachable only through the AND-gate output); (2) pin_on_net:
watchdog WD_OK into the AND-chain; (3) pin_on_net: PRESS coil driven
only via the one-shot output; (4) net_has_no_part: no MCU present.
LANDED 2026-07-22 (schematic stage): electrical_invariants.yaml carries
the coil-rail series_chain (5V_PROTECTED -> Q_COIL -> 5V_KEY_RELAY), the
AND-chain output (U_AND3.4 = KEY_RELAY_ALLOWED), WD_OK into U_AND1.B, and
PRESS_TIMED (one-shot Q) into the K_PRESS driver — E-ADR loop for 0002
CLOSED. ((4) "no MCU present" stays documentary: E1 has no net_has_no_part
kind; the board simply carries no MCU footprint.)

## Amendment 2026-07-22 — decoder polarity fix (74HC138/'139 -> SN74HC238)
**Correction discovered at the schematic stage.** The brief (and the
original decision text above) named the SN74HC138 (3-to-8) + SN74HC139
(dual 2-to-4) decoders. Both are **active-LOW output** parts (the
selected one-hot output goes LOW). The coil driver is the **ULN2803A,
whose inputs are active-HIGH** (input HIGH -> the channel sinks -> the
coil energises). Feeding an active-LOW one-hot into the ULN would
energise the SEVEN NON-selected coils and leave the SELECTED coil OFF —
the exact INVERSE of the one-hot safety intent (it would short 5 of 6
keypad U-lines together instead of connecting the one selected line).

**Fix:** replace the '138/'139 with **two SN74HC238** — the
pin-compatible ACTIVE-HIGH 3-to-8 decoder (selected output HIGH). One
'238 does the 6 U-selects (Y0..Y5), one does the 4 D-selects (Y0..Y3,
A/B only, C tied GND). The one-hot-by-construction guarantee is
preserved (a 3-bit code names exactly one output); only the output
polarity is corrected so the ULN2803 energises the SELECTED coil.
'238 verified JLC-stocked; 02_parts/SN74HC238DR/part.yaml added (pinout
from the TI D2804 figure, function table confirms active-HIGH). The
now-unused '138/'139 part.yaml stay in the shared library (pruned later).
Recorded in 01_docs/journal/03_schematic_cooksense.md.
