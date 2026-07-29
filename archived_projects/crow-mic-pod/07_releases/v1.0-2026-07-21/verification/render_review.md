# Render review — crow-mic-pod (06_build)

Fresh-context review of twin renders, bare fab-truth renders, PDF pages, against
`fab/cpl_jlc.csv` (population ground truth) and `twin/missing_models.txt`
(known-missing bodies: J1, J2). Reviewer had no design context; nothing was
assumed intentional.

Files reviewed: `twin/twin_top.png`, `twin/twin_bottom.png`, `twin/twin_iso_nw.png`,
`twin/twin_iso_se.png`, `twin/twin_edge_west.png`, `twin/twin_edge_east.png`,
`renders/bare_top.png`, `renders/bare_bottom.png`, `pdf/schematic-1.png`,
`pdf/pcb_layers-1..6.png`, `pdf/assembly_top-1.png`, plus `twin/twin_report.csv`.

---

## Findings

### F1 — DEFECT: C3/R3 refdes labels ambiguous (read as swapped) in the x=104mm column
Confirmed on BOTH the modeled twin and the bare fab-truth silkscreen (this is on
the F.Silkscreen gerber, not a render artifact). The vertical column below U1
reads, top to bottom:

    C3 pads (1u cap) — "R3" — R3 pads (100k) — "C3" — R7 pads — "R7" — R9 pads — "R9"

R7 and R9 follow a label-below-part convention. Applying that same convention,
the label below C3's pads says "R3" and the label below R3's pads says "C3" —
i.e. the two labels are swapped. Applying a label-above convention instead makes
"C3" label R7. Measured: the "C3" text sits ~5.5 mm from C3's body and ~1.6 mm
from R7's body (closer to R7 than to anything else). There is no unambiguous
reading of this column; anyone probing/reworking will misattribute C3 and R3.
Must fix: move each refdes adjacent to its own part with a consistent convention.

### F2 — CONCERN: J1 refdes barely legible and jammed against D2's cathode marker
"J1" is printed rotated 90°, at roughly half the height of every other refdes,
at the bottom edge of the J1 courtyard, immediately left of D2's "K" cathode
letter (silk reads "⊣ J1 K D2 FLYBACK" as one jumble). At normal viewing size
the J1 glyphs read as a bracket symbol, and the cluster can be misread as part
of D2's polarity marking. Every other refdes on the board is horizontal and
full-size. Needs disposition: enlarge/relocate J1's refdes.

### F3 — CONCERN: J1 orientation / plug-insertion clearance not verifiable; extra holes unadjudicated
J1 has no 3D model (expected per missing_models.txt), so the renders cannot show
the jack body or its mating face. Facts visible: the courtyard sits fully
inboard — ~10-13 mm of board (carrying the SHIELD bond pad, TP6, R15 and silk
text) lies between the courtyard's west edge and the board edge. For a
side-entry shielded RJ45 this means the plug/boot travels over live board area,
and if the jack actually faces east it would face into D1/U1. Additionally the
footprint shows 8 staggered signal holes, 2 large NPTH posts on the west side,
and 4 extra PTH on the east side (presumably the RJHSE-5384 LED and/or shield
legs) — posts and LED/shield legs on opposite sides could not be reconciled
against the datasheet from renders alone. Needs disposition: confirm footprint
orientation vs the Amphenol RJHSE-5384 drawing and confirm the plug latch/boot
clears TP6/SHIELD pad and the board edge. (twin_report.csv J1 row is
FETCH-FAILED, so no machine check covered this either.)

### F4 — CONCERN: DNP marking inconsistent on silk
Schematic marks three parts DNP: D3 ("SMAJ6.0A TVS DNP"), L1 ("CM choke DNP"),
R15 ("shield bond DNP") — all three are correctly absent from the CPL and
bodiless in the twin. But the silkscreen says "TVS DNP" only at D3; L1 and R15
carry bare refdes with no DNP note. A hand-assembler or inspector will flag L1
and R15 as missing parts. Either mark all three or none.

### F5 — CONCERN: assembly_top drawing is effectively unreadable
`pdf/assembly_top-1.png`: the board is plotted at tiny scale in the top-left of
an A4 sheet; refdes + value strings collide into garbage (e.g. the top edge
reads "HH(ELD-RONB THAM ANDRP+AUDIO−"). Title block is empty (Title, Date, Rev
all blank). As an assembly reference document this fails its purpose; plot at a
scale that fills the sheet.

### F6 — CONCERN: pcb_layers pages carry no layer identification
All six pages plot the board tiny in the sheet corner with empty title blocks
(Title/Date/Rev blank) and no layer name anywhere on the page. Page 4 contains
only the board outline (bottom silk is empty), which is indistinguishable from
a failed plot without external knowledge. Add layer names to the title block.

### F7 — CONCERN: revision identity mismatch across documents
Board silk says "crow-mic-pod v1.1"; schematic title block says "Rev: dev"
(dated 2026-07-21); pcb_layers and assembly title blocks have Rev blank. A
release gate should show one consistent revision string.

### F8 — COSMETIC: schematic text collisions and clipped title-block text
- U1 symbol: pin names for pin 6/7 render jammed as "−IN_BOUT_B".
- L1 symbol (block 7): "B_IN"/"B_OUT" similarly jam ("B_JB_OUT").
- The description line overruns the right page border and is clipped:
  "...crow-array commissio|".
Otherwise the schematic is good: 7 clearly captioned functional blocks, ADR
references, readable values/pin numbers; connectivity is label-based (short
stubs + named labels) rather than long drawn wires, which is consistent and
followable.

### F9 — COSMETIC: H2 refdes reads as a superscript of the warning banner
"NOT ETHERNET — CUSTOM 5V PINOUT" ends with the small "H2" mounting-hole refdes
immediately after "PINOUT", reading like "PINOUT™"/footnote. Legal but
confusing; nudge H2's refdes toward its hole.

### F10 — COSMETIC: minor silk/feature grazes
- "C6" refdes has a small yellow tented-via/dot of the stitch grid touching the
  "C" glyph (reads "Ć6" in renders). Legible.
- "MIC+" label runs along/over its track right up to the J2 pad clearance;
  "R4" refdes overlaps a track junction + via ring in the bare render. Both
  legible (silk over masked copper prints fine), just tight.

---

## Specific checks requested

**Polarity — C1 (electrolytic, CP_Elec 6.3x5.4):** Model: white can with a black
sector on the can top on the EAST (right in top view) side = negative terminal
east. Silk: "+" printed WEST of the body (both twin and bare fab silk), plus the
CP_Elec outline. Model negative-east vs silk positive-west: CONSISTENT. This
discharges the C1 POLARITY-CHECK row in twin_report.csv.

**Polarity — D2 (SS14, SMA):** Model: black molded body with a light-gray
cathode band clearly visible on the WEST (left) end (top and iso views). Silk:
cathode bar glyph + "K" printed WEST of the body. Band-west vs K-west:
CONSISTENT. This discharges the D2 POLARITY-CHECK row in twin_report.csv.

**Population / floating parts:** Every CPL ref (28 parts) has a body in the twin
except J1/J2 (known-missing models) — matches missing_models.txt exactly. All
bodies sit centered on their pads (twin_report: 25/25 MODEL-REG-OK at 0.00mm);
no floating, tilted, or overlapping bodies seen in top/iso views. Bodiless
footprints L1, R15, D3 are all schematic-DNP and correctly absent from the CPL.

**Board outline / mounting:** ~94.5 x 44.5 mm confirmed against render scale;
4 concave quarter-round corner cutouts present and symmetric; 4 mounting holes
(H1-H4) present near corners, clear of parts and silk. Bottom side: no
components, no bottom silk (empty B_Silkscreen gerber, 1.3 kB), tented stitch-via
grid, J2 through-pads and RJ45 holes only. Nothing odd.

**Silkscreen functional labels:** Present and legible — top banner
"NOT ETHERNET — CUSTOM 5V PINOUT"; second "NOT ETHERNET" near J1; full pin map
"RJ45: 1 AUD+ 2 AUD− / 3 5V-BEEP 6 BEEP-RET / 4/7 5V 5/8 GND / CUSTOM 5V
PINOUT"; "MIC PADS J2 / MIC+ / MIC−" with square-pad pin-1 marking on MIC+;
"BEEPER", "FLYBACK", "TVS DNP", "SHIELD", TP1/TP2 AUD+/AUD−, TP3 2V5, TP4 5V,
TP5 GND, TP6 SHIELD; "crow-mic-pod v1.1". Nothing clipped by pads or holes.

**Edge renders:** Low profile throughout; tallest bodies are C1 (~5.5 mm can)
and BZ1 (~4 mm); no collisions, nothing protruding below the board, nothing
overhanging any edge. Caveat: J1 (RJ45, by far the tallest real part) has no
model, so the true height/overhang profile is NOT represented in these views.

**Carried over from twin_report.csv (not a render finding, should not be lost):**
U1 PAD-GEOM — our SOIC-8 pad span 4.95 mm vs JLC's 5.42 mm (d = 0.47 mm);
land patterns disagree and need adjudication against the OPA1678 datasheet.

---

## Summary

| Triage    | Count | IDs |
|-----------|-------|-----|
| DEFECT    | 1     | F1 |
| CONCERN   | 6     | F2, F3, F4, F5, F6, F7 |
| COSMETIC  | 3     | F8, F9, F10 |

F1 is on the fab-truth silkscreen layer and makes two refdes on the shipped
board ambiguous/swapped-looking; it must be fixed and re-rendered. F2/F3 need
disposition before ordering (J1 is also the one part no machine check covered).

RENDER REVIEW VERDICT: FAIL (superseded — see Delta re-review below)

---

## Delta re-review (same reviewer, fresh renders, 2026-07-21)

Board was regenerated to address F1/F2/F4/F7; dispositions supplied for
F3/F5/F6. Re-checked `renders/bare_top.png` (fab truth), `twin/twin_top.png`,
`pdf/schematic-1.png`, and verified the disposition documents exist on disk.

### Fixes verified

**F1 (C3/R3 refdes ambiguity) — FIXED.** Verified on both the twin and the
bare fab-truth silk. "C3" and "R3" now sit WEST of and vertically centered on
their own bodies; "R7" and "R9" sit EAST of theirs. Every label in the column
is side-adjacent to exactly one part; no ambiguous between-parts placement
remains. (The claimed generator-level nearest-neighbor silk check was not
independently exercised here — only its output was inspected.)

**F2 (J1 refdes) — FIXED.** "J1" is now upright, full-size, at the jack's
east/rear side (board ~87.2, 71.0), clearly inside/adjacent to the J1
courtyard edge. The D2 area now reads only "K D2 FLYBACK" — the old rotated
glyph is gone. D1 nearby carries its own label directly above its body, so
attribution is unambiguous.

**F4 (DNP silk) — FIXED.** "DNP" printed under R15 (clean, legible, clear of
pads) and at L1 (in the gap between the east pad pair). All three DNP parts
(D3, L1, R15) are now marked. Minor new cosmetic: L1's "DNP" abuts the
courtyard outline and reads "DNPI" at a glance; text sits inside the courtyard
(harmless — only visible when the choke is absent, which is exactly the DNP
case). Recorded under F10.

**F7 (revision identity) — FIXED.** Silk now reads "crow-mic-pod v1.0";
schematic title block reads "Rev: v1.0", Date 2026-07-21. This matches the
existing release identity (`07_releases/v1.0-2026-07-21/`) — the prior "v1.1"
silk was the outlier. Consistent across board and schematic. (pcb_layers /
assembly title blocks remain blank — covered by the F5/F6 disposition.)

### Dispositions reviewed

**F3 (J1 orientation/clearance) — ACCEPTED.** `01_docs/decisions/
0004-rj45-termination.md` exists; `06_build/ORDER_README_v1.0.md` carries the
substance: jack opening faces WEST toward the 1551WY gland wall, jack + plug
sit inside the lid's 81x31 recess (0.24 mm nominal over the jack body, EMI tabs
compress against the lid), bootless/solid-core plugs mandated, and a
FIRST-ARTICLE lid-close gate before fleet build. A per-pin audit
(`06_build/pin_audit/J1.md`, `review_connectors.md`) independently re-derived
the footprint (180-rotated not mirrored; the 4 east PTH are LED tails at the
rear). This coherently explains everything the renders showed (plug travels
over TP6/SHIELD by design). Residual risk is explicitly parked on a physical
gate, which is the right place for it.

**F5/F6 (assembly/pcb_layers plotting) — ACCEPTED AS DOCUMENTED LIMITATION,
kept open as CONCERN.** ORDER_README_v1.0.md line 76 directs "use
pdf/pcb_layers.pdf page 3 for silk truth" and the bare/twin renders are the
shipped primary visual references. The PDFs themselves are still poor
(tiny scale, colliding text, no layer names); acceptable for this release
since they are not the reference of record, but fix the plotter before the
next release.

**F8/F9/F10 — remain COSMETIC, recorded.** Still present in the re-render:
H2 abutting the banner; stitch-dot touching "C6" (and now also grazing the
new "C3" position, reading "Ç3"); schematic pin-name jams and clipped
title-block description; L1 "DNPI" courtyard graze.

### Updated summary

| Triage    | Count | IDs | State |
|-----------|-------|-----|-------|
| DEFECT    | 0     | — | F1 fixed and verified on fab truth |
| CONCERN   | 2     | F5, F6 | dispositioned (documented limitation), fix plotter next release |
| COSMETIC  | 3     | F8, F9, F10 | recorded, none block order |

Polarity re-confirmed unchanged in the re-render: C1 (+ west silk vs negative
sector east on model) and D2 (K west silk vs cathode band west on model) both
consistent. U1 PAD-GEOM adjudication (twin_report.csv) remains with the owner —
it was never a render finding, but do not lose it.

RENDER REVIEW VERDICT: PASS-WITH-NOTES
