# Render review — esp32-laser-timing v1.4 (schematic-only change)

v1.4 changes ONLY pdf/schematic.pdf (regenerated). Board/gerbers/BOM/CPL/
layer+assembly PDFs are byte-identical to v1.3 (hashes verify).

Occlusion review against canon S-OCCL/S6/S7 (this release fixes the
findings of the 2026-07-17 schematic review):
- 79 dashed pseudo-wires REMOVED (decorative connectivity that crossed
  section boxes and symbols).
- Section boxes now separated (midline clip): no border strikes through
  neighboring content.
- Text occlusions: S-OCCL 28 -> 0 (machine-counted; refs corner-right-
  justified, small-part values left-justified from body edge, two
  placement nudges C12/TP row).
- Title block now reads Rev v1.4 (was stuck at v1.0 since the first
  release; generated from the release tag / ELT_REV).
- S6 readability grade: EFFORTFUL (honest) — connectivity is still
  global-label-based with zero drawn wires; a wire-stub attempt was
  reverted after it T-junction-merged power rails (documented in the
  generator). Wired story-critical paths remain the Phase-2 schwriter
  capability. S7 decoupling adjacency: caps grouped at their ICs, PASS.
- ERC 0 total, netlist parity 0 (netlist untouched — label connectivity
  identical; verified before/after).
