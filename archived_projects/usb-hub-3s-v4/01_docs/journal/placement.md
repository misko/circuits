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

## 2026-08-11 21:45 — iterate 2 (post-architecture backtrack)

- did: Regenerated the enlarged 88-part topology, tightened U1/U2 output-bank
  placement, rotated the U9 aggregate breaker for left-to-right raw/protected
  power flow, moved its ILIM/timer/DVDT support local, and added 48 explicit
  thermal vias across eight footprints including split U9 input/GND lands and
  the C23 cold-socket return.
- result: MEASURED generation completes in about 3.3 seconds with 88 anchored
  footprints, 346 copper pads, 30/30 authored asserts, zero pad overlap and
  zero anchored courtyard overlap. P-PINMAP covers 192 identities; placement
  and pad-separation gates are green. Exact KiCad pre-route DRC reports seven
  `isolated_copper` preliminary islands, 123 unrouted connections, zero parity
  findings and no short/clearance/hole/library defect.
- backtrack: The first exact pin lens found U9's assigned thermal vias on the
  wrong split lands. The generic footprint-local transform had the wrong
  KiCad rotation handedness; identical all-GND fields on U1/U2 had hidden the
  same coordinate permutation. The old placement battery did not run exact
  refilled KiCad DRC, so a human lens was first detector.
- generalized: explicit via geometry needs two ownership checks at generation:
  centre inside the declared owner pad and copper shape clear of every
  different-net pad. Full-severity refill/parity DRC belongs before human
  placement review, allowing only its fixed preliminary-island class. The
  repair and general gate are tracked as IMP-030.
- next: replay the provenance-bound schematic stage after the driver change,
  then render and commission fresh pin/layout/render reviews on the final
  regenerated placement hash. Routing remains stopped.

## 2026-08-11 23:12 — corrected placement complete and paused

- did: Closed the final integrated-review findings on exact board
  `68f00d562f1d...`. J5 moved 0.325 mm so GCT's `PCB Edge` datum is exactly
  y=110.000; strict courtyard checking is now project-default with the one
  documented 0.505 mm J5 mating-envelope exception. U9's ILIM/ITIMER/dVdt
  support moved outward to 2.033/2.380/1.425 mm pad spans. A 1.30 x 0.50 mm
  scoped area permits only U9.16's 0.30 x 0.80 mm same-net bridge into IN
  PowerPAD25; source correctly calls it the fourth Power Input and retains
  current-sharing/resistance/thermal verification.
- result: MEASURED 88/88 count parity, 192 P-PINMAP identities, 346-pad
  separation, 30/30 generator assertions, zero pad/courtyard collisions and
  configured strict placement gates all pass. Exact refill reports seven
  allowed preliminary `isolated_copper`, 123 unrouted and zero parity; P-LAND
  passes 105/105. Fresh pin/layout/render/A-RENDER witnesses are SOUND and
  hash-bound. The board remains DO-NOT-ORDER and unrouted.
- proof before routing: a disposable deterministic tap run emitted all 24/24
  taps including U9.16. A focused one-bridge reviewer fixture reduced 123 to
  122 opens with no new width/clearance class. Running the whole tap set before
  stitch exposed the already-expected U1 duplicate-via/hole and one dangling
  U2 plane-via condition, showing why tap success is not a final DRC verdict;
  the configured stitch/heal pipeline owns those later-stage repairs.
- spent: MEASURED correction loop machine work was seconds: 4.5 s checkpoint
  resume, 8.7 s full placement battery, 5.0 s DRC/P-LAND recheck, 9.7/9.0 s
  renders and 5.2 s disposable tap proof. Most elapsed time was independent
  human evidence over U9 current geometry and the GCT edge datum. All reviews
  were explicitly time-boxed; one earlier unbounded lens was discarded.
- generalized: a completed reviewed stage must promote its deterministic pin
  at that boundary, not only after final PCB DRC; IMP-032 fixes both templates.
  Layout-only config should not invalidate electrical/readability witnesses
  (IMP-016). Edge-connector P-OUT exceptions need structured, measured evidence
  (IMP-033). Package terminology must follow the manufacturer table: a narrow
  power pin is not automatically “auxiliary” or current-free.
- next: PAUSE. The corrected placement is SOUND for routing. On continuation,
  run the canonical checkpoint/review preflight, tier/escape preflights, then
  route signals and deterministic power taps before stitch/fill/complete DRC.

## 2026-08-12 05:20 — exact placement regenerated and independently closed

- did: Resumed from the byte-identical seven-file schematic checkpoint without
  rerunning TSX. Regenerated the exact 88-part placement, ran physical-pin,
  collision, body, pad-separation, policy, refill/parity DRC, escape and JLC
  advanced-tier gates, prepared the deterministic r0, regenerated bounded top
  and isometric renders, and commissioned fresh pin, layout and render lenses.
- result: Checkpoint 7/7 and schematic reviews 2/2 passed. Placement has 88
  anchored parts, 30/30 assertions, zero pad/courtyard collisions, 192 graded
  physical identities and placement/tier gates at zero fail/warn. Exact DRC is
  seven allowed preliminary isolated-copper findings, 118 expected unrouted
  connections and zero parity findings. Prep preserved 48 protected source
  vias and added 12 seed segments plus 16 ordinary vias in 7.261 s. Exact
  board `e0c6e592f506...` passes all four current review witnesses and remains
  DO-NOT-ORDER.
- spent: Machine work remained bounded: placement generation/gates completed
  in roughly thirteen seconds after checkpoint verification; route prep took
  7.261 s; top and isometric renders took 13.094 s and 12.954 s. Independent
  human review dominated elapsed time. One pin-review attempt widened scope
  after its evidence was sufficient and produced no witness; it was discarded.
  A six-item replacement brief closed 192/192 identities promptly.
- friction: Repeated pcbnew enum assertions, image-handler messages and ten
  conservative silk-ownership advisories obscured the stage signal. A layout
  reviewer also initially quoted an older 123-open DRC count; the exact current
  118-open artifact was required before the witness could close.
- generalized: Keep immutable inputs while reviews run; bind every conclusion
  to exact artifact hashes; distinguish machine duration from human evidence
  time; time-box review scope as well as subprocesses; discard incomplete
  reviews; and summarize known diagnostic classes live while retaining the
  full stream. IMP-014 and IMP-049 record the generic work.
- next: Replay promoted r8 through strict import, deterministic taps and
  stitch/refill; require via-ampacity/process evidence and authoritative DRC
  0/0/0 before any routed-board release review.
