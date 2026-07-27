# contract: skills/kicad-pcb/scripts/

**Purpose** — the shared executable backend and checkers. A board carries
CONFIG, not code: anything a specific board needs beyond these scripts is a
BACKEND GAP to report, not a bespoke script to write here.

## Allowed

| Pattern | What |
|---|---|
| `*.py` | generators, checkers, converters — run with `/usr/bin/python3` (pcbnew) |
| `*.sh` | drivers (e.g. `tsx_to_board.sh`) |
| `contracts.md` | this file |

## Audit

- Each script's module docstring states purpose + usage; incident references
  cite board NAMES/commits as provenance, never `projects/...` paths
  (contracts_audit C-ISO).
- Checkers: clean + known-bad tests in `tests/` (see tests/README.md — the
  known-bad count is the number that matters).
- Generators emit artifacts that downstream gates re-measure independently
  (canon M1: checker and checked share no method).
- **The GATE family (canon G-*) — the checkers are themselves governed
  (ADR-0004).** `gate_contract_audit.py [--root DIR]` walks every
  `skills/*/scripts/*.py` that prints a PASS/FAIL verdict and requires three
  obligations: **G-INPUT** name the artifact graded, so a reader can tell
  shipped bytes from a reconstruction (canon M6); **G-COVER** emit an `N/M`
  coverage denominator; **G-RED** have a `tests/` fixture using `must_fail`.
  A script it cannot parse is **G-PARSE FAIL**, never a skip.
  WHY: `contracts_audit.py` governs FOLDERS and nothing governed the CHECKERS,
  so A-AMP graded **10 of 57** declared net-class currents fleet-wide (any
  qualifier — "7 A worst case", "6 A / 5 A" — makes `parse_amps` return None
  and `rules_audit.py:336` files it under OKS as "n/a (no current: declared)",
  a message wrong 100% of the time since zero classes declare none);
  `bom_source_check.row_kind` dropped `RS1/RS2` and `CE1` while printing PASS;
  and `labeled_resistance("10mOhm")` returned 1.0e7 because the multiplier is
  uppercased, so milli decoded as mega.
  **Its acceptance test is adversarial** and pinned in `t1_gate_contract.py`:
  it must flag `rules_audit.py` and `bom_source_check.py`, the two scripts
  measured silent BEFORE it existed. A gate-on-gates that reports this tree
  clean is decoration and should be deleted rather than trusted.
  `SKIP_BASENAMES` lists generators/libraries that produce rather than grade;
  adding a name there is a coverage decision and must be justified.

## Structure

One file per tool; no package/`__init__.py` — scripts are invoked by path.
`__pycache__/` is gitignored, never committed.
