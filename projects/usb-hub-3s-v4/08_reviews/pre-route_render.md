subject: USB Hub 3S v4 exact track-free placement native-render and mechanical presentation review
date: 2026-08-12
reviewer: fresh independent render/mechanical review agent (native-image lens)
context-given: exact board and design-rule digests, original-resolution top/isometric native renders, exact A-RENDER report, and board geometry; prior review verdicts excluded as authority
review_stage: pre-route
review_kind: render
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
board_sha256: e0c6e592f5063d0e7af710c3682f05cfb2f577adff22e79132ac9a84c7f8621e
design_rules_sha256: 1836747093e3a866efaae089ac787a6db42133ead8d09d0dc948c9b35a20af21
route_yaml_sha256: 8fd03f968e4f86403ae60b2e050d6b033f827b3ce1b8d737d19a0dbd827f3874
top_render_sha256: 14991062778cee2e4888696c7effa0c9ade3ed3edcf3109bf9dc5fe00be23560
iso_render_sha256: 98f313e57998b6f4e5b17612cb7bea6124f2173a3f60e2c199ad299c89140f3c
twin_overlay_sha256: d8c029533e60fbcad48aad4b5ccb021b683d677ae14937668342424204cbbab6
render_resolution_px: 2384x1680

# Independent pre-route render/mechanical review

## Verdict

No P0 or P1 render, mechanical-presentation, connector-access, polarity-mark,
silkscreen-attribution, or wrong-artifact defect was found on the exact board
and evidence bytes above. The placement is **SOUND to proceed to routing**
under this lens.

This is not an order authorization. The evidence is a native unpopulated-board
render and intentionally grants no JLC catalog-body registration, body height,
component-to-body collision, per-LCSC polarity, CPL rotation, routed-current,
production-export, or order-preview credit. `order_verdict` therefore remains
`DO-NOT-ORDER`.

- P0 findings: none.
- P1 findings: none.
- P2 limitation: catalog bodies and assembly rotations are ungraded and must
  be closed by populated-twin/assembly evidence before release.

## Complete-board and mechanical presentation

Both original 2384 x 1680 images show the complete rectangular board without
edge, land, text, connector, or corner clipping. Exact Edge.Cuts is a closed
130 x 90 mm rectangle from (20,20) to (150,110) mm. All four M3 holes are
present near the corners and unobstructed. All three fiducials are visible,
separated, non-collinear, and clear of component envelopes.

Independent exact-board placement gating corroborates the visual review with
zero failures and zero warnings: 88 assembled footprint envelopes, zero close
or overlapping courtyard pairs, zero envelope-to-foreign-pad findings, and a
minimum reported courtyard gap of at least 0.10 mm. The P-OUT exception is
only J5's intentional edge-receptacle geometry: its PCB-edge datum is exactly
at y=110.000 mm, its mechanical courtyard overhangs 0.50 mm, and its nearest
copper remains 1.70 mm inside. This gate is corroboration, not the basis of
the visual verdict.

## Connector approach and attribution

- J1's terminal entry faces the west board edge; the exterior approach is
  clear and the nearby `+ BAT`, `- GND`, and `3S INPUT` legends unambiguously
  identify the two terminals. F1 and SW1 remain accessible from above and
  their `FIT 10A MINI FUSE` and `MASTER OFF / ON` captions are unobstructed.
- J2, J3, and J4 form three evenly separated east-edge USB-A receptacle
  positions. Each mating approach is clear, each outline/pad field is fully
  shown, and `USB-A1/A2/A3 5V / 2A` maps to the adjacent connector without
  ambiguity.
- J5's Type-C mouth is aligned to the south edge with a clear cable approach.
  `USB-C 5V / 3A NO PD` is readable and directly associated with J5.

The top view also keeps `POWER ONLY — NO USB DATA` and the board identity
prominent. All 88 assembled reference designators are present on F.SilkS and
visually attributable to their own land patterns; the four holes and three
fiducials are correctly represented geometrically without requiring assembly
refdes. No obvious silk-to-pad obstruction or neighbour misidentification is
visible, including in the dense U1, U2, U9, and J5 support cells.

## Polarity and evidence boundary

J1 input polarity is explicit. The polarized C1, C17-C19, C22, and C23
footprints show clear `+` marks; the asymmetric pad-1/cathode or pin-1 marks
on D1, D5, D6, and the fine-pitch IC footprints remain visible and are not
obscured by reference text. This establishes readable fabrication-side marks,
not assembled-body orientation.

The native images omit many catalog bodies, notably the connector and other
large-component bodies. That omission is explicit in the A-RENDER report and
is not credited as body-fit, polarity, height, CPL-rotation, or order evidence.
No stale- or wrong-board cue was found: the images contain the exact v4
three-USB-A/one-USB-C power-only topology, the same 95 board footprints, four
mounts, three fiducials, connector coordinates, functional legends, and U9
cell present in the hash-matched board. The A-RENDER report is current and
PASS for exact-board geometry only; this independent human inspection, rather
than that machine verdict alone, supports `design_verdict: SOUND`.
