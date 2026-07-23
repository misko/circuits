# Regenerate crow-mic-pod-v2

```
export PATH="$HOME/.bun/bin:$PATH"
# schematic bridge (ERC 0 + parity + FPID resolution):
python3 ../../skills/kicad-pcb/scripts/tsx_preflight.py projects/crow-mic-pod-v2      # BEFORE first build
bash    ../../skills/kicad-pcb/scripts/gen_tscircuit.sh projects/crow-mic-pod-v2
python3 ../../skills/kicad-pcb/scripts/count_parity.py projects/crow-mic-pod-v2       # refdes SET parity

# board (placement + rules + route + stitch -> DRC 0/0/0) is driven by the
# generic backend from 03_src/floorplan.yaml + 03_src/route.yaml (see
# 03_src/rebuild_all.sh), NOT tsx_to_board.sh (this board has no hand-written
# 03_src/generate_board.py — it uses generate_board_generic.py).
```

Source of truth: `src/crow_mic_pod_v2.tsx`. Never hand-edit `build/`,
`kicad/`, `verification/`, `fab/` — fix the TSX and regenerate.
