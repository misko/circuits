# Changelog

## v0.1.1-2026-08-15

- Packaging-only corrective release after the publication boundary found that
  v0.1.0 had rewritten custom 3D-model paths inside its archived PCB. Copper,
  schematic connectivity, fabrication files, BOM/CPL, STEP and reviewed live
  board remain unchanged.
- Preserve `source/pi_usb_port_switch.kicad_pcb` byte-for-byte with the live,
  reviewed board. Add a nested exact source tree whose original relative paths
  resolve the vendored custom footprint and model libraries offline.
- Archive the four exact-artifact final reviews under `08_reviews/` so their
  release copies are independently bound and publication-verifiable.

## v0.1.0-2026-08-15

- Initial hardware-only release of the four-channel Raspberry Pi USB inline
  power/data switch.
- Four identical USB 3 Gen 1-capable paths with accepted USB 2 fallback;
  independent power-only, connected and fully-off states.
- Separate protected 5.15-5.25 V / at least 5 A input, four 0.9 A current-limited
  outputs, deterministic pull-down defaults and hardware data/power interlock.
- JLCPCB four-layer advanced package with selective 0.25 mm-drill via-in-pad
  fill/cap, top SMT and declared through-hole/hand-assembly split.
- Layout sealed at board SHA-256 `d4bc778c1c80453ec7b198e1bf428b22cb03d414c4a0d86c89ab74d6facc4094`:
  DRC 0/0/0, 282/282 electrical invariants, 56/56 critical pairs, 749/749
  via-process coverage, 190/190 models and 185/185 JLC twin bodies.
- Order verdict remains DO-NOT-ORDER until JLC uploader/process previews are
  accepted; production remains HOLD pending the five-board first-article plan.
