subject: pi-usb-port-switch exact pre-route placed board
date: 2026-08-15
reviewer: Codex native 3D/mechanical render review
review_stage: pre-route
review_kind: render
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
board_sha256: 168838f8e57b16581a8f54cdd4b75a85d1d5dbb1698428d281a7c07dccf14101
design_rules_sha256: 8bd0fe7492a4ae67bf266d9840e25c14eee8f1bda228593f36cebd87fcf97b71
top_render_sha256: 897d2f1480566525b30bfda159ebaef8329de6db8e6d898c7ac689947c2274e8
iso_render_sha256: 8c736fcdacac67a3aabdc851448ea0d0daf5661ca7cf7bd3dd09b03e4fa95d3a
bottom_render_sha256: 0141fe161a9ee760ffd578ca509b970d71ae578d9d47ca5b428ccb3c9450b062
render_resolution_px: 3784x3024
model_coverage_sha256: dadcfb7128349912e1831cf6f4af02b76bbc138055ca310aa29231871e60340b

# Pre-route native 3D and mechanical review

## Verdict

The complete 3784 x 3024 top, isometric, and bottom views were inspected at
original resolution. No P0 or P1 wrong-board, missing-fitted-body,
body-to-hole registration, connector-orientation, access, gross collision,
or clipping defect was found. The placement is **SOUND to proceed to routing**
under this native-geometry lens.

The first render attempt omitted KiCad-library bodies because the CLI shell did
not export `KICAD10_3DMODEL_DIR`; it was rejected and receives no review credit.
The hash-bound images above were regenerated with
`/home/mouse9911/.local/share/kicad/10.0/3dmodels`, and all 190/190 fitted
electrical footprints independently resolve their declared model files.

## Complete-board observations

- All four Type-B bodies are registered to their through-hole shell stakes and
  fine-pitch contact lands, face west, and present unobstructed upstream cable
  mouths. All four Type-A bodies register to their shell holes and signal lands,
  face east, and present unobstructed downstream mating mouths.
- J1's two terminal screws align with its two plated holes. The mini-blade fuse
  holder aligns with all four holder lands and remains removable from above.
  Q1, C1/C2, the 3V3 regulator, and the 40-pin Raspberry Pi header are present,
  correctly seated over their land patterns, and not clipped by the board edge.
- The four TUSB522 bodies, four TS3USB221E bodies, eight ESD arrays, four
  TPS2557 bodies, logic/MOSFET packages, passives, and four output bulk
  capacitors are visibly present in the expected repeated channel cells.
- Four M3 mounting holes and three non-collinear top fiducials are visible and
  unobstructed. The bottom view shows the expected through-hole fields and no
  unintended bottom-side component population.
- No visible component body overlaps another body, mounting hole, connector
  approach, fuse-removal path, terminal approach, or board edge. Functional
  legends identify the separate 5 V input, Raspberry Pi GPIO interface,
  fused input, every individual downstream USB output, upstream Type-B side,
  downstream Type-A side, and board identity. The orthographic camera and the
  isometric camera were widened so all eight connector bodies and the complete
  board outline remain inside the review frame.

## Evidence boundary

These are KiCad native-model renders of the placed, unrouted board. They prove
that the exact board and declared model transforms form a coherent assembly
preview. They do **not** prove JLC catalog-body identity, LCSC substitutions,
body height from production data, pick-and-place rotation, polarity in the JLC
uploader, routed copper, or manufacturability. Same-camera catalog-twin,
Gerber, BOM/CPL, rotation, THT/manual-assembly, and order-preview checks remain
mandatory before release. Consequently `order_verdict` is `DO-NOT-ORDER`.
