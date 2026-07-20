# The `tscircuit/` folder — an alternate, verified second-opinion render

Every board project MAY carry a `tscircuit/` folder: the same board authored in
[tscircuit](https://tscircuit.com) (React/TSX "electronics as code"), rendered to
a **full JLCPCB fab output** plus a **verification stack** that measures its
fidelity against the KiCad fab-of-record.

## Why this is allowed under canon S-DSL

The migration boundary is fixed by repo **ADR-0001**
(`docs/decisions/0001-tscircuit-authoring-boundary.md`): TSX authors the schematic;
ERC/rules/routing/twin/policy/release stay KiCad-side. S-DSL says circuit
declarations compile to NATIVE KiCad artifacts and every gate runs on those
artifacts, never on a DSL's claims. tscircuit satisfies the letter
of this because `tsci export` emits native `.kicad_pcb` / `.kicad_sch` — so we run
the SAME `kicad-cli` DRC on tscircuit's output that we run on our own, and we diff
its netlist against the sealed release. The `tscircuit/` folder is a **second
opinion, never a fab source**: KiCad + KRT + the gate stack remain authoritative
and are what actually gets ordered. This is the Model-A adapter the CircuitScript
evaluation anticipated — proven viable 2026-07-19 because tscircuit (unlike
CircuitScript) exports native KiCad, and `kicad-cli` loads and DRCs that export.

## Two audiences, two schematics (ADR-0002)

The schematic has two consumers, and they get DIFFERENT artifacts:
- **Humans** read `build/schematic.pdf` — tscircuit's OWN native render (clean,
  collision-free, real symbols). This is what a release ships as its schematic
  document, and what satisfies the human-graded S6 readability item.
- **The machine** reads `kicad/<board>.kicad_sch` — OUR converter output. It exists
  only to feed ERC / netlist / parity and the backend; it is never required to be
  pretty (in a tscircuit-native flow nobody opens it — you edit the TSX and view
  tscircuit's render). The v2 converter draws wires so it's readable IF opened, but
  its looks are not load-bearing.

Both derive from the same `circuit.json`, so they cannot disagree on connectivity.
Do NOT re-render the KiCad rebuild for the human PDF — that was polishing the wrong
artifact. Ship tscircuit's `schematic.pdf`.

## Folder format

```
tscircuit/
  README.md                 # this format + the board's S-DSL positioning
  GENERATE.md               # how to (re)generate — the one command
  package.json              # tscircuit deps (name, main)
  src/
    <board>.tsx             # THE BOARD authored in tscircuit
  build/                    # (generated) renders
    circuit.json            # [DEFAULT] tscircuit's canonical intermediate
    schematic.svg           # [DEFAULT]
    schematic.pdf           # [DEFAULT] HUMAN schematic doc = tscircuit's own render (SHIP in release)
    pcb.svg                 # [--study only]
    assembly.svg            # [--study only]
    board.gltf              # [--study only] 3D
  fab/                      # [--study only] tscircuit's own JLCPCB fab package (NEVER a fab source)
    gerbers.zip
    bom.csv  cpl.csv        # when the parts-engine resolves JLC codes
  kicad/                    # (generated) the S-DSL bridge
    <board>.kicad_sch       # [DEFAULT] OUR converter output (circuit.json -> annotated sch) — AUTHORITATIVE
    <board>.kicad_pcb       # [--study only] tscircuit native PCB export (study copper)
    <board>.native.kicad_sch# [--study only] tscircuit's native kicad_sch export — reference only (buggy, see below)
  verification/             # (generated) the bridge gate (+ second-opinion under --study)
    tsc_netlist.txt         # [DEFAULT] tscircuit readable-netlist
    drc.json                # [--study only] kicad-cli DRC run ON the tscircuit kicad export
    parity.md               # [DEFAULT] first-order component/net counts vs the sealed KiCad board (M1)
    erc_converter.rpt       # kicad-cli sch ERC on OUR converter kicad_sch (0 errors is the bar)
    converter_netlist.net   # netlist exported from OUR converter kicad_sch
    parity_converter.md     # node-for-node netlist parity: converter vs sealed 04_kicad
    notes.md                # fidelity gaps: footprint mapping, DRC deltas, unrouted nets
  parity_padmap.txt         # (optional) documented per-board pad-name deltas for the parity gate
```

## Generate

```
export PATH="$HOME/.bun/bin:$PATH"          # tsci runs on bun (installed per-user)
bash <kicad-pcb skill>/scripts/gen_tscircuit.sh <project_dir>            # BRIDGE ONLY (default)
bash <kicad-pcb skill>/scripts/gen_tscircuit.sh <project_dir> --study    # + tscircuit's own PCB render
```

**DEFAULT = the BRIDGE ONLY (ADR-0002 Phase D).** With no flag the script emits
only what the KiCad backend consumes + the gates that certify it: `circuit.json`,
the human `schematic.svg`/`schematic.pdf`, the converter `kicad/<board>.kicad_sch`,
the readable netlist, and the ERC + netlist-parity gates (`parity_converter.md`,
`parity.md`). It does NOT render tscircuit's own PCB/gerbers/3D — those are never a
fab source (KRT + the KiCad backend own the fab route — the two hard lines), so
producing them by default was duplicate compute.

**`--study`** restores the full second-opinion render (the `[--study only]` rows
above): `pcb.svg`, `assembly.svg`, `board.gltf`, `fab/gerbers.zip`, the native
`kicad_pcb`/`native.kicad_sch`, and the `kicad-cli` DRC-on-export (`drc.json`). Use
it only to eyeball tscircuit's own layout; the capability is retained + reversible.

To rebuild the WHOLE board (not just the schematic) from TSX in one command —
`tsci build` → converter → placement → rules → KRT → stitch → DRC 0/0/0 — use
`scripts/tsx_to_board.sh <project>` (ADR-0002 Phase E; see below). Both scripts are
READ-ONLY w.r.t. sealed `04_kicad/` and the releases.

## The schematic bridge is OUR converter, not `tsci export -f kicad_sch` (ADR-0001 Phase 2)

tscircuit's own `kicad_sch` exporter has two proven, fidelity-killing bugs:
1. **Symbol-id collision** — it derives a chip's symbol id as
   `Device:U_chip_<footprintName>`; a hand-authored `<footprint>` has no name, so
   every custom-footprint chip collapses to bare `Device:U_chip`. With ≥2 such
   many-pin chips (e.g. an ESP32 module + a USB-C jack) both share one symbol and
   each **truncates to 2 pins**, silently dropping the rest.
2. **No annotation** — the exported sheet isn't annotated, so
   `kicad-cli sch export netlist` builds **0 nets**.

So we do NOT use it for the bridge. `gen_tscircuit.sh` runs
`scripts/circuit_json_to_kicad_sch.py` on `build/circuit.json` to produce the
AUTHORITATIVE `kicad/<board>.kicad_sch` (the native tsci export is kept as
`.native.kicad_sch` for reference only). The converter renders circuit.json's full
connectivity model into a native sheet with a **UNIQUE `elt:SYM_<refdes>` lib_symbol
per component** (collision impossible) and **pins keyed to the exact KiCad pad name**
(first non-`unnamed_*` `pcb_*` port hint; internally-connected duplicate pads collapse
to one pin). Nets resolve via `subcircuit_connectivity_map_key` with propagation through
`internally_connected_source_port_ids`; GND pins render as ground power symbols + one
`PWR_FLAG`; explicit no-connects get `no_connect` flags. The sheet is annotated, so
netlist export builds real nets.

**The converter has two modes (`--mode`, ADR-0002 Phase A, DONE 2026-07-20):**
- **`layout` (DEFAULT, WIRED)** — consumes tscircuit's OWN schematic layout that
  circuit.json already carries (`schematic_component` center/size, `schematic_port`
  geometry, `schematic_trace` routes, `schematic_net_label`) and emits a READABLE WIRED
  sheet: a KiCad `(wire)` where tscircuit drew a trace, a KiCad label where tscircuit
  used a net label, GND as ground symbols. tscircuit schematic units map to KiCad mm
  (×12.7, y-flipped, snapped to a 0.635 mm grid so pin tips and wire ends coincide
  exactly). **This retires the S6 "label-blob" finding** — cook-loadcell 0→80 wires,
  xt60 0→211, esp32 0→230, all ERC 0 + netlist parity 0. Parity is preserved *by
  construction*: connectivity is still keyed to the authoritative canonical-net model,
  cross-net wire segments are filtered, dangling wire ends are pruned (KiCad
  `wire_dangling` is an ERC ERROR), and a self-healing pass adds a name label to any pin
  a wire didn't reach.
- **`grid` (FALLBACK)** — v1's original layout: **one `global_label` per pin as net
  glue** (schwriter2's rule — the netlister joins by label-name), no drawn wires. The
  `layout` mode AUTO-FALLS-BACK to this per board if the trace geometry can't import
  without a genuine cross-net short (logged to stderr), so parity is never worse than v1.

**Proven on all three Phase-1 boards: `kicad-cli sch erc --severity-all` = 0 errors
and node-for-node netlist parity = 0 vs the sealed `04_kicad` board** (cook-loadcell
16 nets/75 nodes, xt60 28/151, esp32 36/189 + 25 NC). The esp32 proof: U1 (41-pad
ESP32-S3) and J1 (USB-C, 17 distinct pads) that truncated to **2 pins each** through
the native export now export **all** pins and reach parity. Parity normalization is
the documented minimum — universal leading-digit net renames (`N3V3`→`3V3`, `N5V`→`5V`)
plus, on esp32, one footprint pad-name delta (AMS1117 SOT-223 tab `4`≡KiCad `2`),
recorded in `tscircuit/parity_padmap.txt` and consumed by `kicad_sch_parity.py`.

In the DEFAULT `layout` mode the converter kicad_sch is now a WIRED, readable sheet
that mirrors tscircuit's own schematic (wires where it drew traces, labels where it used
net labels) — S6 retired. In the `grid` fallback it is a net-glue LAYOUT (labels, not
drawn wires) — a faithful annotated capture. ERC warnings are parametric only:
`lib_symbol_issues` (the embedded `elt` lib isn't in the running kicad-cli config),
`footprint_link_issues`, `endpoint_off_grid` (layout mode's 0.635 mm fidelity grid), a
few `unconnected_wire_endpoint` stubs, and any named-NC single-pin `isolated_pin_label`.

## The converter output is BACKEND-READY — no per-board adapter (ADR-0001 backend completion, 2026-07-19)

The same converter output that clears the netlist-parity gate now drives the FULL
KiCad backend (generate_board → rules → KRT → stitch → DRC `--schematic-parity`) to
DRC 0/0/0 with **no per-board adapter** — proven on cook-loadcell
(`projects/cook-loadcell/tscircuit/backend_proof/build_from_tsx.sh`, board parity 0
vs the sealed board). The converter fills the four things the backend needs that the
parity gate never inspects:

**Net names — the canonical-name convention.** tscircuit's `net.` selector can't
author a leading-digit net name, so a rail is authored with an author-prefix `N`
(`5V`→`N5V`, `3V3`→`N3V3`, `12V`→`N12V`, `1V8`→`N1V8`). The converter's `canon_net`
**strips a single leading `N` that guards a digit-leading rail** and emits the
canonical KiCad name (`N5V`→`5V`, `N5V_A`→`5V_A`). Names where `N` is followed by a
non-digit (`NRST`, `NC`, `NRESET`) are left untouched. For any rail the convention
can't reach, drop a per-board **`tscircuit/net_aliases.txt`** (auto-discovered next
to `build/`): one mapping per line, `TSNAME CANONICAL` (`=` or `->` also accepted),
`#` starts a comment. The convention + alias file are the ONLY net-naming inputs;
generate_board's polarity asserts, `rules/nets.yaml` netclass patterns, and the
promoted KRT route all key on the canonical names, so getting these right is
load-bearing, not cosmetic.

**Footprint FPIDs — commodity token map + `02_parts` override.** Each symbol's
Footprint FPID is resolved from two sources, override-first:
- **`02_parts/*/part.yaml` (specialty parts, wins).** Auto-discovered by walking up
  from `build/circuit.json` to the project's `02_parts/`. Each part.yaml's
  top-level `footprint:` becomes the FPID, keyed by every handle circuit.json might
  carry — the LCSC/JLC code (`sourcing.lcsc`), the `mpn:`, and the part-folder name.
  This is why a specialty part must author `supplierPartNumbers={{ jlcpcb: ["Cxxxx"] }}`
  in its TSX: that code (in `cad_component`/`source_component.supplier_part_numbers`)
  is what links it to its 02_parts footprint. **A specialty part with NO supplier
  code in its TSX gets an empty FPID** (generate_board then hard-errors, by design)
  — this is the one authoring-completeness step, not an adapter.
- **Baked-in commodity token map (`COMMODITY_FP` in the converter).** For parts not
  in 02_parts. The token comes from `cad_component.footprinter_string`, which
  class-disambiguates passives (`res0603` for a `<resistor>` → `Resistor_SMD:...`;
  bare `0603` for a `<capacitor>` → `Capacitor_SMD:...`) so R-vs-C needs no
  per-class table. Covers 0402–1210 R/C, SOT-23/-5/-6/-223, SOD-123/-323, SMA/SMB,
  SOIC-8/14/16 @1.27, 2.54mm pin headers, 2.5mm JST-XH rows, SolderJumper-2, and
  the `smtpad_circle_d1.5`/`testpoint_pad` test points.

**MPN field dropped** (KiCad footprints carry none → `footprint_symbol_field_mismatch`);
sourcing lives in `02_parts/` + `bom_seed`. **Test points** emit `in_bom no`
(matching the KiCad TestPoint footprint's exclude-from-BOM) with a concise `TP`
Value that won't clip the board edge.

Note `part.yaml`'s `footprint:` value is read as the first whitespace-free token, so
a trailing YAML `# inline comment` (even one containing quotes, as TS-1187A has) is
dropped cleanly and never corrupts the emitted s-expr.

## Placement-as-code — the PCB bridge (ADR-0002 Phase B, PROVEN 2026-07-20)

The schematic bridge has a PCB sibling: `scripts/circuit_json_to_kicad_pcb.py`
lands every part at the placement tscircuit carries in `circuit.json`
(`pcb_component` center / rotation / layer — authored in the TSX as
`pcbX`/`pcbY`/`pcbRotation`), reusing the sch converter's FPID map + net model,
into a native `.kicad_pcb` placement SEED. Mapping: `kx = origin_x + tsc_x`,
`ky = origin_y − tsc_y` (y-flip), `korient = (−pcbRotation) mod 360`;
`--outline-from <ref.kicad_pcb>` copies the Edge_Cuts + NPTH mounting holes and
sets the origin to that outline's bbox center (drops the TSX-authored placement
into the certified board frame). Missing placement / FPID is a hard error.

**It is a SEED, not a finished board — our audit + legalize + route certify it.**
The measured two-seed result on cook-loadcell (`placement_proof/NOTES.md`):

- **tscircuit's AUTO-placement is unusable as a seed** (golden rule 7 at scale):
  the raw auto-layout throws **11 audit failures** (4 decoupler-proximity, 7
  functional-silk) and **214 DRC violations incl. 22 courtyard overlaps + 8
  shorting pads** — it is DRC-clean against tscircuit's OWN courtyards but
  physically collides real KiCad footprints. NEVER feed it to the backend.
- **AUTHORED `pcbX/pcbY`** (the engineered floorplan written as code) reproduces
  the sealed floorplan pixel-for-pixel (28/29 parts; the `<solderjumper>` centers
  at pad-1 not body-center → one documented 1.27 mm origin pre-compensation), and
  after a legalize+silk pass reaches **audit PASS → DRC 0/0/0 → board parity 0**.

**Verdict: a real ERGONOMIC win (placement lives with the schematic + netlist in
one reviewable file) that MOVES the placement hand-work rather than removing it** —
authored `pcbX/pcbY` are the same coordinates a hand-coded `generate_board`'s
`ANCHOR/SEED` dicts hold. And `generate_board` shrinks but does not vanish: the
silk story (functional captions, refdes de-collision, F.Fab, TP labels) is NOT in
tscircuit's model and stays KiCad-side (the reusable `legalize_and_silk.py`).
**Adopt OPTIONAL, per-board** (boards actively authored in tscircuit); keep
hand-coded placement valid. Connector-heavy boards need a per-footprint
origin-offset table in the placer.

## The one command — `tsx_to_board.sh` (ADR-0002 Phase E, THE go-forward rebuild)

`scripts/tsx_to_board.sh <project>` is the canonical ONE-COMMAND tscircuit-native
pipeline: it drives a TSX-authored board through the UNCHANGED, netlist-driven KiCad
backend, from source to a DRC-clean, parity-checked board. This is the go-forward
rebuild command for a tscircuit-native project (the schematic-only `gen_tscircuit.sh`
stops at the bridge; this runs the whole backend).

```
export PATH="$HOME/.bun/bin:$PATH"
bash <kicad-pcb skill>/scripts/tsx_to_board.sh <project>            # generate_board placement (default)
bash <kicad-pcb skill>/scripts/tsx_to_board.sh <project> --placement tsx   # placement-as-code seed (Phase B)
```

Flow (each gate's result is printed; ends at DRC 0/0/0):
```
tsci build  ->  circuit_json_to_kicad_sch  ->  sch export netlist  ->  ERC (0 err)
  ->  [placement: generate_board.py  OR  circuit_json_to_kicad_pcb.py at pcbX/pcbY + legalize]
  ->  generate_rules (rules ride into the router, canon R1)
  ->  KRT route (reuse the promoted 03_src/route/r*.kicad_pcb chain if present)
  ->  [route_taps.py if present]  ->  stitch_and_fill  ->  generate_rules LAST
  ->  DRC --severity-all --refill-zones --schematic-parity  ->  board_netlist_parity vs sealed
```

**The KiCad backend is UNCHANGED** — the driver only wires TSX authoring into it and
reparents every backend output into an isolated build root (`tscircuit/tsx_build/`,
gitignored, wiped each run so the driver is idempotent) via a `03_src` symlink and
the `__file__.parent.parent` reparent trick. The sealed `04_kicad/` and releases are
NEVER touched. Discovery is automatic: the internal board name from
`generate_board.py`'s `.net` path (may differ from the TSX name — `lipo3s_tsc.tsx`
builds `usb_power_3s`), the newest promoted route chain, optional `route_taps.py` /
`audit_board.py`. The sealed parity reference defaults to
`<project>/04_kicad/<board>.kicad_pcb`, overridable with a one-line
`tscircuit/sealed_ref.txt` (used by lipo3s-tsc to point at the sibling usb-power-3s
board it reproduces).

**Proven end-to-end on TWO tscircuit-native boards to DRC 0/0/0 + board parity 0
(2026-07-20):**

| board | parts | route | DRC (v/u/p) | board parity |
|---|---|---|---|---|
| cook-loadcell | 29 + 4 holes | r2 | 0 / 0 / 0 | **0** (77 nodes / 17 nets) |
| lipo3s-tsc (capstone) | 96 + 4 holes | r5 + taps | 0 / 0 / 0 | **0** (303 nodes / 56 nets) |

Proof records: each project's `tscircuit/verification/tsx_to_board_proof.md`.

## What the verification stack proves (and its limits)

- **DRC-on-export** is the honest number: tscircuit's auto-layout/route does NOT
  automatically satisfy `kicad-cli` at `--severity-all` (the trivial spike board
  showed 7 clearance/edge items with no pours). Record the count in `notes.md`;
  it is the fidelity signal, not a pass/fail gate for the KiCad release.
- **parity.md** gives first-order component/net-count deltas. A true node-for-node
  parity needs a refdes/net-name normalization map (the two front-ends name nets
  differently — tscircuit auto-names like `C1_pos`); that map lives in `notes.md`
  per board. Parity 0 after normalization is the bar for taking tscircuit
  seriously as an authoring front-end for that board.
- tscircuit's own footprints/parts-engine are NOT `jlc_twin`-checked here — the
  twin remains a KiCad-side, JLC-CAD gate. Do not treat a tscircuit render as
  order-ready; it is a design study.

## Authoring notes (from the cook-loadcell reference, 2026-07-19 — node-for-node parity achieved on 33 parts)

- **Parity by construction:** give each element `connections={{ pin: "net.NAME" }}`
  rather than pairwise `<trace>`. This binds pins to explicit nets and sidesteps
  tscircuit's `C1_pos`-style auto-net-naming, so the readable-netlist matches KiCad
  verbatim.
- **Leading-digit net names break the `net.` selector** (`3V3`, `5V`): rename to
  `N3V3`/`N5V` (or similar) and record the map in `notes.md`. This was the ONLY
  normalization needed to hit node-for-node parity on the reference board.
- **`<hole>` elements default to (0,0) and STACK** — the resulting "pcb_hole
  overlaps" error *silently disables the autorouter for the whole board*. Give
  every `<hole>` (and any pad-relative mechanical) an explicit `pcbX`/`pcbY`.
- **Footprinter covers commodity parts** (0402-1210, SOT-23, SOD-323, SOIC@1.27,
  pin rows, test points) with correct pad count/pitch, but has **no JST-XH shroud,
  no open solder-jumper, and specialty connectors** — use a `<footprint>` child
  matching the KiCad land pattern for those. Connector-heavy boards need this most.
- **Expected DRC-on-export is large and mostly parametric:** tscircuit routes thin
  default geometry (0.15mm tracks, 0.30mm vias) and adds no netclass/pour, so
  `kicad-cli --severity-all` reports hundreds of track_width/via/silk items plus a
  handful of real auto-router shorts in congested corners. Parity proves the DESIGN;
  the copper is a study, not fab-grade. Classify in `notes.md` (parametric vs real).

## The registry — reusable module library (ADR-0002 Phase C, PROVEN 2026-07-20)

Our proven, repeated subcircuits live as **parameterized tscircuit modules** in a
shared library at the repo root, `tscircuit_modules/` (NOT inside any one project — so
many boards import the same certified block):

```
tscircuit_modules/
  README.md                 # catalog + compose pattern + each module's API + next candidates
  src/<Module>.tsx          # the reusable parameterized components (export a function component)
  demo/                     # a gate board that composes the module(s) + its verification stack
    <demo>.tsx  package.json
    build/circuit.json  kicad/<demo>.kicad_sch  verification/{parity.md,channel_parity.py,erc.rpt,*.net}
```

**Compose pattern.** A new board `import`s the module and instantiates it (once per
instance, `.map` for N-identical channels), passing ONLY board-level nets + parameters;
the module channel-PREFIXES its internal nets so instances never collide. Render +
certify with the EXISTING bridge — no new tooling:

```tsx
import { ShuntMonitor } from "../src/ShuntMonitor"
{[1,2,3,4,5,6].map((ch) => (
  <ShuntMonitor key={`mon${ch}`} channel={ch} i2cAddress={0x40+(ch-1)}
    busNet={`VF${ch}`} loadNet={`VP${ch}`} sdaNet="SDA" sclNet="SCL"
    alertNet="ALERT" vsNet="N3V3" gndNet="GND" />
))}
```
```
tsci build <demo>.tsx  →  circuit_json_to_kicad_sch.py build/circuit.json \
   -o kicad/<demo>.kicad_sch --parts-dir <project>/02_parts  →  kicad-cli sch erc / export netlist
```

**Two authoring rules the registry leans on:** (1) a specialty part in a module needs
BOTH `supplierPartNumbers={{ jlcpcb: [...] }}` (the JLC code links to the `02_parts`
footprint via the converter override) AND a `<footprint>` child or footprinter token
(so tscircuit renders it); point `--parts-dir` at the project that owns those footprints.
(2) the ADR-0001 canonical-net convention still applies (`N3V3` → `3V3`).

**Proven.** `ShuntMonitor` (INA238 + WSLP2726 Kelvin shunt + input filter + decoupler,
from ble-bus-bar's `port_channel`) composed **6×** reproduced the 6 hand-authored
channels **node-for-node** (parity PASS all 6, addresses distinct 0x40..0x45, Kelvin
preserved, ERC 0 errors). A module emits circuit.json only — every gate still runs on the
native artifact; routing + twin stay KiCad-only. Adopt OPTIONAL, per-board. Next
candidates: RJ45 port-channel, power-entry-protection, ESP32 standard hookup
(`tscircuit_modules/README.md`).

## Toolchain (persistent, per-user)

- `bun` at `~/.bun/bin/bun` (tscircuit's runtime).
- `tsci` via `npm i -g tscircuit`; `@tscircuit/cli` also present.
- Both persist on disk; a fresh shell/agent needs only `PATH="$HOME/.bun/bin:$PATH"`.
