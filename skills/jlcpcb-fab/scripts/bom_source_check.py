#!/usr/bin/env python3
"""BOM-vs-source consistency gate: the fab BOM's per-refdes LCSC code MUST
equal the SOURCE's per-refdes LCSC code. Nothing else is a legitimate BOM.

    bom_source_check.py FAB_BOM.csv CIRCUIT_JSON [--parts 02_parts_DIR]

Why this exists (the defect it would have blocked)
--------------------------------------------------
usb-hub-3s-v3 v1.1 shipped a corrupt orderable BOM. The board carries only a
Value string per footprint ("10uF"), never the LCSC code; the exporter grouped
footprints by (value, footprint) and re-attached a code by value-token lookup.
So two DISTINCT parts that share a value+footprint collapsed onto one row:

  source: C9-C12,C24-C27 = C77102 (10uF *50V*)   C49,C50 = C77100 (10uF *25V*)
  shipped BOM: all ten on ONE row coded C77100 (25V) — 50V input caps became
               25V caps on the input rail.

and the output cap was SUBSTITUTED: source C84455 (10V) -> BOM C90143 (16V).

A merged row, a substituted code, or a blank code where the source has one are
all silent BOM corruption. This gate is the machine backstop.

The source of truth (canon M6: authoritative source, not a downstream copy)
---------------------------------------------------------------------------
`circuit.json` `source_component.supplier_part_numbers.jlcpcb[0]`, keyed by
refdes (the component `name`). This is emitted from the tscircuit source
(`supplierPartNumbers`) — the SAME declaration a human reads in the .tsx — and
is per-refdes, so it can represent two different codes on one value+footprint
that the KiCad board physically cannot.

Two INDEPENDENT legs (canon M1: checker and checked must not share a method):
  A. per-refdes, vs circuit.json  — catches MERGED / SUBSTITUTED / MISSING.
     Authoritative and independent of HOW the BOM was produced (the v1.1
     corruption happened in a value-token carry-over downstream of the source).
  B. per-vendored-code, vs 02_parts/*/part.yaml (optional) — the OTHER
     direction, from a hand-maintained source that never reads circuit.json:
     every part we deliberately VENDORED (has a part.yaml) AND that the build
     actually uses must appear on the BOM under its vetted `sourcing.lcsc`. A
     substituted or dropped code makes its vetted code ABSENT from the BOM
     (C84455 was vendored; the v1.1 BOM shipped C90143 and C84455 is nowhere).
     Iterates the ~dozens of vendored parts, NOT every BOM row, so a passive
     coded from JLC's basic library with no part.yaml is never a false positive.

Leg C — SEMANTIC value consistency (usb-hub-3s-v3 v1.2, 2026-07-23)
------------------------------------------------------------------
Legs A/B check CODE IDENTITY only (BOM code == source code). They are BLIND to
what the LCSC code actually IS in the catalog. v1.2 shipped R12 = C2933210 (MPN
FRC0603F3741TS = 3.74 kOhm) while the row LABEL said "4.12kOhm" — driving the
buck-C setpoint to ~4.97 V undervoltage. Code identity PASSED; the value was
wrong. This gate now also compares the MPN-ENCODED value to the LABELED value.

Resistor/cap MPNs encode value as EIA 3-sig-fig + multiplier (FRC0603F3741TS ->
"3741" -> 374 x 10^1 = 3.74 kOhm; a real 4.12k encodes "4121" -> 412 x 10^1 =
4120) or as RKM notation ("4K12" = 4.12k, "2R2" = 2.2Ohm). We resolve every
R/C row's MPN (from the BOM MPN column, else the vendored part.yaml directory
name = the MPN), parse its encoded value OFFLINE, and FAIL on a mismatch. An MPN
we cannot parse is FLAGGED for manual review — an unverifiable value is NOT a
pass. This leg needs no network; a catalog fetch, if present, is a bonus not a
dependency.

Exit 1 on any finding; the exit code IS the gate.
"""
import argparse
import csv
import glob
import json
import re
import sys
from collections import namedtuple
from pathlib import Path


def refdes_codes_from_circuit(circuit_json):
    """{refdes: lcsc} from circuit.json source_component entries. A component
    with no jlcpcb supplier code maps to '' (present, but uncoded)."""
    data = json.loads(Path(circuit_json).read_text())
    if isinstance(data, dict):                       # some builds wrap in {..}
        data = data.get("elements") or data.get("soup") or []
    out = {}
    for e in data:
        if not isinstance(e, dict) or e.get("type") != "source_component":
            continue
        name = e.get("name")
        if not name:
            continue
        spn = e.get("supplier_part_numbers") or e.get("supplierPartNumbers") or {}
        jlc = spn.get("jlcpcb") if isinstance(spn, dict) else None
        code = (jlc[0] if isinstance(jlc, list) and jlc else (jlc or "")) or ""
        # An LCSC code is C-prefixed digits (e.g. C559105). A supplier_part_numbers
        # .jlcpcb value that is an MPN — a hand-solder part's FPID-RESOLUTION HANDLE,
        # e.g. AOM-5024L-HD-R, used by the converter to map to its 02_parts footprint
        # for a part JLC does not stock — is NOT an LCSC code. Treat it as uncoded so
        # it never lands in the BOM's LCSC column (the export imports this same fn),
        # and so this gate never false-fails a MISSING-code on a hand-solder line
        # (crow-mic-pod-v2 MK1, render-review finding I, 2026-07-23).
        out[name] = code if re.fullmatch(r"C\d+", code) else ""
    return out


def vendored_primary_codes(parts_dir):
    """{lcsc: MPN} for each 02_parts/<MPN>/part.yaml PRIMARY sourcing.lcsc.
    Alternates are fallbacks, not a promise to order them, so they are NOT
    required to be present. Returns None if the dir/yaml is unavailable."""
    parts_dir = Path(parts_dir)
    if not parts_dir.is_dir():
        return None
    try:
        import yaml
    except ImportError:
        return None
    codes = {}
    for y in sorted(parts_dir.glob("*/part.yaml")):
        try:
            src = (yaml.safe_load(y.read_text()) or {}).get("sourcing") or {}
        except Exception:
            continue
        lcsc = str(src.get("lcsc") or "").strip()
        if lcsc and "TBD" not in lcsc:
            codes.setdefault(lcsc, y.parent.name)
    return codes or None


# A BOM row carries five load-bearing fields. Kept as a namedtuple so the first
# three (refs, lcsc, comment — everything legs A/B ever needed) still unpack the
# old way, while leg C can reach .mpn and .footprint.
BomRow = namedtuple("BomRow", "refs lcsc comment mpn footprint")


def read_bom(bom_path):
    """[BomRow(refs, lcsc, comment, mpn, footprint)] from a fab BOM. Tolerates
    both the Comment,Designator,Footprint,MPN,LCSC and the older
    Comment,Designator,Footprint,LCSC headers (MPN absent -> '')."""
    rows = []
    with open(bom_path, newline="") as f:
        for r in csv.DictReader(f):
            desig = r.get("Designator") or r.get("Designators") or ""
            refs = [d.strip() for d in desig.split(",") if d.strip()]
            rows.append(BomRow(
                refs, (r.get("LCSC") or "").strip(),
                (r.get("Comment") or "").strip(),
                (r.get("MPN") or r.get("Manufacturer Part Number") or "").strip(),
                (r.get("Footprint") or r.get("Package") or "").strip()))
    return rows


# ------------------------------------------------------------ semantic value
_PKG = ("0201", "0402", "0603", "0805", "1206", "1210", "1812",
        "2010", "2512", "2920")
_MULT = {"R": 1.0, "K": 1e3, "M": 1e6}          # RKM decimal-point-as-multiplier
_CAP_UNIT = {"P": 1e-12, "N": 1e-9, "U": 1e-6, "µ": 1e-6, "M": 1e-3}


def row_kind(refs):
    """'R' if every designator is a resistor, 'C' if every one a capacitor,
    else None (mixed / non-passive rows are out of scope for value parsing)."""
    prefixes = {m.group(0).upper() for r in refs
                if (m := re.match(r"[A-Za-z]+", r))}
    if prefixes == {"R"}:
        return "R"
    if prefixes == {"C"}:
        return "C"
    return None


def labeled_resistance(text):
    """Ohms from a resistor LABEL token ('4.12kΩ', '100k', '4k7', '2R2', '0Ω').
    None if it does not read as a resistance."""
    s = re.split(r"[\s/]", text.strip())[0]
    s = s.replace("Ω", "").replace("Ω", "").replace("ohm", "", 1)
    s = re.sub(r"(?i)ohm", "", s).strip()
    if not s:
        return None
    m = re.fullmatch(r"(\d*)([RKM])(\d*)", s, re.I)          # RKM: 4k7, 2R2, R47
    if m and (m.group(1) or m.group(3)):
        return float(f"{m.group(1) or '0'}.{m.group(3) or '0'}") * _MULT[m.group(2).upper()]
    m = re.fullmatch(r"(\d+(?:\.\d+)?)([RKM]?)", s, re.I)    # 4.12k, 100k, 470
    if m:
        return float(m.group(1)) * (_MULT[m.group(2).upper()] if m.group(2) else 1.0)
    return None


def labeled_capacitance(text):
    """Farads from a capacitor LABEL token ('100nF', '10uF', '4u7', '2.2uF')."""
    s = re.split(r"[\s/]", text.strip())[0]
    m = re.fullmatch(r"(\d*)([PNUµM])(\d*)F?", s, re.I)      # RKM: 4u7, 100n
    if m and (m.group(1) or m.group(3)):
        return float(f"{m.group(1) or '0'}.{m.group(3) or '0'}") * _CAP_UNIT[m.group(2).upper()]
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*([PNUµM])F?", s, re.I)   # 100nF, 10uF
    if m:
        return float(m.group(1)) * _CAP_UNIT[m.group(2).upper()]
    return None


def _strip_package(mpn, footprint=""):
    """Remove the (imperial) package token so its digits are not mistaken for a
    value code. Prefer the package the footprint declares; else the first known
    token found in the MPN."""
    s = mpn.upper()
    pk = ""
    fm = re.search(r"(0201|0402|0603|0805|1206|1210|1812|2010|2512|2920)",
                   (footprint or "").upper())
    if fm and fm.group(1) in s:
        pk = fm.group(1)
    else:
        for p in _PKG:
            if p in s:
                pk = p
                break
    if pk:
        s = s.replace(pk, "|", 1)
    return s


def mpn_resistance(mpn, footprint=""):
    """Ohms encoded in a resistor MPN, or None if it cannot be parsed CONFIDENTLY
    (zero candidates, or two candidates that disagree). Handles the two dominant
    encodings: RKM ('4K12'=4.12k, '2R2'=2.2) and 4-digit EIA (3 sig + multiplier,
    '3741'=374e1=3.74k, '4121'=412e1=4120)."""
    s = _strip_package(mpn, footprint)
    s = re.sub(r"-\d{2}(?=\d)", "-", s)         # drop Yageo reel code: -074K12 -> -4K12
    cands = set()
    # RKM: <digits><R|K|M><digits>, at least one side present, not glued to more digits
    for m in re.finditer(r"(?<![A-Z0-9])(\d{0,3})([RKM])(\d{0,3})(?![0-9])", s):
        left, letter, right = m.group(1), m.group(2), m.group(3)
        if not (left or right):
            continue
        cands.add(round(float(f"{left or '0'}.{right or '0'}") * _MULT[letter], 6))
    # 4-digit EIA: 3 significant figures (first nonzero) + 1 multiplier digit
    for m in re.finditer(r"(?<![0-9])([1-9]\d{2})(\d)(?![0-9])", s):
        cands.add(round(int(m.group(1)) * (10 ** int(m.group(2))), 6))
    return next(iter(cands)) if len(cands) == 1 else None


def mpn_capacitance(mpn, footprint=""):
    """Farads encoded in a ceramic-cap MPN, or None if not confidently parseable.
    Anchors on the standard 3-digit code IMMEDIATELY followed by a tolerance
    letter ('104K'=10e4 pF=100nF, '475M'=47e5 pF=4.7uF) to avoid grabbing a
    voltage/series digit-run."""
    s = _strip_package(mpn, footprint)
    cands = set()
    for m in re.finditer(r"(?<![0-9])(\d{2})([0-8])[JKMDFGZ](?![0-9])", s):
        cands.add(round(int(m.group(1)) * (10 ** int(m.group(2))) * 1e-12, 15))
    return next(iter(cands)) if len(cands) == 1 else None


def value_findings(bom_rows, vendored=None):
    """Leg C: MPN-encoded value vs LABELED value for every R/C row.

    MPN is resolved from the BOM's own MPN column, else the vendored part.yaml
    directory name (== the MPN). A confidently-parsed value that disagrees with
    the label is a VALUE-MISMATCH (the v1.2 defect). An MPN we cannot parse is
    UNVERIFIABLE-VALUE — flagged for review, never a silent pass. A row with no
    resolvable MPN is left to legs A/B (nothing to parse)."""
    lcsc_to_mpn = {c: m for c, m in (vendored or {}).items()}
    out = []
    for row in bom_rows:
        refs = row.refs if isinstance(row, BomRow) else row[0]
        lcsc = row.lcsc if isinstance(row, BomRow) else row[1]
        comment = row.comment if isinstance(row, BomRow) else row[2]
        mpn = (row.mpn if isinstance(row, BomRow) else "") or lcsc_to_mpn.get(lcsc, "")
        footprint = row.footprint if isinstance(row, BomRow) else ""
        kind = row_kind(refs)
        if not kind or not mpn:
            continue
        tag = comment or (",".join(refs[:3]) + ("…" if len(refs) > 3 else ""))
        if kind == "R":
            labeled, derived, unit = labeled_resistance(comment), mpn_resistance(mpn, footprint), "Ω"
        else:
            labeled, derived, unit = labeled_capacitance(comment), mpn_capacitance(mpn, footprint), "F"
        if labeled is None:
            continue                    # label is not a passive value (jumper text etc.)
        if labeled == 0:
            continue                    # 0Ω jumper — no meaningful value to encode
        if derived is None:
            out.append(
                f"UNVERIFIABLE-VALUE on row '{tag}' ({lcsc or 'no LCSC'}): MPN "
                f"'{mpn}' cannot be parsed for its encoded value — labeled "
                f"{_fmt(labeled, unit)}; resolve the catalog value MANUALLY "
                f"(an unverifiable value is not a pass)")
            continue
        # exact E96/EIA codes should match the label to well within 1% (rounding);
        # the v1.2 defect was a 9% error. A relative gap over 1.5% is a mismatch.
        if abs(derived - labeled) / labeled > 0.015:
            out.append(
                f"VALUE-MISMATCH on row '{tag}' ({lcsc or 'no LCSC'}): MPN "
                f"'{mpn}' encodes {_fmt(derived, unit)} but the label says "
                f"{_fmt(labeled, unit)} — the ordered part is NOT the labeled "
                f"value")
    return out


def _fmt(v, unit):
    if unit == "Ω":
        for scale, suf in ((1e6, "M"), (1e3, "k"), (1, "")):
            if v >= scale:
                return f"{v / scale:g}{suf}Ω"
        return f"{v:g}Ω"
    for scale, suf in ((1e-6, "µF"), (1e-9, "nF"), (1e-12, "pF")):
        if v >= scale:
            return f"{v / scale:g}{suf}"
    return f"{v:g}F"


def check(bom_rows, refdes_code, vendored=None):
    """Returns a list of finding strings; empty == PASS.

    refdes_code: {refdes: source_lcsc} (authoritative, per-refdes).
    vendored:    {lcsc: MPN} of vendored primary codes, or None to skip legs B/C.

    Leg A (per-refdes vs circuit.json) and leg B (per-vendored-code vs part.yaml)
    check CODE IDENTITY; leg C (MPN-encoded value vs label) checks the catalog
    VALUE the code resolves to."""
    findings = []
    bom_codes = {row[1] for row in bom_rows if row[1]}
    source_codes = {c for c in refdes_code.values() if c}

    # ---- leg A: per-refdes vs the source of truth (circuit.json) ----
    for row in bom_rows:
        refs, bom_lcsc, comment = row[0], row[1], row[2]
        src = {r: refdes_code[r] for r in refs
               if r in refdes_code and refdes_code[r]}
        distinct = set(src.values())
        tag = comment or (",".join(refs[:3]) + ("…" if len(refs) > 3 else ""))
        if len(distinct) > 1:
            detail = ", ".join(f"{r}->{c}" for r, c in sorted(src.items()))
            findings.append(
                f"MERGED row '{tag}' (LCSC {bom_lcsc or 'blank'}): its "
                f"designators have DIFFERENT source codes and must be "
                f"SEPARATE rows — {detail}")
        elif len(distinct) == 1:
            s = next(iter(distinct))
            if not bom_lcsc:
                findings.append(
                    f"MISSING code on row '{tag}': source says {s} for "
                    f"{sorted(src)} but the BOM line has no LCSC")
            elif bom_lcsc != s:
                findings.append(
                    f"SUBSTITUTED code on row '{tag}': BOM has {bom_lcsc} but "
                    f"source says {s} for {sorted(src)}")
        # len==0: no ref on this row is coded in source (hand-solder / uncoded)
        # — nothing per-refdes to compare against.

    # ---- leg B: vendored parts vs the BOM (independent of circuit.json) ----
    # Only require codes the build ACTUALLY uses (present in the source), so a
    # part.yaml for a part not on this board is never a false positive.
    if vendored:
        for code, mpn in sorted(vendored.items()):
            if code in source_codes and code not in bom_codes:
                findings.append(
                    f"DROPPED vendored code {code} (02_parts/{mpn}): the build "
                    f"uses this vetted part but its code is NOWHERE on the BOM "
                    f"— substituted or merged away")

    # ---- leg C: MPN-encoded value vs the LABELED value (semantic, offline) ----
    findings.extend(value_findings(bom_rows, vendored))
    return findings


def resolve_circuit_json(hint):
    """Accept a circuit.json path or a project/03_tscircuit dir and find the
    build's circuit.json (build/ preferred over dist/)."""
    p = Path(hint)
    if p.is_file():
        return p
    for pat in ("build/circuit.json", "dist/**/circuit.json", "**/circuit.json"):
        hits = sorted(glob.glob(str(p / pat), recursive=True))
        if hits:
            return Path(hits[0])
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bom", help="fab BOM csv (Comment,Designator,Footprint,[MPN,]LCSC)")
    ap.add_argument("circuit_json", help="circuit.json (or a 03_tscircuit dir)")
    ap.add_argument("--parts", default="", help="02_parts dir for the per-code leg")
    args = ap.parse_args()

    cj = resolve_circuit_json(args.circuit_json)
    if not cj:
        sys.exit(f"no circuit.json found at/under {args.circuit_json}")
    refdes_code = refdes_codes_from_circuit(cj)
    vendored = vendored_primary_codes(args.parts) if args.parts else None
    findings = check(read_bom(args.bom), refdes_code, vendored)

    coded = sum(1 for v in refdes_code.values() if v)
    print(f"BOM-vs-source: {args.bom}")
    print(f"  source: {cj} ({coded} coded refdes)"
          + (f"; vendored: {len(vendored)} part.yaml codes" if vendored else ""))
    if findings:
        print(f"BOM SOURCE CHECK: FAIL ({len(findings)})")
        for f in findings:
            print("  " + f)
        sys.exit(1)
    print("BOM SOURCE CHECK: PASS (every BOM LCSC == source)")
    sys.exit(0)


if __name__ == "__main__":
    main()
