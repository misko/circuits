---
id: 0003
date: 2026-07-16
status: accepted
---
# 0003 — SY8368QNC synchronous 8 A buck on both rails

## Context

Two 5 V rails (8 A and 6 A) from 9.0-12.6 V. Constraints: JLC SMT stock,
no 0.4 mm-pitch QFN (routing skill rule), input must survive a TVS-clamped
hot-plug transient (SMBJ15A clamps at ~24.4 V), minimum external parts.

## Options

(live JLC stock, 2026-07-16)

- **XL4016E1** (async 8 A, TO-220/TO-263) — REJECTED: the SMD TO-263
  variant is 0 stock at JLC (only THT TO-220, 29,833); async topology dumps
  ~2.5 W in a 10 A catch diode and needs a 40-60 µH high-current inductor.
- **TPS54620 / TPS54824** (TI sync 6/8 A, VQFN 0.5 mm) — REJECTED on VIN:
  17 V abs max leaves no headroom over 12.6 V + hot-plug ringing; any TVS
  that protects the board clamps above 17 V.
- **SY8388ARHC** (Silergy 8 A, $0.51, 12,347 stock) — REJECTED: 0.45 mm pad
  pitch (JLC footprint `P0.45`) violates the >=0.5 mm pitch rule.
- **MP8759GD-Z** (MPS 8 A, 26 V, QFN-12 2x3 P0.5, 4,676 stock, $3.07) —
  viable; kept as the designated FALLBACK (near-identical app circuit,
  0.6 V ref, 700 kHz).
- **SY8368QNC** (Silergy 8 A sync, QFN3x3-10 P0.5, C125897, 2,447 stock,
  $1.16) — 4-28 V operating, 30 V abs max on IN/LX/EN (survives the SMBJ15A
  clamp), 800 kHz, 0.6 V +/-1.5% FB, pin-strap current limit
  (ILMT low = 8 A / float = 12 A / high = 16 A), integrated 20/10 mΩ FETs,
  EN may tie to VIN, 400 µs internal soft-start, PG available.

## Decision

SY8368QNC (LCSC C125897) on both rails: rail A (8 A) with ILMT floating
(12 A limit), rail C (6 A) with ILMT tied low (8 A limit).

## Consequences

One BOM line, one layout block instantiated twice. Inductors per datasheet
40%-ripple sizing: 1.5 µH / Isat > 10 A (rail A), 2.2 µH / Isat > 7.5 A
(rail C). Output >= 66 µF ceramic per rail (4x 22 µF 1210), input 10 µF
ceramic x2 at IN pins + upstream bulk. Stock 2,447 is adequate-not-deep:
re-verify at order time; fallback is MP8759GD-Z with a footprint change
(QFN-12 2x3). 0.5 mm pitch inferred from the standard QFN3x3-10 outline —
verify against the JLC/EasyEDA footprint during part.yaml extraction
(recorded as an extraction task).
