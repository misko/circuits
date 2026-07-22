# Fresh render review — crow-array-central v1.0 (2026-07-18)

Reviewer: fresh-context agent (no design context), inputs = release PDF
renders (schematic A0, assembly top, 10 layer pages) re-rendered at
150-400dpi. Verdict: **PASS-WITH-NOTES**. Dispositions by the release
engineer below; canon S5/S6/S7 human-graded items are covered here.

## Graded items

- S6 schematic readability: **B+** — 23 titled/boxed sections with design
  math in titles, story wired left-to-right (entry -> protection -> bucks
  -> LDOs -> XU316; clock/ADC/port chains coherent); not a label-blob.
- S5 design-math spot check: buck FB math printed and correct in section
  titles ("VO=0.6(1+68/15)=3.32V").
- S7 decoupling adjacency: XU316 decoupling field directly beside U1;
  per-ADC VREF/LDO decouple clusters at U2/U3 (also gated by audit I-prox).

## Findings and dispositions

| Finding (reviewer) | Sev | Disposition |
|---|---|---|
| Assembly drawing F.Fab value-text pile-ups in dense clusters (U2/U3, XU316 decoupling field, USB, power entry) | BLOCKER-for-hand-assembly | KNOWN COSMETIC, pod-v1.0 precedent: SMT placement is driven by cpl.csv, not the drawing; every HAND-SOLDER part (RJ45 row, barrel, USB-C, headers) sits in the readable zones. ORDER_README points hand assembly at pdf/pcb_layers silk pages for truth. F.Fab auto-position de-collision remains a generator TODO (does not gate: fab layers are not printed). |
| Functional words existed ONLY on F.Fab (unprinted): barrel jack unmarked, debug/injection headers anonymous, PTCs/TPs unlabeled | DEFECT | **FIXED (D29)**: add_silk_fn.py stamps each J/F/TP ref's functional value on F.Silk (32 labels: "DC-005 5V IN", "2A PTC", "TP 5V", "xSYS DBG TDI/TDO", per-port PTC/TP words). policy_audit P-SILK-FN now PASS; DRC still 0. |
| "PORT n" silk sits in the strip under the RJ45 snouts — may be hidden with jacks fitted | DEFECT | Accepted: the top-edge banner "NOT ETHERNET - CUSTOM 5V/AUDIO PINOUT" stays visible, port TP/PTC labels (D29) identify channels mid-board; noted in ORDER_README. |
| Release PDFs: schematic Rev "dev", empty title blocks on pcb/assembly pages, A0-vs-A4 size fields | DEFECT | Accepted for v1.0 as cosmetic (same tooling as pod v1.0); MANIFEST git_sha is the authoritative provenance. Generator TODO. |
| Title-block Comment overruns the border (schematic bottom-right) | DEFECT | Accepted, cosmetic (same class as above). |
| F.Cu pour appears flush to outline at render resolution | COSMETIC/CHECK | CONFIRMED SAFE: board+pro carry min_copper_edge_clearance 0.2mm (D20) and DRC (copper_edge_clearance armed, severity-all) reports 0. |
| B.Silkscreen empty (no back-side board ID) | COSMETIC | Accepted: single-sided assembly. |
| Oval slots + "0" glyphs bottom-center on all layer pages | COSMETIC | USB-C (J12) through-hole shield slots + the layer-page plot artifacts of their pad numbers; present in gerbers by design. |

## Twin renders

MODEL-REG: zero non-OK across 208 modeled parts (all 0.00mm
body-on-courtyard); no mirrored best-fit anywhere; the two PAD-MISMATCH
and 23 PAD-GEOM findings are adjudicated with evidence in
03_src/rules/twin_adjudications.yaml (twin exit 0).
