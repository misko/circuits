# Changelog

One entry per REVISION (a design state, git-tagged). Reverse-chronological.
`Released:` is `no`, or the name of the `07_releases/` directory that shipped it
— it is the only link between a revision and a fab order.

Most revisions never ship. That is normal: a board can go v4.4 → v4.10 in a
day and fab exactly one of them.

## v1.0 — 2026-07-21
- Full pipeline complete: placed, routed (KRT 7 waves + 44 taps + stitch),
  DRC 0/0/0 at full severity + schematic parity; rebuild_all.sh end-to-end
  green (M3). BOM 48/48 coded, stock 48/48 >= 5x, jlc_twin exit 0 (all
  findings adjudicated), policy_audit FAIL=0.
- Verification-stage part catches, fixed pre-release: USB-A ports were a
  MALE PLUG rated 1.5A (1001-011-01101) -> Kinghelm KH-AF90DIP-112 female
  THT receptacle (ADR 0006); TPS2513 -> TPS2513A (Apple-2.4A divider is
  A-variant-only).
- 7 thermal via-pairs (POFV) through FET drain paddles into B.Cu pours;
  port silk labels; R25 (PDO config) DNP per ADR 0004.
Released: v1.0-2026-07-21

## v0.1 — YYYY-MM-DD  [tag: v0.1]
- Initial schematic generated; netclasses + ampacity floors defined BEFORE
  routing (see ../03_src/rules/nets.yaml).
Released: no
