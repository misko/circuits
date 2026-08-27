# Documentation map

This index distinguishes current operating authority from evidence and history.
Open the smallest document that owns the question; do not treat every Markdown
file in the repository as an instruction to execute.

## Authority order

When two documents disagree, resolve them in this order:

1. exact project or release `contracts.md` for artifact membership and
   immutability;
2. accepted ADRs for repository-level architectural decisions;
3. the owning skill and its routed reference for engineering procedure;
4. executable gate behavior and its tests for the implemented predicate;
5. measured proof/evidence for what has been demonstrated;
6. journals, improvement entries, plans, and historical reviews for rationale.

Fix the stale higher-level document after confirming the executable behavior.
Do not preserve two live procedures as a compatibility workaround.

## Start here

- Repository quick start: [`../README.md`](../README.md)
- PCB lifecycle skill: [`../skills/pcb-design/SKILL.md`](../skills/pcb-design/SKILL.md)
- PCB execution graph:
  [`../skills/pcb-design/references/execution-graph.md`](../skills/pcb-design/references/execution-graph.md)
- KiCad electrical/layout owner:
  [`../skills/kicad-pcb/SKILL.md`](../skills/kicad-pcb/SKILL.md)
- JLC fabrication owner:
  [`../skills/jlcpcb-fab/SKILL.md`](../skills/jlcpcb-fab/SKILL.md)
- Enclosure owner:
  [`../skills/pcb-enclosure/SKILL.md`](../skills/pcb-enclosure/SKILL.md)
- Forward work registry: [`../improvements.md`](../improvements.md)

## Accepted decisions

ADRs govern forward architecture. Supersede an accepted ADR with a later ADR;
do not silently rewrite its decision.

| ADR | Decision |
|---|---|
| [`0001`](decisions/0001-tscircuit-authoring-boundary.md) | TSX/tscircuit authoring boundary |
| [`0002`](decisions/0002-tscircuit-native-pipeline.md) | Native tscircuit/KiCad pipeline |
| [`0003`](decisions/0003-status-beacon.md) | One live status beacon |
| [`0004`](decisions/0004-gate-integrity.md) | Gate integrity and non-vacuity |
| [`0005`](decisions/0005-imported-facts.md) | Imported fact authority |
| [`0006`](decisions/0006-fab-artifacts-are-graded-as-the-recipient-parses-them.md) | Grade fabrication artifacts as the recipient parses them |
| [`0007`](decisions/0007-claims-become-checks.md) | Claims become executable checks |
| [`0008`](decisions/0008-declarative-pipeline-stage-contract.md) | Declarative stage contract |
| [`0009`](decisions/0009-external-hardware-registry-path.md) | Clear path for foreign-device fact authority |
| [`0010`](decisions/0010-retire-unused-tscircuit-module-registry.md) | Retire the unused shared tscircuit module experiment |

## Measured evidence

These documents explain what was demonstrated at named subjects/commits. They
support decisions but do not replace the owning skill procedure.

| Evidence | Scope |
|---|---|
| [`generic-generator-proof.md`](generic-generator-proof.md) | Generic board generation proof |
| [`generic-router-proof.md`](generic-router-proof.md) | Generic routing proof |
| [`denominator-census.md`](denominator-census.md) | Coverage/denominator census |
| [`pipeline-reliability.md`](pipeline-reliability.md) | Runtime and reliability measurements |
| [`pipeline-shadow-canaries.md`](pipeline-shadow-canaries.md) | Dated rollout/canary evidence; not current authority |
| [`fabricated-examples.md`](fabricated-examples.md) | Prompt, photograph, and rendering provenance plus claim limits for the README showcase |

## Historical plans and snapshots

The following are retained only to explain why current behavior exists. They
are not entry points and must not be used as command or ownership authority:

- [`pipeline-fix-master-plan.md`](pipeline-fix-master-plan.md)
- [`history/2026-08-02-fix-pcb-design.md`](history/2026-08-02-fix-pcb-design.md)
- [`history/2026-08-02-routing-industry-plan.md`](history/2026-08-02-routing-industry-plan.md)
- [`history/2026-08-02-routing-investigation.md`](history/2026-08-02-routing-investigation.md)
- [`history/2026-07-30-resume-state.md`](history/2026-07-30-resume-state.md)

The [`history/` index](history/README.md) records why each retained document is
non-authoritative and where its current owner lives.

Git history is the source for earlier versions. Unresolved work harvested from
these documents belongs in `improvements.md`; current procedure belongs in the
owning skill reference.

## Document classes

| Class | Mutability | Required content |
|---|---|---|
| Skill entry | Update with current workflow | Outcome, quick path, authority routing, invariants |
| Owning reference | Update with current procedure | Inputs, actions, outputs, failure/backtrack, runnable validation |
| Contract | Update structurally; sealed copies immutable | Allowed artifacts, mutability, validation |
| ADR | Append-only after acceptance | Context, decision, consequences, supersession |
| Proof/evidence | Extend or supersede with measured runs | Exact subject, method, denominator, result, limits |
| Improvement | Append/update status until closed | Owner, landing point, completion evidence |
| Journal/review | Immutable observation after adoption/seal | Exact subject and observed result |
| Historical plan | Frozen context | Prominent non-authoritative classification |

## Documentation maintenance

For a PCB workflow change:

1. change the owning implementation and tests;
2. update one owning reference and its skill route;
3. update the declarative graph/catalog if stage composition changed;
4. record incomplete follow-up work in `improvements.md`;
5. run link, authority, contract, and domain tests;
6. commit implementation, evidence, and documentation at the same green
   boundary when they describe one change.

Do not add a second quick-reference document. Improve the root README, the
skill entry, or the owning reference instead.
