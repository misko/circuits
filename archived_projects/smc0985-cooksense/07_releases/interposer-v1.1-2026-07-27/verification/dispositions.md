# DISPOSITIONS — interposer (Board C) v1.1, 2026-07-27

Two ledgers, because this is a fix-pass release:

* **Part A** — the v1.1 review findings, all pre-seal (a finding here costs an
  edit; the same finding after the seal costs a supersede).
* **Part B** — v1.0's I1..I9, restated with what v1.1 changed about each.
  Nothing is silently dropped: a disposition that was RECORDED at v1.0 and is
  still RECORDED at v1.1 is said so out loud.

Source for Part A: `08_reviews/2026-07-27_interposer-v1.1_redteam_integrated.md`
(one integrated zero-context adversarial lens, both required lenses, verdicts
ORDER / ORDER, **0 P0**) plus the two targeted fix-pass re-confirmations
`verification/pin_review.md` and `verification/render_review.md` (both PASS).

---

## Part A — v1.1 findings

| # | Finding (severity) | Disposition | Evidence / change |
|---|---|---|---|
| R1 | Staging archive failed its own required-artifact gate: `release_required_check.py` exit 1, 8 REQUIRED artifacts absent (MANIFEST, ORDER_README, pin_review, render_review, both redteam files, policy_audit, parity) — and `source/assembly.yaml` load-bears on ORDER_README sections that did not exist (P1) | **CLOSED PRE-SEAL.** All eight written; `release_required.txt` re-run to exit 0. The reviewer read the archive mid-stage and reported the true state rather than assuming it would be filled — which is exactly right, and is why the gate is re-run and re-shipped after the fill | `verification/release_required.txt` (re-run), and the eight files themselves |
| R2 | The self-supply BOM row is not self-describing: Comment `10FDZ-BT`, **MPN cell blank**; the orderable variant `10FDZ-BT(S)(LF)(SN)` appears nowhere in the archive's order data, while the archive's own `assembly.yaml` warns the `-M` and `-ST` variants are scrap-on-arrival (P2) | **MITIGATED IN DOCS + RAISED AS CANDIDATE-CANON.** `ORDER_README.md` §2 now names the full `10FDZ-BT(S)(LF)(SN)` with the DO-NOT-SUBSTITUTE variants spelled out, and §0 repeats the `-ST` scrap condition. NOT fixed in `fab/bom.csv`: **F-LEGIBLE grades the MPN column on CODED rows only**, so an uncoded self-supply row's blank MPN is unreachable by the gate. Fixing it is a change to `export_jlc_package.py` — a fleet-wide exporter behaviour, out of scope for a board respin and owned by whoever next touches that skill. Raised as a background task | `fab/bom.csv` row 1 unchanged; `ORDER_README.md` §2; `bom_legibility_check.py` F-MPN reads `if code and ...` |
| R3 | The boss-offset open item is UNDER-STATED as "0.04 mm low" — that is the distance to the PASS-band edge, while the error against the drilled nominal is 2.54 − 2.35 = **0.19 mm** against ~0.20 mm of combined clearance (P2, a re-rating of a known open item) | **ACCEPTED AND WRITTEN INTO THE ORDER PAPERWORK.** `ORDER_README.md` §0 open item 1 now leads with 0.190 mm of error against 0.23 mm of slack (83% of the budget consumed) and says in terms that "0.04 mm low" under-states it. NOTE the reviewer's 0.20 mm used the boss's ø1.70 NOMINAL; the connector in hand MEASURES ø1.60, which is what buys the 0.23 mm. **The reviewer's number is the more dangerous one and is now also in the README**: at nominal ø1.70 the total is 0.18 mm and the boss INTERFERES by ~0.01 mm, so a different lot could bind. Bring-up step 3 now says dry-fit EVERY connector, not just the first | `ORDER_README.md` §0 open item 1; `fab/interposer-{PTH,NPTH}.drl` |
| R4 | Absolute confirmation of CPL rotation 270 is not obtainable from the curated inputs — it rests on the measured per-LCSC row plus cross-board consistency (P2, informational) | **RECORDED, and the ritual already exists.** Correct: no artifact in this repo can prove JLC's library zero in absolute terms. The evidence chain is stated in full in `ORDER_README.md` §3b (measured pad-fit rms 0.0049 mm vs 5.0792 mm next-best = 1037× separation; `jlc_twin` re-fit against JLC's own cached model at 0.01 mm, `jlc_offset=0`; the sealed main board shipping the same code at the same board orientation at 270.0), and §3b closes with the five-second JLC placement-preview look. A-POL raises no single-channel human gate for C2683602 because its row records a NUMBERING-FREE second channel | `jlc_lcsc_rotations.csv:17`; `verification/twin_report.csv`; `ORDER_README.md` §3b |
| R5 | Pin review: 10FDZ-BT **polarity (which housing end carries circuit 1) is UNMEASURED** | **DECLARED AS A NAMED OPEN ITEM, not silently carried.** `ORDER_README.md` §0 open item 2, with the 5.30 / 8.10 mm housing-overhang discriminator, the statement that the board still WORKS if it is reversed (only the `TP_M_*`/`KP_*` naming is wrong), and the instruction to record the answer before bring-up | `ORDER_README.md` §0; `01_docs/10fdz-bt-land-pattern-confirm.md` §4/§6 |

## Part B — v1.0's I1..I9, restated

| # | v1.0 finding | v1.0 disposition | v1.1 state |
|---|---|---|---|
| I1 | No seated-visible pin-1 marker on the hand-solder ZIFs | FIXED pre-v1.0-seal ("1"/"10" silk numerals outside the housing outline) | UNCHANGED and re-confirmed in `render_review.md`. The silk delta v1.0→v1.1 is 50 atoms in ONE character cell (the version digit) — the numerals did not move |
| I2 | GH ribbon harness under-specified — the silent pin1↔pin10 reversal trap | FIXED-IN-DOCS (ORDER_README harness spec) | CARRIED FORWARD verbatim as `ORDER_README.md` §3. **Sharper now**: v1.0's §3 claimed "both boards carry the SAME part at the SAME rotation", which was true of the two BOARDS and FALSE of the two CPLs — the interposer's shipped 90.0 against the main board's 270.0. v1.1 makes the sentence true of the CPLs too |
| I3 | 10FDZ-BT land pattern datasheet-derived, physical fit + circuit-1 end unconfirmed | DEFERRED (USER-HELD ORDER GATE) | **PARTIALLY CLOSED.** The user has the part and has measured it: 10 pins, span 23.50 outside-to-outside, boss ø1.60, pin ~0.6, pitch ~2.54 — all PASS. Two items remain open and are now NAMED in `ORDER_README.md` §0 (R3, R5). The user has explicitly decided to build with the current footprint |
| I4 | `SM10B-GHS-TB` `layout.notes` contradicted the corrected `pins.MP` float rule | FIXED pre-v1.0-seal | UNCHANGED; re-checked — `pins.MP` says FLOAT and the board floats both tabs (`parity.md`) |
| I5 | Uncoded 10FDZ rows ride the BOM **and the CPL**; the GH row's Comment carried the LCSC code while MPN was blank | **RECORDED + ORDER_README prose** telling a human to delete two rows before uploading | **THIS IS THE DEFECT v1.1 FIXES MECHANICALLY.** Both ZIFs now carry `exclude_from_pos_files` on the board and a `not_assembled:` entry with a DATED catalog query in `source/assembly.yaml`; the CPL has 1 row; the MANIFEST's `not_assembled:` line is GENERATED from that file; `assembly_coverage.py` (A-POP) checks all three agree. The GH row's Comment is now `SM10B-GHS-TB` with MPN `SM10B-GHS-TB` and the file carries a UTF-8 BOM (F-LEGIBLE OK, was FAIL). A prose instruction to a human became three artifacts a machine compares |
| I6 | TP labels staggered between rows, count-across ambiguity | RECORDED — next-rev candidate | STILL RECORDED, unchanged. Silk did not move |
| I7 | No back-side silk board ID | RECORDED — next-rev candidate | STILL RECORDED, unchanged. The generic backend's floorplan captions are F.SilkS-only |
| I8 | `J_KEY_MATRIX` refdes near the edge clips at oblique angles | RECORDED — cosmetic | STILL RECORDED, unchanged |
| I9 | 3 near-zero-angle same-net junctions; via annular 0.15 vs 0.13 floor; GH fanout wedges | RECORDED — all DRC-silent, measured cosmetic | STILL RECORDED. The copper is geometrically identical, so all three are bit-for-bit the same features, and DRC is still 0/0/0 at `--severity-all` |

---

**No open P0. Both red-team lens verdicts are ORDER. The two USER-HELD ORDER
gates that remain are stated in `ORDER_README.md` §0 and are not mine to
waive:** the 10FDZ-BT polarity read against the OEM's CN1, and the flex
jumper's G1/G2 coupon discipline.
