# Placement, anchors, and proximity gates

## Contents

1. Electrical snap-back and physical legality
2. Proximity and protected-placement rules
3. Placement-freeze routability receipt
4. Functional-cell shadow checks
5. Promotion boundary

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

## Placement-freeze routability receipt

Physical legality is necessary but not sufficient on a dense or high-speed
board. Before placement promotion run:

```text
placement_routability_preflight.py grade PROJECT --board BOARD \
  --placement-config 03_src/placement_gates.json \
  --json 06_build/verification/placement_routability_receipt.json
```

This is a compositor inside the existing placement stage. It reuses
`placement_gates.py`, `critical_route_check.py`, and
`route_ownership_preflight.py`, then grades source-owned `route.routability`
declarations for layer roles/class eligibility and high-speed endpoint
topology. Part dossiers own the reusable classification
`layout.route_topology.kind`; `route.yaml` owns the exact footprint instance,
pads, critical pairs and reason.

Use `shunt` for a protection device whose signal pads tap distinct conductors
and whose return pads leave the signal path. Use `series_flow_through` or
`series_directional` when signal current must enter and leave through declared
banks. `require_topology: true` with no rows is a failure, not zero-row PASS.
The receipt reports declared feasibility and catches misclassified endpoints
early; structural reopening does not independently regrade its predicates, so
it cannot authorize P-FEAS promotion or claim that a global route exists. Dense
ECOs that need bounded candidate route probes remain governed by IMP-148.

## Functional-cell shadow checks

Scalar distance and body clearance can both pass while a repeated power or
interface cell is functionally backwards, locally crossed, or impossible to
escape. When those risks apply, author a board-scoped
`03_src/rules/placement_cells.yaml` contract and let
`placement_routability_preflight.py` discover it, or pass
`--functional-cells` explicitly.

The data-only `placement_cell_checks.py` library grades these independent
predicates:

| Predicate | What must be explicit or observed |
|---|---|
| Selected part and pad roles | Exact selected MPN, functional pad bank, and expected nets; the snapshot must independently observe the MPN and pads |
| Signed functional vector | Ordered anchors plus expected direction/projection, not absolute distance alone |
| Ordered local path | The intended anchor sequence and any two-terminal members; crossings and reversed chains fail |
| Simultaneous reservation | Layer, corridor/bbox and commodity for every route that must coexist |
| Constrained-pad escape | One explicit direct, dogbone, or approved selective-via-in-pad decision for every measured constrained pad |
| Critical-ground egress | A local via/trace/zone egress for every selected critical-ground pad |
| Hot-path lower bound | Authored PCB mOhm allocation plus segment length, maximum width, eligible layers, and stack copper thickness |
| Pilot/replica equivalence | Ref map, transform/tolerance, exact MPN/pad structure, semantic structure, and transformed obstacles |

Applicability is evidence-derived. A measured constrained pad or selected
critical-ground role cannot be suppressed by omitting a `require_*` flag.
Malformed applicable evidence is `INCOMPLETE`; a genuinely simple board with
no selected/applicable facts is `N-A` with a zero denominator.

Keep the evidence independent:

- the selected MPN in the contract is the expectation, not the observation;
- a missing observed footprint MPN is `INCOMPLETE`, not an assumed match;
- a `verified: true` field is not a substitute for the measured geometry it
  summarizes;
- authored obstacle, fabrication and stack facts must be hash-bound inputs;
- the hot-path check proves only a geometric copper-resistance lower bound and
  consumes the allocation from the owning electrical/power contract.

The current pcbnew adapter extracts placed part/pad geometry and accepts only
the documented obstacle, fabrication and stack snapshot additions. It does not
make the library a router, a DRC engine, or an electrical DC-bias calculator.

## Promotion boundary

Functional cells and source-preparation authority are requested in a separate
`*.shadow.json` diagnostic beside the placement-routability receipt. The live
placement grade does not execute them, hash them as authoritative inputs, or
include them in its verdict/denominator. A separately budgeted canary runner
may consume the request; never copy a shadow PASS into the main check list by
hand.

Operational isolation is part of shadow status. A missing or malformed
explicit shadow input records shadow `INCOMPLETE`; it must not raise out of the
authoritative compositor. Keep shadow diagnostics and their identity outside
the legacy placement-routability projection used to construct the P-FEAS
subject, so checker churn cannot stale a previously accepted placement. Add
them to that identity only in the same change that promotes the predicate.

The current P-FEAS stage emitter is also fail-closed: structural receipt
reopening does not rerun the seven placement predicates. It therefore writes
only a typed `INCOMPLETE` shadow result, no accepted output and no accepted
bundle.

Promote only after focused known-bad fixtures and representative USB Hub,
Pluto, and USB-controlled-debug-hub canaries establish all of the following:

1. the pcbnew adapter observes every required identity/geometry fact rather
   than echoing the authored expectation;
2. simple boards remain explicitly non-applicable;
3. existing accepted placements retain verdict, denominator and blocker
   equivalence, or each stricter result has a reviewed explanation;
4. boxed pads, crossed paths, overlapping same-layer reservations, missing
   ground egress, impossible hot paths and non-equivalent replicas fail;
5. a changed footprint, MPN, pad map, obstacle or stack invalidates reuse.

Promote the compositor predicate once and remove the corresponding duplicate
manual checklist in the same change. Until then, legacy placement admission
remains authority and a shadow mismatch triggers investigation, not override.
