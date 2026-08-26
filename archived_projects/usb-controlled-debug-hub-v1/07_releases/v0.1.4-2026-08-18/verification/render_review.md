# Final render review — USB Controlled Debug Hub v0.1.2

review_stage: release-staging
review_kind: exact-twin-render
reviewer: Codex fresh-context visual review
reviewed_at: 2026-08-17
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
board_sha256: c5cd719571e216224c83aca142ac84e1f11facdfb48b1bcb771c9d5b97c06e68
twin_report_sha256: 47115ee38cc9861235adb7d3493aa557363781a8ea10474a7649bfbc66cd58a0
missing_models_sha256: 9d625f0879a30b8d8264fdb28b4ef43659be5f10d9cb981a9bd9aec3040836d8
twin_top_sha256: ac354b769a1a3d6f261ada631ffcc3036156daaf1f1c420289a35c2730414519
twin_bottom_sha256: cac92f60b8015c3ccefef6de35fface9f2510366b160fbe70615bef79ef220dd
twin_iso_nw_sha256: b5a86cb18a4f7476968cf4667e3a20be03744c7e31738fe06e24bdb49a0ed08a
twin_iso_se_sha256: bccdb922d26fbd7de1a8fb7dc2a09f1c07a7d18b406f0b7da56353fe575fe80f
top_overlay_report_sha256: f7a5f2cf4870f9dc6479965ae5fe66bfa945de33c7b0f0031f55102e10ce50e4
bottom_overlay_report_sha256: c126996e7e49a2d6b4a978a15245d420fa3e7744db679652c563b28dbb86e413
top_overlay_sha256: c3b20598eb0cb28d0efe81870017bfb12a04396f48571443d6f6694239ff71ec
bottom_overlay_sha256: 0899d16eb47b9cac912551a1493520c3fa00745f5b8033567340fffadba0d4e3
model_registration_stage_sha256: ccbfc3d3c53d1c77fdc942f90aa40d1949ebf6d5a137d5885469669c8da5e70f
orientation_receipt_sha256: 8a057d61d5e9f209b5c2ee168536ed63a41f02743986e4b2469d132e594a8b86

## Findings

- P0: none.
- P1: none in model placement or render registration.
- P2: `C_TRUNK_USB` is a symmetric two-pad polarized part. Its independent
  marking channel agrees with the pad fit, but the exact marking/polarity must
  still be confirmed in JLC's final assembly preview.
- P2: the plotted top F.Fab assembly page is visually congested in the central
  hub and lower-left power regions. Use the twin, functional silk, BOM/CPL and
  JLC placement preview as the operational assembly references.

## Exact twin and registration verdict

- The regenerated JLC twin is bound to the exact board hash above. It mounts
  139/139 bodies: all 138 CPL placements plus the declared manual Keystone 3568
  fuse-holder body. `missing_models.txt` is producer-generated and empty.
- The catalog fit reports 138 OK placements. The five TPS2557 exposed-pad and
  USB2517 exposed-pad multiplicity notes are numbering/granularity findings,
  not missing or displaced geometry; their body registration is independently
  PASS.
- Top A-RENDER passes 30/129 measurable bodies. The remaining 99 are all named
  below the render's resolution floor; there are zero resolvable-but-unmeasured
  and zero no-model refs. Worst reviewed connector/body registration is inside
  1.00 mm: `J_UP` centre delta 0.325 mm/outward 0.000 mm and USB-A centres
  0.219--0.233 mm/outward 0.000 mm.
- Bottom A-RENDER passes 9/9 bodies with no exclusions or missing models. The
  maximum centre delta is 0.188 mm (`U_ESD4`) and maximum outward excursion is
  0.023 mm, both inside the 1.00 mm criterion.
- Native P-MODEL-REG passes 4/4 groups: repeated USB-A, USB-B, Phoenix power
  terminal and aggregate eFuse. The exact USB models sit on the declared front
  side; no connector is inverted below the PCB.
- Top, bottom, both isometrics and edge views are mutually consistent. USB-A
  bodies share one north-facing keyed orientation, USB-B faces west, the
  Phoenix terminal and fuse holder are upright, and no opposite-side body
  occludes a connector or ESD device.
- Polarity and assembly-side cues are coherent: `J_PWR` pad 1 is the lower
  `+5V` input and pad 2 the upper `GND`; the terminal hardware itself is not
  polarized. The board's `+5V`/`GND` silk remains visible beside the populated
  body. Bottom components appear only in the bottom render and match the 9-row
  CPL side denominator.

## Human render gate

The exact connector evidence subject is
`8a7f766c33855e7c9b325d1f792f928b0fd38197eb61d7f13969415eaea65f97`.
Machine P-ORIENT passes 5/5, this fresh visual review finds the mouths and rear
shells coherent, and the user/product owner approved this exact subject on
2026-08-17. The hash-bound decision is retained in
`orientation_approval.md`. JLC polarity/rotation/THT previews remain open, so
the order verdict remains DO-NOT-ORDER.
