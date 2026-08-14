# fix_pcb_design

Close the four measured defects in the parts and schematic stages, and stop
respinning releases that contain no board change. Written 2026-08-02 from a
fleet sweep of 29 board generations, 945 commits, 614 part dossiers, 47
superseded releases and 210 classified P0/P1 review findings.

Status: PROPOSED. Nothing here is landed.

---

## 0. The finding that organizes everything

**The pipeline's instruments are ordered by when an ARTIFACT EXISTS, not by
when a DECISION IS MADE.**

Every gate needs something to grade. A board exists at placement, a netlist at
schematic, a BOM at export. So the gates cluster where the artifacts are — and
the decisions that cause the most expensive failures are made before any of
those artifacts exist.

Measured, in the canonical driver `skills/pcb-design/templates/03_src/rebuild_all.sh`:

| Parts (pre-build) | Schematic | Placement | Routing | Post-route |
|---|---|---|---|---|
| **2** | 17 | 12 | 4 | 4 |

And `policy_audit.py:223` reads `choices=("full","placement")`. **There is no
`--phase parts`.** Yet run against a parts-only tree — `04_kicad/`, `06_build/`,
`07_releases/`, `03_tscircuit/` deleted — `policy_audit.py` still produces **10
gradeable rows in 0.89 s**: S-VER, P-ESC, P-TIER, P-LAYOUT, P-PREC, R-LEN,
E-ADR, E-TOPO, M-REPRO, M-JRNL.

The checks exist. Nothing calls them until the release audit.

The consequence, measured three ways:

- **21 of 47 superseded releases (45%) have a root cause inside the parts
  stage.** Of those 21, **17 (81%) were decidable at the parts stage** from a
  document already vendored in the repo, or from one distributor query that was
  never run.
- **35 of 210 classified P0/P1 findings originate at parts — 16 of 48 P0s
  (33%), the largest single origin.** Routing originates 18 findings and 2 P0s
  (4.2%).
- Backtrack (`D-BACK`) entries in stage journals: **24 in routing journals, 5 in
  placement, 1 in schematic, 0 in parts.** The stage that *discovers* the
  problem is almost never the stage that *caused* it.

This plan does not add a review lens. It moves existing instruments to the
stage that decides, and builds exactly two things that do not exist.

---

## 1. The four defects, measured

### D1 — Part facts are re-derived per board, and disagree

| Measure | Value |
|---|---|
| `part.yaml` dossiers in the fleet | **614** |
| Distinct MPNs behind them | **309** |
| Redundant dossiers (re-derivations of a part already done) | **305** |
| MPNs used on more than one board | 136 |
| …byte-identical everywhere | 42 |
| …**that contradict each other** | **94 (69%)** |

`USBLC6-2SC6`: **12 dossiers, 9 distinct versions.** Five record the pin map as
`1:I/O1, 3:I/O2, 4:I/O2, 6:I/O1`; five as `1:IO1, 3:IO2, 4:IO2b, 6:IO1b`; one as
`IO2B/IO1B`. Two of those conventions make pins 1 and 6 indistinguishable.
`escape:` present in 7 of 12. `layout_refs:` in **1 of 12**. `asserts:` in **1 of 12**.

The best dossier (`pluto-rx2-8way`) carries escape + layout + layout_refs +
asserts. The worst four carry none of them. **The improvement never propagated —
not forward, not sideways.** Which dossier you get is a lottery over which board
happened to do the research.

Second half of the same defect: the shared module registry holds **1 module and
0 importers across 28 boards**, and **49% of authored footprints are
byte-identical copies of another board's**. Every reuse asset — the ledger,
archetypes, precedents, modules — is read by prose only. **No executable gate
consults any of them.**

### D2 — Reference designs are essentially never fetched

Across all 614 dossiers:

| `layout_refs` state | Count |
|---|---|
| Dossiers carrying `layout_refs` at all | **89 / 614 (14%)** |
| Entries in the tier-graded machine-readable form | 58 |
| Entries still bare prose strings | 185 |
| **Tier 2 reached** — vendor reference *design files* in hand | **6** |
| Tier 2 named but not reached | 15 |
| Tier 1 reached (a figure in the datasheet) | 25 |

`P-PREC` grades honesty about the ceiling, which is the right idea. Its live
fleet state: **15 graded of 119 in scope at HEAD, 11 owed** (17/120, 10 owed in
the working tree), and `tests/t1_layout_precedent.py` currently reports **10
passed / 2 failed** — the precedent gate is RED right now.

The canon's own example: the RP2040 dossier read a **200 dpi raster** while
Raspberry Pi publishes a permissively-licensed **"Minimal Viable Board"
reference design in KiCad** — schematic and layout.

The defect is not that P-PREC is wrong. It is that `reached: true` is a
**self-assertion with no artifact behind it**.

**And P-PREC is a PARTS-stage LAYOUT field. It is not evidence that anyone
consulted a reference design while drawing the SCHEMATIC.** Measured directly
2026-08-02:

| Schematic-stage artifact | Cites a reference design / typical-application circuit |
|---|---|
| `projects/*/01_docs/journal/*schematic*.md` + `0[23]_*.md` | **0 of 29** |
| `projects/*/01_docs/decisions/*.md` (ADRs) | **0 of 99** |
| `projects/*/03_tscircuit/src/*.tsx` | 2 of 10 |

**Zero of 128 schematic-stage prose artifacts** mention a reference design, a
typical application circuit, or an application circuit. That is the direct
measurement of "did we look at reference designs when we drew the schematic,"
and the answer is no.

The internal reuse ledger is in the same state: `proven-parts.yaml` holds 38
MPNs, of which **31 appear in the fleet — 10.0% of the 309 distinct MPNs.**

### D3 — Schematic completeness is self-declared

**Across 69 gate scripts and 55 test files there is zero code that grades
whether a part's typical-application circuit is fully instantiated.**

`module_first_check.py:317-329` checks declared `support_refs` are non-empty,
unique and present. **Never complete.** No script in three skills derives a
required set from a datasheet.

The gate that looks like it covers this does not: **E-INV passes 9 of 9 boards
at 100%** — while naming **232 of 999 components (23%)**. The author of the
schematic writes the invariant file, so the author picks which 23% gets checked.

cooksense declared its schematic gate GREEN at `16145f2b`
(*"ERC 0, parity 189==189, E-INV 13/13, E-ADR complete"*), then added **61
components and removed 11** — 24 pull-up/pull-down default networks, 11
bypass/timing caps, 8 logic ICs, 7 series isolation resistors, 2 divider pairs —
across **172 commits, 7 sealed releases and 6 supersedes**.

The information was available: across 13 verified companion-component
incidents, **the datasheet answer was present in 12**, and **the board's own
dossier already carried it in 7**.

### D4 — Most release churn is not the board

| Measure | Value |
|---|---|
| `SUPERSEDED.md` files repo-wide | **47** |
| …that explicitly state *no copper / no board change* | **33 (70%)** |
| …where the board actually changed | 14 (30%) |

CPL rotations, CPL datum, BOM legibility, gerber payload, regenerated evidence,
paperwork. And the structural cause is not the defects themselves — it is that
**a paperwork fix and a copper fix use the same release mechanism**, so
regenerating a BOM mints a new version directory *and* a `SUPERSEDED.md` on the
old one.

Related instrument failure: **`jlc_twin.py` PAD-GEOM compares pairwise pad
CENTRE distances only** (`:314-329`, `PAD_GEOM_TOL = 0.3` at `:142`). It reads
no pad dimension anywhere. It printed `C5337088,J5,OK,fit=0.00mm`
**character-identical on the defective and the corrected board**. J5's land
pattern was wrong in **12 of 13 usb-hub-3s-v3 releases**. The `land_pattern:`
field that would fix it exists in **12 of 614 dossiers (2%)** and is declared
ADVISORY on the stated grounds that jlc_twin grades its consequence — which is
measurably false.

---

## 2. Traceability — where each defect is addressed

This is the table to read. Every defect has one primary fix that closes it and,
where relevant, a secondary fix that removes its cause.

| Defect | Primary fix | Secondary | New check IDs | Closes it by |
|---|---|---|---|---|
| **D1** part facts re-derived and disagree | **F1** fleet part library | **F6** reuse promotion | `M-PART1`, `M-PARTREF`, `M-REUSE` | Making one dossier per MPN structurally the only possibility: 614 files → 309, and the 94 contradictions cease to be representable |
| **D2** reference designs never fetched | **F2** fetched-artifact gate + prior-art census | **F5** wiring | `P-PREC-FETCH`, `P-PRIOR` | Replacing the self-asserted `reached: true` with a vendored file whose sha256 verifies; and making prior-art availability an input to selection rather than a note after it |
| **D3** schematic completeness self-declared | **F3** application-circuit conformance | — | `E-APPCKT` | Giving the required-companion set a machine home outside the schematic author's own declaration, with a printed coverage denominator |
| **D4** release churn is not the board | **F4** split copper release from evidence revision + early export battery | — | `M-REL-KIND`, `F-EARLY` | Removing the mechanism that turns a paperwork fix into a board supersede, and moving the export checks off the seal critical path |
| *(all four)* | **F5** call the machinery at the stage that decides | — | `--phase parts`, `parts-gate` | The enabling change: 10 gradeable rows already run on a parts-only tree in 0.89 s and are never invoked until the release audit |
| **stock caught us off guard** *(added 2026-08-02, user requirement)* | **F7** sourcing for build AND bench | `Q-BUILD`, `Q-WEST`, `Q-WEST-WAIVE` | Splitting one flat rule into two jobs with two floors: a reel that must build 5 boards, and a bench spare that must be in hand next week |

Read the last row first. **F5 is wiring, not new capability**, and every other
fix lands into it.

---

## 3. The fixes

### F1 — Promote parts to a fleet library  → closes **D1**

**The change.** `02_parts/<MPN>/` moves from per-board to repo-level
`parts/<MPN>/`. A board declares which MPNs it consumes in
`03_src/rules/parts.yaml` and holds no dossier of its own.

**Why this and not "be more careful".** The 94 contradictions are not
carelessness; they are the predictable output of 29 independent derivations of
309 facts. Remove the duplication and the contradiction class cannot be
expressed.

| New check | Grades | Denominator | Fails when |
|---|---|---|---|
| `M-PART1` | one canonical dossier per MPN fleet-wide | distinct MPNs referenced by live boards (**309** today) | two live dossiers exist for one MPN |
| `M-PARTREF` | every MPN a live board references resolves in the library | MPN references across live boards | a reference does not resolve |

**Known-bad fixture.** Two dossiers for one MPN whose `pins:` blocks differ →
`M-PART1` must FAIL. Verify it goes red against the pre-fix tree, which today
contains 94 real instances.

**Migration.** For each of the 94 divergent sets, merge field-by-field —
richest field wins, provenance recorded (`merged_from:` naming the board and
commit each field came from). This is a one-time pass of 94 merges, not 614.

**Immutability.** Sealed releases keep their embedded copies; `07_releases/` is
never touched. Only the live tree references the library. A sealed board's
dossier is a historical record of what was believed then — that is what a seal
means.

**Would have caught.** The USBLC6 9-way divergence; the 305 redundant
re-derivations; the "good dossier exists on another board" case that recurs
throughout the fleet.

**Second-order win.** After F1 the land-pattern backfill (D4's instrument gap)
is 309 parts, not 614 — and only the multi-pin subset actually needs it.

---

### F2 — Reference design as a fetched artifact, plus a prior-art census  → closes **D2**

Two halves. The first makes the existing gate honest; the second moves the
question *before* the decision.

**F2a — `P-PREC-FETCH`.** A `layout_refs` entry with `reached: true` must name a
file vendored under `parts/<MPN>/refs/` whose `sha256:` verifies. Self-assertion
stops counting.

| Grades | Denominator | Fails when |
|---|---|---|
| that a claimed-reached reference is actually in hand | tier-graded entries (**58** today, rising as the 185 bare strings migrate) | `reached: true` with no file, or a file whose hash does not match |

**F2b — `P-PRIOR`, a pre-selection prior-art census.** Before a part is
committed, record what open prior art exists for it — counts per tier, with the
queries that produced them. **A part with zero prior art is not rejected. It is
FLAGGED as a cost driver**, and that flag is an input to the existing D-MOD
module-first decision.

This is measurable before commitment: the research found **PE42482 scores zero
open KiCad designs while AP63203 scores 421** — a fact available at selection
time on the board where PE42482 later drove the most routing work in the fleet.

*Confidence note: the 0-vs-421 figures come from a single research pass and are
marked partially confirmed pending the verifier's URL check. The mechanism does
not depend on those particular numbers.*

**Known-bad fixture.** A dossier claiming `tier: 2, reached: true` with an empty
`refs/` directory → FAIL. A dossier whose `refs/` file hash has drifted → FAIL.

**Would have caught.** The RP2040 raster-vs-KiCad case the canon already
documents; and would have flagged PE42482's zero prior art at selection, when
the module-first decision was still open.

**Note on P-PREC's current state.** It is RED (`t1_layout_precedent.py`: 10
passed, 2 failed). Fix that before extending it, or F2 inherits a broken base.

---

### F3 — Application-circuit conformance  → closes **D3**

**This is the one thing in this plan that does not exist anywhere.** Be honest
about that: external research found **no standard encodes a part's required
external components**, and the only genuinely automated, netlist-consuming
conformance checker located — AMD's Versal Schematic Checker, Apache-2.0 —
exists only because AMD hand-wrote per-part rules. This is building, not
adopting.

**The change.** A new `requires:` block in the fleet dossier, expressing the
companion components the datasheet's typical-application circuit demands, as
machine-readable rules. Sketch, in the style of the existing schema:

```yaml
requires:
  source: "XU316-1024-QF60 datasheet §14 p.29, Figure 14.3"
  rules:
    - id: vdd_core_bulk
      what: "0V9 core rail decoupling"
      predicate: count(caps on net VDD_CORE with value >= 100nF) >= 12
      why: "vendor minimum; 8 shipped in v1.1 and forced a supersede"
    - id: reset_pull
      what: "RST_N pull-up"
      predicate: exists(resistor from RST_N to VDD_IO, 4k7..47k)
```

**`E-APPCKT`** evaluates each rule against the exported netlist at the schematic
gate.

**Coverage is the headline output, not a footnote.** The check prints
`E-APPCKT: N of M in-scope parts modelled` on the PASS path (canon M-COVER). A
part with no `requires:` model is **OWED and printed**, never silently passed.
Without that line this gate becomes the next E-INV: green at 100% over a
denominator its own author chose.

**Scope control — the authoring cost is the real risk.** Model only parts above
a complexity threshold: multi-pin actives, converters, anything already carrying
`support_refs`. Post-F1 that is a few dozen parts, not 309, and each is authored
once for the fleet rather than once per board. Sequence by measured cost: the
parts that appear in the D3 incident list first.

**Known-bad fixture.** A netlist with 8 caps on a rail whose rule demands 12 →
FAIL. This is the XU316 case, reproducible from the sealed v1.1 bytes.

**Would have caught.** XU316 0V9 (8 caps against a vendor minimum of 12, found
by external review of sealed bytes); cooksense's 24 missing pull-down default
networks; part of the R12/R30 wrong-value class.

**Honest limit.** `E-APPCKT` cannot invent the rule. It converts a datasheet
read that already happens into something durable and checkable. The evidence
says that read *is* happening — the answer was in the dossier in 7 of 13
incidents — and is then not carried into any gate.

**Two cost realities that must be stated before this is committed to.**

*The target set is smaller than "all parts", and the amortisation is weaker than
F1 implies.* Scoped by the existing P-LAYOUT regex the candidate set is 120
records / **101 distinct MPNs** — but **50 of the 120 (42%) are connectors,
switches, LEDs, crystals, inductors and antennas with no application circuit to
transcribe.** The real target is **70 records / 60 distinct MPNs**, 56 of them
with ≥8 pins. And only **13 MPNs sit on more than one active board**; 88 of 101
are single-use, so F1's "author once, use everywhere" argument holds for the
fleet's history but only weakly for its future. **`E-APPCKT` needs its OWN scope
predicate — do not reuse P-LAYOUT's regex**, which was written for keep_short
budgets, or the coverage line stalls at 58% forever or fills with vacuous rows.

*Step 0 is often a download, not a read.* **300 of 614 part folders contain no
PDF at all**, and 190 more record a `sha256` for a file not present in the tree.
For a large share of the target set the datasheet is not on disk.

**The coverage line must not be self-graded.** If the dossier author writes both
the `requires:` rows AND the count of obligations they were drawn from, the
coverage number is prose with a number on it — canon M1, checker and checked
sharing a method (the author). Derive the denominator by a **second method**:
extract obligation candidates from the datasheet's section headings / figure
captions in a pass separate from transcription, and grade transcription against
that. If that cannot be built, publish the coverage as a raw count with no
verdict attached rather than as a certificate.

---

### F4 — Split the copper release from the evidence revision  → closes **D4**

**F4a — `F-EARLY`.** The fab-export battery — CPL datum and rotation, BOM
legibility (`F-MPN`/`F-WORDS`/`F-ENCODE`), gerber payload census — must have run
green **on the current board hash before the seal ceremony opens**, not as part
of it. These are seconds of script time and they currently sit on the critical
path of the most expensive ritual in the pipeline.

**F4b — `M-REL-KIND`, the structural fix.** A release directory whose board
sha256 equals its predecessor's is an **evidence revision**, not a version bump:
`v1.2+e3`, no `SUPERSEDED.md`, no DO-NOT-ORDER language, no re-review. Only a
board-hash change may mint a new version.

| Grades | Denominator | Fails when |
|---|---|---|
| release kind matches the board delta | release directories per board | a new version directory carries a board sha256 identical to its predecessor |

**Would have removed 33 of 47 supersedes** — every one that already says in its
own text that the fab payload is byte-identical.

**Also in scope (small, high payoff).** Make PAD-GEOM read pad *dimensions*, not
just centres, and promote `land_pattern:` from ADVISORY. Sequence this **after
F1**: the backfill is 309 parts instead of 614, and the honest deliverable is
the backfill campaign, not the checker.

---

### F5 — Call the machinery at the stage that decides  → **enables everything**

The cheapest item in this plan and the one that unblocks measurement.

1. `policy_audit.py --phase parts` — the 10 rows that already grade on a
   parts-only tree in 0.89 s.
2. `pcb_flow.py parts-gate` — a stage-exit entry point, so "we passed the parts
   stage" becomes a thing that can be false.
3. Wire `/shopping-list` as the sourcing arm. **It already exists and works**:
   `shopping_list.py` is 1154 lines implementing `Q-COVER`, `Q-GRADE`,
   `Q-IDENT`, `Q-SNIPPET`, `Q-STOCK`, `Q-WIDE`, with 20 tests in
   `tests/t1_shopping_list.py`. It is simply not part of the parts stage.

**Implement `Q-2SOURCE`, restated around the real requirement — see F7.** It is
declared "a hard pre-selection gate" at `SKILL.md:499` and has **zero code hits
in `skills/` or `tests/`**. Do not leave a hard gate declared and unimplemented;
that is the exact shape this plan exists to remove.

---

### F7 — Sourcing that serves the build AND the bench  → strengthens **D1**, closes the Q-2SOURCE gap

**The requirement that sets the design.** This operation hand-finishes and
repairs its own boards. A part that exists only at LCSC cannot be held in the
hand next week. **Western availability is therefore not a supply-chain-risk
hedge — it is a bench requirement**, and it is not satisfied by any amount of
LCSC stock. That is a far stronger justification than the obsolescence framing
the rule currently carries, and it survives every objection in the research
(which was aimed at breadth-as-quality-proxy, a different claim).

**The design error in Q-2SOURCE as written** is that it applies ONE threshold to
TWO different jobs. Split it:

| Check | Job | Pool | Threshold | Fails when |
|---|---|---|---|---|
| `Q-BUILD` | supply the 5-board assembly | LCSC/JLC | `stock >= max(100, 10 x build_qty)` | below floor, or below build need |
| `Q-WEST` | supply the bench for repair/finish | DigiKey **or** Mouser | Active status (not NRND/LTB/Obsolete) **and** in stock **and** `stock >= repair_spares` (default 10) | no western listing at all, or a non-Active status |

The floors differ **because the jobs differ**. 100+ units is the right bar for a
reel that must build boards; it is the wrong bar for a bench spare, where a
specialty RF part showing 25 at DigiKey is entirely adequate. A flat 100 across
both pools would reject good parts for the wrong reason.

**Scope — measured, not guessed.** Across 40 sealed releases, 1758 BOM lines:

| Class | Lines | Share |
|---|---|---|
| Generic-value passives (any equivalent from a kit works) | 803 | 46% |
| **Lines where the exact MPN matters** | **955** | **54%** |
| **Distinct non-generic MPNs, fleet-wide** | **109** | — |

`Q-WEST` applies to the **109**, not to 614 dossiers and not to every BOM line.
The exemption is machine-decidable from `Comment` + `Footprint` — a standard
E-series value in a standard R/C package, with no tolerance or dielectric
requirement declared — so it is a **class**, not a per-part judgement call. A
precision or specialty passive (`TNPW06034K64BEEA`, an X2Y, a controlled-ESR
bulk) falls OUT of the exemption and into `Q-WEST` automatically.

**The exception path is an ADR, never a silent waiver.** A part may be LCSC-only
when there is a real reason — no western equivalent exists, or the western part
is 40x the price for a function that is not bench-serviceable anyway. That
reason is written down, names what happens if a board needs that part repaired,
and is graded. `Q-WEST-WAIVE` counts waived parts and prints the count on the
PASS path; a waiver with no ADR fails.

**Denominator.** `Q-WEST: N of M non-exempt MPNs have a western Active source;
K waived with ADR`. Printed on the PASS path. Without that line this becomes
another gate green over a scope its own author chose.

**Re-run at order day.** The measured failure is stock evaporating between
schematic freeze and order — one documented case cascaded a JLC stock-out into a
TQFN-16 to WLP-9 package change, trace width 0.254 to 0.15 mm, and three hours of
re-routing. Snapshot at the parts gate, re-verify at fab export, and record a
**footprint-compatible alternate** in the dossier (a JLC BOM line takes exactly
one LCSC code, so the alternate cannot live in the BOM — it must live in source
and be re-resolved by the pipeline).

**Known-bad fixture.** A dossier whose only source is an LCSC code, with no
western listing and no waiver ADR, must FAIL `Q-WEST`. A part with DigiKey stock
but status NRND must FAIL. Both are reproducible from parts already in the fleet.

**Implementation cost is low** — `shopping_list.py` already queries Mouser and
DigiKey and already implements `Q-STOCK` (`stock > floor AND >= qty`,
`:642-654`). What is missing is the per-pool split, the raised floor, the
status screen, and the exemption class. Confirm one thing first: the skill's
stated scope is a board's **self-supplied** parts, so it may not currently walk
the JLC-assembled majority of the BOM.

---

### F8 — Class A hardening: four pure-process fixes  → **unblocks measurement**

Four changes that touch only `skills/` and `tests/`. **No board tree changes, no
data authoring, every board benefits the moment they land.** Grouped because
they share a cost shape, not a subject.

**F8.1 — `M3`, guard `pre_route_review_check.config()`.** `:82-84` does an
unguarded `path.read_text()` on `03_src/route.yaml`. Verified by execution
2026-08-02: the gate **raises `FileNotFoundError` with a traceback** on
smc0985-cooksense, whose route.yaml is at `03_src/cooksense/route.yaml`
(ADR-0007 two-board project). All 8 tests in `t1_pre_route_review.py` write a
route.yaml, so the absent-file path was never fixtured. **A gate that raises is
indistinguishable from a gate that found nothing.** Fix the multi-board path
resolution, not just the crash. Fixture: `t_no_route_yaml`. **1 hour.**

*Budget for the consequence, not the fix: PR-REVIEW currently passes on 0 of 10
boards. Making it grade reveals ten boards' worth of findings.*

**F8.2 — `B.4`, E-INV prints its coverage.** Today
`electrical_invariants.py` prints `E-INV OK: 11/11 invariants hold` (verified by
execution on crow-recorder-central-v2). Change to:

```
E-INV OK: 168/168 assertions; NAMES 84/239 components, 41/156 passives
```

Canon M-COVER, already applied to P-ADJ, P-PREC and count_parity. **5 lines.**
It converts the repo's most-trusted green line from self-certifying to measured:
fleet-wide, assertions name **232 of 999 components (23%)** and **138 of 737
passives (19%)**, while every board reads 100%.

**Land it report-only. Do NOT ratchet the fraction in the same change** —
measure across a few boards first, then set a floor. And announce it: every
board's E-INV line will look worse overnight, which is correct and reads as a
regression if unannounced.

**F8.3 — `M2`, `P-DRIFT`.** `generate_board_generic.py:1283-1306` legalizes
floating parts by refdes-sorted occupancy ring search, which is **globally
coupled**: adding 11 anchored 0402s re-solved **8 unrelated floaters** (C_AND1
moved 5.946 mm, none of them edited), and deleting `R_EXPRST` left a stale
reservation that **errored the stitch 30 minutes into a rebuild**. Diff
regenerated placement against the last promoted board for every refdes named by
coordinate in `route.yaml` (reservations, seed_stubs, prep.keepouts, fences);
FAIL on any move over threshold or any ref that no longer exists.

`grep -rn P-DRIFT skills/ tests/` returns **nothing** — it was specified in a
learnings file and never built. The identical staleness guard already exists for
`placement.bbox_override` at `:1278-1282`, so this is a **~20-line port**, not a
design. Measured cost it avoids: cooksense v1.2 paid 5 race + 8 stitch cycles;
v1.7 paid 3 full reroutes, the first dying 30 minutes in.

**This is the best cost-avoided-per-effort item in the plan for the stated
pain**, and it needs zero per-board data because it compares two generated
artifacts. **½ day.**

*Record honestly that this is a symptom fix.* P-DRIFT detects the coupling; it
does not remove it. **"Make the legalizer locally stable" is the real repair**
and belongs on the list as its own item.

**F8.4 — `M5`, the fleet gate runner.** 5 of the 8 gates SKILL.md marks
"RUN THEM" run in **0 drivers and 0 CI**; 3 more run inside `run_tests.sh` with
assertions built so they **cannot fail on findings** (`t1_net_reference.py:512`
asserts `rc in (0,1)`, "never the counts"). Add `fleet_gates.sh` and print the
counts. **Report-only first** — running the gates and seeing the real state
costs nothing; turning the counts into a falling ceiling is a separate
commitment (see §5). Live example of what it would surface: **58 ghost net
references across 4 of 10 active boards**, every one a `keep_short` budget
grading nothing. **½ day.**

---

### F9 — `E-ACCOUNT`: the netlist is the denominator  → completes **D3**

The complement of F3. F3 catches components that should exist and do not;
`E-ACCOUNT` catches components that exist and were never accounted for — the
**removal and ghost side**.

Every component in the exported netlist must be claimed by exactly one
accounting source: an F3 `requires:` row, an `integration.yaml` `support_refs`
entry, an `electrical_invariants.yaml` assertion, or an explicit waiver.

**Why it is different from every other check here: its denominator is the
netlist, which the schematic author cannot shrink.** Writing fewer assertions
makes the score *worse* — the exact inversion of E-INV's current property.

| Grades | Denominator | Fails when |
|---|---|---|
| every netlist component is claimed by something that is not the schematic | components in the exported netlist | any unaccounted refdes; a claim naming a refdes not in the netlist (the ghost class, 58 live today) |

Output shape: `E-ACCOUNT: 239/239 accounted (requires 61, support_refs 47,
E-INV 84, waived 8); 0 unaccounted`, broken down by source so a board that
complies by mass-listing `support_refs` is visible as such.

**Fix the waiver channel before building it.** The source proposal gates
`unaccounted.yaml` on `why:` being ≥20 characters. **That is string length —
the author-supplied denominator walking back in through the door the gate exists
to close**, and on cooksense's +61 delta the cheapest compliant path is 61
waiver rows. Require an `adr:` that resolves to a real ADR file instead.

**Baselines today, stated so the first run is not mistaken for a regression:**
crow-recorder-central-v2 names **7 of 199** components; usb-hub-3s-v3 20 of 122;
programmable-usb2-hub 52 of 211; cooksense 84 of 239. **The first run is ~90%
unaccounted on most boards** and the honest deliverable is a classification
campaign.

**Known-bad fixture.** A netlist stub carrying the actual cooksense delta — the
24 pull-up/pull-down refdes, 11 `C_*`, 8 `U_*` — against the 13-assertion
invariants file that existed at `16145f2b`. Must FAIL naming 61.

**Sequence it AFTER F3.** `requires:` rows are what make most components
accountable cheaply; running E-ACCOUNT first means classifying by hand what F3
would have classified for free. **2 days** plus the campaign.

---

### F10 — Bounded gate migration, then pin  → **resolves a real disagreement**

Two independent analyses reached opposite conclusions and this plan should not
pick a side silently.

**The case for aggressive adoption.** Six gates that do exactly what this plan
asks for **already exist, fail closed, print coverage, and are fixtured** — and
they run on 1–2 of 21 board drivers. `policy_audit` is executable in **4** of
21. cooksense and usb-hub-3s-v3, which hold **20 of the fleet's 47 superseded
releases between them**, wire **0 of 19** gates. `SKILL.md:846-847` makes this
permanent by policy — *"reseeded at its next revision — never retro-edited"* —
so the denominator grows one board at a time and the two worst boards never
arrive.

**The case against a rising ratchet.** `skills/` changed on **16 of 17 days**
(317 commits); **77 commits touch a gate and a board in the same commit**; an
E-ADR fix sits literally between usb-hub-3s-v3's schematic and placement
commits. A fleet ratchet that may only rise forces all 10 live boards to absorb
every new gate — and re-attestation is already **~60% of loop commits**.

**Both are right about different things.** Unadopted gates are worthless;
an unbounded rising ratchet mints unbounded work.

**The resolution: a one-time dated migration, then pin.**

1. Wire the existing 19 gates onto the drivers of the **two worst boards**
   (smc0985-cooksense, usb-hub-3s-v3). Bounded, finite, known denominator.
2. Measure what falls out. That number decides whether to continue.
3. **Then pin:** a board commissioned after date D runs gate set D and finishes
   against the gates it started with. New gates apply to new boards.

This is the only item in the plan that is **purely board work** — it edits
`projects/*/03_src/rebuild_*.sh` and adds no process code at all. **1 day for
the two boards.**

---

### F11 — `P-DOSSIER`: does every part the design names HAVE a dossier?  → closes **D1**

The cheapest gate in this document, and it was in none of the analyses until a
completeness critic went looking for loop-backs the sealed-release ledger cannot
see.

`pluto-rx2-8way/01_docs/journal/04_schematic.md:30-38`: two commodity parts (an
LED and a button) had **no dossier at all**, would "resolve to an EMPTY FPID and
hard-error `generate_board` at stage 5", and forced a **D-BACK to stage 2**. The
journal names the root cause itself: the 02_parts README's *"one dossier per
part the design NAMES"* was measured against `DETAIL_DESIGN.md` §8's value
index, **which lists the ballasts and not the indicators.** A definition
mismatch between two documents.

**Measured today: no script anywhere maps design parts → `02_parts` coverage.**
`tsx_preflight.py:68` fails only on the degenerate `0/0` case, and
`grep -rn "no dossier|missing dossier|not in 02_parts" skills/ tests/` finds no
gate.

| Grades | Denominator | Fails when |
|---|---|---|
| every refdes the design names resolves to a dossier | **100% of parts on every board** — no scope predicate needed | any named part has no dossier |

**~20 lines**, denominator is total by construction, and the RED fixture is a
real historical D-BACK. Nothing else in this plan has that ratio.

**Related, and worth a look while you are here — dossier mortality.**
**Nine parts were researched, dossiered, then abandoned**: usb-hub-3s-v3
discarded 6 of the 36 dossiers it founded (17%) — `TPS26631PWPR`, `BZT52C3V9`,
`BZT52C6V2`, `MF-MSMF600`, `PMR100HZPFU5L00`, `RT0603BRD074K12L` — plus
`ULN2803ADWR` (cooksense), `SMP-MSLD-PCE-5T` (pluto-cal-switch) and
`LM5116MHX-NOPB` (programmable-usb2-hub). **None appears as a SUPERSEDED root
cause**, so no corpus in this analysis can see them. They are the purest
instances of "better part selection would have avoided this work" and they are
currently invisible. Counting them is a measurement, not a gate — do it before
sizing F2.

---

### F6 — Reuse promotion  → closes **D1**'s second half

The module registry holds **1 module and 0 importers across 28 boards**.

**Promotion criterion.** A subcircuit that has appeared on ≥2 boards and passed
a schematic gate on both is promoted to `tscircuit_modules/`, carrying its
`requires:` model from F3.

**`M-REUSE`** reports the reuse rate and names un-promoted subcircuits appearing
on ≥3 boards.

**Report-only at first, deliberately.** The repo's own memory records that a
ratchet which only rises mints re-verification work across every live board. Let
this one measure for a few boards before it gates anything.

**On PRE-ROUTED submodules — researched 2026-08-02, and the answer changes what
F6 should aim at.** Three practices get conflated under "reuse"; keep them apart:

| Practice | Is it common? | Evidence |
|---|---|---|
| Physical pre-routed **modules** you solder down, with a formal integration document | **Universal** | Every vendor class converges on it. For RF it is *regulatory*: 47 CFR 15.212(a)(1)(vii) makes the integration instructions a condition of the module's grant |
| Reference **layout + written routing guidance** you re-derive from | **Universal** | TI's own documentation standard SZZA036C makes "10. Layout / Layout Guidelines / Layout Example" mandatory in every modern datasheet — but in 7 of 7 datasheets checked the example is a **rendered figure**, and in **0 of 10** was an editable layout file attached |
| Portable pre-routed **copper blocks** dropped into a new board | **Not common practice** | Real capability in every major EDA tool, used only in a niche. The industry's own reuse evangelist (PCEA chair, PCD&F 2026-05-01) calls reuse blocks *"surprisingly underutilized"* and *"frequently recreated from scratch in each new project"* |

Two findings matter operationally:

1. **`tscircuit` packages carry no frozen copper.** Your own tool reuses
   *placement* as code (`pcbX`/`pcbY`, `pcbPack`, `manual-edits.json`) and
   deliberately re-runs the router. So "promote a routed block" is not something
   the current authoring path can express.
2. **`atopile` does exactly this, routinely, headlessly.** 156 of 157
   first-party packages ship a `layouts/default/default.kicad_pcb`; 36 of 40
   sampled contain real routed copper, transplanted into the parent board during
   `ato build` by a ~500-line pure-Python merger that copies segments, arcs,
   zones, vias and placement with net remapping. **KiCad 10** (2026-03-20) also
   stores a design block as a plain `.kicad_pcb` in a `.kicad_block` directory —
   the only routed-block format here a scripted pipeline could read and write —
   but it has **no CLI or Python API**, so it cannot enter the pipeline as-is.

**What F6 should therefore aim at, in order:**

- **Now:** promote *schematic* subcircuits with their `requires:` models. That is
  what tscircuit expresses and what the fleet's 1-module/0-importer state makes
  urgent.
- **Consider:** for the **8-way RF switch matrix**, the relevant practice is not
  cross-board block reuse but **within-board channel replication** — route one
  arm, replicate to the other seven. That is the mature, widely-used code path in
  every tool, it is a different mechanism from block reuse, and it maps onto a
  board you already have.
- **Not yet:** cross-board routed-copper reuse. Adopting it means porting
  atopile's LayoutSync pattern against your tscircuit→KiCad output. There is
  working prior art to copy rather than invent, so this is not reckless — **but
  it is being early, not being conventional.** Do not file it under "adopting
  industry standard practice."

---

## 4. Sequencing

### The cost lens that should drive the order

Every fix here is a **process** change — none is a board fix. But they fall into
three very different cost shapes, and the shape matters more than the subject:

| Class | Meaning | Cost |
|---|---|---|
| **A — pure process** | Edit a script. Every board benefits immediately. No per-board work | bounded, one-time |
| **B — process + wiring** | Edit a script, then call it from N of the 21 board drivers | bounded, mechanical |
| **C — process + data campaign** | Edit a script, then *someone authors the data it grades*, per part or per board | **unbounded, needs judgement** |

| Fix | Stage | Class | Data campaign |
|---|---|---|---|
| F8.1 M3 config guard | schematic/placement | **A** | none |
| F8.2 E-INV coverage | schematic | **A** | none |
| F8.3 P-DRIFT | placement→routing | **A** | **none** — diffs two generated artifacts |
| F8.4 fleet runner | cross-cutting | **A** | none |
| F11 P-DOSSIER | parts | **A** | none — denominator is total |
| F5 `--phase parts` | parts | **A/B** | none — wiring |
| F4a F-EARLY | fab-export | **A** | none |
| F4b M-REL-KIND | release | **A** | none |
| F1 fleet library | parts | **A + one-time** | 94 dossier merges, then never |
| F10 gate migration | cross-cutting | **B** | 21 drivers; **the only pure board work here** |
| F7 Q-BUILD/Q-WEST | parts | **A + light C** | waiver ADRs among 109 MPNs |
| F2 P-PREC-FETCH | parts | **C** | fetch + vendor a file per part |
| F3 E-APPCKT | schematic | **C** | 70 records / 60 MPNs; 300 folders need a download first |
| F9 E-ACCOUNT | schematic | **C** | classification campaign, ~90% unaccounted at first run |
| F6 reuse promotion | cross-cutting | **C** | module authoring |

**Everything in Class A can land in about a week and touches zero board trees.**

### Phases

| Phase | Fixes | Why here | Effort |
|---|---|---|---|
| **0a** | **F8.1** M3 guard, **F8.2** E-INV coverage, **F11** P-DOSSIER | Three Class A fixes, ~1 day total. Two are one-hour. All three are live defects, not improvements | 1 day |
| **0b** | **F8.3** P-DRIFT, **F8.4** fleet runner | Class A. P-DRIFT is the best cost-avoided-per-effort item for the stated loop pain and needs no board data | 1 day |
| **0c** | F5 wiring, F4a, F4b | Class A/B. Makes the parts stage a thing that can fail; removes the paperwork-supersede mechanism | days |
| **1** | F1 library | Mechanical; removes cost rather than adding checks; shrinks every later campaign | 1–2 weeks |
| **1b** | **F7** sourcing split | Highest-urgency user requirement; `shopping_list.py` already queries both western pools, so this is a threshold split + status screen + exemption class | days |
| **1c** | **F10** bounded gate migration on the two worst boards, then measure and decide | Multiplies every gate above; bounded on purpose | 1 day |
| **2** | F2 fetch gate + prior-art census, PAD-GEOM dimensions | Depend on F1's single-dossier shape | 1–2 weeks |
| **3** | **F3** E-APPCKT, then **F9** E-ACCOUNT | The Class C pair. F3 first — its `requires:` rows are what make components accountable cheaply, so running F9 first means hand-classifying what F3 would classify for free | ongoing |
| — | F6 report-only | Alongside from Phase 1 | continuous |

**Before Phase 3 starts, run the two measurements this plan is missing:** the
dossier-mortality count (F11's note) and the marginal re-verification cost of one
iteration (§6.1). Both change the sizing.

---

## 5. What this plan explicitly does NOT do

- **Not adding a review lens.** Lenses already dominate detection. The gap is
  upstream instruments, not more eyes at the end.
- **Not replacing the router.** Routing originates 18 of 210 findings and 2 of
  48 P0s (4.2%), and first-pass routing completes in 1–4 hours on every board
  measured. *(An external benchmark reports KiCadRoutingTools' clean-pass rate
  falling from 0.74 to 0.20 between small and medium boards while Freerouting
  holds at 0.78. That is worth its own investigation — it is not this plan.)*
- **Not building the two-pool gate *as originally specified*.** The flat
  "two pools, stock > 10" rule applies one threshold to two different jobs.
  F7 implements the requirement properly — build supply and bench supply, two
  floors, a machine-decidable exemption class, and an ADR exception path.
  *(Revised 2026-08-02: an earlier draft of this plan recommended deleting
  Q-2SOURCE outright. That was wrong — it read the rule as an obsolescence
  hedge, which the research does undercut, and missed that the real driver is
  hand-repair sourcing, which no LCSC stock level satisfies.)*
- **Not backfilling `land_pattern:` across 614 dossiers.** Do it after F1, over
  309, multi-pin subset only.
- **Not adding a ratchet that forces every new check onto all 10 live boards.**
  `skills/` changed on 16 of 17 days and 77 commits touch a gate and a board
  together; a rising fleet ratchet multiplies that. F10 replaces it with a
  bounded migration.

### Considered and deliberately deferred

Each of these was specified in full and is worth building later. Recording the
reason so the decision is reviewable rather than forgotten.

| Item | What it is | Why deferred |
|---|---|---|
| `P-PIN2` — derive the pin map twice from methodologically independent sources | Highest single-defect cost in the whole set: **6 sealed DO-NOT-ORDER releases** from one relay sub-figure misread, and the same wrong dossier still sits in an un-superseded archived board | **Its second source is measurably unavailable.** The fleet's twin adjudications already record **124 `NO-CAD` + `FETCH-FAILED` rows** — vendor CAD is missing for exactly the unusual parts that need this most. 4–5 days. Revisit after F1, when the vendor-CAD hit rate over 309 parts can be *measured* instead of hoped for |
| `M4` — turn `G-VACUOUS`'s floor into a falling ceiling | `gate_contract_audit.py` prints "13/46 fixtured; 33 OWED" and exits 0, so an honestly declared gap costs nothing | Commits to an unscoped 33-fixture backfill. Run F8.4's fleet runner first and see the real numbers |
| `E-DETAIL` — make `DETAIL_DESIGN.md` machine-parseable | Would have caught two P0s on usb-hub-3s v1.0 (four gate resistors promised and absent; "2×10 µF became one") | **Redundant with F9.** A DETAIL row is one of E-ACCOUNT's five accounting sources. Build F9 first; if its breakdown shows DETAIL rows carrying real weight, promote this then. Building both buys the same catch twice |
| Board housekeeping on pluto-rx2-8way-v4 | `DISPOSITIONS.md` reads `open` on all 19 pre-seal findings while the closure lives in prose below the table; six stale `CHECKLIST.md` ticks; stray empty `projects/pluto-rx2-8way-v4/projects/…` dirs | Not process work — one board, outside sealed dirs, a normal commit. Genuinely small and still undone |

---

## 6. Open questions

1. **Carrying cost.** Every fix here adds an artifact that must be re-attested
   each iteration. Roughly 60% of loop commits are already re-attestation. Before
   Phase 1 lands, measure the marginal re-verification cost of one iteration —
   this plan prices build effort, not carry.
2. **Gate churn under live boards.** A board's green is invalidated by a gate
   that lands after it was measured. Consider pinning the gate set at commission
   so a board finishes against the gates it started with.
3. **The stop rule.** 73.3% of commits on boards that sealed come after the
   first seal, and mean seal lifetime on one family was 5.6 hours. Nothing in
   this plan tells a board it is finished. That may be the largest remaining
   defect and it is out of scope here.
4. **CORPUS BIAS — read this before quoting any number in §1.** Every
   parts-stage share in this document (including "21 of 47 supersedes, 45%") is
   measured over **`SUPERSEDED.md`, i.e. sealed releases.** The user asked about
   *loop-backs*, and the loop-back record is the `D-BACK` journal, which no
   analysis counted. Classified by TARGET rather than by where it was written:

   | D-BACK target | n |
   |---|---|
   | **placement** | ~10 |
   | parts | 2 |
   | schematic | 1 |
   | **declared placement, root cause was a pipeline config constant** | 2 |

   **On the loop-back record placement dominates roughly 2:1 over everything
   else combined.** And two loop-backs were caused by the pipeline's own wrong
   constants and recorded as placement failures — `crow-recorder-central-v2`'s
   journal says it outright (*"D-BACK REFRAMED (6/8 were config, not
   placement)"*, `routing.md:140`: 7 of 8 pads had a DRC-legal via site the whole
   time; `try_via` fell back to `hole_to_copper=0.205`, 0.055 mm stricter than
   that board's actual 0.15 mm floor), as does `pluto-rx2-8way`'s
   (*"BOTH WALLS FELL TO CONFIG"*, `routing.md:283`).

   **This does not invalidate the parts and schematic work** — the sealed-release
   ledger is the right corpus for *what shipped wrong*, and 17 of 21 parts-rooted
   supersedes were decidable at the parts stage. But it means **a plan aimed only
   at parts and schematic is aimed at the wrong half of the loop.** Placement,
   and the pipeline's own constants, are unaddressed here and should be the next
   investigation.

---

## Provenance

Numbers in §1 were measured directly against the tree at
`809b38af` and the working tree on 2026-08-02, and independently recounted by
an adversarial verifier; the 614 / 309 / 136 / 42 / 94 / 305 dossier census and
the 47 / 33 supersede split were confirmed exactly. Figures carrying a
confidence note are single-source and marked as such. Findings quoted from the
review corpus are conditioned on the 10 of 28 generations that carry a
disposition ledger — 18 generations contribute zero rows, so fleet rates over
review findings are not claimable.
