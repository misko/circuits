#!/usr/bin/env python3
"""Post-route stitch + fill for crow-array-central (4-layer).

Stackup: F.Cu / In1.Cu SOLID GND (the reference plane) / In2.Cu / B.Cu,
all four carrying a GND zone (In1 full-connect plane; F/In2/B thermal
pours). This step:
  - width-floor backstop (dru gotcha: exact-nm compare) on power nets,
  - twin-via dedupe + micro-stub cleanup (pass chaining artifacts),
  - GND stitch grid (bonds all four GND planes/pours),
  - GND pad-service vias (every GND SMD pad gets a via to the planes),
  - via janitor (drop vias with same-net copper on <2 layers),
  - zone fill + pad-bearing GND-island rescue + dangling-via cleanup.
Every via site is exact-collide checked (pcb_toolkit); FAILS before save
if a mandatory step comes up short. Adapted from the crow-array-pod
stitcher (2L) to 4L with a solid inner GND plane.
"""
import math
import os
import sys
from pathlib import Path
_sk = [p for p in (Path(__file__).resolve().parents[3] / "skills" / "kicad-pcb" / "scripts",
                   Path(os.path.expanduser("~/.claude/skills/kicad-pcb/scripts"))) if p.is_dir()]
sys.path.insert(0, str(_sk[0]))
import pcbnew
from pcb_toolkit import Toolkit

PCB = str(Path(__file__).parent.parent / "04_kicad" / "crow_array_central.kicad_pcb")
b = pcbnew.LoadBoard(PCB)
tk = Toolkit(b, 0.15)

X0, Y0, X1, Y1 = 10.0, 10.0, 186.0, 132.0
failures = []

# SHT40 (U6) ships a track/via keepout over its own I2C/3V3 pad approaches —
# strip those flags (keep it a copper-pour keepout) so the sensor's own
# connections don't fire items_not_allowed. Matches route_prep.
for f in b.GetFootprints():
    if f.GetReference() == "U6":
        for z in f.Zones():
            if z.GetIsRuleArea():
                z.SetDoNotAllowTracks(False)
                z.SetDoNotAllowVias(False)

# pre-pass: dedupe same-net twin vias from pass chaining
vinfo = [(t, t.GetNetCode(), t.GetPosition().x, t.GetPosition().y)
         for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
dead = set()
for i, (v1, n1, x1, y1) in enumerate(vinfo):
    if i in dead:
        continue
    for j in range(i + 1, len(vinfo)):
        v2, n2, x2, y2 = vinfo[j]
        if j not in dead and n1 == n2 and abs(x1 - x2) < 300000 and abs(y1 - y2) < 300000:
            dead.add(j)
for j in dead:
    b.Remove(vinfo[j][0])
print(f"deduped {len(dead)} twin vias")

# remove only TRULY degenerate (near-zero-length) segments. A 0.05mm
# threshold deletes real fanout-stub bend segments and disconnects XU316
# escapes — use 0.002mm so only point-tracks go.
stubs = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"
         and math.hypot(t.GetEnd().x - t.GetStart().x, t.GetEnd().y - t.GetStart().y) < 2000]
for t in stubs:
    b.Remove(t)
print(f"removed {len(stubs)} degenerate point-tracks (<0.002mm)")

# remove DANGLING track stubs (KRT rip-up leftovers): a track whose one end
# touches NO pad, NO via and NO other same-net track endpoint is loose copper
# (track_dangling). Iterate — removing one can expose the next.
def _endpoint_connected(b, tr, pt):
    px, py = pt.x, pt.y
    nc = tr.GetNetCode()
    for t in b.GetTracks():
        if t is tr or t.GetNetCode() != nc:
            continue
        if t.GetClass() == "PCB_VIA":
            if abs(t.GetPosition().x - px) < 30000 and abs(t.GetPosition().y - py) < 30000:
                return True
        else:
            for q in (t.GetStart(), t.GetEnd()):
                if abs(q.x - px) < 30000 and abs(q.y - py) < 30000:
                    return True
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetCode() == nc and p.HitTest(pcbnew.VECTOR2I(px, py), 0):
                return True
    return False


dang_total = 0
for _ in range(6):
    dang = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"
            and (not _endpoint_connected(b, t, t.GetStart())
                 or not _endpoint_connected(b, t, t.GetEnd()))]
    if not dang:
        break
    for t in dang:
        b.Remove(t)
    dang_total += len(dang)
print(f"removed {dang_total} dangling track stubs")

# pre-pass: lift sub-floor power segments to their class floors (dru backstop)
FLOOR = {"5V": 0.5, "5V_P": 0.5, "5V_IN": 0.5,
         "3V3": 0.4, "0V9": 0.4, "1V8": 0.4, "3V3A": 0.2,
         "BK1_SW": 0.4, "BK2_SW": 0.4}
FLOOR.update({f"BEEP_5V{n}": 0.4 for n in range(1, 9)})
FLOOR.update({f"BEEP_RET{n}": 0.4 for n in range(1, 9)})
FLOOR.update({f"5V_AUD{n}": 0.4 for n in range(1, 9)})
# xu316_taps rule area (matches generate_board): power taps here keep their
# thin escape width — widening them to 0.4mm at the 0.4mm pin pitch shorts
# adjacent rail stubs into each other (the dru grants 0.15mm here).
TAPX0, TAPY0, TAPX1, TAPY1 = 84.0, 84.0, 116.0, 116.0


def _in_taps(tr):
    mx = (tr.GetStart().x + tr.GetEnd().x) / 2e6
    my = (tr.GetStart().y + tr.GetEnd().y) / 2e6
    return TAPX0 < mx < TAPX1 and TAPY0 < my < TAPY1


# 'pwr_neck' rule areas (D25, neck_approaches.py): DRC-guarded necks at
# unroutable approaches. The lift pass must NOT re-widen them (it did — the
# rebuild of the promoted board re-inflated every neck back into its
# clearance violation and neck_approaches had to redo all 18).
_neck_zones = [z for z in b.Zones()
               if z.GetIsRuleArea() and z.GetZoneName() == "pwr_neck"]


def _in_neck(tr):
    for pt in (tr.GetStart(), tr.GetEnd(),
               pcbnew.VECTOR2I((tr.GetStart().x + tr.GetEnd().x) // 2,
                               (tr.GetStart().y + tr.GetEnd().y) // 2)):
        for z in _neck_zones:
            if z.Outline().Collide(pt, 0):
                return True
    return False


lifted = 0
for tr in b.GetTracks():
    if tr.GetClass() != "PCB_TRACK":
        continue
    fl = FLOOR.get(tr.GetNetname())
    if (fl and tr.GetWidth() < int(fl * 1e6) and not _in_taps(tr)
            and not _in_neck(tr)):
        tr.SetWidth(int(fl * 1e6))  # EXACT nm compare (dru gotcha)
        lifted += 1
print(f"lifted {lifted} power segments to class floor (tap+neck areas exempt)")

# pre-pass: normalize sub-floor vias to the JLC 6L SMALL-VIA floor 0.30/0.15
# (ADR-0009). The 0.4mm-pitch XU316 via-in-pad escapes cannot use 0.45/0.30
# standard-tier vias (0.45 copper shorts the adjacent TDO/TDI pair 0.4mm apart
# and the 0.30 drill encroaches neighbour pads). 0.30dia keeps a 0.10mm copper
# gap at 0.4mm pitch and 0.075mm annular on a 0.15 drill; the escape rides the
# JLC small-via option (invoked by the 0.25-drill DRU floor). Only enlarge
# what is smaller; the 0.6/0.3 grid + service vias are untouched.
norm = 0
for v in b.GetTracks():
    if v.GetClass() != "PCB_VIA":
        continue
    changed = False
    if v.GetWidth() < int(0.30e6):
        v.SetWidth(int(0.30e6))
        changed = True
    if v.GetDrillValue() < int(0.15e6):
        v.SetDrill(int(0.15e6))
        changed = True
    norm += changed
print(f"normalized {norm} sub-floor vias to 0.30/0.15 (small-via floor)")

USED = {(v.GetPosition().x / 1e6, v.GetPosition().y / 1e6)
        for v in b.GetTracks() if v.GetClass() == "PCB_VIA"}
PTH = [(p.GetPosition().x / 1e6, p.GetPosition().y / 1e6, p.GetDrillSize().x / 2e6)
       for fp in b.GetFootprints() for p in fp.Pads() if p.GetDrillSize().x > 0]
# footprint via-keepout boxes (e.g. SHT40 U6 central keepout): no stitch via
KEEPOUT = []
for fp in b.GetFootprints():
    for z in fp.Zones():
        if z.GetIsRuleArea() and z.GetDoNotAllowVias():
            bb = z.GetBoundingBox()
            KEEPOUT.append((bb.GetLeft() / 1e6, bb.GetTop() / 1e6,
                            bb.GetRight() / 1e6, bb.GetBottom() / 1e6))


def try_via(net, x, y, size=0.6, drill=0.3):
    if not (X0 + 1.2 < x < X1 - 1.2 and Y0 + 1.2 < y < Y1 - 1.2):
        return False
    # 0.85mm min via-centre spacing -> 0.55mm hole-to-hole > the 0.5mm floor
    if any((x - ux) ** 2 + (y - uy) ** 2 < 0.85 ** 2 for ux, uy in USED):
        return False
    if any(math.hypot(x - hx, y - hy) < r + drill / 2 + 0.75 for hx, hy, r in PTH):
        return False
    if any(kl - 0.3 < x < kr + 0.3 and kt - 0.3 < y < kb + 0.3
           for kl, kt, kr, kb in KEEPOUT):
        return False
    # check ALL 6 copper layers (ADR-0008), not the toolkit default (F,B):
    # a through via passes In1/In4 (solid GND, same-net skip) + In2/In3
    # (signal) — miss an inner signal layer and stitch vias short its tracks.
    if tk.via_site_ok(x, y, net.GetNetCode(), size=size, drill=drill,
                      layers=(pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu,
                              pcbnew.In3_Cu, pcbnew.In4_Cu, pcbnew.B_Cu)):
        tk.add_via(x, y, net, size=size, drill=drill)
        USED.add((x, y))
        return True
    return False


def _in_poly(x, y, poly):
    inside = False
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


gnd = b.FindNet("GND")

# XU316 distributed-power-pin taps: routed thin (0.15mm) inside the
# xu316_taps rule area (D19 exemption) directly by KRT — no rail pour
# patch needed. GND handled by the planes + pours + stitch below.

# ---- GND stitching grid (bonds F/In1/In2/B GND planes)
g = sum(try_via(gnd, float(gx), float(gy))
        for gx in range(14, 184, 7) for gy in range(14, 112, 7))
# IDEMPOTENCY (canon M3 promoted-artifact re-run): on an already-stitched
# board the grid pass correctly adds ~0 NEW vias, so the density gate must
# count TOTAL GND vias present, not this run's additions (the added-count
# check false-failed the rebuild of the promoted final.kicad_pcb).
g_total = sum(1 for t in b.GetTracks()
              if t.GetClass() == "PCB_VIA" and t.GetNetname() == "GND")
print(f"GND grid: {g} vias added, {g_total} total GND vias")
if g_total < 120:
    failures.append(f"GND grid too sparse: {g_total} total")

# ---- GND pad service: bond every GND SMD pad DIRECTLY to the In1 plane
# with a via that OVERLAPS the pad copper (same-net, so via_site_ok allows
# it). A via merely "near" the pad only bonds the POUR — if the pour is
# fragmented and doesn't thermal-reach the pad, the pad floats. Touching
# the pad guarantees pad->via->In1 regardless of pour topology.
pads_gnd = [(fp.GetReference(), p) for fp in b.GetFootprints() for p in fp.Pads()
            if p.GetNetname() == "GND" and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD]
via_pts = [(v.GetPosition().x / 1e6, v.GetPosition().y / 1e6)
           for v in b.GetTracks() if v.GetClass() == "PCB_VIA" and v.GetNetname() == "GND"]
added = 0
for ref, p in pads_gnd:
    px, py = p.GetPosition().x / 1e6, p.GetPosition().y / 1e6
    hw = p.GetSize().x / 2e6
    hh = p.GetSize().y / 2e6
    # already have a via touching this pad's copper?
    if any(abs(px - vx) < hw + 0.35 and abs(py - vy) < hh + 0.35 for vx, vy in via_pts):
        continue
    done = False
    # rings from the pad centre outward; a via overlapping the pad bonds it
    for ring in (0.0, 0.35, min(hw, hh) + 0.1, max(hw, hh) + 0.15, 0.9, 1.3, 1.8):
        for ang in range(0, 360, 30):
            x = round(px + ring * math.cos(math.radians(ang)), 2)
            y = round(py + ring * math.sin(math.radians(ang)), 2)
            if try_via(gnd, x, y):
                via_pts.append((x, y))
                added += 1
                done = True
                break
            if ring == 0.0:
                break
        if done:
            break
print(f"GND pad-service vias: {added}")


def _seg_d2(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
    return (px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2


# ---- via janitor: remove vias with same-net copper on < 2 layers
_ztmp = {}
for z in b.Zones():
    if z.GetNetname() and not z.GetIsRuleArea():
        o = z.Outline().COutline(0)
        poly = [(o.CPoint(i).x / 1e6, o.CPoint(i).y / 1e6) for i in range(o.PointCount())]
        for lay in z.GetLayerSet().Seq():
            _ztmp.setdefault((z.GetNetname(), lay), []).append(poly)

_orphans = []
for v in [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]:
    nn = v.GetNetname()
    # ONLY janitor GND stitch vias (the ones this script adds). KRT's
    # signal/power vias are load-bearing by construction; a naive
    # <2-layer test wrongly removed VA1P/QSPI_CS vias and disconnected them.
    if nn != "GND":
        continue
    vx, vy = v.GetPosition().x / 1e6, v.GetPosition().y / 1e6
    r2 = (v.GetWidth() / 2e6) ** 2
    attach = set()
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA" or t.GetNetCode() != v.GetNetCode():
            continue
        if _seg_d2(vx, vy, t.GetStart().x / 1e6, t.GetStart().y / 1e6,
                   t.GetEnd().x / 1e6, t.GetEnd().y / 1e6) <= r2:
            attach.add(t.GetLayer())
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetCode() == v.GetNetCode():
                pp = p.GetPosition()
                bb = p.GetBoundingBox()
                bb.Inflate(v.GetWidth() // 2)
                if abs(pp.x / 1e6 - vx) < 2.5 and abs(pp.y / 1e6 - vy) < 2.5 and bb.Contains(v.GetPosition()):
                    for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
                        if p.IsOnLayer(lay):
                            attach.add(lay)
    for (znet, zlay), polys in _ztmp.items():
        if znet == nn and any(_in_poly(vx, vy, poly) for poly in polys):
            attach.add(zlay)
    if len(attach) < 2:
        _orphans.append((v, nn, round(vx, 2), round(vy, 2)))
for v, nn, vx, vy in _orphans:
    b.Remove(v)
print(f"via janitor removed {len(_orphans)}: {[(n, x, y) for _, n, x, y in _orphans][:10]}")

# Starved-thermal rescue: GND SMD pads left unconnected by thermal spokes
# get a via dropped ON the pad (same-net) bonding pad->plane directly.
_gvias = [(v.GetPosition().x / 1e6, v.GetPosition().y / 1e6)
          for v in b.GetTracks() if v.GetClass() == "PCB_VIA" and v.GetNetname() == "GND"]
_added_svc = 0
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname() != "GND" or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
            continue
        px, py = p.GetPosition().x / 1e6, p.GetPosition().y / 1e6
        hw, hh = p.GetSize().x / 2e6, p.GetSize().y / 2e6
        if any(abs(px - vx) < hw + 0.05 and abs(py - vy) < hh + 0.05 for vx, vy in _gvias):
            continue
        for r in (0.0, min(hw, hh) * 0.6, min(hw, hh) + 0.1, 0.5, 0.8):
            done = False
            for ang in range(0, 360, 45):
                x = round(px + r * math.cos(math.radians(ang)), 2)
                y = round(py + r * math.sin(math.radians(ang)), 2)
                if try_via(gnd, x, y, size=0.45, drill=0.3):
                    _gvias.append((x, y))
                    _added_svc += 1
                    done = True
                    break
                if r == 0.0:
                    break
            if done:
                break
print(f"GND pad-on-via rescue: {_added_svc}")

# ---- fill, then stitch any pad-bearing GND island without continuity
filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
via_by_net = {}
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        via_by_net.setdefault(t.GetNetname(), []).append(t.GetPosition())
added = 0
for z in b.Zones():
    nn = z.GetNetname()
    if not nn or z.GetIsRuleArea():
        continue
    for lay in z.GetLayerSet().Seq():
        polys = z.GetFilledPolysList(lay)
        for i in range(polys.OutlineCount()):
            o = polys.Outline(i)
            bb = o.BBox()
            if bb.GetWidth() < 8e5 or bb.GetHeight() < 8e5:
                continue
            if nn == "GND" and not any(o.PointInside(p) for p in via_by_net.get(nn, [])):
                placed = False
                for fx in range(2, 19, 2):
                    for fy in range(2, 19, 2):
                        x = bb.GetLeft() + bb.GetWidth() * fx // 20
                        y = bb.GetTop() + bb.GetHeight() * fy // 20
                        if not o.PointInside(pcbnew.VECTOR2I(x, y)):
                            continue
                        if try_via(gnd, round(x / 1e6, 2), round(y / 1e6, 2)):
                            via_by_net.setdefault(nn, []).append(pcbnew.VECTOR2I(x, y))
                            added += 1
                            placed = True
                            break
                    if placed:
                        break
                if not placed:
                    inside = [p2 for fp2 in b.GetFootprints() for p2 in fp2.Pads()
                              if p2.GetNetname() == nn and o.PointInside(p2.GetPosition())]
                    # an island whose GND pad already has a service via is
                    # connected THROUGH that pad -> plane (pad thermal-joins the
                    # island pour); not an orphan even without an in-island via.
                    served = any(
                        math.hypot(p2.GetPosition().x / 1e6 - vp.x / 1e6,
                                   p2.GetPosition().y / 1e6 - vp.y / 1e6) < 2.6
                        for p2 in inside for vp in via_by_net.get(nn, []))
                    if inside and not served:
                        failures.append(f"GND island ({bb.GetLeft()/1e6:.1f},{bb.GetTop()/1e6:.1f}) unstitchable")
print(f"island stitch vias: {added}")

# ---- post-fill dangling-via cleanup
filler.Fill(b.Zones())
fill_polys = {}
for z in b.Zones():
    if z.GetIsRuleArea() or not z.GetNetname():
        continue
    for lay in z.GetLayerSet().Seq():
        fill_polys.setdefault((z.GetNetname(), lay), []).append(z.GetFilledPolysList(lay))
removed = 0
for v in [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]:
    nn = v.GetNetname()
    if nn != "GND":            # GND stitch vias only (see janitor note)
        continue
    pos = v.GetPosition()
    vx, vy = pos.x / 1e6, pos.y / 1e6
    r2 = (v.GetWidth() / 2e6) ** 2
    attach = set()
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA" or t.GetNetCode() != v.GetNetCode():
            continue
        if _seg_d2(vx, vy, t.GetStart().x / 1e6, t.GetStart().y / 1e6,
                   t.GetEnd().x / 1e6, t.GetEnd().y / 1e6) <= r2:
            attach.add(t.GetLayer())
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetCode() == v.GetNetCode():
                bb = p.GetBoundingBox()
                bb.Inflate(v.GetWidth() // 2)
                if bb.Contains(pos):
                    for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
                        if p.IsOnLayer(lay):
                            attach.add(lay)
    for (znet, zlay), plist in fill_polys.items():
        if znet == nn and zlay not in attach:
            if any(pl.Contains(pos) for pl in plist):
                attach.add(zlay)
    if len(attach) < 2:
        b.Remove(v)
        removed += 1
print(f"post-fill dangling-via cleanup removed {removed}")

if failures:
    print("FAILURES:\n  " + "\n  ".join(failures))
    sys.exit(1)
filler.Fill(b.Zones())
b.Save(PCB)
print("filled + saved")
