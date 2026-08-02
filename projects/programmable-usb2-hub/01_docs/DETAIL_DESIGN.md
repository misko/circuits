# Detailed design

## Rated envelope

The board accepts an absolute 12-24 V SELV input and guarantees four
independently switched 5 V / 2 A outputs at the mated USB-A test plugs. The
downstream maximum is 40 W. The power topology gate calculates approximately
4.1 A worst-case input at 12 V including the logic rail; the retained 10 A
fuse/trunk is conservative and supports transient/startup margin.

## Input protection

J1 feeds exact Littelfuse 0297010.H in a Keystone 3568 holder, then LM74810-Q1
with two BSC016N06NS 60 V common-drain MOSFETs. SMBJ24A is on
`VIN_PROTECTED`. The 90.9 kOhm / 4.64 kOhm OV network accepts 24.0 V at its low
corner and trips below the TVS minimum breakdown at its high corner. U4
AP63203 is statically coordinated by its exact 40 V/<400 ms absolute limit
against the TVS 38.9 V/1 ms maximum clamp; first articles capture both D1 and
U4 VIN to detect inductive overshoot.

## Five-volt conversion

Each LM5116 rail serves two 2 A ports. Q3-Q6 are exact AON6266E 60 V switches
with 20 nC maximum Qg. At the declared 110 kHz high corner, two devices plus
the controller's 7 mA maximum bias require 11.4 mA, below the 12.0 mA derated
allowance. R101/R201 are 34 kOhm, giving 98.95 kHz nominal. The retained
6.8 uH inductors remain below 15.2 A saturation at the calculated worst ripple
and 4 A rail load. Switch loss, temperature, ringing and load-step recovery are
first-article acceptance measurements.

R102/R202 are 3.92 kOhm 0.1%, R111/R211 are 11 Ohm 1% in series, and
R103/R203 are 1.21 kOhm 0.1%. Including the LM5116 reference tolerance gives
5.0769 V worst-low and 5.2478 V worst-high.

## Per-port power path

Each TPS259470A has 1.47 kOhm 1% ILM, yielding 2.268 A nominal and
approximately 2.02-2.52 A over device/resistor tolerance. Hardware current
limiting, FLT, post-switch VBUS ADC, ILM telemetry, default-off enable,
soft-start, OVLO, reverse blocking and a local negative-transient Schottky are
independent per port.

The guaranteed connector-boundary resistance is 135 mOhm maximum: 45 mOhm
eFuse, 10 mOhm PCB/vias/joints, and 80 mOhm for qualified VBUS+GND mated
contacts. At 2 A with 20% loss margin this consumes 324 mV, leaving the
worst-case test-plug voltage above 4.75 V. Copper extraction and hot four-wire
measurement must each confirm the 10 mOhm board allocation.

## Hub, data isolation and control

USB2517I-JZX runs in SMBus mode. Ports 1-4 feed FSUSB42MUX switches; OE_N high
physically disconnects and OE_N low connects. Hardware pull-ups guarantee
disconnect during reset. Port 5 connects to the STM32G0B1 management USB
device. The PHUB protocol separately reports commanded power/data states,
enable/OE readback, measured VBUS, current estimate and faults. Actual child
attach/enumeration is merged by the host utility from the operating system.

## Fabrication and qualification

The four-layer advanced-tier board uses the exact stackup recorded in
`floorplan.yaml`; USB impedance is an order-time calculator/coupon check.
USB1130-15-A is rated above the 2 A guarantee but is consigned/manual unless
the exact part becomes JLC-placeable. Release checks include DRC/ERC/parity,
body/pad clearance, pin identity, critical USB routing, RF schematic/PCB/fab
reviews, assembly/twin/source checks, and fresh final adversarial reviews.
First articles then undergo hot resistance, full-load thermal, simultaneous
load-step, surge, USB eye and reconnect/packet-error tests.
