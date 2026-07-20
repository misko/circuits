# Generic board generator — validation proof

`skills/kicad-pcb/scripts/generate_board_generic.py` regenerating two REAL
boards from a declarative floorplan YAML, checked against their sealed
`04_kicad` boards. Sealed boards and releases were not modified; output goes
to `06_build/proof/`.

| board | parts | bespoke generator | floorplan.yaml | netlist parity | audit_board |
|---|---|---|---|---|---|
| cook-loadcell  | 33 | 373 lines | 111 (88 non-comment) | **0 — PASS** (77 nodes) | **PASS** (0 failures) |
| crow-array-pod | 40 | 486 lines | 136 (112 non-comment) | **0 — PASS** (90 nodes) | **PASS** (0 fails, 0 warns) |

Reproduce:

    cd projects/cook-loadcell
    /usr/bin/python3 ../../skills/kicad-pcb/scripts/generate_board_generic.py 03_src/floorplan.yaml
    /usr/bin/python3 ../../skills/kicad-pcb/scripts/board_netlist_parity.py \
        06_build/proof/cook_loadcell.kicad_pcb 04_kicad/cook_loadcell.kicad_pcb

`audit_board.py` is path-hardcoded to `04_kicad/`, so it is run against a
scratch tree with the proof board copied into `04_kicad/` (see
`tests/run_tests.sh --slow`, which automates exactly this).

## Features exercised
cook-loadcell: plain rect outline, 4 mounting holes, anchors + seeds +
ring legalizer, attr fixup (`SJ*` clear exclude_from_bom), GND pours both
layers, 10 collision-nudged captions, TP labels derived from part values,
refdes de-collision with a 90-degree fallback, 8 pad-net asserts.

crow-array-pod: R6.25 concave corner-cut outline, project-local `pod`
footprint library, `pin:` glob (anchored-but-floating passives), per-pad
zone-connection override on J1's GND tails, F.Cu-solid/B.Cu-thermal split
pours, polarity `K` marks, 4 pad-net + 3 pad-order orientation asserts.
