#!/usr/bin/env python3
"""Nudge track segments off sub-0.09mm clearance violations on the promoted
route artifact (03_src/route/final.kicad_pcb). Runs BEFORE stitch (these are
routed tracks). DRC-driven, per-item, collision-verified, revert-on-regress.

For each clearance violation, pick the movable TRACK segment (prefer the one
whose net is a power rail / the longer one; a pad/via is fixed). Shift its
endpoints perpendicular, AWAY from the conflicting item, by (0.09 - actual +
0.04). Any same-net segment sharing a moved endpoint has that shared vertex
moved too (keeps connectivity, adds a small jog). Every moved/added segment
is exact-collide checked at 0.10mm; if the whole edit is clean AND the DRC
violation count does not rise, keep it, else revert. Iterate.
"""
import json
import math
import os
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, os.path.expanduser("~/.claude/skills/kicad-pcb/scripts"))
import pcbnew
from pcb_toolkit import Toolkit

PCB = str(Path(__file__).parent.parent / "04_kicad" / "crow_array_central.kicad_pcb")
NM = 1e6


def drc_clearance():
    out = Path("/tmp/_cn_drc.json")
    subprocess.run(["kicad-cli", "pcb", "drc", "--severity-all", "--refill-zones", "--format", "json",
                    "-o", str(out), PCB], stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, check=True)
    d = json.load(open(out))
    items = []
    for v in d["violations"]:
        if v["type"] != "clearance":
            continue
        its = v.get("items", [])
        if len(its) != 2:
            continue
        parsed = []
        for it in its:
            desc = it.get("description", "")
            p = it.get("pos", {})
            net = desc.split("[", 1)[1].split("]", 1)[0] if "[" in desc else ""
            kind = "track" if desc.startswith("Track") else ("via" if "Via" in desc else "pad")
            parsed.append((kind, net, p.get("x"), p.get("y")))
        items.append(parsed)
    return items, len(d["violations"])


def total_viol():
    _, n = drc_clearance()
    return n


PWR = {"3V3", "5V", "0V9", "1V8", "5V_P"}


def nudge_once(skip):
    items, _ = drc_clearance()
    for a, bpair in ((it[0], it[1]) for it in items):
        key = (a[1], round(a[2] or 0, 2), round(a[3] or 0, 2),
               bpair[1], round(bpair[2] or 0, 2), round(bpair[3] or 0, 2))
        if key in skip:
            continue
        # choose the track to move: prefer a track item; if both tracks,
        # prefer power net (wide) then the one nearer its own conflict.
        mover, other = None, None
        for cand, oth in ((a, bpair), (bpair, a)):
            if cand[0] == "track":
                if mover is None or (cand[1] in PWR and other and other[1] not in PWR):
                    mover, other = cand, oth
        if mover is None:
            continue
        ox, oy = other[2], other[3]
        b = pcbnew.LoadBoard(PCB)
        tk = Toolkit(b, 0.1)
        nc = b.FindNet(mover[1]).GetNetCode()
        # find the segment of this net nearest the conflict point (mover pos)
        mx, my = mover[2], mover[3]
        seg, sd = None, 1e9
        for t in b.GetTracks():
            if t.GetClass() != "PCB_TRACK" or t.GetNetCode() != nc:
                continue
            ax, ay = t.GetStart().x / NM, t.GetStart().y / NM
            bx, by = t.GetEnd().x / NM, t.GetEnd().y / NM
            dx, dy = bx - ax, by - ay
            L2 = dx * dx + dy * dy
            u = 0 if L2 == 0 else max(0, min(1, ((mx - ax) * dx + (my - ay) * dy) / L2))
            d2 = (mx - ax - u * dx) ** 2 + (my - ay - u * dy) ** 2
            if d2 < sd:
                sd, seg = d2, t
        if seg is None or sd > 0.2 ** 2:
            continue
        ax, ay = seg.GetStart().x / NM, seg.GetStart().y / NM
        bx, by = seg.GetEnd().x / NM, seg.GetEnd().y / NM
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy) or 1.0
        # perpendicular unit; pick the sign that moves AWAY from (ox,oy)
        nxp, nyp = -dy / L, dx / L
        mxm, mym = (ax + bx) / 2, (ay + by) / 2
        if (mxm + nxp - ox) ** 2 + (mym + nyp - oy) ** 2 < (mxm - nxp - ox) ** 2 + (mym - nyp - oy) ** 2:
            nxp, nyp = -nxp, -nyp
        delta = 0.13
        w = seg.GetWidth() / NM
        nax, nay = ax + nxp * delta, ay + nyp * delta
        nbx, nby = bx + nxp * delta, by + nyp * delta
        # collision check moved segment + jog stubs to old endpoints
        if tk.collides(nax, nay, nbx, nby, w, nc, seg.GetLayer(), clr=0.1):
            continue
        if tk.collides(ax, ay, nax, nay, w, nc, seg.GetLayer(), clr=0.1):
            continue
        if tk.collides(bx, by, nbx, nby, w, nc, seg.GetLayer(), clr=0.1):
            continue
        seg.SetStart(pcbnew.VECTOR2I_MM(round(nax, 4), round(nay, 4)))
        seg.SetEnd(pcbnew.VECTOR2I_MM(round(nbx, 4), round(nby, 4)))
        for (px, py, npx, npy) in ((ax, ay, nax, nay), (bx, by, nbx, nby)):
            s = pcbnew.PCB_TRACK(b)
            s.SetStart(pcbnew.VECTOR2I_MM(round(px, 4), round(py, 4)))
            s.SetEnd(pcbnew.VECTOR2I_MM(round(npx, 4), round(npy, 4)))
            s.SetWidth(seg.GetWidth())
            s.SetLayer(seg.GetLayer())
            s.SetNetCode(nc)
            b.Add(s)
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        b.Save(PCB)
        return key
    return None


import shutil
base = total_viol()
BAK = PCB + ".nbak"
skip = set()
for _ in range(60):
    before = total_viol()
    shutil.copy(PCB, BAK)
    k = nudge_once(skip)
    if k is None:
        break
    after = total_viol()
    if after >= before:
        shutil.copy(BAK, PCB)   # revert this nudge, skip this item, try others
        skip.add(k)
        continue
    print(f"  nudge {k[0]} @({k[1]},{k[2]}): {before} -> {after}")
os.remove(BAK) if os.path.exists(BAK) else None
print(f"clearance_nudge: net reduction {base - total_viol()}")
