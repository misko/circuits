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
| `rules/` | see `rules/contracts.md` |
| `lib/` | see `lib/contracts.md` |
| `contracts.md` | this file |

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

## Validate

- every script runs against the current board without error
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
