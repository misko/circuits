# tscircuit-vs-KiCad parity — usb-hub-3s-v3

Compares the tscircuit render's netlist against the KiCad fab-of-record.
Canon S-DSL: KiCad stays authoritative; this quantifies tscircuit fidelity.

KiCad board: `/home/mouse9911/gits/circuits/projects/usb-hub-3s-v3/04_kicad/usb_hub_3s_v2.kicad_pcb`
- KiCad: 119 footprints, 64 named nets
- tscircuit: ~118 components, ~65 nets

NOTE: refdes/net-name conventions differ between the two front-ends; a
node-for-node parity requires a name-normalization map (see notes.md). The
count deltas above are the first-order fidelity signal.
