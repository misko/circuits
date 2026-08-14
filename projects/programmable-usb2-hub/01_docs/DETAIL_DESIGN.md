# Detailed design

## Rated envelope

The board accepts an absolute 12-24 V SELV input and targets four independently
switched 5 V / 2 A continuous outputs at the mated USB-A test plugs. The two
LTC3889 channels each supply two ports, so each regulated rail is designed for
4 A continuous. The downstream maximum is 40 W. The exact boundary is encoded
in `requirements.yaml`: integrated eFuse, board copper/vias/joints and both
mated power contacts are included; cable and appliance are excluded.

## Input protection

J1 feeds exact Littelfuse 0297010.H in a Keystone 3568 holder, then LM74810-Q1
with two CSD18533Q5AT 60 V common-drain MOSFETs. SMBJ24A is on
`VIN_PROTECTED`. The 90.9 kOhm / 4.64 kOhm OV network accepts the commissioned
24.0 V ceiling at its low corner and trips below the TVS minimum breakdown at
its high corner. The admitted surge is explicitly limited to a 50 V maximum
open-circuit Thevenin source with at least 1.6 ohm source impedance and a
10/1000 us-or-shorter, <=1 ms pulse. Using SMBJ24A's 26.7 V minimum breakdown
gives at most 14.563 A; 14.563 A x the independent 38.9 V clamp maximum is
566.5 W, below its 600 W rating. LM74810's 5.4 us maximum OV turnoff deglitch
plus 36 nC / 168 mA gate discharge bounds Q2 disconnect below 5.7 us. Q1/Q2/U1
see at most the 50 V upstream ceiling; Q3-Q6/U2/U3 see the protected 38.9 V
bound. The AP63203 3.3 V regulator is cascaded from regulated AUX_6V. This
board makes no automotive load-dump or lightning claim; first articles capture
both D1 and VIN_PROTECTED to verify layout-induced overshoot.

## Five-volt conversion

One LTC3889IUKG#PBF controls two 250 kHz synchronous bucks. Each channel uses a
CSD18533Q5AT high-side/low-side pair, one MWSA1206S-6R8MT 6.8 uH inductor, one
WSL2512R0100FEA 10 mOhm Kelvin shunt, and four 100 uF / 10 V output capacitors.
Linear16 word `0x14DC` is 5.21484375 V; the declared rail
window is 5.183925-5.246075 V after the conservative full-temperature and
programming allowance.

At 24 V input and the -20% inductance corner, the inductor is 5.44 uH and

`Delta_I = 5.21484375 * (1 - 5.21484375/24) / (250000 * 5.44uH)`

= 3.0013 A peak-to-peak ripple. At 4 A load the peak is 5.5006 A, and the
required peak with 15% margin is 6.3257 A. Program
`IOUT_CAL_GAIN = 0xD280` Linear11 = 10 mOhm
and `IOUT_OC_FAULT_LIMIT = 0xCBC0` Linear11 = 7.5 A, selecting the documented
75 mV full-scale tier. Applying the explicit 68/75/82 mV threshold range and
the shunt's +/-1% tolerance gives 6.7327 A worst-low and 8.2828 A worst-high.
The low corner passes the required peak, the high corner is below the
inductor's 15.2 A Isat(-20%) rating, and worst-high shunt dissipation is
0.686 W below its 1 W rating. Temperature, ringing, current-limit waveform and
load-step recovery remain first-article tests.

## Per-port power path

Each port uses TPS259470ARPWR, whose integrated back-to-back MOSFETs provide
true reverse blocking. A 1.47 kOhm 1% RILM gives 2.268 A nominal and an
approximately 2.021-2.519 A guaranteed range after device and resistor
tolerance. A 2.2 nF ITIMER bounds overload blanking and a 3.3 nF DVDT capacitor
sets soft start. Dedicated active-low FLT feeds both the hub OCS input and MCU;
firmware latches a faulted command off. ILM reaches the ADC through 1 kOhm but
has no shunt capacitor because TI limits total ILM capacitance to 50 pF.
Post-switch VBUS has a separate divided, filtered ADC channel.

The guaranteed connector-boundary resistance is 135 mOhm maximum: 45 mOhm
eFuse, 10 mOhm PCB/vias/joints, and 80 mOhm for qualified VBUS+GND mated
contacts. At 2 A with 20% residual margin this consumes 324 mV. From the
5.183925 V worst-low rail, the mated-plug corner is 4.859925 V, above 4.75 V.
Copper extraction and hot four-wire measurement must each confirm the 10 mOhm
board allocation.

TPS259470ARPWR passed the pre-selection rule on 2026-08-01 with exact-stock
evidence from two independent suppliers: Mouser reported 9,831 units and
JLC/LCSC C3662799 reported 1,736. Release rechecks volatile stock on order day.

## Hub, data isolation and control

USB2517I-JZX runs in SMBus mode. Ports 1-4 feed FSUSB42MUX switches; OE_N high
physically disconnects and OE_N low connects. Hardware pull-ups guarantee
disconnect during reset. Port 5 connects to the STM32G0B1 management USB
device. The PHUB protocol separately reports commanded power/data states,
enable/OE readback, measured VBUS, current estimate and faults. Actual child
attach/enumeration is merged by the host utility from the operating system.

Hardware pull-down transistors hold both LTC3889 RUN inputs low while the MCU
applies the exact PMBus image. The ASEL pins are left in the datasheet-defined
open state; firmware first writes `MFR_ADDRESS = 0x4F` through global address
`0x5A`, then uses device address `0x4F` for all reads. Firmware must read back
every load-bearing LTC3889 value, including
`0x14DC`, `0xD280` 10 mOhm calibration, `0xCBC0`, 250 kHz, phases and fault responses,
before releasing either rail. The MCU then releases USB2517 reset to latch
SMBus mode; the hub remains unattached while the image is loaded and verified.
Only a final write of `USB_ATTACH=1` exposes the hub upstream. Ports 1-5 are
enabled and ports 6-7 disabled. Any bus error or mismatch leaves rails, hub,
port power and data paths in their safe states.

## Fabrication and qualification

The four-layer advanced-tier board uses the exact stackup recorded in
`floorplan.yaml`; USB impedance is an order-time calculator/coupon check.
USB1130-15-A is rated for at least 3 A and is therefore retained for the
proprietary 2 A power path, but remains a
consigned/manual-placement sourcing line unless the exact part becomes
JLC-placeable. Release checks include DRC/ERC/parity,
body/pad clearance, pin identity, critical USB routing, RF schematic/PCB/fab
reviews, assembly/twin/source checks, and fresh final adversarial reviews.
First articles then undergo hot resistance, four-port 2 A thermal soak,
simultaneous load-step, current-limit waveform, surge, USB eye
and reconnect/packet-error tests.
