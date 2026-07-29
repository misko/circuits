#!/usr/bin/env python3
"""tier_preflight — assert routing/stitch TOOL CONFIG == the DECLARED fab tier.

WHY (2026-07-23, crow-recorder-central-v2). ~60% of that board's routing
stage was spent fighting four defects that were all the SAME defect: a tool
default that silently disagreed with the board's declared fab tier / DRC
floors, each only surfacing as a wall of downstream findings:

  1. generate_rules' hardcoded 0.2mm clearance default vs the tier's ~0.10mm
     expectation -> the router (0.13) routed under the DRC clearance nobody
     had examined: 500 then 158 phantom clearance findings.
  2. via_site_ok() checked only F.Cu/B.Cu, blind to In2/In3 (the layers the
     board's signal routing actually used) -> 200 shorting_items + 501
     clearance findings appeared only after stitch.
  3. stitch.normalize_vias fell back to its own hardcoded 0.6/0.3 default and
     resized 323/323 correctly-sized 0.30mm tier vias, collision-unchecked.
  4. try_via's via tier carried {size,drill} only, so via_site_ok fell back
     to hole_to_copper=0.205 — 0.055mm STRICTER than the board's 0.15mm
     hole_clearance floor -> a FALSE placement wall: 7 of the 8 "unstitchable"
     GND pads had a DRC-legal via site 0.2-0.8mm away the whole time, and the
     miss was first (wrongly) diagnosed as a placement-density D-BACK.

Every 6-layer small-via board will hit these unless the config is CHECKED
against the tier before any KRT cycle is spent. This gate runs as the FIRST
step of route_and_stitch_generic's `route` command (refuse-to-route;
`--skip-preflight` is the loud escape hatch) and standalone:

    python3 tier_preflight.py <project_root> [--explain] [--route-config P]

For every routing/stitch/rescue parameter that has a DRC-floor twin it
computes the EFFECTIVE value (explicit config, or the code default it would
silently ride) and compares it against the declared tier + board DRC floors.
Each mismatch is ONE NAMED LINE with a copy-paste fix; where a default was
never set, the tier-correct value is COMPUTED and printed. `--explain`
prints the derivation for every check, passing ones included.

FAIL (exit 1, blocks route) vs WARN (printed, does not block): a check is a
FAIL when the mismatch has a measured defect class behind it or the config
is explicitly sub-floor; it is a WARN when the risk is real but the full DRC
gate catches it loudly anyway (an under-strict default), or when the twin is
a placement-quality heuristic (legalize), so that proven shipped boards
(cook-loadcell, crow-array-pod) are not retro-blocked.

No pcbnew dependency — `route` runs on the KRT venv, so this reads the
board file as TEXT (the layer table) and the .kicad_pro as JSON.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import yaml  # noqa: E402

from fab_tier_util import FabTierError, resolve as resolve_tier  # noqa: E402

# ------------------------------------------------------------------ defaults
# The CODE DEFAULTS this gate models. Each entry names the source so a drifted
# default is a one-line fix here; t2_tier_preflight pins the load-bearing ones.
D = {
    "rules_clearance": 0.2,      # generate_rules_generic: clr = mm(...) or 0.2
    "via_site_htc": 0.205,       # pcb_toolkit.via_site_ok hole_to_copper=
    "stitch_clearance": 0.15,    # route_and_stitch Ctx: stitch.clearance
    "taps_clearance": 0.15,      # cmd_taps
    "seed_clearance": 0.13,      # p_seed_stubs
    "norm_size": 0.6,            # p_normalize_vias c.get("size", 0.6)
    "norm_drill": 0.3,
    "norm_below": 0.449,         # p_normalize_vias c.get("below_width", 0.449)
    "via_spacing": 0.62,         # Ctx.try_via v.get("spacing", 0.62)
    "h2h_min_gap": 0.5,          # p_hole_to_hole c.get("min_gap", 0.5)
    "island_layers": ["F.Cu", "B.Cu", "In2.Cu"],   # p_island c.get("layers")
    "legalize_clearance": 0.25,  # generate_board_generic legalize default
    "hole_clearance": 0.25,      # generate_board design_rules default
    "htc_slack": 0.05,           # allowed over-strictness before a check is a
                                 # false wall (crow delta was 0.055 -> trips)
}


def _mm(v):
    if v is None:
        return None
    return float(str(v).strip().lower().replace("mm", "").strip())


class Finding:
    def __init__(self, check, level, param, msg, fix=None):
        self.check, self.level, self.param = check, level, param
        self.msg, self.fix = msg, fix

    def render(self):
        out = f"  {self.check:<15} {self.level} {self.param}: {self.msg}"
        if self.fix:
            out += f"\n  {'':<15}      fix: {self.fix}"
        return out


class Preflight:
    def __init__(self, root, route_cfg=None, route_path=None, toolkit=None,
                 explain=False):
        self.root = Path(root).resolve()
        self.explain = explain
        self.findings = []
        self.notes = []            # --explain derivation lines
        self.toolkit = Path(toolkit) if toolkit else \
            Path(__file__).resolve().parent / "pcb_toolkit.py"
        self.route_path = Path(route_path) if route_path else \
            self.root / "03_src" / "route.yaml"
        if route_cfg is not None:
            self.cfg = route_cfg
        elif self.route_path.is_file():
            self.cfg = yaml.safe_load(self.route_path.read_text(encoding="utf-8-sig")) or {}
        else:
            self.cfg = None
        self.tier = resolve_tier(self.root)   # FabTierError propagates: HARD
        nets_p = self.root / "03_src" / "rules" / "nets.yaml"
        self.nets = (yaml.safe_load(nets_p.read_text(encoding="utf-8-sig")) or {}) \
            if nets_p.is_file() else {}

    # ------------------------------------------------------------- helpers
    def get(self, dotted, default=None):
        node = self.cfg
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def fail(self, check, param, msg, fix=None):
        self.findings.append(Finding(check, "FAIL", param, msg, fix))

    def warn(self, check, param, msg, fix=None):
        self.findings.append(Finding(check, "WARN", param, msg, fix))

    def note(self, s):
        self.notes.append(f"    . {s}")

    # ---------------------------------------------------------- board facts
    def board_path(self):
        b = self.get("project.board")
        if not b:
            return None
        p = Path(b)
        return p if p.is_absolute() else self.root / p

    def hole_floor(self):
        """The board's hole-to-copper DRC floor, best source first:
        .kicad_pro design rules (what DRC actually enforces) -> floorplan
        design_rules.hole_clearance (what the generator will write) ->
        the generator default."""
        bp = self.board_path()
        if bp:
            pro = bp.with_suffix(".kicad_pro")
            if pro.is_file():
                try:
                    r = json.loads(pro.read_text(encoding="utf-8-sig"))["board"][
                        "design_settings"]["rules"]
                    v = r.get("min_hole_clearance")
                    if v is not None:
                        self.note(f"hole floor {v} from {pro.name} "
                                  f"min_hole_clearance")
                        return float(v), pro.name
                except Exception:
                    pass
        fp = self.floorplan()
        if fp:
            v = ((fp.get("design_rules") or {}).get("hole_clearance"))
            if v is not None:
                self.note(f"hole floor {v} from floorplan design_rules")
                return _mm(v), "floorplan.yaml design_rules.hole_clearance"
        self.note(f"hole floor: generator default {D['hole_clearance']}")
        return D["hole_clearance"], "generator default"

    def floorplan(self):
        if hasattr(self, "_fp"):
            return self._fp
        self._fp = None
        cands = sorted((self.root / "03_src").glob("**/floorplan.yaml")) \
            if (self.root / "03_src").is_dir() else []
        bp = self.board_path()
        for c in cands:
            try:
                d = yaml.safe_load(c.read_text(encoding="utf-8-sig")) or {}
            except Exception:
                continue
            out = (d.get("project") or {}).get("output")
            if bp and out and (self.root / out).resolve() == bp.resolve():
                self._fp = d
                return d
            if self._fp is None:
                self._fp = d
        return self._fp

    def copper_layers(self):
        """The board's copper layer NAMES, parsed from the .kicad_pcb layer
        table as text (no pcbnew — route runs on the KRT venv). Falls back
        to the floorplan's declared layer count."""
        bp = self.board_path()
        if bp and bp.is_file():
            txt = bp.read_text(errors="replace")
            i = txt.find("(layers")
            if i >= 0:
                depth, j = 0, i
                while j < len(txt):
                    if txt[j] == "(":
                        depth += 1
                    elif txt[j] == ")":
                        depth -= 1
                        if depth == 0:
                            break
                    j += 1
                names = re.findall(r'"([A-Za-z0-9_.]+\.Cu)"', txt[i:j + 1])
                if names:
                    self.note(f"copper stack from {bp.name}: {names}")
                    return names
        fp = self.floorplan() or {}
        n = int(((fp.get("board") or {}).get("layers")) or 2)
        names = ["F.Cu"] + [f"In{i}.Cu" for i in range(1, n - 1)] + ["B.Cu"]
        self.note(f"copper stack from floorplan layer count {n}: {names}")
        return names

    # -------------------------------------------------------------- checks
    def drc_clearances(self):
        """{who: (effective_mm, explicit?)} for the Default class + every
        nets.yaml class — the clearances generate_rules will actually emit."""
        out = {}
        dc = self.nets.get("default_clearance")
        out["Default"] = (_mm(dc) if dc is not None else D["rules_clearance"],
                          dc is not None)
        for name, c in (self.nets.get("classes") or {}).items():
            c = c or {}
            cc = c.get("clearance")
            out[name] = (_mm(cc) if cc is not None else D["rules_clearance"],
                         cc is not None)
        return out

    def eff_route_clearance(self):
        c = self.get("route.common.clearance")
        if c is not None:
            return float(c), "route.common.clearance (explicit)"
        if self.tier is not None:
            return (float(self.tier["min_space"]),
                    f"tier-derived min_space (tier {self.tier['name']})")
        return None, "unset, no tier"

    def check_clearances(self):
        drc = self.drc_clearances()
        drc_max = max(v for v, _ in drc.values())
        drc_who = [k for k, (v, _) in drc.items() if v == drc_max]
        rclr, rsrc = self.eff_route_clearance()
        self.note(f"DRC clearances: " + ", ".join(
            f"{k}={v}{'' if ex else ' (HARDCODE default)'}"
            for k, (v, ex) in drc.items()))
        self.note(f"route clearance: {rclr} [{rsrc}]; DRC max {drc_max} "
                  f"({','.join(drc_who)})")

        # PF-RULES-CLR — defect class 1: a netclass riding generate_rules'
        # hardcoded 0.2 while the router routes tighter. The unexamined
        # hardcode IS the defect (crow-rv2: 500 -> 158 phantom findings).
        if rclr is not None:
            hard = [k for k, (v, ex) in drc.items()
                    if not ex and v > rclr + 1e-9]
            if hard:
                sug = rclr if (self.tier is None
                               or rclr >= float(self.tier["min_space"])) \
                    else round(float(self.tier["min_space"]) + 0.01, 3)
                self.fail(
                    "PF-RULES-CLR", "nets.yaml clearance",
                    f"{hard} ride generate_rules' HARDCODED "
                    f"{D['rules_clearance']}mm clearance default (no explicit "
                    f"clearance), above the route clearance {rclr} — the "
                    f"router will route under the DRC floor nobody declared "
                    f"(crow-rv2 2026-07-23: 500 phantom clearance findings)",
                    fix=f"nets.yaml: default_clearance: {sug}mm and/or "
                        f"per-class clearance: {sug}mm (tier "
                        f"min_space {self.tier['min_space'] if self.tier else '?'})")
                return  # PF-ROUTE-CLR would duplicate the same mismatch

        # PF-ROUTE-CLR — router clearance vs the (explicit) DRC clearances.
        if rclr is not None and rclr < drc_max - 1e-9:
            self.fail(
                "PF-ROUTE-CLR", "route.common.clearance",
                f"effective {rclr} [{rsrc}] < DRC clearance {drc_max} "
                f"({','.join(drc_who)}) — KRT packs to its clearance under "
                f"congestion, so routed copper lands below the DRC floor",
                fix=f"route.common.clearance: {drc_max}  (or lower the "
                    f"netclass clearance, floor: tier min_space "
                    f"{self.tier['min_space'] if self.tier else '?'})")
        if self.tier is not None and rclr is not None \
                and rclr < float(self.tier["min_space"]) - 1e-9:
            self.fail("PF-ROUTE-CLR", "route.common.clearance",
                      f"{rclr} is below fab tier '{self.tier['name']}' "
                      f"min_space {self.tier['min_space']}",
                      fix=f"route.common.clearance: {self.tier['min_space']}")

        # PF-STITCH-CLR — the clearance stitch/taps/seed verify their copper
        # at. Under-strict = the emitted copper can fail DRC clearance; WARN
        # (the DRC gate catches it loudly; proven boards ride the default).
        for param, val, dflt, present in (
                ("stitch.clearance", self.get("stitch.clearance"),
                 D["stitch_clearance"], self.get("stitch") is not None),
                ("taps.clearance", self.get("taps.clearance"),
                 D["taps_clearance"],
                 bool(self.get("taps.connections"))),
                ("stitch.seed_stubs.clearance",
                 self.get("stitch.seed_stubs.clearance"),
                 D["seed_clearance"],
                 bool(self.get("stitch.seed_stubs.stubs")))):
            if not present:
                continue
            eff = float(val) if val is not None else dflt
            src = "explicit" if val is not None else f"default {dflt}"
            self.note(f"{param}: {eff} [{src}]")
            if eff < drc_max - 1e-9:
                self.warn(
                    "PF-STITCH-CLR", param,
                    f"effective {eff} [{src}] < DRC clearance {drc_max} — "
                    f"rescue/tap copper is verified looser than the DRC "
                    f"gate will judge it",
                    fix=f"{param.rsplit('.', 1)[0]}: clearance: {drc_max}")

    def check_via_geometry(self):
        """PF-VIA-FLOOR: every explicit via size/drill vs the tier floors.
        Missing values that ARE tier-derived by the generators pass."""
        t = self.tier
        vd, vr = float(t["min_via_diameter"]), float(t["min_via_drill"])
        spots = [
            ("route.common.via_size", self.get("route.common.via_size"), vd),
            ("route.common.via_drill", self.get("route.common.via_drill"), vr),
            ("stitch.via.size", self.get("stitch.via.size"), vd),
            ("stitch.via.drill", self.get("stitch.via.drill"), vr),
            ("taps.via.size", self.get("taps.via.size"), vd),
            ("taps.via.drill", self.get("taps.via.drill"), vr),
            ("stitch.seed_stubs.via.size",
             self.get("stitch.seed_stubs.via.size"), vd),
            ("stitch.seed_stubs.via.drill",
             self.get("stitch.seed_stubs.via.drill"), vr),
            ("stitch.astar_fallback.via.size",
             self.get("stitch.astar_fallback.via.size"), vd),
            ("stitch.astar_fallback.via.drill",
             self.get("stitch.astar_fallback.via.drill"), vr),
            ("stitch.hole_to_hole.shrink_to.size",
             self.get("stitch.hole_to_hole.shrink_to.size"), vd),
            ("stitch.hole_to_hole.shrink_to.drill",
             self.get("stitch.hole_to_hole.shrink_to.drill"), vr),
        ]
        for i, wv in enumerate(self.get("route.waves", []) or []):
            name = wv.get("name", f"w{i + 1}")
            spots += [(f"route.waves[{name}].via_size",
                       wv.get("via_size"), vd),
                      (f"route.waves[{name}].via_drill",
                       wv.get("via_drill"), vr)]
        for i, te in enumerate(self.get("stitch.via.tiers") or []):
            spots += [(f"stitch.via.tiers[{i}].size", te.get("size"), vd),
                      (f"stitch.via.tiers[{i}].drill", te.get("drill"), vr)]
        for param, val, floor in spots:
            if val is None:
                continue
            if float(val) < floor - 1e-9:
                self.fail("PF-VIA-FLOOR", param,
                          f"{val} is below fab tier '{t['name']}' floor "
                          f"{floor} — no process at that tier drills it",
                          fix=f"{param}: {floor}")
            elif self.explain:
                self.note(f"{param}: {val} >= tier floor {floor}")

    def check_normalize_vias(self):
        """PF-NORM — defect class 3: normalize_vias resizes copper with NO
        collision check; riding its own 0.6/0.3 default on a small-via tier
        blew 323/323 correct 0.30mm vias up to 0.6mm (crow-rv2)."""
        passes = self.get("stitch.passes") or []
        if "normalize_vias" not in passes:
            return
        t = self.tier
        c = self.get("stitch.normalize_vias") or {}
        size = float(c.get("size", D["norm_size"]))
        below = float(c.get("below_width", D["norm_below"]))
        vd, vr = float(t["min_via_diameter"]), float(t["min_via_drill"])
        self.note(f"normalize_vias effective: size={size} "
                  f"below_width={below} (tier via floor {vd}/{vr})")
        if below > vd + 1e-9:
            unset = "size" not in c or "below_width" not in c
            self.fail(
                "PF-NORM", "stitch.normalize_vias",
                f"below_width {below}"
                f"{' (pass default — block not tier-derived)' if unset else ''}"
                f" > tier via floor {vd}: the pass would resize EVERY "
                f"correctly-sized {vd}mm tier via to {size}mm, "
                f"collision-unchecked (crow-rv2 2026-07-23: 323/323 vias "
                f"inflated, then 902 DRC findings)",
                fix=f"stitch.normalize_vias: {{size: {vd}, drill: {vr}, "
                    f"below_width: {round(vd - 0.01, 3)}}}")

    def check_hole_to_copper(self):
        """PF-HTC — defect class 4: the effective hole_to_copper every via
        placement is screened at, vs the board's real hole_clearance floor.
        Over-strict (> floor + slack) is a FAIL: it silently manufactures a
        FALSE placement wall (crow-rv2: 0.205 vs 0.15 floor, 7 of 8 'stuck'
        pads had legal sites). Under via the DEFAULT is a WARN (the DRC gate
        catches it loudly); an EXPLICIT sub-floor value is a FAIL."""
        H, hsrc = self.hole_floor()
        want = round(H + 0.005, 3)
        stitch = self.get("stitch")
        if isinstance(stitch, dict):
            tiers = self.get("stitch.via.tiers")
            entries = list(enumerate(tiers)) if tiers else [(None, {})]
            for i, te in entries:
                param = (f"stitch.via.tiers[{i}].hole_to_copper" if i is not None
                         else "stitch.via.tiers (unset)")
                htc = te.get("hole_to_copper")
                eff = float(htc) if htc is not None else D["via_site_htc"]
                src = "explicit" if htc is not None else \
                    f"via_site_ok default {D['via_site_htc']}"
                self.note(f"{param}: effective {eff} [{src}] vs hole floor "
                          f"{H} [{hsrc}]")
                if eff > H + D["htc_slack"] + 1e-9:
                    self.fail(
                        "PF-HTC", param,
                        f"effective {eff} [{src}] is {round(eff - H, 3)}mm "
                        f"STRICTER than the board hole_clearance floor {H} "
                        f"[{hsrc}] — a FALSE placement wall: try_via refuses "
                        f"DRC-legal sites (crow-rv2 2026-07-23: 7 of 8 "
                        f"'unstitchable' GND pads had legal sites 0.2-0.8mm "
                        f"away; misdiagnosed as a placement D-BACK)",
                        fix=f"stitch.via.tiers: [{{size: "
                            f"{te.get('size', self.tier['min_via_diameter'])}, "
                            f"drill: "
                            f"{te.get('drill', self.tier['min_via_drill'])}, "
                            f"hole_to_copper: {want}}}]  # floor {H} + 5um")
                elif htc is not None and eff < H - 1e-9:
                    self.fail("PF-HTC", param,
                              f"explicit {eff} < board hole_clearance floor "
                              f"{H} [{hsrc}] — stitch will place vias the "
                              f"DRC hole_clearance check rejects",
                              fix=f"hole_to_copper: {want}")
                elif htc is None and eff < H - 1e-9:
                    self.warn("PF-HTC", param,
                              f"default {eff} < board hole_clearance floor "
                              f"{H} [{hsrc}] — placements pass the stitch "
                              f"screen but can fail DRC hole_clearance",
                              fix=f"stitch.via.tiers: [{{..., "
                                  f"hole_to_copper: {want}}}]")
        # Paths with NO config knob (via_site_ok default assumes a 0.20
        # floor): flag as a generator gap when this board's floor differs.
        if abs(D["via_site_htc"] - (H + 0.005)) > D["htc_slack"]:
            users = [p for p, on in (
                ("taps", bool(self.get("taps.connections"))),
                ("stitch.seed_stubs", bool(self.get("stitch.seed_stubs.stubs"))),
                ("stitch.astar_fallback",
                 "astar_fallback" in (self.get("stitch.passes") or []))) if on]
            if users:
                self.warn(
                    "PF-HTC", "+".join(users),
                    f"these paths call via_site_ok with NO hole_to_copper "
                    f"knob (hardcoded default {D['via_site_htc']}, assumes a "
                    f"0.20 floor) but this board's floor is {H} — generator "
                    f"gap, no config fix exists; expect false "
                    f"refusals/DRC findings at the margin")

    def check_hole_to_hole(self):
        """PF-H2H: drill-edge spacing config vs the tier hole-to-hole floor."""
        t = self.tier
        h2h = float(t.get("min_hole_to_hole", 0))
        stitch = self.get("stitch")
        if isinstance(stitch, dict):
            spacing = float(self.get("stitch.via.spacing",
                                     D["via_spacing"]))
            drills = [float(te.get("drill", t["min_via_drill"]))
                      for te in (self.get("stitch.via.tiers") or [])] or \
                     [float(self.get("stitch.via.drill",
                                     t["min_via_drill"]))]
            gap = round(spacing - max(drills), 3)
            self.note(f"stitch.via.spacing {spacing} c-c, max drill "
                      f"{max(drills)} -> edge gap {gap} vs tier "
                      f"hole-to-hole {h2h}")
            if gap < h2h - 1e-9:
                need = round(h2h + max(drills) + 0.01, 2)
                self.fail("PF-H2H", "stitch.via.spacing",
                          f"{spacing} c-c with {max(drills)} drills = "
                          f"{gap}mm drill-edge gap < tier '{t['name']}' "
                          f"hole-to-hole floor {h2h}",
                          fix=f"stitch.via.spacing: {need}")
        if "hole_to_hole" in (self.get("stitch.passes") or []):
            mg = float(self.get("stitch.hole_to_hole.min_gap",
                                D["h2h_min_gap"]))
            self.note(f"hole_to_hole repair min_gap {mg} vs tier {h2h}")
            if mg < h2h - 1e-9:
                self.fail("PF-H2H", "stitch.hole_to_hole.min_gap",
                          f"{mg} < tier '{t['name']}' hole-to-hole floor "
                          f"{h2h} — the repair pass would bless gaps the "
                          f"fab rejects",
                          fix=f"stitch.hole_to_hole: {{min_gap: {h2h}}}")

    def check_layers(self):
        """PF-LAYER — defect class 2 (config side): every copper layer the
        config names must exist on the board, and the island-rescue layer
        list must COVER every declared plane layer (a rescue blind to a
        plane layer strands that plane's pads exactly like the F/B-only
        via_site_ok did)."""
        stack = set(self.copper_layers())
        named = []
        for p in ("route.common.layers",):
            for n in self.get(p, []) or []:
                named.append((p, n))
        for i, wv in enumerate(self.get("route.waves", []) or []):
            for n in wv.get("layers") or []:
                named.append((f"route.waves[{wv.get('name', i)}].layers", n))
        for p in ("stitch.island_rescue.layers", "stitch.heal_islands.layers"):
            for n in self.get(p) or []:
                named.append((p, n))
        pr_layers = []
        for e in self.get("stitch.pad_rescue.nets") or []:
            if isinstance(e, dict):
                lay = e.get("layer") or e.get("plane_layer")
                if lay:
                    pr_layers.append(lay)
                    named.append(("stitch.pad_rescue.nets[].layer", lay))
        pl = self.get("stitch.pad_rescue.plane_layer")
        if pl:
            pr_layers.append(pl)
            named.append(("stitch.pad_rescue.plane_layer", pl))
        ps = self.get("stitch.power_stitch.plane_layer")
        if ps:
            named.append(("stitch.power_stitch.plane_layer", ps))
        for t in self.get("taps.connections") or []:
            for k in ("layer", "hop_layer"):
                if t.get(k):
                    named.append((f"taps.connections[].{k}", t[k]))
        bad = sorted({(p, n) for p, n in named
                      if n.endswith(".Cu") and n not in stack})
        for p, n in bad:
            self.fail("PF-LAYER", p,
                      f"names copper layer {n!r} which this board does not "
                      f"have (copper stack: {sorted(stack)}) — the config "
                      f"was written for a different layer count",
                      fix=f"restrict {p} to layers in {sorted(stack)}")
        # coverage: island_rescue must see every declared plane layer
        if "island_rescue" in (self.get("stitch.passes") or []) and pr_layers:
            eff = self.get("stitch.island_rescue.layers") \
                or D["island_layers"]
            missing = sorted({l for l in pr_layers
                              if l in stack and l not in eff})
            self.note(f"island_rescue layers {eff}; declared plane layers "
                      f"{sorted(set(pr_layers))}")
            if missing:
                want = sorted(set(eff) | set(missing))
                self.fail(
                    "PF-LAYER", "stitch.island_rescue.layers",
                    f"effective {eff}"
                    f"{' (pass default)' if not self.get('stitch.island_rescue.layers') else ''}"
                    f" does not cover declared plane layer(s) {missing} — "
                    f"islands on an unscanned plane are invisible, the "
                    f"F/B-only blindness that cost crow-rv2 200 shorting + "
                    f"501 clearance findings (2026-07-23, via_site_ok twin)",
                    fix=f"stitch.island_rescue: {{layers: {want}}}")

    def check_via_site_source(self):
        """PF-VIASITE — defect class 2 (code side): via_site_ok's layer
        default must resolve the board's FULL copper stack. Pinned by
        reading the toolkit SOURCE (a different method than executing it,
        canon M1): a regression back to a hardcoded (F_Cu, B_Cu) pair is
        blind to inner copper — 200 shorting_items + 501 clearance findings
        on crow-rv2 (2026-07-23), fixed in 60f0a13."""
        if not self.toolkit.is_file():
            self.warn("PF-VIASITE", str(self.toolkit),
                      "pcb_toolkit.py not found — cannot verify via-site "
                      "layer coverage")
            return
        txt = self.toolkit.read_text(errors="replace")
        m = re.search(r"def via_site_ok\(.*?(?=\n    def |\nclass |\Z)",
                      txt, re.S)
        body = m.group(0) if m else ""
        if "CuStack" not in body:
            self.fail(
                "PF-VIASITE", "pcb_toolkit.via_site_ok",
                "layer default does not resolve the board's full copper "
                "stack (no GetEnabledLayers().CuStack() in the function) — "
                "through-vias would be collision-checked on F/B only, blind "
                "to In*.Cu (crow-rv2 2026-07-23: 200 shorting + 501 "
                "clearance findings post-stitch)",
                fix="restore the CuStack() default from commit 60f0a13")
        elif self.explain:
            self.note("via_site_ok defaults to the full CuStack (60f0a13)")

    def check_legalize(self):
        """PF-LEGALIZE (WARN — placement-quality heuristic, not a DRC
        identity): the legalizer gap must at least host one tier via
        pocket (drill + 2 * hole_clearance) or rescue vias have nowhere to
        land between clusters. crow-rv2 measured this: legalize 0.25 packed
        the buck clusters so tight that exhaustive scans found ZERO legal
        0.30mm sites; 0.35 measurably reduced (not eliminated) the class.
        WARN, not FAIL: crow-rv2 shipped 0/0/0 at 0.35 < the 0.45 bound."""
        fp = self.floorplan() or {}
        lg = ((fp.get("placement") or {}).get("legalize")) or {}
        eff = float(lg.get("clearance", D["legalize_clearance"]))
        H, _ = self.hole_floor()
        pocket = round(float(self.tier["min_via_drill"]) + 2 * H, 3)
        self.note(f"legalize.clearance {eff} vs via pocket bound {pocket} "
                  f"(drill {self.tier['min_via_drill']} + 2*hole_clr {H})")
        if eff < pocket - 1e-9:
            self.warn(
                "PF-LEGALIZE", "floorplan placement.legalize.clearance",
                f"{eff} < {pocket} (tier via drill "
                f"{self.tier['min_via_drill']} + 2*hole_clearance {H}) — "
                f"part gaps may be too tight for any legal rescue via "
                f"(crow-rv2 2026-07-23: 0.25 left pour fragments with zero "
                f"legal 0.30mm sites; 0.35 measurably helped)",
                fix=f"placement.legalize.clearance: {pocket}")

    def check_krt_preset(self):
        """PF-KRT (WARN): KRT's own {standard,advanced} preset is NOT this
        pipeline's fab tier. On a tier whose via floor sits between the
        presets, 'advanced' auto-escalates vias DOWN below the declared
        floor unless pinned (crow-rv2 2026-07-23: 33 vias at 0.25 < the
        0.30 floor until --fab-overrides pinned it)."""
        preset = self.get("route.common.fab_tier")
        if preset != "advanced":
            return
        vd = float(self.tier["min_via_diameter"])
        if vd > 0.25 + 1e-9 and not self.get("route.common.fab_overrides"):
            self.warn(
                "PF-KRT", "route.common.fab_tier",
                f"KRT preset 'advanced' (its internal 0.25 via floor) with "
                f"no fab_overrides pin, but the declared tier floor is "
                f"{vd} — KRT may auto-escalate vias DOWN below the tier "
                f"(crow-rv2: 33 vias at 0.25mm, drill_out_of_range class)",
                fix="route.common.fab_overrides: <abs path to a KRT "
                    "overrides file pinning via "
                    f"{vd}/{self.tier['min_via_drill']}>")

    # ----------------------------------------------------------------- run
    def run(self):
        head = f"tier preflight: {self.root.name}"
        if self.tier is None:
            print(f"{head} — no fab_tier declared in 03_src/rules/nets.yaml; "
                  f"nothing to check (legacy board). Declare one to arm "
                  f"this gate.")
            return 0
        t = self.tier
        print(f"{head}  tier={t['name']} (via {t['min_via_diameter']}/"
              f"{t['min_via_drill']}, space {t['min_space']}, "
              f"h2h {t.get('min_hole_to_hole')})")
        if self.cfg is None:
            print(f"  no route config at {self.route_path} — only "
                  f"rules/toolkit checks run")
            self.cfg = {}
        self.check_clearances()
        self.check_via_geometry()
        self.check_normalize_vias()
        self.check_hole_to_copper()
        self.check_hole_to_hole()
        self.check_layers()
        self.check_via_site_source()
        self.check_legalize()
        self.check_krt_preset()
        if self.explain:
            print("  derivations:")
            for n in self.notes:
                print(n)
        fails = [f for f in self.findings if f.level == "FAIL"]
        warns = [f for f in self.findings if f.level == "WARN"]
        for f in self.findings:
            print(f.render())
        print(f"tier preflight: {len(fails)} FAIL / {len(warns)} WARN"
              + ("" if fails else " — config is tier-consistent"))
        return 1 if fails else 0


def preflight_route_cfg(cfg, explain=False):
    """Entry point for route_and_stitch_generic cmd_route: takes its loaded
    cfg dict (with _root/_path). Returns the exit code (0 clean, 1 FAILs).
    A FabTierError (typo'd tier) propagates — that is already a hard error
    everywhere else in the pipeline."""
    pf = Preflight(cfg["_root"], route_cfg=cfg, route_path=cfg.get("_path"),
                   explain=explain)
    return pf.run()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("project_root", help="dir containing 03_src/ + 04_kicad/")
    ap.add_argument("--route-config", default=None,
                    help="route.yaml path (default 03_src/route.yaml)")
    ap.add_argument("--toolkit", default=None,
                    help="pcb_toolkit.py to source-check (tests)")
    ap.add_argument("--explain", action="store_true",
                    help="print the derivation behind every check")
    a = ap.parse_args(argv)
    try:
        pf = Preflight(a.project_root, route_path=a.route_config,
                       toolkit=a.toolkit, explain=a.explain)
    except FabTierError as e:
        print(f"tier preflight: FAIL — {e}")
        return 1
    return pf.run()


if __name__ == "__main__":
    sys.exit(main())
