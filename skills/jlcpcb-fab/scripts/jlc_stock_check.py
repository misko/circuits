"""Check a JLC-format BOM against the JLCPCB parts library.

    python3 jlc_stock_check.py bom_jlc.csv [--search-missing] [--min-stock 5]
                               [--out report.csv] [--candidates 3]

Plain python3 (no pcbnew needed). BOM columns: Comment,Designator,Footprint,LCSC.

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
args = ap.parse_args()

rows = list(csv.DictReader(open(args.bom)))
coded = [r for r in rows if r.get("LCSC", "").strip()]
uncoded = [r for r in rows if not r.get("LCSC", "").strip()]
print(f"{len(rows)} BOM lines: {len(coded)} with LCSC, {len(uncoded)} without\n")

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

print(f"\n{'FAIL' if failures else 'PASS'}: {failures} coded lines with problems; "
      f"{len(uncoded)} lines still uncoded")
sys.exit(1 if failures else 0)
