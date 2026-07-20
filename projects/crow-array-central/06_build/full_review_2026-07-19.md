# crow-array-central — full independent review + audit (2026-07-19)

Fresh-eyes audit of the released project against the CURRENT canon
(`design-policies.md`). Live release under audit: **07_releases/v1.0-2026-07-18**
(first and only release — no SUPERSEDED chain expected; ORDER GATED on the
commission's field-test sequence per ORDER_README §1). This is the campaign's
hardest board: 6-layer, 234 parts, XU316-1024 TQ128 (128-pin 0.4mm-pitch QFP
+ EP) + dual PCM1865 + 8 RJ45 audio ports.

Policy: adopted-forward — sealed artifacts (schematic/board/fab/release) were
NOT touched. Everything below was re-measured on 2026-07-19 (fresh ERC/DRC,
fresh policy_audit, fresh stock check, fresh-context pin reviews, fresh render
review, independent zone-fill re-count, pod cross-check) — nothing copied
forward from the release's own verification bundle without re-verification.

## 1. Graded scoreboard (every canon ID)

| ID | Grade | Evidence (re-measured 2026-07-19) |
|---|---|---|
| S1 / S-ERC | PASS | fresh `kicad-cli sch erc --severity-all`: 0 errors, 0 warnings |
| S2 / S-NET | PASS | 151 routed nets all deliberately named; auto-names only on sanctioned NC pins |
| S3 / S-VER + pin review | PASS | 18/18 part.yaml `verified:` cite figure+page; THREE fresh-context re-derivations run today (§3): XU316 U1 (no-mirror), Q9/AO3401A, PCM1865 U2 — all PASS |
| S4 / S-NC | PASS | all floats generator-`no_connect`-flagged; ERC pin_not_connected = 0 |
| S5 | PASS (graded A) | fresh render review: buck FB math in section titles (`VO=0.6(1+68/15)=3.32V`, core `0.6(1+10/20)=0.9V`), crystal CL, ADC coupling recipe — math lives with the design |
| S6 | PASS (graded A−) | 15 numbered/titled sections, power chain genuinely wired (J9→F1→D9→Q9→bucks→LDOs), signal chain P1-8→coupling→dual PCM1865→XU316; only the 128-pin XU316 uses net-label pins (unavoidable) |
| S7 | PASS (graded B) | per-ADC AVDD/DVDD/VREF/LDO decouple in-box under each PCM1865; XU316 decoupling is a dedicated adjacent box tied by rail labels (standard pin-dense compromise) |
| S-OCCL | PASS | fresh policy_audit: 0 text occlusions |
| P1 / P-CRT | PASS | fresh full-severity DRC: 0 courtyard findings |
| P2 / P-POL | PASS | machine check present AND independently eyeballed on the twin (§3): C90 `+` toward 5V, D9/TVS pin-1 dots, RJ45 uniform, USB-C normal — no reversed part |
| P3 / P-KEEP | PASS | mate/edge/screw-keepout (audit I12: RJ45 north / barrel west / USB-C south; M3 3.2mm ring) present + passing |
| P4 / P-SILK-REF | PASS | every refdes on visible F.SilkS incl. the dense ADC cluster, de-collided at full res |
| P5 / P-SILK-FN | PASS | `NOT ETHERNET` banner, PORT 1-8, per-port PTC words, `2A PTC`, TP labels, `xSYS DBG`, `INJ IN`, board ID — comprehensive (D29) |
| P6 / P-PLANE | PASS | In1 carries only the GND plane (0 tracks) |
| R1 / R-RULES | PASS | route-input r0.kicad_pro carries all 8 classes (Default, PWR5, RAIL, ARAIL, PORTPWR, CLK, USB, AUDIO) |
| R2 / R-POUR | WAIVED-valid | D15: power = DRU-floored tracks on 4 signal layers (In2/In3 fragment under the XU316); PWR5 0.5mm floor, worst trunk 1.2A within a 0.5mm 1oz outer's ~1.2-1.4A @10°C; re-verified on the board (5V_P/5V_IN min-width = 0.500mm; §5) |
| R3 / R-PLANE | N-A | no plane_regions configured (power-as-tracks); In1/In4 solid GND under signals |
| R4 | PASS (design review) | escape feasibility resolved empirically: 6L + small-via 0.30/0.15 (ADR-0009) closes the 0.4mm-pitch escape; DRC 0 |
| R5 / R-LEN | N-A | no length-gated timing nets declared (clock spread handled by placement) |
| R6 / R-THERM | WAIVED-valid | the lone flagged pad is U1.129 (XU316 EP); its thermal vias are FOOTPRINT PTH pads — re-verified: **16 PTH thermal vias + center, all net GND** (§6), audit I11 counts them |
| R7 / R-DRC | WAIVED-valid | FRESH `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity` today: **0 violations / 0 parity / exactly 2 `Zone[GND]↔Zone[GND]` unconnected** — the ADR-0010 shape, re-verified §2 |
| M1 | PASS | independent-reference battery demonstrably ran (JLC twin, fresh-agent pin reviews, this audit re-ran all from outside the design) |
| M2 | PASS | canon IDs machine-enforced via policy_audit.py; project audit_board.py present (I11/I12) |
| M3 / M-REPRO | PASS (one letter-gap → F3) | all rebuild inputs git-tracked incl. promoted chain 03_src/route/final.kicad_pcb; MANIFEST NAMES it + pins to git_sha but records no explicit sha256 line |
| M4 / M-WAIV | PASS | 3 policy waivers + 19 twin adjudications, all carry measurement/evidence; every waiver RE-VERIFIED true on current artifacts today |
| M5 / M-REL | PASS (one letter-gap → F2) | v1.0 sha256 table verifies file-by-file (6/6 re-hashed, all match); git_sha 7f077e1 exists; board+sch byte-unchanged since that commit; DRC regenerated from that board = 0/0/0+2; GAP: no CHANGELOG.md (FIXED this audit) |
| M6 | PASS | authoritative-source discipline honored: twin PAD-GEOM/MISMATCH each cite the datasheet land pattern / fetched CAD identity; ROT-DB-SUGGESTs deferred to JLC order preview (empirical layer), not blind-applied |

Fresh policy_audit.py (FULL mode, 2026-07-19): **zero FAIL** — 15 PASS,
3 WAIVED (all evidence-verified), 6 HUMAN (graded above), 2 N-A. Reproduces
the release's policy_audit.md byte-for-content (only timestamps differ).

## 2. Release integrity + ADR-0010 re-verification (M-REL / R-DRC detail)

- **sha256 table**: all 6 release files (gerbers.zip, bom.csv, cpl.csv, 3
  PDFs) re-hashed 2026-07-19 — every hash matches the MANIFEST byte-for-byte.
- **git_sha 7f077e1** exists (release seal commit, 2026-07-18 23:49). The
  working-tree `04_kicad/crow_array_central.kicad_pcb` and `.kicad_sch` are
  **byte-identical** to that commit (git diff empty) — the audited board IS
  the released source. git_dirty:false consistent.
- **Fresh DRC from the released board**: `kicad-cli pcb drc --severity-all
  --refill-zones --schematic-parity` → **0 violations, 2 unconnected, 0
  parity** (exit 5 = the 2 waived items). Both unconnected items inspected
  in JSON: BOTH are `Zone [GND] on In1.Cu, priority 0 ↔ Zone [GND] on F.Cu,
  priority 0` — the exact ADR-0010 shape. **Zero pad/track/via unconnected**,
  so no component GND pad is stranded (the "zero electrical impact" claim
  holds — if a sliver orphaned a pad, DRC would emit a pad-level ratsnest
  item, and none appears).
- **ADR-0010 irreducibility, re-run myself**: `island_removal_mode 0`
  (ALWAYS) is present on all four GND pours (F/B/In1/In4). I re-filled the
  zones with `pcbnew.ZONE_FILLER` independently: the F.Cu GND pour genuinely
  fragments into **103 islands, 17 of them sub-2mm²** (0.15–1.3mm²) in the
  dense escape pockets, while In1/In4 stay single solid planes and B.Cu has
  2 — the sliver-formation mechanism is real and reproduces. The headless CLI
  still reports exactly 2 Zone-Zone items with island-removal set, confirming
  the core "headless fill won't clear them" claim. Verdict: **waiver valid**,
  electrically and manufacturably inert.
- **Stock re-verified TODAY** (§4): 43/45 coded lines in stock ≥25; the XU316
  consign line is the documented stock-0 exception; ONE new drift (F1).

## 3. Fresh-context pin reviews (S3 bar: derived from datasheet FIGURES first)

Three independent fresh agents, conclusion-free dossiers (pad geometry + nets
only), datasheet-figure-first. The checkpointed dossiers
(06_build/pin_audit_fresh_2026-07-19/) were used and independently re-judged.

| Part | Verdict | Key derivation |
|---|---|---|
| **U1 XU316** (TQFP-128 + EP, 129 pins) | **PASS — NO MIRROR** | winding derived from datasheet **Fig 22 p41**: pin 1 top-left, CCW top view (down the W edge 1-32, S 33-64, E 65-96, N 97-128). Dossier shoelace = CCW, matches edge-by-edge AND direction-within-edge. All 128 pins + EP checked vs Table 4 pp81-84: every function/net sane (VDD=0V9, VDDIOx=3V3, VDDIOB18/USB_VDD18=1V8, USB_VDD33=3V3, PLL_AVDD filtered, QSPI set, USB_DM/DP, XIN/XOUT, JTAG, I2C X0D35/36, I2S/TDM, EP pin129=VSS=GND). LV_L/T/R_N selects agree with their I/O-bank voltages. |
| **Q9 AO3401A** (SOT-23 reverse-FET) | **PASS — board correct** | AO3401A datasheet p1: pin1=Gate, pin2=Source, pin3=Drain; P-ch body diode anode=DRAIN/cathode=SOURCE. Independently derived: high-side reverse guard needs DRAIN=input, SOURCE=load. Board: pad1=GATE9, pad2(S)=5V (load), pad3(D)=5V_P (input) → matches. Vgs≈−5V at turn-on enhances; reverse input reverse-biases the body diode → blocks. The ADR-0007/D19 polarity saga is settled: board right, part.yaml doc-error fixed. |
| **U2 PCM1865** (TSSOP-30) | **PASS — NO MIRROR** | SLAS831D **p10** figure: pin 1 top-left, CCW; dossier coords trace the same. 30/30 pins sane: AVDD=3V3A, DVDD/IOVDD=3V3, AGND/DGND=GND, VREF_A/LDO_A decoupled, SCKI=MCLK_A, LRCK/BCK/DOUT=DATA1, I2C SDA(23)/SCL(24), MS/AD(25)=GND (addr 0x4A), MD0=GND (I2C mode), XI=GND/XO=NC (external-clocked via SCKI), MICBIAS unused. |

Non-blocking QUESTIONS from the U1 reviewer (both intentional, do not block):
(a) MIPI unused analog supplies VDD18/VDD09 tied to GND rather than left
unpowered — standard "power-off the block", worth a one-line confirm against
the XMOS HW design guide; (b) MCLK_SRC fans out to both X0D11(7) and
X1D11(23) — deliberate dual-tile MCLK feed.

## 4. Stock (order-day gate) — one new drift

Fresh `jlc_stock_check.py bom.csv --min-stock 25` (2026-07-19): 45 coded
lines, 6 uncoded (the documented hand-solder set: RJ45 J1-J6, barrel J9,
KF128 J11, USB-C J12, headers J10/J13/J14 — all in MANIFEST not_assembled).

- **U1 XU316 C6938291: stock 0** — the KNOWN consign line, documented
  (ORDER_README §3). Expected.
- **F1 (NEW): R-line C25744 (10k 0402, BASIC) dropped to stock 0 today**
  (was ≥25 on 2026-07-18; endpoint healthy — the 100k basic sanity part
  returns 217k). This basic 10k line (5 refs) is NOT in the MANIFEST
  stock_note's shallow-line watch list. Trivially substitutable (C60489/
  C60490 = 1.6M/7.3M stock 10k 0402). Order-day re-verify + swap needed.
- Shallow lines flagged in MANIFEST re-confirmed present: XC6227 C6035451
  (268), AP61102 C5224055 (461), 100u C48970904 — all > 25.

## 5. History coherence

- **D25 power-neck ampacity (re-verified)**: the board carries **36
  `pwr_neck` named rule areas + 1 `xu316_taps`**; `.kicad_dru` scopes
  PWR5/RAIL to a 0.15mm floor inside those areas, 0.50/0.40 outside. On the
  board: 5V trunk necks to **0.200mm** (matches D25's "neck to 0.20mm"),
  5V_P/5V_IN stay 0.500mm, XU316 per-pin RAIL taps 0.15mm. Ampacity math is
  conservative and correct: a 0.20mm 1oz external trace carries ≈0.74A at
  10°C rise (IPC-2221 k=0.048; IPC-2152 external ≥ that), so the 5V per-buck
  VIN branch (≤0.45A) sees ≈3°C and the 3V3 trunk (≤0.40A) ≈4°C rise — the
  exemptions live on the board as rule areas with margin math (canon-compliant).
- **D28 RJ45 map = pod-interop authority (re-verified against the sealed
  pod)**: extracted the pod board at git **17ceffe** and read J1 directly —
  pod J1: 1=AUDIO_P, 2=AUDIO_N, 3=BEEP_5V, 4=5V, 5=GND, 6=BEEP_RET, 7=5V,
  8=GND. Central board J1: 1=AUD_P1, 2=AUD_N1, 3=BEEP_5V1, 4=5V_AUD1, 5=GND,
  6=BEEP_RET1, 7=5V_AUD1, 8=GND. **Contact-for-contact match on all 8 pins**
  (4=5V, 5=GND, 7=5V, 8=GND). The pod CHANGELOG itself cites "central D28" as
  the map authority — coherent both directions. Shield: central SH→GND
  single-point; pod SHIELD net with DNP R15 bond — deliberate star.
- ARCHITECTURE/BRIEF D-register (D3-D29) all still describe the shipped
  board; ADR-0007/8/9/10 re-read and each matches the board.

## 6. Cross-portfolio traps

- **Wrong-pitch footprints**: the twin's 21 PAD-GEOM + 2 PAD-MISMATCH
  findings were audited against their adjudications. All PAD-GEOM are
  small house-style pad offsets (0.16–0.58mm) on **correctly-classed**
  footprints, each adjudicated citing the datasheet recommended land: the
  1812 PTCs F1/F11-F28 on Fuse_1812_4532Metric (part 4.37-4.5mm 1812 body,
  MODEL-REG-OK 0.00mm), Sunlord MWSA0402S inductors (catalog land verified),
  SOT-23 FETs, SMB TVS, SOT-23-5 LDO, USB-C (vendored). The 2 PAD-MISMATCH
  are pad-NAME-duplication artifacts (U1's 17 pads numbered "129" = EP + 16
  vias; U13 XC6227 SOT-89-5 tab+lead both "2"), package identity confirmed
  from the fetched CAD name in each case. **No wrong-pitch footprint.**
- **TQ128 EP 16-via thermal grid**: re-counted on the board — U1 pin129 =
  17 pads (1 center 4.7×4.7 + 16 PTH thermal vias), **all net GND**, into
  the In1/In4 planes. Present as designed (D-note / R-THERM waiver).
- **Neck exemptions vs IPC-2152**: verified §5 — every sub-floor run lives
  inside a named `pwr_neck`/`xu316_taps` rule area with its own DRU floor and
  documented margin math; no undersized copper carries trunk current.

## 7. Findings table

| # | Sev | Finding | Falsifiable evidence | Remediation | New release? |
|---|---|---|---|---|---|
| F1 | **MINOR** | Basic 10k 0402 line **C25744 dropped to JLC stock 0 on 2026-07-19** (was ≥25 on 2026-07-18); not in the MANIFEST stock_note watch list. 5 refs. Trivially substitutable. | fresh `jlc_stock_check.py` 2026-07-19: `LOW_STOCK(0) C25744 x5 10k base`; direct re-query confirms 0 (sanity part C25741 returns 217774) | Order-day: re-verify + substitute (e.g. C60489/C60490, millions in stock). Order is field-test-gated so not blocking now; add C25744 to the ORDER_README watch list at the next release. | No |
| F2 | MINOR | **No CHANGELOG.md** — canon M5 letter ("CHANGELOG entry names the dir"); 7/12 fleet projects incl. the sibling pod have one; central relied on the BRIEF D-register only. | `find projects/crow-array-central -iname CHANGELOG*` → empty (pre-fix) | **FIXED this audit**: created 01_docs/CHANGELOG.md naming v1.0-2026-07-18 with gate summary | No |
| F3 | MINOR | Canon M3 letter: promoted route chain `03_src/route/final.kicad_pcb` is git-tracked AND named in the MANIFEST tools line ("committed at git_sha"), but its sha256 is not in the MANIFEST hash table (same class as usb-power-3s F5; softer here — file is git-pinned). | `grep final 07_releases/*/MANIFEST.txt` → only the tools line, no sha256 row | Record the chain-file sha256 in the next release's MANIFEST (sealed release untouched) | No |
| F4 | NOTE | U1 pin review QUESTIONS (both intentional): MIPI unused supplies tied to GND (confirm vs XMOS HW design guide) + MCLK_SRC dual-tile fan-out (X0D11+X1D11). | §3; U1 dossier pins 24/27 = GND, pins 7/23 = MCLK_SRC | Optional one-line confirmation note in DETAIL_DESIGN at next spin; no board change | No |
| F5 | NOTE | Release PDF cosmetics: empty title/rev blocks ("dev"), layer sheets stamped A4 while schematic is A0, F.Fab value-text pile-ups in dense clusters. Dispositioned (pod-v1.0 precedent; MANIFEST git_sha is provenance; hand-solder parts sit in readable zones). | 07_releases/v1.0…/pdf/*; render review §findings | Generator TODO (title-block vars, F.Fab de-collision) — next release | No (cosmetic) |

## 8. Bottom line — orderability

**The design is READY and the release is sealed and internally consistent;
the ORDER remains GATED** — not by any defect found here, but by the
commission's own risk sequence (ORDER_README §1: pod field tests + USB
firmware proven on the XMOS eval board BEFORE this custom central board is
fabbed). No CRITICAL or MAJOR finding; nothing blocks a future order beyond
that gate.

When the field-test gate clears, order with:
- **Fab**: DRC re-verified 0 violations / 0 parity / 2 waived Zone-Zone
  GND slivers TODAY from the exact release board; sha256 table verifies;
  6-layer + **SMALL-VIA (advanced) option 0.30/0.15 REQUIRED** (ADR-0009).
- **XU316 (U1) consign**: C6938291 is JLC stock 0 by design — consign /
  global-source, or Digi-Key/XMOS direct + hand-reflow (TQFP-128 0.4mm + EP).
- **Order-day stock**: re-run verify mode the same day; **F1: substitute
  C25744 (10k) — now stock 0**; re-check XC6227/AP61102/100u shallow lines.
- **CPL rotation preview**: the ROT-DB-SUGGEST parts (U2/U3 TSSOP-30,
  U4 SOIC-8, U5 VSSOP-8, U10/U11 SOT-563, U12 SOT-23-5, D10 USON-10, Q1-Q9
  SOT-23) need the mandatory 3D-preview pin-1 check (ORDER_README §2).
- **Cost EXCEEDS the $79-90 target** (~$150-220/board at qty5: 6L + small-via
  + XU316 consign) — documented, correctness-first per the brief.

All 3 waivers remain evidence-valid (R-DRC re-run, R-POUR width re-measured,
R-THERM 16 EP vias re-counted); all 19 twin adjudications carry evidence;
XU316/Q9/PCM1865 pin geometry independently re-derived clean (no mirror, no
polarity flip); the RJ45 map matches the sealed pod contact-for-contact.

Audit fixes committed (docs only — no schematic/board/fab/sealed artifacts
touched): CHANGELOG.md (F2), this report.
