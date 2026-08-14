# Pluto RX2 eight-way v5 — release-local design math

This document records the numeric reasoning used by the hardware release. It
is design evidence, not measured first-article performance.

## RF cross-section and return fence

The selected JLC04161H-7628 four-layer stack has 0.2104 mm from F.Cu to the
solid In1.Cu reference plane, nominal dielectric constant 4.4, 35 um outer
copper and 1.6 mm finished thickness. JLC's coated-coplanar calculator inputs
for a 0.295 mm finished trace and 0.200 mm coplanar gap return:

`Z0 = 49.971863887 ohm`, `Er_eff = 3.13660852672`.

At 5.9 GHz, guided wavelength is:

`lambda_g = 299.792458 / (5.9 * sqrt(3.13660852672)) = 28.691 mm`.

The lambda/20 fence limit is `28.691 / 20 = 1.435 mm`; the layout contract
rounds down to 1.400 mm. Saved-board measurement grades all 18 route flanks
and finds a worst aperture of 1.3979 mm. Each of the nine RF nets remains on
F.Cu, with zero RF vias and zero intentional stubs.

## Via geometry and process separation

U1's exposed RF-ground pad uses nine 0.45/0.25 mm filled-and-capped vias. The
remaining 629 vias use 0.45/0.20 mm and receive no fill or cap treatment. At
1.6 mm thickness, nominal drill aspect ratios are `1.6/0.25 = 6.4:1` for the
protected family and `1.6/0.20 = 8.0:1` for the ordinary family.

The distinct drill sizes make the protected family selectable in fabrication
data without applying the paid process to ordinary routing/fence vias.

## Power path and thermal corner

The admitted input is 4.75–5.5 V. The 3.3 V load contract is 20 mA. At the
maximum input, load-only LDO dissipation is:

`P = (5.5 - 3.3) * 0.020 = 0.044 W`.

Including the bounded quiescent term used in the source calculation gives
44.825 mW. With the adopted board-level thermal estimate, temperature rise is
approximately 7.6 degC. This is a design estimate; first-article temperature
and current are the authority.

The input and output capacitor banks each retain a conservative effective
capacitance of 1.798 uF after tolerance/bias derating, exceeding the 1.0 uF
minimum used by the regulator stability contract. The protected-input
capacitors are 16 V parts. The SMBJ6.0A transient clamp's admitted maximum
clamp is 10.3 V; it is not sustained-overvoltage protection.

USB-C CC1 and CC2 each use 5.1 kohm Rd. D+/D-/SBU are intentionally absent;
the connector is power-only. There is no electrical path that intentionally
supplies or back-powers the Pluto.

## RF and state bounds

The board is receive-only. The intended operator RF ceiling is 0 dBm.
+2.5 dBm is retained only as the cited AD9363 input absolute maximum, not as
an operating or qualification target.

The PE42482A-X settling ceiling is 1.4 us. The hardware/protocol design uses
a 5 ms ALL_OFF guard, a nominal ratio of `5 ms / 1.4 us = 3571`. Passive bias
sets `V4..V1 = 1000` (ALL_OFF) while the switch supply is valid and MCU pins
are tri-stated. Firmware behavior is not included or qualified in this release.

The initial separately specified dwell profile is 20/23/26/30/34/39/44/50 ms
with an 80 ms marker body and 5 ms guards, totaling 386 ms per cycle. These
values describe the hardware interface's intended use only; no firmware or
timing pass is claimed by this archive.

## First-article RF acceptance equations

For each selected antenna `i`, retain calibrated `S21_i`, `S11_i` and
`S22_i` at the SMA mating planes. Define insertion loss as
`IL_i(f) = -20*log10(|S21_i(f)|)` and path spread as
`max_i(IL_i(f)) - min_i(IL_i(f))`.

Acceptance is `IL_i <= 2.0 dB` through 1 GHz and `<= 3.5 dB` at 5.9 GHz;
spread `<= 1.5 dB`; active-path return loss `-20*log10(|S11|)` and
`-20*log10(|S22|) >= 10 dB`; common-to-off isolation `>= 30 dB` through
4 GHz and `>= 25 dB` at 5.9 GHz. No path or state may be inferred from a
different path.
