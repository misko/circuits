subject: pi-usb-port-switch exact pre-route placed board
date: 2026-08-15
reviewer: Codex physical-pin/package-land review
review_stage: pre-route
review_kind: pin
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
board_sha256: 168838f8e57b16581a8f54cdd4b75a85d1d5dbb1698428d281a7c07dccf14101
parts_sha256: 9f07c5382cde77e74e0f5f0c7c8396b62a9678f2a1e090422b2ac5f3d0379683
design_rules_sha256: 8bd0fe7492a4ae67bf266d9840e25c14eee8f1bda228593f36cebd87fcf97b71

# Pre-route physical-pin and package review

## Verdict and evidence boundary

The exact generated board, circuit JSON, normalized KiCad netlist, schematic,
manifest, 27 source-owned part dossiers, and the embedded footprint lands were
reviewed together. No unresolved physical-pin, package-winding, exposed-pad,
pair-polarity, connector, or intentional-pin-collapse defect was found. The
placed design is **SOUND to proceed to routing** under this lens.

This is not an order authorization. Routed connectivity, impedance, return
continuity, final DRC, fabrication outputs, JLC assembly mappings, CPL rotation,
and first-article USB operation remain downstream gates; therefore
`order_verdict` remains `DO-NOT-ORDER`.

- P-PINMAP: **PASS**, 34 multi-pin references and 436 declared physical pin
  identities graded. Every physical identity reaches the schematic and exact
  footprint; every manufacturer-fused duplicate land is explicit and evidenced.
- S-COUNT: **PASS**, board, circuit JSON, schematic, and netlist all agree with
  the manifest over 190/190 electrical references.
- Critical pair inventory: **PASS**, all 56 pairs are explicitly mapped to
  their P/N nets, USB netclass, allowed-layer set, and via policy. Core, TX,
  and USB2 paths are F.Cu/zero-via; the eight connector RX pairs alone permit
  matched F.Cu/B.Cu transitions with nearby GND return vias.

## Critical package findings

- **USB connectors J3-J10:** PASS. The four upstream Type-B and four downstream
  Type-A footprints retain the selected Wuerth contact numbering, SuperSpeed
  transmit/receive polarity, USB2 D+/D-, VBUS/GND, shell stakes, and mechanical
  holes. Shell lands remain on the authored common shield/ground policy; no USB
  signal is silently collapsed into a mounting land.
- **Population attributes:** PASS. Upstream Type-B J3/J5/J7/J9 carry exact
  JLC/LCSC code C5334230 and remain in the position file for JLC through-hole
  assembly. Downstream Type-A J4/J6/J8/J10 and F1 remain electrically present
  in the board and BOM but carry `FP_EXCLUDE_FROM_POS_FILES`, exactly matching
  the declared post-PCBA hand-solder set. This prevents an uncoded Type-A
  substitution and prevents one F1 centroid from pretending to place two
  separate fuse clips.
- **TUSB522 redrivers U2/U8/U14/U20:** PASS. Each RGE24 perimeter winding and
  exposed ground pad matches its dossier. Upstream and downstream RX/TX pair
  segments preserve P/N identity across the AC-coupling and series-component
  boundaries; shutdown/control and local 3V3 supply pins remain distinct.
- **Thermal lands and vias:** PASS. The four TUSB522 exposed-ground pads each
  carry two filled/capped GND vias. U1's large 3V3 output tab carries two
  filled/capped vias into a local B.Cu 3V3 heat spreader, so neither barrel is
  a one-layer decorative via; placement DRC reports no dangling via.
- **TS3USB221E switches U3/U9/U15/U21:** PASS. Each RSE10 land pattern preserves
  the common D+/D- and two switched branch identities, select/enable control,
  3V3, and GND. The active-low enable path is driven by the hardware interlock,
  not by a floating or firmware-dependent assumption.
- **TPD6E05U06 arrays U5/U6/U11/U12/U17/U18/U23/U24:** PASS. Each six-channel
  array preserves the connector-side USB2 and SuperSpeed signal identities and
  a dedicated GND land; no positive/negative member is exchanged.
- **TPS2557 port switches U10/U16/U22/U26:** PASS. IN, OUT, EN, fault, ILIM,
  GND, and exposed-ground lands agree with the DRB package dossier. Each output
  feeds only its matching downstream Type-A VBUS; upstream connector VBUS is
  not joined to the protected external 5 V tree.
- **Input protection and logic:** PASS. J1 retains separate positive/GND input
  terminals; F1's duplicate holder lands connect raw input to fused input; Q1's
  multi-land PowerDI drain/source/gate map implements reverse-polarity
  protection without an undocumented land collapse. The regulator, logic
  gates, MOSFETs, pull resistors, and Raspberry Pi header preserve separate
  `PWR_EN[1:4]` and `DATA_EN[1:4]` commands. Hardware AND/interlock behavior
  prevents data-on while power is off, and pulls establish a fully-off state
  for reset, unpowered, or floating Pi GPIO.

## Route-preservation obligations

Routing must not exchange P/N members, cross a redriver direction, join any
upstream VBUS to the external supply, or bypass the per-port power switch.
Core, TX, and USB2 pairs must remain on F.Cu without vias over continuous
In1.Cu GND. The eight contracted connector RX pairs may use only their short,
matched B.Cu crossovers over continuous In2.Cu between paired signal vias, with
the explicit nearby GND return vias retained. Exposed-ground lands must retain
their local return geometry.
The final connected critical-route and parity gates must independently prove
these conditions; this review does not infer them from placement.

No firmware, host daemon, or Pi utility is part of this board or this review.
