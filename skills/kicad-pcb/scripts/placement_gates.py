"""Shared placement-stage static gates — run POST-placement, PRE-routing.

    /usr/bin/python3 placement_gates.py BOARD.kicad_pcb [--config placement_gates.json]

Two checks, both born from the smc0985-cooksense routing D-BACK of 2026-07-23
(journal: 01_docs/journal/routing_cooksense.md), where a placement that PASSED
every existing audit cost ~13 hours of routing before the defects surfaced:

  P-OUT  pads-inside-OUTLINE. Every footprint pad (bbox, optionally the
         courtyard too) must sit inside the REAL Edge.Cuts polygon with a
         margin — not inside a configured rectangle (audit_template I1) and
         not merely "mouth reaches the edge" (per-board I-EDGE). The incident:
         J_PI (2x20, 48mm body) was anchored ON-board but laid its body OFF
         the south edge — 34/40 pins 1..43mm off the outline. I-EDGE saw the
         mouth at the edge and PASSED; a 600k-iteration KRT run found it.
         This is the generalized harvest of the bespoke I-OUT check cooksense
         then built (commit 1813595, 03_src/cooksense/audit_board.py).

  P-CAP  crossing-DEMAND vs corridor-CAPACITY. From placement + the board's
         own netlist (pad nets), sweep candidate cut lines across both axes;
         at each cut, demand = nets whose pads sit on BOTH sides of a band
         (cross-footprint; pour-carried and excluded nets don't count) and
         capacity = the un-blocked width along the cut (pad copper + no-track
         rule areas subtracted, per routable layer) divided by the
         track+clearance pitch. FAIL when demand exceeds factor x capacity
         anywhere. The incident: the placement journal eyeballed "~3 nets
         cross east" where 26 nets actually crossed a corridor that could
         carry 6 — an 8x under-count with no static check to catch it, found
         only by routing to exhaustion. This gate is that missing static
         estimate: coarse by construction (bbox blockage, straight-line
         demand), a smoke alarm for corridor starvation, not a router.

Config (JSON, ALL optional — a missing file or missing key = defaults):
{
  "outline_margin": 0.15,        // mm, min pad-copper-to-Edge.Cuts distance
  "courtyard": false,            // stricter: courtyard polygons inside too
  "out_ok": ["J9"],              // refs waived from P-OUT (castellated etc.)
  "cap": {
    "track": 0.25, "clearance": 0.2,   // pitch = track+clearance
    "layers": 2,                 // routable copper layers (inner planes DON'T route)
    "band": 3.0,                 // corridor band half-ignore width for demand (mm)
    "step": 2.0,                 // cut-line scan step (mm)
    "edge": 1.0,                 // ignore cuts closer than this to the extents
    "factor": 0.5,               // FAIL when demand > factor*capacity
    "warn_factor": 0.3,          // WARN above this fraction of capacity
    "exclude_nets": ["^GND"],    // regexes; nets with a POUR are auto-excluded
    "waive_cuts": [{"axis":"y","lo":40,"hi":50,"why":"..."}]  // evidence req'd
  },
  "waive": {"P-CAP": "evidence sentence"}   // whole-check waiver, evidence req'd
}

Exit 1 on any FAIL. Prints measured numbers (worst cut per axis) either way —
report them, don't summarize them (canon: measured numbers, honestly).
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path

import pcbnew

MM = pcbnew.ToMM


# --------------------------------------------------------------- geometry
def _outline_polys(board):
    """Board outline as [(outer_ring, [hole_rings...])], rings = [(x,y) mm]."""
    sps = pcbnew.SHAPE_POLY_SET()
    try:
        ok = board.GetBoardPolygonOutlines(sps)          # KiCad <= 9
    except TypeError:
        ok = board.GetBoardPolygonOutlines(sps, True)    # KiCad 10: aInferOutlineIfNecessary
    if not ok:
        return []
    out = []
    for i in range(sps.OutlineCount()):
        ring = sps.Outline(i)
        outer = [(MM(ring.CPoint(k).x), MM(ring.CPoint(k).y))
                 for k in range(ring.PointCount())]
        holes = []
        for j in range(sps.HoleCount(i)):
            h = sps.Hole(i, j)
            holes.append([(MM(h.CPoint(k).x), MM(h.CPoint(k).y))
                          for k in range(h.PointCount())])
        out.append((outer, holes))
    return out


def _in_ring(px, py, ring):
    inside = False
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        if (y1 > py) != (y2 > py):
            xx = x1 + (py - y1) * (x2 - x1) / (y2 - y1)
            if px < xx:
                inside = not inside
    return inside


def _dist_ring(px, py, ring):
    d = 1e9
    n = len(ring)
    for i in range(n):
        ax, ay = ring[i]
        bx, by = ring[(i + 1) % n]
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
        d = min(d, math.hypot(px - (ax + t * dx), py - (ay + t * dy)))
    return d


def signed_margin(px, py, polys):
    """+d: point is d mm inside the outline; -d: d mm outside (or in a hole)."""
    best = -1e9
    for outer, holes in polys:
        d = _dist_ring(px, py, outer)
        if _in_ring(px, py, outer):
            for h in holes:
                if _in_ring(px, py, h):
                    d = -_dist_ring(px, py, h)
                    break
                d = min(d, _dist_ring(px, py, h))
        else:
            d = -d
        best = max(best, d)
    return best


# ----------------------------------------------------------------- P-OUT
def check_out(board, cfg, fails, notes):
    margin = cfg.get("outline_margin", 0.15)
    ok_refs = set(cfg.get("out_ok", []))
    polys = _outline_polys(board)
    if not polys:
        fails.append("P-OUT board has NO closed Edge.Cuts outline")
        return
    worst, warg = 1e9, None
    for f in board.GetFootprints():
        r = f.GetReference()
        pts = []
        for p in f.Pads():
            bb = p.GetBoundingBox()
            L, T, R, B = MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom())
            pts.append((f"{r}.{p.GetNumber()}", [(L, T), (R, T), (R, B), (L, B)]))
        if cfg.get("courtyard", False):
            for lay in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
                poly = f.GetCourtyard(lay)
                for i in range(poly.OutlineCount() if poly else 0):
                    ring = poly.Outline(i)
                    pts.append((f"{r}(courtyard)",
                                [(MM(ring.CPoint(k).x), MM(ring.CPoint(k).y))
                                 for k in range(ring.PointCount())]))
        for name, corners in pts:
            m = min(signed_margin(x, y, polys) for x, y in corners)
            if r not in ok_refs and m < worst:
                worst, warg = m, name
            if m < margin - 1e-6 and r not in ok_refs:
                if m < 0:
                    fails.append(f"P-OUT {name} is {-m:.1f}mm OFF the board outline")
                else:
                    fails.append(f"P-OUT {name} only {m:.2f}mm inside the outline "
                                 f"(< {margin}mm margin)")
    if warg is not None:
        notes.append(f"P-OUT tightest pad-to-outline margin {worst:.2f}mm ({warg}) "
                     f"[min {margin}]")


# ----------------------------------------------------------------- P-CAP
def _routable_layers(board, n):
    cands = [pcbnew.F_Cu, pcbnew.B_Cu,
             pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.In3_Cu, pcbnew.In4_Cu]
    have = cands[:2 + max(0, board.GetCopperLayerCount() - 2)]
    return have[:max(1, n)]


def _merge(iv):
    iv = sorted(iv)
    out = []
    for a, b in iv:
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def check_cap(board, cfg, fails, warns, notes):
    cap = cfg.get("cap", {})
    track = cap.get("track", 0.25)
    clr = cap.get("clearance", 0.2)
    pitch = track + clr
    band = cap.get("band", 3.0)
    hw = band / 2.0
    step = cap.get("step", 2.0)
    edge = cap.get("edge", 1.0)
    factor = cap.get("factor", 0.5)
    wfactor = cap.get("warn_factor", 0.3)
    layers = _routable_layers(board, cap.get("layers", 2))
    excl = [re.compile(p) for p in cap.get("exclude_nets", ["^GND"])]
    waive_cuts = cap.get("waive_cuts", [])
    for w in waive_cuts:
        if not str(w.get("why", "")).strip():
            fails.append(f"P-CAP waive_cuts entry without evidence (why): {w}")
            return

    # nets carried by a pour are PLANEABLE: they don't consume corridor tracks
    # Rule areas: "all" (default) treats EVERY rule area as corridor blockage —
    # at placement stage a rule area is declared stay-out intent even when it
    # only forbids pours today (the cooksense isolation strip forbade pours on
    # the board; the 6mm track creepage lived in route.yaml where no static
    # check could see it). "tracks" = only DoNotAllowTracks areas; "none" = off.
    komode = cap.get("keepouts", "all")
    pour_nets, keepouts = set(), []
    for z in board.Zones():
        if z.GetIsRuleArea():
            if komode == "all" or (komode == "tracks" and z.GetDoNotAllowTracks()):
                zb = z.GetBoundingBox()
                keepouts.append((set(l for l in layers if z.IsOnLayer(l)),
                                 (MM(zb.GetLeft()), MM(zb.GetTop()),
                                  MM(zb.GetRight()), MM(zb.GetBottom()))))
        elif z.GetNetname():
            pour_nets.add(z.GetNetname())

    pads = []                       # (net, ref, x, y, bbox, layer_set|None=THT)
    net_ext = {}                    # net -> [minx, miny, maxx, maxy] of pad centres
    for f in board.GetFootprints():
        r = f.GetReference()
        for p in f.Pads():
            n = p.GetNetname()
            bb = p.GetBoundingBox()
            lays = None if p.GetDrillSize().x > 0 else \
                set(l for l in layers if p.IsOnLayer(l))
            x, y = MM(p.GetPosition().x), MM(p.GetPosition().y)
            pads.append((n, r, x, y,
                         (MM(bb.GetLeft()), MM(bb.GetTop()),
                          MM(bb.GetRight()), MM(bb.GetBottom())), lays))
            if n:
                e = net_ext.setdefault(n, [x, y, x, y])
                e[0], e[1] = min(e[0], x), min(e[1], y)
                e[2], e[3] = max(e[2], x), max(e[3], y)

    # A net whose pads ALL sit inside one keepout region is a RESIDENT of that
    # region: it routes inside it by design (cooksense keypad-iso strip), so it
    # is neither corridor demand nor blocked by its own region's blockage.
    resident = set()
    for n, (nx0, ny0, nx1, ny1) in net_ext.items():
        for _, (kl, kt, kr, kb) in keepouts:
            if kl - 0.5 <= nx0 and nx1 <= kr + 0.5 and \
                    kt - 0.5 <= ny0 and ny1 <= kb + 0.5:
                resident.add(n)
                break

    def in_keepout(x, y):
        return any(kl - 0.5 <= x <= kr + 0.5 and kt - 0.5 <= y <= kb + 0.5
                   for _, (kl, kt, kr, kb) in keepouts)

    def demand_nets(axis, c):
        """Nets needing a TRACK across cut `axis`=c: pads of more than one
        footprint on strictly both sides of the band, not pour-carried, not
        excluded. The cross-footprint requirement keeps a single straddling
        IC's internal nets from counting as corridor demand. A net whose pads
        on ONE side all sit inside a keepout region TERMINATES there — the
        region legally admits its track (cooksense reed-coil feeds ending
        inside the isolation strip), so it is not corridor traffic competing
        for the un-blocked lanes."""
        lo, hi = {}, {}
        lo_out, hi_out = set(), set()      # nets with >=1 pad OUTSIDE keepouts
        for n, r, x, y, bb, lays in pads:
            if not n or n in pour_nets or n in resident \
                    or any(rx.search(n) for rx in excl):
                continue
            v = y if axis == "y" else x
            if v < c - hw:
                lo.setdefault(n, set()).add(r)
                if not in_keepout(x, y):
                    lo_out.add(n)
            elif v > c + hw:
                hi.setdefault(n, set()).add(r)
                if not in_keepout(x, y):
                    hi_out.add(n)
        out = []
        for n in lo:
            if n in hi and n in lo_out and n in hi_out \
                    and not (len(lo[n]) == 1 and lo[n] == hi[n]):
                out.append(n)
        return sorted(out)

    def capacity(axis, c, x0, x1):
        """Track slots across the cut: per routable layer, the free intervals
        of [x0,x1] not blocked by pad copper / no-track rule areas in the
        band, each interval carrying 1 + floor((w-track)/pitch) tracks."""
        total = 0
        for L in layers:
            blocked = []
            for n, r, x, y, bb, lays in pads:
                if lays is not None and L not in lays:
                    continue
                bl, bt, br, bbm = bb
                if axis == "y":
                    if bt - clr <= c + hw and bbm + clr >= c - hw:
                        blocked.append([bl - clr, br + clr])
                else:
                    if bl - clr <= c + hw and br + clr >= c - hw:
                        blocked.append([bt - clr, bbm + clr])
            for klays, (kl, kt, kr, kb) in keepouts:
                if L not in klays:
                    continue
                if axis == "y" and kt <= c + hw and kb >= c - hw:
                    blocked.append([kl, kr])
                if axis == "x" and kl <= c + hw and kr >= c - hw:
                    blocked.append([kt, kb])
            pos = x0
            for a, b in _merge([[max(x0, a), min(x1, b)]
                                for a, b in blocked if b > x0 and a < x1]):
                w = a - pos
                if w >= track:
                    total += 1 + int((w - track) / pitch)
                pos = max(pos, b)
            w = x1 - pos
            if w >= track:
                total += 1 + int((w - track) / pitch)
        return total

    bb = board.GetBoardEdgesBoundingBox()
    BX0, BY0 = MM(bb.GetLeft()), MM(bb.GetTop())
    BX1, BY1 = MM(bb.GetRight()), MM(bb.GetBottom())
    worst = None                    # (ratio, axis, c, D, C, nets)
    viol = []
    for axis, lo_, hi_, px0, px1 in (("y", BY0, BY1, BX0, BX1),
                                     ("x", BX0, BX1, BY0, BY1)):
        c = lo_ + edge + hw
        while c <= hi_ - edge - hw:
            waived = any(w.get("axis") == axis
                         and w.get("lo", -1e9) <= c <= w.get("hi", 1e9)
                         for w in waive_cuts)
            if not waived:
                D = demand_nets(axis, c)
                if D:
                    C = capacity(axis, c, px0 + 0.3, px1 - 0.3)
                    ratio = len(D) / max(C, 0.5)
                    if worst is None or ratio > worst[0]:
                        worst = (ratio, axis, c, len(D), C, D)
                    if len(D) > factor * C:
                        viol.append((axis, c, len(D), C, D))
            c += step
    if worst:
        r, axis, c, D, C, nets = worst
        notes.append(f"P-CAP worst cut {axis}={c:.1f}mm: demand {D} nets vs "
                     f"capacity {C} tracks ({len(layers)} layers, pitch "
                     f"{pitch:.2f}mm) — ratio {r:.2f} [fail > {factor}]")
        if not viol and D > wfactor * C:
            warns.append(f"P-CAP cut {axis}={c:.1f}mm at {100*r:.0f}% of corridor "
                         f"capacity ({D}/{C}) — placement has little routing slack")
    else:
        notes.append("P-CAP no crossing demand anywhere (or all nets planeable)")
    if viol:
        # report the worst violating cut per axis, with the crossing nets named
        for axis in ("y", "x"):
            va = [v for v in viol if v[0] == axis]
            if not va:
                continue
            _, c, D, C, nets = max(va, key=lambda v: v[2] / max(v[3], 0.5))
            fails.append(f"P-CAP corridor starved at {axis}={c:.1f}mm: crossing "
                         f"demand {D} nets > capacity {C} tracks "
                         f"({len(va)} violating cut(s) on this axis); crossers: "
                         f"{nets[:12]}{'...' if len(nets) > 12 else ''}")


# ------------------------------------------------------------------ main
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("board")
    ap.add_argument("--config", default=None,
                    help="optional JSON config; a MISSING file means defaults")
    ap.add_argument("--courtyard", action="store_true",
                    help="P-OUT stricter mode: courtyards inside the outline too")
    args = ap.parse_args(argv)

    cfg = {}
    if args.config and Path(args.config).exists():
        cfg = json.loads(Path(args.config).read_text(encoding="utf-8-sig"))
    if args.courtyard:
        cfg["courtyard"] = True
    waive = cfg.get("waive", {})
    for cid, why in waive.items():
        if not str(why).strip():
            print(f"FAIL: {cid} waiver without evidence (empty why)")
            return 1

    board = pcbnew.LoadBoard(args.board)
    fails, warns, notes = [], [], []
    if "P-OUT" in waive:
        notes.append(f"P-OUT WAIVED: {waive['P-OUT']}")
    else:
        check_out(board, cfg, fails, notes)
    if "P-CAP" in waive:
        notes.append(f"P-CAP WAIVED: {waive['P-CAP']}")
    else:
        check_cap(board, cfg, fails, warns, notes)

    for n in notes:
        print("  note:", n)
    for w in warns:
        print("WARN:", w)
    for x in fails:
        print("FAIL:", x)
    print("PLACEMENT-GATES:", "FAIL" if fails else "PASS",
          f"({len(fails)} fails, {len(warns)} warns)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
