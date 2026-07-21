# RESUME STATE — PCB-design product + clean-room 3S board

_Snapshot: 2026-07-21. Read this first to resume; it points at the durable canon._

## TL;DR

Goal: **a stable `/pcb-design` skill that turns one prompt → designed, placed,
routed board + JLCPCB files.** The skill's *mechanics* (generic backend +
verification) are solid and tested; this session closed the *judgment* gap that
a from-scratch clean-room run exposed. The test board (3S LiPo → 3×USB-A + 1×
USB-C 6A) is at **DRC 3/0/0**, one escape-ADR + via-in-pad away from a release.

## Where the work lives (branches / worktrees)

| path | branch | what |
|---|---|---|
| `~/gits/circuits` | `main` | the skill + all projects + tests. Authoritative. |
| `~/gits/circuits-cr3s` | `cleanroom-3s-v2` | ISOLATED worktree, **all projects removed**, only `projects/3s-power-board-cleanroomv2/`. The clean-room board grind. |
| `~/.claude/skills/{pcb-design,kicad-pcb,jlcpcb-fab}` | — | **symlinks → `~/gits/circuits/skills/*`** (one home, no drift). |

Toolchain (outside any project, all present): `/usr/bin/python3` (pcbnew),
`/usr/bin/kicad-cli`, `tsci` at `~/.nvm/versions/node/v22.12.0/bin/tsci`,
`~/.bun/bin`, KRT `~/gits/KiCadRoutingTools`, venv `~/virtual-envs/spf`.

## The skill is now project-independent (main @ 6340049)

- Carries its own canon under `skills/pcb-design/templates/`: the 9 stage
  `contracts.md` + `03_src/{floorplan,route,rules/nets}.yaml` schema examples +
  a generic `rebuild_all.sh`. Commission copies from the skill, **never** from a
  project. Verified self-contained in a projects-free sandbox.
- `03_src` + `04_kicad` contract templates rewritten to the generic-backend
  reality (config + shared scripts, no per-board `generate_board.py`).

## Generic backend — the shared pipeline (skills/kicad-pcb/scripts/)

A board carries CONFIG, not a backend. Shared scripts:
- `generate_board_generic.py` ← `03_src/floorplan.yaml` (placement/zones/silk)
- `route_and_stitch_generic.py {prep,route,import,stitch}` ← `03_src/route.yaml`
- `generate_rules_generic.py <root>` ← `03_src/rules/nets.yaml` (netclasses+DRU)

Fixes landed this session (all on main, each with a red-verified known-bad test):
- shared `generate_rules_generic` (was hand-written per board) — **ee9f8a9**
- multi-plane `pad_rescue` (bonds GND→In1 **and** VIN→In2) — **67ad0e3**
- stub-floor scoping (`pad_rescue_stubs` rule area) + `fp-lib-table` KIPRJMOD — **67ad0e3**
- `generate_rules_generic` **preserves foreign .kicad_dru rules** so it doesn't
  clobber the stub exemption (gap #1/#3 collision) — **1550f30**
- stub-floor exemption **net-scoped** (`A.NetName ==`) so it doesn't raise the
  floor for SIG tracks crossing the box — **17f3c30**

Test suite: **103 pass / 63 known-bad**, all green. `./tests/run_tests.sh`
(add `--slow` for e2e board rebuilds). Principle: *test the checkers, not just
with them* — every gate has a known-bad fixture that must fail.

## ROOT-CAUSE lesson + the guardrails (main @ 6ae4a4c)

The clean-room 3S board stalled because **load-bearing design decisions never
lived in the skill** — they were in an interactive session + one board's
ORDER_README; two copied boards masked the gap. Comparison with the shipped
`usb-power-3s` (same brief) is the proof: it used a **buck controller (LM5145) +
external FETs** at the **ADVANCED** fab tier; the clean-room agent picked an
**integrated QFN-10 (SY8368)** at **standard** tier and couldn't escape it.

Now encoded as mandatory gates in `skills/pcb-design/SKILL.md`:
- **D-ESC** — escape feasibility checked at part selection (pitch vs tier
  lanes; prefer controller+FETs for >3A bucks); recorded in the part.yaml.
- **D-TIER** — fab tier is an early DECISION with criteria; ADVANCED
  (0.25/0.15mm vias, via-in-pad) is proven/orderable; exact ORDER_README line.
- **D-ADJ** — adjacency placement IS design (golden rule 7): passives hard
  against their pins, dense packages rotated so hard nets face open copper.

## T5 skill canary — the agentic red/green test (`tests/t5_skill_canary/`)

The meta-fix: nothing ever tested the SKILL from scratch (every success was
interactive or a copy). T5 is that test.
- **GREEN** (`green_brief.md`): a feasible 12V→5V/2A buck board; a fresh agent
  must reach MEASURED 0/0/0 + judgment artifacts.
- **RED** (`red_brief.md`): mandates the incident QFN at standard rules
  (infeasible); pass = a refusal ADR naming the wall + no fake release; a
  genuine green = MISCALIBRATED (exit 2).
- `grade.py {green,red} <proj>` re-measures DRC itself (reports are claims).
- Run procedure in `tests/t5_skill_canary/README.md` (opt-in; an agent run each).
- **Not yet run as a live agent test** — the harness/briefs exist; running the
  two canaries is the next validation step. (grade.py already correctly
  RED-graded the current clean-room tree FAIL — its escape ADR is missing.)

## The 3S clean-room board — exact state (cleanroom-3s-v2 @ 0ea3957)

`projects/3s-power-board-cleanroomv2/` — **DRC 3 violations / 0 unconnected /
0 parity** (independently re-measured). Trajectory: 209/52 → (multi-plane
rescue) 207/23 → (Opus placement + advanced-tier grind) **3/0/0**.

The 3 residuals are ALL the SY8368 QFN escape:
- 2× `track_width`: SIG neck-downs at **0.089mm** and **0.076mm** — below the
  0.25mm SIG floor and below advanced-tier 0.09mm. KRT necked the escape; the
  fix is **via-in-pad** (drop the pad straight to an inner layer) or a legal
  escape width, NOT a floor waiver.
- 1× `via_dangling`: a via connected on only one layer.

### To finish the board (next actions, in order)
1. Resolve the QFN escape properly: via-in-pad on the pinched SY8368 pads (the
   `pad_rescue` via-in-pad mechanism exists) OR reshape the escape to a legal
   width. Advanced-tier floors are set; keep them.
2. **WRITE THE ESCAPE ADR** in `01_docs/decisions/0006-*.md` (D-ESC/D-TIER):
   package pitch vs tier lanes, why ADVANCED, the via-in-pad decision, the
   adjacency changes. Add the D-ESC check line to the SY8368 part.yaml. Add the
   ORDER_README line: "ADVANCED option REQUIRED: min via 0.25/0.15mm (QFN
   fanout)". **This artifact is required** — its absence is the T5 lesson
   repeating (analysis in a chat report evaporates).
3. Reach 0/0/0, then full verification per the skill (bom_seed, jlc_stock,
   jlc_twin geometry, fresh-context pin + render reviews, policy_audit 0 FAIL,
   waiver_provenance) → complete 6-part release under `07_releases/`.
4. Re-grade: `grade.py red projects/3s-power-board-cleanroomv2` should flip to
   PASS once the escape ADR is written.

### Backend gap the grind surfaced (report, don't hack)
`generate_rules_generic` clamps class widths to `max(w, 0.25)` and nets.yaml
has no config key for a sub-0.25 width or a scoped/area DRU rule. If a board
legitimately needs that, it's a BACKEND GAP (a `floorplan/route.yaml` schema
addition), not a hand-injected DRU rule.

## How to run a clean-room agent (the isolation contract)

The 2026-07-20 contamination (an agent read a sibling board's design source)
is fixed PHYSICALLY: the worktree has NO other projects on disk. When launching
a from-scratch/grind agent:
- Root it in an isolated worktree (`git worktree add … -b …; git rm -r
  projects/`). Everything it needs is in `skills/`.
- HARD RULE in the brief: do not read `~/gits/circuits` or any other project;
  log every out-of-root read to `06_build/reads_outside_root.log` (must end
  toolchain-only). **Audit the agent's transcript** for sibling-project paths
  when it finishes — this is how both leaks were caught.
- Pass `model: opus` explicitly if the session model is Fable — agents inherit
  the parent model.
- Reports are claims: re-measure DRC / re-run the suite / grep the transcript
  yourself before relaying.

## Open tasks (see TaskList; key ones)
- **#47** grind 3S board to 0/0/0 + release (at 3/0/0; see "To finish" above).
- **#44** clean-room contracts: rewrite stale + prove audit-grade via blind
  fresh-context auditors (per-stage, contract+folder only).
- **#43** `hooks.py` for the irreducible ~10% (rotation solvers, coord patches).
- **#41** 6-layer support in the generic generator (crow-array-central).
- Run the T5 canaries live (green + red) as the first real skill regression test.

## Durable canon (don't re-derive; update in place if evidence changes)
- `~/gits/circuits/CLAUDE.md` — repo rules (immutability, build order, testing).
- `skills/pcb-design/SKILL.md` — orchestration + D-ESC/D-TIER/D-ADJ gates.
- `skills/kicad-pcb/references/design-policies.md` — S/P/R/M check canon.
- `docs/decisions/0001,0002` — tscircuit authoring boundary + native pipeline.
- `docs/generic-generator-proof.md`, `docs/generic-router-proof.md` — what's proven.
- `tests/README.md` — the testing contract.
