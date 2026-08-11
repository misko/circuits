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
| IMP-001 | Validate rule/config schemas before expensive TSX generation | proposed | USB Hub 3S v4, Stage 2 schematic |
| IMP-002 | Require an explicit human-schematic readability review | proposed | USB Hub 3S v4, Stage 2 schematic |
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
| IMP-016 | Exclude orchestration-only fields from the adopted-design-rules digest | proposed | USB Hub 3S v4, Stage 4 replay |

## IMP-001 — pre-build rule/config schema validation

- status: proposed
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
- history: 2026-08-11 — proposed and promoted from the schematic journal.

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

## IMP-002 — explicit human-schematic readability review

- status: proposed
- observed: `projects/usb-hub-3s-v4/01_docs/journal/03_schematic.md` and
  `projects/usb-hub-3s-v4/08_reviews/pre-route_topology.md`
- evidence: The one-page tscircuit render is electrically coherent and
  zoom-readable, but less conventionally sectioned left-to-right than a
  hand-arranged production schematic. Connectivity, parity, ERC, freshness and
  the KiCad-sheet occlusion gate do not establish that the shipped tscircuit
  PDF communicates the design clearly.
- intended landing point: a structured, hash-bound schematic-render review at
  the schematic checkpoint. It should grade the actual
  `03_tscircuit/build/schematic.pdf`, record readability findings and a closed
  verdict, and be required before placement. This is distinct from the
  placement-phase `pre-route_render.md`, which grades PCB renders.
- completion evidence required: canonical review schema and checker; the PCB
  design instructions and `08_reviews` contract name the new witness; clean and
  stale/missing/defective fixtures; the USB Hub v4 PDF receives an explicit
  verdict bound to its SHA-256.
- history: 2026-08-11 — proposed and promoted from the schematic journal.

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
  config budgets 60 seconds, times out at 180 seconds and emits a heartbeat
  every 10 seconds. `tests/t1_rebuild_templates.py` rejects a return to the
  former unbounded direct call.
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
- history: 2026-08-11 — implementation started after the Stage 4 deterministic
  replay proved the full/reuse contradiction.

## IMP-016 — adopted-rule digest should not include orchestration metadata

- status: proposed
- observed: USB Hub 3S v4 Stage 4 replay, 2026-08-11
- evidence: adding only `flow.budgets_s.tscircuit_build` and
  `flow.timeouts_s.tscircuit_build` invalidated all four hash-bound electrical,
  pin, layout and render reviews because `design_rules_digest()` hashes the
  whole `route.yaml`. The review files had to be rebound even though board,
  copper, parts and every design/fabrication rule were unchanged.
- intended landing point: hash a versioned canonical projection of adopted
  electrical, fabrication, placement and routing semantics. Exclude progress,
  timeout, budget, path, owner, blocker and other orchestration-only fields;
  retain a separate raw config/provenance hash for forensic replay.
- completion evidence required: timeout/heartbeat/log-path mutations leave the
  adopted-rules digest stable; width, clearance, via, layer, route-wave, tap,
  zone, placement and fabrication mutations invalidate it; existing projects
  migrate via fresh reviews.
- history: 2026-08-11 — proposed after bounded TSX execution caused a vacuous
  four-review rebind.
