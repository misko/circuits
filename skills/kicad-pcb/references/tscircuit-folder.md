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
  kicad/                    # (generated) NATIVE export — the S-DSL bridge
    <board>.kicad_pcb
    <board>.kicad_sch
  verification/             # (generated) the second-opinion gate
    tsc_netlist.txt         # tscircuit readable-netlist
    drc.json                # kicad-cli DRC run ON the tscircuit kicad export
    parity.md               # component/net counts vs the sealed KiCad board (M1)
    notes.md                # fidelity gaps: footprint mapping, DRC deltas, unrouted nets
```

## Generate

```
export PATH="$HOME/.bun/bin:$PATH"          # tsci runs on bun (installed per-user)
bash <kicad-pcb skill>/scripts/gen_tscircuit.sh <project_dir>
```

The script builds every artifact above, runs `kicad-cli` DRC on the tscircuit
KiCad export, and writes `parity.md`. It is READ-ONLY w.r.t. `04_kicad/` and the
releases — it only writes under `tscircuit/`.

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
