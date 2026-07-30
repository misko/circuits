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
- **VACUITY (canon G-VACUOUS), the fourth obligation.** G-RED asks *can this
  gate fail at all* — 31/31 answer yes. G-VACUOUS asks *can it fail ON THE CASE
  IT EXISTS FOR*, and six gates were measured GREEN on 2026-07-28/29 with their
  subject false: `R-LEN` PASSes cooksense on the word `lengthens` in a comment
  about creepage; `keypad_isolation_6mm`'s `B.NetName != ''` exempts the shell
  tab it was written for (**1.0672 mm against a 6.000 mm constraint**, 106
  pairs); A-RENDER's verdict rests on **2 of 203** parts; `waiver_provenance`
  passed a waiver typed `2.62 mm` that measures **3.085 mm**, over the 3 mm it
  claimed; E-OFF is N-A on an undeclared cell; P-FACT prints `OK — 0/0` on a
  malformed assertion.
  **THE DECLARATION IS A FIXTURE, NOT PROSE** — a declared blind spot with no
  fixture is worse than an undeclared one, being the `keep_short` defect (39 of
  181 budgets naming a datasheet pin function) one level up. So: the gate's
  MODULE DOCSTRING carries a `VACUITY:` block AND `tests/` carries
  `@test(..., kind="vacuity", gate="<basename>.py")` constructing that input and
  asserting the gate PASSES. Both homes or neither — prose alone FAILS, an
  orphan fixture FAILS, a fixture whose FIRST assertion is `must_fail` is a
  FALSE declaration and FAILS (a `must_fail` CONTRAST after the subject is
  wanted), a fixture asserting nothing FAILS, and a fixture naming a gate
  outside the inventory FAILS so a rename cannot silently un-declare.
  The block is read from `ast.get_docstring` ONLY: a `VACUITY:` in a comment,
  nested docstring or code string does not count, because crediting text
  anywhere in a file is exactly R-LEN's defect.
  **DRU predicates count.** `--dru BOARD.kicad_dru` grades rule-file conditions
  against the board's own inventory (`dru_inventory`, geometry-free): a
  condition NO object can satisfy — a netclass, net or `insideArea` the board
  lacks — and a `NetName != ''` conjunct on a clearance-family constraint. A
  predicate that excludes its subject is worse than a silent Python gate,
  because it makes DRC itself report zero.
  **THE RATCHET:** coverage is reported for all 31 and every OWED gate is
  printed BY NAME; only a false declaration, a declaration without a fixture,
  and a drop below the committed `VACUITY_FLOOR` FAIL. Adoption is **5/31** as
  of 2026-07-29. Raise `VACUITY_FLOOR` in the SAME commit that adds a
  declaration; `t1_gate_contract.py t_vacuity_floor_is_pinned_to_the_measured
  _count` pins it to the tree from outside and refuses a lowering — that pin is
  what breaks the circularity, since G-VACUOUS itself passes a repo where
  nothing is declared and declares that blind spot in its own docstring.
- **NET REFERENCES (canon E-NETREF).** `net_reference_audit.py PROJECT_DIR`
  (`--root REPO` for the fleet, `--kinds` to print the denominator) grades
  ELEVEN enumerated kinds of net-name reference in hand-authored source —
  `nets.yaml`, `electrical_invariants.yaml`, `power_tree.yaml`,
  `02_parts/*/part.yaml`, `03_src/floorplan.yaml` including net-shaped tokens in
  silk caption PROSE — against the exported `.net`. Each kind carries a NAMED
  CONSUMER, which is the argument that a miss costs something; adding a kind
  without one is not allowed. Verdicts are RESOLVED / GHOST (fails) / UNREACHED
  (reported, does not fail), never a silent skip, and every unresolved name gets
  a near-miss diagnosis with its own counted denominator.
  WHY: cooksense v1.7 measured **10 of 123** referenced net names absent from
  its own netlist and the first fleet sweep **64 of 908** — a `GND_ISO` silk
  caption that reached the shipped F.Silkscreen, an eFuse input-decoupling
  `keep_short` addressed to `5V_SELV` so three real rails carried zero graded
  capacitors, and `supplies: {N3V3: 3.3}` hiding a whole rail from every
  `node_level` grade.
  **The oracle is read by a method the checked side does not share** (canon M1):
  two regexes over the netlist's `(nets ...)` section, NOT
  `electrical_invariants.py`'s s-expression tokenizer and not pcbnew — so this
  audit cannot inherit a parser bug from the gate whose narrow `supplies:` case
  it widens. `supplies:` STAYS owned by `electrical_invariants.py`, which can
  refuse at load time; the overlap on that one field is deliberate.
  **Matching is EXACT.** Only `nets.yaml` `classes.<C>.nets[]` honours `*`/`?`,
  because those become KiCad netclass PATTERNS. Substring matching is the defect
  that let `GND_ISO` pass a human read against `SPI_MISO`, and
  `t1_net_reference.py` pins it: the fixture asserts the gate FAILS *and* that a
  naive containment resolver PASSES the same bytes.
- **IMPORTED FACTS (canon M-IMPORT / D-MATE, ADR-0005 phase 3).**
  `import_provenance_check.py PROJECT_DIR` (or `--root REPO` for every board)
  grades the PROVENANCE of every fact a board consumes from hardware this repo
  did not design. Input: the board's `03_src/rules/mates.yaml` and the device
  record `spf/<device>/{README.md,facts.yaml}`. Findings: **M-EXIST** (the id
  exists AND its `quote:` appears verbatim in the human record, with the value
  inside it — a machine index drifted from its record is not evidence),
  **M-GRADE** (MEASURED/CITED/ESTIMATED/OWED; absent or unknown is a FAIL,
  never a skip), **M-BAR** (ESTIMATED + `use: dimensional` needs a PARSEABLE
  error bar), **M-PROXY** (the grade must match the METHOD — a number off a
  rendered plot is not MEASURED however reproducibly it was extracted; the
  keyword list deliberately excludes "derived", because subtracting two caliper
  readings is still a measurement), **M-OWED** (a fact nobody has may not be
  spent dimensionally, and must state how to obtain it), **M-RESTATE** (a board
  that writes a value has made a second home for it), **D-MATE** (every
  consumption names its site; a BRIEF declaring a Mating fact-lock must have
  the yaml). WHY: every other gate here compares OUR artifacts to OUR
  artifacts. pluto-cal-switch's PlutoPlus SMA span came off an undimensioned
  vector assembly plot at 35.60 mm — three independent extractions agreeing to
  0.003 mm — and a caliper on two physical units read 35.04 and 34.72 mm,
  10-18x the ±0.05 mm mating window. No gate could see it, because the number
  never came from an artifact any gate reads.
  **It says NOTHING TO GRADE, not PASS, when no board declares a mates.yaml**
  — most boards mate to nothing foreign, and a gate that cried wolf on all of
  them would train readers to ignore red; but an empty denominator may never
  read as a pass (M-COVER). Known-bads in `t1_import_provenance.py`, headed by
  the PlutoPlus record AS IT STOOD BEFORE THE CALIPER.
  DECLARED SCOPE LIMIT: it grades PROVENANCE, not correctness, and it is NOT a
  mating-feasibility checker (error bar vs mating budget). That has been run
  once, by hand, on one interface; canon M8 promotes on the SECOND board
  needing it.
- **THE LIVE BEACON (canon M9 / M-BEACON).** `pcb_status.py` READS the beacon;
  `status_beacon_check.py [PROJECT ...] [--root REPO]` grades it against the
  TREE — the two are deliberately separate scripts, because a reader that
  validated its own input would prove nothing (canon M1). Four findings:
  **M-BEACON-DUP** (a field appears twice — an APPEND into a file the 01_docs
  contract says is OVERWRITTEN, which the reader's last-wins rule renders as a
  frame nobody wrote), **M-BEACON-FIELD** (a missing field; the one that makes
  AGE unevaluable, and unevaluable is a FAIL — M-COVER), **M-BEACON-REL** (a
  completed-seal claim must name the LIVE release), **M-BEACON-AGE**
  (`updated:` may not predate that board's newest seal). Release identity and
  ordering are IMPORTED from `jlcpcb-fab/scripts/release_index.py`, never
  re-derived (M-WIDTH). WHY: M9 made the beacon mandatory and nothing made it
  TRUE — measured 2026-07-27, EVERY beacon in the fleet named the wrong
  release, 13 findings across 4 of 6 boards. Known-bads in `t1_status.py` are
  the REAL drifted files (`tests/fixtures/beacons/`), not synthetic ones,
  including the mtime ADJACENT-PROPERTY red-verify.
  DECLARED SCOPE LIMIT: whether a project OWES a beacon is a LIFECYCLE question
  it does not answer — it grades the beacons that EXIST and prints the projects
  with none BY NAME, so the gap is visible rather than silent.
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

- **RELEASE SELECTION IS SCOPED TO A BOARD, AND IMPORTED, NEVER RE-DERIVED.**
  `policy_audit.py` takes `--board <04_kicad stem>` on a MULTI-BOARD project
  and resolves M-REL / M-BOM / A-POP / A-BODY against **that board's** release
  series via `jlcpcb-fab/scripts/release_index.py` — never `rels[-1]`.
  A release set it cannot attribute is a FAIL that names the directory, never
  a silent pick (canon M-COVER), and every dependent row fails with it rather
  than falling through to `06_build` as though nothing were wrong.
  The report's header line states the board graded and the alternatives.
  WHY: `smc0985-cooksense` builds `cooksense` AND `interposer` and holds both
  series in one `07_releases/`. `interposer-…` sorts LAST, so `rels[-1]`
  resolved to the interposer while `boards[0]` handed the audit the cooksense
  board — four checks graded the wrong archive, and M-REL demanded
  `SUPERSEDED.md` on `cooksense-v1.4`, the LIVE release, blocking a v1.5 seal
  (measured 2026-07-27). `power_topology.py` reads its fuse declaration through
  the same index, newest release first, and NAMES the file and line the number
  came from — it printed `fuse rated 3401 A` off `AO3401A` in a part list.
  Pinned by `tests/t1_release_index.py` and `t1_audit.py`
  (`t_mrel_scopes_to_the_board_under_audit`, red-verified).

## Structure

One file per tool; no package/`__init__.py` — scripts are invoked by path.
`__pycache__/` is gitignored, never committed.
