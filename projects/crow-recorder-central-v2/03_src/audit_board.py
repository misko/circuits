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
    ("U10", "1", "5V",          "XC6227 CE (active-high, tied to the 5V input)"),
    ("U10", "4", "5V",          "XC6227 analog LDO VIN (5V -> 3V3A)"),
    ("U10", "2", "GND",         "XC6227 VSS (pin 2 = tab)"),
    ("U10", "5", "3V3A",        "XC6227 analog LDO VOUT"),
]

# MATE / KEEPOUT: every external connector's pads + NPTH board-lock posts must
# sit inside the board outline with clearance to the EDGE (a post hanging off
# the edge = a jack that will not seat).
EDGE_CLEARANCE_MM = 0.3
MATE_CONNECTORS = ["J1", "J2", "J3", "J4", "J5", "J6", "J7", "J8", "J9",
                   "J10", "J_DBG"]

# USB HS DIFF-PAIR length/spread + geometry gate (R-LEN; external review F2,
# 2026-07-24). The pair is timing-critical: XMOS XU316 layout guide requires
# 90ohm differential, coupled, max intra-pair skew 1mm. Geometry solved for
# JLCPCB JLC06161H-3313 (L1 over In1 GND: prepreg 3313 h=0.0994mm Er=4.1,
# 1oz + mask): w=0.125mm gap=0.15mm -> Zdiff ~90ohm (2D FD field solve, see
# DETAIL_DESIGN "USB 90ohm"). Enforced here by MEASUREMENT of the routed
# copper: length spread <= 1mm, every segment at the solved width, the whole
# pair on F.Cu with ZERO vias (uninterrupted In1 reference plane).
USB_PAIR = ("USB_DP", "USB_DN")
USB_SKEW_MM = 1.0
USB_WIDTH_MM = 0.125

# U1 (XU316) EP thermal-via gate (external review F1, 2026-07-24): the 16
# EP holes must be REAL VIA OBJECTS (ViaDrill in the drill file), net GND,
# 0.30/0.15, inside the 4.7mm EP under U1 — not duplicate-numbered
# thru-hole pads (those emitted as ComponentDrill and read as open plated
# component holes under the pasted EP).
U1_EP_VIAS = 16
U1_EP_HALFSPAN_MM = 2.0   # via grid is +/-1.65mm around U1 centre
U1_EP_DRILL_MM = 0.15


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

    # ---- USB HS DIFF PAIR: length spread + width + reference integrity ----
    usb_len = {n: 0.0 for n in USB_PAIR}
    usb_bad = []
    f_cu = board.GetLayerID("F.Cu")
    for t in board.GetTracks():
        net = t.GetNetname()
        if net not in USB_PAIR:
            continue
        if t.GetClass() == "PCB_VIA":
            usb_bad.append(f"USB {net}: via at "
                           f"({mm(t.GetPosition().x):.2f},"
                           f"{mm(t.GetPosition().y):.2f}) — pair must stay on "
                           f"F.Cu over the In1 reference plane")
            continue
        usb_len[net] += mm(t.GetLength())
        w = mm(t.GetWidth())
        if abs(w - USB_WIDTH_MM) > 0.001:
            usb_bad.append(f"USB {net}: segment width {w:.3f}mm != solved "
                           f"{USB_WIDTH_MM}mm (90ohm geometry)")
        if t.GetLayer() != f_cu:
            usb_bad.append(f"USB {net}: segment on "
                           f"{board.GetLayerName(t.GetLayer())} — pair must "
                           f"stay on F.Cu over In1")
    for n in USB_PAIR:
        if usb_len[n] <= 0.0:
            usb_bad.append(f"USB {n}: no routed copper found")
    if not usb_bad:
        spread = abs(usb_len[USB_PAIR[0]] - usb_len[USB_PAIR[1]])
        if spread > USB_SKEW_MM:
            usb_bad.append(
                f"USB pair length spread {spread:.3f}mm > {USB_SKEW_MM}mm "
                f"(XU316 skew budget): "
                f"{USB_PAIR[0]}={usb_len[USB_PAIR[0]]:.2f}mm "
                f"{USB_PAIR[1]}={usb_len[USB_PAIR[1]]:.2f}mm")
        else:
            print(f"USB pair: {USB_PAIR[0]}={usb_len[USB_PAIR[0]]:.2f}mm "
                  f"{USB_PAIR[1]}={usb_len[USB_PAIR[1]]:.2f}mm "
                  f"spread={spread:.3f}mm (<= {USB_SKEW_MM}mm), width "
                  f"{USB_WIDTH_MM}mm, all F.Cu, 0 vias")
    fails += usb_bad

    # ---- U1 EP THERMAL VIAS: real via objects, GND, inside the EP ----
    u1 = board.FindFootprintByReference("U1")
    if u1 is None:
        fails.append("U1-EP: U1 not on board")
    else:
        cx, cy = mm(u1.GetPosition().x), mm(u1.GetPosition().y)
        got = 0
        for t in board.GetTracks():
            if t.GetClass() != "PCB_VIA":
                continue
            px, py = mm(t.GetPosition().x), mm(t.GetPosition().y)
            if abs(px - cx) <= U1_EP_HALFSPAN_MM and \
                    abs(py - cy) <= U1_EP_HALFSPAN_MM:
                if t.GetNetname() != "GND":
                    fails.append(f"U1-EP via ({px:.2f},{py:.2f}): net "
                                 f"{t.GetNetname()!r} != GND")
                elif abs(mm(t.GetDrillValue()) - U1_EP_DRILL_MM) > 0.001:
                    fails.append(f"U1-EP via ({px:.2f},{py:.2f}): drill "
                                 f"{mm(t.GetDrillValue()):.3f} != "
                                 f"{U1_EP_DRILL_MM}")
                else:
                    got += 1
        if got < U1_EP_VIAS:
            fails.append(f"U1-EP: {got} GND thermal VIAS under the EP, "
                         f"need {U1_EP_VIAS} (F1: pads are not vias — "
                         f"ComponentDrill vs ViaDrill)")
        else:
            print(f"U1-EP: {got} GND 0.30/0.15 thermal vias inside the EP")

    if fails:
        print(f"audit_board FAIL ({len(fails)}):")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print(f"audit_board OK: {len(POLARITY)} polarity + "
          f"{len(MATE_CONNECTORS)} connector mate/keepout checks + "
          f"USB diff-pair length-spread + U1 EP thermal-via checks pass")


if __name__ == "__main__":
    main()
