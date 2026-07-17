# CHANGELOG — esp32-laser-timing

## v1.1 — 2026-07-17
Released: 07_releases/v1.1-2026-07-17/
- FIX: all 72 reference designators now print on the silkscreen (F.SilkS)
  via a de-collision pass; v1.0 had refdes on F.Fab only (no names on the
  physical board). New audit gate I10 enforces refdes-on-silk.
- Twin: U2 (AMS1117 SOT-223) now mounts via pad_alias {4:2}; prior
  PAD-GEOM/PAD-MISMATCH waivers replaced with a coverage-restoring alias.
- Copper functionally identical to v1.0 (203 vias, 613 vs 612 tracks,
  CPL byte-identical). Supersedes v1.0.


## v1.0 — 2026-07-17  [tag: elt-v1.0]
- Initial design: ESP32-S3-WROOM-1-N8R2, native USB-C, 3 laser / 3
  photodiode (LM339 on 5V) / 3 button channels, OLED header, 92x62mm
  2-layer, all-0805 Basic passives, 5 unique Extended parts.
Released: 07_releases/v1.0-2026-07-17
