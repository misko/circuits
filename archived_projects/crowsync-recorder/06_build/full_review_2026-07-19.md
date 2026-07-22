# crowsync-recorder — full independent review + audit (2026-07-19)

Fresh-eyes audit of the released project against the CURRENT canon
(`design-policies.md` incl. S-DSL, I10b, R-THERM, P-SILK-FN, small-via/fab
lessons), following the usb-power-3s audit protocol. Live release under
audit: **07_releases/v1.2-2026-07-17** (SUPERSEDED chain v1.0 → v1.1 → v1.2
verified closed; v1.2 has no SUPERSEDED.md). Policy: adopted-forward —
releases predating a policy are graded honestly, gaps tracked, sealed
artifacts untouched. MANIFEST records the order as placed 2026-07-17.

Everything below was re-measured on 2026-07-19 (fresh ERC + DRC + parity,
fresh policy_audit FULL, fresh project audit, fresh stock check,
fresh-context pin reviews, fresh renders + fresh-agent render review) —
nothing is copied forward from the release's own verification bundle
without re-verification.

## 1. Graded scoreboard (every canon ID)

| ID | Grade | Evidence (re-measured 2026-07-19) |
|---|---|---|
| S1 / S-ERC | PASS | fresh `kicad-cli sch erc --severity-all`: 0 errors, 0 warnings (no baseline needed — v1.1 eliminated the 51 off-grid warnings) |
| S2 / S-NET | PASS | 35 routed nets, all deliberately named; only sanctioned `unconnected-(…)` autonames on NC pins |
| S3 / S-VER + pin review | PASS | 8/8 part.yaml `verified:` cite figure+page; THREE fresh-context re-derivations run today (§3): U1 PCM2900C, U3 TPS7A2033, D1/D2 USBLC6 — no mirror, no swapped pin; U1's two QUESTIONs resolved from the netlist (§3); **zero Q9-class doc errors found** (part.yaml matched the datasheet figures pin-for-pin on all three) |
| S4 / S-NC | PASS | all floats carry generator-emitted no_connect flags; ERC pin_not_connected = 0; sanctioned floats (U1 5/6/7/15/16/25, U3.4, J1 A8/B8) each datasheet-verified today |
| S5 | PASS | derivations re-computed exactly: preamp gain 1+3.01k/1k = 4.01, FS at 104 dB SPL (63 mV/Pa × 3.17 Pa = 200 mVrms × 4 ≈ 0.8 Vrms = codec FS); PPS divider 3.3×10k/32.1k = 1.028 V; crystal caps 2×(20−3) = 34 ≈ 33 pF; R7 drop 60 mA×2.2 Ω = 0.13 V; LED currents 0.5/1.0 mA; 70 mA USB budget — all match DETAIL_DESIGN.md and BOM values |
| S6 | **FAIL** (finding F1) | fresh-agent render review: ~10–13 drawn wire segments, all short row-local bridges; the story-critical paths are label-jumped (J1→D1→R1/R2→codec USB entry, preamp feedback network R10/R11/R12/C20, all inter-block links); reviewer "cannot follow the audio or power path visually — full mental re-netting required". Canon permits label-blob only for pullups/decouplers/bulk. The v1.1 release review graded this "READABLE for story paths" — fresh eyes disagree; no S6 waiver exists |
| S7 | PASS (adequate) | decouplers drawn inside their IC's section with purpose captions ("10u VCCCI", "1u VCCP2I"…), no detached cap farm; adjacency is by grouping+caption, not pin-wired — same debt class as S6 |
| S-DSL | PASS | schematic compiled by schwriter2 to native .kicad_sch; every gate (ERC/parity/S-OCCL) runs on the artifacts |
| S-OCCL | PASS | fresh policy_audit: 0 text occlusions (note: several net labels have the wire drawn through the glyphs — legible, logged under F1 remediation) |
| P1 / P-CRT | PASS | fresh full-severity DRC: 0 courtyard findings |
| P2 / P-POL | PASS | machine check present AND independently re-derived this audit (§4): D3/D4 LED pad1(cathode)=GND ✓, J1/J2/J3 keyed-connector pin-nets ✓; no electrolytics on this board; silk pin-1 triangles confirmed by the fresh render reviewer for U1/U2/U3/D1/D2 (LED cathode NOT marked on silk → folded into F2) |
| P3 / P-KEEP | PASS | fresh audit_board.py: PASS, 0 fails 0 warns, 51 footprints (mate directions, edge distances, screw keepouts) |
| P4 / P-SILK-REF | WAIVED-valid | re-measured two ways: policy_audit counts 51 refdes not on silk; fresh render reviewer independently confirms zero silk characters, refdes on F.Fab only — exactly the waiver's claim; policy adopted 2026-07-17 after v1.0; fab sealed; next-spin remediation named |
| I10b (refdes occlusion) | N-A | no refdes on silk to occlude (subsumed by the P4 waiver) |
| P5 / P-SILK-FN | WAIVED-valid | re-measured: zero functional silk near J1/J2/J3 — matches waiver; render reviewer notes the two identical JST-GH connectors (MIC vs PPS) are physically indistinguishable on the bare board — MIC/PPS silk words top of the next-spin list; functions live in ORDER_README + assembly PDF |
| P6 / P-PLANE | PASS | In1 carries only the GND plane (0 tracks); GND additionally poured F.Cu/B.Cu |
| R1 / R-RULES | WAIVED-valid | re-measured: ALL route inputs r0/r0a/r0b/r1–r4 .kicad_pro show classes=['Default']; live 04_kicad project has PWR(0.6)/USB(0.3) netclasses + .kicad_dru floors (PWR 0.30, USB 0.15) emitted by generate_rules.py; canon R1 adopted post-release; waiver expires at the next routing campaign |
| R2 / R-POUR | WAIVED-valid (evidence corrected) | re-measured on the board: MIC_BIAS_F and VBUS_PCM trunks are 0.5 mm (waiver said "0.6 mm" — the netclass width, not the routed width; text corrected this audit, finding F3). At 70 mA total budget 0.5 mm still carries >20× IPC-2152 margin; GND poured on 3 layers, In2 pours cover VBUS_5V and 3V3A |
| R3 / R-PLANE | N-A | no plane_regions configured; USB pair rides the unbroken In1 plane (P6 PASS); no sensitive-region gate declared — acceptable |
| R4 | PASS | finest pitch SSOP-28 0.65 mm escaped with 0.45/0.2 vias (ADVANCED tier), thin-wave USB-column fanout documented in PROGRESS; DRC 0/0/0 |
| R5 / R-LEN | N-A | no timing-critical nets declared (USB full-speed 12 Mb/s pair is short and paired; no length gate needed at this speed) |
| R6 / R-THERM | PASS | fresh check: all pads ≥4 mm² on power nets have ≥2 nearby same-net vias |
| R7 / R-DRC | PASS | FRESH `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity` today: 0 violations / 0 unconnected / 0 parity |
| M1 | PASS | independent-reference battery demonstrably ran: JLC twin (all 27 codes fitted; 2 PAD-GEOM adjudicated against manufacturer drawings), release-time fresh pin review (9 parts), and THIS audit re-ran pin reviews + render review from outside the project's assumptions |
| M2 | PASS | canon IDs machine-enforced via policy_audit.py; project audit_board.py present and passing |
| M3 / M-REPRO | PASS (one gap → F4) | all rebuild inputs git-tracked; promoted chain 03_src/route/r3.kicad_pcb sha 5b4c8272… byte-identical to the 06_build final wave output; GAP: no MANIFEST records the chain-file sha (canon M3 letter — same class as usb-power-3s F5) |
| M4 / M-WAIV | PASS (two evidence defects → F2, F3) | all 4 waivers + 3 adjudications parse and carry measurements; 3 of 4 waivers re-verified exactly true on current artifacts; R-POUR's number was imprecise (fixed) and the C2297 NO-CAD adjudication's evidence is STALE — EasyEDA now HAS the LED CAD (twin fit=0.11 mm, bodies render in twin_top.png), contradicting "render as empty space" in the sealed ORDER_READMEs (stale-evidence note added this audit) |
| M5 / M-REL | PASS | v1.2: full sha256 table verifies 6/6; git_sha 282a238 exists, tree board sha c764ee86 == release claim byte-for-byte; fresh DRC from that exact board = 0/0/0; fab (zip/bom/cpl) byte-identical across v1.0/v1.1/v1.2 as claimed; CHANGELOG names every release dir; SUPERSEDED chain closed; v1.0 (71f35c4) and v1.1 (f12bda1) git_shas exist; tag crowsync-v1.0 exists; BRIEF prompt_sha256 re-verifies (c0a5c91c…) |
| M6 | PASS-with-note (F2) | authoritative-source discipline honored (PAD-GEOM adjudications cite the GCT drawing and TI D0008A land pattern; rotation DB kept as the empirical layer over twin fit angles per canon). Gap: 9 refs carry twin ROT-DB-SUGGEST fit-vs-DB disagreements; ORDER_README's preview checklist covers ALL of them with expected physical orientations (unlike the usb-power-3s F1 omission) but NO record exists that the order-time preview check was executed for the 2026-07-17 order |

Fresh policy_audit.py summary (FULL mode, 2026-07-19): **zero FAIL** —
14 PASS, 4 WAIVED (evidence re-verified; 2 corrected this audit), 6 HUMAN
(graded above), 2 N-A. Fresh project audit_board.py: PASS 0/0. Fresh stock
check TODAY: all 27 coded lines in stock, 0 uncoded (thinnest: SM03B-GHS-TB
C514175 = 62, PCM2900CDBR C180425 = 286 — both above min 15; approved
SM03B alternate C54582898 documented in ORDER_README).

## 2. Release integrity (M-REL detail)

- v1.2 MANIFEST sha256: all 6 files re-hashed, all match.
- `git_sha 282a238` exists; `04_kicad/crowsync_recorder.kicad_pcb` at
  282a238 == HEAD == release claim (sha256 c764ee86…). Fresh DRC with
  `--severity-all --refill-zones --schematic-parity` from that board:
  0/0/0. Fresh ERC: 0 errors, 0 warnings.
- Fab byte-identity claim verified: gerbers.zip, bom.csv, cpl.csv
  sha-identical across v1.0, v1.1, v1.2 (both supersessions were
  schematic-PDF-only, exactly as their SUPERSEDED.md files state).
- CHANGELOG entry per release; SUPERSEDED chain closed; tag crowsync-v1.0
  exists; BRIEF prompt sha256 re-computed and verified.
- 06_build twin_report.csv is byte-identical to the release's copy — the
  released twin evidence is the current evidence.

## 3. Fresh-context pin reviews (S3 bar: derived from datasheet FIGURES first)

Three independent fresh agents, conclusion-free dossiers (pin_audit.py) +
datasheet PDFs only; explicit Q9-class hunt (part.yaml doc-error vs
datasheet, 3 instances fleet-wide before this audit — none added here):

| Part group | Verdict | Key derivation |
|---|---|---|
| U1 PCM2900CDBR (SSOP-28) | **QUESTION → resolved PASS** | SBFS039 p6 pin-assignment figure: pin 1 top-left, CCW, 14/side — dossier matches, NOT mirrored. All 28 pins verified: SEL0/1→VDDI ("must be set high"), TEST0→GND, TEST1 open, HID0-2 float (internal pulldowns), VCC*I/VDDI = internal-regulator outputs decoupled-only (fig 38 bus-powered — board correctly does NOT drive VCCCI), VOUT L/R unused-open, 5 grounds→GND. Agent's two QUESTIONs closed by netlist re-check this audit: XTI/XTO = {Y1.1/Y1.3 + C5/C6 + R6 1M} exactly per fig 38 ✓; D+/D- = U1→R1/R2 22R→DP_C/DM_C→D1 ESD→J1, R3 1k5 pullup chip-side D+→VDDI ✓. part.yaml: all 28 names + constraint annotations match the datasheet — no doc errors |
| U3 TPS7A2033PDBVR (SOT-23-5) | **PASS** | SBVS338H p4 fig 4-4 DBV column (agent explicitly avoided the X2SON column trap): 1=IN→VBUS_5V, 2=GND, 3=EN→VBUS_5V (always-on, internal 500k pulldown needs the tie), 4=N/C ("no internal electrical connection" — float sanctioned), 5=OUT→3V3A. CCW, zero rotation, no mirror. part.yaml matches — no doc errors |
| D1/D2 USBLC6-2SC6 (SOT-23-6, 2 instances) | **PASS / PASS** | UMW datasheet p1 §4 figure: pass-through pairs are 1↔6 (I/O1) and 3↔4 (I/O2), 2=GND, 5=VBUS. D1: 1/6=DP_C, 3/4=DM_C, 5=VBUS_5V ✓. D2: 1/6=MIC, 3/4=PPS, 5=3V3A — rail-referenced clamp judged electrically sound (clamps 3.3V-domain harness lines to 3V3A+Vf; internal 5V zener). 90° rotation, no mirror; pairwise symmetry holds across instances. part.yaml matches — no doc errors. (The audit orchestrator's briefing mis-stated the pairs as 1/3+4/6; the fresh agent independently derived the correct 1↔6/3↔4 from the figure — independence working as designed) |

## 4. Independent polarized-part re-derivation (Q9-class hunt)

Board pad-1 nets vs the FOOTPRINT's own convention (not part.yaml):

| Ref | Footprint (pad1 meaning) | pad1 net | Verdict |
|---|---|---|---|
| D3/D4 LED KT-0805G | LED_0805 (pad1=cathode) | GND both | ✓ (anodes fed via R17 1k from SSPND / R18 2k2 from VBUS_5V) |
| J1 USB4105-GF-A | keyed USB-C | A4/B4=VBUS_5V, A1/B1=GND, CC1/CC2 separate 5k1 Rd | ✓ |
| J2 SM03B (keyed) | pin1 | MIC (pins 2/3 GND) | ✓ matches D2 I/O1 pair + harness plan |
| J3 SM02B (keyed) | pin1 | PPS (pin 2 GND) | ✓ |

No self-consistent-wrong-together pair found. No electrolytics on this
board. Wide-vs-narrow SOIC trap: U2 is the NARROW SOIC-8 3.9 mm — correct
for TLV9062IDR "D"; the twin's PAD-GEOM (4.95 vs 5.42 mm) is the
adjudicated IPC-vs-TI-example land-pattern difference, non-mirrored fit
0.24 mm. Wrong-pitch trap: twin pairwise pad-distance gate ran on all 27
codes; U1 SSOP-28 fit 0.04 mm. JLC-rotation authority: DB rows
(^SSOP-/270, ^SOIC-/270, ^SOT-23/-90) kept over twin fit angles per canon
M6; all 9 fit-vs-DB refs are in the ORDER_README preview checklist (see F2).

## 5. History coherence

- ARCHITECTURE.md power tree and signal chains == shipped netlist,
  node-spot-verified today (USB entry J1→D1→22R→U1 with chip-side 1k5;
  mic chain J2→D2/R9→C19→U2A(VCOM_BUF ref)→R13/C21→C9→VINL; PPS
  J3→D2/R14→22k/10k→C10→VINR; VCOM→U2B buffer; bias 3V3A→FB1→2k2).
- DETAIL_DESIGN math re-derives (S5 row). BRIEF criteria G1–G8 met;
  A5/A6 assumptions formally accepted by the user 2026-07-17.
- ADR-0001…0005 all still describe the board (2× USBLC6 with different
  rail references is ADR-0001 by design and flagged "do not fix" in
  ORDER_README).
- ERRATA.md correctly quarantines the v1.0 render-review misstatement.
- Mild drift (F5): BRIEF G-table evidence pointers cite v1.0 (fab-identical
  ancestor of live v1.2) — accurate-at-the-time, chain discoverable via
  CHANGELOG; no current_release field to go stale.

## 6. Findings table

| # | Sev | Finding | Falsifiable evidence | Remediation | New release? |
|---|---|---|---|---|---|
| F1 | **MAJOR** | S6 fails fresh-eyes grading on the live release with NO waiver: story-critical paths (USB entry J1→D1→R1/R2→codec; preamp feedback R10/R11/R12/C20; all inter-block links) are label-jumped; only ~13 short row-local wires exist. The v1.1/v1.2 render reviews graded S6 "READABLE for story paths" — an honest-grading gap (the drawn segments are real but don't cover the canon's required chains). Legibility nits ride along: wires drawn through label glyphs (MIC_BIAS_F, VINL_F, PPS_ATT, XTO, RG_X), ~60% dead sheet space | fresh render review 2026-07-19 (schematic.png from the release .kicad_sch); canon S6 text; 07_releases/v1.1…/verification/render_review.md "READABLE" claim + its own "known label-only spots" list | next schematic-only release: schwriter2 draws the USB-entry chain, preamp feedback loop, and inter-block links (or an evidence-backed S6 waiver citing the documented T3 engine limits); fix label-through-wire collisions | Schematic-only release (fab byte-identical, like v1.1/v1.2); NOT an orderability blocker |
| F2 | MINOR | LED polarity disposition chain is the board's weakest link: twin POLARITY-CHECK rows for D3/D4 undispositioned in twin_adjudications.yaml; the C2297 NO-CAD adjudication + ORDER_README claim "NO EasyEDA CAD — render as empty space" is STALE (CAD now present: fit=0.11 mm, MODEL-REG-OK, bodies visible in twin_top.png); LEDs have no cathode mark on silk (render review §P2); and no archived record that the order-time JLC-preview rotation/polarity checklist (which correctly lists all 9 ROT-DB-SUGGEST refs incl. D3/D4) was executed for the 2026-07-17 order | 06_build/twin/twin_report.csv D3/D4 rows; twin_top.png (LED bodies render); 03_src/rules/twin_adjudications.yaml (pre-fix); ORDER_README §rotation; verification/ contains no preview record | **Partially fixed this audit** (stale-evidence note added to the adjudication). Remaining: at first-article, BEFORE first power, verify D3/D4 orientation (consequence is benign — a reversed indicator = dark LED, caught by first-power ritual step 3); next spin adds LED cathode silk marks; future orders archive a preview screenshot in verification/ | No |
| F3 | MINOR | R-POUR waiver evidence imprecision: claimed "0.6 mm trunks"; the routed MIC_BIAS_F/VBUS_PCM segments measure 0.5 mm (0.6 is the netclass width, 0.3 the dru floor). Margin conclusion unaffected (>20× at 70 mA) | pcbnew width scan 2026-07-19: both nets all-segments 0.5 mm; 03_src/rules/policy_waivers.yaml (pre-fix) | **FIXED this audit** (waiver text now states measured 0.5 mm); policy_audit re-run, still zero FAIL | No |
| F4 | MINOR | Canon M3 letter unmet: promoted route chain 03_src/route/r3.kicad_pcb is git-tracked and byte-identical to the final wave output (sha 5b4c8272…) but its sha is recorded in NO MANIFEST | grep r3/route 07_releases/*/MANIFEST.txt → empty | Record the chain-file sha in the next release's MANIFEST (sealed releases untouched) | No |
| F5 | NOTE | BRIEF G-table evidence pointers cite v1.0 (live is v1.2; fab byte-identical) — mild staleness, chain discoverable via CHANGELOG | 01_docs/BRIEF.md G1/G7/G8 rows | Point the G rows at the live release next time the BRIEF is touched | No |
| F6 | NOTE | 06_build/route contains an orphan r4.kicad_pcb never referenced by route_waves.sh or rebuild_all.sh (which import r3); promoted r3 verified as the actual final chain | ls 06_build/route; grep r4 03_src/*.sh → empty; sha match r3 build↔promoted | None required (06_build is disposable); delete r4 on next rebuild to avoid confusion | No |

## 7. Bottom line — orderability

**The live release v1.2-2026-07-17 is ORDERABLE AS-IS** (and per its
MANIFEST the order already went out 2026-07-17), with one first-article
action and no blocking findings:

- Fab package: DRC re-verified 0/0/0 TODAY (severity-all, refill,
  schematic parity) from the exact release source; ERC 0/0; sha table
  verifies 6/6; fab byte-identical across the whole v1.0→v1.2 chain;
  ADVANCED small-via option (0.45/0.2) required and documented.
- BOM/CPL: all 27 lines coded and IN STOCK today (SM03B at 62 is the
  thin line; approved alternate documented); zero hand-solder; CPL
  rotations follow the empirically-authoritative DB (canon M6) and every
  fit-vs-DB disagreement is covered by the ORDER_README preview checklist.
- Electrical confidence: three fresh-context pin reviews today (U1, U3,
  D1/D2) all PASS with zero Q9-class doc errors; polarized/keyed parts
  independently re-derived clean; design math re-derives; netlist matches
  the documented architecture node-for-node where spot-checked.
- **First-article (F2)**: verify D3/D4 LED orientation before/at first
  power (dark LED = reversed; non-destructive) — the one polarity check
  no machine gate on this project can close.
- Canon debt for the next spin, none order-blocking: S6 drawn story
  wires (F1, schematic-only release), refdes + functional silk (P4/P5
  waivers, esp. MIC vs PPS words on the twin JST-GH headers), LED
  cathode marks, chain-file sha in MANIFEST (F4).

Audit fixes committed (docs/audit-config only — no schematic/board/fab or
sealed release artifacts touched): R-POUR waiver measured-width correction,
C2297 stale-evidence adjudication note, regenerated 06_build/policy_audit.md,
this report.
