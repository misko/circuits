# ADR-0008 — Refactor pipeline composition around typed stages and artifacts

Status: accepted, 2026-08-12
Supersedes: nothing. Extends ADR-0004 and ADR-0007.

## Context

USB Hub 3S v4 reached a sealed design through correct fail-closed gates, but
the execution path repeatedly discovered cheap source, evidence and packaging
defects after expensive generation or review. The individual repairs produced
IMP-001 through IMP-065. Implementing every item as another independently
wired command would duplicate ordering, timeout, hash, report and verdict
logic in the shell driver, conductor, skill prose and tests.

The useful distinction is:

- domain validators own engineering predicates;
- the pipeline owns applicability, ordering, execution, artifact promotion,
  subject identity, review admissibility and claim transitions.

## Decision

Introduce the versioned contract in
`skills/pcb-design/references/pipeline-stage-contract.md` and refactor toward a
small declarative stage engine. Existing validators remain authoritative and
are wrapped before they are rewritten. The first migration runs in shadow mode
and must reproduce the existing command plan and verdicts.

The core owns:

1. a typed `StageSpec` and `StageResult`;
2. one bounded runner and structured timing record;
3. one transactional artifact-bundle primitive;
4. semantic and raw identities for stage subjects;
5. typed review commissions and admissible witnesses;
6. qualification obligations and early-warning/late-authority pairs.

Domain ownership remains separate:

- `kicad-pcb` owns KiCad, netlist, placement, geometry, routing and DRC
  predicates;
- `jlcpcb-fab` owns JLC/LCSC catalog, BOM/CPL, rotation, twin and fabrication
  package predicates;
- `pcb-design` owns composition and release/publication lifecycle.

Project-specific values remain project configuration and evidence. Core code
must not contain USB Hub or Pluto refdes, currents, via sizes, resistance
limits, population lists or test limits.

## Migration constraints

- Do not modify sealed release bytes.
- Freeze public contracts before parallel implementation.
- Give each parallel workstream disjoint module and test ownership.
- Do not rewire `rebuild_all.sh`, `pcb_flow.py` or release publication until
  shadow-plan equivalence passes.
- Preserve the final authoritative checks when adding earlier warnings.
- Require a clean and a known-bad fixture for every new predicate.
- Use USB Hub 3S v4 and Pluto RX2 8-way v4 as independent canaries.

## Consequences

IMP entries remain the incident and acceptance ledger. Several entries will be
completed by one shared mechanism rather than one script each: IMP-026/049 by
the review service, IMP-050/054/058/062 by artifact transactions, and
IMP-057/059/060/063 by pre-seal rehearsal.

The existing pipeline remains the execution authority until a later ADR or an
append-only amendment records measured shadow equivalence and enables staged
migration.
