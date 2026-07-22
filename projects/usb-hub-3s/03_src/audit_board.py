#!/usr/bin/env /usr/bin/python3
"""usb-hub-3s per-board placement/pad invariant gate (03_src contract step 4).

Checks beyond the generic generator's own asserts:
  I-POL  2-pad polarized parts: pad 1 net == the part-fact net (re-checked
         here against the LIVE board, not the netlist -> catches a stale board)
  I-PROX decoupler/support proximity: critical passives within reach of the
         pin they serve (D-ADJ)
  I-EDGE port connectors overhang or reach their board edge
  I-SILK refdes present on F.SilkS for every part (I8) - generator emits them;
         this asserts they survived
Exit 1 on any FAIL.
"""
import sys
import pcbnew

BOARD = "04_kicad/usb_hub_3s.kicad_pcb"
MM = pcbnew.ToMM

POLARIZED = {  # ref -> (pad, expected net)
    "J1": ("1", "GND"), "D1": ("1", "VBAT_F"), "D2": ("1", "VCONN5V"),
    "D3": ("1", "VBUSC"), "D4": ("1", "BOOT_A"), "D5": ("1", "VIN"),
    "D6": ("1", "LX2"), "D7": ("1", "LX1"),
    "C1": ("1", "VIN"), "C2": ("1", "VIN"), "C26": ("1", "VOUT_PD"),
    "Q1": ("5", "VBAT_F"), "Q8": ("5", "VOUT_PD"),
}

# (passive, its anchor ref, max center distance mm) - D-ADJ gate
PROX = [
    ("C9", "Q2", 7.0),     # buck hf input cap at HS FET
    ("C18", "U2", 8.0),    # boot cap at HB/SW pins
    ("C19", "U2", 8.0),    # VCC cap
    ("R1", "U2", 7.5),     # RT at pins (center-based; pin col is 3mm off center)
    ("C14", "U2", 7.5),    # CRAMP at pins
    ("C21", "U1", 10.5),   # BST2 cap near chip/bridge
    ("C22", "U1", 12.0),   # BST1 cap (its LX1 side IS the pour edge; BST loop = pad->pour->pin17, nH-tolerant at 250kHz)
    ("C30", "U1", 9.0),    # VCC5V cap at pin (center-based; QFN 7mm wide)
    ("C31", "U1", 9.0),    # VCCIO cap at pin
    ("C20", "U1", 13.0),   # input sense RC sits mid-path chip<->RS2 shunt
    ("C25", "U1", 10.0),   # output sense filter
    ("C33", "U3", 6.0), ("C34", "U4", 6.0), ("C35", "U5", 6.0),
    ("R10", "U3", 6.0), ("R11", "U4", 6.0), ("R12", "U5", 6.0),
    ("U8", "J2", 18.0), ("U9", "J3", 18.0), ("U10", "J4", 18.0),  # ESD near ports (conn origin sits ~10mm east of its pad row)
    ("D8", "J5", 14.0), ("D9", "J5", 14.0),
]

EDGE_X1 = 130.0  # east edge


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
        if MM(bb.GetBottom()) < 110.0 - 0.5:
            fails.append(f"I-EDGE J5 body bottom {MM(bb.GetBottom()):.1f} < south edge 110.0")

    no_silk = []
    for ref, f in fps.items():
        if ref.startswith("H"):
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
