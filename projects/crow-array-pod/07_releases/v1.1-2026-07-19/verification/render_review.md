# Render review — crow-array-pod v1.1 (RJ45 delta)

Fresh-context visual review, 2026-07-19. Scope: v1.1 delta (Amphenol RJHSE-5384
RJ45 jack J1 replacing the v1.0 screw terminal) + general silk/refdes quality.
Inputs: `pdf/render3d_{top,iso,west}.png`, `pdf/pcb_layers-1..6.png` (re-rasterized
from `pdf/pcb_layers.pdf` at 300 dpi for measurement, 11.811 px/mm, page origin =
board origin), `pdf/assembly_top-1.png`, `pdf/schematic-1.png`, `twin/twin_*.png`,
`twin/twin_report.csv`. Reference: ADR-0004 section (c). J1 has no 3D model
(twin_report: `J1 NO-CAD`) — J1 judged from its hole field, as instructed.

## 1. Jack orientation / mate direction — PASS

From the F.Cu plot (layers-1) and the top renders, the J1 hole field at board
(78, 71) rot 90 reads, west to east:

- Two large **black unplated** Ø3.25 board-lock holes, both at **x ≈ 75.5 mm**
  (y ≈ 61.1 and 73.8) — the **WEST** column.
- The staggered 8-contact field east of them: two columns at x ≈ 78.0 / 79.8,
  contacts running y ≈ 63.9–71.0.
- The four small plated LED-tail holes at **x ≈ 84.6 mm** (y ≈ 60.6, 62.9, 72.0,
  74.3 — two north/south pairs) — the **EAST** extreme of the pattern. Two SH
  shield-tail holes at x ≈ 78.9, y ≈ 59.3 / 75.6.

Applying the corrected doctrine (NPTH snap posts mark the FACE side): posts west
→ **mating face WEST**, at x ≈ 75.5 − 5.46 = **70.0 mm**, opening toward the
M12 gland wall (west/left). LED tails mark the rear, east. This matches
ADR-0004's corrected rot-90 placement; the earlier 180-backwards mount
(opening east) is NOT what the plots show.

## 2. 1551WY clearance vs recess (x 56.75–137.75, y 56.75–87.75) — PASS

Measured hole field puts the face at x ≈ 70.0, so the body spans
x ≈ 70.0–85.8 (15.75 deep) — consistent with the ADR's claimed ~69.5–86.3
within pixel-measurement error (±0.5 mm). Checks:

- Body inside recess: x 70.0–85.8 ⊂ 56.75–137.75; body y extent (ADR 57.6–77.3,
  silk outline on layers-3 agrees, spanning ~y 57.5–77.5) ⊂ 56.75–87.75, with
  ~0.85 mm margin at the north edge. OK.
- Plug volume: 12 mm west of the face → west extent x ≈ 58.0 ≥ recess west edge
  56.75, ~1.25 mm margin. OK (ADR claims face ≥ 68.75; measured 70.0). OK.
- Other tall parts (from twin board positions + twin edge renders): C1 e-cap
  Ø6.3×5.4 at (91.6, 83.6), BZ1 CMT-8504 (~4 mm) at (72, 84), U1 SOIC-8,
  L1 WE-SL2 (~2.4 mm) at (93.7, 54.2). All ≤ 5.4 mm tall — under even the
  7.90 mm perimeter-band headroom, so nothing besides J1 depends on the recess.
  BZ1's body edge pokes ~0.5 mm south of the recess rectangle and L1 sits north
  of it, but both are far below the band headroom — harmless. The jack is the
  only >7.9 mm part and it is inside the recess. `twin_edge_west.png` confirms
  the tallest silhouettes are C1 and BZ1 (no J1 model to check the 13.46 mm
  body visually — ADR's CONDITIONAL FIT / first-article lid gate still applies).

## 3. Safety silk — PASS

- North banner **"NOT ETHERNET — CUSTOM 5V PINOUT"** present along the north
  edge, spanning x ≈ 102.4–133.5 (center ≈ 118). L1's silk outline ends at
  x ≈ 98.4 (y 51–59) — **~4 mm clear gap, no collision** (silk_north crop).
  The tiny "H2" refdes sits just past the banner's east end; adjacent but not
  overlapping.
- Jack-adjacent warning: a second **"NOT ETHERNET"** at x ≈ 56.6–65.3, y ≈ 58 —
  west of the jack, above the plug zone, visible with a plug inserted.
- Per-contact legend west of the jack, in the plug zone (x ≈ 57–68.6, ends
  1.4 mm clear of the face at x 70): "RJ45: 1 AUD+ 2 AUD− / 3 5V-BEEP
  6 BEEP-RET / 4/7 5V 5/8 GND / CUSTOM 5V PINOUT". Matches the ADR-0004 net
  map (1 AUDIO_P, 2 AUDIO_N, 3 BEEP_5V, 6 BEEP_RET, 4/7 5V, 5/8 GND). ~0.85 mm
  stroke text — legible in the 300 dpi plot and the top render, no collisions.

## 4. Refdes on silk — PASS with one nit

All parts carry visible refdes on F.Silk: H1–H4, TP1–TP6 (with function labels
SHIELD / AUD+ / AUD− / 5V / GND / 2V5), R1–R15, C1–C7, D1–D3, L1, U1, BZ1, J2
("MIC PADS", MIC+/MIC− labels). Functional labels present at connectors/TPs
(BEEPER, FLYBACK, TVS DNP, MIC PADS, per-TP nets). **J1's refdes exists but is
tiny and rotated 90°, placed just south of the jack outline hard against D2's
"K" cathode mark** (renders as "⊣ K" at ~(77, 82)) — legible only under
magnification and could be misread as part of D2's marking. Cosmetic; the jack
is unambiguous anyway. Pin-1 triangle present at the jack outline's south edge.
B.Silk is empty (no bottom parts) — correct.

## 5. Polarity marks vs JLC models (twin POLARITY-CHECK) — PASS

- **C1** (CP_Elec 6.3×5.4, flagged POLARITY-CHECK): our silk "+" is WEST of the
  body. The JLC model's can top shows its **black crescent (negative-side
  marking) on the EAST half** (twin_top / twin_iso crops). Positive west,
  negative east → **silk and model agree**.
- **D2** (SMA flyback, flagged POLARITY-CHECK): our silk "K" is WEST of the
  body. The JLC model shows its **light cathode band at the WEST end** of the
  package → **agree**.
- D3 (TVS, DNP): no body mounted in the twin (correct for DNP); "K" + "TVS DNP"
  silk present for hand-fit later.

## 6. Other observations (minor)

- `render3d_*.png` are model-less board renders (bare board + silk);
  `render3d_west.png` is nearly information-free (an edge-on black bar). The
  twin renders carry the model evidence — fine, but the 3D set adds little.
- B.Cu is a clean solid GND pour; no slivers, isolated islands, or off-board
  text seen on layers 1–6. Mask layers show normal openings.
- twin_report carries a pre-existing **U1 PAD-GEOM** flag (our pad1↔8 span
  4.95 mm vs JLC model 5.42 mm) + ROT-DB suggestion — not part of this delta;
  should remain on the adjudication list.
- pcb_layers/assembly title blocks have empty Title/Rev fields (sheet id only);
  schematic title block reads "crow-array-pod", Rev: dev. Cosmetic.
- Board version string "crow-array-pod v1.1" present on F.Silk south edge.
- Assembly drawing center is crowded (value strings overlap near TP4/TP5) —
  drawing-only, board silk itself is clean.

## Verdict

**PASS**, with conditions:

1. **First-article lid-close gate stands** (ADR-0004c): jack body height cannot
   be verified visually (no J1 model) — close the 1551WY lid on the first
   assembled pod before fleet build; trim EMI tabs / fall back to RJHSE-L384 if
   it binds.
2. Carry the pre-existing U1 PAD-GEOM (4.95 vs 5.42 mm) adjudication before any
   re-spin that touches U1.
3. Cosmetic, next rev only (no fab change warranted): make J1's refdes larger /
   move it clear of D2's "K" mark.
