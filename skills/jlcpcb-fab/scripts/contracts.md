# contract: skills/jlcpcb-fab/scripts/

**Purpose** — executable order/verification tooling (gerber export, BOM/CPL,
stock, twin).

## Allowed

| Pattern | What |
|---|---|
| `*.py` | tools — network access mocked in tests via `$EASYEDA2KICAD` seam |
| `*.sh` | drivers |
| `*.csv` | data tables (e.g. `jlc_rotations_db.csv` — JLC CPL rotation corrections) |
| `contracts.md` | this file |

## Audit

- Checkers: clean + known-bad tests in `tests/` (t1_jlc_twin.py,
  t1_bom_source.py, t1_release_freshness.py).
- `release_freshness_check.py <release_dir>` gates a seal: it FAILS when a
  generated fab/PDF artifact is sha256-identical to an earlier release of the
  same board (stale/inherited output), when the shipped
  `verification/policy_audit.md` result disagrees with the MANIFEST's claimed
  result (audit FAIL vs manifest 0-FAIL/PASS), or when the shipped
  `ORDER_README.md` still carries a draft/placeholder marker — the three
  defects usb-hub-3s-v3 v1.2 shipped DO-NOT-ORDER past every other gate
  (2026-07-23). Documented same-name-identical exceptions (with a reason) go
  in `<release_dir>/verification/freshness_exceptions.txt`.
- Fetch/stock classifiers must treat any UNRECOGNIZED failure as a blocking
  failure, never as an affirmative disposition (the NO-CAD incident,
  2026-07-20).
- The fab BOM's LCSC code is the SOURCE's per-refdes code
  (`circuit.json supplier_part_numbers`), never a value+footprint match:
  `export_jlc_package.py` groups by (LCSC, footprint) so two distinct codes
  on one value+footprint stay on separate rows, and `bom_source_check.py`
  (canon M6 / policy_audit M-BOM) FAILS a merged/substituted/missing/
  dropped-vendored BOM (usb-hub-3s-v3 v1.1 shipped 25V caps for 50V,
  2026-07-23).
- Code identity is not enough: `bom_source_check.py` also runs a SEMANTIC
  value check (leg C) — for every R/C row it resolves the MPN (BOM MPN column,
  else the vendored `02_parts/<MPN>/part.yaml` dir name) and decodes its
  EIA/RKM value OFFLINE, FAILING a VALUE-MISMATCH and FLAGGING an unparseable
  MPN as UNVERIFIABLE-VALUE (never a silent pass). usb-hub-3s-v3 v1.2 shipped
  R12 = C2933210 (FRC0603F3741TS = 3.74k) labeled 4.12k, 2026-07-23. A catalog
  fetch, when in-env, is a stronger add-on but the offline check stands alone.
