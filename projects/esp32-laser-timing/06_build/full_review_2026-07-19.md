# esp32-laser-timing — full independent review + audit (2026-07-19)

Fresh-eyes audit of the released project against the CURRENT canon
(`design-policies.md` incl. S-DSL, R-PLANE/R3, P-SILK-FN, M3 chain-file
letter). Live release under audit: **07_releases/v1.7-2026-07-17**.
SUPERSEDED chain verified CLOSED and COHERENT: v1.0 → v1.1 → v1.2 → v1.3
→ v1.4 → v1.5 → v1.6 → v1.7 (longer than the briefed v1.0..v1.5 — v1.6
= schwriter2 schematic, v1.7 = GND power icons; every superseded dir has
a SUPERSEDED.md naming its successor; v1.7 has none). The USB-C
double-flip saga is honestly recorded: v1.1 correct → v1.2 wrong
model_rot_z:180 override → v1.3 revert, with v1.1/v1.2's SUPERSEDED.md
carrying the correction notes. Policy: adopted-forward — pre-policy
releases graded honestly, sealed artifacts untouched.

Everything below was re-measured on 2026-07-19 (fresh ERC + DRC + parity,
fresh policy_audit FULL, fresh project audit, fresh stock check,
fresh-context pin reviews, fresh renders + fresh-eyes review) — nothing
is copied forward from the release's own verification bundle without
re-verification.

## 1. Graded scoreboard (every canon ID)

| ID | Grade | Evidence (re-measured 2026-07-19) |
|---|---|---|
| S1 / S-ERC | PASS | fresh `kicad-cli sch erc --severity-all`: **0 violations total** (0 errors, 0 warnings — no baseline needed) |
| S2 / S-NET | PASS | 36 routed nets all deliberately named; `unconnected-(…)` autonames only on sanctioned NC pins (J1 SBU1/2, U3 OUT4, unused module IOs) |
| S3 / S-VER + pin review | PASS | 22/22 part.yaml `verified:` cite figure/page or live JLC attribute check; THREE fresh-context re-derivations run today (§3): ESP32-S3-WROOM-1, TYPE-C-31-M-12, LM339DT — no mirror, no swapped pin, all PASS |
| S4 / S-NC | PASS | policy_audit S-NC: all floats no_connect-flagged; ERC 0 confirms |
| S5 | PASS | math re-derived: Vth = 3.3·2.7/12.7 = 0.702 V ✓; hysteresis ≈88 mV from 33k/10k-pullup/1k-source ✓ ≈ "roughly 100 mV"; LM339 CM ceiling 5−1.5 = 3.5 V > 3 V max node ✓; LDO worst 0.61 W peak sane; render agent independently recomputed the divider from the schematic image and matched |
| S6 | PASS-with-debt (marginal) | fresh-eyes grade: "label-blob with excellent labeling discipline" — 16 real wires (gate/drain chains, VTH dividers, EN node, USB D+ entry, LM339 VCC decoupler) + 46 GND power icons + 7 titled blocks with purpose labels, but >90% of connections are still label pairs; no continuously drawn power path or signal chain. Same debt class the fleet carries; tracked (F7), schwriter2 path-syntax is the queued remediation |
| S7 | PASS-with-debt | decouplers drawn inside their IC's block with purpose labels ("100n LM339", "22u MCU 3V3"); only C6 pin-attached; not a cap farm |
| S-DSL | PASS | schematic compiled by schwriter2 to native .kicad_sch (v1.6+); all gates run on the artifact (fresh ERC/parity/S-OCCL on the .kicad_sch itself) |
| S-OCCL | PASS | fresh policy_audit: 0 text occlusions (label-aware checker — the v1.4 label-blind claim is honestly recorded in ERRATA and was resolved in v1.5) |
| P1 / P-CRT | PASS | fresh full-severity DRC: 0 courtyard findings |
| P2 / P-POL | PASS | machine check present (audit I9) AND independently re-derived this audit (§4): C11 pad1(+)=5V, D2 LED pad1(cathode)=GND — correct vs FOOTPRINT conventions, not just part.yaml; C11 '+' silk verified at the pad-1 side in the render |
| P3 / P-KEEP | PASS | I1–I7 present in audit_board.py; fresh audit: PASS 0 fails 0 warns; antenna guard (I3) re-ran clean |
| P4 / P-SILK-REF | PASS | all 72 refdes on F.SilkS, waiver list EMPTY (refdes_waiver.json = []); zoom render: refdes legible even in the dense comparator region |
| P5 / P-SILK-FN | PASS | 50 board silk texts re-dumped: LASER/PHOTODIODE/BUTTON 1-3 + per-pin 5V/SW/PD/IN/GND, "USB-C 5V", OLED "GND VCC SCL SDA" + "CHECK MODULE PINOUT: SOME SWAP GND/VCC!", full PIN MAP block, labeled TPs, BOOT/RESET/PWR — exemplary; legible in fresh renders |
| P6 / P-PLANE | N-A | 2-layer (no dedicated plane layer); ground strategy graded under R3 below |
| R1 / R-RULES | WAIVED-valid | re-verified: 06_build/route/r0.kicad_pro classes=['Default'] exactly as the waiver states (historical route input; canon adopted post-release); CURRENT 04_kicad project file carries PWR 0.5 / COMP 0.25 / LSW 0.3 netclasses + matching .kicad_dru — rules-run-last discipline in rebuild_all |
| R2 / R-POUR | WAIVED-valid | re-measured: 5V = 87 segments ALL 0.6 mm (≥ the 0.5 floor), 3V3 = 95 segments all 0.6 mm; waiver math (IPC-2152 ~1.4-1.5 A capacity vs 0.7 A class budget, worst case ~0.55 A) re-checked sane; documented trunk exception per canon R2 |
| R3 / R-PLANE | **FINDING (F2)** | B.Cu GND pour is connected (DRC 0 unconnected) BUT: 26 B.Cu signal segments measured inside the analog region bbox (VTH1/2/3 ×16, COMP1/2 ×6, 3V3 ×3, 5V ×1) while ARCHITECTURE claims "The LM339 input region … sits over unbroken B.Cu copper — audit checks no B.Cu track crosses under it" — NO such check exists in audit_board.py, and policy_audit R-PLANE = "no plane_regions configured". This board is the canon R3 motivating incident and is still unremediated |
| R4 | PASS | no fine-pitch escape problem: largest packages SOIC-14/SOT-223/WROOM at JLC standard 2-layer rules; 0.6/0.3 vias only, DRC 0/0/0 |
| R5 / R-LEN | PASS | re-measured today: COMP lengths {COMP1 65.9, COMP2 62.9, COMP3 74.9} mm, spread **11.9 mm < 40 mm gate** — identical to the release's audit.txt; I7 separation (analog ≥4 mm from FET drains) also passing |
| R6 / R-THERM | N-A | 2-layer, no internal plane to sink into (policy_audit N-A); LDO SOT-223 tab sits on the enlarged 3V3 F.Cu pour per DETAIL_DESIGN — checked present (3V3 zone, prio 2) |
| R7 / R-DRC | PASS | FRESH `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity`: **0 violations / 0 unconnected / 0 parity** — matches release verification/drc.json |
| M1 | PASS | independent-reference battery demonstrably ran and caught real things: twin adjudications from JLC CAD (5, all evidenced), figure-first pin reviews (the LM339 "right-side minus-first" order caught at figure read), JLC-authoritative USB-C rotation ruling; THIS audit re-ran all of it from outside |
| M2 | PASS | canon IDs machine-enforced (policy_audit FULL: zero FAIL); project audit I1–I10 present |
| M3 / M-REPRO | PASS (one gap → F5) | rebuild inputs git-tracked incl. promoted chain 03_src/route/r3.kicad_pcb; GAP: no MANIFEST records the chain file's sha (M3 letter) — same gap as usb-power-3s |
| M4 / M-WAIV | PASS | 2 policy waivers + 5 twin adjudications all carry measurements; both waivers' evidence RE-VERIFIED true on current artifacts today (R-RULES: r0 classes really Default-only; R-POUR: trunk widths really ≥ floor) |
| M5 / M-REL | PASS (content finding → F1) | v1.7: sha256 table verifies 6/6; git_sha eaf413d exists; board at eaf413d == HEAD == sha 870b65e4 (MANIFEST gates-line claim) byte-for-byte; fresh DRC from that exact board = 0/0/0; fab byte-identity claim verified across v1.1–v1.7 (gerbers/bom/cpl sha-identical; v1.0 differs = the refdes-less silk, correctly quarantined); all 8 release git_shas exist; CHANGELOG names every dir; chain closed. BUT the v1.7 ORDER_README's accreted history sections contradict each other (F1) |
| M6 | PASS | the double-flip incident is the canon M6 case study and its final state is CORRECT: fresh agent read JLC's own .kicad_mod `(rotate (xyz 0 0 180))`, confirmed the adjudication applies NO override, and confirmed mouth-west/leads-on-pads in the shipped twin render |

Fresh policy_audit.py (FULL mode, 2026-07-19): **zero FAIL** — 15 PASS,
2 WAIVED (both evidence-verified), 7 HUMAN (graded above), 2 N-A.

## 2. Release integrity (M-REL detail)

- v1.7 MANIFEST sha256: all 6 files re-hashed, all match.
- `git_sha eaf413d` exists; board file at that commit sha256 =
  870b65e4… == working tree == MANIFEST gates-line claim. Fresh DRC from
  it: 0/0/0 + parity 0.
- Fab byte-identity: gerbers.zip b3a0c897…, bom.csv 015ee5ea…, cpl.csv
  a54ecc66… IDENTICAL across v1.1–v1.7 (verified per-release); v1.0's
  zip differs (superseded refdes-less silk, "do not order" recorded).
- Gerber zip = 11 files (correct 2-layer set incl. PTH+NPTH drills);
  STANDARD JLC options genuinely sufficient (min via 0.6/0.3).
- All 8 release git_shas exist as commits; git log narrative matches the
  CHANGELOG chain (incl. the v1.2 mistake + v1.3 revert commits).
- BRIEF prompt sha present; A4 full-delegation + D1–D15 register coherent.
- Stock re-verified TODAY: all 20 coded lines in stock (PASS, ≥5×), 10
  deliberately uncoded hand-solder THT lines per MANIFEST not_assembled;
  exactly 5 unique Extended parts as ADR-0003 tallies.

## 3. Fresh-context pin reviews (S3 bar: datasheet FIGURES first)

Three independent fresh agents, conclusion-free dossiers (06_build/pin_audit/):

| Part | Verdict | Key derivation |
|---|---|---|
| U1 ESP32-S3-WROOM-1-N8R2 | **PASS** | Fig 3-1 p.10: pin1 top-left, CCW 14/12/14 + EP; board = identical orientation, NOT mirrored (corner pads 1/14/15/26/27/40 all verified by position); USB polarity correct (pad13 IO19=D−→USB_DM, pad14 IO20=D+→USB_DP); strapping IO0 tactile-only, IO3/45/46 unconnected ✓; EN RC verified on-board (R3 10k + C1 1u + SW2); EP=GND; figure/table doc-error hunt clean. Advisory: no UART0 fallback header (native-USB-only download path) |
| J1 TYPE-C-31-M-12 (USB-C) | **PASS / PASS** | full contact table derived from HRO drawing rev A; board pad x-sequence EXACTLY matches the recommended land pattern (not mirrored/rotated); VBUS×4→5V, GND×4, DP{A6,B6}→USB_DP, DN{A7,B7}→USB_DM criss-cross correct; CC1/CC2 each to a DEDICATED 5.1k (net membership re-extracted: CC1={J1.A5,R1.1} only, CC2={J1.B5,R2.1} only); SBU float sanctioned. **Double-flip final state verified correct**: JLC's own kicad_mod says rot_z=180, adjudication applies NO override, shipped render shows mouth WEST off-edge + contacts on pads — v1.2's wrong override remains reverted |
| U3 LM339DT (SOIC-14) | **PASS** | Fig 1 p.3 derived: OUT2/OUT1/VCC on 1/2/3, inputs bottom half with left (−,+) / right (+,−) asymmetry — the classic swap trap, checked pin-by-pin; all 3 channels +IN=PDn, −IN=VTHn, OUT=COMPn, zero cross-channel mixes; VCC=5V (user-pinned CM requirement), GND=12; 4th comparator +IN=GND, −IN=VTH3, OUT4 no_connect (parks low, no oscillation) per D13; footprint = byte-identical to stock KiCad narrow SOIC-14 3.9×8.7 P1.27 (row span 4.95 mm — wide-SOIC trap ABSENT) |

## 4. Independent polarized-part re-derivation (Q9-class hunt)

Board pad-1 nets vs the FOOTPRINT's own convention:

| Ref | Footprint (pad1 meaning) | pad1 net | Verdict |
|---|---|---|---|
| C11 100u elec | CP_Elec_6.3x5.4 (pad1=+) | 5V | ✓, '+' silk at the pad-1 (south) side in render |
| D2 green LED | LED_0805 (pad1=cathode) | GND | ✓ (anode via R4 1k from 3V3) |
| J1 USB-C | keyed, table above | — | ✓ (16/22 nets re-judged by fresh agent) |

No self-consistent-wrong-together pair found. Cross-portfolio traps swept:
wide/narrow SOIC ✓ (U3 narrow, verified), wrong-pitch ✓ (WROOM 1.27 mm
columns match JLC CAD per the twin's translation-only delta; terminal
1.2 vs 1.3 mm hole delta documented in ORDER_README), SOT-223 tab-merge
handled via pad_alias {4:2} (coverage-restoring, not a waiver),
TS-1187A 2-vs-4 pad naming adjudicated from the vendor circuit diagram.

## 5. Fresh render review (S5/S6/S7 + P4/P5 + P2)

- Fresh-eyes agent graded the released v1.7 schematic PDF: S5 PASS (read
  the values off the sheet and re-derived 0.701 V; pullups to 3V3 not 5V
  spotted as correct level handling), S6 marginal (see scoreboard), S7
  PASS-with-debt, no text collisions on the schematic sheet.
- Board re-graded on fresh renders of the actual board (after the agent
  caught stale renders — see F8): P4 PASS, P5 PASS, P2 PASS (C11 '+'
  south side = pad1/5V ✓), antenna overhang plausible with copper-free
  guard (I3 machine check is the authority and passes).
- assembly_top.pdf has severe Fab-text pile-ups in the terminal rows and
  divider cluster ("LASER 1 TEBASER 2 TEBASER 3 TERM") and an empty
  title block → F6, same class as the sister project's finding.
- Board silk carries "esp32-laser-timing v1.1" — CORRECT for the copper
  (fab is byte-identical to v1.1 by design); noted, not a defect.

## 6. History coherence

- ARCHITECTURE power tree, net domains, connector map, pin map == shipped
  board (spot-verified against nets + silk). ONE drift → F2 (the B.Cu
  "audit checks" claim).
- DETAIL_DESIGN math re-derives (§ S5); the −IN4 doc correction (VTH3,
  was 3V3) matches the board.
- ADR-0001…0005 still describe the board; D1–D15 all realized (D13 4th
  comparator verified pin-level; D5 pin map verified by fresh U1 review).
- CHANGELOG entries name every release dir; git commit narrative matches,
  including the honest v1.2-mistake/v1.3-revert pair and the ERRATA
  record of the label-blind S-OCCL claim.
- Drift found & FIXED this audit (commit 272487e): BRIEF
  `current_release` v1.0 → v1.7; README "v1.0 released" → v1.7;
  PROGRESS log ended at v1.0 → chain appended; ERRATA contained a pasted
  git-command line + duplicated entry → cleaned (content preserved);
  CHECKLIST antenna gate mislabeled I8 → I3.

## 7. Findings table

| # | Sev | Finding | Falsifiable evidence | Remediation | New release? |
|---|---|---|---|---|---|
| F1 | **MAJOR** | v1.7 ORDER_README history sections SELF-CONTRADICT on the USB-C saga: "## v1.7 vs v1.1" claims the render was "fixed with a model_rot_z:180 adjudication" (that override is exactly the v1.2 MISTAKE that v1.3 reverted), while the next section "## v1.7 vs v1.2/v1.1" correctly calls it wrong; "## What changed from v1.0" describes v1.1's silkscreen change as "v1.7 is a silkscreen fix". Sections were accreted per release with the version string bumped, not regenerated; v1.4–v1.6 deltas are missing entirely. The operative content (options, checklist, first-power) is correct, and SUPERSEDED.md + CHANGELOG tell the true story — but the LIVE order document misstates the project's flagship M6 lesson | 07_releases/v1.7-2026-07-17/ORDER_README.md sections "What changed from v1.0", "v1.7 vs v1.1" vs "v1.7 vs v1.2/v1.1"; CHANGELOG v1.2/v1.3 entries | Next release: generate ORDER_README's history from the CHANGELOG chain (one "vs previous live fab" section + a pointer), don't accrete; sealed v1.7 stays untouched — this report is the correction of record | Not by itself (fab + operative instructions unaffected) |
| F2 | **MAJOR** | R3/R-PLANE unenforced on the board that MOTIVATED canon R3: ARCHITECTURE states "audit checks no B.Cu track crosses under it [LM339 input region]" — no such check exists (audit_board.py has no plane-region item; policy_audit R-PLANE: "no plane_regions configured"); measured today: 26 B.Cu signal segments inside the analog-region bbox (VTH×16, COMP×6, 3V3×3, 5V×1). Electrical risk LOW (crossers are mostly the region's own quasi-DC nets, pour fully connected, comparator response 1.3 µs dominates) but the doc claims a check that never ran — the exact "unenforced intent drifts" failure canon R3 names | ARCHITECTURE.md "Ground strategy"; 06_build/policy_audit.md R-PLANE row; measurement script output in this audit (bbox x94.3–121.7 y79.5–112) | Configure plane_regions for the LM339 input region (bbox above) in 03_src/rules/policy_audit config + add the audit item; then either re-route the VTH/COMP B.Cu crossings out of the region on the next spin or waive with the low-risk math recorded. Reword ARCHITECTURE if the gate stays region-limited | No (next spin / config change) |
| F3 | MINOR | Stale live-release pointers: BRIEF current_release=v1.0, README "v1.0 released", PROGRESS ends at v1.0 — seven releases behind | pre-fix files at git eaf413d | **FIXED this audit** (commit 272487e) | No |
| F4 | MINOR | ERRATA.md corrupted: a pasted `git add … && git commit … && git push` command line + full duplicate of the sole entry sat in the file since 2026-07-17 | 01_docs/ERRATA.md pre-fix (lines 7–15) | **FIXED this audit** (cleaned, content preserved, cleanup noted in-file) | No |
| F5 | MINOR | Canon M3 letter unmet: promoted route chain 03_src/route/r3.kicad_pcb is git-tracked but its sha is in NO MANIFEST (grep r3 07_releases/*/MANIFEST.txt → empty) — same gap found on usb-power-3s | MANIFEST files | Record the chain-file sha in the next release's MANIFEST; sealed releases untouched | No |
| F6 | MINOR | Release PDF polish: assembly_top.pdf has severe overlapping Fab text (terminal rows triple-overprint, LM339 divider cluster illegible) + empty title block — degrades the hand-solder aid for exactly the 10 THT joints a human solders | 07_releases/v1.7…/pdf/assembly_top.pdf render | export_pdfs.sh: Fab-text de-collision + title block vars; next release | No (cosmetic; board silk itself is clean) |
| F7 | MINOR | S6 debt: schematic still >90% label-paired (16 wires); fresh-eyes reviewer graded the story-path criterion a fail even while praising the labeling discipline | fresh render review this audit | schwriter2 path-syntax upgrade (already the queued fleet remediation); mandatory-graded until then | No |
| F8 | NOTE (process) | Fresh-render protocol hazard, caught live: generic filenames (board_top.png) in a shared scratchpad served a DIFFERENT project's stale render to the review agent, which correctly refused to certify. Renders re-cut with project-prefixed names and re-reviewed | render agent transcript; scratchpad file dates | Encode in the review protocol: project-prefixed render filenames + the reviewer must confirm the board title text matches the project | No |
| F9 | NOTE | CHECKLIST referenced the antenna gate as I8 (it is I3; I8 is COMP length spread) | CHECKLIST.md pre-fix | **FIXED this audit** | No |

## 8. Bottom line — orderability

**The live release v1.7-2026-07-17 is ORDERABLE AS-IS.**

- Fab package: fresh DRC 0/0/0 + parity 0 from the exact release board;
  sha table verifies; fab byte-identical to v1.1 (the copper that passed
  twin + pin review + this audit); 11-file 2-layer zip; STANDARD JLC
  options suffice (0.6/0.3 vias) — correctly documented.
- BOM/CPL: all 20 coded lines IN STOCK today at ≥5×; 5 unique Extended;
  10 deliberate hand-solder THT lines with codes/plan in ORDER_README.
- **Mandatory at order time** (already in ORDER_README, re-endorsed):
  walk the rotation/polarity preview checklist — especially D2 LED
  (twin model unmarked; JLC preview is the only machine-independent
  check) and C11 electrolytic stripe vs the '+' silk; the four
  ROT-DB-vs-fit family disagreements (SOT-23, SOT-23-6, SOIC-14, USB-C)
  are prior-order-verified DB rows but must be eyeballed per the twin's
  EDA-zero/assembly-zero gap.
- Ignore the contradictory history sections in ORDER_README (F1): the
  authoritative story is CHANGELOG + the SUPERSEDED chain — J1 ships
  with NO rotation override, which is the correct state.
- Both waivers remain evidence-valid; the R3 gap (F2) is a
  gate-configuration + next-spin item, not an orderability blocker.

Audit fixes committed (docs only — no schematic/board/fab/release
artifacts touched): 272487e (BRIEF/README/PROGRESS pointers, ERRATA
cleanup, CHECKLIST I3), plus this report.

## 9. Independent finalization pass (2026-07-19, second reviewer)

The partial report above was checkpointed "waiting on the board-render
regrade." A second, fresh-context reviewer re-ran the full gate battery
from the released source and re-derived the load-bearing measurements —
NOTHING trusted from the checkpoint's own bundle. All reproduce:

- **M-REL / release integrity.** v1.7 sha256 table re-hashed 6/6 MATCH.
  git_sha `eaf413d` exists; board at that commit = working tree =
  `870b65e4…` (MANIFEST gates-line claim), byte-for-byte. All 8 release
  git_shas exist as commits. Fab byte-identity re-hashed: gerbers.zip
  `b3a0c897…` + bom `015ee5ea…` + cpl `a54ecc66…` IDENTICAL across
  v1.1–v1.7; v1.0's zip differs (`ab9324f0…` — the refdes-less silk,
  correctly quarantined; bom/cpl unchanged). SUPERSEDED chain re-walked:
  v1.0–v1.6 each carry SUPERSEDED.md, v1.7 (live) has none — closed.
- **Gates from the released board.** Fresh `kicad-cli sch erc
  --severity-all` = 0 violations. Fresh `kicad-cli pcb drc --severity-all
  --refill-zones --schematic-parity` = 0 / 0 / 0. policy_audit FULL =
  **zero FAIL** (15 PASS, 2 WAIVED, 7 HUMAN, 2 N-A). Project audit_board.py
  = PASS 0 fails 0 warns.
- **Waiver evidence re-verified true.** R-RULES: `06_build/route/r0.kicad_pro`
  net classes = `['Default']` exactly, while current `04_kicad` project
  carries `['Default','PWR','COMP','LSW']` + a 4-rule `.kicad_dru`. R-POUR:
  5V = 0.6 mm on every segment, 3V3 = 0.6 mm on every segment (both ≥ the
  0.5 mm floor).
- **F2 (R3) re-measured independently.** audit_board.py contains NO
  plane/B.Cu-region check (grep of its check IDs: I1–I10, antenna=I3,
  keepout, separation=I7, polarity=I9 — no plane item); policy_audit
  R-PLANE = "no plane_regions configured" (HUMAN). Re-measured under the
  analog region: VTH×16 (VTH1/2/3 = 6/6/4) plus COMP/3V3/5V/BTN B.Cu
  signal segments cross under it — the ARCHITECTURE "audit checks no B.Cu
  track crosses under it" claim describes a gate that does not exist. F2
  stands (electrical risk LOW; the unenforced-intent doc drift is the R3
  motivating incident, still open).
- **F5 (M3) re-confirmed.** `grep r3\. 07_releases/*/MANIFEST.txt` → empty;
  the promoted chain `03_src/route/r3.kicad_pcb` is git-tracked but its sha
  is in no MANIFEST.
- **R5 re-measured.** COMP lengths {65.9, 62.9, 74.9} mm, spread 11.9 mm <
  40 mm gate (I8) — identical to release audit.txt.
- **J1 double-flip final state re-verified.** `model_rot_z` appears in the
  twin adjudication ONLY inside the prose describing the reverted v1.2
  error — NO override field is applied; entry is MODEL-REG FALSE-ALARM,
  fit 0.00 mm 22/22 = JLC CAD, mounted at JLC's own `(rotate 0 0 180)`.
  M6 final state CORRECT.
- **Board render regrade completed.** Fresh top render independently
  confirms P4 (all refdes on silk, legible incl. the dense comparator
  bank), P5 (USB-C 5V, PIN MAP block, LASER/PHOTODIODE/BUTTON per-pin
  labels, OLED "CHECK MODULE PINOUT" warning — exemplary), P2 (C11 '+'
  at the pad-1/south side; board silk reads "v1.1", correct for the
  byte-identical copper). F6 re-confirmed: assembly_top.pdf shows severe
  Fab-text overprint in the terminal rows + divider cluster and an empty
  title block.
- **272487e doc fixes present.** BRIEF `current_release=v1.7`, README
  "v1.7 released", CHECKLIST antenna gate = I3, ERRATA carries zero
  pasted git-command lines.

**Verdict unchanged and CONFIRMED: v1.7-2026-07-17 is ORDERABLE AS-IS**,
subject to the order-time rotation/polarity preview walk (D2 LED, C11
stripe, the four ROT-DB families) already in ORDER_README. The two MAJOR
findings are documentation/gate-config items, not fab blockers: F1
(ORDER_README history self-contradiction — authoritative story is
CHANGELOG + SUPERSEDED chain: J1 ships with NO rotation override) and F2
(R3 gate unenforced — config + next-spin). No new release is required to
order; both MAJORs are next-release/next-spin fixes. Sealed
schematic/board/fab/release artifacts were NOT touched by either pass.
