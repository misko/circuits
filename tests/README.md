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
| `vacuity` | the checker **PASSES** input whose graded fact is FALSE — a *declared blind spot* (canon G-VACUOUS) |

### The third kind: `vacuity` — a blind spot, pinned on purpose

`known_bad` proves a gate *can* fail. It does not prove the gate can fail **on
the case it exists for**, and six gates were measured green on 2026-07-28/29
with their subject false — `R-LEN` passing cooksense on the word `lengthens` in
a comment about creepage, a `.kicad_dru` barrier rule exempting the very
connector tab it was written for (1.0672 mm against a 6.000 mm constraint),
A-RENDER's verdict resting on 2 of 203 parts, a waiver typed `2.62 mm` that
measures 3.085 mm. See the `G-VACUOUS` row in `design-policies.md`.

So a gate declares its blind spot in **two bound homes**: a `VACUITY:` block in
its module docstring, and

    @test("...", kind="vacuity", gate="<basename>.py")

in `tests/`, which constructs that input and asserts the gate **passes** on it.
`gate_contract_audit.py` fails prose with no fixture, a fixture with no prose,
and a fixture whose *first* assertion is `must_fail` (that would disprove the
blind spot it claims). A declaration without a fixture is worse than none: it
reads as diligence and grades nothing.

Two conventions, both load-bearing:

- **Subject first, then the CONTRAST.** Assert `must_pass` on the blind-spot
  input, *then* `must_fail` on the same input changed in exactly one way. The
  contrast is what distinguishes a blind spot from a fact the gate cannot
  represent at all — every one of the fixtures seeded on 2026-07-29 has one.
- **Closing the blind spot is expected to BREAK the fixture.** That breakage is
  the ratchet, not a regression: convert it to `known_bad`. The runner prints
  these separately, and the count is not a success metric — it is an inventory
  of places a gate is *known* to pass while the fact is false:

      1 DECLARED BLIND SPOT(S) reproduced: a gate passing on input whose
      graded fact is FALSE (G-VACUOUS)

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
| `t1_converter.py` | unique lib_symbol per refdes, pins keyed to KiCad pad name, annotated, ERC 0, 41-pin regression, rail canonicalisation, FPID resolution | **a wire root carrying two different LABEL NAMES falls back to `--mode grid`** — the merge happens on LABELS, not pins, and a MID-SEGMENT label was a singleton in the union-find so no guard could see it (smc0985-cooksense: `3V3_ANALOG` mid-segment on a `3V3` wire, 3 segs dropped, SUCCESS declared, 191 nets and no `3V3_ANALOG`; caught only by S-NETMERGE at 161/162). Carries the adjacent-property check that a net's OWN mid-segment label still imports, or every board goes to grid mode; pin-count assertion has teeth, sheet/board parity rejects a mismatch, empty circuit cannot pass parity |
| `t1_generate_board.py` | parts land per config, anchors unmoved, F.Fab copies, parity 0 | **missing FPID = hard error**, unknown footprint, violated polarity assert, over-subscribed floorplan, unknown zone net |
| `t1_audit.py` | audit_template / audit_board / parity pass a clean board, policy_audit P-SILK-REF passes, M-REL grades a per-board-named release and sorts v1.10 above v1.9 | **courtyard overlap FAILS**, **refdes-on-F.Fab-only FAILS**, pad off-board, missing GND pour, stranded decoupler, renamed net, deleted part, **policy_audit P-SILK-REF FAILS** on an F.Fab-only board, **M-REL reaches into the SIBLING BOARD's release series** (the cooksense/interposer shape — pre-fix it demands `SUPERSEDED.md` on the LIVE cooksense-v1.4), **an UNATTRIBUTABLE release set is a FAIL naming the directory, and M-BOM/A-POP/A-BODY fail with it** (pre-fix: `| M-REL | PASS |` over a release it could not attribute) |
| `t1_placement_gates.py` | the three current boards pass as placed, synthetic two-cluster board with a wide corridor passes, P-CAP waiver with evidence, P-OUT `out_ok` ref waiver | **P-OUT fails a pad outside an L-shaped outline that audit_template I1's RECTANGLE check provably cannot see**, **P-CAP fails a pinched 1.2mm corridor (10 nets vs ~6 slots; red-verified inline with the keepout blockage disabled)**, **the HISTORICAL cooksense pre-REDO board (18392f2, the 13h D-BACK) fails both gates**, waiver without evidence, missing Edge.Cuts is a FAIL not a skip |
| `t1_release_index.py` | numeric-per-component version order, both shipped name shapes parse (incl. a board whose own name ends in `-v2`), `04_kicad` underscores and release-dir hyphens are one board, **the REAL cooksense tree resolves to cooksense-v1.4 and not the last directory**, all 9 projects resolve with a denominator | **THE PRE-FIX SELECTOR, run against the real sealed tree, returns `interposer-v1.0` while the board graded is `cooksense` — the red side is MEASURED on every run, not asserted in a docstring** (4 SUPERSEDED demands pre-fix incl. the live release, 3 post-fix, all 3 of which have the file); 'the latest' with no board named on a two-board project REFUSES; a prefix naming a board the project does not build REFUSES; a bare `v1.0-<date>` in a two-board project REFUSES; a directory that is not a release at all REFUSES |
| `t1_release_freshness.py` | the four earlier supersede modes, plus **`--sourcing-supersede`** (canon M8): a part substitution whose MPN+LCSC move on one row and whose `.tsx` moves with it PASSES, and the real sealed usb-hub-3s-v3 v1.11 passes against v1.10; plus **`--value-change-supersede`**: a re-valued 22k pair whose CPL delta is 2 `Val` cells and whose BOM delta is the 2 DECLARED refs PASSES, and the five earlier modes are each shown to still refuse that same tree | **13 known-bad on the sourcing mode alone** — a changed Footprint, a dropped row, a REORDERED designator list, a blanked MPN, a BOM that moved with no `.tsx` change (the HAND-EDITED class, canon M3), an UNDOCUMENTED substitution (neither code in MANIFEST/README), a moved CPL, a changed board md5, a changed gerber **while the same test proves a RE-PLOT of the same copper is still accepted** (a strip list too wide is as wrong as one too narrow), a supersede that substitutes nothing, an MPN-only edit (that is `--legible-bom`'s job), an added fab file, and a BOM failing F-LEGIBLE. GIT-SWAP RED-VERIFIED: pre-fix **0 passed / 14 failed**, post-fix **14 / 0 / 13 known-bad**. **17 more on the value-change mode** — the three headline ones (a moved CPL COORDINATE, a BOM edit on an UNDECLARED designator, a CHANGED GERBER) each carry an inline ADJACENT-PROPERTY red-verify: the same tree with that one property RESTORED must PASS, re-measured every run, because a git-swap red on a brand-new flag proves only that the flag is new. Plus a moved rotation, an undeclared `Val` move, a HAND-EDITED CSV (no source moved, canon M3), a board edited without its schematic (the shortcut that leaves `--schematic-parity` reporting `footprint_symbol_mismatch`), a new Comment against the OLD part's LCSC (**the R12/R30 wrong-part class**), BOM and CPL DISAGREEING about the new value (they come from one `fp.GetValue()` call), a changed Footprint, a designator list WIDER than the real delta, a supersede that re-values nothing, a dropped BOM ref, an undocumented change, an added fab file, a non-authoring `source/` change, and a run with no `--designators` at all. GIT-SWAP RED-VERIFIED 2026-07-28: pre-fix **0 passed / 18 failed / 0 known-bad**, post-fix **18 / 0 / 17**; whole file 56/18/41 -> 74/0/58. HARNESS INTEGRITY re-measured on the new suite (the commit-`0dd56ab` class, where the runner could exit 0 while reporting failures): breaking one new assertion makes `run_tests.sh --only=value-change` print `17 passed, 1 failed` / `FAILURES PRESENT` and **exit 1** |
| `t1_status.py` | **the beacon reader** (`pcb_status.py`): fresh/live-pid/done/blocked boards are not STALLED, multi-board `STATUS-<board>.md` scoping. **The beacon GATE** (`status_beacon_check.py`, canon M-BEACON): a beacon naming the LIVE release against the REAL sealed release set passes; the fleet is graded with a full `N/M` denominator (asserted; the VERDICT deliberately is not — see below) | STALLED detection + the age test RED-verified against a classifier that drops it. **The known-bads are REAL DRIFTED BEACONS, verbatim at 98f4c3a** (`fixtures/beacons/`, PROVENANCE.md): **`M-BEACON-DUP` on the file that had v1.2's frame APPENDED under v1.1's** (4 duplicated fields; the reader rendered `sealed / done` over a SUPERSEDED release), **`M-BEACON-REL` naming v1.2 while v1.3 is live**, **`M-BEACON-AGE` predating that seal**, **`M-BEACON-FIELD` on the cooksense beacon with no `step:`/`op_pid:`/`updated:` at all**, AGE biting ALONE on a beacon broken in exactly one way, a zero denominator, and **the mtime ADJACENT-PROPERTY red-verify** — the fixture's file is seconds old and still stale, same input opposite verdict. Measured when the gate landed: 13 findings across 4 of 6 fleet beacons. **usb-hub-3s-v3 is deliberately NOT asserted**: its beacon was left drifted while its v1.11 seal ran elsewhere, to test on a live seal whether the RITUAL refreshes it |
| `t1_contracts.py` | repo (non-projects) passes contracts_audit **and its verdict CARRIES ITS DENOMINATOR** (`243/6958 tracked; 6715 NOT GRADED` — the default invocation grades 3.5% of the tree and `0 violations` was reading as coverage), well-governed fixture tree passes, `projects/<name>` placeholder not flagged | **stray unpermitted file FAILS**, **governed subfolder without its contract FAILS**, **ungoverned tree FAILS (C-COV)**, **skills→concrete-project reference FAILS (C-ISO)**, **a MARKDOWN PIPE no longer tears a pattern cell in four** — `` `*.c\|*.h\|*.rs\|*.py` `` permits all four, escaped or inside a code span, and the known-bad is the ASYMMETRY in ONE tree (`main.c` AND `pinmap.h` pass while `notes.md` still FAILS); the shipped 05_firmware TEMPLATE permits a header and a `src/` tree; **the 01_docs contract's OWN prompt-hash command is EXTRACTED and RUN** and must reproduce a recorded digest and refuse an altered prompt |
| `t1_escape_tier.py` | escape_check calibration matches shipped ground truth, P-ESC+P-TIER pass an agreeing part, the proven-parts ledger parses and every `` see `x` `` cross-reference RESOLVES, P-ADJ-UNREACHED passes when every keep_short budget resolves | **the incident config FAILS P-TIER (0.5mm QFN @ standard)**, tampered block, style lie, missing block, tier typo, unescapable package; **S-VER now reads the KEY, not the first place the word appears** — a citation hidden behind a `# ... verified: figure 3` COMMENT FAILS, and so does one the 300-char window rescued by matching `p 4` out of a PPTC's `Itrip 4A` three keys later (the real MF-MSMF200L-2; 15 of 557 fleet part.yaml had grep-vs-key disagreement); **P-ADJ-UNREACHED** FAILS a keep_short budget whose net has <2 pads, naming the net (**61 of 119 fleet budgets, 51%, were graded by NOTHING**) — a SEPARATE ID so the two existing P-ADJ span waivers cannot absorb it, proven by making the two verdicts disagree; **the proven-parts validator BITES** — six mutations of the shipped ledger each produce their own finding |
| `t1_rules_bom.py` | netclasses + widths reach `.kicad_pro` and `.kicad_dru`, rules_audit passes | **ampacity floor** violated, `.kicad_pro`/`.kicad_dru` disagree, unpatterned net, generate_rules never ran, **unmapped BOM line**, missing BOM, **a genuine second .kicad_pro still aborts (kicad-cli-dropping purge scoped)** |
| `t1_rebuild_templates.py` | rebuild_reuse.sh template: bash -n, DRC gate carries all three flags on one invocation, generate_rules before import AND last after stitch, pinned sch copied before DRC, no tsci, board name derived from config. **M-FRESH (canon, 2026-07-30)**: every `circuit.json` `rebuild_all.sh` GRADES is one it WRITES from `dist/`, and the driver STAMPS before `tsci build` and VERIFIES between the build and the converter; `build_provenance.py` passes when the converter input IS the builder's output | **ordering assertion rejects rules-before-stitch**, **DRC-flag assertion rejects a dropped --schematic-parity**; **the PRE-FIX TEMPLATE (`git show e50be3f`) is rejected by the wiring check** (measured: 17 passed / 3 failed, `consumed=['03_tscircuit/build/circuit.json'] produced=[]`); **THE INCIDENT ITSELF — `build/circuit.json` holds an obsolete pad-numbering scheme, `tsci build` writes the corrected one to `dist/src/<TSX>/`, the converter is handed `build/`** and F-PATH fires, with the fixture asserting inline that the stale bytes are VALID json (which is why nine parser-shaped checkers passed them); **a `touch` on the stale file cannot forge freshness** — and that fixture is the only one that catches the plausible wrong implementation (measured: swapping the sha256 equality for `artifact newer than producer` leaves the incident test PASSING at 19/1); F-VOID on a build that wrote nothing, **F-KNOB on the `BOARD=power3s` shape caught at `stamp`, i.e. BEFORE the build**, F-NORUN on a board whose driver never completed a run, F-STALE once the tscircuit sources move past the last verified build, the audit's UNREACHED/OWED/FAIL trichotomy never rendering as a pass (M-COVER), and F-KNOB still biting on a driver that never adopted the stamp (the ratchet is not an amnesty). Five mutations RED-VERIFIED, each isolating exactly one fixture |
| `t1_jlc_twin.py` | affirmative NO-CAD does not block, cache replays without the network, empty BOM announces it checked nothing, **`xform()` reproduces pcbnew's OWN pad placement exactly** (and the fixture is required to be able to tell the two handednesses apart), `--assembly` reads the coded not-assembled/consigned pairs from the declared home (`--also` still works) | **HTTP 403 = FETCH-FAILED + exit 1**, fetcher crash blocks, timeout blocks, nonzero exit is never NO-CAD, **the fitted `jlc_offset` has the correct handedness (both directions; RED-verified — the pre-fix form returns every 90/270 part 180° off)** |
| `t1_assembly_gates.py` | A-POP passes a fully declared release; **the pcbnew-free board reader agrees with pcbnew on a real sealed board, 195/195, 0 mismatches** (the canon-M1 independence claim is MEASURED, not asserted); A-STOCK passes a parseable PASS verdict, honours the `--json` sidecar, lets a `sourcing_plan` entry clear a line, and says out loud when there is nothing to grade | **cooksense v1.1 FAILS naming all 13 blank-LCSC refs on its CPL**, the interposer v1.0 FAILS (uncoded on CPL + no assembly.yaml + no MANIFEST line), crow-rv2 v1.3 FAILS (its PLACED consigned U1 declared not_assembled), **one extra `exclude_from_pos_files` FAILS naming only that ref**, entry without evidence, reason outside the vocabulary, consign-as-unpopulated, declared-but-not-excluded, MANIFEST drift; **crow-rv2 v1.3 FAILS A-STOCK (its own CPU at `LOW_STOCK(0)`)**, **cooksense v1.1 FAILS with a DISTINCT no-parseable-verdict finding**, **deleting the verdict from PASSING evidence still FAILS**, ungraded line, no evidence at all, verdict-less `--json`, incomplete `sourcing_plan` |
| `t1_net_label_survival.py` | label survival passes an intact netlist, pin_map with `{n}` substitution, evidenced exemption, template rebuild_all wires the semantic battery in canonical order (tsx_preflight BEFORE tsci build; battery right after netlist export) | **the P5VA_4→AUDIO4M merged-label netlist FAILS (LABEL-LOST)**, **a misplanted port pin FAILS (PIN-MAP)**, wired NC pin, exemption without `why:` = config error, zero-net netlist = hard error, **the template battery aborts on a violated invariant with its named GATE FAILED line** |
| `t1_import_provenance.py` | the REAL pluto-cal-switch `mates.yaml` graded against the REAL `spf/plutoplus_hardware/` record (15/15 facts, both disagreeing units consumed), a clean synthetic tree, a board that mates to nothing **saying NOTHING TO GRADE instead of PASS**, a BRIEF that declines to mate, and the gate obeying G-INPUT/G-COVER/G-RED | **the PRE-CALIPER PlutoPlus span as the headline: 35.60 mm ESTIMATED with no bar, spent on a dimension (M-BAR), and the same number graded MEASURED because three extractions agreed to 0.003 mm (M-PROXY)** — both RED-verified by neutering the check (18/2 and 19/1); plus an unparseable bar, a missing grade, an invented grade, an unknown id, **facts.yaml DRIFTED from the record it indexes**, a missing device folder, unparseable yaml, an OWED fact spent dimensionally, OWED with no route, a board RESTATING a value, a consumption with no site, a BRIEF lock with no yaml, and an empty `consumes:` (M-COVER) |
| `t1_tsx_to_board.py` | generic fall-through when `generate_board.py` is absent (ADR-0002 amendment), board name from `floorplan.yaml`, bespoke priority + unchanged legacy path | **no backend at all = FATAL naming BOTH options** (all five red-verified vs the pre-retrofit driver, incl. its latent silent-exit-on-missing-tsx bug) |
| `t1_copper_length.py` | REALIZED COPPER LENGTH (canon R-LEN). A genuinely matched pair PASSES at spread 0.0000 mm; a member is an ORDERED NET CHAIN so 8+12 and 12+8 both measure 20.000 mm; an ARC is r*theta and not its chord; a via barrel is priced at 1.1896 mm from a DECLARED `stackup_mm`; the phase conversion prints (6.105 ps/mm, 13.19 deg/mm, both re-derived from the ordered stackup and corroborating the two boards' ADRs within 2%); and **the pcbnew-free reader AGREES WITH `PCB_TRACK.GetLength()` on four real routed boards — 351 nets, 0 disagreements above 1 um** (the canon-M1 independence claim is MEASURED, since pcbnew generated and imported this copper). The census reproduces the fleet's ONE honest bespoke length check, crow-recorder-central-v2's USB pair, at 23.6209 / 23.5110 mm, spread 0.1099 mm — canon M8's second strike, and the reason its 3-component/0-branch topology must NOT fail. | **THE HEADLINE IS THE VACUITY ITSELF, RE-MEASURED EVERY RUN: the PRE-FIX R-LEN predicate is RUN against smc0985-cooksense's REAL `audit_board.py` and PASSES on two CREEPAGE COMMENTS**, and passes a file whose entire content is `# the slot is length-adjusted` — while the new gate on the same tree says N-A with a zero denominator and never prints `PASS`. Plus: two arms 1.5 mm apart FAIL naming 19.79 deg at 6 GHz; **the PIN bites where the ceiling does not** (0.6 mm spread inside a 1.0 mm ceiling but off a published 0.0 +-0.05 mm — the two verdicts disagree on purpose, because a re-route silently turns published picoseconds into fiction); ONE VIA on ONE arm FAILS `no_vias` (the only place that ban is graded anywhere — nothing in the router enforces it); THREE separate UNREACHED reasons each asserted alone (a ZONE, a via with no stackup, a BRANCH) and none may render as PASS, with `--strict` making the coverage gap exit 1; an UNROUTED board is UNREACHED WITH ITS COUNT naming every net (**which is exactly what both pluto boards report today**); a spread with no `congruent_pads:` claim is printed and NOT graded; seven malformed declarations exit 2 UNGRADED; a TRUNCATED `(segment)` exits 2 rather than under-reporting copper; and E-NETREF grades the declaration where it ENTERS as kind **K12**, with an inline adjacent-property re-verify that the same block with the typo FIXED resolves. |
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
| **THE HARNESS ITSELF, REINTRODUCED.** `0dd56ab0` swept nine suites ending in `main()` instead of `sys.exit(main())` — they printed "N failed" and exited 0, and the runner printed `ALL SUITES PASSED` over red. It pinned NOTHING, so `t1_layout_precedent.py`, created three days later at `bcec2fd6`, carried the bug straight back in and hid its own `PREC_GRADED_FLOOR` ratchet failure. **Second, independent instance in the runner:** `rc` came from each suite's EXIT STATUS while `TF` came from a STDOUT grep, and only `rc` was read — so the two channels could disagree and the printed verdict was the wrong one | 2026-07-27 `0dd56ab0` → 2026-07-30 `bcec2fd6` | `t4_regressions.t_every_suite_propagates_and_is_wired_in` — **executes each suite's `__main__` block with `main` stubbed to return 1** and asserts the SystemExit code, so it grades the PROPERTY (exit-code propagation), not the string `sys.exit(main())` that `0dd56ab0`'s own sweep false-positived `t3_acceptance.py` on. Same sweep asserts every `t*.py` on disk is WIRED INTO `run_tests.sh` (**measured: `t1_release_required.py` — A-EVID, 6 tests, 4 known-bad — had never once run**). Known-bad sibling `t_exit_code_guard_bites_a_bare_main` keeps the sweep from becoming a gate that cannot fail once the tree is clean. `run_tests.sh` now fails on EITHER channel and names the disagreement. **RED-VERIFIED both halves on the real defect**: the sweep, run before the one-line repair, printed `['t1_layout_precedent.py']`; and on that same tree the **pre-fix runner printed `1 failed` AND `ALL SUITES PASSED` and exited 0**, where the fixed one prints `FAILED: HARNESS DISAGREEMENT` and exits 1 |

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

## Which real bytes may a fixture read?

A fixture that asserts something about a REAL board must read bytes that cannot
move under it. Three legal oracles, in order of preference:

1. **A pinned commit** — `git show <COMMIT>:<path>`. The strongest, because the
   path is only a locator. `t1_audit.py`'s `PRENOTCH_COMMIT` and
   `t1_placement_gates.py`'s `PREREDO_COMMIT` do this, and they are immune to
   anything happening in the working tree.
2. **A sealed release** — `07_releases/<rel>/source/…`. Immutable by canon, so a
   verdict derived from it is reproducible (canon M-SHIP).
3. **A live `projects/<board>/04_kicad/…`** — legal only where the assertion
   tolerates the board being regenerated, or where a live read is the POINT
   (catching a regression the moment someone revises that board). Say which in
   a comment.

**Never assert PASS/FAIL content about a live `04_kicad/` board you do not own.**
`04_kicad/` is regenerated from source, and mid-rebuild it is track-free with
netclasses clobbered — exactly what canon R1 warns about, and it was observed as
a test failure on 2026-07-29: `t1_gate_contract.py`'s G-VACUOUS-DRU fixture went
red because cooksense's live `.kicad_dru` did not yet carry the barrier rules
(`apply_drc_policy.py` re-applies them AFTER `generate_rules`) and `KEYPAD_ISO`
was absent from `.kicad_pro`, where netclasses actually live — 0 occurrences live
against 15 in the seal. A gate whose verdict depends on whether a sibling happens
to be rebuilding is not a gate.

**THE TRIGGER FIRED — THIRD INSTANCE, 2026-07-30.** `t1_escape_tier`'s
`t_land_honours_a_scoped_clearance` read the LIVE pluto-rx2-8way board and
asserted five RF launches still fail. True when written; false hours later, when
canon R-SCOPE landed `scoped_clr_rf_*` on that very board and REPAIRED them. The
fixture failed for being right about a board that had moved. Fixed by building
the baseline through `board_copy(drop_rules=...)` — strip the relaxation, prove
the five come back, add it, prove they clear. **That is strictly stronger than
the original**: it is a round trip on real bytes, and what is under test is the
gate's response to the RULE rather than the board's current state.

So the three instances are `t1_fleet_regrade` (a dossier deletion),
`t1_gate_contract` (a mid-rebuild board) and this one (a board that got FIXED) —
and note the third is the one no rule would have predicted: the others broke on
transient states, this one broke on a permanent improvement.

**A CHECKER IS NOW EARNED AND IS STILL NOT BUILT, DELIBERATELY.** All three were
caught by the suite itself within one run of the change that caused them, which
is the outcome a checker would buy — and the repo carries 34 gates and 73+
check-IDs against a standing argument to consolidate. What the pattern actually
teaches is cheaper than a gate and is now the rule above: **a fixture asserting a
defect must CONSTRUCT the defect, never assume a live board still has it.**
Reach for `drop_rules=` / a pinned commit / a sealed release before reaching for
`projects/<board>/04_kicad`. If a FOURTH instance appears that the suite does not
catch in the same run, build the checker then.

**The earlier population count stands.** It was three files and seven
references, measured 2026-07-29, and five of the seven were already correct. A new gate for a seven-item set is the gate sprawl this repo is
starting to pay for: 73 check-IDs across 32 gates, each of which is maintenance
and each of which can itself go vacuous (see G-VACUOUS). The durable asset is the
meta-principles, not another ID. If this class recurs — a third fixture breaking
on mutable project state — that is the evidence that earns a checker, and the
count above is the baseline to compare against.

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

---

## 2026-07-28 gate batch — what each new fixture pins

Not every suite has a row above; these landed in this batch and are recorded
here so the coverage is legible.

* **`t1_rotation_authority`** — `jlc_rotation_measure` reads the pin-1 mark in
  the footprint-LOCAL frame. `our_pads()` used `GetFPRelativePosition()`
  (local) while `our_marks()` used `GetStart() - fp.GetPosition()` (BOARD), so
  the PIN-1-MARK channel ran exactly `board_rot` degrees out of step. ONE PART
  placed at 0/90/180/270 must give ONE answer with an identical distance
  multiset — turning a part on the board cannot change which angle of JLC's
  model matches our land. Known-bad: a model marking pin 1 at the WRONG END
  must raise **PIN-1 DISSENT**, withhold the row and exit nonzero, with an
  inline adjacent-property re-verify that the corrected fixture still passes.
* **`t1_electrical_invariants`** — E-ADR skips a `status: superseded` ADR
  (pluto-cal-switch 12 protection ADRs -> 10, FAIL 11/12 -> PASS 10/10), and
  the known-bad proves the skip reads the STATUS and not the presence of the
  word: `accepted`, the template's own
  `accepted # ... | superseded-by-0012` placeholder (on 10 live ADRs), and
  `proposed` must all still FAIL.
* **`t1_bom_source`** — the FH/Fenghua voltage-suffix ceramics
  (`0402CG101J500NT`) decode; a bare digit-run and a four-digit suffix still
  return None; and a standing cross-check runs the decoder against all 146
  vetted ledger rows, whose catalog-verified `value:` fields are an
  INDEPENDENT authority (0 disagreements, with a denominator assertion so the
  check cannot quietly stop covering anything).
* **`t1_power_topology`** — a sub-amp trunk current prints at full precision
  (`.1f` rendered 0.126 A as `0.1 A` and anything under 0.05 A as `0.0 A`),
  the UNDER-BUILT finding cannot quote the SAME number as both quantities, and
  the amp-scale `6.8 A` figure is asserted UNCHANGED so the fix does not
  rewrite every archived report.

**HARNESS INTEGRITY re-measured on this batch** (the commit-`0dd56ab` class,
where the runner could exit 0 while reporting failures): breaking one new
assertion makes `run_tests.sh --only=pin-1` print `1 passed, 1 failed` /
`FAILURES PRESENT` and **exit 1**; restored, exit 0. Measure the runner's own
status, not a pipeline's — `./tests/run_tests.sh | tail` reports `tail`'s exit
code and reads as a false all-clear.

## 2026-07-29 — `t1_schema_reader` (canon G-ORPHAN)

`schema_reader_audit.py` grades the SKILL, not a board: every schema key a
hand-authored source file may declare must name the gate that reads it, and the
named gate must PROVABLY read it (AST read positions, never a grep). 24 tests,
10 known-bad, 1 declared vacuity.

* **The headline known-bad is the R-LEN discrimination.** A reader that carries
  the exact key name as a plain assignment and a message, and reads it nowhere,
  must FAIL with `MENTION` in the finding — and the fixture asserts inline that
  the pre-fix predicate (`re.search(key, source_text)`, which passed
  smc0985-cooksense on two comments about a creepage slot being lengthened)
  CREDITS that same reader. A real red against the wrong algorithm rather than
  against a file that did not exist yesterday.
* **Both halves on one input.** An `ADVISORY` key with a reason PASSES; the
  same key in the same tree with that one contract row deleted FAILS as an
  ORPHAN. Same for the vacuity's contrast: one row moved from `OWED` to a named
  reader that does not read it flips the verdict.
* **Four REAL findings are asserted against real bytes**, each with its
  contrast so the fixture cannot pass vacuously: a policy waiver is applied by
  `id` ALONE (neither `policy_audit.py` nor `waiver_provenance.py` reads
  `refs:`, while both read `id`); `power_topology.py` reaches `linear_rails`
  nowhere while reading its sibling `rails`; `rules_audit.py` reads `current`
  and not `intent`/`routing`/`verify`; and `pins.<N>.tie` is read by none of
  four candidate gates across 43 real dossiers. Each assertion FAILS LOUDLY
  when the finding is closed, naming the contract row to move off `OWED` —
  the ratchet, not a regression.
* **`VACUITY_FLOOR` in `gate_contract_audit.py` rose 5 -> 6 in the same
  commit**, because this gate declares a blind spot (it passes a family whose
  every key is `OWED`). `t_vacuity_floor_is_pinned_to_the_measured_count`
  measures the tree, so the number could not have been left behind.

**HARNESS INTEGRITY re-measured on this suite:** breaking one new assertion
makes `run_tests.sh --only='PROVABLY reads'` print `0 passed, 1 failed` /
`FAILURES PRESENT` and exit 1; restored it prints `1 passed, 0 failed` (and
still exits 1, because that filter selects no known-bad fixture and the runner
refuses to report success on zero — which is the guard working, not a flake).

**This suite has 8 sibling failures in a FRESH WORKTREE and they are not
regressions:** `06_build/` is gitignored, so `t1_electrical_invariants` (6) and
`t1_net_reference` (2) cannot find `projects/smc0985-cooksense/06_build/
netlists/cooksense.net` or the pluto-cal-switch netlists their real-bytes
fixtures require. Full run in this worktree: **861 passed, 8 failed, 512
known-bad**, every failure that one cause.
