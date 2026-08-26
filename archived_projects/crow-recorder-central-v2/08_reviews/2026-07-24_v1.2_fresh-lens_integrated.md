subject: crow-recorder-central-v2 v1.2-staging final bytes (07_releases/crow-recorder-central-v2-v1.2-2026-07-24)
date: 2026-07-24
reviewer: fresh-lens integrated (fable-medium, final-bytes)
context-given: release-archive-only
verdict: ORDER

# Fresh-context integrated review — v1.2 staged archive, final bytes

All numbers below were measured directly on the staged archive's bytes
(/usr/bin/python3 + pcbnew on source/, text parses of fab/ and verification/),
not taken from prior reviewers or the release's own evidence files, except
where marked "cross-check" (evidence file vs my independent measurement).

## 1. Archive completeness + freshness — PASS

Present: fab/ (gerber zip 15 files, PTH+NPTH drills, bom.csv, cpl.csv),
pdf/ x3 (schematic, assembly, pcb_layers), source/ (kicad_pcb, kicad_sch,
tsx, .net, kicad_pro/prl/dru, 2 .pretty libs + fp-lib-table), 3d/step,
verification/ (29 files), ORDER_README.md.

Freshness — every fab artifact is v1.2-current:
- Gerber zip internal dates all 2026-07-24 13:16; F.Cu gtl CreationDate
  2026-07-24T13:16:17; drills 13:16:18 (netlist export 13:11:53, step 13:23).
- cpl.csv contains C_c9..C_c13 and C_b0v9 at (91.85, -116.05) top — pcbnew
  confirms the footprint at (91.85, 116.05) board coords. Required check: MET.
- PTH drill: T1C0.150 is tagged **ViaDrill** (as is T2C0.200); the only
  ComponentDrill tools are T3..T6 (0.600/0.890/1.000/1.570). NO 0.15mm
  ComponentDrill tool — the v1.0 EXT-F1 regression did not recur. MET.
- All three PDFs contain C_c9 and C_c13 (pdftotext hit counts 1/2/1 and
  1/3/1) — regenerated post-fix, not stale v1.1 plots.
- source/ tsx and kicad_sch both contain C_c13 (source-of-truth updated,
  not a board-only hack; canon M3 respected).
- missing_models: CPL rows 172, modeled 172, missing bodies 0.

One structural note, NOT a defect: **MANIFEST.txt is absent from staging**,
while ORDER_README says "hashes in MANIFEST.txt". This is the documented seal
procedure (FL2-P1-1 disposition: manifest is stamped at seal, after this
review lands in verification/). v1.1 has its MANIFEST.txt. Seal conditions:
(a) stamp MANIFEST.txt with this archive's final hashes including this file,
(b) add SUPERSEDED.md to v1.1 in the seal commit. Both are mechanical seal
steps already practiced at v1.1; ORDER is conditional on them happening.

## 2. Gate evidence — PASS (all recomputed or parsed from raw JSON)

- drc.json: **0 violations / 0 unconnected / 0 schematic-parity** (parsed the
  JSON arrays myself, not the summary text).
- erc.json: severity histogram = {warning: 1211}, **0 errors** — matches
  ORDER_README's "0 errors / 1211 baselined warnings" exactly.
- parity.md: converter 116 nets / 598 nodes / 146 no-connects == kicad, REAL
  DISCREPANCIES 0. Cross-check: my .net parse finds 262 named nets = 116 real
  + 146 unconnected-(...) singletons — internally consistent.
- audit.txt: opens with "USB pair: USB_DP=23.62mm USB_DN=23.51mm
  spread=0.110mm (<=1.0mm), width 0.125mm, all F.Cu, 0 vias" + "U1-EP: 16 GND
  0.30/0.15 thermal vias inside the EP" + 21 polarity + 11 mate/keepout
  checks OK. No stderr noise (RT3-P2-1 fix held).
- twin_report: **165 OK / 369 checked**; the only fetch failure is
  C9900035627 (RJ45 consign placeholder), carried as ADJUDICATED-FETCH-FAILED
  with the 8-attempt evidence + pod-v2 precedent; D1 pad-geometry is the
  adjudicated fleet SMA class. Exit condition met.
- bom_source_check: PASS (185 coded refdes, every BOM LCSC == source).
- stock_check: FAIL lines are exactly the two declared consignment codes —
  C6938291 x1 = U1 (XU316) and C9900035627 x8 = J3..J10 RJ45s — plus 2
  uncoded lines (JP_INJ, J_DBG headers, hand-place). As declared.
- policy_audit: 0 FAIL; PASS=27, WAIVED=2 (P-ADJ with per-net measured
  rationale, S-OCCL converter-artifact), HUMAN=6, N-A=3; M-WAIV 17
  adjudications all evidenced.

## 3. The decoupling fix (EXT2-F1) — VERIFIED INDEPENDENTLY

- bom.csv C1525 row: contains C_c1..C_c13 — all 13 present in the one 100nF
  0402 line (44 refs total on the line).
- Net membership (my parse of source/crow_recorder_central_v2.net): net 0V9
  has exactly 13 C_c* caps: C_c1..C_c13. C_b0v9 (10uF bulk) also on 0V9.
- **Netlist diff v1.1 archive vs v1.2 archive, recomputed from both .net
  files by me**: net-name sets identical (262 = 262, symmetric diff empty);
  exactly 2 nets changed; 0V9 ADDED (C_c9..C_c13 pin 1), GND ADDED
  (C_c9..C_c13 pin 2), REMOVED none, nothing else anywhere. This matches
  decoupling_fix.md's claim to the node. A 5-cap-only diff also proves the
  C_b0v9 move was placement-only (no net change) — as it should be.

## 4. Survival of v1.1 closures — ALL INTACT (pcbnew, this archive)

- USB pair: USB_DP 23.621mm / USB_DN 23.511mm, **skew 0.110mm**, both
  entirely F.Cu, 0 vias, all segments 0.125mm. (F2)
- U1 EP: exactly **16 GND vias, 0.30mm dia / 0.15mm drill, inside the EP pad
  bbox** (pad 129). All 644 0.15mm-drill vias on the board are 0.30mm size. (F1)
- LV straps: U1 pads 40/43/52 net = unconnected-(U1-PadNN) — still floated. (PR2-P0-1)
- Filled+capped: board file carries `(filling yes)` + `(capping yes)` (+
  tenting/covering/plugging tokens) in the board setup — board-wide
  via-in-pad process ordered in the file, and §1a orders it at fab. (F1)
- TDI: now F.Cu + In3.Cu, 1 via, 70.32mm total — the reroute that freed the
  C_c11/C_c13 pocket landed as described.

## 5. ORDER_README v1.2 — CONSISTENT

- Header: v1.2, supersede chain v1.2->v1.1->v1.0 with the EXT2-F1 driver
  quoted against the datasheet section (§14 p.29 "at least 12"), not reviewer
  authority. Gates paragraph matches the shipped evidence numerically (DRC
  0/0/0, ERC 0/1211, twin 165/369, USB 0.110mm — all re-measured above).
- §4a rail-sequencing gate (EXT2-F2): all corners enumerated — cold/room/warm
  start, fast disconnect-reconnect, slow ramps, brownouts, repeated cycling,
  light+heavy USB load — with the explicit PASS condition (1V8 VALID before
  0V9 valid threshold at every corner; RST_N held until all I/O rails
  stable) and the "any-corner failure requires a real interlock, not a delay
  tweak" escalation. Present and strengthened as claimed.
- 0V9 ripple/droop first-article measurement present (repeated boot,
  sustained HS traffic, max audio load) as the EXT2-F1 empirical close-out.
- NOT-ETHERNET banner + consignment/preview instructions carried.

## 6. PDN judgement (placement-based) — ADEQUATE

I re-measured 5 of the 13 table rows on the archived board; all match the
given table to 0.01mm:

| cap | 0V9 pad->served pin | GND pad->GND via |
| C_c9 (v1.2) | 1.63mm (pin 14) | 0.00 (in-pad) |
| C_c11 (v1.2) | 2.01mm (pin 50) | 0.50 |
| C_c13 (v1.2) | 2.02mm (pin 54) | 0.40 |
| C_c1 (v1.1) | 2.28mm (pin 45) | 0.00 |
| C_c6 (v1.1) | 3.22mm (pin 5) | 0.00 |

Judgement: this is a genuine placement fix, not count-washing. The five new
caps sit at or tighter than the incumbent population (1.63–3.63mm to served
pin), every core-VDD pin's nearest 100nF is now <=3.22mm (worst = pin 5,
unchanged, with C_c10 added to its feeder 3.63mm out), the previously worst
pins 50/54 improved 3.51/3.90 -> 2.01/2.02mm, and every GND return is
via-in-pad (0.00mm) or <=0.50mm into solid In1/In4 planes with board-wide
filled+capped vias. On a 14x14mm TQFP-128 whose pin rows sit ~7.7mm from
package center, 1.6–3.2mm pad-to-pin with sub-mm plane returns is "close to
the chip" by any reasonable reading of ds §14; 13 >= 12 meets the letter,
and the loop geometry meets the intent. The scoped 0.29–0.34mm track floors
for the four new taps are dispositioned (RT3-P2-2): each tap is a parallel
decoupler drop into a 0.4mm-pitch pad row where 0.4mm copper cannot clear
the neighbor pad; ripple current only, primary feed intact; .kicad_dru
carries the scoped rules (u1_0v9_west/south/east_tap, tap103 at 0.34).

## 7. Other fresh-eyes observations

- P3 (info): parity.md's "116 nets" vs the .net's 262 could confuse a future
  reader; the 146 no-connect singletons account for the difference. No action.
- P3 (info): the 0V9 width histogram is {0.5: 99 segs, 0.4: 6, 0.35: 1,
  0.3: 8} — the 0.35mm segment falls under the tap103 scoped floor (0.34);
  consistent with the dru.
- Carried P2s (buck Cin loop 2.51/2.78mm, D_USB stub ~7mm, beeper aggregate,
  BOM cosmetics, L1 stock) remain accurately recorded in ORDER_README §5 and
  the dispositions ledger; nothing regressed.
- Nothing new found at P0/P1 severity.

## Verdict

**ORDER.** The single v1.2 driver (EXT2-F1) is closed with measured placement
evidence I reproduced independently; the netlist diff is surgically minimal
(exactly 5 caps, 2 nets); all four v1.1 closures survive byte-for-byte checks
on this archive; every gate artifact is fresh and internally consistent; the
first-article gates (§4a) correctly carry the remaining empirical risk
(rail sequencing, USB-HS, EP X-ray, 0V9 ripple). Seal must stamp MANIFEST.txt
(including this file) and add SUPERSEDED.md to v1.1 — both standard seal
steps per the v1.1 precedent.
