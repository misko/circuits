#!/usr/bin/env /usr/bin/python3
"""v1.1 seed-stub PLANNER — maze-routes the pour-fed chip-pin connections KRT
cannot own, against the FROZEN promoted chain (03_src/route/final_chain).

Why this exists: the pour-fed nets LX1/VOUT_PDS/VOUT_PD leave U1's south pin
row and must cross the dense gate/sense escape field to reach their pour
islands. KRT excludes pour-fed nets; the tap-threader only does direct/L/Z
joins (too short for these weaving runs); and hand-fixed stub geometry kept
colliding because every fresh KRT race re-placed the escape tracks. The chain
is now FROZEN (canon M3), so a deterministic maze route over its exact copper
is stable: same chain in, same stubs out. Emits seed_stubs.yaml; the
INDEPENDENT checker in add_seed_stubs.py (different method — pcbnew Collide)
re-verifies every emitted segment before it is placed, and DRC is final judge.
"""
import heapq, math, sys
from pathlib import Path
import yaml
import pcbnew

ROOT = Path(__file__).resolve().parent.parent
CHAIN = ROOT / "03_src/route/final_chain.kicad_pcb"
OUT = ROOT / "03_src/seed_stubs.yaml"

GRID = 0.05            # mm
CLR = 0.135          # planner clearance (just over the 0.13 checker floor;
                     # the escape field itself is packed at 0.13, so a larger
                     # margin walls off the pin-exit gaps the stub must use)
VIA_SIZE, VIA_DRILL = 0.25, 0.15
VIA_R = VIA_SIZE / 2
VIA_COST = 0.6        # mm-equiv penalty per layer change

# Each connection: net, start pin (REF.PAD), goal point (in the pour island),
# stub width, and a bounding box to keep the search bounded. ORDER = most-
# constrained first: all three exit the same U1 south pin row and fan out, so
# an earlier stub can wall a later one. VOUT_PD (longest, dives far south) then
# VOUT_PDS (west lane) then LX1 (shortest, most flexible, routes around both).
# Lane discipline for the shared escape throat just south of U1's pin row
# (y67.5-69 is the bottleneck): each pin drops in ~its own column, then fans
# at a DISTINCT y-level so no stub seals another's throat.
#  - LX1 (east pin U1.18) drops low and fans west at y~71 into its finger
#    (avoid keeps it out of the high y68 lane + U1.15's throat);
#  - VOUT_PDS (middle U1.15) then owns the high y~68 west lane, exit clear;
#  - VOUT_PD (west pin U1.10) dives straight south, whole south region free.
JOBS = [
    {"net": "LX1", "start": "U1.18", "goal": (60.6, 70.9), "w": 0.25,
     "box": (56.0, 66.5, 69.5, 73.0),
     "avoid": [(65.55, 67.4, 66.95, 69.6)]},   # keep LX1 out of U1.15's throat
    {"net": "VOUT_PDS", "start": "U1.15", "goal": (51.5, 73.0), "w": 0.25,
     "box": (45.5, 66.8, 67.5, 78.0)},
    {"net": "VOUT_PD", "start": "U1.10", "goal": (55.0, 83.5), "w": 0.25,
     "box": (52.5, 64.5, 66.8, 86.0)},
]

b = pcbnew.LoadBoard(str(CHAIN))


def net_of(name):
    ni = b.GetNetsByName().find(name)
    if ni == b.GetNetsByName().end():
        sys.exit(f"net {name!r} not on chain")
    return ni.value()[1].GetNetCode()


def pad_xy(ref, num):
    fp = b.FindFootprintByReference(ref)
    for p in fp.Pads():
        if p.GetNumber() == num:
            pos = p.GetPosition()
            return (pos.x / 1e6, pos.y / 1e6)
    sys.exit(f"no pad {ref}.{num}")


def seg_dist(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L2))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def build_obstacles(mynet, w, box, extra, avoid=()):
    """Return (blockedF, blockedB) sets of (ix,iy) cells whose centre is within
    clearance of FOREIGN copper. Same-net copper is free. `extra` = extra
    obstacle primitives from already-routed stubs (list of ('seg',...)/('via'..))."""
    x0, y0, x1, y1 = box
    half = w / 2 + CLR
    bf, bb = set(), set()

    def mark(store, cx, cy, reach):
        r = reach
        imin = int((cx - r - x0) / GRID) - 1
        imax = int((cx + r - x0) / GRID) + 1
        jmin = int((cy - r - y0) / GRID) - 1
        jmax = int((cy + r - y0) / GRID) + 1
        for ix in range(imin, imax + 1):
            for iy in range(jmin, jmax + 1):
                gx = x0 + ix * GRID
                gy = y0 + iy * GRID
                if math.hypot(gx - cx, gy - cy) <= r:
                    store.add((ix, iy))

    def mark_seg(store, x1s, y1s, x2s, y2s, reach):
        imin = int((min(x1s, x2s) - reach - x0) / GRID) - 1
        imax = int((max(x1s, x2s) + reach - x0) / GRID) + 1
        jmin = int((min(y1s, y2s) - reach - y0) / GRID) - 1
        jmax = int((max(y1s, y2s) + reach - y0) / GRID) + 1
        for ix in range(imin, imax + 1):
            for iy in range(jmin, jmax + 1):
                gx = x0 + ix * GRID
                gy = y0 + iy * GRID
                if seg_dist(gx, gy, x1s, y1s, x2s, y2s) <= reach:
                    store.add((ix, iy))

    for t in b.GetTracks():
        if t.GetNetCode() == mynet:
            continue
        if t.Type() == pcbnew.PCB_VIA_T:
            p = t.GetPosition()
            reach = t.GetWidth() / 2e6 + half
            mark(bf, p.x / 1e6, p.y / 1e6, reach)
            mark(bb, p.x / 1e6, p.y / 1e6, reach)
        else:
            s, e = t.GetStart(), t.GetEnd()
            reach = t.GetWidth() / 2e6 + half
            store = bf if t.GetLayer() == pcbnew.F_Cu else bb
            mark_seg(store, s.x / 1e6, s.y / 1e6, e.x / 1e6, e.y / 1e6, reach)
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetCode() == mynet:
                continue
            pos = p.GetPosition()
            sz = p.GetSize()
            reach = max(sz.x, sz.y) / 2e6 + half
            if p.IsOnLayer(pcbnew.F_Cu):
                mark(bf, pos.x / 1e6, pos.y / 1e6, reach)
            if p.IsOnLayer(pcbnew.B_Cu):
                mark(bb, pos.x / 1e6, pos.y / 1e6, reach)
    for prim in extra:
        if prim[0] == "seg":
            _, layer, xa, ya, xb, yb, ww = prim
            store = bf if layer == "F.Cu" else bb
            mark_seg(store, xa, ya, xb, yb, ww / 2 + w / 2 + CLR)
        else:
            _, xa, ya = prim
            mark(bf, xa, ya, VIA_R + half)
            mark(bb, xa, ya, VIA_R + half)
    # soft keepout rects (route-planning lane separation, both layers)
    for (ax, ay, bx, by) in avoid:
        for ix in range(int((ax - x0) / GRID) - 1, int((bx - x0) / GRID) + 2):
            for iy in range(int((ay - y0) / GRID) - 1, int((by - y0) / GRID) + 2):
                gx, gy = x0 + ix * GRID, y0 + iy * GRID
                if ax <= gx <= bx and ay <= gy <= by:
                    bf.add((ix, iy)); bb.add((ix, iy))
    return bf, bb


def astar(start, goal, box, bf, bb):
    x0, y0, x1, y1 = box
    nx = int((x1 - x0) / GRID)
    ny = int((y1 - y0) / GRID)

    def cell(px, py):
        return (int(round((px - x0) / GRID)), int(round((py - y0) / GRID)))
    sc = cell(*start)
    gc = cell(*goal)
    blocked = {0: bf, 1: bb}

    def free(ix, iy, lay):
        return 0 <= ix <= nx and 0 <= iy <= ny and (ix, iy) not in blocked[lay]
    # start/goal cells forced free (we begin on the pad, end in the pour)
    def h(ix, iy):
        return math.hypot(ix - gc[0], iy - gc[1]) * GRID
    steps = [(1, 0, GRID), (-1, 0, GRID), (0, 1, GRID), (0, -1, GRID),
             (1, 1, GRID * 1.414), (1, -1, GRID * 1.414),
             (-1, 1, GRID * 1.414), (-1, -1, GRID * 1.414)]
    start_state = (sc[0], sc[1], 0)
    openh = [(h(*sc), 0.0, start_state)]
    came = {}
    g = {start_state: 0.0}
    seen = set()
    goal_state = None
    while openh:
        f, gc_cost, st = heapq.heappop(openh)
        if st in seen:
            continue
        seen.add(st)
        ix, iy, lay = st
        if (ix, iy) == gc:
            goal_state = st
            break
        for dx, dy, cost in steps:
            nix, niy = ix + dx, iy + dy
            if (nix, niy) == gc or free(nix, niy, lay) or (nix, niy) == sc:
                ns = (nix, niy, lay)
                ng = gc_cost + cost
                if ng < g.get(ns, 1e18):
                    g[ns] = ng
                    came[ns] = st
                    heapq.heappush(openh, (ng + h(nix, niy), ng, ns))
        # via transition
        other = 1 - lay
        if free(ix, iy, other) or (ix, iy) == sc or (ix, iy) == gc:
            ns = (ix, iy, other)
            ng = gc_cost + VIA_COST
            if ng < g.get(ns, 1e18):
                g[ns] = ng
                came[ns] = st
                heapq.heappush(openh, (ng + h(ix, iy), ng, ns))
    if goal_state is None:
        return None
    # reconstruct
    path = []
    st = goal_state
    while st in came:
        path.append(st)
        st = came[st]
    path.append(start_state)
    path.reverse()
    return [(x0 + ix * GRID, y0 + iy * GRID, "F.Cu" if lay == 0 else "B.Cu")
            for ix, iy, lay in path]


def simplify(path):
    """Collapse collinear same-layer runs into segments; record via points at
    layer changes. Returns (segments, vias). segments = list of
    (layer, [(x,y),...]); vias = list of (x,y)."""
    segs = []
    vias = []
    i = 0
    cur_layer = path[0][2]
    run = [(round(path[0][0], 3), round(path[0][1], 3))]
    def flush(layer, pts):
        # merge collinear
        if len(pts) < 2:
            return
        merged = [pts[0]]
        for k in range(1, len(pts) - 1):
            ax, ay = merged[-1]
            bx, by = pts[k]
            cx, cy = pts[k + 1]
            cross = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
            if abs(cross) > 1e-6:
                merged.append(pts[k])
        merged.append(pts[-1])
        segs.append((layer, merged))
    for k in range(1, len(path)):
        x, y, lay = path[k]
        x, y = round(x, 3), round(y, 3)
        if lay != cur_layer:
            flush(cur_layer, run)
            vias.append((x, y))          # via at the transition point
            cur_layer = lay
            run = [(x, y)]
        else:
            run.append((x, y))
    flush(cur_layer, run)
    return segs, vias


stubs = []
placed_extra = []
for job in JOBS:
    mynet = net_of(job["net"])
    ref, num = job["start"].split(".")
    start = pad_xy(ref, num)
    goal = job["goal"]
    bf, bb = build_obstacles(mynet, job["w"], job["box"], placed_extra,
                             job.get("avoid", ()))
    path = astar(start, goal, job["box"], bf, bb)
    if path is None:
        # diagnostic flood from the start pad over the same obstacle sets
        x0, y0, x1, y1 = job["box"]
        nx = int((x1 - x0) / GRID); ny = int((y1 - y0) / GRID)
        blk = {0: bf, 1: bb}
        sc = (int(round((start[0] - x0) / GRID)), int(round((start[1] - y0) / GRID)))
        gc = (int(round((goal[0] - x0) / GRID)), int(round((goal[1] - y0) / GRID)))
        fr = lambda ix, iy, l: 0 <= ix <= nx and 0 <= iy <= ny and (ix, iy) not in blk[l]
        from collections import deque
        seen = {(sc[0], sc[1], 0)}; dq = deque(seen)
        while dq:
            ix, iy, l = dq.popleft()
            for dx, dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                n = (ix+dx, iy+dy, l)
                if n not in seen and fr(ix+dx, iy+dy, l): seen.add(n); dq.append(n)
            n = (ix, iy, 1-l)
            if n not in seen and fr(ix, iy, 1-l): seen.add(n); dq.append(n)
        nbr = sum(1 for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1))
                  if fr(sc[0]+dx, sc[1]+dy, 0)) + (1 if fr(sc[0],sc[1],1) else 0)
        best = min(seen, key=lambda c: math.hypot(c[0]-gc[0], c[1]-gc[1]))
        sys.exit(f"PLAN FAIL {job['net']} {job['start']}->{goal}: no clear path "
                 f"[start exits={nbr}, reached={len(seen)}, "
                 f"closest=({x0+best[0]*GRID:.2f},{y0+best[1]*GRID:.2f})L{best[2]} "
                 f"d={math.hypot(best[0]-gc[0],best[1]-gc[1])*GRID:.2f}mm]")
    segs, vias = simplify(path)
    # always drop a via at the goal so the pour island bonds on fill
    if goal not in vias:
        vias.append((round(goal[0], 3), round(goal[1], 3)))
    total = sum(math.hypot(p[i + 1][0] - p[i][0], p[i + 1][1] - p[i][1])
                for _, p in segs for i in range(len(p) - 1))
    print(f"  {job['net']:9s} {job['start']}->{goal}: "
          f"{len(segs)} runs, {len(vias)} vias, {total:.1f}mm")
    stub = {"net": job["net"], "segments": [
        {"layer": lay, "width": job["w"], "pts": [list(pt) for pt in pts]}
        for lay, pts in segs], "vias": [list(v) for v in vias]}
    stubs.append(stub)
    # register this stub as an obstacle for later jobs
    for lay, pts in segs:
        for i in range(len(pts) - 1):
            placed_extra.append(("seg", lay, pts[i][0], pts[i][1],
                                 pts[i + 1][0], pts[i + 1][1], job["w"]))
    for v in vias:
        placed_extra.append(("via", v[0], v[1]))

header = (
    "# v1.1 pour-net chip-pin seed stubs — MAZE-PLANNED by plan_seed_stubs.py\n"
    "# against the FROZEN chain (03_src/route/final_chain.kicad_pcb). Do not\n"
    "# hand-edit coordinates; re-run the planner if the chain is re-promoted.\n"
    "# add_seed_stubs.py re-checks every segment (independent pcbnew Collide)\n"
    "# before placing; DRC is the final judge.\n")
with open(OUT, "w") as f:
    f.write(header)
    yaml.safe_dump({"via": {"size": VIA_SIZE, "drill": VIA_DRILL},
                    "stubs": stubs}, f, sort_keys=False, default_flow_style=None)
print(f"wrote {OUT}")
