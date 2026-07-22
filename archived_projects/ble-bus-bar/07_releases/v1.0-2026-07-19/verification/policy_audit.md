ble-bus-bar: HUMAN=6, N-A=4, PASS=14, WAIVED=2
licy_audit.py; canon: design-policies.md

| ID | Grade | Detail |
|---|---|---|
| S-ERC | PASS | 0 errors (0 warnings) |
| S-NC | PASS | all floats no_connect-flagged |
| S-NET | PASS | 53 routed nets, all named |
| S-VER | PASS | 8/8 verified: cite figure/page |
| S-OCCL | PASS | 0 text occlusions (<= 0) |
| S5 | HUMAN | design-math spot-check per review protocol |
| S6 | HUMAN | schematic readability graded in render review |
| S7 | HUMAN | decoupling-adjacency graded in render review |
| P-CRT | PASS | 0 courtyard findings |
| R-DRC | PASS | 0/0/0 at severity-all |
| P-POL | PASS | polarity machine-check present (pad-1 nets vs part facts) |
| P-KEEP | PASS | mate/keepout checks present in project audit |
| P-SILK-REF | PASS | all refdes on visible silk |
| P-SILK-FN | PASS | every connector/fuse/TP has functional silk nearby |
| P-PLANE | N-A | 2-layer: see R-PLANE regions |
| R-PLANE | WAIVED | U7@B.Cu: 63.5mm signal in plane (max 35) — waived: Flagged 41.2 mm signal run lies under the module BODY, south of the antenna. The antenna r... |
| R-POUR | WAIVED | high-current-class nets with no pour: ['SW', 'VIN_E', 'VLDO', 'VTAP', 'VUSB'] — waived: EPWR-class nets are track-carried BY DESIGN: worst-case branch current is the buck's 0.49 ... |
| R-THERM | N-A | 2-layer: no internal plane to sink into |
| R-RULES | PASS | r0.kicad_pro: classes=['Default', 'TRUNK', 'PORT', 'EPWR', 'RAIL3V3'] |
| R4 | HUMAN | escape feasibility at fab rules — design review |
| R-LEN | N-A | no timing-critical nets declared |
| M-REPRO | PASS | all rebuild inputs git-tracked |
| M-REL | N-A | no releases yet |
| M-WAIV | PASS | 15 adjudications, all evidenced |
| M1 | HUMAN | independent-reference coverage — release review |
| M6 | HUMAN | authoritative-source discipline — encoded in protocols |

Summary: HUMAN=6, N-A=4, PASS=14, WAIVED=2


## HUMAN-graded items — reviewer verdicts (2026-07-19)

| Item | Verdict | Evidence |
|---|---|---|
| S5 design math | PASS | delta pin review re-derived the U7 EP grid + U11 package dims from datasheets and matched; DETAIL_DESIGN values spot-checked in reviews (INA LSB, buck divider) |
| S6 schematic readability | PASS | render review: "single readable page, tiled story ... no overlapping wire/label text"; note: title-block comment slightly overruns border (cosmetic) |
| S7 decoupling adjacency | PASS | audit IP gates (CB-U 5mm x6, C8-module, C9-flash pin8 3.7mm, C4-U8, C1-U8, C12-U9); C7 re-tasked as rail bulk near the buck (audit note) |
| M1 verification independence | PASS | pin reviews + render review by fresh-context agents; twin vs JLC CAD; DRC vs generators |
