# Generate — crow-recorder-central-v2

```
export PATH="$HOME/.bun/bin:$PATH"

# 0. preflight (BEFORE the first build) — alphanumeric USB-C pads must be mapped
python3 ~/.claude/skills/kicad-pcb/scripts/tsx_preflight.py projects/crow-recorder-central-v2

# 1. schematic bridge (default): circuit.json + schematic.pdf + converter kicad_sch
#    + ERC (0 errors) + netlist parity
bash ~/.claude/skills/kicad-pcb/scripts/gen_tscircuit.sh projects/crow-recorder-central-v2

# 2. refdes SET parity (manifest vs every generated artifact)
python3 ~/.claude/skills/kicad-pcb/scripts/count_parity.py projects/crow-recorder-central-v2

# 3. whole board (later stages): tsci -> converter -> placement -> rules -> KRT
#    -> stitch -> DRC 0/0/0. Requires 03_src/generate_board.py + a promoted route.
bash ~/.claude/skills/kicad-pcb/scripts/tsx_to_board.sh projects/crow-recorder-central-v2
```

Board internal name: `crow_recorder_central_v2`. Authoring file:
`src/crow_recorder_central_v2.tsx`.
