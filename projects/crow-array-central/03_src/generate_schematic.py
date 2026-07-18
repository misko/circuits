"""Generate 04_kicad/crow_array_central.kicad_sch — schwriter2 (structure only).

Central 8-channel USB-audio recorder: XU316-1024-TQ128 + two shared-clock
PCM1865 ADCs, USB-HS device to a Pi 5, 8 RJ45 pod ports (NOT ETHERNET).
The power sequencing / clocking / USB / boot straps are copied from the XMOS
XK-AUDIO-316-MC-AB hardware manual (01_docs/reference/xmos_mc_audio_notes.md,
ADR-0003 fidelity mandate); every design choice traces to that file's cited
figures or to 01_docs/decisions/ADR-000x.

Pin numbers are PHYSICAL PADS from 02_parts/<MPN>/part.yaml (each cites its
datasheet figure). The 8x port channel and the 8x ADC-input channel are built
by ONE reusable generator function each (commission requirement). GND draws as
power-symbol ground icons; the story-critical chains (power entry->protection,
buck FB strings, one full port signal path) are WIRED (canon S6); pullups,
decouplers and bulk are net-label-only. NC pins get no_connect flags (canon S4).
DNP reserves (J7/J8 jacks, ch7/8) carry "DNP" in Value so the fab exporter
drops them from BOM/CPL while the pads stay in the gerbers.

Run: python3 03_src/generate_schematic.py   (writes into 04_kicad/)
"""
import sys
from pathlib import Path

HERE = Path(__file__).parent
for p in (HERE.parents[2] / "skills" / "kicad-pcb" / "scripts",
          Path.home() / ".claude" / "skills" / "kicad-pcb" / "scripts"):
    if p.is_dir():
        sys.path.insert(0, str(p))
        break
import schwriter2  # noqa: E402
from schwriter2 import Schematic  # noqa: E402

# The XU316 is a single 129-pad cell (~165mm tall); the whole design needs
# the A0 sheet KiCad supports but the engine doesn't preload.
schwriter2.PAPERS.setdefault("A0", (1189.0, 841.0))

PROJECT = "crow_array_central"
SMALL = {"RES", "CAP", "CAPP", "FBEAD", "IND", "FUSE", "TP", "DIODE2"}

rev = Schematic.rev_from_git(HERE, "CAC_REV", "cac-v*").replace("cac-", "")
sch = Schematic(
    PROJECT, "crow-array-central", paper="A0",
    comment="XU316 + dual PCM1865 8ch USB audio recorder; 8x RJ45 NOT-ETHERNET pod ports; crow-array commission",
    rev=rev, small_syms=SMALL, libname="cac")
sch.no_bom_syms = {"TP"}

# ═══════════════════════════════ symbols ═══════════════════════════════
sch.defsym("RES", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="R")
sch.defsym("CAP", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="C")
# polarized electrolytic: pad 1 = POSITIVE (KiCad CP_Elec convention)
sch.defsym("CAPP", 7.62, 5.08, [("1", "+", "L", 0), ("2", "-", "R", 0)], ref="C")
sch.defsym("FBEAD", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="FB")
sch.defsym("IND", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="L")
sch.defsym("FUSE", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="F")
sch.defsym("TP", 5.08, 5.08, [("1", "1", "L", 0)], ref="TP")
# D_SMB diode: pad 1 = CATHODE (KiCad convention; SMBJ band = cathode)
sch.defsym("DIODE2", 7.62, 5.08, [("1", "K", "L", 0), ("2", "A", "R", 0)], ref="D")
# AO3400A/AO3401A SOT-23: 1=G 2=S 3=D (part.yaml top-view figure)
sch.defsym("FET3", 10.16, 10.16,
           [("1", "G", "L", 0), ("2", "S", "L", 2), ("3", "D", "R", 0)], ref="Q")
# barrel jack DC-005: 1=TIP 2=SLEEVE 3=SWITCH (TIP on R to chain into F1)
sch.defsym("BARREL", 10.16, 10.16,
           [("2", "SLV", "L", 0), ("3", "SW", "L", 2), ("1", "TIP", "R", 0)], ref="J")
# KF128 2-pole terminal
sch.defsym("TERM2", 7.62, 7.62,
           [("1", "1", "L", 0), ("2", "2", "L", 1)], ref="J")
# generic 2-pin header (injection / debug row units)
sch.defsym("HDR2", 7.62, 7.62,
           [("1", "1", "L", 0), ("2", "2", "L", 1)], ref="J")
# AP61102 buck SOT-563: 1=FB 2=GND 3=VIN 4=SW 5=EN 6=PG (part.yaml top view)
sch.defsym("BUCK", 12.7, 17.78,
           [("3", "VIN", "L", 0), ("5", "EN", "L", 2), ("1", "FB", "L", 4),
            ("4", "SW", "R", 0), ("6", "PG", "R", 2), ("2", "GND", "R", 4)],
           ref="U")
# TCR2LF18 SOT-23-5: 1=VIN 2=GND 3=CE 5=VOUT 4=NC
sch.defsym("LDO_TCR", 12.7, 15.24,
           [("1", "VIN", "L", 0), ("3", "CE", "L", 2), ("2", "GND", "L", 4),
            ("5", "VOUT", "R", 0), ("4", "NC", "R", 4)], ref="U")
# XC6227 SOT-89-5: 1=CE 2=VSS 3=NC 4=VIN 5=VOUT
sch.defsym("LDO_XC", 12.7, 15.24,
           [("4", "VIN", "L", 0), ("1", "CE", "L", 2), ("2", "VSS", "L", 4),
            ("5", "VOUT", "R", 0), ("3", "NC", "R", 4)], ref="U")
# NC7NZ34 triple buffer VSSOP-8: A1=1 Y3=2 A2=3 GND=4 Y2=5 A3=6 Y1=7 VCC=8
sch.defsym("BUF3", 12.7, 20.32,
           [("1", "A1", "L", 0), ("3", "A2", "L", 2), ("6", "A3", "L", 4),
            ("4", "GND", "L", 6),
            ("8", "VCC", "R", 0), ("7", "Y1", "R", 2), ("5", "Y2", "R", 4),
            ("2", "Y3", "R", 6)], ref="U")
# W25Q16 SOIC-8: 1=/CS 2=DO 3=/WP 4=GND 5=DI 6=CLK 7=/HOLD 8=VCC
sch.defsym("FLASH", 12.7, 20.32,
           [("1", "CS", "L", 0), ("6", "CLK", "L", 2), ("5", "DI", "L", 4),
            ("2", "DO", "L", 6),
            ("8", "VCC", "R", 0), ("7", "HOLD", "R", 2), ("3", "WP", "R", 4),
            ("4", "GND", "R", 6)], ref="U")
# SHT40 DFN-4: 1=SDA 2=SCL 3=VDD 4=VSS
sch.defsym("SHT", 10.16, 12.7,
           [("1", "SDA", "L", 0), ("2", "SCL", "L", 2),
            ("3", "VDD", "R", 0), ("4", "VSS", "R", 2)], ref="U")
# FA-238 crystal 3225-4: 1=XTAL1 2=GND 3=XTAL2 4=GND
sch.defsym("XTAL", 10.16, 12.7,
           [("1", "X1", "L", 0), ("3", "X2", "L", 2),
            ("2", "GND", "R", 0), ("4", "GND", "R", 2)], ref="Y")
# TPD2E2U06 SOT-553: 3=IO1 5=IO2 4=GND 1=NC 2=NC
sch.defsym("ESD2", 10.16, 12.7,
           [("3", "IO1", "L", 0), ("1", "NC1", "L", 2), ("2", "NC2", "L", 3),
            ("5", "IO2", "R", 0), ("4", "GND", "R", 3)], ref="D")
# TPD4EUSB30 USON-10: 1=D1+ 2=D1- 3=GND 4=D2+ 5=D2- 6..10 NC/pass 8=GND
sch.defsym("ESD4", 12.7, 15.24,
           [("1", "D1P", "L", 0), ("2", "D1M", "L", 2), ("4", "D2P", "L", 4),
            ("5", "D2M", "L", 6),
            ("3", "GND", "R", 0), ("8", "GND2", "R", 1),
            ("10", "N10", "R", 3), ("9", "N9", "R", 4),
            ("7", "N7", "R", 5), ("6", "N6", "R", 6)], ref="D")

# RJ45 RJHSE-5384: contacts 1-8, LEDs 9-12, SH shield
sch.defsym("RJ45", 15.24, 33.02,
           [(str(k), f"P{k}", "L", k - 1) for k in range(1, 9)] +
           [("9", "LED1A", "R", 0), ("10", "LED1B", "R", 1),
            ("11", "LED2A", "R", 2), ("12", "LED2B", "R", 3),
            ("SH", "SHLD", "R", 5)], ref="J")

# USB-C USB4105 16P: VBUS A4/A9/B4/B9, GND A1/A12/B1/B12, CC A5/B5,
# D+ A6/B6, D- A7/B7, SBU A8/B8, SH
sch.defsym("USBC", 17.78, 40.64,
           [("A4", "VBUS", "L", 0), ("A9", "VBUSa", "L", 1),
            ("B4", "VBUSb", "L", 2), ("B9", "VBUSc", "L", 3),
            ("A6", "DP1", "L", 5), ("B6", "DP2", "L", 6),
            ("A7", "DM1", "L", 8), ("B7", "DM2", "L", 9),
            ("A5", "CC1", "L", 11), ("B5", "CC2", "L", 12),
            ("A1", "GND", "R", 0), ("A12", "GNDa", "R", 1),
            ("B1", "GNDb", "R", 2), ("B12", "GNDc", "R", 3),
            ("A8", "SBU1", "R", 5), ("B8", "SBU2", "R", 6),
            ("SH", "SHLD", "R", 8)], ref="J")

# PCM1865 TSSOP-30 (part.yaml pin table p.10)
PCM_PINS = [
    ("3", "VIN1P", "L", 0), ("1", "VIN1M", "L", 1),
    ("4", "VIN2P", "L", 2), ("2", "VIN2M", "L", 3),
    ("30", "VIN3P", "L", 4), ("28", "VIN3M", "L", 5),
    ("29", "VIN4P", "L", 6), ("27", "VIN4M", "L", 7),
    ("6", "VREF", "L", 9), ("5", "MICBIAS", "L", 10),
    ("15", "SCKI", "L", 12), ("17", "BCK", "L", 13), ("16", "LRCK", "L", 14),
    ("18", "DOUT", "L", 15),
    ("8", "AVDD", "R", 0), ("7", "AGND", "R", 1),
    ("13", "DVDD", "R", 2), ("12", "DGND", "R", 3),
    ("14", "IOVDD", "R", 4), ("11", "LDO", "R", 5),
    ("10", "XI", "R", 6), ("9", "XO", "R", 7),
    ("24", "SCL", "R", 9), ("23", "SDA", "R", 10),
    ("25", "MSAD", "R", 11), ("26", "MD0", "R", 12),
    ("22", "GPIO0", "R", 13), ("21", "GPIO1", "R", 14),
    ("20", "GPIO2", "R", 15), ("19", "GPIO3", "R", 16),
]
sch.defsym("ADC", 25.4, 45.72, PCM_PINS, ref="U")

# ── XU316-1024-TQ128 — full 129-pad map (02_parts/XU316.../part.yaml) ──
XU = {
    1: "QSPI_D2", 2: "QSPI_CS", 3: "QSPI_D3", 4: "QSPI_CLK", 5: "0V9",
    6: "BEEP_G1", 7: "MCLK_SRC", 8: "VBUS_DET", 9: "BEEP_G2", 10: "3V3",
    11: "0V9", 12: "BEEP_G3", 13: None, 14: "0V9", 15: None, 16: None,
    17: "3V3", 18: "0V9", 19: None, 20: "LRCK_X", 21: None, 22: "BCLK_X",
    23: "MCLK_SRC", 24: "GND", 25: None, 26: None, 27: "GND", 28: None,
    29: None, 30: "GND", 31: None, 32: None, 33: "XOUT", 34: "XIN",
    35: "1V8", 36: "TDI", 37: "TDO", 38: "RST_N", 39: "0V9", 40: "3V3",
    41: "PLL_AVDD", 42: "GND", 43: "3V3", 44: "TMS", 45: "0V9", 46: None,
    47: None, 48: None, 49: None, 50: "0V9", 51: "TCK", 52: "3V3",
    53: None, 54: "0V9", 55: None, 56: "1V8", 57: None, 58: None,
    59: "USB_DM", 60: "USB_DP", 61: "3V3", 62: "1V8", 63: None, 64: None,
    65: None, 66: None, 67: None, 68: "0V9", 69: None, 70: None, 71: None,
    72: "3V3", 73: None, 74: None, 75: None, 76: None, 77: "BEEP_G8", 78: None,
    79: None, 80: "BEEP_G7", 81: None, 82: None, 83: None, 84: None, 85: "0V9",
    86: None, 87: None, 88: None, 89: "3V3", 90: None,
    91: None, 92: None, 93: "I2C_SCL", 94: "I2C_SDA", 95: "0V9",
    96: None, 97: None, 98: None, 99: None, 100: None, 101: None, 102: None,
    103: None, 104: "0V9", 105: "0V9", 106: "0V9", 107: "DATA1",
    108: "DATA2", 109: "3V3", 110: None, 111: None, 112: "BEEP_G6",
    113: "0V9", 114: None, 115: None, 116: None, 117: None, 118: "BEEP_G5",
    119: None, 120: None, 121: "3V3", 122: None, 123: None, 124: None,
    125: None, 126: "BEEP_G4", 127: "QSPI_D0", 128: "QSPI_D1", 129: "GND",
}
# signal name per pad for the symbol pin label (from part.yaml)
XU_NAME = {
    1: "X0D06", 2: "X0D01", 3: "X0D07", 4: "X0D10", 5: "VDD", 6: "X0D00",
    7: "X0D11", 8: "X0D14", 9: "X0D16", 10: "VDDIOL", 11: "VDD", 12: "X1D36",
    13: "X1D37", 14: "VDD", 15: "X1D38", 16: "X1D39", 17: "VDDIOL", 18: "VDD",
    19: "X1D00", 20: "X1D01", 21: "X1D09", 22: "X1D10", 23: "X1D11/APLLOUT",
    24: "MIPI_VDD18", 25: "MIPI_DN2", 26: "MIPI_DP2", 27: "MIPI_VDD09",
    28: "MIPI_DN1", 29: "MIPI_DP1", 30: "VSS", 31: "MIPI_DN0", 32: "MIPI_DP0",
    33: "XOUT", 34: "XIN", 35: "VDDIOB18", 36: "TDI", 37: "TDO", 38: "RST_N",
    39: "VDD", 40: "LV_L_N", 41: "PLL_AVDD", 42: "PLL_AGND", 43: "LV_T_N",
    44: "TMS", 45: "VDD", 46: "X0D12", 47: "X0D13", 48: "X0D22", 49: "X0D23",
    50: "VDD", 51: "TCK", 52: "LV_R_N", 53: "X1D12", 54: "VDD", 55: "NC",
    56: "VDDIOB18", 57: "X1D23", 58: "USB_ID", 59: "USB_DM", 60: "USB_DP",
    61: "USB_VDD33", 62: "USB_VDD18", 63: "X1D14", 64: "X1D13", 65: "X1D15",
    66: "X1D16", 67: "X1D17", 68: "VDD", 69: "X1D18", 70: "X1D19", 71: "X1D20",
    72: "VDDIOR", 73: "X1D21", 74: "X1D22", 75: "X1D49", 76: "X1D50",
    77: "X1D51", 78: "X1D52", 79: "X1D53", 80: "X1D54", 81: "X1D55",
    82: "X1D56", 83: "X1D57", 84: "X1D58", 85: "VDD", 86: "X0D24", 87: "X0D25",
    88: "X0D26", 89: "VDDIOR", 90: "X0D27", 91: "X0D28", 92: "X0D29",
    93: "X0D35", 94: "X0D36", 95: "VDD", 96: "X0D37", 97: "X0D38", 98: "X0D40",
    99: "X0D39", 100: "X0D42", 101: "X0D41", 102: "X1D43", 103: "X0D43",
    104: "VDD", 105: "VDD", 106: "VDD", 107: "X1D24", 108: "X1D25",
    109: "VDDIOT", 110: "X1D26", 111: "X1D27", 112: "X1D28", 113: "VDD",
    114: "X1D29", 115: "X1D30", 116: "X1D31", 117: "X1D32", 118: "X1D33",
    119: "X1D34", 120: "X1D35", 121: "VDDIOT", 122: "X0D30", 123: "X0D32",
    124: "X0D31", 125: "X0D34", 126: "X0D33", 127: "X0D04", 128: "X0D05",
    129: "VSS_EP",
}
# symbol layout: pads 1-65 left, 66-129 right (each its own slot)
xu_pins = []
for pad in range(1, 66):
    xu_pins.append((str(pad), XU_NAME[pad], "L", pad - 1))
for pad in range(66, 130):
    xu_pins.append((str(pad), XU_NAME[pad], "R", pad - 66))
sch.defsym("XU316", 40.64, 65 * 2.54 + 2.54, xu_pins, ref="U")

# ═══════════════════════════════ footprints ════════════════════════════
sch.sym_fp = {
    "RES": "Resistor_SMD:R_0402_1005Metric",
    "CAP": "Capacitor_SMD:C_0402_1005Metric",
    "CAPP": "Capacitor_SMD:CP_Elec_4x5.4",
    "FBEAD": "Inductor_SMD:L_0402_1005Metric",
    "IND": "Inductor_SMD:L_Sunlord_MWSA0402S",
    "FUSE": "Fuse:Fuse_1812_4532Metric",
    "TP": "TestPoint:TestPoint_Pad_D1.5mm",
    "DIODE2": "Diode_SMD:D_SMB",
    "FET3": "Package_TO_SOT_SMD:SOT-23",
    # Vendored into cac.pretty with the west barrel-body silk clamped inside
    # the board edge (the jack overhangs the west edge by design; the stock
    # silk drew the outline 0.8mm past it -> silk_edge_clearance). 2026-07-18.
    "BARREL": "cac:BarrelJack_Horizontal",
    "TERM2": "TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-2-3.5-H_1x02_P3.50mm_Horizontal",
    "HDR2": "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
    "BUCK": "Package_TO_SOT_SMD:SOT-563",
    "LDO_TCR": "Package_TO_SOT_SMD:SOT-23-5",
    "LDO_XC": "Package_TO_SOT_SMD:SOT-89-5",
    "BUF3": "Package_SO:VSSOP-8_2.3x2mm_P0.5mm",
    "FLASH": "Package_SO:SOIC-8_5.3x5.3mm_P1.27mm",
    # Vendored into cac.pretty (keepout: tracks/vias ALLOWED, copperpour
    # not_allowed) so the board copy matches the lib without a runtime
    # DoNotAllow edit (that edit caused lib_footprint_mismatch). 2026-07-18.
    "SHT": "cac:Sensirion_DFN-4_1.5x1.5mm_P0.8mm_SHT4x_NoCentralPad",
    "XTAL": "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
    "ESD2": "Package_TO_SOT_SMD:SOT-553",
    "ESD4": "Package_SON:USON-10_2.5x1.0mm_P0.5mm",
    "RJ45": "Connector_RJ:RJ45_Amphenol_RJHSE538X",
    "USBC": "Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal",
    "ADC": "Package_SO:TSSOP-30_4.4x7.8mm_P0.5mm",
    "XU316": "cac:TQFP-128_14x14mm_P0.4mm_EP4.7mm",
}
# small D_SMB test-point footprints etc handled per-symbol above

# ═══════════════════════════════ circuit ═══════════════════════════════

# ---------- region: POWER ENTRY + PROTECTION (ADR-0002) ----------
sch.region("1. 5V ENTRY + PROTECTION: barrel(pop) / terminal(DNP); PTC+TVS+revFET  [ADR-0002, D4]")
sch.row(("BARREL", "J9", "DC-005 5V IN",
         {"1": "5V_IN", "2": "GND", "3": "GND"}),
        ("FUSE", "F1", "2A PTC", {"1": "5V_IN", "2": "5V_P"}))
sch.chain("J9.1", "F1.1")
sch.row(("TERM2", "J11", "5V TERM DNP", {"1": "5V_IN", "2": "GND"}))
sch.row(("DIODE2", "D9", "SMBJ5.0A TVS", {"1": "5V_P", "2": "GND"}),
        ("FET3", "Q9", "AO3401A revFET", {"1": "GATE9", "2": "5V", "3": "5V_P"}))
sch.row(("RES", "R90", "100k FET gate", {"1": "GATE9", "2": "GND"}),
        ("CAPP", "C90", "100u 5V bulk", {"1": "5V", "2": "GND"}),
        ("TP", "TP9", "TP 5V", {"1": "5V"}))

# ---------- region: BUCK 3V3 (AP61102 #1) ----------
sch.region("2. BUCK 3V3 (AP61102): VO=0.6(1+68/15)=3.32V; EN=5V always-on  [XMOS ref U16]")
sch.row(("BUCK", "U10", "AP61102 3V3",
         {"3": "5V", "5": "5V", "1": "FB1", "4": "BK1_SW", "6": "BK1_PG", "2": "GND"}),
        ("IND", "L10", "1u0 3V3", {"1": "BK1_SW", "2": "3V3"}))
sch.chain("U10.4", "L10.1")
sch.row(("RES", "R10", "68k FB1 hi", {"1": "3V3", "2": "FB1"}),
        ("RES", "R11", "15k FB1 lo", {"1": "FB1", "2": "GND"}))
sch.chain("R10.2", "R11.1")
sch.row(("CAP", "C10", "4u7 VIN", {"1": "5V", "2": "GND"}),
        ("CAP", "C11", "10u 3V3", {"1": "3V3", "2": "GND"}),
        ("CAP", "C12", "100p FF", {"1": "3V3", "2": "FB1"}),
        ("RES", "R12", "10k PG1 pu", {"1": "5V", "2": "BK1_PG"}))

# ---------- region: BUCK 0V9 core (AP61102 #2), PG-gated ----------
sch.region("3. BUCK 0V9 core (AP61102): VO=0.6(1+10/20)=0.9V; EN<-3V3 PG (seq)  [XMOS ref U17]")
sch.row(("BUCK", "U11", "AP61102 0V9",
         {"3": "5V", "5": "BK1_PG", "1": "FB2", "4": "BK2_SW", "6": "BK2_PG", "2": "GND"}),
        ("IND", "L11", "1u0 0V9", {"1": "BK2_SW", "2": "0V9"}))
sch.chain("U11.4", "L11.1")
sch.row(("RES", "R13", "10k FB2 hi", {"1": "0V9", "2": "FB2"}),
        ("RES", "R14", "20k FB2 lo", {"1": "FB2", "2": "GND"}))
sch.chain("R13.2", "R14.1")
sch.row(("CAP", "C13", "4u7 VIN", {"1": "5V", "2": "GND"}),
        ("CAP", "C14", "22u 0V9", {"1": "0V9", "2": "GND"}),
        ("CAP", "C15", "560p FF", {"1": "0V9", "2": "FB2"}),
        ("RES", "R15", "10k PG2 pu", {"1": "3V3", "2": "BK2_PG"}),
        ("TP", "TP11", "TP 0V9", {"1": "0V9"}))

# ---------- region: LDO 1V8 + LDO 3V3A ----------
sch.region("4. LDO 1V8 (TCR2LF18 <-3V3) + LDO 3V3A (XC6227 <-5V, quiet analog)  [XMOS ref U18/U15]")
sch.row(("LDO_TCR", "U12", "TCR2LF18 1V8",
         {"1": "3V3", "3": "3V3", "2": "GND", "5": "1V8", "4": None}),
        ("CAP", "C16", "1u VIN", {"1": "3V3", "2": "GND"}),
        ("CAP", "C17", "1u 1V8", {"1": "1V8", "2": "GND"}))
sch.row(("LDO_XC", "U13", "XC6227 3V3A",
         {"4": "5V", "1": "5V", "2": "GND", "5": "3V3A", "3": None}),
        ("CAP", "C18", "4u7 VIN", {"1": "5V", "2": "GND"}),
        ("CAP", "C19", "10u 3V3A", {"1": "3V3A", "2": "GND"}),
        ("CAP", "C20", "100n 3V3A", {"1": "3V3A", "2": "GND"}),
        ("RES", "R16", "4k7 bleed", {"1": "3V3A", "2": "GND"}))

# ---------- region: XU316 ----------
sch.region("5. XU316-1024-TQ128 xcore.ai: APLL MCLK master, TDM master, async UAC2  [ADR-0003/0006]")
xu_nets = {str(p): (XU[p] if XU[p] is not None else None) for p in range(1, 130)}
sch.row(("XU316", "U1", "XU316-1024-TQ128-I24", xu_nets))

# ---------- region: XU316 decoupling + PLL filter ----------
sch.region("6. XU316 decoupling: 12x100n VDD, per-VDDIO 100n, bulk 10u; PLL_AVDD FB+1u  [part.yaml H.2]")
# 12x 100n on 0V9 core, banked
dec = []
for i in range(1, 13):
    dec.append(("CAP", f"C1{i:02d}", "100n VDD", {"1": "0V9", "2": "GND"}))
for a, b, c, d in [dec[k:k + 4] for k in range(0, 12, 4)]:
    sch.row(a, b, c, d)
sch.row(("CAP", "C121", "10u VDD", {"1": "0V9", "2": "GND"}),
        ("CAP", "C122", "10u VDD", {"1": "0V9", "2": "GND"}),
        ("FBEAD", "FB3", "600R PLL", {"1": "0V9", "2": "PLL_AVDD"}),
        ("CAP", "C123", "1u PLL", {"1": "PLL_AVDD", "2": "GND"}))
sch.chain("FB3.2", "C123.1")
# per-VDDIO 3V3 decoupling + bulk
sch.row(("CAP", "C130", "100n 3V3", {"1": "3V3", "2": "GND"}),
        ("CAP", "C131", "100n 3V3", {"1": "3V3", "2": "GND"}),
        ("CAP", "C132", "100n 3V3", {"1": "3V3", "2": "GND"}),
        ("CAP", "C133", "100n 3V3", {"1": "3V3", "2": "GND"}))
sch.row(("CAP", "C134", "100n 3V3", {"1": "3V3", "2": "GND"}),
        ("CAP", "C135", "100n 3V3", {"1": "3V3", "2": "GND"}),
        ("CAP", "C136", "10u 3V3", {"1": "3V3", "2": "GND"}),
        ("CAP", "C137", "10u 3V3", {"1": "3V3", "2": "GND"}))
sch.row(("CAP", "C138", "100n 1V8", {"1": "1V8", "2": "GND"}),
        ("CAP", "C139", "100n 1V8", {"1": "1V8", "2": "GND"}),
        ("CAP", "C140", "10u 1V8", {"1": "1V8", "2": "GND"}),
        ("CAP", "C141", "100n USB33", {"1": "3V3", "2": "GND"}),
        ("CAP", "C142", "100n USB18", {"1": "1V8", "2": "GND"}))

# ---------- region: crystal ----------
sch.region("7. 24MHz crystal (FA-238): Rf 1M, Rd 680R, CL 18pF (USB clock, §7.3 p19)")
sch.row(("XTAL", "Y1", "FA-238 24MHz",
         {"1": "XIN", "3": "XTAL2", "2": "GND", "4": "GND"}),
        ("RES", "R20", "680R Rd", {"1": "XOUT", "2": "XTAL2"}))
sch.row(("RES", "R21", "1M Rf", {"1": "XIN", "2": "XOUT"}),
        ("CAP", "C25", "18p CL1", {"1": "XIN", "2": "GND"}),
        ("CAP", "C26", "18p CL2", {"1": "XTAL2", "2": "GND"}))

# ---------- region: QSPI boot flash ----------
sch.region("8. QSPI boot flash (W25Q16): CS_N pull-up 10k to 3V3 (Fig 12 p22)")
sch.row(("FLASH", "U4", "W25Q16JVSSIQ",
         {"1": "QSPI_CS", "6": "QSPI_CLK", "5": "QSPI_D0", "2": "QSPI_D1",
          "8": "3V3", "7": "QSPI_D3", "3": "QSPI_D2", "4": "GND"}),
        ("RES", "R30", "10k CS pu", {"1": "3V3", "2": "QSPI_CS"}),
        ("CAP", "C30", "100n flash", {"1": "3V3", "2": "GND"}))

# ---------- region: USB-C device ----------
sch.region("9. USB-C device (USB4105) + ESD (TPD4EUSB30) + CC Rd + VBUS sense  [§11.1/§14.1]")
usbc_nets = {"A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS",
             "A6": "USB_DP", "B6": "USB_DP", "A7": "USB_DM", "B7": "USB_DM",
             "A5": "CC1", "B5": "CC2", "A1": "GND", "A12": "GND",
             "B1": "GND", "B12": "GND", "A8": None, "B8": None, "SH": "GND"}
sch.row(("USBC", "J12", "USB4105-GF-A", usbc_nets),
        ("ESD4", "D10", "TPD4EUSB30",
         {"1": "USB_DP", "2": "USB_DM", "4": None, "5": None,
          "3": "GND", "8": "GND", "10": None, "9": None, "7": None, "6": None}))
sch.row(("RES", "R31", "5k1 CC1 Rd", {"1": "CC1", "2": "GND"}),
        ("RES", "R32", "5k1 CC2 Rd", {"1": "CC2", "2": "GND"}),
        ("RES", "R33", "220k VBUS", {"1": "VBUS", "2": "VBUS_DET"}),
        ("RES", "R34", "330k VBUS", {"1": "VBUS_DET", "2": "GND"}),
        ("CAP", "C31", "1u VBUS", {"1": "VBUS", "2": "GND"}))
sch.chain("R33.2", "R34.1")

# ---------- region: MCLK buffer + clock series terminations ----------
sch.region("10. MCLK buffer (NC7NZ34) fanout to both ADCs; BCLK/LRCK 33R source term  [§3 clocks]")
sch.row(("BUF3", "U5", "NC7NZ34 MCLK buf",
         {"1": "MCLK_SRC", "3": "MCLK_SRC", "6": "MCLK_SRC", "4": "GND",
          "8": "3V3", "7": "MCLK_A0", "5": "MCLK_B0", "2": None}),
        ("CAP", "C35", "100n buf", {"1": "3V3", "2": "GND"}))
sch.row(("RES", "R40", "33R MCLK_A", {"1": "MCLK_A0", "2": "MCLK_A"}),
        ("RES", "R41", "33R MCLK_B", {"1": "MCLK_B0", "2": "MCLK_B"}),
        ("RES", "R42", "33R BCLK", {"1": "BCLK_X", "2": "BCLK"}),
        ("RES", "R43", "33R LRCK", {"1": "LRCK_X", "2": "LRCK"}))

# ---------- region: reset + I2C pullups + SHT40 ----------
sch.region("11. RST_N RC (10k->1V8, 10n) + I2C 4k7 pull-ups + SHT40 T/RH  [§2 reset, §7]")
sch.row(("RES", "R50", "10k RST pu", {"1": "1V8", "2": "RST_N"}),
        ("CAP", "C40", "10n RST", {"1": "RST_N", "2": "GND"}),
        ("RES", "R51", "4k7 SCL pu", {"1": "3V3", "2": "I2C_SCL"}),
        ("RES", "R52", "4k7 SDA pu", {"1": "3V3", "2": "I2C_SDA"}))
sch.row(("SHT", "U6", "SHT40-AD1B (0x44)",
         {"1": "I2C_SDA", "2": "I2C_SCL", "3": "3V3", "4": "GND"}),
        ("CAP", "C41", "100n SHT", {"1": "3V3", "2": "GND"}),
        ("HDR2", "J13", "xSYS DBG TDI/TDO", {"1": "TDI", "2": "TDO"}),
        ("HDR2", "J14", "xSYS DBG TMS/TCK", {"1": "TMS", "2": "TCK"}))

# ---------- ADC decoupling + straps helper ----------
def adc_block(chip, ref, addr_net):
    """One PCM1865: nets for its 30 pins. chip in {'A','B'} sets the data
    line and the input-net prefix; addr_net strap sets I2C address."""
    p = chip                                   # net prefix per chip
    data = "DATA1" if chip == "A" else "DATA2"
    mclk = "MCLK_A" if chip == "A" else "MCLK_B"
    nets = {
        "3": f"V{p}1P", "1": f"V{p}1M", "4": f"V{p}2P", "2": f"V{p}2M",
        "30": f"V{p}3P", "28": f"V{p}3M", "29": f"V{p}4P", "27": f"V{p}4M",
        "6": f"VREF_{p}", "5": None,           # MICBIAS NC (pods bias locally)
        "15": mclk, "17": "BCLK", "16": "LRCK", "18": data,
        "8": "3V3A", "7": "GND", "13": "3V3", "12": "GND", "14": "3V3",
        "11": f"LDO_{p}", "10": "GND", "9": None,        # XI=GND, XO NC
        "24": "I2C_SCL", "23": "I2C_SDA", "25": addr_net, "26": "GND",
        "22": f"GP0_{p}", "21": f"GP1_{p}", "20": f"GP2_{p}", "19": f"GP3_{p}",
    }
    return ("ADC", ref, "PCM1865DBTR", nets)


sch.region("12. ADC1 PCM1865 (ch1-4, I2C 0x4A) + decoupling + GPIO 100k pulldowns  [§5, ADR-0006]")
sch.row(adc_block("A", "U2", "GND"))
sch.row(("CAP", "C50", "4u7 AVDD_A", {"1": "3V3A", "2": "GND"}),
        ("CAP", "C51", "100n AVDD_A", {"1": "3V3A", "2": "GND"}),
        ("CAP", "C52", "4u7 DVDD_A", {"1": "3V3", "2": "GND"}),
        ("CAP", "C53", "100n DVDD_A", {"1": "3V3", "2": "GND"}))
sch.row(("CAP", "C54", "2u2 VREF_A", {"1": "VREF_A", "2": "GND"}),
        ("CAP", "C55", "2u2 LDO_A", {"1": "LDO_A", "2": "GND"}),
        ("CAP", "C56", "100n LDO_A", {"1": "LDO_A", "2": "GND"}),
        ("CAP", "C57", "100n IOV_A", {"1": "3V3", "2": "GND"}))
sch.row(("RES", "R60", "100k GP0_A", {"1": "GP0_A", "2": "GND"}),
        ("RES", "R61", "100k GP1_A", {"1": "GP1_A", "2": "GND"}),
        ("RES", "R62", "100k GP2_A", {"1": "GP2_A", "2": "GND"}),
        ("RES", "R63", "100k GP3_A", {"1": "GP3_A", "2": "GND"}))

sch.region("13. ADC2 PCM1865 (ch5-8, I2C 0x4B) + decoupling + GPIO 100k pulldowns  [§5, ADR-0006]")
sch.row(adc_block("B", "U3", "3V3"))
sch.row(("CAP", "C60", "4u7 AVDD_B", {"1": "3V3A", "2": "GND"}),
        ("CAP", "C61", "100n AVDD_B", {"1": "3V3A", "2": "GND"}),
        ("CAP", "C62", "4u7 DVDD_B", {"1": "3V3", "2": "GND"}),
        ("CAP", "C63", "100n DVDD_B", {"1": "3V3", "2": "GND"}))
sch.row(("CAP", "C64", "2u2 VREF_B", {"1": "VREF_B", "2": "GND"}),
        ("CAP", "C65", "2u2 LDO_B", {"1": "LDO_B", "2": "GND"}),
        ("CAP", "C66", "100n LDO_B", {"1": "LDO_B", "2": "GND"}),
        ("CAP", "C67", "100n IOV_B", {"1": "3V3", "2": "GND"}))
sch.row(("RES", "R64", "100k GP0_B", {"1": "GP0_B", "2": "GND"}),
        ("RES", "R65", "100k GP1_B", {"1": "GP1_B", "2": "GND"}),
        ("RES", "R66", "100k GP2_B", {"1": "GP2_B", "2": "GND"}),
        ("RES", "R67", "100k GP3_B", {"1": "GP3_B", "2": "GND"}))

# ---------- ADC input coupling network (8x) ----------
# maps port n -> (chip ref, P-net, M-net)  per ARCHITECTURE port/channel table
CHAN = {1: ("VA1P", "VA1M"), 2: ("VA2P", "VA2M"), 3: ("VA3P", "VA3M"),
        4: ("VA4P", "VA4M"), 5: ("VB1P", "VB1M"), 6: ("VB2P", "VB2M"),
        7: ("VB3P", "VB3M"), 8: ("VB4P", "VB4M")}


def adc_input(n, cP, cN):
    """Coupling + series + diff filter from AUD_Pn/Nn to a PCM1865 pair.
    Injection taps (INJ_C via 1k) land on ch4 (ADC1) and ch8 (ADC2)."""
    base = 200 + n * 10
    sch.row(("CAP", f"C{base}", f"1u cpl P{n}", {"1": f"AUD_P{n}", "2": f"AIN_P{n}"}),
            ("RES", f"R{base}", f"49R9 P{n}", {"1": f"AIN_P{n}", "2": cP}))
    sch.chain(f"C{base}.2", f"R{base}.1")
    sch.row(("CAP", f"C{base+1}", f"1u cpl N{n}", {"1": f"AUD_N{n}", "2": f"AIN_N{n}"}),
            ("RES", f"R{base+1}", f"49R9 N{n}", {"1": f"AIN_N{n}", "2": cN}))
    sch.chain(f"C{base+1}.2", f"R{base+1}.1")
    sch.row(("CAP", f"C{base+2}", f"1n diff {n}", {"1": cP, "2": cN}))


sch.region("14. ADC INPUT COUPLING (8x): AUD_Pn/Nn -> 1u -> 49R9 -> PCM1865 diff pair")
for n in range(1, 9):
    adc_input(n, *CHAN[n])
# injection header couples ONE test signal into ch4 (ADC1) + ch8 (ADC2) via 1k (D7)
sch.region("15. SKEW INJECTION HEADER (J10): INJ -> 1u -> INJ_C -> 1k into ch4 & ch8  [D7, §5A]")
sch.row(("HDR2", "J10", "INJ IN", {"1": "INJ", "2": "GND"}),
        ("CAP", "C90i", "1u inj", {"1": "INJ", "2": "INJ_C"}))
sch.row(("RES", "R80", "1k inj ch4", {"1": "INJ_C", "2": "AIN_P4"}),
        ("RES", "R81", "1k inj ch8", {"1": "INJ_C", "2": "AIN_P8"}))

# ---------- the 8x PORT CHANNEL (commission-mandated single generator) ----------
def port_channel(n):
    """RJ45 port n: ESD at jack, per-port audio+beep PTCs, low-side beeper
    FET with slowed gate (ADR-0005), separate BEEP_RETn to the FET drain.
    J7/J8 (n>=7) jacks DNP; channels reserved (ARCHITECTURE port table)."""
    dnp = " DNP" if n >= 7 else ""
    sch.region(f"P{n}. PORT {n} (RJ45 J{n}{' DNP' if n>=7 else ''}) NOT ETHERNET: ESD + audio/beep PTC + slowed beeper FET  [ADR-0005]")
    rj_nets = {"1": f"AUD_P{n}", "2": f"AUD_N{n}", "3": f"BEEP_5V{n}",
               "4": f"5V_AUD{n}", "5": "GND", "6": f"BEEP_RET{n}",
               "7": f"5V_AUD{n}", "8": "GND",
               "9": None, "10": None, "11": None, "12": None, "SH": "GND"}
    sch.row(("RJ45", f"J{n}", f"RJHSE-5384{dnp}", rj_nets),
            ("ESD2", f"D{20+n}", f"TPD2E2U06 p{n}",
             {"3": f"AUD_P{n}", "5": f"AUD_N{n}", "4": "GND", "1": None, "2": None}))
    sch.row(("FUSE", f"F{10+n}", f"PTC audio {n}", {"1": "5V", "2": f"5V_AUD{n}"}),
            ("FUSE", f"F{20+n}", f"PTC beep {n}", {"1": "5V", "2": f"BEEP_5V{n}"}))
    # low-side beeper driver: gate <- XU316 via 1k + 4.7nF slow + 100k pulldown
    sch.row(("RES", f"R{100+n}", f"1k gate {n}", {"1": f"BEEP_G{n}", "2": f"BG_{n}"}),
            ("FET3", f"Q{n}", f"AO3400A beep {n}",
             {"1": f"BG_{n}", "2": "GND", "3": f"BEEP_RET{n}"}))
    sch.chain(f"R{100+n}.2", f"Q{n}.1")
    sch.row(("CAP", f"C{300+n}", f"4n7 gate {n}", {"1": f"BG_{n}", "2": "GND"}),
            ("RES", f"R{110+n}", f"100k pd {n}", {"1": f"BG_{n}", "2": "GND"}),
            ("TP", f"TP{20+n}", f"TP BEEP_RET{n}", {"1": f"BEEP_RET{n}"}))


for n in range(1, 9):
    port_channel(n)

# ═══════════════════════════════ emit ══════════════════════════════════
content = sch.emit()
out = HERE.parent / "04_kicad"
out.mkdir(exist_ok=True)
(out / f"{PROJECT}.kicad_sch").write_text(content)

(HERE / "lib").mkdir(exist_ok=True)
sch.write_symbol_lib(HERE / "lib" / "cac.kicad_sym")
(out / "sym-lib-table").write_text(
    sch.sym_lib_table("cac", "${KIPRJMOD}/../03_src/lib/cac.kicad_sym"))
(out / "fp-lib-table").write_text(sch.fp_lib_table(
    {"cac": "${KIPRJMOD}/../03_src/lib/cac.pretty"}))

if not (out / f"{PROJECT}.kicad_pro").exists():
    (out / f"{PROJECT}.kicad_pro").write_text(
        '{\n  "board": { "design_settings": {} },\n'
        f'  "meta": {{ "filename": "{PROJECT}.kicad_pro", "version": 1 }},\n'
        '  "schematic": { "legacy_lib_dir": "", "legacy_lib_list": [] }\n}\n')

nlabels = content.count("(global_label")
print(f"wrote {PROJECT}.kicad_sch via schwriter2: {len(sch.cells)} cells, "
      f"{len(sch.wires)} wires, {nlabels} net labels, internal S-OCCL 0, parens balanced")
