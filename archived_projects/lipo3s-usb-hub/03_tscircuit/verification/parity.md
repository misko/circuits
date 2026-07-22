# tscircuit-vs-KiCad parity — lipo3s-usb-hub

Compares the tscircuit render's netlist against the KiCad fab-of-record.
Canon S-DSL: KiCad stays authoritative; this quantifies tscircuit fidelity.

KiCad board: `/home/mouse9911/gits/circuits/projects/lipo3s-usb-hub/04_kicad/lipo3s_usb_hub.kicad_pcb`
- KiCad: 100 footprints, 55 named nets
- tscircuit: ~223 components, ~54 nets

NOTE: refdes/net-name conventions differ between the two front-ends; a
node-for-node parity requires a name-normalization map (see notes.md). The
count deltas above are the first-order fidelity signal.
