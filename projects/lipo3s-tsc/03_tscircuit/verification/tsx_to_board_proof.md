# tsx_to_board.sh — end-to-end proof (lipo3s-tsc, the 100-part capstone)

ADR-0002 Phase E. The ONE-COMMAND tscircuit-native rebuild driven through the
UNCHANGED usb-power-3s KiCad backend, from TSX to a DRC-clean board. The board's
internal name is `usb_power_3s` (so the promoted route r5 + rules + FPIDs transfer
byte-for-byte); the TSX source is `lipo3s_tsc.tsx`.

```
export PATH="$HOME/.bun/bin:$PATH"
bash <kicad-pcb skill>/scripts/tsx_to_board.sh projects/lipo3s-tsc
```

Sealed parity reference (via `03_tscircuit/sealed_ref.txt`):
`../usb-power-3s/04_kicad/usb_power_3s.kicad_pcb`. Reparents into an isolated build
root (`03_tscircuit/tsx_build/`, gitignored) — sealed `04_kicad/` + releases untouched.

## Result (2026-07-20)

| gate | result |
|---|---|
| tsci build -> circuit.json | ok |
| converter -> kicad_sch | 96 components (96 FPID), 303 pins, 365 wires, MODE=layout WIRED; 75 FPID overrides from 02_parts |
| ERC `--severity-all` | **0 errors** (608 warnings, parametric baselined) |
| placement (generate_board.py) | 96 footprints + 4 holes (100 parts); audit PASS (0 fails, 0 warns) |
| KRT route (promoted chain r5) | imported 773 segments, 104 vias |
| route_taps.py | all taps routed (120 vias) |
| stitch_and_fill | via janitor -4, island stitch 12 vias, filled |
| audit (post-route) | PASS (0 fails, 0 warns) |
| generate_rules LAST | Default/SWITCH_NODE/PWR_RAIL/VBUS, 11 patterns, dru floors |
| **DRC `--severity-all --refill-zones --schematic-parity`** | **0 violations / 0 unconnected / 0 parity** |
| **board_netlist_parity vs sealed `usb-power-3s/04_kicad/usb_power_3s.kicad_pcb`** | **PASS — 303 nodes / 56 nets, net-for-net identical** |

DRC **0/0/0** + board parity **0** on the 100-part capstone. Reproduces the sealed
usb-power-3s board electrically from the TSX source, backend byte-for-byte unchanged.
