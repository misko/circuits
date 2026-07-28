# Changelog — usb-hub-3s-v3

Board internal name `usb_hub_3s_v2`; project directory `usb-hub-3s-v3`.

## v1.12 — 2026-07-28

Released: `07_releases/v1.12-2026-07-28/`. **COPPER MOVED, AND SO DID A
PLACEMENT COORDINATE.** `J5`'s land pattern was wrong in every release of this
board from v1.0 to v1.11, and is corrected here. The board file has a new md5
for the first time since v1.9 — `83af8e5a…` → `35ba862e…` — and v1.9's change
was a restored pour, not moved geometry; this is the first release since **v1.6**
whose copper features are in different places.

v1.11 gains `SUPERSEDED.md`. It is otherwise immutable, and it is **not**
DO-NOT-ORDER in the sense v1.6–v1.8 were (those shipped gerbers with no copper
pour at all). v1.11's boards would populate. What they would carry is an
elevated assembly-yield risk on the port that feeds the Pi — see "Is v1.11
unbuildable?" below, which answers that honestly rather than dramatically.

### What was wrong

`J5` is HRO `TYPE-C-31-M-12A` (LCSC **C5337088**) on footprint
`usb_hub_3s:TYPE-C-31-M-12_EdgeTrim`. That footprint was KiCad's stock
`Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12` with three silkscreen lines
deleted — verified, not assumed: `diff` against
`/usr/share/kicad/footprints/Connector_USB.pretty/USB_C_Receptacle_HRO_TYPE-C-31-M-12.kicad_mod`
returns the footprint NAME line and three removed `fp_line` records, and
**every pad record identical**. **The stock geometry does not match the part**,
and three independent sources say so:

| | pad length | pad row → alignment-hole line | hole ⌀ |
|---|---|---|---|
| HRO sheet `TYPE-C-31-M-12A` REV A 2022.10.26 | 1.140 | 1.070 | 0.60 |
| HRO sheet `TYPE-C-31-M-12` REV A 2020.12.08 (2 yrs earlier) | 1.140 | 1.070 | 0.60 |
| JLC / EasyEDA package `C5337088` | **1.14000** | **1.070102** | **0.59999** |
| **v1.0 … v1.11 as sealed** | **1.450** | **1.445** | 0.65 |

The board is the outlier by **+0.375 mm on the datum** and **+0.310 mm on pad
length**.

**The base `-12` sheet was read, not cited.** It matters because if the two HRO
part numbers had different land patterns, the stock footprint might have been
right for one of them. It is not: the 2020.12.08 `TYPE-C-31-M-12` drawing
(sha256 `6ae33d50…`) carries a **dimension-for-dimension identical** recommended
layout — `8-0.30`, `4-0.60`, `0.50`, `1.50`, `1.64`, `2.00`/`1.70`, `1.70`/`1.40`,
`0.60`/`0.90`, `Ø0.60`, `2.50`, `3.50`, `4.80`, `5.78`, `6.40`, `8.65`, `4.18`,
`5.79`, and the same "TOLERANCE FOR PCB LAYOUT IS ± 0.05" note. Two vendor
sheets two years apart, and both disagree with the stock footprint. (That PDF is
a working copy, not a committed artifact: the dossier this project owns is the
`-12A` sheet at `02_parts/TYPE-C-31-M-12A/`, which is the part actually bought.)

### Why that is not cosmetic

This connector **cannot self-align in reflow.** It is pinned by two Ø0.50
moulded posts in NPTH holes and four stamped shell legs soldered into plated
slots, so surface tension on twelve lands cannot pull it into place — the body
goes where the posts and legs put it, and the lands must be where the leads
land.

**JLC's own 3D model settles what the tails actually do**, and it corrects the
first version of this entry. Anchored on the part's own datum — the two Ø0.5000
posts, measured out of the mesh at x = ±2.8900, span **5.7800**, exactly the
sheet — the housing is 7.35 deep with the tail projecting **0.4000** past it,
which is the sheet's own top-view `0.40 ± 0.10` and makes the mesh 7.7500 deep.
So the **solderable contact tail runs 1.070 … 1.470 from the alignment line and
is 0.400 long** — and it lands **100 % on its pad in v1.11 as well as v1.12.**

Nothing hung off a land. What the stock pattern actually did was **invert the
fillet balance and over-paste the row**:

| | land | tail | heel (mouth side) | toe (past the tip) | paste vs spec |
|---|---|---|---|---|---|
| **v1.11** | 0.720 … 2.170 | 1.070 … 1.470 | **0.350** | **0.700** | **+27.2 %** |
| **v1.12** | 0.500 … 1.640 | 1.070 … 1.470 | **0.570** | **0.170** | — |

The heel is the end where the tail leaves the housing and where the fillet
carries the joint; the vendor puts the surplus there, and v1.11 put it at the
toe instead — starving the heel to 61 % of intended while doubling the toe. And
0.700 mm of every land and its open stencil aperture sat beyond the tail tip on
a **0.5 mm-pitch** row, on a part that cannot self-align. That is a
**bridge-and-fillet** exposure, not an open-joint one.

**This entry originally claimed the leads sat 0.220 mm off their lands, at
80.7 % overlap.** That was wrong, and it was wrong in a specific and instructive
way: the measurement equated the vendor's recommended LAND with the LEAD, so it
compared a land to a land and labelled the answer a lead. Its own output should
have given it away — it reported the corrected pattern as "100 % overlap, heel
0.0000, toe 0.0000", which would be a land with no fillet at either end, i.e. a
bad land pattern rather than the vendor's own. The fresh-context lens caught it
pre-seal (F-1); the numbers above are the re-measurement, and
`verification/lead_overlap.txt` carries the correction in full with the method.
The fix does not change. The story did.

### What moved, exactly

Only the pad row moved. **The connector body did not.**

| feature | v1.11 | v1.12 | source |
|---|---|---|---|
| pad row centre (from alignment line) | 1.445 | **1.070** | all three |
| pad length | 1.450 | **1.140** | all three |
| `A1/B12 ↔ B1/A12` centres | 6.50 | **6.40** | all three |
| `A4/B9 ↔ B4/A9` centres | 4.90 | **4.80** | all three |
| shell pad width | 1.00 | **0.90** | sheet + JLC |
| front shell pad height | 2.1 | **2.00** | sheet + JLC |
| rear shell pad / drill height | 1.6 / 1.2 | **1.70 / 1.40** | sheet |
| shell slot centre span | 8.64 | **8.65** | layout view + JLC |
| front shell slot from alignment line | 0.53 | **0.50** | sheet + JLC |
| alignment hole ⌀ | 0.65 | **0.60** | DECISION, below |

Unchanged and verified unchanged: pad pitch 0.50 and widths 0.30/0.60,
`A5↔A8` 2.50, `B8↔B5` 3.50, alignment span 5.78, slot separation 4.18,
front slot drill height 1.70, and **the whole F.Fab / F.CrtYd / F.SilkS body
outline, byte-for-byte**.

### The two decisions this release had to make

**1. Which feature moves.** The 1.070 separation can be restored by moving the
pad row *or* by moving the alignment holes. They are not equivalent.

The **alignment holes are the datum**, and in v1.11 their positions are right:
span 5.78, exactly the sheet's, and they are the feature the moulded posts
actually locate the body by. The four shell slots are body-referenced too, and
they were *not* perfectly right — front offset 0.53 against the sheet's 0.50,
centre span 8.64 against 8.65, and wrong pad/drill heights — so it would
overstate the case to call the hole/slot set flawless. But the scale separates
them cleanly: the slot errors are **0.03 mm, 0.005 mm and pad-size only**, on
0.60-wide plated slots taking ~0.3 mm stamped legs, while the pad row is out by
**0.375 mm** on a 0.5 mm-pitch row. One of those is a rounding inheritance; the
other is the defect.

So: the datum stays, the slots are corrected *relative to it*, and the pad row —
the outlier by an order of magnitude — moves to meet it. Moving the holes
instead would have carried the connector body, and therefore the USB-C mouth,
0.375 mm away from the board edge: a change to a **mating interface**, on an
edge-mount part, against eleven sealed releases of mechanical review. So the pad
row moved.

The mating face is stated and checked, not assumed: the alignment line sits at
board **y = 106.400** and the south edge at **y = 112.000**, so
**alignment-to-edge = 5.600 mm, identical in v1.11 and v1.12.** (The sheet's
nominal is 5.79; this board's 5.600 is a pre-existing edge position carried
from v1.0, and this release deliberately does not touch it — correcting a land
pattern and re-siting a connector are two different changes and only one of
them was reviewed.) The proof that the body did not move is structural rather
than narrative: the F.Fab, F.CrtYd and F.SilkS records and the 3D-model
reference are **byte-identical** to v1.11's, so there is nothing in the file
that *could* have moved it.

**2. Alignment hole diameter: 0.65 → 0.60, CHANGED.** ⌀0.65 was a defensible
choice, not an error: the sheet's layout view states its own tolerance as
±0.05, so 0.55–0.65 is vendor-sanctioned, and 0.65 buys post-entry clearance
against the Ø0.50 moulded post — a post that will not enter lifts the part off
all twelve lands, which is the worst failure available. It was defensible **in
the old geometry, where the pad row was 0.375 mm further away.** At the
corrected datum it is no longer free, and the number that decides it was
measured rather than argued: with the corrected pad row, KiCad's own shape
engine puts land `A1/B12` at **0.1944 mm** from the NPTH hole at ⌀0.65 — under
this board's `min_hole_clearance` of 0.200, so **DRC fails** — and at
**0.2194 mm** at ⌀0.60, which clears. Both were built and both were measured;
the ⌀0.65 variant is kept as the gate's known-bad fixture.

Two secondary reasons point the same way. JLC — who drill this board *and*
place this part — ship **0.600** in their own `C5337088` package. And the
lateral-play argument reverses at the true geometry: the sheet's contacts are
`16-0.20±0.05`, so a 0.20 mm lead on a 0.30 mm land has 0.05 mm of registration
margin per side, which is exactly what a ⌀0.60 hole on a Ø0.50 post preserves
and what a ⌀0.65 hole spends.

### Three corrections to the defect report this release was commissioned from

The brief listed the front slot offset (0.53), the slot span (8.64) and the
shell pad width (1.00) as already correct. Two of the three are not, and the
third is a real number read from the wrong view. All were re-measured before
being changed:

* **front slot offset is 0.50, not 0.53.** The sheet's own `0.50` dimension
  terminates on the pad-inner-edge line, and the front slot centre measures
  0.4 px — 0.004 mm — from that same line: they are one line. JLC agrees at
  0.500126. 0.53 is a stock-KiCad inheritance with no support in either sheet.
* **slot centre span is 8.65, not 8.64.** Both numbers are on the sheet and
  they are different dimensions: `8.64` on the FRONT VIEW is the **part's leg
  span**; `8.65` on the RECOMMENDED LAYOUT view is the **slot centres**. JLC
  reads 8.64972. A footprint takes the layout view's.
* **shell pad width is 0.90, not 1.00** — this one the brief did not list as a
  delta at all, but it names JLC's 0.900 × 2.000 in passing. The sheet
  dimensions it too, at the rear-left slot: `0.90` pad over `0.60` drill.

None of the three is large (30 µm, 5 µm, 100 µm). They are recorded because a
land pattern authored from a drawing should contain the drawing's numbers, and
because "already correct" claims that turn out to be inherited are exactly how
the 0.375 mm survived twelve releases.

### The second defect, which nobody had named

Correcting the land pattern turned out to correct something else that was
wrong for the same reason, and it is arguably the worse of the two.

`export_jlc_package.py` emits a CPL `Mid X`/`Mid Y` that is **the centre of the
bounding box of the pad centres**, not KiCad's footprint anchor — because JLC
places a part so that **its own model origin** lands on that coordinate. (That
convention is measured, not assumed: 227 of 228 JLC footprints across this
fleet, and it exists in this repo because `crow-recorder-central-v2` v1.4
shipped a USB-C 1.3025 mm off and unable to seat.)

The pad centres were wrong, so the datum computed from them was wrong:

| | datum, measured from the alignment-hole line |
|---|---|
| JLC's own `C5337088` model origin | **+1.30492 mm** |
| v1.11's emitted CPL row for J5 | +1.10250 mm — **0.2024 mm off** |
| v1.12's emitted CPL row for J5 | +1.30500 mm — **0.00008 mm off** |

v1.11 therefore told the placement machine to set the connector **0.2025 mm
north of where its own alignment posts sit**, and those posts have only
0.075 mm of radial clearance in v1.11's ⌀0.65 holes — so the commanded position
is one the part cannot physically occupy.

**These are two independent failure modes, not one error that adds to the
other**, and it is worth being exact about that rather than stacking the numbers
for effect. The land error mis-registers every joint on a part that is already
seated. The placement error asks the machine to put the part where its posts
will not go. Which one you actually get depends on whether the posts or the
pick-head win, and this project cannot determine that from here — a chamfered
post in a 0.65 hole may well be dragged into place by 0.2 mm, in which case the
placement error is absorbed at the cost of scrubbing the lands, and only the
0.375 mm land error survives to the joint. Both are fixed; neither needed the
other to justify the release.

**No gate could have caught it**, and the reason is canon M1 rather than an
oversight: `A-POS` recomputes the datum from the same board it is grading, so
it is self-consistent by construction — v1.11's MANIFEST reads *"A-POS datum:
119 rows graded, worst residual 0.00050 mm"* and that number is true and means
nothing here. Checker and checked shared a method. The comparison that does
have force is the one above: our datum against **JLC's**, computed from their
package rather than from ours.

`fab/cpl.csv` therefore is **not** byte-identical to v1.11's: J5's `Mid Y`
moves 107.5025 → 107.7050. That single row is the whole CPL delta.

### Verified two ways, with no shared code

The footprint is **authored**, not copied. (`pluto-rx2-8way` holds a correct
`TYPE-C-31-M-12A` from the same drawings; it was read as precedent and no byte
of it was taken — files are never copied between projects.)

* **Instrument A** — a purpose-written s-expression tokeniser over the raw
  `.kicad_mod` **text**, compared against dimensions retyped by hand off the
  sheet. It never imports `pcbnew`.
* **Instrument B** — `pcbnew.FootprintLoad` plus KiCad's own shape engine. It
  never reads the file as text.

**127 checks, 0 failures.** Both instruments independently confirm the datum at
1.0700 and the pad length at 1.1400.

**The gate was proved able to fail, twice.** Fed the v1.11 footprint exactly as
sealed (`git show HEAD:…`) it goes red and names the defect —
`PAD ROW → ALIGNMENT got 1.4450 want 1.0700 d=+0.3750`, pad length +0.3100 on
all sixteen lands, wide-land x ±0.0500. Fed the corrected footprint with only
the hole reverted to ⌀0.65, it goes red on the clearance measurement above.

The vendor sheet was also measured **as a raster**, independently of both
instruments and of JLC: page 1 at 600 dpi, scale calibrated on four pad-centre
spans that agree to 0.15 % (S = 105.1268 px/mm), intensity-weighted sub-pixel
centroids. Datum 1.0654, pad length 1.1415, front slot offset 0.4985, slot span
8.6510, hole ⌀ 0.5994. That reading is what refuted 4.90/6.50 outright: at the
scale set by the narrow-pad pitch alone, the wide-pad spans read 4.8095 and
6.4095, and 4.90/6.50 would be 9.5 px away.

### Why no gate caught this, and why `jlc_twin` will not catch it now either

`jlc_twin` is the gate whose whole job is comparing our footprint to JLC's, and
it reported **`fit=0.00mm` on J5 on the defective board.** It is not a tuning
problem, it is **structurally blind to this class**, in two independent ways:

* `pads_of()` drops unnumbered pads, so the two NPTH alignment holes — the
  datum the whole defect is measured against — never enter the fit at all;
* `centered()` removes the centroid from both point sets before comparing, so
  the comparison is **translation-invariant by construction**. A pad row
  displaced 0.375 mm *as a rigid group*, relative to features the fit cannot
  see, is exactly the thing that survives a centroid-removed match;
* and — raised by the fresh lens, then measured here — **JLC names its pads
  differently, so the correspondence set is not just small but degenerate.**
  Their package names its lands `{1, A1/B12, A4/B9, A5, A6, A7, A8, B1/A12,
  B4/A9, B5, B6, B7, B8}`; ours are `{A1, A12, A4, A5…A9, B1, B12, B4…B9, SH}`.
  The intersection is **eight names** — A5…A8, B5…B8 — and **all eight are
  collinear** (their y = 2982.205, ours = −3.670, one value each). After
  `centered()`, the fit is eight points on a line against eight points on a
  line: it carries no information at all about where that line sits on the only
  axis this defect lives on.

**So a fix that merely stops dropping unnumbered pads will not close this.** The
gate needs a numbering-free landmark fit — which this repo already has, in
`export_jlc_package`'s `placement_datum` cross-check.

It is run in this release and it passes, and its verdict is **not** evidence
about the datum. This gate gap is reported and already queued; it is
deliberately **not** patched inside a board fix — `skills/` changes and board
changes do not belong in the same commit, and a gate rewritten by the agent
whose work it is about to grade is not a gate.

Nothing else was positioned to catch it either: DRC grades copper against
copper and the wrong pattern is internally consistent; `escape_check` grades
pitch and escape geometry, which were right; the pin review grades the pad-name
→ net map, which was right. **The land pattern itself had no checker.** The
two-instrument gate written for this release is the first thing in this repo
that reads a vendor drawing's numbers and compares them to emitted copper.

### Exposure elsewhere — RECORDED, NOT FIXED HERE

The same defective footprint file, **byte-identical** (md5
`7aebd381d4637d498f8d9fdf9a6ea0ab`), is carried by two sibling projects that
are **not in this release's scope**:

* `projects/usb-hub-3s/03_src/lib/usb_hub_3s.pretty/TYPE-C-31-M-12_EdgeTrim.kicad_mod`
  — and that project has a **sealed release, `v1.0-2026-07-21`**, so a sealed
  archive there carries the defect.
* `projects/usb-hub-3s-v2/03_src/lib/usb_hub_3s.pretty/TYPE-C-31-M-12_EdgeTrim.kicad_mod`
  — no sealed release.

Both measure the same 1.4450 datum, 1.45 pad length and ⌀0.65 hole. Within this
project, **all twelve sealed releases v1.0 … v1.11 carry it** (md5 identical in
every `source/usb_hub_3s.pretty/`). Recording it here so the finding does not
die with this release; fixing those boards is their own change, with their own
gates and their own reviews.

### Is v1.11 unbuildable? No — and that is not the same as fine

Stated plainly, because "DO-NOT-ORDER" has been used on this board before for a
genuinely different reason (v1.6–v1.8 shipped gerbers with no copper pour) and
the two should not be blurred.

v1.11's boards **would populate**, and the bare PCB is a perfectly good PCB.
The holes and slots are in the right places, so a connector pushed home by hand
seats correctly, and every contact tail then sits **100 %** on its own land.
What v1.11 buys is elevated **assembly-yield** risk on the port that feeds the
Pi: 0.700 mm of open stencil aperture per land beyond the tail tip, 27 % more
paste than the vendor specifies, on a 0.5 mm pitch, is a bridge waiting for a
reflow profile to find it — and the heel fillet, the one that carries the joint,
is starved to 0.350 mm where the vendor asks for 0.570.

**The honest uncertainty is the placement half, not the land half.** v1.11's CPL
asks the machine for a position the part cannot occupy (0.2025 mm against
0.075 mm of radial post clearance). Either the posts drag the part into the
holes — in which case the placement error is absorbed and you get the land error
described above — or they do not, and the part is set down proud on its posts.
We cannot tell which from here, and it would take a built board to find out. The
worse branch is the reason this release exists rather than a note in the
ORDER_README.

So: a defect worth a new release and a `SUPERSEDED.md`. It is not a board that
cannot be built, and this entry does not claim it is.

**Order v1.12.**

### What moved in the fab payload, measured three ways

| artifact | v1.11 → v1.12 |
|---|---|
| `fab/bom.csv` | **byte-identical** — no part changed |
| `fab/cpl.csv` | **one row**: `J5` `Mid Y` −107.502 → −107.705 |
| `fab/*_gerbers.zip` | 11 of 13 members changed; `Edge_Cuts.gm1` and `B_Paste.gbp` **byte-identical after the plot-timestamp strip** |
| `fab/*-NPTH.drl` | the alignment-hole tool, ⌀0.65 → ⌀0.60 |
| `fab/*-PTH.drl` | the four shell slots |
| netlist | **0 differences** — 122 components, 73 nets, 372 nodes, identical |

The copper that moved was bounded exactly, with KiCad's own polygon booleans
rather than a text diff (the zone filler re-emits its region polygons in an
arbitrary order, so a line diff on a copper gerber is noise):

```
COPPER-POUR SYMMETRIC DIFFERENCE (SHAPE_POLY_SET XOR, saved filled polygons)
  F.Cu     3.5905 mm2   regions not wholly inside the J5 corner: 0.000001 mm2
  In1.Cu  10.0333 mm2                                            0.000000 mm2
  In2.Cu   9.4501 mm2                                            0.000000 mm2
  B.Cu     5.0280 mm2                                            0.000968 mm2
  TOTAL   28.1019 mm2   outside the J5 corner: 0.000969 mm2  (0.0034 %)
```

Every XOR region of meaningful area (≥ 0.0001 mm²) lies in a tight box around
J5 — F.Cu x 114.840–125.160, y 103.862–107.106. The 0.000969 mm² remainder is
174 zone-filler slivers, the largest 78 × 16 µm: re-triangulation noise, not
geometry. And independently, at the pcbnew level: `Edge_Cuts` **identical**,
**0** footprints moved, exactly **one** footprint's pads changed, **0** tracks
and **0** vias changed outside the J5 corner, with the track delta confined to
`CC1 / CC2 / DPC / DMC` — the four nets `route.yaml` hands to the deterministic
tap router precisely because *"CC + interleaved D+/D- edge pads defeat KRT"*.

### Routing: why KRT was not re-rolled

J5's nets are **not** KRT-routed. `route.yaml` `waves.exclude` names
`CC1, CC2, DPC, DMC` verbatim and VBUS/GND are pour-owned, so the affected area
belongs to the deterministic tap pass, which re-derives from pad positions on
every build. Verified rather than assumed: the promoted chain
`03_src/route/final_chain.kicad_pcb` holds 504 items across 44 nets with **zero**
items on those nets and **zero** endpoints anywhere in the J5 corner box. So
`rebuild_fast.sh`'s stated validity condition — *"valid ONLY while KRT-routed
pins do NOT move"* — holds, and re-rolling KRT would have replaced 504
stochastic, already-reviewed items with 504 unreviewed ones for no benefit and
destroyed the fix-pass diff above.

### Gates

```
DRC          0 violations / 0 unconnected / 0 schematic-parity
             (--severity-all --refill-zones --schematic-parity)
ERC          0 errors, 221 warnings — all lib_symbol_issues, identical to v1.11
audit_board  PASS — 21 polarity, 19 proximity, 4 edge, 129 silk
netlist      PARITY 0 — 122 components, 73 nets, 372 nodes; board-vs-board 372/372
J5 geometry  PASS — 127 checks, 0 failures, two instruments sharing no code
             + 2 RED-verifies that make the gate fail on demand
rules_audit  PASS — 0 fails, 32 checks; A-AMP 10/10; A-ORDER generate_rules last
F-PAYLOAD    OK — 5 checks on the SHIPPED zip; F-POUR B/F/In1/In2 = 17/87/1/1
             G36 regions, all four copper gerbers distinct
A-ROT        119/119 CPL rotations sourced from measured per-LCSC rows
A-POS        119 rows, worst residual 0.00050 mm (Q6), tol 0.05 mm
A-BODY       bodies mounted 119/119
M-BOM        bom_source_check PASS — 46 lines, 0 without LCSC
F-LEGIBLE    OK — 48 checks; 46/46 MPNs resolved, 46/46 Comments readable
A-STOCK      PASS — 46/46 coded lines. READ THE CAVEAT: this is CATALOG stock
P-FACT       FAIL 1 — KT-0805Y/D8, pre-existing, adjudicated, unchanged
A-RENDER     29 unfaithful refs — pre-existing and IDENTICAL to v1.11's 29,
             adjudicated as 0 board defects; COVERAGE 53/121, unchanged
jlc_twin     exit 0, 119/119 bodies — and see below, its J5 verdict is not evidence
```

**`jlc_stock_check` on `C5337088` now reads 84**, down from the 104 recorded at
v1.11 and against the 0 JLC's assembly side allocated at the real upload. The
gate PASSES it (84 ≥ 5 × 1). That is exactly the necessary-and-not-sufficient
verdict v1.10 → v1.11 taught this board to distrust, and the tool now prints its
own scope caveat. **J5 remains a pre-order line.** The gate reads LCSC catalog
stock; JLC's assembly uploader allocates from a different pool; F-ECHO at upload
is the only instrument that settles it.

### What the fresh-context lens changed

The FIX-PASS lens ran against the staged archive before the seal and returned
**ORDER-WITH-CONDITIONS, no P0**. It re-derived every dimension by methods that
share no code with this release's gate — `pdftocairo -svg` **vector** extraction
of the sheet (5036 paths, 0 images, so it never touched a raster), its own
EasyEDA parser, its own `.kicad_mod` re-parse — and confirmed the corrected
copper on every number, plus 5.600000 mm alignment-to-edge on both boards and
the 0.2194 / 0.1944 / 0.4200 clearance figures. Its conditions were all pre-seal
edits and all of them are in this release:

| | what it found | what changed |
|---|---|---|
| **F-1** | the severity narrative was a tautology — see "Why that is not cosmetic" | `lead_overlap.txt` rewritten from the part's own mesh; every derived sentence corrected in the MANIFEST, ORDER_README, `part.yaml`, `SUPERSEDED.md` and **the footprint `descr`**, which forced a rebuild because it lives inside the board file |
| **F-2/F-3** | `policy_audit.md` absent; the MANIFEST said `A-POP: PASS` while the shipped gate file said FAIL | both are post-stamp artifacts by construction; the stamp step generates them in the right order and the archived copies are those re-runs |
| **F-4** | `gerber_payload_delta.txt` asserted "every geometric change lies inside the J5 corner" directly above its own count of **494** that do not | reworded to defer to the XOR area bound, which is the representation-free measurement |
| **F-5** | `min_hole_clearance: 0.200` has no fab provenance — `fab_tiers.yaml` models no hole-to-copper capability at any tier | **accepted.** Decision 2 stands on the vendor's ⌀0.60 nominal and JLC's own ⌀0.59999, not on the DRC number; 0.2194 is inherent to the vendor's own layout (0.500 − 0.300 = 0.200 axial by construction). Filed as a missing `fab_tiers.yaml` field |
| **F-6** | JLC gives **all four** shell slots at 2.00/1.70, disagreeing with both sheets on the **rear** pair, and no document said so | stated in the MANIFEST. The footprint follows the sheet; JLC's package is the simplification, and 1.40 leaves 0.30 mm/end on an 0.800 leg where v1.11's 1.20 left 0.20 |
| **F-7** | the **F.Courtyard is stale** — kept byte-identical by design, but sized for the old land row: north margin 0.500 → 1.030 mm | declared, not changed. Changing it would perturb the very graphics the mating-face proof rests on. Next revision re-derives it |
| **F-8** | J5's twin metrics moved (MODEL-REG 0.05 → 0.33 mm, overlay excursion 0.049 → 0.326); "identical to v1.11" was true of the set, not of J5 | declared, with the cause (F-7) |
| **F-9** | "deliberate" was asserted for the 5.600 mm mating face with no decision record behind it | reworded to "pre-existing and untouched" everywhere, with the direction stated: the mouth overhangs 0.680 where the vendor intends 0.490 — *more* plug clearance, not less |
| **F-10** | the base `-12` sheet row pointed outside the archive without saying so | the MANIFEST's source table now footnotes all three rows with where they live |

One finding I verified and **refined rather than accepted**: it read the
`jlc_twin` correspondence set as *empty*. It is not empty — it is eight collinear
points, a sharper and slightly different failure, and the text above says so.

### Still open, unchanged by this release

`U11`/`U2` `C13755` (LM5116) — catalog stock but JLC assembly 0, pre-order or
consignment, no substitute. `J5` `C5337088` — catalog 84, allocated 0 at the
last upload; if it cannot be pre-ordered the footprint-compatible fallback is
`C165948` `TYPE-C-31-M-12` at 5 A instead of 6 A, and **that fallback is now
safer than it was**, because the two HRO sheets carry a dimension-identical
recommended layout and this release's footprint is authored to it. `R42`/`F1`/
`SW1` off the CPL is deliberate and declared. The A-POL single-channel
order-preview human gate and the In1_Cu/In2_Cu viewer check stand as v1.11 left
them. `C2984354`/R12 twin FETCH-FAILED, identical to v1.11 — a network failure,
not a finding.

## v1.11 — 2026-07-27

Released: `07_releases/v1.11-2026-07-27/`. **ONE OUT-OF-STOCK PASSIVE SUBSTITUTED
FOR AN ELECTRICALLY IDENTICAL PART. NO COPPER CHANGE.** v1.10 gains
`SUPERSEDED.md`; it is otherwise immutable and it is **not** DO-NOT-ORDER — its
board is this board. It is *unorderable as a PCBA*, which is a different thing.

### Why

v1.10's `fab/bom.csv` was uploaded to JLCPCB and line 8 came back **"10
shortfall"**: `C25744`, the 10 kΩ 0402 on **R28/R29**, the USB-C CC1/CC2 Rp
pull-ups. JLC's parts API, re-queried 2026-07-27, reports **`stockCount: 0`**.
It was the **only basic-library 10 kΩ 0402 in the catalog**, so every
replacement is an Extended part; the one-time feeder fee is accepted.

| | C25744 (out) | **C60490 (in)** |
|---|---|---|
| MPN | `0402WGF1002TCE` UNI-ROYAL | **`RC0402FR-0710KL` YAGEO** |
| stock | **0** | **8 220 334** |
| library | base | **expand** |
| `leastPatchNumber` | 20 | **20** |
| price @1–999 | $0.0020 | $0.0058 |
| `describe` | `-55℃~+155℃ 10kΩ 50V 62.5mW Thick Film Resistor ±1% ±100ppm/℃ 0402 Chip Resistor - Surface Mount ROHS` | **character-identical** |

Both records read live 2026-07-27 (`selectSmtComponentList`, exact
`componentCode`); the two `describe` strings were compared **as strings** and are
equal. Same package, value, tolerance, tempco, power, voltage — a true drop-in.

### Changed at SOURCE, never in the csv (canon M3)

The edit is two `supplierPartNumbers` in `03_tscircuit/src/usb_hub_3s_v2.tsx`;
`circuit.json` was regenerated by `tsci build` and the BOM row by
`export_jlc_package.py`. A `bom.csv` that moved without its `.tsx` moving would
be a hand-edited BOM — the defect crow-mic-pod-v2 paid for on this same day.

New: **`02_parts/RC0402FR-0710KL/part.yaml`**, with the VALUE claim carrying its
provenance (S-VER / M-IMPORT). A 2-terminal passive has no pin map to derive, so
the fact needing a grade is the value, and it has two independent readings — the
MPN decode (`10KL` → 10 × 10³, `F` = ±1%) and the live catalog query, M-QUOTE
grade **CITED**. Its `asserts: value 10k` block is executable and was
**RED-VERIFIED** at the seal: rewriting the BOM Comment to `22kΩ` in a scratch
copy makes `part_facts_check` FAIL naming R28 and R29. 22k is not an arbitrary
wrong value — it is the USB Type-C **1.5 A** Rp, so the assert refuses exactly
the substitution that would silently downgrade this port.

There was **no `0402WGF1002TCE` dossier to retire**: `C25744` never had one here,
resolving instead through the vetted passives ledger, which is what that ledger
is for. The ledger row **stays** — append-only, and eleven sealed releases across
three boards still reference the code. `02_parts/0402WGF1603TCE/part.yaml` (R42,
a different code, DNP) cross-referenced `C25744` inside its `verified:` note;
that measurement is left intact and a dated gotcha records that the code moved
while the R0402 geometry it cited did not.

### What did NOT change, measured

* `source/usb_hub_3s_v2.kicad_pcb` md5 `83af8e5a5596a51cf139dd06e8903d47` —
  identical to v1.10's **and** to `04_kicad/`'s.
* Gerbers + drills **re-plot** from this release's own source **15/15
  byte-identical** to v1.10's sealed zip after the timestamp strip.
* `fab/cpl.csv` byte-identical (119 rows). `fab/bom.csv`: 46 → 46 rows,
  designator list identical in order, **two cells changed**, both on `R28,R29`;
  0 Footprint changes, 0 Comment changes, 0 rows added or removed.
* The schematic **cannot** change under this edit, verified not assumed: the
  LCSC code appears nowhere in the `.kicad_sch`, and re-running the bridge
  converter on the new `circuit.json` reproduces the committed sheet with 0
  differing lines after normalising UUIDs and the title-block date.
* `circuit.json`: 3604 non-warning elements, exactly **3** substantive deltas —
  R28's and R29's `supplier_part_numbers` and `source_filesystem_md5_hash`.

### The gate lesson

`jlc_stock_check.py` **PASSED that line at the v1.10 seal**, hours before JLC
refused it: `{"lcsc": "C25744", ..., "status": "OK", "stock": 291}`. The figure
it reads is `stockCount`, LCSC's **catalog** stock, and it does not predict
whether JLC's assembly uploader will clear a line. A FAIL from it is real; a
PASS is necessary and not sufficient. C60490's 8.2 M is two to four orders of
magnitude above the 291 that failed, which reduces the risk without eliminating
the class. Teaching the gate to read the assembly-side figure is a **separate**
change, named rather than folded in here.

`release_freshness_check` likewise has **no supersede mode for a substitution**
(`--legible-bom` explicitly FAILS a changed LCSC, because when it was written a
changed LCSC could only be the C82317 accident). This release is gated with
seven documented, individually measured exceptions instead, and
`verification/freshness_exceptions.txt` says so out loud. A
`--substitution-supersede` mode is filed as a follow-up.

### Still open, unchanged by this release

U11/U2 `C13755` (LM5116) — catalog 7275, JLC **assembly** stock 0, needs
Pre-order or consignment, no substitute. U3/U4/U5, Q1/Q6, Q2–Q5 share the
`leastPatchNumber: 0` signature, unconfirmed. J5 `C5337088` showed 0 at upload,
catalog now 104. R42/F1/SW1 off the CPL is deliberate and declared. The A-POL
single-channel order-preview gate and the In1_Cu/In2_Cu viewer check stand as
v1.10 left them.

## v1.10 — 2026-07-27

Released: `07_releases/v1.10-2026-07-27/`. **BOM-LEGIBILITY supersede of v1.9.
NO COPPER CHANGE.** v1.9 gains `SUPERSEDED.md`; it is otherwise immutable and it
is **not** DO-NOT-ORDER — its board is this board.

### Why

Canon **F-LEGIBLE** (ADR-0006): a fab artifact is graded as its RECIPIENT will
parse it, not as we wrote it. v1.9's `fab/bom.csv` carries **26 findings**:

| check | findings | what JLC saw |
|---|---|---|
| F-WORDS | 21 | the Comment is an LCSC code — 21 of 46 rows unreviewable by a human on either side |
| F-MPN | 4 | `C25757`/R42, `C2296`/D8, `C2297`/D9–D12 ship a **blank MPN** despite having `02_parts` dossiers (JLC: *No Part Selected*); and **SW1 ships `SS12D07VG6 087` with a SPACE** where `02_parts/SS12D07VG6-087` says a HYPHEN |
| F-ENCODE | 1 | `Ω` with no UTF-8 byte-order-mark — a cp936 reader sees `惟` |

v1.10 ships **0 findings**: 46/46 coded rows carry an MPN from the dossier or the
vetted passives ledger, 46/46 Comments read, byte-order-mark present.

The SW1 space-vs-hyphen is the one that matters most and is unique to this
board: usb-hub-3s-v3 is the **only** project that ever created the retired
`lcsc_mpn_map.csv` side-file, so it is the only one where a second home for the
MPN could drift from the first. This is why F-MPN requires the two match paths to
AGREE and not merely to be non-empty — a blank-only check passes that row.

### What did NOT change, measured

* `source/usb_hub_3s_v2.kicad_pcb` md5 `83af8e5a5596a51cf139dd06e8903d47` —
  identical to v1.9's **and** to `04_kicad/`'s.
* Gerbers + drills **re-plotted** from this release's own source: **15/15
  byte-identical** to v1.9's sealed zip after stripping the plot timestamp
  comments — the restored pour (36 zones / 106 filled outlines) included.
* `fab/cpl.csv` byte-identical; every A-ROT rotation and A-POS coordinate
  carried forward unchanged. 21 of 22 payload files sha256-identical.
* Asserted mechanically by `release_freshness_check.py --legible-bom-supersede`,
  a mode added for this class: only `Comment` and `MPN` may move, and a changed
  `LCSC` (a substitution) or `Footprint` FAILs.

No source change was needed on this board — all 29 dossiers already declared
their code under `sourcing:`, so the MPN column is filled entirely from
artifacts already in the tree.

### Still open, unchanged by this release

The A-POL single-channel JLC order-preview human gate (C130056, C13755, C473910,
C7519, C98732), the order-day stock recheck, the In1_Cu/In2_Cu gerber-viewer
check — and now **F-ECHO**: after uploading, diff JLC's own resolved part table
back against ours (`verification/bom_echo_gate.txt`, 46 lines).

## v1.9 — 2026-07-27

Released: `07_releases/v1.9-2026-07-27/`. **DO-NOT-ORDER supersede of v1.8, v1.7
AND v1.6.** All three gain `SUPERSEDED.md`; they are otherwise immutable.

### The defect: three sealed releases with NO COPPER POUR

v1.6, v1.7 and v1.8 shipped gerbers carrying **zero copper pour on all four
layers — 44287.91 mm2 of missing copper**. No GND plane, no VIN plane, no
5VA/5VC/VBUS/switch-node islands. On such a board the 7 A battery trunk and the
6 A rails exist only as the thin routed stubs that were never meant to carry
them, and the return path does not exist at all.

**Root cause:** `03_src/post_stitch_fixes.py` section 6, added in v1.6, unfills
the zones so it can place vias and never refills before its own save. That script
holds the **LAST** save in the pipeline, so the refill guard inside the stitch
driver guarded nothing.

**Why every gate stayed green:** `kicad-cli pcb drc --refill-zones` refills the
zones **IN MEMORY**. It reports 0/0/0 on a board whose saved file has no fill.
DRC, parity, twin, renders, ERC and the policy audit were all measuring an
in-memory board that was correct while the bytes on disk were not.

**The signature was in the shipped payload the whole time.** v1.8's `In1_Cu` and
`In2_Cu` gerbers are BYTE-IDENTICAL at 18921 bytes — a GND plane and a VIN plane
cannot be the same file unless neither contains a plane.

### The fix, and the two gates that make the class impossible

* **M-SHIP read-back** (`route_and_stitch_generic.py verify-fill`): reopens the
  saved `.kicad_pcb` AS TEXT and counts `filled_polygon` blocks. Text rather than
  pcbnew deliberately — pcbnew is the tool whose save behaviour is under test
  (canon M1). Wired into `rebuild_fast.sh` and `rebuild_all.sh`.
* **F-PAYLOAD** (`fab_payload_census.py`, canon F-POUR/F-IDENT): opens the
  shipped **zip** and grades it against the board. The only gate downstream of
  the export, and the one that closes the loop.

MEASURED, both releases graded side by side in
`verification/fab_payload_census.txt`:

| | v1.8 | v1.9 |
|---|---|---|
| F-PAYLOAD | **FAIL: 5 findings, 0 ok** | **OK: 5 checks passed** |
| G36 regions B.Cu / F.Cu / In1.Cu / In2.Cu | 0 / 0 / 0 / 0 | **17 / 87 / 1 / 1** |
| F-IDENT | inner layers byte-identical at 18921 B | all 4 copper gerbers distinct |
| saved-board read-back | 0 `filled_polygon` | **36 zones, 106 `filled_polygon`** |
| gerber zip | 88 692 B | **394 534 B** |

**Nothing electrical changed.** Netlist parity vs v1.8 is **0 differences**
(122 components, 73 nets, 372 nodes) and `fab/cpl.csv` is byte-identical.

### Also in v1.9 — four gates that did not exist when v1.8 sealed

* **A-AMP now grades 10/10 net-class currents** (was 3/10: the parser could not
  read any declaration carrying a qualifier, so "7 A worst case", "6 A / 5 A" and
  "7 A pulsed" were silently unchecked). PWR_IN, PWR_RAIL and SWITCH_NODE are now
  declared `pour_fed:` with cross-sections MEASURED on this board with pcbnew:
  narrowest 8.750 mm (VBAT), 9.300 mm (PMID) and 6.050 mm (SW_A) against
  IPC-2221 requirements of 4.399 / 2.765 / 4.399 mm. **VBUS and GATE are NOT
  pour-fed and are not declared so** — VBUS reaches its port pour through one
  0.800 mm B.Cu track per port (8.810 mm of it standalone copper), redeclared at
  the design's own 2 A continuous (dT 9.6 C; the 2.5 A burst is dT 16.0 C, stated
  and handed to bench gate Q4b); GATE is 100 % track and was failing only because
  a 2 A switching peak was being read as continuous — I_rms is 0.276 A.
* **S-COUNT parity restored 4-way.** The v1.6 status-LED cell was never added to
  `03_tscircuit/manifest.yaml`: **12** refs (Q8, R37-R42, D8-D12), not the 8 the
  audit reported — `count_parity.py` prints `extra[:8]` and truncates.
* **A-RENDER** (`twin_overlay.py`) run for the first time, both sides. 29 refs
  flagged, **0 board defects**; the bottom side correctly REFUSED (no populated
  bottom). Per-class adjudication with the crops examined:
  `verification/gate_adjudications_v1.9.md`.
* **`pdf/schematic.pdf` is tscircuit's own render again** (ADR-0002). v1.6-v1.8
  regressed to an Eeschema re-render (`Creator: Eeschema-PDF`) and A-EVID passed
  it because A-EVID checks the FILENAME, not the producer.
* **`verification/rules_audit.txt` ships** — v1.8 shipped none while A-AMP failed.
* **`verification/bom_source_check.txt` PASSES again** after the 10 mOhm shunt
  C127692 was catalog-verified into the fleet passives ledger; leg C had started
  grading milliohms and read the row as UNVERIFIABLE-VALUE.

### The three pre-seal lenses, and what they cost in EDITS

Three zero-context reviews were run against the STAGED archive before the seal —
pin review **PASS-WITH-NOTES**, render review **PASS**, integrated red-team
**ORDER**, **no P0 in any of them**. That timing is the whole point: `07_releases/`
becomes immutable at the seal commit, so **a finding here costs an edit and the
same finding afterwards costs a supersede**. Every item below was fixed at
SOURCE (canon M3) and propagated. **The board did not change** —
`source/usb_hub_3s_v2.kicad_pcb` is md5 `83af8e5a5596a51cf139dd06e8903d47`,
identical to `04_kicad/`; DRC 0/0/0; 106 `filled_polygon` blocks in the saved
text.

**P1 — the OFF-state budget was 2.6× low, and the bench gate it fed COULD NOT
PASS.** `power_tree.yaml` declared `quiescent_ua: 271`. It omitted the two
LM5116 **UVLO dividers** — `R6+R7` and `R15+R16`, each 49.9 k + 6.98 k =
**56.88 kΩ**, sitting **permanently across VIN**. SW1 gates ENABLE, not power
(pad 1 = T1→GND, pad 2 = COM→ENKILL, pad 3 unconnected; no pole touches
VBAT/VBAT_F/VIN), so both conduct for the whole of storage:
`12.6 V / 56 880 Ω = 221.5 µA` each = **443.0 µA** that was never counted.
Corrected to **714 µA typ / 744 µA countable worst**; storage life on a 3S
5000 mAh pack is **292 days to flat / 233 to the 20 % LiPo floor**, not 769/615.

**The serious part is the gate, not the number.** ORDER_README bench **Q6**
declared *"PASS ≤ 300 µA"* — a threshold a correctly-built board **cannot
meet**. A gate that cannot pass is the same defect class as a gate that cannot
fail, and this one would have condemned a good board. Q6 is re-based to
**≤ 1.00 mA**, derived rather than picked: worst-case-good 744 µA;
weakest-possible-bad 1461 µA (Q8 failed, pack LED lit, at the *weakest* corner
VIN 9.0 V / Vf 2.4 V); `sqrt(744 × 1461) = 1042` → 1.00 mA sits **1.34× above
good and 1.46× below bad**. It carries a **1.00–1.45 mA INDETERMINATE band with
a discrimination step** (lift D8 and re-measure), because two terms — the D2/R1
zener leg and **C1/C2 polymer leakage, which has no entry in its `part.yaml` at
all** — are unbounded in the record and are NAMED rather than silently zeroed.
Root cause reported upstream: `power_topology.py grade_off_control()` checks
only that `quiescent_ua` is *declared*, never that it reconciles with the
netlist.

**Five shipped documents were asserting things that are not true, and all five
are corrected:**

* **The CS/CSG pair is not a Kelvin connection.** sec.2.5 said *"no shared trunk
  copper enters the sense loop"*. Re-measured with pcbnew: `R10.1` taps the
  **GND plane 3.73 mm** from `RS1.2`, putting **0.359 mΩ** (buck-A) / 0.381 mΩ
  (buck-C) of shared trunk copper inside the loop; with the CS side, 0.483 /
  0.555 mΩ → **+4.8 % / +5.6 %** sense error → **the 11.0 A current limit is
  really ≈10.5 A**. The claim is withdrawn verbatim and the corrected limit is
  in a new sec.2.5a. Still 1.75× the rail load; no design change.
* **The R-THERM waiver described a board that no longer exists.** It said
  *"U11.21 … 1 direct via (vs 3 on U2.21)"* and carried a next-rev work order
  that is **already done**. Measured here: **U2.21 = 7 GND vias, U11.21 = 7**.
  Its dissipation figures were still the superseded 15.5 A Q1 / 5 A Q6 envelope.
  Rewritten, and the three TPS2557 EPs (1 via each) are **named for the first
  time** with the numbers that make them acceptable. *A stale waiver is an
  inherited defect* — this one had outlived four releases, having been raised
  and DEFERRED once already at v1.5 (RL-11).
* **The port ceiling nobody had written down: 2.72 A, not 2.5 A.** `R20/R21/R22
  = 36.5 kΩ` → `I_OS(min) = 2717 mA`, and the TPS2557 is guaranteed not to limit
  below it, so **nothing enforces 2 A or 2.5 A**. Three ports at the ceiling is
  8.16 A on a 6 A rail, still under the valley limit, so **nothing intervenes**
  — checked survivable term by term (L1, RS1 0.67 W in a 1 W part, F1) at a cost
  of **ΔT 19.4 °C** on the feed. A-AMP still grades 2.0 A and that choice is now
  written down beside the number instead of hidden by it.
* **`DETAIL_DESIGN` had no line for DEMB.** `U2.11`/`U11.11` are tied to GND
  (R_DEMB = 0 Ω), so **both bucks run in permanent diode emulation** — a
  deliberate departure from the TI worked design this project declares it
  adopts, against that file's own rule that *"a value in the schematic with no
  line here is UNJUSTIFIED"*. Now derived (DCM below ≈0.9 A/rail) and recorded
  as the CHOICE it is.
* **A datasheet citation belonged to a different device variant.** The
  "unused channel-2 pins may float" claim quoted SLVSBY8D's **TPS2514x** pin
  table, where pins 3/4 are genuine N/C; the fitted **TPS2513A** has real
  DP2/DM2 there. Restated as an engineering judgement, not a datasheet
  permission.

**Also corrected before the seal:** 5VA's **E-MARGIN had never been computed**
although it feeds three known 2 A loads — now derived (**+151.8 mV** at the
receptacle, +7.8 mV with the mating contacts charged) and **wired into the
machine gate**, which now grades 2 rails instead of 1; the rail's declared
window went from the bare nominal 5/5 to the tolerance-inclusive 5.032/5.273.
The **stackup is declared for the first time** (JLC 4-layer STANDARD, 1 oz outer
/ 0.5 oz inner) — the board file carries none, so every ampacity figure's copper
weight was an unnamed fab default; it is now an **order-form obligation** in
ORDER_README, which is where it binds, since gerbers do not carry it. Two
gate-reporting defects the render review caught were fixed: `A-POP` shipped a
**FAIL** that was purely an ordering artifact (it grades the MANIFEST, and ran
21 minutes before the MANIFEST existed — re-run **PASS**, and it now runs after
the stamp), and the MANIFEST's `twin:` line repeated `missing_models.txt`'s
`122/122` without the caveat that **R12 (C2984354) has no JLC model at all**.
And the gerber zip size stated in six documents was **394 530 B**; the file on
disk is **394 534 B**, corrected everywhere.

**RECORDED, DEFERRED, WITH THEIR MEASUREMENTS** — both are copper, and v1.9
exists to fix the pour; re-routing would void every verdict just collected.
Buck-A's pour is **2.7× (SW) and 3.2× (CS) more resistive than the
geometrically MIRRORED buck-C cell**, from a 0.300 mm neck ~0.8 mm long — and
SW_A is 1.38× of IPC-2221 by summed cross-section but **0.96× by
resistance-equivalent width**, a 44 % disagreement between two methods, so
`nets.yaml` now states the method with the number. High-side gate loops measure
**25–34 nH** (Q ≈ 1, so switching-loss/EMI, not shoot-through) — the
uncomfortable part being that the GATE class justifies its 0.300 mm width on
dI/dt loop area and **nobody had ever measured the loop**.

**Left OPEN and written down rather than papered over:** the fix lens's own SOR
reads **3.009 mΩ** for the three 5VC delivery segments against RL-2's 9.32 mΩ
and the 12 mΩ carried in the budget — **a 3× disagreement between two mesh
solves on identical copper that neither side could reconcile**. It is in the
safe direction (the shipped budget is the pessimistic one), which is the only
reason it is not a finding. Bench gates Q2/Q5 settle it, not whichever number
reached the file first.

## v1.8 — 2026-07-26

Released: `07_releases/v1.8-2026-07-26/`. **VERIFICATION-COMPLETENESS supersede of
v1.7-2026-07-26.** v1.7 gains `SUPERSEDED.md`; it is otherwise immutable.
**Fab payload BYTE-IDENTICAL to v1.7** (`diff -r` clean) — the board is not changed.

### Why: a new gate found what no tool had ever checked

`release_required_check.py` (canon **A-EVID**) enforces the **REQUIRED** direction of
`07_releases/contracts.md`. Nothing ever did: `contracts_audit` iterates files that
EXIST and asks whether they are permitted, which cannot see an absence. Run against
v1.7 it reported **5 missing**. Two were real evidence gaps, three were naming.

**usb-hub had never shipped a `pin_review.md` or a `render_review.md`** — absent from
v1.5, v1.6 *and* v1.7. A predecessor-diff check could not see it, because the
predecessor was missing them too.

### The two reviews, and what they found

Both **PASS**. Both found something.

**Pin review** (122 components, 73 nets, all 372 connected pins walked; board pads
cross-checked pad-by-pad against the netlist, 0 mismatches):

* **CONCERN — U12.** As shipped, with R42 unpopulated, the USBLC6-2SC6 sits on VBUSC
  at 5.352 V nominal / 5.479 V no-load — **~100-230 mV above its 5.25 V V_RWM,
  continuously**. Below breakdown (6.0 V), so leakage not damage. Every earlier
  document framed R42 as landing *on* 5.25 V **if fitted** and never wrote down the
  corollary. **Now stated plainly in ORDER_README at gate Q9.** The reviewer's
  recommendation — populate R42 by default, or a 6 V-V_RWM array — is a **v-next
  design decision**: populating R42 puts it on the CPL and changes the fab payload,
  which this supersede must not do.
* **DOC DEFECT — SW1.** The tsx comment described the deleted eFuse-era **D6 / EN_C**
  enable scheme as if current, contradicting the same file's own v1.2 header. The
  copper was never wrong (E-INV asserts both EN pins on ENKILL), which is exactly why
  nothing machine-checkable caught it. **Fixed**, and the v1.1 revision note marked
  SUPERSEDED.

**Render review** — no blocking defect, no render-vs-CPL or render-vs-netlist
disagreement. It did the **bare-vs-twin discrimination on Q1-Q6 explicitly**, the test
an earlier review generation failed when two of four lenses read the bare copper drain
paddle as a moulded package: bare shows the paddle, twin shows solid bodies with pin-1
dots in the netlist-correct corners. It recomputed the **CPL datum** from pad geometry
and matched all five connectors, each 1.5-4.7 mm off the KiCad anchor — the v1.6 fix
holds. It states plainly that the LED and C1/C2 3D models are polarity-symmetric so a
render **cannot** decide physical orientation; both stay on the order-preview gate.
One cosmetic nit carried to v-next: refdes "D1" runs into the "LEDS DARK = SWITCH OFF"
legend (silk is copper — not touched here).

### Also

* **Red-team naming** (crow-mic-pod's pattern): dated history stays in `08_reviews/`;
  the release ships the current review under the contract name. `redteam_layout.md`
  (from `2026-07-25_v1.5_redteam_layout.md`) and `redteam_topology.md` (from
  `2026-07-22_v1.0_redteam_topology_rereview.md`) are **copies**, with provenance
  headers naming the source and the lineage. The v1.2 protection red-team is a
  different document, not this one's successor — said explicitly, because
  "re-review" is otherwise ambiguous.
* **Assembly PDF** — the stricter option: the board moves to the contract, not the
  contract to the board. `assembly_front.pdf` + `assembly_back.pdf` are replaced by a
  single **2-page `pdf/assembly.pdf`**, front then back.
  *Correction to the brief for the record:* the named exemplar
  (crow-recorder-central-v2 v1.5) is **1 page**, not 2 — its 254137 bytes match but its
  page count does not. The genuine 2-page exemplar is **crow-mic-pod-v2 v1.2**
  (2 pages, 73472 B). v1.8 ships the 2-page form the user chose.
* **Archive still stands alone** — re-proved, not assumed: `source/` extracted to a
  bare temp dir, DRC **0/0/0** and ERC `footprint_link_issues` **0**. That is v1.6's
  defect, which cost a release; cooksense shipped the same one today.

## v1.7 — 2026-07-26

Released: `07_releases/v1.7-2026-07-26/`. **VERIFICATION-COMPLETE supersede of
v1.6-2026-07-26.** v1.6 gains `SUPERSEDED.md`; it is otherwise immutable.

**THE FAB PAYLOAD IS BYTE-IDENTICAL to v1.6** — `fab/bom.csv`, `fab/cpl.csv`, the
13-file gerber zip and both drill files are the same bytes, verified by `diff -r`.
**The board is not changed and v1.6's board was not wrong.** This is an
evidence-completeness supersede, not a fab defect.

### What was wrong

v1.6 shipped **13** verification files where v1.5 shipped **34**. The MANIFEST
asserted DRC 0/0/0, twin 119/119, passives 26/26, A-STOCK and freshness — while
the release carried no `drc.json`, no `erc.json`, no `bom_source_check.txt`, no
stock check, and no **`manifest_selfcheck.txt`**, the artifact whose entire job is
proving the manifest's PROSE matches its MACHINE EVIDENCE. The release asserted
its own gate results with the evidence stripped out.

**Two distinct causes, diagnosed rather than papered over:**

1. **Generated, never staged.** All six `twin_*.png` existed in `06_build/twin/`
   dated 01:02 the same day. The staging step did not carry them. A copy miss.
2. **Never produced at all.** `render_top_bare.png` / `render_bottom_bare.png`
   existed nowhere outside v1.5 — a **skipped stage**. And the nine machine-
   evidence files (`drc.json`, `erc.json`, `audit.txt`, `bom_source_check.txt`,
   `stock_check.{json,txt}`, `release_freshness.txt`, `manifest_selfcheck.txt`,
   `standalone_archive_drc.json`) existed nowhere under `06_build`: the gates ran
   and their output went to **stdout**, never to an artifact. A number in a chat
   message is not evidence.

### And the missing evidence hid a real defect

v1.6's `source/fp-lib-table` was copied raw from `04_kicad/` and points at
`${KIPRJMOD}/../03_src/lib/...`, which **does not exist inside the archive**.
Extracted on its own, v1.6's archive yields **12 `lib_footprint_issues`** (DRC)
and **12 `footprint_link_issues`** (ERC). v1.5 rewrote that table to
`${KIPRJMOD}/`; v1.6 did not. The gate that catches exactly this is
`standalone_archive_drc.json` — **one of the 21 files v1.6 was missing**. v1.7
fixes the table and ships the proof: standalone archive DRC **0/0/0**, extracted
to a bare directory with no project around it.

### Why no gate caught it

**M-REL requires only that `verification/` exist and be non-empty.** Thirteen
files satisfied it. A directory-presence check cannot see a missing artifact —
the same shape as `jlc_twin` exiting 0 on 11 parts it never verified. A
required-artifact-list check is proposed (not landed) in the seal commit.

### v1.7 verification set

34 files, matching v1.5's list exactly (`comm -23` empty), plus the gates re-run
against the **shipped artifact** rather than the working tree.

## v1.6 — 2026-07-26

### THE TARGET IS A RASPBERRY PI 4, NOT A PI 5 (ADR-0004)

Every power document on this board rested on one sentence recorded at
commission: that the Pi can be told to skip PD negotiation and assume a 5 A
supply via `PSU_MAX_CURRENT=5000`. **That is a Pi 5 bootloader-EEPROM feature.
The user has confirmed the load is a Pi 4, which has no such setting.**

The conclusion — no PD source controller — survives. The reason does not, and
the difference is not cosmetic. A Pi 5 *is* a PD sink and the old story was
"talk it out of negotiating". A **Pi 4 does not negotiate PD for its power input
at all**: its USB-C input is a plain 5 V sink with CC pull-downs, officially
**5 V / 3 A (15 W)**. A plain regulated rail is not a workaround for a Pi 4, it
is the only interface it has. ADR-0001 is marked `superseded-by: 0004`
(reasoning only); the BRIEF keeps the old paragraph struck, not deleted.

**The margin improves 16.5x.** Same hardware, same 97 mOhm budget, same 1.2
derating, same 5.227 V worst-case rail, same 4.63 V threshold — only the load
changed, because we now know what it is:

| | IR drop | delivered | slack |
|---|---|---|---|
| Pi 5 premise @ 5 A | 582.0 mV | 4.645 V | **+15.0 mV** |
| Pi 4 actual @ 3 A | 349.2 mV | 4.878 V | **+247.8 mV** |

E-MARGIN re-graded PASS at 3 A. *"15 mV of paper slack is not a margin you ship
on"* was a true statement about the wrong load, and it is retired. The bench
gates are not — Q2/Q5 are now judged against the 3 A number.

`load_uv_threshold: 4.63` is unchanged: it was always the **Pi 4** figure, until
now applied to a Pi 5 by inference. And one number is upgraded from inference to
specification — the **Pi 4 absolute maximum input is +6.0 V** (Pi 4 datasheet
p.8, Absolute Maximum Ratings, *"a stress rating only"*).

`power_tree.yaml` USB-C `iout_max_A: 5 -> 3`. **The board stays provisioned for
5 A** — buck-C, the F2 7 A polyfuse, the VBUSC via count and the delivery-corner
pours — and that is now stated as deliberate over-provisioning rather than left
as an unexplained mismatch.

### D5 / U12 — RESOLVED by the Pi 4 numbers; do not reselect

| V | what | source |
|---|---|---|
| 5.479 | worst-case operating VBUSC | power_tree.yaml |
| 6.00 | **Pi 4 ABSOLUTE MAXIMUM input** | Pi 4 datasheet p.8 |
| 6.00 | U12 guaranteed non-conduction floor (V_BR min; no typ, no max) | ST 11265 rev 5 Table 2 |
| 6.67 | D5 breakdown **minimum** | Littelfuse SMBJ rev 06/03/20 |

**D5 cannot protect the Pi** — by the time it conducts, the rail is already
670 mV above the Pi's absolute maximum. It never could have, at any breakdown
that also clears a 5.479 V operating rail. The TVS protects the **board** against
**transients**. So the "inverted hierarchy" is a non-issue for the Pi and the
empty TVS window does not matter. **Stated plainly: nothing on this board
protects the Pi from a SUSTAINED over-voltage** — a TVS clamps transients, not a
stuck regulator — which is the fail-high posture the BRIEF already accepts as
best-effort for a supervised prototype. Escalation, if that ever changes, is an
**active OVP at ~5.6-5.7 V (a disconnect/crowbar), NOT a different TVS**.

### R42 — a DNP setpoint-trim strap, and the series-resistor trap

The user asked for an optional way to drop the rail if the bench says U12 is
stressed; the instinct was a **series resistor in the 5 V line**. Recorded as
rejected because it is genuinely attractive and wrong: over-voltage is a
**light-load** phenomenon and IR drop is a **heavy-load** one, so they are
anti-correlated. At 0 A a series part drops 0 mV — nothing in the exact case it
was added for; at full load it removes voltage when the rail is already lowest.
It costs 72 mV and 0.18 W at 3 A, and does nothing about a fail-high
(20 mOhm x 3 A = 60 mV of a multi-volt excursion).

Instead **trim the setpoint**: `R42 = 160k, 0402, DNP, in PARALLEL with R12`
(the buck-C FB top). Rtop 4.12k -> 4.12k||160k = 4.017k, rail **5.352 -> 5.249 V**,
landing on U12's 5.25 V V_RWM — load-independent, zero heat, zero delivery cost.
Fitted, worst-case vout_min 5.227 -> 5.125 V, minus 349 mV = 4.776 V, still
**+146 mV**. *The trim is only affordable because the load is a Pi 4;* at 5 A it
would have eaten the whole margin. Ships **unpopulated**, declared
`dnp_by_design` with dated evidence, deliberately uncoded, and its value pinned
by an E-INV `part_value` assert — the parallel combination is nonlinear in the
strap, so a 16k slip gives 4.500 V and a board that browns out at no load.

New bench gate: measure VBUSC at no load and at 3 A, and U12 leakage at the
measured voltage over temperature. **PASS = fit nothing if U12 leakage is
acceptable at 5.352 V; fit R42 if not.** Record the numbers either way.


**COPPER revision.** `07_releases/v1.6-2026-07-26/`. **v1.5 and every earlier
release are DO-NOT-ORDER.** v1.5 gains `SUPERSEDED.md`; it is otherwise
immutable.

### Why v1.5 became DO-NOT-ORDER: a datum defect in the CPL exporter

A new **A-POS** gate measured every CPL row against JLC's own convention and
found **11 of v1.5's 108 rows off-datum**. JLC positions a part from the
bounding box of its **PAD CENTRES**; the exporter had been emitting
`fp.GetPosition()`, the footprint **anchor**, which is only the same point when
the land happens to be symmetric about it. Measured error, per ref:

| ref | offset from JLC's datum |
|---|---|
| J1 (XT60, the pack inlet) | **4.6861 mm** |
| J2 / J3 / J4 (USB-A) | **3.7346 mm** each |
| J5 (USB-C, 0.5 mm pitch) | **1.4975 mm** |
| Q4 / Q5 / Q6 | 0.0625 mm each |

Every external connector on the board, and the worst of them by nearly 5 mm.
This is not a rotation question and no render would ever have shown it. The
exporter fix is in the tree; v1.6 re-exports from scratch and every row lands
on-datum.

### What changed in the copper

- **H3 mounting hole — a short of the 6 A rail to GND through a screw.**
  MEASURED on sealed v1.5, on FILLED copper: H3 (106.0, 24.0) is a 1.600 mm-radius
  NPTH carrying **`5VA` at 1.850 mm AND `GND` at 1.850 mm on BOTH outer layers** —
  0.250 mm of bare laminate and ~20 um of solder mask between them. Every M3
  fastener bridges it, including the smallest cap head (r 2.75). v1.5's only
  mitigation was a sentence in `ORDER_README` about nylon standoffs. v1.6 states
  a rule instead — **within r <= 4.00 mm of any mounting hole all outer copper is
  one net and that net is GND** — and enforces it by notching the 5VA pour (5VA
  now stops 4.50 mm from H3) and by raising the router's hole keepout 3.0 -> 4.2 mm
  so a signal wave cannot re-create it on a different net.
- **H4** — `VBUSA3` reached 4.152 mm, inside a DIN 9021 washer (r 4.50). The pour's
  SE corner is chamfered; it now stops at 5.00 mm.
- **In2 VIN plane vs every mounting drill** — the 9-12.6 V plane sat 1.850 mm from
  a 1.600 mm drill on all four holes (0.250 mm, against a +-0.13 mm NPTH position
  tolerance). A 12-gon rule area per hole pushes VIN to >= 2.077 mm. In1 GND is
  deliberately left alone: a grounded fastener touching GND is the benign case.
- **VBUS ampacity 0.5 -> 0.8 mm.** "Pour-fed" was true of the connector end and
  false of the feed: each of VBUSA1/2/3 ran **13.554 mm of 0.500 mm B.Cu at
  exactly the class floor** carrying ~2 A. One 0.650 mm segment per port cannot be
  widened (TPS2557 VSON-8 is a 0.650 mm pitch and an 0.8 mm track is wider than
  the pitch), so it takes a `scoped_floors` relaxation pinned to three 2x3 mm rule
  areas over those pin pairs, with the measured geometry as its evidence.
- **PowerPAK EP paste, all six power FETs.** Each carried **ONE 100%-area aperture
  over a 3.810 x 3.910 mm exposed pad = 14.897 mm2**; IPC-7093 asks 50-80% as an
  array. A vendored footprint (`03_src/lib/usb_hub_3s.pretty/
  PowerPAK_SO-8_Single_Paste65`) replaces it with a 2x2 window-pane at **65.0%**
  (4 x 1.5359 x 1.5762 = 9.683 mm2), webs 0.369/0.379 mm. The ratio is not
  invented: KiCad's own HTSSOP-20-1EP_...\_Mask2.75x3.43mm uses 4 x 1.11 x 1.38
  over 2.75 x 3.43 = **65.0%** for this same package family. Copper and mask are
  unchanged.
- **USB-C delivery corner.** PMID crossed F.Cu<->B.Cu on 2 vias and F2 had ZERO
  vias on either pad at 0.775 W. Now 4 per F2 pad, 6 across the PMID pour, and 3
  per J5 VBUS contact pair, all sites derived from live pad geometry.
- **Three fiducials (FID1-3).** v1.0-v1.5 shipped with none, on a board whose
  smallest machine-placed pitch is 0.500 mm (J5, which IS on the CPL). Nearly
  free during a spin, impossible afterwards.

### Status LEDs (user decisions D2/D3/D4)

Five indicators, **+11 placements and exactly +2 BOM lines**:

| ref | part | taps | current |
|---|---|---|---|
| D8 | C2296 amber | VIN via R37, returned through **Q8** | 1.504 mA typ (0.946-1.547) |
| D9/D10/D11 | C2297 green | **VBUSA1/2/3** — per port | 0.282-0.377 mA |
| D12 | C2297 green | **VBUSC** — post Q6 + F2 | 0.275-0.405 mA |

- **The pack LED had to be FET-gated.** There is no switched power node on this
  board: SW1's pads are GND / ENKILL / NC, and neither `VBAT` nor `VBAT_F` reaches
  a switch pole — it switches ENABLE. Ungated, D8 would add **1.504 mA to a
  271 uA OFF-state budget (6.6x) and flatten a 3S 5000 mAh pack in ~117 days**.
  Q8 (BSS138, the same feeder as Q7) gates it off ENKILL; the adder is Q8's
  I_DSS, <= 0.5 uA. `power_tree.yaml` quiescent 270 -> **271 uA**.
- **Per-port, not one rail LED**: with a single 5VA indicator a port that had
  latched off into current limit looks identical to a working one.
- **The C indicator taps VBUSC, not 5VC**, so a dark C LED with the A LEDs lit
  means the ADR-0002 protection chain opened. Cost to the 15 mV E-MARGIN slack:
  0.346 mA x 42.4 mOhm = **14.7 uV = 0.098%**.
- Silk: `PACK ON`, `USB-A1/2/3 5V`, `USB-C 5V OK`, and — because the pack LED is
  enable-gated and the XT60 stays hot — `LEDS DARK = SWITCH OFF` /
  `PACK STILL LIVE AT XT60`.
- **CPL rotation for C2296/C2297 is 0, NOT 180.** The pad-NUMBER fit returns 180
  at a 17.7x margin and is wrong: JLC numbers pad 1 = ANODE, KiCad's `Device:LED`
  is pin 1 = K, and both libraries draw the cathode WEST, so the parts already
  align. A 180 row would ship every indicator dark — indistinguishable from a
  dry joint. See the release notes for the two numbering-free channels.

### D5 / U12 protection ordering — the sourcing half of the story

*(Superseded in framing by "D5 / U12 — RESOLVED by the Pi 4 numbers" above, which
is the conclusion. This subsection is retained because the SOURCING result stands
on its own and saves the next person a day of catalog searching.)*

The finding is real and **the requested fix cannot be bought.** ST's USBLC6-2SC6
(U12) specifies VBUS-GND breakdown as **MIN 6.0 V @ 1 mA with no typ and no max**
(doc ID 11265 rev 5, Table 2); D5's breakdown MINIMUM is 6.67 V, so the small ESD
array conducts first. A replacement would need Vwm >= 5.479 V **and** Vbr(max)
< 6.00 V at once; that window is **empty** — the SMBJ family has no step between
Vwm 5.0 V and 6.0 V, and the tightest SMB part found at any qualifying Vwm
(SM6T6V8A) still breaks down 450 mV above U12's floor and is not JLC-stocked.
v1.6 therefore **records the accepted residual** with its numbers, corrects the
part.yaml (VBR window was `6.67-8.15 V @1mA`; it is **6.67-7.37 V @ 10 mA**, and
Ppk is 10/1000us not 8/20us), and names the escalation as an ACTIVE OVP rather
than a better TVS. Lowering 5VC is refused: it would spend the 15 mV margin.

### Two budget corrections, neither of them a hardware change

**The GND return was ABSENT, not negligible.** RL-2's 12 mOhm board-copper figure
named three segments — 5VC L2.2→Q6 tab 2.198, PMID Q6.S→F2.1 4.914, VBUSC F2.2→J5
2.209 — and all three are FORWARD path. The return from J5 back to the buck was
simply missing, and in a budget a missing term looks exactly like a zero one. Solved
2026-07-26 by the same method as the forward path (SOR on filled copper, 0.8 mm
cells, all four layers, 178 GND vias coupling them, converged on the one-port
resistance over 10350 sweeps): **0.956 mOhm**. It is small for the reason you would
hope — In1.Cu carries 17520 of 18908 GND cells, with B.Cu (12105) and F.Cu (9438) in
parallel — but at 5 A it is 4.78 mV, a third of the old 15 mV slack, so it had to be
counted rather than called negligible. `ir_budget_mohm: 97 → 98`; slack at 3 A
+247.8 → **+244.2 mV**.

**A Pi 5 at 5 A is now a DECLARED NON-GOAL**, not an implicit one, because the
margin is contingent on the load and not on the hardware — the copper is
bit-identical to the copper that measured +15.0 mV. The 5 A arithmetic is preserved
in `power_tree.yaml` so anyone retargeting finds it waiting: at 5 A the board still
PASSES E-MARGIN (588.0 mV vs 597 mV headroom = +9.0 mV) but is back on paper-thin
slack, and both the 4.63 V undervoltage threshold and ADR-0003's 6.00 V
absolute-maximum chain are **Pi 4 figures** that would need re-deriving.

### Gates and bench

- New bench gate (user decision D7): LEDs fitted, SW1 OFF, **measure pack current
  with a uA meter and record it with the ambient. PASS <= 300 uA.** That
  measurement, not the BSS138 datasheet's 25 C maximum, is what qualifies
  `quiescent_ua`.
- P-FACT `pad1_net_polarity` declared for both LEDs and for every polarized 2-pad
  part on the board (C1/C2 polymer, D1, D2, D3/D4, D5) — coverage was zero.
- E-INV gains `part_value` on all five 6.98 k ballasts plus the LED-cell topology
  asserts: 36 invariants, all holding.
- Two tier-preflight FAILs that predate v1.6 and were invisible when it sealed:
  the Default netclass rode a hardcoded 0.2 mm clearance while the router used
  0.18, and `island_rescue` scanned only the outer layers on a board with two
  inner planes.

## v1.5 — 2026-07-25

Released: `07_releases/v1.5-2026-07-25/`. **CPL-CORRECTION supersede of
v1.4-2026-07-23** (v1.4 gains `SUPERSEDED.md`, otherwise immutable).
**v1.4 and every earlier release are DO-NOT-ORDER. Order from v1.5.**

**Why: a P0 in the CPL, not in the copper.** Sealed v1.4 places **C1 and C2 —
100 uF / 35 V POLARIZED polymer electrolytics — at CPL 270.0 where the measured
correct value is 90.0**: 180 degrees reversed, directly across the 9.0-12.6 V 3S
LiPo input behind a 10 A fuse. A reverse-biased polymer electrolytic on a
near-zero-impedance pack heats, gasses and **vents**, at first power-up, before
any bench gate can run. Found by a pre-order PCBA audit
(`08_reviews/2026-07-25_v1.4_pcba-audit_assembly.md`, 15 findings, dispositions
PCBA-1..15) — the earlier reviews had audited the board, not what the machine
would build.

- **fab/cpl.csv — EXACTLY FOUR changed cells, and nothing else:**
  `C1 270.0->90.0`, `C2 270.0->90.0`, `Q7 270.0->180.0`, `J1 90.0->0.0`.
  108 placements both sides, 0 rows added or removed.
  - **C1/C2** (PCBA-1, P0): no per-LCSC rotation row existed for C2982822, so the
    exporter fell through to the footprint-NAME DB, which a per-part fact cannot
    live in. Polarity re-verified independently of the pad fit: JLC's own library
    silk draws a crossed **"+" over its pad 1** and a bar **"-" over pad 2**, and
    our pad 1 is on VIN.
  - **J1** (PCBA-2, P1): the name-DB pattern `^AMASS_XT60PW-M` is START-ANCHORED
    and this board uses a vendored `XT60PW-M_EdgeTrim`, so **no rule fired at
    all** and the offset silently defaulted to 0. Four-pad fit (2 blades + 2
    anchors) gives rms **0.0000 mm @270**, 12.0 mm out at 90.
  - **Q7** (PCBA-3, P1): `^SOT-23` = -90 is wrong for C78284. 3-pad asymmetric
    fit, rms 0.062 mm @180 vs 1.95 mm @270. Would have left Q6 un-gated — a dead
    or silently unprotected Pi rail.
  - Root cause behind all three, fixed at source before this release: a
    **handedness bug in `jlc_twin.xform()`** that NEGATED every rotation offset
    the tool ever reported (repo `e0d735c`, `9078ad9`, `95a8180`, `1b69760`).
- **NO COPPER CHANGE.** Gerbers, both drill files, `source/`, `3d/` and `pdf/`
  are **sha256-IDENTICAL to v1.4** — 20 files. Proven by RE-EXPORT from the
  unchanged board: 13/13 zip members identical once the plot's own timestamp
  comments are stripped (`verification/cpl_acceptance_gate.md`).
- **fab/bom.csv**: identical to v1.4 row-for-row except the **MPN column is now
  populated on all 43 lines** (was 0/43). Cross-checked against the
  independently datasheet-authored `02_parts/` directory names: **26/26 hard-part
  MPNs matched, 0 directories unaccounted for** (PCBA-10).
- **NEW `03_src/rules/assembly.yaml`** (PCBA-5) — the population set finally has a
  machine-readable home: `service` (incl. **THROUGH-HOLE assembly**, 4 refdes /
  22 plated holes, J1-J4), `sides: [top]` (measured 108/108), `fiducials: none`
  (deliberate: the smallest centre-to-centre distance between two distinct
  pads is a measured **0.500 mm** at J5, > 0.4 mm),
  `build_quantity: 5`, and F1/SW1 as the only `not_assembled` refdes with dated
  evidence. The MANIFEST `not_assembled:` line is GENERATED from it.
- **NEW `01_docs/DETAIL_DESIGN.md`** (PCBA-7) — it did not exist, although three
  sealed `part.yaml` files have cited sec.1/2/5 as authority since 2026-07-21.
  Derivations from the datasheets directly (LM5116 SNVS499I eq. 7-24; USBLC6-2
  Doc ID 11265 Rev 5). The sec.5 citation was wrong three ways and is corrected.
- **ORDER-PREVIEW HUMAN GATE** in ORDER_README (PCBA-8). v1.4 mentioned the JLC
  preview **zero times** while **12** twin findings are waived on exactly that
  gate — **C1/C2 among them**. P1-P7 now say what to look for and what rejects.
- **U12 over-voltage: ACCEPTED + MEASURED** (user decision; MANIFEST waiver
  **W-U12**). 5.352 V nominal / 5.479 V worst corner vs the 5.25 V at which ST
  characterizes leakage — but ST's absolute-ratings table carries **no V_BUS
  limit** and V_BR is **6.0 V minimum**, cleared by 521 mV. R12 deliberately NOT
  changed. Bench gate Q1 now RECORDS measured VBUSC/VBUSA.
- **Stock, at build_quantity 5:** PASS, 43/43 lines OK, 0 uncoded. Split **12
  Basic / 31 Extended** (~31 feeder setups, priced before the order). Tightest
  ceilings: C473910 = **37 boards**, C5337088 = 90, C408523 = 225. Table rebuilt
  sorted by tightness with a named alternate per row (PCBA-13/14).
- **Panel-rail policy, measured:** three of the four edges cannot take a rail —
  J1 (-6.82 mm), J2-J4 (-4.29 mm) and J5 (-2.90 mm) physically OVERHANG the
  outline. Only the edge opposite the USB-C connector is usable (+1.43 mm).
- **TWO fresh review lenses, both ORDER**, both archived in `verification/`:
  a zero-context lens over the STAGED release (0 P0 / 3 P1 / 9 P2 — it
  re-derived the four CPL cells five ways and got **107/107 parts agreeing with
  the shipped CPL to <1°**, and it found real defects in this release's own
  paperwork, all fixed), and the **FIRST layout/thermal/power-integrity lens
  ever run against THIS copper** (0 P0 / 5 P1 / 7 P2). The prior layout lens was
  written against the **v1.0** board; 10 footprints were added afterwards
  (C53, C54, D5, F2, Q6, Q7, R30, R34, R35, SW1; tracks 642→1061), so the whole
  discrete VBUS protection chain had never been layout-reviewed — v1.3 and v1.4
  both sealed carrying that claim.
- **Build note that changes what you do (RL-3):** H3's mounting hole has **5VA
  and GND copper both starting at r = 1.80 mm, on BOTH outer layers**. A metal
  M3 screw head bridges the 6 A USB-A rail to GND through solder mask alone.
  **Fit a nylon screw, or leave H3 unfitted.** ORDER_README section 3a, B1.
- **The Pi-rail margin is thinner than any previous release said.** The board
  copper on the 5 A path was a **~3 mΩ estimate** carried since v1.3; the layout
  lens MEASURED it at **≥9.32 mΩ** (mesh solve; true ≈10.4-11.6). Three figures
  have now been published for this one margin — **157 mV → 69 mV → 15 mV** —
  each step removing an optimistic assumption without the hardware changing.
  `power_tree.yaml` synced (`vout_min` 5.27→5.227, `vout_max` 5.43→5.479,
  `ir_budget_mohm` 88→97); E-MARGIN re-run **PASS**. 15 mV of paper slack is not
  a margin to ship on — bench gates Q2/Q5 measure the delivered voltage.
- **The archive is self-contained for the first time (PCBA-16).** `source/
  fp-lib-table` pointed at `${KIPRJMOD}/../03_src/lib/` — OUT of the release —
  so a standalone re-measure of v1.3/v1.4 raises **6 `lib_footprint_issues`**
  despite the vendored `.pretty` folders being shipped, and their MANIFESTs
  claim the path they do not have. v1.5 points it at the vendored copies:
  standalone `kicad-cli pcb drc` from inside the archive now reads **0
  violations / 0 unconnected**. Cost: `fp-lib-table` is the ONE payload file not
  byte-identical to v1.4 (19, not 20) — a library-path line, not copper.

## v1.4 — 2026-07-23

Released: `07_releases/v1.4-2026-07-23/`. **DOCS-ONLY supersede of
v1.3-2026-07-23** (v1.3 gains `SUPERSEDED.md`, otherwise immutable — the one
allowed addition). **Board, BOM, CPL, gerbers, source and PDFs are
byte-identical to v1.3** (22/22 files sha256-verified; the freshness gate's
9 identical-artifact findings are the release's declared purpose, waived with
evidence in `verification/freshness_waiver.md`). v1.3's electrical state and
verification battery stand unchanged. **Order from v1.4.**

Driven by a post-seal user-supplied external review
(`08_reviews/2026-07-23_v1.3_external-user_full.md`, dispositions EXT13-1..8):

- **SW1 fallback-header shunt polarity was REVERSED in the v1.3 README.**
  The tsx wires SW1 pin1=T1→GND, pin2=COM→ENKILL; grounding ENKILL shuts both
  bucks down and opens Q6. Correct: **COM-T1 shunted = OFF; shunt removed =
  ON.**
- **F1 was misdescribed as "KH-AF90DIP-112"** (the USB-A connector family).
  F1 = **Keystone 3568 MINI-blade fuse holder, C5249699** (BOM row 38).
- **Tolerance-inclusive worst-case rail table** replaces the Vref-only
  numbers: R13/R4 = C5126242 = FRC0603F1211TS **±1 %** (ledger row 150) was
  omitted. 5VC static range **5.227-5.479 V** (was 5.272-5.432); low-corner
  headroom **597 mV vs the 440 mV IR budget — E-MARGIN still PASS** (157 mV
  slack); 5VA top corner 5.273 V slightly above the 5.25 V USB-A intent
  (accepted, no-data charge ports; 0.1 % R13/R4 recorded as next-rev option).
- **Packaging note:** F1 (C5249699) + SW1 (C2939728) are on `fab/bom.csv` but
  intentionally off `fab/cpl.csv` (hand-solder) — JLC upload shows 2 unmatched
  designators; README instructs marking both DNP + a hand-fit purchasing list
  (incl. the off-BOM 10 A MINI blade fuse element).
- **Bench qualification TIGHTENED** (Q0-Q7, adopted from the review): R12 AND
  R30 ohmmeter pre-power; no-load rails with a **5.45 V firm ceiling**;
  VBUSC@5A ≥5.00 V at the board; 5 A→0 A load-release overshoot capture;
  cable-end hot ≥4.80-4.85 V; SW1/header continuity logic; `vcgencmd
  get_throttled` through the Pi stress test. OV posture (Option 2) carried
  VERBATIM.

Verification scoping (canon): docs-only fix-pass — targeted source-evidence
confirmations (`verification/2026-07-23_v1.4_docfix_confirmation.md`), M-BOM
re-run PASS, policy_audit re-run 0 FAIL; no fresh review lens (no new
electrical state).

## v1.3 — 2026-07-23

Released: `07_releases/v1.3-2026-07-23/`. **Supersedes v1.2-2026-07-23**
(v1.2 was found **DO-NOT-ORDER** by an external human review after seal; it gains
`SUPERSEDED.md`, otherwise immutable). v1.3 is the FIX PASS for the confirmed
blockers — a BOM + docs + artifact-regen revision; the netlist topology and
routing are unchanged (same promoted KRT chain).

**R12 catalog-verified (THE order blocker).** v1.2's BOM resolved R12 to
**C2933210 = 3.74 kΩ** (tscircuit value-resolution; the tsx left R12 uncoded),
driving the buck-C setpoint to ~4.97 V undervoltage. v1.3 bakes the LIVE-catalog-
verified **C2984354** (AR03BTCX4121, Viking **4.12 kΩ ±0.1 % ±25 ppm** 0603,
stock 15 353 on 2026-07-23) into the tsx (`fbtopMpn`); verified alternate
C861436 (Yageo RT0603BRD074K12L). The buck-C setpoint is RE-DERIVED against the
ACTUAL Q6+F2 delivery path (Q6 AON6403 ~4.3 mΩ + F2 SMD2920-700 R1max 18 mΩ
catalog-verified — NOT the removed eFuse 34-48 mΩ model): 5VC 5.352 V nom /
5.27 V worst-case; **E-MARGIN PASS** (640 mV headroom vs 528 mV need at
ir_budget 88 mΩ).

**D5 directionality fixed.** v1.2's C140903 is listed **BIDIRECTIONAL** by the
JLC catalog (LRC SMB-FL) — the design's uni-directional cathode-on-VBUSC
assumption was unverifiable against it. v1.3 uses **C113976** (SMBJ6.0A
**UNIDIRECTIONAL** DO-214AA/SMB, catalog-verified, stock 74 758).

**R30 catalog-verified (2nd wrong-part, caught by the semantic M-BOM gate).**
v1.2's BOM resolved R30 (Q6 gate pull-up, QG→PMID) to **C2933195 =
FRC0603F3091TS = 3.09 kΩ** while labeled 100 kΩ (v1.2 SUPERSEDED addendum,
`688a8af`) — functional but burning ~1.7 mA through Q7 whenever the port FET was
ON. v1.3 bakes **C25803** (UNI-ROYAL 0603WAF1003T5E, **100 kΩ ±1 %** 0603, JLC
Basic, ledger-verified; MPN E96 decode `1003` = 100×10³) — the same code the
board's other 100 k 0603s (R1/R8/R17) resolve to, so the BOM row merges (43
grouped lines). Q6 margins re-derived at 100 k from the AON6403 STATIC table:
OFF/back-feed |Vgs| ≈ 60 mV (Q7 Idss 0.5 µA + Q6 IGSS 0.1 µA × 100 k), 20×
below |Vgs(th)|min 1.2 V → blocks; ON Vgs = −5.35 V (fully enhanced); pull-up
waste 54 µA vs ~1.7 mA at 3.09 k.

**OV honesty (BRIEF A3/D3, Option 2 — user decision).** The discrete Q6/Q7/F2/D5
chain is kept as **SECONDARY** protection; no active OVP added. Docs now state
plainly: protected against shorts / overload / reverse-feed-off; **NOT guaranteed
against a buck high-side short** (D5+F2 = best-effort crowbar). Context:
supervised prototype, replaceable Pi. Escalation boundary (verbatim): "add active
OVP if the system becomes unattended, hard-access, carries valuable storage, or
powers expensive SDR".

**Assembly:** SW1 (SS12D07) moved **off automated assembly** (hand-solder;
VG4-vs-VG6 pitch unconfirmed; header+shunt fallback documented). F1 holder's CPL
status corrected to match its documented hand-solder plan (was erroneously
machine-placed in v1.1/v1.2 CPLs). CPL 108 placements.

**ORDER_README:** bench-qualification plan baked as a REQUIRED pre-Pi-connection
deployment gate (Q1-Q5: assembled-R12 measurement, 8-24 h electronic-load soak,
switch-node scoping at 12.6 V, thermal soak, end-of-cable VBUSC verification).

All release artifacts regenerated fresh from v1.3 source and sha256-distinct from
v1.2 (the v1.2 stale-artifact defect class is machine-checked by
`release_freshness_check.py` this release).

## v1.2 — 2026-07-23

Released: `07_releases/v1.2-2026-07-23/`. **Supersedes v1.1-2026-07-23**
(v1.1 gains `SUPERSEDED.md`, otherwise immutable).

**Discrete VBUS protection — the eFuse is DROPPED (ADR-0002; BRIEF A2/D2 user
decision).** The v1.1 TPS26631 eFuse was over-built for a 5 V/5 A Pi rail and was
the root cause of BOTH the board routing wall (its 20-pin HTSSOP IN_SYS pin boxed
in a fine-pitch escape) AND v1.1's two electrical order-blockers. −9 parts / +1 =
**110 total**. New USB-C protection chain: `5VC → Q6 (AON6403 P-FET,
ENKILL-gated reverse-block via Q7 BSS138) → F2 (PPTC polyfuse 2920, 7 A/16 V) →
VBUSC → J5`, with **D5 (SMBJ6.0A TVS)** over-voltage clamp. buck-C FB stays on
**LOCAL 5VC** (R12 4.12k → 5.352 V; the v1.1 runaway fix). buck-C EN re-merged to
ENKILL. Removed: U13, R31/R32, R33/R36, C51/C52, D6, D7.

Gates at seal (git_sha in `MANIFEST.txt`, `git_dirty: false`):
- DRC **0/0/0** (severity-all, refill-zones, schematic-parity); source/ standalone
  re-measure **0/0** (V-REL-FPLIB).
- ERC 0; parity **110 ×5 sources**; E-INV **24/24**; E-ADR/E-TOPO/E-MARGIN/E-OFF PASS.
- policy_audit **0 FAIL** (PASS=27, WAIVED=2: R-THERM + R-POUR); M-BOM (BOM==source) PASS.
- jlc_twin **GREEN** — F2 (C6165170), D5 (C140903), Q6 (C2760089/AON6403) fetched +
  fit; all PAD-GEOM/PAD-MISMATCH/POLARITY-CHECK adjudicated.
- Fresh zero-context red-team: **ORDER** (architecture approved, no design P0; Q6
  5 A / 0.11 W OK, reverse-block correct). Report in `verification/`.
- 2 Extended-tier parts (F2, D5) carry a MANDATORY order-day `jlc_stock` recheck
  (ORDER_README); first-power OV caution documented (ADR-0002 tradeoff).

## v1.1 — 2026-07-23

Released: `07_releases/v1.1-2026-07-23/`. **Supersedes v1.0-2026-07-22**
(review-driven revision; v1.0 gains `SUPERSEDED.md`, otherwise immutable).

Protected-VBUS revision. +15 parts (115 total). Adds a **TPS26631 eFuse** (U13)
with a **two-FET reverse-current block** (Q6 AON6354 + Q7 BSS138) on the USB-C
rail — **5.83 A current-limit, 5.91 V input-OV cutoff, soft-start, auto-retry**;
moves the USB-C setpoint to **5.151 V sensed at the connector** (buck-C FB → VBUSC,
resolving the Blocker-2 4.97 V finding); adds a **master-off slide switch (SW1)**
on the merged EN bus; raises buck caps to **50 V input / 10 V output** (RT-T2/T5);
adds optional (DNP) SW-node snubbers; relabels silk/docs to the honest framing
(Pi-dedicated 5 A, NOT USB-PD; power-distribution board, not a USB hub).

Gates at seal (git_sha in `MANIFEST.txt`, `git_dirty: false`):
- DRC **0/0/0** (severity-all, refill-zones, schematic-parity); source/ standalone
  re-measures **0/0/0** (V-REL-FPLIB, with vendored `usb_hub_3s.pretty` +
  `Button_Switch_THT.pretty`).
- policy_audit **0 FAIL** (PASS=27, WAIVED=2 [R-THERM + R-POUR ev-backed], HUMAN=6,
  N-A=2). **E-INV 16/16, E-ADR, E-TOPO, E-MARGIN, E-OFF PASS**; P-LAYOUT/P-ADJ PASS.
- JLC twin **exit 0** (88 OK / 232 checked; U13 fit 0.01 mm, Q7 0.08 mm; Q6 reuses
  the AON6354 merged-drain adjudication; SW1 new — pitch confirm at order).
- Pin review PASS, render review PASS. Fix-confirmation review resolves each
  external-review finding (`08_reviews/2026-07-23_v1.1_fix_confirmation.md`).

Carried decisions / open items (none blocks the order):
- **SW1 (SS12D07VG6) footprint pitch = MANDATORY JLC order-preview confirm** — our
  2.5 mm (standard SS-12D07) vs JLC's mislabeled-VG4 model 2.0 mm; jumper fallback.
- **Snubbers R34/R35/C53/C54 = DNP-by-design** (bench-tune footprints; removed from
  fab BOM/CPL, pads remain in gerbers). Encoding `doNotPopulate` in the tsx is a
  next-rev item.
- Bench: loop-stability Bode with the eFuse in-loop; OVP no-false-trip at 5 A.
- **RT-T3** (LM5116 UVLO ~9.65 V cold-start > 9.0 V nominal) accepted as documented
  P2 (LiPo deep-discharge protective) — unchanged from v1.0.

## v1.0 — 2026-07-22

Released: `07_releases/v1.0-2026-07-22/`

First orderable release. 3S-LiPo powered 3-port USB hub (3× USB-A 5 V + 1×
Pi-dedicated USB-C 5 V/5 A), 4-layer, 130.1 × 92.1 mm, XT60 input →
10 A MINI-blade fuse → dual synchronous LM5116 bucks.

Gates at seal (git_sha in `MANIFEST.txt`, `git_dirty: false`):
- DRC 0/0/0 (severity-all, refill-zones, schematic-parity); source/ re-measures
  0/0/0 standalone (V-REL-FPLIB).
- policy_audit 0 FAIL (PASS=19, WAIVED=1 R-THERM evidence-backed, HUMAN=6, N-A=9).
- E-INV / E-ADR / E-TOPO PASS; P-LAYOUT / P-ADJ PASS.
- JLC digital twin exit 0 (80 OK / 209 checked; all criticals adjudicated).
- Pin review PASS, render review PASS.
- Red-team **topology: ORDER** — the original memo's DO-NOT-ORDER was a pre-fix
  snapshot driven solely by P1 RT-T1 (fuse 20 A→10 A, fixed `071fe56`); an
  independent zero-context re-review returned ORDER and re-confirmed the 10 A
  sizing (`verification/…_topology_rereview.md`, `verification/RT-T1_regate_note.md`).
- Red-team **layout: ORDER**, zero P0/P1.

Key decisions carried in this release:
- USB-C port is Pi-dedicated; needs `PSU_MAX_CURRENT=5000` on the Pi 5 EEPROM
  for 5 A (ADR-0001).
- F1 10 A MINI blade element is hand-fit (off-CPL); the Keystone-3568 holder
  (C5249699) is JLC-placed.
- F-2.1 (LM5116 UVLO ≈ 9.65 V cold-start > 9.0 V nominal) accepted as a
  documented P2 per user decision (doubles as LiPo deep-discharge protection).
- P2 next-rev work order (RT-T2/T4/T5, AON6354 doc hygiene, LM5116 EP via-arrays
  + VBAT_F B.Cu pour) recorded in `ORDER_README.md`; none blocks this order.
