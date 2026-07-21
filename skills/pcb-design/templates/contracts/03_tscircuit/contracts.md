# contract: 03_tscircuit/

**Purpose** — the board's tscircuit AUTHORING source: the circuit written once,
in TSX, plus the two artifacts it compiles to for its **two audiences**.

- **Humans** read `build/schematic.pdf` — tscircuit's OWN native render. This is
  the schematic document a release ships and what satisfies the human-graded S6
  readability item.
- **The machine** reads `kicad/<board>.kicad_sch` — OUR converter's output
  (`circuit_json_to_kicad_sch.py`), the AUTHORITATIVE bridge into the KiCad
  backend. It feeds ERC / netlist / parity / placement / routing. It is never
  required to be pretty; nobody opens it in a tscircuit-native flow.

Both derive from the same `build/circuit.json`, so they **cannot disagree on
connectivity**. Do not re-render the KiCad rebuild for the human PDF.

This is pipeline stage **03 — hand-written truth**, the same stage as `03_src/`
(hence the number). `03_src/` holds the KiCad-side generators + the promoted
route; `03_tscircuit/` holds the TSX the design is authored in. If they
disagree about the circuit, the TSX is right and the KiCad side is stale.

The bridge is OUR converter, **not** `tsci export -f kicad_sch` — that exporter
collapses every custom-`<footprint>` chip to one `Device:U_chip` symbol and
truncates it to 2 pins, and emits an unannotated sheet that netlists to 0 nets.

**Mutability** — three classes, and the boundary is load-bearing:

| Class | Paths | Rule |
|---|---|---|
| **HAND-EDITED truth** | `src/<board>.tsx`, `net_aliases.txt`, `parity_padmap.txt`, `sealed_ref.txt`, `package.json`, `README.md`, `GENERATE.md`, `contracts.md` | the only files a human writes here |
| **GENERATED** | `build/`, `kicad/`, `verification/`, `fab/` | emitted by `gen_tscircuit.sh` / `tsx_to_board.sh`. **Never hand-edited** — a hand-fix here is erased on the next run and silently diverges from the TSX. Fix the TSX and regenerate. Committed for reviewable diffs |
| **DISPOSABLE cache** | `dist/`, `.tscircuit/`, `node_modules/`, `tsx_build/` | gitignored, wiped freely |

## Allowed

| File | Class | What |
|---|---|---|
| `src/<board>.tsx` | hand | **THE BOARD** authored in tscircuit — the circuit, and optionally the placement (`pcbX`/`pcbY`/`pcbRotation`) |
| `package.json` | hand | tscircuit deps (name, main) |
| `README.md` | hand | what this board is + its authoring positioning |
| `GENERATE.md` | hand | how to (re)generate — the one command |
| `net_aliases.txt` | hand | `TSNAME CANONICAL` per line, for rails the strip-`N` convention can't reach. Auto-discovered |
| `parity_padmap.txt` | hand | documented per-board footprint pad-name deltas consumed by `kicad_sch_parity.py` |
| `sealed_ref.txt` | hand | one line: the sealed parity reference board, if not `04_kicad/<board>.kicad_pcb` |
| `build/circuit.json` | gen | tscircuit's canonical intermediate — the single source both audiences compile from |
| `build/schematic.svg` | gen | tscircuit's native render |
| `build/schematic.pdf` | gen | **the HUMAN schematic document — SHIP THIS in the release** |
| `kicad/<board>.kicad_sch` | gen | **the AUTHORITATIVE machine bridge** (our converter, `--mode layout` = wired) |
| `verification/tsc_netlist.txt` | gen | tscircuit readable-netlist |
| `verification/erc_converter.rpt` | gen | `kicad-cli sch erc --severity-all` on the converter sheet — **0 errors is the bar** |
| `verification/converter_netlist.net` | gen | netlist exported from the converter sheet |
| `verification/parity_converter.md` | gen | **node-for-node netlist parity vs sealed `04_kicad`** — 0 is the bar |
| `verification/parity.md` | gen | first-order component/net-count deltas (M1 signal) |
| `verification/notes.md` | gen+hand | fidelity gaps: footprint mapping, DRC deltas, unrouted nets |
| `verification/tsx_to_board_proof.md` | gen | the `tsx_to_board.sh` end-to-end proof record |
| `verification/net_check.net` | gen | scratch netlist export used for node-count sanity mid-authoring |
| `dist/**` | gen | tsci build output tree (mirrors `build/`; regenerate) |
| `.tscircuit/**` | gen | tsci cache (gitignored; regenerate) |
| `contracts.md` | hand | this file |

**`--study`-only artifacts** (DEFAULT OFF; `gen_tscircuit.sh <project> --study`).
These render tscircuit's OWN pcb/copper as a second opinion. They are **NEVER a
fab source** — KRT + the KiCad backend own the fab route (ADR-0002's two hard
lines). Allowed but never required, and never shipped in a release:

| File | What |
|---|---|
| `build/pcb.svg`, `build/assembly.svg`, `build/board.gltf` | tscircuit's own PCB / 3D render |
| `fab/gerbers.zip`, `fab/bom.csv`, `fab/cpl.csv` | tscircuit's own JLC package — study only |
| `kicad/<board>.kicad_pcb` | tscircuit native PCB export (study copper) |
| `kicad/<board>.native.kicad_sch` | tscircuit's native kicad_sch — reference only (the buggy exporter above) |
| `verification/drc.json` | `kicad-cli` DRC run ON the tscircuit export. Expect a LARGE mostly-parametric count (thin default 0.15 mm copper, no netclasses/pours). It is a fidelity signal, not a gate |

## The authoring rules (getting these wrong is silent, not loud)

1. **Bind pins to explicit nets**: `connections={{ pin: "net.NAME" }}`, not
   pairwise `<trace>`. This sidesteps tscircuit's `C1_pos`-style auto-net-naming
   so the netlist matches KiCad verbatim — parity by construction (canon S2).
2. **A specialty part MUST author `supplierPartNumbers={{ jlcpcb: ["Cxxxxx"] }}`.**
   That JLC code is the handle the converter uses to resolve the part's FPID from
   `02_parts/*/part.yaml`. **No supplier code → empty FPID → `generate_board`
   hard-errors by design.** This is the one authoring-completeness step.
3. **Specialty connectors need a `<footprint>` child** matching the KiCad land
   pattern. tscircuit's footprinter covers commodity parts (0402–1210, SOT-23,
   SOD-323, SOIC@1.27, pin rows, test points) but has no JST-XH shroud, no open
   solder-jumper, and no specialty connectors. Connector-heavy boards need this most.
4. **Leading-digit rails break the `net.` selector** (`3V3`, `5V`): author them
   `N`-prefixed (`N3V3`, `N5V`). The converter's `canon_net` strips a single
   leading `N` that guards a digit (`N5V`→`5V`, `N5V_A`→`5V_A`) and leaves
   `NRST`/`NC`/`NRESET` alone. Anything the convention can't reach goes in
   `net_aliases.txt`. These names are **load-bearing, not cosmetic** —
   `generate_board`'s polarity asserts, `rules/nets.yaml` netclass patterns, and
   the promoted KRT route all key on the canonical names.
5. **Give every `<hole>` an explicit `pcbX`/`pcbY`.** They default to (0,0) and
   STACK; the resulting "pcb_hole overlaps" error *silently disables the
   autorouter for the whole board*.
6. **Never seed the backend from tscircuit AUTO-placement.** Measured on
   cook-loadcell: 11 audit failures + 214 DRC violations incl. 22 courtyard
   overlaps and 8 shorting pads. It is DRC-clean against tscircuit's own
   courtyards and physically collides real KiCad footprints (golden rule 7).
   Authored `pcbX`/`pcbY` is the supported placement-as-code path.

## Forbidden

- **Hand-editing anything in `build/`, `kicad/`, `verification/`, `fab/`.** The
  next generate erases it, and until then the board silently disagrees with its
  own source. Fix the TSX.
- **Treating any `03_tscircuit/` artifact as a fab source.** tscircuit's gerbers,
  copper, and DRC are a study. The fab route is KRT + the KiCad backend, and the
  digital twin (`jlc_twin`) stays KiCad-side — its whole value is
  checker-independence (canon M1); a tool that authors + routes + self-DRCs
  against its own footprints collapses that.
- Writing to `07_releases/` or the sealed `04_kicad/` from here. Both
  `gen_tscircuit.sh` and `tsx_to_board.sh` are READ-ONLY w.r.t. them;
  `tsx_to_board.sh` reparents every backend output into the gitignored
  `tsx_build/` root.
- Committing `dist/`, `.tscircuit/`, `node_modules/`, `tsx_build/`.

## Validate — runnable by a fresh agent with zero context

```
export PATH="$HOME/.bun/bin:$PATH"
bash <kicad-pcb skill>/scripts/gen_tscircuit.sh <project>     # the bridge
bash <kicad-pcb skill>/scripts/tsx_to_board.sh <project>      # the whole board
```

1. `gen_tscircuit.sh` emits `build/circuit.json`, `build/schematic.pdf`, and
   `kicad/<board>.kicad_sch`, and prints **ERC 0 errors** + **netlist parity 0**
2. `tsx_to_board.sh` ends at **DRC 0/0/0** (`--severity-all --refill-zones
   --schematic-parity`) and **board parity 0** vs the sealed reference
3. every component in the converter output has a non-empty FPID (the converter
   prints `N components (N with FPID)` — the two numbers must be equal)
4. `.gitignore` covers `dist/`, `.tscircuit/`, `node_modules/`, `tsx_build/`
5. no file under `build/`, `kicad/`, `verification/`, `fab/` has been
   hand-edited — regenerate and diff; drift means someone edited a generated file

ERC **warnings** are baselined and parametric only: `lib_symbol_issues` (the
embedded `elt` lib isn't in the running kicad-cli config), `footprint_link_issues`,
`endpoint_off_grid` (layout mode's 0.635 mm fidelity grid), a few
`unconnected_wire_endpoint` stubs, and named-NC `isolated_pin_label`.

## Repair

- Hand-edited generated file → port the change into `src/<board>.tsx`, regenerate.
- Component with an empty FPID → add `supplierPartNumbers` (jlcpcb code) to the
  TSX and/or the matching `02_parts/<MPN>/part.yaml`.
- Netlist parity non-zero → it is a real circuit difference until proven
  otherwise. Only a *documented* footprint pad-name delta belongs in
  `parity_padmap.txt`; only a *documented* rail rename belongs in
  `net_aliases.txt`. Neither file is a place to silence a discrepancy.
- Converter fell back to `grid` mode (logged to stderr) → tscircuit's trace
  geometry couldn't import without a genuine cross-net short. Parity is still
  enforced, but the sheet is label-glue rather than wired; fix the TSX layout.

## Compliance audit (design-policies.md IDs)

This folder answers **S6** (the human schematic is tscircuit's own clean render —
the label-blob era is retired), **S1/S4** (ERC at severity-all = 0 errors; explicit
no-connects emitted as `no_connect` flags), **S2** (no auto-named nets reach copper
— rule 1 above), and **S-DSL** (the declaration compiles to NATIVE KiCad artifacts
and every gate runs on those artifacts, never on the DSL's claims).

It does NOT answer **R1/R6** (routing physics — KRT) or **M1** (the digital twin).
Those are the two permanent hard lines: the authoring tool must never self-grade
them. See `references/tscircuit-folder.md` and
`docs/decisions/0002-tscircuit-native-pipeline.md`.
