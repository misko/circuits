#!/usr/bin/env python3
"""Does a LEGAL BARREL EXIST inside each over-bound fence aperture?

`fence_apertures.py` names the object NEAREST to each empty LATTICE site.  That
is a hint, not a verdict: it measures centre-to-centre distance to a pad centre
or a track MIDPOINT, and it only ever looks at the square lattice's own sites.
"occupied" is not "unstitchable", and a lattice that misses a site by 0.05 mm
looks identical to copper sitting on it.

This asks the different question, and it is the one that decides whether an
aperture needs an EXCEPTION or just a via: sweeping the CONTINUUM inside the
aperture's flank band, is there anywhere a 0.25/0.15 through via on GND can
legally stand?  Legality is judged by the SAME primitive the stitcher uses --
`pcb_toolkit.Toolkit.via_site_ok`, exact-collision against every copper layer
plus net-blind hole-to-hole -- so a site this script calls legal is a site
`route_and_stitch_generic` will accept, and one it calls illegal is refused by
the backend for the same reason.  Two design exclusions are applied ON TOP,
because they are decisions rather than clearances:

  * the ten declared SMA `avoid` rings (r = 1.90 mm about each jack's centre
    pin).  A via inside one eats the >= D3.5 mm bottom-plane antipad the
    KH-SMA-KE-Z launch calls for, so it is a return-loss defect before it is a
    DRC one -- it may not be used to close an aperture;
  * the module's carrier-facing SMD keepout rect (58.10..59.30, 73.80..86.00
    + 0.15), which the stitcher's `avoid` list also carries.

Both are READ FROM `03_src/route.yaml` rather than restated here, so the
exclusion set cannot drift from the one the stitcher obeys.

OUTPUT.  Per over-bound aperture: how many legal sites exist, the greedy
minimum set that brings every sub-gap under the bound, and -- when no such set
exists -- the best achievable sub-gap, which is the number an exception
argument would have to be made against.

Usage: fence_sites.py BOARD [band_mm] [bound_mm] [--yaml]
       --yaml emits the closing vias as a route.yaml `stitch.seed_stubs` block.

DECLARED BACKEND GAP (canon M8; 03_src/contracts.md makes any *.py beyond
audit_board/bom_seed a STOPGAP that must name its gap and the schema that would
replace it).
THE GAP: the shared stitcher has ONE via-placing search that is a board-wide
SQUARE LATTICE (`stitch.stitch_grid`).  A fence is a per-ARM structure, and a
lattice is a poor fence: its sites are placed relative to the board origin, not
to the arm, so on a 45-degree arm it both projects at p*sqrt(2) and misses
legal ground it could have used.  There is no per-arm fence pass in the backend.
THE CONFIG SCHEMA THAT WOULD REPLACE IT: `stitch.fence: {arms: [...],
offset_mm: [min,max], pitch_mm, bound_mm}` -- walk each named net's centreline,
step at `pitch_mm`, and place the first legal via in the offset window on each
side, with the same via_site_ok refusal discipline `seed_stubs` already has.
THIS IS THE SECOND BOARD TO NEED IT (pluto-rx2-8way v1 carries the same fence),
which by the contract's own rule TRIGGERS MANDATORY PROMOTION into the shared
backend.  Promotion is REPORTED to the caller and NOT done here: this agent's
partition is `projects/pluto-rx2-8way-v2/` only.
"""
import json
import math
import os
import sys

import pcbnew

sys.path.insert(0, os.path.expanduser(
    os.environ.get("KICAD_SKILL_SCRIPTS",
                   os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "../../../skills/kicad-pcb/scripts"))))
import pcb_toolkit  # noqa: E402
import yaml  # noqa: E402

BOARD = sys.argv[1]
args = [a for a in sys.argv[2:] if not a.startswith("--")]
BAND = float(args[0]) if len(args) > 0 else 2.5
BOUND = float(args[1]) if len(args) > 1 else 1.1910
EMIT_YAML = "--yaml" in sys.argv

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = yaml.safe_load(open(os.path.join(HERE, "route.yaml")))

ARMS = ["ANT1", "ANT2", "ANT3", "ANT4", "ANT5", "ANT6", "ANT7", "RX2_OUT",
        "RX1_MAIN", "RX1_TAP", "RX1_TAP_MID"]

# ---- via geometry + guards, READ FROM the stitcher's own config ------------
_st = CFG["stitch"]
VIA = _st["via"]["tiers"][0]
VS, VD = float(VIA["size"]), float(VIA["drill"])
H2C = float(VIA.get("hole_to_copper", 0.155))
CLR = float(_st.get("clearance", 0.2))
PTH_MARGIN = float(_st["via"].get("pth_margin", 0.3))
KEEPIN = float(_st.get("keepin", {}).get("inset", 0.8))
AVOID = _st["stitch_grid"].get("avoid", []) or []
# offset window: nearer than 0.5 mm the barrel cannot clear a 0.36 mm arm at
# 0.20 mm clearance anyway (0.18 + 0.20 + 0.125 = 0.505), and the band ceiling
# is the measurement band itself.
OFF_MIN, OFF_MAX = 0.51, BAND
STEP_S, STEP_D = 0.05, 0.05

bd = pcbnew.LoadBoard(BOARD)
F_CU = bd.GetLayerID("F.Cu")
mm = lambda v: v / 1e6
GND = bd.FindNet("GND")
GNDC = GND.GetNetCode()
tk = pcb_toolkit.Toolkit(bd, CLR)

# board outline bbox for the keep-in inset
bb = bd.GetBoardEdgesBoundingBox()
X0, Y0 = mm(bb.GetX()) + KEEPIN, mm(bb.GetY()) + KEEPIN
X1, Y1 = mm(bb.GetRight()) - KEEPIN, mm(bb.GetBottom()) - KEEPIN

# ---- fence elements: GND vias AND PTH GND pads (the SMA posts) -------------
elems, posts = [], 0
for t in bd.GetTracks():
    if t.GetClass() == "PCB_VIA" and t.GetNetname() == "GND":
        p = t.GetPosition()
        elems.append((mm(p.x), mm(p.y)))
for fp in bd.GetFootprints():
    for pad in fp.Pads():
        if (pad.GetNetname() == "GND"
                and pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
                and pad.GetDrillSizeX() > 0):
            p = pad.GetPosition()
            elems.append((mm(p.x), mm(p.y)))
            posts += 1

# PTH pads, for the stitcher's board-wide pth_margin guard
pths = []
for fp in bd.GetFootprints():
    for pad in fp.Pads():
        if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and pad.GetDrillSizeX() > 0:
            p = pad.GetPosition()
            pths.append((mm(p.x), mm(p.y), mm(pad.GetDrillSizeX()) / 2.0))


def in_avoid(x, y):
    for a in AVOID:
        x0, y0 = float(a["x0"]), float(a["y0"])
        x1, y1 = float(a["x1"]), float(a["y1"])
        m = float(a.get("margin", 0.0))
        if (min(x0, x1) - m <= x <= max(x0, x1) + m
                and min(y0, y1) - m <= y <= max(y0, y1) + m):
            if x0 == x1 and y0 == y1:          # a RING, not a rect
                if math.hypot(x - x0, y - y0) <= m:
                    return True
            else:
                return True
    return False


def pth_ok(x, y):
    for px, py, pr in pths:
        if math.hypot(x - px, y - py) < pr + VS / 2.0 + PTH_MARGIN:
            return False
    return True


def legal(x, y):
    if not (X0 <= x <= X1 and Y0 <= y <= Y1):
        return False
    if in_avoid(x, y) or not pth_ok(x, y):
        return False
    return tk.via_site_ok(x, y, GNDC, size=VS, drill=VD, hole_to_copper=H2C)


def polyline(net):
    segs = []
    for t in bd.GetTracks():
        if (t.GetClass() != "PCB_TRACK" or t.GetNetname() != net
                or t.GetLayer() != F_CU):
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


def frame(chain, s):
    """(x, y, unit tangent, unit normal) at arclength s."""
    s0 = 0.0
    for i in range(len(chain) - 1):
        (x1, y1), (x2, y2) = chain[i], chain[i + 1]
        L = math.hypot(x2 - x1, y2 - y1)
        if L == 0:
            continue
        if s <= s0 + L or i == len(chain) - 2:
            t = (s - s0) / L
            tx, ty = (x2 - x1) / L, (y2 - y1) / L
            return x1 + t * (x2 - x1), y1 + t * (y2 - y1), tx, ty, -ty, tx
        s0 += L
    return chain[-1][0], chain[-1][1], 1, 0, 0, 1


def total_len(ch):
    return sum(math.hypot(ch[i + 1][0] - ch[i][0], ch[i + 1][1] - ch[i][1])
               for i in range(len(ch) - 1))


def report():
  print(f"board: {BOARD}")
  print(f"fence elements: {len(elems)} ({posts} PTH GND posts); "
        f"band +/-{BAND} mm; bound <= {BOUND} mm")
  print(f"probe via {VS}/{VD} mm, clearance {CLR}, hole_to_copper {H2C}, "
        f"pth_margin {PTH_MARGIN}, keepin {KEEPIN}; "
        f"{len(AVOID)} declared avoid regions EXCLUDED\n")

  total_over, closable, residual, emit = 0, 0, [], []
  CACHE = []
  for net in ARMS:
      ch = polyline(net)
      if len(ch) < 2:
          continue
      L = total_len(ch)
      for side in (-1, 1):
          tag = "W" if side < 0 else "E"
          pts = []
          for (vx, vy) in elems:
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
              total_over += 1
              s1, s2 = pts[i], pts[i + 1]
              # sweep the continuum inside the aperture's flank band
              sites = []
              n = int((s2 - s1) / STEP_S)
              for a in range(1, n + 1):
                  s = s1 + a * STEP_S
                  if s >= s2:
                      break
                  x, y, tx, ty, nx, ny = frame(ch, s)
                  d = OFF_MIN
                  while d <= OFF_MAX + 1e-9:
                      px, py = x + side * nx * d, y + side * ny * d
                      if legal(px, py):
                          # re-project: the offset point's true arclength
                          r = project(ch, px, py)
                          if r and not r[3] and r[2] == side and r[0] <= BAND:
                              sites.append((r[1], round(px, 3), round(py, 3),
                                            round(r[0], 3)))
                      d += STEP_D
              # A SITE IS ONLY A CANDIDATE FOR *THIS* APERTURE IF ITS OWN
              # PROJECTED ARCLENGTH LANDS INSIDE IT.  The sweep steps `s` along
              # the centreline and then offsets laterally, and on a polyline
              # with a kink the offset point re-projects to a DIFFERENT `s` —
              # sometimes outside (s1, s2) entirely.  Keeping those made
              # `allmarks` non-monotonic and produced negative/garbage
              # "gaps": ANT1 sideE reported 182 legal sites and a best
              # achievable equal to the untouched gap, which is the signature
              # of an unsorted difference list, not of blocked copper.
              sites = sorted(z for z in sites if s1 < z[0] < s2)
              # THE BEST ACHIEVABLE SUB-GAP IS NOT A GREEDY OUTCOME, it is a
              # property of the legal-site SET: adding a via can never widen a
              # gap, so taking EVERY legal site is minimax-optimal and its worst
              # consecutive spacing is the floor no placement can beat.  (An
              # earlier revision walked greedily from s1 and ABORTED the whole
              # aperture the first time a window held no site, then reported the
              # ORIGINAL gap as "best achievable" — which overstated ANT5 sideE
              # at 2.6123 mm when the true floor is set by one blocked stretch.
              # A search that gives up must not be allowed to publish its
              # give-up point as a physical limit.)
              allmarks = sorted([s1] + [z[0] for z in sites] + [s2])
              best_possible = max(allmarks[j + 1] - allmarks[j]
                                  for j in range(len(allmarks) - 1))
              CACHE.append({"net": net, "side": tag, "s1": s1, "s2": s2,
                            "gap": g, "best_possible": best_possible,
                            "sites": [list(z) for z in sites]})
              ok = best_possible <= BOUND + 1e-9
              thresh = BOUND if ok else best_possible
              # then MINIMISE THE COUNT at that threshold: farthest site still
              # within `thresh`, and when even that is empty, step to the next
              # site beyond it (the blocked stretch) and carry on.
              chosen, cur = [], s1
              while s2 - cur > thresh + 1e-9:
                  cand = [z for z in sites if cur < z[0] <= cur + thresh + 1e-9]
                  if cand:
                      pick = cand[-1]
                  else:
                      nxt = [z for z in sites if z[0] > cur]
                      if not nxt:
                          break
                      pick = nxt[0]
                  chosen.append(pick)
                  cur = pick[0]
              marks = [s1] + [z[0] for z in chosen] + [s2]
              worst_after = max(marks[j + 1] - marks[j]
                                for j in range(len(marks) - 1))
              print(f"{net} side{tag}  GAP {g:.4f} mm  s={s1:.2f}..{s2:.2f}"
                    f"   legal sites in band: {len(sites)}")
              if ok:
                  closable += 1
                  for z in chosen:
                      print(f"    + via ({z[1]:.3f}, {z[2]:.3f})  "
                            f"s={z[0]:.2f} off={z[3]:.2f}")
                      emit.append((net, tag, z[1], z[2]))
                  print(f"    => CLOSABLE with {len(chosen)} via(s); "
                        f"worst sub-gap {worst_after:.4f} <= {BOUND}")
              else:
                  for z in chosen:
                      print(f"    + via ({z[1]:.3f}, {z[2]:.3f})  "
                            f"s={z[0]:.2f} off={z[3]:.2f}")
                      emit.append((net, tag, z[1], z[2]))
                  print(f"    => NOT CLOSABLE: best achievable sub-gap "
                        f"{worst_after:.4f} mm ({worst_after/BOUND:.2f}x bound)"
                        f"  [{len(chosen)} via(s) still help]")
                  residual.append((net, tag, s1, s2, g, worst_after, len(sites)))
              print()

  print(f"\napertures over bound: {total_over}   fully closable by added vias: "
        f"{closable}   residual: {len(residual)}")
  for net, tag, s1, s2, g, w, ns in residual:
      print(f"  RESIDUAL {net} side{tag} s={s1:.2f}..{s2:.2f}  "
            f"{g:.4f} -> {w:.4f} mm  ({ns} legal sites in band)")
  print(f"total vias proposed: {len(emit)}")

  json.dump(CACHE, open("06_build/verify/fence_sites.json", "w"), indent=1)
  print("legal-site cache -> 06_build/verify/fence_sites.json")

  if EMIT_YAML:
      print("\n# --- paste under stitch.seed_stubs.stubs ---")
      for net, tag, x, y in emit:
          print(f"      - {{net: GND, vias: [[{x}, {y}]]}}   # fence {net} {tag}")


if __name__ == "__main__":
    report()
