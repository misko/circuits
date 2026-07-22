# shitty-kitty — full independent review + audit (2026-07-19)

Fresh-eyes audit of the released project against the CURRENT canon
(`design-policies.md` incl. S-DSL, R-THERM, P-SILK-FN, R-RULES, M-REL).
Live release under audit: **07_releases/v1.0-2026-07-18** (only release;
no SUPERSEDED chain). Protocol identical to
usb-power-3s/06_build/full_review_2026-07-19.md.

Everything below was re-measured on 2026-07-19: fresh policy_audit (FULL),
fresh `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity`,
fresh ERC, fresh stock check, THREE fresh-context pin reviews (new agents,
conclusion-free dossiers regenerated today in
06_build/audit_2026-07-19/pin_dossiers/), a fresh-context render review on
renders generated today, and an independent polarized-part re-derivation.
Nothing is copied forward from the release's own verification bundle
without re-verification.

**Completion provenance (2026-07-19):** this audit was checkpointed by a
Fable agent that exhausted credits, then FINISHED and INDEPENDENTLY
RE-VERIFIED by an Opus continuation. Every checkpoint claim was re-derived
from primary sources (board nets, git objects, fresh DRC/ERC/policy_audit,
own-eyes render): all held EXCEPT F7 — the Fable draft asserted the
`sk-v1.0` tag was "created this audit" but `git tag -l` showed it never
was. The Opus continuation created the annotated tag at seal commit
a6ce780 (tag object 1523518) and corrected the F7/M5 rows below. Re-verified
from scratch and confirmed grounded: MANIFEST sha256 (3/3), board
byte-identity to 326aba3/a6ce780 (6d524e7e…), MPR121 ADDR straps
(0x5A-0x5D distinct, from pad-4 nets), TMC2209 coil/sense pairing + ENN
strap (from pad nets), Q1/U9/U2 thermal-via counts (2/2/17), F1 twin
ROT-DB-SUGGEST evidence (17 rows), fresh DRC 0/0/0, policy_audit zero-FAIL.

## 1. Graded scoreboard (every canon ID)

| ID | Grade | Evidence (re-measured 2026-07-19) |
|---|---|---|
| S1 / S-ERC | PASS | fresh ERC at severity-all: 0 errors, 0 warnings |
| S2 / S-NET | PASS | 79 routed nets all deliberately named; autonames only on sanctioned NC pins |
| S3 / S-VER + pin review | PASS | 12/12 part.yaml `verified:` cite figure+page; THREE fresh-context re-derivations today (§3): MPR121 x4, TMC2209, ESP32-S3 — no mirror, no swapped pin, all PASS |
| S4 / S-NC | PASS | all floats no_connect-flagged; ERC pin_not_connected = 0; every float independently sanctioned against the datasheets by today's reviewers (TMC VREF/STDBY "may be left open" incl. the defined 73% open-VREF scale; ESP32 IO3/45/46 strap floats safe; MPR121 ELE6-11 DS-allowed) |
| S5 | PASS | math re-derived exactly: buck ripple 5x0.583/(10u x 1.1M)=0.27A, I_L_pk 2.13A < 3.5A Isat; TMC I_RMS = 0.325/0.17/sqrt2 = 1.35A (0.15R, vsense=0); LDO 1.7V x 0.4A = 0.68W; input 11.4W/12V = 0.95A + motor 0.46A < F1 2A hold; TVS clamp 26V < TMC 29V abs-max — all match DETAIL_DESIGN and shipped BOM values |
| S6 | PASS-with-notes | fresh render review: 8 titled section boxes with story captions + ~17-19 drawn story wires (entry chain J1->F1->Q1->TVS, buck SW->L1->Cout, TMC coil outputs->J5, U3 ELE0-5->J3, EN/endstop RCs); ESP32->TMC control lines and the I2C chain remain label-only — hybrid, well above label-blob; minor pin-text run-togethers ("GNDFB/VOUT" at U8, "GNDVBUS" at D1, "IO37" clip at U1) — F4 |
| S7 | PASS-with-notes | every cap drawn inside its IC's section with purpose captions ("100n VREG", "4.7u buck in"); rows are label-connected, not pin-wired — same accepted debt class as usb-power-3s |
| S-DSL | PASS | schwriter2 -> native .kicad_sch; all gates run on artifacts |
| S-OCCL | PASS | fresh policy_audit: 0 text occlusions |
| P1 / P-CRT | PASS | fresh full-severity DRC: 0 courtyard findings |
| P2 / P-POL | PASS | machine check present AND independently re-derived today (§4): D2/D5 LED pad1(cathode)=GND, C40/C41 pad1(+)=VIN_12V, D3 pad1(cathode)=VIN_12V rail, J1 pad1=TIP=VIN_RAW center-positive with "2.1mm CENTER +" silk, L1/F1 non-polar — all correct vs footprint conventions; render review: "+" silk on both electrolytics; weak silk polarity marks on D3/D5 noted (F5) |
| P3 / P-KEEP | PASS | audit_board.py mate/edge/keepout checks present; fresh audit PASS 0 fails 0 warns; ESP32 antenna end (pad-free north end of module) hangs over the y=125.075 board edge — off-copper by construction |
| P4 / P-SILK-REF | PASS | re-measured: 77/78 refdes on visible F.Silkscreen; H1-H4 mounting holes exempt; J5 hidden refdes carried in 06_build/refdes_waiver.json (functional "MOTOR A1 A2 B1 B2" silk present) — waiver file is a bare list, no evidence note (F6) |
| I10b | PASS | fresh render review: all refdes legible, no collisions; densest cluster (around U2) still readable |
| P5 / P-SILK-FN | PASS (strong) | re-measured silk inventory + render review: "12V IN / 2.1mm CENTER +", "MOTOR" + per-pin A1/A2/B1/B2, "ENDSTOP" GND/SIG, "HOST UART+5V / 5V MAX 1.5A" + per-pin 5V 5V G G TX RX, electrode headers fully numbered 1-12+G on both, "USB-C DATA ONLY / POWER FROM 12V", RESET/BOOT/STATUS/PWR, "MOTOR OFF AT BOOT: ENN PULLUP R8" |
| P6 / P-PLANE | PASS | In1 carries only the GND plane (0 tracks); In2 = VIN_12V/5V/3V3 pours only |
| R1 / R-RULES | PASS | route-input 03_src/route/r0.kicad_pro carries all 9 netclasses (fresh policy_audit R-RULES); rebuild_all.sh runs generate_rules.py LAST (line 41) after every pcbnew save, then the DRC gate |
| R2 / R-POUR | PASS (graded honestly) | machine check vacuous here (no netclass >= 0.5mm width — see F3 note), so re-derived by hand: power trunks are In2 POURS (VIN_12V 2486mm2, 5V 1267mm2, 3V3 5349mm2) with 12/11/35 feeding vias; entry chain VIN_RAW/VIN_F routed 0.6-0.8mm; F.Cu taps floor-limited by QFN pad necks with the margin math WRITTEN in nets.yaml (MOTOR 0.35mm @1A chopped: "~25-35C rise worst case, StealthChop runs cooler, kept short" — honest, documented) |
| R3 / R-PLANE | N-A | no plane_regions configured; ELEC separation covered by project audit I7 |
| R4 | PASS | 0.4mm-pitch UQFN + 0.5mm QFN escaped at JLC 4L STANDARD tier (0.45/0.30 vias, fab_overrides.txt pins the floor, no advanced option) — DRC 0/0/0 proves feasibility; no small-via order dependency at all |
| R5 / R-LEN | PASS | electrode length-spread audit present (audit I8: 24 stubs routed, max 22.7mm) — note DETAIL_DESIGN says "<20mm", measured max is 22.7mm (F4 doc drift) |
| R6 / R-THERM | PASS | fresh check: Q1 DPAK tab 2 same-net vias, U9 SOT-223 tab 2, U2 EP 17, all pads >= 4mm2 covered — the Q1/U9 R-THERM retrofit (commit 326aba3) HELD |
| R7 / R-DRC | PASS | FRESH severity-all + refill-zones + schematic-parity today: **0 / 0 / 0** — identical to release verification/drc.json |
| M1 | PASS | independent-reference battery demonstrably ran: jlc_twin (54 OK + adjudications), 5 fresh pin reviewers at release, and THIS audit re-ran pin/render/polarity checks from outside the project's assumptions |
| M2 | PASS | policy_audit.py FULL + project audit_board.py both present and green |
| M3 / M-REPRO | PASS (one gap -> F2) | all rebuild inputs git-tracked incl. promoted chain 03_src/route/r5.kicad_pcb + r0.kicad_pro/dru; GAP: the chain file's sha is recorded in NO MANIFEST (letter of M3 unmet — same class as usb-power-3s F5) |
| M4 / M-WAIV | PASS | 14 twin adjudications all carry measurements (pad-pitch numbers, datasheet citations, pad_alias restores coverage per the alias-over-waiver rule); policy_waivers.yaml empty (nothing waived); evidence spot-re-verified: J6 3.5mm pitch on board, SOT-223 TabPin2 merge, DPAK 6.70-vs-7.31 precedent, ESP32 EP 40-perimeter non-mirror fit 0.008mm |
| M5 / M-REL | PASS (one gap -> F7) | sha256 table verifies 3/3 (gerbers.zip, bom.csv, cpl.csv); git_sha 326aba3 exists, board at HEAD byte-identical (sha256 6d524e7e...) to that commit; fresh DRC from it = 0/0/0; git_dirty claim true; CHANGELOG names the dir; release sealed at a6ce780; GAP (F7, now closed): CHANGELOG claims "[tag: sk-v1.0]" but the tag did not exist — the Opus continuation created the annotated tag `sk-v1.0` at a6ce780 (tag obj 1523518), verified present. NB the M-REL machine check does NOT test tag existence (it passes on provenance+hashes) — the tag gap is a human-graded catch |
| M6 | FINDING (F1) | authoritative-source discipline mostly honored (MODEL-REG Q1/J2 dispositioned per JLC's own footprint rotation, per the USB-C saga rule), EXCEPT: rotation fit-vs-DB conflicts on JLC-assembled oriented ICs left without disposition or eyeball-list coverage (see F1) |

Fresh policy_audit.py summary (FULL mode, 2026-07-19): **zero FAIL** —
19 PASS, 6 HUMAN (all graded above), 1 N-A. Fresh stock check today:
**all 27 coded lines in stock** at >= 5x qty (MPR121 lowest at 1179 units);
6 lines intentionally uncoded (THT hand-solder, matches MANIFEST
not_assembled exactly).

## 2. Release integrity (M-REL detail)

- v1.0 MANIFEST sha256: 3/3 files re-hashed, all match.
- `git_sha 326aba3` exists ("R-THERM power-pad vias; pin+render review
  PASS; cost estimate"); `04_kicad/shitty_kitty.kicad_pcb` at HEAD ==
  326aba3 byte-for-byte; fresh DRC from that source: 0/0/0.
- Release dir committed/sealed at a6ce780; no hand-edits since.
- MANIFEST/ORDER_README internally consistent: 27 coded lines / 72
  placements / 6 THT hand-solder refs (J1,J3,J4,J5,J6,J8) — matches the
  BOM (27 coded + 6 uncoded) and the board.
- ORDER_README correctly states JLC 4L STANDARD tier, "do NOT select the
  advanced option" — board min via 0.45/0.30 confirmed in fab_overrides +
  release manifest; no hidden small-via dependency.
- Tag gap CLOSED this audit: annotated tag `sk-v1.0` now exists at a6ce780
  (tag object 1523518; `git for-each-ref refs/tags/sk-v1.0` confirms). It
  was claimed in CHANGELOG and by the Fable checkpoint draft but had NEVER
  been created — the Opus continuation created it (not pushed).

## 3. Fresh-context pin reviews (S3 bar: datasheet FIGURES first)

Three independent fresh agents, conclusion-free dossiers regenerated today
(pad geometry + nets only; no part.yaml functions leaked — the dossier
generator found no MPN mapping, which made the reviews *more* independent):

| Part group | Verdict | Key derivation |
|---|---|---|
| U3-U6 MPR121QR2 (UQFN-20) | **PASS x4** | MPR121 Rev4 p.1 top-view: pin1 IRQ upper-left, CCW — board winding identical, mirror explicitly ruled out (pins 1-5 on WEST). **ADDR straps all match the claimed addresses**: U3=GND(0x5A), U4=3V3(0x5B), U5=SDA(0x5C), U6=SCL(0x5D). Per-chip 75k REXT to GND (R20/22/24/26), 100n VREG caps (C31/33/35/37), VDD=3V3, dedicated IRQs w/ 10k pullups to distinct ESP32 GPIOs, electrode partition clean: U3=INNER1-6, U4=INNER7-12, U5=OUTER1-6, U6=OUTER7-12, ELE6-11 NC-flagged (DS-allowed). The tiny 0.115mm "pads" in the dossier are custom-pad anchors of the stock KiCad UQFN-20 footprint — not a geometry defect |
| U2 TMC2209-LA-T (QFN-28) | **PASS** | rev1.09 Fig 2.1: pin1 OB2 top-left, CCW — board identical, not mirrored (mirror would put UART on power pins). **Coil/sense pairs intact**: OA1(24)/OA2(21)->MOT_A1/A2->J5.1/2, OB1(26)/OB2(1)->MOT_B1/B2->J5.3/4 — each driver pair on ONE coil (the fatal cross-coil split is absent; any residual A/B swap is direction-only, benign). BRA/BRB -> 0.15R to GND (not motor pins). ENN active-low w/ R8 10k pullup to 3V3 = outputs OFF at boot, confirmed from the datasheet. VCP cap correctly references VS (VIN_12V), CPO-CPI flying cap = 22nF (C1729) per DS; V5OUT 4.7u in DS 2.2-4.7u range; MS1=MS2=GND (UART addr 0), CLK=GND, SPREAD=GND; VREF float sanctioned ("or leave open", defined 73% scale); EP=GND |
| U1 ESP32-S3-WROOM-1 (40+EP) | **PASS** | Fig 3-1: pin1 GND top-left, CCW — matches; independently corroborated by NC-autoname pin names matching the DS number-to-name map on all 14 floats. **Straps safe**: IO0=BOOT (pull-up default), IO3/IO45/IO46 float = sanctioned defaults (3.3V flash, normal boot); USB_D-(IO19)=USB_DM, USB_D+(IO20)=USB_DP not swapped; UART0 TXD0=HOST_TX/RXD0=HOST_RX; TMC single-wire = U1TXD-1k-PDN_UART + U1RXD direct (standard half-duplex). Reviewer's two conditionals closed on-board this audit: (a) TX/RX naming is BOARD-side by design (D8), J8 silk TX/RX sits on HOST_TX/HOST_RX pads and ORDER_README documents the crossover ("board TX -> host RX"); (b) EN has R6 10k pullup + C11 1u + SW2 reset — never floats |

## 4. Independent polarized-part re-derivation (Q9-class hunt)

Board pad-1 nets vs the FOOTPRINT's own convention (not part.yaml):

| Ref | Footprint (pad1 meaning) | pad1 net | Verdict |
|---|---|---|---|
| D3 SMBJ16A | D_SMB (pad1=cathode) | VIN_12V | OK — cathode to rail, unidirectional TVS correct |
| D2/D5 LEDs | LED_0805 (pad1=cathode) | GND | OK — anode fed via 1k from rail/GPIO |
| C40/C41 100u | CP_Elec (pad1=+) | VIN_12V | OK — "+" silk paired (render-verified) |
| J1 DC-005 | pad1=TIP | VIN_RAW | OK — center-positive, "2.1mm CENTER +" silk; sleeve pads 2/3 = GND |
| Q1 AOD4185 | TO-252 (1=G, 2=tab=D, 3=S) | GATE_Q1 / VIN_F / VIN_12V | OK — P-FET reverse-polarity: drain=battery side (VIN_F), source=load (VIN_12V), gate pulled to GND via R1 100k; body diode blocks reversal |
| F1/L1/SW1/SW2 | non-polar / rail-merged | — | OK (twin pad_alias restored SW1/SW2 coverage) |

MOTOR-DISABLED-AT-BOOT strap verified electrically: ENN net = {U2.2 (ENN),
R8.2 (10k to 3V3), U1.6 (IO6 — a non-strap GPIO, hi-Z at reset)}. Pullup
wins at boot; TMC outputs off. G5 met in copper, not just prose.

## 5. History coherence

- ARCHITECTURE power tree == shipped board (J1->F1->Q1->TVS/bulk ->
  TMC VS + buck -> 5V -> LDO -> 3V3; USB-C powers nothing — VBUS only
  references the ESD array; verified on nets).
- DETAIL_DESIGN math re-derives (S5 row). Electrode ring assignment
  U3=IN1-6/U4=IN7-12/U5=OUT1-6/U6=OUT7-12 matches the board exactly.
- D13 (2x-vs-4x MPR121 next-spin cost note) is coherent everywhere it
  appears: BRIEF D13, COST_ESTIMATE Goal-1c ("$10.67 = 43% of component
  cost"; 2x12ch drop-in, "out of scope for v1.0, flagged for next spin"),
  and the shipped board indeed runs 4 chips at 6/12 channels each. The
  optimization is correctly a NEXT-SPIN design change, not a v1.0 defect.
- ADRs 0001-0005 still describe the board. PROGRESS "DONE" state true.
- Drift found & FIXED this audit: BRIEF goal table G1-G5 all still said
  "unmet" after the release shipped; no release entry in the BRIEF log
  (F8) -> corrected, current_release pointer added.

## 6. Findings table

| # | Sev | Finding | Falsifiable evidence | Remediation | New release? |
|---|---|---|---|---|---|
| F1 | **MAJOR** | Twin ROT-DB-SUGGEST fit-vs-DB conflicts on JLC-ASSEMBLED oriented parts left undispositioned, and the ORDER_README preview-eyeball list omits every IC among them. Shipped CPL rotations came from the community DB (U2 QFN-28: fit says offset 90, DB applied 270 — 180 apart; U8 TSOT: fit 90 vs DB 180) or from NO DB row at all (U3-U6 UQFN-20 and U7 LGA-12: twin suggested 90, nothing adopted; note "UQFN-20" does NOT match the DB's `(.*?_|V)?QFN-…` pattern, so the generic QFN rule silently skipped all four MPR121s). The DB is the validated empirical layer and fit-vs-assembly-zero disagreement is a KNOWN ambiguity — but per M6 only JLC's order preview (or first article) can arbitrate, and no preview evidence exists in verification/. A 90/180-wrong QFN = dead board (VS<->GND). | 06_build/twin/twin_report.csv rows U2/U8/U7/U3-U6 (17 ROT-DB-SUGGEST total); jlc_rotations_db.csv QFN pattern; cpl.csv rotations U2=270, U3-6=90, U7=90, U8=180; ORDER_README eyeball list (names only D1/D2/D5/D3/Q1/C40/C41) | **Mandatory before first power** (5 boards ordered 2026-07-18): first-article visual check of pin-1 marks vs board silk for U2, U3-U6, U7, U8 (plus the already-listed D1/D2/D5/D3/Q1/C40/C41). Record the outcome as twin adjudications; add the ICs to the ORDER_README eyeball list next release; after empirical confirmation add the missing `UQFN-20`/`LGA-12` rows (or widen the QFN pattern) to jlc_rotations_db.csv | Not by itself; corrected-CPL release ONLY if first article shows misrotation |
| F2 | MINOR | Canon M3 letter unmet: promoted route chain 03_src/route/r5.kicad_pcb is git-tracked and named in the MANIFEST tools line, but its sha256 is recorded nowhere | `grep r5 MANIFEST.txt` -> mention without hash | Record the chain-file sha in the next release's MANIFEST (sealed release untouched) | No |
| F3 | MINOR | R-POUR machine check is VACUOUS on this board (`0 nets`): it keys on netclasses with track_width >= 0.5mm, and every class here is 0.25-0.4mm (deliberate QFN-neck floors). The policy intent (power on pours) IS met — In2 pours re-verified by hand — but the auditor would not catch a future regression | 06_build/policy_audit.md R-POUR row; .kicad_pro netclass widths | Teach policy_audit R-POUR to also key on nets.yaml `current:` >= 1A (or a config net list) so pour coverage is checked by declared current, not track width | No |
| F4 | MINOR | Doc-vs-artifact drift, three instances: (a) ARCHITECTURE prose floors ("PWR12 0.8mm / MOTOR 0.6mm / PWR5 0.5mm") vs enforced DRU floors 0.30/0.35/0.40 — nets.yaml carries the honest neck-limit rationale but ARCHITECTURE was never aligned; (b) DETAIL_DESIGN "5VOUT: 2.2uF (C19110)" vs shipped 4.7u C1779 (DS range 2.2-4.7u, electrically fine); (c) DETAIL_DESIGN/ARCHITECTURE "stubs < 20mm" vs audit-measured max 22.7mm | ARCHITECTURE.md net-domains section; DETAIL_DESIGN passives table; audit.txt I8 line | Align the three doc claims with nets.yaml/board reality in the next doc pass (nets.yaml is already the declared source of truth) | No |
| F5 | MINOR | Silk polarity marks weak on D3 (no cathode bar — bracket only) and D5 (plain rectangle); D2 has only a small corner tick. Assembly is CPL-driven and the twin/pin reviews verify the nets, but hand-rework polarity relies on the fab drawing | fresh render review (today); board silk inventory | Add cathode-bar silk for D3/D2/D5 in the next spin (generator change) | No (cosmetic; covered by F1's first-article check) |
| F6 | NOTE | J5 refdes-on-silk waiver (06_build/refdes_waiver.json) is a bare `["J5"]` with no evidence note — M4 wants the why recorded (the why is real: "MOTOR" + A1/A2/B1/B2 functional silk occupies the space) | refdes_waiver.json | Add the one-line evidence note when next touched | No |
| F7 | NOTE (fixed) | CHANGELOG claimed `[tag: sk-v1.0]` but the tag was never created. The Fable checkpoint draft ALSO claimed it fixed this — it had not (`git tag -l` still showed no sk-v1.0 at Opus handoff). | `git tag -l` (showed no sk-v1.0 at both the pre-Fable state and the Opus handoff) | **FIXED (Opus continuation)**: annotated tag sk-v1.0 created at seal commit a6ce780, tag obj 1523518, verified via `git for-each-ref` (not pushed) | No |
| F8 | NOTE (fixed) | BRIEF goal table G1-G5 stale ("unmet" post-release); no release/log entry | 01_docs/BRIEF.md (pre-fix) | **FIXED this audit** (doc commit) | No |

## 7. Bottom line — orderability

**The live release v1.0-2026-07-18 is SOUND — already ordered (qty 5,
2026-07-18) — with ONE mandatory arrival action (F1):**

- Fab package: DRC re-verified 0/0/0 TODAY from the exact release source;
  sha table verifies; JLC 4L STANDARD tier, no advanced option — correctly
  documented.
- BOM/CPL: all 27 coded lines IN STOCK today (>= 5x qty); 6 intentional
  hand-solder THT lines match the MANIFEST.
- Electrical design independently re-derived clean today: MPR121 addressing
  and electrode partition, TMC2209 coil/sense pairing, ESP32 straps/USB/UART,
  every polarized part, the ENN boot-disable strap, thermal-via retrofit,
  In2 power pours.
- **Mandatory (F1): on first article, BEFORE first power — verify pin-1
  orientation of U2/U3-U6/U7/U8 and polarity of D1/D2/D3/D5/Q1/C40/C41
  against the board silk, then run the ORDER_README first-power ritual
  (barrel polarity beep-out, rails, ENN high).** The CPL rotation layer is
  the one subsystem whose correctness could not be re-proven from the repo
  alone (fit-vs-DB ambiguity + missing UQFN/LGA DB rows).
- Re-spin queue already tracked: D13 2x-MPR121 cost optimization, F4 doc
  alignment, F5 diode silk, F1 DB rows + eyeball-list expansion.

Audit changes committed (docs/tag/audit artifacts only — no schematic,
board, fab, or sealed-release files touched): BRIEF goal-table fix + log
(Fable checkpoint — verified real), the **sk-v1.0 annotated tag (created in
the Opus continuation — the one checkpoint claim that had not actually been
executed)**, fresh policy_audit/DRC/ERC artifacts, pin dossiers + this
report. Every canon ID re-graded above was re-measured from primary
sources this session, not copied from the checkpoint text.
