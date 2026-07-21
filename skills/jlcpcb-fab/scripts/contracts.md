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

- Checkers: clean + known-bad tests in `tests/` (t1_jlc_twin.py).
- Fetch/stock classifiers must treat any UNRECOGNIZED failure as a blocking
  failure, never as an affirmative disposition (the NO-CAD incident,
  2026-07-20).
