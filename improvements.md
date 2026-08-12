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
- history:
  - 2026-08-11 — proposed and promoted from the schematic journal.
  - 2026-08-11 — implementation started with pre-producer label-survival and
    electrical schema gates; V4 passed before its 9.1-second TSX invocation.

## IMP-003 — pre-generation footprint resolution

- status: proposed
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
- intended landing point: extend the shared design/release schema so every
  `engineering_qualification_bound`, `qualified_max`, or other non-datasheet
  basis creates a typed validation obligation with an owner, acceptance test
  and latest release stage it blocks. A gate must reject a production claim if
  any such obligation is open, and report distinctly whether it blocks design,
  first-article ordering, first-article acceptance or production.
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

- status: proposed
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

## IMP-055 — preflight exact body/model availability before placement freeze

- status: proposed
- observed: USB Hub 3S v4 JLC digital twin, 2026-08-12
- evidence: the final twin mounts 71 of 75 placed bodies. JLC's current library
  has no usable exact 3D body for four deliberately hand-soldered connectors:
  the upstream USB-C power input and three USB-A outputs. Their footprints,
  mechanical drawings, pin identities and courtyards are independently
  reviewed, but the digital twin cannot prove their shell height or enclosure
  interference. Discovering this only after routing makes a package swap
  disproportionately expensive.
- intended landing point: after part selection and before placement, probe the
  exact supplier CAD endpoint for every height-, polarity- or enclosure-
  critical code. Record `MODEL`, `NO-MODEL` or `TRANSIENT` with the tested
  endpoint and date; never turn `TRANSIENT` into `NO-MODEL`. A genuine absence
  requires a datasheet-derived body envelope or a reviewed local STEP model,
  plus an explicit first-article/mechanical-fit obligation in the buyer file.
- completion evidence required: known-present, genuine-absent, throttled and
  wrong-body fixtures; a board-stage gate that closes before placement review;
  and a release check proving every placed body is either modeled or has a
  named mechanical fallback and first-article disposition.
- history: 2026-08-12 — recorded after the v4 twin made exact model coverage
  measurable; project-level dossier review exists, shared preflight remains
  open.

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
