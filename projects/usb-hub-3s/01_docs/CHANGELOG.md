# Changelog

One entry per REVISION (a design state, git-tagged). Reverse-chronological.
`Released:` is `no`, or the name of the `07_releases/` directory that shipped it
— it is the only link between a revision and a fab order.

Most revisions never ship. That is normal: a board can go v4.4 → v4.10 in a
day and fab exactly one of them.

## v1.1 — 2026-07-22
- RESPIN driven by the v1.0 review ledger (08_reviews/DISPOSITIONS.md
  X1-X30; two red-team reviews archived). Sealed v1.0 untouched.
- P0 fixes: D1 TVS moved to VIN behind Q1 (X1/X29, ADR-0001 amendment +
  exact fuse 0297020.WXNV with I2t coordination); PD power cell
  re-floorplanned as a compact reference block with bridge-rail HF banks
  C46-C51 and Kelvin-stubbed shunts (X2/X18/X19); gate-R slots R28-R31
  populated at the gates (X4); FET/TVS coordination: Q4-Q8 -> 60V AON6262E,
  per-node clamps D6 SMAJ15A / D7 SMAJ24A (X3, ADR-0007).
- P1: L1 -> YSPI1770Y-100M 16A rms (X5, ADR-0008); LX copper F.Cu-only
  minimum islands (X20); 0.45/0.3 trunk via farms + thermal arrays, In2
  full-connect (X22/X23); UVLO worst-case band documented + PROTECTED-3S-
  PACK-ONLY silk (X7/X14); standby-drain corrected to mA-class (X12);
  ADR-0009 records D3 as surge-grade and Q8 backfeed as benign (X8/X30).
- Docs reconciled to as-built refdes (X10/X15 - the "R7 DNP" trap fixed);
  electrical_invariants.yaml added (checker pending).
- Released: (pending this revision's gates)

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
