subject: USB Hub 3S v4 final schematic topology and physical-pin design
date: 2026-08-12
reviewer: Codex fresh-context topology/pin/datasheet reviewer
context-given: exact schematic/netlist, project contracts/rules/parts dossiers, and locally vendored authoritative datasheets
source_commit: cc8368ffbb7b93cf8f4b567534e8537df792d638
review_stage: pre-route
review_kind: topology
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
schematic_pdf_sha256: df1e051f99d22590e4989e06b041d921cab43e8b8e359c0615f885dc55db9379
netlist_sha256: ed689c7d75719a3c7955511a2b1311fb0438443cb2ef6da58280ed97a4461763
exact_netlist_sha256: cdfe6036d270e6e030a363d3e756aaebc80ea5cafc320dadc7652f1c345e9265
parts_sha256: 07da71701403799d279677f0a50f5817940c5a0b2cf15cdb2521b0860d563d97
design_rules_sha256: 1836747093e3a866efaae089ac787a6db42133ead8d09d0dc948c9b35a20af21

# Independent pre-route topology review

## Scope and method

I independently reviewed the exact ten-page schematic PDF and electrical
netlist named above, all active `02_parts/*/part.yaml` records, the authored
requirements/power/protection/invariant contracts, and the locally vendored
manufacturer datasheets. I did not take a machine-gate result or an earlier
review verdict as evidence that the design is correct. I reconstructed the
net membership directly: 88 components, 69 named nets and 324 connected
physical pins, then compared every multi-pin active/connector/diode pin with
the manufacturer's pin figure and pin-functions table. Exact hashes were
rechecked at entry and immediately before this review was written.

The intended product boundary is power distribution only: three charge-only
USB-A receptacles and one fixed-5-V Type-C source. There is no upstream USB
connector, USB hub/PHY, USB Power Delivery controller, or USB data path. The
input is a protected 3S pack whose external BMS/disconnect owns the 9.0-V
lower service boundary. The board deliberately has no active sustained-input
or converter-fail-high overvoltage cutoff and is a supervised prototype.

## End-to-end path trace

The exact netlist implements the complete input chain
`J1.1 BAT_POS -> F1 -> VBAT_FUSED -> Q1.D(5..8) -> Q1.S(1..3) -> VIN`.
Q1 is a P-channel DMP3013SFV-7 in the correct ideal-diode orientation: its
body diode permits positive start-up from fused battery drain to protected
source and blocks a reversed pack. R22+R23 provide 200 kohm from source to
gate and R1 provides 100 kohm gate-to-ground. D5's cathode is at VIN and its
anode at the gate. D1 SMBJ15A is cathode-to-VIN/anode-to-GND and is correctly
placed after reverse blocking, so a reversed pack does not forward-bias the
rail TVS. C1 polarity is VIN-positive/GND-negative.

VIN feeds two independent buck modules. U1 TPSM63610 supplies `5VA_RAW`; U9
TPS259827ONRGET is the sole series bridge to `5VA`; U4/U5/U6 TPS2559 then
independently feed `VBUSA1/2/3` and J2/J3/J4. U2 TPSM63604 supplies
`5VC_RAW`; U3 TPS25810 is the sole series attach-controlled bridge to `VBUSC`
and all four J5 VBUS contacts. No output receptacle bypasses its intended
switch. Ground, exposed-pad and parallel input/output lands are all on the
expected nets.

SW1 common is EN_BUS, its OFF throw is GND and its ON throw is explicitly
open. R2 is the only VIN pull-up, so OFF hard-disables both buck modules and
therefore removes power from every downstream source IC. This is enable-gated
shutdown, not a galvanic battery disconnect.

## USB-A power-only cells

Each TPS2559 has pins 2/3/4 and active-high EN pin 5 on 5VA, pins 7/8/9 on its
own VBUSA rail, pin 6 on an exact 43.2-kohm ILIM resistor to GND, FAULT pulled
up locally, and both GND and PowerPAD on GND. TI SLVSCL5A gives the applicable
current-limit equations and the characterized 44.2-kohm row. Charging the
declared resistor tolerance/TCR gives approximately 2.554--2.849 A: above the
2.5-A short-peak requirement and below the GCT USB1130 3.0-A contact rating.
That remains a short-peak/fault threshold, not permission for 2.5-A continuous
service.

Each USBLC6-2SC6 has pin 5 on the matching post-switch VBUS, pin 2 on GND and
the two flow-through pairs on only that receptacle's D+/D- charging-signature
nets. U7 serves ports 1/2; U8 channel 1 serves port 3. Every USB-A data contact
terminates locally at a TPS2513A and its clamp. No such net reaches another
receptacle, an upstream port, a PHY, or a hub controller. U8 pins 3/4 are
unused driven I/O, not falsely called NC; leaving them unloaded is within the
TI SLVSBY8D pin/electrical limits. The design's 2-A/2.5-A behavior is correctly
bounded as a proprietary charge-only extension rather than a USB-IF BC1.2
current-compliance claim.

U9 is the exact `TPS259827O` no-OVLO circuit-breaker variant in TI SLVSEI3D's
device table. IN pins 1/2/3/16, IN pad 25 and EN_UVLO are on 5VA_RAW; all eight
OUT pins are on 5VA; RETRY_DLY and LDSTRT are grounded; R26=210 ohm programs
the aggregate limit; C29=47 nF owns ITIMER and C30=3.3 nF owns dVdt. IMON, PG
and NRETRY are sanctioned opens. RETRY_DLY-to-GND selects latch-off and
cycling SW1 removes U9 input power to reset it. Applying TI's Equation 4 and
full-temperature characterized coefficient corners gives the declared
6.160253--8.066419-A band. Its low corner clears 6-A service, its high corner
is below the three-port 8.547-A worst-high sum, and C29's 11.129--45.962-ms
timer passes every <=10-ms service peak while bounding operation above U1's
8-A continuous rating inside U1's documented 10-A peak envelope.

## Type-C source and no-data/no-PD intent

U3 TPS25810 pins IN1, IN2, AUX, EN, CHG and CHG_HI are all on 5VC_RAW.
According to TI SLVSCR1C Table 3 this selects Type-C 3-A Rp advertisement and
the 3.16--3.64-A current-limit range. OUT pins 14/15 alone feed VBUSC. R14 is
100 kohm from REF to REF_RTN as required. CC1 and CC2 remain separate from U3
through the connector-side D6 channels to J5 A5/B5. D6 is the 5.5-V
TPD2EUSB30 variant, which is compatible with the CC operating range. U3's
unused open-drain DEBUG/AUDIO/POL/UFP/LD_DET pins are explicitly open, a state
TI permits; FAULT alone is pulled up for observation.

J5 A4/A9/B4/B9 are VBUSC; A1/A12/B1/B12 and shell are GND. A6/A7/B6/B7
(D+/D-) and A8/B8 (SBU) are explicit no-connects. Thus U3 detects Rd on either
CC pin, applies/discharges VBUS according to attach state and advertises
fixed-5-V Type-C current. It does not negotiate USB-PD and it carries no USB
data or alternate-mode signal.

The 5VC_RAW cold-socket bank also closes structurally: C9/C10/C11 and C23 are
on U3 IN, while C13 is on OUT. The declared worst-corner combined input bank
is 155.592 uF versus TI's 120-uF cold-socket requirement, and the 10-uF OUT
capacitor follows TI's recommendation.

## Regulator and physical-pin disposition

Both modules have every VIN/VOUT, VLDOIN, feedback, RT, PG, enable/mode,
bootstrap and ground land on the required net. U1 SW4, VCC6 and NC16 and U2
SW2, VCC7 and NC15 are explicitly open exactly as their TI pin tables direct.
All exposed/thermal ground lands are GND. U1's six exact 22-uF ceramic outputs
derive to 80.784 uF effective against 75 uF required; U2's three derive to
40.392 uF against 30 uF. The omitted CFF networks are intentional: U1's
admitted polymer ESR zero can fall below the datasheet's 200-kHz no-CFF
boundary, and U2's mixed bank is not the close-to-minimum table case.

The revised U2 divider is implemented exactly as R11=4.12 kohm, R24=24.3 ohm
and R12=1 kohm. The declared 0--500-nA FB-current term is explicitly an
engineering qualification screen because TI publishes only 10 nA typical; it
is not misrepresented as a manufacturer guarantee. The resulting exact-board
voltage, frequency response and load-step behavior are therefore release
measurements rather than claims silently inferred from nominal arithmetic.

Every other intentional open is explicit in the netlist: SW1.3; U8.3/4;
U9.9/11/13; U3.16--20; and the J5 data/SBU contacts. J1's manufacturer-neutral
contacts are deliberately assigned pad 1 BAT+ and pad 2 GND by the board
contract. F1 represents the Keystone holder; the replaceable Littelfuse
0297010.WXNV 10-A fuse is correctly an explicit user-fitted element rather
than a fictitious assembled component.

## Findings and release boundary

P0: None.

P1: None. No schematic or netlist correction is required before placement.

P2 / preserved qualifications:

1. The Type-C load-plane service is conditional on a hot four-wire result of
   <=39 milliohm for the complete nominated J5-to-Pi interconnect. This
   includes both mated pairs, plug substrates/terminations, cable conductors,
   the Pi receptacle and Pi entry path. A single contact's USB-IF/GCT LLCR is
   not substituted for that complete-path result.
2. First article must measure both rails over input, load and temperature,
   including the U2 FB-current uncertainty, <=15-mV steady variation reserve,
   startup/load-step ceiling and mixed-bank loop response. These are explicit
   qualification bounds, not unresolved schematic connectivity.
3. First article must measure USB-A and Type-C path resistance/current sharing,
   Q1/U1/U2/U3/U4-U6/U9/fuse-holder temperature, U9 <=50-ms overload behavior,
   OFF current <=1 mA over the qualified temperature range, and the actual
   battery-lead hot-plug waveform.
4. The selected fuse provides catastrophic wiring/trunk protection only.
   Installation must confirm prospective pack fault current below its 1000-A
   interrupt rating; no semiconductor-protection or sustained-overvoltage
   claim is created.
5. This remains a supervised prototype with a required external >=9.0-V pack
   disconnect and no active sustained-overvoltage/fail-high cutoff. That is the
   commissioned boundary, not a missing implementation claim.

## Closed verdict

The exact schematic/netlist topology is SOUND for its commissioned power-only,
fixed-5-V, no-PD, no-active-OVP prototype boundary. The power paths, physical
pins, polarities, enable/current-limit/configuration networks and intentional
opens are complete and datasheet-consistent. `DO-NOT-ORDER` remains mandatory:
placement/routing, JLC fabrication/assembly evidence and the enumerated
first-article electrical/thermal/interconnect qualifications are not supplied
by this schematic-stage review.
