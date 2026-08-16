# Placement checkpoint — 2026-08-16

## Outcome

The track-free four-layer board is ready for placement review, not routing or
fabrication. All 133 schematic parts are anchored; four USB-A receptacles form
the north-edge port bank, the upstream USB-B and protected 5 V input occupy
separate edges, and the hub/management/power cells remain visually distinct.
Five USBLC6 arrays and four FSUSB42 switches are deliberately on B.Cu beneath
their connector/data cells. No firmware was generated.

Measured checkpoint:

- generator: 133/133 anchored, 9 B.Cu, 18 source-bound exact model overrides,
  zero inter-footprint copper overlaps and zero same-side courtyard overlaps;
- placement policy: 5/5 checks and all 38/38 declared adjacency budgets pass;
- placement geometry: P-OUT/P-CAP/P-BODYCLR pass, including one evidence-bound
  USB-B mating-edge courtyard exception while every drilled/copper land stays
  on board;
- identity: P-PINMAP passes 293 declared physical identities over 27 multi-pin
  references; S-COUNT is 133/133 in board, circuit JSON, KiCad schematic,
  manifest and netlist;
- models: P-MODEL passes 133/133 fitted footprints; P-MODEL-REG passes the
  USB-A, USB-B and power-terminal tuples with 32/32 drilled attachment centres;
- pad geometry: 576 copper pads, 129168 inter-footprint pad pairs and 205535
  paste-to-foreign-copper pairs pass the current overlap/touch screen.

## Where the stage spent time

The largest effort was not moving parts. It was making the placement evidence
tell the truth:

1. the generic floorplan needed a first-class top/bottom-side declaration so
   ESD and data-switch paths could be short without top-side body collisions;
2. adjacency rules needed optional net scoping so the D+/D- clamp path was not
   graded through an unrelated shared VBUS reference branch;
3. exact connector STEP files needed explicit source-owned transforms and
   manufacturer-derived F.Fab/courtyard envelopes;
4. native connector models are multipart, so nearest-component pixel
   extraction measured one shell edge instead of the whole body;
5. a raw headless render lacked `KICAD10_3DMODEL_DIR`, exited zero, and omitted
   every stock KiCad package body despite P-MODEL resolving those files;
6. tscircuit's private `pin5_internal_1` identity for a repeated shell pad had
   to be normalized to physical pin 5 before pin-map comparison.

Each class was corrected in the shared pipeline and regression-tested before
the board was accepted. The resulting general changes are IMP-107 through
IMP-112 in `improvements.md`.

## What generalized well

- Exact native CAD before routing paid off. It caught a translated terminal,
  a too-small upstream-connector courtyard and incomplete render evidence while
  placement changes were still cheap.
- Electrical-path-specific adjacency is more faithful than whole-net-pair
  distance for ESD/filter devices that also share power or ground.
- Bottom-side placement should be an explicit authored property, not a
  per-board pcbnew postprocessor.
- Durable reports must list every finding; console truncation is acceptable,
  report truncation creates serial repair loops.
- Model-path coverage, XY registration, vertical/side-view registration and
  final pixels remain distinct claims. Passing one must never stand in for the
  others.

## Before routing

Placement approval still requires the exact-board pin/layout/render/A-RENDER
review receipts. Route preparation must replace the inherited example
`route.yaml`, declare every upstream/internal/downstream USB pair, select the
JLC advanced four-layer process and solve/lock the 90-ohm differential geometry
against the provisional stackup. Pre-route DRC and critical-pair inventory must
then pass. The first routing wave will contain USB data pairs only; power and
control follow after their geometry is preserved.
