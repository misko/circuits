# Operator checkpoints and canonical pause state

Ask the user only where human intent or physical evidence is authority:

1. connector edge/cable direction/mating side before routing;
2. operational labels, bench access and service clearance before release;
3. installed parts, exposed pads, rail resistance and current limit before
   first power.

Router parameters and search micro-decisions remain machine-owned. When they
cannot close, stop with a semantic diagnosis and owning backtrack stage.

For any pause, `01_docs/pause_state.json` is the sole current-state authority.
`01_docs/STATUS.md` and root `RESUME.md` are generated views carrying the same
state id:

```text
checkpoint + receipts + blocker + next command
                    |
                    v
       01_docs/pause_state.json
             /              \
    STATUS.md              RESUME.md
```

```bash
python3 skills/pcb-design/scripts/pause_state.py record PROJECT \
  --phase routing --checkpoint 03_src/route/critical_prefix.kicad_pcb \
  --receipt 06_build/route/candidate_grades/wave/receipt.json \
  --blocker "I2C corridor repair" \
  --next-command "python3 ... route 03_src/route.yaml --resume"

python3 skills/pcb-design/scripts/pause_state.py verify PROJECT
```

A missing/changed checkpoint, stale view, or contradictory state id fails.
Because all references are project-relative and hash-bound, a clean clone can
resume without chat history or `/tmp` artifacts.
