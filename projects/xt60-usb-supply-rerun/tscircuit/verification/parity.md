# tscircuit-vs-KiCad parity — xt60-usb-supply-rerun

Compares the tscircuit render's netlist against the KiCad fab-of-record.
Canon S-DSL: KiCad stays authoritative; this quantifies tscircuit fidelity.

KiCad board: `/home/mouse9911/gits/circuits/projects/xt60-usb-supply-rerun/04_kicad/xt60-usb-supply.kicad_pcb`
- KiCad: 51 footprints, 28 named nets
- tscircuit: ~114 components, ~24 nets

NOTE: refdes/net-name conventions differ between the two front-ends; a
node-for-node parity requires a name-normalization map (see notes.md). The
count deltas above are the first-order fidelity signal.

---

## Rigorous node-for-node result (scratchpad/parity.py — pcbnew vs circuit.json)

The auto-counts above are a regex heuristic; the authoritative diff maps each tscircuit pad
to its net via `circuit.json` `subcircuit_connectivity_map_key` and compares logical
`(refdes,padname)` node sets against `pcbnew`:

- components: **51 / 51** matched (refdes-for-refdes)
- named nets: **28 / 28** matched (after `5V_A→N5V_A`, `5V_C→N5V_C`)
- per-net node sets `{net → {refdes.pad}}`: **28 / 28** matched
- total logical nodes: **151 / 151**
- **NODE-FOR-NODE PARITY: YES**

See `notes.md` for the normalization map, the footprinter connector-gap findings (11 hand
`<footprint>` land patterns), ERC (635) and PCB DRC (217+118) classification.
