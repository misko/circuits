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
| **HAND-EDITED truth** | `src/<board>.tsx`, `net_aliases.txt`, `manifest.yaml`, `parity_padmap.txt`, `sealed_ref.txt`, `package.json`, `README.md`, `GENERATE.md`, `contracts.md` | the only files a human writes here |
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
| `manifest.yaml` | hand | `components: [refdes, …]` — the AUTHOR'S declared part list, written with the tsx. The S-COUNT parity base: after a silent tsci drop every generated artifact agrees, only this file disagrees (`count_parity.py`) |
| `parity_padmap.txt` | hand | documented per-board footprint pad-name deltas consumed by `kicad_sch_parity.py` |
| `sealed_ref.txt` | hand | one line: the sealed parity reference board, if not `04_kicad/<board>.kicad_pcb` |
| `build/circuit.json` | gen | tscircuit's canonical intermediate — the single source both audiences compile from. **IT IS A COPY, NOT A BUILD OUTPUT**: `tsci build` writes `dist/src/<TSX>/circuit.json` and never writes `build/`, so whoever drives the build MUST copy it here and canon **M-FRESH** (`build_provenance.py verify`) asserts the two are byte-identical before any gate reads it — unconnected, this path holds whatever an earlier run left and nine gates went green on it (2026-07-30) |
| `build/.tsci_build_marker` | gen | transient: `gen_tscircuit.sh` drops it immediately before `tsci build` and removes it on BOTH exits, so a producer that does not post-date it means the build did not run. A lingering one means a run was killed mid-build — delete it |
| `dist/**` | gen | `tsci build`'s OWN output tree (`dist/src/<TSX>/circuit.json`). Never read by a gate directly; it is the PRODUCER that M-FRESH resolves independently of the driver, which is what makes the comparison canon-M1 clean |
| `build/schematic.svg` | gen | tscircuit's native render — the intermediate the PDF is made from; deleted and regenerated with it |
| `build/schematic.pdf` | gen | **the HUMAN schematic document — SHIP THIS in the release** (`07_releases/…/pdf/schematic.pdf`). **IT IS NOT A BUILD OUTPUT EITHER**: `tsci build` never writes it, so the driver must DELETE it and re-render it every run — `rebuild_all.sh` [1r] does `rm -f` then `tsci export -f schematic-svg` + `rsvg-convert`, and canon **M-FRESH** (`build_provenance.py verify --render`, finding **F-RENDER**) then requires it to EXIST and to post-date the `circuit.json` it depicts. The delete is what makes a failed or skipped render produce ABSENCE (loud) instead of the previous revision (silent): measured 2026-07-30, this file was stamped 14:47:14 beside an 18:42:05 `circuit.json` and every gate was green |
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
| `.gitignore` | hand | keeps `dist/`, `.tscircuit/` and `node_modules/` out of git. **12 of the fleet's boards ship one and no contract permitted it until 2026-07-31** — the board-root contract has a `.gitignore` row, this one did not, and the gap was invisible because `--projects`' exit code was never read |
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
7. **Alphanumeric pad names are dropped SILENTLY.** tscircuit rejects pads like
   USB-C `A1..B12` or a shield `SH` WITHOUT an error, and the whole part vanishes
   with ERC still 0 (2026-07-21: four USB connectors, 48/52). Map every such pad
   in `parity_padmap.txt` and run `tsx_preflight.py` BEFORE the first tsci build;
   the refdes SET is then guarded by `count_parity.py` against the hand-authored
   `manifest.yaml` (canon S8 / S-COUNT, TSX-PRE).

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
python3 <kicad-pcb skill>/scripts/tsx_preflight.py <project>  # BEFORE the first build
bash <kicad-pcb skill>/scripts/gen_tscircuit.sh <project>     # the bridge
bash <kicad-pcb skill>/scripts/tsx_to_board.sh <project>      # the whole board
python3 <kicad-pcb skill>/scripts/count_parity.py <project>   # refdes SET parity
```

1. `tsx_preflight.py` passes **before the first tsci build** — alphanumeric pads
   (USB-C `A1..B12`, shield `SH`) are dropped by tscircuit with **ERC still 0**;
   each must be mapped in `parity_padmap.txt` first (canon TSX-PRE)
2. `gen_tscircuit.sh` emits `build/circuit.json`, `build/schematic.pdf`, and
   `kicad/<board>.kicad_sch`, and prints **ERC 0 errors** + **netlist parity 0**
3. `tsx_to_board.sh` ends at **DRC 0/0/0** (`--severity-all --refill-zones
   --schematic-parity`) and **board parity 0** vs the sealed reference
4. `count_parity.py` reports **0 symmetric difference** — the hand-authored
   `manifest.yaml` refdes SET equals every generated artifact (circuit.json,
   kicad_sch, netlist, board); a silent tsci drop surfaces here as the missing
   refdes (canon S8 / S-COUNT)
5. every component in the converter output has a non-empty FPID (the converter
   prints `N components (N with FPID)` — the two numbers must be equal)
6. `.gitignore` covers `dist/`, `.tscircuit/`, `node_modules/`, `tsx_build/`
7. no file under `build/`, `kicad/`, `verification/`, `fab/` has been
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
- Converter exited **3** with `LABEL PLACEMENT FAILED ... no legal placement`
  → a `global_label` has nowhere legible to go (canon S11). The converter
  de-collides labels by sliding an anchor outward along the reach it already
  has, or sideways across it, carrying a wire so connectivity is untouched; it
  will NOT turn a plate around or re-anchor it on another pin, because a plate
  is read as belonging to the pin at its blunt end. This is a HARD ERROR and
  deliberately **not** a fallback to `grid`: answering "this label cannot be
  placed legibly" with a different sheet is not an answer. The message names
  the label and what it occludes — open the TSX and give that corner room.
- Converter printed `N plate(s) left lying on a conductor` and exited **0** →
  the search cleared every HARD obstacle for those plates and no offset cleared
  the WIRES, so each keeps the placement the pre-wire pass gave it and S-OCCL
  reports it by name. **Wires are a SOFT obstacle class and everything older is
  HARD**, on purpose: a plate on a body/pin/Reference/other plate can composite
  into a different NET NAME (`ANT2` + `3V3_MOD` -> `N3V3_MOD2`, which read as
  though a 3V3 rail reached an RF port) and stays exit 3; a plate on a
  conductor is illegible but cannot say anything false, and is a matter of
  degree. MEASURED 2026-07-31: with wires HARD, four of the six layout-mode
  fleet sheets stop converting at all. The fix is the TSX layout — move the
  label's pin off the bus it reaches across.
- Reference/Value drawn on a wire → the property rows are de-collided too, and
  they may step SIDEWAYS as well as further out. `prop_rows` alone is a y-only
  offset from the body edge, which cannot clear a conductor leaving a vertical
  passive's own top pin (MEASURED on pluto-rx2-8way-v2: **9 of its 13** S-OCCL
  findings were this, not label plates). A displaced row must stay STRICTLY
  NEAREST its own symbol's body — a Reference that drifts to the neighbouring
  part is a prettier sheet that names the wrong component, and the candidate is
  refused rather than shipped.
- Converter exited **4** with `WIRE AMBIGUITY (S12) ... draws two nets as one
  conductor` → tscircuit routed two DIFFERENT nets onto the same line, so the
  emitted sheet would show one conductor where there are two. Nothing is
  written. The converter first tries to resolve it itself
  (`disambiguate_wires` drops the fewest imported segments that leave no two
  nets sharing ink, and the self-healing label pass still names every pin, so
  connectivity is untouched); exit 4 means even that was not enough, and it is
  deliberately **not** a fallback because by then the fallback has already been
  taken. Fix the TSX layout so the two nets do not share a track. **A JUNCTION
  DOT IS NOT THE REPAIR** — at a different-net touch point a dot does not
  annotate the ambiguity, it creates the short (MEASURED: a dot MERGES, a
  dotless T does not).
- **A CROSSING IS NOT A T.** Where a net continues collinearly out the far side
  of the wire it touches, the reader sees one wire crossing another — which is
  what it is, and what KiCad does — and S12 does not flag it. MEASURED
  2026-07-31 on the fleet: that discriminator is the difference between 8 raw
  endpoint-in-interior events and 3 real ones, and it is the whole of this
  board family's `interposer` (`KP_D4` crosses `KP_D2` and carries on) and of
  crow-recorder-central-v2's 3V3-against-0V9 pair, which reads as a power-rail
  short on a raw scan and is an ordinary undotted crossing in the render.
- **A GREEN S-OCCL DOES NOT MEAN THE LABELS POINT AT THE RIGHT PIN, and this is
  the one thing to remember about the de-collision pass.** MEASURED 2026-07-31:
  run it over the PRE-FIX direction derivation (`948ef54d`, where 1504 of 1504
  fleet labels carried an `anchor_side` exactly opposite
  `center - anchor_position`) and the sheet comes out with ZERO collisions while
  every plate still names the WRONG pin — the pass moves plates until nothing
  overlaps, and a plate fired across its own part is as movable as any other.
  Legibility and correctness are different questions; only the first is graded
  here, and no connectivity-keyed gate can see the second (same netlist, same
  ERC). Two fixtures in `tests/t1_converter.py` hold the pass off deliberately
  to keep that pinned. The shipped fixture `label_sides_v` is the miniature of
  it: its own vertical plates run through its own Reference and Value, and it
  reads clean only because the pass moves them (S-OCCL 2 -> 0, MEASURED).
- **A LABEL'S OWN WIRE IS FORGIVEN ONLY FROM BEHIND OR PERPENDICULAR.** A plate
  starts at the anchor the wire ends on, so the conductor it names lies on the
  plate's BASE EDGE and charging it there would move every label on every wired
  sheet. But a wire leaving that same anchor FORWARD — into the half-space the
  plate reaches into — runs down the plate's own centreline, through the
  letters. MEASURED on the shipped `two_resistors` fixture: `MID` at
  (38.100,27.940) reaching `+x` with its wire running to (50.800,27.940),
  **2.7819 mm of conductor through three glyphs in KiCad's own render**, and 0
  findings while the exemption was scoped to touch alone. It counted as a CLEAN
  CONTROL in two test files for as long as neither the pass nor S-OCCL had ever
  parsed a wire.

## Compliance audit (design-policies.md IDs)

This folder answers **S6** (the human schematic is tscircuit's own clean render —
the label-blob era is retired), **S1/S4** (ERC at severity-all = 0 errors; explicit
no-connects emitted as `no_connect` flags), **S2** (no auto-named nets reach copper
— rule 1 above), **S8/S-COUNT** (refdes SET parity between the hand-authored
`manifest.yaml` and every generated artifact via `count_parity.py`, plus **TSX-PRE**
alphanumeric-pad preflight via `tsx_preflight.py` before the first tsci build), and
**S-DSL** (the declaration compiles to NATIVE KiCad artifacts and every gate runs on
those artifacts, never on the DSL's claims), and **S12/S-WNET** (no two nets drawn
as one conductor — `sch_occlusion.py` on `kicad/<board>.kicad_sch`, plus the
converter's own `disambiguate_wires` + exit-4 verdict).

**S12'S DECLARED SCOPE LIMIT, and it is a measurement gap rather than a clean
result.** S12 grades `kicad/<board>.kicad_sch`. Under ADR-0002 Phase A the PDF a
human actually reads is tscircuit's OWN render, NOT a plot of that sheet —
MEASURED 2026-07-31: two boards in this fleet seal a `.kicad_sch` with zero wires
while their shipped `pdf/schematic.pdf` draws hundreds of wire segments and
junction dots. On a `--mode grid` board S12 therefore reads 0 because there is no
drawing in the file it reads, not because the drawing is sound. Both artifacts
descend from the same tscircuit routes, so fixing the TSX fixes both — but a
green S12 on a grid-mode board is not evidence about the human PDF.

It does NOT answer **R1/R6** (routing physics — KRT) or **M1** (the digital twin).
Those are the two permanent hard lines: the authoring tool must never self-grade
them. See `references/tscircuit-folder.md` and
`docs/decisions/0002-tscircuit-native-pipeline.md`.
