# Changelog

One entry per REVISION (a design state, git-tagged). Reverse-chronological.
`Released:` is `no`, or the name of the `07_releases/` directory that shipped it
— it is the only link between a revision and a fab order.

Most revisions never ship. That is normal: a board can go v4.4 → v4.10 in a
day and fab exactly one of them.

## v0.0 — 2026-08-13  [untagged checkpoint]
- Accepted the clean-room one-of-eight SP8T, autonomous dwell controller and
  independent power-only USB-C architectures.
- Selected 13 exact BOM codes and closed their source, package, pin, power,
  protection and JLC evidence before schematic generation.
- Rejected a 10-V protected-input capacitor after clamp coordination and
  replaced it with the exact 16-V code.
- Selected the JLC04161H-7628 four-layer basis; exact RF geometry remains
  intentionally pending the official calculator at PCB stage.
Released: no
