# tscircuit-vs-KiCad parity — crow-recorder-central-v2

Compares the tscircuit render's netlist against the KiCad fab-of-record.
Canon S-DSL: KiCad stays authoritative; this quantifies tscircuit fidelity.

KiCad board: `/home/mouse9911/gits/circuits/projects/crow-recorder-central-v2/04_kicad/crow_recorder_central_v2.kicad_pcb`
- KiCad: 203 footprints, 116 named nets
- tscircuit: ~642 components, ~116 nets

NOTE: refdes/net-name conventions differ between the two front-ends; a
node-for-node parity requires a name-normalization map (see notes.md). The
count deltas above are the first-order fidelity signal.
