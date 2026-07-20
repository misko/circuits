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

  Before/after renders: `projects/cook-loadcell/03_tscircuit/verification/schematic_v1_grid.png`
  (the label blob) vs `schematic_v2_wired.png` (the wired sheet). ERC warnings are
  parametric only (`endpoint_off_grid` from the 0.635 mm grid, `lib_symbol_issues`/
  `footprint_link_issues` env notes, a few `unconnected_wire_endpoint` stubs).
  **Phase A refinement (the real quality fix).** The converter v2 rebuild still has
  KiCad-side label collisions (our generic symbols/text, NOT tscircuit's — tscircuit's
  own render is clean). Rather than polish the rebuild (S-OCCL on the machine artifact),
  we SPLIT THE AUDIENCES: the **human schematic document** is tscircuit's own render
  (`build/schematic.pdf` via `schematic.svg` → rsvg-convert), which a release ships and
  which satisfies human-graded S6; the **machine artifact** is the converter
  `.kicad_sch` (ERC/netlist/parity only, never required to be pretty). `gen_tscircuit.sh`
  now emits `build/schematic.pdf`. Both come from the same circuit.json, so connectivity
  can't diverge. See `references/tscircuit-folder.md` "Two audiences, two schematics."

- **Phase B — Placement-as-code. PROVEN + measured on cook-loadcell 2026-07-20;
  verdict: adopt OPTIONAL, per-board, NOT fleet-mandatory.** A `circuit.json →
  .kicad_pcb` placer (`scripts/circuit_json_to_kicad_pcb.py`) lands each part at
  tscircuit's `pcb_component` center/rotation/layer (mapped tsc-mm/y-up → KiCad
  mm/y-down, `pcbRotation` → `−orient`), reusing the sch converter's FPID
  resolution + net model; our audit + legalize + route then certify it.

  **The honest two-seed measurement (`projects/cook-loadcell/03_tscircuit/placement_proof/`,
  NOTES.md):**
  - **RAW tscircuit AUTO-placement** (the TSX authored `pcbX/pcbY` for the 4 holes
    ONLY; 29 electrical parts auto-placed) → `audit_board` **11 FAIL** (4
    decoupler-proximity: C3–C6 13–16 mm from U1 vs 8–12 budget; 7 functional-silk),
    and `kicad-cli` DRC on the raw seed **214 violations incl. 22 courtyard
    overlaps + 8 shorting pads** — tscircuit's layout is DRC-clean against its OWN
    courtyards but physically collides real KiCad footprints. **Golden rule 7
    confirmed at scale: auto placement is unusable as a seed.**
  - **AUTHORED placement-as-code** (`pcbX/pcbY/pcbRotation` = the engineered
    floorplan written into the TSX) → seed reproduces the sealed floorplan **28/29
    parts pixel-identical** (SJ1 Δ1.27 mm: tscircuit's `<solderjumper>` centers at
    pad-1 not body-center — documented origin quirk, 1 coord correction);
    legalize+silk (0 caps snapped — floorplan already satisfies IP; 7 functional
    captions + 33 refdes + 7 TP labels generated) → **audit PASS**; reused promoted
    route r2 → **DRC 0/0/0**; board parity **0 (77/77 nodes)**.

  **Verdict.** Placement-as-code is a real **ergonomic** win (placement +
  schematic + netlist in one reviewable file, edited in the design tool) but it
  **MOVES the placement hand-work, it does not remove it** — the authored
  `pcbX/pcbY` are the same coordinates `generate_board`'s `ANCHOR/SEED` dicts hold.
  And `generate_board` **shrinks but does not vanish**: the silk story (functional
  captions, refdes de-collision, F.Fab, TP labels) is not in tscircuit's model and
  stays KiCad-side — it became `legalize_and_silk.py` (the durable, seed-agnostic
  legalizer any seed needs). So: adopt where the ergonomics pay (boards actively
  authored in tscircuit); keep hand-coded placement fully valid; **never** seed the
  backend from tscircuit auto-placement; promote the placer + a generalized
  legalize+silk pass to the toolchain regardless. Connector-heavy boards need a
  per-footprint origin-offset table in the placer (the `<solderjumper>` quirk).
- **Phase C — The registry. PROVEN on ONE module 2026-07-20; verdict: the compose
  model delivers "author once, compose everywhere" for a proven block.** Publish our
  proven subcircuits as reusable tscircuit modules. New boards COMPOSE certified blocks
  — tscircuit ergonomics, our engineering.

  **Library location.** A shared `tscircuit_modules/` at the REPO ROOT (deliberately
  outside any one project so many boards import it): `src/<Module>.tsx` (the reusable
  parameterized components), `demo/` (a gate board that composes them + its verification
  stack), `README.md` (catalog + the compose pattern + the API of each module + the next
  candidates). See `references/tscircuit-folder.md` "The registry".

  **First module — `ShuntMonitor`** (`tscircuit_modules/src/ShuntMonitor.tsx`), distilled
  from ble-bus-bar's `port_channel(i)`: the canonical repeated-proven subcircuit —
  INA238 (I2C, address by A1/A0 strap) + WSLP2726 0.5 mR Kelvin shunt + differential input
  filter (2×10R + 100n) + 100n decoupler. Props:
  `ShuntMonitor({ channel, i2cAddress, busNet, loadNet, sdaNet, sclNet, alertNet, vsNet,
  gndNet, shuntMilliohm?, inaJlc?, shuntJlc? })`. Internal Kelvin nodes `KA{ch}`/`KB{ch}`
  are channel-prefixed so N instances never collide; the address decodes from `i2cAddress`
  to the four strap targets {GND,VS,SDA,SCL}. Emits `RS/RP/RN/CD/CB/U{ch}` with
  ble-bus-bar's exact refdes.

  **Gate (falsifiable, `tscircuit_modules/demo/`, PASS).** The demo composes `ShuntMonitor`
  **6×** (channels 1..6, addresses 0x40..0x45) + a minimal bus/MCU stub, renders via
  `tsci build → circuit.json → our converter (`--parts-dir` = ble-bus-bar's `02_parts`) →
  kicad_sch` (54/54 components with real FPIDs). Result (`verification/parity.md`):
  - **NODE-FOR-NODE PARITY vs the sealed ble-bus-bar board: PASS on all 6 channels** —
    every `{RS,RP,RN,CD,CB,U}{i}` pad→net map is identical to the hand-authored channel.
  - **Addresses distinct 0x40..0x45: PASS** (A1/A0 straps decode correctly per channel;
    the six channels are byte-identical in topology except at those two strap pins).
  - **Kelvin sense preserved: PASS** (RP taps the shunt bus stud → IN+, RN taps the load
    stud → IN-=VBUS, CD bridges KA↔KB, per channel).
  - **ERC `--severity-all`: 0 errors** (380 warnings, all in the three documented
    parametric classes: endpoint_off_grid / lib_symbol_issues / footprint_link_issues).

  **Verdict.** One authored module, instantiated 6×, reproduced the 6 hand-authored
  channels EXACTLY — the only per-channel variation is the I2C address, which is a module
  *parameter*. The registry model works for our proven repeated blocks with **no new
  tooling**: the same converter + gate stack certifies a composed board unchanged. Next
  candidates (in `tscircuit_modules/README.md`): RJ45 port-channel, power-entry-protection,
  ESP32 standard hookup. Adopt OPTIONAL, per-board (like placement-as-code); a module is
  an authoring convenience that emits circuit.json — the gates, routing, and twin are
  unmoved.
- **Phase D — Retire the redundancy. DONE 2026-07-20.** TSX becomes the go-forward
  authoring path (schwriter2 deprecated to FALLBACK-ONLY, not deleted — still the path
  for footprints tscircuit can't yet express); slim `gen_tscircuit.sh` to the bridge
  only (drop the duplicate gerber/3D/native-PCB study exports we never use).

  **Result.** `gen_tscircuit.sh <project>` (no flag) now emits ONLY the bridge:
  `build/circuit.json`, the human `schematic.svg`/`schematic.pdf`, the converter
  `kicad/<board>.kicad_sch`, the readable netlist, and the ERC + netlist-parity gates
  (`parity_converter.md`, `parity.md`). The tscircuit PCB STUDY exports — native
  `.kicad_pcb`, `pcb.svg`, `assembly.svg`, `board.gltf`, `fab/gerbers.zip`,
  `.native.kicad_sch`, and the DRC-on-tscircuit-export — are GATED behind `--study`
  (DEFAULT OFF). tscircuit's own PCB/gerbers are never our fab source (KRT + the KiCad
  backend own the fab route — the two hard lines), so rendering them by default was
  duplicate compute; `--study` keeps the capability fully reversible. Verified on
  cook-loadcell: `gen_tscircuit.sh` (no flag) → bridge + ERC **0 errors** + netlist
  parity **0**, and does NOT emit the study artifacts; `--study` restores the full
  render (DRC-on-export 451, as expected for tscircuit's thin default copper). Docs
  updated: pcb-design schematic-authoring step (schwriter2 = fallback-only), kicad-pcb
  golden-rule 3d (the wired path is now tscircuit, not "until schwriter emits wires"),
  and `tscircuit-folder.md` folder-format (study outputs marked `[--study only]`).
  schwriter2.py is RETAINED.
- **Phase E — One command. DONE 2026-07-20.** `scripts/tsx_to_board.sh <project>` is the
  canonical one-command tscircuit-native pipeline, generalized from cook-loadcell's
  `backend_proof/build_from_tsx.sh`:
  `tsci build → circuit_json_to_kicad_sch → sch export netlist → ERC →
  [placement: generate_board OR circuit_json_to_kicad_pcb at pcbX/pcbY] → generate_rules
  → KRT route (reuse the promoted 03_src/route/r*.kicad_pcb chain if present) →
  [route_taps] → stitch_and_fill → generate_rules LAST →
  DRC --severity-all --refill-zones --schematic-parity → board_netlist_parity`.

  **The KiCad backend runs BYTE-FOR-BYTE UNCHANGED** (it's netlist-driven) — the driver
  only wires TSX authoring into it and reparents every backend output into an isolated,
  gitignored build root (`03_tscircuit/tsx_build/`, wiped each run → idempotent) via a
  `03_src` symlink + the `__file__.parent.parent` reparent trick, so the sealed
  `04_kicad/` and releases are never touched. It auto-discovers the internal board name,
  the promoted route chain, and optional backend steps; the sealed parity reference is
  `<project>/04_kicad/<board>.kicad_pcb` or a one-line `03_tscircuit/sealed_ref.txt`.

  **Proven end-to-end on TWO tscircuit-native boards to DRC 0/0/0 + board parity 0:**

  | board | parts | route | DRC (viol/unconn/parity) | board parity |
  |---|---|---|---|---|
  | cook-loadcell (via backend_proof setup) | 29 + 4 holes | r2 | 0 / 0 / 0 | **0** (77 nodes / 17 nets) |
  | lipo3s-tsc (the 100-part capstone) | 96 + 4 holes | r5 + taps | 0 / 0 / 0 | **0** (303 nodes / 56 nets) |

  Proof records (non-destructive): each project's
  `03_tscircuit/verification/tsx_to_board_proof.md`. Documented as THE go-forward rebuild
  command in the pcb-design skill (stage 4-6) and `tscircuit-folder.md`. tscircuit checks
  run during authoring (fast feedback); the KiCad gates run at commit/release (CI).

## Migration status: COMPLETE (2026-07-20)

Phases 0–E are done + audited. tscircuit is the adopted design front-end; the KiCad
backend + gate stack is the unchanged CI/fab backbone; the converter is the compiler
between them, and `tsx_to_board.sh` is the one-command pipeline that runs it end to end
(proven DRC 0/0/0 + board parity 0 on cook-loadcell and the 100-part lipo3s-tsc capstone).
The two hard lines are permanent by design — **routing physics** (KRT) and the
**digital twin** (jlc_twin) stay KiCad-only because the authoring tool must never
self-grade them. schwriter2 is RETAINED as the fallback for footprints tscircuit can't
yet express (deprecated from co-standard, never deleted). Every step remains additive +
reversible: each board keeps its KiCad generators until it migrates, `--study` restores
the full second-opinion render, and no sealed artifact was mutated.

## Relationship to ADR-0001 & reversibility

ADR-0001's boundary (native artifacts, gates run on artifacts, S-DSL) is UNCHANGED and
still governs — this ADR just moves more of the FRONT-END into tscircuit while the gates
stay put. Additive + reversible: every board keeps its KiCad generators until it migrates;
schwriter2 remains the fallback; the hard lines (routing/twin) are permanent by design.
