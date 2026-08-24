#!/usr/bin/env python3
"""route_and_stitch_generic — ONE parameterized routing + stitch/fill backend,
driven by a small declarative per-board `03_src/route.yaml`, replacing the
hand-written `03_src/route_prep.py` + `route_waves.sh` + `stitch_and_fill.py`
that every project used to carry (215-537 lines of stitcher each).

WHY. `generate_board_generic.py` collapsed the board GENERATOR; the stage
after it stayed bespoke. Surveying six shipped boards (usb-power-3s,
ble-bus-bar, crow-array-pod, cook-loadcell, crowsync-recorder, cook-hub)
showed the same pipeline every time, with different constants:

    route-prep (segment-free + unfilled + keepouts + rules ride along)
      -> KRT waves, hardest-first, chained rN -> rN+1
      -> import ONCE into the segment-free base (source vias preserved)
      -> taps (optional): collision-checked NAMED connections KRT cannot
         thread — pour-fed sense pins, boxed-in pads, plane drops
      -> stitch: clean KRT artifacts -> rescue pads -> stitch grid
                 -> janitor -> FILL -> island rescue -> heal islands -> gate
      -> generate_rules LAST (pcbnew saves clobber .kicad_pro netclasses)

    /usr/bin/python3 route_and_stitch_generic.py prep    03_src/route.yaml
    <KRT venv python>  route_and_stitch_generic.py route 03_src/route.yaml
    <KRT venv python>  route_and_stitch_generic.py route 03_src/route.yaml \
                          --through-wave critical
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
  * the route input is SEGMENT-FREE and UNFILLED — KRT routes straight
    through pre-existing segments otherwise (400+ silent crossings, twice).
    Source-owned vias remain as routing obstacles.
  * KRT output is imported ONCE, into the segment-free base, never into a
    board that already carries routed segments (that doubles everything).
  * `import` REFILLS the pours it imported into — EXCEPT when a following
    pipeline step places explicit copper before stitch's `fill` (`taps` or
    `stitch.seed_stubs`), where it must hand `import_krt.py --no-fill` so the
    later fill flows around that copper (see `_import_may_fill`).
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
  * a mis-shaped `length_match_group` (not a list of patterns, or not a list
    of such lists) — coercing it would route with the WRONG matched set and
    say nothing
  * a KRT wave exiting nonzero
  * an opted-in wave whose realized output violates its realized_width
    contract (the command-line width is not evidence)
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
            wins; CLI --race overrides), import_source (build|promoted),
            prefix {board, through_wave, r0_sha256, board_sha256} (optional
            reviewed, hash-bound critical prefix from which later waves resume),
            kicad_python (KiCad interpreter), ownership_preflight and
            candidate_grade {mode: observe|enforce}, exploration_guard
            {mode, plateau_attempts, max_attempts, max_novel_signatures,
            max_operation_amplification}, forbid_new_via_in_pad (compare
            every wave output with its input and refuse router-created vias
            in SMD lands), common{...}, waves[]
            {name, nets|group, realized_width (wrapper-owned output contract),
            + any KRT flag override}
  flow:     heartbeat_s, timeouts_s {route_wave, route_race,
            route_evaluate, route_import}; performance budgets are separate

`route --resume` is intentionally single-chain only. It accepts only the
contiguous prefix in route_progress.json whose route.yaml, r0, optional
reviewed route.prefix, per-wave input and output hashes still agree. Bare rN
files are never treated as evidence. A route.prefix is checked against r0 for
base-copper inheritance, physical DRC, and connected critical pairs before it
can skip any wave; stale hashes fail closed.
`route --through-wave NAME` creates that same authenticated prefix as a
deliberate stage pause, writes no FINAL marker, and resumes with `--resume`.
  taps:     clearance, via{}, connections[] {net, from, to, width,
            layer/hop_layer, plane, optional via{} geometry override and
            via_protection{capping,filling}} — see cmd_taps
  stitch:   via{}, keepin{}, passes[] (the ORDER — this is the axis the
            six boards actually disagree on), plus one block per pass;
            protect_via_in_pad can promote every realized barrel centred in
            an SMT land into one declared filled/capped drill family

The `passes` list is deliberately explicit rather than a fixed pipeline:
the survey found the stitch grid running first, middle and LAST across
boards, and it matters (the grid consumes via-exclusion zones that later
rescues must dodge).
"""
import argparse
import hashlib
import json
import math
import os
import re
import shutil
import stat
import sys
import threading
import time
import zlib
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from process_runner import run_bounded


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
    cfg = yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}
    if "project" not in cfg:
        die(f"{path}: no 'project:' block")
    cfg["_path"] = path
    # Support both 03_src/route.yaml and ADR-0007's
    # 03_src/<board>/route.yaml. Resolve from the named stage directory,
    # never by a fixed parent count.
    stage = next((p for p in path.parents if p.name == "03_src"), None)
    if root:
        cfg["_root"] = Path(root).resolve()
    elif stage is not None:
        cfg["_root"] = stage.parent
    else:
        die(f"{path}: route config must live below a 03_src directory or use --root")
    return cfg


def rel(cfg, p):
    p = Path(os.path.expanduser(str(p)))
    return p if p.is_absolute() else (cfg["_root"] / p)


def _target_board(cfg, target_board=None):
    """Resolve a transaction board; explicit overrides stay in build output.

    The configured legacy board retains its existing path behavior.  An
    override is a new write authority and is therefore narrower: project-
    relative, beneath ``project.build_dir``, no parent traversal, and no
    symlink at any existing component.
    """
    if target_board is None:
        return rel(cfg, cfg["project"]["board"]).resolve()
    raw = Path(str(target_board))
    if raw.is_absolute():
        die("--target-board must be project-relative, not absolute")
    if ".." in raw.parts:
        die("--target-board may not traverse outside the project")
    root = Path(cfg["_root"]).resolve()
    current = root
    for part in raw.parts:
        if part in {"", "."}:
            continue
        current = current / part
        if current.is_symlink():
            die(f"--target-board may not traverse symlink: {current}")
    target = (root / raw).resolve(strict=False)
    build = rel(cfg, get(cfg, "project.build_dir", "06_build/route"))
    try:
        build = build.resolve(strict=False)
        build.relative_to(root)
    except ValueError:
        die("project.build_dir must resolve inside the declared project workspace")
    live_board = rel(cfg, cfg["project"]["board"]).resolve(strict=False)
    if live_board == build or live_board.is_relative_to(build):
        die("project.build_dir may not contain the configured live board")
    try:
        target.relative_to(build)
    except ValueError:
        die("--target-board must resolve beneath project.build_dir")
    if target == live_board:
        die("--target-board may not name the configured live board")
    if target.exists():
        try:
            identity = target.lstat()
            if not stat.S_ISREG(identity.st_mode):
                die("--target-board must be an independent regular file")
            if identity.st_nlink != 1:
                die("--target-board must be an independent regular file, not a hardlink")
        except OSError as exc:
            die(f"--target-board link identity could not be verified: {exc}")
    if target.exists() and live_board.exists():
        try:
            if os.path.samefile(target, live_board):
                die("--target-board may not alias the configured live board")
        except OSError as exc:
            die(f"--target-board identity could not be verified: {exc}")
    return target


def get(cfg, dotted, default=None):
    node = cfg
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    return node


def record_pass_timing(cfg, command, name, elapsed, rc=0, counters=None):
    """Append one cheap timing sample to pcb_flow's shared performance log.

    The stitch process re-execs across SWIG barriers, so in-memory profilers
    lose precisely the slow/failure-prone boundary we care about.  Persisting
    after every pass keeps the trace useful after a crash and lets a handoff
    report where wall time actually went.  Timing is observational only: a
    logging failure is printed and never changes board geometry or gate state.
    """
    import datetime
    import json
    config_path = cfg.get("_path")
    nested = bool(config_path and config_path.parent != cfg["_root"] / "03_src")
    state_default = (Path("06_build") / config_path.parent.name
                     if nested else Path("06_build"))
    state = get(cfg, "flow.paths.state_dir", state_default)
    path = rel(cfg, state) / "performance.json"
    try:
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        else:
            data = {"schema": 1, "runs": []}
        if data.get("schema") != 1 or not isinstance(data.get("runs"), list):
            raise ValueError("unsupported performance schema")
        row = {
            "at": datetime.datetime.now(datetime.timezone.utc).isoformat(
                timespec="seconds"),
            "stage": f"{command}:{name}",
            "seconds": round(float(elapsed), 3),
            "rc": int(rc),
            "command": f"route_and_stitch_generic.py {command} [{name}]",
        }
        if counters:
            row["counters"] = counters
        data["runs"].append(row)
        data["runs"] = data["runs"][-200:]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n")
    except Exception as exc:  # observation must never mutate the verdict
        print(f"WARNING: could not record {command}:{name} timing: {exc}")


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
            d = yaml.safe_load(p.read_text(encoding="utf-8-sig")) or {}
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
        d = json.loads(pro.read_text(encoding="utf-8-sig"))
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


def _critical_route_gate(cfg, require_connected=False, board=None):
    """Make the shared route entry points enforce the adopted pair contract."""
    root = Path(cfg["_root"])
    route = get(cfg, "route", {}) or {}
    adopted = any((root / "03_src/rules" / name).is_file()
                  for name in ("requirements.yaml", "integration.yaml"))
    if "preflight_critical_pairs" not in route and not adopted:
        print("R-PAIRMAP: legacy/unadopted route config — not graded")
        return
    checker = Path(__file__).resolve().parent / "critical_route_check.py"
    board = Path(board) if board is not None else rel(
        cfg, cfg["project"]["board"])
    # `route` is intentionally runnable under KRT's virtualenv (numpy, scipy),
    # which normally does not contain KiCad's pcbnew module.  The checker is a
    # board reader and therefore belongs to the explicitly configured KiCad
    # interpreter, just like the per-wave geometry guards below.
    kpy = get(cfg, "route.kicad_python", "/usr/bin/python3")
    cmd = [kpy, str(checker), str(root), "--board", str(board)]
    if require_connected:
        cmd.append("--require-connected")
    result = run_bounded(
        cmd, timeout_s=_timeout_s(cfg, "route_preflight", 180),
        heartbeat_s=_heartbeat_s(cfg), label="critical-route-preflight",
        state_path=rel(cfg, get(cfg, "project.build_dir", "06_build/route")) /
        "critical_route_state.json")
    if result.returncode:
        phase = "R-CRITESC" if require_connected else "R-PAIRMAP"
        die(f"{phase} failed — direct route/import/stitch entry cannot bypass "
            "the adopted critical-pair contract")


def cmd_prep(cfg):
    _critical_route_gate(cfg)
    import pcbnew
    src = rel(cfg, cfg["project"]["board"])
    build = rel(cfg, get(cfg, "project.build_dir", "06_build/route"))
    out = build / get(cfg, "prep.out", "r0.kicad_pcb")
    out.parent.mkdir(parents=True, exist_ok=True)

    # M-REPRO: prep adds keepout shapes and can add deterministic seed/rescue
    # copper. KiCad otherwise assigns every one a fresh random UUID, so two
    # geometrically identical prep runs have different r0 hashes. That is not
    # cosmetic here: route_progress authenticates the exact r0 SHA and a fresh
    # prep then makes a valid bounded route impossible to resume. Reuse KiCad's
    # own QA seed hook, namespaced by the source board just as the board
    # generator does. Creation order is deterministic and the source board's
    # existing objects retain their identities.
    uuid_seed = zlib.crc32(f"{src.stem}:route-prep".encode())
    pcbnew.KIID.SeedGenerator(uuid_seed)
    print(f"UUID generator seeded: crc32('{src.stem}:route-prep') = "
          f"{uuid_seed} (M-REPRO r0)")

    b = pcbnew.LoadBoard(str(src))
    copper = list(b.GetTracks())
    segments = [item for item in copper if item.GetClass() != "PCB_VIA"]
    source_vias = [item for item in copper if item.GetClass() == "PCB_VIA"]
    if segments:
        die(f"route-prep expects a SEGMENT-FREE board, found {len(segments)} "
            f"routed copper item(s) in {src.name} — KRT routes straight "
            f"through existing segments (400+ silent crossings, observed "
            f"twice)")
    if source_vias:
        print(f"source-owned vias: {len(source_vias)} preserved as KRT obstacles")
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

    # Some dense high-speed launches need deterministic, reviewed geometry
    # to exist BEFORE KRT sees the board (for example, two coupled pair banks
    # deliberately assigned to different copper layers).  Reuse the same
    # collision-refusing/idempotent seed emitter that stitch uses, but run it
    # on r0 so every later routing wave treats that copper as an obstacle.
    # Keeping this config-backed avoids a per-board Python pre-router and makes
    # the exact geometry part of the reproducible route recipe.
    preseed = get(cfg, "prep.seed_stubs") or {}
    ctx = None
    if preseed.get("stubs"):
        ctx = Ctx(cfg, out)
        p_seed_stubs(ctx, preseed)
        if ctx.failures:
            die("prep.seed_stubs refused deterministic pre-route copper:\n  "
                + "\n  ".join(ctx.failures))
        ctx.board.Save(str(out))
        print(f"prep seed_stubs: {ctx.counts.get('seed_stubs', 0)} "
              "segments/vias placed before KRT")

    # Plane drops are routing INPUTS, not post-route cleanup.  Running the
    # collision-checked pad rescue only after KRT lets dense signal/power waves
    # consume the last legal via+stub sites around small GND/plane pads; the
    # subsequent pour then isolates those pads and every reroute can expose a
    # different weakest island.  `prep.pad_rescue: true` reuses the exact
    # stitch.pad_rescue policy on the track-free r0 so KRT sees every accepted
    # barrel/stub as an obstacle.  A mapping overlays the stitch policy when a
    # board needs an early-only override.  This remains declarative and the
    # normal post-route pad_rescue stays as the verification/safety net.
    early = get(cfg, "prep.pad_rescue")
    if early:
        if early is True:
            early_cfg = dict(get(cfg, "stitch.pad_rescue", {}) or {})
        elif isinstance(early, dict):
            early_cfg = dict(get(cfg, "stitch.pad_rescue", {}) or {})
            early_cfg.update(early)
        else:
            die("prep.pad_rescue must be true or a mapping of "
                "stitch.pad_rescue overrides")
        _stitch_tier_geometry(cfg)
        if ctx is None:
            ctx = Ctx(cfg, out)
        before = len(list(ctx.board.GetTracks()))
        p_pad_rescue(ctx, early_cfg)
        if ctx.failures:
            die("prep.pad_rescue refused deterministic pre-route copper:\n  "
                + "\n  ".join(ctx.failures))
        ctx.board.Save(str(out))
        added = len(list(ctx.board.GetTracks())) - before
        print(f"prep pad_rescue: {added} copper items placed before KRT; "
              f"{len(ctx.pending)} pad(s) left for the post-route fallback")

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
# EVERY KRT CAPABILITY THIS DRIVER CANNOT NAME IS A CAPABILITY THE PIPELINE DOES
# NOT HAVE. A key absent from this map is not a soft limitation: `_krt_args`
# hard-dies on it (t_kb_unknown_krt_flag), so a `route.yaml` that needs it
# cannot be written at all, and the only way to get the route is BY HAND — which
# is a canon-M3 violation (nothing under 03_src/ regenerates it) wearing a green
# DRC gate. That is exactly what happened on pluto-rx2-8way, 2026-07-29: the
# nine-arm AoA board whose entire release value IS phase match had to be routed
# by hand with `--length-match-group`, and the agent correctly REFUSED to promote
# the chain file because the recipe was unexpressible. Five keys were missing:
#
#   neckdown_length / neckdown_taper_length — the answer to a launch whose
#     vendor land cannot carry the impedance width. MEASURED on PE42482A-X:
#     the 0.60 x 0.30 mm land at 0.50 mm pitch puts a GND land edge 0.350 mm
#     off the RF centreline; a 0.36 mm trace needs 0.180 + 0.200 = 0.380 mm,
#     deficit 0.030 mm, so 6 of 11 rf nets routed and the five pins with GND on
#     BOTH flanks (ANT2/3/6/7, RX2_OUT) failed. Max landable width is the pad
#     width itself, 0.30 mm = 55.3 ohm, which FAILS the RF50_width floor. The
#     alternative — relaxing clearance to <= 0.17 mm — was refused for a
#     measured reason: the stitch fence would then sit 0.15-0.17 mm from a
#     0.36 mm arm (g/h ~ 0.8) and detune the pure-microstrip 50.5 ohm the width
#     was derived from. A neck-down + taper is the intended answer.
#   length_match_group / length_match_tolerance / meander_amplitude — KRT DOES
#     do SINGLE-ENDED INTER-NET length matching, contrary to what this repo
#     asserted twice before anyone ran the flag. MEASURED, same session:
#     `--length-match-group 'ANT*' 'RX2_OUT' --length-match-tolerance 0.15`
#     printed "8 nets (0 diff pairs, 8 single-ended), target=19.83mm" and took
#     the group spread 2.237 -> 1.1586 mm (29.5 -> 15.28 deg at 13.19 deg/mm),
#     11/11 routed, 0 failed, min_clearance_used 0.2 — NO clearance relaxation
#     anywhere. The residual is the tolerance that was passed in, not a floor.
#
# `--length-match-group` is argparse `action="append", nargs="+"`, so it is
# REPEATABLE and each occurrence is one group. `grouplist` renders both shapes:
# a flat list of patterns is ONE group; a list of lists is one flag per group.
_KRT_FLAGMAP = {
    "ordering": ("--ordering", "val"),
    "layers": ("--layers", "list"),
    "layer_costs": ("--layer-costs", "list"),
    "clearance": ("--clearance", "val"),
    "board_edge_clearance": ("--board-edge-clearance", "val"),
    "hole_to_hole_clearance": ("--hole-to-hole-clearance", "val"),
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
    "neckdown_length": ("--neckdown-length", "val"),
    "neckdown_taper_length": ("--neckdown-taper-length", "val"),
    "length_match_group": ("--length-match-group", "grouplist"),
    "length_match_tolerance": ("--length-match-tolerance", "val"),
    "meander_amplitude": ("--meander-amplitude", "val"),
    "no_stub_layer_swap": ("--no-stub-layer-swap", "flag"),
    "no_power_tap_neckdown": ("--no-power-tap-neckdown", "flag"),
    "keepout": ("--keepout", "flag"),
}


def _krt_args(d, extra_flags=None):
    flagmap = dict(_KRT_FLAGMAP)
    flagmap.update(extra_flags or {})
    out = []
    for k, v in d.items():
        if k in ("name", "nets", "group", "engine"):
            continue
        if k not in flagmap:
            die(f"unknown KRT option {k!r} — extend _KRT_FLAGMAP rather than "
                f"guessing a flag name")
        flag, kind = flagmap[k]
        if kind == "flag":
            if v:
                out.append(flag)
        elif kind == "list":
            out.append(flag)
            out += [str(x) for x in v]
        elif kind == "grouplist":
            # a REPEATABLE nargs='+' flag: one occurrence per group. A flat
            # list of strings is one group (the common case); a list of lists
            # is several. Anything else is a config error, not a coercion —
            # a mis-shaped group that silently became one flag would route
            # with the WRONG matching set and say nothing.
            if not isinstance(v, (list, tuple)) or not v:
                die(f"{k!r} must be a non-empty list of net patterns, or a "
                    f"list of such lists (one per group), got {v!r}")
            groups = v if isinstance(v[0], (list, tuple)) else [v]
            for g in groups:
                if not isinstance(g, (list, tuple)) or not g or \
                        not all(isinstance(x, str) for x in g):
                    die(f"{k!r}: each group must be a non-empty list of net "
                        f"pattern STRINGS, got {g!r}")
                out.append(flag)
                out += [str(x) for x in g]
        else:
            out += [flag, str(v)]
    return out


def _wave_chain(cfg, py, krt, waves, tier, common, workdir, cur, env=None,
                tag="", start_wave=1, stop_wave=None, progress=None,
                cancel_event=None, prepared=None):
    """Run the chained KRT waves rN -> rN+1 inside `workdir`, starting from
    board `cur`. Returns the final chain file. `env` extends the subprocess
    environment (race candidates get ROUTE_RACE_CANDIDATE)."""
    sub_env = dict(os.environ, **(env or {}))
    prepared = Path(prepared) if prepared is not None else Path(workdir) / get(
        cfg, "prep.out", "r0.kicad_pcb")
    for i, wv in enumerate(waves, 1):
        if i < start_wave:
            continue
        if stop_wave is not None and i > stop_wave:
            break
        name = wv.get("name", f"w{i}")
        nets = wv.get("nets")
        if nets is None:
            grp = wv.get("group", name)
            f = workdir / f"nets_{grp}.txt"
            if not f.is_file():
                die(f"wave {name!r}: {f} missing — run `prep` first")
            nets = f.read_text(encoding="utf-8-sig").split()
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
        # Wrapper-owned postcondition: do not pass this to KRT.  The command
        # line can request one width while later router cleanup emits another;
        # only the realized board is authoritative.
        realized_width = opts.pop("realized_width", None)
        if realized_width is not None:
            if not isinstance(realized_width, dict):
                die(f"wave {name!r}: realized_width must be a mapping")
            required = {"nominal", "minimum",
                        "max_subnominal_length_per_net",
                        "max_subnominal_segments_per_net"}
            unknown = set(realized_width) - required
            missing = required - set(realized_width)
            if unknown or missing:
                die(f"wave {name!r}: realized_width keys must be exactly "
                    f"{sorted(required)}; missing={sorted(missing)}, "
                    f"unknown={sorted(unknown)}")
            try:
                realized_width = {
                    "nominal": float(realized_width["nominal"]),
                    "minimum": float(realized_width["minimum"]),
                    "max_subnominal_length_per_net": float(
                        realized_width["max_subnominal_length_per_net"]),
                    "max_subnominal_segments_per_net": int(
                        realized_width["max_subnominal_segments_per_net"]),
                }
            except (TypeError, ValueError):
                die(f"wave {name!r}: realized_width values must be numeric")
            if (realized_width["minimum"] <= 0
                    or realized_width["nominal"] < realized_width["minimum"]
                    or realized_width["max_subnominal_length_per_net"] < 0
                    or realized_width["max_subnominal_segments_per_net"] < 0):
                die(f"wave {name!r}: invalid realized_width bounds: "
                    f"{realized_width}")
        engine = str(opts.pop("engine", "single")).strip().lower()
        if engine not in ("single", "diff"):
            die(f"wave {name!r}: engine must be 'single' or 'diff', got {engine!r}")
        if engine == "diff":
            # route_diff.py owns coupled _P/_N geometry.  Unlike route.py it
            # does not consume single-ended power-net options.  It DOES own
            # the shared fab-tier flags now; retain fab_tier/fab_overrides so
            # emission-time neck floors use the same manufacturing authority
            # as this wrapper and the generated DRC rules.
            for unsupported in ("power_nets", "power_nets_widths",
                                "no_power_tap_neckdown"):
                opts.pop(unsupported, None)
        router_script = "route_diff.py" if engine == "diff" else "route.py"
        # route_diff.py has a small engine-specific argparse surface which
        # route.py intentionally does not share.  Keep those flags here rather
        # than in _KRT_FLAGMAP so the flagmap-vs-route.py contract remains
        # exact and a single-ended wave cannot accidentally request them.
        diff_flags = ({
            "diff_pair_gap": ("--diff-pair-gap", "val"),
            "diff_pair_intra_match": ("--diff-pair-intra-match", "flag"),
        } if engine == "diff" else None)
        cmd = ([py, str(krt / router_script), str(cur), "--output", str(nxt)]
               + _krt_args(opts, diff_flags) + ["--nets"] + list(nets))
        print(f"\n=== {tag}wave {name} ({engine}): {len(nets)} nets ===\n  "
              + " ".join(cmd[:2] + ["..."] + cmd[-min(6, len(nets) + 1):]))
        result = run_bounded(
            cmd, env=sub_env, timeout_s=_timeout_s(cfg, "route_wave", 900),
            heartbeat_s=_heartbeat_s(cfg), label=f"{tag}route:{name}".strip(),
            state_path=workdir / f"wave_{i}_state.json",
            cancel_event=cancel_event)
        # Race lanes are concurrent and have their own race_log.json; avoid
        # concurrent writers to the shared performance file.  The normal
        # single chain records each wave here.
        if not tag:
            record_pass_timing(cfg, "route", name,
                               result.elapsed_s,
                               rc=result.returncode,
                               counters={"nets": len(nets), "wave": i})
        if result.returncode != 0:
            die(f"KRT wave {name!r} exited {result.returncode}")
        if not nxt.is_file():
            die(f"KRT wave {name!r} produced no {nxt}")
        summaries = [line.split("JSON_SUMMARY:", 1)[1].strip()
                     for line in result.output.splitlines()
                     if "JSON_SUMMARY:" in line]
        decoded_summaries = []
        for raw_summary in summaries:
            try:
                decoded_summaries.append(json.loads(raw_summary))
            except json.JSONDecodeError as exc:
                die(f"KRT wave {name!r} emitted malformed JSON_SUMMARY: "
                    f"{exc}")

        # route.py exits zero after writing its best candidate even when one
        # or more requested nets remain open.  Partial-stage KiCad DRC also
        # deliberately defers opens, so neither return code nor physical DRC
        # can authenticate wave completeness.  Reconcile every emitted
        # summary in order: a later final-reconciliation pass may explicitly
        # recover a net that failed in the first pass (for example a boxed
        # multipoint supply), but an unresolved failure must stop promotion.
        unresolved = set()
        frontier = []
        for summary in decoded_summaries:
            recovered = {str(v) for v in (summary.get("routed_single") or [])}
            unresolved.difference_update(recovered)
            unresolved.update(str(v) for v in
                              (summary.get("failed_single") or []))
            for item in summary.get("failed_multipoint") or []:
                if isinstance(item, dict) and item.get("net_name"):
                    unresolved.add(str(item["net_name"]))
                    frontier.append(item)
        if unresolved:
            last = decoded_summaries[-1] if decoded_summaries else {}
            operations = {
                "requested": len(nets),
                "queued": max(int(last.get(key, 0) or 0) for key in
                              ("queued", "queued_operations", "operations")),
                "ripups": max(int(last.get(key, 0) or 0) for key in
                              ("ripups", "ripup_count")),
            }
            decision = (None if tag else _route_progress_observe(
                cfg, workdir, i, name, unresolved, frontier, operations))
            suffix = (f"; exploration={decision['decision']}: "
                      f"{decision['reason']}" if decision else "")
            die(f"KRT wave {name!r} left requested net(s) unresolved despite "
                "exit 0: " + ", ".join(sorted(unresolved)) + suffix)

        if engine == "diff":
            if decoded_summaries:
                summary = decoded_summaries[-1]
                skipped = summary.get("skipped_bad_fanout") or []
                if skipped:
                    die(f"KRT wave {name!r} skipped {len(skipped)} requested "
                        "differential pair(s) after its fanout precheck: "
                        + ", ".join(str(v) for v in skipped))
                deferred = summary.get("single_ended_diff_pairs") or []
                failed_pairs = summary.get("failed_diff_pairs") or []
                if deferred or failed_pairs:
                    detail = []
                    if deferred:
                        detail.append("deferred=" + ",".join(str(v) for v in deferred))
                    if failed_pairs:
                        detail.append("failed=" + ",".join(str(v) for v in failed_pairs))
                    die(f"KRT wave {name!r} did not coupled-route every requested "
                        "differential pair (" + "; ".join(detail) + ")")
        if realized_width is not None:
            guard = (Path(__file__).resolve().parent
                     / "realized_track_width_guard.py")
            report = workdir / f"wave_{i}_realized_track_width.json"
            kpy = get(cfg, "route.kicad_python", "/usr/bin/python3")
            checked = run_bounded(
                [kpy, str(guard), str(nxt), "--nets", *list(nets),
                 "--nominal-width", str(realized_width["nominal"]),
                 "--min-width", str(realized_width["minimum"]),
                 "--max-subnominal-length-per-net",
                 str(realized_width["max_subnominal_length_per_net"]),
                 "--max-subnominal-segments-per-net",
                 str(realized_width["max_subnominal_segments_per_net"]),
                 "--json", str(report)],
                timeout_s=_timeout_s(cfg, "route_wave_gate", 60),
                heartbeat_s=_heartbeat_s(cfg),
                label=f"{tag}route:{name}:realized-width".strip(),
                state_path=workdir / f"wave_{i}_realized_width_state.json",
                cancel_event=cancel_event, echo=False)
            if checked.returncode != 0:
                detail = checked.output[-1600:].strip()
                die(f"KRT wave {name!r} violated its realized_width "
                    f"contract; report: {report}"
                    + (f"\n{detail}" if detail else ""))
        # Some routers escape a boxed SMD endpoint by dropping an ordinary
        # via directly in its land.  That can look connected while violating
        # the board's assembly/reliability contract (solder wicking, uncapped
        # hole).  When enabled, compare EACH wave to its exact input and stop
        # at the first newly-created via-in-pad.  Source-owned vias present in
        # `cur` remain allowed, so an explicitly authored filled/capped EP
        # field is not confused with an autorouter shortcut.
        if get(cfg, "route.forbid_new_via_in_pad", False):
            guard = Path(__file__).resolve().parent / "via_in_pad_guard.py"
            report = workdir / f"wave_{i}_via_in_pad.json"
            kpy = get(cfg, "route.kicad_python", "/usr/bin/python3")
            checked = run_bounded(
                [kpy, str(guard), str(cur), str(nxt), "--json", str(report)],
                timeout_s=_timeout_s(cfg, "route_wave_gate", 60),
                heartbeat_s=_heartbeat_s(cfg),
                label=f"{tag}route:{name}:via-in-pad".strip(),
                state_path=workdir / f"wave_{i}_via_in_pad_state.json",
                cancel_event=cancel_event, echo=False)
            if checked.returncode != 0:
                detail = checked.output[-1200:].strip()
                die(f"KRT wave {name!r} added forbidden via-in-pad geometry; "
                    f"report: {report}" + (f"\n{detail}" if detail else ""))
        # KRT preserves the .kicad_pro today, but it does not consistently
        # carry the custom .kicad_dru beside each output.  KiCad resolves a
        # board's custom rules by BASENAME, so quick DRC on rN.kicad_pcb
        # silently loses every generated width floor when rN.kicad_dru is
        # absent.  Copy both rule sidecars from the exact wave input after
        # every successful route.  Overwrite deliberately: a stale rN sidecar
        # from an earlier grind is worse than no sidecar because it appears to
        # be authoritative while grading different source rules.
        for ext in (".kicad_pro", ".kicad_dru"):
            src_rules = cur.with_suffix(ext)
            if src_rules.is_file():
                shutil.copy2(src_rules, nxt.with_suffix(ext))
        _wave_drc_gate(
            cfg, nxt, f"{tag}route:{name}:physical-drc".strip(),
            workdir / f"wave_{i}_physical_drc.json")
        # The legacy per-wave gates above remain as fast local defence.  An
        # opted-in board additionally grades the candidate in a fresh basename
        # using r0's exact sidecars; candidate-owned sidecars can never produce
        # a promotable verdict. Race lanes defer this heavier transaction to
        # the measured winner so N concurrent candidates do not multiply it.
        if not tag:
            _grade_route_candidate(
                cfg, workdir, prepared, nxt,
                _wave_net_inventory(waves, i, workdir), f"wave-{i}-{name}",
                touched_nets=list(nets), mutation_baseline=cur)
            _route_progress_observe(
                cfg, workdir, i, name, [], [],
                {"requested": len(nets), "queued": len(nets), "ripups": 0})
        if progress is not None:
            progress.setdefault("waves", []).append({
                "index": i, "name": name,
                "input": os.path.relpath(cur, workdir),
                "input_sha256": _sha256(cur),
                "output": os.path.relpath(nxt, workdir),
                "output_sha256": _sha256(nxt),
                "elapsed_s": round(result.elapsed_s, 3),
            })
            _atomic_json(workdir / "route_progress.json", progress)
        cur = nxt
    return cur


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _seed_uuid_stream(pcbnew, board_stem, phase):
    """Seed KiCad object identities for one deterministic pipeline phase.

    Board generation and route preparation already seed their UUID streams,
    but imported KRT copper, optional taps and stitch/fence vias are created
    by later processes.  Leaving any of those streams random changes KiCad's
    save order and can perturb filled-zone tessellation, so a clean replay no
    longer reproduces its own board/fabrication bytes.  A phase namespace also
    prevents separate writers from drawing the same UUID sequence.
    """
    namespace = f"{board_stem}:{phase}"
    seed = zlib.crc32(namespace.encode())
    pcbnew.KIID.SeedGenerator(seed)
    print(f"UUID generator seeded: crc32('{namespace}') = {seed} "
          f"(M-REPRO {phase})")
    return seed


def _atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temp, path)


def _control_spec(value, key, allowed):
    """Normalize one opt-in route control without changing legacy configs."""
    if value is False or value is None:
        return None
    if value is True:
        return {"mode": "enforce"}
    if not isinstance(value, dict):
        die(f"route.{key} must be true/false or a mapping")
    unknown = set(value) - set(allowed) - {"mode"}
    if unknown:
        die(f"route.{key} has unknown key(s): {sorted(unknown)}")
    mode = str(value.get("mode", "enforce")).lower()
    if mode not in ("observe", "enforce"):
        die(f"route.{key}.mode must be observe or enforce")
    return dict(value, mode=mode)


def _wave_net_inventory(waves, through, workdir):
    nets = set()
    for index, wave in enumerate(waves[:through], 1):
        members = wave.get("nets")
        if members is None:
            group = wave.get("group", wave.get("name", f"w{index}"))
            path = Path(workdir) / f"nets_{group}.txt"
            if not path.is_file():
                die(f"candidate grading cannot resolve wave {index} nets: {path}")
            members = path.read_text(encoding="utf-8-sig").split()
        nets.update(str(net) for net in members)
    return sorted(nets)


def _candidate_authority_sha(r0):
    digest = hashlib.sha256()
    for path in (Path(r0), Path(r0).with_suffix(".kicad_pro"),
                 Path(r0).with_suffix(".kicad_dru")):
        if not path.is_file():
            die(f"candidate grading authority missing: {path}")
        digest.update(bytes.fromhex(_sha256(path)))
    return digest.hexdigest()


def _grade_route_candidate(cfg, build, r0, candidate, required_nets, label,
                           *, touched_nets=None, mutation_baseline=None):
    """Run the shared immutable-workspace grader when the board opts in."""
    spec = _control_spec(
        get(cfg, "route.candidate_grade", False), "candidate_grade",
        {"shadow_native_drc", "shadow_semantic_copper",
         "semantic_copper_timeout_s"})
    if spec is None:
        return None
    from route_candidate_workspace import grade_candidate, verify_receipt

    r0, candidate, build = Path(r0), Path(candidate), Path(build)
    required_nets = sorted(set(str(net) for net in required_nets))
    touched_nets = sorted(set(str(net) for net in (touched_nets or [])))
    mutation_baseline = (Path(mutation_baseline)
                         if mutation_baseline is not None else None)
    stem = (f"{re.sub(r'[^A-Za-z0-9_.-]+', '-', label)}-"
            f"{_sha256(candidate)[:12]}-{_candidate_authority_sha(r0)[:12]}")
    base = build / "candidate_grades" / stem
    workspace = base
    suffix = 1
    # A receipt self-digest is tamper evidence, not an authorization token.
    # Never skip authoritative tools by replaying an existing workspace.
    while workspace.exists():
        suffix += 1
        workspace = Path(f"{base}-run{suffix}")

    receipt = grade_candidate(
        r0, candidate, workspace, required_nets=required_nets,
        touched_nets=touched_nets, mutation_baseline=mutation_baseline,
        shadow_native_drc=bool(spec.get("shadow_native_drc", False)),
        shadow_semantic_copper=bool(
            spec.get("shadow_semantic_copper", False)),
        semantic_copper_timeout_s=int(
            spec.get("semantic_copper_timeout_s", 120)),
        kicad_python=get(cfg, "route.kicad_python", "/usr/bin/python3"))
    valid, failures = verify_receipt(workspace / "receipt.json")
    if not valid:
        message = (f"{label}: candidate receipt failed independent verification: "
                   + "; ".join(failures))
        if spec["mode"] == "enforce":
            die(message)
        print("WARNING: " + message + " (observe mode; legacy behavior retained)")
        return receipt
    print(f"{label}: immutable candidate {receipt['verdict']} -> "
          f"{workspace / 'receipt.json'}")
    if receipt["verdict"] != "ACCEPTED":
        message = (f"{label}: authoritative candidate grading returned "
                   f"{receipt['verdict']}; inspect {workspace / 'receipt.json'}")
        if spec["mode"] == "enforce":
            die(message)
        print("WARNING: " + message + " (observe mode; legacy behavior retained)")
    return receipt


def _route_ownership_gate(cfg, build):
    spec = _control_spec(
        get(cfg, "route.ownership_preflight", False),
        "ownership_preflight", set())
    if spec is None:
        return
    script = Path(__file__).resolve().parent / "route_ownership_preflight.py"
    report = Path(build) / "route_ownership.json"
    checked = run_bounded(
        [get(cfg, "route.kicad_python", "/usr/bin/python3"), str(script),
         str(cfg["_path"]), "--json", str(report)],
        timeout_s=_timeout_s(cfg, "route_preflight", 180),
        heartbeat_s=_heartbeat_s(cfg), label="route:ownership-preflight",
        state_path=Path(build) / "route_ownership_state.json", echo=False)
    if checked.returncode:
        message = (f"route ownership preflight exited {checked.returncode}; "
                   f"report: {report}\n{checked.output[-1400:].strip()}")
        if spec["mode"] == "enforce":
            die(message)
        print("WARNING: " + message + "\nobserve mode retains legacy routing")
    else:
        print(f"route ownership preflight: PASS/N-A -> {report}")


def _route_progress_observe(cfg, workdir, wave_index, wave_name, unresolved,
                            frontier, operations):
    spec = _control_spec(
        get(cfg, "route.exploration_guard", False), "exploration_guard",
        {"plateau_attempts", "max_attempts", "max_novel_signatures",
         "max_operation_amplification"})
    if spec is None:
        return None
    from route_progress_guard import observe

    progress = Path(workdir) / "route_progress.json"
    progress_doc = (json.loads(progress.read_text(encoding="utf-8-sig"))
                    if progress.is_file() else {})
    subject = (f"{progress_doc.get('r0_sha256', 'unknown')}:"
               f"{progress_doc.get('config_sha256', _sha256(cfg['_path']))}:"
               f"{wave_index}:{wave_name}")
    observation = {
        "subject": subject,
        "unresolved": sorted(unresolved),
        "hard_findings": [],
        "frontier": frontier,
        "operations": operations,
    }
    state_path = Path(workdir) / "exploration" / f"wave_{wave_index}.json"
    result_path = state_path.with_name(f"wave_{wave_index}_decision.json")
    try:
        previous = (json.loads(state_path.read_text(encoding="utf-8-sig"))
                    if state_path.is_file() else None)
        state, result = observe(
            observation, previous,
            plateau_attempts=int(spec.get("plateau_attempts", 2)),
            max_attempts=int(spec.get("max_attempts", 5)),
            max_novel_signatures=int(spec.get("max_novel_signatures", 3)),
            max_operation_amplification=float(
                spec.get("max_operation_amplification", 8.0)))
        _atomic_json(state_path, state)
        _atomic_json(result_path, result)
    except Exception as exc:
        if spec["mode"] == "enforce":
            die(f"route exploration guard incomplete: {exc}")
        print(f"WARNING: route exploration guard incomplete: {exc}")
        return None
    print(f"route exploration: {result['decision']} — {result['reason']} -> "
          f"{result_path}")
    return result


_DEFAULT_WAVE_DRC_HARD_TYPES = {
    "annular_width", "board_edge", "clearance", "copper_edge_clearance",
    "diff_pair_uncoupled_length_too_long", "drill_out_of_range",
    "hole_clearance", "hole_to_hole", "shorting_items", "track_width",
    "through_hole_pad_without_hole", "via_diameter", "via_in_pad",
}


def _wave_drc_gate(cfg, board, label, report):
    """Fail a route checkpoint on physical DRC, while allowing partial opens.

    A route wave is intentionally incomplete, so dangling tracks/vias,
    unconnected items and standalone-library context cannot gate it.  Shorts,
    clearances, width, holes, edges and differential-coupling limits can never
    be repaired by a later unrelated wave and therefore authenticate here.
    """
    spec = get(cfg, "route.wave_drc", False)
    if not spec:
        return
    if spec is True:
        hard = set(_DEFAULT_WAVE_DRC_HARD_TYPES)
    elif isinstance(spec, dict):
        unknown = set(spec) - {"enabled", "hard_types"}
        if unknown:
            die(f"route.wave_drc has unknown key(s): {sorted(unknown)}")
        if not spec.get("enabled", True):
            return
        values = spec.get("hard_types", sorted(_DEFAULT_WAVE_DRC_HARD_TYPES))
        if not isinstance(values, list) or not all(
                isinstance(value, str) and value for value in values):
            die("route.wave_drc.hard_types must be a list of non-empty strings")
        hard = set(values)
    else:
        die("route.wave_drc must be true/false or a mapping")

    board, report = Path(board), Path(report)
    checked = run_bounded(
        ["kicad-cli", "pcb", "drc", "--severity-all", "--format", "json",
         "-o", str(report), str(board)],
        timeout_s=_timeout_s(cfg, "route_wave_gate", 180),
        heartbeat_s=_heartbeat_s(cfg), label=label,
        state_path=report.with_name(report.stem + "_state.json"), echo=False)
    # kicad-cli returns non-zero when it finds violations; the JSON is the
    # authoritative classified result.  A missing/unreadable report is a tool
    # failure and must not be mistaken for a clean board.
    if not report.is_file():
        die(f"{label}: kicad-cli wrote no DRC report (exit "
            f"{checked.returncode}): {checked.output[-800:]}")
    try:
        payload = json.loads(report.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        die(f"{label}: unreadable DRC report {report}: {exc}")
    hits = [row for row in payload.get("violations", [])
            if row.get("type") in hard]
    if hits:
        counts = {}
        for row in hits:
            counts[row.get("type", "unknown")] = \
                counts.get(row.get("type", "unknown"), 0) + 1
        sample = str(hits[0].get("description", ""))[:300]
        die(f"{label}: physical route DRC FAILED: "
            + ", ".join(f"{name}={count}"
                        for name, count in sorted(counts.items()))
            + f"; first: {sample}; report: {report}")
    print(f"{label}: PASS — zero hard physical DRC findings "
          f"({len(payload.get('violations', []))} partial-stage findings "
          f"deferred) -> {report}")


def _heartbeat_s(cfg):
    value = float(get(cfg, "flow.heartbeat_s", 10))
    if value <= 0:
        die("flow.heartbeat_s must be positive")
    return value


def _timeout_s(cfg, stage, default=None):
    value = get(cfg, f"flow.timeouts_s.{stage}",
                get(cfg, "flow.timeouts_s.default", default))
    if value is None:
        return None
    value = float(value)
    if value <= 0:
        die(f"flow.timeouts_s.{stage} must be positive")
    return value


def _race_candidate(cfg, py, krt, waves, tier, common, build, i, results,
                    cancel_event):
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
                            env={"ROUTE_RACE_CANDIDATE": str(i)}, tag=tag,
                            cancel_event=cancel_event, prepared=cdir / r0.name)
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
        r = run_bounded(
            [kpy, str(imp), str(chain), str(ev), str(ev)],
            timeout_s=_timeout_s(cfg, "route_evaluate", 180),
            heartbeat_s=_heartbeat_s(cfg), label=f"c{i}:import",
            state_path=cdir / "import_state.json", cancel_event=cancel_event,
            echo=False)
        if r.returncode != 0:
            die(f"candidate {i}: import_krt exited {r.returncode}: "
                f"{r.output[-300:]}")
        qj = cdir / "quick.json"
        r = run_bounded(
            [kpy, os.path.abspath(__file__), "quick", str(cfg["_path"]),
             "--root", str(cfg["_root"]), "--board", str(ev),
             "--json", str(qj)],
            timeout_s=_timeout_s(cfg, "route_evaluate", 180),
            heartbeat_s=_heartbeat_s(cfg), label=f"c{i}:quick",
            state_path=cdir / "quick_state.json", cancel_event=cancel_event,
            echo=False)
        if not qj.is_file():
            die(f"candidate {i}: quick wrote no JSON (exit {r.returncode}): "
                f"{r.output[-300:]}")
        q = json.loads(qj.read_text(encoding="utf-8-sig"))
        results[i] = {
            "chain": str(chain),
            "unconnected": q["unconnected"]["routed_total"],
            "violations": sum(e["count"]
                              for e in q.get("violations", {}).values()),
            "verdict": q["verdict"],
        }
    except Exception as e:                # noqa: BLE001 — lane-isolated
        results[i] = {"error": str(e)}


def _new_route_progress(cfg, r0, prefix=None):
    progress = {
        "schema": 1, "config": str(cfg["_path"]),
        "config_sha256": _sha256(cfg["_path"]),
        "r0_sha256": _sha256(r0), "waves": [],
    }
    if prefix is not None:
        progress["prefix"] = dict(prefix)
    return progress


def _route_prefix(cfg, build, waves, r0):
    """Authenticate and materialize an optional reviewed wave prefix.

    A dense critical route can be expensive or stochastic to rediscover.  The
    prefix is therefore a source artifact, not a loose build checkpoint: both
    it and the exact prepared base are hash-bound, it must retain every base
    footprint/pad/seed/via, and it must pass physical DRC plus the adopted
    connected-pair contract before any later wave is allowed to consume it.
    """
    spec = get(cfg, "route.prefix")
    if spec is None:
        return 0, r0, None
    if not isinstance(spec, dict):
        die("route.prefix must be a mapping")
    required = {"board", "through_wave", "r0_sha256", "board_sha256"}
    unknown = set(spec) - required
    missing = required - set(spec)
    if unknown or missing:
        die("route.prefix keys must be exactly "
            f"{sorted(required)}; missing={sorted(missing)}, "
            f"unknown={sorted(unknown)}")
    matches = [i for i, wave in enumerate(waves, 1)
               if wave.get("name", f"w{i}") == spec["through_wave"]]
    if len(matches) != 1:
        die(f"route.prefix.through_wave {spec['through_wave']!r} must name "
            "exactly one configured wave")
    through = matches[0]
    expected_r0 = str(spec["r0_sha256"]).lower()
    actual_r0 = _sha256(r0)
    if not re.fullmatch(r"[0-9a-f]{64}", expected_r0):
        die("route.prefix.r0_sha256 must be a lowercase SHA-256 digest")
    if expected_r0 != actual_r0:
        die("route.prefix r0 hash mismatch — prep/source geometry changed; "
            "the reviewed prefix is stale")
    source = rel(cfg, spec["board"]).resolve()
    if not source.is_file():
        die(f"route.prefix board not found: {source}")
    expected_board = str(spec["board_sha256"]).lower()
    actual_board = _sha256(source)
    if not re.fullmatch(r"[0-9a-f]{64}", expected_board):
        die("route.prefix.board_sha256 must be a lowercase SHA-256 digest")
    if expected_board != actual_board:
        die("route.prefix board hash mismatch — reviewed copper changed")

    staged = build / f"r{through}.kicad_pcb"
    if source != staged.resolve():
        shutil.copy2(source, staged)
    # The exact current rules accompany the materialized checkpoint.  A
    # source-side stale .dru must not grade current geometry under old floors.
    for ext in (".kicad_pro", ".kicad_dru"):
        sidecar = r0.with_suffix(ext)
        if sidecar.is_file():
            shutil.copy2(sidecar, staged.with_suffix(ext))

    # P-ROUTEBASE in direct mode proves that the checkpoint retained the
    # exact r0 footprint/pad identity and all deterministic prep copper.
    checker = Path(__file__).resolve().parent / "promoted_route_check.py"
    kpy = get(cfg, "route.kicad_python", "/usr/bin/python3")
    checked = run_bounded(
        [kpy, str(checker), "--prepared", str(r0), "--chain", str(staged)],
        timeout_s=_timeout_s(cfg, "route_preflight", 180),
        heartbeat_s=_heartbeat_s(cfg), label="route-prefix:base",
        state_path=build / "prefix_base_state.json")
    if checked.returncode:
        die("route.prefix does not derive from the exact prepared base "
            "(P-ROUTEBASE failed)")
    _wave_drc_gate(cfg, staged, "route-prefix:physical-drc",
                   build / "prefix_physical_drc.json")
    _critical_route_gate(cfg, require_connected=True, board=staged)
    prefix_nets = _wave_net_inventory(waves, through, build)
    _grade_route_candidate(
        cfg, build, r0, staged, prefix_nets,
        f"prefix-through-{through}", touched_nets=prefix_nets,
        mutation_baseline=r0)
    receipt = {
        "through_index": through,
        "through_wave": spec["through_wave"],
        "source": str(source),
        "source_sha256": actual_board,
        "r0_sha256": actual_r0,
        "materialized": os.path.relpath(staged, build),
        "materialized_sha256": _sha256(staged),
    }
    print(f"route prefix: authenticated through wave {through} "
          f"({spec['through_wave']}) -> {staged}")
    return through, staged, receipt


def _resume_route(cfg, build, waves, r0, prefix_index=0, prefix_board=None,
                  prefix_receipt=None):
    """Return (next wave index, current board, progress), fail closed on drift."""
    path = build / "route_progress.json"
    if not path.is_file():
        die("--resume requested but route_progress.json is missing — existing "
            "rN files have no provenance and cannot be trusted")
    try:
        progress = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        die(f"cannot resume: unreadable {path}: {exc}")
    if progress.get("schema") != 1:
        die(f"cannot resume: unsupported progress schema in {path}")
    if progress.get("config_sha256") != _sha256(cfg["_path"]):
        die("cannot resume: route.yaml changed since the recorded waves")
    if progress.get("r0_sha256") != _sha256(r0):
        die("cannot resume: prep r0 changed since the recorded waves")
    recorded_prefix = progress.get("prefix")
    if recorded_prefix != prefix_receipt:
        die("cannot resume: reviewed route.prefix provenance changed")
    cur = prefix_board if prefix_board is not None else r0
    records = progress.get("waves") or []
    for expected, rec in enumerate(records, prefix_index + 1):
        if rec.get("index") != expected or expected > len(waves):
            die("cannot resume: progress waves are not a contiguous prefix")
        if rec.get("name") != waves[expected - 1].get("name", f"w{expected}"):
            die(f"cannot resume: wave {expected} identity changed")
        output = build / rec.get("output", "")
        if not output.is_file() or _sha256(output) != rec.get("output_sha256"):
            die(f"cannot resume: recorded wave {expected} output is missing or changed")
        if _sha256(cur) != rec.get("input_sha256"):
            die(f"cannot resume: wave {expected} input hash no longer chains")
        cur = output
    return prefix_index + len(records) + 1, cur, progress


def cmd_route(cfg, race=None, skip_preflight=False, resume=False,
              through_wave=None):
    # Invalidate build-lineage promotion at the FIRST route-command boundary,
    # before critical-pair, tier, KRT, wave or r0 validation.  Any failed rerun
    # means the build lineage has no current winner; retaining an old FINAL
    # would let a later `import --route-source build` consume stale copper.
    build = rel(cfg, get(cfg, "project.build_dir", "06_build/route"))
    (build / "FINAL").unlink(missing_ok=True)
    _critical_route_gate(cfg)
    # TIER PREFLIGHT FIRST (refuse-to-route). Four measured crow-rv2 defects
    # (2026-07-23) were tool defaults disagreeing with the declared fab tier
    # — 500+158 phantom clearance findings, 200 shorting + 501 clearance
    # inner-layer via findings, 323/323 vias resized, and a FALSE placement
    # wall from hole_to_copper 0.205 vs the 0.15 board floor — together ~60%
    # of that board's routing stage. No KRT cycle is spent until the config
    # provably agrees with the tier. Escape hatch: --skip-preflight (loud).
    if skip_preflight:
        print("=" * 70 + "\nWARNING: --skip-preflight — routing WITHOUT the "
              "tier-consistency gate.\nEvery config-vs-tier mismatch it would "
              "have caught (phantom clearance\nwalls, via resizing, false "
              "placement walls) will now surface only as\npost-stitch DRC "
              "findings. Run tier_preflight.py standalone before\ntrusting "
              "this route.\n" + "=" * 70)
    else:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from tier_preflight import preflight_route_cfg
        from fab_tier_util import FabTierError
        try:
            rc = preflight_route_cfg(cfg)
        except FabTierError as e:
            die(str(e))
        if rc != 0:
            die("tier preflight FAILED — the routing config disagrees with "
                "the declared fab tier (fixes printed above; details: "
                "tier_preflight.py <project> --explain). Refusing to spend "
                "KRT cycles on a config the DRC gate already rejects. "
                "Escape hatch: route --skip-preflight (loud, discouraged)")
    _route_ownership_gate(cfg, build)
    krt = Path(os.path.expanduser(get(cfg, "route.krt", "~/gits/KiCadRoutingTools")))
    py = get(cfg, "route.python") or str(krt / ".venv" / "bin" / "python")
    if not (krt / "route.py").is_file():
        die(f"KRT not found at {krt} (KiCad has no autorouter; clone "
            f"github drandyhaas/KiCadRoutingTools)")
    common = dict(get(cfg, "route.common", {}) or {})
    waves = get(cfg, "route.waves", []) or []
    if not waves:
        die("route.waves is empty — nothing to route")
    stop_wave = None
    if through_wave is not None:
        matches = [i for i, wave in enumerate(waves, 1)
                   if wave.get("name", f"w{i}") == through_wave]
        if len(matches) != 1:
            die(f"--through-wave {through_wave!r} must name exactly one "
                f"route wave; available: "
                f"{[wave.get('name', f'w{i}') for i, wave in enumerate(waves, 1)]}")
        stop_wave = matches[0]
    # tier-derived geometry: missing via/clearance come from the declared fab
    # tier; explicit sub-floor values are rejected (per-wave overrides too).
    tier = fab_tier(cfg)
    tier_geometry(common, tier, "route.common")

    cur = build / get(cfg, "prep.out", "r0.kicad_pcb")
    if not cur.is_file():
        die(f"{cur} missing — run `prep` first")
    _wave_drc_gate(cfg, cur, "route:r0:physical-drc",
                   build / "r0_physical_drc.json")

    prefix_index, prefix_board, prefix_receipt = _route_prefix(
        cfg, build, waves, cur)
    if stop_wave is not None and stop_wave < prefix_index:
        die(f"--through-wave {through_wave!r} precedes the authenticated "
            f"route.prefix through wave {prefix_index}")

    n = int(race if race is not None else get(cfg, "route.race", 1) or 1)
    if n > 1:
        if prefix_receipt is not None:
            die("route.race is not supported with route.prefix; continue the "
                "authenticated suffix as one deterministic chain")
        if through_wave is not None:
            die("--through-wave is only defined for one deterministic "
                "wave-chain; a stochastic race must run its complete chain")
        if resume:
            die("--resume is only defined for one deterministic wave-chain; "
                "a stochastic race must restart its candidate set")
        return _cmd_route_race(cfg, py, krt, waves, tier, common, build, n)

    if resume:
        start_wave, cur, progress = _resume_route(
            cfg, build, waves, cur, prefix_index, prefix_board,
            prefix_receipt)
        print(f"resume: {start_wave - 1}/{len(waves)} authenticated wave(s); "
              f"continuing from {cur}")
    else:
        cur = prefix_board
        start_wave = prefix_index + 1
        progress = _new_route_progress(cfg, build / get(
            cfg, "prep.out", "r0.kicad_pcb"), prefix_receipt)
        _atomic_json(build / "route_progress.json", progress)
    cur = _wave_chain(cfg, py, krt, waves, tier, common, build, cur,
                      start_wave=start_wave, stop_wave=stop_wave,
                      progress=progress,
                      prepared=build / get(cfg, "prep.out", "r0.kicad_pcb"))
    completed = prefix_index + len(progress.get("waves") or [])
    if completed < len(waves):
        print(f"\nroute pause: {completed}/{len(waves)} authenticated "
              f"wave(s) complete -> {cur}\n"
              "No FINAL marker was written. Continue the exact chain with "
              "`route --resume` (and optionally another --through-wave).")
        return 0
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
    print(f"race: {n} candidate wave-chains, concurrent")
    # A marker from an earlier race must never survive a failed rerun and be
    # mistaken for this run's winner by `import --route-source build`.
    (build / "FINAL").unlink(missing_ok=True)
    results = {}
    cancel_event = threading.Event()
    threads = [threading.Thread(target=_race_candidate,
                                args=(cfg, py, krt, waves, tier, common,
                                      build, i, results, cancel_event),
                                name=f"route-race-c{i}", daemon=True)
               for i in range(n)]
    for t in threads:
        t.start()
    timeout_s = _timeout_s(
        cfg, "route_race",
        (_timeout_s(cfg, "route_wave", 900) or 900) * len(waves) + 360)
    started = time.monotonic()
    heartbeat = _heartbeat_s(cfg)
    next_heartbeat = started + heartbeat
    while any(t.is_alive() for t in threads):
        now = time.monotonic()
        if timeout_s is not None and now - started >= timeout_s:
            cancel_event.set()
            for t in threads:
                t.join(timeout=3)
            alive = [t.name for t in threads if t.is_alive()]
            die(f"route race timed out after {now - started:.1f}s "
                f"(limit {timeout_s:g}s); cancelled all candidates"
                + (f"; threads still unwinding: {alive}" if alive else ""))
        if now >= next_heartbeat:
            done = sum(not t.is_alive() for t in threads)
            print(f"[route-race] heartbeat: {done}/{n} candidates finished, "
                  f"{now - started:.1f}s elapsed")
            next_heartbeat = now + heartbeat
        for t in threads:
            t.join(timeout=0.1)

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
    clean = {i: r for i, r in ok.items()
             if str(r.get("verdict", "")).upper() == "CLEAN"}
    best = (min(clean, key=lambda i: (clean[i]["unconnected"],
                                      clean[i]["violations"], i))
            if clean else None)
    log = {"candidates": {str(i): results[i] for i in sorted(results)},
           "chosen": best,
           "rule": "CLEAN candidates only; then min routed-net unconnected, "
                   "min copper violations, then lowest index"}
    (build / "race_log.json").write_text(json.dumps(log, indent=1) + "\n")
    if best is None:
        die(f"all {n} completed race candidates are DIRTY — refusing to "
            f"promote a least-bad route; inspect {build / 'race_log.json'}")
    chain = Path(ok[best]["chain"])
    r0 = build / get(cfg, "prep.out", "r0.kicad_pcb")
    race_nets = _wave_net_inventory(waves, len(waves), build)
    _grade_route_candidate(
        cfg, build, r0, chain, race_nets,
        f"race-winner-c{best}", touched_nets=race_nets,
        mutation_baseline=r0)
    print(f"race winner: c{best} ({ok[best]['unconnected']} unconnected, "
          f"{ok[best]['violations']} violations) -> {chain}")
    print(f"race log -> {build / 'race_log.json'}")
    (build / "FINAL").write_text(str(chain) + "\n")
    return 0


#: stitch passes that HARD-DIE on a board whose pours are already FILLED, and
#: therefore decide whether `import` may fill. `seed_stubs` is the only member:
#: a stub laid after fill is not flowed around by the pour, so the pin it
#: serves stays open, and the pass refuses rather than emit dead copper.
UNFILLED_PASSES = ("seed_stubs",)


def _import_may_fill(cfg):
    """False when the configured stitch plan places EXPLICIT COPPER before its
    `fill` — then `import` must hand `import_krt.py --no-fill`.

    THE BLOCKER THIS FIXES (2026-07-29, pluto-cal-switch). `import_krt.py` has
    had `--no-fill` since it was written and `cmd_import` never passed it, so
    every board reaching stitch through prep -> route -> import arrived with
    its zones FILLED — and `p_seed_stubs` dies on a filled zone. The backend's
    only EXPLICIT-GEOMETRY surface was therefore unreachable through the
    pipeline: the whole `stitch.seed_stubs` schema, its five fixtures and its
    contract row could only be exercised on a hand-built board. cal-switch —
    whose published artifact IS a phase delta, and which needs its two RF arms
    placed as deterministic copper (measured arm1 = arm2 = 16.080266 mm,
    spread 0.000000 mm, equal in integer nanometres) — could only get there by
    HAND-UNFILLING the board between import and stitch, correctly called that
    a diagnostic rather than a shippable path, and correctly REFUSED to promote
    the chain: a recipe not expressible in `route.yaml` is a canon-M3 violation
    wearing a green gate.

    Named `taps.connections` also place explicit copper between import and
    stitch. A pre-filled zone does not flow around their new segments/vias;
    the stale fill then reports zero-clearance and zero-hole-clearance noise
    until a later refill. Keep it unfilled so quick measures the copper that
    actually exists and stitch's declared `fill` owns the first pour.

    DERIVED, NOT DECLARED — deliberately no new config key. An opt-in
    `import.fill: false` would leave the failure mode alive (configure
    seed_stubs, forget the key, die at stitch); and the fact is already
    written down twice in the config, in `stitch.passes` and in
    `stitch.seed_stubs.stubs`. The condition is NARROW on purpose: only a
    non-empty stub list, in a pass list where `seed_stubs` precedes `fill`.
    Every other board keeps the old post-import filled state byte-for-byte,
    because the pre-`fill` stitch passes were debugged against it.
    """
    if get(cfg, "taps.connections") or []:
        return False
    order = list(get(cfg, "stitch.passes", DEFAULT_PASSES) or [])
    if not (get(cfg, "stitch.seed_stubs.stubs") or []):
        return True
    for name in order:
        if name == "fill":
            return True                 # fill comes first: nothing to protect
        if name in UNFILLED_PASSES:
            return False
    return True


def cmd_import(cfg, route_source=None, target_board=None):
    """Import the final chain file ONCE into the segment-free base."""
    target = _target_board(cfg, target_board)
    if not target.is_file():
        die(f"import target board not found: {target}")
    _critical_route_gate(cfg, board=target)
    import pcbnew
    build = rel(cfg, get(cfg, "project.build_dir", "06_build/route"))
    # Selection is a declared policy, not filesystem precedence.  A stale
    # build/FINAL must never silently override the reviewed promoted route.
    route_source = route_source or get(cfg, "route.import_source", "auto")
    if route_source not in ("auto", "build", "promoted"):
        die("route import source must be auto, build or promoted")
    final = get(cfg, "route.final")
    build_chain = None
    marker = build / "FINAL"
    if marker.is_file():
        build_chain = Path(marker.read_text(encoding="utf-8-sig").strip())
    promoted_chain = rel(cfg, final) if final else None
    if route_source == "build":
        if build_chain is None:
            die("route source is build but no build/FINAL marker exists — run `route`")
        chain = build_chain
    elif route_source == "promoted":
        if promoted_chain is None:
            die("route source is promoted but route.final is not configured")
        chain = promoted_chain
    else:
        available = [("build", build_chain), ("promoted", promoted_chain)]
        available = [(name, path) for name, path in available
                     if path is not None and path.is_file()]
        if not available:
            die("route source not found: no usable build FINAL or promoted "
                "route.final")
        if len(available) > 1:
            print("import source auto: both build and promoted routes exist; "
                  "retaining legacy build precedence. Set route.import_source "
                  "or --route-source to make this provenance explicit.")
            chain = build_chain
            route_source = "build(auto)"
        else:
            route_source, chain = available[0]
    if not chain.is_file():
        die(f"chain file {chain} not found")
    b = pcbnew.LoadBoard(str(target))
    copper = list(b.GetTracks())
    segments = [item for item in copper if item.GetClass() != "PCB_VIA"]
    source_vias = [item for item in copper if item.GetClass() == "PCB_VIA"]
    if segments:
        die(f"import target {target.name} already has {len(segments)} routed "
            f"copper item(s) — "
            f"re-importing DOUBLES everything (holes_co_located x69, "
            f"observed 2026-07). Regenerate the board first.")
    if source_vias:
        print(f"import base: {len(source_vias)} source-owned vias preserved")
    stale = Path(str(target) + Ctx.STATE_SUFFIX)
    if stale.is_file():
        stale.unlink()          # a fresh import invalidates any resume point
    imp = Path(__file__).resolve().parent / "import_krt.py"
    cmd = [sys.executable, str(imp), str(chain), str(target), str(target)]
    if not _import_may_fill(cfg):
        cmd.append("--no-fill")
        print("import: --no-fill (the stitch plan places explicit copper "
              "before its `fill` — see _import_may_fill)")
    before_sha = _sha256(target)
    started_ns = time.time_ns()
    r = run_bounded(
        cmd, timeout_s=_timeout_s(cfg, "route_import", 300),
        heartbeat_s=_heartbeat_s(cfg), label="route-import",
        state_path=(build / "import_state.json" if target_board is None else
                    Path(str(target) + ".import_state.json")))
    if r.returncode != 0:
        die(f"import_krt exited {r.returncode}")
    receipt = {
        "schema": 1, "selected_source": route_source,
        "chain": os.path.relpath(chain, cfg["_root"]),
        "chain_sha256": _sha256(chain),
        "target": os.path.relpath(target, cfg["_root"]),
        "target_before_sha256": before_sha,
        "target_after_sha256": _sha256(target),
        "config": os.path.relpath(cfg["_path"], cfg["_root"]),
        "config_sha256": _sha256(cfg["_path"]),
        "started_ns": started_ns, "finished_ns": time.time_ns(),
        "elapsed_s": round(r.elapsed_s, 3),
    }
    provenance = (build / "import_provenance.json" if target_board is None else
                  Path(str(target) + ".import_provenance.json"))
    _atomic_json(provenance, receipt)
    print(f"import provenance -> {provenance} "
          f"(source={route_source}, sha256={receipt['chain_sha256'][:12]})")
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


def _tap_via_near(tk, p, nc, stub_w, layer, vs, vd, htc=None):
    """A collision-checked via site near p, reachable from p by a clear stub
    on `layer` (the escape-from-a-dense-pin-row move).

    HOLE-TO-HOLE IS DEFERRED HERE, and ONLY here (`hole_to_hole=0`). This is
    the one via emitter whose site set is a short fixed LADDER around a pad
    that cannot move, and whose only possible conflict partner is chain
    copper that a later pass can still move: `stitch.hole_to_hole` nudges
    whichever via of the pair is draggable, and it now FAILS LOUDLY when it
    cannot (p_hole_to_hole). Every free-choice emitter — verified_astar's
    layer changes, Ctx.try_via's stitch/grid/rescue vias — has a whole board
    of alternatives and must NOT create a conflict in the first place.

    MEASURED, usb-hub-3s-v3 2026-07-25: enforcing the floor here instead
    costs the board. The SW_A tap out of U2.20 sits 0.35mm from an imported
    HO_A via, so the pad site (offset 0,0 — no stub at all) is refused and
    the ladder falls to a 0.8mm stub that grazes that same via at 0.125mm
    against a 0.15mm netclass clearance. Sealed v1.5 took the pad site and
    the stitch moved the HO_A via 0.6mm east; that is the right answer, and
    it needs a repair pass, not a stricter placer. Every OTHER constraint
    (copper clearance, hole-to-copper, the stub's own path) stays hard —
    nothing downstream repairs those.

    Preserve the exact pad coordinate for the zero-offset site. Rounding a
    half-micron pad centre to the millimetre grid made `p1 != v1` and emitted
    a 0.0005mm full-width stub beside an adjacent fine-pitch signal pad."""
    for dx, dy in TAP_OFFS:
        v = p if dx == 0 and dy == 0 else \
            (round(p[0] + dx, 3), round(p[1] + dy, 3))
        kw = {"hole_to_copper": htc} if htc is not None else {}
        if not tk.via_site_ok(v[0], v[1], nc, size=vs, drill=vd,
                              hole_to_hole=0, **kw):
            continue
        if (dx == 0 and dy == 0) or \
                tk.collides(p[0], p[1], v[0], v[1], stub_w, nc, layer) is None:
            return v
    return None


def _route_one_tap(pcbnew, tk, t, i, vs, vd, htc=None):
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
    local_via = t.get("via") or {}
    if not isinstance(local_via, dict):
        die(f"{what}: `via:` must be a mapping")
    unknown_via = sorted(set(local_via) - {"size", "drill",
                                           "hole_to_copper", "exact"})
    if unknown_via:
        die(f"{what}: `via:` has unknown key(s) {unknown_via}")
    tvs = float(local_via.get("size", vs))
    tvd = float(local_via.get("drill", vd))
    thtc = float(local_via["hole_to_copper"]) \
        if "hole_to_copper" in local_via else htc
    if tvs <= 0 or tvd <= 0 or tvd >= tvs:
        die(f"{what}: `via:` needs size > drill > 0")
    exact_via = bool(local_via.get("exact", False))
    protection = t.get("via_protection")

    def add_tap_via(point):
        try:
            return tk.add_via(
                *point, nobj, size=tvs, drill=tvd, protection=protection,
                protection_path=f"taps.connections[{i}].via_protection")
        except ValueError as exc:
            die(str(exc))

    p1 = _tap_point(tk.board, t.get("from"), netname, what + " from")
    drop = bool(t.get("drop"))
    if drop and not t.get("plane"):
        die(f"{what}: `drop: true` requires `plane: true`")
    if exact_via and not drop:
        die(f"{what}: `via.exact: true` requires a plane drop")
    p2 = p1 if drop else \
        _tap_point(tk.board, t.get("to"), netname, what + " to")

    if t.get("plane"):
        # plane tap: stub -> via near `from` -> hop-layer join -> via AT `to`
        # (a point where the net's inner plane exists, so the fill merges it)
        if exact_via:
            kw = {"hole_to_copper": thtc} if thtc is not None else {}
            v1 = p1 if tk.via_site_ok(p1[0], p1[1], nc, size=tvs,
                                      drill=tvd, **kw) else None
        else:
            v1 = _tap_via_near(tk, p1, nc, w, lay, tvs, tvd, thtc)
        if not v1:
            return None
        if drop:
            # The declared plane already lies under the source pad. One
            # collision-checked via is the complete connection; a second via
            # and track merely create a needless neck inside the same pour.
            if p1 != v1:
                tk.add_seg(*p1, *v1, nobj, lay, w)
            add_tap_via(v1)
            return "plane_drop"
        kw = {"hole_to_copper": thtc} if thtc is not None else {}
        if not tk.via_site_ok(p2[0], p2[1], nc, size=tvs, drill=tvd, **kw):
            return None
        if tk.joinpath(netname, v1, p2, w, layer=hop,
                       widths_fallback=()) is None:
            return None
        if p1 != v1:
            tk.add_seg(*p1, *v1, nobj, lay, w)
        add_tap_via(v1)
        add_tap_via(p2)
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
        if protection is not None:
            die(f"{what}: `via_protection:` is not supported with `escape:`; "
                "declare a deterministic plane drop or hop")
        kw = {"hole_to_copper": thtc} if thtc is not None else {}
        if not tk.via_site_ok(p1[0], p1[1], nc, size=tvs, drill=tvd, **kw):
            print(f"       {what}: via-in-pad site blocked at {p1}")
            return None
        # vs/vd, NOT the toolkit's 0.45/0.2 default: the escape's layer-change
        # vias are TAP vias and must be checked and emitted at the tap tier's
        # geometry (usb-hub-3s-v3, 2026-07-25 — a 0.2-drill check cleared a
        # site the 0.3-drill via then violated).
        if tk.verified_astar(netname, p1, p2, w,
                             grid=float(t.get("escape_grid", 0.25)),
                             window=float(t.get("escape_window", 4.0)),
                             viacost=int(t.get("escape_viacost", 8)),
                             attempts=int(t.get("escape_attempts", 14)),
                             via_size=tvs, via_drill=tvd,
                             hole_to_copper=thtc):
            return "escape"
        return None

    # strategy 1: same-layer join (direct / L / Z scan), no vias
    if tk.joinpath(netname, p1, p2, w, layer=lay,
                   widths_fallback=()) is not None:
        return "joinpath"
    # strategy 2: via hop — stub -> via -> hop-layer join -> via -> stub
    v1 = _tap_via_near(tk, p1, nc, w, lay, tvs, tvd, thtc)
    v2 = _tap_via_near(tk, p2, nc, w, lay, tvs, tvd, thtc)
    if v1 and v2 and tk.joinpath(netname, v1, v2, w, layer=hop,
                                 widths_fallback=()) is not None:
        if p1 != v1:
            tk.add_seg(*p1, *v1, nobj, lay, w)
        add_tap_via(v1)
        add_tap_via(v2)
        if p2 != v2:
            tk.add_seg(*v2, *p2, nobj, lay, w)
        return "via_hop"
    return None


def cmd_taps(cfg, target_board=None):
    """Collision-checked tap connections KRT cannot thread (pour-fed sense
    pins, boxed-in connector pads, plane drops) — the bespoke tail every
    dense power board wrote by hand (usb-pwr-hub-3s route_taps.py was the
    second strike after cook-hub; canon M8 promotes it to config). Runs
    AFTER `import`, BEFORE `stitch`, so pours fill around the tap copper.

      taps:
        clearance: 0.15
        via: {size: 0.6, drill: 0.3, hole_to_copper: 0.255}
                                            # size/drill tier-derived; the
                                            # drilled-hole screen is explicit
        connections:
          - {net: VCC,  from: U1.4,  to: C8.1,        width: 0.3}
          - {net: CC1,  from: J5.A5, to: R10.2,       width: 0.25,
             layer: F.Cu, hop_layer: B.Cu}
          - {net: 5V,   from: R6.1,  to: [41.0, 46.5], width: 0.3,
             plane: true}    # `to` = a point inside the net's plane
          - {net: 5V,   from: U2.4, width: 0.3, plane: true, drop: true,
             via: {size: 0.5, drill: 0.2, exact: true},
             via_protection: {capping: yes, filling: yes}}
                              # item-level Type VII via in the source pad
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
    htc = float(via["hole_to_copper"]) \
        if "hole_to_copper" in via else None
    target = _target_board(cfg, target_board)
    if not target.is_file():
        die(f"tap target board not found: {target}")
    clr = float(get(cfg, "taps.clearance", 0.15))
    bref = pcbnew.LoadBoard(str(target))   # read-only, for endpoint geometry

    def route_all(order, tag=""):
        """Route the whole tap set in `order` on a FRESH copy of the target
        board (the original is untouched on disk until the final save), so a
        reattempt is a clean re-route in a new ORDER — not a partial retry
        that keeps an earlier tap's blocking copper. Returns (board, failed
        indices)."""
        attempt = "retry" if tag else "primary"
        _seed_uuid_stream(pcbnew, target.stem, f"route-taps-{attempt}")
        bb = pcbnew.LoadBoard(str(target))
        tkk = Toolkit(bb, clr)
        failed = []
        for idx in order:
            t = taps[idx]
            how = _route_one_tap(pcbnew, tkk, t, idx, vs, vd, htc)
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
    r = run_bounded(
        ["kicad-cli", "pcb", "drc", "--severity-all", "--format", "json",
         "-o", str(rpt), str(target)],
        timeout_s=_timeout_s(cfg, "quick_drc", 180),
        heartbeat_s=_heartbeat_s(cfg), label="quick-drc",
        state_path=build / "quick_drc_state.json", echo=False)
    if not rpt.is_file():
        die(f"quick: kicad-cli drc wrote no report "
            f"(exit {r.returncode}): {r.output[-500:]}")
    g = jsonlib.loads(rpt.read_text(encoding="utf-8-sig"))
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
        self._copper_smd_pads = None

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
        d = json.loads(p.read_text(encoding="utf-8-sig"))
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

    @property
    def copper_smd_pads(self):
        """Undrilled component copper lands that ordinary vias must avoid.

        KiCad correctly permits same-net copper overlap, so the geometric
        collision checker cannot distinguish a useful same-net join from an
        undeclared via-in-pad process.  Cache the exact pad shapes here and
        make that assembly decision explicit at the shared stitch-via seam.
        """
        if self._copper_smd_pads is None:
            layers = [layer for layer in self.board.GetEnabledLayers().Seq()
                      if self.pcbnew.IsCopperLayer(layer)]
            self._copper_smd_pads = [
                (pad, pad.GetBoundingBox())
                for footprint in self.board.GetFootprints()
                for pad in footprint.Pads()
                if pad.GetDrillSize().x <= 0
                and any(pad.IsOnLayer(layer) for layer in layers)
            ]
        return self._copper_smd_pads

    def lands_in_smd_pad(self, x, y):
        """Whether a proposed via centre lies in any exact SMD copper land."""
        pos = self.pcbnew.VECTOR2I_MM(x, y)
        return any(bbox.Contains(pos) and pad.HitTest(pos)
                   for pad, bbox in self.copper_smd_pads)

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

    def via_choice(self, net, x, y, avoid=(), spacing_override=None,
                   allow_via_in_pad=False, exact_size=None,
                   exact_drill=None):
        """Return the first legal ``(x, y, size, drill)`` without emitting it.

        Some callers need to validate copper that must reach the proposed via
        before committing the barrel.  Keeping that probe here preserves the
        same keep-in, spacing, PTH and hole-to-copper guards as ``try_via``;
        a rejected compound candidate must not leave an orphan via behind and
        consume the next candidate's spacing window."""
        v = get(self.cfg, "stitch.via", {}) or {}
        spacing = (float(spacing_override) if spacing_override is not None
                   else float(v.get("spacing", 0.62)))
        pth_margin = float(v.get("pth_margin", 0.3))
        x, y = round(x, 2), round(y, 2)
        if not self.keepin(x, y):
            return None
        # DRC intentionally allows same-net copper to overlap.  An ordinary
        # stitch via in an SMD land is nevertheless a fabrication decision:
        # without declared fill/cap it can wick solder and starve the joint.
        # Refuse it at the one primitive used by grid, fence and rescue
        # emitters.  Only a caller that explicitly owns via-in-pad processing
        # may opt in (currently pad_rescue with via_in_pad: true).
        if not allow_via_in_pad and self.lands_in_smd_pad(x, y):
            return None
        for r in avoid:
            m = float(r.get("margin", 0.0))
            if (float(r["x0"]) - m < x < float(r["x1"]) + m
                    and float(r["y0"]) - m < y < float(r["y1"]) + m):
                return None
        if any((x - ux) ** 2 + (y - uy) ** 2 < spacing ** 2
               for ux, uy in self.used):
            return None
        if (exact_size is None) != (exact_drill is None):
            raise ValueError("exact_size and exact_drill must be paired")
        tiers = ([{"size": exact_size, "drill": exact_drill}]
                 if exact_size is not None else
                 (v.get("tiers") or [{"size": v.get("size", 0.6),
                                      "drill": v.get("drill", 0.3)}]))
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
                return x, y, size, drill
        return None

    def try_via(self, net, x, y, avoid=(), spacing_override=None,
                allow_via_in_pad=False, exact_size=None, exact_drill=None):
        """Place one collide-checked via. THE shared primitive: every via
        this script adds goes through here, so the spacing/PTH/keepin
        guards can never be bypassed by a new pass."""
        choice = self.via_choice(
            net, x, y, avoid, spacing_override=spacing_override,
            allow_via_in_pad=allow_via_in_pad, exact_size=exact_size,
            exact_drill=exact_drill)
        if choice is None:
            return False
        x, y, size, drill = choice
        self.tk.add_via(x, y, net, size=size, drill=drill)
        self.used.add((x, y))
        self.emitted.append((x, y))
        return True

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
        if (t.GetClass() == "PCB_VIA"
                and t.GetWidth(ctx.pcbnew.F_Cu) / 1e6 < lo):
            t.SetWidth(int(size * 1e6))
            t.SetDrill(int(drill * 1e6))
            n += 1
    ctx.bump("normalized_vias", n)
    print(f"normalized {n} sub-spec vias to {size}/{drill}")


@stitch_pass("bridge_via_endpoints")
def p_bridge_via_endpoints(ctx, c):
    """Make a copper-overlap-only track/via join an explicit centreline join.

    Grid routers may stop a track one cell short of an existing same-net via
    once the two copper shapes touch.  KiCad accepts that electrical overlap,
    but a later via janitor can legitimately remove a single-layer transition
    barrel and leave two tracks joined only by rounded-end copper.  Add a
    short bridge only from a *free* endpoint to the via centre and only when
    the entire bridge, including its track radius, remains inside the via's
    existing copper disk.  The original route segment is not moved or
    pivoted.  This changes topology, not the copper envelope, so it cannot
    create a new clearance or assembly conflict.
    """
    pcbnew = ctx.pcbnew
    tol = float(c.get("tol", 0.01))
    max_move = float(c.get("max_move", 0.20))
    tracks = [t for t in ctx.board.GetTracks() if t.GetClass() == "PCB_TRACK"]
    vias = [v for v in ctx.board.GetTracks() if v.GetClass() == "PCB_VIA"]
    pads = [p for fp in ctx.board.GetFootprints() for p in fp.Pads()]

    def otherwise_anchored(t, ex, ey):
        uid = t.m_Uuid.AsString()
        for o in tracks:
            if (o.m_Uuid.AsString() == uid or o.GetNetCode() != t.GetNetCode()
                    or o.GetLayer() != t.GetLayer()):
                continue
            if any(math.hypot(ex - ox, ey - oy) <= tol
                   for ox, oy in _ends_mm(o)):
                return True
        pt = pcbnew.VECTOR2I_MM(ex, ey)
        for p in pads:
            if (p.GetNetCode() == t.GetNetCode() and p.IsOnLayer(t.GetLayer())
                    and p.GetBoundingBox().Contains(pt)):
                return True
        return False

    added = 0
    for t in tracks:
        for which in ("start", "end"):
            pos = t.GetStart() if which == "start" else t.GetEnd()
            ex, ey = pos.x / 1e6, pos.y / 1e6
            if otherwise_anchored(t, ex, ey):
                continue
            tr = t.GetWidth() / 2e6
            best = None
            for v in vias:
                if v.GetNetCode() != t.GetNetCode() or not v.IsOnLayer(t.GetLayer()):
                    continue
                vx, vy = v.GetPosition().x / 1e6, v.GetPosition().y / 1e6
                d = math.hypot(ex - vx, ey - vy)
                vr = v.GetWidth(t.GetLayer()) / 2e6
                # The swept track cap stays wholly inside copper that the via
                # already owns.  No enlargement of the realized copper union.
                if tol < d <= max_move and d + tr <= vr:
                    cand = (d, vx, vy)
                    if best is None or cand < best:
                        best = cand
            if best:
                _, vx, vy = best
                bridge = pcbnew.PCB_TRACK(ctx.board)
                bridge.SetStart(pcbnew.VECTOR2I_MM(round(ex, 4), round(ey, 4)))
                bridge.SetEnd(pcbnew.VECTOR2I_MM(round(vx, 4), round(vy, 4)))
                bridge.SetWidth(t.GetWidth())
                bridge.SetLayer(t.GetLayer())
                bridge.SetNetCode(t.GetNetCode())
                ctx.board.Add(bridge)
                added += 1
    ctx.bump("via_endpoint_bridges", added)
    print(f"bridged {added} copper-contained track endpoint(s) to via centres")


@stitch_pass("drop_micro_fragments")
def p_micro(ctx, c):
    """KRT leaves sub-grid whiskers at pass joins. Removing one with BOTH
    ends served disconnects the net, so the default requires a free end."""
    lim = float(c.get("max_length", 0.12))
    need_free = bool(c.get("require_free_end", True))
    anchor_tol = float(c.get("anchor_tol", 0.05))
    segs, vias, pads = _track_context(ctx)
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
        # "FREE" MUST MEAN FREE OF EVERYTHING, not just of other TRACKS
        # (cooksense v1.2, 2026-07-25). The old test counted only track
        # endpoints, so a whisker whose end sat ON A PAD read as free and was
        # deleted — taking the net's only pad entry with it. Incident:
        # DOOR_RAW entered U_SCHM.11 through a 0.100mm segment landing exactly
        # on the pad's south edge; drop_micro_fragments ate it and the full
        # DRC gate reported 1 unconnected + 1 track_dangling on a chain that
        # raced 0/0. `_end_anchored` is the same served-test drop_dangling and
        # split_t_junctions already use: other track ends, vias, AND pads.
        if need_free and not any(
                not _end_anchored(ctx, t, e[0], e[1], segs, vias, pads,
                                  anchor_tol)
                for e in _ends_mm(t)):
            continue
        dead.append(t)
    for t in dead:
        ctx.remove(t)
    ctx.bump("micro_removed", len(dead))
    print(f"removed {len(dead)} dangling micro-fragments")


@stitch_pass("protect_via_in_pad")
def p_protect_via_in_pad(ctx, c):
    """Promote every exact via-in-SMT-land hit to one IPC-4761 family.

    Autorouters may legally use a same-net SMD land as a layer-transition
    site.  KiCad DRC accepts that copper, but an ordinary open barrel under
    paste can starve the solder joint and Gerber cannot carry per-item fill
    flags.  This pass makes the *realized* set explicit and drill-selectable;
    via_process_check independently grades the saved result and order note.
    """
    if not isinstance(c, dict):
        die("stitch.protect_via_in_pad must be a mapping")
    unknown = sorted(set(c) - {"via", "via_protection", "min"})
    if unknown:
        die(f"stitch.protect_via_in_pad has unknown key(s) {unknown}")
    via_cfg = c.get("via")
    protection = c.get("via_protection")
    if not isinstance(via_cfg, dict):
        die("stitch.protect_via_in_pad.via must be a mapping")
    unknown_via = sorted(set(via_cfg) - {"size", "drill"})
    if unknown_via:
        die("stitch.protect_via_in_pad.via has unknown key(s) "
            f"{unknown_via}")
    try:
        size = float(via_cfg["size"])
        drill = float(via_cfg["drill"])
    except (KeyError, TypeError, ValueError):
        die("stitch.protect_via_in_pad.via needs numeric size and drill")
    if not (size > drill > 0):
        die("stitch.protect_via_in_pad.via needs size > drill > 0")
    try:
        minimum = int(c.get("min", 1))
    except (TypeError, ValueError):
        die("stitch.protect_via_in_pad.min must be an integer")
    if minimum < 0:
        die("stitch.protect_via_in_pad.min must be non-negative")

    pcbnew = ctx.pcbnew
    copper_layers = [layer for layer in ctx.board.GetEnabledLayers().Seq()
                     if pcbnew.IsCopperLayer(layer)]
    pads = []
    for footprint in ctx.board.GetFootprints():
        for pad in footprint.Pads():
            if (pad.GetDrillSize().x > 0
                    or not any(pad.IsOnLayer(layer)
                               for layer in copper_layers)):
                continue
            pads.append((pad, pad.GetBoundingBox()))

    def apply_protection(via):
        if not isinstance(protection, dict) or not protection:
            die("stitch.protect_via_in_pad.via_protection must declare "
                "capping and filling")
        unknown_p = sorted(set(protection) - {"capping", "filling"})
        if unknown_p:
            die("stitch.protect_via_in_pad.via_protection has unknown key(s) "
                f"{unknown_p}")

        def enabled(key):
            value = protection.get(key)
            if isinstance(value, bool):
                return value
            if isinstance(value, str) and value.strip().lower() in ("yes", "no"):
                return value.strip().lower() == "yes"
            die("stitch.protect_via_in_pad.via_protection."
                f"{key} must be a boolean (yes/no)")

        cap = enabled("capping")
        fill = enabled("filling")
        if not (cap and fill):
            die("stitch.protect_via_in_pad requires both capping and filling")
        via.SetCappingMode(pcbnew.CAPPING_MODE_CAPPED)
        via.SetFillingMode(pcbnew.FILLING_MODE_FILLED)

    hits = 0
    changed = 0
    target_w = pcbnew.FromMM(size)
    target_d = pcbnew.FromMM(drill)
    for via in ctx.board.GetTracks():
        if via.GetClass() != "PCB_VIA":
            continue
        pos = via.GetPosition()
        if not any(bbox.Contains(pos) and pad.HitTest(pos)
                   for pad, bbox in pads):
            continue
        hits += 1
        was_target = (via.GetWidth(pcbnew.F_Cu) == target_w
                      and via.GetDrill() == target_d
                      and via.GetCappingMode() == pcbnew.CAPPING_MODE_CAPPED
                      and via.GetFillingMode() == pcbnew.FILLING_MODE_FILLED)
        via.SetWidth(target_w)
        via.SetDrill(target_d)
        apply_protection(via)
        changed += int(not was_target)
    if hits < minimum:
        die(f"protect_via_in_pad: realized {hits}, require at least {minimum}")
    ctx.bump("via_in_pad_protected", changed)
    print(f"protected {hits} realized via-in-pad barrel(s) "
          f"as {size:.3f}/{drill:.3f} mm Type VII ({changed} changed)")


@stitch_pass("protect_via_family")
def p_protect_via_family(ctx, c):
    """Apply Type-VII flags to one complete, drill-selectable via family.

    Gerber carries neither KiCad's per-via fill/cap attributes nor a stable
    item identifier.  When the fabrication contract selects by drill family,
    every realized via in that family must therefore carry the same native
    intent.  This pass never resizes vias and never touches another family.
    """
    if not isinstance(c, dict):
        die("stitch.protect_via_family must be a mapping")
    unknown = sorted(set(c) - {"via", "via_protection", "min"})
    if unknown:
        die(f"stitch.protect_via_family has unknown key(s) {unknown}")
    via_cfg = c.get("via")
    protection = c.get("via_protection")
    if not isinstance(via_cfg, dict):
        die("stitch.protect_via_family.via must be a mapping")
    unknown_via = sorted(set(via_cfg) - {"size", "drill"})
    if unknown_via:
        die("stitch.protect_via_family.via has unknown key(s) "
            f"{unknown_via}")
    try:
        size = float(via_cfg["size"])
        drill = float(via_cfg["drill"])
        minimum = int(c.get("min", 1))
    except (KeyError, TypeError, ValueError):
        die("stitch.protect_via_family needs numeric via size/drill and "
            "integer min")
    if not (size > drill > 0) or minimum < 0:
        die("stitch.protect_via_family requires size > drill > 0 and min >= 0")
    if not isinstance(protection, dict) or not protection:
        die("stitch.protect_via_family.via_protection must declare capping "
            "and filling")
    unknown_p = sorted(set(protection) - {"capping", "filling"})
    if unknown_p:
        die("stitch.protect_via_family.via_protection has unknown key(s) "
            f"{unknown_p}")

    def enabled(key):
        value = protection.get(key)
        if isinstance(value, bool):
            return value
        if isinstance(value, str) and value.strip().lower() in ("yes", "no"):
            return value.strip().lower() == "yes"
        die("stitch.protect_via_family.via_protection."
            f"{key} must be a boolean (yes/no)")

    if not (enabled("capping") and enabled("filling")):
        die("stitch.protect_via_family requires both capping and filling")
    target_w = ctx.pcbnew.FromMM(size)
    target_d = ctx.pcbnew.FromMM(drill)
    hits = changed = 0
    for via in ctx.board.GetTracks():
        if (via.GetClass() != "PCB_VIA"
                or via.GetWidth(ctx.pcbnew.F_Cu) != target_w
                or via.GetDrill() != target_d):
            continue
        hits += 1
        already = (via.GetCappingMode() == ctx.pcbnew.CAPPING_MODE_CAPPED
                   and via.GetFillingMode()
                   == ctx.pcbnew.FILLING_MODE_FILLED)
        via.SetCappingMode(ctx.pcbnew.CAPPING_MODE_CAPPED)
        via.SetFillingMode(ctx.pcbnew.FILLING_MODE_FILLED)
        changed += int(not already)
    if hits < minimum:
        die(f"protect_via_family: realized {hits}, require at least {minimum}")
    ctx.bump("via_family_protected", changed)
    print(f"protected complete {size:.3f}/{drill:.3f} mm via family: "
          f"{hits} realized, {changed} changed")


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
            # DEGENERACY IS DECIDED AFTER THE WRITE-ROUNDING, not before
            # (cooksense v1.2, 2026-07-25). The old guard tested the RAW
            # separation against 1e-6 mm, but the endpoints are written
            # rounded to 1e-4 mm; a junction point 5e-5 mm from the segment
            # end passed the guard and then collapsed on write, emitting a
            # ZERO-LENGTH track. KiCad's crossing test degenerates on a
            # zero-length segment and reported a phantom `tracks_crossing`
            # against an unrelated net 0.7 mm away (I2C_SDA vs KEY_CLOCK).
            ax, ay = round(a[1], 4), round(a[2], 4)
            bx, by = round(b[1], 4), round(b[2], 4)
            if ax == bx and ay == by:
                continue
            s = pcbnew.PCB_TRACK(ctx.board)
            s.SetStart(pcbnew.VECTOR2I_MM(ax, ay))
            s.SetEnd(pcbnew.VECTOR2I_MM(bx, by))
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


@stitch_pass("fresh_reload")
def p_fresh_reload(ctx, c):
    """Unconditional save/re-exec barrier.

    Unlike ``reload`` (which only protects a poisoned SWIG iterator after a
    removal), this pass deliberately rebuilds pcbnew's connectivity model in
    a fresh interpreter.  Put it after the authoritative final ``fill`` and
    before connectivity-sensitive passes such as ``heal_islands``.  Dense
    boards can otherwise retain a pre-fill connectivity view and undercount
    small, real zone fragments that KiCad's later CLI DRC reports.
    """
    die("internal: 'fresh_reload' must be intercepted by cmd_stitch")


# Prefix on every failure this pass records, so a LATER hole_to_hole pass can
# clear an EARLIER one's findings without touching anyone else's failures.
_H2H_TAG = "hole_to_hole: "


@stitch_pass("hole_to_hole")
def p_hole_to_hole(ctx, c):
    """Fab floor is a DRILL-EDGE gap (0.5mm at JLC). Two modes, both shipped:
    nudge the offending via (carrying its track endpoints), or shrink it.

    This is a REPAIR pass, and it is the LAST line — `via_site_ok` refuses a
    site inside the floor in the first place. What it cannot repair it
    REPORTS (ctx.failures): a silent give-up here is a shipped violation."""
    pcbnew = ctx.pcbnew
    floor = float(c.get("min_gap", 0.5))
    mode = c.get("mode", "nudge")
    keep = list(c.get("prefer_keep", ["GND"]))
    # CANONICAL ORDER, not board order (cooksense v1.2, 2026-07-25). This pass
    # walks pairs and moves the SECOND via of each conflicting pair, so its
    # output depends entirely on iteration order — and board order is NOT
    # stable across the SWIG re-exec barrier (split_t_junctions deletes and
    # re-adds segments with fresh random UUIDs, and the save/reload round-trip
    # does not preserve the pre-barrier sequence). Two identical rebuilds from
    # the same frozen chain therefore nudged a different SET of vias (27 vs 28),
    # which moved copper, which changed what pad_rescue could reach: one build
    # bonded C_FAULTAND.1 to the 3V3 plane and the other did not -> M-REPRO
    # FAIL with 1 unconnected on a byte-identical input. Sorting by position
    # makes the pass a pure function of the geometry.
    vlist = sorted((t for t in ctx.board.GetTracks() if t.GetClass() == "PCB_VIA"),
                   key=lambda v: (v.GetPosition().x, v.GetPosition().y,
                                  v.GetDrill(), v.GetNetname()))
    # This predicate is called from the O(V^2) via-pair loop.  Scanning every
    # board track for each conflicting pair made dense boards spend minutes in
    # a test that only ever consumes same-net tracks (529 vias / 3323 segments
    # on programmable-usb2-hub).  Build the exact same candidate sets once.
    tracks_by_net = {}
    for t in ctx.board.GetTracks():
        if t.GetClass() == "PCB_TRACK":
            tracks_by_net.setdefault(t.GetNetCode(), []).append(t)

    def vxy(v):
        return (v.GetPosition().x / 1e6, v.GetPosition().y / 1e6)

    def pinned_midtrack(v):
        """Does a same-net track cross this via MID-SEGMENT (no endpoint on
        it)? Such a via is an UNDRAGGABLE anchor: the nudge below only
        rewrites track ENDPOINTS, so moving it silently strands the crossing
        segment and BREAKS the net — with no error, because the stitch gate
        and `quick` both look at the pre-nudge board. Incident (cooksense
        v1.2, 2026-07-25): ADC_CH7's layer-change via sat mid-way along its
        own B.Cu run; a 0.5mm h2h conflict with a TH_CAM_B via nudged it
        0.72mm away, leaving the B.Cu chain floating -> 1 unconnected + 1
        track_dangling at the FULL DRC gate, on a chain that raced 0/0."""
        vx, vy = vxy(v)
        r = v.GetWidth(pcbnew.F_Cu) / 2e6
        for t in tracks_by_net.get(v.GetNetCode(), []):
            (ax, ay), (bx, by) = _ends_mm(t)
            if (abs(ax - vx) < 0.05 and abs(ay - vy) < 0.05) or \
               (abs(bx - vx) < 0.05 and abs(by - vy) < 0.05):
                continue                      # endpoint-anchored: draggable
            dx, dy = bx - ax, by - ay
            L2 = dx * dx + dy * dy
            if L2 == 0:
                continue
            u = max(0.0, min(1.0, ((vx - ax) * dx + (vy - ay) * dy) / L2))
            if math.hypot(vx - (ax + u * dx), vy - (ay + u * dy)) <= r + t.GetWidth() / 2e6:
                return True
        return False

    moved = 0
    unfixed = []

    def give_up(v1, v2, gap, why):
        (x1, y1), (x2, y2) = vxy(v1), vxy(v2)
        unfixed.append(
            f"{_H2H_TAG}{v1.GetNetname()} via ({x1:.3f},{y1:.3f}) vs "
            f"{v2.GetNetname()} via ({x2:.3f},{y2:.3f}): hole gap "
            f"{gap:.3f}mm < floor {floor}mm and {why}")

    for i in range(len(vlist)):
        for j in range(i + 1, len(vlist)):
            v1, v2 = vlist[i], vlist[j]
            x1, y1 = vxy(v1)
            x2, y2 = vxy(v2)
            d1, d2 = v1.GetDrill() / 1e6, v2.GetDrill() / 1e6
            gap = math.hypot(x1 - x2, y1 - y2) - (d1 + d2) / 2
            if gap >= floor:
                continue
            vm = v1 if (v2.GetNetname() in keep and v1.GetNetname() not in keep) else v2
            if mode != "shrink" and pinned_midtrack(vm):
                other = v2 if vm is v1 else v1
                if pinned_midtrack(other):
                    # BOTH undraggable. Leaving the pair alone is the only SAFE
                    # move (nudging either one breaks its net), but silence here
                    # SHIPS A DRC VIOLATION: usb-hub-3s-v3 v1.5 rebuilt to
                    # hole_to_hole 0.259mm vs 0.4995mm with a clean stitch log
                    # (2026-07-25). An unrepairable pair is a FAILURE, not a
                    # no-op — the placer upstream has to stop making it.
                    give_up(v1, v2, gap, "both vias are pinned mid-track "
                                         "(nudging either one breaks its net)")
                    continue
                vm = other
            if mode == "shrink":
                s = c.get("shrink_to", {"size": 0.48, "drill": 0.2})
                vm.SetWidth(int(float(s["size"]) * 1e6))
                vm.SetDrill(int(float(s["drill"]) * 1e6))
                moved += 1
                continue
            mx, my = vxy(vm)
            ends = [t for t in tracks_by_net.get(vm.GetNetCode(), [])
                    if any(abs(e.x / 1e6 - mx) < 0.05 and abs(e.y / 1e6 - my) < 0.05
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
                    # skip=[vm]: vm's own hole is about to VACATE (mx,my), and
                    # the first ring is 0.25mm — well inside the h2h floor, so
                    # without the skip a via could never step off its own site.
                    if not ctx.tk.via_site_ok(nx, ny, vm.GetNetCode(),
                                              size=vm.GetWidth(pcbnew.F_Cu) / 1e6,
                                              drill=vm.GetDrill() / 1e6,
                                              skip=[vm]):
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
            if not done:
                give_up(v1, v2, gap, "no legal site on any nudge ring "
                                     f"({c.get('rings', [0.25, 0.4, 0.6, 0.85, 1.1])})")
    ctx._used = None
    ctx.bump("h2h_fixed", moved)
    # THE LAST hole_to_hole PASS OWNS THE VERDICT. Boards run this pass twice
    # (repair, then re-check after the via-adding passes), so a later run
    # CLEARS what an earlier one could not fix — but whatever is still
    # unrepairable when the last run ends reaches `gate` as a failure instead
    # of reaching the fab as a DRC violation.
    ctx.failures[:] = [f for f in ctx.failures if not f.startswith(_H2H_TAG)]
    ctx.failures.extend(unfixed)
    ctx.counts["h2h_unrepairable"] = len(unfixed)
    print(f"hole-to-hole repair ({mode}): {moved} vias"
          + (f", {len(unfixed)} UNREPAIRABLE" if unfixed else ""))


def _grid_axis(spec, axis):
    """`[start, stop, pitch]` in MILLIMETRES -> the site coordinates.

    A FRACTIONAL PITCH IS A REAL REQUIREMENT, NOT A ROUNDING QUESTION. This
    was `range(int(start), int(stop), int(pitch))`, so the pitch was silently
    floored to a whole millimetre — and on an RF board the stitch grid IS the
    ground-via fence, whose pitch is derived from the guided wavelength and
    lands on numbers like 1.35 mm. MEASURED, pluto-rx2-8way-v2 (2026-07-30):
    ARCHITECTURE sec 6 requires <= 1.35 mm (the largest round value under the
    derived lambda_g/20 = 1.3693 mm, ADR-0003), the only expressible choices
    were 1 mm (a via forest, ~2500 sites) or 2 mm, and the board shipped at
    **2.0 mm = lambda_g/13.7** — conservative against the SOURCED FREE-SPACE
    lambda/20 = 2.5 mm, and NOT MEETING its own guided bound. `1.35` would
    have become `1`: not a refusal, a different board.

    THE lambda IS THE GUIDED ONE, and this is stated here so the bound is not
    left ambiguous (rf-design.md 3(b), which measured THREE methods in one
    fleet). A fence sits in the substrate alongside a microstrip, so what it
    must sample is the wave ON THE LINE, whose wavelength is
    `lambda_g = lambda_0 / sqrt(eps_eff)` — shorter than free space, hence a
    STRICTER pitch. Free-space lambda/20 is the LOOSER bound and passing it
    proves nothing about the guided one; the BULK-eps_r wavelength is neither.

    Counts are computed as `ceil((stop - start) / pitch)`, which is exactly
    `range`'s own length rule, so every integer config in this repo produces a
    BYTE-IDENTICAL site set (measured over all 13 fleet + archived + template
    configs before this landed: 0 fractional, 0 lattices moved).

    A non-positive pitch is a HARD ERROR. Pre-fix, a negative pitch made
    `range` yield nothing and the pass printed `stitch grid: 0 vias` with no
    complaint; post-fix it would not terminate. Neither is acceptable for the
    only pass that places a board's return-path stitching.
    """
    try:
        start, stop, pitch = (float(v) for v in spec)
    except (TypeError, ValueError):
        die(f"stitch_grid.{axis} must be [start, stop, pitch] in mm, got "
            f"{spec!r}")
    if pitch <= 0:
        die(f"stitch_grid.{axis} pitch is {pitch} — a stitch grid needs a "
            f"POSITIVE pitch. A non-positive one placed ZERO vias and said "
            f"nothing before 2026-07-30, which on a board whose return path "
            f"is stitched is a silent open, not an empty pass")
    return [start + i * pitch
            for i in range(max(0, math.ceil((stop - start) / pitch)))]


@stitch_pass("stitch_grid")
def p_stitch_grid(ctx, c):
    net = ctx.net(c.get("net", "GND"))
    avoid = c.get("avoid", []) or []
    xs, ys = _grid_axis(c["x"], "x"), _grid_axis(c["y"], "y")
    sites = [(x, y) for x in xs for y in ys]
    added = 0
    for x, y in sites:
        if ctx.try_via(net, x, y, avoid=avoid):
            added += 1

    # `min` is a saved-result requirement, not a first-run work counter.  On
    # a deterministic rerun every complete site is already occupied, so
    # try_via correctly emits zero; grading only `added` then reports an
    # existing healthy grid as `0 < min`.  Credit realized same-net plated
    # returns within the same spacing window that prevented a duplicate.
    spacing = float((get(ctx.cfg, "stitch.via", {}) or {}).get(
        "spacing", 0.62))
    elements = _plated_ground_elements(ctx, net.GetNetCode())
    served = sum(any(math.hypot(x - vx, y - vy) <= spacing + 1e-9
                     for vx, vy in elements)
                 for x, y in sites)
    ctx.bump("grid_vias", added)
    ctx.counts["grid_sites_total"] = len(sites)
    ctx.counts["grid_sites_served"] = served
    print(f"stitch grid: {added} vias added; {served}/{len(sites)} "
          "declared sites served by realized same-net plated returns")
    lo = c.get("min")
    if lo is not None and served < int(lo):
        ctx.failures.append(f"stitch grid too sparse: {served} < {lo} "
                            "realized served sites")


def _simple_track_chain(ctx, netname, layer_name):
    """Return one ordered, branch-free saved line/arc centreline.

    A route-following fence cannot be derived honestly from an unordered bag
    of primitives: a disconnected fragment or branch changes the along-line
    denominator. Native KiCad arcs are retained as arcs, never approximated by
    a chord, so fence sites and apertures use their realized arclength.
    Integer KiCad coordinates are the graph keys, so no geometric tolerance
    can join two endpoints that the saved board itself keeps separate.
    """
    pcbnew = ctx.pcbnew
    layer = _layer_id(pcbnew, layer_name)
    tracks = []
    unsupported = []
    for item in ctx.board.GetTracks():
        if item.GetNetname() != netname or item.GetLayer() != layer:
            continue
        if item.GetClass() in ("PCB_TRACK", "PCB_ARC"):
            tracks.append(item)
        elif item.GetClass() != "PCB_VIA":
            unsupported.append(item.GetClass())
    if unsupported:
        die(f"route_fence net {netname!r} has unsupported {layer_name} "
            f"copper {sorted(set(unsupported))}; only PCB_TRACK/PCB_ARC "
            "primitives have a defined route-following fence")
    if not tracks:
        die(f"route_fence net {netname!r} has no {layer_name} track/arc "
            "centreline")

    def key(p):
        return int(p.x), int(p.y)

    points, adj = {}, {}
    for i, t in enumerate(tracks):
        a, b = key(t.GetStart()), key(t.GetEnd())
        if a == b:
            die(f"route_fence net {netname!r} contains a zero-length track")
        points[a], points[b] = t.GetStart(), t.GetEnd()
        adj.setdefault(a, []).append((i, b))
        adj.setdefault(b, []).append((i, a))
    branches = [p for p, edges in adj.items() if len(edges) > 2]
    ends = sorted(p for p, edges in adj.items() if len(edges) == 1)
    if branches or len(ends) != 2:
        die(f"route_fence net {netname!r} is not one simple chain: "
            f"{len(branches)} branch node(s), {len(ends)} endpoint(s)")

    ordered, used, cur = [], set(), ends[0]
    while True:
        nxt = next(((i, other) for i, other in adj[cur] if i not in used),
                   None)
        if nxt is None:
            break
        i, other = nxt
        used.add(i)
        item = tracks[i]
        reverse = key(item.GetEnd()) == cur
        ordered.append(_route_primitive(item, reverse))
        cur = other
    if len(used) != len(tracks) or cur != ends[1]:
        die(f"route_fence net {netname!r} has disconnected {layer_name} "
            f"copper ({len(used)}/{len(tracks)} segments reached)")
    if any(row["length"] <= 1e-12 for row in ordered):
        die(f"route_fence net {netname!r} has invalid zero-length copper")
    return ordered


def _route_angle_on_sweep(angle, start, sweep, tolerance=1e-9):
    tau = 2.0 * math.pi
    if sweep >= 0:
        return (angle - start) % tau <= sweep + tolerance
    return (start - angle) % tau <= -sweep + tolerance


def _route_primitive(item, reverse=False):
    """Emitter-owned line/arc geometry; the release gate reimplements it."""
    def xy(point):
        return point.x / 1e6, point.y / 1e6

    start = xy(item.GetEnd() if reverse else item.GetStart())
    end = xy(item.GetStart() if reverse else item.GetEnd())
    if item.GetClass() == "PCB_TRACK":
        return {"kind": "line", "start": start, "end": end,
                "length": math.hypot(end[0] - start[0], end[1] - start[1])}
    mid, center = xy(item.GetMid()), xy(item.GetCenter())
    radius = math.hypot(start[0] - center[0], start[1] - center[1])
    if radius <= 1e-12:
        return {"kind": "invalid", "start": start, "end": end,
                "length": 0.0}
    a0 = math.atan2(start[1] - center[1], start[0] - center[0])
    am = math.atan2(mid[1] - center[1], mid[0] - center[0])
    a1 = math.atan2(end[1] - center[1], end[0] - center[0])
    ccw = (a1 - a0) % (2.0 * math.pi)
    sweep = ccw if (am - a0) % (2.0 * math.pi) <= ccw + 1e-9 \
        else -((a0 - a1) % (2.0 * math.pi))
    return {"kind": "arc", "start": start, "mid": mid, "end": end,
            "center": center, "radius": radius, "start_angle": a0,
            "sweep": sweep, "length": abs(sweep) * radius}


def _route_primitive_point(primitive, distance):
    """Point and unit left normal at a bounded primitive arclength."""
    length = primitive["length"]
    fraction = max(0.0, min(1.0, distance / length))
    if primitive["kind"] == "line":
        a, b = primitive["start"], primitive["end"]
        dx, dy = b[0] - a[0], b[1] - a[1]
        tx, ty = dx / length, dy / length
        return a[0] + fraction * dx, a[1] + fraction * dy, -ty, tx
    angle = primitive["start_angle"] + fraction * primitive["sweep"]
    cx, cy = primitive["center"]
    direction = 1.0 if primitive["sweep"] >= 0 else -1.0
    tx, ty = (-math.sin(angle) * direction,
              math.cos(angle) * direction)
    return (cx + primitive["radius"] * math.cos(angle),
            cy + primitive["radius"] * math.sin(angle), -ty, tx)


def _route_point(chain, wanted_s):
    """Point and left normal at arclength ``wanted_s`` on ``chain``."""
    walked = 0.0
    for primitive in chain:
        length = primitive["length"]
        if length <= 1e-12:
            continue
        if wanted_s <= walked + length + 1e-9:
            return _route_primitive_point(primitive, wanted_s - walked)
        walked += length
    return _route_primitive_point(chain[-1], chain[-1]["length"])


def _route_corner_sites(chain, side, offsets, band):
    """Yield offset-path miter sites at each internal polyline vertex.

    Greedily filling only the longest current aperture can put one via just
    before a bend and another just after it.  Both are locally legal, yet
    their projections leave an over-pitch aperture *through* the corner that
    no later via can occupy because the two barrels now consume its spacing
    window.  Anchor the bends first at the intersection of their two offset
    centrelines; the ordinary aperture loop can then fill the straight spans
    on either side without that order-dependent trap.

    The returned site is checked against the finite saved polyline, not only
    its infinite supporting lines.  That matters on the outside of a turn,
    where the miter's nearest route point is the vertex and its radial offset
    is larger than the perpendicular offset used to construct it.
    """
    walked = 0.0
    for i, (incoming, outgoing) in enumerate(zip(chain, chain[1:]), 1):
        in_len, out_len = incoming["length"], outgoing["length"]
        walked += in_len
        if in_len <= 1e-12 or out_len <= 1e-12:
            continue
        # A native arc is already a continuously offset curve. The ordinary
        # aperture filler owns its fence; miter anchors are only meaningful at
        # an explicit line-line corner.
        if incoming["kind"] != "line" or outgoing["kind"] != "line":
            continue
        a, b, c = incoming["start"], incoming["end"], outgoing["end"]
        in_dx, in_dy = b[0] - a[0], b[1] - a[1]
        out_dx, out_dy = c[0] - b[0], c[1] - b[1]
        in_u = in_dx / in_len, in_dy / in_len
        out_u = out_dx / out_len, out_dy / out_len
        # Collinear vertices have no corner aperture to anchor.  A U-turn is
        # not a simple routable offset path and is refused by yielding none;
        # the independent fence gate will still expose its unclosed aperture.
        turn_cross = in_u[0] * out_u[1] - in_u[1] * out_u[0]
        turn_dot = in_u[0] * out_u[0] + in_u[1] * out_u[1]
        if abs(turn_cross) <= 1e-9 and turn_dot > 0.0:
            continue
        n1 = side * -in_u[1], side * in_u[0]
        n2 = side * -out_u[1], side * out_u[0]
        mx, my = n1[0] + n2[0], n1[1] + n2[1]
        mlen = math.hypot(mx, my)
        if mlen <= 1e-9:
            continue
        mx, my = mx / mlen, my / mlen
        denominator = mx * n1[0] + my * n1[1]
        if denominator <= 1e-9:
            continue
        for offset in offsets:
            radial = offset / denominator
            x, y = b[0] + mx * radial, b[1] + my * radial
            hits = [(distance, s) for distance, s, projected_side
                    in _project_to_chain_all(chain, x, y)
                    if projected_side == side and distance <= band + 1e-9]
            # A real corner anchor must serve the saved route on BOTH sides
            # of the vertex.  On the inside of a bend the offset centrelines
            # intersect between the arms, so its two finite-segment
            # projections deliberately bracket the vertex rather than both
            # landing exactly on it.
            if (not any(s <= walked + 0.02 for _distance, s in hits)
                    or not any(s >= walked - 0.02
                               for _distance, s in hits)):
                continue
            yield i, walked, x, y, offset


def _project_to_chain_all(chain, px, py):
    """Every finite-primitive ``(distance, arclength, side)`` projection.

    A plated hole beside a bend may physically return current for both arms.
    Keeping only its single nearest polyline point creates a fictitious fence
    aperture through the corner and makes the result depend on segment order.
    Each line/arc therefore gets its own bounded projection; callers select
    the distance band and side they grade.
    """
    hits, walked = [], 0.0
    for primitive in chain:
        a, b, length = (primitive["start"], primitive["end"],
                        primitive["length"])
        if length <= 1e-12:
            continue
        if primitive["kind"] == "line":
            dx, dy = b[0] - a[0], b[1] - a[1]
            raw = ((px - a[0]) * dx + (py - a[1]) * dy) / (length * length)
            fraction = max(0.0, min(1.0, raw))
            qx, qy = a[0] + fraction * dx, a[1] + fraction * dy
            tx, ty = dx / length, dy / length
        else:
            cx, cy = primitive["center"]
            angle = math.atan2(py - cy, px - cx)
            if _route_angle_on_sweep(angle, primitive["start_angle"],
                                     primitive["sweep"]):
                chosen = angle
                if primitive["sweep"] >= 0:
                    fraction = ((angle - primitive["start_angle"])
                                % (2.0 * math.pi)) / primitive["sweep"]
                else:
                    fraction = ((primitive["start_angle"] - angle)
                                % (2.0 * math.pi)) / (-primitive["sweep"])
            else:
                choices = [(math.hypot(px - point[0], py - point[1]), fraction)
                           for fraction, point in ((0.0, a), (1.0, b))]
                _distance, fraction = min(choices)
                chosen = (primitive["start_angle"]
                          + fraction * primitive["sweep"])
            qx = cx + primitive["radius"] * math.cos(chosen)
            qy = cy + primitive["radius"] * math.sin(chosen)
            direction = 1.0 if primitive["sweep"] >= 0 else -1.0
            tx, ty = (-math.sin(chosen) * direction,
                      math.cos(chosen) * direction)
        distance = math.hypot(px - qx, py - qy)
        cross = tx * (py - qy) - ty * (px - qx)
        hits.append((distance, walked + fraction * length,
                     1 if cross >= 0.0 else -1))
        walked += length
    return hits


def _project_to_chain(chain, px, py):
    """Nearest ``(distance, arclength, side)`` on a simple polyline."""
    hits = _project_to_chain_all(chain, px, py)
    return min(hits, key=lambda hit: hit[0]) if hits else None


def _plated_ground_elements(ctx, netcode):
    """Centres of saved GND vias and drilled GND footprint posts/pads."""
    out = []
    for item in ctx.board.GetTracks():
        if item.GetClass() == "PCB_VIA" and item.GetNetCode() == netcode:
            p = item.GetPosition()
            out.append((p.x / 1e6, p.y / 1e6))
    for fp in ctx.board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetCode() != netcode or pad.GetDrillSizeX() <= 0:
                continue
            p = pad.GetPosition()
            out.append((p.x / 1e6, p.y / 1e6))
    return out


def _route_endpoint_refs(ctx, netname, chain):
    """Exact footprint-pad owner at each saved-chain endpoint."""
    refs = []
    for x, y in (chain[0]["start"], chain[-1]["end"]):
        point = ctx.pcbnew.VECTOR2I_MM(x, y)
        matches = []
        for fp in ctx.board.GetFootprints():
            for pad in fp.Pads():
                if (pad.GetNetname() == netname
                        and pad.GetBoundingBox().Contains(point)):
                    matches.append(fp.GetReference())
        matches = sorted(set(matches))
        if len(matches) != 1:
            die(f"route_fence net {netname!r} endpoint ({x:.4f},{y:.4f}) "
                f"belongs to {matches or 'no exact net pad'}; exactly one "
                "package/launch owner is required")
        refs.append(matches[0])
    return tuple(refs)


def _endpoint_span_map(fence_contract):
    """Refdes -> geometry-proven route span owned by its package/launch."""
    out = {}
    for i, row in enumerate(fence_contract.get("endpoint_structures") or []):
        if not isinstance(row, dict):
            die(f"ground_fence.endpoint_structures[{i}] must be a mapping")
        span = float(row.get("maximum_along_route_span_mm", 0.0))
        if span < 0:
            die("ground_fence.endpoint_structures maximum span cannot be "
                "negative")
        for ref in row.get("refs") or []:
            if str(ref) in out:
                die(f"ground_fence.endpoint_structures repeats ref {ref!r}")
            out[str(ref)] = span
    return out


def _fence_side_gaps(chain, elements, side, band, start_span=0.0,
                     end_span=0.0):
    """Along-route apertures outside proven package/launch endpoint spans."""
    length = sum(primitive["length"] for primitive in chain)
    start, stop = float(start_span), length - float(end_span)
    if start >= stop - 1e-9:
        die(f"route_fence endpoint structures consume the complete "
            f"{length:.4f}mm route span ({start_span}+{end_span}mm)")
    points = []
    for x, y in elements:
        for distance, s, projected_side in _project_to_chain_all(
                chain, x, y):
            if distance <= band + 1e-9 and projected_side == side:
                points.append(max(start, min(stop, s)))
    points = sorted({round(s, 4) for s in points})
    boundaries = ([start]
                  + [s for s in points if start + 1e-6 < s < stop - 1e-6]
                  + [stop])
    gaps = [(boundaries[i], boundaries[i + 1])
            for i in range(len(boundaries) - 1)]
    return length, start, stop, points, gaps


@stitch_pass("route_fence")
def p_route_fence(ctx, c):
    """Realize a collision-clean plated-GND fence along both RF flanks.

    The pass consumes the *saved RF centrelines*, not a rectangular attempt
    lattice.  Existing GND vias and drilled launch posts are measured first;
    each new site is accepted only through ``Ctx.try_via`` and the complete
    side is remeasured after every addition.  One via may therefore serve two
    adjacent arms, while a collision-rejected attempted site earns no credit.

    This in-process measurement is an early refusal, not the release verdict.
    ``fence_pitch.py`` independently reopens the final saved board and grades
    the realized aperture, including lead-in and run-out at both endpoints.
    """
    contract = None
    if c.get("contract"):
        contract_path = rel(ctx.cfg, c["contract"])
        try:
            contract = yaml.safe_load(
                contract_path.read_text(encoding="utf-8-sig")) or {}
            contract = contract["rf"]["layout_constraints"]
        except (OSError, KeyError, TypeError, yaml.YAMLError) as exc:
            die(f"stitch.route_fence.contract cannot provide "
                f"rf.layout_constraints from {contract_path}: {exc}")
    route_contract = (contract or {}).get("route") or {}
    fence_contract = (contract or {}).get("ground_fence") or {}

    nets = [str(n) for n in
            (c.get("nets") or route_contract.get("nets") or [])]
    if not nets:
        die("stitch.route_fence.nets must name at least one routed net")
    if c.get("nets") and route_contract.get("nets") \
            and nets != [str(n) for n in route_contract["nets"]]:
        die("stitch.route_fence.nets disagrees with the exact RF-contract "
            "route-net denominator")
    ground = ctx.net(c.get("net", "GND"))
    layer = str(c.get("layer") or route_contract.get("layer") or "F.Cu")
    if c.get("layer") and route_contract.get("layer") \
            and str(c["layer"]) != str(route_contract["layer"]):
        die("stitch.route_fence.layer disagrees with the RF-contract route "
            "layer")
    maximum = float(c.get("maximum_pitch") or
                    fence_contract.get("maximum_along_route_pitch_mm") or 0.0)
    if c.get("maximum_pitch") is not None \
            and fence_contract.get("maximum_along_route_pitch_mm") is not None \
            and abs(float(c["maximum_pitch"]) - float(
                fence_contract["maximum_along_route_pitch_mm"])) > 1e-9:
        die("stitch.route_fence.maximum_pitch disagrees with the RF-contract "
            "maximum_along_route_pitch_mm")
    nominal = float(c.get("nominal_pitch", maximum))
    contract_band = fence_contract.get("maximum_lateral_center_offset_mm")
    if c.get("band") is not None and contract_band is not None \
            and abs(float(c["band"]) - float(contract_band)) > 1e-9:
        die("stitch.route_fence.band disagrees with the RF-contract "
            "maximum_lateral_center_offset_mm")
    band = float(c.get("band") or contract_band or 0.0)
    contract_offset = fence_contract.get("nominal_lateral_center_offset_mm")
    offsets = [float(v) for v in
               (c.get("lateral_offsets") or
                ([contract_offset] if contract_offset is not None else []))]
    if contract_offset is not None and offsets \
            and abs(offsets[0] - float(contract_offset)) > 1e-9:
        die("stitch.route_fence.lateral_offsets[0] must equal the RF-contract "
            "nominal_lateral_center_offset_mm")
    jitters = [float(v) for v in
               (c.get("longitudinal_jitter") or
                [0.0, -0.10, 0.10, -0.20, 0.20, -0.30, 0.30])]
    if maximum <= 0 or nominal <= 0 or nominal > maximum + 1e-9:
        die("stitch.route_fence needs 0 < nominal_pitch <= maximum_pitch")
    if band <= 0 or not offsets or any(v <= 0 or v > band for v in offsets):
        die("stitch.route_fence lateral_offsets must be positive and no "
            "larger than band")
    search_step = float(c.get("longitudinal_step", 0.05))
    if search_step <= 0:
        die("stitch.route_fence.longitudinal_step must be positive")
    max_add = int(c.get("max_new_vias", 5000))
    require_all = str(c.get("require", "all")).lower() == "all"
    via_spacing = c.get("via_spacing")
    if via_spacing is not None:
        via_spacing = float(via_spacing)
        via = get(ctx.cfg, "stitch.via", {}) or {}
        largest_drill = max(float(t.get("drill", via.get("drill", 0.2)))
                            for t in (via.get("tiers") or [via]))
        minimum = largest_drill + float(ctx.tk.h2h)
        if via_spacing + 1e-9 < minimum:
            die(f"stitch.route_fence.via_spacing {via_spacing}mm is below "
                f"drill + saved-board hole-to-hole floor {minimum:.3f}mm")

    processing = [str(n) for n in (c.get("processing_order") or nets)]
    if len(processing) != len(nets) or set(processing) != set(nets):
        die("stitch.route_fence.processing_order must be an exact "
            "permutation of the RF-contract route-net denominator")
    chains = {net: _simple_track_chain(ctx, net, layer) for net in processing}
    span_map = _endpoint_span_map(fence_contract)
    endpoint_spans = {}
    for net, chain in chains.items():
        if fence_contract.get("endpoint_structures"):
            refs = _route_endpoint_refs(ctx, net, chain)
            missing = [ref for ref in refs if ref not in span_map]
            if missing:
                die(f"route_fence net {net!r} endpoint ref(s) {missing} have "
                    "no geometry-proven ground_fence.endpoint_structures row")
        else:
            refs = ("route-start", "route-end")
        endpoint_spans[net] = (span_map.get(refs[0], 0.0),
                               span_map.get(refs[1], 0.0), refs)
    added, corner_added, passed, total = 0, 0, 0, 2 * len(chains)
    unresolved = []

    # Reserve the scarce bend sites before the greedy straight-span filler
    # can consume their via-spacing windows.  This is deliberately a separate
    # first phase across every RF net: changing `processing_order` must not
    # decide whether a later net's corner is physically realizable.
    for net, chain in chains.items():
        for side in (-1, 1):
            for _index, _s, x, y, _offset in _route_corner_sites(
                    chain, side, offsets, band):
                if added >= max_add:
                    break
                if ctx.try_via(ground, x, y,
                               spacing_override=via_spacing):
                    added += 1
                    corner_added += 1

    for net, chain in chains.items():
        for side in (-1, 1):
            tag = "right" if side < 0 else "left"
            start_span, end_span, refs = endpoint_spans[net]
            while True:
                elements = _plated_ground_elements(ctx, ground.GetNetCode())
                length, start, stop, points, gaps = _fence_side_gaps(
                    chain, elements, side, band, start_span, end_span)
                worst = max(gaps, key=lambda pair: pair[1] - pair[0])
                aperture = worst[1] - worst[0]
                if aperture <= maximum + 1e-9:
                    passed += 1
                    print(f"route fence {net} {tag}: {len(points)} element(s), "
                          f"worst aperture {aperture:.4f}mm / {maximum:.4f}mm; "
                          f"graded s={start:.2f}..{stop:.2f} after "
                          f"{refs[0]}={start_span:.2f}mm, "
                          f"{refs[1]}={end_span:.2f}mm endpoint structures")
                    break
                if added >= max_add:
                    unresolved.append(
                        f"{net} {tag}: maximum new-via budget {max_add} "
                        f"reached with {aperture:.4f}mm aperture")
                    break

                a, b = worst
                # Seed long empty spans at the nominal cadence.  Once a span
                # is within two maximum pitches, its midpoint maximizes the
                # clearance to both neighbours and is the most repairable site.
                target = ((a + b) / 2.0 if b - a <= 2.0 * maximum
                          else a + nominal)
                # Search EVERY arclength position that could close the gap,
                # not merely +/- a few nominal jitters.  For a long endpoint
                # span the first new element must be no farther than `maximum`
                # from `a`; for a span shorter than 2*maximum it must also be
                # within `maximum` of `b`.  Exhausting this closed interval is
                # what makes "no legal site" evidence about geometry rather
                # than about one unlucky seed (the first v5 trial abandoned
                # whole 14-31mm flanks after probing only s=0.6..1.4mm).
                low = a + search_step
                high = min(b - search_step, a + maximum)
                if b - a <= 2.0 * maximum:
                    low = max(low, b - maximum)
                candidates = [target + jitter for jitter in jitters]
                if high >= low - 1e-9:
                    count = int(math.floor((high - low) / search_step))
                    candidates.extend(low + i * search_step
                                      for i in range(count + 1))
                    candidates.append(high)
                candidates = sorted(
                    {round(s, 4) for s in candidates
                     if a + 1e-6 < s < b - 1e-6 and low - 1e-9 <= s <= high + 1e-9},
                    key=lambda s: (abs(s - target), s))
                placed = False
                for s in candidates:
                    x, y, nx, ny = _route_point(chain, s)
                    for offset in offsets:
                        vx = x + side * nx * offset
                        vy = y + side * ny * offset
                        if ctx.try_via(ground, vx, vy,
                                       spacing_override=via_spacing):
                            added += 1
                            placed = True
                            break
                    if placed:
                        break
                if not placed:
                    unresolved.append(
                        f"{net} {tag}: no legal site can split saved-board "
                        f"aperture s={a:.3f}..{b:.3f}mm ({aperture:.4f}mm)")
                    break

    ctx.bump("rf_fence_vias", added)
    ctx.bump("rf_fence_corner_vias", corner_added)
    ctx.bump("rf_fence_sides_ok", passed)
    ctx.counts["rf_fence_sides_total"] = total
    print(f"route fence: {added} new via(s) ({corner_added} corner anchor(s)), "
          f"{passed}/{total} flank(s) inside the in-process aperture bound")
    if unresolved:
        for finding in unresolved:
            print(f"  RF FENCE UNRESOLVED: {finding}")
        if require_all:
            ctx.failures.extend("route fence: " + f for f in unresolved)


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

    copper_layers = [layer for layer in ctx.board.GetEnabledLayers().Seq()
                     if pcbnew.IsCopperLayer(layer)]
    # This check runs inside the rings/angles candidate loop. Build the set
    # once per rescued net rather than scanning every footprint for every
    # candidate (the latter scales as targets*candidates*all-board-pads).
    copper_smd_pads = [
        (p2, p2.GetBoundingBox())
        for fp2 in ctx.board.GetFootprints() for p2 in fp2.Pads()
        if p2.GetDrillSize().x <= 0
        and any(p2.IsOnLayer(layer) for layer in copper_layers)
    ]

    def lands_in_smd_pad(x, y):
        """True when an adjacent-via candidate is actually via-in-pad.

        `via_site_ok` deliberately permits same-net copper, so without this
        semantic guard a rescue for one long/nearby pad can land in another
        same-net SMD land even though `via_in_pad: false` was requested.
        """
        pos = pcbnew.VECTOR2I_MM(x, y)
        return any(bbox.Contains(pos) and pad.HitTest(pos)
                   for pad, bbox in copper_smd_pads)
    # `seed_stubs` runs before this pass and may deliberately reach a legal
    # barrel outside the small local pad search box.  Fresh/reloaded boards
    # have authoritative endpoint connectivity here, so credit a pad whose
    # same-net track component already contains a via.  The geometric test
    # below remains necessary for a bare via-in-pad with no explicit track.
    ctx.board.BuildConnectivity()
    conn = ctx.board.GetConnectivity()

    def has_via(pad):
        if any(item.GetClass() == "PCB_VIA"
               and item.GetNetCode() == pad.GetNetCode()
               for item in conn.GetConnectedItems(pad)):
            return True
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
            if vip and ctx.try_via(net_obj, px, py,
                                   allow_via_in_pad=True):
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
                    if not vip and lands_in_smd_pad(vx, vy):
                        continue
                    # Probe the complete via+stub candidate before committing
                    # either item.  The former order called try_via first;
                    # when the stub then collided, the rejected via remained
                    # on the board and consumed the spacing window needed by
                    # later candidates (programmable-usb2-hub, 2026-08-02).
                    if ctx.via_choice(net_obj, vx, vy) is None:
                        continue
                    if ctx.tk.collides(px, py, vx, vy, stub_w,
                                       p.GetNetCode(), lay) is not None:
                        continue
                    if not ctx.try_via(net_obj, vx, vy):
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
        txt = dru.read_text(encoding="utf-8-sig")
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
    target_tries = int(c.get("targets", 1))
    max_pending = int(c.get("max_pending", 8))
    budget_s = float(c.get("budget_s", 30.0))
    if max_pending <= 0 or budget_s <= 0:
        die("stitch.astar_fallback max_pending and budget_s must be positive")
    if len(ctx.pending) > max_pending:
        residual = ", ".join(f"{ref}.{pad}" for ref, pad in ctx.pending)
        ctx.bump("astar_fallback", 0)
        print(f"A* fallback SKIPPED: {len(ctx.pending)} residual endpoints exceed "
              f"max_pending={max_pending}; author explicit dogbones: {residual}")
        return
    layer_names = c.get("layers")
    astar_layers = None
    if layer_names is not None:
        if isinstance(layer_names, str):
            layer_names = [layer_names]
        if not isinstance(layer_names, (list, tuple)):
            die("stitch.astar_fallback.layers must be one or two copper "
                "layer names")
        astar_layers = tuple(_layer_id(ctx.pcbnew, name)
                             for name in layer_names)
        if not 1 <= len(astar_layers) <= 2 or \
                len(set(astar_layers)) != len(astar_layers):
            die("stitch.astar_fallback.layers must name one or two distinct "
                "copper layers")

    # The toolkit's A* emits its own default 0.45/0.2 vias, which are BELOW
    # a 2-layer standard-tier board's floors. Pinning the geometry is config;
    # `restore` is unconditional so an exception cannot leak the patched
    # toolkit into later passes. `net` may be a LIST (GND + 3V3): each plane
    # net's own via targets, so an unserved 3V3 pin is A*-recovered too.
    pin = c.get("via")
    vs = vd = htc = None
    _orig = (ctx.tk.add_via, ctx.tk.via_site_ok)
    if pin:
        vs, vd = float(pin["size"]), float(pin["drill"])
        if "hole_to_copper" in pin:
            htc = float(pin["hole_to_copper"])
        else:
            # Reuse the matching stitch-via tier's fab-specific hole model.
            # Tier geometry itself only owns size/drill floors, while a board
            # may intentionally require a stricter drilled-hole-to-copper gap
            # than pcb_toolkit's generic default.
            tiers = get(ctx.cfg, "stitch.via.tiers", []) or []
            for tier in tiers:
                if (abs(float(tier.get("size", -1)) - vs) < 1e-9 and
                        abs(float(tier.get("drill", -1)) - vd) < 1e-9 and
                        "hole_to_copper" in tier):
                    htc = float(tier["hole_to_copper"])
                    break
        ctx.tk.add_via = (lambda x, y, net, size=None, drill=None, _f=_orig[0]:
                          _f(x, y, net, size=vs, drill=vd))

        def pinned_via_site_ok(x, y, nc, size=None, drill=None,
                               _f=_orig[1], **kw):
            if htc is not None:
                kw.setdefault("hole_to_copper", htc)
            return _f(x, y, nc, size=vs, drill=vd, **kw)

        ctx.tk.via_site_ok = pinned_via_site_ok

    def via_coords():
        return {(round(t.GetPosition().x / 1e6, 2),
                 round(t.GetPosition().y / 1e6, 2))
                for t in ctx.board.GetTracks() if t.GetClass() == "PCB_VIA"}

    before = via_coords()      # A* adds vias inside the toolkit — diff them
    pending = list(ctx.pending)
    fixed = 0
    budget_started = time.monotonic()
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
                elapsed = time.monotonic() - budget_started
                if elapsed >= budget_s:
                    still.append((ref, p.GetNumber()))
                    print(f"  A* budget exhausted before {ref}.{p.GetNumber()} "
                          f"at {elapsed:.3f}s/{budget_s:.3f}s")
                    continue
                candidates = []
                for tx, ty in sorted(targets,
                                     key=lambda q: math.hypot(px - q[0], py - q[1])):
                    if 0.3 < math.hypot(px - tx, py - ty) < float(c.get("max_dist", 10.0)):
                        candidates.append((tx, ty))
                        if len(candidates) >= target_tries:
                            break
                print(f"  A* trying {ref}.{p.GetNumber()}: "
                      f"{len(candidates)} target(s), elapsed={elapsed:.3f}s")
                found = False
                for tgt in candidates:
                    if time.monotonic() - budget_started >= budget_s:
                        break
                    if ctx.tk.verified_astar(
                            netname, (px, py), tgt, w,
                            window=window, attempts=attempts,
                            via_size=vs if vs is not None else 0.45,
                            via_drill=vd if vd is not None else 0.2,
                            layers=astar_layers, hole_to_copper=htc):
                        found = True
                        break
                if found:
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
    print(f"A* fallback: recovered {fixed}, {len(pending)} left; "
          f"elapsed={time.monotonic() - budget_started:.3f}s/"
          f"{budget_s:.3f}s")


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
        attach = set()
        for t in ctx.board.GetTracks():
            if t.GetClass() == "PCB_VIA" or t.GetNetCode() != v.GetNetCode():
                continue
            # Copper overlaps when the distance between the track centreline
            # and via centre is no greater than BOTH copper radii combined.
            # Using only the via radius falsely pruned legitimate via banks
            # whose centres are offset inside a wide power track (the 2A hub
            # In1 distributor uses 2--3 mm tracks with 0.46 mm vias).
            touch_r = (v.GetWidth(pcbnew.F_Cu) + t.GetWidth()) / 2e6
            if seg_d2(vx, vy, t.GetStart().x / 1e6, t.GetStart().y / 1e6,
                      t.GetEnd().x / 1e6, t.GetEnd().y / 1e6) <= touch_r ** 2:
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
                bb.Inflate(v.GetWidth(pcbnew.F_Cu) // 2)
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
    scope = c.get("scope", "emitted")
    if scope not in ("emitted", "all"):
        die("prune_stitch_dangling.scope must be 'emitted' or 'all'")
    zones = [z for z in ctx.board.Zones() if not z.GetIsRuleArea()
             and z.GetNetname()]
    if zones and not any(z.IsFilled() for z in zones):
        die("prune_stitch_dangling must run AFTER `fill` — on an unfilled "
            "board every stitch via looks dangling and would be pruned")
    emitted = ctx.emitted
    if not emitted and scope == "emitted":
        print("prune_stitch_dangling: no stitch-emitted vias this run")
        return

    def seg_d2(px, py, ax, ay, bx, by):
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
        return (px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2

    dead = []
    dead_details = []
    for v in [t for t in ctx.board.GetTracks() if t.GetClass() == "PCB_VIA"]:
        vx, vy = v.GetPosition().x / 1e6, v.GetPosition().y / 1e6
        if scope == "emitted" and not any(
                abs(vx - ex) <= tol and abs(vy - ey) <= tol
                for ex, ey in emitted):
            continue                        # not ours — never touch it
        attach = set()
        for t in ctx.board.GetTracks():
            if t.GetClass() == "PCB_VIA" or t.GetNetCode() != v.GetNetCode():
                continue
            touch_r = (v.GetWidth(pcbnew.F_Cu) + t.GetWidth()) / 2e6
            if seg_d2(vx, vy, t.GetStart().x / 1e6, t.GetStart().y / 1e6,
                      t.GetEnd().x / 1e6, t.GetEnd().y / 1e6) <= touch_r ** 2:
                attach.add(t.GetLayer())
        for fp in ctx.board.GetFootprints():
            for p in fp.Pads():
                if p.GetNetCode() != v.GetNetCode():
                    continue
                bb = p.GetBoundingBox()
                bb.Inflate(v.GetWidth(pcbnew.F_Cu) // 2)
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
                # FILLED polys, not the zone outline — the whole point.  A
                # via ring touching the filled boundary is connected even if
                # its centre is just outside the polygon, so use the same
                # copper-touch predicate as island grouping rather than a
                # centre-only Contains() test.
                if z.IsFilled():
                    polys = z.GetFilledPolysList(lay)
                    if any(_copper_reaches(polys.Outline(i), v.GetPosition(),
                                           v.GetWidth(pcbnew.F_Cu) // 2)
                           for i in range(polys.OutlineCount())):
                        attach.add(lay)
        if len(attach) < minlay:
            dead.append(v)
            dead_details.append(
                (v.GetNetname(), vx, vy,
                 [ctx.board.GetLayerName(layer) for layer in sorted(attach)]))
    for v in dead:
        ctx.remove(v)
    ctx._used = None
    ctx.bump("stitch_dangling_pruned", len(dead))
    if scope == "emitted":
        print(f"pruned {len(dead)} dangling stitch-emitted vias "
              f"(of {len(emitted)} emitted)")
    else:
        total = sum(1 for t in ctx.board.GetTracks()
                    if t.GetClass() == "PCB_VIA") + len(dead)
        print(f"pruned {len(dead)} dangling vias across all {total} vias")
    for netname, x, y, layers in dead_details:
        print(f"  prune {netname} via ({x:.3f},{y:.3f}): "
              f"same-net copper on {layers or 'no layers'}; need {minlay}")


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
    # Keep newly emitted centres separately: try_via() deliberately returns
    # only success/failure, and every successful centre is inside the island
    # by construction.  Existing copper items are evaluated with
    # _island_holds() below so this early rescue pass uses the same
    # copper-overlap semantics as authoritative heal_islands.  The former
    # centre-only/endpoint-only checks misclassified a via ring touching an
    # island edge, or a track body crossing a small island, as disconnected.
    emitted_centres_by_net = {}
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
                isl = {"chain": o, "layer": lay}
                if any(_island_holds(ctx, isl, t)
                       for t in ctx.board.GetTracks()
                       if t.GetClass() == "PCB_VIA"
                       and t.GetNetname() == nn):
                    continue
                if any(o.PointInside(p)
                       for p in emitted_centres_by_net.get(nn, [])):
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
                if any(_island_holds(ctx, isl, t)
                       and not (o.PointInside(t.GetStart())
                                and o.PointInside(t.GetEnd()))
                       for t in ctx.board.GetTracks()
                       if t.GetClass() == "PCB_TRACK" and t.GetNetname() == nn
                       and t.GetLayer() == lay):
                    continue
                has_pad = any(_island_holds(ctx, isl, p2)
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
                            emitted_centres_by_net.setdefault(nn, []).append(
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
def _copper_reaches(o, center, radius):
    """True if a disc of `radius` (IU) centred at `center` OVERLAPS the filled
    outline `o` (a closed SHAPE_LINE_CHAIN): the centre is inside the fill,
    OR the fill's nearest edge point is within `radius` of the centre.

    This is KiCad's own copper-touch connectivity. A same-net via annular
    ring, a track body, or a pad whose copper reaches a filled island is
    CONNECTED to it — even when its geometric CENTRE sits just outside the
    island. The old via-centre-in-poly test misses exactly this: a plane via
    whose ring overlaps a pinched-off fill patch (the patch's own edge lies
    across the ring, the via centre a hair outside it) reads as UNSEATED, so
    the patch becomes a phantom orphan group that no legal via can bridge
    (every in-patch site is inside the existing via's hole-to-hole spacing).
    `heal_islands` then declares it unbridgeable and the post-refill re-verify
    hard-errors on copper kicad-cli DRC reports as 0-unconnected — a FALSE
    positive that stalls the stitch (cooksense v1.2, task#21, 2026-07-24)."""
    if o.PointInside(center):
        return True
    if radius <= 0:
        return False
    np = o.NearestPoint(center)
    dx, dy = np.x - center.x, np.y - center.y
    return dx * dx + dy * dy <= radius * radius


def _island_holds(ctx, isl, item):
    """Is this same-net track/via/pad seated on the island — i.e. does its
    COPPER overlap the FILLED outline (layer-aware)? Overlap, not centre-in-
    poly: a via/track/pad connects to a pour the instant its copper touches
    it, so the seating test must agree with KiCad's connectivity, or a fill
    patch that overlaps a same-net via ring is mis-read as an orphan (see
    _copper_reaches)."""
    o, lay = isl["chain"], isl["layer"]
    cls = item.GetClass()
    if cls == "PCB_VIA":
        if not item.GetLayerSet().Contains(lay):
            return False
        try:                        # KiCad 10 vias carry a PER-LAYER annular
            w = item.GetWidth(lay)  # ring; the layer-aware width is the ring
        except TypeError:           # OD that actually overlaps this island
            w = item.GetWidth()
        return _copper_reaches(o, item.GetPosition(), w // 2)
    if cls == "PCB_TRACK":
        if item.GetLayer() != lay:
            return False
        s, e = item.GetStart(), item.GetEnd()
        mid = ctx.pcbnew.VECTOR2I((s.x + e.x) // 2, (s.y + e.y) // 2)
        r = item.GetWidth() // 2
        return any(_copper_reaches(o, p, r) for p in (s, e, mid))
    if cls == "PAD":
        # A pad's centre-in-poly is kept deliberately strict: broadening it to
        # the pad's circular bounding radius would over-reach a rect pad's real
        # copper and risk merging a GENUINE orphan that merely sits near a pad
        # (weakening the flag). The reported false-positive class is via-ring /
        # track overlap, so only those two seating tests move to copper-touch.
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


def _via_overlap_site(ctx, net, ia, ib, size=None, drill=None):
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
            kwargs = {}
            if size is not None:
                kwargs["exact_size"] = size
            if drill is not None:
                kwargs["exact_drill"] = drill
            if ctx.try_via(net, x, y, **kwargs):
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
    local_via = c.get("via") or {}
    if not isinstance(local_via, dict):
        die("heal_islands.via must be a mapping with optional size/drill")
    unknown_via = sorted(set(local_via) - {"size", "drill"})
    if unknown_via:
        die(f"heal_islands.via has unknown key(s) {unknown_via}")
    vs = float(local_via["size"]) if "size" in local_via else None
    vd = float(local_via["drill"]) if "drill" in local_via else None
    if (vs is None) != (vd is None):
        die("heal_islands.via must declare size and drill together")
    if vs is not None and not (vs > vd > 0):
        die("heal_islands.via needs size > drill > 0")
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
            pt = _via_overlap_site(ctx, net, ia, ib, vs, vd)
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


def _heal_snapshot_path(ctx):
    """Diagnostic snapshots belong in the build tree, never beside canon.

    A ``*.heal_failed.kicad_pcb`` in ``04_kicad`` makes KiCad synthesize a
    matching ``.kicad_pro`` when the snapshot is inspected.  That creates a
    second project basename and correctly trips the repository's one-board /
    one-project contract on the next rules generation.  Keep the evidence,
    but keep it in the configured build directory where it cannot masquerade
    as another canonical board project."""
    build = rel(ctx.cfg, get(ctx.cfg, "project.build_dir", "06_build/route"))
    build.mkdir(parents=True, exist_ok=True)
    return build / (ctx.path.stem + ".heal_failed" + ctx.path.suffix)


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
            # The filled geometry otherwise exists only in this interpreter;
            # a hard error exits before cmd_stitch's final Save(), erasing the
            # exact islands that need inspection.  Preserve a clearly named
            # diagnostic snapshot (never the canonical board) so the caller
            # can distinguish a genuine split from a grouping false positive.
            snap = _heal_snapshot_path(ctx)
            ctx.board.Save(str(snap))
            die(f"heal_islands: net {netname!r} still shows {now} "
                f"disconnected island group(s) after healing (was {was}) — "
                f"the bridge did not merge the pour; a heal that does not "
                f"reduce the island count is an ERROR, not a no-op; "
                f"diagnostic snapshot saved to {snap}")
    left = sorted(n for n, g in after.items() if len(g) > 1)
    if left:
        snap = _heal_snapshot_path(ctx)
        ctx.board.Save(str(snap))
        die(f"heal_islands: net(s) {left} split after heal+refill (a "
            f"bridge for another net can re-slice a pour it crosses) — "
            f"refusing to report a heal that left splits behind; "
            f"diagnostic snapshot saved to {snap}")
    if c.get("clear_rescue_failures", False):
        # island_rescue runs before this authoritative refill/re-group and can
        # legitimately record an unstitchable intermediate island that a
        # later same-net bridge eliminates.  Keep the conservative default,
        # but let a board whose pass order explicitly relies on heal_islands
        # retire only those stale findings whose net now verifies as one (or
        # zero) group.  Findings for every still-split net remain untouched.
        zone_nets = {z.GetNetname() for z in ctx.board.Zones()
                     if z.GetNetname() and not z.GetIsRuleArea()}
        resolved = {n for n in zone_nets if len(after.get(n, [])) <= 1}
        old = len(ctx.failures)
        ctx.failures = [f for f in ctx.failures
                        if not (f.startswith("island ")
                                and f.split("/", 1)[0][7:] in resolved)]
        cleared = old - len(ctx.failures)
        if cleared:
            print(f"heal_islands: cleared {cleared} stale island_rescue "
                  f"finding(s) after authoritative refill verification")
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


def _same_arc_exists(ctx, start, mid, end, lid, code, tol=0.02):
    """Idempotency probe for one native same-net ``PCB_ARC``."""
    def near(a, b):
        return abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) <= tol

    for item in ctx.board.GetTracks():
        if (item.GetClass() != "PCB_ARC" or item.GetNetCode() != code
                or item.GetLayer() != lid):
            continue
        actual_start, actual_end = _ends_mm(item)
        point = item.GetMid()
        actual_mid = point.x / 1e6, point.y / 1e6
        if (near(actual_mid, mid)
                and ((near(actual_start, start) and near(actual_end, end))
                     or (near(actual_start, end) and near(actual_end, start)))):
            return True
    return False


def _same_via_exists(ctx, x, y, code, tol=0.05):
    for t in ctx.board.GetTracks():
        if t.GetClass() == "PCB_VIA" and t.GetNetCode() == code:
            vx, vy = t.GetPosition().x / 1e6, t.GetPosition().y / 1e6
            if abs(vx - x) <= tol and abs(vy - y) <= tol:
                return True
    return False


def _pin_touched(ctx, px, py, code, tol=0.16, pad=None):
    """Is the pin pad touched by same-net track copper or a via — i.e. did
    the seed stub actually reach it?

    THE PROOF IS THE PAD SHAPE, not a radius around the pad ORIGIN
    (cooksense v1.2, 2026-07-25). The old test only accepted copper within
    `tol` of (px,py). That is fine for an 0402 (0.54x0.64) but WRONG for
    anything larger: a via-in-pad landing legitimately on the far end of an
    0603 GND pad — the only site with clearance, MEASURED — was declared
    "connects nothing" and hard-errored the stitch, while the same via
    0.15mm from the origin passed. A via-in-pad is proven by LANDING ON THE
    PAD'S COPPER; the radius stays as the fallback when the caller has no
    pad handle (and for THT pads, whose plated barrel bonds anywhere)."""
    def hits(x, y):
        if math.hypot(x - px, y - py) <= tol:
            return True
        if pad is None:
            return False
        try:
            pt = ctx.pcbnew.VECTOR2I_MM(round(x, 4), round(y, 4))
            return pad.GetEffectiveShape(pad.GetLayer()).Collide(pt)
        except Exception:
            return False
    for t in ctx.board.GetTracks():
        if t.GetNetCode() != code:
            continue
        if t.GetClass() == "PCB_VIA":
            if hits(t.GetPosition().x / 1e6, t.GetPosition().y / 1e6):
                return True
        else:
            for e in _ends_mm(t):
                if hits(e[0], e[1]):
                    return True
    return False


def _copper_item_identity(item):
    """Compact, best-effort identity for a collision refusal.

    A bare ``foreign copper`` result proves safety but hides the object the
    author must route around.  Keep this diagnostic side-effect free and
    tolerant of KiCad SWIG API differences so a reporting failure can never
    weaken the underlying refusal.
    """
    if item is None:
        return "unknown item"
    try:
        kind = str(item.GetClass())
    except Exception:
        kind = type(item).__name__
    try:
        net = str(item.GetNetname() or "<no-net>")
    except Exception:
        net = "<unknown-net>"
    if kind in ("PCB_PAD", "PAD"):
        try:
            fp = item.GetParentFootprint()
            return f"{fp.GetReference()}.{item.GetNumber()}[{net}]"
        except Exception:
            pass
    try:
        if kind == "PCB_VIA":
            p = item.GetPosition()
            return (f"{kind}[{net}]@({p.x / 1e6:.3f},"
                    f"{p.y / 1e6:.3f})")
        a, b = item.GetStart(), item.GetEnd()
        return (f"{kind}[{net}] ({a.x / 1e6:.3f},{a.y / 1e6:.3f})->"
                f"({b.x / 1e6:.3f},{b.y / 1e6:.3f})")
    except Exception:
        return f"{kind}[{net}]"


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
             via: {size: 0.41, drill: 0.15}, # optional per-bank override
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
        if not pin and not str(stub.get("why", "")).strip():
            die(f"seed_stubs.stubs[{i}]: a via/segment bank without `pin` "
                "must declare `why` so its current/connectivity ownership is "
                "not anonymous")
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
        stub_via = dict(via)
        override = stub.get("via", {}) or {}
        if not isinstance(override, dict):
            die(f"seed_stubs.stubs[{i}].via must be a mapping")
        stub_via.update(override)
        _stub_tier_via(ctx.cfg, stub_via)
        stub_vs = float(stub_via.get("size", vs))
        stub_vd = float(stub_via.get("drill", vd))
        for seg in stub.get("segments", []) or []:
            lid = _layer_id(pcbnew, seg["layer"])
            w = float(seg["width"])
            pts = seg["pts"]
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                ax, ay, bx, by = (round(v, 3) for v in (ax, ay, bx, by))
                hit = tk.collides(ax, ay, bx, by, w, code, lid)
                if hit is not None:
                    conflict = (f"seg ({ax},{ay})->({bx},{by}) "
                                f"{seg['layer']} against "
                                f"{_copper_item_identity(hit)}")
                    break
                prims.append(("seg", ax, ay, bx, by, w, lid))
            if conflict:
                break
        if conflict is None:
            for arc in stub.get("arcs", []) or []:
                lid = _layer_id(pcbnew, arc["layer"])
                w = float(arc["width"])
                try:
                    start = tuple(round(float(v), 3) for v in arc["start"])
                    mid = tuple(round(float(v), 3) for v in arc["mid"])
                    end = tuple(round(float(v), 3) for v in arc["end"])
                except (KeyError, TypeError, ValueError) as exc:
                    die(f"seed_stubs.stubs[{i}].arcs needs numeric "
                        f"start/mid/end coordinate pairs: {exc}")
                if not all(len(point) == 2 for point in (start, mid, end)):
                    die(f"seed_stubs.stubs[{i}].arcs start/mid/end must be "
                        "two-coordinate points")
                candidate = tk.make_arc(start, mid, end, net, lid, w)
                hit = tk.collides_item(candidate, code, lid)
                if hit is not None:
                    conflict = (f"arc {start}->{mid}->{end} "
                                f"{arc['layer']} against "
                                f"{_copper_item_identity(hit)}")
                    break
                prims.append(("arc", start, mid, end, w, lid))
        if conflict is None:
            for (vx, vy) in stub.get("vias", []) or []:
                vx, vy = round(vx, 3), round(vy, 3)
                if (not _same_via_exists(ctx, vx, vy, code)
                        and not tk.via_site_ok(vx, vy, code,
                                              size=stub_vs,
                                              drill=stub_vd)):
                    conflict = f"via ({vx},{vy})"
                    break
                prims.append(("via", vx, vy, stub_vs, stub_vd))
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
            elif prim[0] == "arc":
                _, start, mid, end, w, lid = prim
                if _same_arc_exists(ctx, start, mid, end, lid, code):
                    skipped += 1
                    continue
                tk.add_arc(start, mid, end, net, lid, w)
                placed += 1
            else:
                _, vx, vy, prim_vs, prim_vd = prim
                if _same_via_exists(ctx, vx, vy, code):
                    skipped += 1
                    continue
                tk.add_via(vx, vy, net, size=prim_vs, drill=prim_vd)
                placed += 1
        if pinpad is not None:
            px, py = (pinpad.GetPosition().x / 1e6,
                      pinpad.GetPosition().y / 1e6)
            if not _pin_touched(ctx, px, py, code, pad=pinpad):
                die(f"seed_stubs.stubs[{i}]: the stub placed for {pin} does "
                    f"not reach the pin pad — it connects nothing (check the "
                    f"first segment starts at the pad)")
        served += 1
    ctx.bump("seed_stubs", placed)
    print(f"seed_stubs: {served} bank(s) served ({placed} primitives/vias "
          f"placed, {skipped} idempotent-skip), {refused} refused")


# ------------------------------------------ same-net zone priority unify ------
def _zone_overlap_pairs(ctx):
    """Return ``(same_net_same_prio, cross_net_filled)`` zone pairs.

    Same-net priority conflicts are an OUTLINE property: KiCad reports
    ``zones_intersect`` when same-priority zone outlines overlap, even though
    their eventual copper is one electrical net.  Different-net safety is a
    FILLED-COPPER property instead.  It is normal for a full-board GND zone's
    outline to contain higher-priority power zones; zone priority removes GND
    copper beneath them.  Calling that ordinary nesting a short deadlocks the
    stitch pipeline.  A cross-net pair is therefore returned only when the
    post-fill copper polygons have positive-area overlap on a shared layer.

    The caller runs after ``fill`` and again immediately after its own refill,
    so an unfilled cross-net outline is deliberately not guessed about here;
    the final DRC remains the independent shorting-items authority.
    """
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
                if not (za.IsFilled() and zb.IsFilled()):
                    continue
                filled_overlap = False
                for layer in za.GetLayerSet().Seq():
                    if (not pcbnew.IsCopperLayer(layer)
                            or not zb.GetLayerSet().Contains(layer)):
                        continue
                    pa = za.GetFilledPolysList(layer)
                    pb = zb.GetFilledPolysList(layer)
                    if pa.OutlineCount() == 0 or pb.OutlineCount() == 0:
                        continue
                    copper_inter = pcbnew.SHAPE_POLY_SET(pa)
                    copper_inter.BooleanIntersection(pb)
                    if (copper_inter.OutlineCount() > 0
                            and copper_inter.Area() > 0):
                        filled_overlap = True
                        break
                if filled_overlap:
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
      (b) zero new violations: cross-net FILLED-COPPER overlap is a SHORT and
          is REFUSED loudly (never priority-bumped — that would hide a short);
          overlapping outlines resolved by zone priority are valid nesting;
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
            f"FILLED-COPPER SHORT, not a same-net priority union. Refusing "
            f"to touch it: a cross-net copper intersection is design work "
            f"(shorting_items), "
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


def cmd_stitch(cfg, target_board=None):
    global MM
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import pcbnew
    MM = pcbnew.ToMM
    _stitch_tier_geometry(cfg)     # tier floors BEFORE any via is emitted
    target = _target_board(cfg, target_board)
    if not target.is_file():
        die(f"stitch target board not found: {target}")

    # Stitch can cross explicit fresh-interpreter barriers after removals.
    # Each process must have a stable but DISJOINT UUID stream: reseeding every
    # process with one constant would collide with objects emitted before the
    # barrier, while leaving the stream random makes a clean replay unstable.
    # The authenticated resume index is the deterministic phase namespace.
    state_path = Path(str(target) + Ctx.STATE_SUFFIX)
    resume_hint = 0
    if state_path.is_file():
        resume_hint = int(json.loads(
            state_path.read_text(encoding="utf-8-sig")).get("resume", 0))
    _seed_uuid_stream(pcbnew, target.stem, f"route-stitch-{resume_hint}")
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
        command = [sys.executable, os.path.abspath(__file__), "stitch",
                   str(cfg["_path"]), "--root", str(cfg["_root"])]
        if target_board is not None:
            command.extend(["--target-board", str(target_board)])
        os.execv(sys.executable, command)

    start = ctx.load_state()
    if start != resume_hint:
        die(f"stitch resume state changed while loading: expected "
            f"{resume_hint}, got {start}")
    for i in range(start, len(order)):
        name = order[i]
        if name in ("reload", "fresh_reload"):
            print(f"\n-- {name} --")
            pass_start = time.perf_counter()
            if name == "fresh_reload":
                record_pass_timing(cfg, "stitch", name,
                                   time.perf_counter() - pass_start,
                                   counters={"barrier": 1})
                barrier(i + 1, "fresh connectivity rebuild")
            if ctx.dirty:
                record_pass_timing(cfg, "stitch", name,
                                   time.perf_counter() - pass_start,
                                   counters={"barrier": 1})
                barrier(i + 1, "explicit")
            print("   nothing removed since the last barrier — no-op")
            record_pass_timing(cfg, "stitch", name,
                               time.perf_counter() - pass_start,
                               counters={"barrier": 0})
            continue
        cfgblk = get(cfg, f"stitch.{name}", {}) or {}
        print(f"\n-- {name} --")
        before = dict(ctx.counts)
        pass_start = time.perf_counter()
        PASSES[name](ctx, cfgblk)
        deltas = {k: v - before.get(k, 0) for k, v in ctx.counts.items()
                  if v - before.get(k, 0)}
        record_pass_timing(cfg, "stitch", name,
                           time.perf_counter() - pass_start,
                           counters=deltas)
        # An IMPLICIT barrier after any pass that removed something. Without
        # it the NEXT pass's GetTracks() raises on a poisoned SWIG iterator,
        # and (worse) the removals stay half-applied on a saved board.
        if ctx.dirty and i + 1 < len(order):
            barrier(i + 1, f"after {name}")
    ctx.board.Save(str(ctx.path))
    if ctx.state_path().is_file():
        ctx.state_path().unlink()
    print(f"\nsaved {ctx.path}")
    rc = verify_saved_fill(ctx.path)
    if rc == 0:
        _critical_route_gate(cfg, require_connected=True, board=target)
    print("NEXT: run your rules generator LAST — this save did not touch "
          ".kicad_pro, but any pcbnew save in the chain clobbers netclasses.")
    return rc


def verify_saved_fill(path):
    """READ BACK THE SAVED FILE and prove the pour survived (canon M-SHIP).

    THE INCIDENT. usb-hub-3s-v3 shipped v1.6, v1.7 and v1.8 with 51 zones on
    the board and ZERO copper pour in the gerbers — 44287.91 mm2 missing, G36
    region count 0 on all four copper layers. Every gate was green, because
    `kicad-cli pcb drc --refill-zones` REFILLS IN MEMORY and therefore returns
    0/0/0 on a board whose SAVED FILE has no fill.

    `p_fill` prints "filled N zones" — a claim about an IN-MEMORY object it
    just mutated, and the last honest moment before the bytes hit disk. This
    function is the read-back: it reopens the file AS TEXT and counts what is
    actually there. Text, not pcbnew, deliberately — pcbnew is the tool whose
    save behaviour is under test, so re-reading through it would share a method
    with the thing being checked (canon M1).

    Canon M-WIDTH is why this exists at all rather than a zone-specific patch:
    this project already knew "pcbnew saves clobber NETCLASSES" and wrote the
    rule at the width of THAT incident. The law is that a save drops state not
    present in the source, and zone fill is the same class with no rule. Any
    further member found belongs in this same read-back, not in a new one.

    KEEPOUT/RULE-AREA ZONES ARE EXCLUDED: they carry no fill by design, and
    counting them would make a pour-free board look healthy.
    """
    import re as _re
    txt = Path(path).read_text(encoding="utf-8-sig")
    pours = fills = 0
    for m in _re.finditer(r"\(zone[\s(]", txt):
        i = m.start()
        depth, j, in_str = 0, i, False
        while j < len(txt):
            ch = txt[j]
            if ch == '"' and txt[j - 1] != "\\":
                in_str = not in_str
            elif not in_str:
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        break
            j += 1
        blk = txt[i:j + 1]
        if "(keepout" in blk:
            continue
        pours += 1
        fills += len(_re.findall(r"\(filled_polygon\b", blk))
    print(f"  read-back: {pours} pour zone(s) in the SAVED file, "
          f"{fills} filled_polygon block(s)")
    if pours and not fills:
        print("FAIL M-SHIP: the saved board has POUR ZONES BUT NO FILL. "
              "Every downstream gate will still pass — `kicad-cli pcb drc "
              "--refill-zones` refills in memory and reports 0/0/0 — and the "
              "GERBERS WILL SHIP BARE COPPER. This is usb-hub-3s-v3 "
              "v1.6/v1.7/v1.8, 44287.91 mm2 missing across three sealed "
              "releases. Re-run the `fill` pass and do not export.")
        return 1
    return 0


# =============================================================== MAIN ====
def main(argv=None):
    # LINE-BUFFER OUR OWN STDOUT, ONCE, HERE.
    # KRT is a subprocess writing straight to the inherited fd while this
    # driver's own prints sit in a block buffer, so on a long chain every
    # wave header lands AFTER all of the router output it was announcing.
    # MEASURED on programmable-usb2-hub 2026-08-02: 24 `=== wave` headers at
    # lines 10,087-10,156 of a 10,159-line log — wave 1's header arriving
    # 10,041 lines after wave 1's router output. The agent driving this
    # pipeline has no other real-time feedback channel, so an unreadable
    # progress log is a blind operator, not untidy output.
    # Done at the stream, not as `flush=True` on each call: there are 74
    # print() sites here, and a convention that must be remembered rots at
    # print 75.
    sys.stdout.reconfigure(line_buffering=True)
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("command",
                    choices=["prep", "route", "import", "taps", "quick",
                             "stitch", "verify-fill", "all"])
    ap.add_argument("config")
    ap.add_argument("--root", default=None,
                    help="project root (default: the config's grandparent dir)")
    ap.add_argument("--board", default=None,
                    help="quick: evaluate THIS board instead of project.board "
                         "(race candidates)")
    ap.add_argument("--target-board", default=None,
                    help="import/taps/stitch/all: mutate this transaction-local "
                         "board instead of project.board")
    ap.add_argument("--json", default=None,
                    help="quick: write the JSON summary here instead of "
                         "<build_dir>/quick.json")
    ap.add_argument("--race", type=int, default=None,
                    help="route: run N concurrent wave-chains and keep the "
                         "quick-measured best (overrides route.race)")
    ap.add_argument("--skip-preflight", action="store_true",
                    help="route: skip the tier-consistency preflight gate "
                         "(LOUD escape hatch — every mismatch it would have "
                         "caught surfaces as post-stitch DRC findings)")
    ap.add_argument("--resume", action="store_true",
                    help="route: continue an authenticated single-chain prefix; "
                         "refuses stale/unproven rN files and route races")
    ap.add_argument("--through-wave", default=None,
                    help="route: stop successfully after this named wave, "
                         "recording an authenticated resumable prefix but no "
                         "FINAL marker (single-chain only)")
    ap.add_argument("--route-source", choices=["auto", "build", "promoted"],
                    help="import: select route lineage explicitly (overrides "
                         "route.import_source)")
    a = ap.parse_args(argv)
    if a.target_board is not None and a.command not in {
            "import", "taps", "stitch", "verify-fill", "all"}:
        ap.error("--target-board applies only to import/taps/stitch/verify-fill/all")
    cfg = load_cfg(a.config, a.root)
    try:
        if a.command == "prep":
            return cmd_prep(cfg)
        if a.command == "route":
            return cmd_route(cfg, race=a.race,
                             skip_preflight=a.skip_preflight, resume=a.resume,
                             through_wave=a.through_wave)
        if a.command == "import":
            return cmd_import(
                cfg, a.route_source, target_board=a.target_board)
        if a.command == "taps":
            return cmd_taps(cfg, target_board=a.target_board)
        if a.command == "quick":
            return cmd_quick(cfg, board=a.board, json_out=a.json)
        if a.command == "stitch":
            return cmd_stitch(cfg, target_board=a.target_board)
        if a.command == "verify-fill":
            # THE READ-BACK, CALLABLE AFTER THE **LAST** BOARD WRITE.
            # `cmd_stitch` already runs it, but a per-board post-stitch script
            # runs AFTER the stitch driver and can undo the fill — which is
            # exactly what happened: usb-hub-3s-v3's post_stitch_fixes.py
            # section 6 (added in v1.6) unfilled to place vias and never
            # refilled before its save, and it holds the LAST save in the
            # chain. A guard that runs before the last writer guards nothing.
            return verify_saved_fill(_target_board(cfg, a.target_board))
        for fn in (cmd_prep, cmd_route):
            rc = fn(cfg)
            if rc:
                return rc
        rc = cmd_import(cfg, "build", target_board=a.target_board)
        if rc:
            return rc
        for fn in (cmd_taps, cmd_stitch):
            rc = fn(cfg, target_board=a.target_board)
            if rc:
                return rc
        return 0
    except RouteConfigError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
