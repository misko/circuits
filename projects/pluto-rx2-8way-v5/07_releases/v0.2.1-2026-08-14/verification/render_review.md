review_kind: render_review
subject: pluto-rx2-8way-v5 v0.2.1 exact-board render review
date: 2026-08-14
reviewer: Codex fresh visual, 3D, mechanical and assembly lens
independence: exact current artifacts; catalog-model and physical-model evidence kept separate
evidence_scope: staged hardware release v0.2.1-2026-08-14 only
source_commit: 57687a87c09dd1aac6cec52fb68c34286b0dab36
board_sha256: e2d1deaf4052b18b84df02d1b5cab48e131c6debbd70a03678c3ed918b24c2d5
design_verdict: SOUND
production_verdict: HOLD
order_verdict: DO-NOT-ORDER
p0_design_findings: 0
p1_design_findings: 0
p2_design_findings: 0

# Exact-artifact render and assembly review

I inspected the exact native top render, high-resolution isometric render, all
four schematic pages, PCB layer/assembly plots, the full-board registration
overlay and the single-J2 crop. The final top render SHA-256 is
`a402c62e59730f0983cb3defe1436bf80305b0bf08865de7e826f1e9878061bf`;
the 3200x2400 isometric is
`fa3ea79e2bad1a0def480ddad55697212958165449fe7047cbc8d522493144c3`.

The exact native Amphenol model is independently SHA-bound. P-MODEL-REG grades
9/9 SMA bodies and 45/45 drilled centres. For J2, orange F.CrtYd contains both
green F.Fab and pink measured-model envelopes; all five cyan hole centres are
inside the body. All nine connector barrels face outward and remain accessible.
USB-C, J12 and keyed J11 open outward, the mounting holes remain clear, and no
visible body collision or blocked mating interface exists.

The raw JLC catalog render is retained separately as supplier-CAD evidence. Its
C429844 converted WRL is internally misregistered and is explicitly not used
as physical placement evidence. The earlier twin overlay compared its green
expectation and pink pixels from the same faulty mesh, so that apparent pass is
withdrawn for SMA registration. P0/P1/P2 findings are 0/0/0; the physical
render result is **SOUND**. Live JLC preview checks still block ordering.
