# journal — stage 5 (footprints + placement)

## 2026-07-28 12:05 — start
- did: intake for STAGE 5. Read CLAUDE.md, skills/pcb-design/SKILL.md (4-6 + D-ADJ +
  archetypes + LAYOUT PRECEDENT SEARCH), skills/kicad-pcb/references/{floorplan-archetypes.md,
  layout-precedents.md,fab_tiers.yaml}, 01_docs/{BRIEF,ARCHITECTURE,DETAIL_DESIGN}.md,
  16 ADRs, STATUS.md, journal tails, 02_parts/, 03_src/, every contracts.md, and
  `git show a1d12eb` (stage 4).
- result: the footprint denominator is MEASURED off the committed 04_kicad/pluto_cal_switch.kicad_sch,
  not assumed: 73 components carry 21 distinct FPIDs — 17 in `pluto_cal_switch:` (NONE of which
  exist; 03_src/lib/pluto_cal_switch.pretty/ does not exist at all) and 4 stock KiCad
  (Capacitor_SMD:C_0402_1005Metric x22, Resistor_SMD:R_0402_1005Metric x10,
  Capacitor_SMD:C_0805_2012Metric x3, Fuse:Fuse_1812_4532Metric x1). The 64
  footprint_link_issues in the ERC warnings resolve to those 17 project FPIDs.
- next: grade each of the 17 against its datasheet land drawing and decide
  ADOPT-STOCK vs AUTHOR per footprint, then floorplan.

## 2026-07-29 — WIP CHECKPOINT (new session; the previous one was killed mid-flight)
- did: the 2026-07-28 stage-5 session was terminated by an API spend limit after its
  `start` entry and before any `iterate`. It left ~20 uncommitted files. INSPECTED
  them all before touching anything, and the verdict is KEEP AND COMMIT AS-IS:
  * `03_src/lib/pluto_cal_switch.pretty/` — SEVEN authored land patterns, each
    carrying its derivation in its own `descr` (vendor sheet, figure number, and
    the number the geometry answers). Non-empty, self-documenting, and the
    denominator matches: 7 project FPIDs are named by the netlist and 7 files exist.
  * 11 of 12 STOCK adoptions carry a `FOOTPRINT ADOPTED ... AND HERE IS THE
    COMPARISON` gotcha in their own part.yaml, with the vendor drawing number and
    the per-dimension land-vs-outline delta. The 12th (MINISMDC050F-2,
    Fuse:Fuse_1812_4532Metric) has NO comparison — that is this session's debt,
    recorded here rather than discovered later.
  * `03_src/floorplan.yaml` — full placement: 73 anchors, `require_anchor: true`,
    no seeds and no region placement at all, 4 zones, 14 silk captions, 26 pad_net
    asserts + 1 pad_order. Identity is THIS board (`project.name: pluto_cal_switch`).
  * `04_kicad/` output — COMMITTED, not discarded, and here is why the "regenerable,
    so misleading" argument does not apply: the artifact is COMPLETE, not half
    written. 77 footprints (73 refdes + 4 mounting holes), 15 zones, ZERO track
    segments — which is exactly the shape a pre-routing stage-5 board should have.
    04_kicad/contracts.md says generated output is "committed anyway, because a diff
    on a generated .kicad_pcb is how a generator bug becomes visible"; withholding it
    would delete that diff for no gain.
- result: nothing from the killed session is discarded and nothing is re-derived.
  The spend already paid is banked as the baseline my own gates will be measured
  against.
- next: re-run the gate chain from step [3] to find out what is actually true about
  this placement, since NO gate output from the killed session survives.
