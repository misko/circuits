# lipo3s-usb-hub / tscircuit — TSX authoring front-end (ADR-0002 Act 2)

The **authoring source of record** for this board: a 3S LiPo → 3× USB-A (2.5A) +
USB-C (6A) power hub, authored from scratch in tscircuit/TSX and driven through the
converter + KiCad backend to DRC 0/0/0 by the ONE command `tsx_to_board.sh`.

- `src/lipo3s_usb_hub.tsx` — the whole board (96 parts, 56 nets); one parameterized
  `buckStage` composed 2×, one `.map` over the 3 USB-A channels; specialty connectors
  as `<footprint>` children carrying exact KiCad pad-name portHints + JLC codes.
- `sealed_ref.txt` — board-parity reference (the sealed usb-power-3s prior art; the
  independent design converges node-for-node, so parity 0 certifies completeness).
- no `net_aliases.txt` needed — the N-guard convention (N5V_A→5V_A, N5V_C→5V_C) covers
  the only leading-digit rails.

Canon S-DSL / ADR-0001/0002: KiCad `.kicad_pcb` + the gate stack are the fab-of-record;
TSX authors the schematic; ERC / rules / routing / DRC / twin / policy / release all run
on native KiCad artifacts. The `<footprint>` child geometry is a placeholder for
tscircuit's own render only — pad NAMES and nets are load-bearing.
