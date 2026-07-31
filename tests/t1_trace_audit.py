#!/usr/bin/env python3
"""GG-SHADOW / GG-RESOLVE: can a gate SEE its subject? (`trace_audit.py`)

THE EXPECTED ANSWERS LIVE HERE, NOT IN THE AUDITOR. `trace_audit.py --canary`
RUNS the hand-written canary gates and REPORTS what it found; it does not hold
the expectation. The literals below are written by a human. If the analyser
regresses, this suite goes red and the auditor cannot know it should have.
Merging the two for convenience would make this layer another instance of the
class it exists to kill (canon M1: checker and checked must not share a method).

WHAT THIS BANKED LAYER IS. Three rounds of a larger "grade the graders" layer
ended in an independent judge's BANK-AND-STOP. GG-SHADOW and GG-RESOLVE were
verified sound and are what remains; GG-KEY, GG-ZERO, GG-OPAQUE, GG-CENSUS,
GG-BASIS and GG-ALIAS were withdrawn, and `t_no_canon_gg_row_lacks_an_emitter`
pins that neither half of any withdrawn family survives — a canon row with no
emitter is its own defect, and this repo already carries one.

**THE HEADLINE TEST IS `t_vac_...` AND `t_kb_instance19_...`, WHICH ARE THE
SAME EXPERIMENT SPLIT IN TWO.** Two identical genuinely-blind subjects differing
by ONE FILE — `06_build/policy_audit.md`, a battery gate's own output. With it:
rc 0. Without it: rc 3. That is the control that stopped the layer, and it is
run on every suite invocation so the sentence it falsifies can never come back:
the rc-0 run must carry the exhaust caveat and must NOT claim observation.
"""
import json
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent /
                       'skills' / 'kicad-pcb' / 'scripts'))
from harness import (KPY, ROOT, check, contains, eq, main,      # noqa: E402
                     must_fail, must_pass, not_contains, run, test, tmpdir)

TOOL = ROOT / "skills/kicad-pcb/scripts/trace_audit.py"
GRADELIB = ROOT / "skills/kicad-pcb/gradelib"
CANARY = ROOT / "tests/fixtures/gg_canary"
CANON = ROOT / "skills/kicad-pcb/references/design-policies.md"

#: THE HUMAN'S ANSWER KEY. One row per canary gate. `clean_gate.py` yielding []
#: is the NEGATIVE CONTROL and is the most load-bearing row here: a canary made
#: only of defective gates is satisfied by an analyser that returns a finding
#: unconditionally.
CANARY_EXPECT = {
    "clean_gate.py": [],
    "resolve_gate.py": ["GG-RESOLVE"],
    "shadow_gate.py": ["GG-SHADOW"],
}

#: The two families this gate is allowed to emit. Anything else is either a
#: withdrawn family that came back or a new one that landed without a canon row.
BANKED = {"GG-SHADOW", "GG-RESOLVE"}


# ------------------------------------------------------------------ helpers
def gg(args, **kw):
    return run([KPY, TOOL] + [str(a) for a in args], **kw)


def blind_subject(d, with_exhaust):
    """A GENUINELY BLIND subject: a directory with no source at all, so every
    battery gate IS blind. `with_exhaust` adds the ONE file that separates the
    two arms of the instance-19 control — `06_build/policy_audit.md`, which
    `policy_audit.py` writes and reads back."""
    d = Path(d)
    (d / "06_build").mkdir(parents=True, exist_ok=True)
    if with_exhaust:
        (d / "06_build" / "policy_audit.md").write_text(
            "| M-REPRO | PASS | inherited from a previous run\n")
    return d


def trace(opens=(), probes=(), writes=()):
    """A synthetic trace, in the shape `sitecustomize.py` writes."""
    ev = [{"k": "open", "p": str(p), "m": "r"} for p in opens]
    ev += [{"k": "open", "p": str(p), "m": "w"} for p in writes]
    return {"events": ev, "probes": [{"how": "is_file", "p": str(p)}
                                     for p in probes]}


def emitted_ids():
    src = TOOL.read_text()
    return set(re.findall(r'Finding\(\s*"(GG-[A-Z]+)"', src))


def canon_gg_rows():
    return set(re.findall(r"^\|\s*(GG-[A-Z]+)\s*\|", CANON.read_text(), re.M))


# ================================================================ THE CANARY
@test("the canary reports exactly what a human wrote down here")
def t_canary_reports_exactly_what_a_human_wrote_down():
    r = must_pass(gg(["--canary"]), "trace_audit --canary")
    for gate, want in sorted(CANARY_EXPECT.items()):
        line = [l for l in r.out.splitlines() if l.strip().startswith(gate)]
        check(line, f"{gate} is missing from the canary report — every gate RUN "
                    f"must be a row, including the ones that yield nothing, or "
                    f"the printed denominator and the negative control both "
                    f"disappear\n{r.out}")
        got = sorted(set(re.findall(r"GG-[A-Z]+", line[0])))
        eq(got, sorted(want), f"{gate} canary findings")
    eq(len(CANARY_EXPECT), len(list(CANARY.glob("*_gate.py"))),
       "canary gates on disk vs rows in this file's answer key")


@test("the clean gate is silent BECAUSE it enumerates, not because the "
      "analyser is lenient")
def t_the_clean_gate_is_silent_because_it_enumerates():
    # The discrimination proof: clean_gate and shadow_gate read THE SAME
    # basename under the same root. The only difference is that one enumerates
    # both boards and the other selects one. If the analyser were lenient, both
    # would be silent; if it over-reached, both would fire.
    r = must_pass(gg(["--canary"]), "canary")
    contains(r.out, "clean_gate.py: (nothing)")
    contains(r.out, "shadow_gate.py: GG-SHADOW")


# ============================================================ THE TRACER SEAM
@test("the tracer is TRANSPARENT: a real gate is byte-identical with and "
      "without it")
def t_tracer_is_transparent():
    # A tracer that changes what it observes cannot be used on the battery it
    # exists to grade. Run a REAL project-scoped gate both ways.
    gate = ROOT / "skills/kicad-pcb/scripts/power_topology.py"
    subj = CANARY / "subject"
    td = tmpdir("gg_tr_")
    plain = run([KPY, gate, subj])
    traced = run([KPY, gate, subj], env={
        "GRADELIB_TRACE_DIR": str(td),
        "PYTHONPATH": f"{GRADELIB}{os.pathsep}" + os.environ.get("PYTHONPATH", "")})
    eq(traced.rc, plain.rc, "exit code with the tracer installed")
    eq(traced.out, plain.out, "stdout+stderr with the tracer installed")
    check(list(td.glob("trace.*.json")),
          "the tracer was transparent because it did not run at all — no trace "
          "file was written, which would make this test vacuous")
    shutil.rmtree(td, ignore_errors=True)


@test("read and probe are SEPARATE channels and are never summed")
def t_read_and_probe_are_separate_channels():
    d = tmpdir("gg_ch_")
    r = gg(["--subject", blind_subject(d, True)])
    contains(r.out, "OPENED FOR READING")
    contains(r.out, "merely PROBED (stat family, own channel, never summed)")
    shutil.rmtree(d, ignore_errors=True)


# =================================================== THE INSTANCE-19 CONTROL
@test("the rc-0 run over a blind board does NOT claim it observed anything")
def t_instance19_rc0_run_does_not_claim_observation():
    """THE SENTENCE THAT ENDED THE LAYER, PINNED SO IT CANNOT COME BACK.

    Round 3 printed `GG-TRACE OK: ... every one with an OBSERVED population > 0`
    over this exact subject. The only thing under the root is a battery gate's
    OWN OUTPUT that pre-dated the run, and no guard this tool has is an IDENTITY
    test, so the claim was unearned. What is printed now is a RAW COUNT with the
    caveat attached to it."""
    d = tmpdir("gg_i19a_")
    r = gg(["--subject", blind_subject(d, True)])
    eq(r.rc, 0, "a blind board WITH pre-existing exhaust still exits 0")
    contains(r.out, "NOT A PROOF OF OBSERVATION")
    contains(r.out, "NEITHER IS AN IDENTITY TEST")
    # The forbidden claim, in every spelling it has worn.
    for banned in ("OBSERVED population > 0", "every one with an OBSERVED",
                   "family/families graded"):
        not_contains(r.out, banned,
                     "the withdrawn subject-side liveness certification")
    shutil.rmtree(d, ignore_errors=True)


@test("the same blind board WITHOUT the exhaust file is exit 3, not a pass",
      kind="known_bad")
def t_kb_instance19_without_the_exhaust_file_is_exit_3():
    d = tmpdir("gg_i19b_")
    r = must_fail(gg(["--subject", blind_subject(d, False)]),
                  "blind board with no exhaust", expect="GG GRADED NOTHING")
    eq(r.rc, 3, "a battery that opened zero pre-existing files")
    contains(r.out, "THIS IS NOT A PASS")
    shutil.rmtree(d, ignore_errors=True)


@test("exit 0 over a battery that saw ONLY its own pre-existing exhaust",
      kind="vacuity", gate="trace_audit.py")
def t_vac_exit_zero_over_pre_existing_exhaust():
    """THE DECLARED BLIND SPOT, EXECUTABLE (canon G-VACUOUS).

    The graded fact — *the battery saw this board* — is FALSE here: the subject
    contains no source at all and every gate is blind. The gate exits 0 anyway,
    because the one file present is a battery gate's own output that ALREADY
    EXISTED, and neither the write-set (a METHOD test) nor the pre-run snapshot
    (an EXISTENCE test) is an IDENTITY test.

    Closing this needs an identity test — resolving each battery gate's declared
    OUTPUT paths and subtracting those — which is OWED and named in the module
    docstring. When it lands, this fixture is expected to break, and the fix is
    to convert it into a `known_bad`. That breakage is the ratchet."""
    d = tmpdir("gg_vac_")
    r = must_pass(gg(["--subject", blind_subject(d, True)]),
                  "the vacuous pass this gate declares")
    contains(r.out, "1 pre-existing file(s) under the subject root OPENED FOR "
                    "READING")
    shutil.rmtree(d, ignore_errors=True)


# ============================================================== EXIT VOCABULARY
@test("every exit code in the legend is reached by a real run")
def t_every_exit_code_is_reached_by_a_real_run():
    """Round 1 declared codes 3 and 4 in the legend and emitted them from
    nowhere — dead vocabulary, which is worse than none, because a legend reads
    as a capability. Each code below is produced by an actual invocation."""
    seen = {}
    d0 = tmpdir("gg_e0_")
    seen[gg(["--subject", blind_subject(d0, True)]).rc] = "0: no finding"
    seen[gg(["--root", "/nonexistent-XXX"]).rc] = "2: invocation"
    seen[gg([]).rc] = "2: no --subject"
    d3 = tmpdir("gg_e3_")
    seen[gg(["--subject", blind_subject(d3, False)]).rc] = "3: graded nothing"

    # 1 and 4 need a subject with a real defect. Build the smallest one: the
    # canary subject, graded by the two canary gates themselves.
    d = tmpdir("gg_e14_")
    proj = d / "proj"
    shutil.copytree(CANARY / "subject", proj)
    shutil.copy(CANARY / "shadow_gate.py", d / "shadow_gate.py")
    r1 = _run_gate_as_battery(d, proj, "shadow_gate.py")
    seen[r1.rc] = "1: findings"
    shutil.copy(CANARY / "resolve_gate.py", d / "resolve_gate.py")
    r4 = _run_gate_as_battery(d, proj, "resolve_gate.py")
    seen[r4.rc] = "4: unresolved"

    # 5 is the canary going silent — proved by its own test below.
    for code in (0, 1, 2, 3, 4):
        check(code in seen, f"exit {code} was never produced by a real run; "
                            f"reached {sorted(seen)}")
    shutil.rmtree(d, ignore_errors=True)
    for x in (d0, d3):
        shutil.rmtree(x, ignore_errors=True)


def _run_gate_as_battery(root, subj, gate_name):
    """Trace ONE named gate against a subject, with `--gate` pointing at a
    scratch `skills/x/scripts/` so `find_script` resolves it."""
    sd = Path(root) / "skills" / "x" / "scripts"
    sd.mkdir(parents=True, exist_ok=True)
    shutil.copy(Path(root) / gate_name, sd / gate_name)
    return gg(["--root", root, "--subject", subj, "--gate", gate_name,
               "--in-place"])


@test("the canary going SILENT is exit 5, never exit 0", kind="known_bad")
def t_kb_canary_silent_is_exit_5():
    """'I could not see' must never print the same word as 'there was nothing
    to see'. Blind the tracer by pointing GRADELIB_DIR at an empty directory —
    the shims never install, the audit hook never runs, no trace is written."""
    d = tmpdir("gg_blind_")
    (d / "gradelib").mkdir()
    r = must_fail(gg(["--canary"], env={"GRADELIB_DIR": str(d / "gradelib")}),
                  "trace_audit with observation switched off",
                  expect="GG UNOBSERVABLE")
    eq(r.rc, 5, "a silent canary")
    contains(r.out, "GG canary: 0 finding(s)",
             "the canary must actually have gone silent — an `expect` that "
             "matched anything would make this fixture vacuous, and this one "
             "did: tightening it from `expect=\"\"` is what exposed exit 5 "
             "being returned with NOTHING printed")
    # Every gate row must be silent. Asserting on the whole output would false-
    # fail on the LEGEND, which names GG-SHADOW in its description of exit 1 —
    # and a legend naming a family is the gate documenting itself, not finding
    # something.
    for g in CANARY_EXPECT:
        contains(r.out, f"{g}: (nothing)", f"{g} under a blinded tracer")
    contains(r.out, "This is NOT a pass", "the exit-5 sentence")

    # AND THE SAME ON A `--subject` RUN, which is the path that mattered: it
    # used to trace the whole battery first and print a read count, a coverage
    # ratio and a findings list ABOVE the line calling them unearned. Numbers
    # computed with observation off do not belong on the page at all.
    s = tmpdir("gg_blind2_")
    r2 = must_fail(gg(["--subject", blind_subject(s, True)],
                      env={"GRADELIB_DIR": str(d / "gradelib")}),
                   "a blinded --subject run", expect="GG UNOBSERVABLE")
    eq(r2.rc, 5, "a blinded --subject run")
    for banned in ("GG read count", "GG coverage", "GG battery"):
        not_contains(r2.out, banned,
                     "a number computed with observation off")
    shutil.rmtree(s, ignore_errors=True)
    shutil.rmtree(d, ignore_errors=True)


@test("an unreadable --root is exit 2 (never started), not exit 3 (graded "
      "nothing)", kind="known_bad")
def t_kb_bad_root_is_exit_2():
    r = must_fail(gg(["--root", "/nonexistent-XXX", "--subject", ROOT]),
                  "trace_audit with a bad root", expect="INVOCATION error")
    eq(r.rc, 2, "bad --root")


@test("no --subject is an INVOCATION error, not a green repo-level pass",
      kind="known_bad")
def t_kb_no_subject_is_an_invocation_error():
    """The round-3 vacuity, DELETED rather than declared. That layer had
    repo-scoped families, so a subject-less run exited 0 while every TRACED
    predicate had graded nothing — a green compatible with every gate in the
    fleet being blind on every board. Both banked families are subject-side, so
    the mode has nothing to do and says so."""
    r = must_fail(gg([]), "trace_audit with no subject",
                  expect="--subject PROJECT_DIR is REQUIRED")
    eq(r.rc, 2, "no --subject")


# =================================================== PREDICATE DISCRIMINATION
@test("GG-SHADOW fires ONCE on a planted unread twin, and is silent without it",
      kind="known_bad")
def t_kb_planted_twin_fires_exactly_once():
    import trace_audit as ta                                  # noqa: E402
    d = tmpdir("gg_twin_")
    a = d / "03_src" / "rules"
    b = d / "03_src" / "boardB" / "rules"
    a.mkdir(parents=True)
    b.mkdir(parents=True)
    (a / "nets.yaml").write_text("nets: []\n")
    have_clean = ta.index_basenames(d)
    tr = trace(opens=[a / "nets.yaml"])
    eq(len(ta.gg_shadow(tr, d, have_clean)), 0,
       "a gate reading the only file of its name has no shadow")
    # Plant the twin. ONE finding, not two — the finding is about the READ
    # path, and a count that scaled with the battery size would make a ceiling
    # a function of how many gates happened to run.
    (b / "nets.yaml").write_text("nets: []\n")
    have = ta.index_basenames(d)
    fs = ta.gg_shadow(tr, d, have)
    eq(len(fs), 1, "findings after planting one unread twin")
    eq(fs[0].gid, "GG-SHADOW", "finding id")
    contains(fs[0].msg, "boardB", "the finding names the unread twin")
    shutil.rmtree(d, ignore_errors=True)


@test("GG-SHADOW is scoped: prose, generated subtrees and sealed releases are "
      "OUT")
def t_shadow_scope_excludes_prose_and_generated():
    import trace_audit as ta                                  # noqa: E402
    check(".md" not in ta.GRADED_SUFFIXES,
          "`.md` back in scope would hard-fail the pipeline's OWN template "
          "layout: 01_docs/journal/<t>.md beside 01_docs/learnings/<t>.md, and "
          "the contracts.md this repo requires in EVERY folder")
    for gen in ("build", "dist", "kicad", ".tscircuit", "verification"):
        check(gen in ta.GENERATED_PARTS, f"{gen} must be out of scope")
    check(not ta._authored(Path("p/07_releases/v1/source/x.yaml")),
          "a sealed release is not authored source (canon M-SHIP)")
    check(ta._authored(Path("p/03_src/rules/nets.yaml")), "03_src is authored")
    check(not ta._authored(Path("p/03_tscircuit/dist/circuit.json")),
          "a generated subtree inside an authored one is not authored")


@test("GG-RESOLVE fires on a SELECTION and is silent on an ENUMERATION",
      kind="known_bad")
def t_kb_resolve_selection_not_enumeration():
    import trace_audit as ta                                  # noqa: E402
    d = tmpdir("gg_res_")
    b = d / "03_src" / "boardB" / "rules"
    b.mkdir(parents=True)
    (b / "policy_waivers.yaml").write_text("waivers: []\n")
    have = ta.index_basenames(d)
    pre = ta.snapshot(d)
    existed = ta._pre_existed(pre, d)
    missing = d / "03_src" / "rules" / "policy_waivers.yaml"

    # ONE look at a name, and it misses: a SELECTION. This is the finding.
    fs = ta.gg_resolve(trace(probes=[missing]), d, have, existed)
    eq(len(fs), 1, "one look at an absent path whose basename exists elsewhere")
    eq(fs[0].gid, "GG-RESOLVE", "finding id")
    check(fs[0].unresolved, "GG-RESOLVE must carry unresolved -> exit 4")

    # SEVERAL looks at the same name: an ENUMERATION. Silence, whether or not
    # any candidate hit. MEASURED: widening to the stat family without this
    # discriminator cost 18 false positives on cooksense in one run, and
    # accused `waiver_provenance.waiver_files()` — the resolution exemplar.
    other = d / "03_src" / "boardC" / "rules" / "policy_waivers.yaml"
    eq(len(ta.gg_resolve(trace(probes=[missing, other]), d, have, existed)), 0,
       "an enumeration cannot pick the wrong file because it does not pick")
    shutil.rmtree(d, ignore_errors=True)


@test("a gate's own exhaust is subtracted however it was written")
def t_exhaust_is_subtracted_by_method_and_by_birth():
    import trace_audit as ta                                  # noqa: E402
    d = tmpdir("gg_ex_")
    (d / "06_build").mkdir(parents=True)
    direct = d / "06_build" / "direct.md"
    renamed = d / "06_build" / "renamed.md"
    pre = ta.snapshot(d)                     # neither exists yet
    direct.write_text("x")
    renamed.write_text("x")                  # as if os.replace'd into place
    # (a) opened for writing -> the METHOD test catches it.
    # (b) never opened for writing, but BORN after the snapshot -> the
    #     EXISTENCE test catches it. This is `policy_audit.md.tmp` + os.replace.
    reads, _p, writes = ta.subject_evidence(
        [trace(opens=[direct, renamed], writes=[direct])], d, pre)
    eq(len(reads), 0, "reads after both exhaust filters")
    eq(len(writes), 2, "paths discounted as the battery's own output")
    shutil.rmtree(d, ignore_errors=True)


@test("the battery roster is DERIVED from three properties, not hand-listed")
def t_battery_is_derived_not_listed():
    import trace_audit as ta                                  # noqa: E402
    bat = ta.default_battery(ROOT)
    check(len(bat) >= 10, f"the derived battery is {len(bat)} gate(s); a "
                          f"collapse to a handful means the detector broke and "
                          f"every unread file would read as clean")
    check(ta.__file__ and Path(ta.__file__).name not in bat,
          "the gate must never trace itself recursively")
    # A network-importing script is never in the battery: a coverage layer must
    # not make outbound calls to compute a denominator.
    check("jlc_stock_check.py" not in bat, "a network gate is out")
    # The verdict detector is IMPORTED, never re-implemented (canon M1).
    src = TOOL.read_text()
    contains(src, "import gate_contract_audit",
             "the 'is this a gate' detector must have ONE home")


@test("short() is mode-invariant across a symlink", kind="known_bad")
def t_kb_short_is_mode_invariant_across_a_symlink():
    """RED-VERIFIED, MEASURED ON EVERY RUN. The pre-fix `short()` resolved in
    the sandbox branch and NOT in the fall-through branch, so the same defect on
    the same file rendered `03_src/cooksense/rules/nets.yaml` sandboxed and
    `03_src/rules/nets.yaml` in place. MEASURED on a scratch copy of cooksense:
    rc, coverage, read count, probe count and finding COUNT were all identical
    and all 5 GG-SHADOW findings still differed. `where` is the dedupe KEY, so
    the asymmetry was one symlink away from counting one defect twice.

    The pre-fix implementation is re-introduced BELOW and measured DIVERGING;
    the shipped one is measured AGREEING. Neither is asserted in prose."""
    import trace_audit as ta                                  # noqa: E402
    d = tmpdir("gg_short_")
    real = d / "board" / "rules"
    real.mkdir(parents=True)
    (real / "nets.yaml").write_text("nets: []\n")
    (d / "rules").mkdir()
    os.symlink(real / "nets.yaml", d / "rules" / "nets.yaml")
    via_link, via_real = d / "rules" / "nets.yaml", real / "nets.yaml"

    def prefix_short(p, sandbox):
        """The SHIPPED-BEFORE version: resolve only in the sandbox branch."""
        for sb, rl in sandbox:
            try:
                return str(Path(rl) / Path(p).resolve().relative_to(sb))
            except (ValueError, OSError):
                pass
        try:
            return str(Path(p).resolve().relative_to(ROOT))
        except (ValueError, OSError):
            return str(p)

    sb = [(d, "SUBJ")]
    check(prefix_short(via_link, sb) != prefix_short(via_link, []),
          "the pre-fix short() must DIVERGE between the two modes, or this "
          "red-verification proves nothing")

    keep = ta._SANDBOX[:]
    try:
        ta._SANDBOX[:] = sb
        sandboxed = ta.short(via_link)
        ta._SANDBOX[:] = []
        inplace = ta.short(via_link)
    finally:
        ta._SANDBOX[:] = keep
    check(sandboxed.endswith("board/rules/nets.yaml"),
          f"sandbox branch must resolve the symlink, got {sandboxed}")
    check(inplace.endswith("board/rules/nets.yaml"),
          f"fall-through branch must resolve it too, got {inplace}")
    eq(Path(sandboxed).name, Path(via_real).name, "same file, same basename")
    shutil.rmtree(d, ignore_errors=True)


# ================================================== RED-VERIFIED MECHANISM
@test("switching the STAT channel off blinds GG-RESOLVE on its own canary",
      kind="known_bad")
def t_kb_the_stat_channel_off_blinds_resolve():
    """RED-VERIFIED, MEASURED ON EVERY RUN — not asserted in a docstring.

    A COPY of `gradelib/` with the stat-family install REMOVED is built here and
    `GRADELIB_DIR` is pointed at it. That is round 1's `open`-only tracer,
    restored. `resolve_gate.py` guards with `is_file()` and issues no `open`, so
    with the shim gone GG-RESOLVE measures exactly ZERO on the very incident its
    canon row cites — which is what shipped, with no red fixture anywhere."""
    d = tmpdir("gg_nostat_")
    gl = d / "gradelib"
    shutil.copytree(GRADELIB, gl)
    src = (gl / "shims.py").read_text()
    # Remove the two roster entries the install loop iterates. The file still
    # imports, still installs, and still writes traces — it is simply blind to
    # the stat family, exactly as round 1 was.
    src = re.sub(r"^PATH_PROBES = \[[^\]]*\]", "PATH_PROBES = []", src,
                 flags=re.M | re.S)
    src = re.sub(r"^OSPATH_PROBES = \[[^\]]*\]", "OSPATH_PROBES = []", src,
                 flags=re.M | re.S)
    src = src.replace("pathlib.Path.stat = _stat", "pass")
    (gl / "shims.py").write_text(src)

    blind = gg(["--canary"], env={"GRADELIB_DIR": str(gl)})
    contains(blind.out, "resolve_gate.py: (nothing)",
             "with the stat family unshimmed GG-RESOLVE must go silent")
    contains(blind.out, "shadow_gate.py: GG-SHADOW",
             "GG-SHADOW rides the `open` audit hook and must be UNAFFECTED — "
             "if both went silent this fixture would only prove the copy was "
             "broken")
    # ...and the shipped gradelib finds it.
    contains(must_pass(gg(["--canary"]), "canary").out,
             "resolve_gate.py: GG-RESOLVE")
    shutil.rmtree(d, ignore_errors=True)


@test("putting .md back into GG-SHADOW's scope returns the journal/learnings "
      "false positive", kind="known_bad")
def t_kb_md_in_scope_returns_the_journal_false_positive():
    """RED-VERIFIED, MEASURED ON EVERY RUN. `01_docs/journal/<t>.md` beside
    `01_docs/learnings/<t>.md` is the layout `skills/pcb-design/templates/`
    SHIPS. Round 1 hard-failed on it. A ratchet that breaks on a correct action
    does not get honoured, it gets deleted."""
    import trace_audit as ta                                  # noqa: E402
    d = tmpdir("gg_md_")
    for sub in ("journal", "learnings"):
        (d / "01_docs" / sub).mkdir(parents=True)
        (d / "01_docs" / sub / "routing.md").write_text("# routing\n")
    have = ta.index_basenames(d)
    tr = trace(opens=[d / "01_docs" / "journal" / "routing.md"])
    eq(len(ta.gg_shadow(tr, d, have)), 0,
       "the shipped scope must be SILENT on the repo's own doc layout")
    keep = ta.GRADED_SUFFIXES
    try:
        ta.GRADED_SUFFIXES = keep + (".md",)
        n = len(ta.gg_shadow(tr, d, have))
    finally:
        ta.GRADED_SUFFIXES = keep
    eq(n, 1, "with .md back in scope the false positive must RETURN, or this "
             "red-verification proves nothing")
    shutil.rmtree(d, ignore_errors=True)


@test("the basename index is taken BEFORE the battery runs", kind="known_bad")
def t_kb_index_is_pre_battery():
    """A file the battery itself creates must not be able to read as an unread
    twin. Recomputing the index inside the predicate — which is what the
    inherited code did — makes a gate's own output a finding against it."""
    import trace_audit as ta                                  # noqa: E402
    d = tmpdir("gg_idx_")
    a = d / "03_src" / "rules"
    a.mkdir(parents=True)
    (a / "nets.yaml").write_text("nets: []\n")
    have_pre = ta.index_basenames(d)                  # BEFORE
    born = d / "03_src" / "gen"
    born.mkdir()
    (born / "nets.yaml").write_text("nets: []\n")     # the battery writes it
    have_post = ta.index_basenames(d)                 # AFTER (the pre-fix way)
    tr = trace(opens=[a / "nets.yaml"])
    eq(len(ta.gg_shadow(tr, d, have_pre)), 0,
       "a pre-battery index must not see a file that did not exist yet")
    eq(len(ta.gg_shadow(tr, d, have_post)), 1,
       "a post-battery index MUST manufacture the finding, or this "
       "red-verification proves nothing")
    shutil.rmtree(d, ignore_errors=True)


# =============================================== CANON / CONTRACT COHERENCE
@test("every emitted GG-* id has a canon row, and every canon GG-* row has an "
      "emitter")
def t_no_canon_gg_row_lacks_an_emitter():
    """BOTH DIRECTIONS. A check-ID with no canon row cannot be waived, counted
    or regraded; a canon row with no emitter is a capability a reader believes
    in that does not exist — this repo already carries one (`M-BOUND`), which is
    why the withdrawn GG-* families were retired from BOTH halves rather than
    left as prose."""
    emitted, canon = emitted_ids(), canon_gg_rows()
    eq(emitted, BANKED, "GG-* ids emitted by trace_audit.py")
    eq(canon, BANKED, "GG-* rows in design-policies.md")
    for gone in ("GG-KEY", "GG-ZERO", "GG-OPAQUE", "GG-CENSUS", "GG-BASIS",
                 "GG-ALIAS"):
        check(gone not in canon and gone not in emitted,
              f"{gone} was WITHDRAWN by the bank-and-stop decision; it must "
              f"have neither a canon row nor an emitter")


@test("the canon row for the snapshot rule states the LIMIT, not a general "
      "guarantee")
def t_canon_does_not_claim_the_snapshot_is_method_independent():
    """The corrected sentence. The retired one read that the snapshot rule *is
    method-independent and holds for atomic renames, subprocess writes, shell
    redirection and anything else that has not been invented yet* — MEASURED
    FALSE by instance 19. Canon here is read by future agents as settled fact,
    and a wrong general guarantee about a subtle mechanism is exactly how the
    0.60 mm silk corollary propagated into two canon files."""
    txt = CANON.read_text()
    contains(txt, "NEITHER IS AN IDENTITY TEST",
             "the canon must name the gap it actually has")
    # THE FALSIFIED CLAUSE MAY APPEAR — QUOTED AND RETIRED, NEVER ASSERTED.
    # Deleting it outright would be the weaker move: an agent who meets the old
    # wording in a stale brief or an old commit body needs to be able to grep
    # this file and find the refutation. So every occurrence must be inside its
    # own retirement.
    needle = "anything else that has not been invented yet"
    hits = [m.start() for m in re.finditer(re.escape(needle), txt)]
    check(hits, "the retired formulation must be RECORDED, not silently "
                "deleted — a future agent meeting it elsewhere has to be able "
                "to find why it is wrong")
    for h in hits:
        window = txt[h:h + 400]
        check("MEASURED FALSE" in window and "RETIRED" in window,
              f"the falsified general guarantee appears at offset {h} without "
              f"'MEASURED FALSE'/'RETIRED' within 400 chars — that is an "
              f"ASSERTION, not a retirement:\n{window[:300]}")
    # And the control that falsified it is named, with both arms.
    contains(txt, "differing by ONE FILE", "the decisive control")
    contains(txt, "read_count_proves_observation", "the sidecar caveat field")


@test("the gate meets its own G-INPUT/G-COVER/G-RED obligations")
def t_the_gate_meets_the_gate_contract():
    import gate_contract_audit as gca                         # noqa: E402
    rows = [r for r in gca.audit(ROOT)["gates"]
            if r["script"].endswith("trace_audit.py")]
    eq(len(rows), 1, "trace_audit.py must be IN the gate inventory")
    r = rows[0]
    check(r["cover"], "G-COVER: trace_audit.py must print an N/M denominator")
    check(r["input"], "G-INPUT: trace_audit.py must name what it graded")
    check(r["red"], "G-RED: trace_audit.py must have a fixture that fails it")


if __name__ == "__main__":
    sys.exit(main())
