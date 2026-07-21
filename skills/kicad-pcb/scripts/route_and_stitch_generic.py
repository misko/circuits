#!/usr/bin/env python3
"""route_and_stitch_generic — ONE parameterized routing + stitch/fill backend,
driven by a small declarative per-board `03_src/route.yaml`, replacing the
hand-written `03_src/route_prep.py` + `route_waves.sh` + `stitch_and_fill.py`
that every project used to carry (215-537 lines of stitcher each).

WHY. `generate_board_generic.py` collapsed the board GENERATOR; the stage
after it stayed bespoke. Surveying six shipped boards (usb-power-3s,
ble-bus-bar, crow-array-pod, cook-loadcell, crowsync-recorder, cook-hub)
showed the same pipeline every time, with different constants:

    route-prep (track-free + unfilled + keepouts + rules ride along)
      -> KRT waves, hardest-first, chained rN -> rN+1
      -> import ONCE into the track-free base
      -> stitch: clean KRT artifacts -> rescue pads -> stitch grid
                 -> janitor -> FILL -> island rescue -> gate
      -> generate_rules LAST (pcbnew saves clobber .kicad_pro netclasses)

    /usr/bin/python3 route_and_stitch_generic.py prep    03_src/route.yaml
    <KRT venv python>  route_and_stitch_generic.py route 03_src/route.yaml
    /usr/bin/python3 route_and_stitch_generic.py import  03_src/route.yaml
    /usr/bin/python3 route_and_stitch_generic.py stitch  03_src/route.yaml
    /usr/bin/python3 route_and_stitch_generic.py all     03_src/route.yaml

`prep`, `import` and `stitch` need the KiCad-bundled interpreter
(`/usr/bin/python3`, the one with `pcbnew`). `route` only shells out to KRT
and runs on any python.

LOAD-BEARING ORDER (each deviation reintroduces a debugged failure):
  * netclasses/ampacity floors exist BEFORE routing, and the route input
    carries its own .kicad_pro/.kicad_dru (canon R1) — `prep` refuses to
    run if the source .kicad_pro has no netclass patterns.
  * the route input is TRACK-FREE and UNFILLED — KRT routes straight
    through pre-existing copper otherwise (400+ silent crossings, twice).
  * KRT output is imported ONCE, into the track-free base, never into a
    board that already carries tracks (that doubles everything).
  * `generate_rules` runs LAST, after the final pcbnew save. This script
    never writes .kicad_pro, so it cannot clobber netclasses — but the
    caller still has to re-run its rules generator afterwards, and
    `stitch` prints that reminder.

HARD ERRORS (never silent):
  * prep on a board that still has tracks or filled zones
  * prep when the route input would carry no netclasses (canon R1)
  * a KRT wave naming a net the board does not have
  * a KRT wave exiting nonzero
  * any stitch pass falling short of its configured `min` / `require`
  * `import` onto a board that already has tracks

CONFIG SCHEMA — a skill-owned example is
`../pcb-design/templates/03_src/route.yaml` (project-independent — do NOT read
another project's config).
Relative paths resolve against the PROJECT ROOT (the yaml's grandparent dir),
so the commands work from any cwd. Top-level keys:

  project:  name, board (the pcbnew board to route/stitch), build_dir
  prep:     out, keepouts {layers, mounting_holes, npth_pads, edge_band,
            rects[]}, waves {exclude[], groups{}, rest}
  route:    krt, python, common{...}, waves[] {name, nets|group, + any
            KRT flag override}
  stitch:   via{}, keepin{}, passes[] (the ORDER — this is the axis the
            six boards actually disagree on), plus one block per pass

The `passes` list is deliberately explicit rather than a fixed pipeline:
the survey found the stitch grid running first, middle and LAST across
boards, and it matters (the grid consumes via-exclusion zones that later
rescues must dodge).
"""
import argparse
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml


# ---------------------------------------------------------------- errors
class RouteConfigError(RuntimeError):
    """Any hard, board-invalidating error. Never caught internally."""


def die(msg):
    raise RouteConfigError(msg)


# ---------------------------------------------------------------- config
def load_cfg(path, root=None):
    path = Path(path).resolve()
    if not path.is_file():
        die(f"route config not found: {path}")
    cfg = yaml.safe_load(path.read_text()) or {}
    if "project" not in cfg:
        die(f"{path}: no 'project:' block")
    cfg["_path"] = path
    # 03_src/route.yaml -> project root is the grandparent
    cfg["_root"] = Path(root).resolve() if root else path.parent.parent
    return cfg


def rel(cfg, p):
    p = Path(os.path.expanduser(str(p)))
    return p if p.is_absolute() else (cfg["_root"] / p)


def get(cfg, dotted, default=None):
    node = cfg
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    return node


# ------------------------------------------------- fab-tier capability floors
def fab_tier(cfg):
    """The project's declared fab tier (fab_tiers.yaml entry, or None).
    Cached on the cfg dict — nets.yaml is read once per command."""
    if "_tier" not in cfg:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from fab_tier_util import FabTierError, resolve
        try:
            cfg["_tier"] = resolve(cfg["_root"])
        except FabTierError as e:
            die(str(e))
    return cfg["_tier"]


# config key -> the fab_tiers.yaml floor it must respect
_TIER_GEOM = (("via_size", "min_via_diameter"),
              ("via_drill", "min_via_drill"),
              ("clearance", "min_space"))


def tier_geometry(d, tier, where, derive=True,
                  keymap={"via_size": "via_size", "via_drill": "via_drill",
                          "clearance": "clearance"}):
    """CAPABILITY-DERIVED via/clearance geometry (the clean-room 3S gap:
    hardcoded 0.6/0.3 defaults on a 4L-standard board whose declared tier's
    floor is 0.45/0.3 — 2 drill_out_of_range only caught at DRC). Missing
    values default to the tier floor (the cheapest legal geometry); EXPLICIT
    values below a floor are an ERROR naming the tier, never a silent clamp.
    `keymap` renames the keys for callers whose config spells them
    differently (stitch.via uses size/drill)."""
    if tier is None:
        return d
    for gkey, fkey in _TIER_GEOM:
        key = keymap.get(gkey)
        if key is None or fkey not in tier:
            continue
        floor = float(tier[fkey])
        if d.get(key) is None:
            if derive:
                d[key] = floor
        elif float(d[key]) < floor - 1e-9:
            die(f"{where}.{key} = {d[key]} is below fab tier "
                f"'{tier['name']}' {fkey} {floor} — raise it, or raise "
                f"fab_tier (D-TIER)")
    return d


# ============================================================== PREP =====
def _keepout_rect(pcbnew, b, x0, y0, x1, y1, layer):
    poly = pcbnew.PCB_SHAPE(b)
    poly.SetShape(pcbnew.SHAPE_T_POLY)
    poly.SetPolyPoints(pcbnew.VECTOR_VECTOR2I(
        [pcbnew.VECTOR2I_MM(x0, y0), pcbnew.VECTOR2I_MM(x1, y0),
         pcbnew.VECTOR2I_MM(x1, y1), pcbnew.VECTOR2I_MM(x0, y1)]))
    poly.SetLayer(layer)
    poly.SetFilled(False)
    poly.SetWidth(pcbnew.FromMM(0.05))
    b.Add(poly)


def _layer_id(pcbnew, name):
    lay = b_layer_cache.get(name)
    if lay is None:
        lay = getattr(pcbnew, name.replace(".", "_"), None)
        if lay is None:
            die(f"unknown layer name {name!r} (want e.g. 'User.2')")
        b_layer_cache[name] = lay
    return lay


b_layer_cache = {}


def _rules_ride_along(cfg, src_pcb, out_pcb):
    """canon R1: the route input must carry the netclasses. Copy the pro/dru
    beside the r0 board and REFUSE if the pro has no netclass patterns —
    the fleet audit found every board's route input running on bare
    Default 0.2mm, so width floors were only enforced post-route."""
    pro = src_pcb.with_suffix(".kicad_pro")
    if not pro.is_file():
        die(f"canon R1: no {pro.name} beside the board — run the rules "
            f"generator BEFORE route-prep")
    import json
    try:
        d = json.loads(pro.read_text())
    except Exception as e:                                   # pragma: no cover
        die(f"canon R1: {pro} is not readable JSON: {e}")
    ns = d.get("net_settings") or {}
    classes = [c for c in ns.get("classes", []) if c.get("name") != "Default"]
    pats = ns.get("netclass_patterns") or []
    if not classes or not pats:
        die(f"canon R1: {pro.name} carries no netclasses "
            f"({len(classes)} non-Default classes, {len(pats)} patterns) — "
            f"rules must ride INTO the router, not just gate it afterwards")
    shutil.copy(pro, out_pcb.with_suffix(".kicad_pro"))
    dru = src_pcb.with_suffix(".kicad_dru")
    if dru.is_file():
        shutil.copy(dru, out_pcb.with_suffix(".kicad_dru"))
    print(f"canon R1: rules ride along ({len(classes)} netclasses, "
          f"{len(pats)} patterns)")


def cmd_prep(cfg):
    import pcbnew
    src = rel(cfg, cfg["project"]["board"])
    build = rel(cfg, get(cfg, "project.build_dir", "06_build/route"))
    out = build / get(cfg, "prep.out", "r0.kicad_pcb")
    out.parent.mkdir(parents=True, exist_ok=True)

    b = pcbnew.LoadBoard(str(src))
    tracks = list(b.GetTracks())
    if tracks:
        die(f"route-prep expects a TRACK-FREE board, found {len(tracks)} "
            f"tracks in {src.name} — KRT routes straight through existing "
            f"copper (400+ silent crossings, observed twice)")
    nfilled = 0
    for z in b.Zones():
        if z.IsFilled():
            nfilled += 1
        z.UnFill()
    print(f"unfilled {nfilled} zones")

    ko = get(cfg, "prep.keepouts", {}) or {}
    layers = [_layer_id(pcbnew, n) for n in ko.get("layers", ["User.2"])]
    n_ko = 0

    mh = ko.get("mounting_holes")
    if mh:
        r = float(mh.get("radius", 3.0))
        pfx = mh.get("refdes_prefix")
        for f in b.GetFootprints():
            if pfx and not f.GetReference().startswith(pfx):
                continue
            hit = False
            for p in f.Pads():
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    x, y = p.GetPosition().x / 1e6, p.GetPosition().y / 1e6
                    for lay in layers:
                        _keepout_rect(pcbnew, b, x - r, y - r, x + r, y + r, lay)
                    n_ko += 1
                    hit = True
            if pfx and not hit:
                x, y = f.GetPosition().x / 1e6, f.GetPosition().y / 1e6
                for lay in layers:
                    _keepout_rect(pcbnew, b, x - r, y - r, x + r, y + r, lay)
                n_ko += 1

    npth = ko.get("npth_pads")
    if npth:
        # KRT only knows the copper clearance; DRC's hole_clearance is
        # separate. Fence NPTH barrels or tracks graze them (12x on one board).
        margin = float(npth.get("margin", 0.6))
        for f in b.GetFootprints():
            for p in f.Pads():
                if p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH:
                    continue
                x, y = p.GetPosition().x / 1e6, p.GetPosition().y / 1e6
                r = p.GetDrillSize().x / 2e6 + margin
                for lay in layers:
                    _keepout_rect(pcbnew, b, x - r, y - r, x + r, y + r, lay)
                n_ko += 1

    band = ko.get("edge_band")
    if band:
        eb = float(band)
        x0, y0, x1, y1 = board_rect(pcbnew, b, cfg)
        for (a, c, d, e) in [(x0, y0, x1, y0 + eb), (x0, y1 - eb, x1, y1),
                             (x0, y0, x0 + eb, y1), (x1 - eb, y0, x1, y1)]:
            for lay in layers:
                _keepout_rect(pcbnew, b, a, c, d, e, lay)
            n_ko += 1

    for r in ko.get("rects", []) or []:
        rl = [_layer_id(pcbnew, r["layer"])] if r.get("layer") else layers
        for lay in rl:
            _keepout_rect(pcbnew, b, float(r["x0"]), float(r["y0"]),
                          float(r["x1"]), float(r["y1"]), lay)
        n_ko += 1
    print(f"keepouts: {n_ko} rects on {[str(x) for x in ko.get('layers', ['User.2'])]}")

    b.Save(str(out))
    _rules_ride_along(cfg, src, out)

    groups = wave_nets(cfg, board_nets(b))
    for name, nets in groups.items():
        (build / f"nets_{name}.txt").write_text(" ".join(nets) + "\n")
    print(f"wrote {out} + " + ", ".join(
        f"{n}({len(v)})" for n, v in groups.items()))
    return 0


def board_rect(pcbnew, b, cfg=None):
    if cfg:
        r = get(cfg, "stitch.keepin.rect") or get(cfg, "board.rect")
        if r:
            return float(r["x0"]), float(r["y0"]), float(r["x1"]), float(r["y1"])
    bb = b.GetBoardEdgesBoundingBox()
    return (bb.GetLeft() / 1e6, bb.GetTop() / 1e6,
            bb.GetRight() / 1e6, bb.GetBottom() / 1e6)


def board_nets(b):
    return sorted({p.GetNetname() for f in b.GetFootprints() for p in f.Pads()}
                  - {""})


def wave_nets(cfg, allnets):
    """Split the board's nets into named wave groups. `exclude` supports
    globs; one group may be `rest` (everything not named and not excluded)."""
    import fnmatch
    w = get(cfg, "prep.waves", {}) or {}
    excl = list(w.get("exclude", ["GND", "unconnected-*"]))

    def is_excluded(n):
        return any(fnmatch.fnmatch(n, e) for e in excl)

    out, claimed = {}, set()
    for name, nets in (w.get("groups") or {}).items():
        if nets == "rest":
            out[name] = "rest"
            continue
        missing = [n for n in nets if n not in allnets]
        if missing:
            die(f"wave group {name!r} names nets the board does not have: "
                f"{missing}")
        out[name] = list(nets)
        claimed.update(nets)
    for name, v in list(out.items()):
        if v == "rest":
            out[name] = [n for n in allnets
                         if n not in claimed and not is_excluded(n)]
    return out


# ============================================================= ROUTE =====
_KRT_FLAGMAP = {
    "layers": ("--layers", "list"),
    "clearance": ("--clearance", "val"),
    "track_width": ("--track-width", "val"),
    "via_size": ("--via-size", "val"),
    "via_drill": ("--via-drill", "val"),
    "fab_tier": ("--fab-tier", "val"),
    "keepout_layer": ("--keepout-layer", "val"),
    "max_iterations": ("--max-iterations", "val"),
    "max_probe_iterations": ("--max-probe-iterations", "val"),
    "max_ripup": ("--max-ripup", "val"),
    "grid_step": ("--grid-step", "val"),
    "rip_existing_nets": ("--rip-existing-nets", "list"),
    "no_stub_layer_swap": ("--no-stub-layer-swap", "flag"),
    "keepout": ("--keepout", "flag"),
}


def _krt_args(d):
    out = []
    for k, v in d.items():
        if k in ("name", "nets", "group"):
            continue
        if k not in _KRT_FLAGMAP:
            die(f"unknown KRT option {k!r} — extend _KRT_FLAGMAP rather than "
                f"guessing a flag name")
        flag, kind = _KRT_FLAGMAP[k]
        if kind == "flag":
            if v:
                out.append(flag)
        elif kind == "list":
            out.append(flag)
            out += [str(x) for x in v]
        else:
            out += [flag, str(v)]
    return out


def cmd_route(cfg):
    build = rel(cfg, get(cfg, "project.build_dir", "06_build/route"))
    krt = Path(os.path.expanduser(get(cfg, "route.krt", "~/gits/KiCadRoutingTools")))
    py = get(cfg, "route.python") or str(krt / ".venv" / "bin" / "python")
    if not (krt / "route.py").is_file():
        die(f"KRT not found at {krt} (KiCad has no autorouter; clone "
            f"github drandyhaas/KiCadRoutingTools)")
    common = dict(get(cfg, "route.common", {}) or {})
    waves = get(cfg, "route.waves", []) or []
    if not waves:
        die("route.waves is empty — nothing to route")
    # tier-derived geometry: missing via/clearance come from the declared fab
    # tier; explicit sub-floor values are rejected (per-wave overrides too).
    tier = fab_tier(cfg)
    tier_geometry(common, tier, "route.common")

    cur = build / get(cfg, "prep.out", "r0.kicad_pcb")
    if not cur.is_file():
        die(f"{cur} missing — run `prep` first")
    for i, wv in enumerate(waves, 1):
        name = wv.get("name", f"w{i}")
        nets = wv.get("nets")
        if nets is None:
            grp = wv.get("group", name)
            f = build / f"nets_{grp}.txt"
            if not f.is_file():
                die(f"wave {name!r}: {f} missing — run `prep` first")
            nets = f.read_text().split()
        if not nets:
            print(f"wave {name}: 0 nets, skipped")
            continue
        nxt = build / f"r{i}.kicad_pcb"
        opts = dict(common)
        opts.update({k: v for k, v in wv.items()
                     if k not in ("name", "nets", "group")})
        tier_geometry(opts, tier, f"route.waves[{name}]", derive=False)
        cmd = ([py, str(krt / "route.py"), str(cur), "--output", str(nxt)]
               + _krt_args(opts) + ["--nets"] + list(nets))
        print(f"\n=== wave {name}: {len(nets)} nets ===\n  "
              + " ".join(cmd[:2] + ["..."] + cmd[-min(6, len(nets) + 1):]))
        r = subprocess.run(cmd)
        if r.returncode != 0:
            die(f"KRT wave {name!r} exited {r.returncode}")
        if not nxt.is_file():
            die(f"KRT wave {name!r} produced no {nxt}")
        cur = nxt
    print(f"\nwaves done -> {cur}")
    (build / "FINAL").write_text(str(cur) + "\n")
    return 0


def cmd_import(cfg):
    """Import the final chain file ONCE into the track-free base."""
    import pcbnew
    build = rel(cfg, get(cfg, "project.build_dir", "06_build/route"))
    # A fresh route in the build dir WINS over the promoted chain file, the
    # same precedence every rebuild_all.sh used ("[ -f 06_build/... ] || cp").
    final = get(cfg, "route.final")
    if (build / "FINAL").is_file():
        chain = Path((build / "FINAL").read_text().strip())
    elif final:
        chain = rel(cfg, final)
    else:
        die("no route.final in the config and no build FINAL marker — "
            "run `route`, or point route.final at the promoted chain file")
    if not chain.is_file():
        die(f"chain file {chain} not found")
    target = rel(cfg, cfg["project"]["board"])
    b = pcbnew.LoadBoard(str(target))
    n = len(list(b.GetTracks()))
    if n:
        die(f"import target {target.name} already has {n} tracks — "
            f"re-importing DOUBLES everything (holes_co_located x69, "
            f"observed 2026-07). Regenerate the board first.")
    stale = Path(str(target) + Ctx.STATE_SUFFIX)
    if stale.is_file():
        stale.unlink()          # a fresh import invalidates any resume point
    imp = Path(__file__).resolve().parent / "import_krt.py"
    r = subprocess.run([sys.executable, str(imp), str(chain),
                        str(target), str(target)])
    if r.returncode != 0:
        die(f"import_krt exited {r.returncode}")
    return 0


# ============================================================ STITCH =====
class Ctx:
    """Board + toolkit + counters, rebindable across the SWIG barrier."""

    def __init__(self, cfg, path):
        import pcbnew
        from pcb_toolkit import Toolkit
        self.pcbnew, self.Toolkit = pcbnew, Toolkit
        self.cfg = cfg
        self.path = Path(path)
        self.board = pcbnew.LoadBoard(str(self.path))
        self.tk = Toolkit(self.board, float(get(cfg, "stitch.clearance", 0.15)))
        self.failures = []
        self.counts = {}
        self.pending = []          # (ref, padnum) of pads still unserved
        self.dirty = False         # a Remove() happened -> barrier required
        self._used = None
        self._pth = None

    def remove(self, item):
        """EVERY removal goes through here. board.Remove() poisons the
        board's SWIG iterators for the rest of the interpreter: the next
        pass's GetTracks() raises 'SwigPyObject is not iterable', or a
        second LoadBoard hands back a bare SwigPyObject. Marking the board
        dirty makes the driver insert a fresh-interpreter barrier before
        the next pass runs (cook-loadcell, 2026-07-20: without it,
        drop_dangling crashed and left 8 unconnected pads on the board)."""
        self.board.Remove(item)
        self.dirty = True

    # -- cross-barrier state -----------------------------------------
    # An in-process save+LoadBoard is NOT a barrier: after b.Remove(), a
    # second LoadBoard in the same interpreter returns a raw SwigPyObject
    # with no BOARD methods (reproduced on KiCad 10.0.4 — the "SWIG
    # iterators can poison mid-session after a Remove" trap). The only
    # reliable barrier is a FRESH INTERPRETER, so `reload` re-execs and
    # these two helpers carry the counters/pending pads across it.
    STATE_SUFFIX = ".stitch_state.json"

    def state_path(self):
        return Path(str(self.path) + self.STATE_SUFFIX)

    def save_state(self, resume):
        import json
        self.state_path().write_text(json.dumps(
            {"resume": resume, "counts": self.counts,
             "failures": self.failures, "pending": self.pending}))

    def load_state(self):
        import json
        p = self.state_path()
        if not p.is_file():
            return 0
        d = json.loads(p.read_text())
        self.counts = d.get("counts", {})
        self.failures = d.get("failures", [])
        self.pending = [tuple(x) for x in d.get("pending", [])]
        return int(d.get("resume", 0))

    def pads(self, pending):
        """(ref, padnum) -> live pad objects on the CURRENT board."""
        want = set(pending)
        out = []
        for fp in self.board.GetFootprints():
            for p in fp.Pads():
                if (fp.GetReference(), p.GetNumber()) in want:
                    out.append((fp.GetReference(), p))
        return out

    # -- shared site machinery ---------------------------------------
    @property
    def used(self):
        if self._used is None:
            self._used = {(round(v.GetPosition().x / 1e6, 2),
                           round(v.GetPosition().y / 1e6, 2))
                          for v in self.board.GetTracks()
                          if v.GetClass() == "PCB_VIA"}
        return self._used

    @property
    def pth(self):
        if self._pth is None:
            self._pth = [(p.GetPosition().x / 1e6, p.GetPosition().y / 1e6,
                          p.GetDrillSize().x / 2e6)
                         for fp in self.board.GetFootprints() for p in fp.Pads()
                         if p.GetDrillSize().x > 0]
        return self._pth

    def bump(self, k, n=1):
        self.counts[k] = self.counts.get(k, 0) + n

    def keepin(self, x, y):
        k = get(self.cfg, "stitch.keepin", {}) or {}
        x0, y0, x1, y1 = board_rect(self.pcbnew, self.board, self.cfg)
        ins = float(k.get("inset", 0.8))
        if not (x0 + ins < x < x1 - ins and y0 + ins < y < y1 - ins):
            return False
        cc = float(k.get("corner_cut", 0.0))
        if cc:
            for cx, cy in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
                if math.hypot(x - cx, y - cy) < cc + ins:
                    return False
        for r in k.get("avoid", []) or []:
            m = float(r.get("margin", 0.0))
            if (float(r["x0"]) - m < x < float(r["x1"]) + m
                    and float(r["y0"]) - m < y < float(r["y1"]) + m):
                return False
        return True

    def try_via(self, net, x, y, avoid=()):
        """Place one collide-checked via. THE shared primitive: every via
        this script adds goes through here, so the spacing/PTH/keepin
        guards can never be bypassed by a new pass."""
        v = get(self.cfg, "stitch.via", {}) or {}
        spacing = float(v.get("spacing", 0.62))
        pth_margin = float(v.get("pth_margin", 0.3))
        x, y = round(x, 2), round(y, 2)
        if not self.keepin(x, y):
            return False
        for r in avoid:
            m = float(r.get("margin", 0.0))
            if (float(r["x0"]) - m < x < float(r["x1"]) + m
                    and float(r["y0"]) - m < y < float(r["y1"]) + m):
                return False
        if any((x - ux) ** 2 + (y - uy) ** 2 < spacing ** 2
               for ux, uy in self.used):
            return False
        tiers = v.get("tiers") or [{"size": v.get("size", 0.6),
                                    "drill": v.get("drill", 0.3)}]
        for t in tiers:
            size, drill = float(t["size"]), float(t["drill"])
            if any(math.hypot(x - hx, y - hy) < r + drill / 2 + pth_margin
                   for hx, hy, r in self.pth):
                continue
            kw = {}
            if "hole_to_copper" in t:
                kw["hole_to_copper"] = float(t["hole_to_copper"])
            if self.tk.via_site_ok(x, y, net.GetNetCode(), size=size,
                                   drill=drill, **kw):
                self.tk.add_via(x, y, net, size=size, drill=drill)
                self.used.add((x, y))
                return True
        return False

    def net(self, name):
        n = self.board.FindNet(name)
        if n is None or n.GetNetCode() <= 0:
            die(f"stitch: board has no net {name!r}")
        return n


MM = None  # bound in cmd_stitch once pcbnew is importable


# ------------------------------------------------------------ passes ----
PASSES = {}


def stitch_pass(name):
    def deco(fn):
        PASSES[name] = fn
        return fn
    return deco


def _ends_mm(t):
    return ((t.GetStart().x / 1e6, t.GetStart().y / 1e6),
            (t.GetEnd().x / 1e6, t.GetEnd().y / 1e6))


@stitch_pass("dedupe_vias")
def p_dedupe_vias(ctx, c):
    """KRT pass-chaining re-emits the same via in each output; importing the
    chain lands them stacked. via_site_ok skips same-net copper, so it
    happily approves a via ON an identical via — dedupe by coordinate."""
    r = float(c.get("radius", 0.45))
    vs = [(t, t.GetNetCode(), t.GetPosition().x / 1e6, t.GetPosition().y / 1e6)
          for t in ctx.board.GetTracks() if t.GetClass() == "PCB_VIA"]
    dead = set()
    for i, (_, n1, x1, y1) in enumerate(vs):
        if i in dead:
            continue
        for j in range(i + 1, len(vs)):
            _, n2, x2, y2 = vs[j]
            if j in dead or n1 != n2:
                continue
            if c.get("metric", "box") == "box":
                near = abs(x1 - x2) < r and abs(y1 - y2) < r
            else:
                near = math.hypot(x1 - x2, y1 - y2) < r
            if near:
                dead.add(j)
    for j in dead:
        ctx.remove(vs[j][0])
    ctx.bump("deduped_vias", len(dead))
    print(f"deduped {len(dead)} twin vias")


@stitch_pass("dedupe_tracks")
def p_dedupe_tracks(ctx, c):
    seen, dead = set(), []
    for t in ctx.board.GetTracks():
        if t.GetClass() != "PCB_TRACK":
            continue
        a, b = (t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)
        key = (t.GetNetCode(), t.GetLayer(), t.GetWidth(), tuple(sorted([a, b])))
        (dead.append(t) if key in seen else seen.add(key))
    for t in dead:
        ctx.remove(t)
    ctx.bump("deduped_tracks", len(dead))
    print(f"deduped {len(dead)} duplicate segments")


@stitch_pass("normalize_vias")
def p_normalize_vias(ctx, c):
    lo = float(c.get("below_width", 0.449))
    size, drill = float(c.get("size", 0.6)), float(c.get("drill", 0.3))
    n = 0
    for t in ctx.board.GetTracks():
        if t.GetClass() == "PCB_VIA" and t.GetWidth() / 1e6 < lo:
            t.SetWidth(int(size * 1e6))
            t.SetDrill(int(drill * 1e6))
            n += 1
    ctx.bump("normalized_vias", n)
    print(f"normalized {n} sub-spec vias to {size}/{drill}")


@stitch_pass("drop_micro_fragments")
def p_micro(ctx, c):
    """KRT leaves sub-grid whiskers at pass joins. Removing one with BOTH
    ends served disconnects the net, so the default requires a free end."""
    lim = float(c.get("max_length", 0.12))
    need_free = bool(c.get("require_free_end", True))
    segs = [t for t in ctx.board.GetTracks() if t.GetClass() == "PCB_TRACK"]
    endpts = {}
    for t in segs:
        for e in _ends_mm(t):
            k = (round(e[0], 2), round(e[1], 2))
            endpts[k] = endpts.get(k, 0) + 1
    dead = []
    for t in segs:
        (ax, ay), (bx, by) = _ends_mm(t)
        if math.hypot(ax - bx, ay - by) >= lim:
            continue
        if need_free and not any(
                endpts.get((round(e[0], 2), round(e[1], 2)), 0) < 2
                for e in _ends_mm(t)):
            continue
        dead.append(t)
    for t in dead:
        ctx.remove(t)
    ctx.bump("micro_removed", len(dead))
    print(f"removed {len(dead)} dangling micro-fragments")


def _end_anchored(ctx, t, ex, ey, segs, vias, pads, tol):
    """Is this end on an ANCHOR (another segment's endpoint, a via, a pad)?
    KiCad's connectivity anchors tracks at endpoints only, so a T-junction
    landing mid-body is NOT anchored — that is exactly what the
    `track_dangling` DRC item reports."""
    code = t.GetNetCode()
    uid = t.m_Uuid.AsString()
    for o in segs:
        if o.m_Uuid.AsString() == uid or o.GetNetCode() != code or o.GetLayer() != t.GetLayer():
            continue
        for (ox, oy) in _ends_mm(o):
            if math.hypot(ex - ox, ey - oy) <= tol:
                return True
    for vx, vy, vc in vias:
        if vc == code and math.hypot(ex - vx, ey - vy) <= 0.32:
            return True
    for p, pc in pads:
        if pc != code:
            continue
        bb = p.GetBoundingBox()
        bb.Inflate(int(tol * 1e6))
        if bb.Contains(ctx.pcbnew.VECTOR2I_MM(ex, ey)):
            return True
    return False


def _track_context(ctx):
    segs = [t for t in ctx.board.GetTracks() if t.GetClass() == "PCB_TRACK"]
    vias = [(t.GetPosition().x / 1e6, t.GetPosition().y / 1e6, t.GetNetCode())
            for t in ctx.board.GetTracks() if t.GetClass() == "PCB_VIA"]
    pads = [(p, p.GetNetCode()) for fp in ctx.board.GetFootprints()
            for p in fp.Pads()]
    return segs, vias, pads


@stitch_pass("split_t_junctions")
def p_split_t(ctx, c):
    """KRT emits T-junctions: one segment's END lands on the MIDDLE of
    another. The copper is continuous, but KiCad anchors connectivity at
    ENDPOINTS, so DRC reports `track_dangling` on the stub — and a fab gate
    that counts warnings fails on a board that is electrically fine.
    Splitting the crossed segment at the foot makes the junction a shared
    endpoint. Geometry-preserving: same copper, same net, same width.
    Deleting the stub instead is WRONG — on cook-loadcell the T-stub
    carried TP3 and a via, so removal disconnected them."""
    pcbnew = ctx.pcbnew
    tol = float(c.get("tol", 0.05))
    segs, vias, pads = _track_context(ctx)
    splits = {}
    for t in segs:
        for (ex, ey) in _ends_mm(t):
            if _end_anchored(ctx, t, ex, ey, segs, vias, pads, tol):
                continue
            best = None
            for o in segs:
                if (o.m_Uuid.AsString() == t.m_Uuid.AsString() or o.GetNetCode() != t.GetNetCode()
                        or o.GetLayer() != t.GetLayer()):
                    continue
                (ox, oy), (px, py) = _ends_mm(o)
                dx, dy = px - ox, py - oy
                L2 = dx * dx + dy * dy
                if L2 == 0:
                    continue
                u = ((ex - ox) * dx + (ey - oy) * dy) / L2
                if not (0.01 < u < 0.99):
                    continue
                d = math.hypot(ex - ox - u * dx, ey - oy - u * dy)
                if d <= tol + o.GetWidth() / 2e6 and (best is None or d < best[0]):
                    best = (d, o, u, ox + u * dx, oy + u * dy)
            if best:
                _, o, u, fx, fy = best
                splits.setdefault(o.m_Uuid.AsString(), [o, []])[1].append((u, fx, fy))
    n = 0
    for _uid, (o, pts) in splits.items():
        (ox, oy), (px, py) = _ends_mm(o)
        chain = [(0.0, ox, oy)] + sorted(pts) + [(1.0, px, py)]
        for a, b in zip(chain, chain[1:]):
            if math.hypot(a[1] - b[1], a[2] - b[2]) < 1e-6:
                continue
            s = pcbnew.PCB_TRACK(ctx.board)
            s.SetStart(pcbnew.VECTOR2I_MM(round(a[1], 4), round(a[2], 4)))
            s.SetEnd(pcbnew.VECTOR2I_MM(round(b[1], 4), round(b[2], 4)))
            s.SetWidth(o.GetWidth())
            s.SetLayer(o.GetLayer())
            s.SetNetCode(o.GetNetCode())
            ctx.board.Add(s)
        ctx.remove(o)
        n += 1
    ctx.bump("t_junctions_split", n)
    print(f"split {n} segments at T-junctions "
          f"({sum(len(v[1]) for v in splits.values())} junction points)")


@stitch_pass("drop_dangling")
def p_dangling(ctx, c):
    """KRT overshoot tails: a segment with one end served by NOTHING (no
    same-net track end, pad or via) carries no current, but DRC reports it
    as track_dangling and a fab gate that counts warnings fails on it.
    Iterated to a fixpoint — removing one tail exposes the next (ble-bus-bar
    needed three sweeps). `require_free_end` semantics, no length floor:
    the cap is what keeps a genuine long trace from being eaten."""
    tol = float(c.get("tol", 0.05))
    cap = float(c.get("max_length", 1.0))
    sweeps = int(c.get("sweeps", 4))
    total = 0
    for _ in range(sweeps):
        segs = [t for t in ctx.board.GetTracks() if t.GetClass() == "PCB_TRACK"]
        vias = [(t.GetPosition().x / 1e6, t.GetPosition().y / 1e6, t.GetNetCode())
                for t in ctx.board.GetTracks() if t.GetClass() == "PCB_VIA"]
        pads = [(p, p.GetNetCode()) for fp in ctx.board.GetFootprints()
                for p in fp.Pads()]

        def served(t, ex, ey):
            code = t.GetNetCode()
            uid = t.m_Uuid.AsString()
            for o in segs:
                if o.m_Uuid.AsString() == uid or o.GetNetCode() != code:
                    continue
                if o.GetLayer() != t.GetLayer():
                    continue
                (ox, oy), (px, py) = _ends_mm(o)
                if (math.hypot(ex - ox, ey - oy) <= tol
                        or math.hypot(ex - px, ey - py) <= tol):
                    return True
                # T-junction: this end lands on the BODY of a same-net
                # segment. Missing this check ate 8 real connections on
                # cook-loadcell's multipoint nets (2026-07-20).
                dx, dy = px - ox, py - oy
                L2 = dx * dx + dy * dy
                if L2 == 0:
                    continue
                u = max(0.0, min(1.0, ((ex - ox) * dx + (ey - oy) * dy) / L2))
                if math.hypot(ex - ox - u * dx, ey - oy - u * dy) <= \
                        tol + o.GetWidth() / 2e6:
                    return True
            for vx, vy, vc in vias:
                if vc == code and math.hypot(ex - vx, ey - vy) <= 0.32:
                    return True
            for p, pc in pads:
                if pc != code:
                    continue
                bb = p.GetBoundingBox()
                bb.Inflate(int(tol * 1e6))
                if bb.Contains(ctx.pcbnew.VECTOR2I_MM(ex, ey)):
                    return True
            return False

        dead = []
        for t in segs:
            (ax, ay), (bx, by) = _ends_mm(t)
            if math.hypot(ax - bx, ay - by) > cap:
                continue
            if not served(t, ax, ay) or not served(t, bx, by):
                dead.append(t)
        if not dead:
            break
        for t in dead:
            ctx.remove(t)
        total += len(dead)
    ctx.bump("dangling_removed", total)
    print(f"removed {total} dangling stubs (<= {cap}mm, one end unserved)")


@stitch_pass("width_floor")
def p_width_floor(ctx, c):
    """Routers have no ampacity concept. The netclass .kicad_dru floors make
    a thin power track a DRC violation; this lifts KRT's thin-pass output to
    the floor so the gate passes for the right reason."""
    floors = {k: float(v) for k, v in (c.get("nets") or {}).items()}
    region = c.get("region")
    default = c.get("default")
    n = 0
    for t in ctx.board.GetTracks():
        if t.GetClass() != "PCB_TRACK":
            continue
        fl = floors.get(t.GetNetname(), default)
        if fl is None:
            continue
        if region:
            (ax, ay), (bx, by) = _ends_mm(t)
            if not (float(region["x0"]) <= min(ax, bx)
                    and max(ax, bx) <= float(region["x1"])
                    and float(region["y0"]) <= min(ay, by)
                    and max(ay, by) <= float(region["y1"])):
                continue
        if t.GetWidth() < int(float(fl) * 1e6) - 1000:
            t.SetWidth(int(float(fl) * 1e6))
            n += 1
    ctx.bump("width_lifted", n)
    print(f"lifted {n} segments to their netclass floor")


@stitch_pass("reload")
def p_reload(ctx, c):
    """SWIG barrier. Handled by the driver (it needs the pass index), so
    reaching this body means the driver forgot to intercept it."""
    die("internal: 'reload' must be intercepted by cmd_stitch")


@stitch_pass("hole_to_hole")
def p_hole_to_hole(ctx, c):
    """Fab floor is a DRILL-EDGE gap (0.5mm at JLC). Two modes, both shipped:
    nudge the offending via (carrying its track endpoints), or shrink it."""
    pcbnew = ctx.pcbnew
    floor = float(c.get("min_gap", 0.5))
    mode = c.get("mode", "nudge")
    keep = list(c.get("prefer_keep", ["GND"]))
    vlist = [t for t in ctx.board.GetTracks() if t.GetClass() == "PCB_VIA"]

    def vxy(v):
        return (v.GetPosition().x / 1e6, v.GetPosition().y / 1e6)

    moved = 0
    for i in range(len(vlist)):
        for j in range(i + 1, len(vlist)):
            v1, v2 = vlist[i], vlist[j]
            x1, y1 = vxy(v1)
            x2, y2 = vxy(v2)
            d1, d2 = v1.GetDrill() / 1e6, v2.GetDrill() / 1e6
            if math.hypot(x1 - x2, y1 - y2) - (d1 + d2) / 2 >= floor:
                continue
            vm = v1 if (v2.GetNetname() in keep and v1.GetNetname() not in keep) else v2
            if mode == "shrink":
                s = c.get("shrink_to", {"size": 0.48, "drill": 0.2})
                vm.SetWidth(int(float(s["size"]) * 1e6))
                vm.SetDrill(int(float(s["drill"]) * 1e6))
                moved += 1
                continue
            mx, my = vxy(vm)
            ends = [t for t in ctx.board.GetTracks()
                    if t.GetClass() == "PCB_TRACK"
                    and t.GetNetCode() == vm.GetNetCode()
                    and any(abs(e.x / 1e6 - mx) < 0.05 and abs(e.y / 1e6 - my) < 0.05
                            for e in (t.GetStart(), t.GetEnd()))]
            done = False
            for r in c.get("rings", [0.25, 0.4, 0.6, 0.85, 1.1]):
                for ang in range(0, 360, int(c.get("angle_step", 45))):
                    nx = round(mx + r * math.cos(math.radians(ang)), 2)
                    ny = round(my + r * math.sin(math.radians(ang)), 2)
                    if any(math.hypot(nx - ox, ny - oy) < 0.85
                           for ov in vlist if ov is not vm
                           for ox, oy in [vxy(ov)]):
                        continue
                    if not ctx.tk.via_site_ok(nx, ny, vm.GetNetCode(),
                                              size=vm.GetWidth() / 1e6,
                                              drill=vm.GetDrill() / 1e6):
                        continue
                    bad = False
                    for t in ends:
                        st = t.GetStart()
                        at_start = (abs(st.x / 1e6 - mx) < 0.05
                                    and abs(st.y / 1e6 - my) < 0.05)
                        other = t.GetEnd() if at_start else t.GetStart()
                        if ctx.tk.collides(nx, ny, other.x / 1e6, other.y / 1e6,
                                           t.GetWidth() / 1e6, t.GetNetCode(),
                                           t.GetLayer()) is not None:
                            bad = True
                            break
                    if bad:
                        continue
                    vm.SetPosition(pcbnew.VECTOR2I_MM(nx, ny))
                    for t in ends:
                        for gget, gset in ((t.GetStart, t.SetStart),
                                           (t.GetEnd, t.SetEnd)):
                            e = gget()
                            if (abs(e.x / 1e6 - mx) < 0.05
                                    and abs(e.y / 1e6 - my) < 0.05):
                                gset(pcbnew.VECTOR2I_MM(nx, ny))
                    moved += 1
                    done = True
                    break
                if done:
                    break
    ctx._used = None
    ctx.bump("h2h_fixed", moved)
    print(f"hole-to-hole repair ({mode}): {moved} vias")


@stitch_pass("stitch_grid")
def p_stitch_grid(ctx, c):
    net = ctx.net(c.get("net", "GND"))
    gx, gy = c["x"], c["y"]
    avoid = c.get("avoid", []) or []
    n = 0
    for x in range(int(gx[0]), int(gx[1]), int(gx[2])):
        for y in range(int(gy[0]), int(gy[1]), int(gy[2])):
            if ctx.try_via(net, float(x), float(y), avoid=avoid):
                n += 1
    ctx.bump("grid_vias", n)
    print(f"stitch grid: {n} vias")
    lo = c.get("min")
    if lo is not None and n < int(lo):
        ctx.failures.append(f"stitch grid too sparse: {n} < {lo}")


def _rescue_targets(ctx, c):
    """The (netname, plane_layer) pairs pad_rescue must serve.

    THREE forms, in priority order (GAP A: a 4-layer board with In1=GND and
    In2=VIN needs BOTH plane-nets rescued, not one):
      * `nets: [{net: GND, layer: In1.Cu}, {net: VIN, layer: In2.Cu}]` — the
        explicit multi-plane list. A bare string entry is allowed (layer None).
      * `net: GND` (+ optional `plane_layer`) — the ORIGINAL single-net form,
        preserved verbatim so every shipped 2-layer config keeps working.
      * `auto: true` — detect every SOLID inner-plane pour (a non-Default
        copper layer carrying a whole-board net zone) and rescue that net.
    With none of the above it defaults to GND, exactly as before."""
    nets = c.get("nets")
    if nets:
        out = []
        for e in nets:
            if isinstance(e, dict):
                out.append((e["net"], e.get("layer") or e.get("plane_layer")))
            else:
                out.append((e, None))
        return out
    if c.get("auto"):
        return _auto_plane_nets(ctx, c)
    return [(c.get("net", "GND"), c.get("plane_layer"))]


def _auto_plane_nets(ctx, c):
    """Every net that owns a solid pour on an INNER copper layer. A plane is a
    zone on an In*.Cu layer covering most of the board; its net's SMD pads all
    need a barrel down to it. Ordered by layer so output is deterministic."""
    pcbnew = ctx.pcbnew
    x0, y0, x1, y1 = board_rect(pcbnew, ctx.board, ctx.cfg)
    board_area = max((x1 - x0) * (y1 - y0), 1.0)
    frac = float(c.get("auto_min_area_frac", 0.15))
    seen, out = set(), []
    for z in ctx.board.Zones():
        if z.GetIsRuleArea() or not z.GetNetname():
            continue
        for lay in z.GetLayerSet().Seq():
            lname = ctx.board.GetLayerName(lay)
            if lay in (pcbnew.F_Cu, pcbnew.B_Cu) or ".Cu" not in lname:
                continue
            bb = z.GetBoundingBox()
            if (bb.GetWidth() / 1e6) * (bb.GetHeight() / 1e6) < frac * board_area:
                continue
            key = (z.GetNetname(), lname)
            if key in seen:
                continue
            seen.add(key)
            out.append((z.GetNetname(), lname))
    out.sort(key=lambda t: (t[1], t[0]))
    return out


def _rescue_one_net(ctx, c, netname, plane_layer, stub_boxes):
    """Rescue every SMD pad of ONE plane-net to its plane. Via-in-pad first
    where the config allows it (a same-net barrel always bonds when a solid
    pour of that net lives under the whole board), else an adjacent via plus a
    short stub. Each adjacent-via+stub landing appends its footprint to
    `stub_boxes` so GAP B can scope those thin drops out of the trunk floor.
    Returns (served, total, [(ref, pad), ...] unserved)."""
    pcbnew = ctx.pcbnew
    net_obj = ctx.net(netname)
    serve_r = float(c.get("served_within", 1.6))
    rings = c.get("rings", [0.75, 0.95, 1.2, 1.6, 2.1, 2.7])
    astep = int(c.get("angle_step", 30))
    stub_w = float(c.get("stub_width", 0.3))
    vip = bool(c.get("via_in_pad", True))
    skip = set(c.get("skip_refs", []) or [])

    def has_via(pad):
        px, py = pad.GetPosition().x / 1e6, pad.GetPosition().y / 1e6
        for t in ctx.board.GetTracks():
            if t.GetClass() == "PCB_VIA" and t.GetNetCode() == pad.GetNetCode():
                vx, vy = t.GetPosition().x / 1e6, t.GetPosition().y / 1e6
                if (vx - px) ** 2 + (vy - py) ** 2 < serve_r * serve_r:
                    return True
        return False

    ok = tot = 0
    fails = []
    for fp in ctx.board.GetFootprints():
        if fp.GetReference() in skip:
            continue
        for p in fp.Pads():
            if p.GetDrillSize().x > 0 or p.GetNetname() != netname:
                continue
            tot += 1
            if has_via(p):
                ok += 1
                continue
            px, py = p.GetPosition().x / 1e6, p.GetPosition().y / 1e6
            if vip and ctx.try_via(net_obj, px, py):
                ok += 1
                continue
            bb = p.GetBoundingBox()
            w2, h2 = bb.GetWidth() / 2e6, bb.GetHeight() / 2e6
            lay = (p.GetLayer() if p.GetLayer() in (pcbnew.F_Cu, pcbnew.B_Cu)
                   else pcbnew.F_Cu)
            done = False
            for r in rings:
                for ang in range(0, 360, astep):
                    vx = round(px + (w2 + r) * math.cos(math.radians(ang)), 2)
                    vy = round(py + (h2 + r) * math.sin(math.radians(ang)), 2)
                    if not ctx.try_via(net_obj, vx, vy):
                        continue
                    if ctx.tk.collides(px, py, vx, vy, stub_w,
                                       p.GetNetCode(), lay) is not None:
                        continue
                    ctx.tk.add_seg(px, py, vx, vy, p.GetNet(), lay, stub_w)
                    # GAP B: this <stub_w> drop rides `netname`, whose trunk
                    # ampacity floor (e.g. 3.7mm) DRC would flag as track_width.
                    # Record its footprint so a named rule area can scope it.
                    hw = stub_w / 2.0 + 0.05
                    stub_boxes.append((min(px, vx) - hw, min(py, vy) - hw,
                                       max(px, vx) + hw, max(py, vy) + hw))
                    done = True
                    break
                if done:
                    break
            if done:
                ok += 1
            else:
                fails.append((fp.GetReference(), p))
    return ok, tot, fails


@stitch_pass("pad_rescue")
def p_pad_rescue(ctx, c):
    """Every SMD pad of a plane net needs a barrel to that plane. Serves EACH
    configured plane-net (GAP A), then scopes the thin plane-drop stubs out of
    the trunk ampacity floor with one named rule area (GAP B)."""
    targets = _rescue_targets(ctx, c)
    stub_boxes = []
    all_fails = []
    req = c.get("require", "none")
    for netname, plane_layer in targets:
        ok, tot, fails = _rescue_one_net(ctx, c, netname, plane_layer, stub_boxes)
        ctx.bump(f"pad_rescue_{netname}", ok)
        all_fails.extend(fails)
        into = f" -> {plane_layer}" if plane_layer else ""
        print(f"{netname} pad rescue{into}: {ok}/{tot} SMD pads served"
              + (f", {len(fails)} unserved" if fails else ""))
        if req == "all" and fails:
            ctx.failures.append(
                f"{netname} pad rescue: {len(fails)} unserved "
                f"({[f'{r}.{n}' for r, p in fails for n in [p.GetNumber()]][:8]})")
    ctx.pending = [(r, p.GetNumber()) for r, p in all_fails]
    _scope_stub_floor(ctx, c, stub_boxes)


def _scope_stub_floor(ctx, c, stub_boxes):
    """GAP B: keep plane-drop stubs legal WITHOUT lowering the trunk floor
    elsewhere. Emit one named rule area hugging each stub and append a
    `.kicad_dru` rule scoped to `insideArea('<name>')` with a relaxed
    min_track_width. KiCad resolves track_width by LAST MATCH, so a rule
    appended after the netclass floor overrides it only inside the area (the
    same named-rule-area sub-floor pattern cook-hub's `u7_taps` uses)."""
    scope = c.get("stub_scope")
    if scope is False or not stub_boxes:
        return
    scope = scope if isinstance(scope, dict) else {}
    name = scope.get("area_name", "pad_rescue_stubs")
    layers = scope.get("layers") or ["F.Cu", "B.Cu"]
    min_w = float(scope.get("min_track_width", c.get("stub_width", 0.3)))
    # NET-SCOPE the exemption to the rescued plane-nets. Without this the
    # insideArea rule relaxes the floor for ANY track crossing a stub box — so a
    # thin SIG track (0.25mm) passing through fails the 0.3mm stub floor it never
    # asked for (measured +2 on the clean-room 3S board, 2026-07-21). Only the
    # plane-drop net's own stub should be exempted.
    rescued = [n["net"] for n in (c.get("nets") or []) if isinstance(n, dict) and n.get("net")]
    if not rescued and c.get("net"):
        rescued = [c["net"]]
    _add_rule_area(ctx, name, stub_boxes, layers)
    _append_stub_dru(ctx, name, min_w, rescued)
    print(f"stub floor scoped: rule area {name!r} over {len(stub_boxes)} "
          f"plane-drop stub(s), track_width min {min_w}mm on {layers}"
          + (f", nets {rescued}" if rescued else ""))


def _add_rule_area(ctx, name, boxes, layer_names):
    """Permissive rule areas (forbid nothing) so the DRU can scope
    `insideArea('<name>')` tight around each plane-drop stub.

    ONE ZONE PER BOX, all sharing `name`: KiCad serialises a zone with a
    single outline (a multi-outline SHAPE_POLY_SET collapses to its last
    outline on save — verified on 10.0.x), but `insideArea('<name>')` matches
    a track inside ANY zone carrying that name, so N tight boxes give N
    disjoint exemptions without one big rect exempting the trunk between them.
    Each zone spans all its layers via an LSET (generate_board_generic pattern:
    SetLayer collapses the set, so it must precede SetLayerSet)."""
    pcbnew = ctx.pcbnew
    lids = [_layer_id(pcbnew, n) for n in layer_names]
    for x0, y0, x1, y1 in boxes:
        z = pcbnew.ZONE(ctx.board)
        z.SetIsRuleArea(True)
        z.SetZoneName(name)
        ls = pcbnew.LSET()
        add = getattr(ls, "AddLayer", None) or getattr(ls, "addLayer")
        for lid in lids:
            add(lid)
        z.SetLayer(lids[0])
        z.SetLayerSet(ls)
        z.SetDoNotAllowTracks(False)
        z.SetDoNotAllowVias(False)
        z.SetDoNotAllowPads(False)
        z.Outline().NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            z.Outline().Append(pcbnew.VECTOR2I_MM(round(x, 3), round(y, 3)))
        ctx.board.Add(z)


def _append_stub_dru(ctx, name, min_w, nets=None):
    """Append the scoped sub-floor to the board's ride-along `.kicad_dru`
    (idempotent). Last in the file == last match == overrides the trunk floor
    inside the area only. pcbnew.Save() never touches `.kicad_dru`, so this
    survives the stitch save; the caller's generate_rules-LAST, if it rewrites
    the dru, must preserve/re-emit this rule (documented in the config).

    `nets` net-scopes the exemption so ONLY the plane-drop net's own stub is
    relaxed — a SIG track crossing the box keeps its own floor."""
    dru = ctx.path.with_suffix(".kicad_dru")
    cond = f"A.insideArea('{name}')"
    if nets:
        clause = " || ".join(f"A.NetName == '{n}'" for n in nets)
        cond = f"{cond} && ({clause})"
    rule = (f"(rule {name}\n"
            f"  (condition \"{cond}\")\n"
            f"  (constraint track_width (min {min_w:.3f}mm)))\n")
    if dru.is_file():
        txt = dru.read_text()
        if f"(rule {name}\n" in txt:
            return
        sep = "" if txt.endswith("\n") else "\n"
        dru.write_text(txt + sep + rule)
    else:
        dru.write_text("(version 1)\n" + rule)


@stitch_pass("stub_fallback")
def p_stub_fallback(ctx, c):
    """Boxed-in pads: short stub to the nearest same-net copper (a via barrel
    is a pour link; a track end is a direct join)."""
    pcbnew = ctx.pcbnew
    netname = c.get("net", "GND")
    code = ctx.net(netname).GetNetCode()
    lo, hi = float(c.get("min_dist", 0.2)), float(c.get("max_dist", 8.0))
    w = float(c.get("width", 0.3))
    pts = []
    for t in ctx.board.GetTracks():
        if t.GetNetCode() != code:
            continue
        if t.GetClass() == "PCB_VIA":
            pts.append((t.GetPosition().x / 1e6, t.GetPosition().y / 1e6, None))
        else:
            for e in (t.GetStart(), t.GetEnd()):
                pts.append((e.x / 1e6, e.y / 1e6, t.GetLayer()))
    still, fixed = [], 0
    for ref, p in ctx.pads(ctx.pending):
        px, py = p.GetPosition().x / 1e6, p.GetPosition().y / 1e6
        lay = (p.GetLayer() if p.GetLayer() in (pcbnew.F_Cu, pcbnew.B_Cu)
               else pcbnew.F_Cu)
        cands = sorted(((math.hypot(px - x, py - y), x, y, tl)
                        for (x, y, tl) in pts if tl is None or tl == lay),
                       key=lambda t: t[0])
        done = False
        for d, tx, ty, _tl in cands:
            if not (lo < d < hi):
                continue
            if ctx.tk.collides(px, py, round(tx, 2), round(ty, 2), w,
                               code, lay) is not None:
                continue
            ctx.tk.add_seg(px, py, round(tx, 2), round(ty, 2), p.GetNet(), lay, w)
            done = True
            break
        if done:
            fixed += 1
            print(f"  stub recovered {ref}.{p.GetNumber()}")
        else:
            still.append((ref, p.GetNumber()))
    ctx.pending = still
    ctx.bump("stub_fallback", fixed)
    print(f"stub fallback: recovered {fixed}, {len(still)} left")


@stitch_pass("astar_fallback")
def p_astar(ctx, c):
    netname = c.get("net", "GND")
    code = ctx.net(netname).GetNetCode()
    w = float(c.get("width", 0.25))
    window = float(c.get("window", 3.0))
    attempts = int(c.get("attempts", 3))
    targets = [(t.GetPosition().x / 1e6, t.GetPosition().y / 1e6)
               for t in ctx.board.GetTracks()
               if t.GetClass() == "PCB_VIA" and t.GetNetCode() == code]

    # The toolkit's A* emits its own default 0.45/0.2 vias, which are BELOW
    # a 2-layer standard-tier board's floors (crow-array-pod: 2x
    # drill_out_of_range + 1x hole_to_hole from one rescue). Pinning the
    # geometry is what the bespoke stitcher monkeypatched by hand; here it
    # is config. `restore` is unconditional so an exception cannot leak the
    # patched toolkit into later passes.
    pin = c.get("via")
    _orig = (ctx.tk.add_via, ctx.tk.via_site_ok)
    if pin:
        vs, vd = float(pin["size"]), float(pin["drill"])
        ctx.tk.add_via = (lambda x, y, net, size=None, drill=None, _f=_orig[0]:
                          _f(x, y, net, size=vs, drill=vd))
        ctx.tk.via_site_ok = (lambda x, y, nc, size=None, drill=None,
                              _f=_orig[1], **kw:
                              _f(x, y, nc, size=vs, drill=vd, **kw))
    still, fixed = [], 0
    try:
        for ref, p in ctx.pads(ctx.pending):
            px, py = p.GetPosition().x / 1e6, p.GetPosition().y / 1e6
            tgt = None
            for tx, ty in sorted(targets,
                                 key=lambda q: math.hypot(px - q[0], py - q[1])):
                if 0.3 < math.hypot(px - tx, py - ty) < float(c.get("max_dist", 10.0)):
                    tgt = (tx, ty)
                    break
            if tgt and ctx.tk.verified_astar(netname, (px, py), tgt, w,
                                             window=window, attempts=attempts):
                fixed += 1
                print(f"  A* recovered {ref}.{p.GetNumber()}")
            else:
                still.append((ref, p.GetNumber()))
    finally:
        ctx.tk.add_via, ctx.tk.via_site_ok = _orig
        ctx._used = None
    ctx.pending = still
    ctx.bump("astar_fallback", fixed)
    print(f"A* fallback: recovered {fixed}, {len(still)} left")


def _in_poly(x, y, poly):
    inside = False
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def _plane_polys(ctx, layer_name):
    pcbnew = ctx.pcbnew
    lay = _layer_id(pcbnew, layer_name)
    out = {}
    for z in ctx.board.Zones():
        if z.GetIsRuleArea() or not z.GetNetname():
            continue
        if not z.GetLayerSet().Contains(lay):
            continue
        o = z.Outline().COutline(0)
        out.setdefault(z.GetNetname(), []).append(
            [(o.CPoint(i).x / 1e6, o.CPoint(i).y / 1e6)
             for i in range(o.PointCount())])
    return out


@stitch_pass("power_stitch")
def p_power_stitch(ctx, c):
    """Pour-fed power nets: drop a via wherever the net's routed copper
    crosses its own plane island. A power via only helps OVER its island."""
    planes = _plane_polys(ctx, c.get("plane_layer", "In2.Cu"))
    for job in c.get("jobs", []) or []:
        netname, need = job["net"], int(job.get("min", 1))
        net = ctx.net(netname)
        polys = planes.get(netname, [])
        got = 0
        pts = []
        for t in ctx.board.GetTracks():
            if t.GetClass() == "PCB_TRACK" and t.GetNetname() == netname:
                for e in (t.GetStart(), t.GetEnd()):
                    pts.append((round(e.x / 1e6, 2), round(e.y / 1e6, 2)))
        for x, y in pts:
            if got >= need + int(c.get("overshoot", 2)):
                break
            if any(_in_poly(x, y, pp) for pp in polys) and ctx.try_via(net, x, y):
                got += 1
        for site in job.get("sites", []) or []:
            if ctx.try_via(net, float(site[0]), float(site[1])):
                got += 1
        ctx.bump(f"power_stitch_{netname}", got)
        print(f"{netname}: {got} stitch vias (need {need})")
        if got < need:
            ctx.failures.append(f"power stitch {netname}: {got} < {need}")


@stitch_pass("via_janitor")
def p_janitor(ctx, c):
    """A via with same-net copper on fewer than 2 layers connects nothing and
    is a fab-cost hole plus a DRC dangling item."""
    pcbnew = ctx.pcbnew
    minlay = int(c.get("min_layers", 2))
    pad_win = float(c.get("pad_window", 2.0))

    def seg_d2(px, py, ax, ay, bx, by):
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
        return (px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2

    ztmp = {}
    for z in ctx.board.Zones():
        if z.GetNetname() and not z.GetIsRuleArea():
            o = z.Outline().COutline(0)
            poly = [(o.CPoint(i).x / 1e6, o.CPoint(i).y / 1e6)
                    for i in range(o.PointCount())]
            for lay in z.GetLayerSet().Seq():
                ztmp.setdefault((z.GetNetname(), lay), []).append(poly)

    orphans = []
    for v in [t for t in ctx.board.GetTracks() if t.GetClass() == "PCB_VIA"]:
        nn = v.GetNetname()
        vx, vy = v.GetPosition().x / 1e6, v.GetPosition().y / 1e6
        r2 = (v.GetWidth() / 2e6) ** 2
        attach = set()
        for t in ctx.board.GetTracks():
            if t.GetClass() == "PCB_VIA" or t.GetNetCode() != v.GetNetCode():
                continue
            if seg_d2(vx, vy, t.GetStart().x / 1e6, t.GetStart().y / 1e6,
                      t.GetEnd().x / 1e6, t.GetEnd().y / 1e6) <= r2:
                attach.add(t.GetLayer())
        for fp in ctx.board.GetFootprints():
            for p in fp.Pads():
                if p.GetNetCode() != v.GetNetCode():
                    continue
                pp = p.GetPosition()
                if (abs(pp.x / 1e6 - vx) > pad_win
                        or abs(pp.y / 1e6 - vy) > pad_win):
                    continue
                bb = p.GetBoundingBox()
                bb.Inflate(v.GetWidth() // 2)
                if bb.Contains(v.GetPosition()):
                    for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
                        if p.IsOnLayer(lay):
                            attach.add(lay)
        for (znet, zlay), polys in ztmp.items():
            if znet == nn and any(_in_poly(vx, vy, poly) for poly in polys):
                attach.add(zlay)
        if len(attach) < minlay:
            orphans.append(v)
    for v in orphans:
        ctx.remove(v)
    ctx._used = None
    ctx.bump("janitor_removed", len(orphans))
    print(f"via janitor removed {len(orphans)} single-layer vias")


@stitch_pass("fill")
def p_fill(ctx, c):
    filler = ctx.pcbnew.ZONE_FILLER(ctx.board)
    filler.Fill(ctx.board.Zones())
    print(f"filled {len(list(ctx.board.Zones()))} zones")


@stitch_pass("island_rescue")
def p_island(ctx, c):
    """After fill, a pour can be sliced into islands by crossing traces. An
    island holding a pad and no via of its net is a DISCONNECTED pad that
    only shows up as an unconnected item — stitch it or fail loudly."""
    pcbnew = ctx.pcbnew
    min_bb = float(c.get("min_bbox", 0.8))
    layers = [_layer_id(pcbnew, n)
              for n in c.get("layers", ["F.Cu", "B.Cu", "In2.Cu"])]
    via_by_net = {}
    for t in ctx.board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            via_by_net.setdefault(t.GetNetname(), []).append(t.GetPosition())
    added = 0
    for z in ctx.board.Zones():
        nn = z.GetNetname()
        if not nn or z.GetIsRuleArea():
            continue
        for lay in z.GetLayerSet().Seq():
            if lay not in layers:
                continue
            polys = z.GetFilledPolysList(lay)
            for i in range(polys.OutlineCount()):
                o = polys.Outline(i)
                bb = o.BBox()
                if bb.GetWidth() < min_bb * 1e6 or bb.GetHeight() < min_bb * 1e6:
                    continue
                if any(o.PointInside(p) for p in via_by_net.get(nn, [])):
                    continue
                # BARREL CREDIT: a drilled same-net pad inside the island is
                # already bonded through its own plated barrel. (crow-array-pod)
                if any(o.PointInside(p2.GetPosition())
                       for fp2 in ctx.board.GetFootprints() for p2 in fp2.Pads()
                       if p2.GetNetname() == nn and p2.GetDrillSize().x > 0):
                    continue
                # TRACK CREDIT: a same-net segment with one end inside the
                # island and the other outside feeds it directly — an A*
                # rescue lands exactly here and leaves no via to find.
                if any(o.PointInside(t.GetStart()) != o.PointInside(t.GetEnd())
                       for t in ctx.board.GetTracks()
                       if t.GetClass() == "PCB_TRACK" and t.GetNetname() == nn
                       and t.GetLayer() == lay):
                    continue
                has_pad = any(o.PointInside(p2.GetPosition())
                              for fp2 in ctx.board.GetFootprints()
                              for p2 in fp2.Pads() if p2.GetNetname() == nn)
                placed = False
                for fx in range(2, 19, 2):
                    for fy in range(2, 19, 2):
                        x = bb.GetLeft() + bb.GetWidth() * fx // 20
                        y = bb.GetTop() + bb.GetHeight() * fy // 20
                        if not o.PointInside(pcbnew.VECTOR2I(x, y)):
                            continue
                        if ctx.try_via(ctx.net(nn), x / 1e6, y / 1e6):
                            via_by_net.setdefault(nn, []).append(
                                pcbnew.VECTOR2I(x, y))
                            added += 1
                            placed = True
                            break
                    if placed:
                        break
                # `require: pads` fails only on pad-bearing islands (the
                # classic disconnected-pad case). `require: all` fails on
                # ANY unstitchable island, because KiCad reports an
                # island-to-island gap in the same zone as an unconnected
                # item even when neither island holds a pad — and a 0/0/0
                # gate counts it (crow-array-pod, 2026-07-20).
                if not placed and (has_pad or c.get("require") == "all"):
                    ctx.failures.append(
                        f"island {nn}/{pcbnew.BOARD.GetStandardLayerName(lay)} "
                        f"({bb.GetLeft()/1e6:.1f},{bb.GetTop()/1e6:.1f}) "
                        f"{bb.GetWidth()/1e6:.1f}x{bb.GetHeight()/1e6:.1f}mm "
                        f"cannot be stitched"
                        + (" (holds a pad)" if has_pad else ""))
    ctx.bump("island_vias", added)
    print(f"island stitch vias: {added}")


@stitch_pass("gate")
def p_gate(ctx, c):
    """Flush accumulated failures. Boards gate once (before the final fill)
    or twice (usb-power-3s) — hence a pass rather than an epilogue."""
    if ctx.failures:
        print("FAILURES:\n  " + "\n  ".join(ctx.failures))
        ctx.board.Save(str(ctx.path) + ".failed")
        if ctx.state_path().is_file():
            ctx.state_path().unlink()   # never resume a dead run
        sys.exit(1)
    print("gate: clean")


DEFAULT_PASSES = ["dedupe_vias", "drop_micro_fragments", "reload",
                  "pad_rescue", "stitch_grid", "via_janitor", "fill",
                  "island_rescue", "gate"]


# stitch.via and friends spell the geometry size/drill, not via_size/via_drill
_VIA_KEYMAP = {"via_size": "size", "via_drill": "drill", "clearance": None}


def _stitch_tier_geometry(cfg):
    """Tier floors for every via geometry the stitcher can EMIT. Missing
    stitch.via size/drill (and a missing astar_fallback via pin — the
    toolkit's 0.45/0.2 A* default was below crow-array-pod's own floors)
    derive from the declared tier; explicit sub-floor values are errors."""
    tier = fab_tier(cfg)
    if tier is None:
        return
    v = cfg.setdefault("stitch", {}).setdefault("via", {})
    tier_geometry(v, tier, "stitch.via", keymap=_VIA_KEYMAP)
    for i, t in enumerate(v.get("tiers") or []):
        tier_geometry(t, tier, f"stitch.via.tiers[{i}]", derive=False,
                      keymap=_VIA_KEYMAP)
    for blk, derive in (("normalize_vias", False), ("hole_to_hole.shrink_to",
                                                    False)):
        d = get(cfg, f"stitch.{blk}")
        if isinstance(d, dict):
            tier_geometry(d, tier, f"stitch.{blk}", derive=derive,
                          keymap=_VIA_KEYMAP)
    av = get(cfg, "stitch.astar_fallback")
    if isinstance(av, dict):
        tier_geometry(av.setdefault("via", {}), tier,
                      "stitch.astar_fallback.via", keymap=_VIA_KEYMAP)


def cmd_stitch(cfg):
    global MM
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import pcbnew
    MM = pcbnew.ToMM
    _stitch_tier_geometry(cfg)     # tier floors BEFORE any via is emitted
    target = rel(cfg, cfg["project"]["board"])
    ctx = Ctx(cfg, target)
    order = get(cfg, "stitch.passes", DEFAULT_PASSES)
    unknown = [p for p in order if p not in PASSES]
    if unknown:
        die(f"unknown stitch pass(es) {unknown} — known: {sorted(PASSES)}")
    if "fill" not in order:
        die("stitch.passes has no 'fill' — an unfilled board's DRC is a lie")
    if order[-1] != "gate":
        order = list(order) + ["gate"]

    def barrier(next_i, why):
        ctx.board.Save(str(ctx.path))
        ctx.save_state(next_i)
        print(f"   SWIG barrier ({why}): saved, re-execing into a fresh "
              f"interpreter at pass {next_i}/{len(order)}")
        sys.stdout.flush()
        os.execv(sys.executable,
                 [sys.executable, os.path.abspath(__file__), "stitch",
                  str(cfg["_path"]), "--root", str(cfg["_root"])])

    start = ctx.load_state()
    for i in range(start, len(order)):
        name = order[i]
        if name == "reload":
            print("\n-- reload --")
            if ctx.dirty:
                barrier(i + 1, "explicit")
            print("   nothing removed since the last barrier — no-op")
            continue
        cfgblk = get(cfg, f"stitch.{name}", {}) or {}
        print(f"\n-- {name} --")
        PASSES[name](ctx, cfgblk)
        # An IMPLICIT barrier after any pass that removed something. Without
        # it the NEXT pass's GetTracks() raises on a poisoned SWIG iterator,
        # and (worse) the removals stay half-applied on a saved board.
        if ctx.dirty and i + 1 < len(order):
            barrier(i + 1, f"after {name}")
    ctx.board.Save(str(ctx.path))
    if ctx.state_path().is_file():
        ctx.state_path().unlink()
    print(f"\nsaved {ctx.path}")
    print("NEXT: run your rules generator LAST — this save did not touch "
          ".kicad_pro, but any pcbnew save in the chain clobbers netclasses.")
    return 0


# =============================================================== MAIN ====
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("command", choices=["prep", "route", "import", "stitch", "all"])
    ap.add_argument("config")
    ap.add_argument("--root", default=None,
                    help="project root (default: the config's grandparent dir)")
    a = ap.parse_args(argv)
    cfg = load_cfg(a.config, a.root)
    try:
        if a.command == "prep":
            return cmd_prep(cfg)
        if a.command == "route":
            return cmd_route(cfg)
        if a.command == "import":
            return cmd_import(cfg)
        if a.command == "stitch":
            return cmd_stitch(cfg)
        for fn in (cmd_prep, cmd_route, cmd_import, cmd_stitch):
            rc = fn(cfg)
            if rc:
                return rc
        return 0
    except RouteConfigError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
