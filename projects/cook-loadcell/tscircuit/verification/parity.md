# tscircuit-vs-KiCad parity — cook-loadcell

Compares the tscircuit render's netlist against the KiCad fab-of-record.
Canon S-DSL: KiCad stays authoritative; this quantifies tscircuit fidelity.

KiCad board: `/home/mouse9911/gits/circuits/projects/cook-loadcell/04_kicad/cook_loadcell.kicad_pcb`
- KiCad: 33 footprints, 16 named nets
- tscircuit: ~63 components, ~16 nets

NOTE: refdes/net-name conventions differ between the two front-ends; a
node-for-node parity requires a name-normalization map (see notes.md). The
count deltas above are the first-order fidelity signal.
