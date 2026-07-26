# NETLIST PARITY — v1.5-2026-07-25

Node-for-node comparison between the netlist exported from the sealed board's
schematic on 2026-07-25 and the netlist shipped in sealed v1.4-2026-07-23
(`source/usb_hub_3s_v2.net`, which v1.5 ships VERBATIM — sha256-identical).

Method: both files parsed independently (balanced-paren scan for each
`(net ...)` block, ref/pin pairs collected per net) and compared as sets.
This is NOT a byte diff — the two files differ in their header metadata
(`source` path and export `date`) and in sheet-name properties, none of
which is electrical.

```
A 07_releases/v1.4-2026-07-23/source/usb_hub_3s_v2.net
  110 components, 67 nets, 347 nodes
B 06_build/verification/parity_v15.net
  110 components, 67 nets, 347 nodes
component set identical: True
net NAME set identical : True
nets differing node-for-node: 0
PARITY: 0 differences
```

**PARITY: 0.** The board v1.5's CPL was generated from is electrically the
same board v1.4 sealed — which is the premise of the whole release.

Separately, `kicad-cli pcb drc --schematic-parity` reports **0 schematic
parity issues** against the same board (verification/drc.json), an
independent check by a different tool.
