#!/usr/bin/env python3
"""bom_legibility_check.py — canon F-LEGIBLE: grade the BOM AS JLC PARSES IT.

    bom_legibility_check.py TARGET [--parts DIR] [--ledger Y] [--json OUT]
    bom_legibility_check.py TARGET --echo JLC_RESOLVED.csv        # F-ECHO

TARGET is a sealed release directory (`07_releases/<ver>-<date>/`, opened
READ-ONLY, graded via `fab/bom.csv`), a project directory, or a BOM csv path.

WHY THIS EXISTS (ADR-0006). Every BOM check this repo owned asked "is this value
CORRECT?" — `bom_source_check` legs A/B/C, A-POP, A-ROT, A-STOCK. All semantic,
all judged by our own lights. **Not one asked whether the RECIPIENT can PARSE
the file.** That is canon M1 again, and it is the F-PAYLOAD lesson of ADR-0004
(nothing had ever read the gerber the way the fab reads it) moved from the
copper to the BOM. crow-recorder-central-v2 v1.5's BOM was uploaded and the
parts "were not being picked up by their web processing".

MEASURED FLEET-WIDE BEFORE THIS GATE EXISTED (26 sealed `fab/bom.csv`,
1205 rows):

  * 914 / 1205 rows carry a BLANK MPN (counting only the 25 files that HAVE an
    MPN column; 962 / 1205 counting the file that has no such column at all).
  * 470 / 1205 rows have a Comment that is an LCSC CODE or a `simple_*`
    generator placeholder — a row no human on either side can review.
  * 23 / 26 files contain non-ASCII (`Ω`, U+03A9, 303 occurrences) with NO
    UTF-8 byte-order-mark. Nothing is corrupt; a reader defaulting to cp936
    renders `CE A9` as `惟`, which is what the user saw.

THE THREE MECHANICAL CHECKS.

  F-MPN     every CODED row carries BOTH an MPN and an LCSC, and the MPN
            AGREES with the authoritative resolution of its code. Two
            independent match paths, so a stale or merged code cannot kill a
            row silently — redundancy as design.
  F-WORDS   the Comment column is a human-readable value: never an LCSC code,
            never a `simple_*` placeholder, never blank.
  F-ENCODE  the file decodes IDENTICALLY under UTF-8 and under the recipient's
            likely default (cp936). The check is INDIFFERENT to how that is
            achieved — a UTF-8 BOM and ASCII `Ohm` both pass.

AND ONE HUMAN-GATED CHECK, `--echo`.

  F-ECHO    JLC's RESOLVED BOM diffed back against ours; a substitution is a
            FINDING. Our source says C82317 for crow-recorder-central-v2's U5
            in three places (part.yaml, the .tsx, the shipped BOM); JLC's
            resolved output said **C131025**. It redirected our code to a
            different one and we had no mechanism to notice. This half stays
            human-gated ON PURPOSE (ADR-0006 "NOT built"): the human performs
            the upload and saves JLC's resolved table, this script does the
            diff. No API integration, no credentials — the same line already
            drawn on the Mouser/Nexar APIs.

WHERE THE AUTHORITY COMES FROM, AND WHY THAT IS STILL CANON M1. The MPN is
resolved from `02_parts/<MPN>/part.yaml` (the part's own `mpn:` field, falling
back to the directory name) and then from the vetted
`references/lcsc_passives_ledger.yaml` — both HAND-VERIFIED artifacts, neither
produced by this pipeline's exporter (canon M-PROV). The GRADED artifact is the
SHIPPED bom.csv bytes (canon M-SHIP). `export_jlc_package.py` imports the
resolver from this file so exporter and checker cannot disagree about what the
authority SAYS — the same "ONE loader" arrangement `jlc_rotation_resolve.py`
already has with the rotation table — but it is the loader that is shared, not
the grading: the checker re-derives every MPN from the authority and compares it
to bytes the exporter has no further say over.

COVERAGE IS PART OF THE VERDICT (canon G-COVER/M-COVER). Every check reports
`N graded / M total`, a row this parser cannot classify is a FAIL rather than a
skip, and a zero denominator is a FAIL. `mpn_map.get(code, "")` — the silent
default this replaces — is the exact `row_kind` shape M-COVER forbids.
"""
import argparse
import codecs
import csv
import json
import re
import sys
from collections import namedtuple
from pathlib import Path

try:
    import yaml
except ImportError:                                       # pragma: no cover
    yaml = None

LCSC_RE = re.compile(r"C\d+")

#: the recipient's likely default codepage. JLC's web processing is a Chinese
#: stack; cp936/GBK is the default that renders `CE A9` as the mojibake the
#: user actually reported. Named as a constant so the choice is auditable.
RECIPIENT_CODEC = "cp936"

LEDGER_PATH = (Path(__file__).resolve().parent.parent
               / "references" / "lcsc_passives_ledger.yaml")

MpnRes = namedtuple("MpnRes", "mpn value source")


# ============================================================ the authority ==
def load_part_mpns(parts_dir):
    """{lcsc: MpnRes} from `02_parts/<MPN>/part.yaml`.

    THE DIRECTORY NAME IS *ALMOST* THE MPN, and the difference matters. ADR-0006
    says "the DIRECTORY NAME IS THE MPN"; MEASURED over this fleet's 200+
    dossiers that is true for most and FALSE for every MPN containing a slash,
    which cannot appear in a path: `02_parts/SMD2920-700/` declares
    `mpn: SMD2920-700/16N` and `02_parts/LM5116MHX-NOPB/` declares
    `mpn: LM5116MHX/NOPB`. Shipping the directory name for those two would put a
    STRING THAT IS NOT THE PART NUMBER in the column whose whole job is to be
    the exact part number. The `mpn:` FIELD is authoritative; the directory name
    is the fallback for a dossier that omits it.

    Alternates are carried too, keyed by their own code: an alternate is not a
    promise to order that part, but if a BOM row DOES carry the alternate's
    code, the alternate's MPN is the right answer for it.
    """
    parts_dir = Path(parts_dir)
    if not parts_dir.is_dir() or yaml is None:
        return {}
    out = {}
    for y in sorted(parts_dir.glob("*/part.yaml")):
        try:
            d = yaml.safe_load(y.read_text(encoding="utf-8-sig")) or {}
        except Exception:                                 # noqa: BLE001
            continue
        if not isinstance(d, dict):
            continue
        mpn = str(d.get("mpn") or y.parent.name).strip()
        src = d.get("sourcing") or {}
        if not isinstance(src, dict):
            src = {}
        code = str(src.get("lcsc") or "").strip()
        if LCSC_RE.fullmatch(code) and mpn:
            out.setdefault(code, MpnRes(mpn, _declared_value(d),
                                        f"02_parts/{y.parent.name}"))
        for alt in (src.get("alternates") or []):
            if not isinstance(alt, dict):
                continue
            ac = str(alt.get("lcsc") or "").strip()
            am = str(alt.get("mpn") or mpn).strip()
            if LCSC_RE.fullmatch(ac) and am:
                out.setdefault(ac, MpnRes(am, _declared_value(d),
                                          f"02_parts/{y.parent.name} (alt)"))
    return out


def _declared_value(part_yaml):
    """A human-readable value from a part dossier, or '' — best effort.

    Only used to make a Comment LEGIBLE; never to grade a value (that is leg C
    of `bom_source_check`, which owns the semantic comparison).
    """
    for a in (part_yaml.get("asserts") or []):
        if isinstance(a, dict) and a.get("assert") == "value" and a.get("equals"):
            return str(a["equals"]).strip()
    return ""


def load_ledger_mpns(path=None):
    """{lcsc: MpnRes} from the vetted passives ledger (catalog-verified ONCE).

    LOAD-BEARING, not a nicety: basic-library passives have no `02_parts`
    dossier at all. MEASURED over the fleet's 1175 coded rows — 562 resolve
    from `02_parts`, 579 ONLY from this ledger, 34 from neither. Without it,
    F-MPN would condemn half the fleet for a fact the repo already knows.
    """
    p = Path(path) if path else LEDGER_PATH
    if not p.is_file() or yaml is None:
        return {}
    try:
        d = yaml.safe_load(p.read_text(encoding="utf-8-sig")) or {}
    except Exception:                                     # noqa: BLE001
        return {}
    out = {}
    for code, e in (d.items() if isinstance(d, dict) else []):
        if isinstance(e, dict) and e.get("mpn"):
            out[str(code).strip()] = MpnRes(str(e["mpn"]).strip(),
                                            str(e.get("value") or "").strip(),
                                            "lcsc_passives_ledger.yaml")
    return out


class MpnAuthority:
    """The two hand-verified sources, in resolution order, as ONE object.

    `export_jlc_package.py` imports this so the exporter and this checker cannot
    disagree about what the authority says. The two still do DIFFERENT things
    with it: the exporter WRITES a column, the checker re-derives it from the
    authority and compares against the shipped bytes.
    """

    def __init__(self, parts_dir=None, ledger=None):
        self.parts = load_part_mpns(parts_dir) if parts_dir else {}
        self.ledger = load_ledger_mpns(ledger)
        self.parts_dir = str(parts_dir) if parts_dir else ""

    def resolve(self, code):
        """MpnRes for an LCSC code, or None. NEVER a silent default."""
        code = (code or "").strip()
        if not code:
            return None
        return self.parts.get(code) or self.ledger.get(code)

    def describe(self):
        return (f"{len(self.parts)} code(s) from "
                f"{self.parts_dir or '(no 02_parts)'} + "
                f"{len(self.ledger)} from the vetted passives ledger")


# =============================================================== legibility ==
#: generator placeholders the tscircuit backend emits as a footprint-ish Value.
PLACEHOLDER_RE = re.compile(r"^simple_", re.I)


def comment_defect(comment):
    """Why this Comment is not human-readable, or None if it is fine.

    Deliberately NARROW. The three shapes ADR-0006 measured are all it refuses:
    blank, an LCSC code, a `simple_*` generator placeholder. Widening it to
    "looks like it has no unit" would start rejecting legitimate part names
    (`AON6403`, `XT60PW-M`) — the adjacent-property error this repo keeps
    paying for. A row that reads as a PART is legible even without a unit.
    """
    c = (comment or "").strip()
    if not c:
        return "blank"
    if LCSC_RE.fullmatch(c):
        return f"an LCSC CODE ({c}) — the code is already in the LCSC column"
    if PLACEHOLDER_RE.match(c):
        return f"a generator placeholder ({c})"
    return None


def legible_comment(board_value, res, footprint=""):
    """The Comment to SHIP for a row: the board's value if it reads, else the
    authority's declared value, else the MPN, else the FOOTPRINT NAME.
    '' when even that is empty.

    Order matters. The board's own Value is preferred because a human authored
    it; the MPN is the last resort for a CODED row but it is never WRONG, and
    JLC's matcher wants it anyway ("LM5145" left C485912 at 'No Part Selected';
    "LM5145RGYR" matches — the exporter's own comment diagnosed this and then
    made the fix optional).

    THE FOOTPRINT FALLBACK IS FOR THE UNCODED ROW, and it is reached ONLY when
    the authority resolved nothing (`res is None`), i.e. the row carries no LCSC
    for JLC to match on at all. Such a row exists so that a HUMAN reading the
    BOM knows the part is on the board — crow-recorder-central-v2 ships JP_INJ
    (1x03 beep-injector strap) and J_DBG (1x08 JTAG) `dnp_by_design` with a
    deliberately BLANK LCSC, declared with evidence in `03_src/rules/
    assembly.yaml`, and their board Value is the tscircuit placeholder
    `simple_chip`. There is no MPN to fall back to and the board cannot be
    re-generated to fix the Value without moving copper, so the last legible
    fact the SOURCE holds about that row is its footprint —
    `PinHeader_1x03_P2.54mm_Vertical`, which a human can read and check.

    It is deliberately LAST and deliberately narrow. It never fires for a coded
    row (that row either resolves an MPN or FAILS F-MPN), so it cannot be used
    to launder a code-only Comment into a passing one.
    """
    if comment_defect(board_value) is None:
        return board_value.strip()
    if res:
        if res.value and comment_defect(res.value) is None:
            return res.value
        if res.mpn and comment_defect(res.mpn) is None:
            return res.mpn
        return ""
    if footprint and comment_defect(footprint) is None:
        return footprint.strip()
    return ""


def encoding_verdict(raw):
    """(ok, why) — does this byte string decode IDENTICALLY under UTF-8 and
    under the recipient's likely default codepage?

    INDIFFERENT TO THE FIX, by design (ADR-0006): a UTF-8 BOM and plain ASCII
    `Ohm` both pass, because both remove the ambiguity. What fails is a file
    that is valid UTF-8, carries non-ASCII, and offers the reader nothing to
    correct its default with — which is 23 of 26 sealed BOMs.
    """
    if raw.startswith(codecs.BOM_UTF8):
        return True, "UTF-8 byte-order-mark present — the reader is told"
    try:
        u = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        return False, f"not valid UTF-8 at all: {e}"
    if all(ord(ch) < 128 for ch in u):
        return True, "pure ASCII — every codepage agrees"
    try:
        g = raw.decode(RECIPIENT_CODEC)
    except (UnicodeDecodeError, LookupError) as e:
        return False, (f"valid UTF-8 with non-ASCII and no BOM; "
                       f"{RECIPIENT_CODEC} cannot decode it at all ({e}) — "
                       f"the recipient sees replacement junk")
    if g == u:
        return True, f"non-ASCII, but UTF-8 and {RECIPIENT_CODEC} agree"
    bad = sorted({ch for ch in u if ord(ch) > 127})
    seen = "".join(bad[:8])
    return False, (f"non-ASCII {seen!r} with NO UTF-8 byte-order-mark: a reader "
                   f"defaulting to {RECIPIENT_CODEC} sees "
                   f"{''.join(sorted(set(g) - set(u)))[:8]!r} instead. Fix with "
                   f"a BOM marker or ASCII 'Ohm' — this check does not care "
                   f"which")


# ==================================================================== rows ===
BomRow = namedtuple("BomRow", "n comment refs footprint mpn lcsc")


def read_bom(path):
    """(rows, fieldnames). A row the reader cannot key is still RETURNED, so a
    malformed BOM FAILS loudly instead of shrinking the denominator."""
    raw = Path(path).read_bytes()
    text = raw.decode("utf-8-sig", "replace")
    rd = csv.DictReader(text.splitlines())
    rows = []
    for i, r in enumerate(rd, start=1):
        refs = [d.strip() for d in (r.get("Designator")
                                    or r.get("Designators") or "").split(",")
                if d.strip()]
        rows.append(BomRow(i, (r.get("Comment") or "").strip(), refs,
                           (r.get("Footprint") or r.get("Package") or "").strip(),
                           (r.get("MPN")
                            or r.get("Manufacturer Part Number") or "").strip(),
                           (r.get("LCSC") or "").strip()))
    return rows, list(rd.fieldnames or [])


def discover(target):
    """(bom_path, parts_dir, what) for a release dir, a project dir, or a csv.

    Canon M-SHIP: for a release the BOM path resolves INSIDE the sealed archive.
    The MPN AUTHORITY does not and cannot — `02_parts/` is not part of the
    release archive format — so it is taken from the project the release belongs
    to and NAMED in the output, never silently assumed.
    """
    t = Path(target).resolve()
    if t.is_file():
        bom, root = t, None
        for anc in t.parents:
            if (anc / "02_parts").is_dir():
                root = anc
                break
            if anc.name == "07_releases" and (anc.parent / "02_parts").is_dir():
                root = anc.parent
                break
        return bom, (root / "02_parts") if root else None, "BOM file"
    if (t / "fab").is_dir():                                      # release dir
        for name in ("bom.csv", "bom_jlc.csv"):
            if (t / "fab" / name).is_file():
                parts = t.parent.parent / "02_parts"
                return (t / "fab" / name,
                        parts if parts.is_dir() else None, "sealed release")
        return None, None, "sealed release"
    fab = t / "06_build" / "fab"                                  # project dir
    for name in ("bom_jlc.csv", "bom.csv"):
        if (fab / name).is_file():
            parts = t / "02_parts"
            return (fab / name, parts if parts.is_dir() else None, "project")
    return None, None, "project"


# ================================================================== checks ===
def check(bom_path, parts_dir=None, ledger=None, echo=None):
    bom_path = Path(bom_path)
    auth = MpnAuthority(parts_dir, ledger)
    r = {"bom": str(bom_path), "authority": auth.describe(),
         "fails": [], "oks": [], "coverage": {}}

    raw = bom_path.read_bytes()
    rows, fields = read_bom(bom_path)

    # ---- F-ENCODE ---------------------------------------------------------
    ok, why = encoding_verdict(raw)
    r["coverage"]["F-ENCODE"] = f"1/1 file decoded ({len(raw)} bytes)"
    (r["oks"] if ok else r["fails"]).append(
        f"F-ENCODE {bom_path.name}: {why}")

    if not rows:
        r["fails"].append(
            f"F-LEGIBLE: {bom_path} has ZERO data rows — a gate may not pass "
            f"while grading nothing (canon M-COVER)")
        r["coverage"]["F-MPN"] = "0/0 coded rows"
        r["coverage"]["F-WORDS"] = "0/0 rows"
        return r

    # ---- F-MPN ------------------------------------------------------------
    # An MPN COLUMN that does not exist is a FAIL, not a skip: one sealed BOM
    # ships without one and its 48 rows were invisible to the fleet count.
    if "MPN" not in fields and "Manufacturer Part Number" not in fields:
        r["fails"].append(
            f"F-MPN: {bom_path.name} has NO MPN COLUMN at all (header: "
            f"{','.join(fields) or 'empty'}) — every row ships code-only, and a "
            f"missing column is a FAIL, never a skip")

    coded = [x for x in rows if LCSC_RE.fullmatch(x.lcsc)]
    graded = 0
    for x in coded:
        res = auth.resolve(x.lcsc)
        tag = f"row {x.n} ({','.join(x.refs) or x.comment or '?'})"
        if res is None:
            r["fails"].append(
                f"F-MPN {tag}: LCSC {x.lcsc} resolves NO MPN from any "
                f"authority ({auth.describe()}). A coded row with no MPN is a "
                f"FAIL, never a blank — add the dossier's `sourcing.lcsc`, or "
                f"a catalog-verified ledger entry")
            continue
        graded += 1
        if not x.mpn:
            r["fails"].append(
                f"F-MPN {tag}: LCSC {x.lcsc} ships a BLANK MPN, but "
                f"{res.source} says it is '{res.mpn}'. JLC's matcher leaves a "
                f"code-only line at 'No Part Selected'")
        elif x.mpn != res.mpn:
            r["fails"].append(
                f"F-MPN {tag}: BOM says MPN '{x.mpn}' for {x.lcsc}, "
                f"{res.source} says '{res.mpn}' — the two match paths "
                f"DISAGREE, which is exactly what the redundancy is for")
        else:
            r["oks"].append(f"F-MPN {tag}: {x.lcsc} = {res.mpn} ({res.source})")
    r["coverage"]["F-MPN"] = (f"{graded}/{len(coded)} coded rows resolved "
                              f"against the authority "
                              f"({len(rows)} BOM rows total)")
    if coded and graded == 0:
        r["fails"].append(
            "F-MPN: NOT ONE of this BOM's coded rows resolved an MPN — a zero "
            "denominator is a FAIL (canon M-COVER). Is --parts pointing at the "
            "right 02_parts?")

    # ---- F-WORDS ----------------------------------------------------------
    bad = 0
    for x in rows:
        why = comment_defect(x.comment)
        if why:
            bad += 1
            r["fails"].append(
                f"F-WORDS row {x.n} ({','.join(x.refs) or '?'}): Comment is "
                f"{why}. A row nobody can read is a row nobody can check — on "
                f"either side of the upload")
    r["coverage"]["F-WORDS"] = f"{len(rows) - bad}/{len(rows)} rows legible"
    if not bad:
        r["oks"].append(f"F-WORDS all {len(rows)} Comment(s) human-readable")

    # ---- F-ECHO (human-gated) --------------------------------------------
    if echo:
        r.update(echo_check(rows, echo))
    return r


def read_echo(path):
    """{our_lcsc: their_lcsc} from a table SAVED OUT OF JLC's own UI.

    Deliberately permissive about the header: the human is copying a table out
    of a web page, and a gate that rejects the evidence format is a gate that
    gets skipped. Any two columns whose values look like LCSC codes are read as
    (ours, theirs); a single code column is read as theirs, keyed by designator.
    """
    text = Path(path).read_bytes().decode("utf-8-sig", "replace")
    rd = csv.DictReader(text.splitlines())
    pairs = {}
    for row in rd:
        low = {(k or "").strip().lower(): (v or "").strip()
               for k, v in row.items()}
        refs = [d.strip() for d in (low.get("designator")
                                    or low.get("designators") or "").split(",")
                if d.strip()]
        ours = next((v for k, v in low.items()
                     if "lcsc" in k and "match" not in k and "jlc" not in k
                     and LCSC_RE.fullmatch(v)), "")
        theirs = next((v for k, v in low.items()
                       if ("match" in k or "jlc" in k or "resolved" in k)
                       and LCSC_RE.fullmatch(v)), "")
        if not theirs and not ours:
            continue
        key = ours or (refs[0] if refs else "")
        pairs[key] = (theirs or ours, refs)
    return pairs


def echo_check(rows, echo_path):
    """F-ECHO: JLC's RESOLVED codes diffed back against ours.

    THE ONLY THING THAT WOULD HAVE CAUGHT C82317 -> C131025. Our source said
    C82317 for crow-recorder-central-v2's U5 in THREE places (part.yaml, the
    .tsx, the shipped BOM) and JLC's resolved output said C131025 — a
    substitution, on a board from a repo that has already shipped two
    DO-NOT-ORDER releases from the substituted-part class.
    """
    out = {"fails": [], "oks": [], "coverage": {}}
    theirs = read_echo(echo_path)
    ours = {x.lcsc: x for x in rows if LCSC_RE.fullmatch(x.lcsc)}
    graded = 0
    for code, x in sorted(ours.items()):
        hit = theirs.get(code)
        if hit is None:
            hit = next((v for k, v in theirs.items()
                        if k in {r_ for r_ in x.refs}), None)
        if hit is None:
            out["fails"].append(
                f"F-ECHO {code} ({','.join(x.refs)}): OUR code does not appear "
                f"in JLC's resolved table at all — either the line was dropped "
                f"or the export is not the one that was uploaded")
            continue
        graded += 1
        got = hit[0]
        if got != code:
            out["fails"].append(
                f"F-ECHO SUBSTITUTION {','.join(x.refs)}: we specified {code}, "
                f"JLC resolved {got}. This is the C82317 -> C131025 class — "
                f"adjudicate it before paying, never after")
        else:
            out["oks"].append(f"F-ECHO {code} ({','.join(x.refs)}) unchanged")
    out["coverage"]["F-ECHO"] = (f"{graded}/{len(ours)} coded rows echoed "
                                 f"against {Path(echo_path).name}")
    if ours and not graded:
        out["fails"].append(
            "F-ECHO: not one of our codes was found in the resolved table — a "
            "zero denominator is a FAIL, not a clean bill")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="release dir, project dir, or a BOM csv")
    ap.add_argument("--parts", default="",
                    help="02_parts dir (the MPN authority); auto-discovered")
    ap.add_argument("--ledger", default="",
                    help="lcsc_passives_ledger.yaml override")
    ap.add_argument("--echo", default="",
                    help="F-ECHO: JLC's RESOLVED BOM, saved out of their UI")
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)

    bom, parts, what = discover(a.target)
    if a.parts:
        parts = Path(a.parts)
    if bom is None or not Path(bom).is_file():
        print(f"  FAIL F-LEGIBLE: no BOM found for {what} {a.target} — a "
              f"target this gate cannot read is a FAIL, never a skip")
        return 1

    r = check(bom, parts, a.ledger or None, a.echo or None)
    r["target_kind"] = what
    if a.json:
        Path(a.json).write_text(json.dumps(r, indent=2, default=str) + "\n")

    print(f"  graded: {what} BOM {r['bom']}")
    print(f"  authority: {r['authority']}")
    for k, v in sorted(r["coverage"].items()):
        print(f"  coverage {k}: {v}")
    for o in r["oks"][:400]:
        print(f"  ok   {o}")
    for f in r["fails"]:
        print(f"  FAIL {f}")

    if r["fails"]:
        print(f"F-LEGIBLE FAIL: {len(r['fails'])} finding(s), "
              f"{len(r['oks'])} ok")
        return 1
    print(f"F-LEGIBLE OK: {len(r['oks'])} check(s) passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
