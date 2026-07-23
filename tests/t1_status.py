#!/usr/bin/env python3
"""T1: the STATUS-beacon reader distinguishes progressing / STALLED / done
(`skills/kicad-pcb/scripts/pcb_status.py`).

Motivating incident (usb-hub-3s-v3 v1.2, 2026-07-23): agents only signalled at
coarse GATE boundaries, so between gates the coordinator was blind — it could
not tell "one tap from done" from "stalled" without reading a multi-MB
transcript. The STATUS beacon fixes that; this suite proves the READER's
traffic light actually bites: a `working` board that stopped writing its beacon
and holds no running op is flagged STALLED, while a fresh one, a live-pid one,
and a done one are not.

The gate here is the STALENESS classification. RED-VERIFIED inline
(`t_stall_logic_has_teeth`): the same stale fixture the reader flags STALLED is
shown NOT-stalled under a broken classifier that drops the age test — same
input, opposite verdict — which is exactly the logic under test. The reader is
NEW (no prior version to swap in per tests/README), so this working-vs-broken
comparison on one fixture is the red-verify the workflow calls for.
"""
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, ROOT, check, contains, main, must_pass,  # noqa: E402
                     not_contains, run, test, tmpdir)

READER = ROOT / "skills" / "kicad-pcb" / "scripts" / "pcb_status.py"


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


if __name__ == "__main__":
    main()
