# tsx_to_board.sh — end-to-end proof (cook-loadcell)

ADR-0002 Phase E. The ONE-COMMAND tscircuit-native rebuild driven through the
UNCHANGED, netlist-driven KiCad backend, from TSX to a DRC-clean board.

```
export PATH="$HOME/.bun/bin:$PATH"
bash <kicad-pcb skill>/scripts/tsx_to_board.sh projects/cook-loadcell
```

Reparents outputs into an isolated build root (`03_tscircuit/tsx_build/`, gitignored,
throwaway) — the sealed `04_kicad/` + releases are never touched.

## Result (2026-07-20)

| gate | result |
|---|---|
| tsci build -> circuit.json | ok |
| converter -> kicad_sch | 29 components (29 FPID), 77 pins, 80 wires, MODE=layout WIRED |
| ERC `--severity-all` | **0 errors** (205 warnings, parametric baselined) |
| placement (generate_board.py) | 29 parts + 4 holes; audit PASS (0 fails) |
| KRT route (promoted chain r2) | imported 221 segments, 29 vias |
| stitch_and_fill | GND rescue 17/17, stitch 14 vias, 2 zones filled |
| audit (post-route) | PASS (0 fails) |
| generate_rules LAST | Default/BRIDGE/PWR, 10 patterns, dru floors |
| **DRC `--severity-all --refill-zones --schematic-parity`** | **0 violations / 0 unconnected / 0 parity** |
| **board_netlist_parity vs sealed `04_kicad/cook_loadcell.kicad_pcb`** | **PASS — 77 nodes / 17 nets, net-for-net identical** |

DRC **0/0/0** + board parity **0**. Reproduces the sealed cook-loadcell board
electrically from the TSX source, backend byte-for-byte unchanged.
