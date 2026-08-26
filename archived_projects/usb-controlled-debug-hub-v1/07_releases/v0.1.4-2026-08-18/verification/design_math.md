# Release design arithmetic — USB-controlled debug hub v0.1.2

Exact PCB SHA-256:
`c5cd719571e216224c83aca142ac84e1f11facdfb48b1bcb771c9d5b97c06e68`.

This file records the equations behind the machine-checked envelopes. Physical
contact/copper loss, transient response, temperature and USB SI remain
first-article measurements; calculated values are not substituted for them.

## Shared 5 V delivery

The commissioned source is 5.20–5.25 V at `P5V_RAW`, rated for 3 A continuous
and separately qualified for 5 A / 6 ms. Normal worst-case board demand is
2.58 A. At the 5.20 V source floor:

```text
fuse allowance                                     121.000 mV
(45 mΩ eFuse max + 18 mΩ holder/common budget) × 2.58 A
                                                   162.540 mV
nominal shared drop                                283.540 mV
shared drop with independent 5% charge             297.717 mV
derived P5V_PROTECTED floor       5.200 - 0.297717 = 4.902283 V
declared conservative floor                         4.890000 V
reserve                                              12.283 mV
```

The 121 mV fuse term is the published rated-current drop used as an engineering
bound, not a guaranteed production maximum. The 18 mΩ holder/common-copper
allocation must be confirmed hot by four-wire first-article measurement.

Each external 500 mA branch budgets 35 mΩ switch maximum + 25 mΩ PCB/via/
joint + 100 mΩ mated contacts = 160 mΩ, hence 80 mV physical drop. Charging
that by 20% gives 96 mV. The 4.89 V branch input floor has 140 mV to the USB
4.75 V minimum, leaving 44 mV after the charged branch loss. All four ports
must be measured simultaneously at the mated plugs.

## Aggregate current coordination

Four external TPS2557 channels and the management channel use 165 kΩ 1%
programmers. Their independent reviewed limit window is 0.535–0.794 A. The
charged downstream worst-high sum plus the 3.3 V converter input allowance is:

```text
5 × 0.794 A + 0.480 A = 4.450 A
```

TPS259474L aggregate current uses the TI inverse-resistance relation and an
exact 1 kΩ 0.1%, 25 ppm/°C programmer across a 100 °C excursion:

```text
I_limit_low  = 3000.6 A·Ω / 1003.5 Ω = 2.990135 A
I_limit_high = 3667.4 A·Ω /  996.5 Ω = 3.680281 A
```

For `C_AGG_TIMER=3.3 nF`, 5% tolerance and 0.3% temperature charge:

```text
C_min = 3.3 nF × 0.95 × 0.997 = 3.1256 nF
t_min = C_min × 1.286 V / 2.5 µA = 1.608 ms
C_max = 3.3 nF × 1.05 × 1.003 = 3.4754 nF
t_max = C_max × 1.741 V / 1.2 µA = 5.043 ms
```

The 3.0 A / 1.5 ms admitted service peak has only 0.108 ms clearance from the
fastest timer corner. Simultaneous enable, loaded hot-plug, downstream short,
hub OCS behavior and whole-board latch/reset must therefore be tested at the
worst-low aggregate threshold. This is a first-article hold.

## Hub source capacitance

The USB hub source bank is required to retain at least 120 µF effective:

```text
180 µF polymer × 0.80 tolerance × 0.80 lifecycle = 115.200 µF
22 µF X7R × 0.90 tolerance × 0.80 DC bias × 0.85 temperature
                                                   =  13.464 µF
effective total                                    = 128.664 µF
margin above 120 µF                              =   8.664 µF
```

The bank and the programmed dV/dt ceiling yield a calculated maximum startup
inrush of 0.161160 A. Validate the exact assembled capacitor lots and startup
waveform on the first article.

## USB routing and stackup boundary

The routed geometry is provisional 90 Ω differential CPWG: 0.2332 mm trace,
0.15 mm intra-pair gap and 0.30 mm field clearance on modeled
JLC04161H-7628 (outer copper 35 µm, inner 15.2 µm, 0.2104 mm prepreg,
1.065 mm core). Strict realized-copper audit reaches all 12 members in six
groups; DRC is 0/0/0; projected foreign-copper reference-plane checks pass on
both F.Cu/In1 and B.Cu/In2. None of those proves impedance. JLC's order-time
90 Ω solve/coupon is the final authority; a different solve is a STOP and
requires source/routing revalidation. First articles still require Hi-Speed
enumeration, sustained traffic and eye/compliance testing.
