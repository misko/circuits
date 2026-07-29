# contract: 03_src/lib/

**Purpose** — footprints this project OWNS, vendored so a clone opens on a
machine that never saw the shared libraries. cooksense owns **FIVE** (this line
said "exactly TWO" until 2026-07-28 and had been wrong since the KF350 and ZIF
lands were vendored — a contract that miscounts its own directory is a
governance defect, so it is corrected here rather than left):

- `cooksense.pretty/Relay_StandexDIP_1A_pinout13.kicad_mod` — the Standex
  DIP05-1A72-**13L** reed relay (**PIN-OUT CODE 13**), pads **RENUMBERED from
  the physical DIP-14 lead positions 2,6,8,14 -> 1,2,3,4** to match the
  tscircuit `dip4` authoring (the netlist emits `K_*.1/.2/.3/.4`; the PAD-NAME
  NOTE in `cooksense.tsx` documents this board-stage remap, and
  `03_tscircuit/parity_padmap.txt` records it as canon TSX-PRE evidence).
  Pad 1/2 = COIL (DIP leads 2/6, WEST column), 3/4 = CONTACT (DIP leads 8/14,
  EAST column); the 1.5 kVDC isolation boundary runs between the columns at
  7.62 mm (ADR-0002) — and under code 13 that statement is TRUE.
  **REPLACES `Relay_StandexDIP_1A_pinout12.kicad_mod`, DELETED 2026-07-28.**
  Under code 12 the part has eight leads with 1<->14 and 7<->8 tied as two
  CONTACT nodes and the coil on the inner pins; on the 4-pad land that shorted
  `5V_KEY_RELAY` to `U_SEL_BUS` and every ULN2803 output to its keypad line,
  and gave the coil no holes. Do not resurrect it.
- `cooksense.pretty/Omega_PCC-SMP-K_TypeK_PCpin.kicad_mod` — the Omega
  miniature Type-K thermocouple PC-mount jack (no KiCad stock footprint).
  Pad 1 = TCP(+), pad 2 = TCN(-). Mechanical is a placeholder pending the
  PCC-OST-SMP spec measurement (Gate-1); pad count + nets are final.
- `cooksense.pretty/JST_10FDZ-BT_1x10_P2.54mm_Vertical_ZIF.kicad_mod` — the
  10-way 2.54 mm vertical ZIF land (see `01_docs/10fdz-bt-land-pattern-confirm.md`).
- `cooksense.pretty/TerminalBlock_KF350_2P.kicad_mod` and
  `cooksense.pretty/TerminalBlock_KF350_4P.kicad_mod` — the 3.5 mm screw
  terminals; no stock KiCad land matches the KF350 body.

**Mutability** — hand-edited, rarely.

## Allowed

| Pattern | What |
|---|---|
| `<name>.pretty/` | KiCad footprint library owned by this project |
| `*.kicad_mod` | inside a `.pretty/` only |
| `contracts.md` | this file |

## Rules

- Reference these with `${KIPRJMOD}` in `fp-lib-table`, never an absolute path.
- Vendor a footprint here ONLY if you author or modify it. All five qualify:
  the relay is AUTHORED here against DS p.3 sub-figure 13 and RENUMBERED from
  DIP leads 2,6,8,14 to 1,2,3,4 (an unmodified DIP-14 copy would keep the
  physical lead numbers and hard-fail `check_pads_present` against the
  tscircuit netlist), and the TC jack, the ZIF and the two KF350 terminals have
  no stock equivalent.
- A footprint's pad numbering / pin-1 marker is a FACT other tooling depends
  on. Both are recorded in the matching `02_parts/<MPN>/part.yaml` (`pins:` +
  the RENUMBER note); generators trust that file over the footprint.

## Validate

- `fp-lib-table` uses `${KIPRJMOD}`, no absolute paths.
- every footprint referenced by `04_kicad/cooksense.kicad_pcb` resolves from
  `03_src/lib/` or a stock KiCad library — no dangling refs.
- the relay footprint carries pads `1 2 3 4` (not the physical DIP leads) — the
  tscircuit `dip4` contract; `check_pads_present` in generate_board_generic.py
  is the machine backstop (it dies on any netlist pad with no board pad).
- the relay footprint's four pad COORDINATES encode pin-out code 13: pads 1/2
  on the WEST column (x = -3.810) and pads 3/4 on the EAST (x = +3.810). A
  land with a pad on both sides of the coil/contact split is code 12 and is the
  DO-NOT-ORDER defect of v1.0-v1.6 — see the `descr` string, which carries the
  DIP-lead map so the file is self-describing to a reader with the datasheet.

## Repair

- Absolute path in `fp-lib-table` → rewrite with `${KIPRJMOD}`.
- Dangling footprint ref → restore the library or repoint the footprint.
- Relay pads back to 1,7,8,14 → re-run the renumber; the netlist is 1..4.
