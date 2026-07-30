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
