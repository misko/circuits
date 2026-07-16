# brief: xt60-usb-supply

status: in-progress
prompt_sha256: bb5ae2d40b89086de582a1ad4381d416825d4847a527278c363d67b3ca5462ab
current_release: no

## Original prompt

<!-- prompt-verbatim-begin -->
> Ok lets try out our new system. Please from scratch start a new project, and lets design a board that takes 3S lipo XT60 power as input , and outputs 3 x USB A ports (2.5A max) and 1 x USB C port (6A max). Please internally research and make all design decisions. The output should be a fully designed , placed, routed board with JLCPCB manufacturing files
<!-- prompt-verbatim-end -->

- date: 2026-07-16
- channel: Claude Code session (clean-room rerun)

## End goal — definition of done

A fabricable 4-output USB power board: 3S LiPo in via XT60, three USB-A
ports each capable of 2.5 A at 5 V, one USB-C port capable of 6 A at 5 V.
Deliverables: full project per template contracts, a placed + routed board
passing DRC with 0 violations / 0 unconnected / 0 parity issues, and a
stock-checked, twin-verified JLCPCB manufacturing package in `07_releases/`.

| # | Criterion | Source | Status |
|---|---|---|---|
| G1 | XT60 input accepting 3S LiPo (9.0–12.6 V) | P | unmet |
| G2 | 3x USB-A ports, each able to supply 2.5 A at 5 V | P | unmet |
| G3 | 1x USB-C port able to supply 6 A at 5 V | P | unmet |
| G4 | All design decisions researched and recorded internally (ADRs) | P | unmet |
| G5 | Fully placed + routed board, DRC gate green (0/0/0) | P | unmet |
| G6 | JLCPCB manufacturing files (gerbers, BOM, CPL), stock-checked, twin-verified, in an immutable release dir | P | unmet |

## Log

### A1 — 2026-07-16 — assumption (not asked)
Assumed: "2.5 A max" / "6 A max" are port CAPABILITY ratings (each port must
be able to deliver that current, and the hardware must not exceed it), not
precision per-port current-limit setpoints. Protection is provided by each
converter's cycle-by-cycle current limit plus the input fuse.
Authority: P delegates all design decisions ("Please internally research and
make all design decisions").
Escalate if: the user indicates ports must actively limit at exactly those
currents (would add per-port current-limit switches).

### A2 — 2026-07-16 — assumption (not asked)
Assumed: the USB-C port is a 5 V fixed-voltage source (no USB-PD). The
Type-C spec caps resistor-advertised current at 3 A (Rp = 10 kΩ to 5 V);
currents above 3 A legally require PD + e-marked cable, and 5 V/6 A is not a
standard PD profile at all. The port hardware (connector, copper, converter)
is sized for 6 A; the CC advertisement is 3 A.
Authority: P delegation.
Escalate if: the user wants PD negotiation or a spec-legal >3 A contract.

### A3 — 2026-07-16 — assumption (not asked)
Assumed: USB-A ports are charge-only (BC1.2 DCP: D+ shorted to D−); no data
passthrough exists (there is no upstream host).
Authority: P delegation ("outputs" ports from a battery — nothing to bridge
data to).
Escalate if: data passthrough is ever wanted.

### A4 — 2026-07-16 — assumption (not asked)
Assumed: JLCPCB economic SMT assembly for all SMD parts; the four connectors
(XT60, 3x USB-A, USB-C) are allowed to be hand-soldered / consigned if not
in the JLC assembly catalog (typical for THT jacks).
Authority: P ("JLCPCB manufacturing files") — files must be complete; parts
JLC cannot assemble get an explicit hand-solder list in the release MANIFEST.
Escalate if: the user requires 100% turnkey assembly.

## Decision register

| id | decision (one line) | decided by | depth |
|---|---|---|---|
| R1 | Ports are capability-rated, protection via converter limits + input fuse | agent (A1) | log A1 |
| R2 | USB-C is 5 V fixed, Rp-advertised 3 A, hardware sized for 6 A | agent (A2) | log A2 + decisions/0002-usbc-strategy.md |
| R3 | USB-A ports are BC1.2 DCP charge-only | agent (A3) | log A3 |
| R4 | Connectors may be hand-soldered; SMD parts JLC-assembled | agent (A4) | log A4 |
| R5 | Two-rail topology: one 5 V buck for the USB-A trio, one for USB-C | agent (P-delegation) | decisions/0001-topology.md |
| R6 | Buck converter selection | agent (P-delegation) | decisions/0003-buck-selection.md |
| R7 | Input protection: fuse + P-FET reverse polarity + TVS | agent (P-delegation) | decisions/0004-input-protection.md |
| R8 | Board: 4-layer, JLC standard tier | agent (P-delegation) | decisions/0005-stackup.md |
