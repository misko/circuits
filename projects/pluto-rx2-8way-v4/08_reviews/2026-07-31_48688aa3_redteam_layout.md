subject: pluto-rx2-8way-v4 48688aa3  
date: 2026-07-31  
reviewer: redteam-agent (layout/thermal/power-integrity lens)  
context-given: curated-pre-seal-zero-context  
design_verdict: DEFECTIVE  
order_verdict: DO-NOT-ORDER

## Findings

### LTPI-P1-001 — P1 — The RP2040 underside copper keepout is documentation only, and 3V3 copper crosses the live-pad field

Evidence:

- `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/01_docs/ARCHITECTURE.md:29` requires a “complete carrier-side component/copper keepout.”
- `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/01_docs/DETAIL_DESIGN.md:32` requires no carrier copper or parts under the live underside pads.
- `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/02_parts/RP2040-Zero/part.yaml` defines ten 1.01 x 0.61 mm underside pads at 1.27 mm pitch and identifies nine live GPIO pads plus GND as a shorting hazard.
- In `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/04_kicad/pluto_rx2_8way_v4.kicad_pcb:4080`, the supposed keepout is only an `fp_rect` on `Cmts.User`, with the label at line 4156. It is not a KiCad keepout or rule area.
- Independent pcbnew enumeration found only six board zones: four GND pours and the `rf_launch`/`ctrl_escape` rule areas. There is no module keepout.
- After applying U_MCU’s 180° placement, the drawn underside-pad strip occupies board coordinates x = 58.10–59.30 mm, y = 73.80–86.00 mm.
- The 0.40 mm filtered-3V3 segment from (46.55, 70.75) to (59.65, 83.85), authored at `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/04_kicad/pluto_rx2_8way_v4.kicad_pcb:36410`, crosses that strip for 1.697 mm of centerline. The global F.Cu GND pour also fills the remaining strip. Ordinary soldermask is therefore the only isolation from the module’s live underside pads.
- Fresh KiCad DRC reports zero violations, demonstrating that this requirement is not enforced.

Suggested disposition:

- Add a real F.Cu copper/via keepout matching the measured live-pad field, reroute 3V3 outside it, refill zones, regenerate fabrication files, and add an explicit DRC assertion for the keepout.

### LTPI-P1-002 — P1 — The user-fitted module has no defined mechanical support or controlled joint height

Evidence:

- `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/01_docs/DETAIL_DESIGN.md:32` requires physical support for the approximately 1.0 mm carrier-facing components.
- The module dossier measures a 1.000 mm crystal, 0.850 mm RP2040, 0.700 mm regulator, and twenty smaller parts on the carrier-facing side.
- The board provides no spacer, support land, cutout, pin-header mount, or other height-setting feature. No such item appears in `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/06_build/fab/bom.csv`.
- `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/03_src/rules/assembly.yaml` instead directs hand soldering “on the ~1.1 mm standoff the module’s own bottom-side components establish.” This makes the crystal and other populated parts the seating supports and leaves the castellated joints as approximately 1 mm-high solder bridges.
- The module body measures x = 43.70–61.70 mm and y = 69.00–92.50 mm on the carrier. No independent supports occur inside that area.
- USB placement itself is not the defect: the measured receptacle tip reaches y ≈ 93.72 mm, overhanging the y = 93.00 mm carrier edge by about 0.72 mm. The unresolved issue is seating and joint reliability.

Suggested disposition:

- Define a controlled, nonconductive support/fixture scheme outside the component-height keepout, or change to a mechanically supported module interface. Produce a section drawing with nominal joint gap and inspection criteria, then validate on a physical module before ordering assembled carriers.

### LTPI-P1-003 — P1 — SW_V4 runs parallel to ANT4 on F.Cu inside the RF region

Evidence:

- `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/03_src/rules/nets.yaml:123` prohibits long control runs beside RF arms and line 129 requires inner-layer routing under ground across the RF region.
- ANT4 is a 0.36 mm F.Cu trace on x = 39.10 mm from y = 50.25 to 64.25 mm; see `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/04_kicad/pluto_rx2_8way_v4.kicad_pcb:8794`.
- SW_V4 contains 5.85 mm of collinear 0.20 mm F.Cu routing at x = 40.05 mm within y = 56.50–62.55 mm, including the segments at board lines 37642 and 37698.
- Centerline spacing is 0.95 mm. Copper-edge gap is only `0.95 - 0.18 - 0.10 = 0.67 mm`.
- Only one GND via lies in the interline corridor, at (39.61, 56.46); there is no stitched shield along the remaining parallel run.
- All four SW_V nets use far more F.Cu than In2.Cu: SW_V1 43.229/4.285 mm, SW_V2 45.924/2.552 mm, SW_V3 39.159/6.687 mm, and SW_V4 33.295/4.442 mm respectively.
- In1.Cu is a solid GND plane, so the intended isolating layer adjacency exists but was largely not used.

Suggested disposition:

- Drop SW_V4 to In2.Cu at the switch escape and keep it there until outside the ANT4 region, preserving In1 as the continuous separator. Re-measure all four controls for same-layer RF parallelism after rerouting.

### LTPI-P1-004 — P1 — The fabrication bundle does not define the impedance stackup or advanced-via process

Evidence:

- The PCB contains four copper layers and a total thickness of 1.6 mm but no authored `(stackup)` block.
- `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/03_src/rules/nets.yaml:438` assumes JLC04161H-7628 with dielectric spacings `[0.2104, 0.9792, 0.2104]` mm and uses that assumption to assign the 0.36 mm RF width.
- The board contains 3,459 through vias at 0.25/0.15 mm, including 3,443 GND vias. This requires the declared advanced process.
- `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/06_build/fab/pluto_rx2_8way_v4_gerbers.zip` contains only 11 plotted layers plus PTH/NPTH drills. It contains no stackup drawing, impedance table/coupon request, or manufacturing note.
- `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/06_build/fab/MANIFEST.txt` contains only the board name, “DO NOT ORDER” status, and unassembled references.
- The model itself is not closed: `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/03_src/rules/nets.yaml:464` states that its phase constants are for bare copper while the board ships with soldermask, and records a modeled +6.3% effective-permittivity change from 20 µm mask. Applied to the declared constants, that moves delay from 5.9255 to approximately 6.109 ps/mm and adds approximately 5.56° over a 14 mm arm at 6 GHz.

Suggested disposition:

- Add an order/fabrication drawing specifying JLC04161H-7628, copper weights, dielectric thicknesses, controlled-impedance net class, soldermask treatment, 50-ohm target/tolerance, whether the fabricator may adjust width, impedance coupon/TDR reporting, and the 0.25/0.15 mm via process. Recalculate the masked CPWG before freezing width and phase constants.

### LTPI-P1-005 — P1 — The ten plug-in SMA connectors have no executable assembly-service instruction

Evidence:

- `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/01_docs/ARCHITECTURE.md:44` says JLC must confirm/select its plug-in through-hole process.
- `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/06_build/fab/stock_check.csv:10` classifies C504007 as `Plugin`.
- All ten jacks appear in the ordinary top-side `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/06_build/fab/cpl.csv`, but the fabrication candidate contains no order README or assembly drawing selecting the plug-in service.
- Each jack uses one 1.4 mm signal hole and four 1.4 mm ground-post holes. For the specified 0.9 mm square posts, nominal diagonal clearance is only `(1.4 - 0.9√2)/2 = 0.064 mm` radially, making process acceptance and finished-hole interpretation material to assembly.

Suggested disposition:

- Obtain written uploader/order acceptance for all ten plug-in jacks, specify finished-hole requirements and assembly side, and capture that instruction in the released order package. Otherwise exclude the jacks from CPL and define a controlled manual-install process.

### LTPI-P2-006 — P2 — The power-path model understates routed length and describes the bulk capacitor on the wrong side of the ferrite

Evidence:

- Independent graph measurement from FB_3V3 pad 2 to U_SW pad 8 gives 48.415 mm of 0.40 mm copper, including two F.Cu/In2 transitions.
- `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/03_src/rules/power_tree.yaml:75` budgets only approximately 20 mm and 25 mΩ.
- At 1 oz copper, the measured 48.415 mm path is approximately 59.6 mΩ before the ferrite and joints. The documented sum is therefore approximately 124.6 mΩ rather than the declared 100 mΩ. Actual switch current is only 200 µA, so this arithmetic error is not by itself a brownout threat, but the asserted PI model is false.
- `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/01_docs/ARCHITECTURE.md` describes 4.7 µF + 1 µF + 100 nF as local filtering on 3V3. Board pad extraction instead places C_BULK’s 4.7 µF on upstream `3V3_MOD`; only C_SW2 1 µF and C_SW1 100 nF are downstream on filtered `3V3`.
- The 100 nF path from U_SW pad 8 is approximately 3.05 mm of routed copper; the full bead-to-switch run is 48.415 mm.

Suggested disposition:

- Correct the PI model using routed length, explicitly decide which side of the ferrite owns the 4.7 µF capacitor, and shorten the filtered rail or place the intended downstream bulk capacitance locally. Re-run rail impedance/ripple analysis with actual topology.

No P0 finding was established. Fresh KiCad 10.0.4 DRC returned zero violations and zero unconnected items, but it does not cover the module keepout, seating, same-layer control/RF coupling, fabrication stackup, or plug-in assembly obligations above.
