# Pre-route layout review — USB Controlled Debug Hub v1

review_stage: pre-route
review_kind: layout
reviewer: Codex independent exact-artifact layout re-audit
reviewed_at: 2026-08-16
design_verdict: SOUND
proceed_to_routing: YES
order_verdict: DO-NOT-ORDER
board_sha256: 523ef6c6665d4f3c91f3b073b764bf13a86ca8dd18bfacd339f597555a3b1d86
prepared_r0_sha256: 66c4b55ee1c5c59fecce2356fe86c603e32cd99d01685ae54de7b6d7c512eb26
route_yaml_sha256: b65a217479e1fd432413a3f440d46ce81f1fe8ff6e2a05f48a4c81a67cf59147
nets_yaml_sha256: 076104230e08f62e3957c8a788f6d7bb1ed238247a7dc9de997e494168f3a258
design_rules_sha256: b2e7dee272545938667ca333de08555eed6938b854e999e68d2e69c60aa9bcc6
mgmt_four_port_replay_sha256: ac952971bac31922aadb6fc6ed72a56c5c4afb5dba2f7bf6a68f9ccd3755c398
uncoupled_calibration_route_sha256: 4fc94d6c11454eb4ab58effe34226cd611a5c717c24c82a8f9535b93971b7d71
uncoupled_calibration_rules_sha256: 871ad391ced7bdd68c94c483833824e75cefad979e9ff7cc47f37b9fb969c6f7
orientation_subject_sha256: 43a74ee2ddf76192c25f8e51529cdcbc9aad010cefd2362d2d4bf2945d7d553d
orientation_approval_sha256: 84e0858fff5f5acc2f22fece6dfdcc9d0a5c7b7cc9a11f2df3c83e453ce29a62
a_render_top_report_sha256: cf8d885e65d6493a9e98449b784c782c269a1253da759c85c121eb45629ea153
a_render_bottom_report_sha256: 225b125c0f0e436181b1b693ef41c10af39f8e10c3375d426797bca748e1d349

## Findings

- P0: none.
- P1: none.
- P2: after final zone fill, verify the authored return via at
  (38.100,56.900) mm is connected to both inner GND planes and is no longer a
  dangling preparation item. Its net, placement and clearances are already
  correct in r0; final fill owns realized plane connectivity.
- P2: retain the JLC THT/selective-solder preview as an order-side check for
  the USB-A shell/contact holes above the bottom-side ESD devices.
- P2: extend the octilinear-floor arm of R-LEN to understand the three-pad
  shunt nets before layout seal. Its realized-copper arm measures all 12
  declared members, but the separate floor arm reports five groups UNREACHED.
- P2: retain final 15.50 mm uncoupled DRC plus first-article USB 2.0 Hi-Speed
  enumeration, eye and sustained-traffic testing. The measured guard is not a
  USB specification limit or permission for arbitrary single-ended routing.

## Exact-subject evidence

- Exact current board, semantic-rule and prepared-r0 hashes are bound above.
  Board and r0 contain identical 146-footprint, 593-pad position/net maps; the
  track-free board has 17 zones and r0 contains 321 preparation track/via
  items.
- Placement gates pass with 0 failures and 0 warnings. Tightest
  courtyard-to-outline margin is 0.21 mm at J_PORT1 against the authored
  0.15 mm minimum. Worst cut demand is 17 nets versus 346-track estimated
  capacity.
- `P-BODYCLR` grades all 139 assembled envelopes with no close/overlapping
  pair and no envelope-to-foreign-pad finding.
- `P-PADSEP` grades 574 copper pads, 133481 inter-footprint pad pairs and
  214306 paste-to-foreign-copper pairs at the declared 0.09 mm advanced-tier
  floor with zero findings.
- `P-LAND` grades 282/570 netted copper pads, including 19 scoped-width and
  39 scoped-clearance launches, with zero failures or unreachable pads.
- A fresh track-free-board DRC reports 0 violations and 375 expected open
  connections. This confirms placement geometry, but does not waive prepared
  copper checks.
- `R-PAIRMAP` contracts all 10 critical USB pairs. MGMT is explicitly assigned
  to deterministic `seed_stubs` ownership within the `usb_top` stage, on F.Cu
  with no vias. External and upstream pairs retain explicit sources, allowed
  layers and via policies. RF applicability is correctly N/A.
- The USB hub, management controller, per-port data/power cells, aggregate
  eFuse, buck converter and connector rows form distinct, routable regions.
  The two MCP2221A local capacitors now meet their placement budgets.
- `P-MODEL-REG` passes 4/4 physical-registration groups. Current `P-ORIENT`
  machine checks pass 5/5: J_PORT1--4 face north with mating-plane offset
  -0.21 mm, and J_UP faces west with offset +0.25 mm. The explicit user
  approval is present, binds the exact subject and all reviewed view hashes,
  and therefore closes the former orientation P1.
- Both promoted, exact-board A-RENDER overlays pass. The repaired J_UP twin is
  measured in the top overlay with 0.347 mm centre delta, zero outward error
  and 0.180 mm courtyard excursion, all inside the 1.00 mm gate. The bottom
  overlay measures all 9 expected bottom-side bodies and also passes.
- A fresh exact-r0 KiCad error-level DRC using the project `.kicad_dru` reports
  zero physical violations and 364 expected opens. The complete diagnostic
  report records 293 expected preparation findings only: 146 standalone-
  library notices, 28 dangling unfinished tracks and 119 dangling preparation
  vias. The prior J_UP clearance and upstream uncoupled-length P1 findings are
  closed; no clearance, width, pair-gap, uncoupled-length, edge or collision
  type remains.
- The realized-copper arm of R-LEN passes all six declared groups. Upstream
  P/N spread is 0.0010 mm against its 0.5000 mm ceiling. Prepared MGMT P is
  31.2579 mm and N is 31.2549 mm: 0.0030 mm spread against 0.5000 mm, with one
  connected component and two ends per conductor. Every external prepared
  end-to-end pair is within 0.3055 mm against 1.00 mm.
- Prepared-copper provenance is complete: all 48 pin-launched seed banks begin
  on their declared exact pin and net, all 183 expected line primitives are
  present on the declared net, layer and width, and the one additional
  anonymous bank owns the explicit GND return via.
- MGMT source ownership is now end-to-end deterministic. U_CTRL.12/13 retain
  the reviewed obstacle-constrained escape and parallel vertical runs at
  x=78.9916/78.6084 mm. From y=64.6916/64.3084 mm, the pair uses separate
  horizontal/vertical channels below the controller, reconverges beside the
  hub and lands on U_HUB.1/2 without changing logical P/N identity.
- Exact-r0 inventory finds 20 line segments per MGMT conductor, all nominal
  0.2332 mm and all on F.Cu, with zero via. R-LEN sees each conductor as one
  connected two-ended chain; KiCad reports no MGMT open, clearance, width,
  pair-gap or uncoupled-length finding. The deliberate P-side elongation closes
  the unavoidable 0.7700 mm octilinear pad-to-pad floor mismatch to 0.0030 mm
  realized skew, so the declared `elongation: meander` is demonstrated rather
  than merely asserted.
- I independently replayed the exact deterministic MGMT segments onto the
  previously routed four-port diagnostic. The hash-bound replay has zero KiCad
  physical-rule violation and zero open on MGMT_P/N or any of the eight
  P1--P4 HUB conductors. Thus the management route does not violate or block
  the already demonstrated port corridors. The replay is diagnostic evidence,
  not a promoted route artifact.
- The fully deterministic MGMT path removes a stochastic-wave dependency and
  leaves `usb_transition_ports` and `usb_upstream` as separately authenticated
  routing waves. Its source-owned copper stays in the controller/hub band and
  the narrow channel below them; the four-port replay proves that the large
  left/right field remains viable. The existing upstream handoff still ends in
  open routing space at x=39.2 mm, well outside the MGMT corridor.
- The upstream crossover preserves logical polarity and transition symmetry:
  P changes from B.Cu to F.Cu through plated J_UP.3, while N remains on B.Cu
  through the local crossover and changes once through the 0.46/0.20 mm via
  at (38.1,57.77) mm. Thus each end-to-end conductor has one B-to-F
  transition; neither net is relabelled or silently swapped.
- The F.Cu router handoff has N at y=57.770 mm and P at y=58.154 mm, retaining
  the intended order. Its final 0.5 mm is straight, parallel and collinear at
  0.3840 mm centre spacing; 0.2332 mm traces leave a 0.1508 mm copper gap,
  above the 0.145 mm DRC minimum. Both terminals end at x=39.2 mm and enter
  open routing space.
- The new 0.46/0.20 mm return via at (38.100,56.900) mm is genuinely on GND
  and spans all copper layers. It is 0.8700 mm centre-to-centre from the N
  transition via, leaving 0.4100 mm between via edges; its nearest upstream
  trace edge is at least 0.5234 mm away. Both exceed the 0.30 mm field
  clearance, and fresh DRC reports no signal-clearance finding.
- Independent DRC on the hash-bound completed upstream calibration route
  reproduces 15.2335 mm uncoupled under its former 12.75 mm rule. The current
  15.50 mm guard therefore leaves a fixed 0.2665 mm measured-route margin and
  still fails any larger regression. Because the sources cited by the design
  do not define a numeric uncoupled-length maximum, this is a legitimate
  process guard rather than a standards waiver; it does not relax clearance,
  gap, width or the separately passing 0.0010 mm P/N spread.
- F.Cu and B.Cu are respectively adjacent to continuous In1.Cu and In2.Cu GND
  zones, and both inner GND zones exist in board and r0. The explicit nearby
  return via provides the required local adjacent-plane path; the P2 above
  correctly leaves filled-zone connectivity proof to the realized route.

The component placement, approved connector orientation, model registration,
promoted twins, prepared-copper DRC and realized pair lengths are SOUND. This
is approval to proceed to routing on the exact bound subject. It is not
fabrication or ordering approval; the P2 items above remain downstream gates.
