# Changelog

One entry per REVISION (a design state, git-tagged). Reverse-chronological.
`Released:` is `no`, or the name of the `07_releases/` directory that shipped it
— it is the only link between a revision and a fab order.

Most revisions never ship. That is normal: a board can go v4.4 → v4.10 in a
day and fab exactly one of them.

## v0.0 — 2026-08-13  [untagged checkpoint]
- Accepted D13 and backtracked before routing: replaced five loose SWD pads
  with exact keyed Samtec FTSH-105-01-L-DV-K-P-TR / JLC C2932107 header J11,
  using the standard Cortex/MIPI10 target pinout and preserving target-only
  USB-C power.
- Rechecked the suspicious SMA render against the exact Amphenol drawing. The
  five-hole copper and all nine edge anchors were correct; replacing only the
  misregistered converted WRL with its native STEP restores correct body-to-
  hole alignment in render evidence.
- Accepted the clean-room one-of-eight SP8T, autonomous dwell controller and
  independent power-only USB-C architectures.
- Selected 13 exact BOM codes and closed their source, package, pin, power,
  protection and JLC evidence before schematic generation.
- Replaced the initial slow timing with generated `fast20-v1`: unique
  20–50 ms antenna dwells, 5 ms guards, 80 ms marker and a 386 ms cycle.
- Selected direct Raspberry Pi GPIO SWD through the keyed Cortex J11 header as
  the normal profile-update path, retaining ST-LINK compatibility as a
  fallback and prohibiting programmer power into target VTref.
- Generated and hash-bound the clean-room four-page, 29-component schematic;
  manifest/Circuit JSON/KiCad/netlist agree 29/29, 131/131 source pin mappings
  and 32/32 electrical invariants pass, ERC has zero errors, and independent RF
  schematic review passes all four exact-artifact-bound requirements.
- Rejected the first otherwise-green human PDF for incorrect unused-STM32 pin
  function labels, corrected it against DS13866 and regenerated the complete
  checkpoint before signing the topology/readability reviews.
- Rejected a 10-V protected-input capacitor after clamp coordination and
  replaced it with the exact 16-V code.
- Selected the JLC04161H-7628 four-layer basis; exact RF geometry remains
  intentionally pending the official calculator at PCB stage.
- Promoted all nine Amphenol RF 901-143-6RFX female right-angle THT SMA
  connectors from provisional D9 to user-confirmed D12.
- Rejected the stale 901-40129 drawing association before footprint generation;
  retained and hash-bound exact drawing SMA6252A2-3GT50G-50 Rev C plus
  PCN-031726, and corrected the ground-hole requirement from 1.52 to 1.70 mm.
- Solved the JLC04161H-7628 coated CPWG source geometry with JLC's live
  calculator: 0.295-mm width, 0.200-mm ground gap, 49.9719-ohm result; retained
  the exact model inputs and the live-versus-written mask-parameter discrepancy.
- Closed a discovered project-slug versus board-stem mismatch in all three RF
  artifact contracts before advancing the stage.
- Authored exact manufacturer lands for the Amphenol SMA, pSemi QFN and GCT
  USB-C connector, retaining fresh exact-code JLC CAD as an independent
  assembly comparator and explicitly recording every dimensional delta.
- Commissioned a 100 x 100 mm four-layer unrouted placement with nine outward
  right-angle SMAs in the PE42482's cyclic package order, four M3 torque
  points, three fiducials and an exact south-edge power-only USB-C datum.
- Justified the advanced JLC option solely by the nine filled/capped 0.45/0.20
  mm RF-ground vias in U1's exposed pad; ordinary routing does not depend on
  advanced-width traces or small vias.
- Closed the first placement grind before routing: exact-package clearance,
  SMA silk, numeric-to-alphanumeric USB pin identity, keyed J11 pin identity
  and explicit zero critical-pair denominator. Current placement DRC is 0
  violations / 39 expected unrouted items / 0 parity findings; P-OUT, P-CAP,
  P-BODYCLR, P-PADSEP and 127-identity P-PINMAP all pass.
- Rejected the first apparently successful final render because the USB-C
  body was absent under an unresolved headless KiCad model token; vendored and
  hash-bound the exact GCT STEP model, then regenerated the board, gates and
  complete top/oblique/edge evidence before pausing for review.
- Rejected the first SMA visual evidence because a converted JLC WRL body was
  offset from the exact Amphenol five-hole footprint. The native exact-code
  STEP aligns all nine bodies, legs and edge mating datums; J11's exact body is
  also present in the regenerated top/oblique/edge evidence.
- Closed the remaining modeled-placement population gap before routing: pinned
  the eight official KiCad 10.0.4 package-model files used by 17 R/C/U/D/F
  references into project source with upstream licence and SHA-256 provenance,
  regenerated without geometry movement, and promoted complete D14 top,
  oblique and edge renders. The new independent P-MODEL gate passes 29/29 and
  is wired into canonical full and reuse rebuilds with a red fixture.
- Stopped before route preparation when tier preflight exposed a 0.09-mm
  router-clearance setting below the applicable 0.20-mm DRC floor and a
  0.15-mm drill at 1.6-mm thickness above the declared 10:1 PTH aspect limit.
- Corrected those source-known route constraints before copper: every wave now
  inherits 0.20-mm clearance and 0.45/0.20-mm ordinary vias, while the
  legalizer reserves the actual 0.58-mm drill-plus-hole-clearance pocket.
  R-PREFLIGHT is 0 FAIL / 0 WARN and regeneration remains byte-identical at
  board SHA-256 `8429ce851ed4`.
- Accepted D14 and replaced the conservative four-edge 100 x 100 mm ring with
  a 90 x 65 mm open-bottom U: ANT2/ANT1/PLUTO RX/ANT8/ANT7 across the north
  edge, ANT3/ANT4 west and ANT6/ANT5 east. This cuts board area by 41.5% while
  preserving the PE42482 cyclic order and zero proper straight RF-corridor
  crossings.
- Shortened the common straight placement span from 36.501 to 14.502 mm and
  the longest throw span from 46.580 to 35.676 mm. The resulting throw spans
  are 19.983–35.676 mm placement metrics, not routed length or phase claims.
- Regenerated the exact track-free board and moved only F1 by 1 mm after the
  first compact pass exposed a degraded J1 reference-designator ownership
  warning. The final generator reports 29/29 owned silk labels; P-PINMAP,
  P-OUT/P-CAP/P-BODYCLR, P-MODEL, P-PADSEP, P-LAND, placement DRC and
  R-PREFLIGHT all pass.
- Promoted fresh D15 top, oblique and edge renders of board SHA-256
  `3fffbc690051`; all nine exact SMA bodies face outward with visible gaps,
  corner mounting access remains open, and keyed SWD plus power-only USB-C
  remain unobstructed. Routing is still deliberately unstarted.
Released: no
