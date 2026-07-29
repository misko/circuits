# placement journal — pluto-rx2-8way stage 5 (footprints + placement)
#
# CLOCK NOTE, so the timestamps read sanely: stage 4's entries are stamped
# 19:05/19:10 but the system clock at handoff read 17:43 PDT the same day. This
# journal uses the SYSTEM clock (`date`), so the first entry below appears to
# precede the previous stage's finish. It does not; the earlier stamps ran fast.

## 2026-07-28 17:50 — start
- did: took stage 5 (footprints + placement) with the mandate to STOP BEFORE
  ROUTING. Read the canon (repo CLAUDE.md, SKILL.md 4-6 incl. D-ADJ /
  archetypes / LAYOUT PRECEDENT SEARCH, floorplan-archetypes.md,
  layout-precedents.md, fab_tiers.yaml, design-policies.md), this board's
  BRIEF/ARCHITECTURE/DETAIL_DESIGN/CHECKLIST, all eight ADRs, the four journals,
  02_parts/README.md, 03_src/ and every contracts.md, and `git show 0228e7b`.
- result: state confirmed as handed over — `policy_audit` FAIL=0 HUMAN=6 N-A=26
  PASS=8, netlist present (64 components / 74 nets), 04_kicad EMPTY except its
  contracts.md, no `03_src/placement_gates.json` yet. THE FLOORPLAN IS ALREADY
  DERIVED (ADR-0007) and this stage ADAPTS it rather than re-deriving it.
  TEMPLATE-LEFTOVER RE-CHECK (the stage-4 finding): `route.yaml` names
  `pluto_rx2_8way` throughout, `rebuild_all.sh` carries BOARD=TSX=pluto_rx2_8way,
  `rebuild_reuse.sh` derives BOARD from floorplan.yaml, `floorplan.yaml`
  `project.name: pluto_rx2_8way`. Nothing template-shaped survives in 03_src.
- next: (1) INDEPENDENTLY re-verify every standard-KiCad footprint against its
  committed vendor land drawing — the claims are in the part.yaml comments and a
  claim is not a measurement (canon M1); (2) generate the board from
  floorplan.yaml on the generic backend; (3) P-OUT/P-CAP BEFORE any routing.
