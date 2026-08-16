---
name: pcb-design
description: Drive a PCB from a user brief through requirements, architecture, sourced parts, readable schematic, placed/routed KiCad board, independent verification, JLCPCB PCBA release, first article, and publication. Use for new end-to-end board designs or resuming, reviewing, releasing, or publishing a board pipeline.
---

# `/pcb-design` — brief to verified assembled board

Deliver a populated, reviewable board—not merely Gerbers or DRC-clean copper.
Orchestrate the lifecycle; delegate electrical/layout mechanics to `kicad-pcb`
and manufacturer/assembly mechanics to `jlcpcb-fab` through the reference
router below.

## Outcome and authority

Every new board targets assembly unless the user explicitly chooses otherwise.
Every assembled footprint must be JLC sourced, consigned, or covered by a
dated, measured assembly disposition. A release is a complete immutable archive
with exact source, fab payload, human documents, 3D evidence, verification,
order instructions, and manifest.

Authority is deliberately singular:

- `pcb-design`: brief, lifecycle, stage composition, handoffs, independent
  reviews, release seal, publication, first-article transition;
- `kicad-pcb`: schematic/netlist, placement, geometry, routing, DRC/parity,
  impedance and RF realization;
- `jlcpcb-fab`: Gerber/drill/BOM/CPL, stock, population, rotation, JLC twin,
  model registration and manufacturer staging;
- project `contracts.md`: exact artifact membership and immutable seal rules;
- scripts and their `--help`: exact command syntax and executable predicates;
- `improvements.md` and project journals: rationale/history, never authority.

Do not restate an owning procedure in another skill. Link to it. If two sources
conflict, stop, inspect executable behavior and tests, then correct the stale
source in a separate, evidenced change.

## Entry protocol

1. Preserve the user's brief verbatim in `01_docs/BRIEF.md`.
2. Inspect repository status, project contracts, live beacon, journal tail,
   exact handoff, and latest non-superseded release before acting.
3. Determine whether this is commission, resume, repair, review, release-only,
   publication-only, or first-article work.
4. Write a capability profile before selecting procedures:

```json
{
  "schema": 1,
  "signal_integrity": "ordinary | high_speed_digital | rf",
  "assembly": "jlcpcb | none | other",
  "firmware": "forbidden | requested",
  "foreign_mating": false,
  "target": "design | release | publication | first_article | production"
}
```

5. Default `firmware` to `forbidden`. Do not create, modify, build, or release
   firmware unless the user explicitly requests it. A programmable IC does not
   imply firmware scope.
6. Run `scripts/skill_reference_router.py` in plan mode. Read every selected
   procedure completely before its stage and do not load unselected domain
   references.
7. Keep current project drivers and gates authoritative. The typed plan is a
   composition/coverage guard until a project has an approved equivalent trace.

## Reference router

Read these files directly when their condition applies. References longer than
100 lines contain a contents list.

| Condition | Owner | Read completely |
|---|---|---|
| Commission, requirements, fact locks, sourcing, module/package choice | pcb-design | `references/commission-and-scope.md` |
| Any stage execution, handoff, timeout, plateau, or backtrack | pcb-design | `references/lifecycle-and-backtrack.md` |
| Human review, staging, seal, supersede, publication, readiness report | pcb-design | `references/review-and-publication.md` |
| Adding/changing orchestration stages, identities, bundles, reviews, facts | pcb-design | `references/pipeline-stage-contract.md` |
| Choosing model/compute tier | pcb-design | `references/compute-tiers.md` |
| Electrical and machine/human policy canon | kicad-pcb | `../kicad-pcb/references/design-policies.md` |
| TSX/KiCad schematic generation and readability | kicad-pcb | `../kicad-pcb/references/schematic-generation.md` and `../kicad-pcb/references/tscircuit-folder.md` |
| Placement, adjacency, body/courtyard and corridor checks | kicad-pcb | `../kicad-pcb/references/placement-and-proximity.md` |
| Route preparation, KRT, stitch, grind and DRC | kicad-pcb | `../kicad-pcb/references/routing-pipeline.md` and `../kicad-pcb/references/fast-pcb-flow.md` |
| Datasheet/reference-layout precedent selection | kicad-pcb | `../kicad-pcb/references/layout-precedents.md` |
| RF/impedance/phase/isolation applies | kicad-pcb | `../kicad-pcb/references/rf/rf-context.md` plus the applicable RF review protocol linked here: `../kicad-pcb/references/rf-schematic-review-protocol.md`, `../kicad-pcb/references/rf-pcb-review-protocol.md`, `../kicad-pcb/references/rf-fab-review-protocol.md` |
| JLC BOM/CPL, stock, rotation, uploader review | jlcpcb-fab | `../jlcpcb-fab/references/assembly-and-order.md` |
| JLC CAD twin, model transforms, bounding boxes/registration | jlcpcb-fab | `../jlcpcb-fab/references/digital-twin.md` |
| Exact JLC fabrication/assembly staging | jlcpcb-fab | `../jlcpcb-fab/references/release-staging.md` |

For exact CLI flags, run the owning script with `--help`; do not load a long
procedure solely to recover syntax.

## Non-negotiable invariants

1. Keep one live writer per board. Parallel work is independent research,
   calculation, or read-only review in isolated worktrees.
2. Fix source and regenerate downstream. Never hand-edit generated KiCad,
   routed output, CSV, twin, or staged release bytes.
3. Make every load-bearing claim `MEASURED` with method or `INHERITED` with
   source and unverified status.
4. Require nonzero denominators. `0 findings` over `0 graded` is not a pass.
5. Bind reviews and accepted artifacts to exact semantic and raw identities.
6. Give executable stages deadlines and visible progress. Timeout, incomplete,
   or stale evidence never becomes PASS.
7. Preserve the previous accepted bundle when a producer fails.
8. Commit at green stage boundaries and promote the final route chain into
   source.
9. Treat DRC, parity, generation, fabrication, review, seal, publication,
   orderability, first article, and production as different claims.
10. Run cheap schema, source, and geometry gates before expensive producers or
    human review.
11. Review schematic readability at the first judgeable schematic and model/
    placement registration before trusting final renders.
12. Start at the cheapest fabrication tier that can meet the locked facts;
    advanced capability requires measured need and an ADR.

## Lifecycle

| Stage | Required result before advancing | Procedure owner |
|---|---|---|
| Commission | Verbatim brief, capability/fact locks, explicit firmware and mating posture | pcb-design commission |
| Architecture | Topology/protection/measurement boundaries and decisions are falsifiable | pcb-design + KiCad policy |
| Sourcing | Exact dossiers, two-source feasibility, escape/tier/layout precedent evidence | pcb-design commission |
| Schematic | Fresh producer diagnostics, ERC/parity/semantic gates and adopted independent topology/readability reviews | kicad-pcb schematic |
| Placement | Exact part/pin identity, body clearance, adjacency/corridor/precedent gates and adopted pin/layout/render reviews | kicad-pcb placement |
| Routing | Critical inventory, tier preflight, deterministic prep, bounded route/stitch, realized copper audits, DRC 0/0/0 | kicad-pcb routing |
| Layout seal | Fresh canonical rebuild, promoted route, exact board identity and applicable RF realized evidence | kicad-pcb flow |
| Fabrication | Exact JLC payload, BOM/CPL/stock/population/rotation/twin/process evidence | jlcpcb-fab |
| Release staging | Self-contained archive and complete scoped independent review battery | pcb-design review |
| Release seal | Normative two-commit seal, clean manifest and refreshed beacon | project release contract |
| Publication | Publication gate passes against base/head and repository protection applies | pcb-design publication |
| First article | Physical inspection and contract-owned electrical/RF/thermal tests pass | project test plan |
| Production | First-article evidence closes every production hold | pcb-design lifecycle |

### Stage loop

```text
enter(X)
  validate inputs + applicability + subject identity
  perform bounded work with progress
  run owning gate
    PASS                 -> persist result; commit; journal finish; advance
    FAIL and improving   -> journal iteration; change owning source; repeat
    plateau / no remedy  -> classify cause; D-BACK to owner; regenerate
    human evidence owed  -> persist INCOMPLETE commission; pause visibly
    timeout/error        -> keep prior accepted bundle; diagnose
```

Use `StageSpec`/`StageResult` for orchestration metadata. Paths, CLI commands,
and numeric design limits do not belong in stage semantic identity. Unknown
applicability fails; non-applicability requires a reason and zero denominator.

## Commission through sourcing

Read `commission-and-scope.md`. Do not begin architecture until voltage/current
envelopes, simultaneous loads, measurement plane, protection, off-control,
foreign mating, fabrication ceiling, and firmware posture are locked.

Resolve `D-SPEC`, `D-MATE`, `D-MOD`, `D-ESC`, `D-LAYOUT`, `D-TIER`, and
two-source feasibility before detailed generation. Part dossiers must derive
physical pin maps and package/land-pattern facts from authoritative figures.
Volatile price/stock belongs in build evidence; durable identities belong in
dossiers and source.

## Schematic

Load the KiCad schematic procedures. Author TSX as the standard front end and
use the shared generic backend; use schwriter only for a documented unsupported
case. Pin dependencies exactly and keep the lockfile.

Run inexpensive source/schema/count/producer-diagnostic checks before TSX
generation and immediately after it. Bind a human schematic PDF to the exact
Circuit JSON. Stop at the schematic checkpoint until independent topology and
readability witnesses are admissible. A machine-readable but unreadable
schematic does not pass.

## Placement and routing

Load only the applicable KiCad placement/routing references. Prove package
escape, part/pin identity, native-polygon body/courtyard clearance, datasheet
adjacency, corridor capacity, and critical-pair inventory before router spend.

For high-speed digital or RF, activate the conditional signal-integrity
adapter and its source/realized/fab reviews. Bind physical P/N chains,
layer/reference plane, differential engine, via policy, and length tolerance
before routing. High-speed digital may defer coordinate geometry to placement;
microwave designs may own it at source. Do not add a separate unbounded wait
stage.

Route from a track-free, unfilled deterministic input. Run the mechanical grind
at the cheapest tier, stop on the bounded plateau trigger, fix upstream source,
and regenerate. Full DRC requires zero violations, zero unconnected, and zero
parity findings at full severity after rules are emitted last.

## Fabrication and assembly

Load the three JLC procedures only after layout seal. Export source-derived
payloads atomically. Enforce exact BOM identity and legibility, stock verdict,
population coverage, measured A-ROT authority, JLC CAD fit, mounted-body
coverage, same-camera render registration, via process, and payload census.

Capture JLC's final stackup/impedance, via-fill/cap, BOM, rotation, and THT
assembly previews. Public capability tables establish feasibility but do not
prove final uploader selections. Keep the board `DO-NOT-ORDER` or
`FIRST-ARTICLE-ONLY` while order-side evidence is owed.

## Review, seal, and publication

Read `review-and-publication.md`. Run the full review battery once per material
state; scope fix-pass reviews to changed items plus one integrated fresh lens.
All reviews target pre-seal staging and carry parseable design/order verdicts.

Follow only the normative seal procedure in the project `07_releases` contract.
Never mutate a sealed release. Before merging or pushing a design state to the
publication branch, run:

```text
python3 skills/pcb-design/scripts/pcb_publication_gate.py \
  --base <publication-base-sha> --head <candidate-head-sha>
```

Require `P-PUBLISH PASS`. A generated board, DRC 0/0/0, fab preflight, or
manifest does not imply review, seal, publication, order, or production.

## Backtracking and handoff

Read `lifecycle-and-backtrack.md` whenever a gate repeats, a stage waits, or a
session approaches a planned boundary. After three non-improving iterations,
stop local grind, group findings by cause, verify the causal artifact, commit
the failed evidence, and reopen the upstream owner.

Planned handoffs occur after schematic review and layout seal. Persist a compact
content-addressed handoff, refresh the live beacon, append the journal event,
and let a fresh successor resume from repository state. Do not preload history
directories or repeatedly resume a context-heavy agent for mechanical work.

## Compatibility and maintenance

The progressive-disclosure structure must preserve observable behavior:

```text
capability profile -> selected authorities -> ordered StageSpecs
  -> gates/artifacts -> review pauses -> backtrack targets -> release claim
```

Run `scripts/skill_authority_check.py` after changing a skill/reference/router.
It must prove line/word budgets, direct references, unique domain authority,
legacy gate reachability, and fixture profile traces. Run the pipeline unit
tests and the USB Hub v4 and Pluto v4 shadow canaries before changing execution
authority. A fail-closed review pause is compatible behavior; do not force a
green canary by fabricating evidence.

Keep the current driver authoritative until its ordered applicability,
identity, outputs, results, and blockers agree with the typed trace. Preserve
the previous skill through Git history, not a second live legacy file.

## Report

Report decisions and assumptions, measured gate scoreboard with denominators,
design/order verdicts, release path and source/seal commits, and every order-day
or first-article hold. Mark claims as measured or inherited. Use readiness
language matching the strongest proven lifecycle stage.
