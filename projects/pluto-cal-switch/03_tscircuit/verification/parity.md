# tscircuit-vs-KiCad parity — pluto-cal-switch

Compares the tscircuit render's netlist against the KiCad fab-of-record.
Canon S-DSL: KiCad stays authoritative; this quantifies tscircuit fidelity.

KiCad board: `/home/mouse9911/gits/circuits/projects/pluto-cal-switch/04_kicad/pluto_cal_switch.kicad_pcb`
- KiCad: 77 footprints, 49 named nets
- tscircuit: ~132 components, ~50 nets

NOTE: refdes/net-name conventions differ between the two front-ends; a
node-for-node parity requires a name-normalization map (see notes.md). The
count deltas above are the first-order fidelity signal.
