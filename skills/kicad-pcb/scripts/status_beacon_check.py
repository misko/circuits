#!/usr/bin/env python3
"""status_beacon_check.py — canon M-BEACON: the beacon must agree with the TREE.

    status_beacon_check.py [PROJECT_DIR ...] [--root REPO] [--json OUT]

M9 makes the journal + beacon MANDATORY; nothing made them TRUE. Measured
2026-07-27, every beacon in the fleet named the wrong release:

    board                     beacon named        actually live
    crow-mic-pod-v2           v1.2-2026-07-26     v1.3-2026-07-27
    crow-recorder-central-v2  v1.5                v1.6-2026-07-27
    usb-hub-3s-v3             v1.9                v1.10 (v1.11 in flight)
    smc0985-cooksense         v1.3 (stage routed) cooksense-v1.4

and `crow-mic-pod-v2/01_docs/STATUS.md` carried `stage:`/`step:`/`measure:`/
`state:` TWICE — v1.1's blocked seal frame with v1.2's done frame APPENDED
below it, in a file the contract says is OVERWRITTEN. `pcb_status.py` takes
the LAST value of each field, so it reported `sealed / done`: plausible,
internally consistent, and naming a superseded release. That is a SILENT WRONG
ANSWER, which is strictly worse than a blank.

WHY IT DRIFTED — the SECOND-HOME diagnosis. Which release is live is not an
opinion: it is a property of the tree (`07_releases/`, the newest of THIS
board's series, the one with no `SUPERSEDED.md`). A beacon that restates it has
made a SECOND HOME for a fact that already has an authoritative one, and a
second home drifts — the same shape as `lcsc_mpn_map.csv` restating the MPN
that `02_parts/` already held, and cooksense v1.1's 13 CPL rows contradicting
its own MANIFEST. The preferred fix is always to DELETE the restatement. It
cannot be deleted here: `step:`/`measure:`/`next:` are NARRATIVE prose written
for a human coordinator, and a human reading "v1.2 SEALED" needs the version in
the sentence. So the restatement stays and is MACHINE-CHECKED against its
authoritative home — the second-best answer, taken deliberately. What the
beacon may NOT do is be the ONLY place the fact lives, and it never is.

THE FOUR PROPERTIES. Each names an artifact and can fail on its own:

  M-BEACON-DUP    no required field appears twice. The contract says the file
                  is OVERWRITTEN; a second occurrence is an APPEND, and the
                  reader's last-wins rule then reports a frame nobody wrote.
  M-BEACON-FIELD  all seven reader fields are present. A missing one is not a
                  cosmetic gap: it is what makes M-BEACON-AGE UNEVALUABLE, and
                  unevaluable input is a FAIL, never a skip (canon M-COVER).
  M-BEACON-REL    a beacon claiming a COMPLETED seal must name the LIVE
                  release. Release identity, board attribution and numeric
                  version ordering come from `jlcpcb-fab/scripts/release_index`,
                  their ONE home (canon M-WIDTH) — re-deriving `v1.10 > v1.9`
                  or the cooksense/interposer board split here would be a
                  fourth implementation of the defect that shipped three times.
  M-BEACON-AGE    `updated:` may not predate the newest seal of that board.
                  The general rule: a beacon older than the last release is
                  stale BY CONSTRUCTION, whatever it says. This is the one that
                  catches all four boards above.

SCOPE DECISIONS, stated rather than implied:

  * The seal CLAIM is read from `stage:` and `step:` only. `measure:` and
    `next:` are narrative and legitimately name OTHER releases — a freshness
    diff against the predecessor, a planned successor, a sibling board's seal
    (`interposer`'s beacon cites `cooksense-v1.4` correctly). Grading prose
    that is allowed to mention other releases would be the adjacent-property
    error: the property is WHICH RELEASE THIS BEACON CLAIMS, not which
    releases it mentions.
  * A version token needs a DOT (`v1.9`, not `v3`). Board names in this fleet
    end in `-v2`/`-v3`, and the release versions all carry a minor.
  * A token carrying ANOTHER board's prefix is attributed to that board and
    ignored here — the cooksense/interposer split, resolved the same way
    `release_index` resolves it.
  * `M-BEACON-AGE` compares at DAY granularity, because a release directory
    carries a DATE and no time. A beacon rewritten earlier on the seal DAY is
    not caught by AGE; it is caught by REL, which reads the version.
  * Whether a project OWES a beacon is a LIFECYCLE question this gate does not
    answer (four delivered/archived boards in this fleet never had one). It
    grades the beacons that EXIST, and prints the projects that have none BY
    NAME so the gap is visible rather than silent.

M1 (checker and checked share no method): the checked artifact is a
hand-written `STATUS*.md`; the tree side comes from `release_index`, which
nothing that writes a beacon touches. The `updated:` timestamp is parsed with
`pcb_status.age_seconds` DELIBERATELY — the property is "the value THE READER
CONSUMES is stale", so it must be read exactly as the reader reads it.
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pcb_status import FIELDS, age_seconds          # noqa: E402

# release naming/ordering has ONE home in this repo (canon M-WIDTH)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]
                       / "jlcpcb-fab" / "scripts"))
import release_index as _relidx                     # noqa: E402

DUP, FIELD, REL, AGE = ("M-BEACON-DUP", "M-BEACON-FIELD",
                        "M-BEACON-REL", "M-BEACON-AGE")

_FIELD_RE = re.compile(r"^(%s):\s*(.*)$" % "|".join(FIELDS))

#: A release version named in prose. The board prefix is optional and stops at
#: any non-name character (so `07_releases/cooksense-v1.4` yields `cooksense`).
#: The version REQUIRES a minor component: `usb-hub-3s-v3` and
#: `crow-mic-pod-v2` are BOARD names, not releases.
_VER_RE = re.compile(
    r"(?<![\w.])(?:(?P<board>[A-Za-z][A-Za-z0-9_]*(?:-[A-Za-z0-9_]+)*)-)?"
    r"v(?P<ver>\d+(?:\.\d+)+)(?![\d.])")

#: `<...>-YYYY-MM-DD` — the seal DATE carried by every release directory name.
_DATE_RE = re.compile(r"-(\d{4})-(\d{2})-(\d{2})$")

#: A beacon claims a COMPLETED seal. `stage: seal` alone is the seal STAGE
#: (staging is in progress and the live release is still the predecessor), so
#: it counts only once `state:` says the stage's gate is green.
_SEALED_RE = re.compile(r"sealed", re.I)


def strip_quotes(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1]
    return v.strip()


def occurrences(text):
    """field -> [(lineno, value), ...] — EVERY occurrence, not just the last.

    `pcb_status.parse_beacon` keeps the last value (that is the reader's
    contract). This gate must see the duplicates the reader hides, so it walks
    the lines itself and imports only the FIELD VOCABULARY from the reader —
    one home for the field names, two different readings of them.
    """
    out = {}
    for i, line in enumerate(text.splitlines(), 1):
        m = _FIELD_RE.match(line)
        if m:
            out.setdefault(m.group(1), []).append((i, strip_quotes(m.group(2))))
    return out


def beacon_board(path):
    """`STATUS-<board>.md` -> '<board>'; bare `STATUS.md` -> None."""
    m = re.match(r"STATUS-(.+)\.md$", path.name)
    return m.group(1) if m else None


def claimed_versions(text, board_slug):
    """Release versions in `text` attributable to THIS board.

    A bare `v1.9` is this board's; a prefixed `cooksense-v1.4` is this board's
    only when the prefix slugs to this board. Anything else belongs to a
    sibling board and is not this beacon's claim.
    """
    out = []
    for m in _VER_RE.finditer(text or ""):
        pfx = _relidx.slug(m.group("board") or "")
        if pfx and pfx != board_slug:
            continue
        out.append(tuple(int(x) for x in m.group("ver").split(".")))
    return out


def seal_date(release_dir):
    m = _DATE_RE.search(release_dir.name)
    if not m:
        return None
    try:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def grade_beacon(path, project, rel_root=None):
    """-> (row, findings). One beacon, four properties, no early return."""
    board = beacon_board(path)
    row = {"beacon": str(path), "project": project.name, "board": board,
           "live": None, "seal_claimed": False, "has_releases": False}
    fails = []

    try:
        text = path.read_text(errors="replace")
    except OSError as e:                              # unreadable is a FAIL
        return row, [f"{FIELD} {path}: cannot be read ({e}) — an "
                     f"unreadable beacon is a FAIL, never a skip"]

    occ = occurrences(text)

    # ---- M-BEACON-DUP: the file is OVERWRITTEN, so one occurrence each
    for f in FIELDS:
        if len(occ.get(f, [])) > 1:
            lines = ", ".join(str(n) for n, _ in occ[f])
            fails.append(
                f"{DUP} {path}: `{f}:` appears {len(occ[f])} times "
                f"(lines {lines}) — the contract says this file is OVERWRITTEN, "
                f"so a second occurrence is an APPEND and the reader's "
                f"last-wins rule reports a frame nobody wrote")

    # ---- M-BEACON-FIELD: all seven the reader consumes
    missing = [f for f in FIELDS if not occ.get(f)]
    if missing:
        fails.append(
            f"{FIELD} {path}: missing required field(s) {', '.join(missing)} — "
            f"the 01_docs contract requires all seven, and a missing "
            f"`updated:` makes {AGE} unevaluable (canon M-COVER: unevaluable "
            f"input is a FAIL, never a skip)")

    last = {f: occ[f][-1][1] for f in occ}
    stage, state = last.get("stage", ""), last.get("state", "")
    row["seal_claimed"] = bool(_SEALED_RE.search(stage)
                               or _SEALED_RE.search(state)
                               or (stage.strip().lower() == "seal"
                                   and state.strip().lower() == "done"))

    # ---- the tree side: THIS board's release series (one home: release_index)
    try:
        rels = _relidx.releases_for_board(project, board, rel_root)
    except _relidx.ReleaseSetError as e:
        return row, fails + [
            f"{REL} {path}: this board's release series cannot be resolved — "
            f"{e}"]
    row["has_releases"] = bool(rels)

    if rels:
        live = rels[-1]
        row["live"] = live.name
        if (live / "SUPERSEDED.md").exists():
            fails.append(
                f"{REL} {path}: the newest release of this board "
                f"({live.name}) carries SUPERSEDED.md, so the tree names NO "
                f"live release for the beacon to agree with")

        # ---- M-BEACON-REL: a completed seal must name the LIVE release
        if row["seal_claimed"]:
            claim_text = f"{stage}\n{last.get('step', '')}"
            named = claimed_versions(claim_text, _relidx.slug(board or ""))
            live_ver = _relidx.parse_release_name(live.name)[1]
            if not named:
                fails.append(
                    f"{REL} {path}: claims a COMPLETED seal "
                    f"(stage={stage!r} state={state!r}) but `stage:`/`step:` "
                    f"name no release version at all — the live release is "
                    f"{live.name}")
            elif max(named) != live_ver:
                got = "v" + ".".join(str(x) for x in max(named))
                fails.append(
                    f"{REL} {path}: claims a COMPLETED seal of {got} but the "
                    f"LIVE release of board {board or project.name!s} is "
                    f"{live.name} (newest of its own series, no "
                    f"SUPERSEDED.md) — the beacon names a release the tree "
                    f"does not agree with")

        # ---- M-BEACON-AGE: not older than the newest seal
        dates = {d.name: seal_date(d) for d in rels}
        undated = sorted(n for n, dt in dates.items() if dt is None)
        if undated:
            fails.append(
                f"{AGE} {path}: release director(ies) {', '.join(undated)} "
                f"carry no parseable -YYYY-MM-DD seal date, so the newest "
                f"seal cannot be dated — refused rather than guessed")
        else:
            # ties break to the HIGHER VERSION: cooksense v1.3 and v1.4 were
            # both sealed 2026-07-26, and the newest seal is v1.4.
            newest_name, newest = max(
                dates.items(),
                key=lambda kv: (kv[1], _relidx.parse_release_name(kv[0])[1]))
            upd = last.get("updated", "")
            age = age_seconds(upd, newest)
            if age is None:
                fails.append(
                    f"{AGE} {path}: `updated:` is {upd!r}, which is not an "
                    f"ISO-8601 timestamp the reader can parse — a beacon with "
                    f"no clock cannot be shown fresher than the "
                    f"{newest_name} seal")
            elif age > 0:
                fails.append(
                    f"{AGE} {path}: `updated: {upd}` PREDATES the newest seal "
                    f"of this board ({newest_name}, {newest.date()}) — a "
                    f"beacon older than the last release is stale by "
                    f"construction, whatever it says")

    return row, fails


def audit(projects, rel_root=None):
    rows, fails, no_beacon = [], [], []
    for proj in projects:
        beacons = sorted(Path(proj).glob("01_docs/STATUS*.md"))
        if not beacons:
            no_beacon.append(Path(proj).name)
            continue
        for b in beacons:
            row, f = grade_beacon(b, Path(proj), rel_root)
            rows.append(row)
            fails.extend(f)
    return {"beacons": rows, "fails": fails, "no_beacon": sorted(no_beacon),
            "projects": [str(p) for p in projects]}


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", nargs="*",
                    help="project dir(s); default every projects/* under --root")
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[3]),
                    help="repo root containing projects/ (default: this repo)")
    ap.add_argument("--releases-root", default=None,
                    help="override 07_releases/ (tests)")
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)

    if a.project:
        projects = [Path(p) for p in a.project]
    else:
        projects = sorted(p for p in (Path(a.root) / "projects").glob("*")
                          if p.is_dir())

    r = audit(projects, a.releases_root)
    if a.json:
        Path(a.json).write_text(json.dumps(r, indent=2) + "\n")

    rows = r["beacons"]
    for row in rows:
        live = row["live"] or "no release series"
        print(f"  graded: {row['beacon']} "
              f"(board {row['board'] or row['project']}, live: {live})")
    for f in r["fails"]:
        print(f"  FAIL {f}")

    sealed = sum(1 for x in rows if x["seal_claimed"])
    withrel = sum(1 for x in rows if x["has_releases"])
    n = len(rows)
    print(f"  coverage: {n}/{n} beacons graded on {DUP} + {FIELD}; "
          f"{sealed}/{n} claim a completed seal and are graded on {REL}; "
          f"{withrel}/{n} have a release series and are graded on {AGE}")
    if r["no_beacon"]:
        print(f"  no beacon (not graded here — lifecycle, see docstring): "
              f"{', '.join(r['no_beacon'])}")

    if not rows:
        print(f"M-BEACON FAIL: no STATUS beacon found under "
              f"{', '.join(r['projects']) or a.root} — a zero denominator is a "
              f"FAIL, not a pass (canon M-COVER)")
        return 2
    bad = len({f.split()[1] for f in r["fails"]})
    if r["fails"]:
        print(f"M-BEACON FAIL: {len(r['fails'])} finding(s) across {bad} of "
              f"{n} beacon(s)")
        return 1
    print(f"M-BEACON PASS: {n} beacon(s) agree with the tree")
    return 0


if __name__ == "__main__":
    sys.exit(main())
