review_kind: pin_review
subject: pi-usb-port-switch v0.1.0 final physical pin and polarity review
date: 2026-08-15
reviewer: Codex fresh-lens package, pin-map and polarity review
evidence_scope: exact pre-seal staged source, 36 generated dossiers and renders
board_sha256: d4bc778c1c80453ec7b198e1bf428b22cb03d414c4a0d86c89ab74d6facc4094
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
p0_design_findings: 0
p1_design_findings: 0
p2_design_findings: 0

# Final physical-pin review

Thirty-six critical dossiers cover all USB connectors, the GPIO header, fuse,
input protection, regulator, four redrivers, four USB 2 switches, four power
switches, ESD arrays and interlock devices. The 34 multi-pin references expose
436 declared physical pin identities. No package winding, manufacturer-fused
land, exposed-pad, USB direction, D+/D-, SuperSpeed P/N, VBUS or GPIO command
identity is unresolved.

J3/J5/J7/J9 preserve the exact Wurth Type-B pin map and remain on the THT CPL.
J4/J6/J8/J10 preserve the exact Wurth Type-A pin map and are deliberately
excluded for hand assembly. J2 maps GPIO17/27, 22/23, 24/25 and 5/6 to the four
power/data command pairs while all Pi power pins remain electrically unused.

The six polarized electrolytics `C1, C2, C21, C37, C53, C69` agree with pad-1
net assertions, silk plus marks and rendered body orientation. J1 input
polarity, Q1 source/drain/gate mapping and U1 output-tab identity agree with
their dossiers. U2/U8/U14/U20 and U3/U9/U15/U21 preserve every P/N member and
direction through the channel. P0/P1/P2 findings are 0/0/0.
