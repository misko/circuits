# USB Hub 3S v4 — selected Stage 1 architecture

Status: Stage 2 schematic closed; placement and physical implementation remain
unapproved. The JLC advanced-tier escalation in ADR-0004 was accepted by D3 on
2026-08-11.

## Execution/power stack

```text
3S LiPo, 9.0–12.6V
  -> J1 Phoenix 1715022 two-position input terminal
       user cable: XT60-to-bare-wire pigtail, polarity-labelled
  -> F1 Keystone 3568 + user-installed 10A MINI fuse
  -> Q1 DMP3013SFV-7 reverse-polarity series P-FET
       gate-source clamp: D5 BZT52C12-7-F
  -> VIN protected trunk
       transient clamp: D1 SMBJ15A to GND
       lead damping: C1 35TZV100M6.3X8, 100uF / 35V / <=340mOhm
  -> U1 TPSM63610 8A buck module -> 5VA
       -> U4 TPS2557 -> J2 USB-A1, 2A continuous / 2.5A peak
       -> U5 TPS2557 -> J3 USB-A2, 2A continuous / 2.5A peak
       -> U6 TPS2557 -> J4 USB-A3, 2A continuous / 2.5A peak
       -> U7/U8 TPS2513A provide local charge signatures only
       -> D2-D4 USBLC6 protect the exposed charging-signature pairs
  -> U2 TPSM63604 4A buck module -> 5VC_RAW
       -> U3 TPS25810 Type-C source/3A attach switch -> J5 USB-C -> Pi 4
       -> D6 TPD2EUSB30 protects exposed CC1/CC2 at J5

SW1 OFF -> EN_BUS = GND -> U1/U2 disabled -> every downstream source unpowered
```

There is no upstream USB connector, hub controller, USB PHY, USB-PD controller,
or data path. USB-A D+/D− contacts terminate only in charging-signature control
and protection; USB-C D+/D− contacts are explicit no-connects.

## Why two modules

All continuous loads consume 45W nominal at the connectors; the tolerance-
corner power-tree contract is 46.773W. At 9V and 90% efficiency, the contract
therefore derives 5.8A at the input. Coincident 2.5A USB-A peaks raise worst-
corner output power to 54.543W and estimated input current to 6.73A.

One TPSM63610 is rated 8A continuous/10A peak, but the output ports together
need 9A continuous and 10.5A peak. Splitting the board gives the USB-A bank an
8A module for 6A continuous/7.5A peak and gives the Pi a separate 4A module for
3A. It also avoids v3's two discrete controller/MOSFET/inductor/compensation
cells. This is recorded in ADR-0002 and `rules/integration.yaml`.

## Interface/standards boundary

The Type-C source follows attach/detach behavior: TPS25810 detects Rd on either
CC pin, advertises 3A, enables VBUS only after attach and discharges it after
detach. It is fixed 5V Type-C current advertisement, not USB-PD. The architecture
is based on the [USB Type-C specification](https://www.usb.org/sites/default/files/USB%20Type%20C%20Spec%20R2.0%20-%20August%202019_0.pdf), the [TPS25810 datasheet](https://www.ti.com/lit/ds/symlink/tps25810.pdf), and [Raspberry Pi's official power guidance](https://www.raspberrypi.com/documentation/computers/getting-started.html#power-supply).

BC1.2 defines a dedicated charging port at 1.5A; it does not standardize this
product's 2A/2.5A USB-A service. TPS2513A supplies the BC1.2 DCP short and common
legacy signatures, while the higher available current is explicitly a
proprietary charge-only extension. No USB-IF BC1.2 current-compliance claim is
permitted. See [USB-IF Battery Charging compliance](https://compliance.usb.org/index.asp?Format=Standard&UpdateFile=Battery+Charging)
and the [TPS2513A datasheet](https://www.ti.com/lit/ds/symlink/tps2513a.pdf).

## Input protection boundary

The order is intentional: fuse first, reverse-polarity FET second, TVS and
damping capacitor on the protected side. Putting an ordinary unidirectional
TVS before reverse-polarity blocking would forward-bias it under a reversed
pack. SMBJ15A is a transient clamp, not active overvoltage cutoff. A sustained
source above 12.6V, automotive load dump, or converter fail-high is outside the
claim and the board remains a supervised prototype.

TI warns that long input leads plus low-ESR ceramic input capacitors form an
underdamped resonant circuit and recommends 47–100uF electrolytic damping with
roughly 0.1–0.4ohm ESR. The selected Rubycon 100uF part is <=340mohm at
100kHz. See the [TPSM63610 datasheet](https://www.ti.com/lit/ds/symlink/tpsm63610.pdf)
and [Rubycon TZV data](https://www.rubycon.co.jp/wp-content/uploads/catalog-aluminum/TZV.pdf).

## Board and manufacturing architecture

Four layers remain appropriate: F.Cu holds components and short local power
geometry; In1.Cu is uninterrupted GND; In2.Cu distributes VIN/regulated power;
B.Cu provides low-density escape and supporting pours. No controlled-impedance
USB data routing exists.

The power-module exposed lands and the TPS25810/TPS2557 thermal pads require
via-in-pad heat transfer. JLC states that vias in/near pads are not ordinary
ink-plug candidates; the selected process is resin fill plus copper cap. That
requires `jlc_4layer_advanced`, not A3's provisional standard tier. See
[JLCPCB via covering guidance](https://jlcpcb.com/help/article/pcb-via-covering)
and ADR-0004. Through-hole USB/battery/fuse connectors remain compatible with
JLC's mixed SMT/THT assembly flow; the 10A fuse blade itself is user-installed.

## Geometry that Stage 2/placement must preserve

- Manufacturer example geometry around each module, including symmetric input/
  output capacitors, quiet feedback takeoff and uninterrupted plane below.
- Filled/capped thermal-via fields whose production option is explicit.
- Input terminal -> fuse -> reverse-FET -> clamp/damping ordering visible in both schematic and
  placement, with a short TVS ground return.
- Short 5VA fanout with independently current-limited port paths.
- TPS25810 and its output capacitance adjacent to the Type-C receptacle; CC1 and
  CC2 stay separate and reach their connector-side D6 clamp before U3.
- Charge-signature ESD arrays are the first devices reached from each USB-A
  connector pin pair and have short ground returns.
- No high-dV/dt/module-switch geometry crosses feedback, CC or charging-signature
  routes; In1 remains a continuous return plane.
