# render_review — contract-named copy

> **PROVENANCE.** This is the CURRENT render review for this board, shipped under
the name `07_releases/contracts.md` requires. It is a VERBATIM COPY of
`08_reviews/2026-07-27_v1.9_render-review.md`, which remains in place — dated
history lives in `08_reviews/`, the contract name ships in the release, and the
file is COPIED rather than moved so the provenance survives in both places.
>
> **VERDICT: PASS.** 0 P0, 3 P1, 6 P2. The reviewer confirmed the copper pour
independently on all four layers, and derived BOTH feedback dividers from the
shipped netlist before reading any design document — reaching this release's own
numbers (5.352 / 5.248 / 5.151 V) exactly.
>
> **All three P1s were acted on BEFORE the seal**, which is what a pre-seal lens
is for:
> * **RR-1** — `assembly_coverage.txt` shipped `A-POP: FAIL` while the MANIFEST
reported the gate clean. Root-caused by mtime: A-POP read the MANIFEST 21 minutes
before the MANIFEST was written. **Re-run: PASS**, and it is now regenerated AFTER
the stamp. See `gate_adjudications_v1.9.md` §3.1.
> * **RR-2** — `missing_models.txt` reports `122/122` while R12 (C2984354) has no
JLC model at all. The generated file is NOT hand-edited (v1.5 shipped a
hand-authored one that lied); the correction is in the MANIFEST `twin:` line and
`gate_adjudications_v1.9.md` §3.2.
> * **RR-3** — the 5VC worst corner vs "the port limit". **Adjudicated:** 5.479 V is
INSIDE USB Type-C `vSafe5V` (4.75-5.5 V for a source) by 21 mV, but is **+229 mV
above the Raspberry Pi 4's own recommended-input maximum** while staying 521 mV
below its absolute maximum. Recorded in `DETAIL_DESIGN` sec.4 and ORDER_README
section 5.
>
> Per-finding disposition for all nine: `08_reviews/DISPOSITIONS.md`.

---

# v1.9 render review — usb-hub-3s-v3 (zero-context)

## Provenance

| field | value |
|---|---|
| date | 2026-07-27 |
| reviewer | zero-context render review (no prior involvement in this design) |
| release under review | `projects/usb-hub-3s-v3/07_releases/v1.9-2026-07-27/` (staged, read-only) |
| board | `usb_hub_3s_v2`, 130.1 x 92.1 mm, 4 layer, 119 CPL placements, all top side |
| verdict | see final line |

**Inputs used.** `verification/twin_{top,bottom,iso_nw,iso_se,edge_west,edge_east}.png`;
`verification/render_{top,bottom}_bare.png`; `verification/twin_report.csv`,
`missing_models.txt`, `twin_overlay_top.md`, `assembly_coverage.txt`,
`fab_payload_census.txt`, `part_facts.txt`, `audit.txt`, `drc.json`,
`rotation_human_gate.txt`; `pdf/{schematic,pcb_layers,assembly}.pdf` (rasterised
at 100-400 dpi and read as images); `fab/{bom.csv,cpl.csv}`, both drill files and
the gerber zip (opened, `Edge_Cuts` / `F_Silkscreen` extracted); `source/*.kicad_pcb`,
`*.net`, `*.kicad_pro` and the five project footprints, read only to turn pixels into
millimetres; `MANIFEST.txt`, `ORDER_README.md`;
`verification/DETAIL_DESIGN.md` (sec. 2.11 / 4 only, to check one arithmetic claim);
`skills/jlcpcb-fab/scripts/jlc_lcsc_rotations.csv`.

**Independence.** I did not open `01_docs/STATUS.md`, any `08_reviews/` file, or the
copies of prior reviews the release carries in `verification/`
(`2026-07-26_v1.8_render-review.md`, `..._pin-review.md`, the redteam files). I also
deliberately did **not** open `verification/gate_adjudications_v1.9.md`, which
adjudicates several of the findings I was asked to judge independently. Every
conclusion below was reached from the renders, the fab payload and the netlist first;
where the release turned out to have already reasoned about something, I say so and
report whether my numbers matched theirs.

**Caveats applied as instructed.** Q1..Q6 (PowerPAK SO-8) judged from courtyards and
pads in `render_top_bare.png` and `pcb_layers.pdf`, never from body position. The
1210/0805 bulk MLCC overlay FAILs treated as segmentation artifacts. J1..J5 body
overhang past courtyard treated as legitimate. One addition of my own: `twin_overlay_top.md`
measures **J1** at a 6.792 mm centre delta (expected `13.850..31.950 x`, measured
`12.400..19.815 x`) — by the overlay's own legend that is a *render* defect, so I did
**not** judge J1's edge fit from the picture either; I used the expected-geometry
column and the footprint.

---

## Findings

Severity: **P0** blocks the release. **P1** must be answered before ordering but does
not by itself invalidate the payload. **P2** is a quality/legibility defect.

| # | finding | sev | evidence | what I actually looked at |
|---|---|---|---|---|
| 1 | **A failing gate ships inside the release, and the MANIFEST reports the same gate as clean.** `verification/assembly_coverage.txt` ends `A-POP: FAIL (1 finding(s))`, reason `MANIFEST-UNDECLARED: the release MANIFEST carries no not_assembled: line`. But `MANIFEST.txt` *does* carry `not_assembled:  F1, R42, SW1   (GENERATED from 03_src/rules/assembly.yaml)`. Root cause is ordering, and it is measurable: `assembly_coverage.txt` mtime `11:43:54`, `MANIFEST.txt` mtime `12:04:45` — **A-POP reads the MANIFEST 21 minutes before the MANIFEST is written**, so this check can never pass on a first build. The MANIFEST's own GATES block lists A-POP as passing with no mention of the FAIL. | P1 | `assembly_coverage.txt` final line; `MANIFEST.txt` `not_assembled:` line and GATES block; `stat -c %y` on both | read both files; compared mtimes |
| 2 | **`missing_models.txt` is false, and it is the file a reviewer is told to trust.** It states `bodies mounted: 122/122` and `(none — every CPL designator resolves a 3D body)`. In fact **R12 (C2984354) has no JLC model**: its only row in `twin_report.csv` is `FETCH-FAILED,"['[ERROR] Failed to fetch data from EasyEDA API for part C2984354']"`, and it is the one ref of 122 with **no `MODEL-REG*` row at all** (121 of 122 have one). `twin_overlay_top.md` states this correctly — `1 with no JLC model at all`. `MANIFEST.txt` repeats the wrong number (`twin: bodies mounted 122/122`). A reviewer who sees R12 bodiless and consults the designated list is told every part has a body, and would conclude R12 is missing from the board. | P1 | `missing_models.txt`; `twin_report.csv` (R12 rows); `twin_overlay_top.md` coverage line; `MANIFEST.txt` GATES | set-differenced all 122 refs in `twin_report.csv` against those carrying `MODEL-REG*` |
| 3 | **The USB-C rail ships nominally above the USB port ceiling; worst static corner is 229 mV over it.** R42 (160 kΩ) is a DNP trim in parallel with R12 (4.12 kΩ) from `5VC` to `FB_C` on U11. From the shipped netlist alone I computed, before reading any design doc: without R42 `1.215 × (1 + 4.12/1.21) = 5.352 V`; with it `160k∥4.12k = 4.0166k → 5.248 V`. Channel A is `1.215 × (1 + 3.92/1.21) = 5.151 V`. The release's own numbers match mine exactly. It is **declared and reasoned** (ORDER_README bench gate Q9; DETAIL_DESIGN sec. 4 argues 5.25 V is U12's test condition, not an absolute max, with V_BR min 6.0 V giving −648 mV). What I want on the record anyway: DETAIL_DESIGN's own worst static corner for 5VC is **5.479 V**, which is 229 mV above the 5.25 V port limit and applies to **every attached device**, not only to U12. The trim ships loose, so this is a bench decision, not a respin — but it is the one place where the as-shipped board is out of spec by design. | P1 | `usb_hub_3s_v2.net` nets `5VC`/`FB_C`; `fab/bom.csv`; ORDER_README Q9; DETAIL_DESIGN lines 314/320-321/365/514-516 | derived the divider from the netlist independently, then compared |
| 4 | **51 image artifacts that the A-RENDER report names are not in the release.** `twin_overlay_top.md` cites `twin_top_courtyard_overlay.png` plus 50 per-ref crops (`overlay_D8.png`, `overlay_J1.png`, `overlay_Q1.png`, `overlay_R12.png`, …). **None of the 51 exist** — the release has 69 files and not one of them is an `overlay_*.png`. So the report's central claim (29 FAILs, 0 board defects) cannot be re-checked from the release alone. Compounding it, coverage is **53 measured / 121 refs with an expected body** — 68 unresolvable, so render faithfulness is established for 44 % of the board. (The coverage number is disclosed; the missing crops are not.) | P2 | `twin_overlay_top.md` artifact list vs `find` over the release | enumerated every `.png` cited in the report and tested each for existence |
| 5 | **`twin_report.csv` contradicts itself on the indicator LEDs.** For C2296/C2297 it emits `POLARITY-FIT` — *"the pad fit is 180deg wrong PHYSICALLY and offset 0 is what places the part correctly … never let the fitted angle populate the rotation table unchallenged"* — and then, three rows later, `ROT-DB-SUGGEST: fit=0.11mm jlc_offset=180 … -> add LCSC row C2296,180 to jlc_lcsc_rotations.csv`. Applying the suggestion reverses all five LEDs. **The board is correct**: `jlc_lcsc_rotations.csv` carries `C2296,0` and `C2297,0` with a hand-measured two-channel derivation, and `fab/cpl.csv` ships D8-D12 at `0.0`. But the release contains a machine-readable instruction that would flip them, sitting next to the prose saying not to. | P2 | `twin_report.csv` C2296/C2297 rows; `jlc_lcsc_rotations.csv` lines 33-34; `fab/cpl.csv` D8-D12 rotations | read all three; confirmed shipped rotation is 0 |
| 6 | **The silkscreen next to the battery connector reads `J1 FUSE 10A MINI`.** In `render_top_bare.png` this is one contiguous line on one baseline, sitting directly under J1's XT60 outline (the arc and `\|` polarity tick are immediately above it). J1 is the **XT60 battery input**; the 10 A mini blade fuse is **F1**, 12 mm lower, labelled only `F1`. The free text is at `(35, 50)` and F1's body at `(35, 56)`, so it is nominally F1's caption — but on the printed board it lands on J1's line and reads as J1's value. A via also breaks the string between `FUSE` and `10A`. | P2 | `render_top_bare.png` crop of mm X 20-47 / Y 39-60 at 5x; `gr_text` table from `usb_hub_3s_v2.kicad_pcb` | read the crop; cross-checked all 17 free silk strings and their coordinates |
| 7 | **`pdf/assembly.pdf` p1 is unusable as an assembly aid in the dense areas, and does not mark DNP.** Around U2/U11 the value, LCSC and refdes layers overprint into an unreadable block (`12.4kΩ`/`49.9kΩ`/`6.98kΩ`/`100kΩ`/`3.92kΩ`/`1.21kΩ`/`18kΩ`/`330pF`/`3.3nF`/`100nF` stacked); around C1/F1, `C2760089`/`C2939728`/`C78284`/`C2296` are printed on top of one another. Separately, **F1, SW1 and R42 are drawn exactly like placed parts** with no DNP hatch or note — the three parts the CPL omits are indistinguishable from the 119 it places. The drawing also occupies about half the A4 sheet, which is why the type is that small. | P2 | `pdf/assembly.pdf` p1 at 150 dpi | rendered and read the page |
| 8 | **`pdf/schematic.pdf` has no sheet frame, title block, revision or date, and draws every FET and diode as an unmarked box.** At page scale (900 x 450 pt, one sheet, 129 parts) it is not readable; it becomes readable only at ~400 dpi zoom, where U2's pin names/numbers and the net labels are all correct and legible. Q3/Q5 render as plain rectangles with `S1 S2 S3 / D G`, and D3 as a plain rectangle with `K / A` — so device type and polarity are not visible as symbols, only as pin text. `RS1 10mΩ` renders correctly. | P2 | `pdf/schematic.pdf` full page at 140 dpi and a 1400x900 crop at 400 dpi | rendered and read both |
| 9 | **J5 is the tightest of the five connector fits.** From `twin_overlay_top.md`: J2/J3/J4 expected bodies reach `x = 152.512` against a board edge at `150.050` — **2.46 mm proud**, mouths clear. J5's expected body reaches `y = 112.266` against `112.050` — **0.216 mm proud**, i.e. effectively flush. Usable for an edge-mount USB-C, but it is the one connector with no clearance for a cable overmold, and it is an order of magnitude tighter than its neighbours. Worth one look in the JLC 3D preview. | P2 | `twin_overlay_top.md` J2-J5 rows; `twin_top.png` crop at J5 (5x); `TYPE-C-31-M-12_EdgeTrim.kicad_mod` | measured from the overlay's expected column, not from pixels |

**Counts — P0: 0 · P1: 3 · P2: 6.**

---

## The copper pour (the reason this release exists) — CONFIRMED, four layers

I was asked to say what I actually see. I see pour on all four copper layers, and the
four independent views agree:

- **`render_top_bare.png`** — the board reads as continuous red (copper) with black
  gaps. Tracks appear as red channels *bounded* by black clearance slots, which is the
  signature of a flood, not of bare substrate with tracks on it. Mounting holes H1-H4
  render as black discs, i.e. the pour is pulled back around them.
- **`render_bottom_bare.png`** — same, in blue: a continuous plane with clearance
  outlines, antipads and the three USB-A pin fields punched through.
- **`pdf/pcb_layers.pdf` p2 and p3** — **In1.Cu** (green) and **In2.Cu** (orange) are
  each a **solid full-board plane** with only via/pad antipads punched through. No
  splits, no starved regions, and the two pages are visibly different from each other.
- **`fab/…gerbers.zip`** — `F_Cu.gtl` 625 562 B, `B_Cu.gbl` 287 720 B, `In1_Cu.g1`
  174 761 B, `In2_Cu.g2` 269 172 B. All four substantial and all four different sizes.

Against the board: the saved `.kicad_pcb` holds **106 `filled_polygon` blocks**
(F.Cu 87, B.Cu 17, In1.Cu 1, In2.Cu 1). The inner planes are **In1.Cu = GND** and
**In2.Cu = VIN**, each one zone spanning the full `20..150 x 20..112` outline. The four
unfilled In2 zones are keepouts named `hole_vin_H1..H4` around the mounting holes —
legitimately unfilled, and the right way round: the **VIN** plane is cleared at the
screws while the **GND** plane runs to them, so a mounting screw contacts ground, not
the battery rail. `fab_payload_census.txt` grades v1.8 at `0/0/0/0` G36 regions against
v1.9 at `17/87/1/1`, all four gerbers distinct. Nothing I looked at suggests a
repeat of the v1.6-v1.8 defect.

---

## Checked and clean — so the absence is evidence

**Population (CPL vs render).** All 119 CPL designators resolve to a footprint on the
top side; `twin_bottom.png` and `pdf/assembly.pdf` p2 both show an empty bottom side,
matching `placement histogram: top=119` and `0 bottom footprints`. The three BOM
designators with no CPL row — **F1, SW1, R42** — are each declared in `MANIFEST.txt`
`not_assembled:` and given an individual rationale in `ORDER_README.md` §84-86
(F1: no JLC placement model, hand-solder; SW1: JLC's cached model is the wrong VG4
variant, fit by hand after measuring; R42: DNP by design, shipped loose, fit only if
bench gate Q9 fails). Note for future reviewers: these three **do** render with bodies
in `twin_*.png`, so on this board a *bodied* footprint does not imply "placed" any more
than a bodiless one implies "not placed".

**Polarity — netlist.** Every polarized part traced node-by-node out of
`usb_hub_3s_v2.net` and found correct: C1/C2 pin 1 POS→VIN, pin 2 NEG→GND; D1 (SMBJ15A)
K→VIN A→GND; D2 (BZT52C12) K→VIN A→RPP_G (Q1 gate); D3/D4 (1N4148WS) K→BOOT A→VCC;
D5 (SMBJ6.0A) K→VBUSC A→GND; D9-D12 K→GND, A→R38/R39/R40/R41; D8 K→LEDPKK→Q8 drain,
A→LEDPK→R37→VIN.

**On the `P-FACT FAIL` for D8** — I reached the same conclusion the release did, from
the netlist and without reading its adjudication: D8's pad 1 is the cathode and it sits
on `LEDPKK`, which is **Q8's drain** (Q8 source → GND, gate → ENKILL). That is a
switched low-side node, not a positive rail. The gate's closed net-name classifier
cannot express it. **This is a gate gap, not a board defect.**

**Polarity — render.** `twin_top.png` at 6x resolves two of the parts that
`twin_report.csv` marked `POLARITY-FIT-BLIND`:
- **C1/C2** — the silk `+` sits at the terminal *opposite* the model's red can marking.
  Consistent, and both caps are oriented identically.
- **D1/D2** — the model's cathode band is on the **pad-1 (left)** end, matching K→VIN.
- **D9/D10/D11** — silk cathode bar on the left (pad 1) end, all three identical, and
  matching K→GND at rotation 0. The 3D bodies themselves are unmarked, so the render
  cannot corroborate the LEDs; that is what `jlc_lcsc_rotations.csv`'s hand-measured
  two-channel derivation (`C2296,0` / `C2297,0`) is for, and it is present and reasoned.
- **J1** — `+` beside the upper barrel (pad 2 = PLUS at Y 36.8) and `\|` beside the
  lower (pad 1 = MINUS at Y 44). Correct.
- **U3/U4/U5/U6/U7/U8/U9/U10/U12** — pin-1 triangle present on silk on every one.

**Silkscreen.** All 129 `Reference` properties are on **F.SilkS** (7 hidden — H1-H4,
FID1-3), so the manufactured board carries 122 designators. KiCad DRC returns **0
violations with warnings included**, and `silk_over_copper`, `silk_overlap`,
`silk_edge_clearance`, `text_height` and `text_thickness` are all enabled at
`warning` in `usb_hub_3s_v2.kicad_pro` — so those checks ran and found nothing. Several
apparent silk-on-pad collisions I flagged from `render_top_bare.png` (C23, R29, R35,
R18) are **not** real: that render superimposes F.Fab text, which sits at the footprint
origin and therefore lands on the pads, while the F.SilkS copy is offset clear
(e.g. C23 footprint `(64.00, 70.00)`, silk refdes offset `(0, +1.6)`). I record this
because it is a trap: **`render_top_bare.png` is not a silkscreen-truth view.**
Finding 6 survives that correction because it was checked against the gerber text table.

**Board edge and connectors.** Outline is a plain rectangle, `20..150 x 20..112` mm
(130 x 92 plus the 0.1 mm cut line = the stated 130.1 x 92.1); no cutouts or notches.
`twin_edge_west.png` and `twin_edge_east.png` show no component-height conflict: USB-A
bodies stand ~7.1 mm above the board, C1/C2 ~7.7 mm, XT60 ~8 mm, nothing intersecting
and nothing fouling a neighbour. `twin_iso_nw.png` / `twin_iso_se.png` show all three
USB-A mouths and the USB-C mouth clear and unobstructed.

**Drill and clearance.** 320 PTH + 6 NPTH. Minimum PTH copper-to-edge **2.85 mm**.
J5's four shield legs are **routed slots** (`G01 … Y-110.35`, `drill oval 0.6 x 1.7`
and `0.6 x 1.2`), not point holes — they leave **1.15 mm** copper-to-board-edge, which
is fine. (I initially read these as missing from the drill file; that was my parser
ignoring routed slots, not a defect.)

**Mechanical.** H1-H4 are four 3.2 mm NPTH at `(26,26) (26,106) (106,24) (144,92)` —
board-relative `(6,6) (6,86) (86,4) (124,72)`. They are **not** at the four corners:
two are corner holes, one is mid-top 4 mm from the north edge, one is 20 mm up from the
south edge. That is asymmetric but it is clearly deliberate (they dodge the connector
fields), all four render with copper cleared, and all four have VIN keepouts on In2.
FID1-3 at `(33,29) (140,25) (145,105)` render as copper dot plus mask opening, clear of
parts and copper, and are correctly excluded from the CPL
(`FP_EXCLUDE_FROM_POS_FILES` — a fiducial on a CPL is a placement instruction for a
part that does not exist).

**PDFs.** `assembly.pdf` is 2 pages, front then back, and page 1 shows every one of the
119 CPL designators plus H1-H4 and FID1-3; page 2 is correctly an empty outline.
`pcb_layers.pdf` is 9 pages. `schematic.pdf` is 1 page. See findings 7 and 8 for their
quality.

**DRC.** `drc.json`: `"violations": []`, `"unconnected_items": []`,
`"schematic_parity": []`, severities `error + warning + exclusion`.

---

## What I would look at first

Finding 3 is the only thing here that changes what the hardware does, and it is already
a declared, quantified, bench-gated decision — my contribution is confirming the
arithmetic independently and pointing at the **5.479 V worst static corner** as an
attached-device question rather than only a U12 question.

Findings 1 and 2 matter more than their severity suggests, because they are the same
species as the defect that produced this release: **an evidence artifact that says
something other than what is true, next to a MANIFEST that repeats it.** A-POP cannot
pass on a first build because it reads the MANIFEST 21 minutes before it is written,
and `missing_models.txt` asserts a completeness it did not measure. Neither one broke
this board. Both would hide the next one.

VERDICT: PASS
