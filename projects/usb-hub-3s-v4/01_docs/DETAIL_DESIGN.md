# USB Hub 3S v4 — design calculations and schematic closure

Status: Stage 2 schematic values are closed and machine-checked. Physical
land-pattern, placement, copper, thermal and assembly claims remain downstream.

## Load and input trunk

At nominal 5V, simultaneous continuous output is:

```text
Pcontinuous = 3 * 5V * 2A + 5V * 3A = 45W
Ppeak       = 3 * 5V * 2.5A + 5V * 3A = 52.5W
```

The gate uses the conservative high regulation corners, 5.180V and 5.231V:

```text
Pcontract = 3 * 5.180V * 2A + 5.231V * 3A = 46.773W
Iin,max   = 46.773W / (0.90 * 9.0V) = 5.77A continuous
Ppeak,wc  = 3 * 5.180V * 2.5A + 5.231V * 3A = 54.543W
Iin,peak  = 54.543W / (0.90 * 9.0V) = 6.73A
```

The VIN_TRUNK contract is 7.2A and the user-installed fuse is 10A. The 17.5A
Phoenix input terminal has ample nominal current headroom, but its field wiring
and terminal temperature remain first-article measurements. The fuse is
not a port-current regulator; TPS2557 and TPS25810 provide the local limits.
First article must measure fuse-holder, FET and copper temperature at low-pack
voltage and coincident load.

At the 6.73A calculated peak, Q1 dissipates 0.430W using the DMP3013SFV-7
9.5mohm maximum at -10V gate drive. This is a room-temperature bound, not a hot
guarantee: Stage 2/placement must provide the manufacturer's thermal copper and
first article must measure the FET hot because RDS(on) rises with temperature.

## Feedback tolerance windows

For both modules:

```text
Vout = Vref * (1 + Rtop/Rbottom)
low  = Vref_min * (1 + Rtop_min/Rbottom_max)
high = Vref_max * (1 + Rtop_max/Rbottom_min)
```

With 1.000V +/-1% reference and 0.1% divider resistors:

| rail | Rtop | Rbottom | computed worst low | computed worst high | declared envelope |
|---|---:|---:|---:|---:|---:|
| 5VA | 41.2k | 10.0k | 5.060651V | 5.179531V | 5.060–5.180V |
| 5VC_RAW | 41.7k | 10.0k | 5.110052V | 5.230132V | 5.110–5.231V |

These exact inputs and the module's recommended RT, bootstrap/slew, mode,
input, and output parts are machine-checked in `rules/power_tree.yaml` and
`rules/electrical_invariants.yaml`; no generic values are inherited from v3.

## Delivery-path margin

USB-A is claimed at the board receptacle. Maximum/budgeted series resistance is
35mohm TPS2557 + 20mohm PCB/vias/joints + 30mohm connector = 85mohm. At 2A,
including 20% residual margin, the required headroom is 204mV. Computed worst-
low 5VA provides 311mV above 4.75V. At the 2.5A peak the same conservative
calculation is 255mV, still below the 311mV headroom.

The Pi claim is at the load after the nominated cable: 55mohm TPS25810 +
5mohm PCB + 15mohm qualified mated contacts + 20mohm qualified cable = 95mohm.
At 3A and 20% residual margin, required headroom is 342mV. Computed worst-low
5VC_RAW provides 370mV above the stricter 4.75V project boundary. The cable
allocation requires a short heavy-gauge cable, approximately <=0.5m 18AWG,
whose complete round-trip conductor resistance is measured <=20mohm; it is not
a claim about an arbitrary USB-C cable.

Raspberry Pi documents a 5V/3A supply for Pi 4 and notes voltage loss in the
cable; its low-voltage indication is nominally 4.63V +/-5%. This project keeps
the already locked, stricter 4.75V load threshold. See the
[Pi 4 datasheet](https://datasheets.raspberrypi.com/rpi4/raspberry-pi-4-datasheet.pdf)
and [Raspberry Pi power documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#power-supply).

## USB-A current limit

Stage 2 uses the live-JLC-orderable 39.2k 0.1% part from each TPS2557 ILIM pin
to GND. TI's worst-case
equations, including resistor tolerance, give:

```text
IOS,min = 127981 / (39.2 * 1.001)^1.0708 = 2.515A
IOS,max =  99038 / (39.2 * 0.999)^0.947  = 3.072A
```

Thus a 2.5A peak is not clipped at the worst-low threshold, while the worst-high
limit remains close to the GCT connector's 3A contact rating. The 3.072A figure
is a fault-limit corner, not a continuous connector claim. This is a narrow
thermal boundary, not permission to claim 2.5A continuous; first-article tests
must establish peak duration and connector/switch temperature. The resistor
must be adjacent to ILIM because trace resistance changes the threshold. Source:
[TPS2557 datasheet](https://www.ti.com/lit/ds/symlink/tps2557.pdf), section 10.2.

## Shutdown budget

SW1 grounds a common EN_BUS in OFF. With U1/U2 disabled, the USB controllers and
port switches are unpowered. The 250uA design ceiling includes the 12.6uA
enable pull-up, TPSM63610's 7.5uA maximum shutdown current, TPSM63604's 1uA
specified 25C value, TVS/zener and 35V aluminum-capacitor leakage, and
temperature allowance. TI does not publish a guaranteed hot maximum for every
term, so paper analysis cannot close the locked <=1mA acceptance limit. The
schematic minimizes all intentional paths; first article must measure OFF
current at 12.6V over the qualified temperature range.

## Protection coordination

SMBJ15A stand-off is 15V, above the 12.6V operating maximum. Its 10/1000us
maximum clamp is 24.4V. With 20% coordination margin, 29.28V remains below the
30V DMP3013SFV-7 rating, 35V capacitor rating and 42V module absolute maxima. The
clamp is below both modules' 36V recommended ceiling. This arithmetic grades
part survival under the stated pulse envelope; it does not establish the energy
of an arbitrary LiPo wiring event. First article must capture the exact hot-plug
waveform and the release must keep the no-sustained-OV claim.

## Stage 2 component closure

The schematic follows the two TI module application circuits at 1MHz: U1 uses
15.8k RT, auto mode, 20k spread-spectrum tone correction, two 10uF/50V X7R
inputs and three 47uF/10V X7R outputs; U2 uses 13k RT, two identical inputs and
three identical outputs. Both bootstrap slew connections are populated as 0R
for the documented highest-efficiency state and both VLDOIN pins return to the
regulated output. Feed-forward capacitors are omitted because each output bank
is materially above the datasheet minimum; they are optional only when the
output bank is close to that minimum. The custom feedback ratios remain a
deliberate delivery-drop compensation, not a claim that the TI reference
application used those values.

U3 follows the TPS25810 minimal 3A DFP circuit: IN1/IN2/AUX/EN/CHG/CHG_HI share
5VC_RAW, 100k 0.1% connects REF to its isolated REF_RTN, three 47uF capacitors
provide the >=120uF cold-socket input bank, 100nF is local at IN/AUX and 10uF
is at the connector-side OUT rail. D6 shunts both exposed CC contacts to a
short ground return. The Type-C D+/D- and SBU contacts are no-connects.

Each TPS2557 has 100nF local input bypass, 39.2k 0.1% ILIM programming, a
pulled-up fault test point and 150uF/10V post-switch hold-up at its receptacle.
Each TPS2513A has 100nF local bypass. USBLC6 devices are wired flow-through on
both charging-signature contacts with their VBUS reference on the individual
post-switch port rail. No LEDs are fitted, avoiding storage current and light-
load clutter.

The OFF circuit uses one 1M VIN-to-EN_BUS pull-up and SW1 hard-grounding the
bus. At 12.6V the intentional divider current is 12.6uA. Adding both converter
maximum shutdown currents (7.5uA + engineering allowance for U2's specified
1uA typical), the gate network, TVS/zener and capacitor leakage still remains
subject to a maximum-temperature first-article measurement; the schematic has
removed the earlier 100k/126uA enable allocation and stays well below the
locked 1mA acceptance ceiling by design.

Still open for placement/fabrication: manufacturer-exact land patterns,
filled/capped via construction, stencil windows, MLCC effective-capacitance
confirmation, and thermal/current qualification on the actual four-layer
board.
