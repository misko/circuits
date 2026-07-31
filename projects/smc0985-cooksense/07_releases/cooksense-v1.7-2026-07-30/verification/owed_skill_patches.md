# Proposed skill patches FILED by the cooksense v1.7 seal — none implemented

`skills/` was **deliberately not touched**: other agents hold live work there,
and a seal is the wrong moment to move a shared backend. Every item below is a
proposal with the measurement that motivates it, written out so the next pass
does not re-derive it.

Numbering: **P1–P2 are new this pass** (P1 is the one the seal itself is
blocked-on-in-principle). **P3, P4 and P9 are new findings measured this pass.**
**P5–P8 were already owed** and are restated here so the debt has one home.

---

## ⬆ STATUS AT THE SEAL, 2026-07-30 — **P1 AND P10 LANDED. THE REST ARE STILL OWED.**

**P1 and P10 are CLOSED**, in commit `217ea175`, and this release is the first
sealed under them. What shipped:

- `release_freshness_check.py` grades and prints TWO verdicts —
  `DESIGN: PASS|FAIL` and `SOURCING: CLEAR|PLANNED-<n>|BLOCKED-<n>` — with
  `--claim design|sourcing|both` to grade either alone, and
  `--claim sourcing --stock-evidence FRESH.json` to re-ask the sourcing question
  from OUTSIDE an immutable archive at order time.
- New check **(f) A-BUY**. The ID is `A-BUY` and NOT the drafted `A-ORDER`,
  because `rules_audit.py`'s `A-ORDER` has meant *"generate_rules runs LAST,
  a pcbnew save clobbers netclasses"* since 2026-07-17 and is cited by name in
  four files. Two policies under one NAME is worse than a missing ID.
- New check **(g) M-REV**, grading `design_verdict` / `order_verdict` as a CLOSED
  vocabulary out of the review header, never scraped from prose, with a
  conservative legacy retrofit that cannot convert a refusal into an acceptance.
- The `08_reviews` contract now declares both keys and says which consumer reads
  which. **This board's project copies of `08_reviews/contracts.md` and
  `07_releases/contracts.md` were RE-SYNCED from the templates at this seal**
  (CLAUDE.md: project copies are re-synced on their next revision, not
  retro-edited into sealed releases) — they had been declaring the retired
  single-`verdict:` vocabulary while governing reviews that use the new one.

**P2, P3, P4, P5, P6, P7, P8, P9 remain OWED and were not touched.** `skills/`
was again deliberately not modified: at seal time four `skills/` paths carry
another agent's uncommitted in-flight work, and a seal is the worst possible
moment to move a shared backend.

### P11 (NEW, measured this pass) — **A-RENDER's verdict is a function of its INPUT's RESOLUTION**

`twin_overlay.py` grades body faithfulness from PIXELS, and `jlc_twin` renders at
a hard-coded size. On this one unchanged board, three renders give three answers:

    5.1356 px/mm   (jlc_twin's own built-in render)
        FAIL — U_LDO centre 1.248 mm; Q_SWDRVRHA resolvable-but-unmeasured
               (13 body pixels against a floor of 20)
    9.7448 px/mm
        FAIL — on a DIFFERENT ref: J_KEY_MATRIX centre 1.11 mm, outward 0.02 mm.
               U_LDO and Q_SWDRVRHA both clear.
   15.3907 px/mm
        PASS, exit 0, 52 measured / 208, zero resolvable-but-unmeasured

**The failing REF changes with resolution**, so the low-resolution FAIL was never
about `U_LDO` — it was about pixels. Reproduced independently by two agents on
two dates from two renders (2026-07-28 measured 15.3961 px/mm; this pass 15.3907).

Why it matters beyond the noise: a gate that flips with an ungated property of
its input invites re-running until it agrees, and there is currently nothing that
records WHICH render a verdict came from. Proposed: `twin_overlay.py` should
(a) print the calibration px/mm in its VERDICT line, not only in the report body,
(b) REFUSE below a minimum px/mm rather than emitting a resolution-limited FAIL
that looks like a geometry finding, and (c) `jlc_twin` should take a render-size
argument so the gate's input is a declared parameter rather than a constant.
Until then the discipline is what this release does: ship BOTH reports
(`twin_overlay.md` at 15.39 px/mm and `twin_overlay_lowres.md`), because deleting
the run that failed is choosing the resolution that gives the answer you want.

### P12 (NEW, measured this pass) — **three gates fail LOUDLY AND WRONGLY when pointed at the wrong file, and one of them refuses instead**

On a project that builds more than one board, the per-board rules live under
`03_src/<board>/rules/`. Measured:

- `assembly_coverage.py <release>` with its DEFAULT assembly path reports
  **37 UNDECLARED-UNPOPULATED refs**. With `--assembly
  03_src/cooksense/rules/assembly.yaml` the only finding is the missing MANIFEST.
  The 37 is an artifact of the INVOCATION, and it is indistinguishable in a
  report from a real population defect.
- `waiver_provenance.py <project-path>` reports `0/0 waivers graded` and FAILs on
  the zero denominator; the tool wants the `projects` ROOT plus `--project`.
  Correct invocation: PASS, 12/72 graded. (The zero-denominator FAIL is canon
  M-COVER working correctly — it is the only reason the mis-invocation was
  visible at all.)
- `bom_legibility_check.py <release>` without `--parts` reports **31 F-MPN
  FAILs** whose text says `(no 02_parts)`. With `--parts`: 0 findings, 60 checks.
- **`count_parity.py` gets this RIGHT and is the model to copy**: without
  `--board` it REFUSES — *"2 kicad_sch artifacts and no --board: ['cooksense',
  'interposer']. Refusing to pick one silently — that is the defect this check
  exists to catch."*

Proposed: every gate that auto-discovers a per-board input should REFUSE on an
ambiguous project rather than silently probing the single-board path, and should
name the file it actually read in its output. `rels[-1]` over a two-board
`07_releases/` already graded the wrong archive in four gates at once
(2026-07-27); this is the same class one directory level up.

---

## P1 — **A SEAL MAKES TWO CLAIMS AND THE RELEASE MODEL ONLY LETS IT MAKE ONE.** Stock belongs at ORDER time.

**Where**: `skills/jlcpcb-fab/scripts/release_freshness_check.py` check (e),
`skills/jlcpcb-fab/scripts/jlc_stock_check.py`, and the *Forbidden* clause of
`skills/pcb-design/templates/contracts/07_releases/contracts.md`
("Sealing against stock evidence that does not PASS").

**The symptom, measured**: `smc0985-cooksense` v1.7 reached
DRC **0/0/0 exit 0**, `policy_audit` **exit 0 / FAIL=0**, both red-team lenses
and both fresh lenses graded, and **seven successive agents declined to seal
it** — every one of them on `jlc_stock_check` exit 1 for one BOM line. Seven
refusals, zero design defects. That ratio is the finding.

**The argument**: every other gate in the repo grades an artifact we control, so
a red means *there exists an edit to this design that turns it green*, and
refusing to seal is right. **A-STOCK grades the WORLD.** It reads a vendor's live
`stockCount` — 0 on 2026-07-29, 5 on 2026-07-30 — and **no edit to the design
changes it.** The only in-design "fix" is to specify a different part, which is
not a repair but a purchasing decision with its own risk.

A seal currently has to assert both of these at once, and one contaminates the
other:

| claim | v1.7 | who can answer it |
|---|---|---|
| *this design is correct* | **TRUE** | the design gates, at seal time |
| *this design is orderable today* | **FALSE**, on one line | the catalog, at order time |

**Proposed shape** (not implemented):

- Split the release verdict into `DESIGN: PASS/FAIL` and `SOURCING: CLEAR /
  PLANNED / BLOCKED-<n> line(s)`, both printed by `release_freshness_check.py`
  and both stamped into `MANIFEST.txt`. A release may seal with
  `DESIGN: PASS` + `SOURCING: PLANNED`; it may never seal with `DESIGN: FAIL`.
- Keep `jlc_stock_check` exactly as strict — the red is real and must stay red.
  What changes is which claim it can veto.
- The existing `sourcing_plan:` escape already does most of this work. Make it
  say so in the MANIFEST's own gate line instead of hiding inside a YAML file,
  so a reader of the archive sees *sealed correct, not yet buyable* without
  opening `03_src/`.
- Add an order-time re-check entry point (`--order-time <release_dir>`) that
  regrades ONLY sourcing against today's catalog, so the question is asked where
  it is answerable.

**Why this is worth more than the board**: the failure mode is not "a bad board
shipped". It is *a correct board did not ship, seven times, and each agent spent
a full pass rediscovering why*.

---

## P2 — `jlc_twin.py` emits **NO parseable verdict line anywhere**

**Where**: `skills/jlcpcb-fab/scripts/jlc_twin.py`.

**Measured this pass**: `grep -n 'verdict\|VERDICT' jlc_twin.py` returns **one**
hit — line 1070, inside a comment. The script prints per-ref finding rows and
exits, and `twin_report.csv` / `twin_run.log` ship into every release
`verification/` with **nothing a grader can parse**.

**Why it matters here specifically**: the 07_releases contract already learned
this lesson for A-STOCK and wrote it down —

> "The fleet shipped three incompatible text formats and one release with ZERO
> verdict lines; this is the one shape the gate grades. A missing/unparseable
> verdict is a FAIL, never a skip."

— and then `jlc_twin`, in the same `verification/` directory, does exactly the
thing that clause forbids. The contract's *Validate* section requires
"twin/pin/render reviews PASS", which is graded by a human reading a CSV.

**Proposed shape**: emit a final line of the fixed form
`TWIN: PASS|FAIL (n OK / m findings, k adjudicated)` and a `--json` sidecar with
an explicit `verdict` key, mirroring `jlc_stock_check --json`; then add the
`twin_report` verdict to `release_freshness_check.py` beside the stock verdict.

---

## P3 — **`--rev` defaults to `"dev"`, and 33 of 33 sealed schematics in this repo say so**

**Where**: `skills/kicad-pcb/scripts/circuit_json_to_kicad_sch.py:1159` —
`ap.add_argument("--rev", default="dev")`.

**Measured this pass, fleet-wide**:

```
$ for f in projects/*/07_releases/*/source/*.kicad_sch; do
      grep -o 'rev "[^"]*"' "$f" | head -1; done | sort | uniq -c
     33 rev "dev"
$ ls -d projects/*/07_releases/*/source | wc -l
     33
```

**Every sealed release in this repo ships a schematic whose own title block
disclaims it.** The `.kicad_sch` is the first artifact a human opens when a
board comes back wrong, and in all 33 cases it says `dev` — while the release
directory, the MANIFEST, the CHANGELOG and the board silk all name a version.
cooksense v1.7 is the first release that will not, because its board driver now
passes `--rev` explicitly (`03_src/cooksense/rebuild_schematic.sh`, fixed in
source rather than by hand-editing `04_kicad/`, canon M3).

**Proposed shape**: (a) make `--rev` **required** when `-o` writes into a project
tree, or default it from the project's release version rather than to a literal
`"dev"`; and (b) add a release check — the sealed
`source/<board>.kicad_sch` title-block `rev` must equal the release version.
This is the same class as the board-silk-version rule that already exists
(cooksense's floorplan carries a comment explaining why the silk token gets
bumped every revision) — the schematic never got the same rule.

---

## P4 — A-STOCK reads `stockCount` and has **no MOQ term**, so it cannot see "unbuyable"

**Where**: `skills/jlcpcb-fab/scripts/jlc_stock_check.py`.

**Measured this pass, live `selectSmtComponentList` 2026-07-30T21:33:59Z**:

```
C265111   JST SM08B-GHS-TB(LF)(SN)   stock=5     MOQ=21
C22391766 JST SM08B-GHS-TB           stock=0     MOQ=444
C42376901 SHOU HAN SH-SM08B-GHS-TB   stock=6030  MOQ=1
```

The gate reported `LOW_STOCK(5) C265111 x2 ... stock=5` against a floor of 10,
which reads as *"short by 5 pieces, wait a bit"*. The truth is
**`minPurchaseNum` 21 > `stockCount` 5**: you cannot order 21 when 5 exist and
you cannot order 5, so the part is **not buyable at any quantity**, and the
threshold to watch is **21, not 10**. The API already returns `minPurchaseNum`
in the same response the gate parses for `stockCount`; nothing reads it.

**SCOPED TO THE REAL POPULATION** by a live sweep of all 58 coded lines (run by
the v1.7 topology re-gate, RG-P2-5): **`C265111` is the only line where MOQ
exceeds STOCK** — so the UNBUYABLE class has exactly one member today and the
gate's blindness costs one finding, not fifty. But **three further lines carry a
reel MOQ far above the build need** and nothing anywhere says so:

```
C25076   MOQ 837  vs need 10
C11702   MOQ 914  vs need 45
C25105   MOQ 887  vs need 10
```

Cost-only, on 0402 passives, and invisible for the same missing-term reason.

**Proposed shape**: parse `minPurchaseNum`; add a status
`UNBUYABLE(stock,MOQ)` distinct from `LOW_STOCK` for the `MOQ > stock` case; and
grade the requirement as `need <= stock AND MOQ <= stock`, reporting the MOQ as
the watch threshold when it dominates. A buyer told "wait for 10" on this line
would wait forever at stock 20. Report `MOQ >> need` separately as an advisory
cost line — it is not a blocker, but a buyer should not discover a $-per-reel
minimum at checkout.

---

## P5 — `escape_check.py` standalone CLI cannot be invoked at all

**Where**: `skills/kicad-pcb/scripts/escape_check.py`.

Every project-root invocation form tried (`--project .`, `--project <abs>`,
positional) raises `IsADirectoryError` — it opens the project directory as a
file. The subject is **not** ungraded (`policy_audit` calls it correctly and
ships `P-ESC PASS 47 parts` / `P-TIER PASS`), so this is a CLI defect, not a
skipped gate. Restated from `gates_not_run.md`.

---

## P6 — `board_netlist_parity.py` standalone CLI raises on a board path

**Where**: `skills/kicad-pcb/scripts/board_netlist_parity.py`.

`AttributeError: 'NoneType' object has no attribute 'GetFootprints'` — it
expects a sealed release path to diff against and was given a board file, with
no argument check saying so. Parity is graded by a stronger instrument
(`kicad-cli pcb drc --schematic-parity` → 0 issues, plus `count_parity.py` over
four source pairs), so again a CLI defect. Restated from `gates_not_run.md`.

---

## P7 — `jlc_twin` runs **unadjudicated** when one symlink is absent, and says nothing

**Where**: the `03_src/rules/` symlink-farm convention, and `skills/pcb-design/SKILL.md`'s
documented `jlc_twin` invocation.

**Measured**: `03_src/rules/` on this board holds five symlinks (`assembly`,
`electrical_invariants`, `nets`, `policy_waivers`, `power_tree`) and **not**
`twin_adjudications.yaml`, whose real file sits at
`03_src/cooksense/rules/twin_adjudications.yaml`. SKILL.md's documented
invocation therefore runs with **zero adjudications loaded** and exits 1 — which
is what the archived `twin_run.log` shows. Pointed at the real path, the same
run exits 0.

A gate that silently loses its adjudications because a path did not resolve is
the same shape as an inherited waiver: it produces a confident number from an
input nobody checked. **Proposed shape**: `jlc_twin` should FAIL LOUDLY when an
adjudications path is expected and unresolvable, naming the path it tried,
rather than proceeding with an empty set. (The project-side half — adding the
missing symlink — is a board fix, not a skill fix, and is not in this release's
scope because it would move a build input after the battery.)

---

## P8 — `rules_audit.py` A-AMP cannot say "the ceiling is the current limiter"

**Where**: `skills/kicad-pcb/scripts/rules_audit.py` (A-AMP).

A-AMP grades netclass copper width against the class's declared `current:`
string. On an eFuse- or PTC-protected rail the honest ampacity bound is **the
limiter's programmed setting**, not a declared budget. Measured on this board:
`nets.yaml` declares `PWR_IN: 2A`, but `R_ILM` = 1.2 kΩ sets the TPS259573 hard
limit at **1.79 A**, and `power_tree.yaml`'s cited worst-case simultaneous draw
is **0.50 A**. A-AMP fails the class on a current the silicon cannot deliver,
while `power_topology.py` independently reports the same declaration
**over-built by 6.7×** — two gates disagreeing with the declaration in opposite
directions and agreeing with each other about the board.

**Proposed shape**: allow a class to declare `limited_by: {refdes, mechanism,
value}` and grade the copper against `min(declared, limiter)`, requiring the
limiter to be a part on the board so the claim is checkable. Restated from
`build_gates.md` §3.

---

## P9 — **NOTHING CHECKS THAT A RELEASE ARCHIVE CAN FIND ITS OWN VENDORED FOOTPRINT LIBRARY.** 5 of 33 cannot.

**Where**: `skills/jlcpcb-fab/scripts/release_freshness_check.py` (the release
"Validate" gate), and whichever staging step copies `fp-lib-table` into
`source/`.

**Measured this pass, on this release's own staging directory**:

```
$ kicad-cli pcb drc --severity-all --refill-zones --schematic-parity \
      source/cooksense.kicad_pcb
Found 14 violations          # ALL 14: lib_footprint_issues
"The footprint library 'cooksense' is not enabled in the current configuration"
```

`source/fp-lib-table` had been copied byte-for-byte from `04_kicad/fp-lib-table`,
whose vendored-library URI is `${KIPRJMOD}/../03_src/lib/cooksense.pretty` — a
path that resolves only from inside the live project tree. The archive's own copy
of that library sits at `source/cooksense.pretty`. **The `.pretty` was vendored;
the table that finds it was not rewritten.** One URI rewritten →
`0 violations / 0 unconnected / 0 parity`.

**The 07_releases contract already states the requirement** — *"the EXACT source
artifacts incl. fp-lib-table + vendored `.pretty` (V-REL-FPLIB … the archive
must re-measure DRC clean)"* — and **no gate enforces it.** This board's own
sealed v1.6 gets it right, so v1.7's staging was a silent regression that only a
manual standalone re-measure caught.

**Fleet sweep** (`grep 'KIPRJMOD}/\.\.' projects/*/07_releases/*/source/fp-lib-table`):
**5 of 33** sealed archives point outside themselves —
`smc0985-cooksense/cooksense-v1.1-2026-07-24`,
`smc0985-cooksense/interposer-v1.0-2026-07-24`,
`usb-hub-3s-v3/v1.3-2026-07-23`, `usb-hub-3s-v3/v1.4-2026-07-23`,
`usb-hub-3s-v3/v1.6-2026-07-26`. All five are immutable; recorded, not repaired.

**Proposed shape**: two checks in `release_freshness_check.py`, because they fail
differently — (a) **static**: no `uri` in `source/fp-lib-table` may contain
`${KIPRJMOD}/..`, since an archive that reaches outside itself is not
self-contained by definition; (b) **behavioural**: re-run
`kicad-cli pcb drc source/<board>.kicad_pcb` from inside the archive and require
0 violations. (b) is the contract's actual completeness test and (a) is the
cheap one that would have caught all five.


---

## P10 — the release verdict vocabulary has ONE field for TWO claims, and it just cost a correct board its seal

**Where**: `skills/pcb-design/SKILL.md` stage 7 and the
`08_reviews/contracts.md` gate — *"both red-team lenses must be present with an
ORDER verdict; a DO-NOT-ORDER verdict blocks the seal."*

**This is P1's twin, observed from the review side rather than the gate side,
and it is the sharper evidence of the two** because it is a lens saying so in
its own words. The v1.7 topology re-gate wrote, verbatim:

> "The **seal** argument in `A-STOCK_waiver.md` §1 is a real M4 argument and **I
> would accept the seal**: a gate that reads a vendor's catalog is measuring the
> world, no edit to the design changes it, and the argument is explicitly scoped
> so it does not generalise. **But sealing is not the question this verdict
> field asks.** The question is whether this release can be ordered, and it
> cannot."

So the reviewer would seal, the gate reads `verdict:`, `verdict:` means
*orderable*, and the seal is blocked. **The lens and the gate do not disagree
about anything physical.** Measured consequence on this board: DRC 0/0/0,
`policy_audit` FAIL=0, three of four lenses ORDER, and **eight successive
sealing passes declined**.

**Proposed shape**: split the header field into two required keys —

```
design_verdict:   SOUND | DEFECTIVE      # is the artifact correct?
order_verdict:    ORDER | DO-NOT-ORDER | BLOCKED-SOURCING
```

with the seal gate reading `design_verdict` and the ORDER_README reading
`order_verdict`. `BLOCKED-SOURCING` exists precisely so a lens can say "this
board is right and you cannot buy it today" without either half contaminating
the other. Retrofit is cheap: a review with only `verdict:` maps to both keys.

**Do not read this as a request to weaken the gate.** The gate did its job: it
stopped a release whose buyer-facing remedy was mis-instructed (RG-P1-1), and
that defect was found *because* the lens was made to grade an order verdict.
The proposal is to let it say two true things instead of one ambiguous one.

---

## P13 (NEW, measured 2026-07-30 re-gate 2) — **`power_topology.py` GRADES A FILE THAT DECLARES LOADS IT DOES NOT READ, AND G-ORPHAN ALREADY SAYS SO IN WORDS WHILE EXITING 0**

**This is the patch for the class that produced this pass's P0-1.** The
instance is fixed in `03_src/cooksense/rules/power_tree.yaml` (ADR-0026); the
class is not, and it will recur on the next board that writes a rail down in a
key the grader ignores.

### What happened, measured

`power_tree.yaml` graded the AMS1117 at `rails[0].iout_max_A: 0.3`. Seventy-three
lines lower, under a `linear_rails:` key **the file itself labels "Documentation-only
(ignored by power_topology.py)"**, it declared four 0.1 A switched sensor rails whose
own `note:` says they come from `3V3`. MEASURED with `pcbnew`: all four `Q_SW*`
sources are on net `3V3`. The graded number was **43 % of the file's own declared
load**. E-TOPO exited **0** and printed **`51%, PASS`**.

`load_rails()` reads exactly one top-level list — `data.get("rails")` — plus five
scalars. Everything else in the mapping is silently discarded. There is no
unknown-key check of any kind.

### The gate that already knows

`schema_reader_audit.py` (G-ORPHAN) grades
`03_src/rules/power_tree.yaml linear_rails[].iout_max_A` as **OWED**, and its own
emitted text is:

> `linear_rails[].iout_max_A`: as `vin_min`; **also absent from the trunk-current
> sum `rails[]` feeds**

That is the defect, named, in the contract, in words — and `RAW_EXIT=0`, because
**OWED does not fail**. Measured this pass on cooksense: 42 OWED rows fleet-wide,
0 UNREAD, 0 ORPHAN, exit 0. An OWED row is a declared gap that costs nothing, so
nothing ever closes one.

### Proposed shape — two patches, and the second is the one that generalises

**P13a — `power_topology.py` refuses rail-like keys it does not read.** In
`load_rails()`, after pulling `rails:` and the five known scalars, fail on any
remaining top-level key that is *rail-shaped*: a list whose entries are mappings
carrying any of `iout_max_A` / `vin_min` / `vout_min` / `converter` / `element`.
Message names the key, the entries, and their summed `iout_max_A`:

```
LoadError: power_tree.yaml declares 'linear_rails' — 6 entries carrying
  iout_max_A totalling 2.47 A — and this gate reads ONLY `rails:`. A load
  written in a section the checker is told to ignore is a budget that cannot
  fail. Either move it into `rails:` (with a converter whose part.yaml `type:`
  normalizes to a topology), or fold its current into the `rails:` entry it
  hangs off and say so, or rename the key so it is not rail-shaped.
```

Escape hatch, deliberately loud and per-key: an explicit
`ignored_by_e_topo: [linear_rails]` top-level list, which the message names.
That converts a silent omission into a signed one.

*Cost note*: this FAILS the current cooksense file if applied naively, because
`linear_rails:` still legitimately documents five non-converting rails. The
escape hatch is what makes the patch landable — but it must be a DECLARATION,
not a default.

**P13b — G-ORPHAN gains a severity above OWED, for a row whose gap is a
CORRECTNESS gap rather than a coverage gap.** Today `OWED` means "a gate is
INTENDED and absent" and never fails. The `linear_rails[].iout_max_A` row is not
merely uncovered: its own prose asserts a *false invariant* about a number that
IS read elsewhere ("absent from the trunk-current sum"). Proposed third grade —
`OWED-BLOCKING`, declared per-row in the contract template, which FAILS:

```
| `linear_rails[].iout_max_A` | OWED-BLOCKING | absent from the trunk-current sum `rails[]` feeds |
```

so that writing the sentence "this declared number is missing from a sum a gate
performs" is itself the thing that stops a seal. Without this, P13a fixes one
gate and the next schema repeats the shape. **The repo has ratchet FLOORS and no
CEILINGS: an honest declared gap currently costs nothing.**

### Also owed on the same file, smaller

**P13c — a first-class derating.** `rails[].pdiss_max_mw` is today the ONLY way
to express a hot-ambient derating, and it swallows the derivation: cooksense now
carries `497` with 60 lines of comment deriving it from `θ_JA 90 °C/W`,
`Tj_max 125 °C`, `Ta 75 °C` and the LDO's own 11 mA quiescent burn. Every one of
those four terms is a datasheet fact that a gate could hold and re-multiply.
Proposed: `rails[].theta_ja_c_per_w` + `rails[].tj_max_c` (or fall back to the
converter `part.yaml`) + a top-level `ambient_max_c:`, with `pdiss_max_mw`
DERIVED when they are present and cross-checked when both are. Needs the
matching row in `skills/pcb-design/templates/contracts/03_src/contracts.md`
in the same change, or G-ORPHAN fails it as ORPHAN — which is exactly why this
board could not implement it from inside its own partition.

**P13d — E-TOPO's `PD` formula omits the regulator's own ground current.**
`grade_linear` computes `PD = (Vin_max − Vout_min) × Iout`, the PASS-ELEMENT
dissipation only. The AMS1117's Quiescent Current is 5 mA typ / **11 mA max**
(ds1117 EC table), burning `Vin_max × Iq_max = 57.75 mW` inside the same
package — **19 % of this rail's graded PD**, invisible to the gate. cooksense
subtracts it from `pdiss_max_mw` by hand. Proposed: an optional
`rails[].iq_max_mA` (or the converter `part.yaml`'s), added to PD as
`Vin_max × Iq` and printed as its own term.

---

## P14 — **E-TOPO's dropout verdict rests on a `vin_min` NOTHING asks about the copper** (NEW 2026-07-30, re-gate 3; FILED, NOT IMPLEMENTED)

The third P0 on one rail in three rounds, and the first two are already above.
`power_topology.grade_linear` computes

    headroom = vin_min − vout_max   vs   dropout_mv

where `vin_min` is a number the board author TYPES into `power_tree.yaml`. On
cooksense it was `4.850 − 0.50 A × 190.5 mΩ`, where 190.5 mΩ is the polyfuse
plus the reverse-polarity FET plus the eFuse **and the board is not in the
list**. MEASURED on the release board: the routed path `J_PWR.1 → F1 → Q_REV →
U_EFUSE → U_LDO.3` carries a further **137.79 mΩ**, i.e. **42 % of the true
series resistance was in nobody's sum**, and the declared margin was 1.9× the
real one (+55 mV claimed, +29.1 mV measured).

**Nothing in the repo could have caught it**, and the reason is structural
rather than an oversight in any one gate: every existing gate reads the file the
author wrote (canon M1's complaint, one level up). `E-NETREF` proves the net
names exist. `A-AMP` proves the tracks are wide enough for their current.
`G-ORPHAN` proves the key has a reader. **No gate relates a DECLARED VOLTAGE at
a pin to the COPPER between that pin and the source.**

**The checkable case is narrow and mechanical**, which is what makes it a gate
rather than a review item:

> A rail declaring `vin_min` whose converter input net carries **NO ZONE ON ANY
> LAYER** is a rail whose entire input conductor is track. For that rail,
> `vin_min` must not be accepted as a bare number.

Three shapes, cheapest first:

1. **REFUSE + REPORT (smallest).** When the converter's input net has no zone,
   `power_topology.py` prints the net's total track length × its netclass width
   as a series-resistance FLOOR and fails unless the file declares
   `rails[].series_mohm:` at least that large. cooksense's `5V_PROTECTED` is
   260.059 mm at 0.500 mm — a 306.63 mΩ series-sum upper bound that a
   one-minute check would have put beside a 190.5 mΩ declaration.
2. **DERIVE (right).** A `series_path:` declaration (`[J_PWR.1, F1, Q_REV,
   U_EFUSE, U_LDO.3]`) that the gate WALKS on the board, summing routed copper
   at a declared temperature and the named devices' cited resistances, and
   computing `vin_min` itself. This is what ADR-0027 did by hand, and it is
   ~120 lines of `pcbnew` plus a linear solve.
3. **The general form.** The same hole exists for every declared node voltage on
   a track-only net: `linear_rails[].vout_min`, `load_uv_threshold`'s delivery
   budget (E-MARGIN's `ir_budget_mohm` is TYPED too — same class), and any
   ampacity floor argued from a trunk that turns out to be a stub.

**Contract half, required in the SAME change** (canon: a skill change is not
done until its contract catches up): the `03_src` contract template must carry
the `series_mohm:` / `series_path:` row naming the gate that reads it, or
G-ORPHAN fails the new key as ORPHAN.

**Why this board did not implement it:** `skills/` is outside this board's
partition (a live agent owns another board's copper), and the same G-ORPHAN
coupling that blocked P13c blocks this. **The gap is DECLARED, which — as P13b
says one section up — currently costs nothing, and that remains the meta-defect
this file exists to record.**
