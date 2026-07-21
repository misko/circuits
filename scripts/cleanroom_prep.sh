#!/usr/bin/env bash
# cleanroom_prep.sh — one-command scaffolding for a clean-room /pcb-design
# acceptance run (the T5 canary / cleanroom-worktree pattern).
#
#   scripts/cleanroom_prep.sh <name> <brief-file>
#     <name>        worktree/branch suffix, e.g. 3s-v4  ->  branch cleanroom-<name>,
#                   worktree ~/gits/circuits-cr-<name>
#     <brief-file>  file whose FULL TEXT is the commission (verbatim prompt +
#                   any user directives). Never includes maintainer notes.
#
# What it does (and prints): cuts a fresh worktree from current main, strips
# projects/ resume_state.md tests/ (prior-board knowledge and the canary
# briefs must not be readable in-root), commits the strip, recreates an empty
# projects/, then renders the standard isolation prompt to
# <worktree>/CLEANROOM_PROMPT.txt for the orchestrator to launch an agent
# with. The scaffolding lives HERE, outside the skill, because the skill
# under test must not define its own test harness.
set -euo pipefail
NAME="${1:?usage: cleanroom_prep.sh <name> <brief-file>}"
BRIEF_FILE="${2:?usage: cleanroom_prep.sh <name> <brief-file>}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WT="$HOME/gits/circuits-cr-$NAME"
BR="cleanroom-$NAME"
BRIEF="$(cat "$BRIEF_FILE")"

cd "$REPO"
git worktree add "$WT" -b "$BR" main
cd "$WT"
git rm -r -q projects resume_state.md tests 2>/dev/null || git rm -r -q projects tests
git commit -q -m "$BR: physical isolation — strip projects/, resume_state.md, tests/ (cleanroom_prep.sh)"
mkdir projects

cat > CLEANROOM_PROMPT.txt <<EOF
You are running a CLEAN-ROOM acceptance test of the pcb-design skill. You must
design a board from scratch, alone, using only the skill and toolchain — this
tests whether the skill's encoded judgment suffices without any prior board to
copy from.

THE BRIEF (treat as the commission; record verbatim per the BRIEF contract):
$BRIEF

WORKING ROOT (your entire world): $WT — a git worktree on branch $BR. Create
your project under projects/<name>/ there.

HARD ISOLATION RULES (violating any invalidates the test):
1. NEVER read $HOME/gits/circuits or any other checkout/worktree of it, or
   any project outside your worktree. There are no projects in your worktree
   by design.
2. Do NOT use the Skill tool for pcb-design/kicad-pcb/jlcpcb-fab — its
   registry resolves outside your root. READ and follow the in-tree skills
   directly: skills/pcb-design/SKILL.md orchestrates; skills/kicad-pcb/ and
   skills/jlcpcb-fab/ hold the scripts, references and templates. The repo
   CLAUDE.md and the contracts.md governance chain are binding — seed your
   project from skills/pcb-design/templates/ per its README and verify the
   tree with scripts/contracts_audit.py --walk --root <project>.
3. Every file read OUTSIDE the worktree must be toolchain-only and appended
   to <project>/06_build/reads_outside_root.log as "path | one-line reason".
   At the end this log must be toolchain-only.
4. Web research (datasheets, standards, JLC parts/stock) is allowed and
   expected — design research, not contamination. Log nothing for web reads.

TOOLCHAIN (allowed outside-root reads): /usr/bin/python3 (the interpreter
with pcbnew — use it for anything importing pcbnew), /usr/bin/kicad-cli,
tsci at ~/.nvm/versions/node/v22.12.0/bin/tsci, bun at ~/.bun/bin, KRT router
at ~/gits/KiCadRoutingTools, python venv ~/virtual-envs/spf.

WORKING RULES:
- Fully autonomous; the user is absent. Never pause to ask.
- git commit on the worktree branch at each green gate (never push). Keep
  BRIEF.md and decision docs current enough that a successor agent could
  resume from the tree alone.
- Reports are claims: a gate passes only when the gate command's own output
  says so — re-measure, never summarize hope.
- On a genuine infeasibility wall: write a decision record naming it and stop
  honestly — never fake progress or a release.

DELIVERABLE: a fully designed, placed, routed board meeting the brief,
reaching DRC 0 violations / 0 unconnected / 0 parity at
--severity-all --refill-zones --schematic-parity, the skill's full
verification suite, and the JLCPCB manufacturing package released per the
release contract.

FINAL REPORT (your return text): stage-by-stage status with MEASURED numbers;
the fab tier chosen and why; every part selected with its escape verdict
(including per-side escape counts for dense packages); how each brief
requirement/directive is satisfied; commits (shas); and if you stopped early,
exactly where and why.
EOF

echo
echo "READY: $WT  (branch $BR)"
echo "Launch an agent with the contents of $WT/CLEANROOM_PROMPT.txt"
echo "Afterwards: audit the transcript for out-of-root reads; grade with"
echo "tests/t5_skill_canary/grade.py (from the MAIN repo, which keeps tests/)."
