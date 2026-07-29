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
