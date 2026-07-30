#!/usr/bin/env python3
"""copper_length_audit — R-LEN: REALIZED COPPER LENGTH, measured off the board,
for nets whose electrical purpose is PHASE.

    python3 copper_length_audit.py PROJECT_DIR              # grade the groups
    python3 copper_length_audit.py PROJECT_DIR --census      # every net, measured
    python3 copper_length_audit.py PROJECT_DIR --board B.kicad_pcb
    python3 copper_length_audit.py --root REPO_ROOT          # fleet sweep
    python3 copper_length_audit.py --schema                  # print the schema

Plain python3. No pcbnew, no network, no git. Exit 0 when every declared group
is graded and holds, 1 on any FAIL, 2 when the audit could not run at all.

===========================================================================
WHY THIS EXISTS: TWO BOARDS WHOSE ENTIRE PURPOSE IS A LENGTH, AND A GATE THAT
GRADED THE WORD "length"
===========================================================================

`policy_audit.py` has carried an `R-LEN` row since the canon was written. Until
this file landed it was:

    has_len = bool(re.search(r"length|spread", audit_src, re.I))
    rows.append(("R-LEN", "PASS" if has_len else "N-A", ...))

**R-LEN passed if the word "length" or "spread" appeared anywhere in the
project's `03_src/audit_board.py`.** A COMMENT satisfied it. MEASURED over the
fleet on 2026-07-29, before this gate existed:

| board | pre-fix R-LEN | what the words actually were |
|---|---|---|
| smc0985-cooksense | **PASS** | two COMMENTS about a creepage slot being "lengthened" and an outline notch that "lengthens" a path. Nothing to do with any net. |
| pluto-rx2-8way | **PASS** | comments about equal-length radials, plus an I3 check that measures pad-centre RADIUS — placement, not copper — and whose own text says `STAGE-6 OBLIGATION: equalise ROUTED length to +/-0.10mm`. Nothing enforces that obligation. |
| crow-recorder-central-v2 | **PASS** | the only HONEST pass in the fleet: it really does sum `t.GetLength()` over the USB pair and floor the spread at 1 mm. |
| **pluto-cal-switch** | **N-A** — *"no timing-critical nets declared"* | the board that exists to PUBLISH a length delta had NO length gate at all, and the audit said so in words that read like an absence of requirement. |
| crow-mic-pod-v2, usb-hub-3s-v3 | N-A | correct — neither declares a matched path. |

So 3 of 6 boards passed a length gate on prose, 1 of 6 actually measured
copper, and the ONE board whose release artifact IS a length was graded N-A.
That is canon M-COVER's exact failure shape: a gate reporting success over
input it never looked at. This file is also canon M8 (two-strike promotion):
crow-recorder-central-v2's bespoke USB-pair length check is the first strike
and the pluto pair is the second, so the check becomes shared backend.

THE DEFECT UNDERNEATH IT — WHY PLACEMENT IS NOT PHASE.
`pluto-cal-switch/03_src/audit_board.py` publishes, at PASS:

    A-SYM  11 arm pairs are an exact +14.5 mm translation at identical
           rotation (worst error 0.0 um) — the D4 delta is a placement
           property, not a routing outcome

A-SYM compares footprint `GetPosition()` / `GetOrientationDegrees()`; its
sibling A-SEG sums PAD-TO-PAD straight-line distance. Both are placement
metrics carrying electrical names. The published D4 delta is a PHASE
difference between two RF paths, and **phase is a property of copper.** Two
mirror-perfect placements joined by two differently-meandered traces have
identical A-SYM and different phase; the router that lays that copper is, by
this repo's own contract, STOCHASTIC. So both pluto boards could pass every
gate they own and be wrong in the exact quantity they exist to produce — the
D1 reverse-polarity shape, every artifact self-consistent, the intent
unexpressed.

THE ARITHMETIC, RE-DERIVED HERE FROM THE STACKUP RATHER THAN INHERITED.
Ordered stackup `JLC04161H-7628`, top prepreg h = 0.2104 mm, Dk 4.4, RF trace
w = 0.36 mm (pluto-rx2-8way `nets.yaml`; cal-switch uses 0.35 mm). Hammerstad
microstrip effective permittivity, no thickness correction:

    eps_eff = (er+1)/2 + (er-1)/2 / sqrt(1 + 10h/w)
            = 2.70 + 1.70 / sqrt(1 + 5.844)  = 2.70 + 0.650 = 3.350

    t_pd    = sqrt(eps_eff)/c = 1.8303 / 299.792 mm/ns = 6.105 ps/mm
    lambda_g(6 GHz) = 299.792 / (6 * 1.8303) = 27.29 mm
    phase   = 360 * f * t_pd = 360 * 6e9 * 6.105e-12 = 13.19 deg/mm

ASSUMPTIONS STATED: er = 4.4 as declared in the board's own `nets.yaml` (the
laminate's own datasheet window is 4.2-4.6, which moves t_pd by +-1.7%); no
etch-thickness correction; no dispersion. My 6.105 ps/mm reproduces
pluto-rx2-8way ADR-0003's 6.09 and pluto-cal-switch ADR-0011's 6.0 to within
2%, so the three derivations corroborate each other (canon M1). **13.2 deg per
millimetre at 6 GHz** — the commissioning estimate of 12.7 deg/mm was, if
anything, an under-statement. One millimetre of unmatched copper is the same
order as an entire AoA phase budget.

===========================================================================
WHAT IS MEASURED, AND WHAT IS DELIBERATELY NOT (state it or it is a lie)
===========================================================================

MEASURED, per net, from the shipped `.kicad_pcb` bytes:
  * `(segment ...)` centreline length, Euclidean, per copper layer.
  * `(arc ...)` centreline length as r*theta from its start/mid/end triple.
  * `(via ...)` count, layer span, and its BARREL Z-LENGTH — but only when the
    stackup is DECLARED (see below). A via is real copper on a phase path.

NOT MEASURED, each with its reason, because an unmeasurable term is UNREACHED
and never silently a pass (canon M-COVER):

  1. **PAD-ENTRY COPPER.** The land itself is copper, and a track ends where
     the router chose, not at the pad centre. This gate measures TRACKS AND
     VIAS ONLY, so every absolute figure is reported as a **LOWER BOUND**
     (`>=`) and every derived picosecond with it. The DELTA is a different
     matter: for a matched group whose members are congruent — identical
     footprints at identical rotation, which is exactly what `A-SYM` on
     pluto-cal-switch and ADR-0006(d) on pluto-rx2-8way already require — the
     pad term is IDENTICAL on both members and CANCELS. A group therefore
     declares `congruent_pads: true` to claim that cancellation; without it
     the SPREAD is reported and UNREACHED rather than graded, because a
     comparison of two lower bounds with different unmeasured offsets is not
     a measurement.
  2. **VIA BARREL Z-LENGTH WITHOUT A DECLARED STACKUP.** The generated boards
     in this fleet carry NO `(stackup ...)` block, and `(general (thickness))`
     alone cannot give it: assuming equal dielectric spacing on
     `JLC04161H-7628` (0.2104 / 0.9792 / 0.2104 mm) would put an F->In1 hop at
     0.533 mm instead of 0.210 mm — 2.5x wrong, ~0.3 mm of phantom copper,
     4 deg at 6 GHz. So z-length is derived ONLY from a declared
     `stackup_mm:`; otherwise the member's total is UNREACHED and the via
     count is printed. For the pluto arms this never arises: both ADRs forbid
     vias outright, and `no_vias: true` turns that intent into a FAIL.
  3. **ZONES AND POURS.** A net that reaches a filled polygon has no path
     length — the current spreads. Any zone on a member net makes the member
     UNREACHED. A phase net must never be poured, so this is a real finding.

THE TREE PROBLEM — A NET IS NOT A PATH.
Copper on a net is a graph, and "the length of net X" is ambiguous the moment
it branches (a T to a stub, a shunt cap, a fence tap). This gate builds the
per-net copper graph over layer-aware endpoints (segment ends, arc ends, and
via barrels joining the same x,y on two layers) and reports:

    total_mm     all copper on the net, stubs included. Always defined.
    n_comp       connected components. >1 means the net is not one run.
    n_branch     vertices of degree >= 3.
    n_end        vertices of degree 1 (the terminals, i.e. pad landings).
    path_mm      the longest simple path (graph diameter by edge weight).

**`total_mm` is the graded quantity, and a group must EARN it by declaring
`topology: chain`, which this gate VERIFIES from the copper: ZERO branch
vertices and ZERO cycles.** A graph with neither is a disjoint union of simple
paths, so `total_mm` IS the path length, exactly. A member that declares
`chain` and has a branch is **UNREACHED with its branch count**, and both
`total_mm` and `path_mm` are printed so the reader sees the size of the
ambiguity — not failed, because a legitimate tap on an RF line is a design
question this gate has no standing to decide, and not passed, because the
number would be wrong. `topology: tree` opts into grading `total_mm` on a
branching net and says so on every line.

`n_comp > 1` is reported and is deliberately NOT a failure: two tracks landing
on ONE pad at different points are joined by the LAND, which a pads-free
reader cannot see, so an ordinary routed net reads as several components.
Measured on crow-recorder-central-v2, `USB_DP` is 3 components with 0 branches
— 23.6209 mm of copper and no ambiguity whatsoever. Failing that would
penalise the board for the reader's blindness, which is the adjacent-property
error this repo keeps paying for.

A MEMBER IS A CHAIN OF NETS, NOT ONE NET. pluto-cal-switch's matched arm is
three nets (`LOOP_ARM1` -> `PAD_A2A_1` -> `LOOP_ARM1_SW`) because two series
attenuator chips split it; ADR-0011's own note says the delta is measured
across the WHOLE run. So a member names an ORDERED LIST of nets and its length
is their sum. Declaring only the first net was already an authoring defect
this fleet paid for once, in the netclass.

===========================================================================
THE TOLERANCE: WHAT THE PROCESS CAN HOLD, NOT WHAT WOULD BE NICE
===========================================================================

The instinct is to write `match to 0.05 mm`. That number would be waived
inside a week, and it answers the wrong question. Four measurements decide it,
and three of them are NOT under our control:

  (a) **The vendor's own uncontrolled term is already 0.5 mm of copper.**
      PE42482A-X publishes relative insertion phase with min/typ/max
      (Table 3, PDF p8): at 6 GHz RF2-RF1 is -9.4 / -2.8 / +3.8 deg, a
      **13.2 deg window** = **1.00 mm of copper** at 13.19 deg/mm, part to
      part, on the very paths whose difference is published. Matching copper
      tighter than that buys a quantity you cannot distinguish from the
      switch you bought.
  (b) **Mounting inductance asymmetry is ~2 deg** (0.1 nH ~ 3.8 ohm at 6 GHz,
      ADR-0011 sec.3 / ADR-0006(d)) = 0.15 mm of copper, per solder fillet,
      per unit.
  (c) **JLC etch tolerance perturbs WIDTH, not centreline length** — it moves
      impedance, which is why both boards' `nets.yaml` calls the RF width an
      IMPEDANCE width and forbids "safety" widening. It is not a length term.
      The fab length terms are the outline route (+-0.2 mm, and COMMON MODE
      across notches cut by one tool path, ADR-0011 "what is NOT claimed") and
      the laminate Dk spread (+-1.7% on t_pd, common mode across two arms on
      one panel coupon; only the intra-board Dk GRADIENT is differential, and
      on a 50 mm board that is well under 1%).
  (d) **The one term that IS ours, and it is exact.** Copper length in the
      `.kicad_pcb` is a file property, deterministic to the nanometre. It
      costs nothing to hold to 1 um and nothing to measure.

**CONCLUSION, and it is the whole judgement in this file: the requirement is
not MATCHED, it is KNOWN, STABLE and REPRODUCIBLE.** Both ADRs already say so
in prose — pluto-cal-switch ADR-0011 ("a tolerance band is not a number"),
pluto-rx2-8way ADR-0006 ("what the board owes is CONSTANCY"). So the gate is
built to REPORT AND PIN, not to demand zero, and it carries two numbers with
two different jobs:

  `max_spread_mm` — **a DRIFT ceiling, derived, not a matching target.** The
      static delta is calibrated out; what CANNOT be calibrated out is how the
      delta MOVES with temperature, and ADR-0006(b) shows that term is
      proportional to the length DIFFERENCE: `dtau = TC * dT * dL * t_pd`. At
      the ESTIMATED +100 +-100 ppm/degC for FR-4 over 40 degC, dL = 1 mm gives
      0.024 ps = **0.05 deg at 6 GHz**, and dL = 20 mm (a naive rectangular
      fan-out) gives **1.05 deg**, comparable to the whole AoA budget. So
      **1.0 mm is the defensible ceiling** — it is what the by-construction
      geometry delivers with margin, it is ~1x the vendor's own part-to-part
      window, and it is derived from the drift arithmetic rather than from
      taste. `report` is a legal value and means "no ceiling, publish the
      number": an honest absence, not a silent pass.

  `pin:` — **the REPRODUCIBILITY pin, and this is the check that actually
      guards the release.** A published constant is invalidated by any
      re-route that moves the copper, and the router is stochastic. The
      declaration records the measured spread and a tolerance (0.05 mm =
      0.66 deg is a sensible resolution because it is free — see (d)); the
      gate FAILS when the board drifts off the pinned number. That converts
      "somebody re-routed and the published picoseconds are now fiction" from
      an invisible event into a red gate that forces a re-measure and a
      re-publish. **A calibration board's requirement is that the delta be
      KNOWN, STABLE and REPRODUCIBLE — not that it be zero**, and `pin:` is
      the only one of these two checks that grades that.

WHAT THIS GATE DOES NOT ATTEMPT. It does not length-match anything. KRT's
meander machinery (`diff_pair_loop.py`, `diff_xnet.py`) is DIFF-PAIR shaped —
intra-pair and inter-pair P/N equalisation. The pluto matched paths are
single-ended 50 ohm traces that must match EACH OTHER ACROSS NETS, which is
inter-net skew: a different problem with no tool behind it here. Equalisation
is therefore a HUMAN, ITERATIVE routing task, and this gate is the instrument
that task is steered by.

RECORDED FINDING, 2026-07-29: **NO PER-NET VIA BAN IS ENFORCED AT ROUTE
TIME.** `route_and_stitch_generic.py` and both pluto `route.yaml` files carry
no `no_vias` concept; the only mechanism is a per-WAVE `layers: [F.Cu]`
restriction, which is not per-net and is re-checked by nothing afterwards. One
via on one arm is a pure DIFFERENTIAL error on a published delta (ADR-0006(c):
a via's inductance depends on drill and plating, unspecified per hole). This
gate's `no_vias: true` is therefore the ONLY place that intent is graded, and
it is graded on the copper, after the fact, where it counts.

INDEPENDENCE (canon M1). The board is read here by a dedicated
s-expression block scanner over the shipped text — NOT through pcbnew, which
is what generated and imported the copper, and not through `pcb_toolkit.py`.
`tests/t1_copper_length.py` cross-checks this reader against pcbnew's own
`PCB_TRACK.GetLength()` on a real routed sealed board and requires per-net
agreement to 1 um, so the independence claim is MEASURED rather than asserted.

THE DECLARATION IS CHECKED WHERE IT ENTERS (canon M-ENTRY / ADR-0007). Every
net a `length_match:` group names must exist on the board, and the sibling
gate `net_reference_audit.py` (canon E-NETREF) grades the same names against
the exported netlist as kind **K12**. That coordination is not optional: the
first E-NETREF fleet sweep found **64 of 908 referenced net names absent from
their own board's netlist, 39 of them written against a DATASHEET reference
design's pin function rather than any net the board has.** A tolerance
addressed to a net that does not exist is decoration.

NOT YET WIRED INTO `policy_audit.py`, DELIBERATELY. At landing time
smc0985-cooksense was mid-battery on three order-blockers with `policy_audit`
in flight, and R-LEN's current vacuous PASS is part of that evidence run.
Re-pointing the row would move cooksense from `R-LEN PASS` to `R-LEN N-A`
inside another agent's evidence. An unwired gate plus a measurement is
recoverable in one follow-up; a corrupted seal battery is not. **The follow-up
is owed and is spelled out at the `R-LEN` row in `policy_audit.py`.**
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:                                       # pragma: no cover
    sys.exit("copper_length_audit needs pyyaml")

#: nanometre grid for graph node identity. KiCad stores in nm; 1 nm is exact.
NM = 1_000_000.0

#: the derived stackup constants, re-derived in the docstring above.
T_PD_PS_PER_MM = 6.105        # sqrt(3.350)/c on JLC04161H-7628, w/h = 1.711
DEG_PER_MM_6GHZ = 13.19       # 360 * 6 GHz * t_pd

SCHEMA = """\
# 03_src/rules/nets.yaml — the `length_match:` block (canon R-LEN).
#
# A MATCHED SET IS AN INTENT. Until this schema existed it lived only in ADR
# prose, and prose is not executable: pluto-cal-switch's own audit printed
# "the D4 delta is a placement property, not a routing outcome" while grading
# footprint positions. Phase is a property of COPPER, so the intent has to be
# declared somewhere a gate can reach it and graded against the board.

length_match:
  <GROUP_NAME>:
    adr: 0011                  # REQUIRED. the ADR that emitted this intent.
    intent: >                  # REQUIRED. what the match BUYS, in one para.
      ...
    members:                   # REQUIRED. >= 2. each is an ORDERED net chain:
      ARM1: [LOOP_ARM1, PAD_A2A_1, LOOP_ARM1_SW]      # series parts split a
      ARM2: [LOOP_ARM2, PAD_A2B_1, LOOP_ARM2_SW]      # run into several nets
    topology: chain            # chain (VERIFIED from the copper: 1 component,
                               # 0 branch vertices, 2 terminals) | tree
    congruent_pads: true       # claims the unmeasured pad-entry term is equal
                               # across members and cancels in the delta.
                               # Without it the SPREAD is UNREACHED.
    no_vias: true              # any via on a member net is a FAIL. nothing in
                               # the router enforces this; here is the only
                               # place it is graded.
    max_spread_mm: 1.0         # the DRIFT ceiling (see the module docstring:
                               # derived from TC*dT*dL, NOT a matching target)
                               # or the literal `report` for no ceiling.
    pin:                       # OPTIONAL, and the check that guards a release:
      spread_mm: 0.000         # the PUBLISHED spread this board's artifact
      tol_mm: 0.05             # claims. drift beyond tol_mm FAILS, because a
      measured_on: v1.0        # re-route silently invalidates the published ps
    stackup_mm: [0.2104, 0.9792, 0.2104]   # OPTIONAL, dielectric thickness
                               # between consecutive copper layers, outer to
                               # outer. Required ONLY to price via barrels;
                               # without it a member carrying a via is
                               # UNREACHED, never passed.
    phase:                     # OPTIONAL reporting aid, never a gate
      t_pd_ps_per_mm: 6.0
      f_ghz: 6.0
      stackup: JLC04161H-7628
"""


class AuditError(Exception):
    """The audit could not run. Exit 2 — never a silent zero (canon M-COVER)."""


# ============================================================ the board reader
# An INDEPENDENT reader (canon M1): pcbnew generated and imported this copper,
# so pcbnew is not allowed to be the authority on how long it is.

def _blocks(text, tag):
    """Yield the body text of every TOP-LEVEL `(tag ...)` item.

    Paren matching, quote-aware — a `(net "GND (analog)")` would otherwise end
    the block early. Top level only: `\\n\\t(` is the KiCad 9 indent for a
    board child, which keeps `(via ...)`-shaped text inside a footprint or a
    zone's `(fill)` out of the answer.
    """
    open_pat = f"\n\t({tag}"
    i = text.find(open_pat)
    while i != -1:
        j = i + 2                                  # at the '('
        depth, k, in_str = 0, j, False
        while k < len(text):
            c = text[k]
            if in_str:
                if c == "\\":
                    k += 2
                    continue
                if c == '"':
                    in_str = False
            elif c == '"':
                in_str = True
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        yield text[j:k + 1]
        i = text.find(open_pat, k)


_XY = r"([-\d.eE+]+)\s+([-\d.eE+]+)"


def _pt(body, key):
    m = re.search(rf"\({key}\s+{_XY}", body)
    return (float(m.group(1)), float(m.group(2))) if m else None


def _net(body):
    m = re.search(r'\(net\s+"([^"]*)"\)', body)
    if m:
        return m.group(1)
    m = re.search(r"\(net\s+(\d+)\)", body)          # numeric form, older files
    return f"#{m.group(1)}" if m else None


def arc_len(s, m, e):
    """Centreline length of a KiCad arc from its start/mid/end triple."""
    ax, ay = s
    bx, by = m
    cx, cy = e
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-12:                              # collinear: it is a line
        return math.dist(s, e)
    ux = ((ax ** 2 + ay ** 2) * (by - cy) + (bx ** 2 + by ** 2) * (cy - ay)
          + (cx ** 2 + cy ** 2) * (ay - by)) / d
    uy = ((ax ** 2 + ay ** 2) * (cx - bx) + (bx ** 2 + by ** 2) * (ax - cx)
          + (cx ** 2 + cy ** 2) * (bx - ax)) / d
    r = math.dist((ux, uy), s)
    if r <= 0:
        return math.dist(s, e)
    a0 = math.atan2(ay - uy, ax - ux)
    a1 = math.atan2(by - uy, bx - ux)
    a2 = math.atan2(cy - uy, cx - ux)

    def sweep(f, t):
        return (t - f) % (2 * math.pi)
    # the arc runs start -> mid -> end; pick the direction mid lies on.
    if sweep(a0, a1) <= sweep(a0, a2):
        total = sweep(a0, a2)
    else:
        total = 2 * math.pi - sweep(a0, a2)
    return r * total


def copper_layers(text):
    """Ordered copper layer names, outer to outer, from the `(layers ...)` map.

    KiCad's layer INDEX order is F=0, B=2, then inners 4,6,8...; the physical
    stack is F, In1, In2, ..., B. Ordering by index would put B second and put
    every via span on the wrong dielectric, so the physical order is rebuilt by
    name (In<N> sorts numerically), never by the file's index.
    """
    seen = []
    for body in _blocks(text, "layers"):
        for m in re.finditer(r'\(\d+\s+"([^"]+)"\s+(signal|power|mixed|jumper)',
                             body):
            seen.append(m.group(1))
        break
    inners = sorted((n for n in seen if re.fullmatch(r"In\d+\.Cu", n)),
                    key=lambda n: int(re.search(r"\d+", n).group()))
    out = ([n for n in seen if n == "F.Cu"] + inners
           + [n for n in seen if n == "B.Cu"])
    return out


def read_copper(path):
    """{net -> {'segs': [...], 'vias': [...], 'zones': n}} from shipped bytes.

    A seg is (layer, (x1,y1), (x2,y2), length_mm); a via is (layer_a, layer_b,
    (x,y)). Lengths are CENTRELINE. Nothing here consults pcbnew.
    """
    text = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    nets = {}

    def slot(n):
        return nets.setdefault(n, {"segs": [], "vias": [], "zones": 0})

    for body in _blocks(text, "segment"):
        n, a, b = _net(body), _pt(body, "start"), _pt(body, "end")
        lm = re.search(r'\(layer\s+"([^"]+)"', body)
        if n is None or a is None or b is None or lm is None:
            raise AuditError(f"{Path(path).name}: unparseable (segment ...) — "
                             f"refusing to under-report copper (canon M-COVER)")
        slot(n)["segs"].append((lm.group(1), a, b, math.dist(a, b)))
    for body in _blocks(text, "arc"):
        n = _net(body)
        a, mid, b = _pt(body, "start"), _pt(body, "mid"), _pt(body, "end")
        lm = re.search(r'\(layer\s+"([^"]+)"', body)
        if n is None or a is None or mid is None or b is None or lm is None:
            raise AuditError(f"{Path(path).name}: unparseable (arc ...) — "
                             f"refusing to under-report copper (canon M-COVER)")
        slot(n)["segs"].append((lm.group(1), a, b, arc_len(a, mid, b)))
    for body in _blocks(text, "via"):
        n, at = _net(body), _pt(body, "at")
        lm = re.search(r'\(layers\s+"([^"]+)"\s+"([^"]+)"', body)
        if n is None or at is None or lm is None:
            raise AuditError(f"{Path(path).name}: unparseable (via ...) — "
                             f"refusing to under-report copper (canon M-COVER)")
        slot(n)["vias"].append((lm.group(1), lm.group(2), at))
    for body in _blocks(text, "zone"):
        m = re.search(r'\(net_name\s+"([^"]*)"\)', body) or re.search(
            r'\(net\s+"([^"]*)"\)', body)
        if m and m.group(1):
            slot(m.group(1))["zones"] += 1
    return nets, copper_layers(text), text


# ================================================================ the geometry
def _node(xy, layer):
    return (int(round(xy[0] * NM)), int(round(xy[1] * NM)), layer)


def net_geometry(entry, layer_order, stackup_mm=None):
    """Measure ONE net's copper. Returns a dict; nothing here can raise.

    `via_z_mm` is None when the stackup was not declared — the caller must
    treat that as UNREACHED rather than as zero (canon M-COVER: an unmeasured
    term is not a measured zero).
    """
    adj = {}
    track_mm = 0.0
    for layer, a, b, ln in entry["segs"]:
        track_mm += ln
        u, v = _node(a, layer), _node(b, layer)
        adj.setdefault(u, []).append((v, ln))
        adj.setdefault(v, []).append((u, ln))
    idx = {n: i for i, n in enumerate(layer_order)}
    via_z, via_unpriced = 0.0, 0
    for la, lb, at in entry["vias"]:
        if stackup_mm and la in idx and lb in idx and len(stackup_mm) >= 1:
            lo, hi = sorted((idx[la], idx[lb]))
            span = sum(stackup_mm[lo:hi]) if hi <= len(stackup_mm) else None
        else:
            span = None
        if span is None:
            via_unpriced += 1
            span = 0.0
        else:
            via_z += span
        u, v = _node(at, la), _node(at, lb)
        adj.setdefault(u, []).append((v, span))
        adj.setdefault(v, []).append((u, span))

    # components / degrees / the longest path
    #
    # LONGEST SIMPLE PATH IS NP-HARD ON A CYCLIC GRAPH, and the first version of
    # this function pretended otherwise: it relaxed "keep the longer distance"
    # from every terminal, which on a GND pour's stitch mesh walks the cycle
    # forever. It did not return on crow-mic-pod-v2. So the exact tractable
    # case is computed and the intractable one is REFUSED by name:
    #   * a TREE component (|E| == |V| - 1) -> weighted diameter by double
    #     sweep, exact and linear.
    #   * a component with a CYCLE -> `path_mm` is None for the whole net, with
    #     the cycle count. A cyclic phase net is a finding in its own right (a
    #     loop in a 50-ohm run is a resonator), so refusing to invent a number
    #     is the correct outcome, not a limitation to apologise for.
    deg = {n: len(e) for n, e in adj.items()}
    n_edge = sum(deg.values()) // 2
    seen, comps, cyclic = set(), 0, 0
    longest = 0.0

    def sweep(src, comp_set):
        dist = {src: 0.0}
        stack2 = [src]
        while stack2:                       # a tree: each vertex is reached once
            x = stack2.pop()
            for y, w in adj[x]:
                if y not in dist:
                    dist[y] = dist[x] + w
                    stack2.append(y)
        far = max(dist, key=dist.get)
        return far, dist[far]

    for start in adj:
        if start in seen:
            continue
        comps += 1
        stack, comp = [start], []
        seen.add(start)
        while stack:
            x = stack.pop()
            comp.append(x)
            for y, _ in adj[x]:
                if y not in seen:
                    seen.add(y)
                    stack.append(y)
        cs = set(comp)
        ce = sum(deg[x] for x in cs) // 2
        if ce != len(cs) - 1:
            cyclic += 1
            continue
        far, _ = sweep(start, cs)
        _, d = sweep(far, cs)
        longest = max(longest, d)

    return {
        "track_mm": track_mm,
        "via_z_mm": None if via_unpriced else via_z,
        "via_unpriced": via_unpriced,
        "n_via": len(entry["vias"]),
        "n_seg": len(entry["segs"]),
        "n_zone": entry["zones"],
        "n_comp": comps,
        "n_cyclic": cyclic,
        "n_branch": sum(1 for n in deg if deg[n] >= 3),
        "n_end": sum(1 for n in deg if deg[n] == 1),
        "n_edge": n_edge,
        "path_mm": None if cyclic else longest,
        "total_mm": track_mm + (via_z if not via_unpriced else 0.0),
    }


# ============================================================== the declaration
def load_groups(proj):
    """`length_match:` out of 03_src/rules/nets.yaml, schema-checked at load.

    A malformed declaration is an AuditError (exit 2), never a skip: the whole
    point is that the intent has a home a gate can reach.
    """
    p = Path(proj) / "03_src" / "rules" / "nets.yaml"
    if not p.exists():
        return {}, p
    try:
        doc = yaml.safe_load(p.read_text(encoding="utf-8-sig")) or {}
    except Exception as e:
        raise AuditError(f"{p}: unparseable YAML ({e})")
    groups = doc.get("length_match") or {}
    if not isinstance(groups, dict):
        raise AuditError(f"{p}: `length_match:` must be a mapping of "
                         f"GROUP -> declaration, got {type(groups).__name__}")
    for g, d in groups.items():
        if not isinstance(d, dict):
            raise AuditError(f"{p}: length_match.{g} must be a mapping")
        for req in ("adr", "intent", "members"):
            if not d.get(req):
                raise AuditError(f"{p}: length_match.{g} has no `{req}:` — a "
                                 f"tolerance with no ADR and no stated intent "
                                 f"is a number nobody can re-derive (canon M4)")
        mem = d["members"]
        if not isinstance(mem, dict) or len(mem) < 2:
            raise AuditError(f"{p}: length_match.{g}.members must be a mapping "
                             f"of >= 2 named net chains (a group of one has no "
                             f"spread to grade)")
        for name, chain in mem.items():
            if not isinstance(chain, list) or not chain or \
                    not all(isinstance(x, str) for x in chain):
                raise AuditError(f"{p}: length_match.{g}.members.{name} must be "
                                 f"an ORDERED list of net names (a member is a "
                                 f"CHAIN: series parts split one run into "
                                 f"several nets)")
        tol = d.get("max_spread_mm", "report")
        if tol != "report" and not isinstance(tol, (int, float)):
            raise AuditError(f"{p}: length_match.{g}.max_spread_mm must be a "
                             f"number or the literal `report`, got {tol!r}")
        top = d.get("topology", "chain")
        if top not in ("chain", "tree"):
            raise AuditError(f"{p}: length_match.{g}.topology must be `chain` "
                             f"or `tree`, got {top!r}")
        pin = d.get("pin")
        if pin is not None:
            if not isinstance(pin, dict) or "spread_mm" not in pin \
                    or "tol_mm" not in pin:
                raise AuditError(f"{p}: length_match.{g}.pin needs both "
                                 f"`spread_mm:` and `tol_mm:` — a pin with no "
                                 f"tolerance cannot be checked")
    return groups, p


def find_board(proj, override=None):
    if override:
        b = Path(override)
        if not b.exists():
            raise AuditError(f"--board {b} does not exist")
        return b
    cands = sorted((Path(proj) / "04_kicad").glob("*.kicad_pcb"))
    if not cands:
        return None
    name = Path(proj).name.replace("-", "_")
    for c in cands:                    # prefer the board named for the project
        if c.stem == name:
            return c
    return cands[0]


# ==================================================================== grading
def grade(proj, board_override=None):
    proj = Path(proj)
    groups, decl = load_groups(proj)
    board = find_board(proj, board_override)
    res = {"project": proj.name, "declaration": str(decl),
           "board": str(board) if board else None,
           "groups": [], "fails": [], "unreached": [],
           "n_group": len(groups), "n_member": 0, "n_measured": 0}
    if not groups:
        return res
    if board is None:
        res["unreached"].append(
            f"{proj.name}: {len(groups)} group(s) declared and NO board in "
            f"04_kicad/ — nothing to measure")
        for g in groups:
            res["groups"].append({"name": g, "verdict": "UNREACHED",
                                  "why": "no board", "members": []})
            res["n_member"] += len(groups[g]["members"])
        return res

    nets, layer_order, _ = read_copper(board)
    board_nets = set(nets)

    for gname, d in groups.items():
        stack = d.get("stackup_mm")
        tol = d.get("max_spread_mm", "report")
        top = d.get("topology", "chain")
        row = {"name": gname, "adr": d["adr"], "topology": top,
               "max_spread_mm": tol, "members": [], "verdict": "PASS",
               "why": "", "spread_mm": None}
        ghosts = []
        for mname, chain in d["members"].items():
            res["n_member"] += 1
            m = {"name": mname, "nets": list(chain), "total_mm": 0.0,
                 "path_mm": 0.0, "n_via": 0, "n_zone": 0, "n_branch": 0,
                 "n_comp": 0, "n_end": 0, "n_cyclic": 0,
                 "measured": True, "why": []}
            for n in chain:
                if n not in board_nets:
                    # No copper AND no net: distinguish the two. A net with no
                    # copper is unrouted; a net the board does not have at all
                    # is a GHOST reference (canon E-NETREF, kind K12).
                    ghosts.append(n)
                    m["measured"] = False
                    m["why"].append(f"{n}: no copper on this board")
                    continue
                gg = net_geometry(nets[n], layer_order, stack)
                m["total_mm"] += gg["total_mm"]
                m["path_mm"] += (gg["path_mm"] or 0.0)
                for k in ("n_via", "n_zone", "n_branch", "n_comp", "n_end",
                          "n_cyclic"):
                    m[k] += gg[k]
                if gg["n_cyclic"]:
                    m["measured"] = False
                    m["why"].append(
                        f"{n}: {gg['n_cyclic']} copper component(s) contain a "
                        f"CYCLE, so no path length exists (a loop in a 50-ohm "
                        f"run is a resonator, not a wire) — total "
                        f"{gg['total_mm']:.4f} mm printed, path refused")
                if gg["n_zone"]:
                    m["measured"] = False
                    m["why"].append(f"{n}: {gg['n_zone']} zone(s) on this net — "
                                    f"poured copper has no path length")
                if gg["via_unpriced"]:
                    m["measured"] = False
                    m["why"].append(
                        f"{n}: {gg['via_unpriced']} via(s) and no `stackup_mm:` "
                        f"declared — the barrel z-length is not derivable from "
                        f"a board that carries no (stackup) block")
                # `topology: chain` is verified on the two properties that are
                # facts about the BOARD rather than about this reader: NO branch
                # vertex and NO cycle. A graph with neither is a disjoint union
                # of simple paths, so `total_mm` IS the path length — exactly.
                #
                # `n_comp > 1` is deliberately NOT a failure here, and getting
                # that wrong is how this check would have been useless: two
                # tracks landing on ONE pad at different points are joined by
                # the LAND, which a pads-free reader cannot see, so a perfectly
                # ordinary routed net reads as several components. Measured on
                # crow-recorder-central-v2: USB_DP is 3 components, 0 branches
                # — 23.6209 mm of copper and no ambiguity at all. Failing it
                # would have penalised the board for the reader's blindness.
                if top == "chain" and gg["n_seg"] and gg["n_branch"]:
                    m["measured"] = False
                    m["why"].append(
                        f"{n}: declared `topology: chain` but the copper has "
                        f"{gg['n_branch']} BRANCH vertex/vertices (a real T or "
                        f"stub) across {gg['n_comp']} component(s) — total "
                        f"{gg['total_mm']:.4f} mm includes the stub and the "
                        f"longest path is {gg['path_mm']} mm, so which number "
                        f"is 'the length' is a design question this gate has no "
                        f"standing to answer. Declare `topology: tree` to grade "
                        f"the total, or remove the stub.")
                if d.get("no_vias") and gg["n_via"]:
                    res["fails"].append(
                        f"R-LEN-VIA [{gname}/{mname}] {n} carries {gg['n_via']} "
                        f"via(s) on a group declared `no_vias: true` (ADR-"
                        f"{d['adr']}) — a via's inductance depends on drill and "
                        f"plating, unspecified per hole, so one via on one "
                        f"member is a pure DIFFERENTIAL error on a published "
                        f"delta. NOTHING IN THE ROUTER ENFORCES THIS.")
                    row["verdict"] = "FAIL"
            if m["measured"]:
                res["n_measured"] += 1
            row["members"].append(m)

        if ghosts:
            # unrouted vs ghost: net_reference_audit K12 grades the netlist
            # side; here the honest statement is "no copper", because a board
            # mid-pipeline is the normal case and must not read as a defect.
            row["verdict"] = "UNREACHED" if row["verdict"] != "FAIL" else "FAIL"
            row["why"] = (f"{len(ghosts)} member net(s) carry no copper on "
                          f"{Path(board).name}: {', '.join(sorted(set(ghosts)))}"
                          f" — the board is unrouted or partly routed. E-NETREF "
                          f"K12 grades these names against the NETLIST.")
            res["unreached"].append(f"R-LEN-UNREACHED [{gname}] {row['why']}")
            res["groups"].append(row)
            continue

        unm = [m for m in row["members"] if not m["measured"]]
        if unm:
            if row["verdict"] != "FAIL":
                row["verdict"] = "UNREACHED"
            row["why"] = "; ".join(w for m in unm for w in m["why"])
            res["unreached"].append(f"R-LEN-UNREACHED [{gname}] {row['why']}")
            res["groups"].append(row)
            continue

        lens = [m["total_mm"] for m in row["members"]]
        spread = max(lens) - min(lens)
        row["spread_mm"] = spread
        if not d.get("congruent_pads"):
            row["verdict"] = "UNREACHED" if row["verdict"] != "FAIL" else "FAIL"
            row["why"] = (
                f"spread {spread:.4f} mm MEASURED but not graded: the group does "
                f"not declare `congruent_pads: true`, so the unmeasured "
                f"pad-entry copper may differ between members and a comparison "
                f"of two lower bounds is not a measurement")
            res["unreached"].append(f"R-LEN-UNREACHED [{gname}] {row['why']}")
            res["groups"].append(row)
            continue

        if tol != "report" and spread > float(tol) + 1e-9:
            row["verdict"] = "FAIL"
            res["fails"].append(
                f"R-LEN-SPREAD [{gname}] realized copper spread "
                f"{spread:.4f} mm exceeds max_spread_mm {tol} (ADR-{d['adr']}). "
                f"At {DEG_PER_MM_6GHZ:.2f} deg/mm that is "
                f"{spread * DEG_PER_MM_6GHZ:.2f} deg at 6 GHz. Members: "
                + ", ".join(f"{m['name']}={m['total_mm']:.4f}"
                            for m in row["members"]))
        pin = d.get("pin")
        if pin:
            drift = abs(spread - float(pin["spread_mm"]))
            row["pin_drift_mm"] = drift
            if drift > float(pin["tol_mm"]) + 1e-9:
                row["verdict"] = "FAIL"
                res["fails"].append(
                    f"R-LEN-PIN [{gname}] the copper has MOVED off the "
                    f"published number: measured spread {spread:.4f} mm vs "
                    f"pinned {pin['spread_mm']} +-{pin['tol_mm']} mm "
                    f"(drift {drift:.4f} mm = "
                    f"{drift * DEG_PER_MM_6GHZ:.2f} deg at 6 GHz, measured_on "
                    f"{pin.get('measured_on', '?')}). The published delta no "
                    f"longer describes this board — re-measure and re-publish.")
        res["groups"].append(row)
    return res


# ===================================================================== report
def report(res, out=print, verbose=True):
    ok = not res["fails"]
    out(f"R-LEN  copper_length_audit — {res['project']}")
    out(f"  declaration: {res['declaration']}")
    out(f"  board:       {res['board'] or '(none in 04_kicad/)'}")
    if not res["n_group"]:
        out("  N-A: no `length_match:` block in 03_src/rules/nets.yaml — this "
            "board declares no net whose purpose is phase.")
        out("  0 group(s) graded / 0 declared, 0 member path(s) measured / 0")
        return ok
    out("  MEASURED: track centrelines + arc centrelines + via barrels. NOT "
        "measured: pad-entry copper (so every absolute is a LOWER BOUND), and "
        "via barrels without a declared stackup_mm.")
    for g in res["groups"]:
        sp = ("-" if g["spread_mm"] is None else f"{g['spread_mm']:.4f} mm")
        out(f"  [{g['verdict']:<9}] {g['name']}  ADR-{g.get('adr')}  "
            f"topology={g.get('topology')}  spread={sp}  "
            f"ceiling={g.get('max_spread_mm')}")
        if g["spread_mm"] is not None:
            out(f"      = {g['spread_mm'] * T_PD_PS_PER_MM:.3f} ps, "
                f"{g['spread_mm'] * DEG_PER_MM_6GHZ:.2f} deg at 6 GHz "
                f"({T_PD_PS_PER_MM} ps/mm, {DEG_PER_MM_6GHZ} deg/mm derived)")
        if verbose:
            for m in g["members"]:
                out(f"      {m['name']:<10s} >= {m['total_mm']:9.4f} mm  "
                    f"path {m['path_mm']:9.4f}  vias {m['n_via']}  "
                    f"zones {m['n_zone']}  branch {m['n_branch']}  "
                    f"comp {m['n_comp']}  ends {m['n_end']}  "
                    f"nets {'+'.join(m['nets'])}")
        if g["why"]:
            out(f"      why: {g['why']}")
    for f in res["fails"]:
        out(f"  FAIL {f}")
    for u in res["unreached"]:
        out(f"  {u}")
    graded = sum(1 for g in res["groups"] if g["verdict"] in ("PASS", "FAIL"))
    out(f"  {graded} group(s) graded / {res['n_group']} declared, "
        f"{res['n_measured']} member path(s) measured / {res['n_member']}, "
        f"{len(res['unreached'])} UNREACHED")
    # An UNREACHED group must NEVER read as PASS on the bottom line — that is
    # the whole vacuity this gate replaces. `--strict` makes it exit 1.
    if not ok:
        out(f"  FAIL R-LEN {res['project']}")
    elif res["unreached"]:
        out(f"  UNREACHED R-LEN {res['project']}: {len(res['unreached'])} of "
            f"{res['n_group']} group(s) could not be measured — NOT a PASS")
    else:
        out(f"  PASS R-LEN {res['project']}")
    return ok


def census(proj, board_override=None, out=print, min_mm=0.0):
    """Per-net realized copper length for EVERY net. The demonstration mode:
    it needs no declaration, so it works on any routed board in the fleet."""
    board = find_board(proj, board_override)
    if board is None:
        raise AuditError(f"{proj}: no .kicad_pcb in 04_kicad/")
    nets, layer_order, _ = read_copper(board)
    rows = []
    for n, e in sorted(nets.items()):
        g = net_geometry(e, layer_order, None)
        if g["n_seg"] or g["n_via"]:
            rows.append((n, g))
    out(f"R-LEN census — {board}")
    out(f"  copper layer order (physical): {' -> '.join(layer_order)}")
    out(f"  {'net':<22s} {'track_mm':>10s} {'path_mm':>9s} {'seg':>4s} "
        f"{'via':>4s} {'zone':>4s} {'br':>3s} {'cmp':>3s} {'end':>4s}")
    tot = 0.0
    for n, g in sorted(rows, key=lambda r: -r[1]["track_mm"]):
        tot += g["track_mm"]
        if g["track_mm"] >= min_mm:
            pm = "  CYCLIC" if g["path_mm"] is None else f"{g['path_mm']:9.4f}"
            out(f"  {n[:22]:<22s} {g['track_mm']:10.4f} {pm:>9s} "
                f"{g['n_seg']:4d} {g['n_via']:4d} {g['n_zone']:4d} "
                f"{g['n_branch']:3d} {g['n_comp']:3d} {g['n_end']:4d}")
    nv = sum(g["n_via"] for _, g in rows)
    out(f"  {len(rows)} net(s) measured / {len(nets)} net(s) with any copper "
        f"or pour; {tot:.3f} mm of track+arc centreline total")
    out(f"  {nv} via barrel(s) NOT priced: this board carries no (stackup) "
        f"block, so z-length is UNREACHED, not zero (canon M-COVER)")
    return rows


# ======================================================================= main
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="R-LEN: realized copper length for phase-critical nets")
    ap.add_argument("project", nargs="?", help="PROJECT_DIR to grade")
    ap.add_argument("--board", help="grade this .kicad_pcb instead of 04_kicad/")
    ap.add_argument("--root", help="repo root: grade every projects/* board")
    ap.add_argument("--census", action="store_true",
                    help="print realized copper length for EVERY net")
    ap.add_argument("--min-mm", type=float, default=0.0,
                    help="census: only print nets at or above this length")
    ap.add_argument("--schema", action="store_true",
                    help="print the length_match: schema and exit")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 when any declared group is UNREACHED (an "
                         "unmeasured intent is a coverage gap, not a pass)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)

    if a.schema:
        print(SCHEMA)
        return 0
    if not a.project and not a.root:
        ap.error("give a PROJECT_DIR, or --root REPO, or --schema")

    try:
        if a.census:
            census(a.project, a.board, min_mm=a.min_mm)
            return 0
        if a.root:
            root = Path(a.root)
            projs = sorted(p for p in (root / "projects").iterdir()
                           if p.is_dir() and (p / "03_src").is_dir())
            allres, bad = [], 0
            for p in projs:
                r = grade(p)
                allres.append(r)
                good = report(r, verbose=not a.quiet)
                if not good or (a.strict and r["unreached"]):
                    bad += 1
                print()
            ng = sum(r["n_group"] for r in allres)
            nm = sum(r["n_measured"] for r in allres)
            nt = sum(r["n_member"] for r in allres)
            print(f"FLEET: {len(projs)} project(s), {ng} length_match group(s) "
                  f"declared, {nm} member path(s) measured / {nt}, "
                  f"{bad} project(s) FAIL")
            if a.json:
                print(json.dumps(allres, indent=1, default=str))
            return 1 if bad else 0
        res = grade(a.project, a.board)
        ok = report(res, verbose=not a.quiet)
        if a.json:
            print(json.dumps(res, indent=1, default=str))
        if not ok:
            return 1
        return 1 if (a.strict and res["unreached"]) else 0
    except AuditError as e:
        print(f"  FAIL R-LEN UNGRADED: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
