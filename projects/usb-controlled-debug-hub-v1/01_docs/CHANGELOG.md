# Changelog

## Unreleased — 2026-08-15

- Commissioned the single-cable USB 2.0 compound-hub architecture.
- Locked four independently controlled external ports plus one internal
  firmwareless management device.
- Locked the regulated 5 V self-powered envelope and hardware-safe defaults.
- Bound the hub, management bridge, expander, data switches, current switches,
  input protection, connectors, crystal, regulator magnetics and passives to
  exact manufacturer-reviewed order codes.
- Applied the USB2517I hardware checklist to reset, VBUS detection, oscillator,
  supply bypass, port disable, non-removable-port and polarity straps.
- Corrected the admitted full-load input from the initial 2.3 A estimate to
  2.6 A and qualified an exact replaceable 4 A MINI blade fuse.
- Reopened pre-route approval after independent review; added a charged USB
  bulk bank, aggregate latch-off eFuse, low-capacitance shunt ESD, and honest
  command-state interlock wording before any routing was promoted.
- Closed the second topology review by adding the eFuse input bypass,
  correcting the 2.58 A normal/251.86 uF maximum startup arithmetic, and
  extending native-model registration to SMD pad-centre datums.
- Completed exact-model placement review on the corrected 139-part population:
  clean placement DRC/parity, 139/139 model coverage, 4/4 native registration
  groups, 30/30 measurable top bodies and 9/9 bottom bodies within the
  A-RENDER tolerance.
- Approved the track-free board for differential routing through independent
  pin, layout and render lenses. Carried forward release obligations include
  reproducible pin-dossier lookup, J_PWR polarity/function silk, USB transition
  return vias, underside THT/SMT assembly preview and final debug-access review.
- Normalized two part-dossier escape styles to the canonical package-gate
  vocabulary and renewed the exact parts-hash reviews without changing board,
  netlist, PDF or electrical rules.
- Added an authenticated, non-promotable route-wave checkpoint and exercised
  the first three USB-only waves. The checkpoint exposed a KRT pair-gap versus
  foreign-clearance preflight defect in 14.895 seconds, skipped all ten pairs,
  preserved byte-identical route subjects and stopped with no `FINAL`; power
  and control routing remain untouched pending the bounded repair.
- Recast the four PESD2USB3UX protectors as direct-through shunts and completed
  deterministic connector-side USB copper with 8/8 nets connected, 0.3054 mm
  pair spread and no physical DRC finding. A subsequent transition-only run
  stopped safely in 19.329 seconds at four hub-side endpoint-order conflicts
  and one upstream shunt-chain attachment conflict; it emitted no copper or
  vias, authenticated no wave and left all later routing untouched.
- Corrected the four downstream hub-side endpoint orders using the USB2517I's
  documented per-port polarity-swap straps, with coupled strap-state and
  physical-pad invariants. The regenerated 139-part schematic passed both
  independent reviews; canonical resume rebuilt a clean placement/r0 and
  stopped as designed on stale exact-board placement receipts before routing.
- Rejected that placement after perspective/mechanical review proved all four
  USB-A mating mouths faced inward despite perfect model registration. Added a
  reusable semantic board-edge-facing assertion, rotated the receptacles to
  put their mating planes on the north edge, translated their protected data
  cells inward, and rebound the symmetric switch lanes plus hub straps to
  normal end-to-end USB polarity. Fresh schematic review is required before a
  corrected board may be generated.
