subject: programmable-usb2-hub pre-route board c4b42a9f
date: 2026-08-01
reviewer: independent-agent (GPT-5, placement/layout lens)
context-given: full-tree
design_verdict: DEFECTIVE
order_verdict: DO-NOT-ORDER
review_stage: pre-route
review_kind: layout
source_commit: e822cf5a23d42b66bd41bae380237f1e121e8448
board_sha256: c4b42a9fe8c78850c720bdd5e9b036805dfe9cf634ab706654004491da97918a
design_rules_sha256: 72399b539bd768d1ca45d22fa0402573c75665e57052ab0559de70465a8accb7

# Independent pre-route placement/layout review

The exact board is track-free (212 total footprints including board-only
features, 205 assembled envelopes, zero tracks/vias, three zones). The review
measured the saved board with pcbnew and inspected orthographic and isometric
KiCad renders.

## Findings

| id | severity | finding | evidence | required disposition |
|---|---|---|---|---|
| PRLAY-P0-01 | P0 | C23 and R41 have zero courtyard clearance. | `placement_gates.py`: `C23<->R41 courtyard gap 0.000 mm (< 0.100 mm)`; C23 courtyard is x=80.31..82.69, y=75.16..79.84 mm and R41 is x=80.47..83.53, y=73.72..75.28 mm. | Move one part in authored placement, regenerate, and repeat this exact-hash review. |
| PRLAY-P2-01 | P2 | Several reference labels are displaced toward adjacent parts, reducing debug readability. | Generator reports 21/205 degraded ownership placements; prominent examples include U2, U3, U10, U11, L1 and C24. All 205 refs remain present on F.SilkS. | Improve the worst labels before release if routing does not create better legal slots; confirm on the final assembly render. |

## Passing measurements

- P-PADSEP passed over 796 copper pads on 212 footprints, 309,355
  inter-footprint pad pairs and 521,730 paste-to-foreign-copper pairs; no
  separate-footprint land overlap or foreign-pad paste intrusion was found.
- Tightest pad-to-outline margin is 0.41 mm at J6.1 versus the 0.15 mm floor.
- Worst corridor demand is 44 nets across 274 track slots at x=80.5 mm,
  ratio 0.16 versus the 0.50 failure threshold.
- R38-R41 are restored as a four-part row between U7/U8 and the logic-power
  region. R111/R211 sit in symmetric A/B feedback legs. The AP63203 support
  capacitors C23/C24 are no longer placed on any module land; the remaining
  C23-to-R41 collision above is nevertheless a real assembly-envelope defect.
- The four USB-A launch cells are regular and symmetric from J3-J6 through
  ESD/switch cells toward U6. U6/Y1 and U7/U8 remain in the quiet central
  region, separated from the two LM5116 switching cells. The A/B buck cells
  preserve matching controller/FET/inductor/current-sense orientation and
  pass all 29 declared adjacency checks on this geometry except for the
  separate P0 collision gate above.

## Verdict

`design_verdict: DEFECTIVE`. PRLAY-P0-01 is a physical zero-clearance defect
and blocks routing even though copper-pad separation and pin identity pass.
