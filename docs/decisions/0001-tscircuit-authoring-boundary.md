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
`03_tscircuit/` folders remain design studies.

## Phase 2 result (2026-07-19) — OUR converter clears the ceiling: 3/3 ERC + parity

The bridge work item from Phase 1 was resolved by option **(b): our own
`circuit.json → .kicad_sch` converter**, bypassing tscircuit's native `kicad_sch`
exporter entirely. `skills/kicad-pcb/scripts/circuit_json_to_kicad_sch.py` renders
the FULL connectivity model that circuit.json carries (`source_component` /
`source_port` / `source_net` + the `pcb_*` pad geometry) into a native, annotated
sheet:

- **Unique symbol per component.** Each `source_component` gets its own
  `elt:SYM_<refdes>` lib_symbol (a generic N-pin box sized to its ports). Two
  components can never share a symbol, so the `Device:U_chip_<footprint>` collision
  is impossible by construction.
- **Pins keyed to the KiCad pad name.** Each `source_port` becomes a pin numbered
  with the exact KiCad pad name (first non-`unnamed_*` `pcb_*` `port_hint`), so the
  exported netlist nodes match the sealed board verbatim. Internally-connected
  duplicate pads (split shields / thermal pads) collapse to one pin, as KiCad does.
- **Net glue by global label (schwriter2 rule).** One `global_label` per pin carries
  the net name; the netlister joins by label-name = parity. Nets are resolved by
  `subcircuit_connectivity_map_key` with propagation through
  `internally_connected_source_port_ids`. GND pins render as ground power symbols
  with a single `PWR_FLAG` so ERC's power-driven check stays at zero; explicit
  no-connects get `no_connect` flags.
- **Annotated.** Instance `(reference …)` blocks are emitted, so
  `kicad-cli sch export netlist` builds real nets (tscircuit's native export builds 0).

**Gate results — all three Phase-1 boards, converter kicad_sch:**

| Board | ERC (`--severity-all`) | Netlist parity vs sealed 04_kicad |
|---|---|---|
| cook-loadcell | **0 errors** (51 warn, baselined) | **PARITY 0** — 16/16 nets, 75/75 nodes, 2/2 NC |
| xt60-usb-supply-rerun | **0 errors** (95 warn) | **PARITY 0** — 28/28 nets, 151/151 nodes |
| esp32-laser-timing | **0 errors** (119 warn) | **PARITY 0** — 36/36 nets, 189/189 nodes, 25/25 NC |

Warnings are all parametric/environmental: `lib_symbol_issues` ("lib 'elt' not in
config", one per symbol, embedded lib_symbols still render) plus xt60's 4
`isolated_pin_label` (its four intentional named-NC single-pin nets). Zero are
connectivity signal.

**The ceiling is cleared (esp32 proof).** Through tscircuit's NATIVE export the two
many-pin custom-footprint chips truncated to **2 pins each** — U1 (ESP32-S3-WROOM-1,
41 pads) → 2, J1 (USB-C, 20 pads / 17 distinct) → 2. Through OUR converter U1 exports
all **41 pins** and J1 all **17 distinct pads** (both matching the sealed board), and
the whole board reaches node-for-node parity 0. The `≤1 many-pin custom-footprint
chip per board` limit that constrained Phase 1's boundary is gone.

Normalization to reach parity 0 is the documented minimum: the universal leading-digit
net renames (`N3V3→3V3`, `N5V→5V`, `N5V_A/N5V_C`) plus ONE per-board footprint
pad-name delta on esp32 (AMS1117 SOT-223 tab: tscircuit `sot223` names it pad `4`,
KiCad merges the tab into pad `2`; same 3V3 net both sides). No refdes renames were
needed. `gen_tscircuit.sh` now produces `kicad/<board>.kicad_sch` via this converter
(authoritative for the parity gate) and keeps tscircuit's native export as
`kicad/<board>.native.kicad_sch` for reference; it runs ERC + the parity gate
(`kicad_sch_parity.py`) and writes `verification/parity_converter.md`.

**Boundary consequence:** the schematic bridge now holds for custom-footprint-heavy
boards (modules + USB-C + multi-connector), not just commodity-footprint boards.
KiCad `04_kicad/` remains the sole fab-of-record; the converter output is the
verified schematic-capture bridge, not a fab source.

## Backend completion (2026-07-19) — adapter folded into the converter; output is backend-ready, no per-board adapter

Phase 3 proved a TSX-authored schematic can drive the full KiCad backend
(generate_board → rules → KRT → stitch → DRC `--schematic-parity`) to **DRC 0/0/0**
with board-netlist parity to the sealed board — but only via a one-shot,
project-local adapter (`prepare_backend_sch.py` + `assign_footprints.py`) that
patched five gaps the Phase-2 converter left for the netlist-parity gate. Those
five gaps are now **folded into the converter itself**
(`skills/kicad-pcb/scripts/circuit_json_to_kicad_sch.py`), so the converter output
is directly backend-ready and **no per-board adapter is needed**:

1. **Canonical net names.** tscircuit can't author a leading-digit net name, so a
   rail carries a documented author-prefix `N` (`5V`→`N5V`, `3V3`→`N3V3`,
   `12V`→`N12V`). `canon_net` strips a single leading `N` that guards a
   digit-leading rail and emits the canonical KiCad name on the global labels
   (`NRST`/`NC` etc. untouched — the char after `N` must be a digit). An optional,
   auto-discovered per-board `03_tscircuit/net_aliases.txt` (`TSNAME CANONICAL` per
   line) covers anything the convention can't reach.
2. **Footprint FPIDs.** Each symbol's Footprint field is filled from (a) a baked-in
   commodity token→FPID map — circuit.json class-disambiguates passives
   (`res0603` for a resistor vs bare `0603` for a capacitor), so no per-class
   guessing — and (b) a per-board override seeded from `02_parts/*/part.yaml`
   (keyed by LCSC/JLC code, MPN, and part-folder name → its `footprint:`) that
   **wins** for specialty parts. The token comes from
   `cad_component.footprinter_string` in circuit.json.
3. **MPN field dropped** (KiCad footprints carry none → `footprint_symbol_field_mismatch`).
4. **Test-point BOM attrs.** TP symbols emit `in_bom no` (matching the KiCad
   TestPoint footprint) with a concise `TP` Value that won't clip the board edge.

**Gate results (falsifiable, re-run):**

| Gate | Result |
|---|---|
| A — 3 ladder boards, converter → ERC + netlist parity | cook-loadcell **ERC 0 / parity 0** (16/16 nets, 75/75 nodes); xt60 **0 / 0** (28/28, 151/151); esp32 **0 / 0** (36/36, 189/189, 25 NC). Unchanged from Phase 2. |
| B — cook-loadcell full backend from converter output ALONE (no `prepare_backend_sch.py`/`assign_footprints.py`) | **DRC 0 / 0 / 0** (violations / unconnected / schematic-parity) and **board-netlist parity 0** vs sealed (77/77 nodes, 17/17 nets). generate_board loaded every FPID, audit PASS, KRT r2 imported. Adapter fully absorbed. |
| C — xt60 + esp32 backend-readiness spot-check | Canonical nets emitted (parity-proven); MPN fields = 0; esp32 **72/72** components carry an FPID (incl. specialty from 02_parts: ESP32-S3, LM339 SOIC-14, AMS1117 SOT-223, TerminalBlock, TS-1187A button) and 6 TP `in_bom no`; xt60 **34/47** — the 13 gaps are hand-`<footprint>` specialty parts (connectors/inductors/FET/buck ICs) whose TSX omits `supplierPartNumbers`, so circuit.json carries no code to key the 02_parts override. |

**Residual per-board step for the capstone (lipo3s, ~100 parts):** exactly ONE, and
it is an *authoring-completeness* step, not an adapter — every specialty part must
carry `supplierPartNumbers={{ jlcpcb: ["Cxxxx"] }}` in its TSX (which you author
anyway for the JLC BOM) so its LCSC code links to `02_parts/*/part.yaml`. Do that
and FPID resolution is automatic (cook-loadcell 29/29, esp32 72/72 prove it);
commodity passives need nothing (token map). No net-name renaming, footprint
injection, MPN surgery, or BOM-attr patching remains — those are the converter's
job now. Watch leading-digit rails beyond `5V`/`3V3` (`12V`→`N12V`, `1V8`→`N1V8`)
and add a `net_aliases.txt` line for any rail the strip-`N` convention can't reach.

## Phase 4 (2026-07-20) — TSX named the go-forward schematic-authoring standard

The pcb-design skill (stage 4-6) now names **tscircuit/TSX → our converter → native
`.kicad_sch`** the go-forward authoring path for the schematic stage, with schwriter2
retained as co-standard + fallback for footprints tscircuit can't yet express. The
downstream chain (ERC → generate_board → rules → KRT → verify) is unchanged and
authoring-tool-agnostic (it is netlist-driven). Full retirement of schwriter2 as the
DEFAULT completes as new boards actually ship through the TSX path with zero parity
regressions (criterion N≥3); the lipo3s capstone (usb-power-3s re-authored) is the
first such board and validates the standard end-to-end. Migration status: Phases 0-3
+ backend completion DONE and independently audited (converter breaks the exporter
ceiling; converter output alone drives the backend to DRC 0/0/0 with no adapter);
Phase 4 standard documented; capstone pending.

## Reversibility

Additive: every board keeps its KiCad generators; the `03_tscircuit/` folder stays a
study until a board proves out. If a difficulty class fails (e.g. specialty
connectors the footprinter can't express), those parts stay KiCad-native (via
`02_parts` FPID override or schwriter2) and the boundary is recorded here.
