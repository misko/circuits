# PCB execution graph

This document is the map of the PCB lifecycle. It separates the declarative
plan from the commands that actually change a project, because treating those
as one graph makes a plan look like evidence and makes an old receipt look like
a completed rebuild.

## Contents

1. [The three graph layers](#the-three-graph-layers)
2. [Lifecycle graph](#lifecycle-graph)
3. [Stage catalog](#stage-catalog)
4. [Project execution graph](#project-execution-graph)
5. [Routing subgraph](#routing-subgraph)
6. [Release, publication, and first article](#release-publication-and-first-article)
7. [Results, retries, and backtracking](#results-retries-and-backtracking)
8. [Reproduce the plan](#reproduce-the-plan)

## The three graph layers

| Layer | Authority | What it proves | What it cannot prove |
|---|---|---|---|
| Disclosure plan | `skill-authority-map.json` resolved by `skill_reference_router.py` | The capability profile selects a composable ordered set of stages and owning references. | No command ran; no project input was opened; no gate passed. |
| Project conductor | `03_src/rebuild_all.sh`, `03_src/rebuild_reuse.sh`, and `pcb_flow.py` | The exact project driver invoked bounded commands in its recorded order. | A successful command is not automatically a reviewed layout, release, order, or physical article. |
| Owning gates | KiCad, JLC, review, release, and first-article scripts | A named predicate graded exact subjects and wrote a reopenable result. | One domain result cannot promote a stronger lifecycle claim owned elsewhere. |

The typed plan is deliberately `DISCLOSURE_ONLY`. Conditional stages that are
not selected produce `UNKNOWN` dependency placeholders so the graph stays
composable; those placeholders are not `NOT_APPLICABLE` evidence. Engineering
applicability comes from project source plus the owning gate.

`pipeline_execution.execute_attempt()` is an execution primitive, not the
top-level conductor for current projects. No production driver consumes the
typed `StageSpec` list end to end. Until that changes, the project shell driver
and each owning gate remain authoritative for work and verdicts.

## Lifecycle graph

```mermaid
flowchart LR
  C[PCB-COMMISSION] --> A[PCB-ARCHITECTURE]
  A --> S[PCB-SOURCING]
  S --> RC{RF?}
  RC -->|yes| RCTX[KICAD-RF-CONTEXT]
  RCTX --> RSRC[KICAD-RF-SOURCE]
  RSRC --> SCH[KICAD-SCHEMATIC]
  RC -->|no| SCH
  SCH --> PLC[KICAD-PLACEMENT]
  PLC --> MATE{Foreign mating?}
  MATE -->|yes| MI[KICAD-MATING-IMPORT]
  MI --> ROUTE[KICAD-ROUTING]
  MATE -->|no| ROUTE
  ROUTE --> RR{RF?}
  RR -->|yes| RREAL[KICAD-RF-REALIZED]
  RREAL --> LSEAL[KICAD-LAYOUT-SEAL]
  RR -->|no| LSEAL
  LSEAL --> FAB[JLC-FABRICATION]
  FAB --> ASM[JLC-ASSEMBLY-VERIFY]
  ASM --> RFAB{RF?}
  RFAB -->|yes| RFR[JLC-RF-FAB-REVIEW]
  RFR --> REV[PCB-RELEASE-REVIEW]
  RFAB -->|no| REV
  REV --> SEAL[PCB-RELEASE-SEAL]
  SEAL --> PUB[PCB-PUBLICATION]
  SEAL --> FA[PCB-FIRST-ARTICLE]
  FA --> PROD[PCB-PRODUCTION]
```

The target truncates this graph:

- `design` ends at `KICAD-LAYOUT-SEAL`;
- `release` ends at `PCB-RELEASE-SEAL`;
- `publication` adds `PCB-PUBLICATION`;
- `first_article` adds `PCB-FIRST-ARTICLE`;
- `production` adds `PCB-FIRST-ARTICLE` and `PCB-PRODUCTION`.

High-speed digital adds signal-integrity procedures inside schematic,
placement, routing, fabrication, and first article. It does not select the RF
stages. Firmware is a separate requested handoff and never appears as a PCB
stage.

## Stage catalog

This table mirrors `skill-authority-map.json`. Inputs and outputs are semantic
artifact roles, not paths. An omitted conditional predecessor is represented by
an unknown disclosure placeholder until an owning project gate establishes its
actual applicability.

| # | Stage | Owner | Selected when | Requires | Produces |
|---:|---|---|---|---|---|
| 1 | `PCB-COMMISSION` | pcb-design | always | — | `commissioned_brief` |
| 2 | `PCB-ARCHITECTURE` | pcb-design | always | `commissioned_brief` | `architecture_locked` |
| 3 | `PCB-SOURCING` | pcb-design | always | `architecture_locked` | `parts_locked` |
| 4 | `KICAD-RF-CONTEXT` | kicad-pcb | RF | `parts_locked` | `rf_context` |
| 5 | `KICAD-RF-SOURCE` | kicad-pcb | RF | `rf_context` | `rf_source_clearance` |
| 6 | `KICAD-SCHEMATIC` | kicad-pcb | always | `parts_locked`, `rf_source_clearance` | `schematic_reviewed` |
| 7 | `KICAD-PLACEMENT` | kicad-pcb | always | `schematic_reviewed` | `placement_reviewed` |
| 8 | `KICAD-MATING-IMPORT` | kicad-pcb | foreign mating | `placement_reviewed` | `mating_clearance` |
| 9 | `KICAD-ROUTING` | kicad-pcb | always | `mating_clearance`, `placement_reviewed` | `routed_board` |
| 10 | `KICAD-RF-REALIZED` | kicad-pcb | RF | `routed_board` | `rf_realized_clearance` |
| 11 | `KICAD-LAYOUT-SEAL` | kicad-pcb | always | `rf_realized_clearance`, `routed_board` | `layout_sealed` |
| 12 | `JLC-FABRICATION` | jlcpcb-fab | release or later | `layout_sealed` | `fabrication_staged` |
| 13 | `JLC-ASSEMBLY-VERIFY` | jlcpcb-fab | release or later | `fabrication_staged` | `assembly_verified` |
| 14 | `JLC-RF-FAB-REVIEW` | jlcpcb-fab | RF release or later | `fabrication_staged`, `rf_realized_clearance` | `rf_fab_clearance` |
| 15 | `PCB-RELEASE-REVIEW` | pcb-design | release or later | `assembly_verified`, `rf_fab_clearance` | `release_reviewed` |
| 16 | `PCB-RELEASE-SEAL` | pcb-design | release or later | `release_reviewed` | `sealed_release` |
| 17 | `PCB-PUBLICATION` | pcb-design | publication | `sealed_release` | `published_design` |
| 18 | `PCB-FIRST-ARTICLE` | pcb-design | first article or production | `sealed_release` | `first_article_evidence` |
| 19 | `PCB-PRODUCTION` | pcb-design | production | `first_article_evidence` | `production_authorized` |

## Project execution graph

### Schematic or source changed

The bootstrap hold starts at `PCB-COMMISSION` and spans the separately typed
commission, architecture, and sourcing admission stages. After all three have
their required reviewed evidence and `01_docs/COMMISSIONING-HOLD.md` is removed
in that admission change, run the project's full conductor:

```bash
bash projects/<name>/03_src/rebuild_all.sh
```

The normal path intentionally pauses. It can stop for an accepted PCBA
prelayout response, schematic review, placement review, or another declared
operator checkpoint. A typed `INCOMPLETE` at one of these boundaries is a
successful refusal to overclaim, not a broken build.

After the exact schematic checkpoint is accepted, continue without rerunning
the nondeterministic TSX producer:

```bash
bash projects/<name>/03_src/rebuild_all.sh --resume-after-schematic-review
```

The full conductor performs, in order:

```text
source/schema/architecture/RF preflight
  -> TSX build and producer diagnostics
  -> exact circuit.json handoff and human schematic render
  -> provenance, semantic, sourcing, and ERC gates
  -> schematic checkpoint and independent review
  -> board generation, parity, pin, placement, model, and DRC gates
  -> deterministic route preparation
  -> import the authenticated route source selected by route.yaml
  -> taps, stitch/fill, final rules, RF-realized checks
  -> full route-acceptance receipt
```

`rebuild_all.sh` does not search for a fresh route. It prepares the deterministic
input and replays the route selected by `03_src/route.yaml`. This is what makes
the canonical rebuild reproducible.

### Schematic unchanged

Use the deterministic route-authority rebuild:

```bash
bash projects/<name>/03_src/rebuild_reuse.sh
```

It consumes the pinned generated schematic, regenerates board/rules from source,
replays the authenticated route source selected by `route.yaml`, stitches/fills,
and reruns full acceptance. It is the fast iteration and verification path, not
permission to ignore a changed schematic. Most established projects select a
promoted chain; a reviewed configuration may select a bound build source.

Selected bounded or long-running driver commands are wrapped by:

```bash
python3 skills/kicad-pcb/scripts/pcb_flow.py run \
  projects/<name> --stage <stage-name> -- <owning-command...>
```

For those commands, `pcb_flow.py run` supplies the hard deadline, process-tree
cleanup, progress, and state telemetry. Direct in-process and administrative
driver steps are not automatically covered. The child gate still owns
engineering meaning.

## Routing subgraph

The full fresh-route/build-import/stitch workflow is separate from canonical
rebuild:

```bash
/usr/bin/python3 skills/kicad-pcb/scripts/route_and_stitch_generic.py \
  all projects/<name>/03_src/route.yaml
```

`all` is not a read-only candidate probe. It runs preparation, route search,
build-source import, taps, and stitch; without a transaction-local target it
updates the board selected by the project configuration. Use isolated candidate
workspaces and review the exact target before invoking it.

The explicit subcommands are:

```text
prep -> route -> import build -> taps -> stitch -> verify-fill
```

Important branches:

- `route --race N` evaluates isolated candidates and promotes only a clean
  winner; a dirty race has no winner.
- `route --through-wave <id>` emits an authenticated resumable prefix but no
  final-route claim.
- `route --resume` reopens the prefix/config/hash chain before continuing.
- `quick` is the seconds-fast iteration predicate; it is not release admission.
- `import --route-source promoted` replays committed route authority.

The bounded repair loop is:

```bash
/usr/bin/python3 skills/kicad-pcb/scripts/grind_driver.py projects/<name>
```

It stops on the configured attempt limit, repeated unconnected set, or
non-improving plateau. A stop backtracks to source, ownership, endpoint escape,
plane fill, or placement; it is not permission to keep grinding.

Final route admission is one full receipt:

```bash
/usr/bin/python3 skills/kicad-pcb/scripts/route_acceptance_gate.py grade \
  projects/<name> \
  --board projects/<name>/04_kicad/<board>.kicad_pcb \
  --mode full \
  --drc-json projects/<name>/06_build/drc/gate.json \
  --json projects/<name>/06_build/verification/route_acceptance_receipt.json
```

Use the same script's `verify` subcommand to reopen the receipt. The full mode
binds native DRC, parity, connectivity, route ownership, via/copper/reference
checks, and the unchanged board identity. Shadow comparisons are diagnostic and
cannot change that receipt.

The deterministic reuse conductor writes its native DRC detail under
`06_build/route/gate.json`; both conductors publish the same canonical
`06_build/verification/route_acceptance_receipt.json` authority.

## Release, publication, and first article

`layout-seal` closes the PCB layout only:

```bash
/usr/bin/python3 skills/kicad-pcb/scripts/pcb_flow.py layout-seal \
  projects/<name>
```

JLC tooling then stages exact fabrication and assembly evidence. The PCB design
owner composes independent reviews and seals an immutable candidate release.
A sealed candidate may still be `DO-NOT-ORDER`; ordering is a distinct claim.

Initialize the mutable candidate declaration before expensive staging gates,
then rehearse, reopen, and admit the exact accepted receipt:

```bash
/usr/bin/python3 skills/pcb-design/scripts/release_rehearsal.py init \
  projects/<name>/07_releases/<candidate> \
  --project projects/<name>

/usr/bin/python3 skills/pcb-design/scripts/release_rehearsal.py rehearse \
  projects/<name>/07_releases/<candidate> \
  --project projects/<name> \
  --output projects/<name>/06_build/release_rehearsal/<candidate>.json

/usr/bin/python3 skills/pcb-design/scripts/release_rehearsal.py verify \
  projects/<name>/06_build/release_rehearsal/<candidate>.json

/usr/bin/python3 skills/pcb-design/scripts/release_rehearsal.py seal \
  projects/<name>/06_build/release_rehearsal/<candidate>.json \
  --output projects/<name>/06_build/release_rehearsal/<candidate>-seal-admission.json
```

`init` writes a loud draft, not a release. `rehearse` and `verify` do not seal;
`seal` emits admission evidence but never commits or publishes. The owning
release contract defines the subsequent immutable two-commit procedure.

Before merging or pushing material PCB changes, grade the publication diff:

```bash
/usr/bin/python3 skills/pcb-design/scripts/pcb_publication_gate.py \
  --base <publication-base-sha> --head <candidate-head-sha>
```

First article is a physical, operator-owned transition:

```bash
/usr/bin/python3 skills/jlcpcb-fab/scripts/first_article_check.py \
  projects/<name> \
  --card projects/<name>/03_src/rules/first_article.yaml \
  --record <measured-record.yaml> \
  --json <first-article-result.json>
```

Only `AUTHORIZED` can feed production. A release archive, order receipt, or
attractive render cannot substitute for measured article evidence.

## Results, retries, and backtracking

```text
enter stage
  -> validate exact inputs and applicability
  -> run bounded producer or review
  -> reopen outputs with the owning gate
     PASS       persist, commit, journal, advance
     FAIL       change owning source and regenerate
     INCOMPLETE persist the owed evidence and pause
     timeout    retain previous accepted bundle and diagnose
     plateau    classify cause and backtrack to the upstream owner
```

Backtracking invalidates downstream artifacts whose semantic inputs changed.
Never repair a generated board, staged package, or sealed release in place.
Change the owning source, regenerate a new candidate, and retain failed evidence
when it explains the decision.

## Reproduce the plan

Resolve an entire capability profile:

```bash
python3 skills/pcb-design/scripts/skill_reference_router.py \
  --profile projects/<name>/01_docs/capability-profile.json \
  --json
```

Resolve the full plan while narrowing `load_now` to one stage:

```bash
python3 skills/pcb-design/scripts/skill_reference_router.py \
  --profile projects/<name>/01_docs/capability-profile.json \
  --at-stage KICAD-ROUTING \
  --json
```

The output repeats the normalized profile, every selected `StageSpec` row, the
full-plan `references`, stage-local `load_now`, and unknown placeholders.
`--at-stage` narrows only `load_now`; it does not truncate the disclosure plan.
Compare the plan with the project conductor's actual trace; do not treat
equality as execution evidence.
