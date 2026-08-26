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

## 2026-07-29 — PROCESS DEFECT IN MY OWN COMMIT, recorded because hiding it is worse
- did: committed stage 5 as 85e4d28. I staged correctly — `git add --
  projects/pluto-cal-switch/` — and then ran `git commit` WITHOUT a pathspec.
- result: **a pathspec-scoped ADD followed by an unscoped COMMIT commits the whole
  INDEX, not just what I added.** Three other agents are working in this tree, and
  between my `git status` and my `git commit` the cooksense agent staged a deletion
  of `projects/smc0985-cooksense/02_parts/ULN2803ADWR/{part.yaml,SLRS049G.pdf}`.
  Those two deletions are now recorded inside MY commit, under MY message.
- what I did about it, and why NOT the obvious thing: I did NOT restore the files.
  The cooksense agent is live and mid-refactor (12+ modified files including
  02_parts/README.md and journal/02_parts.md, exactly the shape of a deliberate
  part removal). Un-deleting files an active agent has just staged for deletion
  would silently revert their work at a moment they have no reason to re-check.
  The content is intact in history either way; the only damage is
  MIS-ATTRIBUTION, which this note and the handoff report fix.
- THE RULE, stated so the next session does not repeat it: with concurrent agents
  in one worktree, `git add -- <path>` is NOT sufficient. The commit itself must
  carry the pathspec — `git commit -- projects/<board>/` — or the index is shared
  ground and whatever anyone else staged rides along.

## 2026-07-29 — start: DISPOSITION the reds three HONEST GATES just surfaced
- did: read the corrected canon (design-policies P8 / M-COVER / M-WIDTH / M4,
  fab_tiers.yaml's new `published_stroke_min_height`), then re-ran the whole
  battery on the UNCHANGED board to see what the new measurements say.
- result: **nothing on this board moved and three verdicts flipped, which is the
  whole point.** policy_audit FAIL=5 (was FAIL=4 the day before under the old
  metrics): P-ADJ-UNREACHED PASS -> FAIL (4 budgets), P-SILK-OWN new and FAIL
  (1 of 8), plus the three that were already honest (S-OCCL 23, R-DRC, R-THERM).
  P-ADJ itself went from a false FAIL (`RP2040:3V3 72.96 mm of 4 mm`, a poured
  rail measured end to end) to `52/56 graded, 0 exceeded, tightest
  U_PAD_A2A1.2->R_DELTA1.2 5.92 of 6.00`. The placer's new ownership objective
  took refdes ownership 37/73 -> 57/73 at ZERO cost in placed refdes (73/73, 0
  waived) and left 18 of 79 labels degraded: 16 refdes + 2 captions.
- next: the 4 unreached budgets are a REAL defect class, not a naming nit.

## 2026-07-29 — iterate 1: FOUR BUDGETS WERE BEING GRADED OFF OTHER PARTS' PADS
- did: read each of the four against the netlist instead of against the budget's
  own text, then re-pointed each at the node its datasheet sentence is about.
- result: **all four are the SAME defect — a SERIES ELEMENT SPLITS THE NODE, and
  the budget names the half its own part is not on.** Measured, by an
  independent pcbnew script, before deciding anything:

  | budget (was) | pads on that net | the declaring part's pads | verdict |
  |---|---|---|---|
  | KH-SMA-KE-Z `SW1_ANT` 25 mm | C_DCBLK1.2, U_SW1.3 | none of the 5 jacks | graded off the DC block and the switch |
  | KH-SMA-KE-Z `SW2_ANT` 25 mm | C_DCBLK2.2, U_SW2.3 | none | same |
  | RP2040 `USB_DP` 30 mm | J_USB.3, U_ESD.1/6, R_USBP.1 | none (U_MCU.47 is on USB_DP_MCU) | graded off three other parts |
  | RP2040 `USB_DM` 30 mm | J_USB.2, U_ESD.3/4, R_USBM.1 | none (U_MCU.46 is on USB_DM_MCU) | same |

  DISPOSITION, with the pin pair NAMED in every case (an unstated anchor is a
  hidden assumption) and NOT ONE budget renamed to a net that makes it pass:
  * **The antenna run is TWO nets and 25 mm was one number for both.** Measured
    `J_SMA_ANT1.1 -> C_DCBLK1.1 = 13.300` + `C_DCBLK1.2 -> U_SW1.3 = 5.800`
    = `J_SMA_ANT1.1 -> U_SW1.3 = 20.000 mm` (0.72 dB at 6 GHz), and arm 2 is
    13.300 / 5.800 / 20.000 — IDENTICAL to 0.000 mm, so the "common-mode on both
    channels" half of the original `why` is now measured rather than asserted.
    audit_board's independent A-SEG prints the same 20.00 against its 20.0
    target. The 25 mm ceiling is SPLIT AT THE PART BOUNDARY: 16 mm on
    KH-SMA-KE-Z `RX_ANT1`/`RX_ANT2` with `anchor_pins: ["1"]` (the centre
    contact), 9 mm on BGS12WN6 `SW1_ANT`/`SW2_ANT` with `anchor_pins: ["3"]`
    (RF1). 16 + 9 = the same 25. Each leg is now graded by the part that owns a
    pad on it, and the tightest RF constraint on the jack stopped being a number
    nothing evaluated.
  * **"27 ohm series placed close to the chip" is a statement about the MCU-side
    leg**, so the RP2040 budgets are re-pointed to `USB_DP_MCU` / `USB_DM_MCU`
    with `anchor_pins: ["47"]` / `["46"]` at 8 mm. Measured 5.072 and 5.437 mm.
    8 mm is DERIVED and said to be a placement-intent floor, not physics: at USB
    FS the minimum specified rise time is 4 ns and 8 mm of this stackup is
    ~53 ps, 1.3% of the edge. **Nothing was dropped by the re-point** — the
    connector-side leg is already graded TIGHTER by USBLC6-2SC6's own 6 mm
    `USB_DP`/`USB_DM` budgets (ST DocID11265 sec 2.2), measured
    `U_ESD.1 -> J_USB.3 = 5.186` and `U_ESD.4 -> R_USBM.1 = 4.832 mm`. The
    end-to-end chip->connector run is a two-net quantity no single-net budget can
    express, so it is HAND-MEASURED into the part.yaml for the record:
    `U_MCU.47 -> J_USB.3 = 14.098` and `U_MCU.46 -> J_USB.2 = 13.607 mm`, both
    well inside the 30 mm the deleted entries claimed.
- result (gate): **P-ADJ 58/58 declared budgets GRADED, 0 exceeded;
  P-ADJ-UNREACHED PASS 58/58.** The denominator GREW 56 -> 58 because the switch
  leg is now declared where it can be measured, so this is coverage added, not a
  finding suppressed. audit_board's A-PROX — a different checker with a different
  implementation (canon M1) — independently reports 46 budgets, 0 over, 0 not
  evaluated, and agrees pad-for-pad: SW1_ANT 5.80/9.0, RX_ANT1 13.30/16.0,
  USB_DP_MCU 5.07/8.0.
- next: the two degraded captions, which need geometry and not a rename.

## 2026-07-29 — iterate 2: THE TWO CAPTION HAZARDS, CLOSED BY MOVING THINGS
- did: closed P-SILK-OWN and both degraded captions. Every position was SEARCHED
  on a 0.05 mm grid against the real footprint/silk obstacles, not guessed.
- result:
  * **`USB 5V` was labelling the FUSE.** It sat 7.40 mm from J_USB and 6.01 mm
    from F1, so the USB connector owned NO legend at all and F1 appeared to be
    the 5 V source. Cause: both it and `F 0.5A` were squeezed into the one free
    band in that corner (x 119.4..129.0, y ~27.5) and that band is geometrically
    nearer F1. MOVED WEST of the connector to (110.40, 23.00), into the empty
    x 95.5..113.5 / y 20.0..24.4 band, ending 0.35 mm short of J_USB's courtyard
    so it abuts the part it names. MEASURED: 7.72 mm from J_USB vs **18.44 mm**
    from F1 — a +10.73 mm lead — and still inside P-SILK-FN's effective radius
    for J_USB (8.0 + body diag/2 = 13.43 mm), so presence and ownership hold at
    once. **P-SILK-OWN PASS 8/8, thinnest lead in the family 3.80 mm.**
    WHAT THE MOVE DOES NOT FIX, AND WHY NO POSITION DOES: against ALL parts the
    legend is 5.35 mm from C_FLASH, lead -2.37 mm. J_USB's body is 8.94 x 6.16 mm
    so its centroid is 4.47 mm inside its own courtyard, and the nearest legal
    slot outside it is already 7.6 mm from that centroid while every free pocket
    is ringed by 0402s at 5-7 mm. Grid-searched: the best all-parts lead anywhere
    in the band is -0.18 mm and that point breaks the 0.4 mm frame margin; the
    best LEGAL point is -0.72 mm; rotating the glyph run 90 deg into the
    x 110.2..113.5 pocket is WORSE (-3.82 mm, C_FLASH is what that pocket abuts).
    The OLD position was also negative on that metric (-1.98 mm, vs U_ESD), so
    nothing was traded: what changed is the number the hazard is about. A person
    choosing where to plug a cable is choosing among CONNECTORS.
  * **`RX1` needed a ROTATION, and the rotation is load-bearing.** It landed
    5.95 mm from J_SMA_RX1 and 5.15 mm from C_DCBLK2 (lead -0.80 mm). Not
    nudgeable: at 1.2 mm the glyph run is 3.5 mm WIDE, the only clear band is
    west of the jack's courtyard (x < 48.80), and a 3.5 mm box centred there
    lands at x ~46.8, i.e. 0.7 mm from C_DCBLK2's x. `rot: 90` turns 3.8 mm into
    the y axis and leaves 2.08 mm in x. GRID-SEARCHED over x 42..49.5,
    y 50..65: optimum (47.65, 56.70) at lead **+0.64 mm**, and the same search
    over the HORIZONTAL orientation is negative EVERYWHERE (best -0.18 mm) —
    which is the measurement that makes the rotation a fix rather than a
    preference. RX2 takes the identical slot translated +14.50 mm so the
    silkscreen stays congruent with the copper (was +0.67 mm, still +0.67).
    0.64 mm IS THIN AND IS REPORTED AS THIN. The rival is a 0402 DC block;
    nobody plugs a cable into a 0402. Against the family that CAN be mis-mated
    the lead is 10.68 mm (nearest other jack J_SMA_RX2 at 15.80 mm), and
    audit_board's independent courtyard-EDGE metric says 1.16 to J_SMA_RX1 vs
    4.93 to C_SW1B — **I10 tightest port-caption margin 2.57 -> 3.78 mm**.
  * **`PWR` was labelling the RESISTOR.** 7.00 mm from D_LED_PWR, 3.50 mm from
    R_LED1 (lead -3.50 mm), because R_LED1 sat physically BETWEEN the caption and
    the LED and east was the only side the caption was allowed. Both LED captions
    moved WEST, where nothing exists between x 27.49 and x 89.47, and they are
    spread +/-1.0 mm in y against the LEDs' 2.7 mm pitch so the CAPTIONS are
    4.7 mm apart while the parts are 2.7 mm apart. MEASURED: `PWR` 4.12 mm from
    D_LED_PWR vs 5.45 mm from D_LED_MODE (+1.33 mm); `LOOP` 4.12 vs 5.45 the
    other way. `LOOP` is NOT graded (owner inference needs a refdes containing
    the token, and the LED is D_LED_MODE) and was NOT renamed to "MODE" to make
    it gradeable — renaming silk to satisfy a checker is a fake grade.
  * SIDE EFFECT, measured: fixing PWR also rescued the R_LED1 and R_LED2 refdes.
    Silk ownership **61/79 -> 65/79 owned, 18 -> 14 degraded, and 0 of the 14 is
    a caption**. Still 73/73 refdes on silk, 0 waived — this board paid nothing.
- next: the 16 (now 14) degraded refdes, which get a report and not a move.

## 2026-07-29 — iterate 3: THE SILK-STROKE NUMBER, RE-VERIFIED AGAINST THE FIXED CANON
- did: the corollary I was given ("0.60 mm reaches the published 0.15 stroke") is
  wrong and has been corrected upstream. Re-derived it by CALLING the
  generator's own `silk_stroke()` rather than re-implementing it, and corrected
  every place this project still repeated the 0.60 figure as the tier's rule.
- result: **there are TWO formulas, which is why one hand-derived number could
  never have covered both.** Board-silk captions take
  `max(min_silk_stroke, 0.13, 0.16 x h)`; the refdes de-collision path takes
  `max(min_silk_stroke, 0.09, 0.20 x h)`; both clamped above by KiCad's 0.25 x h.
  Measured: caption path 0.60/0.70/0.80 -> 0.1300, 0.90 -> 0.1440,
  **0.9375 -> 0.1500** (first to reach it), 1.00 -> 0.1600, 1.20 -> 0.1920;
  refdes path 0.60 -> 0.1200 and its own threshold is **0.75**. `fab_tiers.yaml`
  now carries `published_stroke_min_height: 0.9375` as DATA and G-SELFCON grades
  both directions, so the threshold is checked instead of believed.
  **This board was already right and is now right FOR THE STATED REASON:** all
  16 stress-read captions measure 0.1600 (h=1.0) or 0.1920 (h=1.2) on the saved
  board, 0 of 16 below 0.15. The 73 refdes stay at 0.60 -> 0.1200, above the
  ENFORCED 0.1125 floor and duplicated on F.Fab. NOTED AND NOT TAKEN: 0.75 mm
  would put the refdes on the published stroke too, because the refdes ratio is
  0.20 and not 0.16 — not taken because a 25% wider glyph re-runs the whole
  73/73 placement and the ownership search, and pluto-rx2-8way has already
  measured that cost at 3 refdes pushed to F.Fab.
- next: one metric disagreement between my own two checkers, found while
  tabulating the refdes leads.

## 2026-07-29 — iterate 4: MY OWN I9 COUNTED A SCREW HOLE AS A LABEL THIEF
- did: tabulated all 24 I9 findings with margins to report them, and one of them
  was J_USB's own refdes, 1.70 mm from J_USB's courtyard and 0.31 mm from H2's.
- result: **I8 excludes mounting holes as things to be GRADED and I9 left them in
  the set of things a label can be STOLEN BY — the same category error, one line
  later.** A mounting hole prints no designator, so no reader can mistake a
  nearby refdes for its name; the shared placer's ownership objective already
  excludes holes for exactly that reason, so I9 also DISAGREED WITH THE PLACER
  about what a rival is. Fixed at the rival set (`cents` now built from
  `comps_only`). **I9 24 -> 23 and it is STILL FAIL**, and the one removed entry
  is verifiably the only one of the 24 whose rival was a hole — measured both
  ways before and after, so this is a false finding deleted and not a real one
  hidden.
- next: report the 23/14 degraded refdes and stop.

## 2026-07-29 — finish: STOPPED BEFORE ROUTING, the declared boundary
- did: full battery, unpiped, real exit codes. NO routing attempted.
- result: **policy_audit FAIL=5 -> FAIL=3, PASS=20 -> 22, HUMAN=6, N-A=12.**
  P-ADJ-UNREACHED and P-SILK-OWN are CLOSED with measurements. The 3 remaining
  reds are the honest ones and stay red: S-OCCL 23 (its evidence is a stage-7
  render review of a PDF that does not exist yet), R-DRC 35/108/0 (35 owned
  exactly as before — 30 solder_mask_bridge = the BGS12WN6's deliberate single
  mask opening, a stage-7 fab deviation; 2 starved_thermal + 1 isolated_copper =
  stage-6 stitching; 2 hole_clearance = J_USB's vendor-fixed 0.225 mm boss vs a
  0.250 floor derived from the tier's HOLE-TO-HOLE number, which is not the same
  specification; 108 unconnected is what an unrouted board IS), and R-THERM
  U_MCU.57 (the QFN-56 exposed pad, stage-6 stitching).
  Exit codes: generate_board 0, audit_board 1 (I9 only), placement_gates 0,
  import_provenance 0, generate_rules 0, tier_preflight 0, count_parity 0,
  policy_audit 1, status_beacon 0, contracts_audit 0.
- **THE 14 DEGRADED REFDES (placer's centroid metric, holes excluded), AND WHAT
  MAKES EACH ACCEPTABLE.** Leads, measured:
  | refdes | own | nearest rival | lead |
  |---|---|---|---|
  | U_MCU | 6.20 | C_IO2 1.28 | -4.92 |
  | C_USBV | 11.00 | C_FLASH 7.32 | -3.68 |
  | C_DV1 | 7.00 | Y1 3.62 | -3.38 |
  | R_CTRL1 | 6.20 | R_DELTA3 3.53 | -2.67 |
  | C_ADCV | 5.40 | C_IO4 2.80 | -2.60 |
  | C_VREGO | 7.20 | C_IO1 4.94 | -2.26 |
  | J_SMA_RX1 | 7.20 | C_DCBLK2 5.13 | -2.07 |
  | C_VREGI | 7.20 | C_VBUS 5.14 | -2.06 |
  | C_IO3 | 3.11 | C_XOUT 1.30 | -1.81 |
  | R_USBM | 2.80 | R_USBP 1.20 | -1.60 |
  | R_USBP | 2.90 | C_FLASH 1.33 | -1.57 |
  | C_CTRL2 | 3.11 | R_CTRL_PD2 2.28 | -0.83 |
  | Y1 | 5.20 | R_HDR_S 4.50 | -0.70 |
  | C_CTRL1 | 1.98 | R_CTRL1 1.61 | -0.37 |
  ACCEPTABLE, and the reasons are of three kinds, stated separately so the
  mitigation is not doing all the work:
  1. **THIRTEEN OF THE FOURTEEN RIVALS ARE PASSIVES IN THE SAME FUNCTIONAL
     CLUSTER** (C_IO*/C_XOUT/C_FLASH/C_VBUS/R_USBP/R_CTRL*). A reader who
     mis-attributes `C_IO3` to `C_XOUT` is choosing between two decoupling
     capacitors of adjacent value inside the MCU's own supply ring. There is no
     mis-mate, no polarity and no rating consequence — both are unpolarised
     0402 MLCCs. The one that is NOT of that kind is `J_SMA_RX1`, and the
     CAPTION that carries the mis-mate risk for that jack (`RX1`) is OWNED, by
     10.68 mm against the other jacks; the refdes is the redundant label.
  2. **THE MITIGATION, STATED AS ONE AND NOT LEANED ON SILENTLY:** every refdes
     is ALSO on F.Fab at its own part's origin (`fab_copy: true`, 73/73, I8
     PASS), and the assembler consumes the CPL, not the silkscreen. So the
     exposure is a HUMAN misreading a physical board during rework, not an
     assembly-yield defect. That is a real reduction in consequence and it is
     NOT a reason the finding is false — the finding is true.
  3. **IT IS NOT MOVABLE FROM HERE.** The placer searched 4 poses x 84 offsets
     per label and found NO owned slot for these 14; it is now an objective
     inside the placer's own obstacle model, so a slot it rejects is a slot that
     collides. Closing them means moving PARTS, and the parts in question are
     the ones whose positions are pinned by the datasheet budgets P-ADJ grades
     (C_IO3 is 2.60 mm from U_MCU.26 against a 4 mm budget; C_CTRL1 is 2.48 mm
     from U_SW1.6 against 4 mm). Trading a graded electrical budget for a silk
     ownership margin is the wrong trade and would be a real regression.
  audit_board's I9 measures the SAME property with a different metric —
  courtyard EDGE, which is how a human reads a label against an outline — and
  reports 23 of 73. THE TWO DISAGREE IN BOTH DIRECTIONS and that is worth
  knowing: C_LDOO (edge margin -0.126) and C_SW1B/C_SW2B (-0.077 each) are
  findings only on the edge metric, while C_USBV (-6.290) and C_VREGO (-5.325)
  are the worst on both. Neither metric is a superset of the other, so the
  honest report is both numbers, not the kinder one.
- **PROPOSED skills/ PATCHES (not applied — an agent is live in skills/):**
  1. `generate_board_generic._ownership` scores CENTROID distance; `03_src/
     audit_board.py` I9 and the fleet's silk reviews read courtyard EDGE. On
     this board the two sets differ in both directions (14 vs 23, 3 findings
     exclusive to edge). The placer's own docstring says centroid "penalises big
     parts for being big" and that edge distance "rescued ZERO" — that was
     measured on the metric BEFORE the objective existed. Re-measure it as an
     OBJECTIVE: score `max(0, edge_own) - max(0, edge_rival)` inside the same
     search and report which measure was used, so the placer optimises the
     property the auditors grade.
  2. `_caption_owner` infers an owner only when the caption's alphanumeric token
     is a substring of exactly one refdes. `USB 5V` -> `USB5V` matches nothing,
     so the caption whose misownership P-SILK-OWN caught is invisible to the
     placer's own objective. Suggest falling back to the LONGEST token in the
     caption that matches exactly one refdes (`USB` -> J_USB), which would have
     let the placer see it. Keep the "ambiguous means no owner" rule.
  3. tier_preflight's PF-HTC WARN is unchanged and still has no config fix:
     `stitch.astar_fallback` calls `via_site_ok` with a hardcoded 0.205
     hole_to_copper against this board's 0.25 floor.
- next: STAGE 6 ROUTING, unchanged and unblocked. Netclasses (6 + 41 patterns +
  6 width rules), the tier config (0 FAIL / 2 WARN) and the placement gates
  (PASS, 0 fails 0 warns) are all green and generated. route.yaml's own note
  sets the order: HARDEST-FIRST means the two loopback arms go FIRST, TOGETHER,
  as one wave, because a router that threads one and then squeezes the other has
  already destroyed the property this board exists to publish.
