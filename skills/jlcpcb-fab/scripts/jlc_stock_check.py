"""Check a JLC-format BOM against the JLCPCB parts library.

    python3 jlc_stock_check.py bom.csv [--search-missing] [--min-stock 5]
                               [--out report.csv] [--json report.json]
                               [--candidates 3]

Plain python3 (no pcbnew needed). BOM columns: Comment,Designator,Footprint,LCSC.

THE VERDICT LINE IS THE GATE (canon A-STOCK). Five sealed releases in this
fleet ship stock evidence whose last line says FAIL — one with the board's own
CPU at stock 0 — because nothing ever parsed it, and the fleet ships THREE
incompatible evidence formats (this script's stdout, its `--out` CSV report,
and a `.csv` file that is really stdout). `--json OUT` writes the ONE
machine-readable sidecar `release_freshness_check.py` grades: per-line
`{lcsc, qty, status, stock}` plus an explicit `verdict`. Ship it in
`07_releases/<rel>/verification/stock_check.json`; a MISSING or UNPARSEABLE
verdict is a FAIL there, never a skip.

- Lines WITH an LCSC code: exact lookup -> stock, basic/extended, price.
  Exit 1 if any coded line is not found or stock < min-stock * qty.
- Lines WITHOUT a code (--search-missing): keyword search from Comment +
  package token; candidates ranked basic-first then stock-desc. These are
  PROPOSALS for a human to confirm — the ranking can't see V/tol/temp specs.
- Unofficial endpoint (verified 2026-07); ~1.2s between calls, don't
  parallelize. Fallback if it breaks: github yaqwsx/jlcparts mirror.
"""
import argparse
import csv
import json
import re
import sys
import time
import urllib.request

URL = ("https://jlcpcb.com/api/overseas-pcb-order/v1/"
       "shoppingCart/smtGood/selectSmtComponentList")


def query(keyword, page_size=10, retries=2):
    body = json.dumps({"currentPage": 1, "pageSize": page_size,
                       "keyword": keyword}).encode()
    req = urllib.request.Request(URL, data=body, headers={
        "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                d = json.load(r)
            return d["data"]["componentPageInfo"]["list"] or []
        except Exception as e:  # noqa: BLE001 — unofficial endpoint, retry all
            if attempt == retries:
                print(f"  ! query failed for {keyword!r}: {e}", file=sys.stderr)
                return None
            time.sleep(3 * (attempt + 1))


def normalize_value(tok):
    """RKM notation -> JLC search notation: 2u2 -> 2.2uF, 4k7 -> 4.7k,
    0R22 -> 0.22, 100n -> 100nF. JLC's search matches '2.2uF' listings
    (basic, megastock) but NOT '2u2' (hits zero-stock consigned noise)."""
    tok = re.sub(r"^(\d+)[uµ](\d+)$", r"\1.\2uF", tok)
    tok = re.sub(r"^(\d+)n(\d+)$", r"\1.\2nF", tok)
    tok = re.sub(r"^(\d+)p(\d+)$", r"\1.\2pF", tok)
    tok = re.sub(r"^(\d+)[kK](\d+)$", r"\1.\2k", tok)
    tok = re.sub(r"^(\d+)[mM](\d+)$", r"\1.\2m", tok)
    tok = re.sub(r"^(\d+)R(\d+)$", r"\1.\2", tok)
    tok = re.sub(r"^(\d+(?:\.\d+)?)[uµ]$", r"\1uF", tok)
    tok = re.sub(r"^(\d+(?:\.\d+)?)n$", r"\1nF", tok)
    tok = re.sub(r"^(\d+(?:\.\d+)?)p$", r"\1pF", tok)
    return tok


def pkg_token(footprint):
    m = re.search(r"(0201|0402|0603|0805|1206|1210|2010|2512)", footprint)
    if m:
        return m.group(1)
    m = re.match(r"([A-Za-z]+-?\d+[\w-]*?)(?:_|$)", footprint)
    return m.group(1) if m else ""


def fields(c):
    return {"code": c.get("componentCode", ""),
            "type": c.get("componentLibraryType", ""),
            "stock": c.get("stockCount", 0),
            "mpn": c.get("componentModelEn", ""),
            "pkg": c.get("componentSpecificationEn", ""),
            "price": (c.get("componentPrices") or [{}])[0].get("productPrice", "")}


ap = argparse.ArgumentParser()
ap.add_argument("bom")
ap.add_argument("--search-missing", action="store_true")
ap.add_argument("--min-stock", type=int, default=5,
                help="fail if stock < this many x qty (default 5 boards)")
ap.add_argument("--candidates", type=int, default=3)
ap.add_argument("--out", default="")
ap.add_argument("--json", default="",
                help="machine-readable sidecar (per-line status/stock + an "
                     "explicit verdict) — the format the A-STOCK release gate "
                     "grades; ship it as verification/stock_check.json")
args = ap.parse_args()

rows = list(csv.DictReader(open(args.bom, encoding="utf-8-sig")))
coded = [r for r in rows if r.get("LCSC", "").strip()]
uncoded = [r for r in rows if not r.get("LCSC", "").strip()]
print(f"input: bom = {args.bom}")
print(f"{len(rows)} BOM lines: {len(coded)} with LCSC, {len(uncoded)} without\n")

# G-COVER (canon M-COVER, 2026-07-27). The verdict counted PROBLEMS, never what
# it had looked at, so an EMPTY BOM — a wrong path, a header-only CSV, a
# filename that is not in the release (the `bom_source_check` defect, ADR-0004)
# — printed `PASS: 0 coded lines with problems` and exit 0. Worse, the --json
# sidecar wrote `"verdict": "PASS"` for that run, and release_freshness A-STOCK
# READS that field: a zero-coverage run could clear the release gate.
#
# `nothing_graded` is computed HERE, before the sidecar is written, so the
# sidecar and the exit code can never disagree.
nothing_graded = ""
if not rows:
    nothing_graded = (f"0/0 BOM lines graded — {args.bom} yielded no rows at "
                      f"all. A zero denominator is a FAIL, never a pass; check "
                      f"that this is the BOM the release actually ships.")
elif not coded:
    nothing_graded = (f"0/{len(rows)} BOM lines graded — every line in "
                      f"{args.bom} lacks an LCSC code, so stock was queried "
                      f"for NONE of them. Nothing here was checked.")

report, failures = [], 0

for r in coded:
    code, qty = r["LCSC"].strip(), len(r["Designator"].split(","))
    hits = query(code, page_size=5)
    time.sleep(1.2)
    exact = next((fields(c) for c in (hits or [])
                  if c.get("componentCode") == code), None)
    if hits is None:
        status = "QUERY_FAILED"; failures += 1
    elif exact is None:
        status = "NOT_FOUND"; failures += 1
    elif exact["stock"] < args.min_stock * qty:
        status = f"LOW_STOCK({exact['stock']})"; failures += 1
    else:
        status = "OK"
    e = exact or {}
    print(f"  {status:16} {code:10} x{qty:<3} {r['Comment'][:36]:38} "
          f"{e.get('type', ''):6} stock={e.get('stock', '-')}")
    report.append({**r, "qty": qty, "status": status, **e})

if args.search_missing and uncoded:
    print("\n-- proposals for uncoded lines (HUMAN MUST CONFIRM SPECS) --")
    for r in uncoded:
        qty = len(r["Designator"].split(","))
        kw = (f"{normalize_value(r['Comment'].split()[0])} "
              f"{pkg_token(r['Footprint'])}").strip()
        hits = query(kw)
        time.sleep(1.2)
        if not hits:
            print(f"  NO_MATCH        {'':10} x{qty:<3} {r['Comment'][:36]:38} "
                  f"(searched {kw!r})")
            report.append({**r, "qty": qty, "status": "NO_MATCH"})
            continue
        # out-of-stock last (a 0-stock basic part is not orderable at any
        # tier); then basic-first, then deepest stock
        cands = sorted((fields(c) for c in hits),
                       key=lambda f: (f["stock"] <= 0,
                                      f["type"] != "base", -f["stock"]))
        best = cands[0]
        print(f"  PROPOSE {best['code']:10} x{qty:<3} {r['Comment'][:36]:38} "
              f"{best['type']:6} stock={best['stock']} {best['mpn'][:24]} "
              f"[{best['pkg']}]")
        for alt in cands[1:args.candidates]:
            print(f"      alt {alt['code']:10} {alt['type']:6} "
                  f"stock={alt['stock']} {alt['mpn'][:24]} [{alt['pkg']}]")
        report.append({**r, "qty": qty, "status": "PROPOSED", **best})

if args.out:
    keys = ["Comment", "Designator", "Footprint", "LCSC", "qty", "status",
            "code", "type", "stock", "mpn", "pkg", "price"]
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(report)
    print(f"\nreport -> {args.out}")

if args.json:
    # The ONE machine-readable form. `verdict` is written EXPLICITLY: a reader
    # must never have to infer PASS from the absence of a FAIL line.
    with open(args.json, "w") as f:
        json.dump({"tool": "jlc_stock_check.py",
                   "bom": str(args.bom),
                   "min_stock_per_board": args.min_stock,
                   "verdict": "FAIL" if (failures or nothing_graded) else "PASS",
                   # THE LIMIT TRAVELS WITH THE VERDICT (canon M-QUOTE,
                   # 2026-07-27). This tool reads `stockCount`, which is LCSC
                   # CATALOG stock. JLC's assembly uploader allocates from a
                   # DIFFERENT pool, so a PASS here does NOT predict that a
                   # line will clear at order time. Measured: usb-hub v1.11's
                   # predecessor shipped this sidecar saying
                   #   "C25744 ... status: OK, stock: 291"  verdict: PASS
                   # and JLC refused that exact line hours later ("10
                   # shortfall"), because LCSC's catalog held 291 while JLC's
                   # assembly warehouse held none. A FAIL from this tool is
                   # REAL -- an outright stock-out is a stock-out. A PASS is
                   # NECESSARY AND NOT SUFFICIENT, and the only instrument that
                   # answers "will it clear" is the uploader itself (F-ECHO).
                   # Emitted as a field, not a comment, because
                   # release_freshness A-STOCK READS this file and a reader of
                   # the sidecar alone must see the limit.
                   "stock_source": "lcsc_catalog_stockCount",
                   "predicts_jlc_assembly_allocation": False,
                   "pass_means": ("catalog stock >= min_stock x qty at query "
                                  "time; NOT that JLC will allocate the line "
                                  "-- see F-ECHO"),
                   "graded_lines": len(coded),
                   "total_lines": len(rows),
                   "zero_coverage": nothing_graded or None,
                   "failures": failures,
                   "uncoded_lines": len(uncoded),
                   "lines": [{"lcsc": r.get("LCSC", "").strip(),
                              "designators": r.get("Designator", ""),
                              "qty": r.get("qty"),
                              "status": r.get("status"),
                              "stock": r.get("stock"),
                              "type": r.get("type", ""),
                              "mpn": r.get("mpn", "")}
                             for r in report]}, f, indent=1)
    print(f"json -> {args.json}")

# Uncoded lines are NOT graded by this tool at all — they carry no LCSC to
# query — so they were silently outside the denominator while reading as part
# of a passing run. The verdict now states both numbers.
graded, total = len(coded), len(rows)

# SCOPE, printed on EVERY exit path -- pass, fail, or zero-coverage. It sat
# below the `nothing_graded` early-exit at first, so the one run that grades
# NOTHING was also the one run that never said what it grades. Moved here after
# the test for it went red, which is the whole argument for writing the test.
#
# The failure mode this addresses: a reader takes a PASS as "this will clear at
# JLC". It will not. Measured 2026-07-27 -- this tool passed C25744 at
# "stock: 291" and JLC refused that exact line the same day with "10
# shortfall", because LCSC's catalog held 291 and JLC's assembly warehouse held
# none. Canon M-QUOTE.
SCOPE = ("  SCOPE: graded against LCSC CATALOG stock (stockCount). JLC's "
         "assembly uploader\n"
         "  allocates from a DIFFERENT pool, so a PASS here does NOT mean the "
         "line will\n"
         "  clear at order time. A FAIL is real; a PASS is necessary and not "
         "sufficient.\n"
         "  The only instrument that answers 'will it clear' is the uploader "
         "itself — F-ECHO.")

if nothing_graded:
    print(f"\nFAIL: {nothing_graded} (canon M-COVER)")
    print(SCOPE)
    sys.exit(1)
print(f"\n{'FAIL' if failures else 'PASS'}: {graded - failures}/{graded} coded "
      f"BOM lines have stock >= {args.min_stock} x qty ({failures} with "
      f"problems); {len(uncoded)}/{total} lines carry NO LCSC and were NOT "
      f"graded by this tool")
print(SCOPE)
sys.exit(1 if failures else 0)
