# Schematic ↔ board parity — crow-recorder-central v1.0

Gate: `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity`

MEASURED (sealed board, 2026-07-22):
- **schematic_parity items: 0** (node-for-node: every board net matches the
  exported schematic netlist; every symbol pin maps to a footprint pad on the
  same net).
- violations: 0
- unconnected: 2 — BOTH `Zone [GND] <-> Zone [GND]` fill micro-slivers,
  waived under ADR-0010 (no pad/track/via unconnected; every one of the 234
  parts' GND pads is tied to the In1/In4 planes).

Independently re-verified STANDALONE: the source/ archive (board + schematic +
fp-lib-table + vendored cac.pretty, co-located) re-measures 0 violations /
2 ADR-0010 slivers / 0 parity with no access to the project tree — the archive
stands alone (V-REL-FPLIB).

The netlist parity reference is source/crow_recorder_central.net.
