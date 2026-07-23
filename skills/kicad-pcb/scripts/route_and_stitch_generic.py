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
      -> taps (optional): collision-checked NAMED connections KRT cannot
         thread — pour-fed sense pins, boxed-in pads, plane drops
      -> stitch: clean KRT artifacts -> rescue pads -> stitch grid
                 -> janitor -> FILL -> island rescue -> heal islands -> gate
      -> generate_rules LAST (pcbnew saves clobber .kicad_pro netclasses)

    /usr/bin/python3 route_and_stitch_generic.py prep    03_src/route.yaml
    <KRT venv python>  route_and_stitch_generic.py route 03_src/route.yaml
    /usr/bin/python3 route_and_stitch_generic.py import  03_src/route.yaml
    /usr/bin/python3 route_and_stitch_generic.py quick   03_src/route.yaml
    /usr/bin/python3 route_and_stitch_generic.py stitch  03_src/route.yaml
    /usr/bin/python3 route_and_stitch_generic.py all     03_src/route.yaml

`prep`, `import`, `quick` and `stitch` need the KiCad-bundled interpreter
(`/usr/bin/python3`, the one with `pcbnew`). `route` only shells out to KRT
and runs on any python.

`quick` is the LOOP CHEAPENER: seconds-fast unconnected + copper
clearance/track_width verdict on the post-import pre-stitch board (no
fill, no zone classes), so a routing iteration is measured without paying
the full rebuild + DRC cycle. Full DRC after stitch stays the release gate.

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
  * a wave whose EXPLICIT track_width is below a member net's netclass
    floor (nets.yaml classes) — a missing width DERIVES from the largest
    member floor instead, so a wave cannot ride under its class
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
  route:    krt, python, race (N concurrent chains, quick-measured best
            wins; CLI --race overrides), kicad_python (race import+quick
            interpreter), common{...}, waves[] {name, nets|group, + any
            KRT flag override}
  taps:     clearance, via{}, connections[] {net, from, to, width,
            layer/hop_layer, plane} — see cmd_taps
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


# ------------------------------------------------- netclass width floors
def net_class_floors(cfg):
    """{net: (class_name, min_width_mm)} from the project's
    03_src/rules/nets.yaml `classes` — the SAME source generate_rules_generic
    emits the .kicad_dru width floors from, so the router and the DRC gate
    cannot disagree (the v4 board's 157 track_width findings were exactly
    that disagreement: waves routed at widths the netclass floors reject).
    Cached on the cfg dict; empty when the project declares no classes."""
    if "_class_floors" not in cfg:
        floors = {}
        p = cfg["_root"] / "03_src" / "rules" / "nets.yaml"
        if p.is_file():
            d = yaml.safe_load(p.read_text()) or {}
            for cname, c in (d.get("classes") or {}).items():
                c = c or {}
                w = c.get("min_width")
                if w is None:
                    continue
                w = float(str(w).strip().lower().replace("mm", "").strip())
                for net in c.get("nets") or []:
                    floors[str(net)] = (cname, w)
        cfg["_class_floors"] = floors
    return cfg["_class_floors"]


def wave_track_width(cfg, wname, nets, explicit):
    """The track width a wave must route at, derived from its member nets'
    netclass floors. Returns the width to pass to KRT, or None (no floor and
    no explicit width — KRT's default is fine for classless nets).

    * missing width -> the LARGEST member floor (the minimum LEGAL width for
      the whole wave: any thinner and some member rides under its class).
    * an EXPLICIT width below a member net's class floor is a HARD ERROR
      naming the class — never a silent ride-under. The stitcher's
      width_floor pass could lift it post-route, but by then KRT has spent
      its clearance budget on a geometry the DRC gate will reject."""
    need = None                      # (floor, class, net) of the max floor
    for n in nets:
        f = net_class_floors(cfg).get(n)
        if f and (need is None or f[1] > need[0]):
            need = (f[1], f[0], n)
    if explicit is not None:
        if need and float(explicit) < need[0] - 1e-9:
            die(f"route wave {wname!r} track_width {explicit} is below "
                f"netclass {need[1]!r} min_width {need[0]} (member net "
                f"{need[2]!r}) — the wave would route the class under its "
                f"ampacity floor and every segment becomes a track_width "
                f"DRC finding (157 of them on the v4 usb-hub-3s board, "
                f"2026-07-21). Raise the wave width, or re-class the net")
        return float(explicit)
    return need[0] if need else None


def check_wave_widths(cfg, groups):
    """Validate every route.waves entry against the netclass floors, at PREP
    time — before any KRT cycle is spent. `groups` is wave_nets() output."""
    common_tw = get(cfg, "route.common.track_width")
    for i, wv in enumerate(get(cfg, "route.waves", []) or [], 1):
        name = wv.get("name", f"w{i}")
        nets = wv.get("nets")
        if nets is None:
            nets = groups.get(wv.get("group", name)) or []
        wave_track_width(cfg, name, list(nets),
                         wv.get("track_width", common_tw))


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
    # wave widths vs netclass floors, HERE — a sub-floor wave must fail
    # prep, not surface as a track_width batch after the KRT cycle is spent
    check_wave_widths(cfg, groups)
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
    "board_edge_clearance": ("--board-edge-clearance", "val"),
    "track_width": ("--track-width", "val"),
    "via_size": ("--via-size", "val"),
    "via_drill": ("--via-drill", "val"),
    "fab_tier": ("--fab-tier", "val"),
    "fab_overrides": ("--fab-overrides", "val"),
    "keepout_layer": ("--keepout-layer", "val"),
    "max_iterations": ("--max-iterations", "val"),
    "max_probe_iterations": ("--max-probe-iterations", "val"),
    "max_ripup": ("--max-ripup", "val"),
    "grid_step": ("--grid-step", "val"),
    "rip_existing_nets": ("--rip-existing-nets", "list"),
    "power_nets": ("--power-nets", "list"),
    "power_nets_widths": ("--power-nets-widths", "list"),
    "no_stub_layer_swap": ("--no-stub-layer-swap", "flag"),
    "no_power_tap_neckdown": ("--no-power-tap-neckdown", "flag"),
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


def _wave_chain(cfg, py, krt, waves, tier, common, workdir, cur, env=None,
                tag=""):
    """Run the chained KRT waves rN -> rN+1 inside `workdir`, starting from
    board `cur`. Returns the final chain file. `env` extends the subprocess
    environment (race candidates get ROUTE_RACE_CANDIDATE)."""
    sub_env = dict(os.environ, **(env or {}))
    for i, wv in enumerate(waves, 1):
        name = wv.get("name", f"w{i}")
        nets = wv.get("nets")
        if nets is None:
            grp = wv.get("group", name)
            f = workdir / f"nets_{grp}.txt"
            if not f.is_file():
                die(f"wave {name!r}: {f} missing — run `prep` first")
            nets = f.read_text().split()
        if not nets:
            print(f"{tag}wave {name}: 0 nets, skipped")
            continue
        nxt = workdir / f"r{i}.kicad_pcb"
        opts = dict(common)
        opts.update({k: v for k, v in wv.items()
                     if k not in ("name", "nets", "group")})
        tier_geometry(opts, tier, f"route.waves[{name}]", derive=False)
        # track width DERIVES from the wave's netclass floors when absent;
        # an explicit sub-floor width died at prep, and dies again here in
        # case route ran on a stale prep.
        tw = wave_track_width(cfg, name, list(nets), opts.get("track_width"))
        if tw is not None:
            opts["track_width"] = tw
        cmd = ([py, str(krt / "route.py"), str(cur), "--output", str(nxt)]
               + _krt_args(opts) + ["--nets"] + list(nets))
        print(f"\n=== {tag}wave {name}: {len(nets)} nets ===\n  "
              + " ".join(cmd[:2] + ["..."] + cmd[-min(6, len(nets) + 1):]))
        r = subprocess.run(cmd, env=sub_env)
        if r.returncode != 0:
            die(f"KRT wave {name!r} exited {r.returncode}")
        if not nxt.is_file():
            die(f"KRT wave {name!r} produced no {nxt}")
        cur = nxt
    return cur


def _race_candidate(cfg, py, krt, waves, tier, common, build, i, results):
    """One race lane: private copy of the prep outputs -> wave chain ->
    import into a copy of the track-free target -> quick numbers."""
    tag = f"[c{i}] "
    try:
        cdir = build / "race" / f"c{i}"
        if cdir.is_dir():
            shutil.rmtree(cdir)
        cdir.mkdir(parents=True)
        r0 = build / get(cfg, "prep.out", "r0.kicad_pcb")
        shutil.copy(r0, cdir / r0.name)
        for ext in (".kicad_pro", ".kicad_dru"):
            if r0.with_suffix(ext).is_file():
                shutil.copy(r0.with_suffix(ext), cdir / (r0.stem + ext))
        for f in build.glob("nets_*.txt"):
            shutil.copy(f, cdir / f.name)
        chain = _wave_chain(cfg, py, krt, waves, tier, dict(common), cdir,
                            cdir / r0.name,
                            env={"ROUTE_RACE_CANDIDATE": str(i)}, tag=tag)
        # evaluate: import into a COPY of the track-free target, then quick.
        # Needs pcbnew, so both steps shell out to the KiCad interpreter —
        # cmd_route itself stays runnable on the KRT venv python.
        kpy = get(cfg, "route.kicad_python", "/usr/bin/python3")
        target = rel(cfg, cfg["project"]["board"])
        ev = cdir / "eval.kicad_pcb"
        shutil.copy(target, ev)
        for ext in (".kicad_pro", ".kicad_dru"):
            if target.with_suffix(ext).is_file():
                shutil.copy(target.with_suffix(ext),
                            ev.with_suffix(ext))
        imp = Path(__file__).resolve().parent / "import_krt.py"
        r = subprocess.run([kpy, str(imp), str(chain), str(ev), str(ev)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            die(f"candidate {i}: import_krt exited {r.returncode}: "
                f"{(r.stderr or r.stdout)[-300:]}")
        qj = cdir / "quick.json"
        r = subprocess.run([kpy, os.path.abspath(__file__), "quick",
                            str(cfg["_path"]), "--root", str(cfg["_root"]),
                            "--board", str(ev), "--json", str(qj)],
                           capture_output=True, text=True)
        if not qj.is_file():
            die(f"candidate {i}: quick wrote no JSON (exit {r.returncode}): "
                f"{(r.stderr or r.stdout)[-300:]}")
        import json
        q = json.loads(qj.read_text())
        results[i] = {
            "chain": str(chain),
            "unconnected": q["unconnected"]["routed_total"],
            "violations": sum(e["count"]
                              for e in q.get("violations", {}).values()),
            "verdict": q["verdict"],
        }
    except Exception as e:                # noqa: BLE001 — lane-isolated
        results[i] = {"error": str(e)}


def cmd_route(cfg, race=None):
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

    n = int(race if race is not None else get(cfg, "route.race", 1) or 1)
    if n > 1:
        return _cmd_route_race(cfg, py, krt, waves, tier, common, build, n)

    cur = _wave_chain(cfg, py, krt, waves, tier, common, build, cur)
    print(f"\nwaves done -> {cur}")
    (build / "FINAL").write_text(str(cur) + "\n")
    return 0


def _cmd_route_race(cfg, py, krt, waves, tier, common, build, n):
    """KRT is stochastic: two routes of the same board differ measurably
    (223 vs 234 segments on cook-loadcell, both DRC-clean — and on dense
    boards the unconnected tail differs too). `race: N` buys N concurrent
    attempts and keeps the MEASURED best: fewest routed-net unconnected,
    tie-broken by fewest copper violations, then lowest index (quick is
    the ruler). The per-candidate numbers land in the route log
    (race_log.json) so the choice is auditable, never vibes."""
    import json
    import threading
    print(f"race: {n} candidate wave-chains, concurrent")
    results = {}
    threads = [threading.Thread(target=_race_candidate,
                                args=(cfg, py, krt, waves, tier, common,
                                      build, i, results))
               for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    ok = {i: r for i, r in results.items() if "error" not in r}
    for i in sorted(results):
        r = results[i]
        if "error" in r:
            print(f"  c{i}: FAILED — {r['error'][:160]}")
        else:
            print(f"  c{i}: unconnected={r['unconnected']} "
                  f"violations={r['violations']} ({r['verdict']})")
    if not ok:
        die(f"all {n} race candidates failed: "
            + "; ".join(f"c{i}: {r['error'][:80]}"
                        for i, r in sorted(results.items())))
    best = min(ok, key=lambda i: (ok[i]["unconnected"],
                                  ok[i]["violations"], i))
    log = {"candidates": {str(i): results[i] for i in sorted(results)},
           "chosen": best,
           "rule": "min routed-net unconnected, then min copper violations,"
                   " then lowest index"}
    (build / "race_log.json").write_text(json.dumps(log, indent=1) + "\n")
    chain = Path(ok[best]["chain"])
    print(f"race winner: c{best} ({ok[best]['unconnected']} unconnected, "
          f"{ok[best]['violations']} violations) -> {chain}")
    print(f"race log -> {build / 'race_log.json'}")
    (build / "FINAL").write_text(str(chain) + "\n")
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


# ============================================================== TAPS =====
# Offsets searched for a clear via landing near a tap endpoint (mm) — the
# proven search pattern from the clean-room 3S route_taps.py, board-free.
TAP_OFFS = [(0, 0)] \
    + [(0, s * d) for d in (0.8, 1.0, 1.3) for s in (-1, 1)] \
    + [(s * d, 0) for d in (0.8, 1.0, 1.3) for s in (-1, 1)] \
    + [(sx * d, sy * d) for d in (0.8, 1.1) for sx in (-1, 1) for sy in (-1, 1)]


def _tap_point(board, spec, netname, what):
    """A tap endpoint: 'REF.PAD' -> that pad's centre (its net must MATCH the
    tap's net — a mismatched ref is a config typo that would otherwise emit a
    short), or [x, y] -> a bare point (e.g. inside the target plane)."""
    if isinstance(spec, (list, tuple)) and len(spec) == 2:
        return (float(spec[0]), float(spec[1]))
    if isinstance(spec, str) and "." in spec:
        ref, num = spec.split(".", 1)
        fp = board.FindFootprintByReference(ref)
        if fp is None:
            die(f"{what}: no footprint {ref!r} on the board")
        for p in fp.Pads():
            if p.GetNumber() == num:
                if p.GetNetname() != netname:
                    die(f"{what}: pad {spec} is on net {p.GetNetname()!r}, "
                        f"not {netname!r} — a tap must never bridge nets")
                pos = p.GetPosition()
                return (pos.x / 1e6, pos.y / 1e6)
        die(f"{what}: footprint {ref} has no pad {num!r}")
    die(f"{what}: endpoint must be 'REF.PAD' or [x, y], got {spec!r}")


def _tap_via_near(tk, p, nc, stub_w, layer, vs, vd):
    """A collision-checked via site near p, reachable from p by a clear stub
    on `layer` (the escape-from-a-dense-pin-row move)."""
    for dx, dy in TAP_OFFS:
        v = (round(p[0] + dx, 3), round(p[1] + dy, 3))
        if not tk.via_site_ok(v[0], v[1], nc, size=vs, drill=vd):
            continue
        if (dx == 0 and dy == 0) or \
                tk.collides(p[0], p[1], v[0], v[1], stub_w, nc, layer) is None:
            return v
    return None


def _route_one_tap(pcbnew, tk, t, i, vs, vd):
    """One tap, cheapest strategy first; every emitted segment/via is
    verified against the live board's exact copper (pcb_toolkit collides /
    via_site_ok / joinpath). Returns how it routed, or None."""
    netname = t.get("net") or die(f"taps.connections[{i}]: no `net`")
    nobj = tk.board.FindNet(netname)
    if nobj is None or nobj.GetNetCode() <= 0:
        die(f"taps.connections[{i}]: board has no net {netname!r}")
    nc = nobj.GetNetCode()
    w = float(t.get("width", 0.3))
    lay = _layer_id(pcbnew, t.get("layer", "F.Cu"))
    hop = _layer_id(pcbnew, t.get("hop_layer", "B.Cu"))
    what = f"taps.connections[{i}] ({netname})"
    p1 = _tap_point(tk.board, t.get("from"), netname, what + " from")
    p2 = _tap_point(tk.board, t.get("to"), netname, what + " to")

    if t.get("plane"):
        # plane tap: stub -> via near `from` -> hop-layer join -> via AT `to`
        # (a point where the net's inner plane exists, so the fill merges it)
        v1 = _tap_via_near(tk, p1, nc, w, lay, vs, vd)
        if not v1 or not tk.via_site_ok(p2[0], p2[1], nc, size=vs, drill=vd):
            return None
        if tk.joinpath(netname, v1, p2, w, layer=hop) is None:
            return None
        if p1 != v1:
            tk.add_seg(*p1, *v1, nobj, lay, w)
        tk.add_via(*v1, nobj, size=vs, drill=vd)
        tk.add_via(*p2, nobj, size=vs, drill=vd)
        return "plane_tap"

    if t.get("escape"):
        # BOXED FINE-PITCH PIN escape (design-policies R-ESC-LAYER). A pin whose
        # net-target sits across a congested F.Cu channel escapes by LAYER, not
        # by placement: a via-in-pad at the pad (advanced-tier via_in_pad) drops
        # the net to the hop layer UNDER the channel, then a wide-window coarse-
        # grid 2-layer A* reaches a point inside the net's (as-yet-unfilled)
        # pour; `stitch` fills and bonds it. Placement/channel-widening does NOT
        # rescue this: measured on usb-hub-3s-v2 TPS25740A, a 2.5mm part shift
        # moved the haul only 7.0->6.2mm because the channel y-gap dominates and
        # cannot shrink (the gate nets need it). `to` is a point inside the pour.
        if not tk.via_site_ok(p1[0], p1[1], nc, size=vs, drill=vd):
            print(f"       {what}: via-in-pad site blocked at {p1}")
            return None
        if tk.verified_astar(netname, p1, p2, w,
                             grid=float(t.get("escape_grid", 0.25)),
                             window=float(t.get("escape_window", 4.0)),
                             viacost=int(t.get("escape_viacost", 8)),
                             attempts=int(t.get("escape_attempts", 14))):
            return "escape"
        return None

    # strategy 1: same-layer join (direct / L / Z scan), no vias
    if tk.joinpath(netname, p1, p2, w, layer=lay) is not None:
        return "joinpath"
    # strategy 2: via hop — stub -> via -> hop-layer join -> via -> stub
    v1 = _tap_via_near(tk, p1, nc, w, lay, vs, vd)
    v2 = _tap_via_near(tk, p2, nc, w, lay, vs, vd)
    if v1 and v2 and tk.joinpath(netname, v1, v2, w, layer=hop) is not None:
        if p1 != v1:
            tk.add_seg(*p1, *v1, nobj, lay, w)
        tk.add_via(*v1, nobj, size=vs, drill=vd)
        tk.add_via(*v2, nobj, size=vs, drill=vd)
        if p2 != v2:
            tk.add_seg(*v2, *p2, nobj, lay, w)
        return "via_hop"
    return None


def cmd_taps(cfg):
    """Collision-checked tap connections KRT cannot thread (pour-fed sense
    pins, boxed-in connector pads, plane drops) — the bespoke tail every
    dense power board wrote by hand (usb-pwr-hub-3s route_taps.py was the
    second strike after cook-hub; canon M8 promotes it to config). Runs
    AFTER `import`, BEFORE `stitch`, so pours fill around the tap copper.

      taps:
        clearance: 0.15
        via: {size: 0.6, drill: 0.3}   # tier-derived when omitted
        connections:
          - {net: VCC,  from: U1.4,  to: C8.1,        width: 0.3}
          - {net: CC1,  from: J5.A5, to: R10.2,       width: 0.25,
             layer: F.Cu, hop_layer: B.Cu}
          - {net: 5V,   from: R6.1,  to: [41.0, 46.5], width: 0.3,
             plane: true}    # `to` = a point inside the net's plane
    """
    import pcbnew
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from pcb_toolkit import Toolkit
    taps = get(cfg, "taps.connections") or []
    if not taps:
        print("taps: none configured")
        return 0
    via = dict(get(cfg, "taps.via", {}) or {})
    tier_geometry(via, fab_tier(cfg), "taps.via", keymap=_VIA_KEYMAP)
    vs, vd = float(via.get("size", 0.6)), float(via.get("drill", 0.3))
    target = rel(cfg, cfg["project"]["board"])
    clr = float(get(cfg, "taps.clearance", 0.15))
    bref = pcbnew.LoadBoard(str(target))   # read-only, for endpoint geometry

    def route_all(order, tag=""):
        """Route the whole tap set in `order` on a FRESH copy of the target
        board (the original is untouched on disk until the final save), so a
        reattempt is a clean re-route in a new ORDER — not a partial retry
        that keeps an earlier tap's blocking copper. Returns (board, failed
        indices)."""
        bb = pcbnew.LoadBoard(str(target))
        tkk = Toolkit(bb, clr)
        failed = []
        for idx in order:
            t = taps[idx]
            how = _route_one_tap(pcbnew, tkk, t, idx, vs, vd)
            print(f"  {tag}tap {t.get('net', '?'):8} {t.get('from')} -> "
                  f"{t.get('to')}  w={t.get('width', 0.3)}  "
                  f"{'OK ' + how if how else 'FAIL'}")
            if not how:
                failed.append(idx)
        return bb, failed

    # BOUNDED tap reattempt (canon M8 — the v1.1 U1 pour-pin tap failures
    # recurred: KRT hugs the escape-field lane edges, so a long pour-net pin
    # tap's corridor is ORDER-fragile). On a failure, re-route the whole set
    # LONGEST-first (seed-stubs-first / most-constrained-first ordering: the
    # long runs claim their corridor before shorter taps box them in), on a
    # fresh board. BOUNDED and PROGRESS-GATED — a retry that does not beat the
    # best failure count stops immediately, so the loop cannot spin: at most
    # max_retries retries, then escalate (the D-BACK discipline).
    max_retries = int(get(cfg, "taps.reattempt.max_retries", 2))
    order = list(range(len(taps)))
    board, failed = route_all(order)
    best_board, best_fail = board, failed
    retries = 0
    while best_fail and retries < max_retries:
        retries += 1
        # most-constrained-first: longest span first (deterministic, stable)
        order = sorted(range(len(taps)),
                       key=lambda i: _tap_len(bref, taps[i]), reverse=True)
        print(f"  tap reattempt {retries}/{max_retries}: "
              f"{len(best_fail)} failing — full re-route, longest-first")
        board, failed = route_all(order, tag="[re] ")
        if len(failed) < len(best_fail):
            best_board, best_fail = board, failed
        else:                        # no progress -> further retries can't help
            print(f"  tap reattempt {retries}: no progress "
                  f"({len(failed)} still failing) — escalating not spinning")
            break
    if best_fail:
        fl = [(taps[i].get("net"), taps[i].get("from"), taps[i].get("to"))
              for i in best_fail]
        die(f"unrouted taps after {retries} bounded reattempt(s): {fl} — a "
            f"tap is a NAMED connection; leaving it to the pour/stitch "
            f"lottery ships an open (the pad shows up only as a DRC "
            f"unconnected item after fill). Reattempt is bounded "
            f"(max_retries={max_retries}); a tap still stuck here is "
            f"structurally fragile (a long pour-net pin run) — promote it to "
            f"a deterministic stitch.seed_stubs, or fix placement (D-ADJ)")
    best_board.Save(str(target))
    print(f"taps: {len(taps)} routed"
          + (f" ({retries} reattempt(s))" if retries else "")
          + f" -> {target.name}")
    return 0


def _tap_len(board, t):
    """Straight-line span of a tap (mm) — the reattempt orders the longest
    (most-constrained) pour-net pin runs first. Resolves 'REF.PAD' endpoints
    against the board; an unresolvable span sorts last (0.0)."""
    try:
        p1 = _tap_point(board, t.get("from"), t.get("net"), "reattempt")
        p2 = _tap_point(board, t.get("to"), t.get("net"), "reattempt")
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])
    except RouteConfigError:
        return 0.0


# ============================================================= QUICK =====
_QUICK_COPPER = ("clearance", "track_width")


def cmd_quick(cfg, board=None, json_out=None):
    """Fast mid-loop verdict on the post-import, PRE-STITCH board.

    WHY (2026-07-21). The DRC grind loop dominates board cost: a full
    rebuild-chain + DRC cycle on the v4 112-part board ran ~8-10 minutes
    with a frontier agent in the loop, so every routing experiment paid the
    full price. `quick` reports the two things a routing iteration can
    actually change — (a) the pcbnew ratsnest unconnected count, (b) copper
    `clearance` + `track_width` violations — in seconds, with NO fill and
    NO stitch. Zone-dependent classes are structurally absent: the zones
    are unfilled at this stage and kicad-cli without --refill-zones emits
    none. Everything else the DRC reports is counted under
    `deferred_classes` (visible, never gating — full DRC after stitch
    remains the release gate, canon: quick is a loop tool, not a gate).

    Unconnected items are split per-net: nets matching prep.waves.exclude
    (pours/stitch own them, e.g. GND) are DEFERRED and do not dirty the
    verdict — on a pre-stitch board they are unconnected by design.

    Exit 1 when routed-net unconnected or copper violations remain, 0 when
    clean. A JSON twin of the summary goes to <build_dir>/quick.json (or
    --json), which `route --race` and grind_driver consume."""
    import fnmatch
    import json as jsonlib
    import time
    import pcbnew
    t0 = time.time()
    target = Path(board).resolve() if board else rel(cfg, cfg["project"]["board"])
    if not target.is_file():
        die(f"quick: board {target} not found")
    b = pcbnew.LoadBoard(str(target))
    conn = b.GetConnectivity()
    conn.RecalculateRatsnest()
    unconn_total = int(conn.GetUnconnectedCount(True))

    build = rel(cfg, get(cfg, "project.build_dir", "06_build/route"))
    build.mkdir(parents=True, exist_ok=True)
    rpt = build / f"quick_drc.{os.getpid()}.json"
    r = subprocess.run(["kicad-cli", "pcb", "drc", "--severity-all",
                        "--format", "json", "-o", str(rpt), str(target)],
                       capture_output=True, text=True)
    if not rpt.is_file():
        die(f"quick: kicad-cli drc wrote no report "
            f"(exit {r.returncode}): {(r.stderr or r.stdout)[-500:]}")
    g = jsonlib.loads(rpt.read_text())
    rpt.unlink()

    excl = list(get(cfg, "prep.waves.exclude", ["GND", "unconnected-*"]))

    def is_deferred(net):
        return any(fnmatch.fnmatch(net, e) for e in excl)

    per_net = {}
    for u in g.get("unconnected_items", []):
        nets = set()
        for it in u.get("items", []):
            m = re.search(r"\[([^\]]+)\]", it.get("description", ""))
            if m:
                nets.add(m.group(1))
        key = sorted(nets)[0] if nets else "?"
        per_net[key] = per_net.get(key, 0) + 1
    routed = {n: c for n, c in sorted(per_net.items()) if not is_deferred(n)}
    deferred = {n: c for n, c in sorted(per_net.items()) if is_deferred(n)}

    viol, other = {}, {}
    for v in g.get("violations", []):
        dst = viol if v["type"] in _QUICK_COPPER else other
        e = dst.setdefault(v["type"], {"count": 0, "samples": []})
        e["count"] += 1
        if len(e["samples"]) < 3:
            e["samples"].append(v.get("description", "")[:160])
    nviol = sum(e["count"] for e in viol.values())

    dirty = bool(routed) or nviol > 0
    out = {
        "board": str(target),
        "runtime_s": round(time.time() - t0, 1),
        "unconnected": {
            "ratsnest_total": unconn_total,
            "routed_total": sum(routed.values()),
            "deferred_total": sum(deferred.values()),
            "routed": routed,
            "deferred": deferred,
        },
        "violations": viol,
        "deferred_classes": {k: e["count"] for k, e in sorted(other.items())},
        "verdict": "DIRTY" if dirty else "CLEAN",
    }
    jp = Path(json_out) if json_out else build / "quick.json"
    jp.write_text(jsonlib.dumps(out, indent=1) + "\n")

    print(f"quick: {target.name}  ({out['runtime_s']}s)")
    print(f"  unconnected: {unconn_total} ratsnest "
          f"({sum(routed.values())} on routed nets, "
          f"{sum(deferred.values())} deferred to pour/stitch)")
    for n, c in list(routed.items())[:10]:
        print(f"    ROUTED-NET OPEN: {n} x{c}")
    for t, e in sorted(viol.items()):
        print(f"  {t}: {e['count']}"
              + (f"  e.g. {e['samples'][0]}" if e['samples'] else ""))
    if other:
        print("  deferred classes (full DRC after stitch owns these): "
              + ", ".join(f"{k}={v}" for k, v in sorted(other.items())))
    print(f"  -> {jp}")
    print(f"quick verdict: {out['verdict']}")
    return 1 if dirty else 0


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
        self.emitted = []          # (x, y) of vias THIS stitch run added —
                                   # the only vias prune_stitch_dangling may
                                   # touch (imported-route/footprint vias are
                                   # someone's design intent, never ours)
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
             "failures": self.failures, "pending": self.pending,
             "emitted": self.emitted}))

    def load_state(self):
        import json
        p = self.state_path()
        if not p.is_file():
            return 0
        d = json.loads(p.read_text())
        self.counts = d.get("counts", {})
        self.failures = d.get("failures", [])
        self.pending = [tuple(x) for x in d.get("pending", [])]
        self.emitted = [tuple(x) for x in d.get("emitted", [])]
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
                self.emitted.append((x, y))
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
    # ALL board reads happen up front, ALL removes happen once at the end.
    # The old shape (remove between sweeps, then GetTracks() again in the
    # same interpreter) hit the intra-pass SWIG poisoning the driver's
    # barrier cannot see: sweep 2's GetStart() returned a bare SwigPyObject
    # (usb-hub-3s, 2026-07-21 — earlier boards survived only because sweep 1
    # never found anything). The fixpoint now runs on a Python-side model.
    segs = []                      # [obj, uuid, code, layer, ends, width_mm]
    vias = []
    for t in ctx.board.GetTracks():
        if t.GetClass() == "PCB_TRACK":
            segs.append([t, t.m_Uuid.AsString(), t.GetNetCode(),
                         t.GetLayer(), _ends_mm(t), t.GetWidth() / 1e6])
        elif t.GetClass() == "PCB_VIA":
            vias.append((t.GetPosition().x / 1e6, t.GetPosition().y / 1e6,
                         t.GetNetCode()))
    pads = [(p, p.GetNetCode()) for fp in ctx.board.GetFootprints()
            for p in fp.Pads()]
    alive = {s[1] for s in segs}

    def served(s, ex, ey):
        _, uid, code, layer, _, _ = s
        for o in segs:
            if o[1] == uid or o[1] not in alive or o[2] != code \
                    or o[3] != layer:
                continue
            (ox, oy), (px, py) = o[4]
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
                    tol + o[5] / 2:
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

    total = 0
    for _ in range(sweeps):
        dead = []
        for s in segs:
            if s[1] not in alive:
                continue
            (ax, ay), (bx, by) = s[4]
            if math.hypot(ax - bx, ay - by) > cap:
                continue
            if not served(s, ax, ay) or not served(s, bx, by):
                dead.append(s)
        if not dead:
            break
        for s in dead:
            alive.discard(s[1])
        total += len(dead)
    for s in segs:
        if s[1] not in alive:
            ctx.remove(s[0])
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
                    okey = (round(mx, 2), round(my, 2))
                    if okey in ctx.emitted:      # keep the emitted-via ledger
                        ctx.emitted[ctx.emitted.index(okey)] = (nx, ny)
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
        # A via SERVES a plane pad only if its barrel drops INSIDE the pad — a
        # via-in-pad bonds pad->plane. A merely-NEARBY via (a neighbour pin's
        # drop `serve_r` away, no copper between) does NOT connect this pad;
        # counting proximity stranded 5 false-served plane pins that each had a
        # clear via-in-pad site (cooksense 2026-07-23). `serve_r` still widens
        # the match to a small ring so a barrel grazing the pad edge counts.
        bb = pad.GetBoundingBox()
        bb.Inflate(int(serve_r * 1e6 / 4))
        for t in ctx.board.GetTracks():
            if (t.GetClass() == "PCB_VIA"
                    and t.GetNetCode() == pad.GetNetCode()
                    and bb.Contains(t.GetPosition())):
                return True
        return False

    # BUILT-IN THERMAL VIA GRIDS: a footprint EP often carries its own
    # same-net PTH thermal pads INSIDE the SMD pad outline (the 3S clean-room
    # HTSSOP-20 EP: 15 of them). Their plated barrels already bond the pad to
    # the plane; a rescue via dropped on top stacks a new drill into the grid
    # — the hole_to_hole clashes that board's cleanup_vias.py part 1 existed
    # to delete post-hoc. A drilled same-net pad inside the outline = served.
    drilled = [(p2.GetPosition(), p2.GetNetCode())
               for fp2 in ctx.board.GetFootprints() for p2 in fp2.Pads()
               if p2.GetDrillSize().x > 0]

    def barrel_served(pad):
        bb = pad.GetBoundingBox()
        return any(nc2 == pad.GetNetCode() and bb.Contains(pos)
                   for pos, nc2 in drilled)

    ok = tot = 0
    fails = []
    for fp in ctx.board.GetFootprints():
        if fp.GetReference() in skip:
            continue
        for p in fp.Pads():
            if p.GetDrillSize().x > 0 or p.GetNetname() != netname:
                continue
            tot += 1
            if has_via(p) or barrel_served(p):
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
    is a pour link; a track end is a direct join). `net` may be a single net
    or a LIST of plane nets (GND + 3V3) — pad_rescue leaves BOTH in pending, so
    a GND-only fallback stranded every unserved 3V3 pin (cooksense 2026-07-23)."""
    pcbnew = ctx.pcbnew
    nets = c.get("net", "GND")
    if isinstance(nets, str):
        nets = [nets]
    lo, hi = float(c.get("min_dist", 0.2)), float(c.get("max_dist", 8.0))
    w = float(c.get("width", 0.3))
    pending = list(ctx.pending)
    fixed = 0
    for netname in nets:
        code = ctx.net(netname).GetNetCode()
        pts = []
        for t in ctx.board.GetTracks():
            if t.GetNetCode() != code:
                continue
            if t.GetClass() == "PCB_VIA":
                pts.append((t.GetPosition().x / 1e6, t.GetPosition().y / 1e6, None))
            else:
                for e in (t.GetStart(), t.GetEnd()):
                    pts.append((e.x / 1e6, e.y / 1e6, t.GetLayer()))
        still = []
        for ref, p in ctx.pads(pending):
            if p.GetNetCode() != code:
                still.append((ref, p.GetNumber()))
                continue
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
        pending = still
    ctx.pending = pending
    ctx.bump("stub_fallback", fixed)
    print(f"stub fallback: recovered {fixed}, {len(pending)} left")

@stitch_pass("astar_fallback")
def p_astar(ctx, c):
    nets = c.get("net", "GND")
    if isinstance(nets, str):
        nets = [nets]
    w = float(c.get("width", 0.25))
    window = float(c.get("window", 3.0))
    attempts = int(c.get("attempts", 3))

    # The toolkit's A* emits its own default 0.45/0.2 vias, which are BELOW
    # a 2-layer standard-tier board's floors. Pinning the geometry is config;
    # `restore` is unconditional so an exception cannot leak the patched
    # toolkit into later passes. `net` may be a LIST (GND + 3V3): each plane
    # net's own via targets, so an unserved 3V3 pin is A*-recovered too.
    pin = c.get("via")
    _orig = (ctx.tk.add_via, ctx.tk.via_site_ok)
    if pin:
        vs, vd = float(pin["size"]), float(pin["drill"])
        ctx.tk.add_via = (lambda x, y, net, size=None, drill=None, _f=_orig[0]:
                          _f(x, y, net, size=vs, drill=vd))
        ctx.tk.via_site_ok = (lambda x, y, nc, size=None, drill=None,
                              _f=_orig[1], **kw:
                              _f(x, y, nc, size=vs, drill=vd, **kw))

    def via_coords():
        return {(round(t.GetPosition().x / 1e6, 2),
                 round(t.GetPosition().y / 1e6, 2))
                for t in ctx.board.GetTracks() if t.GetClass() == "PCB_VIA"}

    before = via_coords()      # A* adds vias inside the toolkit — diff them
    pending = list(ctx.pending)
    fixed = 0
    try:
        for netname in nets:
            code = ctx.net(netname).GetNetCode()
            targets = [(t.GetPosition().x / 1e6, t.GetPosition().y / 1e6)
                       for t in ctx.board.GetTracks()
                       if t.GetClass() == "PCB_VIA" and t.GetNetCode() == code]
            still = []
            for ref, p in ctx.pads(pending):
                if p.GetNetCode() != code:
                    still.append((ref, p.GetNumber()))
                    continue
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
            pending = still
    finally:
        ctx.tk.add_via, ctx.tk.via_site_ok = _orig
        ctx._used = None
        ctx.emitted.extend(sorted(via_coords() - before))
    ctx.pending = pending
    ctx.bump("astar_fallback", fixed)
    print(f"A* fallback: recovered {fixed}, {len(pending)} left")


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


@stitch_pass("prune_stitch_dangling")
def p_prune_stitch_dangling(ctx, c):
    """Epilogue: remove vias THIS STITCH RUN emitted that ended up with
    same-net copper on fewer than 2 layers — the `via_dangling` DRC class.
    via_janitor credits a zone by its OUTLINE, so a via inside the outline
    but in a fill VOID (or over a plane region that belongs to another net)
    passes janitor and still dangles after fill — the 3S clean-room run
    deleted exactly these post-hoc in cleanup_vias.py. This pass therefore
    runs AFTER `fill` and tests the FILLED polys.

    SCOPE: only coordinates in the run's emitted-via ledger (try_via + the
    A* fallback, carried across SWIG barriers in the resume state) are
    candidates. Imported-route and footprint vias are somebody's design
    intent — a dangling one there is a finding for DRC, not for deletion."""
    pcbnew = ctx.pcbnew
    tol = float(c.get("tol", 0.05))
    minlay = int(c.get("min_layers", 2))
    zones = [z for z in ctx.board.Zones() if not z.GetIsRuleArea()
             and z.GetNetname()]
    if zones and not any(z.IsFilled() for z in zones):
        die("prune_stitch_dangling must run AFTER `fill` — on an unfilled "
            "board every stitch via looks dangling and would be pruned")
    emitted = ctx.emitted
    if not emitted:
        print("prune_stitch_dangling: no stitch-emitted vias this run")
        return

    def seg_d2(px, py, ax, ay, bx, by):
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
        return (px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2

    dead = []
    for v in [t for t in ctx.board.GetTracks() if t.GetClass() == "PCB_VIA"]:
        vx, vy = v.GetPosition().x / 1e6, v.GetPosition().y / 1e6
        if not any(abs(vx - ex) <= tol and abs(vy - ey) <= tol
                   for ex, ey in emitted):
            continue                        # not ours — never touch it
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
                bb = p.GetBoundingBox()
                bb.Inflate(v.GetWidth() // 2)
                if bb.Contains(v.GetPosition()):
                    for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
                        if p.IsOnLayer(lay):
                            attach.add(lay)
        for z in zones:
            if z.GetNetCode() != v.GetNetCode():
                continue
            for lay in z.GetLayerSet().Seq():
                if lay in attach:
                    continue
                # FILLED polys, not the outline — the whole point
                if z.IsFilled() and \
                        z.GetFilledPolysList(lay).Contains(v.GetPosition()):
                    attach.add(lay)
        if len(attach) < minlay:
            dead.append(v)
    for v in dead:
        ctx.remove(v)
    ctx._used = None
    ctx.bump("stitch_dangling_pruned", len(dead))
    print(f"pruned {len(dead)} dangling stitch-emitted vias "
          f"(of {len(emitted)} emitted)")


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


# ------------------------------------------------- pour-island healing ----
def _island_holds(ctx, isl, item):
    """Is this same-net track/via/pad geometrically seated on the island?
    (endpoint/position inside the FILLED outline, layer-aware)."""
    o, lay = isl["chain"], isl["layer"]
    cls = item.GetClass()
    if cls == "PCB_VIA":
        return (item.GetLayerSet().Contains(lay)
                and o.PointInside(item.GetPosition()))
    if cls == "PCB_TRACK":
        if item.GetLayer() != lay:
            return False
        s, e = item.GetStart(), item.GetEnd()
        mid = ctx.pcbnew.VECTOR2I((s.x + e.x) // 2, (s.y + e.y) // 2)
        return any(o.PointInside(p) for p in (s, e, mid))
    if cls == "PAD":
        if item.GetDrillSize().x <= 0 and not item.IsOnLayer(lay):
            return False
        return o.PointInside(item.GetPosition())
    return False


def _heal_groups(ctx, min_bb, lids=None):
    """{netname: [island-group, ...]} on the FILLED board. One group = the
    filled islands of ONE pcbnew-connectivity component: items (tracks/vias/
    pads of the net) are clustered with GetConnectedItems — which is
    island-aware after fill (two pads joined only through the same pour
    island share a cluster; pads in different islands do not, verified on
    KiCad 10.0.4) — and each island is seated in the cluster of the items
    it geometrically holds. An island holding no item is its own group (a
    bare plane is a legitimate via-bridge target). Only groups holding at
    least one island >= min_bb in both bbox dims count: smaller slivers are
    the isolated_copper class (grind table: escalate), not heal work."""
    pcbnew = ctx.pcbnew
    conn = ctx.board.GetConnectivity()
    zones = [z for z in ctx.board.Zones()
             if not z.GetIsRuleArea() and z.GetNetname() and z.IsFilled()]
    out = {}
    for netname in sorted({z.GetNetname() for z in zones}):
        code = ctx.board.FindNet(netname).GetNetCode()
        islands = []
        for z in zones:
            if z.GetNetname() != netname:
                continue
            for lay in z.GetLayerSet().Seq():
                if not pcbnew.IsCopperLayer(lay) or (lids and lay not in lids):
                    continue
                polys = z.GetFilledPolysList(lay)
                for i in range(polys.OutlineCount()):
                    o = polys.Outline(i)
                    bb = o.BBox()
                    islands.append(
                        {"zone": z, "layer": lay, "chain": o,
                         "big": (bb.GetWidth() >= min_bb * 1e6
                                 and bb.GetHeight() >= min_bb * 1e6)})
        if not islands:
            continue
        items = {}
        for t in ctx.board.GetTracks():
            if t.GetNetCode() == code:
                items[t.m_Uuid.AsString()] = t
        for fp in ctx.board.GetFootprints():
            for p in fp.Pads():
                if p.GetNetCode() == code:
                    items[p.m_Uuid.AsString()] = p

        parent = {k: k for k in items}

        def find(a):
            r = a
            while parent[r] != r:
                r = parent[r]
            while parent[a] != r:
                parent[a], a = r, parent[a]
            return r

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

        done = set()
        for k, it in items.items():
            if k in done:
                continue
            done.add(k)
            for other in conn.GetConnectedItems(it):
                ku = getattr(other, "m_Uuid", None)
                ku = ku.AsString() if ku is not None else None
                if ku in items:
                    done.add(ku)
                    union(k, ku)
        for idx, isl in enumerate(islands):
            key = f"~island{idx}"
            parent[key] = key
            for k, it in items.items():
                if _island_holds(ctx, isl, it):
                    union(key, k)
        groups = {}
        for idx, isl in enumerate(islands):
            groups.setdefault(find(f"~island{idx}"), []).append(isl)
        out[netname] = [g for g in groups.values()
                        if any(i["big"] for i in g)]
    return out


def _bridge_width(ctx, netname):
    """The zone's NET-CLASS width (rules/nets.yaml classes min_width — the
    same source the .kicad_dru floors are generated from, so the bridge can
    never itself be a track_width finding), falling back to the zone's own
    min thickness."""
    f = net_class_floors(ctx.cfg).get(netname)
    if f:
        return f[1]
    zmw = [z.GetMinThickness() for z in ctx.board.Zones()
           if z.GetNetname() == netname and not z.GetIsRuleArea()]
    return max(zmw) / 1e6 if zmw else 0.25


def _gap_candidates(ctx, ia, ib, step):
    """Candidate (gap_mm, ia, ib, pA, pB) bridge sites between two island
    outlines: sample points along A's outline, snap each to B's nearest
    outline point, re-snap onto A — narrowest gaps first is the caller's
    sort. NearestPoint is KiCad's own chain search (C++), so this stays
    cheap on detailed filled outlines."""
    A, B = ia["chain"], ib["chain"]
    pts = []
    n = A.PointCount()
    for i in range(n):
        p1, p2 = A.CPoint(i), A.CPoint((i + 1) % n)
        seg = math.hypot((p2.x - p1.x) / 1e6, (p2.y - p1.y) / 1e6)
        k = max(1, min(6, int(seg / step)))
        for j in range(k):
            f = j / k
            pts.append(ctx.pcbnew.VECTOR2I(int(p1.x + (p2.x - p1.x) * f),
                                           int(p1.y + (p2.y - p1.y) * f)))
    if len(pts) > 240:
        pts = pts[::len(pts) // 240 + 1]
    out = []
    for a in pts:
        nb = B.NearestPoint(a)
        na = A.NearestPoint(nb)
        d = math.hypot((na.x - nb.x) / 1e6, (na.y - nb.y) / 1e6)
        out.append((round(d, 3), ia, ib,
                    (na.x / 1e6, na.y / 1e6), (nb.x / 1e6, nb.y / 1e6)))
    return out


def _inset_point(pcbnew, chain, p, toward_other, width):
    """Pull a bridge endpoint slightly INTO its island (away from the other
    island) so the track body overlaps filled copper and the refill merges
    it; falls back to the outline point when the inset leaves the poly."""
    d = math.hypot(p[0] - toward_other[0], p[1] - toward_other[1])
    if d < 1e-9:
        return (round(p[0], 3), round(p[1], 3))
    u = ((p[0] - toward_other[0]) / d, (p[1] - toward_other[1]) / d)
    ins = width / 2 + 0.05
    q = (round(p[0] + u[0] * ins, 3), round(p[1] + u[1] * ins, 3))
    if chain.PointInside(pcbnew.VECTOR2I_MM(q[0], q[1])):
        return q
    return (round(p[0], 3), round(p[1], 3))


def _guard_same_net(net, ia, ib):
    """THE net guard: a heal may only ever join copper of ONE net. The
    grouping is already per-net, so tripping this means the grouping is
    broken — die loudly rather than emit a short."""
    code = net.GetNetCode()
    if ia["zone"].GetNetCode() != code or ib["zone"].GetNetCode() != code:
        die(f"heal_islands: NET GUARD — refusing to bridge zone "
            f"[{ia['zone'].GetNetname()}] to zone [{ib['zone'].GetNetname()}]"
            f" while healing {net.GetNetname()!r}: a heal must NEVER bridge "
            f"different nets")


def _via_overlap_site(ctx, net, ia, ib):
    """A collision-checked through-via site inside BOTH islands (different
    layers) — the shared-plane bridge. Every via goes through ctx.try_via
    (via_site_ok + keepin/spacing/PTH guards), same discipline as taps."""
    pcbnew = ctx.pcbnew
    ba, bb = ia["chain"].BBox(), ib["chain"].BBox()
    x0 = max(ba.GetLeft(), bb.GetLeft()) / 1e6
    x1 = min(ba.GetRight(), bb.GetRight()) / 1e6
    y0 = max(ba.GetTop(), bb.GetTop()) / 1e6
    y1 = min(ba.GetBottom(), bb.GetBottom()) / 1e6
    if x1 <= x0 or y1 <= y0:
        return None
    for fx in range(2, 19, 2):
        for fy in range(2, 19, 2):
            x = round(x0 + (x1 - x0) * fx / 20, 2)
            y = round(y0 + (y1 - y0) * fy / 20, 2)
            v = pcbnew.VECTOR2I_MM(x, y)
            if not (ia["chain"].PointInside(v) and ib["chain"].PointInside(v)):
                continue
            if ctx.try_via(net, x, y):
                return (x, y)
    return None


def _bridge_groups(ctx, c, net, ga, gb, width):
    """One bridge between two island-groups of the SAME net, cheapest legal
    strategy first. Returns a description of what was emitted, or None.
      1. same-layer track at `width`, over the narrowest gap whose straight
         path clears live copper (tk.collides, exact shapes) — a blocked
         gap falls through to the NEXT-narrowest candidate;
      2. a through-via where an island of one group overlaps an island of
         the other on a DIFFERENT layer (the shared-plane hop; two group
         merges through a plane = the via pair)."""
    code = net.GetNetCode()
    cands = []
    for ia in ga:
        if not ia["big"]:
            continue
        for ib in gb:
            if not ib["big"] or ia["layer"] != ib["layer"]:
                continue
            cands += _gap_candidates(ctx, ia, ib,
                                     float(c.get("sample_step", 1.5)))
    cands.sort(key=lambda t: t[0])
    taken = []
    tries = int(c.get("max_gap_candidates", 24))
    for d, ia, ib, pa, pb in cands:
        if len(taken) >= tries:
            break
        if any(math.hypot(pa[0] - tx, pa[1] - ty) < 1.0 for tx, ty in taken):
            continue
        taken.append(pa)
        _guard_same_net(net, ia, ib)
        qa = _inset_point(ctx.pcbnew, ia["chain"], pa, pb, width)
        qb = _inset_point(ctx.pcbnew, ib["chain"], pb, pa, width)
        lay = ia["layer"]
        if ctx.tk.collides(qa[0], qa[1], qb[0], qb[1], width, code,
                           lay) is not None:
            continue                     # blocked -> next-narrowest gap
        ctx.tk.add_seg(qa[0], qa[1], qb[0], qb[1], net, lay, width)
        return (f"track bridge ({qa[0]:.2f},{qa[1]:.2f})->"
                f"({qb[0]:.2f},{qb[1]:.2f}) w={width} "
                f"{ctx.board.GetLayerName(lay)} gap {d:.2f}mm")
    for ia in ga:
        if not ia["big"]:
            continue
        for ib in gb:
            if not ib["big"] or ia["layer"] == ib["layer"]:
                continue
            _guard_same_net(net, ia, ib)
            pt = _via_overlap_site(ctx, net, ia, ib)
            if pt:
                return (f"plane via ({pt[0]:.2f},{pt[1]:.2f}) "
                        f"{ctx.board.GetLayerName(ia['layer'])}<->"
                        f"{ctx.board.GetLayerName(ib['layer'])}")
    return None


def _heal_net(ctx, c, netname, groups):
    """Merge every island-group of one net into the largest (by island
    area), retrying the worklist so a bare plane can serve as the stepping
    stone between two same-layer groups (A->plane via, then B->plane via =
    the via PAIR). Unmergeable leftovers are a hard error."""
    net = ctx.net(netname)
    width = _bridge_width(ctx, netname)

    def area(g):
        return sum(i["chain"].Area() for i in g if i["big"])

    ordered = sorted(groups, key=area, reverse=True)
    main, rest = list(ordered[0]), [list(g) for g in ordered[1:]]
    n = 0
    progress = True
    while rest and progress:
        progress = False
        for g in list(rest):
            how = _bridge_groups(ctx, c, net, main, g, width)
            if how:
                print(f"  heal {netname}: {how}")
                main.extend(g)
                rest.remove(g)
                n += 1
                progress = True
    if rest:
        # UNBRIDGEABLE leftovers are almost always orphan pour fragments held
        # alive only by a dangling stitch via — a mode=ALWAYS zone drops them
        # on the very next refill (verified: the kicad-cli --refill-zones DRC
        # reports them GONE). Rather than DIE before the caller's refill can
        # remove them, SKIP them here; the caller refills (mode=ALWAYS) and
        # RE-VERIFIES (`after`), so a leftover that a refill does NOT dissolve
        # (a genuine split holding real copper) still hard-errors there.
        print(f"  heal {netname}: {len(rest)} unbridgeable orphan group(s) "
              f"left to the mode=ALWAYS refill (removed if truly orphan)")
    return n


@stitch_pass("heal_islands")
def p_heal_islands(ctx, c):
    """AUTO-HEAL same-net pour splits: a zone that FILLS as two or more
    disconnected islands (the DRC unconnected_items class whose both sides
    read `Zone [X] <-> Zone [X]`, same net). Provenance: 4 of the v4
    usb-hub-3s clean-room canary's last 7 gate findings were exactly this
    (nets LX1, LX2, VIN_S, VBUSA3 — priority-2 F.Cu converter hot-loop
    pours sliced by escape tracks, 2026-07-21), each bridged BY HAND by an
    expensive agent. This pass makes that mechanical.

    Runs AFTER `fill` (islands only exist on the filled board). Detection:
    pcbnew's own connectivity (GetConnectedItems is island-aware after
    fill) groups the net's tracks/vias/pads; each filled island is seated
    in its items' group; >= 2 groups = a split. Bridging: narrowest
    collision-clear same-layer gap first (a track at the net-class width,
    zone-min-width fallback), then a through-via where a same-net island
    on another layer overlaps both sides (the shared-plane via pair).
    EVERY emitted segment/via is verified against live copper via the
    pcb_toolkit primitives (collides / try_via->via_site_ok), the same
    discipline as `taps`; foreign-net ZONE FILLS are deliberately not
    probed — the refill re-flows them around the new copper (the toolkit's
    documented refill-after-edit contract). Then the zones are REFILLED
    and the groups RECOMPUTED: a heal that does not reduce a net's island
    group count — or that leaves ANY net split — is a hard error, never a
    silent no-op. On an already-healed board the pass emits nothing
    (idempotent), and it structurally cannot bridge nets: grouping is
    per-net and the emit path dies on a zone netcode mismatch."""
    pcbnew = ctx.pcbnew
    min_bb = float(c.get("min_bbox", 0.8))
    lids = ({_layer_id(pcbnew, n) for n in c["layers"]}
            if c.get("layers") else None)
    zones = [z for z in ctx.board.Zones()
             if not z.GetIsRuleArea() and z.GetNetname()]
    if zones and not any(z.IsFilled() for z in zones):
        die("heal_islands must run AFTER `fill` — an unfilled pour has no "
            "islands, so healing there would silently verify nothing")
    ctx.board.BuildConnectivity()
    groups = _heal_groups(ctx, min_bb, lids)
    splits = {n: g for n, g in groups.items() if len(g) > 1}
    if not splits:
        ctx.bump("islands_healed", 0)
        print("heal_islands: no same-net zone split — nothing to heal "
              "(0 bridges)")
        return
    healed = {}
    for netname in sorted(splits):
        healed[netname] = (len(splits[netname]),
                           _heal_net(ctx, c, netname, splits[netname]))
    # refill, then RE-VERIFY on the refilled board
    pcbnew.ZONE_FILLER(ctx.board).Fill(ctx.board.Zones())
    ctx.board.BuildConnectivity()
    after = _heal_groups(ctx, min_bb, lids)
    for netname, (was, _n) in sorted(healed.items()):
        now = len(after.get(netname, []))
        if now >= was:
            die(f"heal_islands: net {netname!r} still shows {now} "
                f"disconnected island group(s) after healing (was {was}) — "
                f"the bridge did not merge the pour; a heal that does not "
                f"reduce the island count is an ERROR, not a no-op")
    left = sorted(n for n, g in after.items() if len(g) > 1)
    if left:
        die(f"heal_islands: net(s) {left} split after heal+refill (a "
            f"bridge for another net can re-slice a pour it crosses) — "
            f"refusing to report a heal that left splits behind")
    tot = sum(n for _w, n in healed.values())
    ctx.bump("islands_healed", tot)
    print(f"heal_islands: {len(healed)} net(s) healed with {tot} bridge(s): "
          + ", ".join(f"{n} ({w}->1)"
                      for n, (w, _x) in sorted(healed.items())))


# ------------------------------------------------- deterministic seed stubs --
def _same_seg_exists(ctx, x1, y1, x2, y2, lid, code, tol=0.02):
    """Idempotency probe: does a same-net track with these endpoints already
    exist on this layer? A rerun of seed_stubs must emit no new copper."""
    for t in ctx.board.GetTracks():
        if (t.GetClass() != "PCB_TRACK" or t.GetNetCode() != code
                or t.GetLayer() != lid):
            continue
        (ax, ay), (bx, by) = _ends_mm(t)

        def near(p, q):
            return abs(p[0] - q[0]) <= tol and abs(p[1] - q[1]) <= tol
        if ((near((ax, ay), (x1, y1)) and near((bx, by), (x2, y2)))
                or (near((ax, ay), (x2, y2)) and near((bx, by), (x1, y1)))):
            return True
    return False


def _same_via_exists(ctx, x, y, code, tol=0.05):
    for t in ctx.board.GetTracks():
        if t.GetClass() == "PCB_VIA" and t.GetNetCode() == code:
            vx, vy = t.GetPosition().x / 1e6, t.GetPosition().y / 1e6
            if abs(vx - x) <= tol and abs(vy - y) <= tol:
                return True
    return False


def _pin_touched(ctx, px, py, code, tol=0.16):
    """Is the pin pad (px,py) touched by same-net track copper or a via —
    i.e. did the seed stub actually reach it?"""
    for t in ctx.board.GetTracks():
        if t.GetNetCode() != code:
            continue
        if t.GetClass() == "PCB_VIA":
            vx, vy = t.GetPosition().x / 1e6, t.GetPosition().y / 1e6
            if math.hypot(vx - px, vy - py) <= tol:
                return True
        else:
            for e in _ends_mm(t):
                if math.hypot(e[0] - px, e[1] - py) <= tol:
                    return True
    return False


@stitch_pass("seed_stubs")
def p_seed_stubs(ctx, c):
    """DETERMINISTIC pour-fed chip-pin stubs (canon M8 promotion). The
    pour-fed nets that leave a dense IC pin row and must weave across the
    escape field to reach their pour island are the connections KRT excludes
    and the tap threader is too short to own: hand-written per board as an
    explicit-geometry emitter with collision REFUSAL (usb-hub-3s
    03_src/plan_seed_stubs.py + add_seed_stubs.py, itself the second strike
    after prior boards' via-farm emitters). This promotes the EMITTER —
    fixed geometry from the config, verified against the live board's exact
    copper, idempotent — into the generic backend.

    Runs BEFORE `fill` (place stub copper first so the pour flows around it
    and bonds the pin). Config (`stitch.seed_stubs`):
        clearance: 0.13                 # tighter than stitch clearance
        via: {size: 0.25, drill: 0.15}  # tier-derived when omitted
        stubs:
          - {net: LX1, pin: U1.18,
             segments: [{layer: F.Cu, width: 0.25, pts: [[x,y],[x,y]]}],
             vias: [[x,y]]}
    SAFETY (the D-BACK lesson — an unbounded emitter is worse than none):
      (a) reduce: each stub declares the `pin` (REF.PAD) it serves and the
          pass PROVES the placed copper reaches that pad — a stub that
          connects nothing is a hard error, not a silent no-op;
      (b) zero new violations: EVERY segment/via is exact-collision-checked
          against foreign copper (tk.collides / via_site_ok) at the stub
          clearance — a stub grazing another net is REFUSED whole, never
          shaved (the add_seed_stubs discipline);
      (c) idempotent: identical same-net copper already on the board is
          skipped, so a rerun emits nothing;
      (d) refuse, don't guess: a colliding stub is recorded as a gate
          failure (escalate) rather than placed thin, and a `pin` on the
          wrong net dies (a seed stub must NEVER bridge nets)."""
    pcbnew = ctx.pcbnew
    stubs = c.get("stubs") or []
    if not stubs:
        print("seed_stubs: none configured (0 stubs)")
        ctx.bump("seed_stubs", 0)
        return
    filled = [z for z in ctx.board.Zones()
              if not z.GetIsRuleArea() and z.GetNetname() and z.IsFilled()]
    if filled:
        die("seed_stubs must run BEFORE `fill` — a stub laid after fill is "
            "not flowed around by the pour, so the pin it serves stays open")
    via = dict(c.get("via", {}) or {})
    _stub_tier_via(ctx.cfg, via)
    vs, vd = float(via.get("size", 0.25)), float(via.get("drill", 0.15))
    tk = ctx.Toolkit(ctx.board, float(c.get("clearance", 0.13)))
    served = refused = placed = skipped = 0
    for i, stub in enumerate(stubs):
        netname = stub.get("net") or die(f"seed_stubs.stubs[{i}]: no `net`")
        net = ctx.net(netname)
        code = net.GetNetCode()
        pin = stub.get("pin")
        pinpad = None
        if pin:
            ref, num = str(pin).split(".", 1)
            fp = ctx.board.FindFootprintByReference(ref)
            if fp is None:
                die(f"seed_stubs.stubs[{i}]: no footprint {ref!r}")
            for p in fp.Pads():
                if p.GetNumber() == num:
                    pinpad = p
                    break
            if pinpad is None:
                die(f"seed_stubs.stubs[{i}]: {ref} has no pad {num!r}")
            if pinpad.GetNetname() != netname:
                die(f"seed_stubs.stubs[{i}]: pin {pin} is on net "
                    f"{pinpad.GetNetname()!r}, not {netname!r} — a seed stub "
                    f"must NEVER bridge nets")
        prims, conflict = [], None
        for seg in stub.get("segments", []) or []:
            lid = _layer_id(pcbnew, seg["layer"])
            w = float(seg["width"])
            pts = seg["pts"]
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                ax, ay, bx, by = (round(v, 3) for v in (ax, ay, bx, by))
                if tk.collides(ax, ay, bx, by, w, code, lid) is not None:
                    conflict = f"seg ({ax},{ay})->({bx},{by}) {seg['layer']}"
                    break
                prims.append(("seg", ax, ay, bx, by, w, lid))
            if conflict:
                break
        if conflict is None:
            for (vx, vy) in stub.get("vias", []) or []:
                vx, vy = round(vx, 3), round(vy, 3)
                if (not _same_via_exists(ctx, vx, vy, code)
                        and not tk.via_site_ok(vx, vy, code, size=vs, drill=vd)):
                    conflict = f"via ({vx},{vy})"
                    break
                prims.append(("via", vx, vy))
        if conflict is not None:
            ctx.failures.append(
                f"seed_stub {netname} {pin or ''}: REFUSED — {conflict} "
                f"collides foreign copper")
            refused += 1
            print(f"  seed_stub {netname} {pin or '?'}: REFUSED ({conflict})")
            continue
        for prim in prims:
            if prim[0] == "seg":
                _, ax, ay, bx, by, w, lid = prim
                if _same_seg_exists(ctx, ax, ay, bx, by, lid, code):
                    skipped += 1
                    continue
                tk.add_seg(ax, ay, bx, by, net, lid, w)
                placed += 1
            else:
                _, vx, vy = prim
                if _same_via_exists(ctx, vx, vy, code):
                    skipped += 1
                    continue
                tk.add_via(vx, vy, net, size=vs, drill=vd)
                placed += 1
        if pinpad is not None:
            px, py = (pinpad.GetPosition().x / 1e6,
                      pinpad.GetPosition().y / 1e6)
            if not _pin_touched(ctx, px, py, code):
                die(f"seed_stubs.stubs[{i}]: the stub placed for {pin} does "
                    f"not reach the pin pad — it connects nothing (check the "
                    f"first segment starts at the pad)")
        served += 1
    ctx.bump("seed_stubs", placed)
    print(f"seed_stubs: {served} pin(s) served ({placed} segments/vias "
          f"placed, {skipped} idempotent-skip), {refused} refused")


# ------------------------------------------ same-net zone priority unify ------
def _zone_overlap_pairs(ctx):
    """(same_net_same_prio, cross_net) copper-zone pairs whose OUTLINES
    overlap on a shared copper layer. KiCad flags a same-net same-priority
    outline intersection as `zones_intersect` ('intersecting zones must have
    distinct priorities'); a cross-net area overlap is a SHORT."""
    pcbnew = ctx.pcbnew
    zones = [z for z in ctx.board.Zones()
             if not z.GetIsRuleArea() and z.GetNetname()]
    same, cross = [], []
    for i in range(len(zones)):
        za = zones[i]
        for j in range(i + 1, len(zones)):
            zb = zones[j]
            if not any(zb.GetLayerSet().Contains(l)
                       for l in za.GetLayerSet().Seq()
                       if pcbnew.IsCopperLayer(l)):
                continue
            if not za.Outline().BBox().Intersects(zb.Outline().BBox()):
                continue
            inter = pcbnew.SHAPE_POLY_SET(za.Outline())
            inter.BooleanIntersection(zb.Outline())
            if inter.OutlineCount() == 0 or inter.Area() <= 0:
                continue
            if za.GetNetCode() == zb.GetNetCode():
                if za.GetAssignedPriority() == zb.GetAssignedPriority():
                    same.append((za, zb))
            else:
                cross.append((za, zb))
    return same, cross


@stitch_pass("unify_zone_priorities")
def p_unify_zone_priorities(ctx, c):
    """AUTO-FIX the `zones_intersect_same_net` class: two pours of the SAME
    net that overlap at the SAME priority. KiCad reports 'Copper zones
    intersect (intersecting zones must have distinct priorities)' on the
    union — the fix hand-applied on usb-hub-3s v1.0 (the 'P3-union'
    precedent) and re-learned on v1.1 (3 findings, priority-2 pool + strip
    overlaps): bump the smaller zone to a distinct, higher priority so KiCad
    sees a legal NESTING instead of an intersection. Same net => the copper
    union is electrically identical; only the priority integer changes.

    SAFETY (an unbounded auto-fixer is worse than none):
      (a) reduce: after bumping + refill the pass RE-MEASURES same-net
          same-priority overlaps and dies if any remain — a unify that does
          not clear the intersection is an error, never a no-op;
      (b) zero new violations: cross-net zone overlap is a SHORT and is
          REFUSED loudly (never priority-bumped — that would hide a short);
          and the refill is checked with the heal_islands grouping so a
          bump that slices a pour into MORE islands (trading
          zones_intersect for unconnected) is a hard error;
      (c) idempotent: once priorities are distinct nothing matches, so a
          rerun is a no-op;
      (d) refuse, don't guess: the cross-net case dies (escalate to the
          shorting_items owner) rather than mechanically merging nets."""
    pcbnew = ctx.pcbnew
    min_bb = float(c.get("min_bbox", 0.8))
    same, cross = _zone_overlap_pairs(ctx)
    if cross:
        za, zb = cross[0]
        die(f"unify_zone_priorities: zones of DIFFERENT nets overlap "
            f"([{za.GetNetname()}] and [{zb.GetNetname()}]) — that is a "
            f"SHORT, not a same-net priority union. Refusing to touch it: a "
            f"cross-net zone intersection is design work (shorting_items), "
            f"never a mechanical priority bump")
    if not same:
        ctx.bump("zone_priorities_unified", 0)
        print("unify_zone_priorities: no same-net same-priority zone overlap "
              "— nothing to unify (0 bumps)")
        return
    before = None
    if any(z.IsFilled() for z in ctx.board.Zones()
           if not z.GetIsRuleArea() and z.GetNetname()):
        ctx.board.BuildConnectivity()
        before = {n: len(g)
                  for n, g in _heal_groups(ctx, min_bb).items()}
    maxp = max((z.GetAssignedPriority() for z in ctx.board.Zones()
                if not z.GetIsRuleArea() and z.GetNetname()), default=0)
    bumped, seen = 0, set()
    for za, zb in same:
        small = za if za.Outline().Area() <= zb.Outline().Area() else zb
        if id(small) in seen:
            continue
        maxp += 1
        small.SetAssignedPriority(maxp)
        seen.add(id(small))
        bumped += 1
        print(f"  unify {small.GetNetname()}: overlapping zone -> "
              f"priority {maxp}")
    pcbnew.ZONE_FILLER(ctx.board).Fill(ctx.board.Zones())
    ctx.board.BuildConnectivity()
    same_after, cross_after = _zone_overlap_pairs(ctx)
    if same_after:
        za, zb = same_after[0]
        die(f"unify_zone_priorities: {len(same_after)} same-net same-priority "
            f"zone overlap(s) REMAIN after the bump (e.g. "
            f"[{za.GetNetname()}]) — a unify that does not clear the "
            f"intersection is an ERROR, not a no-op")
    if cross_after:
        die("unify_zone_priorities: the priority bump exposed a cross-net "
            "zone overlap — refusing to report a fix that created a short")
    if before is not None:
        after = {n: len(g)
                 for n, g in _heal_groups(ctx, min_bb).items()}
        worse = [n for n, cnt in after.items() if cnt > before.get(n, cnt)]
        if worse:
            die(f"unify_zone_priorities: the priority bump sliced pour(s) "
                f"{worse} into MORE islands — refusing a fix that fragments a "
                f"net (that trades zones_intersect for unconnected)")
    ctx.bump("zone_priorities_unified", bumped)
    print(f"unify_zone_priorities: {bumped} zone(s) re-prioritised, "
          f"{len(same)} same-net intersection(s) cleared")


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


DEFAULT_PASSES = ["seed_stubs", "dedupe_vias", "drop_micro_fragments",
                  "reload", "pad_rescue", "stitch_grid", "via_janitor",
                  "fill", "island_rescue", "unify_zone_priorities",
                  "heal_islands", "gate"]


# stitch.via and friends spell the geometry size/drill, not via_size/via_drill
_VIA_KEYMAP = {"via_size": "size", "via_drill": "drill", "clearance": None}


def _stub_tier_via(cfg, via):
    """Tier floors for a seed_stubs via geometry (same discipline as
    stitch.via): a missing size/drill defaults to the declared fab tier's
    floor; an explicit sub-floor value is a hard error naming the tier."""
    tier = fab_tier(cfg)
    if tier is not None:
        tier_geometry(via, tier, "stitch.seed_stubs.via", keymap=_VIA_KEYMAP)


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
    ap.add_argument("command",
                    choices=["prep", "route", "import", "taps", "quick",
                             "stitch", "all"])
    ap.add_argument("config")
    ap.add_argument("--root", default=None,
                    help="project root (default: the config's grandparent dir)")
    ap.add_argument("--board", default=None,
                    help="quick: evaluate THIS board instead of project.board "
                         "(race candidates)")
    ap.add_argument("--json", default=None,
                    help="quick: write the JSON summary here instead of "
                         "<build_dir>/quick.json")
    ap.add_argument("--race", type=int, default=None,
                    help="route: run N concurrent wave-chains and keep the "
                         "quick-measured best (overrides route.race)")
    a = ap.parse_args(argv)
    cfg = load_cfg(a.config, a.root)
    try:
        if a.command == "prep":
            return cmd_prep(cfg)
        if a.command == "route":
            return cmd_route(cfg, race=a.race)
        if a.command == "import":
            return cmd_import(cfg)
        if a.command == "taps":
            return cmd_taps(cfg)
        if a.command == "quick":
            return cmd_quick(cfg, board=a.board, json_out=a.json)
        if a.command == "stitch":
            return cmd_stitch(cfg)
        for fn in (cmd_prep, cmd_route, cmd_import, cmd_taps, cmd_stitch):
            rc = fn(cfg)
            if rc:
                return rc
        return 0
    except RouteConfigError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
