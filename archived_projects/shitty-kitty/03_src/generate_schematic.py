"""Generate 04_kicad/shitty_kitty.kicad_sch — schwriter2 declaration.

STRUCTURE ONLY (symbols, cells+nets, regions, rows, chains); the schwriter2
engine computes every coordinate (text envelopes = courtyards, internal
S-OCCL == 0 gate), draws the story-critical chains as real wires (canon S6),
renders GND pins as ground power symbols (+ the single PWR_FLAG), and emits
no_connect flags at every explicit-None pin.

Pin numbers are PHYSICAL PADS from 02_parts/<MPN>/part.yaml (each cites its
datasheet figure): ESP32-S3-WROOM-1 fig 3-1 p.10 v1.8; TMC2209 fig 2.1 p.9
rev1.09; MPR121QR2 pin fig rev4; LIS2DH12 fig 2 p.8; AP63205 DS41326 p.1;
AOD4185 p.1 (1=G 2=D/tab 3=S); SMBJ16A pad1=cathode; DC-005C-20A (1=tip+
2=sleeve 3=switch); AMS1117 p.1; USBLC6 UMW p.1. Circuit per
01_docs/ARCHITECTURE.md + DETAIL_DESIGN.md; decisions D1-D10 + ADRs.
Run: python3 03_src/generate_schematic.py  (writes into 04_kicad/)
"""

import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parents[2] / "skills" / "kicad-pcb" / "scripts"))
from schwriter2 import Schematic  # noqa: E402

PROJECT = "shitty_kitty"
SMALL = {"RES", "CAP", "CAPP", "LED", "SW", "TERM2", "FUSE", "IND", "TVS", "RES1206"}

rev = Schematic.rev_from_git(HERE, "SK_REV", "sk-v*").replace("sk-", "")
sch = Schematic(
    PROJECT, "shitty-kitty controller", paper="A1",
    comment="Cat toilet lid controller: ESP32-S3 + TMC2209 + 4x MPR121 + LIS2DH12; 01_docs/ + ADRs in repo",
    rev=rev, small_syms=SMALL, libname="sk")

# ------------------------------------------------------------------ symbols
sch.defsym("RES", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="R")
sch.defsym("RES1206", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="R")
sch.defsym("CAP", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="C")
# polarized electrolytic: pad 1 = POSITIVE (part.yaml RVT100UF25V67RV0011)
sch.defsym("CAPP", 7.62, 5.08, [("1", "+", "L", 0), ("2", "-", "R", 0)], ref="C")
sch.defsym("LED", 7.62, 5.08, [("1", "K", "L", 0), ("2", "A", "R", 0)], ref="D")  # pad1 = cathode
sch.defsym("SW", 7.62, 7.62, [("1", "1", "L", 0), ("2", "2", "L", 1)], ref="SW")
sch.defsym("TERM2", 7.62, 7.62, [("1", "P1", "L", 0), ("2", "P2", "L", 1)], ref="J")
sch.defsym("FUSE", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="F")
sch.defsym("IND", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="L")
# TVS unidirectional SMB: pad 1 = CATHODE (band; part.yaml SMBJ16A)
sch.defsym("TVS", 7.62, 5.08, [("1", "K", "L", 0), ("2", "A", "R", 0)], ref="D")
# DC-005C-20A barrel jack (part.yaml): 1=tip(+12V), 2=sleeve(GND), 3=switch
sch.defsym("BARREL", 10.16, 10.16,
           [("1", "TIP+", "R", 0), ("3", "SW", "R", 1), ("2", "SLEEVE", "R", 2)], ref="J")
# AOD4185 P-FET TO-252 (part.yaml: 1=G 2=D/tab 3=S). Reverse-polarity
# high-side: INPUT on the drain, LOAD on the source, gate pulled to GND.
sch.defsym("PFET", 10.16, 12.7,
           [("2", "D", "L", 0), ("1", "G", "L", 3), ("3", "S", "R", 0)], ref="Q")
sch.defsym("HDR6", 7.62, 17.78, [("1", "5V", "L", 0), ("2", "5V", "L", 1), ("3", "GND", "L", 2),
                                 ("4", "GND", "L", 3), ("5", "TX", "L", 4), ("6", "RX", "L", 5)], ref="J")
sch.defsym("HDR13", 7.62, 35.56, [(str(i), f"P{i}", "L", i - 1) for i in range(1, 14)], ref="J")
# XH4 slots 0,1,3,4 mirror the TMC2209 output slots so the motor phases draw
# as four straight wires (T1) once chained.
sch.defsym("XH4", 7.62, 15.24, [("1", "A1", "L", 0), ("2", "A2", "L", 1),
                                ("3", "B1", "L", 3), ("4", "B2", "L", 4)], ref="J")
sch.defsym("USBC", 15.24, 33.02,
           [("A4", "VBUS", "L", 0), ("A9", "VBUS", "L", 1), ("B4", "VBUS", "L", 2), ("B9", "VBUS", "L", 3),
            ("A5", "CC1", "L", 5), ("B5", "CC2", "L", 6),
            ("A1", "GND", "L", 8), ("A12", "GND", "L", 9), ("B1", "GND", "L", 10), ("B12", "GND", "L", 11),
            ("A6", "D+", "R", 0), ("A7", "D-", "R", 1), ("B6", "D+", "R", 2), ("B7", "D-", "R", 3),
            ("A8", "SBU1", "R", 5), ("B8", "SBU2", "R", 6), ("SH", "SHIELD", "R", 9)], ref="J")
sch.defsym("USBLC6", 10.16, 17.78,
           [("1", "I/O1", "L", 0), ("3", "I/O2", "L", 2), ("2", "GND", "L", 5),
            ("6", "I/O1'", "R", 0), ("4", "I/O2'", "R", 2), ("5", "VBUS", "R", 5)], ref="D")
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
sch.defsym("AMS1117", 12.7, 12.7,
           [("3", "VIN", "L", 0), ("1", "GND", "L", 3), ("2", "VOUT", "R", 0)], ref="U")
# TMC2209-LA-T QFN28 (02_parts/TMC2209-LA-T/part.yaml, fig 2.1 p.9 rev1.09)
sch.defsym("TMC2209", 25.4, 58.42,
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
# MPR121QR2 UQFN-20 no EP (02_parts/MPR121QR2/part.yaml)
sch.defsym("MPR121", 20.32, 40.64,
           [("20", "VDD", "L", 0), ("5", "VREG", "L", 2), ("4", "ADDR", "L", 4),
            ("2", "SCL", "L", 6), ("3", "SDA", "L", 7), ("1", "IRQ", "L", 9),
            ("7", "REXT", "L", 11), ("6", "VSS", "L", 13)] +
           [(str(8 + i), f"ELE{i}", "R", i) for i in range(12)], ref="U")
# LIS2DH12 LGA-12 (02_parts/LIS2DH12TR/part.yaml)
sch.defsym("ACCEL", 15.24, 35.56,
           [("9", "VDD", "L", 0), ("10", "VDD_IO", "L", 1), ("2", "CS", "L", 3),
            ("3", "SA0", "L", 4), ("1", "SCL", "L", 6), ("4", "SDA", "L", 7),
            ("5", "RES", "L", 9), ("6", "GND", "L", 10), ("7", "GND", "L", 11),
            ("8", "GND", "L", 12),
            ("12", "INT1", "R", 0), ("11", "INT2", "R", 2)], ref="U")
# AP63205WU-7 TSOT-23-6 (02_parts/AP63205WU-7/part.yaml, DS41326 p.1):
# 1=FB (fixed: wire DIRECTLY to VOUT), 2=EN (ties to VIN), 3=VIN, 4=GND, 5=SW, 6=BST
sch.defsym("BUCK", 12.7, 17.78,
           [("3", "VIN", "L", 0), ("2", "EN", "L", 2), ("4", "GND", "L", 4),
            ("5", "SW", "R", 0), ("6", "BST", "R", 2), ("1", "FB/VOUT", "R", 4)], ref="U")

# ------------------------------------------------------------------ footprints
sch.sym_fp = {
    "RES": "Resistor_SMD:R_0805_2012Metric",
    "RES1206": "Resistor_SMD:R_1206_3216Metric",
    "CAP": "Capacitor_SMD:C_0805_2012Metric",
    "CAPP": "Capacitor_SMD:CP_Elec_6.3x7.7",
    "LED": "LED_SMD:LED_0805_2012Metric",
    "SW": "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A",
    "TERM2": "shitty_kitty:TerminalBlock_3.5-2P_NoSilk",
    "FUSE": "Fuse:Fuse_1812_4532Metric",
    "IND": "Inductor_SMD:L_Sunlord_SWPA6045S",
    "TVS": "Diode_SMD:D_SMB",
    "BARREL": "shitty_kitty:DCJack_DC005_Horizontal",  # vendored (make_lib.py; stock KiCad holes mismatch the drawing)
    "PFET": "Package_TO_SOT_SMD:TO-252-2",
    "HDR6": "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical",
    "HDR13": "Connector_PinHeader_2.54mm:PinHeader_1x13_P2.54mm_Vertical",
    "XH4": "Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical",
    "USBC": "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
    "USBLC6": "Package_TO_SOT_SMD:SOT-23-6",
    "ESP32S3": "shitty_kitty:ESP32-S3-WROOM-1",  # vendored (make_lib.py)
    "AMS1117": "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
    "TMC2209": "Package_DFN_QFN:QFN-28-1EP_5x5mm_P0.5mm_EP3.75x3.75mm",
    "MPR121": "Package_DFN_QFN:UQFN-20_3x3mm_P0.4mm",
    "ACCEL": "Package_LGA:LGA-12_2x2mm_P0.5mm",
    "BUCK": "Package_TO_SOT_SMD:TSOT-23-6",
}

# ═══════════════════ circuit: structure only ═══════════════════

# --- region 1: 12V entry + protection (ADR-0001) ---
sch.region("1. 12V INPUT: barrel -> 2A polyfuse -> P-FET revpol -> SMBJ16A TVS   [ADR-0001]")
sch.row(("BARREL", "J1", "DC-005C-20A 12V", {"1": "VIN_RAW", "2": "GND", "3": "GND"}),
        ("FUSE", "F1", "2A polyfuse 16V", {"1": "VIN_RAW", "2": "VIN_F"}),
        ("PFET", "Q1", "AOD4185 revpol", {"1": "GATE_Q1", "2": "VIN_F", "3": "VIN_12V"}),
        ("TVS", "D3", "SMBJ16A", {"1": "VIN_12V", "2": "GND"}))
sch.chain("J1.1", "F1.1")   # tip -> fuse: the power-entry story, drawn
sch.chain("F1.2", "Q1.2")   # fuse -> P-FET drain (input side)
sch.chain("Q1.3", "D3.1")   # source -> protected rail at the TVS cathode
sch.row(("RES", "R1", "100k gate pd", {"1": "GATE_Q1", "2": "GND"}),
        ("CAPP", "C40", "100u 12V bulk", {"1": "VIN_12V", "2": "GND"}),
        ("CAP", "C25", "100n 12V", {"1": "VIN_12V", "2": "GND"}))

# --- region 2: buck + LDO (D5, ADR-0004) ---
sch.region("2. POWER: AP63205 12V->5V 2A (host 1.5A max); AMS1117 -> 3V3   [D5]")
sch.row(("CAP", "C1", "4.7u buck in", {"1": "VIN_12V", "2": "GND"}),
        ("BUCK", "U8", "AP63205WU-7",
         {"3": "VIN_12V", "2": "VIN_12V", "4": "GND",
          "5": "SW_BUCK", "6": "BST", "1": "5V"}),
        ("IND", "L1", "10uH SWPA6045S", {"1": "SW_BUCK", "2": "5V"}),
        ("CAP", "C3", "22u buck out", {"1": "5V", "2": "GND"}))
sch.chain("U8.5", "L1.1")   # SW node -> inductor: the buck story, drawn
sch.chain("L1.2", "C3.1")   # inductor -> first output cap
sch.row(("CAP", "C2", "4.7u buck in", {"1": "VIN_12V", "2": "GND"}),
        ("CAP", "C4", "22u buck out", {"1": "5V", "2": "GND"}),
        ("CAP", "C5", "100n BST", {"1": "BST", "2": "SW_BUCK"}))
sch.row(("CAP", "C6", "4.7u LDO in", {"1": "5V", "2": "GND"}),
        ("AMS1117", "U9", "AMS1117-3.3", {"3": "5V", "1": "GND", "2": "3V3"}),
        ("CAP", "C7", "22u LDO out", {"1": "3V3", "2": "GND"}))
sch.chain("U9.2", "C7.1")
sch.row(("RES", "R3", "1k LED", {"1": "3V3", "2": "LED_A"}),
        ("LED", "D2", "green PWR", {"1": "GND", "2": "LED_A"}))

# --- region 3: USB-C programming (data only) ---
sch.region("3. USB-C PROGRAMMING (data only; board powers from 12V)")
sch.row(("USBC", "J2", "TYPE-C-31-M-12",
         {"A4": "USB_VBUS", "A9": "USB_VBUS", "B4": "USB_VBUS", "B9": "USB_VBUS",
          "A5": "CC1", "B5": "CC2",
          "A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND",
          "A6": "USB_DP", "A7": "USB_DM", "B6": "USB_DP", "B7": "USB_DM",
          "A8": None, "B8": None, "SH": "GND"}),
        ("USBLC6", "D1", "USBLC6-2SC6",
         {"1": "USB_DP", "6": "USB_DP", "3": "USB_DM", "4": "USB_DM",
          "2": "GND", "5": "USB_VBUS"}))
sch.chain("J2.A6", "D1.1")
sch.row(("RES", "R4", "5.1k CC1", {"1": "CC1", "2": "GND"}),
        ("RES", "R5", "5.1k CC2", {"1": "CC2", "2": "GND"}),
        ("CAP", "C8", "100n VBUS", {"1": "USB_VBUS", "2": "GND"}))

# --- region 4: MCU ---
sch.region("4. ESP32-S3-WROOM-1 (native USB; pin map ARCHITECTURE.md)")
sch.row(("CAP", "C9", "22u MCU 3V3", {"1": "3V3", "2": "GND"}),
        ("CAP", "C10", "100n MCU 3V3", {"1": "3V3", "2": "GND"}))
sch.row(("RES", "R6", "10k EN", {"1": "3V3", "2": "EN"}),
        ("CAP", "C11", "1u EN", {"1": "EN", "2": "GND"}))
sch.row(("SW", "SW2", "TS-1187A RESET", {"1": "EN", "2": "GND"}),
        ("SW", "SW1", "TS-1187A BOOT", {"1": "BOOT", "2": "GND"}))
sch.row(("ESP32S3", "U1", "ESP32-S3-WROOM-1-N8R2",
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
          "31": None, "32": None, "33": None, "34": None, "35": None}))
sch.row(("RES", "R7", "1k status LED", {"1": "LED_ST", "2": "LED_SA"}),
        ("LED", "D5", "green STATUS", {"1": "GND", "2": "LED_SA"}))

# --- region 5: motor driver + motor/endstop (ADR-0002, D9, D10) ---
sch.region("5. TMC2209: quiet StealthChop, UART, MOTOR OFF AT BOOT (R8)   [ADR-0002]")
sch.row(("CAPP", "C41", "100u VS bulk", {"1": "VIN_12V", "2": "GND"}),
        ("TMC2209", "U2", "TMC2209-LA-T",
         {"22": "VIN_12V", "28": "VIN_12V",
          "6": "VCP", "4": "CPO", "5": "CPI",
          "8": "V5OUT", "15": "3V3",
          "2": "ENN", "16": "STEP", "19": "DIR",
          "9": "GND", "10": "GND", "7": "GND", "13": "GND",
          "20": None, "17": None, "25": None,
          "24": "MOT_A1", "21": "MOT_A2", "26": "MOT_B1", "1": "MOT_B2",
          "23": "BRA", "27": "BRB",
          "14": "TMC_UART", "11": "DIAG", "12": "INDEX",
          "3": "GND", "18": "GND", "29": "GND"}),
        ("XH4", "J5", "MOTOR NEMA17",
         {"1": "MOT_A1", "2": "MOT_A2", "3": "MOT_B1", "4": "MOT_B2"}))
sch.chain("U2.24", "J5.1")  # OA1 -> motor pin A1; OA2/OB1/OB2 align + auto-wire
sch.row(("RES", "R8", "10k ENN pu", {"1": "3V3", "2": "ENN"}),
        ("RES", "R9", "1k TMC UART", {"1": "TMC_TX", "2": "TMC_UART"}),
        ("CAP", "C12", "100n VCP", {"1": "VCP", "2": "VIN_12V"}),
        ("CAP", "C26", "22n CP fly", {"1": "CPO", "2": "CPI"}))
sch.row(("CAP", "C13", "4.7u 5VOUT", {"1": "V5OUT", "2": "GND"}),
        ("CAP", "C16", "100n VCC_IO", {"1": "3V3", "2": "GND"}),
        ("CAP", "C14", "100n VS", {"1": "VIN_12V", "2": "GND"}),
        ("CAP", "C15", "100n VS", {"1": "VIN_12V", "2": "GND"}))
sch.row(("RES1206", "R30", "0.15R sense A", {"1": "BRA", "2": "GND"}),
        ("RES1206", "R31", "0.15R sense B", {"1": "BRB", "2": "GND"}))
sch.row(("RES", "R10", "10k endstop pu", {"1": "3V3", "2": "ENDSTOP_N"}),
        ("CAP", "C17", "100n endstop", {"1": "ENDSTOP_N", "2": "GND"}),
        ("RES", "R11", "1k endstop ser", {"1": "ENDSTOP_N", "2": "ENDSTOP_G"}),
        ("TERM2", "J6", "ENDSTOP TERM", {"1": "ENDSTOP_N", "2": "GND"}))
sch.chain("R10.2", "C17.1")  # debounce node, drawn

# --- region 6: host header (D5, D8) ---
sch.region("6. HOST HEADER: 5V/1.5A MAX + UART; I2C bus pullups   [D8]")
sch.row(("HDR6", "J8", "HOST 1x6", {"1": "5V", "2": "5V", "3": "GND", "4": "GND",
                                    "5": "HOST_TX", "6": "HOST_RX"}))
sch.row(("RES", "R12", "4.7k SDA pu", {"1": "3V3", "2": "SDA"}),
        ("RES", "R13", "4.7k SCL pu", {"1": "3V3", "2": "SCL"}))

# --- region 7: accelerometer (D4) ---
sch.region("7. LIS2DH12 ACCEL: lid angle >= 20deg rule   [D4]")
sch.row(("ACCEL", "U7", "LIS2DH12TR",
         {"9": "3V3", "10": "3V3", "2": "3V3", "3": "GND",
          "1": "SCL", "4": "SDA", "5": "GND", "6": "GND", "7": "GND", "8": "GND",
          "12": "ACC_INT", "11": None}),
        ("CAP", "C18", "100n accel", {"1": "3V3", "2": "GND"}),
        ("CAP", "C19", "22u accel", {"1": "3V3", "2": "GND"}))

# --- region 8: capacitive controllers + electrode headers (D4) ---
# 24 electrodes: inner ring J3 pins 1-12, outer ring J4 pins 1-12, pin13 GND.
# 6 electrodes per MPR121: U3=IN1-6, U4=IN7-12, U5=OUT1-6, U6=OUT7-12.
# ADDR straps (datasheet address table): GND=0x5A, VDD=0x5B, SDA=0x5C, SCL=0x5D.
sch.region("8. CAPACITIVE: 4x MPR121QR2, 24 ELECTRODE LINES (short stubs!)   [D4]")


def mpr(ref, ring, base, addr_net, addr_str, irq):
    nets = {"20": "3V3", "6": "GND", "4": addr_net,
            "5": f"VREG_{ref}", "7": f"REXT_{ref}",
            "2": "SCL", "3": "SDA", "1": irq}
    for e in range(12):
        nets[str(8 + e)] = f"{ring}{base + e}" if e < 6 else None
    return ("MPR121", ref, f"MPR121QR2 {addr_str}", nets)


sch.row(mpr("U3", "INNER", 1, "GND", "0x5A", "MPR_IRQ1"),
        ("HDR13", "J3", "ELECTRODES INNER",
         {**{str(p): f"INNER{p}" for p in range(1, 13)}, "13": "GND"}))
sch.chain("U3.8", "J3.1")   # INNER1 stub drawn; INNER2-6 align + auto-wire
sch.row(("CAP", "C30", "100n MPR VDD", {"1": "3V3", "2": "GND"}),
        ("CAP", "C31", "100n VREG", {"1": "VREG_U3", "2": "GND"}),
        ("RES", "R20", "75k REXT", {"1": "REXT_U3", "2": "GND"}),
        ("RES", "R21", "10k IRQ pu", {"1": "3V3", "2": "MPR_IRQ1"}))
sch.row(mpr("U4", "INNER", 7, "3V3", "0x5B", "MPR_IRQ2"))
sch.row(("CAP", "C32", "100n MPR VDD", {"1": "3V3", "2": "GND"}),
        ("CAP", "C33", "100n VREG", {"1": "VREG_U4", "2": "GND"}),
        ("RES", "R22", "75k REXT", {"1": "REXT_U4", "2": "GND"}),
        ("RES", "R23", "10k IRQ pu", {"1": "3V3", "2": "MPR_IRQ2"}))
sch.row(mpr("U5", "OUTER", 1, "SDA", "0x5C", "MPR_IRQ3"),
        ("HDR13", "J4", "ELECTRODES OUTER",
         {**{str(p): f"OUTER{p}" for p in range(1, 13)}, "13": "GND"}))
sch.chain("U5.8", "J4.1")   # OUTER1 stub drawn; OUTER2-6 align + auto-wire
sch.row(("CAP", "C34", "100n MPR VDD", {"1": "3V3", "2": "GND"}),
        ("CAP", "C35", "100n VREG", {"1": "VREG_U5", "2": "GND"}),
        ("RES", "R24", "75k REXT", {"1": "REXT_U5", "2": "GND"}),
        ("RES", "R25", "10k IRQ pu", {"1": "3V3", "2": "MPR_IRQ3"}))
sch.row(mpr("U6", "OUTER", 7, "SCL", "0x5D", "MPR_IRQ4"))
sch.row(("CAP", "C36", "100n MPR VDD", {"1": "3V3", "2": "GND"}),
        ("CAP", "C37", "100n VREG", {"1": "VREG_U6", "2": "GND"}),
        ("RES", "R26", "75k REXT", {"1": "REXT_U6", "2": "GND"}),
        ("RES", "R27", "10k IRQ pu", {"1": "3V3", "2": "MPR_IRQ4"}))

# ------------------------------------------------------------------ emit + side files
content = sch.emit()
out = HERE.parent / "04_kicad"
out.mkdir(exist_ok=True)
(out / f"{PROJECT}.kicad_sch").write_text(content)

(HERE / "lib").mkdir(exist_ok=True)
sch.write_symbol_lib(HERE / "lib" / "sk.kicad_sym")
(out / "sym-lib-table").write_text(
    sch.sym_lib_table("sk", "${KIPRJMOD}/../03_src/lib/sk.kicad_sym"))
(out / "fp-lib-table").write_text(sch.fp_lib_table(
    {"shitty_kitty": "${KIPRJMOD}/../03_src/lib/shitty_kitty.pretty"}))

# NEVER overwrite an existing project file — it carries DRC floors/netclasses.
if not (out / f"{PROJECT}.kicad_pro").exists():
    (out / f"{PROJECT}.kicad_pro").write_text(
        '{\n  "board": { "design_settings": {} },\n'
        f'  "meta": {{ "filename": "{PROJECT}.kicad_pro", "version": 1 }},\n'
        '  "schematic": { "legacy_lib_dir": "", "legacy_lib_list": [] }\n}\n')

nlabels = content.count("(global_label")
print(f"wrote {PROJECT}.kicad_sch via schwriter2: {len(sch.cells)} cells, "
      f"{len(sch.wires)} wires, {nlabels} net labels, internal S-OCCL 0, parens balanced")
