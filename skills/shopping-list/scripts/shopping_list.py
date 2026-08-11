#!/usr/bin/env python3
"""shopping_list.py — what to BUY, per distributor, with the grade of every number.

    shopping_list.py PROJECT_DIR [--scope self_supplied|all] [--boards N]
                     [--min-stock 10] [--out FILE.md] [--json FILE.json]
                     [--bom CANDIDATE_BOM.csv]
                     [--required-pools 2 --jlc-stock-json STOCK.json]
                     [--replay DIR] [--offline] [--no-cache]
                     [--quote-max-age-days 7] [--call-budget 200]

Plain python3. No pcbnew. The only network call is Mouser's Search API.

WHY THIS EXISTS — three incidents, one escalating lesson (canon M-QUOTE, the
narrow instance of M-IMPORT scoped to DISTRIBUTOR facts).

  1. GHR-10V-S. Reported to the user as available on the strength of a DigiKey
     SEARCH-RESULT SNIPPET reading "available to order today with same-day
     shipping". The product page said **In Stock: 0**. That sentence is
     boilerplate; it renders at zero stock. A SNIPPET IS NOT A STOCK FIGURE.

  2. 10FDZ-BT(S)(LF)(SN). The Mouser API, asked `partSearchOptions: "Exact"`
     for the fully-suffixed manufacturer MPN our own `02_parts/` dossier holds,
     returns ONE hit: `LifecycleStatus: Obsolete`, `MouserPartNumber: "N/A"`,
     `Availability: null`, zero price breaks. The same part, searched
     `partSearchOptions: "None"` on the suffix-stripped `10FDZ-BT`, returns TWO
     records, one of them **37 In Stock** at $0.96/1 under Mouser part number
     `306-10FDZBTSLFSN` — whose own digits encode S / LF / SN, so the live
     record IS the (S)(LF)(SN) variant, merely catalogued under the bare MPN.
     ONE PHYSICAL PART, THREE CATALOG RECORDS, THREE DIFFERENT ANSWERS.
     A MACHINE-READABLE FIELD IS NOT AUTOMATICALLY THE RIGHT FIELD, AND ONE
     RECORD IS NOT THE PART. Measured 2026-07-27; the fixture is
     `tests/fixtures/shopping_list/mouser/`.

  3. Same defect class, and the repo already has its name: the ADJACENT-PROPERTY
     ERROR (M-IMPORT's co-resident corollary) — measuring something NEAR the
     property you need. #1 measures the state of a search page; #2 measures the
     state of a CATALOG ENTRY. Neither measures the state of the PART. That #2
     fires through a JSON API is the whole reason "use the API" is not by itself
     the lesson, and why the broad re-search below is STRUCTURAL rather than a
     comment: `grade_mouser()` refuses to emit an unsourceable verdict until
     `RecordSet.broad_done` is True.

THE CHECK IDS (design-policies.md, row M-QUOTE):

  Q-COVER   every selected part is looked up at every declared distributor and
            the report prints `N/M`. A part the tool could not look up is a
            FAIL, never an omission. The user has been burned by exactly this:
            `bom_source_check` dropped 87 of 673 rows and exited 0.
  Q-WIDE    an "obsolete / no stock" verdict from an API is reportable only
            AFTER the broad (suffix-stripped, non-exact) search has also run
            and returned nothing better. A lone exact hit is a prompt to search
            wider, not a finding.
  Q-STOCK   a line counts as SOURCEABLE only at stock > --min-stock (the user's
            standing bar: >10) AND stock >= the quantity needed. A line that
            fails is REPORTED as a finding, never dropped and never silently
            substituted.
  Q-SNIPPET a manual quote must name the PAGE it was read from and the date it
            was read. `source: search_snippet` is refused as a stock figure
            (incident 1) and so is a quote older than --quote-max-age-days.
  Q-GRADE   every number carries its M-IMPORT grade — CITED (machine-readable
            API response, or a product page read with its URL and date),
            ESTIMATED (anything volatile and unverifiable: Amazon, always), or
            OWED (nobody has this fact yet; here is how to obtain it). An
            absent grade is a FAIL, never a quiet promotion.
  Q-2SOURCE when --required-pools is set, each exact manufacturer/MPN row must
            be sourceable from that many independent authorized pools. JLC,
            Mouser and DigiKey qualify; Amazon never does. Per-distributor gaps
            remain visible but no longer falsify a green composed-pool verdict.

THE CREDENTIAL. Never embedded, never printed, never logged, never written into
a cache file or a URL this tool emits. Resolution order:
  1. $MOUSER_API_KEY
  2. <repo root>/.secrets/mouser.env   (repo root = the first ancestor holding
     BOTH `skills/` and `contracts.md`; `git rev-parse --show-toplevel` returns
     a WORKTREE, which is how this was got wrong the first time)
  3. absent -> say so, degrade to the manual path, and grade every Mouser line
     OWED. Never crash, and never produce an unsourced list that looks sourced.

RATE LIMIT. Mouser publishes 50 parts per call, 30 calls per minute, 1,000 calls
per day (mouser.com/api-search/). This tool sleeps 2.1 s between calls (28.6/min)
and refuses to exceed --call-budget in one run. Mouser's API terms forbid caching
their content, so the cache here is a SESSION cache only: it lives in the
gitignored, disposable `06_build/cache/mouser/`, carries `fetched_at`, defaults
to a 6-hour TTL, is never committed, and is never treated as truth at order time
(project 06_build contract, "Forbidden: treating a cached stock number as truth
at order time").
"""
import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

# "Which release is this board's newest?" has ONE implementation in this repo
# (canon M-WIDTH). Imported, never re-derived — see release_index.py for the
# two defects that came from every tool answering it its own way.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]
                       / "jlcpcb-fab" / "scripts"))
import release_index as _relidx                                # noqa: E402

MOUSER_URL = "https://api.mouser.com/api/v1/search/partnumber"
CALL_SPACING_S = 2.1              # 28.6 calls/min against a published 30/min
CACHE_TTL_S = 6 * 3600

#: M-IMPORT's closed vocabulary, as it applies to a distributor fact.
CITED = "CITED"           # machine-readable API response, or a product page
ESTIMATED = "ESTIMATED"   # volatile / unverifiable / snippet-derived
OWED = "OWED"             # nobody has it; the report says how to get it

DISTRIBUTORS = ("mouser", "digikey", "amazon")

#: Q-COVER. A part is GRADED when the lookup completed and returned an answer
#: about the PART — including "this distributor does not list it", which is a
#: finding. Everything else (a failed call, a missing key, an unparseable
#: field, a quote that was never recorded) is UNGRADED and therefore a FAIL,
#: never an omission: `bom_source_check` dropped 87 of 673 rows and exited 0.
GRADED_STATUSES = ("OK", "LOW-STOCK", "NO-STOCK", "NOT-IN-CATALOG",
                   "SUBSTITUTE-ONLY", "MANUFACTURER-MISMATCH",
                   "REFUSED-SNIPPET", "STALE")

AUTHORIZED_POOLS = ("jlc", "mouser", "digikey")


def normalize_manufacturer(value):
    """Normalize an exact manufacturer identity without accepting a near MPN.

    Corporate suffixes and punctuation are spelling, not identity. A small
    alias table covers catalog abbreviations that are unambiguous; substring
    matching is deliberately refused because `ST` and `Diodes` are not safe
    fuzzy keys.
    """
    s = re.sub(r"[^a-z0-9]+", "", str(value or "").lower())
    for suffix in ("incorporated", "corporation", "commercial", "company", "limited",
                   "electronicscorp", "inc", "corp", "ltd", "co"):
        if s.endswith(suffix):
            s = s[:-len(suffix)]
    aliases = {
        "ti": "texasinstruments",
        "st": "stmicroelectronics",
        "gctglobalconnectortechnology": "gct",
        "globalconnectortechnology": "gct",
        "keystone": "keystoneelectronics",
        "diodes": "diodes",
    }
    return aliases.get(s, s)


def same_manufacturer(found, authoritative):
    return bool(normalize_manufacturer(found)) and \
        normalize_manufacturer(found) == normalize_manufacturer(authoritative)


def observation_date(override=""):
    """Calendar used for UTC-stamped catalog snapshots and dated quotes."""
    return (date.fromisoformat(override) if override
            else datetime.now(timezone.utc).date())


# ------------------------------------------------------------------ helpers
def repo_root(start):
    """The repo root is the first ancestor holding BOTH `skills/` and
    `contracts.md`. NOT `git rev-parse --show-toplevel`: inside a git worktree
    that returns the WORKTREE, and a relative `.secrets/` then resolves to a
    directory that does not exist — measured 2026-07-27, and it is the same
    adjacent-property shape as everything else in this file (the property is
    "where the repo's secrets live", not "where git thinks I am")."""
    p = Path(start).resolve()
    for cand in [p, *p.parents]:
        if (cand / "skills").is_dir() and (cand / "contracts.md").is_file():
            return cand
    return None


def main_checkout(start):
    """The MAIN checkout, when `start` is inside a linked git worktree.

    `git rev-parse --show-toplevel` returns the WORKTREE and is therefore the
    wrong question; `--git-common-dir` resolves to the shared `.git`, whose
    parent is the checkout that actually holds `.secrets/`."""
    import subprocess
    try:
        r = subprocess.run(["git", "-C", str(start), "rev-parse",
                            "--git-common-dir"], capture_output=True, text=True,
                           timeout=10)
    except Exception:                             # noqa: BLE001
        return None
    if r.returncode != 0 or not r.stdout.strip():
        return None
    d = Path(r.stdout.strip())
    if not d.is_absolute():
        d = (Path(start) / d)
    return d.resolve().parent


def _read_env_key(envf, name):
    if not envf.is_file():
        return None
    for line in envf.read_text(errors="replace").splitlines():
        line = line.strip()
        if line.startswith("export "):
            line = line[7:].strip()
        if line.startswith(name):
            v = line.split("=", 1)[1].strip().strip('"').strip("'")
            if v:
                return v
    return None


def load_api_key(project_dir):
    """-> (key_or_None, provenance_string). The key itself never reaches any
    printing path — only the PROVENANCE string does."""
    k = os.environ.get("MOUSER_API_KEY", "").strip()
    if k.lower() == "none":
        # An EXPLICIT declaration that there is no key (tests, CI). Distinct
        # from unset: unset means "look in .secrets/", this means "do not".
        return None, "$MOUSER_API_KEY=none (explicitly declared absent)"
    if k:
        return k, "$MOUSER_API_KEY"
    seen = []
    for base in (repo_root(project_dir), repo_root(__file__),
                 main_checkout(project_dir), main_checkout(__file__)):
        if not base or base in seen:
            continue
        seen.append(base)
        v = _read_env_key(base / ".secrets" / "mouser.env", "MOUSER_API_KEY")
        if v:
            return v, "<repo>/.secrets/mouser.env"
    return None, "ABSENT"


def redact(text, key):
    return text.replace(key, "<REDACTED>") if key else text


def yaml_load(path):
    import yaml
    try:
        return yaml.safe_load(path.read_text(errors="replace")) or {}
    except Exception as e:                      # noqa: BLE001
        return {"__parse_error__": f"{type(e).__name__}: {e}"}


def strip_packaging_suffixes(mpn):
    """`10FDZ-BT(S)(LF)(SN)` -> (`10FDZ-BT`, ['(S)', '(LF)', '(SN)']).

    Trailing parenthesised groups of <=4 alphanumerics are PACKAGING/PLATING
    qualifiers (S = tube/reel style, LF = lead-free, SN = tin plate). They are
    not different parts, and Mouser catalogues the live record under the BARE
    MPN while keeping a dead record under the suffixed one."""
    bare, stripped = mpn.strip(), []
    while True:
        m = re.search(r"\(([A-Za-z0-9]{1,4})\)\s*$", bare)
        if not m:
            return bare.strip(), list(reversed(stripped))
        stripped.append(m.group(0).strip())
        bare = bare[:m.start()].rstrip()


def parse_availability(val):
    """-> (qty:int|None, note:str). None means UNPARSEABLE, which is a FAIL and
    never a skip (canon M-COVER). Mouser writes '37 In Stock', the STRING
    'None' (yes, a string), or JSON null."""
    if val is None:
        return None, "null"
    if isinstance(val, (int, float)):
        return int(val), "numeric"
    s = str(val).strip()
    if s in ("", "None", "null", "N/A"):
        return 0, s or "empty"
    m = re.match(r"^([\d,]+)\s*(?:In Stock|in stock)?", s)
    if m and m.group(1):
        return int(m.group(1).replace(",", "")), s
    return None, s


def parse_money(s):
    if s is None:
        return None
    m = re.search(r"([\d.,]+)", str(s).replace(",", ""))
    return float(m.group(1)) if m else None


def price_at(breaks, qty):
    """-> (unit_price, break_qty, below_first_break:bool)."""
    rows = []
    for b in breaks or []:
        q, p = b.get("Quantity"), parse_money(b.get("Price"))
        if isinstance(q, (int, float)) and p is not None:
            rows.append((int(q), p))
    if not rows:
        return None, None, False
    rows.sort()
    ok = [r for r in rows if r[0] <= qty]
    if ok:
        return ok[-1][1], ok[-1][0], False
    return rows[0][1], rows[0][0], True


def slug(*parts):
    return re.sub(r"[^A-Za-z0-9]+", "_", "__".join(parts)).strip("_")[:120]


# ---------------------------------------------------------- the part universe
class Part:
    def __init__(self, mpn, source, directory=None):
        self.mpn = mpn
        self.mpn_source = source          # how the MPN authority was resolved
        self.dir = directory
        self.manufacturer = ""
        self.lcsc = None
        self.type = ""
        self.refs = {}                    # board -> [refdes]
        self.reasons = []                 # why it is on the shopping list
        self.parse_error = None

    @property
    def ref_count(self):
        return sum(len(v) for v in self.refs.values())


def read_parts(project):
    """`02_parts/<dir>/part.yaml`. THE MPN AUTHORITY IS THE `mpn:` FIELD, and
    the DIRECTORY NAME only where there is no field: MPNs legally contain `/`
    (`MCP23017-E/SS`, `KNTC0603/10KF3950`, `LM5116MHX/NOPB`) so a directory
    name is a SANITISED rendering, not the part number. A path is not an MPN."""
    parts, unparsed = {}, []
    base = project / "02_parts"
    if not base.is_dir():
        return parts, unparsed
    for d in sorted(p for p in base.iterdir() if p.is_dir()):
        f = d / "part.yaml"
        if not f.is_file():
            continue
        y = yaml_load(f)
        if "__parse_error__" in y:
            unparsed.append(f"{f.relative_to(project)}: {y['__parse_error__']}")
            continue
        raw = y.get("mpn")
        if isinstance(raw, str) and raw.strip():
            # PyYAML has already removed YAML comments.  A `#` that survives
            # safe_load is therefore data from a quoted scalar and is common
            # in exact Analog Devices orderable MPNs (for example #TRPBF).
            # Splitting it here silently changed the selected part and made
            # Q-IDENT reject the distributor's exact catalog record.
            mpn, src = raw.strip(), "part.yaml mpn:"
        else:
            mpn, src = d.name, "directory name (no mpn: field)"
        p = Part(mpn, src, d.name)
        p.manufacturer = str(y.get("manufacturer") or "").split("#")[0].strip()
        p.type = str(y.get("type") or "").split("#")[0].strip()
        s = y.get("sourcing") or {}
        lc = s.get("lcsc") if isinstance(s, dict) else None
        p.lcsc = (str(lc).split("#")[0].strip().strip('"')
                  if isinstance(lc, str) else None)
        if p.lcsc in ("", "null", "None"):
            p.lcsc = None
        if not p.lcsc:
            p.reasons.append("part.yaml sourcing.lcsc is empty — no fab-library "
                             "line exists, so it is self-supplied")
        for a in (y.get("asserts") or []):
            if isinstance(a, dict) and a.get("assert") == "not_on_assembly_bom":
                p.reasons.append("part.yaml asserts not_on_assembly_bom")
        parts[mpn] = p
    return parts, unparsed


def newest_release_boms(project):
    """-> {board_label: (release_dir_name, bom.csv path)}. Newest release PER
    BOARD, board identity and version ordering both from `release_index`.

    07_releases/ is IMMUTABLE — opened read-only, never written (repo
    CLAUDE.md).

    THIS FUNCTION HELD HALF THE FLEET-WIDE DEFECT. It grouped by board prefix
    correctly, then picked the newest with `d.name > prev[0]` — a TEXT
    comparison, under which `v1.10-2026-07-27` is OLDER than `v1.9-2026-07-27`
    ('1' < '9'). usb-hub-3s-v3 reached a double-digit minor on 2026-07-27, so
    this would have quoted the SUPERSEDED v1.9 BOM — the wrong refdes set, and
    therefore the wrong quantities to order — while naming it as the newest.
    Ordering is now numeric per component, in the one place that owns it
    (canon M-WIDTH).
    """
    out = {}
    rel = project / "07_releases"
    if not rel.is_dir():
        return out
    for _slug, dirs in sorted(_relidx.index(project).items()):
        # newest first, so the first release that actually ships a bom.csv
        # wins — a release without one is skipped, not treated as newest.
        for d in reversed(dirs):
            bom = d / "fab" / "bom.csv"
            if not bom.is_file():
                continue
            # the label is the RELEASE's own spelling of the board, and the
            # project name for the unprefixed `v1.0-DATE` form — unchanged
            # from before; only the ORDERING and the grouping moved.
            raw = (_relidx.parse_release_name(d.name) or ("", ()))[0]
            out[raw or project.name] = (d.name, bom)
            break
    return out


def attach_bom(project, parts, boms):
    """Map BOM rows onto parts. Cooksense-class BOMs ship a BLANK MPN column
    (that is ADR-0006's whole subject), so the match order is LCSC code first,
    then the MPN column, then the Comment token."""
    by_lcsc = {p.lcsc: p for p in parts.values() if p.lcsc}
    by_mpn = {p.mpn: p for p in parts.values()}
    by_dir = {p.dir: p for p in parts.values() if p.dir}
    unmatched = []
    for label, (reldir, bom) in boms.items():
        try:
            rows = list(csv.DictReader(
                bom.open(newline="", errors="replace", encoding="utf-8-sig")))
        except Exception as e:                    # noqa: BLE001
            unmatched.append(f"{label}: cannot read {bom.name}: {e}")
            continue
        for r in rows:
            code = (r.get("LCSC") or "").strip()
            mpn = (r.get("MPN") or "").strip()
            com = (r.get("Comment") or "").strip()
            refs = [x.strip() for x in (r.get("Designator") or "").split(",")
                    if x.strip()]
            p = (by_lcsc.get(code) if code else None) or by_mpn.get(mpn) \
                or by_mpn.get(com) or by_dir.get(com)
            if p is None:
                unmatched.append(
                    f"{label} ({reldir}): BOM row {com!r} refs={len(refs)} "
                    f"LCSC={code or '<blank>'} MPN={mpn or '<blank>'} matches "
                    f"no 02_parts dossier")
                continue
            if mpn and not same_part(mpn, p.mpn):
                unmatched.append(
                    f"{label} ({reldir}): BOM row LCSC={code or '<blank>'} "
                    f"MPN={mpn!r} resolves dossier {p.mpn!r}; exact identity "
                    f"join failed")
                continue
            p.refs.setdefault(label, []).extend(refs)
            if not code:
                p.reasons.append(f"{label} BOM row carries a BLANK LCSC")
    return unmatched


def attach_assembly(project, parts):
    """`03_src/**/rules/assembly.yaml` -> the refs the fab will NOT place."""
    notes = []
    for f in sorted((project / "03_src").rglob("rules/assembly.yaml")):
        y = yaml_load(f)
        if "__parse_error__" in y:
            notes.append(f"{f.relative_to(project)}: {y['__parse_error__']}")
            continue
        for key in ("not_assembled", "consigned"):
            for entry in (y.get(key) or []):
                if not isinstance(entry, dict):
                    continue
                refs = set(entry.get("refs") or [])
                reason = entry.get("reason", "?")
                for p in parts.values():
                    hit = sorted(refs & {r for v in p.refs.values() for r in v})
                    if hit:
                        p.reasons.append(
                            f"assembly.yaml {key}: {', '.join(hit)} "
                            f"({reason}) — hand-soldered, you supply it")
    return notes


# ----------------------------------------------------------- JLC source pool
def read_jlc_snapshot(path, today, max_age_days):
    """Read the machine sidecar emitted by jlc_stock_check.py.

    The sidecar is a dated catalog observation, never an assembly-allocation
    promise. It qualifies as one independent pool only while fresh and only
    when every row can be joined by exact LCSC code, MPN and manufacturer.
    """
    if not path:
        return None, []
    p = Path(path).resolve()
    if not p.is_file():
        return None, [f"JLC snapshot does not exist: {p}"]
    try:
        data = json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception as exc:                         # noqa: BLE001
        return None, [f"JLC snapshot is unparseable: {p}: {exc}"]
    errors = []
    if data.get("tool") != "jlc_stock_check.py":
        errors.append("JLC snapshot `tool` is not jlc_stock_check.py")
    if data.get("stock_source") != "lcsc_catalog_stockCount":
        errors.append("JLC snapshot does not identify lcsc_catalog_stockCount")
    stamp = str(data.get("generated_at") or "")
    if not stamp:
        errors.append("JLC snapshot has no generated_at timestamp; re-run the "
                      "current jlc_stock_check.py instead of trusting an old "
                      "undated observation")
    else:
        try:
            observed = datetime.fromisoformat(stamp.replace("Z", "+00:00")).date()
            age = (today - observed).days
            if age < 0 or age > max_age_days:
                errors.append(f"JLC snapshot age is {age} day(s), outside the "
                              f"0..{max_age_days} day window")
        except ValueError:
            errors.append(f"JLC snapshot generated_at is not ISO-8601: {stamp!r}")
    lines = data.get("lines")
    if not isinstance(lines, list) or not lines:
        errors.append("JLC snapshot has no non-empty `lines` list")
    if data.get("graded_lines") != data.get("total_lines"):
        errors.append("JLC snapshot did not grade every BOM line")
    return (data if not errors else None), errors


def grade_jlc_snapshot(part, qty, boards, min_stock, snapshot):
    if snapshot is None:
        return {"status": "NO-SNAPSHOT", "grade": OWED,
                "manufacturer_match": False,
                "why": "no fresh jlc_stock_check.py JSON was supplied with "
                       "--jlc-stock-json"}
    if not part.lcsc:
        return {"status": "NO-LCSC", "grade": OWED,
                "manufacturer_match": False,
                "why": "part.yaml has no sourcing.lcsc identity"}
    matches = [line for line in snapshot.get("lines", [])
               if str(line.get("lcsc") or "").strip() == part.lcsc]
    if len(matches) != 1:
        return {"status": "JLC-IDENTITY-ERROR", "grade": OWED,
                "manufacturer_match": False,
                "why": f"Q-IDENT: expected exactly one snapshot row for "
                       f"{part.lcsc}, found {len(matches)}"}
    line = matches[0]
    if not same_part(str(line.get("mpn") or ""), part.mpn):
        return {"status": "JLC-IDENTITY-ERROR", "grade": CITED,
                "manufacturer_match": False, "record": line,
                "why": f"Q-IDENT: {part.lcsc} snapshot MPN "
                       f"{line.get('mpn')!r} != dossier {part.mpn!r}"}
    mfr_ok = same_manufacturer(line.get("manufacturer"), part.manufacturer)
    if not part.manufacturer or not mfr_ok:
        return {"status": "MANUFACTURER-MISMATCH", "grade": CITED,
                "manufacturer_match": False, "record": line,
                "why": f"Q-MFR-IDENT: {part.lcsc} snapshot manufacturer "
                       f"{line.get('manufacturer')!r} != dossier "
                       f"{part.manufacturer!r}"}
    per_board = line.get("qty")
    expected = qty / boards if boards else qty
    if not isinstance(per_board, int) or abs(per_board - expected) > 1e-9:
        return {"status": "QTY-MISMATCH", "grade": CITED,
                "manufacturer_match": True, "record": line,
                "why": f"snapshot says {per_board!r}/board but the selected "
                       f"BOM resolves {expected:g}/board; pass --bom for the "
                       f"current candidate and regenerate the snapshot"}
    stock = line.get("stock")
    if line.get("status") != "OK" or not isinstance(stock, (int, float)):
        return {"status": "JLC-NOT-SOURCEABLE", "grade": CITED,
                "manufacturer_match": True, "record": line,
                "why": f"snapshot status={line.get('status')!r}, "
                       f"stock={stock!r}"}
    ok = stock > min_stock and stock >= qty
    why = ""
    if not ok:
        why = (f"Q-STOCK: stock {stock} must be > {min_stock} and >= "
               f"the {qty} needed")
    return {"status": "OK" if ok else "LOW-STOCK", "grade": CITED,
            "manufacturer_match": True, "stock": int(stock),
            "record": line, "why": why,
            "url": "https://jlcpcb.com/parts/componentSearch?searchTxt="
                   + part.lcsc}


# ------------------------------------------------------------------- Mouser
class RecordSet:
    """Every catalog record seen for ONE part, plus WHICH searches produced it.

    `broad_done` is load-bearing: `grade_mouser()` asserts it before it is
    allowed to call anything unsourceable. That is incident 2 made structural."""

    def __init__(self, mpn):
        self.mpn = mpn
        self.searches = []            # [{"kind","query","opt","hits","error"}]
        self.records = []
        self.error = None

    @property
    def broad_done(self):
        return any(s["kind"] == "broad" and not s.get("error")
                   for s in self.searches)

    def add(self, kind, query, opt, payload):
        parts = (payload.get("SearchResults") or {}).get("Parts") or []
        errs = payload.get("Errors") or []
        self.searches.append({"kind": kind, "query": query, "opt": opt,
                              "hits": len(parts),
                              "error": "; ".join(str(e) for e in errs) or None})
        seen = {r["mouser_pn"] for r in self.records}
        for p in parts:
            qty, note = parse_availability(p.get("Availability"))
            rec = {
                "mfr_mpn": p.get("ManufacturerPartNumber"),
                "mouser_pn": p.get("MouserPartNumber"),
                "manufacturer": p.get("Manufacturer"),
                "stock": qty,
                "stock_raw": note,
                "lifecycle": p.get("LifecycleStatus"),
                "factory_stock": p.get("FactoryStock"),
                "lead_time": p.get("LeadTime"),
                "min": p.get("Min"),
                "mult": p.get("Mult"),
                "url": p.get("ProductDetailUrl"),
                "breaks": p.get("PriceBreaks") or [],
                "found_by": kind,
            }
            key = rec["mouser_pn"] or f"{kind}:{rec['mfr_mpn']}"
            if key in seen:
                continue
            seen.add(key)
            self.records.append(rec)


class Mouser:
    def __init__(self, key, cache_dir, replay_dir, offline, budget,
                 use_cache=True):
        self.key = key
        self.cache_dir = cache_dir
        self.replay_dir = replay_dir
        self.offline = offline
        self.budget = budget
        self.use_cache = use_cache
        self.calls = 0
        self.last_call = 0.0

    def _cache_path(self, name):
        return (self.cache_dir / f"{name}.json") if self.cache_dir else None

    def call(self, mpn, opt):
        """-> payload dict. Raises RuntimeError on anything it cannot answer;
        the caller records that as a FAIL, never a skip."""
        name = slug(mpn, opt)
        if self.replay_dir:
            f = self.replay_dir / f"{name}.json"
            if not f.is_file():
                raise RuntimeError(f"replay fixture missing: {f.name}")
            return json.loads(f.read_text(encoding="utf-8-sig"))
        cp = self._cache_path(name)
        if self.use_cache and cp and cp.is_file():
            try:
                d = json.loads(cp.read_text(encoding="utf-8-sig"))
                age = time.time() - float(d.get("fetched_at_epoch", 0))
                if age < CACHE_TTL_S:
                    return d["payload"]
            except Exception:                     # noqa: BLE001
                pass
        if self.offline:
            raise RuntimeError("--offline and no cached/replayed response")
        if not self.key:
            raise RuntimeError("no Mouser API key (see --help): fact is OWED")
        if self.calls >= self.budget:
            raise RuntimeError(f"--call-budget {self.budget} exhausted "
                               f"(Mouser publishes 1000 calls/day)")
        gap = CALL_SPACING_S - (time.time() - self.last_call)
        if gap > 0:
            time.sleep(gap)
        body = json.dumps({"SearchByPartRequest": {
            "mouserPartNumber": mpn, "partSearchOptions": opt}}).encode()
        req = urllib.request.Request(
            f"{MOUSER_URL}?apiKey={self.key}", data=body,
            headers={"Accept": "application/json",
                     "Content-Type": "application/json"})
        self.calls += 1
        self.last_call = time.time()
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                payload = json.load(r)
        except urllib.error.HTTPError as e:
            # The key is in the query string. Scrub it out of every error path.
            raise RuntimeError(redact(f"HTTP {e.code} {e.reason}", self.key))
        except Exception as e:                    # noqa: BLE001
            raise RuntimeError(redact(f"{type(e).__name__}: {e}", self.key))
        if self.use_cache and cp:
            cp.parent.mkdir(parents=True, exist_ok=True)
            cp.write_text(json.dumps({
                "query": {"mpn": mpn, "partSearchOptions": opt},
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "fetched_at_epoch": time.time(),
                "note": "SESSION CACHE. Mouser's API terms forbid caching their "
                        "content; this file is gitignored, TTL-limited and is "
                        "never truth at order time. No API key is stored here.",
                "payload": payload}, indent=1))
        return payload

    def lookup(self, mpn):
        """THE PROTOCOL. Exact on the authoritative MPN, THEN broad on the
        suffix-stripped form — unconditionally, because the exact hit can be a
        stale record that LOOKS like an answer (incident 2)."""
        rs = RecordSet(mpn)
        bare, stripped = strip_packaging_suffixes(mpn)
        try:
            rs.add("exact", mpn, "Exact", self.call(mpn, "Exact"))
        except RuntimeError as e:
            rs.searches.append({"kind": "exact", "query": mpn, "opt": "Exact",
                                "hits": 0, "error": str(e)})
        try:
            rs.add("broad", bare, "None", self.call(bare, "None"))
        except RuntimeError as e:
            rs.searches.append({"kind": "broad", "query": bare, "opt": "None",
                                "hits": 0, "error": str(e)})
        rs.stripped = stripped
        if not rs.records and all(s.get("error") for s in rs.searches):
            rs.error = "; ".join(s["error"] for s in rs.searches
                                 if s.get("error"))
        return rs


def same_part(candidate_mpn, authoritative_mpn):
    """Q-IDENT. A BROAD SEARCH WIDENS THE QUERY, NOT THE PART.

    `B5B-XH-A` broad-searched returns `B5B-XH-A-GU`, `B5B-XH-AM(LF)(SN)` and
    `B5B-XH-A-G` alongside the part we asked for — all in stock, all different
    connectors. Picking the deepest-stock hit would SILENTLY SUBSTITUTE, which
    is the one thing the user asked never to happen. Two MPNs are the same part
    only if they agree once packaging/plating suffixes and separators are
    removed; anything else is a proposal for a human."""
    def norm(s):
        return re.sub(r"[^A-Za-z0-9]", "",
                      strip_packaging_suffixes(str(s or ""))[0]).upper()
    return bool(norm(candidate_mpn)) and norm(candidate_mpn) == \
        norm(authoritative_mpn)


def grade_mouser(rs, qty, min_stock, authoritative_manufacturer=""):
    """-> line dict. Q-WIDE, Q-IDENT and Q-MFR-IDENT are structural."""
    if rs.error:
        return {"status": "LOOKUP-FAILED", "grade": OWED, "why": rs.error}

    for r in rs.records:
        r["is_same_part"] = same_part(r["mfr_mpn"], rs.mpn)
        r["is_same_manufacturer"] = (
            same_manufacturer(r.get("manufacturer"),
                              authoritative_manufacturer)
            if authoritative_manufacturer else True)
    live = [r for r in rs.records if (r["stock"] or 0) > 0]
    same_mpn = [r for r in live if r["is_same_part"]]
    same = [r for r in same_mpn if r["is_same_manufacturer"]]
    best = None
    if same:
        best = sorted(same, key=lambda r: (
            -(r["stock"] or 0),
            (r["lifecycle"] or "").lower() == "obsolete",
            -len(r["breaks"])))[0]

    if best is None:
        # Q-WIDE: no live record is only REPORTABLE once the broad search ran.
        if not rs.broad_done:
            return {"status": "INCONCLUSIVE", "grade": OWED,
                    "why": "Q-WIDE: no live record, and the broad "
                           "(suffix-stripped, partSearchOptions=None) search "
                           "did not complete — a lone exact hit is a prompt to "
                           "search wider, not a finding"}
        if not rs.records:
            return {"status": "NOT-IN-CATALOG", "grade": CITED, "records": 0,
                    "why": f"0 catalog records for {rs.mpn!r} (Exact) or "
                           f"{strip_packaging_suffixes(rs.mpn)[0]!r} (broad). "
                           f"This distributor does not list the part at all — "
                           f"which is a FINDING, not a stock figure"}
        if same_mpn and authoritative_manufacturer:
            seen = ", ".join(sorted({str(r.get("manufacturer") or "<missing>")
                                     for r in same_mpn}))
            return {"status": "MANUFACTURER-MISMATCH", "grade": CITED,
                    "records": len(rs.records),
                    "why": "Q-MFR-IDENT: the orderable MPN text matches, but "
                           f"the authorized catalog records identify {seen}; "
                           f"the dossier authority is "
                           f"{authoritative_manufacturer}. A generic base MPN "
                           f"from another manufacturer is a different part"}
        unparsed = [r for r in rs.records if r["stock"] is None]
        if live and not same:
            alts = ", ".join(f"{r['mfr_mpn']} ({r['stock']} in stock)"
                             for r in live[:4])
            return {"status": "SUBSTITUTE-ONLY", "grade": CITED,
                    "records": len(rs.records),
                    "why": f"Q-IDENT: nothing in stock under the authoritative "
                           f"MPN. In stock under NEIGHBOURING part numbers: "
                           f"{alts}. A near MPN is a PROPOSAL for a human, "
                           f"never a sourced line — this tool will not "
                           f"substitute"}
        if unparsed:
            return {"status": "UNPARSEABLE-AVAILABILITY", "grade": OWED,
                    "why": "Availability field(s) this tool cannot parse: "
                           + "; ".join(sorted({r["stock_raw"]
                                               for r in unparsed}))}
        lifecycles = sorted({(r["lifecycle"] or "-") for r in rs.records})
        return {"status": "NO-STOCK", "grade": CITED,
                "records": len(rs.records),
                "why": f"{len(rs.records)} catalog record(s), every one at 0 "
                       f"stock after the broad search; lifecycle "
                       f"{'/'.join(lifecycles)}"}

    unit, brk, below = price_at(best["breaks"], qty)
    stock = best["stock"]
    ok = stock > min_stock and stock >= qty
    why = ""
    if not ok:
        bits = []
        if stock <= min_stock:
            bits.append(f"stock {stock} is not > the {min_stock} floor")
        if stock < qty:
            bits.append(f"stock {stock} < the {qty} needed")
        why = "Q-STOCK: " + "; ".join(bits)
    # FACTORY STOCK AND LEAD TIME ARE PART OF THE ANSWER. "37 in stock" alone
    # lets someone plan a 200-piece build; 37 in stock / FactoryStock 0 / lead
    # 180 days says the shelf is the whole supply for half a year.
    fs, _ = parse_availability(best.get("factory_stock"))
    caution = (f"distributor stock {stock} is the whole near-term supply: "
               f"FactoryStock {best.get('factory_stock')}, lead "
               f"{best.get('lead_time')} — a re-order is not quick") \
        if (fs == 0) else ""
    return {"status": "OK" if ok else "LOW-STOCK", "grade": CITED,
            "why": why, "caution": caution, "record": best,
            "records": len(rs.records),
            "unit_price": unit, "break_qty": brk, "below_first_break": below,
            "ext_price": round(unit * qty, 4) if unit is not None else None}


# ---------------------------------------------------- manual quotes (D/K, AMZ)
#: The three shapes a hand-recorded distributor fact may take.
#:
#:   product_page    the ONLY admissible source for a STOCK figure.
#:   search_snippet  admissible as a source for NOTHING. Recorded so the report
#:                   can name it and refuse it (incident 1).
#:   catalog_absence the one case where a SEARCH page is legitimate evidence:
#:                   the property "this catalog does not list the part" IS a
#:                   property of the search. Reading PRESENCE off a search page
#:                   is the GHR-10V-S error; reading ABSENCE off one is not.
QUOTE_SOURCES = ("product_page", "search_snippet", "catalog_absence")


def read_manual_quotes(project):
    """`01_docs/sourcing/manual_quotes.yaml` — facts a HUMAN read off a named
    page on a named date. This file is the ONLY way a DigiKey or Amazon number
    enters the report; nothing here is scraped and nothing is inferred."""
    f = project / "01_docs" / "sourcing" / "manual_quotes.yaml"
    if not f.is_file():
        return [], []
    y = yaml_load(f)
    if "__parse_error__" in y:
        return [], [f"manual_quotes.yaml: {y['__parse_error__']}"]
    return list(y.get("quotes") or []), []


def grade_quote(q, qty, min_stock, max_age_days, today,
                authoritative_manufacturer=""):
    """Q-SNIPPET + Q-GRADE over one hand-recorded quote."""
    dist = str(q.get("distributor", "")).lower()
    quoted_manufacturer = str(q.get("manufacturer") or "").strip()
    base = {"distributor": dist, "url": q.get("url"),
            "dpn": q.get("dpn"), "read_on": str(q.get("read_on") or ""),
            "manufacturer": quoted_manufacturer,
            "manufacturer_match": (
                same_manufacturer(quoted_manufacturer,
                                  authoritative_manufacturer)
                if authoritative_manufacturer else True)}
    src = q.get("source")
    if src not in QUOTE_SOURCES:
        return {**base, "status": "QUOTE-INVALID", "grade": OWED,
                "why": f"Q-GRADE: `source:` is {src!r}, not one of "
                       f"{'/'.join(QUOTE_SOURCES)} — an ungraded quote reads as "
                       f"ESTIMATED and a machine may not quietly promote it"}
    if not q.get("url") or not base["read_on"]:
        return {**base, "status": "QUOTE-INVALID", "grade": OWED,
                "why": "Q-SNIPPET: a quote must name the page (`url:`) it was "
                       "read from and the date (`read_on:`) it was read"}
    note = str(q.get("note") or "").strip()
    if src == "search_snippet":
        return {**base, "status": "REFUSED-SNIPPET", "grade": ESTIMATED,
                "why": "Q-SNIPPET: a SEARCH-RESULT SNIPPET IS NOT A STOCK "
                       "FIGURE. GHR-10V-S was reported available on a snippet "
                       "reading 'available to order today with same-day "
                       "shipping'; the product page said In Stock: 0. Open the "
                       "product page and re-record with source: product_page"
                       + (f" — recorded note: {note}" if note else "")}
    if src == "catalog_absence":
        if q.get("listed") is not False:
            return {**base, "status": "QUOTE-INVALID", "grade": OWED,
                    "why": "Q-GRADE: `source: catalog_absence` must carry "
                           "`listed: false` — absence is the only thing it may "
                           "assert"}
        if not note:
            return {**base, "status": "QUOTE-INVALID", "grade": OWED,
                    "why": "Q-GRADE: `source: catalog_absence` must carry a "
                           "`note:` saying WHAT the catalog returned instead — "
                           "'no results' and 'only pack variants' are "
                           "different findings"}
        return {**base, "status": "NOT-IN-CATALOG", "grade": CITED,
                "stock": 0,
                "why": f"catalog searched {base['read_on']}, authoritative MPN "
                       f"not listed as its own orderable line: {note}"}
    try:
        age = (today - date.fromisoformat(base["read_on"])).days
    except ValueError:
        return {**base, "status": "QUOTE-INVALID", "grade": OWED,
                "why": f"Q-SNIPPET: `read_on: {base['read_on']}` is not an "
                       f"ISO date"}
    if age > max_age_days:
        return {**base, "status": "STALE", "grade": ESTIMATED,
                "why": f"Q-SNIPPET: read {age} days ago (> {max_age_days}); "
                       f"stock moves — re-read the product page"}
    stock = q.get("stock")
    if not isinstance(stock, (int, float)):
        return {**base, "status": "QUOTE-INVALID", "grade": OWED,
                "why": f"Q-GRADE: `stock:` is {stock!r}, not a number"}
    stock = int(stock)
    # `price_breaks: [{qty: 1, usd: 3.87}, {qty: 10, usd: 3.448}]` when the page
    # showed a ladder; `unit_price_usd` when it showed one number.
    brk_rows = [(int(b["qty"]), float(b["usd"]))
                for b in (q.get("price_breaks") or [])
                if isinstance(b, dict) and "qty" in b and "usd" in b]
    unit = q.get("unit_price_usd")
    unit = float(unit) if isinstance(unit, (int, float)) else None
    brk_at = None
    if brk_rows:
        brk_rows.sort()
        usable = [r for r in brk_rows if r[0] <= qty] or brk_rows[:1]
        unit, brk_at = usable[-1][1], usable[-1][0]
    # AMAZON IS ALWAYS ESTIMATED. There is no usable API (PA-API needs an
    # affiliate account), listings are third-party-seller-dependent, and both
    # stock and price move without notice. A product page read is the best
    # evidence available and it is still not CITED.
    grade = ESTIMATED if dist == "amazon" else CITED
    ok = stock > min_stock and stock >= qty
    why = ""
    if not ok:
        bits = []
        if stock <= min_stock:
            bits.append(f"stock {stock} is not > the {min_stock} floor")
        if stock < qty:
            bits.append(f"stock {stock} < the {qty} needed")
        why = "Q-STOCK: " + "; ".join(bits)
    if dist == "amazon":
        why = (why + "; " if why else "") + \
            "ESTIMATED by construction — Amazon stock/price are volatile and " \
            "unverifiable; this number may be wrong by the time you read it"
    moq = q.get("min")
    if isinstance(moq, (int, float)) and qty < int(moq):
        why = (why + "; " if why else "") + \
            f"minimum order quantity {int(moq)} exceeds the {qty} needed — the " \
            f"extended price shown is for {qty}, you would pay for {int(moq)}"
    if note:
        why = (why + "; " if why else "") + f"note: {note}"
    return {**base, "status": "OK" if ok else "LOW-STOCK", "grade": grade,
            "stock": stock, "unit_price": unit, "break_qty": brk_at,
            "min": q.get("min"), "mult": q.get("mult"),
            "ext_price": round(unit * qty, 4) if unit is not None else None,
            "lifecycle": q.get("lifecycle"), "why": why}


DIGIKEY_ENABLEMENT = """\
DigiKey HAS an API and this tool does not use it, because it needs OAuth 2.0
client credentials nobody has provided and an agent cannot create an account or
obtain a key. To promote every DigiKey row from ESTIMATED/OWED to CITED:

  1. Sign in at https://developer.digikey.com/ with a DigiKey account.
  2. Create an Organization, then a PRODUCTION app (Sandbox returns
     structurally-correct but incomplete data — do not source from it).
  3. Subscribe the app to **Product Information V4**.
  4. Copy the app's **Client ID** and **Client Secret**.
  5. Append them to `<repo>/.secrets/digikey.env` (mode 600; `.secrets/` is
     already gitignored):
         DIGIKEY_CLIENT_ID=...
         DIGIKEY_CLIENT_SECRET=...
  6. Tell me, and the 2-legged flow (POST client_id + client_secret +
     grant_type=client_credentials to https://api.digikey.com/v1/oauth2/token,
     then GET /products/v4/search/{mpn}/productdetails) becomes a peer of the
     Mouser path.

Until then DigiKey numbers come only from a PRODUCT PAGE a human opened,
recorded in `01_docs/sourcing/manual_quotes.yaml` with its URL and read date.
NEVER from a search-results snippet — that is the GHR-10V-S defect."""


# -------------------------------------------------------------------- report
def render_markdown(ctx):
    L = []
    a = L.append
    a(f"# Shopping list — {ctx['project']}")
    a("")
    a(f"Generated `{ctx['generated']}` by `shopping_list.py` "
      f"(scope `{ctx['scope']}`, {ctx['boards']} board set(s), stock floor "
      f"`> {ctx['min_stock']}`).")
    a("")
    a("**Every number here is a dated OBSERVATION, not a fact.** Stock and "
      "price move; re-run before you pay. Each row carries its M-IMPORT grade: "
      "**CITED** = machine-readable API response or a product page read with "
      "its URL and date · **ESTIMATED** = volatile/unverifiable · **OWED** = "
      "nobody has this number yet.")
    a("")
    a("## Coverage (Q-COVER)")
    a("")
    a(f"- parts in `02_parts/`: **{ctx['total_parts']}**")
    a(f"- selected for this list (`{ctx['scope']}`): **{ctx['selected']}**")
    for d in DISTRIBUTORS:
        c = ctx["coverage"][d]
        a(f"- **{d}**: graded **{c['graded']}/{c['total']}**, "
          f"sourceable **{c['ok']}/{c['total']}**")
    if ctx["required_pools"]:
        c = ctx["jlc_coverage"]
        a(f"- **jlc/lcsc snapshot**: graded **{c['graded']}/{c['total']}**, "
          f"sourceable **{c['ok']}/{c['total']}**")
    if ctx["unparsed"]:
        a("")
        a("**Inputs this tool could not parse — these are FAILURES, not "
          "omissions:**")
        for u in ctx["unparsed"]:
            a(f"- `{u}`")
    a("")
    if ctx["required_pools"]:
        a("## Composed authorized-pool gate (Q-2SOURCE)")
        a("")
        a(f"Each exact manufacturer/MPN row must clear **"
          f"{ctx['required_pools']}** of these independent authorized pools: "
          f"{', '.join(ctx['eligible_pools'])}. Amazon is marketplace evidence "
          f"and never counts. A JLC/LCSC catalog PASS is selection evidence, "
          f"not proof that the assembly uploader will allocate stock.")
        a("")
        a("| exact manufacturer / MPN | needed | qualifying pools | result |")
        a("|---|---:|---|---|")
        for row in ctx["rows"]:
            pools = row.get("authorized_pools") or []
            ok = len(pools) >= ctx["required_pools"]
            a(f"| {row['manufacturer'] or '**MISSING**'} / `{row['mpn']}` | "
              f"{row['qty']} | {', '.join(pools) or 'none'} | "
              f"**{'PASS' if ok else 'FAIL'} "
              f"{len(pools)}/{ctx['required_pools']}** |")
        a("")
        if ctx["pool_failures"]:
            a(f"**COMPOSED-POOLS FAIL:** {len(ctx['pool_failures'])} of "
              f"{ctx['selected']} exact rows do not meet the pool requirement.")
        else:
            a(f"**COMPOSED-POOLS PASS:** {ctx['selected']}/{ctx['selected']} "
              f"exact rows meet the {ctx['required_pools']}-pool requirement.")
        a("")
    a("## Is there one distributor that has everything?")
    a("")
    if ctx["single_source"]:
        a(f"**Yes — {', '.join(ctx['single_source'])}** covers all "
          f"{ctx['selected']} selected lines at stock > {ctx['min_stock']}.")
    else:
        a(f"**No.** No single distributor covers all {ctx['selected']} selected "
          f"lines at stock > {ctx['min_stock']}. Best coverage: " +
          ", ".join(f"{d} {ctx['coverage'][d]['ok']}/"
                    f"{ctx['coverage'][d]['total']}" for d in DISTRIBUTORS)
          + ".")
    a("")

    for d in DISTRIBUTORS:
        a(f"## {d.capitalize()}")
        a("")
        a(f"*Method: {ctx['methods'][d]}*")
        a("")
        a("| MPN | qty | dist. part no. | stock | factory / lead | min/mult | "
          "lifecycle | unit @ break | extended | grade | status | link |")
        a("|---|---:|---|---:|---|---|---|---:|---:|---|---|---|")
        for row in ctx["rows"]:
            r = row["dist"][d]
            rec = r.get("record") or {}
            stock = rec.get("stock", r.get("stock"))
            unit = r.get("unit_price")
            ext = r.get("ext_price")
            url = r.get("url") or rec.get("url") or ""
            link = f"[page]({url})" if url else "—"
            fl = (f"{rec.get('factory_stock')} / {rec.get('lead_time')}"
                  if rec else "—")
            a(f"| `{row['mpn']}` | {row['qty']} | "
              f"{rec.get('mouser_pn') or r.get('dpn') or '—'} | "
              f"{stock if stock is not None else '—'} | {fl} | "
              f"{rec.get('min') or r.get('min') or '—'}/"
              f"{rec.get('mult') or r.get('mult') or '—'} | "
              f"{rec.get('lifecycle') or r.get('lifecycle') or '—'} | "
              f"{('$%.4f @ %s' % (unit, r.get('break_qty'))) if unit is not None else '—'} | "
              f"{('$%.2f' % ext) if ext is not None else '—'} | "
              f"{r['grade']} | {r['status']} | {link} |")
        tot = ctx["totals"][d]
        a("")
        if tot["priced"] == ctx["selected"]:
            a(f"**{d} total: ${tot['usd']:.2f}** — all "
              f"{ctx['selected']} lines sourceable and priced.")
        else:
            a(f"**{d} total: INCOMPLETE — ${tot['usd']:.2f} covers only "
              f"{tot['priced']} of {ctx['selected']} lines.** A total over a "
              f"partial list is not a total. Only SOURCEABLE lines are summed: "
              f"pricing a line you cannot order at the quantity you need "
              f"(0 stock, or an MOQ above the need) gives a number that is "
              f"arithmetically right and operationally false. The missing lines "
              f"are named below.")
        a("")

    a("## Every Mouser catalog record seen, per part")
    a("")
    a("One physical part has SEVERAL catalog records and they disagree — that "
      "is the expected case, not an anomaly, so every record is printed with "
      "its own numbers and the one this list picked is marked. A record whose "
      "manufacturer part number is not the authoritative MPN (modulo "
      "packaging/plating suffixes) is a **substitute proposal for a human**, "
      "never a sourced line (Q-IDENT).")
    a("")
    a("| MPN asked | search | mfr part no. | Mouser no. | stock | lifecycle | "
      "factory / lead | same part? | used |")
    a("|---|---|---|---|---:|---|---|---|---|")
    for row in ctx["rows"]:
        m = row["dist"]["mouser"]
        chosen = (m.get("record") or {}).get("mouser_pn")
        recs = m.get("all_records") or []
        if not recs:
            searched = " + ".join(f"`{s['query']}`/{s['opt']}"
                                  for s in m.get("searches") or [])
            a(f"| `{row['mpn']}` | {searched} | — | — | — | — | — | — | "
              f"**{m['status']}** |")
            continue
        for rec in recs:
            a(f"| `{row['mpn']}` | {rec['found_by']} | `{rec['mfr_mpn']}` | "
              f"{rec['mouser_pn']} | "
              f"{rec['stock'] if rec['stock'] is not None else '**unparseable**'} | "
              f"{rec['lifecycle'] or '—'} | "
              f"{rec['factory_stock']} / {rec['lead_time']} | "
              f"{'yes' if rec.get('is_same_part') else 'NO — different part'} | "
              f"{'**chosen**' if rec['mouser_pn'] == chosen else ''} |")
    a("")
    cautions = [(row["mpn"], row["dist"]["mouser"]["caution"])
                for row in ctx["rows"]
                if row["dist"]["mouser"].get("caution")]
    if cautions:
        a("**Supply cautions (a stock number alone is not a plan):**")
        a("")
        for mpn, c in cautions:
            a(f"- `{mpn}` — {c}")
        a("")

    a("## Distributor gaps — every unavailable line and why")
    a("")
    if not ctx["failures"]:
        a("None. Every queried distributor line cleared its stock floor.")
    else:
        a("| MPN | qty | distributor | status | why |")
        a("|---|---:|---|---|---|")
        for f in ctx["failures"]:
            a(f"| `{f['mpn']}` | {f['qty']} | {f['distributor']} | "
              f"**{f['status']}** | {f['why']} |")
    a("")
    a("## What each line is, and why it is on this list")
    a("")
    a("| MPN | mfr | qty | refs | why self-supplied |")
    a("|---|---|---:|---|---|")
    for row in ctx["rows"]:
        a(f"| `{row['mpn']}` | {row['manufacturer'] or '—'} | {row['qty']} | "
          f"{row['refs'] or '—'} | {'; '.join(row['reasons']) or '—'} |")
    a("")
    a("## DigiKey: what would make these rows CITED")
    a("")
    a("```")
    a(DIGIKEY_ENABLEMENT)
    a("```")
    a("")
    return "\n".join(L).rstrip() + "\n"


# ---------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="per-distributor shopping list with a grade on every number",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=DIGIKEY_ENABLEMENT)
    ap.add_argument("project", help="a project folder (the artifact graded)")
    ap.add_argument("--scope", choices=("self_supplied", "all"),
                    default="self_supplied")
    ap.add_argument("--boards", type=int, default=1,
                    help="how many board sets you are buying for (default 1)")
    ap.add_argument("--min-stock", type=int, default=10,
                    help="a line is sourceable only at stock > this (default 10)")
    ap.add_argument("--quote-max-age-days", type=int, default=7)
    ap.add_argument("--call-budget", type=int, default=200)
    ap.add_argument("--bom", default="",
                    help="current candidate BOM; when supplied it replaces "
                         "sealed-release BOM discovery for quantity/refdes")
    ap.add_argument("--required-pools", type=int, default=0,
                    help="Q-2SOURCE: require each exact row at this many of "
                         "JLC, Mouser and DigiKey; 0 preserves the legacy "
                         "per-distributor shopping verdict")
    ap.add_argument("--jlc-stock-json", default="",
                    help="fresh jlc_stock_check.py JSON sidecar, counted as "
                         "one authorized source pool")
    ap.add_argument("--jlc-max-age-days", type=int, default=7)
    ap.add_argument("--out", default="")
    ap.add_argument("--json", default="")
    ap.add_argument("--replay", default="",
                    help="replay recorded API responses (tests; no network)")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--today", default="", help="override today (tests)")
    a = ap.parse_args(argv)

    if a.required_pools < 0 or a.required_pools > len(AUTHORIZED_POOLS):
        print(f"FAIL Q-2SOURCE: --required-pools must be 0.."
              f"{len(AUTHORIZED_POOLS)}, got {a.required_pools}")
        return 2

    project = Path(a.project).resolve()
    if not project.is_dir():
        print(f"FAIL Q-COVER: project dir does not exist: {project}")
        return 1
    print(f"  input: {project}")

    parts, unparsed = read_parts(project)
    if a.bom:
        candidate_bom = Path(a.bom).resolve()
        if not candidate_bom.is_file():
            print(f"FAIL Q-COVER: --bom does not exist: {candidate_bom}")
            return 2
        boms = {"candidate": ("candidate", candidate_bom)}
    else:
        boms = newest_release_boms(project)
    unparsed += attach_bom(project, parts, boms)
    unparsed += attach_assembly(project, parts)
    quotes, qerr = read_manual_quotes(project)
    unparsed += qerr

    for label, (reldir, bom) in sorted(boms.items()):
        print(f"  BOM input ({label}): {bom} (read-only)")
    if not parts:
        print(f"FAIL Q-COVER: 0 parts under {project.name}/02_parts — a zero "
              f"denominator is a FAIL, never a pass (canon M-COVER)")
        return 1

    selected = ([p for p in parts.values() if p.reasons]
                if a.scope == "self_supplied" else list(parts.values()))
    selected.sort(key=lambda p: p.mpn)
    total, sel = len(parts), len(selected)
    print(f"  scope {a.scope}: {sel}/{total} parts selected")
    if not selected:
        print(f"FAIL Q-COVER: scope {a.scope} selected 0 of {total} parts — a "
              f"gate may not pass while grading nothing")
        return 1

    key, key_prov = load_api_key(project)
    if key:
        print(f"  mouser key: present (from {key_prov}) — never printed/logged")
    else:
        print("  mouser key: ABSENT. Set $MOUSER_API_KEY or create "
              "<repo>/.secrets/mouser.env (mode 600). Every Mouser line will "
              "be graded OWED and this list is NOT sourced.")

    cache = None if a.no_cache else (project / "06_build" / "cache" / "mouser")
    mouser = Mouser(key, cache, Path(a.replay).resolve() if a.replay else None,
                    a.offline, a.call_budget, use_cache=not a.no_cache)

    # Snapshot timestamps are UTC. Using the workstation's local calendar date
    # makes a fresh evening run in the Americas appear one day "in the future"
    # after UTC midnight. Test overrides stay calendar-based and deterministic.
    today = observation_date(a.today)
    jlc_snapshot, jlc_errors = read_jlc_snapshot(
        a.jlc_stock_json, today, a.jlc_max_age_days)
    unparsed += jlc_errors
    qmap = {}
    for q in quotes:
        qmap.setdefault(str(q.get("mpn", "")).strip(), []).append(q)

    rows, failures, pool_failures = [], [], []
    coverage = {d: {"graded": 0, "ok": 0, "total": sel} for d in DISTRIBUTORS}
    jlc_coverage = {"graded": 0, "ok": 0, "total": sel}
    totals = {d: {"usd": 0.0, "priced": 0} for d in DISTRIBUTORS}

    sourcing_started = time.monotonic()
    for source_index, p in enumerate(selected, 1):
        row_started = time.monotonic()
        print(f"  progress sourcing {source_index}/{sel}: {p.mpn} START",
              flush=True)
        qty = max(1, p.ref_count) * a.boards
        row = {"mpn": p.mpn, "mpn_source": p.mpn_source,
               "manufacturer": p.manufacturer, "type": p.type,
               "lcsc": p.lcsc, "qty": qty,
               "refs": "; ".join(f"{k}: {', '.join(v)}"
                                 for k, v in sorted(p.refs.items())),
               "reasons": sorted(set(p.reasons)), "dist": {}}

        rs = mouser.lookup(p.mpn)
        m = grade_mouser(rs, qty, a.min_stock, p.manufacturer)
        m["searches"] = rs.searches
        m["all_records"] = rs.records
        row["dist"]["mouser"] = m

        for d in ("digikey", "amazon"):
            cand = [q for q in qmap.get(p.mpn, [])
                    if str(q.get("distributor", "")).lower() == d]
            if not cand:
                row["dist"][d] = {
                    "status": "NO-QUOTE", "grade": OWED,
                    "why": (f"no {d} quote recorded. Open the PRODUCT PAGE "
                            f"(never a search snippet) and add an entry to "
                            f"01_docs/sourcing/manual_quotes.yaml with its url "
                            f"and read_on date"
                            + ("; the DigiKey API would replace this — see the "
                               "enablement steps at the end of the report"
                               if d == "digikey" else
                               "; Amazon has no usable API (PA-API needs an "
                               "affiliate account) so this stays ESTIMATED "
                               "even once recorded"))}
            else:
                graded = [grade_quote(q, qty, a.min_stock,
                                      a.quote_max_age_days, today,
                                      p.manufacturer)
                          for q in cand]
                good = [g for g in graded if g["status"] == "OK"]
                row["dist"][d] = good[0] if good else graded[0]

        jlc = grade_jlc_snapshot(p, qty, a.boards, a.min_stock, jlc_snapshot)
        row["dist"]["jlc"] = jlc
        if jlc["status"] in GRADED_STATUSES:
            jlc_coverage["graded"] += 1
        if jlc["status"] == "OK":
            jlc_coverage["ok"] += 1

        for d in DISTRIBUTORS:
            r = row["dist"][d]
            if r["status"] in GRADED_STATUSES:
                coverage[d]["graded"] += 1
            if r["status"] == "OK":
                coverage[d]["ok"] += 1
            # A TOTAL COUNTS ONLY WHAT YOU CAN ACTUALLY BUY. Summing a line
            # priced at a quantity you cannot order (MOQ 100 against a need of
            # 2, or a part at 0 stock) produces a number that is arithmetically
            # right and operationally false.
            if r["status"] == "OK" and r.get("ext_price") is not None:
                totals[d]["usd"] += r["ext_price"]
                totals[d]["priced"] += 1
            if r["status"] != "OK":
                failures.append({"mpn": p.mpn, "qty": qty, "distributor": d,
                                 "status": r["status"], "why": r.get("why", "")})

        pools, rejected_pools = [], {}
        if p.manufacturer and jlc["status"] == "OK" \
                and jlc.get("manufacturer_match"):
            pools.append("jlc")
        else:
            rejected_pools["jlc"] = jlc.get("why") or jlc["status"]
        if p.manufacturer and m["status"] == "OK" and m["grade"] == CITED:
            rec = m.get("record") or {}
            if rec.get("is_same_manufacturer"):
                pools.append("mouser")
            else:
                rejected_pools["mouser"] = "Q-MFR-IDENT mismatch or missing"
        else:
            rejected_pools["mouser"] = m.get("why") or m["status"]
        dk = row["dist"]["digikey"]
        if p.manufacturer and dk["status"] == "OK" and dk["grade"] == CITED \
                and dk.get("manufacturer_match"):
            pools.append("digikey")
        else:
            rejected_pools["digikey"] = (
                "Q-MFR-IDENT mismatch or missing on product-page quote"
                if dk["status"] == "OK" and not dk.get("manufacturer_match")
                else dk.get("why") or dk["status"])
        row["authorized_pools"] = pools
        row["rejected_pools"] = rejected_pools
        if a.required_pools and len(pools) < a.required_pools:
            pool_failures.append({
                "mpn": p.mpn, "manufacturer": p.manufacturer,
                "qty": qty, "pools": pools,
                "why": ("part.yaml manufacturer is missing" if not p.manufacturer
                        else f"only {len(pools)} qualifying pool(s): "
                             f"{', '.join(pools) or 'none'}; rejected: "
                             + "; ".join(f"{k}={v}" for k, v in
                                         rejected_pools.items()))})
        rows.append(row)
        print(f"  progress sourcing {source_index}/{sel}: {p.mpn} DONE "
              f"in {time.monotonic() - row_started:.1f}s; authorized pools "
              f"{','.join(pools) or 'none'}", flush=True)

    single = [d for d in DISTRIBUTORS if coverage[d]["ok"] == sel]
    methods = {
        "mouser": "Mouser Search API (search/partnumber). TWO searches per "
                  "part: `Exact` on the authoritative MPN, then `None` on the "
                  "suffix-stripped MPN — one part has several catalog records "
                  "and they disagree. CITED.",
        "digikey": "PRODUCT PAGE read by a human and recorded in "
                   "01_docs/sourcing/manual_quotes.yaml. No API key available "
                   "(OAuth client credentials not provided). CITED from a "
                   "product page; a search snippet is REFUSED.",
        "amazon": "Direct product links only, hand-recorded. No usable API "
                  "(PA-API needs an affiliate account). ESTIMATED, always — "
                  "stock and price are volatile and unverifiable.",
    }
    ctx = {"project": project.name, "scope": a.scope, "boards": a.boards,
           "min_stock": a.min_stock, "total_parts": total, "selected": sel,
           "coverage": coverage, "totals": totals, "rows": rows,
           "failures": failures, "single_source": single, "methods": methods,
           "unparsed": unparsed, "required_pools": a.required_pools,
           "eligible_pools": list(AUTHORIZED_POOLS),
           "pool_failures": pool_failures, "jlc_coverage": jlc_coverage,
           "generated": datetime.now(timezone.utc).strftime(
               "%Y-%m-%d %H:%M UTC"),
           "mouser_calls": mouser.calls, "key_provenance": key_prov}

    if a.out:
        Path(a.out).write_text(render_markdown(ctx))
        print(f"  report -> {a.out}")
    if a.json:
        Path(a.json).write_text(json.dumps(
            {**ctx, "verdict": "PASS" if (
                not unparsed and not (pool_failures if a.required_pools
                                      else failures)) else "FAIL"},
            indent=1, default=str) + "\n")
        print(f"  json   -> {a.json}")

    for d in DISTRIBUTORS:
        c = coverage[d]
        print(f"  {d:9} graded {c['graded']}/{c['total']}, "
              f"sourceable {c['ok']}/{c['total']}")
    for u in unparsed:
        print(f"  FAIL Q-COVER unparsed input: {u}")
    for f in failures:
        print(f"  FAIL {f['status']:24} {f['distributor']:8} {f['mpn']}: "
              f"{f['why']}")
    print(f"  single distributor covering all {sel}: "
          f"{', '.join(single) if single else 'NONE'}")
    if a.required_pools:
        print(f"  jlc       graded {jlc_coverage['graded']}/{sel}, "
              f"sourceable {jlc_coverage['ok']}/{sel}")
        for f in pool_failures:
            print(f"  FAIL Q-2SOURCE {f['manufacturer']} {f['mpn']}: "
                  f"{f['why']}")
        print(f"  composed authorized pools: "
              f"{sel - len(pool_failures)}/{sel} rows meet "
              f"{a.required_pools} independent pool(s)")
    print(f"  mouser API calls this run: {mouser.calls}")
    print(f"  sourcing elapsed: {time.monotonic() - sourcing_started:.1f}s "
          f"for {sel}/{total} selected parts")

    gate_failures = pool_failures if a.required_pools else failures
    bad = len(gate_failures) + len(unparsed)
    if bad:
        if a.required_pools:
            print(f"COMPOSED-POOLS FAIL: {sel}/{total} parts selected, "
                  f"{len(pool_failures)} exact row(s) below the "
                  f"{a.required_pools}-pool requirement and "
                  f"{len(unparsed)} unparseable input(s)")
        else:
            print(f"SHOPPING-LIST FAIL: {sel}/{total} parts selected, "
                  f"{len(failures)} distributor line(s) not sourceable and "
                  f"{len(unparsed)} unparseable input(s)")
        return 1
    if a.required_pools:
        print(f"COMPOSED-POOLS PASS: {sel}/{total} parts selected, every "
              f"exact manufacturer/MPN row sourceable from at least "
              f"{a.required_pools} authorized pools")
        return 0
    print(f"SHOPPING-LIST PASS: {sel}/{total} parts selected, every line "
          f"sourceable at stock > {a.min_stock}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
