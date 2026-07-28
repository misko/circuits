# Netlist parity — interposer v1.1 (node-for-node, against THIS release's bytes)

    kicad_sch_parity.py interposer source/interposer.net source/interposer.kicad_pcb

Both inputs are the SHIPPED files in this archive (canon M-SHIP), not a
`06_build` reconstruction.

    converter nets = 10      kicad nets = 10
    connected nodes: netlist 50 / board 50
    no-connects:     netlist  0 / board  1

## Verdict: 50/50 CONNECTED NODES AGREE. One documented no-connect difference.

The tool prints `REAL DISCREPANCIES: 1/10 nets -> FAIL` for a single item, and
canon says give the node-level diff rather than a headline:

    NO-CONNECT DIFF: only_converter = []
                     only_kicad     = [('J_KEY_MATRIX', 'MP')]

`MP` is the JST-GH footprint's pair of MECHANICAL SOLDER TABS, carried on one
pad node. It is not authored in `interposer.tsx` (the tscircuit pinrow token
models only the numbered signal pads — `03_tscircuit/parity_padmap.txt`
records that for the whole GH family), so the netlist has nothing to say about
it; on the BOARD it exists as copper and is in NO NET.

**On this board that is the specification, not a gap.** The main board bonds
its GH `MP` tabs to `GND_ISO`. Board C has no `GND_ISO`, no `GND`, and no
chassis net at all — BRIEF sections 4/5/7 and ADR-0009 make the whole keypad
domain float — so there is nothing to bond the tabs to and bonding them would
be the defect. `03_src/interposer/audit_board.py` asserts exactly this and
passes, and `verification/audit.txt` records it.

## The 10 nets, enumerated from the SHIPPED board (5 nodes each, 50 total)

| net | nodes |
|---|---|
| KP_U1 | J_MEMBRANE.1  J_CN1_JUMPER.1  J_KEY_MATRIX.1  TP_M_U1.1  TP_C_U1.1 |
| KP_U2 | J_MEMBRANE.2  J_CN1_JUMPER.2  J_KEY_MATRIX.2  TP_M_U2.1  TP_C_U2.1 |
| KP_U3 | J_MEMBRANE.3  J_CN1_JUMPER.3  J_KEY_MATRIX.3  TP_M_U3.1  TP_C_U3.1 |
| KP_U4 | J_MEMBRANE.4  J_CN1_JUMPER.4  J_KEY_MATRIX.4  TP_M_U4.1  TP_C_U4.1 |
| KP_U5 | J_MEMBRANE.5  J_CN1_JUMPER.5  J_KEY_MATRIX.5  TP_M_U5.1  TP_C_U5.1 |
| KP_U6 | J_MEMBRANE.6  J_CN1_JUMPER.6  J_KEY_MATRIX.6  TP_M_U6.1  TP_C_U6.1 |
| KP_D1 | J_MEMBRANE.7  J_CN1_JUMPER.7  J_KEY_MATRIX.7  TP_M_D1.1  TP_C_D1.1 |
| KP_D2 | J_MEMBRANE.8  J_CN1_JUMPER.8  J_KEY_MATRIX.8  TP_M_D2.1  TP_C_D2.1 |
| KP_D3 | J_MEMBRANE.9  J_CN1_JUMPER.9  J_KEY_MATRIX.9  TP_M_D3.1  TP_C_D3.1 |
| KP_D4 | J_MEMBRANE.10 J_CN1_JUMPER.10 J_KEY_MATRIX.10 TP_M_D4.1  TP_C_D4.1 |

Pad k of all three connectors is on the same net for every k in 1..10 — the
straight-through claim graded pad-for-pad, not sampled.

Everything with NO net, enumerated (8 pads): `H1 H2 H3 H4` (the four M2.5
mounting holes, `np_thru_hole`), `J_MEMBRANE` + `J_CN1_JUMPER`'s polarization
bosses (NPTH), and `J_KEY_MATRIX.MP` x2. There is no other copper on the
board: the net set is EXACTLY the ten `KP_*` nets, and there are 0 zones.

## Provenance of the netlist itself

`source/interposer.net` was re-exported for this release by
`kicad-cli sch export netlist --format kicadsexpr` from
`03_tscircuit/kicad/interposer.kicad_sch` (the converter's pinned artifact,
unchanged since v1.0). Against v1.0's sealed netlist it differs on exactly ONE
line — the `(source "...")` header, which records the absolute path of the
working tree it was exported from (this respin ran in a git worktree). Every
`(comp)`, `(net)` and `(node)` line is identical. Measured with a normalized
diff that suppresses only `(date`, `(tool` and that one path line: 0 remaining
differences.
