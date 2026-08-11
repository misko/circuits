---
name: pcb-design
description: "Full PCB design pipeline entry point: takes a design brief and drives it from commission to a verified, ORDERABLE-AND-ASSEMBLED JLCPCB PCBA release. Use when the user wants a new circuit board designed end-to-end."
---

# /pcb-design — brief to an ASSEMBLED board

## PCBA is the deliverable

**Every board is designed to arrive ASSEMBLED.** Gerbers are an intermediate,
not the goal. Operationally: every footprint is machine-placed unless a
recorded decision says otherwise; every BOM line carries an LCSC code unless
`03_src/rules/assembly.yaml` justifies its absence with a dated measurement;
and the CPL is gated the way copper is — classified, never counted. An
unpopulated part is a DEFECT WITH A DECISION RECORD, never a free outcome, and
"hand-solder" is a sourcing wall you must PROVE you hit, not a style.

This is paid-for, and all three incidents below were found by REVIEWERS, not by
any gate:

- **cooksense v1.1** ships 13 CPL placement rows whose BOM line has a BLANK
  LCSC, and its own MANIFEST declares 12 of them `not_assembled` — the machine
  and the manifest were handed contradictory instructions (J_TC is blank on the
  CPL and declared nowhere). Every gate was green.
- **crow-recorder-central-v2 v1.2** sealed with U1 (consigned 0.4mm-pitch
  TQFP-128) at CPL 270 when its own shipped twin measured 90: **180 degrees
  off**. Cost a superseding release whose fab set differs from v1.2 in exactly
  one file.
- **cooksense v1.0 + v1.1** ship U_WD at 270 where this repo's own rotation
  table already held the measurement that says 90 — written into a NEIGHBOURING
  row's evidence prose instead of a row of its own, so the resolver never saw
  it (fixed 2026-07-25; the rule now lives in the table header).

Assembly correctness is not polish applied at order time. It is earned at PART
SELECTION and gated BEFORE the seal, because after the seal the only remedy is
a new release.

The argument is the user's design brief, VERBATIM. You will drive the full
pipeline in `~/gits/circuits/projects/<name>/`. Load the `kicad-pcb` and
`jlcpcb-fab` skills NOW — they hold the routing/fab mechanics and the
hard-won traps; this skill is the orchestration layer only.

## Publication is a sealed-state claim (fail closed)

**DRC 0/0/0, parity 0, a canonical generated board, a fabrication preflight,
or a source-file manifest means the ROUTING/BUILD stage is green. None of
those facts means the design is reviewed, sealed, released, publishable,
shippable, or ready.** At routing completion, rewrite the beacon to
`stage: verify`, `state: working`; do not invent `publish_handoff`, `green`, or
another state outside the schema.

Treat the words **publish**, **release**, **ship**, **ready**, and **merge to
main** as a request for the complete sealed-state process unless the user
explicitly requests an unreviewed work-in-progress branch or draft PR. An
unreviewed WIP must say so in its title and first-screen status and must not be
merged to the repository's publication branch. A `PUBLISH_MANIFEST.md` may
inventory files for a handoff, but it is never release authority and may not
be derived from build metrics alone.

Immediately before any publication-branch push or merge, run:

    python3 skills/pcb-design/scripts/pcb_publication_gate.py \
      --base <publication-branch-base-sha> --head <candidate-head-sha>

The gate selects every project with a material design diff and requires each
live board to have a complete latest sealed release, existing release gates,
byte-identical live/sealed board source, no material drift since the MANIFEST
source commit, and all four pin/render/topology/layout reviews at
`design_verdict: SOUND`, bound to that exact board SHA and archived verbatim in
`08_reviews/`. Zero required reviews is 0/2 coverage and a failure, never a
skip. Repository protection must require this check and a pull request for the
publication branch; a workflow running after an unprotected direct push can
report a violation but cannot undo publication.

## The execution model — a LOOP, not a line

The stages below are numbered, but the pipeline is not a one-way march:
every stage is `(enter → work → gate → EITHER pass forward OR iterate,
bounded)`, and getting stuck at a stage is an EXPECTED transition, not a
failure. The full state machine per stage:

    enter(X) → work → measure gate
      gate green            → commit, journal `finish`, advance to X+1
      gate red, improving   → journal `iterate N`, adjust THIS stage's
                              config, re-measure (budget: see D-BACK)
      STUCK (D-BACK trigger)→ 1. RECOGNIZE  journal the `stuck` entry with
                                 the measured plateau
                              2. DIAGNOSE   read the gate's own output and
                                 name the UPSTREAM DECISION that produced
                                 it (the D-BACK ladder maps finding class
                                 → causal stage; verify the hypothesis
                                 against the artifact — e.g. are ALL
                                 residual violations inside one package's
                                 escape? then it is a PART/PLACEMENT
                                 problem, not a routing problem)
                              3. BACKTRACK  to that stage (e.g. parts
                                 selection), carrying the learnings block
                              4. FIX        the upstream source there
                                 (part.yaml, floorplan.yaml, nets.yaml,
                                 the ADR) — never a downstream artifact
                              5. RESUME     rerun the chain FROM that
                                 stage forward (canon M3 regenerates
                                 everything downstream); journal
                                 `iterate (post-back)` at each re-entered
                                 gate. Work still valid upstream of the
                                 fix (parts untouched, ADRs amended not
                                 rewritten) is kept, not redone.

A stall — repeating a red gate without a new hypothesis — is the ONLY
prohibited state. The bounded budgets, the ladder, and the honest-stop ADR
are specified in D-BACK below.

**PLANNED SESSION SPLITS (handoffs are scheduled, not scrambled).** The
declared handoff boundaries are: after the schematic gate, and after the
routing gate (DRC 0/0/0). At a boundary, if your context is past ~70%
consumed, perform a PLANNED handoff instead of pushing into the next
stage: commit, append a `handoff` journal entry (state, next step, open
hypotheses), refresh the BRIEF's status block, and END the session
cleanly — a successor resumes from the tree alone (proven cheap). An
emergency mid-stage handoff loses in-flight hypotheses; a boundary
handoff loses nothing. **A successor's INTAKE is scoped:** read
`01_docs/STATUS.md` (the beacon), the TAIL of the current stage's journal
(the last handoff/iterate entries), and the files the beacon names — never
whole `journal/` or `learnings/` directories (they run 40-70KB per board;
history beyond the live frame is pulled on demand, not preloaded). For PCB
stages, generate and validate the compact content-addressed handoff with
`kicad-pcb/scripts/pcb_flow.py handoff|validate`; do not hand-copy hashes or
gate counts. Its 16 KiB ceiling is the intake budget, and a source/board hash
or tool/gate identity change makes the handoff stale by construction. A
multi-board project must select one nested board config and isolate its input,
part, state, and journal paths. See the kicad-pcb reference
`references/fast-pcb-flow.md` for the stage/ownership and testing contract.

## 0. Commission (before any engineering)

- Pick a short kebab-case project name from the brief.
- `mkdir -p ~/gits/circuits/projects/<name>` with the numbered stage
  folders `01_docs 02_parts 03_src 03_tscircuit 04_kicad 05_firmware
  06_build 07_releases 08_reviews`. Copy each folder's `contracts.md` from the SKILL's
  OWN canonical set — `<pcb-design skill>/templates/contracts/<stage>/contracts.md`
  (and `templates/contracts/ROOT.contracts.md` → the project-root
  `contracts.md`). **The skill is project-independent: never copy contracts
  or config from another project** — that coupling let a clean-room agent read
  a sibling board's design (2026-07-20). Read the contracts; they are binding.
- Seed `03_src/` config from the skill's schema examples —
  `<pcb-design skill>/templates/03_src/{floorplan.yaml,route.yaml,rebuild_all.sh,
  rules/{nets.yaml,power_tree.yaml,requirements.yaml,power_stages.yaml,
  protection_paths.yaml,electrical_invariants.yaml,integration.yaml}}`
  — plus `rules/mates.yaml` ONLY if the board mates to foreign hardware
  (D-MATE below; a board that mates to nothing must not carry an empty one,
  which `import_provenance_check.py` fails as M-COVER) —
  then replace the values for THIS board. The keys are the contract the
  shared generic backend consumes; the values are yours to derive. (The two
  `rules/` schema files were omitted from the copy list until 2026-07-23
  although stages 1-3 mandate authoring both — seed them.)
- **`03_tscircuit/` is the TSX authoring source** (renamed from bare
  `tscircuit/` 2026-07-20): it holds hand-written SOURCE, the same pipeline
  stage as `03_src/`, hence the same number. `03_src/` = the KiCad-side
  generators + promoted route; `03_tscircuit/` = the TSX the board is
  authored in. The shared module library `tscircuit_modules/` at the REPO
  ROOT is not a project stage and stays unnumbered.
- Write `01_docs/BRIEF.md`: the user's prompt VERBATIM between
  `<!-- prompt-verbatim-begin/end -->` markers with its sha256; then the
  parsed requirements (P#), your clarifying questions (Q#) and the user's
  answers (A#), decisions (D#) appended over time. Only user utterances
  may relax a requirement.
- If the brief is underspecified on something that changes the design
  (voltage/current envelope, port counts, protection expectations, size,
  budget/tier), ASK the user now — 2-4 questions max — and record Q#/A#.
  If the user is absent, make the conservative choice — which for an
  ambiguous CAPABILITY means the SIMPLEST reading that satisfies the
  stated requirement, NOT the most capable (a "5A USB-C" is 5V/5A until
  told otherwise, not 5-20V/100W) — record it as D#, and flag it LOUDLY
  in the report. The most-capable reading is where over-engineering hides
  (usb-hub-3s 2026-07-22; see the SPEC-CHECK rule in D-BACK).
  Fill the BRIEF's **Commission fact-lock** table NOW (output-rail voltage
  range + Imax, connector count, simultaneous-load count, continuous/peak
  duty, exact measurement plane and included/excluded delivery-path elements,
  input envelope, protection posture, off-control, hard-cell
  sourcing class) — every row user-confirmed (Q#/A#) or an explicit D#;
  the two rows left unlocked on usb-hub-3s (output V range, protection
  posture) cost that family two generation restarts (~27 of 53 commits,
  2026-07-23).
- **D-MATE, the mating fact-lock (a GATE, canon M-IMPORT).** If this board
  plugs into, bolts to, or lines up with hardware THIS REPO DID NOT DESIGN,
  fill the BRIEF's **`## Mating fact-lock`** NOW, before any floorplan
  exists. Every dimension the floorplan will consume from outside gets a
  row with its **grade**: **MEASURED** (someone touched the object, or read
  a machine-readable source — a `.kicad_pcb`, a drill file, a STEP),
  **CITED** (a vendor document, with figure/page/section), **ESTIMATED**
  (derived, photogrammetric, inferred — and it MUST carry an error bar
  before it may be spent on a dimension), **OWED** (nobody has it; say how
  to get it and do not design against it).
  The facts live ONCE, in **`spf/<device>/`** — `README.md` is the human
  record (method stated per number, MEASURED / ESTIMATED / NOT ESTABLISHED
  kept apart), `facts.yaml` its machine index. The board declares
  **`03_src/rules/mates.yaml`** naming the device and the ids it consumes,
  with `use:` and `where:` — **and no values**. Boards reference; they never
  restate. Seed it from `templates/03_src/rules/mates.yaml` and run
  `$S/import_provenance_check.py .` (M-EXIST / M-GRADE / M-BAR / M-PROXY /
  M-OWED / M-RESTATE / D-MATE).
  WHY THIS IS AT COMMISSION AND NOT AT PLACEMENT: `pluto-cal-switch`'s
  PlutoPlus SMA span was extracted from an undimensioned vector assembly
  plot at **35.60 mm**, and three independent extractions agreed to
  **0.003 mm** — a floorplan and a $101 adapter order were ready to be built
  on it. A caliper on two physical units read **35.04** (genuine) and
  **34.72** (2025 clone) against a rigid-SMA capture window of **±0.05 mm**:
  10-18x over, and the two units sold under one name disagree by 0.32 mm.
  Precision about a proxy is not accuracy about the object, and where a
  drawing and the thing disagree the THING wins. Also from that episode:
  measure the feature whose position you need, not one adjacent to it (the
  protruding barrels stand ~11 mm toward the camera and parallax hid a 3.5%
  asymmetry the flat silkscreen boxes showed at ~3 sigma), and a published
  tolerance whose DATUM is unstated is ESTIMATED, not CITED (JLCPCB's
  ±0.05 mm hole position is hole-to-hole; the edge-referenced term this
  board needed is ±0.20 mm and JLCPCB does not publish it — 4x).
  "This board mates to nothing foreign" is a fine answer; write it in the
  section, because silence is not a declaration.
- **D-SPEC, spec-tension check (a GATE, with D-ESC/D-TIER/D-ADJ).** Test
  every numeric requirement against (a) the governing standard and (b) the
  sourceable-part envelope BEFORE architecture. A brief can demand what no
  compliant/stocked part delivers — "USB-C 6A" exceeds Type-C's 3A CC
  advertisement and even PD's 5V/5A; "USB-A 2.5A" exceeds every JLC-stocked
  receptacle's continuous rating (both: clean-room run 2026-07-21). Each
  tension gets a spec-tension ADR (what the standard/parts cap is, how the
  requirement is honoured — e.g. protection-ceiling reading, proprietary
  sink note) + a `Spec tensions` row in BRIEF.md flagged to the user.
  Silently building the out-of-spec reading, or silently downgrading the
  requirement, are both failures.
  **VOLTAGE ENVELOPE, not just current.** Every power PORT/output pins its
  voltage range (min/max), not only its current — an unpinned output voltage
  is exactly what let converter TOPOLOGY be interpreted instead of derived
  (usb-hub-3s 2026-07-22: "5A compliant USB-C" pinned the current but not the
  5V-only output, so a buck-boost + 16A trunk was built where a buck sufficed).
  Emit the envelopes into `03_src/rules/power_tree.yaml` (one row per rail:
  vin/vout min-max, iout, converter) so the E-TOPO gate DERIVES the required
  buck/boost/buck_boost from Vin-vs-Vout and asserts the chosen part matches —
  over-capable (buck_boost where buck suffices) fails as over-engineering
  unless an ADR justifies the extra capability.
  For a regulated rail feeding a KNOWN load also pin its `load_uv_threshold`
  (the load's brownout V) + `ir_budget_mohm` (delivery board+connector+cable
  resistance) so **E-MARGIN** gates the setpoint headroom; for a self-powered
  board pin `source_type` + `off_control` + `quiescent_ua` so **E-OFF** gates
  de-energization + stored drain (usb-hub-3s-v3 2026-07-23: a 4.97V-into-Pi5
  thin margin and a LiPo pack self-draining via always-on EN pins BOTH passed
  two zero-context red-team reviews — neither was a number the gates checked).
  **SOURCING SPIKE (part of D-SPEC): scarcity is discovered at COMMISSION,
  never at parts stage.** For every SPEC-CRITICAL function (one a
  requirement/directive names explicitly — "5A compliant USB-C", "isolated
  CAN", …): first consult `references/proven-parts.yaml` (the ledger of
  parts this pipeline has already verified); if the ledger has no fit,
  run a TIMEBOXED part-universe search (LCSC/JLC stock) and classify the
  outcome NOW, before architecture:
  (a) sourceable at the cost-ceiling tier → note it, proceed;
  (b) sourceable only at a costlier tier → make the D-TIER decision here,
      at the cheapest moment (ADR + ORDER_README line);
  (c) not sourceable as specified → spec-tension ADR + user flag BEFORE
      any engineering is spent — propose the nearest compliant reading.
  The stage-2 part.yaml work then verifies the chosen part; it never
  DISCOVERS feasibility.
  **D-MOD, COMPLEXITY-WEIGHTED MODULE INTEGRATION (DEFAULT WHEN THE USER IS
  SILENT).** For each complex subsystem—programmable compute/control, radio,
  interface or switching-power controller, precision AFE/transceiver—compare
  proven modules with the bare IC before parts are locked. Optimize total
  engineering effort (support BOM, layout/escape, firmware/bring-up,
  verification, sourcing and assembly), not only unit price or area. Record
  every choice and the bare IC's external `support_refs` in
  `03_src/rules/integration.yaml`; `module_first_check.py` is P-MOD and runs
  before generation. A bare IC with fewer than the configured support-part
  threshold (10 by default) needs a clear total-system rationale but no ritual
  exception. At or above the threshold it requires an ADR, measured/cited
  evidence and at least one concrete module comparison. A module need not fail
  an absolute requirement: a bare IC may win on total verified complexity,
  layout maturity or integration fit, but cost/area alone is not sufficient.

## Journal discipline — every stage, every iteration (canon M9)

The knowledge-evaporation failure mode: the hardest analysis of a run lives
in the agent's chat report and is gone when the session ends. Journals fix
this at the source, MANDATORY (`policy_audit` M-JRNL / M-LEARN):

- **`01_docs/journal/<stage>.md`** — one file per pipeline stage (e.g.
  `02_parts.md`, `03_schematic.md`, `placement.md`, `routing.md`,
  `verify.md`). APPEND an entry at every stage START, every ITERATION, and
  every FINISH — never batch-reconstruct at the end:

      ## <date> <time> — <start|iterate N|finish>
      - did: <the action, one line>
      - result: <MEASURED outcome — counts, gate output, not hope>
      - next: <what this implies>

- **`01_docs/learnings/<stage>.md`** — written when a stage COMPLETES:
  each issue hit, its root cause, and a concrete "how to avoid next time"
  (a config default? a checker? a part-selection rule?), each marked
  `candidate-canon: yes/no` with a suggested check ID. These are HARVEST
  SOURCES for the skill's canon (design-policies.md / T4), not canon
  themselves — repo policy keeps distilled conclusions in the canon, and a
  harvest pass promotes them; raw evidence lives here, per board.

- **`01_docs/STATUS.md` — the live beacon (canon M9, the coordinator's between-
  gates eye).** The journal is append-only HISTORY; the beacon is its LIVE HEAD,
  a tiny `key: value` file (schema in the 01_docs contract) you OVERWRITE — never
  append — at every stage enter/finish, every iterate, and **IMMEDIATELY BEFORE
  and AFTER every long blocking op** (record `op_pid` before, clear it + refresh
  `measure` after). The poll-to-completion rebuild/grind loop **tees its last
  line into `measure`** so the beacon stays current even mid-grind. Multi-board
  projects carry one per board (`STATUS-<board>.md`, mirroring the per-board
  journal suffix). Why it exists: agents used to signal only at coarse gate
  boundaries, so between gates a coordinator was blind — "one tap from done" and
  "stalled" looked identical without reading a multi-MB transcript (usb-hub-3s-v3
  v1.2, 2026-07-23). **The split is load-bearing: routine progress → the BEACON
  (the coordinator POLLS `pcb_status.py`, never interrupts a live `op_pid`); a
  decision or a D-BACK wall → the agent STOPS and ESCALATES** (`state: blocked` +
  a PUSH — a per-step push can't fire from inside a blocking route loop, which is
  exactly why progress is polled and only walls are pushed). The coordinator's
  monitor is `skills/kicad-pcb/scripts/pcb_status.py` (one line per board;
  derives STALLED from a stale `working` beacon with no live op).

- **The beacon is GATED — canon M-BEACON, M9's enforcement arm.**
  `skills/kicad-pcb/scripts/status_beacon_check.py [PROJECT ...] [--root REPO]`
  checks four properties: no field appears twice (the file is OVERWRITTEN, so a
  second occurrence is an APPEND); all seven fields present; a beacon claiming a
  COMPLETED seal names the LIVE release (the newest of THIS board's series with
  no `SUPERSEDED.md`, resolved through `release_index.py` — one home); and
  `updated:` does not predate that board's newest seal. **REFRESHING THE BEACON
  IS PART OF THE SEAL** — the 07_releases contract's "Seal procedure" step 4:
  a seal is not complete until the beacon names the release it just created, and
  the gate is run after the seal commit. Measured 2026-07-27, before the gate
  existed: EVERY beacon in the fleet named the wrong release (13 findings across
  4 of 6 boards), and one had two frames appended into it, which the reader
  rendered as a confident `sealed / done` pointing at a SUPERSEDED release. A
  beacon is the coordinator's only between-gates eye; a stale one does not go
  blank, it lies.

## Compute discipline — tokens under a declared ceiling (the D-TIER symmetry)

Fab cost is governed by a tier DECLARED up front (D-TIER); compute is the same
resource in tokens and gets the same treatment. Four rules:

- **TIERS.** Every spawned agent declares its WORK CLASS in the spawn prompt —
  mechanical (cheap model, low effort), authoring (default model), judgment
  (default model, full effort) — table and rationale in
  `references/compute-tiers.md`; escalating above the class tier requires a
  stated reason there. The routing-grind ladder (Tier 0 script / Tier 1 cheap /
  Tier 2 frontier, stages 4-6) is the proven instance.
- **CONTEXT BUDGET.** An agent past ~70% of its context window (the SAME
  threshold as the planned-session-splits rule — one number, not two) takes
  the NEXT gate boundary as a PLANNED handoff: commit, journal
  `handoff`, refresh the beacon, and a FRESH successor resumes from the tree
  alone (proven cheap). Repeatedly resuming a heavy agent — "resume-the-giant"
  — is the named anti-pattern: every resume re-pays the giant's whole context
  to buy one step a fresh agent takes for a fraction.
- **COMMS PROTOCOL.** The STATUS beacon is the PULL channel: routine progress
  goes there and the coordinator POLLS `pcb_status.py`. PUSH messages go up
  ONLY at a gate, a decision, or a wall. Reports use a terse fixed shape —
  measured numbers, changed files, next step; no narrative. Coordinators BATCH
  relays rather than waking a heavy agent per event (each wake re-pays its
  whole context).
- **VERIFICATION SCOPING.** The full multi-lens review breadth (both red-team
  lenses, pin, render) runs ONCE per MATERIAL design state. A material change
  still voids prior verdicts — that rule keeps its teeth — but post-fix
  re-verification is TARGETED: confirm the specific changed items, plus ONE
  integrated fresh-CONTEXT lens over the fixed board. "Fresh" buys
  INDEPENDENCE (canon M1: a reviewer with no stake in the fix), not repeated
  breadth. Canon home: design-policies.md, "Verification scoping". Two
  corollaries: verification runs against the PRE-SEAL staging archive (a
  finding must cost an edit, not a supersede), and a SEALED release is never
  re-reviewed absent a supersede trigger — retro-checks against a newly
  minted gate are read-only and scoped to that gate (8 of 16 lens runs in
  one family targeted an immutable board and changed nothing, 2026-07-23).

## Iteration & backtracking — the STUCK protocol (D-BACK)

Getting stuck at stage X is normal; grinding stage X forever is the defect.
Canon M3 makes backtracking CHEAP: everything downstream regenerates from
source, so the fix is always an upstream edit + rerun, never a downstream
patch. Three rules:

**1. Stagnation trigger — when local iteration must STOP.** After **3
consecutive iterations with no measured improvement** (the gate count not
dropping, or the same finding IDs recurring), or on any finding class the
CURRENT stage's config cannot express, stop iterating. Do not negotiate
with a wall.

**1a. CLASSIFY BEFORE YOU ESCALATE.** D-BACK sends you upstream along the
symptom's causal edge — so a MISCLASSIFIED symptom sends you up the wrong edge,
and the protocol will work perfectly while pointing at the wrong stage.
pluto-rx2-8way 2026-07-30: D-BACK was declared on 28 unconnected attributed to
"MCU-field congestion", which sent three agents at a PLACEMENT problem. Measured
later, only 8 were at the MCU, 18 were two keepout config lines, and the 8 were
arithmetic (0.400 mm pitch, 0.250 mm via, 0.175 mm against a 0.200 mm floor — no
legal via-in-pad exists) rather than congestion. The board was never short of
AREA: 108 mm2 of courtyard-free space sat 2.6 mm west. **Group the findings by
CAUSE and name the groups before invoking the ladder.** If the groups are
heterogeneous, do the cheap INDEPENDENT ones first — they are often most of the
count — and escalate only what survives.

**2. The backtrack ladder — where to land.** Follow the symptom's causal
edge one stage up (repeat if the upstream stage is also stuck, max depth
until the spec itself):

| Stuck symptom at stage X | Backtrack to | What changes there |
|---|---|---|
| DRC tail resists (clearance/via clusters in one region) | placement | D-ADJ adjacency, escape corridors, rotation |
| unroutable / congestion across regions | placement, then architecture | floorplan real estate, board size, bank split |
| width/via/hole floors physically impossible | tier or part | D-TIER ADR (raise fab_tier + ORDER_README line) or D-ESC re-selection |
| package cannot escape | part selection | different package per escape_check |
| no sourceable compliant part | architecture, then spec | topology change, or a D-SPEC tension ADR + user flag |
| schematic/parity churn | parts (pin maps) | part.yaml re-verification vs the datasheet FIGURE |
| **difficulty traces to an ARCHITECTURE forced by a spec reading** | **spec (ask/flag)** | **is this wall intrinsic to the spec, or to my INTERPRETATION of it?** |

**SPEC-CHECK ON HARD WALLS (the cheapest backtrack of all — a question).**
Before grinding through architecture-driven difficulty, ask whether the
wall is intrinsic to the requirement or to how you READ it. Some hardness
is a spec ambiguity a single clarification dissolves — not a design
problem. When the causal edge points at the spec:
- **User reachable** → ASK a targeted question before building the
  complexity. ("USB-C: 5V-only, or full PD up to 20V? — that is buck vs
  buck-boost.") A 30-second answer beats hours of grind.
- **User absent (autonomous run)** → take the SIMPLEST reading that
  satisfies the STATED requirement, never the most capable; record it as a
  `D#` assumption AND surface it LOUDLY in the final report (a
  cost-driving assumption buried in an ADR is one the user won't catch
  until a respin). Incident (usb-hub-3s 2026-07-22): "USB-C PD" was read
  as full 5-20V (buck-boost, 100W, 16A, a congested PD cell) when the spec
  was 5V/5A (a simple buck, 55W, ~7A) — the most-complex reading, chosen
  when the agent could not ask. E-TOPO now catches the topology
  mechanically; this rule catches the interpretation before it is built.

**3. The backtrack contract — what to carry.** Before leaving stage X:
(a) commit the attempt (WIP checkpoint — the failed state is evidence,
canon: reports are claims but artifacts are proof); (b) append a
`## <ts> — stuck` journal entry: the trigger, the measured plateau, the
causal hypothesis; (c) write the learnings block NOW, not at stage end —
it is the context the retry runs on. Then edit the UPSTREAM source, rerun
the chain from there, and journal the re-entry as `iterate N (post-back)`.
The same stage may be re-entered at most **3 times** on different upstream
hypotheses; a fourth arrival means the hypothesis space is exhausted —
escalate one more stage up, or write the honest-stop ADR naming the wall.
(Incident: v3 session 2 spent ~50 min re-grinding 4 unconnected pads
before retreating to placement; the retreat then recovered the board in
one pass. The trigger existed in hindsight only — now it is a rule.)

**ONE LIVE WRITER, STAGE-LOCKED.** Only one agent/process may edit a board's
live source tree. Parallel agents may research parts, calculate, or review
read-only exact artifacts; speculative downstream work belongs in an isolated
worktree and cannot be promoted while an upstream gate is red. A D-SPEC,
E-PATH, E-SWDRV, E-SURGE, P-BODYCLR, or R-PAIRMAP failure reopens its owning
stage and cancels downstream promotion rather than accumulating repair work.

## 1-3. Design docs, parts, rules (order matters)

**FIRST-DETECTION OWNERSHIP IS A HARD STOP, NOT A POSTMORTEM LABEL.** Each
defect class below has one earliest stage that owns it and one later independent
backstop. The earliest stage may not defer the decision to DRC or the release
review; the backstop may not be cited as the reason an upstream artifact can
remain incomplete.

| Defect class | Earliest owning stage — required evidence before proceeding | Independent backstop |
|---|---|---|
| External-output capability and measurement boundary | **Requirements.** `requirements.yaml` binds port count, simultaneous count, continuous/peak duty, current and voltage at one named measurement plane, with machine-readable `included_elements` and `excluded_elements`. Prose-only boundary evidence fails. Run D-SPEC/E-PATH before schematic review. | E-MARGIN and simultaneous-load first-article measurement at the same plane. |
| TVS / surge / downstream absolute-maximum compatibility | **Parts + architecture.** `DETAIL_DESIGN.md` carries one rail-wide rating table with source operating maximum and tolerance, TVS standoff/breakdown/clamp, disconnect delay, and every directly exposed part's recommended and absolute maximum. The worst protected-rail waveform must remain below every exposed limit with stated margin; a nominal-input comparison is not evidence. | Fresh topology/protection/ratings review before seal. |
| Controller-to-MOSFET gate-drive compatibility | **Parts + schematic architecture.** `power_stages.yaml` uses maximum or explicitly qualified-maximum Qg, switching frequency, all driven FETs, controller minimum drive/current limit, bias, and thermal assumptions. Typical-only Qg is not proof. Run E-SWDRV before placement. | Switching-node waveform/startup test and controller temperature. |
| UVLO, OVLO, enable, current-limit, and feedback thresholds | **Schematic math.** Derive guaranteed-low and guaranteed-high trip/output corners from IC threshold, resistor tolerance, bias/leakage, and temperature limits. Assert the fitted component values in `electrical_invariants.yaml`; nominal-only arithmetic is incomplete. | E-INV/E-MARGIN plus fresh schematic/topology review. |
| Reset, brownout, debugger-halt, or unpowered safe state | **Schematic topology.** Every safety-relevant CMOS input has a physical pull/default path and a `node_level` or equivalent invariant proving the restrictive state; firmware reset behavior is not a resistor. | Fresh topology review and first-power/reset test. |
| Sustained-current protection part | **Parts/BOM.** Fuse/breaker is an exact MPN with voltage, interrupt, and time-current evidence and an unambiguous holder/assembly quantity; a holder rating or silk value is not the protective part. | Sourcing/assembly gate and incoming inspection. |
| End-to-end voltage drop | **Requirements + power tree.** `ir_budget_mohm` covers the entire bounded path named by the requirement: converter/switch, board copper and vias, solder joints, both mated contacts, and any claimed cable/plug. Exclusions must narrow the user-visible claim rather than silently shrink the model. | PCB resistance extraction, E-MARGIN, and simultaneous full-load qualification. |
| Stackup, impedance, reference plane, and pair matching | **Rules before placement/routing.** Bind the intended fabricated stackup; declare each physical P/N chain in `length_match`; declare allowed layer(s), reference plane, and signal-via policy in `rf.yaml`/`nets.yaml`. | RF schematic review before placement, RF PCB review before layout seal, RF fab review on the exact Gerbers. |
| Switching-converter hot loops / Kelvin sense | **Placement.** Adapt the datasheet/EVM layout, encode pin-local adjacency and span budgets, and pass the placement phase of `policy_audit.py` before any route run. Gate-driver, bootstrap, input-cap/FET/shunt, switch-to-inductor, and Kelvin pairs are separate obligations. | Fresh layout/power-integrity review plus first-article waveforms and temperature. |
| Component-body, courtyard, or foreign-pad collision | **Placement.** Every assembled footprint has a same-side courtyard and passes P-BODYCLR at a positive project clearance; zero distance, touching, and overlap are fatal and non-waivable. | Independent placement/render review and assembly twin. |
| Critical-pair omission or wrong routing mode | **Routing contract before route.** Every physical P/N chain is listed in `route.preflight_critical_pairs`, assigned to the differential engine and length-match group, with layer/via policy. R-PAIRMAP must pass before routing; R-CRITESC checks realized copper after stitch. | RF/USB PCB review and exact-fab review. |
| High-current neckdowns and via transitions | **Routing rules.** Current-class width, maximum pad-escape length, via diameter/drill, and required parallel-via count are binding generator inputs. Audit realized copper; a wide trunk does not excuse a long narrow launch or one undersized layer transition. | DRC/ampacity policy, resistance extraction, and simultaneous full-load thermal/drop test. |
| Render/model registration and mechanically critical manual-fit bodies | **Evidence generation.** The twin denominator includes CPL parts and declared manual-fit mechanical parts; same-camera bare subtraction and model-to-footprint registration must pass before a human render review. | Fresh render review before seal. |

1. `01_docs/ARCHITECTURE.md` (topology + power math) and
   `DETAIL_DESIGN.md` (every component value derived, with margins);
   one ADR per real decision in `01_docs/decisions/` — alternatives,
   rejection reasons, live stock data for part choices.
   **Mandatory ADR: battery/input protection** (reverse polarity, fuse,
   UVLO/over-discharge, OV, TVS clamp vs downstream ratings, AND — for a
   self-powered board — OFF-CONTROL: how it is de-energized for storage
   (a master disconnect / load-switch / EN-gating, or an ADR-justified
   always-on) plus its STORED QUIESCENT DRAW) — a clean-room run once
   shipped a LiPo board with zero UVLO because no stage forced the
   question; usb-hub-3s-v3 (2026-07-23) tied both buck EN pins active with
   no master switch and self-drained the pack in storage because no stage
   asked how it turns OFF. Emit the off-control + quiescent-draw decision
   into `03_src/rules/power_tree.yaml` (`source_type:` / `off_control:` /
   `quiescent_ua:`) so the E-OFF gate checks it, and — for a regulated rail
   feeding a known brownout-sensitive load — its `load_uv_threshold:` +
   `ir_budget_mohm:` so E-MARGIN gates the output-setpoint headroom.
2. `02_parts/<MPN>/part.yaml` per part: pin map read from the datasheet
   FIGURE (not assumed), `verified:` note naming figure+page, LCSC code +
   alternates. Stock is CHECKED at selection (jlc_stock_check) but NOT
   committed — the volatile stock/price number lives in `06_build/cache/`
   (TTL'd), never in `part.yaml`, per the 02_parts contract's three-tier
   model. The PDF set MUST include the package/land-pattern drawing, not
   just electricals.
   **Q-2SOURCE is a hard pre-selection gate, before schematic completion.**
   A component may enter the schematic only when the exact authoritative MPN,
   or an explicitly approved dossier alternate, is active and orderable with
   `stock > 10` and enough stock for five board sets at **two independent
   authorized supplier pools**. JLCPCB/LCSC, Mouser, and DigiKey are separate
   pools; multiple listings or packaging records at one distributor count once,
   and marketplace sellers do not count. Run one composed gate so a
   per-distributor gap cannot be mistaken for the policy verdict:

       shopping_list.py PROJECT_DIR --scope all --boards 5 \
         --bom CANDIDATE.csv --required-pools 2 \
         --jlc-stock-json STOCK.json --out REPORT.md --json REPORT.json

   The candidate BOM fixes prerelease multiplicities; the fresh JLC sidecar is
   joined by LCSC, full MPN and manufacturer; exact DigiKey product-page quotes
   include `manufacturer:`. Fewer than two qualifying pools rejects the part;
   it is not a release-time waiver. Repeat the same gate on order day because
   stock is volatile.
   Before closing the parts/rules checkpoint, run
   `python3 skills/kicad-pcb/scripts/rules_audit.py PROJECT_DIR --phase source`.
   This entry grades every authored `nets.yaml` class for non-empty
   intent/routing/verification, a real net list, positive width, readable
   current or explicit signal exemption, and evidenced `pour_fed` geometry.
   It deliberately does not open future `.kicad_pro`, `.kicad_dru` or board
   artifacts. The full rules audit remains mandatory after generation; source
   PASS is an early contract check, not generated-rule evidence.
   **FAN OUT the research (parts are independent):** ledger hits
   (`references/proven-parts.yaml`) need no research — copy the verified
   block. Partition the REMAINING multi-pin parts into groups of ~4 and
   run them as CONCURRENT research sub-agents, each returning a complete
   part.yaml (pin map from the figure, escape block, layout_refs,
   gotchas). You merge, spot-verify the figure citations (S-VER), and run
   escape_check over the merged set — the gates validate the merged
   output, which is what makes the fan-out safe. Serial research on a
   16-part board wastes ~30 minutes for no verification gain.

   **Mandatory design-decision gates (D-MOD / D-ESC / D-TIER / D-ADJ)** — encoded
   2026-07-21 after a clean-room 3S board stalled at DRC on decisions the
   skill had never captured (they lived in one interactive session and one
   board's ORDER_README; two copied boards masked the gap):
   - **D-ESC, escape feasibility at part selection — MECHANICAL, not
     judgment.** Consult `references/proven-parts.yaml` FIRST — a ledger
     hit is a verified selection (escape block + gotchas included); web
     research covers only the gaps, and every NEWLY verified part is
     harvested back into the ledger at release (with provenance), so no
     board re-pays another board's research. Then, for every candidate
     multi-pin package, run
     `skills/kicad-pcb/scripts/escape_check.py --style <qfn|dfn|leaded|
     bga|connector> --pitch <mm>` (capabilities from
     `references/fab_tiers.yaml`) and paste the emitted `escape:` block
     into the part.yaml. Prefer the candidate with the LOWEST
     tier_required that meets spec; for bucks >3A prefer controller +
     external FETs in leaded packages (the shipped 3S board's LM5145 is
     itself a VQFN and needed ADVANCED — screen the controller package
     too). A 0.4-0.5mm-pitch QFN is a PACKAGE decision, never a router
     problem. ENFORCED: `policy_audit` P-ESC fails any multi-pin part
     without a block or whose block disagrees with recomputation.
     **ESCAPE BUDGET for dense LEADED packages (ADR-0008, usb-pwr-hub-3s
     2026-07-21):** "leaded = outward escape" is only half the check. At
     <=0.65mm pitch, COUNT the escapes per side: when one side carries >=6,
     some signals must cross or drop layers, and adjacent-pin escape vias
     are bound by the tier's `min_hole_to_hole` (fab_tiers.yaml) — at
     standard tier, 0.65 pitch − 0.3 drill = 0.35mm hole gap < the 0.5mm
     floor: NO via fits between adjacent pins. Record the loaded side's
     escape count in the part.yaml escape block; at placement (D-ADJ)
     reserve an explicit ESCAPE CORRIDOR on that side (open copper,
     staggered via rows at >=2x pitch) — or pick advanced tier / a
     wider-pitch part. (escape_check calibration for this class is pending
     the ADR-0008 board's measured outcome — do not trust "leaded: ok"
     alone for dense sides.)
   - **D-LAYOUT, datasheet LAYOUT-section read at part selection — the THIRD
     read after pinout and package.** For every IC + power/sense part, read
     the datasheet's Layout/Application-Information section AND its reference
     design / EVM / app note, and encode the placement rules the chip demands
     into a `layout:` block: `source:` (the section/EVM cited), and a
     `keep_short:` list of nets with `max_span_mm` budgets (use
     `partner_refs:` whenever the requirement names a particular capacitor,
     inductor, shunt, or other consumer; the parts that must
     hug the chip — sense R Kelvin-back, pass FET at the gate pins, decoupling
     local, hot loops tight). The floorplan is then ADAPTED FROM the reference
     layout, never authored against it. ENFORCED: `policy_audit` **P-LAYOUT**
     fails an in-scope part with no block; **P-ADJ** measures each board net's
     pad-span against its budget. `policy_audit.py --phase placement` runs the
     same P-LAYOUT/P-PREC/P-ADJ/P-ADJ-PAIR/P-ADJ-UNREACHED implementation
     immediately after board generation and placement gates, and MUST pass
     before rules or routing begin; it writes `06_build/placement_policy_audit.md`
     without replacing the full release audit. Motivating miss (usb-hub-3s-v2
     TPS25740A, 2026-07-22): pinout (S-VER) + package (P-ESC) both passed, but
     the Layout section (pass FET + sense R + VBUS caps HARD against the
     power-stage pin edge) was never read; the FET row went 7mm off the edge
     across a channel and four QFN escapes could not coexist — a wall found
     only after ~8 routing rebuilds. P-ADJ catches it at placement.
   - **D-TIER, fab tier is a COST CEILING declared at commission.**
     `03_src/rules/nets.yaml` `fab_tier:` names a tier from
     `fab_tiers.yaml` and defaults to the CHEAPEST plausible tier;
     ENFORCED: `policy_audit` P-TIER fails any part whose tier_required
     exceeds it. To accept a costlier tier: write the tier ADR
     (options + why the cheaper tier fails), raise `fab_tier:`, and put
     the tier's exact `order_readme` line in the ORDER_README. ADVANCED
     (0.25/0.15mm vias, via-in-pad) is proven orderable (usb-power-3s
     v1.0-1.3). Do not discover the tier at the DRC gate (symptom:
     drill_out_of_range on router-emitted small vias).
   - **D-ADJ, adjacency placement is part of the DESIGN.** Region/anchor
     placement is electrically blind (golden rule 7). The floorplan MUST
     place each bootstrap cap, feedback divider, decoupler, and CC/config
     resistor HARD AGAINST the pin it serves, and rotate dense packages so
     their hard nets (BST/SW/FB) face open copper. An "escape failure" on
     a short-local net (bootstrap, CC) is almost always a stranded passive,
     not a routing problem.
     **IF THE BOARD'S DELIVERABLE IS A RADIO PROPERTY — impedance, phase or
     isolation — READ `kicad-pcb/references/rf-design.md` BEFORE PLACING.**
     It carries Ossmann's five rules (cited), the numeric guidance external
     sources give, the places those sources DISAGREE with this repo, and four
     things this fleet measured that no general RF guide covers. Two checks in
     it belong at THIS stage and refuse an impossible board in milliseconds:
     the OCTILINEAR FLOOR from pads alone (an octilinear router makes "equal
     length by construction" FALSE of copper — measured 0.3238 mm Euclidean
     spread against a 1.4966 mm floor, 19.74 deg at 6 GHz), and MIN LANDABLE
     WIDTH per pad against the netclass floor (a vendor land left 0.350 mm
     where a 0.36 mm trace needed 0.380, and six of eleven RF nets would not
     route). Both were found by routing for hours; both are pad arithmetic.
          **ARCHETYPES FIRST — placement is ADAPTATION, not derivation.**
     Before drawing a floorplan, check
     `kicad-pcb/references/floorplan-archetypes.md` for this board's
     CLASS (power-hub, sensor-chain, …): a proven placement shape with
     the adjacency groups and escape corridors already drawn. Adapt it to
     this board's parts; derive from scratch only for an unprecedented
     class — and then HARVEST the new shape into the archetype file at
     release (same compounding rule as proven-parts).
     **LAYOUT PRECEDENT SEARCH (for every HARD part: dense escapes,
     switching power, >0.5A analog, RF).** Do not invent the local layout
     from first principles when a routed reference exists. In authority
     order: (1) the part datasheet's Layout Guidelines/Example figure —
     canon M6: the manufacturer's own routed picture WINS over your
     derivation; (2) **any OPEN-HARDWARE REFERENCE DESIGN WITH PUBLISHED
     LAYOUT — the manufacturer's EVAL BOARD / EVM design files first, but
     NOT ONLY those** (EVM layouts are tested instances of the exact local
     circuit — study the escape pattern, hot-loop shape, sense-line dress,
     via strategy); (3) OSHWLab/EasyEDA open projects SEARCHED BY LCSC
     CODE — real JLC-fabbed boards using the exact part, copper viewable;
     (4) open KiCad projects (GitHub/Kitspace; unvetted — weakest).
          **AN EDITABLE DESIGN FILE OUTRANKS A RENDERED FIGURE, and that
     is a difference in EVIDENCE, not convenience.** A figure is read by
     eye at whatever DPI the PDF happens to carry; a design file opens in
     KiCad and is MEASURED. So a tier-1 datasheet figure does not
     discharge tier 2 when design files exist — check for them explicitly,
     and check the LICENCE while you are there, because a permissive
     licence is what makes the file openable at all. It never licenses
     copying: study-then-re-derive is canon M3 regardless of licence.
     THE WORKED CASE (canon P-PREC): pluto-rx2-8way read the RP2040's
     Figure 6 visually at 200 dpi off a raster, while Raspberry Pi
     publishes a "Minimal Viable Board" reference design **in KiCad**
     (schematic + PCB) and the Pico / Pico W designs in Cadence Allegro,
     free, at raspberrypi.com/documentation/microcontrollers/rp2040.html,
     under "permission to use, copy, modify, and distribute ... for any
     purpose, with or without fee" (verified 2026-07-30).
          **THEN ASK WHETHER THE PRECEDENT TRANSFERS — the reference's
     SURROUNDINGS ARE PART OF ITS EVIDENCE, and this is the half the
     search kept missing.** A reference proves its local pattern works IN
     ITS OWN NEIGHBOURHOOD. Before adopting it, compare the neighbourhoods:
     how much free space does the reference leave on each side of the
     part, and does THIS board leave the same? If the reference has open
     room on four sides and your floorplan pushes the part to an edge, or
     puts an RF star in the middle of what was empty, then the LOCAL
     decisions (adjacency, decoupling rows, orientation) may still hold
     while the ESCAPE BUDGET does not — and the escape budget is what
     bites at stage 6, not the decoupling. Do the arithmetic at PLACEMENT:
     escapes per side x (track + clearance) against the band you have
     actually left. Measured on pluto-rx2-8way: 8 escapes on the north
     0.400 mm side into a 3.2 mm band is exactly 8 x (0.25 + 0.15), and
     that board carries 28 unconnected nets and 21 via-clearance findings
     in the MCU field. The RP2040 consult was careful and correct about
     the flash corner and the decoupling; NOTHING IN THE PROCESS ASKED
     whether the fanout survived a different surrounding.
          STUDY, THEN RE-DERIVE: extract the decisions (adjacency,
     orientation, corridor, layer drops) into part.yaml gotchas +
     floorplan.yaml — NEVER import copper (canon M3). Record what you
     consulted as a `layout_refs:` list in the part.yaml, and **use the
     GRADED MAPPING FORM** — `{tier:, artifact:, reached:, why:}` — so the
     record says which authority tier was actually reached and names what
     was NOT (canon P-PREC, graded by `policy_audit.py`). THE LADDER MUST
     NAME ITS CEILING: stopping at tier 1 is often the right call, but it
     must be a stated call, with the stronger artifact named and the
     reason given. Harvest into proven-parts.yaml with the part — the
     precedent search is paid once per part, ever. Full source catalog,
     search technique per source, and the study-vs-copy rules:
     `kicad-pcb/references/layout-precedents.md`.
**A DOSSIER MAY BE DELETED, BUT NOT SILENTLY (canon M-DEPEND).** `02_parts/`
is the MPN authority for EVERY sealed release, not just this board, so removing
a dossier — or moving its `sourcing.lcsc`/`mpn:` — can break an immutable
archive. It is NOT append-only: three legitimate outcomes are keep the dossier,
keep the retired code resolvable as a **mapping-form** `alternates:` entry, or
move the code->MPN fact to the vetted ledger. Graded by
`sealed_dependency_check.py`. Measured: 539 rows across 25 of 33 sealed releases
resolve ONLY because a dossier is still in the tree.

For module-first coverage, a dossier retained only for an immutable historical
release belongs in `integration.yaml` `historical_dossiers:` rather than a
false live selection. P-MOD accepts that declaration only when the dossier's
exact MPN and primary LCSC identity are absent from live TSX authoring source;
if either token remains, retirement fails closed.

3. `03_src/rules/nets.yaml` + `generate_rules.py` BEFORE any layout.
4. `03_src/rules/electrical_invariants.yaml` — the INTENT gate (canon E-INV):
   every protection/topology ADR emits netlist assertions (`pin_on_net`,
   `series_chain`, `net_has_part`) so intent-vs-netlist is machine-checked, not
   just self-consistency. This is the gate the D1 reverse-polarity defect
   needed. `electrical_invariants.py --adr-coverage` (E-ADR) flags a protection
   ADR that emits none.
5. **`03_src/rules/nets.yaml` `length_match:` — REQUIRED THE MOMENT TWO PATHS
   MUST HAVE THE SAME LENGTH** (canon R-LEN). Without it `copper_length_audit`
   reports UNREACHED and you route with NO gate on the property the board sells.
   Size `max_spread_mm` from **DRIFT** (`d_tau = TC*dT*dL*t_pd`), never from a
   desired match: a tolerance tighter than the part's own relative-phase window
   is not physics. **CHECK THE OCTILINEAR FLOOR FROM PADS BEFORE ROUTING** —
   KRT is octilinear, so `max(dx,dy)+0.4142*min(dx,dy)` is the shortest copper
   it can lay, and a ceiling below that is excluded by the router's MOVE SET,
   not by effort. `elongation: meander` opts out and is cross-checked against a
   real `length_match_group` in `route.yaml`. The knob is `meander_amplitude`,
   NOT `length_match_tolerance`.
6. **`03_src/rules/nets.yaml` `scoped_clearances:` — the launch-local relaxation**
   (canon R-SCOPE), when a pad cannot emit its class width at the board-wide
   clearance. **`why:` AND `nets:` are both REQUIRED and the emit is refused
   without them**, for a stronger reason than the `scoped_floors` width case: a
   width relaxation is bounded below by ampacity and A-AMP grades it
   independently from `current:`, but **an isolation relaxation has NO
   downstream grader at all** — DRC simply stops reporting what the rule
   permits, so unexplained it is silent by construction. Clearance is a property
   of a PAIR, so "every pair inside this box" is not an isolation argument.
   When a launch will not route the ranked causes are **grid, then clearance,
   then width** — a neck-down is REFUTED as the remedy (measured: it delivers
   150 mm at the narrow width and 0 mm at the wide one).

## 4-6. Generate, place, route — all regenerable from 03_src

**RF BOARDS ROUTE DIFFERENTLY, AND THE OBLIGATIONS ARE IN
`kicad-pcb/references/rf-design.md`.** If the deliverable is impedance, phase or
isolation: route RF FIRST on ONE layer with NO VIAS inside a phase-critical arm;
EXCLUDE the reference layer from the routing layers so the plane under a matched
group cannot be cut (this is Ossmann's rule 1, and one board arrived at it
independently — nine arms share one unbroken reference, "what makes their phases
comparable at all"). Where two paths must MATCH, prefer a DETERMINISTIC transform
over a stochastic route — but VERIFY WHICH TRANSFORM: on one board a +14.5 mm
translation and a reflection about y = 55.000 coincide for every part the
symmetry gate grades and diverge at the splitter, so the transform is PER-NET and
the gate cannot tell them apart. And the published RF artifact — a delta, a
spread — is MEASURED FROM ROUTED COPPER, never asserted from placement: a
placement gate that reports "the delta is a placement property, not a routing
outcome" is asserting something a stochastic octilinear router can falsify.

Every new board carries `03_src/rules/rf.yaml`. `rf.enabled: false` requires a
rationale; `true` activates a dedicated subpipeline with three independent,
exact-artifact phases: RF schematic review before placement, RF PCB review
before layout seal, and RF Gerber/fab review before prototype ordering. Follow
`rf-schematic-review-protocol.md`, `rf-pcb-review-protocol.md`, and
`rf-fab-review-protocol.md`; `rf_contract_check.py` derives coverage from the
contract's requirement IDs and refuses zero/partial coverage. A fab-ready
prototype remains distinct from production authorization: production waits for
the contract's first-article VNA/TDR acceptance measurements.


Build `03_src/` generators + `rebuild_all.sh` (set -euo pipefail) in the
canonical order. **Schematic authoring — tscircuit/TSX is THE standard,
schwriter2 is FALLBACK-ONLY (ADR-0002 Phases D+E, migration COMPLETE):**
(1) the go-forward path is **tscircuit/TSX driving the SHARED GENERIC BACKEND**
(ADR-0002 amendment 2026-07-23): a board carries CONFIG, not a backend — the heavy
generators are shared (`kicad-pcb/scripts/generate_board_generic.py`,
`route_and_stitch_generic.py`, the converter; proven in
`docs/generic-generator-proof.md`), and a NEW board writes **ZERO board-specific
generation Python**: seed `templates/03_src/rebuild_all.sh` + the config files and
fill the values. A bespoke `03_src/generate_board.py` is the EXCEPTION (a board the
generic backend cannot express — write an ADR if you believe you need one).
`scripts/tsx_to_board.sh` is RETROFITTED for the generic backend (2026-07-23):
`generate_board.py` absent + `floorplan.yaml` present → it runs the generic chain
(generate_board_generic / route_and_stitch_generic / generate_rules_generic) in its
isolated build root; bespoke boards keep the old path. The canonical per-project
rebuild drivers remain `rebuild_all.sh` (full, from tsx) and `rebuild_reuse.sh`
(promoted-chain fast variant — use it for per-iteration/verification rebuilds;
`rebuild_all.sh` only when the schematic changed, because `tsci build` is
non-deterministic and the committed `.kicad_sch` is the pinned canonical). The
chain either driver runs: `tsci build` → converter
`.kicad_sch` → placement → generate_rules → KRT (reuses the promoted route chain)
→ stitch_and_fill → generate_rules LAST → DRC 0/0/0. For schematic-only render
use `gen_tscircuit.sh <project>` (default = the BRIDGE ONLY: circuit.json,
schematic.svg/.pdf, converter `.kicad_sch`, ERC + netlist-parity gate; pass
`--study` for tscircuit's own PCB/gerber/3D second-opinion render, which is never
a fab source). The converter (`circuit_json_to_kicad_sch.py`, default `--mode
layout` = WIRED, retires S6) folds canonical nets + FPIDs from `02_parts` in with
no per-board adapter — see `kicad-pcb/references/tscircuit-folder.md`. Author each
specialty part with `supplierPartNumbers={{jlcpcb:["C…"]}}` so its FPID resolves,
and add a `net_aliases.txt` line for any leading-digit rail (`12V`→`N12V`).
**COUNT EVERYTHING (S-COUNT — tsci drops parts SILENTLY):** before the first
`tsci build`, run `kicad-pcb/scripts/tsx_preflight.py <project>` — alphanumeric
pads (USB-C `A1..B12`, shield `SH`) are rejected by tscircuit WITHOUT an error
and the part vanishes with ERC still 0 (2026-07-21: four USB connectors, 48/52).
Author `03_tscircuit/manifest.yaml` (`components: [C1, R1, …]` — your declared
refdes list) alongside the tsx, and gate the schematic AND board stages on
**GATES ADDED 2026-07-29/30 — RUN THEM; NONE WAS IN THIS DOC UNTIL NOW, WHICH IS
THE SAME "DECLARED BUT NOTHING READS IT" DEFECT THEY EXIST TO CATCH.**
`net_reference_audit.py` (**E-NETREF** — every net name a rule file or dossier
references must EXIST; measured 64 of 908 fleet references were ghosts, every one
a `keep_short` budget, and one reached SHIPPED SILK) · `sealed_dependency_check.py`
(**M-DEPEND**, above) · `copper_length_audit.py` (**R-LEN**, incl. the octilinear
floor) · `adr_bound_provenance.py` (**M-BOUND** — a published inequality is
REGENERATED, and the nearest standard value under it is re-evaluated at the
declared corner; a bound whose only admissible value fails is a FAIL, not a
rounding note) · `schema_reader_audit.py` (**G-ORPHAN** — every schema key names
the gate that reads it, and that gate must PROVABLY read it) ·
`gate_contract_audit.py` (**G-VACUOUS** — every gate declares the input on which
it PASSES while its subject is FALSE, with a fixture; **G-SELFCON**; and
`--dru` grades a `.kicad_dru` predicate that can never fire) ·
`build_provenance.py` (**M-FRESH** — the artifact a gate grades must be the one
the build just wrote) · `trace_audit.py --subject .` (**GG-SHADOW** /
**GG-RESOLVE** — the OBSERVATION arm of M-COVER: every gate above prints `N/M`,
and this one traces a derived battery of them to check that N and M describe the
board they were pointed at. Driver step [10c], advisory. On an ADR-0007
two-board project it names, unaided, every flat `03_src/rules/<name>` gate that
grades ONE board and reports on the PROJECT).

**GG-SHADOW's "nothing in the run opened it" IS A FLEET UNION OVER EVERY TRACE,
AND A TRACER WRITES ONE TRACE PER PROCESS.** A gate that hands each board to a
worker subprocess is graded on what its children read too. **IF YOU ARE PICKING
UP THE PER-BOARD PATH RESOLUTION OWED FOR ADR-0007, READ THIS FIRST**: that
remedy is naturally built as a dispatcher (`03_src/rebuild_all.sh` already is
one; `adr_bound_provenance.py` and `waiver_provenance.py` already spawn
subprocesses), and with the per-trace read-set that shipped, THE FIX FOR THE
DEFECT GG-SHADOW FINDS WOULD HAVE MADE GG-SHADOW FIRE — a ratchet breaking on a
correct action, on a correctly-fixed board. MEASURED on two gates with the
identical 2-file read-set: dispatcher RAW EXIT 1 with 2 false findings,
in-process twin RAW EXIT 0 with none. Fixed by `opened_union()`; fixtured by
`tests/fixtures/gg_dispatch/`.

**READ GG's READ COUNT WITH ITS CAVEAT, AND NEVER QUOTE IT WITHOUT ONE.** It is
a SUPERSET of subject evidence: it counts ANY PRE-EXISTING FILE ANY GATE HAPPENS
TO OPEN, because neither the write-set (a METHOD test) nor the pre-run snapshot
(an EXISTENCE test) is an IDENTITY test. MEASURED — a genuinely-blind board
exits **3** bare, **0** with `06_build/policy_audit.md` (a gate's own output),
and **0** with `01_docs/BRIEF.md` holding three lines of PROSE that are nobody's
output and are graded by nothing. The exhaust case is the worst instance, not
the boundary. **Only the ZERO carries a verdict**: an empty read set is exit 3
GRADED NOTHING and is never a pass. A nonzero one is a raw number, and this
layer's predecessor was stopped for printing it as a certificate.
`design-policies.md`'s `GG-* mechanics` section carries both controls.

**M-FRESH IS WIRED INTO THE DRIVER, NOT RUN BY HAND, AND THAT IS THE POINT.**
`rebuild_all.sh` stage **[0b]** stamps BEFORE `tsci build` and stage **[1a]**
verifies between the build and the converter, so the pipeline ASSERTS the
identity instead of resting on one correct path. `tsci build` writes
`03_tscircuit/dist/src/<TSX>/circuit.json` and **never writes `build/`** — the
driver's `cp` is what connects them, and its absence is the 2026-07-30
pluto-rx2-8way-v2 defect: the converter consumed a superseded
`build/circuit.json` and **TSX-PRE, S-NETMERGE, E-INV, E-ADR, E-TOPO, E-MARGIN,
S-COUNT, E-NETREF and M-BOM all reported green on an obsolete pad-numbering
scheme**, caught only by a by-hand netlist read. **No checker was wrong**; they
graded exactly what they were handed, and the stale bytes are valid json, so no
parser-shaped gate could ever have seen it. The equality is sha256 across two
independently-resolved paths, so a `touch` cannot forge it (`F-PATH`), and the
knob check (`F-KNOB`) fires at `stamp` — the same board carried the TEMPLATE's
own `BOARD=power3s` through four commits, meaning its full driver had never run
while its stage gates reported green one at a time. Fleet state:
`build_provenance.py audit --root .` names every board as adopted / OWED /
UNREACHED and prints **NOTHING GRADED ... This is NOT a pass** when nothing
stamps. **A board whose driver predates this is reseeded from
`templates/03_src/rebuild_all.sh` at its next revision — never retro-edited.**

**A ZERO EXIT FROM `tsci build` IS NOT A ZERO-DIAGNOSTIC BUILD.** The tool can
write `circuit.json`, print “completed with errors,” and still return success.
Run `circuit_json_diagnostics.py` immediately after copying the fresh artifact:
any embedded `*_error` is a hard **TSX-DIAG** stop; embedded `*_warning` records
remain visible counts because supplier-fetch and source-style advisories are
not electrical failures. This boundary precedes M-FRESH and semantic parity:
those gates can correctly certify the identity and connectivity of an artifact
whose own producer has already rejected its pad geometry.

**A WAIVER'S NUMBER IS REGENERATED, NOT TYPED** (canon M4). Load-bearing numbers
carry `evidence: {command:, output:}` and `waiver_provenance.py` re-runs and
diffs them. Measured: 16 of 22 fleet waivers rest on a typed number and ONE
REVERSES ITS OWN CONCLUSION when re-measured (typed 2.62 mm, measures 3.085 mm,
against a 3 mm budget it claimed to be inside). A tolerance must be SMALLER than
the margin it lives inside, or it cannot distinguish pass from fail.

`kicad-pcb/scripts/count_parity.py <project>` — generated artifacts all agree
with each other after a silent drop; only declared intent disagrees.
**Two audiences (ADR-0002 Phase A):** the human schematic document = tscircuit's
OWN render (`build/schematic.pdf`, shipped in the release); the converter
`.kicad_sch` is the machine artifact only (ERC/netlist/parity, need not be pretty).
Compose proven subcircuits from the module library (`tscircuit_modules/`) where one
exists (ADR-0002 Phase C). (2) **schwriter2 declarations** are RETAINED as the
FALLBACK for footprints tscircuit can't yet express (structure-only;
path/subcircuit/net-object API — canon S-DSL); not deleted, still valid, but no
longer the co-standard. EITHER path feeds the SAME downstream: generate_schematic
(or the converter) with no_connect flags for every sanctioned float; wire the
story-critical paths per canon S6 →
**ERC gate** (`kicad-cli sch erc --severity-all` = 0 errors) →
netlist-parity gate → **CHEAP SEMANTIC BATTERY at the SCHEMATIC gate** —
seconds each, run HERE and not first at seal (a defect authored at this
stage and caught at seal costs a superseded release; R12/R30 shipped in
2 sealed BOMs before the check ran, 2026-07-23): `early_design_check.py`
(D-SPEC/E-PATH/E-SWDRV/E-SURGE) first, then `net_label_survival.py`
(S-NETMERGE — every schematic global_label survives to the exported netlist;
the crow net-merge class) + `electrical_invariants.py`
(E-INV, + `--adr-coverage` E-ADR) + `power_topology.py` (E-TOPO/E-MARGIN/
E-OFF) + `count_parity.py` (S-COUNT) + `bom_source_check.py --circuit-only`
at the SCHEMATIC gate (no BOM needed — the R12/R30 class dies when the tsx
builds) + `pre_route_review_check.py . --phase schematic` (PR-REVIEW: an
independent topology review says `SOUND` and binds the exact electrical netlist
and aggregate parts bytes before placement or routing spend; the netlist digest normalizes
only KiCad's volatile export clock and instance UUIDs so a no-change re-export
does not invalidate the review; missing, DEFECTIVE, stale, and
unadopted evidence all stop), then legs A+C again at the FIRST fab-BOM export (early, never
seal-first) — per-refdes LCSC
identity vs circuit.json AND decoded-MPN-catalog-value vs the BOM label →
generate_board — placement is hand-coded OR
**placement-as-code** (`circuit_json_to_kicad_pcb.py` lands parts at the TSX
`pcbX/pcbY`; ADR-0002 Phase B — authored coords only, NEVER tscircuit auto-place,
then legalize) → audit gate (polarity,
proximity, plane-clean, refdes-on-silk) + `placement_gates.py
04_kicad/<board>.kicad_pcb --config 03_src/placement_gates.json` (SHARED:
P-OUT pads-inside-outline-polygon, P-CAP corridor crossing-demand vs
capacity, P-BODYCLR positive courtyard/body clearance — run BEFORE any
routing attempt; a corridor or collision FAIL is a
placement/topology decision, not a router tuning problem)
+ `critical_route_check.py .` (R-PAIRMAP: inventory completeness derived from
independent `nets.yaml length_match` intent, differential/seed source, layers
and via policy; direct route/prep/import entry points invoke the same gate)
+ `policy_audit.py . --board <board> --skip-drc --phase placement`
(SHARED: the authoritative P-LAYOUT/P-PREC/P-ADJ/P-ADJ-PAIR/
P-ADJ-UNREACHED subset; it MUST pass here, after placement and before
generate_rules or route import)
+ `pre_route_review_check.py . --phase placement --board <board>`
(PR-REVIEW: the schematic-side topology witness already bound the exact
netlist+parts before placement; now independent pin/layout/render reviews and
same-camera A-RENDER bind the exact placed board before routing. Missing,
DEFECTIVE, or stale evidence blocks. These early lenses do not replace the
fresh routed-release lenses.)
+ `import_provenance_check.py <project>` if the board carries
`03_src/rules/mates.yaml` (canon D-MATE: the floorplan is where a foreign
dimension becomes copper, so its grade is re-checked at the moment it is
spent — an ESTIMATED number with no error bar may not anchor a connector)
→ generate_rules
BEFORE route-prep
(the route-input .kicad_pro must carry the netclasses — canon R1) →
**tier_preflight (R-PREFLIGHT)**: route-stage entry runs `tier_preflight.py`
automatically (`route` refuses on FAIL; `--skip-preflight` is loud and
discouraged) — run `tier_preflight.py <project> --explain` when authoring
route.yaml, the fix lines are copy-paste → KRT
routing chain (fanout-first, track-free board, import once; promote the
final chain file to 03_src/route/ and commit it — canon M3) →
stitch_and_fill (pours + thermal vias) → `critical_route_check.py . --board
04_kicad/<board>.kicad_pcb --require-connected` (R-CRITESC) →
**generate_rules LAST** (pcbnew saves clobber netclasses) → DRC gate:
`kicad-cli pcb drc --severity-all --refill-zones --schematic-parity`
must report **0 violations / 0 unconnected / 0 parity** at FULL severity.
At route entry run `pcb_flow.py preflight <project>`: on adopted projects it
composes P-MOD first, then P-PINMAP, P-ESC, P-LAND/P-PADSEP, the
placement-policy P-ADJ subset, and R-PREFLIGHT before router spend.
`pcb_flow.py layout-seal`
performs a canonical rebuild plus a fresh 0/0/0 gate and records timings; its
fresh-board P-LAND gate runs after that rebuild and before DRC. Its verdict is
PCB LAYOUT scope only and never substitutes for the jlcpcb-fab
fabrication/assembly release battery.
**THE GRIND IS MECHANICAL FIRST, JUDGMENT SECOND:** iterate with the CHEAP
loop — `route_and_stitch_generic.py quick` (seconds: connectivity +
copper-clearance verdict on the pre-stitch board) — and run
`kicad-pcb/scripts/grind_driver.py` for the classified fix loop: it
auto-applies only table-known batch fixes (`references/grind_fixes.yaml`),
journals every cycle (M9), and STOPS with an escalation report on a novel
class or the D-BACK trigger — your judgment is for the escalations, not
the loop. For stochastic route quality, `route --race N` runs N
candidate chains and keeps the quick-measured best.
**RUN THE GRIND AT THE LOWEST TIER THE LOOP PERMITS (cost discipline).**
The routing grind is mostly MECHANICAL, so it should not burn a frontier
model. Three tiers, escalate only when forced:
- **Tier 0 — no model:** `grind_driver.py` itself. Its classify→
  table-lookup→auto-fix→rebuild→re-measure loop is pure script; the
  bounded D-BACK + subset-plateau stops live in the code, not in model
  judgment. Everything it can auto-fix costs zero model tokens. Widen
  `grind_fixes.yaml` (canon M8) before reaching for a model.
- **Tier 1 — a CHEAP model** (Haiku/Fable): drives the grind_driver, reads
  its escalation reports, applies TABLE-CLEAR config fixes (widen a
  corridor, reorder a wave, add a declared seed-stub), journals, commits
  at gates. Safe at this tier because every gate is machine-MEASURED
  (`kicad-cli drc` cannot be talked into 0/0/0), canon M3 forbids
  hand-editing `04_kicad`, and the loop bounds are in the script.
- **Tier 2 — a frontier model** (Opus/Sonnet): invoked ONLY on a genuine
  D-BACK escalation — the "is this a placement problem, not a routing
  problem?" diagnosis and the upstream backtrack. Rare and short.
The Agent tool takes a per-agent `model`; compose a routing run as a cheap
operator that defers to frontier only on escalation.
Never hand-edit `04_kicad/`; fix the generator and rerun. Commit at each
green gate. Silkscreen carries BOTH the functional labels (terminal words,
pin map) AND every reference designator (F.SilkS, visible, de-collided) —
the audit's I8 check enforces the refdes rule; F.Fab keeps a copy for the
assembly drawing.

## 7. Verify — independent eyes, then release

**SCOPE THE BATTERY TO THE RELEASE TYPE (canon "Verification scoping"):**
the full battery below runs ONCE per MATERIAL design state — the initial
release, and again after any material change. A FIX-PASS release (targeted
diffs on an already-fully-reviewed state — diff-verify the BOM/board delta
first) still runs every MECHANICAL gate (they are seconds) but scopes the
REVIEW lenses to targeted confirmation of each changed item + ONE
integrated fresh-context lens — not the full multi-lens battery.
**EVERYTHING here runs against the PRE-SEAL STAGING archive** — a finding
must cost an edit, not a supersede (3 of one family's 4 seals were killed
by post-ceremony reviews, mean seal lifetime 5.6h, 2026-07-23); the seal is
cut only after the verdicts are in (07_releases contract, "Seal
procedure"). Each check compares against a reference the design didn't
produce (checker and checked must not share a method). **CHEAP MECHANICAL
GATES FIRST, expensive lenses LAST** — the lenses hunt unknowns, never
data defects a script catches (4 of 7 order-blockers on one board were
script-checkable BOM/CPL/format defects first caught by the 4-lens fleet,
2026-07-23). **PARALLELIZE the independent ones:** jlc_twin (network
fetches), the fresh-context PIN REVIEW, and the fresh-context RENDER
REVIEW share no inputs or state — launch them as CONCURRENT
sub-agents/background jobs and join before the policy audit (which
consumes their verdicts). Serializing them roughly doubles the stage's
wall-clock for no independence gain.

### A MANUAL STEP THAT FIXES A PRODUCER'S OUTPUT IS A DEFECT REPORT

**If you hand-copy, hand-rename or hand-fix ANYTHING on the way to a gate,
STOP and file it against the PRODUCER.** Do not do the fix and move on, and
do not "note it for later" — a pipeline step a human has to repair is a
defect, and repairing it silently converts a HARD failure into a PERMANENT
SILENT one.

THE INCIDENT, MEASURED. `export_jlc_package.py` wrote `fab/bom_jlc.csv`
while `07_releases/contracts.md` — and every seal — required `fab/bom.csv`.
Every prior release produced the correct names **BY HAND-COPYING**. The
hand-copy did not merely hide the bug, **it GUARANTEED it stayed hidden**:
every downstream gate always saw a correct tree, so the producer's defect was
UNOBSERVABLE BY CONSTRUCTION. It could not have been found by running the
pipeline, only by reading it.

The cost was not cosmetic. `A-STOCK` and `A-BUY` — two gates that exist
BECAUSE five sealed releases shipped failing stock evidence — resolve their
subject through `fab/bom.csv`. With the name absent they reached a ZERO
DENOMINATOR and emitted NOTES instead of failures. **The repair kept the
humans unblocked and left the machines grading nothing.**

MEASURED 2026-07-31 across the fleet's **90 sealed release dirs**: 37 carry
`fab/bom.csv`, 28 carry the legacy flat `bom.csv` at release root, 25 carry
neither — and **5 sealed archives contain BOTH `fab/bom.csv` AND
`fab/bom_jlc.csv`**. That last number is the fingerprint of the hand-copy,
sealed immutably into five releases, sitting in plain sight for weeks.
Nobody read it, because a tree that contains the right file looks right.

The symptom to watch for is the feeling of *"I'll just rename this"*. That
feeling is a bug report arriving, and the rename is the thing that discards
it. Same class as canon M8 (the third hand-written copy of a script is a
promotion, not a convenience) and M3 (everything must be regenerable from
`03_src/` + `03_tscircuit/` — a tree that only a human can assemble is not).

### A DECLARED FIELD WITH NO CONSUMER IS A DEFECT

A config field nobody reads is not a weak control, it is **the APPEARANCE of
one**: the value sits right there in the canon, so a reader checking whether
the requirement is captured finds that it is, and stops looking.

`skills/kicad-pcb/references/fab_tiers.yaml` carries the exact required
ORDER_README sentence per fab tier as an `order_readme:` field and **no
script reads it** — which is how `pluto-rx2-8way-v2`'s ORDER_README came to
name no fab option at all while **3446 of its 3496 plated holes** sit under
the no-fee tier's 0.30 mm floor.

Machine check: `tests/t1_contracts.py::t_declared_field_has_a_consumer`, with
a TIGHT per-file `ORPHAN_CEILING`. MEASURED 2026-07-31: **47 declared fields
across the 4 `skills/**/references/*.yaml`, 9 with no reader** (fab_tiers 1,
grind_fixes 6, proven-parts 2). The ceiling may only FALL, so wiring a field
up must lower its row in the same change — an honestly declared gap that
costs nothing is how this one survived. **When you add a field to a
reference yaml, add its reader in the SAME change**, or record it and say
who owes the consumer.

- `export_jlc_package.py` (jlcpcb-fab skill): produces `fab/bom.csv` +
  `cpl.csv`; LCSC flows from the TSX `supplierPartNumbers` via
  circuit.json — there is no per-board BOM-seeding script. An UNCODED line is
  a FAILED sourcing decision, not a style choice: it needs an
  `03_src/rules/assembly.yaml` entry with a closed-vocabulary `reason:`
  (`not_in_catalog`|`consign`|`user_supplied`|`dnp_by_design`|`mechanical`|
  `test_point`) and dated `evidence:` (the catalog query and its result).
  `consign` means PLACED — it is a sourcing class, not a population class.
  A part that is not populated must ALSO leave the CPL
  (`FP_EXCLUDE_FROM_POS_FILES`): a blank-LCSC CPL row tells JLC to place a
  part it cannot source (cooksense v1.1 shipped 13 of them).
- `bom_source_check.py fab/bom.csv circuit.json --parts 02_parts`: legs
  A+C — per-refdes LCSC == source, AND every R/C row's MPN-decoded catalog
  value == its BOM label (the R12/R30 wrong-part class: 2 sealed escapes
  before this gate existed, 2026-07-23). Re-run here even though it ran at
  the first BOM export — it now grades the STAGED fab set.
- `bom_legibility_check.py <staging_dir>` (canon **F-LEGIBLE**, ADR-0006):
  the same BOM graded the way JLC PARSES it rather than the way we wrote it —
  **F-MPN** (every coded row carries BOTH MPN and LCSC, resolved from
  `02_parts/<MPN>/part.yaml` then the vetted passives ledger, the two match
  paths AGREEING), **F-WORDS** (no Comment that is an LCSC code or a
  `simple_*` placeholder), **F-ENCODE** (decodes identically under UTF-8 and
  cp936). `bom_source_check` asks whether the value is RIGHT; this asks
  whether the recipient can READ it, and nothing did until one board's BOM was
  uploaded and its parts "were not being picked up by their web processing"
  with every semantic gate green. Ship the output as
  `verification/bom_legibility.txt`. **The exporter enforces the same three
  and exits 3**, so this is a re-grade of the STAGED bytes, not the only
  chance. `--allow-illegible-bom` is the loud escape hatch and marks the
  package NOT ORDERABLE. The order-time **F-ECHO** ritual (JLC's resolved BOM
  diffed back against ours; `bom_echo_gate.txt` is the worklist) is human by
  decision — there is deliberately no JLCPCB API integration.
- **A-ROT is enforced by the exporter itself and cannot be skipped**: it exits
  2 unless every CPL rotation resolves from a MEASURED per-LCSC row (or a
  footprint that MEASURES as its own 180-degree reflection). Clear a block with
  `jlc_rotation_measure.py BOARD REF=LCSC --row`, never with the footprint-NAME
  DB, and never from `jlc_twin`'s `jlc_offset` (canon M1/M-PROV). Then
  `jlc_rotation_audit.py --table` must be green. Any ref the export names in
  `rotation_human_gate.txt` goes on the JLC order-preview human gate before the
  first order (canon A-POL).
- `part_facts_check.py <staging_dir> --parts 02_parts` (canon **P-FACT**): the
  release graded against every part's OWN declared `asserts:` facts —
  pad-1 net polarity vs the netlist, BOM value, must-not-be-on-the-BOM, and
  the MSL statement in the order paperwork. `keepout_region` is DECLARED but
  DEFERRED (needs board geometry) and is named rather than silently passed.
  Adoption is opt-in per part; the coverage line prints how many part.yaml
  actually declare anything, so "we check part facts" cannot be empty.
- `jlc_stock_check.py`: every coded line in stock >= 5x need. The VERDICT
  line is the gate — read it. Five sealed releases across this fleet ship
  stock evidence whose last line says `FAIL` (one with the board's own CPU at
  stock 0) because nothing ever parsed it. A missing or unparseable verdict is
  a FAIL, not a skip.
- `jlc_twin.py BOARD bom.csv 06_build/twin --adjudications
  03_src/rules/twin_adjudications.yaml --assembly 03_src/rules/assembly.yaml`
  (coded not-assembled parts are checked too). Gate: exit 0 — zero
  unadjudicated MIRRORED / PAD-MISMATCH / PAD-GEOM; act on MODEL-SELF and
  POLARITY-CHECK findings; adjudications are evidence-backed per the
  jlcpcb-fab skill (pixel measurements, board_dx/board_dy nudges, NUDGE echo
  verified).
  **A ROT-DB-SUGGEST is a HUMAN BLOCKER you must clear before sealing** — it
  means the CPL angle disagrees with JLC's own CAD model for that LCSC.
  Resolve it by MEASURING (fit the board footprint against JLC's cached model,
  pads matched by NUMBER) and adding a row to
  `jlcpcb-fab/scripts/jlc_lcsc_rotations.csv` with the fit in the evidence
  column — never prose in a neighbouring row's evidence, which does not reach
  the resolver. The footprint-NAME table cannot express a per-part fact:
  C79924 and C7719 are both SOT-23-5 and need 180 vs 270.
  It is deliberately NOT yet an automatic exit-1 (canon A-ROT is HELD): the
  finding's own arithmetic was wrong until 2026-07-25, so promoting it would
  have certified a DO-NOT-ORDER release. `jlc_twin.xform()` used the opposite
  handedness to KiCad's real operator, negating every offset — invisible at
  0/180 (sign-invariant), exactly 180 deg wrong at 90/270. Because the
  per-LCSC table had been POPULATED FROM that finding, six of eleven rows were
  180 deg wrong, each overriding a correct name-DB entry; an external reviewer
  was misled by it, and crow-recorder-central-v2 v1.2 (correct) was "fixed"
  into v1.3 (DO-NOT-ORDER). The operator is fixed and pinned against pcbnew by
  test; A-ROT lands only once the whole table is re-derived independently.
  **The rule this bought: a gate must never derive its expectation from the
  artifact it is grading, nor from a table built by it (canon M1).**
- `twin_overlay.py BOARD 06_build/twin/twin_top.png --bare
  06_build/twin/twin_bare_top.png --side top --twin-dir 06_build/twin
  --bom fab/bom.csv --assembly 03_src/rules/assembly.yaml
  --adjudications 03_src/rules/twin_adjudications.yaml
  --twin-report 06_build/twin/twin_report.csv --crop-flagged --report
  06_build/verify/twin_overlay.md` (canon **A-RENDER**, BLOCKING). **Run it
  after jlc_twin and BEFORE the fresh-context render review — that review is
  worthless on a render nobody has proved is faithful.** It measures each
  body from the populated-minus-same-camera-bare pixel delta and compares it
  against the body position the
  BOARD implies (mesh bbox x JLC's own model transform x placement), so it
  cannot agree with a wrong mount by construction (canon M1). Run it on
  BOTH sides that carry parts; it REFUSES a perspective/iso render, a
  `--side` that contradicts the filename, and a side with no courtyards
  rather than drawing boxes it cannot trust.
  The populated and bare PNG dimensions must match exactly. The bare twin is
  generated by `jlc_twin.py` from the same board/camera with all 3D bodies
  removed; static copper, silk and mask pixels therefore cancel instead of
  masquerading as component bodies. Evidence-backed model/board nudges and
  rotation overrides are read from the same adjudication register used to
  build the twin, so expected and rendered geometry share the declared final
  transform rather than disagreeing because the checker ignored it.
  **Read the COVERAGE line, not the verdict.** Pixel extraction resolves
  large isolated parts and not dense 0402 fields, so coverage is partial by
  construction — on crow-recorder-central-v2 v1.5 it is `22 measured / 177`.
  Every uncovered ref is NAMED with its reason; a ref that should have been
  measurable and was not is a FAILURE, never an omission.
  The gate's own headline: run against the SEALED v1.5 render it FAILS on J2
  at centre delta 1.435 mm / outward 1.491 mm — the 90-degree-rotated USB-C
  that shipped in two releases past four review lenses, because `jlc_twin`
  mounted the body at a pad fit it had rejected in the same breath.
  A body outside its courtyard with expected and measured AGREEING is a
  MODEL defect with no board exposure (J1, 5.686 mm) — reported, never gated,
  because gating it buys a permanent waiver and canon M4 says an inherited
  waiver is a defect vector.
- Fresh-context PIN REVIEW: `pin_audit.py` dossiers -> new agents per
  part group following `kicad-pcb/references/pin-review-protocol.md`.
  Dossiers expose `pin_aliases`/`fused` declarations and select the vendored
  PDF whose bytes match `datasheet.sha256`; a neighboring variant selected by
  filename or directory order is not authority. Zero FAILs to proceed.
- Fresh-context RENDER REVIEW: a new agent reviews the twin renders +
  PDFs with no design context; triage every finding (fix or ADR-documented
  disposition).
- PDF set: `pcb_layers.pdf` / `assembly.pdf` via `kicad-cli pcb export pdf`
  (no per-board export script — the release contract names the files),
  visually verified via PNG export.
  **RENDER PAIR + MISSING-MODEL MANIFEST (standard, 2026-07-21):**
  every release ships BOTH views per side — `render_<side>_bare.png`, the
  no-components render made by `jlc_twin.py` with the exact SAME camera,
  projection, crop, and resolution as the populated twin, and the twin's
  modeled render — PLUS
  `verification/missing_models.txt`: every CPL ref with no attached 3D
  body in the modeled render. Incident: usb-hub-3s U1/Q5/Q6/Q7 rendered
  bodiless (JLC models unattached) and were read as UNPOPULATED by
  review — they were in the CPL all along. A bodiless footprint means
  "no model", never "not placed": the CPL is population ground truth,
  and the manifest converts the render comparison from eyeballing into
  a list. For tscircuit-authored boards the **schematic PDF = tscircuit's own
  render** (`03_tscircuit/build/schematic.pdf`), NOT a KiCad re-render (ADR-0002
  Phase A) — ship it as `pdf/schematic.pdf`.

- **RED-TEAM RELEASE REVIEW (standard, 2026-07-21; scoped + moved pre-seal
  2026-07-23).** Runs against the PRE-SEAL staging archive, breadth per the
  release type: an INITIAL release of a material state gets BOTH lenses
  below; a FIX-PASS release gets targeted fix-confirmation + ONE integrated
  fresh-context lens (canon "Verification scoping"). Reviewer INPUT is
  curated — for independence AND cost: the staging archive +
  `01_docs/{BRIEF,ARCHITECTURE,DETAIL_DESIGN,decisions/}` + `02_parts/` +
  `03_src/` config; **journals, learnings, STATUS, and 08_reviews are
  EXCLUDED** (a reviewer fed the designers' own narrative is no longer
  zero-context, and journal dirs run 40-70KB of token load per lens).
  Launch the lenses as zero-context ADVERSARIAL reviewer sub-agents told to
  hunt for defects, not confirm correctness:
  (a) **topology/protection/ratings lens** — trace protection chains from
  the NETLIST (reverse-polarity behavior incl. TVS directionality), check
  every clamp-vs-protected-part rating pair from part.yaml limits,
  recompute thresholds at worst-case corners, diff design docs vs the
  implemented BOM/netlist. TWO CHECKS THAT PASSED usb-hub-3s-v3 (2026-07-23)
  ON BOTH ZERO-CONTEXT REVIEWS AND ARE NOW MANDATORY, BY CONSTRUCTION:
    - **Setpoint-vs-load margin (E-MARGIN).** For every regulated rail
      feeding a KNOWN load, take the load's brownout/undervoltage voltage and
      compute (Vout_setpoint − Vbrownout); at Imax that difference is the TOTAL
      IR budget (mΩ) for board + connector + cable. State the real cable +
      connector + trace resistance and confirm it fits WITH margin — a thin
      budget browns the load out under load. (v3: 4.97V into a Pi5 UV~4.63V at
      5A = 68mΩ, less than a real 5A USB-C cable alone; both prior reviews
      computed 4.97V and neither judged the margin.) Confirm `power_tree.yaml`
      pins `load_uv_threshold` + `ir_budget_mohm` for such rails and E-MARGIN
      passes.
    - **De-energization / stored quiescent drain (E-OFF).** For any
      self-powered (battery/cell/pack) board, ask: HOW is it de-energized for
      storage/shipping — a master disconnect, or are converter EN pins tied
      always-on? What is the stored quiescent draw and pack self-drain time?
      Confirm the `off_control` declared in `power_tree.yaml` actually EXISTS
      in the netlist (a switch genuinely in series / EN genuinely gated), not
      merely asserted. (v3: both buck EN pins tied active, no switch — the pack
      self-drained in storage; no review asked how it turns off.)
  (b) **layout/thermal/power-integrity lens** — MEASURE the board with
  pcbnew (hot-loop spans in mm, switch-node zone areas + layer adjacency
  vs the stackup, gate-drive routing, thermal vias vs computed
  dissipation).
  Each returns P0/P1/P2 findings with cited evidence and **TWO verdicts,
  because a seal makes two claims** (canon M-REV, the review-side twin of
  A-BUY):

      design_verdict: SOUND | DEFECTIVE            # is the artifact CORRECT?
      order_verdict:  ORDER | DO-NOT-ORDER | BLOCKED-SOURCING

  **The SEAL gate reads `design_verdict`; the ORDER_README reads
  `order_verdict`.** `BLOCKED-SOURCING` exists precisely so a lens can say
  *this board is right and you cannot buy it today* without either half
  contaminating the other — and `order_verdict` is cross-checked against the
  release's own measured `SOURCING:` state in both directions, so it is a
  measurement-backed field and not a second opinion. A legacy single
  `verdict:` retrofits to both keys, conservatively (`DO-NOT-ORDER`/`FAIL`
  -> DEFECTIVE, so no sealed review is retroactively converted into an
  acceptance); vocabularies, the full retrofit table and the reasoning live
  in the `08_reviews/` contract. Verdicts are parsed as DATA, never scraped
  from prose: cooksense v1.5 shipped `VERDICT AT RUN TIME: **DO NOT
  ORDER.**` and it states no verdict at all. Reviews are archived VERBATIM in
  `08_reviews/` (see its contract: provenance header, DISPOSITIONS.md
  ledger; external reviews received are archived there too) and copied
  into the release `verification/` under the two contract-named filenames
  `redteam_topology.md` / `redteam_layout.md` — those exact names are what
  M-REV grades. The release report MUST include the
  **findings table** (finding | severity | evidence | disposition) and
  both verdicts. **A P0 finding blocks the release** — fix and re-gate, or
  supersede; P1s land in ORDER_README + the next-rev work order; P2s are
  recorded. **WHY THE ONE-FIELD FORM WAS RETIRED**: smc0985-cooksense v1.7's
  topology re-gate wrote *"I would accept the seal ... but sealing is not the
  question this verdict field asks"*, and eight successive sealing passes
  declined a board at DRC 0/0/0 with `policy_audit` FAIL=0. The lens and the
  gate never disagreed about anything physical. Rationale: internal gates prove artifacts agree WITH EACH
  OTHER; the D1 reverse-polarity TVS defect (usb-hub-3s v1.0, found by an
  external review 2026-07-21) passed ERC, DRC, parity, twin, and pin
  review because every artifact was consistently wrong together — only an
  adversarial fresh-context read of intent-vs-netlist caught it.

- POLICY AUDIT (final gate): `/usr/bin/python3
  <kicad-pcb skill>/scripts/policy_audit.py <project> [--board <04_kicad
  stem>]` — **one board per run**: the report header names the board graded,
  and M-REL / M-BOM / A-POP / A-BODY resolve the release from THAT board's
  series, never from the last directory in `07_releases/`. On a project that
  builds several boards, run it once per board with `--board`. Zero FAIL; any
  WAIVED entry evidence-backed in `03_src/rules/policy_waivers.yaml`; the
  HUMAN-graded items (schematic readability S6, decoupling S7, design-math
  S5) carry verdicts from the fresh-context reviews. Includes E-INV and
  E-ADR (canon E-INV): the netlist is graded against the intent assertions in
  `03_src/rules/electrical_invariants.yaml`, and every protection/topology ADR
  must emit at least one. Also the power-tree gates E-TOPO / E-MARGIN / E-OFF
  (converter topology, output-setpoint load margin, and a battery source's
  de-energization + stored quiescent draw, all from
  `03_src/rules/power_tree.yaml`). Ship `06_build/policy_audit.md` in the
  release's verification/.

Before cutting the release, HARVEST the ledger: every part this board
newly verified (shipped or fully twin/pin-verified) gets its entry in
`kicad-pcb/references/proven-parts.yaml` — function, LCSC, escape block,
the gotchas you paid to learn, provenance = this board's name. A resolved
`unresolved` function entry is the most valuable harvest of all.

Then cut `07_releases/v1.0-<date>/` per the release contract, following its
**"Seal procedure (normative — the 2-commit seal)"** section EXACTLY: stage
the archive → run every gate + review against staging → source commit S →
stamp MANIFEST (`git_sha: S`, `git_dirty: false`) + re-run M-REL/freshness →
seal commit adds ONLY the release dir → **refresh the STATUS beacon so it names
the release you just cut, and run `status_beacon_check.py` (canon M-BEACON)**.
That section is the ONE home for the seal dance (this file and
ORCHESTRATION_STATE.md only point at it).
Before the resulting design state is merged or pushed to the publication
branch, run `pcb-design/scripts/pcb_publication_gate.py --base <base> --head
<head>` and require `P-PUBLISH PASS`; this is the publication boundary, not a
substitute for any staging or seal gate above.
**Supersede modes — pick the one that matches the SHAPE of the fix.** A
supersede release seals against `release_freshness_check.py <release_dir>
--<mode>-supersede <prior-release-dir>`. Each mode is docs-only PLUS an
exemption for exactly the artifact that legitimately moves, and it then
asserts something STRONGER than identity about that artifact. **Never gate a
supersede with hand-written `--allow-identical` waivers**: an assertion the
gate makes beats a waiver a human writes (usb-hub-3s-v3 v1.11 shipped SEVEN,
every one machine-checkable — weaker evidence than the release it superseded).
The modes' ONE home is the `07_releases/contracts.md` "supersede mode"
sections; this is the index:

| what moved | mode | the extra assertion |
|---|---|---|
| documentation only | `--docs-only-supersede` | `fab/` `source/` `3d/` BYTE-IDENTICAL; ORDER_README + MANIFEST must DIFFER |
| a BOM row leaves | `--bom-only-supersede` | whole rows REMOVED, only for designators NOT on the CPL (canon A-POP) |
| a placement coordinate | `--cpl-only-supersede` | coordinate moves and/or dropped rows; a ROTATION/`Layer`/`Val`/`Package` change or an ADDED row FAILs (canon A-POS) |
| how the BOM READS | `--legible-bom-supersede` | only `Comment` + `MPN` move; this BOM PASSES and the prior FAILs `bom_legibility_check` (canon F-LEGIBLE) |
| WHICH PART is bought | `--sourcing-supersede` | `MPN`+`LCSC` move together; board md5 identical, CPL byte-identical, `.tsx` CHANGED, both codes in MANIFEST/README (canon M8) |
| a part's VALUE | `--value-change-supersede … --designators R4,R5` | gerbers/drills identical after the plot-timestamp strip; CPL delta confined to `Val` cells; BOM delta confined to the DECLARED refs |

**Value-change supersede** is the one to reach for when a resistor/capacitor
VALUE changes on parts that are ALREADY PLACED, and it is the case where "no
copper moved" and "BOM only" come apart. Measured 2026-07-28:
`export_jlc_package.py` reads `val = fp.GetValue()` **from the board** and
feeds that ONE string to BOTH the BOM `Comment` and the CPL `Val`, so a value
change moves the `.kicad_pcb`, the `.kicad_sch`, the `.net`, the BOM rows and
exactly those CPL `Val` cells while **all 11 gerbers and drills stay
byte-identical**. `--designators` is REQUIRED — the mode's whole assertion is
that the delta is confined to the refs you named, so it refuses a list that is
empty, too narrow (a change touching an undeclared ref FAILs) or too WIDE (a
declared ref that moved nothing FAILs). It also requires the SOURCE to have
moved (canon M3 — an unchanged `.kicad_pcb`/`.kicad_sch` means a hand-edited
CSV; editing the board alone leaves `--schematic-parity` reporting
`footprint_symbol_mismatch`) and each declared ref's `LCSC` to have moved with
its value, because a different value is a different part.
**A release is a COMPLETE, SELF-CONTAINED ARCHIVE — not a pointer to a git
SHA.** Someone
holding only that directory must be able to open the board, read the
schematic, check mechanical fit, see every gate's evidence, and re-plot the
gerbers. Six required parts:

- `fab/` — JLC order set: gerber zip, drill files, `bom.csv`, `cpl.csv`
- `pdf/` — schematic (on a tscircuit board = tscircuit's OWN render,
  `03_tscircuit/build/schematic.pdf`), pcb_layers, assembly
- `source/` — the EXACT artifacts the fab files came from:
  `<board>.kicad_sch`, `<board>.kicad_pcb`, the authoring `<board>.tsx`,
  and the exported netlist. **Copied, never symlinked.**
- `3d/` — STEP and/or GLTF where available (mechanical fit); note absence
  in the MANIFEST
- `verification/` — all evidence: DRC/ERC json, twin report + 6 renders,
  pin_review, render_review, policy_audit, parity
- `ORDER_README.md` (JLC options, rotation-preview checklist, hand-solder
  list, first-power ritual) + `MANIFEST.txt` — sha256 of EVERY file above,
  exact `git_sha`, `git_dirty: false` (inputs clean — scope
  `projects/<board>/ + skills/`, computed by `release_git_dirty.py <board>`,
  NOT the whole repo: a dirty sibling board does not block), gate summary

Releases are immutable; fixes mean a new release, a fix-claim needs its
falsifiable measurement in verification/, and superseded releases get a
SUPERSEDED.md pointer. **The completeness rule applies to NEW releases
only** — never retro-fill a sealed release to match it; cut a new version
and add SUPERSEDED.md to the old one.

## Report back

Final message to the user: decisions summary (with the protection ADR
called out), gate scoreboard, release path + git sha, open items for
order day (stock re-check, JLC preview rotation confirmations), and any
D# assumptions made in their absence.

**MARK EVERY LOAD-BEARING CLAIM AS MEASURED OR INHERITED.** A report is the input
to the next agent's brief, and a number that arrives unlabelled is treated as
fact by everyone downstream. Say `MEASURED (by me, <how>)` or `INHERITED (from
<source>, NOT re-verified)` — and put the inherited ones in their own list, so a
successor knows exactly which claims are load-bearing and unchecked.

This is the same discipline the gates already enforce on numbers in DOCUMENTS —
M-BOUND regenerates a published bound, M4 regenerates a waiver's measurement,
E-NETREF validates a reference, G-ORPHAN checks a declared key has a reader — and
none of them reaches a finding passed between agents. That is the hole it closes.

MEASURED, pluto-rx2-8way 2026-07-30: "the 28 unconnected are one MCU-field
congestion problem" was inherited from one agent's summary, restated in three
successor briefs as `STATE (measured, do not re-derive)`, and reported to the
user as the board's remaining risk. It was wrong in every part — four problems,
not one; 18 of 28 were two config lines; the 8 that were at the MCU were
arithmetic, not congestion. **An instruction not to re-derive is an efficiency
gain on a correct number and an error-propagation mechanism on a wrong one**, so
it may only be given about a claim the giver measured.
