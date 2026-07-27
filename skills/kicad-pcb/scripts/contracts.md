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
- **THE REGRADE — the only control for defects that BECOME wrong (ADR-0004).**
  `fleet_regrade.py [--root DIR] [--project NAME]` runs today's standalone
  gates against EVERY sealed release and answers two questions: does it still
  pass, and **which of today's gates NEVER GRADED it**. The second is the one
  that was missing — a gate ID that exists today and appears in NONE of a
  release's shipped verification artifacts never graded it, and an absent
  verdict is not a pass.
  **RUN IT WHENEVER A GATE LANDS.** Shifting left cannot reach this class:
  interposer v1.0 sealed 2026-07-24 with `J_KEY_MATRIX` at CPL 90.0 from
  name-DB rule `^JST_GH_SM,180`, which was REFUTED on 2026-07-25 — the day
  AFTER. It was correct by the knowledge of its day and became a P0 overnight,
  silently, because the pad array is symmetric about its own centre. Its
  `policy_audit.md` carries NO A-POP/A-POS/A-ROT/A-POL/A-BODY/A-STOCK row at
  all, sealed during the days that family was landing and never re-graded.
  It reports its own coverage and names every gate it could not run; a FAIL on
  a release carrying `SUPERSEDED.md` is marked as history, so the live defects
  are not buried under superseded siblings.
  KNOWN GAP IT REPORTS RATHER THAN HIDES: a board superseded by a SUCCESSOR
  PROJECT (crow-mic-pod -> crow-mic-pod-v2) carries no `SUPERSEDED.md`, because
  that file names a successor directory inside the same `07_releases/`. Those
  read as live and are not. The supersede convention has no cross-project form;
  special-casing it inside the tool would hide a real gap in the contract.
  **First run, 2026-07-27: 26 releases regraded, 8 live, 5 live failures, and
  every live release never graded by FAB-PAYLOAD or RENDER** — both landed that
  day, which is the mechanism working, not a defect.

## Structure

One file per tool; no package/`__init__.py` — scripts are invoked by path.
`__pycache__/` is gitignored, never committed.
