# Status

- Stage: layout sealed from fresh source on 2026-07-31.
- Board identity: `pluto_rx2_8way_v4`.
- Architecture: PE42482A-X radial RF star plus Waveshare RP2040-Zero module.
- Fab target: `jlc_4layer_advanced`, controlled impedance.
- Assembly posture: carrier assembled by JLC; RP2040-Zero user-fitted; SMA
  plug-in process must be confirmed at order time.
- Routing: promoted three-candidate winner; every candidate was clean before
  stitching. Deterministic rebuild and final DRC are 0/0/0.
- Verification: P-MOD 1/1, TSX-PRE 6/6, S-COUNT 28/28 across artifacts,
  E-INV 20/20, P-LAND 0 failures, policy audit 0 failures, and R-LEN pass with
  0.1657 mm realized eight-arm spread and no RF vias.
- Current blockers: none for layout. Firmware, fabrication sealing, assembly,
  and measured RF characterization remain.
- Release: no.
