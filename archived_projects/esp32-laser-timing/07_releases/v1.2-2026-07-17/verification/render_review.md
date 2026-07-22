# Render review — esp32-laser-timing v1.2

v1.2 corrects the twin RENDER only (no fab change vs v1.1). One issue found
and fixed:

- **J1 (USB-C, HRO TYPE-C-31-M-12, C165948) — model orientation.** JLC's
  3D model is drawn 180deg rotated vs the footprint, so v1.0/v1.1 rendered
  the receptacle mouth facing INBOARD (east), body 2.1mm off courtyard.
  PAD fit is perfect (0.00mm, 22/22 = JLC CAD) — copper unaffected. Fixed
  with an evidence-backed `model_rot_z: 180` adjudication (confirmed metric
  AND visual): body now on courtyard 0.09mm, mouth faces WEST toward the
  board edge (courtyard front 50.01mm = board edge 50.00mm, flush). This
  was a render-faithfulness bug present since v1.0.
- All other parts unchanged from v1.1: 72 refdes on silk (I10 PASS), U2
  mounted via pad_alias, no mirror/off-pad, functional labels intact.

Disposition: twin render now truthfully depicts the assembled board.
