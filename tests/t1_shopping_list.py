#!/usr/bin/env python3
"""T1: canon M-QUOTE — a distributor number is a fact from OUTSIDE this repo.

Two incidents found this suite, and they are the same defect one level apart —
the ADJACENT-PROPERTY ERROR, measuring something NEAR the property you need:

  1. GHR-10V-S was reported to the user as available on a DigiKey SEARCH-RESULT
     SNIPPET reading "available to order today with same-day shipping". The
     PRODUCT PAGE said In Stock: 0. That sentence is boilerplate and renders at
     zero stock. The property measured was the state of a SEARCH PAGE.
  2. `10FDZ-BT(S)(LF)(SN)` exact-matched on the Mouser API returns ONE record:
     Availability null, LifecycleStatus **Obsolete**, MouserPartNumber "N/A",
     zero price breaks. The same part searched broad on the suffix-stripped
     `10FDZ-BT` returns **37 In Stock** at $0.96. The property measured was the
     state of a CATALOG ENTRY. It fires THROUGH a machine-readable API, which
     is why "use the API" is not by itself the lesson.

THE HEADLINE FIXTURES ARE BOTH REAL RESPONSES, recorded 2026-07-27 with the API
key redacted (it lives in the query string, never in a body) and replayed —
`tests/fixtures/shopping_list/mouser/`. See that folder's README.md.

RED-VERIFIED, and here are the measurements (new-gate variant, per
tests/README "Adding a regression": `shopping_list.py` did not exist before this
change, so there is no pre-fix code to run the suite against; each headline was
verified against a DELIBERATELY NEUTERED checker and the neutering restored
byte-identical afterwards).

  * Q-WIDE neutered — `lookup()` made exact-only, i.e. the pre-fix method that
    produced incident 2, with the broad search recorded as having run:
      -> 12 passed, 5 FAILED. The two headlines
         (t_broad_search_rescues_the_obsolete_exact_record — 10FDZ-BT reported
         NOT sourceable at 37 in stock; t_exact_only_is_inconclusive_not_a_
         finding), plus three that the same neuter reaches BECAUSE it fabricates
         a successful broad search: t_a_neighbouring_mpn_is_never_substituted,
         t_failed_lookup_is_never_dropped, t_absent_key_degrades_loudly. All
         five are real: with only the exact search this tool cannot tell "the
         part is dead" from "I asked the wrong question".
  * Q-SNIPPET neutered — the `if src == "search_snippet"` branch bypassed so a
    snippet grades like a product page:
      -> 16 passed, 1 FAILED — t_search_snippet_is_never_a_stock_figure, with
         "SHOULD HAVE FAILED but exited 0". The 500-unit snippet sourced the
         line. That is GHR-10V-S reproduced exactly, on demand.
  * Q-IDENT neutered — the `same =` filter in `grade_mouser` replaced by `live`:
      -> 16 passed, 1 FAILED — t_a_neighbouring_mpn_is_never_substituted. The
         tool sourced B5B-XH-A-GU, a different connector, against B5B-XH-A.

  Restored byte-identical after each: 17 passed, 0 failed, 11 known-bad.
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, ROOT, check, contains, main, must_fail,  # noqa: E402
                     must_pass, not_contains, run, test, tmpdir)

SHOP = ROOT / "skills" / "shopping-list" / "scripts" / "shopping_list.py"
FIX = Path(__file__).resolve().parent / "fixtures" / "shopping_list" / "mouser"

#: NEVER let a test reach the network. `--replay` covers the fixture path;
#: MOUSER_API_KEY=none declares the credential explicitly absent so a machine
#: that HAS a real key in .secrets/ cannot accidentally spend it here.
NO_NET = {"MOUSER_API_KEY": "none"}


def project(parts, bom_rows, assembly=None, quotes=None, board="brd"):
    """A miniature project: the same shape shopping_list.py reads on a real
    board — 02_parts dossiers, a SEALED release BOM, assembly intent."""
    d = tmpdir("shop_")
    for name, body in parts.items():
        p = d / "02_parts" / name
        p.mkdir(parents=True)
        (p / "part.yaml").write_text(body)
    rel = d / "07_releases" / f"{board}-v1.0-2026-01-01" / "fab"
    rel.mkdir(parents=True)
    rows = ["Comment,Designator,Footprint,MPN,LCSC"] + list(bom_rows)
    (rel / "bom.csv").write_text("\n".join(rows) + "\n")
    if assembly:
        r = d / "03_src" / board / "rules"
        r.mkdir(parents=True)
        (r / "assembly.yaml").write_text(assembly)
    if quotes:
        s = d / "01_docs" / "sourcing"
        s.mkdir(parents=True)
        (s / "manual_quotes.yaml").write_text(quotes)
    return d


def replay_dir(names):
    """A replay store holding EXACTLY the named fixtures. What is absent is as
    load-bearing as what is present: a missing broad response must make the
    tool INCONCLUSIVE, not confidently wrong."""
    d = tmpdir("replay_")
    for n in names:
        shutil.copy(FIX / f"{n}.json", d / f"{n}.json")
    return d


def write_payload(d, name, parts):
    (d / f"{name}.json").write_text(json.dumps(
        {"Errors": [], "SearchResults": {"NumberOfResult": len(parts),
                                         "Parts": parts}}, indent=1))


FDZ_PART = """\
mpn: 10FDZ-BT(S)(LF)(SN)
manufacturer: JST
type: connector_zif_membrane_1x10
sourcing:
  lcsc: null
"""

FDZ_BOM = ['10FDZ-BT,"J_A,J_B",JST_10FDZ_ZIF,,']


def fdz_project(**kw):
    return project({"10FDZ-BT": FDZ_PART}, FDZ_BOM, **kw)


@test("a quoted hash in an orderable MPN is data, not a YAML comment")
def t_quoted_hash_suffix_survives_part_authority():
    d = project({"ltc": """\
mpn: "LTC3812EFE-5#TRPBF"
manufacturer: Analog Devices
type: buck_controller
"""}, ['LTC3812EFE-5#TRPBF,U1,TSSOP-16,LTC3812EFE-5#TRPBF,'])
    rp = tmpdir("replay_hash_mpn_")
    part = {
        "ManufacturerPartNumber": "LTC3812EFE-5#TRPBF",
        "MouserPartNumber": "584-LTC3812EFE5TRP",
        "Manufacturer": "Analog Devices",
        "Availability": "100 In Stock",
        "LifecycleStatus": "Active",
        "FactoryStock": "1000",
        "LeadTime": "12 Weeks",
        "Min": "1",
        "Mult": "1",
        "ProductDetailUrl": "https://www.mouser.com/example",
        "PriceBreaks": [{"Quantity": 1, "Price": "$1.00", "Currency": "USD"}],
    }
    write_payload(rp, "LTC3812EFE_5_TRPBF_Exact", [part])
    write_payload(rp, "LTC3812EFE_5_TRPBF_None", [part])
    out = d / "r.json"
    r = run([KPY, SHOP, d, "--scope", "all", "--replay", rp,
             "--no-cache", "--json", out], env=NO_NET)
    body = json.loads(out.read_text())
    check(body["rows"][0]["mpn"] == "LTC3812EFE-5#TRPBF",
          "part authority truncated the quoted #TRPBF suffix")
    contains(r.out, "mouser    graded 1/1, sourceable 1/1",
             "the exact #TRPBF record must clear Q-IDENT")


# ----------------------------------------------------------------- headline 1
@test("THE INCIDENT: the broad re-search rescues a part the exact match calls "
      "Obsolete (10FDZ-BT, 37 in stock)")
def t_broad_search_rescues_the_obsolete_exact_record():
    d = fdz_project()
    rp = replay_dir(["10FDZ_BT_S_LF_SN_Exact", "10FDZ_BT_None"])
    out = d / "r.md"
    r = run([KPY, SHOP, d, "--replay", rp, "--no-cache", "--out", out],
            env=NO_NET)
    body = out.read_text()
    # the exact record IS obsolete and IS reported — it is just not the answer
    contains(body, "Obsolete", "every record must be printed with its own numbers")
    contains(body, "306-10FDZBTSLFSN", "the live Mouser record")
    contains(body, "| 37 |", "37 In Stock, from the BROAD search")
    contains(r.out, "mouser    graded 1/1, sourceable 1/1",
             "the part is SOURCEABLE — reporting it obsolete is the incident")
    # and the supply caution: 37 on the shelf, FactoryStock 0, 180-day lead
    contains(body, "FactoryStock 0", "factory stock is part of the answer")
    contains(body, "180 Days", "lead time is part of the answer")


@test("a lone exact hit with no broad search is INCONCLUSIVE, never a finding",
      kind="known_bad")
def t_exact_only_is_inconclusive_not_a_finding():
    """Q-WIDE, and this is incident 2's exact shape: one dead record, read as
    the answer. With the broad response absent the tool must say it does not
    know — the one thing it may NOT do is report the part unsourceable."""
    d = fdz_project()
    rp = replay_dir(["10FDZ_BT_S_LF_SN_Exact"])          # broad deliberately absent
    r = must_fail(run([KPY, SHOP, d, "--replay", rp, "--no-cache"], env=NO_NET),
                  "shopping_list.py with no broad response", "Q-WIDE")
    contains(r.out, "INCONCLUSIVE", "the verdict must name its own ignorance")
    not_contains(r.out, "NO-STOCK",
                 "an unsourceable verdict before the broad search is the bug")


# ----------------------------------------------------------------- headline 2
SNIPPET_QUOTES = """\
quotes:
  - mpn: "10FDZ-BT(S)(LF)(SN)"
    distributor: digikey
    source: search_snippet
    url: "https://www.digikey.com/en/products/result?keywords=GHR-10V-S"
    read_on: 2026-01-01
    stock: 500
    note: "available to order today with same-day shipping"
"""


@test("a SEARCH SNIPPET is never a stock figure, however confident it sounds",
      kind="known_bad")
def t_search_snippet_is_never_a_stock_figure():
    """GHR-10V-S, verbatim. The snippet claims 500 units and the boilerplate
    sentence that fooled a human is right there in the fixture."""
    d = fdz_project(quotes=SNIPPET_QUOTES)
    rp = replay_dir(["10FDZ_BT_S_LF_SN_Exact", "10FDZ_BT_None"])
    r = must_fail(run([KPY, SHOP, d, "--replay", rp, "--no-cache",
                       "--today", "2026-01-02"], env=NO_NET),
                  "shopping_list.py on a snippet-sourced quote", "REFUSED-SNIPPET")
    contains(r.out, "digikey   graded 1/1, sourceable 0/1",
             "a refused snippet leaves the line UNSOURCED")
    contains(r.out, "GHR-10V-S", "the refusal must say which incident it is")


@test("a quote with no url or no read date is invalid, not merely weak",
      kind="known_bad")
def t_quote_without_page_or_date_is_invalid():
    d = fdz_project(quotes="""\
quotes:
  - mpn: "10FDZ-BT(S)(LF)(SN)"
    distributor: digikey
    source: product_page
    stock: 900
""")
    rp = replay_dir(["10FDZ_BT_S_LF_SN_Exact", "10FDZ_BT_None"])
    must_fail(run([KPY, SHOP, d, "--replay", rp, "--no-cache"], env=NO_NET),
              "shopping_list.py on an unsourced quote", "QUOTE-INVALID")


@test("an ungraded quote (`source:` missing) is a FAIL, never a quiet promotion",
      kind="known_bad")
def t_quote_without_a_source_kind_is_a_fail():
    d = fdz_project(quotes="""\
quotes:
  - mpn: "10FDZ-BT(S)(LF)(SN)"
    distributor: digikey
    url: "https://www.digikey.com/en/products/detail/x/y/1"
    read_on: 2026-01-01
    stock: 900
""")
    rp = replay_dir(["10FDZ_BT_S_LF_SN_Exact", "10FDZ_BT_None"])
    must_fail(run([KPY, SHOP, d, "--replay", rp, "--no-cache",
                   "--today", "2026-01-02"], env=NO_NET),
              "shopping_list.py on an ungraded quote", "Q-GRADE")


@test("a stale product-page read is refused as a stock figure", kind="known_bad")
def t_stale_quote_is_refused():
    d = fdz_project(quotes="""\
quotes:
  - mpn: "10FDZ-BT(S)(LF)(SN)"
    distributor: digikey
    source: product_page
    url: "https://www.digikey.com/en/products/detail/x/y/1"
    read_on: 2026-01-01
    stock: 900
""")
    rp = replay_dir(["10FDZ_BT_S_LF_SN_Exact", "10FDZ_BT_None"])
    r = must_fail(run([KPY, SHOP, d, "--replay", rp, "--no-cache",
                       "--today", "2026-03-01"], env=NO_NET),
                  "shopping_list.py on a 59-day-old quote", "STALE")
    contains(r.out, "59 days ago", "say HOW stale, not merely that it is")


# ------------------------------------------------------------------- Q-STOCK
@test("stock EXACTLY at the floor is not sourceable — the bar is > 10, not >= 10",
      kind="known_bad")
def t_stock_at_the_floor_is_not_sourceable():
    """The user's standing requirement is `stock > 10`. An off-by-one here
    sources a line on ten pieces, which is how a build stops halfway."""
    d = fdz_project(quotes="""\
quotes:
  - mpn: "10FDZ-BT(S)(LF)(SN)"
    distributor: amazon
    source: product_page
    url: "https://www.amazon.com/dp/B000000000"
    read_on: 2026-01-01
    stock: 10
    unit_price_usd: 1.5
""")
    rp = replay_dir(["10FDZ_BT_S_LF_SN_Exact", "10FDZ_BT_None"])
    r = must_fail(run([KPY, SHOP, d, "--replay", rp, "--no-cache",
                       "--today", "2026-01-02"], env=NO_NET),
                  "shopping_list.py at stock == the floor", "Q-STOCK")
    contains(r.out, "stock 10 is not > the 10 floor", "name the comparison")


@test("an Amazon product page is ESTIMATED even when it is a real page read")
def t_amazon_is_estimated_even_from_a_product_page():
    d = fdz_project(quotes="""\
quotes:
  - mpn: "10FDZ-BT(S)(LF)(SN)"
    distributor: amazon
    source: product_page
    url: "https://www.amazon.com/dp/B000000000"
    read_on: 2026-01-01
    stock: 500
    unit_price_usd: 1.5
""")
    rp = replay_dir(["10FDZ_BT_S_LF_SN_Exact", "10FDZ_BT_None"])
    out = d / "r.md"
    run([KPY, SHOP, d, "--replay", rp, "--no-cache", "--today", "2026-01-02",
         "--out", out], env=NO_NET)
    amz = out.read_text().split("## Amazon", 1)[1].split("## ", 1)[0]
    contains(amz, "ESTIMATED", "Amazon is ESTIMATED by construction")
    not_contains(amz, "CITED", "no Amazon row may ever grade CITED")


# ------------------------------------------------------------------- Q-IDENT
@test("a NEIGHBOURING mpn found by the broad search is never substituted",
      kind="known_bad")
def t_a_neighbouring_mpn_is_never_substituted():
    """The real B5B-XH-A broad response carries B5B-XH-A-GU / -G / -AM, all in
    stock and all DIFFERENT CONNECTORS. Widening the QUERY must not widen the
    PART: here the authoritative record is forced to 0 stock, so the only live
    hits are the neighbours, and the tool must refuse to source the line."""
    d = project({"B5B-XH-A": "mpn: B5B-XH-A(LF)(SN)\nsourcing:\n  lcsc: null\n"},
                ['B5B-XH-A,"J_L",JST_XH,,'])
    rp = replay_dir(["B5B_XH_A_None"])
    exact = json.loads((FIX / "B5B_XH_A_LF_SN_Exact.json").read_text())
    for p in exact["SearchResults"]["Parts"]:
        p["Availability"] = "0 In Stock"
    (rp / "B5B_XH_A_LF_SN_Exact.json").write_text(json.dumps(exact))
    broad = json.loads((rp / "B5B_XH_A_None.json").read_text())
    for p in broad["SearchResults"]["Parts"]:
        if p.get("ManufacturerPartNumber", "").upper().startswith("B5B-XH-A(") \
                or p.get("ManufacturerPartNumber") == "B5B-XH-A":
            p["Availability"] = "0 In Stock"
    (rp / "B5B_XH_A_None.json").write_text(json.dumps(broad))
    r = must_fail(run([KPY, SHOP, d, "--replay", rp, "--no-cache"], env=NO_NET),
                  "shopping_list.py with only neighbouring MPNs in stock",
                  "Q-IDENT")
    contains(r.out, "SUBSTITUTE-ONLY", "a near MPN is a proposal, not a source")
    contains(r.out, "B5B-XH-A-GU", "name the neighbour so a human can decide")


# ------------------------------------------------------------------- Q-COVER
@test("a project with no parts is a FAIL, never a pass on a zero denominator",
      kind="known_bad")
def t_zero_parts_is_a_fail():
    d = tmpdir("shop_empty_")
    (d / "02_parts").mkdir()
    must_fail(run([KPY, SHOP, d, "--offline", "--no-cache"], env=NO_NET),
              "shopping_list.py on an empty tree", "Q-COVER")


@test("a lookup that FAILED is ungraded and therefore a FAIL, not an omission",
      kind="known_bad")
def t_failed_lookup_is_never_dropped():
    """`bom_source_check` dropped 87 of 673 rows and exited 0. A part this tool
    could not look up must appear in the denominator and in the failures."""
    d = fdz_project()
    rp = tmpdir("replay_empty_")                     # no fixtures at all
    r = must_fail(run([KPY, SHOP, d, "--replay", rp, "--no-cache"], env=NO_NET),
                  "shopping_list.py with every lookup failing", "LOOKUP-FAILED")
    contains(r.out, "mouser    graded 0/1", "0 graded of 1 — the denominator "
                                            "is what makes the gap visible")
    contains(r.out, "10FDZ-BT(S)(LF)(SN)", "the dropped part must be NAMED")


@test("an Availability string the tool cannot parse is a FAIL, never a skip",
      kind="known_bad")
def t_unparseable_availability_is_a_fail():
    d = fdz_project()
    rp = tmpdir("replay_junk_")
    junk = [{"ManufacturerPartNumber": "10FDZ-BT",
             "MouserPartNumber": "306-X", "Availability": "plenty, call us",
             "LifecycleStatus": None, "PriceBreaks": [], "Min": "1",
             "Mult": "1", "FactoryStock": "0", "LeadTime": "1 Days",
             "ProductDetailUrl": "https://example.invalid/x"}]
    write_payload(rp, "10FDZ_BT_S_LF_SN_Exact", junk)
    write_payload(rp, "10FDZ_BT_None", junk)
    must_fail(run([KPY, SHOP, d, "--replay", rp, "--no-cache"], env=NO_NET),
              "shopping_list.py on an unparseable Availability",
              "UNPARSEABLE-AVAILABILITY")


# --------------------------------------------------------------- credentials
@test("with no API key the tool SAYS SO and degrades — it does not crash and "
      "does not produce an unsourced list that looks sourced", kind="known_bad")
def t_absent_key_degrades_loudly():
    d = fdz_project()
    r = must_fail(run([KPY, SHOP, d, "--offline", "--no-cache"], env=NO_NET),
                  "shopping_list.py with no credential", "LOOKUP-FAILED")
    contains(r.out, "mouser key: ABSENT", "the absence must be stated")
    contains(r.out, "this list is NOT sourced", "and its consequence named")
    contains(r.out, "mouser    graded 0/1", "graded nothing, and says so")


@test("the API key never reaches stdout, the report, the json or the cache")
def t_the_key_is_never_printed():
    """The key rides in Mouser's QUERY STRING, so every URL this tool records
    or quotes is a leak site. This test plants a distinctive key and greps
    everything the run produced."""
    fake = "SENTINELKEY-0123456789-do-not-log"
    d = fdz_project()
    rp = replay_dir(["10FDZ_BT_S_LF_SN_Exact", "10FDZ_BT_None"])
    out, js = d / "r.md", d / "r.json"
    r = run([KPY, SHOP, d, "--replay", rp, "--out", out, "--json", js],
            env={"MOUSER_API_KEY": fake})
    not_contains(r.out, fake, "stdout")
    not_contains(out.read_text(), fake, "the markdown report")
    not_contains(js.read_text(), fake, "the json sidecar")
    for f in (d / "06_build").rglob("*"):
        if f.is_file():
            not_contains(f.read_text(errors="replace"), fake, f"cache {f.name}")
    contains(r.out, "never printed/logged", "and it says that it protects it")


@test("no recorded fixture contains anything key-shaped")
def t_fixtures_carry_no_credential():
    """Recording real API responses is how this suite stays offline; it is also
    how a credential gets committed. Mouser puts the key in the URL, not the
    body, so the fixtures should be clean — this test is what makes that a
    checked property rather than a belief."""
    import re
    bad = []
    for f in sorted(FIX.glob("*.json")):
        t = f.read_text()
        for pat in (r"apiKey", r"api_key", r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-"
                    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"):
            if re.search(pat, t):
                bad.append(f"{f.name}: matches {pat}")
    check(not bad, f"credential-shaped content in fixtures: {bad}")
    check(len(list(FIX.glob("*.json"))) >= 6,
          "the fixture store is empty — this suite would prove nothing")


# -------------------------------------------------------------- gate contract
@test("shopping_list.py obeys the gate contract it prints a verdict under")
def t_obeys_the_gate_contract():
    audit = ROOT / "skills" / "kicad-pcb" / "scripts" / "gate_contract_audit.py"
    js = tmpdir("gca_") / "g.json"
    run([KPY, audit, "--root", ROOT, "--json", js])
    rows = json.loads(js.read_text())["gates"]
    mine = [g for g in rows if g["script"].endswith("shopping_list.py")]
    check(len(mine) == 1, f"gate_contract_audit did not see shopping_list.py "
                          f"as a verdict-printing gate: {[g['script'] for g in rows]}")
    g = mine[0]
    check(g["cover"], "G-COVER: no N/M denominator")
    check(g["input"], "G-INPUT: does not name the artifact it graded")
    check(g["red"], "G-RED: no tests/ fixture makes it fail")


# ------------------------------------------------------------- part authority
@test("the MPN authority is the `mpn:` field, not the sanitised directory name")
def t_mpn_authority_is_the_field():
    """Real MPNs contain `/` (`MCP23017-E/SS`, `KNTC0603/10KF3950`) and `*`
    (`2.54-2*20PPC104`), so the directory name is a RENDERING of the part
    number, never the part number. A path is not an MPN."""
    d = project({"MCP23017-E-SS": "mpn: MCP23017-E/SS\nsourcing:\n  lcsc: null\n"},
                ['MCP23017-E/SS,"U1",SSOP,,'])
    rp = tmpdir("replay_none_")
    r = run([KPY, SHOP, d, "--replay", rp, "--no-cache"], env=NO_NET)
    contains(r.out, "MCP23017-E/SS", "the slash-bearing MPN, not the dir name")
    not_contains(r.out, "MCP23017-E-SS ", "the sanitised directory name")


# ------------------------------------------------- release selection (M-WIDTH)
@test("the BOM comes from the board's NUMERICALLY newest release: v1.10 beats "
      "v1.9", kind="known_bad")
def t_newest_release_is_numeric_not_text():
    """`newest_release_boms` grouped by board prefix correctly and then picked
    the newest with `d.name > prev[0]` — a TEXT comparison, under which
    `v1.10-2026-07-27` is OLDER than `v1.9-2026-07-27` because '1' < '9'.

    This is the SAME defect that made policy_audit's M-REL grade the wrong
    release when usb-hub-3s-v3 reached a double-digit minor on 2026-07-27; it
    was fixed there and left standing HERE, which is the M-WIDTH failure — a
    rule written at the width of its incident instead of its class. The
    consequence is not cosmetic: the quantities this tool tells you to buy come
    from the refdes on that BOM, so quoting the superseded release quotes the
    wrong parts list while naming it as the newest.

    RED-VERIFIED 2026-07-27 by restoring `if prev is None or d.name > prev[0]`
    over the same directory listing: this test reports
    `newest release: got 'v1.9-2026-07-27', want 'v1.10-2026-07-27'`.
    """
    import importlib
    sys.path.insert(0, str(ROOT / "skills" / "shopping-list" / "scripts"))
    sl = importlib.import_module("shopping_list")
    d = tmpdir("shopver_")
    (d / "04_kicad").mkdir(parents=True)
    (d / "04_kicad" / "brd.kicad_pcb").write_text("(kicad_pcb)\n")
    for v in ("v1.2-2026-07-23", "v1.9-2026-07-27", "v1.10-2026-07-27"):
        fab = d / "07_releases" / v / "fab"
        fab.mkdir(parents=True)
        fab.joinpath("bom.csv").write_text(
            f"Comment,Designator,Footprint,MPN,LCSC\n{v},R1,0402,X,C1\n")
    got = sl.newest_release_boms(d)
    check(len(got) == 1, f"one board, one series expected: {got}")
    (rel, bom), = got.values()
    check(rel == "v1.10-2026-07-27",
          f"newest release: got {rel!r}, want 'v1.10-2026-07-27' — the "
          f"release list is being ordered as TEXT")
    contains(bom.read_text(), "v1.10-2026-07-27",
             "and the BOM actually read must be that release's")


@test("a MULTI-BOARD project quotes each board's OWN newest release")
def t_multi_board_boms_do_not_cross():
    """The cooksense shape: two series under one 07_releases/. Picking 'the
    last directory' would hand the interposer's BOM to both boards."""
    import importlib
    sys.path.insert(0, str(ROOT / "skills" / "shopping-list" / "scripts"))
    sl = importlib.import_module("shopping_list")
    d = tmpdir("shopmb_")
    (d / "04_kicad").mkdir(parents=True)
    for b in ("cooksense", "interposer"):
        (d / "04_kicad" / f"{b}.kicad_pcb").write_text("(kicad_pcb)\n")
    for v in ("cooksense-v1.0-2026-07-23", "cooksense-v1.4-2026-07-26",
              "interposer-v1.0-2026-07-24"):
        fab = d / "07_releases" / v / "fab"
        fab.mkdir(parents=True)
        fab.joinpath("bom.csv").write_text(
            f"Comment,Designator,Footprint,MPN,LCSC\n{v},R1,0402,X,C1\n")
    got = {k: v[0] for k, v in sl.newest_release_boms(d).items()}
    check(got == {"cooksense": "cooksense-v1.4-2026-07-26",
                  "interposer": "interposer-v1.0-2026-07-24"},
          f"per-board newest release: {got}")


if __name__ == "__main__":
    sys.exit(main())
