#!/usr/bin/env python3
"""trace_audit.py — OBSERVED-GRADE: can a gate SEE its subject? (canon GG-*)

    trace_audit.py --subject PROJECT_DIR        # the graded run
    trace_audit.py --gate NAME --subject DIR    # trace ONE gate
    trace_audit.py --canary                     # run the canary and stop
    trace_audit.py --explain                    # print the exit legend and go

WHY THIS EXISTS. `contracts_audit.py` governs FOLDERS. `gate_contract_audit.py`
governs the CHECKERS' CONTRACTS — that each prints a denominator, names its
input and has a red fixture. Nothing governed whether a checker COULD SEE ITS
SUBJECT. Sixteen distinct gates were found by hand in one session that were
green, internally honest, and structurally blind: a gate reading `03_src/rules/`
on a project whose rules live at `03_src/<board>/rules/`; a coverage line that
is 100 % by construction. Each cost a board round.

**THE PROPERTY THIS ADDS TO M-COVER: the denominator must be OBSERVED, NOT
PRINTED.** `gate_contract_audit` can confirm a gate prints `N/M`. Only a trace
can confirm that N and M describe the artifact the gate was pointed at.

TWO FAMILIES, AND ONLY TWO. This file is the BANKED remainder of a larger
"grade the graders" layer that an independent judge stopped after three rounds.
GG-SHADOW and GG-RESOLVE were verified sound and are kept; GG-KEY, GG-ZERO,
GG-OPAQUE, GG-CENSUS, GG-BASIS and GG-ALIAS were withdrawn and have NO canon
row and NO emitter here — a canon row with no emitter is its own defect, so
neither half was carried. See the post-mortem in `design-policies.md`'s
`GG-* mechanics` section.

  GG-SHADOW   a same-basename file under the subject root that NOTHING in the
              run opened. The strongest thing the layer produced: mode-
              invariant, 0 false positives across 7 projects, silent on the
              highest-multiplicity basename in the tree (47 `part.yaml`).
              **"NOTHING IN THE RUN" IS A FLEET UNION OVER EVERY TRACE, AND
              THE UNION IS THE PREDICATE.** A tracer writes one trace per
              PROCESS, so a gate that dispatches a worker subprocess per board
              arrives as several. Testing "never opened" against ONE of those
              — which is what shipped — makes the verdict a function of the
              gate's PROCESS TOPOLOGY: MEASURED, `tests/fixtures/gg_dispatch/`,
              two gates with the provably identical 2-file read-set gave RAW
              EXIT 1 with 2 FALSE findings (dispatcher) against RAW EXIT 0 with
              none (in-process). See `opened_union()`.
  GG-RESOLVE  a path the gate LOOKED AT (opened *or statted*) that does not
              exist, while a file of that name DOES exist under the subject
              root, and the gate looked at EXACTLY ONE path of that name.

WHAT IT CANNOT DO. Stated here rather than left to be discovered:

  * **A wrong PREDICATE over a correctly-read subject is invisible.** A gate
    that reads every pad and computes a Euclidean distance where the question
    is topological traces perfectly clean. No read-set reaches those.
  * **A check that was never written is unreachable.** A tracer can only grade
    code that runs.
  * **Whether the ORACLE is right.** A gate reading its whole subject against a
    wrong vendor model produces a perfectly-covered, entirely wrong verdict and
    scores clean here.
  * **FILE identity, not object identity.** `pcbnew.LoadBoard(path)` takes a
    Python str so the FILE is observed; which pads it then examined is C++ and
    raises no Python event.
  * **Trace absence is a silent global off-switch.** Drop `PYTHONPATH` and every
    gate loses observation while still printing its verdict. The CANARY is the
    only defence, and its silence is exit 5, never exit 0.

VACUITY: (canon G-VACUOUS, applied to this gate.) Fixtured by
`tests/t1_trace_audit.py`, `kind="vacuity", gate="trace_audit.py"`.

**THIS GATE CAN EXIT 0 OVER A BATTERY THAT SAW NOTHING BUT A FILE IT HAPPENED
TO OPEN, AND NO GUARD IT HAS CLOSES THAT.** The read count printed below is a
SUPERSET of subject evidence, and it is printed as a raw count with that caveat
attached rather than as a certification, because the certification would be
FALSE. MEASURED — the control that ended the layer, and the wider one that
followed it. Both arms use a genuinely-blind board (a real project with its
source dirs moved aside, so every gate IS blind) and differ by ONE FILE:

    06_build/ alone .................................... RAW EXIT 3
    + 06_build/policy_audit.md .......................... RAW EXIT 0
    + 01_docs/BRIEF.md, THREE LINES OF PROSE ............ RAW EXIT 0

The first extra file is a battery gate's OWN OUTPUT — the narrow, declared arm.
**THE SECOND IS NOT ANY GATE'S OUTPUT AND IS GRADED BY NOTHING.** `BRIEF.md` is
merely a file two battery gates (`power_topology.py`,
`import_provenance_check.py`) happen to open, and it lifts exit 3 to exit 0
exactly as the exhaust does. The true statement is therefore **ANY PRE-EXISTING
FILE ANY GATE HAPPENS TO OPEN**, and the exhaust case is its worst instance
rather than its boundary. This was found by measuring a caveat that had been
DECLARED narrower than it measures; the umbrella sentences stayed true, so it
was an under-statement, but the executable ratchet was pinned to the narrow arm
and the wide one was undefended.

The cause is that BOTH available guards are the wrong KIND of test:

    write-set   a METHOD test. `policy_audit.py` writes `policy_audit.md.tmp`
                and `os.replace`s it, so the write-set holds only the `.tmp`.
    snapshot    an EXISTENCE test. The real path PRE-EXISTED, so it is in the
                snapshot and reads as subject evidence.

Neither is an IDENTITY test — neither asks *is this path one the battery
PRODUCES*. Both are kept, because each catches what the other misses; what is
NOT kept is the sentence claiming they are sufficient. The direction that IS
sound is the negative: **zero reads is a proof of no observation**, so a
`--subject` run with an empty read set exits 3, and only that direction carries
a verdict here.

The identity test that would close it — resolving each battery gate's declared
output paths and subtracting THOSE — is OWED, named, and not pretended to. AND
IT IS NOW KNOWN TO BE A PARTIAL FIX: it closes the `policy_audit.md` arm and
does NOT close the `BRIEF.md` arm, because BRIEF.md is not an output. Both arms
are reproduced on every suite run by the `kind="vacuity"` fixture.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
# A TEST SEAM, and the only one. `t1_trace_audit.py` points this at a COPY of
# gradelib with a single fix reverted, so every red-verification in that suite
# is MEASURED on every run rather than asserted in a docstring. Unset in normal
# operation.
GRADELIB = Path(os.environ.get("GRADELIB_DIR") or (HERE.parent / "gradelib"))
KPY = "/usr/bin/python3"

# ------------------------------------------------------------ exit vocabulary
# ONE home for the code and its sentence, so a verdict and its exit can never
# diverge (the `jlc_stock_check` exemplar: compute the zero BEFORE writing any
# sidecar). Codes 2 and 3 are settled repo precedent (`waiver_provenance`,
# 1b70262a); 4 and 5 break the "bad invocation" vs "I resolved to the wrong
# path" vs "I could not see" tie from all three sides.
EXIT = {
    0: "NO FINDING — GG-SHADOW and GG-RESOLVE both came back empty. NOT a "
       "certificate that the battery saw the board (see the read-count "
       "caveat)",
    1: "FINDINGS — a same-basename file under the subject root was read by "
       "nothing (GG-SHADOW)",
    2: "INVOCATION — the gate never started (bad args, unreadable root, no "
       "--subject)",
    3: "GRADED NOTHING — started, subject resolved, and the battery opened "
       "ZERO pre-existing files under it",
    4: "UNRESOLVED — a path a gate SELECTED does not exist while that basename "
       "does exist under the subject root (GG-RESOLVE)",
    5: "UNOBSERVABLE — observation was not COMPLETE: the canary came back "
       "silent, or a trace hit the GRADELIB_MAX_EVENTS cap and holds a PREFIX "
       "of its read-set. NEVER a skip",
}


def legend():
    return "\n".join(f"    exit {k} = {v}" for k, v in sorted(EXIT.items()))


def _trunc_line(where, pids):
    """The exit-5 sentence for a TRUNCATED trace. One home, both call sites."""
    return (
        f"GG UNOBSERVABLE: {len(pids)} {where} trace(s) hit the "
        f"GRADELIB_MAX_EVENTS cap and STOPPED RECORDING (pid(s) "
        f"{', '.join(str(p) for p in pids[:6])}). A truncated trace holds a "
        f"PREFIX of the read-set, not the read-set, and GG-SHADOW's claim is "
        f"that NOTHING opened a file — the one claim a prefix CANNOT support, "
        f"so truncation manufactures FALSE findings rather than losing true "
        f"ones. No GG-SHADOW or GG-RESOLVE verdict is carried. Raise "
        f"GRADELIB_MAX_EVENTS and rerun. This is NOT a pass.")


class Finding:
    def __init__(self, gid, where, msg, unresolved=False):
        self.gid, self.where, self.msg = gid, where, msg
        #: EXIT 4 IS CARRIED HERE, NOT INFERRED FROM THE ID. Round 1 declared
        #: code 4 in the legend and emitted it from nowhere — dead vocabulary,
        #: which is worse than no vocabulary, because the legend reads as a
        #: capability.
        self.unresolved = unresolved

    def __str__(self):
        return f"FAIL {self.gid}  {self.where}\n    {self.msg}"

    # Hashable on the CLAIM, so three gates opening the same shadowed file
    # report it once. A finding repeated per-invocation would make the count a
    # function of how many gates the battery happens to run.
    def _key(self):
        return (self.gid, self.where, self.msg)

    def __eq__(self, o):
        return isinstance(o, Finding) and self._key() == o._key()

    def __hash__(self):
        return hash(self._key())


# ==================================================================== TRACING
def run_traced(cmd, tracedir, cwd=None, timeout=600):
    """Run a command with the tracer installed. Returns (rc, out, traces)."""
    env = dict(os.environ)
    env["GRADELIB_TRACE_DIR"] = str(tracedir)
    env["PYTHONPATH"] = str(GRADELIB) + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        cp = subprocess.run([str(c) for c in cmd], capture_output=True,
                            text=True, env=env, timeout=timeout,
                            cwd=str(cwd) if cwd else None)
        rc, out = cp.returncode, (cp.stdout or "") + (cp.stderr or "")
    except subprocess.TimeoutExpired:
        rc, out = 124, "TIMEOUT"
    return rc, out, load_traces(tracedir)


def load_traces(d):
    out = []
    for f in sorted(Path(d).glob("trace.*.json")):
        try:
            out.append(json.loads(f.read_text()))
        except Exception:
            pass
    return out


def opened(tr):
    """-> [abs path] the process opened for READING."""
    return [e["p"] for e in tr["events"]
            if e["k"] == "open" and "w" not in e.get("m", "r")
            and "a" not in e.get("m", "r")]


def wrote(tr):
    """-> [abs path] the process opened for WRITING. A grader that MUTATES its
    subject is not observing it, so the writes are counted and printed."""
    return [e["p"] for e in tr["events"]
            if e["k"] == "open"
            and any(c in e.get("m", "r") for c in ("w", "a", "+", "x"))]


def opened_union(traces):
    """-> {realpath} EVERY path ANY traced process in the run opened for reading.

    **GG-SHADOW'S PREDICATE IS A FLEET UNION, AND THIS IS WHERE THE UNION IS
    TAKEN.** The canon row, this module's docstring and `default_battery`'s all
    say a shadow is a file *never opened by anything in the run*, and the
    derived battery exists BECAUSE of that union — a hand-listed battery made 10
    of 16 round-1 findings false. Building the read-set PER TRACE instead
    silently narrows "the run" to "this one process", and the two are the same
    thing only for a gate that does all its own reading.

    MEASURED 2026-07-31, and it is why this function exists: two gates with the
    PROVABLY IDENTICAL read-set (2 files, both arms) — `tests/fixtures/
    gg_dispatch/dispatch_gate.py`, which spawns one worker SUBPROCESS per board,
    and `inproc_gate.py`, which reads the same two files in one process. Per
    trace: RAW EXIT **1** with **2** GG-SHADOW findings, both FALSE, against RAW
    EXIT **0** with none. **THE VERDICT WAS A FUNCTION OF THE GATE'S PROCESS
    TOPOLOGY, NOT OF WHAT THE GATE READ.**

    That is not an exotic shape. `03_src/rebuild_all.sh` already dispatches
    per-board; `adr_bound_provenance.py` and `waiver_provenance.py` spawn
    subprocesses; and `policy_audit.py` splits into 8 traces on
    smc0985-cooksense where its largest single trace sees 76 of the 133 files
    the gate opened — **43 % of the battery's most important gate's own reads
    were invisible to the predicate grading it.**

    A tracer writes one `trace.<pid>.json` per PROCESS, so a subprocess's reads
    arrive as a SEPARATE trace. Union first, grade after.

    Realpath-keyed, and `.exists()`-filtered, exactly as the per-trace set was:
    a path opened through a `03_src/rules/` symlink and a path opened at
    `03_src/<board>/rules/` are the same file and must cancel.
    """
    return {os.path.realpath(p) for tr in traces for p in opened(tr)
            if Path(p).exists()}


def truncated_traces(traces):
    """-> [pid] whose event log hit `GRADELIB_MAX_EVENTS` and STOPPED.

    THE CONSUMER FOR A FIELD THAT HAD NONE. `sitecustomize.py` has recorded
    `truncated` since the tracer was written and NOTHING read it — a
    declaration with no consumer, which is the exact defect class this layer
    exists to report, sitting inside the layer. Either it gets a reader that
    fails loudly or it gets deleted; this is the reader.

    It has to be LOUD rather than advisory, because a truncated trace is not
    merely incomplete — it is UNSOUND IN THE DIRECTION THAT FIRES. GG-SHADOW's
    claim is *nothing opened this file*. Over a read-set that stopped at a cap,
    that claim cannot be made about anything past the cap, so truncation
    manufactures FALSE findings rather than losing true ones. A run with any
    truncated trace therefore carries no GG-SHADOW verdict at all: exit 5,
    UNOBSERVABLE, the same code as a silent canary and for the same reason —
    "I could not see" must never print the same word as "there was nothing to
    see".
    """
    return sorted(tr.get("pid") for tr in traces if tr.get("truncated"))


def probed(tr):
    """-> [abs path] the process STATTED without opening.

    ITS OWN CHANNEL, NEVER SUMMED WITH `opened`. A gate that asks `p.is_file()`
    has LOOKED AT that path — the whole question GG-RESOLVE asks — but it has
    not read it, and a coverage number that adds a probe to a read would be a
    strong number diluted by a weak one.
    """
    return [e["p"] for e in tr.get("probes", [])]


def snapshot(subj):
    """Realpath of every path under the subject root, BEFORE the battery runs.

    Realpaths, because a project can reach the same file through a
    `03_src/rules/` symlink and through `03_src/<board>/rules/`.

    **THIS IS AN EXISTENCE TEST, NOT AN IDENTITY TEST, AND THAT IS THE LAYER'S
    OPEN GAP.** It discounts a path that was BORN during the run, whatever
    method created it — which is strictly more than the write-set catches
    (`os.replace` of a `.tmp` leaves the real path unwritten). It does NOT
    discount a gate's own output that ALREADY EXISTED when the battery started.
    See the module docstring: the two identical blind boards differing only by
    the presence of `06_build/policy_audit.md` gave rc 0 and rc 3.
    """
    out = set()
    sp = Path(subj)
    if not sp.is_dir():
        return out
    for p in sp.rglob("*"):
        try:
            out.add(os.path.realpath(p))
        except OSError:                                    # pragma: no cover
            pass
    return out


def subject_evidence(traces, subj, pre=None):
    """THE ONE SUBJECT-SIDE READ SET. Both families' inputs come from here.

    Returns (reads, probes, writes). Three filters, each with its own incident:

      * `.exists()` — a path that is not there was not observed.
      * MINUS `wrote()` — a grader's own output is not evidence about its
        subject. This is `M1` (checker and checked must not share a method)
        stated for a denominator: a number a gate can raise by writing a file
        is a number that measures the gate.
      * MINUS anything absent from `pre` — born during the run, so exhaust
        however it arrived. `policy_audit.py` writes `.md.tmp` and
        `os.replace`s it; the write-set alone walks straight past that.
      * REALPATH-KEYED, so a write through one name subtracts the read through
        a symlink to it.

    **AND THE RESULT IS STILL A SUPERSET OF SUBJECT EVIDENCE.** None of these
    is an IDENTITY test — none asks whether the path is one the battery
    PRODUCES — so a gate's own output that pre-dated the run survives every
    filter. The count is therefore reported as a raw number carrying that
    caveat, and only its ZERO is allowed to carry a verdict.
    """
    def norm(p):
        try:
            return os.path.realpath(p)
        except OSError:                                   # pragma: no cover
            return str(p)

    # THE SUBJECT ROOT ITSELF IS NOT EVIDENCE. Every gate in the battery stats
    # its argument; `p.is_dir()` on an EMPTY directory returns True, and
    # counting that as an observation is "I found the folder" wearing the words
    # "I graded the board". MEASURED: it is 11 of 16 invocations' ONLY
    # subject-side event on an empty subject.
    root_real = norm(subj)
    writes = {norm(p) for tr in traces for p in wrote(tr)
              if under(Path(p), subj)}

    def keep(p):
        if not Path(p).exists() or not under(Path(p), subj):
            return None
        n = norm(p)
        if n == root_real or n in writes:
            return None
        if pre is not None and n not in pre:
            writes.add(n)          # it was BORN during the run: exhaust
            return None
        return n

    reads, probes = set(), set()
    for tr in traces:
        reads |= {n for n in (keep(p) for p in opened(tr)) if n}
        probes |= {n for n in (keep(p) for p in probed(tr)) if n}
    return reads, probes, writes


# ================================================== TRACED PREDICATES (GG-*)
def gg_resolve(tr, subject, have, existed):
    """A path the gate LOOKED AT that does not exist, whose basename DOES exist
    under the subject root, AND WHICH THE GATE NEVER REACHED BY ANY OTHER PATH.
    'You looked in the wrong place', as opposed to 'you enumerated and one
    candidate was absent'.

    TWO FIXES OVER ROUND 1, BOTH MEASURED:

    (1) LOOKING AT IS NOT OPENING. Round 1 watched `open` alone. Real gates do
        not open a file to ask whether it is there — MEASURED 2026-07-31, 160
        `.is_file()`, 88 `.is_dir()`, 82 `.exists()`, 6 `.stat()` and 12
        `os.path.*` guards across 47 of 58 scripts, none of which raises an
        audit event. So the predicate measured EXACTLY ZERO on the very
        incident its canon row cites: `waiver_provenance` guards with
        `p.is_file()` and issues no `open` at all. The stat family is shimmed
        in `gradelib/shims.py` and arrives here as `probed()`.

    (2) ENUMERATION IS NOT MIS-RESOLUTION, and widening (1) without this turned
        the RESOLUTION EXEMPLAR into 18 findings — MEASURED, on the first run
        after the stat family went in. `waiver_files()` and its neighbours
        SWEEP candidate roots: nine top-level directories times two waiver
        basenames, every miss a candidate that simply is not a board.

        THE DISCRIMINATOR IS THE CARDINALITY OF THE LOOK. A gate that looked at
        EXACTLY ONE path of a basename SELECTED it, and if that one is absent
        while the file exists elsewhere, it selected wrong. A gate that looked
        at several ENUMERATED, and "cannot pick the wrong file because it does
        not pick" is the exemplar's own sentence. So: one look and a miss is
        the finding; several looks is silence.

    `have` and `existed` are PRE-BATTERY, passed in rather than recomputed:
    a file the battery itself created must not be able to turn a real
    mis-resolution into a silent "reached".
    """
    out = []
    looked = _dedupe_paths(opened(tr) + probed(tr))
    by_name = defaultdict(list)
    for p in looked:
        by_name[Path(p).name].append(p)
    reached = {n for n, ps in by_name.items() if any(existed(p) for p in ps)}
    for p in looked:
        ap = Path(p)
        if existed(p) or ap.name in reached or len(by_name[ap.name]) > 1:
            continue
        alts = [str(x) for x in have.get(ap.name, [])]
        if alts:
            out.append(Finding(
                "GG-RESOLVE", short(p),
                f"the gate looked at EXACTLY ONE path of this name — it "
                f"SELECTED rather than enumerated — that path DOES NOT EXIST, "
                f"and {len(alts)} file(s) of that name DO exist under the "
                f"subject root: " + ", ".join(short(a) for a in alts[:4]),
                unresolved=True))
    return out


def gg_shadow(tr, subject, have, real, writes=()):
    """A same-basename file under the subject root NOTHING IN THE RUN opened.

    smc0985-cooksense keeps five rule files at `03_src/rules/` as SYMLINKS into
    `03_src/cooksense/rules/`, and a second, real set at
    `03_src/interposer/rules/`. A gate reading the flat path grades the
    cooksense board and reports on the project. MEASURED: the interposer's
    288-line rule set is opened by NO battery gate that exists.

    `tr` supplies the LEFT half of the claim — *this gate opened this one* —
    and is per-trace, because the finding is reported against a path some gate
    actually read. `real` supplies the RIGHT half — *and nothing in the run
    opened its twin* — and is a REQUIRED FLEET UNION built by `opened_union()`
    over EVERY trace the run collected.

    **`real` IS A PARAMETER AND HAS NO DEFAULT, DELIBERATELY.** It used to be
    rebuilt from `tr` alone inside this function, which made the finding string
    below ("were NEVER opened") false about its own run whenever a gate did its
    reading in a subprocess, and made the verdict a function of the battery's
    PROCESS TOPOLOGY. A default that reconstructed the per-trace set would let
    that regression back in at any call site that forgot the argument; there is
    no such call site to forget it with.
    """
    out = []
    writes = set(writes)
    real = set(real)
    for p in opened(tr):
        ap = Path(p)
        if not ap.exists() or not under(ap, subject) or not _authored(ap) \
                or not _graded_kind(ap) or os.path.realpath(p) in writes:
            continue
        misses = [x for x in have.get(ap.name, []) if _authored(x)
                  and _graded_kind(x)
                  and os.path.realpath(x) not in real]
        if misses:
            out.append(Finding(
                "GG-SHADOW", short(p),
                f"opened this one; {len(misses)} file(s) of the same name "
                f"exist under the subject root and were NEVER opened: "
                + ", ".join(short(str(m)) for m in misses[:4])))
    return out


# ------------------------------------------------------------------- helpers
#: GG-SHADOW is scoped to HAND-WRITTEN SOURCE, and the scope is a judgement
#: worth stating. MEASURED on smc0985-cooksense: unscoped, the predicate also
#: fired on every gate that opened a SEALED `07_releases/**/ORDER_README.md`
#: while a `06_build/verification/` copy existed — and there, reading the sealed
#: one is exactly right (canon M-SHIP: grade the shipped bytes, a
#: reconstruction is only ever a second opinion). The finding was backwards on
#: 18 of 20 hits. A build artefact SHOULD have a source twin; a hand-written
#: rules file should not have an ungraded sibling.
AUTHORED_DIRS = ("03_src", "02_parts", "03_tscircuit", "01_docs")

#: GENERATED SUBTREES INSIDE AUTHORED ONES. `03_tscircuit/` is hand-written
#: source AND the directory tsci builds into: `build/`, `dist/`, `kicad/` and
#: `.tscircuit/` under it are outputs. MEASURED on pluto-rx2-8way-v2: without
#: this, GG-SHADOW fired on `03_tscircuit/build/circuit.json` having a twin —
#: the case the module's own docstring calls backwards, reproduced one
#: directory deeper than the 07_releases scoping that already handles it.
GENERATED_PARTS = ("build", "dist", "kicad", ".tscircuit", "node_modules",
                   "verification", "__pycache__")

#: AND SCOPED AGAIN, TO WHAT A GATE GRADES. GG-SHADOW's question is "did this
#: gate grade the right CONFIG", and a gate grades machine-readable input:
#: rules YAML, part YAML, netlists, boards, and the shell drivers that decide
#: which of those get built (`rebuild_all.sh` is a live finding and stays in).
#:
#: PROSE IS NOT GRADED BY ANYTHING, and round 1 hard-failed on the pipeline's
#: OWN template convention because of it: `01_docs/journal/<topic>.md` and
#: `01_docs/learnings/<topic>.md` are DELIBERATELY the same basename in two
#: directories — that is the layout `skills/pcb-design/templates/` ships — and a
#: gate that reads one of them is not thereby blind to the other. So is the
#: `contracts.md` this repo requires in EVERY folder (~13 per project). A
#: meta-gate that hard-fails the repo's own documented file layout is the
#: `PREC_OWED_CEILING` failure exactly: a ratchet breaking on a CORRECT action,
#: which is how a ratchet gets deleted. So `.md` is out, by extension, and the
#: motivating cooksense case (five rules `.yaml` + a driver `.sh`) is untouched.
GRADED_SUFFIXES = (".yaml", ".yml", ".json", ".csv", ".net", ".sh",
                   ".kicad_pcb", ".kicad_sch", ".kicad_pro", ".tsx")


def _authored(p):
    parts = Path(p).parts
    return any(d in parts for d in AUTHORED_DIRS) \
        and not any(d in parts for d in GENERATED_PARTS)


def _graded_kind(p):
    return str(p).endswith(GRADED_SUFFIXES)


def _dedupe(fs):
    seen, out = set(), []
    for f in fs:
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out


def _dedupe_paths(ps):
    seen, out = set(), []
    for p in ps:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _sandbox(subject, dest, root=None):
    """A COPY of the subject, SITTING WHERE A PROJECT SITS — symlinks PRESERVED.

    Symlinks matter: `smc0985-cooksense` keeps `03_src/rules/` as five symlinks
    into `03_src/cooksense/rules/`, and that layout IS the motivating GG-SHADOW
    finding. A copy that dereferenced them would silently repair the defect the
    layer exists to report.

    THE SANDBOX PRESERVES REPO CONTEXT. MEASURED at round 2: the copy landed at
    `<tmp>/subject`, so a gate resolving a repo-relative path by WALKING UP from
    its project found no repo. `schema_reader_audit.py` does exactly that —
    `repo = Path(project).resolve().parent.parent` — and exited 2 `G-ORPHAN:
    UNGRADED` in the sandbox while exiting 0 in place. **THE SANDBOX WAS AN
    UNDECLARED SECOND OPERATING POINT, AND THE LAYER'S ANSWER DEPENDED ON WHICH
    ONE YOU CHOSE.**

    So the sandbox is a REPO: `<tmp>/repo/projects/<name>` is the copy, and
    every other top-level entry of the real root (`skills/`, `docs/`, `tests/`,
    ...) is SYMLINKED in beside it. Symlinks rather than copies because they
    are free, because the repo half is read-only to the battery by
    construction, and because a copied `skills/` would be a second home for
    every gate under test.

    `projects/` and `.git` are the two exclusions: the first is replaced by the
    subject alone (a battery gate that walked the whole fleet would grade six
    boards it was not pointed at), the second is 400 MB of no interest.

    `cp -a --reflink=auto` first (MEASURED 0.109 s for the 63 MB cooksense tree
    — copy-on-write, so the sandbox is effectively free), falling back to
    `shutil.copytree` where reflinks are unavailable.
    """
    subject = Path(subject).resolve()
    dest = Path(dest)
    if root is not None:
        root = Path(root).resolve()
        repo = dest / "repo"
        (repo / "projects").mkdir(parents=True, exist_ok=True)
        for p in sorted(root.iterdir()):
            if p.name in ("projects", ".git"):
                continue
            link = repo / p.name
            if not link.exists() and not link.is_symlink():
                try:
                    os.symlink(p, link)
                except OSError:                           # pragma: no cover
                    pass
        dest = repo / "projects" / subject.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        cp = subprocess.run(["cp", "-a", "--reflink=auto",
                             str(subject), str(dest)],
                            capture_output=True, timeout=600)
        if cp.returncode == 0 and dest.is_dir():
            return dest.resolve()
    except Exception:
        pass
    shutil.copytree(subject, dest, symlinks=True, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns(".git", "__pycache__"))
    return dest.resolve()


def index_basenames(subject):
    """{basename: [Path]} for the subject tree. TAKEN BEFORE THE BATTERY RUNS.

    Sealed releases are out of scope (canon M-SHIP: a gate reading the shipped
    bytes is doing the right thing, so a `06_build` twin is not a shadow).
    """
    idx = defaultdict(list)
    sp = Path(subject)
    if sp.is_dir():
        for p in sp.rglob("*"):
            if p.is_file() and "07_releases" not in p.parts \
                    and ".git" not in p.parts:
                idx[p.name].append(p)
    return idx


def under(p, root):
    try:
        Path(p).resolve().relative_to(Path(root).resolve())
        return True
    except (ValueError, OSError):
        return False


#: (sandbox root, the real subject it stands for). A finding whose `where` is
#: `/tmp/gg_b0snmh5c/sandbox/repo/projects/<board>/03_src/rules/nets.yaml` is
#: not comparable between two runs of the same board, and a diff taken over
#: such a string is measuring the temp directory. Set once, when the sandbox is
#: built.
_SANDBOX = []


def short(p):
    """EVERY BRANCH RESOLVES, AND THAT IS A MODE-INVARIANCE FIX.

    MEASURED on a scratch copy of smc0985-cooksense: rc, coverage, read count,
    probe count and finding COUNT were identical between the sandbox and
    `--in-place`, and all five GG-SHADOW findings still rendered DIFFERENTLY —
    `03_src/cooksense/rules/nets.yaml` sandboxed against `03_src/rules/nets.yaml`
    in place. Same defect, same file, two names, because the sandbox branch
    called `.resolve()` (dereferencing the `03_src/rules/` symlink) and the
    fall-through branch did not. A `where` string that depends on which mode you
    chose is a `where` string a diff between two runs cannot use, and the
    finding is the dedupe KEY — so the asymmetry was one symlink away from
    reporting the same defect twice in one mode and once in the other.
    """
    try:
        rp = Path(p).resolve()
    except OSError:                                       # pragma: no cover
        return str(p)
    for sb, real in _SANDBOX:
        try:
            return str(Path(real) / rp.relative_to(sb))
        except (ValueError, OSError):
            pass
    try:
        return str(rp.relative_to(ROOT))
    except (ValueError, OSError):
        return str(rp)


def _pre_existed(pre, subj):
    """-> predicate: did this path exist when the battery started?

    For paths under the subject, the answer comes from the PRE-BATTERY
    snapshot, so a file the battery created cannot make a real mis-resolution
    read as reached. For anything outside it, the live filesystem is the only
    source there is, and it is not the battery that writes there.
    """
    def existed(p):
        ap = Path(p)
        if under(ap, subj):
            try:
                return os.path.realpath(p) in pre
            except OSError:                               # pragma: no cover
                return False
        return ap.exists()
    return existed


# ====================================================================== CANARY
CANARY = ROOT / "tests" / "fixtures" / "gg_canary"


def run_canary(tracedir):
    """Run the canary gates and REPORT what was found.

    THIS FUNCTION DOES NOT HOLD THE EXPECTED ANSWER. The expectations are
    hand-written literals in `tests/t1_trace_audit.py`. Merging the two for
    convenience would make this layer another instance of the class it exists
    to kill: a checker that validates its own output (canon M1).

    What this CAN check without knowing the answer is whether it is BLIND: a
    canary that yields NOTHING means observation is off — a dropped
    `PYTHONPATH`, a broken shim, a cleaned env — and that is exit 5.

    **EACH CANARY GATE IS ITS OWN RUN, so `opened_union` is taken over THAT
    gate's traces and no other's.** That is the definition, not a shortcut: the
    union's scope is "the invocation set being graded", which on a `--subject`
    run is the whole derived battery and here is one hand-written gate. Unioning
    ACROSS the canary gates would be a category error with a visible cost —
    `clean_gate.py` enumerates both boards' `power_tree.yaml`, so a cross-gate
    union would make `shadow_gate.py` go silent and delete the positive control.

    Returns `(findings-by-gate, truncated-pids)`. The second half is the
    `truncated` consumer for the canary's own traces: a canary that hit the
    event cap has a PREFIX of its read-set, so its silence would not prove
    observation is off and its findings would not prove it is on.
    """
    subject = CANARY / "subject"
    pre = snapshot(subject)
    have = index_basenames(subject)
    existed = _pre_existed(pre, subject)
    trunc = []
    # EVERY GATE RUN IS A KEY, INCLUDING THE ONES THAT YIELD NOTHING. Keying
    # only the gates that produced a finding would make the printed denominator
    # "2 gate(s)" on a 3-gate canary and would DELETE the negative control from
    # the report — the clean gate's silence is the half that proves the
    # analyser is not simply returning a finding unconditionally.
    found = {g.name: [] for g in sorted(CANARY.glob("*_gate.py"))}
    for gate in sorted(CANARY.glob("*_gate.py")):
        td = Path(tracedir) / gate.stem
        td.mkdir(parents=True, exist_ok=True)
        _rc, _out, traces = run_traced([KPY, gate, subject], td, timeout=60)
        _r, _p, writes = subject_evidence(traces, subject, pre)
        trunc += truncated_traces(traces)
        real = opened_union(traces)
        for tr in traces:
            for f in gg_resolve(tr, subject, have, existed) \
                    + gg_shadow(tr, subject, have, real, writes):
                found[gate.name].append(f.gid)
    return {k: sorted(set(v)) for k, v in found.items()}, sorted(trunc)


# ======================================================================= MAIN
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--subject", default=None,
                    help="the project dir to grade the battery against "
                         "(REQUIRED — this gate has no repo-level predicate)")
    ap.add_argument("--gate", action="append", default=[],
                    help="a script under skills/*/scripts to trace "
                         "(default: the derived battery)")
    ap.add_argument("--canary", action="store_true")
    ap.add_argument("--explain", action="store_true")
    ap.add_argument("--in-place", action="store_true",
                    help="run the battery against the subject ITSELF. Off by "
                         "default: traced gates WRITE (`*.kicad_prl` from "
                         "every pcbnew LoadBoard, `06_build/policy_audit.md`) "
                         "and a grader must not mutate what it grades.")
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)

    root = Path(a.root).resolve()
    if not root.is_dir():
        print(f"USAGE GG: --root {a.root} is not a directory. This is an "
              f"INVOCATION error (exit 2), NOT a graded-nothing verdict "
              f"(exit 3). The gate never started.")
        print(legend())
        return 2
    if a.explain:
        print(legend())
        return 0

    # `--subject` IS MANDATORY, AND THAT IS THE ROUND-3 VACUITY DELETED RATHER
    # THAN DECLARED. The larger layer had three repo-scoped families, so a
    # subject-less run had something to do — and exited 0 while every TRACED
    # predicate had graded nothing, a green compatible with every gate in the
    # fleet being blind on every board. Both banked families are subject-side,
    # so there is no such mode to bound: a run with no subject has nothing to
    # do and says so as an INVOCATION error.
    if not a.subject and not a.canary:
        print("USAGE GG: --subject PROJECT_DIR is REQUIRED. GG-SHADOW and "
              "GG-RESOLVE are both SUBJECT-side predicates; a run without a "
              "board has nothing to grade, and exiting 0 from here would be a "
              "green that says NOTHING about whether any gate can see its "
              "board. This is an INVOCATION error (exit 2).")
        print(legend())
        return 2

    tmp = Path(tempfile.mkdtemp(prefix="gg_"))
    fails = []
    read_n = probe_n = write_n = 0
    battery, observed_gates = [], []
    try:
        # ---- the canary runs FIRST, and its emptiness is exit 5 -------------
        can, can_trunc = (run_canary(tmp / "canary") if CANARY.is_dir()
                          else ({}, []))
        can_n = sum(len(v) for v in can.values())
        print(f"  GG canary: {can_n} finding(s) over {len(can)} hand-written "
              f"gate(s) in tests/fixtures/gg_canary/")
        for g, ids in sorted(can.items()):
            print(f"    {g}: {', '.join(ids) if ids else '(nothing)'}")
        # A BLINDED RUN STOPS HERE, BEFORE THE BATTERY, ON EVERY PATH.
        #
        # Two things were wrong with deciding this at the end. (1) THE EXIT CODE
        # AND ITS SENTENCE DIVERGED: `--canary` returned a bare 5 with NOTHING
        # printed, so the one code meaning "I could not see" was the one code
        # that said nothing, and a blinded run read as a quiet success in any
        # log that keeps stdout and drops the status. Found by tightening this
        # code's own fixture from `expect=""` — which matches anything — to the
        # real verdict string. (2) A `--subject` run traced the WHOLE BATTERY
        # first and printed a read count, a coverage ratio and a findings list
        # that the verdict then called "unearned" — numbers computed with
        # observation off, on the page, above the line that disowns them. If
        # the canary cannot see, nothing below it is worth printing.
        #
        # TRUNCATION IS CHECKED FIRST, AND BEFORE THE EMPTINESS TEST. A canary
        # that hit the event cap may be silent BECAUSE it was truncated, and
        # reporting that as "observation is off" would name the wrong cause.
        if can_trunc:
            print(_trunc_line("canary", can_trunc))
            print(legend())
            return 5
        if not can_n:
            print(f"GG UNOBSERVABLE: the canary produced NOTHING over "
                  f"{len(can)} hand-written gate(s) with KNOWN defects. "
                  f"Observation is off (a dropped PYTHONPATH, a broken shim, a "
                  f"cleaned env), so the battery was NOT run — every number it "
                  f"would have printed is unearned. This is NOT a pass.")
            print(legend())
            return 5
        if a.canary:
            print(f"GG canary OK: {can_n} finding(s) over {len(can)} gate(s) — "
                  f"observation is live. This says NOTHING about any board; "
                  f"pass --subject to grade one.")
            return 0

        subj = Path(a.subject).resolve()
        if not subj.is_dir():
            print(f"USAGE GG: --subject {a.subject} is not a directory "
                  f"(exit 2, the gate never started).")
            return 2
        # A GRADER MUST NOT MUTATE ITS SUBJECT. MEASURED: traced gates wrote
        # `<project>/*.kicad_prl` (every pcbnew LoadBoard does) and
        # `06_build/policy_audit.md` into the very tree they were grading —
        # into SEALED projects, and into projects a live agent owned.
        real_subj = subj
        if not a.in_place:
            subj = _sandbox(subj, tmp / "sandbox", root)
            _SANDBOX.append((subj, short(str(real_subj))))
            print(f"  GG sandbox: the battery runs against a COPY of "
                  f"{short(str(real_subj))} placed at "
                  f"`<tmp>/repo/projects/{real_subj.name}`, with every other "
                  f"top-level repo entry SYMLINKED beside it so a "
                  f"repo-relative walk-up resolves; the subject is not "
                  f"written to. (--in-place to disable.)")

        # BOTH PRE-BATTERY VIEWS ARE TAKEN HERE, before a single gate runs:
        # the SNAPSHOT (what existed) and the BASENAME INDEX (what a shadow
        # could be). Computing the index afterwards would let a file the
        # battery itself created count as an unread twin.
        pre = snapshot(subj)
        have = index_basenames(subj)
        existed = _pre_existed(pre, subj)

        battery = a.gate or default_battery(root)
        print(f"  GG battery: {len(battery)} project-scoped verdict-printing "
              f"gate(s), DERIVED not listed — a file read by a gate you did "
              f"not run is not an unread file")
        allt, per_gate = [], {}
        for gname in battery:
            gp = find_script(root, gname)
            if gp is None:
                fails.append(Finding("GG-RESOLVE", gname,
                                     "no such script under skills/*/scripts",
                                     unresolved=True))
                continue
            td = tmp / "gates" / gname
            td.mkdir(parents=True, exist_ok=True)
            # The gate's own rc and stdout are DELIBERATELY discarded. Grading
            # them was the withdrawn GG-ZERO/GG-OPAQUE families' job; what is
            # banked here asks only what the gate could SEE, and a battery gate
            # exiting nonzero on a board with real defects is that gate working.
            _rc, _out, traces = run_traced([KPY, gp, subj], td)
            if not traces:
                # NOT a finding, and that is a deliberate narrowing from the
                # withdrawn GG-OPAQUE. An absent trace means the OBSERVER
                # failed, not that the gate is blind; the two must not print
                # the same word. It is counted out of the battery denominator
                # instead, where it lowers the coverage this run can claim.
                print(f"    {gname}: ran and left NO TRACE — observation was "
                      f"off for this invocation. Its read-set is UNKNOWN, "
                      f"which is not the same as zero; it is excluded from "
                      f"the OBSERVED battery count below.")
                continue
            observed_gates.append(gname)
            allt += traces
            per_gate[gname] = traces

        # A TRUNCATED READ-SET CARRIES NO GG-SHADOW VERDICT. Same reasoning as
        # the canary branch above and the same exit code: the numbers below
        # would be computed over a PREFIX, and GG-SHADOW's claim is that
        # NOTHING opened a file — precisely the claim a prefix cannot support.
        bat_trunc = truncated_traces(allt)
        if bat_trunc:
            print(_trunc_line("battery", bat_trunc))
            print(legend())
            return 5

        # THE ONE SUBJECT-SIDE READ SET, computed BEFORE any predicate runs,
        # because GG-SHADOW needs the FLEET write-set and a per-trace view
        # cannot have it.
        reads, probes, writes = subject_evidence(allt, subj, pre)
        read_n, probe_n, write_n = len(reads), len(probes), len(writes)
        # AND THE FLEET READ UNION, FOR THE SAME REASON AND ONE STRONGER. The
        # write-set was already fleet-wide here; the READ set that GG-SHADOW
        # tested "never opened" against was not — it was rebuilt inside the
        # predicate from the ONE trace being graded. A gate that dispatches a
        # worker subprocess per board therefore accused itself of not reading
        # what its own children had just read. MEASURED, `tests/fixtures/
        # gg_dispatch/`: RAW EXIT 1 with 2 false findings against RAW EXIT 0
        # for the same read-set in one process.
        real = opened_union(allt)
        for gname, traces in sorted(per_gate.items()):
            for tr in traces:
                fails += gg_resolve(tr, subj, have, existed)
                fails += gg_shadow(tr, subj, have, real, writes)

        # THE COVERAGE DENOMINATOR (canon G-COVER, M-COVER): how much of the
        # derived battery this run actually OBSERVED.
        print(f"  GG coverage: {len(observed_gates)}/{len(battery)} battery "
              f"gate(s) OBSERVED (a gate that left no trace is excluded, "
              f"never counted as clean)")
        print(f"  GG observation gap: {_unobservable_n()} path-level channel(s)"
              f" this tracer KNOWS it cannot see (a non-python child, pcbnew's "
              f"C++ object model, an fd-inherited open). NOT summed into any "
              f"number above.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    fails = _dedupe(fails)
    for f in fails:
        print(f"  {f}")

    # ------------------------------------------------------------ THE NUMBER
    # A RAW COUNT WITH ITS CAVEAT ATTACHED, NOT A CERTIFICATION. The sentence
    # this replaces read "GG-TRACE OK: every family had an OBSERVED population
    # > 0", and it was MEASURED FALSE: two identical genuinely-blind boards
    # differing only by the presence of `06_build/policy_audit.md` — a battery
    # gate's OWN OUTPUT — gave rc 0 and rc 3. Neither guard is an IDENTITY
    # test, so the positive direction is not provable and is not claimed. The
    # caveat travels ON THE PRINTED LINE, because a number quoted without it in
    # a downstream summary is exactly how this defect propagates.
    #
    # AND THE CAVEAT WAS ITSELF DECLARED TOO NARROW. Its first wording scoped
    # the inflation to "a battery gate's OWN OUTPUT", which is the WORST case
    # and not the boundary. MEASURED 2026-07-31 over an otherwise EMPTY subject,
    # three arms, `--subject` unpiped:
    #
    #     06_build/ alone .................................. RAW EXIT 3
    #     + 06_build/policy_audit.md (a gate's own output) .. RAW EXIT 0
    #     + 01_docs/BRIEF.md, THREE LINES OF PROSE .......... RAW EXIT 0
    #
    # `BRIEF.md` is nobody's output and is graded by nothing; it is merely a
    # file two battery gates (`power_topology.py`,
    # `import_provenance_check.py`) happen to open. The umbrella sentences
    # stayed true, so this was an UNDER-STATEMENT rather than a falsehood — but
    # the executable ratchet was pinned to the narrow arm and the wide one was
    # undefended. The consequence is recorded because it changes what the OWED
    # identity test buys: subtracting the battery's declared OUTPUTS closes the
    # `policy_audit.md` arm and DOES NOT CLOSE the `BRIEF.md` arm.
    caveat = (
        "THIS IS A RAW READ COUNT, NOT A PROOF OF OBSERVATION: it counts ANY "
        "PRE-EXISTING FILE ANY GATE HAPPENS TO OPEN. A battery gate's OWN "
        "OUTPUT is the WORST case, not the boundary — MEASURED, three lines of "
        "PROSE in 01_docs/BRIEF.md, which is nobody's output and is graded by "
        "nothing, lift a genuinely-blind board from exit 3 to exit 0 exactly as "
        "06_build/policy_audit.md does. The write-set is a METHOD test and the "
        "pre-run snapshot is an EXISTENCE test; NEITHER IS AN IDENTITY TEST, "
        "and subtracting the battery's declared OUTPUTS would not close the "
        "prose arm because BRIEF.md is not one. Only the ZERO carries a "
        "verdict (exit 3).")
    print(f"  GG read count [SUPERSET]: {read_n} pre-existing file(s) under "
          f"the subject root OPENED FOR READING, {probe_n} path(s) merely "
          f"PROBED (stat family, own channel, never summed), {write_n} "
          f"path(s) WRITTEN and subtracted. {caveat}")

    unresolved = [f for f in fails if f.unresolved]
    shadow_n = sum(1 for f in fails if f.gid == "GG-SHADOW")
    # Exit 5 is NOT reachable from here: a silent canary returns above, before
    # the battery runs. Keeping a second branch for it would be dead code that
    # reads as a live one — which is what round 1's unreachable exits 3 and 4
    # were, and the reason `t_every_exit_code_is_reached_by_a_real_run` exists.
    if not read_n:
        # THE ONE SOUND DIRECTION. Zero reads is a PROOF of no observation:
        # there is no exhaust to mistake for evidence when there is nothing at
        # all. Its converse — nonzero reads means the board was seen — is what
        # INSTANCE 19 falsified, and it is not claimed anywhere above.
        code, line = 3, (
            f"GG GRADED NOTHING: the battery opened ZERO pre-existing files "
            f"under {short(str(Path(a.subject).resolve()))}. "
            f"{probe_n} path(s) were merely STATTED — the WEAK channel, which "
            f"may not carry a verdict. THIS IS NOT A PASS.")
    elif unresolved:
        code, line = 4, (
            f"GG UNRESOLVED: {len(unresolved)} path(s) a gate SELECTED do not "
            f"exist while that basename does exist under the subject root — "
            + "; ".join(sorted({f.where for f in unresolved})[:3])
            + (f" (plus {shadow_n} GG-SHADOW finding(s), listed above)"
               if shadow_n else ""))
    elif fails:
        # THE HEADLINE WORD IS THE EXIT WORD, and that is the fix for a label
        # with no canon row. Both of these lines used to be headed `GG-TRACE`
        # — a check-ID belonging to the WITHDRAWN liveness family, kept alive
        # as the top-line label of every verdict this gate prints, with no
        # canon row behind it and no emitter to justify one. It was invisible
        # to `t_no_canon_gg_row_lacks_an_emitter` because that test scanned
        # `Finding("GG-...")` and a verdict-line label is not a Finding. The
        # verdict is now headed by EXIT[code]'s own first word, so the label
        # and the exit code cannot diverge and neither needs a row of its own.
        code, line = 1, (
            f"GG FINDINGS: {shadow_n} GG-SHADOW finding(s) over "
            f"{len(observed_gates)}/{len(battery)} observed battery gate(s)")
    else:
        code, line = 0, (
            f"GG NO FINDING: no GG-SHADOW or GG-RESOLVE finding over "
            f"{len(observed_gates)}/{len(battery)} observed battery gate(s). "
            f"{read_n} pre-existing file(s) read. {caveat}")

    if a.json:
        Path(a.json).write_text(json.dumps(
            {"verdict": line, "exit": code, "exit_means": EXIT[code],
             # THE SIDECAR CARRIES THE CAVEAT AS A FIELD, not only as prose. A
             # downstream reader (`release_freshness` A-STOCK reads a sidecar
             # exactly like this one) must not be able to lift the number
             # without it. `read_count_proves_observation` is FALSE on every
             # run this gate will ever make until an identity test exists.
             "battery": battery,
             "battery_observed": observed_gates,
             "coverage": f"{len(observed_gates)}/{len(battery)}",
             "read_count": read_n,
             "probe_count": probe_n,
             "write_count": write_n,
             "read_count_proves_observation": False,
             "read_count_caveat": caveat,
             "fails": [{"id": f.gid, "where": f.where, "msg": f.msg,
                        "unresolved": f.unresolved} for f in fails]},
            indent=2) + "\n")

    print(line)
    if code in (2, 3, 4, 5):
        print(legend())
    return code


def _unobservable_n():
    """The size of the DECLARED path-level observation gap, read from the
    tracer's own roster. Loaded BY PATH so it cannot pick up some other
    `shims` on `sys.path`, and never added to any coverage number — a known
    gap summed into an observed count is how `coverage: 35/35` happened."""
    try:
        import importlib.util as ilu
        spec = ilu.spec_from_file_location("gg_shims", GRADELIB / "shims.py")
        m = ilu.module_from_spec(spec)
        spec.loader.exec_module(m)
        return len(m.UNOBSERVABLE)
    except Exception:                                     # pragma: no cover
        return 0


#: A gate that opens a socket is not a source gate, and a coverage layer must
#: not make outbound calls to compute a denominator. MEASURED: exactly two
#: scripts in the tree import a network module (`jlc_stock_check.py`,
#: `shopping_list.py`), and only the second is project-shaped.
NET_IMPORT_RE = re.compile(
    r"^\s*(?:import|from)\s+(?:urllib|requests|http\.client|socket|ssl)\b",
    re.M)
#: argparse positional named `project`/`root`, or a usage line naming one.
PROJECT_ARG_RE = re.compile(
    r"add_argument\(\s*[\"'](?:project|root)[\"']"
    r"|usage:[^\n]*?(?:PROJECT_DIR|<project-root>|<project>)", re.I)

SCRIPT_GLOBS = ["skills/*/scripts/*.py", "scripts/*.py"]


def default_battery(root):
    """THE BATTERY IS DERIVED, AND THE DERIVATION IS THE FIX FOR THE FALSE
    POSITIVES.

    Round 1 hand-listed three gates. GG-SHADOW's `real` set is a FLEET UNION —
    a file counts as opened if ANY TRACED gate opened it — so a hand-listed
    battery makes the union a function of the list, and every file whose only
    reader was left out reads as an unopened twin. That is not a finding about
    the board; it is a finding about the battery, and MEASURED it was 10 of 16
    hard findings across the fleet in round 1. Two of those boards were SEALED,
    and a meta-gate that turns a sealed board red on its own omission is a
    meta-gate that gets waived off; this repo has already lost a check that way.

    **THIS PARAGRAPH DESCRIBED A UNION THE CODE DID NOT BUILD** for the whole
    of the bank's first life. The battery was derived, the write-set was
    fleet-wide, and the READ set GG-SHADOW graded against was rebuilt PER TRACE
    inside the predicate — so the same false-positive mechanism this docstring
    claims to have fixed came back one level down, keyed on PROCESS instead of
    on gate name. `opened_union()` is where the union is now actually taken.

    So the roster is computed, from three properties none of which is a
    hand-maintained list: the script takes a PROJECT DIR, it PRINTS A VERDICT
    (detector IMPORTED from `gate_contract_audit`, never re-implemented — canon
    M1, because a second implementation of "is this a gate" would be the
    two-homes defect inside the gate that polices two homes), and it does not
    import a network module. A new project-scoped gate joins by existing.
    """
    sys.path.insert(0, str(HERE))
    try:
        import gate_contract_audit as gca
    except Exception:                                     # pragma: no cover
        return ["power_topology.py", "electrical_invariants.py",
                "rules_audit.py"]
    out = []
    for g in SCRIPT_GLOBS:
        for p in sorted(Path(root).glob(g)):
            if p.name == Path(__file__).name:
                continue                    # never trace ourselves recursively
            try:
                src = p.read_text(errors="replace")
            except Exception:               # pragma: no cover
                continue
            if NET_IMPORT_RE.search(src):
                continue
            if PROJECT_ARG_RE.search(src) and gca.prints_verdict(src):
                out.append(p.name)
    return sorted(set(out))


def find_script(root, name):
    for g in SCRIPT_GLOBS:
        for p in root.glob(g):
            if p.name == name:
                return p
    return None


if __name__ == "__main__":
    sys.exit(main())
