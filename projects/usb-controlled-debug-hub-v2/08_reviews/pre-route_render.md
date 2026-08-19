# Pre-route render review — USB-Controlled Debug Hub v2

review_stage: pre-route
review_kind: render
reviewer: Codex exact-artifact digital-twin review
reviewed_at: 2026-08-19
design_verdict: SOUND
order_verdict: BLOCKED-SOURCING
board_sha256: 876030c53811ed00841c3b809cd92d58673a80d05b2e7fa38182ec8fd97b3b26
design_rules_sha256: be908d898837e6c1d23774e5f97d0f29b5829a160e13bc45da40d42c103a2e82
top_a_render_report_sha256: eb740cdb2801724d161c2c86781839aec674c0501d7c54adeb7dfbdade2d704b
bottom_a_render_report_sha256: 88ca161da9a22ca5d40b16f45e5f34920969478f9e0dee21c6ee493d73088d63
twin_report_sha256: 69eee136676d1605eacec35bb661d19f53939632e0173e61e99595c894f004c9
orientation_receipt_sha256: f513e5238ff43e9dacc569217957770b1a145cd7a776ebb32665fb44047d0e9c
model_registration_sha256: 55a0e6e55f54cb86566b6cf3854e410f13aa9aa7fa6a84dc636a6587c0c4ade2

## Findings

- P0: none.
- P1: JLC order-preview confirmation remains mandatory for every
  single-channel rotation row, including D_PD_TVS.
- P2: none.

## Review

- The exact-board fabrication twin mounts 165/165 bodies. Native model
  registration passes all three declared groups, including both USB-C
  connectors and the new aggregate eFuse package.
- Top A-RENDER passes all 35 measurable bodies; 121 smaller bodies are named
  individually as below the declared image-resolution floor, with zero
  resolvable-but-unmeasured and zero missing-model cases. U_AGG measures
  0.101 mm centre delta and zero outward error.
- Bottom A-RENDER passes 9/9 expected bodies. Populated-minus-bare overlays
  agree with the catalog/native expected envelopes within the 1.00 mm gate.
- J_DATA and J_POWER use the approved native exact-manufacturer body because
  the catalog body has a known 2.00 mm mating-plane error. Their footprint,
  CPL datum and rotation remain independently graded and unchanged.

The rendered placement is faithful to the exact board and SOUND for routing.
Uploader previews and final routed-board render evidence remain later gates.
