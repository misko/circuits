#!/usr/bin/env python3
"""KRT tap pass: the SW_B and 5V_C sense-tap trees thread a dense KRT bus
that single L/Z joins cannot cross - so let KRT route them. The tap pads
(plus one pour-fed anchor pad per net) are renamed to temp nets in a COPY,
KRT routes only those, and the segments come back with the net renamed.

usage: route_taps_krt.py prep|finish"""
import sys
from pathlib import Path
import pcbnew

HERE = Path(__file__).parent
PCB = HERE.parent / "04_kicad" / "usb_power_3s.kicad_pcb"
TIN = HERE.parent / "06_build" / "route" / "taps_in.kicad_pcb"
TOUT = HERE.parent / "06_build" / "route" / "taps_out.kicad_pcb"

GROUPS = {  # temp net -> (real net, [(ref, pad), ...] incl. one pour-fed anchor)
    "TAPB": ("SW_B", [("CB3", "2"), ("RB2", "2"), ("QB1", "1"), ("U3", "19")]),
    "TAPC": ("5V_C", [("RA3", "1"), ("CA10", "1"), ("R21", "1"), ("CA63", "1")]),
    "TAPW": ("SW_A", [("U2", "19"), ("QA1", "1"), ("CA3", "2"), ("RA2", "2")]),
    "TAPF": ("FE_MID", [("U1", "10"), ("Q1", "5")]),
    "TAPG": ("GND", [("CB4", "2"), ("CB2", "2")]),
    "TAPH": ("GND", [("U3", "12"), ("U3", "21")]),
    "TAPU": ("VSW", [("U2", "20"), ("QA1", "5")]),
    "TAPV": ("VSW", [("U3", "20"), ("QB1", "5")]),
}

if sys.argv[1] == "prep":
    src = sys.argv[2] if len(sys.argv) > 2 else str(PCB)
    b = pcbnew.LoadBoard(src)
    for tmp, (real, pads) in GROUPS.items():
        ni = pcbnew.NETINFO_ITEM(b, tmp)
        b.Add(ni)
        for ref, num in pads:
            fp = b.FindFootprintByReference(ref)
            for p in fp.Pads():
                if p.GetNumber() == num and p.GetNetname() == real:
                    p.SetNet(ni)
    dst = sys.argv[3] if len(sys.argv) > 3 else str(TIN)
    b.Save(dst)
    print(f"prep: wrote {dst} with temp nets {list(GROUPS)}")
else:  # finish: rename temp nets back in KRT's output so import maps them
    tgt = Path(sys.argv[2]) if len(sys.argv) > 2 else TOUT
    s = tgt.read_text()
    for tmp, (real, _) in GROUPS.items():
        s = s.replace(f'(net "{tmp}")', f'(net "{real}")')
    tgt.write_text(s)
    print("finish: temp nets renamed back")
