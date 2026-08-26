#!/usr/bin/env python3
"""T1: bom_source_check.py + the export_jlc_package grouping fix.

The incident (usb-hub-3s-v3 v1.1, 2026-07-23)
---------------------------------------------
The KiCad board carries only a Value string per footprint ("10uF"), never the
LCSC code. `export_jlc_package.py` grouped footprints by (Value, Footprint) and
re-attached codes from a value-token carry-over — so two DISTINCT parts sharing
a value+footprint collapsed onto ONE BOM row under a SINGLE code:

  source: C9-C12,C24-C27 = C77102 (10uF *50V*)  ·  C49,C50 = C77100 (10uF *25V*)
  shipped BOM: all ten on one row coded C77100 → 25V caps on a 50V input rail.

and the 100uF output cap was substituted C84455 (10V) → C90143 (16V). The BOM
passed every gate because none compared it to the source.

Two things are pinned here:
  1. the GATE (`bom_source_check.py`) FAILS a merged / substituted / missing /
     dropped-vendored BOM and PASSES a correct one — including the REAL sealed
     v1.1 artifact (regression fixture);
  2. the EXPORTER, given the source circuit.json, splits two distinct-code caps
     onto SEPARATE rows (the fix) — red-verified in the docstring against the
     pre-fix (Value,Footprint) grouping which re-merges them.
"""
import csv
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (FAB_SCRIPTS, KPY, ROOT, check, contains, eq, main,  # noqa: E402
                     must_fail, must_pass, run, test, tmpdir)

sys.path.insert(0, str(FAB_SCRIPTS))
import bom_source_check as bsc  # noqa: E402

GATE = FAB_SCRIPTS / "bom_source_check.py"
EXPORT = FAB_SCRIPTS / "export_jlc_package.py"
V3 = ROOT / "projects" / "usb-hub-3s-v3"
POD = ROOT / "archived_projects" / "crow-mic-pod-v2"


def circuit(codes):
    """A minimal circuit.json: {refdes: lcsc} -> source_component list."""
    return [{"type": "source_component", "name": r,
             "supplier_part_numbers": {"jlcpcb": [c]} if c else {}}
            for r, c in codes.items()]


def write_case(d, refdes_codes, bom_rows):
    """circuit.json + a fab bom.csv in dir d. bom_rows entries are
    (comment, [refs], code) or, to exercise leg C's value check,
    (comment, [refs], code, mpn) / (comment, [refs], code, mpn, footprint)."""
    (d / "circuit.json").write_text(json.dumps(circuit(refdes_codes)))
    with open(d / "bom.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "MPN", "LCSC"])
        for row in bom_rows:
            comment, refs, code = row[0], row[1], row[2]
            mpn = row[3] if len(row) > 3 else ""
            fp = row[4] if len(row) > 4 else "C_1210_3225Metric"
            w.writerow([comment, ",".join(refs), fp, mpn, code])
    return d


# the two-distinct-codes-one-value case, at the heart of the incident
SRC = {"C9": "C77102", "C10": "C77102", "C49": "C77100", "C50": "C77100"}


# --------------------------------------------------------------- clean cases
@test("gate PASSES a BOM whose two same-value caps are SEPARATE code rows")
def t_clean_split():
    d = write_case(tmpdir("bomsrc_"), SRC, [
        ("10uF 50V", ["C9", "C10"], "C77102"),
        ("10uF 25V", ["C49", "C50"], "C77100")])
    r = must_pass(run([KPY, GATE, d / "bom.csv", d / "circuit.json"]),
                  "gate on a correctly-split BOM")
    contains(r.out, "PASS", "verdict")


@test("gate PASSES an uncoded hand-solder row (no source code, nothing to check)")
def t_clean_uncoded():
    d = write_case(tmpdir("bomsrc_"), {"J1": ""}, [("USB-C", ["J1"], "")])
    must_pass(run([KPY, GATE, d / "bom.csv", d / "circuit.json"]),
              "gate on an uncoded row")


@test("gate READS a circuit.json carrying a UTF-8 BOM instead of crashing",
      kind="known_bad")
def t_utf8_bom_circuit_json():
    """Found running the gate on a project dir, 2026-07-29: it died with
    `json.decoder.JSONDecodeError: Unexpected UTF-8 BOM (decode using
    utf-8-sig)`. A CRASH is the worst possible verdict — worse than a FAIL,
    because the wrapper reads a non-zero exit as "gate ran and objected" and a
    human reads the traceback as a broken test rather than an ungraded BOM. The
    three bytes EF BB BF are what any Windows editor and several exporters
    prepend, so this is an input the gate must simply accept.

    Note the encoding is a decode concern for EVERY hand-authorable source the
    skills read, not just this one file: the fix is `encoding="utf-8-sig"` at
    all 124 read sites across skills/, not a patch at the one that happened to
    crash first (canon M-WIDTH).

    RED-VERIFIED: with `read_text()` restored at bom_source_check.py:106 this
    fixture dies on the JSONDecodeError instead of reporting a verdict."""
    d = write_case(tmpdir("bomsrc_bom_"), SRC, [
        ("10uF 50V", ["C9", "C10"], "C77102"),
        ("10uF 25V", ["C49", "C50"], "C77100")])
    cj = d / "circuit.json"
    cj.write_bytes(b"\xef\xbb\xbf" + cj.read_bytes())    # prepend the BOM
    r = must_pass(run([KPY, GATE, d / "bom.csv", cj]),
                  "gate on a BOM-prefixed circuit.json")
    check("JSONDecodeError" not in r.out and "Traceback" not in r.out,
          f"the gate must report a verdict, not a traceback:\n{r.out}")
    contains(r.out, "PASS", "verdict")


# ------------------------------------------ non-LCSC supplier handle blanking
@test("refdes_codes_from_circuit blanks a non-C supplier HANDLE (an MPN) and "
      "keeps a real C-code verbatim")
def t_nonC_supplier_handle_blanked():
    """The fix-pass change (crow-mic-pod-v2, 2026-07-23). A hand-solder part with
    no JLC listing carries its MPN in supplier_part_numbers.jlcpcb as an
    FPID-RESOLUTION HANDLE (MK1 = "AOM-5024L-HD-R", used by the converter to map
    to the 02_parts footprint). That MPN is NOT an LCSC code and must never land
    in a BOM LCSC column, so refdes_codes_from_circuit maps it to "" while keeping
    a real C-code untouched. BOTH the M-BOM gate and export_jlc_package import
    this fn, so the single guard fixes both consumers (and stops the gate
    false-failing a MISSING-code on the hand-solder line).

    RED-VERIFY (performed 2026-07-23): reverting the guarded return to the pre-fix
    `out[name] = (jlc[0] if ...)` (no `re.fullmatch(r"C\\d+", code)`) makes this
    test FAIL — MK1 comes back as "AOM-5024L-HD-R"; restoring the guard PASSES."""
    cj = tmpdir("nonc_") / "circuit.json"
    cj.write_text(json.dumps(circuit(
        {"MK1": "AOM-5024L-HD-R", "D3": "C559105", "U1": "C192421"})))
    codes = bsc.refdes_codes_from_circuit(cj)
    eq(codes["MK1"], "", "an MPN handle must be blanked (it is not an LCSC)")
    eq(codes["D3"], "C559105", "a real C-code must be kept verbatim")
    eq(codes["U1"], "C192421", "a real C-code must be kept verbatim")


# ------------------------------------------------------------ known-bad cases
@test("gate FAILS a MERGED row: two source codes collapsed onto one line "
      "(the v1.1 defect)", kind="known_bad")
def t_kb_merged():
    """C9/C10 (C77102, 50V) and C49/C50 (C77100, 25V) share value+footprint;
    the pre-fix exporter put all four on one C77100 row. The gate must reject
    ANY BOM that carries two distinct source codes on one line, however made."""
    d = write_case(tmpdir("bomsrc_"), SRC,
                   [("10uF", ["C9", "C10", "C49", "C50"], "C77100")])
    r = run([KPY, GATE, d / "bom.csv", d / "circuit.json"])
    must_fail(r, "gate on a merged row", "MERGED")
    contains(r.out, "C77102", "must name the collapsed distinct code")


@test("gate FAILS a SUBSTITUTED code: BOM code != source code", kind="known_bad")
def t_kb_substituted():
    """The 100uF C84455->C90143 substitution class: the row's single source
    code is C84455 but the BOM shipped a different one."""
    d = write_case(tmpdir("bomsrc_"), {"C14": "C84455", "C15": "C84455"},
                   [("100uF", ["C14", "C15"], "C90143")])
    r = run([KPY, GATE, d / "bom.csv", d / "circuit.json"])
    must_fail(r, "gate on a substituted code", "SUBSTITUTED")
    contains(r.out, "C84455", "must name the source code")


@test("gate FAILS a MISSING code: source has a code, BOM line is blank",
      kind="known_bad")
def t_kb_missing():
    d = write_case(tmpdir("bomsrc_"), {"C1": "C77102"},
                   [("10uF", ["C1"], "")])
    must_fail(run([KPY, GATE, d / "bom.csv", d / "circuit.json"]),
              "gate on a blank code", "MISSING")


@test("gate leg B FAILS a DROPPED vendored code: a part.yaml code the build "
      "uses is absent from the BOM (independent of circuit.json)", kind="known_bad")
def t_kb_dropped_vendored():
    """The part.yaml-side leg, which never reads circuit.json: C84455 is
    vendored AND used, but the BOM ships C90143 instead, so C84455 is nowhere
    on the BOM. Catches the substitution from the OTHER source (canon M1)."""
    d = tmpdir("bomsrc_")
    write_case(d, {"C14": "C84455"}, [("100uF", ["C14"], "C90143")])
    parts = d / "02_parts" / "GRM32ER61A107ME20L"
    parts.mkdir(parents=True)
    (parts / "part.yaml").write_text(
        "sourcing: {lcsc: C84455, alternates: [C97170]}\n")
    r = run([KPY, GATE, d / "bom.csv", d / "circuit.json",
             "--parts", d / "02_parts"])
    must_fail(r, "gate on a dropped vendored code", "DROPPED")
    contains(r.out, "C84455", "must name the vetted code that vanished")


@test("gate leg B does NOT false-positive on a basic-library passive with no "
      "part.yaml")
def t_clean_legb_no_falsepos():
    """A resistor coded from JLC's basic library that we never vendored as a
    part.yaml must not be flagged — leg B iterates vendored parts, not BOM
    rows, so an un-vendored code is simply not its concern."""
    d = tmpdir("bomsrc_")
    write_case(d, {"R1": "C25804"}, [("10kΩ", ["R1"], "C25804")])
    (d / "02_parts").mkdir()
    must_pass(run([KPY, GATE, d / "bom.csv", d / "circuit.json",
                   "--parts", d / "02_parts"]),
              "gate must ignore an un-vendored basic-library code")


# ------------------------------------------------------- REAL incident fixture
@test("gate FAILS the REAL sealed usb-hub-3s-v3 v1.1 fab BOM (merge + "
      "substitution)", kind="known_bad")
def t_kb_real_v1_1():
    """Pins the actual shipped artifact. The sealed 07_releases/v1.1 fab/bom.csv
    merged C77102 (50V) onto the C77100 (25V) row and substituted the 100uF
    output cap C84455->C90143; the current build's circuit.json is the source."""
    bom = V3 / "07_releases" / "v1.1-2026-07-23" / "fab" / "bom.csv"
    cj = V3 / "03_tscircuit" / "build" / "circuit.json"
    if not bom.exists() or not cj.exists():
        return  # project trimmed from this checkout; nothing to pin
    r = run([KPY, GATE, bom, cj, "--parts", V3 / "02_parts"])
    must_fail(r, "gate on the sealed v1.1 defect", "MERGED")
    contains(r.out, "C77102", "50V input-cap code the row collapsed")
    contains(r.out, "SUBSTITUTED", "the 100uF output-cap substitution")


# ------------------------------- leg C: SEMANTIC value consistency (v1.2 gap)
# usb-hub-3s-v3 v1.2 (2026-07-23) shipped R12 = C2933210 (MPN FRC0603F3741TS =
# 3.74k) while the row LABEL said "4.12kΩ" -> buck-C setpoint ~4.97V undervoltage.
# Legs A/B check CODE IDENTITY (BOM code == source code) and PASSED — they are
# blind to the LCSC's actual catalog value. Leg C parses the MPN's encoded value
# OFFLINE and compares it to the label.

@test("leg C parsers decode EIA/RKM resistor + ceramic-cap MPNs and passive "
      "labels (the offline engine)")
def t_legc_parsers():
    """Unit-level proof of the value engine, independent of the gate wiring.
    FRC0603F3741TS -> 374×10^1 = 3.74k (the v1.2 part); FRC0603F4121TS -> 4120
    (the value it SHOULD have been). RKM and 4-digit EIA both covered; an MPN we
    cannot confidently parse returns None (-> the gate FLAGs it, never passes)."""
    eq(bsc.mpn_resistance("FRC0603F3741TS", "R_0603_1608Metric"), 3740.0,
       "EIA 3741 -> 3.74k (the shipped v1.2 R12)")
    eq(bsc.mpn_resistance("FRC0603F4121TS", "R_0603_1608Metric"), 4120.0,
       "EIA 4121 -> 4.12k (the intended R12)")
    eq(bsc.mpn_resistance("RC0603FR-074K12L", "R_0603_1608Metric"), 4120.0,
       "Yageo RKM 4K12 -> 4.12k")
    eq(bsc.mpn_resistance("RC1206FR-072R2L", "R_1206_3216Metric"), 2.2,
       "RKM 2R2 -> 2.2Ω")
    eq(bsc.mpn_resistance("MYSTERY-PART-XYZ", "R_0603"), None,
       "an MPN with no decodable value must return None (-> FLAG, not pass)")
    check(abs(bsc.mpn_capacitance("GRM188R71H104KA01", "C_0603_1608Metric") - 1e-7)
          < 1e-12, "ceramic 104K -> 100nF")
    eq(bsc.labeled_resistance("4.12kΩ"), 4120.0, "label 4.12kΩ")
    eq(bsc.labeled_resistance("4k7"), 4700.0, "RKM label 4k7")
    check(abs(bsc.labeled_capacitance("100nF") - 1e-7) < 1e-12, "label 100nF")


@test("labeled_resistance: lowercase m is MILLI, uppercase M is MEGA")
def t_legc_milli_is_not_mega():
    """`labeled_resistance("10mΩ")` returned 1.0e7 — the multiplier was
    UPPERCASED before lookup, so milli decoded as mega. A 10 mΩ current-sense
    shunt read as 10 MΩ: a factor of 1e9 on the part that sets BOTH LM5116 buck
    current limits.

    It was invisible because `row_kind` dropped the only rows that use it
    (RS1/RS2) — two defects cancelling, which is why neither was ever observed.
    The repo's own electrical_invariants contract already stated the rule
    ("`m` is MILLI and `M` is MEGA"); this table did not obey it, and the
    module docstring even documented the hazard as a reason to prefer the
    numeric prop rather than fixing the decoder.

    RED-verified: restoring `.upper()` on the multiplier lookup makes the
    10mΩ assertion below return 1e7.
    """
    eq(bsc.labeled_resistance("10mΩ"), 0.01, "10mΩ is ten MILLIohms")
    eq(bsc.labeled_resistance("10MΩ"), 1e7, "10MΩ is ten MEGohms")
    eq(bsc.labeled_resistance("5mΩ"), 0.005, "5mΩ")
    eq(bsc.labeled_resistance("1M"), 1e6, "bare 1M is mega")
    eq(bsc.labeled_resistance("100k"), 1e5, "lowercase k is still kilo")
    eq(bsc.labeled_resistance("2R2"), 2.2, "RKM 2R2 unaffected")


@test("row_kind classifies by the FIRST LETTER, not the whole alpha run")
def t_row_kind_first_letter():
    """MEASURED 2026-07-27: the old whole-run prefix dropped **87 of 673**
    all-R/C BOM rows fleet-wide while the tool printed PASS. A single
    descriptive refdes poisoned its entire row — {"C","CL"} != {"C"}.

    The two most consequential drops:
      RS1/RS2  the 10 mΩ shunts setting BOTH buck current limits
      CE1      the only electrolytic — the part that shipped REVERSED in
               cooksense v1.0/v1.1

    RED-verified: restoring `re.match(r"[A-Za-z]+", r)` makes every assertion
    below return None.
    """
    eq(bsc.row_kind(["RS1", "RS2"]), "R", "the LM5116 sense shunts")
    eq(bsc.row_kind(["CE1"]), "C", "the electrolytic that shipped reversed")
    eq(bsc.row_kind(["C_5V2", "CL1", "Cd1", "Cout_U10"]), "C",
       "descriptive capacitor refdes in one row")
    eq(bsc.row_kind(["Rs1M", "RG1", "Rf", "Rd"]), "R",
       "descriptive resistor refdes in one row")
    eq(bsc.row_kind(["R1", "C1"]), None, "a genuinely mixed row is still None")
    eq(bsc.row_kind(["U1"]), None, "a non-passive row is still None")


@test("gate FAILS the v1.2 defect: R12 = C2933210 / MPN FRC0603F3741TS (3.74k) "
      "labeled '4.12kΩ' — code identity PASSES, VALUE does not", kind="known_bad")
def t_kb_value_mismatch():
    """THE fixture the v1.2 SUPERSEDED.md describes. The BOM code EQUALS the
    source code (leg A/B are satisfied), so the pre-leg-C gate PASSED. Leg C
    parses the MPN (3.74k) against the label (4.12k) and FAILS.

    RED-VERIFY (performed 2026-07-23): with leg C removed from `check()`
    (delete the `findings.extend(value_findings(...))` line), this exact BOM
    exits 0 — legs A/B see only that C2933210 == C2933210. Restore leg C and it
    exits 1 with VALUE-MISMATCH naming 3.74kΩ vs 4.12kΩ. Confirmed at the CLI on
    a scratch fixture before this test was written."""
    d = write_case(tmpdir("bomval_"), {"R12": "C2933210"},
                   [("4.12kΩ", ["R12"], "C2933210",
                     "FRC0603F3741TS", "R_0603_1608Metric")])
    r = run([KPY, GATE, d / "bom.csv", d / "circuit.json"])
    must_fail(r, "gate on a value-mislabelled resistor", "VALUE-MISMATCH")
    contains(r.out, "3.74kΩ", "must name the MPN-encoded catalog value")
    contains(r.out, "4.12kΩ", "must name the labeled value")


@test("gate PASSES the corrected part: MPN FRC0603F4121TS (4.12k) labeled "
      "'4.12kΩ' — encoded value matches the label")
def t_clean_value_match():
    d = write_case(tmpdir("bomval_"), {"R12": "C4121TRUE"},
                   [("4.12kΩ", ["R12"], "C4121TRUE",
                     "FRC0603F4121TS", "R_0603_1608Metric")])
    r = must_pass(run([KPY, GATE, d / "bom.csv", d / "circuit.json"]),
                  "gate on a correctly-labelled resistor")
    contains(r.out, "PASS", "verdict")


@test("gate FLAGS an R/C code resolvable by NO source — unparseable MPN and "
      "absent from the ledger (does NOT silently pass)", kind="known_bad")
def t_kb_value_unverifiable():
    """The third disposition: a value no source can verify is UNVERIFIABLE,
    not a pass. C9999999 is in no ledger and has no part.yaml; its BOM MPN
    ('...BRD07'+'4K12', a non-hyphenated reel code) is one this offline parser
    does not confidently decode — so rather than trust the label the gate
    demands the one-time catalog verify + ledger append. Better a false alarm
    than a silent 3.74k."""
    d = write_case(tmpdir("bomval_"), {"R12": "C9999999"},
                   [("4.12kΩ", ["R12"], "C9999999",
                     "RT0603BRD074K12L", "R_0603_1608Metric")])
    r = run([KPY, GATE, d / "bom.csv", d / "circuit.json"])
    must_fail(r, "gate on an unverifiable passive row", "UNVERIFIABLE-VALUE")
    contains(r.out, "RT0603BRD074K12L", "must name the MPN it could not parse")
    contains(r.out, "ledger", "must direct to the verify-once ledger append")


@test("leg C resolves the MPN from a vendored part.yaml dir name when the BOM "
      "MPN column is blank, and still catches the value mismatch", kind="known_bad")
def t_kb_value_mismatch_via_partyaml():
    """The REAL BOMs ship a blank MPN column (v1.2's did). Leg C then resolves
    LCSC -> MPN from the vendored 02_parts/<MPN>/part.yaml directory name (the
    dir IS the MPN), so the offline value check bites even without a BOM MPN
    column — no network needed."""
    d = tmpdir("bomval_")
    write_case(d, {"R12": "C2933210"},
               [("4.12kΩ", ["R12"], "C2933210", "", "R_0603_1608Metric")])
    part = d / "02_parts" / "FRC0603F3741TS"
    part.mkdir(parents=True)
    (part / "part.yaml").write_text("sourcing: {lcsc: C2933210}\n")
    r = run([KPY, GATE, d / "bom.csv", d / "circuit.json", "--parts", d / "02_parts"])
    must_fail(r, "gate resolving MPN from part.yaml dir name", "VALUE-MISMATCH")
    contains(r.out, "3.74kΩ", "catalog value decoded from the part.yaml MPN")


@test("leg C via the LEDGER catches the REAL sealed v1.2 artifact: blank MPN "
      "column, no vendored mapping — R12/C2933210 named 3.74k vs 4.12k",
      kind="known_bad")
def t_kb_real_v1_2_ledger():
    """THE acceptance fixture. The first leg-C cut resolved MPNs only from the
    BOM column or the vendored dir name; the REAL v1.2 fab BOM ships R12 as
    `4.12kΩ,R12,R_0603_1608Metric,,C2933210` — MPN BLANK — and the seal-era
    part.yaml had lcsc:null, so BOTH sources resolve nothing and R12 stayed
    SILENT on the actual artifact (measured 2026-07-23: pre-ledger gate exit 0
    without --parts; with --parts only 2 UNVERIFIABLE flags on OTHER rows).
    The vetted ledger (references/lcsc_passives_ledger.yaml) is the third
    resolution source: C2933210 -> FRC0603F3741TS / 3.74k, catalog-verified
    once — the sealed BOM now FAILS naming R12.

    RED-VERIFY (performed 2026-07-23, both baselines):
      1. pre-ledger code (git show be22bcb): this BOM exits 0 (no --parts) /
         R12-silent (--parts) — this test's assertions cannot be met;
      2. ledger lookup neutered (--ledger pointing at an empty {} yaml): R12
         degrades to UNVERIFIABLE-VALUE, no VALUE-MISMATCH — the mismatch
         assertions below fail. The in-process contrast is pinned in
         t_ledger_is_the_load_bearing_source."""
    bom = V3 / "07_releases" / "v1.2-2026-07-23" / "fab" / "bom.csv"
    cj = V3 / "03_tscircuit" / "build" / "circuit.json"
    if not bom.exists() or not cj.exists():
        return  # project trimmed from this checkout; nothing to pin
    r = run([KPY, GATE, bom, cj])
    must_fail(r, "gate on the sealed v1.2 value defect", "VALUE-MISMATCH")
    contains(r.out, "R12", "must name the defective refdes")
    contains(r.out, "C2933210", "must name the shipped code")
    contains(r.out, "3.74k", "must name the catalog value")
    contains(r.out, "4.12k", "must name the labeled value")


@test("the ledger is the LOAD-BEARING source on a blank-MPN BOM: empty ledger "
      "-> no VALUE-MISMATCH possible; vetted ledger -> the defect surfaces",
      kind="known_bad")
def t_ledger_is_the_load_bearing_source():
    """The executable RED contrast for the ledger path, on the v1.2-shaped row
    (code present, MPN blank, nothing vendored). With ledger={} the row is
    UNVERIFIABLE (flagged, not silent — the silent-skip is itself fixed); only
    the vetted ledger can turn it into the specific VALUE-MISMATCH. Neutering
    the ledger lookup in value_findings makes the second half fail."""
    rows = [bsc.BomRow(["R12"], "C2933210", "4.12kΩ", "", "R_0603_1608Metric")]
    bare = bsc.value_findings(rows, None, ledger={})
    check(bare and "UNVERIFIABLE-VALUE" in bare[0],
          f"empty-ledger baseline must FLAG (never silently skip): {bare}")
    check(not any("VALUE-MISMATCH" in f for f in bare),
          "empty ledger cannot know the catalog value — no mismatch possible")
    vetted = bsc.value_findings(rows, None)          # default vetted ledger
    check(any("VALUE-MISMATCH" in f and "3.74k" in f for f in vetted),
          f"vetted ledger must resolve C2933210 to 3.74k and mismatch: {vetted}")


@test("leg C PASSES the v1.3 corrective code C2984354 (ledger 4121 -> 4.12k "
      "== label) on a blank-MPN row")
def t_clean_v13_corrective_code():
    """The other half of the acceptance bar: the fixed board must be QUIET.
    C2984354 = AR03BTCX4121 (4.12k 0.1%), catalog-verified in the ledger; a
    blank-MPN BOM row labeled 4.12kΩ resolves through the ledger and matches."""
    d = write_case(tmpdir("bomval_"), {"R12": "C2984354"},
                   [("4.12kΩ", ["R12"], "C2984354", "", "R_0603_1608Metric")])
    r = must_pass(run([KPY, GATE, d / "bom.csv", d / "circuit.json"]),
                  "gate on the ledger-vetted corrective part")
    contains(r.out, "PASS", "verdict")


@test("leg C ignores non-passive and uncoded rows (no false positives)")
def t_clean_value_scope():
    """A connector row (J*, MPN is a part name, not an encoded value) and an
    uncoded hand-solder row must not be value-checked — leg C is scoped to R/C
    designators with a resolvable MPN."""
    d = write_case(tmpdir("bomval_"), {"U1": "C192421", "J1": ""},
                   [("USBLC6-2SC6", ["U1"], "C192421", "USBLC6-2SC6", "SOT-23-6"),
                    ("USB-C", ["J1"], "", "", "USB_C_Receptacle")])
    must_pass(run([KPY, GATE, d / "bom.csv", d / "circuit.json"]),
              "gate must not value-check non-passive / uncoded rows")


# ---------------------------------------------------- exporter round-trip (fix)
@test("exporter groups by SOURCE code: two distinct-code caps export as TWO "
      "rows (round-trip on the real board)", slow=True)
def t_exporter_splits_distinct_codes():
    """The fix. Regenerate the usb-hub-3s-v3 BOM from the sealed board + source
    circuit.json and assert C77102 and C77100 land on SEPARATE C_1210 rows and
    the 100uF row uses the source code C84455 — not the substituted C90143.

    RED-VERIFY (manual, recorded here): swap the grouping key back to
    `groups.setdefault((val, fpname), ...)` with the value-token carry-over and
    the two codes re-merge onto one row and 100uF reverts to the carried code —
    exactly the v1.1 corruption. Restore to re-split."""
    board = V3 / "04_kicad" / "usb_hub_3s_v2.kicad_pcb"
    cj = V3 / "03_tscircuit" / "build" / "circuit.json"
    if not board.exists() or not cj.exists():
        return
    d = tmpdir("bomexp_")
    must_pass(run([KPY, EXPORT, board, d, "--layers", "4", "--lcsc-source", cj]),
              "export_jlc_package with a source circuit.json")
    rows = list(csv.DictReader(open(d / "bom.csv")))
    by_code = {r["LCSC"]: r for r in rows}
    check("C77102" in by_code and "C77100" in by_code,
          f"10uF caps did not split into distinct code rows: {sorted(by_code)}")
    # the 50V code and 25V code must be on DIFFERENT rows, never merged
    eq(set(by_code["C77102"]["Designator"].split(",")) &
       set(by_code["C77100"]["Designator"].split(",")), set(),
       "50V and 25V cap rows share a designator (merged)")
    eq(by_code["C84455"]["Comment"].split()[0], "100uF", "100uF row source code")
    check("C90143" not in by_code, "the substituted 16V code must NOT appear")
    check(all(r["LCSC"] for r in rows), "every exported line must carry an LCSC")


@test("exporter drops FP_EXCLUDE_FROM_POS_FILES parts from the CPL but keeps "
      "them in the BOM (hand-solder); a populated part is in BOTH; a non-C "
      "supplier handle is BLANK in the BOM LCSC and the carry-over cannot "
      "resurrect it", slow=True)
def t_exporter_exclude_from_pos_cpl():
    """The exclude_from_pos fix (2026-07-23) + the non-C LCSC-blank fix (fix pass).
    crow-mic-pod-v2 marks MK1 (electret, hand-solder) and J1 (RJHSE-5384 consign,
    hand-solder) exclude_from_pos: ABSENT from cpl.csv yet PRESENT in
    bom.csv. D3 (SMAJ6.0A) is POPULATED (ADR-0001 D5, the P0-D fix) — it must
    be in BOTH the BOM and the CPL, like U1. MK1's supplier handle is an MPN
    ("AOM-5024L-HD-R"), NOT an LCSC — its BOM LCSC column must be BLANK, and a
    stale prior BOM must not resurrect it into the LCSC column on re-export.

    RED-VERIFY (performed 2026-07-23): (1) neuter the
    `if fp.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_POS_FILES: continue` and
    MK1/J1 wrongly REAPPEAR in the CPL. (2) drop the `re.fullmatch(r"C\\d+", code)`
    guard in export_jlc_package's carry-over (and/or in refdes_codes_from_circuit)
    and the injected MK1="AOM-5024L-HD-R" survives into the re-exported BOM LCSC
    column. Restore to re-fix."""
    board = POD / "04_kicad" / "crow_mic_pod_v2.kicad_pcb"
    cj = POD / "03_tscircuit" / "build" / "circuit.json"
    if not board.exists() or not cj.exists():
        return  # project trimmed from this checkout; nothing to pin
    d = tmpdir("cplexcl_")
    must_pass(run([KPY, EXPORT, board, d, "--layers", "2", "--lcsc-source", cj]),
              "export_jlc_package (pod-v2)")
    cpl_refs = {row["Designator"]
                for row in csv.DictReader(open(d / "cpl.csv"))}
    bom_by_ref = {}
    for row in csv.DictReader(open(d / "bom.csv")):
        for x in row["Designator"].split(","):
            bom_by_ref[x.strip()] = row
    for r in ("MK1", "J1"):
        check(r not in cpl_refs,
              f"{r} is exclude_from_pos but appears in the CPL: {sorted(cpl_refs)}")
        check(r in bom_by_ref, f"{r} must stay in the BOM (documented part)")
    check("D3" in cpl_refs and "D3" in bom_by_ref,
          "populated D3 (P0-D fix) must appear in BOTH the CPL and the BOM")
    check("U1" in cpl_refs and "U1" in bom_by_ref,
          "a normal SMT part (U1) must appear in BOTH the CPL and the BOM")
    # MK1's supplier handle is an MPN, not an LCSC -> BOM LCSC column blank
    eq(bom_by_ref["MK1"]["LCSC"].strip(), "",
       "MK1 hand-solder line must have a BLANK LCSC (an MPN is not an LCSC)")
    # inject a STALE prior BOM carrying MK1's MPN in the LCSC column, re-export,
    # and assert the carry-over guard refuses to resurrect it (the export fix).
    rows = list(csv.DictReader(open(d / "bom.csv")))
    with open(d / "bom.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        for row in rows:
            if "MK1" in [x.strip() for x in row["Designator"].split(",")]:
                row["LCSC"] = "AOM-5024L-HD-R"
            w.writerow(row)
    must_pass(run([KPY, EXPORT, board, d, "--layers", "2", "--lcsc-source", cj]),
              "re-export over a stale BOM (carry-over path)")
    bom2 = {x.strip(): row for row in csv.DictReader(open(d / "bom.csv"))
            for x in row["Designator"].split(",")}
    eq(bom2["MK1"]["LCSC"].strip(), "",
       "carry-over must NOT resurrect MK1's MPN into the LCSC column")


# --------------------------------------------------- --circuit-only (leg C at
# authoring, 2026-07-23). The R12/R30 wrong-value class was AUTHORED in the tsx
# (a supplierPartNumbers code whose catalog value never matched the declared
# resistance) and first caught after seal #3 because leg C only ran once a fab
# BOM existed. --circuit-only runs the decoded-value-vs-value-prop comparison
# straight off circuit.json the moment the tsx builds.
#
# RED-VERIFIED against pre-fix code (git show 747f9d2:.../bom_source_check.py
# swapped in, 2026-07-23): all four tests below FAIL against it — the old CLI
# rejects --circuit-only with "unrecognized arguments" (exit 2, so the clean
# tests' must_pass fails and the known-bad tests' expected finding strings
# never appear). Restored the fixed file afterwards.

def circuit_rc(components):
    """circuit.json text from [(refdes, lcsc, prop_field, value), ...]."""
    els = []
    for ref, code, field, val in components:
        e = {"type": "source_component", "name": ref,
             "supplier_part_numbers": {"jlcpcb": [code] if code else []}}
        if field:
            e[field] = val
        els.append(e)
    return json.dumps(els)


def ledger_yaml(d, entries):
    p = d / "ledger.yaml"
    p.write_text("".join(
        f"{code}:\n  mpn: {mpn}\n  verified: 2026-07-23\n"
        for code, mpn in entries.items()) or "{}\n")
    return p


@test("--circuit-only PASSES coded R/C whose catalog values match their props")
def t_conly_clean():
    d = tmpdir("bomconly_")
    (d / "circuit.json").write_text(circuit_rc([
        ("R12", "C100", "resistance", 4120),        # FRC0603F4121TS = 4.12k
        ("C1", "C200", "capacitance", 100e-9),      # ...104K... = 100nF
        ("R99", "", "resistance", 100000),          # uncoded: out of scope
        ("U1", "C300", "", None)]))                 # not an R/C row
    led = ledger_yaml(d, {"C100": "FRC0603F4121TS", "C200": "CL10B104KB8NNNC"})
    r = must_pass(run([KPY, GATE, "--circuit-only", d / "circuit.json",
                       "--ledger", led]), "--circuit-only on matching values")
    contains(r.out, "CIRCUIT VALUE CHECK: PASS", "verdict")


@test("--circuit-only FAILS a coded R whose decoded catalog value mismatches "
      "its resistance prop (the R12/R30 class)", kind="known_bad")
def t_conly_value_mismatch():
    """The known-bad fixture the mission names: the clean case broken in ONE
    way — R30 declares 100k but its LCSC code resolves (via the ledger MPN)
    to 3.09k, the REAL v1.2 R30 defect (commit 688a8af). Must FAIL at the
    circuit.json stage, no BOM anywhere."""
    d = tmpdir("bomconly_")
    (d / "circuit.json").write_text(circuit_rc([
        ("R30", "C2933195", "resistance", 100000)]))
    led = ledger_yaml(d, {"C2933195": "FRC0603F3091TS"})   # 3.09k
    r = must_fail(run([KPY, GATE, "--circuit-only", d / "circuit.json",
                       "--ledger", led]),
                  "--circuit-only on the R30 wrong-value class",
                  "VALUE-MISMATCH")
    contains(r.out, "R30", "the finding names the refdes")


@test("--circuit-only FAILS a coded R that NO source can resolve "
      "(unverifiable is not a pass)", kind="known_bad")
def t_conly_unverifiable():
    d = tmpdir("bomconly_")
    (d / "circuit.json").write_text(circuit_rc([
        ("R5", "C999999", "resistance", 4700)]))
    must_fail(run([KPY, GATE, "--circuit-only", d / "circuit.json",
                   "--ledger", d / "no_such_ledger.yaml"]),
              "--circuit-only on an unvetted code", "UNVERIFIABLE-VALUE")


@test("--circuit-only resolves via a 02_parts part.yaml MPN dir when the "
      "ledger is silent")
def t_conly_partyaml_source():
    d = tmpdir("bomconly_")
    (d / "circuit.json").write_text(circuit_rc([
        ("R7", "C123456", "resistance", 2.2)]))            # 2R2
    pd = d / "02_parts" / "RC0603FR-072R2L"
    pd.mkdir(parents=True)
    (pd / "part.yaml").write_text(
        "mpn: RC0603FR-072R2L\nsourcing:\n  lcsc: C123456\n")
    must_pass(run([KPY, GATE, "--circuit-only", d / "circuit.json",
                   "--parts", d / "02_parts",
                   "--ledger", d / "no_such_ledger.yaml"]),
              "--circuit-only via part.yaml MPN")


@test("an explicit exact-code ledger value outranks a misleading numeric MPN "
      "heuristic in both authoring and fab checks", kind="known_bad")
def t_explicit_ledger_value_precedes_mpn_heuristic():
    """USB Hub v4 C23 exposed this ordering bug: Panasonic 16SVPF180M is
    exactly 180 uF, but the generic MPN decoder can read the embedded ``180M``
    family token as 18 pF. The catalog-verified LCSC ledger row is direct
    evidence and must therefore win over both BOM and part-directory guesses.
    """
    ledger = {"C136277": {
        "mpn": "16SVPF180M", "value": "180uF", "verified": "2026-08-12"}}
    vendored = {"C136277": "16SVPF180M"}
    rows = [bsc.BomRow(["C23"], "C136277", "180uF", "16SVPF180M",
                       "CP_Elec_6.3x5.8")]
    eq(bsc.value_findings(rows, vendored=vendored, ledger=ledger), [],
       "fab row trusts the explicit catalog value")

    d = tmpdir("bomconly_precedence_")
    cj = d / "circuit.json"
    cj.write_text(circuit_rc([
        ("C23", "C136277", "capacitance", 180e-6)]))
    eq(bsc.circuit_value_findings(cj, vendored=vendored, ledger=ledger), [],
       "authoring row trusts the explicit catalog value")

    heuristic_only = bsc.circuit_value_findings(
        cj, vendored=vendored, ledger={})
    check(any("UNVERIFIABLE-VALUE" in finding for finding in heuristic_only),
          "without the catalog fact this non-ceramic family must stay "
          "unverifiable, never be guessed from a ceramic-value heuristic")


@test("legacy two-positional CLI is unchanged by the --circuit-only addition")
def t_conly_backward_compat():
    d = write_case(tmpdir("bomsrc_"), SRC, [
        ("10uF 50V", ["C9", "C10"], "C77102"),
        ("10uF 25V", ["C49", "C50"], "C77100")])
    must_pass(run([KPY, GATE, d / "bom.csv", d / "circuit.json"]),
              "legacy invocation still passes a correct BOM")
    # and omitting circuit_json without --circuit-only is still an error
    r = run([KPY, GATE, d / "bom.csv"])
    check(r.rc != 0, "bom-only invocation without --circuit-only must error")


@test("mpn_capacitance decodes the FH/Fenghua VOLTAGE-SUFFIX ceramics the "
      "ledger was working around by hand", kind="known_bad")
def t_legc_voltage_suffix_ceramics():
    """THE DEFECT (2026-07-28). The decoder anchored on `<3-digit code><tol>`
    with a `(?![0-9])` lookahead "to avoid grabbing a voltage/series
    digit-run". That lookahead also refused every MPN that puts the VOLTAGE
    CODE straight after the tolerance letter — which is FH/Fenghua's entire
    ceramic range: `0402CG101J500NT` is 0402, C0G, code 101, tolerance J,
    **500 = 50 V**, NT reel. The digit it was rejecting is the `5` of the
    voltage.

    The vetted ledger already carried three explicit `value:` entries for this
    family, which is a workaround recording a PARSER BUG as if it were a part
    fact — and the ledger is the load-bearing offline source, so a parser hole
    hidden there is a hole in leg C for every future board that stocks the
    same series without someone hand-writing a row.

    MEASURED across all 146 vetted ledger rows, whose `value:` fields are
    catalog-verified and are an INDEPENDENT authority (canon M1): 6 MPNs newly
    parsed, all 6 agreeing with their declared value, 0 regressions and 0
    disagreements.

    RED-VERIFIED 2026-07-28 (git-swap, tests/README step 3): with git HEAD's
    bom_source_check.py swapped back in this fails on `FH C0G 101J500 ->
    100pF: got None, want 1e-10` — the family returned None, i.e. the gate
    FLAGGED it as unverifiable rather than checking it.
    """
    for mpn, want in (("0402CG101J500NT", 100e-12),    # C1546, ledger 100pF
                      ("0402CG180J500NT", 18e-12),     # C1549, ledger 18pF
                      ("0402CG120J500NT", 12e-12),     # C1547, ledger 12pF
                      ("0402B102K500NT", 1e-9),        # C1523, ledger 1nF
                      ("0402B472K500NT", 4.7e-9),      # C1538, ledger 4.7nF
                      ("0603B103K500NT", 10e-9)):      # C57112, ledger 10nF
        got = bsc.mpn_capacitance(mpn, "")
        check(got is not None and abs(got - want) < want * 1e-9,
              f"FH ceramic {mpn} -> {want*1e12:g}pF: got {got!r}, want {want}")
    # ...and the guarantee the lookahead was there for still holds: a bare
    # digit-run must NEVER be read as a value.
    eq(bsc.mpn_capacitance("MYSTERY-PART-1234567", ""), None,
       "a bare digit-run is still not a capacitance")
    eq(bsc.mpn_capacitance("0402CG101J5001NT", ""), None,
       "a FOUR-digit run after the tolerance letter is not a voltage code, "
       "and must not be read as one")
    # the classic tolerance-terminated form is untouched
    check(abs(bsc.mpn_capacitance("GRM188R71H104KA01", "C_0603_1608Metric")
              - 1e-7) < 1e-12, "104K -> 100nF still decodes")


@test("every vetted ledger row the MPN decoder CAN read agrees with the "
      "catalog value recorded beside it")
def t_legc_ledger_cross_check():
    """Canon M1 in its cleanest form available here: the ledger's `value:`
    strings were verified once against the JLC catalog — a different authority
    from the MPN grammar — so every row is a free test of the decoder. Any
    disagreement is either a parser bug or a mis-recorded ledger row, and both
    are worth a red build.

    Measured 2026-07-28: 146 rows, 0 disagreements.
    """
    led = bsc.load_ledger()
    check(len(led) > 100, f"the ledger did not load: {len(led)} rows")
    checked, bad = 0, []
    for code, e in led.items():
        mpn, val = e.get("mpn", ""), e.get("value", "")
        for parse, label in ((bsc.mpn_capacitance, bsc.labeled_capacitance),
                             (bsc.mpn_resistance, bsc.labeled_resistance)):
            got, want = parse(mpn, ""), label(val)
            if got is None or want is None:
                continue
            checked += 1
            if abs(got - want) > abs(want) * 0.001:
                bad.append(f"{code} {mpn}: decoded {got!r}, ledger says "
                           f"{val!r} ({want!r})")
    check(not bad, f"MPN decode disagrees with the vetted catalog value on "
                   f"{len(bad)}/{checked} rows: {bad[:6]}")
    check(checked >= 60, f"only {checked} ledger rows were decodable at all — "
                         f"this cross-check has lost its denominator")


if __name__ == "__main__":
    sys.exit(main())
