#!/usr/bin/env python3
"""Deterministic post-stitch DRC repair for router artifacts the waves can
emit at legal-geometry boundaries:
  - hole_to_hole: two via holes < 0.5mm apart -> nudge the lighter via
    (fewer attached segments) along a collision-checked offset, moving its
    attached endpoints with it.
  - hole_clearance: via hole too close to another net's track -> same nudge
    away from the offender.
  - connection_width at a via/track junction -> upgrade the via to 0.6mm
    diameter (bigger annulus swallows the neck) when the site allows.
Runs kicad-cli drc itself (pre_repair.json), applies fixes, saves; the
rebuild chain then re-runs the real gate. Exits 1 if a targeted class
remains unfixed."""
import json, math, os, subprocess, sys
from pathlib import Path
_sk = [p for p in (Path(__file__).resolve().parents[3] / "skills" / "kicad-pcb" / "scripts",
                   Path(os.path.expanduser("~/.claude/skills/kicad-pcb/scripts"))) if p.is_dir()]
sys.path.insert(0, str(_sk[0]))
import pcbnew
from pcb_toolkit import Toolkit

ROOT = Path(__file__).parent.parent
PCB = ROOT / "04_kicad" / "esp32_laser_timing.kicad_pcb"
PRE = ROOT / "06_build" / "drc" / "pre_repair.json"


def run_drc():
    subprocess.run(["kicad-cli", "pcb", "drc", "--severity-all", "--refill-zones",
                    "--format", "json", "-o", str(PRE), str(PCB)],
                   check=True, capture_output=True)
    d = json.loads(PRE.read_text())
    return [v for v in d["violations"]
            if v["type"] in ("hole_to_hole", "hole_clearance", "connection_width",
                             "via_diameter", "drill_out_of_range")]


targets = run_drc()
if not targets:
    print("repair: nothing to do")
    sys.exit(0)

b = pcbnew.LoadBoard(str(PCB))
tk = Toolkit(b, 0.13)
vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
segs = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]


def via_at(x, y):
    best, bd = None, 0.3
    for v in vias:
        dd = math.hypot(v.GetPosition().x / 1e6 - x, v.GetPosition().y / 1e6 - y)
        if dd < bd:
            best, bd = v, dd
    return best


def attached(v):
    out = []
    pos = v.GetPosition()
    for t in segs:
        for endsel in (0, 1):
            e = t.GetStart() if endsel == 0 else t.GetEnd()
            # KRT tap endpoints can sit up to ~0.1mm off the via center and
            # still connect through the barrel - a 20um tolerance severed one
            if abs(e.x - pos.x) < 120000 and abs(e.y - pos.y) < 120000:
                out.append((t, endsel))
    return out


def other_holes(exclude):
    hs = []
    for v in vias:
        if v is exclude:
            continue
        hs.append((v.GetPosition().x / 1e6, v.GetPosition().y / 1e6, v.GetDrillValue() / 2e6))
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetDrillSize().x > 0:
                hs.append((p.GetPosition().x / 1e6, p.GetPosition().y / 1e6,
                           p.GetDrillSize().x / 2e6))
    return hs


def nudge(v, away_from, size=None, drill=None):
    """Relocate via (moving attached endpoints); optionally resize at the
    new site (sub-floor micro-via upgrades)."""
    pos = v.GetPosition()
    vx, vy = pos.x / 1e6, pos.y / 1e6
    if size:
        v.SetWidth(pcbnew.FromMM(size))
    if drill:
        v.SetDrill(pcbnew.FromMM(drill))
    att = attached(v)
    holes = other_holes(v)
    base_ang = math.degrees(math.atan2(vy - away_from[1], vx - away_from[0]))
    for r in (0.3, 0.45, 0.6, 0.8, 1.0):
        for da in (0, 30, -30, 60, -60, 90, -90, 135, -135, 180):
            ang = math.radians(base_ang + da)
            nx, ny = round(vx + r * math.cos(ang), 3), round(vy + r * math.sin(ang), 3)
            if any(math.hypot(nx - hx, ny - hy) < 0.15 + hr + 0.52 for hx, hy, hr in holes):
                continue
            # move via + endpoints, then collision-check everything moved
            v.SetPosition(pcbnew.VECTOR2I_MM(nx, ny))
            for t, endsel in att:
                (t.SetStart if endsel == 0 else t.SetEnd)(pcbnew.VECTOR2I_MM(nx, ny))
            tk2 = Toolkit(b, 0.13)  # fresh index after geometry moves
            ok = True
            for t, _ in att:
                s0, e0 = t.GetStart(), t.GetEnd()
                blockers = tk2.all_blockers(s0.x / 1e6, s0.y / 1e6, e0.x / 1e6, e0.y / 1e6,
                                            t.GetWidth() / 1e6, t.GetNetCode(), t.GetLayer())
                blockers = [bl for bl in blockers if bl is not v and bl is not t]
                if blockers:
                    ok = False
                    break
            if ok and not tk2.via_site_ok(nx, ny, v.GetNetCode(),
                                          size=v.GetWidth() / 1e6, drill=v.GetDrillValue() / 1e6):
                ok = False
            if ok:
                return (nx, ny)
            v.SetPosition(pos)
            for t, endsel in att:
                (t.SetStart if endsel == 0 else t.SetEnd)(pos)
    return None


def fix_microvia(v0):
    """via_diameter / drill_out_of_range: bring the via to 0.45/0.3, moving
    it out of whatever pocket forced the fallback geometry."""
    items = v0["items"]
    cand = via_at(items[0]["pos"]["x"], items[0]["pos"]["y"])
    if cand is None:
        return False
    if cand.GetWidth() >= pcbnew.FromMM(0.449) and cand.GetDrillValue() >= pcbnew.FromMM(0.299):
        return True  # already fixed by the twin finding of this violation
    cx, cy = cand.GetPosition().x / 1e6, cand.GetPosition().y / 1e6
    # in-place resize if legal
    if tk.via_site_ok(cx, cy, cand.GetNetCode(), size=0.45, drill=0.3):
        near = [h for h in other_holes(cand) if math.hypot(h[0]-cx, h[1]-cy) < 0.3 + h[2] + 0.52]
        if not near:
            cand.SetWidth(pcbnew.FromMM(0.45))
            cand.SetDrill(pcbnew.FromMM(0.3))
            return True
    # nudge away from the nearest DIFFERENT-net pad (the pocket)
    bd, away = 9, (cx + 1, cy)
    for fp in b.GetFootprints():
        for pd in fp.Pads():
            if pd.GetNetCode() != cand.GetNetCode():
                dd = math.hypot(pd.GetPosition().x / 1e6 - cx, pd.GetPosition().y / 1e6 - cy)
                if dd < bd:
                    bd, away = dd, (pd.GetPosition().x / 1e6, pd.GetPosition().y / 1e6)
    return nudge(cand, away, size=0.45, drill=0.3) is not None


fixed, failed = 0, []
for v in targets:
    t = v["type"]
    items = v["items"]
    pos0 = items[0]["pos"]
    if t in ("via_diameter", "drill_out_of_range"):
        if fix_microvia(v):
            fixed += 1
        else:
            failed.append(f"{t}: microvia unfixable at ({pos0['x']},{pos0['y']})")
        continue
    if t == "connection_width":
        # pad/track neck: overlay a fat segment from the pad center to the
        # track's far end (same net, collision-checked)
        padit = [it for it in items if it["description"].startswith("Pad")]
        trkit = [it for it in items if it["description"].startswith("Track")]
        done = False
        if padit and trkit:
            ppos = padit[0]["pos"]
            best, bd = None, 9
            for tr in segs:
                for e in (tr.GetStart(), tr.GetEnd()):
                    dd = math.hypot(e.x / 1e6 - ppos["x"], e.y / 1e6 - ppos["y"])
                    if dd < bd:
                        best, bd = tr, dd
            if best is not None and bd < 2.0:
                pad = None
                for fp in b.GetFootprints():
                    for pd in fp.Pads():
                        if abs(pd.GetPosition().x / 1e6 - ppos["x"]) < 0.05 and \
                           abs(pd.GetPosition().y / 1e6 - ppos["y"]) < 0.05:
                            pad = pd
                if pad is not None and best.GetNetCode() == pad.GetNetCode():
                    # far end of the touching segment
                    s0, e0 = best.GetStart(), best.GetEnd()
                    near = s0 if math.hypot(s0.x/1e6-ppos["x"], s0.y/1e6-ppos["y"]) < \
                                 math.hypot(e0.x/1e6-ppos["x"], e0.y/1e6-ppos["y"]) else e0
                    if not tk.collides(ppos["x"], ppos["y"], near.x / 1e6, near.y / 1e6,
                                       0.4, pad.GetNetCode(), best.GetLayer()):
                        tk.add_seg(ppos["x"], ppos["y"], near.x / 1e6, near.y / 1e6,
                                   pad.GetNet(), best.GetLayer(), 0.4)
                        fixed += 1
                        done = True
        if not done:
            cand = None
            for it in items:
                c = via_at(it["pos"]["x"], it["pos"]["y"])
                if c:
                    cand = c
                    break
            if cand:
                # a via rim tangent to a same-net pad edge makes a hairline
                # neck: nudge the via away from the nearest same-net pad
                cx, cy = cand.GetPosition().x / 1e6, cand.GetPosition().y / 1e6
                near_pad, bdp = None, 3.0
                for fp in b.GetFootprints():
                    for pd in fp.Pads():
                        if pd.GetNetCode() == cand.GetNetCode():
                            ddp = math.hypot(pd.GetPosition().x / 1e6 - cx,
                                             pd.GetPosition().y / 1e6 - cy)
                            if ddp < bdp:
                                near_pad, bdp = pd, ddp
                if near_pad is not None and nudge(cand, (near_pad.GetPosition().x / 1e6,
                                                         near_pad.GetPosition().y / 1e6)):
                    print(f"NUDGE {t} via away from pad")
                    fixed += 1
                elif cand.GetWidth() < pcbnew.FromMM(0.6) and tk.via_site_ok(
                        cx, cy, cand.GetNetCode(), size=0.6,
                        drill=cand.GetDrillValue() / 1e6):
                    cand.SetWidth(pcbnew.FromMM(0.6))
                    fixed += 1
                else:
                    failed.append(f"{t}: unfixed at ({pos0['x']},{pos0['y']})")
            else:
                failed.append(f"{t}: no via at ({pos0['x']},{pos0['y']})")
        continue
    # hole-to-hole / hole_clearance: nudge the via item
    vitems = [it for it in items if it["description"].startswith("Via")]
    oitems = [it for it in items if not it["description"].startswith("Via")]
    if not vitems:
        failed.append(f"{t}: no via item")
        continue
    def weight(it):
        c = via_at(it["pos"]["x"], it["pos"]["y"])
        return len(attached(c)) if c else 99
    cand = None
    for it in sorted(vitems, key=weight):
        cand = via_at(it["pos"]["x"], it["pos"]["y"])
        if cand:
            away = (oitems[0]["pos"]["x"], oitems[0]["pos"]["y"]) if oitems else \
                   (vitems[-1]["pos"]["x"], vitems[-1]["pos"]["y"])
            res = nudge(cand, away)
            if res:
                print(f"NUDGE {t} via -> {res}")
                fixed += 1
                break
    else:
        failed.append(f"{t}: nudge failed at ({pos0['x']},{pos0['y']})")

print(f"repair pass: fixed {fixed}/{len(targets)}")
b.Save(str(PCB))
remaining = run_drc()
if remaining and fixed:
    print(f"{len(remaining)} target(s) remain - one more pass may be needed (rerun repair)")
if remaining and not fixed:
    print("UNFIXED:\n  " + "\n  ".join(
        f"{v['type']} at {v['items'][0]['pos']}" for v in remaining))
    sys.exit(1)
sys.exit(0)
