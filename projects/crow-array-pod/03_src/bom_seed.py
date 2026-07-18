#!/usr/bin/env python3
"""Fill LCSC + MPN into 06_build/fab/bom_jlc.csv from 02_parts/<MPN>/part.yaml.
Every ASSEMBLED line must resolve (exit 1 otherwise); the hand-solder set
(J1 terminal, J2 mic pads — decisions D6/D10; the CMT-8504 transducer IS JLC-coded, C22359707) is
deliberately UNCODED and listed for the MANIFEST not_assembled line."""
import csv
import sys
from pathlib import Path
import yaml

HERE = Path(__file__).parent.parent
MAP = {  # BOM Comment -> 02_parts/ MPN
    "OPA1678IDR": "OPA1678IDR",
    "TPD2E2U06DRLR": "TPD2E2U06DRLR",
    "SS14 flyback": "SS14",
    "100u 5VF": "RVT100UF16V67RV0016",
    "100n 5VF": "CC0805KRX7R9BB104", "100n VMID": "CC0805KRX7R9BB104",
    "100n U1": "CC0805KRX7R9BB104",
    "1u coupling": "CL21B105KBFNNNE",
    "10u VMID": "CL21A106KAYNNNE", "10u 5V bulk": "CL21A106KAYNNNE",
    "100R 5VF": "0805W8F1000T5E",
    "3.9k mic bias": "0805W8F3901T5E",
    "10k div hi": "0805W8F1002T5E", "10k div lo": "0805W8F1002T5E",
    "10k fb A": "0805W8F1002T5E",
    "20k gain A": "0805W8F2002T5E", "20k inv in": "0805W8F2002T5E",
    "20k inv fb": "0805W8F2002T5E",
    "68R iso +": "0805W8F680JT5E", "68R iso -": "0805W8F680JT5E",
    "100k bias": "0805W8F1003T5E",
    "CMT-8504-100-SMT-TR": "CMT-8504-100-SMT-TR",
    "0R beep series": "0805W8F0000T5E", "0R choke byp +": "0805W8F0000T5E",
    "0R choke byp -": "0805W8F0000T5E",
}
HAND_SOLDER = {  # Comment prefix -> (MPN, note); uncoded in BOM by design
    "KF128L-3.5-8P": ("KF128L-3.5-8P", "3.5mm screw terminal, THT"),
    "MIC PADS": ("PinHeader-1x02", "mic wire pads (capsule on leads)"),
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
