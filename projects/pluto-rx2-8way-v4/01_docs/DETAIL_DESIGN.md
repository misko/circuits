# Detail design — Pluto RX2 8-way v4

## Timing frame

At 30 Msps each ordinary state is 128 blank + 8192 clean samples; the reference
state is 128 blank + 4096 clean samples. One frame is
`7*8320 + 4224 = 62,464` samples (2.082133 ms, 480.276 sweeps/s). A 499,712
sample buffer holds exactly eight frames. Firmware owns this invariant.

## RF pickoff

R_T1 and R_T2 are series 220-ohm 0402 resistors between RX1_MAIN and RF8. With
50-ohm source/load terminations the low-frequency model gives about 0.43 dB
main-line loss and -20.3 dB tap level. The split arm halves effective shunt
parasitance relative to a single resistor. These are modeled values; assembled
release acceptance requires VNA S-parameters and a per-state correction table.

## Module and carrier power

The module vendor's RT9013-33 rail is modeled at 100 mA total module load. The
carrier adds only PE42482 supply current (200 uA maximum), pull-network current
during switching, and one status LED. A BLM21SP601SN1D with 60 mOhm maximum DCR
separates 3V3_MOD from 3V3; the conservative machine rule charges its path with
the full 100 mA even though the module's own load never crosses the ferrite.

## Layout-critical budgets

- All PE42482 RF routes: 50-ohm geometry derived from the chosen stackup,
  F.Cu only, no vias, continuous L2 reference.
- SMA launch ground posts: solid plane connection and local fence; signal
  barrel antipad follows the authored footprint.
- RP2040-Zero: 18.00 x 23.50 mm module outline, accessible USB-C mouth, no
  carrier copper/parts under live underside pads, and physical support for its
  approximately 1.0 mm carrier-facing components.
- Module control: GP0–GP3 remain in physical order through R_S1–R_S4; no vias
  inside the module joint field.
- Module USB/QSPI/clock remain entirely on the module and do not enter the
  carrier netlist.

## Bring-up and characterization

Check 3V3_MOD-to-GND and 3V3-to-GND resistance before fitting the module. Hand
fit the module with its underside clear, then load a firmware image
that exposes state, cadence, and fault/status counters over USB. Measure all
eight switch paths, RX1 main loss, reference tap loss, isolation, and phase at
70 MHz, 100 MHz, 500 MHz, 1, 2, 4, 5, and 6 GHz. Publish raw Touchstone data
and a host correction table; do not claim calibrated AoA performance from PCB
geometry alone.

## Unsealed fabrication candidate — 2026-07-31

This is preparation evidence, not order authorization and not an immutable
`07_releases/` archive. Generated files remain in the gitignored
`06_build/fab/` and `06_build/twin/` work areas.

- JLC four-layer output contains 11 plotted layers plus PTH/NPTH drills, 11 BOM
  rows, and 27 top-side CPL placements. The exporter used no unsourced-rotation
  or illegible-BOM escape hatch.
- `U_MCU` is absent from BOM and CPL and has no paste apertures; it remains a
  user-fitted, hand-soldered module. The ten plug-in SMA jacks remain on the CPL
  and require explicit order-time process acceptance.
- A-POP/A-POS pass for 32 board footprints, 27 CPL rows, and five declared
  unpopulated refs (`H1`–`H4`, `U_MCU`); worst CPL datum error is 0.00000 mm.
- BOM source and legibility gates pass. Live catalog stock covered five boards
  on 2026-07-31 for all 11 lines, but this is necessary rather than sufficient
  because the uploader allocation pool can differ.
- The modeled twin mounts all 27 CPL bodies with registration checks passing.
  KiCad STEP output omits VRML-only bodies, so the PNG twin is the visual
  population truth.

Before any order, retain the full independent pre-seal review battery: fresh
pin review; separate topology/protection and layout/thermal red-team lenses;
render review and dispositions; zero open P0; M-REV and release gates. Also
confirm PE42482 and LED orientation and the through-hole SMA service decision
in the actual uploader. No assembled hardware exists, so rail checks, USB
operation, timing drift, insertion/return loss, isolation, phase, and RX1 tap
calibration remain unmeasured; VNA acceptance must use physical hardware.
