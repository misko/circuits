# Schematic journal

## 2026-08-11 08:00 — start

- did: Entered Stage 2 after D3 accepted JLC four-layer advanced with resin-filled/copper-capped via-in-pad for the already selected module architecture.
- result: MEASURED from the tree: ADR-0004 is accepted; the Stage 1 checkpoint is `f630b9c0`; `03_tscircuit/` contains zero schematic source/generated artifacts, so no pre-decision schematic work can be mistaken for current evidence.
- next: Derive the exact support BOM and pin/net topology from the selected datasheets, author TSX plus its declared manifest, and run preflight before the first build.

## 2026-08-11 08:34 — complete and paused

- did: Authored the 76-component power-only TSX, exact JLC codes, manifest, pad/rail maps, one new exact Panasonic capacitor dossier, complete electrical invariants, and both human/KiCad schematic audiences. Re-derived the TI module, TPS25810 and TPS2557 support circuits from the exact vendored datasheets; compared the Type-C, Pi and via-in-pad boundaries against current official primary material; and wrote the exact-hash pre-route topology review.
- result: MEASURED final run `2afa66dd752e` passed P-MOD 4/4, RF applicability 1/1, TSX-PRE 17/17, TSX-DIAG 0 embedded errors, M-FRESH 9/9, 76/76 components and 270 pins, label survival 39/39 plus pin map 43/43, E-INV 53/53, E-ADR 1/1, EARLY-DESIGN 3/3, E-TOPO 4/4, E-MARGIN 8/8 reported assertions, E-OFF, S-COUNT 76/76, coded-value BOM, and ERC 0 errors. PR-REVIEW passes 1/1 with normalized netlist `a05e2e137168...`, parts `489acc5734a...`, rules `6ad7729dc81e...`, verdict SOUND / DO-NOT-ORDER. The full ERC baseline contains 562 nonblocking generated-render/library warnings and the TSX artifact contains 367 advisory diagnostics; both distributions are named in the review rather than hidden.
- spent: MEASURED wall clock 34 minutes from the 08:00 stage marker. Five driver attempts were informative: a 0.5-second module-contract stop; a roughly 25-second post-build label-map schema stop; a first exact-review stop; a rerun after removing a real D6 proxy-pad clearance error; and the final zero-error diagnostic run. Datasheet/application re-derivation and exact JLC passive matching dominated authoring time; each TSX build/render was roughly 25 seconds.
- friction: The integration schema initially treated a simple TPS2557 as a complex exception; label-survival rejected rows containing only no-connect assertions; `tsci build` returned zero despite printing “completed with errors” for the first D6 proxy footprint; `route.yaml` still said `standard` after ADR-0004 selected advanced; and one TPS2557 dossier sentence still named the superseded 39.4k value. The hash review caught the last two before placement.
- generalized: Freshness, parity and ERC can all be correct while the foreign producer has rejected its own geometry. Added shared `circuit_json_diagnostics.py`, wired it into all TSX entry points and the canonical rebuild template, documented the boundary in both PCB skills/contracts, and added clean/known-bad coverage; the template suite is 40/40 and the checker unit suite is 3/3. Future projects now stop on embedded `*_error` records even when `tsci` exits zero.
- instruction-change candidate: Run rule/config schema lint before the expensive TSX build, not after netlist export; the label-map schema failure spent a full generation cycle without needing circuit bytes. Also add an explicit human-render readability lens: this one-page auto-layout is electrically coherent and zoom-readable but less conventional than a sectioned left-to-right schematic, a distinction no connectivity gate measures.
- next: PAUSE. On user continuation, begin Stage 3 placement from the exact reviewed netlist. Preserve JLC advanced processing, manufacturer module example geometry, filled/capped thermal-via fields, a continuous layer-2 ground plane, connector-edge ESD, short high-current paths and quiet feedback takeoffs. Do not route until the exact placed board passes pin/layout/render/A-RENDER review.

## 2026-08-11 08:51 — handoff

- did: Promoted the two Stage 2 instruction-change candidates into the governed repository-level `improvements.md` ledger as IMP-001 and IMP-002.
- result: MEASURED both items now have explicit `proposed` status, source evidence, intended canonical landing points and executable completion criteria; neither is represented as already implemented.
- next: Keep the items visible through later stage harvests and change status only when implementation plus tests land, or when a dated rejection rationale is recorded.

## 2026-08-11 17:40 — iterate after exact-review backtrack

- did: Re-entered schematic stage after the exact topology and PDF reviews
  rejected the prior artifact. Added the externally owned 9.0 V pack cutoff
  boundary, a no-OVLO TPS259827 aggregate USB-A circuit breaker, complete
  high-side steady-state voltage reserve, and exact R26/C29 support values.
  Split the human document into eight functional sheets, added adaptive
  portrait/landscape fitting, and grouped U9 schematic pins by electrical
  function while preserving physical pin identities.
- result: MEASURED full rebuilds are again 18--19 seconds wall time with TSX
  generation at 9--13 seconds. All 99 electrical invariants, 45/45 surviving
  labels, 98/98 pin-map assertions, four topology rails, twelve margin rows,
  the 9.0 V external source boundary, 90/90 component parity, coded-value BOM
  and ERC zero-error gate pass. The pipeline intentionally stops at the stale
  DEFECTIVE exact reviews before placement.
- spent: One broad experiment adding absolute `schX`/`schY` coordinates to
  nearly every component remained at 100% CPU for more than two minutes. It
  was stopped, completely reverted, and replaced with functional hierarchy,
  selective pin grouping and page fitting. The same source now finishes TSX
  in the established envelope under a 60-second process-group deadline.
- friction: A presentation-only global X stretch detached ports and labels
  from symbol bodies in a test render. It was rejected immediately and
  replaced with orientation-only fitting, which never transforms Circuit JSON
  coordinates. Functionally arranging U1/U2 pins made their support networks
  less coherent, so those two changes were also reverted; only U9 benefited.
- generalized: Recorded IMP-020 for bounded function-first schematic layout
  and IMP-021 for a future aggregate fault-envelope gate. The shared renderer
  now has exact-input immutability and portrait/landscape fixtures; the PCB
  design guidance names the hierarchy -> functional pins -> page fit -> sparse
  absolute constraint order.
- next: Regenerate once after the U1/U2 reversion, obtain fresh exact topology
  and schematic-render verdicts, and resume the pinned checkpoint only if both
  are SOUND.

## 2026-08-11 17:50 — pre-review contract preflight

- did: Froze the refreshed schematic artifacts and commissioned two fresh
  zero-context reviews, then stopped both before verdict when a direct
  authored-source scan found that `route.yaml`/`floorplan.yaml` still encoded
  the pre-U9 single `5VA` rail. Corrected every regulator-side use to
  `5VA_RAW`, made U9 the only bridge to protected `5VA`, split the copper
  zones, added exact U9 assertions and re-legalized the added breaker,
  capacitor bank and test points on a disposable generated board.
- result: MEASURED disposable generation places all 90 anchored footprints
  with 0 copper-pad overlaps and 0 anchored courtyard overlaps. Placement
  gates and pad-separation pass; P-PINMAP grades 192 physical identities; the
  critical-route negative-applicability contract and fab-tier preflight pass.
  Focused regression suites pass 52/52 topology, 18/18 early electrical,
  12/12 review binding, 5/5 schematic rendering and 46/46 rebuild-template
  tests. No reviewer witness was accepted against the stale contract.
- spent: About ten minutes. The first disposable board generation was under
  one second and named every collision; two small anchor iterations produced
  the clean placement. This was cheap compared with a human review or route.
- friction: The existing schematic review digest binds the whole
  `route.yaml`, but there was no machine gate proving that its named nets and
  pins agreed with the exact netlist before reviewers were launched. The
  initial added-part anchors also overlapped legacy capacitors/testpoints.
- generalized: Added IMP-022 for static net/pin-reference validation plus a
  disposable placement preflight before human review. The present board is
  fixed now; the generic checker remains proposed so this repair does not
  become a mid-stage pipeline rewrite.
- next: Regenerate the exact checkpoint after the corrected adopted rules,
  then relaunch both adversarial reviews from zero context. Resume only on two
  current SOUND verdicts.

## 2026-08-11 18:05 — timer-corner closure and readable freeze

- did: Re-derived the TPS259827 fault timer and startup timing from the current
  TI Rev. D limits instead of the prior typical-value calculation. Changed
  C29 to 47 nF so the full low-capacitance/low-threshold/high-current corner is
  10.575 ms, added C30 = 3.3 nF on DVDT so the worst minimum capacitor term is
  4.04 ms, and checked the corresponding 51.7 nF maximum ITIMER value against
  the datasheet startup relation. Split the three USB-A power branches into
  one page per port and isolated the shared charging-signature controllers.
- result: MEASURED the exact 91-component rebuild completes in 15.97 seconds,
  with TSX generation at 8.195 seconds. All 100 electrical invariants, 46/46
  labels, 99/99 pin maps, twelve margin rows, coded-value BOM and zero-error
  ERC gate pass; the pipeline stops only at deliberately stale review
  witnesses. A disposable 91-footprint board passes all 30 authored placement
  assertions with zero pad/courtyard collisions, 192 graded physical pin
  identities, placement and pad-separation gates, critical-route applicability
  and JLC four-layer-advanced tier preflight. A page-by-page normal-scale pass
  found the new ten-page PDF readable without clipping or ambiguous NCs.
- spent: Roughly fifteen minutes for the datasheet re-derivation, exact passive
  selection, source/rule/document update, one cheap label-map correction, full
  rebuild, disposable placement generation and visual inspection. The only
  validation-chain false stop was an absolute-vs-project-relative CLI argument
  mistake; rerunning the same checker with an absolute Circuit JSON path took
  under two seconds.
- friction: The existing electrical gates accepted a nominal timer capacitor
  and did not combine capacitance tolerance, timer threshold/current limits and
  the DVDT/startup constraint. The error therefore required a manual primary-
  datasheet corner audit. This is direct additional evidence for IMP-021.
- generalized: Timing and protection claims need the same machine-readable
  min/max envelope treatment as voltage/current margins; a nominal RC value is
  not a guarantee. Functional page partitioning is both faster and clearer
  than broad autorouter constraints: the ten-sheet source stays inside the
  established build envelope while making each port independently reviewable.
- next: Accept no old witness. Obtain fresh zero-context SOUND verdicts bound
  to these exact topology/rules/parts/PDF bytes, then resume the frozen
  checkpoint into placement.

## 2026-08-11 18:39 — correction: full timer corner and pinned-producer bridge

- correction to the 18:05 entry: its 10.575 ms timer claim still omitted the
  capacitor temperature coefficient. A fresh independent review rejected that
  proof. C29 is now exact KEMET `C1206C473J5GECAUTO7210` / JLC C2220670,
  47 nF +/-5% C0G in 1206; C30 is exact KEMET
  `C0603X332G5GECAUTO` / JLC C2239978, 3.3 nF +/-2% C0G in 0603. Including
  the C0G 30 ppm/C class bound over the full 100 C excursion gives C29
  44.516--49.498 nF, 11.129--45.962 ms fault timing, and an 82.795 nF startup
  allowance versus the 49.498 nF worst-high timer capacitor.
- did: implemented generic E-FAULT coordination in `early_design_check.py`,
  reconciled programmer and timer refs to exact `part_value` invariants, added
  six clean/known-bad fault-envelope cases, and made the page 6--8 `N5VA`
  switch-input identity explicit. Pinned tscircuit to 0.0.2300 with a committed
  Bun lock and made the full driver restore it frozen before generation.
- result: MEASURED E-FAULT passes the exact 6/7.5/8.547 A load envelope and
  6.0625--7.9255 A breaker range; early-design tests pass 24/24. Two pre-lock
  builds failed loudly in 3.983 s and 1.247 s rather than hanging. An explicit
  executable-path audit then found global tscircuit 0.0.2112 beside the restored
  local 0.0.2300 graph; the driver now invokes the project-local binary.
  Exact local 0.0.2300 generation takes 7.981 s and the entire schematic
  checkpoint reaches only the intentional stale-review stop in 12.01 s, with
  91/91 component/FPID
  parity, 100/100 invariants, 46/46 labels, 99/99 pin maps and ERC zero errors.
- friction: the pinned producer renamed commodity capacitor tokens from the
  older bare `0402` form to `cap0402`. The first disposable board preflight
  therefore stopped on a blank C12 FPID. The bridge now accepts both dialects;
  its 43-test suite includes a direct compatibility assertion. With that fix,
  the exact 1206 C29 placement passes 91 anchored footprints, 352 pads, zero
  copper/courtyard collisions, 192 physical pin identities, placement,
  pad-separation, critical-route applicability and JLC advanced-tier preflight.
- generalized: a dependency lock makes change reproducible but does not make
  producer schemas stable. Bind the lock in provenance, install it frozen,
  invoke the producer by an explicit project-local path, and test every
  external token boundary explicitly. Machine corner proofs
  must include tolerance, temperature and interacting timing limits, then stay
  subordinate to independent review and first-article measurement.
- next: accept only fresh SOUND topology and delivered-PDF verdicts on the
  exact checkpoint. Then resume into the real placement board, repair the four
  non-blocking silkscreen-ownership warnings, render/overlay it, and pause for
  placement reflection before routing.

### 2026-08-11 — exact-review correction: derive, do not transcribe, ILIM

- observed: the next fresh topology pass found that the recorded U9 threshold
  scaled TI's characterized current rows without first removing Equation 4's
  `+0.11A` affine term. The old checker only compared copied threshold numbers
  with system ratings, so mutually consistent but incorrectly calculated
  numbers passed.
- corrected: R26 is now exact 210ohm, JLC/LCSC C478880. The generic E-FAULT
  gate recomputes its charged threshold from the invariant resistance and
  tolerance, explicit equation coefficients/offset, TCR and temperature
  excursion, then checks the published corner lock. The resulting band is
  6.160253--8.066419A, leaving 0.160A above normal load and 0.481A below the
  three-port worst-high fault. Its possible 0.066A excursion over U1's 8A
  continuous rating is below the 10A peak rating and timer-bounded to 45.962ms
  inside an explicit hot-board <=50ms qualification boundary.
- measured: focused early-design tests pass 34/34, including new known-bad
  omitted-offset, stale-corner, over-peak and overlong-overload fixtures.
- reflection: explicit numbers are not derived evidence. When a safety limit
  is programmed by a component, the gate should own the source equation and
  recompute the limit from the exact fitted value before any hash-bound human
  review is commissioned.

## 2026-08-11 22:13 — replay after downstream gate hardening

- did: Changed the canonical drivers to run exact refilled/schematic-parity
  placement DRC before human placement review. Because the schematic
  checkpoint correctly binds the full driver, ran the bounded TSX producer
  again rather than overwriting the checkpoint or claiming the old build.
- result: MEASURED the producer completed in 8.108 seconds and the full
  schematic chain in about 13 seconds: 88/88 component parity, 91/91
  invariants, 45/45 surviving labels, 99/99 label-pin assertions, 5/5 early
  design families and zero-error ERC. The normalized topology/parts/rules
  witness remains current; PR-REVIEW stopped only on the newly rendered PDF
  hash, exactly as intended.
- friction: downstream driver changes currently invalidate the whole
  schematic checkpoint because it fingerprints one orchestration file rather
  than stage-specific code projections. The bounded replay was inexpensive,
  but the PDF producer is byte-nondeterministic and therefore requires a new
  readability witness even when the normalized electrical graph is unchanged.
- generalized: never re-record a provenance checkpoint merely to move past a
  legitimate source change. Keep semantic topology identity normalized and
  document identity exact, so harmless producer churn repeats only the human
  artifact review it actually changes. A future stage-scoped driver digest may
  reduce replay without weakening either claim.
- next: accept a fresh readability verdict on PDF sha256 `1dccd197...`, then
  verify the checkpoint and resume into exact placement P-DRC.
## 2026-08-12 — ADR-0009 routed-review backtrack

The r8 adversarial topology lens invalidated the former Type-C paper closure.
ADR-0009 reduced the TPSM63604 feedback divider impedance by ten, rebalanced it
to 4.1443k/1k, charged a 500nA analytical FB-bias screen, replaced the connector
allowance with GCT's post-test maximum, and named the exact 0.3m cable plus its
hot four-wire acceptance test. Cheap source gates completed in about 3.3s and
caught one unsupported evidence-basis token before TSX generation.

The full source-to-schematic run then took 14.308s, of which 9.465s was TSX
generation. It produced the fresh ten-page PDF and passed 88/88 component
parity, 91/91 invariants, all early electrical families, all topology/margin
rows and zero ERC errors. It stopped deliberately at PR-REVIEW because all
seven hashes in the previous topology/readability witnesses were stale. This
was the intended safe pause, not a lock-up.

Reflection: generation latency is acceptable and now bounded, but the progress
stream is still dominated by 428 known advisory diagnostics. IMP-014 remains
open: summarize advisory classes during the live run while retaining the full
records in build evidence. Fresh independent schematic reviews are required
before the pinned checkpoint may resume.

## 2026-08-12 — exact human-PDF correction and replay

The first fresh readability lens rejected four drawing facts that all machine
electrical gates correctly ignored: the PDF exposed tscircuit's authoring-only
`N5VA*`/`N5VC_RAW` names instead of the release net names; it showed only the
3568 holder, not the exact user-fitted 0297010.WXNV fuse and rating; C22/C23
used non-polarized symbols; and U1/U2's intentionally open SW/VCC pins had no
local explanation.

The general repair is in `render_schematic_pdf.mjs`: it applies the KiCad
bridge's canonical leading-N convention plus an optional exact
`net_aliases.txt` to copied label records only. Seven renderer tests prove
explicit/implicit aliases, input immutability, sheet handling and fail-closed
behavior; all 57 rebuild-template tests still pass. The board source now uses
native polarized-capacitor symbols, identifies JLC's holder-only boundary and
the exact user-fitted 10 A/32 VDC/1 kA fuse, and explains both module open-pin
classes in their page headings.

MEASURED replay: the locked TSX producer completed in 7.969s. The resulting
ten-page, 303280-byte PDF displays only canonical 5VA/5VA_RAW/5VC_RAW names;
pages 3 and 9 visibly mark the positive lands of C22/C23. All 88-component
parity, 91 invariants, five early-design families, four topology rails, twelve
margin assertions, coded-value BOM and zero-error ERC gates passed. The driver
then stopped at five stale/defective review bindings, exactly at the intended
human checkpoint.

Reflection: safety-critical assembly facts must be visible in the artifact a
technician actually uses, and electrically equivalent net aliases must not
create a second human vocabulary. This extends IMP-002; automation can remove
deterministic alias drift, while an exact normal-scale human review remains
necessary for visibility and explanatory adequacy. Fresh zero-context topology
and readability reviews are in progress on the repaired bytes.

The first repaired-PDF pass confirmed those visible changes, then caught a
separate bound-input contradiction: the U2 dossier still named ADR-0007's
superseded 50nA IFB allowance while ADR-0009 and `power_tree.yaml` use the
500nA analytical screen. The dossier was corrected to the same explicitly
non-guaranteed 500nA/first-article obligation. Because the parts digest changed,
both in-progress reviews were discarded and fresh zero-context reviews were
commissioned; the seven generated checkpoint files remained byte-identical.

## 2026-08-12 — second readability correction: exact terminal alignment

The next exact-PDF lens found three presentation/dossier defects: C2/C5 text
was hidden behind BOOT/EN label plates, C22's dossier named protected `5VA`
instead of its exact pre-breaker `5VA_RAW` connection, and polarized C22/C23
were electrically connected but their drawn bodies stopped short of both
wires. The first two were repaired in source and dossier data. The third was
traced through the installed `circuit-to-svg` stack: its scaled-symbol matrix
translates before applying a non-unit scale, so the body terminal is displaced
from the authoritative schematic-port/trace coordinate.

The general repair lives in the exact-Circuit-JSON PDF renderer. It shifts
only copied display components/ports by the inverse transform error, leaves
traces and input bytes unchanged, independently recomputes endpoint residuals
and fails above 0.001 mm. Eight renderer fixtures pass, including exact
two-terminal coincidence and input immutability. On v4 it corrects exactly two
symbols—C22 and C23—with a maximum residual of 0.000168 mm; visual raster
inspection confirms both polarized bodies now join their rails. IMP-044
records the reusable lesson. A full source rebuild and fresh hash-bound human
reviews are still required; no earlier verdict is carried over.

## 2026-08-12 — regression preflight moved ahead of human review

The fresh rebuild completed normally in about 13 seconds (TSX 8.143 seconds)
and stopped at the intended review gate, but the subsequently launched full
repository suite found two source-governance defects: the Type-C delivery
`margin_basis`/`margin_evidence` pair had no declared reader, and ADR-0009's
new `<=14mOhm` cable acceptance bound had no executable bound declaration.
Both in-progress reviewers were interrupted before a verdict could be used.

The project and shared pipeline now fail these cases before TSX: bounded
source-governance stages run G-ORPHAN and M-BOUND ahead of the build stamp and
producer. E-MARGIN reads/reports the complete margin provenance pair and
rejects a partial one. The cable limit regenerates as 98mOhm minus the exact
55+4+25mOhm non-cable terms. Focused results are E-TOPO/E-MARGIN 54/54,
M-BOUND 13 cited / 37 owed with zero failures, and G-ORPHAN 502/502 with 424
proven readers and zero orphans. IMP-045 records the general process repair;
the full build and both reviews must restart from fresh bytes.

## 2026-08-12 — third readability correction: C4 identity

The next exact normal-scale readability review passed the repaired C22/C23
terminal attachment and the explicit C2/C5 placements, but rejected page 9:
the BOOT_C_C/BOOT_C_R/GND label cluster covered C4's reference designator.
Electrical connectivity and the value remained correct, so the change was
limited to an explicit C4 schematic coordinate; no net, value, footprint or
PCB placement changed. The prior topology review was interrupted before it
could certify bytes that were already known to be obsolete.

The replay completed in about 13.5 seconds, including the 8.370-second bounded
TSX stage. G-ORPHAN remained 502/502 with 424 proven readers, M-BOUND remained
13 cited / 37 owed, all 88 components and 91 invariants matched, and ERC again
reported zero errors. Page 9 now uses landscape fit and visibly separates C4,
its 10uF value, both terminals and ground label from the bootstrap cluster.
The checkpoint is 7/7 byte-identical and the driver stopped on the deliberately
stale/missing reviews. IMP-046 records the remaining opportunity to detect
reference/value ink occlusion before asking a human to inspect the PDF.

## 2026-08-12 — Type-C measurement-boundary backtrack

The replacement topology lens questioned the 25mOhm contact term before
finishing its verdict. Direct comparison with USB Type-C Release 2.0 section
3.7.8.1 exposed the larger problem: LLCR is measured across one
plug/receptacle mated contact and explicitly excludes internal paddle cards or
substrates, while the board-to-Pi path contains two mated pairs. The former
25mOhm contacts plus 14mOhm cable decomposition therefore had no stated
endpoints proving that both interfaces and both plug internals were counted.
Both active reviews were interrupted; neither may certify the obsolete rule
digest.

The 98mOhm total is retained only as a qualification target, now decomposed as
55mOhm TPS25810 maximum + 4mOhm board budget + one 39mOhm hot four-wire
complete-interconnect limit. That last measurement runs from J5 PCB-side
power lands to Pi load-plane sense points and includes both mated pairs, cable
plug internals/conductors/terminations, and the Pi receptacle/entry path. The
early-design gate now accepts either an honestly separate load-path
decomposition or one complete Type-C interconnect term, and rejects mixing the
two. IMP-047 records the general endpoint-coverage opportunity. A full source
rebuild and fresh reviews are required again.

## 2026-08-12 — fourth readability correction: visible C2 return

The next exact-PDF readability lens found that page 3 still drew C2 as though
both terminals returned to VIN. The netlist, 91 electrical invariants and ERC
were all correct: C2 pin 1 was VIN and pin 2 GND. The defect was the automatic
schematic route, which visually joined C2's right terminal to the VIN trunk
above C3 before reaching the separately labelled ground return.

An initial attempt to improve the drawing by moving both input capacitors was
rejected by the existing net-survival gate: the changed auto-layout merged
SW1's intentionally open pin 3 onto `5VA_RAW`. That failed at 44/45 surviving
labels before review or board generation. The accepted repair gives C2 its own
vertical VIN/GND labels at its pins and leaves C3 on the original automatic
route. The authoritative netlist again passes 45/45 label survival, 99/99 pin
mapping, 88/88 component parity, 91/91 invariants and zero-error ERC. At normal
page scale C2 now reads conventionally from VIN at the top to GND at the
bottom; C3 remains separately identifiable.

Reflection: source connectivity and human-visible connectivity are distinct
artifacts, and moving a schematic component can perturb more than that local
drawing in an automatic layout. Every readability edit therefore needs the
full net-survival/parity replay, while a future rendered-connectivity gate
should compare each two-terminal symbol's visible endpoint paths with its
electrical nets. IMP-048 records that generalization. The stale review was
kept as evidence of the caught defect; fresh exact-hash reviews are required.

The following all-page lens then applied the same principle beyond C2. It
found unlabeled local power loops at U1 pins 5/9/10 (`5VA_RAW`), U4-U6 pins
7/8/9 (`VBUSA1/2/3`) and U2 pins 1/16 (`VIN`). The netlist proved all five
groups correct, but the PDF required a reader to infer that each isolated loop
matched labels elsewhere. Explicit, pin-bound terminals now identify every
group. The first U1 terminal position crossed the nearby input-capacitor
ground returns and was discarded on visual inspection; the accepted label is
routed below the C2/C3 block and back to U1 pin 9 without a misleading
crossing. Pages 6-8 place each VBUS label directly at the corresponding
TPS2559 output pins, and page 9 places VIN directly at U2's joined input pins.
The project replay remains green through the intentional review stop.
