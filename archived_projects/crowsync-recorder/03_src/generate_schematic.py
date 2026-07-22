"""Generate 04_kicad/crowsync_recorder.kicad_sch — schwriter2 port.

The author declares STRUCTURE ONLY (symbols, cells+nets, regions, rows,
chains); the schwriter2 engine computes every coordinate from text envelopes
(label plates, refs, values are the schematic's courtyards), wires the
story-critical facing pins (canon S6), and gates itself on an internal
S-OCCL == 0 before writing. No hand coordinates anywhere in this file.

Pin numbers are PHYSICAL PADS from 02_parts/<MPN>/part.yaml (each cites its
datasheet figure): PCM2900C SBFS039 p6 pinout + Table 1; TLV9062 SBOS839N
fig 5-6/table 5-3 p6; TPS7A20 SBVS338H fig 4-4 p4; USBLC6 UMW sect 4 p1;
YSX321SL sheet. Circuit per 01_docs/ARCHITECTURE.md + DETAIL_DESIGN.md;
decisions in 01_docs/decisions/. Net assignments are copied MECHANICALLY
from the pre-port generator (netlist parity is a gate).
Run: python3 03_src/generate_schematic.py  (writes into 04_kicad/)
"""

import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parents[2] / "skills" / "kicad-pcb" / "scripts"))
from schwriter2 import Schematic  # noqa: E402

PROJECT = "crowsync_recorder"
SMALL = {"RES", "CAP", "FB", "LED", "XTAL4"}

rev = Schematic.rev_from_git(HERE, "CW_REV", "crowsync-v*").replace("crowsync-", "")
sch = Schematic(
    PROJECT, "crowsync-recorder", paper="A2",
    comment="USB stereo recorder: CH1 mic preamp, CH2 GNSS PPS; 01_docs/ + ADRs in repo",
    rev=rev, small_syms=SMALL, libname="csr")

# ------------------------------------------------------------------ symbols
sch.defsym("RES", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="R")
sch.defsym("CAP", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="C")
sch.defsym("FB", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="FB")
sch.defsym("LED", 7.62, 5.08, [("1", "K", "L", 0), ("2", "A", "R", 0)], ref="D")  # pad1 = cathode
# GCT USB4105 16P receptacle, sink (UFP) role — pad names = footprint pads
sch.defsym("USBC", 15.24, 33.02,
           [("A4", "VBUS", "L", 0), ("A9", "VBUS", "L", 1), ("B4", "VBUS", "L", 2), ("B9", "VBUS", "L", 3),
            ("A5", "CC1", "L", 5), ("B5", "CC2", "L", 6),
            ("A1", "GND", "L", 8), ("A12", "GND", "L", 9), ("B1", "GND", "L", 10), ("B12", "GND", "L", 11),
            ("A6", "D+", "R", 0), ("A7", "D-", "R", 1), ("B6", "D+", "R", 2), ("B7", "D-", "R", 3),
            ("A8", "SBU1", "R", 5), ("B8", "SBU2", "R", 6), ("SH", "SHIELD", "R", 9)], ref="J")
# USBLC6-2SC6 SOT-23-6 (UMW datasheet sect 4, p1): 1 I/O1, 2 GND, 3 I/O2, 4 I/O2, 5 VBUS, 6 I/O1
sch.defsym("USBLC6", 10.16, 17.78,
           [("1", "I/O1", "L", 0), ("3", "I/O2", "L", 2), ("2", "GND", "L", 5),
            ("6", "I/O1'", "R", 0), ("4", "I/O2'", "R", 2), ("5", "VBUS", "R", 5)], ref="D")
# PCM2900C SSOP-28 DB (SBFS039 p6 pinout figure + Table 1) — PHYSICAL pads
sch.defsym("PCM2900C", 20.32, 48.26,
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
sch.defsym("TLV9062", 12.7, 22.86,
           [("3", "IN1+", "L", 0), ("2", "IN1-", "L", 2), ("5", "IN2+", "L", 4), ("6", "IN2-", "L", 6),
            ("8", "V+", "R", 0), ("1", "OUT1", "R", 2), ("7", "OUT2", "R", 4), ("4", "V-", "R", 7)],
           ref="U")
# TPS7A20 DBV SOT-23-5 (SBVS338H fig 4-4, p4): 1 IN, 2 GND, 3 EN, 4 NC, 5 OUT
sch.defsym("TPS7A20", 10.16, 12.7,
           [("1", "IN", "L", 0), ("3", "EN", "L", 1), ("2", "GND", "L", 3),
            ("5", "OUT", "R", 0), ("4", "NC", "R", 2)], ref="U")
# YXC 3225 crystal (YSX321SL sheet): 1/3 electrodes, 2/4 GND
sch.defsym("XTAL4", 10.16, 10.16,
           [("1", "X1", "L", 0), ("2", "G", "L", 2), ("3", "X2", "R", 0), ("4", "G", "R", 2)], ref="Y")
# JST GH headers (MP = mounting pads, tied GND)
sch.defsym("JST3", 5.08, 12.7,
           [("1", "P1", "L", 0), ("2", "P2", "L", 1), ("3", "P3", "L", 2), ("MP", "MP", "L", 3)], ref="J")
sch.defsym("JST2", 5.08, 10.16,
           [("1", "P1", "L", 0), ("2", "P2", "L", 1), ("MP", "MP", "L", 2)], ref="J")

# ------------------------------------------------------------------ footprints
sch.sym_fp = {
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

# ═══════════════════ circuit: structure only, nets verbatim ═══════════════════

# --- region 1: USB entry ---
sch.region("1. USB-C INPUT (UFP, 5V bus power)   [ADR-0001 protection]")
sch.row(("USBC", "J1", "USB4105-GF-A",
         {"A4": "VBUS_5V", "A9": "VBUS_5V", "B4": "VBUS_5V", "B9": "VBUS_5V",
          "A5": "CC1", "B5": "CC2",
          "A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND",
          "A6": "DP_C", "A7": "DM_C", "B6": "DP_C", "B7": "DM_C",
          "A8": None, "B8": None, "SH": "GND"}),
        ("USBLC6", "D1", "USBLC6-2SC6 USB",
         {"1": "DP_C", "6": "DP_C", "3": "DM_C", "4": "DM_C",
          "2": "GND", "5": "VBUS_5V"}))
sch.chain("J1.A6", "D1.1")  # USB D+ story wire into the ESD array
sch.row(("RES", "R4", "5k1 Rd CC1 (UFP)", {"1": "CC1", "2": "GND"}),
        ("RES", "R5", "5k1 Rd CC2 (UFP)", {"1": "CC2", "2": "GND"}))
sch.row(("RES", "R1", "22R D+ series", {"1": "DP_C", "2": "DP"}),
        ("RES", "R3", "1k5 D+ pullup (VDDI)", {"1": "DP", "2": "VDDI"}))
sch.chain("R1.2", "R3.1")  # D+ series R into the pullup node, drawn
sch.row(("RES", "R2", "22R D- series", {"1": "DM_C", "2": "DM"}))
sch.row(("CAP", "C12", "10u 5V bulk", {"1": "VBUS_5V", "2": "GND"}),
        ("CAP", "C13", "100n 5V", {"1": "VBUS_5V", "2": "GND"}))

# --- region 2: codec ---
sch.region("2. PCM2900C USB AUDIO CODEC (bus-powered fig-38; ADR-0002)")
sch.row(("RES", "R7", "2R2 VBUS filter", {"1": "VBUS_5V", "2": "VBUS_PCM"}),
        ("CAP", "C11", "1u VBUS pin", {"1": "VBUS_PCM", "2": "GND"}))
sch.chain("R7.2", "C11.1")  # VBUS filter -> pin cap, drawn
sch.row(("PCM2900C", "U1", "PCM2900CDBR",
         {"1": "DP", "2": "DM", "3": "VBUS_PCM",
          "8": "VDDI", "9": "VDDI",
          "5": None, "6": None, "7": None,
          "12": "VINL", "13": "VINR", "14": "VCOM",
          "4": "GND", "11": "GND", "18": "GND",
          "21": "XTI", "20": "XTO",
          "27": "VDDI", "23": "VCCXI", "10": "VCCCI", "19": "VCCP2", "17": "VCCP1",
          "28": "SSPND", "25": None, "24": "GND",
          "15": None, "16": None,
          "26": "GND", "22": "GND"}))
sch.row(("CAP", "C1", "10u VCCCI", {"1": "VCCCI", "2": "GND"}),
        ("CAP", "C2", "10u VCOM", {"1": "VCOM", "2": "GND"}))
sch.row(("CAP", "C3", "1u VDDI", {"1": "VDDI", "2": "GND"}),
        ("CAP", "C4", "1u VCCXI", {"1": "VCCXI", "2": "GND"}))
sch.row(("CAP", "C7", "1u VCCP2I", {"1": "VCCP2", "2": "GND"}),
        ("CAP", "C8", "1u VCCP1I", {"1": "VCCP1", "2": "GND"}))
sch.row(("RES", "R17", "1k LED SSPND", {"1": "SSPND", "2": "LED3_A"}),
        ("LED", "D3", "green ACT", {"1": "GND", "2": "LED3_A"}))   # pad1 = cathode
sch.row(("RES", "R18", "2k2 LED 5V", {"1": "VBUS_5V", "2": "LED4_A"}),
        ("LED", "D4", "green PWR", {"1": "GND", "2": "LED4_A"}))

# --- region 3: crystal ---
sch.region("3. 12 MHz CRYSTAL (CL 20pF -> 33p)")
sch.row(("CAP", "C5", "33p XTI", {"1": "XTI", "2": "GND"}),
        ("XTAL4", "Y1", "12MHz 3225 20pF", {"1": "XTI", "3": "XTO", "2": "GND", "4": "GND"}),
        ("CAP", "C6", "33p XTO", {"1": "XTO", "2": "GND"}))
sch.chain("Y1.3", "C6.1")  # XTO electrode -> load cap, drawn
sch.row(("RES", "R6", "1M XTI-XTO", {"1": "XTI", "2": "XTO"}))

# --- region 4: analog rail ---
sch.region("4. 3V3A RAIL (TPS7A2033, ADR-0002)")
sch.row(("CAP", "C14", "1u LDO in", {"1": "VBUS_5V", "2": "GND"}),
        ("TPS7A20", "U3", "TPS7A2033PDBVR",
         {"1": "VBUS_5V", "3": "VBUS_5V", "2": "GND", "5": "3V3A", "4": None}),
        ("CAP", "C15", "10u 3V3A", {"1": "3V3A", "2": "GND"}))
sch.chain("U3.5", "C15.1")  # LDO out -> output cap (C14->U3 facing nets differ: labels)
sch.row(("CAP", "C16", "100n 3V3A U2", {"1": "3V3A", "2": "GND"}))

# --- section 5: mic input + preamp ---
sch.region("5. CH1 MIC: bias/ESD/series-R -> TLV9062A gain 4.0 (39k alt = 40x; ADR-0003)")
sch.row(("JST3", "J2", "JST-GH mic",
         {"1": "MIC", "2": "GND", "3": "GND", "MP": "GND"}),
        ("USBLC6", "D2", "USBLC6-2SC6 harness",
         {"1": "MIC", "6": "MIC", "3": "PPS", "4": "PPS", "2": "GND", "5": "3V3A"}))
sch.row(("FB", "FB1", "600R@100MHz bias", {"1": "3V3A", "2": "MIC_BIAS_F"}),
        ("CAP", "C17", "10u bias res", {"1": "MIC_BIAS_F", "2": "GND"}))
sch.chain("FB1.2", "C17.1")  # bias feed -> filter reservoir, drawn
sch.row(("CAP", "C18", "100n bias", {"1": "MIC_BIAS_F", "2": "GND"}),
        ("RES", "R8", "2k2 mic bias", {"1": "MIC_BIAS_F", "2": "MIC"}))
sch.row(("RES", "R9", "100R mic series", {"1": "MIC", "2": "MIC_IN"}),
        ("CAP", "C19", "1u mic couple", {"1": "MIC_IN", "2": "AMP_INP"}),
        ("TLV9062", "U2", "TLV9062IDR",
         {"3": "AMP_INP", "2": "AMP_FB", "1": "AMP_OUT",
          "5": "VCOM", "6": "VCOM_BUF", "7": "VCOM_BUF",
          "8": "3V3A", "4": "GND"}))
sch.chain("R9.2", "C19.1")   # mic series R -> coupling cap, drawn
sch.chain("C19.2", "U2.3")   # coupling cap -> preamp IN+, drawn
sch.row(("RES", "R10", "100k bias->VCOM", {"1": "AMP_INP", "2": "VCOM_BUF"}))
sch.row(("RES", "R11", "3k01 Rf (gain 4.0)", {"1": "AMP_OUT", "2": "AMP_FB"}),
        ("RES", "R12", "1k Rg", {"1": "AMP_FB", "2": "RG_X"}),
        ("CAP", "C20", "10u Cg (15.9Hz)", {"1": "RG_X", "2": "GND"}))
sch.chain("R11.2", "R12.1")  # feedback node, drawn
sch.chain("R12.2", "C20.1")  # gain-set leg, drawn
sch.row(("RES", "R13", "100R amp out", {"1": "AMP_OUT", "2": "VINL_F"}),
        ("CAP", "C9", "1u VINL couple", {"1": "VINL_F", "2": "VINL"}))
sch.chain("R13.2", "C9.1")   # amp out -> VINL coupling (codec VINL cross-region: label)
sch.row(("CAP", "C21", "1n RF stop", {"1": "VINL_F", "2": "GND"}))

# --- section 6: PPS input ---
sch.region("6. CH2 PPS: ESD/series-R -> 22k/10k divider (1.03Vpp) -> AC couple")
sch.row(("JST2", "J3", "JST-GH PPS", {"1": "PPS", "2": "GND", "MP": "GND"}))
sch.row(("RES", "R14", "100R PPS series", {"1": "PPS", "2": "PPS_A"}),
        ("RES", "R15", "22k div top", {"1": "PPS_A", "2": "PPS_ATT"}),
        ("RES", "R16", "10k div bottom", {"1": "PPS_ATT", "2": "GND"}))
sch.chain("R14.2", "R15.1")  # PPS divider chain, drawn
sch.chain("R15.2", "R16.1")
sch.row(("CAP", "C10", "1u VINR couple", {"1": "PPS_ATT", "2": "VINR"}))

# ------------------------------------------------------------------ gates + emit
# canon S4 gate: emitted no_connects must exactly match the sanctioned list —
# a new None-net pin is an ACCIDENTAL float until reviewed and added here.
nc_pins = {(c.ref, p) for c in sch.cells.values() for p, n in c.nets.items() if n is None}
assert nc_pins == SANCTIONED_FLOATS, (
    "unsanctioned floats", sorted(nc_pins ^ SANCTIONED_FLOATS))

content = sch.emit()  # layout + wire-safety + internal S-OCCL gates inside
out = HERE.parent / "04_kicad"
out.mkdir(exist_ok=True)
(out / f"{PROJECT}.kicad_sch").write_text(content)

# Project symbol library + sym-lib-table so ERC can resolve the 'csr' lib
# (kills the lib_symbol_issues "library not in configuration" warnings).
# The library is generated from the SAME symbols the schematic embeds.
(HERE / "lib").mkdir(exist_ok=True)
sch.write_symbol_lib(HERE / "lib" / "csr.kicad_sym")
(out / "sym-lib-table").write_text(
    sch.sym_lib_table("csr", "${KIPRJMOD}/../03_src/lib/csr.kicad_sym"))
# fp-lib-table is owned by 03_src/generate_board.py (board side) — not written here.

# NEVER overwrite an existing project file — it carries DRC floors/netclasses.
if not (out / f"{PROJECT}.kicad_pro").exists():
    (out / f"{PROJECT}.kicad_pro").write_text(
        '{\n  "board": { "design_settings": {} },\n'
        f'  "meta": {{ "filename": "{PROJECT}.kicad_pro", "version": 1 }},\n'
        '  "schematic": { "legacy_lib_dir": "", "legacy_lib_list": [] }\n}\n')

nlabels = content.count("(global_label")
nnc = content.count("(no_connect")
print(f"wrote {PROJECT}.kicad_sch via schwriter2: {len(sch.cells)} cells, "
      f"{len(sch.wires)} wires, {nlabels} net labels, {nnc} no_connects, "
      f"internal S-OCCL 0, parens balanced")
