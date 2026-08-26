# Final red-team layout review — USB Controlled Debug Hub v0.1.2

review_stage: release-staging
review_kind: layout-thermal-power-mechanical
reviewer: Codex fresh-context exact-artifact review
reviewed_at: 2026-08-17
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
board_sha256: c5cd719571e216224c83aca142ac84e1f11facdfb48b1bcb771c9d5b97c06e68
drc_sha256: fc54276e1ae28ee7253a52db9fe59d367fb98bd11ddd10b4a77fd2e963f4f62d
policy_audit_sha256: b828c61108116e520972291320538290479fa34d60052224943a1b78c29636db
placement_gates_sha256: 193d623edf56b9bb2b7e07e5e1c643b1a232b9adc7553613f2fd7d9c30e3860e
pad_separation_sha256: 90f400822e6cdbf76ca610346ba98c3a476e708db28129177863a1bea77ad430
reference_plane_sha256: df91c41d7eaf28f52aaabc89b65538717286369b9c61db2965463bf1574b3499
critical_route_sha256: c81030272e412d92bb7a67691d5a87416ccbff7dcb969a6e4b4009635260734b
orientation_subject_sha256: 8a7f766c33855e7c9b325d1f792f928b0fd38197eb61d7f13969415eaea65f97

## Findings

- P0: none.
- P1: none. The exact release connector-direction image set has machine PASS
  and its hash-bound human approval is recorded in `orientation_approval.md`.
- P2: the top F.Fab assembly page is too dense to serve as the sole manual
  placement/rework map; several value/ref fields overlap in the hub and power
  regions. The fabrication silk, exact twin, CPL and separate bottom assembly
  view remain usable and unambiguous, so this is an operator-documentation
  limitation rather than a board-layout defect.
- P2: retain the two evidence-backed policy dispositions: three bounded
  low-speed In1.Cu segments (9.3024 mm total, no USB copper) and track-routed
  `VBUS1_SW..VBUS4_SW`/`VBUS_CTRL`. The common 3 A rails are poured; the four
  external branches are limited to 0.5 A and require first-article hot-drop and
  thermal validation.

## Exact routed-layout evidence

- The two staged PCB copies and the project board all hash to the subject above.
  Full-severity, refilled KiCad DRC reports zero violations, zero unconnected
  items and zero schematic-parity findings.
- Placement gates pass 0 failures/0 warnings. The tightest connector
  courtyard-to-outline margin is 0.21 mm at `J_PORT1` against the authored
  0.15 mm minimum. All 139 assembled body envelopes pass body/foreign-pad
  clearance; the reported minimum courtyard gap is at least 0.100 mm.
- Pad separation grades 574 copper pads, 133481 inter-footprint pad pairs and
  214306 paste-to-foreign-copper pairs at the 0.090 mm advanced-tier floor with
  no finding.
- All ten USB critical-pair contracts are connected on their declared layers
  and via policies. Realized length grading passes all 6 declared groups/12
  members: upstream spread 0.2347 mm (0.5 mm ceiling), management 0.0030 mm
  (0.5 mm), and port spreads 0.3054/0.2139/0.4983/0.7510 mm (1.0 mm).
- F.Cu USB copper is referenced to In1.Cu and B.Cu USB copper to In2.Cu. The
  independent projected-obstacle check passes both: nearest foreign-track
  clearance is 10.7108 mm over In1 and 0.4468 mm over In2; nearest foreign-via
  clearance is 0.1616 mm and 0.2043 mm respectively, above the declared local
  limits. This is geometric reference-plane evidence, not a field solve.
- Tier preflight is consistent: the 0.46/0.20 mm via family is 8.0:1 at the
  nominal 1.6 mm board thickness against the 10:1 tier limit. The via-process
  census grades all 526 vias: 498 protected 0.46/0.20 mm Type-VII fill/cap
  barrels and 28 ordinary 0.70/0.35 mm barrels, with no partial family.
- Thermal policy passes every pad at or above 4.0 mm2 with at least two nearby
  same-net vias. The 87 via-in-pad sites are fully enumerated, including the
  USB2517 exposed-pad array; the twin and layer renders show no misplaced body
  over a thermal field.
- The common input path uses explicit `P5V_RAW`, `P5V_FUSED` and
  `P5V_PROTECTED` pours. The bounded switched-branch waiver retains at least
  0.31 mm package launches and no more than 0.8 mm of sub-0.50 mm copper per
  external branch. First-article four-wire drop and thermal testing remain the
  proof of the 25 mOhm copper/via/joint allocation.
- Silkscreen policy passes all refdes and all seven connector/fuse functional
  labels. The top render visibly distinguishes `PORT 1..4`, `UPSTREAM USB`,
  `5V INPUT`, `+5V`, `GND`, `4A FUSE`, and the supply/current warning. Bottom
  assembly orientation is explicitly mirrored and its nine fitted references
  are separable.
- Mechanical views show the four USB-A mouths on the north edge with adequate
  lateral cable spacing, the USB-B mouth on the west edge, unobstructed mounting
  holes, and no component body in either approach ray. `J_PWR` is not an
  edge-facing P-ORIENT subject; its exact registered side-entry body is at the
  southwest edge with open wire/screwdriver access and adjacent `+5V`/`GND`
  silk. The fuse-holder body and removal path are clear of the input connector.

## Remaining order and first-article gates

1. In JLC's final preview, confirm all six THT mappings and sides (`J_PWR`,
   `J_UP`, `J_PORT1..4`), every single-channel rotation listed in
   `fab/rotation_human_gate.txt`, and `C_TRUNK_USB` polarity.
2. Confirm JLC04161H-7628 stackup/90-ohm differential solve and the selective
   0.20 mm-drill Type-VII fill/cap acknowledgement before payment.
3. After manufacture, authorize first power only through the release-bound
   checklist; keep production on hold pending USB 2.0 traffic/eye testing,
   simultaneous four-port 500 mA drop, transient, thermal and connector-lot
   qualification.

The exact routed layout is SOUND for a first-article candidate. Exact connector
orientation is approved; the remaining gates are order/validation boundaries
and are not silently converted into fabrication-process approval.
