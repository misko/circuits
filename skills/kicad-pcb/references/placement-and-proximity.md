# Placement, anchors, and proximity gates

## The central fact

Every automatic placement optimizer seen so far (DeepPCB's RL placer, and
by extension anything ratline-driven) is **blind to electrical proximity
rules**. Observed: 100 nF decouplers 56–66 mm from their IC, LDO output
caps 39 mm away, VCC bypass caps 47 mm from their controllers. The
routability gains were real (measurably fewer unrouted nets) — the
electrical placement was broken. Both facts at once.

## The snap-back pass (mandatory after any auto-placement)

For each electrically-critical satellite, ring-search a legal spot 2–5 mm
from its anchor pin:

| Class | Anchor | Budget |
|---|---|---|
| Supply decouplers (100n/1u/2u2) | the IC pin they bypass | ≤ 5 mm |
| VCC/BST caps of switchers | controller VCC/BST pin | ≤ 5 mm |
| FB divider + compensation | controller FB/COMP pins | ≤ 10 mm |
| Current-limit resistors (RILIM) | the switch's ILIM pin | ≤ 8 mm |
| USB ESD arrays | their connector | ≤ 12 mm |
| TVS / local bulk | their connector/load | ≤ 20–35 mm |
| Sense-divider hold caps | ADC pin (slow/high-Z: relaxable, document) | ≤ 8–16 mm |

Auto-derive anchors when unsure: the nearest non-passive part sharing the
satellite's non-GND net.

## Ring-search placement — three legality layers (all three!)

1. Footprint bboxes + margins (courtyards).
2. Mounting-hole screw-head keepouts (~3.2 mm square).
3. **Copper under the new location** — pads must not land on other nets'
   tracks/vias. Forgetting layer 3 produced unroutable parts and
   collisions twice. Exact-collide a probe over the part's bbox on both
   layers (see `pcb_toolkit.py`).

Also: when a part moves, its routed nets are stale — rip and re-route
them, or (THT pads on zone-served nets) verify the barrel reaches a plane.

## Proximity gate

Keep a table of (satellite, anchor, budget) and assert min same-net
pad-to-pad distance ≤ budget as a build gate next to DRC. It has caught:
placement optimizers stranding decouplers, a board that silently carried
its VCC caps 47 mm out, and mis-anchored assumptions (a "C2 near U3"
check that was actually the FE snubber — auto-derive anchors from nets
to avoid encoding wrong intent).

## Protection maps for cloud placement

When sending a board out for AI placement: lock (protected=true) all
connectors, mounting holes, power FETs, inductors, controllers, bulk
caps, shunts; free only small passives and port switches. Verify the
result: zero protected parts moved, no side flips, then snap-back, then
the placement-invariant gates, then route.

## Package choice is a placement/routing decision

A 0.4 mm QFN in a dense quadrant caps its own escape count (see
autorouter-landscape.md). If a micro's quadrant is congested, the SOIC
variant of the same die routes trivially at ~90 mm² cost — same ports,
firmware unchanged; only the pin-number map changes (verify against the
datasheet, anchor-check GND/VDD/UPDI-class pins against the old netlist).
