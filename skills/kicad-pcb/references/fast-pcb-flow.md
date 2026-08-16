# Fast PCB flow: stage, handoff, timing, and test contract

Use `scripts/pcb_flow.py` as the thin orchestration layer around the existing
geometry and release tools.  It does not replace them:

- `escape_check.py` owns package escape and pad-launch feasibility.
- `route_and_stitch_generic.py` owns routing and deterministic copper.
- `grind_driver.py` owns bounded mechanical convergence.
- `jlcpcb-fab` owns fabrication, PCBA, stock, 3D-model, polarity, and sealed
  release gates.

## Contents

1. State machine
2. Route configuration contract
3. Commands
4. Handoff and performance contracts
5. Testing pyramid

## State machine

```text
legacy_unmigrated  (historical release evidence remains valid; new flow absent)

architecture -> sourcing -> schematic -> placement -> routing -> grind
                                                        |         |
                                                        +---------+
                                                             |
                                                       layout_sealed
                                                             |
                                                        fabrication
                                                             |
                                                       release_sealed
```

`layout_sealed` means one canonical rebuild followed by a fresh KiCad
`--severity-all --refill-zones --schematic-parity` result of `0/0/0`.  It does
not mean orderable.  `release_sealed` is reserved for the jlcpcb-fab battery.

## Route configuration contract

Add this optional process block to `03_src/route.yaml`:

```yaml
flow:
  paths:
    # Defaults for a single-board 03_src/route.yaml are shown. For a nested
    # 03_src/<board>/route.yaml, state_dir defaults to 06_build/<board> and
    # rebuild defaults beside that route config.
    board_id: my-board
    state_dir: 06_build
    rebuild: 03_src/rebuild_all.sh
    journal: 01_docs/journal/routing.md
  # Optional arguments are part of the canonical rebuild command. A board
  # with a content-addressed human-review pause can use its verified resume
  # arm here; this is not a skip-rebuild switch.
  rebuild_args: [--resume-after-schematic-review]
  inputs:
    # Optional on a single-board project. REQUIRED for a multi-board project:
    # hash and preflight only this board's consumed inputs and dossiers.
    include: [03_src, 03_tscircuit, 04_kicad/my-board.kicad_sch,
              04_kicad/my-board.kicad_pro, 04_kicad/my-board.kicad_dru]
    parts: [02_parts]
    # Add shared/external producer tools beyond the conductor's default set.
    tools: []
  owner:
    stage: routing
    files: [03_src/route.yaml, 03_src/floorplan.yaml,
            03_src/route/final_chain.kicad_pcb]
  copper:
    deterministic: [prep.seed_stubs, stitch.seed_stubs, route.final]
    stochastic: [route.waves]
  budgets_s:
    escape_packages: 30
    escape_lands: 120
    tier_preflight: 15
    grind: 900
    rebuild: 1200
    layout_drc: 120
  blockers: []
```

A configuration path cannot be both deterministic and stochastic.  The
handoff names the current owner and owned files so parallel agents do not edit
the same routing surface. Owned source/control files must exist; a promoted
`.kicad_pcb` may be reserved before the first routing run creates it.

Pre-route reviews bind a versioned semantic digest of `03_src/rules/*.yaml`
and the design-bearing portions of `route.yaml`. YAML formatting plus
`project`, `flow`, placement-output path, route-output/tool/import path, and
race-count controls are provenance and orchestration, not adopted design
rules; changing them does not manufacture a new human review subject. Seed
copper, keepouts, route waves/common policy, taps, stitch policy, critical-path
declarations, and every rules YAML remain review-invalidating.

For a multi-board project, keep one config at `03_src/<board>/route.yaml` and
select it with `--board <board>`. The conductor refuses an ambiguous root and
refuses a nested config without explicit `flow.inputs.include` and
`flow.inputs.parts`. Gate, handoff, timing, grind, and seal evidence then live
under that board's `state_dir`; sibling inputs cannot overwrite or stale it.

## Commands

```bash
PY=/usr/bin/python3
F=skills/kicad-pcb/scripts/pcb_flow.py

$PY "$F" preflight PROJECT
$PY "$F" grind PROJECT --max-cycles 12
$PY "$F" handoff PROJECT
$PY "$F" validate PROJECT
$PY "$F" layout-seal PROJECT

# Multi-board form (or use --route-config for an exact config path):
$PY "$F" preflight PROJECT --board BOARD
$PY "$F" handoff PROJECT --board BOARD

# Time any stage and fail distinctly (exit 6) on a wall-time regression.
$PY "$F" run PROJECT --stage render --budget-s 30 -- COMMAND ARG...
```

`preflight` runs package escape, P-LAND, and tier consistency before routing.
`grind` delegates to the existing classified, D-BACK-bounded driver.
`layout-seal` validates the complete flow contract before mutating evidence,
runs package/tier preflight, the canonical rebuild driver (plus any declared
`flow.rebuild_args`), **P-LAND against the newly rebuilt board**, then fresh
DRC. A resume argument is valid only when the rebuild driver itself verifies a
content-addressed review checkpoint and still regenerates the board. It
prepares the bounded handoff before publishing the seal witness; failure
cannot leave a valid-looking witness. There is deliberately no stale-board
shortcut.

The canonical rebuild owns the track-free placement review and runs it before
route import. The seal conductor must not rerun that hash check after copper is
present: a routed board is a different lifecycle artifact. It instead repeats
placement clearances, landing, separation and policy checks on the routed
board, requires connected critical paths and fresh 0/0/0 DRC; final routed
human reviews remain the release-stage boundary.

## Handoff contract

`06_build/agent_handoff.yaml` is generated, never narrated by hand.  It is
bounded to 16 KiB and contains:

- stage and scope;
- semantic source hash including top-level tscircuit controls and active KiCad
  schematic/project/rules, exact board hash, shared-tool hash, and exact fresh
  gate hash;
- DRC/unconnected/parity counts;
- latest per-stage timings;
- owner, owned files, blockers, and canonical next commands.

`validate` returns exit 2 when any bound input changes. Handoff generation
refuses a gate older than the board or its active KiCad semantics. Generate a
new handoff only after re-measuring; never repair a stale hash by editing YAML.

## Performance contract

`06_build/performance.json` is append-only (last 200 samples).  The flow
wrapper records full stages.  The generic router records every KRT wave and
every stitch pass, immediately after the pass, so a crash or SWIG re-exec does
not erase the expensive prefix.

When a budget is exceeded, preserve the measurement and investigate the
largest stage first.  Do not weaken correctness gates to meet a time budget.
Typical remedies, in order:

1. Move a static failure into `preflight`.
2. Promote repeated hand geometry into deterministic config.
3. Use `quick` inside the loop; reserve full DRC for the handoff/seal boundary.
4. Race only stochastic route waves, in isolated candidates, then measure.
5. Add or repair spatial indexing inside `pcb_toolkit.py`; do not create a
   second collision implementation.

## Testing pyramid

Every process change needs both a green and a red path.

1. **T1 schema/unit:** flow schema, gate parsing, canonical hashing, ownership
   disjointness, size ceiling.
2. **T2 hermetic integration:** handoff generation/validation; source, board,
   tool and gate staleness; stale-gate generation refusal; transactional seal;
   dirty-gate refusal; budget exit; dry-run command coverage.
3. **T2 PCB fixtures:** exact-collision and escape fixtures remain owned by
   `t1_escape_tier.py`, `t2_route_stitch.py`, and `t2_grind.py`.
4. **T3 project canary:** run `preflight`, `handoff`, and `validate` against a
   real board; `layout-seal` for release candidates.
5. **T5 clean-room canary:** a fresh agent follows only the skill and brief;
   grade its artifacts independently.

Required known-bad cases: vacuous/scoped part inputs, impossible pad launch,
overlapping deterministic/stochastic ownership, dirty or stale gate presented
as current, stale source/board/tool/gate hashes, handoff failure during seal,
oversized handoff, ambiguous or unscoped multi-board input, unbounded grind
attempt, and exceeded budget.
