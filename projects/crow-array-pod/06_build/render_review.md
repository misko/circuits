# crow-array-pod v1.1 — fresh-context visual render review

Reviewer: fresh-context visual gate (no prior session state). Sources: render3d_top.png,
render3d_iso.png, render3d_west.png, pcb_layers-1.png (F.Cu), pcb_layers-2.png (B.Cu),
pcb_layers-3.png (front silk), schematic-1.png, assembly_top-1.png, all under
`06_build/pdf/`. Crops were magnified 3–16x to inspect fine detail.

## 1. Jack orientation — PASS

The J1 hole field reads correctly as an RJHSE-5384 with mating face WEST:

- A 2x2 group of four small plated LED-tail holes sits on the WEST side of the field.
- The 8-position staggered contact-tail field (two columns, 4+4) is in the center,
  with a square pin-1 pad at the top of the east column and a pin-1 arrow on silk at
  the field's NW corner.
- Two large BLACK (unplated NPTH) board-lock holes sit EAST of the contact field.
- Two large plated shield-tab holes at the north and south ends of the field.

Pattern matches the expected west-facing orientation exactly. Caveat: there is no 3D
model for the jack (see item 8), so this is judged from the hole field only, and the
mating face appears inset several mm from the west board edge inside the courtyard
rectangle — enclosure clearance to the 1551WY wall/gland cannot be verified from these
images.

## 2. Safety silk — PASS

- Top banner: "NOT ETHERNET — CUSTOM 5V PINOUT" is large, centered on the north edge,
  clearly legible in the render and the silk plot.
- Near the jack: "NOT ETHERNET" sits NW of J1, and the four-line legend west of the
  jack reads exactly "RJ45: 1 AUD+ 2 AUD- / 3 5V-BEEP 6 BEEP-RET / 4/7 5V  5/8 GND /
  CUSTOM 5V PINOUT". No overlaps; all lines clear of pads and holes.
- Minor note: near the jack the warning is split into "NOT ETHERNET" (above legend)
  and "CUSTOM 5V PINOUT" (last legend line) rather than one combined string; both
  halves are adjacent to the jack, so intent is preserved.

## 3. Refdes legibility — PASS

On the fabricated silk (3D top render + pcb_layers-3): every visible refdes (R1–R15,
C1–C7, D1–D3, U1, L1, BZ1, J1, J2, TP1–TP6, H1–H4) is clear of part bodies and pads;
no collisions, no off-board text. TP function labels (SHIELD, AUD+, AUD-, 5V, GND,
2V5, MIC+, MIC-) are all legible. J1's refdes is small vertical text but readable.

Note: the ASSEMBLY drawing (assembly_top-1.png) has heavy text pile-ups (e.g.
"SHIELD BOND PAD"/"TP6"/"AUD+ AUDIO-" overlapping near the north edge,
"TPD2E2U06.../DR choke byp +", "100u 5VF" over C1, MountingHole strings over H2/H4).
That is a documentation-view artifact — the board silk itself is clean — but the
assembly PDF is hard to use as a build aid in those spots.

## 4. Polarity marks — PASS

- C1 electrolytic: "+" on the west side of the outline, plus chamfered-corner outline. Present.
- D2: "K" silk immediately west of D2's west pad, with "D2 FLYBACK" label above; a
  bracket line groups the label to the part. Present.
- D3: "K" west of the west pad, "D3" and "TVS DNP" labels adjacent. Present.
- BZ1: "+" on silk at the west (top-left) corner of the beeper footprint, "BEEPER"
  label above, "BZ1" below. Present.
- Caveat: a render can confirm the marks exist and sit near a specific pad, but not
  that the marked pad carries the right net; schematic shows D2 K on BZ_P (correct
  flyback sense, cathode to the driven-positive node) — final K-mark-to-net check
  belongs to DRC/netlist review, not visual.

## 5. Acoustic separation / floorplan — PASS

Mic pads J2 (MIC+/MIC-) are at the FAR EAST edge; beeper BZ1 + drive parts (R12,
D2, D3) are in the SOUTHWEST; U1 amplifier + gain network are center; RJ45 cable
entry is WEST. Mic-to-beeper distance is essentially the full board diagonal. The
mic bias/coupling parts (R2, 3.9k bias) are along the route toward J2. Sane.

## 6. Schematic readability — PASS

All seven story regions are present, boxed, titled, and orderable: 1 CABLE ENTRY
(RJ45 + TPD2E2U06 ESD, ADR-0001/0004), 2 CALIBRATION BEEPER (flyback + TVS-empty,
ADR-0002), 3 FILTERED 5VF, 4 MIC INPUT, 5 2.5V MIDPOINT, 6 OPA1678 (A = x1.5
non-inv, B = unity inverter -> diff x3), 7 OUTPUT (68R/leg -> CM-choke reserve).
The label-fragment style is followable; net names (AUDIO_P/N, BEEP_5V/BZ_P/BEEP_RET,
5VF, VMID, A_OUT/B_OUT, FB_A/FB_B) chain cleanly between regions. Decouplers C6
(100n U1) and C7 (10u 5V bulk) are drawn inside the U1 region 6. DNP intent (L1 CM
choke DNP, R13/R14 0R bypass, D3 TVS DNP, R15 shield-bond DNP) is annotated. No
overlapping/colliding text inside the regions.

Minor: the title-block description line ("Remote mic pod: AOM-5024L + OPA1678
balanced driver + CMT-8504 beeper; crow-array commissio…") runs off the right edge
of the sheet frame and is clipped.

## 7. Copper — PASS (with minor notes)

- B.Cu (pcb_layers-2) is a near-solid continuous GND plane over the whole board with
  a regular stitching-via grid. The only non-plane features are a handful of short
  via-to-via jumper traces under the U1 area and near the jack/beeper, each in its
  own clearance — at 16x they resolve as real routed jumpers, not orphan islands.
  One tiny capsule-shaped clearance north of J1 (near R15/TP1) is small enough that
  its end-vias don't resolve at plot resolution — worth a 10-second CAD check that
  it is a connected jumper, not an isolated sliver.
- F.Cu (pcb_layers-1) is pour + traces; RJ45 tail escapes are orderly (AUD pair exits
  east past D1; beeper nets drop south; several tails escape on B.Cu). GND pours
  around the jack have a few narrow necks/fingers, notably a small jagged pour finger
  at the NE corner of the jack clearance — nothing visually broken, but it is the
  kind of thing to let the sliver/min-width DRC confirm.
- The long MIC+ trace from R2 to J2 runs in a clean diagonal clearance channel across
  the east pour; MIC- ties directly into the top pour (GND), consistent with the
  schematic. East pour regions flanking the channel are stitched to the plane.

## 8. Everything else odd (minor list)

1. **render3d_west.png is effectively blank** — an edge-on board sliver with no
   component bodies. No 3D models exist for J1, BZ1, or the TPs, so the west view
   proves nothing about the jack body/mating-face protrusion. The orientation call in
   item 1 rests entirely on the hole-field pattern.
2. **Jack inset from west edge**: J1's courtyard starts several mm east of the board
   edge. Whether a plug can reach the jack through the 1551WY wall/gland opening is a
   mechanical-fit question these images cannot answer.
3. **Assembly drawing text collisions** (see item 3) — worth regenerating with fewer
   visible fields if it will be used at the bench.
4. **Layer-plot title blocks are empty** (Title/Rev/Date blank on pcb_layers pages;
   only the sheet filename is filled). Schematic title block is complete (Rev v1.1,
   2026-07-19).
5. **DNP marking asymmetry on board silk**: D3 gets an explicit "TVS DNP" on the
   board, but L1 (CM choke DNP per schematic) has no DNP marking on the board silk —
   only in the assembly view. R15 (shield bond DNP) likewise unmarked on board.
6. Corner scallops (four large radiused notches) — presumably clearing the 1551WY
   corner bosses; H1–H4 M2.5 holes sit inboard of them. Assumed intentional.
7. Silk version string "crow-array-pod v1.1" matches schematic Rev v1.1. Consistent.
8. Board-lock NPTHs render black (unplated) — correct for RJHSE-5384 pegs.

## Overall verdict — PASS (release-quality visually, with minor follow-ups)

Nothing observed is release-blocking. All eight gate questions come back PASS; the
residual risk is concentrated in what renders cannot show: (a) the jack's mechanical
reach to the enclosure wall (no 3D model, blank west view), (b) net-correctness of
the D2/D3 K marks, and (c) two small copper features (capsule clearance north of J1
on B.Cu; narrow pour finger NE of J1 on F.Cu) that a DRC sliver/min-width pass or a
10-second CAD look should confirm. Recommend closing those three before ordering.
