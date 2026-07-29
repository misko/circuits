#!/usr/bin/env python3
"""Rescue the GND SMD pads KiCad's DRC still reports as unconnected after
stitch (a handful boxed inside the dense PCM1865 / USB-C escape where the
GND pour can't thermal-reach and the grid via-on-pad-centre is too close to
the part's own rail pad). Runs AFTER stitch in the rebuild chain.

Per flagged GND pad: drop a 0.30/0.15 via that OVERLAPS the pad at its OUTER
edge (via centre 0.05mm inside the far edge -> ~0.28mm connection chord, and
maximal clearance to the part's inward rail pad), bonding pad->via->In1/In4
plane. Exact-collide + hole-to-hole(0.2) checked. If no via fits, route a
short GND stub (joinpath) on F.Cu/B.Cu to the nearest GND via. Verified by
re-running DRC: unconnected must fall and nothing else may rise.
"""
import json
import math
import os
import subprocess
import sys
from pathlib import Path
_sk = Path(os.path.expanduser("~/.claude/skills/kicad-pcb/scripts"))
sys.path.insert(0, str(_sk))
import pcbnew
from pcb_toolkit import Toolkit

PCB = str(Path(__file__).parent.parent / "04_kicad" / "crow_recorder_central.kicad_pcb")
NM = 1e6
LAY = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.In3_Cu, pcbnew.In4_Cu, pcbnew.B_Cu)


def drc():
    out = Path("/tmp/_gr_drc.json")
    subprocess.run(["kicad-cli", "pcb", "drc", "--severity-all", "--refill-zones",
                    "--format", "json", "-o", str(out), PCB],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return json.load(open(out))


def flagged_pads(d):
    refs = set()
    for v in d["unconnected_items"]:
        for it in v.get("items", []):
            desc = it.get("description", "")
            if desc.startswith("Pad ") and "[GND]" in desc and " of " in desc:
                refs.add(desc.split(" of ", 1)[1].split(" on ", 1)[0].strip())
    return refs


d0 = drc()
base_v = len(d0["violations"])
targets = flagged_pads(d0)
print("flagged GND pads:", sorted(targets))

b = pcbnew.LoadBoard(PCB)
tk = Toolkit(b, 0.1)
gnd = b.FindNet("GND")
gnc = gnd.GetNetCode()
all_vias = [(v.GetPosition().x / NM, v.GetPosition().y / NM, v.GetDrillValue() / 2 / NM)
            for v in b.GetTracks() if v.GetClass() == "PCB_VIA"]


def h2h_ok(x, y, dr=0.075):
    return all((x - vx) ** 2 + (y - vy) ** 2 >= (0.2 + dr + vr) ** 2
               for vx, vy, vr in all_vias)


def rescue_pad(fp, p):
    px, py = p.GetPosition().x / NM, p.GetPosition().y / NM
    hw, hh = p.GetSize().x / 2 / NM, p.GetSize().y / 2 / NM
    fc = fp.GetPosition()
    ox, oy = px - fc.x / NM, py - fc.y / NM
    L = math.hypot(ox, oy) or 1.0
    ox, oy = ox / L, oy / L
    vr = 0.15
    # via centre candidates: outer edge along +outward, small perpendicular slides
    for f in (1.0, 0.75, 0.5, 0.25):
        rx, ry = (hw - 0.05) * f, (hh - 0.05) * f
        for perp in (0.0, 0.4, -0.4, 0.8, -0.8):
            x = round(px + ox * rx - oy * (min(hw, hh) - 0.05) * perp, 3)
            y = round(py + oy * ry + ox * (min(hw, hh) - 0.05) * perp, 3)
            if not h2h_ok(x, y):
                continue
            if tk.via_site_ok(x, y, gnc, size=0.30, drill=0.15,
                              hole_to_copper=0.205, layers=LAY):
                tk.add_via(x, y, gnd, size=0.30, drill=0.15)
                all_vias.append((x, y, vr))
                return f"via@({x},{y})"
    # fallback: F.Cu stub to nearest GND via (>0.4mm away so joinpath emits a
    # real segment, not a degenerate zero-length track). The pad is F.Cu; a
    # B.Cu stub would need a via at the pad -> F.Cu only.
    gvias = sorted(((vx, vy) for vx, vy, vr in all_vias
                    if (vx - px) ** 2 + (vy - py) ** 2 > 0.4 ** 2),
                   key=lambda q: (q[0] - px) ** 2 + (q[1] - py) ** 2)
    for tx, ty in gvias[:8]:
        w = tk.joinpath("GND", (px, py), (tx, ty), 0.2, layer=pcbnew.F_Cu)
        if w:
            return f"stub F.Cu->({tx:.2f},{ty:.2f}) w={w}"
    return None


done, stuck = [], []
for fp in b.GetFootprints():
    if fp.GetReference() not in targets:
        continue
    for p in fp.Pads():
        if p.GetNetname() != "GND" or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
            continue
        r = rescue_pad(fp, p)
        tag = f"{fp.GetReference()}.{p.GetPadName()}"
        (done if r else stuck).append(tag)
        print(f"  {tag}: {r}")

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(PCB)


# ---- bond remaining unconnected GND copper to the plane. Whatever a leftover
# unconnected GND item references (a boxed pad, or a loose KRT GND stub that is
# actually load-bearing to a pad), a via dropped ON it bonds it to In1/In4.
# Iterate: each round re-reads DRC and drops one via per still-floating point.
def gnd_points():
    d = drc()
    pts = []
    for v in d["unconnected_items"]:
        for it in v.get("items", []):
            desc = it.get("description", "")
            p = it.get("pos", {})
            if p.get("x") is None:
                continue
            if desc.startswith("Track [GND]") or (desc.startswith("Pad ") and "[GND]" in desc):
                pts.append((p["x"], p["y"]))
    return pts


bonded = 0
for _ in range(12):
    pts = gnd_points()
    if not pts:
        break
    bb = pcbnew.LoadBoard(PCB)
    tk2 = Toolkit(bb, 0.1)
    g2 = bb.FindNet("GND")
    av = [(v.GetPosition().x / NM, v.GetPosition().y / NM, v.GetDrillValue() / 2 / NM)
          for v in bb.GetTracks() if v.GetClass() == "PCB_VIA"]
    placed = False
    for px, py in pts:
        for r in (0.0, 0.15, 0.25, 0.35, 0.5):
            for a in range(0, 360, 30):
                x = round(px + r * math.cos(math.radians(a)), 3)
                y = round(py + r * math.sin(math.radians(a)), 3)
                if not (11.2 < x < 184.8 and 11.2 < y < 130.8):
                    continue
                if not all((x - vx) ** 2 + (y - vy) ** 2 >= (0.2 + 0.075 + vr) ** 2 for vx, vy, vr in av):
                    continue
                if tk2.via_site_ok(x, y, g2.GetNetCode(), size=0.30, drill=0.15,
                                   hole_to_copper=0.205, layers=LAY):
                    tk2.add_via(x, y, g2, size=0.30, drill=0.15)
                    placed = True
                    bonded += 1
                    break
            if placed:
                break
        if placed:
            break
    if not placed:
        break
    pcbnew.ZONE_FILLER(bb).Fill(bb.Zones())
    bb.Save(PCB)
print(f"GND plane-bond vias: {bonded}")

d1 = drc()
print(f"rescued {len(done)}, stuck {len(stuck)} {stuck}")
print(f"unconnected {len(d0['unconnected_items'])} -> {len(d1['unconnected_items'])}; "
      f"violations {base_v} -> {len(d1['violations'])}")
