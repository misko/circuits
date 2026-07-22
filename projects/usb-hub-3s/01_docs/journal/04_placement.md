# journal: 04_placement

## 2026-07-21 — start
- did: floorplan v1 (100x80): generated, 21 asserts pass, rendered.
- result: audit FAIL x10 (ESD arrays 15-30mm from ports — USB-A body courtyard
  eats x>100; SW quadrant seeds scattered — VBAT_F/VIN/VOUT_PD patch overlaps).
- next: re-carve.

## 2026-07-21 — iterate 1
- did: board -> 110x82; port electronics column widened (connectors at x=122,
  switches x=100); input chain re-laid (F1 vertical, Q1 (40,80)); PD output
  chain re-laid (RS3 vertical 270, Q8 rot 90 D-north/S-south); zone patches
  re-carved non-overlapping; polymer caps PINNED as anchors after legalizer
  strayed C1/C26 out of their pour patches.
- result: AUDIT PASS (13 polarity, 22 proximity, 4 edge, 116 silk); render
  coherent; J5/J2-4 mouths verified by body_offset asserts (J5 rot 90 not 270).
- next: generate_rules -> KRT route -> stitch -> DRC.

## 2026-07-22 (v1.1) — start (PD cell re-floorplan, X2/X18/X19/X20/X22/X23)
- did: re-derived the PD stage as a reference cell: one FET row [VOUT_PDS|Q6|LX1|Q7|GND..GND|Q5|LX2|Q4|VIN_S] at y=73, L1 (new 18mm YSPI1770Y) directly under it at y=85.6, HF ceramic banks ON both bridge rails (C46-48 VIN_S, C49-51 VOUT_PDS), shunts outside the HF loop with kelvin stubs off pad ends (R14/R15/R18/R19 re-anchored), gate-R slots R28-R31 at the gates, LX zones F.Cu-only ~60mm2 (was 400mm2 x2 layers), 5VA column narrowed to x95-99 to free the east VIN pool, In2 plane connect=full, via_farms.yaml (0.45/0.3 trunk farms + 6-via thermal arrays)
- result: floorplan.yaml + route.yaml + via_farms.yaml + nets.yaml (QG4-7) written; promoted v1.0 chain retired (fresh route required)
- next: generate -> audit -> measure the claimed adjacencies with pcbnew (numbers, not hope)
