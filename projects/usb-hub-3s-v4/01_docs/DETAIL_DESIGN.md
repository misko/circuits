# USB Hub 3S v4 — design calculations and schematic closure

Status: Stage 5 red-team findings are backtracked into the authored schematic
and rules. The regenerated schematic, placement, route and reviews remain to be
completed before any order claim is restored.

## Load and input trunk

At nominal 5V, simultaneous continuous output is:

```text
Pcontinuous = 3 * 5V * 2A + 5V * 3A = 45W
Ppeak       = 3 * 5V * 2.5A + 5V * 3A = 52.5W
```

The gate uses the conservative declared high divider/reference corners,
5.229V and 5.228V. A separate 15mV steady-state variation reserve is checked
against the 5.25V service ceiling:

```text
Pcontract = 3 * 5.229V * 2A + 5.228V * 3A = 47.058W
Iin,max   = 47.058W / (0.90 * 9.0V) = 5.810A continuous
Ppeak,wc  = 3 * 5.229V * 2.5A + 5.228V * 3A = 54.902W
Iin,peak  = 54.902W / (0.90 * 9.0V) = 6.778A
```

The VIN_TRUNK contract is 7.2A. The exact user-installed fuse is Littelfuse
0297010.WXNV, 10A/32V with a 1000A interrupt rating. The 17.5A
Phoenix input terminal has ample nominal current headroom, but its field wiring
and terminal temperature remain first-article measurements. The fuse is
not a port-current regulator; TPS2559 and TPS25810 provide the local limits.
First article must measure fuse-holder, FET and copper temperature at low-pack
voltage and coincident load.

At the 6.778A calculated peak, Q1 dissipates about 0.781W using the
DMP3013SFV-7 17mohm maximum guaranteed at -4.5V gate drive. The continuous
bound is about 0.575W. These are room-temperature bounds, not hot guarantees:
placement must preserve the manufacturer's thermal copper and first article
must measure Q1 hot because RDS(on) rises with temperature.

## Feedback tolerance windows

For both modules:

```text
Vout = Vref * (1 + Rtop/Rbottom) + Ifb * Rtop
R tolerance total = initial tolerance + |TCR| * |temperature excursion|
low  = Vref_min * (1 + Rtop_min/Rbottom_max) + Ifb_min * Rtop_min
high = Vref_max * (1 + Rtop_max/Rbottom_min) + Ifb_max * Rtop_max
```

U1 uses the electrical-table +/-1.5% reference limit; U2 uses TPSM63604's
full-junction-temperature +/-1.0% feedback-system accuracy. Both rows charge
independent +/-0.1% initial divider tolerance and +/-25ppm/C TCR over 100C. U1
uses TI's 0..50nA guaranteed FB-bias range. U2 uses 0..500nA as an analytical
stress screen because TI specifies only 10nA typical; the ten-times-lower
divider impedance makes that 50-times-typical screen practical, but does not
turn it into a manufacturer guarantee:

| rail | Rtop | Rbottom | computed worst low | computed worst high | declared envelope |
|---|---:|---:|---:|---:|---:|
| 5VA | 41.2k +/-0.35% total | 10.0k +/-0.35% total | 5.014892V | 5.228243V | 5.014–5.229V |
| 5VC_RAW | 4.1443k +/-0.35% total | 1.0k +/-0.35% total | 5.064237V | 5.227226V | 5.064–5.228V |

These exact inputs and the module's recommended RT, bootstrap/slew, mode,
input, and output parts are machine-checked in `rules/power_tree.yaml` and
`rules/electrical_invariants.yaml`; no generic values are inherited from v3.

## Delivery-path margin

USB-A is claimed at the board receptacle. Maximum/budgeted series resistance is
4.5mohm TPS259827O + 21mohm TPS2559 + 20mohm PCB/vias/joints + one 30mohm
VBUS contact + one 30mohm GND contact = 105.5mohm. At 2A, including 20%
residual margin, the required headroom is 253.2mV. Computed worst-low 5VA_RAW
provides 264.9mV above 4.75V, leaving about 11.7mV. At the 2.5A short peak,
the un-margined drop is 263.75mV and about 1.1mV remains. The peak is limited
to <=10ms and U9's timer then disconnects a persistent aggregate overload.

The Pi claim is at the load after the nominated cable: 55mohm TPS25810 +
4mohm PCB + a 39mohm qualified complete Type-C interconnect = 98mohm. The
interconnect measurement runs from J5's PCB-side VBUS/GND lands to Pi 4
load-plane sense points and includes both plug/receptacle pairs, both plug
paddle-card/termination paths, the cable conductors and the Pi
receptacle/entry path. USB Type-C Release 2.0 section 3.7.8.1 makes this boundary
necessary: its 40/50mohm LLCR limits cover one mated plug/receptacle contact and
exclude internal plug/receptacle substrates. At 3A and 5% residual margin,
required headroom is 308.7mV. Computed worst-low 5VC_RAW provides 314.237mV
above the stricter 4.75V project boundary, leaving about 5.54mV. The smaller
residual is applied after hot/max/qualified component values, not instead of
them. The exact nominated cable is Amphenol 10165794-Z0030YBLF, 0.3m and 3A,
but none of the three manufacturers guarantees the combined path resistance.
The exact cable/Pi combination must therefore measure <=39mohm at operating
temperature before the load-plane claim is accepted; this is not a claim about
an arbitrary USB-C cable or sink. See the [USB-IF Type-C Release 2.0 specification](https://www.usb.org/sites/default/files/USB%20Type-C%20Spec%20R2.0%20-%20August%202019.pdf),
the [GCT USB4105 Revision B drawing](https://gct.co/files/drawings/usb4105.pdf)
and [Amphenol cable-family presentation](https://cdn.amphenol-cs.com/media/wysiwyg/files/documentation/customerpresentation/usb_type_c_connector_cable_productpresentation.pdf).

Raspberry Pi documents a 5V/3A supply for Pi 4 and notes voltage loss in the
cable; its low-voltage indication is nominally 4.63V +/-5%. This project keeps
the already locked, stricter 4.75V load threshold. See the
[Pi 4 datasheet](https://datasheets.raspberrypi.com/rpi4/raspberry-pi-4-datasheet.pdf)
and [Raspberry Pi power documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#power-supply).

## USB-A current limit

Stage 5 replaces each TPS2557 with TPS2559DRCR and uses an exact 43.2k 0.1%,
25ppm/C resistor from ILIM to GND. TI's characterized 44.2k limits, scaled to
43.2k and extended by initial tolerance plus a 100C TCR excursion, give:

```text
IOS,min approximately 2.554A
IOS,max approximately 2.849A
```

Thus a 2.5A peak is not clipped at the worst-low threshold and the worst-high
limit remains below the GCT connector's 3A contact rating. The threshold is a
fault-limit corner, not a continuous connector claim. This is not permission
to claim 2.5A continuous; first-article tests
must establish peak duration and connector/switch temperature. The resistor
must be adjacent to ILIM because trace resistance changes the threshold. Source:
[TPS2559 datasheet](https://www.ti.com/lit/ds/symlink/tps2559.pdf).

The three port limits are not used as the bank limit: their 8.547A worst-high
sum exceeds U1's 8A continuous rating. U9 TPS259827ONRGET is the exact no-OVLO
circuit-breaker variant. R26=210ohm produces a machine-derived
6.160253-8.066419A charged full-temperature threshold. The calculation applies
TI Equation 4's +0.11A term before scaling its characterized rows, then charges
resistor initial tolerance and TCR. C29=47nF +/-5% C0G, C0G's +/-30ppm/C class bound over
the 100C design excursion, TI's 0.7-1.3V ITIMER comparator delta and 1.4-2.8uA
timer-current limits give 11.129ms minimum and 45.962ms maximum blanking, so
the <=10ms 7.5A service peak passes at every listed corner. A persistent
aggregate fault exceeds even U9's 8.066419A worst-high threshold by 0.481A and
therefore starts the interrupt timer. U9 may regulate 0.066A above U1's 8A
continuous rating during that bounded interval, but remains below U1's
documented 10A peak capability; the exact board must pass the adopted hot
<=50ms transient qualification. C30=3.3nF +/-5% C0G controls U9 dVdt: including the same
30ppm/C over 100C bound, TI's 6.33uA maximum charging current and the 5.015V
rail floor, its capacitor term alone keeps tGHI above 4.253ms and therefore
permits 80.260nF ITIMER capacitance, above C29's 49.498nF maximum, even before
turn-on delay is credited. Cycling SW1
collapses U1 and resets U9. This is overcurrent coordination, not the active
overvoltage cutoff excluded by D1.

## Output-voltage variation boundary

Divider/reference corners are not treated as complete rail maxima. Each rail
reserves 15mV for switching ripple plus steady line/load movement: U1 closes
at 5.228243V + 0.015V = 5.243243V and U2 at 5.227226V + 0.015V =
5.242226V, both below the 5.25V steady-state ceiling. These are exact-board
engineering qualification bounds, not manufacturer guarantees. Startup and
load-step excursions are separately required to remain below 5.5V during
first-article testing; no transient plot is promoted into a production limit.

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

Q1's gate is independently graded rather than inferred from D5. R22+R23 form a
200k upper leg from VIN to RPP_GATE and R1 is a 100k lower leg to ground. At
9.0V, worst resistor tolerance and the +/-10uA gate-leakage direction that
reduces enhancement still give |VGS|=5.291V, above the -4.5V RDS(on) test
condition. At the 29.28V rail coordination corner, opposite leakage and
tolerance give |VGS|=20.314V, below the 25V absolute maximum. Divider current
is 42uA at 12.6V. D5 remains a secondary transient clamp, not the DC bias proof.

The exact fuse has a 1000A interrupt rating, 122A2s typical melting integral
and ambient allowed-current curve. The calculated 5.812A continuous input and
6.780A peak are below its 8.0A allowed load at the admitted 60C maximum local
fuse/holder ambient. This does not prove every LiPo fault: pack/wiring
prospective short current must be confirmed below 1000A, and first article
must verify fuse/holder/copper temperature and non-nuisance operation. No
time-current/I2t evidence coordinates this fuse to Q1 or either module, so it
is catastrophic wiring/trunk protection, not semiconductor protection.

## Stage 5 component closure

The schematic follows the two TI module application circuits at 1MHz: U1 uses
15.8k RT, auto mode, 20k spread-spectrum tone correction, two 10uF/50V X7R
inputs, six 22uF/16V X7R outputs and C22 100uF/16V polymer; U2 uses 13k RT,
two identical inputs, three identical 22uF/16V X7R outputs and C23 180uF/16V
polymer. Both bootstrap slew connections are populated as 0R
for the documented highest-efficiency state and both VLDOIN pins return to the
regulated output. After tolerance, a conservative 20% DC-bias loss and the
full 15% X7R temperature allowance, U1's ceramic bank is 80.784uF effective
against 75uF required and U2's is 40.392uF against 30uF required. C22 is
additional bulk. No feed-forward capacitor is fitted on either module. For U1,
C22's permitted 24mohm/100uF corner places its ESR zero at about 66kHz, below
the 200kHz boundary where TPSM63610 section 8.2.1.2.6 explicitly says not to
use CFF. U2's ceramic bank is already above its minimum and C23 adds substantial
low-ESR polymer bulk, so CFF is also omitted rather than applying the
close-to-minimum recommendation to an unanalysed mixed bank. Exact loop
frequency response and load-step behavior remain first-article qualifications.
The custom feedback ratios remain a
deliberate delivery-drop compensation, not a claim that the TI reference
application used those values.

U3 follows the TPS25810 minimal 3A DFP circuit: IN1/IN2/AUX/EN/CHG/CHG_HI share
5VC_RAW, 100k 0.1% connects REF to its isolated REF_RTN, and C23 contributes a
115.2uF life-corner value after independent initial and endurance allowances.
Together with C9-C11's 40.392uF effective value, the cold-socket bank is
155.592uF against >=120uF required. A 100nF capacitor is local at IN/AUX and 10uF
is at the connector-side OUT rail. D6 shunts both exposed CC contacts to a
short ground return. The Type-C D+/D- and SBU contacts are no-connects.

Each TPS2559 has 100nF local input bypass, 43.2k 0.1%/25ppm/C ILIM programming, a
pulled-up fault test point and 150uF/10V post-switch hold-up at its receptacle.
Each TPS2513A has 100nF local bypass. U7 serves ports A1/A2; U8 serves A3 on
channel 1 and leaves its unused channel-2 DP2/DM2 I/O pins open. Those pins are
not called NC: TI identifies TPS2513A as a dual controller and specifies driven,
finite-impedance DCP nodes (SLVSBY8D Table 1 p.3, pin table p.4 and electrical
table p.6). With no connector or load, the open channel draws no external
current and remains inside every pin limit. The alternative single-channel
TPS2514A would make pins 3/4 explicit NCs, but adds another sourced BOM line
without an electrical benefit; reusing the already qualified dual controller
is the lower integration risk. USBLC6 devices are
wired flow-through on both charging-signature contacts with their VBUS reference
on the individual post-switch port rail. No LEDs are fitted, avoiding storage
current and light-load clutter.

The OFF circuit uses one 1M VIN-to-EN_BUS pull-up and SW1 hard-grounding the
bus. At 12.6V its intentional current is 12.6uA; the Q1 gate divider adds
42uA. Adding both converter
maximum shutdown currents (7.5uA + engineering allowance for U2's specified
1uA typical), the gate network, TVS/zener and capacitor leakage still remains
subject to a maximum-temperature first-article measurement; the schematic has
removed the earlier 100k/126uA enable allocation and stays well below the
locked 1mA acceptance ceiling by design.

Still open after the Stage 5 backtrack: regenerate and independently review the
exact schematic/placement/route; remeasure the TPS2559 land escapes; prove
filled/capped via construction and stencil windows; and complete thermal,
hot-plug, load-step, fuse and current qualification on the actual four-layer
board.
