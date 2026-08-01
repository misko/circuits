subject: pluto-rx2-8way-v4 v1.1 exact release render review
date: 2026-08-01
reviewer: redteam-agent (GPT-5 physical/render lens)
independence: independent-from-design-author
source_commit: bc1fb1003cd9b7f06c70b15d973c5c018d0ff458
board_sha256: 72875d5ea92a52baa9962be3a69f4e69c1fb1ec3b9faf5ba4412934c18296bf7
design_verdict: SOUND

# Fresh exact-artifact render review

The reviewer inspected the v1.1 release-local bare top/bottom fabrication
views, modeled top/bottom/edge/isometric views, assembly drawing, layer PDF,
and independently measured twin overlay. The pictures are current renderings
of the board hash above, not inherited v1.0 images.

- All 27 CPL placements have bodies in the digital twin. The pixel-based
  independent overlay measures all 11 resolvable bodies, with centre error at
  most 0.079 mm and outward excursion at most 0.034 mm versus the 1.00 mm
  limit. The remaining 16 small bodies are individually named as below the
  image-resolution floor, never silently counted as passes.
- `R_S1`..`R_S4` and `R_LED` are visibly separated from the RP2040-Zero
  castellated lands. Direct geometry gives 0.220 mm copper gap and 0.730 mm
  courtyard gap; neither body nor stencil aperture overlaps the module lands.
- The exact assembly PDF has 3/3 nonblank pages, all 32 board references once
  on the overview, no reference overlaps, and complete detail censuses.
- Connector, switch, module, LED, and passive orientations agree across the
  board, CPL, assembly view, and twin. The two-pad LED numbering ambiguity is
  explicitly resolved by the independent pin review and retained as an upload
  preview check.
- No missing model, impossible placement, reversed package, unreadable
  reference, board-edge collision, or misleading modeled-vs-fabricated
  geometry was found.

Uploader preview remains an execution-time corroboration and first-article
inspection remains production/service acceptance. Neither is a render defect.

