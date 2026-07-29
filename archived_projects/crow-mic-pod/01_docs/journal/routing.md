# journal — routing

## 2026-07-21 21:06 — start
- did: full rebuild chain with archive-imported sources (ADR-0005); import of archive-promoted 03_src/route/r3.kicad_pcb
- result: RED — DRC 41 violations / 12 unconnected / 0 parity, all clustered at J1 (RJ45) + L1. Forensics: archived SEALED board passes 0/0 with today's kicad-cli; placement diff sealed-vs-mine = IDENTICAL; track diff = only ~110/400 common; r3 contains MY board's clashing segments, sealed board's segments absent from r3.
- next: conclusion — archive's promoted r3 is STALE (pre "J1 rot-90 fix", commit a121ca9); the sealed v1.1 final route was never re-promoted (canon M3/3g violation IN THE ARCHIVE). Do NOT import the stale chain; re-route with KRT against the verified placement and promote THIS project's own chain.

## 2026-07-21 21:07 — finish
- did: fresh KRT re-route (3 waves per route_waves.sh: power 0.5 / beeper 0.6 / audio 0.3), import, stitch (23 neck bridges), rules LAST, DRC gate
- result: GREEN — waves 11/11 single + 43/43 multipoint pads, 0 failed; DRC severity-all --refill-zones --schematic-parity = 0 violations / 0 unconnected / 0 parity; audit PASS x2; ERC 0. Route promoted to 03_src/route/r3.kicad_pcb
- next: verification stage (bom/stock/twin/pin/render/policy) then release
