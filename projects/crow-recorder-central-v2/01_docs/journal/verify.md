# journal — verify / seal

## 2026-07-25 09:00 — start (v1.4)
- did: opened v1.4 to supersede v1.3 as DO-NOT-ORDER. v1.3 ships SEVEN CPL rows
  180 deg off (U1, U2, U3, U5, U7, U8, D_USB — every fine-pitch part on the
  board) after "fixing" a non-defect: v1.0/v1.1/v1.2 all shipped them at 270 and
  were right. Root cause already fixed at source: jlc_twin.xform() had the
  opposite handedness to KiCad's real operator (1b69760), and the per-LCSC table
  had been populated FROM that broken function (e0d735c).
- result: measured baseline on the sealed v1.3 bytes — A-POP FAIL (board 203 /
  cpl 177 / unpopulated 26 / declared 0; NO-ASSEMBLY-DECL + 26
  UNDECLARED-UNPOPULATED + DECLARED-BUT-PLACED on U1), A-STOCK evidence ends in
  `FAIL: 2 coded lines with problems` including LOW_STOCK(0) on the board's own
  CPU. Board itself unchanged and clean.
- next: re-export against the UNCHANGED 04_kicad board and hold the diff to the
  seven cells before anything else.

## 2026-07-25 10:20 — iterate 1 (the acceptance gate)
- did: re-exported the whole fab set from 04_kicad into 06_build/fab_v14 with the
  corrected per-LCSC table; diffed the new CPL against v1.3's cell-by-cell.
- result: EXACTLY 7 changed cells, all Rotation, all 90.0 -> 270.0 (D_USB, U1,
  U2, U3, U5, U7, U8). 177 rows both sides, 0 added, 0 removed, header and
  designator order identical. CONTROLS Q1/Q2/U9 byte-identical (their per-LCSC
  values are 180, which the negation could not move — the fingerprint).
- next: prove the direction independently. The twin agreeing is not enough: the
  twin is the tool that produced the defect.

## 2026-07-25 11:05 — iterate 2 (independent re-derivation, canon M1)
- did: wrote 06_build/tmp/rot_remeasure.py — our pads from pcbnew, JLC's from a
  TEXT parse of JLC's own cached .kicad_mod, matched by pad NUMBER,
  centroid-aligned, RMS-scored at 0/90/180/270, with the rotation operator PROVEN
  against pcbnew over every pad of every footprint on this board before use.
  Shares no code with jlc_twin / jlc_rotation_resolve / export_jlc_package.
- result: operator max error 0.000000000 mm at all four board angles; the pre-fix
  NEGATED form errs 35.560 mm at 90 and 0.960 mm at 270 and TIES at 0/180 — the
  incident's signature reproduced on this board. All 7 corrected parts fit at 270
  with rms <= 0.0725 mm against a runner-up 15x-4811x worse (U1: 0.0025 @270 vs
  11.9812 @0 over 129 numbered pads). Q1/Q2/U9 fit at 180. 0 mismatches vs the
  shipped CPL.
- next: prove the copper did not move.

## 2026-07-25 11:40 — iterate 3 (copper identity by RE-PLOT)
- did: compared the freshly-plotted zip member-for-member against v1.3's sealed
  zip, stripping only the plot's own timestamp comments.
- result: 15/15 members identical after stripping; raw 0/15 (every member carries
  its own timestamp); per-member diff is exactly 4 lines, all timestamp comments.
  So v1.4 SHIPS v1.3's gerber zip + drills VERBATIM and the sha256 identity is
  literal: 20 payload files identical, fab/cpl.csv the only file that differs.
- next: the PCBA gates v1.3 never had.

## 2026-07-25 13:10 — iterate 4 (assembly.yaml — the population set)
- did: authored 03_src/rules/assembly.yaml from the skill template. Measured the
  26 unpopulated refs on the board first: ALL 26 already carry
  exclude_from_pos_files, so no board change was needed (and none was allowed —
  copper identity is the point of this release).
- result: A-POP PASS (declared 10, consigned 1, exempt H/TP 16). Three decisions
  that took actual measurement rather than inheritance:
  * U1 -> `consigned:`, NOT `not_assembled:`. v1.3's manifest said
    "not_assembled: ... U1 (XU316 consign)" while U1 was ON the CPL. Consigned
    means POPULATED — we ship the part, JLC places it. It also needs `msl:`,
    which meant reading the datasheet: XU316 ds v2.0.0 s14.5 p33, MSL 3 / 168h
    floor life / bake per J-STD-033D. That row was MISSING from this project's
    part.yaml while the sibling crow-recorder-central board's copy had it —
    backfilled into limits: here.
  * J3-J10 -> `not_in_catalog`, with the catalog query as evidence: C9900035627
    and C9900056698 are both C99* consign-only codes at stock 0 with no CAD; the
    nearest stocked jack C464587 was MEASURED 2026-07-23 as not a land drop-in
    (pad 1<->13 ours 3.67 mm vs theirs 11.74 mm). A wall we hit and measured.
  * JP_INJ/J_DBG -> `dnp_by_design`, NOT "hand-solder". v1.3 called them
    "uncoded, hand-solder", which reads as scarcity. Queried it: JLC stocks 2.54
    mm THT headers (C2337 stock 86244, C52016391 stock 29861). There is no wall;
    they are deliberately unstuffed bring-up aids. "Hand-solder" is a wall you
    PROVE you hit, not a style — including proving you did NOT hit one.
- next: A-STOCK.

## 2026-07-25 13:55 — iterate 5 (A-STOCK)
- did: jlc_stock_check.py --json at build_quantity 5, shipped as
  verification/stock_check.json.
- result: the raw verdict line still reads FAIL — on exactly two lines, and
  neither accuses this release. C6938291 (the XU316) stock MEASURED 0, PLACED,
  covered by an assembly.yaml sourcing_plan entry saying plainly that it is
  CONSIGNED so JLC stock is irrelevant for that line. C9900035627 stock 0 but NOT
  placed. Every other coded+placed line clears 5x its per-board quantity; closest
  are C5224055 (383 vs 10) and C882626 (496 vs 5). release_freshness check (e)
  grades this PASS with both lines named. v1.0-v1.3 all shipped that same FAIL
  line with nothing parsing it.
- next: archive self-containment, then the full gate battery.

## 2026-07-25 14:30 — iterate 6 (archive self-containment)
- did: checked whether this board has the usb-hub-3s-v3 v1.3/v1.4 defect (a
  source/fp-lib-table pointing OUT of the release). Copied source/ alone into a
  scratch dir and ran DRC on it.
- result: it does NOT. Both vendored libraries resolve through ${KIPRJMOD} and
  ship inside source/; the rest are ${KICAD10_FOOTPRINT_DIR} (toolchain, not the
  archive). Standalone DRC 0/0/0 with ZERO lib_footprint_issues. Shipped as
  verification/standalone_archive_drc.json.
- next: full battery + fresh lens + the 2-commit seal.

## 2026-07-25 15:50 — finish (gates green on the staged archive)
- did: ran the whole battery against the staged v1.4 bytes.
- result: DRC 0/0/0 . standalone-archive DRC 0/0/0 . ERC 0 err / 1211 warn .
  parity 0 (116 nets, 598 nodes both sides) . count_parity 199x4 .
  check_port_nets 115/115 + 8/8 . audit_board PASS (USB spread 0.110 mm, U1-EP
  16 vias) . twin exit 0, 175 OK / 369 checked, 0 ROT-DB-SUGGEST, all ten
  per-LCSC rows OK src=lcsc . missing_models 177/177/0 . bom_source_check PASS
  (49 lines) . A-POP PASS . A-STOCK PASS at qty 5 . policy_audit 0 FAIL after
  the stamp . contracts_audit PASS.
- next: fresh-context lens over the staged bytes, then source commit S, stamp,
  seal commit.
