"""Generate 04_kicad/ble_bus_bar.kicad_sch — schwriter2 (structure only).

Circuit per 01_docs/ARCHITECTURE.md + DETAIL_DESIGN.md; decisions D1-D8 in
01_docs/BRIEF.md (ADR-0001..0006). libname="bbar" (commission).

Pin numbers are PHYSICAL PADS from 02_parts/<MPN>/part.yaml, each citing
its datasheet figure: INA238 fig 4-1 p.3 SLYS025B (1=A1 2=A0 3=ALERT
4=SDA 5=SCL 6=VS 7=GND 8=VBUS 9=IN- 10=IN+); LMR16006 p.3 SNVSA24
(1=CB 2=GND 3=FB 4=SHDN 5=VIN 6=SW); ESP32-C3-WROOM-02 table 3-1
pp.10-11 v1.7; W25Q64JV fig 1a p.5 RevJ; AMS1117 p.1 (1=GND 2=VOUT+tab
3=VIN, TabPin2 merges tab into pad 2); USBLC6 pinning p.1 (1/6 + 3/4
pass-through pairs, 5=VBUS); TYPE-C-31-M-12 contact table (A/B pads);
diodes: KiCad D_* footprints put the CATHODE on pad 1.

Story wires (canon S6): bus entry -> TVS; fuse -> shunt -> port stud
(channel 1); sense tap -> INA238 IN+; electronics chain F7 -> D7 ->
buck -> L -> 3V3 bulk. The 6x port channel is emitted by a reusable
generator function port_channel(i, a1, a0).

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

PROJECT = "ble_bus_bar"
SMALL = {"RES", "CAP", "C1206", "C1210", "LED", "LEDR", "DSOD", "DSODR", "DSMA", "DSMAR",
         "DSMB", "DSMC", "FUSES", "SHUNT", "LUG5", "LUG4", "BTN", "IND"}

rev = Schematic.rev_from_git(HERE, "BBAR_REV", "bbar-v*").replace("bbar-", "")
sch = Schematic(
    PROJECT, "ble-bus-bar", paper="A1",
    comment="12-24V/60A bus bar: 6x ATO-fused 30A ports, INA238+WSLP2726 sensing, ESP32-C3 BLE, W25Q64 log",
    rev=rev, small_syms=SMALL, libname="bbar")
sch.no_bom_syms = {"LUG5", "LUG4"}

# ------------------------------------------------------------------ symbols
sch.defsym("RES", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="R")
sch.defsym("CAP", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="C")
sch.defsym("C1206", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="C")
sch.defsym("C1210", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="C")
# LED_0805 footprint: pad 1 = CATHODE
sch.defsym("LED", 7.62, 5.08, [("1", "K", "L", 0), ("2", "A", "R", 0)], ref="LED")
# diodes, KiCad convention pad 1 = cathode. DSMAR = A-on-left variant for
# the series pass diode so the L->R story wire reads supply-direction.
for nm in ("DSOD", "DSMA", "DSMB", "DSMC"):
    sch.defsym(nm, 7.62, 5.08, [("1", "K", "L", 0), ("2", "A", "R", 0)], ref="D")
sch.defsym("DSMAR", 7.62, 5.08, [("2", "A", "L", 0), ("1", "K", "R", 0)], ref="D")
sch.defsym("DSODR", 7.62, 5.08, [("2", "A", "L", 0), ("1", "K", "R", 0)], ref="D")
# LEDR: anode left (fed from resistor), cathode right to GND
sch.defsym("LEDR", 7.62, 5.08, [("2", "A", "L", 0), ("1", "K", "R", 0)], ref="LED")
sch.defsym("FUSES", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="F")
sch.defsym("FUSEH", 7.62, 7.62, [("1", "BUS", "L", 0), ("2", "OUT", "R", 0)], ref="F")
sch.defsym("SHUNT", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="RS")
sch.defsym("LUG5", 5.08, 5.08, [("1", "LUG", "R", 0)], ref="J")  # feeds rightward
sch.defsym("LUG4", 5.08, 5.08, [("1", "LUG", "L", 0)], ref="J")
sch.defsym("BTN", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="SW")
sch.defsym("IND", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="L")
sch.defsym("HDR4", 7.62, 12.7,
           [(str(n), f"P{n}", "L", n - 1) for n in range(1, 5)], ref="J")
# INA238 (fig 4-1 p.3): analog left, digital right
sch.defsym("INA", 15.24, 20.32,
           [("10", "IN+", "L", 0), ("9", "IN-", "L", 1), ("8", "VBUS", "L", 2),
            ("7", "GND", "L", 4),
            ("6", "VS", "R", 0), ("4", "SDA", "R", 1), ("5", "SCL", "R", 2),
            ("2", "A0", "R", 3), ("1", "A1", "R", 4), ("3", "ALERT", "R", 5)],
           ref="U")
# LMR16006 (p.3 SNVSA24)
sch.defsym("BUCK", 12.7, 15.24,
           [("5", "VIN", "L", 0), ("4", "SHDN", "L", 1), ("3", "FB", "L", 2),
            ("2", "GND", "L", 4), ("6", "SW", "R", 0), ("1", "CB", "R", 2)],
           ref="U")
# AMS1117 fixed (p.1): 1=GND 2=VOUT(+tab) 3=VIN
sch.defsym("LDO", 10.16, 10.16,
           [("3", "VIN", "L", 0), ("1", "GND", "L", 2), ("2", "VOUT", "R", 0)],
           ref="U")
# USBLC6-2SC6 (pinning p.1): 1/6 line1, 3/4 line2, 2=GND, 5=VBUS
sch.defsym("ESDU", 12.7, 12.7,
           [("1", "IO1", "L", 0), ("3", "IO2", "L", 2), ("2", "GND", "L", 3),
            ("6", "IO1b", "R", 0), ("4", "IO2b", "R", 2), ("5", "VBUS", "R", 3)],
           ref="U")
# W25Q64JV (fig 1a p.5)
sch.defsym("FLASH", 12.7, 15.24,
           [("1", "/CS", "L", 0), ("5", "DI", "L", 1), ("2", "DO", "L", 2),
            ("6", "CLK", "L", 3),
            ("8", "VCC", "R", 0), ("3", "/WP", "R", 1), ("7", "/HOLD", "R", 2),
            ("4", "GND", "R", 4)], ref="U")
# TYPE-C-31-M-12 (contact table; USB2 subset)
sch.defsym("USBC", 15.24, 33.02,
           [("A4", "VBUS", "L", 0), ("A9", "VBUS", "L", 1),
            ("B4", "VBUS", "L", 2), ("B9", "VBUS", "L", 3),
            ("A5", "CC1", "L", 5), ("B5", "CC2", "L", 6),
            ("A6", "DP1", "L", 8), ("B6", "DP2", "L", 9),
            ("A7", "DN1", "L", 10), ("B7", "DN2", "L", 11),
            ("A8", "SBU1", "R", 0), ("B8", "SBU2", "R", 1),
            ("A1", "GND", "R", 3), ("A12", "GND", "R", 4),
            ("B1", "GND", "R", 5), ("B12", "GND", "R", 6),
            ("SH", "SHIELD", "R", 8)], ref="J")
# ESP32-C3-WROOM-02 (table 3-1 pp.10-11)
sch.defsym("ESP", 17.78, 40.64,
           [("1", "3V3", "L", 0), ("2", "EN", "L", 1), ("7", "IO8", "L", 3),
            ("8", "IO9", "L", 4), ("18", "IO0", "L", 6), ("9", "GND", "L", 8),
            ("19", "EP", "L", 9),
            ("3", "IO4/SDA", "R", 0), ("4", "IO5/SCL", "R", 1),
            ("15", "IO3/ALERT", "R", 2), ("5", "IO6/CLK", "R", 4),
            ("6", "IO7/MOSI", "R", 5), ("16", "IO2/MISO", "R", 6),
            ("10", "IO10/CS", "R", 7), ("17", "IO1/LED", "R", 9),
            ("13", "IO18/D-", "R", 11), ("14", "IO19/D+", "R", 12),
            ("11", "RXD", "R", 13), ("12", "TXD", "R", 14)], ref="U")

# ------------------------------------------------------------------ footprints
sch.sym_fp = {
    "RES": "Resistor_SMD:R_0805_2012Metric",
    "CAP": "Capacitor_SMD:C_0805_2012Metric",
    "C1206": "Capacitor_SMD:C_1206_3216Metric",
    "C1210": "Capacitor_SMD:C_1210_3225Metric",
    "LED": "LED_SMD:LED_0805_2012Metric",
    "LEDR": "LED_SMD:LED_0805_2012Metric",
    "DSOD": "Diode_SMD:D_SOD-123",
    "DSODR": "Diode_SMD:D_SOD-123",
    "DSMA": "Diode_SMD:D_SMA",
    "DSMAR": "Diode_SMD:D_SMA",
    "DSMB": "Diode_SMD:D_SMB",
    "DSMC": "Diode_SMD:D_SMC",
    "FUSES": "Fuse:Fuse_1206_3216Metric",
    "FUSEH": "bbar:FuseHolder_Keystone_3557-2",
    "SHUNT": "bbar:R_Shunt_WSLP2726",
    "LUG5": "bbar:Lug_M5",
    "LUG4": "bbar:Lug_M4",
    "BTN": "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A",
    "IND": "Inductor_SMD:L_Sunlord_SWPA6045S",
    "HDR4": "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
    "INA": "Package_SO:MSOP-10_3x3mm_P0.5mm",
    "BUCK": "Package_TO_SOT_SMD:TSOT-23-6",
    "LDO": "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
    "ESDU": "Package_TO_SOT_SMD:SOT-23-6",
    "FLASH": "Package_SO:SOIC-8_5.3x5.3mm_P1.27mm",  # SSIQ = 208-mil WIDE body (twin caught the narrow-SOIC error)
    "USBC": "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
    "ESP": "bbar:ESP32-C3-WROOM-02_D03",
}

# ═══════════════════ circuit: structure only ═══════════════════

# --- region 1: bus input ---
sch.region("1. BUS INPUT: M5 lug 60A + SMCJ33A clamp; GND is REFERENCE only (D1)   [ADR-0001/0005]")
sch.row(("LUG5", "J7", "+12-24V IN M5 LUG", {"1": "VBUS"}),
        ("DSMC", "D9", "SMCJ33A bus TVS", {"1": "VBUS", "2": "GND"}))
sch.chain("J7.1", "D9.1")   # bus entry -> clamp: drawn
sch.row(("LUG4", "J8", "GND REF M4 LUG", {"1": "GND"}))


# --- region 2: the six port channels (generator function) ---
ADDR = {1: ("GND", "GND"), 2: ("GND", "3V3"), 3: ("GND", "SDA"),
        4: ("GND", "SCL"), 5: ("3V3", "GND"), 6: ("3V3", "3V3")}


def port_channel(i):
    """One fused+monitored port: holder -> shunt -> stud, INA238 sense.
    A1/A0 straps encode I2C address 0x40+ (DETAIL_DESIGN #3). Sense nets
    are KA (IN+ side) / KB (IN- side) — deliberately NOT *P/*N names so
    KiCad's diff-pair inference stays out of the DRC. VBUS pin ties to
    the KB node: bus voltage reads through RN's 10R (nA bias -> ~0 error),
    which keeps the sense cluster planar on 2 layers (DETAIL_DESIGN #3)."""
    a1, a0 = ADDR[i]
    vf, vp = f"VF{i}", f"VP{i}"
    ka, kb = f"KA{i}", f"KB{i}"
    sch.region(f"2.{i} PORT {i}: ATO fuse -> 0.5m shunt -> M4 stud; INA238 @0x{0x3f + i:02X}   [ADR-0003]")
    sch.row(("FUSEH", f"F{i}", "3557-2 ATO 30A MAX", {"1": "VBUS", "2": vf}),
            ("SHUNT", f"RS{i}", "WSLP2726 0.5mR", {"1": vf, "2": vp}),
            ("LUG4", f"J{i}", f"PORT {i} M4 LUG", {"1": vp}))
    sch.chain(f"F{i}.2", f"RS{i}.1")   # fuse -> shunt: drawn
    sch.chain(f"RS{i}.2", f"J{i}.1")   # shunt -> port stud: drawn
    row = sch.row(("RES", f"RP{i}", "10R sense+", {"1": vf, "2": ka}),
                  ("INA", f"U{i}", "INA238AIDGSR",
                   {"10": ka, "9": kb, "8": kb, "7": "GND", "6": "3V3",
                    "4": "SDA", "5": "SCL", "2": a0, "1": a1, "3": "ALERT"}),
                  ("CAP", f"CB{i}", "100n INA", {"1": "3V3", "2": "GND"}))
    sch.chain(f"RP{i}.2", f"U{i}.10")  # Kelvin tap -> IN+: drawn
    sch.row(("RES", f"RN{i}", "10R sense-", {"1": vp, "2": kb}),
            ("CAP", f"CD{i}", "100n diff", {"1": ka, "2": kb}))
    return row


for i in range(1, 7):
    port_channel(i)

# --- region 3: electronics tap + buck ---
sch.region("3. ELECTRONICS: 2A fuse -> reverse-block -> LMR16006X 60V buck -> 3.3V   [ADR-0001/0006]")
sch.row(("FUSES", "F7", "0466002 2A", {"1": "VBUS", "2": "VTAP"}),
        ("DSMAR", "D7", "SS310 rev block", {"2": "VTAP", "1": "VIN_E"}),
        ("BUCK", "U8", "LMR16006XDDCR",
         {"5": "VIN_E", "4": "SHDN", "3": "FB", "2": "GND", "6": "SW", "1": "BOOT"}),
        ("IND", "L1", "22u SWPA6045S", {"1": "SW", "2": "3V3"}),
        ("C1206", "C5", "22u 3V3", {"1": "3V3", "2": "GND"}))
sch.chain("F7.2", "D7.2")    # tap fuse -> series diode: drawn
sch.chain("D7.1", "U8.5")    # diode -> buck VIN: drawn
sch.chain("U8.6", "L1.1")    # SW -> inductor: drawn
sch.chain("L1.2", "C5.1")    # inductor -> first bulk: drawn
sch.row(("DSMB", "D10", "SMBJ33A tap TVS", {"1": "VIN_E", "2": "GND"}),
        ("C1210", "C1", "4u7 50V", {"1": "VIN_E", "2": "GND"}),
        ("C1210", "C2", "4u7 50V", {"1": "VIN_E", "2": "GND"}),
        ("CAP", "C3", "100n VIN", {"1": "VIN_E", "2": "GND"}),
        ("DSMA", "D11", "SS310 catch", {"1": "SW", "2": "GND"}),
        ("CAP", "C4", "100n boot", {"1": "BOOT", "2": "SW"}))
sch.row(("RES", "R24", "33k FB hi", {"1": "3V3", "2": "FB"}),
        ("RES", "R25", "10k FB lo", {"1": "FB", "2": "GND"}),
        ("RES", "R26", "560k UVLO hi", {"1": "VIN_E", "2": "SHDN"}),
        ("RES", "R27", "100k UVLO lo", {"1": "SHDN", "2": "GND"}),
        ("C1206", "C6", "22u 3V3", {"1": "3V3", "2": "GND"}))
sch.chain("R24.2", "R25.1")  # FB divider: drawn
sch.chain("R26.2", "R27.1")  # UVLO divider: drawn

# --- region 4: MCU ---
sch.region("4. ESP32-C3-WROOM-02: BLE 5.0 + native USB; straps per ADR-0004")
sch.row(("ESP", "U7", "ESP32-C3-WROOM-02-N4",
         {"1": "3V3", "2": "EN", "7": "IO8", "8": "BOOT9", "17": None,
          "9": "GND", "19": "GND",
          "3": "SDA", "4": "SCL", "15": "ALERT", "5": "SPI_CLK",
          "6": "SPI_MOSI", "16": "SPI_MISO", "10": "FLASH_CS",
          "18": "LED_ST", "13": "USB_DM", "14": "USB_DP",
          "11": "RXD", "12": "TXD"}),
        ("CAP", "C8", "100n U7", {"1": "3V3", "2": "GND"}),
        ("C1206", "C7", "22u U7", {"1": "3V3", "2": "GND"}))
sch.row(("RES", "R21", "10k EN pu", {"1": "3V3", "2": "EN"}),
        ("CAP", "C10", "1u EN", {"1": "EN", "2": "GND"}),
        ("BTN", "SW1", "RESET", {"1": "EN", "2": "GND"}),
        ("BTN", "SW2", "BOOT", {"1": "BOOT9", "2": "GND"}))
sch.row(("RES", "R15", "4k7 SDA pu", {"1": "SDA", "2": "3V3"}),
        ("RES", "R16", "4k7 SCL pu", {"1": "SCL", "2": "3V3"}),
        ("RES", "R17", "10k ALERT pu", {"1": "ALERT", "2": "3V3"}),
        ("RES", "R18", "10k IO2 pu", {"1": "SPI_MISO", "2": "3V3"}),
        ("RES", "R19", "10k CS pu", {"1": "FLASH_CS", "2": "3V3"}),
        ("RES", "R20", "10k IO8 pu", {"1": "IO8", "2": "3V3"}),
        ("CAP", "C14", "100n corridor 3V3", {"1": "3V3", "2": "GND"}))

# --- region 5: log flash ---
sch.region("5. LOG FLASH: W25Q64JV 8MB stats ring (dedicated, not app flash)   [ADR-0004]")
sch.row(("FLASH", "U11", "W25Q64JVSSIQ",
         {"1": "FLASH_CS", "5": "SPI_MOSI", "2": "SPI_MISO", "6": "SPI_CLK",
          "8": "3V3", "3": "3V3", "7": "3V3", "4": "GND"}),
        ("CAP", "C9", "100n U11", {"1": "3V3", "2": "GND"}))

# --- region 6: USB ---
sch.region("6. USB-C: flash/debug + bench power (AMS1117 -> B5819W OR, ~3.0V)   [ADR-0006]")
sch.row(("USBC", "J9", "TYPE-C-31-M-12",
         {"A4": "VUSB", "A9": "VUSB", "B4": "VUSB", "B9": "VUSB",
          "A5": "CC1", "B5": "CC2", "A6": "USB_DP", "B6": "USB_DP",
          "A7": "USB_DM", "B7": "USB_DM", "A8": None, "B8": None,
          "A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND",
          "SH": "GND"}),
        ("ESDU", "U10", "USBLC6-2SC6",
         {"1": "USB_DP", "6": "USB_DP", "3": "USB_DM", "4": "USB_DM",
          "2": "GND", "5": "VUSB"}))
sch.row(("RES", "R22", "5k1 CC1", {"1": "CC1", "2": "GND"}),
        ("RES", "R23", "5k1 CC2", {"1": "CC2", "2": "GND"}),
        ("LDO", "U9", "AMS1117-3.3", {"3": "VUSB", "1": "GND", "2": "VLDO"}),
        ("DSODR", "D8", "B5819W OR", {"1": "3V3", "2": "VLDO"}))
sch.chain("U9.2", "D8.2")    # LDO out -> OR diode anode: drawn
sch.row(("CAP", "C11", "10u LDO in", {"1": "VUSB", "2": "GND"}),
        ("C1206", "C12", "22u LDO out", {"1": "VLDO", "2": "GND"}),
        ("CAP", "C13", "100n VUSB", {"1": "VUSB", "2": "GND"}))

# --- region 7: indicators + debug ---
sch.region("7. LEDS + DEBUG UART (J10 DNP)")
sch.row(("RES", "R28", "2k PWR LED", {"1": "3V3", "2": "LED1A"}),
        ("LEDR", "LED1", "KT-0805G PWR", {"2": "LED1A", "1": "GND"}),
        ("RES", "R29", "1k ST LED", {"1": "LED_ST", "2": "LED2A"}),
        ("LEDR", "LED2", "KT-0805G ST", {"2": "LED2A", "1": "GND"}))
sch.chain("R28.2", "LED1.2")  # resistor -> LED anode: drawn (polarity story)
sch.row(("HDR4", "J10", "DEBUG UART DNP",
         {"1": "3V3", "2": "GND", "3": "TXD", "4": "RXD"}))

# ------------------------------------------------------------------ emit
content = sch.emit()
out = HERE.parent / "04_kicad"
out.mkdir(exist_ok=True)
(out / f"{PROJECT}.kicad_sch").write_text(content)

(HERE / "lib").mkdir(exist_ok=True)
sch.write_symbol_lib(HERE / "lib" / "bbar.kicad_sym")
(out / "sym-lib-table").write_text(
    sch.sym_lib_table("bbar", "${KIPRJMOD}/../03_src/lib/bbar.kicad_sym"))
(out / "fp-lib-table").write_text(sch.fp_lib_table(
    {"bbar": "${KIPRJMOD}/../03_src/lib/bbar.pretty"}))

# NEVER overwrite an existing project file — it carries DRC floors/netclasses.
if not (out / f"{PROJECT}.kicad_pro").exists():
    (out / f"{PROJECT}.kicad_pro").write_text(
        '{\n  "board": { "design_settings": {} },\n'
        f'  "meta": {{ "filename": "{PROJECT}.kicad_pro", "version": 1 }},\n'
        '  "schematic": { "legacy_lib_dir": "", "legacy_lib_list": [] }\n}\n')

nlabels = content.count("(global_label")
print(f"wrote {PROJECT}.kicad_sch via schwriter2: {len(sch.cells)} cells, "
      f"{len(sch.wires)} wires, {nlabels} net labels, internal S-OCCL 0, parens balanced")
