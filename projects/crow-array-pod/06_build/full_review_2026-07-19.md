# crow-array-pod — full independent review + audit (2026-07-19)

Fresh-eyes audit of the released project against the CURRENT canon
(`design-policies.md` incl. S-DSL, R-RULES, P-SILK-FN, M3 promotion, M-REL).
Live release under audit: **07_releases/v1.1-2026-07-19** (SUPERSEDED chain
v1.0 → v1.1 verified closed; v1.0 never ordered, quarantined with reason —
A4 termination change + latent lid interference). Protocol identical to
usb-power-3s/06_build/full_review_2026-07-19.md.

Everything below was re-measured on 2026-07-19 (fresh ERC + DRC + policy
audit + project audit, fresh stock check, THREE fresh-context pin reviews,
fresh render review from re-rasterized release PDFs, board-file geometry
extraction with pcbnew) — nothing is copied forward from the release's own
verification bundle without re-verification.

## 1. Graded scoreboard (every canon ID)

| ID | Grade | Evidence (re-measured 2026-07-19) |
|---|---|---|
| S1 / S-ERC | PASS | fresh `kicad-cli sch erc --severity-all`: 0 errors, 0 warnings |
| S2 / S-NET | PASS | 18 routed nets all deliberately named; only sanctioned `unconnected-(…)` autonames on NC pins (J1 LED tails, BZ1 dummies, D1 NC) |
| S3 / S-VER + pin review | PASS | 6/6 part.yaml `verified:` cite figure+page; THREE fresh-context re-derivations run today (§3): J1 RJHSE-5384, BZ1 CMT-8504, U1 OPA1678 — no mirror, no swapped pin, all PASS. **Both historical doc-error catches re-confirmed fixed**: BZ1 +/− pad convention (fresh reviewer re-read the datasheet p.2 figures incl. the bottom-view mirror trap: pad1=+ top-left ✓) and the J1 mating-face doctrine (fresh reviewer re-derived face=SNAP-POST side from the p.4 side-view chain .215 [5.46]; "LED tails mark the face" confirmed INVERTED, the corrected part.yaml gotcha stands) |
| S4 / S-NC | PASS | 8 generator-emitted no_connect flags; ERC pin_not_connected = 0 |
| S5 | PASS | math re-derived twice (me + fresh render agent): G_A = 1+10k/20k = 1.50; inverter −20k/20k = −1; VMID = 5VF/2 ≈ 2.47 V; 5VF drop 0.75 mA×100R = 75 mV; mic node ≈ 2.9 V; C3/R3 HPF 1.6 Hz; R6∥R7 = 6.7k noise floor — all match DETAIL_DESIGN + BOM values |
| S6 | PASS (with effort) | fresh review: story paths ARE drawn as wires (J1 → shield block → choke bypass → D1 ESD → 68R → both op-amp stages; beeper J1 → R12 → BZ1 with D2/D3 across the pair) — a real step past the fleet's label-blob era; VMID distribution still label-like (4 sites), GND/5V power symbols scattered |
| S7 | PASS | C6/C7 drawn at U1.V+, C4/C5 at the VMID node, C1/C2 at the 5VF filter — no cap farm |
| S-DSL | PASS | schwriter2 → native .kicad_sch; every gate runs on artifacts |
| S-OCCL | PASS | fresh policy_audit: 0 text occlusions |
| P1 / P-CRT | PASS | fresh full-severity DRC: 0 courtyard findings |
| P2 / P-POL | PASS | machine check present AND independently re-derived (§4): C1 pad1(+)=5VF with silk + on the correct (west) side vs the twin model's east negative stripe; D2 & D3 pad1(cathode)=BZ_P = supply side exactly per ADR-0002 doctrine; BZ1 pad1(+) top-left re-derived from the datasheet figure; J1 keyed-connector orientation re-derived (face WEST) |
| P3 / P-KEEP | PASS | fresh audit_board.py: PASS 0 fails 0 warns (incl. I2 lid-recess containment, screw keepouts, I8 AIN length 13.1 mm) |
| P4 / P-SILK-REF | PASS | fresh render review: every refdes prints on F.Silk, legible (refdes_waiver.json = []). Nit: J1's refdes tiny/rotated, crowded against D2's "K"+"FLYBACK" group — cosmetic, next rev (F5) |
| P5 / P-SILK-FN | PASS | "NOT ETHERNET — CUSTOM 5V PINOUT" north banner (x≈102.3–133.4, measured ~3.9 mm clear of L1 silk ending x≈98.5 — the v1.1 banner-fix claim re-verified) + second "NOT ETHERNET" west of the jack (visible with plug in) + per-contact legend in the plug zone matching the ADR-0004 map + labeled TPs/MIC PADS/BEEPER/FLYBACK/TVS DNP |
| P6 / P-PLANE | N-A | 2-layer; covered by R-PLANE named regions |
| R1 / R-RULES | PASS | route input r0.kicad_pro carries classes [Default, PWR, BEEP, AUDIO]; final 04_kicad .kicad_pro still carries them (rules generator ran last) |
| R2 / R-POUR | PASS | no high-current-class nets (max 150 mA beeper burst); PWR/BEEP floors 0.4 mm; B.Cu = continuous GND pour, no stranded islands (fresh render) |
| R3 / R-PLANE | PASS | named-region continuity (B.Cu under U1 r8mm / C3 r5mm) machine-checked, passing |
| R4 | PASS | largest escape challenge is SOT-553 at standard 0.6/0.3 vias; board uses ONLY 0.6/0.3 vias, track widths 0.3–0.6 mm — JLC STANDARD tier confirmed (matches ORDER_README "no advanced option") |
| R5 / R-LEN | PASS | I8 AIN routed length 13.1 mm, gate present in 03_src and passing |
| R6 / R-THERM | N-A | 2-layer, no internal plane; no EP parts on power |
| R7 / R-DRC | PASS | FRESH `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity`: **0 / 0 / 0** — identical to verification/drc.json |
| M1 | PASS | the independent-reference battery demonstrably ran and RE-RAN today from outside the project: datasheet-figure pin reviews (3 fresh agents), catalogue pixel measurement (J1), JLC CAD twin (25 MODEL-REG-OK), render pixel measurement (banner, hole field) |
| M2 | PASS | canon enforced by policy_audit.py (fresh run: 18 PASS / 6 HUMAN / 2 N-A / **0 FAIL**) + project audit_board.py |
| M3 / M-REPRO | **FINDING (F1)** | all rebuild inputs git-tracked (policy_audit letter-PASS), BUT the promoted chain 03_src/route/r3.kicad_pcb is **STALE** — shipped copper derives from 06_build/route/r3.kicad_pcb, and no MANIFEST records any chain sha. See F1 |
| M4 / M-WAIV | PASS | 3 twin adjudications + ADR-0004(b2) D1 acceptance all carry measurements; every one RE-VERIFIED against current artifacts today (§2b) |
| M5 / M-REL | PASS | v1.1: 6/6 sha256 verify; git_sha 543e376 exists; board at HEAD == board at 543e376 (sha256 09a1f47b…); fab files byte-identical release↔06_build; fresh DRC from that exact board 0/0/0; CHANGELOG names the dir; v1.0 chain closed (SUPERSEDED.md → v1.1) and v1.0's own 6/6 sha table also verifies; both fix-claims independently re-verified (face-WEST re-derived by a fresh agent from the datasheet side-view chain + pcbnew positions; banner clearance re-measured ~3.9 mm) |
| M6 | PASS | authoritative-source discipline held: ROT-DB kept as the assembly-zero layer with the JLC preview named as tie-breaker (ORDER_README item 2); PAD-GEOM adjudicated against TI's own land-pattern drawing — independently confirmed today by the fresh U1 reviewer reading D0008A p.53/54 (both 4.95 and 5.42 mm span variants land the feet fully) |

## 2. Release integrity (M-REL detail)

- v1.1 MANIFEST sha256: all 6 files re-hashed, all match; gerbers/bom/cpl
  byte-identical to 06_build/fab (single source of truth).
- `git_sha 543e376` exists; `04_kicad/crow_array_pod.kicad_pcb` at HEAD ==
  at 543e376 (sha256 09a1f47b…). Fresh DRC+parity from that board: 0/0/0.
- v1.0 (superseded): 6/6 sha table verifies, git_sha 17ceffe exists,
  SUPERSEDED.md names v1.1 + reason (A4 + latent lid interference). Chain closed.
- Stock re-verified TODAY: **15/15 coded lines in stock** (≥10× need), 2
  intentionally uncoded hand-solder lines (J1 jack Digi-Key, J2 mic pads).
  C22359707 (CMT-8504) still **182** — the MANIFEST's mandatory order-day
  re-check stands unchanged.
- CPL spot-check: U1 rotation 270 (rotations-DB), Y-axis negated correctly,
  polarized parts at rot 0 with silk-verified marks.

### 2b. Waiver/adjudication evidence re-verification (all 3 + 1)

| Entry | Evidence claim | Re-verified today |
|---|---|---|
| U1 C192421 PAD-GEOM | KiCad 4.95 vs JLC/TI 5.42 span both legitimate D0008A patterns | ✓ board pads measured ±2.475 (4.94) via pcbnew; fresh U1 reviewer independently read TI D0008A outline+land pattern (p.53/54): toe margins ≥0.35 mm both variants, no solderability concern |
| U1 C192421 ROT-DB-SUGGEST | keep "^SOIC-",270; JLC preview is tie-breaker | ✓ cpl.csv ships 270; ORDER_README item 2 carries the MANDATORY pin-1-dot preview check |
| J1 C9900035627 NO-CAD | land pattern verified vs catalogue figures | ✓ every claimed dimension re-measured on the board with pcbnew: stagger 1.02/row offset 1.78, LED tails 4.82 from near row, SH Ø1.57 @16.26, NPTH Ø3.25 @12.70; fresh J1 reviewer re-derived the full pattern from the catalogue p.4 at 300 dpi — 180°-rotation match, NOT mirrored |
| ADR-0004(b2) D1 distance acceptance | clamp-first topology, closest legal position | ✓ D1 at x 87.8–89.2 directly east of the jack courtyard; fresh D1 spot review (release bundle) re-read + nets re-confirmed AUDIO_P/N/GND today |

Twin POLARITY-CHECK items (C1, D2) — the class left undispositioned on
usb-power-3s — are properly dispositioned here: render review §F (model
stripe vs silk agree for both) + ORDER_README checklist items 3/4.

## 3. Fresh-context pin reviews (S3 bar: datasheet FIGURES first)

Three independent fresh agents, conclusion-free dossiers regenerated today
(pin_audit.py), datasheets rendered and read at 300 dpi:

| Part | Verdict | Key derivation |
|---|---|---|
| J1 RJHSE-5384 (the interop-critical part) | **PASS** | catalogue p.4 layout re-derived hole-for-hole: footprint = 180° ROTATION, no mirror (every pitch matched: 2.032/1.016/1.78/2.29/16.26/12.70/4.83). Mating face re-derived from the side-view dim chain (face→post .215 [5.46]; LED tails 1.15 mm from REAR): posts at x=75.46 WEST of contacts x=78.00/79.78, LED tails x=84.60 EAST → **opening WEST** toward the gland ✓. Full interop truth table vs the central sealed map (all 8 central jacks measured from central's board file: AUD_Pn/AUD_Nn/BEEP_5Vn/5V_AUDn/GND/BEEP_RETn/5V_AUDn/GND, SH=GND): **pin-for-pin match over straight-through T568B, 1:1**; every DC loop closes inside one twisted pair (3/6 beep, 4/5, 7/8 power); SH → pod SHIELD floating (TP6 + DNP R15) vs central star bond = correct single-point-ground; LED tails NC ✓ |
| BZ1 CMT-8504 | **PASS** | datasheet p.2 top-view figures: (+) top-left, (−) bottom-left, right column dummies; reviewer explicitly handled the mirrored bottom-view trap. Footprint pad1(−3.5,−3.5)=BZ_P ✓, pad2=BEEP_RET ✓, dummies un-netted ✓; land pattern 2.5×2.5 @ ±3.5 exact match; silk "+" adjacent to pad 1 ✓ |
| U1 OPA1678 (SOIC-8) | **PASS** | Fig 5-3 derived: pin1 top-left, CCW, 4/4; dossier = zero rotation, NOT mirrored; all 8 nets electrically sane (OUT_A/FB_A/AIN/GND/VMID/FB_B/B_OUT/5V), A/B symmetry sane; D package has no EP ✓ |

## 4. Independent polarized-part re-derivation (Q9-class hunt)

Board pad-1 nets vs each FOOTPRINT's own convention (not part.yaml):

| Ref | Convention (pad1) | pad1 net | Verdict |
|---|---|---|---|
| D2 SS14 (D_SMA, pad1=cathode) | cathode = supply side per ADR-0002 | BZ_P | ✓ clamps the low-side-switch kick to the 5V feed |
| D3 SMAJ6.0A DNP (D_SMA) | same orientation as D2 required | BZ_P | ✓ identical, hand-fit safe |
| C1 100u (CP_Elec, pad1=+) | + to rail | 5VF | ✓, silk + west = model negative-stripe east |
| BZ1 (vendored, pad1=+) | + = drive feed | BZ_P | ✓ re-derived from datasheet figure |
| J1 (keyed) | face = snap-post side | — | ✓ opens WEST (fresh re-derivation) |
| D1 TPD2E2U06 | IO1/IO2/GND per DRL figure | AUDIO_P/N, GND | ✓ (release spot review re-checked) |

No self-consistent-wrong-together pair found. The two historical doc errors
(BZ1 pad prose, J1 face-side doctrine) are both FIXED in part.yaml and the
fixes independently re-confirmed today.

## 5. History coherence

- A4 decision trail is fully closed: BRIEF A4 (verbatim user utterance,
  2026-07-19) → D11 → ADR-0004 (net map vs BOTH interop authorities +
  clearance math + face-side correction + b2 D1 acceptance) → CHANGELOG
  v1.1 entry naming the release dir → v1.0/SUPERSEDED.md → MANIFEST.
  ADR-0003's terminal section explicitly marked superseded by 0004 ✓.
- The CONDITIONAL lid-fit gate is documented at every level it needs to be:
  ADR-0004c (13.46±0.38 body vs 13.70 recess headroom, +0.24 nominal /
  −0.14 worst-case, EMI tabs compress), MANIFEST mech_note, ORDER_README
  first-article instruction incl. the RJHSE-L384 fallback, and the release
  render review's condition 1. Fresh render review re-confirmed the jack is
  the ONLY >7.9 mm part and sits inside the 81×31 recess.
- ADR-0001/0002 still describe the board (D1 populated at entry; D2
  populated / D3 empty, pad1=cathode=supply doctrine matches copper).
- Drift found & FIXED this audit (F3): DETAIL_DESIGN.md still titled the
  J1 section "KF128L-3.5-8P screw terminal" and costed the terminal at
  $0.60; ARCHITECTURE.md topology still said "J1 terminal 1..8". Both now
  reference the v1.1 RJ45 jack / ADR-0004 (net map itself was never stale —
  contact n = terminal n by design).

## 6. Findings table

Finalization pass (Opus, 2026-07-19): the checkpointed draft above was
independently re-verified end-to-end from the live artifacts — none of its
load-bearing numbers were taken on trust. Re-confirmed today: git_sha
543e376 exists and `04_kicad/crow_array_pod.kicad_pcb` at HEAD == at 543e376
(sha256 09a1f47b…); v1.1 MANIFEST sha256 table 6/6 re-hashed match; gerbers/
bom/cpl byte-identical release↔06_build; fresh `kicad-cli pcb drc
--severity-all --refill-zones --schematic-parity` = **0 / 0 / 0** and ERC =
0 from that exact board; `policy_audit.py` FULL = **18 PASS / 6 HUMAN / 2 N-A
/ 0 FAIL**; the J1 interop map extracted pin-for-pin from BOTH boards' live
artifacts (pod `.kicad_pcb` pads vs central `generate_schematic.py` rj_nets)
— straight-through T568B 1:1, SH = pod SHIELD(float) / central GND
(single-point ground) CONFIRMED; F2's DNP mechanism confirmed at the board
(D3/L1/R15 attrs all empty) and exporter (`"DNP" in val`, line 121); S5
op-amp math re-derived against BOM parts (R6=10k/R7=20k→1.50, R8=R9=20k→−1,
VMID 2.47 V, R3=100k/C3=1u→1.6 Hz HPF, R6∥R7=6.67k); SUPERSEDED chain
v1.0→v1.1 closed with reason, v1.0 git_sha 17ceffe + sha table verify; F3
doc fixes (DETAIL_DESIGN/ARCHITECTURE RJ45) confirmed already landed and
committed. Pin-review count clarified: THREE fresh-context PASS reviews
(J1/BZ1/U1) + D1 whose pin-MAPPING/winding/nets are PASS but whose PLACEMENT
verdict is FAIL, dispositioned ACCEPTED in writing per ADR-0004(b2)
(clamp-first topology; closest legal position east of the THT jack body).
All findings below stand as written.

| # | Sev | Finding | Falsifiable evidence | Remediation | New release? |
|---|---|---|---|---|---|
| F1 | **MAJOR** | Canon M3 promotion is stale IN SUBSTANCE: the promoted chain `03_src/route/r3.kicad_pcb` (302 segments / 35 vias, committed cf393af) is NOT the chain that produced the shipped copper — the board's 287 segments match `06_build/route/r3.kicad_pcb` (273 seg / 38 vias; 265/273 shared, rest = stitch/fill) and only 36 match the promoted file. Reproducibility survives ONLY because the 06_build copy happens to be git-tracked (WIP checkpoint dfb0950) and rebuild_all.sh prefers an existing 06_build copy; a `git clean` of the canonically-disposable 06_build would silently rebuild DIFFERENT copper from the stale promoted file. Additionally the canon M3 letter (chain sha in MANIFEST) is unmet — no MANIFEST records any route-chain sha. | segment-set comparison (this audit): board∩03_src = 36/287, board∩06_build = 265/287; `grep route 07_releases/*/MANIFEST.txt` → empty; rebuild_all.sh line 28 `[ -f 06_build/... ] \|\| cp` | Promote the REAL final chain: copy 06_build/route/r3.kicad_pcb over 03_src/route/r3.kicad_pcb and commit (route-source artifact — deliberately NOT done by this docs-only audit); make rebuild_all.sh prefer 03_src (copy 03_src→06_build unconditionally); record the chain sha in the next MANIFEST | No (fab artifacts unaffected; board+fab sha-verified against the release) |
| F2 | **MAJOR (hardening, no wrong output today)** | The flagged item, graded: D3/L1/R15 DNP is enforced ONLY by the value-string convention (`"DNP" in Value`, export_jlc_package.py:121). Schematic carries `(dnp no)` on all three (D3/L1 `in_bom yes`, R15 `in_bom no`); board footprints carry NO attributes (no DNP, no exclude-from-BOM/POS) — so fab BOM/CPL exclusion rests entirely on the value-string token, independent of the schematic flags. Verified correct today: all three absent from bom.csv AND cpl.csv, pads present in gerbers — but a value rename that drops the magic token (e.g. "0R shield bond") would silently populate a deliberate float; R15 populated = pod-side shield bond = defeats the single-point-ground design (ground loop). The release's own pin review RECORDED this observation — it was never remediated. | pcbnew attrs D3/L1/R15 = [] (this audit); .kicad_sch `(dnp no)(in_bom yes)` at refs D3/L1/R15; export_jlc_package.py:121; observation paragraph in v1.1 verification/pin_review.md | Generator emits `(dnp yes)` + board `FP_EXCLUDE_FROM_BOM`/`FP_EXCLUDE_FROM_POS_FILES` (+ DNP field) for the reserve parts; exporter keys off attributes with the value token kept as backstop; re-verify ERC/parity stay 0 with the flags set. Pipeline change + next spin; sealed release untouched | No |
| F3 | MINOR | Doc drift: DETAIL_DESIGN.md §Cable-interface + cost roll-up and ARCHITECTURE.md topology still described the v1.0 screw terminal | pre-fix texts at DETAIL_DESIGN.md:6,90 and ARCHITECTURE.md:12 | **FIXED this audit** (doc commit) | No |
| F4 | MINOR | Release PDF polish (same class as usb-power-3s F6): pcb_layers/assembly title blocks empty (schematic's is filled); assembly_top F.Fab value texts collide in the U1/R6–R9/C4–C7 cluster — hand-solder aid degraded there. Honestly pre-disclosed in ORDER_README "Known cosmetic issue" | fresh render review §H; ORDER_README | export_pdfs.sh title-block vars + Fab de-collision pass, next release | No (cosmetic) |
| F5 | NOTE | J1 refdes tiny/rotated, crowded against D2's "K"/"FLYBACK" silk group — legible at 300 dpi, could be misread as D2's marking. Already condition 3 of the release's own render review | both render reviews (release + this audit's fresh one, independently) | enlarge/move J1 refdes next rev | No |
| F6 | NOTE | render3d_west.png is an edge-on sliver with near-zero information; the twin edge renders carry the actual height evidence | fresh render review §H | drop or re-angle in export_pdfs.sh | No |

## 7. Bottom line — orderability

**The live release v1.1-2026-07-19 is ORDERABLE AS-IS**, with the
already-documented order-time and arrival actions:

- Fab package: DRC re-verified 0/0/0 TODAY from the exact release board;
  6/6 sha table verifies; STANDARD JLC options only (0.6/0.3 vias
  re-measured on the board — no advanced tier needed); 1.6 mm thickness
  REQUIRED (lid math assumes it).
- BOM/CPL: all 15 coded lines IN STOCK today (≥10×). Order-day mandatories
  (all already in ORDER_README): re-check C22359707 (182 today — thin),
  eyeball U1 pin-1 dot in the JLC preview (adjudicated ROT-DB item),
  D2 cathode band, C1 stripe.
- **First-article lid-close gate (ADR-0004 CONDITIONAL FIT) is a HARD gate
  before the fleet build**: assemble one pod, crimped plug in, close the
  lid fully. Nominal +0.24 mm over the jack body; EMI tabs compress by
  design; fallback = trim tabs or RJHSE-L384 (verify holes first). This is
  a fleet-build gate, not an order blocker — correctly sequenced in the
  commission's own prototype-first plan.
- The interop-critical J1 was re-derived clean today end-to-end: no mirror,
  face WEST, pin-for-pin match to the central sealed map over
  straight-through T568B, single-point shield ground preserved.
- F1 (stale route-chain promotion) and F2 (DNP by value-string only) are
  repo-hygiene/hardening debts — neither affects the sealed, sha-verified
  fab artifacts.

Audit changes committed (docs + regenerated audit outputs only — no
schematic/board/fab/release artifacts touched): DETAIL_DESIGN + ARCHITECTURE
v1.1 drift fixes, refreshed policy_drc/policy_erc.json, this report.
