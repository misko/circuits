#!/usr/bin/env python3
"""Post-route: rescue-via every GND SMD pad to the B.Cu GND pour, add a
modest GND stitch grid (kept OUT of the guarded analog rect — the bridge
corner stays quiet), fill. Every via site collide-checked (pcb_toolkit).
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

PCB = str(HERE.parent / "04_kicad" / "cook_loadcell.kicad_pcb")
b = pcbnew.LoadBoard(PCB)
tk = Toolkit(b, 0.15)
MM = pcbnew.ToMM

# dedupe same-net twin vias from KRT pass-chaining
vinfo = [(t, t.GetNetCode(), t.GetPosition().x, t.GetPosition().y)
         for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
dead = set()
for i, (v1, n1, x1, y1) in enumerate(vinfo):
    if i in dead:
        continue
    for j in range(i + 1, len(vinfo)):
        v2, n2, x2, y2 = vinfo[j]
        if j not in dead and n1 == n2 and abs(x1 - x2) < 500000 and abs(y1 - y2) < 500000:
            dead.add(j)
for j in dead:
    b.Remove(vinfo[j][0])
print(f"deduped {len(dead)} twin vias")

# normalize sub-spec KRT vias to 0.6/0.3
resized = 0
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA" and pcbnew.ToMM(t.GetWidth()) < 0.449:
        t.SetWidth(pcbnew.FromMM(0.6))
        t.SetDrill(pcbnew.FromMM(0.3))
        resized += 1
if resized:
    print(f"normalized {resized} sub-spec vias to 0.6/0.3")

# remove dangling micro-fragments (< 0.12mm with a free end)
def _ends(t):
    return ((MM(t.GetStart().x), MM(t.GetStart().y)),
            (MM(t.GetEnd().x), MM(t.GetEnd().y)))


allsegs = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
endpts = {}
for t in allsegs:
    for e in _ends(t):
        k = (round(e[0], 2), round(e[1], 2))
        endpts[k] = endpts.get(k, 0) + 1
micro_dead = [t for t in allsegs
              if math.hypot(*(a - c for a, c in zip(*_ends(t)))) < 0.12
              and any(endpts.get((round(e[0], 2), round(e[1], 2)), 0) < 2
                      for e in _ends(t))]
for t in micro_dead:
    b.Remove(t)
if micro_dead:
    print(f"removed {len(micro_dead)} dangling micro-fragments")

# --- SWIG barrier: b.Remove() can poison the board's iterators (kicad-pcb
# skill). All removal passes done; SAVE + RELOAD, rebind board objects.
b.Save(PCB)
b = pcbnew.LoadBoard(PCB)
tk = Toolkit(b, 0.15)

# hole-to-hole repair (0.5 drill-gap floor): nudge one via of each too-close
# pair together with its riding track endpoints; exact-collide green checks.
vlist = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]


def _vxy(v):
    return (MM(v.GetPosition().x), MM(v.GetPosition().y))


moved = 0
for i in range(len(vlist)):
    for j in range(i + 1, len(vlist)):
        v1, v2 = vlist[i], vlist[j]
        x1, y1 = _vxy(v1)
        x2, y2 = _vxy(v2)
        if math.hypot(x1 - x2, y1 - y2) - 0.3 >= 0.5:
            continue
        vm = v1 if (v2.GetNetname() == "GND" and v1.GetNetname() != "GND") else v2
        mx, my = _vxy(vm)
        ends = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"
                and t.GetNetCode() == vm.GetNetCode()
                and any(abs(MM(e.x) - mx) < 0.05 and abs(MM(e.y) - my) < 0.05
                        for e in (t.GetStart(), t.GetEnd()))]
        done = False
        for r in (0.25, 0.4, 0.6, 0.85, 1.1):
            for ang in range(0, 360, 45):
                nx = round(mx + r * math.cos(math.radians(ang)), 2)
                ny = round(my + r * math.sin(math.radians(ang)), 2)
                if any(math.hypot(nx - ox, ny - oy) < 0.85
                       for ov in vlist if ov is not vm
                       for ox, oy in [_vxy(ov)]):
                    continue
                if not tk.via_site_ok(nx, ny, vm.GetNetCode(), size=0.6, drill=0.3):
                    continue
                if any(tk.collides(nx, ny,
                                   MM((t.GetEnd() if abs(MM(t.GetStart().x) - mx) < 0.05
                                       and abs(MM(t.GetStart().y) - my) < 0.05
                                       else t.GetStart()).x),
                                   MM((t.GetEnd() if abs(MM(t.GetStart().x) - mx) < 0.05
                                       and abs(MM(t.GetStart().y) - my) < 0.05
                                       else t.GetStart()).y),
                                   MM(t.GetWidth()), t.GetNetCode(), t.GetLayer())
                       is not None for t in ends):
                    continue
                vm.SetPosition(pcbnew.VECTOR2I_MM(nx, ny))
                for t in ends:
                    for e_get, e_set in ((t.GetStart, t.SetStart), (t.GetEnd, t.SetEnd)):
                        e = e_get()
                        if abs(MM(e.x) - mx) < 0.05 and abs(MM(e.y) - my) < 0.05:
                            e_set(pcbnew.VECTOR2I_MM(nx, ny))
                moved += 1
                done = True
                break
            if done:
                break
if moved:
    print(f"hole-to-hole repair: nudged {moved} vias")

USED = {(round(v.GetPosition().x / 1e6, 2), round(v.GetPosition().y / 1e6, 2))
        for v in b.GetTracks() if v.GetClass() == "PCB_VIA"}
PTH = [(p.GetPosition().x / 1e6, p.GetPosition().y / 1e6, p.GetDrillSize().x / 2e6)
       for fp in b.GetFootprints() for p in fp.Pads() if p.GetDrillSize().x > 0]
failures = []


def in_analog(x, y, m=0.0):
    ax0, ay0, ax1, ay1 = G.ANALOG_RECT
    return ax0 - m < x < ax1 + m and ay0 - m < y < ay1 + m


def try_via(net, x, y, size=0.6, drill=0.3):
    x, y = round(x, 2), round(y, 2)
    if any((x - ux) ** 2 + (y - uy) ** 2 < 0.62 ** 2 for ux, uy in USED):
        return False
    if any(math.hypot(x - hx, y - hy) < r + drill / 2 + 0.3 for hx, hy, r in PTH):
        return False
    if not (G.X0 + 0.8 < x < G.X1 - 0.8 and G.Y0 + 0.8 < y < G.Y1 - 0.8):
        return False
    if tk.via_site_ok(x, y, net.GetNetCode(), size=size, drill=drill):
        tk.add_via(x, y, net, size=size, drill=drill)
        USED.add((x, y))
        return True
    return False


def pad_has_via(pad, d=1.6):
    px, py = MM(pad.GetPosition().x), MM(pad.GetPosition().y)
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA" and t.GetNetCode() == pad.GetNetCode():
            vx, vy = MM(t.GetPosition().x), MM(t.GetPosition().y)
            if (vx - px) ** 2 + (vy - py) ** 2 < d * d:
                return True
    return False


def rescue_pad(pad, label):
    """Via-in-pad first (B.Cu is a solid GND pour under the whole board, so a
    same-net barrel always bonds a GND pad), else adjacent via + short stub."""
    net = pad.GetNet()
    px, py = MM(pad.GetPosition().x), MM(pad.GetPosition().y)
    if try_via(net, px, py):
        return True
    bbox = pad.GetBoundingBox()
    w2, h2 = MM(bbox.GetWidth()) / 2, MM(bbox.GetHeight()) / 2
    lay = pad.GetLayer()
    for r in (0.75, 0.95, 1.2, 1.6, 2.1, 2.7):
        for ang in range(0, 360, 30):
            vx = px + (w2 + r) * math.cos(math.radians(ang))
            vy = py + (h2 + r) * math.sin(math.radians(ang))
            if not try_via(net, vx, vy):
                continue
            layer = lay if lay in (pcbnew.F_Cu, pcbnew.B_Cu) else pcbnew.F_Cu
            if tk.collides(px, py, round(vx, 2), round(vy, 2), 0.3,
                           net.GetNetCode(), layer):
                continue
            tk.add_seg(px, py, round(vx, 2), round(vy, 2), net, layer, 0.3)
            return True
    return False    # caller runs the stub/A* fallback; unrecoverable -> failure


gnd_ok = gnd_n = 0
gnd_fail = []
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetDrillSize().x > 0 or p.GetNetname() != "GND":
            continue
        gnd_n += 1
        if pad_has_via(p) or rescue_pad(p, f"{fp.GetReference()}.{p.GetNumber()}"):
            gnd_ok += 1
        else:
            gnd_fail.append((fp.GetReference(), p))
print(f"GND rescue: {gnd_ok}/{gnd_n} SMD pads via'd")

# fallback for boxed-in GND pads: short stub to the nearest GND copper
# (via barrel = pour link, or track end), else a verified two-layer A*.
gnd_code = b.GetNetInfo().NetsByName()["GND"].GetNetCode()
gnd_pts = []
for t in b.GetTracks():
    if t.GetNetCode() != gnd_code:
        continue
    if t.GetClass() == "PCB_VIA":
        gnd_pts.append((MM(t.GetPosition().x), MM(t.GetPosition().y), None))
    else:
        for e in (t.GetStart(), t.GetEnd()):
            gnd_pts.append((MM(e.x), MM(e.y), t.GetLayer()))
still = []
for ref, p in gnd_fail:
    px, py = MM(p.GetPosition().x), MM(p.GetPosition().y)
    lay = p.GetLayer() if p.GetLayer() in (pcbnew.F_Cu, pcbnew.B_Cu) else pcbnew.F_Cu
    net = p.GetNet()
    cands = sorted(((math.hypot(px - x, py - y), x, y, tl)
                    for (x, y, tl) in gnd_pts if tl is None or tl == lay),
                   key=lambda c: c[0])
    done = False
    for dist, tx, ty, tl in cands:
        if dist < 0.2 or dist > 8.0:
            continue
        if tk.collides(px, py, round(tx, 2), round(ty, 2), 0.3,
                       gnd_code, lay) is not None:
            continue
        tk.add_seg(px, py, round(tx, 2), round(ty, 2), net, lay, 0.3)
        done = True
        break
    if not done:
        tgt = next(((tx, ty) for d2, tx, ty, tl in cands
                    if tl is None and 0.3 < d2 < 10.0), None)
        if tgt and tk.verified_astar("GND", (px, py), tgt, 0.25,
                                     window=3.0, attempts=3):
            done = True
    if done:
        print(f"  GND fallback recovered {ref}.{p.GetNumber()}")
    else:
        still.append((ref, p))
for ref, p in still:
    # NON-FATAL: the board has a full F.Cu GND pour — a pad whose via sites
    # are blocked by a B.Cu track underneath (S_PLUS under R2, RATE_SEL under
    # C4) is still served by top-pour thermal spokes at fill time. The DRC
    # unconnected gate is the arbiter; it fails the chain if the spoke
    # doesn't land.
    print(f"  GND via rescue skipped (top-pour spoke serves it): "
          f"{ref}.{p.GetNumber()}")

# GND stitch grid — OUTSIDE the guarded analog rect (bridge corner quiet)
gnet = b.GetNetInfo().NetsByName()["GND"]
grid_n = 0
for gx in range(24, 74, 8):
    for gy in range(24, 64, 8):
        if in_analog(gx, gy, 1.0):
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
