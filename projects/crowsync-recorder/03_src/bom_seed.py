#!/usr/bin/env python3
"""Fill LCSC + MPN into 06_build/fab/bom_jlc.csv from 02_parts/<MPN>/part.yaml.
Every BOM line must resolve (exit 1 otherwise); every mapped MPN must exist
in 02_parts/. All lines are JLC-assembled (decisions/0005): no hand-solder set."""
import csv, sys
from pathlib import Path
import yaml

HERE = Path(__file__).parent.parent
MAP = {  # BOM Comment -> 02_parts/ MPN
    "USB4105-GF-A": "USB4105-GF-A",
    "USBLC6-2SC6 USB": "USBLC6-2SC6",
    "USBLC6-2SC6 harness": "USBLC6-2SC6",
    "PCM2900CDBR": "PCM2900CDBR",
    "TLV9062IDR": "TLV9062IDR",
    "TPS7A2033PDBVR": "TPS7A2033PDBVR",
    "12MHz 3225 20pF": "X322512MSB4SI",
    "600R@100MHz bias": "GZ1608D601TF",
    "green ACT": "KT-0805G", "green PWR": "KT-0805G",
    "JST-GH mic": "SM03B-GHS-TB",
    "JST-GH PPS": "SM02B-GHS-TB",
    "22R D+ series": "0603WAF220JT5E", "22R D- series": "0603WAF220JT5E",
    "1k5 D+ pullup (VDDI)": "0603WAF1501T5E",
    "5k1 Rd CC1 (UFP)": "0603WAF5101T5E", "5k1 Rd CC2 (UFP)": "0603WAF5101T5E",
    "2R2 VBUS filter": "RCA032R2FLF",
    "1M XTI-XTO": "0603WAF1004T5E",
    "100R mic series": "0603WAF1000T5E", "100R amp out": "0603WAF1000T5E",
    "100R PPS series": "0603WAF1000T5E",
    "2k2 mic bias": "0603WAF2201T5E", "2k2 LED 5V": "0603WAF2201T5E",
    "100k bias->VCOM": "0603WAF1003T5E",
    "3k01 Rf (gain 4.0)": "0603WAF3011T5E",
    "1k Rg": "0603WAF1001T5E", "1k LED SSPND": "0603WAF1001T5E",
    "22k div top": "0603WAF2202T5E",
    "10k div bottom": "RC0603FR-0710KL",
    "10u VCCCI": "CL10A106KP8NNNC", "10u VCOM": "CL10A106KP8NNNC",
    "10u 5V bulk": "CL10A106KP8NNNC", "10u 3V3A": "CL10A106KP8NNNC",
    "10u bias res": "CL10A106KP8NNNC", "10u Cg (15.9Hz)": "CL10A106KP8NNNC",
    "1u VBUS pin": "CL10A105KB8NNNC", "1u VDDI": "CL10A105KB8NNNC",
    "1u VCCXI": "CL10A105KB8NNNC", "1u VCCP2I": "CL10A105KB8NNNC",
    "1u VCCP1I": "CL10A105KB8NNNC", "1u LDO in": "CL10A105KB8NNNC",
    "1u mic couple": "CL10A105KB8NNNC", "1u VINL couple": "CL10A105KB8NNNC",
    "1u VINR couple": "CL10A105KB8NNNC",
    "100n 5V": "CC0603KRX7R9BB104", "100n 3V3A U2": "CC0603KRX7R9BB104",
    "100n bias": "CC0603KRX7R9BB104",
    "33p XTI": "CL10C330JB8NNNC", "33p XTO": "CL10C330JB8NNNC",
    "1n RF stop": "CL10B102KB8NNNC",
}

# token fallback for post-seed merged lines (merge only happens when the
# MPN already agrees, so ambiguous tokens are dropped from the fallback)
TOKEN_MAP = {}
for k, v in MAP.items():
    t = k.split()[0]
    if t in TOKEN_MAP and TOKEN_MAP[t] != v:
        TOKEN_MAP[t] = None  # ambiguous (e.g. JST-GH) -> full-comment only
    else:
        TOKEN_MAP.setdefault(t, v)

bom = HERE / "06_build" / "fab" / "bom_jlc.csv"
rows = list(csv.DictReader(open(bom)))
missing = []
for r in rows:
    mpn = MAP.get(r["Comment"]) or TOKEN_MAP.get(r["Comment"].split()[0])
    if not mpn:
        missing.append(f"unmapped BOM line: {r['Comment']}")
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
print(f"seeded {len(rows)} BOM lines with LCSC codes (0 hand-solder lines)")
