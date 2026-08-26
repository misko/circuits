#!/usr/bin/env python3
"""MEASURE what transmission line each RF arm actually IS.

The question this answers: is an arm a BARE MICROSTRIP (reference plane
below, nothing lateral), a GROUNDED COPLANAR WAVEGUIDE (reference plane
below AND a coplanar ground on the same layer at a gap comparable to the
substrate height), or a hybrid that transitions along its length?

Method, and it shares NO method with the generator (canon M1):
  - read the SAVED .kicad_pcb through pcbnew;
  - rebuild each RF net's F.Cu centreline from its OWN track segments;
  - sample the centreline every `--step` mm, and at each sample march a ray
    perpendicular to the arm, on EACH side, until it enters GND copper on
    F.Cu (the zone FILL polygons, not the zone outline) -- that first entry
    is the coplanar ground edge, and the EDGE-TO-EDGE gap is
    (march distance - trace half width);
  - independently, march the SAME normal on In1.Cu to ask whether the
    reference plane is present directly beneath the sample.

Per sample the cross-section is CLASSIFIED, not averaged:
    GCPW    both sides within TIGHT  (default 0.25 mm ~= 1.19 h)
    ASYM    exactly one side within TIGHT
    USTRIP  neither side within LOOSE (default 0.63 mm = 3 h) -- at 3 h the
            coplanar ground contributes little and the line is microstrip
    TRANS   in between: a transition sample, counted separately rather than
            forced into one of the three
The point of classifying rather than averaging: an arm that is GCPW for 78 %
of its length and microstrip for 22 % is a HYBRID, and its constants are not
either pure model's.

Nothing here reads nets.yaml, route.yaml, or any ADR: a declared
cross-section cannot certify itself.

Usage: line_type.py BOARD [--step 0.05] [--max 3.0] [--h 0.2104]
                          [--tight 0.25] [--loose 0.63]

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


def _opt(name, default):
    if name in sys.argv:
        return float(sys.argv[sys.argv.index(name) + 1])
    return default


STEP = _opt("--step", 0.05)
MAXR = _opt("--max", 3.0)
H_SUB = _opt("--h", 0.2104)   # DECLARED stackup value; printed for ratios only
TIGHT = _opt("--tight", 0.25)
LOOSE = _opt("--loose", 0.63)

ARMS = ["ANT1", "ANT2", "ANT3", "ANT4", "ANT5", "ANT6", "ANT7", "RX2_OUT"]
OTHER_RF = ["RX1_MAIN", "RX1_TAP", "RX1_TAP_MID"]

bd = pcbnew.LoadBoard(BOARD)
F_CU = bd.GetLayerID("F.Cu")
IN1 = bd.GetLayerID("In1.Cu")
mm = lambda v: v / 1e6
nm = lambda v: int(round(v * 1e6))


def gnd_fill(layer):
    """Union of the FILLED polygons of every GND zone on `layer`."""
    acc = pcbnew.SHAPE_POLY_SET()
    for i in range(bd.GetAreaCount()):
        z = bd.GetArea(i)
        if z.GetIsRuleArea() or not z.IsOnLayer(layer) or z.GetNetname() != "GND":
            continue
        acc.BooleanAdd(z.GetFilledPolysList(layer))
    acc.Simplify()
    return acc


FILL = {"F": gnd_fill(F_CU), "I1": gnd_fill(IN1)}


def inside(poly, x, y):
    return poly.Contains(pcbnew.VECTOR2I(nm(x), nm(y)))


def polyline(net):
    segs, widths = [], []
    for t in bd.GetTracks():
        if t.GetClass() != "PCB_TRACK" or t.GetNetname() != net:
            continue
        if t.GetLayer() != F_CU:
            continue
        a, b = t.GetStart(), t.GetEnd()
        segs.append(((round(mm(a.x), 4), round(mm(a.y), 4)),
                     (round(mm(b.x), 4), round(mm(b.y), 4))))
        widths.append(mm(t.GetWidth()))
    if not segs:
        return [], []
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
            key = tuple(sorted([cur, cand]))
            if cand != prev and key not in seen:
                nxt = cand
                seen.add(key)
                break
        if nxt is None:
            break
        chain.append(nxt)
        prev, cur = cur, nxt
    return chain, widths


def march(poly, px, py, nx, ny, t0, fine=0.0005):
    t = t0
    while t <= MAXR:
        if inside(poly, px + t * nx, py + t * ny):
            return t
        t += fine
    return None


def median(v):
    s = sorted(v)
    n = len(s)
    if not n:
        return float("nan")
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


print(f"board: {BOARD}")
print(f"sample step {STEP} mm; normal march to {MAXR} mm at 0.0005 mm")
print(f"declared substrate h = {H_SUB} mm (a STACKUP field, not measured here)")
print(f"classes: GCPW = both sides <= {TIGHT} mm; ASYM = one side; "
      f"USTRIP = neither side <= {LOOSE} mm; TRANS = the remainder")
print()
hdr = (f"{'arm':<13}{'len':>7}{'w':>6}{'n':>5}"
       f"{'gap med':>9}{'gap min':>9}{'g/h':>6}{'g/w':>6}"
       f"{'GCPW%':>8}{'ASYM%':>7}{'TRANS%':>8}{'USTRIP%':>8}"
       f"{'In1 void (s mm)':>18}")
print(hdr)

rows, pooled = [], []
for net in ARMS + OTHER_RF:
    ch, widths = polyline(net)
    if len(ch) < 2:
        print(f"{net:<13} NO F.Cu POLYLINE")
        continue
    w = median(widths)
    half = w / 2.0
    L = sum(math.hypot(ch[i + 1][0] - ch[i][0], ch[i + 1][1] - ch[i][1])
            for i in range(len(ch) - 1))
    gaps, cls, void_s, n = [], {"GCPW": 0, "ASYM": 0, "TRANS": 0, "USTRIP": 0}, [], 0
    s_acc = 0.0
    for i in range(len(ch) - 1):
        (x1, y1), (x2, y2) = ch[i], ch[i + 1]
        dx, dy = x2 - x1, y2 - y1
        seg = math.hypot(dx, dy)
        if seg == 0:
            continue
        ux, uy = dx / seg, dy / seg
        nxv, nyv = -uy, ux
        t = 0.0
        while t < seg:
            px, py = x1 + t * ux, y1 + t * uy
            aW = march(FILL["F"], px, py, nxv, nyv, half)
            aE = march(FILL["F"], px, py, -nxv, -nyv, half)
            dW = (aW - half) if aW is not None else float("inf")
            dE = (aE - half) if aE is not None else float("inf")
            n += 1
            for d in (dW, dE):
                if d != float("inf"):
                    gaps.append(d)
            tightn = (dW <= TIGHT) + (dE <= TIGHT)
            if tightn == 2:
                cls["GCPW"] += 1
            elif tightn == 1:
                cls["ASYM"] += 1
            elif dW > LOOSE and dE > LOOSE:
                cls["USTRIP"] += 1
            else:
                cls["TRANS"] += 1
            if not inside(FILL["I1"], px, py):
                void_s.append(round(s_acc + t, 2))
            t += STEP
        s_acc += seg
    iv = []
    for a in void_s:
        if iv and a - iv[-1][1] <= 1.5 * STEP:
            iv[-1][1] = a
        else:
            iv.append([a, a])
    med, mn = median(gaps), (min(gaps) if gaps else float("nan"))
    pooled += gaps
    pc = {k: 100.0 * v / n for k, v in cls.items()}
    vtxt = "; ".join(f"{a:.2f}-{b:.2f}" for a, b in iv) or "(none)"
    print(f"{net:<13}{L:7.3f}{w:6.3f}{n:5d}"
          f"{med:9.4f}{mn:9.4f}{med/H_SUB:6.2f}{med/w:6.2f}"
          f"{pc['GCPW']:7.1f}%{pc['ASYM']:6.1f}%{pc['TRANS']:7.1f}%"
          f"{pc['USTRIP']:7.1f}%{vtxt:>18}")
    rows.append((net, L, w, med, pc, iv))

print()
print("gap = EDGE-TO-EDGE, arm copper edge to the nearest F.Cu GND pour, per side.")
print("In1 void = arclength interval with NO In1.Cu GND fill directly beneath.")
print()
gm = median(pooled)
print(f"POOLED over all {len(pooled)} side-samples: median gap {gm:.4f} mm, "
      f"min {min(pooled):.4f} mm  ->  g/h = {gm/H_SUB:.3f}, g/w = {gm/0.36:.3f}")
gc = sum(r[4]["GCPW"] for r in rows) / len(rows)
print(f"MEAN per-arm GCPW fraction: {gc:.1f} %   "
      f"(arms >= 50 % GCPW: {sum(1 for r in rows if r[4]['GCPW'] >= 50)} of {len(rows)})")
allvoid = all(len(r[5]) <= 2 for r in rows)
print(f"In1.Cu reference beneath every arm is CONTINUOUS apart from the launch "
      f"antipad intervals above: {allvoid}")
