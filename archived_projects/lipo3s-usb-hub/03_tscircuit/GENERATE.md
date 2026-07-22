# Generate (one command)

```
export PATH="$HOME/.bun/bin:$PATH"     # tsci runs on bun
bash ~/.claude/skills/kicad-pcb/scripts/tsx_to_board.sh ~/gits/circuits/projects/lipo3s-usb-hub
```

Flow (every gate printed; ends at DRC 0/0/0 + board parity 0):
tsci build → circuit_json_to_kicad_sch → sch export netlist → ERC 0 →
generate_board.py (hand floorplan) → audit PASS → generate_rules → import promoted
KRT route r5 → route_taps → stitch_and_fill → generate_rules LAST →
DRC --severity-all --refill-zones --schematic-parity → board_netlist_parity vs sealed.

Output board: `03_tscircuit/tsx_build/04_kicad/lipo3s_usb_hub.kicad_pcb` (throwaway build
root). Promoted to `04_kicad/` as the fab-of-record for the release.

Schematic-only render (human PDF): `gen_tscircuit.sh <project>` → `build/schematic.pdf`.
