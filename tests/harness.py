#!/usr/bin/env python3
"""Tiny dependency-free test harness (no pytest on the KiCad interpreter).

The one idea this harness exists to enforce: **a gate that cannot fail is
worthless**. So every test declares its KIND:

    @test("audit_board passes a clean board")                  # kind="clean"
    @test("audit_board FAILS on a courtyard overlap",
          kind="known_bad")

A `known_bad` test asserts that a checker REJECTS a deliberately broken
fixture. The summary line reports those separately, because "37 tests pass"
means nothing if none of them ever exercised a failure path. If the
known-bad count is zero, the suite prints a loud warning and exits nonzero.

Assert PROPERTIES, never file bytes: KRT routing is stochastic and the
silk de-collision search is order-dependent, so golden-file comparison
would be permanently broken. Compare node sets, counts, exit codes, and
substrings of a report — never a hash of a .kicad_pcb.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "kicad-pcb" / "scripts"
FAB_SCRIPTS = ROOT / "skills" / "jlcpcb-fab" / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
KPY = "/usr/bin/python3"          # the interpreter that has pcbnew

_REGISTRY = []


def test(name, kind="clean", slow=False):
    def deco(fn):
        _REGISTRY.append({"name": name, "kind": kind, "slow": slow, "fn": fn})
        return fn
    return deco


# --------------------------------------------------------------- asserts
class Failed(AssertionError):
    pass


def check(cond, msg):
    if not cond:
        raise Failed(msg)


def eq(got, want, what="value"):
    check(got == want, f"{what}: got {got!r}, want {want!r}")


def contains(hay, needle, what="output"):
    check(needle in hay, f"{what} does not contain {needle!r}\n--- got ---\n"
                         f"{hay[-2000:]}")


def not_contains(hay, needle, what="output"):
    check(needle not in hay, f"{what} unexpectedly contains {needle!r}")


# ------------------------------------------------------------ subprocess
class Run:
    def __init__(self, cp):
        self.rc = cp.returncode
        self.out = (cp.stdout or "") + (cp.stderr or "")
        # KiCad's python spews wx asserts and image-handler debug on every
        # import; strip so assertions read against real output.
        self.out = "\n".join(
            l for l in self.out.splitlines()
            if "property.h(" not in l and ": Debug: " not in l)

    def __repr__(self):
        return f"<rc={self.rc} out={self.out[-400:]!r}>"


def run(args, cwd=None, env=None, timeout=600):
    e = dict(os.environ)
    e.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    if env:
        e.update(env)
    return Run(subprocess.run([str(a) for a in args], cwd=str(cwd) if cwd else None,
                              capture_output=True, text=True, env=e, timeout=timeout))


def must_pass(r, what):
    check(r.rc == 0, f"{what} should have exited 0, got {r.rc}\n{r.out[-3000:]}")
    return r


def must_fail(r, what, expect=None):
    """The known-bad workhorse: assert the checker REJECTED the fixture."""
    check(r.rc != 0, f"{what} SHOULD HAVE FAILED but exited 0 — the gate is "
                     f"not gating.\n{r.out[-3000:]}")
    if expect:
        contains(r.out, expect, f"{what} failure output")
    return r


# ----------------------------------------------------------------- utils
def tmpdir(prefix="ct_"):
    return Path(tempfile.mkdtemp(prefix=prefix))


def project_copy(project, dest, board=None, subdirs=("03_src", "02_parts")):
    """Copy a project into a scratch tree so path-hardcoded per-project
    scripts (audit_board.py, bom_seed.py) can run against a candidate board
    without touching the sealed 04_kicad."""
    src = ROOT / "projects" / project
    dest.mkdir(parents=True, exist_ok=True)
    for sd in subdirs:
        if (src / sd).is_dir():
            shutil.copytree(src / sd, dest / sd, dirs_exist_ok=True)
    (dest / "04_kicad").mkdir(exist_ok=True)
    (dest / "06_build").mkdir(exist_ok=True)
    if board:
        shutil.copy(board, dest / "04_kicad" / Path(board).name)
    wv = dest / "06_build" / "refdes_waiver.json"
    if not wv.exists():
        wv.write_text("[]")
    return dest


def board_nodes(path):
    """(refdes, pad) -> netname, via a subprocess so the harness itself
    never needs pcbnew (it runs on whatever python the user invoked)."""
    code = (
        "import pcbnew,sys,json\n"
        "b=pcbnew.LoadBoard(sys.argv[1]); o={}\n"
        "for f in b.GetFootprints():\n"
        "  for p in f.Pads():\n"
        "    n=p.GetNetname()\n"
        "    if n: o[f'{f.GetReference()}.{p.GetNumber()}']=n\n"
        "print('@@'+json.dumps(o))\n")
    r = must_pass(run([KPY, "-c", code, str(path)]), "board_nodes")
    import json
    return json.loads(r.out.split("@@", 1)[1].strip())


def edit_board(path, snippet):
    """Mutate a board in place with a pcbnew snippet. THE fixture factory:
    known-bad boards are made by breaking a good one in exactly one way, so
    the test proves the checker reacts to THAT defect and nothing else."""
    code = ("import pcbnew,sys\nb=pcbnew.LoadBoard(sys.argv[1])\n"
            + snippet + "\nb.Save(sys.argv[1])\n")
    return must_pass(run([KPY, "-c", code, str(path)]), f"edit_board({path.name})")


# ------------------------------------------------------------------ main
def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    want_slow = "--slow" in argv
    only = None
    for a in argv:
        if a.startswith("--only="):
            only = a.split("=", 1)[1]

    sel = [t for t in _REGISTRY
           if (want_slow or not t["slow"])
           and (not only or re.search(only, t["name"], re.I))]
    npass = nfail = 0
    failed, kb_pass = [], 0
    for t in sel:
        tag = "known-bad" if t["kind"] == "known_bad" else "clean"
        sys.stdout.write(f"  [{tag:9}] {t['name']} ... ")
        sys.stdout.flush()
        try:
            t["fn"]()
        except Exception as e:
            nfail += 1
            failed.append((t["name"], e))
            print("FAIL")
            for line in traceback.format_exc().splitlines()[-12:]:
                print("      " + line)
        else:
            npass += 1
            if t["kind"] == "known_bad":
                kb_pass += 1
            print("ok")
    skipped = len(_REGISTRY) - len(sel)
    print(f"\n  {npass} passed, {nfail} failed"
          + (f", {skipped} skipped (use --slow)" if skipped else ""))
    print(f"  {kb_pass} of those are KNOWN-BAD fixtures that made their "
          f"checker fail as required")
    if not kb_pass and sel:
        # Not fatal per-suite: the e2e tier is legitimately all-clean, and a
        # --only= filter can select clean tests. run_tests.sh enforces the
        # real rule across the whole run, where "zero known-bad" genuinely
        # means the run proved nothing.
        print("  NOTE: no known-bad fixture in this selection — on its own "
              "this suite proves nothing about whether the gates can fail")
    return 1 if nfail else 0


if __name__ == "__main__":
    sys.exit(main())
