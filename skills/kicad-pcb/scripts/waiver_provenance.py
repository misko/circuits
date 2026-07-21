#!/usr/bin/env python3
"""waiver_provenance — catch a waiver whose RATIONALE was copied from another
project and re-presented as fresh judgement.

    python3 waiver_provenance.py PROJECTS_ROOT [--project NAME] [--twin]
                                 [--threshold 0.85]

WHY THIS EXISTS (incident, 2026-07-20). Canon M4 says every waiver carries the
measurement that justifies it, and `policy_audit.py` enforces that a waiver has
a `why` of some length. Nothing enforced that the `why` was about THIS BOARD.

The audit that found it: lipo3s-tsc's policy_waivers.yaml
is BYTE-IDENTICAL to usb-power-3s's (03_src/rules/policy_waivers.yaml) —
including a header sentence that names the other project as its subject
("usb-power-3s released v1.1-2026-07-16..."), and four waivers citing
usb-power-3s's release dates, route inputs r0..r6 and its 96 F.Fab refdes as
though they were lipo3s-tsc's own. The same R-POUR VBUS measurement (2.51A,
~16C rise) appears in three projects; the P-SILK-FN paragraph in four. One
event, reported as four independent findings, each one passing M-WAIV.

A copied rationale is worse than a missing one: it reads as evidence, it
satisfies the evidence gate, and it silently transplants another board's
measurements onto copper nobody measured.

THE CONTRACT. Reuse is legitimate — boards do share copper and parts. What is
not legitimate is UNDECLARED reuse. A waiver that inherits another project's
reasoning must say so:

    - id: R-POUR
      derived_from: usb-power-3s        # <- the declaration
      why: >-
        Identical copper to usb-power-3s (board parity 0); its measurement
        applies here because ...

CHECKS
  W-COPY     a `why` in project A is >= --threshold similar to a `why` in
             project B, and neither declares `derived_from` naming the other.
             Similarity is computed on NORMALIZED text (case, punctuation,
             unit spacing and "@"/"at" folded), so the reword-to-look-fresh
             pass that produced lipo3s-usb-hub's R-POUR does not evade it.
  W-FOREIGN  a waiver's `why`, or the comment header of the file it lives in,
             names a DIFFERENT project in this repo and does not declare
             `derived_from`. This is the byte-copy signature: the text still
             talks about the board it was written for.

Exit 0 when clean, 1 on any finding.
"""
import argparse
import difflib
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("waiver_provenance needs pyyaml")

WAIVER_REL = "03_src/rules/policy_waivers.yaml"
TWIN_REL = "03_src/rules/twin_adjudications.yaml"


def normalize(text):
    """Fold the differences a copy-and-reword pass introduces.

    Real example (R-POUR, usb-power-3s -> lipo3s-usb-hub): '0.8mm' -> '0.8 mm',
    'at 10C rise' -> '@10C rise', a dropped date stamp, a dropped clause. The
    argument and every number survived; only the typography moved.
    """
    t = str(text).lower()
    t = re.sub(r"\b(\d[\d.]*)\s*(mm|mil|a|v|w|c|mm2|oz)\b", r"\1\2", t)
    t = t.replace("@", " at ")
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return " ".join(t.split())


def similarity(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()


def load_waivers(proj_dir, rel):
    """-> list of dicts, each with the raw entry plus its file header comments."""
    p = Path(proj_dir) / rel
    if not p.is_file():
        return []
    raw = p.read_text()
    header = "\n".join(l.lstrip("# ").rstrip() for l in raw.splitlines()
                       if l.lstrip().startswith("#"))
    try:
        entries = yaml.safe_load(raw) or []
    except yaml.YAMLError as e:
        return [{"_parse_error": str(e), "_path": p, "_header": header}]
    out = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        e = dict(e)
        e["_path"] = p
        e["_header"] = header
        out.append(e)
    return out


def declared(entry, other_project):
    """Does this entry declare that it inherits from `other_project`?"""
    d = entry.get("derived_from")
    if not d:
        return False
    vals = d if isinstance(d, (list, tuple)) else [d]
    return any(other_project in str(v) for v in vals)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("root", help="the projects/ directory")
    ap.add_argument("--project", default="",
                    help="grade only this project (still compares fleet-wide)")
    ap.add_argument("--twin", action="store_true",
                    help="also scan twin_adjudications.yaml")
    ap.add_argument("--threshold", type=float, default=0.85)
    a = ap.parse_args(argv)

    root = Path(a.root)
    if not root.is_dir():
        print(f"FAIL W-SRC: no such directory {root}")
        return 1

    projects = sorted(p.name for p in root.iterdir() if p.is_dir())
    rels = [WAIVER_REL] + ([TWIN_REL] if a.twin else [])

    # project -> list of (entry, normalized_why)
    loaded = {}
    for name in projects:
        items = []
        for rel in rels:
            for e in load_waivers(root / name, rel):
                why = e.get("why", "")
                items.append((e, normalize(why)))
        if items:
            loaded[name] = items

    fails, oks = [], []
    graded = [a.project] if a.project else sorted(loaded)

    for e_list in loaded.values():
        for e, _ in e_list:
            if "_parse_error" in e:
                fails.append(f"W-SRC {e['_path']}: unparseable ({e['_parse_error']})")

    # ---- W-FOREIGN: the text still names the board it was written for
    for name in graded:
        for e, _ in loaded.get(name, []):
            hay = normalize(str(e.get("why", "")) + " " + str(e.get("_header", "")))
            for other in projects:
                # `crow-array` is a substring of `crow-array-central`: a
                # sibling naming its own family is not a foreign citation.
                if other == name or len(other) < 5 or other in name or name in other:
                    continue
                if normalize(other) in hay and not declared(e, other):
                    fails.append(
                        f"W-FOREIGN {name} [{e.get('id', '?')}]: rationale names "
                        f"another project ({other!r}) and declares no "
                        f"derived_from — the evidence is about a different board")
                    break

    # ---- W-COPY: the same rationale, twice, undeclared
    for i, name in enumerate(graded):
        for e, na in loaded.get(name, []):
            if len(na) < 60:
                continue
            for other in sorted(loaded):
                if other == name:
                    continue
                for f, nb in loaded[other]:
                    if len(nb) < 60:
                        continue
                    s = similarity(na, nb)
                    if s < a.threshold:
                        continue
                    if declared(e, other) or declared(f, name):
                        oks.append(f"W-COPY {name} [{e.get('id', '?')}] reuses "
                                   f"{other} at {s:.2f} — DECLARED")
                        continue
                    fails.append(
                        f"W-COPY {name} [{e.get('id', '?')}]: rationale is "
                        f"{s:.0%} identical to {other} [{f.get('id', '?')}] "
                        f"with no derived_from — one measurement presented as "
                        f"two independent findings")

    for name in graded:
        n = len(loaded.get(name, []))
        if n and not any(name in f for f in fails):
            oks.append(f"W-COPY/{name}: {n} waivers, all independently reasoned")

    for o in sorted(set(oks)):
        print("  ok  ", o)
    for f in sorted(set(fails)):
        print("FAIL ", f)
    print("WAIVER PROVENANCE:", "FAIL" if fails else "PASS",
          f"({len(set(fails))} fails, {len(set(oks))} ok)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
