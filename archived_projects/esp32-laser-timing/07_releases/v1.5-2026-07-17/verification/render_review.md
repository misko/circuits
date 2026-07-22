# Render review — esp32-laser-timing v1.5 (schematic-only change)

v1.5 changes ONLY pdf/schematic.pdf. Fab files byte-identical to
v1.1-v1.4 (hashes verify).

- CHAIN-COLLAPSE WIRING (first real wires in the fleet): 8 facing
  same-net pin pairs in the divider/hysteresis/pullup and gate chains now
  join with drawn wires; the facing-plate double-prints (VTH/GND/COMP
  glyph soup found by the 2026-07-17 occlusion review) are gone — one
  legible plate per junction, sitting on its wire.
- S-OCCL 24 -> 0 measured with the LABEL-AWARE checker (the v1.4 claim
  used a label-blind checker; see 01_docs/ERRATA.md — resolved by this
  release). 13 machine-computed pitch nudges applied (reporter prints
  exact minimum shifts; no hand-eyeballing).
- Wire-island lesson encoded in the generator: each wire keeps one global
  label (the net glue) — suppressing both sides orphaned 8 islands (16
  parity conflicts) on the first attempt.
- Gates: ERC 0 total, netlist parity 0, policy audit zero FAIL.
- S6 readability: chains now READABLE (drawn); overall sheet still
  label-based for rails/fan-out — EFFORTFUL->IMPROVING; full story-path
  wiring remains Phase 2.
