# Schematic-stage journal

## 2026-08-13 11:20 — start
- did: bound the generic rebuild driver to `pluto_rx2_8way_v5`, authored the independent 33-refdes manifest and four-page TSX source from the v5 dossiers/rules, and added a commission-stage route/timeout contract without a floorplan or copper claim.
- result: source-only preflight passed 12/12 part dossiers, 19 label-map rows, 30/30 electrical-invariant schemas, 8/8 timing states and all six net classes before tscircuit was invoked.
- next: run the canonical producer under the declared 180-second hard timeout and stop at the schematic-review gate.

## 2026-08-13 11:28 — iterate 1
- did: ran the full driver for the first time.
- result: it stopped in 0.74 seconds before tscircuit because `flow.owner.files` named a future `03_src/floorplan.yaml` that intentionally did not exist.
- next: make ownership reflect current-stage sources only; add the floorplan when PCB mechanics are commissioned.

## 2026-08-13 11:31 — iterate 2
- did: reran the full driver after limiting route ownership to the existing execution contract.
- result: every source gate passed; tscircuit then failed loudly after 5.257 seconds because its parser rejects a net token beginning with a digit (`3V3`). No stale artifact passed freshness verification.
- next: use the established `N3V3` producer transport token and let the shared converter restore canonical `3V3`, then require the downstream label-survival gate to prove the round trip.

## 2026-08-13 11:39 — iterate 3
- did: reduced explicit schematic coordinates until tscircuit emitted zero outside-sheet warnings and corrected invalid `+/-` characters in four USB pin labels, then ran the full pipeline.
- result: tscircuit completed in 3.345 seconds; the renderer produced four pages/33 components; freshness passed 9/9; manifest/Circuit JSON/KiCad/netlist agreed 33/33; label survival passed 129/129 pins; electrical invariants passed 30/30; ERC reported zero errors; and the checkpoint pinned seven files. The driver then stopped exactly at the missing two-review gate.
- next: inspect every exact PDF page and reconstruct the exported netlist against manufacturer pin tables before writing either review verdict.

## 2026-08-13 11:46 — iterate 4
- did: visually inspected all four rendered pages and compared U2/U1/J1/U3/U4/J2-J10 pin functions with the v5 dossiers and local manufacturer PDFs.
- result: rejected the first otherwise-green checkpoint because several unused U2 human pin-function labels disagreed with ST DS13866. Used-pin nets were correct, so the 129 pin assertions and ERC had not exposed the documentation defect.
- next: correct the visible functions, regenerate from source and inspect the replacement PDF rather than editing or accepting the generated schematic.

## 2026-08-13 11:55 — finish
- did: regenerated the complete checkpoint after correcting U2, visually inspected every replacement page at 180 dpi and page 4 again at 200 dpi, traced all 150 exported physical pins, and wrote hash-bound topology/readability reviews.
- result: final tscircuit build took 3.314 seconds; all prior electrical/count/freshness/ERC gates remained green; checkpoint verification passed 7/7; and the canonical pre-route review gate passed 2/2 against the exact normalized netlist, dossier set, design rules and PDF.
- next: obtain the separately required independent RF-schematic verdict, refresh project state, then pause before any floorplan/PCB generation.

## 2026-08-13 12:07 — independent closeout
- did: obtained a fresh-context RF review against only the v5 project, then ran the exact-artifact RF contract gate.
- result: the reviewer found no RF schematic defect and passed 4/4 requirements.  The gate first rejected a hyphenated project-slug artifact path because the canonical board stem uses underscores; all schematic, PCB and fab RF artifact contracts were aligned to the actual generator naming convention, after which the gate passed 4/4.
- next: stop at the reviewed-schematic boundary.  PCB work starts only after the D9 SMA mechanics and drawing-lifecycle obligations are resolved and the official JLC impedance geometry is recorded.
