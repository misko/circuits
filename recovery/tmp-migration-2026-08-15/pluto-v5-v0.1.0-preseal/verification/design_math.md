# Pluto RX2 8-way v5 — hardware calculation basis

Status: hardware design evidence only. Physical RF measurements and autonomous
controller qualification remain open.

## RF geometry and operating boundary

The controlled-impedance geometry is F.Cu over solid In1.Cu ground using the
JLC04161H-7628 1.6 mm four-layer stackup:

```text
trace width       = 0.295 mm
coplanar gap      = 0.200 mm
dielectric height = 0.2104 mm
design Dk         = 4.4
JLC result        = 49.971863887 ohm
```

This closes the CAD/uploader input, not broadband switch performance. The first
article must measure each path from 100 MHz to 5.9 GHz with unused ports
terminated in 50 ohms. The requested use of an AD9363 with an AD9361 profile at
5.8 GHz is explicitly experimental and outside the AD9363 published range.

Acceptance limits are:

| Measurement | Limit |
|---|---:|
| Selected-path insertion loss, through 1 GHz | <= 2.0 dB |
| Selected-path insertion loss, at 5.9 GHz | <= 3.5 dB |
| Path-to-path insertion-loss spread | <= 1.5 dB |
| Common-to-off isolation, through 4 GHz | >= 30 dB |
| Common-to-off isolation, at 5.9 GHz | >= 25 dB |
| Active-port input/output return loss | >= 10 dB |

The operating input ceiling is 0 dBm. The switch's +2.5 dBm absolute maximum
is retained only as a damage boundary.

## Power rail

USB-C is power-only and the declared input range is 4.75 to 5.5 V. The 3.3 V
rail load contract is 20 mA maximum. At the minimum input:

```text
available LDO headroom = 4.75 V - 3.3 V = 1.45 V
required dropout       = 0.250 V
headroom margin        = 1.200 V
```

The independently recorded worst-corner headroom is 1.409 V. At maximum input
and load, the conservative LDO dissipation is:

```text
P = (5.5 V - 3.3 V) * 0.020 A + 0.000825 W = 44.825 mW
```

This is below the 238 mW design ceiling and corresponds to an estimated 7.6 C
rise under the adopted thermal model. Physical temperature still must be
measured. Each effective output capacitor is bounded at 1.798 uF against the
1.0 uF minimum.

## Transient coordination

The SMBJ6.0A on VBUS is a transient shunt, not sustained-overvoltage cutoff.
Its 10.3 V maximum clamp with 20% coordination margin is:

```text
10.3 V * 1.20 = 12.36 V
```

That remains below the coordinated 15/16/18 V-or-higher downstream ratings.
The CC protection coordination bound is 12.4 V * 1.20 = 14.88 V, below the
50 V CC resistors and 48 V connector rating. These comparisons do not prove
survival under an arbitrary-duration overvoltage event.

## Via and fence process

The fabrication census contains 638 vias: nine 0.45/0.25 mm U1 vias selected
for copper-paste fill/cap, and 629 ordinary 0.45/0.20 mm vias that must remain
ordinary. The RF fence audit passes 18 of 18 segments; the worst recorded pitch
is 1.3979 mm. Uploader acknowledgement and received-board inspection are still
required because local Gerbers cannot prove the fabricator's process choice.
