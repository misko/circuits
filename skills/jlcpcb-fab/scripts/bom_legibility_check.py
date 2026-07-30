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

A SEALED RELEASE'S VERDICT WAS A FUNCTION OF MUTABLE SOURCE, AND A SEAL THAT
CANNOT BE RE-DERIVED FROM THE SEALED BYTES IS NOT EVIDENCE OF ANYTHING (added
2026-07-29, canon M-SHIP from the inside).

MEASURED, twice in opposite directions, in ONE session. `cooksense-v1.6` sealed
2026-07-27. On 2026-07-29 16:15 this gate FAILED it on rows 39 (U_EXP, C506653)
and 56 (U_ULNA/U_ULNB, C9683); hours later, unchanged bytes, it PASSED it again.
Nothing about v1.6 moved either time. What moved was `02_parts/`: the live v1.7
work removed the `ULN2803ADWR` dossier and then restored it. So ordinary forward
progress on the NEXT revision retro-failed a SEALED release, and then retro-
healed it — the second half is the worse one, because a red that repairs itself
for an unrelated reason is a red nobody records.

The gate could not grade the shipped bytes FROM the shipped bytes, because both
of its authorities live OUTSIDE the archive and both are editable. The remedy has
two halves and neither is "loosen the check":

  1. A THIRD AUTHORITY THAT IS SEALED WITH THE RELEASE. `verification/
     stock_check.csv` is already a REQUIRED release artifact (the 07_releases
     contract mandates `stock_check.{txt,csv}`) and it already carries a
     `code`/`LCSC` -> `mpn` column, because `jlc_stock_check.py` records JLC's
     own `componentModelEn` for every line it queries. That is a code->MPN map
     frozen inside the archive whose provenance is THE RECIPIENT'S OWN CATALOG —
     not our dossiers, not our exporter (canon M-PROV). The map was there all
     along; this gate had simply never looked.

  2. AN HONEST VERDICT CLASS FOR WHAT STILL CANNOT BE RE-DERIVED. `07_releases/`
     is IMMUTABLE, so a release sealed before the map existed can never gain
     one, and a FAIL against bytes nobody may edit is a verdict with no remedy.
     Those rows now land in a THIRD, LOUD, COUNTED class (below) instead of
     being either failed or folded into OK.

IT IS AN EXISTENCE AUTHORITY, NOT AN EQUALITY AUTHORITY, AND THAT IS MEASURED
RATHER THAN ASSUMED. JLC's `componentModelEn` is a catalog DESCRIPTION string
and it is NOT the manufacturer part number on 7 of the 156 rows fleet-wide that
have one: `436500224` for Molex `43650-0224`, `SMAJ5.0A-13-F` for `SMAJ5.0A`,
`2.54-2*20PFemale longPC104` for `2.54-2*20PPC104`, and `MCP3208-CI/SL` where
OUR BOM ships the directory-name form `MCP3208-CI-SL`. Consulting it FIRST would
therefore have turned 7 rows on four releases — including two LIVE ones — into
false DISAGREE failures. So the resolution order is dossier -> ledger -> release-
carried, the release-carried path is the FALLBACK, and reaching it never asserts
equality: it corroborates that the code named a real, catalog-resolvable part
with a manufacturer part number ON THE DAY OF THE SEAL, prints JLC's string
beside ours, and says plainly that the two-path equality check did not run.

THE THREE VERDICTS FOR A CODED ROW, and the discrimination is the whole point:

  FAIL              the row contradicts itself or a HAND-VERIFIED authority. A
                    blank MPN on a coded row is self-contained — it needs no
                    authority at all, and it is the v1.2 defect this gate was
                    built for. A shipped MPN that disagrees with the dossier is
                    the usb-hub `SS12D07VG6 087`-vs-`-087` drift. Both still
                    FAIL on sealed bytes; immutability is not an excuse.
  OK                a hand-verified authority resolved the code and AGREES.
  NOT RE-DERIVABLE  no hand-verified authority resolves this code, on a target
                    that MAY NOT BE EDITED. Never OK, never a FAIL, always
                    counted with its denominator (M-COVER), sub-classified as
                    CORROBORATED (the release's own JLC catalog record carries
                    the code) or UNGRADEABLE (nothing the release carries does).

ON A MUTABLE TARGET — a project dir, a staging BOM, a bare csv — an unresolvable
code REMAINS A FAIL, and that asymmetry is the principle, not a compromise: a
remedy EXISTS there (add the dossier's `sourcing.lcsc`, or a catalog-verified
ledger row) and the exporter must keep blocking before the bytes are ever sealed.
Class-3 rows are how a SEAL gets audited later; a FAIL is how a seal is
PREVENTED. The seal-time run is where the class is closed: the 07_releases
contract requires `bom_legibility_check.py <release_dir>` to exit 0 AND to report
ZERO rows in this class, which is exactly the moment the dossier tree is still
live and the map can still be written.
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

#: a BARE `alternates:` entry, which is free text that OFTEN begins with a code:
#: `C319134 (DC-005-5A-2.0-SMT)`, `C136347 (JFC1206-1300FS, 3 A)`. The leading
#: code is keyed; an entry that names no code (`PCM1864DBTR`, `MF-MSMD050-2
#: (Bourns, verify land/R)`) keys nothing and is counted, never guessed at.
LCSC_LEAD = re.compile(r"^(C\d+)\b")

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

    `alternates:` HAS TWO SCHEMA FORMS IN THE WILD AND THIS READER SILENTLY
    DROPPED THE COMMON ONE (fixed 2026-07-29). It read only the `{lcsc:, mpn:}`
    mapping. MEASURED across the fleet's dossiers: **351 alternates are BARE
    STRINGS and 2 are mappings** — and one of those two was written an hour
    earlier to work around this very bug. The bare form is what the `02_parts`
    contract's own example shows (`alternates: [C2650259, C3188678]`) and what
    `electrical_invariants.py` reads. So the fleet's `02_parts` tree spoke the
    documented dialect and the MPN AUTHORITY understood 0.6% of it, for this
    file's entire life, without a word. A silent skip inside an authority is the
    `jlc_twin`-exits-0 shape: the consumer sees a clean run over a fact nobody
    checked.

    BUT A BARE ALTERNATE CANNOT SUPPLY AN MPN, AND INVENTING ONE WOULD BE WORSE
    THAN THE SKIP. The obvious repair — key the code to the PARENT's `mpn:`, as
    the mapping branch already does when `mpn:` is omitted — puts a FALSE part
    number in the column whose entire job is to be the exact part number: the
    measured case is `02_parts/MCP23017-E-SS`, where the alternate `C47023` is
    `MCP23017-E/SO`, a SOIC-28W part needing a different footprint, not the
    SSOP-28 `MCP23017-E/SS` the dossier is about. That is the adjacent-property
    error this repo keeps paying for, committed inside the fix.

    So a bare alternate resolves to an entry with an EMPTY `mpn`: the code is
    KNOWN and its MPN is UNDECLARED. `check()` turns that into a named finding
    with the remedy ("give this alternate the `{lcsc:, mpn:}` form") instead of
    the old `resolves NO MPN from any authority`, which sent the reader looking
    for a dossier that was there all along. A bare entry that does not even
    START with an LCSC code is a free-text note (`MF-MSMD050-2 (Bourns, verify
    land/R)`, `PCM1864DBTR`) and keys nothing — deliberately, and it is COUNTED
    in `describe()` rather than dropped.
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
            _put(out, code, MpnRes(mpn, _declared_value(d),
                                   f"02_parts/{y.parent.name}"))
        for alt in (src.get("alternates") or []):
            if isinstance(alt, dict):
                ac = str(alt.get("lcsc") or "").strip()
                am = str(alt.get("mpn") or mpn).strip()
                if LCSC_RE.fullmatch(ac) and am:
                    _put(out, ac, MpnRes(am, _declared_value(d),
                                         f"02_parts/{y.parent.name} (alt)"))
                continue
            # the BARE form: 351 of the fleet's 353 alternates, and the form the
            # 02_parts contract's own example shows. KNOWN code, UNDECLARED MPN
            # — never the parent's, which is a different part (see docstring).
            m = LCSC_LEAD.match(str(alt).strip())
            if m:
                _put(out, m.group(1),
                     MpnRes("", "", f"02_parts/{y.parent.name} "
                                    f"(bare alternate, NO mpn declared)"))
    return out


def _put(out, code, res):
    """Register a resolution. Among entries that CARRY an MPN the first dossier
    read wins (the `setdefault` semantics this replaces). An MPN-LESS entry — a
    bare `alternates:` code — never overwrites anything, and is itself UPGRADED
    the moment a real MPN for that code turns up.

    THIS FUNCTION EXISTS BECAUSE THE FIRST VERSION OF THE BARE-ALTERNATE FIX
    BROKE A GOOD ROW, and it was the test suite that said so, not review.
    `C79924` is `crow-recorder-central-v2`'s U9 and is BOTH the `sourcing.lcsc`
    of its own dossier AND a bare alternate of another one. Registered with
    `setdefault` in dossier-name order, the empty-MPN placeholder landed first
    and blocked the real answer forever — so a fix for a silent skip introduced
    a silent skip, on a row that had been resolving correctly. Precedence has to
    be by INFORMATION CONTENT, not by filesystem order.
    """
    prev = out.get(code)
    if prev is None or (not prev.mpn and res.mpn):
        out[code] = res


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


#: the release-carried code->MPN map, relative to a sealed release directory.
#: ALREADY a required release artifact (07_releases contract:
#: `stock_check.{txt,csv}`), so this adds no obligation — only a reader.
RELEASE_MPN_CSV = Path("verification") / "stock_check.csv"

#: how a release-carried resolution names itself, so a caller can tell it apart
#: from a hand-verified one without string-sniffing the whole source field.
RELEASE_SRC = "verification/stock_check.csv"


def sealed_release_of(path):
    """The SEALED, IMMUTABLE release directory `path` lives inside, or None.

    Immutability is not inferred or guessed: `07_releases/<dir>/` is the exact
    boundary CLAUDE.md declares immutable, so the test is "is some ancestor a
    direct child of a directory named 07_releases". A staging BOM under
    `06_build/fab/` is therefore NOT sealed and keeps the FAIL semantics, which
    is the whole asymmetry this file's header argues for.
    """
    p = Path(path).resolve()
    for anc in [p] + list(p.parents):
        if anc.parent.name == "07_releases":
            return anc if anc.is_dir() else None
    return None


def load_release_mpns(release_dir):
    """{lcsc: MpnRes} from the release's OWN sealed `verification/stock_check.csv`.

    THE ONLY AUTHORITY THAT LIVES INSIDE THE ARCHIVE, and the reason a seal can
    be re-derived at all (canon M-SHIP). `jlc_stock_check.py` writes one row per
    BOM line carrying `LCSC` (the code WE asked for), `code` (the code JLC
    ANSWERED with) and `mpn` (JLC's `componentModelEn`). Both codes are keyed,
    because a release where the two differ is a substitution F-ECHO exists to
    adjudicate and a reader looking up either one deserves an answer.

    PROVENANCE, stated because canon M-PROV grades authorities and not just
    boards: this column came from JLC's parts catalog over their API. It was not
    produced by our exporter, our dossiers or this checker, so using it does not
    make checker and checked share a method. What it IS, though, is a catalog
    DESCRIPTION rather than a part number on a measured minority of rows — see
    the header — which is why callers must treat a hit here as EXISTENCE and
    never as equality.
    """
    if not release_dir:
        return {}
    p = Path(release_dir) / RELEASE_MPN_CSV
    if not p.is_file():
        return {}
    out = {}
    try:
        text = p.read_bytes().decode("utf-8-sig", "replace")
        for row in csv.DictReader(text.splitlines()):
            mpn = str(row.get("mpn") or "").strip()
            if not mpn:
                continue
            value = str(row.get("Comment") or "").strip()
            for key in (str(row.get("LCSC") or "").strip(),
                        str(row.get("code") or "").strip()):
                if LCSC_RE.fullmatch(key or ""):
                    out.setdefault(key, MpnRes(mpn, value, RELEASE_SRC))
    except Exception:                                     # noqa: BLE001
        # usb-hub-3s-v3 v1.1 ships a `stock_check.csv` that is PROSE, not a csv
        # ("44 BOM lines: 40 with LCSC, 4 without"). An unreadable map yields no
        # entries and the rows fall to the NOT-RE-DERIVABLE class, which is the
        # honest answer; it must never crash the gate (a traceback is the worst
        # available verdict — fa22228).
        return {}
    return out


class MpnAuthority:
    """The hand-verified sources plus the release-carried one, as ONE object.

    `export_jlc_package.py` imports this so the exporter and this checker cannot
    disagree about what the authority says. The two still do DIFFERENT things
    with it: the exporter WRITES a column, the checker re-derives it from the
    authority and compares against the shipped bytes.

    RESOLUTION ORDER IS dossier -> ledger -> release-carried, and the order was
    chosen by MEASUREMENT, not taste. Putting the release-carried map first would
    have turned 7 rows across four sealed releases — two of them LIVE — into
    false DISAGREE failures, because JLC's `componentModelEn` is `436500224`
    where Molex's part number is `43650-0224`. It is the FALLBACK, reached only
    where the hand-verified pair says nothing, and `release_carried()` marks the
    result so the caller can refuse to grade equality on it.
    """

    def __init__(self, parts_dir=None, ledger=None, release=None):
        self.parts = load_part_mpns(parts_dir) if parts_dir else {}
        self.ledger = load_ledger_mpns(ledger)
        self.release = load_release_mpns(release)
        self.parts_dir = str(parts_dir) if parts_dir else ""
        self.release_dir = str(release) if release else ""
        #: True when the graded artifact MAY NOT BE EDITED to fix a finding.
        self.sealed = bool(release)

    def resolve(self, code):
        """MpnRes for an LCSC code, or None. NEVER a silent default.

        Only an entry that actually CARRIES an MPN is a resolution. A bare
        `alternates:` entry names a code and declares no part number, so it is
        reachable by `known_without_mpn()` for DIAGNOSIS and never returned here
        — which keeps every consumer's contract intact (`legible_comment` must
        still fall back to the FOOTPRINT for a row the authority cannot name)
        while ending the silent skip that hid `C47023`.
        """
        code = (code or "").strip()
        if not code:
            return None
        for table in (self.parts, self.ledger, self.release):
            r = table.get(code)
            if r and r.mpn:
                return r
        return None

    def known_without_mpn(self, code):
        """The dossier entry that NAMES this code but declares no MPN for it, or
        None. The diagnosis that turns `resolves NO MPN from any authority` —
        which sends the reader hunting for a dossier that was there all along —
        into `the dossier names it as a bare alternate; give it the
        {lcsc:, mpn:} form`."""
        r = self.parts.get((code or "").strip())
        return r if (r and not r.mpn) else None

    @staticmethod
    def release_carried(res):
        """True when this resolution came from the release's OWN sealed bytes —
        i.e. it corroborates EXISTENCE and must not be graded for equality."""
        return bool(res) and res.source == RELEASE_SRC

    @property
    def mpnless(self):
        """Codes the dossier tree KNOWS but declares no MPN for — bare
        `alternates:` entries. Named in `describe()` because an authority that
        does not report the inputs it could only half-read is the same silent
        skip in a different coat (canon M-COVER)."""
        return {c for c, r in self.parts.items() if not r.mpn}

    def describe(self):
        rel = (f" + {len(self.release)} from the release's own sealed "
               f"{RELEASE_SRC}" if self.release else
               (f" + NOTHING from the release itself (no {RELEASE_SRC})"
                if self.sealed else ""))
        bare = (f" (of which {len(self.mpnless)} are BARE `alternates:` entries "
                f"that declare NO mpn)" if self.mpnless else "")
        return (f"{len(self.parts)} code(s) from "
                f"{self.parts_dir or '(no 02_parts)'}{bare} + "
                f"{len(self.ledger)} from the vetted passives ledger{rel}")


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
#: printed verbatim when a verdict is NOT re-derivable from the sealed bytes.
#: `fleet_regrade.py` greps for it to render a THIRD cell state, because a table
#: that prints PASS over an ungraded row is the M-COVER failure at fleet scale.
UNGRADED_TOKEN = "NOT-REDERIVABLE-FROM-SHIPPED-BYTES"


def check(bom_path, parts_dir=None, ledger=None, echo=None, release=None):
    bom_path = Path(bom_path)
    # DERIVED, not passed: `release_freshness_check.py` calls check(bom, parts)
    # with a path inside the archive and must get the sealed semantics without
    # knowing this parameter exists.
    if release is None:
        release = sealed_release_of(bom_path)
    auth = MpnAuthority(parts_dir, ledger, release)
    r = {"bom": str(bom_path), "authority": auth.describe(),
         "fails": [], "oks": [], "coverage": {}, "ungraded": [],
         "sealed": bool(release)}

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
    corroborated = 0
    for x in coded:
        res = auth.resolve(x.lcsc)
        tag = f"row {x.n} ({','.join(x.refs) or x.comment or '?'})"
        # ---- the BLANK MPN is a defect IN THE SHIPPED BYTES and needs no
        # authority to see: a coded line with no MPN is what JLC leaves at "No
        # Part Selected", which is the v1.2 incident this gate was built for. It
        # is checked BEFORE resolution so that immutability can never excuse it.
        if not x.mpn:
            src = (f", but {res.source} says it is '{res.mpn}'" if res else
                   f", and the code resolves NO MPN from any authority either "
                   f"({auth.describe()})")
            r["fails"].append(
                f"F-MPN {tag}: LCSC {x.lcsc} ships a BLANK MPN{src}. "
                f"JLC's matcher leaves a code-only line at 'No Part Selected'")
            if res is not None:
                graded += 1
            continue
        if res is None:
            half = auth.known_without_mpn(x.lcsc)
            why = (f"F-MPN {tag}: LCSC {x.lcsc} is NAMED by {half.source} but "
                   f"that entry declares NO mpn, so no authority resolves a part "
                   f"number for it — give the alternate the "
                   f"`{{lcsc: {x.lcsc}, mpn: <the alternate's OWN part number>}}` "
                   f"form; it is NOT the parent dossier's MPN (C47023 is "
                   f"MCP23017-E/SO, not the -E/SS the dossier is about)"
                   if half else
                   f"F-MPN {tag}: LCSC {x.lcsc} resolves NO MPN from any "
                   f"authority ({auth.describe()})")
            # A BARE ALTERNATE IS A FAIL EVEN ON A SEALED RELEASE, and the line
            # between the two classes is REMEDY, not immutability for its own
            # sake. The fact is in the tree; a one-line dossier edit gives the
            # alternate its own `mpn:` and makes the sealed release gradeable
            # again WITHOUT touching it. The ungraded class is for the case where
            # no edit anywhere could restore the fact.
            if auth.sealed and half is None:
                r["ungraded"].append(
                    f"{why}, and this release MAY NOT BE EDITED. The row ships "
                    f"an MPN ('{x.mpn}') and a code, so it is LEGIBLE; what "
                    f"cannot be performed is the two-path AGREEMENT check, "
                    f"because both hand-verified authorities live OUTSIDE the "
                    f"sealed archive and have moved on since. UNGRADEABLE — "
                    f"not OK, and not a FAIL against bytes nobody may fix")
            else:
                r["fails"].append(
                    f"{why}. A coded row this gate cannot name a part number for "
                    f"is a FAIL, never a blank — " + ("give that alternate its "
                    f"own `mpn:`" if half else "add the dossier's "
                    f"`sourcing.lcsc`, or a catalog-verified ledger entry"))
            continue
        # ---- the release's OWN record: EXISTENCE, never equality (header).
        if auth.release_carried(res):
            corroborated += 1
            agree = ("and AGREES with it character for character"
                     if x.mpn == res.mpn else
                     f"which reads '{res.mpn}' — a catalog DESCRIPTION, so the "
                     f"difference is not by itself a defect and is NOT graded "
                     f"here")
            r["ungraded"].append(
                f"F-MPN {tag}: LCSC {x.lcsc} resolves from NO hand-verified "
                f"authority; the release's OWN sealed {RELEASE_SRC} (JLC's "
                f"catalog, recorded at the seal) CORROBORATES that the code "
                f"named a real part with a manufacturer part number, {agree}. "
                f"The row ships '{x.mpn}'. Existence is re-derivable from the "
                f"shipped bytes; the two-path equality check is NOT")
            continue
        graded += 1
        if x.mpn != res.mpn:
            r["fails"].append(
                f"F-MPN {tag}: BOM says MPN '{x.mpn}' for {x.lcsc}, "
                f"{res.source} says '{res.mpn}' — the two match paths "
                f"DISAGREE, which is exactly what the redundancy is for")
        else:
            r["oks"].append(f"F-MPN {tag}: {x.lcsc} = {res.mpn} ({res.source})")
    ungraded_rows = len(coded) - graded
    r["coverage"]["F-MPN"] = (
        f"{graded}/{len(coded)} coded rows cross-checked against a "
        f"HAND-VERIFIED authority; {ungraded_rows} not re-derivable from the "
        f"shipped bytes ({corroborated} corroborated by the release's own "
        f"sealed {RELEASE_SRC}, {ungraded_rows - corroborated} ungradeable) "
        f"({len(rows)} BOM rows total)")
    if coded and graded == 0:
        # A ZERO DENOMINATOR IS A FAIL (M-COVER) — but only where a remedy
        # exists. On a SEALED release, condemning every row because the mutable
        # dossier tree moved on is the exact defect this class was added to end,
        # so there it is the loud NOT-RE-DERIVABLE verdict instead, and the
        # 07_releases contract closes it at the seal (see the header), which is
        # the one moment the tree is still live.
        msg = ("F-MPN: NOT ONE of this BOM's coded rows was cross-checked "
               "against a hand-verified authority — a zero denominator is a "
               "FAIL (canon M-COVER). Is --parts pointing at the right "
               "02_parts?")
        if auth.sealed:
            r["ungraded"].append(
                msg.replace("a FAIL (canon M-COVER)",
                            "NOT a pass (canon M-COVER)")
                + " This release is IMMUTABLE, so the finding is reported as "
                  "ungraded rather than failed; no edit to it could ever clear "
                  "it.")
        else:
            r["fails"].append(msg)

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
    for u in r.get("ungraded", []):
        print(f"  UNGRADED {u}")
    for f in r["fails"]:
        print(f"  FAIL {f}")

    if r["fails"]:
        print(f"F-LEGIBLE FAIL: {len(r['fails'])} finding(s), "
              f"{len(r['oks'])} ok")
        return 1
    # NEITHER OK NOR FAIL, and the distinction is the point. Exit 0 because
    # every row is legible and no defect was found; the missing thing is a
    # CROSS-CHECK, and canon reports coverage in the denominator rather than in
    # the exit code. It is not allowed to READ as OK, so the verdict line is a
    # different sentence carrying the count and a token a fleet sweep can grep.
    if r.get("ungraded"):
        print(f"F-LEGIBLE NOT FULLY GRADED [{UNGRADED_TOKEN}]: "
              f"{len(r['ungraded'])} row(s) could not be cross-checked against "
              f"a hand-verified authority, {len(r['oks'])} check(s) passed, 0 "
              f"defects found. A sealed release graded against a dossier tree "
              f"that has legitimately moved on says exactly this — it does not "
              f"say OK and it does not say FAIL")
        return 0
    print(f"F-LEGIBLE OK: {len(r['oks'])} check(s) passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
