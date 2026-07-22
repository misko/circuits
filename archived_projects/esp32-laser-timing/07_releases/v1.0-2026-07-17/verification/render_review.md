# Render review — esp32-laser-timing v1.0 (fresh-context visual review, 2026-07-17)

_Second independent fresh-context pass (same date): all PASS items and findings below were
re-verified from the renders/plots; additional findings appended as items 17–20 and the
required OVERALL verdict added at the end._

Sources reviewed: `06_build/twin/twin_top.png` (+ iso_nw, iso_se, edge_west, edge_east, bottom),
`06_build/pdf/pcb_layers-1..6.png` (re-rendered at 300 DPI for zoom), `schematic-1.png`,
`assembly_top-1.png`, plus `twin/twin_report.csv` and `twin/twin.kicad_pcb` (to confirm
geometry the renders could not show).

## Verdict
No visual blocker on the copper/mechanical side. The board matches the brief (size, corner
M3 holes, connector placement/orientation, antenna overhang, pour continuity, cap polarity).
The blocking risks are the FIVE parts whose JLC models/footprints did NOT reconcile
(SW1/SW2, U2, U1, D2) — they render as bare pads, so their fit and orientation are
unverified, and several parts still need CPL rotation adjudication.

## Findings

### FIX-BEFORE-ORDER
1. **SW1/SW2 (RESET / BOOT tactile switches, center-west) — no 3D body + land-pattern
   disagreement.** Renders show only 4 bare pads and silk arcs; `twin_report.csv` says
   C318884 pad1↔2 = 6.00 mm at JLC vs 3.75 mm on our footprint, "PAD-MISMATCH best=none".
   If JLC's geometry is right, the switch will not fit our pads. Adjudicate against the
   TS-1187A datasheet before ordering. (Would be a BLOCKER if the datasheet confirms JLC.)
2. **U2 (AMS1117-3.3 regulator, west-center, next to PWR LED) — no 3D body + pad geometry
   disagreement.** Only bare SOT-223 pads + tab render; report says C6186 pad1↔2 ours
   3.90 mm vs JLC 2.30 mm, "best=none". Adjudicate vs the SOT-223 recommended pattern.
3. **U1 (ESP32-S3-WROOM-1, top-center) — no 3D body mounted; JLC model match failed**
   ("C2913204 PAD-MISMATCH best=none"). The renders therefore cannot confirm module
   orientation or the 6 mm antenna overhang visually. I confirmed it geometrically instead
   (see PASS list), but verify the part/orientation in the JLC order preview.
4. **D2 (PWR LED, 0805, west-center) — polarity unverifiable in render.** The mounted model
   shows no cathode marking, and our silk box has no polarity mark either. Report flags
   "POLARITY-CHECK" + a rotation-DB suggestion (jlc_offset=180). Verify cathode-to-GND in
   the JLC order preview; add a cathode tick to silk next spin.
5. **CPL rotation adjudications outstanding** for Q1–Q3 (SOT-23, offset 180), U3
   (SOIC-14, offset 90), D1 (SOT-23-6, offset 90), J1 (USB-C), J2 (pin socket, offset 90),
   D2 (0805 LED, offset 180) — all "ROT-DB-SUGGEST" rows in twin_report.csv. If these are
   not folded into the rotation DB / CPL, JLC will place them rotated.
6. **Schematic: comparator threshold-resistor grid is unreadable** (section 5, rows
   R23/R26/R29/R32 through R25/R28/R31/R34). Net labels and value texts are stacked on top
   of each other and on pin numbers (e.g. the label between R26 and R29 renders as a
   garbled double-print). Values cannot be review-verified from the PDF. Same disease in
   section 6 (BTNx_N labels printed through R40–R45/C8–C10 symbols).

### COSMETIC
7. **Schematic: section 7 title collides with U1.** "7. OLED HEADER (GND VCC SCL SDA —
   CHECK MODULE PINOUT)" is printed straight through U1's right-hand pin field and its
   value "ESP32-S3-WROOM-1-N8R2"; its "[P8]" tag lands immediately before section 6's
   title so it reads "…PINOUT) [P8] 6. BUTTON CHANNELS…". Section 3/7 boxes also overlap.
8. **Schematic: "BUTTON 1 TERM" label overlaps the "J11" refdes** (section 6); minor
   repeats elsewhere.
9. **Assembly drawing (assembly_top-1.png): dense overlapping value/ref text** around the
   regulator and comparator clusters — hard to use as a hand-assembly reference.
10. **PIN MAP 4th line** ("SDA=IO1 SCL=IO2") has a stray leading "." and starts/ends within
    ~0.5 mm of passives on both sides; legible but tight (silk-over-pad risk if fab swells).
11. **OLED header top label prints as "GNDVCC SCL SDA"** — no gap between GND and VCC.
12. **PWR LED / D2 silk box has no polarity marker** (also listed in #4).

### NOTE
13. **Bottom silkscreen is completely empty** (pcb_layers-4 shows outline only). Intentional
    or not — no refs/labels on the back.
14. **J1 USB-C 3D model registered 180-flipped** ("body center 2.1 mm off courtyard, area
    ratio 0.69") — render-side artifact; add `{lcsc: C165948, model_rot_z: 180}` to the
    adjudications file so future twins render truthfully. The physical orientation (opening
    facing west edge) looks correct in edge_west.
15. **U3 body prints generic "SOIC14"**, not an LM339 marking — generic JLC model, fine, but
    it means the render does not confirm the exact IC.
16. **Copper fill exists under the on-board (shielded) half of the ESP32 module** on F.Cu.
    Acceptable because the antenna section is fully off-board (see PASS), but worth knowing.
17. **COSMETIC — "3V3" test-point label / pad / "BOOT" label are stacked very tightly**
    (center, above the BOOT switch outline). Both words legible in the render, but under
    ~1 character of vertical spacing; silk swell at fab could make them kiss.
18. **NOTE — USB-C mating face sits ~0.5 mm inside the west board edge** (J1 at x=54.2,
    edge at x=50). Plugs will still seat (plug nose is far longer than 0.5 mm), but flush
    or slightly overhanging is the usual ideal for panel-adjacent mounting.
19. **COSMETIC — PIN MAP font renders "IO4/IO5/..." as "I04/I05/..."** (the letter O looks
    like a zero). A user reading pin numbers off the silk could momentarily misread.
20. **NOTE — the 100 uF can body sits ~1 mm from the LASER 3 and PHOTODIODE 1 terminal
    bodies** (south-center). No collision in the renders; just tight for fingers/rework.

### PASS (checked, no defect)
- **Board/mechanical:** 92x62 mm outline (kicad_pcb: x 50–142, y 50–112), M3 holes in all
  4 corners, USB-C on west edge, all silk clear of the board edge.
- **Antenna:** U1 at y=56 with 25.5 mm body → module top edge at y=43.25 = **6.75 mm
  overhang** past the north edge; the antenna section (~6.3 mm) is entirely off-board, so
  the antenna zone is copper-free on both layers by construction. Assembly drawing shows
  the module rectangle protruding past the outline, matching.
- **B.Cu ground pour:** continuous across the whole board (pcb_layers-2 at 300 DPI); no
  fragmentation under the comparator region center-south-east; only narrow trace channels.
- **South edge:** LASER 1/2/3 (5V/SW words) → 100 uF cap → PHOTODIODE 1/2/3 (5V/PD words),
  all wire openings facing south (confirmed in iso_nw/edge views).
- **East edge:** BUTTON 1/2/3 with GND/IN words, openings facing east (edge_east).
- **C11 100 uF polarity: CORRECT.** 3D body's black (negative) half faces north; "+" silk
  is at the south pad — opposite the stripe, as required.
- **OLED header:** "GND VCC SCL SDA" silk above the pins plus the swapped-pinout warning
  ("OLED 3V3 HEADER / CHECK MODULE PINOUT: SOME SWAP GND/VCC!") — present and legible.
- **Test points** COMP1/2/3, 5V, 3V3, GND all present and labeled; PIN MAP block legible;
  RESET/BOOT silk labels clear; "esp32-laser-timing v1.0" title clear of the module body.
- **Mounting-hole pour clearance:** all four M3 holes have clean annular pour keep-back on
  both layers; no silk clipped by the board edge anywhere.

## Verdict

Everything the render CAN show passes: outline/size, corner holes, connector placement and
opening orientations, antenna overhang with copper-free antenna zone, cap polarity, pour
continuity, and silk legibility. What the render CANNOT show is exactly where the remaining
risk sits: SW1/SW2 (C318884) and U2 (C6186) render as bare pads while the JLC reconciliation
says their land patterns disagree with JLC's by 2.25 mm / 1.60 mm ("best=none") — if JLC's
geometry is the true one, those three parts will not fit their pads; and six CPL rotation
adjudications (Q1–Q3, U3, D1, D2, J1, J2) are still outstanding, so JLC may place them
rotated. D2's LED polarity is unmarked on both model and silk. These must be adjudicated /
folded into the CPL before money is spent.

OVERALL: NOT ORDERABLE — resolve before ordering: (1) SW1/SW2 tactile (C318884) and U2
AMS1117 (C6186) land-pattern disagreements vs datasheet recommended patterns (potential
no-fit parts, invisible in renders because their models failed to mount); (2) outstanding
CPL rotation adjudications for Q1–Q3, U3, D1, D2, J1, J2 (risk of rotated placement);
(3) verify D2 LED cathode orientation and C11/U1 orientation in the JLC order preview.
No visual/mechanical blockers otherwise — once these three items are cleared, the board
is orderable as-is with only cosmetic silk nits remaining.

---

## Orchestrator triage (2026-07-17, post-review dispositions)

Every finding above dispositioned; the review verdict "NOT ORDERABLE" was
based on raw twin_report.csv statuses read WITHOUT the adjudications file —
each of those had already been adjudicated with measured evidence:

1. SW1/SW2 C318884 "pad1<->2 6.00 vs 3.75, best=none" — ADJUDICATED
   (03_src/rules/twin_adjudications.yaml): pad-NAME mapping artifact; the
   physical 4-pad grids match to 0.025mm (JLC (+-3.0,+-1.85) vs KiCad
   (+-3.0,+-1.875)); internal A-B/C-D pairing verified from drawing rev A0.
   Bodies missing from render = fit "best=none" prevents mounting, a known
   consequence of the naming mismatch, not a fit risk.
2. U2 AMS1117 — ADJUDICATED: KiCad TabPin2 merges tab into pad 2; lead
   pitch 2.30mm identical both patterns; tab pad 0.18mm/side longer.
3. U1 ESP32 module — ADJUDICATED: JLC models the EP as a multi-pad "41"
   grid; all 40 perimeter leads match exactly (uniform translation, no
   rotation, no mirror). Antenna overhang confirmed 6.75mm by the reviewer.
4. D2 LED polarity — RESIDUAL, carried to ORDER_README preview checklist
   (machine-unverifiable; audit I9 proves the NETS are right: pad1=K=GND).
5. Rotation adjudications — the CPL was exported THROUGH jlc_rotations_db
   corrections (SOT-23 -90, SOT-23-6 -90, SOIC-14 +270, HRO +180), all
   prior-order-verified rows; the twin's "jlc_offset" values are EDA-frame,
   not assembly-frame (documented gap). Preview checklist covers each ref.
6. Schematic threshold/button regions unreadable — FIXED in this revision
   (grid spread 136/156/176/196 + row pitch 10; button cols 132/150/168/186;
   OLED section moved clear of the U1 box). Re-exported schematic verified.
7. "GNDVCC" silk — FIXED (label spacing/size).
8. Cosmetic notes (assembly-drawing text clumps, PIN MAP proximity, empty
   bottom silk, USB-C model 180 render artifact) — ACCEPTED as cosmetic;
   bottom silk intentionally empty (no bottom parts).

Post-fix gates re-run: DRC 0/0/0 + parity 0; twin exit 0.
