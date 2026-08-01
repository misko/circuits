#!/usr/bin/env python3
"""dru_subject — does a `.kicad_dru` rule still have a SUBJECT on this board?

A preserved rule (see `generate_rules_generic.foreign_dru_rules`) is never
retired, and preservation is one-way, so a rule outlives the geometry it was
written for. `pad_rescue_stubs` is the measured instance: stitch's
`_scope_stub_floor` emits the rule area AND the `.kicad_dru` rule together, but
only `if stub_boxes` — so on a board whose pads all take a via-in-pad barrel the
pass emits no boxes, the rule area is gone from the saved board, and the rule
from an EARLIER run rides along forever as a predicate that can never fire.
That is G-VACUOUS-DRU (see design-policies.md).

MEASURED 2026-07-31, fleet: 6 boards carry a `pad_rescue_stubs` rule.
4 have live subjects (crow-recorder-central-v2 25 members / 24 areas,
pluto-cal-switch 16/16, usb-hub-3s-v3 6/6, pluto-rx2-8way 2/2) and 2 have
ZERO rule areas on the board at all (crow-mic-pod-v2, programmable-usb2-hub).
So the decision is PER BOARD; a blanket delete would drop four live exemptions
and re-open the clean-room 3S stub-floor collision.

WHY TEXT, NOT pcbnew. Two reasons, and the second is the binding one.
  1. `03_src/contracts.md` steps 5 and 9 run `generate_rules_generic.py` under
     "any python3". Importing pcbnew there would make the retirement decision
     conditional on the interpreter — and a capability that silently no-ops
     under half its callers is the defect this module exists to remove.
  2. Canon M1: checker and checked share no method. `gate_contract_audit.py
     --dru` grades the SAME question with pcbnew's object model and geometry.
     If both read the board the same way, the gate proves nothing about the
     generator. It must NOT import this module.

CONSERVATIVE BY CONSTRUCTION. `members()` returns None — "not derivable" —
rather than 0 whenever the condition or the constraint reaches past what this
module indexes. Retirement happens only on a POSITIVE derivation of zero, so
the failure mode is keeping a dead rule (visible, and the audit still grades
it), never dropping a live one.

usage: dru_subject.py <board.kicad_pcb> <board.kicad_dru>   # report members
"""
import math
import re
import sys
from pathlib import Path

#: constraint kinds whose subjects are TRACKS/ARCS/VIAS only — the set this
#: module can index completely. A clearance-family constraint also polices
#: pads, footprint courtyards and zone fill, which reconstructing a footprint
#: transform from text would get subtly wrong; for those `members()` declines.
TRACKLIKE_CONSTRAINTS = {
    "track_width", "via_diameter", "via_drill", "via_count",
    "annular_width", "length", "skew", "diff_pair_gap",
    "diff_pair_uncoupled", "track_angle", "track_segment_length",
}


# ------------------------------------------------------------ s-expressions
def sexp(text):
    """Parse s-expression text into nested lists of str. Small on purpose —
    a `.kicad_pcb` is only ( ) "quoted" and bare atoms."""
    tok = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+')
    stack, cur = [], []
    for m in tok.finditer(text):
        t = m.group(0)
        if t == "(":
            stack.append(cur)
            cur = []
        elif t == ")":
            if not stack:                      # unbalanced; stop where we are
                break
            parent = stack.pop()
            parent.append(cur)
            cur = parent
        elif t.startswith('"'):
            cur.append(t[1:-1].replace('\\"', '"').replace("\\\\", "\\"))
        else:
            cur.append(t)
    return cur


def kids(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


def kid(node, key):
    k = kids(node, key)
    return k[0] if k else None


# ------------------------------------------------------------------ geometry
def _pt_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if (y0 > y) != (y1 > y):
            xx = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            if xx > x:
                inside = not inside
    return inside


def _seg_dist(ax, ay, bx, by, cx, cy, dx, dy):
    """Minimum distance between segments AB and CD (0 if they cross)."""
    def pt_seg(px, py, x0, y0, x1, y1):
        vx, vy = x1 - x0, y1 - y0
        L = vx * vx + vy * vy
        t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - x0) * vx + (py - y0) * vy) / L))
        return math.hypot(px - (x0 + t * vx), py - (y0 + t * vy))

    d1 = (bx - ax) * (dy - cy) - (by - ay) * (dx - cx)
    if abs(d1) > 1e-12:
        t = ((cx - ax) * (dy - cy) - (cy - ay) * (dx - cx)) / d1
        u = ((cx - ax) * (by - ay) - (cy - ay) * (bx - ax)) / d1
        if 0 <= t <= 1 and 0 <= u <= 1:
            return 0.0
    return min(pt_seg(ax, ay, cx, cy, dx, dy), pt_seg(bx, by, cx, cy, dx, dy),
               pt_seg(cx, cy, ax, ay, bx, by), pt_seg(dx, dy, ax, ay, bx, by))


def overlaps(seg, poly, half_width):
    """KiCad's insideArea is true for an item that OVERLAPS the area, not only
    one contained by it (the caveat generate_rules_generic already documents
    for scoped_clearances), so this tests overlap of the item's SHAPE — the
    segment inflated by half its width — against the polygon."""
    (ax, ay), (bx, by) = seg
    if _pt_in_poly(ax, ay, poly) or _pt_in_poly(bx, by, poly):
        return True
    n = len(poly)
    for i in range(n):
        cx, cy = poly[i]
        dx, dy = poly[(i + 1) % n]
        if _seg_dist(ax, ay, bx, by, cx, cy, dx, dy) <= half_width:
            return True
    return False


# ------------------------------------------------------------------ the board
def _layers_of(node):
    """The layer NAMES a zone/track carries; `*.Cu` kept verbatim and matched
    as a wildcard by `_layer_hit`."""
    out = []
    for key in ("layers", "layer"):
        k = kid(node, key)
        if k:
            out += [s for s in k[1:] if isinstance(s, str)]
    return out


def _layer_hit(item_layer, zone_layers):
    for L in zone_layers:
        if L == item_layer:
            return True
        if L.startswith("*.") and item_layer.endswith(L[1:]):
            return True
        if L == "*":
            return True
    return False


def index_board(pcb_path):
    """{"areas": {name: [(layers, polygon)]}, "items": [item], "nets": set,
        "netclasses": set}

    An `item` is {kind, net, layers, seg, half}. Only tracks/arcs/vias are
    indexed — see TRACKLIKE_CONSTRAINTS."""
    root = sexp(Path(pcb_path).read_text(encoding="utf-8-sig"))
    board = root[0] if len(root) == 1 and isinstance(root[0], list) else root

    # net code -> name, for the older `(net <code>)` spelling on items
    codes = {}
    for n in kids(board, "net"):
        if len(n) >= 3:
            codes[n[1]] = n[2]

    def netname(node):
        k = kid(node, "net")
        if not k or len(k) < 2:
            return ""
        v = k[1]
        return codes.get(v, v if not v.isdigit() else "")

    areas = {}
    for z in kids(board, "zone"):
        if kid(z, "keepout") is None:          # a rule area, not a copper pour
            continue
        nm = kid(z, "name")
        if not nm or len(nm) < 2 or not nm[1]:
            continue
        zl = _layers_of(z)
        for poly in kids(z, "polygon"):
            pts = kid(poly, "pts")
            if not pts:
                continue
            xy = [(float(p[1]), float(p[2])) for p in kids(pts, "xy")]
            if len(xy) >= 3:
                areas.setdefault(nm[1], []).append((zl, xy))

    items = []
    for s in kids(board, "segment"):
        a, b = kid(s, "start"), kid(s, "end")
        w = kid(s, "width")
        if not (a and b):
            continue
        items.append({
            "kind": "track", "net": netname(s), "layers": _layers_of(s),
            "seg": ((float(a[1]), float(a[2])), (float(b[1]), float(b[2]))),
            "half": (float(w[1]) / 2 if w else 0.0)})
    for s in kids(board, "arc"):
        a, m, b = kid(s, "start"), kid(s, "mid"), kid(s, "end")
        w = kid(s, "width")
        if not (a and b):
            continue
        pts = [(float(a[1]), float(a[2]))]
        if m:
            pts.append((float(m[1]), float(m[2])))
        pts.append((float(b[1]), float(b[2])))
        for p, q in zip(pts, pts[1:]):         # chord approximation of the arc
            items.append({"kind": "track", "net": netname(s),
                          "layers": _layers_of(s), "seg": (p, q),
                          "half": (float(w[1]) / 2 if w else 0.0)})
    for v in kids(board, "via"):
        at = kid(v, "at")
        size = kid(v, "size")
        if not at:
            continue
        p = (float(at[1]), float(at[2]))
        items.append({"kind": "via", "net": netname(v), "layers": _layers_of(v),
                      "seg": (p, p), "half": (float(size[1]) / 2 if size else 0.0)})

    nets = {i["net"] for i in items if i["net"]} | {n for n in codes.values() if n}
    return {"areas": areas, "items": items, "nets": nets}


# ------------------------------------------------------------------- the rule
_ATOM = re.compile(
    r"(?P<side>[AB])\.(?P<prop>NetClass|NetName)\s*(?P<op>==|!=)\s*'(?P<val>[^']*)'"
    r"|(?P<side2>[AB])\.insideArea\(\s*'(?P<area>[^']*)'\s*\)")
#: everything the atom regex is allowed to leave behind in a conjunct
_NOISE = re.compile(r"[\s()&]|&&")


def parse_rule(block):
    """(name, condition, [constraint kinds]) from one `(rule ...)` block.
    Accepts the QUOTED and the BARE name — stitch writes `(rule
    pad_rescue_stubs`, and a matcher that only reads the quoted form is blind
    to exactly the rule this module is about."""
    name = re.match(r'\(rule\s+"?([^"\s()]+)"?', block)
    cond = re.search(r'\(condition\s+"((?:[^"\\]|\\.)*)"', block)
    return (name.group(1) if name else "",
            cond.group(1).replace('\\"', '"') if cond else None,
            re.findall(r"\(constraint\s+(\w+)", block))


def members(block, inv):
    """How many board items can this rule match? None == NOT DERIVABLE.

    None is returned — never 0 — when the rule has no condition (its subject is
    the whole board), when a constraint reaches past tracks/arcs/vias, or when
    the condition contains an atom this evaluator does not model. Callers must
    treat None as KEEP."""
    _name, cond, constraints = parse_rule(block)
    if cond is None:
        return None
    if not constraints or any(c not in TRACKLIKE_CONSTRAINTS for c in constraints):
        return None

    alts = [a.strip() for a in cond.split("||")]
    parsed = []
    for alt in alts:
        atoms, rest = [], alt
        for m in _ATOM.finditer(alt):
            atoms.append(m)
            rest = rest.replace(m.group(0), "", 1)
        if _NOISE.sub("", rest):               # an operator/atom we do not model
            return None
        # A `B.` atom makes this a question about a PAIR, and counting single
        # items would answer a different one. Every TRACKLIKE constraint is
        # single-item, so a B side here means the rule is not what it looks
        # like — decline rather than guess.
        if any((m.group("side") or m.group("side2")) == "B" for m in atoms):
            return None
        parsed.append(atoms)

    total = 0
    for item in inv["items"]:
        for atoms in parsed:
            ok = True
            for m in atoms:
                if m.group("area") is not None:
                    polys = inv["areas"].get(m.group("area")) or []
                    if not any(_layer_hit(L, zl)
                               for zl, _p in polys for L in item["layers"]
                               ):
                        ok = False
                        break
                    if not any(overlaps(item["seg"], p, item["half"])
                               for zl, p in polys
                               if any(_layer_hit(L, zl) for L in item["layers"])):
                        ok = False
                        break
                elif m.group("prop") == "NetName":
                    hit = item["net"] == m.group("val")
                    if hit != (m.group("op") == "=="):
                        ok = False
                        break
                else:                          # NetClass — not indexed here
                    return None
            if ok:
                total += 1
                break
    return total


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        sys.exit(__doc__.strip().splitlines()[-1])
    inv = index_board(argv[0])
    text = Path(argv[1]).read_text(encoding="utf-8-sig")
    from generate_rules_generic import extract_rules          # noqa: PLC0415
    print(f"dru_subject: {Path(argv[0]).name} — {len(inv['items'])} track/via "
          f"item(s), rule areas {sorted(inv['areas'])}")
    for name, blk in extract_rules(text):
        n = members(blk, inv)
        print(f"  {name:28s} members={'not derivable' if n is None else n}")


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
