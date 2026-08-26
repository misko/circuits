# Pre-route render review — USB Controlled Debug Hub v1

review_stage: pre-route
review_kind: render
reviewer: Codex independent exact-artifact 3D/render re-audit after J_UP STEP sibling repair
reviewed_at: 2026-08-16
design_verdict: SOUND
proceed_to_routing: YES — render gate only; aggregate pre-route review still controls
order_verdict: DO-NOT-ORDER
board_sha256: 523ef6c6665d4f3c91f3b073b764bf13a86ca8dd18bfacd339f597555a3b1d86
prepared_r0_sha256: 66c4b55ee1c5c59fecce2356fe86c603e32cd99d01685ae54de7b6d7c512eb26
design_rules_sha256: b2e7dee272545938667ca333de08555eed6938b854e999e68d2e69c60aa9bcc6
model_registration_config_sha256: 6a431bc7c0e6e3e65595b93216113e6a30dbd88dad40450048db140a9c3f456a
twin_adjudications_sha256: 3c0c0b8d9844cf6f17890a8fd612fb6420d8a7395e40bf45777c252844e6f77f
twin_top_4k_gate_sha256: fdf0ee6671844dcb0cbd487bfeb84cc75a50319922e1578a09f34dc2d779032b
twin_bottom_4k_gate_sha256: 742c088699613b4827c7443ee922d3f19b1ccb9e8350a994ded8bb1437a5feca
twin_iso_nw_sha256: d4ca9bcf02d431bda4656fdca7364dacaac74a88d7baa8a106f57a4dd595f85e
top_overlay_sha256: 8d7445ddb05d4bcf6bf44a491d77a64b2f35641a34da3ece9068c8662b4e3bde
bottom_overlay_sha256: 83921185ca312eeb62b2bb6bace3c45539b3220f4085f4709330e86b3b11c5bf
top_a_render_report_sha256: cf8d885e65d6493a9e98449b784c782c269a1253da759c85c121eb45629ea153
bottom_a_render_report_sha256: 225b125c0f0e436181b1b693ef41c10af39f8e10c3375d426797bca748e1d349
twin_report_sha256: caf2549036db1b39b98bb2aa4b3aa0175764bd83f6672aad04da0852a2842685
native_registration_report_sha256: ef74f53ef0aa2068a6ec22a62a0b964694b2def2783cebe2825fc9c60eb3b964
orientation_subject_sha256: 43a74ee2ddf76192c25f8e51529cdcbc9aad010cefd2362d2d4bf2945d7d553d
orientation_receipt_sha256: 7b6b96e337fcc96453c45b8086f3f5ff125141228624e9ed707192dbdf604a42
orientation_approval_sha256: 84e0858fff5f5acc2f22fece6dfdcc9d0a5c7b7cc9a11f2df3c83e453ce29a62

## Findings

- P0: none.
- P1: none.
- P2: confirm C_TRUNK_USB polarity in JLC's final order preview; its symmetric
  two-terminal render cannot independently prove polarity.

## Exact render evidence

- The regenerated populated and same-camera bare twins bind the exact board
  above. All 139/139 fitted design bodies resolve: 138 CPL placements plus the
  declared manual-install fuse-holder body.
- Top `A-RENDER` passes. It measures 30/129 expected top bodies; the other 99
  are individually named as below the declared resolvability floor, with zero
  resolvable-but-unmeasured and zero missing-model cases. All four downstream
  USB-A connectors pass. Repaired `J_UP` measures 0.347 mm centre delta and
  0.000 mm outward excursion against the 1.00 mm limits.
- Bottom `A-RENDER` passes 9/9 expected bodies with no exclusions or missing
  models. `U_ESD_UP` now measures 0.012 mm centre delta and 0.000 mm outward
  excursion; the prior opposite-side occlusion is absent.
- The J_UP adjudication changes only the twin render representation: it selects
  the exact catalog STEP, whose SHA-256 is identical to the independently
  proven project-native STEP, and records the measured plan-envelope expansion.
  It does not alter CPL position, rotation, land pattern, pin mapping or access
  direction. The combined overlays and isometric view are visually coherent;
  connector bodies, holes and board edges no longer show the former displaced
  or inverted twin.
- Fresh native `P-MODEL-REG` passes all 4/4 declared groups on the exact board.
  J_UP registers 6/6 drilled centres, 0.013 mm centre delta, 0.000 mm courtyard
  excess and 0.928 mm minimum pad margin. Its signed-Z side measurement places
  98.765% of model solid on the declared front side, above the 75% minimum.
  The repeated USB-A tuple places 94.409% on the front side and independently
  passes all 24/24 drilled centres.
- Current `P-ORIENT` machine evidence passes J_PORT1--4 facing north and J_UP
  facing west, with 1.000 model/footprint axis alignment and the authored
  mating-plane edge offsets. Independent inspection of top, outside, inside
  and orthogonal J_UP views confirms the mouth is west/outward, the rear is
  inboard and the body is on top. The explicit user approval is current and
  binds the unchanged semantic subject, all five connectors and every current
  review-image hash.

The exact manufacturing-twin render, native model registration, connector
mount side and connector access directions are SOUND as pre-route physical
evidence. This receipt does not approve routed copper, fabrication outputs,
JLC uploader choices or ordering; those remain owned by their later gates.
