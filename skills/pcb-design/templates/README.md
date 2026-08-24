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
- `03_src/rules/mates.yaml` → the CONDITIONAL schema example (canon D-MATE):
  seeded only when the board mates to hardware this repo did not design. It is
  the machine copy of the BRIEF's `## Mating fact-lock`, and it holds fact IDs,
  never values — the facts live once in `spf/<device>/`.
- `01_docs/{BRIEF,ARCHITECTURE,CHANGELOG,CHECKLIST}.md` +
  `01_docs/decisions/0000-example-adr.md` → starter skeletons for the design
  docs (fill, never leave placeholder text in a committed project).
- `project.gitignore` → the new project's `.gitignore` (ignores `06_build/`
  per the root contract).
- `ORCHESTRATION_STATE.md` → the multi-board COORDINATOR's state-journal
  skeleton — copied to the orchestration root per CAMPAIGN, not per project
  (it is not part of the commission copy list below).
- Sub-stage contracts nest under `contracts/` exactly as they land in the
  project (`contracts/01_docs/decisions/`,
  `contracts/03_src/{lib,mechanical,rules}/`). The mechanical contract is
  seeded only when commission explicitly selects enclosure work alongside the
  capability profile.

## Commission a new board (what the SKILL does)

```
for s in 01_docs 02_parts 03_src 03_tscircuit 04_kicad 05_firmware 06_build 07_releases 08_reviews; do
  cp <skill>/templates/contracts/$s/contracts.md  projects/<name>/$s/contracts.md
done
cp <skill>/templates/contracts/ROOT.contracts.md  projects/<name>/contracts.md
cp <skill>/templates/03_src/floorplan.yaml         projects/<name>/03_src/floorplan.yaml
cp <skill>/templates/03_src/route.yaml             projects/<name>/03_src/route.yaml
cp <skill>/templates/03_src/rebuild_all.sh         projects/<name>/03_src/rebuild_all.sh
cp <skill>/templates/03_src/rules/nets.yaml        projects/<name>/03_src/rules/nets.yaml
cp <skill>/templates/03_src/rules/power_tree.yaml  projects/<name>/03_src/rules/power_tree.yaml
cp <skill>/templates/03_src/rules/electrical_invariants.yaml projects/<name>/03_src/rules/electrical_invariants.yaml
cp <skill>/templates/03_src/rules/first_article.yaml projects/<name>/03_src/rules/first_article.yaml
# (rebuild driver + BOTH rules schemas seed at commission — stages 1-3 mandate
#  authoring power_tree + electrical_invariants; omitting them from this list
#  made boards discover the schemas mid-pipeline. Fixed 2026-07-23.)
# CONDITIONAL — only if the board mates to hardware this repo did not design
# (canon D-MATE); a board that mates to nothing must NOT carry an empty one,
# which import_provenance_check.py fails as M-COVER:
cp <skill>/templates/03_src/rules/mates.yaml       projects/<name>/03_src/rules/mates.yaml
cp <skill>/templates/01_docs/*.md                  projects/<name>/01_docs/
cp <skill>/templates/01_docs/decisions/0000-example-adr.md projects/<name>/01_docs/decisions/
cp <skill>/templates/project.gitignore             projects/<name>/.gitignore
# nested sub-stage contracts land at the same relative paths:
cp <skill>/templates/contracts/01_docs/decisions/contracts.md projects/<name>/01_docs/decisions/
cp <skill>/templates/contracts/01_docs/journal/contracts.md   projects/<name>/01_docs/journal/
cp <skill>/templates/contracts/01_docs/learnings/contracts.md projects/<name>/01_docs/learnings/
cp <skill>/templates/contracts/03_src/lib/contracts.md        projects/<name>/03_src/lib/
cp <skill>/templates/contracts/03_src/rules/contracts.md      projects/<name>/03_src/rules/
# CONDITIONAL — only when commission's enclosure scope explicitly selects
# `co_design` or `derived`:
mkdir -p projects/<name>/03_src/mechanical
cp <skill>/templates/contracts/03_src/mechanical/contracts.md projects/<name>/03_src/mechanical/
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
