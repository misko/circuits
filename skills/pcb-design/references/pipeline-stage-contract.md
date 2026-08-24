# Declarative PCB pipeline contract

This reference freezes the public interfaces for the pipeline refactor. Read
it when adding or composing a stage, producer, review, release gate or timing
instrumentation. Domain predicates remain in `kicad-pcb` and `jlcpcb-fab`.

## Contents

1. Ownership and typed stage/result schemas
2. Subject identity and artifact transactions
3. Review contracts and lifecycle facts
4. Conditional adapters
5. Migration and shadow implementation status

Migration/coverage IDs owned here: `GG-RESOLVE`, `GG-SHADOW`, `M-COVER`, and
`M-FRESH`. Bounded attempt execution (`M-BOUND`) is owned by
`execution-runtime.md`.

## Ownership

| Owner | Responsibility |
|---|---|
| `pcb-design` | lifecycle, composition, execution, identities, reviews, artifact transactions, release/publication |
| `kicad-pcb` | schematic/netlist, KiCad board, placement, geometry, routing, DRC/parity |
| `jlcpcb-fab` | exact-code readiness, BOM/CPL, stock, rotation, twin and fabrication package |

No core module may contain project refdes or numeric design limits.

## StageSpec schema 1

The public Python representation is `pipeline_contract.StageSpec`. Its mapping
form uses these fields:

```yaml
schema: 1
id: P-ROUTEBASE
owner: kicad-pcb
lifecycle: placement
cost: cheap
work_class: local
timeout_s: 30
requires: [exact_placement, deterministic_route_prep]
produces: [route_compatibility_report]
blocks: [placement_review]
invalidated_by: [placement_semantic, route_process]
```

Required invariants:

- `id` is stable and matches `[A-Z][A-Z0-9-]*`.
- `owner` is `pcb-design`, `kicad-pcb`, or `jlcpcb-fab`.
- `lifecycle` is one of `commission`, `architecture`, `sourcing`,
  `schematic`, `placement`, `routing`, `layout_seal`, `fabrication`,
  `release_staging`, `release_seal`, `publication`, `first_article`, or
  `production`.
- `cost` is `cheap`, `bounded`, `external`, `review`, or `operator`.
- `work_class` is `local`, `network`, `backoff`, `review_wait`, or
  `operator_wait`.
- `timeout_s` is positive for executable work. Operator-only declarative
  stages may omit it.
- `requires`, `produces`, `blocks`, and `invalidated_by` are sorted unique
  symbolic names. Paths and commands do not belong in semantic identity.
- A stage has an applicability result, not a free-form expression language.
  The caller supplies `APPLIES` or `NOT_APPLICABLE` plus a reason and graded
  denominator. Unknown applicability fails.

## StageResult schema 1

`pipeline_contract.StageResult` is the durable result consumed by orchestration:

```yaml
schema: 1
stage_id: P-ROUTEBASE
run_id: 20260812T170000Z-8d31a2f0
subject:
  semantic_sha256: <64 hex>
  raw_sha256: <64 hex>
applicability: APPLIES
applicability_reason: null
status: PASS
started_at: 2026-08-12T17:00:00Z
finished_at: 2026-08-12T17:00:01Z
elapsed_s: 1.0
graded: 95
total: 95
outputs: [route_compatibility_report]
findings: []
resume: null
```

Closed vocabularies:

- applicability: `APPLIES`, `NOT_APPLICABLE`;
- status: `PASS`, `FAIL`, `NOT_APPLICABLE`, `TIMED_OUT`, `INCOMPLETE`,
  `ERROR`.

Rules:

- `PASS` requires `APPLIES`, `total > 0`, and `graded == total`.
- `NOT_APPLICABLE` requires a non-empty `applicability_reason` and zero
  graded/total. `APPLIES` requires it to be null or empty.
- timeouts and incomplete reviews never become admissible PASS evidence.
- the result names output symbols; the artifact bundle binds their paths and
  bytes.

## Companion execution contract

Do not extend `StageSpec` with argv, agent, prompt, context, token, writer-path,
or replacement details. `StageSpec` says what engineering work exists;
`execution-runtime.md` solely owns `TaskEnvelope`, `TaskAttempt`, `WriterScope`,
process-group control, post-hoc writer detection, deadlines, replacement, and
runtime truth claims.

## Subject identity

Every stage subject carries two independent hashes:

- `semantic_sha256`: canonical design meaning used for reuse/review staleness;
- `raw_sha256`: exact source/tool bytes used for reproduction and forensics.

Each identity is a typed projection with a version. Formatting, paths, timeout
and logging changes may affect raw identity without affecting semantic
identity. Electrical, placement, routing, process or release-claim changes must
affect the relevant semantic projection. Never broaden a text normalizer when
a parsed projection is available.

## Artifact bundle schema 1

A producer writes into a new temporary directory and promotes the directory
only after validation. `bundle.json` contains:

```yaml
schema: 1
run_id: 20260812T170000Z-8d31a2f0
producer: jlc-stock-check
producer_version: <identity>
subject: {semantic_sha256: <64 hex>, raw_sha256: <64 hex>}
started_at: 2026-08-12T17:00:00Z
finished_at: 2026-08-12T17:00:02Z
status: PASS
inputs:
  fab/bom.csv: {sha256: <64 hex>, size: 1234}
outputs:
  stock_check.json: {sha256: <64 hex>, size: 4567}
```

The transaction must:

1. start in a sibling temporary directory;
2. reject undeclared, missing, old, empty or unparsable outputs;
3. apply normalization, waivers and adjudication before serialization;
4. reopen durable outputs and cross-check declared key fields;
5. write `bundle.json` last;
6. atomically replace the accepted bundle without exposing a partial result;
7. preserve a previous accepted bundle on failure.

### Frozen receipt composition

The migration uses the existing schema-1 objects rather than introducing a
second verdict or manifest format:

- `stage-receipt-v1` is exactly the `StageResult` schema above. It owns
  applicability, verdict, coverage, findings, timing and subject identity.
- `artifact-bundle-v1` is exactly the `bundle.json` schema above. It owns
  durable paths, byte hashes and atomic acceptance.
- A domain-specific evidence receipt is a declared JSON output inside an
  artifact bundle. It records measurements and provenance only; it must not
  duplicate or override the outer stage verdict.

The first domain receipt is `model-registration-receipt-v1`:

```yaml
schema: 1
kind: model-registration-receipt-v1
tuple:
  footprint_sha256: <64 hex>
  model_sha256: <64 hex>
  transform_sha256: <64 hex>
  contract_sha256: <64 hex>
  tool_identity: <non-empty stable identity>
refs: [J2]
measurements:
  - ref: J2
    attachment_centres_graded: 5
    attachment_centres_total: 5
    centre_delta_mm: 0.0
    fab_outward_mm: 0.0
    courtyard_outward_mm: 0.0
evidence: [native_top_registration_overlay.png]
```

Its tuple cache key is SHA-256 over canonical JSON containing exactly the five
`tuple` fields shown above. Any footprint, model, transform, registration
contract or checker-identity change therefore invalidates reuse. `refs`,
`measurements` and `evidence` are sorted deterministically; evidence paths are
relative to the bundle. The outer `StageResult.outputs` names the accepted
artifact bundle, whose manifest binds this receipt and every referenced image
to exact bytes.

Readiness composition consumes only strict `stage-receipt-v1` mappings plus
their accepted bundles. A receipt is admissible when its stage is applicable,
passing, expected for the current lifecycle/profile, bound to the current
semantic and raw subject hashes, and all named outputs reopen through their
bundle manifests. `project_state.py --readiness-authority shadow` preserves the
legacy findings-ledger decision while recording the receipt comparison.
`--readiness-authority receipts` promotes the closed receipt registry to the
decision, and `agreement` additionally refuses a mismatch with the retained
legacy projection. Authority is selected explicitly per project; a domain JSON
report alone never advances maturity.

Each schema-1 readiness-registry stage also declares `minimum_total`: a
positive expected coverage floor for `APPLIES`, or exactly zero for
`NOT_APPLICABLE`. A non-vacuous PASS below that floor is still inadmissible.
Stage IDs and bundle paths are unique across the registry so one receipt or
manifest cannot satisfy two controls. Example stage entry:

```yaml
stage_id: P-MODEL-REG
required_for: DESIGN_CLEAN
applicability: APPLIES
minimum_total: 1
bundles:
  model_registration_bundle: 06_build/pre_route/model_registration_bundle/bundle.json
```

## Review contract schema 1

A review commission names an immutable subject, one lens, a bounded checklist,
explicit exclusions, one output and a wall-clock deadline. A witness uses:

- design verdict: `SOUND`, `DEFECTIVE`, or `INCOMPLETE`;
- order verdict: `ORDER`, `FIRST-ARTICLE-ONLY`, `DO-NOT-ORDER`, or
  `BLOCKED-SOURCING`;
- canonical `project` slug, source commit and artifact hashes.

The launcher, not the prompt, enforces the deadline. A partial or late file is
inadmissible. Commissioning, pre-seal rehearsal and publication import one
review-header parser.

## Lifecycle facts

Mutable or realized facts use paired observations. Supplier evidence has three
different meanings and must never be coerced into one verdict:

- `catalog_identity` / `catalog_stock`: candidate discovery and negative
  filtering only; never final authority;
- `pcba_availability`: quantity-expanded, BOM-bound JLCPCB PCBA-interface
  evidence used before placement;
- `order_allocation`: final JLCPCB order-interface evidence for the exact
  release BOM and order quantity.

The authoritative pair is:

```yaml
fact: pcba_orderability
early:
  stage: schematic
  blocks: placement
  maximum_age_s: 86400
late:
  stage: fabrication
  blocks: publication
  authority: jlcpcb_order_interface
```

The early `AVAILABLE` observation prevents avoidable layout spend. It never
satisfies the late claim. Only late `ALLOCATED` evidence authorizes `ORDER`;
its failure points back to the owning earlier selection decision. Missing,
partial, stale, changed-BOM, substituted, or unknown evidence is `INCOMPLETE`,
never a pass. A sound design may retain a blocked order verdict without
weakening its design verdict.

Required first pairs are PCBA orderability, supplier model availability, via/current
capacity, generated evidence, live/relocated DRC and review/publication
identity.

## Conditional adapters

High-speed digital signal integrity and RF specialization are adapters inside
the existing lifecycle, not a fourth
pipeline owner and not a review-wait stage:

- `signal-integrity.md` composes generic high-speed source and realized checks
  into schematic and routing. It never selects an RF-named stage.
- RF stages run only when the project RF contract is explicitly applicable.

1. `rf_contract_check.py` resolves explicit applicability.
2. `rf_context.py` selects local source cards with no network or reviewer.
3. `rf_solver.py` runs only declared `pending_solver` work as bounded,
   heartbeat-visible, cached local jobs; locked sections are immediate N-A.
4. `rf_check.py source` grades authored geometry before producer spend.
5. `rf_check.py realized` reopens the saved board and emits exact evidence
   before the existing RF PCB review.

Exact cached bundle reuse is load-bearing: a no-op run must keep its manifest
hash stable or it needlessly invalidates a human review. RF schematic/PCB/fab
review remains owned by the existing review contract; this adapter launches no
reviewer and creates no additional polling boundary.

## Migration

1. Wrap existing commands without changing predicates.
2. Resolve the declarative plan in shadow mode.
3. Compare order, applicability, identities, outputs and blockers with the
   existing pipeline.
4. Migrate one lifecycle boundary at a time.
5. Keep the current pipeline authoritative until USB Hub 3S v4 and Pluto RX2
   8-way v4 canaries agree.

Parallel implementers own new modules and focused tests only. The integration
coordinator exclusively edits `SKILL.md`, `rebuild_all.sh`, `pcb_flow.py`, the
central registry/test runner and `improvements.md`.

## Receipt implementation and migration status

The schema-1 foundation is available under `skills/pcb-design/scripts/`:

- `pipeline_contract.py` — strict `StageSpec` and `StageResult` readers;
- `pipeline_identity.py` — versioned typed semantic/raw subject identities;
- `pipeline_registry.py` — dependency validation, cheap-first resolution and
  comparison with an observed legacy plan;
- `pipeline_runtime.py` — shared bounded process-group execution; see
  `execution-runtime.md` for its authority and current containment limits;
- `pipeline_artifacts.py` — fresh validated bundle staging and atomic
  manifest-last promotion.
- `pipeline_readiness.py` — strict closed receipt registries, coverage floors,
  subject/freshness/bundle validation and shadow or authoritative maturity
  composition;
- `pipeline_review.py` — bounded commissions and exact durable-witness
  admissibility;
- `pipeline_facts.py` — early prevention observations paired with independent
  late authority;
- `pipeline_timing.py` — work-class totals and dependency critical-path
  summaries kept distinct from the observed wall envelope.
- `pipeline_execution.py` — companion task envelopes, bounded attempts,
  fresh-context decisions, agent spans and non-conflated token telemetry;
- `pipeline_catalog.py` — strict, canonical, exact-driver-hash-bound catalogs
  that keep legacy argv/cwd/applicability/accepted evidence separate from typed
  stage semantics;
- `pipeline_shadow.py` — a pure observer that records legacy completion and
  projects typed results without executing, retrying or promoting;
- `pipeline_xtrace.py` — a dedicated-channel Bash trace parser that maps only
  declared source-line commands and preserves unmapped executable evidence.

These modules do not bypass an existing gate or publication path. A producer
is migrated only after its adapter has a
clean and known-bad fixture and its observed plan/result/artifacts agree on
both canary projects.

The 2026-08-15 adoption slice adds two real consumers without changing legacy
authority. `fab_payload_census.py --bundle` can publish reopened JSON/text
evidence transactionally and retain rejected diagnostics. `P-MODEL-REG` now
uses origin-centred, exact-tuple per-group caches plus one aggregate bundle
whose run and subject match its strict `StageResult`; the aggregate reopens
through `pipeline_readiness.py` for both single- and multi-group fixtures.
`project_state.py --receipt-registry` records receipt-derived maturity and its
comparison with the legacy ledger in default shadow mode. Projects may opt
into `--readiness-authority receipts` after their closed registry and bundles
pass clean, missing, stale, tampered, low-denominator and disagreement
fixtures. Route acceptance and release rehearsal retain their hash-bound domain
receipts as authoritative outputs; any sibling shadow diagnostic remains
outside those receipts and their identities. Manufacturing readiness,
placement-routability, and electrical closure may each emit only a canonical
typed `INCOMPLETE` boundary hold for `S-PART-FREEZE`, `P-FEASIBILITY`, or
`E-CLOSURE`. Each invalidates any unsafe former PASS StageResult at that path,
has zero accepted outputs, and creates or replaces no accepted bundle. The
common two-target publisher refuses promotion until bundle and
StageResult share one independently regraded, pointer-last transaction. Legacy
invocations remain authoritative until canaries agree. In particular,
E-CLOSURE retains its historical nine-check battery and the presence-selected
tenth operating-state check for projects that had already opted into it; the
new applicability shadow may neither delete nor replace that check.

The first disposable reuse-driver observation on 2026-08-12 did not agree:
USB Hub 3S v4 stopped after about 11.4 seconds at stale/missing pre-route review
evidence, while legacy Pluto RX2 8-way stopped after about 2.0 seconds at seven
anchored courtyard overlaps. Both failures were prompt and diagnostic. Later
work corrected the legacy broad-phase geometry false positive and completed a
distinct Pluto RX2 8-way v4 green 22-stage reuse trace; USB still deliberately
stops fail-closed when its exact human-review evidence is stale. See
`docs/pipeline-shadow-canaries.md` for the ordered evidence and limitations.

The 2026-08-15 progressive-disclosure refactor adds a pure capability-profile
router and a frozen 109-policy authority/coverage audit. It changes which
procedure text is loaded, not which driver or gate executes. Its simple, USB,
Pi USB, and Pluto fixtures pin the normalized composition trace; the existing
USB and Pluto catalog canaries remain green. No execution authority moves on
that evidence alone.

The 2026-08-24 robustness slice moves bounded subprocess execution for the
explicitly migrated paths: `process_runner.py` is now a compatibility adapter
over the shared process-group runtime, with finite deadlines, heartbeat state,
retention of all bytes read before any bounded transport cutoff, and cleanup of
pipe-holding, output-redirected, and nested subgroup members. Nested execution
requires Linux `/proc` discovery and is refused before launch without it. A
hostile descendant that starts a foreign session can still escape reaping; the
runtime cuts inherited transport and returns non-passing.

This slice also makes intentional fail-closed authority rollbacks at unsafe
publication and migration seams. Former shadow `PASS` StageResults for
S-PART-FREEZE, E-CLOSURE, and P-FEASIBILITY are replaced by typed `INCOMPLETE`
requests with zero outputs, and no accepted bundle is created or replaced.
That can stop a downstream readiness consumer which relied on the former PASS;
it is a visible migration hold, not receipt compatibility. Legacy domain
verdicts remain authoritative, including E-CLOSURE's historical nine-or-ten
check battery. An experimental shared route-admission core had also begun
tightening otherwise-accepted route receipts before it had independent input
authority or runtime isolation. That premature authority is removed: the
original route admission verdict is restored and the shared comparison becomes
a nonexecuting sibling request. Existing route receipt bytes and, where that
experiment alone tightened a result, verdicts can therefore change; consumers
must rebind deliberately rather than assuming receipt compatibility.
Applicability, engineering-verdict, review, release, and publication authority
otherwise do not move.

All other new seams retain explicit rollout boundaries:

- the capability router emits `DISCLOSURE_ONLY` plans and `UNKNOWN` dependency
  placeholders, never N/A evidence;
- the applicability compiler can run only as structural `SHADOW`; it cannot
  authenticate its caller-supplied facts;
- operating-state, functional-cell, and source-preparation shadow selections
  write pending sibling requests and do not execute their compilers in the
  authoritative hot path. Separately budgeted canary output remains diagnostic
  until independent owner receipts and typed extractors can be reopened;
- native-DRC and semantic-copper candidate flags likewise write pending
  requests rather than executing expensive shadows. Final-route grading also
  writes only a pending shared-admission request; a separately budgeted canary
  may execute the comparison outside the authoritative receipt and identity;
- transaction-local route targets and content-addressed bundle helpers are
  experimental; the live importer and mutable `FINAL` path are unchanged, and
  bundle promotion remains unavailable until every authoritative candidate
  predicate can be independently rederived.

High-speed digital disclosure now composes `signal-integrity.md` into the
existing schematic/routing stages. It does not select RF stages. RF remains
selected only by the RF capability/source path. See
`docs/pipeline-shadow-canaries.md` for the measurements and promotion holds.
