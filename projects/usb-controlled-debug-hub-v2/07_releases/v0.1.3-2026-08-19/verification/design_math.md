# Release design math — v0.1.3

subject PCB SHA-256:
`b1c042c695af896b18627c596406157bc5522561c31ac60cc353b11ff065d197`

## Power envelope and current coordination

The hardware PD sink requests 15 V / 3 A, so the connector-side source
envelope is 45 W. The TPS56637 is rated for 6 A output. The aggregate
TPS259804O is programmed by 300 ohm, 1%, 100-ppm/C `R_AGG_ILIM`; charging
TI's characterized 300-ohm row for resistor tolerance and a 100 C excursion
gives a 4.2745–5.7755 A threshold. It is a coordinated latch-off breaker, not
a promise of 5.78 A continuous board loading.

Each external TPS259470A uses TI's characterized 3.32-kohm programmer row.
The full charged local limit is recorded by the power contract and remains
below the aggregate breaker's minimum for a single channel. The declared
normal composite load remains 2.58 A; the design targets debug peripherals,
not four simultaneous 1.5-A charging loads.

Using the TPS56637 full-corner feedback floor, TPS259804 maximum 5-mohm RON,
and bounded common-copper loss gives a charged protected-rail floor of
4.862803 V. The contract rounds down to 4.860 V and reserves 100 mV of
dynamic margin; hot four-wire measurement remains mandatory.

## Startup, fault timing, and PD input protection

The aggregate 6.8-nF C0G ITIMER capacitor, charged with TI's comparator and
current extrema, gives a 1.61–6.65 ms fault interval. The 3.3-nF dV/dt
capacitor gives about 1.394 V/ms nominal slew and approximately 0.351 A into
the declared 251.86-uF maximum effective downstream bank.

Only the small attach capacitance is directly exposed at `VBUS_PD`; buck input
bulk is behind `U_PD_IN`. The 3-A/32-V fuse precedes TVS1800DRVR. TI specifies
the selected 18-V TVS at 24.7 V maximum clamp for the cited 125 C, 35-A,
8/20-us condition, below the 28-V absolute maximum of U_PD_IN. This is a
coordination bound, not surge-compliance certification, so first article must
capture the eFuse-side waveform.

## Reverse-current blocking

`U_PD_IN` and `U_PWR1..4` are exact TPS259470A variants with true
reverse-current blocking. The schematic and identity prove capability, not
assembled leakage. First article must measure reverse current and upstream
rail rise for each port while unpowered, powered-disabled, and powered.

## USB routing and fabrication

All ten contracted differential pairs connect. Six length groups grade all
12 member paths within their declared limits. The modeled geometry is
0.2332-mm trace / 0.15-mm gap on the authored four-layer starting stack; it is
not a field solve. JLC must confirm the selected construction and final
90-ohm differential solution before payment.

The exact board has 498 selectively filled/capped 0.46/0.20-mm vias and 11
ordinary 0.70/0.35-mm vias. At nominal 1.6-mm thickness their conservative
aspect ratios are 8.0:1 and 4.57:1, within the declared 10:1 advanced-tier
bound. The process selector must apply Type VII fill/cap only to the complete
0.20-mm drill family.
