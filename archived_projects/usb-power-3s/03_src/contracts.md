# contract: 03_src/

**Purpose** — the only hand-written truth about the board's electrical
design. Everything in `04_kicad/` and `06_build/` is derived from here. If `03_src/`
and `04_kicad/` disagree, `03_src/` is right and `04_kicad/` is stale.

**Mutability** — hand-edited.

## Allowed

| File | What |
|---|---|
| `generate_schematic.py` | emits `04_kicad/<board>.kicad_sch` from a component/net table |
| `generate_board.py` | drives the pcbnew API: loads footprints from the netlist, places them from a floorplan |
| `generate_rules.py` | emits netclasses into `.kicad_pro` + width floors into `.kicad_dru` from `rules/nets.yaml` |
| `audit_board.py` | the placement/pad invariant gate (I1–I7) |
| `rebuild_all.sh` | THE entry point: full regenerate→route→stitch→gate chain, `set -euo pipefail` | REQUIRED |
| pipeline scripts (`route_taps*.py`, `stitch_and_fill.py`, …) | project-specific routing/stitching steps | every one must be invoked by `rebuild_all.sh` — a script the chain doesn't run is an experiment (forbidden) |
| `bom_seed.py` | maps BOM comments → `02_parts/` MPN → LCSC; fails on unmapped/TBD lines | required before ordering |
| `export_pdfs.sh` | release PDF set (schematic, layers, assembly) + PNG verification renders | |
| `rules/` | see `rules/contracts.md` |
| `lib/` | see `lib/contracts.md` |
| `contracts.md` | this file |

## The pipeline — what runs, in what order, with which interpreter

`rebuild_all.sh` is the single entry point and the authoritative order. A
fresh agent runs it FIRST; everything below is what it does:

| Step | Script | Interpreter |
|---|---|---|
| 1 | `generate_schematic.py` | `/usr/bin/python3` (KiCad-bundled pcbnew) |
| 2 | netlist export | `kicad-cli sch export netlist` |
| 3 | `generate_board.py` (placement + zones + audit) | `/usr/bin/python3` |
| 4 | routing import + tap routing + stitching | `/usr/bin/python3` |
| 5 | `generate_rules.py` — ALWAYS LAST before DRC (pcbnew saves clobber `.kicad_pro` netclasses) | any python3 |
| 6 | DRC gate | `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity` |

**External prerequisites** (a fresh clone needs these; nothing else):
- KiCad ≥ 10 (`kicad-cli`, `/usr/bin/python3` with `pcbnew` importable)
- the `skills/kicad-pcb/scripts` toolkit — resolved repo-relative first,
  `~/.claude/skills/` fallback (scripts do this themselves)
- KiCadRoutingTools ONLY to re-route from scratch (`06_build/route/` inputs);
  the committed board already contains the routing, so the standard rebuild
  does not need it

## Forbidden

- **One-off experiment scripts.** `manhattan_route.py`, `import_ses.py`,
  `route_board.py` accumulated in one real project until nobody knew which
  was live. If it ran once and will not run again, it belongs in git history,
  not `03_src/`. Rule: every script in `03_src/` must be runnable TODAY against the
  current board and produce the current result.
- Writing to `07_releases/`. Generators may write `04_kicad/` and `06_build/` only.
- Board data hardcoded where it duplicates `02_parts/` or `rules/` — see below.

## The hard rules for generators

1. **A missing footprint is a HARD ERROR, never a warning.** A one-line
   `print("SKIP U9: no footprint"); continue` shipped a board without its USB
   ESD array; every board-internal gate passed because none of them compares
   the board to the schematic. Raise.
2. **A parse that yields zero results is an ERROR.** Netlist format changed
   between KiCad 7 (one-line s-exprs) and 10 (pretty-printed); a same-line
   regex silently matched nothing. Guard every parse with a count assertion.
3. **Never clobber `.kicad_pro` wholesale.** It holds the DRC floors and
   severity policy. Generators merge; they do not rewrite.
4. **Pin numbers are PHYSICAL PADS, from `02_parts/<MPN>/part.yaml`** — not
   from a symbol's logical order, not from memory. Cite the part file.
5. **Polarity is a fact, not a convention to guess.** KiCad footprints put
   the cathode on pad 1; a generic `1`/`2` symbol lets the author wire it
   backwards, and NO electrical check can see it (the netlist is
   self-consistent either way). Three reversed parts shipped this way on one
   board, including the battery connector. Assert pad 1's net against
   `part.yaml`.

## Validate — runnable by a fresh agent with zero context

1. `bash 03_src/rebuild_all.sh` completes and its final two lines are
   `violations: 0 {}` and `unconnected: 0` — this exercises every pipeline
   script and both generators end-to-end
2. after the rebuild, `04_kicad/*.kicad_dru` is byte-identical to the committed
   version (it is fully deterministic). The `.kicad_sch`/`.kicad_pcb` are NOT
   byte-stable (fresh UUIDs, item ordering) — for those the invariant is the
   GATE result, not the bytes; commit the regenerated files
3. every `*.py`/`*.sh` in `03_src/` is either in the table above or invoked
   by `rebuild_all.sh` (`grep <name> 03_src/rebuild_all.sh`)
- no script writes to `07_releases/`
- pin maps in the generator match `02_parts/<MPN>/part.yaml` (no divergence)
- `.kicad_dru` and `.kicad_pro` netclasses match what `generate_rules.py`
  emits from `rules/nets.yaml` (regenerate and diff — drift means someone
  hand-edited a generated file)

## Repair

- Stale experiment script → delete it; git history keeps it.
- Generator with a soft skip → convert to `raise`.
- Hand-edited `.kicad_dru` → port the change into `rules/nets.yaml` and
  regenerate.

## Compliance audit (design-policies.md IDs)

This folder answers: **S1/S4** (ERC gate at severity-all = 0 errors;
no_connect flags EMITTED by generate_schematic for sanctioned floats),
**S2** (no auto-named nets reach copper), **R1** (netclasses exist in the
route-INPUT project file — R-RULES inspects it), **M3** (everything
regenerable: the final route chain file is PROMOTED to 03_src/route/ and
committed; 06_build stays disposable), **M4** (waivers/adjudications in
rules/ each carry measurement evidence).

- Audit: `policy_audit.py <project>` runs S-ERC, S-NC, S-NET, R-RULES,
  M-REPRO, M-WAIV directly. Zero FAIL required at release.
- Waivers live in `rules/policy_waivers.yaml`:
  `{id: <CHECK-ID>, refs: [...], why: "<measurement evidence>"}` — an
  entry without evidence is itself a FAIL.
