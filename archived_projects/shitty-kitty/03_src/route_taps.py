#!/usr/bin/env python3
"""Deterministic tap routing for the three connections KRT could not close
on the saturated corridors (CPI: U2.5 -> C26.2; SDA taps: U4.3 and U6.3 to
the SDA bus). Runs in the rebuild chain AFTER the KRT import and BEFORE
stitch_and_fill; every segment is exact-collision-verified (pcb_toolkit).
FAILS (exit 1) if any tap cannot be closed — never ships a partial net."""
import os, sys, math
from pathlib import Path
_sk = [p for p in (Path(__file__).resolve().parents[3] / "skills" / "kicad-pcb" / "scripts",
                   Path(os.path.expanduser("~/.claude/skills/kicad-pcb/scripts"))) if p.is_dir()]
sys.path.insert(0, str(_sk[0]))
import pcbnew
from pcb_toolkit import Toolkit

PCB = str(Path(__file__).parent.parent / "04_kicad" / "shitty_kitty.kicad_pcb")
b = pcbnew.LoadBoard(PCB)
tk = Toolkit(b, 0.095)  # JLC 4L fab floor 0.09 + margin


def pad_pos(ref, num):
    f = b.FindFootprintByReference(ref)
    p = next(p for p in f.Pads() if p.GetNumber() == num)
    return (p.GetPosition().x / 1e6, p.GetPosition().y / 1e6)


def connected(netname, x, y, tol=0.12):
    """same-net track copper already touching this point?"""
    for t in b.GetTracks():
        if t.GetClass() != "PCB_TRACK" or t.GetNetname() != netname:
            continue
        sx, sy = t.GetStart().x/1e6, t.GetStart().y/1e6
        ex, ey = t.GetEnd().x/1e6, t.GetEnd().y/1e6
        dx, dy = ex-sx, ey-sy
        L2 = dx*dx + dy*dy
        tt = 0 if L2 == 0 else max(0, min(1, ((x-sx)*dx + (y-sy)*dy) / L2))
        if math.hypot(x-sx-tt*dx, y-sy-tt*dy) <= tol + t.GetWidth()/2e6:
            return True
    return False


def nearest_net_point(netname, x, y, maxd=25.0):
    best = None
    for t in b.GetTracks():
        if t.GetClass() != "PCB_TRACK" or t.GetNetname() != netname:
            continue
        for e in (t.GetStart(), t.GetEnd()):
            d = math.hypot(e.x/1e6 - x, e.y/1e6 - y)
            if d < maxd and (best is None or d < best[0]):
                best = (d, e.x/1e6, e.y/1e6)
    return best


failures = []

# pads fed FROM THE In2 POUR: place a via beside the pad + a short verified
# stub (the pour is the trunk; canon R2). Used for 3V3 taps the router
# could not reach through the sensor-cluster maze.
import math as _m
# (GND pads are the stitcher's job — fine-pitch GND rescue there)
PAD_VIA_JOBS = [("3V3", "U4", "20"), ("3V3", "U7", "10"), ("3V3", "U7", "2"),
                ("VIN_12V", "U2", "22"), ("VIN_12V", "U2", "28")]
for netname, ref, num in PAD_VIA_JOBS:
    x1, y1 = pad_pos(ref, num)
    if connected(netname, x1, y1):
        print(f"{netname} pour-feed {ref}.{num}: already connected")
        continue
    net = b.FindNet(netname)
    done = False
    for ring in (0.0, 0.7, 0.9, 1.1, 1.4, 1.8, 2.1, 2.5):
        for ang in (range(0, 360, 15) if ring else (0,)):
            x = round(x1 + ring * _m.cos(_m.radians(ang)), 2)
            y = round(y1 + ring * _m.sin(_m.radians(ang)), 2)
            if not tk.via_site_ok(x, y, net.GetNetCode(), size=0.45, drill=0.3):
                continue
            if ring and tk.collides(x1, y1, x, y, 0.15, net.GetNetCode(), pcbnew.F_Cu) is not None:
                continue
            tk.add_via(x, y, net, size=0.45, drill=0.3)
            if ring:
                tk.add_seg(x1, y1, x, y, net, pcbnew.F_Cu, 0.15)
            note = "via-in-pad (KRT-escape pattern; note solder wicking in ORDER_README)" if not ring else f"via at ({x},{y})"
            print(f"{netname} pour-feed {ref}.{num}: {note}")
            done = True
            break
        if done:
            break
    if not done:
        failures.append(f"{netname}: no pour-feed via site near {ref}.{num}")

# U3.4 ADDR-GND strap rescue: fixed verified geometry through the only
# corridor left by the promoted chain (03_src/route/r5). Fails loudly if a
# future re-route moves the corridor — re-derive then.
STRAP = [("GND", (66.9, 64.8875), (66.9, 66.85), 0.15),
         ("GND", (66.9, 66.85), (66.8, 67.0), 0.15)]
gnd = b.FindNet("GND")
if not connected("GND", 66.9, 64.8875):
    ok_strap = all(tk.collides(*a, *bpt, w, gnd.GetNetCode(), pcbnew.F_Cu) is None
                   for _n, a, bpt, w in STRAP)
    ok_via = tk.via_site_ok(66.8, 67.0, gnd.GetNetCode(), size=0.45, drill=0.3)
    if ok_strap and ok_via:
        for _n, a, bpt, w in STRAP:
            tk.add_seg(*a, *bpt, gnd, pcbnew.F_Cu, w)
        tk.add_via(66.8, 67.0, gnd, size=0.45, drill=0.3)
        print("U3.4 ADDR-GND strap: routed + via to In1")
    else:
        failures.append(f"U3.4 GND strap blocked (segs_ok={ok_strap} via_ok={ok_via})")

# pad-center joins: track ends that touch a pad only by a sliver.
# First remove sub-0.15mm sliver segments near the pad (KRT last-hop
# artifacts that create connection_width throats), then join properly.
for netname, ref, num in [("ACC_INT", "U1", "20")]:
    x1, y1 = pad_pos(ref, num)
    for t2 in [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"
               and t.GetNetname() == netname]:
        L = math.hypot(t2.GetEnd().x - t2.GetStart().x, t2.GetEnd().y - t2.GetStart().y) / 1e6
        d0 = math.hypot(t2.GetStart().x/1e6 - x1, t2.GetStart().y/1e6 - y1)
        if L < 0.15 and d0 < 1.2:
            b.Remove(t2)
    np_ = nearest_net_point(netname, x1, y1, maxd=2.0)
    if np_ and np_[0] > 0.05:
        _, x2, y2 = np_
        if tk.collides(x1, y1, x2, y2, 0.25, b.FindNet(netname).GetNetCode(), pcbnew.F_Cu) is None:
            tk.add_seg(x1, y1, x2, y2, b.FindNet(netname), pcbnew.F_Cu, 0.25)
            print(f"{netname} pad join {ref}.{num}")

JOBS = [("CPI", ("U2", "5"), ("C26", "2")),
        ("SDA", ("U4", "3"), None),      # None -> nearest bus copper
        ("SDA", ("U6", "3"), None)]
for netname, (ref, num), dst in JOBS:
    x1, y1 = pad_pos(ref, num)
    if connected(netname, x1, y1):
        print(f"{netname} tap at {ref}.{num}: already connected")
        continue
    if dst:
        x2, y2 = pad_pos(*dst)
    else:
        np_ = nearest_net_point(netname, x1, y1)
        if not np_:
            failures.append(f"{netname}: no bus copper near {ref}.{num}")
            continue
        _, x2, y2 = np_
    w = tk.joinpath(netname, (x1, y1), (x2, y2), 0.2)
    if w is None:
        got = tk.verified_astar(netname, (x1, y1), (x2, y2), 0.2, grid=0.05)
        if not got:
            got = tk.verified_astar(netname, (x1, y1), (x2, y2), 0.15, grid=0.05)
        if not got:
            failures.append(f"{netname}: {ref}.{num} -> ({x2:.2f},{y2:.2f}) unroutable")
            continue
        print(f"{netname} tap {ref}.{num}: verified A* path")
    else:
        print(f"{netname} tap {ref}.{num}: joinpath at {w}mm")

if failures:
    print("FAILURES:\n  " + "\n  ".join(failures))
    sys.exit(1)
b.Save(PCB)
print("taps routed + saved")
