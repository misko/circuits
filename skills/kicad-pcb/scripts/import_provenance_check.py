#!/usr/bin/env python3
"""import_provenance_check — M-IMPORT made mechanical (ADR-0005/0009).

    import_provenance_check.py PROJECT_DIR [--external-hardware-root DIR]
    import_provenance_check.py --root REPO_ROOT          # every board

WHY THIS EXISTS (incident, 2026-07-27). Every gate in this repo compares OUR
artifacts to OUR artifacts. A fact about the OUTSIDE world entered the pipeline
unexamined, and one nearly reached copper:

  pluto-cal-switch must mate to an ADALM-PlutoPlus SMA panel. The vendor
  publishes NO PCB source — three PDFs, no KiCad/Altium, no DXF, no STEP, no
  dimensioned drawing. The three-connector SMA span was extracted from an
  UNDIMENSIONED vector assembly plot at 35.60 mm, and three independent
  extractions agreed to 0.003 mm. A floorplan was ready to be built on it.
  A caliper on two physical units then read 35.04 mm (genuine, 1.6% off the
  plot) and 34.72 mm (2025 clone, 2.5%) against a rigid-SMA mating window of
  +-0.05 mm. The error was 10-18x the window, and NO GATE COULD HAVE SEEN IT,
  because the number never came from an artifact any gate reads.

Precision about a proxy is not accuracy about the object.

THE MECHANISM. `external_hardware/<device>/` is the SINGLE HOME for facts about
hardware this repo did not design: `README.md` is the human record (method
stated per number),
`facts.yaml` is its machine index. A board declares `03_src/rules/mates.yaml`
naming the device and the facts it CONSUMES — ids and where they are spent,
never the values. Boards REFERENCE; they never restate. That is the same shape,
and the same reason, as `assembly.yaml` being the single home for "who gets
placed": cooksense v1.1 shipped 13 CPL rows contradicting its own MANIFEST
because two files held one fact and drifted.

CHECKS (findings are named for the canon row they enforce)
  M-EXIST    the device folder, its facts.yaml, and every referenced fact id
             exist — AND the fact's `quote:` appears VERBATIM in the human
             record, with its value inside that quote. A machine index that
             has drifted from the record it indexes is not evidence.
  M-GRADE    every referenced fact carries a grade in the closed vocabulary
             MEASURED / CITED / ESTIMATED / OWED. Absent or unknown is a FAIL,
             never a skip (M-IMPORT reads an ungraded fact as ESTIMATED; a
             machine may not quietly promote it).
  M-BAR      an ESTIMATED fact used DIMENSIONALLY carries an error bar, and the
             bar must PARSE to a magnitude. This is the check the incident
             wanted: +-1.5% on a 35.60 mm span is +-0.53 mm, and it was about
             to be spent against a +-0.05 mm budget.
  M-PROXY    the grade must match the METHOD. A number read off a rendered
             plot, a photograph, or an inference is not MEASURED however many
             times it was re-extracted; a published number whose DATUM is
             unstated is ESTIMATED, not CITED. Keyword proxy over the method
             text — deliberately NOT triggered by "derived", because arithmetic
             on two caliper readings is still a measurement (the PlutoPlus
             D-free pitches are exactly that).
  M-OWED     a fact nobody has yet is declared OWED with how to obtain it, and
             may NOT be consumed dimensionally. Declaring the gap is the point:
             the PlutoPlus RF-axis height above its PCB is unestablished, and
             it sets the daughter board's entire Z relationship.
  M-RESTATE  a `consumes:` entry may not carry value/grade/method/units/bar —
             that is the board restating a fact whose home is
             `external_hardware/`.
  D-MATE     every consumed fact says WHERE it is spent; and a BRIEF declaring
             a Mating fact-lock must have the mates.yaml to match it.

NOT IN SCOPE, said out loud (M-COVER): this gate grades the PROVENANCE of the
facts a board REFERENCES. It does not check that the numbers are right, and it
is NOT a mating-feasibility checker (error bar vs mating budget) — that has been
run once, by hand, on one interface, and canon M8 promotes on the SECOND board
needing it. A fact sitting in `facts.yaml` that no board consumes is NOT graded
here, and the coverage line says so.

Exit 0 when clean, 1 on any finding.
"""
import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:                                   # pragma: no cover
    sys.exit("import_provenance_check needs pyyaml")

MATES_REL = "03_src/rules/mates.yaml"
BRIEF_REL = "01_docs/BRIEF.md"
GRADES = ("MEASURED", "CITED", "ESTIMATED", "OWED")
USES = ("dimensional", "informational", "owed")

#: keys whose HOME is external_hardware/<device>/facts.yaml. A board that
#: writes one has made a second home for the fact, which is how two files drift.
RESTATED_KEYS = ("value", "grade", "method", "units", "error_bar", "quote",
                 "measured", "source_value")

#: method words that describe a PROXY for the object, not the object. A grade
#: of MEASURED (or CITED) over one of these is the incident's exact shape.
#: "derived" is deliberately absent: subtracting two caliper readings is still
#: a measurement, and the PlutoPlus D-free pitches are computed that way.
PROXY_WORDS = ("photogrammetr", "extracted from", "extraction", "rendered",
               "assembly plot", "estimate", "estimated", "inferred", "infer",
               "pixel", "guess", "assumed", "scaled from", "eyeball")

#: an error bar must PARSE. "about a percent" is not a bar.
BAR_RE = re.compile(r"[+\-±]{0,3}\s*(\d+(?:\.\d+)?)\s*(%|mm|um|µm|mil|deg)",
                    re.I)

#: the BRIEF section D-MATE mandates, and the escape hatch that closes it.
MATING_HEAD_RE = re.compile(r"^#{2,4}\s.*mating fact-lock", re.I | re.M)
NO_MATE_RE = re.compile(r"does not mate", re.I)


def load_yaml(path):
    """-> (obj, error). A file we cannot parse is a FAIL, never a skip."""
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}, None
    except Exception as e:                            # noqa: BLE001
        return None, str(e)


def parse_bar(text):
    """-> the bar's magnitude+unit, or None if it does not parse."""
    if text is None:
        return None
    m = BAR_RE.search(str(text))
    return (float(m.group(1)), m.group(2).lower()) if m else None


def proxy_words(method):
    return sorted({w for w in PROXY_WORDS if w in str(method or "").lower()})


def grade_device(external_hardware_root, device, fails):
    """Load external_hardware/<device>/facts.yaml and its human record."""
    ddir = Path(external_hardware_root) / str(device)
    if not ddir.is_dir():
        fails.append(f"M-EXIST device {device!r}: no such folder {ddir} — the "
                     f"facts have no home, so nothing can be graded")
        return {}, ""
    fpath = ddir / "facts.yaml"
    if not fpath.is_file():
        fails.append(f"M-EXIST device {device!r}: {fpath} missing — the README "
                     f"is the human record, facts.yaml is what a board may "
                     f"reference")
        return {}, ""
    doc, err = load_yaml(fpath)
    if err is not None:
        fails.append(f"M-EXIST device {device!r}: {fpath} unparseable ({err})")
        return {}, ""
    record = ddir / str(doc.get("record") or "README.md")
    if not record.is_file():
        fails.append(f"M-EXIST device {device!r}: record {record} missing — a "
                     f"machine index with no record behind it is not evidence")
        text = ""
    else:
        text = record.read_text(errors="replace")
    facts = {}
    for f in doc.get("facts") or []:
        if isinstance(f, dict) and f.get("id"):
            facts[str(f["id"])] = f
    return facts, text


def grade_fact(device, ref, fact, record_text, fails, oks):
    """The M-IMPORT obligations, over one referenced fact. -> True if graded.

    "Graded" means the fact reached the grade-dependent checks — i.e. it
    carried a grade this tool understands. A fact whose grade is missing or
    unknown is COUNTED AS REFERENCED AND NOT GRADED, so the N/M denominator
    shows the blind spot instead of hiding it.
    """
    fid = str(ref.get("fact"))
    use = str(ref.get("use") or "").strip().lower()
    tag = f"{device}/{fid}"

    # ---- D-MATE: a consumption with no site is not a declaration
    if not str(ref.get("where") or "").strip():
        fails.append(f"D-MATE {tag}: consumed with no `where:` — a fact spent "
                     f"nowhere in particular cannot be reviewed at the point "
                     f"of USE, which is where M-IMPORT grades it")
    if use not in USES:
        fails.append(f"D-MATE {tag}: use {use!r} outside the vocabulary "
                     f"{list(USES)} — an unreadable declaration is a FAIL, "
                     f"never a skip")

    # ---- M-RESTATE: one home per fact
    restated = [k for k in RESTATED_KEYS if k in ref]
    if restated:
        fails.append(f"M-RESTATE {tag}: the board restates {restated} — those "
                     f"live in external_hardware/{device}/facts.yaml. Two "
                     f"homes for one fact "
                     f"is how cooksense v1.1's CPL and MANIFEST drifted")

    # ---- M-GRADE
    grade = str(fact.get("grade") or "").strip().upper()
    if grade not in GRADES:
        fails.append(f"M-GRADE {tag}: grade {fact.get('grade')!r} is not one of "
                     f"{list(GRADES)} — an ungraded fact reads as ESTIMATED and "
                     f"a machine may not quietly promote it")
        return False

    # ---- M-EXIST (second half): the index must still agree with the record
    quote = str(fact.get("quote") or "")
    if not quote:
        fails.append(f"M-EXIST {tag}: no `quote:` — the fact cites no line of "
                     f"the human record, so drift between them is invisible")
    elif quote not in record_text:
        fails.append(f"M-EXIST {tag}: quote {quote[:60]!r} is not in the device "
                     f"record VERBATIM — facts.yaml has drifted from the "
                     f"record it indexes")
    elif fact.get("value") is not None and str(fact["value"]) not in quote:
        fails.append(f"M-EXIST {tag}: value {fact['value']!r} does not appear "
                     f"in the line it quotes — the index and the record "
                     f"disagree about the number")

    # ---- M-PROXY: the grade must match the method
    words = proxy_words(fact.get("method"))
    if grade in ("MEASURED", "CITED") and words:
        fails.append(f"M-PROXY {tag}: graded {grade} but its method reads "
                     f"{words} — that describes a PROXY for the object. "
                     f"Precision about a proxy is not accuracy about the "
                     f"object (the 35.60 mm plot span, three extractions "
                     f"agreeing to 0.003 mm, was 0.56 mm wrong)")
    if grade != "OWED" and not str(fact.get("method") or "").strip():
        fails.append(f"M-PROXY {tag}: no `method:` — a number that cannot say "
                     f"how it was obtained is worse than a gap, because a gap "
                     f"is visible (external_hardware/contracts.md)")

    # ---- M-OWED: a fact nobody has may not be spent as if they did
    if grade == "OWED":
        if use != "owed":
            fails.append(f"M-OWED {tag}: OWED fact consumed as {use!r} — "
                         f"nobody has this number yet. Declare it owed, or "
                         f"go and get it")
        if not str(fact.get("how_to_obtain") or "").strip():
            fails.append(f"M-OWED {tag}: OWED with no `how_to_obtain:` — an "
                         f"open gap with no route to closing it is a wish")
        oks.append(f"M-OWED {tag}: declared OWED, not invented")
        return True
    if use == "owed":
        fails.append(f"M-OWED {tag}: consumed as owed but graded {grade} — the "
                     f"fact exists; consume it or drop the reference")

    # ---- M-BAR: an ESTIMATED dimension must carry a parseable error bar
    if grade == "ESTIMATED" and use == "dimensional":
        bar = parse_bar(fact.get("error_bar"))
        if fact.get("error_bar") in (None, ""):
            fails.append(f"M-BAR {tag}: ESTIMATED and used DIMENSIONALLY with "
                         f"no error bar. This is the incident: a span carrying "
                         f"+-1.5% (+-0.53 mm) was about to be spent against a "
                         f"+-0.05 mm mating window as if it were MEASURED")
        elif bar is None:
            fails.append(f"M-BAR {tag}: error bar {fact['error_bar']!r} does "
                         f"not parse to a magnitude — an unreadable bar is a "
                         f"FAIL, never a skip")
        else:
            oks.append(f"M-BAR {tag}: ESTIMATED, bar {bar[0]}{bar[1]} declared")
    elif grade == "ESTIMATED":
        oks.append(f"M-GRADE {tag}: ESTIMATED, consumed as {use} — no bar "
                   f"required, and none may be spent on a dimension")
    if grade in ("MEASURED", "CITED"):
        oks.append(f"M-GRADE {tag}: {grade}, method stated, record agrees")
    return True


def grade_project(pdir, external_hardware_root, fails, oks):
    """-> (referenced, graded) fact counts for this board (0,0 = declares none)."""
    pdir = Path(pdir)
    mates = pdir / MATES_REL
    brief = pdir / BRIEF_REL

    if not mates.is_file():
        # D-MATE: a BRIEF that declares a mating fact-lock must have the yaml.
        if brief.is_file():
            text = brief.read_text(errors="replace")
            m = MATING_HEAD_RE.search(text)
            if m:
                body = text[m.end():]
                nxt = re.search(r"^#{2}\s", body, re.M)
                body = body[:nxt.start()] if nxt else body
                if not NO_MATE_RE.search(body):
                    fails.append(
                        f"D-MATE {pdir.name}: BRIEF.md declares a Mating "
                        f"fact-lock but {MATES_REL} does not exist — the "
                        f"user-facing lock has no machine copy, so nothing "
                        f"grades the provenance of what it locks")
        return 0, 0

    doc, err = load_yaml(mates)
    if err is not None:
        fails.append(f"M-EXIST {pdir.name}: {MATES_REL} unparseable ({err})")
        return 0, 0
    device = doc.get("device")
    if not device:
        fails.append(f"M-EXIST {pdir.name}: {MATES_REL} names no `device:` — "
                     f"it must point at the external_hardware/<device>/ "
                     f"folder that holds "
                     f"the facts")
        return 0, 0

    refs = doc.get("consumes") or []
    if not isinstance(refs, list) or not refs:
        fails.append(f"M-COVER {pdir.name}: {MATES_REL} consumes NOTHING — a "
                     f"zero denominator is a FAIL; delete the file or name "
                     f"the facts this board spends")
        return 0, 0

    facts, record_text = grade_device(external_hardware_root, device, fails)
    seen = graded = 0
    for ref in refs:
        if not isinstance(ref, dict) or not ref.get("fact"):
            fails.append(f"M-EXIST {pdir.name}: a `consumes:` entry names no "
                         f"`fact:` id ({ref!r})")
            continue
        fid = str(ref["fact"])
        seen += 1
        fact = facts.get(fid)
        if fact is None:
            fails.append(f"M-EXIST {pdir.name}/{fid}: not in "
                         f"external_hardware/{device}/facts.yaml — a board "
                         f"may only consume "
                         f"facts the device record actually holds")
            continue
        graded += bool(grade_fact(device, ref, fact, record_text, fails, oks))
    return seen, graded


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("project", nargs="?", default=None,
                    help="a project dir (with 03_src/rules/mates.yaml)")
    ap.add_argument("--root", default=None,
                    help="repo root: grade every projects/<board>")
    ap.add_argument("--external-hardware-root", default=None,
                    help="the external_hardware/ directory "
                         "(default: <root>/external_hardware)")
    a = ap.parse_args(argv)

    if not a.project and not a.root:
        ap.error("give a PROJECT_DIR or --root")

    if a.root:
        root = Path(a.root)
        projects = sorted(p for p in (root / "projects").glob("*") if p.is_dir())
    else:
        projects = [Path(a.project)]
        root = Path(a.project).resolve().parents[1]
    external_hardware_root = (
        Path(a.external_hardware_root) if a.external_hardware_root
        else root / "external_hardware"
    )

    fails, oks = [], []
    seen_facts = graded_facts = 0
    boards = []
    for p in projects:
        seen, graded = grade_project(p, external_hardware_root, fails, oks)
        seen_facts += seen
        graded_facts += graded
        if seen:
            boards.append(f"{p.name}({graded}/{seen})")

    print(f"  input: {len(projects)} project(s) under "
          f"{projects[0].parent if projects else '?'}; facts from "
          f"{external_hardware_root}")
    for o in oks:
        print("  ok   ", o)
    for f in fails:
        print("FAIL  ", f)
    print(f"  coverage: {graded_facts}/{seen_facts} referenced facts graded "
          f"across {len(boards)}/{len(projects)} project(s) declaring "
          f"{MATES_REL}" + (f" — {', '.join(boards)}" if boards else ""))

    if not seen_facts and not fails:
        # Deliberately NOT a failure. Most boards mate to nothing foreign, and
        # a gate that cries wolf on every such board trains readers to ignore
        # red. It must still say out loud that it graded nothing (M-COVER):
        # "PASS" over an empty denominator is the shape this whole family of
        # gates exists to prevent.
        print("IMPORT PROVENANCE: NOTHING TO GRADE — no board declares "
              f"{MATES_REL}; this run proved nothing about imported facts")
        return 0
    print("IMPORT PROVENANCE:", "FAIL" if fails else "PASS",
          f"({len(fails)} fails, {len(oks)} ok, "
          f"{graded_facts}/{seen_facts} facts graded)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
