# Pre-route layout review

review_stage: pre-route
review_kind: layout
reviewer: Codex primary agent, exact-artifact placement and routability lens
context_given: full project context; this is not a fresh-context independent review
reviewed_on: 2026-08-21
board_sha256: 78e0c6a1c3c2e4435b5f478808e113000c72d606aca05e29cbb425a85f4fa1dd
design_rules_sha256: c992b9c93edc042845555c77283c511ddfdbfbd0240550f70c99c075d4f63a31
design_verdict: SOUND
order_verdict: DO-NOT-ORDER

## Scope and result

The exact placement subject was rechecked after the six source-owned GND
thermal-connect overrides and the deterministic `R_SWAP4.2` ground dogbone
were added.  No footprint anchor, connector datum, board edge, courtyard, or
keepout moved.  The dogbone's collision-clear route is owned by the prepared
route and is separately required to survive promotion by P-ROUTEBASE.

The 2026-08-21 renewal retains every footprint anchor, outline, edge datum,
mounting hole, keepout, and model transform. It additionally verifies that
the clearance-preserving U_PWR2 dogleg and staggered port-2 power-via bank fit
the frozen placement; P-ROUTEBASE now passes over 190 footprints, 329 source
vias, and 726 prepared segments.

The final hash renewal changes only the non-geometric position-export
attribute on the four manually installed USB-A connectors. Their anchors,
outlines, courtyards, models, keepouts and mating datums remain byte-for-byte
represented by the same source values reviewed here.

The exact 150 x 115 mm, four-layer placement was reviewed as a placement and
routing-permission subject, not as a completed PCB. The four USB-A mouths form
one north-edge row; USB-C data and USB-C PD power enter separately from the
west edge. The hub/data/control island occupies the upper and central area,
while the protected PD input, 3.3 V converter, and two independent 5 V/6 A
power banks form a south-edge power row. This preserves visible separation
between the high-current conversion cells and the USB data corridors.

Machine placement evidence is clean:

- placement feasibility grades 3/3 and reports no failures or warnings;
- the tightest pad-to-outline margin is 1.72 mm against a 0.15 mm floor;
- the worst routing cut demands 35 nets against capacity for 536 tracks;
- all 183 assembled body envelopes clear foreign pads and one another, with
  the minimum reported courtyard gap at least 0.100 mm;
- every 30 declared measurable keep-short/adjacency budget resolves, and all
  pass (24/24 keep-short plus 6/6 pair budgets);
- 770 copper pads across 190 footprints pass the 0.090 mm inter-footprint and
  paste-to-foreign-copper separation gate;
- pre-route DRC classifies only three permitted isolated-copper markers, with
  zero parity findings. The 303 unrouted connections are expected at this
  stage and are not presented as routed-board evidence;
- all 183 fitted footprints have a renderer-resolvable 3D model.

The first placement attempt exposed an excessive port-4 hub-side data span.
Moving U_DATA4 and translating its authored launch geometry closed that
problem before route work: the revised route contracts keep both P4 hub-side
lands under 50 mm and both connector-side lands under 12 mm. No obsolete
launch remains at the earlier switch position.

## Findings and boundary

- P0: none.
- P1: none.
- P2: U_PWR_CTRL and U_PWR4 have the tightest reported courtyard gap
  (at least 0.100 mm). The final routed twin and assembly previews must retain
  this pair as an explicit visual inspection point.
- P2: the south conversion row is intentionally spacious enough for routing
  and thermal copper. Any later compaction would invalidate this review.
- Final power-width, via-current, reference-plane, thermal, USB length, and
  impedance checks remain route/release gates. This review does not claim
  those future results.
