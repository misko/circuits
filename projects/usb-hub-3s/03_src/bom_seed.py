#!/usr/bin/env python3
"""bom_seed — unambiguous LCSC mapping gate for usb-hub-3s.

Input : 06_build/fab/bom_jlc.csv + cpl_jlc.csv (export_fab_jlc.py output)
Output: 06_build/fab/bom.csv  (assembly lines, every line coded)
        06_build/fab/cpl.csv  (assembled refs only)

Rules (each is a gate, not a convenience):
- A Comment that IS an LCSC code (C\\d+) maps to itself, but ONLY if that
  code appears in some 02_parts/*/part.yaml sourcing block (lcsc or
  alternates) — a code the parts stage never verified is a typo until
  proven otherwise.
- Passive values map through 03_src/rules/passives_lcsc.yaml
  ((value, footprint) -> code). Missing entry = FAIL, never auto-match:
  JLC auto-match is how wrong-voltage caps ship.
- R25 is DNP (ADR 0004: PDO-config slot, value table is app-note-only).
  It is REMOVED from bom + cpl and reported. Pads stay on the board.
- Hand-solder parts (part.yaml sourcing.lcsc == null) stay UNCODED and
  OUT of bom/cpl, listed explicitly for the ORDER_README.

Exit 1 unless: every assembly line coded AND every non-assembled ref is
either DNP or on the hand-solder list.
"""
import csv
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
FAB = ROOT / "06_build" / "fab"
DNP_REFS = {"R25"}          # ADR 0004
HAND_SOLDER_COMMENTS = {}   # filled from part.yamls with lcsc: null


def known_codes():
    codes = {}
    for py in (ROOT / "02_parts").glob("*/part.yaml"):
        d = yaml.safe_load(py.read_text())
        src = d.get("sourcing") or {}
        mpn = str(d.get("mpn", py.parent.name))
        if src.get("lcsc"):
            codes[src["lcsc"]] = mpn
            for alt in src.get("alternates") or []:
                codes[alt] = f"{mpn} (alt)"
        else:
            HAND_SOLDER_COMMENTS[mpn] = (src.get("note") or "").strip()
    return codes


def main():
    codes = known_codes()
    ptab = yaml.safe_load(
        (ROOT / "03_src" / "rules" / "passives_lcsc.yaml").read_text())
    passives = {(e["value"], e["footprint"]): e["lcsc"]
                for e in ptab["map"]}

    rows = list(csv.DictReader(open(FAB / "bom_jlc.csv")))
    out, uncoded, dnp_lines, hand = [], [], [], []
    for r in rows:
        refs = [x for x in re.split(r"[,\s]+", r["Designator"]) if x]
        val, fp = r["Comment"], r["Footprint"]
        live = [x for x in refs if x not in DNP_REFS]
        if len(live) != len(refs):
            dnp_lines.append(f"{sorted(set(refs)-set(live))} {val} {fp}")
        if not live:
            continue
        if val in HAND_SOLDER_COMMENTS:
            hand.append((val, live, fp))
            continue
        lcsc = None
        if re.fullmatch(r"C\d+", val):
            if val not in codes:
                print(f"FAIL: comment {val} ({live}) is not a code any "
                      f"part.yaml sourcing block verified")
                return 1
            lcsc = val
        else:
            lcsc = passives.get((val, fp))
        if not lcsc:
            uncoded.append((val, live, fp))
            continue
        out.append({"Comment": val, "Designator": ",".join(live),
                    "Footprint": fp, "LCSC": lcsc})

    assembled = {ref for r in out for ref in r["Designator"].split(",")}
    with open(FAB / "bom.csv", "w", newline="") as f:
        w = csv.DictWriter(f, ["Comment", "Designator", "Footprint", "LCSC"])
        w.writeheader()
        w.writerows(sorted(out, key=lambda r: r["Comment"]))

    kept = dropped = 0
    with open(FAB / "cpl_jlc.csv") as fi, \
            open(FAB / "cpl.csv", "w", newline="") as fo:
        rd = csv.reader(fi)
        w = csv.writer(fo)
        w.writerow(next(rd))
        for row in rd:
            if row[0] in assembled:
                w.writerow(row)
                kept += 1
            else:
                dropped += 1

    print(f"bom.csv: {len(out)} coded lines, {len(assembled)} parts; "
          f"cpl.csv: {kept} placed, {dropped} not-assembled")
    print(f"DNP (pads stay, no part): {dnp_lines}")
    print("hand-solder (uncoded by design):")
    for val, refs2, fp in hand:
        print(f"  {refs2} {val} {fp} — {HAND_SOLDER_COMMENTS[val]}")
    if uncoded:
        print("FAIL — unmapped assembly lines (add to passives_lcsc.yaml "
              "with a verified code):")
        for val, refs2, fp in uncoded:
            print(f"  {refs2} {val} {fp}")
        return 1
    not_assembled = ({ref for r2 in rows for ref in re.split(r"[,\s]+", r2["Designator"]) if ref}
                     - assembled - DNP_REFS
                     - {ref for _, rr, _ in hand for ref in rr})
    if not_assembled:
        print(f"FAIL — refs neither coded, DNP nor hand-solder: "
              f"{sorted(not_assembled)}")
        return 1
    print("SEED GATE: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
