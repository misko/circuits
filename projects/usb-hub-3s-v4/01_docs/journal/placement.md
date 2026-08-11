# Placement journal

## 2026-08-11 08:52 — start

- did: Entered Stage 3 from the pushed v0.3.0 schematic checkpoint and began reconciling all 76 footprints against the generic board backend and manufacturer layout cells.
- result: MEASURED the placement source is still intentionally blocked (`board.outline: null`, zero anchors/seeds), so no pre-decision PCB artifact can be mistaken for current evidence. The schematic review remains SOUND and explicitly DO-NOT-ORDER.
- next: Fix the smallest thermally credible four-layer outline, add filled/capped-via process intent, vendor exact custom footprints, and place the input, dual-module, three USB-A and Type-C cells before running placement gates.

## 2026-08-11 09:51 — complete and paused

- did: Authored a deterministic 130 x 90 mm four-layer placement for all 76
  components, four M3 holes and three non-collinear fiducials. Vendored exact
  manufacturer lands for the GCT connectors and TI packages, including the
  TPSM63610/TPSM63604 thermal fields measured from TI's editable EVM files.
  Declared 1.2 mm ENIG JLC advanced fabrication with 0.30 mm filled/capped
  exposed-land vias and two uninterrupted internal GND planes. No track was
  routed.
- result: MEASURED board `a8404ae41e79...` passes 76/76 count parity,
  P-PINMAP over 160 declared physical identities, 18/18 pad-net assertions,
  zero inter-footprint copper overlaps or anchored courtyard overlaps,
  placement gates with zero failures/warnings, P-PADSEP over 335 pads at the
  0.09 mm advanced-tier floor, the no-USB-data critical-route contract and all
  three applicable placement policy rows. Exact pin/layout/render/A-RENDER
  reviews are SOUND and remain DO-NOT-ORDER.
- spent: MEASURED wall clock 59 minutes from the 08:52 stage marker. Board
  generation took 1.5-2.6 seconds per attempt, the complete placement battery
  took about 3 seconds, and each high-quality render took 10-11 seconds. The
  remaining time was engineering work: importing/measuring official EVM lands,
  reconciling frozen footprint names, checking physical pad coordinates and
  iterating the placement. There was no long-running silent producer.
- backtracks: The first producer attempt failed in 0.3 seconds on the frozen
  `SOT-9X3` alias and was fixed by vendoring KiCad's exact `Texas_DRT-3` land
  under the frozen name. The first legal render then exposed an over-spread
  lower converter/controller cell. A physical-pad report also disproved the
  authored `rot270` VIN/VOUT comment, and a later adjacency pass found BOOT,
  RT and feedback parts legally non-overlapping but too remote. All were fixed
  before routing; collision experiments failed loudly in under three seconds.
- human render: The final top view is readily attributable by functional cell
  and the fixed caption `POWER ONLY — NO USB DATA` is prominent. The generic
  silk placer reports conservative ownership degradations for U1 and U2
  because correct pin-local passives surround both modules; the visible labels
  remain unambiguous and exact copies exist on F.Fab. Most custom footprints
  lack 3D bodies, so the render review credits only pad/courtyard/edge/silk
  geometry and retains JLC preview checks for body registration.
- generalized: Promote `layout:` evidence into dossiers before placement;
  pre-resolve all frozen footprint aliases; emit actual directional pad sides
  and structured pad-to-pad adjacency distances; keep human render review as a
  separate lens because “legal geometry” does not imply a good switch loop.
  IMP-003 and IMP-004 record the two new repository-wide candidates.
- next: PAUSE. Routing has not started. On approval, enter Stage 4 with the
  hash-bound placement fixed; run the cheap rule/escape/tier preflights first,
  then route power paths, quiet feedback/reference nets and Type-C CC paths.
