# placement journal — pluto-rx2-8way stage 5 (footprints + placement)
#
# CLOCK NOTE, so the timestamps read sanely: stage 4's entries are stamped
# 19:05/19:10 but the system clock at handoff read 17:43 PDT the same day. This
# journal uses the SYSTEM clock (`date`), so the first entry below appears to
# precede the previous stage's finish. It does not; the earlier stamps ran fast.

## 2026-07-28 17:50 — start
- did: took stage 5 (footprints + placement) with the mandate to STOP BEFORE
  ROUTING. Read the canon (repo CLAUDE.md, SKILL.md 4-6 incl. D-ADJ /
  archetypes / LAYOUT PRECEDENT SEARCH, floorplan-archetypes.md,
  layout-precedents.md, fab_tiers.yaml, design-policies.md), this board's
  BRIEF/ARCHITECTURE/DETAIL_DESIGN/CHECKLIST, all eight ADRs, the four journals,
  02_parts/README.md, 03_src/ and every contracts.md, and `git show 0228e7b`.
- result: state confirmed as handed over — `policy_audit` FAIL=0 HUMAN=6 N-A=26
  PASS=8, netlist present (64 components / 74 nets), 04_kicad EMPTY except its
  contracts.md, no `03_src/placement_gates.json` yet. THE FLOORPLAN IS ALREADY
  DERIVED (ADR-0007) and this stage ADAPTS it rather than re-deriving it.
  TEMPLATE-LEFTOVER RE-CHECK (the stage-4 finding): `route.yaml` names
  `pluto_rx2_8way` throughout, `rebuild_all.sh` carries BOARD=TSX=pluto_rx2_8way,
  `rebuild_reuse.sh` derives BOARD from floorplan.yaml, `floorplan.yaml`
  `project.name: pluto_rx2_8way`. Nothing template-shaped survives in 03_src.
- next: (1) INDEPENDENTLY re-verify every standard-KiCad footprint against its
  committed vendor land drawing — the claims are in the part.yaml comments and a
  claim is not a measurement (canon M1); (2) generate the board from
  floorplan.yaml on the generic backend; (3) P-OUT/P-CAP BEFORE any routing.

## 2026-07-29 15:30 — iterate (second stage-5 pass; the first left no finish entry)
- did: took the stage-5 gate again and started by VERIFYING the handoff rather
  than trusting it. Three of the four things the beacon and the floorplan
  asserted turned out to be wrong, and each was found by running the thing
  rather than reading about it.
  1. **THE BEACON'S BLOCKING RED IS FULLY STALE.** `next:` demanded three
     ledger rows be appended before anything else. They were appended
     2026-07-28 (commit ea86197) and are in
     `skills/jlcpcb-fab/references/lcsc_passives_ledger.yaml` at lines 238-240
     with catalog reads. `bom_source_check --circuit-only` now **PASSES** (15
     vendored part.yaml codes + 151 ledger codes, 0 findings). A first run
     showed 2 `UNVERIFIABLE-VALUE` on C25091 (the 220 R pickoff) — that was MY
     invocation error, not a red: the gate needs `--parts 02_parts`, and with it
     C25091 resolves through `02_parts/0402WGF2200TCE/part.yaml`. Reported as an
     error I made, because a mis-invoked gate reads exactly like a failing one.
  2. **THE STOCK-FOOTPRINT VERIFICATION `floorplan.yaml` CLAIMED WAS NEVER
     RECORDED.** The file said "the numbers are in 02_parts/README.md"; they
     were not, anywhere. Done independently: 11 distinct stock lands parsed out
     of /usr/share/kicad/footprints and compared page-by-page against the
     committed vendor PDFs. **2 exact MATCH · 5 MATCH-WITH-IPC-EXPANSION ·
     3 NO-VENDOR-LAND · 1 MISMATCH**, table in `02_parts/README.md` deviation
     10. The old claim named the right parts, undercounted by two (it said NINE
     and summed 2+3+3+1), and was wrong twice about the mismatch: SOT-223 also
     displaces the row centre **C 6.10 -> 6.30**, so "every delta adds copper"
     is FALSE (0.05 mm of vendor heel land is uncovered), and the 0.80 mm
     adjacent-pad gap is a **0.55 mm reduction** from C04-2032A's 1.35 mm, not
     an unchanged value. Also corrected `USBLC6-2SC6/part.yaml`, which declared
     its SOT-23-6 land "a MATCH": pitch and pad width are exact (0.000) but pad
     length is +0.125 and span +0.10, i.e. IPC-EXPANSION.
  3. **A WAIVER ASSERTED A MEASUREMENT THAT WAS NOT TRUE.** `policy_waivers.yaml`
     said RP2040's renamed `DVDD_1V1` budget was "graded and PASSING at 8.84 mm
     against 10". It is not: the net has SIX pads, not five — `C_VREG_OUT.1` was
     omitted — and the worst pair is `U_MCU.23` -> `C_VREG_OUT.1` = **13.167 mm**.
     Retracted in place with the three numbers that do matter (pin 45 -> pins
     23/50 = 6.98/6.93 mm, INSIDE the budget; the two 100 nF at 1.11 and
     3.90 mm; the mandatory 1 uF at 8.65 mm, which is the real weakness).
  4. **"RX2 -> PLUTO RX2" WAS LABELLING THE WRONG CONNECTOR.** Measured 7.29 mm
     from `J_ANT1` against 7.85 mm from `J_RX2` — the sibling-board defect, on
     the one pair of ports whose confusion feeds an SDR input with an antenna.
- did (fixes, all in `03_src/` + `02_parts/`, nothing hand-edited in 04_kicad):
  * **Silk rebuilt.** The previous block produced SEVEN `crowded caption` WARNs
    and the title sat 0.17 mm off the x0 edge. Rather than nudge by hand again,
    reproduced `generate_board_generic`'s OWN obstacle model offline — pads +
    footprint silk + refdes at clearance/2, **plus the whole-footprint body
    bbox at 0.05, which is the term a by-hand check omits and the term the port
    contract was hitting** — and searched exhaustively. Result: **17 captions,
    0 crowded**. Ten port labels, one per jack, each on ITS OWN radius at the
    largest clearing r, every one nearer its own jack than any other by
    2.2-3.9 mm. Escape wedge measured at **16.73 x 5.96 mm = FOUR rows of
    0.6 mm text and no fifth**, so the port contract is compressed to four
    lines that still carry all four ADR-0004 facts. `0.5A` added at F_IN, which
    P-SILK-FN was failing on along with J_ANT3 and J_ANT6.
  * **Port labels at 0.95 mm / 0.152 mm stroke.** `fab_tiers.yaml`'s corollary
    ("0.15 needs >= 0.60 mm text") is necessary but NOT sufficient here:
    measured against the backend's own `max(min_silk_stroke, 0.13, 0.16*size)`,
    0.60 mm text yields **0.13**. 0.15 needs **size >= 0.9375**.
  * **`placement.patterns`** with `zone_connection: full` on the GND pads of
    U_SW / J_USB / U_MCU. `starved_thermal` **15 -> 4**. Three of the fifteen
    were "1 spokes connected to isolated island" — a GND pad on the RF switch
    whose single spoke did not reach the pour at all, on the part whose EP is
    the RF ground return. The four remaining are named and DELIBERATELY not
    converted (tombstoning class); see floorplan and CHECKLIST section D.
  * **`Datasheet` and `Description` properties cleared** in the three authored
    `.kicad_mod`. They carried citations the converter's symbols do not, so
    KiCad compared a string against "" — **12 parity diffs -> 0**. The
    provenance is unchanged: it lives in each footprint's `descr`, which parity
    does not compare.
  * **J_USB footprint silk trimmed** from local y +3.9 to +2.95 and the +3.9
    cross line DELETED, not moved: it lay 0.71 mm off the board, and drawing it
    inboard would mark a body edge where the body does not end. 2
    `silk_edge_clearance` -> 0.
  * **7 `text_thickness` -> 0 by regeneration alone** — the board was built
    2026-07-28, before `min_silk_stroke` moved 0.15 -> 0.1125 on 2026-07-29. A
    stale artifact, not a placement defect.
- result: see the finish entry below.
- next: finish entry, STATUS beacon, commit.

## 2026-07-29 16:05 — finish
- did: ran the mandated battery in order on the regenerated board and measured
  every number rather than carrying one forward.
- result: **THE PLACEMENT GATE, in order, every number measured** —
  `generate_board_generic` **64 footprints (15 anchored), 10/10 asserts PASS,
  1 floating part legalized, 0 pad shorts, 64/64 refdes on silk (0 waived to
  F.Fab, down from 2), 0 crowded captions**, 13 libraries, 4 holes ·
  `audit_board.py` **PASS, 7 invariant groups / 12 measurements** (I3 nine
  radial arms 17.778..18.102 mm, spread 0.324 mm; I4 RX1_TAP_MID span
  1.180 mm vs the 1.37 bound; I5 the ESD chain — J_USB A6/B6 -> U_ESD.1 and
  A7/B7 -> U_ESD.3 both **1.689 mm** vs 2.0, U_ESD.5 -> C_ESD.1 **0.890 mm**;
  I6 pad row 6.860 mm inside y1 against the vendor's 6.86, overhang 0.535 mm;
  I7 four M3 keepouts clear of 68 parts) · `placement_gates.py` **PASS 0
  fails / 0 warns**: **P-OUT** tightest pad-to-outline **1.29 mm** (J_USB.SH)
  against a 0.15 floor, **P-CAP** worst cut x = 49.5 mm demand 15 nets vs
  capacity 211 tracks, **ratio 0.07** against a 0.5 fail line ·
  `generate_rules_generic` 6 netclasses + 34 patterns + 6 width rules ·
  `tier_preflight --explain` **0 FAIL / 1 WARN** (PF-LEGALIZE, carried
  deliberately and documented) · `count_parity` **S-COUNT PASS 4/4 source
  pairs over 64 refdes** · `kicad-cli pcb drc --severity-all --refill-zones
  --schematic-parity` **4 violations / 99 unconnected / 0 parity** (was
  24 / 100 / 12) — the 4 are all `starved_thermal` and all four are the named,
  deliberately-unconverted 0402 GND pads · `policy_audit` **FAIL=2 HUMAN=6
  N-A=10 PASS=20 WAIVED=3** · `bom_source_check --circuit-only` **PASS** ·
  `part_facts_check` **P-FACT OK but SIXTEEN UNREACHED** (see below) ·
  `waiver_provenance` **ok W-COPY: 3 waivers, all independently reasoned** ·
  `contracts_audit --projects` **0 violations in this board's scope**.
- result: **ON THE `FAIL=0` THE HANDOFF ASKED ME TO KEEP.** It is FAIL=2, and
  the honest statement is that FAIL=0 and FAIL=2 grade DIFFERENT DENOMINATORS.
  At stage 4 `04_kicad/` held no board, so R-DRC, R-THERM, P-SILK-REF,
  P-SILK-FN, P-PLANE, R-POUR and six more were **N-A "no board"** — N-A was 26
  and PASS was 8. Now that a board exists those checks RUN: **N-A 26 -> 10 and
  PASS 8 -> 20**. Sixteen checks that could not run before now run; fourteen of
  them pass. The two that fail are **R-DRC (99 unconnected — there are no
  tracks) and R-THERM (three power pads with ZERO thermal vias — there are no
  vias)**, and this board's `policy_waivers.yaml` refuses to waive either,
  correctly: waiving a gate because its stage has not run yet is the worst
  thing that could go in that file. Fleet precedent is the same
  (crow-mic-pod-v2's placement journal records R-DRC-unconnected as the only
  fail at this gate). I did NOT make the number go to zero, and I did not
  redefine the gate to get there.
- result: **P-COLLIDE's 7 anchored courtyard overlaps are now MEASURED to be
  false positives, not just argued to be.** The generator warns that
  "full-severity DRC will fail this as courtyards_overlap"; DRC reports
  **0 `courtyards_overlap`** with that rule at severity `error` in the
  .kicad_pro. The generator compares axis-aligned bounding boxes and the six
  jack pairs are rotated 15/45/75 degrees, so the boxes lap where the
  courtyards clear (1.16 mm, per the floorplan's rotated-rectangle measurement).
- result: **M-REPRO, measured rather than assumed.** The generator prints
  "identical source now yields byte-identical output". It does NOT: two runs
  from identical source into identical paths differ from byte 2073, and the
  difference is the ORDER of the footprint s-expressions (18277 diff lines,
  same content). Everything that MATTERS is stable — an independent fingerprint
  of **68 footprint (ref, x, y, rotation, FPID) tuples, 85 silk texts and 68
  refdes positions is IDENTICAL across runs**. So the board is reproducible by
  PROPERTY (which is the contract repo CLAUDE.md states) and not by BYTES
  (which the generator's own banner claims). Carried up as a proposed patch.
- next: **STOP — STAGE 5 ENDS HERE, a declared handoff boundary.** Stage 6 owns
  routing: KRT fanout-first on a track-free board, the nine arms equalised to
  +/-0.10 mm (they start at a 0.324 mm pad-to-pad spread), the via fences, the
  L2 antipads measured on the FILLED board, and the four CHECKLIST-D
  obligations this stage added. Nothing in `04_kicad/` is sealed and everything
  in it regenerates from `03_src/` + the pinned `03_tscircuit/kicad/*.kicad_sch`.

## 2026-07-29 17:00 — start (third pass: DISPOSITION the reds three gate fixes surfaced)
- did: took a dispositioning mandate, not a building one. Three gate fixes
  landed after the second pass closed (`62a82fa` P-ADJ anchor pin + P-ADJ-PAIR +
  P-SILK-OWN + P-FACT denominator, `3f5dab4` the `adjacency:` prose crash,
  `3bfdbc6` silk ownership in the placer + the arithmetically wrong stroke
  corollary) and **none of them changed a track or a pad** — they changed what is
  MEASURED. So every red below was already true and had been reported as a pass.
  Read repo CLAUDE.md, design-policies.md (M-COVER / M-WIDTH / M4),
  fab_tiers.yaml, this board's STATUS + journals + eight ADRs, and
  `git show c07aaf2 0580e01 3bfdbc6 62a82fa 3f5dab4`.
- result: baseline re-measured before touching anything, and it reproduces the
  handoff exactly: **policy_audit FAIL=3 HUMAN=6 N-A=10 PASS=21 WAIVED=3**,
  DRC **4 / 99 / 0**, generate_board 64 footprints / 15 anchored / 10-of-10
  asserts / 0 pad shorts / **61-of-64 refdes on silk, 3 waived (FB_IN, R_CC1,
  R_USB2)** / 0 crowded / **44-of-74 labels owned, 27 degraded, 3 unplaced**,
  audit_board PASS, placement_gates PASS, tier_preflight 0 FAIL 1 WARN,
  S-COUNT 4/4 over 64. One INVOCATION correction worth recording because a
  mis-invoked gate reads exactly like a failing one (this board has paid for that
  once already): `waiver_provenance.py projects/pluto-rx2-8way` returns
  **FAIL 0/0 waivers graded** — its `root` argument is the *projects/* directory,
  so the correct call is `waiver_provenance.py projects --project pluto-rx2-8way`,
  which reports ok W-COPY 3/21 across 1/5.
- next: (1) full-list dump of P-ADJ / P-ADJ-PAIR / P-ADJ-UNREACHED, because the
  gate truncates its detail at five items and there are six unreached; (2) decide
  FIX-vs-WAIVE on each red with a measurement, not a preference; (3) retire the
  P-ADJ waiver, which now argues for a change that has landed.

## 2026-07-29 17:20 — iterate (four fixes in copper; only one thing got waived)
- did: reproduced the gate's own P-ADJ loop offline to get the untruncated lists
  (36 keep_short + 7 adjacency + 6 unreached = 43 budgets), then dispositioned
  each red. **THE HEADLINE IS THAT FOUR OF THE FIVE REDS TURNED OUT TO BE FIXABLE
  IN COPPER, so this round retires a waiver rather than adding one.**
- result: **P-ADJ's WAIVER IS RETIRED, AND TWO OF ITS THREE ENTRIES DISSOLVED
  WITHOUT ANY COPPER MOVING.** DVDD_1V1 goes 13.167 -> **8.787 mm** (U_MCU.23 ->
  C_MCU7.1) and SW_V4 goes 21.64 -> **3.057 mm** (U_SW.12 -> R_PD4.1): the same
  placement, measured correctly. The waiver's own closing paragraph had ASKED for
  the anchor-pin metric, which is the tell that it had stopped being a judgement.
- result: **ABM8 `GND <= 3 mm` WAS A REAL 0.233 mm MISS AND IS FIXED, NOT
  WAIVED.** The old 67.24 mm figure was the board diagonal; the anchor metric read
  3.233 mm (Y_XTAL.4 -> C_XTAL1.2) and 3.140 mm (Y_XTAL.2 -> C_XTAL2.2). Both load
  capacitors were ROTATED 180 so their GND pad faces the can instead of their live
  pad — no coordinate moved, and a 2-terminal 0402 courtyard is symmetric so
  nothing else shifted. Now **2.457 / 2.291 mm, PASS with 0.543 mm of margin**.
  The cost is reported, not hidden: the live legs lengthen 1.821 -> 2.780 (XIN) and
  2.011 -> 2.915 mm (XOUT_XTAL), which against the part.yaml's OWN 0.099 pF/mm and
  3 pF stray allowance is +0.153 pF = 5.1% of the allowance, while the return that
  the same sentence says is IN the oscillator loop shortens by 0.78/0.85 mm.
- result: **P-ADJ-PAIR's TWO NEW FAILS WERE AN ORIENTATION, NOT A SHORTAGE.**
  `layout.adjacency` had been in the contract, in the part.yaml, and opened by
  NOTHING; graded for the first time, MCP1755S U_LDO~C_LDO read 4.879 mm and
  U_LDO~C_LDI 10.781 mm of copper gap against 3.0. Root cause: U_LDO sat at
  rotation 0, pointing pins 1/2/3 at a board edge 1.29 mm away, so no capacitor
  could EVER be placed at VIN or VOUT. Rotation 180 turns the pin row inboard;
  C_LDO moved to (33.06, 78.1) and C_LDI to (29.745, 85.9) **rot 270**. Now
  **0.860 mm and 1.200 mm — PASS**. Two measurements behind the details: the
  pocket between H3's keepout (ends x 27.99) and D_TVS (starts x 31.50) is
  3.51 mm and an 0805 courtyard is 3.49, i.e. 0.02 mm of slack against a 0.25
  legalize floor, which is why C_LDI stands up; and rot 90 was rejected BY
  ARITHMETIC before being tried, because it puts pad 1 on the far side for a
  3.10 mm gap — a 0.10 mm fail.
- result: **AND THE ROTATION CLOSED A BUDGET THAT WAS FAILING WHILE UNGRADED.**
  MCP1755S `VBUS_F <= 15 mm` is P-ADJ-UNREACHED (U_LDO has no pad on VBUS_F —
  FB_IN's ferrite makes pin 1 `VBUS_LDO`). Hand-measured on the OLD placement,
  U_LDO.1 -> FB_IN.2 was **17.194 mm** and U_LDO.1 -> F_IN.2 **16.808 mm**, both
  OVER the datasheet's 15 mm with no gate able to say so. They are now 9.395 and
  10.602 mm. That is the strongest argument in this session for why an UNREACHED
  budget is a finding and not a skip.
- result: **A WAIVER'S OWN HAND MEASUREMENT DID NOT REPRODUCE, AND THE PAIR WAS
  OVER BUDGET.** The P-ADJ-UNREACHED entry for PE42482A `SW_VDD <= 3 mm` claimed
  "C_SW1 pad 1 to U_SW pin 8 = 2.62 mm, inside the 3 mm". Measured: **3.085 mm**
  centre-to-centre (2.375 mm of copper gap) — i.e. under P-ADJ's own measure it
  EXCEEDED by 0.085 mm while the file asserted it passed. C_SW1 moved x 44.0 ->
  44.7 and now measures **2.873 mm**; the stop is R_PD4's courtyard at x 45.485
  (0.28 mm left against the 0.25 floor) and the escape corridor above (ends
  y 49.995, 0.25 mm of headroom). The same paragraph's "R_PD4 pad 1 -> 2.53 mm
  from pin 12" (this file said 2.42) MEASURES 3.056 mm — it passes its 4 mm
  budget, but two numbers in the source were wrong and the 0402 RESISTOR land's
  0.51 mm pad offset vs the CAPACITOR land's 0.48 is most of the difference.
- result: **THE ANT8 CAPTION MOVED, AND SO DID FOUR MORE — ALL SEVENTEEN CAPTIONS
  ARE NOW OWNED.** The ownership term measured five port labels nearer a passive
  than their own jack: ANT8 -8.40 mm (2.00 from R_T2), ANT4 -5.48, RX1 -3.29,
  ANT5 -2.96, RX2 -1.54. ANT8 is the one that matters, because ANT8 IS the RX1
  antenna and R_T1/R_T2 are the pickoff every published path delta is referenced
  to. WHAT WAS MEASURED before moving it, on a 0.05-0.1 mm grid against the
  generator's own obstacle model: **on theta 75 there is NO owned slot at all**
  (J_ANT8's body bbox starts at r 14.93 and R_T1's ends at 14.9 — they are FLUSH,
  so a caption is confined to r <= 13.9 while ownership against R_T1 needs
  r >= 16.9, which would need the pickoff at r <= 7.8 and ~6 mm more RX1 main
  line); **outboard on theta 75 is occupied by J_ANT8's own pad 5** (x
  51.86..54.08, y 22.46..24.68, leaving 0.43 mm to the y0 edge); and **horizontal
  text anywhere gives at best +1.76 mm against J_RX1**, which trades the pickoff
  ambiguity for the one jack-to-jack ambiguity this board most needs to avoid and
  is WORSE than the 2.23 mm it already had. **Rotating the caption 90 degrees is
  what solves it**: 2029 owned slots, best at (56.95, 23.30) — 6.692 mm from
  J_ANT8, 9.134 from J_RX1, lead **+2.442 mm**, i.e. closer AND owned AND better
  discriminated than before. The same rot-0/90 search then rescued the other
  four (RX1 7.663/+5.428, RX2 5.822/+2.864, ANT4 6.619/+3.343, ANT5
  6.694/+3.907), every one both closer to its jack and owned, so the port-label
  RULE changed from a geometric convention ("inboard on its own theta") to the
  safety property itself ("maximise the ownership lead subject to jack-to-jack
  discrimination >= 2.2 mm"). Four labels now stand outboard and vertical; six
  did not move. **Ownership 44/74 -> 50/74, degraded 27 -> 22, unplaced 3 -> 2.**
- result: **THE FIRST ANT8 ATTEMPT CAME BACK `WARN silk caption crowded` AND IT
  WAS NOT A COLLISION.** At y = 23.25 every pad, body, footprint-silk and sibling
  caption box clears; the failing test was `_in_frame(0.4)` against the DECLARED
  outline y0 = 21.0 (not the 20.95 edge-cut bbox) — the rotated box top sat at
  21.398 against a 21.400 limit, **2 um out of frame**. The generator emits the
  same one-word WARN for both causes, which cost a rebuild to tell apart.
- next: rewrite the waiver file (retire P-ADJ, re-evidence P-ADJ-UNREACHED with
  all six, add the refdes-on-silk regression WITH its evidence), close the ABM8
  pagination question, correct every doc that repeats the 0.60 mm stroke figure,
  then re-run the whole gate suite unpiped.

## 2026-07-29 17:34 — finish (STAGE 5 STILL DONE, STILL STOPPED BEFORE ROUTING)
- did: re-ran every gate in the mandated order, unpiped, exit codes read from the
  process and not from a pipeline tail.
- result: **policy_audit FAIL=2 HUMAN=6 N-A=11 PASS=23 WAIVED=2** (exit 1), from
  a baseline of FAIL=3 / N-A=10 / PASS=21 / WAIVED=3. The denominator itself grew
  by one row — M-DEPEND appeared (N-A, "no releases yet"), 43 rows -> 44 — which
  is why N-A moved 10 -> 11 with nothing regressing. P-ADJ **PASS** 30/36 graded
  (tightest QSPI_SD2 11.839/12.0, +0.161), P-ADJ-PAIR **PASS** 7/7 (tightest
  J_USB~U_ESD 1.689/2.0, +0.311), P-SILK-OWN **PASS** 12/12 with the thinnest
  lead now **J_ANT8 owns 'ANT8' by 2.44 mm** (was 2.23). The two remaining FAILs
  are R-DRC (99 unconnected: there are no tracks) and R-THERM (U_LDO.4 /
  U_MCU.57 / U_SW.25 at zero thermal vias: there are no vias), both refused a
  waiver on purpose, both closing at stage 6.
- result: **DRC 4 / 99 / 0**, unchanged, and the four are the SAME four deliberate
  starvations re-identified by position off the report: C_MCU7.2 (44.28, 78.10),
  C_ESD.2 (46.48, 78.10), C_MCU8.2 (48.68, 78.10), C_MCU9.2 (39.88, 78.10) — all
  `starved_thermal ... zone min spoke count 2; actual 1` on F.Cu.
- result: the rest, every number: generate_board **64 footprints / 15 anchored /
  10-of-10 asserts / 1 legalized / 0 pad shorts / 62-of-64 refdes on silk (2
  waived: C_MCU7, R_CC1) / 0 crowded captions / 50-of-74 labels owned, 22
  degraded, 2 unplaced** · audit_board **PASS, 7 invariant groups, 12
  measurements** (RX1_TAP_MID 1.180 of 1.37; U_ESD 1.689 mm on both D+ and D-;
  C_ESD 0.890; J_USB pad row 6.860 vs the vendor's 6.86; overhang 0.535) ·
  placement_gates **PASS 0/0** with P-OUT 1.29 mm (J_USB.SH) vs 0.15 and P-CAP
  ratio 0.07 vs 0.5, run BEFORE any routing attempt · generate_rules 6 netclasses
  + 34 patterns + 6 width rules · tier_preflight **0 FAIL / 1 WARN**
  (PF-LEGALIZE, carried) · count_parity **S-COUNT PASS 4/4 over 64 refdes** ·
  waiver_provenance **PASS, ok W-COPY 3 waivers all independently reasoned** ·
  bom_source_check --circuit-only **PASS** · contracts_audit **0 violations in
  this board's scope** (the fleet number is 2669 and none of them are here).
- result: **THE REFDES REGRESSION, PAID FOR RATHER THAN HIDDEN.** 64/64 with zero
  waived became **62/64**, and C_MCU7 and R_CC1 are on F.Fab only. Both numbers
  belong in one sentence: refdes ownership went 24/64 -> 39/64 (the first
  measurement of that property at all) and every caption is now owned, and the
  same ownership-first search that bought those is what strands two 0402s. The
  evidence per part is in the waiver file: C_MCU7 is one of ten identical 100 nF
  in a row of EIGHT parts at 2.2 mm pitch inside a 1.92 mm band; R_CC1 is one of
  two identical 5.1 k under J_USB's bounding box, beaten to its slot by the C_ESD
  refdes at 2.87 mm. The mitigation is stated AS a mitigation: both are on F.Fab
  at 0.45 mm and both are machine-placed 0402s whose position comes from the CPL,
  not the silkscreen. It is better than the 61/64 the gate fixes first produced
  (FB_IN, R_CC1, R_USB2), because the LDO and caption moves freed real estate.
- result: **THE ABM8 PROVENANCE DEFECT IS CLOSED, BY RE-FETCHING RATHER THAN BY
  ARGUMENT.** The three committed sheets carry footers "Page (2) of (9)",
  "(4) of (9)", "(6) of (9)", which reads like a partial harvest and would have
  put the footprint's NO-VENDOR-LAND verdict at risk. Re-fetched
  https://abracon.com/datasheets/ABM8-272-T3.pdf today: **330972 bytes, sha256
  aead22b6bd9d6f8ad4472352f70fce3ade633e90b9772ba80fabe8fd0856ae91 —
  byte-identical to the committed file — and `pdfinfo` reports `Pages: 3`.** The
  document Abracon publishes IS three sheets; the "of (9)" is the vendor's own
  Word-export artifact (Creator: "Acrobat PDFMaker 24 for Word"). Stated narrowly:
  this proves the CITED document is complete as published, not that Abracon has
  no land recommendation elsewhere.
- result: **THE STROKE FIGURE, AND THE CORRECTION I OWE UPWARD IS ITSELF A
  CORRECTION.** The canon is now right (`published_stroke_min_height: 0.9375` as
  DATA on all five tiers, G-SELFCON grading both directions) and this board was
  already at 0.95/0.152, so no copper changed. But "0.60/0.70/0.80 all emit
  0.130" is true only of the BOARD-SILK formula. The refdes path uses
  `max(min_silk_stroke, 0.09, 0.20 x size)`, under which 0.60 emits **0.12** and
  0.75 mm is the first height reaching 0.15. MEASURED, every silk text on this
  board classified: 10 captions 0.95/**0.152**, 7 captions 0.60/**0.130**, 44
  refdes 0.60/**0.120**, 17 refdes 0.45/**0.1125**. So 61 refdes sit below JLC's
  published 0.15 stroke and only the ten port labels clear it. Not churned at
  stage 5 (taller glyphs would strand more refdes than the two already stranded);
  carried in CHECKLIST as an order-day DFM item with its numbers.
- next: **STOP — STAGE 5 REMAINS THE HANDOFF BOUNDARY; NOTHING WAS ROUTED.**
  Stage 6 owns routing. FIVE SKILL PATCHES PROPOSED, NONE MADE (skills/ was
  off-limits, an agent is live in there): (1) `refdes_waiver.json` is written BY
  generate_board and honoured BY policy_audit's P-SILK-REF, so checker and checked
  share a method (canon M1) — P-SILK-REF should require a project-side evidenced
  entry per machine-waived refdes, which is why this board now carries one even
  though the row is PASS; (2) `WARN silk caption crowded` should say WHICH test
  failed — an out-of-frame miss of 2 um and a real pad collision print the same
  word; (3) the caption slot search should try rotation 0/90 the way the refdes
  search does, since rotation is what rescued all five of this board's degraded
  captions and no amount of translation could; (4) `published_stroke_min_height`
  cannot be true for both stroke formulas at once and is currently the
  board-silk one — the refdes pair needs its own published figure (0.75); (5)
  M-REPRO's byte-identical banner still overstates: two runs differ in footprint
  ORDER while every property is identical. Carried from before and unchanged:
  P-COLLIDE's 7 anchored courtyard overlaps remain MEASURED false positives (DRC
  reports 0 `courtyards_overlap` with that rule at severity error, because the
  generator compares axis-aligned bboxes on jacks rotated 15/45/75 degrees).
