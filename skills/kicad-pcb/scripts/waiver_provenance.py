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


================================================================================
THE SECOND INCIDENT (2026-07-29): A LOAD-BEARING NUMBER THAT WAS TYPED
================================================================================

Everything above grades PROSE AGAINST PROSE. Nothing re-derived a number, and
the vacuity block at the bottom of this docstring said so in writing. Measured
consequence, on this repo's own fleet: **16 of 22 waiver entries rest on a
hand-typed measurement and 2 carry a re-runnable command** — and the error is
not "slightly off", it is CONCLUSION-FLIPPING. pluto-rx2-8way's
`P-ADJ-UNREACHED` typed "C_SW1 pad 1 -> U_SW pin 8 = 2.62 mm, inside the 3 mm
the datasheet sentence means"; the pair measured **3.085 mm** centre-to-centre,
the measure `policy_audit.py:412` itself defines — OVER the threshold the waiver
asserted it was inside. The waiver's own conclusion reverses.

So a waiver's evidence stops being a NUMBER and becomes A COMMAND AND ITS
OUTPUT, which this gate then REGENERATES AND DIFFS:

    - id: P-ADJ-UNREACHED
      refs: [PE42482A-X]
      why: >-
        Pin 8 sits on the global 3V3 net, so no keep_short budget can address
        it; measured by hand against the datasheet's 3 mm instead.
      evidence:
        - claim: C_SW1.1 -> U_SW.8, pad centre to pad centre (P-ADJ's measure)
          command: /usr/bin/python3 -c "import pcbnew, math; ..."
          output: "2.873"
          budget: "<= 3.0"        # the CONCLUSION the number carries
          tolerance: 0.02         # optional; units of `output`
          tolerance_why: >-       # mandatory whenever tolerance is present
            Pads are placed by the legalizer, not the router: this pair moves
            only if a part moves, so the only legitimate drift is ...

`command` is re-run from the REPO ROOT, its last stdout line must carry exactly
one number, and that number is compared with `output`. When `budget` is declared
the RELATION is checked too, which is what catches the incident: 3.085 against
`<= 3.0` is not a 0.2 mm discrepancy, it is a reversed verdict, and it is
reported as one.

  W-SCHEMA   `evidence` is not a list of mappings, an item carries an unknown
             key (a typo'd `commmand:` must not degrade silently into prose),
             or `output` does not contain exactly one number. An `output`
             carrying two numbers is prose again.
  W-GRADE    `grade:` is not one of CITED / ESTIMATED; a CITED item carries no
             `command`+`output` (a citation claim with nothing cited); an
             ESTIMATED item carries no `why_not_rerunnable`.
  W-CMD      the command is not READ-ONLY (a denylist of mutating tokens — this
             gate executes what the YAML says, and an audit must not be able to
             write).
  W-REGEN    the command ran, printed a number, and that number DISAGREES with
             the typed `output` by more than `tolerance`.
  W-FLIP     the regenerated number does not satisfy the declared `budget`
             relation that the typed one did. THE CONCLUSION REVERSED. Reported
             separately from W-REGEN and never excused by tolerance.
  W-ARITH    the TYPED `output` does not satisfy its own declared `budget`.
             Costs no board and no command: it is pure arithmetic on the two
             numbers the author wrote down next to each other.
  W-TOL      `tolerance` present without `tolerance_why`, or a tolerance >= the
             MARGIN the entry claims (|budget - output|). A tolerance that
             cannot distinguish pass from fail is not a tolerance — it is the
             next typed number, and this is the check that stops the fix from
             recreating the defect.
  W-REFS     a `refs:` entry that is shaped like a repo path does not exist
             under the project, or a `path:LO-HI` line span reaches past the end
             of the file it cites. A line range is a load-bearing typed number.
  W-MACHINE  a refdes in `04_kicad/refdes_waiver.json` — the file
             `generate_board_generic.py` writes FOR ITSELF and
             `policy_audit.py:793` then reads as evidence, which is canon M1
             from the inside — is not named by any `refs:` in the project's
             own `policy_waivers.yaml`. Machine self-certification, measured.

THE LADDER, for a number that cannot be regenerated here and now (canon
M-IMPORT: ESTIMATED, not CITED — reported with its denominator, never silently
green and never a fleet block):

  CITED      command ran, printed one number, agrees within tolerance.
  UNVERIFIED a command exists but did not produce a number HERE — declared
             `requires:` absent (a board mid-rebuild is the motivating case),
             timeout, or non-zero exit. Named on every run, credited to nobody,
             and deliberately NOT a fail: the alternative is a gate whose
             verdict depends on whether a sibling agent happens to be
             rebuilding a board, which is a gate that gets disabled.
  ESTIMATED  no command is possible; `why_not_rerunnable:` says why. The
             M-IMPORT grade. Legal, reported, never counted as CITED.
  OWED       no `evidence:` block at all — the whole fleet on the day this
             landed. Named entry by entry, counted, ceiling-pinned.

THE RATCHET, because a day-one mandate over 22 entries lands as 22 red rows and
gets switched off inside a week: coverage is REPORTED, every OWED entry is
printed BY NAME, and only three counting facts can FAIL — CITED dropping below
`CITED_FLOOR`, OWED rising above `OWED_CEILING`, and unbacked machine waivers
rising above `MACHINE_UNBACKED_CEILING`. The direction is what makes them
monotone: a new unevidenced waiver, or a citation that stops reproducing, FAILS
TODAY, while the existing 22 are a named debt rather than a wall.

VACUITY: (canon G-VACUOUS — the input class on which this gate PASSES while the
fact it grades is FALSE, fixtured by `t1_audit.py`
`t_vacuity_a_waiver_whose_typed_measurement_is_arithmetically_false_passes`.)

NARROWED, NOT CLOSED, 2026-07-29, and the surviving half is stated exactly.
W-REGEN / W-FLIP / W-ARITH grade ONLY what an entry DECLARES in an `evidence:`
block. A number typed in `why:` prose is still read by nothing — and on the day
the schema landed that was **22 of 22 fleet entries, 0 CITED**, i.e. the gate's
new teeth bite an empty set on the real tree and the incident entry itself is
still ungraded IN ITS ORIGINAL FORM. That is why OWED is enumerated by name on
every run and ceiling-pinned rather than left as a silent zero; a coverage
number nobody prints is how the first version of this blind spot survived.

W-COPY and W-FOREIGN remain TEXT-SIMILARITY checks between one piece of prose
and another. Neither re-derives a number from copper, and `normalize()` folds
unit spacing precisely so that a number survives a reword — correct for
copy-detection, and it means digits are only ever compared to other digits
SOMEONE TYPED. The only other gate on waiver evidence is
`policy_audit.py:165`, `len(str(w.get("why", ""))) < 40` — a LENGTH test.

So a waiver carrying an ORIGINAL, board-specific, 40+ character `why` containing
an INVENTED measurement and NO `evidence:` block passes every gate in this repo.
THE CONTRAST, which is what makes this a blind spot and not a fact the gate
cannot represent: the SAME waiver with the SAME false number moved into an
`evidence:` block is caught, by name, with the conclusion reversal called out —
`t1_waiver_evidence.py`
`t_incident_the_c_sw1_waiver_promoted_to_the_evidence_schema_is_caught`.

MEASURED on pluto-rx2-8way at commit c07aaf2, waiver `P-ADJ-UNREACHED`: "MEASURED
by hand instead: C_SW1 pad 1 to U_SW pin 8 = 2.62 mm, inside the 3 mm the
datasheet sentence means." Re-measured against the board that revision governed:
**3.085 mm** pad-centre to pad-centre — which is the measure `policy_audit.py:412`
itself defines for P-ADJ — i.e. 0.085 mm OVER the 3 mm the waiver asserted it was
inside. The waiver's CONCLUSION FLIPS. `2.62` reproduces under no definition:
edge-to-edge is 2.375 mm (rect) / 2.438 mm (roundrect polygon), so it is neither
a typo nor a mis-defined metric but a free-hand estimate. A second entry reads
"2.53 mm" where R_PD4.1 -> U_SW.12 measures 3.057 mm; that one stays inside its
4 mm budget, so it was wrong without being load-bearing. Both passed for a full
revision cycle.

FLEET DENOMINATOR: 22 waiver entries across 5 boards; **16 carry a hand-typed
number in prose**, 2 carry a re-runnable command, 10 name a script without an
invocation, 3 carry neither. The single densest entry carries 39 separate typed
mm figures, none re-derived by any gate.

THE STRUCTURAL FIX IS NOW APPLIED — see "THE SECOND INCIDENT" above — and it
narrows this block rather than deleting it: re-running the command IS the check,
for every entry that declares one. The fixture above stands because the fleet
declares none yet.
"""
import argparse
import difflib
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("waiver_provenance needs pyyaml")

WAIVER_REL = "03_src/rules/policy_waivers.yaml"
TWIN_REL = "03_src/rules/twin_adjudications.yaml"
MACHINE_REL = "04_kicad/refdes_waiver.json"

# ---------------------------------------------------------------- the ratchet
# MEASURED on the fleet at main tip, 2026-07-29, by this script. Each is
# MONOTONE IN THE DIRECTION THAT MATTERS, so the existing debt is a named list
# and the NEXT one is a hard fail:
#   CITED may only RISE, OWED and unbacked machine waivers may only FALL.
# Edit one of these only in the same commit that earns it, and say which run
# produced the number.
CITED_FLOOR = 0                 # evidence items regenerated and agreeing
OWED_CEILING = 22               # entries with no `evidence:` block at all
MACHINE_UNBACKED_CEILING = 9    # refdes_waiver.json entries with no project
                                # -side evidence. PINNED AT THE HIGHEST VALUE
                                # OBSERVED, NOT THE LATEST: measured 9-of-11 at
                                # 12:xx and 5-of-7 an hour later, because a
                                # sibling agent's cooksense rebuild re-ran the
                                # silk placer and it found slots for four of the
                                # eight refdes it had waived for itself. Both
                                # numbers are real; ratcheting to 5 mid-rebuild
                                # would pin a transient and red that board when
                                # its next placement pass gives four back. The
                                # 2 BACKED are pluto-rx2-8way's C_MCU7 + R_CC1
                                # under P-SILK-REF, and they are backed in both
                                # measurements. Ratchet this down once cooksense
                                # seals, and say which run earned it.

EVIDENCE_KEYS = {"claim", "command", "output", "budget", "tolerance",
                 "tolerance_why", "grade", "requires", "why_not_rerunnable",
                 "note"}
GRADES = ("CITED", "ESTIMATED")

# This gate EXECUTES what the YAML says. An audit that can write is not an
# audit, so a command carrying any of these is refused rather than run. The
# list is deliberately about EFFECTS, not about programs: `python3 -c` is
# allowed (it is how a pcbnew measurement is spelled) and `python3 -c
# "...open(p,'w')..."` is not caught by this — which is why the read-only
# obligation is also stated in the contract, with this as the cheap backstop.
MUTATING = (">", ">>", "|&", " rm ", "rm -", " mv ", " cp ", "unlink",
            "truncate", "tee ", "dd ", "chmod", "chown", "mkdir", "touch ",
            "git commit", "git add", "git checkout", "git reset", "git clean",
            "git push", ".Save(", "Save()", "sudo ", "curl ", "wget ",
            "pip install", "apt ")

_NUM = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")
_REL = re.compile(r"^\s*(<=|>=|<|>|==)\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*$")
# A `why` that leans on a measurement: a number with a unit attached. This is
# the OWED detector, and it is deliberately generous — over-counting OWED is
# safe (the ceiling only ratchets down), under-counting hides the debt.
_TYPED_MEASURE = re.compile(
    r"\d[\d.]*\s*(mm|mil|um|nm|mm2|mm\^2|ohm|kohm|mohm|a\b|ma\b|v\b|mv\b|w\b"
    r"|mw\b|c\b|pf\b|nf\b|uf\b|nh\b|ns\b|ps\b|mhz\b|khz\b|%)", re.I)


def one_number(text):
    """-> float, or None when the text does not carry EXACTLY one number.

    "2.873" and "2.873 mm" are one number; "2.62 mm of 3 mm" is two, and an
    `output:` carrying two numbers is prose again — which is the thing the
    schema exists to stop. Returning None is a W-SCHEMA finding, never a pass.
    """
    hits = _NUM.findall(str(text))
    return float(hits[0]) if len(hits) == 1 else None


def last_line_number(stdout):
    """-> (float, last_line) from a command's stdout, or (None, last_line).

    The LAST non-empty line, and it must carry exactly one number. pcbnew
    scribbles `assert "m_choices.GetCount() > 0" failed` on load, so a rule of
    "the first number anywhere in the output" would read a line number out of
    a wxWidgets assertion and call it a measurement.
    """
    lines = [l for l in str(stdout).splitlines() if l.strip()]
    if not lines:
        return None, ""
    return one_number(lines[-1]), lines[-1].strip()


def relation(budget):
    """'<= 3.0' -> ('<=', 3.0). None when unparseable."""
    m = _REL.match(str(budget))
    return (m.group(1), float(m.group(2))) if m else None


def satisfies(value, rel, limit):
    return {"<=": value <= limit, "<": value < limit, ">=": value >= limit,
            ">": value > limit, "==": value == limit}[rel]


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
    raw = p.read_text(encoding="utf-8-sig")
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


def check_refs(entry, proj_dir, where):
    """W-REFS — a `refs:` entry shaped like a repo path must exist, and a
    `path:LO-HI` span must be inside the file. The line range is a load-bearing
    TYPED NUMBER: crow-mic-pod-v2's R-RULES cites
    `04_kicad/....kicad_dru:8-10` for the two rules that cannot fire, and if a
    regenerated .kicad_dru shifts, that citation silently points at nothing.
    """
    fails = []
    refs = entry.get("refs") or []
    if isinstance(refs, str):
        refs = [refs]
    for raw in refs:
        r = str(raw)
        # "03_src/lib (vendored XU316 footprint)" — a path with a parenthetical
        # gloss is a path, not a broken path.
        r = re.sub(r"\s*\(.*\)\s*$", "", r).strip()
        base, _, tail = r.partition(":")
        looks_like_path = "/" in base or base.endswith(
            (".yaml", ".json", ".md", ".py", ".kicad_pcb", ".kicad_sch",
             ".kicad_dru", ".kicad_pro", ".csv", ".txt"))
        if not looks_like_path:
            continue          # a bare refdes / MPN token; W-MACHINE's business
        p = proj_dir / base
        if not p.exists():
            # A BARE BASENAME IS NOT A PATH. pluto-rx2-8way's S-OCCL cites
            # `pluto_rx2_8way.kicad_sch` with no directory, and that file
            # exists twice (04_kicad/ and 03_tscircuit/kicad/) — failing it
            # would be an adjacent-property error: the citation resolves, it
            # is merely unqualified. Only a ref that resolves NOWHERE in the
            # project, or a real slash-bearing path, is a broken citation.
            if "/" not in base:
                hits = [q for q in proj_dir.rglob(base)]
                if hits:
                    continue
            fails.append(f"W-REFS {where}: refs cites {base!r} which does not "
                         f"exist anywhere under {proj_dir.name} — the "
                         f"evidence points at a file that is not there")
            continue
        m = re.match(r"^(\d+)-(\d+)$", tail)
        if m and p.is_file():
            lo, hi = int(m.group(1)), int(m.group(2))
            try:
                n = len(p.read_text(encoding="utf-8-sig",
                                    errors="replace").splitlines())
            except OSError:
                continue
            if hi > n or lo < 1 or lo > hi:
                fails.append(
                    f"W-REFS {where}: refs cites {base}:{lo}-{hi} but the file "
                    f"has {n} line(s) — a typed line span that no longer "
                    f"resolves is a citation to nothing")
    return fails


def grade_evidence(entry, repo_root, where, regen=True, timeout=180):
    """-> (fails, items) where each item is (grade, label, detail).

    grade in CITED / UNVERIFIED / ESTIMATED. The LADDER lives here: a command
    that cannot produce a number HERE is UNVERIFIED and is reported, never a
    fail — see the module docstring for why that is not a softening.
    """
    fails, items = [], []
    ev = entry.get("evidence")
    if ev is None:
        return fails, items
    if not isinstance(ev, list) or not ev:
        fails.append(f"W-SCHEMA {where}: `evidence:` must be a non-empty LIST "
                     f"of mappings, got {type(ev).__name__}")
        return fails, items

    for i, it in enumerate(ev):
        tag = f"{where} evidence[{i}]"
        if not isinstance(it, dict):
            fails.append(f"W-SCHEMA {tag}: not a mapping ({type(it).__name__})")
            continue
        unknown = sorted(set(it) - EVIDENCE_KEYS)
        if unknown:
            fails.append(
                f"W-SCHEMA {tag}: unknown key(s) {unknown} — a misspelled "
                f"`command:` must not degrade silently back into prose "
                f"(known keys: {sorted(EVIDENCE_KEYS)})")
        claim = str(it.get("claim") or "").strip()
        if len(claim) < 10:
            fails.append(f"W-SCHEMA {tag}: `claim:` must say WHAT was measured")
        label = f"{tag} {claim[:60]!r}"
        cmd = str(it.get("command") or "").strip()
        out_raw = it.get("output")
        grade = str(it.get("grade") or ("CITED" if cmd else "ESTIMATED")).upper()
        if grade not in GRADES:
            fails.append(f"W-GRADE {tag}: grade {grade!r} is not one of "
                         f"{list(GRADES)}")
            grade = "ESTIMATED"

        # ---- the declaration must be internally honest before anything runs
        if grade == "CITED" and not (cmd and out_raw is not None):
            fails.append(f"W-GRADE {tag}: grade CITED with no "
                         f"{'command' if not cmd else 'output'} — a citation "
                         f"claim with nothing cited. Use grade: ESTIMATED and "
                         f"say why in `why_not_rerunnable:` (canon M-IMPORT)")
        if grade == "ESTIMATED" and len(
                str(it.get("why_not_rerunnable") or "").strip()) < 20:
            fails.append(
                f"W-GRADE {tag}: grade ESTIMATED needs `why_not_rerunnable:` — "
                f"ESTIMATED is a legal grade, an UNEXPLAINED one is not")

        typed = one_number(out_raw) if out_raw is not None else None
        if out_raw is not None and typed is None:
            fails.append(
                f"W-SCHEMA {tag}: `output:` {str(out_raw)[:60]!r} does not "
                f"carry exactly one number — an output with two numbers in it "
                f"is prose, and prose is what this schema replaces")

        rel = None
        if it.get("budget") is not None:
            rel = relation(it["budget"])
            if rel is None:
                fails.append(f"W-SCHEMA {tag}: `budget:` "
                             f"{str(it['budget'])[:40]!r} must read like "
                             f"'<= 3.0'")

        tol = it.get("tolerance")
        if tol is not None:
            try:
                tol = float(tol)
            except (TypeError, ValueError):
                fails.append(f"W-SCHEMA {tag}: `tolerance:` must be a number")
                tol = None
        if tol:
            if len(str(it.get("tolerance_why") or "").strip()) < 20:
                fails.append(
                    f"W-TOL {tag}: `tolerance: {tol}` with no "
                    f"`tolerance_why:` — the tolerance is the number most "
                    f"likely to become the next typed number, so it carries "
                    f"the same burden as the measurement")
            if rel and typed is not None:
                margin = abs(rel[1] - typed)
                if tol >= margin:
                    fails.append(
                        f"W-TOL {tag}: tolerance {tol} >= the margin "
                        f"{margin:.4g} this entry claims ({typed} vs budget "
                        f"{rel[0]} {rel[1]}) — a tolerance that cannot "
                        f"distinguish pass from fail is not a tolerance")
        tol = tol or 1e-9

        # ---- W-ARITH: free, no board, no command. The two numbers the author
        # wrote next to each other must be consistent with each other.
        if rel and typed is not None and not satisfies(typed, rel[0], rel[1]):
            fails.append(
                f"W-ARITH {tag}: the TYPED output {typed} does not satisfy the "
                f"budget {rel[0]} {rel[1]} this entry declares — the waiver "
                f"contradicts itself on its own numbers, before any board is "
                f"consulted")

        if not cmd:
            items.append((grade, label, "no command declared"))
            continue

        bad = [t for t in MUTATING if t in cmd]
        if bad:
            fails.append(
                f"W-CMD {tag}: evidence command is not read-only "
                f"({bad!r}) — this gate RUNS what the YAML says, and an audit "
                f"that can write is not an audit")
            items.append(("UNVERIFIED", label, "refused: not read-only"))
            continue

        if not regen:
            items.append(("UNVERIFIED", label, "--no-regen"))
            continue

        # ---- the ladder: declared inputs first, so a board that is being
        # rebuilt right now downgrades to UNVERIFIED instead of failing anyone.
        missing = [str(r) for r in (it.get("requires") or [])
                   if str(r) != "pcbnew" and not (repo_root / str(r)).exists()]
        if "pcbnew" in [str(r) for r in (it.get("requires") or [])]:
            try:
                subprocess.run(["/usr/bin/python3", "-c", "import pcbnew"],
                               capture_output=True, timeout=60, check=True)
            except Exception:
                missing.append("pcbnew (not importable by /usr/bin/python3)")
        if missing:
            items.append(("UNVERIFIED", label,
                          f"declared input absent here: {', '.join(missing)}"))
            continue

        try:
            r = subprocess.run(cmd, shell=True, cwd=str(repo_root),
                               capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            items.append(("UNVERIFIED", label, f"timeout after {timeout}s"))
            continue
        except OSError as e:
            items.append(("UNVERIFIED", label, f"could not launch: {e}"))
            continue
        if r.returncode != 0:
            items.append(("UNVERIFIED", label,
                          f"exit {r.returncode}: "
                          f"{(r.stderr or r.stdout).strip()[-160:]}"))
            continue
        got, line = last_line_number(r.stdout)
        if got is None:
            items.append(("UNVERIFIED", label,
                          f"last stdout line {line[:80]!r} does not carry "
                          f"exactly one number"))
            continue
        if typed is None:
            items.append(("UNVERIFIED", label,
                          f"regenerated {got} but the typed `output:` is "
                          f"unparseable, so there is nothing to diff against"))
            continue

        delta = abs(got - typed)
        flipped = (rel is not None
                   and satisfies(typed, rel[0], rel[1])
                   != satisfies(got, rel[0], rel[1]))
        if flipped:
            fails.append(
                f"W-FLIP {tag}: THE CONCLUSION REVERSES. Typed {typed}, "
                f"regenerated {got} (delta {delta:.4g}); the budget is "
                f"{rel[0]} {rel[1]} and the typed number satisfies it while "
                f"the measured one does not (or the reverse). This is the "
                f"2026-07-29 C_SW1 class and no tolerance excuses it. "
                f"claim: {claim[:80]}")
            items.append(("UNVERIFIED", label, f"conclusion reversed: "
                                               f"{typed} -> {got}"))
            continue
        if delta > tol:
            fails.append(
                f"W-REGEN {tag}: typed {typed}, regenerated {got}, delta "
                f"{delta:.4g} > tolerance {tol:.4g}. claim: {claim[:80]}")
            items.append(("UNVERIFIED", label, f"disagrees by {delta:.4g}"))
            continue
        items.append(("CITED", label,
                      f"regenerated {got} vs typed {typed} (delta "
                      f"{delta:.4g} <= {tol:.4g})"))
    return fails, items


def machine_waivers(proj_dir):
    """-> (list_of_refdes, error) from 04_kicad/refdes_waiver.json.

    THE BLIND SPOT THIS OPENS UP (canon M1). `generate_board_generic.py` writes
    this file for ITSELF when its silk placer finds no slot for a refdes, and
    `policy_audit.py:793` then reads it and SKIPS every refdes in it while
    grading P-SILK-REF. Checker and checked share a method, and until now the
    file sat outside every provenance check while the 04_kicad contract called
    it evidence-backed. pluto-rx2-8way's own P-SILK-REF waiver says so in
    writing and asks for exactly this.
    """
    p = proj_dir / MACHINE_REL
    if not p.is_file():
        return None, None
    try:
        data = json.loads(p.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError) as e:
        return None, f"unreadable ({e})"
    if not isinstance(data, list):
        return None, f"expected a JSON list, got {type(data).__name__}"
    return [str(x) for x in data], None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("root", help="the projects/ directory")
    ap.add_argument("--project", default="",
                    help="grade only this project (still compares fleet-wide)")
    ap.add_argument("--twin", action="store_true",
                    help="also scan twin_adjudications.yaml")
    ap.add_argument("--threshold", type=float, default=0.85)
    ap.add_argument("--no-regen", action="store_true",
                    help="do not RUN evidence commands (every CITED item "
                         "degrades to UNVERIFIED — a fast path, not a pass)")
    ap.add_argument("--timeout", type=int, default=180,
                    help="per-command budget; expiry is UNVERIFIED, not a fail")
    ap.add_argument("--repo-root", default="",
                    help="cwd for evidence commands (default: the parent of "
                         "the projects root)")
    ap.add_argument("--strict-machine", action="store_true",
                    help="make an UNBACKED refdes_waiver.json entry a FAIL "
                         "rather than named debt under the ceiling")
    ap.add_argument("--cited-floor", type=int, default=CITED_FLOOR)
    ap.add_argument("--owed-ceiling", type=int, default=OWED_CEILING)
    ap.add_argument("--machine-ceiling", type=int,
                    default=MACHINE_UNBACKED_CEILING)
    a = ap.parse_args(argv)

    root = Path(a.root)
    if not root.is_dir():
        print(f"FAIL W-SRC: no such directory {root}")
        return 1
    repo_root = Path(a.repo_root).resolve() if a.repo_root \
        else root.resolve().parent

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

    # ---- W-REFS / W-SCHEMA / W-GRADE / W-TOL / W-ARITH / W-REGEN / W-FLIP
    # The evidence pass: a load-bearing number carries a command, and the
    # command is RE-RUN AND DIFFED rather than read as prose.
    tally = {"CITED": [], "UNVERIFIED": [], "ESTIMATED": []}
    owed, carried = [], []
    for name in graded:
        for e, _ in loaded.get(name, []):
            if "_parse_error" in e:
                continue
            where = f"{name} [{e.get('id', '?')}]"
            proj_dir = root / name
            fails.extend(check_refs(e, proj_dir, where))
            ef, items = grade_evidence(e, repo_root, where,
                                       regen=not a.no_regen,
                                       timeout=a.timeout)
            fails.extend(ef)
            if e.get("evidence") is None:
                if _TYPED_MEASURE.search(str(e.get("why", ""))):
                    owed.append(f"{where} — `why` leans on a typed "
                                f"measurement and declares no `evidence:`")
                else:
                    owed.append(f"{where} — no `evidence:` block")
            else:
                carried.append(where)
            for grade, label, detail in items:
                tally[grade].append(f"{label}: {detail}")

    # ---- W-MACHINE: the file the generator writes for itself and the audit
    # then reads as evidence. Every project is scanned, including ones that
    # carry no policy_waivers.yaml at all.
    mach_total, mach_unbacked, mach_backed = 0, [], []
    for name in projects:
        if a.project and name != a.project:
            continue
        refdes, err = machine_waivers(root / name)
        if err:
            fails.append(f"W-MACHINE {name}: {MACHINE_REL} {err}")
            continue
        if refdes is None:
            continue
        named = set()
        for e, _ in loaded.get(name, []):
            refs = e.get("refs") or []
            if isinstance(refs, str):
                refs = [refs]
            named.update(str(r).strip() for r in refs)
        for rd in refdes:
            mach_total += 1
            if rd in named:
                mach_backed.append(f"{name}:{rd}")
            else:
                mach_unbacked.append(
                    f"W-MACHINE {name}: refdes {rd!r} is waived by "
                    f"{MACHINE_REL}, which generate_board_generic.py WRITES "
                    f"and policy_audit.py:793 then READS as evidence for "
                    f"P-SILK-REF, and no entry in {WAIVER_REL} names it in "
                    f"`refs:` — the machine is its own witness (canon M1)")
    if a.strict_machine:
        fails.extend(mach_unbacked)

    # G-INPUT: name the tree and the files actually read. The whole check is a
    # fleet-wide comparison, so WHICH projects were in scope is the verdict.
    print(f"input: root = {root.resolve()}  "
          f"({len(projects)} project dir(s), reading {', '.join(rels)})")
    n_waivers = sum(len(v) for v in loaded.values())
    print(f"input: {len(loaded)} project(s) carry waivers, "
          f"{n_waivers} waiver(s) total; grading "
          f"{len(graded)}: {', '.join(graded) or '(none)'}")

    n_ev_items = sum(len(v) for v in tally.values())
    print(f"input: evidence regeneration "
          f"{'OFF (--no-regen)' if a.no_regen else 'ON'}, cwd for commands = "
          f"{repo_root}, per-command timeout {a.timeout}s")
    print(f"input: {len(carried)} entry(ies) declare `evidence:` "
          f"({n_ev_items} item(s)); {len(owed)} OWED")

    for o in sorted(set(oks)):
        print("  ok  ", o)
    for label in tally["CITED"]:
        print("  CITED      ", label)
    for label in tally["ESTIMATED"]:
        print("  ESTIMATED  ", label)
    for label in tally["UNVERIFIED"]:
        print("  UNVERIFIED ", label)

    # OWED and UNBACKED are printed BY NAME on every run. That enumeration is
    # the whole difference between this and the state that produced the
    # incident: 16 typed numbers nobody had counted.
    for o in sorted(set(owed)):
        print("  OWED       ", o)
    for m in sorted(set(mach_unbacked)):
        print(("FAIL  " if a.strict_machine else "  UNBACKED   ") + m)

    for f in sorted(set(fails)):
        print("FAIL ", f)

    # ---- the three counting facts, monotone in the direction that matters
    n_cited = len(tally["CITED"])
    if n_cited < a.cited_floor:
        fails.append(
            f"W-FLOOR: {n_cited} CITED evidence item(s), below the committed "
            f"floor of {a.cited_floor} — a citation that used to regenerate no "
            f"longer does, or one was deleted. The floor may only be edited UP")
    if len(owed) > a.owed_ceiling:
        fails.append(
            f"W-FLOOR: {len(owed)} OWED entr(ies) with no `evidence:` block, "
            f"above the committed ceiling of {a.owed_ceiling} — a NEW waiver "
            f"was written with a typed number. The ceiling may only be edited "
            f"DOWN")
    if len(mach_unbacked) > a.machine_ceiling:
        fails.append(
            f"W-FLOOR: {len(mach_unbacked)} machine-waived refdes with no "
            f"project-side evidence, above the committed ceiling of "
            f"{a.machine_ceiling} — the generator waived something new for "
            f"itself. The ceiling may only be edited DOWN")
    for f in sorted(set(fails)):
        if f.startswith("W-FLOOR"):
            print("FAIL ", f)

    print(f"EVIDENCE COVERAGE: {n_cited} CITED / "
          f"{len(tally['ESTIMATED'])} ESTIMATED / "
          f"{len(tally['UNVERIFIED'])} UNVERIFIED across {len(carried)} "
          f"declaring entr(ies); {len(owed)} of "
          f"{len(owed) + len(carried)} entr(ies) OWED "
          f"(floors: CITED >= {a.cited_floor}, OWED <= {a.owed_ceiling})")
    print(f"MACHINE WAIVERS: {len(mach_backed)}/{mach_total} refdes in "
          f"{MACHINE_REL} carry a project-side evidenced entry; "
          f"{len(mach_unbacked)} UNBACKED (ceiling {a.machine_ceiling}, "
          f"{'STRICT — failing' if a.strict_machine else 'named debt'})")

    # G-COVER: how many WAIVERS were graded, not how many findings were
    # printed. A run over zero waivers used to print "PASS (0 fails, 0 ok)",
    # indistinguishable from a clean fleet — and W-COPY needs at least two
    # projects loaded before it can compare anything at all.
    n_graded = sum(len(loaded.get(nm, [])) for nm in graded)
    if n_graded == 0:
        print(f"WAIVER PROVENANCE: FAIL 0/{n_waivers} waivers graded — "
              f"nothing under {root} matched {rels}. A zero denominator is a "
              f"FAIL, never a pass (canon M-COVER); if this tree genuinely "
              f"has no waivers, that is a fact worth stating out loud rather "
              f"than a green verdict")
        return 1
    corpus = (f"{n_graded}/{n_waivers} waiver(s) graded across "
              f"{len(graded)}/{len(loaded)} project(s) carrying waivers")
    if len(loaded) < 2:
        corpus += (" — NOTE: W-COPY compares rationales ACROSS projects and "
                   "only one project carries waivers, so the cross-project "
                   "half of this gate graded nothing")
    print("WAIVER PROVENANCE:", "FAIL" if fails else "PASS",
          f"({len(set(fails))} fails, {len(set(oks))} ok) — {corpus}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
