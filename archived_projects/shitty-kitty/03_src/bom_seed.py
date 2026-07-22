#!/usr/bin/env python3
"""Fill LCSC + MPN into 06_build/fab/bom_jlc.csv from 02_parts/<MPN>/part.yaml.
Every ASSEMBLED line must resolve (exit 1 otherwise); the hand-solder THT set
(J1 barrel, J3/J4 electrode headers, J5 motor XH, J6 endstop screw terminal,
J8 host header — decisions/0005) is deliberately UNCODED and listed for the
MANIFEST not_assembled line."""
import csv, sys
from pathlib import Path
import yaml

HERE = Path(__file__).parent.parent
MAP = {  # BOM Comment -> 02_parts/ MPN
    "ESP32-S3-WROOM-1-N8R2": "ESP32-S3-WROOM-1-N8R2",
    "TMC2209-LA-T": "TMC2209-LA-T",
    "MPR121QR2 0x5A": "MPR121QR2", "MPR121QR2 0x5B": "MPR121QR2",
    "MPR121QR2 0x5C": "MPR121QR2", "MPR121QR2 0x5D": "MPR121QR2",
    "LIS2DH12TR": "LIS2DH12TR",
    "AP63205WU-7": "AP63205WU-7",
    "AMS1117-3.3": "AMS1117-3.3",
    "TYPE-C-31-M-12": "TYPE-C-31-M-12",
    "USBLC6-2SC6": "USBLC6-2SC6",
    "AOD4185 revpol": "AOD4185",
    "SMBJ16A": "SMBJ16A",
    "2A polyfuse 16V": "SMD1812P200TF16",
    "10uH SWPA6045S": "SWPA6045S100MT",
    "TS-1187A RESET": "TS-1187A-B-A-B", "TS-1187A BOOT": "TS-1187A-B-A-B",
    "green PWR": "KT-0805G", "green STATUS": "KT-0805G",
    "100u 12V bulk": "RVT100UF25V67RV0011", "100u VS bulk": "RVT100UF25V67RV0011",
    "4.7u buck in": "CL21A475KAQNNNE", "4.7u LDO in": "CL21A475KAQNNNE",
    "4.7u 5VOUT": "CL21A475KAQNNNE",
    "22u buck out": "CL21A226MAQNNNE", "22u LDO out": "CL21A226MAQNNNE",
    "22u MCU 3V3": "CL21A226MAQNNNE", "22u accel": "CL21A226MAQNNNE",
    "1u EN": "CL21B105KBFNNNE",
    "22n CP fly": "CL21B223KBANNNC",
    "100n 12V": "CC0805KRX7R9BB104", "100n BST": "CC0805KRX7R9BB104",
    "100n VBUS": "CC0805KRX7R9BB104", "100n MCU 3V3": "CC0805KRX7R9BB104",
    "100n VCP": "CC0805KRX7R9BB104", "100n VCC_IO": "CC0805KRX7R9BB104",
    "100n VS": "CC0805KRX7R9BB104", "100n endstop": "CC0805KRX7R9BB104",
    "100n accel": "CC0805KRX7R9BB104", "100n MPR VDD": "CC0805KRX7R9BB104",
    "100n VREG": "CC0805KRX7R9BB104",
    "0.15R sense A": "1206W4F150LT5E", "0.15R sense B": "1206W4F150LT5E",
    "100k gate pd": "0805W8F1003T5E",
    "1k LED": "0805W8F1001T5E", "1k status LED": "0805W8F1001T5E",
    "1k TMC UART": "0805W8F1001T5E", "1k endstop ser": "0805W8F1001T5E",
    "4.7k SDA pu": "0805W8F4701T5E", "4.7k SCL pu": "0805W8F4701T5E",
    "5.1k CC1": "0805W8F5101T5E", "5.1k CC2": "0805W8F5101T5E",
    "10k EN": "0805W8F1002T5E", "10k ENN pu": "0805W8F1002T5E",
    "10k endstop pu": "0805W8F1002T5E", "10k IRQ pu": "0805W8F1002T5E",
    "75k REXT": "0805W8F7502T5E",
}
HAND_SOLDER = {  # Comment prefix -> (MPN, note); uncoded in BOM by design
    "DC-005C-20A": ("DC-005C-20A", "12V barrel jack"),
    "ELECTRODES INNER": ("KH-2.54PH180-1X13P-L11.5", "1x13 electrode header"),
    "ELECTRODES OUTER": ("KH-2.54PH180-1X13P-L11.5", "1x13 electrode header"),
    "MOTOR NEMA17": ("B4B-XH-A", "JST XH-4 motor"),
    "ENDSTOP TERM": ("KF128L-3.5-2P", "screw terminal"),
    "HOST 1x6": ("KH-2.54PH180-1X6P-L11.5", "1x6 host header (generic 2.54 ok)"),
}

bom = HERE / "06_build" / "fab" / "bom_jlc.csv"
rows = list(csv.DictReader(open(bom)))
missing, hand = [], []
for r in rows:
    c = r["Comment"]
    hs = next((v for k, v in HAND_SOLDER.items() if c.startswith(k)), None)
    if hs:
        mpn, note = hs
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
