# t0 fixtures — hand-authored `circuit.json` inputs

Minimal, hand-authored `circuit.json` files that drive
`skills/kicad-pcb/scripts/circuit_json_to_kicad_sch.py`. Each carries only the element
types the converter actually reads: `source_component`, `source_port`, `source_net`,
`pcb_port`, `pcb_smtpad`, `cad_component`, plus the `schematic_component` /
`schematic_port` / `schematic_trace` / `schematic_net_label` geometry that selects
`MODE=layout`. (`source_trace` is deliberately absent — the converter never reads it;
connectivity comes from `subcircuit_connectivity_map_key`.)

| fixture | what it is | defect it catches |
| --- | --- | --- |
| `two_resistors` | R1+R2 0603 in series across VIN/MID/GND | baseline regression: sheet must be **annotated** (an un-annotated sheet builds 0 nets), commodity `res0603` → FPID must resolve, and the one `schematic_trace` must import as a KiCad wire without shorting |
| `polarized` | D1 (SOD-123) + polarized C1 | pad-1 identity loss. D1 pad `1` (cathode) must land on `OUT` and C1 pad `1` (+) on `VIN`. A pad-name/pin-number mix-up or a `port_hints` regression silently reverses a diode or a polarized cap |
| `manypin_custom_fp` | U1 (41 pins) + U2 (24 pins), both with an **empty** `footprinter_string` | THE regression fixture for tscircuit's two exporter bugs: symbol-id collision (both chips collapsing to bare `Device:U_chip`) and 2-pin truncation. Assert **41 pins for U1, 24 for U2** and two *distinct* FPIDs — resolved from the local `02_parts/*/part.yaml` override, not the commodity map. Pad names are non-numeric (`P1..P41`, `B1..B24`) so the `port_hints` path is exercised rather than the `pin_number` fallback |
| `digit_rails` | R1/C1/C2 across nets authored `N5V` and `N3V3` | leading-digit rail aliasing. `canon_net` must strip the documented author-prefix `N` guard so the netlist names are `5V` and `3V3`; a regression yields `N5V`/`N3V3` and silently mismatches the board's rails |
| `thermal_ep` | U1 eFuse on `dfn8` (8 pads); `02_parts/*/part.yaml` annotates pad `9` (EP) `tie: GND` | exposed-thermal-pad drop. The EP tscircuit's pad-only footprint can't express is **absent** from `circuit.json`, so the symbol would omit it and the board pad would float invisibly to parity. `load_part_ties` must EMIT the missing symbol pin so the netlist carries **(U1, 9) → GND** alongside the in-circuit GND pad 8. Stripping `tie:` from the part.yaml must make pad 9 vanish (the annotation is load-bearing, not unconditional) |

Validate one with:

    python3 skills/kicad-pcb/scripts/circuit_json_to_kicad_sch.py \
        tests/fixtures/t0/<name>/circuit.json -o /tmp/<name>.kicad_sch
    kicad-cli sch erc -o /tmp/<name>.erc.rpt /tmp/<name>.kicad_sch
    kicad-cli sch export netlist -o /tmp/<name>.net /tmp/<name>.kicad_sch

All four exit 0, report `[MODE=layout, WIRED]`, and produce **0 ERC errors** (warnings are
only the unavailable `elt:` symbol lib / footprint libs and isolated single-pin labels).
