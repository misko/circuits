# Netlist / schematic parity — usb-hub-3s-v3 v1.1

**Node-for-node parity: 0 mismatches.**

Measured by `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity`
against the sealed board + schematic (the `.kicad_sch` sits beside the board so
the parity pass actually RUNS, not a hollow 0):

- board `source/usb_hub_3s_v2.kicad_pcb` == schematic `source/usb_hub_3s_v2.kicad_sch`
- **0 violations / 0 unconnected / 0 schematic_parity** (`drc.json`, `drc_parity.json`)
- Standalone re-measure of the archived `source/` (V-REL-FPLIB) reproduces
  **0 / 0 / 0** — the archive is self-contained.

The exported netlist `source/usb_hub_3s_v2.net` is the parity reference; the
115-component schematic and the board agree node-for-node. E-INV (16/16
invariants) additionally holds against `source/usb_hub_3s_v2.net`.
