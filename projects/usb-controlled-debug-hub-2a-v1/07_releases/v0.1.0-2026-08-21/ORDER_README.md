# USB-Controlled Debug Hub 2A v1 — v0.1.0

**DO NOT ORDER YET.**

DESIGN: PASS candidate — exact local design gates are green.

BLOCKED-SOURCING: public catalogue evidence is 50/50 PASS with the adopted
quantity-five and +200-unit surplus rule, but it does not prove JLCPCB assembly
allocation. Capture an exact order-interface allocation receipt before payment.

ORDER VERDICT: DO-NOT-ORDER until every checklist item below is accepted.

This is a four-port USB 2.0 debug hub. Each USB-A port is electrically designed
for 5 V / 2 A. Full simultaneous output is 40 W; the separate USB-C power input
must negotiate a fixed 20 V / 3 A PDO. The separate USB-C data connector does
not power the board. A 15 V / 3 A source is insufficient for the full-load
contract. USB-A 2 A capability is a board power limit, not a promise that every
legacy device will negotiate a proprietary charging mode.

No custom firmware is included or required for basic hub enumeration. Control
uses the fitted MCP2221A USB bridge and MCP23017 I/O expander; host-side control
software is outside this hardware release.

## Upload files

- PCB: `fab/usb_controlled_debug_hub_2a_gerbers.zip`
- Assembly BOM: `fab/bom.csv` — 50 lines
- Placement: `fab/cpl.csv` — 179 placements, 170 top and 9 bottom
- Four exact GCT USB1130-15-A USB-A receptacles are intentionally absent from
  BOM/CPL and must be procured and hand-fitted or consigned.

## Mandatory JLC order checks

1. Select four layers and the JLC advanced process.
2. Stop until JLC's chosen material/stackup yields a documented 90-ohm USB
   differential solve for the exact release geometry.
3. Paste `fab/order_notes.txt` verbatim. Confirm 578 protected 0.46/0.20 mm
   Type-VII filled/capped vias and zero ordinary vias; do not infer this from
   native KiCad flags because Gerbers do not carry them.
4. Resolve every `fab/bom_echo_gate.txt` row and confirm code, MPN, value,
   package and designators match JLC's resolved table.
5. Inspect every `fab/rotation_human_gate.txt` single-channel part in the JLC
   viewer. Confirm polarity/pin 1, side and rotation.
6. Confirm J_DATA and J_POWER retain all SMT contacts and plated retention
   lands in the mixed SMT/THT preview.
7. Confirm J_PORT1..J_PORT4 remain absent from machine assembly.
8. Re-run order-day stock/allocation for quantity five. Public stock is advisory
   and may not authorize payment.

## First article hold

Build and energize one first article before the remainder. Current-limit the
20 V input; verify PD negotiation, 3.3 V and both 5 V banks unloaded; then test
each port at 2 A and both banks at 4 A. Measure connector/cable-end voltage,
thermal rise, current-limit behavior, USB enumeration/Hi-Speed integrity,
data-only disconnect, power+data disconnect and reverse/backfeed behavior.

Mechanical note: a consolidated STEP is absent because the installed exporter
cannot resolve every standard model alias/VRML dependency. Exact twin renders,
connector views and 183/183 model coverage are supplied in `verification/`.
