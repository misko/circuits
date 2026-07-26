# Red-team lens B — LAYOUT, FABRICATION AND ORDER PAPERWORK
cooksense v1.3, run 2026-07-26 against the staged archive. Adversarial brief:
find reasons the ORDER would go wrong. Read-only; no rebuild, no export.

VERDICT AT RUN TIME: **DO NOT ORDER.** One P0 (since fixed), plus paperwork
findings. Re-verified after the fixes; the geometry findings were all NEGATIVE,
i.e. the board itself is sound and the defects were in what shipped WITH it.

## P0 (at run time) — R_WDPETPD assembled at 100k
Found independently of lens A, from the BOM side rather than the datasheet side:
bom_jlc.csv groups R_WDPETPD onto the C25741 line whose Comment reads
"100kΩ / 1kΩ" and whose LCSC is 0402WGF1003TCE = 100k, while the tsx, the board
Value field, the CPL Val column and an E-INV assert all say 1k.
FIXED at c9e0b3a (pinned to C11702 = 0402WGF1001TCE = 1k) and re-verified: the
BOM line is now `1kΩ,"R_SER0..7,R_WDPETPD",R_0402_1005Metric,,C11702`.

## P1 — the board silk named a revision that was never sealed
F.SilkS carried `cooksense  SMC0985KS  sidecar v1.2` on a v1.3 release, sitting
between two DO-NOT-ORDER releases, on a board with real physical deltas (H4
notch, merged J_ISOLOOP). FIXED: bumped to v1.3 and rebuilt; refdes-on-silk
unchanged at 216/222, crowded captions unchanged at 2.

## P2 — paperwork, all fixed in the re-stage
- MANIFEST/EVIDENCE ERC mismatch (1533 vs 1311) — a bare-directory ERC run;
  see the sibling-context appendix in stranded_islands.md.
- policy_audit.md shipped FAIL=4 contradicting the MANIFEST's green rows; three
  of the four are policy_audit's multi-board mis-targeting (it grades
  `rels[-1]`, which sorts to interposer-v1.0), now annotated at ship time.
- Stale v1.0/v1.1/v1.2 artifacts in verification/ (renders showing J_CONTACTOR
  at the SE corner, a v1.2 stock_check naming C67470 LM393DR, an
  einv_red_verification proving 3 of 63 on a release claiming 83). ALL
  regenerated from the corrected build in the re-stage.

## CHECKED AND FOUND CORRECT — this bounds the coverage, and it is the useful half
- **CPL datum**: all 189 rows re-derived independently from source/cooksense.kicad_pcb
  against the bounding-box centre of PAD CENTRES. Max error **0.00000 mm**.
- **CPL rotations**: all 189 reproduced from `(board_rot + measured per-LCSC
  offset) mod 360` using jlc_lcsc_rotations.csv. **0 mismatches.** No row 90 or
  180 out.
- **Vias**: all 1045 at 0.25 mm / 0.15 mm — the ADVANCED small-via option is
  genuinely required and genuinely met. Standard 0.45/0.30 would not build.
- **Hole-to-hole**: minimum 0.2972 mm, above the declared advanced-tier 0.25 mm
  floor.
- **Board outline**: a single valid closed polygon including the H4 edge notch;
  the 12 milled isolation slots are 0.6 mm, above router-bit minimum.
- **Gerbers**: the zip contents are byte-identical to the loose files; 11 layers
  + 2 drill files, none empty, none missing.
- **Population**: 226 board footprints, 189 CPL rows, 37 unpopulated = 16
  declared in assembly.yaml + 21 exempt (H1-H4, 17 TP). Every unpopulated part
  has a reason with dated evidence. Nothing on the CPL that should not be.
- **THT on an SMT order**: after the v1.3 corrections, no through-hole part
  remains on the CPL.

## COULD NOT CHECK
- Whether JLC's own preview will render the parts as we expect — that is what
  the ORDER_README section 6 human gate exists for, and it is unavoidable.
- C42400616 (J_ISOLOOP) has no CAD in JLC's library, so it cannot appear in any
  preview render; verified by same-minute control fetch of C474892.
- Panelisation/tooling: not part of this archive.
