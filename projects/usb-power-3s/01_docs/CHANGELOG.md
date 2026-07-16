# Changelog — usb-power-3s

## v1.0 — 2026-07-16
- Full design from scratch: architecture + math docs, 5 ADRs, 38-line BOM
  (41 02_parts/ entries), generated schematic (96 components, 68 nets),
  100×60 mm 4-layer board, KRT-routed + scripted power stitching.
- Gate: DRC 0 violations / 0 unconnected / 0 parity issues
  (`--severity-all --refill-zones --schematic-parity`), placement audit PASS,
  polarity audit PASS, JLC stock check PASS (37 coded lines in stock).
- Fixed during bring-up: D2/D3 rail TVS were mapped to a SOT-23-6 ESD-array
  footprint (copy-paste from a previous project) — now D_SMB.
Released: yes — 07_releases/v1.0-2026-07-16/
