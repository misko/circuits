# journal — stage 6 (routing)

## 2026-07-29 — start
- did: entered stage 6. Read CLAUDE.md build order (canon R1), SKILL.md stage 6,
  KRT CLAUDE.md, ADR-0011, `03_src/rules/nets.yaml`, `03_src/route.yaml`, the
  R-LEN canon row and `copper_length_audit.py --schema`. Then MEASURED the arm
  geometry off the placed board instead of inheriting the handoff's claim.
- result: **THE HANDOFF'S CONGRUENCE VECTOR IS THE WRONG TRANSFORM FOR COPPER,
  and the board says so in six pads.** A-SYM graded footprints and found
  "+14.5 mm translation at identical rotation"; that is TRUE for every arm part
  at y=47.750/62.250 — but ONLY because 62.250 = 2*55.0 - 47.750, i.e. for those
  parts a reflection about y=55.0 and a +14.5 translation are THE SAME MAP. The
  splitter resistors are not at those y's, and there the two maps disagree:
    LOOP_ARM1 pads  R_DELTA1.2 (64.000, 53.670)  R_DELTA3.1 (62.400, 54.550)
    LOOP_ARM2 pads  R_DELTA2.2 (64.000, 56.330)  R_DELTA3.2 (62.400, 55.450)
  +14.5 sends 53.670 -> 68.170 (nothing there). Reflection y -> 110.0 - y sends
  53.670 -> 56.330 and 54.550 -> 55.450 — EXACT, and it maps ALL 11 arm-net pads
  onto their partners with 0.000 mm error. ADR-0011's own words are "mirror
  images about the splitter axis"; the ADR was right and the placement metric's
  summary was the thing that generalised too far. Both maps are isometries, so
  either would preserve length — but only the reflection actually lands on arm 2.
- result: measured the three arm chains and they are PURE STRAIGHT LINES,
  collinear pad to collinear pad, no meander needed:
    LOOP_ARM1     R_DELTA3.1 -> R_DELTA1.2 -> U_PAD_A2A1.2   (a 3-pad net, but
                  a DAISY CHAIN with ZERO branch vertices if the delta-bridge
                  tap terminates ON the R_DELTA1.2 land)
    PAD_A2A_1     U_PAD_A2A1.5 -> U_PAD_A2A2.2   1.199 mm, horizontal
    LOOP_ARM1_SW  U_PAD_A2A2.5 -> U_SW1.1        5.903 mm, horizontal
  and the vertical trunk R_DELTA1.2 -> U_PAD_A2A1.2 is 5.920 mm on x=64.000.
- next: author `length_match:` in nets.yaml FIRST (without it R-LEN reports
  R-LEN-UNREACHED and I would route with no gate on the published property),
  then a bespoke `03_src/arm_copper.py` that lays arm 1 and REFLECTS it into
  arm 2, then KRT for the rest.

## 2026-07-29 — iterate 1 (D-BACK to stage 3, BEFORE any track)
- did: authored `length_match: RF_LOOP_D4` in `03_src/rules/nets.yaml` (canon
  R-LEN), then — before laying copper — asked a question no gate in this
  pipeline asks: **for every pad on a class with a width floor, what is the
  widest track that can LAND on it at this board's own 0.15 mm clearance
  floor?** Measured from pad geometry only: 48 approach directions x a 30 um
  grid of landing points inside each land, every other-net F.Cu pad within
  2.5 mm as an obstacle, no router involved.
- result: `copper_length_audit.py` EXIT 0, verdict **UNREACHED** — 1 of 1 group
  declared, 0 graded, `R-LEN-UNREACHED: 6 member net(s) carry no copper` —
  which is the correct verdict for an unrouted board and is the gate I now have
  that stage 5 did not.
- result: **ELEVEN PADS CANNOT ACCEPT THEIR OWN NETCLASS MINIMUM TRACK WIDTH.**

  | pad | net | class | needs | max landable | short by |
  |---|---|---|---|---|---|
  | U_SW1.5 | RX_PLUTO1 | RF50 | 0.350 | 0.250 | 0.100 |
  | U_SW2.5 | RX_PLUTO2 | RF50 | 0.350 | 0.250 | 0.100 |
  | U_MCU.47 | USB_DP_MCU | USB_DP | 0.330 | 0.300 | 0.030 |
  | U_MCU.46 | USB_DM_MCU | USB_DP | 0.330 | 0.300 | 0.030 |
  | U_MCU.10/22/26/33 | 3V3 | PWR | 0.400 | 0.300 | 0.100 |
  | U_MCU.23/45/50 | VREG_VOUT | PWR | 0.400 | 0.300 | 0.100 |

  The grid search and the exact arithmetic agree: a 0.250 mm land on 0.400 mm
  pitch puts the neighbour's copper edge 0.275 mm from the land centre, so
  w <= 2*(0.275-0.150) = 0.250; the RP2040's 0.200 mm land gives 0.300 mm.
  **THE PITCH IS THE PART — no routing and no placement change fixes this.**
  U_SW1.5/U_SW2.5 are the BGS12WN6's RFC port, the MIDDLE pad of its second
  row, with 3V3_SW and RF_CTRL_SW at +-0.400 mm. The pads that are NOT hemmed in
  need nothing: U_SW.1 (LOOP_ARMn_SW), U_SW.3 (SWn_ANT) and U_SW.4 all measure
  0.460 mm landable, so **both published loopback arms and both antenna runs
  land at their full 0.35 mm impedance width with 0.200 mm of clearance to
  spare** and no relaxation touches them.
- result: **NO GATE ASKED THIS AND THE BOARD READ AS READY TO ROUTE.**
  placement_gates PASS (0 fails 0 warns), tier_preflight 0 FAIL / 2 WARN,
  A-PROX 46/46. `escape_check` (D-ESC) models escape as a via-ring / outward-pad
  FEASIBILITY question and never compares a netclass track width against the
  land the track must terminate on. Unfixed, the board would have routed and
  produced clearance violations that read as ROUTER defects on rules that were
  unsatisfiable before the router started — the shape canon calls "a routing
  failure is usually a placement problem", one level further upstream: here it
  is a RULES problem.
- did: fixed it upstream, not at the router. `03_src/floorplan.yaml` grows three
  PERMISSIVE rule areas (`deny: []` — the documented DRU-anchor use, precedent
  cook-hub `u7_taps`; all three F.Cu-only so A-PLANE's "In1.Cu = 1 pour, 0
  keepouts" is untouched) and `03_src/rules/nets.yaml` grows `scoped_floors:`
  emitting `insideArea` width relaxations AFTER the netclass rules. The file
  previously said "NO SCOPED FLOORS, DELIBERATELY ... a width relaxation inside a
  zone would break the impedance of any RF class it touched"; that reasoning is
  still right about a BROAD relaxation and is why each floor is bounded in space
  to the land: 0.45 mm of neck at RX_PLUTOn is lambda_g/61 at 6 GHz
  (lambda_g 27.29 mm), a lumped reactance rather than a transmission line, and
  the alternative — narrowing the whole class to 0.25 mm, about 63 ohm — is the
  real impedance defect. Floors are set BELOW the measured ceiling, not at it:
  0.22 vs 0.250 (0.165 mm realized clearance) and 0.25 vs 0.300 (0.175 mm).
- result: REGENERATED, all measured unpiped. generate_board EXIT 0 — 73/73
  anchored, 24 asserts, 0 legalized, P-COLLIDE 0/0 over 306 pads, silk ownership
  65/79 owned / 14 degraded / 0 captions — **identical to stage 5, so the rule
  areas moved nothing**. audit_board EXIT 1 (I9 23/73 only, unchanged and
  reported not waived); A-PLANE PASS "In1.Cu = exactly 1 GND pour, 0 keepouts";
  A-SYM 11/11 at 0.0 um; A-PROX 46/46 0 over. placement_gates EXIT 0 PASS
  0 fails 0 warns. generate_rules EXIT 0: 6 netclasses + 41 patterns + **9**
  width rules (was 6 — the three scoped rules are present and each names a rule
  area that EXISTS on the board, so A-FIRE can fire them). count_parity EXIT 0
  4/4 over 73 refdes. status_beacon EXIT 0.
- next: `03_src/arm_copper.py` — the deterministic RF chain. See the next entry
  for why the transform is not the one the handoff named.

## 2026-07-29 — iterate 2 (route + stitch, and the M3 restructure)
- did: authored the wave plan, then RESTRUCTURED it after a coordinator
  correction. A first version had `03_src/rf_copper.py` WRITE the RF copper into
  the route-prep board before the waves. That produced identical copper and was
  still wrong: a chain whose recipe is not in `route.yaml` is a canon-M3
  violation wearing a green gate. Rebuilt as PLANNER + backend EMITTER — the
  exact split `stitch.seed_stubs` was promoted from (its own docstring cites
  usb-hub-3s `plan_seed_stubs.py` + `add_seed_stubs.py`) — so `rf_copper.py
  --emit` prints both the `stitch.seed_stubs:` stubs AND the
  `prep.keepouts.rects` corridors, and writes no copper at all.
- result: `route.common.fab_tier: jlc_4layer_advanced` made `route.py` exit 2 on
  wave 1 — KRT's `--fab-tier` is a `{standard, advanced}` PRESET, not a JLC tier
  id — while `tier_preflight` printed "config is tier-consistent" over it. Same
  defect the rx2 run hit. Fixed to `advanced`.
- result: **7/7 waves route.** 495 segments + 45 vias. First pass left 6
  routed-net opens (3V3_SW x2, USB_DM_MCU, USB_DP_MCU, VREG_VOUT x2) and 57
  hole_clearance findings at 0.220-0.225 mm.
- result: **THE 57 hole_clearance FINDINGS WERE THE RULE, NOT THE COPPER.**
  `design_rules.hole_clearance` was 0.25, taken from the tier's
  `min_hole_to_hole: 0.25` — a different specification, which stage 5's beacon
  had already flagged for J_USB's 0.225 mm boss. `fab_tiers.yaml` carries NO
  hole-to-copper key at all. The tightest hole-to-copper this board can produce
  is its own minimum via's annulus plus its own clearance,
  (0.25-0.15)/2 + 0.15 = 0.200 mm, so at 0.25 EVERY legally placed 0.25/0.15 via
  was a violation by construction. Corrected to the derived 0.200 (still 1.43x
  the 0.140 the tier's own floors imply): **hole_clearance findings 57 -> 0**,
  and PF-HTC's standing WARN closed, because `pcb_toolkit.via_site_ok`'s
  hardcoded 0.205 "assumes a 0.20 floor" and now agrees with the gate.
  `stitch.via.tiers[0].hole_to_copper` moved 0.255 -> 0.205 in the same change;
  PF-HTC had failed it in the OPPOSITE direction as "a FALSE placement wall".
  tier_preflight 1 FAIL -> **0 FAIL / 1 WARN** (was 0 FAIL / 2 WARN).
- result: KRT's power neck-down (its issue #72) emitted a taper step of
  **0.0953 mm** — below jlc_4layer_advanced's own 0.127 mm min_track, i.e. not
  manufacturable at any DRC setting. `--neckdown-taper-length 0` would stop it at
  source; at the time `_KRT_FLAGMAP` could not pass it (the coordinator reports
  it can now). Handled with `stitch.width_floor` scoped to the `taper_u_mcu` box
  and the four nets that rule area licenses.
- result: **`stitch.seed_stubs` IS UNREACHABLE THROUGH THE DOCUMENTED PIPELINE,
  and it is a one-line gap.** `p_seed_stubs` hard-dies on any filled zone ("a
  stub laid after fill is not flowed around by the pour"), and
  `import_krt.py:93` runs `ZONE_FILLER(...).Fill(...)` unconditionally — but it
  ALREADY HAS a `--no-fill` flag, and `cmd_import` simply never passes it. So
  prep unfills, import refills, and the only explicit-geometry surface in the
  backend cannot run. Measured, not inferred: stitch aborted at pass 1 twice. I
  unfilled by hand as a DIAGNOSTIC (restoring the state prep declares) to get a
  measurement; that is not a shippable path and no chain is promoted on it.
- result: with the fill state restored, **seed_stubs served 17 of 21 pins and
  REFUSED 4** — SW2_ANT, RX_PLUTO1, LOOP_ARM1 and LOOP_ARM2_SW — each because a
  wave had crossed a corridor my HAND-DRAWN keepout rects had under-reserved, one
  of them by 0.07 mm. That is the refusal doing its job. The rects are now
  EMITTED from the polylines (bounding box + half-width + 0.15 + 0.125), 21 of
  them, one per planned run, so the reservation cannot be wrong by arithmetic I
  did in my head. Re-prep + re-route: 7/7 waves again.
- result: `unify_zone_priorities` FAILED this board on a LEGAL PLANE and is
  removed with the measurement: it refused with "zones of DIFFERENT nets overlap
  ([3V3] and [GND]) — that is a SHORT". They are not a short. floorplan.yaml puts
  the In2.Cu 3V3 pour at priority 2 inside the board-wide In2.Cu GND pour at
  priority 0, deliberately and with the reason written down; distinct priorities
  are exactly how KiCad models a nested plane, and only a SAME-priority overlap
  produces the `zones_intersect` finding the pass exists to fix. This board has
  no same-net overlapping pour at all — its four GND pours are one per copper
  layer. The pass should compare PRIORITIES before calling an overlap a short.

## 2026-07-29 — stuck (D-BACK, declared): U_MCU.45 / U_MCU.50 cannot reach VREG_VOUT
- trigger: FOUR bounded attempts on the same two connections, each MEASURED and
  none better than the last:
  1. `-> C_VREGO.1` on F.Cu — both FAIL
  2. `-> C_VREGO.1` with a B.Cu hop — both FAIL
  3. `-> [108.400, 33.400]`, the nearest point of the copper the pwr wave already
     laid (1.820 mm from pin 50, 3.593 mm from pin 45) — both FAIL
  4. split at waypoints in the 0.915 mm band between the RP2040 pad ring
     (y >= 34.125) and the decoupling row (y <= 33.21): pin 45's own escape to
     [111.800, 33.650] SUCCEEDED and every span that has to travel WEST along
     that band FAILED.
- measured plateau: 2 electrical connections open. The identical waypoint split
  fixed USB_DP_MCU on the first try, so the tap threader is not the limit.
- causal hypothesis, carried UPSTREAM to placement: **eight escapes leave the
  RP2040's north side on a 0.400 mm pitch** (3V3 x4, VREG_VOUT x2, USB_DP,
  USB_DM) into a band 3.2 mm wide, which is exactly 8 x (0.25 track + 0.15
  space) — saturated, so no escape may cross another — and BOTH VREG_VOUT targets
  (C_VREGO x 107.8, C_DV2 x 106.5) sit on the FAR SIDE of the row from pin 45 at
  x 111.8. That is the `escape-corridor` CONDITIONAL `escape_check` publishes for
  a dense side, and `03_src/floorplan.yaml` declares no `escape_corridors:` at
  all. The RP2040's tier was justified on this pitch (ADR-0010) and the escape
  BUDGET was never checked against it.
- learning: the cheap upstream fix is visible and is a stage-5 change, not a
  routing one — the x-slot between C_USBV (109.1) and C_ADCV (112.8) at y = 32.5
  is EMPTY, so moving C_VREGO into it puts a VREG_VOUT land directly north of pin
  45's own escape. P-ADJ has to be re-graded with it (RP2040:VREG_VOUT is
  currently 4.30 mm of a 5.0 mm budget). Not made from inside a routing session.

## 2026-07-29 — finish (STOPPED, NOT PROMOTED): the 50-ohm width is not 50 ohm
- did: verified the coordinator's stackup finding independently, Hammerstad with
  the 1 oz copper-thickness correction, h 0.2104 mm, t 0.035 mm.
- result, MEASURED AND IT DOES NOT DEPEND ON THE Dk DISPUTE:

  | Dk | Z at w=0.35 | w for 50.00 ohm | t_pd at w=0.35 |
  |---|---|---|---|
  | 4.3 (DETAIL_DESIGN sec.1) | **51.37 ohm** | 0.3680 mm | 6.061 ps/mm |
  | 4.4 (ADR-0010's own stackup table) | **50.84 ohm** | 0.3610 mm | 6.125 ps/mm |

  My 50.84 reproduces `nets.yaml`'s own table ("0.35 -> 51.0 ohm") to 0.16 ohm,
  so THE RULES FILE IS RIGHT AND ADR-0010'S HEADLINE "0.35 mm = 50 ohm" IS THE
  NUMBER THAT IS WRONG — at EITHER permittivity. 0.361-0.368 mm is fully
  manufacturable at this tier (0.09 mm min_track), so the width that gives 50 ohm
  exists and was not taken. The sibling `pluto-rx2-8way` uses 0.36 mm on the
  IDENTICAL stackup.
- result, THE ELECTRICAL COST OF THE ERROR, so the decision is not made on
  outrage: 50.84 ohm is |Gamma| 0.0086 = **41.3 dB return loss, VSWR 1.017** —
  two orders of magnitude below the SMA launch's own contribution. It is a
  documentation-consistency defect first and an RF defect a distant second.
- result, AND THIS IS THE PART THAT MATTERS FOR THE RELEASE ARTIFACT: **the
  published DELTA is untouched.** The arm spread is 0.000000 mm by construction,
  and 0.000000 mm x any conversion constant is 0.000 ps. ADR-0011's 6.0 ps/mm
  being 2.0% low (6.125 measured at Dk 4.4, w 0.35) moves only the per-arm
  ABSOLUTE: 16.080266 mm reads 96.48 ps at 6.0 and 98.17 ps at 6.105, a 1.69 ps
  difference on a number the release publishes per arm.
- STOPPED HERE, DELIBERATELY, AND NO CHAIN IS PROMOTED. Changing the RF class
  width is a change to ADR-0010's published impedance constant and ADR-0011's
  published conversion constant. That is a SCOPE change, not a routing fix, and
  the instruction on a scope change is to report rather than decide. Promoting a
  chain at 0.35 mm now would seal a width the board's own rules file contradicts,
  and re-racing after the width changes is cheap while a superseded release is
  not.
