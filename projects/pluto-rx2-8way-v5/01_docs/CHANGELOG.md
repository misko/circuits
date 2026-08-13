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
- Closed a discovered project-slug versus board-stem mismatch in all three RF
  artifact contracts before advancing the stage.
Released: no
