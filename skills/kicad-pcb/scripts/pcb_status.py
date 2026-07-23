#!/usr/bin/env python3
"""STATUS-beacon reader — the coordinator's monitor for in-flight boards.

Agents signal at coarse GATE boundaries (schematic / routing / seal). Between
gates the coordinator was blind: it could not tell "one tap from done" from
"stalled" without reading a multi-MB transcript (incident: usb-hub-3s-v3 v1.2,
2026-07-23). The STATUS beacon closes that gap — each board OVERWRITES a tiny
`01_docs/STATUS*.md` at every transition (schema in that file / the 01_docs
contract). This reader scans them and prints ONE line per board:

    <board> | <stage> | <step> / <measure> | <state> | <age>

The state column is DERIVED, not just echoed:
  - `working` + fresh `updated` + a LIVE `op_pid`   -> progressing (coordinator
    POLLS, never interrupts)
  - `working` + `updated` older than --stale-secs + NO live op_pid -> STALLED
    (a working agent that stopped writing its beacon and holds no running op)
  - `blocked` -> the agent PUSHED a decision / D-BACK wall up; coordinator acts
  - `done`    -> terminal for this stage

A live op_pid overrides staleness: a long route legitimately runs for many
minutes while the beacon sits, so a running pid means progressing regardless of
age. That is why the beacon is rewritten IMMEDIATELY BEFORE a long op (recording
op_pid) and AFTER it (clearing op_pid, updating measure) — see SKILL.md.

No pcbnew needed; runs on /usr/bin/python3 (or any python3).

usage:
  pcb_status.py [--root DIR] [--stale-secs N] [--no-header]
Default root is the repo this script lives in; scans projects/*/01_docs/STATUS*.md.
"""
import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

FIELDS = ("stage", "step", "measure", "state", "next", "op_pid", "updated")
_FIELD_RE = re.compile(r"^(%s):\s*(.*)$" % "|".join(FIELDS))
DEFAULT_STALE_SECS = 900  # 15 min: a working agent silent this long with no
                          # running op has stopped writing its beacon.


def parse_beacon(path):
    """Last occurrence of each known field wins (fenced values beat any prose
    mention above them). Surrounding quotes stripped."""
    vals = {}
    for line in path.read_text(errors="replace").splitlines():
        m = _FIELD_RE.match(line)
        if m:
            v = m.group(2).strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                v = v[1:-1]
            vals[m.group(1)] = v.strip()
    return vals


def board_label(path):
    """`STATUS-<board>.md` -> project:<board>; bare `STATUS.md` -> project.
    project = the dir that OWNS 01_docs (…/projects/<project>/01_docs/STATUS…)."""
    project = path.parent.parent.name
    m = re.match(r"STATUS-(.+)\.md$", path.name)
    return f"{project}:{m.group(1)}" if m else project


def pid_alive(pid_str):
    if not pid_str:
        return False
    try:
        pid = int(pid_str)
    except ValueError:
        return False
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists, owned by someone else — still alive
    return True


def age_seconds(updated, now):
    if not updated:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            return (now - datetime.strptime(updated, fmt)).total_seconds()
        except ValueError:
            continue
    return None


def humanize(sec):
    if sec is None:
        return "?"
    sec = int(sec)
    if sec < 0:
        return "0s"
    if sec < 60:
        return f"{sec}s"
    if sec < 3600:
        return f"{sec // 60}m"
    if sec < 86400:
        return f"{sec // 3600}h{(sec % 3600) // 60:02d}m"
    return f"{sec // 86400}d{(sec % 86400) // 3600:02d}h"


def classify(vals, now, stale_secs):
    """-> (state_column, is_stalled). The one place the traffic light lives."""
    state = (vals.get("state") or "").lower()
    live = pid_alive(vals.get("op_pid"))
    age = age_seconds(vals.get("updated"), now)
    if state == "done":
        return "done", False
    if state == "blocked":
        return "BLOCKED", False
    if state == "working":
        if live:
            return f"working (pid {vals.get('op_pid')} live)", False
        # STALLED := working + no live op + updated older than the threshold
        # (a missing/unparseable timestamp counts as stale — conservative).
        if age is None or age > stale_secs:
            return "STALLED", True
        return "working", False
    return (vals.get("state") or "?") + " (?)", False


def collect(root, now, stale_secs):
    rows = []
    for path in sorted(root.glob("projects/*/01_docs/STATUS*.md")):
        vals = parse_beacon(path)
        col, stalled = classify(vals, now, stale_secs)
        rows.append({
            "label": board_label(path),
            "stage": vals.get("stage", "?"),
            "step": vals.get("step", ""),
            "measure": vals.get("measure", ""),
            "state_col": col,
            "stalled": stalled,
            "age": humanize(age_seconds(vals.get("updated"), now)),
        })
    return rows


def render(rows, header=True):
    out = []
    if header:
        out.append("# board | stage | step / measure | state | age")
    for r in rows:
        sm = r["step"]
        if r["measure"]:
            sm = f"{sm} / {r['measure']}" if sm else r["measure"]
        out.append(f"{r['label']} | {r['stage']} | {sm} | "
                   f"{r['state_col']} | {r['age']}")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[3]),
                    help="repo root containing projects/ (default: this repo)")
    ap.add_argument("--stale-secs", type=int, default=DEFAULT_STALE_SECS,
                    help=f"working+idle older than this = STALLED "
                         f"(default {DEFAULT_STALE_SECS})")
    ap.add_argument("--no-header", action="store_true")
    args = ap.parse_args(argv)

    rows = collect(Path(args.root), datetime.now(), args.stale_secs)
    if not rows:
        print("# no STATUS beacons found under "
              f"{args.root}/projects/*/01_docs/STATUS*.md")
        return 0
    print(render(rows, header=not args.no_header))
    return 0


if __name__ == "__main__":
    sys.exit(main())
