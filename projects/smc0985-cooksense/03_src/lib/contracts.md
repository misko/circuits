# contract: 03_src/lib/

**Purpose** — footprints this project OWNS, vendored so a clone opens on a
machine that never saw the shared libraries. cooksense owns exactly TWO,
both authored at the board (placement) stage:

- `cooksense.pretty/Relay_StandexDIP_1A_pinout12.kicad_mod` — the Standex
  DIP05-1A72 reed relay, geometry from cook-hub but pads **RENUMBERED
  1,7,8,14 -> 1,2,3,4** to match the tscircuit `dip4` authoring (the netlist
  emits `K_*.1/.2/.3/.4`; the schematic PAD-NAME NOTE in `cooksense.tsx`
  documents this board-stage remap). Pad 1/2 = COIL (west), 3/4 = CONTACT
  (east); the 1.5 kVDC isolation boundary runs between the columns (ADR-0002).
- `cooksense.pretty/Omega_PCC-SMP-K_TypeK_PCpin.kicad_mod` — the Omega
  miniature Type-K thermocouple PC-mount jack (no KiCad stock footprint).
  Pad 1 = TCP(+), pad 2 = TCN(-). Mechanical is a placeholder pending the
  PCC-OST-SMP spec measurement (Gate-1); pad count + nets are final.

**Mutability** — hand-edited, rarely.

## Allowed

| Pattern | What |
|---|---|
| `<name>.pretty/` | KiCad footprint library owned by this project |
| `*.kicad_mod` | inside a `.pretty/` only |
| `contracts.md` | this file |

## Rules

- Reference these with `${KIPRJMOD}` in `fp-lib-table`, never an absolute path.
- Vendor a footprint here ONLY if you author or modify it. Both owned
  footprints qualify: the relay is RENUMBERED from cook-hub's (not an
  unmodified copy — a straight copy would keep pads 1,7,8,14 and hard-fail
  `check_pads_present` against the tscircuit netlist), and the TC jack has no
  stock equivalent.
- A footprint's pad numbering / pin-1 marker is a FACT other tooling depends
  on. Both are recorded in the matching `02_parts/<MPN>/part.yaml` (`pins:` +
  the RENUMBER note); generators trust that file over the footprint.

## Validate

- `fp-lib-table` uses `${KIPRJMOD}`, no absolute paths.
- every footprint referenced by `04_kicad/cooksense.kicad_pcb` resolves from
  `03_src/lib/` or a stock KiCad library — no dangling refs.
- the relay footprint carries pads `1 2 3 4` (not `1 7 8 14`) — the tscircuit
  `dip4` contract; `check_pads_present` in generate_board_generic.py is the
  machine backstop (it dies on any netlist pad with no board pad).

## Repair

- Absolute path in `fp-lib-table` → rewrite with `${KIPRJMOD}`.
- Dangling footprint ref → restore the library or repoint the footprint.
- Relay pads back to 1,7,8,14 → re-run the renumber; the netlist is 1..4.
