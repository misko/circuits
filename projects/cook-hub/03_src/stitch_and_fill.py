#!/usr/bin/env python3
"""Post-route: rescue-via every GND SMD pad to the In1 plane, bond the In2
power pours (3V3 / 5VP / 3V3A) to their nets at SMD pads inside the pour
regions, thermal-via the AMS1117 tab (R-THERM), GND stitch grid, fill.
Every via site collide-checked (pcb_toolkit) + PTH-hole guard; the script
FAILS before save if a mandatory rescue comes up short.
NOTHING is added inside geom.NOGO (the engineered bank region).
Run: /usr/bin/python3 03_src/stitch_and_fill.py"""
import math
import os
import sys
from pathlib import Path

_sk = [p for p in (Path(__file__).resolve().parents[3] / "skills" / "kicad-pcb" / "scripts",
                   Path(os.path.expanduser("~/.claude/skills/kicad-pcb/scripts"))) if p.is_dir()]
sys.path.insert(0, str(_sk[0]))
import pcbnew  # noqa: E402
from pcb_toolkit import Toolkit  # noqa: E402

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import geom as G  # noqa: E402

PCB = str(HERE.parent / "04_kicad" / "cook_hub.kicad_pcb")
b = pcbnew.LoadBoard(PCB)
tk = Toolkit(b, 0.15)
MM = pcbnew.ToMM

# pre-pass: dedupe same-net twin vias from KRT pass-chaining
vinfo = [(t, t.GetNetCode(), t.GetPosition().x, t.GetPosition().y)
         for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
dead = set()
for i, (v1, n1, x1, y1) in enumerate(vinfo):
    if i in dead:
        continue
    for j in range(i + 1, len(vinfo)):
        v2, n2, x2, y2 = vinfo[j]
        if j not in dead and n1 == n2 and abs(x1 - x2) < 450000 and abs(y1 - y2) < 450000:
            dead.add(j)
for j in dead:
    b.Remove(vinfo[j][0])
print(f"deduped {len(dead)} twin vias")

USED = {(round(v.GetPosition().x / 1e6, 2), round(v.GetPosition().y / 1e6, 2))
        for v in b.GetTracks() if v.GetClass() == "PCB_VIA"}
PTH = [(p.GetPosition().x / 1e6, p.GetPosition().y / 1e6, p.GetDrillSize().x / 2e6)
       for fp in b.GetFootprints() for p in fp.Pads() if p.GetDrillSize().x > 0]
failures = []


def in_nogo(x, y, margin=0.0):
    nx0, ny0, nx1, ny1 = G.NOGO
    return nx0 - margin < x < nx1 + margin and ny0 - margin < y < ny1 + margin


def try_via(net, x, y, size=0.6, drill=0.3):
    x, y = round(x, 2), round(y, 2)
    if in_nogo(x, y, 0.4):
        return False
    if any((x - ux) ** 2 + (y - uy) ** 2 < 0.62 ** 2 for ux, uy in USED):
        return False
    if any(math.hypot(x - hx, y - hy) < r + drill / 2 + 0.3 for hx, hy, r in PTH):
        return False
    if tk.via_site_ok(x, y, net.GetNetCode(), size=size, drill=drill):
        tk.add_via(x, y, net, size=size, drill=drill)
        USED.add((x, y))
        return True
    return False


def rescue_pad(pad, label, mandatory=True, viainpad=False, stub_w=0.3):
    """Via-in-pad (same-net barrel bonds the pad straight to its plane/pour),
    else a via adjacent to the SMD pad + short F/B stub from the pad.

    viainpad=True is used for pads that sit over a same-net INNER copper
    (GND -> In1 solid plane; 5VP/3V3/3V3A -> In2 pour): a same-net barrel on
    the pad centre bonds pad<->inner directly, so it leaves NO thin outer stub
    and NO single-layer (dangling) via. stub_w is the fallback outer-stub
    width (>= the net's DRU floor: 0.5 for PWR pour nets, else 0.3)."""
    net = pad.GetNet()
    px, py = MM(pad.GetPosition().x), MM(pad.GetPosition().y)
    if viainpad and try_via(net, px, py, size=0.6, drill=0.3):
        return True
    bbox = pad.GetBoundingBox()
    w2 = MM(bbox.GetWidth()) / 2
    h2 = MM(bbox.GetHeight()) / 2
    lay = pad.GetLayer()
    for r in (0.75, 0.95, 1.2, 1.5, 1.9, 2.4, 3.0):
        for ang in range(0, 360, 30):
            vx = px + (w2 + r) * math.cos(math.radians(ang))
            vy = py + (h2 + r) * math.sin(math.radians(ang))
            if not try_via(net, vx, vy):
                continue
            layer = lay if lay in (pcbnew.F_Cu, pcbnew.B_Cu) else pcbnew.F_Cu
            # widen the bond stub to the net floor where the corridor allows;
            # fall back to 0.3 (ampacity-fine for these <0.61A bond taps) so
            # the rescue still lands rather than being dropped.
            for w in (stub_w, 0.3):
                if tk.collides(px, py, round(vx, 2), round(vy, 2), w,
                               net.GetNetCode(), layer):
                    continue
                tk.add_seg(px, py, round(vx, 2), round(vy, 2), net, layer, w)
                return True
    if mandatory:
        failures.append(f"rescue failed: {label} at ({px:.1f},{py:.1f})")
    return False


# is a same-net track/via already within d mm of the pad? then plane spokes
# and KRT routing already serve it (GND pads: the via IS the plane link)
def pad_has_via(pad, d=1.6):
    px, py = MM(pad.GetPosition().x), MM(pad.GetPosition().y)
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA" and t.GetNetCode() == pad.GetNetCode():
            vx, vy = MM(t.GetPosition().x), MM(t.GetPosition().y)
            if (vx - px) ** 2 + (vy - py) ** 2 < d * d:
                return True
    return False


IN2_POUR = {"3V3": lambda x, y: not in_nogo(x, y),
            "5VP": lambda x, y: 26 < x < 53 and 110 < y < 131,
            "3V3A": lambda x, y: 21 < x < 52 and 21 < y < 40}

gnd_ok = gnd_n = pour_n = 0
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetDrillSize().x > 0:
            continue                      # THT reaches the planes directly
        nname = p.GetNetname()
        px, py = MM(p.GetPosition().x), MM(p.GetPosition().y)
        if nname == "GND":
            gnd_n += 1
            if pad_has_via(p):
                gnd_ok += 1
                continue
            # non-fatal: a GND SMD pad boxed-in for both via-in-pad and an
            # adjacent via+stub (dense ESD/divider clusters, KRT tracks crossing
            # under) is reported by the DRC unconnected gate, not silently shipped.
            if rescue_pad(p, f"GND {fp.GetReference()}.{p.GetNumber()}",
                          mandatory=False, viainpad=True):
                gnd_ok += 1
        elif nname in IN2_POUR and IN2_POUR[nname](px, py):
            # U12 (AMS1117) VOUT tab is bonded to the 3V3 pour by the dedicated
            # R-THERM section below (needs >=2 thermal vias); leave it for that.
            if fp.GetReference() == "U12":
                continue
            if not pad_has_via(p, 2.2):
                # adjacent via + short stub (NOT via-in-pad: a 0.6 barrel on a
                # dense 0402 pour pad bridges to its neighbours -> shorts/mask
                # bridges). Stub widened to the PWR floor (0.5) where the
                # corridor allows, else 0.3 (ampacity-fine for <0.61A taps).
                if rescue_pad(p, f"{nname} {fp.GetReference()}.{p.GetNumber()}",
                              mandatory=False, viainpad=False, stub_w=0.5):
                    pour_n += 1
print(f"GND rescue: {gnd_ok}/{gnd_n} SMD pads via'd; {pour_n} pour-bond vias")

# AMS1117 tab (3V3): >= 2 thermal vias near the tab (canon R6)
u12 = b.FindFootprintByReference("U12")
tab = next(p for p in u12.Pads() if p.GetNumber() == "2" and p.GetDrillSize().x == 0)
tabn = 0
tx, ty = MM(tab.GetPosition().x), MM(tab.GetPosition().y)
# tab pad is 2x3.8mm; vias land inside it (same-net) or just off it
for dx in (0.0, -0.6, 0.6, -1.0, 1.0):
    for dy in (0.0, 1.0, -1.0, 1.5, -1.5, 0.6, -0.6):
        if try_via(tab.GetNet(), tx + dx, ty + dy):
            tabn += 1
        if tabn >= 2:
            break
    if tabn >= 2:
        break
if tabn < 2:
    failures.append(f"U12 tab thermal vias: only {tabn}")

# GND stitch grid over the SELV region (skip NOGO)
grid_n = 0
gnet = b.GetNetInfo().NetsByName()["GND"]
for gx in range(24, 202, 12):
    for gy in range(24, 130, 12):
        if in_nogo(gx, gy, 1.0):
            continue
        if try_via(gnet, gx, gy):
            grid_n += 1
print(f"stitch grid: {grid_n} vias")

if failures:
    print("FAILURES:\n  " + "\n  ".join(failures))
    sys.exit(1)

filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
b.Save(PCB)
print(f"filled {len(list(b.Zones()))} zones; saved")
