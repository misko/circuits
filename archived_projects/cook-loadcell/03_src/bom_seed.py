#!/usr/bin/env python3
"""Fill LCSC + MPN into 06_build/fab/bom_jlc.csv for cook-loadcell.
Every ASSEMBLED line must resolve to an LCSC code (exit 1 otherwise).
XH connectors are THT — JLC assembles THT XH headers (economic PCBA THT);
if the order screen rejects them they fall back to hand-solder (codes kept
so the twin/rotation checks still run). JP1 pin header = hand-solder.
Run AFTER export_jlc_package.py: /usr/bin/python3 03_src/bom_seed.py"""
import csv
import sys
from pathlib import Path
import yaml

HERE = Path(__file__).parent.parent
BOM = HERE / "06_build" / "fab" / "bom_jlc.csv"

SPECIFIC = [
    ("HX711", "HX711"),
    ("PESD5V0S1BA", "PESD5V0S1BA"),
    ("S8550", "S8550"),
    ("SENSOR", "B3B-XH-A"),
    ("FULL BRIDGE ALT", "B5B-XH-A"),
    ("TO HUB J6", "B5B-XH-A"),
]
PASSIVE_LCSC = {
    ("100n", "C_0603"): "C14663",
    ("10u", "C_0805"): "C15850",
    ("100R", "R_0603"): "C22775",
    ("20k", "R_0603"): "C4184",      # 20k 1% 0603 basic
    ("8.2k", "R_0603"): "C25981",    # 8.2k 1% 0603 basic
}
HAND_SOLDER = {
    "RATE 1-2": "JP1 2.54 pin header THT + shunt on 1-2 (hand-solder)",
}


def yaml_lcsc(mpn):
    y = yaml.safe_load(open(HERE / "02_parts" / mpn / "part.yaml"))
    return (y.get("sourcing") or {}).get("lcsc", ""), y.get("mpn", mpn)


def main():
    if not BOM.exists():
        sys.exit(f"{BOM} missing — run export_jlc_package.py first")
    rows = list(csv.DictReader(open(BOM)))
    missing, hand, mpn_map = [], [], {}
    for r in rows:
        c, fp = r["Comment"], r["Footprint"]
        if r.get("LCSC"):
            continue
        hs = next((v for k, v in HAND_SOLDER.items() if k in c), None)
        if hs:
            hand.append((r["Designator"], c, hs))
            continue
        sp = next((m for k, m in SPECIFIC if k in c), None)
        if sp:
            lcsc, mpn = yaml_lcsc(sp)
            r["LCSC"] = lcsc
            mpn_map[lcsc] = mpn
            continue
        tok = c.split()[0]
        fam = ("C_0603" if "C_0603" in fp else "C_0805" if "C_0805" in fp
               else "R_0603" if "R_0603" in fp else None)
        code = PASSIVE_LCSC.get((tok, fam))
        if code:
            r["LCSC"] = code
            continue
        missing.append((r["Designator"], c, fp))
    if missing:
        print("UNRESOLVED BOM LINES:")
        for m in missing:
            print("  ", m)
        sys.exit(1)
    with open(BOM, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    mp = HERE / "06_build" / "fab" / "lcsc_mpn_map.csv"
    with open(mp, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["LCSC", "MPN"])
        for k, v in sorted(mpn_map.items()):
            w.writerow([k, v])
    print(f"bom_seed: {sum(1 for r in rows if r.get('LCSC'))} coded; "
          f"{len(hand)} hand-solder:")
    for h in hand:
        print("   HAND:", h[0], "—", h[2])


if __name__ == "__main__":
    main()
