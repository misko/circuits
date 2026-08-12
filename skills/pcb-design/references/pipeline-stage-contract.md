# Declarative PCB pipeline contract

This reference freezes the public interfaces for the pipeline refactor. Read
it when adding or composing a stage, producer, review, release gate or timing
instrumentation. Domain predicates remain in `kicad-pcb` and `jlcpcb-fab`.

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

These modules are shadow infrastructure, not permission to bypass an existing
gate or publication path. A producer is migrated only after its adapter has a
clean and known-bad fixture and its observed plan/result/artifacts agree on
both canary projects.
