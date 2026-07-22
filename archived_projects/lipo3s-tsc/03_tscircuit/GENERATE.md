# Generate

```
export PATH="$HOME/.bun/bin:$PATH"     # tsci runs on bun

# 1. render + convert (GATE 1: ERC 0 + netlist parity 0 vs sealed schematic)
bash ~/.claude/skills/kicad-pcb/scripts/gen_tscircuit.sh ~/gits/circuits/projects/lipo3s-tsc
#    (or, minimal:)
cd tscircuit && tsci build src/lipo3s_tsc.tsx
python3 ~/.claude/skills/kicad-pcb/scripts/circuit_json_to_kicad_sch.py \
    dist/src/lipo3s_tsc/circuit.json -o kicad/lipo3s_tsc.kicad_sch --project lipo3s_tsc

# 2. full KiCad backend (GATE 2: DRC 0/0/0 + board parity 0 vs sealed board)
bash 03_tscircuit/build_backend.sh
```
