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

The supported release envelope is at most 125 mA total RT9013 load at
`TA <= 50 C`, with the module WS2812 commanded dark. At the worst declared USB
and LDO corners, dissipation is
`(5.25 - 3.234) V * 0.125 A = 252 mW`. The RT9013 dossier's conservative
SOT-23-5 upper-bound model gives `(150 - 50) C / 250 C/W = 400 mW`, leaving
148 mW of arithmetic margin. This is a design bound, not proof of the module's
actual thermal impedance; representative-firmware current and case-temperature
measurements are required before hardware acceptance. Firmware outside this
load/ambient/LED envelope is unsupported.

The carrier adds only PE42482 supply current (200 uA maximum) and passive
pull-network current to the filtered RF-switch rail; the status LED is driven
from a module GPIO and returns to GND. A BLM21SP601SN1D with 60 mOhm maximum
DCR separates 3V3_MOD from 3V3. The 4.7 uF bulk, 1 uF and 100 nF capacitors are
all on the downstream 3V3 side. The conservative machine rule charges the
delivery path with the full 125 mA even though the module's own load never
crosses the ferrite.

## RF-control input proof

R_S1..R_S4 are 100 ohm, 1% source resistors and R_PD1..R_PD4 are 10 kohm
pull-downs at the PE42482 inputs. The proof does not credit RP2040 output
impedance. At `VDD(max)=3.366 V`, `Z0(max)=67 ohm`, and `Rs(min)=99 ohm`, the
first incident step is `2*3.366*67/(67+99) = 2.717 V`, below the switch's
3.6 V control absolute maximum. The settled high is
`3.366*10000/(10000+99) = 3.333 V`, well above the 1.17 V maximum VIH
threshold. With a conservative 20 pF input, five time constants are about
`5*(99+67)*20 pF = 16.6 ns`, negligible against the 4.267 us blanking window.
Firmware additionally selects 2 mA drive and slow slew on GP0..GP3.

## Layout-critical budgets

- All PE42482 RF routes: 50-ohm geometry derived from the chosen stackup,
  F.Cu only, no vias, continuous L2 reference.
- SMA launch ground posts: solid plane connection and local fence; signal
  barrel antipad follows the authored footprint.
- RP2040-Zero: 18.00 x 23.50 mm module outline, accessible USB-C mouth, no
  carrier copper/tracks/vias/pours under its live underside-pad field, and a
  sample-measured physical gap over its carrier-facing components.
- Module control: GP0–GP3 remain in physical order through R_S1–R_S4; no vias
  inside the module joint field.
- Module USB/QSPI/clock remain entirely on the module and do not enter the
  carrier netlist.

## Bring-up and characterization

Check 3V3_MOD-to-GND and 3V3-to-GND resistance before fitting the module. The
RP2040-Zero is DNP at JLC. Before fitting a production batch, measure actual
samples: board thickness, the tallest carrier-facing component, and
castellation coplanarity. Use an electrically insulating fixture/gauge that
supports only bare module-edge interspaces; it must not bear on the crystal,
RP2040, RT9013, underside pads, or other components. Establish and record a
positive gap above the tallest measured part, keep the module parallel to the
carrier, tack opposing castellations, recheck the gap, then hand-solder and
inspect every fillet. A drawing/STEP nominal alone is not acceptance because
Waveshare publishes no protrusion or coplanarity tolerance.

After the fit inspection, load a firmware image that exposes state, cadence,
and fault/status counters over USB. Measure all
eight switch paths, RX1 main loss, reference tap loss, isolation, and phase at
70 MHz, 100 MHz, 500 MHz, 1, 2, 4, 5, and 6 GHz. Publish raw Touchstone data
and a host correction table; do not claim calibrated AoA performance from PCB
geometry alone.

## Fabrication/order instructions

- Order the four-layer `JLC04161H-7628` stack, nominal 1.6 mm, ENIG.
- Select the advanced small-via option required by the authored 0.25/0.15 mm
  finished-via/drill geometry; do not accept an automatic standard-tier
  substitution.
- Request controlled impedance for the masked L1 CPWG. The authored 0.36 mm
  width is a preliminary field-solver model on the declared stack, not a fab
  guarantee: use JLC's order solver, allow JLC to adjust width/spacing while
  preserving 50 ohm intent, and request/retain the impedance coupon/TDR report.
- Obtain written JLC acceptance for plug-in through-hole assembly of all ten
  KH-SMA-KE-Z jacks. If they cannot accept that process, order the carrier
  without those placements and hand-fit them; never silently convert the CPL.
- In the uploader preview, confirm PE42482 pin-1 orientation, LED cathode, all
  ten SMA identities, and the resolved BOM `(LCSC, value, refdes)` echo.
- Keep U_MCU off BOM, CPL and paste. Its sample-metrology/fixture procedure
  above is a physical build gate, not an automated-PCBA instruction.

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
