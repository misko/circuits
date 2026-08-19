# Release design math — v0.1.1

subject PCB SHA-256:
`a0acddd9b0b4e1888583ffacad43f2c2446e76cb040ebc64844cd25779a73987`

## Power envelope and current coordination

The hardware PD sink requests 15 V / 3 A, so the connector-side source
envelope is 45 W. The TPS56637 is rated for 6 A output, but the retained
aggregate TPS259474L eFuse—not the PD source—is the governing 5 V trunk
protection. With its exact 1 kOhm programmer, the accepted full-corner
threshold is 2.990–3.680 A.

Each external TPS259470A has 5.90 kOhm ±1% on ILM. TI equation 5
`ILIM = KILM / RILM`, including the documented device error and resistor
tolerance, gives 0.503–0.628 A. Four high corners sum to
`4 × 0.628 A = 2.512 A`. The declared continuous composite load is 2.58 A;
the 3.0 A service peak is time-bounded. The design therefore targets standard
USB peripheral power and debug control, not four simultaneous 1.5 A loads.

The protected-rail floor calculation uses the TPS56637 feedback corner
5.07363 V, TPS259474L 45 mOhm maximum and an 18 mOhm common-copper budget:
`5.07363 V - 2.58 A × (0.045 + 0.018) ohm = 4.911 V`.
The contract rounds down to 4.90 V and requires hot four-wire confirmation.

## PD attach and input protection

Only 0.1 uF is directly exposed at `VBUS_PD`. The two 10 uF buck input
capacitors are behind `U_PD_IN`. The 470 kOhm / 28.7 kOhm / 35.7 kOhm
divider gives accepted full-corner rising windows of 9.6457–10.3289 V UVLO
and 17.3813–18.6525 V OVLO. A 3.3 nF DVDT capacitor controls inrush.

The 3 A / 32 V fuse precedes the controller and gate. The 16 V TVS has a
26 V maximum clamp below the 32 V regulator absolute maximum. These ratings
are coordination bounds, not surge-compliance certification.

## Reverse-current blocking

`U_PD_IN` and `U_PWR1..4` are exact TPS259470A variants with true
reverse-current blocking. The schematic and part identity prove capability;
they do not prove assembled-board leakage. The first article must measure
upstream-rail rise and reverse current for each port while the board is
unpowered, powered, and the selected port is disabled.

## USB routing and fabrication

All ten contracted differential pairs connect, and six length groups measure
12/12 member paths. Pair spreads are 0.4706 mm upstream, 0.0030 mm management,
and 0.3054/0.2139/0.4983/0.7510 mm for ports 1–4, within their respective
0.5 or 1.0 mm limits.

The modeled geometry is 0.2332 mm trace / 0.15 mm gap on the authored
four-layer starting stack. This is not a field solve. JLC must confirm the
selected stack and 90-ohm differential geometry before payment.

The exact board has 502 selectively filled/capped 0.46/0.20 mm vias and
11 ordinary 0.70/0.35 mm vias. At 1.6 mm thickness their conservative aspect
ratios are 8.0:1 and 4.57:1, both within the declared 10:1 advanced-tier bound.
