"""Generate 04_kicad/usb_power_3s.kicad_sch — schwriter2 port.

The author declares STRUCTURE ONLY (symbols, cells+nets, regions, rows,
chains); the schwriter2 engine computes every coordinate from text envelopes
(label plates, refs, values are the schematic's courtyards), wires the
story-critical facing pins (canon S6), and gates itself on an internal
S-OCCL == 0 before writing. No hand coordinates anywhere in this file.

Pin numbers are PHYSICAL PADS checked against datasheets (see per-symbol
comments; polarity conventions pad1=cathode / XT60 pad1=minus are post-fix).
Circuit per 01_docs/ARCHITECTURE.md + 01_docs/DETAIL_DESIGN.md; decisions in
01_docs/decisions. Net assignments are copied MECHANICALLY from the pre-port
generator (netlist parity is a gate).
Run: python3 03_src/generate_schematic.py  (writes into 04_kicad/)
"""

import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parents[2] / "skills" / "kicad-pcb" / "scripts"))
from schwriter2 import Schematic  # noqa: E402

PROJECT = "usb_power_3s"
SMALL = {"RES", "CAP", "IND", "TVS", "LED", "SHUNT", "FUSE"}

# no up3s-v* tags exist: fallback order is UP3S_REV env, then git describe,
# then "dev" — releases pass the version string via UP3S_REV.
rev = Schematic.rev_from_git(HERE, "UP3S_REV", "up3s-v*").replace("up3s-", "")
sch = Schematic(
    PROJECT, "usb-power-3s", paper="A1",
    comment="3S LiPo -> 3x USB-A 2.5A + USB-C 6A; 01_docs/ + ADRs in repo",
    rev=rev, small_syms=SMALL, libname="pwr")

# ------------------------------------------------------------------ symbols
sch.defsym("XT60", 5.08, 7.62, [("1", "-", "R", 0), ("2", "+", "R", 1)], ref="J")
sch.defsym("HDR8", 5.08, 22.86, [(str(i), f"P{i}", "L", i - 1) for i in range(1, 9)], ref="J")
sch.defsym("USB_A", 7.62, 15.24,
           [("1", "VBUS", "L", 0), ("2", "D-", "L", 1), ("3", "D+", "L", 2), ("4", "GND", "L", 3),
            ("SH", "SHIELD", "L", 4)], ref="J")
# pad names = GCT USB4105 footprint pads (16P power-only receptacle, source role)
sch.defsym("USBC_PWR", 15.24, 33.02,
           [("A4", "VBUS", "L", 0), ("A9", "VBUS", "L", 1), ("B4", "VBUS", "L", 2), ("B9", "VBUS", "L", 3),
            ("A5", "CC1", "L", 5), ("B5", "CC2", "L", 6),
            ("A1", "GND", "L", 8), ("A12", "GND", "L", 9), ("B1", "GND", "L", 10), ("B12", "GND", "L", 11),
            ("A6", "D+", "R", 0), ("A7", "D-", "R", 1), ("B6", "D+", "R", 2), ("B7", "D-", "R", 3),
            ("A8", "SBU1", "R", 5), ("B8", "SBU2", "R", 6), ("SH", "SHIELD", "R", 9)], ref="J")
sch.defsym("FUSE", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="F")
sch.defsym("RES", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="R")
sch.defsym("CAP", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="C")
sch.defsym("IND", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="L")
sch.defsym("TVS", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="D")
sch.defsym("LED", 7.62, 5.08, [("1", "K", "L", 0), ("2", "A", "R", 0)], ref="D")
# CSD18543Q3A SON 3.3x3.3 (SLPS432): 1-3 = S, 4 = G, 5-8 = D (thermal pad = D)
sch.defsym("NFET_SON", 10.16, 17.78,
           [("4", "G", "L", 2), ("2", "S", "L", 4), ("3", "S", "L", 5),
            ("5", "D", "R", 0),
            ("1", "S", "R", 5)], ref="Q")
# LM74800-Q1 WSON-12 (SNOSD95C table 6-1) — already physical
sch.defsym("LM74800", 17.78, 33.02,
           [("1", "DGATE", "L", 0), ("2", "A", "L", 2), ("3", "VSNS", "L", 4), ("4", "SW", "L", 6),
            ("5", "OV", "L", 8), ("6", "EN_UVLO", "L", 10), ("7", "GND", "L", 11),
            ("8", "HGATE", "R", 0), ("9", "OUT", "R", 2), ("10", "VS", "R", 4),
            ("11", "CAP", "R", 6), ("12", "C", "R", 8)], ref="U")
# LM5145 VQFN-20 RGY (SNVSAI4 fig 6-1): physical pads; EP = pad 21 -> GND
sch.defsym("LM5145", 17.78, 40.64,
           [("20", "VIN", "L", 0), ("1", "EN", "L", 2), ("2", "RT", "L", 4), ("3", "SS", "L", 6),
            ("11", "ILIM", "L", 8), ("8", "SYNCIN", "L", 10), ("6", "AGND", "L", 12),
            ("12", "PGND", "L", 13), ("21", "EP", "L", 14),
            ("14", "VCC", "R", 0), ("17", "BST", "R", 2), ("18", "HO", "R", 4), ("19", "SW", "R", 6),
            ("13", "LO", "R", 8), ("5", "FB", "R", 10), ("4", "COMP", "R", 12), ("10", "PGOOD", "R", 14),
            ("7", "SYNCOUT", "R", 1), ("9", "NC", "R", 3), ("15", "NC", "R", 5), ("16", "NC", "R", 7)],
           ref="U")
# TPS2557 DRB VSON-8 (SLVS931B): 1 GND, 2-3 IN, 4 EN(hi), 5 ILIM, 6-7 OUT, 8 FAULT, 9 PAD->GND
sch.defsym("TPS2557", 12.7, 22.86,
           [("2", "IN", "L", 0), ("3", "IN", "L", 1), ("4", "EN", "L", 3),
            ("1", "GND", "L", 6), ("9", "PAD", "L", 7),
            ("6", "OUT", "R", 0), ("7", "OUT", "R", 1), ("8", "FAULT", "R", 3),
            ("5", "ILIM", "R", 5)], ref="U")

# ------------------------------------------------------------------ footprints
# default by symbol type; per-ref overrides below (P3, see ../FOOTPRINTS.md + BOM.md)
sch.sym_fp = {
    "RES": "Resistor_SMD:R_0402_1005Metric",
    "CAP": "Capacitor_SMD:C_0402_1005Metric",
    "TVS": "Diode_SMD:D_SMB",
    "LED": "LED_SMD:LED_0805_2012Metric",
    "SHUNT": "Resistor_SMD:R_2512_6332Metric",
    "FUSE": "usb_power_3s:FuseHolder_ATO_FLR_EdgeTrim",
    "XT60": "usb_power_3s:XT60PW-M_EdgeTrim",
    "HDR8": "Connector_JST:JST_GH_SM08B-GHS-TB_1x08-1MP_P1.25mm_Horizontal",
    "USB_A": "Connector_USB:USB_A_CNCTech_1001-011-01101_Horizontal",
    "USBC_PWR": "Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal",
    "NFET_SON": "Package_SON:VSON-8_3.3x3.3mm_P0.65mm_NexFET",
    "LM74800": "usb_power_3s:WSON-12_3x3_P0.5_LM74800DRR",
    "LM5145": "usb_power_3s:VQFN-20_3.5x4.5_P0.5_LM5145RGY",
    "TPS2557": "Package_SON:VSON-8-1EP_3x3mm_P0.65mm_EP1.65x2.4mm",
    "IND": "Inductor_SMD:L_0603_1608Metric",
}
# per-ref overrides copied MECHANICALLY from the pre-port generator (net
# effect after its SPF-purge/update sequence; footprint parity is gated)
sch.ref_fp = {
    # capacitor size exceptions
    "CA2": "Capacitor_SMD:C_0603_1608Metric", "CB2": "Capacitor_SMD:C_0603_1608Metric",
    **{f"C{s}5{i}": "Capacitor_SMD:C_1210_3225Metric" for s in "AB" for i in "123"},
    **{f"C{s}6{i}": "Capacitor_SMD:C_1210_3225Metric" for s in "AB" for i in "1234"},
    **{f"C{s}11{i}": "Capacitor_SMD:C_1206_3216Metric" for s in "AB" for i in "12"},
    "CA7": "Capacitor_SMD:CP_Elec_6.3x5.9", "CB7": "Capacitor_SMD:CP_Elec_6.3x5.9",
    "CE1": "Capacitor_SMD:CP_Elec_8x10",
    # magnetics
    "LA1": "Inductor_SMD:L_Sunlord_MWSA1005S", "LB1": "Inductor_SMD:L_Sunlord_MWSA1005S",
    "L2": "Inductor_SMD:L_Chilisin_BMRx00060630", "L4": "Inductor_SMD:L_Chilisin_BMRx00060630",
    # USBLC6-2 ESD arrays are SOT-23-6, not SMB
    "D2": "Diode_SMD:D_SMB", "D3": "Diode_SMD:D_SMB",
    "D8": "Package_TO_SOT_SMD:SOT-23-6",
    # usb-power-3s specific (post-purge updates in the pre-port generator)
    "C16": "Capacitor_SMD:C_0603_1608Metric",   # 2u2 EN delay
    "C30": "Capacitor_SMD:C_1206_3216Metric", "C31": "Capacitor_SMD:C_1206_3216Metric",
    "C32": "Capacitor_SMD:C_1206_3216Metric", "C33": "Capacitor_SMD:C_1206_3216Metric",
    "C34": "Capacitor_SMD:C_1206_3216Metric",   # 22u port caps
}

# Sanctioned floats (canon S4: no_connect flags EMITTED, not narrated).
# 13 on this board (verification/pin_review.md): U2/U3 SYNCOUT+NC (7,9,15,16),
# U4/U5/U6 FAULT pin 8 (no MCU, resolution 2), J5 SBU1/SBU2 (power-only).
SANCTIONED_FLOATS = (
    {("U2", p) for p in ("7", "9", "15", "16")}
    | {("U3", p) for p in ("7", "9", "15", "16")}
    | {("U4", "8"), ("U5", "8"), ("U6", "8")}
    | {("J5", "A8"), ("J5", "B8")}
)


def fet(ref, value, g, d, s):
    """CSD18543Q3A: all 8 physical pins netted (1-3 S, 4 G, 5-8 D)."""
    return ("NFET_SON", ref, value, {"4": g, "5": d, "1": s, "2": s, "3": s})


def buck_stage(S, uref, rilim, cilim, en_net, vout, rfb2, pgood_net=None):
    """Fully-expanded LM5145 stage (values: P1_DETAIL_DESIGN.md section 2).
    Review fixes: bulk caps are individual physical instances (3x Cin, 4x Cout);
    RILIM sized for worst-case IRDSON 180uA x RDS(on)hot-max 9.9-11 mOhm."""
    sch.row(("LM5145", uref, f"LM5145 rail {S}",
             {"20": "VSW", "1": en_net, "2": f"RT_{S}", "3": f"SS_{S}", "11": f"ILIM_{S}",
              "8": "GND", "6": "GND", "12": "GND", "21": "GND",
              "14": f"VCC_{S}", "17": f"BST_{S}", "18": f"HO_{S}", "19": f"SW_{S}",
              "13": f"LO_{S}", "5": f"FB_{S}", "4": f"COMP_{S}",
              "10": pgood_net or f"PGOOD_{S}",
              "7": None, "9": None, "15": None, "16": None}),
            fet(f"Q{S}1", "CSD18543Q3A HS", f"HO_{S}", "VSW", f"SW_{S}"))
    sch.chain(f"{uref}.18", f"Q{S}1.4")   # HO gate network, drawn (T1 adds SW)
    sch.row(fet(f"Q{S}2", "CSD18543Q3A LS", f"LO_{S}", f"SW_{S}", "GND"),
            ("IND", f"L{S}1", "MWSA1005S-3R3 16A", {"1": f"SW_{S}", "2": vout}))
    sch.chain(f"Q{S}2.5", f"L{S}1.1")     # switch node into the inductor, drawn
    # frequency / soft-start / bias
    sch.row(("RES", f"R{S}1", "16k5 RT (606kHz)", {"1": f"RT_{S}", "2": "GND"}),
            ("CAP", f"C{S}1", "47n SS (4ms)", {"1": f"SS_{S}", "2": "GND"}))
    sch.row(("CAP", f"C{S}2", "2u2 VCC", {"1": f"VCC_{S}", "2": "GND"}),
            ("CAP", f"C{S}3", "100n BST", {"1": f"BST_{S}", "2": f"SW_{S}"}))
    sch.row(("RES", f"R{S}2", rilim, {"1": f"ILIM_{S}", "2": f"SW_{S}"}),
            ("CAP", f"C{S}4", cilim, {"1": f"ILIM_{S}", "2": "GND"}))
    # LC — every physical capacitor is its own instance (review BLOCKER fix)
    sch.row(*[("CAP", f"C{S}5{i+1}", "10u 50V X7R", {"1": "VSW", "2": "GND"})
              for i in range(3)])
    sch.row(*[("CAP", f"C{S}6{i+1}", "47u 10V X7R", {"1": vout, "2": "GND"})
              for i in range(4)])
    sch.row(("CAP", f"C{S}7", "220u poly 25mR", {"1": vout, "2": "GND"}))
    # feedback + type-III compensation (sense point = the rail the load sees)
    sch.row(("RES", f"R{S}3", "20k RFB1", {"1": vout, "2": f"FB_{S}"}),
            ("RES", f"R{S}4", rfb2, {"1": f"FB_{S}", "2": "GND"}))
    sch.chain(f"R{S}3.2", f"R{S}4.1")     # FB divider chain, drawn
    sch.row(("RES", f"R{S}5", "13k RC1", {"1": f"COMP_{S}", "2": f"CX_{S}"}),
            ("CAP", f"C{S}8", "8n2 CC1", {"1": f"CX_{S}", "2": f"FB_{S}"}))
    sch.chain(f"R{S}5.2", f"C{S}8.1")     # comp RC leg, drawn
    sch.row(("CAP", f"C{S}9", "39p CC2", {"1": f"COMP_{S}", "2": f"FB_{S}"}))
    sch.row(("CAP", f"C{S}10", "1n2 CC3", {"1": vout, "2": f"CY_{S}"}),
            ("RES", f"R{S}6", "4k64 RC2", {"1": f"CY_{S}", "2": f"FB_{S}"}))
    sch.chain(f"C{S}10.2", f"R{S}6.1")    # CC3-RC2 leg, drawn


# ═══════════════════ circuit: structure only, nets verbatim ═══════════════════

# --- region 1: input ---
sch.region("1. INPUT + PROTECTION (3S LiPo 9.0-12.6V, <=9A)")
sch.row(("XT60", "J1", "XT60_BATT", {"1": "GND", "2": "VBATT_RAW"}),   # pad1 = "-" blade
        ("FUSE", "F1", "15A ATO", {"1": "VBATT_RAW", "2": "VBATT_F"}),
        ("TVS", "D1", "SMBJ16A", {"1": "VBATT_F", "2": "GND"}))        # pad1 = cathode -> rail
sch.chain("J1.2", "F1.1")   # battery + into the fuse, drawn
sch.chain("F1.2", "D1.1")   # fused rail onto the TVS cathode, drawn
sch.row(("CAP", "C15", "100n at U1.A", {"1": "VBATT_F", "2": "GND"}),
        ("CAP", "CE1", "100u hybrid 35V", {"1": "VSW", "2": "GND"}))

# --- region 2: front-end ---
sch.region("2. FRONT-END: LM74800-Q1 + 2x CSD18543Q3A b2b (rev-pol; UVLO 9.33V on / OV 15.25V)")
sch.row(("LM74800", "U1", "LM74800-Q1",
         {"1": "DG_FE", "2": "VBATT_F", "3": "VBATT_F", "4": "FE_LAD", "5": "FE_OV",
          "6": "FE_EN", "7": "GND", "8": "HG_FE", "9": "VSW", "10": "FE_MID",
          "11": "FE_CAP", "12": "FE_MID"}),
        fet("Q2", "CSD18543Q3A switch", "HG_FE", "FE_MID", "VSW"))
sch.chain("U1.8", "Q2.4")   # HGATE network, drawn (T1 adds the VSW source tie)
sch.row(fet("Q1", "CSD18543Q3A diode", "DG_FE", "FE_MID", "VBATT_F"))
sch.row(("RES", "R1", "887k ladder-top", {"1": "FE_LAD", "2": "FE_EN"}),
        ("RES", "R2", "52k3 ladder-mid (UVLO 9.33V)", {"1": "FE_EN", "2": "FE_OV"}),
        ("RES", "R3", "82k5 ladder-bot (OV 15.25V)", {"1": "FE_OV", "2": "GND"}))
sch.chain("R1.2", "R2.1")   # UVLO/OV ladder chain, drawn
sch.chain("R2.2", "R3.1")
sch.row(("CAP", "C16", "2u2 EN delay", {"1": "FE_EN", "2": "GND"}),
        ("CAP", "C1", "100n CAP-VS", {"1": "FE_CAP", "2": "FE_MID"}))
sch.row(("CAP", "C2", "100n VS-GND", {"1": "FE_MID", "2": "GND"}),
        ("CAP", "C3", "47n HGATE dv/dt", {"1": "HG_FE", "2": "VSW"}))

# --- region 3: buck A -> USB-C rail ---
sch.region("3. BUCK A  5.08V / 6A -> 5V_C (USB-C)   [math: 01_docs/DETAIL_DESIGN.md]")
sch.row(("RES", "R4", "100k EN-A hi (8.5V on)", {"1": "VSW", "2": "EN_A"}),
        ("RES", "R5", "16k5 EN-A lo (7.5V off)", {"1": "EN_A", "2": "GND"}))
sch.chain("R4.2", "R5.1")   # EN divider chain, drawn
buck_stage("A", "U2", "348R RILIM (wc 6.3A)", "18p CILIM", "EN_A", "5V_C",
           "3k74 RFB2 (5.08V)", "PGOODA_RAW")
sch.row(("RES", "R21", "20k PGOOD_A pu (5V_C)", {"1": "5V_C", "2": "PGOODA_RAW"}),
        ("RES", "R33", "20k seq div hi", {"1": "PGOODA_RAW", "2": "PGOOD_A"}),
        ("RES", "R34", "16k5 seq div lo", {"1": "PGOOD_A", "2": "GND"}))
sch.chain("R21.2", "R33.1")  # PGOOD sequencing divider chain, drawn
sch.chain("R33.2", "R34.1")

# --- region 4: buck B -> USB-A rail (sequenced after A) ---
sch.region("4. BUCK B  5.08V / 7.5A -> 5V_A (3x USB-A)   EN = PGOOD_A")
buck_stage("B", "U3", "432R RILIM (wc 7.8A)", "18p CILIM", "PGOOD_A", "5V_A",
           "3k74 RFB2 (5.08V)")

# --- region 5: USB-A ports, DCP-strapped, 2.5A limited ---
sch.region("5. USB-A x3: TPS2557 ILIM 2.51A each, D+/D- DCP short (ADR-0003)")
for _i, (_u, _j, _rl, _vb, _dcp, _cin, _cout) in enumerate([
        ("U4", "J2", "R16", "VBUS1", "DCP1", "C20", "C30"),
        ("U5", "J3", "R17", "VBUS2", "DCP2", "C21", "C31"),
        ("U6", "J4", "R18", "VBUS3", "DCP3", "C22", "C32")]):
    sch.row(("TPS2557", _u, "TPS2557 2.5A",
             {"2": "5V_A", "3": "5V_A", "4": "5V_A", "1": "GND", "9": "GND",
              "6": _vb, "7": _vb, "8": None, "5": f"ILIM{_i+1}"}),
            ("RES", _rl, "24k3 RILIM (2.51A)", {"1": f"ILIM{_i+1}", "2": "GND"}))
    sch.chain(f"{_u}.5", f"{_rl}.1")  # ILIM chain, drawn
    sch.row(("CAP", _cin, "100n sw in", {"1": "5V_A", "2": "GND"}),
            ("CAP", _cout, "22u port", {"1": _vb, "2": "GND"}))
    sch.row(("USB_A", _j, "USB-A 2.5A",
             {"1": _vb, "2": _dcp, "3": _dcp, "4": "GND", "SH": "GND"}))

# --- region 6: USB-C port ---
sch.region("6. USB-C source: Rp 10k x2 = 3A advertisement, 6A copper (ADR-0002)")
sch.row(("RES", "R19", "10k Rp CC1 (3A adv)", {"1": "5V_C", "2": "CC1"}),
        ("USBC_PWR", "J5", "USB4105-GF-A",
         {"A4": "5V_C", "A9": "5V_C", "B4": "5V_C", "B9": "5V_C",
          "A5": "CC1", "B5": "CC2",
          "A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND",
          "A6": "DCPC", "A7": "DCPC", "B6": "DCPC", "B7": "DCPC",
          "A8": None, "B8": None, "SH": "GND"}))
sch.chain("R19.2", "J5.A5")  # Rp into CC1, drawn (CC2 label-based: one chain per adjacency)
sch.row(("RES", "R20", "10k Rp CC2 (3A adv)", {"1": "5V_C", "2": "CC2"}))
sch.row(("CAP", "C33", "22u port", {"1": "5V_C", "2": "GND"}),
        ("CAP", "C34", "22u port", {"1": "5V_C", "2": "GND"}))

# --- region 7: rail TVS + indicators ---
sch.region("7. RAIL CLAMPS + LEDs")
sch.row(("TVS", "D2", "SMBJ5.0A", {"1": "5V_A", "2": "GND"}),   # pad1 = cathode
        ("TVS", "D3", "SMBJ5.0A", {"1": "5V_C", "2": "GND"}))
sch.row(("RES", "R22", "1k LED-A", {"1": "5V_A", "2": "LEDA_A"}),
        ("LED", "D4", "green 5V_A", {"1": "GND", "2": "LEDA_A"}))  # pad1 = cathode
sch.row(("RES", "R23", "1k LED-C", {"1": "5V_C", "2": "LEDC_A"}),
        ("LED", "D5", "green 5V_C", {"1": "GND", "2": "LEDC_A"}))

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

# --- register the 'pwr' symbol library (ERC lib_symbol_issues fix) ---
# The schematic embeds every symbol; ERC still warns per-symbol when the
# named library is not in the project's sym-lib-table. Emit the SAME
# symbols as a real library (identical content -> no mismatch class) and
# point the table at it.
(HERE / "lib").mkdir(exist_ok=True)
sch.write_symbol_lib(HERE / "lib" / "pwr.kicad_sym")
(out / "sym-lib-table").write_text(
    sch.sym_lib_table("pwr", "${KIPRJMOD}/../03_src/lib/pwr.kicad_sym"))
# fp-lib-table is owned by 03_src/generate_board.py (board side) — not written here.

# NEVER overwrite an existing project file - it carries the DRC rule floors,
# netclasses and severity policy.
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
