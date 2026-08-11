# Changelog

## v0.5.0 — 2026-08-11  [tag: usb-hub-3s-v4-v0.5.0]

- Completed the routed-board checkpoint from the exact reviewed placement.
  Promoted route `r4` imports 379 segments and 10 route/seed vias, then replays
  20 named power taps and the serialized stitch/fill chain.
- Closed the authoritative KiCad gate at 0 violations, 0 unconnected items and
  0 schematic-parity findings through both the full TSX build and deterministic
  pinned-schematic rebuild.
- Added fail-closed route-race promotion, fabrication-tier-aware via screening,
  parity-safe explicit thermal vias, simple-polygon validation, fresh post-fill
  connectivity, KiCad 10 via API use and bounded TSX producer progress.
- Recorded the Stage 4 timing/failure trace plus IMP-005 through IMP-016 in the
  repository improvement ledger; the focused regression battery is 230 passed,
  0 failed and 2 intentionally skipped slow tests.

Released: no; routed design checkpoint only, deliberately DO-NOT-ORDER

## v0.4.0 — 2026-08-11  [tag: usb-hub-3s-v4-v0.4.0]

- Completed the exact unrouted placement checkpoint: 76 components on a
  deterministic 130 x 90 mm, four-layer JLC advanced board with four M3 holes
  and three global fiducials.
- Vendored manufacturer-derived connector, converter, controller, switch,
  fuse and protection footprints, including filled/capped 0.30 mm thermal-via
  fields measured from TI editable EVM layouts.
- Closed exact-board count, pin-map, overlap, outline/capacity, pad-separation,
  placement-policy and hash-bound pin/layout/render review gates.
- Recorded IMP-003/IMP-004 after cheap footprint-alias and directional/
  adjacency checks caught defects before routing.

Released: no; placement checkpoint only, deliberately DO-NOT-ORDER

## v0.1 — 2026-08-10  [tag: usb-hub-3s-v4-v0.1]

- Commissioned a fresh, fail-closed v4 project with a verbatim requirement
  record and explicit power-only/supervised-prototype boundary.
- Selected JLCPCB standard four-layer PCBA as the provisional manufacturing
  tier; no schematic, PCB, or fabrication package exists yet.

Released: no
