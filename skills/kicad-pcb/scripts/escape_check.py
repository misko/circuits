#!/usr/bin/env python3
"""Package escape feasibility vs fab tier — the D-ESC gate's math.

Predicts, from package geometry and the fab capability model
(references/fab_tiers.yaml), the cheapest tier a package can escape at.
This is a PREDICTION from datasheet geometry; DRC/KRT later discover the
same wall empirically — checker and checked share no method (canon M1).

The physics, per package style:
- leaded / connector / passive: pads escape OUTWARD (gull-wing rows, edge
  pins); no via fanout ring is forced, feasible at every tier.
- qfn / dfn (bottom-terminated, exposed pad): inner-facing nets need a
  dogbone via ring just outside the pads. The ring exists iff
      min_via_diameter + min_space <= pitch
  (adjacent dogbone vias at pad pitch), OR the tier allows via-in-pad.
  Incident: SY8368 QFN-10 @ 0.45-0.5mm pitch — 0.45 + 0.127 = 0.577 > 0.5
  at jlc_4layer_standard = the clean-room 3S stall (2026-07-20).
- bga: needs the dogbone ring AND a routing lane between balls
  (min_track + 2*min_space <= pitch - ball land, land ~= pitch/2).

usage:
  escape_check.py <part.yaml> [...]      # grade part.yaml escape blocks
  escape_check.py --style qfn --pitch 0.5   # ad-hoc, at part selection
Prints per-tier verdicts + the minimum tier; exits 1 on any infeasible-
everywhere part or any part.yaml whose declared block contradicts the math.
"""
import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

TIERS_PATH = Path(__file__).resolve().parent.parent / "references" / "fab_tiers.yaml"

OUTWARD_STYLES = {"leaded", "connector", "passive", "module"}
RING_STYLES = {"qfn", "dfn"}


def load_tiers(path=TIERS_PATH):
    return yaml.safe_load(Path(path).read_text())["tiers"]


def feasible(style, pitch, tier):
    """Can this package escape at this tier? Pure geometry."""
    if style in OUTWARD_STYLES:
        return True
    if style in RING_STYLES:
        return (tier["min_via_diameter"] + tier["min_space"] <= pitch
                or tier.get("via_in_pad", False))
    if style == "bga":
        ring = (tier["min_via_diameter"] + tier["min_space"] <= pitch
                or tier.get("via_in_pad", False))
        lane = tier["min_track"] + 2 * tier["min_space"] <= pitch - pitch / 2
        return ring and lane
    raise ValueError(f"unknown escape style '{style}' "
                     f"(known: {sorted(OUTWARD_STYLES | RING_STYLES | {'bga'})})")


def tier_required(style, pitch, tiers):
    """Name of the cheapest (lowest-rank) feasible tier, or None."""
    ranked = sorted(tiers.items(), key=lambda kv: kv[1]["rank"])
    for name, t in ranked:
        if feasible(style, pitch, t):
            return name
    return None


# package/footprint-string sanity: catches an escape block whose declared
# inputs contradict the part's own footprint name (the tamper/copy hole)
STYLE_TOKENS = [
    (r"\bW?LCSP|\bBGA", "bga"),
    (r"\bU?[TVWX]?QFN|\bDFN|\bSON\b", "qfn"),
    (r"\bH?T?SS?OP|\bSOIC|\bSOT|\bSOP|\bTO-|\bQFP|\bDPAK|\bPAK", "leaded"),
]


def infer_from_strings(*strings):
    """(style_guess, pitch_guess) from package/footprint text; None if unknown."""
    blob = " ".join(s for s in strings if s)
    style = None
    for pat, st in STYLE_TOKENS:
        if re.search(pat, blob, re.I):
            style = st
            break
    m = re.search(r"P(\d+\.\d+)(?:mm)?", blob)
    pitch = float(m.group(1)) if m else None
    return style, pitch


def check_part(part_yaml, tiers):
    """-> list of problem strings (empty = part's escape block agrees)."""
    y = yaml.safe_load(Path(part_yaml).read_text()) or {}
    npins = len(y.get("pins") or {})
    if npins <= 2:
        return []
    esc = y.get("escape")
    mpn = y.get("mpn", Path(part_yaml).parent.name)
    if not esc:
        return [f"{mpn}: multi-pin part has NO escape block "
                f"(D-ESC: declare style+pitch, run escape_check)"]
    probs = []
    style, pitch = esc.get("style"), esc.get("pitch")
    if not style or not pitch:
        return [f"{mpn}: escape block missing style/pitch"]
    g_style, g_pitch = infer_from_strings(y.get("package", ""),
                                          y.get("footprint", ""))
    if g_style and g_style != style and not (
            g_style == "leaded" and style in ("connector", "module")):
        probs.append(f"{mpn}: declared style '{style}' contradicts "
                     f"package/footprint text ('{g_style}')")
    if g_pitch and abs(g_pitch - float(pitch)) > 0.051:
        probs.append(f"{mpn}: declared pitch {pitch} contradicts "
                     f"footprint text (P{g_pitch}mm)")
    want = tier_required(style, float(pitch), tiers)
    got = esc.get("tier_required")
    if want is None:
        probs.append(f"{mpn}: {style} @ {pitch}mm escapes at NO known tier "
                     f"— package problem, re-select the part")
    elif got != want:
        probs.append(f"{mpn}: declared tier_required '{got}' but the math "
                     f"says '{want}' ({style} @ {pitch}mm) — stale/copied block")
    return probs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("parts", nargs="*", help="part.yaml paths")
    ap.add_argument("--style", help="ad-hoc: package style")
    ap.add_argument("--pitch", type=float, help="ad-hoc: pad pitch mm")
    ap.add_argument("--tiers", default=str(TIERS_PATH))
    args = ap.parse_args()
    tiers = load_tiers(args.tiers)
    bad = 0

    if args.style and args.pitch:
        for name, t in sorted(tiers.items(), key=lambda kv: kv[1]["rank"]):
            ok = feasible(args.style, args.pitch, t)
            print(f"  {name:24s} {'ok' if ok else 'INFEASIBLE'}")
        req = tier_required(args.style, args.pitch, tiers)
        print(f"tier_required: {req or 'NONE — re-select the part'}")
        if req:
            print(f'escape: {{style: {args.style}, pitch: {args.pitch}, '
                  f'tier_required: {req}, checked: escape_check}}')
        sys.exit(0 if req else 1)

    for p in args.parts:
        probs = check_part(p, tiers)
        for pr in probs:
            print(f"FAIL {pr}")
        bad += len(probs)
        if not probs:
            print(f"ok   {Path(p).parent.name}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
