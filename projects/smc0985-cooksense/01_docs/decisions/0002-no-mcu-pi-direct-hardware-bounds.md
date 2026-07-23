# ADR-0002 — No MCU: Pi-direct control, enforcement in hardware

status: accepted
date: 2026-07-22
tags: topology, protection

## Decision (user D1, supersedes brief §3.2/§3.4/§12.1)
No Pico/RP2350 anywhere. The Pi 5 drives the key shift registers
directly (DATA/CLOCK/LATCH + OE_N/RESET_N). ZERO firmware exists.
Every bound the brief assigned to firmware moves into logic:
- 74HC138 (U) + 74HC139 (D) DECODERS between register and coil
  drivers: one-hot BY CONSTRUCTION — two U (or two D) selectors
  closed is physically impossible (kills ghosting-by-bug, brief C3).
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
This ADR must emit into 03_src/rules/electrical_invariants.yaml once
refdes exist: (1) series_chain for the relay-rail authorization path
(rail reachable only through the AND-gate output); (2) pin_on_net:
watchdog WDO into the AND-chain; (3) pin_on_net: PRESS coil driven
only via the one-shot output; (4) net_has_no_part: no MCU present.
E-ADR will hold this loop OPEN until the invariants land — intended.
