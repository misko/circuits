# Changelog

One entry per REVISION (a design state, git-tagged). Reverse-chronological.
`Released:` is `no`, or the name of the `07_releases/` directory that shipped it
— it is the only link between a revision and a fab order.

Most revisions never ship. That is normal: a board can go v4.4 → v4.10 in a
day and fab exactly one of them.

## v0.0 — 2026-08-13  [untagged checkpoint]
- Accepted the clean-room one-of-eight SP8T, autonomous dwell controller and
  independent power-only USB-C architectures.
- Selected 12 exact BOM codes and closed their source, package, pin, power,
  protection and JLC evidence before schematic generation.
- Replaced the initial slow timing with generated `fast20-v1`: unique
  20–50 ms antenna dwells, 5 ms guards, 80 ms marker and a 386 ms cycle.
- Selected direct Raspberry Pi GPIO SWD on five bare pads as the normal
  profile-update path, retaining ST-LINK compatibility as a fallback.
- Generated and hash-bound the clean-room four-page, 33-component schematic;
  manifest/Circuit JSON/KiCad/netlist agree 33/33, 129/129 pin mappings and
  30/30 electrical invariants pass, ERC has zero errors, and independent RF
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
  SMA silk, numeric-to-alphanumeric USB pin identity and explicit zero critical
  pair denominator. Final placement DRC is 0 violations / 39 expected unrouted
  items / 0 parity findings; P-OUT, P-CAP, P-BODYCLR, P-PADSEP and 117-identity
  P-PINMAP all pass.
- Rejected the first apparently successful final render because the USB-C
  body was absent under an unresolved headless KiCad model token; vendored and
  hash-bound the exact GCT STEP model, then regenerated the board, gates and
  complete top/oblique/edge evidence before pausing for review.
Released: no
