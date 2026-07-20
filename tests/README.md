# tests/

    ./tests/run_tests.sh              # fast tier (default) — seconds to ~2 min
    ./tests/run_tests.sh --slow       # + e2e real-board regeneration
    ./tests/run_tests.sh --only=fpid  # filter by test name (regex)

Everything in the default tiers is **hermetic**: the network is mocked, and
no sealed `04_kicad` board, release, or project file is ever written. Tests
build scratch trees under `/tmp` and read the real projects only.

---

## The principle: test the CHECKERS, not just with them

A gate that cannot fail is worthless. This is not hypothetical — two gates
in this repo were shipping green on real defects when the suite was written:

- **`jlc_twin` exited 0 on 11 unverified parts.** Its fetch classifier
  treated any error message it didn't recognise (an `HTTP Error 403`, a
  traceback) as `NO-CAD` — a *disposition* meaning "the library genuinely
  has no model" — instead of a failure. A part we could not fetch was never
  checked, but the run reported success.
- **`audit_template` printed `AUDIT: PASS` on stacked parts.** Its overlap
  check was bounding-BOX and warn-only, so two footprints occupying the same
  space produced a warning nobody read.

Both are now fixed *and pinned by a known-bad fixture*. The fix without the
fixture would just rot back.

So **every checker gets two kinds of test**:

| kind | asserts |
|---|---|
| `clean` | the checker PASSES a good input |
| `known_bad` | the checker **FAILS** a deliberately broken input |

The runner reports them separately and **refuses to report success if zero
known-bad fixtures ran**:

    TOTAL   50 passed, 0 failed, 26 known-bad fixtures made their checker fail

"50 tests pass" means nothing on its own. The second number is the one that
says the gates can still bite.

### Assert PROPERTIES, never file bytes

KRT routing is stochastic and the silk de-collision search is
order-dependent, so golden-file comparison would be permanently broken.
Compare node sets, counts, exit codes, and report substrings — never a hash
of a `.kicad_pcb`. `e2e_boards.py` has an explicit test for this: two runs
must agree on *connectivity*, not on bytes.

### Known-bad fixtures are good inputs broken in exactly ONE way

`harness.edit_board()` mutates a freshly generated board with a pcbnew
snippet; `t1_generate_board.scratch_config()` does the same for a floorplan
YAML. Building the bad case by breaking the good case is what proves the
checker reacts to *that* defect and not to some unrelated malformation.

---

## Tiers

**T0 fixtures** (`fixtures/t0/`, seconds) — tiny hand-authored `circuit.json`
inputs. See `fixtures/t0/README.md`.

| fixture | catches |
|---|---|
| `two_resistors` | baseline: sheet is annotated and exports nets at all |
| `polarized` | pad-1 net identity survives conversion (diode/cap orientation) |
| `manypin_custom_fp` | **the `Device:U_chip` collision**: two hand-footprinted chips must export 41 and 24 pins, not 2 each |
| `digit_rails` | leading-digit rail aliasing (`N5V` -> `5V`, `N3V3` -> `3V3`) |

**T1 unit tests** (fast) — one suite per component:

| suite | clean cases | known-bad cases |
|---|---|---|
| `t1_converter.py` | unique lib_symbol per refdes, pins keyed to KiCad pad name, annotated, ERC 0, 41-pin regression, rail canonicalisation, FPID resolution | pin-count assertion has teeth, sheet/board parity rejects a mismatch, empty circuit cannot pass parity |
| `t1_generate_board.py` | parts land per config, anchors unmoved, F.Fab copies, parity 0 | **missing FPID = hard error**, unknown footprint, violated polarity assert, over-subscribed floorplan, unknown zone net |
| `t1_audit.py` | audit_template / audit_board / parity pass a clean board, policy_audit P-SILK-REF passes | **courtyard overlap FAILS**, **refdes-on-F.Fab-only FAILS**, pad off-board, missing GND pour, stranded decoupler, renamed net, deleted part, **policy_audit P-SILK-REF FAILS** on an F.Fab-only board |
| `t1_rules_bom.py` | netclasses + widths reach `.kicad_pro` and `.kicad_dru`, rules_audit passes | **ampacity floor** violated, `.kicad_pro`/`.kicad_dru` disagree, unpatterned net, generate_rules never ran, **unmapped BOM line**, missing BOM |
| `t1_jlc_twin.py` | affirmative NO-CAD does not block, cache replays without the network, empty BOM announces it checked nothing | **HTTP 403 = FETCH-FAILED + exit 1**, fetcher crash blocks, timeout blocks, nonzero exit is never NO-CAD |

**T4 regression corpus** (`t4_regressions.py`, fast) — one named test per
incident this project has already paid for, so none can silently return.
Every test names the defect, its DATE, and the commit or doc that records it.

| incident | date · source | pinned by |
|---|---|---|
| jlc_twin exited 0 on 11 unverified parts (HTTP 403 read as NO-CAD) | 2026-07-20 · `f67ccfa` | all 11 recorded FETCH-FAILED, none NO-CAD, exit 1 |
| LM5145 footprint MIRROR-NUMBERED = dead board (reached fab) | 2026-07-16 · `522d61c`, usb-power-3s v1.0 `SUPERSEDED.md` | twin blocks a mirrored land pattern; and does *not* accuse an identical one |
| wrong-PITCH footprint on a self-consistent board (U7 SSOP-8) | 2026-07-19 · `d0ed295` | twin blocks a wrong-scale land pattern |
| `Device:U_chip` collision truncating many-pin chips to 2 pins | 2026-07-19 · `d37fc92` | per-refdes symbol ids; 41 and 24 pins survive |
| XT60 battery polarity REVERSED — '+' net on the '-' blade | 2026-07-14 · spf `fa0b9c1` | pad-1-net assert is a hard generator error; P-POL fails a project with no scripted check |
| 6A switch-node copper routed as 0.15mm thin-pass tracks | 2026-07-14 · spf `c4b8cdb`/`a5e7ca7` | `A-AMP` on 6A/0.15mm; plus a test showing DRC is blind to it |
| netclasses clobbered by pcbnew save (generate_rules must run LAST) | 2026-07-17 · `ae93b4b`, contracts.md line 5 | new `A-ORDER` check on `rebuild_all.sh` |
| a WAIVER INHERITED BY COPY, its rationale re-presented as fresh judgement | 2026-07-20 · canon M4 | new `waiver_provenance.py` — `W-COPY` / `W-FOREIGN` |
| DRC violations COUNTED rather than CLASSIFIED | 2026-07-13 · spf `96785a0` | identical geometry 0.10mm apart: one REAL, one margin |
| auto/AI placement blind to electrical proximity | 2026-07-13 · spf `47e0f82`/`96785a0`, `17fea03` | IP gate at the incident distance; *all* violators reported |
| a release shipped with NO refdes on silk | 2026-07-17 · esp32 v1.0 `SUPERSEDED.md`, `cfbc83b` | whole-board F.Fab-only, and the hidden-text variant |
| a part in the schematic that never reached the board | 2026-07-14 · spf `bed8ace` | netlist parity names the missing refdes |

Two things this file does that the T1 tiers do not:

* **Verified red against pre-fix code.** Where the fix lives in current code,
  the old version was swapped back in and the test confirmed to FAIL. The
  test comment records it. Eight were verified this way; the ones that could
  not be are named below.
* **Says so when it cannot reproduce.** Three incidents are recorded as NOT
  REPRODUCED at the top of `t4_regressions.py` rather than covered by a test
  that passes vacuously — most importantly, the `.kicad_pro` clobber itself
  does not reproduce on this KiCad build, so what is pinned is the ordering
  contract the clobber forced, not the clobber.

**E2E** (`--slow`) — regenerate cook-loadcell and crow-array-pod with the
generic generator and assert netlist parity 0 against the sealed boards plus
`audit_board` PASS.

**Live network** (`--net`) — opt-in only, never in CI-by-default. No such
suite ships today; add it as `net_live.py` if you need a real EasyEDA fetch.

---

## How the network is mocked

`jlc_twin` shells out to `easyeda2kicad`, which is a complete and
deterministic seam — no HTTP interception needed.

- **Failure injection**: `stub_e2k()` writes a fake fetcher binary and points
  `$EASYEDA2KICAD` at it. It can print any message and exit any code.
- **Replay**: `fetch()` returns early when
  `OUTDIR/easyeda/<LCSC>/jlc.pretty/*.kicad_mod` is non-empty, so the
  per-code cache dir *is* the fixture store. Seed it and the fetcher is never
  invoked — `t_cache_replay` proves this by pointing `$EASYEDA2KICAD` at a
  stub that would fail loudly if called.
- **Record**: to capture a real part, run `jlc_twin` once with the network on
  and copy `OUTDIR/easyeda/<CODE>/` into a fixture dir.

---

## Adding a regression when a new defect is found

This is the whole workflow — follow it every time something ships broken.

1. **Write the known-bad fixture first, and watch it FAIL** against the
   current code. If it passes, you have not reproduced the defect, or the
   gate you are testing is not the gate that missed it.

   ```python
   @test("audit_template FAILS on <the new defect>", kind="known_bad")
   def t_new_defect():
       d, b = fresh_board()
       edit_board(b, "<pcbnew snippet that introduces exactly this defect>")
       r = run([KPY, AUDIT_T, b, "--config", with_audit_cfg(d)])
       must_fail(r, "audit_template on <defect>", "<expected rule id>")
   ```

2. **Fix the checker** so the fixture fails it.

3. **Prove the test has teeth.** Swap the old checker back in and confirm the
   new test fails against it:

   ```sh
   cp skills/.../checker.py /tmp/fixed.py
   git show HEAD:skills/.../checker.py > skills/.../checker.py
   ./tests/run_tests.sh --only="<new test name>"      # must FAIL
   cp /tmp/fixed.py skills/.../checker.py
   ```

   A regression test that passes both before and after the fix is testing
   nothing. Do this step — it is how both gates above were verified.

4. Note the real-world incident in the test's docstring. Every known-bad
   fixture in this suite corresponds to a defect that actually shipped;
   the docstring is where that context lives.

## Interpreter notes

- `/usr/bin/python3` is the KiCad-bundled interpreter and the only one with
  `pcbnew`. `run_tests.sh` checks for it up front and refuses to run without.
- `audit_template.py` writes `/tmp/audit_drc.txt` and `classified_drc.py`
  writes `/tmp/classified_drc.txt` — both hardcoded, so do not parallelise
  those two suites.
- No pytest: `harness.py` is a ~60-line runner so the suite runs on the
  KiCad interpreter with zero installs.
