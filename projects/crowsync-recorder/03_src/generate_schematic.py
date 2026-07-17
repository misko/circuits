"""Generate 04_kicad/crowsync_recorder.kicad_sch.

Machinery (symbols, global-label connectivity, structure links, sections)
derives from the usb-power-3s generator (verified 2026-07). Pin numbers are
PHYSICAL PADS from 02_parts/<MPN>/part.yaml (each cites its datasheet
figure). Circuit per 01_docs/ARCHITECTURE.md + DETAIL_DESIGN.md; decisions
in 01_docs/decisions/.
Run: python3 03_src/generate_schematic.py  (writes into 04_kicad/)
"""

import uuid
from pathlib import Path

HERE = Path(__file__).parent
ROOT_UUID = str(uuid.uuid4())
PROJECT = "crowsync_recorder"


def u():
    return str(uuid.uuid4())


# ------------------------------------------------------------------ symbol library
def lib_symbol(name, w, h, pins, ref="U"):
    x0, y0 = -w / 2, -h / 2
    out = [f'    (symbol "csr:{name}" (in_bom yes) (on_board yes)']
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


defsym("RES", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="R")
defsym("CAP", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="C")
defsym("FB", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="FB")
defsym("LED", 7.62, 5.08, [("1", "K", "L", 0), ("2", "A", "R", 0)], ref="D")
# GCT USB4105 16P receptacle, sink (UFP) role — pad names = footprint pads
defsym("USBC", 15.24, 33.02,
       [("A4", "VBUS", "L", 0), ("A9", "VBUS", "L", 1), ("B4", "VBUS", "L", 2), ("B9", "VBUS", "L", 3),
        ("A5", "CC1", "L", 5), ("B5", "CC2", "L", 6),
        ("A1", "GND", "L", 8), ("A12", "GND", "L", 9), ("B1", "GND", "L", 10), ("B12", "GND", "L", 11),
        ("A6", "D+", "R", 0), ("A7", "D-", "R", 1), ("B6", "D+", "R", 2), ("B7", "D-", "R", 3),
        ("A8", "SBU1", "R", 5), ("B8", "SBU2", "R", 6), ("SH", "SHIELD", "R", 9)], ref="J")
# USBLC6-2SC6 SOT-23-6 (UMW datasheet §4, p1): 1 I/O1, 2 GND, 3 I/O2, 4 I/O2, 5 VBUS, 6 I/O1
defsym("USBLC6", 10.16, 17.78,
       [("1", "I/O1", "L", 0), ("3", "I/O2", "L", 2), ("2", "GND", "L", 5),
        ("6", "I/O1'", "R", 0), ("4", "I/O2'", "R", 2), ("5", "VBUS", "R", 5)], ref="D")
# PCM2900C SSOP-28 DB (SBFS039 p6 pinout figure + Table 1) — PHYSICAL pads
defsym("PCM2900C", 20.32, 48.26,
       [("1", "D+", "L", 0), ("2", "D-", "L", 1), ("3", "VBUS", "L", 3),
        ("8", "SEL0", "L", 5), ("9", "SEL1", "L", 6),
        ("5", "HID0", "L", 8), ("6", "HID1", "L", 9), ("7", "HID2", "L", 10),
        ("12", "VINL", "L", 12), ("13", "VINR", "L", 13), ("14", "VCOM", "L", 14),
        ("4", "DGNDU", "L", 16), ("11", "AGNDC", "L", 17),
        ("21", "XTI", "R", 0), ("20", "XTO", "R", 1),
        ("27", "VDDI", "R", 3), ("23", "VCCXI", "R", 4), ("10", "VCCCI", "R", 5),
        ("19", "VCCP2I", "R", 6), ("17", "VCCP1I", "R", 7),
        ("28", "SSPND", "R", 9), ("25", "TEST1", "R", 10), ("24", "TEST0", "R", 11),
        ("15", "VOUTR", "R", 13), ("16", "VOUTL", "R", 14),
        ("26", "DGND", "R", 16), ("22", "AGNDX", "R", 17), ("18", "AGNDP", "L", 15)],
       ref="U")
# TLV9062 SOIC-8 D (SBOS839N fig 5-6 / table 5-3, p6)
defsym("TLV9062", 12.7, 22.86,
       [("3", "IN1+", "L", 0), ("2", "IN1-", "L", 2), ("5", "IN2+", "L", 4), ("6", "IN2-", "L", 6),
        ("8", "V+", "R", 0), ("1", "OUT1", "R", 2), ("7", "OUT2", "R", 4), ("4", "V-", "R", 7)],
       ref="U")
# TPS7A20 DBV SOT-23-5 (SBVS338H fig 4-4, p4): 1 IN, 2 GND, 3 EN, 4 NC, 5 OUT
defsym("TPS7A20", 10.16, 12.7,
       [("1", "IN", "L", 0), ("3", "EN", "L", 1), ("2", "GND", "L", 3),
        ("5", "OUT", "R", 0), ("4", "NC", "R", 2)], ref="U")
# YXC 3225 crystal (YSX321SL sheet): 1/3 electrodes, 2/4 GND
defsym("XTAL4", 10.16, 10.16,
       [("1", "X1", "L", 0), ("2", "G", "L", 2), ("3", "X2", "R", 0), ("4", "G", "R", 2)], ref="Y")
# JST GH headers (MP = mounting pads, tied GND)
defsym("JST3", 5.08, 12.7,
       [("1", "P1", "L", 0), ("2", "P2", "L", 1), ("3", "P3", "L", 2), ("MP", "MP", "L", 3)], ref="J")
defsym("JST2", 5.08, 10.16,
       [("1", "P1", "L", 0), ("2", "P2", "L", 1), ("MP", "MP", "L", 2)], ref="J")

# ------------------------------------------------------------------ footprints
SYM_FP = {
    "RES": "Resistor_SMD:R_0603_1608Metric",
    "CAP": "Capacitor_SMD:C_0603_1608Metric",
    "FB": "Inductor_SMD:L_0603_1608Metric",
    "LED": "LED_SMD:LED_0805_2012Metric",
    "USBC": "Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal",
    "USBLC6": "Package_TO_SOT_SMD:SOT-23-6",
    "PCM2900C": "Package_SO:SSOP-28_5.3x10.2mm_P0.65mm",
    "TLV9062": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
    "TPS7A20": "Package_TO_SOT_SMD:SOT-23-5",
    "XTAL4": "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
    "JST3": "Connector_JST:JST_GH_SM03B-GHS-TB_1x03-1MP_P1.25mm_Horizontal",
    "JST2": "Connector_JST:JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal",
}
REF_FP = {}

# ------------------------------------------------------------------ instances
BODY = []
LABELS = []
NO_CONNECTS = []
NC_PINS = set()
# Sanctioned floats (canon S4: no_connect flags EMITTED, not narrated).
# Verified against 07_releases/v1.0-2026-07-16/verification/pin_review.md and
# ORDER_README "known intentional oddities":
#  - J1 A8/B8 (SBU1/SBU2): "SBU NC" per the GCT pin table (pin_review J1 PASS)
#  - U3 pin 4: TPS7A20 NC, "NC floating per datasheet" (pin_review U3 PASS)
#  - U1 pins 5/6/7/25/15/16 (HID0-2, TEST1, VOUTR, VOUTL): "VOUTL/VOUTR/
#    TEST1/HID0-2 codec pins unconnected (datasheet-sanctioned)" (ORDER_README;
#    pin_review U1 PASS "HID NC on internal pulldowns")
SANCTIONED_FLOATS = {
    ("J1", "A8"), ("J1", "B8"),
    ("U3", "4"),
    ("U1", "5"), ("U1", "6"), ("U1", "7"),
    ("U1", "25"), ("U1", "15"), ("U1", "16"),
}
PIN_NET = {}
PIN_POS = {}
LINKS = []
LINKED = set()
SECTIONS = []


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
    """Dashed guide line between two same-net pins (asserted same-net)."""
    a, b = (refA, pinA), (refB, pinB)
    assert a in PIN_NET and b in PIN_NET, f"link: unknown pin {a} / {b}"
    assert PIN_NET[a] == PIN_NET[b], \
        f"link {a}<->{b}: nets differ ({PIN_NET[a]} vs {PIN_NET[b]})"
    (ax, ay, sa), (bx, by, sb) = PIN_POS[a], PIN_POS[b]
    LANE = 8.5
    if abs(ay - by) < 0.05 and (sa == "R") == (ax < bx):
        pts = [(ax, ay), (bx, by)]
    elif sa == "R" and sb == "L" and ax < bx - 1:
        mid = (ax + bx) / 2
        pts = [(ax, ay), (mid, ay), (mid, by), (bx, by)]
    elif sa == "L" and sb == "R" and bx < ax - 1:
        mid = (ax + bx) / 2
        pts = [(ax, ay), (mid, ay), (mid, by), (bx, by)]
    else:
        lane = ax + LANE if sa == "R" else ax - LANE
        pts = [(ax, ay), (lane, ay), (lane, by), (bx, by)]
    LINKED.add(frozenset((a, b)))
    xy = " ".join(f"(xy {px:.2f} {py:.2f})" for px, py in pts)
    LINKS.append(
        f'  (polyline (pts {xy}) (stroke (width 0.2) (type dash)'
        f' (color 30 90 170 0.85)) (uuid "{u()}"))')


def place(sym, ref, value, x, y, nets):
    pm, w, h = PINMAPS[sym]
    _grow_section(x - w / 2 - 14, y - h / 2 - 3.2, x + w / 2 + 14, y + h / 2 + 3.2)
    ry, vy = y - h / 2 - 1.6, y + h / 2 + 1.8
    vsz = 0.9 if sym in ("RES", "CAP", "FB", "LED", "XTAL4") else 1.27
    fp = REF_FP.get(ref, SYM_FP.get(sym, ""))
    BODY.append(
        f'  (symbol (lib_id "csr:{sym}") (at {x:.2f} {y:.2f} 0) (unit 1)'
        f' (in_bom yes) (on_board yes) (dnp no) (uuid "{u()}")\n'
        f'    (property "Reference" "{ref}" (at {x:.2f} {ry:.2f} 0) (effects (font (size 1.27 1.27))))\n'
        f'    (property "Value" "{value}" (at {x:.2f} {vy:.2f} 0) (effects (font (size {vsz} {vsz}))))\n'
        f'    (property "Footprint" "{fp}" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))\n'
        + "\n".join(f'    (pin "{n}" (uuid "{u()}"))' for n in pm)
        + f'\n    (instances (project "{PROJECT}" (path "/{ROOT_UUID}" (reference "{ref}") (unit 1))))\n  )'
    )
    for pin_num, net in nets.items():
        if net is None:
            # canon S4: sanctioned float -> EMIT a no_connect flag at the
            # pin endpoint (same point the global label would attach to).
            side, py, _ = pm[pin_num]
            ncx = x - _ / 2 - 2.54 if side == "L" else x + _ / 2 + 2.54
            NO_CONNECTS.append(
                f'  (no_connect (at {ncx:.2f} {y - py:.2f}) (uuid "{u()}"))')
            NC_PINS.add((ref, pin_num))
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


# ═══════════════════ crowsync-recorder circuit ═══════════════════

# --- section 1: USB entry ---
section("1. USB-C INPUT (UFP, 5V bus power)   [ADR-0001 protection]", 20, 20)
place("USBC", "J1", "USB4105-GF-A", 35, 45,
      {"A4": "VBUS_5V", "A9": "VBUS_5V", "B4": "VBUS_5V", "B9": "VBUS_5V",
       "A5": "CC1", "B5": "CC2",
       "A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND",
       "A6": "DP_C", "A7": "DM_C", "B6": "DP_C", "B7": "DM_C",
       "A8": None, "B8": None, "SH": "GND"})
place("RES", "R4", "5k1 Rd CC1 (UFP)", 65, 30, {"1": "CC1", "2": "GND"})
place("RES", "R5", "5k1 Rd CC2 (UFP)", 65, 38, {"1": "CC2", "2": "GND"})
place("USBLC6", "D1", "USBLC6-2SC6 USB", 68, 55,
      {"1": "DP_C", "6": "DP_C", "3": "DM_C", "4": "DM_C", "2": "GND", "5": "VBUS_5V"})
place("RES", "R1", "22R D+ series", 95, 47, {"1": "DP_C", "2": "DP"})
place("RES", "R2", "22R D- series", 95, 55, {"1": "DM_C", "2": "DM"})
place("RES", "R3", "1k5 D+ pullup (VDDI)", 95, 63, {"1": "DP", "2": "VDDI"})
place("CAP", "C12", "10u 5V bulk", 65, 71, {"1": "VBUS_5V", "2": "GND"})
place("CAP", "C13", "100n 5V", 65, 79, {"1": "VBUS_5V", "2": "GND"})

# --- section 2: codec ---
section("2. PCM2900C USB AUDIO CODEC (bus-powered fig-38; ADR-0002)", 130, 20)
place("PCM2900C", "U1", "PCM2900CDBR", 160, 55,
      {"1": "DP", "2": "DM", "3": "VBUS_PCM",
       "8": "VDDI", "9": "VDDI",
       "5": None, "6": None, "7": None,
       "12": "VINL", "13": "VINR", "14": "VCOM",
       "4": "GND", "11": "GND", "18": "GND",
       "21": "XTI", "20": "XTO",
       "27": "VDDI", "23": "VCCXI", "10": "VCCCI", "19": "VCCP2", "17": "VCCP1",
       "28": "SSPND", "25": None, "24": "GND",
       "15": None, "16": None,
       "26": "GND", "22": "GND"})
place("RES", "R7", "2R2 VBUS filter", 125, 30, {"1": "VBUS_5V", "2": "VBUS_PCM"})
place("CAP", "C11", "1u VBUS pin", 125, 38, {"1": "VBUS_PCM", "2": "GND"})
place("CAP", "C1", "10u VCCCI", 195, 30, {"1": "VCCCI", "2": "GND"})
place("CAP", "C2", "10u VCOM", 195, 38, {"1": "VCOM", "2": "GND"})
place("CAP", "C3", "1u VDDI", 195, 46, {"1": "VDDI", "2": "GND"})
place("CAP", "C4", "1u VCCXI", 195, 54, {"1": "VCCXI", "2": "GND"})
place("CAP", "C7", "1u VCCP2I", 195, 62, {"1": "VCCP2", "2": "GND"})
place("CAP", "C8", "1u VCCP1I", 195, 70, {"1": "VCCP1", "2": "GND"})
# suspend LED
place("RES", "R17", "1k LED SSPND", 195, 82, {"1": "SSPND", "2": "LED3_A"})
place("LED", "D3", "green ACT", 195, 90, {"1": "GND", "2": "LED3_A"})   # pad1 = cathode
place("RES", "R18", "2k2 LED 5V", 125, 46, {"1": "VBUS_5V", "2": "LED4_A"})
place("LED", "D4", "green PWR", 125, 54, {"1": "GND", "2": "LED4_A"})

# --- section 3: crystal ---
section("3. 12 MHz CRYSTAL (CL 20pF -> 33p)", 130, 105)
place("XTAL4", "Y1", "12MHz 3225 20pF", 160, 118,
      {"1": "XTI", "3": "XTO", "2": "GND", "4": "GND"})
place("RES", "R6", "1M XTI-XTO", 160, 130, {"1": "XTI", "2": "XTO"})
place("CAP", "C5", "33p XTI", 135, 118, {"1": "XTI", "2": "GND"})
place("CAP", "C6", "33p XTO", 185, 118, {"1": "XTO", "2": "GND"})

# --- section 4: analog rail ---
section("4. 3V3A RAIL (TPS7A2033, ADR-0002)", 20, 105)
place("TPS7A20", "U3", "TPS7A2033PDBVR", 45, 118,
      {"1": "VBUS_5V", "3": "VBUS_5V", "2": "GND", "5": "3V3A", "4": None})
place("CAP", "C14", "1u LDO in", 22, 130, {"1": "VBUS_5V", "2": "GND"})
place("CAP", "C15", "10u 3V3A", 45, 130, {"1": "3V3A", "2": "GND"})
place("CAP", "C16", "100n 3V3A U2", 68, 130, {"1": "3V3A", "2": "GND"})

# --- section 5: mic input + preamp ---
section("5. CH1 MIC: bias/ESD/series-R -> TLV9062A gain 4.0 (39k alt = 40x; ADR-0003)", 20, 150)
place("JST3", "J2", "JST-GH mic", 28, 165,
      {"1": "MIC", "2": "GND", "3": "GND", "MP": "GND"})
place("USBLC6", "D2", "USBLC6-2SC6 harness", 55, 172,
      {"1": "MIC", "6": "MIC", "3": "PPS", "4": "PPS", "2": "GND", "5": "3V3A"})
place("FB", "FB1", "600R@100MHz bias", 28, 185, {"1": "3V3A", "2": "MIC_BIAS_F"})
place("CAP", "C17", "10u bias res", 28, 193, {"1": "MIC_BIAS_F", "2": "GND"})
place("CAP", "C18", "100n bias", 28, 201, {"1": "MIC_BIAS_F", "2": "GND"})
place("RES", "R8", "2k2 mic bias", 55, 193, {"1": "MIC_BIAS_F", "2": "MIC"})
place("RES", "R9", "100R mic series", 82, 165, {"1": "MIC", "2": "MIC_IN"})
place("CAP", "C19", "1u mic couple", 105, 165, {"1": "MIC_IN", "2": "AMP_INP"})
place("RES", "R10", "100k bias->VCOM", 105, 175, {"1": "AMP_INP", "2": "VCOM_BUF"})
place("TLV9062", "U2", "TLV9062IDR", 135, 175,
      {"3": "AMP_INP", "2": "AMP_FB", "1": "AMP_OUT",
       "5": "VCOM", "6": "VCOM_BUF", "7": "VCOM_BUF",
       "8": "3V3A", "4": "GND"})
place("RES", "R11", "3k01 Rf (gain 4.0)", 160, 190, {"1": "AMP_OUT", "2": "AMP_FB"})
place("RES", "R12", "1k Rg", 135, 195, {"1": "AMP_FB", "2": "RG_X"})
place("CAP", "C20", "10u Cg (15.9Hz)", 135, 203, {"1": "RG_X", "2": "GND"})
place("RES", "R13", "100R amp out", 165, 165, {"1": "AMP_OUT", "2": "VINL_F"})
place("CAP", "C21", "1n RF stop", 165, 175, {"1": "VINL_F", "2": "GND"})
place("CAP", "C9", "1u VINL couple", 190, 165, {"1": "VINL_F", "2": "VINL"})

# --- section 6: PPS input ---
section("6. CH2 PPS: ESD/series-R -> 22k/10k divider (1.03Vpp) -> AC couple", 20, 220)
place("JST2", "J3", "JST-GH PPS", 28, 233, {"1": "PPS", "2": "GND", "MP": "GND"})
place("RES", "R14", "100R PPS series", 55, 230, {"1": "PPS", "2": "PPS_A"})
place("RES", "R15", "22k div top", 80, 230, {"1": "PPS_A", "2": "PPS_ATT"})
place("RES", "R16", "10k div bottom", 80, 240, {"1": "PPS_ATT", "2": "GND"})
place("CAP", "C10", "1u VINR couple", 105, 230, {"1": "PPS_ATT", "2": "VINR"})

# ------------------------------------------------------------------ structure links
link("J1", "A6", "D1", "1")
link("J1", "A7", "D1", "3")
link("D1", "6", "R1", "1")
link("D1", "4", "R2", "1")
link("R1", "2", "U1", "1")
link("R2", "2", "U1", "2")
link("R1", "2", "R3", "1")
link("R7", "2", "C11", "1")
link("R7", "2", "U1", "3")
link("U1", "21", "Y1", "1")
link("U1", "20", "Y1", "3")
link("Y1", "1", "C5", "1")
link("Y1", "3", "C6", "1")
link("U3", "5", "C15", "1")
link("U3", "5", "FB1", "1")
link("FB1", "2", "R8", "1")
link("R8", "2", "J2", "1")
link("J2", "1", "D2", "1")
link("J2", "1", "R9", "1")
link("R9", "2", "C19", "1")
link("C19", "2", "U2", "3")
link("C19", "2", "R10", "1")
link("U2", "1", "R11", "1")
link("R11", "2", "U2", "2")
link("U2", "2", "R12", "1")
link("R12", "2", "C20", "1")
link("U1", "14", "U2", "5")
link("U2", "7", "R10", "2")
link("U2", "1", "R13", "1")
link("R13", "2", "C21", "1")
link("R13", "2", "C9", "1")
link("C9", "2", "U1", "12")
link("J3", "1", "R14", "1")
link("J3", "1", "D2", "3")
link("R14", "2", "R15", "1")
link("R15", "2", "R16", "1")
link("R15", "2", "C10", "1")
link("C10", "2", "U1", "13")
link("U1", "28", "R17", "1")
link("R17", "2", "D3", "2")
link("R18", "2", "D4", "2")


def auto_links():
    """Every non-GND 2-pin point-to-point net gets a link; every rail bypass
    part links to its nearest same-net pin (see usb-power-3s provenance)."""
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
sch.append('(kicad_sch (version 20230121) (generator csr_generate_schematic)')
sch.append(f'  (uuid "{ROOT_UUID}")')
sch.append('  (paper "A3")')
sch.append('  (title_block (title "crowsync-recorder") (date "2026-07-16") (rev "v0.1")')
sch.append('    (comment 1 "USB stereo recorder: CH1 mic preamp, CH2 GNSS PPS; 01_docs/ + ADRs in repo"))')
sch.append("  (lib_symbols")
sch.extend(SYMBOLS.values())
sch.append("  )")
# canon S4 gate: emitted no_connects must exactly match the sanctioned list —
# a new None-net pin is an ACCIDENTAL float until reviewed and added here.
assert NC_PINS == SANCTIONED_FLOATS, (
    "unsanctioned floats" , sorted(NC_PINS ^ SANCTIONED_FLOATS))
sch.extend(LABELS)
sch.extend(NO_CONNECTS)
sch.extend(BODY)
sch.extend(LINKS)
for title, x0, y0, x1, y1 in SECTIONS:
    x0, y0 = max(x0 - 2, 12.0), max(y0 - 4.5, 12.0)
    x1, y1 = x1 + 2, y1 + 2.5
    sch.append(f'  (rectangle (start {x0:.2f} {y0:.2f}) (end {x1:.2f} {y1:.2f})'
               f" (stroke (width 0.35) (type solid) (color 120 120 130 0.7))"
               f' (fill (type none)) (uuid "{u()}"))')
sch.append('  (sheet_instances (path "/" (page "1")))')
sch.append(")")
content = "\n".join(sch)
assert content.count("(") == content.count(")"), (
    content.count("("), content.count(")"))
(HERE.parent / "04_kicad").mkdir(exist_ok=True)
(HERE.parent / "04_kicad" / "crowsync_recorder.kicad_sch").write_text(content)

# Project symbol library + sym-lib-table so ERC can resolve the 'csr' lib
# (kills the lib_symbol_issues "library not in configuration" warnings).
# The library is generated from the SAME SYMBOLS dict the schematic embeds,
# so embedded copies always match the library byte-for-byte.
lib = ['(kicad_symbol_lib (version 20220914) (generator csr_generate_schematic)']
for name, s in SYMBOLS.items():
    lib.append(s.replace(f'(symbol "csr:{name}"', f'(symbol "{name}"', 1))
lib.append(')')
libtxt = "\n".join(lib) + "\n"
assert libtxt.count("(") == libtxt.count(")")
(HERE / "lib").mkdir(exist_ok=True)
(HERE / "lib" / "csr.kicad_sym").write_text(libtxt)
(HERE.parent / "04_kicad" / "sym-lib-table").write_text(
    '(sym_lib_table\n  (version 7)\n'
    '  (lib (name "csr")(type "KiCad")'
    '(uri "${KIPRJMOD}/../03_src/lib/csr.kicad_sym")(options "")'
    '(descr "generated project symbols"))\n)\n')

# NEVER overwrite an existing project file — it carries DRC floors/netclasses.
if not (HERE.parent / "04_kicad" / "crowsync_recorder.kicad_pro").exists():
    (HERE.parent / "04_kicad" / "crowsync_recorder.kicad_pro").write_text(
        '{\n  "board": { "design_settings": {} },\n'
        '  "meta": { "filename": "crowsync_recorder.kicad_pro", "version": 1 },\n'
        '  "schematic": { "legacy_lib_dir": "", "legacy_lib_list": [] }\n}\n')
print("wrote crowsync_recorder.kicad_sch (+.kicad_pro, csr.kicad_sym, sym-lib-table);",
      f"{len(BODY)} items, {len(LABELS)} net labels,",
      f"{len(NO_CONNECTS)} no_connects, parens balanced")
