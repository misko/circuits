"""Generate 04_kicad/esp32_laser_timing.kicad_sch.

Machinery (symbols, global-label connectivity, structure links, sections)
derives from the crowsync-recorder generator (verified 2026-07). Pin numbers
are PHYSICAL PADS from 02_parts/<MPN>/part.yaml (each cites its datasheet
figure): ESP32-S3-WROOM-1 fig 3-1 p.10 v1.8; LM339DT fig 1 p.3 (DocID2159
rev4); AO3400A p.1 (G/S/D); AMS1117 fixed p.1 (1=GND,2=VOUT+tab,3=VIN);
USBLC6 UMW p.1. Circuit per 01_docs/ARCHITECTURE.md + DETAIL_DESIGN.md;
decisions in 01_docs/decisions/ (D1-D15 in BRIEF.md).
Run: python3 03_src/generate_schematic.py  (writes into 04_kicad/)
"""

import uuid
from pathlib import Path

HERE = Path(__file__).parent
ROOT_UUID = str(uuid.uuid4())
PROJECT = "esp32_laser_timing"


def u():
    return str(uuid.uuid4())


# ------------------------------------------------------------------ symbol library
def lib_symbol(name, w, h, pins, ref="U"):
    x0, y0 = -w / 2, -h / 2
    out = [f'    (symbol "elt:{name}" (in_bom yes) (on_board yes)']
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
# polarized electrolytic: pad 1 = POSITIVE (KiCad CP_Elec convention, part.yaml RVT100UF16V67RV0016)
defsym("CAPP", 7.62, 5.08, [("1", "+", "L", 0), ("2", "-", "R", 0)], ref="C")
defsym("LED", 7.62, 5.08, [("1", "K", "L", 0), ("2", "A", "R", 0)], ref="D")  # pad1 = cathode
defsym("TP", 5.08, 5.08, [("1", "1", "L", 0)], ref="TP")
defsym("SW", 7.62, 7.62, [("1", "1", "L", 0), ("2", "2", "L", 1)], ref="SW")
defsym("TERM2", 7.62, 7.62, [("1", "P1", "L", 0), ("2", "P2", "L", 1)], ref="J")
defsym("HDR4", 7.62, 12.7, [("1", "GND", "L", 0), ("2", "VCC", "L", 1),
                            ("3", "SCL", "L", 2), ("4", "SDA", "L", 3)], ref="J")
# HRO TYPE-C-31-M-12 16P receptacle, sink (UFP). Pad names = KiCad footprint pads
defsym("USBC", 15.24, 33.02,
       [("A4", "VBUS", "L", 0), ("A9", "VBUS", "L", 1), ("B4", "VBUS", "L", 2), ("B9", "VBUS", "L", 3),
        ("A5", "CC1", "L", 5), ("B5", "CC2", "L", 6),
        ("A1", "GND", "L", 8), ("A12", "GND", "L", 9), ("B1", "GND", "L", 10), ("B12", "GND", "L", 11),
        ("A6", "D+", "R", 0), ("A7", "D-", "R", 1), ("B6", "D+", "R", 2), ("B7", "D-", "R", 3),
        ("A8", "SBU1", "R", 5), ("B8", "SBU2", "R", 6), ("SH", "SHIELD", "R", 9)], ref="J")
# USBLC6-2SC6 SOT-23-6 (UMW datasheet pinning, p1): 1 I/O1, 2 GND, 3 I/O2, 4 I/O2, 5 VBUS, 6 I/O1
defsym("USBLC6", 10.16, 17.78,
       [("1", "I/O1", "L", 0), ("3", "I/O2", "L", 2), ("2", "GND", "L", 5),
        ("6", "I/O1'", "R", 0), ("4", "I/O2'", "R", 2), ("5", "VBUS", "R", 5)], ref="D")
# ESP32-S3-WROOM-1 (fig 3-1 p.10 v1.8): all 41 physical pads.
# Left: power/EN/USB/strap+left-side IOs; Right: bottom row + right side.
defsym("ESP32S3", 30.48, 58.42,
       [("1", "GND", "L", 0), ("40", "GND", "L", 1), ("41", "EPAD", "L", 2),
        ("2", "3V3", "L", 4), ("3", "EN", "L", 6),
        ("13", "IO19/D-", "L", 8), ("14", "IO20/D+", "L", 9),
        ("27", "IO0/BOOT", "L", 11),
        ("4", "IO4", "L", 13), ("5", "IO5", "L", 14), ("6", "IO6", "L", 15),
        ("7", "IO7", "L", 17), ("8", "IO15", "L", 18), ("9", "IO16", "L", 19),
        ("10", "IO17", "R", 0), ("11", "IO18", "R", 1), ("23", "IO21", "R", 2),
        ("39", "IO1/SDA", "R", 4), ("38", "IO2/SCL", "R", 5),
        ("12", "IO8", "R", 7), ("15", "IO3*", "R", 8), ("16", "IO46*", "R", 9),
        ("17", "IO9", "R", 10), ("18", "IO10", "R", 11), ("19", "IO11", "R", 12),
        ("20", "IO12", "R", 13), ("21", "IO13", "R", 14), ("22", "IO14", "R", 15),
        ("24", "IO47", "R", 16), ("25", "IO48", "R", 17), ("26", "IO45*", "R", 18),
        ("28", "IO35", "R", 19), ("29", "IO36", "L", 21),
        ("30", "IO37", "L", 22), ("31", "IO38", "R", 21),
        ("32", "IO39", "R", 20), ("33", "IO40", "L", 20),
        ("34", "IO41", "R", 6), ("35", "IO42", "R", 3),
        ("36", "RXD0", "L", 12), ("37", "TXD0", "L", 10)], ref="U")
# LM339DT SOIC-14 (ST DocID2159 rev4 fig 1 p.3): 1=OUT2 2=OUT1 3=VCC 4=IN1-
# 5=IN1+ 6=IN2- 7=IN2+ 8=IN3- 9=IN3+ 10=IN4- 11=IN4+ 12=GND 13=OUT4 14=OUT3
defsym("LM339", 15.24, 38.1,
       [("5", "IN1+", "L", 0), ("4", "IN1-", "L", 1),
        ("7", "IN2+", "L", 3), ("6", "IN2-", "L", 4),
        ("9", "IN3+", "L", 6), ("8", "IN3-", "L", 7),
        ("11", "IN4+", "L", 9), ("10", "IN4-", "L", 10),
        ("3", "VCC", "R", 0), ("2", "OUT1", "R", 3), ("1", "OUT2", "R", 5),
        ("14", "OUT3", "R", 7), ("13", "OUT4", "R", 9), ("12", "GND", "R", 12)],
       ref="U")
# AO3400A SOT-23 (rev3.1 p.1): 1=G 2=S 3=D
defsym("NFET", 10.16, 12.7,
       [("1", "G", "L", 1), ("3", "D", "R", 0), ("2", "S", "R", 3)], ref="Q")
# AMS1117-3.3 SOT-223 fixed (ds1117 p.1): 1=GND 2=VOUT(+tab) 3=VIN
defsym("AMS1117", 12.7, 12.7,
       [("3", "VIN", "L", 0), ("1", "GND", "L", 3), ("2", "VOUT", "R", 0)], ref="U")

# ------------------------------------------------------------------ footprints
SYM_FP = {
    "RES": "Resistor_SMD:R_0805_2012Metric",
    "CAP": "Capacitor_SMD:C_0805_2012Metric",
    "CAPP": "Capacitor_SMD:CP_Elec_6.3x5.4",
    "LED": "LED_SMD:LED_0805_2012Metric",
    "TP": "TestPoint:TestPoint_Pad_D1.5mm",
    "SW": "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A",
    "TERM2": "esp32_laser_timing:TerminalBlock_3.5-2P_NoSilk",  # vendored no-silk variant (make_lib.py)
    "HDR4": "Connector_PinSocket_2.54mm:PinSocket_1x04_P2.54mm_Vertical",
    "USBC": "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
    "USBLC6": "Package_TO_SOT_SMD:SOT-23-6",
    "ESP32S3": "esp32_laser_timing:ESP32-S3-WROOM-1",  # vendored: EP micro-holes + silk stripped (make_lib.py)
    "LM339": "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
    "NFET": "Package_TO_SOT_SMD:SOT-23",
    "AMS1117": "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
}
REF_FP = {}

# ------------------------------------------------------------------ instances
BODY = []
LABELS = []
DEFERRED_LABELS = []
BODIES = []
PART_AT = {}
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


def snap(v):
    return round(v / 1.27) * 1.27


def place(sym, ref, value, x, y, nets):
    x, y = snap(x), snap(y)
    pm, w, h = PINMAPS[sym]
    PART_AT[ref] = (x, y, sym)
    BODIES.append((x - w / 2, y - h / 2, x + w / 2, y + h / 2))
    _grow_section(x - w / 2 - 14, y - h / 2 - 3.2, x + w / 2 + 14, y + h / 2 + 3.2)
    ry, vy = y - h / 2 - 1.6, y + h / 2 + 1.8
    small = sym in ("RES", "CAP", "CAPP", "LED", "SW", "TP", "TERM2")
    vsz = 0.9 if small else 1.27
    fp = REF_FP.get(ref, SYM_FP.get(sym, ""))
    in_bom = "no" if sym == "TP" else "yes"  # TPs: exclude-from-BOM on BOTH sides (parity)
    BODY.append(
        f'  (symbol (lib_id "elt:{sym}") (at {x:.2f} {y:.2f} 0) (unit 1)'
        f' (in_bom {in_bom}) (on_board yes) (dnp no) (uuid "{u()}")\n'
        # small parts: ref right-justified at the top-LEFT corner so it never
        # sits directly above the next stacked part's centered value
        # (S-OCCL fix 2026-07-17; value-inside-body was tried and reverted —
        # long value strings clipped the body edges and pin numbers)
        + (f'    (property "Reference" "{ref}" (at {x - w/2 - 0.6:.2f} {ry:.2f} 0)'
           f' (effects (font (size 1.0 1.0)) (justify right)))\n' if small else
           f'    (property "Reference" "{ref}" (at {x:.2f} {ry:.2f} 0) (effects (font (size 1.27 1.27))))\n')
        # small parts: value left-justified from the body's LEFT edge — it
        # extends RIGHT while stacked refs extend LEFT from the same edge,
        # so the two text families are horizontally disjoint by construction
        + (f'    (property "Value" "{value}" (at {x - w/2:.2f} {vy:.2f} 0)'
           f' (effects (font (size {vsz} {vsz})) (justify left)))\n' if small else
           f'    (property "Value" "{value}" (at {x:.2f} {vy:.2f} 0) (effects (font (size {vsz} {vsz}))))\n')
        + f'    (property "Footprint" "{fp}" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))\n'
        + "\n".join(f'    (pin "{n}" (uuid "{u()}"))' for n in pm)
        + f'\n    (instances (project "{PROJECT}" (path "/{ROOT_UUID}" (reference "{ref}") (unit 1))))\n  )'
    )
    for pin_num, net in nets.items():
        side, py, _ = pm[pin_num]
        if net is None:
            ex = x - _ / 2 - 2.54 if side == "L" else x + _ / 2 + 2.54
            BODY.append(f'  (no_connect (at {ex:.2f} {y - py:.2f}) (uuid "{u()}"))')
            continue
        # Labels attach directly at pin tips. A 5.08mm wire-stub variant was
        # tried and REVERTED (2026-07-17): part spacing assumes 2.54mm label
        # reach, and longer stubs T-junctioned onto neighbours' stubs,
        # merging GND/5V/3V3 (81 parity conflicts). Wire emission is a
        # placement-coupled Phase-2 change; the label/pin-name occlusion is
        # fixed at the SYMBOL (pin names drawn inside the body) instead.
        tipx = x - _ / 2 - 2.54 if side == "L" else x + _ / 2 + 2.54
        if side == "L":
            lx, ang, just = x - _ / 2 - 2.54, 180, "right"
        else:
            lx, ang, just = x + _ / 2 + 2.54, 0, "left"
        PIN_NET[(ref, pin_num)] = net
        PIN_POS[(ref, pin_num)] = (tipx, y - py, side)
        # deferred: the chain-collapse pass may replace facing label pairs
        # with one real wire (S-OCCL: facing plates double-printed)
        DEFERRED_LABELS.append([ref, pin_num, net, lx, y - py, ang, just])


# ═══════════════════ esp32-laser-timing circuit ═══════════════════

# --- section 1: USB entry ---
section("1. USB-C INPUT (UFP sink, 5V + native USB)   [ADR-0001]", 20, 20)
place("USBC", "J1", "TYPE-C-31-M-12", 35, 45,
      {"A4": "5V", "A9": "5V", "B4": "5V", "B9": "5V",
       "A5": "CC1", "B5": "CC2",
       "A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND",
       "A6": "USB_DP", "A7": "USB_DM", "B6": "USB_DP", "B7": "USB_DM",
       "A8": None, "B8": None, "SH": "GND"})
place("RES", "R1", "5.1k CC1", 67, 28, {"1": "CC1", "2": "GND"})
place("RES", "R2", "5.1k CC2", 67, 36, {"1": "CC2", "2": "GND"})
place("USBLC6", "D1", "USBLC6-2SC6", 69, 56,
      {"1": "USB_DP", "6": "USB_DP", "3": "USB_DM", "4": "USB_DM",
       "2": "GND", "5": "5V"})

# --- section 2: power ---
section("2. POWER: 5V -> AMS1117 -> 3V3; bulk at lasers   [P4]", 20, 78)
place("AMS1117", "U2", "AMS1117-3.3", 40, 92,
      {"3": "5V", "1": "GND", "2": "3V3"})
place("CAP", "C2", "22u LDO in", 22, 92, {"1": "5V", "2": "GND"})
place("CAP", "C3", "22u LDO out", 62, 92, {"1": "3V3", "2": "GND"})
place("CAPP", "C11", "100u 5V bulk", 22, 104, {"1": "5V", "2": "GND"})
place("CAP", "C12", "100n 5V bulk", 56, 104, {"1": "5V", "2": "GND"})
place("RES", "R4", "1k LED", 87, 92, {"1": "3V3", "2": "LED_A"})
place("LED", "D2", "green PWR", 74, 100, {"1": "GND", "2": "LED_A"})  # pad1 = cathode
place("TP", "TP4", "TP 5V", 22, 117, {"1": "5V"})
place("TP", "TP5", "TP 3V3", 40, 117, {"1": "3V3"})
place("TP", "TP6", "TP GND", 58, 117, {"1": "GND"})

# --- section 3: MCU ---
section("3. ESP32-S3-WROOM-1 (native USB; pin map ADR-0004)", 20, 128)
place("ESP32S3", "U1", "ESP32-S3-WROOM-1-N8R2", 55, 170,
      {"1": "GND", "40": "GND", "41": "GND", "2": "3V3", "3": "EN",
       "13": "USB_DM", "14": "USB_DP", "27": "BOOT",
       "4": "COMP1", "5": "COMP2", "6": "COMP3",
       "7": "LDRV1", "8": "LDRV2", "9": "LDRV3",
       "10": "BTN1_G", "11": "BTN2_G", "23": "BTN3_G",
       "39": "SDA", "38": "SCL",
       "12": None, "15": None, "16": None, "17": None, "18": None,
       "19": None, "20": None, "21": None, "22": None, "24": None,
       "25": None, "26": None, "28": None, "29": None, "30": None,
       "31": None, "32": None, "33": None, "34": None, "35": None,
       "36": None, "37": None})
place("CAP", "C4", "22u MCU 3V3", 22, 140, {"1": "3V3", "2": "GND"})
place("CAP", "C5", "100n MCU 3V3", 22, 148, {"1": "3V3", "2": "GND"})
place("RES", "R3", "10k EN", 90, 140, {"1": "3V3", "2": "EN"})
place("CAP", "C1", "1u EN", 96, 153, {"1": "EN", "2": "GND"})
place("SW", "SW2", "TS-1187A RESET", 90, 158, {"1": "EN", "2": "GND"})
place("SW", "SW1", "TS-1187A BOOT", 90, 170, {"1": "BOOT", "2": "GND"})

# --- section 4: laser channels ---
section("4. LASER CHANNELS x3: low-side AO3400A, off at boot   [P5]", 130, 20)
for i, (q, rs, rp, jt, gpio) in enumerate([
        ("Q1", "R10", "R11", "J4", "LDRV1"),
        ("Q2", "R12", "R13", "J5", "LDRV2"),
        ("Q3", "R14", "R15", "J6", "LDRV3")]):
    y = 32 + i * 26
    n = i + 1
    place("RES", rs, "100R gate", 140, y, {"1": gpio, "2": f"GATE{n}"})
    place("RES", rp, "100k gate pd", 140, y + 8, {"1": f"GATE{n}", "2": "GND"})
    place("NFET", q, "AO3400A", 162, y + 4, {"1": f"GATE{n}", "3": f"LSW{n}", "2": "GND"})
    place("TERM2", jt, f"LASER {n} TERM", 184, y + 4, {"1": "5V", "2": f"LSW{n}"})

# --- section 5: photodiode comparators ---
section("5. PHOTODIODE CHANNELS x3: BPW34 -> 1k load -> LM339 @5V   [P6, ADR-0002]", 130, 106)
place("LM339", "U3", "LM339DT", 178, 135,
      {"5": "PD1", "4": "VTH1", "2": "COMP1",
       "7": "PD2", "6": "VTH2", "1": "COMP2",
       "9": "PD3", "8": "VTH3", "14": "COMP3",
       "11": "GND", "10": "VTH3", "13": None,   # spare comparator: +IN=GND, -IN=VTH3 (0.7V, defined; adjacent pad => routable at signal width; D13)
       "3": "5V", "12": "GND"})
place("CAP", "C6", "100n LM339", 196, 118, {"1": "5V", "2": "GND"})
for i in range(3):
    n = i + 1
    y = 122 + i * 12
    place("TERM2", f"J{7+i}", f"PHOTODIODE {n} TERM", 132, y,
          {"1": "5V", "2": f"PD{n}"})
    place("RES", f"R{20+i}", "1k PD load", 148, y, {"1": f"PD{n}", "2": "GND"})
for i in range(3):
    n = i + 1
    y = 166 + i * 10
    place("RES", f"R{23+i}", "10k div top", 136, y, {"1": "3V3", "2": f"VTH{n}"})
    place("RES", f"R{26+i}", "2.7k div bot", 156, y, {"1": f"VTH{n}", "2": "GND"})
    place("RES", f"R{29+i}", "33k hyst", 181, y, {"1": f"PD{n}", "2": f"COMP{n}"})
    place("RES", f"R{32+i}", "10k comp pu", 208, y, {"1": "3V3", "2": f"COMP{n}"})
for i in range(3):
    place("TP", f"TP{i+1}", f"TP COMP{i+1}", 214, 132 + i * 8, {"1": f"COMP{i+1}"})

# --- section 6: buttons ---
section("6. BUTTON CHANNELS x3: 10k pu / 100n / 1k series   [P9]", 130, 196)
for i in range(3):
    n = i + 1
    y = 208 + i * 12
    place("TERM2", f"J{10+i}", f"BUTTON {n} TERM", 132, y,
          {"1": f"BTN{n}_N", "2": "GND"})
    place("RES", f"R{40+i}", "10k btn pu", 150, y, {"1": "3V3", "2": f"BTN{n}_N"})
    place("CAP", f"C{8+i}", "100n btn", 168, y, {"1": f"BTN{n}_N", "2": "GND"})
    place("RES", f"R{43+i}", "1k btn ser", 195, y, {"1": f"BTN{n}_N", "2": f"BTN{n}_G"})

# --- section 7: OLED ---
section("7. OLED HEADER (GND VCC SCL SDA - CHECK MODULE PINOUT)   [P8]", 20, 212)
place("HDR4", "J2", "OLED HDR 1x4F", 30, 226,
      {"1": "GND", "2": "3V3", "3": "SCL", "4": "SDA"})
place("RES", "R50", "4.7k SDA pu", 52, 222, {"1": "3V3", "2": "SDA"})
place("RES", "R51", "4.7k SCL pu", 52, 230, {"1": "3V3", "2": "SCL"})
place("CAP", "C7", "100n OLED", 72, 226, {"1": "3V3", "2": "GND"})

# ------------------------------------------------------------------ structure links
link("J1", "A6", "D1", "1")
link("J1", "A7", "D1", "3")
link("D1", "6", "U1", "14")
link("D1", "4", "U1", "13")
link("J1", "A5", "R1", "1")
link("J1", "B5", "R2", "1")
link("C2", "1", "U2", "3")
link("U2", "2", "C3", "1")
link("R3", "2", "C1", "1")
link("R3", "2", "U1", "3")
link("C1", "1", "SW2", "1")
link("SW1", "1", "U1", "27")
link("R4", "2", "D2", "2")
for i in range(3):
    n = i + 1
    rs, rp, q = f"R{10+2*i}", f"R{11+2*i}", f"Q{n}"
    link("U1", str(7 + i), rs, "1")
    link(rs, "2", q, "1")
    link(rp, "1", q, "1")
    link(q, "3", f"J{4+i}", "2")
    link(f"J{7+i}", "2", f"R{20+i}", "1")
    link(f"R{20+i}", "1", "U3", ["5", "7", "9"][i])
    link(f"R{23+i}", "2", f"R{26+i}", "1")
    link(f"R{23+i}", "2", "U3", ["4", "6", "8"][i])
    link("U3", ["2", "1", "14"][i], f"R{32+i}", "2")
    link("U3", ["2", "1", "14"][i], "U1", str(4 + i))
    link(f"R{29+i}", "1", f"R{20+i}", "1")
    link(f"R{29+i}", "2", f"R{32+i}", "2")
    link(f"J{10+i}", "1", f"R{40+i}", "2")
    link(f"R{40+i}", "2", f"C{8+i}", "1")
    link(f"R{43+i}", "1", f"C{8+i}", "1")
    link(f"R{43+i}", "2", "U1", ["10", "11", "23"][i])
link("J2", "4", "R50", "2")
link("J2", "3", "R51", "2")
link("R50", "2", "U1", "39")
link("R51", "2", "U1", "38")


def auto_links():
    """Every non-GND 2-pin point-to-point net gets a link; every rail bypass
    part links to its nearest same-net pin (crowsync provenance)."""
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
        if net == "GND" or ref[0] not in "RCLD":
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
# ---- chain-collapse: facing same-net pins joined by ONE real wire ----
# The label-per-pin model double-prints facing plates in series chains
# (S-OCCL review 2026-07-17). For each net: an R-side tip facing an L-side
# tip at the same y, gap <= 30mm, with the span EMPTY (no body bbox, no
# third pin tip that a wire endpoint-on-segment would T-join), becomes one
# wire; both labels are suppressed. Every net keeps >= 1 label (netlist
# name = parity invariant); a net whose only pins got wired keeps one
# label at a wire endpoint (labels attach to wire ends).
from collections import defaultdict as _dd
_by_net = _dd(list)
for _i, (_r, _p, _n, _lx, _ly, _ang, _j) in enumerate(DEFERRED_LABELS):
    _by_net[_n].append(_i)
_suppress, _pairedpins = set(), set()
for _net, _idxs in _by_net.items():
    for _i in _idxs:
        _ri, _pi = DEFERRED_LABELS[_i][0], DEFERRED_LABELS[_i][1]
        if (_ri, _pi) in _pairedpins:
            continue
        _ax, _ay, _sa = PIN_POS[(_ri, _pi)]
        if _sa != "R":
            continue
        _best = None
        for _jj in _idxs:
            if _jj == _i:
                continue
            _rj, _pj = DEFERRED_LABELS[_jj][0], DEFERRED_LABELS[_jj][1]
            if (_rj, _pj) in _pairedpins:
                continue
            _bx, _by, _sb = PIN_POS[(_rj, _pj)]
            if _sb != "L" or abs(_by - _ay) > 0.01:
                continue
            _gap = _bx - _ax
            if _gap <= 0 or _gap > 30:
                continue
            if _best is None or _gap < _best[0]:
                _best = (_gap, _jj, _bx)
        if _best is None:
            continue
        _gap, _jj, _bx = _best
        _rj, _pj = DEFERRED_LABELS[_jj][0], DEFERRED_LABELS[_jj][1]
        _blocked = any(not (bb[2] <= _ax + 0.01 or _bx - 0.01 <= bb[0]
                            or bb[3] <= _ay - 1.0 or _ay + 1.0 <= bb[1])
                       for bb in BODIES)
        if not _blocked:
            for (_r3, _p3), (_tx, _ty, _s3) in PIN_POS.items():
                if (_r3, _p3) in ((_ri, _pi), (_rj, _pj)):
                    continue
                if abs(_ty - _ay) < 0.01 and _ax < _tx < _bx:
                    _blocked = True
                    break
        if _blocked:
            continue
        BODY.append(f'  (wire (pts (xy {_ax:.2f} {_ay:.2f})'
                    f' (xy {_bx:.2f} {_ay:.2f}))'
                    f' (stroke (width 0)) (uuid "{u()}"))')
        _pairedpins.add((_ri, _pi)); _pairedpins.add((_rj, _pj))
        # keep ONE label per wire: a global label is the glue that ties the
        # wire island into its net — suppressing both sides orphaned 8 wire
        # pairs into auto-named islands (16 parity conflicts, 2026-07-17).
        # The surviving plate sits on the wire span: standard KiCad reading.
        _suppress.add(_jj)
_n_wires = sum(1 for b in BODY if b.startswith('  (wire'))
for _i, (_r, _p, _net, _lx, _ly, _ang, _j) in enumerate(DEFERRED_LABELS):
    if _i in _suppress:
        continue
    LABELS.append(
        f'  (global_label "{_net}" (shape passive) (at {_lx:.2f} {_ly:.2f} {_ang})'
        f' (fields_autoplaced) (effects (font (size 1.27 1.27)) (justify {_j})) (uuid "{u()}"))'
    )
print(f"chain-collapse: {_n_wires} wires, {len(_suppress)} labels suppressed, "
      f"{len(DEFERRED_LABELS) - len(_suppress)} labels kept")

# ---- plate-pitch reporter: different-net label plates must not overlap ----
# (machine-computed nudges; apply and regenerate until it reports none)
_plates=[]
for _i,(_r,_p,_n,_lx,_ly,_ang,_j) in enumerate(DEFERRED_LABELS):
    if _i in _suppress: continue
    _wl=(len(_n)+2)*1.05
    if _ang==180: _plates.append((_lx-_wl,_ly-1.1,_lx,_ly+1.1,_r,_n))
    else: _plates.append((_lx,_ly-1.1,_lx+_wl,_ly+1.1,_r,_n))
_nudge={}
for _a in range(len(_plates)):
    for _b in range(_a+1,len(_plates)):
        A,B=_plates[_a],_plates[_b]
        if A[5]==B[5] and A[4]==B[4]: continue
        if A[0]<B[2] and B[0]<A[2] and A[1]<B[3] and B[1]<A[3]:
            _ox=min(A[2],B[2])-max(A[0],B[0])
            # move the part whose PART x is rightmost, right by overlap+0.8
            _ra,_rb=A[4],B[4]
            _mover=_ra if PART_AT.get(_ra,(0,0))[0]>=PART_AT.get(_rb,(0,0))[0] else _rb
            _need=_ox+0.8
            _nudge[_mover]=max(_nudge.get(_mover,0),_need)
for _r,_d in sorted(_nudge.items()):
    _x,_y,_sym=PART_AT[_r]
    print(f"PITCH-NUDGE {_r} ({_sym}): x {_x:.0f} -> {_x+_d:.1f}  (move right {_d:.1f}mm)")

sch = []
sch.append('(kicad_sch (version 20230121) (generator elt_generate_schematic)')
sch.append(f'  (uuid "{ROOT_UUID}")')
sch.append('  (paper "A2")')
# title-block rev tracks the release tag (canon: provenance is generated,
# never hand-set — the v1.3 release PDF shipped saying "Rev: v1.0")
import subprocess as _sp
try:
    import os as _os
    _rev = (_os.environ.get("ELT_REV")
            or _sp.run(["git", "describe", "--tags", "--match", "elt-v*",
                        "--abbrev=0"], capture_output=True, text=True,
                       cwd=str(HERE)).stdout.strip().replace("elt-", "")
            or "dev")
except Exception:
    _rev = "dev"
import datetime as _dt
_date = _dt.date.today().isoformat()
sch.append(f'  (title_block (title "esp32-laser-timing") (date "{_date}") (rev "{_rev}")')
sch.append('    (comment 1 "Laser interruption timing bench controller; 01_docs/ + ADRs in repo"))')
sch.append("  (lib_symbols")
sch.extend(SYMBOLS.values())
sch.append("  )")
sch.extend(LABELS)
sch.extend(BODY)
# LINKS (dashed pseudo-wires) intentionally NOT emitted: decorative
# connectivity crossed section boxes and symbols (occlusion review
# 2026-07-17); real wire stubs at every labeled pin carry the intent now.
_rects = []
for title, x0, y0, x1, y1 in SECTIONS:
    x0, y0 = max(x0 - 2, 12.0), max(y0 - 4.5, 12.0)
    x1, y1 = x1 + 2, y1 + 2.5
    _rects.append([title, x0, y0, x1, y1])
# separate intersecting section boxes: pull the shared edge to the overlap
# midline on the axis of least overlap — boxes may abut, never cross
# (occlusion review 2026-07-17: borders struck through neighboring content)
for _i in range(len(_rects)):
    for _j in range(_i + 1, len(_rects)):
        _a, _b = _rects[_i], _rects[_j]
        _ox = min(_a[3], _b[3]) - max(_a[1], _b[1])
        _oy = min(_a[4], _b[4]) - max(_a[2], _b[2])
        if _ox <= 0 or _oy <= 0:
            continue
        if _ox <= _oy:
            _mid = (max(_a[1], _b[1]) + min(_a[3], _b[3])) / 2
            if _a[1] < _b[1]:
                _a[3] = min(_a[3], _mid - 0.5); _b[1] = max(_b[1], _mid + 0.5)
            else:
                _b[3] = min(_b[3], _mid - 0.5); _a[1] = max(_a[1], _mid + 0.5)
        else:
            _mid = (max(_a[2], _b[2]) + min(_a[4], _b[4])) / 2
            if _a[2] < _b[2]:
                _a[4] = min(_a[4], _mid - 0.5); _b[2] = max(_b[2], _mid + 0.5)
            else:
                _b[4] = min(_b[4], _mid - 0.5); _a[2] = max(_a[2], _mid + 0.5)
for title, x0, y0, x1, y1 in _rects:
    sch.append(f'  (rectangle (start {x0:.2f} {y0:.2f}) (end {x1:.2f} {y1:.2f})'
               f" (stroke (width 0.35) (type solid) (color 120 120 130 0.7))"
               f' (fill (type none)) (uuid "{u()}"))')
sch.append('  (sheet_instances (path "/" (page "1")))')
sch.append(")")
content = "\n".join(sch)
assert content.count("(") == content.count(")"), (
    content.count("("), content.count(")"))
(HERE.parent / "04_kicad").mkdir(exist_ok=True)
(HERE.parent / "04_kicad" / "esp32_laser_timing.kicad_sch").write_text(content)

# symbol library file + sym-lib-table (ERC: lib_symbol_issues) — same symbol
# bodies as embedded, plain names
lib = ['(kicad_symbol_lib (version 20231120) (generator elt_generate_schematic)']
for name, s in SYMBOLS.items():
    lib.append(s.replace(f'(symbol "elt:{name}"', f'(symbol "{name}"', 1))
lib.append(')')
(HERE / "lib").mkdir(exist_ok=True)
(HERE / "lib" / "elt.kicad_sym").write_text("\n".join(lib) + "\n")
(HERE.parent / "04_kicad" / "sym-lib-table").write_text(
    '(sym_lib_table\n  (version 7)\n'
    '  (lib (name "elt")(type "KiCad")(uri "${KIPRJMOD}/../03_src/lib/elt.kicad_sym")(options "")(descr "project symbols"))\n)\n')

# fp-lib-table covering every referenced footprint lib (ERC: footprint_link_issues)
STD = "/usr/share/kicad/footprints"
libs = sorted({fp.split(":")[0] for fp in SYM_FP.values()} | {"MountingHole"})
rows = ['(fp_lib_table', '  (version 7)']
for l in libs:
    if l == "esp32_laser_timing":
        rows.append('  (lib (name "esp32_laser_timing")(type "KiCad")(uri "${KIPRJMOD}/../03_src/lib/esp32_laser_timing.pretty")(options "")(descr "project footprints"))')
        continue
    rows.append(f'  (lib (name "{l}")(type "KiCad")(uri "{STD}/{l}.pretty")(options "")(descr "system"))')
rows.append(')')
(HERE.parent / "04_kicad" / "fp-lib-table").write_text("\n".join(rows) + "\n")

# NEVER overwrite an existing project file — it carries DRC floors/netclasses.
if not (HERE.parent / "04_kicad" / "esp32_laser_timing.kicad_pro").exists():
    (HERE.parent / "04_kicad" / "esp32_laser_timing.kicad_pro").write_text(
        '{\n  "board": { "design_settings": {} },\n'
        '  "meta": { "filename": "esp32_laser_timing.kicad_pro", "version": 1 },\n'
        '  "schematic": { "legacy_lib_dir": "", "legacy_lib_list": [] }\n}\n')
print("wrote esp32_laser_timing.kicad_sch (+.kicad_pro);",
      f"{len(BODY)} items, {len(LABELS)} net labels, parens balanced")
