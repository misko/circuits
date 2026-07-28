# NETLIST PARITY — v1.9-2026-07-27

Two independent parity statements, by two different tools, about two different
artifact pairs.

## 1. Shipped netlist vs the last sealed netlist — node-for-node

The point of this release is that the COPPER changed and NOTHING ELSE did. That
claim is falsifiable, so here it is falsified against v1.8's own sealed netlist.

Method: both `.net` files parsed independently (balanced-paren scan for each
`(net ...)` block, `(ref, pin)` pairs collected per net) and compared as SETS.
Not a byte diff — the two files differ in header metadata (`source` path,
export `date`) and sheet-name properties, none of which is electrical.

```
A (v1.9 shipped) 07_releases/v1.9-2026-07-27/source/usb_hub_3s_v2.net
  122 components, 73 nets, 372 nodes
B (v1.8 sealed)  07_releases/v1.8-2026-07-26/source/usb_hub_3s_v2.net
  122 components, 73 nets, 372 nodes
component set identical: True
net NAME set identical : True
nets differing node-for-node: 0
PARITY: 0 differences
```

**PARITY: 0.** The board whose gerbers this release ships is electrically the
same board v1.8 sealed. Corroborated independently by `fab/cpl.csv`, which is
BYTE-IDENTICAL to v1.8's (`diff` clean, 119 rows): placement did not move
either. What moved is 44287.91 mm2 of copper pour, from absent to present.

## 2. Board vs schematic — kicad-cli, a different tool entirely

`kicad-cli pcb drc --severity-all --refill-zones --schematic-parity` on the
sealed board with the authoritative `.kicad_sch` beside it:

```
Found 0 violations
Found 0 unconnected items
Found 0 schematic parity issues
```

**DRC 0 / 0 / 0** (`verification/drc.json`). The schematic-parity leg is the
independent check: it walks the board's netlist against the schematic's, by a
code path that shares nothing with the parser above (canon M1).

## 3. Declared intent vs generated artifacts — S-COUNT, 4-way

`count_parity.py` compares the AUTHOR'S declared part list
(`03_tscircuit/manifest.yaml`) against all four generated artifacts:

```
ok   board == manifest (122 components)
ok   circuit.json == manifest (122 components)
ok   kicad_sch == manifest (122 components)
ok   netlist == manifest (122 components)
```

This FAILED 4x before this release. The board, circuit.json, kicad_sch and
netlist all agreed at 122; only the declared-intent file lagged at 110, because
the v1.6 status-LED cell was never added to it. Twelve refs were missing —
`Q8, R37, R38, R39, R40, R41, R42, D8, D9, D10, D11, D12`.

**Note for future audits: `count_parity.py` prints `extra[:8]`. Its message
TRUNCATES at eight refdes.** The 2026-07-27 audit that raised this read the
printed list and reported "8 refs missing"; the real gap was 12. Diff the sets,
do not count the printed list.
