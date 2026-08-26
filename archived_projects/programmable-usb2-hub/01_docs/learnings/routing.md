# Routing learnings

## 2026-07-31 — accelerated DRC cleanup

- issue: Five dense local via/track clusters survived the general router and produced clearance and hole-clearance tails.
  - root cause: The exact local escape geometry and legal via sizes/locations were not represented in the declarative route source.
  - avoid next time: Promote reviewed deterministic escapes and layer constraints into `route.yaml` plus the route chain as soon as they prove clean; keep full DRC for batch boundaries.
  - candidate-canon: no — already covered by M3 deterministic-source and exact-collision rules.

- issue: Connectivity-sensitive island healing initially observed a stale pre-fill connectivity model and left one GND split.
  - root cause: Zone fill and connectivity grouping occurred in one pcbnew interpreter without a hard rebuild of the connectivity model.
  - avoid next time: Put `fresh_reload` after the authoritative final fill and before `heal_islands`.
  - candidate-canon: yes — add a route-pipeline check that connectivity-sensitive post-fill passes require a fresh interpreter barrier; suggested check ID R-FRESH-CONN.

- issue: Pad rescue duplicated already-routed seed escapes whose connected via lay outside its local geometric search radius.
  - root cause: Rescue recognized only a near-pad via, not a same-net connected component that already reached a via.
  - avoid next time: Credit a pad when KiCad connectivity shows its same-net component already contains a via, while retaining the geometric via-in-pad fallback.
  - candidate-canon: yes — add a seed/rescue idempotence fixture; suggested check ID R-RESCUE-IDEMP.

- issue: A valid first layout-seal handoff went stale immediately.
  - root cause: `pcb_flow.py` changed while the long seal process was running, so the produced board and handoff did not share one tool identity.
  - avoid next time: Always run `pcb_flow.py validate` after handoff generation and repeat the seal when any source/board/tool/gate hash races.
  - candidate-canon: no — already enforced by the content-addressed handoff contract.
