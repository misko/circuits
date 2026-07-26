"""Shared JLC CPL-rotation resolution for the exporter and the twin (canon A-ROT).

THE CLASS THIS FILE EXISTS TO KILL
----------------------------------
In one day (2026-07-25) this fleet found rotation defects on FIVE boards —
22 wrong CPL rotations on smc0985-cooksense alone, across two SEALED releases.
Every one of them was the SAME root cause wearing a different mask:

    ROTATION AUTHORITY WAS INHERITED BY PATTERN-MATCHING A FOOTPRINT *NAME*,
    AND A NAME IS NOT A PART.

Five distinct mechanisms, all from that one root (commits 8f472e1, e0d735c,
9078ad9, 95a8180, 95317d5, a7329c1, 99c739c, 1648979):

  (a) WRONG KEY      C79924 and C7719 are both `SOT-23-5` and need 180 vs 270.
                     One name, two answers — the key cannot hold the fact.
  (b) NEGATED OFFSET `jlc_twin.xform()` used the wrong handedness (in FIVE
                     copies), and the per-LCSC table was POPULATED FROM the
                     broken checker: six rows were 180 out and each OVERRODE a
                     correct name-DB row. Canon M1, collecting.
  (c) NO RULE FIRED  C98732 (XT60, a VENDORED footprint name) and C125121
                     (LTV-817S opto) matched nothing and silently defaulted to
                     0.0. Silence is the quietest failure mode.
  (d) PARTIAL PREFIX `^SOT-23` swallowed `SOT-23-6`, putting TEN safety-chain
                     AND gates 90 deg out on a cooking interlock.
  (e) UNEVIDENCED    `^JST_GH_SM,180` was simply wrong — EIGHT connectors 180
                     out on two sealed releases. Nobody ever measured it.

THE FIX, AND WHY IT IS ONE CHANGE RATHER THAN FIVE
--------------------------------------------------
Rung 1 (the per-LCSC MEASURED table) is kept as the ONLY authority. A footprint
name-DB match is now ADVISORY ONLY: it can inform a finding, it can never
decide a CPL cell. A part with no per-LCSC row resolves UNSOURCED, which is
BLOCKING — not 0.0, not a name-DB guess.

That single change kills (a), (c), (d) and (e) outright:
  - no key to get wrong: the LCSC code IS the part's identity;
  - no prefixes to over-match: there is no prefix matching left on the
    authority path;
  - silence becomes a FAIL instead of a default.
And it contains (b), because the only way into the table is a MEASUREMENT with
an operator verified against something outside this pipeline (RULE 2 in
`jlc_lcsc_rotations.csv`; graded by `jlc_rotation_audit.py --table`, canon
M-PROV).

THE FREE SIGNAL WE WERE THROWING AWAY
-------------------------------------
When a MEASURED offset disagrees with the name DB by EXACTLY 180 degrees, that
is not "the DB is stale". `formB(a) == formA(-a)` IDENTICALLY, and both forms
are the identity's own reflection at 0/180 — so a handedness error is
invisible at 0/180 and EXACTLY 180 wrong at 90/270. An exact-180 disagreement
is therefore the SIGNATURE OF A HANDEDNESS ERROR in whichever side produced
the number. That signature was on screen for weeks and was read as staleness
(see `git show e0d735c^`). It costs one comparison, and it was already
sufficient to catch the incident. `cross_check()` now says so, out loud, in
the finding text.

No pcbnew dependency: the exporter (`export_jlc_package.py`), the twin
(`jlc_twin.py`) and the auditor (`jlc_rotation_audit.py`) all import this, and
it is unit-testable with plain python3.
"""
import csv
import os
import re
from collections import namedtuple
from pathlib import Path

HERE = Path(__file__).parent

#: the MEASURED authority table. Overridable by env so a TEST can construct its
#: own unsourced state instead of borrowing a real project's defect.
#:
#: WHY THIS EXISTS (2026-07-26). Two known-bad fixtures asserted that A-ROT
#: BLOCKS the usb-hub-3s-v3 export, and both EXPIRED the moment the board's 14
#: missing rows were measured and landed: the export now reports "A-ROT OK: all
#: 119 CPL rotations are sourced", so the gate could no longer be made to fail
#: and the fixtures failed instead. A known-bad fixture that depends on a LIVE
#: PROJECT being broken has an expiry date, and it expires exactly when someone
#: does the right thing — which is the worst possible moment to lose the proof
#: that a gate can fail. Point this at a deliberately-reduced table and the
#: unsourced state is synthetic, permanent, and owned by the test.
LCSC_ROT_PATH = Path(os.environ.get("JLC_LCSC_ROTATIONS",
                                    HERE / "jlc_lcsc_rotations.csv"))
NAME_DB_PATH = HERE / "jlc_rotations_db.csv"

# resolution sources. There is no "name" source any more — that is the point.
SRC_LCSC = "lcsc"
SRC_UNSOURCED = "unsourced"

#: (finding_id, text) pairs emitted by resolve()/cross_check().
F_UNSOURCED = "ROT-UNSOURCED"
F_HANDEDNESS = "ROT-XCHECK-180"
F_DISAGREE = "ROT-XCHECK"

Resolution = namedtuple(
    "Resolution", "cpl offset source blocking advice advice_pattern findings")


def load_lcsc_rotations(path=None):
    """Return {LCSC: offset_deg} from the per-LCSC rotation table.

    Populate ONLY with codes whose exact pad-fit was MEASURED against JLC's own
    cached model with an operator verified against an authority OUTSIDE this
    pipeline (cite the fit + residual in the `evidence` column). A guessed row
    is worse than none: it is now the ONLY authority there is.
    """
    return {code: row["offset"] for code, row in load_lcsc_rows(path).items()}


def load_lcsc_rows(path=None):
    """Return {LCSC: {"offset": float, "evidence": str, "polarity": str,
    "lineno": int}} — the same rows as load_lcsc_rotations() but with the
    metadata `jlc_rotation_audit.py` grades (canon A-POL / M-PROV).

    Rows whose key starts with `#` are RULE/refutation prose, skipped here.
    """
    rows = {}
    p = Path(path) if path else LCSC_ROT_PATH
    if not p.exists():
        return rows
    with open(p) as f:
        for i, row in enumerate(csv.DictReader(f), start=2):
            code = (row.get("LCSC") or "").strip()
            rot = (row.get("rotation") or "").strip()
            if not code or not rot or code.startswith("#"):
                continue
            try:
                off = float(rot)
            except ValueError:
                continue
            rows[code] = {"offset": off,
                          "evidence": (row.get("evidence") or "").strip(),
                          "polarity": (row.get("polarity") or "").strip(),
                          "lineno": i}
    return rows


def load_name_db(path=None):
    """Return [(compiled_pattern, offset, pattern_text)] — the ADVISORY
    footprint-NAME DB.

    ONE loader, so the exporter and the auditor cannot disagree about what the
    file says. The table documents refuted rules by DISABLING THEM IN PLACE —
    a `#`-prefixed key plus prose continuation lines carrying the measurement
    (2026-07-25, `^JST_GH_SM`). Those continuation rows parse as [text, ""] and
    `float("")` raises ValueError; an earlier loader caught only `re.error`,
    so annotating a rule HARD-CRASHED the fab export for every board. A comment
    in a data file must never be able to stop a board shipping.
    """
    db = []
    p = Path(path) if path else NAME_DB_PATH
    if not p.exists():
        return db
    with open(p) as f:
        for row in csv.reader(f):
            if len(row) < 2 or not row[0] or row[0].startswith(("Footprint", "#")):
                continue
            try:
                db.append((re.compile(row[0]), float(row[1]), row[0]))
            except (re.error, ValueError):
                pass
    return db


def name_db_advice(fpname, name_db):
    """(offset, pattern_text) of the first matching ADVISORY name-DB rule, or
    (None, None). Accepts both the 2-tuple and 3-tuple row forms so a caller
    holding a legacy [(pat, off)] list still works."""
    for entry in name_db or []:
        pat, off = entry[0], entry[1]
        text = entry[2] if len(entry) > 2 else getattr(pat, "pattern", "")
        if pat.search(fpname):
            return off, text
    return None, None


def cross_check(measured, advice, advice_pattern, fpname="", lcsc=""):
    """Compare a MEASURED per-LCSC offset against the advisory name DB.

    Returns a list of (finding_id, text). Empty when they agree, or when the
    name DB has nothing to say.

    The EXACTLY-180 case is called out by name. It is not a stale row: it is
    the arithmetic signature of a handedness error, because the two candidate
    rotation forms satisfy `formB(a) == formA(-a)` identically and coincide at
    0/180. Whichever side produced the number, that side's operator is the
    thing to go and measure against pcbnew — not the row.
    """
    if advice is None:
        return []
    delta = round((measured - advice) % 360, 1)
    who = f"{lcsc or '?'} ({fpname or '?'})"
    if delta == 0:
        return []
    if delta == 180:
        return [(F_HANDEDNESS,
                 f"{who}: MEASURED offset {measured:g} vs advisory name-DB "
                 f"{advice:g} (rule {advice_pattern!r}) — EXACTLY 180 apart. "
                 f"An exact 180 is NEVER 'the DB is stale'. It has exactly "
                 f"two causes and both are P0s: (1) A NEGATED ROTATION "
                 f"OPERATOR — formB(a) == formA(-a) identically, so a "
                 f"handedness error is invisible at 0/180 and exactly 180 "
                 f"wrong at 90/270; verify the operator that produced each "
                 f"number against pcbnew itself (pad.GetFPRelativePosition() "
                 f"vs pad.GetPosition()) before trusting either (e0d735c: "
                 f"read as staleness for weeks). (2) OPPOSITE PAD-1 "
                 f"CONVENTION on a symmetric part — the two libraries number "
                 f"the terminals the other way round, which a pad-NUMBER fit "
                 f"structurally cannot see (a7329c1: the CP_Elec_6.3x7.7 rule "
                 f"encodes a different vendor's pad 1, so EVERY part it "
                 f"resolves is 180 out). Resolve with a NUMBERING-FREE "
                 f"channel (canon A-POL), never with the fit margin")]
    return [(F_DISAGREE,
             f"{who}: MEASURED offset {measured:g} vs advisory name-DB "
             f"{advice:g} (rule {advice_pattern!r}) — {delta:g} apart. The "
             f"MEASUREMENT wins (the name DB is advisory); if the rule is "
             f"wrong for this family, refute it IN PLACE in "
             f"jlc_rotations_db.csv with the measurement")]


def resolve(fpname, board_rot, lcsc, name_db, lcsc_table):
    """Resolve the JLC CPL rotation for one part. Returns a `Resolution`.

    `Resolution.source` is `lcsc` (a MEASURED per-LCSC row — the only
    authority) or `unsourced` (no row: **BLOCKING**). `Resolution.blocking` is
    True exactly when the part is unsourced.

    `advice` / `advice_pattern` carry what the footprint-NAME DB would have
    said. It is reported, cross-checked, and never obeyed.
    """
    advice, advice_pat = name_db_advice(fpname, name_db)
    if lcsc and lcsc in lcsc_table:
        off = lcsc_table[lcsc]
        return Resolution(round((board_rot + off) % 360, 1), off, SRC_LCSC,
                          False, advice, advice_pat,
                          cross_check(off, advice, advice_pat, fpname, lcsc))
    hint = ""
    if advice is not None:
        hint = (f" The advisory name-DB rule {advice_pat!r} would have said "
                f"{advice:g} — that is a HINT for the measurement, NEVER the "
                f"answer (^JST_GH_SM,180 was unevidenced and put EIGHT "
                f"connectors 180 out; ^SOT-23 swallowed SOT-23-6 and put TEN "
                f"safety gates 90 out).")
    else:
        hint = (" No name-DB rule matches either — the pre-A-ROT resolver "
                "would have silently shipped this part at offset 0 (the "
                "C98732 XT60 / C125121 opto class).")
    return Resolution(
        round(board_rot % 360, 1), 0.0, SRC_UNSOURCED, True, advice,
        advice_pat,
        [(F_UNSOURCED,
          f"{lcsc or '(no LCSC)'} ({fpname}): NO measured per-LCSC rotation "
          f"row. The CPL cell cannot be sourced, so it is BLOCKED rather than "
          f"defaulted.{hint} FIX: measure the offset against JLC's cached "
          f"model with a pcbnew-verified operator and add a row to "
          f"jlc_lcsc_rotations.csv citing the fit residual + separation.")])


def resolve_rotation(fpname, board_rot, lcsc, name_db, lcsc_table):
    """Back-compatible 3-tuple form: (cpl_rotation, offset, source).

    `source` is "lcsc" or "unsourced" — it is NEVER "name" any more. Callers
    that only want the number must still treat "unsourced" as blocking; use
    `resolve()` to get the findings text.
    """
    r = resolve(fpname, board_rot, lcsc, name_db, lcsc_table)
    return r.cpl, r.offset, r.source
