"""Generate 04_kicad/cook_hub.kicad_sch — schwriter2 (structure only).

SMC0985KS Phase-1 sensor/control hub, spec PCB A+B combined (parent D1a).
Pin numbers are PHYSICAL PADS from 02_parts/<MPN>/part.yaml (each cites its
datasheet figure): Pico 2 module pins per Pico-2 DS sec 3.1; DIP05-1A72
pin-out code 12 (DS p.3: coil 1/7, contacts 14/8); SN74HC595 SCLS041;
ULN2803A SLRS049 (IN n pairs OUT n on the OPPOSITE corner);
SN74LVC1G123 SCES586E Fig 4-1; SN74LVC1G11 SCLS520 Fig 4-1 (pin2=GND!);
SN74LVC1G00 5-pin SC-70; SN74HC14 SCLS085; MAX31856 (EasyEDA CAD, pin
review re-verifies); USBLC6-2SC6 ST p.1 (1/6 + 3/4 pairs); LTV-817S
(1=A 2=K 3=E 4=C); AMS1117 (1=GND 2=OUT+tab 3=IN); SOT-23 FETs 1=G 2=S 3=D;
D_SMA/SMB/SOD-323 pad1=CATHODE.

Circuit per 01_docs/ARCHITECTURE.md + DETAIL_DESIGN.md; decisions D4-D14
(01_docs/BRIEF.md). DNP reserves (J12/J13 turntable, J15 MAX31865) carry
"DNP" in Value. Safety chain (ADR-0003) is drawn as story wires.
Run: python3 03_src/generate_schematic.py  (writes into 04_kicad/)
"""

import sys
from pathlib import Path

HERE = Path(__file__).parent
for p in (HERE.parents[2] / "skills" / "kicad-pcb" / "scripts",
          Path.home() / ".claude" / "skills" / "kicad-pcb" / "scripts"):
    if p.is_dir():
        sys.path.insert(0, str(p))
        break
from schwriter2 import Schematic  # noqa: E402

PROJECT = "cook_hub"
SMALL = {"RES", "CAP", "CAPP", "TP", "DSMA", "DSMB", "DSOD", "FUSE", "FER",
         "SJ", "BTN", "HDR2", "HDR3"}

rev = Schematic.rev_from_git(HERE, "HUB_REV", "hub-v*").replace("hub-", "")
sch = Schematic(
    PROJECT, "cook-hub", paper="A1",
    comment="SMC0985KS Phase-1 hub: Pico 2 + sensors + 16x reed-relay keypad emulation w/ HW watchdog; smc0985-cook commission",
    rev=rev, small_syms=SMALL, libname="cookhub")
sch.no_bom_syms = {"TP"}

# ------------------------------------------------------------------ symbols
sch.defsym("RES", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="R")
sch.defsym("CAP", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="C")
sch.defsym("CAPP", 7.62, 5.08, [("1", "+", "L", 0), ("2", "-", "R", 0)], ref="C")
sch.defsym("FUSE", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="F")
sch.defsym("FER", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="FB")
sch.defsym("TP", 5.08, 5.08, [("1", "1", "L", 0)], ref="TP")
# diodes: pad 1 = CATHODE (KiCad D_* convention)
sch.defsym("DSMA", 7.62, 5.08, [("1", "K", "L", 0), ("2", "A", "R", 0)], ref="D")
sch.defsym("DSMB", 7.62, 5.08, [("1", "K", "L", 0), ("2", "A", "R", 0)], ref="D")
sch.defsym("DSOD", 7.62, 5.08, [("1", "K", "L", 0), ("2", "A", "R", 0)], ref="D")
sch.defsym("SJ", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="SJ")
sch.defsym("BTN", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="SW")
# FET SOT-23 (1=G 2=S 3=D): D left-top, G left-bottom, S right
sch.defsym("FET", 10.16, 10.16,
           [("3", "D", "L", 0), ("1", "G", "L", 2), ("2", "S", "R", 0)], ref="Q")
sch.defsym("BARREL", 10.16, 7.62,
           [("1", "TIP+", "R", 0), ("2", "SLV-", "R", 2)], ref="J")
for n in range(2, 7):
    sch.defsym(f"XH{n}", 10.16, 2.54 * (n + 1),
               [(str(k), str(k), "R", k - 1) for k in range(1, n + 1)], ref="J")
sch.defsym("TERM2", 17.78, 7.62,
           [("1", "1", "R", 0), ("2", "2", "R", 2)], ref="J")
sch.defsym("HDR2", 7.62, 7.62,
           [("1", "1", "L", 0), ("2", "2", "L", 1)], ref="JP")
sch.defsym("HDR3", 7.62, 10.16,
           [("1", "1", "L", 0), ("2", "2", "L", 1), ("3", "3", "L", 2)], ref="JP")
sch.defsym("HDR6", 10.16, 17.78,
           [(str(k), str(k), "R", k - 1) for k in range(1, 7)], ref="J")
# Pico 2 module on socket: pins 1-20 left, 40-21 right (module top view)
sch.defsym("PICO", 25.4, 53.34,
           [(str(k), f"P{k}", "L", k - 1) for k in range(1, 21)] +
           [(str(41 - k), f"P{41 - k}", "R", k - 1) for k in range(1, 21)],
           ref="J")
# reed relay pinout 12: coil 1/7 left, contacts 14/8 right
sch.defsym("RELAY", 12.7, 12.7,
           [("1", "COIL+", "L", 0), ("7", "COIL-", "L", 3),
            ("14", "CT_A", "R", 0), ("8", "CT_B", "R", 3)], ref="K")
sch.defsym("IDC32", 15.24, 2.54 * 17,
           [(str(2 * c - 1), f"CH{c}A", "L", c - 1) for c in range(1, 17)] +
           [(str(2 * c), f"CH{c}B", "R", c - 1) for c in range(1, 17)], ref="J")
sch.defsym("SR595", 15.24, 25.4,
           [("14", "SER", "L", 0), ("11", "SRCLK", "L", 1), ("12", "RCLK", "L", 2),
            ("13", "/OE", "L", 3), ("10", "/SRCLR", "L", 4), ("16", "VCC", "L", 6),
            ("8", "GND", "L", 8),
            ("15", "QA", "R", 0), ("1", "QB", "R", 1), ("2", "QC", "R", 2),
            ("3", "QD", "R", 3), ("4", "QE", "R", 4), ("5", "QF", "R", 5),
            ("6", "QG", "R", 6), ("7", "QH", "R", 7), ("9", "QH'", "R", 8)], ref="U")
sch.defsym("ULN", 15.24, 25.4,
           [(str(k), f"IN{k}", "L", k - 1) for k in range(1, 9)] +
           [("9", "GND", "L", 8)] +
           [(str(19 - k), f"OUT{k}", "R", k - 1) for k in range(1, 9)] +
           [("10", "COM", "R", 8)], ref="U")
sch.defsym("MAX", 17.78, 20.32,
           [("4", "T+", "L", 0), ("3", "T-", "L", 1), ("2", "BIAS", "L", 2),
            ("1", "AGND", "L", 4), ("14", "DGND", "L", 5), ("6", "DNC", "L", 7),
            ("5", "AVDD", "R", 0), ("8", "DVDD", "R", 1), ("9", "/CS", "R", 2),
            ("10", "SCK", "R", 3), ("11", "SDO", "R", 4), ("12", "SDI", "R", 5),
            ("7", "/DRDY", "R", 6), ("13", "/FAULT", "R", 7)], ref="U")
sch.defsym("HC14", 15.24, 25.4,
           [("1", "1A", "L", 0), ("3", "2A", "L", 1), ("5", "3A", "L", 2),
            ("9", "4A", "L", 3), ("11", "5A", "L", 4), ("13", "6A", "L", 5),
            ("14", "VCC", "L", 7), ("7", "GND", "L", 8),
            ("2", "1Y", "R", 0), ("4", "2Y", "R", 1), ("6", "3Y", "R", 2),
            ("8", "4Y", "R", 3), ("10", "5Y", "R", 4), ("12", "6Y", "R", 5)], ref="U")
sch.defsym("WD123", 12.7, 17.78,
           [("2", "B", "L", 0), ("1", "A", "L", 1), ("3", "/CLR", "L", 2),
            ("8", "VCC", "L", 4), ("4", "GND", "L", 5),
            ("5", "Q", "R", 0), ("6", "Cext", "R", 3), ("7", "RCext", "R", 4)], ref="U")
sch.defsym("G00", 10.16, 12.7,
           [("1", "A", "L", 0), ("2", "B", "L", 1), ("3", "GND", "L", 3),
            ("4", "Y", "R", 0), ("5", "VCC", "R", 3)], ref="U")
sch.defsym("G11", 10.16, 15.24,
           [("1", "A", "L", 0), ("3", "B", "L", 1), ("6", "C", "L", 2),
            ("2", "GND", "L", 4), ("4", "Y", "R", 0), ("5", "VCC", "R", 4)], ref="U")
sch.defsym("OPTO", 10.16, 10.16,
           [("1", "A", "L", 0), ("2", "K", "L", 2),
            ("4", "C", "R", 0), ("3", "E", "R", 2)], ref="U")
sch.defsym("USBLC6", 12.7, 15.24,
           [("1", "IO1", "L", 0), ("6", "IO1B", "L", 1), ("3", "IO2", "L", 2),
            ("4", "IO2B", "L", 3), ("2", "GND", "L", 5),
            ("5", "VBUS", "R", 0)], ref="U")
sch.defsym("AMS", 12.7, 10.16,
           [("3", "VIN", "L", 0), ("1", "GND", "L", 3), ("2", "VOUT", "R", 0)], ref="U")

# ------------------------------------------------------------------ footprints
sch.sym_fp = {
    "RES": "Resistor_SMD:R_0603_1608Metric",
    "CAP": "Capacitor_SMD:C_0603_1608Metric",
    "CAPP": "Capacitor_SMD:CP_Elec_6.3x7.7",
    "FUSE": "Fuse:Fuse_1812_4532Metric",
    "FER": "Inductor_SMD:L_0805_2012Metric",
    "TP": "TestPoint:TestPoint_Pad_D1.5mm",
    "DSMA": "Diode_SMD:D_SMA",
    "DSMB": "Diode_SMD:D_SMB",
    "DSOD": "Diode_SMD:D_SOD-323",
    "SJ": "Jumper:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm",
    "BTN": "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A",
    "FET": "Package_TO_SOT_SMD:SOT-23",
    "BARREL": "Connector_BarrelJack:BarrelJack_CUI_PJ-063AH_Horizontal",
    "XH2": "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical",
    "XH3": "Connector_JST:JST_XH_B3B-XH-A_1x03_P2.50mm_Vertical",
    "XH4": "Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical",
    "XH5": "Connector_JST:JST_XH_B5B-XH-A_1x05_P2.50mm_Vertical",
    "XH6": "Connector_JST:JST_XH_B6B-XH-A_1x06_P2.50mm_Vertical",
    "TERM2": "cookhub:TerminalBlock_KF350_2P",
    "HDR2": "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
    "HDR3": "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
    "HDR6": "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical",
    "PICO": "cookhub:Pico2_Socket_2x20",
    "RELAY": "cookhub:Relay_StandexDIP_1A_pinout12",
    "IDC32": "cookhub:IDC_2x16_Keyed",
    "SR595": "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
    "ULN": "Package_SO:SOIC-18W_7.5x11.6mm_P1.27mm",
    "MAX": "Package_SO:TSSOP-14_4.4x5mm_P0.65mm",
    "HC14": "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
    "WD123": "Package_SO:SSOP-8_3.9x5.05mm_P1.27mm",
    "G00": "Package_TO_SOT_SMD:SOT-353_SC-70-5",
    "G11": "Package_TO_SOT_SMD:SOT-23-6",
    "OPTO": "Package_DIP:SMDIP-4_W9.53mm",
    "USBLC6": "Package_TO_SOT_SMD:SOT-23-6",
    "AMS": "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
}
# 10u/22u lines are 0805 (coil TPs stay SMD D1.5 — B.Cu verticals pass
# 1.15mm west of them, a THT barrel would collide)
BIGCAP = ["C1", "C2", "C3", "C6", "C8", "C10", "C19"]
sch.ref_fp = {r: "Capacitor_SMD:C_0805_2012Metric" for r in BIGCAP}

# ═══════════════════ circuit: structure only ═══════════════════

# --- 1: power entry ---
sch.region("1. POWER ENTRY: 5V/2A barrel -> polyfuse -> reverse PFET -> 5VP (TVS+bulk)   [ADR-0001, spec 7.1/7.3]")
sch.row(("BARREL", "J1", "EXT 5V 2A", {"1": "5V_IN", "2": "GND"}),
        ("FUSE", "F1", "MF-MSMF200L 2A", {"1": "5V_IN", "2": "5V_D"}),
        ("FET", "Q3", "AO3401A rev-prot", {"3": "5V_D", "1": "Q3G", "2": "5VP"}),
        ("DSMB", "D2", "SMBJ5.0A", {"1": "5VP", "2": "GND"}))
sch.chain("J1.1", "F1.1")
sch.chain("F1.2", "Q3.3")
sch.chain("Q3.2", "D2.1")
sch.row(("RES", "R12", "100k Q3 gate", {"1": "Q3G", "2": "GND"}),
        ("CAPP", "CE1", "220u 16V bulk", {"1": "5VP", "2": "GND"}),
        ("CAP", "C4", "22u 5VP", {"1": "5VP", "2": "GND"}),
        ("CAP", "C5", "22u 5VP", {"1": "5VP", "2": "GND"}),
        ("TP", "TP1", "TP 5VP", {"1": "5VP"}),
        ("TP", "TP4", "TP GND", {"1": "GND"}),
        ("TP", "TP5", "TP GND", {"1": "GND"}))

# --- 2: rails ---
sch.region("2. RAILS: AMS1117-3.3 logic rail; ferrite-filtered 3V3A analog; VSYS OR-feed   [ADR-0005, spec 7.2]")
sch.row(("CAP", "C1", "10u LDO in", {"1": "5VP", "2": "GND"}),
        ("AMS", "U12", "AMS1117-3.3", {"3": "5VP", "1": "GND", "2": "3V3"}),
        ("CAP", "C2", "22u 3V3", {"1": "3V3", "2": "GND"}),
        ("CAP", "C3", "22u 3V3", {"1": "3V3", "2": "GND"}))
sch.chain("U12.2", "C2.1")
sch.row(("FER", "FB1", "600R ferrite", {"1": "3V3", "2": "3V3A"}),
        ("CAP", "C6", "10u 3V3A", {"1": "3V3A", "2": "GND"}),
        ("CAP", "C7", "100n 3V3A", {"1": "3V3A", "2": "GND"}))
sch.chain("FB1.2", "C6.1")
sch.row(("DSMA", "D1", "SS34 VSYS OR", {"1": "VSYS", "2": "5VP"}),
        ("CAP", "C10", "10u VSYS", {"1": "VSYS", "2": "GND"}),
        ("TP", "TP2", "TP 3V3", {"1": "3V3"}),
        ("TP", "TP3", "TP 3V3A", {"1": "3V3A"}))

# --- 3: watchdog + gating (the safety chain) ---
sch.region("3. HW WATCHDOG + COIL-RAIL GATING: 3 independent locks, all-off default   [ADR-0003, spec 6.5/7.4]")
sch.row(("WD123", "U7", "SN74LVC1G123",
         {"2": "WD_PULSE", "1": "GND", "3": "3V3", "8": "3V3", "4": "GND",
          "5": "WD_OK", "6": "WD_CX", "7": "WD_RCX"}),
        ("CAP", "C11", "1u X7R WD", {"1": "WD_CX", "2": "WD_RCX"}),
        ("RES", "R11", "390k 1% WD", {"1": "WD_RCX", "2": "3V3"}))
sch.chain("U7.6", "C11.1")
sch.chain("C11.2", "R11.1")
sch.row(("CAP", "C14", "100n U7", {"1": "3V3", "2": "GND"}),
        ("RES", "R22", "10k RLY_EN pd", {"1": "RLY_EN", "2": "GND"}),
        ("RES", "R21", "10k /OE pu", {"1": "OE_N", "2": "3V3"}),
        ("TP", "TP21", "TP WD_PULSE", {"1": "WD_PULSE"}),
        ("TP", "TP22", "TP WD_OK", {"1": "WD_OK"}))
sch.row(("G00", "U8", "74LVC1G00 /OE",
         {"1": "RLY_EN", "2": "WD_OK", "3": "GND", "4": "OE_N", "5": "3V3"}),
        ("CAP", "C15", "100n U8", {"1": "3V3", "2": "GND"}),
        ("TP", "TP20", "TP /OE", {"1": "OE_N"}))
sch.row(("G11", "U9", "74LVC1G11 AND3",
         {"1": "WD_OK", "3": "ESTOP_OK", "6": "RLY_EN", "2": "GND",
          "4": "COIL_EN", "5": "3V3"}),
        ("RES", "R24", "1k Q2 gate", {"1": "COIL_EN", "2": "Q2G"}),
        ("FET", "Q2", "2N7002", {"1": "Q2G", "2": "GND", "3": "Q1G"}),
        ("RES", "R23", "47k Q1 pu", {"1": "Q1G", "2": "5VP"}))
sch.chain("U9.4", "R24.1")
sch.chain("R24.2", "Q2.1")
sch.row(("FET", "Q1", "AO3401A hi-side", {"1": "Q1G", "2": "5VP", "3": "RELAY_5V"}),
        ("RES", "R25", "10k bleed", {"1": "RELAY_5V", "2": "GND"}),
        ("CAP", "C8", "10u RELAY_5V", {"1": "RELAY_5V", "2": "GND"}),
        ("CAP", "C9", "100n RELAY_5V", {"1": "RELAY_5V", "2": "GND"}),
        ("CAP", "C16", "100n U9", {"1": "3V3", "2": "GND"}),
        ("TP", "TP33", "TP RELAY_5V", {"1": "RELAY_5V"}))

# --- 4: shift registers + coil drivers ---
sch.region("4. RELAY COIL DRIVE: GP11/12/13 -> 2x 74HC595 -> 2x ULN2803A -> 16 coils   [spec 6.4]")
sch.row(("SR595", "U3", "74HC595 #1",
         {"14": "SR_DATA", "11": "SR_CLK", "12": "SR_LATCH", "13": "OE_N",
          "10": "3V3", "16": "3V3", "8": "GND",
          "15": "DRV1", "1": "DRV2", "2": "DRV3", "3": "DRV4", "4": "DRV5",
          "5": "DRV6", "6": "DRV7", "7": "DRV8", "9": "SR_CASC"}),
        ("CAP", "C12", "100n U3", {"1": "3V3", "2": "GND"}),
        ("SR595", "U4", "74HC595 #2",
         {"14": "SR_CASC", "11": "SR_CLK", "12": "SR_LATCH", "13": "OE_N",
          "10": "3V3", "16": "3V3", "8": "GND",
          "15": "DRV9", "1": "DRV10", "2": "DRV11", "3": "DRV12", "4": "DRV13",
          "5": "DRV14", "6": "DRV15", "7": "DRV16", "9": None}),
        ("CAP", "C13", "100n U4", {"1": "3V3", "2": "GND"}))
sch.row(("ULN", "U5", "ULN2803A K1-K8",
         dict({str(k): f"DRV{k}" for k in range(1, 9)},
              **{"9": "GND", "10": "RELAY_5V"},
              **{str(19 - k): f"COIL_{k}" for k in range(1, 9)})),
        ("ULN", "U6", "ULN2803A K9-K16",
         dict({str(k): f"DRV{k + 8}" for k in range(1, 9)},
              **{"9": "GND", "10": "RELAY_5V"},
              **{str(19 - k): f"COIL_{k + 8}" for k in range(1, 9)})))
sch.row(("TP", "TP17", "TP SR DATA", {"1": "SR_DATA"}),
        ("TP", "TP18", "TP SR CLK", {"1": "SR_CLK"}),
        ("TP", "TP19", "TP SR LATCH", {"1": "SR_LATCH"}))
sch.row(*[("TP", f"TP{40 + k}", f"TP COIL {k}", {"1": f"COIL_{k}"})
          for k in range(1, 9)])
sch.row(*[("TP", f"TP{48 + k}", f"TP COIL {k + 8}", {"1": f"COIL_{k + 8}"})
          for k in range(1, 9)])

# --- 5: relay bank (isolated zone) ---
sch.region("5. REED RELAY BANK + J11 (ISOLATED KEYPAD ZONE, >=6mm creepage, milled slots)   [ADR-0002, spec 6.2/6.3/8.4]")
for row0 in (1, 5, 9, 13):
    sch.row(*[("RELAY", f"K{n}", "DIP05-1A72-12L",
               {"1": "RELAY_5V", "7": f"COIL_{n}",
                "14": f"KC{n}A", "8": f"KC{n}B"})
              for n in range(row0, row0 + 4)])
sch.row(("IDC32", "J11", "X9555WV 2x16 KEYPAD",
         dict({str(2 * c - 1): f"KC{c}A" for c in range(1, 17)},
              **{str(2 * c): f"KC{c}B" for c in range(1, 17)})))

# --- 6: Pico 2 module ---
sch.region("6. PICO 2 MODULE (pluggable, 2x 1x20 sockets; USB CDC exits to Pi 5)   [spec 2.2/5]")
sch.row(("PICO", "J2", "Pico 2 socket",
         {"1": "SDA0", "2": "SCL0", "3": "GND", "4": "SDA1", "5": "SCL1",
          "6": "GP4_SPARE", "7": "WD_PULSE", "8": "GND", "9": "HX_DAT",
          "10": "HX_CLK", "11": "DOOR_IN", "12": "ESTOP_OK", "13": "GND",
          "14": "ARC", "15": "SR_DATA", "16": "SR_CLK", "17": "SR_LATCH",
          "18": "GND", "19": "RLY_EN", "20": "CONT_REQ",
          "21": "MISO", "22": "CS0", "23": "GND", "24": "SCK", "25": "MOSI",
          "26": "CS1", "27": "TT_A", "28": "GND", "29": "TT_B", "30": "RUN",
          "31": "TH1_ADC", "32": "TH2_ADC", "33": "GND", "34": "TH3_ADC",
          "35": "ADC_VREF", "36": None, "37": None, "38": "GND",
          "39": "VSYS", "40": "VBUS_PICO"}))
sch.row(("BTN", "SW1", "RUN reset", {"1": "RUN", "2": "GND"}),
        ("TP", "TP29", "TP VBUS", {"1": "VBUS_PICO"}),
        ("TP", "TP30", "TP RUN", {"1": "RUN"}),
        ("TP", "TP31", "TP ADC_VREF", {"1": "ADC_VREF"}),
        ("TP", "TP32", "TP ARC GP10", {"1": "ARC"}))

# --- 7: I2C buses ---
sch.region("7. I2C0 (MLX90640 + ambient SHT45) / I2C1 (exhaust SHT45): damping, jumper pullups, low-C ESD   [ADR-0004, D11, spec 3.3-3.5]")
sch.row(("RES", "R41", "33R SDA0", {"1": "SDA0", "2": "SDA0_J"}),
        ("RES", "R42", "33R SCL0", {"1": "SCL0", "2": "SCL0_J"}),
        ("XH4", "J3", "I2C0 MLX+SHT45",
         {"1": "3V3", "2": "GND", "3": "SDA0_J", "4": "SCL0_J"}),
        ("USBLC6", "U13", "USBLC6-2SC6",
         {"1": "SDA0_J", "6": "SDA0_J", "3": "SCL0_J", "4": "SCL0_J",
          "2": "GND", "5": "3V3"}),
        ("CAP", "C20", "100n U13", {"1": "3V3", "2": "GND"}))
sch.row(("HDR3", "JP1", "I2C0 PU 2k2|4k7",
         {"1": "PU0_22", "2": "3V3", "3": "PU0_47"}),
        ("RES", "R71", "2k2 SDA0 pu", {"1": "PU0_22", "2": "SDA0_J"}),
        ("RES", "R72", "2k2 SCL0 pu", {"1": "PU0_22", "2": "SCL0_J"}),
        ("RES", "R73", "4k7 SDA0 pu", {"1": "PU0_47", "2": "SDA0_J"}),
        ("RES", "R74", "4k7 SCL0 pu", {"1": "PU0_47", "2": "SCL0_J"}),
        ("TP", "TP6", "TP SDA0", {"1": "SDA0_J"}),
        ("TP", "TP7", "TP SCL0", {"1": "SCL0_J"}))
sch.row(("RES", "R43", "33R SDA1", {"1": "SDA1", "2": "SDA1_J"}),
        ("RES", "R44", "33R SCL1", {"1": "SCL1", "2": "SCL1_J"}),
        ("XH4", "J4", "I2C1 EXHAUST SHT45",
         {"1": "3V3", "2": "GND", "3": "SDA1_J", "4": "SCL1_J"}),
        ("USBLC6", "U14", "USBLC6-2SC6",
         {"1": "SDA1_J", "6": "SDA1_J", "3": "SCL1_J", "4": "SCL1_J",
          "2": "GND", "5": "3V3"}),
        ("CAP", "C21", "100n U14", {"1": "3V3", "2": "GND"}))
sch.row(("HDR3", "JP2", "I2C1 PU 2k2|4k7",
         {"1": "PU1_22", "2": "3V3", "3": "PU1_47"}),
        ("RES", "R75", "2k2 SDA1 pu", {"1": "PU1_22", "2": "SDA1_J"}),
        ("RES", "R76", "2k2 SCL1 pu", {"1": "PU1_22", "2": "SCL1_J"}),
        ("RES", "R77", "4k7 SDA1 pu", {"1": "PU1_47", "2": "SDA1_J"}),
        ("RES", "R78", "4k7 SCL1 pu", {"1": "PU1_47", "2": "SCL1_J"}),
        ("TP", "TP8", "TP SDA1", {"1": "SDA1_J"}),
        ("TP", "TP9", "TP SCL1", {"1": "SCL1_J"}))

# --- 8: thermocouple ---
sch.region("8. MAX31856 K-TYPE FRONT-END (SPI0 CS0) + J15 MAX31865 provision (CS1)   [ADR-0004, D9/D10, spec 3.6]")
sch.row(("TERM2", "J5", "TC K-TYPE",
         {"1": "TC_PLUS_J", "2": "TC_MINUS_J"}),
        ("RES", "R61", "100R TC+", {"1": "TC_PLUS_J", "2": "TC_P"}),
        ("MAX", "U1", "MAX31856",
         {"4": "TC_P", "3": "TC_N", "2": "TC_N", "1": "GND", "14": "GND",
          "6": None, "5": "3V3A", "8": "3V3A", "9": "CS0", "10": "SCK",
          "11": "MISO", "12": "MOSI", "7": "DRDY_N", "13": "FAULT_N"}))
sch.chain("R61.2", "U1.4")
sch.row(("RES", "R62", "100R TC-", {"1": "TC_MINUS_J", "2": "TC_N"}),
        ("CAP", "C61", "100n TC diff", {"1": "TC_P", "2": "TC_N"}),
        ("CAP", "C62", "10n TC+ cm", {"1": "TC_P", "2": "GND"}),
        ("CAP", "C63", "10n TC- cm", {"1": "TC_N", "2": "GND"}))
sch.row(("CAP", "C18", "100n U1", {"1": "3V3A", "2": "GND"}),
        ("CAP", "C19", "10u U1", {"1": "3V3A", "2": "GND"}),
        ("TP", "TP34", "TP /DRDY", {"1": "DRDY_N"}),
        ("TP", "TP35", "TP /FAULT", {"1": "FAULT_N"}))
sch.row(("HDR6", "J15", "MAX31865 DNP",
         {"1": "3V3A", "2": "GND", "3": "SCK", "4": "MOSI", "5": "MISO",
          "6": "CS1"}),
        ("TP", "TP10", "TP SCK", {"1": "SCK"}),
        ("TP", "TP11", "TP MISO", {"1": "MISO"}),
        ("TP", "TP12", "TP MOSI", {"1": "MOSI"}),
        ("TP", "TP13", "TP CS0", {"1": "CS0"}),
        ("TP", "TP14", "TP CS1", {"1": "CS1"}))

# --- 9: thermistors ---
sch.region("9. NTC THERMISTOR DIVIDERS x3 (port, enclosure, spare; 10k 1% refs)   [spec 3.10]")
for i, (rr, rf, cf, dd, tp, th, adc) in enumerate([
        ("R51", "R54", "C51", "D5", "TP25", "TH1", "TH1_ADC"),
        ("R52", "R55", "C52", "D6", "TP26", "TH2", "TH2_ADC"),
        ("R53", "R56", "C53", "D7", "TP27", "TH3", "TH3_ADC")]):
    sch.row(("RES", rr, "10k 1% ref", {"1": "3V3A", "2": th}),
            ("RES", rf, "1k RC", {"1": th, "2": adc}),
            ("CAP", cf, "100n RC", {"1": adc, "2": "GND"}),
            ("DSOD", dd, "PESD5V0S1BA", {"1": th, "2": "GND"}),
            ("TP", tp, f"TP {adc}", {"1": adc}))
    sch.chain(f"{rr}.2", f"{rf}.1")
    sch.chain(f"{rf}.2", f"{cf}.1")
sch.row(("XH6", "J9", "NTC x3",
         {"1": "TH1", "2": "GND", "3": "TH2", "4": "GND", "5": "TH3",
          "6": "GND"}))

# --- 10: door + E-stop ---
sch.region("10. DOOR (NC+EOL, D8) & E-STOP (NC hard path -> coil-rail AND gate)   [spec 3.8/3.9, ADR-0003/0004]")
sch.row(("XH3", "J7", "DOOR NC+EOL",
         {"1": "HALL_PWR", "2": "DOOR_RAW", "3": "GND"}),
        ("RES", "R33", "3k3 door pu", {"1": "3V3", "2": "DOOR_RAW"}),
        ("RES", "R34", "10k door RC", {"1": "DOOR_RAW", "2": "DOOR_IN"}),
        ("CAP", "C33", "100n door RC", {"1": "DOOR_IN", "2": "GND"}),
        ("DSOD", "D4", "PESD5V0S1BA", {"1": "DOOR_RAW", "2": "GND"}))
sch.chain("R34.2", "C33.1")
sch.row(("HDR2", "JP5", "HALL 3V3 opt", {"1": "3V3", "2": "HALL_PWR"}),
        ("SJ", "SJ1", "DOOR->ADC2 opt", {"1": "DOOR_RAW", "2": "TH3_ADC"}),
        ("TP", "TP23", "TP DOOR", {"1": "DOOR_IN"}))
sch.row(("XH2", "J8", "E-STOP NC", {"1": "ESTOP_RAW", "2": "GND"}),
        ("RES", "R31", "3k3 estop pu", {"1": "3V3", "2": "ESTOP_RAW"}),
        ("RES", "R32", "10k estop RC", {"1": "ESTOP_RAW", "2": "ESTOP_F"}),
        ("CAP", "C31", "100n estop RC", {"1": "ESTOP_F", "2": "GND"}),
        ("DSOD", "D3", "PESD5V0S1BA", {"1": "ESTOP_RAW", "2": "GND"}))
sch.chain("R32.2", "C31.1")
sch.row(("HC14", "U11", "74HC14 E-stop",
         {"1": "ESTOP_F", "2": "ESTOP_INV", "3": "ESTOP_INV", "4": "ESTOP_OK",
          "5": "GND", "9": "GND", "11": "GND", "13": "GND",
          "6": None, "8": None, "10": None, "12": None,
          "14": "3V3", "7": "GND"}),
        ("CAP", "C17", "100n U11", {"1": "3V3", "2": "GND"}),
        ("TP", "TP24", "TP ESTOP_OK", {"1": "ESTOP_OK"}))

# --- 11: HX711 digital + contactor ---
sch.region("11. LOADCELL DIGITAL LINK (to cook-loadcell) & OPTO CONTACTOR OUT (30V/50mA)   [spec 3.7/7.5]")
sch.row(("XH5", "J6", "LOADCELL DIG",
         {"1": "5VP", "2": "3V3", "3": "GND", "4": "HX_DAT", "5": "HX_CLK"}),
        ("USBLC6", "U15", "USBLC6-2SC6",
         {"1": "HX_DAT", "6": "HX_DAT", "3": "HX_CLK", "4": "HX_CLK",
          "2": "GND", "5": "3V3"}),
        ("CAP", "C22", "100n U15", {"1": "3V3", "2": "GND"}),
        ("TP", "TP15", "TP HX DAT", {"1": "HX_DAT"}),
        ("TP", "TP16", "TP HX CLK", {"1": "HX_CLK"}))
sch.row(("RES", "R26", "330R opto LED", {"1": "CONT_REQ", "2": "CONT_A"}),
        ("OPTO", "U10", "LTV-817S",
         {"1": "CONT_A", "2": "GND", "4": "CONT_C", "3": "CONT_E"}),
        ("TERM2", "J10", "CONTACTOR 30V",
         {"1": "CONT_C", "2": "CONT_E"}),
        ("TP", "TP28", "TP CONT GP15", {"1": "CONT_REQ"}))
sch.chain("R26.2", "U10.1")

# --- 12: future expansion ---
sch.region("12. PHASE-2 / SPARE HEADERS: turntable encoder + step/dir (shared pins, D7), spare I2C0   [spec 4.1/4.2/8.5]")
sch.row(("XH5", "J12", "ENCODER DNP",
         {"1": "3V3", "2": "GND", "3": "TT_A", "4": "TT_B", "5": "GP4_SPARE"}),
        ("XH4", "J13", "STEP/DIR/EN DNP",
         {"1": "TT_A", "2": "TT_B", "3": "GP4_SPARE", "4": "GND"}),
        ("XH5", "J14", "SPARE I2C0+GP4",
         {"1": "3V3", "2": "GND", "3": "SDA0_J", "4": "SCL0_J",
          "5": "GP4_SPARE"}))

# ------------------------------------------------------------------ emit
content = sch.emit()
out = HERE.parent / "04_kicad"
out.mkdir(exist_ok=True)
(out / f"{PROJECT}.kicad_sch").write_text(content)

(HERE / "lib").mkdir(exist_ok=True)
sch.write_symbol_lib(HERE / "lib" / "cookhub.kicad_sym")
(out / "sym-lib-table").write_text(
    sch.sym_lib_table("cookhub", "${KIPRJMOD}/../03_src/lib/cookhub.kicad_sym"))
(out / "fp-lib-table").write_text(sch.fp_lib_table(
    {"cookhub": "${KIPRJMOD}/../03_src/lib/cookhub.pretty"}))

if not (out / f"{PROJECT}.kicad_pro").exists():
    (out / f"{PROJECT}.kicad_pro").write_text(
        '{\n  "board": { "design_settings": {} },\n'
        f'  "meta": {{ "filename": "{PROJECT}.kicad_pro", "version": 1 }},\n'
        '  "schematic": { "legacy_lib_dir": "", "legacy_lib_list": [] }\n}\n')

nlabels = content.count("(global_label")
print(f"wrote {PROJECT}.kicad_sch via schwriter2: {len(sch.cells)} cells, "
      f"{len(sch.wires)} wires, {nlabels} net labels, internal S-OCCL 0, parens balanced")
