// cook-loadcell — tscircuit render (SCAFFOLD / placeholder)
// Fab-of-record: ../../04_kicad/cook_loadcell.kicad_pcb (~33 parts). Author this
// board node-for-node from that netlist, then `gen_tscircuit.sh` renders it and
// writes verification/parity.md. Canon S-DSL: KiCad stays authoritative.
export default () => (
  <board width="10mm" height="10mm">
    {/* TODO: author cook_loadcell from the KiCad netlist (components, nets, footprints, JLC parts) */}
  </board>
)
