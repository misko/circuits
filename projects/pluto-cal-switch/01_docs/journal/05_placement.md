# journal — stage 5 (footprints + placement)

## 2026-07-28 12:05 — start
- did: intake for STAGE 5. Read CLAUDE.md, skills/pcb-design/SKILL.md (4-6 + D-ADJ +
  archetypes + LAYOUT PRECEDENT SEARCH), skills/kicad-pcb/references/{floorplan-archetypes.md,
  layout-precedents.md,fab_tiers.yaml}, 01_docs/{BRIEF,ARCHITECTURE,DETAIL_DESIGN}.md,
  16 ADRs, STATUS.md, journal tails, 02_parts/, 03_src/, every contracts.md, and
  `git show a1d12eb` (stage 4).
- result: the footprint denominator is MEASURED off the committed 04_kicad/pluto_cal_switch.kicad_sch,
  not assumed: 73 components carry 21 distinct FPIDs — 17 in `pluto_cal_switch:` (NONE of which
  exist; 03_src/lib/pluto_cal_switch.pretty/ does not exist at all) and 4 stock KiCad
  (Capacitor_SMD:C_0402_1005Metric x22, Resistor_SMD:R_0402_1005Metric x10,
  Capacitor_SMD:C_0805_2012Metric x3, Fuse:Fuse_1812_4532Metric x1). The 64
  footprint_link_issues in the ERC warnings resolve to those 17 project FPIDs.
- next: grade each of the 17 against its datasheet land drawing and decide
  ADOPT-STOCK vs AUTHOR per footprint, then floorplan.

## 2026-07-29 — WIP CHECKPOINT (new session; the previous one was killed mid-flight)
- did: the 2026-07-28 stage-5 session was terminated by an API spend limit after its
  `start` entry and before any `iterate`. It left ~20 uncommitted files. INSPECTED
  them all before touching anything, and the verdict is KEEP AND COMMIT AS-IS:
  * `03_src/lib/pluto_cal_switch.pretty/` — SEVEN authored land patterns, each
    carrying its derivation in its own `descr` (vendor sheet, figure number, and
    the number the geometry answers). Non-empty, self-documenting, and the
    denominator matches: 7 project FPIDs are named by the netlist and 7 files exist.
  * 11 of 12 STOCK adoptions carry a `FOOTPRINT ADOPTED ... AND HERE IS THE
    COMPARISON` gotcha in their own part.yaml, with the vendor drawing number and
    the per-dimension land-vs-outline delta. The 12th (MINISMDC050F-2,
    Fuse:Fuse_1812_4532Metric) has NO comparison — that is this session's debt,
    recorded here rather than discovered later.
  * `03_src/floorplan.yaml` — full placement: 73 anchors, `require_anchor: true`,
    no seeds and no region placement at all, 4 zones, 14 silk captions, 26 pad_net
    asserts + 1 pad_order. Identity is THIS board (`project.name: pluto_cal_switch`).
  * `04_kicad/` output — COMMITTED, not discarded, and here is why the "regenerable,
    so misleading" argument does not apply: the artifact is COMPLETE, not half
    written. 77 footprints (73 refdes + 4 mounting holes), 15 zones, ZERO track
    segments — which is exactly the shape a pre-routing stage-5 board should have.
    04_kicad/contracts.md says generated output is "committed anyway, because a diff
    on a generated .kicad_pcb is how a generator bug becomes visible"; withholding it
    would delete that diff for no gain.
- result: nothing from the killed session is discarded and nothing is re-derived.
  The spend already paid is banked as the baseline my own gates will be measured
  against.
- next: re-run the gate chain from step [3] to find out what is actually true about
  this placement, since NO gate output from the killed session survives.

## 2026-07-29 — iterate: the gates disagreed with the source in SIX places
- did: re-ran the chain from step [3] on the checkpointed placement. The board
  GENERATED clean on the first try (73/73 anchored, 24 asserts, 0 pad shorts) —
  and then every measuring gate found something the source was asserting falsely.
- result, in the order the gates found them:
  1. **A-SYM FAILED on all 11 arm pairs: "+14.500 is 4.000 mm off the required
     +18.500".** floorplan.yaml's banner, its segment table and audit_board.py's
     ARM1_Y/ARM2_Y all said the arms were 18.5 mm apart; the ANCHORS said 14.5.
     THE CHECKER WAS WRONG AND THE ANCHORS WERE RIGHT, and it took a derivation
     rather than a coin-flip to establish it: the separation is bounded ABOVE at
     14.66 mm by YAT-10A+'s own 6 mm GCPW-launch keep_short (the drop from
     R_DELTA1's arm pad at y=53.67 to U_PAD_A2A1's RF-IN is that net) and BELOW
     at 13.85 mm by the authored SMA courtyard (+/-3.90, jack hanging 9.40 mm
     below its switch). 18.5 IS OUTSIDE THAT WINDOW AND ALWAYS WAS: it blew a
     datasheet launch budget by 1.92 mm to buy coupling margin on a constraint
     already met 23x. Banner, segment table and checker constant all corrected to
     14.5 WITH the derivation written in. A-SYM now PASSES at 0.0 um of error.
  2. **A-PROX: 4 budgets over, 2 NOT EVALUATED — and every one was a STALE NET
     NAME from stage 4's re-spec, not a placement fault.** YAT-2A+ still budgeted
     LOOP_ARM1/2, nets no YAT-2A+ instance has a pad on since A9 split each arm
     pad into two chips; the budget belonged on YAT-10A+, and once moved there the
     checker used the pin-anchored metric instead of a full-net-span fallback and
     read 5.92 vs 6.00. YAT-10A+'s LOOP_IN named a net stage 4 merged out of
     existence. RP2040's VREG_VIN named a PIN, not a net. All re-pointed at
     source. THE ONE REAL PLACEMENT DEBT the re-pointing exposed: YAT-2A+'s
     RF-OUT launch into the switch ran 8.00 mm against its own 6 mm budget, and
     DETAIL_DESIGN sec.2 ASKS for 8. Two of this board's own documents in direct
     conflict; the launch budget wins (sec.2 feeds a loss budget ADR-0016 credits
     at ZERO, a blown launch degrades the RL the pad's 30 dB rests on), so both
     switches and everything hanging off them moved +2.10 mm in x TOGETHER.
     44/44 budgets now measured, 0 over, 0 unevaluated.
  3. **THREE RP2040 SUPPLY CAPS WERE PLACED AGAINST PIN NUMBERS THAT ARE NOT THE
     PINS THEIR OWN COMMENTS NAMED.** "C_VREGI: 1 uF at VREG_VIN (pad 23 area)" —
     pad 23 is DVDD; VREG_VIN is pad 44, on the opposite EDGE. Same for C_VREGO
     (pads 45/50 are NORTH, cap was SOUTH) and C_ADCV (pad 43, 5.9 mm away).
     Invisible to ERC, to the netlist and to every render; it surfaced as
     A-PROX RP2040:3V3 = 4.84 mm against a 4.0 mm budget with SIX of ten 3V3 pins
     over. Rebuilt as four edge rows whose coordinates come from MEASURED
     courtyards (0402 = 1.91 x 1.01, QFN-56 = 8.35 sq), with a 2.1 mm gap left
     open in the north row as the USB pair's escape corridor. U_FLASH had to move
     to make the north row exist at all — the U_FLASH-to-U_MCU gap was 1.58 mm and
     a rot-90 0402 needs 1.91.
  4. **Y1 at rot 90 put pad 1 (XIN) on the FAR side of the case from the MCU** —
     XIN measured 6.28 mm against RP2040's 6.0. rot 270 costs nothing (a 4-pad
     3225 is symmetric in copper; only the numbering turns over) and gives 4.27.
     R_XTAL was on the far side of the crystal from the pin it damps: 7.20 mm on
     XOUT, now 3.17.
  5. **ALL FIVE SMA PORT CAPTIONS WERE AIMED AT THE PREVIOUS GEOMETRY** — "ANT1"
     5.0 mm from J_SMA_ANT1, "RX1" 9.8 mm from J_SMA_RX1. On a board with five
     IDENTICAL jacks that is worse than no caption: a confident label pointing at
     the wrong port, and plugging into the wrong one is SILENT. Re-aimed, and a
     new gate (I10) now grades them by name so they cannot drift again.
  6. **THE FOUR HEADER TERMINAL LEGENDS WERE OFF BY ONE PIN.** J_HDR's origin is
     PAD 1, so its pads sit at y = 52.00/54.54/57.08/59.62; the legends were at
     46.00/48.54/51.08/53.62. "G" labelled bare board 6 mm above pin 1 and each
     other legend sat beside the pin BEFORE the one it named — on the one UNKEYED
     entry on the board, carrying a 5.0 V ceiling and a control input. Fixed, and
     the whole header cluster moved -5.00 mm rigidly to make room for the legends
     at the height the silk stroke rule requires.
- next: the silk stroke floor, the DRC classification, and the two gates that are
  red for reasons upstream of this board.

## 2026-07-29 — iterate: silk, and 58 -> 35 DRC
- did: applied the 2026-07-29 fab_tiers change (min_silk_stroke 0.1125, and the
  corollary that reaching JLC's published 0.15 needs >= 0.60 mm text), then
  classified every DRC finding rather than counting them.
- result:
  * **THE 0.60 mm RULE IS NOT ENOUGH ON THIS GENERATOR, MEASURED.** Caption stroke
    comes out as max(0.1125, 0.13, height x 0.16), so 0.60 -> 0.13, 0.70 -> 0.13
    and 0.80 -> 0.13, ALL BELOW 0.15. The first height that actually reaches
    0.15 is 0.9375. Every stress-read caption is therefore 1.0 (-> 0.160) or 1.2
    (-> 0.192): 16 captions, 0 below 0.15. The 73 refdes stay at 0.60/0.120 —
    above the ENFORCED 0.1125 floor, below the published 0.15, and that is the
    right call because a refdes is read at leisure with a BOM in hand and is
    duplicated on F.Fab.
  * **DRC 58 -> 35, and all 35 are CLASSIFIED with a named owner. Parity is 0.**
    - 7 SILK findings were MINE and are FIXED IN THE FOOTPRINTS: the switch's four
      silk side-verticals were drawn from each corner inward THROUGH its own pads
      (the break was cut on the wrong axis); the USB micro-B drew a line across
      its MOUTH, which sits flush to the board edge, putting silk 0.05 mm inside
      Edge.Cuts.
    - 16 CLEARANCE findings, every one INSIDE a footprint at exactly 0.150 mm:
      14 in the two BGS12WN6 lands (Figure 5: 0.25 mm lands on a 0.40 mm grid) and
      2 in the TPD2E2U06's SOT-553. A DRC floor of 0.200 is STRICTER THAN A
      DATASHEET LAND THE BOARD IS REQUIRED TO USE — unfixable by routing or
      placement. default_clearance and all six netclasses now declare 0.15
      explicitly (which is also what PF-RULES-CLR was asking for), route and
      stitch clearance match it, and all 16 are gone.
    - 30 solder_mask_bridge = 15 pad pairs x 2 BGS12WN6, i.e. the SINGLE mask
      opening the footprint deliberately carries because the 0.15 mm land gap is
      below JLC's 0.2 mm mask-dam minimum. A declared fab deviation with its
      evidence already in the footprint's descr. STAGE 7.
    - 2 starved_thermal (U_ESD.2, Y1.4) + 1 isolated_copper (the In2.Cu 3V3
      region pour) + R-THERM U_MCU.57(0 vias): all four need STITCHING. STAGE 6.
    - 2 hole_clearance: J_USB's D0.55 locating-boss NPTH sits 0.225 mm from pads
      1 and 5 against a 0.250 floor. Both geometries are VENDOR-FIXED. Recorded in
      02_parts with the three things that are genuinely unresolved, including that
      the 0.250 floor is derived from the tier's HOLE-TO-HOLE number, which is not
      the same specification as hole-to-copper.
  * **tier_preflight went 2 FAIL -> 0 FAIL.** PF-NORM would have inflated every
    correctly-sized 0.25 mm tier via to 0.6 mm collision-unchecked (crow-rv2:
    323/323 vias, then 902 findings); normalize_vias is re-aimed at the tier floor.
    PF-STITCH-CLR and PF-HTC closed. The 2 remaining WARNs are a declared
    generator gap with no config fix (astar_fallback's hardcoded hole_to_copper)
    and legalize.clearance, which is inert here at 0 floating parts.
- next: two gates stay RED and neither is waived. Report and stop before routing.

## 2026-07-29 — finish: STOPPED at the declared pre-routing boundary
- did: full sweep. STOPPED before any routing attempt, as instructed.
- result: **A-POL 205/205, A-SYM 11/11 at 0.0 um, A-ARMSEP 14.500 mm (23x),
  A-DELTA 0.860/1.330 vs 1.385, A-ANTIPAD 5/5, A-PLANE 1 pour 0 keepouts,
  A-RFSEP 9.00 mm vs 8.0, A-SEG 14/14, A-PROX 44/44 0-over 0-unevaluated,
  I8 73/73, I10 5/5 (tightest 2.57 mm).** P-COLLIDE 0/0 over 306 pads.
  placement_gates PASS (P-OUT tightest 1.65 mm; P-CAP worst cut ratio 0.02 vs a
  0.5 fail line — corridor capacity is not this board's problem).
  import_provenance 18/18. tier_preflight 0 FAIL / 2 WARN. count_parity 4/4 over
  73 refdes. contracts_audit 244 files 0 violations. policy_audit FAIL=4 HUMAN=6
  N-A=11 PASS=20 (was FAIL=2 PASS=9 at the schematic gate; the denominator grew
  because a board file now exists to grade).
- **TWO GATES ARE RED THAT COULD HAVE BEEN MADE GREEN AND WERE NOT:**
  * **I9: 39 of 73 refdes labels are nearer another part than their own** (worst:
    J_SMA_RX1's label 7.06 mm from its own courtyard and 1.05 mm from U_SW1). This
    gate is NEW — I wrote it this stage — and it is red on its first run, which is
    the honest outcome. The cause is upstream and is not this board's placement:
    the shared silk placer walks a fixed offset ladder out to 11 mm and takes the
    FIRST non-colliding slot, with NO ownership test. I cannot patch skills/ this
    session. Exposure is bounded — every refdes also exists on F.Fab at its own
    part's origin and the CPL, not the silk, is what the assembler consumes — so
    this is a human misreading a physical board, not an assembly-yield defect.
    Waiving it or loosening the metric would be the silent downgrade. NOTE the
    metric WAS corrected once, and in the strict direction of honesty: it started
    as centroid distance, which penalised big parts for being big and called the
    "RX1" caption a misattribution because a neighbouring 0402's centre was 0.8 mm
    nearer than a 5-hole jack's centroid. Courtyard-EDGE distance is how a human
    reads a label, and it rescued ZERO of the 39 genuine failures.
  * **P-ADJ: LOOP_SPLIT span 5.5 mm > 2.5 mm** and 20 more like it. P-ADJ measures
    FULL NET SPAN, which is the metric audit_board's own A-PROX docstring calls
    wrong and explains why: on this board it reports RP2040:3V3 at 72.96 mm
    against a 4 mm budget, because a rail crosses the board, which is what rails
    do. The SAME 44 budgets measured with the pin-anchored metric are 44/44 PASS.
    The fleet pattern for this gate is a waiver — policy_audit's own source notes
    that both boards carrying keep_short budgets hold one — and a waiver copied
    without re-deriving its evidence is an inherited defect (M4). NOT WAIVED.
  * (S-OCCL 23 and R-DRC 35/108 are unchanged in kind from the schematic gate:
    S-OCCL's evidence is a stage-7 render review, and 108 unconnected is what an
    unrouted board looks like.)
- **E-ADR RE-MEASURED AND IT IS GREEN: 10/10.** The stage-5 brief said to expect
  11/12 and to leave the declared O8b gap red. It is not red: the 2026-07-28 fix
  taught protection_adrs() to read front-matter `status:` and skip superseded
  ADRs, so the denominator fell 12 -> 10 with the numerator. Nothing was retagged
  and nothing waived. ARCHITECTURE sec.12's O8b row is CLOSED with the
  measurement, because a row claiming a gate is red while the gate prints OK is
  the same stale-prose defect as the 18.5 mm arm separation.
- next: STAGE 6 — ROUTING. Netclasses, widths and the tier config are green and
  generated. Hardest-first means the two loopback arms go FIRST, together, as one
  wave (route.yaml says so). Owed INTO stage 6: stitching closes 2
  starved_thermal + 1 isolated_copper + U_MCU.57's exposed pad; the 30
  solder_mask_bridge findings are a stage-7 fab deviation, not a routing task.
