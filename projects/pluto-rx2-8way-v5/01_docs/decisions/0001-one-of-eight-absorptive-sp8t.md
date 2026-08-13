---
id: 0001
date: 2026-08-12
status: accepted
---
# 0001 — One-of-eight absorptive SP8T architecture

## Context

The user locked a receive-only connection from one Pluto Plus RX port to at
most one of four or eight antennas, 100 MHz to approximately 5.9 GHz, with SMA
connectors and JLCPCB fabrication. D7 later selects eight antenna ports and an
independent USB-C 5 V input. RF limits, exact control/power implementations,
mechanics, assembly and test are not yet approved. D5 confirms physical AD9363
silicon running an AD9361 software profile and accepts continued operation
outside ADI's official AD9363 325 MHz–3.8 GHz range. Prior reliable 5.8 GHz use
is USER-REPORTED/INHERITED, not independently measured here, and does not
create an ADI guarantee.

## Options

- **True absorptive SP8T, N=8.** One RF stage directly implements one-of-eight.
  pSemi PE42482 is feasibility evidence: 10 MHz–8 GHz, terminated all-off,
  1.17 V minimum input-high, representative 1.1 dB typical insertion loss and
  41 dB typical isolation at 6 GHz, and 227 ns typical switching. These are
  device conditions, not board acceptance limits. JLC lists exact part
  PE42482A-X/C5121458 for Economic and Standard SMT assembly; the fresh page
  displayed 45 units on 2026-08-12. LCSC separately displayed 1500 units.
  Both counts are volatile observations only.
- **True absorptive SP4T, N=4.** One stage and five RF launches. PE42442 covers
  30 MHz–6 GHz, is 1.8 V-control compatible and supports all-off in three-pin
  mode. It is simpler only because four antenna connectors disappear; it gives
  up half the requested expansion. LCSC displayed 32 units of C470913 on
  2026-08-12.
- **Cascaded switches, N=8.** A tree of SPDTs or SP4T+SPDT can synthesize eight
  paths. PE42422 shows an individual 5 MHz–6 GHz SPDT with low typical loss,
  but each selected signal traverses multiple ICs and PCB junctions. The tree
  increases aggregate loss, route/coupling exposure, controls and transient
  state combinations. LCSC displayed 39 units of C500477 on 2026-08-12. No
  binding requirement presently justifies that complexity.
- **Alternate true reflective SP8T.** ADI ADRF5080 covers 100 MHz–20 GHz and
  has all-off, but is reflective, uses a 36-terminal LGA and has different
  supply/integration tradeoffs. It remains a technical alternate, not a
  selected part.
- **Commercial SP8T module.** Mini-Circuits USB-1SP8T-852H is a finished
  10 MHz–8.5 GHz SMA solid-state USB switch; RCM-1SP8T-12 is a finished
  DC–12 GHz SMA mechanical switch. They reduce custom RF-layout risk and are
  useful validation/benchmark alternatives. The USB module has materially
  higher module insertion loss than the bare-switch candidate, while the RCM
  is a large, costly mechanical test-system class. Either largely replaces the
  requested JLCPCB selector board rather than defining it.
- **Passive splitter.** A splitter presents multiple simultaneous coupled
  paths and unavoidable ideal division loss before excess loss. It violates
  the locked selectable one-of-N function and is rejected.

## Decision

N=8 is selected by D7. D8 continued after the leading recommendations were
presented, accepting the single true absorptive SP8T direction. Select exact
order code **PE42482A-X / JLC C5121458**. Tie LS low for binary mode and make
the passive control word `V4..V1=1000`, the documented terminated ALL_OFF
state. Do not use a cascade, commercial module or splitter unless a later
binding requirement overturns this trade.

The accepted architecture authorizes the next schematic stage after the
required stage pause. It does not authorize RF copper or fabrication.

## Consequences

This commits the design to nine SMA RF launches and a single switch
stage, while preserving a legal zero-selected state if the user requires it.
It would reduce control-state and accumulated-RF-stage complexity relative to
a cascade and preserve all eight antenna choices relative to SP4T.

Exact part, 3.3V supply, binary control/default state, JLC stackup and
provisional first-article limits are now locked in the machine contracts.
The exact route geometry, board outline, cable and instrument availability
remain open. Order-time JLC assembly eligibility and allocation must be checked
again; catalog stock is not that proof. Before release, the full
100 MHz–5.9 GHz system must be characterized at approved reference planes.
That may support an article-specific result but must never be described as
ADI-guaranteed AD9363 performance outside 325 MHz–3.8 GHz.

Primary sources:
[PE42482](https://www.psemi.com/pdf/datasheets/pe42482ds.pdf),
[JLC PE42482A-X/C5121458](https://jlcpcb.com/partdetail/Psemi-PE42482AX/C5121458),
[PE42442](https://www.psemi.com/pdf/datasheets/pe42442ds.pdf),
[PE42422](https://psemi.com/pdf/datasheets/pe42422ds.pdf),
[ADRF5080](https://www.analog.com/en/products/ADRF5080.html),
[USB-1SP8T-852H](https://www.minicircuits.com/pdfs/USB-1SP8T-852H.pdf), and
[RCM-1SP8T-12](https://www.minicircuits.com/pdfs/RCM-1SP8T-12.pdf).
