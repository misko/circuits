#!/usr/bin/env python3
"""MEASURED 180-degree self-symmetry of a footprint — the ONLY exemption A-ROT
grants from "every CPL rotation comes from a MEASURED per-LCSC row".

WHY AN EXEMPTION EXISTS AT ALL
------------------------------
Making UNSOURCED blocking is right, but 2784 of the fleet's CPL rows are chip
passives (`R_0603`, `C_1210`, `L_...`) whose rotation offset is 0 in every
library on earth. A gate that demands 173 datasheet-grade measurements before
any board can export is a gate that gets switched off, and a switched-off gate
protects nothing.

WHY THIS EXEMPTION IS NOT THE BUG AGAIN
---------------------------------------
The defect class being retired is *authority inherited by pattern-matching a
footprint NAME*. This exemption matches NO name and reads NO table. It MEASURES
a property of the board's own footprint:

    a part is exempt only if its pad set AND all of its graphics map onto
    themselves EXACTLY under a 180-degree rotation about the footprint origin.

If a footprint is its own 180-degree reflection then it carries no orientation
to get wrong: offset 0 and offset 180 place identical copper, so there is
nothing for a measurement to add. If it is NOT — if a silk chamfer, a polarity
bar, a pin-1 dot or a cathode band breaks the symmetry — the footprint is
telling you it has an orientation, and A-ROT demands the measured row.

MEASURED on usb-hub-3s-v3 v1.5's board, which is exactly where the class bit:

    R_0603/R_0402/R_1206/R_2512   pads sym 0.000  gfx sym 0.000   EXEMPT
    C_0603/C_0805/C_1210          pads sym 0.000  gfx sym 0.000   EXEMPT
    L_Sunlord_MWSA1206S-6R8       pads sym 0.000  gfx sym 0.000   EXEMPT
    Fuse_2920_7451Metric          pads sym 0.000  gfx sym 0.000   EXEMPT
    CP_Elec_6.3x7.7 (C1, C2)      pads sym 0.000  gfx ASYM 1.812  MEASURE  <-- the P0
    D_SOD-123 / D_SOD-323 / D_SMB pads sym 0.000  gfx ASYM 0.100+ MEASURE
    SOT-23 / SOT-23-6 / QFN / ... pads ASYM                       MEASURE

The polarized electrolytics that shipped 180 REVERSED on two boards
(usb-hub-3s-v3 C1/C2, cooksense CE1) are caught by the GRAPHICS half alone:
their pads are perfectly symmetric — which is precisely why a pad-number fit
could not see the reversal — and their silk polarity mark is not. The same
graphics asymmetry is the NUMBERING-FREE channel canon A-POL requires, reused
here as the exemption test, so the two gates cannot disagree.

Also enforced: an exempt part must have EXACTLY TWO pads. A 180-symmetric part
with more pads can still be 90 degrees wrong, and only a 2-terminal chip part
is universally drawn pads-on-x by both libraries. More pads => measure it.
"""
import math

try:
    import pcbnew
except ImportError:  # pragma: no cover - only the exporter path needs it
    pcbnew = None

#: mm. A footprint is authored on a grid; anything above this is a real feature,
#: not a rounding artefact. Every EXEMPT part measured on the fleet is 0.000.
TOL_MM = 0.02

GFX_LAYERS = {"F.Fab", "B.Fab", "F.SilkS", "B.SilkS", "F.CrtYd", "B.CrtYd"}


def _pads(fp):
    """[(x, y, w, h, shape)] in footprint-local mm. Pad NUMBERS are
    deliberately ignored — the whole point is a numbering-free test."""
    out = []
    for p in fp.Pads():
        r = p.GetFPRelativePosition()
        s = p.GetSize()
        out.append((r.x / 1e6, r.y / 1e6, s.x / 1e6, s.y / 1e6,
                    int(p.GetShape())))
    return out


def _gfx_points(fp):
    """[(x, y, layer)] endpoints of every SHAPE on a fab/silk/courtyard layer,
    in footprint-local mm.

    SHAPES ONLY, never text: a refdes is placed for legibility, not for
    orientation, and counting it would let its position decide whether a part
    is symmetric (the same rule canon A-POL's marker_side() follows, for the
    same reason)."""
    out = []
    c = fp.GetPosition()
    for d in fp.GraphicalItems():
        if pcbnew is not None and not isinstance(d, pcbnew.PCB_SHAPE):
            continue
        ln = d.GetLayerName()
        if ln not in GFX_LAYERS:
            continue
        for q in (d.GetStart(), d.GetEnd()):
            out.append(((q.x - c.x) / 1e6, (q.y - c.y) / 1e6, ln))
    return out


def _worst_mismatch(items, key_of, pos_of):
    """Largest distance from any item's 180-rotated image to the nearest
    same-kind item. 0.0 means the set is its own 180-reflection."""
    worst = 0.0
    for it in items:
        k, (x, y) = key_of(it), pos_of(it)
        best = None
        for other in items:
            if key_of(other) != k:
                continue
            ox, oy = pos_of(other)
            d = math.hypot(ox + x, oy + y)     # (x,y) rotated 180 -> (-x,-y)
            if best is None or d < best:
                best = d
        if best is None:
            return float("inf")
        worst = max(worst, best)
    return worst


def symmetry(fp, tol_mm=TOL_MM):
    """Measure a footprint's 180-degree self-symmetry.

    Returns a dict:
      exempt      bool  — A-ROT may skip the measured-row requirement
      n_pads      int
      pad_resid   float (mm)  worst pad mismatch under 180
      gfx_resid   float (mm)  worst graphics mismatch under 180
      why         str   the reason, phrased for a blocking report
    """
    pads = _pads(fp)
    pad_resid = _worst_mismatch(pads, lambda p: (round(p[2], 3), round(p[3], 3),
                                                 p[4]),
                                lambda p: (p[0], p[1])) if pads else float("inf")
    gfx = _gfx_points(fp)
    gfx_resid = _worst_mismatch(gfx, lambda g: g[2],
                                lambda g: (g[0], g[1])) if gfx else 0.0

    if len(pads) != 2:
        why = (f"{len(pads)} pads — the exemption is only for 2-terminal chip "
               f"parts (a symmetric part with more pads can still be 90 deg "
               f"wrong)")
        ok = False
    elif pad_resid > tol_mm:
        why = (f"pad set is NOT 180-symmetric (worst {pad_resid:.3f} mm > "
               f"{tol_mm} mm) — the footprint has an orientation")
        ok = False
    elif gfx_resid > tol_mm:
        why = (f"pads are 180-symmetric ({pad_resid:.3f} mm) but the GRAPHICS "
               f"are not (worst {gfx_resid:.3f} mm) — a silk/fab polarity "
               f"mark, cathode band, chamfer or pin-1 feature breaks the "
               f"symmetry, so the part HAS an orientation that a pad fit "
               f"cannot see (the usb-hub C1/C2 + cooksense CE1 class)")
        ok = False
    else:
        why = (f"2 pads, 180-symmetric to {pad_resid:.3f} mm with graphics "
               f"symmetric to {gfx_resid:.3f} mm — offset 0 and offset 180 "
               f"place identical copper, so there is no orientation to source")
        ok = True
    return {"exempt": ok, "n_pads": len(pads), "pad_resid": pad_resid,
            "gfx_resid": gfx_resid, "why": why}
