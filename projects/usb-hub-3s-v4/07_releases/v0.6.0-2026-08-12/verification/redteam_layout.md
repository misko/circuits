subject: USB Hub 3S v4 final routed board
date: 2026-08-12
reviewer: redteam-agent (layout/thermal/power-integrity lens)
context-given: exact-board/full-tree
source_commit: 2c15f1dd1ef600bed4c6081062bc7f3640c25237
board_sha256: 9888b1267744b8f659ce3f57dd0cbdd037e208440781bd1c80da88b2b1966dfb
design_verdict: SOUND
order_verdict: DO-NOT-ORDER

# Independent adversarial layout / thermal / power-integrity reseal

## Scope and evidence binding

I independently reviewed the exact canonical board named in the header, its
filled-zone copper, stack-up, route/current contracts, routed copper renders and
layer PDF, exact-board DRC, V-PROCESS and A-VIA reports, and the authored
first-article boundaries. The earlier render review was not used as authority.
This lens covers physical current paths, return paths, thermal transfer,
switching/sense geometry, connector mechanics, clearances and fabrication
process intent. It does not re-grade schematic topology or supplier stock.

Exact corroborating evidence:

| Evidence | SHA-256 / exact result |
|---|---|
| `06_build/drc/gate.json` | `b795882fe8cd6a5ade1e28fb60b4b406f65cd3148e2cf4a53d91d4413ffde116`; KiCad 10.0.4, 0 violations / 0 unconnected / 0 parity |
| `06_build/verification/via_process.json` | `afb11ddc257b4235b2402e42dedf60a6d1c962e565ee05b602d8a74f61c1258f`; 183/183 vias graded |
| `06_build/verification/via_ampacity.json` | `653b23a195964d33e7168927b8a16093838bde9ed74e68c46ad5a14988492ab6`; four serial transfer banks PASS |
| `03_src/route.yaml` | `8fd03f968e4f86403ae60b2e050d6b033f827b3ce1b8d737d19a0dbd827f3874` |
| `03_src/rules/nets.yaml` | `2401f744752f79316ce6fdf25916ca629583b3402745674f85cf23721b56b8a0` |
| `03_src/floorplan.yaml` | `bc08b2c6fd2cdd80c259a358d2788a1c5a99637d5727cd4264f8f40d5787d4ad` |
| `top_copper.png` / `bottom_copper.png` | `b4129d7e9a803ae4000cb2f86e0e5a8fb1f9cc3d17afed7780b2e24e17a0f7e2` / `4b4c7d8f0286efa36b17908eab1409bd5994a10ed1129d2a0253a8796b3dfee0` |
| `pcb_layers.pdf` | `b5ed9d474f648a321405f4300f69cf79786dafd275038abfee1b87e968294a90` |

The exact board census is 95 footprints, 379 pads, 629 track/via objects and 54
zones. Of those routing objects, 183 are vias. The stack is 1.2 mm nominal with
35 um outer copper and 15.2 um inner copper. In1.Cu and In2.Cu are continuous
GND planes except for normal antipads; power distribution is on bounded F.Cu
and B.Cu zones rather than on a thin internal power plane.

## Adversarial path trace

### Input and VIN trunk

`BAT_POS` and `VBAT_FUSED` each use broad 10 mm-deep dual-outer-layer regions;
their through-hole terminal/fuse lands bond the two layers. Q1 sits immediately
after the fuse region. Its four drain lands enter `VBAT_FUSED` and its three
source lands enter the large branched `VIN` region. The source side has six
ordinary 0.60/0.30 mm VIN vias, while the continuous F.Cu path remains primary;
there is no single serial via on which the whole 7.2 A trunk depends.

The VIN polygon reaches both converters without a visible isolated lobe or
thin accidental bridge. U1 is physically much nearer Q1 and owns the 6 A USB-A
service, while the lower-current U2 branch continues south. The wide region and
dual ground planes are credible for routing, but exact resistance and hot rise
remain measurements because the nominal polygon envelope is not a solved
current-density map.

### USB-A aggregate rail and port distribution

U1's six local 22 uF ceramics are arranged as two compact rows at its output,
with the raw rail spreading directly into a 21.3 x 22.0 mm dual-layer zone.
`5VA_RAW` reaches U9 over broad F.Cu, with eleven total layer transfers on that
net. U9's split input PowerPAD 25 and ground PowerPAD 26 remain electrically
separate; pad 25 has four protected 0.50/0.20 mm vias and pad 26 has two.
The only narrow U9 input exception is the documented 0.30 mm by 0.80 mm
pin-16-to-pad-25 local bridge; the other parallel input perimeter lands and
PowerPAD own the trunk interface. No claim that pin 16 is current-free is made.

U9 OUT17-24 enter the protected rail through a 4.2 x 2.1 mm F.Cu collector.
Fourteen distributed 0.70/0.30 mm ordinary vias are the actual serial transfer
to the 16 x 58 mm B.Cu distributor. A-VIA credits 11.76 A at the adopted 10 C
rise screen versus 8.0 A required. There is no former 0.30 mm series bar and no
visible collector island.

Each U4/U5/U6 input island has four ordinary 0.60/0.30 mm vias plus one
protected 0.50/0.20 mm via. A-VIA credits 3.91 A per bank versus the 2.849 A
worst-high switch limit. The vertical B.Cu distributor is broad and the three
banks are spaced consistently. The port-output regions are each 38.2 x 17 mm
on both outer layers. U4 enters its F.Cu region directly; U5 and U6 also have
two parallel 0.30 mm by 0.60 mm pad-local launches to two ordinary vias before
widening on B.Cu. This difference is not a visible current bottleneck, because
U4 retains a broad direct F.Cu path, but it makes the already-planned loaded
per-port resistance/symmetry test important.

### Type-C rail

U2 has two close VIN capacitors, three nearby 22 uF output ceramics and a broad
19.5 x 24 mm `5VC_RAW` region. The 0.30 mm auxiliary U2.5 branch is explicitly
non-trunk; U2.8/U2.9 and the local bank own the output-current path. C23's bulk
positive land is local to U3 IN, and two filled/capped vias at C23 ground close
the cold-socket return directly into the ground planes.

U3's output enters a 21 x 14 mm dual-layer `VBUSC` region; four ordinary vias
support layer sharing, while the direct F.Cu path reaches all four J5 VBUS
contacts. The four VBUS and four GND contacts are retained. CC1 and CC2 remain
separate, reach connector-side D6, and have a local D6 ground via. No power path
is visibly forced through a signal-width route.

## Ground, switching loops and thermal transfer

The two internal ground planes are not routed through slots or necked power
islands. Ninety-nine GND vias (55 ordinary and 44 protected) join local ground
lands and outer copper to those planes. Connector shells and through-hole
ground contacts add direct multi-layer return points at the board edges.

The integrated U1/U2 modules avoid external switch-node/inductor routing.
Their bootstrap, RT and feedback networks are local: U1 bootstrap branches are
about 2.9 mm, U2's main bootstrap branches remain within the converter cell,
and both feedback dividers stay on F.Cu adjacent to their modules. U9 ILIM,
ITIMER and dVdt parts are likewise local. The three TPS2559 ILIM resistors sit
beside their respective devices. None of these sense paths visibly crosses a
high-dV/dt external switch trace; there is no USB high-speed or RF return-path
obligation on this power-only board.

Thermal-via ownership is explicit: U1 has 8 protected ground vias, U2 has 8,
U3 has 6, U4/U5/U6 have 6 each, U9 has four protected input and two protected
ground vias, and C23 ground has 2. The remaining protected sites are deliberate
pad drops. The footprints use separated/windowed paste apertures for U3,
U4-U6, U9 and Q1; U1/U2 use their manufacturer-style divided underside lands.
This is coherent with filled-and-capped via-in-pad assembly, not an attempt to
print paste over open ordinary holes.

V-PROCESS finds 65 protected 0.50/0.20 mm vias, 104 ordinary 0.60/0.30 mm vias
and 14 ordinary 0.70/0.30 mm vias, with zero partially protected vias. The
families are drill-disjoint and the generated order note says to fill/cap only
the complete 0.20 mm family. That proves unambiguous design intent, not the
fabricator's execution.

## Mechanical, clearance and silkscreen observations

The exact sealed run reports all 88 assembled courtyard envelopes with no
close/overlapping pair and no envelope-to-foreign-pad finding, P-LAND with 94
graded lands and zero unreachable lands, P-PADSEP over 346 copper pads with no
different-footprint or paste intrusion failure, and DRC 0/0/0. The copper
plots show no board-edge incursion. All four M3 holes remain approachable and
the three top fiducials are non-collinear and clear.

J1 faces west; J2-J4 face east; J5 meets the south-edge datum. Their mating
approaches are unobstructed at footprint level. Input polarity, fuse rating,
master switch state, power-only/no-data behavior and per-port ratings are
prominent. Polarized capacitor `+` marks and pin/cathode asymmetry marks are
present, although those marks do not establish populated orientation.

## Findings

### P0

None. No visible short, open, severed return plane, isolated high-current pour,
unprotected serial microvia, connector-edge conflict, or destructive thermal
layout defect was found on the exact board.

### P1 — release blockers, explicitly not observed board defects

1. **P1-QA-01 — Exact copper extraction and hot resistance are still open.**
   No `A-AMP`/current-density or extracted DC-resistance artifact exists in
   `06_build`. The authored contracts deliberately require filled-copper
   extraction, U9 pin-bank current-sharing/neck review, loaded three-port
   symmetry, per-port four-wire resistance, and hot Type-C path measurement.
   This is especially consequential because the USB-A residual delivery margin
   is only about 11.7 mV after its allocated loss/margin and the Type-C residual
   is about 5.5 mV. Qualify the exact fabricated copper, vias, solder joints and
   connector lands; do not infer those milliohm budgets from DRC or via count.
2. **P1-QA-02 — Loaded thermal and dynamic behavior are unclosed.** Q1 is
   analytically about 0.575 W continuous and 0.781 W at the coincident peak
   before hot RDS(on) rise. U1 must sustain the 6 A USB-A service and a bounded
   aggregate transient; U2/U3 must sustain the 3 A Type-C load. Measure Q1,
   fuse holder, U1/U2/U3/U4-U6/U9, connector and copper temperatures at the
   declared low-pack/high-load corners. Also close startup, hot-plug, ripple,
   load-step and mixed ceramic/polymer loop response on the first article.
   These tests are pre-existing qualification boundaries, not a newly observed
   layout defect.
3. **P1-QA-03 — Type-VII construction needs fabricated evidence.** V-PROCESS
   proves the saved-board flags and drill-family separation, but resin/copper-
   paste fill, copper cap, plating and stencil execution must be acknowledged
   in the JLCPCB order preview and verified on the first build by X-ray and/or
   cross-section appropriate to the prototype risk. Reject any quote that
   applies the protected process ambiguously to ordinary 0.30 mm vias.
4. **P1-QA-04 — Assembly body/rotation truth is outside layout closure.** The
   current fabrication export reports 22 unsourced placements across 16 LCSC
   codes, including power ICs, Q1, polarized capacitors and connectors. This
   does not invalidate their board placement, but no order may use guessed CPL
   rotations or unreviewed catalog bodies. Close the exact JLC model/rotation
   worklist and inspect the upload preview before release.

### P2

1. **P2-DOC-01 — Preserve exact-artifact identity in qualification data.** Hot
   resistance, thermal images and oscilloscope captures must name this board
   hash, stack-up, copper weight, via process, assembly revision, load plane and
   ambient. Unbound measurements would not close the narrow millivolt budgets.
2. **P2-DOC-02 — Reduce raw-PDF ambiguity at handoff.** The routed layer and
   assembly PDFs contain blank/nearly blank pages and a densely overprinted
   identifier/value page. This is not a PCB defect, but layer-named concise
   manufacturing drawings would reduce operator selection errors.

## Final disposition

`SOUND / DO-NOT-ORDER`. The exact routed layout has credible high-current
geometry, explicit serial via capacity, continuous dual ground planes, compact
power/sense cells, coherent thermal transfer and clean connector mechanics.
No PCB-design defect was identified by this adversarial lens. Release remains
blocked by the planned and explicitly bounded physical qualification,
fabricator-process confirmation and assembly-rotation/body evidence above.
