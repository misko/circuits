# contract: skills/jlcpcb-fab/references/

**Purpose** — vetted, catalog-verified data the fab scripts consume offline.

## Allowed

| Pattern | What |
|---|---|
| `lcsc_passives_ledger.yaml` | vetted LCSC->MPN/value ledger for fleet R/C passives — leg C of `bom_source_check.py` (canon M6 / policy_audit M-BOM). Schema per entry: `<LCSC>: {mpn, value, verified}` |
| `assembly-and-order.md` | BOM/CPL, sourcing, rotation, and uploader-side procedure |
| `digital-twin.md` | JLC CAD correspondence, model transforms, and render-registration procedure |
| `connector-orientation.md` | connector mouth-axis, mating-plane, and bounded human-view verification procedure |
| `release-staging.md` | exact fabrication/assembly staging battery and seal handoff |
| `first-article-bringup.md` | staged population, exposed-pad, resistance, current-limit and first-power procedure |
| `contracts.md` | this file |

## Audit

- **Verify once, ever; never from a label.** Every ledger `value` comes from
  the JLC/LCSC CATALOG record (exact componentCode match), dated + sourced in
  `verified` — NEVER copied from a BOM Comment. The ledger exists because the
  label can be the lie: C2933210 is catalog 3.74k, every usb-hub BOM labeled
  it 4.12k (the v1.2 DO-NOT-ORDER incident, 2026-07-23), and C2933195 is
  catalog 3.09k labeled 100k (found by the seeding cross-check, same day).
- Append-only per code (a code's catalog value does not change); corrections
  need the same catalog evidence as additions.
- The gate treats an R/C row resolvable by none of {BOM MPN column, vendored
  part.yaml dir name, this ledger} as UNVERIFIABLE-VALUE (a FAIL, not a pass):
  a new code costs one catalog lookup + one appended line, then is quiet
  forever.
- Checked by `tests/t1_bom_source.py` (real sealed v1.2 artifact known-bad +
  empty-ledger RED contrast).
