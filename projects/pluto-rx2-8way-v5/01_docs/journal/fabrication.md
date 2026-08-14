# Fabrication-stage journal

## 2026-08-13 21:20 — start
- did: entered fabrication from the exact layout seal and ran the strict JLC
  exporter without rotation or BOM-legibility escape hatches.
- result: export stopped before leaving uploadable BOM/CPL output because 14
  placements across six exact LCSC codes had no independently measured
  rotation-authority row.
- next: measure each missing code from raw project/JLC lands and physical
  marking/body evidence; do not copy a fitted angle from the twin under test.

## 2026-08-13 21:24 — iterate 1
- did: measured C2866134, C2932107, C429844, C5184243, C5452432 and C83270,
  reran the 99-row M-PROV/A-POL table audit, and reran strict export.
- result: rotation table passed 99/99; export produced 11 Gerber layers plus
  PTH/NPTH drills, 13 fully coded BOM rows and 29 top-side CPL placements.
  The generated human preview denominator is U1, U2 and J11; D1 and all nine
  outward SMA directions retain explicit order-preview obligations.
- next: grade the bytes and the complete assembly population, not merely the
  exporter exit code.

## 2026-08-13 21:27 — iterate 2
- did: ran BOM source/legibility, live same-day stock, A-POP/A-POS, selective
  via process, Gerber archive integrity and independent saved-board/payload
  pour checks.
- result: BOM source and legibility pass 13/13; live stock passes 13/13 at the
  five-board quantity; A-POP covers 29/29 placements with worst CPL datum
  error 0.00050 mm; via process grades 638/638; ZIP tests 13/13; F-PAYLOAD
  grades 4/4 pour-bearing copper layers and all four copper files.
- next: replace project bodies with exact JLC catalog bodies and fail closed on
  every catalog/manufacturer land disagreement.

## 2026-08-13 21:31 — iterate 3
- did: ran the final JLC digital twin, measured the reported land conflicts
  directly against the pinned manufacturer documents, wrote narrow
  part/ref/status adjudications, reran the twin, and graded the render pixels
  against the board-implied body positions.
- result: the raw twin correctly stopped on 12 refs. Exact evidence showed
  C429844's five hole centres agree to 0.000 mm despite JLC collapsing four
  grounds to pad 2; Samtec's exact J11 land overrides JLC's generic row span;
  Littelfuse's solder-pad bounds favor the project D_SMB land. The adjudicated
  twin exits 0 with 29/29 bodies mounted and zero unreviewed critical refs.
  A-RENDER grades all 14 resolvable bodies within 1.00 mm and explicitly names
  all 15 sub-resolution/occluded refs.
- next: run an independent exact-Gerber RF review and preserve all uploader
  and physical first-article boundaries rather than treating a local pass as
  an order/performance pass.

## 2026-08-13 21:45 — iterate 4
- did: dispatched a fresh exact-Gerber review bound to commit, board, contract
  and ZIP hashes; time-boxed an exploratory reviewer after repeated quiet
  waits and handed the already measured evidence to a bounded final reviewer.
- result: the first reviewer independently measured 13/13 archive integrity
  and timestamp-normalized re-export identity, DRC 0/0/0, nine 0.295-mm F.Cu
  RF paths with zero RF vias, and the exact drill census. The bounded reviewer
  finalized the canonical record. One schema-only header mismatch
  (`local_fab_package_verdict` versus required `fab_package_verdict`) was
  corrected and the RF contract then passed 4/4.
- next: keep machine identifiers and review-header vocabulary in a generated
  dispatch envelope (IMP-095); do not allow an evidence-complete review tail
  to become a new quiet pipeline lock.

## 2026-08-13 21:51 — finish
- did: generated and visually checked purpose-derived release PDFs and a full
  component-bearing STEP while keeping the canonical board unchanged.
- result: fabrication package verdict is READY for JLC upload review; physical
  RF performance is explicitly NOT_YET_MEASURED. The release assets are a
  seven-page nonblank PCB packet, a three-page top-side assembly packet and a
  5.43-MB STEP using the exact JLC PE42482 STEP in a disposable export copy.
  Board SHA-256 remains `39251c24d4b3cc878824f26c48178cbc4a4d418fa528045c6c13f2308e017acd`.
- next: pause at the stage boundary. Next approved stage is firmware build,
  state-machine/decoder verification and Raspberry Pi SWD programming proof;
  JLC uploader echoes and physical first-article VNA/timing tests remain later
  external gates and have not been claimed.
