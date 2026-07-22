#!/usr/bin/env python3
"""Fill LCSC + MPN into 06_build/fab/bom_jlc.csv from 02_parts/<MPN>/part.yaml.
Every ASSEMBLED line must resolve (exit 1 otherwise); the hand-solder THT set
(terminals J4-J12, OLED socket J2 — decisions/0005) is deliberately UNCODED
and listed for the MANIFEST not_assembled line."""
import csv, sys
from pathlib import Path
import yaml

HERE = Path(__file__).parent.parent
MAP = {  # BOM Comment -> 02_parts/ MPN
    "ESP32-S3-WROOM-1-N8R2": "ESP32-S3-WROOM-1-N8R2",
    "TYPE-C-31-M-12": "TYPE-C-31-M-12",
    "USBLC6-2SC6": "USBLC6-2SC6",
    "LM339DT": "LM339DT",
    "AO3400A": "AO3400A",
    "AMS1117-3.3": "AMS1117-3.3",
    "TS-1187A RESET": "TS-1187A-B-A-B",
    "TS-1187A BOOT": "TS-1187A-B-A-B",
    "green PWR": "KT-0805G",
    "100u 5V bulk": "RVT100UF16V67RV0016",
    "22u LDO in": "CL21A226MAQNNNE", "22u LDO out": "CL21A226MAQNNNE",
    "22u MCU 3V3": "CL21A226MAQNNNE",
    "1u EN": "CL21B105KBFNNNE",
    "100n 5V bulk": "CC0805KRX7R9BB104", "100n MCU 3V3": "CC0805KRX7R9BB104",
    "100n LM339": "CC0805KRX7R9BB104", "100n OLED": "CC0805KRX7R9BB104",
    "100n btn": "CC0805KRX7R9BB104",
    "100R gate": "0805W8F1000T5E",
    "1k PD load": "0805W8F1001T5E", "1k btn ser": "0805W8F1001T5E",
    "1k LED": "0805W8F1001T5E",
    "2.7k div bot": "0805W8F2701T5E",
    "4.7k SDA pu": "0805W8F4701T5E", "4.7k SCL pu": "0805W8F4701T5E",
    "5.1k CC1": "0805W8F5101T5E", "5.1k CC2": "0805W8F5101T5E",
    "10k div top": "0805W8F1002T5E", "10k comp pu": "0805W8F1002T5E",
    "10k btn pu": "0805W8F1002T5E", "10k EN": "0805W8F1002T5E",
    "33k hyst": "0805W8F3302T5E",
    "100k gate pd": "0805W8F1003T5E",
}
HAND_SOLDER = {  # Comment prefix -> (MPN, note); uncoded in BOM by design
    "LASER": ("KF128L-3.5-2P", "screw terminal"),
    "PHOTODIODE": ("KF128L-3.5-2P", "screw terminal"),
    "BUTTON": ("KF128L-3.5-2P", "screw terminal"),
    "OLED HDR": ("2.54-1x4P-Female", "female socket"),
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
w.writeheader(); w.writerows(rows)
coded = sum(1 for r in rows if r["LCSC"])
print(f"seeded {coded} assembled BOM lines with LCSC codes; "
      f"{len(hand)} hand-solder lines uncoded by design:")
for h in hand:
    print("  ", h)
