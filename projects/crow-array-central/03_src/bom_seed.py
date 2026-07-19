#!/usr/bin/env python3
"""Fill LCSC + MPN into 06_build/fab/bom_jlc.csv for crow-array-central.

Every ASSEMBLED line must resolve to an LCSC code (exit 1 otherwise). The
BOM Comment encodes value+function (e.g. "100n VDD", "49R9 P1", "1k gate 3",
"AP61102 3V3"); we resolve it in three tiers:
  1. SPECIFIC part -> keyword match -> 02_parts/<MPN>/part.yaml sourcing.lcsc
  2. PASSIVE -> value token (100n/10u/4u7/1k/49R9/...) -> PASSIVE_LCSC
     (0402 JLC basics, stock-checked at bom_seed time — jlcpcb-fab skill).
  3. HAND_SOLDER / consign -> uncoded on purpose, listed for the MANIFEST.

The XU316 (C6938291) is a 0-stock JLC extended/consign part: it stays an
ASSEMBLED line with its code (JLC consign-sources it) but is flagged in the
ORDER_README as hand-solder/consign fallback.
"""
import csv
import re
import sys
from pathlib import Path
import yaml

HERE = Path(__file__).parent.parent

# --- tier 1: specific parts (comment keyword -> 02_parts MPN dir) ----------
SPECIFIC = [
    ("XU316", "XU316-1024-TQ128-I24"),
    ("PCM1865", "PCM1865DBTR"),
    ("W25Q16", "W25Q16JVSSIQ"),
    ("NC7NZ34", "NC7NZ34K8X"),
    ("SHT40", "SHT40-AD1B-R2"),
    ("AP61102", "AP61102Z6-7"),
    # D27 SOURCING SUBSTITUTE: Toshiba TCR2LF18 C150173 is JLC stock 0 ->
    # pin-compatible TI TLV70018DDCR (SOT-23-5, 1.8V/200mA, same winding;
    # evidence in 02_parts/TLV70018DDCR/part.yaml + release pin review)
    ("TCR2LF18", "TLV70018DDCR"),
    ("XC6227", "XC6227C331PR-G"),
    # D27 SOURCING SUBSTITUTE: Epson FA-238 exact code C2650433 is JLC
    # stock 0 -> YXC X322524MOB4SI (same 3225-4P land, SAME CL 12pF,
    # tighter ppm; evidence in 02_parts/X322524MOB4SI/part.yaml + twin)
    ("FA-238", "X322524MOB4SI"),
    ("AO3401A", "AO3401A"),
    ("AO3400A", "AO3400A"),
    ("SMBJ5.0A", "SMBJ5.0A"),
    ("TPD4EUSB30", "TPD4EUSB30DQAR"),
    ("TPD2E2U06", "TPD2E2U06DRLR"),
    ("2A PTC", "SMD1812P200TF16"),           # F1 entry PTC (2A hold)
    ("PTC audio", "MINISMDC050F-2"),         # F1x audio PTC (0.5A hold)
    ("PTC beep", "MINISMDC050F-2"),          # F2x beep PTC (0.5A hold)
    ("PTC", "MINISMDC050F-2"),               # merged F11-F28 line: the JLC
                                             # exporter merges same-(LCSC,
                                             # footprint) lines and reduces
                                             # the Comment to the common
                                             # token "PTC" ("2A PTC" F1
                                             # matches its own entry first)
    ("1u0", "MWSA0402S-1R0MT"),              # L10/L11 buck inductors
]

# --- tier 3: hand-solder / consign (uncoded by design) ---------------------
# (comment keyword -> (MPN, note)); LCSC kept blank in the assembled BOM.
HAND_SOLDER = {
    "RJHSE-5384": ("RJHSE-5384", "8P8C jack, THT tabs — hand-solder (LCSC has no assy stock)"),
    "USB4105": ("USB4105-GF-A", "USB-C 16P mid-mount — hand-solder (through-hole shield tabs)"),
    "DC-005": ("DC-005C-20A", "barrel jack, THT — hand-solder"),
    "INJ IN": ("PinHeader_1x02", "2.54mm header — hand-solder"),
    "xSYS DBG": ("PinHeader_1x02", "2.54mm header — hand-solder"),
    "5V TERM DNP": ("KF128L-3.5-2P", "3.5mm terminal, DNP alternate entry — hand-solder if fitted"),
}

# --- tier 2: passives (value token -> LCSC). 0402 unless noted. -----------
# Codes are JLC basics, stock-checked with jlc_stock_check.py (--search-missing
# proposes; a human confirms V/tol/dielectric before adoption). Filled below;
# any blank -> the line fails and stock-check must resolve it.
PASSIVE_LCSC = {
    # capacitors 0402 X5R/X7R (jlc_stock_check --search-missing 2026-07-18,
    # basic-first; specs (V/dielectric) confirmed in the search comment)
    "100n": "C1525",     # 100nF 16V X7R basic
    "10u": "C15525",     # 10uF 10V X5R basic
    "4u7": "C23733",     # 4.7uF 10V X5R basic
    "1u": "C52923",      # 1uF 25V X7R basic
    "2u2": "C12530",     # 2.2uF 10V X5R basic
    "1n": "C1523",       # 1nF 50V X7R basic
    "100p": "C1546",     # 100pF 50V C0G basic
    "560p": "C107029",   # 560pF 50V (extended)
    "18p": "C1549",      # 18pF 50V C0G basic (crystal load)
    "4n7": "C1538",      # 4.7nF 50V X7R basic (beeper gate slow)
    "10n": "C15195",     # 10nF 50V X7R basic
    "22u": "C385994",    # 22uF 6.3V X5R (extended; 0V9 bulk)
    "100u": "C48970904", # C90 bulk: RYVP6.3V100UF4*5 SMD alu D4xL5.4mm (exact
                         # CP_Elec_4x5.4 land), 100uF 6.3V (5V rail = 79%
                         # derating, ok for alu bulk), stock 1795 2026-07-18
    # resistors 0402 (Uniohm 0402WGF basics where available; 1% class)
    "68k": "C137947",    # (extended)
    "15k": "C25756",     # basic
    "10k": "C25744",     # basic 0402WGF1002TCE
    "20k": "C25765",     # basic
    "4k7": "C25900",     # basic
    "680R": "C137948",   # (extended)
    "1M": "C26083",      # basic
    "5k1": "C25905",     # basic
    "220k": "C138030",   # (extended)
    "330k": "C25778",    # (extended)
    "33R": "C25105",     # basic (series term; 5% fine)
    "100k": "C25741",    # basic
    "1k": "C11702",      # basic (gate series)
    "49R9": "C25120",    # basic (audio diff term)
    # ferrite bead FB3 PLL_AVDD filter (D12): 600R@100MHz 0402 Murata BLM15
    "600R": "C76886",    # BLM15AX601SN1D (extended)
}


def value_token(comment):
    """First whitespace token of a passive comment is its value."""
    return comment.split()[0] if comment else ""


def resolve_specific(comment):
    for kw, mpn in SPECIFIC:
        if kw in comment:
            return mpn
    return None


def main():
    bom = HERE / "06_build" / "fab" / "bom_jlc.csv"
    rows = list(csv.DictReader(open(bom)))
    missing, hand = [], []
    for r in rows:
        c = r["Comment"]
        # DNP lines carry through (excluded from assembly by the exporter)
        hs = next(((mpn, note) for k, (mpn, note) in HAND_SOLDER.items() if k in c), None)
        if hs:
            mpn, note = hs
            hand.append(f"{r['Designator']} ({c}: {mpn}, {note})")
            r["LCSC"] = ""
            r["MPN"] = mpn
            continue
        mpn = resolve_specific(c)
        if mpn:
            y = HERE / "02_parts" / mpn / "part.yaml"
            if not y.exists():
                missing.append(f"{c}: no 02_parts/{mpn}")
                continue
            src = yaml.safe_load(open(y)).get("sourcing") or {}
            lcsc = src.get("lcsc")
            if not lcsc or "TBD" in str(lcsc):
                missing.append(f"{c} ({mpn}): sourcing TBD/null")
                continue
            r["LCSC"], r["MPN"] = lcsc, mpn
            continue
        # passive
        tok = value_token(c)
        lcsc = PASSIVE_LCSC.get(tok)
        if lcsc:
            r["LCSC"], r["MPN"] = lcsc, ""
        else:
            missing.append(f"passive '{c}' (token {tok!r}): no LCSC — run jlc_stock_check --search-missing")
    if missing:
        print("UNRESOLVED (%d):\n  " % len(missing) + "\n  ".join(missing))
        sys.exit(1)
    fieldnames = list(rows[0].keys())
    if "MPN" not in fieldnames:
        fieldnames.insert(fieldnames.index("LCSC"), "MPN")
    w = csv.DictWriter(open(bom, "w", newline=""), fieldnames=fieldnames)
    w.writeheader()
    w.writerows(rows)
    coded = sum(1 for r in rows if r["LCSC"])
    print(f"seeded {coded} assembled BOM lines with LCSC; {len(hand)} hand-solder uncoded:")
    for h in hand:
        print("  ", h)


if __name__ == "__main__":
    main()
