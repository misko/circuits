# parity — node-for-node netlist parity evidence (generated 2026-07-26 at seal)

## 1. Archive board vs tracked 04_kicad board (board_netlist_parity.py)
built nodes=78  sealed nodes=78
nets built=18  sealed=18
BOARD PARITY 0 -> PASS (78 nodes identical, net-for-net)

## 2. Board vs schematic (kicad-cli DRC --schematic-parity, full severity)
verification/drc.json: 0 violations / 0 unconnected / 0 schematic-parity issues
(run 2026-07-26 on source/crow_mic_pod_v2.kicad_pcb loaded in place with its .kicad_pro)

## 3. Netlist reference
source/crow_mic_pod_v2.net is the exported parity reference shipped with the archive.
