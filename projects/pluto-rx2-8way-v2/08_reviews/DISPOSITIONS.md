# DISPOSITIONS — pluto-rx2-8way-v2

The findings ledger across ALL reviews. One row per finding. `verification:` is
what I did to the CLAIM before dispositioning it — findings are claims, and each
is checked against the artifacts (netlist / board / part.yaml) independently.

**RELEASE STATE 2026-07-30: `v1.0-2026-07-30` IS STAGING AND DID NOT SEAL.**
THREE of the four lenses returned `design_verdict: DEFECTIVE`. Per the 08_reviews
contract that BLOCKS the seal until re-gated; per the pcb-design skill it is a
STOP-and-report, not something to argue into a green. FIVE P0s are open.

| lens | design_verdict | order_verdict | P0 | P1 | P2 |
|---|---|---|---|---|---|
| redteam topology/protection/ratings | **DEFECTIVE** | **DO-NOT-ORDER** | 2 | 6 | 14 |
| redteam layout/thermal/power-integrity | **DEFECTIVE** | **DO-NOT-ORDER** | 1 | 8 | 8 |
| pin review (12 parts, 98 pads) | SOUND | ORDER | 0 | 0 | 3 |
| render review (fresh eyes, no design context) | **DEFECTIVE** | **DO-NOT-ORDER** | 2 | 8 | 10 |

## P0 — each blocks the release

| id | review file | finding (one line) | severity | verification | disposition |
|---|---|---|---|---|---|
| P0-1 | `2026-07-30_v1.0_redteam_layout.md` | The RX1 resistive pickoff is BUILT AS A 10.107 mm BRANCH LINE, not the lumped node `DETAIL_DESIGN` §2 declares; the branch is 90° at 4.06 GHz and transforms the 490 Ω tap arm to **5.1 Ω shunt across the antenna node** — RX1 through-loss **−13.995 dB** and antenna-node return loss **1.91 dB at 4.00 GHz**, broken across ~2–5.5 GHz, on a board that silkscreens `ANT8 = RX1 TAP −20.26 dB` | **P0** | **confirmed, independently and BEFORE the lens ran.** `policy_audit` P-ADJ failed `KH-SMA-KE-Z:RX1_MAIN` and I measured the geometry directly: `J_ANT8.1 ↔ J_RX1.1 = 8.000 mm`, `J_ANT8.1 ↔ R_T1.1 = 9.903 mm`, RX1_MAIN routed copper **18.107 mm** over an 8.000 mm through path — i.e. a ~10 mm branch, 0.36 λg at 6 GHz. I recorded it as an open finding and explicitly refused to waive it (commit `0b012540`). The lens then put the dB on it. | **OPEN — fix requires a D-BACK to PLACEMENT.** R_T1/R_T2 must move hard against `J_ANT8` so the tap is a lumped node, which moves KRT-routed pads and therefore discards the promoted route chain (`03_src/route/r4.kicad_pcb`) and needs a fresh routing campaign. Not a config edit. |
| P0-2 | `2026-07-30_v1.0_redteam_topology.md` | ADR-0002 (status: accepted) and `ARCHITECTURE` §10 declare `U_MCU` **CONSIGNED and on the CPL**, while `assembly.yaml`, the BOM and the CPL all say `user_supplied` / hand-soldered / off both; `assembly_coverage.json` reports `consigned: 0`. ARCHITECTURE contradicts itself between §7 and §10 | **P0** | **confirmed.** `assembly.yaml` carries a dated posture CHANGE ("POSTURE CHANGED 2026-07-30, at the placement gate, on evidence the commission agent did not have") with a MEASURED mechanical reason — 23 components on the module's carrier-facing face, tallest 1.000 mm, against 0.010 mm castellation lands. The measurement is sound; the ADR and ARCHITECTURE §10 were never updated to match, so the release's own paperwork gives JLC two contradictory instructions about the same part. This is the cooksense-v1.1 class (13 CPL rows whose BOM line was blank while the MANIFEST declared 12 of them not_assembled). | **OPEN — docs fix, cheap.** Amend ADR-0002 with a dated supersession note and rewrite ARCHITECTURE §10 to the built posture. Must land before any seal; costs no rebuild. |
| P0-3 | `2026-07-30_v1.0_redteam_topology.md` | The staged archive has **no `MANIFEST.txt` and no `ORDER_README.md`**, and its own `assembly_coverage.txt` ships `A-POP: FAIL`; all three order-time human gates `assembly.yaml` cites (hand-solder `U_MCU`, through-hole line selection, the rotation preview) point at an ORDER_README that does not exist | **P0** | **confirmed — and it is a TRUE finding about a STAGING directory, which is what pre-seal review is for.** The archive was deliberately left un-stamped because the seal is blocked upstream by A-ROT (below); writing a MANIFEST with a placeholder `git_sha` would have shipped a draft marker. `A-POP: FAIL` reduces to exactly one finding, `MANIFEST-UNDECLARED`, which closes when the MANIFEST exists. | **OPEN — closes at seal time**, after P0-1 and P0-2. The MANIFEST's `not_assembled:` line is GENERATED from `assembly.yaml`, never hand-written. |
| P0-4 | `2026-07-30_v1.0_render-review_all.md` | **`pdf/schematic.pdf` renders an EARLIER REVISION of the board.** It draws `U_MCU` pin 1 = 5V … pin 23 = GP0; the released `.kicad_sch` and `.net` both say pin 1 = GP0 … pin 23 = 5V — the exact reverse — and it names the rails `N3V3`/`N3V3_MOD` where the netlist says `3V3`/`3V3_MOD` | **P0** | **confirmed by an INDEPENDENT method — file times and the driver's own stage list, not by re-reading the PDF.** `03_tscircuit/build/schematic.pdf` is stamped **14:47:14**; `03_tscircuit/build/circuit.json` beside it is **18:42:05** and the released `.kicad_sch` is **18:54:21**. The PDF is ~4 h older than the circuit it claims to render and predates the driver run entirely. CAUSE: `tsci build` writes `dist/src/<TSX>/`; only `gen_tscircuit.sh` writes `build/schematic.{pdf,svg}`, and `rebuild_all.sh` copies **circuit.json** from `dist/` → `build/` and nothing else. So the PDF is whatever the last hand-run left behind. **This is the EXACT sibling of the stale-`build/circuit.json` defect this board already paid for** — same directory, same cause, and M-FRESH does not cover it because M-FRESH stamps circuit.json. | **OPEN.** Regenerate with `gen_tscircuit.sh` in the same pass as P0-1. **PROPOSED SKILLS PATCH (reported, not applied):** `rebuild_all.sh` must regenerate — or at minimum freshness-check — `03_tscircuit/build/schematic.pdf`, because the 07_releases contract names that exact file as the release's HUMAN SCHEMATIC DOCUMENT. A stale human schematic is the one artifact no machine gate reads and every human does. |
| P0-5 | `2026-07-30_v1.0_render-review_all.md` | **`J_ANT8` and `J_RX1` sit 8.00 mm centre-to-centre; a standard SMA coupling nut is 5/16 in = 7.94 mm across flats.** Two mated plugs interfere and neither can be torqued | **P0** | **confirmed with a DIFFERENT instrument than the lens used** (it measured pixels on the calibrated twin render; I measured footprint centres through pcbnew against the nut dimension). `J_RX1 ↔ J_ANT8 = 8.000 mm`, inside the **9.17 mm across-corners** of a 5/16 in hex, so the two nuts overlap at EVERY rotation. It is **exactly one pair** — the next-closest jacks are `J_RX2 ↔ J_ANT8` at 9.933 mm, which clears across-corners by 0.76 mm — and it is the pair the netlist puts on the **same net (`RX1_MAIN`)**, i.e. the two that must be cabled SIMULTANEOUSLY for the reference channel to exist at all. | **OPEN — same D-BACK to placement as P0-1**, and conveniently the same 8.000 mm number. Separate `J_ANT8`/`J_RX1` to ≥ 10 mm centre-to-centre. |

**ONE PLACEMENT DECISION, THREE INDEPENDENT CONSEQUENCES, THREE DIFFERENT
LENSES.** The 8.000 mm between `J_ANT8` and `J_RX1` is simultaneously: the
`policy_audit` P-ADJ span failure (a mechanical gate, found first and priced by
nobody), the branch-line P0-1 that costs −13.995 dB at 4 GHz (the layout lens),
and the coupling-nut interference P0-5 that means the board cannot be cabled
(the render lens, looking at pictures). No single lens found more than one of
them.

## Blocking, not a review finding: A-ROT

| id | source | finding | severity | verification | disposition |
|---|---|---|---|---|---|
| B-1 | `export_jlc_package.py` exit 2 | Three LCSC codes have no measured row in the per-LCSC rotation authority table: **C2286** (LED_ST), **C504007** (ten SMA jacks), **C5121458** (U_SW) — 12 placements | blocker | **measured, all three, by hand from the raw footprint pairs (canon M1 — a different method from `jlc_rotation_measure.py`, which WITHHELD all three as `single-channel`).** Derivations and numbers in `01_docs/journal/05_verify.md`. All three offsets are **0**, so the staged CPL is already correct and will be BYTE-IDENTICAL once the rows land. | **OWED OUTSIDE THIS BOARD'S PARTITION.** The table is `skills/jlcpcb-fab/scripts/jlc_lcsc_rotations.csv`; board agents must not edit `skills/`. Reported upward as a three-row patch. |

**A trap inside B-1, worth its own line.** `twin_report.csv` carries a
`ROT-DB-SUGGEST` row saying *add `C2286,180`* while its own `POLARITY-FIT` row
three lines earlier says offset **0** is the physically correct answer. The
topology lens flagged the same contradiction independently. Copying the
suggestion places every indicator LED backwards, which is indistinguishable from
a bad solder joint. The correct row is `C2286,0,two-channel`: both libraries draw
the cathode WEST (ours F.SilkS bar at local x = −1.485 plus the F.Fab chamfer on
the −x end; JLC's bevelled silk end at −x with their pin-1 dot at +0.80 beside
their pad 1 at x = +0.75), so JLC numbers pad 1 = ANODE where KiCad numbers pad 1
= CATHODE and the physical parts already align.

## P1 — ORDER_README + the next-rev work order

| id | review file | finding | severity | verification | disposition |
|---|---|---|---|---|---|
| P1-1 | layout + topology (BOTH, independently) | The ground-via fence FAILS its own `≤ 1.35 mm` bound on 12 of 21 arm-sides (my measurement) / 15 of 22 (the lens's independent re-derivation); **both agree the worst is 5.1071 mm = λg/5.36**, at `J_ANT8` — the array's own phase reference | P1 | **confirmed by three independent measurements** (mine at ±2.5 mm band, the lens's re-derivation, and the lens's re-run of my instrument at ±2.6 and ±3.0 mm bands to test whether the SMA posts at 2.540 mm were being excluded — verdict unchanged at 12/21, worst 5.1071 both times). Every aperture is a named site OCCUPANCY, not a pitch: the declared SMA `avoid` rings, the SSE control corridor's copper, the star hub. | **deferred — ARCHITECTURE §6 already records it as an open finding, not a met requirement** (commit `03b0485e`). The lens's condition is accepted: the "≤ 1.35 mm" sentence must be rewritten and **no phase table may be published before bench measurement**. λ/2 resonance at 16.09 GHz is out of band. |
| P1-2 | layout | The module's declared underside copper keepout (User.2 rect, x 58.10–59.30 / y 73.80–86.00, drawn against TEN LIVE SMD PADS on the RP2040-Zero's carrier-facing face) contains **22 GND vias**, because the pwr/ctrl/sig waves each override `keepout_layer` to User.3 and — decisively — **the zone and stitch passes are not router objects at all** | P1 | **confirmed and quantified, and I MADE IT WORSE.** Measured: 22 GND vias, 0 tracks, inside the rect. The lattice puts **6 sites there at the old 2.0 mm pitch, 9 at 1.35, and 26 at 0.95** — so my fence change (commit `03b0485e`) roughly quadrupled the count. `route.yaml`'s own comment claims that rect "binds EVERY wave"; that claim is FALSE for the stitcher, which never consults a router keepout. | **OPEN, fix identified, deliberately NOT applied yet.** `stitch.stitch_grid.avoid` takes rectangles — adding this rect removes all 22. Not applied now because the board is going back to placement for P0-1 and a source edit without a rebuild would leave the committed board no longer regenerable from its own config (canon M3). Apply it in the SAME pass that fixes P0-1. |
| P1-3 | topology | `nets.yaml` asserts a coplanar conductor "does not" run alongside the RF lines. **Measured, it does**: `ANT5 ↔ SW_V4` at **0.265 mm** (g/h 1.26) for 1.936 mm; `ANT4 ↔ 3V3` at 0.770 mm with 100 % of the arm within 2.0 mm; six arms have 0.000 mm clearance within 2.0 mm | P1 | not re-measured by me — **INHERITED from the lens, with its numbers.** | deferred to the next-rev work order; the coplanar-loading question is the one `rf-design.md` 3(c) already records this fleet as unable to settle without a field solver. |
| P1-4 | layout | The length-match pass half-ran: `ANT3`/`ANT7` are unmeandered at 2 segments each, leaving a **0.5314 mm** spread against a **0.0007 mm** octilinear floor = 6.985°, **53 % of the part's whole 13.2° relative-phase window, free to recover** | P1 | **confirmed against the shipped R-LEN evidence**: `copper_length_audit` reports PASS at spread 0.5314 mm = 7.01° against a 1.0 mm ceiling with the floor at 0.0007 mm. The gate passes; the lens's point is that the ceiling is loose, not that the gate is wrong. | deferred — recover in the same routing campaign that fixes P0-1, where the arms are re-routed anyway. |
| P1-5 | layout | `ANT5` runs 2.40 mm over a reference perforated by `SW_V3`/`SW_V4` vias at 0.539–0.545 mm, vs 0.35–0.40 mm on the other seven arms | P1 | INHERITED from the lens. | deferred to the next-rev work order. |
| P1-6 | layout | The module is **absent from the STEP export and from all five twin renders** | P1 | consistent with `missing_models.txt` and with `U_MCU` being `on_bom: false` / `exclude_from_pos_files` — a bodiless footprint means "no model", never "not placed", and here it genuinely is not placed by JLC. | recorded; ORDER_README must say so explicitly so a reviewer of the renders does not read the gap as a defect. |
| P1-7 | topology | `keep_short {SW_V4, 4 mm}` missed by **+3.958 mm** as built (`U_SW.12 → R_PD4.1 = 7.96 mm`) | P1 | **confirmed independently, before the lens ran** — this is the second of the two findings `policy_audit` P-ADJ surfaced once the mis-encoded arm budget stopped drowning the list. Not decorative: V4 = 1 with V1..V3 = 0 MUTES EVERY PORT (Table 5, PDF p10), so pin 12 is the pin whose float is silent. NOT WAIVED. | **OPEN** — move `R_PD4` (and its three siblings) to the pad in the same placement pass as P0-1. |
| P1-8 | topology | `source/` omitted `.kicad_pro` and `.kicad_dru` | P1 | **confirmed and FIXED during staging, and the fix is load-bearing.** A standalone re-measure of `source/` outside the repo returned **657 violations** for two independent reasons: `fp-lib-table` pointed at `${KIPRJMOD}/../03_src/lib/…` (escaping the archive) and the netclass/dru files were missing, so DRC graded the board against KiCad's DEFAULT 0.2 mm rules. After copying both files in and rewriting the URI to `${KIPRJMOD}/…`: **0/0/0**, shipped as `verification/standalone_archive_drc.json`. | **fixed in staging.** The lens read the pre-fix archive. |

## P2

Recorded in the two review files verbatim (14 + 8). Three from the pin review
carry forward and are worth naming here because none is visible in copper:
**J_ANT8's centre pin is on `RX1_MAIN`, not on a switch port** — correct per
ARCHITECTURE §1–2, but the refdes teaches the wrong topology and deserves a silk
legend; **the V1-is-MSB obligation now lives entirely in firmware that does not
exist yet** (`05_firmware/` holds only `contracts.md`), and a V1 = LSB assumption
yields sweep order 1,5,3,7,2,6,4,8 which an AoA solver absorbs as a permuted
array; and **the `RP2040-Zero` dossier shipped with an empty function column and
no `verified:` note**, so the pin reviewer graded it against the vendor files
present rather than against a dossier claim.

## 2026-07-30 — round 2 (r2), the ONLY live verdicts. Round 1 is VOID.

The four `2026-07-30_v1.0_*.md` reviews without an `_r2` suffix graded a board
that NO LONGER EXISTS: since they were written, C_SW2 rotated 180 degrees, six
User.3 barrel windows were declared, the control pocket was re-routed twice
(`--race 3` then `--race 4`), the promoted chain moved r4 -> r5, and five
declared thermal barrels landed in U_SW's exposed pad. A placement change of
that size voids a verdict; the round-1 files are retained as history and MUST
NOT be cited as this board's verification.

The four r2 reviews were run FRESH-CONTEXT and CONCURRENT, each with a DISTINCT
filename. That is deliberate: a contract naming ONE review file lets a second
reviewer silently overwrite the first, which nearly lost a review on the sibling
board.

| lens | file | design_verdict | order_verdict |
|---|---|---|---|
| topology/protection/ratings | `2026-07-30_v1.0_redteam_topology_r2.md` | **DEFECTIVE** | DO-NOT-ORDER |
| layout/thermal/PI/RF        | `2026-07-30_v1.0_redteam_layout_r2.md`   | **DEFECTIVE** | DO-NOT-ORDER |
| fresh-context pin review    | `2026-07-30_v1.0_pin-review_all_r2.md`   | SOUND | ORDER |
| fresh-context render review | `2026-07-30_v1.0_render-review_all_r2.md`| SOUND | DO-NOT-ORDER |

**TWO DEFECTIVE VERDICTS => THE SEAL IS REFUSED.** The staging archive was
deleted from `07_releases/` rather than left sitting there (an unsealed
directory named like a release is a lie waiting to be read); the bytes are
preserved at `06_build/staging/` so the next round re-stages rather than
re-derives. No release exists for this board.

### Dispositions

| finding | lens | disposition |
|---|---|---|
| **P0 fence: worst along-arm aperture 3.0500 mm vs the ADR-0003 bound of 1.35 mm (2.26x), `fence_pitch.txt` ships ending `VERDICT: FAIL`, and ARCHITECTURE sec 6 quoted stale numbers from a superseded board** | layout | **OPEN — the blocking finding.** ARCHITECTURE sec 6 REWRITTEN 2026-07-30 with the re-measured numbers, dated, and labelled an open P0 rather than a met requirement. The physical gap is NOT closed: it needs a placement change that frees the occupied lattice sites, a per-arm fence pass, or an ADR-0003 amendment that re-derives a bound the board can hold and measures what the residual apertures cost. The reviewer's independent count (13 of 20) and the tool's (11 of 20) differ with the segment convention; the WORST VALUE agrees exactly. |
| **P0 no MANIFEST / no ORDER_README in the staged archive; three order-time human gates homeless** | topology | **CORRECT, and it is why the archive was pulled.** Staging was incomplete when the lenses ran — the reviewer graded what was there and was right to. |
| **P0 shipped `policy_audit.md` predates the fab artifacts, so A-POP/M-BOM/M-REL read vacuous N-A and the summary shows zero FAILs** | topology | **CORRECT and generalisable.** A stale audit inside a release does not look stale; it looks passing. Next round: `policy_audit` runs LAST, after the fab set, and its output is copied in the same step. |
| **P1 ARCHITECTURE sec 10 still called the module CONSIGNED and "placed by JLC"** | topology | **FIXED 2026-07-30.** Section 7 had been corrected earlier the same day and section 10 had not, so the document contradicted ITSELF while every gate stayed green. Found by a zero-context reviewer; no checker looks at prose. |
| **P1 the S-OCCL waiver's premise is falsified by the shipped file — all four occlusions ARE in `pdf/schematic.pdf`, plus two the checker never listed** | render | **OPEN, and the waiver is now KNOWN-BAD.** Its whole argument was that the collisions live only in the machine `.kicad_sch`. They do not. The waiver must be withdrawn or re-argued against the document a human reads — it may not be renewed as written. |
| **P1 schematic readability S6 FAIL: `N3V3_MOD`/`ANT2` overlap on U_SW pin 2 so the picture says the 3V3 rail is wired to an RF port; no title block; struck-through labels** | render | **OPEN.** S6 is a HUMAN-graded item and the human graded it FAIL. A label pair that actively lies is worse than an unreadable one. |
| **P1 `assembly.pdf` / `pcb_layers.pdf` unusable as documents (1:1 in a corner of A4, no layer-name captions)** | render | **OPEN.** Export options, not board content. |
| **P1 arms are built as grounded coplanar waveguide (GND pour at median 0.205 mm both sides over 67.5-94.3% of each arm) while the published constant set is a BARE-MICROSTRIP derivation; `nets.yaml` states in writing that a coplanar ground "does not" run alongside** | layout | **OPEN, and the most valuable finding of the round.** If it holds, ADR-0003's whole constant set is derived for a geometry the board does not have (CBCPW: eps_eff 3.1552, -5.21%, -4.98 deg per arm at 6 GHz). It also moves the fence bound. Must be settled BEFORE the fence P0, because it changes the number the fence is graded against. |
| **P1 the length-match meander widens the 0.360 mm line to 0.600 mm over 0.555 mm (local Z0 37.17 ohm) on six of eight arms, and turned a 0.001 mm pad-chord spread into 0.5313 mm of track-length spread** | layout | **OPEN.** A gate that shares the router's own length metric cannot see this. |
| **P1 the "unbroken In1.Cu under a matched arm" invariant is held on ANT5 by 0.0224 mm against +/-0.075-0.10 mm layer registration** | layout | **OPEN.** A tolerance smaller than the registration it lives inside cannot distinguish pass from fail. |
| **P1 no stackup/impedance declaration anywhere in the order package** | layout | **OPEN.** A controlled-impedance board that does not tell the fab it is one is not a controlled-impedance board. |
| **P1 `P-FACT` could not reach the KT-0603R `pad1_net_polarity` assertion although `source/*.net` is present** | topology | **OPEN (gate defect).** The reviewer verified the polarity by hand and it is correct; the CHECK is structurally blind. Propose upward as a `skills/` patch — not this board's partition. |
| **P1 `pin_audit.py` produced a CONTENT-FREE dossier for U_MCU** (`MPN unknown`, `datasheet: (none)`, `(not in yaml)` x23) because it resolves refdes->MPN through `bom_jlc.csv`, and U_MCU is declared-unpopulated so it is in neither BOM nor CPL | pin | **OPEN (gate defect), and the shape is A-POP's twin.** The gate could not have failed on the one part whose own `part.yaml` warns in capitals about wrong-pad GPIO. The reviewer recovered the map from `02_parts/` and both vendor figures independently and the board is unaffected. Propose upward as a `skills/` patch. |
| **P1 three-corner mounting: the SE hole sits 12.7 mm inboard, leaving the USB-C quadrant unsupported** | render | **OPEN.** A press-fit USB-C on an unsupported corner is a flex path. |
| P2 x25 across the four lenses | all | recorded in the review files; none blocking. |

---

## 2026-07-31 — the ARTIFACT round. Re-measured, not re-argued.

An independent seal judge (`2026-07-31_v1.0_redteam_archive-integrity.md`)
refused the staged archive `design_verdict: DEFECTIVE` / `order_verdict:
DO-NOT-ORDER`, and scoped that verdict itself: *"I did not grade the circuit. I
graded the ARCHIVE and the gates that would grade the archive at seal."*
Three more lenses ran the same day (`_redteam_rf-electrical`,
`_redteam_schematic-netlist`, `_redteam_fab-manufacturability`).

**THE COPPER WAS NEVER IN QUESTION AND DID NOT MOVE.** Footprint signature,
track count, via count and zone count are IDENTICAL between the archive the
lenses read and the archive shipped now (32 footprints at identical positions
and rotations; 199 tracks; 3446 vias; 6 zones — measured through pcbnew). Every
row below is a paperwork or evidence change.

### Closed, each with the measurement that closes it

| finding (round, lens) | disposition |
|---|---|
| **P0 fence: worst along-arm aperture 3.0500 mm, 13 of 20 arm-sides over, `fence_pitch.txt` ships `VERDICT: FAIL`** (r2, layout) | **FIXED.** `fence_pitch.py` re-run against the shipped board: worst interior along-arm gap **1.1769 mm** against the λ_pp/20 bound **1.1910 mm**, **22 arm-sides measured, 0 OVER**, `VERDICT: PASS`, RAW EXIT 0. |
| **`verification/fence_apertures.txt` asserted `RX1_TAP sideL GAP 1.9000 mm` with 6 empty sites, inside the same directory where `fence_pitch.txt` said PASS** (2026-07-31, archive-integrity) | **FIXED.** The file was the PRE-FIX output: the classifier counted only `PCB_VIA` and so saw 3433 of the fence's 3473 elements, missing the 40 PTH GND launch posts. Re-run against the shipped board: `fence elements: 3433 PCB_VIA GND + 40 PTH GND post(s) = 3473`, **ZERO apertures**, RAW EXIT 0. The two files now agree. |
| **P1 arms are CBCPW while the constant set is a bare-microstrip derivation, and `nets.yaml` says in writing that a coplanar ground does not run alongside** (r2, layout) | **FIXED** at `c566911b` — re-derived as conductor-backed coplanar waveguide (ADR-0004), the falsified sentence removed, and the fence bound got TIGHTER as a result. Independently re-derived by the 2026-07-31 RF lens, which reports `design_verdict: SOUND` for the RF architecture, the constant set, the fence bound and the tap topology. |
| **P0 no `MANIFEST.txt`, no `ORDER_README.md`; three order-time human gates homeless; `A-POP: FAIL`** (r2, topology) | **FIXED.** Both documents present. `assembly_coverage.py` against this archive: **A-POP: PASS**, RAW EXIT 0 — 32 footprints, 27 CPL, 5 unpopulated all declared, A-POS datum worst 0.00000 mm. All three human gates are on ORDER_README's first screen (§2a through-hole, §2b rotation, §2c polarity), plus §2d F-ECHO. |
| **P1 no stackup / impedance declaration anywhere in the order package** (r2, layout) | **PARTIALLY FIXED — and the residue is named.** ORDER_README §0 now states stackup `JLC04161H-7628`, the ADVANCED small-via requirement, IMPEDANCE CONTROL REQUESTED, 1 oz outer copper and the surface-finish choice, with the hole census that makes the tier mandatory (3446 of 3496 plated holes under the no-fee tier's 0.30 mm drill floor; min hole-to-hole 0.3016 mm against a 0.50 mm floor). The `.kicad_pcb` still carries **no `(stackup …)` block** — and neither does any of the 34 sealed boards in this fleet, so that is FLEET NORM and a generator change, not this board's regression. Recorded as ORDER_README §7 item 4. |
| **P0 the shipped `policy_audit.md` predates the fab artifacts, so A-POP/M-BOM/M-REL read vacuous N-A** (r2, topology) | **FIXED by ordering.** `policy_audit` now runs LAST, after the fab set and after the release-scoped gates, and its output is copied in the same step. M-BOM now reads `PASS … every LCSC == source (28 coded)` rather than N-A. |
| **P1 `P-FACT` could not reach the KT-0603R `pad1_net_polarity` assertion although `source/*.net` is present** (r2, topology) | **CLOSED BY THE ARCHIVE, not by a gate patch.** With the netlist inside the graded archive, `part_facts_check.py` now reaches **7 of 8** assertions (was 6 of 8) and the polarity assertion is one of the newly graded. The single remaining UNREACHED is named and correct: RP2040-Zero's value assert keys on `C5350143`, which is on no BOM row because the module is `on_bom: false`. |
| **P0-1 / P0-5 the RX1 pickoff is a 10 mm branch line (−13.995 dB at 4 GHz) and two SMA coupling nuts interfere at 8.000 mm** (r1, layout + render) | **FIXED** at `5425538b`, re-measured 2026-07-31 through pcbnew: `J_ANT8`↔`J_RX1` is **11.0000 mm** centre-to-centre; RX1_MAIN carries **11.0000 mm** of copper over an 11.0000 mm through path, i.e. **no branch**; `R_T1.1` sits **5.5000 mm** from `J_ANT8.1` (was 9.903). Closest jack pair is now `J_ANT8`↔`J_RX2` at **9.9334 mm**, clearing a 5/16 in nut's 9.168 mm across-corners by 0.765 mm. |
| **P0-4 `pdf/schematic.pdf` renders an EARLIER revision** (r1, render) | **FIXED** — `rebuild_all.sh` step [1r] deletes the PDF FIRST and regenerates it, and step [1a] M-FRESH requires the render to post-date the `circuit.json` it depicts. |
| **A-EVID: 10 contract-REQUIRED artifacts absent** (2026-07-31, archive-integrity) | **FIXED.** `release_required_check.py … --contract 07_releases/contracts.md` → **A-EVID OK: 33 required artifact(s) present**, RAW EXIT 0. The one conditional absence is `3d/<board>.gltf` (no exporter). |
| **`fab/bom.csv` + `fab/cpl.csv` absent, so A-STOCK and A-BUY reached a ZERO DENOMINATOR and emitted NOTES** (2026-07-31, archive-integrity) | **FIXED IN THE PRODUCER** (`export_jlc_package.py`, commit `628ee3d4`), not by a hand-copy. `release_freshness_check.py` now reports `A-STOCK: … 11 graded line(s), verdict=PASS` and `A-BUY: measured SOURCING: CLEAR over 11 coded+placed line(s)`; overall `SOURCING: CLEAR`. |
| **`bom_source_check.txt`, `bom_legibility.txt`, `part_facts.txt` name `07_releases/v1.0-2026-07-30/`, a directory that does not exist** (2026-07-31, archive-integrity) | **FIXED** by re-running all three against the real archive path. **The shortcut was refused**: sealing under the name `v1.0-2026-07-30` would have turned the gate green without making the evidence truer. |
| **`assembly.yaml` cites `verification/jlc_catalog_C504007.json` and `verification/stock_check.csv` and NEITHER FILE EXISTS** (2026-07-31, archive-integrity) | **FIXED with real evidence, not by deleting the citation.** The raw JLC assembly-endpoint response is archived with a `_provenance` block; every field re-reads identical on 2026-07-31 except `stockCount`, 23169 → 22708. `stock_check.csv` is produced by `jlc_stock_check.py --out` and carries the `mpn` column the contract requires. |
| **`ORDER_README` carries `design_verdict: PENDING`, outside the closed vocabulary, and claims a 62 ↔ 62 bijection where the truth is 63** (2026-07-31, archive-integrity) | **FIXED.** Verdicts are `DEFECTIVE` / `DO-NOT-ORDER`, inside `SOUND\|DEFECTIVE` and `ORDER\|DO-NOT-ORDER\|BLOCKED-SOURCING`. The bijection count is no longer retyped into prose at all — the MANIFEST footer states it (80 files) and the check is run rather than quoted: 80 rows ↔ 80 files, 0 rows without a file, 0 files without a row, 0 hash mismatches on an independent re-hash of all 80. |
| **`01_docs/CHANGELOG.md` does not exist while M-REL's check is `if cl.exists()`** (2026-07-31, archive-integrity) | **FIXED.** The absence was a SILENT SKIP precisely where there was nothing to check. |
| **`MANIFEST` `git_sha` stale, no `git_dirty` line** (2026-07-31, archive-integrity) | **FIXED, and deliberately NOT used to move M-REL.** `git_sha: 628ee3d4…`, `git_dirty: true` — MEASURED by `release_git_dirty.py`, RAW EXIT 1. Every input this board owns is committed; the one dirty path is a sibling workflow's uncommitted `skills/kicad-pcb/scripts/route_and_stitch_generic.py` in this shared tree, and the MANIFEST names it. |

### Still open

| finding | disposition |
|---|---|
| **`policy_audit` S-OCCL: FAIL, 13 schematic text occlusions** | **OPEN, and it is a NEW class rather than the old one.** MEASURED: 170/170 drawable objects placed, population `wires 35, global_labels 46, symbol instances 89`; **12 of the 13 are text-over-WIRE**, a population `sch_occlusion.py` only gained on 2026-07-31. The four text-over-TEXT pairs the r2 render lens found are **gone**. **NO WAIVER, by choice** — this project withdrew its S-OCCL waiver on 2026-07-30 after the render lens falsified its premise, and `policy_waivers.yaml` carries zero entries with that history written into it. The fix belongs in the converter's de-collision pass (`circuit_json_to_kicad_sch.py`), which must treat a wire as an obstacle. **A `skills/` change — proposed upward, not made in this board's partition.** |
| **`policy_audit` A-POP: FAIL** | **OPEN ONLY AS AN ARTEFACT OF NOT SEALING.** `policy_audit` resolves A-POP's target as *the latest sealed release, else the project directory*; with `07_releases/` empty it grades the project root, finds no MANIFEST there and reports `MANIFEST-UNDECLARED`. The same gate against the actual archive is **A-POP: PASS, RAW EXIT 0**. Closes at the seal; nothing about the board changes. |
| **`release_freshness_check`: DESIGN FAIL, 10 findings** | **OPEN, and ALL TEN ARE IN REVIEW DOCUMENTS — zero about the board, the fab set, or any machine evidence.** 8 × `EVIDENCE PATH MISMATCH` (six review files name the `07_releases/v1.0-2026-07-30/` they were run against; that directory was never created) + 2 × `REVIEW-NO-VERDICT` on `redteam_topology.md` / `redteam_layout.md`, which DO state `design_verdict: DEFECTIVE` — at lines 211-212 and 77-78, below the 40-line header window the gate reads. **Neither may be closed by editing a review** (this contract makes review files append-only, verbatim) **nor by choosing a seal name that matches the stale path.** Both close when the fresh scoped red-team writes reviews naming the archive it actually graded, and those become the promoted lens files. |
| **`M-REL` is UNGRADED on this archive** | **OPEN, and it is a GATE property, not a claim about these hashes.** M-REL's regex (`policy_audit.py:1643-1646`) admits two MANIFEST layouts and this archive ships a third (`<hash>  <size>  <path>`); its zero-coverage backstop at `:1660` tests for the literal substring `sha256:`, which this banner does not contain. So M-REL verifies ZERO of the 80 rows and a green M-REL here would be evidence of nothing. The hash table was written because it is correct. `policy_audit.py` is another workflow's file — reported, not edited. |
| **P1 `pin_audit.py` produces a CONTENT-FREE dossier for `U_MCU`** (r2, pin) | **OPEN (gate defect), unchanged.** It resolves refdes→MPN through the fab BOM, and `U_MCU` is `on_bom: false`, so the one part whose `part.yaml` warns in capitals about wrong-pad GPIO is the one the gate cannot reach. A `skills/` patch. |
| **P1 `assembly.pdf` / `pcb_layers.pdf` unusable as documents** (r2, render) | **OPEN.** Export options, not board content. |
| **P1 three-corner mounting leaves the USB-C quadrant unsupported** (r2, render) | **OPEN.** Carried to v-next. |
| **P1 the length-match meander widens the 0.360 mm line to 0.600 mm on six of eight arms** (r2, layout) | **OPEN.** Carried; the gate that would see it must measure copper WIDTH, not polyline length (canon M1 — the current gate shares the router's own metric). |
| **P1 the "unbroken In1.Cu" invariant is held on ANT5 by 0.0224 mm against ±0.075–0.10 mm registration** (r2, layout) | **OPEN.** A tolerance smaller than the registration it lives inside cannot distinguish pass from fail. |
| **Surface finish is not declared in `03_src/`** (2026-07-31, this round) | **OPEN, OWED to v-next.** ORDER_README §0 states ENIG as an order-time RECOMMENDATION with its measured basis, and says explicitly that no project file declares one — rather than inventing a finish and shipping it as if it were a decision. |
