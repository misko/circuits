# ADR-0007 — bind downstream USB lane order to outward connector orientation

status: accepted for pre-route
date: 2026-08-16
tags: [usb, signal-integrity, routing, straps]

## Context

The first bounded `usb_transition` run rejected all four external hub-side
pairs.  At that point the USB-A receptacles were unknowingly rotated 180
degrees inward.  The resulting connector-side FSUSB42 paths were DRC-clean,
but they encoded the lane handedness of the mechanically invalid placement.
KRT correctly refused to cross pair members at the opposite switch banks.

USB2517I provides one `PRT_SWPn` strap per downstream port.  With
`CFG_SEL[2:0]=000`, a sampled zero associates D+ with physical DP and D- with
DM, while a sampled one reverses that association.  FSUSB42's two analog lane
channels are also electrically symmetric even though their pin labels use
plus/minus names.  Both mechanisms are valid only when the complete physical
connector-to-hub assignment is explicit.

## Options

- **Keep the inward connector placement** — rejected. Registration and DRC do
  not make a receptacle usable when its mating opening faces the PCB interior.
- **Rotate the receptacles but cross the traces** — rejected. It adds avoidable
  discontinuity and uncoupled length to all four USB High-Speed paths.
- **Rename D+/D- without binding every switch and hub pad** — rejected. It can
  hide a real polarity reversal behind apparently routable copper.
- **Use the USB2517I's documented per-port swap only where endpoint order
  requires it** — selected. The external paths preserve coupled physical
  ordering through the symmetric FSUSB42 lanes with normal hub polarity. The
  internal management path asserts `PRT_SWP1` and exchanges only the two
  physical hub-pad assignments needed to remove its geometric crossover.

## Decision

Rotate all four USB-A receptacles 180 degrees so their mating faces point
toward the north (`y0`) board edge.  Recess each mating plane approximately
0.2 mm from that edge so the complete courtyard retains at least 0.15 mm
outline margin; do not align only the through-hole contact row.

For each FSUSB42, carry logical D+ through the electrically symmetric 6-to-4
channel and D- through the 7-to-3 channel. Keep `PRT_SWP2..5` low so the four
external paths use normal physical polarity. Set `PRT_SWP1` high with the
manufacturer's 100 kOhm strap so the management path maps logical D+ to
physical DM and logical D- to physical DP:

| Function | Hub port | Physical DM pad carries | Physical DP pad carries | Strap |
|---|---:|---|---|---|
| Onboard management device | 1 | `MGMT_P` | `MGMT_N` | `PRT_SWP1=1` |
| External socket 1 | 2 | `P1_HUB_N` | `P1_HUB_P` | `PRT_SWP2=0` |
| External socket 2 | 3 | `P2_HUB_N` | `P2_HUB_P` | `PRT_SWP3=0` |
| External socket 3 | 4 | `P3_HUB_N` | `P3_HUB_P` | `PRT_SWP4=0` |
| External socket 4 | 5 | `P4_HUB_N` | `P4_HUB_P` | `PRT_SWP5=0` |

The TSX assignments, switch input/output pins, ESD channels, route seeds,
strap rails and electrical invariants must agree on every row.  `edge_faces`
must independently prove that each mating-face displacement points toward
`y0`.  The router remains forbidden from inventing pad swaps or demoting these
pairs to single-ended routing.

## Consequences

Logical USB polarity is preserved while the PCB keeps each pair coupled. The
management port's intentional physical-pad inversion is inseparable from its
high strap through executable invariants. Schematic, netlist, pin review and
placement review must be renewed whenever a pad assignment or strap rail
changes. First-article USB enumeration and eye/compliance testing remain
mandatory.

Primary authority: Microchip USB2517/USB2517I datasheet DS00001598C, Table 5-1,
Table 5-2 and Register FAh (`PRTSP`).
