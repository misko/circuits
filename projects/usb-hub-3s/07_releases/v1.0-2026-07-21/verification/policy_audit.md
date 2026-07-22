usb-hub-3s: HUMAN=6, N-A=4, PASS=20
ated by policy_audit.py; canon: design-policies.md

| ID | Grade | Detail |
|---|---|---|
| S-ERC | PASS | 0 errors (208 warnings) |
| S-NC | PASS | all floats no_connect-flagged |
| S-NET | PASS | 66 routed nets, all named |
| S-VER | PASS | 11/11 verified: cite figure/page |
| P-ESC | PASS | 26 parts: escape blocks agree with escape_check |
| P-TIER | PASS | all parts escape at declared fab_tier 'jlc_4layer_advanced' |
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
| P-PLANE | PASS | In1 carries only its plane (0 tracks) |
| R-PLANE | N-A | no plane_regions configured |
| R-POUR | PASS | high-current-class nets all poured (13 nets) |
| R-THERM | PASS | all pads >=4.0mm2 have >=2 nearby same-net vias |
| R-RULES | PASS | r0.kicad_pro: classes=['Default', 'SWITCH_NODE', 'PWR_IN', 'PWR_RAIL', 'VBUS', 'GATE', 'SENSE', 'USB_DATA', 'AUX_5V', 'NC_PADS', 'GND_RET'] |
| R4 | HUMAN | escape-first routing order — design review (feasibility itself is machine-checked: P-ESC/P-TIER) |
| R-LEN | N-A | no timing-critical nets declared |
| M-REPRO | PASS | all rebuild inputs git-tracked |
| M-REL | N-A | no releases yet |
| M-JRNL | PASS | 5 stage journals, 5 with entries |
| M-LEARN | N-A | no release yet |
| M-WAIV | PASS | 18 adjudications, all evidenced |
| M1 | HUMAN | independent-reference coverage — release review |
| M6 | HUMAN | authoritative-source discipline — encoded in protocols |

Summary: HUMAN=6, N-A=4, PASS=20
