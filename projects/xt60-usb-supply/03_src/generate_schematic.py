#!/usr/bin/env python3
"""Generate 04_kicad/xt60-usb-supply.kicad_sch from the design table below.

Single source of truth for the electrical design. Connectivity is by
global labels (see lib/schwriter.py). Pin numbers are PHYSICAL PADS
resolved from 02_parts/<MPN>/part.yaml by function name — a missing part
file, missing function, or polarity mismatch is a HARD ERROR (03_src
contract rules 1/4/5).

Run with /usr/bin/python3. Never writes .kicad_pro.
"""
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from schwriter import Part, Schematic, netmap  # noqa: E402

PROJ = Path(__file__).resolve().parent.parent
PARTS_DIR = PROJ / "02_parts"
OUT = PROJ / "04_kicad" / "xt60-usb-supply.kicad_sch"

VENDOR_LIB = "xt60_usb_supply"  # 03_src/lib/xt60_usb_supply.pretty


def load_part_yaml(mpn):
    p = PARTS_DIR / mpn / "part.yaml"
    if not p.exists():
        raise SystemExit(f"ERROR: 02_parts/{mpn}/part.yaml missing (contract: extract before use)")
    d = yaml.safe_load(p.read_text())
    if d.get("mpn") != mpn:
        raise SystemExit(f"ERROR: {p} mpn field != directory name")
    return d


def pins_by_function(mpn):
    """{function_name_upper: pad_str} from part.yaml pins."""
    d = load_part_yaml(mpn)
    out = {}
    for pad, v in (d.get("pins") or {}).items():
        name = v["name"] if isinstance(v, dict) else str(v)
        out.setdefault(str(name).upper(), str(pad))
    if not out:
        raise SystemExit(f"ERROR: {mpn} part.yaml has no pins")
    return out


def conn_by_function(mpn, func_to_net):
    """Resolve {function: net} -> ordered {pad: {name, net}} via part.yaml."""
    fmap = pins_by_function(mpn)
    d = load_part_yaml(mpn)
    pads = {}
    used = set()
    for func, net in func_to_net.items():
        key = func.upper()
        if key not in fmap:
            raise SystemExit(
                f"ERROR: {mpn}: function {func!r} not in part.yaml pins "
                f"(available: {sorted(fmap)})")
        pads[fmap[key]] = {"name": func, "net": net}
        used.add(key)
    # every part.yaml pin must be addressed (no silently floating pins)
    for pad, v in (d.get("pins") or {}).items():
        name = (v["name"] if isinstance(v, dict) else str(v)).upper()
        if str(pad) not in pads:
            raise SystemExit(
                f"ERROR: {mpn}: part.yaml pin {pad} ({name}) not wired by the "
                f"design table — wire it or give it an explicit NC net")
    return pads


def two_pin(net1, net2, names=("1", "2")):
    return {"1": {"name": names[0], "net": net1},
            "2": {"name": names[1], "net": net2}}


def build():
    s = Schematic(title="xt60-usb-supply")

    # ---------------- Input & protection ----------------
    sec = "Input + protection"
    s.add_part(Part("J1", "XT60PW-M",
                    "Connector_AMASS:AMASS_XT60PW-M_1x02_P7.20mm_Horizontal",
                    conn_by_function("XT60PW-M", {"+": "VBAT_RAW", "-": "GND"})),
               section=sec)
    s.add_part(Part("F1", "15A", "Fuse:Fuse_Littelfuse-NANO2-451_453",
                    two_pin("VBAT_RAW", "VBAT_F")), section=sec)
    s.add_part(Part("Q1", "AOD4185", "Package_TO_SOT_SMD:TO-252-2",
                    conn_by_function("AOD4185",
                                     {"G": "PFET_G", "D": "VBAT_F", "S": "VBAT_P"})),
               section=sec)
    s.add_part(Part("R1", "100k", "Resistor_SMD:R_0603_1608Metric",
                    two_pin("PFET_G", "GND")), section=sec)
    s.add_part(Part("D1", "SMBJ15A", "Diode_SMD:D_SMB",
                    conn_by_function("SMBJ15A", {"K": "VBAT_P", "A": "GND"})),
               section=sec)
    for ref in ("CB1", "CB2"):
        s.add_part(Part(ref, "100uF 25V polymer",
                        f"{VENDOR_LIB}:CAP-SMD_BD6.3-L6.6-W6.6-LS7.3-FD",
                        conn_by_function("MA25V101M06600600601",
                                         {"+": "VBAT_P", "-": "GND"})),
                   section=sec)
    s.add_part(Part("LED1", "red", "LED_SMD:LED_0805_2012Metric",
                    conn_by_function("NCD0805R1", {"K": "GND", "A": "LED1_A"})),
               section=sec)
    s.add_part(Part("R2", "1k", "Resistor_SMD:R_0603_1608Metric",
                    two_pin("VBAT_P", "LED1_A")), section=sec)

    # ---------------- Buck rails ----------------
    for rail, U, L, lval, ilmt_net, cin, cout, rf, cvcc, cbs, sw, v5, fb in (
        ("A", "U1", "L1", "1.5uH", "NC_U1_ILMT",
         ("CIN_A1", "CIN_A2"), ("COUT_A1", "COUT_A2", "COUT_A3", "COUT_A4"),
         ("RFA1", "RFA2"), "CVCC_A", "CBS_A", "SW_A", "5V_A", "FB_A"),
        ("C", "U2", "L2", "2.2uH", "GND",
         ("CIN_C1", "CIN_C2"), ("COUT_C1", "COUT_C2", "COUT_C3", "COUT_C4"),
         ("RFC1", "RFC2"), "CVCC_C", "CBS_C", "SW_C", "5V_C", "FB_C"),
    ):
        sec = f"Buck {rail} (5V {'8A' if rail == 'A' else '6A'})"
        vcc_net = f"VCC_{rail}"
        bst_net = f"BST_{rail}"
        s.add_part(Part(U, "SY8368QNC",
                        f"{VENDOR_LIB}:QFN-10_L3.0-W3.0-P0.45-TL_SILERGY",
                        conn_by_function("SY8368QNC", {
                            "IN": "VBAT_P", "LX": sw, "BS": bst_net,
                            "FB": fb, "EN": "VBAT_P", "VCC": vcc_net,
                            "PG": f"NC_{U}_PG", "ILMT": ilmt_net,
                            "GND": "GND",
                        })), section=sec)
        for ref in cin:
            s.add_part(Part(ref, "10uF 25V X7R", "Capacitor_SMD:C_1206_3216Metric",
                            two_pin("VBAT_P", "GND")), section=sec)
        s.add_part(Part(cvcc, "100nF", "Capacitor_SMD:C_0603_1608Metric",
                        two_pin(vcc_net, "GND")), section=sec)
        s.add_part(Part(cbs, "100nF", "Capacitor_SMD:C_0603_1608Metric",
                        two_pin(bst_net, sw)), section=sec)
        mpn_l = "FXL0630-1R5-M" if rail == "A" else "FXL0630-2R2-M"
        load_part_yaml(mpn_l)  # existence + facts gate
        s.add_part(Part(L, lval, f"{VENDOR_LIB}:IND-SMD_L7.0-W6.6",
                        two_pin(sw, v5)), section=sec)
        for ref in cout:
            s.add_part(Part(ref, "22uF 16V X7R", "Capacitor_SMD:C_1210_3225Metric",
                            two_pin(v5, "GND")), section=sec)
        s.add_part(Part(rf[0], "22k 1%", "Resistor_SMD:R_0603_1608Metric",
                        two_pin(v5, fb)), section=sec)
        s.add_part(Part(rf[1], "3k 1%", "Resistor_SMD:R_0603_1608Metric",
                        two_pin(fb, "GND")), section=sec)

    # ---------------- USB-A ports ----------------
    sec = "USB-A ports (BC1.2 DCP)"
    for i, (jref, uref) in enumerate((("J2", "U3"), ("J3", "U4"), ("J4", "U5")), 1):
        dcp = f"DCP{i}"
        s.add_part(Part(jref, "USB-A", f"{VENDOR_LIB}:USB-A-TH_XY-AF90-WJDG",
                        conn_by_function("XY-AF90-WJDG", {
                            "VBUS": "5V_A", "D-": dcp, "D+": dcp,
                            "GND": "GND", "SHIELD1": "GND", "SHIELD2": "GND",
                        })), section=sec)
        s.add_part(Part(uref, "USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6",
                        conn_by_function("USBLC6-2SC6", {
                            "I/O1": dcp, "GND": "GND", "I/O2": dcp,
                            "I/O2B": dcp, "VBUS": "5V_A", "I/O1B": dcp,
                        })), section=sec)

    # ---------------- USB-C port ----------------
    sec = "USB-C port (5V 6A, Rp 3A)"
    s.add_part(Part("J5", "TYPE-C-31-M-12A",
                    f"{VENDOR_LIB}:USB-C-SMD_TYPE-C-31-M-12A",
                    conn_by_function("TYPE-C-31-M-12A", {
                        "VBUS1": "5V_C", "VBUS2": "5V_C",
                        "GNDP1": "GND", "GNDP2": "GND",
                        "CC1": "CC1", "CC2": "CC2",
                        "DP1": "NC_J5_DP1", "DN1": "NC_J5_DN1",
                        "DP2": "NC_J5_DP2", "DN2": "NC_J5_DN2",
                        "SBU1": "NC_J5_SBU1", "SBU2": "NC_J5_SBU2",
                        "SHELL": "GND",
                    })), section=sec)
    s.add_part(Part("U6", "USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6",
                    conn_by_function("USBLC6-2SC6", {
                        "I/O1": "CC1", "GND": "GND", "I/O2": "CC2",
                        "I/O2B": "CC2", "VBUS": "5V_C", "I/O1B": "CC1",
                    })), section=sec)
    s.add_part(Part("R3", "10k 1%", "Resistor_SMD:R_0603_1608Metric",
                    two_pin("5V_C", "CC1")), section=sec)
    s.add_part(Part("R4", "10k 1%", "Resistor_SMD:R_0603_1608Metric",
                    two_pin("5V_C", "CC2")), section=sec)

    # ---------------- Indicators ----------------
    sec = "Indicators"
    s.add_part(Part("LED2", "green", "LED_SMD:LED_0805_2012Metric",
                    conn_by_function("KT-0805G", {"K": "GND", "A": "LED2_A"})),
               section=sec)
    s.add_part(Part("R5", "1k", "Resistor_SMD:R_0603_1608Metric",
                    two_pin("5V_A", "LED2_A")), section=sec)
    s.add_part(Part("LED3", "green", "LED_SMD:LED_0805_2012Metric",
                    conn_by_function("KT-0805G", {"K": "GND", "A": "LED3_A"})),
               section=sec)
    s.add_part(Part("R6", "1k", "Resistor_SMD:R_0603_1608Metric",
                    two_pin("5V_C", "LED3_A")), section=sec)

    return s


def polarity_audit(s):
    """Assert polarized 2-pad parts per part.yaml facts (contract rule 5)."""
    nm = netmap(s)

    def net_of(ref, pad):
        for net, nodes in nm.items():
            if (ref, pad) in nodes:
                return net
        raise SystemExit(f"ERROR polarity audit: {ref} pad {pad} not in netmap")

    checks = [
        # (ref, pad, expected_net, why)
        ("J1", pins_by_function("XT60PW-M")["-"], "GND", "XT60 '-' blade to GND"),
        ("J1", pins_by_function("XT60PW-M")["+"], "VBAT_RAW", "XT60 '+' blade to VBAT_RAW"),
        ("D1", pins_by_function("SMBJ15A")["K"], "VBAT_P", "TVS cathode to +rail"),
        ("CB1", pins_by_function("MA25V101M06600600601")["+"], "VBAT_P", "polymer + to rail"),
        ("CB2", pins_by_function("MA25V101M06600600601")["+"], "VBAT_P", "polymer + to rail"),
        ("LED1", pins_by_function("NCD0805R1")["K"], "GND", "LED cathode to GND"),
        ("LED2", pins_by_function("KT-0805G")["K"], "GND", "LED cathode to GND"),
        ("LED3", pins_by_function("KT-0805G")["K"], "GND", "LED cathode to GND"),
    ]
    for ref, pad, want, why in checks:
        got = net_of(ref, pad)
        if got != want:
            raise SystemExit(f"ERROR polarity: {ref} pad {pad} on {got}, want {want} ({why})")
    print(f"POLARITY: PASS ({len(checks)} checks)")


def main():
    s = build()
    polarity_audit(s)
    OUT.parent.mkdir(exist_ok=True)
    s.write(OUT)
    nm = netmap(s)
    print(f"SCHEMATIC: wrote {OUT.name}: {len(list(s.parts()))} parts, "
          f"{len(nm)} nets, {sum(len(v) for v in nm.values())} nodes")


if __name__ == "__main__":
    main()
