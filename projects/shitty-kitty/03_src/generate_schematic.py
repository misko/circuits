"""Generate 04_kicad/shitty_kitty.kicad_sch.

Machinery (symbols, global-label connectivity, structure links, sections)
derives from the esp32-laser-timing generator (verified 2026-07-17). Pin
numbers are PHYSICAL PADS from 02_parts/<MPN>/part.yaml (each cites its
datasheet figure): ESP32-S3-WROOM-1 fig 3-1 p.10 v1.8; TMC2209 (see
02_parts/TMC2209-LA-T/part.yaml); MPR121QR2; LIS2DH12; AP63205; AOD4185;
AMS1117 p.1; USBLC6 UMW p.1. Circuit per 01_docs/ARCHITECTURE.md +
DETAIL_DESIGN.md; decisions D1-D10 in BRIEF.md + ADRs 0001-0005.
Run: python3 03_src/generate_schematic.py  (writes into 04_kicad/)
"""

import uuid
from pathlib import Path

HERE = Path(__file__).parent
ROOT_UUID = str(uuid.uuid4())
PROJECT = "shitty_kitty"


def u():
    return str(uuid.uuid4())


# ------------------------------------------------------------------ symbol library
def lib_symbol(name, w, h, pins, ref="U"):
    x0, y0 = -w / 2, -h / 2
    out = [f'    (symbol "sk:{name}" (in_bom yes) (on_board yes)']
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
# polarized electrolytic: pad 1 = POSITIVE (part.yaml RVT100UF25V67RV0011)
defsym("CAPP", 7.62, 5.08, [("1", "+", "L", 0), ("2", "-", "R", 0)], ref="C")
defsym("LED", 7.62, 5.08, [("1", "K", "L", 0), ("2", "A", "R", 0)], ref="D")  # pad1 = cathode
defsym("SW", 7.62, 7.62, [("1", "1", "L", 0), ("2", "2", "L", 1)], ref="SW")
defsym("TERM2", 7.62, 7.62, [("1", "P1", "L", 0), ("2", "P2", "L", 1)], ref="J")
defsym("FUSE", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="F")
defsym("IND", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="L")
# TVS unidirectional SMB: pad 1 = CATHODE (band; part.yaml SMBJ16A)
defsym("TVS", 7.62, 5.08, [("1", "K", "L", 0), ("2", "A", "R", 0)], ref="D")
# barrel jack DC-005 class (part.yaml DC-005C-20A): 1=tip(+), 2=sleeve, 3=switch
defsym("BARREL", 10.16, 10.16, [("1", "TIP+", "R", 0), ("2", "SLEEVE", "R", 2), ("3", "SW", "R", 1)], ref="J")
# AOD4185 P-FET TO-252 (part.yaml): 1=G, 2=D(tab), 3=S
defsym("PFET", 10.16, 12.7, [("1", "G", "L", 1), ("2", "D", "R", 0), ("3", "S", "R", 3)], ref="Q")
defsym("HDR6", 7.62, 17.78, [("1", "5V", "L", 0), ("2", "5V", "L", 1), ("3", "GND", "L", 2),
                             ("4", "GND", "L", 3), ("5", "TX", "L", 4), ("6", "RX", "L", 5)], ref="J")
defsym("HDR13", 7.62, 35.56, [(str(i), f"P{i}", "L", i - 1) for i in range(1, 14)], ref="J")
defsym("XH4", 7.62, 12.7, [("1", "A1", "L", 0), ("2", "A2", "L", 1),
                           ("3", "B1", "L", 2), ("4", "B2", "L", 3)], ref="J")
# HRO TYPE-C-31-M-12 16P receptacle, sink (UFP). Pad names = KiCad footprint pads
defsym("USBC", 15.24, 33.02,
       [("A4", "VBUS", "L", 0), ("A9", "VBUS", "L", 1), ("B4", "VBUS", "L", 2), ("B9", "VBUS", "L", 3),
        ("A5", "CC1", "L", 5), ("B5", "CC2", "L", 6),
        ("A1", "GND", "L", 8), ("A12", "GND", "L", 9), ("B1", "GND", "L", 10), ("B12", "GND", "L", 11),
        ("A6", "D+", "R", 0), ("A7", "D-", "R", 1), ("B6", "D+", "R", 2), ("B7", "D-", "R", 3),
        ("A8", "SBU1", "R", 5), ("B8", "SBU2", "R", 6), ("SH", "SHIELD", "R", 9)], ref="J")
# USBLC6-2SC6 SOT-23-6 (UMW p1): 1 I/O1, 2 GND, 3 I/O2, 4 I/O2, 5 VBUS, 6 I/O1
defsym("USBLC6", 10.16, 17.78,
       [("1", "I/O1", "L", 0), ("3", "I/O2", "L", 2), ("2", "GND", "L", 5),
        ("6", "I/O1'", "R", 0), ("4", "I/O2'", "R", 2), ("5", "VBUS", "R", 5)], ref="D")
# ESP32-S3-WROOM-1 (fig 3-1 p.10 v1.8): all 41 physical pads.
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
# AMS1117-3.3 SOT-223 fixed (ds1117 p.1): 1=GND 2=VOUT(+tab) 3=VIN
defsym("AMS1117", 12.7, 12.7,
       [("3", "VIN", "L", 0), ("1", "GND", "L", 3), ("2", "VOUT", "R", 0)], ref="U")
# TMC2209-LA-T QFN28 (02_parts/TMC2209-LA-T/part.yaml, fig 2.1 p.9 rev1.09):
# 1 OB2, 2 ENN, 3 GND, 4 CPO, 5 CPI, 6 VCP, 7 SPREAD, 8 5VOUT, 9 MS1, 10 MS2,
# 11 DIAG, 12 INDEX, 13 CLK, 14 PDN_UART, 15 VCC_IO, 16 STEP, 17 VREF, 18 GND,
# 19 DIR, 20 STDBY, 21 OA2, 22 VS, 23 BRA, 24 OA1, 25 NC, 26 OB1, 27 BRB,
# 28 VS, 29 EP(GND)
defsym("TMC2209", 25.4, 58.42,
       [("22", "VS", "L", 0), ("28", "VS", "L", 1),
        ("6", "VCP", "L", 3), ("4", "CPO", "L", 4), ("5", "CPI", "L", 5),
        ("8", "5VOUT", "L", 7), ("15", "VCC_IO", "L", 9),
        ("2", "ENN", "L", 11), ("16", "STEP", "L", 12), ("19", "DIR", "L", 13),
        ("9", "MS1", "L", 15), ("10", "MS2", "L", 16), ("7", "SPREAD", "L", 17),
        ("13", "CLK", "L", 18), ("20", "STDBY", "L", 19), ("17", "VREF", "L", 20),
        ("24", "OA1", "R", 0), ("21", "OA2", "R", 1),
        ("26", "OB1", "R", 3), ("1", "OB2", "R", 4),
        ("23", "BRA", "R", 6), ("27", "BRB", "R", 7),
        ("14", "PDN_UART", "R", 9), ("11", "DIAG", "R", 11), ("12", "INDEX", "R", 12),
        ("3", "GND", "R", 14), ("18", "GND", "R", 15), ("29", "EP", "R", 16),
        ("25", "NC25", "R", 18)], ref="U")
# MPR121QR2 UQFN-20 no EP (02_parts/MPR121QR2/part.yaml, pin fig p.1 rev4):
# 1 IRQ, 2 SCL, 3 SDA, 4 ADDR, 5 VREG, 6 VSS, 7 REXT, 8-19 ELE0-11, 20 VDD
defsym("MPR121", 20.32, 40.64,
       [("20", "VDD", "L", 0), ("5", "VREG", "L", 2), ("4", "ADDR", "L", 4),
        ("2", "SCL", "L", 6), ("3", "SDA", "L", 7), ("1", "IRQ", "L", 9),
        ("7", "REXT", "L", 11), ("6", "VSS", "L", 13)] +
       [(str(8 + i), f"ELE{i}", "R", i) for i in range(12)], ref="U")
# LIS2DH12 LGA-12 (02_parts/LIS2DH12TR/part.yaml, fig 2 p.8 + table 2 p.9):
# 1 SCL, 2 CS, 3 SA0, 4 SDA, 5 RES(GND), 6-8 GND, 9 VDD, 10 VDD_IO, 11 INT2, 12 INT1
defsym("ACCEL", 15.24, 35.56,
       [("9", "VDD", "L", 0), ("10", "VDD_IO", "L", 1), ("2", "CS", "L", 3),
        ("3", "SA0", "L", 4), ("1", "SCL", "L", 6), ("4", "SDA", "L", 7),
        ("5", "RES", "L", 9), ("6", "GND", "L", 10), ("7", "GND", "L", 11),
        ("8", "GND", "L", 12),
        ("12", "INT1", "R", 0), ("11", "INT2", "R", 2)], ref="U")
# AP63205WU-7 TSOT-23-6 (02_parts/AP63205WU-7/part.yaml, DS41326 fig p.1):
# 1=FB (fixed: wire DIRECTLY to VOUT), 2=EN (may tie to VIN), 3=VIN, 4=GND,
# 5=SW, 6=BST
BUCK_PIN = {"FB": "1", "EN": "2", "VIN": "3", "GND": "4", "SW": "5", "BST": "6"}
defsym("BUCK", 12.7, 17.78,
       [(BUCK_PIN["VIN"], "VIN", "L", 0), (BUCK_PIN["EN"], "EN", "L", 2),
        (BUCK_PIN["GND"], "GND", "L", 4),
        (BUCK_PIN["SW"], "SW", "R", 0), (BUCK_PIN["BST"], "BST", "R", 2),
        (BUCK_PIN["FB"], "FB/VOUT", "R", 4)], ref="U")
defsym("RES1206", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="R")

# ------------------------------------------------------------------ footprints
SYM_FP = {
    "RES": "Resistor_SMD:R_0805_2012Metric",
    "CAP": "Capacitor_SMD:C_0805_2012Metric",
    "CAPP": "Capacitor_SMD:CP_Elec_6.3x7.7",
    "LED": "LED_SMD:LED_0805_2012Metric",
    "SW": "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A",
    "TERM2": "shitty_kitty:TerminalBlock_3.5-2P_NoSilk",
    "FUSE": "Fuse:Fuse_1812_4532Metric",
    "IND": "Inductor_SMD:L_Sunlord_SWPA6045S",
    "TVS": "Diode_SMD:D_SMB",
    "BARREL": "Connector_BarrelJack:BarrelJack_Horizontal",
    "PFET": "Package_TO_SOT_SMD:TO-252-2",
    "HDR6": "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical",
    "HDR13": "Connector_PinHeader_2.54mm:PinHeader_1x13_P2.54mm_Vertical",
    "XH4": "Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical",
    "USBC": "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
    "USBLC6": "Package_TO_SOT_SMD:SOT-23-6",
    "ESP32S3": "shitty_kitty:ESP32-S3-WROOM-1",
    "AMS1117": "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
    "RES1206": "Resistor_SMD:R_1206_3216Metric",
    "C1206": "Capacitor_SMD:C_1206_3216Metric",
    # @@FPS@@
}
REF_FP = {}

# ------------------------------------------------------------------ instances
BODY = []
LABELS = []
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
    _grow_section(x - w / 2 - 14, y - h / 2 - 3.2, x + w / 2 + 14, y + h / 2 + 3.2)
    ry, vy = y - h / 2 - 1.6, y + h / 2 + 1.8
    vsz = 0.9 if sym in ("RES", "CAP", "CAPP", "LED", "SW", "FUSE", "IND", "TVS", "RES1206", "C1206") else 1.27
    fp = REF_FP.get(ref, SYM_FP.get(sym, ""))
    BODY.append(
        f'  (symbol (lib_id "sk:{sym}") (at {x:.2f} {y:.2f} 0) (unit 1)'
        f' (in_bom yes) (on_board yes) (dnp no) (uuid "{u()}")\n'
        f'    (property "Reference" "{ref}" (at {x:.2f} {ry:.2f} 0) (effects (font (size 1.27 1.27))))\n'
        f'    (property "Value" "{value}" (at {x:.2f} {vy:.2f} 0) (effects (font (size {vsz} {vsz}))))\n'
        f'    (property "Footprint" "{fp}" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))\n'
        + "\n".join(f'    (pin "{n}" (uuid "{u()}"))' for n in pm)
        + f'\n    (instances (project "{PROJECT}" (path "/{ROOT_UUID}" (reference "{ref}") (unit 1))))\n  )'
    )
    for pin_num, net in nets.items():
        assert pin_num in pm, f"{ref}: pin {pin_num} not in symbol {sym}"
        side, py, _ = pm[pin_num]
        if net is None:
            ex = x - _ / 2 - 2.54 if side == "L" else x + _ / 2 + 2.54
            BODY.append(f'  (no_connect (at {ex:.2f} {y - py:.2f}) (uuid "{u()}"))')
            continue
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
    missing = set(pm) - set(nets)
    assert not missing, f"{ref}: pins with no net/NC assignment: {missing}"


# ═══════════════════ shitty-kitty circuit ═══════════════════

# --- section 1: 12V entry + protection (ADR-0001) ---
section("1. 12V INPUT: barrel -> polyfuse -> P-FET revpol -> TVS   [ADR-0001]", 20, 20)
place("BARREL", "J1", "DC-005C-20A 12V", 30, 32,
      {"1": "VIN_RAW", "2": "GND", "3": "GND"})
place("FUSE", "F1", "2A polyfuse 16V", 52, 30, {"1": "VIN_RAW", "2": "VIN_F"})
# Q1 AOD4185 P-FET (part.yaml: 1=G 2=D/tab 3=S): D=input, S=load, G=GND pull
place("PFET", "Q1", "AOD4185 revpol", 70, 32, {"1": "GATE_Q1", "2": "VIN_F", "3": "VIN_12V"})
place("RES", "R1", "100k gate pd", 70, 44, {"1": "GATE_Q1", "2": "GND"})
place("TVS", "D3", "SMBJ16A", 90, 32, {"1": "VIN_12V", "2": "GND"})  # pad1 = cathode -> +12V
place("CAPP", "C40", "100u 12V bulk", 90, 44, {"1": "VIN_12V", "2": "GND"})
place("CAP", "C25", "100n 12V", 105, 44, {"1": "VIN_12V", "2": "GND"})

# --- section 2: buck + LDO ---
section("2. POWER: AP63205 12V->5V 2A; AMS1117 -> 3V3   [D5, ADR-0004]", 20, 62)
# EN tied DIRECTLY to VIN (part.yaml: EN is a high-voltage pin, ties to VIN
# for automatic startup, no resistor needed — DS p.11)
place("BUCK", "U8", "AP63205WU-7", 42, 78,
      {BUCK_PIN["VIN"]: "VIN_12V", BUCK_PIN["EN"]: "VIN_12V",
       BUCK_PIN["GND"]: "GND", BUCK_PIN["SW"]: "SW_BUCK",
       BUCK_PIN["BST"]: "BST", BUCK_PIN["FB"]: "5V"})
place("CAP", "C1", "4.7u buck in", 22, 78, {"1": "VIN_12V", "2": "GND"})
place("CAP", "C2", "4.7u buck in", 22, 86, {"1": "VIN_12V", "2": "GND"})
place("CAP", "C5", "100n BST", 62, 70, {"1": "BST", "2": "SW_BUCK"})
place("IND", "L1", "10uH SWPA6045S", 62, 78, {"1": "SW_BUCK", "2": "5V"})
place("CAP", "C3", "22u buck out", 78, 78, {"1": "5V", "2": "GND"})
place("CAP", "C4", "22u buck out", 78, 86, {"1": "5V", "2": "GND"})
place("AMS1117", "U9", "AMS1117-3.3", 98, 78, {"3": "5V", "1": "GND", "2": "3V3"})
place("CAP", "C6", "4.7u LDO in", 92, 90, {"1": "5V", "2": "GND"})
place("CAP", "C7", "22u LDO out", 112, 90, {"1": "3V3", "2": "GND"})
place("RES", "R3", "1k LED", 126, 78, {"1": "3V3", "2": "LED_A"})
place("LED", "D2", "green PWR", 126, 86, {"1": "GND", "2": "LED_A"})  # pad1 = cathode

# --- section 3: USB-C programming (data only, no power in) ---
section("3. USB-C PROGRAMMING (data only; board powers from 12V)", 20, 104)
place("USBC", "J2", "TYPE-C-31-M-12", 35, 128,
      {"A4": "USB_VBUS", "A9": "USB_VBUS", "B4": "USB_VBUS", "B9": "USB_VBUS",
       "A5": "CC1", "B5": "CC2",
       "A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND",
       "A6": "USB_DP", "A7": "USB_DM", "B6": "USB_DP", "B7": "USB_DM",
       "A8": None, "B8": None, "SH": "GND"})
place("RES", "R4", "5.1k CC1", 62, 112, {"1": "CC1", "2": "GND"})
place("RES", "R5", "5.1k CC2", 62, 120, {"1": "CC2", "2": "GND"})
place("USBLC6", "D1", "USBLC6-2SC6", 66, 136,
      {"1": "USB_DP", "6": "USB_DP", "3": "USB_DM", "4": "USB_DM",
       "2": "GND", "5": "USB_VBUS"})
place("CAP", "C8", "100n VBUS", 84, 120, {"1": "USB_VBUS", "2": "GND"})

# --- section 4: MCU ---
section("4. ESP32-S3-WROOM-1 (native USB; pin map ARCHITECTURE.md)", 20, 158)
place("ESP32S3", "U1", "ESP32-S3-WROOM-1-N8R2", 55, 200,
      {"1": "GND", "40": "GND", "41": "GND", "2": "3V3", "3": "EN",
       "13": "USB_DM", "14": "USB_DP", "27": "BOOT",
       "4": "STEP", "5": "DIR", "6": "ENN",
       "7": "DIAG", "8": "INDEX", "9": "ENDSTOP_G",
       "10": "TMC_TX", "11": "TMC_UART", "23": None,
       "39": "SDA", "38": "SCL",
       "12": "MPR_IRQ1", "17": "MPR_IRQ2", "18": "MPR_IRQ3", "19": "MPR_IRQ4",
       "20": "ACC_INT", "21": "LED_ST",
       "36": "HOST_RX", "37": "HOST_TX",
       "15": None, "16": None, "22": None, "24": None,
       "25": None, "26": None, "28": None, "29": None, "30": None,
       "31": None, "32": None, "33": None, "34": None, "35": None})
place("CAP", "C9", "22u MCU 3V3", 22, 172, {"1": "3V3", "2": "GND"})
place("CAP", "C10", "100n MCU 3V3", 22, 180, {"1": "3V3", "2": "GND"})
place("RES", "R6", "10k EN", 90, 172, {"1": "3V3", "2": "EN"})
place("CAP", "C11", "1u EN", 90, 180, {"1": "EN", "2": "GND"})
place("SW", "SW2", "TS-1187A RESET", 90, 190, {"1": "EN", "2": "GND"})
place("SW", "SW1", "TS-1187A BOOT", 90, 202, {"1": "BOOT", "2": "GND"})
place("RES", "R7", "1k status LED", 90, 214, {"1": "LED_ST", "2": "LED_SA"})
place("LED", "D5", "green STATUS", 90, 222, {"1": "GND", "2": "LED_SA"})

# --- section 5: motor driver + motor/endstop connectors ---
section("5. TMC2209 DRIVER: quiet, UART, MOTOR OFF AT BOOT   [ADR-0002, D9]", 150, 20)
place("TMC2209", "U2", "TMC2209-LA-T", 175, 55,
      {"22": "VIN_12V", "28": "VIN_12V",
       "6": "VCP", "4": "CPO", "5": "CPI",
       "8": "V5OUT", "15": "3V3",
       "2": "ENN", "16": "STEP", "19": "DIR",
       "9": "GND", "10": "GND", "7": "GND", "13": "GND",
       "20": None, "17": None, "25": None,
       "24": "MOT_A1", "21": "MOT_A2", "26": "MOT_B1", "1": "MOT_B2",
       "23": "BRA", "27": "BRB",
       "14": "TMC_UART", "11": "DIAG", "12": "INDEX",
       "3": "GND", "18": "GND", "29": "GND"})
place("RES", "R8", "10k ENN pu", 152, 24, {"1": "3V3", "2": "ENN"})  # MOTOR DISABLED AT BOOT
place("RES", "R9", "1k TMC UART", 152, 32, {"1": "TMC_TX", "2": "TMC_UART"})
place("CAP", "C12", "100n VCP", 200, 24, {"1": "VCP", "2": "VIN_12V"})
place("CAP", "C26", "22n CP fly", 200, 32, {"1": "CPO", "2": "CPI"})
place("CAP", "C13", "4.7u 5VOUT", 200, 40, {"1": "V5OUT", "2": "GND"})
place("CAP", "C16", "100n VCC_IO", 200, 48, {"1": "3V3", "2": "GND"})
place("CAP", "C14", "100n VS", 152, 40, {"1": "VIN_12V", "2": "GND"})
place("CAP", "C15", "100n VS", 152, 48, {"1": "VIN_12V", "2": "GND"})
place("CAPP", "C41", "100u VS bulk", 152, 56, {"1": "VIN_12V", "2": "GND"})
place("RES1206", "R30", "0.15R sense A", 200, 60, {"1": "BRA", "2": "GND"})
place("RES1206", "R31", "0.15R sense B", 200, 68, {"1": "BRB", "2": "GND"})
place("XH4", "J5", "MOTOR NEMA17", 224, 55,
      {"1": "MOT_A1", "2": "MOT_A2", "3": "MOT_B1", "4": "MOT_B2"})
place("TERM2", "J6", "ENDSTOP TERM", 224, 76, {"1": "ENDSTOP_N", "2": "GND"})
place("RES", "R10", "10k endstop pu", 152, 76, {"1": "3V3", "2": "ENDSTOP_N"})
place("CAP", "C17", "100n endstop", 152, 84, {"1": "ENDSTOP_N", "2": "GND"})
place("RES", "R11", "1k endstop ser", 175, 84, {"1": "ENDSTOP_N", "2": "ENDSTOP_G"})

# --- section 6: host header ---
section("6. HOST HEADER: 5V/1.5A MAX + UART   [D5, D8]", 150, 100)
place("HDR6", "J8", "HOST 1x6", 160, 116,
      {"1": "5V", "2": "5V", "3": "GND", "4": "GND",
       "5": "HOST_TX", "6": "HOST_RX"})
place("RES", "R12", "4.7k SDA pu", 185, 108, {"1": "3V3", "2": "SDA"})
place("RES", "R13", "4.7k SCL pu", 185, 116, {"1": "3V3", "2": "SCL"})

# --- section 7: accelerometer ---
section("7. LIS2DH12 ACCEL (lid angle >=20deg)   [D4]", 150, 136)
place("ACCEL", "U7", "LIS2DH12TR", 165, 158,
      {"9": "3V3", "10": "3V3", "2": "3V3", "3": "GND",
       "1": "SCL", "4": "SDA", "5": "GND", "6": "GND", "7": "GND", "8": "GND",
       "12": "ACC_INT", "11": None})
place("CAP", "C18", "100n accel", 190, 150, {"1": "3V3", "2": "GND"})
place("CAP", "C19", "22u accel", 190, 158, {"1": "3V3", "2": "GND"})

# --- section 8: capacitive controllers + electrode headers ---
# 24 electrodes: J3 inner ring pins 1-12, J4 outer ring pins 1-12, pin13 GND
# (harness shield drain). 6 electrodes per MPR121 (ADR-0004): U3=IN1-6,
# U4=IN7-12, U5=OUT1-6, U6=OUT7-12. ADDR straps 0x5A/5B/5C/5D.
MPR = [("U3", "INNER", 1, "GND", "0x5A"), ("U4", "INNER", 7, "3V3", "0x5B"),
       ("U5", "OUTER", 1, "SDA", "0x5C"), ("U6", "OUTER", 7, "SCL", "0x5D")]
section("8. CAPACITIVE: 4x MPR121, 24 ELECTRODES   [D4; layout: short stubs]", 280, 20)
for i, (ref, ring, base, addr, a2) in enumerate(MPR):
    x = 300 + (i % 2) * 130
    y = 45 + (i // 2) * 120
    nets = {"20": "3V3", "6": "GND", "4": addr,
            "5": f"VREG_{ref}", "7": f"REXT_{ref}",
            "2": "SCL", "3": "SDA", "1": f"MPR_IRQ{i+1}"}
    for e in range(12):
        nets[str(8 + e)] = f"{ring}{base + e}" if e < 6 else None
    place("MPR121", ref, f"MPR121QR2 {a2}", x, y, nets)
    place("CAP", f"C{30 + 2*i}", "100n MPR VDD", x - 32, y - 14, {"1": "3V3", "2": "GND"})
    place("CAP", f"C{31 + 2*i}", "100n VREG", x - 32, y - 6, {"1": f"VREG_{ref}", "2": "GND"})
    place("RES", f"R{20 + 2*i}", "75k REXT", x - 32, y + 2, {"1": f"REXT_{ref}", "2": "GND"})
    place("RES", f"R{21 + 2*i}", "10k IRQ pu", x - 32, y + 10, {"1": "3V3", "2": f"MPR_IRQ{i+1}"})
place("HDR13", "J3", "ELECTRODES INNER", 300, 200,
      {**{str(p): f"INNER{p}" for p in range(1, 13)}, "13": "GND"})
place("HDR13", "J4", "ELECTRODES OUTER", 430, 200,
      {**{str(p): f"OUTER{p}" for p in range(1, 13)}, "13": "GND"})


def auto_links():
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
sch = []
sch.append('(kicad_sch (version 20230121) (generator sk_generate_schematic)')
sch.append(f'  (uuid "{ROOT_UUID}")')
sch.append('  (paper "A1")')
sch.append('  (title_block (title "shitty-kitty controller") (date "2026-07-17") (rev "v1.0")')
sch.append('    (comment 1 "Cat toilet lid controller; 01_docs/ + ADRs in repo"))')
sch.append("  (lib_symbols")
sch.extend(SYMBOLS.values())
sch.append("  )")
sch.extend(LABELS)
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
(HERE.parent / "04_kicad" / "shitty_kitty.kicad_sch").write_text(content)

# symbol library file + sym-lib-table (ERC: lib_symbol_issues)
lib = ['(kicad_symbol_lib (version 20231120) (generator sk_generate_schematic)']
for name, s in SYMBOLS.items():
    lib.append(s.replace(f'(symbol "sk:{name}"', f'(symbol "{name}"', 1))
lib.append(')')
(HERE / "lib").mkdir(exist_ok=True)
(HERE / "lib" / "sk.kicad_sym").write_text("\n".join(lib) + "\n")
(HERE.parent / "04_kicad" / "sym-lib-table").write_text(
    '(sym_lib_table\n  (version 7)\n'
    '  (lib (name "sk")(type "KiCad")(uri "${KIPRJMOD}/../03_src/lib/sk.kicad_sym")(options "")(descr "project symbols"))\n)\n')

# fp-lib-table covering every referenced footprint lib
STD = "/usr/share/kicad/footprints"
libs = sorted({fp.split(":")[0] for fp in SYM_FP.values()} | {"MountingHole"})
rows = ['(fp_lib_table', '  (version 7)']
for l in libs:
    if l == "shitty_kitty":
        rows.append('  (lib (name "shitty_kitty")(type "KiCad")(uri "${KIPRJMOD}/../03_src/lib/shitty_kitty.pretty")(options "")(descr "project footprints"))')
        continue
    rows.append(f'  (lib (name "{l}")(type "KiCad")(uri "{STD}/{l}.pretty")(options "")(descr "system"))')
rows.append(')')
(HERE.parent / "04_kicad" / "fp-lib-table").write_text("\n".join(rows) + "\n")

# NEVER overwrite an existing project file — it carries DRC floors/netclasses.
if not (HERE.parent / "04_kicad" / "shitty_kitty.kicad_pro").exists():
    (HERE.parent / "04_kicad" / "shitty_kitty.kicad_pro").write_text(
        '{\n  "board": { "design_settings": {} },\n'
        '  "meta": { "filename": "shitty_kitty.kicad_pro", "version": 1 },\n'
        '  "schematic": { "legacy_lib_dir": "", "legacy_lib_list": [] }\n}\n')
print("wrote shitty_kitty.kicad_sch (+.kicad_pro);",
      f"{len(BODY)} items, {len(LABELS)} net labels, parens balanced")
