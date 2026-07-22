# Generate this folder

```
export PATH="$HOME/.bun/bin:$PATH"
bash ~/.claude/skills/kicad-pcb/scripts/gen_tscircuit.sh ~/gits/circuits/projects/crow-mic-pod
```

Writes build/ fab/ kicad/ verification/ (read-only w.r.t. 04_kicad + releases).
Source of truth for the netlist: `../04_kicad/crow_mic_pod.kicad_pcb`.
