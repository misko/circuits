# tscircuit-vs-KiCad parity — esp32-laser-timing

Compares the tscircuit render's netlist against the KiCad fab-of-record.
Canon S-DSL: KiCad stays authoritative; this quantifies tscircuit fidelity.
Full analysis + root-cause + classification: **`notes.md`**.

KiCad board: `../04_kicad/esp32_laser_timing.kicad_pcb` — 76 footprints
(72 electrical + 4 M3 mounting holes), 36 named nets.

## Components
- **72 / 72** electrical components authored node-for-node (same refdes, real footprint,
  JLC part). 4 KiCad mounting-hole footprints (H1–H4) are non-electrical `<hole>` — no
  refdes/net in a netlist, correctly absent.

## Nets (after `3V3→N3V3`, `5V→N5V` normalization)
- **tscircuit MODEL** (circuit.json / readable-netlist), node-for-node vs KiCad:
  **36 / 36 named nets identical.** The design is exact — including the 41-pin ESP32-S3
  module and 14-pin LM339, zero pin-label mismatches.
- **tscircuit kicad_sch EXPORT**, node-for-node vs KiCad: **14 / 36**. The gap is entirely
  in tscircuit's DSL→native-KiCad schematic exporter, not the authoring:
  1. custom-footprint chips share one `Device:U_chip` symbol → U1 & J1 collide, truncated to
     2 pins each (root-caused in `notes.md`);
  2. dense-net fragmentation (GND cap pins split onto `Net-(C4-Pad2)`; VTH1/VTH2 split).

## Gates on the tscircuit export (fidelity signals, not release gates)
- ERC (`kicad-cli sch erc --severity-all`): **563** (~494 parametric grid/symbol, 40 real
  no-connects, ~29 collision/fragmentation artifacts).
- DRC (`kicad-cli pcb drc --severity-all`): **260 violations / 150 unconnected** (~200
  parametric text/footprint/clearance, 9 real auto-router shorts, 24 mask bridges).

## Node-for-node verdict
- **tscircuit design model: YES** (36/36) — parity by construction.
- **Through the native kicad_sch export: NO** — the exporter is not fidelity-preserving for a
  large/active board with 2+ many-pin hand-authored-footprint chips.
