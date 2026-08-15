# Parts-stage learnings

## Source and lifecycle checks belong before schematic capture
- what happened: the first plausible exact choices included one regulator with incomplete multi-pool evidence, one P-FET with conflicting lifecycle classifications and one exact resistor with zero distributor stock.
- root cause: an electrically plausible MPN is not yet an orderable design identity.
- avoid next time: run one exact-MPN, fixed-quantity, composed two-pool gate before the part is allowed into TSX; preserve per-pool failures rather than averaging them into a reassuring catalogue result.
- candidate-canon: already required by Q-2SOURCE; this run is completion evidence.

## Close the complete loaded connector path before selecting a USB power switch
- what happened: the initial switch/FET choices looked adequate individually, but fuse, holder, reverse-polarity FET, switch, copper and both mated power contacts consumed the 5.0 V input margin together.
- root cause: component-level resistance checks do not prove voltage at the commissioned measurement plane.
- avoid next time: calculate backward from the mated-load minimum through every series element, including the return contact, before selecting the load switch or accepting the source-voltage envelope.
- candidate-canon: yes; extend D-SPEC/E-PATH commissioning examples for connector-powered fixtures.

## Package escape can decide fabrication tier before the schematic exists
- what happened: the 0.5 mm redriver/ESD packages and 0.4 mm USB 2 switch made the least-cost standard tier conditional or impossible for the requested USB 3 attempt.
- root cause: feature count and footprint pitch, not schematic complexity, set the local escape floor.
- avoid next time: perform exact-package escape grading during the sourcing spike and bind the fabrication tier before capture; treat a USB 2-only fallback as a separate architecture, not a routing-time rescue.
- candidate-canon: already enforced by P-ESC/P-TIER; retain as a USB fixture example.

## Mixed JLC/global BOMs need per-row evidence composition
- what happened: three deliberately uncoded global/user-fit parts initially invalidated valid JLC evidence for 24 unrelated coded rows.
- root cause: the shopping-list composer treated a distributor as an all-or-nothing BOM source instead of one independent pool per exact row.
- avoid next time: retain fresh JLC evidence for every coded row and mark only the uncoded row ineligible for that pool; require it to clear two other pools.
- candidate-canon: implemented as IMP-103 with an end-to-end regression.

## Executable rule classes should be populated with directional nets as soon as pin roles are known
- what happened: prose described USB 2, USB 3 and power classes while `nets.yaml` still contained `classes: {}`; the source audit correctly reported 0/0 coverage.
- root cause: the scaffold separated architecture prose from executable net ownership but did not require them to converge when the part pin maps became fixed.
- avoid next time: at parts-stage finish, inventory every critical series boundary and use directional host/device plus connector/IC suffixes before schematic capture. Do not claim width/gap until the selected stackup is solved.
- candidate-canon: yes; add this checkpoint to the parts-stage finish template.
