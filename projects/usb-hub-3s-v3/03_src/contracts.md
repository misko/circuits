# contract: 03_src/

**Purpose** — the only hand-written truth about the board's *KiCad-side*
design: placement, rules, the promoted route, and the per-board gates.
Everything in `04_kicad/` and `06_build/` is derived from here plus
`03_tscircuit/`. If `03_src/` and `04_kicad/` disagree, `03_src/` is right and
`04_kicad/` is stale.

**Mutability** — hand-edited.

**Where the generators live** — the heavy pipeline scripts are SHARED and live
in the skill, `skills/kicad-pcb/scripts/`, NOT in this folder: `generate_board_generic.py`,
`route_and_stitch_generic.py`, and `generate_rules_generic.py`. A board does not
carry its own `generate_board.py` / `route_prep.py` / `stitch_and_fill.py` /
`generate_rules.py` anymore (those are RETIRED — ADR-0002 / generic backend,
2026-07-20; `generate_rules` was promoted to the shared emitter after a
clean-room run proved its logic is 100% board-independent). `03_src/` holds the
board-specific **config** the shared scripts consume, plus exactly ONE small
per-board gate: `audit_board.py` (board-specific placement/pad invariants).

## Allowed

| File | What | Consumed by |
|---|---|---|
| `floorplan.yaml` | placement config: outline, mounting holes, `fiducials {footprint, refdes_prefix, at[]}` (>=3 non-collinear; board-only, BOM- and CPL-excluded — a fiducial has no net, no BOM line and no placement row, so it is a BOARD FEATURE, not a part), named regions, anchors, `repeat:` banks, keepouts (incl. `deny: []` PERMISSIVE DRU anchors — the thing `rules/nets.yaml` `scoped_floors` scopes a width relaxation to), zones, silk, orientation asserts | SHARED `generate_board_generic.py` |
| `route.yaml` | routing + stitch config: KRT prep/route/import order, pours, thermal vias, pad-rescue, `taps:` (collision-checked named connections KRT cannot thread), and the stitch pass list — `dedupe_vias / normalize_vias / drop_micro_fragments / drop_dangling / split_t_junctions / reload / hole_to_hole / pad_rescue / stub_fallback / astar_fallback / stitch_grid / power_stitch / via_janitor / fill / island_rescue / heal_islands / prune_stitch_dangling / gate` (order is per-board config; `heal_islands` after the last `fill` auto-bridges same-net pour splits — the "Zone [X] <-> Zone [X]" DRC class) | SHARED `route_and_stitch_generic.py` (`prep`/`route`/`import`/`taps`/`stitch`) |
| `rules/` | `nets.yaml` (netclasses + ampacity), `electrical_invariants.yaml` (E-INV intent assertions), `power_tree.yaml` (E-TOPO per-rail voltage envelopes), `policy_waivers.yaml`, `twin_adjudications.yaml` — see `rules/contracts.md` | SHARED `generate_rules_generic.py`, policy_audit, jlc_twin |
| `route/**` | the PROMOTED KRT chain (`*.kicad_pcb`) — a committed ARTIFACT, not code (canon M3); `import` replays it deterministically | SHARED `route_and_stitch_generic.py import` |
| `audit_board.py` | the ONLY per-board emitter: the placement/pad invariant gate (polarity, proximity, plane-clean, refdes-on-silk, and any BOARD-SPECIFIC guard e.g. an analog-keepout distance). Everything else is config or shared. | — |
| `bom_seed.py` | maps BOM comments → `02_parts/` MPN → LCSC; fails on unmapped/TBD lines | required before ordering |
| `rebuild_all.sh` | THE entry point: thin driver that calls the SHARED generics in canonical order, `set -euo pipefail` | REQUIRED |
| `export_pdfs.sh` | release PDF set (pcb_layers, assembly) + PNG verification renders | |
| `lib/` | project-local footprints tscircuit/KiCad can't yet express — see `lib/contracts.md` | |
| `*.py` | **STOPGAP ONLY (canon M8)**: any script beyond `audit_board.py`/`bom_seed.py` is a declared backend gap — its docstring MUST name the gap and the config schema that would replace it. The SECOND board needing the same script triggers mandatory promotion into the shared backend | `rebuild_all.sh` |
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
| 5 | `$S/generate_rules_generic.py .` — netclasses BEFORE route-prep (canon R1) | any python3 |
| 6 | `$S/route_and_stitch_generic.py prep 03_src/route.yaml` (netclass-carrying, track-free route input) | `/usr/bin/python3` |
| 7 | `$S/route_and_stitch_generic.py import 03_src/route.yaml` (replay the promoted `route/` chain — canon M3) | `/usr/bin/python3` |
| 7b | `$S/route_and_stitch_generic.py taps 03_src/route.yaml` — only if `taps:` configured (no-op otherwise); pour-fed sense pins / boxed-in pads, before the pours fill | `/usr/bin/python3` |
| 7c | `$S/route_and_stitch_generic.py quick 03_src/route.yaml` — the LOOP tool, not a gate: seconds-fast ratsnest-unconnected + copper clearance/track_width verdict on the post-import pre-stitch board (JSON to `06_build/route/quick.json`). Iterate routing against THIS, not against step 10 (~seconds vs ~8-10 min/cycle measured on a 112-part board) | `/usr/bin/python3` |
| 8 | `$S/route_and_stitch_generic.py stitch 03_src/route.yaml` (pours + thermal vias); verdict must be `gate: clean` | `/usr/bin/python3` |
| 9 | `$S/generate_rules_generic.py .` — ALWAYS LAST (pcbnew saves clobber `.kicad_pro` netclasses) | any python3 |
| 10 | DRC gate `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity` = 0/0/0 | `kicad-cli` |
| 10b | `$S/grind_driver.py .` — the BOUNDED mechanical grind loop when step 10 is dirty: classifies findings, auto-applies only the conservatively-safe generator reruns per `references/grind_fixes.yaml`, escalates real work into `06_build/grind_escalation.md` (exit 2/3/4 — table/novel/D-BACK), journals each cycle (M9). It cannot loop forever; a nonzero exit summons the designer ONCE with counts + samples | `/usr/bin/python3` |

**External prerequisites** (nothing else):
- KiCad ≥ 10 (`kicad-cli`, `/usr/bin/python3` with `pcbnew` importable)
- the `skills/kicad-pcb/scripts` toolkit (the shared generics) + bun/`tsci`
- KiCadRoutingTools ONLY to re-route from scratch; the committed `route/` chain
  already contains the routing, so the standard rebuild replays it via `import`

## Forbidden

- **A per-board `generate_board.py` / `route_prep.py` / `route_waves.sh` /
  `stitch_and_fill.py` / `generate_rules.py`.** These are the RETIRED bespoke
  generators; the shared generics replace them (`generate_rules_generic.py` is
  the shared rules emitter — do not hand-copy it back in). If the generic backend genuinely cannot express
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
6. `.kicad_dru`/`.kicad_pro` netclasses match what `generate_rules_generic.py`
   emits from `rules/nets.yaml` (regenerate and diff — drift means a hand-edited
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
inspects it), **E-INV/E-ADR** (the netlist graded against the intent assertions
in `rules/electrical_invariants.yaml`; every protection/topology ADR must emit
>= 1), **E-TOPO** (converter topology DERIVED from `rules/power_tree.yaml`
voltage envelopes and asserted against the converter `part.yaml` `type:`),
**M3** (everything regenerable: the promoted route chain lives in
`03_src/route/` and is committed; `06_build` stays disposable), **M4**
(waivers/adjudications in `rules/` each carry measurement evidence).

- Audit: `policy_audit.py <project>` runs S-ERC, S-NC, S-NET, R-RULES, M-REPRO,
  M-WAIV directly, plus E-INV, E-ADR, E-TOPO via the intent checkers
  `electrical_invariants.py` / `power_topology.py` it drives. Zero FAIL required
  at release.
- Waivers live in `rules/policy_waivers.yaml`:
  `{id: <CHECK-ID>, refs: [...], derived_from: <project?>, why: "<measurement
  evidence>"}` — an entry without evidence is itself a FAIL, and an inherited
  rationale without `derived_from` is a `waiver_provenance` FAIL (W-COPY/W-FOREIGN).
