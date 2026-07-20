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

## Phase 1 findings (2026-07-19) — the ladder ran; the boundary is now precise

Three boards spanning the difficulty spectrum, each authored node-for-node in TSX
from the sealed KiCad netlist:

| Board | Parts | tscircuit MODEL parity (circuit.json vs KiCad) |
|---|---|---|
| cook-loadcell | 33 | **YES** — 29/29 comp, 16/16 nets (2 leading-digit renames) |
| xt60-usb-supply-rerun (connector-heavy) | 51 | **YES** — 51/51 comp, 28/28 nets, 151/151 nodes (11 hand `<footprint>` children; all specialty connectors expressible) |
| esp32-laser-timing (large/active) | 76 | **YES** — 72/72 comp, 36/36 nets; ESP32-S3 (41-pad) + LM339 pin maps exact |

**Authoring is proven across the spectrum** — tscircuit models our boards faithfully,
including specialty connectors (via `<footprint>` children carrying KiCad pad names
as `portHints`) and many-pin modules/actives.

**But the native `kicad_sch` EXPORT — the actual bridge our pipeline needs — has two
exporter-maturity gaps found this round (NOT authoring/design gaps):**

1. **Symbol-id collision (root-caused, esp32):** the exporter derives a chip's
   schematic symbol id as `Device:U_chip_<footprintName>`. A hand-authored
   `<footprint>` has no name, so every custom-footprint chip collapses to bare
   `Device:U_chip`; **two** such many-pin chips (module U1 + USB-C J1) then share one
   symbol and each **truncates to 2 pins**. Empirical rule: **≤1 many-pin
   hand-authored-footprint chip survives the native export per board.** Dense nets
   also fragment (`Net-(C4-Pad2)`).
2. **No symbol annotation:** the exported `.kicad_sch` is not annotated, so
   `kicad-cli sch export netlist` builds 0 nets from it without an annotation pass
   (confirmed uniformly across all three boards). ERC on the export is dominated by
   parametric artifacts (off-grid wires, generated-symbol issues), not design signal.

**Consequence for the boundary:** commodity-footprint boards clear the native export;
boards needing ≥2 many-pin custom footprints (module + USB-C, multi-connector) author
faithfully but do NOT yet survive tscircuit's native `kicad_sch` export intact. The
bridge mechanism — not the authoring — is the work item. Options (Phase 2 decision):
(a) post-process the exported `.kicad_sch` (annotate + de-collide `U_chip` symbol ids);
(b) route `circuit.json → our own kicad_sch converter` (control naming/annotation);
(c) fix/contribute upstream in tscircuit's KiCad exporter; (d) constrain the boundary
to commodity-footprint boards, keeping custom-footprint-heavy boards on schwriter2.
Until one is chosen and proven, KiCad `04_kicad/` stays the sole fab-of-record and the
`tscircuit/` folders remain design studies.

## Reversibility

Additive until Phase 4: every board keeps its KiCad generators; the `tscircuit/`
folder stays a study until a board proves out. If a difficulty class fails Phase 1
(e.g. specialty connectors), those parts stay KiCad-native and the boundary is
recorded here.
