# contract: 03_src/

**Purpose** — the only hand-written truth about the board's *KiCad-side*
design: placement, rules, the promoted route, and the per-board gates.
Everything in `04_kicad/` and `06_build/` is derived from here plus
`03_tscircuit/`. If `03_src/` and `04_kicad/` disagree, `03_src/` is right and
`04_kicad/` is stale.

**Mutability** — hand-edited.

**Where the generators live** — the heavy pipeline scripts are SHARED and live
in the skill, `skills/kicad-pcb/scripts/`, NOT in this folder. A board does not
carry its own `generate_board.py` / `route_prep.py` / `stitch_and_fill.py`
anymore (those bespoke generators are RETIRED — ADR-0002 / generic backend,
2026-07-20). `03_src/` holds the board-specific **config** the shared scripts
consume, plus a few small per-board emitters/gates.

## Allowed

| File | What | Consumed by |
|---|---|---|
| `floorplan.yaml` | placement config: outline, mounting holes, named regions, anchors, `repeat:` banks, keepouts, zones, silk, orientation asserts | SHARED `generate_board_generic.py` |
| `route.yaml` | routing + stitch config: KRT prep/route/import order, pours, thermal vias, pad-rescue | SHARED `route_and_stitch_generic.py` (`prep`/`route`/`import`/`stitch`) |
| `rules/` | `nets.yaml` (netclasses + ampacity), `policy_waivers.yaml`, `twin_adjudications.yaml` — see `rules/contracts.md` | `generate_rules.py`, policy_audit, jlc_twin |
| `route/` | the PROMOTED KRT chain (`*.kicad_pcb`) — a committed ARTIFACT, not code (canon M3); `import` replays it deterministically | SHARED `route_and_stitch_generic.py import` |
| `generate_rules.py` | the ONLY per-board emitter: writes netclasses into `.kicad_pro` + width floors into `.kicad_dru` from `rules/nets.yaml`. A rules gate, not a generator. | — |
| `audit_board.py` | the placement/pad invariant gate (polarity, proximity, plane-clean, refdes-on-silk, board-specific guards) | — |
| `bom_seed.py` | maps BOM comments → `02_parts/` MPN → LCSC; fails on unmapped/TBD lines | required before ordering |
| `rebuild_all.sh` | THE entry point: thin driver that calls the SHARED generics in canonical order, `set -euo pipefail` | REQUIRED |
| `export_pdfs.sh` | release PDF set (pcb_layers, assembly) + PNG verification renders | |
| `lib/` | project-local footprints tscircuit/KiCad can't yet express — see `lib/contracts.md` | |
| `contracts.md` | this file | |

## The pipeline — what runs, in what order, with which interpreter

`rebuild_all.sh` is the single entry point and the authoritative order. A fresh
agent runs it FIRST. `$S` = `skills/kicad-pcb/scripts` (resolved repo-relative,
`~/.claude/skills/` fallback). Schematic authoring is upstream in
`03_tscircuit/` (see its contract); this stage begins at the netlist.

| Step | Command | Interpreter |
|---|---|---|
| 1 | `03_tscircuit` → netlist (tsci build → `$S/circuit_json_to_kicad_sch.py` → `kicad-cli sch export netlist`) | bun/tsci + `/usr/bin/python3` |
| 2 | ERC gate `kicad-cli sch erc --severity-all` = 0 errors + netlist-parity gate | `kicad-cli` |
| 3 | `$S/generate_board_generic.py 03_src/floorplan.yaml -o 04_kicad/<board>.kicad_pcb` (placement + zones) | `/usr/bin/python3` |
| 4 | `03_src/audit_board.py` (placement/pad invariants) | `/usr/bin/python3` |
| 5 | `03_src/generate_rules.py` — netclasses BEFORE route-prep (canon R1) | any python3 |
| 6 | `$S/route_and_stitch_generic.py prep 03_src/route.yaml` (netclass-carrying, track-free route input) | `/usr/bin/python3` |
| 7 | `$S/route_and_stitch_generic.py import 03_src/route.yaml` (replay the promoted `route/` chain — canon M3) | `/usr/bin/python3` |
| 8 | `$S/route_and_stitch_generic.py stitch 03_src/route.yaml` (pours + thermal vias); verdict must be `gate: clean` | `/usr/bin/python3` |
| 9 | `03_src/generate_rules.py` — ALWAYS LAST (pcbnew saves clobber `.kicad_pro` netclasses) | any python3 |
| 10 | DRC gate `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity` = 0/0/0 | `kicad-cli` |

**External prerequisites** (nothing else):
- KiCad ≥ 10 (`kicad-cli`, `/usr/bin/python3` with `pcbnew` importable)
- the `skills/kicad-pcb/scripts` toolkit (the shared generics) + bun/`tsci`
- KiCadRoutingTools ONLY to re-route from scratch; the committed `route/` chain
  already contains the routing, so the standard rebuild replays it via `import`

## Forbidden

- **A per-board `generate_board.py` / `route_prep.py` / `route_waves.sh` /
  `stitch_and_fill.py`.** These are the RETIRED bespoke generators; the shared
  generics replace them. If the generic backend genuinely cannot express
  something, that is a backend gap (a hooks entry-point candidate) — report it,
  do not hand-write a parallel backend. Every 03_src/generate_board.py was 290–780
  lines the product exists to delete.
- **One-off experiment scripts.** If it ran once and will not run again, it
  belongs in git history, not `03_src/`. Every script here must be runnable
  TODAY against the current board and produce the current result.
- Writing to `07_releases/`. Generators may write `04_kicad/` and `06_build/` only.
- Board data hardcoded where it duplicates `02_parts/` or `rules/`.

## The hard rules for generators (SHARED and per-board alike)

1. **A missing footprint / missing FPID is a HARD ERROR, never a warning.** A
   silent `SKIP U9` shipped a board without its USB ESD array; every
   board-internal gate passed because none compares the board to the schematic.
   The shared `generate_board_generic.py` already raises — never re-introduce a
   soft skip in a per-board script.
2. **A parse that yields zero results is an ERROR.** The netlist format changed
   between KiCad 7 and 10; a same-line regex silently matched nothing. Guard
   every parse with a count assertion.
3. **Never clobber `.kicad_pro` wholesale.** It holds the DRC floors and
   severity policy. `generate_rules.py` merges; it does not rewrite.
4. **Pin numbers are PHYSICAL PADS, from `02_parts/<MPN>/part.yaml`** — not a
   symbol's logical order, not memory. Cite the part file.
5. **Polarity is a fact, not a convention to guess.** KiCad footprints put the
   cathode on pad 1; a generic `1`/`2` symbol lets the author wire it backwards
   and NO electrical check can see it (the netlist is self-consistent either
   way). Three reversed parts shipped this way on one board, including the
   battery connector. `floorplan.yaml` orientation asserts + `audit_board.py`
   check pad 1's net against `part.yaml`.

## Validate — runnable by a fresh agent with zero context

1. `bash 03_src/rebuild_all.sh` completes and the DRC gate's final counts are
   `violations: 0`, `unconnected: 0`, `parity: 0` — this exercises the shared
   generics + the per-board config end-to-end.
2. after the rebuild, `04_kicad/*.kicad_dru` is byte-identical to the committed
   version (fully deterministic). The `.kicad_sch`/`.kicad_pcb` are NOT
   byte-stable (fresh UUIDs, KRT is stochastic) — for those the invariant is the
   GATE result, not the bytes; commit the regenerated files.
3. `03_src/` contains NO retired bespoke generator (`generate_board.py`,
   `route_prep.py`, `route_waves.sh`, `stitch_and_fill.py`) — grep confirms.
4. every remaining `*.py`/`*.sh` in `03_src/` is either in the Allowed table
   above or invoked by `rebuild_all.sh` (`grep <name> 03_src/rebuild_all.sh`).
5. no script writes to `07_releases/`.
6. `.kicad_dru`/`.kicad_pro` netclasses match what `generate_rules.py` emits
   from `rules/nets.yaml` (regenerate and diff — drift means a hand-edited
   generated file).

## Repair

- Retired bespoke generator present → delete it; the shared generic replaces it.
  If it did something the generic can't, file the backend gap first.
- Stale experiment script → delete it; git history keeps it.
- Per-board generator with a soft skip → convert to `raise`.
- Hand-edited `.kicad_dru` → port to `rules/nets.yaml` and regenerate.

## Compliance audit (design-policies.md IDs)

This folder answers: **S1/S4** (ERC gate at severity-all = 0 errors; no_connect
flags for sanctioned floats emitted upstream), **S2** (no auto-named nets reach
copper), **R1** (netclasses exist in the route-INPUT project file — R-RULES
inspects it), **M3** (everything regenerable: the promoted route chain lives in
`03_src/route/` and is committed; `06_build` stays disposable), **M4**
(waivers/adjudications in `rules/` each carry measurement evidence).

- Audit: `policy_audit.py <project>` runs S-ERC, S-NC, S-NET, R-RULES, M-REPRO,
  M-WAIV directly. Zero FAIL required at release.
- Waivers live in `rules/policy_waivers.yaml`:
  `{id: <CHECK-ID>, refs: [...], derived_from: <project?>, why: "<measurement
  evidence>"}` — an entry without evidence is itself a FAIL, and an inherited
  rationale without `derived_from` is a `waiver_provenance` FAIL (W-COPY/W-FOREIGN).
