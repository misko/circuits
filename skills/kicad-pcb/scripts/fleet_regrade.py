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

AND A THIRD QUESTION, ADDED 2026-07-29: **IS THE VERDICT EVEN REPRODUCIBLE?**

The regrade's whole premise is that a sealed release can be re-graded. That is
false for any gate whose AUTHORITY lives outside the sealed archive and can be
edited — and F-LEGIBLE was such a gate for its whole existence. `cooksense-v1.6`
went FAIL, then PASS, on UNCHANGED SEALED BYTES, within one session, because the
live v1.7 work removed and then restored an `02_parts/ULN2803ADWR` dossier. A
verdict that moves under the artifact is not evidence about the artifact, and the
self-healing direction is the worse one: nobody records a red that repaired
itself for an unrelated reason.

So the sweep now MEASURES reproducibility instead of assuming it: each gate that
declares a PERTURBATION is run twice — once normally, once with its mutable
external authority NEUTRALISED — and a release whose PASS/FAIL verdict MOVES
between the two runs is reported as NOT REPRODUCIBLE and fails the sweep. This is
canon M1 applied to the regrade itself: the perturbation is an independent
method, and it does not ask the gate whether it is coupled, it makes the coupling
observable. MEASURED at landing: **9 of 33 sealed releases flipped PASS -> FAIL
under the perturbation — every single release that PASSED F-LEGIBLE at all, four
of them LIVE and orderable.** After F-LEGIBLE learned to read the code->MPN map
already sealed inside each release (`verification/stock_check.csv`) and to report
what it still cannot cross-check as a THIRD verdict rather than a failure: 0 of
33.
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

KPY = "/usr/bin/python3"

#: printed by a gate that RAN, found no defect, and could NOT fully grade the
#: shipped bytes. A protocol, deliberately a literal string in both files: see
#: `bom_legibility_check.UNGRADED_TOKEN`, which must stay identical. Rendered as
#: its own cell state, because a table printing PASS over an ungraded row is the
#: M-COVER failure at fleet scale.
UNGRADED_TOKEN = "NOT-REDERIVABLE-FROM-SHIPPED-BYTES"

#: gates runnable standalone against a SEALED release directory (canon M-SHIP:
#: each reads the release's own bytes, not a rebuild). The 4th field is the
#: REPRODUCIBILITY PERTURBATION: extra argv that neutralises this gate's mutable
#: EXTERNAL authority, so the same release can be graded as it will be after the
#: project tree has moved on. `{empty_dir}` and `{empty_yaml}` are substituted
#: with a scratch empty directory and an empty YAML mapping. A gate with no
#: perturbation declared is NOT thereby certified reproducible — it is simply
#: unmeasured, and the summary says so rather than implying a clean bill.
GATES = [
    ("F-PAYLOAD", "jlcpcb-fab/scripts/fab_payload_census.py", ["{rel}"], []),
    ("F-LEGIBLE", "jlcpcb-fab/scripts/bom_legibility_check.py", ["{rel}"],
     ["--parts", "{empty_dir}", "--ledger", "{empty_yaml}"]),
    ("A-EVID", "kicad-pcb/scripts/release_required_check.py", ["{rel}"], []),
    ("A-POP", "jlcpcb-fab/scripts/assembly_coverage.py", ["{rel}"], []),
]

#: check IDs that exist TODAY. A release whose verification/ mentions none of a
#: family's IDs was never graded by it.
FAMILIES = {
    "ASSEMBLY": ["A-POP", "A-POS", "A-ROT", "A-POL", "A-BODY", "A-STOCK"],
    "FAB-PAYLOAD": ["F-POUR", "F-IDENT"],
    "FAB-BOM": ["F-LEGIBLE", "F-MPN", "F-WORDS", "F-ENCODE", "F-ECHO"],
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


def run_gate(root, script, args, rel, extra=(), subs=None):
    """(rc, first-interesting-line, full output). rc is None when it could not
    run at all — which is UNRUNNABLE and never a pass."""
    path = root / "skills" / script
    if not path.is_file():
        return None, f"gate script absent: {script}", ""
    fmt = dict(rel=str(rel), **(subs or {}))
    cmd = [KPY, str(path)] + [a.format(**fmt) for a in list(args) + list(extra)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except Exception as e:                        # noqa: BLE001
        return None, f"could not run: {e}", ""
    out = (r.stdout or "") + (r.stderr or "")
    first = ""
    for ln in out.splitlines():
        if "FAIL" in ln:
            first = ln.strip()
            break
    if not first:
        for ln in out.splitlines():
            if UNGRADED_TOKEN in ln:
                first = ln.strip()
                break
    tail = out.strip().splitlines()[-1:][0] if out.strip() else ""
    return r.returncode, (first or tail), out


#: a FAIL line's STABLE identity: the check ID plus the row it is about. The
#: full line embeds the authority's own description, which changes under the
#: perturbation for reasons that are not findings — keying on the ID is what
#: makes two runs comparable at all.
FINDING_RE = re.compile(r"\bFAIL\s+([A-Z]-[A-Z]+)(\s+row\s+\d+)?")


def finding_ids(out):
    return {(m.group(1) + (m.group(2) or "")).strip()
            for m in FINDING_RE.finditer(out or "")}


def verdict_of(rc, out):
    """PASS / FAIL / UNGR. **UNGR IS NOT A PASS** — the gate ran, found no
    defect, and could not grade the shipped bytes. Folding it into PASS is the
    exact `row_kind` silent-default shape canon M-COVER forbids, one level up."""
    if rc is None:
        return "?"
    if rc != 0:
        return "FAIL"
    return "UNGR" if UNGRADED_TOKEN in out else "PASS"


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
    ap.add_argument("--no-reproducibility", action="store_true",
                    help="skip the M-SHIP perturbation re-run (halves runtime, "
                         "and gives up the only measurement that can tell you a "
                         "seal's verdict is not re-derivable)")
    a = ap.parse_args(argv)
    root = Path(a.root)

    scratch = Path(tempfile.mkdtemp(prefix="fleet_regrade_"))
    (scratch / "empty_dir").mkdir(exist_ok=True)
    (scratch / "empty.yaml").write_text("{}\n")
    subs = {"empty_dir": str(scratch / "empty_dir"),
            "empty_yaml": str(scratch / "empty.yaml")}

    rels = releases(root, a.project)
    rows, unrunnable = [], []
    for rel in rels:
        name = f"{rel.parts[-3]}/{rel.name}"
        res, holes = {}, graded_families(rel)
        moved = []
        for gid, script, args, perturb in GATES:
            rc, msg, out = run_gate(root, script, args, rel)
            if rc is None:
                unrunnable.append(f"{name}: {gid} — {msg}")
                res[gid] = "?"
                continue
            res[gid] = verdict_of(rc, out)
            if res[gid] != "PASS":
                res[gid + "_why"] = msg[:200]
            # ---- M-SHIP: is this verdict re-derivable from the sealed bytes?
            if perturb and not a.no_reproducibility:
                prc, pmsg, pout = run_gate(root, script, args, rel,
                                           perturb, subs)
                pv = verdict_of(prc, pout)
                res[gid + "_perturbed"] = pv
                # UNGR under the perturbation is the HONEST answer, not a move:
                # the gate is saying out loud that it cannot cross-check without
                # the external authority. A PASS<->FAIL move is the defect.
                if {res[gid], pv} == {"PASS", "FAIL"} or (
                        res[gid] == "FAIL" and pv in ("PASS", "UNGR")):
                    moved.append(
                        f"{gid}: {res[gid]} normally, {pv} with its MUTABLE "
                        f"authority neutralised — this verdict is a function of "
                        f"editable source OUTSIDE the sealed archive "
                        f"({pmsg[:120]})")
                else:
                    # The census above grades the VERDICT. A release that FAILS
                    # for a SECOND, independent reason keeps its verdict while a
                    # COUPLED FINDING vanishes underneath it, so the weaker
                    # signal is measured too: findings present normally and
                    # ABSENT under the perturbation. Only that direction counts —
                    # a finding that appears only when the authority is removed
                    # is the intended degradation to "ungraded", not drift.
                    # MEASURED 2026-07-29: 5 releases (usb-hub-3s-v3 v1.5-v1.9,
                    # whose `SS12D07VG6 087` DISAGREE finding needs the dossier
                    # tree to exist and which fail F-ENCODE either way).
                    lost = sorted(finding_ids(out) - finding_ids(pout))
                    if lost:
                        res[gid + "_coupled_findings"] = ",".join(lost)
        rows.append({"release": name, "gates": res, "not_reproducible": moved,
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
    print(f"\n{'release':{w}}   " + " ".join(f"{g:10}" for g, _, _, _ in GATES)
          + "  never-graded-by")
    fails = 0
    for r in sorted(rows, key=lambda x: x["release"]):
        cells = " ".join(f"{r['gates'].get(g, '?'):10}" for g, _, _, _ in GATES)
        holes = ",".join(r["never_graded"]) or "-"
        mark = "*" if r["release"] in superseded else " "
        print(f"  {r['release']:{w}} {mark} {cells}  {holes}")
        if any(r["gates"].get(g) == "FAIL" for g, _, _, _ in GATES) \
                and r["release"] not in superseded:
            fails += 1
    print("\n  PASS / FAIL / UNGR / ? — **UNGR IS NOT A PASS**: the gate ran, "
          "found no defect, and could not cross-check the shipped bytes against "
          "anything the release itself carries. On a LIVE release that is "
          "counted as an open coverage hole below, because an absent verdict is "
          "not a pass (canon M-COVER). `?` = the gate could not run at all.")

    print("\n  * = carries SUPERSEDED.md (a FAIL on a superseded release is "
          "history, not a live defect)")
    print("  NOTE: a board superseded by a SUCCESSOR PROJECT rather than a "
          "later version (crow-mic-pod -> crow-mic-pod-v2, usb-hub-3s -> "
          "usb-hub-3s-v3) carries NO SUPERSEDED.md, because that file names a "
          "successor DIRECTORY inside the same 07_releases/. Those releases "
          "read as live here and are not — the supersede convention has no "
          "cross-project form. Reported rather than special-cased: inventing a "
          "rule for it inside this tool would hide a real gap in the contract.")
    # FIXED 2026-07-27. This loop used to suppress `why` for any superseded
    # release, which made the tool CONTRADICT ITS OWN PURPOSE: a retired defect
    # vanished from the report the instant a successor was sealed, so the one
    # artifact that could tell you WHY a release was retired stopped saying it
    # at exactly the moment that became history worth keeping.
    #
    # It also made t1_fleet_regrade's "the retired defect is STILL NAMED, with
    # its reason" assertion UNPASSABLE — a gate that cannot pass, the same class
    # as usb-hub v1.9's `<= 300 uA` bench gate that would have failed a good
    # board. Found by that test going red, not by anyone predicting it.
    #
    # Suppression was the right instinct aimed at the wrong thing: the noise a
    # reader must not drown in is superseded FAILS COUNTED AS LIVE BLOCKERS, and
    # that is handled above (`fails` skips superseded, and the row carries `*`).
    # A reason is not noise; it is the audit trail. So it is printed either way
    # and LABELLED, which is strictly more information than withholding it.
    for r in sorted(rows, key=lambda x: x["release"]):
        for g, _, _, _ in GATES:
            why = r["gates"].get(g + "_why")
            if not why:
                continue
            hist = "  [superseded: history, not a live defect]" \
                if r["release"] in superseded else ""
            print(f"  {g} {r['release']}: {why}{hist}")

    # ---- M-SHIP: the reproducibility census ------------------------------
    perturbed_gates = [g for g, _, _, p in GATES if p]
    unmeasured = [g for g, _, _, p in GATES if not p]
    ungr = [(r["release"], g) for r in sorted(rows, key=lambda x: x["release"])
            for g, _, _, _ in GATES if r["gates"].get(g) == "UNGR"]
    if a.no_reproducibility:
        print("\n  REPRODUCIBILITY NOT MEASURED (--no-reproducibility). The "
              "verdicts above may be functions of editable source outside the "
              "sealed archives and this run cannot tell you which.")
        not_repro = []
    else:
        not_repro = [(r["release"], m)
                     for r in sorted(rows, key=lambda x: x["release"])
                     for m in r["not_reproducible"]]
        print(f"\n  reproducibility: {len(rows)} release(s) x "
              f"{len(perturbed_gates)} gate(s) with a declared perturbation "
              f"({','.join(perturbed_gates)}) re-graded with the gate's MUTABLE "
              f"EXTERNAL authority neutralised. {len(not_repro)} verdict(s) "
              f"MOVED.")
        print(f"  NOT MEASURED: {','.join(unmeasured) or 'none'} declare no "
              f"perturbation — unmeasured is NOT certified reproducible, and "
              f"naming them is the difference between the two (canon M-COVER).")
        for name, why in not_repro:
            print(f"  NOT-REPRODUCIBLE {name}: {why}")
        drifted = [(r["release"], g, r["gates"][g + "_coupled_findings"])
                   for r in sorted(rows, key=lambda x: x["release"])
                   for g, _, _, _ in GATES
                   if r["gates"].get(g + "_coupled_findings")]
        print(f"  {len(drifted)} release(s) keep their verdict but LOSE a "
              f"finding under the perturbation — a coupled defect masked by a "
              f"second, independent failure:")
        for name, gid, why in drifted:
            print(f"  COUPLED-FINDING {name} {gid}: {why} present normally, "
                  f"absent once the mutable authority is neutralised")
    for name, gid in ungr:
        hist = " [superseded]" if name in superseded else ""
        print(f"  UNGRADED {name}: {gid} ran clean but could not cross-check "
              f"the shipped bytes against anything the release carries{hist}")

    if a.json:
        Path(a.json).write_text(json.dumps(
            {"rows": rows, "unrunnable": unrunnable,
             "superseded": sorted(superseded),
             "not_reproducible": [list(x) for x in not_repro],
             "ungraded": [list(x) for x in ungr]}, indent=2) + "\n")

    live_holes = sum(1 for r in rows
                     if r["never_graded"] and r["release"] not in superseded)
    live_ungr = sum(1 for name, _ in ungr if name not in superseded)
    print(f"\nFLEET REGRADE: {fails} live release(s) FAIL a gate they can be "
          f"run against; {live_holes} live release(s) were NEVER GRADED by at "
          f"least one gate family that exists today; {len(not_repro)} "
          f"verdict(s) are NOT RE-DERIVABLE from the sealed bytes; "
          f"{live_ungr} live gate verdict(s) are UNGRADED")
    return 1 if (fails or live_holes or not_repro or live_ungr) else 0


if __name__ == "__main__":
    sys.exit(main())
