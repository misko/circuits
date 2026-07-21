# contract: scripts/

**Purpose** — repo-level tooling that governs the repo itself (not any one
skill or board). Skill tooling lives in `skills/*/scripts/`; board tooling is
config for the generic backend. Only cross-cutting repo infrastructure
belongs here.

## Allowed

| Pattern | What |
|---|---|
| `*.py` | repo tools (`contracts_audit.py`, ...) |
| `*.sh` | repo scaffolding (`cleanroom_prep.sh` — the clean-room launcher; lives OUTSIDE the skill because the skill under test must not define its own test harness) |
| `contracts.md` | this file |

## Audit

- Every tool here is exercised by `tests/` with clean + known-bad coverage,
  same bar as skill checkers.
