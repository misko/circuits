#!/usr/bin/env python3
"""Fill LCSC + MPN into 06_build/fab/bom_jlc.csv for cook-hub.

Every ASSEMBLED line must resolve to an LCSC code (exit 1 otherwise) — the
BOM Comment (schematic value) is resolved in three tiers:
  1. SPECIFIC part -> keyword -> 02_parts/<MPN>/part.yaml sourcing.lcsc
  2. PASSIVE -> value token -> PASSIVE_LCSC (0603/0805 JLC basics,
     verified with jlc_stock_check at seal time)
  3. HAND_SOLDER lines stay uncoded ON PURPOSE (MANIFEST not_assembled):
     - K1-K16 DIP05-1A72-12L reed relays: DO-NOT-SUBSTITUTE (spec 15.4),
       JLC C1561362 stock 0 -> Digi-Key hand-solder line (order 16+4).
     - J2 Pico 2 socket (2x FemaleHeader 1x20 C50981: THT hand-solder).
       The Pico 2 module itself is NOT part of this BOM (ORDER_README).
     - J1 DC-005-20A barrel, J11 X9555WV IDC, J5/J9 KF350 terminals: THT.
DNP values (MAX31865 DNP / ENCODER DNP / STEP-DIR DNP headers) are excluded
by the exporter already ("DNP" in Value).
Run AFTER export_jlc_package.py: /usr/bin/python3 03_src/bom_seed.py
"""
import csv
import sys
from pathlib import Path
import yaml

HERE = Path(__file__).parent.parent
BOM = HERE / "06_build" / "fab" / "bom_jlc.csv"

SPECIFIC = [
    ("MAX31856", "MAX31856MUD+T"),
    ("AMS1117", "AMS1117-3.3"),
    ("AO3401A", "AO3401A"),
    ("2N7002", "2N7002"),
    ("SMBJ5.0A", "SMBJ5.0A"),
    ("SS34", "SS34"),
    ("USBLC6", "USBLC6-2SC6"),
    ("PESD5V0S1BA", "PESD5V0S1BA"),
    ("ULN2803A", "ULN2803ADWR"),
    ("74HC14", "SN74HC14DR"),
    ("74HC595", "SN74HC595DR"),
    ("74LVC1G00", "SN74LVC1G00DCKR"),
    ("74LVC1G11", "SN74LVC1G11DBVR"),
    ("SN74LVC1G123", "SN74LVC1G123DCTR"),
    ("LTV-817S", "LTV-817S-TA1"),
    ("MF-MSMF200L", "MF-MSMF200L-2"),
    ("600R ferrite", "GZ2012D601TF"),
    ("220u 16V", "RVT220UF16V"),
    ("RUN reset", "TS-1187A-B-A-B"),
    # JST XH connector family (SMD-compatible THT, JLC assembles THT XH)
    ("EXT 5V 2A", "DC-005-20A"),             # hand-solder tier (below)
]

# XH connectors by footprint token (Comment carries the function words)
XH_BY_FP = {
    "B2B-XH-A": "B2B-XH-A", "B3B-XH-A": "B3B-XH-A", "B4B-XH-A": "B4B-XH-A",
    "B5B-XH-A": "B5B-XH-A", "B6B-XH-A": "B6B-XH-A",
}

# 0603 basics (verify with jlc_stock_check before ordering); 0805 for bulk
PASSIVE_LCSC = {
    # capacitors
    ("100n", "C_0603"): "C14663",   # 100n X7R 50V 0603 basic
    ("10n", "C_0603"): "C57112",    # 10n X7R 50V 0603 basic
    ("1u", "C_0603"): "C15849",     # 1u X5R 25V 0603 basic
    ("10u", "C_0805"): "C15850",    # 10u X5R 25V 0805 basic
    ("22u", "C_0805"): "C45783",    # 22u X5R 25V 0805 basic
    # resistors 0603 1% basics
    ("33R", "R_0603"): "C23140",
    ("100R", "R_0603"): "C22775",
    ("330R", "R_0603"): "C23138",
    ("1k", "R_0603"): "C21190",
    ("2k2", "R_0603"): "C4190",
    ("3k3", "R_0603"): "C22978",
    ("4k7", "R_0603"): "C23162",
    ("10k", "R_0603"): "C25804",
    ("47k", "R_0603"): "C25819",
    ("100k", "R_0603"): "C25803",
    ("390k", "R_0603"): "C23150",
}

HAND_SOLDER = {
    "DIP05-1A72-12L": "K1-K16 reed relays — DO-NOT-SUBSTITUTE (spec 15.4); "
                      "Digi-Key DIP05-1A72-12L, order 16 + 4 spares",
    "Pico 2 socket": "J2 socket = 2x FemaleHeader 1x20 C50981 THT "
                     "(hand-solder); Pico 2 module NOT included",
    "EXT 5V 2A": "J1 DC-005-20A barrel jack THT (hand-solder, C130239)",
    "X9555WV": "J11 keypad IDC 2x16 THT (hand-solder, C692429)",
    "TC K-TYPE": "J5 KF350-3.5-2P terminal THT (hand-solder, C474892)",
    "NTC x3": "J9 XH THT",
}


def yaml_lcsc(mpn):
    y = yaml.safe_load(open(HERE / "02_parts" / mpn / "part.yaml"))
    return (y.get("sourcing") or {}).get("lcsc", ""), y.get("mpn", mpn)


def main():
    if not BOM.exists():
        sys.exit(f"{BOM} missing — run export_jlc_package.py first")
    rows = list(csv.DictReader(open(BOM)))
    missing = []
    hand = []
    mpn_map = {}
    for r in rows:
        c = r["Comment"]
        fp = r["Footprint"]
        if r.get("LCSC"):
            continue
        # tier 3 first: explicit hand-solder classes
        hs = next((v for k, v in HAND_SOLDER.items() if k in c), None)
        if hs is None and "DIP05" in c:
            hs = HAND_SOLDER["DIP05-1A72-12L"]
        if hs:
            hand.append((r["Designator"], c, hs))
            continue
        # XH connectors by footprint
        xh = next((m for k, m in XH_BY_FP.items() if k in fp), None)
        if xh:
            lcsc, mpn = yaml_lcsc(xh)
            r["LCSC"] = lcsc
            mpn_map[lcsc] = mpn
            continue
        # tier 1 specific
        sp = next((m for k, m in SPECIFIC.items() if k in c), None) \
            if isinstance(SPECIFIC, dict) else \
            next((m for k, m in SPECIFIC if k in c), None)
        if sp:
            lcsc, mpn = yaml_lcsc(sp)
            if lcsc:
                r["LCSC"] = lcsc
                mpn_map[lcsc] = mpn
                continue
            hand.append((r["Designator"], c, f"{sp}: no LCSC (hand-solder)"))
            continue
        # tier 2 passive
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
    # write the MPN map for the exporter's MPN column
    mp = HERE / "06_build" / "fab" / "lcsc_mpn_map.csv"
    with open(mp, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["LCSC", "MPN"])
        for k, v in sorted(mpn_map.items()):
            w.writerow([k, v])
    print(f"bom_seed: {sum(1 for r in rows if r.get('LCSC'))} coded lines; "
          f"{len(hand)} hand-solder lines:")
    for h in hand:
        print("   HAND:", h[0][:40], "—", h[2][:70])


if __name__ == "__main__":
    main()
