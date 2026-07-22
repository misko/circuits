---
name: pcb-design
description: "Full PCB design pipeline entry point: takes a design brief and drives it from commission to an orderable, verified JLCPCB release (/pcb-design <the board I would like to design...>). Use when the user wants a new circuit board designed end-to-end."
---

# /pcb-design — brief to orderable release

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
handoff loses nothing.

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
  `<pcb-design skill>/templates/03_src/{floorplan.yaml,route.yaml,rules/nets.yaml}`
  — then replace the values for THIS board. The keys are the contract the
  shared generic backend consumes; the values are yours to derive.
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
  If the user is absent, make the conservative choice, record it as D#
  with reasoning, and flag it in the final report.
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
   UVLO/over-discharge, OV, TVS clamp vs downstream ratings) — a
   clean-room run once shipped a LiPo board with zero UVLO because no
   stage forced the question.
2. `02_parts/<MPN>/part.yaml` per part: pin map read from the datasheet
   FIGURE (not assumed), `verified:` note naming figure+page, LCSC code +
   alternates + stock. The PDF set MUST include the package/land-pattern
   drawing, not just electricals.
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
(1) the go-forward path is **tscircuit/TSX**. An ESTABLISHED project rebuilds with ONE
command — `scripts/tsx_to_board.sh <project>` (Phase E). ⚠️ **It is a REBUILD driver: it
hard-fails without a pre-existing `03_src/generate_board.py` (+ stitch_and_fill, audit_board,
a promoted route chain) — it orchestrates a KiCad backend, it does not create one. For a NEW
board that backend is still hand-written and is the BULK of the work; budget it explicitly**
(clean-room finding 2026-07-20, ADR-0002 Phase E scope correction). The chain it runs: `tsci build` → converter
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
netlist-parity gate → generate_board — placement is hand-coded OR
**placement-as-code** (`circuit_json_to_kicad_pcb.py` lands parts at the TSX
`pcbX/pcbY`; ADR-0002 Phase B — authored coords only, NEVER tscircuit auto-place,
then legalize) → audit gate (polarity,
proximity, plane-clean, refdes-on-silk) → generate_rules BEFORE route-prep
(the route-input .kicad_pro must carry the netclasses — canon R1) → KRT
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

Run ALL of these; each compares against a reference the design didn't
produce (checker and checked must not share a method). **PARALLELIZE the
independent ones:** jlc_twin (network fetches), the fresh-context PIN
REVIEW, and the fresh-context RENDER REVIEW share no inputs or state —
launch them as CONCURRENT sub-agents/background jobs and join before the
policy audit (which consumes their verdicts). Serializing them roughly
doubles the stage's wall-clock for no independence gain. bom_seed +
jlc_stock run first (seconds, and twin consumes the BOM).

- `bom_seed.py`: 22/22-style unambiguous LCSC mapping; hand-solder THT
  lines deliberately uncoded and listed.
- `jlc_stock_check.py`: every coded line in stock >= 5x need.
- `jlc_twin.py BOARD bom.csv 06_build/twin --adjudications
  03_src/rules/twin_adjudications.yaml --also <REF=LCSC,...>` (include
  hand-solder parts with known codes). Gate: exit 0 — zero unadjudicated
  MIRRORED / PAD-MISMATCH / PAD-GEOM; act on MODEL-SELF and
  POLARITY-CHECK findings; adjudications are evidence-backed per the
  jlcpcb-fab skill (pixel measurements, board_dx/board_dy nudges, NUDGE
  echo verified).
- Fresh-context PIN REVIEW: `pin_audit.py` dossiers -> new agents per
  part group following `kicad-pcb/references/pin-review-protocol.md`.
  Zero FAILs to proceed.
- Fresh-context RENDER REVIEW: a new agent reviews the twin renders +
  PDFs with no design context; triage every finding (fix or ADR-documented
  disposition).
- `export_pdfs.sh`: pcb_layers / assembly PDFs, visually verified via PNG
  export. **RENDER PAIR + MISSING-MODEL MANIFEST (standard, 2026-07-21):**
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

- **RED-TEAM RELEASE REVIEW (standard, 2026-07-21 — runs on EVERY
  release).** After the pin/render reviews pass, launch TWO zero-context
  ADVERSARIAL reviewer sub-agents in parallel, each given ONLY the release
  archive + dev package (01_docs, 02_parts, 03_src) and told to hunt for
  defects, not confirm correctness:
  (a) **topology/protection/ratings lens** — trace protection chains from
  the NETLIST (reverse-polarity behavior incl. TVS directionality), check
  every clamp-vs-protected-part rating pair from part.yaml limits,
  recompute thresholds at worst-case corners, diff design docs vs the
  implemented BOM/netlist;
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
  must emit at least one. Ship `06_build/policy_audit.md` in the release's
  verification/.

Before cutting the release, HARVEST the ledger: every part this board
newly verified (shipped or fully twin/pin-verified) gets its entry in
`kicad-pcb/references/proven-parts.yaml` — function, LCSC, escape block,
the gotchas you paid to learn, provenance = this board's name. A resolved
`unresolved` function entry is the most valuable harvest of all.

Then cut `07_releases/v1.0-<date>/` per the release contract. **A release is
a COMPLETE, SELF-CONTAINED ARCHIVE — not a pointer to a git SHA.** Someone
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
  exact `git_sha`, `git_dirty: false` (CLEAN tree), gate summary

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
