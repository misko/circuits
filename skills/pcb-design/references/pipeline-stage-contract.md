# Declarative PCB pipeline contract

This reference freezes the public interfaces for the pipeline refactor. Read
it when adding or composing a stage, producer, review, release gate or timing
instrumentation. Domain predicates remain in `kicad-pcb` and `jlcpcb-fab`.

## Contents

1. Ownership and typed stage/result schemas
2. Subject identity and artifact transactions
3. Review contracts and lifecycle facts
4. Conditional RF adapter
5. Migration and shadow implementation status

Migration/coverage IDs owned here: `GG-RESOLVE`, `GG-SHADOW`, `M-BOUND`,
`M-COVER`, and `M-FRESH`.

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
bundle manifests. During migration this computation is shadow-only: the
legacy findings ledger remains execution authority until canary equivalence is
separately approved.

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

Mutable or realized facts use paired observations:

```yaml
fact: stock_allocation
early:
  stage: sourcing
  blocks: schematic
  maximum_age_s: 86400
late:
  stage: fabrication
  blocks: first_article
  authority: jlc_uploader
```

The early observation prevents avoidable spend. It never satisfies the late
claim. The late failure points back to the owning earlier decision.

Required first pairs are stock, supplier model availability, via/current
capacity, generated evidence, live/relocated DRC and review/publication
identity.

## Conditional RF adapter

RF specialization is an adapter inside the existing lifecycle, not a fourth
pipeline owner and not a review-wait stage:

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

## Shadow implementation status

The schema-1 foundation is available under `skills/pcb-design/scripts/`:

- `pipeline_contract.py` — strict `StageSpec` and `StageResult` readers;
- `pipeline_identity.py` — versioned typed semantic/raw subject identities;
- `pipeline_registry.py` — dependency validation, cheap-first resolution and
  comparison with an observed legacy plan;
- `pipeline_runtime.py` — bounded process-group execution, lossless logs and
  work-class telemetry;
- `pipeline_artifacts.py` — fresh validated bundle staging and atomic
  manifest-last promotion.
- `pipeline_review.py` — bounded commissions and exact durable-witness
  admissibility;
- `pipeline_facts.py` — early prevention observations paired with independent
  late authority;
- `pipeline_timing.py` — work-class totals and dependency critical-path
  summaries kept distinct from the observed wall envelope.
- `pipeline_catalog.py` — strict, canonical, exact-driver-hash-bound catalogs
  that keep legacy argv/cwd/applicability/accepted evidence separate from typed
  stage semantics;
- `pipeline_shadow.py` — a pure observer that records legacy completion and
  projects typed results without executing, retrying or promoting;
- `pipeline_xtrace.py` — a dedicated-channel Bash trace parser that maps only
  declared source-line commands and preserves unmapped executable evidence.

These modules are shadow infrastructure, not permission to bypass an existing
gate or publication path. A producer is migrated only after its adapter has a
clean and known-bad fixture and its observed plan/result/artifacts agree on
both canary projects.

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
