# ADR-0001 (repo) — tscircuit authoring boundary: TSX authors, KiCad verifies

Status: **accepted** 2026-07-19
Scope: cross-project / pipeline. Governs where tscircuit is allowed to sit in the
board pipeline. Binds the pcb-design + kicad-pcb skills.

## Decision

We migrate the **authoring boundary** to tscircuit (TSX), NOT the toolchain. TSX
becomes the front-end for **circuit authoring + schematic capture**. Everything
downstream stays KiCad-side and remains the verification backbone and fab-of-record.

- **Moves to TSX:** circuit declaration + schematic capture. tscircuit exports
  native `.kicad_sch`; the board flows into the existing pipeline through that export.
- **Stays KiCad (the "not switching" list — load-bearing gates):** ERC,
  netlist-parity, rules/ampacity (R1/R2), placement audit (P2/P3/P4/keepouts/
  isolation), KRT routing + pours/thermal (R-*), `jlc_twin`, fresh-context pin +
  render review, `policy_audit`, and the immutable release model (M5).

This is canon **S-DSL** made concrete: declarations compile to native KiCad
artifacts; every gate runs on artifacts, never on the DSL's claims.

## Why not the full switch

A literal 100%-tscircuit pipeline was rejected on evidence, not taste:

- **Routing:** the cook-loadcell reference render (2026-07-19) routed thin default
  geometry (0.15mm tracks, 0.30mm vias), no pours, no thermal vias, and produced
  ~14 real shorts in one congested corner. tscircuit has **no ampacity/netclass
  concept** — the exact class of defect R1/R2 + KRT exist to prevent. Our hardest
  boards (ble-bus-bar 60A, crow-array-central TQ128 6-layer) live precisely here.
- **Digital twin:** `jlc_twin` caught **four wrong-footprint boards this campaign**
  (wide-SOIC W25Q64 flash, U7 pitch, plus loadcell package coding). Its value is
  checker-independence (M1) — comparing our board against JLC's own CAD. A tool
  that authors AND routes AND self-DRCs against its own footprints collapses that
  independence.
- **Policy audit / release:** machine checks (S-OCCL, P-CRT, R-THERM…) and the
  sha256/provenance release model are KiCad-artifact + repo-process shaped.

## What tscircuit genuinely wins (why we adopt it at all)

Schematic authoring + layout. TSX typed components + registry beat raw schwriter2
declarations, and — proven on the reference — export to a **wired** `.kicad_sch`
with **node-for-node netlist parity** (29/29 components, 16/16 nets; only two
leading-digit power-rail renames). A wired TSX front-end also retires the
fleet-wide **S6 label-blob** finding that all 8 project audits flagged.

## Rollout (evidence-gated, reversible, additive)

- **Phase 1 — prove the bridge on a difficulty ladder.** cook-loadcell (simple,
  DONE, parity achieved) + a connector-heavy board (footprinter-gap stress) + a
  large/active board (scale + IC stress). Gate each: TSX → kicad_sch → **ERC 0 AND
  netlist parity 0 vs the sealed board**.
- **Phase 2 — productionize the handoff.** `tsc_schematic_gate` (TSX → kicad_sch →
  ERC → parity report) + a TSX authoring guide (see
  `skills/kicad-pcb/references/tscircuit-folder.md` authoring notes).
- **Phase 3 — flip authoring for NEW boards only.** New commissions author the
  schematic in TSX feeding the unchanged generate_board→rules→KRT→verify chain.
  **Shipped boards are immutable — never re-migrated**; back-port only when a board
  is already being revised.
- **Phase 4 — retire schwriter2 as the default** after N≥3 new boards ship clean
  through the TSX schematic path with zero parity regressions; keep schwriter2 as
  the fallback for footprints tscircuit can't express.

## Reversibility

Additive until Phase 4: every board keeps its KiCad generators; the `tscircuit/`
folder stays a study until a board proves out. If a difficulty class fails Phase 1
(e.g. specialty connectors), those parts stay KiCad-native and the boundary is
recorded here.
