# T5 — the skill canary (agentic red/green test of /pcb-design itself)

**Why this tier exists (2026-07-21).** The T1–T4 suites prove the *checkers*
work; nothing proved the *skill* could take a brief to a board. Every prior
"success" was interactive or a copy of a shipped board — the skill had never
been red or green from scratch, just unmeasured. The first true clean-room run
then stalled on three decisions the skill had never encoded (package escape,
fab tier, adjacency placement — now SKILL.md gates D-ESC/D-TIER/D-ADJ). This
tier is "a gate that cannot fail is worthless," applied to the skill itself.

## The two canaries

| canary | brief | correct outcome |
|---|---|---|
| **GREEN** | `green_brief.md` — 12V→5V/2A buck board, deliberately feasible at standard tier | fresh agent reaches **measured** DRC 0/0/0 + parity + judgment artifacts (protection ADR, D-ESC note), zero bespoke generation Python |
| **RED** | `red_brief.md` — mandates the incident QFN-10 at standard-tier rules (infeasible as specified) | agent **names the wall** (escape/tier refusal ADR) and ships **no fake release**. A genuine 0/0/0 = MISCALIBRATED, investigate. |

Both briefs carry a CALIBRATION comment for maintainers — never paste it to
the agent; the brief text above it is the verbatim prompt.

## How to run (orchestrator procedure — an agent run each, so opt-in)

1. Isolated sandbox per run, NO other projects on disk (the cleanroom-worktree
   pattern): `git worktree add <dir> -b t5-canary-<date>`, `git rm -r projects/`,
   commit, `mkdir projects/t5-<green|red>`.
2. Launch a FRESH agent (no session history) with: the isolation rules, the
   toolchain paths, "follow skills/pcb-design/SKILL.md", and the brief file's
   verbatim text. Absent-user autonomous; honest-blocker reporting REQUIRED.
3. Grade on artifacts, never on the agent's claims:
   `/usr/bin/python3 tests/t5_skill_canary/grade.py green <project-dir>`
   (exit 0 PASS / 1 FAIL / 2 MISCALIBRATED — red only).
4. Tear down the worktree; keep the graded tree only on failure (evidence).

When to run: after any change to SKILL.md / the generic backends' interfaces /
the templates, and periodically. Not per-commit — each canary costs a full
agent run.

## Grading contract (what grade.py measures)

- GREEN: re-runs DRC itself (a report saying 0/0/0 is a claim, not evidence);
  requires the protection-ADR and D-ESC artifacts; forbids the five retired
  bespoke generators in 03_src.
- RED: passes only on a refusal ARTIFACT (ADR/report matching escape/tier
  infeasibility language) with no MANIFEST-bearing release; a release with
  measured non-clean DRC = FAIL (faked green); a release with measured clean
  DRC = MISCALIBRATED (exit 2) — fix the brief, don't celebrate.
