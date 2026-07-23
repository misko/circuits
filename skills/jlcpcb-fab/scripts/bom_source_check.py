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

Exit 1 on any finding; the exit code IS the gate.
"""
import argparse
import csv
import glob
import json
import re
import sys
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


def read_bom(bom_path):
    """[(designators:list[str], lcsc:str, comment:str)] from a fab BOM.
    Tolerates both the Comment,Designator,Footprint,MPN,LCSC and the older
    Comment,Designator,Footprint,LCSC headers."""
    rows = []
    with open(bom_path, newline="") as f:
        for r in csv.DictReader(f):
            desig = r.get("Designator") or r.get("Designators") or ""
            refs = [d.strip() for d in desig.split(",") if d.strip()]
            rows.append((refs, (r.get("LCSC") or "").strip(),
                         (r.get("Comment") or "").strip()))
    return rows


def check(bom_rows, refdes_code, vendored=None):
    """Returns a list of finding strings; empty == PASS.

    refdes_code: {refdes: source_lcsc} (authoritative, per-refdes).
    vendored:    {lcsc: MPN} of vendored primary codes, or None to skip leg B."""
    findings = []
    bom_codes = {lc for _, lc, _ in bom_rows if lc}
    source_codes = {c for c in refdes_code.values() if c}

    # ---- leg A: per-refdes vs the source of truth (circuit.json) ----
    for refs, bom_lcsc, comment in bom_rows:
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
