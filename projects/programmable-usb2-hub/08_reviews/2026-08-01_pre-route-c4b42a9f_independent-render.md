subject: programmable-usb2-hub pre-route board c4b42a9f
date: 2026-08-01
reviewer: independent-agent (GPT-5, render-faithfulness lens)
context-given: full-tree
design_verdict: DEFECTIVE
order_verdict: DO-NOT-ORDER
review_stage: pre-route
review_kind: render
source_commit: e822cf5a23d42b66bd41bae380237f1e121e8448
board_sha256: c4b42a9fe8c78850c720bdd5e9b036805dfe9cf634ab706654004491da97918a
design_rules_sha256: 72399b539bd768d1ca45d22fa0402573c75665e57052ab0559de70465a8accb7

# Independent pre-route render-faithfulness review

The exact board was rendered orthographically and isometrically with
`kicad-cli pcb render`. The geometry is legible as a bare placement map, but
it is not a faithful populated-body proof.

## Findings

| id | severity | finding | evidence | required disposition |
|---|---|---|---|---|
| PRREN-P0-01 | P0 | The critical connector bodies are absent, so their overhang, access, orientation, and collision envelope cannot be judged. | Exact board model inventory is zero for J1-J6. J3-J6 have a vendored `USB1130-15-A-envelope.wrl` declared by part metadata, but the board footprints attach no model. The rendered images show only pads/silkscreen for all six connectors. | Generate a populated/bare same-camera twin with faithful J1-J6 bodies, then run A-RENDER and repeat the independent render review. |
| PRREN-P0-02 | P0 | The four port eFuse bodies are absent from the exact render. | U9-U12 each have zero attached models on the reviewed board; their dense port-cell placement is therefore shown as lands only. | Mount the exact JLC/part body in the twin and include all four in the A-RENDER denominator. |
| PRREN-P1-01 | P1 | F1 cannot be visually validated in this environment from the source-board model reference. | F1 names `${KICAD10_3DMODEL_DIR}/Fuse.3dshapes/Fuseholder_Blade_Mini_Keystone_3568.step`, but the variable/library is unavailable here and the body renders absent. | Use a vendored or otherwise resolvable exact Keystone 3568 body in the twin and confirm fuse insertion/tool clearance in edge/iso views. |

## Render observations

- The 2 A port captions, USB host label, SWD label, input polarity, 10 A fuse
  instruction, project identity, and proprietary-power-mode warning are
  visible in the orthographic placement view.
- Pad and silkscreen rendering agrees with the saved board coordinates,
  including the restored R38-R41 row and new R111/R211 series-feedback parts.
  This does not rescue missing-body coverage: a bare-looking render cannot
  prove that a populated board is mechanically sound.

## Verdict

`design_verdict: DEFECTIVE`. No SOUND render verdict is justified until the
critical connector, eFuse, and fuse-holder bodies are present in a same-camera
populated/bare proof and A-RENDER passes.
