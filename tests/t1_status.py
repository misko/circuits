#!/usr/bin/env python3
"""T1: the STATUS beacon — the READER's traffic light, and the GATE that makes
the beacon TRUE (`pcb_status.py` + `status_beacon_check.py`, canon M9/M-BEACON).

Motivating incident (usb-hub-3s-v3 v1.2, 2026-07-23): agents only signalled at
coarse GATE boundaries, so between gates the coordinator was blind — it could
not tell "one tap from done" from "stalled" without reading a multi-MB
transcript. The STATUS beacon fixes that; the first half of this suite proves
the READER's traffic light actually bites: a `working` board that stopped
writing its beacon and holds no running op is flagged STALLED, while a fresh
one, a live-pid one, and a done one are not.

The gate there is the STALENESS classification. RED-VERIFIED inline
(`t_stall_logic_has_teeth`): the same stale fixture the reader flags STALLED is
shown NOT-stalled under a broken classifier that drops the age test — same
input, opposite verdict — which is exactly the logic under test. The reader is
NEW (no prior version to swap in per tests/README), so this working-vs-broken
comparison on one fixture is the red-verify the workflow calls for.

SECOND HALF — canon M-BEACON, added 2026-07-27. M9 made the beacon MANDATORY;
nothing made it TRUE, and the reader is happy to render a stale frame. MEASURED
on the fleet the day the gate landed, `status_beacon_check.py` returned
**13 findings across 4 of 6 beacons**:

    crow-mic-pod-v2      4x M-BEACON-DUP + M-BEACON-REL (v1.2 vs live v1.3)
                         + M-BEACON-AGE (updated 2026-07-26 < the v1.3 seal)
    crow-recorder-c-v2   M-BEACON-REL (v1.5 vs live v1.6) + M-BEACON-AGE
    cooksense            M-BEACON-FIELD (no step/op_pid/updated) + M-BEACON-AGE
    usb-hub-3s-v3        M-BEACON-FIELD + M-BEACON-REL (v1.9 vs live v1.10)
                         + M-BEACON-AGE
    interposer, pluto    PASS (the controls — interposer's beacon WAS refreshed
                         at its own seal, same day, and names its live release)

Three of those boards were fixed in the same change; **usb-hub-3s-v3 WAS LEFT
FAILING ON PURPOSE.** Its v1.11 seal was in another agent's hands at that
moment, and whether the seal RITUAL refreshes the beacon is the exact question
this gate exists to answer. Leaving it is the live proof: if v1.11 lands and
usb-hub still fails M-BEACON, the process fix (the beacon-refresh step now in
SKILL.md and the 07_releases seal procedure) was necessary — measured on a real
seal instead of a fixture. This suite therefore does NOT assert usb-hub's
verdict either way; it asserts the gate's PROPERTIES, on the real drifted bytes
in `fixtures/beacons/` (verbatim from commit 98f4c3a, see its PROVENANCE.md) run
against the REAL sealed release directories. No synthetic beacon was written
for the known-bad side: four real ones were wrong.
"""
import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (FIXTURES, KPY, ROOT, check, contains, main,  # noqa: E402
                     must_fail, must_pass, not_contains, run, test, tmpdir)

READER = ROOT / "skills" / "kicad-pcb" / "scripts" / "pcb_status.py"
BEACON_GATE = ROOT / "skills" / "kicad-pcb" / "scripts" / "status_beacon_check.py"
BEACONS = FIXTURES / "beacons"
PROJECTS = ROOT / "projects"


def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def write_beacon(root, project, *, stage, step, measure, state, nxt,
                 op_pid, updated, board=None):
    name = f"STATUS-{board}.md" if board else "STATUS.md"
    p = root / "projects" / project / "01_docs" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        "# STATUS beacon\n<!-- reader parses from here down -->\n"
        f"stage:   {stage}\n"
        f'step:    "{step}"\n'
        f'measure: "{measure}"\n'
        f"state:   {state}\n"
        f'next:    "{nxt}"\n'
        f"op_pid:  {op_pid}\n"
        f"updated: {updated}\n")
    return p


def reader(root, *extra):
    return run([KPY, READER, "--root", str(root), *extra])


def fresh(**kw):
    kw.setdefault("updated", _iso(datetime.now()))
    return kw


# a pid that is (almost) certainly not a running process
DEAD_PID = 999999


# ------------------------------------------------------------ clean cases
@test("pcb_status: a fresh working board with a live op_pid reads as "
      "progressing, never STALLED")
def t_live_pid_progressing():
    d = tmpdir("status_")
    # our own pid is guaranteed alive; a live op overrides any age
    write_beacon(d, "board-live", **fresh(
        stage="routing", step="rebuildE running", measure="route 0/0/0",
        state="working", nxt="DRC gate",
        op_pid=os.getpid(),
        updated=_iso(datetime.now() - timedelta(hours=3))))  # STALE timestamp!
    r = must_pass(reader(d), "reader on live-pid board")
    contains(r.out, "board-live", "names the board")
    contains(r.out, "pid", "shows the live pid")
    not_contains(r.out, "STALLED", "a live op is NEVER stalled, even if old")


@test("pcb_status: a fresh working board with no op_pid reads working, not "
      "STALLED")
def t_fresh_working():
    d = tmpdir("status_")
    write_beacon(d, "board-fresh", **fresh(
        stage="placement", step="nudging C3", measure="audit 1 FAIL",
        state="working", nxt="re-audit", op_pid=""))
    r = must_pass(reader(d), "reader on fresh board")
    contains(r.out, "board-fresh | placement", "stage column present")
    contains(r.out, "working", "state working")
    not_contains(r.out, "STALLED", "fresh board is not stalled")


@test("pcb_status: a done board is terminal, not flagged")
def t_done_terminal():
    d = tmpdir("status_")
    write_beacon(d, "board-done", **fresh(
        stage="seal", step="release cut", measure="DRC 0/0/0; parity 0",
        state="done", nxt="handoff", op_pid=""))
    r = must_pass(reader(d), "reader on done board")
    contains(r.out, "board-done", "names the board")
    contains(r.out, "done", "state done")
    not_contains(r.out, "STALLED", "done is terminal, not stalled")


@test("pcb_status: a blocked board surfaces as BLOCKED (an escalated PUSH), "
      "distinct from STALLED")
def t_blocked_distinct():
    d = tmpdir("status_")
    write_beacon(d, "board-blocked", **fresh(
        stage="parts", step="TPS25740A out of stock", measure="0 in stock",
        state="blocked", nxt="await D-TIER decision", op_pid=""))
    r = must_pass(reader(d), "reader on blocked board")
    contains(r.out, "BLOCKED", "blocked surfaced")
    not_contains(r.out, "STALLED", "blocked (pushed) is not the same as stalled")


@test("pcb_status: multi-board STATUS-<board>.md files each get their own line, "
      "labelled project:board")
def t_multiboard_scoping():
    d = tmpdir("status_")
    write_beacon(d, "cooksense", board="cooksense", **fresh(
        stage="routing", step="grind", measure="route 2/5",
        state="working", nxt="tap", op_pid=""))
    write_beacon(d, "cooksense", board="sensor-pod", **fresh(
        stage="verify", step="twin", measure="0 unadjudicated",
        state="done", nxt="seal", op_pid=""))
    r = must_pass(reader(d), "reader on multi-board project")
    contains(r.out, "cooksense:cooksense", "per-board label 1")
    contains(r.out, "cooksense:sensor-pod", "per-board label 2")


# -------------------------------------------------------- known-bad cases
@test("pcb_status FLAGS a working board that went silent (stale updated, no "
      "live op) as STALLED", kind="known_bad")
def t_stalled_detected():
    d = tmpdir("status_")
    write_beacon(d, "board-stall", stage="routing",
                 step="widen R12.1 escape; rebuildE running",
                 measure="route 0/0/0; 1 fragile tap (R12.1)",
                 state="working", nxt="if R12.1 clears -> DRC gate",
                 op_pid=DEAD_PID,   # a stale pid that is NOT alive
                 updated=_iso(datetime.now() - timedelta(hours=2)))
    # short threshold so 2h is unambiguously stale
    r = must_pass(reader(d, "--stale-secs", "600"), "reader on stalled board")
    contains(r.out, "STALLED", "a silent working board must be flagged STALLED")
    contains(r.out, "board-stall", "names the stalled board")


@test("pcb_status: an unparseable/missing `updated` on a working board is "
      "treated as stale (STALLED), never silently passed", kind="known_bad")
def t_missing_timestamp_is_stale():
    d = tmpdir("status_")
    write_beacon(d, "board-noupdate", stage="routing", step="grind",
                 measure="route 5/5", state="working", nxt="tap",
                 op_pid="", updated="not-a-timestamp")
    r = must_pass(reader(d), "reader on beacon with bad timestamp")
    contains(r.out, "STALLED", "a working board with no valid clock is stale")


@test("pcb_status staleness logic has TEETH — RED-verify: a classifier that "
      "drops the age test calls the SAME stale fixture not-stalled",
      kind="known_bad")
def t_stall_logic_has_teeth():
    """Import the reader's own classify() and show that the stale, no-live-pid,
    working fixture the shipped logic flags STALLED is called NOT stalled once
    the age comparison is removed. Same input, opposite verdict = the age test
    is load-bearing, not decorative."""
    sys.path.insert(0, str(READER.parent))
    import importlib
    mod = importlib.import_module("pcb_status")
    importlib.reload(mod)
    now = datetime.now()
    stale_vals = {
        "state": "working", "op_pid": str(DEAD_PID),
        "updated": _iso(now - timedelta(hours=2)),
    }
    # shipped classifier: STALLED
    col, stalled = mod.classify(stale_vals, now, 600)
    check(stalled and "STALLED" in col,
          f"shipped classify should flag STALLED, got {col!r}")

    # broken classifier: working + no-live-pid but the age test removed ->
    # never stalled. This is the pre-fix behavior the gate must beat.
    def classify_no_age(vals, now, stale_secs):
        state = (vals.get("state") or "").lower()
        if state == "done":
            return "done", False
        if state == "blocked":
            return "BLOCKED", False
        if state == "working":
            if mod.pid_alive(vals.get("op_pid")):
                return "working (live)", False
            return "working", False           # <-- age test dropped
        return "?", False
    bcol, bstalled = classify_no_age(stale_vals, now, 600)
    check(not bstalled and "STALLED" not in bcol,
          f"broken classify should MISS the stall, got {bcol!r}")


# ============================================================ canon M-BEACON
# The gate that makes the beacon TRUE: status_beacon_check.py.
FIXED_BEACON = (
    "# STATUS beacon\n<!-- reader parses from here down -->\n"
    "stage:   seal\n"
    'step:    "v1.3 SEALED and LIVE: '
    '07_releases/crow-mic-pod-v2-v1.3-2026-07-27"\n'
    'measure: "DRC 0/0/0; A-POP PASS 39/26/13"\n'
    "state:   done\n"
    'next:    "order per the v1.3 ORDER_README"\n'
    "op_pid:\n"
    "updated: 2026-07-27T18:39:08\n")


def beacon_project(project, *, fixture=None, body=None, name="STATUS.md"):
    """A scratch project holding ONE beacon. The release side is NOT mocked:
    `beacon_gate` points --releases-root at the real sealed 07_releases/."""
    d = tmpdir("beacon_")
    proj = d / "projects" / project
    (proj / "01_docs").mkdir(parents=True)
    dst = proj / "01_docs" / name
    if fixture:
        shutil.copy(BEACONS / fixture, dst)
    else:
        dst.write_text(body)
    return proj, dst


def beacon_gate(proj, releases_of=None, *extra):
    args = [KPY, BEACON_GATE, str(proj)]
    if releases_of:
        args += ["--releases-root", str(PROJECTS / releases_of / "07_releases")]
    return run(args + list(extra))


# ------------------------------------------------------------ clean cases
@test("M-BEACON: a beacon that names the LIVE release, with all seven fields "
      "written once, PASSES against the real sealed release set")
def t_beacon_agrees_with_the_tree():
    proj, _ = beacon_project("crow-mic-pod-v2", body=FIXED_BEACON)
    r = must_pass(beacon_gate(proj, "crow-mic-pod-v2"), "M-BEACON clean")
    contains(r.out, "M-BEACON PASS", "verdict")
    contains(r.out, "crow-mic-pod-v2-v1.3-2026-07-27", "names the live release")
    contains(r.out, "coverage:", "G-COVER denominator present")


@test("M-BEACON grades EVERY beacon in the fleet and prints an N/M "
      "denominator — no beacon is silently skipped (canon M-COVER)")
def t_beacon_fleet_denominator():
    """Asserts COVERAGE, never the verdict: usb-hub-3s-v3's beacon is
    deliberately left drifted (see the module docstring), so pinning
    PASS/FAIL here would encode the thing under observation."""
    r = run([KPY, BEACON_GATE, "--root", str(ROOT)])   # the real fleet
    n = len(sorted(PROJECTS.glob("*/01_docs/STATUS*.md")))
    check(n >= 5, f"expected the real fleet to carry beacons, found {n}")
    contains(r.out, f"coverage: {n}/{n} beacons graded", "full denominator")
    for b in sorted(PROJECTS.glob("*/01_docs/STATUS*.md")):
        contains(r.out, str(b), f"names the artifact it graded ({b.name})")


# -------------------------------------------------------- known-bad cases
@test("M-BEACON-DUP FAILS the REAL crow-mic-pod-v2 beacon that had two frames "
      "APPENDED into a file the contract says is OVERWRITTEN", kind="known_bad")
def t_beacon_duplicate_keys():
    """The real bytes at 98f4c3a (fixtures/beacons/PROVENANCE.md): v1.1's
    `blocked` seal frame with v1.2's `done` frame appended below it, so
    `stage:`/`step:`/`measure:`/`state:` each appear TWICE. pcb_status.py takes
    the last value and reported `sealed / done` — plausible, and naming a
    release that had already been superseded. MEASURED: 4 M-BEACON-DUP findings
    on this one file, of the 13 the gate returned across the fleet."""
    proj, _ = beacon_project("crow-mic-pod-v2",
                             fixture="crow-mic-pod-v2_STATUS.md")
    r = must_fail(beacon_gate(proj, "crow-mic-pod-v2"), "M-BEACON on dup keys",
                  "M-BEACON-DUP")
    for f in ("stage", "step", "measure", "state"):
        contains(r.out, f"`{f}:` appears 2 times", f"{f} duplicate named")
    contains(r.out, "OVERWRITTEN", "the finding cites the contract rule")


@test("M-BEACON-REL/AGE FAIL the REAL crow-mic-pod-v2 beacon: it claims a "
      "completed seal of v1.2 while v1.3 is live, and predates that seal",
      kind="known_bad")
def t_beacon_names_a_superseded_release():
    """Board attribution and numeric version ordering come from
    release_index.py (canon M-WIDTH, its one home): the LIVE release is the
    newest of THIS board's own series with no SUPERSEDED.md —
    crow-mic-pod-v2-v1.3-2026-07-27, against the beacon's v1.2."""
    proj, _ = beacon_project("crow-mic-pod-v2",
                             fixture="crow-mic-pod-v2_STATUS.md")
    r = must_fail(beacon_gate(proj, "crow-mic-pod-v2"), "M-BEACON on drift",
                  "M-BEACON-REL")
    contains(r.out, "claims a COMPLETED seal of v1.2", "names what it claimed")
    contains(r.out, "crow-mic-pod-v2-v1.3-2026-07-27", "names the live release")
    contains(r.out, "M-BEACON-AGE", "the stale clock is its own finding")
    contains(r.out, "updated: 2026-07-26T12:15:00", "quotes the stale stamp")


@test("M-BEACON-FIELD FAILS the REAL cooksense beacon that carries no "
      "`step:`, `op_pid:` or `updated:` at all — a missing field is a FAIL, "
      "never a skip", kind="known_bad")
def t_beacon_missing_fields():
    """The real bytes at 98f4c3a: 20 non-schema narrative keys and no clock,
    still reading `stage: routed` two sealed releases later. The missing
    `updated:` is what makes M-BEACON-AGE unevaluable, and unevaluable input is
    a FAIL (canon M-COVER) — both findings fire, neither silently."""
    proj, _ = beacon_project("smc0985-cooksense",
                             fixture="smc0985-cooksense_STATUS-cooksense.md",
                             name="STATUS-cooksense.md")
    r = must_fail(beacon_gate(proj, "smc0985-cooksense"),
                  "M-BEACON on a fieldless beacon", "M-BEACON-FIELD")
    for f in ("step", "op_pid", "updated"):
        contains(r.out, f, f"names the missing field {f}")
    contains(r.out, "M-BEACON-AGE", "the unevaluable age is reported, not skipped")
    contains(r.out, "cooksense-v1.4-2026-07-26",
             "the newest seal is the v1.4 of THIS board, not the interposer's "
             "v1.1 and not the same-day v1.3")


@test("M-BEACON-AGE bites ALONE: a beacon naming the live release but written "
      "before that seal is still stale by construction", kind="known_bad")
def t_beacon_age_alone():
    """Broken in exactly ONE way from the passing fixture above: the version
    claim is correct (M-BEACON-REL clean), only the clock is old. Proves AGE is
    load-bearing on its own — it is the property that catches a beacon whose
    prose happens to mention the right number."""
    body = FIXED_BEACON.replace("updated: 2026-07-27T18:39:08",
                                "updated: 2026-07-26T09:00:00")
    proj, _ = beacon_project("crow-mic-pod-v2", body=body)
    r = must_fail(beacon_gate(proj, "crow-mic-pod-v2"), "M-BEACON on age",
                  "M-BEACON-AGE")
    not_contains(r.out, "FAIL M-BEACON-REL",
                 "the version claim is CORRECT here — only the clock is old")
    contains(r.out, "PREDATES the newest seal", "says why")


@test("M-BEACON-AGE is not the mtime ADJACENT PROPERTY — RED-verify: the "
      "drifted beacon's file was touched seconds ago and is still stale",
      kind="known_bad")
def t_beacon_age_is_not_file_mtime():
    """'The beacon file was modified recently' is ADJACENT to 'the beacon
    agrees with the tree' (canon M-IMPORT's co-resident corollary), and it is
    the cheap implementation someone would reach for. Same input, opposite
    verdict: the fixture copy's mtime is NOW, so an mtime check calls it fresh,
    while M-BEACON-AGE reads the value the READER reads and calls it stale.
    Neutering the gate this way is the red-verify tests/README asks for on a
    NEW checker with no pre-fix version to swap in."""
    import time
    proj, dst = beacon_project("crow-mic-pod-v2",
                               fixture="crow-mic-pod-v2_STATUS.md")
    mtime_age = time.time() - dst.stat().st_mtime
    check(mtime_age < 300,
          f"fixture mtime should be fresh, is {mtime_age:.0f}s old")
    # the broken (adjacent) check: fresh by mtime => "not stale". No finding.
    check(mtime_age < 900, "mtime check would report this beacon FRESH")
    # the shipped check, on the same bytes:
    r = must_fail(beacon_gate(proj, "crow-mic-pod-v2"), "M-BEACON on mtime-fresh"
                  " but content-stale beacon", "M-BEACON-AGE")
    contains(r.out, "stale by construction", "grades the CONTENT, not the file")


@test("M-BEACON refuses a zero denominator: a tree with no beacon at all is a "
      "FAIL naming where it looked, never a green run over nothing",
      kind="known_bad")
def t_beacon_zero_denominator():
    d = tmpdir("beacon_")
    (d / "projects" / "empty-board" / "01_docs").mkdir(parents=True)
    r = must_fail(run([KPY, BEACON_GATE, str(d / "projects" / "empty-board")]),
                  "M-BEACON on a beaconless tree", "no STATUS beacon found")
    contains(r.out, "M-COVER", "cites the canon rule it is obeying")


if __name__ == "__main__":
    sys.exit(main())
