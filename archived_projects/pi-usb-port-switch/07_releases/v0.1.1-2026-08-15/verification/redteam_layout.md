review_kind: redteam_layout
subject: pi-usb-port-switch v0.1.0 exact routed layout
date: 2026-08-15
reviewer: Codex adversarial layout, power and high-speed lens
evidence_scope: exact pre-seal staged hardware archive
board_sha256: d4bc778c1c80453ec7b198e1bf428b22cb03d414c4a0d86c89ab74d6facc4094
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
p0_design_findings: 0
p1_design_findings: 0
p2_design_findings: 0

# Adversarial routed-layout review

The 150 x 120 mm board preserves four readable west-to-east channels with
outward-facing upstream Type-B and downstream Type-A connectors. J1, the fuse,
GPIO header and all cable approaches remain accessible. Six mounting holes and
connector shell stakes are unobstructed. Final DRC is 0/0/0.

All 56 declared USB differential segments are connected and retain their
contracted layer/via policy. The predominant outer-layer geometry is 0.25 mm
width / 0.18 mm gap over an adjacent ground reference; explicit paired
transitions retain nearby ground return vias. The design does not claim that
geometry alone proves 90 ohms. A named JLC four-layer stackup and calculator/
process echo remain a payment stop, and USB 3 remains a first-article target.

The 4.05 A protected trunk uses broad copper and an eight-via transfer credited
at 6.72 A under the independent 10 C-rise screen. All nine declared vertical
power transfers pass. Every 0.9 A output transfer has at least 1.10 A credited
capacity. Five high-current nets are poured; large thermal lands retain local
same-net via support. Exactly 61 via-in-pad barrels are filled/capped and the
remaining 688 ordinary barrels are process-disjoint.

Model coverage is 190/190. The JLC twin mounts 185/185 CPL bodies. The strict
shadow-free registration gate measures every resolvable expected body: 27/27
are within 1.00 mm, with zero resolvable-but-unmeasured and zero missing-model
findings. No unresolved design finding remains under this lens.
