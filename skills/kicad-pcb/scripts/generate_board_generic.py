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

CONFIG SCHEMA — see `references/floorplan-schema.md`; a skill-owned example
is `../pcb-design/templates/03_src/floorplan.yaml` (project-independent — do
NOT read another project's config). Top-level keys:

  project:    name, netlist, output, parts_dir
  board:      outline (x0/y0/x1/y1 or x0/y0/w/h), corner_cut, edge_width,
              layers, optional stackup {nominal_thickness_mm,
                copper_finish, dielectric_constraints, mask_thickness_mm,
                copper_thickness_mm[], dielectrics[]},
              optional via_protection {capping, filling}; each boolean emits
                the matching BOARD-DEFAULT KiCad setup token after the final
                pcbnew save (prefer item-level thermal_vias.protection for
                selective filled/capped via-in-pad orders),
              mounting_holes {footprint, refdes_prefix, at[]},
              fiducials {footprint, refdes_prefix, at[]} — board-only
                optical alignment targets; BOM- and CPL-excluded
  libraries:  list of ".pretty" search roots; a bare dir is treated as a
              KiCad-style root holding "<lib>.pretty", a {lib,path} entry
              binds one library name to one explicit .pretty dir
  placement:  anchors {REF: [x,y,rot]}, post_anchors {REF: [x,y,rot]},
              seeds {REF: [x,y]}, regions,
              patterns[] (glob -> region/near/attrs/model_override/
                pad_overrides),
              repeat[] (array primitive; caption-only blocks allowed),
              bbox_override {REF: [x0,y0,x1,y1]} for modules whose footprint
                bbox includes an off-board antenna keepout (pinned refs only),
              legalize {enable, clearance, edge_margin, hole_keepout, ring_max}
  design_rules: pcbnew design-settings floors (mm)
  zones:      list of {net, layers, priority, outline|region|board,
                       connect: thermal|full, min_thickness, clearance}
              Inner layers (In1.Cu/In2.Cu) require board.layers >= 3/4.
  keepouts:   list of {region|points, layers, name, deny[]} — rule areas.
              ONE zone spans all its layers via an LSET.
  silk:       captions[], refdes {size, min_size, fab_copy, clearance},
              labels {match, from: value|net} for functional captions
  asserts:    pad_net[] {ref, pad, net}, pad_order[] {ref, pads, axis},
              body_offset[] {ref, axis, sign} — which way a connector mouth
                faces (catches a 180 flip pad_order cannot see),
              pad_beyond_edge[] {ref, pad, offset, edge} — an edge-launch
                clearing must hang OFF the board
  thermal_vias: fields[] and/or promote_heatsink_pads[], plus optional
                protection {capping, filling} applied to only those vias;
                a field-level protection mapping overrides the shared value

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
import zlib
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
from pcb_toolkit import apply_via_protection

MM = pcbnew.ToMM
STD_FP_ROOT = "/usr/share/kicad/footprints"

# ------------------------------------------------- THE silk stroke formula
# THE ONLY PLACE the emitted-stroke arithmetic lives. G-SELFCON
# (gate_contract_audit.py) does not copy these numbers or re-implement the
# formula: it lifts `silk_stroke` and these constants out of THIS file's AST
# and calls them. A checker carrying its own copy of the formula it grades is
# canon M1 failing in the other direction — it agrees with a stale copy, which
# is exactly how the "0.60mm reaches a 0.15 stroke" corollary survived being
# written down (it is 0.9375mm; see fab_tiers.yaml).
KICAD_STROKE_OVER_HEIGHT = 0.25   # KiCad's own clamp: stroke <= 0.25 x height
SILK_STROKE_MIN = 0.13            # hard floor for board-level silk text
SILK_STROKE_OVER_SIZE = 0.16      # ... and its stroke:height ratio
REFDES_STROKE_MIN = 0.09          # the refdes de-collision path has its own
REFDES_STROKE_OVER_SIZE = 0.20    # ... pair, and they differ. Both are graded.


def silk_stroke(size, floor, ratio=SILK_STROKE_OVER_SIZE,
                hard=SILK_STROKE_MIN):
    """The stroke (mm) this generator emits for silk text of height `size` on
    a tier whose published stroke floor is `floor`.

    TWO bounds, and the pair is the whole point: a LOWER floor
    (max(floor, hard, ratio x size)) and KiCad's UPPER clamp
    (KICAD_STROKE_OVER_HEIGHT x size). Before 2026-07-29 the lower floor was
    applied without the clamp, so 0.45mm text was stored with a 0.13mm stroke
    that KiCad can only plot at 0.1125 — a value no tier could publish
    truthfully in either direction. The clamp is a no-op at size >= 0.52mm,
    which is every height any shipped board uses."""
    return min(size * KICAD_STROKE_OVER_HEIGHT,
               max(float(floor or 0.0), hard, size * ratio))


def _kicad_fp_env():
    """The running KiCad's versioned footprint-dir env var (KiCad renames it
    every major: KICAD9_FOOTPRINT_DIR, KICAD10_FOOTPRINT_DIR, ...)."""
    m = re.match(r"(\d+)", getattr(pcbnew, "Version", lambda: "")() or "")
    return "${KICAD%s_FOOTPRINT_DIR}" % (m.group(1) if m else "9")


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
    s = path.read_text(encoding="utf-8-sig")
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


def _validate_simple_polygon(points, what):
    """Refuse degenerate or self-intersecting authored polygons.

    KiCad accepts a crossed/overlapping ZONE outline and can then fill only a
    seemingly unrelated tail of it.  That failure is especially expensive:
    placement and routing remain legal, while the first authoritative refill
    reports an entire power cell disconnected.  Validate the inexpensive
    source geometry before a board object is emitted.
    """
    eps = 1e-9
    if len(points) < 3:
        die(f"{what}: polygon needs at least 3 vertices, got {len(points)}")
    if points[0] == points[-1]:
        die(f"{what}: repeat of the first vertex at the end is not allowed "
            "(the generator closes polygons itself)")
    for i, (a, b) in enumerate(zip(points, points[1:] + points[:1])):
        if abs(a[0] - b[0]) <= eps and abs(a[1] - b[1]) <= eps:
            die(f"{what}: zero-length edge at vertex {i}: {a}")
    area2 = sum(a[0] * b[1] - b[0] * a[1]
                for a, b in zip(points, points[1:] + points[:1]))
    if abs(area2) <= eps:
        die(f"{what}: polygon has zero signed area")

    def orient(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) \
            - (b[1] - a[1]) * (c[0] - a[0])

    def on_segment(a, b, p):
        return (min(a[0], b[0]) - eps <= p[0] <= max(a[0], b[0]) + eps
                and min(a[1], b[1]) - eps <= p[1] <= max(a[1], b[1]) + eps
                and abs(orient(a, b, p)) <= eps)

    def intersects(a, b, c, d):
        o1, o2, o3, o4 = (orient(a, b, c), orient(a, b, d),
                          orient(c, d, a), orient(c, d, b))
        if ((o1 > eps and o2 < -eps) or (o1 < -eps and o2 > eps)) and \
                ((o3 > eps and o4 < -eps) or (o3 < -eps and o4 > eps)):
            return True
        return ((abs(o1) <= eps and on_segment(a, b, c))
                or (abs(o2) <= eps and on_segment(a, b, d))
                or (abs(o3) <= eps and on_segment(c, d, a))
                or (abs(o4) <= eps and on_segment(c, d, b)))

    n = len(points)
    edges = list(zip(points, points[1:] + points[:1]))
    for i, (a, b) in enumerate(edges):
        for j in range(i + 1, n):
            # Adjacent edges share exactly their authored vertex; that is the
            # only legal intersection.  First/last are adjacent as well.
            if j == i + 1 or (i == 0 and j == n - 1):
                continue
            c, d = edges[j]
            if intersects(a, b, c, d):
                die(f"{what}: self-intersection/overlap between edges "
                    f"{i} {a}->{b} and {j} {c}->{d}")


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
        # capability-derived silk floor from the project's declared fab tier
        # (None when no tier / no nets.yaml — legacy defaults apply verbatim)
        from fab_tier_util import FabTierError, resolve as resolve_tier
        try:
            self.tier = resolve_tier(base)
        except FabTierError as e:
            die(str(e))
        self.holes = []
        self.log = []
        self.waived = []

    def silk_floors(self):
        """(min height, min stroke) from the declared tier — (0, 0) when no
        tier, so every comparison below degrades to a no-op for legacy
        boards."""
        if not self.tier:
            return 0.0, 0.0
        return (float(self.tier.get("min_silk_text_height", 0) or 0),
                float(self.tier.get("min_silk_stroke", 0) or 0))

    def silk_h(self, value, default, what):
        """A silkscreen text height: the config's explicit value, or
        `default` floored at the tier's min_silk_text_height. An EXPLICIT
        height below the tier floor is an ERROR naming the tier (the
        clean-room 3S run hand-carried its silk floor because nothing here
        read the declared tier) — never a silent lift. F.Fab text is exempt
        (it is fab documentation, not silkscreen print)."""
        floor = float(self.tier.get("min_silk_text_height", 0)) if self.tier else 0.0
        if value is None:
            return max(float(default), floor)
        v = float(value)
        if floor and v < floor - 1e-9:
            die(f"silk {what} {v}mm is below fab tier '{self.tier['name']}' "
                f"min_silk_text_height {floor}mm — illegible at fab; raise "
                f"the height or the tier (D-TIER)")
        return v

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
                    out = {
                        "text": str(cap["text"]).format(i=i, k=k),
                        "at": [cx + float(cap["at"][0]), cy + float(cap["at"][1])],
                        "size": float(cap.get("size", 0.7)),
                    }
                    # only carry `nudge` when the block SAYS so — hardcoding a
                    # default here would override the board's `caption_nudge`
                    # and silently nudge captions on a hand-placed silkscreen.
                    if "nudge" in cap:
                        out["nudge"] = cap["nudge"]
                    captions.append(out)
        if n_ref:
            self.say(f"repeat blocks expanded to {n_ref} anchors")

    def say(self, msg):
        self.log.append(msg)
        print(msg)

    # ------------------------------------------- deterministic identity
    def seed_uuids(self):
        """Make every UUID this run mints a deterministic function of the
        SOURCE, so identical source produces byte-identical boards.

        WHY (2026-07-26, usb-hub-3s-v3 v1.6 M-REPRO). The generator was
        already deterministic in every VALUE (identical footprint hashes
        across isolated runs) but minted FRESH RANDOM UUIDs each run. KiCad
        serialises footprints in UUID order, so the zone filler walked zones
        in a different order per run, Clipper tessellated the pour boundaries
        differently, and island_rescue — keyed off zone islands — inherited
        all of it: three regenerations of identical source gave 292/294/293
        vias. The staged release could not prove M-REPRO.

        HOW. `KIID::SeedGenerator()` is KiCad's own QA hook: it reseeds the
        library's mt19937-backed UUID generator, after which UUIDs are drawn
        from a fixed pseudo-random stream. Object CREATION ORDER is already
        deterministic (that is what the identical value-hashes measured), so
        the stream assigns every object the same UUID on every run. mt19937
        is fully specified by its seed — no PID, no clock, no platform
        dependence — so this holds across machines, and the stream's period
        makes collisions no more likely than random UUIDs (the caller must
        still assert |uuid set| == |objects| on the result; see
        tests/t1_generate_board.py t_uuid_determinism).

        The seed itself is derived from the OUTPUT BOARD NAME, not a
        constant, so two different boards do not share a UUID stream while
        one board's stream never depends on anything but its source.
        """
        seed = zlib.crc32(self.out.stem.encode())
        pcbnew.KIID.SeedGenerator(seed)
        self.say(f"UUID generator seeded: crc32({self.out.stem!r}) = {seed} "
                 f"(M-REPRO: identical source now yields byte-identical "
                 f"output)")

    # ------------------------------------------------------------- run
    def build(self):
        comps, pad_net, nets = parse_netlist(self.netlist)
        self.comps, self.pad_net = comps, pad_net
        self.seed_uuids()
        self.board = pcbnew.BOARD()
        self.board.SetCopperLayerCount(int(self.board_cfg.get("layers", 2)))
        stack = self.board_cfg.get("stackup") or {}
        if stack:
            nominal = float(stack.get("nominal_thickness_mm", 1.6))
            if nominal <= 0:
                die("board.stackup.nominal_thickness_mm must be positive")
            self.board.GetDesignSettings().SetBoardThickness(pcbnew.FromMM(nominal))
        self.netmap = {}
        for n in sorted(nets):
            ni = pcbnew.NETINFO_ITEM(self.board, n)
            self.board.Add(ni)
            self.netmap[n] = ni

        self.expand_repeats()
        self.add_outline()
        self.add_mounting_holes()
        self.add_fiducials()
        placed = self.place_parts()
        self.check_pads_present()
        self.promote_heatsink_pads_to_vias()
        self.run_asserts()
        self.legalize()
        self.apply_post_anchors()
        self.check_placement_collisions()
        self.normalize_footprint_text()
        self.apply_design_rules()
        self.add_zones()
        self.add_keepouts()
        self.add_silk()
        self.out.parent.mkdir(parents=True, exist_ok=True)
        self.board.Save(str(self.out))
        self.write_stackup()
        self.write_via_protection()
        self.write_waiver()
        # emit fp-lib-table when configured (no-op otherwise). Kept OUT of the
        # save path above so a board without the config is unaffected.
        self.write_fp_lib_table()
        self.say(f"saved {self.out.name}: {placed} parts, {len(self.holes)} holes")
        return self.board

    # ---------------------------------------------------------- stackup
    def write_stackup(self):
        """Author a physical KiCad stackup from declarative source.

        KiCad 10's Python binding exposes ``BOARD_STACKUP`` only as an opaque
        SWIG pointer, so there is no supported setter API.  Emitting the native
        s-expression here is still part of the generic generator (and is
        immediately round-tripped through pcbnew below); it is not a project
        post-processing escape hatch.  Boards without ``board.stackup`` remain
        byte-for-byte on the legacy path.
        """
        cfg = self.board_cfg.get("stackup")
        if not cfg:
            return
        if not isinstance(cfg, dict):
            die("board.stackup must be a mapping")

        count = int(self.board_cfg.get("layers", 2))
        copper = cfg.get("copper_thickness_mm")
        dielectrics = cfg.get("dielectrics")
        if not isinstance(copper, list) or len(copper) != count:
            die(f"board.stackup.copper_thickness_mm must contain exactly "
                f"{count} entries")
        if not isinstance(dielectrics, list) or len(dielectrics) != count - 1:
            die(f"board.stackup.dielectrics must contain exactly {count - 1} "
                f"entries")

        def num(value, path, *, allow_zero=False):
            try:
                value = float(value)
            except (TypeError, ValueError):
                die(f"{path} must be numeric")
            if value < 0 or (not allow_zero and value == 0):
                die(f"{path} must be {'non-negative' if allow_zero else 'positive'}")
            return f"{value:.9g}"

        def quoted(value):
            return json.dumps(str(value), ensure_ascii=False)

        copper_values = [float(v) for v in copper]
        if any(v <= 0 for v in copper_values):
            die("board.stackup copper thicknesses must all be positive")
        dielectric_values = []
        for i, item in enumerate(dielectrics, 1):
            if not isinstance(item, dict):
                die(f"board.stackup.dielectrics[{i - 1}] must be a mapping")
            for key in ("type", "thickness_mm", "material", "epsilon_r",
                        "loss_tangent"):
                if key not in item:
                    die(f"board.stackup.dielectrics[{i - 1}] missing {key!r}")
            if item["type"] not in ("prepreg", "core"):
                die(f"board.stackup.dielectrics[{i - 1}].type must be prepreg "
                    f"or core")
            thickness = float(item["thickness_mm"])
            if thickness <= 0:
                die(f"board.stackup.dielectrics[{i - 1}].thickness_mm must be positive")
            dielectric_values.append(thickness)
            num(item["epsilon_r"],
                f"board.stackup.dielectrics[{i - 1}].epsilon_r")
            num(item["loss_tangent"],
                f"board.stackup.dielectrics[{i - 1}].loss_tangent",
                allow_zero=True)

        nominal = float(cfg.get("nominal_thickness_mm", 1.6))
        physical = sum(copper_values) + sum(dielectric_values)
        tolerance = float(cfg.get("thickness_tolerance_mm", 0.10))
        if tolerance < 0 or abs(physical - nominal) > tolerance + 1e-12:
            die(f"board.stackup physical copper+dielectric thickness "
                f"{physical:.6f}mm differs from nominal {nominal:.6f}mm by "
                f"more than thickness_tolerance_mm={tolerance:.6f}")

        mask = num(cfg.get("mask_thickness_mm", 0.01),
                   "board.stackup.mask_thickness_mm")
        copper_names = ["F.Cu"] + [f"In{i}.Cu" for i in range(1, count - 1)] + ["B.Cu"]
        lines = ["\t\t(stackup",
                 "\t\t\t(layer \"F.SilkS\"", "\t\t\t\t(type \"Top Silk Screen\")", "\t\t\t)",
                 "\t\t\t(layer \"F.Paste\"", "\t\t\t\t(type \"Top Solder Paste\")", "\t\t\t)",
                 "\t\t\t(layer \"F.Mask\"", "\t\t\t\t(type \"Top Solder Mask\")",
                 f"\t\t\t\t(thickness {mask})", "\t\t\t)"]
        for idx, layer in enumerate(copper_names):
            lines += [f"\t\t\t(layer {quoted(layer)}", "\t\t\t\t(type \"copper\")",
                      f"\t\t\t\t(thickness {copper_values[idx]:.9g})", "\t\t\t)"]
            if idx < len(dielectrics):
                item = dielectrics[idx]
                lines += [f"\t\t\t(layer \"dielectric {idx + 1}\"",
                          f"\t\t\t\t(type {quoted(item['type'])})",
                          "\t\t\t\t(color \"FR4 natural\")",
                          f"\t\t\t\t(thickness {float(item['thickness_mm']):.9g})",
                          f"\t\t\t\t(material {quoted(item['material'])})",
                          f"\t\t\t\t(epsilon_r {float(item['epsilon_r']):.9g})",
                          f"\t\t\t\t(loss_tangent {float(item['loss_tangent']):.9g})",
                          "\t\t\t)"]
        lines += ["\t\t\t(layer \"B.Mask\"", "\t\t\t\t(type \"Bottom Solder Mask\")",
                  f"\t\t\t\t(thickness {mask})", "\t\t\t)",
                  "\t\t\t(layer \"B.Paste\"", "\t\t\t\t(type \"Bottom Solder Paste\")", "\t\t\t)",
                  "\t\t\t(layer \"B.SilkS\"", "\t\t\t\t(type \"Bottom Silk Screen\")", "\t\t\t)",
                  f"\t\t\t(copper_finish {quoted(cfg.get('copper_finish', 'None'))})",
                  "\t\t\t(dielectric_constraints " +
                  ("yes" if bool(cfg.get("dielectric_constraints", True)) else "no") + ")",
                  "\t\t)"]

        text = self.out.read_text()
        marker = "\n\t(setup\n"
        if text.count(marker) != 1:
            die(f"cannot inject stackup: expected one setup block in {self.out}")
        text = text.replace(marker, marker + "\n".join(lines) + "\n", 1)
        self.out.write_text(text)
        try:
            parsed = pcbnew.LoadBoard(str(self.out))
        except Exception as exc:
            die(f"emitted stackup does not parse in pcbnew: {exc}")
        self.board = parsed
        self.say(f"stackup authored: {count} copper layers, "
                 f"{physical:.4f}mm physical / {nominal:.4f}mm nominal")

    # --------------------------------------------------- via protection
    def write_via_protection(self):
        """Emit board-level filled/capped-via fabrication defaults.

        KiCad 10 writes ``(capping no)`` / ``(filling no)`` when pcbnew saves
        a board, and its Python binding exposes no supported setters for these
        setup fields.  Therefore this must run after the final board save (and
        after the optional stackup injection), exactly like ``write_stackup``:
        patch the native s-expression, then parse it back with pcbnew so a
        format drift is a generation failure rather than a malformed board.

        These flags are BOARD-WIDE DEFAULTS. Via-in-pad fields should normally
        use ``thermal_vias.protection`` instead, which writes item-level
        IPC-4761 overrides and leaves ordinary routing/stitch vias on the
        board default.
        """
        cfg = self.board_cfg.get("via_protection")
        if cfg is None:
            return
        if not isinstance(cfg, dict):
            die("board.via_protection must be a mapping")
        if not cfg:
            die("board.via_protection must declare capping and/or filling")
        unknown = sorted(set(cfg) - {"capping", "filling"})
        if unknown:
            die(f"board.via_protection has unknown key(s): {unknown}; "
                f"known: ['capping', 'filling']")

        def yes_no(value, path):
            if isinstance(value, bool):
                return "yes" if value else "no"
            if isinstance(value, str) and value.strip().lower() in ("yes", "no"):
                return value.strip().lower()
            die(f"{path} must be a boolean (yes/no)")

        text = self.out.read_text()
        emitted = []
        for key in ("capping", "filling"):
            if key not in cfg:
                continue
            value = yes_no(cfg[key], f"board.via_protection.{key}")
            pattern = rf"(?m)^(\s*)\({key} (?:yes|no)\)\s*$"
            text, count = re.subn(pattern, rf"\1({key} {value})", text)
            if count != 1:
                die(f"cannot emit board.via_protection.{key}: expected one "
                    f"KiCad setup token in {self.out}, found {count}")
            emitted.append(f"{key}={value}")
        self.out.write_text(text)
        try:
            parsed = pcbnew.LoadBoard(str(self.out))
        except Exception as exc:
            die(f"emitted via protection does not parse in pcbnew: {exc}")
        self.board = parsed
        self.say("via protection authored (board-level): " + ", ".join(emitted))

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

    # A cutout rect that reaches PAST a board side is not an island in the
    # outline — it is a NOTCH in the boundary, and the side it crosses has to be
    # SPLIT around it. Emitting it as a closed rectangle (what this generator did
    # until 2026-07-25) leaves the untouched side segment running straight
    # through the rect, so the Edge.Cuts polygon self-intersects and the board
    # has NO valid shape: KiCad reports `invalid_outline` ("malformed outline
    # (self-intersecting)") and every zone fill / gerber outline downstream is
    # built from a guess. cooksense v1.3's H4 keypad-isolation notch
    # (rect x[191.50,200.10] against a board edge at x=200.0) was authored as an
    # edge-reaching cutout, generated, MEASURED on "filled copper" and COMMITTED
    # with the outline already broken — nothing between generate_board and DRC
    # reads Edge.Cuts, so an unrun DRC was the only thing holding the gate.
    _SIDES = ("N", "S", "W", "E")

    def _classify_cutouts(self, X0, Y0, X1, Y1, R):
        """Split board.cutouts into INTERNAL islands and per-side edge NOTCHES.

        Returns (internal, notches) where notches maps side -> list of
        (lo, hi, depth): the span consumed on that side and the coordinate the
        notch bottoms out at. Geometry that cannot be expressed as a simple
        boundary notch is a hard error rather than a silent malformed outline."""
        internal, notches = [], {s: [] for s in self._SIDES}
        for cut in self.board_cfg.get("cutouts") or []:
            a, b, c, d = [float(v) for v in cut["rect"]]
            cx0, cx1 = min(a, c), max(a, c)
            cy0, cy1 = min(b, d), max(b, d)
            out = [s for s, past in (("W", cx0 < X0), ("E", cx1 > X1),
                                     ("N", cy0 < Y0), ("S", cy1 > Y1)) if past]
            if not out:
                internal.append((cx0, cy0, cx1, cy1))
                continue
            r = [cx0, cy0, cx1, cy1]
            if len(out) > 1:
                die(f"board.cutouts rect {r} reaches past {len(out)} board "
                    f"sides ({'+'.join(out)}) — a corner cutout is a different "
                    f"outline, not a notch; express it with board.corner_cut "
                    f"or shrink the rect to cross ONE side")
            if R > 0:
                die(f"board.cutouts rect {r} is edge-reaching, but the outline "
                    f"has corner_cut R={R}; notch-on-rounded-corner is not "
                    f"implemented (it would have to split an arc)")
            side = out[0]
            # span consumed on the crossed side, and how deep the notch bites in
            lo, hi, depth = ((cy0, cy1, cx1) if side == "W" else
                             (cy0, cy1, cx0) if side == "E" else
                             (cx0, cx1, cy1) if side == "N" else
                             (cx0, cx1, cy0))
            s_lo, s_hi = (Y0, Y1) if side in ("W", "E") else (X0, X1)
            if not (s_lo < lo < hi < s_hi):
                die(f"board.cutouts rect {r} spans the whole {side} side "
                    f"({lo}..{hi} vs {s_lo}..{s_hi}) — that severs the board, "
                    f"it is not a notch")
            if not (X0 < depth < X1 if side in ("W", "E")
                    else Y0 < depth < Y1):
                die(f"board.cutouts rect {r} notches the {side} side to "
                    f"{depth}, which is outside the outline — check the rect")
            notches[side].append((lo, hi, depth))
        for side, ns in notches.items():
            ns.sort()
            for (lo, hi, _), (lo2, _, _) in zip(ns, ns[1:]):
                if lo2 < hi:
                    die(f"board.cutouts: two notches overlap on the {side} "
                        f"side ({lo}..{hi} and from {lo2}) — merge them into "
                        f"one rect")
        return internal, notches

    def _side_with_notches(self, side, X0, Y0, X1, Y1, notches, w):
        """Emit one board side, split around its notches. Direction is
        irrelevant to Edge.Cuts (the polygon is assembled from the segment
        soup), so every side is walked in increasing coordinate order."""
        fixed = {"W": X0, "E": X1, "N": Y0, "S": Y1}[side]
        lo, hi = (Y0, Y1) if side in ("W", "E") else (X0, X1)
        pt = ((lambda t, f=fixed: (f, t)) if side in ("W", "E")
              else (lambda t, f=fixed: (t, f)))          # (along, across) -> xy
        inner = ((lambda t, d: (d, t)) if side in ("W", "E")
                 else (lambda t, d: (t, d)))
        cur = lo
        for nlo, nhi, depth in notches:
            self._seg(*pt(cur), *pt(nlo), w)             # side up to the notch
            self._seg(*pt(nlo), *inner(nlo, depth), w)   # in
            self._seg(*inner(nlo, depth), *inner(nhi, depth), w)   # across
            self._seg(*inner(nhi, depth), *pt(nhi), w)   # back out
            cur = nhi
        self._seg(*pt(cur), *pt(hi), w)

    def add_outline(self):
        w = float(self.board_cfg.get("edge_width", 0.1))
        X0, Y0, X1, Y1, R = self.X0, self.Y0, self.X1, self.Y1, self.RCUT
        internal, notches = self._classify_cutouts(X0, Y0, X1, Y1, R)
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
            for side in self._SIDES:
                self._side_with_notches(side, X0, Y0, X1, Y1,
                                        notches[side], w)
        n_notch = sum(len(v) for v in notches.values())
        if n_notch:
            self.say(f"outline: {n_notch} edge notch(es) cut into the boundary "
                     f"+ {len(internal)} internal cutout(s)")
        # internal rectangular cutouts / isolation slots: closed islands
        for cx0, cy0, cx1, cy1 in internal:
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

    def add_fiducials(self):
        """Global optical fiducials — `board.fiducials {footprint, refdes_prefix,
        at[]}`, same shape as mounting_holes.

        WHY THIS IS A GENERATOR FEATURE AND NOT A PART. A fiducial is a bare
        copper dot with a mask opening and NO net, NO BOM line and NO placement
        row. Authoring it as a netlist part means inventing an unconnected net,
        an FPID override and two exclusion attrs to undo the three things being a
        part implies — and it still would not be reproducible from a floorplan.
        Adding it here also puts it in the ONE place where it is still cheap:
        BEFORE zones and rule areas, so the pour clears it and DRC grades it.
        Bolted on after routing it is a netless copper island in the middle of a
        filled plane.

        A fiducial is nearly free during a spin and IMPOSSIBLE to add afterwards,
        which is why a board with 0.5 mm-pitch machine-placed parts and no
        fiducial is a recurring finding rather than a one-off.

        Attributes mirror mounting holes (BOARD_ONLY | EXCLUDE_FROM_BOM) plus
        EXCLUDE_FROM_POS_FILES: a fiducial on the CPL is a placement instruction
        for a part that does not exist.
        """
        fd = self.board_cfg.get("fiducials")
        if not fd:
            return
        fpid = fd.get("footprint", "Fiducial:Fiducial_1mm_Mask2mm")
        prefix = fd.get("refdes_prefix", "FID")
        at = fd.get("at") or []
        if at and len(at) < 3:
            die(f"board.fiducials: {len(at)} given — an optical alignment set "
                f"needs at least 3 non-collinear targets to fix rotation as "
                f"well as translation")
        pts = [(float(x), float(y)) for x, y in at]
        if len(pts) >= 3:
            (ax, ay), (bx, by), (cx, cy) = pts[0], pts[1], pts[2]
            area2 = abs((bx - ax) * (cy - ay) - (cx - ax) * (by - ay))
            if area2 < 1.0:
                die(f"board.fiducials: the first three targets are collinear "
                    f"(|cross| = {area2:.3f} mm^2) — a collinear set cannot fix "
                    f"board rotation")
        for i, (fx, fy) in enumerate(pts, 1):
            ref = f"{prefix}{i}"
            fp = self.res.load(ref, fpid)
            fp.SetReference(ref)
            fp.SetAttributes(fp.GetAttributes()
                             | pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_BOM
                             | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
            fp.SetPosition(pcbnew.VECTOR2I_MM(fx, fy))
            self.board.Add(fp)
        self.say(f"fiducials: {len(pts)} placed ({fpid})")

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
        model_overrides = 0
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
            overrides = [pat["model_override"]
                         for pat in self.patterns_for(ref)
                         if "model_override" in pat]
            if len(overrides) > 1:
                die(f"{ref}: multiple placement patterns specify "
                    "model_override; make the model source unambiguous")
            if overrides:
                self.apply_model_override(fp, ref, overrides[0])
                model_overrides += 1
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
        if model_overrides:
            self.say(f"3D model overrides: {model_overrides} footprints "
                     f"source-bound to resolvable files")
        return placed

    def apply_model_override(self, fp, ref, filename):
        """Replace a library footprint's model path with source-owned CAD.

        The original model transform is preserved because a package model can
        legitimately need a footprint-specific offset or rotation.  A missing
        source file is fatal at generation time: KiCad's renderer otherwise
        exits zero while silently omitting the body.
        """
        filename = str(filename or "").strip()
        if not filename:
            die(f"{ref}: placement model_override must be a non-empty path")
        expanded = filename.replace("${KIPRJMOD}",
                                    str(self.out.resolve().parent))
        if "${" in expanded or "$(" in expanded:
            die(f"{ref}: placement model_override contains an unresolved "
                f"variable: {filename!r}")
        candidate = Path(os.path.expanduser(expanded))
        if not candidate.is_absolute():
            candidate = self.out.resolve().parent / candidate
        if not candidate.is_file() or candidate.stat().st_size == 0:
            die(f"{ref}: placement model_override does not resolve to a "
                f"non-empty file: {filename!r} -> {candidate}")

        old = list(fp.Models())
        model = pcbnew.FP_3DMODEL()
        model.m_Filename = filename
        if old:
            # Never mutate an item returned from the SWIG vector in place: the
            # assignment is made on a temporary and is lost on save.  Copy the
            # transform into a new object, then replace the vector atomically.
            for dst, src in ((model.m_Offset, old[0].m_Offset),
                             (model.m_Scale, old[0].m_Scale),
                             (model.m_Rotation, old[0].m_Rotation)):
                dst.x, dst.y, dst.z = src.x, src.y, src.z
            model.m_Show = old[0].m_Show
            model.m_Opacity = old[0].m_Opacity
        fp.Models().clear()
        fp.Models().push_back(model)

    def promote_heatsink_pads_to_vias(self):
        """Turn explicitly marked footprint thermal holes into real vias.

        KiCad library footprints commonly model an exposed-pad via field as
        duplicate PTH pads carrying ``pad_prop_heatsink``. Electrically that
        works, but fabrication processes distinguish component pad holes from
        vias: a via-fill/cap order applies to vias, not ordinary PTH pads.
        Boards opting in through ``thermal_vias.promote_heatsink_pads`` keep
        the exact library land geometry while promoting only those marked
        drilled subpads to board-level ``PCB_VIA`` objects at the same
        position, net, diameter and drill.

        Refusal is deliberate: an unknown reference, a reference with no
        marked drilled pad, a slot/oval, or an unnetted marked pad is an
        authoring error. The generator never guesses which ordinary hole was
        intended to receive an advanced fill/cap process.
        """
        cfg = self.cfg.get("thermal_vias") or {}
        fields = cfg.get("fields") or []
        refs = cfg.get("promote_heatsink_pads") or []
        default_protection = cfg.get("protection")
        if not fields and not refs:
            return
        if fields and not isinstance(fields, list):
            die("thermal_vias.fields must be a list")
        emitted = 0
        for i, field in enumerate(fields):
            if not isinstance(field, dict):
                die(f"thermal_vias.fields[{i}] must be a mapping")
            frefs = field.get("refs")
            if frefs is None and field.get("ref"):
                frefs = [field["ref"]]
            if (not isinstance(frefs, list) or not frefs
                    or any(not isinstance(r, str) for r in frefs)):
                die(f"thermal_vias.fields[{i}].refs must be a non-empty "
                    "list of refdes")
            padnum = str(field.get("pad", ""))
            if not padnum:
                die(f"thermal_vias.fields[{i}] has no pad number")
            at = field.get("at") or []
            if (not isinstance(at, list) or not at
                    or any(not isinstance(p, (list, tuple)) or len(p) != 2
                           for p in at)):
                die(f"thermal_vias.fields[{i}].at must be a non-empty list "
                    "of footprint-relative [x,y] positions")
            size = float(field.get("size", 0))
            drill = float(field.get("drill", 0))
            if size <= 0 or drill <= 0 or drill >= size:
                die(f"thermal_vias.fields[{i}] needs size > drill > 0")
            for ref in frefs:
                fp = self.fps.get(ref)
                if fp is None:
                    die(f"thermal_vias.fields[{i}]: unknown ref {ref!r}")
                target = [p for p in fp.Pads()
                          if p.GetNumber() == padnum and p.GetNetCode() > 0]
                codes = {p.GetNetCode() for p in target}
                if len(codes) != 1:
                    die(f"thermal_vias.fields[{i}]: {ref}.{padnum} must "
                        "resolve to exactly one nonzero net")
                net = target[0].GetNet()
                theta = math.radians(fp.GetOrientationDegrees())
                ct, st = math.cos(theta), math.sin(theta)
                origin = fp.GetPosition()
                for dx, dy in at:
                    dx, dy = float(dx), float(dy)
                    # KiCad board coordinates have +Y downward.  A positive
                    # footprint rotation therefore maps local (dx, dy) as
                    # (dx*cos + dy*sin, -dx*sin + dy*cos), not the ordinary
                    # Cartesian transform.  The opposite sign was electrically
                    # invisible on all-GND fields but put U9's split IN/GND
                    # vias under the wrong exposed land at rot90.
                    x = origin.x / 1e6 + dx * ct + dy * st
                    y = origin.y / 1e6 - dx * st + dy * ct
                    via = pcbnew.PCB_VIA(self.board)
                    via.SetPosition(pcbnew.VECTOR2I_MM(x, y))
                    via.SetWidth(pcbnew.FromMM(size))
                    via.SetDrill(pcbnew.FromMM(drill))
                    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                    via.SetNet(net)
                    try:
                        apply_via_protection(
                            via, field.get("protection", default_protection),
                            f"thermal_vias.fields[{i}].protection")
                    except ValueError as exc:
                        die(str(exc))
                    if not any(p.HitTest(via.GetPosition(), 0, pcbnew.F_Cu)
                               for p in target):
                        die(f"thermal_vias.fields[{i}]: emitted {ref}.{padnum} "
                            f"via at ({x:.3f},{y:.3f}) outside its named pad")
                    via_shape = via.GetEffectiveShape(pcbnew.F_Cu)
                    for other_fp in self.fps.values():
                        for other in other_fp.Pads():
                            if (other.GetNetCode() <= 0
                                    or other.GetNetCode() == net.GetNetCode()
                                    or not other.IsOnLayer(pcbnew.F_Cu)):
                                continue
                            if other.GetEffectiveShape(pcbnew.F_Cu).Collide(
                                    via_shape, 0):
                                die(f"thermal_vias.fields[{i}]: emitted "
                                    f"{ref}.{padnum} via at ({x:.3f},{y:.3f}) "
                                    f"intersects different-net pad "
                                    f"{other_fp.GetReference()}."
                                    f"{other.GetNumber()}")
                    self.board.Add(via)
                    emitted += 1
        if not isinstance(refs, list) or any(not isinstance(r, str) for r in refs):
            die("thermal_vias.promote_heatsink_pads must be a list of refdes")
        if len(refs) != len(set(refs)):
            die("thermal_vias.promote_heatsink_pads contains duplicate refdes")

        promoted = 0
        for ref in refs:
            fp = self.fps.get(ref)
            if fp is None:
                die(f"thermal_vias.promote_heatsink_pads: unknown ref {ref!r}")
            pads = [p for p in fp.Pads()
                    if p.GetProperty() == pcbnew.PAD_PROP_HEATSINK
                    and p.GetDrillSize().x > 0]
            if not pads:
                die(f"thermal_vias.promote_heatsink_pads: {ref} has no drilled "
                    "pad_prop_heatsink pads")
            source_fpid = fp.GetFPIDAsString()
            for pad in pads:
                size, drill = pad.GetSize(), pad.GetDrillSize()
                if size.x != size.y or drill.x != drill.y:
                    die(f"thermal_vias.promote_heatsink_pads: {ref}."
                        f"{pad.GetNumber()} is not a circular pad/drill")
                if pad.GetNetCode() <= 0:
                    die(f"thermal_vias.promote_heatsink_pads: {ref}."
                        f"{pad.GetNumber()} is unnetted")
                via = pcbnew.PCB_VIA(self.board)
                via.SetPosition(pad.GetPosition())
                via.SetWidth(size.x)
                via.SetDrill(drill.x)
                via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                via.SetNet(pad.GetNet())
                try:
                    apply_via_protection(via, default_protection,
                                         "thermal_vias.protection")
                except ValueError as exc:
                    die(str(exc))
                fp.Remove(pad)
                self.board.Add(via)
                promoted += 1
            # The generated footprint intentionally no longer matches its
            # library copy: its marked holes are now true board vias. An
            # unchanged FPID would make KiCad report a permanent
            # lib_footprint_mismatch; clearing it declares an embedded,
            # board-local generated footprint. Preserve the exact authority
            # in its embedded description so traceability is not traded for a
            # quiet DRC report.
            desc = fp.GetLibDescription() or ""
            fp.SetLibDescription(
                (desc + " " if desc else "")
                + f"[generated thermal-via promotion from {source_fpid}]")
            fp.SetFPID(pcbnew.LIB_ID())
        total_refs = {r for field in fields
                      for r in ((field.get("refs") or [field.get("ref")])
                                if isinstance(field, dict) else []) if r}
        total_refs.update(refs)
        self.say(f"thermal vias: emitted {emitted} explicit + promoted "
                 f"{promoted} marked heatsink pad(s) across {len(total_refs)} "
                 "footprint(s) as board-level vias")

    # ------------------------------------------------- P-COLLIDE (placement)
    def _pad_poly(self, pad):
        """Pad copper as mm polygon rings, on its first copper layer."""
        cu = pad.GetLayerSet().CuStack()
        sps = pcbnew.SHAPE_POLY_SET()
        pad.TransformShapeToPolygon(sps, cu[0], 0, 5000, pcbnew.ERROR_INSIDE)
        out = []
        for i in range(sps.OutlineCount()):
            o = sps.Outline(i)
            out.append([(pcbnew.ToMM(o.CPoint(j).x), pcbnew.ToMM(o.CPoint(j).y))
                        for j in range(o.PointCount())])
        return out

    @staticmethod
    def _polys_overlap(A, B):
        """True when two polygon ring lists (mm) share any area.

        Deliberately NOT "min endpoint-to-edge distance <= 0": two rectangles
        crossing in an X have all FOUR endpoint-to-other-edge distances
        strictly positive, so a nearest-point metric reports a comfortable gap
        across a dead short. (Measured on cooksense v1.3: J_ESTOPLOOP.1 vs
        J_DOOR.1 overlap by 1.300 x 0.600 mm and the endpoint metric called it
        +0.250mm.) The test is therefore a true segment-crossing test plus a
        containment test for the fully-enclosed case."""
        def cross(o, a, b):
            return ((a[0] - o[0]) * (b[1] - o[1])
                    - (a[1] - o[1]) * (b[0] - o[0]))

        def seg_hit(p, q, a, c):
            d1, d2 = cross(a, c, p), cross(a, c, q)
            d3, d4 = cross(p, q, a), cross(p, q, c)
            if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
                return True
            # collinear/touching: any endpoint lying on the other segment
            for u, v, w in ((a, c, p), (a, c, q), (p, q, a), (p, q, c)):
                if abs(cross(u, v, w)) < 1e-12 \
                   and min(u[0], v[0]) - 1e-9 <= w[0] <= max(u[0], v[0]) + 1e-9 \
                   and min(u[1], v[1]) - 1e-9 <= w[1] <= max(u[1], v[1]) + 1e-9:
                    return True
            return False

        def inside(ring, pt):
            x, y = pt
            hit = False
            for i in range(len(ring)):
                (ax, ay), (bx, by) = ring[i], ring[(i + 1) % len(ring)]
                if (ay > y) != (by > y) and \
                   x < (bx - ax) * (y - ay) / ((by - ay) or 1e-18) + ax:
                    hit = not hit
            return hit

        for ra in A:
            for i in range(len(ra)):
                p, q = ra[i], ra[(i + 1) % len(ra)]
                for rb in B:
                    for j in range(len(rb)):
                        if seg_hit(p, q, rb[j], rb[(j + 1) % len(rb)]):
                            return True
        return (A and B
                and (inside(B[0], A[0][0]) or inside(A[0], B[0][0])))

    def check_placement_collisions(self):
        """P-COLLIDE — no two parts may be placed ON TOP OF each other.

        THE HOLE THIS FILLS (cooksense v1.3, 2026-07-25): the legalizer only
        moves FLOATING parts. Anchored parts are written down exactly as
        `placement.anchors` says, with NO collision test against each other, so
        two anchors at (or near) the same coordinate place one footprint inside
        the other and the generator prints `placed 223 footprints` and exits 0.
        That happened TWICE in one revision — `U_COMP2: [30.0, 88.0, 0]` and
        `Q_SWA: [30.0, 88.0, 0]` (byte-identical anchors), and J_ESTOPLOOP
        [196,84,90] inside J_DOOR [197,84,90] — shorting the OPTO-ISOLATED 30V
        contactor loop to 3V3 / GND / DOOR_RAW at a measured 0.044mm on a
        mains-adjacent cooking interlock. Both survived a commit. DRC does
        catch it (shorting_items), but DRC is hundreds of router-minutes
        downstream and nothing forced it to run; this makes the placement stage
        refuse to hand on a board that is already electrically dead.

        Three findings, DELIBERATELY graded differently:
          * SHORT (FATAL)   — copper of two pads on DIFFERENT nets overlaps.
                              There is no such thing as an acceptable short, so
                              there is no waiver and no threshold.
          * OVERLAP (FATAL) — copper of two pads in DIFFERENT footprints but on
                              the SAME net overlaps or touches. Connectivity is
                              explicit track/zone copper, never coincident land
                              geometry. Same-footprint composite pads remain
                              legal. The post-build P-PADSEP gate additionally
                              enforces the fab-tier positive-gap floor + paste.
          * PINNED-LAP (FATAL) — two ANCHORED footprints' courtyards overlap
                              or touch. Zero assembly distance is not a valid
                              placement; move the anchors before routing.
                              The legalizer cannot resolve this one, so it is a
                              source defect in floorplan.yaml rather than a
                              density accident, and naming the two ANCHORS is
                              diagnosis that DRC's `courtyards_overlap` does not
                              give you. This used to warn and defer to final
                              DRC; programmable-usb2-hub then reached render
                              review with resistors against module lands. New
                              and materially revised boards fail here. Archived
                              boards are not regenerated to preserve history.
        Floating-vs-anything courtyard overlap is NOT reported at all: resolving
        that is the legalizer's job and it is allowed to leave tight packing."""
        pads = []
        for f in self.board.GetFootprints():
            for p in f.Pads():
                if not p.GetLayerSet().CuStack():
                    continue
                bb = p.GetBoundingBox()
                pads.append((f.GetReference(), p, p.GetNetname(),
                             pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()),
                             pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom())))
        pads.sort(key=lambda r: r[3])
        overlaps, cache = [], {}
        for i, (r1, p1, n1, l1, t1, x1, b1) in enumerate(pads):
            for r2, p2, n2, l2, t2, x2, b2 in pads[i + 1:]:
                if l2 > x1:
                    break                       # sweep: no later pad can touch
                if r1 == r2 or t1 > b2 or t2 > b1:
                    continue
                if not any(p2.GetLayerSet().Contains(l)
                           for l in p1.GetLayerSet().CuStack()):
                    continue
                for k, pp in ((id(p1), p1), (id(p2), p2)):
                    if k not in cache:
                        cache[k] = self._pad_poly(pp)
                if self._polys_overlap(cache[id(p1)], cache[id(p2)]):
                    overlaps.append(("OVERLAP" if n1 == n2 else "SHORT",
                                     r1, p1.GetNumber(), n1,
                                     r2, p2.GetNumber(), n2,
                                     min(x1, x2) - max(l1, l2),
                                     min(b1, b2) - max(t1, t2)))
        laps = []
        pin = [f for f in self.board.GetFootprints()
               if f.GetReference() in self.pinned]
        for i, fa in enumerate(pin):
            pa = fa.GetCourtyard(pcbnew.F_CrtYd)
            ba = pa.BBox()
            if ba.GetWidth() == 0:
                continue
            for fb in pin[i + 1:]:
                pb = fb.GetCourtyard(pcbnew.F_CrtYd)
                bb = pb.BBox()
                # The bbox is a sweep/filter only. Rotated rectangular
                # courtyards routinely have intersecting axis-aligned boxes
                # while their actual assembly polygons are disjoint (the
                # Pluto RX2 radial SMA ring exposed seven such false fails).
                # KiCad DRC grades the polygons, so make the source gate ask
                # the same geometric question rather than moving an
                # electrically-derived placement to satisfy its bounding box.
                if (bb.GetWidth() == 0 or not ba.Intersects(bb)
                        or not pa.Collide(pb)):
                    continue
                laps.append((fa.GetReference(), fb.GetReference(),
                             pcbnew.ToMM(min(ba.GetRight(), bb.GetRight())
                                         - max(ba.GetLeft(), bb.GetLeft())),
                             pcbnew.ToMM(min(ba.GetBottom(), bb.GetBottom())
                                         - max(ba.GetTop(), bb.GetTop()))))
        for a, b, ox, oy in sorted(laps):
            print(f"FAIL P-COLLIDE PINNED-LAP {a} <-> {b}: courtyard polygons "
                  f"overlap/touch (bbox window {ox:.3f} x {oy:.3f} mm) — "
                  f"both are ANCHORED, so the "
                  f"legalizer cannot fix it; fix placement.anchors "
                  f"(full-severity DRC will fail this as courtyards_overlap)")
        if overlaps or laps:
            msg = ["P-COLLIDE: this placement has inter-footprint pad overlap."]
            for kind, r1, pn1, n1, r2, pn2, n2, ox, oy in sorted(overlaps):
                msg.append(f"  {kind:<10} {r1}.{pn1} [{n1}] <-> {r2}.{pn2} "
                           f"[{n2}]  pad copper overlaps "
                           f"(bbox {ox:.3f} x {oy:.3f} mm)")
            for a, b, ox, oy in sorted(laps):
                msg.append(f"  PINNED-LAP {a} <-> {b}  courtyard polygons "
                           f"overlap/touch (bbox window {ox:.3f} x {oy:.3f} "
                           f"mm) — both are ANCHORED, so the "
                           f"legalizer cannot fix it: fix placement.anchors")
            die("\n".join(msg))
        self.say(f"P-COLLIDE: 0 inter-footprint pad overlaps/shorts, "
                 f"{len(laps)} anchored courtyard "
                 f"overlap(s) ({len(pads)} copper pads, {len(pin)} anchored "
                 f"parts)")

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
        # `body_offset`: WHICH WAY DOES THE CONNECTOR MOUTH FACE. A jack's
        # pads cluster at its rear, so the body centroid is displaced toward
        # the opening. Pad order alone cannot catch a 180-degree flip on a
        # symmetric part; this can, and it is the check every board with an
        # edge connector needs (shitty-kitty J1/J2/J6, audit_board I2).
        for e in a.get("body_offset") or []:
            ref, axis = e["ref"], e.get("axis", "x")
            sign = str(e.get("sign", "+"))
            if sign not in ("+", "-"):
                die(f"body_offset: sign must be '+' or '-', got {sign!r}")
            f = self.fps.get(ref) or die(f"body_offset: unknown refdes {ref}")
            pads = [p.GetPosition() for p in f.Pads()]
            if not pads:
                die(f"body_offset: {ref} has no pads")
            bb = f.GetBoundingBox(False, False)
            v = (bb.Centre().x - sum(p.x for p in pads) / len(pads)) if axis == "x" \
                else (bb.Centre().y - sum(p.y for p in pads) / len(pads))
            if (v <= 0) if sign == "+" else (v >= 0):
                die(f"ORIENTATION ASSERT: {ref} body is offset {MM(v):+.2f}mm in "
                    f"{axis} from its pads, expected sign {sign} — the connector "
                    f"opening faces the wrong way")
            n += 1
        # `pad_beyond_edge`: a clearing measured off a pad must fall OUTSIDE
        # the board. An edge-launch antenna (ESP32-S3) is only legal because
        # its keepout hangs off the edge; if the module creeps inboard the
        # keepout lands on live copper and nothing else notices.
        EDGES = {"x0": ("x", -1), "x1": ("x", 1), "y0": ("y", -1), "y1": ("y", 1)}
        for e in a.get("pad_beyond_edge") or []:
            ref, edge = e["ref"], e.get("edge", "y1")
            if edge not in EDGES:
                die(f"pad_beyond_edge: unknown edge {edge!r} (want {sorted(EDGES)})")
            axis, out = EDGES[edge]
            f = self.fps.get(ref) or die(f"pad_beyond_edge: unknown refdes {ref}")
            pad = next((p for p in f.Pads() if p.GetNumber() == str(e["pad"])), None)
            if pad is None:
                die(f"pad_beyond_edge: {ref} has no pad {e['pad']}")
            pos = MM(pad.GetPosition().x if axis == "x" else pad.GetPosition().y)
            got = pos + out * float(e.get("offset", 0.0))
            lim = {"x0": self.X0, "x1": self.X1,
                   "y0": self.Y0, "y1": self.Y1}[edge]
            tol = float(e.get("tolerance", 0.05))
            if (got < lim - tol) if out > 0 else (got > lim + tol):
                die(f"EDGE ASSERT: {ref} clearing measured from pad {e['pad']} "
                    f"reaches {axis}={got:.2f}, which is INSIDE the {edge} edge "
                    f"({lim:.2f}) — it must hang off the board")
            n += 1
        if n:
            self.say(f"asserts: {n} passed")

    # -------------------------------------------------------- legalize
    def bbox(self, f):
        """The rect the legalizer treats as this part's occupied space.

        Normally the footprint bounding box. But a module whose footprint
        carries an ANTENNA KEEPOUT (ESP32-S3, and every castellated radio
        module) has a bbox far larger than its body, and part of it is
        deliberately off-board. Using it as an obstacle fences off live
        board and starves the legalizer. `placement.bbox_override` names the
        real body box in absolute mm; shitty-kitty's audit_board I6 makes
        the identical exemption, so the two must agree.
        """
        ov = (self.place_cfg.get("bbox_override") or {}).get(f.GetReference())
        if ov:
            x0, y0, x1, y1 = [float(v) for v in ov]
            return (x0, y0, x1, y1)
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
        # A bbox_override is an ABSOLUTE rect, so it cannot travel with a part
        # the legalizer is free to move. Refuse rather than silently compute
        # collisions against a stale box.
        for r in (self.place_cfg.get("bbox_override") or {}):
            if r not in self.fps:
                die(f"placement.bbox_override names unknown refdes {r!r}")
            if r not in keep:
                die(f"placement.bbox_override on {r!r}, which the legalizer may "
                    f"move — the override is an absolute rect and would go "
                    f"stale. Pin {r} (placement.pin/keep) or drop the override.")
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

    def apply_post_anchors(self):
        """Apply reviewed local moves *after* deterministic legalization.

        Adding an ordinary anchor removes that ref from the legalizer's
        obstacle/search sequence and can shift unrelated floating parts,
        invalidating an otherwise reusable promoted route.  `post_anchors`
        is deliberately narrower: the normal legalization result is produced
        first, then only the named footprints move.  The existing P-COLLIDE
        gate runs immediately afterward, so a bad local move is still a hard
        placement failure rather than hidden overlap.
        """
        post = self.place_cfg.get("post_anchors") or {}
        if not isinstance(post, dict):
            die("placement.post_anchors must be a mapping of REF: [x,y,rot]")
        moved = 0
        for ref, pose in sorted(post.items()):
            if ref not in self.fps:
                die(f"placement.post_anchors names unknown refdes {ref!r}")
            if not isinstance(pose, (list, tuple)) or len(pose) not in (2, 3):
                die(f"placement.post_anchors[{ref!r}] must be [x,y] or "
                    f"[x,y,rotation]")
            vals = list(pose) + [0]
            fp = self.fps[ref]
            fp.SetPosition(pcbnew.VECTOR2I_MM(float(vals[0]), float(vals[1])))
            fp.SetOrientationDegrees(float(vals[2]))
            self.pinned.add(ref)
            moved += 1
        if moved:
            self.say(f"post-anchored {moved} reviewed local part(s)")

    # -------------------------------------- footprint-internal silk text
    def normalize_footprint_text(self):
        """Tier-floor FOOTPRINT-INTERNAL silk text — Reference/Value fields
        and user text items that arrive INSIDE placed library footprints.

        silk_h() already floors every height this generator EMITS, but a
        library footprint carries its own text, and nothing policed it: the
        v4 usb-hub-3s first DRC carried 112 text_height findings on a
        112-part fresh board (2026-07-21). Normalize UP to the tier floor at
        generation — the same treatment add_silk gives its own text (an
        explicit config value errors, a library default is silently lifted:
        the library never declared a tier, so there is nothing to hold it
        to). F.Fab is documentation, not silkscreen print — exempt, same
        exemption silk_h documents."""
        hfloor, tfloor = self.silk_floors()
        if not hfloor and not tfloor:
            return
        silk = {pcbnew.F_SilkS, pcbnew.B_SilkS}
        n = 0
        for fp in self.board.GetFootprints():
            items = [fp.Reference(), fp.Value()] + list(fp.GraphicalItems())
            for t in items:
                if not callable(getattr(t, "GetTextSize", None)) \
                        or t.GetLayer() not in silk:
                    continue
                sz = t.GetTextSize()
                h = sz.y / 1e6
                changed = False
                if hfloor and h < hfloor - 1e-9:
                    scale = hfloor / max(h, 1e-6)
                    t.SetTextSize(pcbnew.VECTOR2I(int(sz.x * scale),
                                                  pcbnew.FromMM(hfloor)))
                    changed = True
                if tfloor and t.GetTextThickness() / 1e6 < tfloor - 1e-9:
                    t.SetTextThickness(pcbnew.FromMM(tfloor))
                    changed = True
                n += changed
        if n:
            self.say(f"normalized {n} footprint-internal silk text item(s) "
                     f"to the '{self.tier['name']}' floors "
                     f"({hfloor}mm / {tfloor}mm stroke)")

    # ---------------------------------------------------- design rules
    DS_KEYS = {
        "track_min_width": "m_TrackMinWidth", "min_clearance": "m_MinClearance",
        "via_min_annulus": "m_ViasMinAnnularWidth", "hole_clearance": "m_HoleClearance",
        "hole_to_hole": "m_HoleToHoleMin", "copper_edge_clearance": "m_CopperEdgeClearance",
        "via_min_size": "m_ViasMinSize", "min_through_drill": "m_MinThroughDrill",
        "solder_mask_min_width": "m_SolderMaskMinWidth",
        "solder_mask_expansion": "m_SolderMaskExpansion",
        "silk_text_height": "m_MinSilkTextHeight",
        "silk_text_thickness": "m_MinSilkTextThickness",
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
        # CAPABILITY-DERIVED silk DRC constraints. A fresh pcbnew BOARD()
        # defaults m_MinSilkTextHeight to 0.8mm — ABOVE the 0.6mm refdes
        # this generator emits — so every fresh board failed its own silk
        # (112 text_height findings on the v4 112-part board, one per
        # visible Reference field, 2026-07-21; the shipped 2-layer boards
        # only pass because their sealed .kicad_pro was hand-set to 0.6).
        # The constraint now derives from the tier the text heights are
        # already floored at: one capability source, both sides agree.
        # Explicit design_rules values BELOW the tier floor are an error
        # (DRC would stop policing sub-floor silk); stricter is allowed —
        # but then the silk config must supply matching heights.
        hfloor, tfloor = self.silk_floors()
        for key, floor, tkey in (("silk_text_height", hfloor,
                                  "min_silk_text_height"),
                                 ("silk_text_thickness", tfloor,
                                  "min_silk_stroke")):
            if not floor:
                continue
            if vals.get(key) is None:
                vals[key] = floor
            elif float(vals[key]) < floor - 1e-9:
                die(f"design_rules.{key} = {vals[key]} is below fab tier "
                    f"'{self.tier['name']}' {tkey} {floor} — DRC would stop "
                    f"policing sub-floor silk; raise it, or raise fab_tier "
                    f"(D-TIER)")
        for k, v in vals.items():
            if k not in self.DS_KEYS:
                die(f"unknown design_rules key {k!r} (known: {sorted(self.DS_KEYS)})")
            setattr(ds, self.DS_KEYS[k], pcbnew.FromMM(float(v)))
        ds.m_MinConn = int((self.cfg.get("design_rules") or {}).get("min_conn", 0))

    # ------------------------------------------------------------ zones
    LAYER_NAMES = {"F.Cu": pcbnew.F_Cu, "B.Cu": pcbnew.B_Cu,
                   "In1.Cu": pcbnew.In1_Cu, "In2.Cu": pcbnew.In2_Cu,
                   "In3.Cu": pcbnew.In3_Cu, "In4.Cu": pcbnew.In4_Cu}
    # min copper count that has each inner layer (6-layer boards need In3/In4 —
    # the mixed-signal-audio-hub archetype's In1+In4 GND-plane stackup)
    INNER_LAYERS = {"In1.Cu": 3, "In2.Cu": 4, "In3.Cu": 5, "In4.Cu": 6}

    def check_layer(self, lname, what):
        """A copper layer must be BOTH spelled correctly and present in the
        stackup. pcbnew's LSET will happily hold In1.Cu on a 2-layer board,
        producing a zone on a layer that does not exist — it just never
        fills, and no DRC complains."""
        if lname not in self.LAYER_NAMES:
            die(f"{what} on unknown layer {lname!r} "
                f"(known: {sorted(self.LAYER_NAMES)})")
        need = self.INNER_LAYERS.get(lname)
        have = int(self.board_cfg.get("layers", 2))
        if need and have < need:
            die(f"{what} on {lname}, but board.layers is {have} — that layer "
                f"is not in the stackup, so the copper would silently vanish")
        return self.LAYER_NAMES[lname]

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
        for zi, z in enumerate(self.cfg.get("zones") or []):
            net = z.get("net")
            if net and net not in self.netmap:
                die(f"zone on unknown net {net!r} (netlist has no such net)")
            pts = self.zone_points(z)
            _validate_simple_polygon(pts,
                                     f"zones[{zi}] net {net!r} outline")
            for lname in z.get("layers") or ["F.Cu", "B.Cu"]:
                lid = self.check_layer(lname, f"zone on net {net!r}")
                zone = pcbnew.ZONE(self.board)
                zone.SetLayer(lid)
                if net:
                    zone.SetNet(self.netmap[net])
                zone.SetAssignedPriority(int(z.get("priority", 0)))
                zone.SetMinThickness(pcbnew.FromMM(float(z.get("min_thickness", 0.25))))
                zone.SetLocalClearance(pcbnew.FromMM(float(z.get("clearance", 0.25))))
                # KiCad's zone defaults are 0.50 mm for both values.  That is
                # too coarse for common 0402/fine-pitch layouts and silently
                # turns otherwise legal thermal connections into
                # `starved_thermal` DRC failures.  Keep the default unless the
                # board source declares a manufacturing-qualified geometry.
                if "thermal_gap" in z:
                    zone.SetThermalReliefGap(
                        pcbnew.FromMM(float(z["thermal_gap"])))
                if "thermal_spoke_width" in z:
                    zone.SetThermalReliefSpokeWidth(
                        pcbnew.FromMM(float(z["thermal_spoke_width"])))
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
        # escape_corridors: [{ref, side: N|S|E|W, depth_mm, width_mm?}] —
        # reserved routing lanes off a dense package's loaded side (Phase F,
        # from usb-pwr-hub-3s ADR-0008: 8 escapes on one 0.65mm side need a
        # corridor at STANDARD tier or the hole-to-hole floor walls them in).
        # Sugar over keepouts: expands to a named rule area (esc_<ref>_<side>)
        # denying footprints+pours — tracks and vias stay allowed, that is
        # the point of the lane. escape_check v2's `escape-corridor`
        # condition (P-ESC) is satisfied by exactly this reservation.
        for ec in self.cfg.get("escape_corridors") or []:
            ref, side = ec.get("ref"), str(ec.get("side", "")).upper()
            fp = self.board.FindFootprintByReference(str(ref)) if ref else None
            if not fp:
                die(f"escape_corridor: unknown ref {ref!r}")
            if side not in ("N", "S", "E", "W"):
                die(f"escape_corridor {ref}: side must be N|S|E|W, got {ec.get('side')!r}")
            depth = float(ec.get("depth_mm", 0))
            if depth <= 0:
                die(f"escape_corridor {ref}: depth_mm must be > 0")
            bb = fp.GetBoundingBox(False, False)
            x0, y0 = pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop())
            x1, y1 = pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom())
            if ec.get("width_mm"):
                w = float(ec["width_mm"])
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                if side in ("N", "S"):
                    x0, x1 = cx - w / 2, cx + w / 2
                else:
                    y0, y1 = cy - w / 2, cy + w / 2
            rect = {"N": [x0, y0 - depth, x1, y0], "S": [x0, y1, x1, y1 + depth],
                    "W": [x0 - depth, y0, x0, y1], "E": [x1, y0, x1 + depth, y1]}[side]
            (self.cfg.setdefault("keepouts", []) or self.cfg["keepouts"]).append({
                "rect": rect,
                "layers": ec.get("layers") or ["F.Cu"],
                "name": f"esc_{ref}_{side}",
                "deny": ["footprints", "pours"],
            })
        for k in self.cfg.get("keepouts") or []:
            pts = self.zone_points(k)
            _validate_simple_polygon(
                pts, f"keepout {k.get('name', '?')!r} outline")
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
                lid = self.check_layer(lname, f"keepout {k.get('name', '?')!r}")
                # KiCad's SWIG binding spells this AddLayer on some builds and
                # addLayer on others; both appear across our own generators.
                add = getattr(ls, "AddLayer", None) or getattr(ls, "addLayer")
                add(lid)
            # ORDER IS LOAD-BEARING: ZONE::SetLayer() COLLAPSES the layer set
            # to that single layer, so it must come FIRST and SetLayerSet must
            # have the last word. Reversed, a 4-layer antenna keepout silently
            # became an F.Cu-only rule area — DRC-clean, and wrong on the three
            # layers nobody looked at. (Found regenerating shitty-kitty; the
            # two 2-layer proof boards declared no keepouts and never hit it.)
            z.SetLayer(self.LAYER_NAMES[layers[0]])
            z.SetLayerSet(ls)
            if set(z.GetLayerSet().Seq()) != {self.LAYER_NAMES[n] for n in layers}:
                die(f"keepout {k.get('name', '?')!r}: layer set did not stick "
                    f"(wanted {layers}, got "
                    f"{[self.board.GetLayerName(l) for l in z.GetLayerSet().Seq()]})")
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
        """Emit an fp-lib-table covering exactly the libraries the netlist
        actually used — BY DEFAULT, beside the output board (2026-07-21).

        Emission used to be opt-in (`project.fp_lib_table: <path>`), and the
        v4 usb-hub-3s canary never opted in: its first DRC carried 116
        lib_footprint_issues — "The current configuration does not include
        the footprint library 'X'", one per footprint (112 parts + 4
        mounting holes), all noise, all preventable at generation. Measured:
        the same board + the table = 0 in that class. A fresh board now gets
        `<board dir>/fp-lib-table` unless the project says
        `fp_lib_table: false`; an explicit path still overrides."""
        tbl = self.cfg.get("project", {}).get("fp_lib_table")
        if tbl is False:
            return
        path = self._p(tbl) if tbl else self.out.parent / "fp-lib-table"
        prjdir = path.parent.resolve()          # ${KIPRJMOD} == the pro dir
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
                # the RUNNING KiCad's own env var, not a hardcoded major:
                # a ${KICAD9_*} table happens to resolve on 10.0.4 through
                # back-compat vars, but that is version luck, and an
                # unresolved var is 116 lib_footprint_issues again
                uri = uri.replace(STD_FP_ROOT, _kicad_fp_env())
            elif uri and os.path.isabs(uri):
                # A PROJECT-LOCAL lib (e.g. 03_src/lib/pod.pretty) must be
                # ${KIPRJMOD}-relative, never absolute: contract 04_kicad
                # "fp-lib-table has no absolute paths" / project-structure.md
                # "use ${KIPRJMOD} for local libs". Absolute paths break the
                # instant a repo is cloned or the board moves. Only rewrite
                # libs UNDER the project tree; a stray absolute system path
                # stays as-is (and the contract check will still catch it).
                try:
                    inside = Path(uri).resolve().is_relative_to(self.base.resolve())
                except AttributeError:                          # py<3.9
                    inside = str(Path(uri).resolve()).startswith(
                        str(self.base.resolve()) + os.sep)
                if inside:
                    relp = os.path.relpath(Path(uri).resolve(), prjdir)
                    uri = "${KIPRJMOD}/" + relp.replace(os.sep, "/")
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

    # ------------------------------------------------- silk OWNERSHIP term
    # A LABEL MUST END UP NEARER ITS OWN PART THAN ANY OTHER. The slot search
    # used to take the FIRST non-colliding offset out to ~11mm and never ask
    # whose label it was, so the objective it optimised ("does not collide")
    # was silent about the only property a reader uses ("which part is this
    # naming?"). MEASURED on the shipped output of two boards, 2026-07-29:
    # pluto-cal-switch 36 of 73 refdes labels nearer another part than their
    # own; pluto-rx2-8way 40 of 64, plus the 'ANT4'/'RX1'/'RX2' port captions
    # attributed to passives on a board with ten near-identical SMA jacks —
    # a mis-mate hazard, not a cosmetic one.
    #
    # This is a MISSING OBJECTIVE, not a measurement-precision problem:
    # pluto-cal-switch first tried tightening the METRIC (courtyard-edge
    # distance instead of centroid) and it rescued ZERO of its 36. Hence a
    # term, scored inside the placer's own obstacle model (which includes the
    # whole-footprint body bbox an offline check omits).
    def _ownership(self, cand, ref):
        """(ok, d_own, d_other, other_ref) for label box `cand` claimed by
        `ref`. Distances are box-centre to footprint centroid — the same
        measurement the board audits use, so the numbers are comparable.
        Mounting holes carry no printed designator and cannot be confused
        with a part, so they do not compete."""
        cx = (cand[0] + cand[2]) / 2.0
        cy = (cand[1] + cand[3]) / 2.0
        d_own, d_oth, oth = None, float("inf"), None
        for r, x, y in self._own_cent:
            d = math.hypot(x - cx, y - cy)
            if r == ref:
                d_own = d
            elif d < d_oth:
                d_oth, oth = d, r
        if d_own is None:                  # unknown/hole ref: nothing to own
            return True, 0.0, d_oth, oth
        return (d_own <= d_oth + 1e-9), d_own, d_oth, oth

    def _caption_owner(self, txt):
        """A fixed caption's PRESUMPTIVE owner, inferred from the board's own
        data rather than a new config key: the SINGLE part whose refdes
        contains the caption's alphanumeric token ('ANT4' -> J_ANT4,
        'RX2' -> J_RX2). Ambiguous ('CTRL' on a board with R_CTRL1/R_CTRL2)
        or unmatched ('70 MHz - 6 GHz') means no owner, and then the caption
        keeps the pre-existing first-clear-slot behaviour."""
        tok = re.sub(r"[^A-Z0-9]", "", txt.upper())
        if len(tok) < 2:
            return None
        hits = [r for r in self.fps if r not in self.hole_refs
                and tok in re.sub(r"[^A-Z0-9]", "", r.upper())]
        return hits[0] if len(hits) == 1 else None

    def _place_owned(self, t, ax, ay, offsets, ref, kind, txt,
                     pad_obst, silk_obst, poses=(None,), frame_m=0.2):
        """Slot search with the ownership term. PHASE 1 walks the poses and
        offsets in the placer's existing preference order but accepts only a
        slot that is collision-free AND OWNED. PHASE 2 runs only when no owned
        slot exists anywhere: it takes the slot with the SMALLEST ownership
        deficit and files an EVIDENCED degradation with the measured lead —
        never a silent first-slot placement (the J_ISOLOOP class is real: pads
        at the centre of the body in x means anything printed either side is
        under the moulding once fitted, and no term can fix that). Returns
        (placed, cand)."""
        best = None
        for pose in poses:
            if pose:
                pose()
            for dx, dy in offsets:
                t.SetPosition(pcbnew.VECTOR2I_MM(ax + dx, ay + dy))
                cand = box_of(t.GetBoundingBox())
                if not self._in_frame(cand, frame_m):
                    continue
                if any(hit(cand, o) for o in pad_obst) \
                        or any(hit(cand, o) for o in silk_obst):
                    continue
                if ref is None:
                    return True, cand
                ok, d_own, d_oth, oth = self._ownership(cand, ref)
                if ok:
                    self.own_ok += 1
                    return True, cand
                if best is None or (d_own - d_oth) < best[0] - 1e-12:
                    best = (d_own - d_oth, pose, dx, dy, d_own, d_oth, oth)
        if best is None:
            return False, None
        _, pose, dx, dy, d_own, d_oth, oth = best
        if pose:
            pose()
        t.SetPosition(pcbnew.VECTOR2I_MM(ax + dx, ay + dy))
        self.own_deg.append((kind, ref, txt, d_own, d_oth, oth))
        print(f"WARN silk ownership: {kind} {txt!r} for {ref} lands "
              f"{d_own:.2f}mm from {ref} but {d_oth:.2f}mm from {oth} "
              f"(lead {d_oth - d_own:+.2f}mm) — no owned slot in the "
              f"{len(poses)}x{len(offsets)} search")
        return True, box_of(t.GetBoundingBox())

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
        # stroke from the ONE formula (module-level silk_stroke): floored at
        # the tier's min_silk_stroke and clamped to what KiCad can plot.
        t.SetTextThickness(pcbnew.FromMM(
            silk_stroke(size, self.silk_floors()[1])))
        return t

    def add_silk(self):
        rc = self.silk_cfg.get("refdes") or {}
        clr = float(rc.get("clearance", 0.16))
        min_h = self.silk_h(self.silk_cfg.get("min_text_height"), 0.6,
                            "min_text_height")
        pad_obst, silk_obst = self._obstacles(clr)
        # ownership scoring state (see _ownership / _place_owned)
        self._own_cent = [(r, MM(f.GetPosition().x), MM(f.GetPosition().y))
                          for r, f in sorted(self.fps.items())
                          if r not in self.hole_refs]
        self.own_ok, self.own_deg, self.own_none = 0, [], []

        # ---- fixed functional captions, collision-nudged
        cap_nudge = bool(self.silk_cfg.get("caption_nudge", True))
        crowded = 0
        for cap in self.silk_cfg.get("captions") or []:
            if isinstance(cap, dict):
                txt = cap["text"]
                x, y = float(cap["at"][0]), float(cap["at"][1])
                size = self.silk_h(cap.get("size"), 0.7,
                                   f"caption {txt[:24]!r} size")
                nudge = self.NUDGE if cap.get("nudge", cap_nudge) else [(0, 0)]
                rot = float(cap.get("rot", 0))
            else:
                txt, x, y = cap[0], float(cap[1]), float(cap[2])
                size = self.silk_h(cap[3] if len(cap) > 3 else None, 0.7,
                                   f"caption {txt[:24]!r} size")
                nudge = self.NUDGE if cap_nudge else [(0, 0)]
                rot = 0.0
            size = max(size, min_h)
            t = self._mktext(txt, size)
            if rot:
                t.SetTextAngleDegrees(rot)
            owner = self._caption_owner(txt)
            ok, _ = self._place_owned(t, x, y, nudge, owner, "caption", txt,
                                      pad_obst, silk_obst, frame_m=0.4)
            if not ok:
                # no clear slot at all: fall back to the coordinate the config
                # ASKED FOR, not the last offset the search happened to try.
                t.SetPosition(pcbnew.VECTOR2I_MM(x, y))
            self.board.Add(t)          # keep even if crowded
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
                    derived.append((ref, txt,
                                    self.silk_h(rule.get("size"), 0.6,
                                                f"label {ref} size")))

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
            ok, cand = self._place_owned(t, fx, fy, self.OFF, ref, "label",
                                         txt, pad_obst, silk_obst)
            if ok:
                silk_obst.append(cand)
                self.board.Add(t)
                nlab += 1
            else:
                self.own_none.append(("label", ref, txt))

        # ---- polarity marks ("K" beside pad 1 of a diode, etc.)
        for mark in self.silk_cfg.get("polarity_marks") or []:
            ref, pad, glyph = mark["ref"], str(mark.get("pad", 1)), mark.get("text", "K")
            f = self.fps.get(ref) or die(f"polarity_mark: unknown refdes {ref}")
            p1 = next((p for p in f.Pads() if p.GetNumber() == pad), None)
            if p1 is None:
                die(f"polarity_mark: {ref} has no pad {pad}")
            px, py = MM(p1.GetPosition().x), MM(p1.GetPosition().y)
            kt = self._mktext(glyph, self.silk_h(None, 0.6, "polarity mark"))
            ok, cand = self._place_owned(kt, px, py, self.OFF, ref, "polarity",
                                         glyph, pad_obst, silk_obst)
            if not ok:
                die(f"no clear spot for the {ref} polarity mark {glyph!r}")
            self.board.Add(kt)
            silk_obst.append(cand)

        # ---- refdes: F.SilkS de-collided + ALWAYS an F.Fab copy
        # (fab_size is NOT tier-floored: F.Fab is documentation, not silk)
        size = self.silk_h(rc.get("size"), 0.6, "refdes size")
        small = self.silk_h(rc.get("min_size"), 0.45, "refdes min_size")
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

            def mkpose(rot, sz, ref=ref):
                def _pose():
                    ref.SetTextAngleDegrees(rot)   # stand up in narrow gaps
                    ref.SetTextSize(pcbnew.VECTOR2I_MM(sz, sz))
                    ref.SetTextThickness(int(silk_stroke(
                        sz, self.silk_floors()[1], REFDES_STROKE_OVER_SIZE,
                        REFDES_STROKE_MIN) * 1e6))
                return _pose

            poses = [mkpose(rot, sz) for rot in (0, 90)
                     for sz in (size, small)]
            ok, cand = self._place_owned(ref, fx, fy, self.OFF, r, "refdes",
                                        r, pad_obst, silk_obst, poses=poses)
            if ok:
                silk_obst.append(cand)
            if not ok:
                ref.SetTextAngleDegrees(0)
                ref.SetVisible(False)
                self.waived.append(r)
                self.own_none.append(("refdes", r, r))
        n = len(self.fps) - len(self.hole_refs)
        self.say(f"refdes on silk: {n - len(self.waived)}/{n} placed, "
                 f"{len(self.waived)} waived to F.Fab: {sorted(self.waived)}; "
                 f"{nlab} functional labels, {crowded} crowded captions")
        # THE DENOMINATOR (canon M-COVER): every label with an owning part is
        # graded, and the ones ownership could not be satisfied for are named
        # with their measured lead — a degradation REPORTED, never silent.
        own_tot = self.own_ok + len(self.own_deg) + len(self.own_none)
        self.say(f"silk ownership: {self.own_ok}/{own_tot} owned labels sit "
                 f"nearer their own part than any other; "
                 f"{len(self.own_deg)} degraded, {len(self.own_none)} unplaced"
                 + (": " + ", ".join(
                     f"{k} {t!r}@{rf} own {a:.2f} vs {o} {b:.2f}"
                     for k, rf, t, a, b, o in self.own_deg)
                    if self.own_deg else ""))

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
    cfg = yaml.safe_load(cfgp.read_text(encoding="utf-8-sig"))
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
