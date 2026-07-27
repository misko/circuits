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
4120) or as RKM notation ("4K12" = 4.12k, "2R2" = 2.2Ohm). Resolution order for
every R/C row: the BOM's MPN column -> the vendored part.yaml directory name
(the dir IS the MPN) -> the vetted LCSC ledger
(references/lcsc_passives_ledger.yaml, {code: {mpn, value, verified}} — the
proven-parts pattern: pay the catalog verification ONCE, ever). The first
source that yields a value wins; the comparison is OFFLINE. An R/C row with an
LCSC code that NONE of the three resolves is FLAGGED for manual review — an
unverifiable value is NOT a pass; catalog-verify the code once and append it to
the ledger, then it is quiet forever. The ledger matters because the REAL fab
BOMs ship a BLANK MPN column and basic-library passives carry no part.yaml: on
the sealed v1.2 artifact the first two sources resolve NOTHING, and without the
ledger R12 stays silent (measured 2026-07-23). This leg needs no network; a
catalog fetch, if present, is a bonus not a dependency.

--circuit-only — leg C at the AUTHORING stage (no fab BOM yet, 2026-07-23)
--------------------------------------------------------------------------
The R12/R30 class was AUTHORED in the tsx (a supplierPartNumbers code whose
catalog value never matched the declared resistance) and first caught after
seal #3, because leg C only ran once a fab BOM existed. `--circuit-only`
runs the same decoded-MPN-value-vs-label comparison DIRECTLY on circuit.json
the moment the tsx builds: for every R/C source_component that carries an
LCSC code, the code's catalog value (via 02_parts part.yaml MPN dirs, then
the vetted ledger) must match the component's own value prop (`resistance` /
`capacitance` — the number the tsx declared). No BOM, no netlist, no network.

    bom_source_check.py --circuit-only CIRCUIT_JSON [--parts 02_parts] [--ledger Y]

Same semantics as leg C: a mismatch > 1.5% is VALUE-MISMATCH; a coded R/C
that NO source resolves is UNVERIFIABLE-VALUE (an unverifiable value is not
a pass — vet the code once, append it to the ledger, quiet forever). The
NUMERIC prop is authoritative; the display string is only a fallback (display
"10mΩ" would mis-read as MΩ under RKM rules, the numeric 0.01 cannot).

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


#: leg C coverage, filled in place so `main` can print an N/M denominator.
LEGC_STATS = {}


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
#: RKM decimal-point-as-multiplier. CASE-SENSITIVE ON `m`/`M`, and that single
#: distinction is load-bearing: `labeled_resistance("10mOhm")` returned
#: 1.0e7 because the multiplier was uppercased before lookup, so MILLI decoded
#: as MEGA — a 10 mOhm current-sense shunt read as 10 MOhm, a factor of 1e9.
#: The repo's own electrical_invariants contract already states the rule
#: ("note `m` is MILLI and `M` is MEGA"); this table now obeys it.
#: The bug was invisible because `row_kind` dropped the only rows that use it
#: (RS1/RS2) — two defects cancelling, which is why neither was ever observed.
_MULT = {"R": 1.0, "r": 1.0, "K": 1e3, "k": 1e3, "M": 1e6, "m": 1e-3}
_CAP_UNIT = {"P": 1e-12, "N": 1e-9, "U": 1e-6, "µ": 1e-6, "M": 1e-3}


def row_kind(refs):
    """'R' if every designator is a resistor, 'C' if every one a capacitor,
    else None (mixed / non-passive rows are out of scope for value parsing).

    CLASSIFY BY THE FIRST LETTER, NOT THE WHOLE LEADING-ALPHA RUN. The old
    `re.match(r"[A-Za-z]+", r)` took the entire run, so a DESCRIPTIVE refdes
    poisoned its whole row: `RS1` -> "RS", `CE1` -> "CE", `Rs1M` -> "RS",
    `Cd1` -> "CD". Measured over the sealed fleet 2026-07-27: **87 of 673
    all-R/C BOM rows were dropped while the tool printed PASS**, and the two
    most consequential were

      RS1/RS2  the 10 mOhm shunts that set BOTH LM5116 buck current limits
      CE1      the board's only electrolytic — the part that shipped REVERSED
               in cooksense v1.0/v1.1

    A single ref with a multi-letter prefix was enough: a row of `C_5V2` plus
    `CL1` yields prefixes {"C","CL"} != {"C"} and the whole row exits leg C.

    SAFE ON THIS FLEET, MEASURED NOT ASSUMED: every refdes beginning R has an
    R_* footprint and every one beginning C has a C_*/CP_* footprint (CP =
    polarized; that is CE1). Nothing beginning R or C is a connector or other
    non-passive. Were such a part to appear, its value would fail to decode and
    the row would be FLAGGED — canon says an unverifiable value is not a pass —
    so it surfaces rather than silently skipping, which is the whole point.
    """
    prefixes = {r[0].upper() for r in refs if r}
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
        return float(f"{m.group(1) or '0'}.{m.group(3) or '0'}") * _MULT[m.group(2)]
    m = re.fullmatch(r"(\d+(?:\.\d+)?)([RKM]?)", s, re.I)    # 4.12k, 100k, 470
    if m:
        return float(m.group(1)) * (_MULT[m.group(2)] if m.group(2) else 1.0)
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


# The vetted LCSC->MPN/value ledger (the proven-parts pattern): each entry was
# catalog-verified ONCE; leg C then works offline forever after.
LEDGER_PATH = (Path(__file__).resolve().parent.parent
               / "references" / "lcsc_passives_ledger.yaml")


def load_ledger(path=None):
    """{lcsc: {mpn, value, verified}} from the vetted passives ledger.
    Returns {} if the file or PyYAML is unavailable (leg C then degrades to
    BOM-MPN/part.yaml resolution and FLAGS what those cannot resolve)."""
    p = Path(path) if path else LEDGER_PATH
    if not p.is_file():
        return {}
    try:
        import yaml
    except ImportError:
        return {}
    try:
        data = yaml.safe_load(p.read_text()) or {}
    except Exception:
        return {}
    return {str(k): v for k, v in data.items() if isinstance(v, dict)}


def value_findings(bom_rows, vendored=None, ledger=None, stats=None):
    """Leg C: catalog value vs LABELED value for every R/C row.

    Resolution order (first source that yields a value wins):
      1. the BOM's own MPN column                  (decode the MPN)
      2. the vendored part.yaml directory name     (the dir IS the MPN)
      3. the vetted LCSC ledger                    (explicit catalog value,
                                                    else decode its MPN)
    An R/C row with an LCSC code (or an MPN) that NO source resolves is
    UNVERIFIABLE-VALUE — flagged for review, never a silent pass; catalog-
    verify the code once and append it to the ledger. The real fab BOMs ship a
    blank MPN column and basic-library passives have no part.yaml, so on a real
    board the ledger is usually the source that bites (the sealed v1.2 R12 was
    invisible to sources 1 and 2 — measured 2026-07-23).

    ledger=None loads the default references/lcsc_passives_ledger.yaml;
    pass {} to disable (the RED baseline)."""
    if ledger is None:
        ledger = load_ledger()
    lcsc_to_mpn = {c: m for c, m in (vendored or {}).items()}
    out = []
    for row in bom_rows:
        refs = row.refs if isinstance(row, BomRow) else row[0]
        lcsc = row.lcsc if isinstance(row, BomRow) else row[1]
        comment = row.comment if isinstance(row, BomRow) else row[2]
        bom_mpn = row.mpn if isinstance(row, BomRow) else ""
        footprint = row.footprint if isinstance(row, BomRow) else ""
        kind = row_kind(refs)
        if stats is not None and refs:
            stats["rows"] = stats.get("rows", 0) + 1
        if not kind:
            if stats is not None and refs and not (
                    {r[0].upper() for r in refs} - {"R", "C"}):
                # an all-R/C row leg C still cannot classify: record it, do not
                # let it vanish. This counter existing at all is the fix for the
                # 87-of-673 silent drop measured 2026-07-27.
                stats.setdefault("unclassified", []).append(",".join(refs[:4]))
            continue
        if stats is not None:
            stats["passives"] = stats.get("passives", 0) + 1
        led = ledger.get(lcsc) if lcsc else None
        if not (bom_mpn or lcsc_to_mpn.get(lcsc) or led or lcsc):
            continue        # no code and no MPN anywhere: leg A's MISSING story
        tag = (comment or ",".join(refs[:3])) + f" [{','.join(refs[:4])}" \
              + ("…]" if len(refs) > 4 else "]")
        parse_label = labeled_resistance if kind == "R" else labeled_capacitance
        decode_mpn = mpn_resistance if kind == "R" else mpn_capacitance
        unit = "Ω" if kind == "R" else "F"
        labeled = parse_label(comment)
        if labeled is None:
            # NOT silent: a passive row whose LABEL does not read as a value was
            # never value-checked, and coverage must say so (canon M-COVER).
            if stats is not None:
                stats.setdefault("unlabeled", []).append(f"{tag} = {comment!r}")
            continue                    # label is not a passive value (part-name text)
        if labeled == 0:
            if stats is not None:
                stats["graded"] = stats.get("graded", 0) + 1
            continue                    # 0Ω jumper — no meaningful value to encode
        # --- resolve, in trust order; remember what was tried for the flag ---
        derived, via, tried = None, "", []
        for src, mpn in (("BOM MPN", bom_mpn),
                         ("part.yaml", lcsc_to_mpn.get(lcsc, ""))):
            if mpn:
                tried.append(f"{src} '{mpn}'")
                v = decode_mpn(mpn, footprint)
                if v is not None:
                    derived, via = v, f"{src} '{mpn}'"
                    break
        if derived is None and led:
            tried.append(f"ledger {lcsc}")
            v = parse_label(str(led.get("value", ""))) if led.get("value") else None
            if v is None and led.get("mpn"):
                v = decode_mpn(str(led["mpn"]), footprint)
            if v is not None:
                derived = v
                via = f"ledger {lcsc} = '{led.get('mpn', '?')}'"
        if stats is not None:
            stats["graded"] = stats.get("graded", 0) + 1
        if derived is None:
            out.append(
                f"UNVERIFIABLE-VALUE on row '{tag}' ({lcsc or 'no LCSC'}): "
                f"labeled {_fmt(labeled, unit)} but no source yields the "
                f"catalog value (tried: {'; '.join(tried) or 'nothing resolvable'}"
                f") — catalog-verify the code ONCE and append it to "
                f"{LEDGER_PATH.name} (an unverifiable value is not a pass)")
            continue
        # exact E96/EIA codes should match the label to well within 1% (rounding);
        # the v1.2 defect was a 9% error. A relative gap over 1.5% is a mismatch.
        if abs(derived - labeled) / labeled > 0.015:
            out.append(
                f"VALUE-MISMATCH on row '{tag}' ({lcsc or 'no LCSC'}): "
                f"{via} = {_fmt(derived, unit)} but the label says "
                f"{_fmt(labeled, unit)} — the ordered part is NOT the labeled "
                f"value")
    return out


def circuit_value_findings(circuit_json, vendored=None, ledger=None):
    """--circuit-only leg C: decoded catalog value vs the tsx VALUE PROP,
    straight off circuit.json — runs the moment the tsx builds, before any
    fab BOM exists (the R12/R30 class was authored here and caught 3 seals
    later when leg C first ran on a BOM).

    For every R/C source_component carrying an LCSC code
    (supplier_part_numbers.jlcpcb[0], same primary-code rule as leg A):
      labeled  = the component's own `resistance`/`capacitance` numeric prop
                 (authoritative — it IS the tsx declaration; the display
                 string is only a fallback because RKM parsing cannot tell
                 display 'mΩ' milli from 'M' mega, the numeric can)
      derived  = the code's catalog value via part.yaml MPN dir -> ledger
                 (no BOM MPN column exists at this stage)
    derived vs labeled > 1.5% -> VALUE-MISMATCH; nothing resolves the code ->
    UNVERIFIABLE-VALUE (never a silent pass). Uncoded R/C components are out
    of scope here (nothing sourced to verify).

    ledger=None loads the default vetted ledger; pass {} to disable (RED)."""
    if ledger is None:
        ledger = load_ledger()
    data = json.loads(Path(circuit_json).read_text())
    if isinstance(data, dict):
        data = data.get("elements") or data.get("soup") or []
    lcsc_to_mpn = dict(vendored or {})
    out = []
    for e in data:
        if not isinstance(e, dict) or e.get("type") != "source_component":
            continue
        name = e.get("name") or ""
        kind = row_kind([name]) if name else None
        if not kind:
            continue
        spn = e.get("supplier_part_numbers") or e.get("supplierPartNumbers") or {}
        jlc = spn.get("jlcpcb") if isinstance(spn, dict) else None
        codes = jlc if isinstance(jlc, list) else ([jlc] if jlc else [])
        lcsc = next((str(c) for c in codes
                     if re.fullmatch(r"C\d+", str(c or ""))), "")
        if not lcsc:
            continue                    # uncoded at authoring: nothing to verify
        parse_label = labeled_resistance if kind == "R" else labeled_capacitance
        decode_mpn = mpn_resistance if kind == "R" else mpn_capacitance
        unit = "Ω" if kind == "R" else "F"
        prop = e.get("resistance") if kind == "R" else e.get("capacitance")
        if isinstance(prop, (int, float)):
            labeled = float(prop)
        else:
            disp = e.get("display_resistance" if kind == "R"
                         else "display_capacitance") or ""
            labeled = parse_label(str(disp)) if disp else None
        if not labeled:                 # no declared value, or 0Ω jumper
            continue
        derived, via, tried = None, "", []
        mpn = lcsc_to_mpn.get(lcsc, "")
        if mpn:
            tried.append(f"part.yaml '{mpn}'")
            v = decode_mpn(mpn)
            if v is not None:
                derived, via = v, f"part.yaml '{mpn}'"
        led = ledger.get(lcsc)
        if derived is None and led:
            tried.append(f"ledger {lcsc}")
            v = parse_label(str(led.get("value", ""))) if led.get("value") else None
            if v is None and led.get("mpn"):
                v = decode_mpn(str(led["mpn"]))
            if v is not None:
                derived = v
                via = f"ledger {lcsc} = '{led.get('mpn', '?')}'"
        if derived is None:
            out.append(
                f"UNVERIFIABLE-VALUE on {name} ({lcsc}): tsx declares "
                f"{_fmt(labeled, unit)} but no source yields the catalog value "
                f"(tried: {'; '.join(tried) or 'nothing resolvable'}) — "
                f"catalog-verify the code ONCE and append it to "
                f"{LEDGER_PATH.name} (an unverifiable value is not a pass)")
        elif abs(derived - labeled) / labeled > 0.015:
            out.append(
                f"VALUE-MISMATCH on {name} ({lcsc}): {via} = "
                f"{_fmt(derived, unit)} but the tsx value prop says "
                f"{_fmt(labeled, unit)} — the coded part is NOT the declared "
                f"value (the R12/R30 class, caught at authoring)")
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


def check(bom_rows, refdes_code, vendored=None, ledger=None,
          not_assembled=()):
    """Returns a list of finding strings; empty == PASS.

    refdes_code:   {refdes: source_lcsc} (authoritative, per-refdes).
    vendored:      {lcsc: MPN} of vendored primary codes, or None to skip leg B.
    ledger:        {lcsc: {mpn, value, ...}}; None loads the default vetted
                   ledger, {} disables leg C's ledger source.
    not_assembled: refdes DECLARED unpopulated in 03_src/rules/assembly.yaml.
                   Their codes are EXPECTED to be absent from the assembly BOM
                   — that is the fix, not the defect (canon A-POP: a CPL row
                   whose BOM line has a blank LCSC is forbidden, so an
                   unplaced part must leave the BOM rather than sit on it
                   uncoded). Without this, leg B fires DROPPED on exactly the
                   rows a correct assembly.yaml tells you to remove, which
                   pushes the operator to put an unsourceable row back.

    Leg A (per-refdes vs circuit.json) and leg B (per-vendored-code vs part.yaml)
    check CODE IDENTITY; leg C (catalog value vs label) checks the VALUE the
    code resolves to."""
    findings = []
    bom_codes = {row[1] for row in bom_rows if row[1]}
    unpop = set(not_assembled or ())
    # a code is "expected absent" only when EVERY refdes the source assigns it
    # to is declared unpopulated — a code shared with a placed part must still
    # appear, so this can never excuse a real substitution
    excused = set()
    for code in {c for c in refdes_code.values() if c}:
        refs = {r for r, c in refdes_code.items() if c == code}
        if refs and refs <= unpop:
            excused.add(code)
    source_codes = {c for c in refdes_code.values() if c} - excused

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

    # ---- leg C: catalog value vs the LABELED value (semantic, offline) ----
    findings.extend(value_findings(bom_rows, vendored, ledger, stats=LEGC_STATS))
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


def load_not_assembled(path):
    """Refdes declared not_assembled in 03_src/rules/assembly.yaml.

    Read from the ONE declared home (canon A-POP), never re-listed here — a
    second hand-maintained copy of "who is not placed" is the drift this
    whole family of gates exists to stop."""
    try:
        import yaml
    except ImportError:
        return ()
    p = Path(path)
    if not p.is_file():
        return ()
    asm = yaml.safe_load(p.read_text()) or {}
    return {str(r) for e in (asm.get("not_assembled") or [])
            for r in (e.get("refs") or [])}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bom", help="fab BOM csv (Comment,Designator,Footprint,"
                                "[MPN,]LCSC); with --circuit-only this slot "
                                "takes the circuit.json instead")
    ap.add_argument("circuit_json", nargs="?", default="",
                    help="circuit.json (or a 03_tscircuit dir); omitted in "
                         "--circuit-only mode where the first positional is it")
    ap.add_argument("--parts", default="", help="02_parts dir for the per-code leg")
    ap.add_argument("--ledger", default="",
                    help="vetted LCSC passives ledger yaml (default: the skill's "
                         "references/lcsc_passives_ledger.yaml)")
    ap.add_argument("--assembly", default="",
                    help="03_src/rules/assembly.yaml — refdes declared "
                         "not_assembled there are EXPECTED to be off the "
                         "assembly BOM, so leg B does not report their codes "
                         "as DROPPED (canon A-POP)")
    ap.add_argument("--circuit-only", action="store_true",
                    help="AUTHORING-stage leg C: no fab BOM — decoded catalog "
                         "value vs the tsx value prop, straight off circuit.json"
                         " (the R12/R30 class, the moment the tsx builds)")
    args = ap.parse_args()

    if args.circuit_only:
        cj = resolve_circuit_json(args.circuit_json or args.bom)
        if not cj:
            sys.exit(f"no circuit.json found at/under "
                     f"{args.circuit_json or args.bom}")
        vendored = vendored_primary_codes(args.parts) if args.parts else None
        ledger = load_ledger(args.ledger) if args.ledger else load_ledger()
        findings = circuit_value_findings(cj, vendored, ledger)
        print(f"circuit-only value check: {cj}"
              + (f"; vendored: {len(vendored)} part.yaml codes" if vendored else "")
              + f"; ledger: {len(ledger)} vetted passive codes")
        if findings:
            print(f"CIRCUIT VALUE CHECK: FAIL ({len(findings)})")
            for f in findings:
                print("  " + f)
            sys.exit(1)
        print("CIRCUIT VALUE CHECK: PASS (every coded R/C catalog value == "
              "its tsx value prop)")
        sys.exit(0)

    if not args.circuit_json:
        ap.error("circuit_json is required (or pass --circuit-only)")
    cj = resolve_circuit_json(args.circuit_json)
    if not cj:
        sys.exit(f"no circuit.json found at/under {args.circuit_json}")
    refdes_code = refdes_codes_from_circuit(cj)
    vendored = vendored_primary_codes(args.parts) if args.parts else None
    ledger = load_ledger(args.ledger) if args.ledger else load_ledger()
    unpop = load_not_assembled(args.assembly) if args.assembly else ()
    findings = check(read_bom(args.bom), refdes_code, vendored, ledger, unpop)

    coded = sum(1 for v in refdes_code.values() if v)
    print(f"BOM-vs-source: {args.bom}")
    print(f"  source: {cj} ({coded} coded refdes)"
          + (f"; vendored: {len(vendored)} part.yaml codes" if vendored else "")
          + f"; ledger: {len(ledger)} vetted passive codes"
          + (f"; not_assembled: {len(unpop)} declared refdes "
             f"({', '.join(sorted(unpop)[:4])}...)" if unpop else ""))
    # canon M-COVER: leg C's denominator, so a PASS cannot hide how little it
    # graded. Measured 2026-07-27, BEFORE this line existed: row_kind dropped
    # 87 of 673 all-R/C rows fleet-wide — including RS1/RS2, the 10 mOhm shunts
    # setting BOTH buck current limits, and CE1, the only electrolytic (the part
    # that shipped REVERSED in cooksense v1.0/v1.1) — while printing PASS.
    s = LEGC_STATS
    unc, unl = s.get("unclassified", []), s.get("unlabeled", [])
    print(f"  coverage leg C: {s.get('graded', 0)}/{s.get('passives', 0)} "
          f"R/C rows value-graded ({s.get('rows', 0)} BOM rows seen)")
    for u in unc:
        print(f"  COVERAGE-GAP leg C could not classify all-R/C row: {u}")
    for u in unl:
        print(f"  COVERAGE-GAP leg C read no value from label: {u}")
    if unc:
        findings.append(
            f"LEG-C-BLIND: {len(unc)} all-R/C row(s) were not value-graded "
            f"because row_kind could not classify them — a gate that skips is "
            f"a gate that cannot fail on the property it names")

    if findings:
        print(f"BOM SOURCE CHECK: FAIL ({len(findings)})")
        for f in findings:
            print("  " + f)
        sys.exit(1)
    print("BOM SOURCE CHECK: PASS (every BOM LCSC == source)")
    sys.exit(0)


if __name__ == "__main__":
    main()
