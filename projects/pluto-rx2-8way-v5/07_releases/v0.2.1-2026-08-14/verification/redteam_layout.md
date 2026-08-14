review_kind: redteam_layout
subject: pluto-rx2-8way-v5 v0.2.1 exact-board layout review
date: 2026-08-14
reviewer: Codex adversarial layout, RF-return and manufacturability lens
independence: fresh exact-artifact pass
evidence_scope: staged hardware release v0.2.1-2026-08-14 only
source_commit: 57687a87c09dd1aac6cec52fb68c34286b0dab36
release: projects/pluto-rx2-8way-v5/07_releases/v0.2.1-2026-08-14
board_sha256: e2d1deaf4052b18b84df02d1b5cab48e131c6debbd70a03678c3ed918b24c2d5
design_verdict: SOUND
production_verdict: HOLD
order_verdict: DO-NOT-ORDER
p0_design_findings: 0
p1_design_findings: 0
p2_design_findings: 0

# Exact-board adversarial layout review

The exact 90 x 65 mm four-layer board contains 244 straight track segments,
14 native arcs, 624 vias and four filled zones. KiCad reports 0 violations,
0 unconnected items and 0 schematic-parity findings. All nine RF nets are
branch-free 0.295-mm F.Cu paths with zero RF vias over continuous In1.Cu.
Seven paths use tangent arcs; two direct paths remain straight. The minimum
bend radius is 3.350 routed widths against the blocking 3.0-width floor.

The realized RF gate grades 9/9 paths and all 18 fence flanks; worst aperture
is 1.3979 mm against 1.4000 mm. Via-process grading covers nine selectively
filled/capped 0.45/0.25-mm U1 vias and 615 ordinary 0.45/0.20-mm vias with no
partial family. J12 is confined to the south service area on `VBUS_RAW`/GND.
P-MODEL-REG independently grades 9/9 SMA placements and 45/45 attachment
centres; the supplier WRL is excluded from physical evidence.

P0/P1/P2 findings are 0/0/0. The exact layout is **SOUND** for uploader
validation and a controlled first article. JLC stackup/impedance, via process,
through-hole service, resolved placements and physical VNA results remain
mandatory before ordering.
