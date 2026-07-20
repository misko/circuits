# lipo3s-tsc — BRIEF (provenance + positioning)

**What this is.** `lipo3s-tsc` is the **capstone / demonstration project** of the
ADR-0001 tscircuit authoring-boundary migration: the sealed `usb-power-3s` board
(the "lipo3s" board — 3S LiPo XT60 input → 3× USB-A @2.5A + 1× USB-C @6A, 100
parts) **re-authored in tscircuit / TSX** and driven end-to-end through the
now-complete `TSX → circuit_json_to_kicad_sch converter → KiCad backend` path to an
orderable, DRC-clean board. It proves the fully-built tscircuit backend produces a
board **node-for-node identical** to the hand-KiCad original on a real 100-part
active power board.

**Electrical design = usb-power-3s (unchanged).** Same schematic, same nets, same
refdes, same real KiCad footprints, same values. Nothing electrical was redesigned;
only the *authoring front-end* changed (schwriter2 hand-KiCad → tscircuit TSX).

**Source of truth (frozen):**
- Board: `projects/usb-power-3s/04_kicad/usb_power_3s.kicad_pcb`
- Schematic model: `projects/usb-power-3s/03_src/generate_schematic.py`
- Parts + backend: `projects/usb-power-3s/02_parts/`, `03_src/`
- Sealed release: **usb-power-3s v1.3-2026-07-17, git_sha `d8992b8`**

`projects/usb-power-3s/` is the SEALED reference and is never touched by this project.

**How it was built (the proven path):**
1. `03_tscircuit/src/lipo3s_tsc.tsx` — the board authored NODE-FOR-NODE in TSX
   (specialty connectors/ICs as `<footprint>` children carrying the exact KiCad pad
   names; every part with an LCSC code authored via `supplierPartNumbers` so its FPID
   auto-resolves from the copied `02_parts`).
2. `tsci build` → `circuit.json` → `circuit_json_to_kicad_sch.py` (the BACKEND-READY
   converter: strip-`N` canonical net names, `02_parts`/commodity FPIDs, no MPN field,
   TP BOM attrs) → `03_tscircuit/kicad/lipo3s_tsc.kicad_sch`.
3. `03_tscircuit/build_backend.sh` — the copied `03_src` backend, run UNCHANGED, sourced
   from the converter schematic (board internal name kept `usb_power_3s` so the
   promoted KRT route `r5`, rules, and FPIDs transfer byte-for-byte):
   generate_board → audit → import_krt(r5) → route_taps → stitch_and_fill →
   generate_rules → DRC `--schematic-parity`.

**Gates (both green):**
- **GATE 1** — converter `kicad_sch` ERC 0 errors; netlist parity **0** node-for-node
  vs the sealed usb-power-3s schematic (55 nets / 290 connected nodes / 13 no-connects).
- **GATE 2** — backend **DRC 0/0/0** (violations/unconnected/schematic-parity) +
  board-netlist parity **0** (303/303 nodes identical, net-for-net) vs the sealed board.

**Reuse note (02_parts).** The copied `02_parts` `part.yaml` `footprint:` fields for
five parts were set to the FPID the *sealed board* actually uses (so the backend loads
identical footprints): CSD18543Q3A → `Package_SON:VSON-8_3.3x3.3mm_P0.65mm_NexFET`,
TPS2557DRBR → `Package_SON:VSON-8-1EP_3x3mm_P0.65mm_EP1.65x2.4mm`, MWSA1005S-3R3MT →
`Inductor_SMD:L_Sunlord_MWSA1005S`, 178.6165.0002 → `usb_power_3s:FuseHolder_ATO_FLR_EdgeTrim`,
XT60PW-M → `usb_power_3s:XT60PW-M_EdgeTrim`. Sourcing (LCSC/MPN) is unchanged.
