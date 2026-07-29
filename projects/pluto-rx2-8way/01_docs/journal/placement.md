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
