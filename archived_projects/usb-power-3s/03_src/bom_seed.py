#!/usr/bin/env python3
"""Fill LCSC + MPN into 06_build/fab/bom_jlc.csv from 02_parts/<MPN>/part.yaml.
The map below is the explicit BOM-comment -> MPN assignment; every BOM line
must resolve (exit 1 otherwise), and every mapped MPN must exist in 02_parts/."""
import csv, sys
from pathlib import Path
import yaml

HERE = Path(__file__).parent.parent
MAP = {  # BOM Comment -> 02_parts/ MPN
    "100k EN-A hi (8.5V on)": "0402WGF1003TCE",
    "100n BST": "CC0402KRX7R9BB104", "100n CAP-VS": "CC0402KRX7R9BB104",
    "100n VS-GND": "CC0402KRX7R9BB104", "100n at U1.A": "CC0402KRX7R9BB104",
    "100n sw in": "CC0402KRX7R9BB104",
    "100u hybrid 35V": "EEHZA1V101P",
    "10k Rp CC1 (3A adv)": "RC0402FR-0710KL", "10k Rp CC2 (3A adv)": "RC0402FR-0710KL",
    "10u 50V X7R": "GRM32ER71H106KA12L",
    "13k RC1": "0402WGF1302TCE",
    "15A ATO": "178.6165.0002",
    "16k5 EN-A lo (7.5V off)": "AC0402FR-0716K5L", "16k5 RT (606kHz)": "AC0402FR-0716K5L",
    "16k5 seq div lo": "AC0402FR-0716K5L",
    "18p CILIM": "0402CG180J500NT",
    "1k LED-A": "0402WGF1001TCE", "1k LED-C": "0402WGF1001TCE",
    "1n2 CC3": "CC0402KRX7R9BB122",
    "20k PGOOD_A pu (5V_C)": "0402WGF2002TCE", "20k RFB1": "0402WGF2002TCE",
    "20k seq div hi": "0402WGF2002TCE",
    "220u poly 25mR": "6SVPC220MV",
    "22u port": "CL31A226KAHNNNE",
    "24k3 RILIM (2.51A)": "RC0402FR-0724K3L",
    "2u2 EN delay": "CL10A225KO8NNNC", "2u2 VCC": "CL10A225KO8NNNC",
    "348R RILIM (wc 6.3A)": "RT0402BRD07348RL",
    "39p CC2": "CC0402JRNPO9BN390",
    "3k74 RFB2 (5.08V)": "0402WGF3741TCE",
    "432R RILIM (wc 7.8A)": "RC0402FR-07432RL",
    "47n HGATE dv/dt": "0402B473K500NT", "47n SS (4ms)": "0402B473K500NT",
    "47u 10V X7R": "GRM32ER71A476KE15L",
    "4k64 RC2": "0402WGF4641TCE",
    "52k3 ladder-mid (UVLO 9.33V)": "0402WGF5232TCE",
    "82k5 ladder-bot (OV 15.25V)": "RC-02K8252FT",
    "887k ladder-top": "ERJ2RKF8873X",
    "8n2 CC1": "0402B822K500NT",
    "CSD18543Q3A HS": "CSD18543Q3A", "CSD18543Q3A LS": "CSD18543Q3A",
    "CSD18543Q3A diode": "CSD18543Q3A", "CSD18543Q3A switch": "CSD18543Q3A",
    "LM5145 rail A": "LM5145RGYR", "LM5145 rail B": "LM5145RGYR",
    "LM74800-Q1": "LM74800QDRRRQ1",
    "MWSA1005S-3R3 16A": "MWSA1005S-3R3MT",
    "SMBJ16A": "SMBJ16A", "SMBJ5.0A": "SMBJ5.0A",
    "TPS2557 2.5A": "TPS2557DRBR",
    "USB-A 2.5A": "1001-011-01101",
    "USB4105-GF-A": "USB4105-GF-A",
    "XT60_BATT": "XT60PW-M",
    "green 5V_A": "KT-0805G", "green 5V_C": "KT-0805G",
}

bom = HERE / "06_build" / "fab" / "bom_jlc.csv"
# parts sourced outside JLC: BOM line stays uncoded, ordered/hand-soldered separately
HAND_SOLDER = {"USB-A 2.5A"}

# after LCSC seeding, re-export MERGES same-code lines and shortens the
# comment to the shared value token ("100n BST"+"100n CAP-VS" -> "100n"),
# so exact-comment lookup must fall back to the first token - which is
# unambiguous by construction (lines only merge when the MPN already agrees)
TOKEN_MAP = {}
for k, v in MAP.items():
    t = k.split()[0]
    if TOKEN_MAP.setdefault(t, v) != v:
        sys.exit(f"ambiguous token {t!r}: {TOKEN_MAP[t]} vs {v}")

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
    if r["Comment"] in HAND_SOLDER or "lcsc" not in src:
        r["MPN"] = mpn  # uncoded on purpose: not JLC-assemblable
        continue
    lcsc = src["lcsc"]
    if not lcsc or "TBD" in str(lcsc):
        missing.append(f"{mpn}: sourcing TBD")
        continue
    r["LCSC"] = lcsc
    r["MPN"] = mpn
if missing:
    print("FAILURES:\n  " + "\n  ".join(missing))
    sys.exit(1)
w = csv.DictWriter(open(bom, "w", newline=""), fieldnames=rows[0].keys())
w.writeheader(); w.writerows(rows)
print(f"seeded {len(rows)} BOM lines with LCSC codes")
