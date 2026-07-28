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
| `t1_audit.py` | audit_template / audit_board / parity pass a clean board, policy_audit P-SILK-REF passes, M-REL grades a per-board-named release and sorts v1.10 above v1.9 | **courtyard overlap FAILS**, **refdes-on-F.Fab-only FAILS**, pad off-board, missing GND pour, stranded decoupler, renamed net, deleted part, **policy_audit P-SILK-REF FAILS** on an F.Fab-only board, **M-REL reaches into the SIBLING BOARD's release series** (the cooksense/interposer shape — pre-fix it demands `SUPERSEDED.md` on the LIVE cooksense-v1.4), **an UNATTRIBUTABLE release set is a FAIL naming the directory, and M-BOM/A-POP/A-BODY fail with it** (pre-fix: `| M-REL | PASS |` over a release it could not attribute) |
| `t1_placement_gates.py` | the three current boards pass as placed, synthetic two-cluster board with a wide corridor passes, P-CAP waiver with evidence, P-OUT `out_ok` ref waiver | **P-OUT fails a pad outside an L-shaped outline that audit_template I1's RECTANGLE check provably cannot see**, **P-CAP fails a pinched 1.2mm corridor (10 nets vs ~6 slots; red-verified inline with the keepout blockage disabled)**, **the HISTORICAL cooksense pre-REDO board (18392f2, the 13h D-BACK) fails both gates**, waiver without evidence, missing Edge.Cuts is a FAIL not a skip |
| `t1_release_index.py` | numeric-per-component version order, both shipped name shapes parse (incl. a board whose own name ends in `-v2`), `04_kicad` underscores and release-dir hyphens are one board, **the REAL cooksense tree resolves to cooksense-v1.4 and not the last directory**, all 9 projects resolve with a denominator | **THE PRE-FIX SELECTOR, run against the real sealed tree, returns `interposer-v1.0` while the board graded is `cooksense` — the red side is MEASURED on every run, not asserted in a docstring** (4 SUPERSEDED demands pre-fix incl. the live release, 3 post-fix, all 3 of which have the file); 'the latest' with no board named on a two-board project REFUSES; a prefix naming a board the project does not build REFUSES; a bare `v1.0-<date>` in a two-board project REFUSES; a directory that is not a release at all REFUSES |
| `t1_contracts.py` | repo (non-projects) passes contracts_audit, well-governed fixture tree passes, `projects/<name>` placeholder not flagged | **stray unpermitted file FAILS**, **governed subfolder without its contract FAILS**, **ungoverned tree FAILS (C-COV)**, **skills→concrete-project reference FAILS (C-ISO)** |
| `t1_escape_tier.py` | escape_check calibration matches shipped ground truth, P-ESC+P-TIER pass an agreeing part | **the incident config FAILS P-TIER (0.5mm QFN @ standard)**, tampered block, style lie, missing block, tier typo, unescapable package |
| `t1_rules_bom.py` | netclasses + widths reach `.kicad_pro` and `.kicad_dru`, rules_audit passes | **ampacity floor** violated, `.kicad_pro`/`.kicad_dru` disagree, unpatterned net, generate_rules never ran, **unmapped BOM line**, missing BOM, **a genuine second .kicad_pro still aborts (kicad-cli-dropping purge scoped)** |
| `t1_rebuild_templates.py` | rebuild_reuse.sh template: bash -n, DRC gate carries all three flags on one invocation, generate_rules before import AND last after stitch, pinned sch copied before DRC, no tsci, board name derived from config | **ordering assertion rejects rules-before-stitch**, **DRC-flag assertion rejects a dropped --schematic-parity** |
| `t1_jlc_twin.py` | affirmative NO-CAD does not block, cache replays without the network, empty BOM announces it checked nothing, **`xform()` reproduces pcbnew's OWN pad placement exactly** (and the fixture is required to be able to tell the two handednesses apart), `--assembly` reads the coded not-assembled/consigned pairs from the declared home (`--also` still works) | **HTTP 403 = FETCH-FAILED + exit 1**, fetcher crash blocks, timeout blocks, nonzero exit is never NO-CAD, **the fitted `jlc_offset` has the correct handedness (both directions; RED-verified — the pre-fix form returns every 90/270 part 180° off)** |
| `t1_assembly_gates.py` | A-POP passes a fully declared release; **the pcbnew-free board reader agrees with pcbnew on a real sealed board, 195/195, 0 mismatches** (the canon-M1 independence claim is MEASURED, not asserted); A-STOCK passes a parseable PASS verdict, honours the `--json` sidecar, lets a `sourcing_plan` entry clear a line, and says out loud when there is nothing to grade | **cooksense v1.1 FAILS naming all 13 blank-LCSC refs on its CPL**, the interposer v1.0 FAILS (uncoded on CPL + no assembly.yaml + no MANIFEST line), crow-rv2 v1.3 FAILS (its PLACED consigned U1 declared not_assembled), **one extra `exclude_from_pos_files` FAILS naming only that ref**, entry without evidence, reason outside the vocabulary, consign-as-unpopulated, declared-but-not-excluded, MANIFEST drift; **crow-rv2 v1.3 FAILS A-STOCK (its own CPU at `LOW_STOCK(0)`)**, **cooksense v1.1 FAILS with a DISTINCT no-parseable-verdict finding**, **deleting the verdict from PASSING evidence still FAILS**, ungraded line, no evidence at all, verdict-less `--json`, incomplete `sourcing_plan` |
| `t1_net_label_survival.py` | label survival passes an intact netlist, pin_map with `{n}` substitution, evidenced exemption, template rebuild_all wires the semantic battery in canonical order (tsx_preflight BEFORE tsci build; battery right after netlist export) | **the P5VA_4→AUDIO4M merged-label netlist FAILS (LABEL-LOST)**, **a misplanted port pin FAILS (PIN-MAP)**, wired NC pin, exemption without `why:` = config error, zero-net netlist = hard error, **the template battery aborts on a violated invariant with its named GATE FAILED line** |
| `t1_import_provenance.py` | the REAL pluto-cal-switch `mates.yaml` graded against the REAL `spf/plutoplus_hardware/` record (15/15 facts, both disagreeing units consumed), a clean synthetic tree, a board that mates to nothing **saying NOTHING TO GRADE instead of PASS**, a BRIEF that declines to mate, and the gate obeying G-INPUT/G-COVER/G-RED | **the PRE-CALIPER PlutoPlus span as the headline: 35.60 mm ESTIMATED with no bar, spent on a dimension (M-BAR), and the same number graded MEASURED because three extractions agreed to 0.003 mm (M-PROXY)** — both RED-verified by neutering the check (18/2 and 19/1); plus an unparseable bar, a missing grade, an invented grade, an unknown id, **facts.yaml DRIFTED from the record it indexes**, a missing device folder, unparseable yaml, an OWED fact spent dimensionally, OWED with no route, a board RESTATING a value, a consumption with no site, a BRIEF lock with no yaml, and an empty `consumes:` (M-COVER) |
| `t1_tsx_to_board.py` | generic fall-through when `generate_board.py` is absent (ADR-0002 amendment), board name from `floorplan.yaml`, bespoke priority + unchanged legacy path | **no backend at all = FATAL naming BOTH options** (all five red-verified vs the pre-retrofit driver, incl. its latent silent-exit-on-missing-tsx bug) |
| `t1_bom_legibility.py` | the MPN authority prefers a dossier's `mpn:` FIELD over its directory name (the `/` in `LM5116MHX/NOPB`), F-WORDS refuses exactly three shapes and accepts real part names, **F-ENCODE is indifferent between a UTF-8 BOM marker and ASCII `Ohm`**, the exporter's own output passes the INDEPENDENT checker at F-MPN 46/46 and ships a BOM marker, the escape hatch is loud, the F-ECHO worklist is written, a clean echo passes | **the SEALED crow-recorder-central-v2 v1.5 BOM — the one JLC could not process — FAILS all three checks**, **a sealed BOM with NO MPN COLUMN is a FAIL not a skip** (usb-hub-3s v1.0; its 48 rows were excluded from ADR-0006's own 914/1205 denominator), **the two match paths DISAGREE on usb-hub-3s-v3 SW1** (`SS12D07VG6 087` vs the dossier's `SS12D07VG6-087` — the retired side-file's drift, which a blank-only check would pass), zero data rows, an unresolvable code, **F-ECHO catches the C82317 -> C131025 substitution** and a zero-overlap table, **the exporter BLOCKS the incident board and leaves nothing uploadable** (all 5 exporter tests red-verified against the pre-ADR-0006 exporter), **25 of 26 sealed BOMs fail** |

**T2 integration tests** (`t2_route_stitch.py`, fast + `--slow` e2e) — the
generic router/stitcher (`route_and_stitch_generic.py`). Route-prep, the KRT
command line (driven by a hermetic stub router), import, and the stitch pass
ordering. KRT is stochastic, so every assertion is a PROPERTY — argv, pass
order, node sets, exit codes — never bytes.

| suite | clean cases | known-bad cases |
|---|---|---|
| `t2_route_stitch.py` | prep writes a track-free r0 with per-layer keepouts + wave lists, the KRT command line carries geometry/keepout/per-wave overrides, waves are chained rN→rN+1, a wave with no track_width derives it from the netclass floor, `quick` passes a routed board with the routed/deferred split, stitch runs the configured pass order, stitch preserves connectivity, two runs agree on connectivity, a removal pass triggers a SWIG barrier, heal_islands bridges a split same-net pour (2 groups → 1, net-class width, kicad-cli-DRC-verified), heal_islands via-hops through a shared plane when every same-layer gap is blocked, heal_islands never bridges different nets (red-verified with the net guard disabled), heal_islands is idempotent (red-verified with island-seating disabled) | **tracked route input rejected**, **netclass-less project rejected (canon R1)**, **unknown wave net**, **a wave below its class floor fails prep**, **quick catches a planted open + a planted sub-floor track**, **KRT nonzero exit blocks**, **KRT silent no-output caught**, **double-import rejected**, **missing chain file**, **unknown stitch pass**, **no-`fill` pass list**, **unknown KRT flag**, **stitch-grid minimum bites**, **pad-rescue `require:all` bites**, **power-stitch minimum bites**, **a failed gate leaves no stale resume marker**, **a heal with NO legal bridge is a hard error, never a violating bridge (red-verified with the collision check disabled)**, **heal_islands refuses to run before fill** |
| `t2_grind.py` | grind_driver auto-fixes a batch class to 0/0/0 with M9 journal entries per cycle, same-net zone<->zone splits classify as the auto `unconnected_zone_islands` (heal_islands rerun) while pad<->zone stays escalate | **a never-improving board escalates D-BACK within 3 cycles (the driver is UNABLE to loop forever)**, **a novel class escalates immediately with no fix attempt**, **table-escalate classes stop the loop with the compact report**, **--max-cycles caps even an improving run** |

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
| `jlc_twin.xform()` HANDEDNESS: every `jlc_offset` NEGATED — invisible at 0/180, exactly 180° wrong at 90/270; six "authority" rotation rows were populated from it, and a CORRECT sealed release (crow-rv2 v1.2) was "fixed" into a wrong one (v1.3) on that evidence | 2026-07-25 · `1b69760`, `e0d735c` | `t1_jlc_twin.t_xform_matches_pcbnew` (the operator vs pcbnew itself) + `t_fit_offset_handedness` (both fit directions), RED-verified |
| a CPL placing 13 parts whose BOM line has a BLANK LCSC, while the MANIFEST declared 12 of them not_assembled | 2026-07-24 · cooksense v1.1 sealed bytes | `t1_assembly_gates` A-POP names all 13 + the MANIFEST contradiction |
| five sealed releases shipping stock evidence whose LAST LINE says FAIL, one with the board's own CPU at stock 0 | 2026-07-23/24 · crow-rv2 v1.0-v1.3 sealed bytes | `t1_assembly_gates` A-STOCK, incl. "deleting the verdict still FAILS" |
| **a FIXTURE laid on top of existing copper, so the DRC violation CLASS it asserted was order-dependent — the SUB-FLOOR test flaked at 4.6% (3/65, serial) and was excused twice as "the known temp-path flake"** | 2026-07-27 · ADR-0005 | `add_track`'s ISOLATION ASSERT + `t_add_track_rejects_a_contaminated_site` (RED-verified by neutering the assert) |
| **RELEASE SELECTION picked the wrong release and said nothing — three instances of one class.** `rels[-1]` over a MULTI-BOARD `07_releases/` resolved to the sibling board (`interposer-v1.0`) while the audit graded `cooksense`, so M-REL/M-BOM/A-POP/A-BODY all reported on the wrong archive and M-REL demanded `SUPERSEDED.md` on the LIVE `cooksense-v1.4`, blocking its v1.5 seal; `v1.10` sorted before `v1.9` as TEXT (fixed in M-REL, left standing in `shopping_list` — the M-WIDTH failure); `_version_key`'s `^v` regex opted every board-prefixed release out of the stale check | 2026-07-27 (a) · 2026-07-27 (b) · 2026-07-24 (c) | `t1_release_index.py` — one implementation (`release_index.py`) with 5 known-bad; the headline RUNS THE PRE-FIX SELECTOR against the real sealed tree, plus `t1_audit.t_mrel_scopes_to_the_board_under_audit` / `t_mrel_unattributable_release_set_fails` and `t1_shopping_list.t_newest_release_is_numeric_not_text`, all RED-verified |
| E-TOPO printed `fuse rated 3401 A` on a board with NO such fuse: an unanchored `([\d.]+)\s*A` read the part number `AO3401A` out of an ORDER_README line whose true rating, 2 A, is four tokens later (`SMAJ5.0A` reads as 5.0 A the same way) | 2026-07-27 · crow-recorder-central-v2 sealed READMEs | `t1_power_topology` — the incident line is graded at 2 A, the two decoys are refused, and the message NAMES the file+line it read |

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
`audit_board` PASS. `t2_route_stitch.py` adds the routing half: both boards
run generate → rules → prep → **real KRT** → import → stitch → rules-last →
DRC, and must reach 0 violations / 0 unconnected / 0 parity (cook-loadcell
also re-checks netlist parity 0 vs the sealed board). KRT is stochastic, so
this asserts the 0/0/0 PROPERTY across a fresh route, not a golden board.

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
- `audit_template.py` and `classified_drc.py` write pid-suffixed DRC
  reports (`/tmp/audit_drc.<pid>.txt`, `/tmp/classified_drc.<pid>.txt`).
  They used to share two FIXED paths, and a concurrent session (a live
  clean-room canary running the same scripts) clobbered a suite run's
  report mid-read — two t4 flakes with another board's categories in the
  output (2026-07-21). Per-process paths ended that class.
  **AND THEN THIS NOTE BECAME AN EXCUSE.** A SECOND, unrelated flake with a
  similar symptom (`t_subfloor_crossnet_clearance_is_real`, missing `REAL=1`)
  was twice waved off as "the known temp-path flake, commit 2de4b2a" — but it
  measured **3/65 = 4.6% running strictly SERIALLY**, with no concurrency and
  no second `kicad-cli` anywhere, which alone refutes a shared path. It was
  the fixture: the injected track pair sat on the sealed board's existing
  copper, KiCad emits one violation class per neighbourhood, and pcbnew's
  `Save()` does not order Python-added tracks stably. Fixed 2026-07-27 by
  moving the pair to clear copper and making the fixture assert its own
  isolation; the `REAL=1` expectation was NOT weakened. **A named prior flake
  is a hypothesis, not a diagnosis — measure the rate before you reuse the
  name.**
- No pytest: `harness.py` is a ~60-line runner so the suite runs on the
  KiCad interpreter with zero installs.
