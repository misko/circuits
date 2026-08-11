subject: usb-hub-3s-v4 canonical schematic electrical-netlist 56259186049e
date: 2026-08-11
reviewer: Codex root, separate hash-bound topology/ratings pass using generated-netlist inspection and vendor-source re-derivation
independence_limit: same task owns the design and this review; exact-byte and second-parser checks are independent instruments, but external-human independence remains a declared G-VACUOUS process boundary
review_stage: pre-route
review_kind: topology
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
netlist_sha256: 56259186049e0344119d4862f1fc3cf52709924f0298b36098cb8ca141737597
parts_sha256: d2c061e3ea7d3ed1ed57410d6ef4cf551384ed02440339c8fcee0207b7f4fd3d
design_rules_sha256: d527db4303161f3501ebcdcff57e3314318bf79599a4915bec429f4cd0d887dd
raw_netlist_sha256: bfaec338e4598ee29ed395e46563380e264db568a824d90e0fe5f2759a9e2ad8
schematic_sha256: 71b598821511a220c2a59204ca199489956578f169efa246416866a4d85e9559
circuit_json_sha256: 954da1f76f9894f61478451a1fa0d48dcc50eb47f5d43e035540c31ae18d4dba
tsx_sha256: d76cfde91a7bac158ad50e1a4a7c34fa9653a844ed73a02057b0dbd4356204a8
manifest_sha256: 5fc11998c0872b092b060dcac19416504e17210d32479bed8904360926907f61
human_schematic_pdf_sha256: a85b912f51c6b3df56c87a39a7a1ce5509fc5d3b2beec1d2d3adf1b7876f45ab

The checker-defined `netlist_sha256` normalizes KiCad's export time,
UUID-shaped instance stamps, schematic source path, generated Sheetname/
Sheetfile properties and project-derived netclass labels. The separately bound
rules digest owns netclass policy. Component identities, values, footprints,
non-sheet properties, nets, nodes, physical pin names and no-connects remain
byte-bound. This review is a permission to spend on placement, not a
fabrication or safety approval.

# Pre-route topology review

## Verdict and method

No P0/P1 source-to-netlist, pin-identity, protection-order, converter-topology,
port-policy, ratings or rule-tier defect remains in the exact state above. The
schematic is SOUND to proceed to placement and deliberately DO-NOT-ORDER.

The Stage 3 hash rebind above covers layout-evidence, pin-alias and assembly-
fiducial additions only. The normalized netlist remains exactly
`a05e2e137168...`; no component, value, connection or no-connect changed, so
the topology conclusions are not reopened.

The Stage 4 pre-route rebind covers only the routing recipe, measured
pad-launch scopes and associated rule-area/zone declarations. The normalized
netlist remains byte-identical, so no topology conclusion changed.

The final pre-route rebind additionally records J5's fab-local locator-corner
relief, parity-safe explicit thermal vias, simple-zone validation, rail-test
point locations and hole-clearance-aware tap/via settings. The from-source
rebuild changed generated schematic/netlist serialization, so the witness was
not copied forward: the exact regenerated netlist was traversed again. Its
semantic projection remains 60 nets and 270 nodes, the critical rail traces
below are unchanged, and all independent semantic gates pass; the current
electrical artifact was re-reviewed and is now bound as `56259186049e...`.

The routed-replay rebind changes only `flow.budgets_s.tscircuit_build` and
`flow.timeouts_s.tscircuit_build`, adding observability/deadline metadata to
the foreign producer. It changes no electrical rule, route geometry or board
artifact; the broad design-rules digest nevertheless includes all route YAML.

The deterministic-replay rebind additionally removes only the exporter path,
generated sheet metadata and project-derived netclass labels from the topology
digest. Direct diffing proved these were the complete differences between
netlists exported from the byte-identical full-build and pinned schematics.
Clean/known-bad tests retain value, footprint, connection and pin sensitivity.

The review used three paths: direct netlist traversal of every critical rail,
the repository's independently implemented semantic gates, and a new reading
of the exact manufacturer application/pin tables. The final generated state is
76/76 refdes in source, manifest, circuit JSON, KiCad schematic and netlist;
60 nets and 270 connected nodes. TSX-DIAG reports zero embedded errors. ERC is
zero errors. The 486 recorded ERC warnings are 336 generated off-grid geometry,
149 synthetic-library lookup and one generated wire-end warning; the exact
netlist still passes 39/39 label-survival and 43/43
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
