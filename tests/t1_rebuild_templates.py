#!/usr/bin/env python3
"""T1: the skill-owned 03_src rebuild driver TEMPLATES.

WHY THIS SUITE EXISTS (2026-07-23): the deterministic promoted-chain rebuild
driver was independently rewritten by THREE boards (usb-hub-3s-v2 and -v3
`rebuild_fast.sh`, crow-recorder-central-v2 `rebuild_reuse.sh`) — a canon M8
two-strike violation. The pattern is now the skill-owned template
`skills/pcb-design/templates/03_src/rebuild_reuse.sh`. These are PROPERTY
assertions on the template text + `bash -n` — never byte-golden, and never an
execution of a real board rebuild (that is the --slow e2e tier's job).

The properties pinned here are each a paid-for incident:
  * generate_rules runs BEFORE import (canon R1) and LAST again after stitch
    (pcbnew saves clobber .kicad_pro netclasses — 2026-07-17, `ae93b4b`).
  * the DRC gate carries --severity-all --refill-zones --schematic-parity on
    ONE invocation (violations are classified at full severity, zones are
    refilled, and parity actually runs).
  * the pinned .kicad_sch is copied beside the board BEFORE the DRC call —
    without it --schematic-parity SILENTLY SKIPS (crow-rv2 finding,
    routing.md M-REPRO entry, 2026-07-23).
  * rebuild_reuse.sh never invokes tsci/tsci-build — `tsci build` is
    non-deterministic (~2900-line UUID/ordering churn in the regenerated
    .kicad_sch, measured on crow-rv2); the committed sch is PINNED canonical.
  * rebuild_all.sh hands the converter the artifact `tsci build` ACTUALLY
    WROTE (M-FRESH, 2026-07-30 — see below).
  * rebuild_all.sh promotes its generated schematic to the pinned reuse path
    only AFTER the schematic checkpoint and both exact reviews pass, but
    BEFORE placement. Otherwise a deliberate placement-review pause leaves
    rebuild_reuse.sh silently replaying the topology from before the TSX edit.

M-FRESH (2026-07-30, pluto-rx2-8way-v2). `tsci build` writes
`03_tscircuit/dist/src/<TSX>/circuit.json`; this template read
`03_tscircuit/build/circuit.json`, a path the builder never writes. The
converter consumed a SUPERSEDED file and TSX-PRE, S-NETMERGE, E-INV, E-ADR,
E-TOPO, E-MARGIN, S-COUNT, E-NETREF and M-BOM all reported green against an
entire obsolete pad-numbering scheme. No checker was wrong — they graded
exactly what they were handed. The path fix alone is worth nothing (the next
mis-wiring is free), so the driver now stamps before the build and VERIFIES
after it, via `skills/kicad-pcb/scripts/build_provenance.py`. The known-bads
below drive that checker directly, because a template-text assertion can only
prove the wiring is right today.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (ROOT, SCRIPTS, KPY, check, contains, main,  # noqa: E402
                     must_fail, must_pass, not_contains, run, test, tmpdir)

TPL_DIR = ROOT / "skills" / "pcb-design" / "templates" / "03_src"
REUSE = TPL_DIR / "rebuild_reuse.sh"
ALL = TPL_DIR / "rebuild_all.sh"
ROUTE = TPL_DIR / "route.yaml"
PROV = SCRIPTS / "build_provenance.py"
DIAG = SCRIPTS / "circuit_json_diagnostics.py"
GEN_TSCIRCUIT = SCRIPTS / "gen_tscircuit.sh"
TSX_TO_BOARD = SCRIPTS / "tsx_to_board.sh"


def drc_gate_ok(txt):
    """True iff a single kicad-cli DRC invocation carries all three flags.
    Continuation-line aware (the templates split the command with '\\')."""
    joined = txt.replace("\\\n", " ")
    for m in re.finditer(r'kicad-cli\s+pcb\s+drc[^\n]*', joined):
        line = m.group(0)
        if all(f in line for f in
               ("--severity-all", "--refill-zones", "--schematic-parity")):
            return True
    return False


def erc_invocations(txt):
    """Every `kicad-cli sch erc` command in the driver, continuation-joined."""
    joined = txt.replace("\\\n", " ")
    return [m.group(0) for m in re.finditer(r'kicad-cli\s+sch\s+erc[^\n]*',
                                            joined)]


def erc_gate_ok(txt):
    """-> (ok, why). The BLOCKING ERC run must gate on ERRORS, not warnings.

    Canon S4 and the kicad-pcb golden rules both make the gate "0 errors,
    warnings baselined with reasons". `--exit-code-violations` is what makes
    kicad-cli return nonzero at all (MEASURED: the same schematic exits 0
    without it and 5 with it), so it marks the BLOCKING run — and paired with
    `--severity-all` it blocks on warnings, which is the defect.

    Three properties, each a separate way to get this wrong:
      * a blocking run EXISTS (an ERC stage that cannot fail is not a gate);
      * NO blocking run carries `--severity-all` (gating on warnings);
      * a full-severity REPORTING run exists (dropping it would trade a false
        gate for a blind one — "baselined" needs a recorded baseline).
    """
    runs = erc_invocations(txt)
    if not runs:
        return False, "the driver runs no `kicad-cli sch erc` at all"
    blocking = [r for r in runs if "--exit-code-violations" in r]
    if not blocking:
        return False, ("no ERC run carries --exit-code-violations, so ERC "
                       "cannot fail this driver at any severity")
    bad = [r for r in blocking if "--severity-all" in r]
    if bad:
        return False, (f"a BLOCKING ERC run gates at --severity-all, i.e. on "
                       f"WARNINGS: {bad[0][:90]!r}")
    if not any("--severity-error" in r for r in blocking):
        return False, ("no blocking ERC run names --severity-error; the "
                       "severity it gates on must be stated, not defaulted")
    if not any("--severity-all" in r and "--exit-code-violations" not in r
               for r in runs):
        return False, ("no full-severity REPORTING run: warnings are supposed "
                       "to be baselined, and a baseline nobody writes down "
                       "cannot be reviewed")
    return True, ""


def early_boundaries_ok(txt):
    required = (
        'electrical_closure.py" .',
        '--stage-result "$PIPELINE_EVIDENCE/E-CLOSURE.stage.json"',
        '--stage-result "$PIPELINE_EVIDENCE/S-PART-FREEZE.stage.json"',
        '--stage-result "$PIPELINE_EVIDENCE/P-FEASIBILITY.stage.json"',
    )
    return all(value in txt for value in required)


@test("TSX-DIAG reports its coverage and FAILS an embedded producer error",
      kind="known_bad")
def t_kb_tsx_diag_embedded_error_is_loud():
    d = tmpdir("tsx-diag-")
    artifact = d / "circuit.json"
    artifact.write_text(json.dumps([
        {"type": "source_component"},
        {"type": "pcb_port_clearance_error", "message": "pads overlap"},
        {"type": "source_part_not_found_warning", "message": "advisory"},
    ]))
    r = must_fail(run([KPY, DIAG, artifact]),
                  "circuit_json_diagnostics.py on an embedded error",
                  expect="TSX-DIAG FAIL")
    contains(r.out, "2 diagnostic record(s) graded / 3 circuit JSON element(s)",
             "TSX-DIAG coverage")


def pre_route_land_gate_ok(txt):
    """P-LAND must run after rules exist and before any route import."""
    board = txt.find("generate_board_generic.py")
    rules = txt.find("generate_rules_generic.py", board + 1)
    land = txt.find('escape_check.py" --board', rules + 1)
    route = min((p for p in (txt.find('route_and_stitch_generic.py" prep'),
                             txt.find('route_and_stitch_generic.py" import'))
                 if p >= 0), default=-1)
    return board >= 0 and rules > board and land > rules and route > land


def audit_board_guard_ok(txt):
    """-> (ok, why). The per-board `03_src/audit_board.py` call is GUARDED by
    a file test AND its absence is ANNOUNCED.

    Two failure modes with opposite signs, which is why both halves are here:
    calling it unconditionally aborts every zero-bespoke-Python board at
    `set -e`; skipping it silently makes a board that LOST its audit script
    indistinguishable from one that never had it (the M-COVER class, arriving
    in a driver instead of a checker).
    """
    call = re.search(r'^[^#\n]*(?:\$PY|python3?)\s+\S*03_src/audit_board\.py',
                     txt, re.M)
    if not call:
        return False, ("the driver never invokes 03_src/audit_board.py — the "
                       "per-board placement gate has no call site")
    blocks = [m for m in re.finditer(
        r'^if\s+\[[^\]]*-f\s+\S*03_src/audit_board\.py[^\]]*\].*?^fi\s*$',
        txt, re.M | re.S)]
    holder = next((m for m in blocks
                   if m.start() < call.start() < m.end()), None)
    if holder is None:
        return False, ("the audit_board.py call is NOT inside an `if [ -f "
                       "... ]` guard — it aborts any board that has no "
                       "per-board audit script (a generic-backend board)")
    if not re.search(r'^\s*else\b', holder.group(0), re.M) or \
            not re.search(r'\becho\b', holder.group(0).split("else", 1)[-1]):
        return False, ("the guard has no `else` that SAYS SO — a silent skip "
                       "makes a board that lost its audit script look like a "
                       "board that passed one")
    return True, ""


def rules_last_after_stitch(txt):
    """True iff the LAST generate_rules_generic call comes after the LAST
    stitch call, and one generate_rules call precedes the import."""
    rules = [m.start() for m in re.finditer(r'generate_rules_generic', txt)]
    stitch = [m.start() for m in re.finditer(r'route_and_stitch_generic\.py"?\s+stitch', txt)]
    imp = [m.start() for m in re.finditer(r'route_and_stitch_generic\.py"?\s+import', txt)]
    if not (rules and stitch and imp):
        return False
    return rules[-1] > stitch[-1] and rules[0] < imp[0]


def ampacity_audits_stage_ordered(txt, has_tsci):
    """Cheap source audit precedes producer spend; full audit grades the
    final generated rules and realized board before route acceptance."""
    source = txt.find('rules_audit.py" . --phase source')
    full = txt.find('rules_audit.py" . --board')
    rules = [m.start() for m in re.finditer(r'generate_rules_generic', txt)]
    acceptance = txt.rfind('route_acceptance_gate.py"')
    if source < 0 or full < 0 or not rules or acceptance < 0:
        return False
    producer_boundary = txt.find("run_stage tscircuit_build") if has_tsci \
        else txt.find("kicad-cli sch export netlist")
    return (producer_boundary >= 0 and source < producer_boundary
            and rules[-1] < full < acceptance)


def via_ampacity_stage_ordered(txt):
    """Full route acceptance composes A-VIA after stitch/final rules."""
    stitch = txt.rfind('route_and_stitch_generic.py" stitch')
    rules = txt.rfind("generate_rules_generic.py")
    audit = txt.rfind('rules_audit.py" . --board')
    acceptance = txt.rfind('route_acceptance_gate.py"')
    window = txt[acceptance:acceptance + 500] if acceptance >= 0 else ""
    return 0 <= stitch < rules < audit < acceptance and "--mode full" in window


def schematic_resume_ok(txt):
    """The resume arm verifies pinned bytes and cannot run the TSX producer."""
    flag = txt.find("--resume-after-schematic-review")
    branch = txt.find('if [ "$RESUME_AFTER_SCHEMATIC_REVIEW" = false ]')
    producer = txt.find("run_stage tscircuit_build", branch)
    record = txt.find('stage_checkpoint.py" record . schematic', producer)
    alternate = txt.find("\nelse\n", record)
    provenance = txt.find('build_provenance.py" audit .', alternate)
    verify = txt.find('stage_checkpoint.py" verify . schematic', provenance)
    close = txt.find("\nfi\n", verify)
    review = txt.find('pre_route_review_check.py" . --phase schematic', close)
    positions = (flag, branch, producer, record, alternate, provenance, verify,
                 close, review)
    if min(positions) < 0 or not (
            flag < branch < producer < record < alternate < provenance < verify
            < close < review):
        return False
    resumed_arm = txt[alternate:close]
    return "tsci build" not in resumed_arm and "tscircuit_build" not in resumed_arm


# ------------------------------------------------------------------ M-FRESH
def _expand(txt):
    """Expand the driver's own top-level `NAME=value` assignments.

    Enough shell to resolve `$CJ`, `$TSX`, `$BOARD` in path arguments; anything
    fancier is out of scope and shows up as an unexpanded `$` (which the
    wiring check treats as UNRESOLVED, never as satisfied).

    THE BARE `$NAME` FORM IS BOUNDARY-ANCHORED, and it has to be: a plain
    `str.replace("$S", ...)` rewrites `$SCHPDF` into
    `"$SKROOT/kicad-pcb/scripts"CHPDF`, because this driver defines both `S=`
    and `SCHPDF=`. Found 2026-07-30 when the render-wiring check below could
    not see a `rm -f "$SCHPDF"` that was plainly there — a shell-expander that
    mangles the path is a checker reading a file nobody wrote."""
    env = dict(re.findall(r'^([A-Z][A-Z0-9_]*)=([^\s#]+)', txt, re.M))
    for _ in range(3):
        for k, v in env.items():
            txt = txt.replace(f'"${k}"', v).replace(f"${{{k}}}", v)
            txt = re.sub(r'\$' + k + r'(?![A-Za-z0-9_])', v.replace('\\', '\\\\'),
                         txt)
    return txt


def circuit_json_wiring(txt):
    """(consumed, produced) — the circuit.json paths this driver FEEDS to
    downstream tools, and the ones it WRITES from the builder's output tree.

    The 2026-07-30 defect is exactly `consumed - produced != {}`: the converter
    was fed `03_tscircuit/build/circuit.json`, which `tsci build` never writes
    and which nothing in the driver copied there."""
    t = _expand(txt)
    consumed = set()
    for tool in (r"circuit_json_to_kicad_sch\.py", r"bom_source_check\.py"):
        for m in re.finditer(tool + r'"?((?:\s+--?\S+)*\s+)(\S*circuit\.json)', t):
            consumed.add(m.group(2).strip('"\''))
    produced = set()
    for m in re.finditer(r'^\s*cp\s+"?(\S*?dist/\S*circuit\.json)"?\s+"?(\S*circuit\.json)"?',
                         t, re.M):
        produced.add(m.group(2).strip('"\''))
    produced |= {c for c in consumed if "dist/" in c}   # reading dist/ directly is fine
    return consumed, produced


def tsx_diagnostic_wiring_ok(txt):
    """TSX-DIAG must grade the copied producer artifact before conversion."""
    t = _expand(txt)
    copied = re.search(
        r'^\s*cp\s+"?\S*dist/\S*circuit\.json"?\s+"?\S*circuit\.json"?',
        t, re.M)
    diagnostic = re.search(
        r'circuit_json_diagnostics\.py"?\s+"?\S*circuit\.json"?', t)
    converter = re.search(r'circuit_json_to_kicad_sch\.py', t)
    return bool(copied and diagnostic and converter and
                copied.start() < diagnostic.start() < converter.start())


#: the template as it stood BEFORE the human schematic was rendered or graded.
#: A pinned commit, so the red side of `t_template_render_wiring` is a real
#: measurement on real bytes and is immune to anything in the working tree
#: (tests/README, "Which real bytes may a fixture read?", oracle 1).
PRE_RENDER_COMMIT = "885ce0e8"


def _render_wiring_ok(txt):
    """Does this driver DELETE the human schematic before regenerating it, and
    hand it to the M-FRESH verify?

    Three ordered facts, because any two of them without the third is the
    defect: (1) `rm -f` on build/schematic.pdf, (2) a render that runs AFTER
    that removal, (3) `--render` on the build_provenance verify, which must run
    after both. Without (1) a failed render leaves the previous revision in
    place and the mtime check grades last week's file; without (3) nothing
    looks at it at all — which is the 2026-07-30 state."""
    # join shell line-continuations first: the verify invocation is wrapped, and
    # a per-line regex would read `--render` as belonging to a different command.
    t = re.sub(r'\\\n\s*', ' ', _expand(txt))
    rm = re.search(r'^\s*rm\s+-f\b[^\n]*schematic\.pdf', t, re.M)
    render = re.search(r'render_schematic_pdf\.mjs[^\n]*schematic', t)
    verify = re.search(r'build_provenance\.py"?\s+verify[^\n]*--render', t)
    if not (rm and render and verify):
        return False
    return rm.start() < render.start() < verify.start()


# ---------------------------------------------------------- clean cases
@test("rebuild_reuse.sh template: bash -n clean, and so is rebuild_all.sh")
def t_syntax():
    for f in (REUSE, ALL):
        r = run(["bash", "-n", f])
        check(r.rc == 0, f"bash -n {f.name} failed:\n{r.out[-1500:]}")


@test("the full driver runs tsci through the bounded heartbeat/timeout runner")
def t_full_build_bounds_tsci():
    txt = ALL.read_text()
    call = re.search(
        r'^\s*run_stage\s+tscircuit_build\s+env\s+--chdir=03_tscircuit\s+'
        r'\./node_modules/\.bin/tsci\s+build\s+"src/\$TSX\.tsx"', txt, re.M)
    check(call is not None,
          "rebuild_all.sh must run tsci build as the tscircuit_build stage")
    direct = re.search(r'^\s*\(\s*cd\s+03_tscircuit\s+&&\s+tsci\s+build',
                       txt, re.M)
    check(direct is None,
          "rebuild_all.sh must not retain an unbounded direct tsci build")


@test("full rebuild rejects orphan schema fields and unproven ADR bounds before TSX")
def t_source_governance_before_producer():
    txt = ALL.read_text()
    schema = txt.find("run_stage source_schema_governance")
    bounds = txt.find("run_stage adr_bound_governance")
    stamp = txt.find('build_provenance.py" stamp')
    producer = txt.find("run_stage tscircuit_build")
    check(min(schema, bounds, stamp, producer) >= 0,
          "full driver omits source-governance or producer boundary")
    check(schema < bounds < stamp < producer,
          "source governance must fail before provenance stamp and TSX spend")
    check("--timeout 30" in txt[bounds:producer],
          "ADR commands have no per-bound hard deadline")


@test("source-governance ordering check rejects a post-TSX schema audit",
      kind="known_bad")
def t_source_governance_ordering_bites():
    txt = ALL.read_text()
    line = next(row for row in txt.splitlines(True)
                if "run_stage source_schema_governance" in row)
    broken = txt.replace(line, "", 1) + "\n" + line
    check(not (broken.find("run_stage source_schema_governance") <
               broken.find("run_stage adr_bound_governance") <
               broken.find('build_provenance.py" stamp') <
               broken.find("run_stage tscircuit_build")),
          "known-bad fixture failed to violate source-governance ordering")


@test("the canonical route template gives TSX both a budget and hard deadline")
def t_route_template_bounds_tsci():
    txt = ROUTE.read_text()
    budget = re.search(
        r"(?ms)^\s{2}budgets_s:\s*$.*?^\s{4}tscircuit_build:\s*([0-9.]+)\s*$",
        txt,
    )
    timeout = re.search(
        r"(?ms)^\s{2}timeouts_s:\s*$.*?^\s{4}tscircuit_build:\s*([0-9.]+)\s*$",
        txt,
    )
    check(budget is not None, "route template omits TSX performance budget")
    check(timeout is not None, "route template omits TSX hard deadline")
    check(float(timeout.group(1)) >= float(budget.group(1)),
          "TSX hard deadline must not be shorter than its normal budget")


@test("both rebuild drivers run the authoritative placement-policy subset "
      "before any route import")
def t_placement_policy_before_route():
    for path in (REUSE, ALL):
        txt = txt0 = path.read_text()
        policy = txt.find("policy_audit.py")
        phase = txt.find("--phase placement", policy)
        route = txt.find("route_and_stitch_generic.py")
        check(policy >= 0 and phase >= 0 and route >= 0 and policy < route,
              f"{path.name} must run policy_audit --phase placement before "
              "route_and_stitch_generic; got policy={policy}, phase={phase}, "
              f"route={route} in {len(txt0)} bytes")


@test("both rebuild drivers run P-PINMAP immediately after generation, before placement or route work")
def t_pin_map_before_route():
    for path in (REUSE, ALL):
        txt = path.read_text()
        gate = txt.find("pin_map_check.py")
        generated = txt.rfind("generate_board_generic.py", 0, gate)
        placement = txt.find("placement/pad invariants", gate)
        route = txt.find("route_and_stitch_generic.py")
        check(gate >= 0 and generated >= 0 and placement >= 0 and route >= 0
              and generated < gate < placement < route,
              f"{path.name} must run P-PINMAP after board generation and "
              "before placement/routing")
        check(txt.count('"$S/pin_map_check.py"') == 1,
              f"{path.name} must have exactly one executable P-PINMAP call")


@test("both rebuild drivers require exact SOUND schematic and placement reviews before route import")
def t_pre_route_reviews_before_route():
    for path in (REUSE, ALL):
        txt = path.read_text()
        schematic = txt.find('pre_route_review_check.py" . --phase schematic')
        placement = txt.find('pre_route_review_check.py" . --phase placement')
        prep = txt.find('route_and_stitch_generic.py" prep')
        route = txt.find('route_and_stitch_generic.py" import')
        check(schematic >= 0 and prep > schematic and placement > prep
              and route > placement,
              f"{path.name}: schematic then placement PR-REVIEW must both "
              "bound a fresh prep before route import")
        check(txt.count('"$S/pre_route_review_check.py"') == 2,
              f"{path.name}: expected exactly two executable PR-REVIEW calls")


@test("both rebuild drivers run exact refill/parity placement DRC before human placement review")
def t_placement_drc_before_review():
    for path in (REUSE, ALL):
        txt = path.read_text()
        board = txt.find("generate_board_generic.py")
        drc = txt.find("kicad-cli pcb drc", board)
        gate = txt.find("placement_drc_check.py", drc)
        review = txt.find('pre_route_review_check.py" . --phase placement', gate)
        check(board >= 0 and drc > board and gate > drc and review > gate,
              f"{path.name}: exact placement DRC must run after board generation "
              "and before placement review")
        window = txt[drc:review]
        for flag in ("--severity-all", "--refill-zones", "--schematic-parity"):
            contains(window, flag, f"{path.name} placement DRC flags")
        contains(window, "06_build/drc/pre_route.json",
                 f"{path.name} placement DRC report")
        check("--allow" not in window,
              f"{path.name}: P-DRC must not expose a generic defect allowlist")


def model_coverage_before_review(txt):
    generated = txt.find("generate_board_generic.py")
    coverage = txt.find('"$S/model_coverage_check.py"', generated)
    review = txt.find('pre_route_review_check.py" . --phase placement',
                      coverage)
    return generated >= 0 and coverage > generated and review > coverage


@test("both rebuild drivers require fitted-body model coverage before modeled placement review")
def t_model_coverage_before_review():
    for path in (REUSE, ALL):
        txt = path.read_text()
        check(model_coverage_before_review(txt),
              f"{path.name}: P-MODEL must independently reopen the generated "
              "board before placement review")
        check(txt.count('"$S/model_coverage_check.py"') == 1,
              f"{path.name}: expected exactly one executable P-MODEL call")


@test("the fitted-body wiring check rejects a driver that drops P-MODEL",
      kind="known_bad")
def t_kb_model_coverage_before_review():
    txt = ALL.read_text()
    mutated = txt.replace('"$S/model_coverage_check.py"',
                          '"$S/model_gate_removed.py"', 1)
    check(mutated != txt, "mutation did not remove the P-MODEL call")
    check(not model_coverage_before_review(mutated),
          "driver without P-MODEL was accepted before modeled review")


@test("rebuild_all.sh resumes the exact reviewed schematic checkpoint without rerunning TSX")
def t_schematic_review_checkpoint_resume():
    txt = ALL.read_text()
    check(schematic_resume_ok(txt),
          "full driver must build+record on the normal arm, audit+verify without "
          "TSX on the resume arm, and only then consume exact human reviews")


@test("the schematic resume ordering check has teeth: removing checkpoint verification is rejected",
      kind="known_bad")
def t_kb_schematic_review_checkpoint_resume():
    txt = ALL.read_text()
    mutated = re.sub(
        r'^\s*\$PY\s+"\$S/stage_checkpoint\.py"\s+verify\s+\.\s+schematic.*?^\s*\|\|.*?\n',
        "", txt, flags=re.M | re.S)
    check(mutated != txt, "mutation did not remove checkpoint verification")
    check(not schematic_resume_ok(mutated),
          "resume ordering check accepted an arm with no checkpoint verification")


@test("rebuild_reuse.sh: ONE DRC invocation carries --severity-all "
      "--refill-zones --schematic-parity")
def t_drc_flags():
    check(drc_gate_ok(REUSE.read_text()),
          "no single kicad-cli pcb drc line carries all three gate flags")


@test("rebuild_reuse.sh: generate_rules before import (R1) AND last after "
      "stitch (netclass clobber)")
def t_rules_ordering():
    check(rules_last_after_stitch(REUSE.read_text()),
          "generate_rules ordering violated: need one call before import and "
          "the final call after stitch")


@test("both rebuild drivers run cheap and full ampacity/rules audits at the "
      "stage boundaries")
def t_ampacity_audits_stage_ordered():
    for path, has_tsci in ((ALL, True), (REUSE, False)):
        check(ampacity_audits_stage_ordered(path.read_text(), has_tsci),
              f"{path.name}: source A-AMP must precede producer work and full "
              "A-AMP/A-FIRE must follow final generate_rules before route acceptance")


@test("the ampacity wiring check rejects a driver that drops full A-AMP",
      kind="known_bad")
def t_kb_ampacity_audit_missing():
    txt = REUSE.read_text()
    bad = re.sub(
        r'^\$PY "\$S/rules_audit\.py" \. --board.*\n'
        r'^\s*\|\| \{ echo "GATE FAILED \[7a\].*\n',
        '', txt, flags=re.M)
    check(bad != txt, "fixture failed to remove full rules audit")
    check(not ampacity_audits_stage_ordered(bad, False),
          "driver without full A-AMP was accepted")


@test("both rebuild drivers compose series-transition via ampacity after final "
      "board construction inside full route acceptance")
def t_via_ampacity_stage_ordered():
    for path in (ALL, REUSE):
        check(via_ampacity_stage_ordered(path.read_text()),
              f"{path.name}: full route acceptance must follow stitch/final "
              "rules and include A-VIA")


@test("the A-VIA wiring check rejects a driver with the gate removed",
      kind="known_bad")
def t_kb_via_ampacity_missing():
    txt = REUSE.read_text()
    bad = txt.replace('route_acceptance_gate.py"',
                      'route_acceptance_gate_REMOVED.py"', 1)
    check(bad != txt, "fixture failed to remove full route acceptance")
    check(not via_ampacity_stage_ordered(bad),
          "driver without the A-VIA compositor was accepted")


@test("rebuild_reuse.sh: pinned .kicad_sch is copied beside the board BEFORE "
      "the DRC gate (else --schematic-parity silently skips)")
def t_sch_beside_board():
    txt = REUSE.read_text()
    cp = re.search(r'^\s*cp\s+"?\$SCH"?\s+"04_kicad/\$BOARD\.kicad_sch"', txt, re.M)
    drc = re.search(r'^\s*kicad-cli pcb drc', txt, re.M)   # the invocation, not the header comment
    check(cp and drc and cp.start() < drc.start(),
          "the pinned sch copy is missing or comes after the DRC invocation")


@test("rebuild_reuse.sh: never invokes tsci (the non-deterministic stage is "
      "skipped; the committed .kicad_sch is pinned canonical)")
def t_no_tsci():
    txt = REUSE.read_text()
    check(not re.search(r'^\s*[^#\n]*\btsci\b', txt, re.M),
          "rebuild_reuse.sh invokes tsci — that stage is non-deterministic "
          "and belongs to rebuild_all.sh only")
    contains(txt, "PINNED", "header (must document the pinned-sch fact)")
    contains(txt, "rebuild_all.sh", "header (must say when to use which driver)")


@test("rebuild_all.sh: the reviewed schematic is promoted before placement "
      "and the final stage only verifies that pin")
def t_all_promotes_pinned_schematic_at_stage_boundary():
    txt = ALL.read_text()
    review = re.search(
        r'^\s*\$PY\s+"\$S/pre_route_review_check\.py"\s+\.\s+--phase\s+schematic',
        txt, re.M)
    board = re.search(r'^\s*\$PY\s+"\$S/generate_board_generic\.py"',
                      txt, re.M)
    drc = re.search(r'^\s*(?:run_stage\s+layout_drc\s+)?kicad-cli pcb drc',
                    txt, re.M)
    copies = list(re.finditer(
        r'^\s*cp\s+"04_kicad/\$BOARD\.kicad_sch"\s+'
        r'"03_tscircuit/kicad/\$BOARD\.kicad_sch"', txt, re.M))
    verifies = list(re.finditer(
        r'^\s*cmp\s+-s\s+"04_kicad/\$BOARD\.kicad_sch"\s+'
        r'"03_tscircuit/kicad/\$BOARD\.kicad_sch"', txt, re.M))
    check(review and board and drc and len(copies) == 1 and len(verifies) == 2,
          "expected one review-gated promotion and two pin verifications")
    cp = copies[0]
    check(review.start() < cp.start() < board.start() < drc.start(),
          "the schematic pin must occur after schematic review and before "
          "board generation/DRC so staged deterministic iteration is current")
    check(verifies[0].start() > cp.start() and verifies[-1].start() > drc.start(),
          "promotion must be checked immediately and again after PCB stages")


@test("rebuild_reuse.sh: board name is DERIVED from floorplan.yaml project.name "
      "(no hand-edited BOARD= constant)")
def t_board_derived():
    txt = REUSE.read_text()
    check(re.search(r'^BOARD=\$\(', txt, re.M),
          "BOARD is not derived from config")
    contains(txt, "project", "derivation (must read the project block)")
    check(not re.search(r'^BOARD=[A-Za-z0-9_]+\s*$', txt, re.M),
          "template carries a hardcoded BOARD= constant")


# ------------------------------------------------------- known-bad cases
@test("the ordering assertion has TEETH: rules-before-stitch is rejected",
      kind="known_bad")
def t_kb_ordering_teeth():
    """Prove rules_last_after_stitch is not a rubber stamp: feed it the
    template with the final generate_rules call moved BEFORE stitch (the
    exact 2026-07-17 netclass-clobber shape) and it must reject."""
    txt = REUSE.read_text()
    lines = txt.splitlines(keepends=True)
    rules_idx = [i for i, l in enumerate(lines)
                 if "generate_rules_generic" in l and not l.lstrip().startswith("#")]
    stitch_idx = [i for i, l in enumerate(lines)
                  if re.search(r'route_and_stitch_generic\.py"?\s+stitch', l)]
    check(rules_idx and stitch_idx, "template lost its rules/stitch steps")
    bad = lines[:]
    rules_line = bad.pop(rules_idx[-1])
    bad.insert(stitch_idx[0] - 1, rules_line)   # final rules call now precedes stitch
    mutated = "".join(bad)
    check(mutated != txt, "mutation did not change the template")
    check(not rules_last_after_stitch(mutated),
          "the ordering check ACCEPTED generate_rules before stitch — it is blind")


@test("the DRC-flag assertion has TEETH: a dropped --schematic-parity is "
      "rejected", kind="known_bad")
def t_kb_drc_flag_teeth():
    """--schematic-parity was SILENTLY missing from two boards' fast drivers
    until crow-rv2's rewrite noticed it never ran. The check must reject a
    gate line without it."""
    txt = REUSE.read_text()
    mutated = txt.replace("--schematic-parity", "")
    check(mutated != txt, "mutation did not change the template")
    check(not drc_gate_ok(mutated),
          "the DRC-flag check ACCEPTED a gate without --schematic-parity")


# ============================================================ M-FRESH: wiring
@test("rebuild_all.sh: every circuit.json the driver GRADES is one the builder "
      "WROTE (the 2026-07-30 silent-staleness defect)")
def t_converter_reads_what_the_builder_wrote():
    consumed, produced = circuit_json_wiring(ALL.read_text())
    check(consumed, "the driver feeds no circuit.json to any tool at all — "
                    "the wiring check has lost its subject")
    orphans = sorted(consumed - produced)
    check(not orphans,
          f"the driver grades {orphans}, which nothing in it writes from "
          f"03_tscircuit/dist/. `tsci build` writes dist/src/<TSX>/circuit.json "
          f"and NOTHING ELSE; a path it never writes holds whatever an earlier "
          f"run left there, and every gate below then reports green on "
          f"superseded content.")


@test("the wiring assertion has TEETH: the PRE-FIX template (converter fed "
      "build/circuit.json with no copy) is rejected", kind="known_bad")
def t_kb_wiring_teeth():
    """RED-VERIFIED against the pre-fix template, reconstructed here rather
    than described: delete the `cp dist/... $CJ` line — which is byte-for-byte
    what `skills/pcb-design/templates/03_src/rebuild_all.sh` looked like on
    2026-07-30 — and `t_converter_reads_what_the_builder_wrote` must reject it.

    MEASURED, not asserted, and RE-MEASURED 2026-07-30 at 221687ef. The real
    pre-fix file was swapped back in
    (`git show e50be3f:skills/pcb-design/templates/03_src/rebuild_all.sh`) and
    this suite rerun — **17 passed, 3 FAILED** — and `circuit_json_wiring` on
    those bytes returned:

        consumed = ['03_tscircuit/build/circuit.json']
        produced = []            -> orphans = ['03_tscircuit/build/circuit.json']

    versus produced == consumed (0 orphans) on the fixed template. The three
    reds were this test, the clean wiring test above, and the M-FRESH ordering
    test. THIS one goes red for the right reason: on a template with no `cp`
    from dist/ there is nothing to delete, so the mutation is a no-op and the
    `mutated != txt` guard fires. Restored after."""
    txt = ALL.read_text()
    mutated = re.sub(r'^\s*cp\s+"?\S*dist/\S*circuit\.json"?[^\n]*\n', "",
                     txt, flags=re.M)
    check(mutated != txt, "mutation did not change the template — the copy "
                          "from dist/ is gone already")
    consumed, produced = circuit_json_wiring(mutated)
    check(consumed - produced,
          "the wiring check ACCEPTED a driver that grades a circuit.json its "
          "builder never wrote — it is blind to the exact defect it exists for")


@test("rebuild_all.sh: TSX-DIAG grades the fresh circuit.json before the "
      "converter can certify it")
def t_tsx_diagnostic_boundary():
    check(tsx_diagnostic_wiring_ok(ALL.read_text()),
          "circuit_json_diagnostics.py must run after the dist/ producer copy "
          "and before circuit_json_to_kicad_sch.py")


@test("rebuild_all.sh: installs the committed Bun graph before tsci build")
def t_locked_tscircuit_install():
    txt = ALL.read_text()
    install = re.search(
        r'run_stage\s+tscircuit_deps\s+env\s+--chdir=03_tscircuit\s+'
        r'bun\s+install\s+--frozen-lockfile\s+--ignore-scripts', txt)
    build = re.search(
        r'run_stage\s+tscircuit_build\s+env\s+--chdir=03_tscircuit\s+'
        r'\./node_modules/\.bin/tsci\s+build', txt)
    check(install and build and install.start() < build.start(),
          "the driver must restore the committed dependency graph with a "
          "frozen, lifecycle-script-free install before invoking tsci")


@test("the locked-install assertion has TEETH: an ambient tsci build is rejected",
      kind="known_bad")
def t_kb_locked_tscircuit_install_teeth():
    txt = ALL.read_text()
    mutated = re.sub(r'^run_stage\s+tscircuit_deps[^\n]*\n', "", txt,
                     count=1, flags=re.M)
    check(mutated != txt, "mutation did not remove the dependency install")
    install = re.search(r'bun\s+install\s+--frozen-lockfile', mutated)
    build = re.search(r'run_stage\s+tscircuit_build', mutated)
    check(not (install and build and install.start() < build.start()),
          "a driver that invokes tsci from ambient dependency state was accepted")


@test("the local-producer assertion has TEETH: a global tsci invocation is rejected",
      kind="known_bad")
def t_kb_local_tscircuit_binary_teeth():
    txt = ALL.read_text()
    mutated = txt.replace("./node_modules/.bin/tsci build", "tsci build", 1)
    check(mutated != txt, "mutation did not replace the project-local producer")
    local = re.search(
        r'run_stage\s+tscircuit_build.*?\./node_modules/\.bin/tsci\s+build',
        mutated)
    check(not local,
          "a driver that restored a local graph but invoked global tsci was accepted")


@test("all shared TSX entry points restore the lock and invoke its local producer")
def t_shared_tscircuit_entry_points_are_local():
    for path in (GEN_TSCIRCUIT, TSX_TO_BOARD):
        txt = path.read_text()
        contains(txt, "bun install --frozen-lockfile --ignore-scripts",
                 f"{path.name} frozen install")
        contains(txt, "./node_modules/.bin/tsci",
                 f"{path.name} project-local producer")
        check("TSCI=tsci" not in txt,
              f"{path.name} retains an ambient producer fallback")
        contains(txt, "bun.lock is required; refusing ambient tsci",
                 f"{path.name} fail-closed missing-lock message")
        check(not re.search(r'timeout\s+\d+\s+tsci\s+build', txt),
              f"{path.name} retains a direct global tsci build")


@test("the shared-entry assertion has TEETH: restoring a lock but using global "
      "tsci is rejected", kind="known_bad")
def t_kb_shared_tscircuit_entry_points_are_local_teeth():
    txt = GEN_TSCIRCUIT.read_text().replace(
        'TSCI=./node_modules/.bin/tsci', 'TSCI=tsci', 1)
    check("bun install --frozen-lockfile --ignore-scripts" in txt,
          "mutation accidentally removed the frozen install")
    check("TSCI=./node_modules/.bin/tsci" not in txt,
          "mutation did not remove the local producer binding")


@test("the TSX-DIAG wiring assertion has TEETH: removing the checker is "
      "rejected", kind="known_bad")
def t_kb_tsx_diagnostic_boundary_teeth():
    txt = ALL.read_text()
    mutated = re.sub(
        r'^\$PY\s+"\$S/circuit_json_diagnostics\.py".*?^\s*\|\|.*?\n',
        "", txt, flags=re.M | re.S)
    check(mutated != txt, "mutation did not remove the TSX-DIAG invocation")
    check(not tsx_diagnostic_wiring_ok(mutated),
          "TSX-DIAG wiring check accepted a build with no producer-diagnostic gate")


# ================================================ the ERC gate + the [4] guard
@test("rebuild_all.sh: the BLOCKING ERC run gates on ERRORS, and the "
      "full-severity baseline is still recorded")
def t_erc_gates_on_errors():
    """Canon S4 says "0 errors, warnings baselined with reasons" and this
    TEMPLATE said `--severity-all --exit-code-violations`, which blocks on
    warnings. The template contradicted the canon it implements.

    MEASURED 2026-07-30, pluto-rx2-8way-v2's real `04_kicad/
    pluto_rx2_8way_v2.kicad_sch`, by running kicad-cli directly:

        --severity-all   --exit-code-violations -> EXIT 5, 220 findings
                                                   (131 endpoint_off_grid,
                                                     89 lib_symbol_issues)
        --severity-error --exit-code-violations -> EXIT 0, 0 findings
        --severity-all   (no exit flag)         -> EXIT 0   [safe under set -e]

    Both warning classes are tscircuit->KiCad converter geometry/symbol
    artifacts; neither is electrical. A driver that cannot reach its own DRC
    stage on 220 cosmetics gets edited per-board, and the per-board edit is how
    the ERC gate becomes whatever each board could make pass."""
    ok, why = erc_gate_ok(ALL.read_text())
    check(ok, f"rebuild_all.sh ERC gate: {why}")


@test("the ERC-gate check has TEETH: the PRE-FIX template (one "
      "`--severity-all --exit-code-violations` run) is rejected",
      kind="known_bad")
def t_kb_erc_gate_teeth():
    """RED-VERIFIED by RECONSTRUCTING the pre-fix line inline rather than
    describing it, so the red side is re-measured on every run.

    The reconstruction is byte-equivalent to what
    `git show 982858d8:skills/pcb-design/templates/03_src/rebuild_all.sh`
    carries. GIT-SWAP RED-VERIFIED 2026-07-30: the real pre-fix template
    restored over the fixed one, this suite measured **20 passed / 4 FAILED** —
    this fixture, `t_erc_gates_on_errors`, and the two `[4]`-guard fixtures,
    and NOTHING ELSE, so each pair isolates its own defect. `erc_gate_ok` on
    those bytes returned `a BLOCKING ERC run gates at --severity-all, i.e. on
    WARNINGS`. Restored: **24 / 0**.

    THE THIRD PROPERTY IS ASSERTED SEPARATELY because the obvious wrong fix
    passes the first two: simply DELETING the `--severity-all` reporting run
    leaves a gate that is correct and a baseline nobody can review."""
    pre = ('kicad-cli sch erc --severity-all --exit-code-violations '
           '"04_kicad/$BOARD.kicad_sch" \\\n    -o 06_build/erc.rpt '
           '|| { echo "ERC FAILED"; exit 1; }\n')
    ok, why = erc_gate_ok(pre)
    check(not ok, "the ERC-gate check ACCEPTED the pre-fix line that gates on "
                  "220 cosmetic warnings")
    contains(why, "WARNINGS", "the finding must name what it is gating on")

    # an ERC stage that cannot fail at all is equally refused (the opposite
    # over-correction: drop the exit flag and the gate quietly stops gating).
    ok2, why2 = erc_gate_ok('kicad-cli sch erc --severity-error "$S" -o r\n')
    check(not ok2, "a non-blocking ERC stage was accepted as a gate")

    # and dropping the recorded baseline is refused too.
    ok3, _ = erc_gate_ok('kicad-cli sch erc --severity-error '
                         '--exit-code-violations "$S" -o r\n')
    check(not ok3, "an ERC gate with NO full-severity report was accepted — "
                   "'warnings are baselined' with no baseline written down")

    # ADJACENT PROPERTY, re-measured every run: the SHIPPED template, which
    # differs from `pre` in exactly this respect, passes all three.
    ok4, why4 = erc_gate_ok(ALL.read_text())
    check(ok4, f"the shipped template no longer satisfies its own gate: {why4}")


@test("rebuild_all.sh: the per-board audit_board.py call is GUARDED, and its "
      "absence is ANNOUNCED rather than skipped in silence")
def t_audit_board_guarded():
    """A ZERO-BESPOKE-PYTHON board (repo ADR-0002 — the go-forward default)
    has no `03_src/audit_board.py` at all: placement comes from floorplan.yaml
    and every invariant the script would have hand-checked is a SHARED gate
    running beside this line. The template called it unconditionally, so under
    `set -euo pipefail` it aborted every such board — measured on
    pluto-rx2-8way-v2, 2026-07-30."""
    ok, why = audit_board_guard_ok(ALL.read_text())
    check(ok, f"rebuild_all.sh [4]: {why}")


@test("both rebuild drivers run P-LAND after rules and before route import")
def t_pre_route_land_gate():
    for path in (ALL, REUSE):
        check(pre_route_land_gate_ok(path.read_text()),
              f"{path.name}: P-LAND must follow generated rules and precede route import")


@test("the pre-route P-LAND ordering check rejects a seal-only/absent gate",
      kind="known_bad")
def t_kb_pre_route_land_gate():
    text = ALL.read_text().replace(
        '$PY "$S/escape_check.py" --board "04_kicad/$BOARD.kicad_pcb" \\\n'
        '    || { echo "GATE FAILED [5a] P-LAND: a placed pad cannot launch its declared width"; exit 1; }\n',
        "")
    check(not pre_route_land_gate_ok(text),
          "a driver with no pre-route pad-launch gate was accepted")


@test("the [4] guard check has TEETH in BOTH directions: the unconditional "
      "PRE-FIX call is rejected, and so is a SILENT skip", kind="known_bad")
def t_kb_audit_board_guard_teeth():
    """The two failure modes have opposite signs and the same cause — nobody
    decided what "this board has no audit_board.py" means.

    RED-VERIFIED by reconstruction, re-measured every run. `$PY
    03_src/audit_board.py` on its own line is verbatim what
    `git show 982858d8:...rebuild_all.sh` carries; GIT-SWAP RED-VERIFIED
    2026-07-30 alongside the ERC pair — the real pre-fix template made this
    fixture and `t_audit_board_guarded` red too, **20 passed / 4 FAILED** with
    both pre-fix defects restored and **24 / 0** with both fixed.

    The SILENT half matters more than it looks: `if [ -f x ]; then run; fi`
    with no `else` fixes the abort and introduces the M-COVER defect — a board
    that LOST its audit script becomes indistinguishable from one that never
    had one, and reads as having passed a gate that never ran."""
    ok, why = audit_board_guard_ok("$PY 03_src/audit_board.py\n")
    check(not ok, "the guard check ACCEPTED the unconditional pre-fix call")
    contains(why, "aborts", "the finding must name the consequence")

    silent = ("if [ -f 03_src/audit_board.py ]; then\n"
              "    $PY 03_src/audit_board.py\n"
              "fi\n")
    ok2, why2 = audit_board_guard_ok(silent)
    check(not ok2, "a guard that skips the per-board gate SILENTLY was "
                   "accepted — a board that lost its audit script would read "
                   "as one that passed it")
    contains(why2, "silent skip", "the finding must name the silent skip")

    # a driver with no call site at all is a FAIL, never a pass-by-absence.
    ok3, _ = audit_board_guard_ok("echo hello\n")
    check(not ok3, "a driver that never calls audit_board.py was accepted")

    # ADJACENT PROPERTY: the shipped template differs from `silent` in exactly
    # the `else` and passes.
    ok4, why4 = audit_board_guard_ok(ALL.read_text())
    check(ok4, f"the shipped template no longer satisfies its own guard: {why4}")


@test("rebuild_all.sh: M-FRESH stamps BEFORE the build and verifies AFTER it, "
      "before the first gate can report green")
def t_mfresh_ordering():
    t = ALL.read_text()
    stamp = re.search(r'build_provenance\.py"?\s+stamp', t)
    build = re.search(
        r'^\s*(?:\(\s*cd 03_tscircuit && tsci build|'
        r'run_stage\s+tscircuit_build\s+env\s+--chdir=03_tscircuit\s+'
        r'(?:\./node_modules/\.bin/)?tsci\s+build)', t, re.M)
    verify = re.search(r'build_provenance\.py"?\s+verify', t)
    conv = re.search(r'circuit_json_to_kicad_sch\.py', t)
    check(stamp and build and verify and conv,
          "the driver is missing one of stamp / tsci build / verify / converter")
    check(stamp.start() < build.start(),
          "M-FRESH stamp must run BEFORE the build — a witness written by the "
          "build is not a witness (canon M1), and the knob check has to fire "
          "before anything is produced")
    check(build.start() < verify.start() < conv.start(),
          "M-FRESH verify must sit between the build and the converter: after "
          "it there is an artifact to compare, and before it no gate has yet "
          "graded anything")


# ==================================================== M-FRESH: the checker
def _scratch(name="pluto_x", board=None, tsx=None):
    """A minimal project tree the checker can grade without bun/tsci/kicad."""
    d = tmpdir("mfresh_")
    (d / "03_src").mkdir(parents=True)
    (d / "03_tscircuit" / "src").mkdir(parents=True)
    (d / "03_tscircuit" / "src" / f"{name}.tsx").write_text("export default 1\n")
    (d / "03_tscircuit" / "package.json").write_text('{"name":"scratch"}\n')
    (d / "03_tscircuit" / "bun.lock").write_text('lockfileVersion = 1\n')
    (d / "04_kicad").mkdir()
    (d / "06_build").mkdir()
    # an ADOPTED driver: it calls the checker, so its runs leave evidence and
    # `audit` grades it rather than filing it under OWED.
    (d / "03_src" / "rebuild_all.sh").write_text(
        f"#!/bin/bash\nBOARD={board or name}\nTSX={tsx or name}\n"
        f'$PY "$S/build_provenance.py" stamp . --board "$BOARD" --tsx "$TSX"\n')
    return d


def _produce(d, name, payload):
    """Stand in for `tsci build`: write dist/src/<name>/circuit.json."""
    p = d / "03_tscircuit" / "dist" / "src" / name / "circuit.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload))
    return p


def _stamp(d, name):
    return run([KPY, PROV, "stamp", d, "--board", name, "--tsx", name])


def _verify(d, name, artifact):
    return run([KPY, PROV, "verify", d, "--board", name, "--tsx", name,
                "--artifact", artifact])


@test("M-FRESH passes when the converter input IS the builder's output")
def t_mfresh_clean():
    d = _scratch()
    must_pass(_stamp(d, "pluto_x"), "M-FRESH stamp on a well-formed project")
    time.sleep(0.01)
    src = _produce(d, "pluto_x", {"pads": "vendor-order"})
    dst = d / "03_tscircuit" / "build" / "circuit.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(src.read_bytes())
    r = must_pass(_verify(d, "pluto_x", dst), "M-FRESH verify on a copied build")
    contains(r.out, "M-FRESH PASS", "verify output")
    contains(r.out, "byte-identical", "verify output")


@test("M-FRESH FAILS on the pluto-rx2-8way-v2 incident: the converter input is "
      "a SUPERSEDED file the builder never wrote", kind="known_bad")
def t_kb_mfresh_the_incident():
    """THE ACCEPTANCE FIXTURE. This reconstructs 2026-07-30 exactly:
    `build/circuit.json` holds an obsolete pad-numbering scheme from an earlier
    run, `tsci build` writes the corrected one to `dist/src/<TSX>/`, and the
    converter is handed `build/`.

    RED-VERIFIED by mutation, MEASURED 2026-07-30 at 221687ef: with the
    content comparison in `cmd_verify` disabled (`if a != b:` -> `if False:`)
    the suite went **18 passed / 2 FAILED** — this test and the touch test
    below, and nothing else. Restored after.

    Before `build_provenance.py` existed there was no command to run here at
    all, and the pipeline that DID run on these exact semantics reported
    TSX-PRE, S-NETMERGE, E-INV, E-ADR, E-TOPO, E-MARGIN, S-COUNT, E-NETREF and
    M-BOM all green. The last assertion below pins why: the stale bytes are
    perfectly well-formed circuit-json, so every downstream checker parses and
    passes them. Freshness is not a property any of them can see, which is why
    it needed its own gate rather than a fix inside one."""
    d = _scratch()
    stale = d / "03_tscircuit" / "build" / "circuit.json"
    stale.parent.mkdir(parents=True, exist_ok=True)
    stale.write_text(json.dumps({"pads": "invented-order"}))     # the superseded scheme
    must_pass(_stamp(d, "pluto_x"), "M-FRESH stamp")
    time.sleep(0.01)
    _produce(d, "pluto_x", {"pads": "vendor-order"})             # what the build made
    r = must_fail(_verify(d, "pluto_x", stale),
                  "M-FRESH verify on a stale converter input", expect="F-PATH")
    contains(r.out, "this build did not produce", "verify output")
    # the contrast that makes the finding non-trivial: the stale file is VALID.
    # A parser-shaped checker sees nothing wrong with it — which is precisely
    # why nine of them passed.
    json.loads(stale.read_text())


@test("M-FRESH is NOT defeatable by touching the stale file", kind="known_bad")
def t_kb_mfresh_touch_cannot_forge():
    """A rerun that 'happens to touch the file' is the obvious way an mtime-only
    freshness check gets defeated, and it is the failure mode this repo would
    have shipped if the assertion were `is build/ newer than dist/`. The
    equality is CONTENT-based and CROSS-FILE, so the newest mtime in the tree
    buys nothing.

    RED-VERIFIED, and this mutation is the one that matters. MEASURED
    2026-07-30 at 221687ef: replacing the hash comparison with the naive mtime
    rule (`if artifact.stat().st_mtime_ns < producer.stat().st_mtime_ns:`)
    leaves the incident test above PASSING — **19 passed / 1 FAILED** — and only
    THIS test goes red. The plausible wrong implementation is caught here and
    nowhere else; without this fixture the gate would look fully tested and
    still be defeated by one `touch`. Restored after."""
    d = _scratch()
    stale = d / "03_tscircuit" / "build" / "circuit.json"
    stale.parent.mkdir(parents=True, exist_ok=True)
    stale.write_text(json.dumps({"pads": "invented-order"}))
    must_pass(_stamp(d, "pluto_x"), "M-FRESH stamp")
    time.sleep(0.01)
    _produce(d, "pluto_x", {"pads": "vendor-order"})
    now = time.time() + 5                       # newest mtime in the whole tree
    os.utime(stale, (now, now))
    must_fail(_verify(d, "pluto_x", stale),
              "M-FRESH verify against a touched stale artifact", expect="F-PATH")


@test("M-FRESH FAILS when the builder wrote nothing at all", kind="known_bad")
def t_kb_mfresh_void():
    """`tsci build` exiting 0 without writing (or being skipped entirely) must
    not be indistinguishable from a build that produced the graded artifact."""
    d = _scratch()
    must_pass(_stamp(d, "pluto_x"), "M-FRESH stamp")
    stale = d / "03_tscircuit" / "build" / "circuit.json"
    stale.parent.mkdir(parents=True, exist_ok=True)
    stale.write_text(json.dumps({"pads": "invented-order"}))
    must_fail(_verify(d, "pluto_x", stale),
              "M-FRESH verify with an empty dist/", expect="F-VOID")


@test("M-FRESH FAILS on the BOARD=power3s shape — a driver never edited for "
      "this board, caught BEFORE the build", kind="known_bad")
def t_kb_mfresh_template_knobs():
    """The second half of the 2026-07-30 finding: pluto-rx2-8way-v2 carried the
    TEMPLATE's own `BOARD=power3s` / `TSX=power3s` from commission (ea6d1fa1)
    through four commits, so the full driver had never run there while its stage
    gates were reporting green one at a time.

    RED-VERIFIED by mutation, MEASURED 2026-07-30 at 221687ef: with the knob
    check neutered in `cmd_stamp` (`fails = grade_knobs(...)` -> `fails = []`)
    the suite went **19 passed / 1 FAILED** — this test alone — and the checker
    happily stamped a run for a board whose .tsx does not exist. Restored
    after.

    It fails at `stamp`, i.e. before `tsci build` — the earliest point at which
    it is knowable, and before anything downstream could go green."""
    d = _scratch(name="pluto_x")
    r = must_fail(run([KPY, PROV, "stamp", d, "--board", "power3s",
                       "--tsx", "power3s"]),
                  "M-FRESH stamp with the template knobs", expect="F-KNOB")
    contains(r.out, "TEMPLATE SENTINEL", "stamp output")
    contains(r.out, "BEFORE the build ran", "stamp output")
    check(not (d / "06_build" / "build_provenance.json").exists(),
          "a refused stamp still wrote a provenance record — a refusal that "
          "leaves evidence of a run is worse than no check")


@test("M-FRESH audit FAILS a board whose driver has never completed a run",
      kind="known_bad")
def t_kb_mfresh_audit_norun():
    """`rm -rf 06_build/` is always legal (06_build is disposable), so 'no
    record' means exactly 'no evidence this board was built' — which is the
    honest verdict, not a pass. This is what distinguishes a board that ran and
    passed from one that never ran."""
    d = _scratch()
    must_fail(run([KPY, PROV, "audit", d]),
              "M-FRESH audit on a never-built board", expect="F-NORUN")


@test("M-FRESH audit FAILS once the sources move past the last verified build "
      "(canon M3)", kind="known_bad")
def t_kb_mfresh_audit_stale_sources():
    """M3 says everything is regenerable from 03_src/ + 03_tscircuit/. That is
    worthless if the regeneration silently no-ops, so a board whose tscircuit
    sources have changed since its last verified build is reported STALE rather
    than assumed current."""
    d = _scratch()
    must_pass(_stamp(d, "pluto_x"), "M-FRESH stamp")
    time.sleep(0.01)
    src = _produce(d, "pluto_x", {"pads": "vendor-order"})
    dst = d / "03_tscircuit" / "build" / "circuit.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(src.read_bytes())
    must_pass(_verify(d, "pluto_x", dst), "M-FRESH verify")
    must_pass(run([KPY, PROV, "audit", d]), "M-FRESH audit right after a build")
    (d / "03_tscircuit" / "src" / "pluto_x.tsx").write_text("export default 2\n")
    must_fail(run([KPY, PROV, "audit", d]),
              "M-FRESH audit after the sources moved", expect="F-STALE")


@test("M-FRESH binds the resolved TSX dependency lock, not only package.json",
      kind="known_bad")
def t_kb_mfresh_audit_stale_lockfile():
    d = _scratch()
    must_pass(_stamp(d, "pluto_x"), "M-FRESH stamp")
    time.sleep(0.01)
    src = _produce(d, "pluto_x", {"pads": "vendor-order"})
    dst = d / "03_tscircuit" / "build" / "circuit.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(src.read_bytes())
    must_pass(_verify(d, "pluto_x", dst), "M-FRESH verify")
    (d / "03_tscircuit" / "bun.lock").write_text(
        'lockfileVersion = 1\n[packages]\n"tscircuit" = "new"\n')
    must_fail(run([KPY, PROV, "audit", d]),
              "M-FRESH audit after dependency graph moved", expect="F-STALE")


@test("M-FRESH audit NAMES what it cannot grade, and an empty denominator "
      "never reads as a pass", kind="known_bad")
def t_kb_mfresh_audit_never_silent():
    """canon M-COVER. Three fleet shapes must stay distinguishable and none may
    land in the pass column: a driver with no knobs at all (UNREACHED — cooksense
    and crow-mic-pod-v2 drive `gen_tscircuit.sh`), a knobbed driver that has not
    adopted the stamp (OWED — it emits no evidence either way, so 'never ran' is
    unknowable there), and an adopted driver with no record (FAIL F-NORUN)."""
    d = _scratch()
    (d / "03_src" / "rebuild_all.sh").write_text("#!/bin/bash\necho hi\n")
    r = run([KPY, PROV, "audit", d])
    contains(r.out, "UNREACHED", "audit output")
    contains(r.out, "NOT a pass", "audit output")
    not_contains(r.out, "M-FRESH PASS", "audit output")

    # knobbed but UNADOPTED: named and counted as OWED, and still not a pass
    (d / "03_src" / "rebuild_all.sh").write_text(
        "#!/bin/bash\nBOARD=pluto_x\nTSX=pluto_x\n")
    r = run([KPY, PROV, "audit", d])
    contains(r.out, "OWED", "audit output")
    not_contains(r.out, "M-FRESH PASS", "audit output")

    # adopted with no record: the honest FAIL
    (d / "03_src" / "rebuild_all.sh").write_text(
        "#!/bin/bash\nBOARD=pluto_x\nTSX=pluto_x\nbuild_provenance.py stamp .\n")
    must_fail(run([KPY, PROV, "audit", d]),
              "M-FRESH audit once the driver stamps but has no record",
              expect="F-NORUN")


@test("M-FRESH audit FAILS an unresolvable BOARD= even on a driver that never "
      "adopted the stamp", kind="known_bad")
def t_kb_mfresh_knob_fails_without_adoption():
    """The adoption ratchet must not become an amnesty. `BOARD=power3s` is a
    defect TODAY — it means the driver was never edited for this board — and it
    is knowable from the tree with no cooperation from the driver at all. So
    F-KNOB is graded on every knobbed board, adopted or not, and it FAILS.

    RED-VERIFIED by mutation, MEASURED 2026-07-30 at 221687ef: neutering the
    OTHER `grade_knobs` call — the one in `audit_project`, which is a SEPARATE
    call site from `cmd_stamp`'s — gives **19 passed / 1 FAILED**, this test
    alone. The two call sites are red-verified independently on purpose:
    collapsing them is exactly how the adoption ratchet would quietly become an
    amnesty. Restored after."""
    d = _scratch(name="pluto_x")
    (d / "04_kicad" / "pluto_x.kicad_pcb").write_text("(kicad_pcb)\n")
    (d / "03_src" / "rebuild_all.sh").write_text(       # UNADOPTED on purpose
        "#!/bin/bash\nBOARD=power3s\nTSX=power3s\n")
    r = must_fail(run([KPY, PROV, "audit", d]),
                  "M-FRESH audit on an unadopted driver with template knobs",
                  expect="F-KNOB")
    contains(r.out, "OWED", "audit output")            # counted as unadopted
    contains(r.out, "BOARD=power3s", "audit output")
    contains(r.out, "TEMPLATE SENTINEL", "audit output")


# ======================================= F-RENDER: the HUMAN schematic (M-FRESH)
# The 07_releases contract names 03_tscircuit/build/schematic.pdf as the release's
# `pdf/schematic.pdf`. It is the one artifact in the archive a human reads, and
# until 2026-07-30 NOTHING graded it: `tsci build` does not write it, the template
# did not write it, so it was whatever the last gen_tscircuit.sh run left behind.
def _render(d, when=None):
    """Write the human schematic, optionally at a chosen mtime."""
    p = d / "03_tscircuit" / "build" / "schematic.pdf"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"%PDF-1.4 human schematic\n")
    if when is not None:
        os.utime(p, ns=(when, when))
    return p


def _verify_r(d, name, artifact, render):
    return run([KPY, PROV, "verify", d, "--board", name, "--tsx", name,
                "--artifact", artifact, "--render", str(render)])


def _built(d, name="pluto_x"):
    """stamp -> build -> copy. Returns (project, converter_input, producer)."""
    must_pass(_stamp(d, name), "M-FRESH stamp")
    time.sleep(0.02)
    src = _produce(d, name, {"pads": "vendor-order"})
    dst = d / "03_tscircuit" / "build" / "circuit.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(src.read_bytes())
    return dst, src


@test("M-FRESH grades the HUMAN schematic too, and says so when it is NOT given "
      "one (canon M-COVER)")
def t_mfresh_render_clean():
    d = _scratch()
    dst, _ = _built(d)
    time.sleep(0.02)
    r = must_pass(_verify_r(d, "pluto_x", dst, _render(d)),
                  "M-FRESH verify with a freshly rendered human schematic")
    contains(r.out, "postdates both the stamp and the producer", "verify output")
    # ...and the ungraded case is PRINTED, never passed silently. Same tree,
    # one flag removed: the verdict is still PASS but it now names what it did
    # not grade, which is the difference between coverage and a clean-looking
    # denominator of zero.
    d2 = _scratch()
    dst2, _ = _built(d2)
    r2 = must_pass(_verify(d2, "pluto_x", dst2), "M-FRESH verify with no --render")
    contains(r2.out, "NOT GRADED", "verify output")
    contains(r2.out, "not a pass", "verify output")


@test("M-FRESH FAILS the pluto-rx2-8way-v2 SCHEMATIC incident: the human "
      "schematic is OLDER than the circuit.json it depicts", kind="known_bad")
def t_kb_mfresh_render_is_the_schematic_incident():
    """THE SECOND ACCEPTANCE FIXTURE, and it is a MEASURED tree, not an invented
    one. pluto-rx2-8way-v2 2026-07-30, `ls --time-style=full-iso
    03_tscircuit/build/`:

        18:42:05.403  circuit.json
        14:47:14.802  schematic.pdf
        14:47:13.824  schematic.svg

    Three hours fifty-five minutes of design revision that the shipped
    schematic does not show — and the release contract copies exactly that PDF
    into `pdf/schematic.pdf`. Every gate was green, because this is the one
    artifact M-FRESH did not cover: F-PATH grades the MACHINE input
    (circuit.json), and the human document had no gate at all.

    The fixture reproduces the ORDERING, which is the whole fact: the render
    predates the producer. It is not a content check — there is nothing to
    compare a PDF to — and that limit is declared in the module's VACUITY block
    and fixtured below.

    RED-VERIFIED BY THREE MUTATIONS, 2026-07-30, each isolating a different
    subset — which is what shows the fixtures grade different facts rather than
    one fact three times. Baseline 25 passed / 0 failed / 11 known-bad.
      M1  neuter BOTH F-RENDER time orderings (`if rmt < ...:` -> `if False:`)
          -> **23 / 2**: THIS test and the vacuity's CONTRAST, nothing else.
      M2  drop `--render` support entirely (`render = None`)
          -> **20 / 5**: all five render fixtures, no collateral.
      M3  neuter only the audit-side `render_sha256` comparison
          -> **24 / 1**: only `t_kb_mfresh_audit_render_rewritten`.
    Restored: 25 / 0 / 11. M3 is the one that matters most — it proves the
    content half and the ordering half are separately load-bearing, so removing
    either leaves a hole the other does not cover."""
    d = _scratch()
    dst, producer = _built(d)
    # the survivor: rendered well before this run's build, exactly as measured
    stale = _render(d, when=producer.stat().st_mtime_ns - 14_090_000_000_000)
    r = must_fail(_verify_r(d, "pluto_x", dst, stale),
                  "M-FRESH verify on a stale human schematic", expect="F-RENDER")
    contains(r.out, "OLDER than the circuit.json this run produced", "verify output")
    contains(r.out, "pdf/schematic.pdf", "verify output")
    # THE CONTRAST that proves the finding is about RECENCY and not about the
    # file: same tree, same bytes, re-rendered after the build -> PASS.
    d2 = _scratch()
    dst2, _ = _built(d2)
    time.sleep(0.02)
    must_pass(_verify_r(d2, "pluto_x", dst2, _render(d2)),
              "the same human schematic re-rendered after the build")


@test("M-FRESH FAILS when the human schematic is ABSENT — the driver deletes it "
      "before rendering, so absence is the loud failure mode", kind="known_bad")
def t_kb_mfresh_render_missing_is_loud():
    """Why the template does `rm -f` FIRST. A render step that fails or is
    skipped (for example, a missing PDF converter) must not be able to leave the
    previous revision's PDF sitting where the seal will copy it. Deleting first
    converts the failure from STALENESS, which is silent and shipped, into
    ABSENCE, which this finding names. A gate that only checked mtime ordering
    would PASS the skipped-render case, because the file it would have graded
    is the one from last time."""
    d = _scratch()
    dst, _ = _built(d)
    r = must_fail(_verify_r(d, "pluto_x", dst,
                            d / "03_tscircuit" / "build" / "schematic.pdf"),
                  "M-FRESH verify with no human schematic at all",
                  expect="F-RENDER")
    contains(r.out, "does not exist", "verify output")


@test("M-FRESH audit FAILS a human schematic REWRITTEN after verification — the "
      "content half, which no timestamp can forge", kind="known_bad")
def t_kb_mfresh_audit_render_rewritten():
    """The build-time half of F-RENDER is a time ordering (see the VACUITY
    block). This is the half that is content-based: `render_sha256` is pinned
    into the provenance record at verify time, so anything that rewrites the
    human schematic OUTSIDE the driver — a hand re-render, a copy from another
    board, a partially-written file — is caught after the fact, and caught at
    `audit`, which is what runs at seal time."""
    d = _scratch()
    dst, _ = _built(d)
    time.sleep(0.02)
    rnd = _render(d)
    must_pass(_verify_r(d, "pluto_x", dst, rnd), "M-FRESH verify")
    rnd.write_bytes(b"%PDF-1.4 SOME OTHER BOARD\n")
    r = must_fail(run([KPY, PROV, "audit", d]),
                  "M-FRESH audit after the human schematic was rewritten",
                  expect="F-RENDER")
    contains(r.out, "rewritten outside the driver", "audit output")


@test("M-FRESH PASSES a human schematic that was merely TOUCHED and never "
      "re-rendered", kind="vacuity", gate="build_provenance.py")
def t_vac_mfresh_a_touched_render_passes():
    """THE DECLARED BLIND SPOT (canon G-VACUOUS), and it is the exact hole
    F-PATH does not have. F-PATH compares sha256 across two independently
    resolved paths, so no timestamp operation can forge it. THE RENDER HAS NO
    SECOND COPY: `build/schematic.pdf` is the only instance of itself, so its
    build-time freshness can only be a TIME ORDERING — and `touch` moves a
    time. Here the PDF still holds the previous revision's bytes and the gate
    says PASS.

    Declared rather than papered over, and bounded by two things that do not
    close it: the DRIVER deletes the render before regenerating (so under the
    template the failure mode is absence, which `t_kb_mfresh_render_missing_
    is_loud` pins), and `audit` compares `render_sha256` (which
    `t_kb_mfresh_audit_render_rewritten` pins). What is left uncovered is a
    `touch` between the build and the verify inside one run.

    THE CONTRAST — subject first, then the same input changed in exactly one
    way — is the un-touched file: identical bytes, true mtime, and the gate
    FAILS. That is what makes this a blind spot rather than a fact the gate
    cannot represent."""
    d = _scratch()
    dst, producer = _built(d)
    stale = _render(d, when=producer.stat().st_mtime_ns - 14_090_000_000_000)
    body = stale.read_bytes()
    after = producer.stat().st_mtime_ns + 1_000_000_000
    os.utime(stale, ns=(after, after))                  # ONE touch, no re-render
    r = must_pass(_verify_r(d, "pluto_x", dst, stale),
                  "M-FRESH verify on a TOUCHED but never re-rendered schematic")
    contains(r.out, "M-FRESH PASS", "verify output")
    check(stale.read_bytes() == body,
          "the fixture must not have re-rendered anything — the bytes are the "
          "previous revision's, which is the whole point")

    # THE CONTRAST: same bytes, same tree, mtime left telling the truth.
    d2 = _scratch()
    dst2, producer2 = _built(d2)
    honest = _render(d2, when=producer2.stat().st_mtime_ns - 14_090_000_000_000)
    honest.write_bytes(body)
    os.utime(honest, ns=(producer2.stat().st_mtime_ns - 14_090_000_000_000,) * 2)
    must_fail(_verify_r(d2, "pluto_x", dst2, honest),
              "the same stale bytes with an honest mtime", expect="F-RENDER")


@test("new early electrical, body-clearance, and critical-route gates are "
      "stage-ordered in both rebuild drivers")
def t_new_stage_gate_ordering():
    for path in (ALL, REUSE):
        txt = path.read_text()
        check(txt.index("early_design_check.py") <
              txt.index("pre_route_review_check.py"),
              f"{path.name}: early electrical decisions must precede reviews")
        placement = txt.index("placement_routability_preflight.py")
        route_import = txt.index("route_and_stitch_generic.py\" import")
        check(placement < route_import,
              f"{path.name}: composed P-BODYCLR/R-PAIRMAP must precede route import")
        connected = txt.index("--require-connected")
        stitch = txt.index("route_and_stitch_generic.py\" stitch")
        check(stitch < connected,
              f"{path.name}: R-CRITESC must grade realized post-stitch copper")
    composed = (SCRIPTS / "placement_routability_preflight.py").read_text()
    check("placement_gates.inspect" in composed and
          "critical_route_check.check" in composed,
          "placement compositor no longer owns both physical and route-contract predicates")


@test("rebuild_all fails source-only schemas before invoking tscircuit")
def t_source_schema_precedes_tsci():
    txt = ALL.read_text()
    build = txt.index('run_stage tscircuit_build')
    check(txt.index('--schema-only') < build,
          "label_survival schema gate must precede tscircuit")
    check(txt.index('early_design_check.py') < build,
          "electrical source-schema gate must precede tscircuit")
    check(txt.index('control_protocol_check.py') < build,
          "control timing validation must precede tscircuit")
    check(txt.index('control_profile_codegen.py') < build,
          "generated timing-consumer parity must precede tscircuit")
    source_prec = txt.index('--phase source')
    check(source_prec < build,
          "part layout/precedent source gate must precede tscircuit")
    check(source_prec < txt.index('pre_route_review_check.py'),
          "part layout/precedent source gate must precede hash-bound reviews")


@test("both rebuild drivers keep the conditional RF module bounded inside "
      "existing lifecycle stages")
def t_rf_module_stage_order():
    for path in (ALL, REUSE):
        txt = path.read_text()
        contract = txt.find('rf_contract_check.py"')
        context = txt.find('run_stage rf_context')
        solver = txt.find('run_stage rf_solver')
        source = txt.find('run_stage rf_source')
        stitch = txt.rfind('route_and_stitch_generic.py" stitch')
        realized = txt.rfind('run_stage rf_realized')
        acceptance = txt.rfind('route_acceptance_gate.py"')
        check(-1 not in (contract, context, solver, source, stitch, realized,
                         acceptance),
              f"{path.name}: incomplete RF stage wiring")
        check(contract < context < solver < source,
              f"{path.name}: RF applicability/context/solver/source order")
        check(stitch < realized < acceptance,
              f"{path.name}: realized RF evidence must follow routing and "
              "precede final route acceptance")
        check("pipeline_review.py" not in txt[context:source],
              f"{path.name}: RF module added a reviewer/wait stage")


@test("both rebuild drivers emit all three fail-closed boundary holds")
def t_early_boundary_wiring():
    for path in (ALL, REUSE):
        txt = path.read_text()
        check(early_boundaries_ok(txt),
              f"{path.name}: incomplete E-CLOSURE/S-PART-FREEZE/P-FEASIBILITY wiring")
        board_generation = txt.index('$PY "$S/generate_board_generic.py"')
        check(txt.index("electrical_closure.py") < board_generation,
              f"{path.name}: E-CLOSURE must precede board generation")
        check(txt.index("S-PART-FREEZE.stage.json") <
              board_generation,
              f"{path.name}: part freeze must precede placement")


@test("early-boundary template check rejects a dropped typed receipt",
      kind="known_bad")
def t_early_boundary_wiring_has_teeth():
    text = ALL.read_text().replace(
        '--stage-result "$PIPELINE_EVIDENCE/P-FEASIBILITY.stage.json"',
        '--stage-result "$PIPELINE_EVIDENCE/removed.stage.json"', 1)
    check(not early_boundaries_ok(text),
          "template without P-FEASIBILITY unexpectedly passed wiring check")


@test("both rebuild drivers replay configured taps between route import and stitch")
def t_route_taps_stage_ordering():
    for path in (ALL, REUSE):
        txt = path.read_text()
        route_import = txt.index("route_and_stitch_generic.py\" import")
        taps = txt.index("route_and_stitch_generic.py\" taps")
        stitch = txt.index("route_and_stitch_generic.py\" stitch")
        check(route_import < taps < stitch,
              f"{path.name}: deterministic taps must replay after import and "
              "before zone fill/stitch")


@test("rebuild_all.sh: the human schematic is DELETED then regenerated, and the "
      "M-FRESH verify is handed it with --render")
def t_template_render_wiring():
    """The template half of the fix, and the `rm -f` is the load-bearing line.

    Rendering into a path that already holds last revision's PDF cannot fail
    safely: if the exact-Circuit-JSON renderer does not run, the old file survives
    and the seal copies it. Deleting first makes the failure mode ABSENCE,
    which F-RENDER names. The renderer therefore carries `|| true` on purpose
    — the GATE must report the outcome, not `set -e`, or the operator
    gets a bare non-zero exit with no finding.

    GIT-SWAP RED-VERIFIED against the pre-fix template (`git show HEAD:` at the
    commit that added the render stage): measured below on every run, because
    a wiring assertion that only ever sees the fixed file proves nothing."""
    t = ALL.read_text()
    check(_render_wiring_ok(t),
          "rebuild_all.sh must rm -f the schematic BEFORE rendering it, and "
          "pass --render to build_provenance.py verify")
    # the RED side, MEASURED not asserted: the template as it stood before this
    # change must be REJECTED by the same predicate.
    prev = run(["git", "-C", str(ROOT), "show",
                f"{PRE_RENDER_COMMIT}:skills/pcb-design/templates/03_src/rebuild_all.sh"])
    check(prev.rc == 0, f"could not read the pre-fix template: {prev.out[-400:]}")
    check(not _render_wiring_ok(prev.out),
          "the PRE-FIX template passed the render-wiring check — the check has "
          "no teeth (pre-fix it neither rendered nor graded schematic.pdf)")


if __name__ == "__main__":
    sys.exit(main())
