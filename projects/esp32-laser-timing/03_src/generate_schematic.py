"""Generate 04_kicad/esp32_laser_timing.kicad_sch — schwriter2 port.

The author declares STRUCTURE ONLY (symbols, cells+nets, regions, rows,
chains); the schwriter2 engine computes every coordinate from text envelopes
(label plates, refs, values are the schematic's courtyards), wires the
story-critical facing pins (canon S6), and gates itself on an internal
S-OCCL == 0 before writing. No hand coordinates anywhere in this file.

Pin numbers are PHYSICAL PADS from 02_parts/<MPN>/part.yaml (each cites its
datasheet figure): ESP32-S3-WROOM-1 fig 3-1 p.10 v1.8; LM339DT fig 1 p.3
(DocID2159 rev4); AO3400A p.1 (G/S/D); AMS1117 fixed p.1 (1=GND,2=VOUT+tab,
3=VIN); USBLC6 UMW p.1. Circuit per 01_docs/ARCHITECTURE.md + DETAIL_DESIGN.md;
decisions in 01_docs/decisions/ (D1-D15 in BRIEF.md). Net assignments are
copied MECHANICALLY from the pre-port generator (netlist parity is a gate).
Run: python3 03_src/generate_schematic.py  (writes into 04_kicad/)
"""

import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parents[2] / "skills" / "kicad-pcb" / "scripts"))
from schwriter2 import Schematic  # noqa: E402

PROJECT = "esp32_laser_timing"
SMALL = {"RES", "CAP", "CAPP", "LED", "SW", "TP", "TERM2"}

rev = Schematic.rev_from_git(HERE, "ELT_REV", "elt-v*").replace("elt-", "")
sch = Schematic(
    PROJECT, "esp32-laser-timing", paper="A2",
    comment="Laser interruption timing bench controller; 01_docs/ + ADRs in repo",
    rev=rev, small_syms=SMALL)
sch.no_bom_syms = {"TP"}  # TPs: exclude-from-BOM on BOTH sides (parity)

# ------------------------------------------------------------------ symbols
sch.defsym("RES", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="R")
sch.defsym("CAP", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="C")
# polarized electrolytic: pad 1 = POSITIVE (KiCad CP_Elec convention, part.yaml RVT100UF16V67RV0016)
sch.defsym("CAPP", 7.62, 5.08, [("1", "+", "L", 0), ("2", "-", "R", 0)], ref="C")
sch.defsym("LED", 7.62, 5.08, [("1", "K", "L", 0), ("2", "A", "R", 0)], ref="D")  # pad1 = cathode
sch.defsym("TP", 5.08, 5.08, [("1", "1", "L", 0)], ref="TP")
sch.defsym("SW", 7.62, 7.62, [("1", "1", "L", 0), ("2", "2", "L", 1)], ref="SW")
sch.defsym("TERM2", 7.62, 7.62, [("1", "P1", "L", 0), ("2", "P2", "L", 1)], ref="J")
sch.defsym("HDR4", 7.62, 12.7, [("1", "GND", "L", 0), ("2", "VCC", "L", 1),
                                ("3", "SCL", "L", 2), ("4", "SDA", "L", 3)], ref="J")
# HRO TYPE-C-31-M-12 16P receptacle, sink (UFP). Pad names = KiCad footprint pads
sch.defsym("USBC", 15.24, 33.02,
           [("A4", "VBUS", "L", 0), ("A9", "VBUS", "L", 1), ("B4", "VBUS", "L", 2), ("B9", "VBUS", "L", 3),
            ("A5", "CC1", "L", 5), ("B5", "CC2", "L", 6),
            ("A1", "GND", "L", 8), ("A12", "GND", "L", 9), ("B1", "GND", "L", 10), ("B12", "GND", "L", 11),
            ("A6", "D+", "R", 0), ("A7", "D-", "R", 1), ("B6", "D+", "R", 2), ("B7", "D-", "R", 3),
            ("A8", "SBU1", "R", 5), ("B8", "SBU2", "R", 6), ("SH", "SHIELD", "R", 9)], ref="J")
# USBLC6-2SC6 SOT-23-6 (UMW datasheet pinning, p1): 1 I/O1, 2 GND, 3 I/O2, 4 I/O2, 5 VBUS, 6 I/O1
sch.defsym("USBLC6", 10.16, 17.78,
           [("1", "I/O1", "L", 0), ("3", "I/O2", "L", 2), ("2", "GND", "L", 5),
            ("6", "I/O1'", "R", 0), ("4", "I/O2'", "R", 2), ("5", "VBUS", "R", 5)], ref="D")
# ESP32-S3-WROOM-1 (fig 3-1 p.10 v1.8): all 41 physical pads.
sch.defsym("ESP32S3", 30.48, 58.42,
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
sch.defsym("LM339", 15.24, 38.1,
           [("5", "IN1+", "L", 0), ("4", "IN1-", "L", 1),
            ("7", "IN2+", "L", 3), ("6", "IN2-", "L", 4),
            ("9", "IN3+", "L", 6), ("8", "IN3-", "L", 7),
            ("11", "IN4+", "L", 9), ("10", "IN4-", "L", 10),
            ("3", "VCC", "R", 0), ("2", "OUT1", "R", 3), ("1", "OUT2", "R", 5),
            ("14", "OUT3", "R", 7), ("13", "OUT4", "R", 9), ("12", "GND", "R", 12)],
           ref="U")
# AO3400A SOT-23 (rev3.1 p.1): 1=G 2=S 3=D
sch.defsym("NFET", 10.16, 12.7,
           [("1", "G", "L", 1), ("3", "D", "R", 0), ("2", "S", "R", 3)], ref="Q")
# AMS1117-3.3 SOT-223 fixed (ds1117 p.1): 1=GND 2=VOUT(+tab) 3=VIN
sch.defsym("AMS1117", 12.7, 12.7,
           [("3", "VIN", "L", 0), ("1", "GND", "L", 3), ("2", "VOUT", "R", 0)], ref="U")

# ------------------------------------------------------------------ footprints
sch.sym_fp = {
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

# ═══════════════════ circuit: structure only, nets verbatim ═══════════════════

# --- region 1: USB entry ---
sch.region("1. USB-C INPUT (UFP sink, 5V + native USB)   [ADR-0001]")
sch.row(("USBC", "J1", "TYPE-C-31-M-12",
         {"A4": "5V", "A9": "5V", "B4": "5V", "B9": "5V",
          "A5": "CC1", "B5": "CC2",
          "A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND",
          "A6": "USB_DP", "A7": "USB_DM", "B6": "USB_DP", "B7": "USB_DM",
          "A8": None, "B8": None, "SH": "GND"}),
        ("USBLC6", "D1", "USBLC6-2SC6",
         {"1": "USB_DP", "6": "USB_DP", "3": "USB_DM", "4": "USB_DM",
          "2": "GND", "5": "5V"}))
sch.chain("J1.A6", "D1.1")  # USB D+ story wire into the ESD array
sch.row(("RES", "R1", "5.1k CC1", {"1": "CC1", "2": "GND"}),
        ("RES", "R2", "5.1k CC2", {"1": "CC2", "2": "GND"}))

# --- region 2: power ---
sch.region("2. POWER: 5V -> AMS1117 -> 3V3; bulk at lasers   [P4]")
sch.row(("CAP", "C2", "22u LDO in", {"1": "5V", "2": "GND"}),
        ("AMS1117", "U2", "AMS1117-3.3", {"3": "5V", "1": "GND", "2": "3V3"}),
        ("CAP", "C3", "22u LDO out", {"1": "3V3", "2": "GND"}))
sch.chain("U2.2", "C3.1")  # LDO out -> output cap (C2->U2 facing nets differ: labels)
sch.row(("CAPP", "C11", "100u 5V bulk", {"1": "5V", "2": "GND"}),
        ("CAP", "C12", "100n 5V bulk", {"1": "5V", "2": "GND"}))
sch.row(("RES", "R4", "1k LED", {"1": "3V3", "2": "LED_A"}),
        ("LED", "D2", "green PWR", {"1": "GND", "2": "LED_A"}))  # pad1 = cathode
sch.row(("TP", "TP4", "TP 5V", {"1": "5V"}),
        ("TP", "TP5", "TP 3V3", {"1": "3V3"}),
        ("TP", "TP6", "TP GND", {"1": "GND"}))

# --- region 3: MCU ---
sch.region("3. ESP32-S3-WROOM-1 (native USB; pin map ADR-0004)")
sch.row(("CAP", "C4", "22u MCU 3V3", {"1": "3V3", "2": "GND"}),
        ("CAP", "C5", "100n MCU 3V3", {"1": "3V3", "2": "GND"}))
sch.row(("RES", "R3", "10k EN", {"1": "3V3", "2": "EN"}),
        ("CAP", "C1", "1u EN", {"1": "EN", "2": "GND"}))  # T1 auto-wires the EN node
sch.row(("SW", "SW2", "TS-1187A RESET", {"1": "EN", "2": "GND"}),
        ("SW", "SW1", "TS-1187A BOOT", {"1": "BOOT", "2": "GND"}))
sch.row(("ESP32S3", "U1", "ESP32-S3-WROOM-1-N8R2",
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
          "36": None, "37": None}))

# --- region 4: laser channels ---
sch.region("4. LASER CHANNELS x3: low-side AO3400A, off at boot   [P5]")
for i, (q, rs, rp, jt, gpio) in enumerate([
        ("Q1", "R10", "R11", "J4", "LDRV1"),
        ("Q2", "R12", "R13", "J5", "LDRV2"),
        ("Q3", "R14", "R15", "J6", "LDRV3")]):
    n = i + 1
    sch.row(("RES", rp, "100k gate pd", {"1": f"GATE{n}", "2": "GND"}),
            ("RES", rs, "100R gate", {"1": gpio, "2": f"GATE{n}"}),
            ("NFET", q, "AO3400A", {"1": f"GATE{n}", "3": f"LSW{n}", "2": "GND"}),
            ("TERM2", jt, f"LASER {n} TERM", {"1": "5V", "2": f"LSW{n}"}))
    sch.chain(f"{rs}.2", f"{q}.1")   # GPIO -> series R -> gate: drawn
    sch.chain(f"{q}.3", f"{jt}.2")   # drain -> laser terminal: drawn

# --- region 5: photodiode comparators ---
sch.region("5. PHOTODIODE CHANNELS x3: BPW34 -> 1k load -> LM339 @5V   [P6, ADR-0002]")
for i in range(3):
    n = i + 1
    sch.row(("TERM2", f"J{7+i}", f"PHOTODIODE {n} TERM", {"1": "5V", "2": f"PD{n}"}),
            ("RES", f"R{20+i}", "1k PD load", {"1": f"PD{n}", "2": "GND"}))
sch.row(("LM339", "U3", "LM339DT",
         {"5": "PD1", "4": "VTH1", "2": "COMP1",
          "7": "PD2", "6": "VTH2", "1": "COMP2",
          "9": "PD3", "8": "VTH3", "14": "COMP3",
          "11": "GND", "10": "VTH3", "13": None,   # spare comparator: +IN=GND, -IN=VTH3 (0.7V, defined; adjacent pad => routable at signal width; D13)
          "3": "5V", "12": "GND"}),
        ("CAP", "C6", "100n LM339", {"1": "5V", "2": "GND"}))
sch.chain("U3.3", "C6.1")  # VCC -> decoupler, drawn adjacent (canon S7)
for i in range(3):
    n = i + 1
    sch.row(("RES", f"R{23+i}", "10k div top", {"1": "3V3", "2": f"VTH{n}"}),
            ("RES", f"R{26+i}", "2.7k div bot", {"1": f"VTH{n}", "2": "GND"}),
            ("RES", f"R{29+i}", "33k hyst", {"1": f"PD{n}", "2": f"COMP{n}"}),
            ("RES", f"R{32+i}", "10k comp pu", {"1": "3V3", "2": f"COMP{n}"}))
    sch.chain(f"R{23+i}.2", f"R{26+i}.1")  # threshold divider chain, drawn
sch.row(("TP", "TP1", "TP COMP1", {"1": "COMP1"}),
        ("TP", "TP2", "TP COMP2", {"1": "COMP2"}),
        ("TP", "TP3", "TP COMP3", {"1": "COMP3"}))

# --- region 6: buttons ---
sch.region("6. BUTTON CHANNELS x3: 10k pu / 100n / 1k series   [P9]")
for i in range(3):
    n = i + 1
    sch.row(("TERM2", f"J{10+i}", f"BUTTON {n} TERM", {"1": f"BTN{n}_N", "2": "GND"}),
            ("RES", f"R{40+i}", "10k btn pu", {"1": "3V3", "2": f"BTN{n}_N"}),
            ("CAP", f"C{8+i}", "100n btn", {"1": f"BTN{n}_N", "2": "GND"}),
            ("RES", f"R{43+i}", "1k btn ser", {"1": f"BTN{n}_N", "2": f"BTN{n}_G"}))
    sch.chain(f"R{40+i}.2", f"C{8+i}.1")  # debounce node, drawn

# --- region 7: OLED ---
sch.region("7. OLED HEADER (GND VCC SCL SDA - CHECK MODULE PINOUT)   [P8]")
sch.row(("HDR4", "J2", "OLED HDR 1x4F", {"1": "GND", "2": "3V3", "3": "SCL", "4": "SDA"}),
        ("CAP", "C7", "100n OLED", {"1": "3V3", "2": "GND"}))
sch.row(("RES", "R50", "4.7k SDA pu", {"1": "3V3", "2": "SDA"}),
        ("RES", "R51", "4.7k SCL pu", {"1": "3V3", "2": "SCL"}))

# ------------------------------------------------------------------ emit + side files
content = sch.emit()  # layout + wire-safety + internal S-OCCL gates inside
out = HERE.parent / "04_kicad"
out.mkdir(exist_ok=True)
(out / f"{PROJECT}.kicad_sch").write_text(content)

(HERE / "lib").mkdir(exist_ok=True)
sch.write_symbol_lib(HERE / "lib" / "elt.kicad_sym")
(out / "sym-lib-table").write_text(
    sch.sym_lib_table("elt", "${KIPRJMOD}/../03_src/lib/elt.kicad_sym"))
(out / "fp-lib-table").write_text(sch.fp_lib_table(
    {"esp32_laser_timing": "${KIPRJMOD}/../03_src/lib/esp32_laser_timing.pretty"}))

# NEVER overwrite an existing project file — it carries DRC floors/netclasses.
if not (out / f"{PROJECT}.kicad_pro").exists():
    (out / f"{PROJECT}.kicad_pro").write_text(
        '{\n  "board": { "design_settings": {} },\n'
        f'  "meta": {{ "filename": "{PROJECT}.kicad_pro", "version": 1 }},\n'
        '  "schematic": { "legacy_lib_dir": "", "legacy_lib_list": [] }\n}\n')

nlabels = content.count("(global_label")
print(f"wrote {PROJECT}.kicad_sch via schwriter2: {len(sch.cells)} cells, "
      f"{len(sch.wires)} wires, {nlabels} net labels, internal S-OCCL 0, parens balanced")
