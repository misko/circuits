"""Generate kicad/usb_power_3s.kicad_sch.

Machinery and buck/FE subcircuits derive from the SPF power board generator
(verified 2026-07: pin numbers are PHYSICAL PADS checked against datasheets;
polarity conventions pad1=cathode / XT60 pad1=minus are post-fix). Circuit
per docs/ARCHITECTURE.md + docs/DETAIL_DESIGN.md; decisions in docs/decisions.
Run: python3 src/generate_schematic.py  (writes into kicad/)
"""

import uuid
from pathlib import Path

HERE = Path(__file__).parent
ROOT_UUID = str(uuid.uuid4())
PROJECT = "usb_power_3s"


def u():
    return str(uuid.uuid4())


# ------------------------------------------------------------------ symbol library
# pins: (number, name, side 'L'|'R', slot_index_from_top)
def lib_symbol(name, w, h, pins, ref="U"):
    x0, y0 = -w / 2, -h / 2
    out = [f'    (symbol "pwr:{name}" (in_bom yes) (on_board yes)']
    out.append(f'      (property "Reference" "{ref}" (at 0 {h/2+1.27:.2f} 0) (effects (font (size 1.27 1.27))))')
    out.append(f'      (property "Value" "{name}" (at 0 {-h/2-1.27:.2f} 0) (effects (font (size 1.27 1.27))))')
    out.append(f'      (symbol "{name}_0_1"')
    out.append(f'        (rectangle (start {x0:.2f} {y0:.2f}) (end {w/2:.2f} {h/2:.2f})'
               f' (stroke (width 0.254) (type default)) (fill (type background)))')
    out.append("      )")
    out.append(f'      (symbol "{name}_1_1"')
    for num, pname, side, slot in pins:
        y = h / 2 - 2.54 * (slot + 1)
        if side == "L":
            px, ang = x0 - 2.54, 0
        else:
            px, ang = w / 2 + 2.54, 180
        out.append(
            f'        (pin passive line (at {px:.2f} {y:.2f} {ang}) (length 2.54)'
            f' (name "{pname}" (effects (font (size 1.27 1.27))))'
            f' (number "{num}" (effects (font (size 1.27 1.27)))))'
        )
    out.append("      )")
    out.append("    )")
    return "\n".join(out), {num: (side, h / 2 - 2.54 * (slot + 1), w) for num, _, side, slot in pins}


SYMBOLS = {}
PINMAPS = {}


def defsym(name, w, h, pins, ref="U"):
    s, pm = lib_symbol(name, w, h, pins, ref)
    SYMBOLS[name] = s
    PINMAPS[name] = (pm, w, h)


defsym("XT60", 5.08, 7.62, [("1", "-", "R", 0), ("2", "+", "R", 1)], ref="J")
defsym("SCREW2", 5.08, 7.62, [("1", "1", "L", 0), ("2", "2", "L", 1)], ref="J")
defsym("HDR3", 5.08, 10.16, [(str(i), f"P{i}", "L", i - 1) for i in range(1, 4)], ref="J")
defsym("HDR8", 5.08, 22.86, [(str(i), f"P{i}", "L", i - 1) for i in range(1, 9)], ref="J")
defsym("USB_A", 7.62, 15.24,
       [("1", "VBUS", "L", 0), ("2", "D-", "L", 1), ("3", "D+", "L", 2), ("4", "GND", "L", 3),
        ("SH", "SHIELD", "L", 4)], ref="J")
defsym("HDR4", 5.08, 12.7, [(str(i), f"P{i}", "R", i - 1) for i in range(1, 5)], ref="J")
# pad names = GCT USB4105 footprint pads (16P power-only receptacle, source role)
defsym("USBC_PWR", 15.24, 33.02,
       [("A4", "VBUS", "L", 0), ("A9", "VBUS", "L", 1), ("B4", "VBUS", "L", 2), ("B9", "VBUS", "L", 3),
        ("A5", "CC1", "L", 5), ("B5", "CC2", "L", 6),
        ("A1", "GND", "L", 8), ("A12", "GND", "L", 9), ("B1", "GND", "L", 10), ("B12", "GND", "L", 11),
        ("A6", "D+", "R", 0), ("A7", "D-", "R", 1), ("B6", "D+", "R", 2), ("B7", "D-", "R", 3),
        ("A8", "SBU1", "R", 5), ("B8", "SBU2", "R", 6), ("SH", "SHIELD", "R", 9)], ref="J")
defsym("FUSE", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="F")
defsym("RES", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="R")
defsym("CAP", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="C")
defsym("IND", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="L")
defsym("TVS", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="D")
defsym("LED", 7.62, 5.08, [("1", "K", "L", 0), ("2", "A", "R", 0)], ref="D")
defsym("SHUNT", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="R")
# USBLC6-2SC6 SOT-23-6 (ST): 1 I/O1, 2 GND, 3 I/O2, 4 I/O2', 5 VBUS, 6 I/O1'
defsym("USBLC6", 10.16, 17.78,
       [("1", "I/O1", "L", 0), ("3", "I/O2", "L", 2), ("2", "GND", "L", 5),
        ("6", "I/O1'", "R", 0), ("4", "I/O2'", "R", 2), ("5", "VBUS", "R", 5)], ref="D")
# CSD18543Q3A SON 3.3x3.3 (SLPS432): 1-3 = S, 4 = G, 5-8 = D (thermal pad = D)
defsym("NFET_SON", 10.16, 17.78,
       [("4", "G", "L", 2), ("2", "S", "L", 4), ("3", "S", "L", 5),
        ("5", "D", "R", 0),
        ("1", "S", "R", 5)], ref="Q")
# TPS7A16 DGN (SBVS171F): 1 OUT, 2 FB/DNC(float!), 3 PG, 4 GND, 5 EN, 6 NC, 7 DELAY, 8 IN, pad 9
defsym("TPS7A16", 12.7, 17.78,
       [("8", "IN", "L", 0), ("5", "EN", "L", 2), ("4", "GND", "L", 4), ("9", "PAD", "L", 5),
        ("1", "OUT", "R", 0), ("3", "PG", "R", 2), ("7", "DELAY", "R", 3),
        ("2", "FB/DNC", "R", 4), ("6", "NC", "R", 5)], ref="U")
# AP2112 SOT-25 (DS39724): 1 VIN, 2 GND, 3 EN, 4 NC, 5 VOUT
defsym("AP2112", 10.16, 12.7,
       [("1", "VIN", "L", 0), ("3", "EN", "L", 1), ("2", "GND", "L", 3),
        ("5", "VOUT", "R", 0), ("4", "NC", "R", 2)], ref="U")
# LM74800-Q1 WSON-12 (SNOSD95C table 6-1) — already physical
defsym("LM74800", 17.78, 33.02,
       [("1", "DGATE", "L", 0), ("2", "A", "L", 2), ("3", "VSNS", "L", 4), ("4", "SW", "L", 6),
        ("5", "OV", "L", 8), ("6", "EN_UVLO", "L", 10), ("7", "GND", "L", 11),
        ("8", "HGATE", "R", 0), ("9", "OUT", "R", 2), ("10", "VS", "R", 4),
        ("11", "CAP", "R", 6), ("12", "C", "R", 8)], ref="U")
# LM5145 VQFN-20 RGY (SNVSAI4 fig 6-1): physical pads; EP = pad 21 -> GND
defsym("LM5145", 17.78, 40.64,
       [("20", "VIN", "L", 0), ("1", "EN", "L", 2), ("2", "RT", "L", 4), ("3", "SS", "L", 6),
        ("11", "ILIM", "L", 8), ("8", "SYNCIN", "L", 10), ("6", "AGND", "L", 12),
        ("12", "PGND", "L", 13), ("21", "EP", "L", 14),
        ("14", "VCC", "R", 0), ("17", "BST", "R", 2), ("18", "HO", "R", 4), ("19", "SW", "R", 6),
        ("13", "LO", "R", 8), ("5", "FB", "R", 10), ("4", "COMP", "R", 12), ("10", "PGOOD", "R", 14),
        ("7", "SYNCOUT", "R", 1), ("9", "NC", "R", 3), ("15", "NC", "R", 5), ("16", "NC", "R", 7)],
       ref="U")
# TPS2557 DRB VSON-8 (SLVS931B): 1 GND, 2-3 IN, 4 EN(hi), 5 ILIM, 6-7 OUT, 8 FAULT, 9 PAD->GND
defsym("TPS2557", 12.7, 22.86,
       [("2", "IN", "L", 0), ("3", "IN", "L", 1), ("4", "EN", "L", 3),
        ("1", "GND", "L", 6), ("9", "PAD", "L", 7),
        ("6", "OUT", "R", 0), ("7", "OUT", "R", 1), ("8", "FAULT", "R", 3),
        ("5", "ILIM", "R", 5)], ref="U")
# TPS2553 DBV (SLVS841): 1 IN, 2 GND, 3 EN, 4 FAULT, 5 ILIM, 6 OUT
defsym("TPS2553", 12.7, 15.24,
       [("1", "IN", "L", 0), ("3", "EN", "L", 2), ("2", "GND", "L", 4),
        ("6", "OUT", "R", 0), ("4", "FAULT", "R", 2), ("5", "ILIM", "R", 4)], ref="U")
# INA226 VSSOP-10 (SBOS547): 1 A1, 2 A0, 3 ALERT, 4 SDA, 5 SCL, 6 VS, 7 GND, 8 VBUS, 9 IN-, 10 IN+
defsym("INA226", 15.24, 27.94,
       [("6", "VS", "L", 0), ("10", "IN+", "L", 2), ("9", "IN-", "L", 3), ("8", "VBUS", "L", 4),
        ("1", "A1", "L", 6), ("2", "A0", "L", 7), ("7", "GND", "L", 9),
        ("4", "SDA", "R", 0), ("5", "SCL", "R", 1), ("3", "ALERT", "R", 3)], ref="U")
# ATtiny816 SOIC-20 (DS40001913A table 5-1, SOIC column). Package changed from
# VQFN-20 0.4mm 2026-07-14: QFN escape saturation made the last 4-5 airlines
# unroutable at any legal geometry; 1.27mm pitch removes the problem. Same
# ports, so firmware is unchanged. Mapping: QFN k -> SOIC k-3 (k=4..20),
# QFN 1/2/3 -> SOIC 18/19/20, QFN EP(21) dropped (no EP on SOIC).
defsym("ATTINY816", 40.64, 53.34,
       [("1", "VDD", "L", 0), ("20", "GND", "L", 18),
        ("16", "PA0/UPDI", "L", 2), ("2", "PA4/VIN_SENSE", "L", 4), ("4", "PA6/V5A_SENSE", "L", 6),
        ("5", "PA7/NTC", "L", 8), ("3", "PA5/FAULT_USB", "L", 10), ("9", "PB2/SW_SENSE", "L", 12),
        ("15", "PC3/SHDN_ACK", "L", 14), ("12", "PC0/PGOOD_A", "L", 16),
        ("7", "PB4/FE_EN", "R", 0), ("6", "PB5/BUCKA_EN", "R", 2), ("14", "PC2/LOW_BATT", "R", 4),
        ("8", "PB3/AUX_CTL", "R", 6), ("10", "PB1/SDA", "R", 8), ("11", "PB0/SCL", "R", 10),
        ("17", "PA1/USB_EN1", "R", 12), ("18", "PA2/USB_EN2", "R", 14), ("19", "PA3/LED", "R", 16),
        ("13", "PC1/PGOOD_B", "R", 18)],
       ref="U")

# ------------------------------------------------------------------ footprints
# default by symbol type; per-ref overrides below (P3, see ../FOOTPRINTS.md + BOM.md)
SYM_FP = {
    "RES": "Resistor_SMD:R_0402_1005Metric",
    "CAP": "Capacitor_SMD:C_0402_1005Metric",
    "TVS": "Diode_SMD:D_SMB",
    "LED": "LED_SMD:LED_0805_2012Metric",
    "SHUNT": "Resistor_SMD:R_2512_6332Metric",
    "FUSE": "usb_power_3s:FuseHolder_ATO_FLR_EdgeTrim",
    "XT60": "usb_power_3s:XT60PW-M_EdgeTrim",
    "SCREW2": "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2_1x02_P5.00mm_Horizontal",
    "HDR3": "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
    "HDR4": "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
    "HDR8": "Connector_JST:JST_GH_SM08B-GHS-TB_1x08-1MP_P1.25mm_Horizontal",
    "USB_A": "Connector_USB:USB_A_CNCTech_1001-011-01101_Horizontal",
    "USBC_PWR": "Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal",
    "NFET_SON": "Package_SON:VSON-8_3.3x3.3mm_P0.65mm_NexFET",
    "TPS7A16": "Package_SO:MSOP-8-1EP_3x3mm_P0.65mm_EP1.68x1.88mm",
    "AP2112": "Package_TO_SOT_SMD:SOT-23-5",
    "LM74800": "usb_power_3s:WSON-12_3x3_P0.5_LM74800DRR",
    "LM5145": "usb_power_3s:VQFN-20_3.5x4.5_P0.5_LM5145RGY",
    "TPS2553": "Package_TO_SOT_SMD:SOT-23-6",
    "TPS2557": "Package_SON:VSON-8-1EP_3x3mm_P0.65mm_EP1.65x2.4mm",
    "INA226": "Package_SO:VSSOP-10_3x3mm_P0.5mm",
    "ATTINY816": "Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm",
}
REF_FP = {
    # capacitor size exceptions
    "CA2": "Capacitor_SMD:C_0603_1608Metric", "CB2": "Capacitor_SMD:C_0603_1608Metric",
    **{f"C{s}5{i}": "Capacitor_SMD:C_1210_3225Metric" for s in "AB" for i in "123"},
    **{f"C{s}6{i}": "Capacitor_SMD:C_1210_3225Metric" for s in "AB" for i in "1234"},
    **{f"C{s}11{i}": "Capacitor_SMD:C_1206_3216Metric" for s in "AB" for i in "12"},
    "CA7": "Capacitor_SMD:CP_Elec_6.3x5.9", "CB7": "Capacitor_SMD:CP_Elec_6.3x5.9",
    "CE1": "Capacitor_SMD:CP_Elec_8x10",
    "C5": "Capacitor_SMD:C_0603_1608Metric", "C7": "Capacitor_SMD:C_0603_1608Metric",
    "C9": "Capacitor_SMD:C_0603_1608Metric", "C16": "Capacitor_SMD:C_0603_1608Metric",
    "D5": "Diode_SMD:D_SOD-123",
    "F2": "Fuse:Fuse_1812_4532Metric",
    # magnetics
    "LA1": "Inductor_SMD:L_Sunlord_MWSA1005S", "LB1": "Inductor_SMD:L_Sunlord_MWSA1005S",
    "L2": "Inductor_SMD:L_Chilisin_BMRx00060630", "L4": "Inductor_SMD:L_Chilisin_BMRx00060630",
    # USBLC6-2 ESD arrays are SOT-23-6, not SMB
    "D2": "Diode_SMD:D_SMB", "D3": "Diode_SMD:D_SMB",
    "D8": "Package_TO_SOT_SMD:SOT-23-6",
    # JST-GH per BOM (symbols are generic 2-pin)
    "J2": "Connector_JST:JST_GH_BM02B-GHS-TBT_1x02-1MP_P1.25mm_Vertical",
    "J8": "Connector_JST:JST_GH_BM02B-GHS-TBT_1x02-1MP_P1.25mm_Vertical",
    "J11": "Connector_JST:JST_GH_BM03B-GHS-TBT_1x03-1MP_P1.25mm_Vertical",
    # inboard DNP pigtail header per BOM §I (was XT30PW-M pre-3-port redesign)
    "J12": "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
}

# ------------------------------------------------------------------ instances
BODY = []
LABELS = []


# --- structure aids (v4): pin endpoint registry, dashed link lines, section
# boxes. Links are GRAPHIC polylines (never wires): connectivity stays 100%
# on the global labels, and link() asserts both endpoints already share a
# net, so a wrong link is a build error instead of a netlist change.
PIN_NET = {}    # (ref, pin) -> net
PIN_POS = {}    # (ref, pin) -> (x, y) endpoint at the symbol body edge
LINKS = []
LINKED = set()  # normalized pairs, for auto-link dedupe
SECTIONS = []   # [title, x0, y0, x1, y1]


def section(title, x, y):
    SECTIONS.append([title, x, y - 2, x + 1.9 * len(title), y + 1])
    BODY.append(f'  (text "{title}" (at {x:.2f} {y:.2f} 0)'
                f' (effects (font (size 2.0 2.0) bold) (justify left)) (uuid "{u()}"))')


def _grow_section(x0, y0, x1, y1):
    if not SECTIONS:
        return
    s = SECTIONS[-1]
    s[1], s[2] = min(s[1], x0), min(s[2], y0)
    s[3], s[4] = max(s[3], x1), max(s[4], y1)


def link(refA, pinA, refB, pinB):
    """Dashed guide line between two same-net pins (validated).

    Side-aware routing so lines never cut through symbol bodies: vertical
    legs run in an outward lane past each pin's exit side (fresh-eyes review
    found body-crossing L-routes unreadable)."""
    a, b = (refA, pinA), (refB, pinB)
    assert a in PIN_NET and b in PIN_NET, f"link: unknown pin {a} / {b}"
    assert PIN_NET[a] == PIN_NET[b], \
        f"link {a}<->{b}: nets differ ({PIN_NET[a]} vs {PIN_NET[b]})"
    (ax, ay, sa), (bx, by, sb) = PIN_POS[a], PIN_POS[b]
    LANE = 8.5  # beyond the 2.54 label anchor; dashes under text are OK
    if abs(ay - by) < 0.05 and (sa == "R") == (ax < bx):
        pts = [(ax, ay), (bx, by)]                     # facing, level: straight
    elif sa == "R" and sb == "L" and ax < bx - 1:
        mid = (ax + bx) / 2                            # facing gap: H-V-H
        pts = [(ax, ay), (mid, ay), (mid, by), (bx, by)]
    elif sa == "L" and sb == "R" and bx < ax - 1:
        mid = (ax + bx) / 2
        pts = [(ax, ay), (mid, ay), (mid, by), (bx, by)]
    else:                                              # outward lane on A's side
        lane = ax + LANE if sa == "R" else ax - LANE
        pts = [(ax, ay), (lane, ay), (lane, by), (bx, by)]
    LINKED.add(frozenset((a, b)))
    xy = " ".join(f"(xy {px:.2f} {py:.2f})" for px, py in pts)
    LINKS.append(
        f'  (polyline (pts {xy}) (stroke (width 0.2) (type dash)'
        f' (color 30 90 170 0.85)) (uuid "{u()}"))')


def place(sym, ref, value, x, y, nets):
    """nets: {pin_number: net_name or None}"""
    pm, w, h = PINMAPS[sym]
    _grow_section(x - w / 2 - 14, y - h / 2 - 3.2, x + w / 2 + 14, y + h / 2 + 3.2)
    # ref above / value below, clear of the body (fixed +-14 collided on small parts)
    ry, vy = y - h / 2 - 1.6, y + h / 2 + 1.6
    fp = REF_FP.get(ref, SYM_FP.get(sym, ""))
    BODY.append(
        f'  (symbol (lib_id "pwr:{sym}") (at {x:.2f} {y:.2f} 0) (unit 1)'
        f' (in_bom yes) (on_board yes) (dnp no) (uuid "{u()}")\n'
        f'    (property "Reference" "{ref}" (at {x:.2f} {ry:.2f} 0) (effects (font (size 1.27 1.27))))\n'
        f'    (property "Value" "{value}" (at {x:.2f} {vy:.2f} 0) (effects (font (size 1.27 1.27))))\n'
        f'    (property "Footprint" "{fp}" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))\n'
        + "\n".join(f'    (pin "{n}" (uuid "{u()}"))' for n in pm)
        + f'\n    (instances (project "{PROJECT}" (path "/{ROOT_UUID}" (reference "{ref}") (unit 1))))\n  )'
    )
    for pin_num, net in nets.items():
        if net is None:
            continue
        side, py, _ = pm[pin_num]
        if side == "L":
            lx, ang, just = x - _ / 2 - 2.54, 180, "right"
        else:
            lx, ang, just = x + _ / 2 + 2.54, 0, "left"
        PIN_NET[(ref, pin_num)] = net
        PIN_POS[(ref, pin_num)] = (x - _ / 2 if side == "L" else x + _ / 2, y - py, side)
        LABELS.append(
            f'  (global_label "{net}" (shape passive) (at {lx:.2f} {y - py:.2f} {ang})'
            f' (fields_autoplaced) (effects (font (size 1.27 1.27)) (justify {just})) (uuid "{u()}"))'
        )


def text(s, x, y, size=2.0):
    BODY.append(f'  (text "{s}" (at {x:.2f} {y:.2f} 0)'
                f' (effects (font (size {size} {size}) bold) (justify left)) (uuid "{u()}"))')


def fet(ref, value, x, y, g, d, s):
    """CSD18543Q3A: all 8 physical pins netted (1-3 S, 4 G, 5-8 D)."""
    place("NFET_SON", ref, value, x, y,
          {"4": g, "5": d, "1": s, "2": s, "3": s})


def buck_stage(suffix, uref, x0, y0, rilim, cilim, en_net, vout, rfb2, pgood_net=None):
    """Fully-expanded LM5145 stage (values: P1_DETAIL_DESIGN.md section 2).
    Review fixes: bulk caps are individual physical instances (3x Cin, 4x Cout);
    RILIM sized for worst-case IRDSON 180uA x RDS(on)hot-max 9.9-11 mOhm."""
    S = suffix
    place("LM5145", uref, f"LM5145 rail {S}", x0, y0,
          {"20": "VSW", "1": en_net, "2": f"RT_{S}", "3": f"SS_{S}", "11": f"ILIM_{S}",
           "8": "GND", "6": "GND", "12": "GND", "21": "GND",
           "14": f"VCC_{S}", "17": f"BST_{S}", "18": f"HO_{S}", "19": f"SW_{S}",
           "13": f"LO_{S}", "5": f"FB_{S}", "4": f"COMP_{S}",
           "10": pgood_net or f"PGOOD_{S}",
           "7": None, "9": None, "15": None, "16": None})
    # frequency / soft-start / bias (10 mm pitch keeps ref/value text clear)
    place("RES", f"R{S}1", "16k5 RT (606kHz)", x0 - 45, y0 - 15, {"1": f"RT_{S}", "2": "GND"})
    place("CAP", f"C{S}1", "47n SS (4ms)", x0 - 45, y0 - 5, {"1": f"SS_{S}", "2": "GND"})
    place("CAP", f"C{S}2", "2u2 VCC", x0 - 45, y0 + 5, {"1": f"VCC_{S}", "2": "GND"})
    place("CAP", f"C{S}3", "100n BST", x0 - 45, y0 + 15, {"1": f"BST_{S}", "2": f"SW_{S}"})
    place("RES", f"R{S}2", rilim, x0 - 45, y0 + 25, {"1": f"ILIM_{S}", "2": f"SW_{S}"})
    place("CAP", f"C{S}4", cilim, x0 - 45, y0 + 35, {"1": f"ILIM_{S}", "2": "GND"})
    # power FETs (physical 8-pin SON)
    fet(f"Q{S}1", "CSD18543Q3A HS", x0 + 35, y0 - 20, f"HO_{S}", "VSW", f"SW_{S}")
    fet(f"Q{S}2", "CSD18543Q3A LS", x0 + 35, y0 + 4, f"LO_{S}", f"SW_{S}", "GND")
    # LC — every physical capacitor is its own instance (review BLOCKER fix)
    place("IND", f"L{S}1", "MWSA1005S-3R3 16A", x0 + 35, y0 + 22, {"1": f"SW_{S}", "2": vout})
    for i in range(3):
        place("CAP", f"C{S}5{i+1}", "10u 50V X7R", x0 - 20, y0 + 24 + 10 * i, {"1": "VSW", "2": "GND"})
    for i in range(4):
        place("CAP", f"C{S}6{i+1}", "47u 10V X7R", x0 + 35, y0 + 30 + 10 * i, {"1": vout, "2": "GND"})
    place("CAP", f"C{S}7", "220u poly 25mR", x0 + 35, y0 + 72, {"1": vout, "2": "GND"})
    # feedback + type-III compensation (sense point = the rail the load sees)
    place("RES", f"R{S}3", "20k RFB1", x0 + 65, y0 - 15, {"1": vout, "2": f"FB_{S}"})
    place("RES", f"R{S}4", rfb2, x0 + 65, y0 - 5, {"1": f"FB_{S}", "2": "GND"})
    place("RES", f"R{S}5", "13k RC1", x0 + 65, y0 + 5, {"1": f"COMP_{S}", "2": f"CX_{S}"})
    place("CAP", f"C{S}8", "8n2 CC1", x0 + 65, y0 + 15, {"1": f"CX_{S}", "2": f"FB_{S}"})
    place("CAP", f"C{S}9", "39p CC2", x0 + 65, y0 + 25, {"1": f"COMP_{S}", "2": f"FB_{S}"})
    place("CAP", f"C{S}10", "1n2 CC3", x0 + 65, y0 + 35, {"1": vout, "2": f"CY_{S}"})
    place("RES", f"R{S}6", "4k64 RC2", x0 + 65, y0 + 45, {"1": f"CY_{S}", "2": f"FB_{S}"})


# ═══════════════════ usb-power-3s circuit ═══════════════════
# Purge SPF per-ref footprint overrides that would collide with our refs
for _k in ("J2","J8","J11","J12","J13","J14","J9","J10","J7","J6","J3","J4","J5",
           "D5","F2","C5","C7","C9","C16"):
    REF_FP.pop(_k, None)
REF_FP.update({
    "C16": "Capacitor_SMD:C_0603_1608Metric",   # 2u2 EN delay
    "C30": "Capacitor_SMD:C_1206_3216Metric", "C31": "Capacitor_SMD:C_1206_3216Metric",
    "C32": "Capacitor_SMD:C_1206_3216Metric", "C33": "Capacitor_SMD:C_1206_3216Metric",
    "C34": "Capacitor_SMD:C_1206_3216Metric",   # 22u port caps
})

# --- section 1: input ---
section("1. INPUT + PROTECTION (3S LiPo 9.0-12.6V, <=9A)", 20, 20)
place("XT60", "J1", "XT60_BATT", 30, 40, {"1": "GND", "2": "VBATT_RAW"})  # pad1 = "-" blade
place("FUSE", "F1", "15A ATO", 60, 40, {"1": "VBATT_RAW", "2": "VBATT_F"})
place("TVS", "D1", "SMBJ16A", 60, 55, {"1": "VBATT_F", "2": "GND"})       # pad1 = cathode -> rail
place("CAP", "C15", "100n at U1.A", 90, 55, {"1": "VBATT_F", "2": "GND"})
place("CAP", "CE1", "100u hybrid 35V", 120, 40, {"1": "VSW", "2": "GND"})

# --- section 2: front-end ---
section("2. FRONT-END: LM74800-Q1 + 2x CSD18543Q3A b2b (rev-pol; UVLO 9.33V on / OV 15.25V)", 20, 72)
place("LM74800", "U1", "LM74800-Q1", 60, 105,
      {"1": "DG_FE", "2": "VBATT_F", "3": "VBATT_F", "4": "FE_LAD", "5": "FE_OV",
       "6": "FE_EN", "7": "GND", "8": "HG_FE", "9": "VSW", "10": "FE_MID",
       "11": "FE_CAP", "12": "FE_MID"})
fet("Q1", "CSD18543Q3A diode", 105, 92, "DG_FE", "FE_MID", "VBATT_F")
fet("Q2", "CSD18543Q3A switch", 105, 116, "HG_FE", "FE_MID", "VSW")
place("CAP", "C1", "100n CAP-VS", 105, 135, {"1": "FE_CAP", "2": "FE_MID"})
place("CAP", "C2", "100n VS-GND", 105, 145, {"1": "FE_MID", "2": "GND"})
place("CAP", "C3", "47n HGATE dv/dt", 140, 92, {"1": "HG_FE", "2": "VSW"})
place("RES", "R1", "887k ladder-top", 20, 105, {"1": "FE_LAD", "2": "FE_EN"})
place("RES", "R2", "52k3 ladder-mid (UVLO 9.33V)", 20, 117, {"1": "FE_EN", "2": "FE_OV"})
place("RES", "R3", "82k5 ladder-bot (OV 15.25V)", 20, 129, {"1": "FE_OV", "2": "GND"})
place("CAP", "C16", "2u2 EN delay", 20, 141, {"1": "FE_EN", "2": "GND"})

# --- section 3: buck A -> USB-C rail ---
section("3. BUCK A  5.08V / 6A -> 5V_C (USB-C)   [math: docs/DETAIL_DESIGN.md]", 175, 20)
place("RES", "R4", "100k EN-A hi (8.5V on)", 200, 30, {"1": "VSW", "2": "EN_A"})
place("RES", "R5", "16k5 EN-A lo (7.5V off)", 200, 42, {"1": "EN_A", "2": "GND"})
buck_stage("A", "U2", 255, 45, "348R RILIM (wc 6.3A)", "18p CILIM", "EN_A", "5V_C",
           "3k74 RFB2 (5.08V)", "PGOODA_RAW")
place("RES", "R21", "20k PGOOD_A pu (5V_C)", 200, 54, {"1": "5V_C", "2": "PGOODA_RAW"})
place("RES", "R33", "20k seq div hi", 200, 66, {"1": "PGOODA_RAW", "2": "PGOOD_A"})
place("RES", "R34", "16k5 seq div lo", 200, 78, {"1": "PGOOD_A", "2": "GND"})

# --- section 4: buck B -> USB-A rail (sequenced after A) ---
section("4. BUCK B  5.08V / 7.5A -> 5V_A (3x USB-A)   EN = PGOOD_A", 175, 155)
buck_stage("B", "U3", 255, 185, "432R RILIM (wc 7.8A)", "18p CILIM", "PGOOD_A", "5V_A",
           "3k74 RFB2 (5.08V)")

# --- section 5: USB-A ports, DCP-strapped, 2.5A limited ---
section("5. USB-A x3: TPS2557 ILIM 2.51A each, D+/D- DCP short (ADR-0003)", 20, 170)
for _i, (_u, _j, _rl, _vb, _dcp, _cin, _cout) in enumerate([
        ("U4", "J2", "R16", "VBUS1", "DCP1", "C20", "C30"),
        ("U5", "J3", "R17", "VBUS2", "DCP2", "C21", "C31"),
        ("U6", "J4", "R18", "VBUS3", "DCP3", "C22", "C32")]):
    _y = 190 + _i * 42
    place("TPS2557", _u, "TPS2557 2.5A", 45, _y,
          {"2": "5V_A", "3": "5V_A", "4": "5V_A", "1": "GND", "9": "GND",
           "6": _vb, "7": _vb, "8": None, "5": f"ILIM{_i+1}"})
    place("RES", _rl, "24k3 RILIM (2.51A)", 80, _y - 10, {"1": f"ILIM{_i+1}", "2": "GND"})
    place("CAP", _cin, "100n sw in", 80, _y, {"1": "5V_A", "2": "GND"})
    place("CAP", _cout, "22u port", 80, _y + 10, {"1": _vb, "2": "GND"})
    place("USB_A", _j, "USB-A 2.5A", 120, _y, {"1": _vb, "2": _dcp, "3": _dcp, "4": "GND", "SH": "GND"})

# --- section 6: USB-C port ---
section("6. USB-C source: Rp 10k x2 = 3A advertisement, 6A copper (ADR-0002)", 20, 320)
place("USBC_PWR", "J5", "USB4105-GF-A", 55, 355,
      {"A4": "5V_C", "A9": "5V_C", "B4": "5V_C", "B9": "5V_C",
       "A5": "CC1", "B5": "CC2",
       "A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND",
       "A6": "DCPC", "A7": "DCPC", "B6": "DCPC", "B7": "DCPC",
       "A8": None, "B8": None, "SH": "GND"})
place("RES", "R19", "10k Rp CC1 (3A adv)", 105, 340, {"1": "5V_C", "2": "CC1"})
place("RES", "R20", "10k Rp CC2 (3A adv)", 105, 350, {"1": "5V_C", "2": "CC2"})
place("CAP", "C33", "22u port", 105, 362, {"1": "5V_C", "2": "GND"})
place("CAP", "C34", "22u port", 105, 372, {"1": "5V_C", "2": "GND"})

# --- section 7: rail TVS + indicators ---
section("7. RAIL CLAMPS + LEDs", 150, 320)
place("TVS", "D2", "SMBJ5.0A", 165, 340, {"1": "5V_A", "2": "GND"})   # pad1 = cathode
place("TVS", "D3", "SMBJ5.0A", 165, 352, {"1": "5V_C", "2": "GND"})
place("RES", "R22", "1k LED-A", 195, 340, {"1": "5V_A", "2": "LEDA_A"})
place("LED", "D4", "green 5V_A", 195, 350, {"1": "GND", "2": "LEDA_A"})  # pad1 = cathode
place("RES", "R23", "1k LED-C", 195, 362, {"1": "5V_C", "2": "LEDC_A"})
place("LED", "D5", "green 5V_C", 195, 372, {"1": "GND", "2": "LEDC_A"})

# ------------------------------------------------------------------ structure links
link("J1", "2", "F1", "1")
link("F1", "2", "D1", "1")
link("F1", "2", "U1", "2")
link("U1", "1", "Q1", "4")
link("U1", "8", "Q2", "4")
link("Q1", "5", "Q2", "5")
link("Q1", "1", "U1", "3")
link("U1", "11", "C1", "1")
link("U1", "4", "R1", "1")
link("R1", "2", "R2", "1")
link("R2", "2", "R3", "1")
link("R1", "2", "C16", "1")
link("R4", "2", "R5", "1")
link("R21", "2", "R33", "1")
link("R33", "2", "R34", "1")
for _S, _U in (("A", "U2"), ("B", "U3")):
    link(_U, "18", f"Q{_S}1", "4")
    link(_U, "13", f"Q{_S}2", "4")
    link(f"Q{_S}1", "1", f"Q{_S}2", "5")
    link(f"Q{_S}1", "1", f"L{_S}1", "1")
    link(f"L{_S}1", "2", f"C{_S}61", "1")
    link(f"L{_S}1", "2", f"R{_S}3", "1")
    link(f"R{_S}3", "2", f"R{_S}4", "1")
    link(f"R{_S}4", "1", _U, "5")
    link(_U, "4", f"R{_S}5", "1")
    link(f"R{_S}5", "2", f"C{_S}8", "1")
    link(f"C{_S}3", "2", f"R{_S}2", "2")
for _u, _j, _r in (("U4", "J2", "R16"), ("U5", "J3", "R17"), ("U6", "J4", "R18")):
    link(_u, "7", _j, "1")
    link(_u, "5", _r, "1")
link("R19", "2", "J5", "A5")
link("R20", "2", "J5", "B5")
link("R22", "2", "D4", "2")
link("R23", "2", "D5", "2")


def auto_links():
    """Derive structure links from the netlist itself (validated by the same
    same-net assertion as hand links; kicad-happy's subcircuit detection
    confirmed these classes cover its dividers/decoupling/RC findings):
    a) every 2-pin point-to-point net gets a link (series junctions, gate
       drives, port feeds) - by construction unambiguous;
    b) every rail bypass part (2-pin passive, one pin GND) links to the
       NEAREST same-net pin, visualizing which IC each decoupler serves."""
    import math
    bynet = {}
    for (ref, pin), net in PIN_NET.items():
        bynet.setdefault(net, []).append((ref, pin))
    n_auto = 0
    for net, pins in bynet.items():
        if net == "GND":
            continue
        refs = {r for r, _ in pins}
        if len(pins) == 2 and len(refs) == 2:
            (rA, pA), (rB, pB) = pins
            if frozenset(((rA, pA), (rB, pB))) not in LINKED:
                link(rA, pA, rB, pB); n_auto += 1
    for (ref, pin), net in list(PIN_NET.items()):
        if net == "GND" or ref[0] not in "RCLDF":
            continue
        mates = {PIN_NET.get((ref, o)) for o in ("1", "2")} - {None}
        if "GND" not in mates or len(bynet.get(net, [])) <= 2:
            continue
        x0, y0, _ = PIN_POS[(ref, pin)]
        best = None
        for (r2, p2) in bynet[net]:
            if r2 == ref:
                continue
            x1, y1, _s = PIN_POS[(r2, p2)]
            d = math.hypot(x1 - x0, y1 - y0)
            if best is None or d < best[0]:
                best = (d, r2, p2)
        if best and best[0] < 60 and frozenset(((ref, pin), (best[1], best[2]))) not in LINKED:
            link(ref, pin, best[1], best[2]); n_auto += 1
    print(f"auto-links: {n_auto} derived ({len(LINKED)} total links)")


auto_links()


# ------------------------------------------------------------------ emit
sch = []
sch.append('(kicad_sch (version 20230121) (generator spf_generate_schematic)')
sch.append(f'  (uuid "{ROOT_UUID}")')
sch.append('  (paper "A2")')
sch.append('  (title_block (title "usb-power-3s") (date "2026-07-16") (rev "v0.1")')
sch.append('    (comment 1 "3S LiPo -> 3x USB-A 2.5A + USB-C 6A; docs/ + ADRs in repo"))')
sch.append("  (lib_symbols")
sch.extend(SYMBOLS.values())
sch.append("  )")
sch.extend(LABELS)
sch.extend(BODY)
sch.extend(LINKS)
for title, x0, y0, x1, y1 in SECTIONS:
    # pad the box clear of the title (top) and labels; clamp inside the A2
    # frame (fresh-eyes review: borders struck titles / spilled into margin)
    x0, y0 = max(x0 - 2, 12.0), max(y0 - 4.5, 12.0)
    x1, y1 = x1 + 2, y1 + 2.5
    sch.append(f'  (rectangle (start {x0:.2f} {y0:.2f}) (end {x1:.2f} {y1:.2f})'
               f" (stroke (width 0.35) (type solid) (color 120 120 130 0.7))"
               f' (fill (type none)) (uuid "{u()}"))')
sch.append(f'  (sheet_instances (path "/" (page "1")))')
sch.append(")")
content = "\n".join(sch)
assert content.count("(") == content.count(")"), (
    content.count("("), content.count(")"))
((HERE.parent / "kicad").mkdir(exist_ok=True) or (HERE.parent / "kicad" / "usb_power_3s.kicad_sch")).write_text(content)

# NEVER overwrite an existing project file - it carries the DRC rule floors,
# netclasses and severity policy (v4.4 DRC-clean state).
if not (HERE.parent / "kicad" / "usb_power_3s.kicad_pro").exists():
    (HERE.parent / "kicad" / "usb_power_3s.kicad_pro").write_text(
    '{\n  "board": { "design_settings": {} },\n'
    '  "meta": { "filename": "usb_power_3s.kicad_pro", "version": 1 },\n'
    '  "schematic": { "legacy_lib_dir": "", "legacy_lib_list": [] }\n}\n'
)
print("wrote usb_power_3s.kicad_sch (+.kicad_pro) v3;",
      f"{len(BODY)} items, {len(LABELS)} net labels, parens balanced")
