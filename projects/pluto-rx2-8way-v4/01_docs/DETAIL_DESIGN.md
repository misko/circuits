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
