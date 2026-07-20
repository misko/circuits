# lipo3s-usb-hub

3S LiPo (XT60) → 3× USB-A (2.5 A) + 1× USB-C (6 A) power/charging board. Act 2
validation of the tscircuit-native pipeline (ADR-0002): authored from scratch in
`03_tscircuit/src/lipo3s_usb_hub.tsx` and built to a sealed, orderable JLCPCB release by
the one-command `tsx_to_board.sh`.

- Design: `01_docs/ARCHITECTURE.md`, `01_docs/DETAIL_DESIGN.md`, `01_docs/decisions/`
- Parts: `02_parts/<MPN>/part.yaml`   Backend: `03_src/`   Fab-of-record: `04_kicad/`
- Release: `07_releases/`

Protection (ADR-0002): 15 A fuse + LM74800 ideal-diode reverse block + HW UVLO/OV +
input & rail TVS + TPS2557 per-port limits. No firmware; safe from first power-up.
