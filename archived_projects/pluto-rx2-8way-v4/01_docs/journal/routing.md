# Routing journal

## 2026-07-31 19:38 — start
- did: Prepared a track-free v4 board and launched a three-candidate, five-wave route race through the shared routing backend.
- result: RF, RF-tap, power, control, and status groups were routed independently from fresh v4 placement.
- next: Compare candidates by routed-net unconnected count, then copper violations, then candidate index.

## 2026-07-31 20:47 — finish
- did: Measured all candidates and promoted candidate c0 as 03_src/route/r5.kicad_pcb.
- result: c0, c1, and c2 each measured CLEAN with 0 unconnected items and 0 copper violations; the promoted file SHA-256 is 0d97998bc431f1152fa422e2627418170854b0ead37540317794150139c5e47f.
- next: Import the immutable promoted chain, then run deterministic ground stitching and fill.

## 2026-07-31 21:02 — iterate 1
- did: Rejected one carried route-dependent fence coordinate because exact collision checking found fresh v4 copper at (41.560, 58.150), then rebuilt from the promoted chain.
- result: seed_stubs served 31 pins with 35 primitives and 0 refusals; stitch gate clean; 3,367 grid vias and 6 filled zones generated.
- next: Run final DRC, RF-length audit, policy audit, and the layout seal.
