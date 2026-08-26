#!/usr/bin/env python3
"""ROTATION AUTHORITY AUDIT — grades the rotation TABLE and reports the fleet's
UNSOURCED codes. Canon A-ROT (authority) / A-POL (polarity channel) / M-PROV
(provenance independence).

    jlc_rotation_audit.py --table [PATH]     grade jlc_lcsc_rotations.csv
    jlc_rotation_audit.py --fleet [--root R] per-board UNSOURCED migration report
    jlc_rotation_audit.py --release DIR      one release (or any dir with fab/)

WHY EACH MODE EXISTS
--------------------
`--table` (A-POL + M-PROV). The per-LCSC table is now the ONLY rotation
authority (see jlc_rotation_resolve.py). An authority nobody grades is how the
last one died: six of its rows had been populated FROM `jlc_twin.xform()`, the
very function they were used to check, so every consumer inherited the same
negation and even an external reviewer reading the table was misled by it
(e0d735c, 1b69760). Canon M1 said "checker and checked must not share a
method" and was a PRINCIPLE — nothing could check it. M-PROV makes it
mechanical: a row must carry a DATED MEASUREMENT with a residual, and must not
claim a provenance that is this pipeline's own output.

A-POL's table half is the other thing a fitted number cannot tell you. On
usb-hub-3s-v3's indicator LEDs (C2296/C2297) the pad-NUMBER fit returns 180
with a 17.7x margin — and it is WRONG, because JLC numbers pad 1 = ANODE while
KiCad's `Device:LED` is pin 1 = K. Both libraries draw the cathode WEST, so the
true offset is 0 and a 180 row would ship every indicator dark. A HIGH FIT
MARGIN IS NOT CONFIDENCE: a pad-number fit structurally CANNOT detect a model
whose own numbering differs from ours. Only a NUMBERING-FREE channel can, and
this gate requires that channel to be RECORDED in the row — because a
measurement that is not in the row does not exist (RULE 1; C7719 sat inert for
a day as prose inside another row's evidence, 8f472e1).

`--fleet` is the A-ROT MIGRATION aid. Making UNSOURCED blocking by default WILL
fail boards that were shipping on name-DB guesses — which is the point, but the
transition needs a worklist. This prints, per board, exactly which LCSC codes
have no measured row, which refs they place, and what the (advisory) name DB
would have guessed, so each can be measured and landed as a row.

Exit codes: 0 clean, 1 findings (--table / --release), 2 usage/IO error.
`--fleet` is a REPORT and exits 0 unless `--strict`.
"""
import argparse
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jlc_rotation_resolve import (LCSC_ROT_PATH, cross_check,  # noqa: E402
                                  load_lcsc_rows, load_name_db, name_db_advice)

# --------------------------------------------------------------- A-POL vocab
#: what the `polarity` column may say. DECLARED per row — never inferred from
#: the evidence prose, because inferring it is how a gate learns to agree with
#: whatever is written.
POL_NA = "n/a"                       # not polarized and not 2-pad collinear
POL_TWO = "two-channel"              # a NUMBERING-FREE channel is recorded
POL_ONE = "single-channel"           # none exists -> human order-preview gate
POL_VOCAB = (POL_NA, POL_TWO, POL_ONE)

#: numbering-free channels. Each is a physical feature that exists on BOTH
#: footprints and is decided WITHOUT consulting a pad number, so it cannot be
#: fooled by a library that numbers the terminals the other way round.
CHANNEL_RE = re.compile(
    r"chamfer|chamfered|silk\s|silkscreen|F\.SilkS|pin-?1 (dot|mark|marker)|"
    r"diode (glyph|triangle)|glyph|mounting tab|MP tab|MP mounting|tab row|"
    r"body (outline|asymmetry)|courtyard|notch|lead axis|lead-span|"
    r"numbering direction|numbering-free|F\.Fab chamfer|'\+' on", re.I)

#: prose that means "this part has an orientation fact a pad fit cannot see".
POLARIZED_RE = re.compile(
    r"POLARIZED|polarity|polarised|electrolytic|\bLED\b|\bdiode\b|\bTVS\b|"
    r"cathode|anode|2-pad|two-pad|collinear|keyed|opto", re.I)

#: DISCHARGE for `n/a`. POLARIZED_RE is a substring match and CANNOT SEE A
#: NEGATION, so it fired twice on rows whose evidence said the opposite of what
#: it matched: C7719's "confirmed ..., not assumed" tripped the M-PROV rationale
#: word, and C5158048's "THE PART IS NOT POLARIZED" tripped this one. Wording
#: around it a second time would have taught the table to avoid true words.
#:
#: The fix is shaped as ACCEPT-ON-EVIDENCE rather than reject-on-keyword,
#: because "does this prose contain a negation" is not decidable by regex but
#: "does this row cite a datasheet" is. An `n/a` row may therefore discuss
#: polarity freely -- to record why the part has none, or which tool got it
#: wrong -- PROVIDED it makes a positive unpolarized claim AND cites the
#: manufacturer document that backs it. Both are required: the claim alone is
#: the same unevidenced assertion as `^JST_GH_SM,180`, and the citation alone
#: does not say what the datasheet established.
#:
#: The bar is deliberately a DATASHEET and not a measurement. Symmetry is the
#: one polarity question geometry CANNOT settle -- a part whose pads and marks
#: are symmetric looks identical whether both terminals are cathodes or the die
#: is simply centred (PESD5V0S1BA: pin 1 = K1, pin 2 = K2, sym045 back-to-back
#: zeners, no anode pin brought out -- section 5 Table 2, and NOT the same
#: datasheet's shared SOD323 outline note "the marking bar indicates the
#: cathode", which is boilerplate that cannot distinguish an orientation on a
#: part where BOTH pins are the cathode).
UNPOLARIZED_RE = re.compile(
    r"NOT POLARIZED|not polarized|not polarised|unpolarized|unpolarised|"
    r"both pins are cathodes|both terminals are cathodes|no anode pin|"
    r"electrically (identical|symmetric|symmetrical)|"
    r"bidirectional|symmetric part", re.I)

#: the manufacturer document an `n/a` discharge must cite. A section/table
#: reference or an archived filename -- not the bare word "datasheet", which is
#: a gesture at evidence rather than evidence.
DATASHEET_RE = re.compile(
    r"\.pdf\b|section\s+\d|table\s+\d|datasheet\s+(archived|section|table)|"
    r"sha256-cached", re.I)

#: the human gate a SINGLE-CHANNEL row must name.
HUMAN_GATE_RE = re.compile(r"order[- ]preview", re.I)

#: prose recording that the pad-NUMBER fit and the numbering-free channel gave
#: DIFFERENT answers. That is not a footnote — it is the A-POL alarm firing,
#: and a row that records it must also name the human gate.
DISAGREE_RE = re.compile(r"CHANNELS DISAGREE|channels disagree|falsely|"
                         r"self-contradict|contradiction", re.I)

# ------------------------------------------------------------- M-PROV vocab
#: a DATED measurement is the minimum evidence for an authority row.
DATE_RE = re.compile(r"20\d\d-\d\d-\d\d")
#: ...with a residual/separation number, or an explicit exactness claim.
MEASURE_RE = re.compile(
    r"rms\s*[0-9]*\.?[0-9]+\s*mm|[0-9]*\.?[0-9]+\s*mm\b|EXACT|ALREADY ALIGNED",
    re.I)

#: FORBIDDEN PROVENANCE — the row's number came from the thing the row grades,
#: or from no measurement at all. This is canon M1 with teeth. The exact
#: phrasing of the incident: "THE TABLE WAS POPULATED FROM THE BROKEN CHECKER,
#: so it inherited the negation and each wrong row OVERRODE a correct name-DB
#: entry — strictly worse than no table" (e0d735c).
#: DISCHARGE for the jlc_offset provenance pattern, and ONLY that one.
#: THIRD instance of the same blindness in this file: a substring match cannot
#: tell "this number CAME FROM jlc_offset" from "jlc_offset says 90 and it is
#: WRONG". The M-PROV rationale check already fired on 'assumed' inside
#: "confirmed ..., not assumed", and A-POL fired on 'POLARIZED' inside "THE PART
#: IS NOT POLARIZED". Both were reshaped ACCEPT-ON-EVIDENCE rather than worded
#: around, because wording around it teaches the table to avoid true words.
#:
#: A row recording a REFUTED twin offset is the most valuable kind there is —
#: C192421 (crow-mic-pod-v2 U1) is where jlc_twin says 90 and the pad fit says
#: 270, EXACTLY 180 apart, which is the signature of the handedness bug that
#: negated every twin offset and put six rows of this table 180 out. Forcing
#: that conflict out of the evidence to satisfy a grep would delete the warning
#: precisely where it is most needed.
#:
#: The discharge is deliberately NARROW: it applies to jlc_offset alone and
#: requires an explicit refutation marker. "populated from", "copied from",
#: "as suggested" and the name-DB patterns stay unconditional, because those
#: are unambiguous SOURCING claims with no legitimate refuting use.
REFUTES_RE = re.compile(
    r"\bREFUTED\b|\brefutes?\b|is WRONG|is the outlier|CONFLICT, resolved|"
    r"CHANNELS DISAGREE|does not agree|must not be read as|excluded\b", re.I)

FORBIDDEN_PROV = [
    (re.compile(r"jlc_offset", re.I),
     "cites jlc_twin's own jlc_offset — the table may not be populated from "
     "the checker it grades (canon M1; e0d735c: six rows inherited a negated "
     "operator and each OVERRODE a correct name-DB row)"),
    (re.compile(r"populated from|derived from (the )?(twin|jlc_twin)|"
                r"per (the )?jlc_twin|twin reported|suggested by (the )?"
                r"(twin|jlc_twin)|as suggested", re.I),
     "names this pipeline's own output as the source of the number"),
    (re.compile(r"copied from|inherited from|same as C\d+|by analogy|"
                r"assumed|guessed|presumably|should be|standard for", re.I),
     "is a RATIONALE, not a measurement — a row copied or reasoned into "
     "existence is an inherited defect (canon M4)"),
    (re.compile(r"(taken|read) from the name[- ]?DB", re.I),
     "took the number from the advisory name DB, which is exactly the "
     "authority A-ROT retired"),
]


class Finding(str):
    """A graded problem. `str` so callers can just print it."""


# --------------------------------------------------------------------------
def grade_table(path=None):
    """Grade the per-LCSC rotation table. Returns (findings, n_rows)."""
    p = Path(path) if path else LCSC_ROT_PATH
    if not p.exists():
        return [Finding(f"M-PROV: no rotation table at {p}")], 0
    rows = load_lcsc_rows(p)
    name_db = load_name_db()
    out = []
    for code, row in sorted(rows.items()):
        ev = row["evidence"]
        pol = (row["polarity"] or "").lower()
        where = f"{code} (line {row['lineno']})"

        # ---- M-PROV: the authority must be independently MEASURED
        if len(ev) < 40:
            out.append(Finding(
                f"M-PROV {where}: evidence is {len(ev)} chars — an authority "
                f"row needs the MEASUREMENT (fit residual + next-best "
                f"separation + date), not a label"))
        else:
            if not DATE_RE.search(ev):
                out.append(Finding(
                    f"M-PROV {where}: evidence carries no measurement DATE "
                    f"(YYYY-MM-DD) — an undated row cannot be re-verified "
                    f"against the model it was fitted to"))
            if not MEASURE_RE.search(ev):
                out.append(Finding(
                    f"M-PROV {where}: evidence carries no residual/separation "
                    f"figure — 'measured' without a number is a claim"))
            for pat, why in FORBIDDEN_PROV:
                m = pat.search(ev)
                # narrow discharge: a row may NAME jlc_twin's offset in order to
                # REFUTE it, provided it says so explicitly (see REFUTES_RE).
                if m and m.group(0).lower() == "jlc_offset" \
                        and REFUTES_RE.search(ev):
                    continue
                if m:
                    out.append(Finding(
                        f"M-PROV {where}: evidence {why} (matched "
                        f"{m.group(0)!r}). Re-derive the offset from the BOARD "
                        f"plus JLC's cached model with an operator verified "
                        f"against pcbnew itself, and rewrite the row"))

        # ---- A-POL: a polarized / 2-pad part needs a NUMBERING-FREE channel
        if pol not in POL_VOCAB:
            out.append(Finding(
                f"A-POL {where}: polarity column is {row['polarity']!r} — "
                f"must be one of {list(POL_VOCAB)}. Silence is not a "
                f"declaration"))
        elif pol == POL_NA and POLARIZED_RE.search(ev) \
                and not (UNPOLARIZED_RE.search(ev) and DATASHEET_RE.search(ev)):
            m = POLARIZED_RE.search(ev)
            has_claim = UNPOLARIZED_RE.search(ev)
            missing = ("cites no manufacturer document (a section/table "
                       "reference or an archived .pdf) for that claim"
                       if has_claim else
                       "makes no positive unpolarized claim at all")
            out.append(Finding(
                f"A-POL {where}: declared {POL_NA!r} but its own evidence says "
                f"{m.group(0)!r}, and {missing}. A pad-NUMBER fit cannot see a "
                f"library that numbers the terminals the other way round "
                f"(C2296/C2297: fit 180 at a 17.7x margin, true offset 0) — "
                f"declare {POL_TWO!r} or {POL_ONE!r}, or discharge {POL_NA!r} "
                f"with BOTH an explicit unpolarized statement AND the datasheet "
                f"that establishes it (symmetry is the one polarity question "
                f"geometry cannot settle)"))
        elif pol == POL_TWO and not CHANNEL_RE.search(ev):
            out.append(Finding(
                f"A-POL {where}: declared {POL_TWO!r} but the evidence names "
                f"no NUMBERING-FREE channel (silk chamfer, pin-1 dot/glyph, "
                f"mounting-tab position, body/courtyard asymmetry, lead axis). "
                f"A measurement that is not in the ROW does not exist "
                f"(RULE 1, 8f472e1)"))
        elif pol == POL_TWO and DISAGREE_RE.search(ev) \
                and not HUMAN_GATE_RE.search(ev):
            out.append(Finding(
                f"A-POL {where}: the evidence records that the two channels "
                f"DISAGREED, which is the A-POL alarm itself — the row must "
                f"ALSO name the JLC ORDER-PREVIEW human gate. A disagreement "
                f"resolved on paper and never looked at is how a 17.7x-margin "
                f"fit ships every indicator LED dark"))
        elif pol == POL_ONE and not HUMAN_GATE_RE.search(ev):
            out.append(Finding(
                f"A-POL {where}: declared {POL_ONE!r} but the evidence does "
                f"not name the JLC ORDER-PREVIEW human gate. A row with no "
                f"numbering-free channel is carried by a human eye or by "
                f"nothing"))

        # ---- the free signal: exactly-180 disagreement with the name DB.
        # DISCHARGED only by a declared NUMBERING-FREE channel, because that is
        # the one instrument that can answer a 180 question without consulting
        # a pad number. `n/a` and `single-channel` rows leave it OPEN.
        if pol != POL_TWO:
            adv, adv_pat = name_db_advice_for_row(ev, name_db)
            if adv is not None:
                for fid, text in cross_check(row["offset"], adv, adv_pat,
                                             "", code):
                    if fid == "ROT-XCHECK-180":
                        out.append(Finding(
                            f"{fid} {where}: {text} Declare {POL_TWO!r} with "
                            f"the channel recorded once a numbering-free "
                            f"feature has adjudicated it"))
    return out, len(rows)


def name_db_advice_for_row(evidence, name_db):
    """Best-effort footprint name for a table row: the evidence prose names the
    footprint it was fitted against. Returns (offset, pattern) or (None, None).

    Deliberately BEST-EFFORT and advisory-only: a row that does not name its
    footprint simply gets no cross-check, and no cross-check is never a pass —
    the M-PROV/A-POL grades above stand on their own.
    """
    for tok in re.findall(r"[A-Za-z][A-Za-z0-9_.\-]{5,}", evidence or ""):
        off, pat = name_db_advice(tok, name_db)
        if off is not None:
            return off, pat
    return None, None


# --------------------------------------------------------------------------
def read_fab(fab_dir):
    """(cpl_rows, ref->lcsc) from a fab/ directory. Accepts the sealed
    `bom.csv`/`cpl.csv` names and the exporter's `bom_jlc.csv`/`cpl_jlc.csv`."""
    d = Path(fab_dir)
    cpl_p = next((d / n for n in ("cpl.csv", "cpl_jlc.csv") if (d / n).exists()),
                 None)
    bom_p = next((d / n for n in ("bom.csv", "bom_jlc.csv") if (d / n).exists()),
                 None)
    if cpl_p is None:
        return [], {}
    cpl = list(csv.DictReader(open(cpl_p, encoding="utf-8-sig")))
    ref2code = {}
    if bom_p is not None:
        for row in csv.DictReader(open(bom_p, encoding="utf-8-sig")):
            code = (row.get("LCSC") or "").strip()
            for r in (row.get("Designator") or "").split(","):
                if r.strip():
                    ref2code[r.strip()] = code
    return cpl, ref2code


def exempt_refs(board_path):
    """{refdes} whose footprint MEASURES as its own 180-degree reflection.

    Optional and lazy: needs pcbnew. Without it the report simply lists more
    codes, which is the safe direction for a worklist. The GATE itself
    (export_jlc_package.py) always measures — the report never decides.
    """
    try:
        import pcbnew
        from jlc_footprint_symmetry import symmetry
    except Exception:
        return None
    try:
        b = pcbnew.LoadBoard(str(board_path))
    except Exception:
        return None
    if b is None:
        return None
    return {fp.GetReference() for fp in b.GetFootprints()
            if symmetry(fp)["exempt"]}


def audit_fab(fab_dir, lcsc_table, name_db, exempt=None):
    """Return {lcsc_or_'': {"refs": [...], "packages": {...}, "advice": ...}}
    for every CPL row whose code has NO measured per-LCSC row and whose
    footprint is not MEASURED 180-symmetric."""
    cpl, ref2code = read_fab(fab_dir)
    unsourced = {}
    for row in cpl:
        ref = (row.get("Designator") or "").strip()
        pkg = (row.get("Package") or "").strip()
        code = ref2code.get(ref, "")
        if code and code in lcsc_table:
            continue
        if exempt is not None and ref in exempt:
            continue
        e = unsourced.setdefault(code, {"refs": [], "packages": set(),
                                        "advice": None, "advice_pat": None})
        e["refs"].append(ref)
        e["packages"].add(pkg)
        if e["advice"] is None:
            e["advice"], e["advice_pat"] = name_db_advice(pkg, name_db)
    return unsourced, len(cpl)


def fleet_report(root, lcsc_table, name_db, out=sys.stdout):
    """Per-board UNSOURCED report over active and frozen project history."""
    root = Path(root)
    boards = []
    projects = {}
    for collection in ("projects", "archived_projects"):
        base = root / collection
        for proj in sorted(base.glob("*")) if base.is_dir() else []:
            if not proj.is_dir():
                continue
            if proj.name in projects:
                raise RuntimeError(
                    f"duplicate project slug {proj.name!r}: "
                    f"{projects[proj.name]} and {proj}")
            projects[proj.name] = proj
    for proj in (projects[name] for name in sorted(projects)):
        if not proj.is_dir():
            continue
        rels = sorted((proj / "07_releases").glob("*/fab")) if \
            (proj / "07_releases").is_dir() else []
        builds = sorted(proj.glob("06_build/fab"))
        for fab in rels + builds:
            boards.append(fab)
    total_codes, total_refs = set(), 0
    print("A-ROT MIGRATION REPORT — CPL rows with no MEASURED per-LCSC "
          "rotation row", file=out)
    print("(each is a cell the pre-A-ROT resolver filled from a footprint-NAME "
          "guess or from 0.0)", file=out)
    print("Footprints that MEASURE as their own 180-degree reflection are "
          "exempt and excluded here — measured\nfrom the project's 04_kicad "
          "board when one is readable, never from the package NAME.\n",
          file=out)
    ex_cache = {}
    for fab in boards:
        proj = next((p for p in fab.parents if (p / "04_kicad").is_dir()),
                    fab.parent)
        if proj not in ex_cache:
            bl = sorted((proj / "04_kicad").glob("*.kicad_pcb")) \
                if (proj / "04_kicad").is_dir() else []
            ex = set()
            for b in bl:
                ex |= (exempt_refs(b) or set())
            ex_cache[proj] = ex or None
        uns, n_cpl = audit_fab(fab, lcsc_table, name_db, ex_cache[proj])
        rel = fab.relative_to(root)
        if not n_cpl:
            continue
        n_bad = sum(len(v["refs"]) for v in uns.values())
        print(f"{rel}", file=out)
        print(f"  CPL rows {n_cpl};  UNSOURCED {n_bad} rows / "
              f"{len(uns)} codes", file=out)
        for code, e in sorted(uns.items()):
            adv = ("name-DB would guess %g (%s)" % (e["advice"], e["advice_pat"])
                   if e["advice"] is not None else
                   "NO name-DB rule either -> pre-A-ROT default was 0.0")
            refs = ",".join(sorted(e["refs"])[:8])
            more = "" if len(e["refs"]) <= 8 else f" (+{len(e['refs']) - 8} more)"
            print(f"    {code or '(NO LCSC)':<12} x{len(e['refs']):<3} "
                  f"{'/'.join(sorted(e['packages']))[:44]:<46} {adv}",
                  file=out)
            print(f"       refs: {refs}{more}", file=out)
            if code:
                total_codes.add(code)
            total_refs += len(e["refs"])
        print("", file=out)
    print(f"FLEET TOTAL: {len(total_codes)} distinct LCSC codes unsourced "
          f"across {total_refs} CPL rows", file=out)
    print("Each needs ONE measured row in jlc_lcsc_rotations.csv: fit the "
          "board footprint against JLC's cached model with a pcbnew-verified "
          "operator, and record residual + next-best separation + date.",
          file=out)
    return len(total_codes)


# --------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--table", nargs="?", const="", default=None,
                    help="grade the per-LCSC rotation table (A-POL + M-PROV)")
    ap.add_argument("--fleet", action="store_true",
                    help="per-board UNSOURCED migration report")
    ap.add_argument("--release", default="",
                    help="grade ONE release/project dir (looks for fab/)")
    ap.add_argument("--root", default="",
                    help="repo root for --fleet (default: walk up from here)")
    ap.add_argument("--strict", action="store_true",
                    help="--fleet exits 1 when anything is unsourced")
    args = ap.parse_args(argv)

    if args.table is None and not args.fleet and not args.release:
        ap.error("pick one of --table / --fleet / --release")

    rc = 0
    if args.table is not None:
        finds, n = grade_table(args.table or None)
        if finds:
            print(f"ROTATION-TABLE FAIL: {len(finds)} findings over {n} rows")
            for f in finds:
                print(f"  {f}")
            rc = 1
        else:
            print(f"ROTATION-TABLE OK: {n} rows, each an independently "
                  f"MEASURED authority (M-PROV) with its polarity channel "
                  f"declared (A-POL)")

    if args.fleet or args.release:
        table = {c: r["offset"] for c, r in load_lcsc_rows().items()}
        name_db = load_name_db()
        if args.release:
            base = Path(args.release)
            fab = base / "fab" if (base / "fab").is_dir() else base
            # Match the exporter's one valid exemption: reopen the exact
            # release board and measure 180-degree pad+graphics symmetry.
            # The old --release path omitted this argument, so a package the
            # exporter correctly accepted was re-reported as 130/179
            # UNSOURCED rows (mostly chip passives).  A downstream audit may
            # not silently grade a stricter, different population.
            board_hits = sorted((base / "source").glob("*.kicad_pcb"))
            if not board_hits:
                board_hits = sorted(base.glob("04_kicad/*.kicad_pcb"))
            exempt = exempt_refs(board_hits[0]) if len(board_hits) == 1 else None
            uns, n_cpl = audit_fab(fab, table, name_db, exempt)
            if not n_cpl:
                print(f"A-ROT N-A: no CPL under {fab}")
                return rc
            n_bad = sum(len(v["refs"]) for v in uns.values())
            if uns:
                print(f"A-ROT FAIL: {n_bad}/{n_cpl} CPL rows have NO measured "
                      f"per-LCSC rotation row ({len(uns)} codes):")
                for code, e in sorted(uns.items()):
                    print(f"  {code or '(NO LCSC)'}: "
                          f"{','.join(sorted(e['refs']))}")
                rc = 1
            else:
                print(f"A-ROT OK: all {n_cpl} CPL rotations resolve from a "
                      f"MEASURED per-LCSC row or exact-board measured "
                      f"180-degree symmetry")
        else:
            root = Path(args.root) if args.root else \
                Path(__file__).resolve().parents[3]
            n = fleet_report(root, table, name_db)
            if n and args.strict:
                rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
