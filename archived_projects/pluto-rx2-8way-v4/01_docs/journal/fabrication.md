# Fabrication journal

## 2026-07-31 21:45 — start
- did: Exported a four-layer JLC candidate from the layout-sealed board without rotation or BOM escape hatches.
- result: 11 Gerber layers plus drills, 11 BOM rows, and 27 top-side CPL placements generated; U_MCU was dropped from BOM and CPL by assembly.yaml.
- next: Independently grade population, BOM identity/legibility, live stock, and the modeled assembly.

## 2026-07-31 21:51 — finish
- did: Ran A-POP/A-POS, BOM-source, F-LEGIBLE, live JLC stock, and the JLC digital twin; visually inspected top, bottom, and isometric twin renders.
- result: A-POP PASS at 27 placed / 5 declared off with 0.00000 mm worst datum error; BOM source PASS; F-LEGIBLE 11/11; stock PASS 11/11 for five boards; twin bodies 27/27 and every model registration OK. The render leaves U_MCU empty exactly as declared.
- next: Keep the package unsealed and unordered until target hardware, JLC preview/polarity, plug-in assembly acceptance, and physical VNA measurements are complete.

## 2026-07-31 22:00 — iterate 1
- did: Normalized the candidate into canonical `06_build/fab` and `06_build/twin` work areas, reran direct A-POP, BOM-source, F-LEGIBLE, contract, and aggregate policy checks, and preserved the two RP2040-Zero vendor figures as a two-page PDF.
- result: Project contract audit PASS at 93 files / 0 violations; direct candidate A-POP PASS at 27/27 placements and 5/5 declared unpopulated; BOM source PASS with 7/7 R/C rows graded; F-LEGIBLE PASS 11/11. Aggregate policy is 28 PASS / 6 HUMAN / 11 N-A / 1 FAIL, where the sole failure is the expected pre-seal project-root `MANIFEST-UNDECLARED`; the explicit candidate manifest passes.
- next: Do not seal. Obtain the fresh independent pin, topology/protection, layout/thermal, and render reviews, disposition every finding to zero open P0, then run M-REV and seal-time manifest/freshness gates.

## 2026-07-31 22:08 — iterate 2
- did: Rejected the PDF-wrapper normalization because it would preserve rendered pixels but not the vendor's byte-original JPEG evidence, restored both original files, and narrowed the board-local parts contract to permit provenance-pinned vendor JPG/PNG diagrams when no PDF equivalent exists.
- result: The original vendor bytes and their pinned sha256 values remain intact; project contract audit PASS now covers 94 files / 0 violations without disguising an image as a datasheet PDF.
- next: Carry this exception into the shared template only through a separately reviewed process change; this board commit remains v4-only.
