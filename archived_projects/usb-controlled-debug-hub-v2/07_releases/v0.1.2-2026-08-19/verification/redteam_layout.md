# Adversarial layout/fabrication review — v0.1.2 representation fix-pass

subject: usb-controlled-debug-hub-v2
board_sha256: a0acddd9b0b4e1888583ffacad43f2c2446e76cb040ebc64844cd25779a73987
gerber_zip_sha256: ab8e020c8b7b663dff3296387828750a758d25f27a53b5244971847ff61243ca
bom_sha256: 260ef36687b42b8a9d7443773bee69e96c1f274479a6c1163dd0ae6c5acb6c90
cpl_sha256: 98b481fbb59262d74212f4df9cab83f23ca6a3a0be93b75006f519c5a0548294
design_verdict: SOUND
order_verdict: BLOCKED-SOURCING
design P0/P1/P2: 0 / 0 / 2

The exact PCB, Gerber ZIP, BOM and CPL hashes above are unchanged from v0.1.1.
The representation-only delta is confined to the twin adjudication contract.
The strict supersede gate rejects any fab/ or 3d/ change and any other source/
change, so a moved footprint, coordinate, rotation, pad or copper artifact
cannot hide inside this release.

Canonical replay regenerates the exact source-owned placement and promoted
route. Atomic acceptance is 9/9: DRC/unconnected/parity 0/0/0, all ten
critical pairs connected, six length groups and twelve member paths passing,
reference-plane obstacle checks passing, via-current declarations passing and
513/513 realized vias inside the declared aspect limit.

The fabrication payload contains four distinct copper layers with saved filled
regions, 54 fully coded BOM rows and 168 CPL placements (159 top, 9 bottom).
The selective process census is exact: 502 protected 0.46/0.20 mm Type-VII
vias and 11 ordinary 0.70/0.35 mm vias. Model coverage and twin population are
168/168; orientation is exact-current PASS.

The prior C165948 catalog model is independently shown to put the mating mouth
2.00 mm behind the authoritative datum. It is not translated into place.
Instead, the exact SHA-bound native model is retained for `J_DATA` and
`J_POWER`; P-MATE-REG is 6/6 PASS and A-RENDER measures the two connector
centres within 0.148 mm. The rejected catalog identity remains auditable.

P2 observations: the reference-plane check is not a field solve, so JLC's
90-ohm differential calculation remains mandatory; and broad current paths
require first-article four-wire voltage-drop/thermal measurements. Neither is
a current saved-board defect.

The package is not order-authorized until JLC's final allocation, BOM echo,
rotation/polarity, six THT mappings, selective-via, stackup and impedance
previews are captured.
