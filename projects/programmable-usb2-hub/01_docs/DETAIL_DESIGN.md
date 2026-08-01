# Detailed design

## Rated operating envelope

The board accepts 12–24 V SELV DC and delivers four independently switched
5 V outputs rated 3.0 A continuous at their USB-A solder terminals. Maximum
declared downstream load is 60 W. At 12 V, 90% conversion efficiency and
0.8 A of 3.3 V logic load, the calculated input is about 6.1 A / 73.5 W; the
input connector, fuse, reverse-protection FETs and copper trunk are therefore
designed around a 10 A fused envelope. The external source must be rated at
least 75 W and must tolerate attached-load startup.

## Input protection

The order is J1 terminal, F1 10 A MINI fuse, LM74810-Q1 controller with two
BSC016N06NS 60 V MOSFETs in a common-drain back-to-back arrangement, then
`VIN_PROTECTED`. The SMBJ26A TVS is on the protected side so reverse input does
not forward-bias the TVS ahead of the controller. The LM74810 dividers set a
nominal 24.22 V overvoltage trip (25.50 V conservative corner) and 10.96 V
UVLO rising / 10.08 V falling. CAP-to-VS is 220 nF; both raw-side controller
decouplers are 100 nF / 100 V. The exposed RTN pad remains floating per the
selected operating mode.

## Five-volt conversion and delivery margin

Two LM5116 synchronous bucks each supply two ports. Their feedback network is
3.92 kOhm over 1.21 kOhm from the 1.215 V reference, giving 5.151 V nominal.
The machine-readable tolerance stack in `03_src/rules/power_tree.yaml` gives a
5.032 V low corner. Each converter is a 7 A cell carrying at most 6 A declared
continuous load.

Each port uses a TPS259470A reverse-blocking eFuse. A 976 ohm ILM resistor sets
3.416 A nominal current limit; the data-sheet/tolerance corner used for design
is 3.044–3.795 A. ITIMER is 2.2 nF, dV/dt is 3.3 nF, OVLO is 36.5 kOhm / 10
kOhm, FLT_N has a 10 kOhm pullup, and EN has a 100 kOhm pulldown. A B340A
Schottky clamps negative VBUS transients locally.

The PCB branch-loss budget is 70 mOhm: 45 mOhm maximum eFuse resistance plus
25 mOhm for board copper and joints. At 3 A, applying the gate's 20% margin to
the computed rail low corner leaves 4.780 V at the receptacle solder terminal,
above the 4.75 V threshold. This explicitly excludes the mating plug and cable;
the release claim requires a four-port 3 A thermal and voltage-drop bench test.

## USB hub and data isolation

USB2517I-JZX is configured as an SMBus slave at address 0x2C (`CFG[2:0]=001`).
Ports 1–4 feed external sockets and port 5 feeds the STM32G0B1 management USB
device; ports 6–7 are disabled during pre-enumeration configuration. Hub
PRT_PWR outputs are active high, OCS inputs are active-low open-drain.

Each external pair passes through an FSUSB42MUX. SEL is fixed low so HSD1 is
the only used throw. OE_N high disconnects the common D+/D- pins and OE_N low
connects them. A 10 kOhm hardware pullup therefore guarantees disconnect while
the MCU is resetting or unprogrammed. The unused HSD2 pins are not connected.

USB geometry is 0.25 mm width / 0.15 mm gap on L1 over the uninterrupted L2
ground plane, with <=0.50 mm intra-segment mismatch. This is a preliminary
90-ohm estimate; order-time stackup calculation and an eye test remain release
requirements.

## Host control and reported state

The STM32 management interface uses fixed 64-byte PHUB v1 records with
CRC-32. Per port it separately reports commanded power, final enable readback,
measured VBUS present, voltage, current estimate, FLT/latched fault, commanded
data state, and OE_N-derived data state. Actual child connection/enumeration is
an operating-system hub-topology fact and is merged by the host utility; the
firmware never invents it.

## Fabrication posture

The four-layer board uses the JLCPCB advanced tier because the TPS259470
thermal lands contain 0.25/0.15 mm plated-over filled vias. USB1130-15-A is the
locked 3 A USB-A receptacle but has no LCSC placement code; the present release
is therefore not fully assembled/orderable until those four connectors are
consigned or installed after assembly. Controlled impedance, 1 oz outer
copper and the selected four-layer stack must be recorded with the order.
