"""Generate 04_kicad/crow_array_pod.kicad_sch — schwriter2 (structure only).

The engine computes every coordinate, wires the story chain (canon S6:
mic bias -> capsule, coupling -> bias R, stage-A feedback string, stage-B
inverter string, isolation -> choke, beeper feed, decoupler), draws GND as
power-symbol ground icons, and gates itself on internal S-OCCL == 0.

Pin numbers are PHYSICAL PADS from 02_parts/<MPN>/part.yaml (each cites its
datasheet figure): OPA1678 fig 5-3 p.4 SBOS855E (1=OUT_A 2=-IN_A 3=+IN_A
4=V- 5=+IN_B 6=-IN_B 7=OUT_B 8=V+); TPD2E2U06 DRL pin table p.3 SLLSEG9C
(1,2=NC 3=IO1 4=GND 5=IO2); CMT-8504 mech drawing p.2 (1=+ 2=- 3,4=dummy);
SS14/SMAJ D_SMA pad1=cathode; WE-SL2 windings 1-4 / 2-3 (KiCad std pads).
Circuit per 01_docs/ARCHITECTURE.md + DETAIL_DESIGN.md; decisions D3-D9 in
01_docs/BRIEF.md. DNP reserves (D3 TVS, L1 choke, R15 shield bond) carry
"DNP" in their Value so the fab exporter drops them from BOM/CPL while the
pads stay in the gerbers.
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

PROJECT = "crow_array_pod"
SMALL = {"RES", "CAP", "CAPP", "TP", "HDR2", "DSMA"}

rev = Schematic.rev_from_git(HERE, "POD_REV", "pod-v*").replace("pod-", "")
sch = Schematic(
    PROJECT, "crow-array-pod", paper="A3",
    comment="Remote mic pod: AOM-5024L + OPA1678 balanced driver + CMT-8504 beeper; crow-array commission",
    rev=rev, small_syms=SMALL, libname="pod")
sch.no_bom_syms = {"TP"}

# ------------------------------------------------------------------ symbols
sch.defsym("RES", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="R")
sch.defsym("CAP", 7.62, 5.08, [("1", "1", "L", 0), ("2", "2", "R", 0)], ref="C")
# polarized electrolytic: pad 1 = POSITIVE (KiCad CP_Elec convention)
sch.defsym("CAPP", 7.62, 5.08, [("1", "+", "L", 0), ("2", "-", "R", 0)], ref="C")
sch.defsym("TP", 5.08, 5.08, [("1", "1", "L", 0)], ref="TP")
# D_SMA diode: pad 1 = CATHODE (KiCad convention; SS14 band = cathode)
sch.defsym("DSMA", 7.62, 5.08, [("1", "K", "L", 0), ("2", "A", "R", 0)], ref="D")
# mic wire pads (capsule off-board on leads): both pins left, like a header
sch.defsym("HDR2", 7.62, 7.62, [("1", "MIC+", "L", 0), ("2", "MIC-", "L", 1)], ref="J")
# 8-pos screw terminal, linear 1..8 (T568B numbering at the central end)
sch.defsym("TERM8", 10.16, 22.86,
           [(str(n), f"P{n}", "R", n - 1) for n in range(1, 9)], ref="J")
# OPA1678IDR SOIC-8 (fig 5-3 p.4): A stage inputs top-left, outputs right
sch.defsym("OPAMP", 12.7, 20.32,
           [("3", "+IN_A", "L", 0), ("2", "-IN_A", "L", 1),
            ("5", "+IN_B", "L", 3), ("6", "-IN_B", "L", 4),
            ("4", "V-", "L", 6),
            ("8", "V+", "R", 0), ("1", "OUT_A", "R", 2), ("7", "OUT_B", "R", 4)],
           ref="U")
# TPD2E2U06DRL SOT-5 (pin table p.3): 3=IO1 5=IO2 4=GND 1,2=NC
sch.defsym("ESD", 10.16, 12.7,
           [("3", "IO1", "L", 0), ("1", "NC", "L", 2), ("2", "NC", "L", 3),
            ("5", "IO2", "R", 0), ("4", "GND", "R", 3)], ref="D")
# CMT-8504 transducer: + / - left column (electrical), dummies right
sch.defsym("BUZZ", 10.16, 10.16,
           [("1", "+", "L", 0), ("2", "-", "L", 2),
            ("3", "DMY", "R", 0), ("4", "DMY", "R", 2)], ref="BZ")
# WE-SL2 CM choke: windings 1->4 (line A) and 2->3 (line B)
sch.defsym("CMCHOKE", 10.16, 10.16,
           [("1", "A_IN", "L", 0), ("2", "B_IN", "L", 2),
            ("4", "A_OUT", "R", 0), ("3", "B_OUT", "R", 2)], ref="L")

# ------------------------------------------------------------------ footprints
sch.sym_fp = {
    "RES": "Resistor_SMD:R_0805_2012Metric",
    "CAP": "Capacitor_SMD:C_0805_2012Metric",
    "CAPP": "Capacitor_SMD:CP_Elec_6.3x5.4",
    "TP": "TestPoint:TestPoint_Pad_D1.5mm",
    "DSMA": "Diode_SMD:D_SMA",
    "HDR2": "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
    "TERM8": "pod:TerminalBlock_3.5-8P_NoSilk",
    "OPAMP": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
    "ESD": "Package_TO_SOT_SMD:SOT-553",
    "BUZZ": "pod:CMT-8504",
    "CMCHOKE": "Inductor_SMD:L_CommonMode_Wuerth_WE-SL2",
}
# shield bond pad: bigger probe/bond target than a signal TP
sch.ref_fp = {"TP6": "TestPoint:TestPoint_Pad_D2.5mm"}

# ═══════════════════ circuit: structure only ═══════════════════

# --- region 1: cable entry ---
sch.region("1. CABLE ENTRY (Cat5e NOT-ETHERNET pinout, terminal n = T568B pin n)   [P4, ADR-0001/0003]")
sch.row(("TERM8", "J1", "KF128L-3.5-8P",
         {"1": "AUDIO_P", "2": "AUDIO_N", "3": "BEEP_5V", "4": "5V",
          "5": "GND", "6": "BEEP_RET", "7": "5V", "8": "GND"}),
        ("ESD", "D1", "TPD2E2U06DRLR",
         {"3": "AUDIO_P", "5": "AUDIO_N", "4": "GND", "1": None, "2": None}))
sch.chain("J1.1", "D1.3")   # AUDIO+ into the entry ESD clamp: drawn
sch.row(("TP", "TP1", "TP AUDIO+", {"1": "AUDIO_P"}),
        ("TP", "TP2", "TP AUDIO-", {"1": "AUDIO_N"}),
        ("TP", "TP4", "TP 5V", {"1": "5V"}),
        ("TP", "TP5", "TP GND", {"1": "GND"}))
sch.row(("TP", "TP6", "SHIELD BOND PAD", {"1": "SHIELD"}),
        ("RES", "R15", "shield bond DNP", {"1": "SHIELD", "2": "GND"}))

# --- region 2: beeper (driven from CENTRAL via dedicated pair) ---
sch.region("2. CALIBRATION BEEPER (central-switched; clamp: flyback pop., TVS empty)   [ADR-0002]")
sch.row(("RES", "R12", "0R beep series", {"1": "BEEP_5V", "2": "BZ_P"}),
        ("BUZZ", "BZ1", "CMT-8504-100-SMT-TR",
         {"1": "BZ_P", "2": "BEEP_RET", "3": None, "4": None}))
sch.chain("R12.2", "BZ1.1")  # series pad -> transducer +: drawn
sch.row(("DSMA", "D2", "SS14 flyback", {"1": "BZ_P", "2": "BEEP_RET"}),
        ("DSMA", "D3", "SMAJ6.0A TVS DNP", {"1": "BZ_P", "2": "BEEP_RET"}))

# --- region 3: filtered bias rail ---
sch.region("3. FILTERED 5VF: mic bias + midpoint reference supply   [D9]")
sch.row(("RES", "R1", "100R 5VF", {"1": "5V", "2": "5VF"}),
        ("CAPP", "C1", "100u 5VF", {"1": "5VF", "2": "GND"}),
        ("CAP", "C2", "100n 5VF", {"1": "5VF", "2": "GND"}))
sch.chain("R1.2", "C1.1")    # filter R into the bulk cap: drawn

# --- region 4: microphone input ---
sch.region("4. MIC INPUT: 3.9k bias, 1u coupling, 100k to midpoint   [source doc table]")
sch.row(("RES", "R2", "3.9k mic bias", {"1": "5VF", "2": "MIC"}),
        ("HDR2", "J2", "MIC PADS (AOM-5024L)", {"1": "MIC", "2": "GND"}))
sch.chain("R2.2", "J2.1")    # bias resistor -> capsule + pad: drawn
sch.row(("CAP", "C3", "1u coupling", {"1": "MIC", "2": "AIN"}),
        ("RES", "R3", "100k bias", {"1": "AIN", "2": "VMID"}))
sch.chain("C3.2", "R3.1")    # coupling cap -> input bias node: drawn

# --- region 5: midpoint ---
sch.region("5. 2.5V MIDPOINT: 10k/10k from 5VF, 10u||100n   [source doc table]")
sch.row(("RES", "R4", "10k div hi", {"1": "5VF", "2": "VMID"}),
        ("RES", "R5", "10k div lo", {"1": "VMID", "2": "GND"}))
sch.chain("R4.2", "R5.1")
sch.row(("CAP", "C4", "10u VMID", {"1": "VMID", "2": "GND"}),
        ("CAP", "C5", "100n VMID", {"1": "VMID", "2": "GND"}),
        ("TP", "TP3", "TP 2V5 MID", {"1": "VMID"}))

# --- region 6: amplifier ---
sch.region("6. OPA1678: A = x1.5 non-inv, B = unity inverter -> diff x3   [source doc table]")
sch.row(("OPAMP", "U1", "OPA1678IDR",
         {"3": "AIN", "2": "FB_A", "5": "VMID", "6": "FB_B",
          "4": "GND", "8": "5V", "1": "A_OUT", "7": "B_OUT"}),
        ("CAP", "C6", "100n U1", {"1": "5V", "2": "GND"}))
sch.chain("U1.8", "C6.1")    # V+ -> decoupler, drawn adjacent (canon S7)
sch.row(("RES", "R6", "10k fb A", {"1": "A_OUT", "2": "FB_A"}),
        ("RES", "R7", "20k gain A", {"1": "FB_A", "2": "VMID"}))
sch.chain("R6.2", "R7.1")    # stage-A feedback divider: drawn
sch.row(("RES", "R8", "20k inv in", {"1": "A_OUT", "2": "FB_B"}),
        ("RES", "R9", "20k inv fb", {"1": "FB_B", "2": "B_OUT"}))
sch.chain("R8.2", "R9.1")    # stage-B inverter string: drawn
sch.row(("CAP", "C7", "10u 5V bulk", {"1": "5V", "2": "GND"}))

# --- region 7: output isolation + EMI reserve ---
sch.region("7. OUTPUT: 68R/leg -> CM-choke reserve (0R bridged) -> pair   [D7]")
sch.row(("RES", "R10", "68R iso +", {"1": "A_OUT", "2": "AUD_P_I"}),
        ("CMCHOKE", "L1", "CM choke DNP",
         {"1": "AUD_P_I", "2": "AUD_N_I", "4": "AUDIO_P", "3": "AUDIO_N"}))
sch.chain("R10.2", "L1.1")   # isolation R into the choke reserve: drawn
sch.row(("RES", "R11", "68R iso -", {"1": "B_OUT", "2": "AUD_N_I"}),
        ("RES", "R13", "0R choke byp +", {"1": "AUD_P_I", "2": "AUDIO_P"}),
        ("RES", "R14", "0R choke byp -", {"1": "AUD_N_I", "2": "AUDIO_N"}))

# ------------------------------------------------------------------ emit
content = sch.emit()
out = HERE.parent / "04_kicad"
out.mkdir(exist_ok=True)
(out / f"{PROJECT}.kicad_sch").write_text(content)

(HERE / "lib").mkdir(exist_ok=True)
sch.write_symbol_lib(HERE / "lib" / "pod.kicad_sym")
(out / "sym-lib-table").write_text(
    sch.sym_lib_table("pod", "${KIPRJMOD}/../03_src/lib/pod.kicad_sym"))
(out / "fp-lib-table").write_text(sch.fp_lib_table(
    {"pod": "${KIPRJMOD}/../03_src/lib/pod.pretty"}))

# NEVER overwrite an existing project file — it carries DRC floors/netclasses.
if not (out / f"{PROJECT}.kicad_pro").exists():
    (out / f"{PROJECT}.kicad_pro").write_text(
        '{\n  "board": { "design_settings": {} },\n'
        f'  "meta": {{ "filename": "{PROJECT}.kicad_pro", "version": 1 }},\n'
        '  "schematic": { "legacy_lib_dir": "", "legacy_lib_list": [] }\n}\n')

nlabels = content.count("(global_label")
print(f"wrote {PROJECT}.kicad_sch via schwriter2: {len(sch.cells)} cells, "
      f"{len(sch.wires)} wires, {nlabels} net labels, internal S-OCCL 0, parens balanced")
