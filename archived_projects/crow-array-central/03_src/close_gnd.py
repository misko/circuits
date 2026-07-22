#!/usr/bin/env python3
"""DRC-GUARDED close of any GND items left unconnected after gnd_rescue.

The F.Cu GND pour is fragmented by the dense top-layer routing, so its
connectivity is UNSTABLE: a via added to bond one boxed pad can re-flow the
fill and disconnect others (observed live: one via took unconnected 4 -> 15).
So every candidate edit here is applied to a throwaway copy, refilled, and
DRC'd; it is kept ONLY if the TOTAL unconnected count strictly decreases,
else reverted. Runs AFTER gnd_rescue, BEFORE clearance_nudge.

Per remaining unconnected GND item, candidate edits are tried in reliability
order: on-pad-edge via; via anywhere on the item's F.Cu escape chain; extend
the chain's open tip to a via site (stub+via); a new short F.Cu stub from a
pad to a via site; joinpath to the nearest existing GND via; a via inside the
unbonded F.Cu fill island (zone items); a nearby pour-seed via. First edit
that strictly reduces unconnected wins. One stuck item never blocks others.
"""
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, os.path.expanduser("~/.claude/skills/kicad-pcb/scripts"))
import pcbnew
from pcb_toolkit import Toolkit

PCB = str(Path(__file__).parent.parent / "04_kicad" / "crow_array_central.kicad_pcb")
TMP = "/tmp/_close_gnd.kicad_pcb"
NM = 1e6
LAY = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.In3_Cu, pcbnew.In4_Cu, pcbnew.B_Cu)


def drc(path):
    out = Path("/tmp/_cg_drc.json")
    subprocess.run(["kicad-cli", "pcb", "drc", "--severity-all", "--refill-zones",
                    "--format", "json", "-o", str(out), path],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return json.load(open(out))


def unconn_items(d):
    return d["unconnected_items"]


def gnd_items(d):
    out = []
    for v in d["unconnected_items"]:
        its = v.get("items", [])
        if any("[GND]" in it.get("description", "") for it in its):
            out.append(its)
    return out


def sig(its):
    return tuple(sorted((it.get("description", "")[:20],
                         round(it.get("pos", {}).get("x") or 0, 2),
                         round(it.get("pos", {}).get("y") or 0, 2)) for it in its))


def mk(b):
    tk = Toolkit(b, 0.1)
    av = [(v.GetPosition().x / NM, v.GetPosition().y / NM, v.GetDrillValue() / 2 / NM)
          for v in b.GetTracks() if v.GetClass() == "PCB_VIA"]
    return tk, av


def h2h(av, x, y):
    return all((x - vx) ** 2 + (y - vy) ** 2 >= (0.2 + 0.075 + vr) ** 2 for vx, vy, vr in av)


def vok(tk, av, x, y, gnc):
    return (11.2 < x < 184.8 and 11.2 < y < 130.8 and h2h(av, x, y)
            and tk.via_site_ok(x, y, gnc, size=0.30, drill=0.15,
                               hole_to_copper=0.205, layers=LAY))


def _near(ax, ay, bx, by, t=0.02):
    return abs(ax - bx) < t and abs(ay - by) < t


def _pt_seg(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    u = 0 if L2 == 0 else max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / L2))
    return math.hypot(px - x1 - u * dx, py - y1 - u * dy)


def seg_holes_ok(av, x1, y1, x2, y2, w=0.2):
    """Every via DRILL must keep >=0.2mm to this segment's copper (the DRU
    hole_clearance floor tk.collides does NOT enforce for via barrels). Vias
    coincident with an endpoint are the intended same-net connection -> skip."""
    for vx, vy, vr in av:
        if _near(vx, vy, x1, y1, 0.05) or _near(vx, vy, x2, y2, 0.05):
            continue
        if _pt_seg(vx, vy, x1, y1, x2, y2) < vr + 0.2 + w / 2 - 1e-6:
            return False
    return True


def chain(b, gnc, sx, sy):
    ft = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"
          and t.GetNetCode() == gnc and t.GetLayer() == pcbnew.F_Cu]
    if not ft:
        return [], (sx, sy)
    seed = min(ft, key=lambda t: min(
        (t.GetStart().x / NM - sx) ** 2 + (t.GetStart().y / NM - sy) ** 2,
        (t.GetEnd().x / NM - sx) ** 2 + (t.GetEnd().y / NM - sy) ** 2))
    ids, ch, fr = {id(seed)}, [seed], [seed]
    while fr:
        cur = fr.pop()
        for pt in (cur.GetStart(), cur.GetEnd()):
            px, py = pt.x / NM, pt.y / NM
            for t in ft:
                if id(t) in ids:
                    continue
                if (_near(t.GetStart().x / NM, t.GetStart().y / NM, px, py)
                        or _near(t.GetEnd().x / NM, t.GetEnd().y / NM, px, py)):
                    ids.add(id(t)); ch.append(t); fr.append(t)
    pts, ends = [], {}
    for t in ch:
        ax, ay = t.GetStart().x / NM, t.GetStart().y / NM
        bx, by = t.GetEnd().x / NM, t.GetEnd().y / NM
        n = max(2, int(math.hypot(bx - ax, by - ay) / 0.1))
        for i in range(n + 1):
            f = i / n
            pts.append((round(ax + (bx - ax) * f, 3), round(ay + (by - ay) * f, 3)))
        for e in ((round(ax, 2), round(ay, 2)), (round(bx, 2), round(by, 2))):
            ends[e] = ends.get(e, 0) + 1

    def on_pad(ex, ey):
        vv = pcbnew.VECTOR2I(int(ex * NM), int(ey * NM))
        return any(p.GetNetCode() == gnc and p.HitTest(vv, 0)
                   for fp in b.GetFootprints() for p in fp.Pads())
    singles = [e for e, c in ends.items() if c == 1]
    opens = [e for e in singles if not on_pad(*e)]
    tip = (opens or singles or [(sx, sy)])[0]
    return pts, tip


# ---- candidate generators: each returns a callable edit(b, tk, av, gnd)->label|None
def candidates_for(its):
    """Yield (kind, seedpoint, pad_ref/None) descriptors to build edits from."""
    cs = []
    for it in its:
        desc, p = it.get("description", ""), it.get("pos", {})
        x, y = p.get("x"), p.get("y")
        if x is None:
            continue
        if desc.startswith("Pad ") and " of " in desc:
            ref = desc.split(" of ", 1)[1].split(" on ", 1)[0].strip()
            cs.append(("pad", x, y, ref))
        elif desc.startswith("Track [GND]"):
            cs.append(("track", x, y, None))
        elif desc.startswith("Via [GND]"):
            cs.append(("track", x, y, None))
        elif desc.startswith("Zone [GND]"):
            cs.append(("zone", x, y, None))
    return cs


def try_edits(kind, sx, sy, ref):
    """Return an ordered list of edit(b,tk,av,gnd)->label functions."""
    edits = []

    def pad_via(b, tk, av, gnd):
        for fp in b.GetFootprints():
            if fp.GetReference() != ref:
                continue
            for p in fp.Pads():
                if p.GetNetname() != "GND":
                    continue
                px, py = p.GetPosition().x / NM, p.GetPosition().y / NM
                hw, hh = p.GetSize().x / 2 / NM, p.GetSize().y / 2 / NM
                fc = fp.GetPosition()
                ox, oy = px - fc.x / NM, py - fc.y / NM
                Ln = math.hypot(ox, oy) or 1.0
                ox, oy = ox / Ln, oy / Ln
                for f in (1.0, 0.7, 0.4, 0.0):
                    x = round(px + ox * (hw - 0.05) * f, 3)
                    y = round(py + oy * (hh - 0.05) * f, 3)
                    if vok(tk, av, x, y, gnd.GetNetCode()):
                        tk.add_via(x, y, gnd, size=0.30, drill=0.15)
                        return f"{ref} on-pad-via@({x},{y})"
        return None

    def chain_via(b, tk, av, gnd):
        gnc = gnd.GetNetCode()
        pts, tip = chain(b, gnc, sx, sy)
        pts.sort(key=lambda q: -((q[0] - sx) ** 2 + (q[1] - sy) ** 2))
        for (x, y) in pts:
            if vok(tk, av, x, y, gnc):
                tk.add_via(x, y, gnd, size=0.30, drill=0.15)
                return f"chain-via@({x},{y})"
        return None

    def extend_tip(b, tk, av, gnd):
        gnc = gnd.GetNetCode()
        _, (lx, ly) = chain(b, gnc, sx, sy)
        r = 0.15
        while r <= 2.6:
            for a in range(0, 360, 6):
                x = round(lx + r * math.cos(math.radians(a)), 3)
                y = round(ly + r * math.sin(math.radians(a)), 3)
                if not vok(tk, av, x, y, gnc):
                    continue
                if (tk.collides(lx, ly, x, y, 0.2, gnc, pcbnew.F_Cu, clr=0.1) is None
                        and seg_holes_ok(av, lx, ly, x, y)):
                    tk.add_seg(lx, ly, x, y, gnd, pcbnew.F_Cu, 0.2)
                    tk.add_via(x, y, gnd, size=0.30, drill=0.15)
                    return f"extend-tip({lx},{ly})->via@({x},{y})"
            r += 0.05
        return None

    def new_stub(b, tk, av, gnd):
        if ref is None:
            return None
        gnc = gnd.GetNetCode()
        for fp in b.GetFootprints():
            if fp.GetReference() != ref:
                continue
            for p in fp.Pads():
                if p.GetNetname() != "GND":
                    continue
                px, py = p.GetPosition().x / NM, p.GetPosition().y / NM
                r = 0.3
                while r <= 2.6:
                    for a in range(0, 360, 6):
                        x = round(px + r * math.cos(math.radians(a)), 3)
                        y = round(py + r * math.sin(math.radians(a)), 3)
                        if not vok(tk, av, x, y, gnc):
                            continue
                        if (tk.collides(px, py, x, y, 0.2, gnc, pcbnew.F_Cu, clr=0.1) is None
                                and seg_holes_ok(av, px, py, x, y)):
                            tk.add_seg(px, py, x, y, gnd, pcbnew.F_Cu, 0.2)
                            tk.add_via(x, y, gnd, size=0.30, drill=0.15)
                            return f"{ref} new-stub->via@({x},{y})"
                    r += 0.05
        return None

    def join_via(b, tk, av, gnd):
        gnc = gnd.GetNetCode()
        _, (lx, ly) = chain(b, gnc, sx, sy)
        gv = sorted(av, key=lambda q: (q[0] - lx) ** 2 + (q[1] - ly) ** 2)
        for (vx, vy, _) in gv[:15]:
            if math.hypot(vx - lx, vy - ly) < 0.35:
                continue
            w = tk.joinpath("GND", (lx, ly), (vx, vy), 0.2, layer=pcbnew.F_Cu)
            if w:
                return f"joinpath({lx},{ly})->gndvia({vx:.2f},{vy:.2f})"
        return None

    def island_via(b, tk, av, gnd):
        gnc = gnd.GetNetCode()
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        vpos = [pcbnew.VECTOR2I(int(vx * NM), int(vy * NM)) for vx, vy, _ in av]
        seedv = pcbnew.VECTOR2I(int(sx * NM), int(sy * NM))
        for z in b.Zones():
            if z.GetIsRuleArea() or z.GetNetname() != "GND" or not z.IsOnLayer(pcbnew.F_Cu):
                continue
            polys = z.GetFilledPolysList(pcbnew.F_Cu)
            for i in range(polys.OutlineCount()):
                o = polys.Outline(i)
                # island that contains this item's seed OR has no via
                has_seed = o.PointInside(seedv)
                has_via = any(o.PointInside(p) for p in vpos)
                if has_via and not has_seed:
                    continue
                bb = o.BBox()
                for fx in range(1, 20):
                    for fy in range(1, 20):
                        x = (bb.GetLeft() + bb.GetWidth() * fx // 20) / NM
                        y = (bb.GetTop() + bb.GetHeight() * fy // 20) / NM
                        v = pcbnew.VECTOR2I(int(x * NM), int(y * NM))
                        if not o.PointInside(v):
                            continue
                        if vok(tk, av, round(x, 3), round(y, 3), gnc):
                            tk.add_via(round(x, 3), round(y, 3), gnd, size=0.30, drill=0.15)
                            return f"island-via@({round(x,3)},{round(y,3)})"
        return None

    def pourseed(b, tk, av, gnd):
        gnc = gnd.GetNetCode()
        r = 0.3
        while r <= 2.2:
            for a in range(0, 360, 10):
                x = round(sx + r * math.cos(math.radians(a)), 3)
                y = round(sy + r * math.sin(math.radians(a)), 3)
                if vok(tk, av, x, y, gnc):
                    tk.add_via(x, y, gnd, size=0.30, drill=0.15)
                    return f"pourseed-via@({x},{y})"
            r += 0.05
        return None

    if kind == "pad":
        edits = [pad_via, chain_via, extend_tip, new_stub, join_via, pourseed, island_via]
    elif kind == "track":
        edits = [chain_via, extend_tip, join_via, new_stub, pourseed, island_via]
    else:  # zone
        edits = [island_via, chain_via, extend_tip, pourseed]
    return edits


def apply_guarded(edit_fn, allow_equal_unconn=False):
    """Apply edit IN PLACE on the real PCB (so DRC sees the project's .kicad_pro
    / .kicad_dru rules — a /tmp copy would DRC with defaults and mis-count
    violations); keep only if unconnected strictly drops (or stays equal when
    allow_equal_unconn) AND violations do not rise, else restore the backup."""
    d = drc(PCB)
    base_u, base_v = len(unconn_items(d)), len(d["violations"])
    b = pcbnew.LoadBoard(PCB)
    tk, av = mk(b)
    gnd = b.FindNet("GND")
    label = edit_fn(b, tk, av, gnd)
    if not label:
        return None
    def hard(dd):   # real errors only (exclude track_dangling warnings)
        return sum(1 for v in dd["violations"] if v["type"] != "track_dangling")
    base_h = hard(d)
    shutil.copy(PCB, TMP)          # backup
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.Save(PCB)
    dt = drc(PCB)
    after_u, after_v, after_h = len(unconn_items(dt)), len(dt["violations"]), hard(dt)
    ok_u = after_u < base_u or (allow_equal_unconn and after_u == base_u)
    # never trade a dangling warning for a real error; total must not rise
    if ok_u and after_h <= base_h and after_v <= base_v:
        return f"{label}  [u {base_u}->{after_u}, v {base_v}->{after_v}]"
    shutil.copy(TMP, PCB)          # restore
    return None


def fix_u3_gnd(b, tk, av, gnd):
    """ROOT-CAUSE for the U3.7 (PCM1865 pin-7) GND escape that no via can
    reach: a 21mm I2C_SCL trace on In3.Cu runs along y=61.5 directly under
    the whole U3 west GND row, walling every layer at that y. Jog that In3
    trace SOUTH to y=62.3 between x=116.5..119.5 (In3 verified clear there),
    which frees a via site on U3.7's own F.Cu escape stub; drop a 0.30/0.15
    GND via there -> pad->stub->via->In1/In4 plane, pour-independent. Also
    resolves the F.Cu<->In1 zone-island mismatch (that island gets a plane
    tie). Coords are placement-frozen (promoted route)."""
    gnc = gnd.GetNetCode()
    scl = b.FindNet("I2C_SCL")
    # find the long In3 I2C_SCL horizontal at y=61.5
    seg = None
    for t in b.GetTracks():
        if (t.GetClass() == "PCB_TRACK" and t.GetNetname() == "I2C_SCL"
                and t.GetLayer() == pcbnew.In3_Cu
                and abs(t.GetStart().y / NM - 61.5) < 0.05
                and abs(t.GetEnd().y / NM - 61.5) < 0.05
                and abs(t.GetStart().x / NM - t.GetEnd().x / NM) > 5.0):
            seg = t
    if seg is None:
        return None
    ax, ay = seg.GetStart().x / NM, seg.GetStart().y / NM
    bx, by = seg.GetEnd().x / NM, seg.GetEnd().y / NM
    xe, xw = max(ax, bx), min(ax, bx)   # east, west ends
    JW, JE, JY = 116.5, 119.5, 62.3     # jog window + depth
    w = seg.GetWidth() / NM
    jog = [(xe, 61.5, JE, 61.5), (JE, 61.5, JE, JY), (JE, JY, JW, JY),
           (JW, JY, JW, 61.5), (JW, 61.5, xw, 61.5)]
    for (x1, y1, x2, y2) in jog:
        if tk.collides(x1, y1, x2, y2, w, scl.GetNetCode(), pcbnew.In3_Cu, clr=0.1):
            return None
    b.Remove(seg)
    for (x1, y1, x2, y2) in jog:
        tk.add_seg(x1, y1, x2, y2, scl, pcbnew.In3_Cu, w)
    # via on U3.7's F.Cu escape stub (y=61.5), now that In3 is clear
    for x in (118.0, 118.05, 117.95, 118.1, 117.9, 118.15):
        if vok(tk, av, x, 61.5, gnc):
            tk.add_via(x, 61.5, gnd, size=0.30, drill=0.15)
            return f"I2C_SCL In3 jog + U3.7 GND via@({x},61.5)"
    return None


d0 = drc(PCB)
u0 = len(unconn_items(d0))
print(f"close_gnd start: unconnected={u0}")

# ROOT-CAUSE special case FIRST (the U3.7 escape the generic search can't
# reach without a local reroute of the I2C_SCL In3 wall).
if any(abs((it.get("pos", {}).get("x") or 0) - 119.1375) < 0.1
       and abs((it.get("pos", {}).get("y") or 0) - 61.5) < 0.1
       for its in gnd_items(d0) for it in its):
    r = apply_guarded(fix_u3_gnd)
    print(f"  U3.7 root-cause fix: {r}")

skip = set()
progress = True
rounds = 0
while progress and rounds < 20:
    rounds += 1
    progress = False
    d = drc(PCB)
    if len(unconn_items(d)) == 0:
        break
    for its in gnd_items(d):
        s = sig(its)
        if s in skip:
            continue
        cand = candidates_for(its)
        done = None
        for (kind, sx, sy, ref) in cand:
            for edit_fn in try_edits(kind, sx, sy, ref):
                res = apply_guarded(edit_fn)
                if res:
                    print(f"  closed {kind}@({sx},{sy}): {res}")
                    done = res
                    break
            if done:
                break
        if done:
            progress = True
            break  # re-read DRC (pour re-flow) before next item
        else:
            skip.add(s)

d1 = drc(PCB)
print(f"close_gnd end: unconnected {u0} -> {len(unconn_items(d1))}; "
      f"violations {len(d0['violations'])} -> {len(d1['violations'])}")
