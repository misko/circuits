# Phase-3 backend proof — cook-loadcell (ADR-0001)

> **UPDATE 2026-07-19 — ADAPTER FOLDED IN, no per-board adapter remains.**
> The five gaps below (items 1–5) are now handled inside the converter
> (`skills/kicad-pcb/scripts/circuit_json_to_kicad_sch.py`): canonical net names
> (strip-`N` convention + optional `tscircuit/net_aliases.txt`), footprint FPIDs
> (commodity token map + `02_parts/*/part.yaml` MPN/LCSC override), MPN field
> dropped, and TP `in_bom no` + concise `TP` value. `build_from_tsx.sh` now copies
> the converter output **directly** (step [1] is a plain `cp`, no transform) and
> still reaches **DRC 0/0/0 + board parity 0**. `prepare_backend_sch.py` /
> `assign_footprints.py` are **superseded** and out of the chain — retained below
> only as the historical record of what the converter now does. The table's
> "One honest caveat" (the fix belongs upstream in the converter) is now resolved.


**Claim under test (ADR-0001 Phase 3):** a TSX-authored schematic can drive the
"unchanged generate_board → rules → KRT → verify chain" to DRC 0/0/0, end to end.

**Verdict: PROVEN.** The TSX-authored schematic drives the entire cook-loadcell
KiCad backend to **DRC 0 / 0 / 0** (violations / unconnected / schematic-parity)
and produces a board **node-for-node identical to the sealed 04_kicad board**
(77/77 nodes, 17/17 nets). The downstream chain is byte-for-byte unchanged; the
handoff needs **one adapter** (`prepare_backend_sch.py`) that finishes the
schematic-capture the Phase-2 converter left incomplete for the KiCad backend.

Reproduce: `bash build_from_tsx.sh` (writes only into this dir; never touches
`04_kicad/`). Final lines: `violations: 0 {}` / `unconnected: 0` / `parity: 0`
/ `BOARD PARITY 0 -> PASS`.

---

## The integration point — where schematic meets board

cook-loadcell's pipeline is **netlist-driven**, not schematic-object-driven.
`03_src/generate_board.py` does NOT read the `.kicad_sch`; it reads the
**exported netlist** `06_build/netlists/cook_loadcell.net`
(`kicad-cli sch export netlist`). From that netlist it takes, per part:

- the refdes set (its coded floorplan `ANCHOR`/`SEED` is keyed by refdes),
- the KiCad footprint **FPID** (`lib:name`) — it `FootprintLoad`s each one,
- the pad→net node map (it binds pads by `(refdes, pad-number)` → net name),
- the net names (its polarity/role asserts and `rules/nets.yaml` netclass
  patterns key on canonical names like `5V`, `3V3`, `E_PLUS`).

**So the schematic→board handoff is the netlist file, and whatever authored the
schematic is irrelevant downstream *provided its exported netlist carries those
four things in the sealed board's vocabulary*.** Everything after generate_board
(audit, KRT `import_krt` of the promoted `r2.kicad_pcb`, `stitch_and_fill`,
`generate_rules`, DRC) is refdes/net-name-keyed and schematic-source-agnostic.

This is why the chain can be reused **unchanged**: the 03_src scripts run
byte-for-byte (this dir's `03_src` is a symlink to `../../03_src`; each script
keys its project root off `Path(__file__).parent.parent`, which the symlinked
invocation reparents to `backend_proof/`, so outputs land here, never in the
sealed `04_kicad/`).

## Was the chain "unchanged"? — YES, except ONE adapter at the schematic

The Phase-2 converter kicad_sch cleared the Phase-2 **netlist-parity** gate
(`kicad_sch_parity.py`: ref/pad/net node equality). But that gate never
inspects three things the **KiCad backend + its DRC `--schematic-parity` gate**
require, so the converter output is not directly consumable. `prepare_backend_sch.py`
finishes the schematic capture — converter kicad_sch → backend-ready kicad_sch:

| # | What the converter left | Why the backend needs it fixed | Fix in the adapter |
|---|---|---|---|
| 1 | net labels `N5V`, `N3V3` (tscircuit can't author leading-digit names) | generate_board polarity asserts + `rules/nets.yaml` PWR class + promoted KRT route r2 (routed on `5V`/`3V3`) + DRC parity all key on canonical names → 11 `net_conflict` | rename labels `N5V→5V`, `N3V3→3V3` (same `DEFAULT_NETMAP` as `gen_tscircuit.sh`) |
| 2 | **empty Footprint field** on every symbol | generate_board `FootprintLoad`s by FPID and **hard-errors** on a blank; DRC parity → 36 `footprint_symbol_mismatch` | fill each symbol's Footprint from the tscircuit footprint **token authored in the `.tsx`** via a token→FPID map (the role schwriter2's `sym_fp` plays; `0603`/`0805` resolve per R/C class) |
| 3 | `MPN` field on every symbol (from tscircuit `supplierPartNumbers`) | KiCad lib footprints carry no `MPN` → 20 `footprint_symbol_field_mismatch` | drop `MPN` (sourcing lives in `02_parts/` + `bom_seed`, as on the sealed board) |
| 4 | TP symbols `in_bom yes` | KiCad TestPoint footprint defaults exclude-from-BOM → 7 `footprint_symbol_mismatch` (BOM-attr) | mark TP symbols `in_bom no` (as schwriter2's `no_bom_syms={"TP"}` does) |
| 5 | TP Value = tscircuit default `simple_test_point` (18 chars) | renders as footprint value silk **clipped by the board edge** → 2 `silk_edge_clearance` | give TPs a concise silk-safe Value |

After the adapter, `kicad-cli sch export netlist` emits canonical nets + FPIDs
**automatically**, so there is **no netlist-level patching** and the 03_src
backend is untouched. Adapter is `.kicad_sch`-scoped text surgery keyed off the
`elt:SYM_<refdes>` lib_id; footprint tokens are read from the authored
`src/cook_loadcell.tsx` (so footprint identity is TSX-derived, not lifted from
the sealed board).

**One honest caveat (the right place for the fix is upstream):** all five items
are gaps in the **Phase-2 converter** (`circuit_json_to_kicad_sch.py`), not in
tscircuit authoring — the `.tsx` carries every fact needed (footprint tokens,
net intent, TP identity). The cleanest long-term home for items 1–5 is the
converter itself (emit canonical nets + FPIDs + BOM attrs, skip MPN); the proof
keeps them in a project-local adapter to leave the shared converter untouched.

## Results

- **DRC** (`kicad-cli pcb drc --severity-all --refill-zones --schematic-parity`,
  parity vs the TSX-derived kicad_sch): **0 violations / 0 unconnected / 0 parity.**
- **Board-netlist parity vs sealed `04_kicad`** (`board_netlist_parity.py`):
  **77/77 nodes identical, net-for-net, 17/17 nets** (75 connected + the 2 U1
  no-connects VBG/XO). Board render is pixel-identical to the sealed board in
  copper, GND pour, placement, and captions — the only visible delta is TP silk
  reading `TP` instead of `E+/S-/…` (item 5's concise value).
- **ERC** on the TSX schematic: 0 errors (51 baselined warnings, all
  `lib_symbol_issues` from the embedded `elt` lib — same as Phase 2).
- **audit_board.py** (I1/I8/I-AN/IP/IZ/IS): PASS, 0 failures.

## Readiness for the lipo3s capstone (usb-power-3s, ~100 parts)

**Green to proceed** through this same path, with these frictions to expect:

1. **The adapter must move into the toolchain, or be regenerated per board.**
   `prepare_backend_sch.py`'s five transforms are general (net normalize, token→
   FPID, MPN drop, BOM attr, value hygiene), but the **token→FPID map is
   board-specific**: every distinct footprint on lipo3s needs a token→`lib:name`
   entry, and `0402`/`0603`/`0805`/SOT/SOIC-class ambiguities resolve per part
   class. For a 100-part board this map is the bulk of the work. Strongly prefer
   fixing items 1–4 in the **converter** so the map is the only per-board input
   (and can be seeded from `02_parts/`).
2. **Custom/specialty footprints.** cook-loadcell is all commodity KiCad
   library parts, so token→FPID is a clean lookup. lipo3s has USB-C, the buck
   module, XT60, etc. Phase-1 showed these author fine in TSX via `<footprint>`
   children carrying KiCad pad names — but each still needs a real KiCad FPID
   (a vendored `.pretty` or a std-lib name) in the map, and its pad NUMBERS must
   equal the netlist pins (they did here because the converter uses KiCad pad
   names as pins — verify this holds for merged-pad / thermal-pad parts like
   SOT-223 and DPAKs; ADR notes an AMS1117 tab pad-name delta needed a padmap).
3. **generate_board polarity/role asserts are net-name-locked.** They passed
   here only because net normalization restored `5V`/`E_PLUS`/`DAT`. lipo3s's
   generate_board will have its own asserts (battery polarity, buck SW/FB) — the
   net-name normalization must cover every leading-digit rail lipo3s uses
   (`3V3`, `5V`, and watch for `12V`/`1V8`-style names → `N12V`/`N1V8`).
4. **The promoted route (`r2`) is net-name-keyed.** `import_krt` matches tracks
   to board nets by name; any net-name drift silently unroutes that net →
   unconnected DRC. Net normalization is load-bearing, not cosmetic.
5. **DRC `--schematic-parity` is the real gate** (KiCad 10) and it is strict:
   footprint fields, BOM/DNP attrs, and net names must ALL agree between the
   `.kicad_sch` and the board. On a 100-part active board expect the converter's
   BOM-attr and field deltas to scale; budget for reconciling `dnp`,
   `exclude_from_bom`, and merged-pad `net_conflict` classes (the ADR's known
   KiCad-10 noise classes) as part of the adapter, per part family.

Bottom line: the backend **accepts** TSX authoring end-to-end today; the residual
work for the capstone is **converter maturity** (emit backend-complete kicad_sch)
so the per-board adapter shrinks to just the footprint map — which `02_parts/`
already contains.
