#!/usr/bin/env python3
"""Parts parity + sourcing gate: map every BOM line (Comment+Footprint) to
a 02_parts/<MPN>/part.yaml and its LCSC code; FAIL on unmapped lines or
TBD sourcing. Fills the BOM's LCSC column and writes lcsc_mpn_map.csv for
the exporter's MPN column. Hand-solder parts (THT connectors JLC cannot
economically assemble) are explicitly listed, stay uncoded in the
ASSEMBLY BOM, and must appear in the release MANIFEST.

Usage: python3 03_src/bom_seed.py [FABDIR]   (default 06_build/fab)
"""
import csv
import sys
from pathlib import Path

import yaml

PROJ = Path(__file__).resolve().parent.parent
FAB = Path(sys.argv[1]) if len(sys.argv) > 1 else PROJ / "06_build" / "fab"

# BOM Comment (value) -> MPN. THE mapping; a BOM value not here fails.
VALUE_TO_MPN = {
    "SY8368QNC": "SY8368QNC",
    "AOD4185": "AOD4185",
    "SMBJ15A": "SMBJ15A",
    "15A": "0451015.MRL",
    "USBLC6-2SC6": "USBLC6-2SC6",
    "1.5uH": "FXL0630-1R5-M",
    "2.2uH": "FXL0630-2R2-M",
    "10uF 25V X7R": "CL31B106KAHNNNE",
    "22uF 16V X7R": "CL32B226KOJNNNE",
    "100uF 25V polymer": "MA25V100M6x6",
    "100nF": "CL10B104KB8NNNC",
    "2.2uF": "CL10A225KO8NNNC",
    "10k 1%": "0603WAF1002T5E",
    "22k 1%": "0603WAF2202T5E",
    "3k 1%": "0603WAF3001T5E",
    "1k": "0603WAF1001T5E",
    "100k": "0603WAF1003T5E",
    "red": "NCD0805R1",
    "green": "KT-0805G",
    "XT60PW-M": "XT60PW-M",
    "USB-A": "XY-AF90-WJDG",
    "TYPE-C-31-M-12A": "TYPE-C-31-M-12A",
}

# hand-solder / not JLC-assembled: stay UNCODED in the assembly BOM
HAND_SOLDER = {"XT60PW-M", "XY-AF90-WJDG"}


def main():
    bom_path = FAB / "bom_jlc.csv"
    if not bom_path.exists():
        raise SystemExit(f"ERROR: {bom_path} missing — run the JLC export first")
    rows = list(csv.DictReader(bom_path.open()))
    if not rows:
        raise SystemExit("ERROR: BOM parse yielded zero lines")

    fails, mpn_map = [], {}
    for row in rows:
        val = row["Comment"]
        mpn = VALUE_TO_MPN.get(val)
        if mpn is None:
            fails.append(f"unmapped BOM value: {val!r} ({row['Designator']})")
            continue
        pyaml = PROJ / "02_parts" / mpn / "part.yaml"
        if not pyaml.exists():
            fails.append(f"{val!r} -> {mpn}: no 02_parts/{mpn}/part.yaml")
            continue
        d = yaml.safe_load(pyaml.read_text())
        lcsc = (d.get("sourcing") or {}).get("lcsc")
        if mpn in HAND_SOLDER:
            row["LCSC"] = ""      # deliberate: hand-solder list
            continue
        if not lcsc or str(lcsc).upper().startswith("TBD"):
            fails.append(f"{mpn}: sourcing.lcsc is TBD/missing")
            continue
        row["LCSC"] = lcsc
        mpn_map[lcsc] = mpn

    # reverse parity: every 02_parts dir must be in the BOM
    bom_mpns = {VALUE_TO_MPN.get(r["Comment"]) for r in rows}
    for d in sorted((PROJ / "02_parts").iterdir()):
        if d.is_dir() and d.name not in bom_mpns:
            fails.append(f"stale 02_parts/{d.name}: not in BOM")

    if fails:
        print("BOM SEED: FAIL")
        for f in fails:
            print(" -", f)
        sys.exit(1)

    with bom_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with (FAB / "lcsc_mpn_map.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["LCSC", "MPN"])
        for lcsc, mpn in sorted(mpn_map.items()):
            w.writerow([lcsc, mpn])
    hs = sorted({r["Designator"] for r in rows
                 if VALUE_TO_MPN[r["Comment"]] in HAND_SOLDER})
    print(f"BOM SEED: PASS — {len(rows)} lines coded; hand-solder: {hs}")


if __name__ == "__main__":
    main()
