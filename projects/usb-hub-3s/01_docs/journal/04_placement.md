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
