# ble-bus-bar — full independent review + audit (2026-07-19)

Fresh-eyes audit of the LIVE release against the CURRENT canon
(`design-policies.md`, incl. S-DSL / P-POL / R-POUR / R-PLANE / M-REL).
Live release under audit: **07_releases/v1.1-2026-07-19** (git_sha
`6d4319b`, "v1.0 + durable anchoring ONLY"). SUPERSEDED chain: v1.0 →
v1.1 verified closed (v1.0/SUPERSEDED.md points to v1.1; v1.1 has no
SUPERSEDED.md = it is live). Policy: adopted-forward — releases predating
a policy are graded honestly, gaps tracked, sealed artifacts untouched.

Everything below was re-measured on 2026-07-19 (fresh ERC + DRC, fresh
policy_audit, board-geometry probes, three fresh-context pin reviews)
— nothing copied forward from the release bundle without re-verification.
Provenance note: the completed fresh-context RENDER REVIEW (independent
agent, this cycle) is incorporated below where marked [render review]. A
prior Fable agent's checkpointed doc touches (BRIEF 8→7 holes;
DETAIL_DESIGN VBUS-impedance correction) were verified as legitimate.

## 1. Graded scoreboard (every canon ID)

| ID | Grade | Evidence (re-measured 2026-07-19) |
|---|---|---|
| S1 / S-ERC | PASS | fresh `kicad-cli sch erc --severity-all`: 0 errors, 0 warnings on the released `.kicad_sch` |
| S2 / S-NET | PASS | 53 routed nets, all deliberately named; no `Net-(…)` autonames on copper |
| S3 / S-VER + pin review | PASS | 8/8 part.yaml `verified:` cite figure+page; THREE fresh-context re-derivations run today (§3): INA238, SS310, W25Q64 — no mirror, no swapped pin, all PASS |
| S4 / S-NC | PASS | all floats carry generator-emitted no_connect flags; ERC pin_not_connected = 0 |
| S5 | PASS | design math re-derived: Vout = 0.765·(1+33k/10k) = 3.29 V; UVLO 1.25·(660/100) = 8.25 V; trunk IPC-2221 0.048·30^0.44·2374^0.725 = 60.3 A (1.5×); shunt 30²·0.5 mΩ = 0.45 W; INA FS 15 mV/40.96 mV = 37% — all match DETAIL_DESIGN. [render review]: FB 33k/10k, UVLO, 10R sense, INA 0x40–0x45 all annotated on the schematic |
| S6 | PASS (graded) | [render review]: 12 titled story boxes, ~8 power chains drawn left-to-right. Caveat: inter-element hops via net-label PAIRS not one continuous wire — a disciplined label-chain, not a blob. Acceptable readability; debt visible/tracked |
| S7 | CONCERN (half credit) | [render review]: INA decouplers CB1-6 wired AT the VS pins (good); but buck input caps + ESP32 C7/C8 drawn as detached label→cap→GND rows near-but-not-at-pin. Same debt class as S6; MINOR (F5) |
| S-DSL | PASS | schematic compiled by schwriter2 to native `.kicad_sch`; every gate (ERC/parity/S-OCCL) runs on artifacts |
| S-OCCL | PASS | fresh policy_audit: 0 text occlusions |
| P1 / P-CRT | PASS | fresh full-severity DRC: 0 courtyard findings |
| P2 / P-POL | PASS (machine) / CONCERN (silk glyph) | machine pad-1-net check PASS AND independently re-derived (§3/§4): D7/D11 cathode(pad1)=load-side, D9/D10 correct, INA/flash all correct. [render review] CONCERN: D7-D11 render NO visible cathode-band glyph, LED1/2 no A/K mark. Machine probe: footprints DO carry standard silk cathode marks (3 F.SilkS graphics each) but they render faint/absent. All machine-placed SMD (CPL-driven) + ORDER_README preview cathode-check → LOW risk; MINOR (F6) |
| P3 / P-KEEP | PASS | mate/edge/screw-keepout + antenna checks in audit_board.py; fresh audit PASS. Antenna keepout (50,50)-(61.2,75.3) machine-probed: 0 track endpoints, 0 pads (copper-free both layers) |
| P4 / P-SILK-REF | PASS | all refdes on visible F.SilkS (waiver file covers only small passives next to bodies). [render review]: all refdes legible EXCEPT one clipped "ST" status-LED silk near LED2 (illegible) — MINOR (F7) |
| P5 / P-SILK-FN | PASS | [render review]: "+12-24V IN"/"M5 LUG"/two "+" glyphs; "GND REF"/"NOT LOAD RETURN"; PORT 1-6; "30A MAX" per fuse; UART pinout; "CHECK POLARITY BEFORE FIRST POWER". Every human touch-point marked |
| P6 / P-PLANE | N-A | 2-layer board — return-path continuity graded under R-PLANE |
| R1 / R-RULES | PASS | route-input `r0.kicad_pro` carries classes [Default, TRUNK, PORT, EPWR, RAIL3V3] — rules rode INTO the router |
| R2 / R-POUR | WAIVED-valid | re-measured on the board: TRUNK VBUS poured F.Cu **and** B.Cu (paired, per ADR-0002); all 6 VF*/6 VP* PORT nets poured F.Cu single-layer (B.Cu reserved for GND plane/corridor, by design); EPWR nets [SW,VIN_E,VLDO,VTAP,VUSB] track-carried at exactly the 0.5 mm floor, ≥6× margin on 0.49 A worst case — waiver numbers verified true today |
| R3 / R-PLANE | WAIVED-valid | re-measured: 63.5 mm B.Cu signal within 10 mm of U7 (audit flag; waiver cites a 41.2 mm longest run) = ESP32 fanout UNDER the module body, unavoidable on 2L; the RF-critical antenna zone is copper-free (probed above). Number-precision nit noted (F9) but core claim holds |
| R4 | PASS | escape feasibility proven: 0.5 mm-pitch INA238 MSOP + USB-C 0.3/0.2 mm via weave fanned out, DRC 0/0/0 at JLC 2 oz advanced tier |
| R5 / R-LEN | N-A | no timing-critical nets on this board |
| R6 / R-THERM | N-A | 2-layer: no internal plane to sink into |
| R7 / R-DRC | PASS | FRESH `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity` today: 0 / 0 / 0 — identical to the release's verification/drc.json |
| M1 | PASS | independent-reference battery demonstrably ran: JLC twin (caught the v1.0 U11 narrow-SOIC), fresh-agent pin + render reviews, and THIS audit re-ran all from outside the design's assumptions |
| M2 | PASS | canon IDs machine-enforced via policy_audit.py; project audit_board.py present |
| M3 / M-REPRO | PASS | all rebuild inputs git-tracked incl. promoted chain `03_src/route/r3.kicad_pcb`; its sha256 `c4d36e04…` IS recorded in the v1.1 MANIFEST (the M3 letter usb-power-3s missed — here satisfied) |
| M4 / M-WAIV | PASS | both policy waivers + twin adjudications carry measurements; every waiver's evidence RE-VERIFIED true on current artifacts today (R-POUR + R-PLANE rows above) |
| M5 / M-REL | PASS | v1.1 sha256 table verifies file-by-file (3/3); git_sha `6d4319b` exists, board at that sha == HEAD board (`de5fe0f`) byte-for-byte; DRC regenerated from that board = 0/0/0; CHANGELOG names the dir; SUPERSEDED chain closed; git_dirty:false true |
| M6 | PASS | authoritative-source discipline honored (twin rot-DB suggestions carried to ORDER_README preview; JLC model rotations authoritative; datasheet figures drove all three pin reviews) |

Fresh policy_audit.py (FULL, 2026-07-19): **zero FAIL** — 15 PASS,
2 WAIVED (both evidence-verified), 6 HUMAN (graded above), 3 N-A.

## 2. Release integrity (M-REL detail)

- v1.1 MANIFEST sha256: all 3 shipped files (gerbers.zip, bom.csv,
  cpl.csv) re-hashed today — all match the MANIFEST byte-for-byte.
- `git_sha 6d4319b` exists; `04_kicad/ble_bus_bar.kicad_pcb` at
  `6d4319b` == HEAD == tree sha `de5fe0f…` (electrical content frozen
  since v1.0; v1.1 = mounting-only). Fresh DRC from that board: 0/0/0
  (violations / unconnected / schematic-parity), ERC 0.
- Promoted route chain `03_src/route/r3.kicad_pcb` git-tracked, sha256
  `c4d36e04…` matches the MANIFEST tools line.
- SUPERSEDED chain closed: v1.0/SUPERSEDED.md → v1.1; v1.1 is live.
- BRIEF prompt_sha256 (`89d12ed9…`) is the commission verbatim.
- Stock: MANIFEST records 30/30 ≥25× PASS at cut; order-day re-check is
  already mandated in ORDER_README (INA238 line the one to watch).

## 3. Fresh-context pin reviews (S3 bar: derived from datasheet FIGURES first)

Three independent fresh agents, conclusion-free dossiers regenerated from
the CURRENT board (pad geometry + nets only, no part.yaml functions):

| Part | Verdict | Key derivation |
|---|---|---|
| U1–U6 INA238AIDGSR (VSSOP-10 DGS) | **PASS** | SLYS025B Fig 4-1 (p.3) top view: pin8=VBUS, pin9=IN−, pin10=IN+, pins1-5 A1/A0/ALERT/SDA/SCL, 6=VS, 7=GND. Board: IN+ (pin10, KA1) = shunt UPSTREAM (VF1/fuse) side via RP 10R; IN− (pin9, KB1) = DOWNSTREAM (VP1/stud) side via RN 10R — correct high-side positive-current convention. VBUS (pin8) tied to the IN− node (KB1) = the standard TI config (VBUS is a ~1.2 MΩ hi-Z input; reads load-side bus). Addresses re-derived from Table 6-2: A1/A0 straps give **0x40,0x41,0x42,0x43,0x44,0x45** across U1-U6, all distinct — matches DETAIL_DESIGN §3 |
| D7 SS310 (DO-214AC / D_SMA) | **PASS** | datasheet p.1 "color band = cathode". KiCad D_SMA pad1=cathode. Board: pad1(cathode)=VIN_E (electronics LOAD, downstream); pad2(anode)=VTAP=post-fuse VBUS (SOURCE, upstream). Series reverse-BLOCK orientation correct: forward VTAP→VIN_E; a reversed bus drives the anode negative and D7 blocks. Protection boundary noted: only the branch downstream of pad1 is reverse-protected (expected) |
| U11 W25Q64JVSSIQ (SOIC-8 208-mil) | **PASS** | RevJ Fig 1a: 1/CS 2/DO 3/WP 4/GND 5/DI 6/CLK 7/HOLD 8/VCC — all 8 board nets match (CS→FLASH_CS, DO→SPI_MISO, DI→SPI_MOSI, CLK→SPI_CLK, VCC/WP/HOLD→3V3, GND→GND). **Twin-fix STANDS**: board footprint = `SOIC-8_5.3x5.3mm` (body 5.3, lead span 7.18 mm) matches the SSIQ=208-mil datasheet package (§10.1: body 5.23×5.28, span 7.70-8.10 nom); a narrow 150-mil footprint would leave leads ~1.8 mm short. Advisory (carried, not a fault): /WP+/HOLD hard-tied to VCC is safe ONLY while Quad-SPI unused (QE=0 default) — firmware must not issue quad commands |

## 4. ADR-0001 reverse-polarity residual risk — honest grade

**Question posed: is the first-power ritual sufficient, or a stronger
finding?** Analysis (re-derived on the board, not from the ADR prose):

- **Main-bus omission of a series element is CORRECT engineering.** A
  60 A reverse-block FET/diode costs ≥1.8 W heat, board area, and adds a
  failure mode in the main current path. Lug-fed distribution blocks
  (Blue Sea, Eaton, automotive fuse boxes) ship unprotected + marked
  polarity. ADR-0001 §1 states this correctly; no finding there.
- **The ELECTRONICS branch is genuinely HARDWARE-protected**: on reverse
  hookup D9 (SMCJ33A) conducts forward and clamps the bus to ≈−1 V, and
  D7 (anode=VTAP) is reverse-biased and BLOCKS the buck/MCU entirely
  (§3 confirmed D7 orientation). Good.
- **The SENSING branch is NOT hardware-protected — procedure only.** The
  6× INA238 IN+/IN−/VBUS pins hang off the port copper (VF*/VP*) through
  only 10 Ω. At the reversed ≈−1 V bus, each pin sinks ≈(1−0.3)/10 ≈
  70 mA into its internal ESD structures — ~14× the 5 mA i_pin abs-max,
  ~140 mA per INA, ~0.84 A across all six. ADR-0001 §4 discloses this
  honestly ("above the 5 mA abs-max, survivable for a seconds-long
  mistake, fatal if left connected"). The 10 Ω "sense-limit" aids
  seconds-survival but does NOT prevent damage on a sustained reverse.

**Verdict: the DECISION is SOUND and the risk is honestly disclosed —
this is a model ADR, not a hidden defect.** The mitigations are real and
layered: physical keying (M5 `+` stud vs M4 GND-ref stud — a genuine
poka-yoke against lug swap), prominent silk ("CHECK POLARITY BEFORE FIRST
POWER" + two `+` glyphs), and an explicit ORDER_README first-power meter
ritual (step 2 states in-line that a reversed hookup destroys the six
monitors). The exposure exists ONLY under an installation error the
ritual specifically targets; correctly wired, there is no exposure ever.

Graded **MINOR (F1)**, not MAJOR: unlike a MAJOR finding this is not an
unresolved verification gap or an undisclosed risk — the board is
fit-for-purpose when installed correctly and the residual is an
accepted, documented tradeoff consistent with the commission directive
(D6). It is stronger than a bare "ritual note" only in that the board's
PRIMARY FUNCTION (6× INA telemetry, G3) is left on procedure-only defense
while a lower-value branch (buck/MCU) gets a hardware block — an
inconsistency worth closing next spin. Recommended (next spin, not a
blocker): (a) a per-pin GND Schottky clamp on the INA sense taps
(pennies) diverts the ESD current and removes the procedure-only
exposure; (b) strengthen the ADR to quantify the consequence (loss of all
6 monitors) and note the second-order worst case — if D9 fails OPEN
rather than short under forward surge, the INA pins see full −24 V through
10 Ω (~2.4 A/pin, instantly destructive), so the D9-fail-short assumption
should be stated as an assumption.

## 5. History coherence

- ARCHITECTURE/DETAIL_DESIGN power tree == shipped board (spot-verified:
  J7→F7→D7→buck; VBUS trunk paired pours; 6× INA238 addresses 0x40-0x45;
  KELVIN + ANTENNA rule areas present on the board).
- DETAIL_DESIGN math re-derives (§ S5). The checkpointed VBUS-impedance
  CORRECTION (VBUS pin is ~1.2 MΩ, not nA-class → ~0.2 mV offset on RN,
  firmware calibrates per ORDER_README step 4) is a real, correct catch;
  its cross-reference to the ritual holds.
- BRIEF A4/D9 corrected to "7× M4" (was "8×") at the checkpoint — now
  matches ADR-0007's H1-H7 and the board's 7 mounting holes.
- ADR-0001…0007 all still describe the board. BRIEF G1-G6 met.
- Drift found: (a) both ORDER_READMEs titled "v1.0" + "165×64 mm" while
  the v1.1 board is **165.2×74.2 mm** — the working-copy
  `06_build/ORDER_README.md` FIXED this audit; the SEALED
  `07_releases/v1.1/ORDER_README.md` copy is a finding (F2, next
  release). (b) BRIEF G-table points G1/G6 at the `v1.0` release dir
  though v1.1 is live — minor (F8), v1.1 is electrically identical.

## 6. Findings table

| # | Sev | Finding | Falsifiable evidence | Remediation | New release? |
|---|---|---|---|---|---|
| F1 | **MINOR** | ADR-0001 reverse-polarity: the 6× INA238 sense branch has NO hardware reverse-protection (10 Ω limits to ~70 mA = 14× the 5 mA abs-max; damage on sustained reverse), defended by ritual + silk + stud-keying only, while the electronics branch gets a hardware block (D7). Risk is honestly disclosed + accepted; not a defect, but the asymmetry + a pennies fix warrant a stronger next-spin note. | ADR-0001 §4; INA238 abs-max i_pin 5 mA (part.yaml); board: KA*/KB* off port copper via 10 Ω; D7 blocks electronics but not the sense taps | Next spin: per-pin GND Schottky clamp on INA sense taps; strengthen ADR to quantify 6-monitor loss + state the D9-fail-short assumption | No — accepted residual, industry-consistent, procedurally mitigated |
| F2 | MINOR | SEALED v1.1 `07_releases/…/ORDER_README.md` titled "v1.0" and lists "165 × 64 mm" — the v1.1 board is 165.2×74.2 mm (mounting section WAS updated; header + JLC-options size line were not). JLC reads the true outline from Edge.Cuts, so not an order defect. | grep line 1 + line 5 of the release ORDER_README vs board `GetBoardEdgesBoundingBox` = 165.2×74.2 | Working-copy `06_build/ORDER_README.md` corrected THIS audit; correct the header/size in the NEXT release (sealed copy untouched) | No |
| F3 | MINOR | [render review] copper PDF exports have page-furniture/frame overlapping the board area, obscuring PORT2/PORT3 labels | 07_releases/v1.1/pdf/pcb_layers.pdf | export_pdfs.sh: fit frame to outline / set title-block; next release | No (cosmetic) |
| F4 | MINOR | [render review] schematic "VBUS/BUSOUT" net label collides with the fuse symbol body → renders "BU5OUT" in all 6 port sections (ERC/parity unaffected; label text overlap) | 07_releases/v1.1/pdf/schematic.pdf, 6× port sections | schwriter2: nudge the label anchor off the fuse body; next schematic regen | No (cosmetic) |
| F5 | MINOR | S7 half-credit: buck input caps + ESP32 C7/C8 drawn as detached label→cap→GND rows near-but-not-at-pin (INA decouplers CB1-6 correctly wired at VS) | [render review]; schematic | schwriter2: attach the remaining decouplers at their IC pins; next regen | No |
| F6 | MINOR | P2 silk-glyph: D7-D11 cathode bands + LED1/2 A/K marks render effectively absent (footprints carry standard faint silk marks). CPL-driven SMD + ORDER_README preview cathode-check → LOW risk. | machine probe: 3 F.SilkS graphics per diode/LED but [render review] sees no distinct band; polarity triple-verified (pad nets + pin review + twin) | Next spin: bolder cathode/anode silk glyphs; keep the preview cathode-check in ORDER_README | No |
| F7 | MINOR | P4: one clipped "ST" status-LED silk near LED2 renders illegible (all other refdes legible) | [render review]; F.SilkS near LED2 | de-collide/reposition that silk label; next spin | No |
| F8 | NOTE | BRIEF G-table points G1/G6 at the `07_releases/v1.0-2026-07-19` dir; v1.1 is the live release (electrically identical, mounting-only) | 01_docs/BRIEF.md G1/G6 rows | Optional: add a v1.1 pointer; left as-is (v1.0 is where the electrical criteria were first met — historically accurate) | No |
| F9 | NOTE | R-PLANE waiver text cites a "41.2 mm signal run" while policy_audit flags the 63.5 mm B.Cu total within 10 mm of U7 — number-precision mismatch; both describe the same under-body fanout and the antenna zone is copper-free | policy_waivers.yaml R-PLANE vs policy_audit.md + board probe (63.5 mm) | Reconcile the waiver number to the auditor's metric at next policy_audit regen | No |

## 7. Bottom line — orderability

**The live release v1.1-2026-07-19 is ORDERABLE AS-IS.** No CRITICAL and
no MAJOR findings; all nine findings are MINOR/NOTE (documentation,
cosmetic-render, or accepted-residual next-spin items).

- Fab package: DRC re-verified 0/0/0 TODAY from the exact release source
  (`git_sha 6d4319b` board == HEAD); sha256 table verifies 3/3; ERC 0.
  JLC options: **2 oz OUTER copper REQUIRED**, **0.2 mm min-via option
  REQUIRED** (USB-C 0.3/0.2 weave) — both clearly in ORDER_README/MANIFEST.
- BOM/CPL: 30/30 coded lines PASS ≥25× at cut; hand-solder set (F1-F6
  holders, J1-J8 studs, H1-H7 mounts) is the intended not_assembled list.
  Order-day stock re-check per ORDER_README (INA238 the line to watch).
- Both policy waivers RE-VERIFIED evidence-valid on the current board
  (TRUNK paired pours + PORT pours present; EPWR at the 0.5 mm floor with
  ≥6× margin; antenna zone copper-free; under-body B.Cu fanout is a 2L
  necessity). VBUS trunk margin honestly 1.5×; port pours 1.24×.
- Three highest-risk parts (INA238 VBUS-to-IN− + addresses, SS310
  reverse-block, W25Q64 wide-SOIC twin-fix) independently re-derived
  datasheet-figure-first today — all PASS.
- **Mandatory at arrival (ADR-0001, F1)**: run the ORDER_README
  first-power polarity ritual — a reversed hookup destroys all six
  INA238 monitors and the sense branch has no hardware backstop. Verify
  D7-D11/LED cathode orientation in the JLC 3D preview (F6) before
  assembly.

Audit fixes committed (docs/build-config only; no schematic / board /
fab / sealed-release artifacts touched): working-copy
`06_build/ORDER_README.md` v1.1 title + 74 mm board size; this report.
