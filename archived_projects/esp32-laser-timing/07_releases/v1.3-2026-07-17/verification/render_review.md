# Render review — esp32-laser-timing v1.3

v1.3 RESTORES the correct J1 (USB-C) render that v1.1 already had, undoing
an erroneous v1.2 change. No fab change across v1.1/v1.2/v1.3.

- **J1 (USB-C, C165948).** JLC's own footprint mounts this model at
  rot_z=180 ((rotate 0 0 180) in jlc.pretty/*.kicad_mod) — authoritative.
  v1.1 mounted at 180 (correct). v1.2 added model_rot_z:180 -> net 0,
  CANCELLING JLC's built-in flip and rotating the mouth inboard (WRONG).
  v1.3 reverts: model mounts at 180, contacts over the east pads
  (x53.15-58.24), mouth at the WEST board edge. Verified by reading JLC's
  .kicad_mod rotation AND the leads-on-pads render, not the MODEL-REG
  metric (which is a false alarm here: the USB-C body bbox is asymmetric
  y[-5.05,+2.85], so bbox-center vs courtyard-center is offset ~2mm even
  when correct — the same trap as the Q1 DPAK).
- MODEL-REG for J1 is dispositioned as a FALSE ALARM with NO rotation
  override (twin_adjudications.yaml). PAD fit perfect (0.00mm).
- All other parts unchanged: 72 refdes on silk (I10 PASS), U2 pad_alias
  mount, functional labels intact.
