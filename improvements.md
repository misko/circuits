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

## IMP-001 — pre-build rule/config schema validation

- status: proposed
- observed: `projects/usb-hub-3s-v4/01_docs/journal/03_schematic.md`,
  2026-08-11 08:34 entry
- evidence: A malformed `label_survival` row was knowable from YAML alone, but
  was not rejected until after an approximately 25-second TSX build/render.
  Existing `tsx_preflight.py` runs before generation but currently grades
  alphanumeric pad mapping, not all adopted rule schemas.
- intended landing point: a cheap canonical pre-build schema gate, invoked by
  both PCB rebuild templates before `build_provenance.py stamp` and before any
  `tsci build`. It should validate every rule block whose schema does not depend
  on generated circuit/netlist/board bytes, including `label_survival`.
- completion evidence required: clean and known-bad executable fixtures; both
  canonical rebuild templates prove the gate precedes TSX generation; the USB
  Hub v4 rule set passes; the original malformed label-survival shape fails
  without invoking the producer.
- history: 2026-08-11 — proposed and promoted from the schematic journal.

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
