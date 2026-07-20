# lipo3s-tsc / tscircuit — TSX authoring front-end (ADR-0001 capstone)

This is the **authoring source** for the lipo3s-tsc board: usb-power-3s re-authored
in tscircuit/TSX and driven through the converter + KiCad backend to DRC 0/0/0,
node-for-node identical to the sealed usb-power-3s board. Unlike a normal
`03_tscircuit/` second-opinion folder, here the TSX is the *actual front-end* whose
converter output feeds the backend (see ../01_docs/BRIEF.md).

- `src/lipo3s_tsc.tsx`   — the board authored node-for-node (100 parts, 68 nets)
- `kicad/lipo3s_tsc.kicad_sch` — (generated) the converter's backend-ready schematic
- `build_backend.sh`     — drive the copied 03_src backend from the converter schematic
- `verification/`        — ERC, netlist, parity artifacts

Canon S-DSL / ADR-0001: KiCad `.kicad_sch`/`.kicad_pcb` + the gate stack are the
fab-of-record. TSX authors the schematic; ERC/rules/routing/DRC/twin/policy/release
all run on native KiCad artifacts.
