"""Generate 04_kicad/cook_loadcell.kicad_sch — schwriter2 (structure only).

Spec PCB C (§3.7): HX711 + bridge-combination network. Pin numbers are
PHYSICAL PADS from 02_parts/<MPN>/part.yaml: HX711 SOP-16 (DS pin table,
re-verified in pin review + twin), S8550 SOT-23 (1=B 2=E 3=C), PESD
SOD-323 pad1=cathode, JST XH positional. Circuit per 01_docs/
ARCHITECTURE.md + DETAIL_DESIGN.md, decisions D1-D8 (01_docs/BRIEF.md).

Bridge (D1): ring splices RING_12..RING_41 join neighbouring sensors'
outer gauges; RED taps = E_PLUS (J1), S_PLUS (J2), E_MINUS (J3),
S_MINUS (J4); J5 full-bridge lands on the same four nodes.
Run: python3 03_src/generate_schematic.py"""

import sys
from pathlib import Path

HERE = Path(__file__).parent
for p in (HERE.parents[2] / "skills" / "kicad-pcb" / "scripts",
          Path.home() / ".claude" / "skills" / "kicad-pcb" / "scripts"):
    if p.is_dir():
        sys.path.insert(0, str(p))
        break
from schwriter2 import Schematic  # noqa: E402

PROJECT = "cook_loadcell"
SMALL = {"RES", "CAP", "TP", "DSOD", "SJ", "HDR3"}

rev = Schematic.rev_from_git(HERE, "LC_REV", "lc-v*").replace("lc-", "")
sch = Schematic(
    PROJECT, "cook-loadcell", paper="A3",
    comment="SMC0985KS Phase-1 load-cell daughterboard: 4x 50kg half-bridge ring (or 1x full bridge) + HX711; smc0985-cook commission",
    rev=rev, small_syms=SMALL, libname="cooklc")
sch.no_bom_syms = {"TP"}

sch.defsym("RES", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="R")
sch.defsym("CAP", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="C")
sch.defsym("TP", 5.08, 5.08, [("1", "1", "L", 0)], ref="TP")
sch.defsym("DSOD", 7.62, 5.08, [("1", "K", "L", 0), ("2", "A", "R", 0)], ref="D")
sch.defsym("SJ", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="SJ")
sch.defsym("HDR3", 7.62, 10.16,
           [("1", "1", "L", 0), ("2", "2", "L", 1), ("3", "3", "L", 2)], ref="JP")
sch.defsym("PNP", 10.16, 10.16,
           [("1", "B", "L", 1), ("2", "E", "R", 0), ("3", "C", "R", 2)], ref="Q")
for n in (3, 5):
    sch.defsym(f"XH{n}", 10.16, 2.54 * (n + 1),
               [(str(k), str(k), "R", k - 1) for k in range(1, n + 1)], ref="J")
sch.defsym("HX711", 20.32, 25.4,
           [("8", "INA+", "L", 0), ("7", "INA-", "L", 1), ("10", "INB+", "L", 2),
            ("9", "INB-", "L", 3), ("3", "AVDD", "L", 5), ("4", "VFB", "L", 6),
            ("2", "BASE", "L", 7), ("5", "AGND", "L", 8),
            ("1", "VSUP", "R", 0), ("16", "DVDD", "R", 1), ("12", "DOUT", "R", 3),
            ("11", "PD_SCK", "R", 4), ("15", "RATE", "R", 5), ("14", "XI", "R", 6),
            ("13", "XO", "R", 7), ("6", "VBG", "R", 8)], ref="U")

sch.sym_fp = {
    "RES": "Resistor_SMD:R_0603_1608Metric",
    "CAP": "Capacitor_SMD:C_0603_1608Metric",
    "TP": "TestPoint:TestPoint_Pad_D1.5mm",
    "DSOD": "Diode_SMD:D_SOD-323",
    "SJ": "Jumper:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm",
    "HDR3": "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
    "PNP": "Package_TO_SOT_SMD:SOT-23",
    "XH3": "Connector_JST:JST_XH_B3B-XH-A_1x03_P2.50mm_Vertical",
    "XH5": "Connector_JST:JST_XH_B5B-XH-A_1x05_P2.50mm_Vertical",
    "HX711": "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
}
sch.ref_fp = {"C1": "Capacitor_SMD:C_0805_2012Metric",
              "C4": "Capacitor_SMD:C_0805_2012Metric",
              "C6": "Capacitor_SMD:C_0805_2012Metric"}

# --- 1: sensors + bridge ring ---
sch.region("1. LOAD SENSORS: 4x 3-wire half-bridge ring OR J5 full bridge (mode = population)   [D1, spec 3.7b]")
sch.row(("XH3", "J1", "SENSOR 1 B/R/W", {"1": "RING_41", "2": "E_PLUS", "3": "RING_12"}),
        ("XH3", "J2", "SENSOR 2 B/R/W", {"1": "RING_12", "2": "S_PLUS", "3": "RING_23"}))
sch.row(("XH3", "J3", "SENSOR 3 B/R/W", {"1": "RING_23", "2": "E_MINUS", "3": "RING_34"}),
        ("XH3", "J4", "SENSOR 4 B/R/W", {"1": "RING_34", "2": "S_MINUS", "3": "RING_41"}))
sch.row(("XH5", "J5", "FULL BRIDGE ALT",
         {"1": "E_PLUS", "2": "S_PLUS", "3": "S_MINUS", "4": "E_MINUS", "5": "SH"}))
sch.row(("RES", "R7", "100R shield bond", {"1": "SH", "2": "GND"}),
        ("CAP", "C7", "100n shield bond", {"1": "SH", "2": "GND"}),
        ("SJ", "SJ1", "SH hard bond DNP", {"1": "SH", "2": "GND"}))

# --- 2: excitation regulator ---
sch.region("2. EXCITATION: HX711 analog regulator + S8550 -> E+ = AVDD 4.30V   [D2, HX711 DS typ. circuit]")
sch.row(("PNP", "Q1", "S8550", {"1": "BASE", "2": "5V", "3": "E_PLUS"}),
        ("RES", "R1", "20k 1% AVDD-VFB", {"1": "E_PLUS", "2": "AVDD_FB"}),
        ("RES", "R2", "8.2k 1% VFB-GND", {"1": "AVDD_FB", "2": "GND"}))
sch.chain("Q1.3", "R1.1")
sch.chain("R1.2", "R2.1")
sch.row(("CAP", "C1", "10u E+", {"1": "E_PLUS", "2": "GND"}),
        ("CAP", "C2", "100n E+", {"1": "E_PLUS", "2": "GND"}),
        ("TP", "TP1", "TP E+", {"1": "E_PLUS"}),
        ("TP", "TP2", "TP S+", {"1": "S_PLUS"}),
        ("TP", "TP3", "TP S-", {"1": "S_MINUS"}),
        ("TP", "TP4", "TP GND", {"1": "GND"}))

# --- 3: HX711 ---
sch.region("3. HX711 24-BIT BRIDGE ADC: ch A gain 128; XI=GND internal osc; RATE by JP1   [D3, spec 3.7d]")
sch.row(("HX711", "U1", "HX711",
         {"8": "S_PLUS", "7": "S_MINUS", "10": "GND", "9": "GND",
          "3": "E_PLUS", "4": "AVDD_FB", "2": "BASE", "5": "GND",
          "1": "5V", "16": "3V3", "12": "DAT", "11": "CLK",
          "15": "RATE_SEL", "14": "GND", "13": None, "6": None}),
        ("HDR3", "JP1", "RATE 1-2=10SPS 2-3=80",
         {"1": "GND", "2": "RATE_SEL", "3": "3V3"}))
sch.row(("CAP", "C3", "100n DVDD", {"1": "3V3", "2": "GND"}),
        ("CAP", "C4", "10u 3V3", {"1": "3V3", "2": "GND"}),
        ("CAP", "C5", "100n VSUP", {"1": "5V", "2": "GND"}),
        ("CAP", "C6", "10u 5V", {"1": "5V", "2": "GND"}))

# --- 4: digital link ---
sch.region("4. DIGITAL LINK TO COOK-HUB J6 (pin-for-pin): 5V 3V3 GND DAT CLK   [D6/D7]")
sch.row(("XH5", "J6", "TO HUB J6",
         {"1": "5V", "2": "3V3", "3": "GND", "4": "DAT", "5": "CLK"}),
        ("DSOD", "D1", "PESD5V0S1BA", {"1": "DAT", "2": "GND"}),
        ("DSOD", "D2", "PESD5V0S1BA", {"1": "CLK", "2": "GND"}))
sch.row(("TP", "TP5", "TP DAT", {"1": "DAT"}),
        ("TP", "TP6", "TP CLK", {"1": "CLK"}),
        ("TP", "TP7", "TP 3V3", {"1": "3V3"}))

content = sch.emit()
out = HERE.parent / "04_kicad"
out.mkdir(exist_ok=True)
(out / f"{PROJECT}.kicad_sch").write_text(content)
(HERE / "lib").mkdir(exist_ok=True)
sch.write_symbol_lib(HERE / "lib" / "cooklc.kicad_sym")
(out / "sym-lib-table").write_text(
    sch.sym_lib_table("cooklc", "${KIPRJMOD}/../03_src/lib/cooklc.kicad_sym"))
(out / "fp-lib-table").write_text(sch.fp_lib_table())
if not (out / f"{PROJECT}.kicad_pro").exists():
    (out / f"{PROJECT}.kicad_pro").write_text(
        '{\n  "board": { "design_settings": {} },\n'
        f'  "meta": {{ "filename": "{PROJECT}.kicad_pro", "version": 1 }},\n'
        '  "schematic": { "legacy_lib_dir": "", "legacy_lib_list": [] }\n}\n')
print(f"wrote {PROJECT}.kicad_sch: {len(sch.cells)} cells, {len(sch.wires)} wires, S-OCCL 0")
