# Release design math

subject PCB SHA-256:
`02956a64f67e0ef620fb060833dbc1d877e4b02bd7c79ede7cb901c6bf083719`

## Power envelope

The dedicated input requests 15 V / 3 A, giving 45 W at the connector. Four
downstream ports at 5 V / 1.5 A would demand 30 W; control/hub losses and buck
loss remain inside the 45 W source envelope. This is a source envelope, not a
claim that each port may exceed its programmed current limit simultaneously.
The first article must measure the actual 5 V trunk at aggregate load.

The three declared high-current layer-transfer banks contain eight credited
0.20 mm finished barrels each. The governed conservative credit is 0.55 A per
barrel, hence `8 * 0.55 A = 4.4 A` per bank, above the 3 A continuous design
current. All credited barrels electrically participate on both named layers.

## USB geometry

The modeled four-layer starting geometry is 0.2332 mm trace / 0.15 mm gap with
0.30 mm corridor clearance. Length audit results are 0.4706 mm upstream,
0.0030 mm management, and 0.3054/0.2139/0.4983/0.7510 mm for ports 1–4,
respectively; all are below their declared 0.5 or 1.0 mm ceilings. These local
numbers do not replace JLC's final 90-ohm field solve for the selected stackup.

## Process envelope

The exact board has 486 vias at 0.46/0.20 mm and 28 vias at 0.70/0.35 mm. The
complete smaller family is filled and capped; the ordinary family is open.
Partial-family processing is forbidden. DRC, connectivity and schematic parity
are all zero findings on the exact subject.
