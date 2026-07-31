#!/usr/bin/env python3
"""MEASURE the realized ground-via fence pitch flanking every RF arm.

Independent of the stitcher (canon M1): reads the SAVED .kicad_pcb through
pcbnew, reconstructs each arm's F.Cu polyline from its OWN track segments,
and measures the ALONG-ARM centre-to-centre spacing of the GND vias that
flank it.  Nothing here reads route.yaml, so a declared pitch cannot certify
itself.

WHY ALONG-ARM AND NOT NEAREST-NEIGHBOUR.  ADR-0003 defines the bound as the
"maximum centre-to-centre spacing of the ground-via fence flanking any RF arm,
so the fence acts as a continuous wall rather than a periodic structure with a
passband".  A wall's aperture is what the wave travelling ALONG the arm sees,
so the spacing that matters is the projection onto the arm axis, per side.
A square lattice's nearest-neighbour distance IS its pitch in every direction,
which is why the lattice pitch alone cannot discharge the bound: on a 45-degree
arm one lattice row projects at p*sqrt(2), not p.

WHICH BOUND, AND WHY IT MOVED (2026-07-30).  The default used to be 1.35 mm,
the largest round value under ADR-0003's microstrip `lambda_g/20 = 1.3693`.
`line_type.py` then MEASURED the arms and they are not microstrip: a GND pour
runs alongside every arm at 0.2005 mm edge-to-edge (g/h = 0.955) over 61-93 %
of its length.  On a grounded coplanar waveguide the fence's lateral-shielding
job is already discharged by that solid pour, and the fence's real job is to
SHORT the coplanar ground to the In1.Cu reference so the parasitic
parallel-plate mode cannot propagate.  That mode fills the dielectric between
two conducting sheets, so it runs at the BULK er:

    lambda_pp = lambda_0/sqrt(er) = 49.9654/sqrt(4.4) = 23.8201 mm
    bound     = lambda_pp/20      = 1.1910 mm

which is TIGHTER than the microstrip bound it replaces.  Derivation:
`03_src/gcpw_constants.py`; decision: `01_docs/decisions/0004-*`.

EXIT CODE.  This script used to `print("VERDICT: FAIL")` and exit 0, so every
caller that checked `$?` was told the fence passed.  It now exits 1 on FAIL.
A gate that cannot block is a comment (canon: "test the checkers").

Usage: fence_pitch.py BOARD [band_mm] [bound_mm]

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
BAND = float(sys.argv[2]) if len(sys.argv) > 2 else 2.5
BOUND = float(sys.argv[3]) if len(sys.argv) > 3 else 1.1910

ARMS = ["ANT1", "ANT2", "ANT3", "ANT4", "ANT5", "ANT6", "ANT7", "RX2_OUT"]
OTHER_RF = ["RX1_MAIN", "RX1_TAP", "RX1_TAP_MID"]

bd = pcbnew.LoadBoard(BOARD)
F_CU = bd.GetLayerID("F.Cu")
mm = lambda v: v / 1e6

# A FENCE ELEMENT IS A PLATED HOLE ON GND, not only a `via` object.  Each SMA
# jack's four ground POSTS are 1.4 mm PTH pads that tie all four planes — they
# ARE the launch return path (KH-SMA-KE-Z part.yaml) and they stand exactly
# where the stitch grid's `avoid` ring forbids a via.  Counting only PCB_VIA
# reports an aperture at every launch that is in fact the densest ground in the
# board.
vias, posts = [], 0
for t in bd.GetTracks():
    if t.GetClass() == "PCB_VIA" and t.GetNetname() == "GND":
        p = t.GetPosition()
        vias.append((mm(p.x), mm(p.y)))
for fp in bd.GetFootprints():
    for pad in fp.Pads():
        if pad.GetNetname() != "GND":
            continue
        if pad.GetAttribute() != pcbnew.PAD_ATTRIB_PTH:
            continue
        if pad.GetDrillSizeX() <= 0:
            continue
        p = pad.GetPosition()
        vias.append((mm(p.x), mm(p.y)))
        posts += 1

xs = sorted({round(x, 3) for x, y in vias})
ys = sorted({round(y, 3) for x, y in vias})
print(f"board:            {BOARD}")
print(f"GND fence elements: {len(vias)}  (of which PTH GND pads/posts: {posts})")
print(f"lattice columns:  {len(xs)}   rows: {len(ys)}")
if len(xs) > 2:
    dx = sorted({round(xs[i + 1] - xs[i], 4) for i in range(len(xs) - 1)})
    dy = sorted({round(ys[i + 1] - ys[i], 4) for i in range(len(ys) - 1)})
    print(f"column pitches seen: {dx[:6]}")
    print(f"row pitches seen:    {dy[:6]}")


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
    # start at the end FARTHEST from the others -> deterministic direction
    start = sorted(ends)[0] if ends else sorted(adj)[0]
    chain, seen, cur, prev = [start], set(), start, None
    while True:
        nxt = None
        for cand in adj.get(cur, []):
            key = tuple(sorted([cur, cand]))
            if cand != prev and key not in seen:
                nxt = cand
                seen.add(key)
                break
        if nxt is None:
            break
        chain.append(nxt)
        prev, cur = cur, nxt
    return chain


def project(chain, px, py):
    """(perp distance, arclength s, side, clamped?) at the nearest foot."""
    best = None
    s0 = 0.0
    for i in range(len(chain) - 1):
        (x1, y1), (x2, y2) = chain[i], chain[i + 1]
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy)
        if L == 0:
            continue
        t = ((px - x1) * dx + (py - y1) * dy) / (L * L)
        tc = max(0.0, min(1.0, t))
        qx, qy = x1 + tc * dx, y1 + tc * dy
        d = math.hypot(px - qx, py - qy)
        cross = (dx * (py - y1) - dy * (px - x1)) / L
        # clamped at the polyline's OUTER ends = the via is BEYOND the arm
        outer = (i == 0 and t < 0.0) or (i == len(chain) - 2 and t > 1.0)
        if best is None or d < best[0]:
            best = (d, s0 + tc * L, 1 if cross >= 0 else -1, outer)
        s0 += L
    return best


def total_len(ch):
    return sum(math.hypot(ch[i + 1][0] - ch[i][0], ch[i + 1][1] - ch[i][1])
               for i in range(len(ch) - 1))


print(f"\nband = +/-{BAND} mm perpendicular to the arm copper; "
      f"vias BEYOND either end excluded; bound <= {BOUND} mm\n")
hdr = (f"{'arm':<12}{'len':>7} {'side':>4}{'n':>4}{'max gap':>9}"
       f"{'lead-in':>8}{'run-out':>8}{'offsets(mm)':>26}  verdict")
print(hdr)
worst, worst_where, rows, over = 0.0, "", 0, []
for net in ARMS + OTHER_RF:
    ch = polyline(net)
    if len(ch) < 2:
        print(f"{net:<12} NO F.Cu POLYLINE")
        continue
    L = total_len(ch)
    for side in (-1, 1):
        pts, offs = [], []
        for (vx, vy) in vias:
            r = project(ch, vx, vy)
            if r is None:
                continue
            d, s, sgn, outer = r
            if outer or d > BAND or sgn != side:
                continue
            if s <= 1e-6 or s >= L - 1e-6:
                continue
            pts.append(s)
            offs.append(d)
        order = sorted(range(len(pts)), key=lambda i: pts[i])
        pts = [pts[i] for i in order]
        offs = [offs[i] for i in order]
        tag = 'W' if side < 0 else 'E'
        if len(pts) < 2:
            print(f"{net:<12}{L:7.3f} {tag:>4}{len(pts):>4}   "
                  f"(fewer than 2 flanking vias)")
            continue
        gaps = [pts[i + 1] - pts[i] for i in range(len(pts) - 1)]
        g = max(gaps)
        gi = gaps.index(g)
        rows += 1
        if g > worst:
            worst, worst_where = g, f"{net} {tag} at s={pts[gi]:.2f}..{pts[gi+1]:.2f}"
        ok = "OK" if g <= BOUND + 1e-9 else "OVER"
        if ok == "OVER":
            over.append((net, tag, g, pts[gi], pts[gi + 1]))
        band = f"{min(offs):.2f}-{max(offs):.2f} ({len(set(round(o,2) for o in offs))} rows)"
        print(f"{net:<12}{L:7.3f} {tag:>4}{len(pts):>4}{g:9.4f}"
              f"{pts[0]:8.3f}{L - pts[-1]:8.3f}{band:>26}  {ok}")

print(f"\nWORST interior along-arm gap: {worst:.4f} mm  [{worst_where}]"
      f"   ({rows} arm-sides measured, {len(over)} OVER)")
print(f"BOUND: <= {BOUND} mm  (ARCHITECTURE sec 6 / ADR-0004: GCPW "
      f"ground-stitch, lambda_pp/20 = lambda_0/sqrt(er)/20 = 1.1910 mm)")
fail = worst > BOUND + 1e-9
if fail:
    print(f"worst = lambda_pp/{23.8201/worst:.2f}  "
          f"({worst/BOUND:.2f}x the bound)")
print("VERDICT: " + ("FAIL" if fail else "PASS"))
sys.exit(1 if fail else 0)
