#!/usr/bin/env python3
"""Fill LCSC + MPN into 06_build/fab/bom_jlc.csv from 02_parts/<MPN>/part.yaml.
Every ASSEMBLED line must resolve (exit 1 otherwise); the hand-solder set
(F1-F6 Keystone 3557-2 holders — 30A THT joints, ADR-0005) is deliberately
UNCODED and listed for the MANIFEST not_assembled line. J1-J8 studs are
bare plated holes (no part), J10 is DNP — neither reaches the BOM."""
import csv
import sys
from pathlib import Path
import yaml

HERE = Path(__file__).parent.parent
MAP = {  # BOM Comment -> 02_parts/ MPN
    "INA238AIDGSR": "INA238AIDGSR",
    "WSLP2726 0.5mR": "WSLP2726L5000FEA",
    "LMR16006XDDCR": "LMR16006XDDCR",
    "ESP32-C3-WROOM-02-N4": "ESP32-C3-WROOM-02-N4",
    "W25Q64JVSSIQ": "W25Q64JVSSIQ",
    "AMS1117-3.3": "AMS1117-3.3",
    "USBLC6-2SC6": "USBLC6-2SC6",
    "TYPE-C-31-M-12": "TYPE-C-31-M-12",
    "22u SWPA6045S": "SWPA6045S220MT",
    "SS310 rev block": "SS310", "SS310 catch": "SS310",
    "SMCJ33A bus TVS": "SMCJ33A", "SMBJ33A tap TVS": "SMBJ33A",
    "B5819W OR": "B5819W",
    "0466002 2A": "0466002.NRHF",
    "RESET": "TS-1187A-B-A-B", "BOOT": "TS-1187A-B-A-B",
    "KT-0805G PWR": "KT-0805G", "KT-0805G ST": "KT-0805G",
    # resistors (UNI-ROYAL 0805 1%)
    "10R sense+": "0805W8F100JT5E", "10R sense-": "0805W8F100JT5E",
    "4k7 SDA pu": "0805W8F4701T5E", "4k7 SCL pu": "0805W8F4701T5E",
    "10k ALERT pu": "0805W8F1002T5E", "10k IO2 pu": "0805W8F1002T5E",
    "10k CS pu": "0805W8F1002T5E", "10k IO8 pu": "0805W8F1002T5E",
    "10k EN pu": "0805W8F1002T5E", "10k FB lo": "0805W8F1002T5E",
    "33k FB hi": "0805W8F3302T5E", "560k UVLO hi": "0805W8F5603T5E",
    "100k UVLO lo": "0805W8F1003T5E",
    "5k1 CC1": "0805W8F5101T5E", "5k1 CC2": "0805W8F5101T5E",
    "2k PWR LED": "0805W8F2001T5E", "1k ST LED": "0805W8F1001T5E",
    # capacitors
    "100n INA": "CC0805KRX7R9BB104", "100n diff": "CC0805KRX7R9BB104",
    "100n U7": "CC0805KRX7R9BB104", "100n U11": "CC0805KRX7R9BB104",
    "100n VIN": "CC0805KRX7R9BB104", "100n boot": "CC0805KRX7R9BB104",
    "100n corridor 3V3": "CC0805KRX7R9BB104", "100n VUSB": "CC0805KRX7R9BB104",
    "22u 3V3": "CL31A226KAHNNNE", "22u U7": "CL31A226KAHNNNE",
    "22u LDO out": "CL31A226KAHNNNE",
    "4u7 50V": "GRM32ER71H475KA88L",
    "10u LDO in": "CL21A106KAYNNNE",
    "1u EN": "CL21B105KBFNNNE",
    # merged-line comments (exporter merges per (LCSC, footprint) after codes land)
    "10R": "0805W8F100JT5E", "100n": "CC0805KRX7R9BB104",
    "22u": "CL31A226KAHNNNE", "4k7": "0805W8F4701T5E",
    "10k": "0805W8F1002T5E", "5k1": "0805W8F5101T5E",
    "SS310": "SS310", "TS-1187A": "TS-1187A-B-A-B", "KT-0805G": "KT-0805G",
}
HAND_SOLDER = {  # Comment prefix -> (MPN, note); uncoded in BOM by design
    "3557-2": ("3557-2", "Keystone ATO holder, THT 30A joints, hand-solder"),
}

bom = HERE / "06_build" / "fab" / "bom_jlc.csv"
rows = list(csv.DictReader(open(bom)))
missing, hand = [], []
for r in rows:
    c = r["Comment"]
    hs = next((v for k, v in HAND_SOLDER.items() if c.startswith(k)), None)
    if hs:
        mpn, note = hs
        if not (HERE / "02_parts" / mpn / "part.yaml").exists():
            missing.append(f"{mpn}: no 02_parts/ entry (hand-solder)")
        hand.append(f"{r['Designator']} ({c}: {mpn}, {note})")
        r["LCSC"] = ""
        r["MPN"] = mpn
        continue
    mpn = MAP.get(c)
    if not mpn:
        missing.append(f"unmapped BOM line: {c}")
        continue
    y = HERE / "02_parts" / mpn / "part.yaml"
    if not y.exists():
        missing.append(f"{mpn}: no 02_parts/ entry")
        continue
    src = yaml.safe_load(open(y))["sourcing"]
    lcsc = src.get("lcsc")
    if not lcsc or "TBD" in str(lcsc):
        missing.append(f"{mpn}: sourcing TBD")
        continue
    r["LCSC"] = lcsc
    r["MPN"] = mpn
if missing:
    print("FAILURES:\n  " + "\n  ".join(missing))
    sys.exit(1)
fieldnames = list(rows[0].keys())
if "MPN" not in fieldnames:
    fieldnames.insert(fieldnames.index("LCSC"), "MPN")
w = csv.DictWriter(open(bom, "w", newline=""), fieldnames=fieldnames)
w.writeheader()
w.writerows(rows)
coded = sum(1 for r in rows if r["LCSC"])
print(f"seeded {coded} assembled BOM lines with LCSC codes; "
      f"{len(hand)} hand-solder lines uncoded by design:")
for h in hand:
    print("  ", h)
