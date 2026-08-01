# Architecture — Pluto RX2 8-way v4

## Signal path

Seven dedicated antenna SMA inputs feed RF1–RF7 of an absorptive PE42482A-X.
The eighth state is a -20 dB-class tap from the eighth/RX1 antenna main line;
the untapped main line continues to the Pluto RX1 output. RFC goes to the Pluto
RX2 output. The switch is controlled in parallel so no serial-bus latency can
consume the 128-sample blanking window.

## Control and timing

A Waveshare RP2040-Zero module integrates the RP2040, 2 MB flash, 12 MHz clock,
USB-C, boot/reset controls and a quiet RT9013-33 LDO. GP0–GP3 are consecutive
both logically and physically and drive the switch through 47-ohm source
resistors; 10 k pull-downs at the switch define a safe 0000 power-up state.
PIO emits the state/blank cadence without host jitter. USB is used for firmware,
configuration, and status—not hop timing.

## Power and protection

The module's USB-C is the only power/data connector. Its RT9013-33 produces
3V3_MOD. A BLM21SP601SN1D ferrite and local 4.7 uF + 1 uF + 100 nF ceramics
create a quiet 3V3 node for the RF switch. The carrier intentionally has no
second USB or 5 V path, avoiding source contention and duplicate protection.

## Physical architecture

The board is a radial RF star in the upper region and a module/control strip in
the lower region. The RP2040-Zero sits at the southeast edge with its USB-C
accessible and a complete carrier-side component/copper keepout. Layer roles:

- F.Cu: all RF, local power and short digital escape.
- In1.Cu: uninterrupted RF ground reference; never routed.
- In2.Cu: digital escape and low-speed control.
- B.Cu: ground pour; the promoted route does not use it for signals.

PE42482 RF arms remain via-free and are length-characterized. The module reduces
carrier nets to 3V3_MOD, GND, GP0–GP4; its underside keepout and USB overhang are
mechanical placement constraints rather than dense-package escape problems.

## Fabrication

Fabrication target is JLC four-layer advanced PCBA with impedance control. JLC
must confirm/select its plug-in through-hole process for the ten SMA jacks. The
RP2040-Zero is deliberately excluded from position/paste outputs and fitted by
the builder after carrier assembly; its populated underside prevents a direct
reflow joint to the carrier.

## System boundary

Pluto and antenna interconnects are cabled. No rigid mechanical mate or
imported foreign-hole pattern exists. Host software freezes receiver AGC and
tracking loops during the sweep and consumes the half-dwell reference marker.

## Programming and control interface

Programming and host control use the RP2040-Zero module's own USB-C connector;
the carrier has no second programming connector. Hold the module BOOT button
while attaching USB to enter its ROM UF2 bootloader. Carrier GPIO binding is
GP0=PE42482 V1, GP1=V2, GP2=V3, GP3=V4, and GP4=status LED. The firmware target
name is the build variable `MCU_BOARD=waveshare_rp2040_zero`.
