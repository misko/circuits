---
name: pcb-design
description: "Full PCB design pipeline entry point: takes a design brief and drives it from commission to a verified, ORDERABLE-AND-ASSEMBLED JLCPCB PCBA release (/pcb-design <the board I would like to design...>). Use when the user wants a new circuit board designed end-to-end."
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
history beyond the live frame is pulled on demand, not preloaded).

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
  rules/{nets.yaml,power_tree.yaml,electrical_invariants.yaml}}`
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
  range + Imax, input envelope, protection posture, off-control, hard-cell
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

## 1-3. Design docs, parts, rules (order matters)

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
   **FAN OUT the research (parts are independent):** ledger hits
   (`references/proven-parts.yaml`) need no research — copy the verified
   block. Partition the REMAINING multi-pin parts into groups of ~4 and
   run them as CONCURRENT research sub-agents, each returning a complete
   part.yaml (pin map from the figure, escape block, layout_refs,
   gotchas). You merge, spot-verify the figure citations (S-VER), and run
   escape_check over the merged set — the gates validate the merged
   output, which is what makes the fan-out safe. Serial research on a
   16-part board wastes ~30 minutes for no verification gain.

   **Mandatory design-decision gates (D-ESC / D-TIER / D-ADJ)** — encoded
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
     `keep_short:` list of nets with `max_span_mm` budgets (the parts that must
     hug the chip — sense R Kelvin-back, pass FET at the gate pins, decoupling
     local, hot loops tight). The floorplan is then ADAPTED FROM the reference
     layout, never authored against it. ENFORCED: `policy_audit` **P-LAYOUT**
     fails an in-scope part with no block; **P-ADJ** measures each board net's
     pad-span against its budget (warn+waiver). Motivating miss (usb-hub-3s-v2
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
     derivation; (2) the manufacturer's EVAL BOARD design files (EVM
     layouts are tested instances of the exact local circuit — study the
     escape pattern, hot-loop shape, sense-line dress, via strategy);
     (3) OSHWLab/EasyEDA open projects SEARCHED BY LCSC CODE — real
     JLC-fabbed boards using the exact part, copper viewable; (4) open
     KiCad projects (GitHub/Kitspace; unvetted — weakest). STUDY, THEN
     RE-DERIVE: extract the decisions (adjacency, orientation, corridor,
     layer drops) into part.yaml gotchas + floorplan.yaml — NEVER import
     copper (canon M3). Record what you consulted as a
     `layout_refs:` list in the part.yaml (doc names/EVM ids/project
     links), and harvest it into proven-parts.yaml with the part — the
     precedent search is paid once per part, ever. Full source catalog,
     search technique per source, and the study-vs-copy rules:
     `kicad-pcb/references/layout-precedents.md`.
3. `03_src/rules/nets.yaml` + `generate_rules.py` BEFORE any layout.
4. `03_src/rules/electrical_invariants.yaml` — the INTENT gate (canon E-INV):
   every protection/topology ADR emits netlist assertions (`pin_on_net`,
   `series_chain`, `net_has_part`) so intent-vs-netlist is machine-checked, not
   just self-consistency. This is the gate the D1 reverse-polarity defect
   needed. `electrical_invariants.py --adr-coverage` (E-ADR) flags a protection
   ADR that emits none.

## 4-6. Generate, place, route — all regenerable from 03_src

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
2 sealed BOMs before the check ran, 2026-07-23): `net_label_survival.py`
(S-NETMERGE — every schematic global_label survives to the exported netlist;
the crow net-merge class) + `electrical_invariants.py`
(E-INV, + `--adr-coverage` E-ADR) + `power_topology.py` (E-TOPO/E-MARGIN/
E-OFF) + `count_parity.py` (S-COUNT) + `bom_source_check.py --circuit-only`
at the SCHEMATIC gate (no BOM needed — the R12/R30 class dies when the tsx
builds), then legs A+C again at the FIRST fab-BOM export (early, never
seal-first) — per-refdes LCSC
identity vs circuit.json AND decoded-MPN-catalog-value vs the BOM label →
generate_board — placement is hand-coded OR
**placement-as-code** (`circuit_json_to_kicad_pcb.py` lands parts at the TSX
`pcbX/pcbY`; ADR-0002 Phase B — authored coords only, NEVER tscircuit auto-place,
then legalize) → audit gate (polarity,
proximity, plane-clean, refdes-on-silk) + `placement_gates.py
04_kicad/<board>.kicad_pcb --config 03_src/placement_gates.json` (SHARED:
P-OUT pads-inside-outline-polygon, P-CAP corridor crossing-demand vs
capacity — run BEFORE any routing attempt; a corridor FAIL is a
placement/topology decision, not a router tuning problem)
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
stitch_and_fill (pours + thermal vias) → **generate_rules LAST** (pcbnew
saves clobber netclasses) → DRC gate:
`kicad-cli pcb drc --severity-all --refill-zones --schematic-parity`
must report **0 violations / 0 unconnected / 0 parity** at FULL severity.
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
- `twin_overlay.py BOARD 06_build/twin/twin_top.png --side top --twin-dir
  06_build/twin --bom fab/bom.csv --assembly 03_src/rules/assembly.yaml
  --twin-report 06_build/twin/twin_report.csv --crop-flagged --report
  06_build/verify/twin_overlay.md` (canon **A-RENDER**, BLOCKING). **Run it
  after jlc_twin and BEFORE the fresh-context render review — that review is
  worthless on a render nobody has proved is faithful.** It measures each
  body in PIXELS out of the PNG and compares against the body position the
  BOARD implies (mesh bbox x JLC's own model transform x placement), so it
  cannot agree with a wrong mount by construction (canon M1). Run it on
  BOTH sides that carry parts; it REFUSES a perspective/iso render, a
  `--side` that contradicts the filename, and a side with no courtyards
  rather than drawing boxes it cannot trust.
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
  Zero FAILs to proceed.
- Fresh-context RENDER REVIEW: a new agent reviews the twin renders +
  PDFs with no design context; triage every finding (fix or ADR-documented
  disposition).
- PDF set: `pcb_layers.pdf` / `assembly.pdf` via `kicad-cli pcb export pdf`
  (no per-board export script — the release contract names the files),
  visually verified via PNG export.
  **RENDER PAIR + MISSING-MODEL MANIFEST (standard, 2026-07-21):**
  every release ships BOTH views per side — `render_<side>_bare.png`
  (kicad-cli svg export of Cu+Mask+SilkS+Edge, rasterized: the
  no-components truth view) and the twin's modeled render — PLUS
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
  Each returns P0/P1/P2 findings with cited evidence and an
  ORDER / DO-NOT-ORDER verdict. Reviews are archived VERBATIM in
  `08_reviews/` (see its contract: provenance header, DISPOSITIONS.md
  ledger; external reviews received are archived there too) and copied
  into the release `verification/`. The release report MUST include the
  **findings table** (finding | severity | evidence | disposition) and
  both verdicts. **A P0 finding blocks the release** — fix and re-gate, or
  supersede; P1s land in ORDER_README + the next-rev work order; P2s are
  recorded. Rationale: internal gates prove artifacts agree WITH EACH
  OTHER; the D1 reverse-polarity TVS defect (usb-hub-3s v1.0, found by an
  external review 2026-07-21) passed ERC, DRC, parity, twin, and pin
  review because every artifact was consistently wrong together — only an
  adversarial fresh-context read of intent-vs-netlist caught it.

- POLICY AUDIT (final gate): `/usr/bin/python3
  <kicad-pcb skill>/scripts/policy_audit.py <project>` — zero FAIL; any
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
seal commit adds ONLY the release dir. That section is the ONE home for the
seal dance (this file and ORCHESTRATION_STATE.md only point at it).
**Docs-only supersede:** when a new release changes ONLY documentation, seal
it with `release_freshness_check.py <release_dir> --docs-only-supersede
<prior-release-dir>` — fab/source/3d identity to the prior is ASSERTED (any
deviation blocks: it is not docs-only), identical pdf/ allowed, ORDER_README
+ MANIFEST must differ, audit/manifest + draft-marker checks still gate.
Never waive fab-identical files one-by-one for this case.
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
