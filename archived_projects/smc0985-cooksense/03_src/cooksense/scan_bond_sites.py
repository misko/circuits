#!/usr/bin/env /usr/bin/python3
"""MAX-GROWTH on-pad via site scan for the TRAPPED-PLANE-PAD class.

WHY THIS EXISTS, and why it is not a proximity search
-----------------------------------------------------
`route.yaml`'s ~20 deterministic-bond precedents state the method in prose and
then re-state the reason it had to be corrected once already:

    "SITES CHOSEN BY MAX GROWTH, NOT BY PROXIMITY ... Picking the NEAREST legal
     site gave exactly that: Q_SWDRVB.2 at 0.140 mm off centre and U_TC.5 at
     0.020 mm both scored growth 0.00 — legal by nothing."

Slack is the property that survives a re-route; distance to the pad centre is
not. So every on-pad point is scored by how far a via could GROW there and
still be legal, and the winner is the max-growth site (nearest-to-centre only
breaks ties).

THE PRIMITIVE IS THE PASS'S OWN, DELIBERATELY
---------------------------------------------
Sites are graded with `pcb_toolkit.Toolkit.via_site_ok` at exactly the
parameters `route_and_stitch_generic.py seed_stubs` will re-check them with
(`route.yaml: seed_stubs.clearance: 0.13`, via 0.25/0.15) — so a site this
scanner accepts is a site seed_stubs does not REFUSE. That deliberately shares
a method with the placer, which is why it is NOT the gate: the gate is
`kicad-cli pcb drc --severity-all --refill-zones --schematic-parity` on the
rebuilt board, which shares no method with either (canon M1).

CONTROLS (`--control`)
----------------------
via_site_ok is trusted here, so the scan is checked at both ends before use:
  * POSITIVE — a coordinate already committed in route.yaml and DRC-clean on
    this board must score LEGAL with growth > 0.
  * NEGATIVE — the same coordinate probed on a FOREIGN net's netcode must be
    REFUSED (its own via is then no longer same-net-exempt), and a point on a
    foreign track's centreline must be REFUSED.
A scan that cannot say NO cannot say YES.

usage:
  scan_bond_sites.py BOARD REF.PAD [REF.PAD ...]      # scan
  scan_bond_sites.py BOARD --control                  # self-test
"""
import math
import os
import sys

import pcbnew

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..",
    "skills", "kicad-pcb", "scripts"))
from pcb_toolkit import Toolkit                                # noqa: E402

MM = pcbnew.ToMM
CLEARANCE = 0.13        # route.yaml seed_stubs.clearance
VIA_SIZE = 0.25         # advanced-tier via, as seed_stubs derives it
VIA_DRILL = 0.15
STEP = 0.02             # scan pitch, mm (small pads)
COARSE_STEP = 0.05      # scan pitch for pads wider than COARSE_OVER mm
COARSE_OVER = 1.00
GROW_STEP = 0.05        # growth sweep pitch, mm
GROW_CAP = 1.50

# COST NOTE, measured rather than guessed. A naive implementation ran >10 min on
# the 1.5 mm TestPoint pad and was killed. The cost is `hole_to_hole_ok`, which
# walks EVERY drilled hole on the board (~1.5k) on every call — and it is a
# function of (x, y, drill) ONLY, never of the via's outer SIZE. So it is
# evaluated ONCE per candidate point (in the legality test) and the growth sweep
# runs with `hole_to_hole=0`, which is exact, not an approximation: growing the
# annular ring cannot change a drill-edge-to-drill-edge distance.


def _pad(board, spec):
    ref, _, num = spec.partition(".")
    fp = board.FindFootprintByReference(ref)
    if fp is None:
        sys.exit(f"no footprint {ref!r}")
    for p in fp.Pads():
        if p.GetNumber() == num:
            return p
    sys.exit(f"{ref} has no pad {num!r}")


def growth(tk, x, y, code):
    """Largest legal via SIZE at (x, y) minus the 0.25 design size.

    `hole_to_hole=0`: the drill is fixed at VIA_DRILL through the whole sweep,
    so the hole-to-hole verdict cannot change with size. It is evaluated once,
    by the caller's legality test."""
    s = VIA_SIZE
    while s + GROW_STEP <= GROW_CAP:
        if not tk.via_site_ok(x, y, code, size=s + GROW_STEP, drill=VIA_DRILL,
                              hole_to_hole=0):
            break
        s += GROW_STEP
    return round(s - VIA_SIZE, 3)


def _barrel_inside(pad, x, y):
    """Is the whole 0.25 mm via ANNULUS inside the pad's own copper?

    `pad.HitTest(centre)` — what the precedents used — only proves the CENTRE is
    on copper, so a max-growth site can land with half the barrel hanging off a
    SOT-23 pad's tip. Clearance-wise that is fine (same net); as a SOLDER JOINT
    it is not, which is the objection route.yaml already raised against a 0.075 mm
    annulus on U_TC.8's 0.400 mm-wide pad. Checked on 8 rays so an oblong pad's
    corners cannot pass by luck."""
    r = VIA_SIZE / 2.0
    d = r * 0.70710678
    for dx, dy in ((r, 0), (-r, 0), (0, r), (0, -r),
                   (d, d), (d, -d), (-d, d), (-d, -d)):
        if not pad.HitTest(pcbnew.VECTOR2I_MM(x + dx, y + dy)):
            return False
    return True


def scan(board, tk, spec, inside=False):
    pad = _pad(board, spec)
    code = pad.GetNetCode()
    bb = pad.GetBoundingBox()
    x0, x1 = MM(bb.GetLeft()), MM(bb.GetRight())
    y0, y1 = MM(bb.GetTop()), MM(bb.GetBottom())
    cx, cy = MM(pad.GetPosition().x), MM(pad.GetPosition().y)
    best, legal, oncopper = None, 0, 0
    step = COARSE_STEP if max(x1 - x0, y1 - y0) > COARSE_OVER else STEP
    nx = int(round((x1 - x0) / step)) + 1
    ny = int(round((y1 - y0) / step)) + 1
    for i in range(nx):
        for j in range(ny):
            x, y = round(x0 + i * step, 4), round(y0 + j * step, 4)
            if not pad.HitTest(pcbnew.VECTOR2I_MM(x, y)):
                continue
            if inside and not _barrel_inside(pad, x, y):
                continue
            oncopper += 1
            if not tk.via_site_ok(x, y, code, size=VIA_SIZE, drill=VIA_DRILL):
                continue
            legal += 1
            g = growth(tk, x, y, code)
            off = math.hypot(x - cx, y - cy)
            key = (g, -round(off, 4))
            if best is None or key > best[0]:
                best = (key, x, y, g, off)
    print(f"{spec:<14} net={pad.GetNetname():<6} pad {MM(pad.GetSize(pcbnew.F_Cu).x):.3f}x"
          f"{MM(pad.GetSize(pcbnew.F_Cu).y):.3f} centre ({cx:.4f},{cy:.4f})  "
          f"grid {step:.2f}mm, {oncopper} "
          f"{'barrel-inside' if inside else 'on-copper'} points, {legal} LEGAL")
    if best is None:
        print(f"{'':<14} -> NO LEGAL ON-PAD SITE (needs an off-pad stub, "
              f"the U_TC.8 pattern)")
        return None
    _, x, y, g, off = best
    print(f"{'':<14} -> BEST ({x:.4f}, {y:.4f})  growth {g:.2f}  "
          f"off-centre {off:.3f}"
          + ("  [PAD CENTRE]" if off < 1e-6 else ""))
    return x, y, g, off


def control(board, tk):
    """Positive and negative controls. Exits non-zero if either fails."""
    ok = True
    gnd = board.GetNetsByName()["GND"].GetNetCode()
    v3 = board.GetNetsByName()["3V3"].GetNetCode()
    # POSITIVE: committed route.yaml bonds, present and DRC-clean on this board.
    for name, x, y, code in (("R_AND1PD.2 [GND]", 157.8000, 70.6600, gnd),
                             ("C_AND3.2 [GND]", 183.9800, 70.6000, gnd),
                             ("U_LATCHB.5 [3V3]", 182.8375, 73.3500, v3)):
        good = tk.via_site_ok(x, y, code, size=VIA_SIZE, drill=VIA_DRILL)
        g = growth(tk, x, y, code) if good else None
        print(f"CONTROL+ {name:<18} ({x},{y}) -> "
              f"{'LEGAL growth %.2f' % g if good else 'REFUSED'}")
        if not good or g <= 0:
            ok = False
    # NEGATIVE 1: the same GND coordinates probed as 3V3 — the GND via that is
    # actually there stops being same-net-exempt, so the site must be REFUSED.
    for name, x, y in (("R_AND1PD.2 site as 3V3", 157.8000, 70.6600),
                       ("C_AND3.2 site as 3V3", 183.9800, 70.6000)):
        bad = tk.via_site_ok(x, y, v3, size=VIA_SIZE, drill=VIA_DRILL)
        print(f"CONTROL- {name:<18} -> {'LEGAL (WRONG)' if bad else 'REFUSED'}")
        if bad:
            ok = False
    # NEGATIVE 2: a point on a foreign track's centreline.
    for t in board.GetTracks():
        if (t.GetClass() == "PCB_TRACK" and t.GetNetCode() not in (gnd, 0)
                and t.GetLayer() == pcbnew.F_Cu):
            mx = MM((t.GetStart().x + t.GetEnd().x) / 2)
            my = MM((t.GetStart().y + t.GetEnd().y) / 2)
            bad = tk.via_site_ok(mx, my, gnd, size=VIA_SIZE, drill=VIA_DRILL)
            print(f"CONTROL- GND via on {t.GetNetname()} centreline "
                  f"({mx:.3f},{my:.3f}) -> "
                  f"{'LEGAL (WRONG)' if bad else 'REFUSED'}")
            if bad:
                ok = False
            break
    print("CONTROLS:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    board = pcbnew.LoadBoard(sys.argv[1])
    tk = Toolkit(board, CLEARANCE)
    if "--control" in sys.argv[2:]:
        sys.exit(control(board, tk))
    inside = "--inside" in sys.argv[2:]
    for spec in sys.argv[2:]:
        if spec.startswith("--"):
            continue
        scan(board, tk, spec, inside=inside)


main()
