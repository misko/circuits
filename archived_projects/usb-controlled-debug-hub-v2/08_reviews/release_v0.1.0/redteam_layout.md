# Exact-board layout/fabrication red-team — 2026-08-18

subject: usb-controlled-debug-hub-v2
board_sha256: 02956a64f67e0ef620fb060833dbc1d877e4b02bd7c79ede7cb901c6bf083719
design_verdict: SOUND
order_verdict: BLOCKED-SOURCING
- design P0/P1/P2: **0 / 0 / 1**

Fresh exact-board checks pass: native DRC/unconnected/parity 0/0/0, route
acceptance 9/9, all ten critical USB pairs connected, six length groups and
twelve member paths passing, reference-plane obstacle checks passing, and
162/162 fitted bodies resolvable. The JLC twin mounts 162/162 placements.
Connector orientation is machine PASS 6/6 and human-approved 6/6.

The fabrication payload contains four distinct copper layers with filled
regions, a 49-row fully coded BOM, and a 162-row CPL split 153 top / 9 bottom.
The 486-via 0.46/0.20 mm family is consistently protected; the 28-via
0.70/0.35 mm family is consistently ordinary.

P2 observation: the reference-plane check proves projected obstacle clearance,
not impedance. JLC must confirm the final stackup and 90-ohm differential solve;
the first article must prove USB High-Speed operation and full-load thermal/drop
behavior.

Payment remains blocked until the final JLC rotation/polarity, six-connector
THT, via-process, stackup, impedance, resolved-BOM and allocation previews are
captured and accepted.
