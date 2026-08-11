# USB Hub 3S v4 — Stage 1 design calculations

Status: architecture/parts calculation. Component-level schematic values not
listed here remain Stage 2 obligations.

## Load and input trunk

At nominal 5V, simultaneous continuous output is:

```text
Pcontinuous = 3 * 5V * 2A + 5V * 3A = 45W
Ppeak       = 3 * 5V * 2.5A + 5V * 3A = 52.5W
```

The gate uses the conservative high regulation corners, 5.180V and 5.241V:

```text
Pcontract = 3 * 5.180V * 2A + 5.241V * 3A = 46.803W
Iin,max   = 46.803W / (0.90 * 9.0V) = 5.78A continuous
Ppeak,wc  = 3 * 5.180V * 2.5A + 5.241V * 3A = 54.573W
Iin,peak  = 54.573W / (0.90 * 9.0V) = 6.74A
```

The VIN_TRUNK contract is 7.2A and the user-installed fuse is 10A. The 17.5A
Phoenix input terminal has ample nominal current headroom, but its field wiring
and terminal temperature remain first-article measurements. The fuse is
not a port-current regulator; TPS2557 and TPS25810 provide the local limits.
First article must measure fuse-holder, FET and copper temperature at low-pack
voltage and coincident load.

At the 6.74A calculated peak, Q1 dissipates 0.432W using the DMP3013SFV-7
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
| 5VC_RAW | 41.8k | 10.0k | 5.119932V | 5.240252V | 5.119–5.241V |

These exact inputs are machine-checked in `rules/power_tree.yaml`. Stage 2 must
also apply the module's recommended RT, bootstrap/slew, mode, input and output
parts; no generic values are inherited from v3.

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

Stage 2 uses 39.4k 0.1% from each TPS2557 ILIM pin to GND. TI's worst-case
equations, including resistor tolerance, give:

```text
IOS,min = 127981 / (39.4k * 1.001)^1.0708 = 2.502A
IOS,max =  99038 / (39.4k * 0.999)^0.947  = 3.057A
```

Thus a 2.5A peak is not clipped at the worst-low threshold, while the worst-high
limit remains close to the GCT connector's 3A contact rating. This is a narrow
thermal boundary, not permission to claim 2.5A continuous; first-article tests
must establish peak duration and connector/switch temperature. The resistor
must be adjacent to ILIM because trace resistance changes the threshold. Source:
[TPS2557 datasheet](https://www.ti.com/lit/ds/symlink/tps2557.pdf), section 10.2.

## Shutdown budget

SW1 grounds a common EN_BUS in OFF. With U1/U2 disabled, the USB controllers and
port switches are unpowered. The provisional 250uA ceiling includes both module
shutdown currents, UVLO/enable dividers, TVS/zener leakage and the 35V aluminum
capacitor leakage with engineering allowance. Stage 2 must replace this top-
down allocation with exact maximum-temperature terms; the locked acceptance
limit remains <=1mA at a 12.6V pack.

## Protection coordination

SMBJ15A stand-off is 15V, above the 12.6V operating maximum. Its 10/1000us
maximum clamp is 24.4V. With 20% coordination margin, 29.28V remains below the
30V DMP3013SFV-7 rating, 35V capacitor rating and 42V module absolute maxima. The
clamp is below both modules' 36V recommended ceiling. This arithmetic grades
part survival under the stated pulse envelope; it does not establish the energy
of an arbitrary LiPo wiring event. First article must capture the exact hot-plug
waveform and the release must keep the no-sustained-OV claim.

## Schematic obligations still open

- Exact module frequency/mode, input/output capacitor effective capacitance,
  ripple-current and stability checks against each datasheet application table.
- Exact EN/UVLO divider and every OFF-state maximum/leakage term.
- TPS25810 REF/IN/AUX/OUT capacitors, CC/strap state and Type-C functional test
  points following the vendor application.
- TPS2513A/TPS2557/USBLC6 support values, TPD2EUSB30 CC protection and per-port fault behavior.
- LED/fault indicators, if any, without violating the storage budget.
- Every passive MPN, tolerance, voltage/temp derating and live JLC identity.
- Filled/capped via construction, stencil windows and thermal-pad land patterns
  checked against TI and JLC before placement is frozen.
