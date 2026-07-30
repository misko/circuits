# routing — stage 6 journal (pluto-rx2-8way)

## 2026-07-29 18:05 — start
- did: read the stage-5 handoff, `03_src/route.yaml` in full, `rules/nets.yaml`,
  ADR-0002/0006/0007, `01_docs/CHECKLIST.md` section D, and the new shared gate
  `skills/kicad-pcb/scripts/copper_length_audit.py` (+ its `--schema` and the
  60-line owed-work note at `policy_audit.py`'s R-LEN row). Mapped the RF pad
  chains off the stage-5 board with pcbnew.
- result: the board carries 11 RF50 nets on 9 radial slots. MEASURED pad map:
  ANT1 (U_SW.24 <-> J_ANT1) ... ANT7 (U_SW.17 <-> J_ANT7) and RX2_OUT
  (U_SW.22 <-> J_RX2) are each TWO-PAD nets; the RF8 radial is THREE nets in
  series through the pickoff (U_SW.19 -RX1_TAP- R_T2 -RX1_TAP_MID- R_T1
  -RX1_MAIN- J_ANT8) and `RX1_MAIN` additionally carries J_RX1.1, so it is a
  T, not a chain. So the matched set is NOT "the nine arms" as copper.
- next: FIX THE SPEC FIRST. Three sub-tasks before a single track exists:
  (1) re-derive the +/-0.10 mm arm obligation, which is 1.3 deg at 6 GHz and
  is not holdable; (2) author `length_match:` in `03_src/rules/nets.yaml`;
  (3) re-point the two E-NETREF ghost keep_short budgets on PE42482A-X.

## 2026-07-29 18:50 — iterate 1 (spec repair, no copper)
- did: (1) WITHDREW the "+/-0.10 mm ROUTED arm length" obligation everywhere the
  project stated it (`03_src/audit_board.py` I3 note, `01_docs/CHECKLIST.md`
  section D) with the arithmetic, and authored `length_match: RF_RADIAL_STAR` in
  `03_src/rules/nets.yaml` — 8 congruent radials (ANT1..ANT7 + RX2_OUT),
  `topology: chain`, `congruent_pads: true`, `no_vias: true`,
  `max_spread_mm: 1.0`. (2) Re-pointed two ghost keep_short budgets to the nodes
  their datasheet sentences are about and DELETED a third rather than re-point it
  to a net that would pass. (3) Added `audit_board.py` I8, the instrument the
  deleted budget needed. (4) Rewrote the P-ADJ-UNREACHED waiver, including the
  correction of its own false general claim.
- result: MEASURED, all from the gates themselves.
  * 13.19 deg/mm at 6 GHz on JLC04161H-7628 (eps_eff 3.350, t_pd 6.105 ps/mm,
    lambda_g 27.29 mm), so 0.10 mm = 1.3 deg — inside PE42482A-X's OWN published
    13.2 deg = 1.00 mm part-to-part window (Table 3, PDF p8) and below
    ADR-0006(d)'s ~2 deg/fillet mounting term. 1.0 mm ceiling derived from
    `dtau = TC*dT*dL*t_pd`: 1 mm = 0.05 deg over 40 degC, 20 mm = 1.05 deg.
  * WHY THE MATCHED SET IS EIGHT AND NOT NINE, from the copper and not from
    taste: ANT1..ANT7 + RX2_OUT are two-pad nets at three distinct switch-pad
    radii (2.2743 / 2.0427 / 1.9164 mm — the jacks sit on a CIRCLE, the QFN
    lands on a SQUARE), giving pad-to-pad 17.7784 / 17.9725 / 18.1021 mm,
    spread 0.3238 mm = 4.27 deg. RX2_OUT lands on the SAME 18.1021 value as
    ANT3/ANT6, so including the common-mode RFC arm widens the group by ZERO.
    The RF8 radial is excluded and ADR-0006 already said why in prose ("the
    tapped path contains two resistors and a different topology, so it is
    unequal by construction"): three nets in series, `RX1_MAIN` is a T because
    it also carries J_RX1.1 (10.3533 mm away), and its phase is set by a lumped
    2 x 220 ohm cell.
  * E-NETREF 120 sites: GHOSTS 4 -> 1. `SW_VDD` -> `{net: 3V3, anchor_pins:
    ["8"]}` graded at U_SW.8 -> C_SW1.1 = 2.873 of 3.0 (P-ADJ's tightest margin
    on the board, +0.127, and the SAME number stage 5 moved C_SW1 to x 44.7 to
    achieve by hand). ABM8 `XOUT` -> `{net: XOUT_XTAL, anchor_pins: ["3"]}`
    graded at Y_XTAL.3 -> R_XTAL.2 = 3.618 of 6.0, split at the part boundary
    (MCU leg stays on RP2040's XOUT at 3.062). `SW_LS` DELETED, not re-pointed:
    GND was available and would have measured U_SW.1 -> C_SW1.2 = 6.956 mm, a
    real number about the wrong thing, so the obligation moved to audit_board I8
    (nearest GND via within 0.5 mm of the pin-1 pad centre) which also now grades
    Y_XTAL pads 2/4 at <= 1.0 mm each with DISTINCT vias. The one surviving ghost
    is KH-SMA `RF_ANT_LAUNCH`, a generic dossier name with no near-miss, waived
    with I2/I3 as its evidence.
  * K12 8/8 member names resolve against the netlist. copper_length_audit:
    `UNREACHED R-LEN : 1 of 1 group(s) could not be measured — NOT a PASS`,
    8 member nets carry no copper. That is the correct pre-route verdict.
  * P-ADJ 32/35 graded (was 30/36 — one budget deleted, two more now gradeable),
    0 exceeded. P-ADJ-UNREACHED 3/42 (was 6/43). audit_board PASS, 8 groups,
    13 measurements, I8 UNREACHED with 0 GND vias on the board and saying so.
    policy_audit FAIL=2 HUMAN=6 N-A=11 PASS=23 WAIVED=2, unchanged — the two
    fails are still R-DRC and R-THERM, which is what routing is for.
- next: generate_rules FIRST (canon R1), then KRT.

## 2026-07-29 19:40 — stuck (D-BACK, escalated upstream)
- did: FOUR measured KRT iterations on the `rf` wave (the first wave, F.Cu only,
  no vias, per route.yaml) on the track-free prep board r0, plus one full
  six-wave chain. Configurations, all at `clearance 0.2` and the netclass-derived
  `track_width 0.36`: (1) baseline grid 0.1; (2) grid 0.1 + `--power-nets 'ANT*'
  'RX*' --power-nets-widths 0.36` with `--track-width 0.2` as the neck;
  (3) grid 0.05 baseline; (4) grid 0.05 + power-nets; plus a 4-point sweep of
  `--neckdown-length` / `--neckdown-taper-length` (0.45/0.25, 0.6/0.3, 1.2/0.5)
  at both grids. ONE PRE-ROUTE DEFECT FIXED FIRST (below).
- result: TWO INDEPENDENT STRUCTURAL WALLS, both measured, neither a
  router-tuning problem, and NEITHER FIXABLE FROM THIS STAGE. Nothing was
  imported into 04_kicad and NO chain was promoted — a route that violates
  `nets.yaml` RF50 `min_width` or fails R-LEN is not a route.

  W0 (FIXED, not a wall). `route.yaml route.common.fab_tier` was
  `jlc_4layer_advanced`. That key is KRT's OWN preset and its only legal values
  are {standard, advanced}; `route.py` exits 2 on the FIRST wave with
  `invalid choice: 'jlc_4layer_advanced'`. Fixed to `advanced` (KRT's internal
  0.25 mm via floor equals this tier's `min_via_diameter`, so nothing
  auto-escalates and no `fab_overrides` pin is needed). tier_preflight had
  printed `0 FAIL / 1 WARN — config is tier-consistent` over the invalid value,
  because PF-KRT `return`s unless the value is exactly "advanced" — an invalid
  string is indistinguishable from "standard". Skill patch proposed below.

  W1 — THE 0.36 mm IMPEDANCE WIDTH CANNOT LEAVE FIVE OF THE NINE RF LANDS, AND
  IT IS EXACT ARITHMETIC, NOT CONGESTION. PE42482A-X's vendor land (Figure 23
  inset) is 0.60 x 0.30 mm at 0.50 mm pitch, so a neighbouring GND land's near
  edge sits 0.50 - 0.15 = 0.350 mm from the RF land's centreline. A 0.36 mm
  track centred on that line needs 0.180 + 0.200 = 0.380 mm. DEFICIT 0.030 mm.
  The maximum width that can leave these lands at 0.2 mm clearance is
  2*(0.35-0.20) = 0.30 mm — exactly the pad width, ~55.3 Ohm on this stackup
  against the derived 0.36 mm / 50.5 Ohm.
  KRT reports it precisely: `ALL neighbors blocked ... Blocking obstacles:
  GND(2) ... the start/target pads are boxed in by static obstacles
  (neighboring pads + clearance), not by congestion`.
  WHICH PADS ESCAPE AND WHY: 6 of 11 rf nets route (ANT1/ANT4/ANT5 + the three
  pickoff nets), 5 FAIL (ANT2, ANT3, ANT6, ANT7, RX2_OUT). The survivors are
  exactly the pads with ONE free flank or an octilinear exit; the failures are
  pins 2/4/15/17/22, which have a GND land on BOTH flanks.
  THE VENDOR LAND ITSELF SITS AT EXACTLY THE FLOOR: pad-edge to pad-edge is
  0.200 mm against a 0.200 mm clearance, which is why DRC reports 0 clearance
  findings today and why the launch has ZERO margin BY CONSTRUCTION.
  WHAT WAS TRIED AND WHAT IT COST: KRT's power-net neck-down machinery CAN
  produce the textbook launch taper — measured on ANT5 at grid 0.1, `0.4 mm at
  0.1998 + 0.35 at 0.2 + a stepped 0.232/0.264/0.296/0.328 taper + 16.513 mm at
  0.36`. But its FALLBACK when the wide route is blocked is to re-route the
  WHOLE net at the narrow width, and which arms get the taper is
  order-dependent: across the four sweeps the same three arms came back
  variously fully-0.36, fully-0.2, or tapered. Grid 0.05 + neck 0.2 routed
  11/11 — with EVERY arm at 0.2 mm, i.e. 67 Ohm, which `generate_rules`' own
  `RF50_width` DRU rule (min 0.36mm) would then fail on every arm. There is no
  configuration that routes all nine at 0.36.
  THE RELAXATION IS REFUSED, AND FOR A MEASURED REASON RATHER THAN BY QUOTING
  route.yaml. Dropping the board clearance to <= 0.17 mm does route it, and it
  is WRONG on this board specifically: the stitch pass then places the RF
  ground-via FENCE at 0.15-0.17 mm from a 0.36 mm arm over 0.2104 mm of
  prepreg, i.e. a coplanar gap of g/h ~ 0.8. nets.yaml derives 0.36 mm = 50.5
  Ohm as PURE MICROSTRIP with no coplanar term, so a fence that close detunes
  the very number the width was chosen for. Clearance on this board is
  electrical in exactly one place — the fence gap — and that place needs it
  >= 0.2, while the launch needs it < 0.2. TWO SCOPES, and the pipeline can
  express only one: `generate_rules_generic.py` `scoped_floors:` emits a
  `track_width` constraint only, never a `clearance` one.

  W2 — AND THE DEEPER ONE: KRT IS OCTILINEAR AND THE STAR IS AT 30 DEGREES, SO
  SIX OF NINE ARMS CANNOT BE ROUTED STRAIGHT AT ALL. Every KRT segment measured
  is horizontal, vertical or exactly 45 degrees. ADR-0007's ten slots are at
  15/45/75/105/135/165/195/225/315/345 degrees; of the NINE switch radials only
  THREE (135 = ANT1, 225 = ANT4, 315 = ANT5) lie on a 45-degree multiple. The
  other six are 15 degrees off every routable direction, and the SHORTEST
  octilinear path between two points is `max(dx,dy) + (sqrt2-1)*min(dx,dy)` =
  `cos15 + 0.4142*sin15` = **1.0731 x** the straight radius:

  | arm | theta | off-45 | pad-to-pad | octilinear MINIMUM | excess |
  |---|---|---|---|---|---|
  | ANT1 (RF1) | 135 | 0.0 | 17.7784 | 17.7784 | 0.0000 |
  | ANT4 (RF4) | 225 | 0.0 | 17.7784 | 17.7784 | 0.0000 |
  | ANT5 (RF5) | 315 | 0.0 | 17.7784 | 17.7784 | 0.0000 |
  | ANT2 (RF2) | 165 | 15.0 | 17.9725 | 19.2869 | 1.3144 |
  | ANT7 (RF7) | 15 | 15.0 | 17.9725 | 19.2869 | 1.3144 |
  | ANT3 (RF3) | 195 | 15.0 | 18.1021 | 19.4259 | 1.3238 |
  | ANT6 (RF6) | 345 | 15.0 | 18.1021 | 19.4259 | 1.3238 |
  | RX2_OUT (RFC) | 105 | 15.0 | 18.1021 | 19.4259 | 1.3238 |
  | RF8 -> J_ANT8 | 75 | 15.0 | 17.8560 | 19.1618 | 1.3058 |

  So the placement's 0.3237 mm pad-to-pad spread (4.27 deg at 6 GHz) becomes a
  **1.6475 mm octilinear-MINIMUM spread = 21.73 deg**, and the 1.0 mm
  `max_spread_mm` ceiling authored this morning is **UNREACHABLE BY
  CONSTRUCTION** — not missed by a stochastic router, but excluded by the
  router's move set. CONFIRMED ON REAL COPPER: the one chain that routed all
  nine (grid 0.05, 0.2 mm arms) measures ANT1/4/5 at 17.535, ANT2 19.145,
  ANT7 19.565, ANT3/ANT6/RX2_OUT 19.772 — **spread 2.237 mm = 29.5 deg**,
  1.35x the theoretical minimum, which is the stochastic term on top.
  ADR-0007's "equal trace length is equal phase BY CONSTRUCTION" is TRUE OF THE
  PLACEMENT AND FALSE OF THE COPPER, and this is exactly the gap
  copper_length_audit.py was built to expose — on its first real run, on the
  board whose entire product is that equality.
  AND THE FIX FALLS OUT OF THE SAME TABLE, which is why this is an escalation
  and not a complaint: the nine arms form TWO TIGHT CLUSTERS — three at
  17.7784 and six spanning 19.1618..19.4259, a spread of only **0.1390 mm
  (1.83 deg) WITHIN the six**. Lengthening the three 45-degree arms by
  ~1.45 mm collapses the whole group to ~0.14 mm, which is BETTER than the
  0.3237 mm the placement starts from. Two ways to buy that:
    (a) MOVE THE THREE 45-DEGREE JACKS OUTWARD. J_ANT1/J_ANT4/J_ANT5 at
        r = 21.5 instead of 20.0 makes their straight octilinear arms
        ~19.28 mm, matching the six. It trades a placement property that does
        NOT deliver equal copper (equal RADIUS) for one that DOES (equal
        octilinear PATH). Checked, both ways it could bite: the flange gap to
        their 30-degree neighbours GROWS (chord between r=20 and r=21.5 at
        30 deg = 10.85 mm vs 10.35), and J_ANT1 stays 8.9 mm from its M3 hole
        at (24.5, 24.5) (was 10.4). It breaks `audit_board` I3's `r = 20.000`
        ring assertion, ADR-0007's R=20 derivation and the "ten centre pins on
        one circle" claim, so it is an ADR-0007 REVISION, not a floorplan tweak.
    (b) AN INTER-NET SKEW EQUALISER. copper_length_audit's own docstring
        already records that none exists ("KRT's meander machinery is
        DIFF-PAIR shaped ... Equalisation is therefore a HUMAN, ITERATIVE
        routing task"). Three deliberate 1.45 mm jogs is the whole job here,
        but there is no source-expressible mechanism to place them.
- next: STOPPED AT STAGE 6, NO CHAIN PROMOTED, `route.final:` still absent (so
  `import` stays a no-op rather than a silent wrong replay). 04_kicad carries no
  tracks and was never written to; the only committed change is route.yaml's
  `fab_tier`. The causal edge points UPSTREAM in both walls — W1 to a missing
  scoped-clearance capability in generate_rules (or an ADR that prices a
  55 Ohm launch neck), W2 to ADR-0007's angular geometry versus an octilinear
  router. FOUR SKILL/UPSTREAM PATCHES PROPOSED, NONE MADE:
  (1) `generate_rules_generic.py`: extend `scoped_floors:` (or add
      `scoped_clearance:`) to emit `(constraint clearance (min ...))` inside a
      named rule area, with the same mandatory `why:`. It is the ONLY way to
      say "0.09 inside the QFN launch, 0.2 everywhere else" from source, and
      the fine-pitch launch exemption is a general need, not this board's.
  (2) `route_and_stitch_generic.py` `_KRT_FLAGMAP`: add `neckdown_length` and
      `neckdown_taper_length`. They are the launch-taper controls; today a
      route that needs them cannot be declared in route.yaml, so such a board
      is not regenerable from source (canon M3).
  (3) `tier_preflight.py` PF-KRT: FAIL a `route.common.fab_tier` outside
      {standard, advanced}. It is the only gate that reads that string before a
      KRT cycle is spent, and it currently treats garbage as "standard".
  (4) `copper_length_audit.py` (or its canon row): record the OCTILINEAR
      FEASIBILITY BOUND. `max(dx,dy) + 0.4142*min(dx,dy)` per member is
      computable from the PADS alone, before any copper exists, and it would
      have refused the 1.0 mm ceiling at authoring time this morning instead of
      at the fifth KRT run. A ceiling below the router's own lower bound is
      unreachable by construction and should be a hard error, not a FAIL later.
