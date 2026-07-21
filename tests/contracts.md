# contract: tests/

**Purpose** — the suite that proves the gates can FAIL (tests/README.md is
the binding testing contract; read it before touching anything here).

## Allowed

| Pattern | What |
|---|---|
| `README.md` | the testing contract |
| `contracts.md` | this file |
| `run_tests.sh` | the runner (fast / --slow / --net tiers) |
| `harness.py` | the ~100-line runner library (no pytest) |
| `t*.py` | suites: t0 fixtures are data, t1 unit, t2 integration, t3 acceptance, t4 regressions (one test per paid-for incident) |
| `e2e_boards.py` | --slow real-board regeneration |
| `net_live.py` | opt-in live-network tier (does not exist until needed) |
| `fixtures/**` | hand-authored fixture data (see fixtures/t0/README.md) |
| `t5_skill_canary/**` | the agentic red/green skill test: briefs + grade.py |

## Audit

- `./tests/run_tests.sh` — the summary must report a NONZERO known-bad
  count; the runner refuses success at zero.
- Every new checker or gate lands with a known-bad fixture red-verified
  against the pre-fix code (procedure in README.md §Adding a regression).
