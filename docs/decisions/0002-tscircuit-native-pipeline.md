# ADR-0002 (repo) — tscircuit-native pipeline: design in tscircuit, certify + fab in KiCad

Status: **accepted** 2026-07-20
Scope: cross-project / pipeline. Extends ADR-0001 (which moved only schematic
authoring). This deepens adoption to the full front-end while keeping the KiCad
verification backbone. Binds the pcb-design + kicad-pcb skills.

## The reframe (why this is adoption, not risk)

Stop treating tscircuit and our KiCad pipeline as two competing stacks. They are a
**dev loop vs CI/release loop** — exactly like software. You don't delete CI because
the local linter is nice; you run both, each for its strength.

- **tscircuit = the design environment** (everything a human touches): authoring,
  schematic layout, placement, module reuse, fast in-editor preview (its own
  DRC/autoroute/3D for quick feedback).
- **KiCad backend = CI + fabrication** (invoked as a service at commit/release):
  KRT routing, `jlc_twin`, `policy_audit`, immutable release.
- **The converter is the compiler** between them (circuit.json → native KiCad).

One pipeline, one compile step. This dissolves the redundancy: each stage has a single
owner; nothing is run twice for real (the duplicate "study" renders are retired, Phase D).

## Best-of-both, by stage

| Capability | tscircuit owns (dev loop) | KiCad backend owns (CI + fab) |
|---|---|---|
| Circuit authoring | TSX, typed, reviewable | — |
| Schematic layout | wired, readable (converter v2) | ERC certifies |
| Placement | placement-as-code (`pcbX/pcbY`) | audit + legalize certify |
| Module reuse | registry — our proven blocks as components | — |
| Fast feedback | its DRC / autoroute / 3D as PREVIEW | — |
| Routing (fab) | draft/preview only | **KRT** — ampacity, escape, pours |
| Digital twin | — | **jlc_twin** — independent referee |
| Policy audit + release | — | certification layer |

## The two hard lines (CI guarantees, not "tscircuit can't")

Two rows stay KiCad-only because the authoring tool must never self-grade them:
- **Routing physics.** tscircuit has no ampacity/netclass concept — the cook-loadcell
  reference shorted a congested corner and routed 0.15 mm defaults. KRT owns the fab
  route (tscircuit autoroute is allowed as an in-editor preview only).
- **The digital twin.** Its entire value is checker-independence (canon M1) — comparing
  our board against JLC's own CAD. It caught 4 wrong-footprint boards this campaign. A
  tool that authors + routes + self-DRCs against its own footprints collapses that.

## Rollout (each phase shippable + reversible)

- **Phase A — Schematic quality (converter v2, wired). DONE 2026-07-20.** Consume
  circuit.json's `schematic_component` positions + `schematic_trace` wire routes +
  `schematic_net_label` (not one-label-per-pin). Emit a wired, readable `.kicad_sch`
  that still ERC-0 + netlist-parity-0. **Retires the fleet-wide S6 label-blob finding.**
  v1 label-grid stays as fallback for boards whose trace geometry doesn't import cleanly.

  **Result.** `circuit_json_to_kicad_sch.py` gained a `--mode layout` (DEFAULT; `--mode
  grid` = v1 fallback), wired into `gen_tscircuit.sh` as the default emitter. It maps
  tscircuit schematic units -> KiCad mm (×12.7, y-flipped, snapped to a 0.635 mm grid so
  pin tips and wire ends coincide exactly), builds a UNIQUE per-refdes lib_symbol whose
  pins land on the `schematic_port` centers, draws a KiCad `(wire)` per `schematic_trace`
  edge, emits a KiCad label per `schematic_net_label`, and keeps GND as ground power
  symbols + one PWR_FLAG. Connectivity is still keyed to v1's authoritative canonical-net
  model, so parity is preserved *by construction*: cross-net wire segments are filtered,
  dangling wire ends are pruned (KiCad `wire_dangling` = ERC error), and a self-healing
  pass adds a name label to any pin a wire didn't reach — and the whole board falls back
  to the grid if a genuine cross-net short survives. Verified on all three Phase-1 boards
  with **0 → many** drawn wires, ERC 0, netlist parity 0 (none fell back):

  | board | v1 wires | v2 wires | ERC errors | netlist parity |
  |---|---|---|---|---|
  | cook-loadcell | 0 | 80 | 0 | 0 (16 nets / 75 nodes / 2 NC) |
  | xt60-usb-supply | 0 | 211 | 0 | 0 (28 nets / 151 nodes) |
  | esp32-laser-timing | 0 | 230 | 0 | 0 (36 nets / 189 nodes / 25 NC) |

  Before/after renders: `projects/cook-loadcell/tscircuit/verification/schematic_v1_grid.png`
  (the label blob) vs `schematic_v2_wired.png` (the wired sheet). ERC warnings are
  parametric only (`endpoint_off_grid` from the 0.635 mm grid, `lib_symbol_issues`/
  `footprint_link_issues` env notes, a few `unconnected_wire_endpoint` stubs).
- **Phase B — Placement-as-code.** `pcbX/pcbY` in TSX is the placement seed; a
  `circuit.json → .kicad_pcb` placer lands parts there; `generate_board` shrinks to
  "import placement → legalize → audit." Placement lives with the schematic.
- **Phase C — The registry.** Publish our proven subcircuits as reusable tscircuit
  modules (RJ45 port-channel, power-entry-protection, ESP32 standard hookup, Kelvin-shunt
  block). New boards COMPOSE certified blocks — tscircuit ergonomics, our engineering.
- **Phase D — Retire the redundancy.** TSX becomes the sole authoring path (schwriter2
  deprecated as boards migrate); slim `gen_tscircuit.sh` to the bridge only (drop the
  duplicate gerber/3D/native-PCB study exports we never use).
- **Phase E — One command.** `board.tsx → tsci build → converter → [audit → KRT → DRC →
  twin → policy → release]`, documented as THE process. tscircuit checks run during
  authoring (fast feedback); KiCad gates run at commit/release (CI).

## Relationship to ADR-0001 & reversibility

ADR-0001's boundary (native artifacts, gates run on artifacts, S-DSL) is UNCHANGED and
still governs — this ADR just moves more of the FRONT-END into tscircuit while the gates
stay put. Additive + reversible: every board keeps its KiCad generators until it migrates;
schwriter2 remains the fallback; the hard lines (routing/twin) are permanent by design.
