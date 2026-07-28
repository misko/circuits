# NETLIST PARITY — v1.12-2026-07-28

Three independent parity statements, by three different tools, about three
different artifact pairs.

> A note on this file's own method, because it nearly shipped a lie: the first
> version of the parser below matched `(net (code` on one line and found **0
> nets in both files**, which compared EQUAL and printed `PARITY: 0`. That is
> the `jlc_twin` exit-0 shape — a hollow pass. KiCad 10 writes `(net` and
> `(code ...)` on separate lines. The parser now ASSERTS a non-zero census in
> both inputs before it is allowed to report agreement.

## 1. Shipped netlist vs the last sealed netlist — node-for-node

This release moves COPPER and NOTHING ELECTRICAL. That claim is falsifiable, so
here it is falsified against v1.11's own sealed netlist.

Method: both `.net` files parsed independently (balanced-paren scan from each
`(net` token, `(ref, pin)` pairs collected per net) and compared as SETS — not a
byte diff, since the two files differ in header metadata (`source` path, export
`date`), none of which is electrical. KiCad's `unconnected-*` auto-names carry
fresh suffixes and are excluded from the name-set comparison (they are not signal).

```
A (v1.12 shipped) 07_releases/v1.12-2026-07-28/source/usb_hub_3s_v2.net
  122 components, 73 nets (65 named), 372 nodes
B (v1.11 sealed)  07_releases/v1.11-2026-07-27/source/usb_hub_3s_v2.net
  122 components, 73 nets (65 named), 372 nodes
component set identical: True
net NAME set identical : True
nets differing node-for-node: 0
PARITY: 0 differences
```

**PARITY: 0.** The board whose gerbers this release ships is electrically the
same board v1.11 sealed. What moved is J5's land pattern and nothing else.

## 2. Board vs board — every (refdes, pad) -> net

`board_netlist_parity.py`, a different tool reading the two `.kicad_pcb` files
through pcbnew rather than the netlist exports:

```
input: built  = 04_kicad/usb_hub_3s_v2.kicad_pcb
input: sealed = 07_releases/v1.11-2026-07-27/source/usb_hub_3s_v2.kicad_pcb
built nodes=372  sealed nodes=372
nets built=66  sealed=66
BOARD PARITY 0 -> PASS (372/372 nodes identical, net-for-net)
```

## 3. The DRC gate's own schematic-parity leg

`kicad-cli pcb drc --severity-all --refill-zones --schematic-parity`, with the
authoritative `.kicad_sch` beside the board so the parity leg actually RUNS:
**0 violations / 0 unconnected / 0 schematic-parity** (`verification/drc.json`).

It earned its keep on this release. The FIRST build came back **0/0/1** because
the corrected footprint carried a populated `Datasheet` PROPERTY, which
propagates to the board while the schematic symbol's field is empty. The
property was reverted to `""` (the datasheet reference lives in the footprint's
`descr` and in `02_parts/TYPE-C-31-M-12A/part.yaml`, neither of which is parity-
compared) and the board rebuilt. Recorded rather than quietly fixed.
