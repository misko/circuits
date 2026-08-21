# Pre-route topology review

review_stage: pre-route
review_kind: topology
reviewer: Codex primary agent, exact-artifact topology lens
context_given: full project context; this is not a fresh-context independent review
reviewed_on: 2026-08-20
netlist_sha256: 91a3b7ff27188f7bf4f42ef443e5f7ee31b2edc85ca53b867348b97dccfbcd87
parts_sha256: badcebfc53e8d49105a92b4d6d56db12dbff51ae0a6fd34de757eb04de796283
design_rules_sha256: dfcb459279c5e43f13926baa75656106e0f750386568aa7531679d1a8723edc5
design_verdict: SOUND
order_verdict: DO-NOT-ORDER

## Scope and result

The exact normalized KiCad netlist, all part dossiers, and the adopted rule
set named above were reviewed before replaying placement or routing. The
four-port power/data architecture is coherent and no topology defect was
found:

- J_POWER is a power-only USB-C PD sink. Raw VBUS passes through F_PD, the
  TVS/protection node, U_PD_IN, and only then reaches the two 5 V converters
  and the independent 3.3 V converter. Default 5 V and lower PDO operation is
  rejected by the input UV threshold.
- The two TPS56637 banks are separate. Bank A supplies ports 1/2 plus the
  bounded management VBUS load; bank B supplies ports 3/4. Each bank has its
  own aggregate latch-off breaker before the individual port switches.
- Each external VBUS path contains its own TPS259470A current limiter and
  always-on reverse-current block. Each connector is downstream of that
  switch; no connector VBUS bypass was found.
- J_DATA VBUS reaches only the high-impedance hub detector path. It cannot
  energize the 3.3 V rail or either 5 V bank. Its D+/D- pair reaches the hub
  through the upstream ESD network.
- Each downstream hub pair reaches exactly one FSUSB42, ESD array, and USB-A
  connector. Hardware AND gating prevents data-connect without the matching
  commanded power state. Pull states keep external power and data disabled
  until commanded.
- The port-4 switch is anchored at (132.0, 40.0) after the first placement
  attempt exposed a 56.34 mm hub-side span. The revised physical pin spans are
  below the adopted limits: both P4 hub-side lands are under 50 mm and both
  P4 connector-side lands are under 12 mm. The route contract's switch-side
  launches were translated with the anchor; no stale old-position launch is
  retained.
- Hub straps, crystal/load network, reset, management bridge/expander, and
  deliberately disabled hub ports 6/7 are explicit. Intentional no-connects
  are visible rather than inferred.

Machine evidence from the same rebuild independently reports 55/55 electrical
invariants, 128/128 surviving labels, 183/183 component-count agreement,
seven of seven power rails topology-correct, four of four 2 A external-output
claims closed, both aggregate fault envelopes closed, and zero blocking ERC
violations.

The rule digest was renewed after the placement twin added only
`assembly.yaml` representation metadata and `twin_adjudications.yaml`. The
normalized netlist, part-dossier digest, schematic PDF, and every electrical
claim above remain byte-identical. The delta selects exact native connector
bodies for rendering and records a manufacturer-authoritative inductor land;
it does not change a symbol, pin, net, component value, or fabricated pad.

## Findings and boundary

- P0: none.
- P1: none.
- P2: the review was performed by the active primary agent with full project
  context. The hash gate proves currency and verdict, not reviewer
  independence. A fresh-context final topology red-team remains mandatory for
  a release candidate.
- This verdict authorizes continued pipeline work only. It does not authorize
  fabrication, assembly, procurement, or publication.
