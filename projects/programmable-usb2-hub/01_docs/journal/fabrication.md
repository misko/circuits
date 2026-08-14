# Fabrication journal

## 2026-07-31 20:58 — start

- did: Exported a diagnostic JLC package after the valid canonical layout seal and ran rotation, population, datum, BOM-legibility, and assembly coverage checks.
- result: MEASURED BOM 60/60 coded lines and CPL 195 placements; A-ROT blocks 25 placements over 15 codes; A-POP correctly blocks the real through-hole refs F1/J1/J2/J7. J3-J6 are source-owned as not assembled and excluded from position output.
- next: Capture order-day stock, then hand off the external fabrication decisions without treating the diagnostic package as orderable.

## 2026-07-31 21:10 — blocked

- did: Ran the five-board-minimum catalog stock snapshot and separated early deterministic PCBA-readiness checks from the order-day volatile check.
- result: MEASURED A-STOCK passes 58/60 lines; C23017 has stock 3 for quantity 2/board and C780769 has stock 1 for quantity 1/board. The deterministic rotation and process blockers could and should have been detected after part/footprint/assembly freeze, before routing; only the final stock/uploader result must remain an order-day gate.
- next: Add an early PCBA-readiness dry run to future projects; for this release, obtain measured rotations, choose the F1/J1/J2/J7 population process, and choose stocked order codes before the full staged release battery.

## 2026-07-31 21:46 — sourcing iteration

- did: Added the Q-2SOURCE pre-selection rule, ran all 26 dossiers through the Mouser API, read the necessary exact DigiKey product pages, joined them with JLC stock, and corrected R102/R202 to source the specified 0.1% C728591 instead of generic C23017.
- result: MEASURED Q-2SOURCE passes 19/26 and rejects seven MPNs. The corrected BOM improves JLC A-STOCK from 58/60 to 59/60; only C780769/AP63203WU-7 remains low at JLC. A fresh canonical seal remains P-LAND 304/304 and KiCad 0/0/0 with a valid handoff.
- next: Treat the seven rejected selections as a design-input worklist, not release-time waivers; do not order the diagnostic package while sourcing, A-ROT, and A-POP remain red.

## 2026-07-31 22:54 — canonical fabrication handoff

- did: Replaced all seven Q-2SOURCE rejects with exact, dossier-reviewed MPNs; declared U4 consigned from Mouser/DigiKey; represented F1 honestly as two post-PCBA Keystone 3568 clips; declared J1/J2/J7 for JLC post-through-hole assembly; measured the 15 missing rotation codes; fixed EasyEDA zero-padded numeric pad handling in the shared rotation tool; rebuilt from declarative source and exported strictly.
- result: MEASURED Q-2SOURCE 26/26; canonical P-LAND 303/303 and KiCad DRC 0 violations / 0 unconnected / 0 parity; strict export 59/59 BOM lines and 194 CPL placements with A-ROT 194/194; BOM-source identity PASS; JLC live stock 58/59 with only planned-consigned C5248536 at zero. Twin mounted 194/194 bodies but remains red on 21 refs requiring datasheet-backed land-pattern/model adjudication. Fifteen exact codes remain on the mandatory first-order JLC preview human gate.
- next: Do not order this diagnostic package. Resolve the 21 twin-critical refs from manufacturer recommended-land-pattern evidence, run the visual polarity/registration review, then stage and seal a clean immutable release. Repeat Q-2SOURCE and the JLC uploader check on payment day.

## 2026-07-31 23:59 — publish handoff green

- did: Rebuilt and sealed the canonical declarative layout after promoting the proven route chain; regenerated the strict JLC package; reviewed all 21 exact-code twin-critical refs against the manufacturers' recommended lands; encoded the evidence in `03_src/rules/twin_adjudications.yaml`; and reran assembly, BOM-source, rotation-authority, twin, and regression gates.
- result: MEASURED P-LAND 302/302; authoritative KiCad DRC 0 violations / 0 unconnected / 0 parity; BOM 59/59 legible and source-identical; CPL 194/194 rotation-sourced; A-POP PASS; twin bodies 194/194 with zero unadjudicated critical refs; Q-2SOURCE remains 26/26; current JLC catalog stock is 58/59 with only planned-consigned U4 at zero.
- next: Publish only the exact manifest onto a clean `origin/main` feature branch. Before paying, repeat Q-2SOURCE and JLC allocation checks and accept the mandatory first-order 15-code placement-preview gate. No commit, push, staging release, or order was performed in this checkout.

## 2026-08-01 09:20 — release audit backtrack

- correction: The preceding entry used "sealed" for a generated layout seal, but no immutable `07_releases/` archive or two-commit release seal existed. This board had not completed the PCB-design skill's independent pin, render, topology, and layout review battery and was not releasable.
- did: Ran a fresh policy audit against the live canonical board before constructing release staging; inspected each mechanical failure against declarative source and the cited part dossiers.
- result: MEASURED KiCad DRC remained 0/0/0, but policy audit reported 9 FAIL rows. The most important finding was physical, not clerical: AP63203 input capacitor C21 was 24.38 mm from U4 although DS41326 requires it directly across VIN/GND; C23/C24 were also upstream of L3. The declarative floorplan now places the regulator cell in datasheet order, and prose-only adjacency statements have been separated from measurable budgets.
- next: Rebuild the canonical board from source, resolve every resulting electrical and thermal-policy finding, then run the four independent adversarial reviews exactly once on the mechanically green state.

## 2026-08-01 10:45 — pre-release gate correctly stops before review

- did: Rebuilt the canonical declarative board after correcting the AP63203 cell and adding source-owned thermal vias; reran authoritative DRC/parity and the full policy audit; refreshed the strict JLC fab/BOM/CPL package and live catalog stock; and tested legal local placements around all six remaining TPS25947 adjacency misses without editing the canonical artifact.
- result: MEASURED KiCad DRC remains 0 violations / 0 unconnected / 0 parity. The strict package is 59 BOM lines and 194 CPL placements; live JLC catalog coverage is 58/59, with only C5248536 / AP63203QWU-7 at stock zero and already declared PLANNED consignment from the two qualifying independent distributors. `waiver_provenance.py` regenerates 3/3 R-THERM measurements and passes; policy is now FAIL=2 / HUMAN=6 / N-A=7 / PASS=30 / WAIVED=1. A-POP is staging-only (there is no release MANIFEST yet). P-ADJ is real: U10/C422 and U12/C442 input bypass spans plus all four ILIM networks exceed their datasheet-derived limits. Five legal local moves exist, but in the port-4 cell C442 and R444 cannot both meet their limits without either overlapping courtyards or displacing C441/the 3 A P4_VBUS trunk. This is a coordinated cell reroute, not a justifiable blanket waiver.
- next: Do not create a release staging directory and do not launch the four expensive independent reviews while P-ADJ is red. Re-place and reroute the complete port-4 eFuse/timing/input-cap cell (and batch the other five local corrections), then rebuild, require policy FAIL=0 after adding the generated staging MANIFEST, and only then run pin/render/topology/layout review.

## 2026-08-01 13:30 — v1.0 staging stops at independent evidence

- did: Integrated the eFuse placement/routing corrections into `floorplan.yaml` and the source-owned route chain; rebuilt canonically; staged `v1.0-2026-08-01`; exported the complete JLC payload, PDFs, source archive, 3D files, stock evidence, and exact-code twin; then launched the mandated fresh-context pin groups and A-RENDER gate.
- result: MEASURED canonical DRC 0/0/0, board parity 699/699, P-ADJ 27/27, P-ADJ-PAIR 2/2, P-PLANE, A-POP, BOM-source, F-LEGIBLE, fabrication-payload census, and twin 194/194 all pass. The pin review fails Q1-Q6 because the footprints do not preserve physical datasheet drain pin numbers 6-8, and leaves J3-J6 as QUESTION because the supplied GCT evidence and dossiers do not independently state contact numbering/functions. A-RENDER independently fails 29 modeled-body measurements; inspected capacitor/connector crops show that its saturation segmentation selects only part of several bodies, while Q1-Q6 still show untrusted mesh/render displacement. Live JLC remains 58/59, with C5248536/U4 stock zero and PLANNED exact-part consignment.
- next: Do not order or seal. Fix the MOSFET pin model in authoring source, close the GCT contact authority gap, and repair/prove A-RENDER against its known-bad fixtures without widening tolerance. Only then rerun render/topology/layout reviews, stamp hashes from a clean source commit, and seal.

## 2026-08-01 18:00 — adversarial review backtrack

- did: Reconciled the completed pin/render fixes and ran their shared regression suites; read the first complete topology, layout, and render adversarial reviews against the exact staged board.
- result: MEASURED P-PINMAP 7/7, pin-audit 1/1, A-RENDER 21/21, and pcb-flow 31/31 tests pass; targeted pin reviews and same-camera A-RENDER 57/57 close the earlier tool/pin findings. The staged design remains DEFECTIVE: topology has three P0s (transient-rating window, 24 V OV acceptance, total connector/cable output margin), layout has three P0s (USB reference/layer/length, LM5116 loop placement, power neckdowns/vias), and render review has two P0s (missing J3-J6 bodies and false F1 body registration).
- next: Stop sealing and backtrack to architecture/parts/placement. Fix source-owned decisions and geometry, then regenerate and rerun the early gates before any routing grind or release review.

## 2026-08-01 18:28 — early review boundary installed

- did: Added fail-closed `PR-REVIEW` at the first exact schematic/netlist and placed-board artifacts; wired it into both canonical rebuild paths and direct `pcb_flow preflight`; bound its tool bytes into layout-seal provenance; documented the policy; and added clean, known-bad, stale-hash, unmigrated, and declared-vacuity fixtures. Corrected the post-review expansion of the commissioned connector-voltage boundary: USB-IF grades a self-powered hub at its downstream port, not at the far end of an unspecified detachable cable.
- result: MEASURED PR-REVIEW 7/7, rebuild-template 36/36, A-RENDER 21/21, gate-contract 36/36, schema 27/27, and pcb-flow 33/33 PASS; `quick_validate.py` accepts both PCB skills. E-MARGIN remains honestly red at 4/8 using 130 mOhm for eFuse + PCB/joints + both mated connector contacts. The lower-Qg 60 V buck switch and lower-loss reverse-blocking port strategy are not selected: the two-independent-supplier rule applies before either can enter source.
- next: Do not route or package a release. Complete two-supplier stock/identity evidence for the replacement power parts, close the topology arithmetic, generate the exact netlist, and obtain a `SOUND` pre-route topology witness before placement work resumes.

## 2026-08-01 19:24 — architecture/component-selection backtrack resumed

- did: Re-entered the architecture and component-selection gates at the user's direction; held schematic regeneration, placement, routing, and release work until the complete connector-voltage and switch-drive budgets are feasible.
- result: The existing board and v1.0 staging archive remain evidence only. Current declarative arithmetic proves the 130 mOhm TPS259470/PCB/initial-contact path fails E-MARGIN on all four ports, and BSC016N06NS remains rejected as an LM5116 switching FET by the conservative VCC gate-charge budget.
- next: Establish a worst-case feasible regulator plus reverse-blocking protection topology, qualify every changed exact MPN from at least two independent authorized supplier pools, and obtain a fresh pre-route topology review before any placement or routing resumes.

## 2026-08-01 20:39 — architecture iteration 1 (post-back)

- did: Completed the live Mouser/DigiKey two-source comparison for the replacement power set, rejected the stocked module candidate on the binding connector-voltage window, began independent exact-datasheet dossier research, and audited the retained input-protection path against its own dossier.
- result: MEASURED five replacement exact MPNs each had stock greater than ten at both Mouser and DigiKey; the proposed 99.7 mOhm complete port path leaves 75.005 mV static low-side margin. The audit found a separate rating defect: AON6354 is a 30 V FET, while protection_paths.yaml had incorrectly asserted 60 V and exposed Q1/Q2 to a 38.9 V clamp. The 60 V CSD18533 replacement set must therefore include the input reverse-protection pair as well as the four buck switches. P-MOD correctly remains red before the live source rewrite.
- next: Finish official pin maps, equations, module exceptions, and part dossiers; update the architecture/rule files; then require P-MOD, E-SURGE, E-SWDRV, E-PATH, E-MARGIN, and exact-hash schematic topology review to pass before placement resumes.
