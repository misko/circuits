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


def circuit(codes):
    """A minimal circuit.json: {refdes: lcsc} -> source_component list."""
    return [{"type": "source_component", "name": r,
             "supplier_part_numbers": {"jlcpcb": [c]} if c else {}}
            for r, c in codes.items()]


def write_case(d, refdes_codes, bom_rows):
    """circuit.json + a fab bom.csv in dir d. bom_rows: [(comment, [refs], code)]."""
    (d / "circuit.json").write_text(json.dumps(circuit(refdes_codes)))
    with open(d / "bom.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "MPN", "LCSC"])
        for comment, refs, code in bom_rows:
            w.writerow([comment, ",".join(refs), "C_1210_3225Metric", "", code])
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
    rows = list(csv.DictReader(open(d / "bom_jlc.csv")))
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


if __name__ == "__main__":
    sys.exit(main())
