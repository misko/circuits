#!/usr/bin/env python3
"""Package escape feasibility vs fab tier — the D-ESC gate's math (v2:
the ESCAPE-BUDGET model with CONDITIONAL verdicts).

Predicts, from package geometry and the fab capability model
(references/fab_tiers.yaml), the cheapest tier a package can escape at.
This is a PREDICTION from datasheet geometry; DRC/KRT later discover the
same wall empirically — checker and checked share no method (canon M1).

The physics, per package style:
- leaded / connector / passive: pads escape OUTWARD (gull-wing rows, edge
  pins); no via fanout ring is forced. BUT a DENSE leaded side hits the
  hole-to-hole wall: when pitch - min_via_drill < min_hole_to_hole, NO via
  fits between adjacent pins, so every escape must clear the row on the
  surface layer first. With >= DENSE_LEADED_ESCAPES escapes on one side
  the fan-out band saturates — the cheap tier is then CONDITIONAL on a
  reserved escape corridor at placement (floorplan `escape_corridors:`).
  Incident: LM5116 HTSSOP-20 @ 0.65mm, 8 escapes on the right side —
  0.65 - 0.3 drill = 0.35 < 0.5 hole-to-hole at jlc_4layer_standard =
  the v3 clean-room stall (usb-pwr-hub-3s ADR-0008, 2026-07-21).
- qfn / dfn (bottom-terminated, exposed pad): inner-facing nets need a
  dogbone via ring just outside the pads. The ring exists iff
      min_via_diameter + min_space <= pitch
  (adjacent dogbone vias at pad pitch), OR the tier allows via-in-pad.
  Incident: SY8368 QFN-10 @ 0.45-0.5mm pitch — 0.45 + 0.127 = 0.577 > 0.5
  at jlc_4layer_standard = the clean-room 3S stall (2026-07-20).
  CALIBRATION AGAINST SHIPPED GROUND TRUTH (a4ff7ed, 2026-07-21): the
  same SY8368 SHIPPED x2 at STANDARD tier on xt60-usb-supply-rerun with
  outward-only escapes — one surface track per fine pad, zero vias
  between pads, every escape net terminating in an adjacent passive.
  So for a SMALL dual-row-class QFN (npins <= OUTWARD_MAX_PINS) with a
  declared escape budget (escapes_worst_side <= OUTWARD_MAX_ESCAPES) the
  ring-infeasible tier is CONDITIONALLY feasible: condition
  `outward-only-local` (outward-only escape + all fine-pad nets local to
  adjacent passives, D-ADJ). A four-sided VQFN (LM5145, 20 pins — 3
  boards shipped ADVANCED) or a QFN-48 (IP6559-C) can NOT do outward-only
  and stays unconditional-advanced.
- bga: needs the dogbone ring AND a routing lane between balls
  (min_track + 2*min_space <= pitch - ball land, land ~= pitch/2).

CONDITIONS VOCABULARY (emitted in the escape block, verified by P-ESC):
  outward-only-local  every fine-pad net terminates in an adjacent local
                      passive; escapes go outward only, no crossings, no
                      layer drops (the shipped SY8368 configuration)
  escape-corridor     a reserved routing lane at placement for the dense
                      side's fan-out (floorplan `escape_corridors:` key)
A part.yaml claiming a CONDITIONAL tier must record the SAME conditions
in its escape block, or P-ESC fails it — a conditional verdict must be
EARNED per board, never inherited by copy.

usage:
  escape_check.py <part.yaml> [...]      # grade part.yaml escape blocks
  escape_check.py --style qfn --pitch 0.5 [--escapes-worst-side N] [--pins N]
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

# Calibration constants — each number is PAID-FOR ground truth, not tuning:
#   OUTWARD_MAX_ESCAPES = 6: the SY8368 shipped with ~6 outward escapes on
#     its fine side (measured on the sealed xt60-usb-supply-rerun board).
#   OUTWARD_MAX_PINS = 12: the dual-row 3x3-class QFN family the proof
#     covers; the LM5145 (VQFN-20, 4 sides, 3 boards shipped ADVANCED)
#     must NOT qualify for the outward-only rescue.
#   DENSE_LEADED_ESCAPES = 6: leaded sides with < 6 escapes closed at the
#     cheapest tier on many boards; 8 escapes hit the ADR-0008 wall (v3).
OUTWARD_MAX_ESCAPES = 6
OUTWARD_MAX_PINS = 12
DENSE_LEADED_ESCAPES = 6
COND_OUTWARD = "outward-only-local"
COND_CORRIDOR = "escape-corridor"
KNOWN_CONDITIONS = {COND_OUTWARD, COND_CORRIDOR}


def load_tiers(path=TIERS_PATH):
    return yaml.safe_load(Path(path).read_text())["tiers"]


def grade_tier(style, pitch, tier, escapes_worst_side=None, npins=None):
    """One tier's verdict: ('ok'|'conditional'|'no', [conditions]).

    'ok' = unconditionally feasible geometry. 'conditional' = feasible only
    under the returned conditions (which the part.yaml must record and the
    board must honour). 'no' = infeasible at this tier.
    """
    pitch = float(pitch)
    if style in OUTWARD_STYLES:
        # Dense-leaded wall (ADR-0008): applies to gull-wing rows only —
        # connectors/passives/modules never carry an 8-escape 0.65mm side
        # in this fleet, so the corridor condition stays evidence-scoped.
        if style == "leaded" and escapes_worst_side is not None \
                and int(escapes_worst_side) >= DENSE_LEADED_ESCAPES:
            wall = pitch - tier["min_via_drill"] < tier["min_hole_to_hole"]
            if wall and not tier.get("via_in_pad", False):
                return "conditional", [COND_CORRIDOR]
        return "ok", []
    if style in RING_STYLES:
        ring = (tier["min_via_diameter"] + tier["min_space"] <= pitch
                or tier.get("via_in_pad", False))
        if ring:
            return "ok", []
        # outward-only rescue: proven ONLY for the small dual-row class
        # with a declared, small escape budget (see module docstring)
        if (escapes_worst_side is not None
                and int(escapes_worst_side) <= OUTWARD_MAX_ESCAPES
                and (npins is None or int(npins) <= OUTWARD_MAX_PINS)):
            return "conditional", [COND_OUTWARD]
        return "no", []
    if style == "bga":
        ring = (tier["min_via_diameter"] + tier["min_space"] <= pitch
                or tier.get("via_in_pad", False))
        lane = tier["min_track"] + 2 * tier["min_space"] <= pitch - pitch / 2
        return ("ok", []) if ring and lane else ("no", [])
    raise ValueError(f"unknown escape style '{style}' "
                     f"(known: {sorted(OUTWARD_STYLES | RING_STYLES | {'bga'})})")


def feasible(style, pitch, tier):
    """Back-compat: unconditional geometric feasibility (no budget facts)."""
    return grade_tier(style, pitch, tier)[0] == "ok"


def tier_required(style, pitch, tiers, escapes_worst_side=None, npins=None):
    """Name of the cheapest UNCONDITIONALLY feasible tier, or None."""
    ranked = sorted(tiers.items(), key=lambda kv: kv[1]["rank"])
    for name, t in ranked:
        if grade_tier(style, pitch, t, escapes_worst_side, npins)[0] == "ok":
            return name
    return None


def tier_conditional(style, pitch, tiers, escapes_worst_side=None, npins=None):
    """Cheapest tier feasible AT ALL -> (name, [conditions]) or (None, [])."""
    ranked = sorted(tiers.items(), key=lambda kv: kv[1]["rank"])
    for name, t in ranked:
        v, conds = grade_tier(style, pitch, t, escapes_worst_side, npins)
        if v in ("ok", "conditional"):
            return name, conds
    return None, []


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
    mpn = y.get("mpn", Path(part_yaml).parent.name)
    probs = []
    # `mates:` is a connector PART FACT (plug|receptacle) — the male-plug
    # incident (usb-hub-3s ADR-0006, 2026-07-21): a USB-A MALE PLUG served
    # weeks as a receptacle because gender lives only in the drawing title
    # block. The fact is recorded here; role-vs-gender remains a HUMAN
    # check (pin review) — see t4_regressions.
    mates = y.get("mates")
    if mates is not None and mates not in ("plug", "receptacle"):
        probs.append(f"{mpn}: mates: '{mates}' is not plug|receptacle")
    if npins <= 2:
        return probs
    esc = y.get("escape")
    if not esc:
        return probs + [f"{mpn}: multi-pin part has NO escape block "
                        f"(D-ESC: declare style+pitch, run escape_check)"]
    style, pitch = esc.get("style"), esc.get("pitch")
    if not style or not pitch:
        return probs + [f"{mpn}: escape block missing style/pitch"]
    g_style, g_pitch = infer_from_strings(y.get("package", ""),
                                          y.get("footprint", ""))
    if g_style and g_style != style and not (
            g_style == "leaded" and style in ("connector", "module")):
        probs.append(f"{mpn}: declared style '{style}' contradicts "
                     f"package/footprint text ('{g_style}')")
    if g_pitch and abs(g_pitch - float(pitch)) > 0.051:
        probs.append(f"{mpn}: declared pitch {pitch} contradicts "
                     f"footprint text (P{g_pitch}mm)")

    ews = esc.get("escapes_worst_side")
    if ews is not None and (not isinstance(ews, int) or ews < 0):
        probs.append(f"{mpn}: escapes_worst_side '{ews}' is not a "
                     f"non-negative integer")
        ews = None
    conds_declared = esc.get("conditions") or []
    unknown_conds = sorted(set(conds_declared) - KNOWN_CONDITIONS)
    if unknown_conds:
        probs.append(f"{mpn}: unknown escape condition(s) {unknown_conds} "
                     f"(known: {sorted(KNOWN_CONDITIONS)})")
        return probs

    want = tier_required(style, float(pitch), tiers, ews, npins)
    got = esc.get("tier_required")
    if want is None:
        probs.append(f"{mpn}: {style} @ {pitch}mm escapes at NO known tier "
                     f"— package problem, re-select the part")
    elif got == want:
        if conds_declared:
            probs.append(f"{mpn}: conditions {conds_declared} declared but "
                         f"tier_required '{got}' is UNCONDITIONAL for this "
                         f"geometry — stale/copied conditions")
    elif got not in tiers:
        probs.append(f"{mpn}: declared tier_required '{got}' is not a tier "
                     f"in fab_tiers.yaml")
    else:
        v, need = grade_tier(style, float(pitch), tiers[got], ews, npins)
        if v == "conditional":
            if sorted(set(conds_declared)) == sorted(set(need)):
                pass  # conditional verdict, EARNED: conditions recorded
            elif not conds_declared:
                probs.append(
                    f"{mpn}: tier_required '{got}' is CONDITIONAL on "
                    f"{need} but the block records no conditions — record "
                    f"conditions: {need} (and honour them on the board) or "
                    f"raise the tier to '{want}'")
            else:
                probs.append(
                    f"{mpn}: recorded conditions {sorted(conds_declared)} "
                    f"do not match the math's {sorted(need)} for tier "
                    f"'{got}'")
        else:
            probs.append(f"{mpn}: declared tier_required '{got}' but the "
                         f"math says '{want}' ({style} @ {pitch}mm"
                         + (f", {ews} escapes worst side" if ews is not None
                            else "")
                         + ") — stale/copied block")
    return probs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("parts", nargs="*", help="part.yaml paths")
    ap.add_argument("--style", help="ad-hoc: package style")
    ap.add_argument("--pitch", type=float, help="ad-hoc: pad pitch mm")
    ap.add_argument("--escapes-worst-side", type=int, default=None,
                    help="ad-hoc: escape count on the worst single side "
                         "(enables the conditional-verdict model)")
    ap.add_argument("--pins", type=int, default=None,
                    help="ad-hoc: total pin count (bounds the outward-only "
                         "rescue to the small dual-row QFN class)")
    ap.add_argument("--tiers", default=str(TIERS_PATH))
    args = ap.parse_args()
    tiers = load_tiers(args.tiers)
    bad = 0

    if args.style and args.pitch:
        ews, npins = args.escapes_worst_side, args.pins
        for name, t in sorted(tiers.items(), key=lambda kv: kv[1]["rank"]):
            v, conds = grade_tier(args.style, args.pitch, t, ews, npins)
            lab = {"ok": "ok",
                   "conditional": "CONDITIONAL on " + ",".join(conds),
                   "no": "INFEASIBLE"}[v]
            print(f"  {name:24s} {lab}")
        req = tier_required(args.style, args.pitch, tiers, ews, npins)
        creq, cconds = tier_conditional(args.style, args.pitch, tiers,
                                        ews, npins)
        print(f"tier_required: {req or 'NONE — re-select the part'}")
        if creq and req and creq != req:
            print(f"tier_conditional: {creq} (conditions: "
                  f"[{', '.join(cconds)}])")
        if req:
            extra = (f", escapes_worst_side: {ews}" if ews is not None else "")
            print(f'escape: {{style: {args.style}, pitch: {args.pitch}'
                  f'{extra}, tier_required: {req}, checked: escape_check}}')
            if creq and creq != req:
                print(f'# cheaper CONDITIONAL form (earn it on the board):\n'
                      f'# escape: {{style: {args.style}, pitch: {args.pitch}'
                      f'{extra}, tier_required: {creq}, conditions: '
                      f'[{", ".join(cconds)}], checked: escape_check}}')
        sys.exit(0 if req else 1)

    # G-COVER: `escape_check.py` with no part arguments printed NOTHING and
    # exited 0 — a green run over zero parts, which is the whole M-COVER
    # class. A shell glob that matched nothing (a renamed 02_parts dir, a
    # wrong cwd) reached exactly this line and read as success.
    if not args.parts:
        print("P-ESC FAIL: 0/0 parts graded — no part.yaml paths were given "
              "(a glob that matched nothing lands here). A zero denominator "
              "is a FAIL, never a pass (canon M-COVER). Pass part.yaml paths, "
              "or use --style/--pitch for the ad-hoc tier table.")
        sys.exit(1)

    graded = 0
    for p in args.parts:
        if not Path(p).exists():
            # G-COVER: a path that does not exist is UNGRADED, and must not be
            # silently absent from the denominator.
            print(f"FAIL {p}: no such part.yaml — a part that cannot be read "
                  f"is not a part that passed")
            bad += 1
            continue
        probs = check_part(p, tiers)
        graded += 1
        for pr in probs:
            print(f"FAIL {pr}")
        bad += len(probs)
        if not probs:
            print(f"ok   {Path(p).parent.name}")
    # G-INPUT: name the tier table too — the verdict depends on it entirely.
    print(f"input: tiers = {Path(args.tiers).resolve()} "
          f"({len(tiers)} tier(s))")
    verdict = "FAIL" if bad else "PASS"
    print(f"P-ESC {verdict}: {graded}/{len(args.parts)} part.yaml graded, "
          f"{bad} problem(s)")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
