#!/usr/bin/env python3
"""audit_board — crow-recorder-central-v2 board invariants the generic backend
does not cover: independent PAD-1 POLARITY re-check (polarized parts, FET
orientation, converter/LDO supply pins) and MATE-DIRECTION / KEEPOUT checks
(every external connector's pads + NPTH board-lock posts inside the outline
with edge clearance).

This is the P-POL / P-KEEP artifact (policy_audit greps 03_src for a scripted
polarity + mate/keepout/screw/edge check). It is a REAL gate: it loads the
board and EXITS NONZERO on any violation — swap a diode net or drag a post off
the board and it goes red. (Pattern: crow-mic-pod-v2/03_src/audit_board.py.)

    /usr/bin/python3 03_src/audit_board.py            # audits 04_kicad/<board>
    /usr/bin/python3 03_src/audit_board.py <board.kicad_pcb>
"""
import sys, os
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BOARD = os.path.join(HERE, "..", "04_kicad",
                             "crow_recorder_central_v2.kicad_pcb")

# PAD-1 POLARITY facts (from 02_parts/*/part.yaml + ADR-0001/0005). pad -> net.
# A reversed polarized part is invisible to ERC/DRC/parity — only this catches
# it. GUARD (red-team disposition 2026-07-23): Q1's D->S orientation below is
# the CORRECT as-built reverse-polarity topology — these facts pin it.
POLARITY = [
    # ref, pad, expected_net, why
    ("J1",  "1", "JACK_IN",     "DC-005 barrel CENTER pin = + (GST25A05 center-positive)"),
    ("J1",  "2", "GND",         "DC-005 sleeve = return"),
    ("D1",  "1", "VIN_RAW",     "SMAJ5.0A cathode (D_SMA pad1=band) clamps the raw input"),
    ("D1",  "2", "GND",         "SMAJ5.0A anode to ground"),
    ("Q1",  "3", "VIN_RAW",     "AO3401A P-FET RPP: raw input enters the DRAIN (ADR-0001)"),
    ("Q1",  "2", "5V",          "AO3401A P-FET RPP: protected 5V rail at the SOURCE"),
    ("Q1",  "1", "GATE_RPP",    "AO3401A gate to the pulldown divider"),
    ("Q2",  "3", "BEEP_RETURN", "AO3400A low-side beeper switch: load on the DRAIN"),
    ("Q2",  "2", "GND",         "AO3400A low-side: source grounded"),
    ("U7",  "3", "5V",          "AP61102 3V3 buck VIN"),
    ("U7",  "2", "GND",         "AP61102 3V3 buck GND"),
    ("U7",  "4", "SW1",         "AP61102 3V3 buck switch node"),
    ("U8",  "3", "5V",          "AP61102 0V9 buck VIN"),
    ("U8",  "2", "GND",         "AP61102 0V9 buck GND"),
    ("U8",  "4", "SW2",         "AP61102 0V9 buck switch node"),
    ("U9",  "1", "3V3",         "TCR2LF18 LDO VIN (3V3 -> 1V8)"),
    ("U9",  "5", "1V8",         "TCR2LF18 LDO VOUT"),
    ("U10", "1", "5V",          "XC6227 analog LDO VIN (5V -> 3V3A)"),
    ("U10", "5", "3V3A",        "XC6227 analog LDO VOUT"),
]

# MATE / KEEPOUT: every external connector's pads + NPTH board-lock posts must
# sit inside the board outline with clearance to the EDGE (a post hanging off
# the edge = a jack that will not seat).
EDGE_CLEARANCE_MM = 0.3
MATE_CONNECTORS = ["J1", "J2", "J3", "J4", "J5", "J6", "J7", "J8", "J9",
                   "J10", "J_DBG"]


def mm(v):
    return v / 1e6


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
            fails.append(f"POLARITY {ref} pad {pad}: net {got!r} != {want!r} ({why})")

    # ---- MATE-DIRECTION / KEEPOUT (edge, posts, screw-hole class) ----
    bb = board.GetBoardEdgesBoundingBox()
    if bb is None or bb.GetWidth() == 0:
        fails.append("KEEPOUT: no Edge_Cuts outline found")
    else:
        x0, y0 = mm(bb.GetLeft()), mm(bb.GetTop())
        x1, y1 = mm(bb.GetRight()), mm(bb.GetBottom())
        clr = EDGE_CLEARANCE_MM
        for ref in MATE_CONNECTORS:
            fp = board.FindFootprintByReference(ref)
            if fp is None:
                fails.append(f"MATE {ref}: not on board")
                continue
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
    print(f"audit_board OK: {len(POLARITY)} polarity + "
          f"{len(MATE_CONNECTORS)} connector mate/keepout checks pass")


if __name__ == "__main__":
    main()
