# ADR-0002 — high-current copper strategy + layer count

Status: accepted 2026-07-18

## Context

60 A continuous trunk, six 30 A port paths. This is the board's crux.
Options considered: (a) 2-layer 2 oz with paired pours, (b) 4-layer,
(c) exposed-copper + solder bulking, (d) heavy-copper (4 oz) service.

## Decision: 2-layer, 2 oz outer, paired pours (a)

Ampacity math in DETAIL_DESIGN §1 (IPC-2221 external, ΔT ≤ 30 °C):
- Trunk 60 A needs 22 mm of single 2 oz; built as 16.5 mm F.Cu +
  16.5 mm B.Cu paired pours = 1.50× margin. The layers are bonded by
  the input-stud barrel and 24 fuse-holder THT pins — real 30 A-class
  joints, not via farms.
- Port 30 A needs 8.5 mm; built as a 10.5 mm F.Cu pour (1.24× width
  margin, ΔT ≈ 21 °C) — single-layer on purpose, so B.Cu under the
  slices stays available for the GND plane and the I2C corridor
  (the sense electronics need SOME routable layer on a 2L board).

## Rejected

- **4-layer (b)**: JLC 4L standard stackups put 0.5–1 oz on inner
  layers — they add almost no ampacity where we need it, double the
  fab cost, and the signal load (one I2C bus + SPI + USB) nowhere near
  justifies extra routing layers. Escalation path if a future rev adds
  load: 4L with 2 oz outer keeps this floorplan valid.
- **Exposed copper + solder bulk (c)**: rejected for safety — this is
  a live 12–24 V bar that humans touch with metal tools while powered
  (fuse swaps). Solder-mask stays over all power copper; margins are
  met in copper alone. Also removes an uncontrolled variable (solder
  thickness is not a spec'd quantity).
- **4 oz heavy copper (d)**: JLC prices 2L 4 oz at a multiple of 2L
  2 oz and it forces coarser track/space than the 0.5 mm-pitch INA238
  and module fanout tolerate. 2 oz meets the numbers with margin.

## Enforcement (canon R1/R2)

- Netclasses TRUNK/PORT carry 3.0 mm minimum-width `.kicad_dru` floors
  BEFORE routing — any accidental thin power track is a hard DRC fail.
  Power connectivity is pour-only (priority over GND), thermal relief
  NONE (solid) on every power zone.
- Kelvin taps are the sanctioned sub-floor exception: named `KELVIN`
  rule areas at each shunt scope the floor down to 0.30 mm (the
  exemption lives ON the board, canon R1).
- JLC 2 oz capability floors: 0.254 mm min track/space → Default class
  0.30 mm track / 0.30 mm clearance; vias 0.6/0.3.
