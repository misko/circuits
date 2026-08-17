# Pre-route schematic-render review — USB Controlled Debug Hub v1

subject: usb-controlled-debug-hub-v1 exact current delivered schematic after upstream ESD equivalent-channel swap
date: 2026-08-16
reviewer: Codex independent agent (bounded same-net route delta recheck after fresh exact-PDF review)
context-given: fresh nine-page SOUND review plus inspected UP_HUB_P F.Cu route-only correction around J_UP.4/GND and J_UP.1/VBUS; exact PDF/netlist/parts hashes independently rechecked
review_stage: pre-route
review_kind: schematic_render
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
schematic_pdf_sha256: caf453be6210b81c2e6d928bbf897bed2a86d8a234769bd90f7b7ad25def9d1c
netlist_sha256: 3a03dd6c9d770c4d820ffb2b228f482adec3715ec350f65c07be13511b708662
parts_sha256: 737e094242d31f2989dca17f67f3e86c85a55bd023ef09eb2d01e04150149da2
design_rules_sha256: a07bbbdd824643533aaaed6c1f6184acffcee54d61eed61a54ed015f9e929fb6

## Verdict

All nine exact-current pages were freshly inspected as complete pages and at
high zoom after the intentional U_ESD_UP equivalent-channel swap. The drawing
is genuinely readable: page titles identify each function, symbols and pin
numbers are legible, endpoints retain visible net identity, and the sequence
teaches the design from power entry through hub/control policy to the four
repeated switched ports. The current PDF is SOUND to continue to placement.

The subsequent bounded delta translates U_ESD_UP straight away from the USB-B
lands to eliminate a same-net physical pad overlap and updates only the
corresponding route seed coordinates. Its side, rotation, pins and net
assignments remain the reviewed ones: N on IO1, P on IO2 and pin 3 on GND. The
exact PDF, normalized netlist and parts digests are unchanged, so this
PCB-geometry correction cannot alter schematic pixels or readability. The
SOUND verdict and both P2 presentation notes therefore remain applicable to
the newly bound design-rule digest.

The final bounded route correction alters only the authored F.Cu geometry of
`UP_HUB_P`: after clearing J_UP.4/GND, the same net now remains at y=59.55 mm
through x=35.5 mm before rising to its existing handoff, thereby also clearing
J_UP.1/VBUS. The connector, ESD and hub endpoints, placement, PDF, normalized
netlist and parts are unchanged. A same-net route-shape correction cannot
alter schematic pixels or their interpretation, so it does not change this
readability verdict.

## Findings

- P0: none.
- P1: none.
- P2-SR-01: On page 2 the two ground labels at J_UP pins 4 and 5 occupy nearly
  the same visual area. The pin numbers and signal labels remain legible, and
  both endpoints are intentionally ground, but separating the labels would
  make shield-versus-signal-ground presentation easier to audit at whole-page
  scale.
- P2-SR-02: Page 5 routes the AND-gate supply and ground connections around
  long page-perimeter wires. The heading and gate pin labels make the policy
  unambiguous, but local power symbols or a tighter grouping would teach the
  same circuit with less visual travel.

Neither P2 item changes the electrical reading or blocks the next stage. No
new collision, clipping, hidden pin, ambiguous crossing or unexplained NC was
found in the current artifact.

## Page-by-page review

- Page 1 presents a coherent power story: terminal, fuse, aggregate eFuse,
  protected 5 V bulk/high-frequency capacitors, and 3.3 V buck. The UV/OV,
  timer, current-limit, dV/dt, bootstrap and output-filter support networks are
  distinct and traceable.
- Page 2 groups the upstream Type-B connector, shunt ESD, USB2517I hub, VBUS
  sensing, reset, crystal/RBIAS, bypass rails and intentional-NC note. The hub
  pin bank is dense at whole-page scale but fully legible at normal zoom. The
  current equivalent-channel assignment is visible without a misleading
  polarity crossing: `UP_HUB_N` is shown at U_ESD_UP IO1 and `UP_HUB_P` at
  IO2, continuing to U_HUB UP_DM and UP_DP respectively.
- Page 3 explicitly states `P1 swapped, P2-5 normal, P6-7 disabled`. CFG,
  non-removable, swap, gang, boost and disable straps are separated into rows,
  and their rail destinations remain visible.
- Page 4 keeps the independently switched management VBUS path, MCP2221A,
  MCP23017, I2C pull-ups, resets and eight command pull-downs readable. The
  intentional-NC note clearly accounts for unused controller/expander pins.
- Page 5 shows two four-channel AND banks and states the bounded policy claim:
  power command is gated by hub policy, and data follows commanded power
  enable. All four channels remain auditable despite the sparse layout.
- Pages 6-9 use one consistent visual grammar. Each separates the data-enable
  inverter, FSUSB42 data switch, shunt ESD, TPS2557 power switch,
  current-limit resistor, local capacitors and USB-A connector. D−/D+, VBUS,
  fault and command labels remain visible without concealed pins or ambiguous
  crossings.

## Upstream and management semantics cross-check

The normalized netlist confirms the exact current upstream picture:

- `UP_HUB_N`: J_UP.2 (`D_MINUS`), U_ESD_UP.1 (`IO1`), U_HUB.58 (`UP_DM`).
- `UP_HUB_P`: J_UP.3 (`D_PLUS`), U_ESD_UP.2 (`IO2`), U_HUB.59 (`UP_DP`).
- U_ESD_UP.3 is `GND`; J_UP VBUS and both ground/shield endpoints remain
  distinct from the differential pair.

The intentional management-port swap remains disclosed rather than hidden:
U_CTRL.13 (`D_PLUS`) reaches U_HUB.1 (`DN1_DM`) as `MGMT_P`, and U_CTRL.12
(`D_MINUS`) reaches U_HUB.2 (`DN1_DP`) as `MGMT_N`; page 3 visibly straps
`HUB_SWAP1` high. The reader can therefore distinguish this deliberate hub
port configuration from the upstream shunt-channel assignment.

## Boundary

This verdict covers human readability and agreement with the exact normalized
netlist only. It does not approve electrical ratings, ESD channel equivalence,
footprints, placement, routing, impedance, connector mating direction,
thermal behavior, manufacturing output, firmware, first-article testing, or
order readiness.
