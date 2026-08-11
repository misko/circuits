subject: usb-hub-3s-v4 canonical schematic normalized-netlist a05e2e137168
date: 2026-08-11
reviewer: Codex root, separate hash-bound topology/ratings pass using generated-netlist inspection and vendor-source re-derivation
independence_limit: same task owns the design and this review; exact-byte and second-parser checks are independent instruments, but external-human independence remains a declared G-VACUOUS process boundary
review_stage: pre-route
review_kind: topology
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
netlist_sha256: a05e2e137168339f0d0980dce58edd4503c6dd49e79950cc43dd89007c07b27e
parts_sha256: 489acc5734a1133f4656ac2136a40fce883f1c935341dbb8151f8732a240921e
design_rules_sha256: 6ad7729dc81e83def84290c837ce5ac3d6c36598403cff5304b795d0f5975586
raw_netlist_sha256: 41b7a04e51426ae18ec11a7a3c13322776be599af3e74692c894fee71c98078e
schematic_sha256: 6fe3f84f1176ee100811c2e21ef6c213c49676e31135d8c6dcb202e455a40c6b
circuit_json_sha256: b40a3c9f3ad9e15108c98eec1026861c4351c6104ba889acc9d4647e16b959a4
tsx_sha256: d76cfde91a7bac158ad50e1a4a7c34fa9653a844ed73a02057b0dbd4356204a8
manifest_sha256: 5fc11998c0872b092b060dcac19416504e17210d32479bed8904360926907f61
human_schematic_pdf_sha256: 9efafd26b9b3379db7a253902e186045efab6c40cfafe8b02a4457fa299ca1f8

The checker-defined `netlist_sha256` normalizes only KiCad's export time and
UUID-shaped instance stamps. Component identities, values, footprints, nets,
nodes, physical pin names and no-connects remain byte-bound. This review is a
permission to spend on placement, not a fabrication or safety approval.

# Pre-route topology review

## Verdict and method

No P0/P1 source-to-netlist, pin-identity, protection-order, converter-topology,
port-policy, ratings or rule-tier defect remains in the exact state above. The
schematic is SOUND to proceed to placement and deliberately DO-NOT-ORDER.

The review used three paths: direct netlist traversal of every critical rail,
the repository's independently implemented semantic gates, and a new reading
of the exact manufacturer application/pin tables. The final generated state is
76/76 refdes in source, manifest, circuit JSON, KiCad schematic and netlist;
60 nets and 270 connected nodes. TSX-DIAG reports zero embedded errors. ERC is
zero errors. The 562 recorded ERC warnings are 336 generated off-grid geometry,
149 synthetic-library lookup, 76 footprint-library lookup and one generated
wire-end warning; the exact netlist still passes 39/39 label-survival and 43/43
pin assertions, so none is an electrical orphan.

The one-page human schematic is electrically coherent and readable when
zoomed, but its auto-layout is denser and less conventionally left-to-right
than a hand-sectioned production schematic. That is a documentation-quality
debt to grade again at release, not evidence of a different netlist.

## Execution trace reconstructed from the netlist

```text
BAT+ J1.1
  -> F1.1 -- 10 A user-fit fuse -- F1.2
  -> Q1 drain pads 5..8 -- P-FET/body-diode polarity -- source pads 1..3
  -> VIN
       -> D1 cathode; D1 anode -> GND                 transient clamp
       -> C1 100 uF / 35 V -> GND                    lead damping
       -> R2 1 M -> EN_BUS; SW1 common -> GND in OFF shutdown
       -> U1 TPSM63610 -> 5VA
            -> U4/U5/U6 TPS2557 -> VBUSA1/2/3 -> J2/J3/J4 VBUS
            -> U7/U8 TPS2513A -> local DP_Ax/DM_Ax charge signatures
       -> U2 TPSM63604 -> 5VC_RAW
            -> U3 TPS25810 attach switch -> VBUSC -> all four J5 VBUS contacts
            -> U3 CC1/CC2 -> D6 connector clamp -> J5 A5/B5
```

The Type-C D+/D- and SBU contacts are explicit independent no-connects. USB-A
D+/D- stop locally at their TPS2513A signature controller and USBLC device;
there is no upstream connector, hub IC, USB PHY, PD controller or board-wide
data pair. This is a four-port power distributor, not a USB data hub.

## Protection and shutdown

The exact input order implements ADR-0005. Q1's drain is on `VBAT_FUSED` and
source is on `VIN`, so its body diode initially passes a correct source toward
the load and blocks a reversed pack. D5 is a separate 12 V source-to-gate
zener, cathode on VIN; D1 is the SMBJ15A transient suppressor after reverse
blocking, cathode on VIN and anode on GND. This avoids forward-biasing an
upstream unidirectional TVS during reverse connection.

SMBJ15A's 15 V stand-off is above the 12.6 V operating ceiling. Its cited
24.4 V 10/1000 us clamp, with the project's 20% coordination factor, remains
below the 30 V P-FET, 35 V electrolytic and 42 V module transient ratings. This
is not active sustained-overvoltage cutoff and no converter fail-high claim is
made, matching the user's boundary.

SW1 grounds the common active-high EN bus in OFF; its third throw is NC. The
intentional 1 M pull-up draws 12.6 uA at a full pack, and the downstream port
devices are then unpowered. The 250 uA stored-state design allocation is well
below the locked 1 mA acceptance limit, but TPSM63604 and several leakage terms
do not all carry guaranteed hot maxima. OFF current over temperature remains a
mandatory first-article measurement rather than a falsely closed paper claim.

## Converter cells and output margin

U1 and U2 are plain bucks because 9 V minimum input exceeds every output.
Their physical SW lands are no-connects exactly as TI requires; their VCC and
NC pins are also explicit no-connects. Each module has two 10 uF / 50 V input
MLCCs, a 0 ohm RBOOT-CBOOT link, the documented 1 MHz RT value, and VLDOIN tied
to its output. U1 uses auto mode plus 20 k spread-spectrum tone correction and
three 47 uF outputs. U2 uses three 47 uF outputs. These cells follow TI's
[TPSM63610](https://www.ti.com/lit/ds/symlink/tpsm63610.pdf) and
[TPSM63604](https://www.ti.com/lit/ds/symlink/tpsm63604.pdf) application and
layout requirements, apart from the intentional custom feedback ratios.

The exact 0.1% dividers and 1% references recompute to 5.060651–5.179531 V for
5VA and 5.110052–5.230132 V for 5VC_RAW. With 20% residual path margin, all
three USB-A ports retain 106 mV beyond their complete 2 A path allocation and
the Pi path retains about 18 mV beyond its complete 3 A board/contact/cable
allocation. E-TOPO passes 4/4 rails and E-MARGIN passes all four delivery
paths plus their four feedback-window assertions. The input contract is
46.773 W and 5.8 A at 9 V/90% versus the declared 7.2 A trunk class.

## Port policy

U3 implements TI's minimal fixed-5 V/3 A DFP circuit: IN1, IN2, AUX, EN, CHG
and CHG_HI share 5VC_RAW; 100 k 0.1% connects REF to REF_RTN; three 47 uF
capacitors provide the cold-socket input bank; 100 nF is local and 10 uF is on
VBUSC. CC1 and CC2 remain separate and reach TPD2EUSB30. The topology matches
the [TPS25810 3 A application](https://www.ti.com/lit/ds/symlink/tps25810.pdf)
and is attach-controlled fixed-5 V Type-C, not USB-PD.

Each USB-A port has a separate TPS2557, local 100 nF input bypass, 150 uF
post-switch capacitor, fault pull-up/test point and 39.2 k 0.1% ILIM resistor.
TI's equations give 2.515 A minimum and 3.072 A maximum current-limit corners.
The lower corner preserves the commissioned 2.5 A short peak; the upper is a
fault limit, not a continuous-current claim. GCT rates each USB1130 power
contact at 3 A, so 2 A continuous remains the stated service and 2.5 A peak
duration remains a thermal qualification. TPS2513A provides BC1.2/legacy
recognition, while the higher available current is explicitly proprietary and
not represented as USB-IF BC1.2 compliance.

Raspberry Pi's official material calls for a 5 V/3 A supply for Pi 4 and warns
about cable voltage loss; the project therefore binds its load-plane claim to
a nominated short cable measured at no more than 20 mOhm round trip, not an
arbitrary Type-C cable. See the [Pi 4 datasheet](https://datasheets.raspberrypi.com/rpi4/raspberry-pi-4-datasheet.pdf).

## Manufacturing boundary and blockers

The adopted rules are consistently advanced: `nets.yaml` selects
`jlc_4layer_advanced`, `route.yaml` selects `fab_tier: advanced`, and assembly
requires JLC four-layer resin-filled/copper-capped via-in-pad. This is justified
by TPS25810's 0.50 mm WQFN and the direct exposed-land thermal-via fields, not
by USB data density. JLC's own [via-covering guidance](https://jlcpcb.com/help/article/pcb-via-covering)
identifies epoxy/copper fill plus copper cap as suitable for via-in-pad and
warns that ordinary ink plugging is not suitable there.

Ordering remains blocked on manufacturer-exact placement, thermal-via and
stencil implementation; placement-phase pin/layout/render review; routing and
full DRC/parity; live JLC BOM/CPL stock and assembly verification; uploader
confirmation of the fill/cap process; and first-article OFF-current, rail,
load-step, fault-limit, cable-drop, hot-plug and thermal qualification.

design_verdict: SOUND
order_verdict: DO-NOT-ORDER
