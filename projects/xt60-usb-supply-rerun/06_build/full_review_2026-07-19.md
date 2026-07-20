# xt60-usb-supply — full independent review + audit (2026-07-19)

Fresh-eyes audit of the released project against the CURRENT canon
(`design-policies.md` incl. S-DSL, S6/S7, P-SILK-FN, R-THERM, M-REL exact-sha
rule). Live release under audit: **07_releases/v1.0.2-2026-07-16**
(SUPERSEDED chain verified closed: v1.0 → "verification only" pointer →
v1.0.2; v1.0.1 → v1.0.2; v1.0.2 has no SUPERSEDED.md; all three fab
packages byte-identical — sha 78e2669c…). Order status per MANIFEST/README:
package cut, **order not yet placed**. Policy: adopted-forward — the
release (2026-07-16) predates several canon items (adopted 2026-07-17);
graded honestly, sealed artifacts untouched.

Everything below was **independently re-measured on 2026-07-19 by this audit**
(fresh ERC + DRC + policy_audit + project audit, fresh gerber regeneration
from the claimed source sha, fresh live stock check, fresh-context pin
reviews, fresh renders). Nothing is carried forward from the release's own
verification bundle — nor from the prior (Fable) draft of this report —
without re-verification. **One prior-draft finding was overturned on
re-measurement**: the earlier F1 "C25804 stock 0" is NOT reproducible — the
part is fully in stock today (see §2 and finding F1). Peer connector pin
reviews (J2/J3/J4, J5) were provided by a fresh-context reviewer
(2026-07-19); each was VERIFIED against this audit's own board artifacts
before adoption (§3a).

## 1. Graded scoreboard (every canon ID)

| ID | Grade | Evidence (re-measured 2026-07-19) |
|---|---|---|
| S1 / S-ERC | PASS | fresh `kicad-cli sch erc --severity-all`: 0 errors, 4 warnings = exactly the documented baseline (isolated_pin_label on the four deliberate NC_* one-pin nets, confirmed by coordinate: NC_U1_PG @62.23,101.6; NC_U2_PG @412.75,101.6; NC_J5_SBU1 @381,166.37; NC_J5_SBU2 @381,168.91) |
| S2 / S-NET | PASS | 22 routed nets, all deliberately named; zero auto-names on copper (policy_audit S-NET) |
| S3 / S-VER + pin review | PASS | 6/6 part.yaml `verified:` cite figure+page; THREE fresh-context re-derivations run today (§3): SY8368 U1/U2, AOD4185+XT60 J1, USB-A+USB-C — no mirror, no swapped pin, all verdicts PASS |
| S4 / S-NC | PASS | all floats carry generator-emitted no_connect flags (SBU pads, PG pins); ERC pin_not_connected = 0 |
| S5 | PASS | derivations re-computed by a fresh render-review agent from the drawing alone: Vout = 0.6·(1+22k/3k) = 5.000 V both rails (RFA1/RFA2, RFC1/RFC2 read off the sheet); Rp 10k → 3 A advertisement (legal max); LED currents 10.6/2.9 mA; F1 15 A vs 8.2 A worst input; Vgs −12.6 V < ±20 V — all match DETAIL_DESIGN.md and BOM. One marginal catch → finding F4 (R2 dissipation corner) |
| S6 | **FAIL (adopted-forward gap → F2)** | fresh render review: **~0 drawn story wires** — pure label-blob; every part an island with net-label stubs (power entry J1→F1→Q1→D1→bucks must be mentally re-netted; DCP shorts only inferable from repeated labels). 10 titled section boxes exist and no text occlusions, but this is the exact fleet-audit failure S6 was written against. Policy adopted 2026-07-17, release cut 2026-07-16; generator is schwriter v1 (grep add_wire = 0); the schwriter2 wire retrofit that landed on usb-power-3s never reached this project |
| S7 | **FAIL (adopted-forward gap → F2)** | same review: all buck passives (CIN_*, CVCC*, CBS*, COUT_*) live in remote "Buck A/C passives" grid boxes on the opposite side of the sheet from their converters; association is by refdes string only. Values themselves correct |
| S-DSL | PASS | schematic compiled by the generator to native .kicad_sch; all gates (ERC/parity/S-OCCL) run on artifacts |
| S-OCCL | PASS | fresh policy_audit: 0 text occlusions; render review confirms no collisions (the one virtue of the grid layout) |
| P1 / P-CRT | PASS | fresh full-severity DRC: 0 courtyard findings |
| P2 / P-POL | PASS | machine check present (project audit) AND independently re-derived this audit (§4): D1 pad1(cathode)=VBAT_P, LED1-3 pad1(cathode)=GND, CB1/CB2 pad1(+)=VBAT_P, J1 pad1('−' blade)=GND — footprint '+/−' silk paired to the correct pads (KiCad AMASS footprint: silk '−' at (-2.8,2.5) hugs pad1, '+' at (9.5,2.5) hugs pad2; corroborated by an independent EasyEDA C98732 footprint) |
| P3 / P-KEEP | PASS | fresh audit_board.py: PASS 0 fails (I1–I7, proximity 21 pairs, In1 clean) |
| P4 / P-SILK-REF | PASS | ~45 real parts' refdes on visible F.Silk (H1–H4 mounting holes deliberately hidden); fresh render review: legible, de-collided, no pad collisions (§5) |
| P5 / P-SILK-FN | WAIVED-valid | re-measured: zero free functional silk text; only functional glyphs are the XT60 footprint's own '+'/'−' (correctly placed) and CB1/CB2 '+'. Matches the waiver (P5 adopted 2026-07-17 post-release); functions live in ORDER_README + assembly PDF + first-power beep ritual; next-spin labels tracked |
| P6 / P-PLANE | PASS | In1 carries only the GND plane (0 tracks), fresh check |
| R1 / R-RULES | N-A (gap noted → F6) | live .kicad_pro HAS the 5 current-tiered netclasses (FEEDBACK/PWR_5V 0.3/PWR_INPUT 0.5/SWITCH_NODE 0.5/USB_SIGNAL) + matching .kicad_dru floors (re-inspected today); policy_audit reports N-A because no route-input r0.kicad_pro is preserved to inspect. Rules generator runs LAST in rebuild_all.sh (verified) |
| R2 / R-POUR | PASS | re-measured on the board: every power net rides a priority-1 F.Cu pour + In2.Cu reinforcement — VBAT_RAW/F (F.Cu), VBAT_P/5V_A/5V_C (F.Cu+In2.Cu), SW_A/SW_C (F.Cu, 0.5 mm floor). Remaining power-net tracks are floor-compliant (5V_A/5V_C min 0.3; SW min 0.5); the two 0.25 mm VBAT_P runs live inside the named EN_TAP_A/C rule areas that scope a 0.2 floor. **The sister board's VBUS-as-0.8mm-track defect class is ABSENT: 5V_C (USB-C 6 A VBUS) is poured on F.Cu+In2.Cu, not a thin track** |
| R3 / R-PLANE | N-A | no plane_regions configured; no sensitive analog — acceptable |
| R4 | PASS | 0.45 mm-pitch QFN escaped with designed copper corridors at standard-tier vias — 183× 0.6/0.3 + 4× 0.55/0.3, **NO small-via option needed** (min via 0.55/0.3, verified from the board); buck footprint fit vs JLC CAD = 0.00 mm (§4) |
| R5 / R-LEN | N-A | no timing-critical nets on a power-only board |
| R6 / R-THERM | WAIVED-valid (= tracked defect) | re-measured: Q1 DPAK tab (VBAT_F) has 0 in-pad vias; VBAT_F has zero vias net-wide (F.Cu pour only). DETAIL_DESIGN math re-checked: 8.2²·15 mΩ ≈ 1.0 W, ~70 °C/W single-sided → ~70 °C rise only at the pack-empty (9.0 V, 8.2 A) corner. Honest next-spin defect (tab via stitch to In2), not evidence-of-adequacy |
| R7 / R-DRC | PASS | FRESH `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity` today on the HEAD board: **0 / 0 / 0** — matches the release's verification/drc.rpt |
| M1 | PASS | independent-reference battery demonstrably ran (twin v3 PAD-GEOM gate, fresh-agent pin review, fresh render review) — and THIS audit re-ran all of it from outside, incl. 3 fresh pin agents + 1 fresh render agent on newly generated artifacts |
| M2 | PASS | canon IDs machine-enforced via policy_audit.py (regenerated identically this audit); project audit_board.py present and passing fresh |
| M3 / M-REPRO | PASS (two gaps → F3, F5) | promoted chain 03_src/route/routed_final.kicad_pcb is git-tracked and consumed by rebuild_all.sh; **release gerbers regenerate DRC-clean and content-consistent from the claimed source sha 2316609** (§2). GAPS: chain-file sha in no MANIFEST (F5); HEAD board is a post-release rebuild differing from the fab source by 2 via positions (F3) |
| M4 / M-WAIV | PASS | 3 waivers + 4 twin adjudications all carry measurements; every waiver's evidence RE-VERIFIED true on current artifacts today (M-REL commit chronology; P-SILK-FN silk state; R-THERM 0-via count on VBAT_F) |
| M5 / M-REL | WAIVED-valid | v1.0.2 sha256 table: 6/6 files re-hashed today, all match (gerbers 78e2669c, bom 8f41f00c, cpl bcad17d7, +3 PDFs). git_sha "HEAD@release" is the waived defect — evidence verified: content commit 41ae1a6 exists (20:14); exact-sha rule commit 036ae11 (20:24) postdates it as the waiver claims; fab byte-identity v1.0=v1.0.1=v1.0.2 confirmed by hash; CHANGELOG names all release dirs; SUPERSEDED chain closed; source commit 2316609 exists and reproduces the board DRC-clean |
| M6 | PASS | twin ROT-DB disagreements on polarized parts (CB1/CB2, LED1-3, Q1, J5, U3-U6, J1) are ALL dispositioned into the ORDER_README JLC-preview checklist + MANIFEST preview_check line. Residual: the preview eyeball has not happened yet (order not placed) — remains MANDATORY at order time |

Fresh policy_audit.py (FULL mode, 2026-07-19) reproduced **byte-identical to
the committed report**: **zero FAIL** — 14 PASS, 3 WAIVED (all
evidence-verified), 6 HUMAN (graded above: S5 PASS, S6 FAIL, S7 FAIL, R4
PASS, M1 PASS, M6 PASS), 3 N-A.

## 2. Release integrity (M-REL detail)

- v1.0.2 MANIFEST sha256: all 6 files re-hashed today, all match.
- Fab byte-identity: gerbers.zip/bom.csv/cpl.csv sha-identical across
  v1.0, v1.0.1, v1.0.2 (verified by hash — all three 78e2669c/8f41f00c/bcad17d7).
- **Reproducibility proven, not assumed**: the board file at the claimed
  fab source commit (2316609, pre-rename path `projects/xt60-usb-supply/`)
  was extracted WITH its full project context (.kicad_pro netclasses,
  .kicad_dru floors, .kicad_sch, fp-lib-table, vendored lib) and DRC
  re-run: **0 violations / 0 unconnected / 0 parity**. (Caveat for future
  auditors: extracting the board file ALONE — without its .kicad_pro/.dru —
  yields 116 phantom violations because DRC falls back to Default 0.2 mm
  clearance and loses the vendored footprint libs. The clean result
  requires the full project tree, which this audit reconstructed from git.)
- Fresh DRC on the HEAD board is also **0/0/0** (with --schematic-parity).
- Discrepancy found (F3): the HEAD `04_kicad/` board is NOT the fab source —
  it is the c23ccd2 "final green rebuild" made AFTER the release was cut.
  HEAD and source-2316609 have identical via/track COUNTS (187 vias, 170
  tracks) but 2 PTH via positions differ (HEAD: 172.183,127.51 & 172.975,126.0
  ; source: 172.358,126.924 & 173.863,126.4). Provenance is intact (MANIFEST
  names 2316609), but the repo tip no longer regenerates the shipped bytes.
- **Stock re-verified TODAY (live JLC query): 20/20 coded lines IN STOCK,
  0 problems.** 2 lines intentionally uncoded (J1 XT60, J2–J4 USB-A:
  hand-solder per MANIFEST). This **overturns the prior draft's F1**
  ("C25804 stock 0"): C25804 (10k 1%, R3/R4 the USB-C Rp pull-ups) reads
  **stock 48160, basic part, OK** on 2026-07-19 — the BOM is assemblable
  as-is. The SY8368 (C125897, stock 2429) and USB-C (C5337088, stock 1405)
  are the lowest-stock lines and both comfortably cover qty 5.

## 3. Fresh-context pin reviews (S3 bar: derived from datasheet FIGURES first)

Three independent fresh agents this audit, conclusion-free pin_audit.py
dossiers (pad geometry + nets only), datasheet figures rendered first:

| Part group | Verdict | Key derivation |
|---|---|---|
| U1/U2 SY8368QNC (QFN3x3-10, vendored footprint) | **PASS** | AN_SY8368 p.2 figure: pin 1 top-left, winds CW (top view, custom flip-chip numbering — datasheet is authoritative), 1–6 across N edge (EN,PG,ILMT,FB,VC,BS), 7/8 IN on E, 9 = center GND, 10 = LX on W. Vendored .kicad_mod pad geometry matches EXACTLY, NOT mirrored (LX-left/GND-center/IN-right signature intact; a mirror would swap LX↔IN). All pins electrically sane incl. **ILMT→GND = datasheet-sanctioned 8 A valley limit (ILMT abs-max 4 V — a 12 V strap would destroy it; GND is the only correct strap)**, and **EN→VBAT_P safe only because EN sits in the 30 V abs-max group** with IN. U1/U2 pin-for-pin symmetric |
| Q1 AOD4185 + J1 XT60PW-M | **PASS** | AOD4185 Rev4.2 TO-252 figure: G=left lead, D=tab, S=right; board pad1=G, pad2(tab)=D=VBAT_F, pad3=S=VBAT_P — battery faces the DRAIN, body diode conducts at first plug-in, channel enhances at Vgs=−Vbat (−12.6 V < ±20 V). **J1 polarity derived THREE ways and all agree pad1(GND)=physical '−' blade**: (a) datasheet p.2 outline shows a molded '+' housing mark; (b) the KiCad AMASS footprint silk '−' hugs pad1 / '+' hugs pad2; (c) an independent EasyEDA C98732 footprint likewise puts '−' at pad1. Explicitly NOT the sister-board XT60 reversal. Caveat: only the molded '+' was directly legible in the datasheet view; the '−' rests on the two independent footprints + XT60 convention + the visible '+' |
| J2–J4 USB-A + J5 USB-C | **PASS** (peer review, verified §3a) | see §3a |

### 3a. USB connector review detail (peer fresh-context review 2026-07-19, verified against this audit's artifacts)

- **J2 (XY-AF90-WJDG on USB_A_Stewart_SS-52100-001_Horizontal): PASS** —
  geometry exact cross-manufacturer; pin1=5V_A / pad4=GND, no mirror;
  D-/D+ (pads 2/3) shorted on DCP1 = valid BC1.2 DCP. **CAVEAT CLOSED by
  this audit**: J3 and J4 are footprint-identical and net-topology-identical
  to J2 — same footprint `USB_A_Stewart_SS-52100-001_Horizontal`, same pin
  map (pad1=5V_A, pad2/3=shorted DCP, pad4=GND, SH=GND), each with its OWN
  per-port DCP net (J2=DCP1, J3=DCP2, J4=DCP3 — correct: the three ports
  must not share a DCP node). Peer J2 PASS extends cleanly to J3/J4.
- **J5 (TYPE-C-31-M-12A): PASS** — pin table matches Type-C spec pad-for-pad,
  VBUS→5V_C, A5→CC1/B5→CC2, SBU NC'd; Rp=10k/CC = 3 A@5 V source-only
  advertisement (correct); 4 D pins shorted (DCPC) standard. Verified
  against the board: R3/R4 (C25804) confirmed as the 10k CC pull-ups
  (5V_C→CC1/CC2), SBU pads carry NC flags (ERC isolated_pin_label baseline).

## 4. Independent polarized-part re-derivation (Q9-class doc-error hunt)

Board pad-1 nets vs the FOOTPRINT's own convention (not part.yaml — the
class of doc errors that cancel):

| Ref | Footprint (pad1 meaning) | pad1 net | Verdict |
|---|---|---|---|
| D1 SMBJ15A | D_SMB (pad1=cathode) | VBAT_P | ✓ cathode to rail, anode GND (unidirectional TVS right way) |
| LED1 red / LED2,LED3 green | LED_0805 (pad1=cathode) | GND | ✓ (anodes fed via 1k: R2 from VBAT_P, R5 from 5V_A, R6 from 5V_C) |
| CB1/CB2 100u polymer | CP_Elec (pad1=+) | VBAT_P | ✓ |
| J1 XT60PW-M | pad1='−' blade | GND | ✓ (three-source verified, §3) |
| Q1 AOD4185 | TO-252 (1=G, 2=tab=D, 3=S) | PFET_G/VBAT_F/VBAT_P | ✓ battery faces drain (correct reverse-protection orientation) |

No self-consistent-wrong-together pair found. Wide-vs-narrow SOIC trap: N-A
(no SOIC on this board). Vendored-footprint pitch/width trap (cook-hub U7
class): twin pad-correspondence fit = **0.00 mm** for U1/U2 (C125897) and
L1/L2 (C167217/C167218) against JLC's own CAD; all 20 twin rows fit ≤0.13 mm,
jlc_offset=0 — no pitch/width mismatch anywhere.

## 5. Fresh render review (P4/P5/P2 + S5/S6/S7)

Fresh agent, newly generated renders (schematic PDF→PNG; F.Silk+Cu+Edge
plot; assembly PDF; 3D top/bottom):

- **Board**: P4 PASS — ~45 refdes legible on silk, no pad collisions; P5 —
  no plain-word functional text (matches waiver), XT60 '+/−' present and
  correct, CB1/CB2 '+' present; P2 — XT60 '+/−' and CB '+' marks clearly
  identifiable in-render. D1 cathode band and LED cathode marks are below
  3D-render resolution but were confirmed ELECTRICALLY on the board (§4).
- **Schematic**: S5 PASS (values re-derived from the drawing: 5.000 V
  dividers, 3 A Rp, LED currents, fuse margin, Vgs rating). S6 FAIL / S7
  FAIL — ~0 drawn wires, remote passive-farm boxes (§1). Title block has
  title but empty Date/Rev (cosmetic → N1).

## 6. History coherence

- ARCHITECTURE.md power tree == shipped board (walked: J1→F1→Q1(D→S)→
  VBAT_P→U1/U2→L1/L2→5V_A/5V_C→ports; In1 solid GND; In2 patches). Minor
  drift: ARCHITECTURE groups a "PWR_RAIL" domain (line 25) that nets.yaml
  actually splits into PWR_INPUT + PWR_5V netclasses (note N1 — doc naming
  only, the netclasses themselves are correct).
- DETAIL_DESIGN math re-derives (§S5): Iin 8.2 A worst / 5.8 A@12.6 V; F1
  1.8× margin (1.4× derated); Q1 1.0 W/~70 °C; TVS Vc 24.4 V < 30 V;
  inductor ripple + ILMT 8 A valley all self-consistent and consistent
  with the BOM.
- ADR 0001–0009 all still describe the board (0007 ILMT-low and 0008
  DCP-short verified on copper; 0009 documents the accepted no-UVLO
  limitation).
- BRIEF criteria G1–G6 met; assumption log A1–A4 accurate; decision
  register R1–R11 consistent with the board.
- Drift found & FIXED in the checkpoint commit (verified in place this
  audit): BRIEF `current_release` and README "Current release" both now
  point at v1.0.2-2026-07-16 (were v1.0, two verification releases stale).

## 7. Findings table

| # | Sev | Finding | Falsifiable evidence | Remediation | New release? |
|---|---|---|---|---|---|
| F1 | **NOTE (prior-draft finding OVERTURNED)** | The prior draft flagged Rp pull-ups R3/R4 (10k 1%, C25804) as STOCK 0 (MAJOR order-time). On independent re-measurement TODAY this is **NOT reproducible**: C25804 is a basic part in stock, and ALL 20 coded BOM lines are in stock (0 problems). The BOM is assemblable as-is | fresh `jlc_stock_check.py` 2026-07-19: `OK C25804 base stock=48160`; 20/20 coded lines OK | none needed for stock; standard practice: re-run the stock check on order day (ORDER_README step 4) as stock moves | No |
| F2 | **MAJOR (canon gap, not orderability)** | S6 + S7 FAIL: schematic is a pure label-blob (~0 drawn story wires; all passives in remote grid boxes) — the exact fleet-audit defect the 2026-07-17 canon adopted against, graded adopted-forward | fresh render review §5; `grep add_wire 03_src/generate_schematic.py` = 0 (schwriter v1) | port the schwriter2 wire retrofit (story wires J1→F1→Q1→D1→bucks; LX→L→COUT→FB loops; decouplers into their IC sections) at the next verification refresh; netlist parity 0 is the proof | verification-only release when done |
| F3 | MINOR | Repo-tip board ≠ released board: c23ccd2 "final green rebuild" (post-release) moved 2 vias, so `04_kicad/` at HEAD no longer regenerates the shipped gerbers byte-for-byte (release still reproducible DRC-clean from source sha 2316609) | §2 via diff: 2 PTH coords differ HEAD vs source; HEAD board DRC 0/0/0 | next release re-exports from the then-current source and records that exact sha; no action on sealed dirs | No (HEAD board is DRC 0/0/0 and is the natural v1.1 source) |
| F4 | MINOR | R2 (LED1 series 1k 0603) dissipates ~114 mW at 12.6 V full-charge — above the 0603 100 mW rating (in-spec ≤~11.6 V; DETAIL_DESIGN computed the LED current 10.6 mA but never the resistor power) | R2 pad1=VBAT_P confirmed on board; (12.6−1.9)²/1k = 114 mW vs UNIROYAL 0603 rating 100 mW (02_parts/0603WAF1001T5E). R5/R6 on 5 V rails dissipate ~9 mW, fine | next spin: 2k (halves brightness, 57 mW) or 0805; harmless to order — corner exists only near full charge | No |
| F5 | MINOR | Canon M3 letter unmet: promoted route chain 03_src/route/routed_final.kicad_pcb is git-tracked but its sha is recorded in NO MANIFEST | `grep routed_final 07_releases/*/MANIFEST.txt` → empty; `git ls-files` confirms it IS tracked | record the chain-file sha in the next release's MANIFEST | No |
| F6 | MINOR | R-RULES grades N-A because the historical route-input .kicad_pro was never preserved — the "rules rode into the router" claim for the original campaign is now unverifiable (the LIVE .kicad_pro DOES carry all 5 netclasses + dru floors, and rules-gen runs last, both re-inspected today) | policy_audit R-RULES: "no route-input .kicad_pro found"; live .kicad_pro classes verified present | route_prep-style preservation at the next routing campaign (as usb-power-3s remediated) | No |
| F7 | NOTE | policy_audit P-SILK-FN counts only free board text, so it misses J1's footprint-level '+'/'−' glyphs (reports "no functional silk near J1" while correct fp_text marks exist) — grading unaffected (waiver stands regardless) | §4 J1 footprint silk coords vs policy_audit.md P-SILK-FN row | teach the checker to include fp_text items; keep the waiver until word-labels land | No |
| N1 | NOTE | ARCHITECTURE.md "PWR_RAIL" domain name vs nets.yaml classes PWR_INPUT/PWR_5V; schematic title block Date/Rev empty; MANIFEST "ordered:" line says package cut, order not placed | ARCHITECTURE.md §Net domains; pdf/schematic.pdf title block | fold into next doc pass; update "ordered:" when the order goes out | No |

No CRITICAL findings. No finding blocks the order.

## 8. Bottom line — orderability

**The live release v1.0.2-2026-07-16 is ORDERABLE AS-IS**, with the
standard order-time/arrival ritual (no stock blocker):

- Fab package: DRC re-verified 0/0/0 TODAY from the exact release source
  (full project context) and on the HEAD board; sha256 table verifies
  6/6; fab byte-identity across v1.0/v1.0.1/v1.0.2 confirmed; standard
  4-layer tier, **NO small-via option needed** (min via 0.55/0.3).
- BOM/CPL: **all 20 coded lines IN STOCK today** (the prior-draft C25804
  stock-0 blocker did not reproduce — F1); 2 intentional hand-solder lines
  (J1 XT60, J2–J4 USB-A). Standard practice: re-run the stock check on
  order day, as stock moves.
- **Mandatory at order time (M6 / ORDER_README)**: the JLC-preview
  rotation/polarity eyeball of CB1/CB2, Q1, J5, U3–U6, LED1–3 (+ J1/J2–J4
  at hand-solder) has NOT happened yet (order never placed) — it is the
  designed disposition of the twin's ROT-DB/POLARITY findings and must run
  before paying, followed by the first-power beep ritual on arrival
  (XT60 blade polarity vs the board nets).
- Every protection-chain orientation (XT60 polarity three-source verified,
  P-FET drain-to-battery, TVS, LEDs, buck pinout incl. ILMT-low respecting
  the 4 V abs-max) was independently re-derived clean today; all three
  waivers remain evidence-valid; the Q1 thermal shortfall (R6) and the
  S6/S7 schematic-readability gap (F2) are honest tracked next-spin
  defects, not orderability blockers.

Audit fixes committed (docs/audit-config only — no schematic/board/fab/
release/sealed artifacts touched): this report finalized (incl. the F1
correction); the checkpoint's BRIEF `current_release` and README
current-release pointer verified in place.
