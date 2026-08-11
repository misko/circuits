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
- `contracts_audit.py` has THREE scopes and the suite reads the RAW EXIT CODE
  of all three (`tests/t1_contracts.py`). Never pipe them — `| tail` reports
  tail's status.

  | invocation | population | graded by |
  |---|---|---|
  | `contracts_audit.py` | 325 tracked, `projects/**` + `archived_projects/**` excluded | strict: any violation = exit 1 |
  | `contracts_audit.py --projects` | 8035 tracked (`git ls-files`) | 2681 governed debt entries; `DEBT_CEILING`, per unit, TIGHT |
  | `contracts_audit.py --present` | 8035 = tracked ∪ untracked-not-ignored | the above + `STRAY_UNITS` (currently zero) |

## Canon rows this repo's tooling adds (2026-07-31)

These are stated HERE because `skills/kicad-pcb/references/design-policies.md`
is a skill-owned file and was another agent's during the change that minted
them. **OWED: a `design-policies.md` row for each**, with the `M-` prefix its
family uses.

| id | rule | machine check |
|---|---|---|
| **M-CEIL** | **A DECLARED GAP MUST COST SOMETHING.** This repo has ratchet FLOORS and no CEILINGS, so an honestly declared gap is free — and free gaps do not close. Every measured-and-accepted defect count gets a CEILING that may only FALL, recorded per UNIT (never as a fleet aggregate: a fleet total breaks when a new board is commissioned, which is a CORRECT action — `PREC_OWED_CEILING`, 2026-07-30) and asserted with EQUALITY, never `<=`, so an improvement must be recorded in the same change and slack cannot be banked. Both vacuity guards are mandatory: a unit the sweep sees with no row FAILS (a map satisfiable by omission is not a bound), and a row for a unit the sweep does not see FAILS (a bound nothing measures is not a bound). **THE MOTIVATING HALF-FIX**: on 2026-07-28 `contracts_audit`'s verdict was made to carry its denominator because `243 files, 0 violations` was being read as COVERAGE. That made the gap VISIBLE without making it COST anything, and `--projects` sat at 2674 violations / RAW EXIT 1 on every suite run for three days while the test above it asserted only that the output did not say `NOT GRADED` | `contracts_audit.py` `DEBT_CEILING`/`STRAY_UNITS`; `t1_contracts.py::t_projects_exit_code_is_read` |
| **M-PRESENT** | **THE UNGOVERNED-FILE POPULATION IS THE WALK MINUS `git check-ignore`, AND IT IS GRADED ON PRESENCE.** A raw walk of this repo is 227883 files and auditing it is meaningless; a file that is neither tracked nor ignored is either a violation or something that should not be in the repo, which is 7523. **Presence, not violations**: MEASURED — point the auditor at a COPY of a governed tree and it reports `0 violations`, RAW EXIT 0, because a copy brings its own `contracts.md` with it. The 3.1 GB stray `git worktree` found at this repo's root on 2026-07-31 was exactly that, and a violation-counting gate grades it GREEN. What is wrong with a stray is that it EXISTS. Declared as a SET OF UNITS, not a file count — a count over an in-flight board flaps on every file its author writes, and a ratchet that fails on correct work gets deleted | `contracts_audit.py --present`; `t1_contracts.py::t_present_scope_is_presence_not_violations` |
| **M-FIELD** | **A DECLARED FIELD WITH NO CONSUMER IS A DEFECT** — the appearance of a control, which is worse than its absence, because a reader checking whether the requirement is captured finds that it is. `fab_tiers.yaml`'s `order_readme:` carries the exact required ORDER_README sentence and no script reads it. Scope MEASURED first (a check that cannot pass is not a gate): 47 declared fields across `skills/**/references/*.yaml`, 9 unread | `t1_contracts.py::t_declared_field_has_a_consumer`, `ORPHAN_CEILING` |
| **M-HANDFIX** | **A MANUAL STEP THAT FIXES A PRODUCER'S OUTPUT IS A DEFECT REPORT** — file it against the producer instead of performing it. The hand-copy that bridged `export_jlc_package.py`'s `fab/bom_jlc.csv` to the contract's `fab/bom.csv` did not merely hide the bug, it GUARANTEED it stayed hidden: every downstream gate always saw a correct tree, so the defect was unobservable by construction. `A-STOCK`/`A-BUY` reached a zero denominator and emitted NOTES instead of failures | prose (SKILL.md stage 7); **OWED: a mechanical check** — 5 sealed archives carry BOTH names, so the fingerprint is greppable |
