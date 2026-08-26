# Changelog

One entry per REVISION (a design state, git-tagged). Reverse-chronological.
`Released:` is `no`, or the name of the immutable `07_releases/` directory that
sealed this reviewed design state. It does not mean the candidate was ordered.
Order events and uploader selections are separate evidence owned by the
release/order records.

Most revisions are never sealed, and many sealed candidates are never ordered.
That is normal: a board can go v4.4 → v4.10 in a day, seal one reviewed
candidate, and order none or one later.

## v0.1 — YYYY-MM-DD  [tag: v0.1]
- Initial schematic generated; netclasses + ampacity floors defined BEFORE
  routing (see ../03_src/rules/nets.yaml).
Released: no
