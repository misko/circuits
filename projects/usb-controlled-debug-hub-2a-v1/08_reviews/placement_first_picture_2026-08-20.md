# First placement picture — 2026-08-20

subject: `04_kicad/usb_controlled_debug_hub_2a.kicad_pcb`

stage_verdict: REVIEWABLE
route_verdict: HOLD
order_verdict: DO-NOT-ORDER

## Machine evidence

- Complete source placement: 183/183 circuit references are present and intentionally anchored.
- Generator assertions: 34/34 pad-net, connector-edge and functional pad-bank assertions pass.
- P-COLLIDE: zero inter-footprint pad overlaps and zero anchored courtyard overlaps.
- P-PINMAP: all 399 declared physical pin identities across 29 multi-pin references reach both schematic and footprint.
- P-OUT/P-CAP/P-BODYCLR: placement gates PASS with the tightest copper pad 1.72 mm inside the board edge, worst cut demand/capacity 35/536, and no sub-0.10 mm body-clearance finding.
- Placement-routability: ACCEPTED 7/7 with no N-A shortcuts: 10/10 USB differential pairs, 5/5 connector lane maps, 9/9 shunt/series endpoint topologies, four executable layer roles, 5/5 many-pad power owners and 4/4 explicit high-current paths pass on the exact board.
- Model coverage: PASS at 183/183. The exact rendered board is available as `06_build/verification/placement/renders/top_3d_150x115.png`.
- Connector orientation: machine PASS for all 6/6 edge connectors and explicit user approval is recorded for the exact semantic subject in `08_reviews/connector_orientation.yaml`.
- Native model registration: PASS for both exact connector groups (4x USB1130 and 2x TYPE-C-31-M-12). The first USB1130 run correctly exposed a 1.8 mm VRML-Y origin error; a reflected correction then made the bbox pass but visibly reversed the mouth. The final source model retains the drawing's handedness, applies the correct VRML-origin translation, passes the independent F.Fab/courtyard/pad registration gate, and shows the mouth only from the authored outside/cable camera.

## Human first-picture review

The first track-free picture has the intended architecture:

- four evenly spaced USB-A receptacles on the north edge;
- the upstream USB-C data inlet on the west edge;
- the proven hub, data-switch and control island retained in the upper half;
- the USB-C PD inlet and TPS16630 input-protection cell on the southwest edge;
- a separate 3.3 V converter followed by two visibly separate 5 V bank cells along the south edge;
- bank A is associated with ports 1/2 and bank B with ports 3/4.

The initial 150 x 135 mm outline deliberately exposed a broad routing/thermal corridor between the logic island and the two high-current banks. After reviewing the measured component extents, the user approved a conservative pre-route compaction to 150 x 115 mm: the complete southern power cluster moves north by 20 mm as a rigid group, retaining approximately 10 mm of physical separation from the logic island. Routing, current-density, and thermal proof remain required before any more aggressive compaction.

## Routing checkpoint

- The source-owned power copper and nine declared transfer banks passed the
  pre-route checks.
- All four connector-to-ESD-to-data-switch port pairs are deterministically
  connected on B.Cu.
- All four data-switch-to-hub pairs are connected. The longest P4 lane is a
  collision-checked source-owned escape; P1, then P2/P3 were routed in
  most-constrained-first order. Four immutable routing candidates are
  authenticated and accepted through `usb_hub_ports`.
- The first upstream attempt was correctly refused. J_DATA exposes four
  alternating A6/B7/A7/B6 USB 2.0 contacts on F.Cu while U_ESD_UP is on B.Cu;
  a generic multi-terminal pair cannot infer the required local crossover.
  This is a bounded launch-geometry task, not permission for more unchanged
  stochastic retries.
- The crossover was subsequently authored as a collision-checked tree and the
  proven long coupled route was promoted into the source contract. The exact
  upstream wave now skips as already connected and passes the immutable
  candidate grade. Five of eight route waves are authenticated. The next
  unresolved item is the management pair's package-local P/N handoff; its first
  attempt was refused without altering the authenticated prefix.

## Holds before remaining routing

1. Obtain a fresh human readability review of the current ten-page schematic. The duplicate schematic-placement authority was removed and the converter now emits `MODE=layout, WIRED`; the renderer passes all ten pages, but the previous first-picture approval is not bound to these current bytes.
2. Review the now-authored input, switch-node and two-bank power pours. The deterministic prep adds 56 power-transfer vias; all nine declared series banks pass the conservative 10 C-rise screen, and the prepared board has zero non-library DRC violations. Realized trace/pour resistance and loaded first-article temperature remain release gates.
3. Complete and grade the upstream USB-C duplicate-contact/ESD escape, the
   management pair, port-power branches and ordinary nets against the
   uninterrupted In1/In2 ground references. Five of eight route waves are
   currently authenticated.
4. Resolve the eight degraded automatic refdes-ownership warnings during final silk review. They are operator-legibility issues, not placement collisions.

The placement image is `06_build/verification/placement/renders/top_placement.png`.
