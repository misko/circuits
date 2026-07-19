#!/usr/bin/env python3
"""Deterministic hand-routing of the six sense channels + I2C corridor.

Runs BEFORE KRT (the current KRT respects existing tracks/vias as
obstacles — verified 2026-07-18 with a wall-crossing probe; the router
then completes the west-zone nets AROUND this copper). Everything east
of the electronics zone is a repeated generator-owned pattern
(ADR-0003): Kelvin taps at the shunt pad inner edges, 10R filter Rs,
INA238 pin hookups, A1/A0 address straps, and the B.Cu corridor
(SDA/SCL/ALERT/3V3) crossing under the port slices with via taps.

Channel topology (x rel cx; pcbnew y-down):
- KA (IN+ node): RP at x4.7/y75.6, jog to col 6.3, up to pad10 row 64.5
- KB (IN- + VBUS pin): RN at x6.5/y72.5 — its pad2 IS the column
  (7.46), up to pad9 row 64.0; pad8 (VBUS) joins via the 5.0 jog.
  Planarity: KB's horizontal (64.0) passes NORTH of KA's column top
  (64.5), and KA's jog row (75.6) is SOUTH of KB's column top (72.5) —
  no crossings by construction.
- straps/lane taps fan east of the pad row (columns 8.1..11.35).

Run: /usr/bin/python3 03_src/route_channels.py
"""
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import geom as G  # noqa: E402

PCB = HERE.parent / "04_kicad" / "ble_bus_bar.kicad_pcb"
b = pcbnew.LoadBoard(str(PCB))
F, B = pcbnew.F_Cu, pcbnew.B_Cu


def net(name):
    n = b.FindNet(name)
    if n is None:
        raise RuntimeError(f"net {name} missing")
    return n


nseg = nvia = 0


def seg(x1, y1, x2, y2, netname, layer=F, w=G.W_SIG):
    global nseg
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I_MM(x1, y1))
    t.SetEnd(pcbnew.VECTOR2I_MM(x2, y2))
    t.SetWidth(pcbnew.FromMM(w))
    t.SetLayer(layer)
    t.SetNet(net(netname))
    b.Add(t)
    nseg += 1


def via(x, y, netname, d=G.VIA_D):
    global nvia
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I_MM(x, y))
    v.SetWidth(pcbnew.FromMM(d))
    v.SetDrill(pcbnew.FromMM(G.VIA_DRILL))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetNet(net(netname))
    b.Add(v)
    nvia += 1


RPAD = 0.9575          # 0805 pad center offset
LANE_Y = {"SDA": G.LANE_SDA, "SCL": G.LANE_SCL,
          "ALERT": G.LANE_ALERT, "3V3": G.LANE_3V3}
ADDR = {1: ("GND", "GND"), 2: ("GND", "3V3"), 3: ("GND", "SDA"),
        4: ("GND", "SCL"), 5: ("3V3", "GND"), 6: ("3V3", "3V3")}
STRAP_Y = {"GND": G.GND_BAND_Y, "3V3": G.LANE_3V3,
           "SDA": G.LANE_SDA, "SCL": G.LANE_SCL}

XW, XE = 3.9, 8.1      # INA pad columns (rot 180)
PAD_Y = {"6": 62.5, "7": 63.0, "8": 63.5, "9": 64.0, "10": 64.5,
         "5": 62.5, "4": 63.0, "3": 63.5, "2": 64.0, "1": 64.5}

for i in range(1, 7):
    cx = G.CX[i - 1]
    vf, vp, ka, kb = f"VF{i}", f"VP{i}", f"KA{i}", f"KB{i}"
    # rot-90 filter Rs: pad1 south (tap side), pad2 north (= column start)
    rp_pad1_y, rp_pad2_y = G.RP_Y + RPAD, G.RP_Y - RPAD
    rn_pad1_y, rn_pad2_y = G.RN_Y + RPAD, G.RN_Y - RPAD

    # Kelvin taps at shunt pad INNER edges (audit I-KELVIN) -> filter Rs
    seg(cx + G.KP_ATTACH[0], G.TAP_P_Y, cx + G.RP_X, G.TAP_P_Y, vf, w=G.W_TAP)
    seg(cx + G.RP_X, G.TAP_P_Y, cx + G.RP_X, rp_pad1_y, vf, w=G.W_TAP)
    seg(cx + G.KN_ATTACH[0], G.TAP_N_Y, cx + G.RN_X, G.TAP_N_Y, vp, w=G.W_TAP)
    # (KN tap ends inside RN pad1: pad1 center y 72.4575 vs tap row 72.5)

    # KA: RP.2 (north pad) -> column -> pad10 (IN+)
    seg(cx + G.KA_COL, rp_pad2_y, cx + G.KA_COL, PAD_Y["10"], ka)
    seg(cx + G.KA_COL, PAD_Y["10"], cx + XW, PAD_Y["10"], ka)
    # KB: RN.2 (north pad) -> column -> pad9 (IN-)
    seg(cx + G.KB_COL, rn_pad2_y, cx + G.KB_COL, PAD_Y["9"], kb)
    seg(cx + G.KB_COL, PAD_Y["9"], cx + XW, PAD_Y["9"], kb)
    # pad8 (VBUS) joins the KB node via a jog east of the pad ends
    seg(cx + G.PAD8_JOG_X, PAD_Y["9"], cx + G.PAD8_JOG_X, PAD_Y["8"], kb)
    seg(cx + G.PAD8_JOG_X, PAD_Y["8"], cx + XW, PAD_Y["8"], kb)
    # diff cap CD bridges the KA/KB verticals with its own pads (no tracks)

    # INA GND (pad 7): track west into the VP pour region, via to B.Cu
    seg(cx + XW, PAD_Y["7"], cx + 2.6, PAD_Y["7"], "GND")
    via(cx + 2.6, PAD_Y["7"], "GND")

    # 3V3: lane via -> north vertical -> rail y=61.9 -> drop into pad 6
    # (0.3mm = RAIL3V3 floor; 0.5 would graze the SCL tap via ring)
    x3 = cx + G.COL_3V3
    via(x3, G.LANE_3V3, "3V3")
    seg(x3, G.LANE_3V3, x3, G.V3_NORTH_Y, "3V3", w=0.3)
    seg(x3, G.V3_NORTH_Y, cx + 4.35, G.V3_NORTH_Y, "3V3", w=0.3)
    seg(cx + 4.35, G.V3_NORTH_Y, cx + 4.35, PAD_Y["6"], "3V3", w=0.3)

    # CB bypass: pad1 (south) stubs to the rail; pad2 (north) via-in-pad
    cbx = cx + G.CB_X
    seg(cbx, G.CB_Y + RPAD, cbx, G.V3_NORTH_Y, "3V3", w=0.3)
    via(cbx, G.CB_Y - RPAD, "GND")

    # INA digital pins (east col): SDA/SCL/ALERT taps down to the lanes
    for (pin, col, lane) in [("4", G.COL_SDA, "SDA"), ("5", G.COL_SCL, "SCL"),
                             ("3", G.COL_ALERT, "ALERT")]:
        seg(cx + XE, PAD_Y[pin], cx + col, PAD_Y[pin], lane)
        seg(cx + col, PAD_Y[pin], cx + col, LANE_Y[lane], lane)
        via(cx + col, LANE_Y[lane], lane)

    # A1/A0 address straps (ADR-0003 address map)
    a1, a0 = ADDR[i]
    ty1, ty0 = STRAP_Y[a1], STRAP_Y[a0]
    seg(cx + G.COL_A1, PAD_Y["1"], cx + G.COL_A1, ty1, a1)
    via(cx + G.COL_A1, ty1, a1)
    seg(cx + XE, PAD_Y["2"], cx + G.COL_A0, PAD_Y["2"], a0)
    if a0 == a1:   # merge into A1's column — avoids twin-via hole spacing
        seg(cx + G.COL_A0, PAD_Y["2"], cx + G.COL_A0, ty1 - 0.4, a0)
        seg(cx + G.COL_A0, ty1 - 0.4, cx + G.COL_A1, ty1 - 0.4, a0)
    else:
        seg(cx + G.COL_A0, PAD_Y["2"], cx + G.COL_A0, ty0, a0)
        via(cx + G.COL_A0, ty0, a0)

# ---------------------------------------------------------------- corridor
EAST = {"SDA": G.CX[5] + G.COL_SDA, "SCL": G.CX[5] + G.COL_SCL,
        "ALERT": G.CX[5] + G.COL_ALERT, "3V3": G.CX[5] + G.COL_3V3}
for lane, bx in G.BOUND_X.items():
    y = LANE_Y[lane]
    w = G.LANE_W[lane]
    via(bx, G.BOUND_PAD1_Y, lane)                     # via-in-pad terminal
    seg(bx, G.BOUND_PAD1_Y, bx, y, lane, layer=B, w=w)
    seg(bx, y, EAST[lane], y, lane, layer=B, w=w)

# C14.1 (3V3 lane terminal) west bridge: KRT cannot attach at the
# via-in-pad (boxed by the strip keepout), so hand-bridge the corridor
# to R17.2 (3V3) — KRT then serves R15/16/17 pad2 normally.
via(85.7, 60.9, "3V3")
seg(G.BOUND_X["3V3"], G.BOUND_PAD1_Y, 85.7, G.BOUND_PAD1_Y, "3V3", layer=B)
seg(85.7, G.BOUND_PAD1_Y, 85.7, 60.9, "3V3", layer=B)
seg(85.7, 60.9, G.BOUND_X["ALERT"], 60.9, "3V3")
seg(G.BOUND_X["ALERT"], 60.9, G.BOUND_X["ALERT"], G.BOUND_Y - 0.9575, "3V3")

# C14.2 (GND) sits inside the pocket fenced by the bridge + terminal
# verticals — give it its own path west to the open B.Cu plane.
seg(G.BOUND_X["3V3"], G.BOUND_Y - 0.9575, 85.0, G.BOUND_Y - 0.9575, "GND")
via(85.0, G.BOUND_Y - 0.9575, "GND")

b.Save(str(PCB))
print(f"route_channels: {nseg} segments, {nvia} vias (6 channels + corridor)")
