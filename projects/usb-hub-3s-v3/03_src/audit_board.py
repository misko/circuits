#!/usr/bin/env /usr/bin/python3
"""usb-hub-3s-v3 per-board placement/pad invariant gate (03_src contract step 4).

v3 = v2 MINUS the PD cell (ADR-0001): the TPS25740A (U1), pass FETs Q6/Q7, the
5mR sense RS3, and every PD-config passive are gone, so their invariants are
removed here. The USB-C port is now a plain 5V/5A rail (J5 VBUS on the 5VC net).

Checks beyond the generic generator's own asserts:
  I-POL  2-pad polarized parts: pad 1/5 net == the part-fact net (re-checked
         against the LIVE board, not the netlist -> catches a stale board)
  I-PROX decoupler/support proximity: critical passives within reach of the
         pin they serve (D-ADJ)
  I-EDGE port connectors reach their board edge (mouth off-board)
  I-SILK refdes present on F.SilkS for every part (I8)
Exit 1 on any FAIL.
"""
import os
import sys
import pcbnew

# resolve relative to this file so it works from any cwd (repo root or project root)
_PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARD = os.path.join(_PROJ, "04_kicad", "usb_hub_3s_v2.kicad_pcb")
MM = pcbnew.ToMM

POLARIZED = {  # ref -> (pad, expected net)
    "J1": ("1", "GND"),
    "D1": ("1", "VIN"), "D2": ("1", "VIN"),      # TVS + Vgs zener cathodes on VIN
    "D3": ("1", "BOOT_A"), "D4": ("1", "BOOT_C"),  # boot diode cathode = HB side
    "C1": ("1", "VIN"), "C2": ("1", "VIN"),      # polymer positive on VIN
    "Q1": ("5", "VBAT_F"),                        # revpol P-FET drain = battery side
    "Q2": ("5", "VIN"), "Q3": ("5", "SW_A"),     # buck A HS drain=VIN, LS drain=SW
    "Q4": ("5", "VIN"), "Q5": ("5", "SW_C"),     # buck C
    "RS1": ("1", "CS_A"), "RS2": ("1", "CS_C"),
    "U2": ("21", "GND"), "U11": ("21", "GND"),   # LM5116 EP
    # v1.6 status LEDs. Pad 1 is the CATHODE on all five (KiCad Device:LED pin 1 =
    # K; LED_0805_2012Metric marks pad 1 with both the F.Fab chamfer and the
    # F.SilkS band). Checked HERE against the live board as well as in
    # floorplan asserts, because those two read different artifacts: the floorplan
    # assert grades the netlist->board mapping at generation time, this grades the
    # SAVED board after route + stitch + fill (canon M1, and it is what catches a
    # stale 04_kicad). A reversed indicator never lights and looks exactly like a
    # dry joint, so nothing downstream would ever find it.
    "D8": ("1", "LEDPKK"),                        # pack LED cathode -> Q8 drain
    "D9": ("1", "GND"), "D10": ("1", "GND"),      # USB-A port indicators
    "D11": ("1", "GND"), "D12": ("1", "GND"),     # USB-A port 3 + USB-C indicator
}

# (passive, its anchor ref, max center distance mm) - D-ADJ gate
PROX = [
    ("C8", "U2", 9.0),    # VCC cap at U2
    ("C7", "U2", 13.0),   # boot cap (between U2 and Q2; nH-tolerant at ~230kHz)
    ("C13", "Q2", 6.0),   # buck A HF input cap at HS FET drain (VIN)
    ("C23", "U11", 9.0),  # VCC cap at U11
    ("C22", "U11", 13.0), # boot cap
    ("C28", "Q4", 6.0),   # buck C HF input cap at HS FET
    ("R9", "U2", 11.0), ("R18", "U11", 11.0),   # CS kelvin 0R links
    ("C35", "U3", 7.0), ("C36", "U4", 7.0), ("C37", "U5", 7.0),  # port Cin
    ("R20", "U3", 7.0), ("R21", "U4", 7.0), ("R22", "U5", 7.0),  # ILIM
    ("U8", "J2", 11.0), ("U9", "J3", 11.0), ("U10", "J4", 11.0), # ESD near ports
    ("R28", "J5", 12.0), ("R29", "J5", 12.0),   # CC Rp pull-ups near the USB-C receptacle
]

EDGE_X1 = 150.0  # east edge
EDGE_Y1 = 112.0  # south edge


def main():
    b = pcbnew.LoadBoard(BOARD)
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    fails = []

    def padnet(ref, num):
        f = fps.get(ref)
        if not f:
            return None
        for p in f.Pads():
            if p.GetNumber() == num:
                return p.GetNetname()
        return None

    for ref, (pad, want) in POLARIZED.items():
        got = padnet(ref, pad)
        if got != want:
            fails.append(f"I-POL {ref} pad {pad}: net {got!r} != {want!r}")

    for ref, anchor, dmax in PROX:
        fa, fb = fps.get(ref), fps.get(anchor)
        if not fa or not fb:
            fails.append(f"I-PROX missing ref {ref if not fa else anchor}")
            continue
        d = (fa.GetPosition() - fb.GetPosition()).EuclideanNorm()
        if MM(d) > dmax:
            fails.append(f"I-PROX {ref} is {MM(d):.1f}mm from {anchor} (max {dmax})")

    for ref in ("J2", "J3", "J4"):
        f = fps.get(ref)
        if not f:
            fails.append(f"I-EDGE missing {ref}")
            continue
        bb = f.GetBoundingBox(False, False)
        if MM(bb.GetRight()) < EDGE_X1 - 0.5:
            fails.append(f"I-EDGE {ref} body right {MM(bb.GetRight()):.1f} < east edge {EDGE_X1}")
    f = fps.get("J5")
    if not f:
        fails.append("I-EDGE missing J5")
    else:
        bb = f.GetBoundingBox(False, False)
        if MM(bb.GetBottom()) < EDGE_Y1 - 0.5:
            fails.append(f"I-EDGE J5 body bottom {MM(bb.GetBottom()):.1f} < south edge {EDGE_Y1}")

    no_silk = []
    for ref, f in fps.items():
        # SKIP BY ATTRIBUTE, NOT BY NAME PREFIX. This used to read
        # `ref.startswith("H")`, i.e. it decided "is this an assembled part?"
        # from the first letter of a refdes -- which exempted every H* part
        # (a header would have slipped through) and exempted nothing else.
        # v1.6 added FID1-FID3 and the check failed them: a fiducial has no
        # silk refdes ON PURPOSE, because silk beside a fiducial destroys the
        # optical contrast the fiducial exists to provide. FP_BOARD_ONLY is the
        # attribute that actually means "board feature, not a placed part", and
        # it is what mounting holes and fiducials both already carry. Same class
        # of bug as the rotation name-DB: a NAME IS NOT A PART FACT.
        if f.GetAttributes() & pcbnew.FP_BOARD_ONLY or ref.startswith("REF"):
            continue
        r = f.Reference()
        if not (r.IsVisible() and r.GetLayer() == pcbnew.F_SilkS):
            no_silk.append(ref)
    if no_silk:
        fails.append(f"I-SILK refdes not on F.SilkS: {sorted(no_silk)[:8]}...")

    if fails:
        print("AUDIT FAIL")
        for x in fails:
            print(" ", x)
        sys.exit(1)
    print(f"AUDIT PASS: {len(POLARIZED)} polarity, {len(PROX)} proximity, "
          f"4 edge, {len(fps)} silk checks")


if __name__ == "__main__":
    main()
