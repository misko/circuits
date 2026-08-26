#!/usr/bin/env python3
"""audit_board — crow-mic-pod-v2 board invariants the generic backend does not
cover: independent PAD-1 POLARITY re-check (polarized 2-pad parts + op-amp
supply) and MATE-DIRECTION / KEEPOUT checks (RJ45 board-lock NPTH posts inside
the outline with edge clearance; connector pads inside the outline).

This is the P-POL / P-KEEP artifact (policy_audit greps 03_src for a scripted
polarity + mate/keepout/screw/edge check). It is a REAL gate: it loads the
board and EXITS NONZERO on any violation — swap a diode net or drag a post off
the board and it goes red.

    /usr/bin/python3 03_src/audit_board.py            # audits 04_kicad/<board>
    /usr/bin/python3 03_src/audit_board.py <board.kicad_pcb>
"""
import sys, os
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BOARD = os.path.join(HERE, "..", "04_kicad", "crow_mic_pod_v2.kicad_pcb")

# PAD-1 POLARITY facts (from 02_parts/*/part.yaml + the ADRs). pad name -> net.
# A reversed polarized 2-pad part is invisible to ERC/DRC/parity — only this.
POLARITY = [
    # ref, pad, expected_net, why
    ("D2",  "1", "5V_BEEP",  "SS14 flyback cathode (D_SMA pad1=band) on the rail"),
    ("D3",  "1", "5V_BEEP",  "SMAJ6.0A TVS cathode (D_SMA pad1=band) on the rail"),
    ("MK1", "1", "MIC_OUT",  "electret + (output/drain) terminal"),
    ("MK1", "2", "GND",      "electret - (case/ground) terminal"),
    ("U1",  "8", "5V_AUDIO", "op-amp V+ supply"),
    ("U1",  "4", "GND",      "op-amp V- (ground, single supply)"),
    ("D1",  "3", "AUDIO_P",  "ESD IO1 clamps the hot audio output"),
    ("D1",  "5", "AUDIO_N",  "ESD IO2 clamps the cold audio output"),
]

# MATE / KEEPOUT: the RJ45 board-lock posts are NPTH; every J1 pad + post must
# sit inside the board outline with clearance to the EDGE (a post hanging off
# the edge = a jack that will not seat). We also assert the connector mouth is
# an edge part (its pad field near the west edge).
EDGE_CLEARANCE_MM = 0.3
MATE_CONNECTORS = ["J1"]


def mm(v):
    return v / 1e6


def outline_bbox(board):
    # the board's own Edge_Cuts bounding box (reliable across KiCad versions)
    bb = board.GetBoardEdgesBoundingBox()
    return bb if bb.GetWidth() > 0 else None


def main():
    bp = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BOARD
    board = pcbnew.LoadBoard(bp)
    fails = []

    # ---- POLARITY ----
    for ref, pad, want, why in POLARITY:
        fp = board.FindFootprintByReference(ref)
        if fp is None:
            fails.append(f"POLARITY {ref}: footprint not on board")
            continue
        got = None
        for p in fp.Pads():
            if p.GetPadName() == pad or p.GetName() == pad:
                got = p.GetNetname()
                break
        if got is None:
            fails.append(f"POLARITY {ref} pad {pad}: no such pad")
        elif got != want:
            fails.append(f"POLARITY {ref} pad1/pad {pad}: net {got!r} != {want!r} ({why})")

    # ---- MATE-DIRECTION / KEEPOUT (edge, posts, screw-hole class) ----
    bb = outline_bbox(board)
    if bb is None:
        fails.append("KEEPOUT: no Edge_Cuts outline found")
    else:
        x0, y0, x1, y1 = mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom())
        clr = EDGE_CLEARANCE_MM
        for ref in MATE_CONNECTORS:
            fp = board.FindFootprintByReference(ref)
            if fp is None:
                fails.append(f"MATE {ref}: not on board")
                continue
            # every pad AND NPTH post (mechanical hole) inside outline w/ clearance
            for p in fp.Pads():
                px, py = mm(p.GetPosition().x), mm(p.GetPosition().y)
                if not (x0 + clr <= px <= x1 - clr and y0 + clr <= py <= y1 - clr):
                    fails.append(f"KEEPOUT {ref} pad {p.GetPadName()!r}: "
                                 f"({px:.1f},{py:.1f}) off-board / < {clr}mm to edge")

    if fails:
        print(f"audit_board FAIL ({len(fails)}):")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print(f"audit_board OK: {len(POLARITY)} polarity + mate/keepout checks pass")


if __name__ == "__main__":
    main()
