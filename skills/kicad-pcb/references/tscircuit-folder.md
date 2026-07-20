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

## Folder format

```
tscircuit/
  README.md                 # this format + the board's S-DSL positioning
  GENERATE.md               # how to (re)generate — the one command
  package.json              # tscircuit deps (name, main)
  src/
    <board>.tsx             # THE BOARD authored in tscircuit
  build/                    # (generated) renders
    circuit.json            # tscircuit's canonical intermediate
    schematic.svg
    pcb.svg
    assembly.svg
    board.gltf              # 3D
  fab/                      # (generated) JLCPCB fab package
    gerbers.zip
    bom.csv  cpl.csv        # when the parts-engine resolves JLC codes
  kicad/                    # (generated) the S-DSL bridge
    <board>.kicad_pcb       # tscircuit native PCB export (study copper)
    <board>.kicad_sch       # OUR converter output (circuit.json -> annotated sch) — AUTHORITATIVE
    <board>.native.kicad_sch# tscircuit's native kicad_sch export — reference only (buggy, see below)
  verification/             # (generated) the second-opinion gate
    tsc_netlist.txt         # tscircuit readable-netlist
    drc.json                # kicad-cli DRC run ON the tscircuit kicad export
    parity.md               # first-order component/net counts vs the sealed KiCad board (M1)
    erc_converter.rpt       # kicad-cli sch ERC on OUR converter kicad_sch (0 errors is the bar)
    converter_netlist.net   # netlist exported from OUR converter kicad_sch
    parity_converter.md     # node-for-node netlist parity: converter vs sealed 04_kicad
    notes.md                # fidelity gaps: footprint mapping, DRC deltas, unrouted nets
  parity_padmap.txt         # (optional) documented per-board pad-name deltas for the parity gate
```

## Generate

```
export PATH="$HOME/.bun/bin:$PATH"          # tsci runs on bun (installed per-user)
bash <kicad-pcb skill>/scripts/gen_tscircuit.sh <project_dir>
```

The script builds every artifact above, runs `kicad-cli` DRC on the tscircuit
KiCad export, and writes `parity.md`. It is READ-ONLY w.r.t. `04_kicad/` and the
releases — it only writes under `tscircuit/`.

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

## Toolchain (persistent, per-user)

- `bun` at `~/.bun/bin/bun` (tscircuit's runtime).
- `tsci` via `npm i -g tscircuit`; `@tscircuit/cli` also present.
- Both persist on disk; a fresh shell/agent needs only `PATH="$HOME/.bun/bin:$PATH"`.
