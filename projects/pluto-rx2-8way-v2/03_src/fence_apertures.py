#!/usr/bin/env python3
"""CLASSIFY every fence aperture by CAUSE — name the copper that occupies the
lattice site, never a count.

For each arm-side gap wider than the bound, enumerate the stitch-grid LATTICE
sites that fall inside the gap's flank band, find the ones with no via, and
report the NEAREST board object (pad / track / footprint) to that site.

DECLARED BACKEND GAP (canon M8; 03_src/contracts.md makes any *.py beyond
audit_board/bom_seed a STOPGAP that must name its gap and the schema that
would replace it).
THE GAP: this repo carries 32 gates and NONE grades an RF cross-section or a
ground-stitch spacing. `rf-design.md` sec 6 ranked a via-fence gate and
REJECTED it on the premise that "all three fleet values are already
conservative"; measured, that premise was half wrong -- this board sits outside
its own bound by 2.56x -- and the rejection has since been amended but not
reversed. So the check lives here.
THE CONFIG SCHEMA THAT WOULD REPLACE IT: `rules/nets.yaml` already carries
`length_match.<G>.phase.{t_pd_ps_per_mm, f_ghz, stackup, cross_section}`; a
shared gate needs only that `cross_section` key (declared 2026-07-30) plus a
`fence: {bound_mm, band_mm, arms: []}` block, and it would then grade every
board in this family from source alone.
THIS IS THE SECOND BOARD TO NEED IT -- pluto-rx2-8way v1 carried the same
measurement -- which by the contract's own rule TRIGGERS MANDATORY PROMOTION
into the shared backend. Promotion is REPORTED to the caller and NOT done
here: this agent's partition is `projects/pluto-rx2-8way-v2/` only.
"""
import math
import sys

import pcbnew

BOARD = sys.argv[1]
PITCH = float(sys.argv[2])
ORIGIN = (23.0, 23.0)
BAND = 2.5
# BOUND is argv[3] (default 1.1910 = lambda_pp/20, the GCPW ground-stitch
# bound derived in 03_src/gcpw_constants.py). It used to be the
# hardcoded 1.35 of the BARE-MICROSTRIP derivation, which is the wrong
# cross-section for this board -- see 01_docs/decisions/0004-*.
BOUND = float(sys.argv[3]) if len(sys.argv) > 3 else 1.1910
ARMS = ["ANT1", "ANT2", "ANT3", "ANT4", "ANT5", "ANT6", "ANT7", "RX2_OUT",
        "RX1_TAP", "RX1_MAIN", "RX1_TAP_MID"]

bd = pcbnew.LoadBoard(BOARD)
F_CU = bd.GetLayerID("F.Cu")
mm = lambda v: v / 1e6

vias = [(mm(t.GetPosition().x), mm(t.GetPosition().y))
        for t in bd.GetTracks()
        if t.GetClass() == "PCB_VIA" and t.GetNetname() == "GND"]
viaset = {(round(x, 2), round(y, 2)) for x, y in vias}

# ---- every non-GND copper object, as (label, x, y) ------------------------
objs = []
for fp in bd.GetFootprints():
    ref = fp.GetReference()
    for pad in fp.Pads():
        p = pad.GetPosition()
        objs.append((f"pad {ref}.{pad.GetNumber()} net={pad.GetNetname()}",
                     mm(p.x), mm(p.y)))
for t in bd.GetTracks():
    if t.GetClass() == "PCB_VIA":
        if t.GetNetname() != "GND":
            p = t.GetPosition()
            objs.append((f"via net={t.GetNetname()}", mm(p.x), mm(p.y)))
        continue
    if t.GetNetname() == "GND":
        continue
    a, b = t.GetStart(), t.GetEnd()
    objs.append((f"track net={t.GetNetname()} {t.GetLayerName()}",
                 (mm(a.x) + mm(b.x)) / 2, (mm(a.y) + mm(b.y)) / 2))

SMA = {"J_ANT1": (29.85, 37.20), "J_ANT2": (25.10, 48.25),
       "J_ANT3": (29.20, 59.15), "J_ANT4": (39.10, 64.25),
       "J_ANT5": (52.80, 60.15), "J_ANT6": (56.90, 49.25),
       "J_ANT7": (52.80, 38.35), "J_RX2": (40.75, 33.10),
       "J_ANT8": (46.50, 25.00), "J_RX1": (54.50, 25.00)}


def polyline(net):
    segs = []
    for t in bd.GetTracks():
        if t.GetClass() != "PCB_TRACK" or t.GetNetname() != net:
            continue
        if t.GetLayer() != F_CU:
            continue
        a, b = t.GetStart(), t.GetEnd()
        segs.append(((round(mm(a.x), 4), round(mm(a.y), 4)),
                     (round(mm(b.x), 4), round(mm(b.y), 4))))
    if not segs:
        return []
    adj = {}
    for a, b in segs:
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    ends = [p for p, n in adj.items() if len(n) == 1]
    start = sorted(ends)[0] if ends else sorted(adj)[0]
    chain, seen, cur, prev = [start], set(), start, None
    while True:
        nxt = None
        for cand in adj.get(cur, []):
            k = tuple(sorted([cur, cand]))
            if cand != prev and k not in seen:
                nxt = cand
                seen.add(k)
                break
        if nxt is None:
            break
        chain.append(nxt)
        prev, cur = cur, nxt
    return chain


def project(chain, px, py):
    best, s0 = None, 0.0
    for i in range(len(chain) - 1):
        (x1, y1), (x2, y2) = chain[i], chain[i + 1]
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy)
        if L == 0:
            continue
        t = ((px - x1) * dx + (py - y1) * dy) / (L * L)
        tc = max(0.0, min(1.0, t))
        d = math.hypot(px - (x1 + tc * dx), py - (y1 + tc * dy))
        cross = (dx * (py - y1) - dy * (px - x1)) / L
        outer = (i == 0 and t < 0) or (i == len(chain) - 2 and t > 1)
        if best is None or d < best[0]:
            best = (d, s0 + tc * L, 1 if cross >= 0 else -1, outer)
        s0 += L
    return best


def at(chain, s):
    s0 = 0.0
    for i in range(len(chain) - 1):
        (x1, y1), (x2, y2) = chain[i], chain[i + 1]
        L = math.hypot(x2 - x1, y2 - y1)
        if s <= s0 + L:
            t = (s - s0) / L if L else 0
            return x1 + t * (x2 - x1), y1 + t * (y2 - y1)
        s0 += L
    return chain[-1]


def nearest_obj(x, y, rmax=1.4):
    best = None
    for lbl, ox, oy in objs:
        d = math.hypot(x - ox, y - oy)
        if best is None or d < best[0]:
            best = (d, lbl)
    for ref, (sx, sy) in SMA.items():
        d = math.hypot(x - sx, y - sy)
        if d <= 1.90:
            return (d, f"AVOID ring {ref} (declared r=1.90)")
    return best


print(f"lattice: origin {ORIGIN}, pitch {PITCH} mm; band +/-{BAND}; "
      f"bound {BOUND} mm\n")
for net in ARMS:
    ch = polyline(net)
    if len(ch) < 2:
        continue
    L = sum(math.hypot(ch[i + 1][0] - ch[i][0], ch[i + 1][1] - ch[i][1])
            for i in range(len(ch) - 1))
    for side in (-1, 1):
        pts = []
        for (vx, vy) in vias:
            r = project(ch, vx, vy)
            if r is None:
                continue
            d, s, sgn, outer = r
            if outer or d > BAND or sgn != side or s <= 1e-6 or s >= L - 1e-6:
                continue
            pts.append(s)
        pts.sort()
        if len(pts) < 2:
            continue
        for i in range(len(pts) - 1):
            g = pts[i + 1] - pts[i]
            if g <= BOUND + 1e-9:
                continue
            s1, s2 = pts[i], pts[i + 1]
            tag = "L" if side < 0 else "R"
            print(f"{net} side{tag}  GAP {g:.4f} mm  s={s1:.2f}..{s2:.2f}")
            # lattice sites inside the gap's flank band on this side
            found = []
            nx = int((70 - ORIGIN[0]) / PITCH) + 2
            ny = int((95 - ORIGIN[1]) / PITCH) + 2
            for a in range(nx):
                for b in range(ny):
                    X = ORIGIN[0] + a * PITCH
                    Y = ORIGIN[1] + b * PITCH
                    r = project(ch, X, Y)
                    if r is None:
                        continue
                    d, s, sgn, outer = r
                    if outer or d > BAND or sgn != side:
                        continue
                    if not (s1 < s < s2):
                        continue
                    if (round(X, 2), round(Y, 2)) in viaset:
                        continue
                    dd, lbl = nearest_obj(X, Y)
                    found.append((s, X, Y, d, dd, lbl))
            for s, X, Y, d, dd, lbl in sorted(found)[:6]:
                print(f"    empty site ({X:6.2f},{Y:6.2f}) off={d:.2f} "
                      f"-> nearest {lbl} at {dd:.2f} mm")
            if not found:
                mx, my = at(ch, (s1 + s2) / 2)
                dd, lbl = nearest_obj(mx, my)
                print(f"    NO lattice site in this band segment "
                      f"(mid of gap at {mx:.2f},{my:.2f}; nearest {lbl})")
            print()
