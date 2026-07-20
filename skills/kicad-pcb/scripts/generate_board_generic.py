#!/usr/bin/env python3
"""generate_board_generic — ONE parameterized board generator, driven by a
small declarative per-board floorplan YAML, replacing the hand-written
`03_src/generate_board.py` that every project used to carry (290-780 lines
each, pairwise 295-869 diff-lines apart).

WHY. tscircuit replaced schematic authoring but never touched the board
backend, so each board re-implemented the SAME pipeline with different
constants: parse netlist -> nets -> outline -> mounting holes -> place
footprints -> orientation asserts -> legalize floaters -> design settings ->
zones -> silk captions -> refdes de-collision (F.SilkS + F.Fab copy) -> save.
This script IS that pipeline; the YAML supplies only the constants.

    /usr/bin/python3 generate_board_generic.py 03_src/floorplan.yaml
    /usr/bin/python3 generate_board_generic.py floorplan.yaml -o scratch/x.kicad_pcb

Needs the KiCad-bundled interpreter (`/usr/bin/python3`) for `pcbnew`.

HARD ERRORS (never silent — these are the defects that shipped before):
  * a component with no FPID in the netlist and no 02_parts override
  * an FPID whose footprint is not found in any configured library
  * a netlist pad with no corresponding board pad
  * a failed orientation/polarity assert
  * the legalizer failing to find a clear spot for a part
Missing FPID is THE one that must never degrade to a warning: a silently
un-placed part is an electrically-wrong board that still passes DRC.

CONFIG SCHEMA — see `references/floorplan-schema.md`; a real 50-line example
is `projects/cook-loadcell/03_src/floorplan.yaml`. Top-level keys:

  project:    name, netlist, output, parts_dir
  board:      outline (x0/y0/x1/y1 or x0/y0/w/h), corner_cut, edge_width,
              layers, mounting_holes {footprint, refdes_prefix, at[]}
  libraries:  list of ".pretty" search roots; a bare dir is treated as a
              KiCad-style root holding "<lib>.pretty", a {lib,path} entry
              binds one library name to one explicit .pretty dir
  placement:  anchors {REF: [x,y,rot]}, seeds {REF: [x,y]}, regions,
              patterns[] (glob -> region/near/attrs/pad_overrides),
              legalize {enable, clearance, edge_margin, hole_keepout, ring_max}
  design_rules: pcbnew design-settings floors (mm)
  zones:      list of {net, layers, priority, outline|region|board,
                       connect: thermal|full, min_thickness, clearance}
  keepouts:   list of {region|points, layers, name, tracks/vias/pours}
  silk:       captions[], refdes {size, min_size, fab_copy, clearance},
              labels {match, from: value|net} for functional captions
  asserts:    pad_net[] {ref, pad, net}, pad_order[] {ref, pads, axis}

Everything not supplied falls back to a documented default, so a plain
rectangular 2-layer board with a GND pour needs ~25 lines of YAML.
"""
import argparse
import fnmatch
import json
import math
import os
import re
import sys
from pathlib import Path

import pcbnew
import yaml

# Reuse the PROVEN per-board FPID override loader (02_parts/*/part.yaml ->
# FPID) rather than re-deriving it: it is the same source of truth the
# schematic converter uses, so board and sheet cannot disagree on footprints.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from circuit_json_to_kicad_sch import load_part_overrides
except Exception:                                            # pragma: no cover
    def load_part_overrides(parts_dir):
        return {}

MM = pcbnew.ToMM
STD_FP_ROOT = "/usr/share/kicad/footprints"


# ---------------------------------------------------------------- errors
class FloorplanError(RuntimeError):
    """Any hard, board-invalidating error. Never caught internally."""


def die(msg):
    raise FloorplanError(msg)


# ------------------------------------------------------------- netlist IO
def parse_netlist(path):
    """KiCad .net -> ({ref: (fpid, value)}, {(ref,pad): net}, {nets}).

    Identical grammar to every bespoke generator (they all carried this same
    regex pair); centralised here so a netlister change is a one-line fix.
    """
    path = Path(path)
    if not path.is_file():
        die(f"netlist not found: {path}")
    s = path.read_text()
    comps = {}
    for m in re.finditer(
            r'\(comp\s+\(ref\s+"([^"]+)"\)(.*?)(?=\(comp\s+\(ref|\(libparts)', s, re.S):
        ref, body = m.group(1), m.group(2)
        fp = re.search(r'\(footprint\s+"([^"]*)"\)', body)
        val = re.search(r'\(value\s+"([^"]*)"\)', body)
        comps[ref] = (fp.group(1) if fp else "", val.group(1) if val else "")
    if not comps:
        die(f"parsed 0 components from {path}")
    pad_net, nets = {}, set()
    for m in re.finditer(
            r'\(net\s+\(code\s+"\d+"\)\s+\(name\s+"([^"]+)"\)(.*?)(?=\(net\s+\(code|\Z)',
            s, re.S):
        name, body = m.group(1), m.group(2)
        nets.add(name)
        for r, p in re.findall(r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)', body):
            pad_net[(r, p)] = name
    if not nets:
        die(f"parsed 0 nets from {path}")
    return comps, pad_net, nets


# ------------------------------------------------------- footprint loading
class FootprintResolver:
    """FPID -> loaded FOOTPRINT, over an ordered list of library roots.

    Two kinds of root, because real projects mix both:
      * a KiCad-style ROOT dir holding many "<lib>.pretty" subdirs
        (/usr/share/kicad/footprints) — `lib` part of the FPID selects one
      * an explicit {lib: pod, path: 03_src/lib/pod.pretty} binding for a
        project-local library
    A missing FPID or an unfound footprint is a HARD ERROR, always.
    """

    def __init__(self, libraries, base, parts_dir=None):
        self.roots = []          # (libname_or_None, path)
        for entry in libraries or [STD_FP_ROOT]:
            if isinstance(entry, dict):
                lib = entry.get("lib")
                p = (base / entry["path"]).resolve() if not os.path.isabs(entry["path"]) \
                    else Path(entry["path"])
                self.roots.append((lib, p))
            else:
                p = Path(entry) if os.path.isabs(entry) else (base / entry).resolve()
                self.roots.append((None, p))
        # 02_parts/*/part.yaml FPID overrides, for netlists with a blank
        # footprint field (the converter leaves it blank by design so the
        # backend surfaces it loudly instead of guessing).
        self.overrides = load_part_overrides(str(parts_dir)) if parts_dir else {}
        self.used_libs = set()

    def fpid_for(self, ref, fpid, value):
        if fpid:
            return fpid
        for key in (value, ref):
            if key and key in self.overrides:
                return self.overrides[key]
        die(f"{ref} has no footprint FPID in the netlist and no 02_parts "
            f"override (value={value!r}). Fix the schematic footprint map or "
            f"add 02_parts/<part>/part.yaml with a `footprint:` line.")

    def candidates(self, lib, name):
        for rootlib, path in self.roots:
            if rootlib is None:
                yield path / f"{lib}.pretty"
            elif rootlib == lib:
                yield path

    def load(self, ref, fpid, value=""):
        fpid = self.fpid_for(ref, fpid, value)
        if ":" not in fpid:
            die(f"{ref}: malformed FPID {fpid!r} (want 'lib:footprint')")
        lib, name = fpid.split(":", 1)
        tried = []
        for cand in self.candidates(lib, name):
            tried.append(str(cand))
            if not cand.is_dir():
                continue
            fp = pcbnew.FootprintLoad(str(cand), name)
            if fp is not None:
                fp.SetFPID(pcbnew.LIB_ID(lib, name))
                self.used_libs.add(lib)
                return fp
        die(f"{ref}: footprint not found: {fpid}\n  searched: " + "\n            ".join(tried))


# ------------------------------------------------------------- geometry
def rect_of(cfg_board):
    o = cfg_board.get("outline") or {}
    x0 = float(o.get("x0", 0.0))
    y0 = float(o.get("y0", 0.0))
    if "x1" in o and "y1" in o:
        x1, y1 = float(o["x1"]), float(o["y1"])
    elif "w" in o and "h" in o:
        x1, y1 = x0 + float(o["w"]), y0 + float(o["h"])
    else:
        die("board.outline needs x0/y0 plus either x1/y1 or w/h")
    if x1 <= x0 or y1 <= y0:
        die(f"board.outline degenerate: ({x0},{y0})-({x1},{y1})")
    return x0, y0, x1, y1


def box_of(bb, pad=0.0):
    return (MM(bb.GetLeft()) - pad, MM(bb.GetTop()) - pad,
            MM(bb.GetRight()) + pad, MM(bb.GetBottom()) + pad)


def hit(a, b):
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def match_any(ref, patterns):
    return any(fnmatch.fnmatchcase(ref, p) for p in patterns)


# ---------------------------------------------------------------- builder
class BoardBuilder:
    def __init__(self, cfg, base, out_override=None):
        self.cfg = cfg
        self.base = base
        proj = cfg.get("project") or {}
        self.name = proj.get("name") or base.name
        self.netlist = self._p(proj.get("netlist") or die("project.netlist is required"))
        self.out = Path(out_override) if out_override else \
            self._p(proj.get("output") or die("project.output is required"))
        parts_dir = self._p(proj["parts_dir"]) if proj.get("parts_dir") else None
        self.res = FootprintResolver(cfg.get("libraries"), base, parts_dir)
        self.board_cfg = cfg.get("board") or {}
        self.X0, self.Y0, self.X1, self.Y1 = rect_of(self.board_cfg)
        self.RCUT = float(self.board_cfg.get("corner_cut", 0.0) or 0.0)
        self.place_cfg = cfg.get("placement") or {}
        self.silk_cfg = cfg.get("silk") or {}
        self.holes = []
        self.log = []
        self.waived = []

    def _p(self, rel):
        return Path(rel) if os.path.isabs(str(rel)) else (self.base / str(rel))

    # ----------------------------------------------------------- repeats
    def expand_repeats(self):
        """`placement.repeat` -> concrete anchors. THE array primitive: a
        bank of N identical slices at a fixed pitch, each slice contributing
        several refdes families at slice-relative offsets. This is exactly
        the shape of ble-bus-bar's 6 port slices (J/RS/F/RP/RN/CD/U/CB) and
        cook-hub's 16-relay bank, which between them are ~120 hand-written
        ANCHOR lines. `{i}` in a refdes or caption interpolates the index.

        repeat:
          - name: port
            count: 6
            index_from: 1
            origin: [107.0, 0.0]
            pitch:  [19.0, 0.0]
            members:
              "J{i}":  {at: [0.0, 57.0]}
              "U{i}":  {at: [6.0, 63.5], rot: 180}
            captions:
              - {text: "PORT {i}", at: [0.0, 50.0], size: 0.8}
        """
        anchors = self.place_cfg.setdefault("anchors", {})
        captions = self.silk_cfg.setdefault("captions", [])
        n_ref = 0
        for blk in self.place_cfg.get("repeat") or []:
            count = int(blk["count"])
            i0 = int(blk.get("index_from", 1))
            ox, oy = [float(v) for v in blk.get("origin", [0.0, 0.0])]
            px, py = [float(v) for v in blk.get("pitch", [0.0, 0.0])]
            for k in range(count):
                i = i0 + k
                cx, cy = ox + px * k, oy + py * k
                for tmpl, spec in (blk.get("members") or {}).items():
                    ref = tmpl.format(i=i, k=k)
                    if ref in anchors:
                        die(f"repeat {blk.get('name', '?')}: {ref} is already "
                            f"anchored explicitly — remove one of the two")
                    dx, dy = [float(v) for v in spec["at"]]
                    anchors[ref] = [cx + dx, cy + dy, float(spec.get("rot", 0))]
                    n_ref += 1
                for cap in blk.get("captions") or []:
                    captions.append({
                        "text": str(cap["text"]).format(i=i, k=k),
                        "at": [cx + float(cap["at"][0]), cy + float(cap["at"][1])],
                        "size": float(cap.get("size", 0.7)),
                        "nudge": cap.get("nudge", True),
                    })
        if n_ref:
            self.say(f"repeat blocks expanded to {n_ref} anchors")

    def say(self, msg):
        self.log.append(msg)
        print(msg)

    # ------------------------------------------------------------- run
    def build(self):
        comps, pad_net, nets = parse_netlist(self.netlist)
        self.comps, self.pad_net = comps, pad_net
        self.board = pcbnew.BOARD()
        self.board.SetCopperLayerCount(int(self.board_cfg.get("layers", 2)))
        self.netmap = {}
        for n in sorted(nets):
            ni = pcbnew.NETINFO_ITEM(self.board, n)
            self.board.Add(ni)
            self.netmap[n] = ni

        self.expand_repeats()
        self.add_outline()
        self.add_mounting_holes()
        placed = self.place_parts()
        self.check_pads_present()
        self.run_asserts()
        self.legalize()
        self.apply_design_rules()
        self.add_zones()
        self.add_keepouts()
        self.add_silk()
        self.out.parent.mkdir(parents=True, exist_ok=True)
        self.board.Save(str(self.out))
        self.write_waiver()
        self.say(f"saved {self.out.name}: {placed} parts, {len(self.holes)} holes")
        return self.board

    # --------------------------------------------------------- outline
    def _seg(self, xa, ya, xb, yb, w, layer=None):
        s = pcbnew.PCB_SHAPE(self.board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pcbnew.VECTOR2I_MM(xa, ya))
        s.SetEnd(pcbnew.VECTOR2I_MM(xb, yb))
        s.SetLayer(layer if layer is not None else pcbnew.Edge_Cuts)
        s.SetWidth(pcbnew.FromMM(w))
        self.board.Add(s)

    def _arc(self, cx, cy, ax, ay, bx, by, r, w):
        """Concave quarter-arc centred on the rect corner (corner cutouts for
        enclosure screw bosses — Hammond-style lids)."""
        a = pcbnew.PCB_SHAPE(self.board)
        a.SetShape(pcbnew.SHAPE_T_ARC)
        mang = math.atan2((ay + by) / 2 - cy, (ax + bx) / 2 - cx)
        mx, my = cx + r * math.cos(mang), cy + r * math.sin(mang)
        a.SetArcGeometry(pcbnew.VECTOR2I_MM(ax, ay), pcbnew.VECTOR2I_MM(mx, my),
                         pcbnew.VECTOR2I_MM(bx, by))
        a.SetLayer(pcbnew.Edge_Cuts)
        a.SetWidth(pcbnew.FromMM(w))
        self.board.Add(a)

    def add_outline(self):
        w = float(self.board_cfg.get("edge_width", 0.1))
        X0, Y0, X1, Y1, R = self.X0, self.Y0, self.X1, self.Y1, self.RCUT
        if R > 0:
            self._seg(X0 + R, Y0, X1 - R, Y0, w)
            self._seg(X1, Y0 + R, X1, Y1 - R, w)
            self._seg(X0 + R, Y1, X1 - R, Y1, w)
            self._seg(X0, Y0 + R, X0, Y1 - R, w)
            self._arc(X0, Y0, X0 + R, Y0, X0, Y0 + R, R, w)
            self._arc(X1, Y0, X1, Y0 + R, X1 - R, Y0, R, w)
            self._arc(X1, Y1, X1 - R, Y1, X1, Y1 - R, R, w)
            self._arc(X0, Y1, X0, Y1 - R, X0 + R, Y1, R, w)
        else:
            self._seg(X0, Y0, X1, Y0, w)
            self._seg(X1, Y0, X1, Y1, w)
            self._seg(X1, Y1, X0, Y1, w)
            self._seg(X0, Y1, X0, Y0, w)
        # optional rectangular cutouts / isolation slots in the outline
        for cut in self.board_cfg.get("cutouts") or []:
            cx0, cy0, cx1, cy1 = [float(v) for v in cut["rect"]]
            self._seg(cx0, cy0, cx1, cy0, w)
            self._seg(cx1, cy0, cx1, cy1, w)
            self._seg(cx1, cy1, cx0, cy1, w)
            self._seg(cx0, cy1, cx0, cy0, w)

    # -------------------------------------------------- mounting holes
    def add_mounting_holes(self):
        mh = self.board_cfg.get("mounting_holes")
        if not mh:
            return
        fpid = mh.get("footprint", "MountingHole:MountingHole_3.2mm_M3")
        prefix = mh.get("refdes_prefix", "H")
        for i, (hx, hy) in enumerate(mh.get("at") or [], 1):
            ref = f"{prefix}{i}"
            fp = self.res.load(ref, fpid)
            fp.SetReference(ref)
            fp.SetAttributes(fp.GetAttributes()
                             | pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_BOM)
            fp.SetPosition(pcbnew.VECTOR2I_MM(float(hx), float(hy)))
            self.board.Add(fp)
            self.holes.append((float(hx), float(hy)))

    # -------------------------------------------------------- placement
    ATTR_FLAGS = {
        "exclude_from_bom": pcbnew.FP_EXCLUDE_FROM_BOM,
        "board_only": pcbnew.FP_BOARD_ONLY,
        "exclude_from_pos_files": pcbnew.FP_EXCLUDE_FROM_POS_FILES,
        "dnp": getattr(pcbnew, "FP_DNP", 0),
    }

    def patterns_for(self, ref):
        for pat in self.place_cfg.get("patterns") or []:
            if match_any(ref, [pat["match"]] if isinstance(pat.get("match"), str)
                         else pat.get("match", [])):
                yield pat

    def region_center(self, name):
        regions = self.place_cfg.get("regions") or {}
        if name not in regions:
            die(f"placement references unknown region {name!r}")
        rx0, ry0, rx1, ry1 = [float(v) for v in regions[name]]
        return (rx0 + rx1) / 2, (ry0 + ry1) / 2

    def is_pinned(self, ref):
        """Is this anchored part immovable by the legalizer?

        Default: anchored implies pinned (cook-hub's clean rule). But real
        boards need the escape hatch — crow-array-pod and ble-bus-bar both
        anchor every part yet let the passives float, and unifying to the
        clean rule would silently change their output. `placement.pin` is
        an explicit glob allowlist: when present, ONLY matching refs pin.
        """
        pin = self.place_cfg.get("pin")
        if pin is None:
            return True
        return match_any(ref, pin if isinstance(pin, list) else [pin])

    def initial_pose(self, ref):
        """(x, y, rot, pinned). Anchors are pinned (never legalized away);
        seeds and pattern-derived starts are free to move."""
        anchors = self.place_cfg.get("anchors") or {}
        seeds = self.place_cfg.get("seeds") or {}
        if ref in anchors:
            a = list(anchors[ref]) + [0]
            return float(a[0]), float(a[1]), float(a[2]), self.is_pinned(ref)
        if ref in seeds:
            s = list(seeds[ref]) + [0]
            return float(s[0]), float(s[1]), float(s[2]), False
        for pat in self.patterns_for(ref):
            if "near" in pat:
                # "decouplers snap within Nmm of their IC": start ON the
                # target; the legalizer then walks outward to the nearest
                # legal spot, which is exactly the desired semantics.
                tgt = pat["near"]
                if tgt in (self.place_cfg.get("anchors") or {}):
                    ax, ay = anchors[tgt][0], anchors[tgt][1]
                    return float(ax), float(ay), 0.0, False
            if "region" in pat:
                cx, cy = self.region_center(pat["region"])
                return cx, cy, 0.0, False
        if self.place_cfg.get("require_anchor", False):
            die(f"{ref} has no floorplan anchor, seed, or matching pattern "
                f"(placement.require_anchor is on)")
        # last resort: board centre, and let the legalizer sort it out
        return (self.X0 + self.X1) / 2, (self.Y0 + self.Y1) / 2, 0.0, False

    def place_parts(self):
        self.pinned = set()
        placed = 0
        for ref, (fpid, val) in sorted(self.comps.items()):
            fp = self.res.load(ref, fpid, val)
            fp.SetReference(ref)
            fp.SetValue(val)
            x, y, rot, pin = self.initial_pose(ref)
            fp.SetPosition(pcbnew.VECTOR2I_MM(x, y))
            if rot:
                fp.SetOrientationDegrees(rot)
            if pin:
                self.pinned.add(ref)
            for pat in self.patterns_for(ref):
                for a in pat.get("attrs") or []:
                    if a not in self.ATTR_FLAGS:
                        die(f"unknown attr {a!r} in placement pattern {pat['match']!r}")
                    fp.SetAttributes(fp.GetAttributes() | self.ATTR_FLAGS[a])
                for a in pat.get("clear_attrs") or []:
                    if a not in self.ATTR_FLAGS:
                        die(f"unknown clear_attr {a!r}")
                    fp.SetAttributes(fp.GetAttributes() & ~self.ATTR_FLAGS[a])
            for pad in fp.Pads():
                key = (ref, pad.GetNumber())
                if key in self.pad_net:
                    pad.SetNet(self.netmap[self.pad_net[key]])
                # pad-level overrides: e.g. a dense connector's GND tails
                # need SOLID zone connection or the plane's thermal spokes
                # starve (crow-array-pod J1, cook-hub relay bank).
                for pat in self.patterns_for(ref):
                    for ov in pat.get("pad_overrides") or []:
                        pads = ov.get("pads")
                        onnet = ov.get("on_net")
                        if pads and pad.GetNumber() not in [str(v) for v in pads]:
                            continue
                        if onnet and self.pad_net.get(key) != onnet:
                            continue
                        if ov.get("zone_connection") == "full":
                            pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
                        elif ov.get("zone_connection") == "thermal":
                            pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_THERMAL)
                        if "clearance" in ov:
                            pad.SetLocalClearance(pcbnew.FromMM(float(ov["clearance"])))
            self.board.Add(fp)
            placed += 1
        self.fps = {f.GetReference(): f for f in self.board.GetFootprints()}
        self.say(f"placed {placed} footprints ({len(self.pinned)} anchored)")
        return placed

    def check_pads_present(self):
        board_pads = {(f.GetReference(), p.GetNumber())
                      for f in self.board.GetFootprints() for p in f.Pads()}
        missing = sorted(k for k in self.pad_net if k not in board_pads)
        if missing:
            die(f"netlist pads with no board pad ({len(missing)}): {missing[:20]}"
                + (" ..." if len(missing) > 20 else ""))

    # ---------------------------------------------------------- asserts
    def padnet(self, ref, num):
        f = self.fps.get(ref) or die(f"assert references unknown refdes {ref}")
        for p in f.Pads():
            if p.GetNumber() == str(num):
                return p.GetNetname()
        die(f"assert references unknown pad {ref}.{num}")

    def run_asserts(self):
        a = self.cfg.get("asserts") or {}
        n = 0
        for e in a.get("pad_net") or []:
            got = self.padnet(e["ref"], e["pad"])
            if got != e["net"]:
                die(f"POLARITY/ROLE ASSERT: {e['ref']} pad {e['pad']} is on "
                    f"{got!r}, expected {e['net']!r}")
            n += 1
        for e in a.get("pad_order") or []:
            ref, pads, axis = e["ref"], [str(p) for p in e["pads"]], e.get("axis", "x")
            f = self.fps.get(ref) or die(f"pad_order: unknown refdes {ref}")
            pos = {p.GetNumber(): p.GetPosition() for p in f.Pads()}
            vals = []
            for p in pads:
                if p not in pos:
                    die(f"pad_order: {ref} has no pad {p}")
                vals.append(pos[p].x if axis == "x" else pos[p].y)
            if not all(vals[i] < vals[i + 1] for i in range(len(vals) - 1)):
                die(f"ORIENTATION ASSERT: {ref} pads {pads} not ascending in "
                    f"{axis} (part is rotated wrong)")
            n += 1
        if n:
            self.say(f"asserts: {n} passed")

    # -------------------------------------------------------- legalize
    def bbox(self, f):
        return box_of(f.GetBoundingBox(False, False))

    def clear_at(self, f, x, y, skip, lg):
        old = f.GetPosition()
        f.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        l, t, r_, b = self.bbox(f)
        f.SetPosition(old)
        w2, h2 = (r_ - l) / 2, (b - t) / 2
        em = float(lg.get("edge_margin", 0.8))
        if not (self.X0 + em + w2 < x < self.X1 - em - w2
                and self.Y0 + em + h2 < y < self.Y1 - em - h2):
            return False
        if self.RCUT > 0:
            for cx, cy in [(self.X0, self.Y0), (self.X1, self.Y0),
                           (self.X0, self.Y1), (self.X1, self.Y1)]:
                nx, ny = max(abs(x - cx) - w2, 0), max(abs(y - cy) - h2, 0)
                if math.hypot(nx, ny) < self.RCUT + 0.3:
                    return False
        hk = float(lg.get("hole_keepout", 2.4))
        for hx, hy in self.holes:
            if max(abs(x - hx) - w2, abs(y - hy) - h2, 0) < hk:
                return False
        # placement_forbid: PYTHON-SIDE rects the legalizer must not park a
        # part in (antenna clearings, connector plug volumes, router
        # corridors). Deliberately distinct from `keepouts`, which are board
        # rule-area objects — these never become board geometry.
        for fr in self.place_cfg.get("forbid") or []:
            fx0, fy0, fx1, fy1 = [float(v) for v in fr["rect"]]
            m = float(fr.get("margin", 0.3))
            if not (x + w2 + m <= fx0 or fx1 <= x - w2 - m
                    or y + h2 + m <= fy0 or fy1 <= y - h2 - m):
                return False
        clr = float(lg.get("clearance", 0.25))
        for r2, f2 in self.fps.items():
            if r2 == skip or r2 in self.hole_refs:
                continue
            L, T, R_, B = self.bbox(f2)
            if not (x + w2 + clr <= L or R_ <= x - w2 - clr
                    or y + h2 + clr <= T or B <= y - h2 - clr):
                return False
        return True

    def legalize(self):
        lg = self.place_cfg.get("legalize") or {}
        self.hole_refs = {f.GetReference() for f in self.board.GetFootprints()
                          if f.GetAttributes() & pcbnew.FP_BOARD_ONLY}
        if not lg.get("enable", True):
            return
        keep = set(self.pinned)
        for pat in self.place_cfg.get("keep") or []:
            keep |= {r for r in self.fps if fnmatch.fnmatchcase(r, pat)}
        ring_max = int(lg.get("ring_max", 40))
        moved = 0
        for r in sorted(self.fps):
            f = self.fps[r]
            if r in keep or r in self.hole_refs:
                continue
            ox, oy = MM(f.GetPosition().x), MM(f.GetPosition().y)
            if self.clear_at(f, ox, oy, r, lg):
                continue
            done = False
            for ring in [0.5 * k for k in range(1, ring_max)]:
                for ang in range(0, 360, 20):
                    nx = round(ox + ring * math.cos(math.radians(ang)), 1)
                    ny = round(oy + ring * math.sin(math.radians(ang)), 1)
                    if self.clear_at(f, nx, ny, r, lg):
                        f.SetPosition(pcbnew.VECTOR2I_MM(nx, ny))
                        moved += 1
                        done = True
                        break
                if done:
                    break
            if not done:
                die(f"legalizer: no clear spot for {r} within "
                    f"{0.5 * ring_max:.1f}mm of its seed — the floorplan is "
                    f"over-subscribed; add an anchor or grow the board")
        self.say(f"legalized {moved} floating parts")

    # ---------------------------------------------------- design rules
    DS_KEYS = {
        "track_min_width": "m_TrackMinWidth", "min_clearance": "m_MinClearance",
        "via_min_annulus": "m_ViasMinAnnularWidth", "hole_clearance": "m_HoleClearance",
        "hole_to_hole": "m_HoleToHoleMin", "copper_edge_clearance": "m_CopperEdgeClearance",
        "via_min_size": "m_ViasMinSize", "min_through_drill": "m_MinThroughDrill",
        "solder_mask_min_width": "m_SolderMaskMinWidth",
        "solder_mask_expansion": "m_SolderMaskExpansion",
    }
    DS_DEFAULTS = {
        "track_min_width": 0.127, "min_clearance": 0.127, "via_min_annulus": 0.05,
        "hole_clearance": 0.25, "hole_to_hole": 0.5, "copper_edge_clearance": 0.2,
        "via_min_size": 0.45, "min_through_drill": 0.3,
    }

    def apply_design_rules(self):
        ds = self.board.GetDesignSettings()
        vals = dict(self.DS_DEFAULTS)
        vals.update(self.cfg.get("design_rules") or {})
        for k, v in vals.items():
            if k not in self.DS_KEYS:
                die(f"unknown design_rules key {k!r} (known: {sorted(self.DS_KEYS)})")
            setattr(ds, self.DS_KEYS[k], pcbnew.FromMM(float(v)))
        ds.m_MinConn = int((self.cfg.get("design_rules") or {}).get("min_conn", 0))

    # ------------------------------------------------------------ zones
    LAYER_NAMES = {"F.Cu": pcbnew.F_Cu, "B.Cu": pcbnew.B_Cu,
                   "In1.Cu": pcbnew.In1_Cu, "In2.Cu": pcbnew.In2_Cu}

    def zone_points(self, z):
        if "points" in z:
            return [(float(a), float(b)) for a, b in z["points"]]
        if "region" in z:
            regions = self.place_cfg.get("regions") or {}
            if z["region"] not in regions:
                die(f"zone references unknown region {z['region']!r}")
            rx0, ry0, rx1, ry1 = [float(v) for v in regions[z["region"]]]
            return [(rx0, ry0), (rx1, ry0), (rx1, ry1), (rx0, ry1)]
        if "rect" in z:
            rx0, ry0, rx1, ry1 = [float(v) for v in z["rect"]]
            return [(rx0, ry0), (rx1, ry0), (rx1, ry1), (rx0, ry1)]
        return [(self.X0, self.Y0), (self.X1, self.Y0),
                (self.X1, self.Y1), (self.X0, self.Y1)]

    def add_zones(self):
        for z in self.cfg.get("zones") or []:
            net = z.get("net")
            if net and net not in self.netmap:
                die(f"zone on unknown net {net!r} (netlist has no such net)")
            pts = self.zone_points(z)
            for lname in z.get("layers") or ["F.Cu", "B.Cu"]:
                if lname not in self.LAYER_NAMES:
                    die(f"zone on unknown layer {lname!r}")
                zone = pcbnew.ZONE(self.board)
                zone.SetLayer(self.LAYER_NAMES[lname])
                if net:
                    zone.SetNet(self.netmap[net])
                zone.SetAssignedPriority(int(z.get("priority", 0)))
                zone.SetMinThickness(pcbnew.FromMM(float(z.get("min_thickness", 0.25))))
                zone.SetLocalClearance(pcbnew.FromMM(float(z.get("clearance", 0.25))))
                zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL
                                      if z.get("connect") == "full"
                                      else pcbnew.ZONE_CONNECTION_THERMAL)
                if z.get("island_removal", True):
                    zone.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
                zone.Outline().NewOutline()
                for x, y in pts:
                    zone.Outline().Append(pcbnew.VECTOR2I_MM(x, y))
                self.board.Add(zone)

    def add_keepouts(self):
        """Rule areas: antenna keepouts, isolation slots, AND named-but-
        permissive DRU anchors.

        Two distinct uses, both real:
          * `deny: [tracks, vias, pours]` — a true keepout (an antenna
            clearing that must stay bare copper-free).
          * `deny: []` with a `name` — a PERMISSIVE area that forbids
            nothing and exists only so `generate_rules.py` can write a
            `.kicad_dru` rule scoped to `insideArea('<name>')`. cook-hub's
            `u7_taps` and usb-power-3s's `SW_TAP_A/B` are exactly this; an
            implementation that always denies would silently break them.
        One ZONE spans all its layers via an LSET (not one zone per layer):
        that is how KiCad models a multi-layer rule area.
        """
        for k in self.cfg.get("keepouts") or []:
            pts = self.zone_points(k)
            deny = set(k.get("deny", ["tracks", "vias", "pours"]) or [])
            unknown = deny - {"tracks", "vias", "pours", "pads", "footprints"}
            if unknown:
                die(f"keepout {k.get('name', '?')}: unknown deny item(s) {sorted(unknown)}")
            z = pcbnew.ZONE(self.board)
            z.SetIsRuleArea(True)
            if k.get("name"):
                z.SetZoneName(str(k["name"]))
            layers = k.get("layers") or ["F.Cu", "B.Cu"]
            ls = pcbnew.LSET()
            for lname in layers:
                if lname not in self.LAYER_NAMES:
                    die(f"keepout on unknown layer {lname!r}")
                # KiCad's SWIG binding spells this AddLayer on some builds and
                # addLayer on others; both appear across our own generators.
                add = getattr(ls, "AddLayer", None) or getattr(ls, "addLayer")
                add(self.LAYER_NAMES[lname])
            z.SetLayerSet(ls)
            z.SetLayer(self.LAYER_NAMES[layers[0]])
            z.SetDoNotAllowTracks("tracks" in deny)
            z.SetDoNotAllowVias("vias" in deny)
            z.SetDoNotAllowPads("pads" in deny)
            for setter in ("SetDoNotAllowZoneFills", "SetDoNotAllowCopperPour"):
                if hasattr(z, setter):
                    getattr(z, setter)("pours" in deny)
                    break
            if hasattr(z, "SetDoNotAllowFootprints"):
                z.SetDoNotAllowFootprints("footprints" in deny)
            z.Outline().NewOutline()
            for x, y in pts:
                z.Outline().Append(pcbnew.VECTOR2I_MM(x, y))
            self.board.Add(z)

    # ------------------------------------------------------ fp-lib-table
    def write_fp_lib_table(self):
        """Emit 04_kicad/fp-lib-table covering exactly the libraries the
        netlist actually used. Only usb-power-3s did this; every board wants
        it, because without it KiCad opens the board with broken library
        links even though the footprints are embedded."""
        if not self.cfg.get("project", {}).get("fp_lib_table"):
            return
        path = self._p(self.cfg["project"]["fp_lib_table"])
        rows = []
        for lib in sorted(self.res.used_libs):
            uri = None
            for rootlib, root in self.res.roots:
                if rootlib == lib:
                    uri = str(root)
                elif rootlib is None and (root / f"{lib}.pretty").is_dir():
                    uri = str(root / f"{lib}.pretty")
                if uri:
                    break
            if uri and uri.startswith(STD_FP_ROOT):
                uri = uri.replace(STD_FP_ROOT, "${KICAD9_FOOTPRINT_DIR}")
            rows.append(f'  (lib (name "{lib}")(type "KiCad")(uri "{uri}")'
                        f'(options "")(descr ""))')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("(fp_lib_table\n  (version 7)\n" + "\n".join(rows) + "\n)\n")
        self.say(f"wrote {path.name}: {len(rows)} libraries")

    # ------------------------------------------------------------- silk
    def _obstacles(self, ref_clear, include_bodies=True):
        pad_obst, silk_obst = [], []
        for fp in self.board.GetFootprints():
            for p in fp.Pads():
                pad_obst.append(box_of(p.GetBoundingBox(), ref_clear))
            for g in fp.GraphicalItems():
                if g.IsOnLayer(pcbnew.F_SilkS):
                    silk_obst.append(box_of(g.GetBoundingBox(), ref_clear * 0.5))
            # the part BODY is an obstacle too: silk under a body is invisible
            # on the assembled board (a U1 refdes once shipped under a SOIC).
            if include_bodies and fp.GetReference() not in self.hole_refs:
                pad_obst.append(box_of(fp.GetBoundingBox(False, False), 0.05))
        return pad_obst, silk_obst

    def _in_frame(self, cand, m=0.2):
        return (self.X0 + m < cand[0] and cand[2] < self.X1 - m
                and self.Y0 + m < cand[1] and cand[3] < self.Y1 - m)

    NUDGE = [(0, 0)] + \
        [(o * s, 0) for o in (0.8, 1.5, 2.3, 3.2, 4.2) for s in (-1, 1)] + \
        [(0, o * s) for o in (0.8, 1.5, 2.3, 3.2, 4.2) for s in (-1, 1)] + \
        [(dx, dy) for d in (1.5, 2.6, 3.8) for dx in (-d, d) for dy in (-d, d)]

    OFF = [(0, o * s) for o in (1.0, 1.6, 2.2, 2.9, 3.6, 4.4, 5.2, 6.0) for s in (-1, 1)] + \
          [(o * s, 0) for o in (1.3, 2.0, 2.8, 3.6, 4.5, 5.4, 6.2) for s in (-1, 1)] + \
          [(dx, dy) for d in (1.4, 2.2, 3.0, 4.0, 5.0) for dx in (-d, d) for dy in (-d, d)] + \
          [(0, o * s) for o in (7.0, 8.0, 9.0, 10.0, 11.0) for s in (-1, 1)] + \
          [(o * s, 0) for o in (7.2, 8.2, 9.2, 10.2) for s in (-1, 1)] + \
          [(dx, dy) for d in (6.0, 7.0, 8.0, 9.0) for dx in (-d, d) for dy in (-d, d)]

    def _mktext(self, txt, size, layer=None):
        t = pcbnew.PCB_TEXT(self.board)
        t.SetText(txt)
        t.SetLayer(layer if layer is not None else pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I_MM(size, size))
        t.SetTextThickness(pcbnew.FromMM(max(0.13, size * 0.16)))
        return t

    def add_silk(self):
        rc = self.silk_cfg.get("refdes") or {}
        clr = float(rc.get("clearance", 0.16))
        min_h = float(self.silk_cfg.get("min_text_height", 0.6))
        pad_obst, silk_obst = self._obstacles(clr)

        # ---- fixed functional captions, collision-nudged
        cap_nudge = bool(self.silk_cfg.get("caption_nudge", True))
        crowded = 0
        for cap in self.silk_cfg.get("captions") or []:
            if isinstance(cap, dict):
                txt = cap["text"]
                x, y = float(cap["at"][0]), float(cap["at"][1])
                size = float(cap.get("size", 0.7))
                nudge = self.NUDGE if cap.get("nudge", cap_nudge) else [(0, 0)]
                rot = float(cap.get("rot", 0))
            else:
                txt, x, y = cap[0], float(cap[1]), float(cap[2])
                size = float(cap[3]) if len(cap) > 3 else 0.7
                nudge = self.NUDGE if cap_nudge else [(0, 0)]
                rot = 0.0
            size = max(size, min_h)
            t = self._mktext(txt, size)
            if rot:
                t.SetTextAngleDegrees(rot)
            ok = False
            for dx, dy in nudge:
                t.SetPosition(pcbnew.VECTOR2I_MM(x + dx, y + dy))
                cand = box_of(t.GetBoundingBox())
                if not self._in_frame(cand, 0.4):
                    continue
                if any(hit(cand, o) for o in pad_obst) or any(hit(cand, o) for o in silk_obst):
                    continue
                ok = True
                break
            self.board.Add(t)          # keep even if crowded (best offset wins)
            if not ok:
                crowded += 1
                print(f"WARN silk caption crowded: {txt[:40]}")
            silk_obst.append(box_of(t.GetBoundingBox(), clr * 0.5))

        # ---- functional captions derived from part values (J*/F*/TP*)
        label_rules = self.silk_cfg.get("labels") or []
        derived = []
        for rule in label_rules:
            pats = [rule["match"]] if isinstance(rule.get("match"), str) else rule.get("match", [])
            src = rule.get("from", "value")
            strip = rule.get("strip", "")
            for ref, f in sorted(self.fps.items()):
                if not match_any(ref, pats):
                    continue
                if src == "value":
                    txt = f.GetValue()
                elif src == "refdes":
                    txt = ref
                else:
                    die(f"silk.labels: unknown source {src!r}")
                if strip:
                    txt = txt.replace(strip, "")
                txt = txt.strip()
                if txt:
                    derived.append((ref, txt, float(rule.get("size", 0.6))))

        # refresh obstacles now that captions are down
        pad_obst, silk_obst2 = self._obstacles(clr)
        silk_obst = silk_obst2 + silk_obst
        for t in self.board.GetDrawings():
            if t.GetClass() == "PCB_TEXT" and t.IsOnLayer(pcbnew.F_SilkS):
                silk_obst.append(box_of(t.GetBoundingBox(), clr * 0.5))

        nlab = 0
        for ref, txt, size in derived:
            f = self.fps[ref]
            t = self._mktext(txt, max(size, min_h))
            fx, fy = MM(f.GetPosition().x), MM(f.GetPosition().y)
            for dx, dy in self.OFF:
                t.SetPosition(pcbnew.VECTOR2I_MM(fx + dx, fy + dy))
                cand = box_of(t.GetBoundingBox())
                if not self._in_frame(cand):
                    continue
                if any(hit(cand, o) for o in pad_obst) or any(hit(cand, o) for o in silk_obst):
                    continue
                silk_obst.append(cand)
                self.board.Add(t)
                nlab += 1
                break

        # ---- polarity marks ("K" beside pad 1 of a diode, etc.)
        for mark in self.silk_cfg.get("polarity_marks") or []:
            ref, pad, glyph = mark["ref"], str(mark.get("pad", 1)), mark.get("text", "K")
            f = self.fps.get(ref) or die(f"polarity_mark: unknown refdes {ref}")
            p1 = next((p for p in f.Pads() if p.GetNumber() == pad), None)
            if p1 is None:
                die(f"polarity_mark: {ref} has no pad {pad}")
            px, py = MM(p1.GetPosition().x), MM(p1.GetPosition().y)
            for dx, dy in self.OFF:
                kt = self._mktext(glyph, 0.6)
                kt.SetPosition(pcbnew.VECTOR2I_MM(px + dx, py + dy))
                cand = box_of(kt.GetBoundingBox())
                if self._in_frame(cand) and not any(hit(cand, o) for o in pad_obst) \
                        and not any(hit(cand, o) for o in silk_obst):
                    self.board.Add(kt)
                    silk_obst.append(cand)
                    break
            else:
                die(f"no clear spot for the {ref} polarity mark {glyph!r}")

        # ---- refdes: F.SilkS de-collided + ALWAYS an F.Fab copy
        size = float(rc.get("size", 0.6))
        small = float(rc.get("min_size", 0.45))
        fab_copy = bool(rc.get("fab_copy", True))
        prio_first = rc.get("priority_prefixes", "UJDBQ")

        def prio(fp):
            r = fp.GetReference()
            return (0 if r[0] in prio_first or r.startswith("TP") else 1, r)

        for fp in sorted(self.board.GetFootprints(), key=prio):
            r = fp.GetReference()
            ref = fp.Reference()
            if fab_copy:
                fab = self._mktext(r, float(rc.get("fab_size", 0.5)), pcbnew.F_Fab)
                fab.SetTextThickness(int(0.08e6))
                fab.SetPosition(fp.GetPosition())
                self.board.Add(fab)
            if r in self.hole_refs:
                ref.SetVisible(False)
                continue
            ref.SetLayer(pcbnew.F_SilkS)
            ref.SetVisible(True)
            fx, fy = MM(fp.GetPosition().x), MM(fp.GetPosition().y)
            ok = False
            for rot in (0, 90):                       # stand up in narrow gaps
                ref.SetTextAngleDegrees(rot)
                for sz in (size, small):
                    ref.SetTextSize(pcbnew.VECTOR2I_MM(sz, sz))
                    ref.SetTextThickness(int(max(0.09, sz * 0.2) * 1e6))
                    for dx, dy in self.OFF:
                        ref.SetPosition(pcbnew.VECTOR2I_MM(fx + dx, fy + dy))
                        cand = box_of(ref.GetBoundingBox())
                        if not self._in_frame(cand):
                            continue
                        if any(hit(cand, o) for o in pad_obst) \
                                or any(hit(cand, o) for o in silk_obst):
                            continue
                        silk_obst.append(cand)
                        ok = True
                        break
                    if ok:
                        break
                if ok:
                    break
            if not ok:
                ref.SetTextAngleDegrees(0)
                ref.SetVisible(False)
                self.waived.append(r)
        n = len(self.fps) - len(self.hole_refs)
        self.say(f"refdes on silk: {n - len(self.waived)}/{n} placed, "
                 f"{len(self.waived)} waived to F.Fab: {sorted(self.waived)}; "
                 f"{nlab} functional labels, {crowded} crowded captions")

    def write_waiver(self):
        wp = self.cfg.get("project", {}).get("waiver")
        path = self._p(wp) if wp else self.out.parent / "refdes_waiver.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(sorted(self.waived)))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("config", help="floorplan YAML")
    ap.add_argument("-o", "--output", help="override project.output")
    ap.add_argument("--netlist", help="override project.netlist")
    args = ap.parse_args(argv)

    cfgp = Path(args.config).resolve()
    cfg = yaml.safe_load(cfgp.read_text())
    if not isinstance(cfg, dict):
        die(f"{cfgp} is not a YAML mapping")
    # paths in the config are relative to the PROJECT ROOT (the config's
    # parent's parent when it lives in 03_src/, else the config's dir)
    base = cfgp.parent.parent if cfgp.parent.name.startswith("03_") else cfgp.parent
    if cfg.get("project", {}).get("root"):
        base = (cfgp.parent / cfg["project"]["root"]).resolve()
    if args.netlist:
        cfg.setdefault("project", {})["netlist"] = args.netlist
    BoardBuilder(cfg, base, args.output).build()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except FloorplanError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
