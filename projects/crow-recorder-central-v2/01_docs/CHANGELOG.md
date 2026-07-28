# Changelog

One entry per REVISION (a design state, git-tagged). Reverse-chronological.
`Released:` is `no`, or the name of the `07_releases/` directory that shipped it.

## v1.9 — 2026-07-28 — FIRMWARE + DOCS ONLY (retune of v1.8)

- **No copper, no BOM, no netlist, no release.** Same shape as v1.8. v1.7
  remains the live, sealed, orderable release; the pod's v1.3 likewise.
- **THE ACCEPTANCE CRITERION CHANGED, not just the constant.** USER DECISION:
  CAL-1 as filed sized the shortfall against LS1's datasheet MINIMUM output,
  which is the wrong end of the tolerance for a CLIPPING problem — the unit
  that clips is a LOUD one. The criterion is now **"clears a unit on the
  datasheet's TYPICAL curve"** (~104 dB @ 10 cm at 3.9 kHz, rev 1.04 p.3):
  burst **110.8173 dB SPL** at the capsule, ceiling 101.3144, **binding
  shortfall 9.5028 dB** (was 5.5028 against the minimum-spec unit).
- **The constant.** `CAL_BURST_DUTY_DEN` **6 → 12**. Nominal attenuation
  `20·log10(sin(π/12))` = **−11.7401 dB** → **99.0772 dB SPL** typical /
  95.0772 dB minimum-spec, clearing by **+2.2372** / +6.2372 dB. The old 1/6
  cleared the OLD criterion by 0.52 dB and MISSES the new one by 3.48 dB.
- **`sin(πD)` IS NO LONGER A CONSERVATIVE BOUND, and the old conclusion is not
  carried forward.** v1.8 established the law as a conservative bound at 1/6
  by integrating the L-R-diode circuit over 20 µH…3 mH. Re-run at 1/12, it
  fails — for TWO reasons, one predicted and one not:
  - **L-R regime change** (predicted): the 20.8 µs pulse no longer lets the
    current build, the long freewheel tail dominates, and the L = 3 mH corner
    returns **−10.905 dB** against the law's −11.740 — **+0.835 dB
    non-conservative**. At 1/6 every corner had been conservative.
  - **Gate-RC duty bias** (NOT predicted, and the dominant term): turn-ON waits
    only for the gate to CLIMB to `Vgs(th)` (20–44 % of the 3.3 V drive), but
    turn-OFF waits for it to FALL from ~3.26 V DOWN to `Vgs(th)` (56–80 % of
    the way). The lags are asymmetric, so the conduction window is **STRETCHED
    by +1.11…+6.47 µs**. Being an ABSOLUTE time, its fractional cost grows as
    the duty shrinks: **5 % of the pulse at D = 1/2, 31 % at D = 1/12.**
    DETAIL_DESIGN had documented this RC purely as an EMI slew-limiter; nobody
    had noticed it also biases the duty upward, which only becomes a defect
    once duty is used to control LEVEL.
  - **Combined worst case: −8.71 dB, not −11.74 dB. Slack +3.03 dB.**
- **So the criterion is met NOMINALLY (+2.24 dB) and MISSED under the
  worst-case model (−0.79 dB), and that is recorded as OPEN, not smoothed
  over.** The minimum-spec unit still clears worst-case by +3.21 dB. The real
  finding is structural: **the open-loop uncertainty (~3 dB) is LARGER than the
  criterion (2.24 dB)**, so this level cannot be set open-loop to the accuracy
  the criterion demands. Trim against a MEASUREMENT at bring-up, or take
  `DEN = 14` — the first value that clears worst case (+0.11 dB; 16 → +0.93,
  20 → +2.41). Scoping `BEEP_RETURN` at TP11 against the commanded pulse reads
  the stretch directly and collapses most of the 3 dB.
- **Trim floor 16 → 24.** The old floor would have forbidden 1/14…1/20 —
  exactly the values that fix the worst case. At 1/24 the gate still peaks at
  2.94 V, clearing the AO3400A's 2.5 V Rdson spec point; past ~1/37 it never
  reaches 2.5 V at all.
- **Test moved to the new criterion and re-RED-verified.** `make test` **PASS,
  0 failures**, and now carries BOTH old values as ALWAYS-RUN inline known-bad
  fixtures (den 2 → −9.50 dB, den 6 → −3.48 dB against the typical unit), so
  the gate proves it can fail on every run rather than only on a recompile.
  Recompiled at `DEN = 2` and at `DEN = 6`: **6 failures each, exit 1 both
  times.** A new assertion pins the declared worst-case constant to the model,
  so a future retune cannot silently leave the uncertainty stale.
- **Far end re-checked at the new duty, still fine.** Far-pod matched-filter
  SNR 42.95 dB at a 25 dB(⅓-oct) ambient and 22.95 dB at 45 dB, timing σ
  0.28–2.83 µs against a 20.83 µs sample. Local path 95.077 dB SPL, 81.1 dB
  above the mic's own self-noise. Coil average current now ~10–25 mA (deep
  DCM), shared Q2 ~60–150 mA, pod capsule headroom to its 110 dB THD limit
  10.92 dB (typical) / 14.92 dB (minimum-spec).
- One quantization note: the timer rounding error grew from −0.0006 dB at 1/6
  to −0.0014 dB at 1/12, because `sin(πD)` is steeper at small D. Negligible
  now; the test's tolerance is stated against that physics rather than a
  round number.
- Released: no

## v1.8 — 2026-07-28 — FIRMWARE + DOCS ONLY (SUPERSEDED BY v1.9 SAME DAY — the duty below was retuned 1/6 → 1/12 when the acceptance criterion moved to the TYPICAL-curve unit; kept for the record)

- **No copper, no BOM, no netlist, no release.** `04_kicad/` and `07_releases/`
  untouched; `03_src/` and `03_tscircuit/` untouched. **v1.7 remains the live,
  sealed, orderable release.** Release payloads are
  `fab/ source/ verification/ 3d/ pdf/ MANIFEST.txt ORDER_README.md` and carry
  no firmware, so nothing here is supersedable or needs to be superseded.
- **What changed, and why it is a design state at all.** This board's
  calibration-burst DRIVE LEVEL is now defined, bounded and derived. It was
  previously undefined — and the obvious first cut (50 % duty, the CMT-8504's
  own characterisation condition) is the one value that is WRONG.
- **The defect is on the sibling board.** `crow-mic-pod-v2` CAL-1: LS1 sits
  45.61798 mm from MK1, putting **106.8173 dB SPL** on the capsule against an
  OPA1678 worst-case linear input-common-mode ceiling of **101.3144 dB**.
  Shortfall **5.5028 dB** — the calibration transducer saturates the preamp it
  exists to calibrate. The pod cannot fix it (its divider was measured unable to
  clear the guaranteed spec by ANY value, best +0.86 dB, optimum in the opposite
  direction), so the user's chosen fix is a ~6 dB drive reduction HERE. The pod
  v1.3 release stays live and is NOT superseded.
- **Established first: the level is firmware, and only firmware.** Measured from
  the SEALED v1.7 netlist, not the source — `PLUS5V_BEEP` is the 5 V rail
  through a ferrite bead with **no series resistor and no regulator** (11 nodes);
  `BEEP_RETURN` is **one AO3400A for all eight ports** (10 nodes, BRIEF D1);
  `BEEP_GATE` has exactly **two** nodes, `U1.122` and `R_bg1.1`. There is no
  analog level control on this board. The GPIO waveform is the only lever.
- **The constant.** `05_firmware/cal_burst.c`, `CAL_BURST_DUTY_NUM/DEN = 1/6`
  → `20·log10(sin(π/6)) = −6.0206 dB` of 4 kHz fundamental → **100.7967 dB SPL**
  at the capsule, clearing the ceiling by **0.5178 dB**. Named, derived in place,
  with a trim ladder and a trim floor (duty 1/16, where the 4.7 µs gate RC stops
  fully enhancing Q2). `make test` re-derives every number from the physics:
  **PASS, 0 failures**, and **RED-verified** — rebuilt at the pre-fix `DEN = 2`
  it reports 5 failures including a negative ceiling margin, and exits 1.
- **The model, stated because it is not free.** SPL follows the 4 kHz
  FUNDAMENTAL, not the RMS: the datasheet's own response curve (rev 1.04 p.3)
  is a sharp resonance peaking ~104 dB at ~3.9 kHz, and a resonator passes the
  component at resonance. `sin(π·D)` holds at BOTH ends of the coil's
  unspecified inductance and a numerical L-R-diode integration over
  20 µH…3 mH returns −6.02…−6.68 dB, so the law is a conservative bound. Model
  sanity by a second method (canon M1): the datasheet's MEASURED 150 mA at ½
  duty vs an ANALYTIC volt-second balance of 151.7 mA — 1.1 % apart.
  Electrical→acoustic is **ESTIMATED, not specified** (the datasheet has no
  SPL-vs-drive curve) and deliberately conservative.
- **The far end of the link budget was checked, and 6 dB does not break it.**
  All six pods fire together, so each pod's dominant path is its own LS1;
  the five others power-sum to 67.0 dB SPL, **39.8 dB below** the local path.
  Far-pod matched-filter SNR after −6 dB is 48.7 dB at a 25 dB(1/3-oct) ambient
  and 28.7 dB at 45 dB, giving a timing σ of 0.15–1.5 µs against a 20.83 µs
  sample. Massive margin at both ends.
- **Owed, and flagged, not silently absorbed.** (a) CAL-1's shortfall uses LS1's
  datasheet MINIMUM; a unit at the datasheet's TYPICAL curve (~104 dB @ 10 cm)
  lands at 110.8173 dB and stays **3.48 dB over** the ceiling even after
  −6.02 dB, so the level must be TRIMMED AGAINST A MEASUREMENT at bring-up.
  (b) The operator-facing copy of this constraint is owed to the NEXT release's
  `ORDER_README.md` — every existing one is inside an immutable sealed release
  and cannot be retro-filled.
- Released: no

## v1.7 — 2026-07-27
- **SOURCING supersede of v1.6. NO COPPER CHANGE.** v1.6 is not wrong and its
  board is this board; it is UNORDERABLE because JLC cannot SUPPLY one of its
  47 coded lines.
- **The blocker.** `C25767` (UNI-ROYAL 0402WGF2203TCE, 220 kΩ 0402, `R_vb1`)
  reads `stockCount: 0`. It is ON the CPL (1 × 5 boards = 5 needed), carried no
  `sourcing_plan:` and sat on no watch-list. **At the v1.6 seal it measured 16
  and graded `OK`** — nothing distinguishes "clears 5× need" from "clears it by
  eleven units", and the watch-list that release DID name (`C5224055` 383,
  `C882626` 496) missed the line at 16.
- **The substitution.** `C138030` / YAGEO `RC0402FR-07220KL`, stock **736 704**,
  same 0402 land, catalog `describe` string **character-identical** (compared as
  strings), same RC0402FR series as this board's existing `C60490`/`C105871`
  swaps. Q-IDENT: the record's MPN exactly equals the authoritative MPN the
  vetted passives ledger already holds for that code — a sourced line, not a
  proposal. Changed at SOURCE (`supplierPartNumbers` in the `.tsx`), never in
  the CSV (canon M3).
- **The copper did not move, measured.** Board md5
  `de39e145e856cb14d491770c77d1ec0a` identical across `04_kicad/`, v1.6 and
  v1.7; gerbers+drills **17/17 byte-identical after the timestamp strip** when
  RE-PLOTTED from this release's own board; `fab/cpl.csv` byte-identical;
  `fab/bom.csv` 49 → 49 rows, designators identical in order, **exactly 2 cells
  changed**, both on `R_vb1`.
- **Gated by an assertion, not by waivers.** `release_freshness_check.py
  --sourcing-supersede` landed with this release under canon M8 — usb-hub-3s-v3
  v1.11 shipped the identical shape behind SEVEN hand-written file waivers.
  v1.7 carries **zero** freshness waivers.
- **Also carried in** (2026-07-27 order-readiness audit): two stale
  ORDER_README sentences that were true at v1.4 and false from v1.6 on; a stale
  `verification/twin_top.png` byte-identical to v1.5's, on which A-RENDER FAILED
  while the same sealed BOARD renders faithfully — regenerated here; the first
  ever F-PAYLOAD and A-RENDER reports for this board; and three page anchors in
  `02_parts/XC6227C331PR-G/part.yaml` that were all low by one (values right,
  citations unresolvable — under M-IMPORT that is the part that matters).
- Released: `crow-recorder-central-v2-v1.7-2026-07-27`

## v1.6 — 2026-07-27
- **BOM-LEGIBILITY supersede of v1.5, plus one rail declaration. NO COPPER
  CHANGE, and v1.5 is NOT DO-NOT-ORDER** — its board is this board.
- **What was wrong.** v1.5's `fab/bom.csv` was uploaded to JLCPCB and the parts
  "were not being picked up by their web processing". Graded the way the
  RECIPIENT parses it (canon **F-LEGIBLE**, ADR-0006) the sealed file carries
  **72 findings**: 47 F-MPN (every coded row ships a blank MPN, so JLC's matcher
  leaves a code-only line at *No Part Selected*), 24 F-WORDS (the Comment is an
  LCSC code or a `simple_chip`/`simple_inductor` generator stand-in) and
  1 F-ENCODE (the ohm sign with no UTF-8 byte-order-mark, so a cp936 reader
  renders `CE A9` as the mojibake the user saw). **v1.6: 0 findings.**
- **Five dossiers needed a source fix, and the answer was already in the tree.**
  `1277AS-H-1R0M`, `1277AS-H-2R2M`, `BLM21PG600SN1D`, `BLM21SP601SN1D` and
  `TLV70018DDCR` declared their code as a bare top-level `lcsc:` instead of the
  `sourcing: {lcsc: ...}` block the 02_parts contract mandates and the F-MPN
  authority reads. Y1's NDK crystal genuinely has no dossier and gained a
  catalog-verified ledger row (`C2762192` = `NX3225SA-24MHZ-EXS00A-CS08583`).
- **E-TOPO: FAIL → OK, and this is the second half of the release.** E-TOPO
  gained LINEAR-regulator support on 2026-07-27, *after* v1.5 sealed, and
  reported `UNGRADED CONVERTERS: 2 of 3` — this board's `1V8` (U9) and `3V3A`
  (U10) rails lived in a COMMENT in `power_tree.yaml`, so **two of its three
  regulators had never been graded by anything.** Both are now declared and
  graded on dropout and dissipation:
  `1V8` headroom 1382 mV vs **620 mV**, PD 81 mW vs **200 mW** (40%);
  `3V3A` headroom 1567 mV vs **200 mV**, PD 147 mW vs **500 mW** (29%).
  All four numbers CITED to figure/page in the converters' own `part.yaml`
  (Toshiba TCR2LF series 2014-11-06 pp.2/4; Torex ETR03054-006 pp.3/6 of 23),
  both dropouts taken at a HIGHER current than the rail draws so each bounds it
  from above. Rail currents DERIVED from the netlist, not assumed — and where
  XMOS publishes no VDDIO operating current the estimate carries its bar
  (5 ± 5 mA) rather than borrowing the 126 mA absolute maximum.
- **The copper did not move, measured three ways.** `.kicad_pcb` md5-identical
  (`de39e145e856cb14d491770c77d1ec0a`) to v1.5's and to `04_kicad/`'s; gerbers +
  drills **re-plot 17/17 byte-identical** to v1.5's sealed archive after the
  timestamp strip; `fab/cpl.csv` byte-identical; 20 of 21 payload files
  sha256-identical. Asserted mechanically by
  `release_freshness_check.py --legible-bom-supersede`.
- **Regenerable from source, proven (canon M3).** The shipped BOM was re-exported
  from `03_src/` + `03_tscircuit/` + `02_parts/` and came out sha256-identical to
  an independent earlier generation of the same release
  (`d2cdad3ab4742d1e…`) — two runs, one artifact.
- Released: `07_releases/crow-recorder-central-v2-v1.6-2026-07-27`

## v1.5 — 2026-07-25
- **CPL-CORRECTION supersede: v1.4 is DO-NOT-ORDER for PCBA.** v1.4 places J2,
  the board's ONLY USB-C connector, **1.3025 mm off its own pads**. Its contacts
  are 1.150 mm long, so pad overlap is **0.000 mm** — not a marginal joint, no
  joint at all — and the four shell posts miss their holes, so the part cannot
  physically seat. A v1.4 board has no USB power and no USB data.
- **ROOT CAUSE: the CPL emitted the wrong DATUM.** JLC places a part so that
  *its own* origin lands on `Mid X/Y`, and that origin is the **centre of the
  bounding box of the pad centres**. `export_jlc_package.py` emitted KiCad's
  **footprint anchor** — an authoring convenience with no fab meaning — for the
  fleet's entire history. The two coincide for most parts (which is why this was
  never seen) and diverge on CONNECTORS, where the anchor sits on pin 1 or a
  mounting feature. MEASURED over **228 cached JLC-native footprints across six
  boards**: origin == pad-centre bbox to ≤0.01 mm in **227 (99.6 %)**. Two weaker
  readings were tested on the same 228 and REFUTED — bbox of pad *outlines*
  213/228, *centroid* 198/228; the outline reading would have left J2 0.1625 mm
  out. Fixed at source in `placement_datum()`; the class is fleet-wide (anchor ≠
  datum on 12/203 here, 12/227, 12/114, 14/238, 2/40, 1/39 on the others, up to
  24.16 mm).
- **New gate A-POS** (`assembly_coverage.py`): `CPL-DATUM-OFF` grades every
  placed row's coordinate against the pad-array centre (tol 0.05 mm), and
  `CPL-NOT-SMT-PLACEABLE` fails a ref with plated drilled pads and F.Paste on
  none of them on an SMT-only order. Pin-in-paste is exempt BY MEASUREMENT, not
  by the `through_hole` attribute. Known-bad fixture: the sealed v1.4 bytes.
- **J1 off the CPL** (`process_incompatible`, a new closed-vocabulary reason): a
  true THT barrel jack — 3 plated pads, F.Paste on none — on a `sides: [top]`
  order, and the board's ONLY power inlet. `assembly.yaml`'s contradicting clause
  ("the only other THT parts are already off the CPL") is corrected.
- **R_inj1/R_inj2 off the CPL** (`dnp_by_design`): 1 kΩ + 1 kΩ tying ADC ch1 to
  ch5 through a floating INJ net (JP_INJ is unstuffed), i.e. **−26.5 dB**
  crosstalk against a 110 dB spec, on a board whose product IS isolation.
- **BLOCKING REWORK, all boards:** 2× 33 pF 0402 piggybacked across R_fb1a and
  R_fb2a — the AP61102 C3 feedforward caps, absent on both rails. Datasheet
  DS42004 Rev6-2 Table 1 gives 33 pF at EVERY Vout in the AP61102 column, and
  pin 6 is PG (not OUT), so the part is permanently in the Figure-2 case. 3V3
  loses **5.52×** of its FB ripple without it; 0V9 only 1.50×. No copper needed.
- Rotations UNCHANGED from v1.4. Payload identity PROVEN BY RE-PLOT: 15/15
  gerber/drill members byte-identical after timestamp strip; `fab/cpl.csv` is the
  only file in the whole release that differs. Asserted mechanically by the new
  `release_freshness_check.py --cpl-only-supersede` mode, which also FAILs any
  rotation/layer/identity change or added row.
- U1's MSL-3 / 168 h floor life is now an EXECUTABLE part fact (canon P-FACT)
  rather than prose; 4 AP61102 divider values pinned via canon E-INV part_value.
- Released: `07_releases/crow-recorder-central-v2-v1.5-2026-07-25`

## v1.4 — 2026-07-25
- **CPL-CORRECTION supersede: v1.3 is DO-NOT-ORDER for PCBA.** v1.3 shipped SEVEN
  CPL rows 180 deg off — U1 (C6938291, the CONSIGNED XU316 TQFP-128, 0.4mm pitch),
  U2+U3 (C181312 PCM1865 TSSOP-30), U5 (C82317 SOIC-8), U7+U8 (C5224055 SOT-563)
  and D_USB (C90627 USON-10), i.e. every fine-pitch part on the board — all at
  90.0 where the measured value is 270.0. v1.0/v1.1/v1.2 shipped these SEVEN
  correctly at 270; v1.3 "fixed" a non-defect. ROOT CAUSE (fixed at source before
  this release): jlc_twin.xform() used the OPPOSITE handedness to the operator
  KiCad applies to a rotated footprint's pads, negating every jlc_offset —
  invisible at 0/180 (sign-invariant), exactly 180 deg wrong at 90/270 (1b69760,
  pinned by two RED-verified tests against pcbnew). jlc_lcsc_rotations.csv had
  been POPULATED FROM that function, so six rows inherited the negation and an
  external reviewer reading the table was misled (canon M1); corrected in e0d735c.
  Q1/Q2/U9 are UNCHANGED because their values are 180, which the negation cannot
  move — that asymmetry is the root cause's fingerprint.
- ACCEPTANCE GATE (stated as a number BEFORE looking): the v1.4-vs-v1.3 CPL diff
  is EXACTLY SEVEN changed CELLS, all Rotation, all 90.0 -> 270.0; 0 rows added or
  removed; Q1/Q2/U9 byte-identical. Measured cell-by-cell. The seven angles were
  then RE-DERIVED by a method sharing no code with the twin/resolver/exporter
  (pcbnew for our pads, a text parse of JLC's own cached footprint for theirs,
  operator proven against pcbnew first): all seven fit at 270 with residual
  <= 0.0725mm against a runner-up 15x-4811x worse, 0 mismatches vs the shipped
  CPL. verification/cpl_acceptance_gate.md + rotation_remeasure.txt.
- NO COPPER CHANGE, proven by RE-PLOT rather than by copying: all 15 gerber/drill
  zip members hash identically once the plot's own timestamp comments are stripped;
  20 payload files are sha256-identical to sealed v1.3 and fab/cpl.csv is the only
  file that differs (verification/replot_identity.txt + payload_identity.txt).
- **PCBA gates land on this board.** 03_src/rules/assembly.yaml is authored (A-POP
  PASS: board 203 / cpl 177 / unpopulated 26 = 10 declared + 16 exempt H,TP), with
  U1 moved from v1.3's `not_assembled` prose into `consigned:` — a consigned part
  is POPULATED — carrying the REQUIRED msl: (MSL 3, 168h floor life, XU316 ds
  v2.0.0 s14.5 p33; also backfilled into the part.yaml limits: block, which was
  missing it). J3-J10 declared not_in_catalog with the dated catalog query;
  JP_INJ/J_DBG re-classified dnp_by_design after proving JLC DOES stock 2.54mm
  headers — "hand-solder" is a wall you prove you hit, not a style. A-STOCK PASS
  at build_quantity 5 with verification/stock_check.json and a sourcing_plan entry
  for C6938291 (JLC stock MEASURED 0; consigned, so JLC stock is irrelevant) —
  v1.0-v1.3 all shipped a stock report ending in FAIL that nothing ever parsed.
- Archive self-containment CHECKED, not assumed: a standalone DRC on a copy of
  source/ alone is 0/0/0 with zero lib_footprint_issues (this board's fp-lib-table
  resolves both vendored libraries via ${KIPRJMOD} and they ship inside source/),
  so it does NOT have the usb-hub-3s-v3 v1.3/v1.4 out-of-archive-pointer defect.
- Project contracts.md copies re-synced from skills/pcb-design/templates/contracts/
  (01_docs, 02_parts, 03_src, 03_src/rules, 07_releases) — this revision is when
  they catch up, per CLAUDE.md.
Released: crow-recorder-central-v2-v1.4-2026-07-25

## v1.3 — 2026-07-24
- CPL/evidence-only supersede closing the THIRD external review of v1.2 (HOLD-
  for-PCBA; archived 08_reviews/2026-07-24_v1.2_external-llm_full.md). Root cause:
  jlc_rotations_db.csv keyed by FOOTPRINT NAME while JLC orients per LCSC PART —
  the sealed v1.2 CPL shipped U1 (consigned XU316) at 270 deg vs its exact pad-fit
  90 deg (180 deg off), plus 9 more ROT-DB-SUGGEST rows. Fixed at the source: new
  per-LCSC rotation table skills/jlcpcb-fab/scripts/jlc_lcsc_rotations.csv checked
  BEFORE the name-DB (RED-verified, fleet-wide fix). CPL regenerated -> twin 0
  ROT-DB-SUGGEST (was 10). missing_models corrected 172->177; ORDER_README gains
  U1 rotation-closure + JLC-preview pin-1 human gate + 8-beeper aggregate-load
  (~1.2A vs 2A fuse) + MSL-3 consigned-U1 handling. Copper/gerbers/drill/BOM/source
  byte-identical to v1.2 (documented in freshness_exceptions.txt). Fresh-lens ORDER.
Released: crow-recorder-central-v2-v1.3-2026-07-24

## v1.2 — 2026-07-24
- Respin closing the SECOND external review of v1.1 (HOLD; archived verbatim
  08_reviews/2026-07-24_v1.1_external-llm2_full.md, EXT2-F1..F5 dispositioned).
  EXT2-F1 (the driver): 0V9 core rail had 8x 100nF for 15 XU316 core-VDD pins
  vs the vendor minimum — VERIFIED at the datasheet (XM-014532-PC-2.0.0 §14
  "Integration" p.29: "at least 12" 100nF low-inductance MLCCs close to the
  chip; §H.2 p.92). v1.2 ships 13x (C_c1..C_c13): C_c9 -> pins 11/14 (1.63mm),
  C_c10 -> pin-5 pocket (0V9 pad on the existing 0.5mm feeder), C_c11/C_c13 ->
  pins 50/54 (2.01/2.02mm, via the C_b0v9 bulk slot swap — bulk has no
  pin-adjacency requirement per ds §14, moved 3.75mm south with a B.Cu feed),
  C_c12 -> pin 95 (2.55mm). TDI F.Cu run rerouted to In3 to free the south
  band; 32 U1-cluster floaters pinned at their exact v1.1 positions so only
  the intended copper changed; netlist diff vs v1.1 = exactly the 5 caps
  (verification/decoupling_fix.md). EXT2-F2: ORDER_README §4a rail-sequencing
  scope gate strengthened (all startup corners + explicit 1V8-before-0V9 +
  reset-held pass condition; interlock = v-next design item, never a delay
  tweak). EXT2-F3 (D_USB stub) carried P2 + in-line-ESD pre-production v-next.
  EXT2-F4 (RJ45/PoE + DC OVP) = ADR-0007 USER waiver carried UNCHANGED.
  USB pair / U1 EP via grid / LV-strap floats re-measured intact.
Released: crow-recorder-central-v2-v1.2-2026-07-24

## v1.1 — 2026-07-24
- Respin closing the external DO-NOT-ORDER review of v1.0 (orchestrator-verified;
  08_reviews/2026-07-24_v1.0_external-llm_full.md, EXT-F1..F6 dispositioned).
  F1: U1 (XU316) EP thermal grid remodeled from 16 duplicate-numbered thru-hole
  pads (emitted ComponentDrill) to 16 REAL GND vias (ViaDrill T1) seeded by
  03_src/add_u1_thermal_vias.py at rebuild step 3.5; board setup capping/filling
  = yes; filled+capped via-in-pad explicitly ordered (ORDER_README §1a) + X-ray
  first-article gate. F2: USB_DM renamed USB_DN (KiCad pairs only P/N suffixes),
  USB_DIFF netclass with diff_pair {0.125/0.15} solved for JLC06161H-3313 (2D FD
  field solve 89.7-90.5 ohm, verification/usb90_solve.md), pair rerouted with KRT
  route_diff: spread 0.110mm, all F.Cu, 0 vias; diff-pair DRC rule ACTIVE
  (proven able to fail); R-LEN now graded via audit_board skew gate. F4: all
  evidence regenerated against the staged archive itself (standalone-source DRC
  0/0/0; manifest counts == shipped evidence; bom_source/stock name the sealed
  dir). Promoted converter sch guarded in rebuild_all (dogleg surgery survives
  regeneration). PR2-P0-1 (this release's own zero-context pin review): U1
  LV_L_N/LV_T_N/LV_R_N straps (40/43/52) were 3V3-tied on the FIXED-1.8V IOB
  bank (AMR VDDIO+0.5=2.3V, ds v2.0.0 §4.4/§4.8/§15.1) — fixed to the
  datasheet float select; netlist diff vs v1.0 = exactly 7 node moves (4 USB
  rename + these 3). Sourcing: RG1/R_cs/R_rst -> C60490, R_scl/R_sda ->
  C105871 (basics stocked out). ADR-0007 RJ45/beeper USER waiver carried
  UNCHANGED.
Released: crow-recorder-central-v2-v1.1-2026-07-24

## v1.0 — 2026-07-23
- P0 fix pass sealed: two geometric net-merges (P5VA_4->AUDIO4M, MID2P->5V)
  fixed at source; check_port_nets gate added (115/115 labels, 8/8 ports).
  P1 set closed with measured evidence (5V trunk 0.5mm + 1144mm2 pours,
  P-ADJ local measurements, 8x per-port NOT-ETH silk, ADR-0005 amendment,
  ADR-0007 PoE waiver carried from pod-v2). audit_board (P-POL/P-KEEP) added,
  red-tested. Sourcing staged: TLV70018 for TCR2LF18 (stock 0), NX3225SA for
  FA-238 (stock 0), 402k for 400k (not stocked), BLM21SP601SN1D for the
  mislabeled 60R bead (wrong-part catch); XU316 + RJ45 consignment per
  ADR-0003. DRC 0/0/0; policy_audit 0 FAIL; ERC 0 err; count_parity 194 x4.
Released: crow-recorder-central-v2-v1.0-2026-07-23

## v0.1 — 2026-07-23
- Commissioned crow-recorder-central-v2 (mixed-signal-audio-hub class), CLEAN-ROOM
  from the brief + sanctioned skill references. ADR-0001..0006 written; fab_tier
  = jlc_6layer_smallvia (ADR-0002); netclasses + ampacity floors defined BEFORE
  routing (03_src/rules/nets.yaml). Parts research fanned out (18 parts; 8 ledger
  hits). Schematic (tscircuit) authoring in progress.
Released: no
- Placement: mixed-signal-audio-hub floorplan (39 anchors + 155 pattern-placed
  passives), 6-layer In1+In4 GND planes; audit_template I1-I8 PASS (0/0). Project-
  local footprints: TQFP-128_EP (16-via grid), US8, vendored numeric-pad USB-C+RJ45.
  generate_rules merged 5 netclasses into 04_kicad. Routing (KRT) in progress.
