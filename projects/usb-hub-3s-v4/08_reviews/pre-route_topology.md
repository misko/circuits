subject: USB Hub 3S v4 C23 supplier-substitution schematic topology and ratings
date: 2026-08-12
reviewer: Codex fresh-context topology/ratings/datasheet reviewer
context-given: exact schematic checkpoint/current diff, circuit/netlist/KiCad schematic, project contracts/rules/parts evidence, and authoritative manufacturer datasheets
source_commit: 2c15f1dd1ef600bed4c6081062bc7f3640c25237
review_stage: pre-route
review_kind: topology
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
checkpoint_sha256: bfbff9c0decfed7de348022ec1352238199f4b2b6c5b8ee05ed6ba659a4a75fc
circuit_json_sha256: 0bca19d0da74d36e4c0d47e80b7d1f812c9c20bb655e7bc1c1c502d02fd8ca95
kicad_schematic_sha256: 114ba1ca14f8cf4bef649c6962bc011cbaebdb0ec494cff31fa8385d587bad43
schematic_pdf_sha256: 1f108b7080a20a4c704e58bfcab9ee3f275ba53b480c526750f9f82df6be99d1
netlist_sha256: ed689c7d75719a3c7955511a2b1311fb0438443cb2ef6da58280ed97a4461763
exact_netlist_sha256: 222667931a0147368cac49ea1b0799e78826ef64f0282dc33907a8287af2612f
parts_sha256: 8e3d14083528ee127709753251ab2f8f4349a34203d73b93f0dd49a5f5dffb2e
design_rules_sha256: ef3693aae5be7dfbb29e762e15203d6e86db57164f31176238be1657b35dfb62

# Independent pre-route topology review

## Scope and method

I independently reviewed the exact checkpoint, `circuit.json`, ten-page
schematic PDF, KiCad schematic and electrical netlist named above; the current
diff; all 25 `02_parts/*/part.yaml` records; the authored requirements,
power, protection and invariant contracts; the exact C29/C30 supplier
identities; the old and replacement C23 dossiers; and the authoritative
manufacturer datasheets. I did not take a machine-gate result or an earlier
review verdict as evidence that the design is correct. I reconstructed the net
membership directly: 88 components, 69 named nets and 324 connected physical
pins, then compared every multi-pin active/connector/diode pin with the
manufacturer's pin figure and pin-functions table. Exact hashes were rechecked
at entry and immediately before this review was written.

The intended product boundary is power distribution only: three charge-only
USB-A receptacles and one fixed-5-V Type-C source. There is no upstream USB
connector, USB hub/PHY, USB Power Delivery controller, or USB data path. The
input is a protected 3S pack whose external BMS/disconnect owns the 9.0-V
lower service boundary. The board deliberately has no active sustained-input
or converter-fail-high overvoltage cutoff and is a supervised prototype.

## Checkpoint and delta adjudication

Every member named by `06_build/checkpoints/schematic.json` matches its
recorded size and SHA-256: rebuild driver, `circuit.json`, schematic PDF,
manifest, KiCad schematic, build provenance and exact netlist. Circuit JSON,
manifest, KiCad schematic and netlist contain the same 88-refdes set. All
45/45 authored net labels and 99/99 pin-map assertions survive the export.

Against the immediately preceding hash-bound review, the sole electrically
relevant source change is C23's fitted identity: APAQ
`160AV5K181M0606C` / JLC C369910 is replaced by Panasonic
`16SVPF180M` / JLC C136277. The polarized 180-uF value, two-pin footprint,
pin 1 on `5VC_RAW` and pin 2 on GND are unchanged. The normalized netlist hash
is exactly unchanged, proving that no schematic net, pin or value changed; raw
export metadata and generated UUID churn account for the new exact-byte hash.
The old APAQ dossier remains in `02_parts` as historical evidence, but the
source, generated circuit and active power rule all select the Panasonic part.

The exact [Panasonic 16SVPF180M product page](https://na.industrial.panasonic.com/products/capacitors/polymer-capacitors/lineup/os-con-aluminum-polymer/series/91057/model/91080)
and [manufacturer datasheet](https://industrial.panasonic.com/cdbs/www-data/pdf/AAB8000/AAB8000C177.pdf)
fix 16 V, 180 uF plus/minus 20%, 22 milliohm maximum ESR, 3.3 A rms ripple at
100 kHz/+105 degrees C, 576 uA maximum leakage, -55 to +105 degrees C and
5000-hour endurance at +105 degrees C with capacitance remaining within
plus/minus 20% of initial. The body mark denotes the negative terminal, so the
selected polarized-symbol mapping is correct. Compared with the replaced
APAQ dossier, voltage, capacitance/tolerance, ripple, leakage, temperature and
endurance corner are identical; only maximum ESR changes, from 21 to 22
milliohm.

An earlier reviewed source delta changed only the supplier identities of the
two U9 timing capacitors: C29 changed from JLC C2220670 to C5451690 and C30
changed from C2239978 to C77036. C29 remains 47 nF in 1206 on
`ITIMER_A`-to-GND; C30 remains 3.3 nF in 0603 on `DVDT_BANK`-to-GND. A later
regeneration also corrected the presentation-only statement that the exact
Littelfuse fuse element is user-fitted in the F1 holder after PCBA; F1 remains
the assembled Keystone holder between BAT_POS and VBAT_FUSED. Those already
adjudicated deltas are preserved in this current witness and introduce no
additional current schematic change.

The exact [Holy Stone HCN catalog](https://www.holystone.com.tw/downloads/series/10000/1000/60/20161108152237_file1.pdf)
row identifies C29 `C1206N473J050T` as 47 nF, J (plus/minus 5%), NP0/C0G,
50 V and 1206; [LCSC C5451690](https://www.lcsc.com/product-detail/C5451690.html)
maps to that exact MPN. The official [Murata part-number list](https://www.murata.com/-/media/webrenewal/tool/library/common-pdf/static-model/component-list-s-mlcc-2506.ashx)
identifies C30 `GRM1885C1H332JA01D` as 3.3 nF, plus/minus 5%, C0G, 50 V and
0603; [LCSC C77036](https://www.lcsc.com/product-detail/C77036.html) maps to
that exact MPN. Both use the adopted plus/minus 30 ppm/degree C C0G class
bound. The C30 dossier/rule update from plus/minus 2% to the exact selected
part's plus/minus 5% is therefore correct rather than an optimistic tolerance
substitution.

The subsequent rules-only rebind adds assembly/CPL policy for the six already
excluded hand-soldered THT refs F1, J1, J2, J3, J4 and SW1, plus documented
manufacturing-CAD land/body adjudications for U1 and J5. Those records govern
population and fabrication-preview interpretation only. They do not change a
schematic pin, net, part value, voltage/current rating, electrical acceptance
equation or checkpoint artifact, so they do not change this SOUND topology
verdict.

The current policy-only delta adds `policy_waivers.yaml` SHA-256
`c9f3abf083d35185be07465d7385296bb36a393b412f6696c327ec0502cc96c3`
and `FIRST_ARTICLE_TEST_PLAN.md` SHA-256
`bcaa103a011e1be88f9ab816b842ed535ab8fb1464916a85f2c2f20b7eb0d506`.
The S-OCCL disposition is bounded to the exact schematic hash above: I
independently reproduced 740/740 placed drawable objects, three named
text-only intersections and zero S-WNET merged-net conductors. It does not
waive connectivity, parity, ERC or independent PDF readability. The
P-SILK-FN disposition is bounded to routed-board SHA-256
`9888b1267744b8f659ce3f57dd0cbdd037e208440781bd1c80da88b2b1966dfb`:
all test-point refs remain visible and the controlled plan maps TP1--TP12;
only TP3--TP12 lack separate on-board net captions. Although the policy reader
applies each waiver by check ID rather than by `refs`, the rationale measures
the complete current populations and enumerates every accepted finding, so it
does not silently absorb another current S-OCCL or P-SILK-FN defect. The two
waivers are documentation/usability dispositions for the supervised
five-board prototype, not topology or ratings waivers.

The test plan is consistent with the reviewed electrical boundary: it retains
current-limited initial power, exact C22/C23 polarity, 9.0--12.6-V input,
2-A-per-port USB-A and 3-A Type-C loads, attach/overload behavior, worst
simultaneous load, the complete hot Type-C-path 39-milliohm limit, thermal
soak, and the absence of sustained-OVP protection. It is a bench procedure,
not a relaxation of this review: the numeric OFF-current, rail-variation,
hot-plug, overload-time, stability and temperature qualifications enumerated
below remain independently controlling even where the plan refers to them as
the documented design limits.

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
the aggregate limit; C29=47 nF owns ITIMER and C30=3.3 nF owns dVdt. Both
capacitors return directly to GND and neither control net has another load.
IMON, PG and NRETRY are sanctioned opens. RETRY_DLY-to-GND selects latch-off
and cycling SW1 removes U9 input power to reset it. Applying TI's Equation 4
and full-temperature characterized coefficient corners gives the declared
6.160253--8.066419-A band. Its low corner clears 6-A service and its high
corner is below the three-port 8.547-A worst-high sum.

C29's full charged capacitance interval is 44.51605--49.49805 nF. Applying
TI's 0.7--1.3-V ITIMER comparator delta and 1.4--2.8-uA discharge-current
limits gives 11.1290125--45.962475 ms. The minimum exceeds the declared
at-most-10-ms 7.5-A service peak, while the maximum bounds a persistent
overload above U1's 8-A continuous rating inside U1's documented 10-A peak
envelope.

For C30, the exact plus/minus-5% tolerance and minus-0.3% temperature corner
give 3.125595 nF worst-low. With the adopted 5.014892-V rail floor, 3.6-V gate
overdrive and TI's 6.33-uA maximum dVdt charging current, Equation 7 gives a
4.253817-ms minimum capacitor-only `tGHI` term. Equation 6 therefore permits
80.260703 nF maximum ITIMER capacitance versus C29's 49.49805-nF worst-high
value: 30.762653 nF of margin without crediting turn-on delay. C29's 50-V
rating also exceeds ITIMER's required 4 V; C30's 50-V rating exceeds the dVdt
pin's `VIN + 4 V` requirement by more than 40 V at the rail high corner. The
wider C30 tolerance does not invalidate startup or voltage rating.

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
remains valid after the substitution. C23 contributes
`180 uF * 0.80 initial tolerance * 0.80 endurance = 115.2 uF`; each ceramic
contributes `22 uF * 0.90 tolerance * 0.80 DC bias * 0.85 temperature =
13.464 uF`, or 40.392 uF for three. The combined 155.592 uF exceeds TI's
120-uF cold-socket requirement by 35.592 uF (29.66%). The 16-V C23 rating is
2.91 times the qualified 5.5-V rail-transient ceiling, leaving 65.625% of its
rating as headroom. The 10-uF OUT capacitor follows TI's recommendation.

## Regulator and physical-pin disposition

Both modules have every VIN/VOUT, VLDOIN, feedback, RT, PG, enable/mode,
bootstrap and ground land on the required net. U1 SW4, VCC6 and NC16 and U2
SW2, VCC7 and NC15 are explicitly open exactly as their TI pin tables direct.
All exposed/thermal ground lands are GND. U1's six exact 22-uF ceramic outputs
derive to 80.784 uF effective against 75 uF required; U2's three derive to
40.392 uF against 30 uF. The omitted CFF networks are intentional: U1's
admitted polymer ESR zero can fall below the datasheet's 200-kHz no-CFF
boundary, and U2's mixed bank is not the close-to-minimum table case.

For the replacement C23, the 22-milliohm ESR ceiling places its own nominal,
initial-low and endurance-low ESR zeros at approximately 40.19, 50.24 and
62.80 kHz. The 1-milliohm increase from the APAQ part moves those zeros down by
about 4.5%, not enough to change topology or the adequacy equations. It does
not waive first-article loop/load-step and thermal qualification: C9--C11
alone still furnish 40.392 uF effective ceramic capacitance against U2's
30-uF minimum, and the polymer remains admitted additional low-ESR storage.

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
6. Assembly must preserve exact C29 JLC C5451690 and C30 JLC C77036 identities;
   a same-value X7R, lower-voltage part or wider-tolerance substitution would
   invalidate the timer/startup proof and this hash-bound review.
7. Assembly must fit C23 as exact Panasonic `16SVPF180M`, JLC C136277, with
   pin 1 positive on `5VC_RAW` and pin 2 negative on GND. Another nominal
   180-uF part requires fresh ESR/ripple/endurance/footprint adjudication and
   repeats the U2 mixed-bank loop, load-step and thermal qualification.
8. S-OCCL and P-SILK-FN are accepted only for the exact hashed schematic/board
   and supervised five-board prototype. Copy the TP1--TP12 controlled map to
   the bench sheet/ORDER_README, and add local TP3--TP12 function legends at
   the next production-oriented copper/silkscreen revision. Any artifact or
   finding-population change requires fresh review rather than inheriting the
   whole-check waiver.

## Closed verdict

The exact checkpoint topology and ratings are SOUND for the commissioned
power-only, fixed-5-V, no-PD, no-active-OVP prototype boundary. The C23
supplier substitution preserves topology, polarity, nominal value, tolerance,
voltage, ripple and life corner; the 22-milliohm ESR ceiling preserves the
155.592-uF bank proof and the explicit first-article mixed-bank qualification.
The previously reviewed C29/C30 timing relations also remain closed. The
remaining power paths, physical pins, polarities,
enable/current-limit/configuration networks and intentional opens are complete
and datasheet-consistent. `DO-NOT-ORDER` remains mandatory: placement/routing,
JLC fabrication/assembly evidence and the enumerated first-article
electrical/thermal/interconnect qualifications are not supplied by this
schematic-stage review.
