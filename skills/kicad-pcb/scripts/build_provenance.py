#!/usr/bin/env python3
"""M-FRESH — the artifact a gate grades must be the one the build just wrote.

Usage:
    build_provenance.py stamp  PROJECT_DIR --board B --tsx T
    build_provenance.py verify PROJECT_DIR --board B --tsx T --artifact PATH
    build_provenance.py audit  PROJECT_DIR          # after the fact, any time
    build_provenance.py audit  --root REPO          # the whole fleet

WHY THIS EXISTS (pluto-rx2-8way-v2, 2026-07-30). `tsci build` writes
`03_tscircuit/dist/src/<TSX>/circuit.json`. The skill-owned `rebuild_all.sh`
template handed the converter `03_tscircuit/build/circuit.json` — a path
`tsci build` NEVER WRITES. The converter therefore consumed whatever
`build/circuit.json` happened to hold from some earlier run, and **every gate
downstream went green against superseded content**: TSX-PRE, S-NETMERGE, E-INV,
E-ADR, E-TOPO, E-MARGIN, S-COUNT, E-NETREF and M-BOM all PASSED on an entire
obsolete pad-numbering scheme. Nothing in the pipeline noticed; it was caught by
a by-hand netlist read.

**Nothing was wrong with any checker.** They graded exactly what they were
handed. That is the whole point of this file: a converter that reads a path the
builder never writes produces SILENT STALENESS, and silent staleness makes every
downstream gate a liar without making any of them incorrect. A path fix alone
is not a fix, because the next mis-wiring is free. The pipeline has to ASSERT
that the artifact it grades is the one it just built.

The same board carried the second half of the shape: its `rebuild_all.sh` still
read `BOARD=power3s` / `TSX=power3s` — the TEMPLATE's own knobs — from
commission through four commits, meaning the full driver HAD NEVER RUN on that
board while its stage gates reported green individually. A driver that was never
run for this board must not be indistinguishable from one that ran and passed.

FINDINGS
  F-KNOB   the driver's BOARD=/TSX= knobs do not resolve to files in THIS
           project (the `BOARD=power3s` shape). Graded at `stamp`, i.e. BEFORE
           `tsci build` — the earliest point at which it is knowable.
  F-VOID   the builder produced no artifact at all: `tsci build` exited 0 (or
           was skipped) and wrote nothing this run.
  F-STALE  the producer predates this run's build step, or the sources moved
           since the record was written. A stale artifact is an attack on canon
           M3: "regenerable from 03_src/ + 03_tscircuit/" is worthless if the
           regeneration silently no-ops.
  F-PATH   the artifact the converter is handed is not byte-identical to the one
           the builder wrote. THIS is the pluto-rx2-8way-v2 defect.
  F-NORUN  no verified provenance record for this board — the driver has never
           completed a run here.

WHY THE EQUALITY IS CONTENT-BASED AND CROSS-FILE (the anti-defeat argument).
mtime alone is defeatable by `touch`, and `touch` is exactly what a rerun that
"happens to touch the file" does. So F-PATH compares sha256(converter input)
against sha256(the file this checker LOCATED ITSELF under `dist/`) — a hash
equality between two independently-resolved paths, which no timestamp operation
can forge. mtime-vs-run-start is the SECOND condition (F-STALE), never the only
one.

CANON M1 (checker and checked share no method). The thing graded is
`circuit.json`, produced by `tsci build` (a foreign toolchain) and copied by the
driver. This checker does not build it, does not copy it, and does not take the
driver's word for where the builder put it — it GLOBS `03_tscircuit/dist/` for
the producer and compares against the path the converter was handed. If it
merely read a "fresh" flag written by the build step it would prove nothing.

DECLARED SCOPE LIMIT. The source fingerprint proves the sources have not MOVED
since the recorded build; it cannot prove the artifact is what a rebuild from
those sources WOULD produce (only re-running tsci proves that, and tsci is
non-deterministic in its .kicad_sch churn). What it does buy is the M3 half that
matters: a board whose `03_tscircuit/src/` has changed since its last verified
build is reported STALE rather than assumed current.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
import uuid
from pathlib import Path

RECORD = "06_build/build_provenance.json"   # 06_build/*.json — disposable by contract

#: files whose bytes decide what `tsci build` emits into circuit.json.
SRC_GLOBS = ("src/**/*.tsx", "src/**/*.ts", "package.json", "tsconfig.json")

#: template sentinel knobs. A board still carrying these has never run the
#: driver — pluto-rx2-8way-v2 carried them from commission through 4 commits.
TEMPLATE_KNOBS = {"power3s", "cook_loadcell", "<board>", "BOARD", "TSX"}


# --------------------------------------------------------------- primitives
def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def source_fingerprint(tsdir):
    """sha256 over the sorted (relpath, sha256) of every tscircuit source file.

    Returns (hexdigest, [relpath, ...]). The file LIST is returned so the
    coverage denominator is a real count and not a claim.
    """
    seen = {}
    for g in SRC_GLOBS:
        for p in sorted(tsdir.glob(g)):
            if p.is_file():
                seen[str(p.relative_to(tsdir))] = sha256_file(p)
    h = hashlib.sha256()
    for rel in sorted(seen):
        h.update(rel.encode())
        h.update(b"\0")
        h.update(seen[rel].encode())
        h.update(b"\n")
    return h.hexdigest(), sorted(seen)


def find_producer(tsdir, tsx):
    """Locate what the BUILDER wrote, without asking the driver.

    `tsci build src/<TSX>.tsx` emits `dist/src/<TSX>/circuit.json`. Older/other
    tsci layouts have used `dist/circuit.json`. We glob rather than hardcode so
    a tsci layout change surfaces as F-VOID (loud) and never as a silent pass.
    """
    preferred = tsdir / "dist" / "src" / tsx / "circuit.json"
    if preferred.is_file():
        return preferred
    cands = [p for p in sorted(tsdir.glob("dist/**/circuit.json")) if p.is_file()]
    if len(cands) == 1:
        return cands[0]
    for p in cands:                       # ambiguous: prefer one naming the tsx
        if tsx in p.parts:
            return p
    return cands[0] if cands else None


def read_driver_knobs(project):
    """Extract BOARD=/TSX= from 03_src/rebuild_all.sh, following a dispatcher.

    cooksense (ADR-0007, >1 fabricated board) makes 03_src/rebuild_all.sh a thin
    `exec bash "$HERE/<board>/rebuild_all.sh"` dispatcher, so the knobs live one
    level down. Returns (board, tsx, driver_path) with None for anything absent.
    """
    drv = project / "03_src" / "rebuild_all.sh"
    if not drv.is_file():
        return None, None, None
    for _ in range(4):                      # bounded dispatcher chase
        txt = drv.read_text(errors="replace")
        m = re.search(r'exec\s+bash\s+"?\$\{?HERE\}?/([^"\s]+rebuild_all\.sh)', txt)
        if not m:
            break
        nxt = (drv.parent / m.group(1)).resolve()
        if not nxt.is_file():
            break
        drv = nxt
    txt = drv.read_text(errors="replace")
    b = re.search(r'^BOARD=(\S+)', txt, re.M)
    t = re.search(r'^TSX=(\S+)', txt, re.M)
    return (b.group(1) if b else None), (t.group(1) if t else None), drv


def board_name_candidates(project):
    """Names this project could legitimately call its board, read from the tree.

    Independent of the driver (that is the thing being graded): the floorplan's
    own `project.name`, plus the stems of any KiCad artifact already on disk.
    """
    out = set()
    fp = project / "03_src" / "floorplan.yaml"
    if fp.is_file():
        m = re.search(r'^project:\s*$\s*(?:^\s+.*$\s*)*?^\s+name:\s*(\S+)',
                      fp.read_text(errors="replace"), re.M)
        if m:
            out.add(m.group(1).strip('"\''))
    for ext in ("*.kicad_pcb", "*.kicad_sch"):
        for p in (project / "04_kicad").glob(ext):
            out.add(p.stem)
    return out


def grade_knobs(project, board, tsx, driver):
    """F-KNOB: do the driver's knobs resolve to THIS project? -> [failure, ...]

    BOARD and TSX are graded INDEPENDENTLY. A driver can carry one and not the
    other (several fleet boards set BOARD= and drive the schematic through
    `gen_tscircuit.sh`), and an unresolvable BOARD= is a defect on its own —
    returning early on a missing TSX would have hidden it.
    """
    fails = []
    tsdir = project / "03_tscircuit"
    cands = board_name_candidates(project)
    if board is not None and cands and board not in cands:
        fails.append(
            f"F-KNOB {driver}: BOARD={board} is not a name this project uses "
            f"(floorplan/04_kicad say {sorted(cands)}) — the driver would write "
            f"and grade a board that is not this one")
    if tsx is None:
        return fails
    if tsx in TEMPLATE_KNOBS and not (tsdir / "src" / f"{tsx}.tsx").is_file():
        fails.append(
            f"F-KNOB {driver}: TSX={tsx} is the TEMPLATE SENTINEL and "
            f"03_tscircuit/src/{tsx}.tsx does not exist — this driver has never "
            f"been edited for this board, so it has never run for it")
    elif not (tsdir / "src" / f"{tsx}.tsx").is_file():
        have = sorted(p.name for p in (tsdir / "src").glob("*.tsx"))
        fails.append(
            f"F-KNOB {driver}: TSX={tsx} but 03_tscircuit/src/{tsx}.tsx does "
            f"not exist (present: {have or 'nothing'})")
    return fails


def load_record(project):
    p = project / RECORD
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def write_record(project, rec):
    p = project / RECORD
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n")
    return p


# ------------------------------------------------------------------- stamp
def cmd_stamp(args):
    project = Path(args.project).resolve()
    tsdir = project / "03_tscircuit"
    board, tsx, driver = args.board, args.tsx, project / "03_src" / "rebuild_all.sh"

    fails = grade_knobs(project, board, tsx, driver)
    if not tsdir.is_dir():
        fails.append(f"F-KNOB {project}: no 03_tscircuit/ — nothing to build")

    fp, srcs = (source_fingerprint(tsdir) if tsdir.is_dir() else ("", []))
    if tsdir.is_dir() and not srcs:
        fails.append(f"F-VOID {tsdir}: no tscircuit source files match "
                     f"{list(SRC_GLOBS)} — a build here cannot mean anything")

    print(f"M-FRESH stamp: board={board} tsx={tsx} "
          f"fingerprint over {len(srcs)}/{len(srcs)} tscircuit source file(s) "
          f"under {tsdir}")
    if fails:
        for f in fails:
            print(f"  FAIL {f}")
        print(f"M-FRESH FAIL: {len(fails)} finding(s) BEFORE the build ran — "
              f"refusing to stamp a run that cannot be about this board")
        return 1

    rec = {
        "phase": "pre-build",
        "run_id": uuid.uuid4().hex,
        "project": project.name,
        "board": board,
        "tsx": tsx,
        "started_ns": time.time_ns(),
        "src_fingerprint": fp,
        "src_files": srcs,
        "driver": str(driver.relative_to(project)) if driver.is_file() else None,
    }
    out = write_record(project, rec)
    print(f"M-FRESH PASS (stamp): run {rec['run_id'][:12]} recorded in "
          f"{out.relative_to(project)}")
    return 0


# ------------------------------------------------------------------ verify
def cmd_verify(args):
    project = Path(args.project).resolve()
    tsdir = project / "03_tscircuit"
    artifact = Path(args.artifact)
    if not artifact.is_absolute():
        artifact = (project / artifact).resolve()

    rec = load_record(project)
    checks, fails = 0, []

    checks += 1
    if rec is None or rec.get("phase") != "pre-build":
        print(f"M-FRESH verify: artifact under grade = {artifact}")
        print(f"  FAIL F-NORUN {project / RECORD}: no pre-build stamp for this "
              f"run — `build_provenance.py stamp` did not run before the build, "
              f"so nothing here can attest that the build happened at all")
        print(f"M-FRESH FAIL: 1 finding, {checks - 1}/{checks} assertion(s) reached")
        return 1

    checks += 1
    if (rec.get("board"), rec.get("tsx")) != (args.board, args.tsx):
        fails.append(
            f"F-KNOB {project / RECORD}: stamped board/tsx "
            f"{rec.get('board')}/{rec.get('tsx')} != verified "
            f"{args.board}/{args.tsx} — the driver's knobs changed mid-run, or "
            f"this record belongs to another board")

    producer = find_producer(tsdir, args.tsx or "")
    checks += 1
    if producer is None:
        fails.append(
            f"F-VOID {tsdir / 'dist'}: the builder wrote no circuit.json this "
            f"run. `tsci build` produced nothing — a converter run now would "
            f"grade whatever the last run left behind")
    else:
        checks += 1
        if producer.stat().st_mtime_ns < rec["started_ns"]:
            age = (rec["started_ns"] - producer.stat().st_mtime_ns) / 1e9
            fails.append(
                f"F-STALE {producer}: predates this run's build step by "
                f"{age:.1f}s — the builder did not write it, so it is a "
                f"survivor of an earlier build")
        checks += 1
        if not artifact.is_file():
            fails.append(
                f"F-PATH {artifact}: the converter is about to read a path the "
                f"builder never wrote. The builder wrote {producer}")
        else:
            a, b = sha256_file(artifact), sha256_file(producer)
            if a != b:
                fails.append(
                    f"F-PATH {artifact}: content differs from what the builder "
                    f"wrote at {producer} ({a[:12]} != {b[:12]}) — the pipeline "
                    f"is about to grade an artifact this build did not produce")

    checks += 1
    now_fp, srcs = source_fingerprint(tsdir)
    if now_fp != rec.get("src_fingerprint"):
        fails.append(
            f"F-STALE {tsdir}: 03_tscircuit/ sources changed between stamp and "
            f"verify ({len(srcs)} file(s) fingerprinted) — the artifact under "
            f"grade was not built from the sources now on disk (canon M3)")

    print(f"M-FRESH verify: artifact under grade = {artifact}")
    print(f"  builder wrote: {producer if producer else '(nothing)'}")
    print(f"  sources: {len(srcs)}/{len(srcs)} file(s) fingerprinted")
    if fails:
        for f in fails:
            print(f"  FAIL {f}")
        print(f"M-FRESH FAIL: {len(fails)} finding(s) over {checks} assertion(s) "
              f"— refusing to let a gate report green on this artifact")
        return 1

    rec.update({
        "phase": "verified",
        "verified_ns": time.time_ns(),
        "artifact": os.path.relpath(artifact, project),
        "artifact_sha256": sha256_file(artifact),
        "producer": os.path.relpath(producer, project),
    })
    write_record(project, rec)
    print(f"M-FRESH PASS: {checks}/{checks} assertion(s) — "
          f"{rec['artifact']} is byte-identical to {rec['producer']}, "
          f"written this run, from the sources now on disk")
    return 0


# ------------------------------------------------------------------- audit
def audit_project(project):
    """After-the-fact grade. Returns (status, findings, detail).

    status:
      "adopted"    the driver invokes this checker, so its run leaves evidence
                   and the record is graded. Findings here FAIL.
      "unadopted"  the driver carries knobs but does not stamp — it emits no
                   evidence either way, so "never ran" is UNKNOWABLE here. That
                   is itself the finding, reported BY NAME and counted against
                   ADOPTION_FLOOR, but it is not a red row a reader cannot fix.
                   F-KNOB is STILL graded: a `BOARD=power3s` is a defect today,
                   not an adoption gap.
      "unreached"  not the knobbed-driver shape at all.

    Nothing is ever silently skipped (canon M-COVER: an empty denominator may
    not read as a pass).
    """
    project = Path(project)
    tsdir = project / "03_tscircuit"
    board, tsx, driver = read_driver_knobs(project)
    if driver is None:
        return "unreached", [], "no 03_src/rebuild_all.sh"
    if tsx is None and board is None:
        return "unreached", [], f"{driver.name} carries no BOARD=/TSX= knobs " \
                                f"(not the template driver shape)"
    if not tsdir.is_dir():
        return "unreached", [], "no 03_tscircuit/"

    fails = grade_knobs(project, board, tsx, driver)
    if "build_provenance.py" not in driver.read_text(errors="replace"):
        return "unadopted", fails, (
            f"board={board} tsx={tsx}: {driver.name} never calls "
            f"build_provenance.py, so no run it performs leaves evidence that "
            f"it happened — reseed it from "
            f"skills/pcb-design/templates/03_src/rebuild_all.sh")

    rec = load_record(project)
    if rec is None:
        fails.append(
            f"F-NORUN {project / RECORD}: no provenance record — this board's "
            f"driver has never completed a stamped run, so no gate result here "
            f"can be attributed to a build")
    elif rec.get("phase") != "verified":
        fails.append(
            f"F-NORUN {project / RECORD}: record is phase={rec.get('phase')!r}, "
            f"never reached `verified` — the last run started and did not "
            f"finish its build verification")
    else:
        if rec.get("board") != board or rec.get("tsx") != tsx:
            fails.append(
                f"F-KNOB {project / RECORD}: record is for "
                f"{rec.get('board')}/{rec.get('tsx')}, driver now says "
                f"{board}/{tsx} — the record does not describe this driver")
        now_fp, _ = source_fingerprint(tsdir)
        if now_fp != rec.get("src_fingerprint"):
            fails.append(
                f"F-STALE {tsdir}: sources have changed since the last verified "
                f"build — every downstream artifact is under suspicion until "
                f"the driver is rerun (canon M3)")
        art = project / rec.get("artifact", "")
        if not art.is_file():
            fails.append(f"F-PATH {art}: the verified artifact is gone")
        elif sha256_file(art) != rec.get("artifact_sha256"):
            fails.append(
                f"F-PATH {art}: content changed since it was verified — "
                f"something wrote the graded artifact outside the driver")
    return "adopted", fails, f"board={board} tsx={tsx}"


#: A COMMITTED INTEGER, raised in the SAME change that migrates a board's
#: driver. It is what stops adoption from silently going backwards once the
#: template is fixed: every new board seeded from
#: skills/pcb-design/templates/03_src/rebuild_all.sh adopts M-FRESH for free, so
#: the count can only fall if someone deletes the calls.
#:
#: 0 on 2026-07-30, and that number IS the finding: five of the five knobbed
#: live boards (crow-recorder-central-v2, pluto-cal-switch, pluto-rx2-8way,
#: pluto-rx2-8way-v2, usb-hub-3s-v3) can produce NO EVIDENCE that their driver
#: ever ran, which is exactly how pluto-rx2-8way-v2 carried BOARD=power3s
#: through four commits of green stage gates. Their drivers are project files;
#: the template is the source of truth and is fixed here, and each copy
#: re-syncs on its next revision rather than being retro-edited.
ADOPTION_FLOOR = 0


def cmd_audit(args):
    if args.root:
        root = Path(args.root).resolve()
        # LIVE boards only. archived_projects/ is sealed history — grading it
        # would produce a permanent red nobody is allowed to fix (04_kicad and
        # 07_releases are IMMUTABLE), which is a ratchet that teaches readers to
        # ignore the colour.
        projects = sorted({p.parent.parent
                           for p in root.glob("projects/*/03_src/rebuild_all.sh")})
    else:
        projects = [Path(args.project).resolve()]

    rows = [(p, *audit_project(p)) for p in projects]
    adopted = [r for r in rows if r[1] == "adopted"]
    unadopted = [r for r in rows if r[1] == "unadopted"]
    unreached = [r for r in rows if r[1] == "unreached"]
    knobbed = adopted + unadopted
    fails = [f for r in adopted for f in r[2]]
    knob_fails = [f for r in unadopted for f in r[2]]

    print(f"M-FRESH audit: {len(adopted)}/{len(knobbed)} knobbed board(s) "
          f"adopted ({len(unadopted)} OWED, {len(unreached)} UNREACHED — all "
          f"named below; none is a silent skip)")
    for p, _st, fs, detail in adopted:
        print(f"  {'FAIL' if fs else 'ok  '} {p.name}: {detail}")
        for f in fs:
            print(f"       FAIL {f}")
    for p, _st, fs, detail in unadopted:
        print(f"  OWED {p.name}: {detail}")
        for f in fs:
            print(f"       FAIL {f}")
    for p, _st, _fs, detail in unreached:
        print(f"  UNREACHED {p.name}: {detail}")

    bad = fails + knob_fails
    if len(adopted) < ADOPTION_FLOOR:
        bad.append(f"ADOPTION {len(adopted)} board(s) call build_provenance.py, "
                   f"below the committed floor of {ADOPTION_FLOOR} — a driver "
                   f"stopped stamping")
        print(f"  FAIL {bad[-1]}")
    if bad:
        print(f"M-FRESH FAIL: {len(bad)} finding(s) over {len(knobbed)} knobbed "
              f"board(s) ({len(adopted)} adopted, floor {ADOPTION_FLOOR})")
        return 1
    if not adopted:
        print(f"M-FRESH: NOTHING GRADED — 0/{len(knobbed)} knobbed board(s) "
              f"stamp their builds, so no board here can show its gates ran on "
              f"a fresh artifact. This is NOT a pass.")
        return 0
    print(f"M-FRESH PASS: {len(adopted)}/{len(knobbed)} knobbed board(s) carry "
          f"a verified, current build provenance record "
          f"({len(unadopted)} OWED, floor {ADOPTION_FLOOR})")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("stamp", help="record the pre-build state (run BEFORE tsci build)")
    s.add_argument("project")
    s.add_argument("--board", required=True)
    s.add_argument("--tsx", required=True)
    s.set_defaults(fn=cmd_stamp)

    v = sub.add_parser("verify", help="assert the artifact under grade is this run's build")
    v.add_argument("project")
    v.add_argument("--board", required=True)
    v.add_argument("--tsx", required=True)
    v.add_argument("--artifact", required=True,
                   help="the path the NEXT stage will read (the converter input)")
    v.set_defaults(fn=cmd_verify)

    a = sub.add_parser("audit", help="after-the-fact: did the driver run, and is it current?")
    a.add_argument("project", nargs="?", default=".")
    a.add_argument("--root", help="grade every board under REPO/projects/")
    a.set_defaults(fn=cmd_audit)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
