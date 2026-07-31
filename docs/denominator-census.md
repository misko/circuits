# Denominator census — what each verdict's population actually is

**MEASURED 2026-07-31 at `7f5e48cd`.** This is a PHASE-0 census: read-only,
no verdict was altered. It exists to be the ORACLE for the change that makes an
empty population yield UNGRADED — that change must produce EXACTLY the
conversions listed here and no others. A conversion this document does not name
is a regression, not an improvement.

The rule being instrumented: **a verdict may not be emitted without its
denominator, and an empty denominator yields UNGRADED — never PASS, never
FAIL.** The proven local pattern being promoted is
`skills/jlcpcb-fab/scripts/bom_legibility_check.py` (`UNGRADED_TOKEN` at :625,
`ungraded_rows = len(coded) - graded` at :742, the "ungraded rather than failed;
no edit to it could ever clear it" rule at :765).

**The one way this goes wrong:** UNGRADED must mean *the population was empty*,
never *grading was inconvenient*. A check that CAN reach its evidence and finds
it bad must still FAIL. Every conversion below is justified by a MEASURED
`|population| == 0`, not by a verdict anyone wanted changed.

## Trees the numbers were taken in

| Tree | Path | State |
|---|---|---|
| PRIMARY | `/home/mouse9911/gits/circuits` | `7f5e48cd`, working tree carries built `06_build/` evidence |
| FRESH | `<scratch>/wt_fresh` | `git worktree add --detach`, same sha, **no `06_build/`** |
| CENSUS | `<scratch>/wt_census` | same, used for the fleet gate census so `projects/` was never written |

`projects/pluto-rx2-8way-v2/` was excluded from the PRIMARY gate census only —
another workflow owned it. It IS in the FRESH/CENSUS numbers.

## How it was measured (instrumentation was THROWAWAY; the tree is clean)

`grade()` is a nested function, so it was instrumented by splicing ONE
recording line into a copy of the source held in memory and `exec`ing it with
`__file__` set to the real path, leaving every sibling-script lookup and every
verdict bit-identical:

```python
src = Path(POLICY_AUDIT).read_text()
OLD = "    def grade(cid, ok, detail_pass, detail_fail):\n        if ok:\n"
NEW = ("    def grade(cid, ok, detail_pass, detail_fail):\n"
       "        _CENSUS(cid, ok, sys._getframe(1))\n        if ok:\n")
assert src.count(OLD) == 1          # splice point moved => census not valid
exec(compile(src.replace(OLD, NEW), POLICY_AUDIT, "exec"),
     {"__name__": "__census__", "__file__": POLICY_AUDIT, "_CENSUS": rec})
```

`_CENSUS` records `cid`, `ok`, `f_lineno` and a `len()`-snapshot of every caller
local. **`f_lineno` lands on the ARGUMENT line, one past the `grade(` line** —
every line number below is the `grade(` line itself. The `check()` side was a
pure AST read of `tests/*.py`; nothing was executed.

## 1. `grade()` — 44 sites, and what each verdict stands over

`policy_audit.py` emits **104 verdict rows: 44 through `grade()` (AST count;
47 raw text matches = 44 + the `def` + one prose comment + one commented-out
call) and 60 through `rows.append()` which BYPASSES `grade()` entirely** (64
`rows.append` sites exist; 4 are `grade()`'s own body). Of the 60: 46 `N-A`,
6 `HUMAN`, 5 `FAIL`, 1 conditional `N-A`/`HUMAN`, 1 computed, and **exactly one
that can emit PASS — `R-LEN` at :1429** (`"PASS" if has_len else "N-A"`), whose
own comment already calls it "VACUOUS: this grades the WORD, not the copper".
A `grade()`-only change reaches 44 of 104 emissions and does NOT reach R-LEN.

### 1a. THE ORACLE — vacuous PASSES (population EMPTY, verdict PASS)

4 check IDs at 4 call sites. **16 instances over 8 board-runs (CENSUS tree);
14 over the 7 board-runs of the PRIMARY tree.** These, and only these, are the
`grade()` PASS→UNGRADED conversions phase 2 must produce.

| ID | site | population | `\|pop\|`=0 on | non-empty elsewhere |
|---|---|---|---|---|
| `M-REPRO` | :1542 | `deps` — `.kicad_pcb` paths regexed out of `03_src/rebuild_all.sh` | pluto-cal-switch, pluto-rx2-8way, pluto-rx2-8way-v2, cooksense, cooksense/interposer, usb-hub-3s-v3 | crow-mic-pod-v2=1, crow-recorder-central-v2=1 |
| `R-POUR` | :1262 | `pwr` — nets in a netclass with `track_width >= 0.5` | crow-mic-pod-v2, pluto-cal-switch, pluto-rx2-8way, pluto-rx2-8way-v2, cooksense/interposer | central-v2=1, cooksense=4, usb-hub-3s-v3=9 |
| `P-KEEP` | :1050 | keepout/mate declarations | crow-mic-pod-v2, cooksense, cooksense/interposer | 2…9 elsewhere |
| `P-POL` | :1024 | `floorplan.yaml asserts.pad_net[]` | cooksense, cooksense/interposer | 5…43 elsewhere |

**M-REPRO is worse than the ADR-0007 case it was found on.** The 15-line
cooksense dispatcher yields `deps == []`, while the two real drivers
(`03_src/cooksense/rebuild_all.sh` 181 lines, `03_src/interposer/rebuild_all.sh`
187 lines) declare 2 deps each and are never read. But **4 more projects yield
`[]` from substantial single-board drivers** — pluto-cal-switch (99 lines),
pluto-rx2-8way (118), pluto-rx2-8way-v2 (187), usb-hub-3s-v3 (63). So
`M-REPRO | PASS | all rebuild inputs git-tracked` is vacuous on **5 of 7
projects**, and the multi-board path split is one cause of five, not the cause.

**P-POL / P-KEEP are a different mechanism and must be converted for a
different reason.** `ok = bool(pol_where)`, so an empty population alone gives
FAIL — but the pass is rescued by a REGEX OVER SOURCE PROSE. On cooksense,
MEASURED: the flat `03_src/floorplan.yaml` and `03_src/route.yaml` **do not
exist** (the real ones are `03_src/cooksense/floorplan.yaml`, 80,994 bytes,
carrying **26** `asserts.pad_net` + **31** keepouts, and
`03_src/cooksense/route.yaml`, 99,118 bytes, 3 `prep.keepouts`;
`03_src/interposer/floorplan.yaml` carries 9 + 0). P-POL's PASS rests on
**exactly one** regex hit in 38,431 bytes of `audit_src`, and that hit is the
word "polarity" **inside an f-string in the gate's own success message**
(`AUDIT PASS: {…} polarity, …`). P-KEEP's 59 hits begin inside a docstring
describing checks. The interposer is additionally graded through
`03_src/audit_board.py`, a symlink to `cooksense/audit_board.py` — the wrong
board's script.

**Side-finding, same root, found by running this census.** `policy_audit.py`
writes its report to one fixed path, `06_build/policy_audit.md`, whichever board
`--board` selected — and on cooksense that file is **git-TRACKED** (one of 35
tracked paths under `projects/*/06_build`, the rest being `contracts.md` and
`verification/`). So grading the interposer OVERWRITES the cooksense report in
place, and the project ends up with one report claiming to be the project's.
It was caught here because the census run dirtied the file and it was restored
with `git checkout --`; a report path should carry the board name when
`len(boards) > 1`, exactly as the `Board graded:` header already does.

### 1b. NO DENOMINATOR VARIABLE AT ALL — latent, not yet firing

4 IDs compute only a findings list; the population is never bound to a
variable, so it can be neither printed nor checked. Their true populations were
measured independently through `pcbnew` and are **non-empty on every board**, so
these are not conversions today — but nothing would report it if they became
empty.

| ID | site | true population, measured | range over 8 boards |
|---|---|---|---|
| `P-SILK-REF` | :1089 | footprints not `FP_BOARD_ONLY` and not waived | 23 … 235 |
| `R-THERM` | :1292 | SMD pads ≥ `therm_pad_area_mm2` on multi-pin parts (4-layer only) | 1 … 8 |
| `P-PLANE` | :1204 | tracks eligible to sit on In1 | 183 … 4181 |
| `P-CRT` | :951 | footprint courtyards checked by `kicad-cli` | 27 … 243 |

### 1c. DELEGATED — the denominator lives in a child process

7 IDs (`E-INV`, `E-ADR`, `E-TOPO`, `E-MARGIN`, `E-OFF`, `A-POP`, `M-DEPEND`)
grade a subprocess exit code. The child may carry its coverage in stdout
(`M-DEPEND` greps an `M-DEPEND coverage:` line; `A-POP` an `A-POP:` line) but
`policy_audit` truncates the detail to 200 chars and never reads a denominator.
A child that grades zero items and exits 0 becomes a PASS here. These need the
child to emit an UNGRADED signal, not a `grade()` change.

### 1d. Already correct — the shape to copy

18 sites already refuse an empty population, and `_adj_row` at :847 is the
model: it returns `N-A` when nothing is declared and requires `bool(graded_)`
so "0 of N budgets reached" cannot read as PASS. `R-RULES` is the other model —
in the FRESH tree its `cands` population is absent and it correctly goes `N-A`
on all 6 boards rather than failing.

## 2. `check()` — the count that decides the phase-1 shape

MEASURED by AST over `tests/*.py` (excluding `harness.py`): **3,829 assertion
call sites.**

| class | sites | what |
|---|---|---|
| LOGIC | 2,738 | `eq`/`contains`/`not_contains` (1,946) + `check()` over computed values (792) — **no population, no meaningful denominator** |
| SUBPROC | 1,033 | `must_pass`/`must_fail` — the verdict is a child gate's exit code |
| EVIDENCE | **58** | `check()` whose condition asks the filesystem, incl. 5 literal `check(False, …)` absence branches |

**Evidence-dependent sites are 58 of 3,829 (1.5%), and 58 of the 850 direct
`check()` calls (6.8%) — a small minority.** A blanket required `over=` on
`check()` would therefore be wrong: it would force a meaningless denominator
onto 2,738 pure logic assertions to reach 58 real ones, and the 2,738 would be
filled in mechanically, which is how a required field becomes decoration.

**The measurement also rules out `check(..., over=)` as sufficient**, because
the empirical flip set (§3) is 8 tests and **6 of them never reach a `check()`
call at all** — they die in `cook_netlist()` at
`tests/t1_electrical_invariants.py:378` on a bare
`raise AssertionError(f"missing real netlist fixture: {COOK_NET}")`, which the
harness's `except Exception` counts as a failure. A parameter on the assertion
primitive cannot see that.

**The shape the measurement supports:** a distinct `Ungraded` outcome in
`harness.py` (a third state beside pass/fail, reported on its own line the way
`vacuity` already is at :214) plus a `require_evidence(path…)` helper called at
the point of evidence ACQUISITION — which is where all 8 flips actually happen.
Leave the 2,738 logic assertions untouched.

## 3. The suite's `failed` count is a function of untracked worktree state

Identical sha `7f5e48cd`, same machine, sequential runs, unpiped
(`> log 2>&1`, exit status preserved). Raw `TOTAL` lines, verbatim:

PRIMARY — `/home/mouse9911/gits/circuits`:
```
  TOTAL                    1109 passed, 9 failed, 660 known-bad fixtures made their checker fail
```
FRESH — `<scratch>/wt_fresh` (`git worktree add --detach`, same sha):
```
  TOTAL                    1101 passed, 17 failed, 654 known-bad fixtures made their checker fail
```

1,113 tests ran in both; **0 ran in only one**; exactly **8 flip**, all
`ok → FAIL`, all on absent `06_build/*` evidence (per-project
`.gitignore:1: 06_build/*`; `git ls-files projects/*/06_build` = 35, none of
them these). 6 of the 8 are `known_bad` fixtures, which is the whole
660 → 654 delta.

| # | suite | test | artifact whose absence flips it |
|---|---|---|---|
| 1 | `t1_electrical_invariants.py` | E-INV part_value passes the cooksense watchdog pull-down as SHIPPED (1k) | `projects/smc0985-cooksense/06_build/netlists/cooksense.net` |
| 2 | " | E-INV part_value FAILS THE INCIDENT: the watchdog pull-down at 100k | same |
| 3 | " | the THREE topology invariants that shipped with the fix PASS on the 100k board | same |
| 4 | " | part_value FAILS a value the netlist carries but the gate cannot decode | same |
| 5 | " | part_value FAILS a min bound and an equals-with-tolerance | same |
| 6 | " | part_value refuses to load an assertion that declares NO bound | same |
| 7 | `t1_net_reference.py:490` | the REAL cooksense pre-fix silk caption is caught | `…/06_build/proof/floorplan_p0proof.yaml` + `…/06_build/netlists/cooksense.net` |
| 8 | `t1_net_reference.py:539` | pluto-cal-switch — resolves EVERY reference | `projects/pluto-cal-switch/06_build/netlists/` |

1–6 route through `cook_netlist()` at `t1_electrical_invariants.py:378`;
7–8 are the `check(False, "missing real evidence: …")` sites named in the brief.

**The same mechanism is visible on the gate side, in the same file, both
directions at once.** Running the fleet gate census in both trees, 215 shared
`(board, check)` rows, 9 differ: `E-INV` flips PASS→FAIL on **all 8 boards**
("no exported netlist found (looked in `06_build/netlists/*.net`,
`04_kicad/*.net`)"), plus `M-REL` on cooksense and `M-BOM` on the interposer.
Meanwhile `R-RULES`, whose population comes from the same kind of absent
`06_build` path, correctly goes `N-A` on all 6. **`E-INV` hard-FAILs an empty
population and `R-RULES` declines to grade it — same file, same tree pair.**
That is the inverse defect and its remedy, side by side.

## Reproduce

```
./tests/run_tests.sh > log 2>&1                    # in each worktree, unpiped
/usr/bin/python3 skills/kicad-pcb/scripts/policy_audit.py projects/<name>
/usr/bin/python3 skills/kicad-pcb/scripts/policy_audit.py \
    projects/smc0985-cooksense --board interposer  # the ADR-0007 split
```
