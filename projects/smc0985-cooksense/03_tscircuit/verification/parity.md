# tscircuit-vs-KiCad parity — smc0985-cooksense

Compares the tscircuit render's netlist against the KiCad fab-of-record.
Canon S-DSL: KiCad stays authoritative; this quantifies tscircuit fidelity.

KiCad board: `/home/mouse9911/gits/circuits/projects/smc0985-cooksense/04_kicad/cooksense.kicad_pcb`
- KiCad: 219 footprints, 160 named nets
- tscircuit: ~329 components, ~160 nets

NOTE: refdes/net-name conventions differ between the two front-ends; a
node-for-node parity requires a name-normalization map (see notes.md). The
count deltas above are the first-order fidelity signal.
