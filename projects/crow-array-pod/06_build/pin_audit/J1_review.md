# Fresh-context pin review: J1 (Amphenol RJHSE-5384), crow-array-pod v1.1

Reviewer: fresh-context agent, 2026-07-19. Inputs: pin dossier `06_build/pin_audit/J1.md`,
catalogue `02_parts/RJHSE-5384/Amphenol_ModularJacks_Catalogue_2015-04.pdf` (300 dpi renders
of PDF pp.5/6/7 = catalogue pp.4/5/6), central port map
(`crow-array-central/03_src/generate_schematic.py` `port_channel()`), D28 in central
`01_docs/BRIEF.md`, system table `crow-array/01_docs/BRIEF_SOURCE.txt` (T568B pairs).
Numbering re-derived from the catalogue figures; part.yaml note NOT trusted as input.

## VERDICT: FAIL — pad numbering and all nets are correct, but J1 is mounted 180 deg
## backwards on the board: the mating face points EAST (into the board), not WEST.

---

## (a) Footprint numbering vs catalogue figure — PASS (geometry); FAIL (board orientation)

Derived independently from the RJHSE-548X RECOMMENDED PCB LAYOUT (PDF p.5, catalogue p.4),
cross-checked against RJHSE-L38X (PDF p.6) and RJHSE-538X04 multiport (PDF p.7 — same
labels per port):

- Contacts: two staggered rows, **8 at upper-left, 1 at lower-right** (figure orientation,
  LED holes at top); numbers descend left-to-right alternating rows; even pins in the row
  nearer the LED row. Stagger 1.02 mm, in-row pitch 2.03 mm, row separation 1.78 mm.
- LED holes: left group labelled **"12 11"**, right group **"10 9"** (so 9/10 sit on the
  pin-1/2 end, 11/12 on the pin-7/8 end); LED pair pitch 2.29 mm, outer span 13.72 mm.
- Shield holes o1.57, span 16.26 mm; mounting NPTH o3.25, span 12.70 mm.

The KiCad `RJ45_Amphenol_RJHSE538X` pad table (per dossier and library file) is this figure
**rotated exactly 180 deg** — every pitch and span above ties out 1:1, and the figure's
own vertical chain closes against the pad table exactly: post->odd row .100 [2.54],
post->SH .135 [3.43], post->even .170 [4.32], post->LED .360 [9.14].

- **Winding**: sweeping pins 1..12 around the centroid of the catalogue figure gives **CW
  (top view)**; the dossier's computed winding is **CW (top view)**. Match. Not a mirror:
  the label asymmetry (9/10 grouped with pins 1/2) is preserved under rotation, and the
  TIA-568 cross-check (latch-up jack front view => pin 1 on viewer's right, where the
  548X front view puts LED 1 = holes 9/10) confirms the figure is a true component-side
  top view. A mirrored pattern would also flip the even/odd stagger and the jack could
  not physically insert. **Pad numbering: PASS.**

**FAIL finding — mating-face side.** The dossier's part.yaml note claims "even-numbered
contact row and LED row are both on the mating-face side in both sources." That is
**wrong**, and the error is load-bearing. From the L38X/548X SIDE VIEW dimension chains
(measured on the 300 dpi renders, all closing to <0.1 mm):

- front face -> shield front stub: **.100 [2.54]**
- front face -> mounting-post centerline: **.215 [5.46]** (dash-dot centerline in the
  side view lands exactly on the post; 508X non-shielded shows the analogous 2.29/5.08)
- therefore front face -> odd contact row = 5.46 + 2.54 = **8.0 mm**, even row 9.78 mm,
  **LED tails 14.6 mm from the face = 1.15 mm from the REAR** of the 15.75 mm body.

The KiCad library footprint body (F.Fab local y -8.00..+7.75, posts at -2.54, LED row at
+6.60) matches this chain **exactly**: face->post 5.46, face->odd 8.0, LED->rear 1.15.
So: **the LED-tail row marks the REAR of the jack; the mating face is on the
mounting-post side, opposite the LED row.**

Consequence on the pod board: J1 sits at (78.0, 64.0) rot -90 on F.Cu. Computed absolute
pads (verified against the generator's own passing asserts): LED pads 9-12 at x=71.4
(west of contacts at 76.2-78.0), pin 1 north — and the mounting NPTHs land at x=80.54,
**EAST** of the contacts. The mating face is therefore at x ~86, **pointing EAST into the
board interior**. `generate_board.py` (line ~224) asserts "mating face WEST (LED-tail
pads 9-12 mark the mating face and must sit west of the contact pads)" — the assert
enforces exactly the backwards orientation, and the ADR-0004 recess check reserves the
12 mm plug volume on the WEST side, where the jack's REAR actually sits. A plug cannot
be inserted from the west enclosure opening. **Dead board mechanically.**

Correct fix direction: J1 rotation +90 (LED row east, posts/face west), then re-run the
recess/courtyard checks with the corrected premise, and fix the part.yaml orientation
notes. Note the connectivity below is by pad number and survives the rotation error —
this is a body-orientation failure only.

Cross-project note: the same false doctrine is recorded in D28 / both projects'
part.yaml notes ("pod re-verification ... conclusion matches the central project's").
The **central** board itself is nevertheless CORRECT: its jacks are placed at rot 0 with
"openings north", which puts local -y (the true face, post side) toward the north edge.
The doctrine, not the central board, is wrong — but it should be corrected before it is
applied to any future placement.

## (b) Contact-by-contact interop truth table — PASS

Straight-through T568B cable: pod contact n connects to central contact n. Central port
map (`port_channel()` rj_nets): 1=AUD_Pn, 2=AUD_Nn, 3=BEEP_5Vn, 4=5V_AUDn, 5=GND,
6=BEEP_RETn, 7=5V_AUDn, 8=GND, 9-12=NC, SH=GND. Consistent with D28 (board-correct map:
4=5V, 5=GND, 7=5V, 8=GND, feed+return per pair) and BRIEF_SOURCE T568B table.

| pin | function | expected (datasheet + interop authority) | pod board net | verdict |
|-----|----------|------------------------------------------|---------------|---------|
| 1 | CT1 | audio pair + (orange) -> central AUD_Pn | AUDIO_P | PASS |
| 2 | CT2 | audio pair - (orange) -> central AUD_Nn | AUDIO_N | PASS |
| 3 | CT3 | beeper 5V feed (green) -> central BEEP_5Vn (PTC F2x from 5V) | BEEP_5V | PASS |
| 4 | CT4 | 5V audio feed (blue) <- central 5V_AUDn (PTC F1x from 5V) | 5V | PASS |
| 5 | CT5 | ground return (blue) -> central GND | GND | PASS |
| 6 | CT6 | beeper switched return (green) -> central BEEP_RETn (Q_n drain) | BEEP_RET | PASS |
| 7 | CT7 | 5V audio feed (brown, parallels pair 4/5) <- central 5V_AUDn | 5V | PASS |
| 8 | CT8 | ground return (brown) -> central GND | GND | PASS |
| 9 | LED1_A | no connection required (internal LED unused) | unconnected | PASS |
| 10 | LED1_B | no connection required | unconnected | PASS |
| 11 | LED2_A | no connection required | unconnected | PASS |
| 12 | LED2_B | no connection required | unconnected | PASS |
| SH (x2) | shield | SHIELD (single-point bond topology, see (c)) | SHIELD | PASS |

DC-on-pair sanity: every DC current flows out and back on one twisted pair (blue 4/5
feed+return, brown 7/8 feed+return, green 3/6 beep feed+switched return, orange 1/2
differential audio). No split-pair DC. PASS.

## (c) Shield topology — PASS

Pod: both SH pads -> SHIELD net; SHIELD reaches GND only through DNP R15 (with TP6 bond
pad) — verified in `generate_schematic.py` (TP6 "SHIELD BOND PAD", R15 "shield bond DNP"
SHIELD->GND). Central: SH -> GND hard. Cable shield is therefore grounded at exactly one
end (central star point); pod end floats unless R15 is deliberately fitted. Single-point
bond preserved, no shield ground loop. Matches D28's declared intent. PASS.

## (d) LED pins 9-12 unconnected — PASS

The RJHSE-5384 has two internal LEDs whose leads are pins 9-12. Leaving them open is
electrically safe (LEDs simply never illuminate) and the pod has no LED drive circuitry.
Holes are present so the part seats mechanically (datasheet: "holes 12 req'd based on
2 LEDs"). Sane. PASS.

## Findings summary (protocol format)

- VERDICT: **FAIL** (blocks order)
- J1 orientation: expected mating face WEST off the board edge (ADR-0004); board has
  face EAST (LED/rear row west). Datasheet side-view chain proves LED tails are 1.15 mm
  from the REAR, mounting posts 5.46 mm from the face — the generator's "LED tails mark
  the mating face" premise is inverted. Fix: rot +90, correct the assert, recess check,
  and part.yaml notes (both projects); re-check whether sealed pod v1.0 shares the error.
- J1 pads 1-8, SH (all): datasheet-derived numbering and interop-expected nets match the
  board exactly — PASS, and connectivity is unaffected by the rotation fix.
- J1 pads 9-12 (LED): expected NC, board NC — PASS.
