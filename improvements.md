# Future improvements

This is the repository-wide ledger for design-pipeline and process
improvements discovered while building boards. A project journal records what
happened during one stage; this file keeps the resulting work visible across
projects until it is implemented or deliberately rejected.

Status vocabulary: `proposed`, `accepted`, `implementing`, `completed`,
`rejected`. Entries are never deleted. A completed item must link to its
canonical implementation and executable tests; a rejected item must retain the
rationale.

## Index

| ID | Improvement | Status | Discovered |
|---|---|---|---|
| IMP-001 | Validate rule/config schemas before expensive TSX generation | implementing | USB Hub 3S v4, Stage 2 schematic |
| IMP-002 | Require early and exact rendered-schematic readability gates | implementing | USB Hub 3S v4, Stages 2 and 5 schematic |
| IMP-003 | Resolve every frozen footprint/library alias before board generation | proposed | USB Hub 3S v4, Stage 3 placement |
| IMP-004 | Emit a directional pad-side and critical-adjacency report before placement freeze | proposed | USB Hub 3S v4, Stage 3 placement |
| IMP-005 | Replay configured power/sense taps in the full rebuild driver | completed | USB Hub 3S v4, Stage 4 routing |
| IMP-006 | Make hole-to-copper screening tier-aware for every via emitter | completed | USB Hub 3S v4, Stage 4 routing |
| IMP-007 | Emit parity-safe real fabrication primitives for thermal via-in-pad | completed | USB Hub 3S v4, Stage 4 pre-route DRC |
| IMP-008 | Bind layout provenance to generator, footprint-library and tool inputs | proposed | USB Hub 3S v4, Stage 4 regeneration |
| IMP-009 | Refuse to promote a route race when every candidate is dirty | completed | USB Hub 3S v4, Stage 4 routing |
| IMP-010 | Require a fresh-reload, post-fill connectivity gate | completed | USB Hub 3S v4, Stage 4 full DRC |
| IMP-011 | Reject self-intersecting zone and keepout polygons before board generation | completed | USB Hub 3S v4, Stage 4 fill diagnosis |
| IMP-012 | Use the KiCad 10 layer-aware via-width API | completed | USB Hub 3S v4, Stage 4 routing |
| IMP-013 | Bound every quiet external producer with heartbeat and timeout | completed | USB Hub 3S v4, Stage 4 replay |
| IMP-014 | Keep verbose foreign-producer diagnostics out of the progress channel | proposed | USB Hub 3S v4, Stage 4 replay |
| IMP-015 | Bind topology reviews to a stable electrical netlist projection | implementing | USB Hub 3S v4, Stage 4 replay |
| IMP-016 | Exclude orchestration-only fields from the adopted-design-rules digest | completed | USB Hub 3S v4, Stages 4 and 8 replay |
| IMP-017 | Require RF review provenance only when `rf.enabled` is true | completed | USB Hub 3S v4, Stage 5 recovery audit |
| IMP-018 | Make effective-capacitance evidence a machine-readable schematic gate | completed | USB Hub 3S v4, Stage 5 topology review |
| IMP-019 | Separate fuse-holder identity from exact fuse-element coordination | proposed | USB Hub 3S v4, Stage 5 topology review |
| IMP-020 | Prefer functional schematic partitioning and pin grouping over broad absolute placement | implementing | USB Hub 3S v4, Stage 5 schematic repair |
| IMP-021 | Machine-check aggregate fault/current-limit envelopes | implementing | USB Hub 3S v4, Stage 5 topology review |
| IMP-022 | Validate authored board net/pin references against the exact netlist before human review | proposed | USB Hub 3S v4, Stage 5 schematic checkpoint |
| IMP-023 | Pin and provenance-bind TSX producer dependencies | implementing | USB Hub 3S v4, Stage 5 schematic rebuild |
| IMP-024 | Give the regression-suite runner per-suite heartbeats and hard deadlines | implementing | USB Hub 3S v4, Stage 5 verification |
| IMP-025 | Treat a mixed output bank and fitted CFF as one control-loop decision | proposed | USB Hub 3S v4, Stage 5 topology review |
| IMP-026 | Time-box fresh-context reviews and convert unresolved checks into findings | implementing | USB Hub 3S v4, Stage 5 topology re-review |
| IMP-027 | Lint standards-defined terminology and evidence identifiers before review | proposed | USB Hub 3S v4, Stage 5 topology re-review |
| IMP-028 | Validate part layout-precedent closure before hash-bound schematic review | completed | USB Hub 3S v4, Stage 6 placement entry |
| IMP-029 | Prefetch and provenance-bind JLC catalog models before A-RENDER | proposed | USB Hub 3S v4, Stage 6 placement review |
| IMP-030 | Make thermal-via transforms ownership-safe and run exact placement DRC | implementing | USB Hub 3S v4, Stage 6 placement review |
| IMP-031 | Add a published-legibility silk class for operational markings | proposed | USB Hub 3S v4, Stage 6 placement render review |
| IMP-032 | Promote the reviewed schematic at its stage boundary | completed | USB Hub 3S v4, Stage 6 placement replay |
| IMP-033 | Require machine-checked evidence for per-reference P-OUT exceptions | proposed | USB Hub 3S v4, Stage 6 edge-connector review |
| IMP-034 | Validate deterministic route copper against exact placement before review | proposed | USB Hub 3S v4, Stage 7 route preparation |
| IMP-035 | Prove pour-service coverage for every net excluded from routing | proposed | USB Hub 3S v4, Stage 7 authoritative DRC |
| IMP-036 | Let layout sealing resume an exact reviewed schematic checkpoint | completed | USB Hub 3S v4, Stage 8 layout seal |
| IMP-037 | Keep track-free review checks typed to the pre-route artifact | completed | USB Hub 3S v4, Stage 8 layout seal |
| IMP-038 | Make ampacity audit a canonical stage gate | completed | USB Hub 3S v4, routed review |
| IMP-039 | Select via treatment per process family, not board-wide | completed | USB Hub 3S v4, manufacturing review |
| IMP-040 | Validate promoted-route compatibility before placement review | completed | USB Hub 3S v4, corrected-process replay |
| IMP-041 | Grade series-transition via ampacity non-vacuously | completed | USB Hub 3S v4, routed review |
| IMP-042 | Bind fresh pin review to an exact local datasheet digest | completed | USB Hub 3S v4, routed pin review |
| IMP-043 | Propagate typical-only and accessory-qualified bounds into release blockers | implementing | USB Hub 3S v4, routed topology review |
| IMP-044 | Prove rendered symbol terminals coincide with authoritative trace endpoints | completed | USB Hub 3S v4, schematic readability re-review |
| IMP-045 | Run repository schema and bound-provenance ratchets before producer or reviewer spend | completed | USB Hub 3S v4, schematic regression replay |
| IMP-046 | Preflight rendered reference/value occlusion before human review | proposed | USB Hub 3S v4, schematic readability review |
| IMP-047 | Give IR-budget terms non-overlapping measurement endpoints | implementing | USB Hub 3S v4, Type-C topology review |
| IMP-048 | Compare visible schematic paths with authoritative electrical nets | proposed | USB Hub 3S v4, schematic readability review |
| IMP-049 | Bound independent-review briefs and enforce closure deadlines | implementing | USB Hub 3S v4, exact placement review |
| IMP-050 | Prove fresh generated outputs instead of trusting exit zero | implementing | USB Hub 3S v4, routed-review export |
| IMP-051 | Give long external stages progress and bounded retry budgets | implementing | USB Hub 3S v4, JLC digital-twin fetch |
| IMP-052 | Preflight mutable catalog clients and distinguish compatibility from throttling | implementing | USB Hub 3S v4, JLC digital-twin fetch |
| IMP-053 | Prefer explicit catalog facts over MPN-shape heuristics | completed | USB Hub 3S v4, C23 source substitution |
| IMP-054 | Persist the final adjudicated state in generated reports | completed | USB Hub 3S v4, JLC digital twin |
| IMP-055 | Register exact 3D model attachment geometry before placement freeze | implementing | USB Hub 3S v4 and Pluto RX2 8-way v5 twins |
| IMP-056 | Separate automated and manual population denominators | completed | USB Hub 3S v4, release audit |
| IMP-057 | Validate relocated release archives in their own dependency context | implementing | USB Hub 3S v4, release staging |
| IMP-058 | Treat multi-format evidence as one atomic result | proposed | USB Hub 3S v4, release staging |
| IMP-059 | Preflight publication review identity before immutable seal | implementing | USB Hub 3S v4, publication gate |
| IMP-060 | Replay a release's declared freshness mode at publication | completed | USB Hub 3S v4, docs-only publication correction |
| IMP-061 | Close exact-code manufacturing readiness before part freeze | proposed | USB Hub 3S v4, nine-hour pipeline retrospective |
| IMP-062 | Provide one transactional primitive for generated artifact bundles | implementing | USB Hub 3S v4, nine-hour pipeline retrospective |
| IMP-063 | Rehearse the complete release and publication-internal contract before seal | proposed | USB Hub 3S v4, nine-hour pipeline retrospective |
| IMP-064 | Pair early warning gates with late authoritative rechecks | implementing | USB Hub 3S v4, nine-hour pipeline retrospective |
| IMP-065 | Measure pipeline critical path by work class and order cheap gates first | implementing | USB Hub 3S v4, nine-hour pipeline retrospective |
| IMP-066 | Confirm broad-phase geometry findings with native transformed polygons | completed | Pluto RX2 8-way legacy canary replay |
| IMP-067 | Prevent executable example values from entering new-project scaffolds | proposed | Pluto RX2 8-way v5 commission |
| IMP-068 | Coordinate protection before freezing downstream voltage ratings | proposed | Pluto RX2 8-way v5 exact-parts stage |
| IMP-069 | Derive stage readiness from canonical gate receipts | implementing | Pluto RX2 8-way v5 pre-schematic audit |
| IMP-070 | Mechanically scope clean-room filesystem discovery | proposed | Pluto RX2 8-way v5 clean-room audit |
| IMP-071 | Derive observable timing from executable state schedules | implementing | Pluto RX2 8-way v5 control-protocol audit |
| IMP-072 | Classify committed binary evidence in the canonical scaffold | proposed | Pluto RX2 8-way v5 checkpoint commit |
| IMP-073 | Grade human symbol pin functions, including unused pins | proposed | Pluto RX2 8-way v5 schematic readability review |
| IMP-074 | Type ADR gate applicability instead of inferring it from prose | proposed | Pluto RX2 8-way v5 schematic gate |
| IMP-075 | Bind mechanical dimensions to exact document identity and feature role | proposed | Pluto RX2 8-way v5 connector review |
| IMP-076 | Reconcile exact package geometry and logical pin identity in the first-board preflight | proposed | Pluto RX2 8-way v5 placement grind |
| IMP-077 | Reconcile footprint and symbol metadata before schematic-parity DRC | proposed | Pluto RX2 8-way v5 keyed-SWD placement |
| IMP-078 | Run the source-resolvable tier/routing preflight before schematic and placement spend | proposed | Pluto RX2 8-way v5 keyed-SWD placement |
| IMP-079 | Derive compact floorplans from topology and operational connector envelopes before placement freeze | proposed | Pluto RX2 8-way v5 compact placement |
| IMP-080 | Emit and measure RF fences from routed centrelines, not a rectangular lattice declaration | completed | Pluto RX2 8-way v5 route preparation |
| IMP-081 | Seed route-prep UUID generation so identical source yields byte-identical r0 | completed | Pluto RX2 8-way v5 route preparation |
| IMP-082 | Require executable budgets for datasheet `short`/`close` layout obligations before placement review | proposed | Pluto RX2 8-way v5 pre-route placement renewal |
| IMP-083 | Make no-via-in-pad intent executable at every routing wave | completed | Pluto RX2 8-way v5 first control/power route |
| IMP-084 | Make geometry admission consume pad-local copper and mask rules | completed | Pluto RX2 8-way v5 first post-stitch DRC |
| IMP-085 | Normalize overlap-only track/via joints before deleting barrels | completed | Pluto RX2 8-way v5 route cleanup |
| IMP-086 | Run external mating-fact provenance before PCB generation | proposed | Pluto RX2 8-way v5 post-stitch gate |
| IMP-087 | Grade rerunnable density gates against realized saved geometry | completed | Pluto RX2 8-way v5 RF-fence rerun |
| IMP-088 | Seed deterministic identities across import and stitch, not only route prep | proposed | Pluto RX2 8-way v5 layout-seal entry |
| IMP-089 | Treat same-net via-in-pad as a fabrication process, not a DRC clearance | completed | Pluto RX2 8-way v5 final layout red team |
| IMP-090 | Bind review freshness to declared stage dependencies, not monolithic source bags | proposed | Pluto RX2 8-way v5 corrected layout seal |
| IMP-091 | Freeze executable assembly-process ownership before placement export | proposed | Pluto RX2 8-way v5 layout-seal entry |
| IMP-092 | Make provenance source discovery honor declared source boundaries and ignore policy | proposed | Pluto RX2 8-way v5 layout seal |
| IMP-093 | Compare repeated-pad catalog lands as geometry, not merged labels | implementing | Pluto RX2 8-way v5 final JLC twin |
| IMP-094 | Bind review contracts to the exporter artifact index | proposed | Pluto RX2 8-way v5 fabrication entry |
| IMP-095 | Dispatch exact-artifact reviews from a machine-written envelope | proposed | Pluto RX2 8-way v5 RF fabrication review |
| IMP-096 | Derive release PDF pages from populated sides and document purpose | proposed | Pluto RX2 8-way v5 release-asset export |

## IMP-001 — pre-build rule/config schema validation

- status: implementing
- observed: `projects/usb-hub-3s-v4/01_docs/journal/03_schematic.md`,
  2026-08-11 08:34 entry
- evidence: A malformed `label_survival` row was knowable from YAML alone, but
  was not rejected until after an approximately 25-second TSX build/render.
  Existing `tsx_preflight.py` runs before generation but currently grades
  alphanumeric pad mapping, not all adopted rule schemas.
- additional evidence: the Stage 4 full replay completed routing and DRC before
  `project_state.py` found that a gate marked `pass` had no evidence list. The
  findings ledger is source-only and could have failed before TSX generation.
- intended landing point: a cheap canonical pre-build schema gate, invoked by
  both PCB rebuild templates before `build_provenance.py stamp` and before any
  `tsci build`. It should validate every rule block whose schema does not depend
  on generated circuit/netlist/board bytes, including `label_survival`.
- completion evidence required: clean and known-bad executable fixtures; both
  canonical rebuild templates prove the gate precedes TSX generation; the USB
  Hub v4 rule set passes; the original malformed label-survival shape fails
  without invoking the producer.
- implementation progress: the full-build template now runs
  `net_label_survival.py --schema-only` and the source-only portion of
  `early_design_check.py` before the provenance stamp and `tsci build`;
  executable ordering and malformed-label fixtures pass in
  `tests/t1_net_label_survival.py` and `tests/t1_rebuild_templates.py`. The
  broader all-rule schema inventory and source-only findings-ledger validation
  remain outstanding, so this item is not complete.
- follow-up evidence: Pluto RX2 8-way v5 parsed 25/25 YAML files and passed the
  selected package, topology, netclass and surge checks, yet four canonical
  readers disagreed at the same pre-schematic boundary on 2026-08-13:
  `electrical_invariants.py` rejected the prose-only invariant shape;
  `rf_contract_check.py` rejected `rf.ports[0]` without a `nets` list;
  `assembly_coverage.py --emit-manifest-line` raised an `AttributeError` on
  scalar `not_assembled` rows instead of issuing a bounded schema failure; and
  `net_label_survival.py --schema-only` reported PASS while interpreting zero
  of the thirteen intended pin-map rows. Parse success and a zero-row schema
  pass are both M-COVER failures when authored declarations were expected.
- completion evidence extension: the canonical pre-build command must invoke
  every source-readable rule-family reader, require an expected non-zero
  denominator when that family is authored, convert malformed input to a
  concise failure rather than a traceback, and refuse TSX when any family is
  ungraded. The four v5 shapes above become executable known-bads.
- implementation progress: the electrical-invariant reader now has an
  explicit source-only mode and configurable non-zero minimum; label survival
  rejects unknown keys and empty pin-map declarations; assembly projection
  shape failures are bounded diagnostics rather than tracebacks; and the RF
  reader accepts an explicitly evidenced `pending_solver` cross-section before
  PCB work while refusing it at PCB/fab review. The canonical full-build
  template invokes the new source checks before TSX. Focused clean/known-bad
  regressions for these readers and control timing pass 108 tests. Assembly,
  control-protocol and RF now have canonical key/reader tables; the repository
  ratchet reports 604/604 declared keys, 508 proven, zero orphan and zero
  unread. `mates.yaml`, `twin_adjudications.yaml`, a complete stage registry
  and preflight of the findings ledger remain open.
- history:
  - 2026-08-11 — proposed and promoted from the schematic journal.
  - 2026-08-11 — implementation started with pre-producer label-survival and
    electrical schema gates; V4 passed before its 9.1-second TSX invocation.
  - 2026-08-13 — v5's four source-reader failures were converted into bounded,
    non-vacuous pre-TSX checks and executable regression fixtures.

## IMP-003 — pre-generation footprint resolution

- status: implementing
- observed: `projects/usb-hub-3s-v4/01_docs/journal/placement.md`,
  2026-08-11 Stage 3 closeout
- evidence: The first board-generation attempt stopped immediately because the
  frozen schematic named `Package_TO_SOT_SMD:SOT-9X3`, while the installed
  KiCad library now names the exact TI land `Texas_DRT-3`. The local project
  alias was then vendored and generation completed. The failure was cheap and
  loud, but the mismatch was knowable before starting the board producer.
- intended landing point: extend the pre-build/pre-board schema gate so every
  manifest footprint resolves through the project `fp-lib-table`, including
  frozen aliases, before invoking either TSX or PCB generation. The resolver
  must report the unresolved refdes, requested library identifier, and the
  exact library search order.
- completion evidence required: fixtures for a missing library, missing
  footprint, stale renamed alias and valid project-local alias; the canonical
  pipeline proves the resolver runs before the producer; USB Hub v4 passes
  without relying on the generator to discover the problem.
- history: 2026-08-11 — proposed after the Stage 3 first-generation stop.

## IMP-004 — directional pad-side and adjacency report

- status: proposed
- observed: `projects/usb-hub-3s-v4/01_docs/journal/placement.md`,
  2026-08-11 Stage 3 closeout
- evidence: Collision, outline, capacity and pad-separation gates all accepted
  the first legal placement. A direct physical-pad report then showed the two
  power modules rotated with VIN and VOUT on the opposite sides from the
  authored comment, and the human render exposed BOOT/RT/feedback parts that
  were legally separated but electrically too remote. The corrected board
  measures U1 BOOT 2.70 mm, RT 1.99 mm and nearest FB 2.06 mm; U2 VIN bypasses
  are 1.60 mm and RT is 2.07 mm from their actual lands.
- intended landing point: before placement review, emit a small report from
  the exact board listing the global coordinates and side/order of named
  directional pads plus the minimum pad-to-pad distances for every structured
  `layout:` adjacency obligation. Comments such as “VIN west” must be checked
  against board bytes, never accepted as evidence.
- completion evidence required: rotated/mirrored and far-but-nonoverlapping
  known-bad fixtures; a clean report for USB Hub v4; the canonical placement
  stage runs it before render review and before routing.
- history: 2026-08-11 — proposed after two defects escaped geometry-only gates.

## IMP-002 — early and exact rendered-schematic readability gates

- status: implementing
- observed: `projects/usb-hub-3s-v4/01_docs/journal/03_schematic.md`, the Stage
  5 exact-replay backtrack, and the rejected USB Hub v4 schematic-render
  review.
- evidence: Connectivity, parity, ERC, freshness and source-level section
  metadata all passed, but an independent review of the delivered PDF found
  approximately 2.1--2.5 pt native text, weak functional grouping, no visible
  block headings or important active-part identities, excessive label hopping
  through critical circuits, unexplained intentional NCs, and poor page use.
  The source described sections, but the rendered artifact did not communicate
  them. Because the first explicit picture review occurred after detailed
  electrical and PCB work, a cheap presentation defect caused a late
  backtrack.
- required process:
  1. Render a small "first picture" as soon as the functional schematic
     skeleton exists. Require a human-readable left-to-right flow, visible
     functional headings, local critical support circuits, explained NCs and
     useful page occupancy before detailed sourcing or PCB work begins.
  2. At schematic freeze, repeat the review against the exact delivered PDF
     and bind the closed verdict to the PDF SHA-256, canonical electrical
     netlist, adopted design rules and exact parts manifest.
  3. Review the artifact itself at normal viewing size; source metadata and a
     zoom-readable drawing are not substitutes.
- implement now: keep the hash-bound `schematic_render` review as a mandatory
  schematic-phase prerequisite to placement, repair USB Hub v4 until that
  independent review is SOUND, and make the first-picture checkpoint explicit
  in the PCB design/review contract. This is required now because the current
  v4 artifact has already failed the gate; deferring it would knowingly carry
  an unreadable schematic into release.
- implement later: add deterministic, cheap render heuristics for minimum text
  size, drawing bounds/page occupancy, required headings and identities, and
  unexplained NCs; add a reusable skeleton-render template and cached stage
  telemetry. These checks reduce review load but do not replace the human
  verdict, and they do not need to block completion of the present electrical
  design once its actual PDF is readable.
- completion evidence required: canonical review schema and checker; the PCB
  design instructions and `08_reviews` contract name both checkpoints; clean
  and stale/missing/defective fixtures; a future project proves the
  first-picture gate runs before detailed generation; and the USB Hub v4 PDF
  receives an explicit SOUND verdict bound to its exact SHA-256 and electrical
  inputs.
- partial implementation: `skills/kicad-pcb/scripts/render_schematic_pdf.mjs`
  renders each declared sheet independently from the exact Circuit JSON;
  it now applies the same leading-`N` digit convention and explicit
  `net_aliases.txt` mapping as the KiCad bridge to display canonical net names
  without mutating Circuit JSON. USB Hub v4's exact review also proved that
  polarity, user-fitted safety consumables and manufacturer-required open-pin
  dispositions are part of schematic readability, not merely BOM/dossier
  facts; the repaired source renders all three visibly. Alias behavior and
  exact-input immutability have executable coverage in
  `tests/t1_schematic_render.py`;
  `skills/pcb-design/scripts/pre_route_review_check.py` and the USB Hub v4
  `03_src/route.yaml` require independent topology and `schematic_render`
  reviews bound to exact schematic/electrical inputs; the PCB-design and
  `08_reviews` contracts now require the earlier first-picture checkpoint.
  `stage_checkpoint.py` plus `rebuild_all.sh
  --resume-after-schematic-review` preserve the reviewed bytes across the
  deliberate pause instead of rerunning nondeterministic TSX. Executable
  coverage is in `tests/t1_schematic_render.py`,
  `tests/t1_pre_route_review.py`, `tests/t1_stage_checkpoint.py`, and
  `tests/t1_rebuild_templates.py`.
- history:
  - 2026-08-11 — proposed and promoted from the schematic journal.
  - 2026-08-11 — expanded after the first exact-artifact review rejected USB
    Hub v4; split into a mandatory present repair/contract change and later
    automated presentation heuristics.
  - 2026-08-11 — implemented the exact multi-sheet renderer, explicit
    first-picture contract, hash-bound freeze review, and content-preserving
    review-pause resume; remains `implementing` until USB Hub v4 receives the
    exact SOUND readability verdict.
  - 2026-08-12 — the next exact-PDF review found authoring-only net aliases,
    invisible C22/C23 polarity, an unnamed user-fitted fuse element and
    unexplained module SW/VCC opens. Canonical-name rendering was repaired in
    the shared renderer/template; the board source now exposes the remaining
    assembly and intentional-open facts before a fresh review.

## IMP-005 — deterministic tap replay in the full rebuild

- status: completed
- observed: USB Hub 3S v4 Stage 4 routing preflight, 2026-08-11
- evidence: `route.yaml` configured five explicit 5VA F.Cu-to-B.Cu bonds, and
  both the project contract and `rebuild_reuse.sh` require the standard `taps`
  command between route import and stitch. The canonical `rebuild_all.sh`
  omitted that command, so a full rebuild would silently skip source-owned
  copper that an iterative rebuild correctly replayed.
- intended landing point: invoke `route_and_stitch_generic.py taps` after
  promoted-chain import and before stitch/fill in the canonical full driver;
  keep project copies aligned.
- completion evidence required: an executable template test requires
  `import < taps < stitch` in both full and reuse drivers; USB Hub v4 completes
  the same route from its source contract under the full ordering.
- implementation: `skills/pcb-design/templates/03_src/rebuild_all.sh` and the
  USB Hub v4 copy now invoke `taps` strictly between import and stitch.
  `tests/t1_rebuild_templates.py` pins the full and reuse order.
- history: 2026-08-11 — implementation started after comparing the v4 driver,
  its contract, the reuse driver and USB Hub v3; completed in Stage 4.

## IMP-006 — tier-aware hole-to-copper screening for every via emitter

- status: completed
- observed: USB Hub 3S v4 Stage 4 `tier_preflight.py`, 2026-08-11
- evidence: the board declares the JLCPCB four-layer advanced 0.25 mm
  hole-to-copper floor. Configured stitch tiers carry the correct 0.255 mm
  collision-screening value, but the generic `taps` path still calls
  `via_site_ok` with its 0.205 mm default and offers no project knob. The A*
  fallback can already inherit a matching stitch-tier value, but the preflight
  currently reports it as knobless too. An under-strict screen is caught by
  final DRC, but only after copper generation; an over-strict default can
  create a false routing wall.
- intended landing point: every via emitter resolves one effective
  `hole_to_copper` value from an explicit pin or the matching fab-tier entry,
  passes it to every site check and A* layer change, and reports that resolved
  value accurately in `tier_preflight.py`.
- completion evidence required: clean tests for taps and A* on a non-default
  hole floor, known-bad under-floor/false-wall fixtures, and zero PF-HTC
  warnings on USB Hub v4 without relying on final DRC.
- implementation: `route_and_stitch_generic.py` forwards the configured
  value through tap via-site checks and verified A* layer changes;
  `tier_preflight.py` resolves and grades both paths. Clean/non-default and
  under-floor fixtures live in `tests/t2_route_stitch.py` and
  `tests/t2_tier_preflight.py`. USB Hub v4 preflight is 0 FAIL / 0 WARN at
  0.255 mm versus the declared 0.25 mm floor.
- history: 2026-08-11 — proposed and completed during the bounded Stage 4
  preflight loop.

## IMP-007 — parity-safe fabrication primitives for thermal via-in-pad

- status: completed
- observed: USB Hub 3S v4 Stage 4 pre-route DRC, 2026-08-11
- evidence: 40 exposed-land thermal holes were represented by duplicated
  footprint PTH pads carrying KiCad's `pad_prop_heatsink` marker. They are
  electrically valid, but JLC's official via-covering guidance distinguishes
  vias from component pad holes and says via finishing does not apply to pads.
  A Gerber/fab order must not rely on the fabricator reinterpreting the
  primitive. The same cheap DRC also exposed the 0.20/0.30 mm board-floor
  contradiction before KRT ran.
- intended landing point: explicit, config-gated board-level via declarations
  resolve named footprint pads, inherit their live nets and preserve the
  library-linked footprint identity used by schematic parity. The legacy
  marker-promotion path remains supported but fails closed on an empty match.
- implementation: `generate_board_generic.py` emits 40 explicit true vias for
  U1-U6 while retaining all six library FPIDs. `tests/t1_generate_board.py`
  covers count/geometry, unknown refs and legacy empty matches. USB Hub v4's
  refill/full-severity pre-route DRC has no drill-floor or schematic-parity
  finding; its manufacturing contract still requires resin fill and copper cap.
- history: 2026-08-11 — implemented after the pre-route quick check prevented
  routing over a fabrication-primitive mismatch.

## IMP-008 — complete generated-layout provenance inputs

- status: proposed
- observed: USB Hub 3S v4 Stage 4 regeneration, 2026-08-11
- evidence: the board/review hashes bind the generated artifact and authored
  rule bytes, but a generator implementation or vendored footprint change can
  alter board bytes without appearing as a named producer input in the pending
  layout provenance record.
- intended landing point: bind the board generator, resolved footprint files,
  project library tables, KiCad version and any post-generator transformer to
  the layout provenance record, with a report explaining which input changed.
- completion evidence required: clean rebuild plus stale generator/library/tool
  fixtures that invalidate provenance before routing.
- history: 2026-08-11 — proposed during parity-safe footprint regeneration.

## IMP-009 — fail-closed route-race promotion

- status: completed
- observed: USB Hub 3S v4 Stage 4 route race, 2026-08-11
- evidence: an early race returned success and selected the least-bad candidate
  even though every candidate's cheap verdict still contained routed-net opens.
  The failure then surfaced only after import, taps, fill and full DRC.
- implementation: `_cmd_route_race` now considers only `CLEAN` candidates,
  clears any stale `FINAL` marker before a run, records an all-dirty
  `race_log.json` with `chosen: null`, and exits nonzero. Clean selection,
  all-failed and all-dirty fixtures live in `tests/t2_route_stitch.py`.
- history: 2026-08-11 — completed before rerunning USB Hub v4's route race.

## IMP-010 — fresh post-fill connectivity gate

- status: completed
- observed: USB Hub 3S v4 Stage 4 full DRC, 2026-08-11
- evidence: an in-process stitch gate reported clean while a fresh authoritative
  KiCad CLI refill found 35 unconnected items and one dangling via. Fill state,
  island healing and connectivity must cross the same serialization boundary as
  the release DRC.
- intended landing point: force save/fresh reload after fill, heal split same-net
  islands, prune stitch-created dangling copper, then gate; retain full CLI DRC
  with refill and schematic parity as the authority.
- completion evidence required: USB Hub v4 reaches fresh 0/0/0 and a fixture
  proves a stale in-memory connectivity result cannot pass.
- implementation: `route_and_stitch_generic.py` provides an unconditional
  `fresh_reload` process barrier, collision-checked `heal_islands`, and
  ownership-scoped `prune_stitch_dangling`; USB Hub v4 runs all three before
  `gate` and then independently runs KiCad CLI DRC with refill and schematic
  parity. `tests/t2_route_stitch.py` proves the fresh barrier always re-execs,
  split same-net pours heal and re-verify, a dangling emitted via is pruned,
  and an unbridgeable split is still found by the independent DRC backstop.
- history: 2026-08-11 — completed after USB Hub v4 reproduced the stale
  in-memory result and then reached serialized 0/0/0.

## IMP-011 — simple-polygon validation before generation

- status: completed
- observed: USB Hub 3S v4 Stage 4 fill diagnosis, 2026-08-11
- evidence: the authored VIN polygon crossed/overlapped itself. KiCad accepted
  the zone but filled only its downstream tail, silently omitting the protected
  input region even on the segment-free board.
- implementation: `generate_board_generic.py` rejects repeated closure points,
  zero-length edges, zero area and non-adjacent crossing/collinear-overlapping
  edges for every zone and keepout. `tests/t1_generate_board.py` carries the
  original self-intersection as a known-bad fixture.
- history: 2026-08-11 — completed while tracing the missing VIN fill.

## IMP-012 — KiCad 10 layer-aware via-width API

- status: completed
- observed: USB Hub 3S v4 Stage 4 routing, 2026-08-11
- evidence: calling the legacy no-argument via `GetWidth()` under KiCad 10
  emitted assertion noise during otherwise bounded search loops, obscuring real
  progress and making the pipeline appear stuck.
- implementation: the importer/router now obtains via width through the
  layer-aware API. Focused route/import tests run without the assertion flood.
- history: 2026-08-11 — completed during Stage 4 diagnostics.

## IMP-013 — bounded external-producer progress

- status: completed
- observed: `projects/usb-hub-3s-v4/01_docs/journal/routing.md`,
  2026-08-11 12:17 entry
- evidence: a from-source replay appeared to stop at `Generating circuit
  JSON...` while the host was under global OOM and I/O pressure. The process
  was still alive and ultimately continued, but the direct `tsci build` call
  had no pipeline heartbeat, state file or process-group deadline. Routing and
  DRC already used the bounded runner, so progress observability depended on
  which child happened to be active.
- implementation: the canonical full rebuild template and USB Hub v4 invoke
  `tsci build` as the `tscircuit_build` stage through `pcb_flow.py`; the v4
  config budgets and times out at 60 seconds and emits a heartbeat every 10
  seconds. The canonical route template now names a 60-second budget and a
  conservative 180-second starting deadline for projects without measured
  history. `tests/t1_rebuild_templates.py` rejects a return to the former
  unbounded direct call.
- history: 2026-08-11 — completed during Stage 4 deterministic replay.

## IMP-014 — bounded console detail for foreign-producer diagnostics

- status: proposed
- observed: USB Hub 3S v4 Stage 4 from-source replay, 2026-08-11
- evidence: `tsci build` emits hundreds of unnamed-trace and supplier-model
  advisories before the repository's diagnostic gate prints the useful
  classified summary (`367 advisory`, zero embedded errors). The volume hides
  stage transitions and makes a healthy build hard to scan even though the
  complete detail remains useful for diagnosis.
- intended landing point: retain the complete producer stream in a timestamped
  build log while the interactive channel prints stage start/heartbeat/end,
  hard errors and a warning-class summary. Failure must automatically include
  a bounded tail and the log path; suppression may never discard evidence.
- completion evidence required: clean/chatty/failing producer fixtures prove
  bounded console output, lossless retained logs and visible failure context.
- history: 2026-08-11 — proposed after the first full routed replay.
- additional evidence: the 2026-08-12 exact placement resume completed all
  useful machine work in seconds, but its live stream repeated KiCad's empty
  enum assertion three times at nearly every pcbnew load, repeated image-
  handler registration diagnostics during prep/review checks, and printed ten
  non-blocking silk-ownership lines. The same class also affects KiCad render
  progress. The retained log should preserve every line, while the live view
  groups known warning signatures by class/count and keeps stage timing,
  heartbeat, failure context and artifact paths prominent.

## IMP-015 — stable electrical topology-review digest

- status: implementing
- observed: USB Hub 3S v4 Stage 4 from-source replay, 2026-08-11
- evidence: a fresh TSX-to-KiCad reconstruction invalidated the pre-route
  normalized-netlist hash while all independent semantic gates and a direct
  60-net/270-node traversal reported the same electrical graph. The current
  digest deliberately normalizes only export time and instance UUIDs, leaving
  other non-electrical serialization/presentation churn capable of forcing a
  manual re-review.
- intended landing point: parse KiCad's legacy netlist and hash a canonical
  projection containing every component identity, value, footprint, property,
  net name, physical pin identity and no-connect, with unordered collections
  sorted and presentation paths/timestamps excluded. Keep the raw-byte hash in
  the review for forensic provenance.
- completion evidence required: permutations of ordering, UUIDs, timestamps
  and source paths retain one semantic digest; a one-pin, value, footprint,
  property, net or no-connect change produces a different digest; existing
  reviewed boards migrate through explicit fresh reviews.
- implementation progress: `pre_route_review_check.py` now normalizes the
  export date, instance UUIDs, schematic source path, generated Sheetname/
  Sheetfile properties and project-derived netclass labels. This makes full
  and pinned exports of the byte-identical v4 schematic agree while a
  component-value change remains a known-bad failure in
  `tests/t1_pre_route_review.py`. Collection-order canonicalization and the
  complete mutation matrix remain outstanding, so this item is not complete.
- additional evidence: the final v4 full-source proof produced a new
  normalized digest (`2bb964f6...` versus pinned `be5c7573...`) and correctly
  stopped for review, even though an independent structural parse found exact
  equality over all 88 `(ref, footprint, value)` records, all 324 physical
  pin-to-net identities and all 69 net names. This isolates the remaining
  false invalidation to collection/serialization ordering and makes sorted
  structural projection the next implementation step, not a speculative
  optimization.
- history: 2026-08-11 — implementation started after the Stage 4 deterministic
  replay proved the full/reuse contradiction.

## IMP-016 — adopted-rule digest should not include orchestration metadata

- status: completed
- observed: USB Hub 3S v4 Stage 4 replay, 2026-08-11
- evidence: adding only `flow.budgets_s.tscircuit_build` and
  `flow.timeouts_s.tscircuit_build` invalidated all four hash-bound electrical,
  pin, layout and render reviews because `design_rules_digest()` hashes the
  whole `route.yaml`. The review files had to be rebound even though board,
  copper, parts and every design/fabrication rule were unchanged.
- additional evidence: adding U9's placement-local taper rule and moving J5's
  deterministic CC seed coordinates invalidated both schematic reviews even
  though the normalized electrical netlist and delivered schematic PDF did
  not change. The fail-closed stop was correct under the present contract, but
  it forced electrical/readability review work for a layout-only mutation.
- intended landing point: hash a versioned canonical projection of adopted
  electrical, fabrication, placement and routing semantics. Exclude progress,
  timeout, budget, path, owner, blocker and other orchestration-only fields;
  retain a separate raw config/provenance hash for forensic replay.
- completion evidence required: timeout/heartbeat/log-path mutations leave the
  adopted-rules digest stable; width, clearance, via, layer, route-wave, tap,
  zone, placement and fabrication mutations invalidate it; existing projects
  migrate via fresh reviews.
- implementation: `pre_route_review_check.py` now hashes canonical parsed YAML
  under a versioned `design-v1` projection. All `03_src/rules/*.yaml` and the
  design-bearing keepout, seed, wave, critical-route, tap and stitch sections
  remain bound. Project paths, the whole `flow` block, intermediate/output
  filenames, KRT checkout/import selection and race count are excluded as
  orchestration. `tests/t1_pre_route_review.py` independently reproduces the
  projection and proves both process-only stability and deterministic-copper
  invalidation; the fast-flow reference defines the boundary.
- history: 2026-08-11 — proposed after bounded TSX execution caused a vacuous
  four-review rebind.
- history: 2026-08-12 — implemented when the new checkpoint-resume argument
  reproduced the same false invalidation immediately before v4 layout seal.

## IMP-017 — conditional RF review provenance

- status: completed
- observed: USB Hub 3S v4 Stage 5 recovery-path audit, 2026-08-11
- evidence: `reviewed_commit_provenance()` requires exact SOUND RF schematic
  and PCB review files even when `03_src/rules/rf.yaml` explicitly declares
  `rf.enabled: false`. The ordinary RF contract correctly supports a negative
  applicability decision, but the immutable-commit recovery path hard-codes
  six review lenses and contradicts it.
- intended landing point: always require pin, render, topology and layout
  review provenance; add the two RF review witnesses only when the parsed RF
  contract enables RF. Malformed or missing applicability must fail closed.
- implementation: `pcb_flow.py` parses the schema-1 RF applicability contract
  for reviewed-commit provenance. Non-RF boards require the four general
  review lenses; RF-enabled boards additionally require both exact RF reviews;
  missing/malformed applicability fails closed. `tests/t2_pcb_flow.py` covers
  both branches and the complete 34-test file passes.
- history: 2026-08-11 — implemented and regression-tested during the v4 Stage
  5 backtrack.

## IMP-018 — effective-capacitance evidence gate

- status: completed
- observed: USB Hub 3S v4 Stage 5 independent topology review, 2026-08-11
- evidence: U1 named three 47uF MLCCs and TPS25810 shared another three, so
  nameplate totals appeared to clear 75uF and 120uF requirements. The exact HRE
  manufacturer sheet has no DC-bias curve; none of the existing semantic gates
  rejected crediting unproved nameplate capacitance at 5V bias.
- intended landing point: a machine-readable capacitance obligation names the
  required effective minimum, operating bias, temperature and stability/ESR
  boundary. Each credited capacitor supplies an exact tolerance/DC-bias curve
  or an independent guaranteed minimum; uncredited high-frequency bypass parts
  remain allowed but cannot satisfy the sum.
- implementation: `early_design_check.py` now grades `effective_capacitance_banks`
  from exact component refs and identities. Every contributor must declare
  initial negative tolerance, DC-bias, temperature and lifecycle derating;
  accepted dielectric types and requirement evidence are mandatory. The terms
  are applied multiplicatively and a deficient bank fails before placement.
  `tests/t1_early_design.py` contains clean, DC-bias-shortfall and omitted-term
  fixtures. USB Hub v4 passes at 80.784/75uF for U1, 40.392/30uF for U2 and
  155.592/120uF for the TPS25810 cold-socket bank.
- history: 2026-08-11 — proposed after the independent review rejected
  nameplate MLCC credit; completed during the Stage 5 backtrack.

## IMP-019 — fuse element and coordination contract

- status: proposed
- observed: USB Hub 3S v4 Stage 5 independent topology review, 2026-08-11
- evidence: the schematic and BOM exactly identified the Keystone 3568 holder
  and said “fit 10A MINI fuse”, but did not identify the replaceable fuse whose
  voltage, interrupt, time-current, I2t and ambient-derating properties carry
  the protection claim.
- intended landing point: model holder and fuse element as distinct identities.
  A user-fit/consigned element must name its exact MPN, ratings, installation
  instruction, normal-current/ambient margin, protected-device coordination
  and maximum admitted prospective fault current.
- completion evidence required: holder-only and generic-rating known-bad
  fixtures; exact-element clean fixture; release assembly output names the
  element even though it is absent from the JLC placement file.
- history: 2026-08-11 — proposed after selecting Littelfuse 0297010.WXNV.

## IMP-020 — bounded, function-first schematic layout

- status: implementing
- observed: USB Hub 3S v4 Stage 5 schematic repair, 2026-08-11
- evidence: adding `schX`/`schY` to nearly every component changed a normal
  9--13 second TSX build into a 100% CPU run that had not completed after two
  minutes. The bounded runner's heartbeats proved it was alive, but the broad
  placement graph made the autorouter combinatorial. Reverting those
  coordinates, splitting the drawing by functional responsibility, arranging
  only U9's pins by electrical role, and fitting tall sheets to portrait pages
  restored 9--13 second builds and produced a materially clearer PDF.
- intended landing point: author schematic readability in this order: (1)
  functional sheets with explicit titles, (2) functional pin arrangement for
  dense mixed-role ICs, (3) adaptive page orientation, and only then (4) a
  small, measured set of absolute component constraints. Any step that adds
  constraints must run under the stage deadline and be reverted if it exceeds
  the established performance envelope.
- implementation progress: `render_schematic_pdf.mjs` chooses portrait or
  landscape A-series fit from exact component bounds without transforming the
  Circuit JSON; USB Hub v4 separates input enable, USB-A regulation and
  aggregate protection, and gives U9 a functional schematic pin arrangement.
  The renderer has clean landscape/portrait, exact-input immutability and
  fail-closed ownership fixtures in `tests/t1_schematic_render.py`.
- completion evidence required: USB Hub v4 receives an exact SOUND schematic
  readability verdict; the PCB-design authoring guidance names the ordering
  above; a fixture or static check rejects broad all-component absolute
  placement without an explicit waiver and tighter measured deadline.
- history: 2026-08-11 — proposed and implementation started after the bounded
  all-component placement experiment was stopped at two minutes.

## IMP-021 — aggregate fault/current-limit envelope

- status: implementing
- observed: USB Hub 3S v4 Stage 5 topology review, 2026-08-11
- evidence: three TPS2559 output switches each have a worst-high current limit
  of about 2.849 A, so their independent maxima sum to 8.547 A while U1 is
  rated for 8 A continuous. Per-port current checks and total normal-load
  power checks both passed because neither represented simultaneous downstream
  fault limits. The independent review found the missing envelope. A later
  primary-datasheet audit also found that the initial nominal 33 nF U9 timer
  did not guarantee 10 ms at the joint C/threshold/current corner and violated
  the startup relation while DVDT was open; the generic gate did not model
  either multi-parameter timing envelope.
  A later exact-hash review found a third escape: the authored U9 limits
  omitted TPS25982 Equation 4's `+0.11A` affine term. Because E-FAULT trusted
  copied threshold scalars instead of deriving them from R26 and the equation,
  the wrong pair remained internally consistent and passed every machine gate.
- present disposition: USB Hub v4 adds U9, a no-OVLO TPS259827 aggregate
  circuit breaker, between `5VA_RAW` and `5VA`. Its documented resistor and
  timer corners admit the stated short peak but disconnect persistent
  aggregate overload before U1 must carry the downstream worst-high sum. C29
  is now a 47 nF +/-5% C0G part. Including the 30ppm/C class bound over the
  100C design excursion gives 44.516 nF minimum and guarantees 11.129 ms at
  0.7 V and 2.8 uA. C30 is a 3.3 nF +/-2% C0G part; its 3.224 nF full-corner
  minimum gives a 4.388 ms capacitor term at the documented VIN and DVDT-current
  corner, permitting 82.795 nF while C29's full-corner maximum is 49.498 nF.
  This exact design still requires the topology review and first-article
  transient qualification. The review's second timer escape demonstrated that
  the generic gate is required now, before the present schematic can freeze.
- intended landing point: add a machine-readable fault-envelope contract that
  lists every downstream limiter's full-tolerance maximum, simultaneity rule,
  upstream continuous/peak ratings, aggregate limiter threshold and timer,
  reset behavior, post-timer device response, legitimate-pulse recurrence or
  minimum recovery interval, and evidence. Derived corners must retain enough
  precision or round outward. Fail if an unbounded simultaneous sum exceeds an
  upstream rating, if the interrupting device/timing is absent, or if repeated
  admissible peaks can accumulate without an explicit qualification boundary.
- completion evidence required: clean aggregate-breaker and mutually-exclusive
  fixtures; known-bad independent-limit sum and missing-timer fixtures; USB Hub
  v4 passes from exact U9/R26/C29/C30 values and cited TPS25982 limits.
- implementation progress: `early_design_check.py` now adopts `E-FAULT` when
  `power_tree.yaml` declares `fault_envelopes`. It calculates the simultaneous
  downstream worst-high sum, coordinates breaker threshold corners with
  normal load and upstream continuous/peak ratings, calculates minimum and
  maximum fault time, and checks the maximum timer capacitor against the
  minimum dV/dt startup ramp. Capacitor nominal/tolerance and all programmer
  refs must resolve to exact `electrical_invariants.yaml` `part_value` rows so
  duplicated proof data cannot silently drift. Breaker thresholds are now
  recomputed from the exact programmer, tolerance, TCR, temperature excursion,
  inverse-resistance coefficients and affine current offset; a separately
  published corner lock must match. Explicit normal/fault margins and any
  timer-bounded interval above an upstream continuous rating are also graded.
  Executable clean,
  mutually-exclusive, escaped-X7R, over-threshold, startup-relation and
  missing-timer fixtures live in `tests/t1_early_design.py`.
- measured result: the focused suite is 34/34 green, including 27 known-bad
  discriminators. USB Hub v4's exact authored contract passes at
  normal/peak/fault = 6/7.5/8.547625 A, breaker threshold =
  6.160253--8.066419 A, timer = 11.129--45.962 ms, and startup allowance =
  82.795 nF. The independent exact-hash topology review is SOUND and adds
  TI's maximum 270 us post-timer response for an approximately 46.232 ms
  total worst-case response, still inside the 50 ms physical qualification.
  That review also exposed the remaining generic obligations: outward-rounded
  aggregate precision and an explicit recovery/recurrence condition for the
  legitimate <=10 ms peaks. First-article transient qualification remains;
  the machine proof does not replace it.
- history:
  - 2026-08-11 — proposed after the independent review found a fault
    combination that normal operating-load checks could not represent.
  - 2026-08-11 — implementation started immediately after a second independent
    review reproduced the timer-temperature escape in the revised design.
  - 2026-08-11 — expanded after a fresh exact-hash review found that copied
    threshold scalars omitted the datasheet equation's affine current offset.
  - 2026-08-11 — the corrected exact-hash review closed SOUND and extended the
    future gate scope to outward rounding, post-timer response and repeated-
    peak recovery.

## IMP-022 — pre-review authored-board reference validation

- status: proposed
- observed: USB Hub 3S v4 Stage 5 schematic checkpoint, 2026-08-11
- evidence: the refreshed schematic and electrical rules correctly split the
  USB-A supply into `5VA_RAW -> U9 -> 5VA`, but `route.yaml` and
  `floorplan.yaml` still assigned the U1 output, output bulk and distributor
  geometry to the old unsplit `5VA` rail. The schematic gates passed and two
  expensive human reviews were about to start; a manual frozen-input scan
  caught the contradiction and the reviews had to be stopped. A scratch board
  generation also immediately exposed stale anchored overlaps introduced by
  the added capacitors and breaker.
- intended landing point: before requesting pre-route human review, parse the
  exact canonical netlist and statically resolve every net and `REF.PAD`
  mentioned by floorplan zones/assertions/thermal fields and routing excludes,
  waves, stubs and taps. Require the authored pin's net to equal the declared
  net, reject unknown/superseded names, and optionally run deterministic board
  generation plus collision/placement gates as a disposable preflight.
- completion evidence required: known-bad stale-net, wrong-pad-net, missing
  ref/pad and anchored-overlap fixtures; a clean split-rail fixture; driver
  ordering proves the cheap semantic pass and disposable placement preflight
  happen before either independent review is commissioned.
- present disposition: USB Hub v4's raw/protected zones, taps, assertions and
  placement were corrected manually; disposable board generation now reports
  91/91 anchored parts, zero pad/courtyard collisions, placement PASS and
  pad-separation PASS. The generic checker should be implemented after the
  current board reaches a stable release checkpoint so this repair does not
  expand into another pipeline rewrite mid-stage.
- history: 2026-08-11 — proposed after the review freeze caught a stale
  downstream topology contract before reviewer time was wasted.

## IMP-023 — pinned and provenance-bound TSX dependencies

- status: implementing
- observed: USB Hub 3S v4 Stage 5 schematic rebuild, 2026-08-11
- evidence: the project declared `tscircuit: "*"`, carried no lockfile and had
  no local dependency graph. Two bounded rebuilds failed in 3.983 s and 1.247 s
  because a newly cached `@tscircuit/core@0.0.1658` imported
  `@tscircuit/copper-pour-solver` from a dependency class the package exposed
  only as a development dependency. The missing module existed in another
  global graph, so the same electrical sources could pass or fail according to
  ambient cache/global state.
- intended landing point: every TSX project pins an exact `tscircuit` producer,
  commits its package-manager lock, installs from that graph, and includes the
  manifest plus lock bytes in M-FRESH. A dependency update is an intentional
  producer change that requires rebuild and re-review, not an ambient event.
- implementation progress: USB Hub v4 now pins `tscircuit@0.0.2300` and commits
  `03_tscircuit/bun.lock`; its local graph was installed without lifecycle
  scripts. `build_provenance.py` now fingerprints Bun/npm/pnpm/Yarn lockfiles
  alongside the TSX and package manifest. The project/template contracts and
  PCB-design instructions state the exact-version/committed-lock rule, and
  `tests/t1_rebuild_templates.py` carries a known-bad lock-mutation fixture.
  The canonical driver now runs a bounded
  `bun install --frozen-lockfile --ignore-scripts` before `tsci build`, so a
  clean checkout restores the graph instead of inheriting ambient modules, and
  invokes `./node_modules/.bin/tsci` rather than a PATH-resolved executable.
  The pinned producer also changed capacitor footprinter tokens from `0603`
  to `cap0603`; the bridge now accepts both producer dialects, with a regression
  assertion across 0402/0603/0805/1206/1210.
- measured result: the PATH-resolved executable was independently checked and
  found to be global tscircuit 0.0.2112 even after the local 0.0.2300 graph was
  restored. After binding the executable itself, project-local 0.0.2300
  generation completes in 7.981 s and the whole schematic checkpoint reaches
  the intentional exact-review stop in 12.01 s. The bridge emits 91/91
  non-empty FPIDs; the converter suite is
  43/43 green and the template/provenance suite is 52/52 green, including 24
  known-bad discriminators and one declared provenance blind spot.
- completion evidence required: the focused provenance suite passes, USB Hub
  v4 builds from its local locked graph, and the full schematic checkpoint is
  regenerated and reviewed from that producer identity.
- history: 2026-08-11 — proposed and implementation started when the first
  post-review rebuild exposed an ambient mixed dependency graph.

## IMP-024 — bounded, observable regression-suite execution

- status: implementing
- observed: USB Hub 3S v4 Stage 5 verification, 2026-08-11
- evidence: `tests/run_tests.sh` captures each suite's complete stdout in a
  shell variable and emits nothing until that suite exits. Real default-tier
  suites such as `t1_generate_board.py` and `t1_escape_tier.py` can therefore
  run for more than a minute with no visible progress, no per-suite heartbeat
  and no hard deadline. Process inspection showed the suite was alive, but the
  user-visible behavior was indistinguishable from the historical pipeline
  lockups this work is meant to eliminate.
- intended landing point: execute every suite through the existing
  process-group runner (or an equivalent small wrapper) with periodic
  heartbeat, elapsed time, last-output summary and a declared hard deadline;
  preserve the current independent exit-status/stdout-verdict reconciliation
  and aggregate counts.
- completion evidence required: a quiet-child fixture produces heartbeats and
  is killed with a distinct timeout verdict; a chatty suite streams bounded
  progress; a suite that prints failures but exits zero still trips the harness
  disagreement guard; the ordinary fast tier retains its exact aggregate
  verdict.
- implementation progress: `tests/run_tests.sh` now streams each suite through
  `tee`, emits periodic elapsed-time heartbeats and terminates the suite's
  process group at a declared hard deadline while preserving the suite exit
  status separately from `tee`. `tests/t1_pipeline_reliability.py` exercises
  the shared bounded runner's quiet-child heartbeat/deadline/process-group
  behavior. Direct runner fixtures for chatty-output bounding and the
  exit-zero/printed-failure reconciliation path remain before completion.
- history:
  - 2026-08-11 — proposed after the live fast-tier sweep reproduced the same
    silent-wait experience despite the PCB pipeline stages themselves being
    bounded and observable.
  - 2026-08-11 — implementation started after the schematic checkpoint was
    stable; the default runner now exposes progress and enforces deadlines.

## IMP-025 — mixed output-bank and CFF control-loop contract

- status: proposed
- observed: USB Hub 3S v4 fresh pre-route topology review, 2026-08-11
- evidence: U1 populated TI's table-value 22pF CFF plus required 4.99k series
  RFF while also fitting a 100uF polymer output capacitor. The exact APAQ part
  permits 24mohm ESR, placing its nominal ESR zero near 66kHz; TPSM63610
  section 8.2.1.2.6 explicitly forbids CFF when an output-capacitor ESR zero is
  below 200kHz. E-CAP correctly proved the ceramic minimum but did not treat
  added polymer bulk and CFF as one control-loop decision.
- intended landing point: extend the machine-readable output-bank contract to
  enumerate additional ceramic/polymer capacitance, ESR corners, switching
  frequency, any CFF/RFF population, vendor zero/pole placement requirements
  and explicit CFF prohibitions. Reject a fitted CFF at any admitted prohibited
  corner and require a first-article frequency-response/load-step obligation
  when a mixed bank cannot be closed analytically.
- present disposition: v4 removes R25/C27 and also removes U2's C28 because its
  mixed ceramic/polymer bank is not close to the minimum for which TI recommends
  CFF. ADR-0008 and the PCB-design checklist now require the complete-bank
  review. Implement the general gate after the schematic checkpoint is stable;
  the fresh topology lens currently supplies the independent backstop.
- completion evidence required: known-bad low-ESR-polymer-plus-CFF and
  prohibited ESR-zero fixtures; clean ceramic-minimum+CFF and mixed-bank/no-CFF
  fixtures; exact fitted refs/values bind to the schematic rather than prose.
- history: 2026-08-11 — proposed and the immediate design/instruction repair
  applied after fresh review caught the TPSM63610 prohibition before routing.

## IMP-026 — bounded fresh-context review execution

- status: implementing
- observed: USB Hub 3S v4 Stage 5 topology re-review, 2026-08-11
- evidence: a fresh topology reviewer remained active well beyond the useful
  review window without returning a verdict or a bounded list of unresolved
  checks. From the pipeline's point of view this was the same silent-lockup
  failure class as an unbounded producer, even though the work was reasoning
  rather than a child process. Interrupting it also meant its partial work was
  not admissible as exact review evidence.
- intended landing point: every commissioned fresh-context lens declares an
  elapsed-time or turn budget, verifies exact artifact hashes at entry and
  exit, and returns a closed verdict by the deadline. Any check that cannot be
  resolved inside the budget becomes an explicit material unresolved finding;
  it must not keep the pipeline apparently busy forever. Orchestration should
  expose reviewer age/status and allow a clean replacement without crediting
  partial prose.
- implementation progress: the PCB-design review instructions now require a
  declared review budget and deadline behavior. USB Hub v4's replacement
  topology and PDF lenses were commissioned with exact hashes, 10--12 minute
  budgets, start/end freshness checks and the unresolved-as-finding rule.
  A reusable machine-enforced reviewer watchdog/evidence fixture remains
  outstanding, so this item is not complete.
- follow-up evidence: during the r8 placement re-review, reviewers again ran
  beyond the useful evidence-gathering window despite receiving the written
  budget and despite the machine gates already supplying a complete bounded
  dossier. The operator had to interrupt them and close the evidence manually.
  This proves that a prompt-level deadline is advisory, not enforcement. The
  landing point must therefore own the reviewer process/turn externally: emit
  visible age/last-progress, interrupt at the declared wall time, reject any
  partial witness, and immediately convert the unfinished checklist into a
  named unresolved finding or launch one bounded replacement.
- completion evidence required: a canonical review launcher or protocol test
  proves that a quiet reviewer cannot exceed its declared budget unnoticed;
  a timed-out reviewer produces no admissible witness; and a bounded reviewer
  either returns a current closed verdict or names every unresolved check.
- history: 2026-08-11 — proposed and implementation started after an unbounded
  topology re-review was interrupted without admissible evidence.
- history: 2026-08-12 — r8 reproduced the overrun under an explicit written
  budget; machine-enforced interruption and evidence closure are now required
  for completion, not optional hardening.

## IMP-027 — standards terminology and evidence-identifier lint

- status: proposed
- observed: USB Hub 3S v4 Stage 5 fresh topology review, 2026-08-11
- evidence: the electrical design was SOUND, but review found two forms of
  documentation drift that can change the apparent claim: some prose cites
  TPS2559 document `SLVSCP1C` rather than the exact `SLVSCL5A`, and the local
  token `usb_type_c_receptacle_power_only` can be confused with USB Type-C
  Release 2.5's standardized Power-Only receptacle construction even though
  this board uses a normal 16-contact receptacle with data/SBU lands left NC.
  The same review also caught a parameter-direction error: a capacitor's
  maximum ESR proves the lowest possible ESR-zero frequency, not its highest.
- intended landing point: validate datasheet document identifiers against the
  exact part dossiers; maintain a small glossary of standards-defined terms
  that require an explicit claim/no-claim qualifier; and require prose that
  derives a bound from min/max source data to state which direction that source
  can prove. Run these cheap checks before commissioning exact human reviews.
- completion evidence required: fixtures reject a wrong-but-plausible document
  identifier, an unqualified collision with a governed standards term, and a
  maximum value used to prove a maximum for an inverse relationship; correct
  citations, qualified functional terminology and bound direction pass.
- history: 2026-08-11 — proposed from the final v4 topology lens; the exact
  design review records all three P2 findings so they remain visible meanwhile.

## IMP-028 — pre-review layout-precedent closure

- status: completed
- observed: USB Hub 3S v4 Stage 6 placement entry, 2026-08-11
- evidence: the first real-board build completed footprint placement before
  `P-PREC` found two source-only `part.yaml` records whose precedent ladders
  stopped at tier 1. Correcting those records changes the parts digest and
  therefore invalidates otherwise-current, hash-bound topology and schematic
  render reviews, even though no electrical topology or rendered sheet changed.
- intended landing point: run `P-LAYOUT` and `P-PREC` over the frozen part
  dossiers before schematic generation and before commissioning any review
  bound to the parts digest. Placement should rerun the same checks as a guard,
  but should never be their first execution on a new board.
- completion evidence required: a rebuild-order fixture proves malformed or
  unclosed `layout_refs` fails before TSX generation and before review
  commissioning; a corrected dossier reaches the schematic checkpoint without
  a later placement-stage invalidation; and the placement gate retains an
  independent defense-in-depth check.
- implementation: `policy_audit.py --phase source` now emits only the shared
  P-LAYOUT/P-PREC rows and deliberately ignores any stale realized board.
  `rebuild_all.sh` runs it after the other source-schema checks and before the
  M-FRESH stamp/TSX producer. The existing placement phase still reruns the
  same implementation and adds P-ADJ geometry. Clean and known-bad source-phase
  fixtures prove a project with no board can pass an honest ladder and an
  unclosed tier-1 stop fails; the rebuild-order fixture pins this phase before
  both TSX and review consumption. USB Hub v4's corrected 24-dossier source
  phase passes 2/2 and the subsequent schematic checkpoint reaches only the
  expected stale-review stop.
- history:
  - 2026-08-11 — proposed after the v4 placement policy gate exposed two
    omissions that were knowable before the exact schematic reviews.
  - 2026-08-11 — implemented before recommissioning the invalidated reviews;
    the full v4 driver demonstrated the new early stop/order on real inputs.

## IMP-029 — bounded, cached JLC model preparation for A-RENDER

- status: proposed
- observed: USB Hub 3S v4 Stage 6 placement review, 2026-08-11
- evidence: the native exact-board orthographic and isometric renders each
  completed in 8.6--8.8 seconds, but the first cold-cache `jlc_twin.py` run
  timed out at 180 seconds and a cache-reusing retry timed out at 360 seconds
  after exceeding its 240-second budget. The process was healthy and emitted
  ten-second heartbeats while resolving EasyEDA/JLC models, so this was not a
  deadlock; network/model preparation was incorrectly placed on the exact-
  review critical path. The early JLC export also correctly found 22
  placements without measured per-LCSC rotation evidence.
- intended landing point: after BOM/LCSC identities freeze, prefetch every
  catalog model through a bounded parallel/cache-preparation stage. Record a
  content digest and resolver/tool identity for every successful model and
  make the populated-twin renderer consume only that pinned local cache.
  Missing/failed models must produce a named coverage worklist without
  repeatedly spending the whole review window. The A-RENDER witness schema
  should distinguish `native_geometry`, `catalog_body` and `rotation` coverage
  and machine-verify how it was produced, so a manually authored PASS cannot
  masquerade as a successful `twin_overlay.py` run.
- completion evidence required: cold/warm/missing-model fixtures with bounded
  progress; the warm render performs no network access; a cache or resolver
  mutation invalidates the witness; the placement checker refuses a
  geometry-only PASS where catalog-body coverage is claimed; and USB Hub v4's
  38-code population reaches a complete twin without an indefinite wait.
- present disposition: placement review may use the exact native board render
  for geometry and routing feasibility, but it grants no body-registration,
  height, polarity, CPL-rotation or order credit. The full catalog twin and all
  22 rotation measurements remain explicit DO-NOT-ORDER release blockers.
- history: 2026-08-11 — proposed after two bounded cold-cache twin attempts
  exposed a network/cache stage on the placement-review critical path.

## IMP-030 — rotation-safe thermal-via ownership and exact placement DRC

- status: implementing
- observed: USB Hub 3S v4 Stage 6 placement review, 2026-08-11
- evidence: U9's split exposed pad contains adjacent `5VA_RAW` and GND lands.
  The generic board generator transformed explicit footprint-local thermal-via
  offsets with the wrong KiCad rotation handedness, so a 90-degree placement
  could put a via into the neighbouring net while still assigning it the
  declared source net. U1/U2 had the same coordinate permutation but all
  affected lands were GND, hiding the defect. The original placement battery
  ran overlap and pad-separation checks but did not run exact refilled KiCad
  DRC before commissioning human reviews; the independent pin lens found the
  short and zero-clearance findings instead.
- intended landing point: use one tested footprint-local-to-board transform;
  require every explicit via centre to lie inside its named owner pad and its
  copper shape to avoid every different-net pad; then run full-severity,
  refilled, schematic-parity JSON DRC immediately after placement policy and
  before human review. At this stage only unrouted ratsnest and KiCad's
  `isolated_copper` preliminary-zone class may remain, with no caller-defined
  defect allowlist.
- implementation progress: `generate_board_generic.py` now uses KiCad's
  measured coordinate operator and enforces both owner-pad containment and
  foreign-pad non-collision for each explicit via. The v4 floorplan declares
  48 vias across eight footprints, including independent U9 input/GND fields
  and two cold-socket C23 return vias. `placement_drc_check.py` plus both
  canonical rebuild templates now place P-DRC before PR-REVIEW; clean and
  known-bad fixtures cover shorts, library/clearance defects, parity,
  incomplete reports and attempted generic suppression.
- completion evidence required: the focused generator, placement-DRC,
  template-order and gate-contract suites pass; a clean v4 regeneration has
  zero pad/courtyard collisions; exact pre-route DRC has zero non-island
  violations and zero schematic-parity findings; and fresh pin/layout/render
  reviews bind that exact board hash.
- history: 2026-08-11 — proposed and implementation started immediately after
  the exact placement pin review found the rotated split-pad short.

## IMP-031 — published-legibility silk class for operational markings

- status: proposed
- observed: USB Hub 3S v4 Stage 6 placement render review, 2026-08-11
- evidence: the generated board and DRC accepted 24 functional legends at
  0.60--0.75 mm text height / 0.13 mm stroke and refdes as small as
  0.45 mm / 0.1125 mm. The tier ledger intentionally permits those values
  from boards that were observed to print, while JLCPCB's current official
  capability table says legend below 1.0 mm height or 0.15 mm line width may
  be unidentifiable. The first exact render lens correctly distinguished
  on-screen readability from manufactured readability and rejected safety,
  polarity, switch and port markings below the published envelope.
- intended landing point: model two explicit silk assurance classes rather
  than one ambiguous minimum: `empirical_printed` for noncritical density and
  `published_legible` for polarity, voltage/current, fuse, switch, connector
  and other operational markings. The generic generator should derive both
  height and emitted stroke from the selected class, fail an operational
  caption below the published class, and report coverage by class. Reference
  designators should default to the published class where space permits and
  any smaller fallback must remain visible debt, not a silent success.
- present disposition: v4 now uses 1.0 mm text and 0.16 mm emitted stroke for
  all retained functional captions and every refdes; redundant internal-net
  captions were removed rather than crowded below the limit. Exact P-DRC
  passes with zero silk-overlap or silk-over-copper findings. The fleet-wide
  two-class schema and gate remain future work.
- completion evidence required: clean and known-bad fixtures distinguish the
  two classes; every operational caption is independently inventoried and
  constrained; the emitted-stroke coupling is tested; and a board cannot earn
  a render/release PASS by citing merely `printed before` for a safety label.
- history: 2026-08-11 — proposed after the fresh v4 render review compared the
  exact produced geometry with JLCPCB's official legend table.

## IMP-032 — promote the reviewed schematic at its stage boundary

- status: completed
- observed: USB Hub 3S v4 Stage 6 placement replay, 2026-08-11
- evidence: the full driver deliberately pauses after schematic review and
  again after placement review, while the deterministic reuse driver consumes
  `03_tscircuit/kicad/<board>.kicad_sch`. The full driver copied its newly
  generated schematic into that pinned path only after final PCB DRC. During
  the intended placement iteration, `rebuild_reuse.sh` therefore exported the
  previous schematic topology and failed its review hash before board
  generation. The two schematic files had different SHA-256 digests and the
  normalized netlist changed from the reviewed `be5c7573...` to stale
  `56259186...`; this was a loud stop, but deterministic replay could not be
  used at the stage where it is explicitly needed.
- intended landing point: promote the exact generated schematic immediately
  after its semantic/ERC/checkpoint gates and both hash-bound schematic reviews
  pass, before board generation. A later PCB-stage failure must not revoke a
  completed schematic stage. Verify the pin immediately and again after the
  PCB stages; never promote a producer output that failed its own review.
- implementation: both canonical full-build drivers now copy and compare the
  schematic at the reviewed Stage-2 boundary, and the final stage only compares
  it again. `tests/t1_rebuild_templates.py` proves there is exactly one copy,
  that it follows schematic review, precedes board generation/DRC, and is
  verified both immediately and after PCB work.
- completion evidence: the focused rebuild-template suite passes, a fresh v4
  schematic replay promotes byte-identical `04_kicad` and pinned schematics at
  the review boundary, and `rebuild_reuse.sh` subsequently exports the reviewed
  normalized netlist rather than the superseded one.
- history: 2026-08-11 — found and fixed during the U9/J5 placement correction;
  the stale replay stopped in 0.4 seconds rather than wasting a routing run.

## IMP-033 — evidence-backed per-reference P-OUT exceptions

- status: proposed
- observed: USB Hub 3S v4 Stage 6 edge-connector review, 2026-08-11
- evidence: strict courtyard-to-outline checking correctly reports J5's
  mechanical courtyard 0.500 mm beyond Edge.Cuts after its manufacturer `PCB
  Edge` datum is aligned exactly. That overhang is intentional for the GCT
  USB4105 edge receptacle, while its tightest copper remains 1.700 mm inside.
  `placement_gates.py` supports `out_ok: ["J5"]`, and the contracts call such
  exceptions evidence-backed, but the checker accepts a bare ref string and
  neither requires nor prints the reason. V4 therefore carries a separate
  `out_ok_evidence` map that is human-readable but not yet machine-graded.
- intended landing point: replace or extend bare `out_ok` entries with
  structured `{ref, why, expected_excursion_mm, datum}` records. The gate must
  fail an exception without evidence, print the measured excursion and reason,
  continue checking all copper pads, and invalidate the exception when the
  measured overhang exceeds its declared bound.
- completion evidence required: edge-connector/castellated clean fixtures plus
  missing-reason, wrong-ref and over-excursion known-bads; migration of the
  existing bare-list test; v4 passes at the measured 0.500 mm J5 courtyard
  excursion and still fails if any J5 copper leaves the board.
- present disposition: keep strict courtyard mode enabled for v4 and retain the
  explicit human-readable J5 evidence. Implement the shared schema before a
  second board copies the ungraded map; this is not a routing blocker.
- history: 2026-08-11 — proposed while closing J5's manufacturer edge-datum P1.

## IMP-034 — pre-review exact validation of deterministic route copper

- status: proposed
- observed: USB Hub 3S v4 Stage 7 route preparation, 2026-08-11
- evidence: the canonical routing preflight passed, but `route prep` then
  refused four explicit U5/U6 output via-in-pad drops in 0.70 seconds. Their
  0.50/0.20 mm geometry was copied from the superseded placement. On the exact
  TPS2559 0.50 mm-pitch row, the 0.50 mm via left only 0.13 mm to an adjacent
  0.24 mm foreign-net land, below the adopted 0.18 mm clearance. The route
  emitter behaved correctly and no stochastic routing time was spent, but the
  deterministic copper had not been part of the placement-stage machine gate.
- intended landing point: add a read-only `prep --validate` mode, or equivalent
  exact-board gate, that resolves every authored seed segment/via and tap,
  checks pin/net identity, pad contact, foreign copper, holes, outline and rule
  areas, and emits no board artifact. Run it after placement DRC and before
  hash-bound pin/layout/render review so a moved footprint cannot leave stale
  absolute route coordinates for the routing stage to discover.
- completion evidence required: clean and known-bad fixtures cover moved pads,
  wrong nets, foreign-pad clearance, hole spacing, board-edge/rule-area
  conflicts and idempotency; the full rebuild order pins the validation before
  placement reviews; the tier preflight also grades every prep/stitch seed-via
  declaration against the exact board-setup via and annular constraints. USB
  Hub v4's exact off-pad 0.50/0.20 mm U5/U6 drops pass while the former in-pad
  configuration fails with the measured 0.13 mm foreign-copper gap.
- present disposition: fix v4 now because these four drops are the declared
  current path to the B.Cu output pours and block routing. A rejected interim
  0.40/0.20 mm attempt cleared the neighboring pads but exact DRC found four
  `via_diameter` plus four `annular_width` violations against the board's
  conservative 0.50 mm / 0.15 mm setup; the tier preflight had not compared
  this seed-via block with those board constraints. Keep the shared pre-review
  validation as future work; bounded prep plus exact DRC remain safe backstops.
- history: 2026-08-11 — proposed after the first corrected-placement prep run
  stopped before KRT and exposed stale, electrically impossible via geometry.
- follow-up evidence: Pluto RX2 8-way v5's D15 floorplan proved zero proper
  straight-corridor/courtyard intersections, but the first exact seed attempt
  still refused 7/9 RF centreline segments in 0.41 s: each hit an adjacent U1
  or SMA ground pad at an oblique endpoint. Package-normal and launch-normal
  escape sections made all nine polylines collision-clean. A read-only exact
  seed validation before the D15 human review would have exposed the distinction
  between a body-clear floorplan proof and legal copper without regenerating a
  review checkpoint.

## IMP-035 — static pour-service coverage for router-excluded nets

- status: proposed
- observed: USB Hub 3S v4 Stage 7 authoritative post-stitch DRC, 2026-08-11
- evidence: both KRT race candidates were CLEAN and the in-process stitch gate
  also said clean, but fresh KiCad CLI refill found ten opens on nets excluded
  from stochastic routing plus one dangling 5VC_RAW via. All were deterministic
  coverage omissions knowable from the track-free placement: five inter-pad
  gaps in U9's parallel OUT bank, R22 and TP3 outside their named pours, C6/C9
  surface islands without explicit plane drops, and R11 incorrectly declared
  as a drop even though no plane existed under its pad. KRT correctly reported
  zero routed-net opens because these nets were deliberately outside its scope.
- intended landing point: before route search, enumerate every pad on every
  `prep.waves.exclude` net. For each, require exact geometric evidence that it
  is served by a filled zone on a flashed layer, a same-net plated land, or a
  named deterministic seed/tap whose endpoint reaches the intended pour. A
  `plane: true, drop: true` declaration must prove that the named plane
  actually overlaps the selected via site; prose or same-net copper beneath an
  SMD pad is not connectivity. Report the uncovered refs/pins and the owning
  remedy before KRT runs.
- completion evidence required: fixtures reject a pad just outside a pour, a
  split same-net pin bank, a drop over no plane, and a surface island cut by
  later routing; valid direct-pour, plane-drop, plane-tap and seed-stub cases
  pass. USB Hub v4's excluded nets grade every physical landing and the first
  authoritative post-stitch refill reaches zero deferred opens without a
  discovery/rebuild cycle.
- present disposition: repair v4 now in declarative taps and one scoped U9
  output-bank bridge. Keep fresh CLI refill/parity as the authority (IMP-010
  is working as intended); add the static coverage gate before another board
  spends a route/review cycle discovering deterministic opens at the end.
- history: 2026-08-11 — proposed when the first corrected route was clean for
  every routed net but failed 0/0/0 exclusively on excluded pour-net service.
- follow-up evidence: Pluto RX2 8-way v5's first successful RF prep served only
  26/32 SMD GND pads. The six uncovered pads were precisely U1's interleaved
  RF-ground perimeter lands; adding short deterministic links into the exposed
  pad and its existing filled/capped field made the next pre-route denominator
  32/32 before KRT. Coverage must be evaluated after deterministic critical
  copper exists, because that copper both supplies connections and consumes
  legal rescue space.

## IMP-036 — checkpoint-aware canonical rebuild at layout seal

- status: completed
- observed: USB Hub 3S v4 Stage 8 layout-seal preparation, 2026-08-12
- evidence: the full producer deliberately pins and pauses on exact schematic,
  PDF and netlist bytes for independent review. Its safe continuation is
  `rebuild_all.sh --resume-after-schematic-review`, which verifies that
  checkpoint and regenerates the complete board. `pcb_flow.py layout-seal`
  could only call `rebuild_all.sh` without arguments, so it would rerun the
  nondeterministic TSX producer, replace the approved bytes and correctly stop
  for another review instead of ever reaching its seal checks.
- implementation: `flow.rebuild_args` declares optional, source-hashed
  arguments to the canonical rebuild driver. Layout sealing passes them to the
  driver but still performs the fresh board build; malformed values fail
  before seal mutation. USB Hub v4 declares its content-addressed resume arm.
  `tests/t2_pcb_flow.py` covers the exact command and malformed configuration;
  `skills/kicad-pcb/references/fast-pcb-flow.md` defines the contract.
- history: 2026-08-12 — implemented before v4's first layout-seal attempt so
  the orchestration defect could not cause a redundant review loop.

## IMP-037 — stage-typed placement-review validation

- status: completed
- observed: USB Hub 3S v4 Stage 8 layout seal, 2026-08-12
- evidence: the canonical rebuild correctly graded four independent placement
  reviews against the exact track-free board, imported the promoted route,
  applied 29 deterministic services and reached DRC 0/0/0. The seal conductor
  then invoked the same pre-route checker against the routed board. Its hash
  differed by design, so a clean layout could never acquire a seal witness.
- implementation: `pcb_flow.py layout-seal` leaves the track-free review in
  the canonical rebuild at its true lifecycle boundary. After routing it still
  repeats body/outline clearance, critical-route, landability, pad-separation,
  placement-policy and full DRC checks. Reviewed-commit recovery remains bound
  to exact final pin/render/topology/layout review provenance. Hermetic tests
  prove no post-route plan contains `pre_route_placement` and that geometry,
  connectivity and DRC remain present.
- history: 2026-08-12 — implemented after the first fully clean v4 seal replay
  exposed the impossible cross-stage comparison in 0.094 seconds.

## IMP-038 — make ampacity audit a canonical stage gate

- status: completed
- observed: USB Hub 3S v4 routed-evidence review, 2026-08-12
- evidence: `rules_audit.py` correctly rejected four high-current classes and
  an unreadable switching-node declaration when run manually. Neither
  canonical rebuild driver invoked it: source policy read only its A-FIRE
  helper, while layout seal reached DRC 0/0/0 and acquired a witness despite a
  0.30 mm U9 output-bank collector and one plane-transfer via carrying the
  protected aggregate rail. A capable checker outside the execution stack is
  documentation, not a gate.
- implementation: full and deterministic canonical drivers, plus both
  skill-owned templates, now run `rules_audit --phase source` before producer
  spend and the full board-bound audit immediately after the final rules
  generation and before final DRC. High-current pour classes carry explicit
  geometry evidence; signal exemptions are parseable. Template tests reject a
  driver with either stage missing or misordered.
- completion evidence: generator/router suites pass, rebuild-template tests
  prove source-before-producer and full-rules-before-final-DRC ordering, and
  USB Hub v4's exact regenerated board must pass A-CLASS/A-AGREE/A-AMP/A-FIRE/
  A-ORDER before reacquiring layout seal.
- history: 2026-08-12 — implemented immediately after the first routed copper
  extraction found the checker had teeth but no call site.

## IMP-039 — selective, fabricator-compatible via treatment

- status: completed
- observed: USB Hub 3S v4 manufacturing-evidence review, 2026-08-12
- evidence: the board source declared `capping: yes, filling: yes` as a KiCad
  board default. KiCad 10 documents “From rules” vias as inheriting that
  default, so every ordinary 0.60/0.30 mm routing/stitch via appeared to request
  IPC-4761 Type VII even though only via-in-pad holes need the process. JLC's
  current capability table limits its via-in-pad family and its order guide
  requires the selected hole family in order remarks. The blanket declaration
  was ambiguous, unnecessarily expensive and not an exact manufacturing
  instruction.
- implementation: the shared generator and tap emitter now support item-level
  capping/filling overrides through KiCad's per-via API. USB Hub v4 marks only
  its 0.50/0.20 mm via-in-pad fields and exact SMD-pad drops Type VII; ordinary
  0.60/0.30 and 0.70/0.30 mm transfers inherit the tented board default. The
  machine-readable assembly contract requests copper-paste fill, names the
  exact geometry/source and retains a mandatory uploader confirmation.
- completion evidence: clean tests prove item-level flags and geometry survive
  a KiCad save; known-bads reject malformed protection and misuse of exact via
  placement; the regenerated board/fab package must census protected versus
  ordinary vias and reproduce the order remark before release seal.
- history: 2026-08-12 — implemented while comparing the exact v4 board against
  KiCad 10 IPC-4761 behavior and JLCPCB's current via-covering guidance.

- follow-up: the first selective implementation still assigned four ordinary
  off-pad seed vias the protected family's 0.50/0.20 mm geometry. Native KiCad
  flags were correct, but Gerber order instructions cannot address them by
  per-item metadata. USB Hub v4 now makes the process families disjoint by
  drill: every 0.20 mm drill is Type VII and all ordinary vias use 0.30 mm.
  The r7 source and fully stitched censuses prove no cross-family exception.

## IMP-040 — promoted-route compatibility before placement review

- status: completed
- observed: USB Hub 3S v4 corrected-process replay, 2026-08-12
- evidence: the track-free board and its schematic/placement geometry were
  independently sound, but `route.final` still selected r5. Exact import then
  failed in under one second because 18 of the 48 inherited source-owned vias
  were 0.60/0.30 mm in r5 and 0.50/0.20 mm in the current source. All 48 r5
  copies also predated the item-level Type-VII flags. The human layout lens
  correctly refused to grant route permission to a canonical command that
  could not execute, forcing a review round to discover a static derivative
  incompatibility.
- implementation: `promoted_route_check.py` runs inside the placement phase of
  `pre_route_review_check.py`, immediately after exact track-free generation
  and before any human review is credited. For an explicitly selected existing
  `route.final`, P-ROUTEBASE independently compares footprint placement/layer,
  pad geometry/net identity, and every inherited source-via identity
  `(net, x, y)`, geometry and IPC-4761 process bits. Missing/new source vias and
  stale placement fail with exact evidence. An absent artifact is explicit
  N-A only for a first route. The importer's independent geometry refusal
  remains in place as defence in depth.
- completion evidence: seven focused fixtures cover compatible inheritance,
  a first route, geometry drift, process drift, added and removed source vias,
  and moved placement. USB Hub v4's freshly regenerated exact base passes
  95-footprint / 48-source-via coverage against promoted r7; the stale r5 case
  is the measured incident this gate now prevents before review spend.
- present disposition: v4 was repaired by a fresh bounded route from corrected
  r0 and promotion of r7 after the process families were made drill-disjoint.
  P-ROUTEBASE is now a mandatory canonical placement-review prerequisite.
- history: 2026-08-12 — proposed after the exact v4 review found the stale
  promoted artifact before any routing or fabrication spend.
- history: 2026-08-12 — implemented and regression-tested before v4's first
  layout seal; the exact corrected r0/r7 pair passes 95/48 comparisons.

- follow-up: deterministic route-prep copper is now part of the same identity
  boundary, not merely the generated placement. The canonical drivers run
  prep before placement review, and P-ROUTEBASE compares every prepared
  segment and via with the promoted route. Focused coverage is 9/9, including
  a missing prepared segment and a missing prepared via. USB Hub v4's exact
  corrected r0/r8 pair passes 95 footprints / 64 base-or-prepared vias / 12
  prepared segments; the earlier r7 correctly fails on all twelve newly
  declared U4-U6 input-bank vias.

## IMP-041 — series-transition via ampacity as a non-vacuous gate

- status: completed
- observed: USB Hub 3S v4 routed-copper review, 2026-08-12
- evidence: connectivity, full DRC and netclass ampacity all passed while the
  exact board forced the aggregate protected rail through four 0.30 mm drill
  barrels and each 2.849 A USB-A input island through one 0.20 mm drill barrel.
  Those banks credited only 3.36 A versus 8 A and 0.55 A versus 2.849 A under
  TI SLVA959B Table 3-1's IPC-2152 10 C-rise screening values. Same-net vias
  elsewhere cannot repair this: they may be geometrically countable without
  carrying the series current at all.
- implementation: `via_ampacity_check.py` grades named, tight series-boundary
  rectangles from `route.yaml`, sums only declared finished-hole capacities,
  gives fill material zero electrical credit, and requires a source, method,
  temperature rise, continuous-current requirement, minimum via count and
  physical reason. A-VIA runs after the final saved-board construction and
  rules audit but before authoritative DRC in both canonical drivers and in
  layout seal. Its explicit vacuity fixture proves the geometric limitation;
  independent topology/path review and loaded first-article testing remain
  mandatory.
- completion evidence: clean, insufficient, explicit-N-A and vacuity fixtures
  pass 4/4; gate-contract adoption rises with the new declared blind spot. The
  exact r8 board passes all four banks: U9 has fourteen 0.70/0.30 mm transfers
  crediting 11.76 A for 8 A, and each U4-U6 input has four ordinary 0.60/0.30
  mm transfers plus one protected 0.50/0.20 mm pad drop, crediting 3.91 A for
  2.849 A. V-PROCESS independently counts 65 protected and 118 ordinary vias
  with drill-disjoint process families; DRC is 0/0/0.
- history: 2026-08-12 — implemented before routed review was allowed to resume;
  the checker first failed the previously clean r7 board, then passed the
  declaratively repaired and freshly routed r8 board.

## IMP-042 — exact local datasheet authority before pin review

- status: completed
- observed: USB Hub 3S v4 routed pin review, 2026-08-12
- evidence: the first exact-board pin lens reached a conclusion while the
  selected TPS2559, TPS259827O and SMBJ15A dossiers had no hash-selected local
  datasheet bytes. A mutable URL or a neighboring family PDF can look plausible
  and still make the review non-reproducible. This was discovered only after
  the independent reviewer had spent its full pass.
- implementation: `pin_audit.py` now fail-closes as P-AUTH unless
  `datasheet.sha256` is a valid digest matching exactly one of the local PDF
  candidates. It never falls back to directory order, a sole unbound PDF or a
  URL. The parts contract now calls the URL human retrieval provenance and the
  digest-selected bytes review authority. Exact vendor-authored PDFs were
  archived for TPS2559, TPS259827O, SMBJ15A and the Phoenix 1715022 terminal;
  the latter two retain exact distributor-mirror provenance because their
  manufacturers' delivery endpoints block automation.
- completion evidence: `tests/t1_pin_audit.py` passes one clean selector and
  three known-bad authority cases; schema governance proves the digest reader
  and the pin-review canon names P-AUTH. The exact v4 dossiers are regenerated
  from the sealed-board hash before the confirmation lens is commissioned.
- history: 2026-08-12 — implemented immediately after the routed pin lens
  exposed the late authority gap; focused pin, contract, schema and gate-on-gate
  suites passed before review resumed.

## IMP-043 — non-guaranteed bounds must remain release obligations

- status: implementing
- observed: USB Hub 3S v4 routed topology review, 2026-08-12
- evidence: the first sealed-board topology review found that TPSM63604 lists
  FB input current as 10nA typical without a maximum, while the project treated
  a 50nA engineering allowance like a closed component corner. The same review
  found that the Pi delivery calculation named neither an exact cable nor the
  GCT connector's 50mOhm post-test limit. Correct arithmetic cannot promote an
  unguaranteed typical value or an unnamed accessory into production evidence.
- implementation: v4 lowers the Type-C divider impedance by ten, screens FB
  current at 500nA and names Amphenol 10165794-Z0030YBLF. GCT's
  post-environment contact limit remains plausibility evidence, while the
  binding qualified term is a hot four-wire J5-land-to-Pi-load-plane bound that
  includes both mated pairs and cable/sink internals. Complete-path voltage and
  resistance remain explicit first-article findings. The paper gate may permit
  a controlled engineering article after independent review, but it may not
  close the physical qualification or production-release state.
- additional evidence: the first repaired-PDF review found the selected U2
  dossier still described the superseded 50nA screen while ADR-0009 and the
  executable rule used 500nA. The exact-bound human comparison caught the
  contradiction, but a typed shared qualification obligation would give this
  fact one machine-readable owner instead of duplicating it across prose.
- additional evidence: Pluto RX2 8-way v5 set the TPS7A2433 dossier's
  `pdiss_max_mw` to 66 and explicitly described it as a 30mA analysis ceiling,
  while the field contract defines it as a package rating or board/ambient
  derating. `power_topology.py` correctly proved 44.825mW < 66mW but could not
  detect that the compared ceiling had the wrong semantic authority. Correct
  arithmetic over a self-selected design budget is not a component-rating
  proof.
- intended landing point: extend the shared design/release schema so every
  `engineering_qualification_bound`, `qualified_max`, or other non-datasheet
  basis creates a typed validation obligation with an owner, acceptance test
  and latest release stage it blocks. A gate must reject a production claim if
  any such obligation is open, and report distinctly whether it blocks design,
  first-article ordering, first-article acceptance or production.
  Numeric rating fields additionally need a typed `{value, basis, source,
  conditions}` record; a package rating, board/ambient derating, engineering
  screen and design operating budget are distinct closed-vocabulary bases and
  may not substitute for one another merely because their units match.
- completion evidence required: clean fixtures for a controlled prototype and
  a fully qualified production release; known-bads for a typical-only maximum,
  unnamed interconnect and missing acceptance test; USB Hub v4 reports its
  FB/interconnect obligations without misclassifying them as guaranteed
  limits.
- history: 2026-08-12 — project-level implementation started while repairing
  the routed topology review; shared schema/release enforcement remains open.
- history: 2026-08-12 — corrected the stale U2 dossier before commissioning a
  fresh review; no review hash was carried across the changed parts digest.
- implementation progress: `power_topology.py` now reads and reports the
  optional delivery `margin_basis`/`margin_evidence` pair and rejects partial
  declarations; USB Hub v4's 5% residual is therefore no longer an orphan
  schema field. This closes field propagation into the design gate, but the
  generic release-obligation schema and production-claim refusal remain open.
- history: 2026-08-12 — USB-IF's normative LLCR measurement boundary showed
  that the first contact/cable split did not account unambiguously for two
  mated pairs and excluded plug internals; IMP-047 records the endpoint-level
  generalization and v4 now qualifies the complete interconnect instead.

## IMP-044 — rendered-symbol endpoint coincidence

- status: completed
- observed: USB Hub 3S v4 schematic readability re-review, 2026-08-12
- evidence: Circuit JSON connected C22/C23 and their traces at identical
  schematic-port coordinates, but the delivered PDF visibly separated each
  polarized-capacitor body from both wires. The installed `circuit-to-svg`
  renderer composes a terminal translation with a non-unit symbol scale in an
  order that leaves a scale-dependent offset. Electrical parity and ERC could
  not detect this presentation defect.
- implementation: `render_schematic_pdf.mjs` now corrects only a display copy
  of scaled two-port symbols and their display ports before SVG conversion;
  traces and the authoritative Circuit JSON remain unchanged. It recreates
  the installed renderer's transform, fail-closes above 1 micrometre residual,
  and reports the correction count and maximum residual. The correction is
  deliberately presentation-only and remains subordinate to normal-scale
  human readability review.
- completion evidence: `tests/t1_schematic_render.py` proves both symbol
  terminals land on their original endpoints, the input object and exact JSON
  file stay unchanged, aliases remain canonical, and malformed/unowned inputs
  fail closed. The exact v4 PDF applies two corrections with a measured
  0.000168 mm maximum residual; pages 3 and 9 visibly join C22/C23 to both
  rails.
- history: 2026-08-12 — implemented immediately after the second independent
  PDF review exposed the gap; ineffective source-size hints were removed.

## IMP-045 — pre-spend schema and bound governance

- status: completed
- observed: USB Hub 3S v4 schematic regression replay, 2026-08-12
- evidence: the canonical schematic rebuild passed and two fresh human
  reviews were already in progress when the full repository suite found that
  new `margin_basis`/`margin_evidence` fields had no declared reader and that
  ADR-0009 published `<=14mOhm` without an executable bound block. Both facts
  were knowable from authored bytes before the 8.143-second producer or any
  reviewer time.
- implementation: the full rebuild template and v4 driver now run
  `schema_reader_audit.py` and `adr_bound_provenance.py` as bounded,
  heartbeat-emitting source stages before the provenance stamp and TSX build.
  ADR commands have a 30-second per-command limit and both wrapper stages a
  60-second process-group deadline. The v4 delivery-margin pair is read and
  reported by E-MARGIN; ADR-0009's cable limit regenerates from the exact
  98mOhm path decomposition. The fleet ratchets are now 502/502 declared
  schema keys, 424 proven readers, and 13 cited ADR bounds with 37 owed.
- completion evidence: `tests/t1_rebuild_templates.py` proves ordering and a
  post-TSX known-bad; `tests/t1_power_topology.py` covers complete and partial
  margin provenance; `t1_schema_reader.py` and `t1_adr_bounds.py` pin the
  raised monotone floors. The two prematurely commissioned reviews were
  interrupted and cannot become accepted evidence.
- history: 2026-08-12 — implemented in the same stage that exposed the gap.

## IMP-047 — IR-budget terms need non-overlapping measurement endpoints

- status: implementing
- observed: USB Hub 3S v4 Type-C topology review, 2026-08-12
- evidence: a 25mOhm contact term applied USB-IF/GCT's 50mOhm post-stress LLCR
  as four parallel VBUS plus four parallel GND contacts, and a separate
  14mOhm cable term named an exact assembly. USB Type-C Release 2.0 section
  3.7.8.1 defines LLCR across one plug/receptacle pair and excludes internal
  paddle cards/substrates. The real board-to-Pi path has two mated pairs. Each
  scalar was plausible, their sum was machine-checked, and the boundary still
  omitted or ambiguously assigned physical segments.
- implementation progress: USB Hub v4 now uses one <=39mOhm hot four-wire
  qualified term from J5 PCB-side VBUS/GND lands to Pi load-plane sense points,
  explicitly including both mated pairs, cable plug internals/conductors and
  Pi entry path. `early_design_check.py` accepts that complete-interconnect
  alternative for a load-plane claim and rejects mixing it with decomposed
  contact/cable terms; the template contract documents the choice.
- intended landing point: give every IR component structured `from`/`to`
  endpoints and a path-order/coverage gate that detects gaps and overlap,
  rather than relying on evidence prose. Measurement planes should identify
  Kelvin points, not only device classes.
- completion evidence required: clean fixtures for fully decomposed and
  end-to-end-qualified paths; known-bads for a missing sink connector, double
  counted interface, overlapping complete/decomposed terms and unjoined
  endpoints; the real v4 report prints one continuous regulator-to-load path.
- history: 2026-08-12 — project correction and mutual-exclusion guard landed;
  structured endpoint continuity remains open.

## IMP-046 — rendered reference/value occlusion preflight

- status: proposed
- observed: USB Hub 3S v4 schematic readability review, 2026-08-12
- evidence: the exact PDF was electrically correct and its scaled-symbol
  terminals passed the endpoint check, but BOOT_C_C/BOOT_C_R/GND label ink
  covered C4's reference designator on page 9. The independent normal-scale
  review blocked placement; moving only C4's schematic coordinate made its
  reference, value and terminals plainly readable. Existing electrical, ERC
  and terminal-coincidence gates cannot grade text occlusion.
- intended landing point: before commissioning human readability review,
  compare rendered ink or PDF text boxes for every component reference and
  value against label, conductor and symbol ink. Report the exact page/ref and
  refuse a zero-denominator run. Keep the human review: collision-free text is
  necessary but does not prove page flow, explanatory adequacy or correct
  visual interpretation.
- completion evidence required: a clean multi-page fixture with every
  reference/value measured; known-bads for label-over-reference,
  wire-through-value and missing/unmeasurable text; a discriminator proving
  the fixed C4 page changes verdict while an adjacent clear component does not.
- history: 2026-08-12 — recorded after the third fresh PDF review caught the
  defect before any placement or routing work was allowed to resume.

## IMP-048 — compare visible schematic paths with electrical nets

- status: proposed
- observed: USB Hub 3S v4 schematic readability review, 2026-08-12
- evidence: page 3 visibly presented C2 as VIN-to-VIN while the exact netlist
  correctly placed it between VIN and GND. Netlist parity, invariants and ERC
  could prove only the electrical artifact; terminal-coincidence could prove
  only that a symbol met the lines drawn at it. None could prove those visible
  lines communicated the same endpoint nets. The independent human lens did.
- near-term implementation: retain exact-PDF human review and replay the full
  net-survival/parity gates after every presentation edit. USB Hub v4 now uses
  explicit per-pin VIN/GND labels for C2, avoiding an ambiguous shared auto-
  routed trunk. It also names the formerly isolated U1 `5VA_RAW`, U4-U6
  `VBUSA1/2/3` and U2 `VIN` pin groups at their visible endpoints. A broader
  attempted move was rejected when net-survival caught an unrelated SW1
  open-pin merge, demonstrating why a local-looking layout edit cannot skip
  the electrical replay.
- intended landing point: derive a display graph from each rendered sheet,
  associate symbol terminals and net-label anchors with visible conductors,
  and compare the reached endpoint labels with the exact netlist. Report each
  checked terminal and refuse missing, multiply-labelled or zero-denominator
  paths. Treat explicit disconnected net labels as valid named endpoints.
- completion evidence required: a clean VIN-to-GND capacitor; a known-bad
  rendering of the same netlist as VIN-to-VIN; a misleading junction; a valid
  explicit-label endpoint; and a discriminator proving that endpoint
  coincidence alone still passes the VIN-to-VIN fixture.
- history: 2026-08-12 — recorded after the fourth fresh schematic review;
  project-level explicit endpoints landed, generic visible-path comparison is
  still open.

## IMP-049 — bounded independent-review briefs and closure deadlines

- status: implementing
- observed: USB Hub 3S v4 exact placement review, 2026-08-12
- evidence: pin, layout and render reviews began on the same frozen board.
  Render and layout closed normally, but the first pin reviewer kept widening
  an already-complete physical-land investigation despite repeated requests to
  write a verdict. It produced no review file and was discarded. A replacement
  brief limited to six named failure classes closed promptly, passed all
  192 physical identities and wrote the required exact-hash witness. No design
  bytes changed in either attempt.
- intended landing point: every independent review commission names its exact
  immutable inputs, one allowed output, bounded checklist, explicit exclusions,
  verdict vocabulary and a wall-clock closure budget. At the deadline the
  reviewer must write a closed verdict from evidence already collected or
  return `INCOMPLETE`; it may not silently broaden scope. An incomplete attempt
  is never review evidence and is replaced, with its elapsed time recorded.
- completion evidence required: orchestration tests for on-time SOUND,
  on-time DEFECTIVE, deadline INCOMPLETE and forbidden-file mutation; review
  journals separate machine-stage duration from human-review duration and
  report discarded attempts without treating them as design failures.
- history: 2026-08-12 — proposed after the placement pin lens became the only
  long-running activity despite all producer and gate commands being bounded.
- history: 2026-08-12 — the strict schema-1 commission/witness core landed in
  shadow form. It binds one lens, exact subject/commit/artifacts, a non-zero
  checklist, explicit exclusions, one output and a UTC deadline; durable
  output/input hashes are independently supplied at admission. Late and
  partial witnesses remain inadmissible, while a complete DEFECTIVE witness
  remains valid blocking evidence. A launcher/legacy-Markdown adapter and
  real-review adoption remain open, so this entry is not complete.
- history: 2026-08-12 — USB Hub 3S v4 now exercises a project-local real
  placement commission at the exact route-prep boundary. It emits either an
  atomic `ALREADY_ADMISSIBLE` pointer or an immutable content-addressed
  `INCOMPLETE` request with top/isometric renders; it never writes the human
  witnesses or acceptance token. The unchanged review gate still reported all
  eight stale findings. First preparation measured 19.77--21.15 seconds and a
  semantic rerun 1.06--1.07 seconds, so no placement-resume flag was added.
  Promotion of the adapter and direct schema-1 review-service integration
  remain open.

## IMP-050 — generated evidence must prove fresh output, not exit zero

- status: implementing
- observed: USB Hub 3S v4 routed-review export, 2026-08-12
- evidence: `kicad-cli pcb render` rejected a negative-first rotation argument,
  printed its usage page, returned exit code zero and wrote no file. Because
  the output directory already held an isometric PNG from 02:29, `set -e` let
  the script continue and its final checksum table presented that stale image
  beside fresh 05:23 evidence. Only explicit timestamp inspection exposed it.
- implementation progress: the v4 exporter now removes each exact expected
  target before starting, requires a non-empty file immediately after every
  producer/conversion, and uses the proven positive-first `35,0,-35` rotation
  syntax. A complete rerun regenerated all nine outputs, including a fresh
  isometric view. No exit status can preserve an adjacent old artifact now.
- intended landing point: make delete-before-produce plus postcondition
  verification the shared rule for every generated review/release artifact.
  Where practical also stamp input hash, producer command and finish time in a
  machine manifest; consumers should bind that manifest rather than infer
  freshness from directory presence.
- completion evidence required: a fixture whose fake producer prints usage,
  exits zero and leaves an old file must fail; clean and zero-byte outputs must
  discriminate; project exporters/templates adopt the same helper or shared
  wrapper.
- history: 2026-08-12 — project repair landed immediately; shared helper and
  executable known-bad coverage remain open.

## IMP-051 — long external stages must expose progress and a bounded retry budget

- status: implementing
- observed: USB Hub 3S v4 JLC digital-twin fetch, 2026-08-12
- evidence: after its one setup line, `jlc_twin.py` produced no console output
  for more than 90 seconds while fetching and retrying catalog CAD. The process
  was alive and measurable only by inspecting its cache: 16/40 unique codes had
  completed at roughly two minutes, then 19 code directories existed with eight
  still empty during backoff. To an operator this is indistinguishable from the
  historical pipeline lock-up unless they know how to inspect processes and
  cache timestamps.
- intended landing point: every network or otherwise long-running stage prints
  a periodic machine-readable heartbeat containing `completed/total`, current
  item, attempt/max-attempts, retry/backoff seconds, elapsed time and a rolling
  ETA. The orchestrator must declare a wall-clock budget before launch and end
  with a distinct `TIMED-OUT` result plus a resumable command; completed
  content-addressed cache entries must survive the stop. Silence longer than a
  configured heartbeat interval is itself a process finding, not permission to
  wait indefinitely. Consumers such as `jlc_rotation_measure.py` should index
  the cache tree once, not run a recursive repository-wide glob independently
  for every requested code, and should emit a per-code progress/result line.
- implementation progress: `jlc_twin.py` now fetches each unique LCSC code only
  once per run, prints `completed/total`, current code, state, attempt budget,
  elapsed time, rolling ETA, backoff and whole-run budget, heartbeats while a
  child is silent, bounds every child and the complete batch, preserves the
  per-code cache, and prints a distinct resumable `TIMED-OUT` result. The live
  v4 rerun is the first production exercise; rotation-measure cache indexing
  and shared orchestration remain open.
- completion evidence required: deterministic fixtures for steady progress,
  transient retry recovery, a permanently failing item, a silent child process
  and resume from partial cache; journals report productive fetch time,
  backoff time and final coverage separately.
- history: 2026-08-12 — recorded during the first v4 manufacturing-twin run;
  the active process was left unchanged because its cache showed forward
  progress, but the missing telemetry was visible immediately. The first
  16-code rotation batch then spent 36 seconds CPU-searching cache roots in
  silence before reporting that only two requested models were available,
  confirming the same observability problem outside the network fetcher.
- history: 2026-08-12 — the JLC twin implementation and deterministic silent-
  child/cache-replay tests landed; 33/33 twin tests pass, including a fixture
  that heartbeats, times out in 0.25 seconds and emits the resumable command.
- history: 2026-08-12 — the Pluto RX2 8-way v4 canary isolated the same
  symptom in local compute: `cpwg_field_solver.py` used about 24 CPU cores but
  emitted no progress for its measured 35.724-second solve. The design result
  was clean; the observability contract was not. The stage is now assigned a
  measured 45-second performance budget and a 60-second process-group deadline
  through the bounded runner so silence produces heartbeats instead of an
  indefinite-looking shell.

## IMP-052 — preflight mutable catalog clients and distinguish compatibility from rate limits

- status: implementing
- observed: USB Hub 3S v4 JLC digital-twin fetch, 2026-08-12
- evidence: installed `easyeda2kicad` 1.0.1 sent its pinned Chrome/120
  User-Agent and EasyEDA's CloudFront returned HTTP 403. The same exact product
  endpoint returned HTTP 200 with Chrome/146. After twelve successful model
  fetches the newer identity also received 403, demonstrating a second state:
  burst/rate enforcement. Treating both as a generic retry consumed minutes
  and could never tell the operator whether waiting or upgrading was useful.
- intended landing point: before a batch, issue one bounded capability probe
  against the exact endpoint/client headers and classify incompatible client,
  transient service failure and mid-batch throttling separately. Keep the
  User-Agent/configuration repository-owned and overrideable; print the tested
  client identity. Apply a rate budget and adaptive backoff after a successful
  preflight rather than mistaking the first burst 403 for a permanent client
  failure. Never relabel any 403 as `NO-CAD`.
- implementation progress: a repository-owned compatibility wrapper patches
  only the upstream HTTP User-Agent (default Chrome/146, configurable through
  `JLC_TWIN_USER_AGENT`) without editing the installed package; `jlc_twin.py`
  selects it only for the real `easyeda2kicad` entry point, leaving test stubs
  untouched. Hermetic tests prove both behaviors. The separate one-request
  capability probe and explicit throttle classification remain open.
- completion evidence required: mocked old-UA 403/new-UA 200, mid-batch 403
  after successful fetches, recovery after declared cooldown, permanent 403
  and cache-only replay; production journal reports compatibility failures,
  throttled time and useful fetch time separately.
- history: 2026-08-12 — compatibility wrapper and selection tests landed after
  upstream issue #191/PR #190 identified the same User-Agent failure class;
  live C124196 then fetched successfully through the wrapper before burst
  throttling reappeared.

## IMP-053 — explicit catalog values outrank MPN-shape heuristics

- status: completed
- observed: USB Hub 3S v4 C23 source substitution, 2026-08-12
- evidence: the cheap source gate interpreted Panasonic MPN `16SVPF180M` as
  18 pF before consulting the repository's exact LCSC-code ledger, which
  correctly records C136277 as 180 uF. The rebuild stopped safely in 16.6
  seconds before TSX/KiCad generation, but the finding was false: a generic
  ceramic-value decoder had claimed authority over an electrolytic family.
- implemented: `bom_source_check.py` now gives an exact LCSC-code ledger value
  precedence over a value guessed from an MPN. Its ceramic decoder explicitly
  refuses Panasonic OS-CON `SVP*`/`SEP*` families rather than inventing a
  capacitance. A regression fixture proves `16SVPF180M` resolves to 180 uF and
  not 18 pF; the focused source suite passes 29/29 with two environment skips.
- general rule: measured, part-specific and code-specific records outrank
  syntax heuristics. A heuristic may fill an otherwise unknown field; it may
  never override an explicit authority, and an unrecognized family must be
  `UNKNOWN` rather than a plausible-looking number.
- history: 2026-08-12 — fixed at the first false pre-generation stop and
  replayed through the complete v4 source/electrical gate set.

## IMP-054 — generated reports must persist the final adjudicated state

- status: completed
- observed: USB Hub 3S v4 JLC digital twin, 2026-08-12
- evidence: `jlc_twin.py` correctly applied two evidence-backed library-absence
  adjudications in memory and exited zero, but had already written
  `twin_report.csv`. The durable CSV therefore retained transient
  `FETCH-FAILED` rows while the console reported success, and its footer still
  told the operator to retry absences already proven genuine.
- implemented: the report is now written only after adjudications have been
  applied. Its rows carry `ADJUDICATED-FETCH-FAILED`; resumable/retry guidance
  is printed only for still-unresolved statuses, while genuine library
  absences receive a distinct non-retry explanation. A regression fixture
  reads the emitted CSV, not merely the process exit code; the twin suite
  passes 34/34.
- general rule: every durable artifact is a serialization of the final state
  consumed by the verdict. If normalization, waivers or adjudication happen
  after collection, report generation must be the last pure step and tests
  must reopen the report from disk.
- history: 2026-08-12 — fixed before release staging; the v4 twin report was
  regenerated and now agrees with its successful console verdict.

## IMP-055 — register exact 3D model attachment geometry before placement freeze

- status: implementing
- observed: USB Hub 3S v4 and Pluto RX2 8-way v5 JLC digital twins,
  2026-08-12 through 2026-08-14
- evidence: the final twin mounts 71 of 75 placed bodies. JLC's current library
  has no usable exact 3D body for four deliberately hand-soldered connectors:
  the upstream USB-C power input and three USB-A outputs. Their footprints,
  mechanical drawings, pin identities and courtyards are independently
  reviewed, but the digital twin cannot prove their shell height or enclosure
  interference. Discovering this only after routing makes a package swap
  disproportionately expensive.
- follow-up evidence: Pluto RX2 8-way v5 named KiCad 10's exact GCT USB4105
  STEP in J1's footprint and `kicad-cli pcb render` exited successfully, yet the
  resulting image contained bare J1 lands because `${KICAD10_3DMODEL_DIR}` did
  not resolve in that headless process. Visual inspection caught the missing
  body before routing; a project-local hash-bound copy referenced through
  `${KIPRJMOD}` rendered correctly. Availability on disk and a plausible model
  path therefore do not prove render-time body coverage.
- follow-up evidence: Pluto RX2 8-way v5's first SMA render showed complete
  plated holes beside every connector even though the exact Amphenol footprint
  and all nine mating-face datums were dimensionally correct. The converted
  EasyEDA WRL had lost the native model's XY registration; swapping only to the
  native exact-code STEP put all four legs under the body without changing one
  pad or anchor. A rendered body count would still have passed this defect: the
  body existed, but it was in the wrong coordinate frame.
- decisive evidence: the v0.1.2 Pluto twin then produced a visually plausible
  green/magenta overlay after `mount_anchor` removed the 1.796-mm repeated-pad
  centroid error. That result was still not physical registration evidence:
  the renderer drew the internally misregistered converted JLC WRL and the
  analytic expectation was derived from that same WRL. They agreed with each
  other while disagreeing with the footprint and native exact-code STEP. An
  independent native-STEP render disagreed with the WRL-derived expectation by
  about 4.05--4.10 mm in body centre and 1.54 mm in outward extent. For J2,
  the converted-WRL body also missed the signal-pad centre and protruded about
  3.4 mm beyond two non-mating courtyard edges. The current v0.1.2 overlay is
  therefore a renderer self-consistency witness, not an approved mechanical-
  registration witness, and must be superseded before release evidence relies
  on it.
- root cause: the pipeline treated three distinct claims as one. `P-MODEL`
  proves that a model token resolves and produces a non-empty body.
  `A-RENDER` proves that final pixels agree with the mounted model and camera.
  Neither proves that the model's internal mechanical frame agrees with the
  footprint, physical attachment field or manufacturer datum. The existing
  catalog `MODEL-REG` bounding-box comparison is not sufficient for
  asymmetric or edge-mounted bodies, and a subjective asymmetry waiver can
  hide an origin error.
- refactor decision: retain `P-MODEL` as the model-availability gate and
  narrow `A-RENDER` to renderer fidelity. Add an independent
  `P-MODEL-REG` gate for physical model-to-footprint registration. The
  authority used to form the registration expectation must not be the same
  converted mesh under test. A pass in one gate must not be described as a
  pass in either of the other two.
- registration authority order: prefer the exact manufacturer's native STEP
  plus mechanical drawing; then a provenance-bound, previously registered
  package model; then a datasheet-derived body envelope and attachment datums.
  A catalog or converted WRL is a candidate/comparator, not the authority when
  it conflicts with native CAD or the drawing. Native STEP and converted WRL
  must receive separate hashes and separate receipts because conversion may
  change the internal origin while preserving a plausible body.
- intended landing point: after exact part selection and before placement,
  create one disposable origin-centred coupon for every unique
  `(footprint hash, model hash, transform)` tuple. Render bare top, populated
  top, front, side and isometric views with standardized scale and colours.
  Overlay pad copper, drill centres, courtyard/fabrication outline, model
  silhouette and declared physical landmarks. Emit numerical residuals and a
  human-readable registration card; approve it once and cache it by the tuple
  hash. Repeated instances on a board reuse that receipt, while any footprint,
  model or transform change invalidates it automatically.
- landmark contract: mechanically significant parts declare semantic anchors
  appropriate to the package, such as unique signal/reference pad, required
  attachment holes or lead centres, mating axis, body datum, polarity marker
  and permitted mating-edge overhang. Courtyard containment is the default;
  exceptions name the permitted edge and limit rather than waiving the whole
  comparison. Simple SMD packages may use body/lead overlap defaults, while
  asymmetric connectors require explicit drawing- or native-CAD-derived
  landmarks.
- diagnostic contract: every failure prints the complete transform stack
  (`model internal -> model scale/rotation/offset -> footprint local -> board
  -> camera`), the first failing landmark and its signed delta. Classify the
  result as `MODEL-MISSING`, `MODEL-WRONG-SOURCE`, `MODEL-INTERNAL-ORIGIN`,
  `MODEL-TRANSFORM`, `FOOTPRINT-DRAWING-MISMATCH` or `RENDER-CAMERA`; produce
  one focused coupon image and report instead of repeatedly rerendering the
  complete board.
- pipeline ownership: part freeze resolves and registers each unique critical
  model; placement permits only approved registration tuples; whole-board
  rendering checks instance rotation, mating direction and camera fidelity;
  the JLC twin compares manufacturing catalog geometry without overriding the
  approved mechanical model. Release requires registration receipts for all
  height-, polarity-, mating- or enclosure-critical references in addition to
  `P-MODEL` and `A-RENDER` receipts.
- relation to other improvements: IMP-093 remains responsible for retaining
  repeated physical pads and comparing their numbering-free geometry. Its
  `mount_anchor` can establish a rigid catalog-to-footprint transform, but it
  cannot certify a mesh's internal model origin. IMP-029 remains responsible
  for bounded catalog-model acquisition and caching; it must feed, not close,
  `P-MODEL-REG`.
- minimal implementation: a `pcb_model_register`-style command may initially
  use 2D silhouettes plus explicit human-authored attachment landmarks; full
  STEP feature recognition is not required. It writes a Markdown/HTML index
  with one row per unique tuple, source and hashes, transform, landmark/body/
  courtyard deltas, verdict and links to the standardized images. A single
  human approval is reusable only while all tuple hashes remain unchanged.
- partial implementation: `model_coverage_check.py` now independently reopens
  the saved board before modeled placement review and requires a renderer-
  resolvable non-empty body for every fitted, non-DNP, non-board-only
  footprint. The canonical full/reuse rebuild templates run it and persist the
  deterministic `model_coverage.json` report. `floorplan.yaml` may source-bind
  a package-correct file through `placement.patterns[].model_override`; the
  generator preserves the library model transform and refuses missing or
  ambiguous overrides. The clean fixture passes 22/22 and the known-bad
  removes its model after generation and fails 0/22. Pluto RX2 8-way v5 passes
  29/29 with eight provenance- and digest-pinned official KiCad package-model
  files covering 17 fitted refs.
- remaining: automated attachment-field/body registration and polarity-marker
  projection, coupon/receipt production, independent authority binding and
  hash-cache invalidation are not implemented. The native-STEP-versus-
  converted-WRL SMA failure therefore remains an explicit visual/mechanical
  review obligation; body coverage, `mount_anchor`, catalog bounding boxes and
  same-mesh pixel agreement must never close it.
- completion evidence required: known-present, genuine-absent and transient
  model-resolution fixtures; correct body with wrong internal XY origin; right
  XY with wrong rotation; correct body with wrong footprint drills; repeated
  pad labels; a symmetric body with wrong polarity; a conversion that changes
  origin; and the shared-source self-consistency false pass reproduced by the
  Pluto WRL/native-STEP pair. The clean fixture must prove the receipt is
  reused for repeated refs, and any footprint/model/transform hash change must
  invalidate it before placement or release.
- history:
  - 2026-08-12 — recorded after the v4 twin made exact model coverage
    measurable; project-level dossier review exists, shared preflight remains
    open.
  - 2026-08-13 — extended after v5 proved render exit zero can coexist with an
    unresolved exact-model token and a missing connector body.
  - 2026-08-13 — extended after the v5 SMA image proved body presence alone
    does not catch a format-conversion registration error.
  - 2026-08-13 — implemented the independent fitted-body resolver gate,
    source-bound override, canonical stage wiring and red fixture; retained
    `implementing` because automated model registration is still open.
  - 2026-08-14 — refactored availability, renderer fidelity and physical
    registration into separate claims after the corrected Pluto twin exposed
    a shared-source false pass. Defined an independent, hash-cached per-part
    registration receipt as the remaining implementation target.

## IMP-056 — population evidence must separate automated and manual bodies

- status: completed
- observed: USB Hub 3S v4 release audit, 2026-08-12
- evidence: the twin correctly broadened its mechanical population from 70 JLC
  CPL placements to 75 total installed bodies by adding five declared manual-
  install parts. Four manual connector models were genuinely absent, so its
  honest aggregate was 71/75. `policy_audit.py` then called that aggregate
  "CPL placements" and failed A-BODY, even though the actual JLC population was
  70/70. The producer and consumer were each locally reasonable but disagreed
  about the denominator's meaning.
- implemented: `missing_models.txt` now persists three counters: aggregate
  bodies, `CPL bodies mounted`, and `manual bodies mounted`. A-BODY grades the
  contractual CPL counter when present while the aggregate/manual deficits
  stay visible for mechanical review and first-article disposition. Historical
  reports fall back to the old aggregate format. Twin and policy known-bad
  fixtures prove an empty-CPL/manual-body case and a 2/2-CPL plus 0/1-manual
  case independently.
- general rule: when a verification population is a union of sets owned by
  different processes, persist every constituent denominator. Never make a
  consumer infer "placed", "assembled" or "installed" from one aggregate.
- history: 2026-08-12 — completed before v4 release staging; current evidence
  states aggregate 71/75, JLC CPL 70/70, manual 1/5.

## IMP-057 — validate a relocated release archive in its own dependency context

- status: implementing
- observed: USB Hub 3S v4 release staging, 2026-08-12
- evidence: the live project passed exact KiCad DRC at 0 violations,
  0 unconnected items and 0 schematic-parity findings. The first DRC run over
  the copied `07_releases/.../source/` board instead reported three
  `lib_footprint_issues`: its release-only `fp-lib-table` shadowed KiCad's
  complete `Package_SON` library with an incomplete one-footprint directory,
  so U4-U6 could not resolve `Texas_DRC0010J`. A live-project validation could
  never expose that packaging defect because it resolved the system library.
- implementation progress: the v4 staging archive now maps `Package_SON` the
  same way as the live project and reruns DRC from the relocated source tree.
  The archived board passes 0/0/0 and its SHA-256 is byte-identical to the
  frozen routed board. The result is shipped as
  `verification/standalone_archive_drc.json`.
- intended landing point: promote relocated-source validation into the shared
  release gate. After copying source and rewriting any project-local library
  paths, run KiCad DRC/parity from inside the staged archive, reopen the JSON,
  require all three finding sets to be empty, and check the staged board hash
  against the live frozen board. Also enumerate every `lib_id` used by the
  board and prove its footprint resolves under the staged `fp-lib-table`;
  copied but unused libraries must not create false confidence.
- completion evidence required: known-bad fixtures for an absent library, an
  incomplete same-name library that shadows a valid system library, and a
  relocated custom-library path; a clean fixture must prove both exact board
  identity and zero standalone findings.
- history: 2026-08-12 — project-level read-back landed during v4 staging;
  shared release-contract promotion and hermetic fixtures remain open.

## IMP-058 — multi-format evidence is one atomic result, not adjacent files

- status: proposed
- observed: USB Hub 3S v4 release staging, 2026-08-12
- evidence: the staged `stock_check.json` and `stock_check.txt` carried the
  accepted C23 substitution C136277 / 16SVPF180M, but `stock_check.csv` still
  carried rejected C369910 / 160AV5K181M0606C. A-STOCK passed because release
  freshness correctly reads the canonical JSON; M-DEPEND then exposed that
  C136277 had no release-internal CSV resolver and was passing only through
  the mutable live `02_parts/16SVPF180M` dossier. Each file looked valid in
  isolation and all three shared a basename, which made adjacency appear to be
  provenance.
- project correction: reran `jlc_stock_check.py` once against the current
  strict 40-line BOM with `--out` and `--json` in the same process, capturing
  stdout as the text form. The new CSV/JSON/text set agrees on every code; live
  stock remains PASS 40/40 and C136277 reports 1052 catalog units.
- intended landing point: every producer that emits several representations
  writes them into a temporary result directory with one run ID and one input
  hash, validates pairwise key-field equality, then atomically promotes the
  complete set. Release staging copies the declared bundle, never three
  independent globs. A release gate must cross-check the exact LCSC set and
  core facts across BOM, stock JSON, stock CSV and text; a canonical form may
  decide the verdict, but disagreement in a secondary form still fails the
  archive.
- completion evidence required: known-bad mixed-generation JSON/CSV, missing
  member, duplicate code and current-code/old-MPN fixtures; a clean producer
  run must reopen all written files and prove the same input hash, row set and
  verdict before promotion.
- history: 2026-08-12 — v4 archive corrected before seal; shared atomic-bundle
  writer and cross-format release gate remain open.

## IMP-059 — preflight the publication parser's review identity before seal

- status: implementing
- observed: USB Hub 3S v4 publication gate after v0.6.0 seal, 2026-08-12
- evidence: all four routed reviews were exact-board/hash-bound and SOUND, and
  release freshness graded both required red-team verdicts. Publication still
  rejected three reviews because their `subject:` values said `USB Hub 3S v4`
  rather than containing the repository's exact slug `usb-hub-3s-v4`. The pin
  review happened to use the slug and passed. Review quality was not the
  defect; a machine identity field had been left encoded as human prose and no
  pre-seal gate exercised the downstream parser.
- project correction: preserve immutable v0.6.0 and obtain three append-only,
  independent exact-board publication reseals with canonical subjects. Seal a
  docs-only v0.6.1 successor whose fab/source/3d trees are byte-identical and
  whose named review files are verbatim copies of those append-only records.
- intended landing point: add a pre-seal review-header gate shared with
  `pcb_publication_gate.py`. Require a dedicated canonical `project:` slug or,
  until that schema lands, require the exact project slug inside `subject:`.
  It must also grade verdict vocabulary, full source-commit syntax, board hash,
  required lens coverage and archive byte identity against the staging release
  before immutability begins. Review commissions should receive the exact
  header block as structured input rather than translating a display name.
- completion evidence required: spaced-display-name/slug mismatch,
  wrong-neighbour project, missing subject, malformed commit, stale board hash
  and untracked-review fixtures; the pre-seal and publication readers must
  import one parser and return the same finding IDs.
- history: 2026-08-12 — narrow independent publication reseals commissioned;
  docs-only v0.6.1 correction in progress, shared pre-seal parser still open.
- history: 2026-08-14 — Pluto RX2 8-way v5 repeated the same exact-slug
  failure on two otherwise SOUND, hash-bound reviews because the mutable
  release staging path still did not call the publication parser. Preserve
  immutable v0.1.0 and correct the identity fields through a strict docs-only
  v0.1.1 successor; this is additional evidence that the shared pre-seal
  parser is required, not a project-specific convention.

## IMP-060 — publication must replay the release's declared freshness mode

- status: completed
- observed: USB Hub 3S v4 v0.6.1 docs-only staging, 2026-08-12
- evidence: `release_freshness_check.py` already had the correct strong mode
  for this correction: `--docs-only-supersede` asserts that every file under
  `fab/`, `source/` and `3d/` is byte-identical to the named predecessor while
  requiring release documents to differ. `pcb_publication_gate.py` discarded
  that release shape and always invoked ordinary freshness, where identical
  fabrication/PDF artifacts are deliberately treated as stale. Therefore a
  legitimate docs-only release could pass its normative seal gate and be
  structurally unable to pass publication.
- implemented: a superseding MANIFEST now declares `release_mode: docs-only`
  and an exact sibling directory in `supersedes:`. The publication wrapper
  parses those fields and composes the existing docs-only freshness mode. It
  fails closed on an unknown mode, a path-shaped predecessor, a missing
  predecessor or self-reference; a release with no mode retains ordinary
  freshness. The wrapper does not reimplement the identity comparison.
- completion evidence: `tests/t1_publication_gate.py` now proves the clean
  composition and the known-bad missing-predecessor refusal; 8/8 publication
  tests pass. V4's v0.6.1 gate additionally asserts the real 20-file fab,
  17-file source and one-file 3D trees against v0.6.0.
- general rule: an orchestration layer that composes a parameterized gate must
  preserve the subject's declared mode. Calling the same executable with
  weaker/default arguments is not composition; it is a different predicate.
- history: 2026-08-12 — completed before v0.6.1 seal.

## IMP-061 — exact-code manufacturing readiness before part freeze

- status: proposed
- observed: USB Hub 3S v4 nine-hour pipeline retrospective, 2026-08-12
- evidence: fabrication entry found four classes of fact after routing that
  were already properties of the selected exact LCSC codes. F1, J1-J4 and SW1
  were in the SMT CPL despite having drilled pads, no paste and catalog
  `assemblyComponentFlag=false`; C29 and C30 needed current-stock substitutes;
  C23's selected code had no usable supplier CAD record; and the first strict
  export lacked rotation authority for 22 placements over 16 codes. The board
  could remain copper-identical, but each late discovery forced source,
  evidence, schematic or review replay.
- intended landing point: after electrical qualification of a candidate and
  before the part is frozen into the schematic, run one bounded exact-code
  manufacturing-readiness gate. For every fitted ref/code it records:
  exact-code resolution and observation date; current stock evidence;
  JLC assembly eligibility; population class (`jlc_smt`, `manual`,
  `consigned`, or `dnp`) and its `assembly.yaml` disposition; supplier
  symbol/footprint/body state (`AVAILABLE`, `ABSENT`, or `TRANSIENT`);
  polarity; and rotation-authority readiness for every automatically placed
  package. No field may silently default from pad shape, package family or a
  neighbouring catalog code.
- pass semantics: mutable stock is a dated risk observation, not a permanent
  design fact. A genuine model absence or non-JLC part may pass only with an
  explicit mechanical envelope/local-model fallback and manual/first-article
  obligation. `TRANSIENT` never becomes `ABSENT`, and an automatically placed
  part without exact rotation authority remains unready.
- relationship: this composes the early portions of IMP-052 and IMP-055 with
  population and rotation readiness. It does not replace the final placed-
  board twin, same-day stock check or JLC uploader allocation check.
- completion evidence required: fixtures for stocked SMT/model-present,
  manual THT, genuine no-model with approved fallback, throttled catalog,
  missing rotation, and a code changed after preflight; both schematic and
  placement entry must refuse a stale or incomplete readiness record.
- history: 2026-08-12 — proposed from the nine-hour retrospective because the
  05:31-07:22 fabrication backtracks were cheaper to prevent at part freeze.
- follow-up evidence: Pluto RX2 8-way v5 independently checked all 13 JLC/LCSC
  codes and recorded distributor observations, but did not produce the
  contract-required composed Q-2SOURCE verdict before declaring exact-part
  closure. The 10V 4.7uF capacitor's recorded independent pool had zero local
  stock, and the 16V input capacitor recorded an exact listing without a
  qualifying stock count; neither prose entry can prove two active/orderable
  pools. The dossiers also committed `jlc_observed_stock` and second-source
  stock prose even though the parts contract assigns volatile stock/price only
  to TTL cache and dated generated sourcing evidence.
- completion evidence extension: schematic entry must consume one generated,
  parseable Q-2SOURCE/Q-COVER verdict for the exact candidate-BOM hash and
  board count. A dossier linter rejects volatile quantity/price fields, and a
  second-source identity with absent or insufficient stock remains a FAIL, not
  a narrative qualification. Candidate-BOM, assembly population and dossier
  code sets must be derived or checked for exact identity rather than maintained
  as three ungoverned lists.
- follow-up result: v5's first composed run failed 3/13. Removing the already
  rejected 10-V capacitor dossier, consolidating C1-C3 on the qualified 16-V
  code and adding current exact DigiKey product-page observations produced a
  parseable 12/12 Q-2SOURCE pass. Volatile stock prose was removed from all
  retained dossiers. This repairs v5 but does not yet implement the generic
  candidate-BOM hash/set-identity gate.
- diagnostic follow-up: in composed-pool mode the shopping tool still prints
  `FAIL NO-QUOTE` for non-required distributors (especially Amazon) before its
  final 12/12 PASS. Preserve each pool's coverage details, but label unavailable
  optional pools as diagnostics rather than gate failures so a successful
  composite verdict is not visually contradictory.

## IMP-062 — transactional generated-artifact bundles

- status: implementing
- observed: USB Hub 3S v4 nine-hour pipeline retrospective, 2026-08-12
- evidence: a KiCad render printed usage, exited zero and left an old PNG in
  place; stock JSON/TXT described C136277 while the adjacent CSV still
  described rejected C369910; and the twin CSV was initially written before
  adjudication even though the final in-memory verdict passed. These are one
  failure family: directory presence and process exit were mistaken for a
  coherent result.
- intended landing point: provide one shared producer transaction used by
  review exporters, catalog evidence, twins and release staging. It receives
  an input hash, producer command/version and declared expected outputs;
  writes into a new temporary result directory; requires every output to be
  newly created, non-empty and parseable; applies normalization/adjudication;
  reopens the durable files; compares key fields across representations; and
  atomically promotes the whole bundle with one run ID and completion time.
  Partial or failed attempts remain diagnostic workspaces and can never
  replace the current accepted bundle.
- relationship: this is the reusable mechanism needed to finish IMP-050 and
  IMP-058 and generalize IMP-054. Those incident-specific entries remain the
  acceptance cases; this entry owns the common transaction boundary.
- completion evidence required: known-bads for usage-plus-exit-zero with an
  old file, zero-byte output, missing bundle member, mixed-generation CSV/JSON,
  post-write adjudication and interrupted promotion; a clean fixture must
  prove atomic replacement and identical run/input identity in every member.
- history: 2026-08-12 — proposed from the nine-hour retrospective as the
  common fix for three apparently different release-evidence defects.
- history: 2026-08-12 — the shared schema-1 primitive and focused clean/bad
  fixtures landed in shadow form. It uses fresh sibling staging, a strict
  declared-output census, durable parse/read-back, manifest-last serialization
  and atomic directory promotion while preserving any accepted bundle on
  failure. Adoption by real producers and retained failed diagnostic
  workspaces remain open, so this entry is not complete.

## IMP-063 — complete pre-seal release rehearsal

- status: proposed
- observed: USB Hub 3S v4 nine-hour pipeline retrospective, 2026-08-12
- evidence: mutable staging exposed an incomplete `Package_SON` library only
  when DRC ran in the relocated archive; cross-format read-back then exposed a
  stale stock CSV; after v0.6.0 was immutable, publication rejected three
  human display-name subjects that did not carry the canonical project slug;
  and the v0.6.1 attempt showed that the publication wrapper discarded the
  declared docs-only freshness mode. The first two were caught before seal,
  while the latter two unnecessarily required a superseding release.
- intended landing point: add one canonical rehearsal command over the fully
  populated but still mutable release staging directory. It must run from the
  relocated `source/` dependency context; resolve every used footprint;
  reopen DRC/parity and every generated report; cross-check BOM, CPL,
  population and stock code sets; validate expected-output/hash manifests;
  parse review identity, verdict, commit, board hash, lens coverage and archive
  byte identity with the exact parser imported by publication; and replay
  freshness using the MANIFEST's declared release mode and predecessor.
- boundary: the rehearsal exercises every publication predicate that can be
  known from project and staging bytes. The final diff-aware repository
  publication gate still runs after the seal because source ancestry,
  candidate-head selection and branch protection are genuinely post-seal
  facts. Passing rehearsal is not permission to skip that boundary.
- relationship: this composes the shared completion work in IMP-057,
  IMP-058 and IMP-059 and consumes the mode preservation completed by
  IMP-060. It must reuse their readers rather than reimplement them.
- completion evidence required: replay the original v0.6.0 display-name
  mismatch as a pre-seal known-bad; fixtures for footprint-library shadowing,
  stale secondary evidence, malformed review identity, wrong board hash,
  missing predecessor and unsupported release mode; a clean staged initial
  release and docs-only successor must both pass before a seal commit exists.
- history: 2026-08-12 — proposed from the nine-hour retrospective to make
  inexpensive metadata and packaging findings cost a staging edit, not an
  immutable supersede.
- history: 2026-08-14 — Pluto RX2 8-way v5 passed its lower-level release and
  freshness gates but post-seal publication rejected a prose value in the
  reserved `release_mode` field, two non-canonical review subjects and a
  material BRIEF edit after the stamped source commit. All were knowable in
  mutable staging. This recurrence promotes the rehearsal from an efficiency
  improvement to a required release-safety control; implementation remains
  open.

## IMP-064 — early warning plus late authoritative recheck

- status: implementing
- observed: USB Hub 3S v4 nine-hour pipeline retrospective, 2026-08-12
- evidence: moving every check earlier would reduce rework but would be unsafe
  if the early observation were treated as permanent authority. Supplier
  stock and APIs change; placement changes body interactions; routing changes
  realized via/copper capacity; release copying changes dependency resolution;
  and publication depends on the final repository delta.
- intended landing point: declare lifecycle pairs for mutable or realized
  facts. The early member prevents expensive downstream work; the late member
  authorizes the final claim. At minimum:
  - exact-code stock at part selection, then same-day uploader/allocation check;
  - model availability before placement, then full placed-board twin;
  - declared via/process/current boundaries before routing, then exact-board
    process census and series-transition measurement;
  - generated-output postconditions at production, then release-bundle
    manifest/read-back;
  - canonical review headers at commission and staging, then the final
    repository publication gate;
  - live-project DRC during design, then relocated-archive DRC before seal.
- schema requirement: each pair names the fact owner, observation timestamp or
  immutable subject hash, maximum useful age where applicable, the stage it
  blocks and the later authoritative recheck. An early pass cannot satisfy a
  later claim; a late failure points back to the earliest causal stage.
- completion evidence required: orchestration fixtures prove all early checks
  precede expensive consumers and all late checks remain present; a stale
  stock observation, post-placement model mismatch, realized via shortfall and
  post-seal publication mismatch must each fail at their proper boundary.
- history: 2026-08-12 — proposed from the retrospective to codify "shift
  left, do not weaken the final gate."
- history: 2026-08-12 — the schema-1 fact-pair core landed with semantic/raw
  identities, exact invalidator census, optional early freshness and explicit
  prevention/authority roles. Early PASS is structurally unable to authorize
  a final claim; late evaluation accepts no early result and only the declared
  current authority can authorize. Real stock/model/via/release adapters and
  orchestration placement remain open, so this entry is not complete.
- follow-up evidence: Pluto RX2 8-way v5 had two honest source-authority
  exceptions at part freeze: Amphenol's current drawing endpoint returned HTTP
  403, and the locally cached STM32 data sheet was Rev 4 while current online
  facts were cross-checked against Rev 5. Prose correctly deferred footprint
  and release authority, but no typed lifecycle record made those precise
  future blockers visible to orchestration.
- lifecycle extension: manufacturer-document authority uses an early/late
  pair too. Part selection may record `CURRENT`, `STALE`, or `DEFERRED` with
  exact document identity, retry budget, fallback grade and first blocked
  stage; footprint approval and pin review require hash-bound local authority,
  and release rechecks the current revision. Repeated fetch failure is a
  visible bounded state, never an unbounded retry and never an implicit pass.

## IMP-065 — critical-path telemetry and cheap-first scheduling

- status: implementing
- observed: USB Hub 3S v4 nine-hour pipeline retrospective, 2026-08-12
- evidence: measured route races took about 9-10 seconds, canonical layout
  seals about 33-39 seconds and strict JLC export about 0.3 seconds. Human
  review dominated elapsed time, one review broadened scope without producing
  a witness, and the first digital-twin fetch took roughly eleven mostly
  silent minutes. The pipeline felt locked even though routing and local
  producers were healthy.
- intended landing point: every orchestration stage emits machine-readable
  spans with stage/gate name, immutable subject, work class (`local`,
  `network`, `backoff`, `review_wait`, or `operator_wait`), start/finish,
  elapsed time, cache hit/miss, result and resumable command. A stage summary
  reports the actual critical path separately from aggregate subprocess time.
  Within dependency constraints, schedule cheap static and deterministic gates
  before network work and human review. Never reorder a weaker check to stand
  in for a later authoritative one.
- relationship: IMP-049 owns reviewer closure, IMP-051 owns heartbeat/retry
  behavior inside long external operations, and IMP-014 owns progress-channel
  noise. This entry owns cross-stage timing and gate-order feedback so future
  boards can see where time was actually spent.
- completion evidence required: a deterministic orchestration fixture with
  overlapping local/network/review spans computes the right critical path;
  summaries distinguish productive fetch from backoff and reviewer wait; a
  template-order test proves source-only gates precede TSX, external fetch and
  independent review where their inputs permit.
- history: 2026-08-12 — proposed from the retrospective after measured timing
  showed that optimizing the router would not address the experienced delay.
- history: 2026-08-12 — schema-1 shadow infrastructure now records bounded
  stage execution with work-class/start/finish/elapsed/log evidence, and a
  dependency registry recomputes after each choice so newly unblocked cheap
  work precedes already-runnable network/review work. Real-stage declarations,
  cross-stage critical-path aggregation and canary shadow equivalence remain
  open, so this entry is not complete.
- history: 2026-08-12 — cross-stage aggregation now distinguishes observed
  wall envelope, summed stage work, subprocess work and the deterministic
  dependency-duration critical path, with separate local/network/backoff/
  review/operator totals and cache/status counts. Real-stage span adapters and
  USB Hub/Pluto shadow traces remain open, so this entry is not complete.
- history: 2026-08-12 — the first real legacy adapters landed in
  non-authoritative form: exact-driver-hash-bound stage catalogs, a pure
  completion observer and a dedicated-channel xtrace mapper. A detached
  disposable-worktree exercise measured USB Hub 3S v4 reuse failing
  diagnostically at pre-route review after about 11.4 seconds (41 trace
  records) and legacy Pluto RX2 8-way reuse failing at seven anchored courtyard
  overlaps after about 2.0 seconds (20 records). Neither run hung, but neither
  completed, so equivalence and any authority migration remain open. This
  legacy Pluto observation is not the Pluto RX2 8-way v4 sealed canary required
  by ADR-0008.
- history: 2026-08-12 — a repeat with absolute Bash source identities exercised
  the strict source-line adapter itself. USB produced a fully mapped 23-stage
  failure prefix (36 top-level trace records, no unmapped executable command)
  at the same review gate after about 14.3 seconds; Pluto produced a fully
  mapped three-stage failure prefix (15 top-level records, no unmapped command)
  at the same board-generation collision after about 1.3 seconds. This closes
  trace-map plumbing, not canary equivalence: the not-reached tails and both
  design blockers remain explicit.
- history: 2026-08-12 — after replacing the legacy Pluto bbox-only courtyard
  false positive with native polygon confirmation (IMP-066), a disposable
  reuse run observed all 12 catalog stages in 7.29 seconds. Stitch/fill was the
  longest stage at 3.798 seconds; the first honest stop is now the final
  postcheck at 45 DRC violations / 15 unconnected / 0 parity. This closes the
  legacy trace tail but not a green canary or shadow equivalence.
- history: 2026-08-12 — the distinct sealed-project Pluto RX2 8-way v4 reuse
  canary first exposed two cheap source-contract debts (explicit zero
  differential-pair applicability and provenance on 26 non-pin seed-via
  banks), then completed all 22 declared stages green in 139.91 seconds:
  DRC 0/0/0, fence coverage 22/22 and RF length coverage 8/8. During that run,
  stitch/fill reported useful pass progress while the 35.724-second CPWG solve
  was silent despite about 24-core utilization; that measured stage now owns a
  budget, deadline and heartbeat. This establishes one complete v4 legacy
  observation, not shadow-plan/result equivalence or authority migration.
- history: 2026-08-12 — after the bounded solver adapter landed, a final
  disposable reuse run completed all 22 stages green in 94.94 seconds with no
  unmapped command. The solver recorded 6.579 seconds, the configured 45/60
  second budget/deadline and a durable terminal state; the earlier 35.724-
  second measurement remains the conservative sizing observation.

## IMP-066 — native geometry must confirm broad-phase findings

- status: completed
- observed: legacy Pluto RX2 8-way reuse-canary replay, 2026-08-12
- evidence: the generator's anchored-courtyard gate reported seven collisions,
  but KiCad DRC reported zero courtyard violations. All seven transformed
  courtyard polygons are disjoint: the six radial SMA pairs have about
  1.140 mm clearance and `R_T2`/`R_T1` has about 0.350 mm, even though their
  axis-aligned bounding boxes intersect. Moving these reviewed anchors would
  have damaged an electrically-derived RF floorplan to appease an
  approximation.
- general rule: bounding boxes, raster extents and convex envelopes are useful
  broad-phase filters, never final collision evidence. A geometry gate may
  reject only after the authoritative tool's transformed native shapes confirm
  overlap or touch; diagnostics may still report the bounding-box window for
  localization. The same principle applies to rotated bodies, board outlines,
  keepouts, apertures and model-registration checks.
- implementation: `skills/kicad-pcb/scripts/generate_board_generic.py` now
  filters anchored pairs by bounding box and then grades KiCad courtyard
  polygons with `SHAPE_POLY_SET.Collide`. The PCB-design authoring guidance
  makes exact confirmation normative.
- completion evidence: `tests/t1_generate_board.py` regenerates the real Pluto
  floorplan and proves the exact seven pairs have intersecting boxes but
  non-colliding polygons. Existing known-bad fixtures still prove that a true
  same-coordinate or anchored-courtyard overlap fails loudly.
- history: 2026-08-12 — completed during the legacy canary blocker-removal
  wave; fresh board generation and the 13-measurement project audit both pass
  without a Pluto source edit.

## IMP-067 — scaffolds must never copy executable example values

- status: proposed
- observed: Pluto RX2 8-way v5 clean-room commission, 2026-08-12
- evidence: before any schematic existed, the new project's live rule files
  contained plausible executable examples for another board: a 3S-LiPo/
  LM5116 power tree, cook/load-cell netclasses and route target, a five-board
  assembly declaration, and unrelated electrical invariants. YAML parsing
  could not distinguish these examples from project decisions. A downstream
  command could therefore grade or act on coherent but foreign intent.
- general rule: examples belong in contracts, references, fixtures or files
  explicitly marked non-executable. A project initializer must emit only
  project identity plus null/empty fail-closed sentinels until commission or
  part selection supplies each value. No copied example row may become a live
  project declaration merely because it parses.
- intended landing point: refactor project scaffolding so each generated live
  YAML is produced from a minimal sentinel template; add a cheap pre-TSX
  provenance/content gate that rejects foreign project names, example markers,
  undeclared non-null design values and active rows without a local decision
  source. Keep full annotated examples in skill-owned reference files.
- completion evidence required: initialize two unrelated fixture projects and
  prove their live rule files contain no example MPN, net, board path,
  population quantity or invariant; inject one foreign active row in each
  rule family and prove the pre-TSX gate names it and fails; prove an explicitly
  source-linked local decision passes.
- recommendation: fix the initializer/process before the next new board. The
  v5 instance was cleaned immediately because leaving it in place could have
  contaminated later generation; no TSX/KiCad artifact had yet been created.
- history: 2026-08-12 — v5 power, protection, invariant, netclass, assembly and
  route files were replaced with project-specific fail-closed sentinels. The
  reusable initializer and generic rejection gate remain open.

## 2026-08-12 nine-hour retrospective traceability

This table records the complete shift-left review so the recommendations are
not recoverable only from chat or one project's journal. “Early” is the first
stage with enough information to reject or disposition the issue; the final
authoritative recheck remains governed by IMP-064.

| Observed issue | Earliest useful boundary | Canonical improvement |
|---|---|---|
| Manual/THT parts entered the SMT CPL | exact-code part freeze | IMP-061, with population reporting in IMP-056 |
| C23/C29/C30 stock or CAD suitability was discovered after routing | exact-code part freeze | IMP-052, IMP-055, IMP-061 |
| Rotation authority was first demanded by strict export | exact-code part freeze, confirm after placement | IMP-061 |
| Exact connector bodies were unavailable after routing | before placement freeze | IMP-055, IMP-061 |
| A promoted route inherited stale placement/via-process geometry | before placement review | IMP-040 |
| DRC-clean forced via banks lacked current capacity | architecture declaration, then realized route | IMP-041, IMP-064 |
| Type-VII intent was board-wide or not Gerber-addressable | manufacturing architecture before routing | IMP-039 |
| A generic MPN decoder overruled exact catalog value | static source preflight | IMP-053 |
| A renderer exited zero but left a stale PNG | artifact producer transaction | IMP-050, IMP-062 |
| Stock CSV disagreed with JSON/TXT | atomic evidence production and staging read-back | IMP-058, IMP-062 |
| Twin CSV disagreed with the final adjudicated verdict | final-state serialization before exit | IMP-054, IMP-062 |
| An independent reviewer widened scope for hours and wrote nothing | externally bounded review commission | IMP-026, IMP-049 |
| Release-only footprint-table shadowing broke standalone resolution | mutable relocated staging | IMP-057, IMP-063 |
| Human display name failed canonical publication identity | review commission and mutable staging | IMP-059, IMP-063 |
| Publication discarded docs-only freshness semantics | orchestration mode tests before seal | IMP-060, IMP-063 |
| Healthy stages appeared locked because work class was invisible | every orchestration boundary | IMP-051, IMP-065 |
| Parseable rule files failed canonical readers or passed with zero graded rows | source-only preflight before generation | IMP-001, IMP-045, IMP-069 |
| Hand-maintained stage booleans claimed completion without fresh gate receipts | every stage transition | IMP-069 |
| Two-source proof was distributed across prose and volatile stock was committed in dossiers | exact-code part freeze | IMP-061, IMP-064 |
| A broad clean-room search surfaced explicitly excluded legacy design material | commission and every discovery command | IMP-070 |
| A 500 ms marker followed by the same state for 5 ms is observably 505 ms | control-protocol lock before firmware and analysis | IMP-071 |
| Generated PDF evidence was treated as text because it contained no NUL byte | project scaffold and staging preflight | IMP-072 |
| A regulator calculation passed against a locally chosen operating ceiling mislabeled as a package limit | source-bound capture before power analysis | IMP-043, IMP-045 |
| Manufacturer documents were inaccessible or a locally cached revision was stale | source authority at part freeze, then final recheck | IMP-042, IMP-051, IMP-064 |

Recommended execution order for future boards:

1. Commission the product, manufacturing, qualification and clean-room
   boundaries; enforce the allowed discovery scope mechanically (IMP-070).
2. Close exact-code manufacturing readiness—including the composed
   two-source gate—before part freeze (IMP-061, IMP-064).
3. Run every applicable canonical source-only schema, bound and authority
   gate before TSX or reviewers, then derive stage readiness from their fresh
   receipts (IMP-001, IMP-042, IMP-045, IMP-053, IMP-069).
4. Generate and electrically grade the schematic, then run presentation
   preflights before bounded human readability review (IMP-044, IMP-046,
   IMP-048, IMP-049).
5. Generate placement, prove promoted-route/model compatibility, then run
   bounded placement review (IMP-040, IMP-055).
6. Route and remeasure realized copper, via process and ampacity; generate
   review evidence transactionally (IMP-039, IMP-041, IMP-062).
7. Build complete mutable staging and run the pre-seal rehearsal (IMP-063).
8. Seal immutably, refresh the beacon, then run the final repository-level
   publication gate and retain the external JLC/first-article order holds.

## IMP-068 — coordinate protection before freezing downstream voltage ratings

- status: proposed
- observed: Pluto RX2 8-way v5 exact-parts stage, 2026-08-13
- evidence: the initially selected protected-input capacitor was rated 10 V,
  while the exact SMBJ6.0A maximum clamp is 10.3 V before the required 20%
  coordination margin. The source-stage surge gate rejected it before TSX or
  schematic generation; replacing it with the exact 16-V code made the path
  pass with unchanged topology.
- general rule: a TVS selection and every part exposed behind it form one
  interface proof. Before an exact-code freeze, compare the source envelope,
  admitted waveform, series impedance/current limiting, TVS standoff and
  maximum clamp, PCB overshoot allowance, and every downstream recommended/
  absolute voltage rating—including capacitors. Nominal source voltage and TVS
  part name alone are insufficient.
- intended landing point: make the early protection-path gate a mandatory
  dependency of exact-code freeze, before TSX/symbol/footprint work. Diagnostics
  should name the weakest exposed part and show `clamp x margin` against its
  rating, then rerun automatically when that exact code changes.
- completion evidence required: fixtures proving rejection of a capacitor
  below clamp, a regulator below clamp, a waveform mismatch, and an omitted
  exposed part; a coordinated 16-V-capacitor path must pass. The same proof must
  remain mandatory in the later authoritative schematic/release rechecks.
- recommendation: generic process change soon; no v5 repair is pending because
  the existing early gate caught and corrected this instance before schematic
  entry.

## IMP-069 — derive stage readiness from canonical gate receipts

- status: implementing
- observed: Pluto RX2 8-way v5 pre-schematic audit, 2026-08-13
- evidence: `requirements.yaml` and the project status described architecture,
  interface and exact-parts work as complete, while the canonical electrical-
  invariant and RF-contract readers rejected their files, the assembly reader
  raised an exception, the label-survival check passed vacuously with zero
  graded pin-map rows, and the project-state reader could not find the required
  findings ledger. The selected commands that had been run were green, but the
  declared stage was not green under all applicable canonical consumers.
- general rule: a stage-complete boolean records desired state, not evidence.
  Readiness must be derived from fresh, subject-bound receipts for every
  applicable canonical gate. A pass with an unexpected zero denominator,
  an uninvoked rule family, a missing ledger, an exception or a stale subject
  leaves the stage ungraded and blocks its consumers.
- intended landing point: define a stage registry that enumerates applicable
  rule families, canonical reader commands and expected minimum coverage. Each
  reader emits a bounded result with the input hash, validator version,
  numerator/denominator, evidence paths and terminal state. `project_state.py`
  derives maturity only from those receipts, and generation refuses `FAIL`,
  `ERROR`, `STALE` and `UNGRADED` alike.
- completion evidence required: orchestration fixtures must reject an omitted
  reader, a manually true completion flag, a missing findings ledger, a stale
  receipt and a nominal pass with zero rows; a clean fixture with all expected
  families and nonzero coverage must advance exactly one declared boundary.
- recommendation: address before resuming v5 schematic generation. This is the
  umbrella fix that prevents several individually cheap contract mismatches
  from becoming a misleading stage-level green claim.
- implementation progress: v5 now has a canonical `findings.yaml`, a dated
  source-audit receipt with coverage and timing, a 50-file byte-identity
  checkpoint, and a derived `DRAFT` maturity
  instead of relying on the old completion booleans. Generic readers now emit
  bounded/non-vacuous source verdicts for the failures that exposed this gap,
  and the rebuild template invokes them before TSX. The generic stage registry,
  subject hashes, freshness checking and receipt-to-`project_state.py`
  composition remain outstanding; therefore this is not complete.
- implementation note: source-phase policy currently imports PCB machinery and
  emits KiCad property assertions even though its two source rows pass. A stage
  registry should phase-lazy-load dependencies so source receipts are quiet,
  fast and free of irrelevant PCB initialization.
- history:
  - 2026-08-13 — proposed from the v5 false-green checkpoint.
  - 2026-08-13 — implementation began with bounded source readers, a v5
    findings ledger, a dated source receipt and a 50-file checkpoint; three
    rule families were promoted into the schema/reader ratchet.

## IMP-070 — mechanically scope clean-room filesystem discovery

- status: proposed
- observed: Pluto RX2 8-way v5 clean-room research, 2026-08-13
- evidence: a repository-wide search surfaced filenames and text snippets from
  explicitly excluded earlier Pluto projects. No legacy design artifact was
  intentionally opened or copied and the provenance record was corrected, but
  the breach showed that a prose instruction cannot constrain an otherwise
  broad discovery command.
- general rule: clean-room scope is a command-boundary property. Allowed roots,
  denied roots and permitted reusable process material must be machine-readable
  and enforced for filesystem discovery and reads; prompt wording and operator
  memory are not controls.
- intended landing point: commission an allowlist of new-project and generic
  skill/process roots plus explicit deny patterns for legacy subjects. Route
  searches through a wrapper that validates working directory and arguments,
  rejects repository-wide expansion and path traversal, and emits an auditable
  discovery receipt. Any breach stops the stage and records exactly what became
  visible before work continues.
- completion evidence required: fixtures must permit the commissioned project
  and reusable skills, reject an older project, a symlink escape, a traversal
  path and a broad repository search, and produce a stable incident record for
  each denied attempt.
- recommendation: implement before the next clean-room project; for v5, retain
  the disclosed provenance incident and avoid any further broad searches.

## IMP-071 — derive observable protocol timing from executable state schedules

- status: implementing
- observed: Pluto RX2 8-way v5 dwell-protocol review, 2026-08-13
- evidence: the declared 500 ms marker body was immediately followed by a 5 ms
  guard in the same switch state, so a downstream observer sees one contiguous
  505 ms interval. Cycle duration, capture requirements and distinguishability
  were then checked manually from prose and duplicated derived values.
- general rule: a receiver observes merged state runs, not semantic labels such
  as `marker`, `dwell` or `guard`. Observable windows, unique dwell signatures,
  cycle time and minimum capture must be derived from one atomic state schedule;
  the decoder must treat any unmatched or incomplete observation as unknown.
- intended landing point: add a conditional control-protocol checker for boards
  using timing-coded switching. It merges adjacent identical states, applies
  controller and estimator error bounds, computes observation windows and
  cycle/capture limits, and rejects handwritten derived-value drift, ambiguous
  merged intervals, overlapping windows and insufficient capture duration.
- completion evidence required: fixtures must cover the corrected v5 schedule,
  the original 500+5 ms adjacent-state ambiguity, overlapping tolerance
  windows, a truncated capture and a no-signal/reset interval; only the fully
  distinguishable schedule may pass.
- recommendation: land before firmware generation or downstream decoder work.
  It is conditional process machinery, not a burden for boards without an
  observable timing protocol.
- implementation progress: `control_protocol_check.py` now derives contiguous
  observable runs, active-state windows, marker duration, cycle time and
  guaranteed capture from the atomic schedule; it rejects derived-value drift,
  overlapping windows and decoder contracts without explicit unknown outcomes.
  The canonical rebuild template runs it before TSX and executable fixtures
  cover a clean v5 contract, the original 500+5 marker mismatch, overlap,
  derived drift and no-signal decoder behavior. Schema 2 now adds one versioned
  profile identity and project-confined consumer paths;
  `control_profile_codegen.py` generates the STM32 header and decoder JSON from
  that same contract and `--check` rejects either consumer when stale. The v5
  `fast20-v1` revision-1 profile proves disjoint 20/23/26/30/34/39/44/50 ms
  dwell windows, an 85 ms observable marker, a 386 ms frame and a 772 ms
  arbitrary-phase guaranteed-capture minimum. Actual firmware/decoder behavior
  and an explicit truncated-capture end-to-end fixture remain before closure.
- history:
  - 2026-08-13 — proposed from the adjacent ALL_OFF marker/guard ambiguity.
  - 2026-08-13 — implementation began with a generic source checker, template
    gate and regression suite; v5 passes at marker 505 ms/cycle 2160 ms.
  - 2026-08-13 — added versioned two-consumer code generation and moved v5 to
    the user-requested fast20-v1 profile; source, header and decoder now fail
    closed on any one-sided timing edit.

## IMP-072 — classify committed binary evidence in the canonical scaffold

- status: proposed
- observed: Pluto RX2 8-way v5 source-evidence staging, 2026-08-13
- evidence: two valid generated Yageo PDF files contained no NUL byte, so Git's
  heuristic treated them as text and `git diff --check` emitted thousands of
  whitespace diagnostics. A project-local `.gitattributes` entry declaring
  `*.pdf binary` restored bounded, useful review output.
- general rule: the repository must declare the representation of committed
  evidence formats whose bytes are not meaningfully line-reviewable. Tool
  heuristics are not a stable content contract.
- intended landing point: include a canonical `.gitattributes` file in the
  project scaffold and initializer copy list with `*.pdf binary`. Add other
  evidence types only when their review/merge behavior is explicitly known;
  continue to verify content with hashes and purpose-specific readers.
- completion evidence required: initialize a fixture, stage a valid PDF with no
  NUL byte and prove diff/check output remains bounded with no text-whitespace
  diagnostics; prove the file hash survives scaffold, copy and archive steps.
- recommendation: low-risk and inexpensive; land in the next scaffold update.

## IMP-073 — grade human symbol pin functions, including unused pins

- status: proposed
- observed: Pluto RX2 8-way v5 schematic readability review, 2026-08-13
- evidence: the first generated schematic connected every used STM32 pin to
  the correct net and passed 129/129 pin-map assertions, 30/30 electrical
  invariants, 33/33 component parity and zero-error ERC. It nevertheless gave
  several unused U2 pins the wrong human function names: PC14/PC15, PA8,
  PA11/PA9, PA12/PA10 and PB6 were mislabelled. The fresh visual/datasheet
  review caught the defect; the checkpoint was discarded, corrected against
  ST DS13866, regenerated and re-reviewed before PCB work.
- general rule: connectivity parity proves physical pad-to-net identity, not
  that the delivered schematic tells a human the truth about each pad. A pin-
  function check must cover connected and intentionally unused pins alike and
  compare the generated symbol's visible function to the exact part dossier or
  an explicit reviewed alias. Unconnected does not mean unimportant.
- intended landing point: before rendering and review, compare every generated
  symbol pin number/function with `02_parts/*/part.yaml pins:`. Require exact
  normalized identity or a board-local alias row that names its evidence and
  purpose suffix (`_NC`, role alias, alternate-function choice). Report the
  refdes, physical pin, visible text and dossier text for each mismatch.
- completion evidence required: a fixture with correct connected nets but the
  v5-style wrong unused labels must fail; correct exact labels must pass;
  intentional aliases and alternate-function abbreviations must fail unless
  explicitly declared and then pass without weakening physical-pin parity.
- recommendation: implement before the next new schematic. The v5 instance is
  repaired and hash-bound, so no current project fix remains.
- history: 2026-08-13 — proposed from the first v5 human-review rejection.

## IMP-074 — ADR gate applicability must be typed, not inferred from prose

- status: proposed
- observed: Pluto RX2 8-way v5 schematic gate, 2026-08-13
- evidence: `electrical_invariants.py --adr-coverage` reported `E-ADR OK: 0/0`
  even though ADR-0001 selects the complete RF topology, ADR-0002 selects the
  controller/control topology, ADR-0003 selects the protected power topology,
  and 30 executable invariants cite those decisions. The gate discovers
  protection/topology ADRs by keywords in titles/tags; the accepted v5 titles
  use descriptive names that do not match its regex.
- general rule: whether an ADR must emit executable assertions is schema, not
  natural-language classification. A zero denominator is meaningful only when
  the commissioned ADR set explicitly says that none is applicable.
- intended landing point: add closed front-matter metadata such as
  `assertion_domains: [topology, protection, control]` to the ADR contract and
  make E-ADR consume it. New ADRs must declare at least one domain or explicit
  `none` with a reason. Retain the title heuristic temporarily as a migration
  warning, never as the authoritative denominator.
- completion evidence required: fixtures must classify descriptive titles
  without keywords, reject a missing domain, reject an applicable ADR with no
  invariant, accept a cited applicable ADR, and accept explicit `none` only
  with substantive rationale. A migrated v5 run must report a nonzero cited
  denominator.
- recommendation: implement as a schema migration before relying on E-ADR for
  another newly commissioned board. V5's direct 30-invariant and independent
  topology reviews close the local risk, so changing accepted ADR metadata is
  not required inside this schematic checkpoint.
- history: 2026-08-13 — proposed from the v5 gate's misleading 0/0 coverage.

## IMP-075 — bind mechanical dimensions to exact document identity and feature role

- status: proposed
- observed: Pluto RX2 8-way v5 pre-placement connector review, 2026-08-13
- evidence: the `901-143-6RFX` dossier named a plausible Amphenol asset but the
  asset was drawing `901-40129`, not the selected MPN. The resulting draft
  geometry mixed a 1.50-mm RF-contact hole with a 1.52-mm value from the wrong
  part. The exact current drawing `SMA6252A2-3GT50G-50` Rev C instead requires
  one 1.50-mm centre hole and four 1.70-mm ground holes. This was caught before
  footprint or PCB generation; the dossier and evidence were corrected.
- general rule: an authoritative domain is not enough. Before any dimension is
  transcribed, resolve the exact product page to an exact document identity,
  verify visible MPN/document/revision, retain or explicitly qualify hash-bound
  bytes, and check current PCNs. Mechanical facts must be keyed by physical
  feature role and datum (`rf_contact_hole`, `ground_leg_holes`, mating face),
  never stored only as an unlabeled list of dimensions.
- intended landing point: add a pre-footprint document-identity gate that
  compares selected MPN, product-page drawing title, local PDF visible identity,
  dossier `doc_id`/revision/hash and applicable PCNs. Add a typed footprint
  contract whose role-labelled source dimensions are measured against realized
  pads, drills, courtyard, board-edge datum and mating direction before
  placement generation.
- completion evidence required: fixtures must reject a correct-vendor/wrong-
  part drawing, swapped centre/ground hole sizes, an unlabeled diameter list,
  an unmatched local hash, and a geometry-changing PCN without reapproval; an
  exact drawing plus no-form/fit-change origin PCN and matching realized
  footprint must pass with a nonzero feature count.
- recommendation: implement before the next custom connector footprint. The v5
  instance is corrected, but its realized-footprint measurement and render
  review remain mandatory before placement approval.
- history: 2026-08-13 — proposed after D12 triggered the exact drawing audit.

## IMP-076 — reconcile exact package geometry and logical pin identity in the first-board preflight

- status: proposed
- observed: Pluto RX2 8-way v5 first unrouted placement, 2026-08-13
- evidence: the first board generated in under one second and was mechanically
  collision-free, but the immediate placement DRC exposed four
  0.1944-mm GCT land-to-NPTH gaps against a provisional 0.200-mm generic hole
  rule, two 0.150-mm SOT-553 land gaps against a 0.200-mm default netclass, and
  decorative SMA silk crossing its own pads/edge. In the same cheap pass,
  P-PINMAP exposed that TSX's numeric USB logical ports had not yet been
  explicitly reconciled with GCT's alphanumeric physical contacts. All were
  source-only corrections; the next board passed 0 placement violations and
  117/117 declared physical identities before any routing work began.
- general rule: immediately after the first exact-footprint board exists, run
  one bounded preflight that (1) measures each package's own copper-to-copper,
  copper-to-hole and silk-to-mask/edge minima, (2) compares those minima with
  the adopted board/netclass rules, and (3) reconciles dossier logical pins,
  producer pins and realized pad identities. A manufacturer land below a
  generic rule must require an exact-package local override with evidence; it
  must not emerge later as unexplained route-grind noise.
- intended landing point: make the canonical placement stage run
  `pin_map_check.py`, exact intra-footprint geometry census and placement DRC
  as one first-board bundle before route config/rule preparation or human
  rendering. Emit a machine-readable report naming the package, exact feature
  pair, measured gap, controlling rule, local override and evidence path.
- completion evidence required: fixtures must reproduce the GCT NPTH gap, the
  SOT-553 0.150-mm land gap, an unjustified blanket rule relaxation, missing
  numeric-to-alphanumeric aliases, and self-clipping connector silk. The first
  four must fail with exact feature identities; evidence-backed package-local
  overrides and complete aliases must pass without weakening unrelated nets.
- recommendation: implement before the next custom-footprint project. V5 has
  already run the bundle manually and is clean, so no route-stage fix remains.
- history: 2026-08-13 — proposed from the bounded v5 placement grind.

## IMP-077 — reconcile footprint and symbol metadata before schematic-parity DRC

- status: proposed
- observed: Pluto RX2 8-way v5 keyed-SWD placement, 2026-08-13
- evidence: the exact J11 custom footprint initially carried non-empty KiCad
  `Datasheet` and `Description` properties while the generated schematic
  symbol carried empty values. Connectivity, physical-pin mapping, pad
  separation and placement geometry all passed, but immediate pre-route KiCad
  schematic-parity DRC correctly stopped first on `Datasheet` and then on
  `Description`. Two otherwise identical one-second placement regenerations
  were needed to expose the fields serially. The searchable human description
  remains in the footprint `descr` and the authoritative provenance remains in
  the part dossier, so clearing the duplicate instance properties repaired the
  exact board without losing evidence.
- general rule: symbol/footprint standard fields are parity-bearing design
  data, even when they are not electrical. A project footprint template must
  either inherit the exact generated-symbol value or leave the field empty;
  it must not independently author a second value that is expected to survive
  schematic-to-PCB parity.
- intended landing point: add a source/first-board lint that compares
  `Reference`, `Value`, `Datasheet`, `Description` and other parity-bearing
  footprint properties with the generated symbol contract before full DRC.
  Report every divergent field in one invocation. Keep descriptive search text
  in `descr`/`tags` and document authority in `part.yaml` unless the producer
  has one explicit, shared field source.
- completion evidence required: fixtures with two simultaneous divergent
  fields must report both at once; inherited-identical and deliberately empty
  properties must pass; the check must not erase or weaken dossier evidence.
- recommendation: low-cost lint before the next custom footprint. The v5
  instance is repaired and now reports zero schematic-parity findings.

## IMP-078 — run source-resolvable tier/routing preflight before expensive stages

- status: proposed
- observed: Pluto RX2 8-way v5 keyed-SWD placement, 2026-08-13
- evidence: after the exact schematic had been generated and reviewed and the
  placement had passed geometry, pin-map, landability and DRC checks,
  `tier_preflight.py` stopped before routing because
  the tier-derived effective `route.common.clearance=0.09 mm` was below the
  applicable 0.20 mm DRC floor and the tier-derived 0.15 mm drill through the
  declared 1.6 mm board gives 10.667:1, above
  the selected JLC advanced-tier 10:1 PTH aspect limit. It also warned that the
  0.50 mm legalization clearance is below the derived 0.53 mm rescue-via
  requirement. All three facts were derivable from already-authored
  `route.yaml`, net rules, stackup and fab-tier data before TSX generation or
  human schematic review.
- general rule: split routing preflight into a source-resolvable phase and an
  exact-board phase. Run the source phase with other cheap schema/electrical
  gates before foreign producers and reviewers; repeat the full phase after
  placement for facts that genuinely require realized pads and board setup.
- intended landing point: add `tier_preflight.py --phase source` (or an
  equivalent pure checker), invoke it before the TSX build in the canonical
  drivers, and retain the present pre-route invocation as the authoritative
  exact-board recheck. Diagnostics must distinguish source-known failures from
  placement-dependent checks and preserve the same effective-rule derivation.
- completion evidence required: the v5 clearance/aspect fixture must fail
  before a producer is called; a placement-dependent seed-via fixture must be
  deferred explicitly and fail at the exact-board recheck; clean designs must
  pass both phases without weakening the late authority.
- recommendation: implement early because it saves review cycles without
  changing any electrical or manufacturing rule. V5's local inputs are now
  corrected; this improvement changes when the conflict is discovered, not
  what values are acceptable.
- v5 disposition: explicitly selected the strictest adopted 0.20-mm class
  clearance for every router wave and JLC's preferred 0.45/0.20-mm ordinary
  via. Nominal aspect is 8:1 and remains 8.8:1 at JLC's published +10% board-
  thickness tolerance. Legalization clearance is 0.58 mm, derived from the
  actual 0.20-mm route drill plus twice the 0.19-mm hole clearance rather than
  merely accepting the checker's tier-minimum 0.53-mm warning threshold.
  R-PREFLIGHT now reports 0 FAIL / 0 WARN without changing the track-free
  board hash. The early source-phase implementation remains open.

## IMP-079 — derive compact floorplans from topology and operational connector envelopes

- status: proposed
- observed: Pluto RX2 8-way v5 compact placement, 2026-08-13
- evidence: the first board used a 100 x 100 mm four-edge ring because mapping
  the PE42482 cyclic pin order directly around the complete perimeter made
  crossing-free RF fan-out obvious. It passed every placement gate, but the
  square was not a component-density requirement. Before routing, the same
  cycle was cut between ANT4 and ANT5 and mapped onto a five-top/two-per-side
  open U. The resulting 90 x 65 mm board retains zero proper straight RF-
  corridor crossings, four M3 holes, three fiducials, keyed SWD and USB-C,
  while reducing area by 41.5%, the common straight span from 36.501 to
  14.502 mm and the maximum throw span from 46.580 to 35.676 mm. All exact-
  board placement, model, pad, DRC, escape and tier gates remain green.
- general rule: floorplanning must distinguish a topology proof, a geometric
  packing minimum and a comfortable operational target. Before freezing the
  first outline, test whether each cyclic/radial net order can be cut or folded
  onto an open boundary without crossings. Size connector banks from mating
  bodies, installed cable nuts, tool approach, mounting torque paths, RF
  launch/fence space and labelling—not courtyard non-overlap alone.
- intended landing point: add a pre-placement floorplan worksheet/checker that
  consumes exact connector body width/datum, requested edge grouping, minimum
  service/tool pitch, mounting-hole envelopes and ordered critical endpoints.
  It should emit at least two candidates: `geometric_minimum` and
  `comfortable_target`, plus board area, endpoint order, straight-corridor
  crossing count, connector/body gaps and any unmodelled service envelope.
  The human brief must select the target before detailed placement review.
- completion evidence required: a cyclic nine-port fixture must show the
  closed-ring and open-U embeddings, reject a smaller courtyard-clean layout
  whose declared tool envelope overlaps, and reproduce the v5 90 x 65 mm
  comfortable candidate with zero crossings. A non-cyclic connector bank and
  an enclosure-locked board must demonstrate that the checker reports no
  unjustified compaction opportunity.
- recommendation: implement before the next connector-heavy RF or power board.
  V5 is already compacted before routing, so no immediate corrective work is
  owed; the remaining exact-route and human placement reviews are unchanged.
- history: 2026-08-13 — proposed after the user challenged the conservative
  square and the open-U remap removed 41.5% of board area without weakening a
  placement gate.

## IMP-080 — emit and measure RF fences from routed centrelines

- status: completed
- observed: Pluto RX2 8-way v5 deterministic route preparation, 2026-08-13
- evidence: the generic stitch backend's `stitch_grid` accepts only orthogonal
  `x`/`y` lattice axes. It can provide ordinary plane stitching but cannot
  intentionally follow the nine straight/diagonal/bent RF polylines. The
  shared `fence_pitch.py` correctly measures saved geometry rather than
  trusting requested sites, but its RF net list is hard-coded to one legacy
  naming scheme and therefore cannot grade v5's `RF_COMMON`/`RF_ANT1..8`
  routes. Calling either mechanism an RF-fence proof would be a false green.
- general rule: an RF fence is a relationship to realized transmission-line
  geometry. The source must name the RF nets, flank band, lateral target,
  maximum along-route aperture, endpoint return structures and via geometry.
  Emission must sample the actual saved centreline, collision-check both
  flanks, and refuse uncovered apertures; an independent gate must then measure
  the surviving vias/PTH returns from the saved board.
- implementation: `route_and_stitch_generic.py` now has a generic
  `stitch.route_fence` pass. It reconstructs each exact saved straight-track
  chain, derives the net denominator/layer/maximum pitch from `rf.yaml`, grades
  explicit package/connector endpoint structures, reserves constrained bend
  sites before straight-span filling, collision-checks both flanks through the
  shared fabrication-aware via primitive, and refuses every unresolved
  aperture. A plated return beside a bend is credited to every adjacent finite
  route segment it physically serves; forcing it onto only one nearest
  projection created a fictitious corner opening.
- independent implementation: `fence_pitch.py` was generalized without
  sharing emitter state. It reopens the saved board, accepts a contract or
  explicit net list while retaining its legacy positional CLI, reconstructs
  and fail-closes each simple chain, counts realized GND vias/PTH posts, grades
  lead-in/interior/run-out apertures outside only geometry-proven endpoint
  spans, and writes a machine-readable report. `rf_contract_check.py` now
  reconciles the layout net denominator, route cross-section, via/stub policy,
  guided-wavelength pitch, lateral offset and endpoint evidence before layout.
- local-minimum evidence: the first disposable v5 emitter closed 3/18 flanks;
  endpoint structures raised that to 12/18 and the 0.50-mm same-net spacing
  policy to 16/18. Reducing spacing to 0.46 mm made the greedy result worse at
  14/18. Both survivors were symmetric 45-degree inner bends where legal vias
  placed just before and after the corner consumed its remaining placement
  window. Corner-first anchors plus multi-segment physical credit close the
  same saved geometry deterministically rather than retrying or rerouting it.
- completion evidence: focused clean/known-bad fixtures cover a bent chain,
  both flanks, endpoint-inclusive failure/pass, idempotence and saved-board
  measurement. V5 realizes 394 new 0.45/0.20-mm GND vias, including 22 corner
  anchors. The independent report grades 18/18 arm-sides PASS; worst aperture
  is 1.3979 mm against the 1.4000-mm guided-wavelength bound. KiCad DRC remains
  0 violations / 0 unconnected / 0 schematic-parity findings and all four
  filled zones survive the saved-file read-back.
- recommendation: make this contract mandatory before routing on every RF
  board that relies on a coplanar via fence. Define the exact route nets,
  stackup/reference plane, guided-wavelength pitch, lateral band, via geometry
  and endpoint return structures before copper, but emit and independently
  grade only after the actual centrelines exist. Keep ordinary plane stitching
  separate and never let an attempted-site count certify an RF fence.
- sources: Analog Devices' MMIC layout note recommends CPWG ground holes at
  `lambda/20` or less; its RF/mixed-signal PCB guidance recommends fences on
  both CPWG sides and an unbroken underlying plane. V5 derives a conservative
  1.40 mm maximum from its retained JLC effective dielectric constant at
  5.9 GHz and records the calculation in `03_src/rules/rf.yaml`.
- history: 2026-08-13 — completed before exact-board RF PCB review. The
  rejected 0.25/0.15-mm via fallback and RF reroute experiments were not
  carried into the board; the solution preserves the approved RF copper and
  the ordinary 0.45/0.20-mm JLC via geometry.

## IMP-081 — deterministic UUIDs for route preparation

- status: completed
- observed: Pluto RX2 8-way v5 D16 repeatability check, 2026-08-13
- evidence: two consecutive preparations from identical source reported the
  same 14 keepouts, 29 seed segments and 44 plane-rescue items, yet produced
  different r0 SHA-256 values. A text diff showed only fresh KiCad UUIDs. The
  route progress contract authenticates the exact r0 hash, so rerunning prep
  would make a valid bounded route unresumable even though no geometry moved.
- general rule: every deterministic stage that creates KiCad objects must seed
  KiCad's UUID generator from a stable artifact namespace before the first
  object is minted. Deterministic values with random identities are not a
  reproducible input to hash-bound downstream work.
- implementation: `route_and_stitch_generic.py cmd_prep` now seeds
  `pcbnew.KIID.SeedGenerator` from CRC32 of `<source-board>:route-prep` before
  creating keepouts, seed copper or rescue copper. Existing source objects
  retain their identities. `tests/t2_route_stitch.py` prepares a fixture with
  keepouts, deterministic seed copper and early pad rescue twice and requires
  byte equality.
- completion evidence: the focused regression passes; two v5 preparations
  complete in 0.56 s and 0.53 s and are byte-identical at SHA-256
  `d598d305f5d75dd5bcebdd8320ef0949ca787bd0f5c7e53a573c66c995e726de`.
- history: 2026-08-13 — discovered and completed at the D16 reflection pause,
  before KRT or route-progress provenance existed.

## IMP-082 — require executable budgets for datasheet short/close layout obligations

- status: proposed
- observed: Pluto RX2 8-way v5 exact pre-route placement renewal, 2026-08-13
- evidence: the TPD2E2U06 dossier said to place the clamp "immediately behind"
  J1 and the TPS7A24 dossier said to put both 4.7-uF capacitors "directly at"
  the LDO pins. The generated board passed collision, courtyard, pad-separation,
  escape and placement DRC, while `policy_audit --phase placement` reported
  P-ADJ N-A because neither prose sentence supplied a machine-readable
  denominator. A fresh layout reviewer then measured U4 about 8.33 mm from J1
  and C1/C2 about 4.24/4.61 mm from U3 and correctly blocked routing. After the
  source repair, four partner-specific budgets are all graded: U4.3→J1.A5
  1.922 mm of 4.0, U4.5→J1.B5 3.028 mm of 4.0, U3.1→C1.1 1.875 mm of 2.5,
  and U3.5→C2.1 1.875 mm of 2.5. Placement DRC remains 0 violations / 39
  expected unrouted items / 0 parity findings.
- general rule: a manufacturer layout statement containing `short`, `close`,
  `near`, `immediately`, `directly at`, or an equivalent critical-placement
  obligation must not be satisfied by `layout.notes` alone. Before board
  generation it must become a typed `keep_short` or `adjacency` budget with an
  explicit anchor pin, partner ref/role, numeric limit, measurement definition
  and source citation. If no defensible number exists, record an explicit
  HUMAN obligation that prevents the automated row from appearing applicable
  or complete; never let the constraint disappear into an N-A denominator.
- intended landing point: extend the part-schema/source preflight to classify
  critical-layout language and reject prose-only obligations unless paired
  with an executable budget or explicit human-gate record. Make the placement
  summary surface `declared/graded/unreached` counts prominently and treat an
  all-N-A P-ADJ result as a review warning whenever in-scope dossiers contain
  critical-layout language. Keep the exact-board P-ADJ evaluator as the late
  authoritative measurement.
- completion evidence required: fixtures must reject prose-only ESD-clamp and
  regulator-bypass instructions, a budget with no anchor, a broad-rail nearest-
  any-part false pass, and a partner name that resolves to nothing. They must
  accept the four v5 partner-specific budgets with a 4/4 denominator, accept a
  properly typed human-only obligation without claiming a machine pass, and
  preserve current boards whose layout notes contain no critical adjacency
  instruction.
- recommendation: implement before the next exact-placement project. The v5
  instance is repaired now, so the generic lint is not a blocker for its
  bounded control/power route; the fresh board-bound layout review remains the
  authority for this revision.
- history: 2026-08-13 — proposed after a fresh reviewer caught a real layout
  defect that every existing geometric gate passed because the datasheet intent
  existed only as prose.

## IMP-083 — make no-via-in-pad intent executable at every routing wave

- status: completed
- observed: Pluto RX2 8-way v5 first control/power routing attempt,
  2026-08-13
- evidence: one bounded five-wave KRT chain completed quickly but left the
  same `SW_V1` endpoint open that all three subsequent race candidates left
  open. The candidates also escaped boxed component lands with seven new
  ordinary vias directly in U1/U2/J1/C6 SMD pads, including 0.30/0.15-mm
  geometry below the board's authored 0.45/0.20-mm ordinary-via contract. The
  prepared route independently exposed a second form of the same semantic
  defect: with `via_in_pad: false`, plane-pad rescue for one J11 GND land put
  its adjacent same-net via in another long J11 GND land. KRT exited zero in
  every case; only the later quick/census work rejected the chain.
- general rule: `via_in_pad: false` is a geometry invariant, not a suggestion
  to an emitter. Each stochastic wave must compare its output with its exact
  input and refuse every newly-created via whose centre lies in any SMD land.
  Vias already present in the input remain source-owned, so a separately
  reviewed filled/capped exposed-pad field is allowed without weakening the
  rule. A deterministic adjacent-via placer must likewise reject all SMD-pad
  landing sites, including foreign pads on the same net. When a legal escape
  is topologically boxed, own the minimum package dogbone in source and leave
  only the unobstructed trunk to the router.
- implementation: `via_in_pad_guard.py` performs the exact input/output via
  comparison and records the offending via, pad, net, coordinate, size and
  drill. `route.forbid_new_via_in_pad: true` runs it after every successful
  KRT wave and before progress authentication or the next wave. The route
  driver now removes a stale `FINAL` marker before both single-chain and race
  attempts. `pad_rescue` rejects adjacent sites inside any SMD pad whenever
  `via_in_pad` is false. The schema contract names both new reader paths.
- completion evidence: the hermetic KRT fixture exits zero after creating a
  via in an SMD pad and the wave gate fails, records the exact finding and
  removes a planted stale `FINAL`; an independent review then found that an
  earlier preflight/config failure could still retain `FINAL`, so invalidation
  moved to the first `cmd_route` operation and a separate early-failure fixture
  now proves it. Fixtures also prove that source-owned vias already in the
  input are allowed, rejected waves do not enter authenticated progress, clean
  waves and both race lanes execute the guard, mask-only apertures are not
  mistaken for copper, and a two-pad same-net rescue emits an adjacent legal
  via without landing in either pad. The complete non-slow routing/stitch suite
  passes 108/108, including 47 known-bad fixtures. Schema-reader governance
  passes 616/616 with zero orphans and gate-contract audit passes 59/59.
  On v5, deterministic package/connector dogbones plus explicit J11 drops
  prepare byte-identically at SHA-256
  `cab54a0b9f9d304bdd9cf68c0d4ed756e8e93814dfe845db9de4e923756ca695`;
  the prep comparison reports zero newly-created via-in-pad and its DRC has
  zero copper/clearance/edge findings.
- recommendation: enable the wave guard on every new board whose assembly
  contract does not explicitly authorize router-created via-in-pad. Keep it
  opt-in for existing designs until their intentional source vias can be
  distinguished and reviewed; do not silently reinterpret legacy geometry.
- history: 2026-08-13 — completed before retrying v5 routing. The failed
  single chain and identical three-way race were retained as evidence rather
  than promoted or retried again.

## IMP-084 — site admission must honor realized pad-local copper and mask rules

- status: completed
- observed: Pluto RX2 8-way v5 first post-stitch full DRC, 2026-08-13
- evidence: two 0.45/0.20-mm GND grid vias were admitted 1.118 mm from 1-mm
  fiducials because `via_site_ok` used only the common 0.20-mm clearance. Each
  fiducial authored 0.60-mm local copper clearance and 0.50-mm solder-mask
  expansion. Full DRC reported two clearance, two hole-clearance and two
  solder-mask-bridge findings; the realized copper requirement was 1.325 mm.
- general rule: a geometry emitter's site predicate must evaluate the rules of
  every object it approaches, including per-pad copper clearance and mask
  expansion on each affected outer layer. Board/netclass defaults are only a
  floor, never permission to ignore an object's stricter local rule.
- implementation: `pcb_toolkit.py` caches each pad's local clearance and front/
  back realized mask expansion and applies them in copper, drill and via-mask
  collision probes. Bounding-box margins are per object rather than global.
- completion evidence: a known-bad fixture independently proves rejection by
  local copper clearance and by mask expansion. The final v5 lattice admits
  200 sites, rejects both fiducial-adjacent sites, and saved-board DRC is 0.
- recommendation: keep this in the shared toolkit and require every new via,
  tap, rescue and fence emitter to use the same predicate rather than a private
  board-default-only collision approximation.
- history: 2026-08-13 — completed before accepting the v5 post-stitch stage.

## IMP-085 — normalize overlap-only track/via joints before deleting barrels

- status: completed
- observed: Pluto RX2 8-way v5 R3.1 cleanup, 2026-08-13
- evidence: KRT stopped a 0.25-mm 3V3 track 0.100 mm from the centre of an
  existing 0.45-mm same-net via because the copper caps already overlapped.
  Removing that unused single-layer barrel would leave a cap-overlap-only
  joint rather than an explicit centreline node. A first endpoint-moving draft
  was rejected because pivoting a complete segment can change its whole copper
  envelope even when the moved cap stays contained.
- general rule: cleanup may remove an anchoring via only after every surviving
  connection is explicit. A normalizer may add a bridge only when the endpoint
  is otherwise free, net/layer agree, and the complete bridge capsule is
  contained inside copper that already exists. Do not pivot existing routes.
- implementation: `bridge_via_endpoints` adds a short same-net track from the
  free endpoint to the via centre under strict `distance + track_radius <=
  via_radius`; no geometric tolerance is allowed. `via_janitor` then removes
  only barrels attached on fewer than two copper layers.
- completion evidence: the focused fixture accepts a 0.100-mm exactly-contained
  bridge and refuses a 0.101-mm just-over-boundary bridge. Independent replay
  adds two bridges, removes 12 barrels and leaves R3.1 with two tracks sharing
  `(68.80,57.00)`, no via, zero opens and zero DRC findings. The routing/stitch
  suite passes 110/110 non-slow tests, including 48 known-bad fixtures.
- recommendation: retain this as a narrowly ordered pre-janitor normalization;
  do not generalize it into arbitrary endpoint snapping or gap healing.
- history: 2026-08-13 — completed and independently renewed P0/P1/P2=0/0/0.

## IMP-086 — run external mating-fact provenance before PCB generation

- status: proposed
- observed: Pluto RX2 8-way v5 post-stitch gate, 2026-08-13
- evidence: `BRIEF.md` had a `Mating fact-lock` describing the SMA cable
  boundary, but `03_src/rules/mates.yaml` was absent. `import_provenance_check`
  correctly failed D-MATE only after routing and stitch work had completed.
  The repaired machine copy references SMA gender, port order and RX absolute
  maximum from their single `spf/plutoplus_hardware` home and passes 3/3; it
  consumes no Pluto dimension and changes no copper.
- general rule: when the brief declares a foreign-hardware mating boundary,
  D-MATE/M-IMPORT is source governance and must run before schematic freeze or
  PCB generation. A late gate is still useful, but it should verify an already
  pinned fact-lock rather than discover the first missing declaration.
- intended landing point: add `import_provenance_check.py PROJECT` to the early
  source-governance stage and include `mates.yaml` plus the referenced SPF fact
  index/record hashes in the schematic checkpoint whenever the denominator is
  nonzero. Retain the final rerun for drift detection.
- completion evidence required: a project with a Mating fact-lock and no
  machine copy must stop before TSX/PCB generation; a board explicitly saying
  it does not mate remains a visible zero-denominator N-A; a valid informational
  cable boundary passes early and again at final layout without restating data.
- recommendation: implement before the next board that interfaces with
  externally designed hardware. V5's instance is fixed and not blocked.
- history: 2026-08-13 — proposed after the right gate ran at the wrong stage.

## IMP-087 — grade rerunnable density gates against realized saved geometry

- status: completed
- observed: Pluto RX2 8-way v5 RF-fence disposable rerun, 2026-08-13
- evidence: the already-complete ordinary 5-mm GND stitch grid caused
  `stitch_grid` to emit zero duplicate vias, then falsely failed its own
  `min: 80` contract as `0 < 80`. The first run had safely realized 200 grid
  sites; the gate was measuring work performed in this invocation rather than
  the board property the minimum was meant to require.
- general rule: a rerunnable stage's acceptance criteria must grade the
  realized saved result, not its mutation delta. `added`, `removed`, cache-hit
  and retry counters are useful telemetry, but they cannot stand in for
  population, density, connectivity, fill or coverage requirements. This
  applies beyond vias to thermal arrays, test points, zones, labels, model
  coverage and any resumable generator.
- implementation: `stitch_grid` still reports newly added vias separately,
  but its minimum now counts declared lattice sites served by realized
  same-net plated returns inside the same spacing window that suppresses a
  duplicate. It records `grid_sites_total` and `grid_sites_served`; a foreign
  blocker earns no credit. The existing impossible-minimum known-bad remains
  red.
- completion evidence: a new fixture realizes a grid, reruns the complete
  stitch pass, proves zero new vias, and requires the saved served-site
  denominator to remain green. On the fenced v5 rerun, zero duplicate grid
  vias and 200/234 realized served sites pass the unchanged `min: 80`; the
  complete stitch gate is clean.
- recommendation: audit every resumable `min`/`require: all` gate for this
  distinction before the next board. Prefer three explicit values in reports:
  `attempted or added this run`, `realized subjects graded`, and `required
  denominator`. Run this cheap idempotence fixture when a new emitter is
  introduced, before using it in an expensive board replay.
- history: 2026-08-13 — completed during disposable RF-fence promotion, before
  touching the real board.

## IMP-088 — seed deterministic identities across import and stitch

- status: proposed
- observed: Pluto RX2 8-way v5 layout-seal entry, 2026-08-13
- evidence: IMP-081 seeded route preparation, so identical source produces a
  byte-identical r0. The later `import_krt.py` and stitch passes still construct
  PCB tracks/vias without a stable KiCad UUID seed. A canonical rebuild can
  therefore reproduce identical copper and clean DRC while changing the board
  SHA solely through fresh object identities, invalidating exact-artifact RF,
  pin, render, topology and layout reviews.
- general rule: reproducibility ends at the last artifact-producing stage, not
  the first deterministic one. Every process that creates identity-bearing
  objects must derive a stage-specific seed from immutable input identity and
  preserve deterministic creation order. A geometry-only comparison may be a
  useful diagnostic, but it must not silently replace exact-byte provenance.
- intended landing point: seed KiCad's UUID generator in `import_krt.py` from
  the exact base-board plus promoted-chain identity, and in `cmd_stitch` from
  the exact imported-board plus route/stitch-contract identity. Record those
  seeds and input hashes in provenance, then require two clean full replays to
  produce byte-identical imported and post-stitch boards.
- completion evidence required: fixtures must replay import and stitch twice
  from byte-identical inputs, including tracks, vias, corner anchors, filled
  zones and fresh-interpreter barriers, and require byte equality. Changing
  one source track or stitch parameter must change the identity namespace;
  an idempotent rerun on the finished board must still emit no duplicates.
- recommendation: implement before the next routed board and before using a
  full rebuild as an exact-review recovery path. V5 should use the existing
  reviewed-commit layout-seal path now; changing producer identity policy
  after its exact board was reviewed would create avoidable subject churn.
- history: 2026-08-13 — proposed when the layout-seal rehearsal showed that a
  canonical rebuild could be geometrically correct yet stale every exact-board
  review for identity-only reasons.

## IMP-089 — treat same-net via-in-pad as a fabrication process

- status: completed
- observed: Pluto RX2 8-way v5 final layout red team, 2026-08-13
- evidence: exact board `0b8ab1962ef7` was DRC 0/0/0, P-PADSEP clean and RF
  fence 18/18, yet an ordinary 0.45/0.20-mm GND stitch via at
  `(42.50,77.50)` was centred inside keyed SWD connector J11.3's
  0.74 x 2.79-mm F.Cu/F.Mask/F.Paste land. Same-net copper overlap is legal,
  so DRC had no reason to object. The via was neither filled nor capped and
  could wick paste/solder from the connector joint. A final-chain-to-board
  `via_in_pad_guard.py` comparison reported exactly this one post-route hole.
- general rule: via placement needs two independent meanings. Electrical DRC
  decides whether copper may touch; assembly policy decides whether a drilled
  barrel may occupy an SMT land. Every ordinary grid, fence, rescue and repair
  emitter must refuse exact SMD-pad hits at its shared admission seam. Only an
  explicitly owned via-in-pad operation may opt in, and every realized
  via-in-pad must be filled+capped and selectable by an unambiguous fabrication
  family that does not include ordinary vias.
- landed in: `route_and_stitch_generic.py` now rejects ordinary stitch sites
  whose centres hit exact KiCad SMD copper, with explicit opt-in only for
  `pad_rescue.via_in_pad: true`. `via_process_check.py` independently scans the
  final board, refuses any unprotected via in an SMT land, refuses native
  fill/cap intent without an assembly contract, and proves protected versus
  ordinary drill-family separation at layout/fab entry.
- regression: `t2_route_stitch.py` places a same-net J11-like land directly on
  a declared grid site and requires the site to remain barrel-free;
  `t1_via_process.py` requires both the unprotected-via-in-pad and
  native-flags-without-order-contract fixtures to fail.
- project correction: v5 replay removes the single J11 grid via. The nine
  intended U1 EP holes are 0.45/0.25-mm filled+capped vias; all 629 ordinary
  route/stitch/fence holes remain 0.45/0.20 mm. JLC's published POFV guidance
  lists a 0.25-mm hole with 0.40-mm via diameter, so the selected protected
  0.45/0.25-mm family is within that published geometry and drill-distinct.
- history: 2026-08-13 — completed before layout seal after independent final
  pin and layout lenses both refused the otherwise-green exact board.

## IMP-090 — bind review freshness to declared stage dependencies

- status: proposed
- observed: Pluto RX2 8-way v5 corrected layout seal, 2026-08-13
- evidence: changing U1's final fabrication-via drill family in
  `floorplan.yaml`, its human dossier note, and `assembly.yaml` correctly
  invalidated layout/fabrication review. It also invalidated the pre-route
  schematic topology and PDF-readability witnesses solely because those
  witnesses hash the complete `02_parts` and design-rules bags. The schematic,
  netlist and PDF bytes were unchanged; the changed assembly/process fields
  are not inputs to either schematic lens. The gate failed loudly, which is
  safe, but required two unrelated review renewals and makes future users more
  likely to resent or bypass freshness checks.
- general rule: every review witness should declare the artifact and semantic
  source families its conclusion actually consumes. Freshness must fail on any
  consumed dependency change, but not on unrelated downstream fields. A broad
  whole-directory hash is a safe bootstrap, not a scalable final dependency
  model.
- intended landing point: add a versioned `review_dependencies` contract for
  each review kind. Build deterministic projections such as schematic
  topology = netlist + pin/electrical dossier fields + electrical/RF rules;
  schematic readability = PDF + net-label/pin-identity inputs; PCB layout =
  board + floorplan/routing/fab constraints; fabrication = exact outputs +
  assembly/process/source evidence. Store both the projection hash and its
  enumerated input list in the review.
- safety condition: unknown keys, an undeclared review kind, or a dependency
  extractor that cannot prove full coverage must fall back to the current
  broad hash, never silently narrow freshness. Regression fixtures must change
  one consumed and one unrelated field and require respectively STALE and
  STILL-CURRENT outcomes.
- recommendation: implement before the next board with frequent post-schematic
  sourcing/layout iterations. Do not refactor this during v5 final review; the
  bounded broad-hash renewal is safer than changing provenance semantics under
  an active seal.
- history: 2026-08-13 — proposed after the exact via-process correction made
  the stage-mismatch visible before layout seal.

## IMP-091 — freeze executable assembly-process ownership before placement export

- status: proposed
- observed: Pluto RX2 8-way v5 layout-seal entry, 2026-08-13
- evidence: `assembly.yaml` said J2-J10 would be wave-soldered by JLC *if* the
  uploader accepted C429844, otherwise hand-soldered. That advisory either/or
  left all nine paste-free THT connectors on the SMT CPL but declared neither
  the gate's executable `through_hole: {process, refs, evidence}` path nor a
  `not_assembled` hand-solder path. A-POP therefore found nine
  `CPL-NOT-SMT-PLACEABLE` defects only at final review, after routing and exact
  artifact reviews had already run.
- general rule: population ownership is a source decision, not an order-note
  afterthought. Before the first BOM/CPL export, every fitted paste-free drilled
  part must be assigned to a named purchased THT process, or declared
  `not_assembled` with its disposition and excluded from placement. Conditional
  prose must not allow one CPL to mean two mutually exclusive process plans.
- intended landing point: run A-POP/A-POS immediately after the first board and
  BOM/CPL candidate exist, before placement freeze and routing. Add an early
  source gate that rejects a drilled/paste-free fitted ref unless exactly one
  executable owner covers it. Treat an uploader-dependent fallback as a new
  release branch whose population set and CPL are regenerated, never as an
  in-place order-time edit.
- completion evidence required: a fixture with a THT connector on an SMT CPL
  and only conditional prose must stop before routing; the same fixture must
  pass with a complete purchased-process declaration, and independently pass
  when declared unassembled and absent from the CPL. A ref covered by both
  paths must fail as ambiguous.
- recommendation: implement before the next PCB. V5 now selects JLCPCB THT
  connector assembly as the required path; exact C429844 still needs the normal
  uploader allocation/process echo before payment, and refusal creates a
  separate hand-solder release.
- history: 2026-08-13 — proposed and corrected at v5 layout-seal entry, before
  the seal was minted.

## IMP-092 — make provenance source discovery honor declared source boundaries and ignore policy

- status: proposed
- observed: Pluto RX2 8-way v5 layout seal, 2026-08-13
- evidence: the first exact reviewed-commit seal attempt treated five generated
  two-byte files under `03_tscircuit/.tscircuit/cache/` as source inputs. The
  directory was already excluded by the project's `.gitignore`, its contents
  were tool cache rather than design authority, and the committed source was
  unchanged. Moving the ignored cache out of the project made the same sealed
  source pass without changing a design artifact.
- general rule: provenance must enumerate the declared authoritative inputs of
  a stage. Generated caches, editor state, lock files and build scratch must
  never silently join that authority merely because they appear below a broad
  source directory. A dirty or untracked *authoritative* input must still fail
  closed.
- intended landing point: centralize source discovery behind one policy-aware
  walker. It should consume explicit source roots, honor repository and
  project ignore rules for non-authoritative files, always exclude known tool
  cache/lock families such as `.tscircuit/`, and write the enumerated relative
  path list beside every source digest so unexpected membership is inspectable.
- safety condition: ignore rules must not be able to hide a path explicitly
  declared by a stage contract. Regression fixtures must prove that adding a
  cache file leaves the digest stable, adding an undeclared authoritative
  source fails discovery, and changing a declared-but-ignored source still
  changes the digest or fails loudly.
- recommendation: implement before the next layout seal. Until then, remove or
  relocate ignored generator caches before provenance generation and inspect
  the exact source-member list; do not weaken the reviewed-commit or clean-tree
  requirement.
- history: 2026-08-13 — proposed after the reviewed-commit seal was blocked by
  ignored tsCircuit cache bytes rather than a source or board delta.

## IMP-093 — compare repeated-pad catalog lands as geometry, not merged labels

- status: proposed
- observed: Pluto RX2 8-way v5 final JLC twin, 2026-08-13
- evidence: the exact C429844 catalog footprint and the manufacturer-derived
  901-143-6RFX footprint put all five holes at the same centres to 0.000 mm and
  use the same 2.40/2.80-mm copper diameters. The project preserves four
  distinct shell pins 2/3/4/5; JLC labels all four shell posts `2`.
  `jlc_twin.py` therefore compared one project pad 2 with the centroid of four
  JLC pad-2 instances, reporting a 1.796-mm `PAD-MISMATCH` and a false 3.59-mm
  `PAD-GEOM` delta. The tool correctly failed closed, but could not encode the
  one-to-many naming relationship and required 27 per-ref adjudicated finding
  rows for nine geometrically identical connectors.
- general rule: repeated pad numbers are a naming/multiplicity property, not a
  licence to collapse physical lands into one point. Land-pattern comparison
  must retain every physical instance and expose two independent results:
  numbering/pin-map agreement and numbering-free geometric agreement. A
  geometry pass must never be promoted into an electrical pin-map claim.
- intended landing point: add a deterministic multiset/assignment channel to
  `jlc_twin.py` for repeated labels. Compare complete pad clouds by position,
  shape, drill and layer after rigid transforms, report the winning residual
  and runner-up separation, and keep `PAD-MULTIPLICITY` visible. Permit an
  evidence-bound alias only for electrical identity; do not require an
  impossible one-to-many scalar `pad_alias` merely to measure geometry.
- completion evidence required: the C429844-shaped fixture must report five
  centres matched at 0.000 mm while separately naming the 2-versus-2/3/4/5
  convention and the real 0.10-mm drill delta. A fixture with one moved shell
  post must remain red, and a geometrically symmetric but electrically swapped
  polarized part must still require the independent polarity channel.
- recommendation: implement before the next board with multi-post connectors,
  exposed tabs or duplicated same-net pads. V5 is safely resolved by exact
  manufacturer evidence and retains its explicit uploader DFM gate; changing
  the matcher is not required for this board's release.
- history: 2026-08-13 — proposed after the strict final twin failed safely but
  represented a catalog numbering convention as two geometric failures.
- implementation progress: 2026-08-14 — the renderer and independent
  A-RENDER gate now consume an evidence-bound `mount_anchor` only after a
  whole-pattern fit fails. Each side's named pad must occur exactly once;
  invalid or duplicated datums refuse the run. A C429844-shaped known-bad
  fixture reproduces the old 1.796-mm centroid shift and proves the unique
  signal-hole 1-to-1 datum yields a zero-offset model while retaining the raw
  failed-fit evidence. This closes the false render displacement without
  claiming that numbering or full pad geometry agrees.
- remaining work: the numbering-free multiset/assignment channel described
  above is still open. It must match all five physical lands, report the real
  drill delta, stay red when one post moves and preserve the independent
  polarity channel before IMP-093 can be marked completed.

## IMP-094 — bind review contracts to the exporter artifact index

- status: proposed
- observed: Pluto RX2 8-way v5 fabrication entry, 2026-08-13
- evidence: `rf.yaml` named
  `06_build/fab/pluto_rx2_8way_v5-gerbers.zip`, while the strict exporter
  deterministically emitted
  `06_build/fab/pluto_rx2_8way_v5_gerbers.zip`. The PCB, plots and review intent
  were sound; one hand-typed hyphen made the exact-artifact RF review contract
  point at a nonexistent file. The mismatch was corrected before review and
  changed no fabrication bytes.
- general rule: a producer-generated artifact name is output metadata. A
  downstream exact-artifact contract should select it through one emitted
  index or an unambiguous role query, not restate the producer's filename
  convention. If a path is retained for human readability, post-export
  contract binding must run immediately and fail before review work begins.
- intended landing point: have `export_jlc_package.py` emit a versioned
  `artifact_index.json` with roles such as `gerber_archive`, `bom`, `cpl`,
  `pth_drill` and `npth_drill`, each carrying relative path and SHA-256.
  Extend `rf_contract_check.py` to resolve the fab artifact by role and compare
  any declared path/hash against that index at fabrication entry.
- completion evidence required: a filename-convention change must keep a
  role-bound review current, while a hand-declared stale path, two candidate
  Gerber archives, a missing role or a changed artifact hash must fail before
  the review is dispatched. The index itself must be regenerated and shipped
  with the release evidence.
- recommendation: implement before renaming another exporter or board stem.
  V5's source path is corrected now, so this is not a blocker for its current
  fabrication stage.
- history: 2026-08-13 — proposed after exact-artifact review setup found the
  hyphen-versus-underscore path mismatch before any release was sealed.

## IMP-095 — dispatch exact-artifact reviews from a machine-written envelope

- status: proposed
- observed: Pluto RX2 8-way v5 RF fabrication review dispatch, 2026-08-13
- evidence: after source commit `9706143a`, the coordinator sent the reviewer
  a manually expanded 40-character SHA that did not exist. The reviewer
  independently ran `git rev-parse HEAD`, found the disagreement, and refused
  to bind the review until the exact
  `9706143aea030b4e4ddddcd72e5e55293f3b19e8` value was confirmed. No review or
  release was misbound, but correctness depended on reviewer suspicion rather
  than a dispatch mechanism.
- general rule: exact commit IDs, artifact paths and digests are machine data.
  They must travel to a reviewer as one generated, immutable envelope; prose
  may explain the task but must not restate or expand identifiers by hand. The
  reviewer must verify the envelope against local bytes before writing a
  verdict.
- intended landing point: add a small review-dispatch producer that records
  schema version, project/board, exact `git rev-parse` commit, scoped dirty
  result, artifact path/role/SHA-256, contract path/SHA-256 and requested
  requirement IDs. Make review freshness validate the copied header against
  that envelope. Where IMP-094's exporter index exists, consume it rather than
  rediscovering the fab path.
- completion evidence required: a nonexistent expanded SHA, a one-character
  artifact digest error, a dirty consumed input and a path selecting a sibling
  artifact must all fail before review text is accepted. A clean envelope must
  round-trip its exact identifiers into the archived review without manual
  copy/paste.
- recommendation: implement with IMP-094, before the next exact-artifact review
  fan-out. V5's reviewer caught and corrected the dispatch before finalizing,
  so its present review can bind safely to the machine-read commit and is not
  blocked.
- history: 2026-08-13 — proposed after the independent reviewer detected the
  coordinator's invalid hand-expanded commit ID.

## IMP-096 — derive release PDF pages from populated sides and document purpose

- status: proposed
- observed: Pluto RX2 8-way v5 release-asset export, 2026-08-13
- evidence: the generic assembly command plotted
  `F.Silkscreen,B.Silkscreen,F.Fab,B.Fab,F.Courtyard,B.Courtyard,Edge.Cuts`
  as seven separate pages on a top-only board. Four pages were blank or only a
  title block/outline, while the F.Fab page overlaid values and catalog-like
  text densely enough to weaken its locator purpose. A purpose-derived export
  instead produced three nonblank pages: top silk, top fab with pad numbers and
  reference designators but values excluded, and top courtyard, each with the
  board edge as a common layer. The PCB layer packet similarly fell from nine
  pages to seven by dropping the empty bottom-silk page and making Edge.Cuts a
  common reference rather than a near-empty standalone page.
- general rule: a release PDF is a human verification artifact, not a dump of
  every possible layer name. Its page denominator must be derived from actual
  populated sides, nonempty layer content and the document's purpose. Edge
  geometry should appear as a common registration reference; assembly pages
  should prioritize refdes/pin/polarity legibility over repeating BOM values.
- intended landing point: replace ad-hoc `kicad-cli pcb export pdf` invocations
  with a shared release-PDF producer. It should inspect the board, select only
  meaningful top/bottom assembly layers, emit a page manifest naming each
  page's role, rasterize every page, and reject blank/near-blank pages or pages
  whose critical identifiers are missing/occluded. Preserve an explicit
  diagnostic mode that can still dump every layer when needed.
- completion evidence required: a top-only board produces no bottom assembly
  pages; a populated two-sided board produces both; Edge.Cuts is visible on
  every page; a known blank layer and a deliberately obscured polarity/refdes
  fixture both fail. The producer must prove fresh nonempty output rather than
  accepting a stale PDF after a CLI parse warning.
- recommendation: implement before the next release asset stage. V5's current
  generated 7-page PCB and 3-page assembly packets have been visually checked,
  so the shared producer is not a blocker for this board.
- history: 2026-08-13 — proposed after the first mechanically successful PDF
  export was visibly poor as a human assembly packet.

## IMP-097 — preserve schematic-sheet coordinate domains in native conversion

- status: implemented
- observed: Pluto RX2 8-way v5 hardware-release audit, 2026-08-13
- evidence: the TSX human schematic contained four independently readable
  authored sheets, but `circuit_json_to_kicad_sch.py` treated every sheet's
  local coordinates as one global plane. The resulting native KiCad schematic
  superimposed J1/J2, U1/U2 and four value/reference fields. The rendered TSX
  PDF looked correct, so reviewing only that publication artifact hid the
  defective native source until full `S-OCCL` release grading found six exact
  overlaps.
- general rule: a schematic sheet identifier defines a coordinate domain.
  Geometry from separate domains must be emitted as separate native sheets or
  assigned deterministic non-overlapping regions before any global transform.
  A readable publication PDF does not prove the editable/native schematic is
  readable.
- landed at: the shared layout-preserving converter now computes bounds per
  `schematic_sheet_id`, orders pages by the authored `sheet_index`, stacks
  their unchanged local geometry into non-overlapping regions, and restricts
  port resolution to the trace's own sheet. The converter still proves the
  exported netlist independently against the board.
- completion evidence: a regression gives two authored sheets identical local
  component coordinates and requires different emitted KiCad coordinates,
  four exported nodes and zero native schematic occlusions. The full converter
  suite passes 44/44. Pluto v5's regenerated native schematic has 202/202
  drawable objects placed, zero text occlusions, zero two-net conductor events
  and exact 22-net/131-node parity with the unchanged routed board.
- recommendation: carry this fix immediately. Keep both human-render review
  and native `S-OCCL`/netlist parity as independent gates; neither subsumes the
  other.
- history: 2026-08-13 — found and fixed during hardware-only release audit;
  firmware was not read or invoked.

## IMP-098 — make clean replay produce every ignored review prerequisite it consumes

- status: proposed
- observed: Pluto RX2 8-way v5 hardware-release clean replay, 2026-08-13
- evidence: a fresh worktree at committed source stopped at placement review
  because `06_build/pre_route/twin_overlay.md` was absent. The replay driver
  requires and freshness-checks that derived report, but neither the driver nor
  an earlier declared stage produced it; the report is correctly ignored as a
  build artifact. Running the strict pre-route fab exporter, JLC twin producer
  and overlay grader created it, after which the unchanged replay passed all
  four placement-review bindings and continued to DRC 0/0/0.
- general rule: a clean-build driver may consume an ignored artifact only when
  its dependency graph contains a deterministic producer edge before the first
  consumer. A freshness check is not a producer, and a file left behind by a
  prior interactive run is not reproducibility evidence.
- intended landing point: express the pre-route twin and overlay as an explicit
  pipeline stage with declared source/config/model inputs, bounded execution,
  outputs and review invalidators. `rebuild_reuse.sh` should run that stage—or
  invoke one checkpoint-aware producer—before `pre_route_review_check.py`.
  Keep the review itself human-authored and committed; only its derived subject
  and machine report are regenerated.
- completion evidence required: delete or use a clean checkout with no
  `06_build/pre_route`; one command must reproduce the twin/report and reach
  the placement gate. A missing model, stale board hash, or failed overlay must
  still stop before route import. A stale ignored report must never satisfy the
  gate without its producer running or authenticating its inputs.
- recommendation: implement before the next board's placement-review replay.
  V5's exact prerequisite was regenerated and verified, so this is no longer a
  blocker for its hardware release.
- history: 2026-08-13 — proposed after the first genuinely clean v5 release
  replay exposed a hidden dependency on an ignored prior-run artifact.
- follow-up: the 2026-08-14 J12 renewal confirmed that this producer also needs
  a role-scoped output namespace. Writing a preliminary package under
  `06_build/pre_route/fab/` created valid `bom.csv`, `cpl.csv` and Gerber bytes,
  but the observation audit correctly reported an unresolved selection because
  canonical consumers select `06_build/fab/<basename>` while a second copy of
  the same basename existed elsewhere under the project. The temporary package
  was moved outside the subject and only uniquely named pre-route BOM/CPL
  witnesses were retained. The intended producer should emit a role-indexed
  artifact bundle (IMP-094), not introduce plausible same-basename alternatives
  into a tree whose consumers still resolve by path convention.

## IMP-099 — seed every late KiCad writer, not only board and route preparation

- status: implemented
- observed: Pluto RX2 8-way v5 hardware-release reproducibility proof,
  2026-08-13
- evidence: the committed and first clean-replayed boards had identical
  electrical copper multisets (880/880 items), footprint placements (36/36)
  and pad geometry/net assignments (171/171), yet their PCB SHA-256 digests
  differed. Replotting showed 9/13 fabrication members identical after timestamp
  normalization; all four copper Gerbers differed. The cause was unseeded UUID
  creation in KRT import and multi-process stitch writers. KiCad save order
  changed, and F.Cu fill differed by six nanometre-scale tessellation vertices.
- general rule: deterministic generation ends at the last object-creating
  writer. Seeding only the base-board generator or route-prep stage is
  insufficient when import, taps, stitching, fencing, island healing, or
  barrier-resumed processes can mint tracks/vias. Each writer needs a stable,
  disjoint namespace; barrier resumptions must include the authenticated pass
  index so they neither randomize nor reuse a prior writer's UUID stream.
- landed at: `import_krt.py` now seeds a board-namespaced `route-import` UUID
  stream. `route_and_stitch_generic.py` provides phase-namespaced seeding for
  optional tap attempts and each stitch interpreter/resume index. A regression
  imports the same chain twice and requires byte-identical boards with no
  duplicate UUIDs.
- completion evidence: two complete v5 clean replays both passed DRC 0/0/0 and
  produced byte-identical PCB SHA-256
  `43689fe44daa2bd437979c573e78da39a51aacd9d4664a24e7e29bc1c22ea0b3`.
  The focused import regression passes. Final release export will recheck all
  Gerber/drill members from this canonical board.
- recommendation: carry immediately; implemented for the shared pipeline and
  exercised by v5 before sealing. Retain semantic copper comparison as a useful
  diagnostic, but do not treat it as a substitute for deterministic source and
  fabrication bytes.
- history: 2026-08-13 — found, generalized, fixed and double-replay verified
  before the v5 hardware release was assembled.

## IMP-100 — validate assembly semantics before release staging

- status: proposed
- observed: Pluto RX2 8-way v5 hardware-release staging, 2026-08-13
- evidence: `assembly.yaml` used the descriptive scalar
  `build_quantity: 5_first_articles`, which reached
  `release_freshness_check.py` and raised an uncaught integer-conversion
  exception instead of producing a gate result. The same file also used
  `sourcing_plan:` as a convenient complete BOM/function map. The release gate
  correctly interprets that field as an exception plan for a stock shortfall,
  so all 13 otherwise-stocked BOM lines became incomplete plans with no
  measured stock/date. The current board was repaired to numeric
  `build_quantity: 5` and `sourcing_plan: []`; exact BOM mapping remains in
  its proper circuit/dossier authorities.
- general rule: validate configuration by semantic role at the earliest
  schema boundary. `build_quantity` is a positive integer, not a display
  label. `sourcing_plan` contains only measured exception/disposition records,
  never the normal BOM population or a shopping list. A consumer must report a
  schema failure rather than crash on a malformed value.
- intended landing point: add an assembly-schema validator to commission/source
  preflight and reuse it from the exporter, stock gate and release gate. Give
  ordinary part mapping its existing authoritative homes rather than adding a
  second assembly-side map. Harden `release_freshness_check.py` so invalid
  types return a named fail-closed finding with path and field.
- completion evidence required: fixtures for a descriptive quantity, zero or
  negative quantity, a normal BOM row misfiled as `sourcing_plan`, and a valid
  measured stock-shortfall plan. Every malformed fixture must fail before PCB
  generation or market queries and none may raise a traceback.
- recommendation: implement before the next project reaches sourcing or
  release staging. Pluto v5's source and sealed copy are corrected, so this is
  not a blocker for its present hardware archive.
- history: 2026-08-13 — recorded after the first shipped-byte freshness run
  exposed both schema/semantic defects despite a passing live stock report.

## IMP-101 — make local PCB ECO routing preserve the validated copper baseline

- status: proposed
- observed: Pluto RX2 8-way v5 J12 bench-power renewal, 2026-08-14
- evidence: adding one two-pin connector outside the RF core required only two
  deterministic `VBUS_RAW` segments. A fresh whole-board stochastic route ran
  quickly but attempted a new via inside R6.1 and was correctly rejected by the
  via-in-pad guard. Importing the already validated promoted route onto the new
  exact base, then importing only the two J12 segments, produced a clean board.
  Exact comparison proved all 236 earlier tracks and 57 earlier vias unchanged
  to the nanometre limit; stitch, RF-fence, via-process and DRC gates then
  passed. The useful result came from treating the change as a bounded ECO, not
  from reopening a solved global search.
- general rule: when a placement-compatible promoted route exists and the
  design change has a small declared copper boundary, prefer an explicit ECO
  transaction: authenticate the old route against the new base, import it,
  add only declared deterministic delta copper, prove the protected baseline
  geometry is unchanged, then rerun every downstream connectivity, plane,
  process, RF and DRC gate. Never preserve old copper merely because it loads;
  P-ROUTEBASE and the post-import diff are both mandatory.
- intended landing point: extend the shared route orchestrator with an `eco`
  mode and a small YAML contract naming allowed added/removed refs, nets and
  copper-object budgets. Emit a machine-readable before/after geometry report
  and reject any undeclared track/via movement before stitch. If compatibility
  or the declared delta proof fails, fall back to a bounded fresh route rather
  than weakening the comparison.
- completion evidence required: fixtures for a clean one-connector/two-track
  ECO, a moved old track, an undeclared removed via, a changed pad/net, and a
  legitimate placement-incompatible change that must request a fresh route.
  The clean fixture must reproduce identical protected-baseline geometry across
  two runs and finish with the normal saved-board gates.
- recommendation: implement before the next local connector, test-point or
  protection-component PCB revision. The Pluto candidate itself is already
  covered by an exact manual migration/diff and full downstream replay, so this
  is a pipeline generalization rather than a blocker for the current board.
- relationship: IMP-040 proves that promoted copper is compatible with the new
  base before review; IMP-083 rejects unsafe router vias; this improvement adds
  an explicit minimal-change execution path between those two controls.
