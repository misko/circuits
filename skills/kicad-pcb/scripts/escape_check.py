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
  escape_check.py --board B.kicad_pcb    # P-LAND: landable width per pad
Prints per-tier verdicts + the minimum tier; exits 1 on any infeasible-
everywhere part or any part.yaml whose declared block contradicts the math.

===========================================================================
P-LAND — THE WIDEST TRACK THAT CAN ACTUALLY LEAVE A PAD (canon M-ENTRY)
===========================================================================
D-ESC above asks whether a PACKAGE can be escaped at a fab tier. It never
asks the other half: whether the track the NETCLASS demands can physically
leave the land it must terminate on. Two boards asked that question
independently (canon M8's two strike), and neither was asked it by a gate:

- `pluto-rx2-8way` — PE42482A-X's vendor land is 0.60 x 0.30 mm on 0.50 mm
  pitch, leaving 0.350 mm from the RF centreline to a GND land edge. A
  0.36 mm trace at the declared 0.200 mm clearance needs 0.180 + 0.200 =
  0.380 mm: DEFICIT 0.030 mm. Landable maximum 0.300 mm = 55.3 ohm against
  a 50 ohm RF50 floor. It surfaced only when 6 of 11 RF nets failed to
  route, three hours in.
- `pluto-cal-switch` — ELEVEN pads that cannot accept their own class
  minimum (U_SW1.5/U_SW2.5 need 0.350, take 0.250; U_MCU.46/.47 need
  0.330, take 0.300; U_MCU.10/.22/.26/.33 and .23/.45/.50 need 0.400, take
  0.300). Found BY HAND at the top of stage 6. placement_gates PASSED and
  tier_preflight was 0 FAIL.

The measure needs no router, no copper, no stackup and no fab tier: it is
computable the moment parts are PLACED, which is canon M-ENTRY (ADR-0007)
— grade a fact where it enters, not where it shows.

WHAT IS MEASURED, EXACTLY. For each pad: a straight track `--reach` mm
long, launched from a 30 um grid of landing points INSIDE the land, in each
of `--dirs` directions. Its widest legal width from point L in direction t
is w = 2 * (d - clearance), where d is the distance from the track
CENTRELINE to the nearest other-net copper land; the pad's landable maximum
is the best w over all (L, t). It is a LAUNCH measure, not a route: a track
may turn once it is clear of the land field, and a track wider than the
land it lands on is legal.

THE LANDING POINT IS A FREE VARIABLE AND IT MATTERS. A centre-only model
(which is how both boards published their headline arithmetic — "0.350 mm
from the RF centreline", "the neighbouring land's copper edge sits 0.275 mm
from the centre") agrees on the hemmed pads and is WRONG on the corner
ones: measured, it fails six pads of pluto-cal-switch's SHIPPED, DRC-clean
copper, the same six the board's own hand measurement cleared at 0.460 mm.

WHAT THIS GATE DOES *NOT* CLAIM, AND THE CORRECTION IS THE VALUABLE HALF.
It does NOT say width is why a board failed to route. Measured on
`pluto-rx2-8way` 2026-07-30: at KRT's default `grid_step: 0.1` NOTHING
routes the five boxed RF pads at ANY width — 0.30, 0.25 and 0.20 all fail
— because the RF land centres sit at odd multiples of 0.05 mm and a
0.1 mm grid cannot put a centreline on them. With `grid_step: 0.05` and
`clearance: 0.14` the wave routes 11/11 at the FULL 0.36 mm. So the ranked
causes of a launch that will not route are GRID, then CLEARANCE, then
WIDTH, and the fix-line says so on every failing run.

NECK-DOWN IS REFUTED AS THE REMEDY, not merely unconfigured. Measured:
`--neckdown-length 0.3` routes 11/11 and delivers 149.832 mm of RF copper
at 0.25 mm and 0.000 mm at 0.36, because KRT's re-widen pass only restores
width where the NARROW-PLANNED path has wide clearance — which, on a
radial star leaving a QFN, it never does.

VACUITY: (canon G-VACUOUS. Fixtured by `t1_escape_tier.py`
`t_vacuity_P_LAND_passes_a_pad_whose_class_declares_no_width_floor`.)

P-LAND grades a pad against a DECLARED floor, so a pad whose netclass
declares no `track_width` minimum is out of scope and CANNOT fail — the
gate passes while the fact it grades ("this pad can emit the width its net
needs") is false, because the need was never written down. Measured on the
fleet 2026-07-30 (7 boards, 2689 copper pads): 1440 sit on a class with no
declared width floor, and on `pluto-cal-switch` deleting three lines from
`nets.yaml` would turn all ELEVEN findings into silence.

This is deliberate and it is bounded, not hidden: the count prints on every
run as `N no declared width floor` inside the denominator, so the blind
spot is enumerated on every board. It is not closed by grading pads against
a netclass DEFAULT width — that would invent a requirement the board never
made, and the fleet's Default class alone would red every board on day one.
The real closure is R1's other half (every routed class declares its floor),
which belongs to `rules_audit`, not here.

RELAXATIONS ARE READ, NOT IGNORED. `pluto-cal-switch` already SOLVED its
eleven pads, with three permissive rule areas plus `scoped_floors:` bounded
to lambda_g/61. A gate that reported eleven failures on that board would be
switched off inside a week. The floors and the relaxations are both read
from the SHIPPED `.kicad_dru` (last-match precedence, exactly as KiCad
resolves them), never from the YAML that generated it — the generator and
this checker share no input (canon M1).
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

OUTWARD_STYLES = {"leaded", "connector", "passive", "module",
                  "through_hole"}
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
    return yaml.safe_load(Path(path).read_text(encoding="utf-8-sig"))["tiers"]


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
    y = yaml.safe_load(Path(part_yaml).read_text(encoding="utf-8-sig")) or {}
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
    known_styles = OUTWARD_STYLES | RING_STYLES | {"bga"}
    if style not in known_styles:
        return probs + [f"{mpn}: unknown escape style '{style}' "
                        f"(known: {sorted(known_styles)})"]
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


# ===========================================================================
# P-LAND — landable width per pad vs the netclass width floor
# ===========================================================================
# Defaults. REACH_MM is how far the straight launch must hold its width: a
# track can turn after it clears the land field, so a long reach would grade
# the ROUTE and not the LAUNCH. 1.0 mm is ~2.5 fine pitches — past every
# neighbouring land in the two motivating cases and short of any trunk.
# DIRS 48 = 7.5 deg steps, the same sampling pluto-cal-switch's hand
# measurement used. CAP_MM bounds the reported number where a direction is
# simply open (an unbounded "landable width" is not a fact about the pad).
REACH_MM = 1.0
DIRS = 48
CAP_MM = 2.0
NEIGHBOUR_R_MM = 2.5          # obstacle search radius, as measured by hand
TOL_MM = 1e-4                 # 0.1 um: float noise, never a real deficit
LAUNCH_STEP_MM = 0.03         # the hand measurement's 30 um landing grid
MAX_LAUNCH_PTS = 25           # bounds a 2 mm thermal land to 6x6 samples;
# the optimum sits at an extreme point of the land (a corner pad measures
# 0.250 mm from its centre and 0.450 mm from its own corner), and the grid
# always includes the bbox extremes, so a finer grid moved no fleet number.

LAND_FIX_ORDER = (
    "P-LAND FIX ORDER (measured on pluto-rx2-8way, 2026-07-30 — a launch "
    "that will not route is THREE questions):\n"
    "  1. ROUTER GRID, and it is free. At KRT `grid_step: 0.1` NOTHING "
    "routed that board's five boxed RF pads at ANY width (0.30/0.25/0.20 "
    "all fail): the land centres sit at odd multiples of 0.05 mm. At "
    "`grid_step: 0.05` + `clearance: 0.14` the same wave routes 11/11 at "
    "the FULL 0.36 mm.\n"
    "  2. A LAUNCH-LOCAL SCOPED CLEARANCE (a rule area over the land "
    "field). This gate reads `constraint clearance` rule-area relaxations "
    "if they exist.\n"
    "  3. WIDTH — a `scoped_floors:` taper bounded by a rule area, with "
    "the impedance/ampacity argument as its `why:` (pluto-cal-switch "
    "bounds its necks to lambda_g/61).\n"
    "  NOT A REMEDY: router NECK-DOWN. Measured `--neckdown-length 0.3` "
    "routes 11/11 and delivers 149.832 mm of RF copper at 0.25 mm and "
    "0.000 mm at 0.36 — the re-widen pass only restores width where the "
    "narrow-planned path has wide clearance, which leaving a QFN it never "
    "has.\n"
    "  AND THIS GATE DOES NOT CLAIM WIDTH IS WHY A BOARD FAILED TO ROUTE. "
    "It states one geometric fact: this pad cannot emit its class width at "
    "the declared clearance.")


def _seg_pt_dist(ax, ay, bx, by, px, py):
    """Distance from point p to segment ab."""
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else ((px - ax) * dx + (py - ay) * dy) / L2
    t = max(0.0, min(1.0, t))
    return ((px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2) ** 0.5


def _seg_seg_dist(a, b, c, d):
    """Distance between segments ab and cd (0 if they cross)."""
    (ax, ay), (bx, by), (cx, cy), (dx, dy) = a, b, c, d
    d1x, d1y = bx - ax, by - ay
    d2x, d2y = dx - cx, dy - cy
    den = d1x * d2y - d1y * d2x
    if den != 0:
        t = ((cx - ax) * d2y - (cy - ay) * d2x) / den
        u = ((cx - ax) * d1y - (cy - ay) * d1x) / den
        if 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0:
            return 0.0
    return min(_seg_pt_dist(ax, ay, bx, by, cx, cy),
               _seg_pt_dist(ax, ay, bx, by, dx, dy),
               _seg_pt_dist(cx, cy, dx, dy, ax, ay),
               _seg_pt_dist(cx, cy, dx, dy, bx, by))


def _poly_seg_dist(poly, a, b):
    """Distance from polygon (list of (x, y)) to segment ab. 0 if it hits."""
    best = float("inf")
    for i in range(len(poly)):
        best = min(best, _seg_seg_dist(poly[i], poly[(i + 1) % len(poly)], a, b))
        if best == 0.0:
            return 0.0
    return best


def launch_points(poly, step=LAUNCH_STEP_MM, max_pts=MAX_LAUNCH_PTS):
    """Landing points INSIDE the land: a grid, plus the centroid.

    The launch point is a free variable and it MATTERS: a corner pad of a
    2x3 land field measures 0.250 mm from its centre and 0.450 mm from its
    own corner, and `pluto-cal-switch`'s hand measurement (48 directions x a
    30 um grid of landing points) reported 0.460 mm for exactly those pads
    and routed them at 0.35 mm. A centre-only model FAILS six pads on that
    board's SHIPPED, DRC-clean copper — measured, which is why this samples
    the land.
    """
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    nx = max(1, min(int(round((x1 - x0) / step)), int(max_pts ** 0.5)))
    ny = max(1, min(int(round((y1 - y0) / step)), int(max_pts ** 0.5)))
    eps = 1e-6
    pts = [(cx, cy)]
    for i in range(nx + 1):
        for j in range(ny + 1):
            p = (x0 + (x1 - x0) * i / nx if nx else cx,
                 y0 + (y1 - y0) * j / ny if ny else cy)
            p = (min(max(p[0], x0 + eps), x1 - eps),
                 min(max(p[1], y0 + eps), y1 - eps))
            if _point_in_poly(p, poly):
                pts.append(p)
    return pts


def max_landable(pad, obstacles, clearance, dirs=DIRS, reach=REACH_MM,
                 cap=CAP_MM):
    """Widest track that can leave `pad` -> (width_mm, capped, angle).

    pad/obstacles are dicts with 'c' (centre (x, y) mm) and 'poly'. The
    width is maximised over landing points inside the land x `dirs` straight
    launch directions; in direction t from point L the widest legal track is
    2 * (d - clearance) where d is the distance from the centreline to the
    nearest other-net land. A direction with no obstacle inside `reach` is
    reported AT THE CAP, never at infinity.
    """
    import math
    best, best_d = 0.0, None
    span = cap / 2.0 + clearance
    if not obstacles:
        return cap, True, None
    rays = [(math.cos(2.0 * math.pi * k / dirs),
             math.sin(2.0 * math.pi * k / dirs)) for k in range(dirs)]
    for lx, ly in launch_points(pad["poly"]):
        # near-obstacle ordering + an early exit: the first obstacle that
        # cannot beat the incumbent ends the direction.
        near = sorted(obstacles,
                      key=lambda ob: _poly_seg_dist(ob["poly"], (lx, ly),
                                                    (lx, ly)))
        for ux, uy in rays:
            ex, ey = lx + reach * ux, ly + reach * uy
            d = span
            for ob in near:
                d = min(d, _poly_seg_dist(ob["poly"], (lx, ly), (ex, ey)))
                if 2.0 * (d - clearance) <= best:
                    break
            w = 2.0 * (d - clearance)
            if w > best:
                best, best_d = w, round(math.degrees(math.atan2(uy, ux)), 1)
    return min(best, cap), best >= cap - TOL_MM, best_d


# --- .kicad_dru: the floors and the relaxations, as KiCad resolves them ---
_RULE_HEAD_RE = re.compile(r'\(rule\s+"?([^"\s)]+)"?')
_COND_RE = re.compile(r'\(condition\s+"(.*?)"\s*\)', re.S)
_CON_RE = re.compile(r'\(constraint\s+(\w+)\s*\(min\s+([0-9.]+)mm\s*\)')
_CLASS_RE = re.compile(r"A\.NetClass\s*==\s*'([^']+)'")
_AREA_RE = re.compile(r"A\.insideArea\('([^']+)'\)")
_NET_RE = re.compile(r"A\.NetName\s*==\s*'([^']+)'")


def read_dru_rules(path):
    """-> [{name, kind, constraint, min_mm, netclass|area, nets}] IN FILE ORDER.

    Only the two condition shapes this pipeline emits are understood; any
    other condition is returned with kind 'unparsed' so the caller can name
    it rather than silently ignore a rule that may relax a pad (M-COVER).
    """
    out = []
    text = Path(path).read_text(encoding="utf-8-sig") if Path(path).exists() else ""
    for m in _RULE_HEAD_RE.finditer(text):
        # brace-match the rule form: `.kicad_dru` closes its parens on the
        # constraint line, so a line-anchored regex reads ZERO rules and the
        # gate would grade every pad as floorless (measured: 300/300).
        depth, i = 0, m.start()
        while i < len(text):
            if text[i] == "(":
                depth += 1
            elif text[i] == ")":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        name, body = m.group(1), text[m.end():i]
        con = _CON_RE.search(body)
        if not con or con.group(1) not in ("track_width", "clearance"):
            continue
        cm = _COND_RE.search(body)
        cond = cm.group(1) if cm else ""
        rec = {"name": name, "constraint": con.group(1),
               "min_mm": float(con.group(2)), "cond": cond,
               "netclass": None, "area": None, "nets": []}
        cls, area = _CLASS_RE.search(cond), _AREA_RE.search(cond)
        if area:
            rec["kind"] = "area"
            rec["area"] = area.group(1)
            rec["nets"] = _NET_RE.findall(cond)
        elif cls and "&&" not in cond:
            rec["kind"] = "class"
            rec["netclass"] = cls.group(1)
        else:
            rec["kind"] = "unparsed"
        out.append(rec)
    return out


def resolve_min(rules, constraint, pad, areas):
    """LAST-MATCH-WINS resolution, exactly as KiCad orders .kicad_dru rules.

    -> (min_mm | None, rule_name | None). `areas` maps area name -> list of
    (polygon, layer-set) for the board's RULE AREAS.
    """
    hit = (None, None)
    for r in rules:
        if r["constraint"] != constraint or r["kind"] == "unparsed":
            continue
        if r["kind"] == "class":
            if r["netclass"] == pad["cls"]:
                hit = (r["min_mm"], r["name"])
        else:
            if r["nets"] and pad["net"] not in r["nets"]:
                continue
            for poly, layers in areas.get(r["area"], []):
                if (layers & pad["layers"]) and _point_in_poly(pad["c"], poly):
                    hit = (r["min_mm"], r["name"])
                    break
    return hit


def _point_in_poly(pt, poly):
    x, y = pt
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xx = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < xx:
                inside = not inside
    return inside


def read_board(board_path):
    """-> (pads, areas, board_name) via pcbnew. Requires /usr/bin/python3.

    A pad is {ref, num, net, cls, c, poly, layers}. `poly` is KiCad's OWN
    effective pad polygon, so roundrect/oval/custom lands are graded as
    drawn rather than as a bounding box (a bbox would MANUFACTURE deficits).
    """
    import pcbnew
    b = pcbnew.LoadBoard(str(board_path))
    scale = 1e6
    pads, unreached = [], []
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        for p in fp.Pads():
            if not p.IsOnCopperLayer():
                continue
            layers = frozenset(p.GetLayerSet().CuStack())
            pos = p.GetPosition()
            rec = {"ref": ref, "num": p.GetNumber(), "net": p.GetNetname(),
                   "cls": p.GetNetClassName(), "layers": layers,
                   "c": (pos.x / scale, pos.y / scale), "poly": None}
            try:
                sps = p.GetEffectivePolygon(sorted(layers)[0])
                o = sps.Outline(0)
                rec["poly"] = [(o.CPoint(i).x / scale, o.CPoint(i).y / scale)
                               for i in range(o.PointCount())]
            except Exception as e:                      # noqa: BLE001
                rec["why_unreached"] = f"pad outline unreadable ({e})"
                unreached.append(rec)
                continue
            if len(rec["poly"]) < 3:
                rec["why_unreached"] = "pad outline has < 3 points"
                unreached.append(rec)
                continue
            pads.append(rec)
    # Routed input only (empty at stage 5, which is where this gate is
    # meant to run): the vias and tracks already touching a land. Vias give
    # the VIA-ON-PAD escape class; tracks give the routed cross-check that
    # keeps the model from being silently over-strict.
    vias, tracks = [], []
    for t in b.GetTracks():
        s, e = t.GetStart(), t.GetEnd()
        if t.GetClass() == "PCB_VIA":
            # deliberately NOT GetWidth(): a via's width is per-layer in
            # KiCad 10 and the no-layer overload spews a wx assert per call.
            # Only the via's CENTRE is used (is it on this land?).
            vias.append((t.GetNetname(), (s.x / scale, s.y / scale), None))
        else:
            tracks.append((t.GetNetname(), t.GetWidth() / scale,
                           (s.x / scale, s.y / scale),
                           (e.x / scale, e.y / scale)))
    areas, pours = {}, []
    for z in b.Zones():
        if not z.GetIsRuleArea():
            # A COPPER POUR is an escape: a pad sitting inside a same-net
            # zone is fed by the pour and no track has to leave it at all.
            # Measured — without this, 17 pads on the SEALED, DRC-clean
            # crow-recorder-central-v2 FAIL, and 16 of them (the XU316
            # TQFP-128 power ring) carry NO TRACK AT ALL: they are pour-fed.
            lay = frozenset(z.GetLayerSet().CuStack())
            out = z.Outline()
            for i in range(out.OutlineCount()):
                o = out.Outline(i)
                pours.append((z.GetNetname(), lay,
                              [(o.CPoint(j).x / scale, o.CPoint(j).y / scale)
                               for j in range(o.PointCount())]))
            continue
        name = z.GetZoneName()
        lay = frozenset(z.GetLayerSet().CuStack())
        out = z.Outline()
        for i in range(out.OutlineCount()):
            o = out.Outline(i)
            poly = [(o.CPoint(j).x / scale, o.CPoint(j).y / scale)
                    for j in range(o.PointCount())]
            areas.setdefault(name, []).append((poly, lay))
    return pads, unreached, areas, pours, vias, tracks


def read_class_clearance(pro_path):
    """-> {netclass: clearance_mm}, plus the board's min_clearance floor."""
    import json
    y = json.loads(Path(pro_path).read_text(encoding="utf-8-sig"))
    cl = {c["name"]: float(c.get("clearance", 0.0))
          for c in (y.get("net_settings") or {}).get("classes", [])}
    floor = float(((y.get("board") or {}).get("design_settings") or {})
                  .get("rules", {}).get("min_clearance", 0.0) or 0.0)
    return cl, floor


def check_board(board_path, pro_path=None, dru_path=None, dirs=DIRS,
                reach=REACH_MM, verbose=False):
    """Grade every pad's landable width against its declared width floor.

    -> (lines, stats). SCOPE, and the defence of it:
      * IN SCOPE: every copper pad whose NET's resolved width floor is
        DECLARED — i.e. some `.kicad_dru` `track_width (min ...)` rule
        matches it. Not "signal pads only": 7 of pluto-cal-switch's 11
        findings are PWR pads on the RP2040, and a signal-only gate would
        have found 4 of 11. Not "one footprint's pads": DRC clearance is a
        function of net + layer, never of which footprint a land belongs
        to, so the neighbour set is EVERY other-net pad within
        NEIGHBOUR_R_MM (canon M-WIDTH — the rule is written at the width
        of its class, not of the incident, where every neighbour happened
        to be a sibling pad).
      * OUT OF SCOPE, counted and reported: a pad with NO net (mechanical /
        NPTH — nothing is ever routed to it), and a pad whose class has no
        declared width floor (nothing demanded a width of it; grading it
        against a netclass DEFAULT would invent a requirement the board
        never made).
      * UNREACHED, named, never passed: a pad whose land geometry cannot be
        resolved. A pad that cannot be read is not a pad that passed.
    """
    pads, unreached, areas, pours, vias, tracks = read_board(board_path)
    name = Path(board_path).stem
    pro_path = pro_path or Path(board_path).with_suffix(".kicad_pro")
    dru_path = dru_path or Path(board_path).with_suffix(".kicad_dru")
    cls_clear, min_clear = ({}, 0.0)
    if Path(pro_path).exists():
        cls_clear, min_clear = read_class_clearance(pro_path)
    rules = read_dru_rules(dru_path)
    unparsed = [r["name"] for r in rules if r["kind"] == "unparsed"]

    lines, fails = [], []
    stats = {"copper_pads": len(pads) + len(unreached), "graded": 0,
             "failed": 0, "unreached": len(unreached), "no_net": 0,
             "no_floor": 0, "relaxed": 0, "scoped_clearance": 0,
             "pour_fed": 0, "via_on_pad": 0, "xcheck": 0, "xcheck_over": 0}
    for u in unreached:
        lines.append(f"UNREACHED {name} {u['ref']}.{u['num']} "
                     f"net={u['net'] or '-'}: {u['why_unreached']}")

    by_layer = {}
    for p in pads:
        for L in p["layers"]:
            by_layer.setdefault(L, []).append(p)

    for p in pads:
        if not p["net"]:
            stats["no_net"] += 1
            continue
        floor, frule = resolve_min(rules, "track_width", p, areas)
        if floor is None:
            stats["no_floor"] += 1
            continue
        if any(net == p["net"] and (lay & p["layers"])
               and _point_in_poly(p["c"], poly) for net, lay, poly in pours):
            stats["pour_fed"] += 1
            continue
        # VIA ON THE LAND: the escape leaves DOWNWARD and no track has to
        # emit at all. Measured — this is how the sealed, DRC-clean
        # crow-recorder-central-v2 escapes its XU316 TQFP-128 power ring
        # (U1.10 carries no track, only a 0.3 mm via at 82.850, 99.400 on a
        # 1.475 x 0.250 mm land). Empty on an unrouted board, which is where
        # this gate is meant to run.
        if any(net == p["net"] and _point_in_poly((vx, vy), p["poly"])
               for net, (vx, vy), _r in vias):
            stats["via_on_pad"] += 1
            continue
        stats["graded"] += 1
        if frule and frule.startswith("scoped_"):
            stats["relaxed"] += 1
        # clearance: KiCad takes the LARGER of the two netclass clearances,
        # never below the board floor; a rule-area `clearance` relaxation
        # (the sibling's scoped-clearance work) wins by last-match if present.
        obstacles = []
        for q in by_layer_pads(by_layer, p):
            if q["net"] == p["net"] or q is p:
                continue
            if abs(q["c"][0] - p["c"][0]) > NEIGHBOUR_R_MM or \
               abs(q["c"][1] - p["c"][1]) > NEIGHBOUR_R_MM:
                continue
            obstacles.append(q)
        scoped_cl, crule = resolve_min(rules, "clearance", p, areas)
        if scoped_cl is not None:
            clear = scoped_cl
            stats["scoped_clearance"] += 1
        else:
            crule = None
            clear = max([min_clear, cls_clear.get(p["cls"], 0.0)]
                        + [cls_clear.get(q["cls"], 0.0) for q in obstacles])
        w, capped, ang = max_landable(p, obstacles, clear, dirs, reach)
        ok = w + TOL_MM >= floor
        tag = ">=" if capped else "="
        msg = (f"{name} {p['ref']}.{p['num']} net={p['net']} "
               f"class={p['cls']} floor={floor:.3f} "
               f"(rule {frule}) landable{tag}{w:.3f} @ clearance "
               f"{clear:.3f}" + (f" (rule {crule})" if crule else "")
               + (f" best_dir={ang} deg" if ang is not None else ""))
        # G-VACUOUS / M1: on a ROUTED input, the copper that already left
        # this land REFUTES the model if it is wider than the model says is
        # possible. A prediction nothing can contradict is not a prediction,
        # so the contradiction is printed, never swallowed.
        actual = max([tw for tn, tw, s, e in tracks
                      if tn == p["net"] and (_point_in_poly(s, p["poly"])
                                             or _point_in_poly(e, p["poly"]))],
                     default=None)
        if actual is not None:
            stats["xcheck"] += 1
            if actual > w + 0.001 and not capped:
                stats["xcheck_over"] += 1
                lines.append(
                    f"MODEL-REFUTED P-LAND {name} {p['ref']}.{p['num']} "
                    f"net={p['net']}: a {actual:.3f} mm track already leaves "
                    f"this land, above the {w:.3f} mm this model allows at "
                    f"clearance {clear:.3f}. EXACTLY TWO READINGS and DRC "
                    f"decides which: either the model is too strict (fix "
                    f"the gate, not the board), or that copper does not "
                    f"hold the DECLARED clearance and DRC will say so. "
                    f"Measured on pluto-rx2-8way 2026-07-30 it is the "
                    f"second: the RF star is routed at 0.36 mm on a 0.14 mm "
                    f"clearance the .kicad_dru never declares, and it costs "
                    f"49 DRC findings that are ONE missing constraint")
        if ok:
            if verbose:
                lines.append("ok   P-LAND " + msg)
        else:
            stats["failed"] += 1
            fails.append(f"FAIL P-LAND {msg} — SHORT BY {floor - w:.3f} mm")
    lines.extend(fails)
    if unparsed:
        lines.append(f"note: {len(unparsed)} .kicad_dru rule(s) have a "
                     f"condition this gate does not model and were NOT "
                     f"applied: {sorted(set(unparsed))}")
    return lines, stats, {"pro": pro_path, "dru": dru_path,
                          "rules": len(rules)}


def by_layer_pads(by_layer, p):
    seen, out = set(), []
    for L in p["layers"]:
        for q in by_layer.get(L, []):
            if id(q) not in seen:
                seen.add(id(q))
                out.append(q)
    return out


def run_land(args):
    total_bad = 0
    graded_boards = 0
    for bp in args.board:
        if not Path(bp).exists():
            print(f"FAIL P-LAND {bp}: no such board — a board that cannot "
                  f"be read is not a board that passed")
            total_bad += 1
            continue
        lines, st, inp = check_board(bp, args.project, args.dru,
                                     args.dirs, args.reach, args.verbose)
        graded_boards += 1
        for L in lines:
            print(L)
        # G-INPUT: name every input the verdict depends on.
        print(f"input: board = {Path(bp).resolve()}")
        print(f"input: floors+relaxations = {Path(inp['dru']).resolve()} "
              f"({inp['rules']} width/clearance rule(s))")
        print(f"input: clearances = {Path(inp['pro']).resolve()}")
        print(f"input: model = {LAUNCH_STEP_MM} mm landing grid inside the "
              f"land (<= {MAX_LAUNCH_PTS} points) x {args.dirs} directions, "
              f"reach {args.reach} mm, other-net lands within "
              f"{NEIGHBOUR_R_MM} mm as obstacles, cap {CAP_MM} mm")
        # M-COVER: the denominator, every bucket named.
        print(f"P-LAND denominator {Path(bp).stem}: {st['graded']} graded / "
              f"{st['copper_pads']} copper pads "
              f"({st['no_floor']} no declared width floor, "
              f"{st['pour_fed']} fed by a same-net POUR, "
              f"{st['via_on_pad']} escaped by a VIA ON THE LAND, "
              f"{st['no_net']} no net, {st['unreached']} UNREACHED); "
              f"{st['relaxed']} graded against a SCOPED floor, "
              f"{st['scoped_clearance']} against a scoped clearance; "
              f"{st['failed']} failing")
        print(f"routed cross-check {Path(bp).stem}: {st['xcheck']} graded "
              f"pad(s) already carry a same-net track, "
              f"{st['xcheck_over']} of them WIDER than this model allows "
              f"(0 = the model is not over-strict on real copper; "
              f"an unrouted board reports 0/0)")
        bad = st["failed"] + st["unreached"]
        if st["graded"] == 0:
            print(f"FAIL P-LAND {Path(bp).stem}: 0 pads graded — no pad on "
                  f"this board resolves a declared track_width floor. A "
                  f"zero denominator is a FAIL, never a pass (canon "
                  f"M-COVER); netclass floors are generated BEFORE routing "
                  f"(canon R1), so 0 means generate_rules has not run.")
            bad += 1
        total_bad += bad
    if total_bad:
        print(LAND_FIX_ORDER)
    verdict = "FAIL" if total_bad else "PASS"
    print(f"P-LAND {verdict}: {graded_boards}/{len(args.board)} board(s) "
          f"graded, {total_bad} problem(s)")
    sys.exit(1 if total_bad else 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("parts", nargs="*", help="part.yaml paths")
    ap.add_argument("--board", action="append", default=[],
                    help="P-LAND: grade landable width per pad on a "
                         ".kicad_pcb (repeatable)")
    ap.add_argument("--project", help="P-LAND: .kicad_pro (default: the "
                                      "board's own stem)")
    ap.add_argument("--dru", help="P-LAND: .kicad_dru (default: the board's "
                                  "own stem)")
    ap.add_argument("--dirs", type=int, default=DIRS,
                    help=f"P-LAND: launch directions sampled (default {DIRS})")
    ap.add_argument("--reach", type=float, default=REACH_MM,
                    help=f"P-LAND: launch length mm (default {REACH_MM})")
    ap.add_argument("--verbose", action="store_true",
                    help="P-LAND: print the passing pads too")
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
    if args.board:
        return run_land(args)
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
