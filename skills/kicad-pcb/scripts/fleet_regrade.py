#!/usr/bin/env python3
"""fleet_regrade.py — run TODAY'S gates against EVERY sealed release.

    fleet_regrade.py [--root DIR] [--json OUT] [--project NAME]

WHY THIS EXISTS. Some defects were always wrong. Others BECOME wrong, and no
amount of shifting left catches those — only re-grading sealed work against
later knowledge does.

THE INCIDENT. interposer v1.0 sealed 2026-07-24 with `J_KEY_MATRIX` at CPL
rotation 90.0. That came from name-DB rule `^JST_GH_SM,180`, which was REFUTED
on 2026-07-25 — the day AFTER the seal. The release was correct by the knowledge
of its day and became a P0 overnight: at 180 degrees the pad array is symmetric
about its own centre, so every pad still lands on a pad and the part solders
perfectly, while pin1<->pin10 swap reverses the entire ten-line keypad ribbon.
Nothing told anyone.

Worse, and this is the part a shift-left cannot reach: that release's
`verification/policy_audit.md` has **no A-POP, A-POS, A-ROT, A-POL, A-BODY or
A-STOCK row at all**. Not failed — ABSENT. It was sealed during the same days
that gate family was landing and was never re-graded, so every one of its P0s
lives in a gate it was never subjected to. A release sealed before a gate exists
is invisible to that gate forever, and nothing in the pipeline noticed.

TWO QUESTIONS, AND THE SECOND IS THE ONE THAT WAS MISSING

  1. Does this release still PASS the gates we can run today?
  2. Which of today's gates NEVER GRADED it — because they did not exist, or
     because nobody re-ran them? (the `graded_by:` gap)

Question 2 is answered without changing the seal format: a gate ID that exists
today and appears in NONE of the release's shipped verification artifacts never
graded it. That is a coverage HOLE, reported as such — an absent verdict is not
a pass, which is the whole M-COVER principle applied to releases rather than to
rows.

THIS TOOL OBEYS ITS OWN CONTRACT (canon M-COVER). It reports `N/M` releases
regraded, and every gate it could NOT run is NAMED with the reason. A regrade
that silently skips what it cannot run would reproduce, at fleet scale, exactly
the defect it exists to find.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

KPY = "/usr/bin/python3"

#: gates runnable standalone against a SEALED release directory (canon M-SHIP:
#: each reads the release's own bytes, not a rebuild).
GATES = [
    ("F-PAYLOAD", "jlcpcb-fab/scripts/fab_payload_census.py", ["{rel}"]),
    ("A-EVID", "kicad-pcb/scripts/release_required_check.py", ["{rel}"]),
    ("A-POP", "jlcpcb-fab/scripts/assembly_coverage.py", ["{rel}"]),
]

#: check IDs that exist TODAY. A release whose verification/ mentions none of a
#: family's IDs was never graded by it.
FAMILIES = {
    "ASSEMBLY": ["A-POP", "A-POS", "A-ROT", "A-POL", "A-BODY", "A-STOCK"],
    "FAB-PAYLOAD": ["F-POUR", "F-IDENT"],
    "RENDER": ["A-RENDER"],
    "META": ["M-REL", "M-REPRO", "M-CONS", "M-BOM"],
}


def releases(root, project=None):
    out = []
    for p in sorted((root / "projects").glob("*/07_releases/*/")):
        if project and p.parts[-3] != project:
            continue
        if not p.is_dir():
            continue
        out.append(p)
    return out


def run_gate(root, script, args, rel):
    path = root / "skills" / script
    if not path.is_file():
        return None, f"gate script absent: {script}"
    cmd = [KPY, str(path)] + [a.format(rel=str(rel)) for a in args]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except Exception as e:                        # noqa: BLE001
        return None, f"could not run: {e}"
    out = (r.stdout or "") + (r.stderr or "")
    first = ""
    for ln in out.splitlines():
        if "FAIL" in ln:
            first = ln.strip()
            break
    return r.returncode, first or out.strip().splitlines()[-1:][0] if out.strip() else ""


def graded_families(rel):
    """{family: True/False} — did ANY of this family's IDs appear in the
    release's own shipped verification evidence?"""
    blob = []
    for p in list(rel.glob("verification/*")) + [rel / "MANIFEST.txt"]:
        if p.is_file() and p.suffix.lower() in (".md", ".txt", ".csv", ".json", ""):
            try:
                blob.append(p.read_text(errors="replace"))
            except Exception:                     # noqa: BLE001
                continue
    text = "\n".join(blob)
    return {fam: any(re.search(rf"\b{re.escape(i)}\b", text) for i in ids)
            for fam, ids in FAMILIES.items()}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[3]))
    ap.add_argument("--json", default=None)
    ap.add_argument("--project", default=None)
    a = ap.parse_args(argv)
    root = Path(a.root)

    rels = releases(root, a.project)
    rows, unrunnable = [], []
    for rel in rels:
        name = f"{rel.parts[-3]}/{rel.name}"
        res, holes = {}, graded_families(rel)
        for gid, script, args in GATES:
            rc, msg = run_gate(root, script, args, rel)
            if rc is None:
                unrunnable.append(f"{name}: {gid} — {msg}")
                res[gid] = "?"
            else:
                res[gid] = "PASS" if rc == 0 else "FAIL"
                if rc != 0:
                    res[gid + "_why"] = msg[:200]
        rows.append({"release": name, "gates": res,
                     "never_graded": [f for f, ok in holes.items() if not ok]})

    superseded = {r["release"] for r in rows
                  if (root / "projects" / r["release"].split("/")[0]
                      / "07_releases" / r["release"].split("/")[1]
                      / "SUPERSEDED.md").is_file()}

    print(f"  coverage: {len(rows)}/{len(rels)} sealed release(s) regraded "
          f"with {len(GATES)} standalone gate(s); {len(unrunnable)} gate run(s) "
          f"could not execute")
    for u in unrunnable:
        print(f"  UNRUNNABLE {u}")

    # Never truncate the release name. A first version cut it at 50 chars,
    # which on `crow-recorder-central-v2/crow-recorder-central-v2-v1.5-...`
    # removed THE VERSION — the one field a reader needs most. Column width is
    # measured from the data, not guessed.
    w = max([len(r["release"]) for r in rows] + [len("release")])
    print(f"\n{'release':{w}}   " + " ".join(f"{g:10}" for g, _, _ in GATES)
          + "  never-graded-by")
    fails = 0
    for r in sorted(rows, key=lambda x: x["release"]):
        cells = " ".join(f"{r['gates'].get(g, '?'):10}" for g, _, _ in GATES)
        holes = ",".join(r["never_graded"]) or "-"
        mark = "*" if r["release"] in superseded else " "
        print(f"  {r['release']:{w}} {mark} {cells}  {holes}")
        if any(r["gates"].get(g) == "FAIL" for g, _, _ in GATES) \
                and r["release"] not in superseded:
            fails += 1

    print("\n  * = carries SUPERSEDED.md (a FAIL on a superseded release is "
          "history, not a live defect)")
    print("  NOTE: a board superseded by a SUCCESSOR PROJECT rather than a "
          "later version (crow-mic-pod -> crow-mic-pod-v2, usb-hub-3s -> "
          "usb-hub-3s-v3) carries NO SUPERSEDED.md, because that file names a "
          "successor DIRECTORY inside the same 07_releases/. Those releases "
          "read as live here and are not — the supersede convention has no "
          "cross-project form. Reported rather than special-cased: inventing a "
          "rule for it inside this tool would hide a real gap in the contract.")
    for r in sorted(rows, key=lambda x: x["release"]):
        for g, _, _ in GATES:
            why = r["gates"].get(g + "_why")
            if why and r["release"] not in superseded:
                print(f"  {g} {r['release']}: {why}")

    if a.json:
        Path(a.json).write_text(json.dumps(
            {"rows": rows, "unrunnable": unrunnable,
             "superseded": sorted(superseded)}, indent=2) + "\n")

    live_holes = sum(1 for r in rows
                     if r["never_graded"] and r["release"] not in superseded)
    print(f"\nFLEET REGRADE: {fails} live release(s) FAIL a gate they can be "
          f"run against; {live_holes} live release(s) were NEVER GRADED by at "
          f"least one gate family that exists today")
    return 1 if (fails or live_holes) else 0


if __name__ == "__main__":
    sys.exit(main())
