# 03_tscircuit — usb-hub-3s authoring source

The board authored in tscircuit TSX (`src/usb_hub_3s.tsx`): 3S LiPo XT60 in,
3x USB-A (TPS2557-limited, TPS2513 DCP) + 1x USB-C PD (IP6559-C 100W).
Circuit derivation lives in `01_docs/DETAIL_DESIGN.md`; part facts in
`02_parts/*/part.yaml`. Placement is `03_src/floorplan.yaml`
(generate_board path). S-DSL positioning: TSX compiles to native KiCad via
the shared converter; every gate runs on the native artifacts.
