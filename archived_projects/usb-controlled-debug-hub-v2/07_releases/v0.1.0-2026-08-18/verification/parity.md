# tscircuit-vs-KiCad parity — usb-controlled-debug-hub-v2

Compares the tscircuit render's netlist against the KiCad fab-of-record.
Canon S-DSL: KiCad stays authoritative; this quantifies tscircuit fidelity.

KiCad board: `/home/mouse9911/gits/circuits/projects/usb-controlled-debug-hub-v2/04_kicad/usb_controlled_debug_hub.kicad_pcb`
- KiCad: 146 footprints, 104 named nets
- tscircuit: ~164 components, ~117 nets

NOTE: refdes/net-name conventions differ between the two front-ends; a
node-for-node parity requires a name-normalization map (see notes.md). The
count deltas above are the first-order fidelity signal.
