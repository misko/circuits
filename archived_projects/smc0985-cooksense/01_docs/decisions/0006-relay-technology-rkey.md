# ADR-0006 — Relay cell: cook-hub's proven DIP05 reed default; RKEY field

status: accepted
date: 2026-07-22
tags: protection

## Decision (user D6)
Default relay = Standex-Meder DIP05-1A72-12L: ALREADY SHIPPED on
sealed cook-hub v1.0 (02_parts/DIP05-1A72-12L — paid-for prior art;
drivers + flyback pattern reusable with it). Meets brief §4.3 (SPST-NO
dry contact, >=1kV, high off-R, low off-C, 5V coil). Order-day stock
check mandatory; PhotoMOS AQY212GS recorded as the simplification
alternate for the 10 SELECTOR positions only (no coil/driver/flyback;
few-ohm Ron absorbed by RKEY) — PRESS and STOP stay REED regardless
(true mechanical open = no phantom-press leakage on the two contacts
that matter). Decide selector tech at parts stage from stock + price.

## RKEY (spec-tension T1)
Shared solder-select field 0R(default)/22/47/100/220/470/1k, 1206
pads, test points both sides, decade-box header; RSTOP separate, 0R
default. Qualification: max reliable emulation R found on the TIMER
key, fully assembled appliance, isolated interface (Gate 8).

## Amendment — 2026-07-28, v1.7: the part number is -13L, not -12L

The DECISION above is unchanged: the relay cell stays the Standex DIP05-1A72
reed, PRESS and STOP stay reed, AQY212GS stays the selector-only alternate,
RKEY is untouched. What changed is the four-character PIN-OUT CODE suffix, and
it changed because the code that was written down was never the one this board
was drawn for.

- **-12L is WRONG for this board and always was.** Pin-out code 12 (DS p.3
  sub-figure 12) has EIGHT leads: 1<->14 tied as one CONTACT node, 7<->8 as the
  other, coil on the inner pins. On this board's four-pad land that shorts
  `5V_KEY_RELAY` to `U_SEL_BUS` and every ULN2803 output to its keypad line, and
  the coil gets no holes at all. It also puts the coil/contact split ALONG the
  package at a 2.54 mm adjacent-pin boundary, so the "isolation boundary runs
  between the columns at 7.62 mm" claim ADR-0002 makes — and which the v1.1
  isolation-comb repack, i.e. the shape of the whole board, is built on — would
  have been FALSE.
- **-13L (C1524853) is the part the board was designed for.** Sub-figure 13 has
  FOUR leads: CONTACT at DIP 14<->8 (both EAST column), COIL at DIP 2<->6 (both
  WEST column). The coil/contact separation IS the 7.62 mm column spacing.
  ADR-0002's isolation claim goes from false to true with this part number.
- Every electrical fact this ADR and ADRs 0018/0021 rest on is a DIP05-1A72
  FAMILY fact and is unaffected: 5 V / 7.5 V-max coil, 500 R, 10 W / 200 V /
  0.5 A switch, 1.5 kVDC coil-contact, -20..+70 C. Those citations stand; only
  the directory they point at moved, `02_parts/DIP05-1A72-12L/` ->
  `02_parts/DIP05-1A72-13L/`.
- **The AQY212GS alternate is unaffected** (it is a different technology and
  land). **The DIP05-1A72-12D internal-diode alternate is WITHDRAWN**: it was
  approved here as "same pinout, internal diode", which was true of -12L and is
  FALSE of -13L, because 12 and 13 are different pin-out codes, not diode
  options on one code. Any internal-diode variant for this board must be a
  code-13 part read off DS p.4 and confirmed before order.
- Sourcing consequence, stated rather than inherited: JLC has C1524853 at
  stockCount **0** (fresh query 2026-07-28, controls live the same minute), so
  the hand-solder / self-supplied posture is unchanged. The DISTRIBUTOR read is
  OWED — every Mouser/DigiKey quote in `01_docs/sourcing/` is keyed to the -12L
  code and does not transfer.

Governs from v1.7. Sealed releases v1.0-v1.6 carry the -12L land and are
DO-NOT-ORDER for that reason (see CHANGELOG).
