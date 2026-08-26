review_kind: render_review
subject: pi-usb-port-switch v0.1.0 exact-board render and assembly review
date: 2026-08-15
reviewer: Codex fresh visual, 3D, mechanical and assembly lens
evidence_scope: exact pre-seal staged hardware archive
board_sha256: d4bc778c1c80453ec7b198e1bf428b22cb03d414c4a0d86c89ab74d6facc4094
design_verdict: SOUND
production_verdict: HOLD
order_verdict: DO-NOT-ORDER
p0_design_findings: 0
p1_design_findings: 0
p2_design_findings: 0

# Exact-artifact render review

I inspected the exact top, bottom and isometric native renders, six populated
twin views, same-camera bare views, PCB/assembly PDFs and the 3200-pixel strict
registration overlay. The top render SHA-256 is
`c31de5b48163588770e53f810fe4330c21f89e66171d58acfba2e88dff61d9ab`;
the isometric is
`60c998e3f02909571a2b2f6b3be81a596ce5a6173b58868cd4a4a19bab97adda`.

All eight USB receptacles face outward and their shell/mounting lands agree
with the body location. J1 screw access, F1 fuse access, J2 ribbon approach and
all six mounting holes are clear. Fine-pitch bodies sit over their lands,
electrolytic polarity marks agree with silk, and no visible body collision,
blocked mating interface or misleading connector label was found.

All 190 fitted board footprints resolve 3D models and the component-bearing
STEP was regenerated with those assignments available. JLC twin population is
185/185 because the five declared hand-assembled references are outside the
CPL. The strict pixel gate measures 27/27 resolvable bodies within 1.00 mm;
159 smaller bodies are explicitly below the measurement resolution, not
silently passed. P0/P1/P2 findings are 0/0/0.
