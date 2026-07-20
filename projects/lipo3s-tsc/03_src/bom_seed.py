#!/usr/bin/env python3
"""Fill LCSC + MPN into 06_build/fab/bom_jlc.csv from 02_parts/<MPN>/part.yaml.

lipo3s-tsc variant: the tscircuit front-end names BOM Comments by the converter's
component VALUE (passives = tscircuit display value, e.g. "887kΩ"/"348Ω"/"100nF";
specialty parts = their LCSC code, e.g. "C840100"), NOT the sealed board's
descriptive strings ("887k ladder-top"). So MAP is keyed by those values/codes.
Each (value/code) is unambiguous -> a single MPN (verified against the 100-part
netlist). Every BOM line must resolve (exit 1 otherwise); every mapped MPN must
exist in 02_parts/."""
import csv, sys
from pathlib import Path
import yaml

HERE = Path(__file__).parent.parent
MAP = {  # BOM Comment (converter value/code) -> 02_parts/ MPN
    # passives, keyed by tscircuit display value
    "887kΩ": "ERJ2RKF8873X",
    "82.5kΩ": "RC-02K8252FT",
    "52.3kΩ": "0402WGF5232TCE",
    "100kΩ": "0402WGF1003TCE",
    "24.3kΩ": "RC0402FR-0724K3L",
    "20kΩ": "0402WGF2002TCE",
    "16.5kΩ": "AC0402FR-0716K5L",
    "13kΩ": "0402WGF1302TCE",
    "10kΩ": "RC0402FR-0710KL",
    "4.64kΩ": "0402WGF4641TCE",
    "3.74kΩ": "0402WGF3741TCE",
    "1kΩ": "0402WGF1001TCE",
    "432Ω": "RC0402FR-07432RL",
    "348Ω": "RT0402BRD07348RL",
    "220uF": "6SVPC220MV",
    "100uF": "EEHZA1V101P",
    "47uF": "GRM32ER71A476KE15L",
    "22uF": "CL31A226KAHNNNE",
    "10uF": "GRM32ER71H106KA12L",
    "2.2uF": "CL10A225KO8NNNC",
    "100nF": "CC0402KRX7R9BB104",
    "47nF": "0402B473K500NT",
    "8.2nF": "0402B822K500NT",
    "1.2nF": "CC0402KRX7R9BB122",
    "39pF": "CC0402JRNPO9BN390",
    "18pF": "0402CG180J500NT",
    # specialty parts, keyed by LCSC code (the converter value for custom-fp chips)
    "C840100": "CSD18543Q3A",
    "C3215600": "LM74800QDRRRQ1",
    "C485912": "LM5145RGYR",
    "C130056": "TPS2557DRBR",
    "C17700181": "MWSA1005S-3R3MT",
    "C207061": "178.6165.0002",
    "C98732": "XT60PW-M",
    "C3020560": "USB4105-GF-A",
    "C2297": "KT-0805G",
    "C353386": "SMBJ16A",
    "C113974": "SMBJ5.0A",
    "1001-011-01101": "1001-011-01101",
}

bom = HERE / "06_build" / "fab" / "bom_jlc.csv"
# parts sourced outside JLC: BOM line stays uncoded, ordered/hand-soldered separately
HAND_SOLDER = {"1001-011-01101"}

rows = list(csv.DictReader(open(bom)))
missing = []
for r in rows:
    mpn = MAP.get(r["Comment"])
    if not mpn:
        missing.append(f"unmapped BOM line: {r['Comment']}")
        continue
    y = HERE / "02_parts" / mpn / "part.yaml"
    if not y.exists():
        missing.append(f"{mpn}: no 02_parts/ entry")
        continue
    src = yaml.safe_load(open(y)).get("sourcing", {})
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
