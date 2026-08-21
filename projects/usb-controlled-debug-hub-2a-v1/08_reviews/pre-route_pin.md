# Pre-route physical-pin review

review_stage: pre-route
review_kind: pin
reviewer: Codex primary agent, exact-artifact physical-pin lens
context_given: full project context; this is not a fresh-context independent review
reviewed_on: 2026-08-21
board_sha256: 78e0c6a1c3c2e4435b5f478808e113000c72d606aca05e29cbb425a85f4fa1dd
parts_sha256: 7b0bf8de2f63d1996a4456d3c5c29217d357982fd39175571ce3c84c83718937
design_rules_sha256: c992b9c93edc042845555c77283c511ddfdbfbd0240550f70c99c075d4f63a31
design_verdict: SOUND
order_verdict: DO-NOT-ORDER

## Scope and result

The hash binding was refreshed after the deterministic `R_SWAP4.2` ground
dogbone and exact TVS escape-tier dossier correction.  The dogbone adds no
pin identity or net change: it connects the already-GND pad to the GND plane.
The TVS correction changes only the declared minimum manufacturable escape
tier, not the selected part, footprint, pinout, or board connectivity.

The 2026-08-21 renewal binds the same deterministic 183-part placement to
ADR-0004 and the exact promoted pre-stitch route. The U_PWR2 GND dogleg and
staggered same-net power-via bank change only routed copper; all physical pin
identities, footprints, pad numbers, and nets reviewed below are unchanged.
The later hash renewal adds only the source-owned `exclude_from_pos_files`
attribute to J_PORT1..J_PORT4; it changes no pin, pad, net, land or geometry.

The exact generated board was checked against the exact circuit JSON and all
part dossiers before routing. `pin_map_check.py` graded 29 multi-pin
references and 399 declared physical pin identities. Every declared physical
pin reaches both the schematic and the footprint; every intentional fused
land is explicit and evidenced. `electrical_invariants.py` independently
reports 55/55 exact-netlist invariants holding.

The six user-facing connectors received a separate physical-datum review.
Their native model hashes, footprint fabrication bounds, pad/drill datums,
mating-plane offsets, and local access axes are explicit in
`model_registration.yaml`. Native registration passes both connector
families, and the manufacturing twin grades P-MATE-REG 6/6. J_DATA and
J_POWER retain the exact manufacturer-backed native body because the JLC
catalog mesh puts its mating support 2.00 mm behind the exact HRO drawing;
the catalog land correspondence and CPL rotation remain independently
graded. The four USB-A connectors are deliberately manual/consigned parts,
but their exact GCT model and footprint remain in the same denominator.

The current exact machine connector-orientation subject is
`475cf8ff51ff459bd325a8cb987313a4d6f2fbbfc2ba1918bf218ba7b2f145d8`.
Machine geometry passes 6/6. Human approval is deliberately not asserted in
this review; P-ORIENT remains a separate fail-closed permission before route
spend.

## Findings and boundary

- P0: none.
- P1: none.
- P2: the review was performed by the active primary agent with full project
  context. A fresh-context final pin review remains mandatory for release.
- This verdict authorizes continued placement-stage work only. It does not
  authorize routing until the exact P-ORIENT subject is explicitly approved,
  and it does not authorize fabrication or procurement.
