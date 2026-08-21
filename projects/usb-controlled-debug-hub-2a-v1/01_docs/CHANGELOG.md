# Changelog

One entry per REVISION (a design state, git-tagged). Reverse-chronological.
`Released:` is `no`, or the name of the `07_releases/` directory that shipped it
— it is the only link between a revision and a fab order.

Most revisions never ship. That is normal: a board can go v4.4 → v4.10 in a
day and fab exactly one of them.

## v0.1.1 — 2026-08-21  [tag: 55c03b8b]
- Repaired and source-owned all USB 2.0 routes, including complete critical-pair,
  length-matching and adjacent-reference-plane contracts.
- Removed broad clearance workarounds; native KiCad DRC/parity is 0/0/0 with
  the full declared clearance rules active.
- Made required route checks fail closed when their declarations or evidence
  are absent.
Released: v0.1.1-2026-08-21

## v0.1.0 — 2026-08-21  [tag: 1d3bdeb1]
- Initial four-port 2 A USB debug hub release with separate USB-C PD power and
  USB-C data inputs.
- Netclasses and ampacity floors were defined before routing.
Released: v0.1.0-2026-08-21
