#!/usr/bin/env /usr/bin/python3
"""INDEPENDENT re-derivation of the 10 per-LCSC CPL rotations on this board.

Canon M1: this must NOT share a method with the tool that produced the defect.
So it imports NOTHING from jlc_twin / jlc_rotation_resolve / export_jlc_package:
  * OUR pads come from pcbnew (the board itself),
  * JLC's pads come from a plain TEXT parse of JLC's cached `.kicad_mod`
    (easyeda2kicad output, no pcbnew, no jlc_twin loader),
  * the rotation operator is DERIVED and then PROVEN against pcbnew on this
    board's own footprints before it is used for anything.

Metric: pad sets matched by pad NUMBER, centroid-aligned (so translation
cannot smear the answer), scored by RMS residual at each of 0/90/180/270.
Reports the best angle and the runner-up so the separation is visible.

    rot_remeasure.py BOARD.kicad_pcb <twin_outdir>/easyeda fab/cpl.csv
    exit 0 = every checked ref's shipped CPL rotation equals board_rot + the
             independently fitted offset; exit 1 = at least one mismatch.

STOPGAP (canon M8) — THE GAP THIS NAMES. There is no shared release gate that
re-derives CPL rotations independently of `jlc_twin`. The canon calls it
**A-ROT** and it is HELD (skills/pcb-design/templates/03_src/rules/assembly.yaml
"A-ROT — PLANNED, held 2026-07-25"): it was held precisely because
`jlc_twin.xform()` had a handedness bug that negated every reported offset, so
no gate built on `jlc_offset` — or on a table populated from it — could object
to its own error. crow-recorder-central-v2 v1.3 sealed green and 180 deg wrong
on that evidence. This script is the missing measurement, written per-board
because the gate does not exist yet.

THE CONFIG SCHEMA THAT WOULD REPLACE IT: A-ROT reads
`03_src/rules/assembly.yaml` for the population set (`not_assembled:` +
`consigned:` supply the coded-but-unplaced refs) and grades EVERY CPL row —
not the hand-listed REFS below — with this same pcbnew-proven operator,
emitting `verification/rotation_audit.txt`. Promote this file into
`skills/jlcpcb-fab/scripts/` (with the operator proof as a RED-verified test,
alongside `t1_jlc_twin.t_xform_matches_pcbnew`) on the SECOND board that needs
it; delete this copy then.

RESIDUAL ORACLE, stated because it is real (2026-07-25 fresh-lens finding F12b):
this script and `jlc_twin` read the SAME cached JLC `.kicad_mod` files, produced
by easyeda2kicad. Re-parsing them as text defeats a PARSER bug, not a CONVERSION
bug, and the whole answer rests on JLC's pad NUMBERING being faithful — pad
numbering is the only thing that breaks the 180 deg symmetry of a TQFP/TSSOP/
SOIC land. That residual is closed only by a human eyeballing the pin-1 dot in
JLC's own placement preview, which ORDER_README section 3a makes BLOCKING.
"""
import math
import re
import sys
from pathlib import Path

import pcbnew

BOARD = sys.argv[1]
CACHE = Path(sys.argv[2])          # <twin outdir>/easyeda
CPL = Path(sys.argv[3])

REFS = {"U1": "C6938291", "U2": "C181312", "U3": "C181312",
        "U5": "C82317", "U7": "C5224055", "U8": "C5224055",
        "D_USB": "C90627", "Q1": "C15127", "Q2": "C20917", "U9": "C79924"}

bd = pcbnew.LoadBoard(BOARD)
NM = 1e6


# ---------------------------------------------------------------- operator
def op(x, y, ang):
    """KiCad's footprint-pad rotation, y-down frame. PROVEN below."""
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return (x * c + y * s, -x * s + y * c)


def prove_operator():
    """pad.GetPosition() == fp.GetPosition() + op(pad.GetFPRelativePosition()).
    Run over EVERY pad of EVERY footprint on the board, bucketed by angle."""
    err = {}
    for fp in bd.GetFootprints():
        ang = fp.GetOrientationDegrees() % 360
        fx, fy = fp.GetPosition().x / NM, fp.GetPosition().y / NM
        for pad in fp.Pads():
            r = pad.GetFPRelativePosition()
            px, py = op(r.x / NM, r.y / NM, ang)
            ax, ay = pad.GetPosition().x / NM, pad.GetPosition().y / NM
            e = math.hypot(fx + px - ax, fy + py - ay)
            k = round(ang, 3)
            err[k] = max(err.get(k, 0.0), e)
    return err


# ------------------------------------------------------- JLC .kicad_mod
PAD_RE = re.compile(
    r'\(pad\s+(?:"([^"]*)"|(\S+))\s+\S+\s+\S+\s*\(at\s+([-\d.]+)\s+([-\d.]+)',
    re.S)


def jlc_pads(code):
    d = CACHE / code / "jlc.pretty"
    mods = sorted(d.glob("*.kicad_mod"))
    if not mods:
        return None, None
    txt = mods[0].read_text()
    out = {}
    for nq, nb, x, y in PAD_RE.findall(txt):
        out.setdefault(nq or nb, []).append((float(x), float(y)))
    return out, mods[0].name


def our_pads(ref):
    for fp in bd.GetFootprints():
        if fp.GetReference() == ref:
            out = {}
            for pad in fp.Pads():
                r = pad.GetFPRelativePosition()
                out.setdefault(pad.GetNumber(), []).append(
                    (r.x / NM, r.y / NM))
            return out, fp.GetOrientationDegrees() % 360, fp.GetFPIDAsString()
    return None, None, None


def rms(ours, jlc, ang):
    """Centroid-aligned RMS over pad NUMBERS common to both, using only pad
    names that appear exactly once on each side (duplicate-numbered thermal
    pads / paste windows carry no correspondence)."""
    common = [k for k in (set(ours) & set(jlc))
              if len(ours[k]) == 1 and len(jlc[k]) == 1 and k.strip()]
    if len(common) < 2:
        return None, 0
    a = [ours[k][0] for k in common]
    b = [op(*jlc[k][0], ang) for k in common]
    ca = (sum(p[0] for p in a) / len(a), sum(p[1] for p in a) / len(a))
    cb = (sum(p[0] for p in b) / len(b), sum(p[1] for p in b) / len(b))
    s = sum((ax - ca[0] - (bx - cb[0])) ** 2 + (ay - ca[1] - (by - cb[1])) ** 2
            for (ax, ay), (bx, by) in zip(a, b))
    return math.sqrt(s / len(a)), len(common)


cpl = {}
for line in CPL.read_text().splitlines()[1:]:
    f = line.split(",")
    if len(f) >= 7:
        cpl[f[0]] = f[6]

print("== OPERATOR PROOF (this board, pcbnew as the oracle) ==")
for ang, e in sorted(prove_operator().items()):
    print(f"   board angle {ang:6.1f} deg : max |pcbnew - operator| = {e:.9f} mm")
print("   (the NEGATED form is the pre-fix jlc_twin.xform; shown for contrast)")
neg_err = {}
for fp in bd.GetFootprints():
    ang = fp.GetOrientationDegrees() % 360
    fx, fy = fp.GetPosition().x / NM, fp.GetPosition().y / NM
    for pad in fp.Pads():
        r = pad.GetFPRelativePosition()
        c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        x, y = r.x / NM, r.y / NM
        px, py = (x * c - y * s, x * s + y * c)
        ax, ay = pad.GetPosition().x / NM, pad.GetPosition().y / NM
        k = round(ang, 3)
        neg_err[k] = max(neg_err.get(k, 0.0),
                         math.hypot(fx + px - ax, fy + py - ay))
for ang, e in sorted(neg_err.items()):
    print(f"   board angle {ang:6.1f} deg : max |pcbnew - NEGATED| = {e:.9f} mm")

print("\n== PER-PART FIT (ours vs JLC's cached land, matched by pad NUMBER) ==")
print(f"{'ref':7s} {'lcsc':11s} {'brd':>5s} {'n':>4s}  "
      f"{'best':>5s} {'rms_mm':>9s}  {'next':>5s} {'rms_mm':>9s} "
      f"{'sep':>7s}  {'CPL':>6s} {'shipped':>8s} ok")
bad = 0
for ref, code in REFS.items():
    ours, brot, fpid = our_pads(ref)
    jlc, modname = jlc_pads(code)
    if ours is None or jlc is None:
        print(f"{ref:7s} {code:11s}  NO DATA (ours={ours is not None} "
              f"jlc={jlc is not None})")
        bad += 1
        continue
    scored = []
    for ang in (0, 90, 180, 270):
        r, n = rms(ours, jlc, ang)
        if r is not None:
            scored.append((r, ang, n))
    scored.sort()
    (r0, a0, n0), (r1, a1, _) = scored[0], scored[1]
    want = (brot + a0) % 360
    got = cpl.get(ref, "?")
    ok = abs(float(got) - want) < 0.01 if got not in ("?", "") else False
    if not ok:
        bad += 1
    sep = (r1 / r0) if r0 > 1e-9 else float("inf")
    print(f"{ref:7s} {code:11s} {brot:5.0f} {n0:4d}  {a0:5.0f} {r0:9.4f}  "
          f"{a1:5.0f} {r1:9.4f} {sep:6.0f}x  {want:6.1f} {got:>8s} "
          f"{'OK' if ok else 'MISMATCH'}")

print(f"\nrows checked: {len(REFS)}   mismatches vs shipped fab/cpl.csv: {bad}")
sys.exit(1 if bad else 0)
