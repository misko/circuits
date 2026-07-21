# pcb-design templates — the skill's project-independent seed set

The `/pcb-design` skill is **completely independent of any project**. Everything
a new board needs to START is here, in the skill — nothing is copied out of
`projects/`. That coupling is what let a clean-room agent read a sibling board's
design source on 2026-07-20; the fix is that the skill carries its own canon.

## Contents

- `contracts/ROOT.contracts.md` → a new project's root `contracts.md`
- `contracts/<stage>/contracts.md` → each stage folder's binding contract
  (`01_docs 02_parts 03_src 03_tscircuit 04_kicad 05_firmware 06_build 07_releases`)
- `03_src/{floorplan.yaml,route.yaml,rules/nets.yaml}` → annotated SCHEMA
  EXAMPLES for the generic backend's config. The **keys are the contract**; the
  values are placeholders adopted from a proven board — replace them.

## Commission a new board (what the SKILL does)

```
for s in 01_docs 02_parts 03_src 03_tscircuit 04_kicad 05_firmware 06_build 07_releases; do
  cp <skill>/templates/contracts/$s/contracts.md  projects/<name>/$s/contracts.md
done
cp <skill>/templates/contracts/ROOT.contracts.md  projects/<name>/contracts.md
cp <skill>/templates/03_src/floorplan.yaml         projects/<name>/03_src/floorplan.yaml
cp <skill>/templates/03_src/route.yaml             projects/<name>/03_src/route.yaml
cp <skill>/templates/03_src/rules/nets.yaml        projects/<name>/03_src/rules/nets.yaml
```

Then derive the board: fill `01_docs`, author `03_tscircuit`, and replace the
config values. The heavy generators are SHARED in `skills/kicad-pcb/scripts/`
(`generate_board_generic.py`, `route_and_stitch_generic.py`, the converter) —
a board carries CONFIG, not a backend.

## Keeping these current

When the pipeline changes, update the template here — it is the single source
of truth for what a new board looks like. A drifted template silently ships the
old shape to every future board (this is exactly how the bespoke-era `03_src`
contract survived into new boards long after the generic backend replaced it).
