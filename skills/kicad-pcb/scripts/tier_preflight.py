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


def board_scoped(root, rel, board=None):
    """Resolve a per-board input under BOTH project layouts -> (Path|None, why).

    Single-board: `03_src/<rel>`. ADR-0007 multi-board: `03_src/<board>/<rel>`.

    THIS GATE MUST SELECT — it grades ONE board's route config — so unlike
    `waiver_provenance.waiver_files()` it cannot simply enumerate. What it can
    do is REFUSE rather than guess, which is `release_index.py`'s rule for the
    same situation ("'the latest' with no board named on a two-board project
    REFUSES"). Three properties, each paid for:

      * A FLAT PATH THAT IS A SYMLINK INTO ONE BOARD'S DIRECTORY IS NAMED AS
        SUCH. MEASURED on smc0985-cooksense 2026-07-30: `03_src/rules/` holds
        FIVE such symlinks — assembly.yaml, electrical_invariants.yaml,
        nets.yaml, policy_waivers.yaml, power_tree.yaml — every one pointing at
        `../cooksense/rules/`. So every gate reading the flat address grades
        the cooksense board while believing it read a project-wide file, and
        `--board interposer` gets cooksense's netclasses. Silent before this.
      * TWO BOARDS AND NO `--board` IS A REFUSAL, not a first-match.
      * NOTHING FOUND returns None with a reason, so the caller can report
        GRADED NOTHING instead of grading invented defaults (which is what
        this gate did: with no route.yaml it fell back to `self.cfg = {}` and
        emitted PF-ROUTE-CLR FAIL about a file that does not exist).
    """
    src = Path(root) / "03_src"
    per = {}
    for p in sorted(src.glob(f"*/{rel}")):
        if p.is_file():
            per.setdefault(p.relative_to(src).parts[0], p)
    flat = src / rel
    owner = None
    if flat.is_file():
        owner = next((b for b, q in per.items()
                      if q.resolve() == flat.resolve()), None)
    if board:
        if board in per:
            return per[board], f"03_src/{board}/{rel}"
        if flat.is_file() and owner in (None, board):
            return flat, f"03_src/{rel} (single-board layout)"
        if flat.is_file():
            return None, (f"--board {board} was named, but 03_src/{rel} "
                          f"resolves into {owner}'s directory — a board "
                          f"selector wearing a project-wide address. "
                          f"{board} declares no {rel} of its own "
                          f"(boards with one: {', '.join(sorted(per)) or 'none'})")
        return None, (f"no {rel} for board {board!r} (boards declaring one: "
                      f"{', '.join(sorted(per)) or 'none'})")
    if flat.is_file():
        if owner:
            return flat, (f"03_src/{rel} — A SYMLINK INTO {owner}'s directory, "
                          f"so this run grades {owner} however it is labelled; "
                          f"name a board with --board to be explicit")
        return flat, f"03_src/{rel} (single-board layout)"
    if len(per) == 1:
        b, p = next(iter(per.items()))
        return p, f"03_src/{b}/{rel} (the only board declaring one)"
    if len(per) > 1:
        return None, (f"{len(per)} boards declare {rel} "
                      f"({', '.join(sorted(per))}) and none was named — "
                      f"REFUSING to guess. Pass --board <name>")
    return None, f"ABSENT: no {rel} at 03_src/{rel} or 03_src/<board>/{rel}"


class Preflight:
    def __init__(self, root, route_cfg=None, route_path=None, toolkit=None,
                 explain=False, board=None):
        self.root = Path(root).resolve()
        self.explain = explain
        self.findings = []
        self.notes = []            # --explain derivation lines
        self.toolkit = Path(toolkit) if toolkit else \
            Path(__file__).resolve().parent / "pcb_toolkit.py"
        self.board = board or None
        if route_path:
            self.route_path, self.route_note = Path(route_path), "--route-config"
        else:
            self.route_path, self.route_note = board_scoped(
                self.root, "route.yaml", self.board)
        if route_cfg is not None:
            self.cfg = route_cfg
        elif self.route_path is not None and self.route_path.is_file():
            self.cfg = yaml.safe_load(
                self.route_path.read_text(encoding="utf-8-sig")) or {}
        else:
            self.cfg = None
        nets_p, self.nets_note = board_scoped(
            self.root, "rules/nets.yaml", self.board)
        self.nets_path = nets_p
        # The tier comes from the SAME resolved nets.yaml this run grades. It
        # used to come from the flat address independently, so on a multi-board
        # tree `resolve_tier` returned None, `run()` read that as "legacy board,
        # nothing to check" and the gate EXITED 0 having disarmed itself.
        self.tier = resolve_tier(self.root, nets_path=nets_p)  # FabTierError: HARD
        self.nets = (yaml.safe_load(nets_p.read_text(encoding="utf-8-sig")) or {}) \
            if nets_p is not None and nets_p.is_file() else {}

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

    def scoped_clearances(self):
        """nets.yaml `scoped_clearances[]` as [(zone, value, nets), ...] — the
        BOUNDED isolation relaxations generate_rules will emit into the
        .kicad_dru (canon R-SCOPE). Entries missing a zone or a value are
        skipped here and REFUSED by the emitter, which owns that validation:
        this gate must not be the only place a malformed entry is noticed."""
        out = []
        for sc in (self.nets.get("scoped_clearances") or []):
            sc = sc or {}
            v = _mm(sc.get("clearance"))
            if sc.get("zone") and v is not None:
                out.append((sc["zone"], v, list(sc.get("nets") or [])))
        return out

    def route_clearance_scopes(self):
        """EVERY place a router clearance can be set, as
        [(param, value|None, source), ...] — the common scope first, then one
        entry per wave that OVERRIDES it.

        WHY THIS IS A LIST AND NOT A NUMBER (2026-07-30, pluto-rx2-8way). The
        pre-fix `eff_route_clearance` read `route.common.clearance` ONLY, so a
        per-wave `clearance:` was INVISIBLE: that board declared 0.2mm at
        route.common, at both netclasses and at stitch — and overrode one wave
        to 0.14 to escape a PE42482A-X land. Preflight printed `0 FAIL —
        config is tier-consistent` while the wave routed 0.06mm under the DRC
        floor, and the route landed 49 clearance findings at 0.166..0.194mm.

        The values are NOT collapsed to one figure, because collapsing is how
        the defect survived: the strictest number alone would have flagged
        SOMETHING, but attributed it to `route.common.clearance` — a key whose
        value was correct — and the fix line would have told the author to
        change the one place that was already right. Each scope is graded and
        NAMED separately; only `check_clearances`' hardcode comparison
        (PF-RULES-CLR, which asks "will the router ever route tighter than an
        undeclared DRC default") takes the strictest, and says so there."""
        if hasattr(self, "_clr_scopes"):
            return self._clr_scopes
        base = self.get("route.common.clearance")
        if base is not None:
            scopes = [("route.common.clearance", float(base),
                       "explicit")]
        elif self.tier is not None:
            scopes = [("route.common.clearance", float(self.tier["min_space"]),
                       f"tier-derived min_space (tier {self.tier['name']})")]
        else:
            scopes = [("route.common.clearance", None, "unset, no tier")]
        inherit = []
        for i, wv in enumerate(self.get("route.waves", []) or []):
            wv = wv or {}
            name = wv.get("name", f"w{i + 1}")
            c = wv.get("clearance")
            if c is None:
                inherit.append(name)
                continue
            scopes.append((f"route.waves[{name}].clearance", float(c),
                           f"wave OVERRIDE of common {scopes[0][1]}"))
        for name in inherit:
            self.note(f"route.waves[{name}]: inherits "
                      f"{scopes[0][0]} = {scopes[0][1]}")
        self._clr_scopes = scopes
        return scopes

    def eff_route_clearance(self):
        """The STRICTEST scope — the clearance the router will pack to
        SOMEWHERE on this board. Used only where a single figure is the
        question (the PF-RULES-CLR hardcode comparison); everything else
        grades `route_clearance_scopes()` scope by scope."""
        scopes = [s for s in self.route_clearance_scopes() if s[1] is not None]
        if not scopes:
            return None, "unset, no tier"
        param, val, src = min(scopes, key=lambda s: s[1])
        return val, f"{param} ({src})"

    def check_clearances(self):
        drc = self.drc_clearances()
        drc_max = max(v for v, _ in drc.values())
        drc_who = [k for k, (v, _) in drc.items() if v == drc_max]
        scopes = self.route_clearance_scopes()
        rclr, rsrc = self.eff_route_clearance()
        self.note(f"DRC clearances: " + ", ".join(
            f"{k}={v}{'' if ex else ' (HARDCODE default)'}"
            for k, (v, ex) in drc.items()))
        self.note("route clearance scopes: " + ", ".join(
            f"{p}={v} [{s}]" for p, v, s in scopes))
        self.note(f"strictest route clearance: {rclr} [{rsrc}]; DRC max "
                  f"{drc_max} ({','.join(drc_who)})")

        # PF-RULES-CLR — defect class 1: a netclass riding generate_rules'
        # hardcoded 0.2 while the router routes tighter. The unexamined
        # hardcode IS the defect (crow-rv2: 500 -> 158 phantom findings).
        # This one question IS about a single number — "will the router route
        # tighter than a floor nobody declared, ANYWHERE" — so it takes the
        # strictest scope; the per-scope grading below then attributes it.
        if rclr is not None:
            hard = [k for k, (v, ex) in drc.items()
                    if not ex and v > rclr + 1e-9]
            if hard:
                sug = rclr if (self.tier is None
                               or rclr >= float(self.tier["min_space"])) \
                    else round(float(self.tier["min_space"]) + 0.01, 3)
                # THE FIX LINE MUST OFFER BOTH DIRECTIONS (2026-07-30). Where
                # the strictest scope is a WAVE override, "declare the DRC
                # floor at the router's number" means adopting a LOCAL
                # routability budget BOARD-WIDE — and on the board that made
                # this reachable (pluto-rx2-8way) clearance is ISOLATION
                # between nine RF arms, so that advice would trade the whole
                # electrical argument for a green gate. Its route.yaml already
                # records rejecting this line once. The other direction —
                # declare the isolation number EXPLICITLY (which is what this
                # check actually asks for: stop riding a hardcode) and bound
                # the relaxation with scoped_clearances — is the one that keeps
                # both facts true, so it is printed beside the first.
                alt = ""
                if rsrc.startswith("route.waves["):
                    alt = (f"; the strictest scope is a WAVE ({rsrc}), so if "
                           f"{sug}mm is a LOCAL routability budget rather than "
                           f"the board's isolation, declare the isolation "
                           f"number explicitly instead and bound the "
                           f"relaxation: nets.yaml scoped_clearances: "
                           f"[{{zone: <rule area>, nets: [...], clearance: "
                           f"{sug}, why: <measurement>}}]  (canon R-SCOPE)")
                self.fail(
                    "PF-RULES-CLR", "nets.yaml clearance",
                    f"{hard} ride generate_rules' HARDCODED "
                    f"{D['rules_clearance']}mm clearance default (no explicit "
                    f"clearance), above the route clearance {rclr} [{rsrc}] — "
                    f"the router will route under the DRC floor nobody "
                    f"declared (crow-rv2 2026-07-23: 500 phantom clearance "
                    f"findings)",
                    fix=f"nets.yaml: default_clearance: {sug}mm and/or "
                        f"per-class clearance: {sug}mm (tier "
                        f"min_space {self.tier['min_space'] if self.tier else '?'})"
                        + alt)
                return  # PF-ROUTE-CLR would duplicate the same mismatch

        # PF-ROUTE-CLR — router clearance vs the (explicit) DRC clearances,
        # graded ONCE PER SCOPE. A per-wave override is a first-class scope:
        # pluto-rx2-8way 2026-07-30 rode a 0.14 wave under a 0.2 DRC floor
        # through a gate that only ever read route.common (49 findings at
        # 0.166..0.194mm). The finding NAMES the scope, so the fix line points
        # at the key that is actually wrong.
        scoped = self.scoped_clearances()
        if scoped:
            self.note("nets.yaml scoped_clearances: " + ", ".join(
                f"{z}={v} {n or '(no nets — emitter refuses)'}"
                for z, v, n in scoped))
        for param, val, src in scopes:
            if val is None:
                continue
            if val < drc_max - 1e-9:
                # canon R-SCOPE: a BOUNDED nets.yaml scoped_clearances entry is
                # the declared, evidenced answer to this mismatch. It downgrades
                # to WARN and never to silence, because the relaxation is a
                # GEOMETRIC claim (the tight copper must actually lie inside the
                # named rule area) and this gate reads config, not copper — DRC
                # is what settles it.
                cover = [(z, v) for z, v, _ in scoped if v <= val + 1e-9]
                if cover:
                    self.warn(
                        "PF-ROUTE-CLR", param,
                        f"effective {val} [{src}] < DRC clearance {drc_max} "
                        f"({','.join(drc_who)}), but nets.yaml declares "
                        f"scoped_clearances "
                        f"{[f'{z}={v}' for z, v in cover]} at or below it "
                        f"(canon R-SCOPE). NOT VERIFIED HERE: whether the "
                        f"sub-{drc_max} copper actually lands inside those "
                        f"rule areas is a GEOMETRY question this gate cannot "
                        f"answer — DRC settles it",
                        fix="none if the relaxation is intended; confirm the "
                            "rule area encloses BOTH items of every tight "
                            "pair (KiCad insideArea is per-ITEM, not per "
                            "closest-approach point)")
                elif scoped:
                    hi = min(v for _, v, _ in scoped)
                    self.fail(
                        "PF-ROUTE-CLR", param,
                        f"effective {val} [{src}] < DRC clearance {drc_max} "
                        f"({','.join(drc_who)}), and the declared "
                        f"scoped_clearances relaxation ({hi}) sits ABOVE the "
                        f"router's own budget — it licenses nothing at the "
                        f"value KRT will pack to, so the R8 mismatch is "
                        f"re-created one level down inside the rule area",
                        fix=f"nets.yaml scoped_clearances[].clearance: {val} "
                            f"(match the router budget) — or raise {param} to "
                            f"{hi}")
                else:
                    self.fail(
                        "PF-ROUTE-CLR", param,
                        f"effective {val} [{src}] < DRC clearance {drc_max} "
                        f"({','.join(drc_who)}) — KRT packs to its clearance "
                        f"under congestion, so routed copper lands below the "
                        f"DRC floor (pluto-rx2-8way 2026-07-30: a 0.14 WAVE "
                        f"override under a 0.2 floor = 49 clearance findings)",
                        fix=f"{param}: {drc_max}  (or lower the netclass "
                            f"clearance, floor: tier min_space "
                            f"{self.tier['min_space'] if self.tier else '?'}; "
                            f"or, if the relaxation is LOCAL and evidenced, a "
                            f"nets.yaml scoped_clearances entry bounded to a "
                            f"rule area — canon R-SCOPE)")
            if self.tier is not None \
                    and val < float(self.tier["min_space"]) - 1e-9:
                self.fail("PF-ROUTE-CLR", param,
                          f"{val} is below fab tier '{self.tier['name']}' "
                          f"min_space {self.tier['min_space']} — no netclass "
                          f"or scoped relaxation makes that etchable",
                          fix=f"{param}: {self.tier['min_space']}")

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

    def check_via_aspect_ratio(self):
        """PF-VIA-ASPECT: plated through holes must be plateable at thickness.

        Diameter-only capability is insufficient.  A 0.15 mm mechanical drill
        is a published minimum, but through a 1.6 mm board it is 10.67:1 and
        exceeds JLC's published 10:1 plated-through-hole limit.  RX2 v4 reached
        final adversarial review with 3,446 such vias because every earlier
        gate compared the drill only to ``min_via_drill``.

        The check is armed only when the declarative floorplan carries a
        nominal physical stackup; legacy boards without that input remain
        explicitly ungraded rather than acquiring an invented thickness.
        """
        limit = self.tier.get("max_pth_aspect_ratio")
        fp = self.floorplan() or {}
        stack = (fp.get("board") or {}).get("stackup") or {}
        thick = stack.get("nominal_thickness_mm")
        if limit is None:
            self.note("via aspect ratio: tier carries no max_pth_aspect_ratio; ungraded")
            return
        if thick is None:
            self.note("via aspect ratio: floorplan has no nominal stackup thickness; ungraded")
            return

        thick = float(thick)
        limit = float(limit)
        drills = []
        for param, val in (
                ("route.common.via_drill", self.get("route.common.via_drill")),
                ("stitch.via.drill", self.get("stitch.via.drill")),
                ("taps.via.drill", self.get("taps.via.drill")),
                ("stitch.seed_stubs.via.drill",
                 self.get("stitch.seed_stubs.via.drill")),
                ("stitch.astar_fallback.via.drill",
                 self.get("stitch.astar_fallback.via.drill")),
                ("stitch.hole_to_hole.shrink_to.drill",
                 self.get("stitch.hole_to_hole.shrink_to.drill"))):
            if val is not None:
                drills.append((param, float(val)))
        for i, wv in enumerate(self.get("route.waves", []) or []):
            if wv.get("via_drill") is not None:
                drills.append((f"route.waves[{wv.get('name', f'w{i + 1}')}].via_drill",
                               float(wv["via_drill"])))
        for i, te in enumerate(self.get("stitch.via.tiers") or []):
            drills.append((f"stitch.via.tiers[{i}].drill",
                           float(te.get("drill", self.tier["min_via_drill"]))))
        if not drills:
            drills.append(("tier-derived min_via_drill",
                           float(self.tier["min_via_drill"])))

        seen = set()
        for param, drill in drills:
            key = (param, drill)
            if key in seen:
                continue
            seen.add(key)
            ratio = thick / drill
            self.note(f"{param}: {thick:g}/{drill:g} = {ratio:.3f}:1 "
                      f"vs tier limit {limit:g}:1")
            if ratio > limit + 1e-9:
                max_thick = drill * limit
                min_drill = thick / limit
                self.fail(
                    "PF-VIA-ASPECT", param,
                    f"{thick:g}mm board / {drill:g}mm mechanical drill = "
                    f"{ratio:.3f}:1 > tier '{self.tier['name']}' plated-"
                    f"through-hole limit {limit:g}:1 — the hole meets the "
                    f"diameter floor but is not reliably plateable at this "
                    f"board thickness (RX2 v4: 3,446 vias reached final "
                    f"review at 10.667:1)",
                    fix=f"use nominal_thickness_mm <= {max_thick:.3f}, or "
                        f"mechanical drill >= {min_drill:.3f}mm and re-run "
                        f"landability/clearance/impedance gates")

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
        # Paths outside Ctx.try_via must forward their own effective screen.
        # Taps expose taps.via.hole_to_copper; A* accepts an explicit pin or
        # inherits a matching stitch-via tier. Grade those values in BOTH
        # directions, then report only a genuinely unresolved path.
        def grade_path(param, value, source):
            if value is None:
                return False
            eff = float(value)
            self.note(f"{param}: effective {eff} [{source}] vs hole floor "
                      f"{H} [{hsrc}]")
            if eff > H + D["htc_slack"] + 1e-9:
                self.fail("PF-HTC", param,
                          f"effective {eff} is stricter than the board "
                          f"hole_clearance floor {H} by "
                          f"{round(eff - H, 3)}mm — a FALSE placement wall",
                          fix=f"hole_to_copper: {want}")
            elif eff < H - 1e-9:
                self.fail("PF-HTC", param,
                          f"explicit {eff} < board hole_clearance floor {H} "
                          f"[{hsrc}] — this emitter can place vias the DRC "
                          "hole_clearance check rejects",
                          fix=f"hole_to_copper: {want}")
            return True

        taps_ok = True
        if self.get("taps.connections"):
            taps_ok = grade_path(
                "taps.via.hole_to_copper",
                self.get("taps.via.hole_to_copper"), "explicit")

        astar_ok = True
        if "astar_fallback" in (self.get("stitch.passes") or []):
            av = self.get("stitch.astar_fallback.via") or {}
            ahtc = av.get("hole_to_copper") if isinstance(av, dict) else None
            asrc = "explicit"
            if ahtc is None:
                avs = float(av.get("size", self.tier["min_via_diameter"]))
                avd = float(av.get("drill", self.tier["min_via_drill"]))
                for te in self.get("stitch.via.tiers", []) or []:
                    if (abs(float(te.get("size", -1)) - avs) < 1e-9
                            and abs(float(te.get("drill", -1)) - avd) < 1e-9
                            and "hole_to_copper" in te):
                        ahtc = te["hole_to_copper"]
                        asrc = "matching stitch.via.tiers entry"
                        break
            astar_ok = grade_path(
                "stitch.astar_fallback.via.hole_to_copper", ahtc, asrc)

        if abs(D["via_site_htc"] - (H + 0.005)) > D["htc_slack"]:
            users = []
            if not taps_ok:
                users.append("taps")
            if not astar_ok:
                users.append("stitch.astar_fallback")
            if users:
                self.warn(
                    "PF-HTC", "+".join(users),
                    f"these paths have no resolved hole_to_copper screen and "
                    f"fall back to {D['via_site_htc']} (assumes a 0.20 floor), "
                    f"but this board's floor is {H}; set "
                    f"taps.via.hole_to_copper or "
                    f"stitch.astar_fallback.via.hole_to_copper")

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

    #: KRT's own `--fab-tier` choices (KiCadRoutingTools/fab_tiers.py TIERS).
    #: NOT this pipeline's tier vocabulary — that is fab_tiers.yaml, whose
    #: names (jlc_4layer_advanced, jlc_6layer_smallvia, ...) argparse REJECTS.
    KRT_PRESETS = ("standard", "advanced")

    def check_krt_preset(self):
        """PF-KRT: `route.common.fab_tier` is KRT's own {standard,advanced}
        PRESET, not this pipeline's fab tier. Two distinct defects:

        (1) FAIL — a value outside {standard, advanced}. KRT's argparse
            `choices` rejects it, so `route.py` exits 2 on the FIRST wave and
            the whole route stage is dead. MEASURED on pluto-rx2-8way,
            2026-07-29: `route.common.fab_tier: jlc_4layer_advanced` (the
            pipeline tier name, copied one level down) killed wave 1 while
            this very gate printed "0 FAIL / 0 WARN — config is
            tier-consistent" over it, because the old check read the value
            ONLY to compare it against the literal 'advanced' and returned
            silently on everything else. A gate that passes a value it never
            validated.
        (2) WARN — a legal 'advanced' preset on a tier whose via floor sits
            above KRT's internal 0.25, unpinned: KRT auto-escalates vias DOWN
            below the declared floor (crow-rv2 2026-07-23: 33 vias at 0.25 <
            the 0.30 floor until --fab-overrides pinned it).
        """
        preset = self.get("route.common.fab_tier")
        if preset is None:
            return                      # KRT's own default ('standard') applies
        if preset not in self.KRT_PRESETS:
            extra = ""
            if str(preset) == self.tier["name"]:
                extra = (" — this is the PIPELINE tier name (fab_tiers.yaml) "
                         "copied into a KRT-preset slot; the two vocabularies "
                         "are different and only one of them is argparse-legal")
            self.fail(
                "PF-KRT", "route.common.fab_tier",
                f"{preset!r} is not one of KRT's --fab-tier choices "
                f"{list(self.KRT_PRESETS)}{extra}. route.py's argparse "
                f"REJECTS it, so the FIRST wave exits 2 and no board is "
                f"routed (pluto-rx2-8way 2026-07-29: 'jlc_4layer_advanced' "
                f"here killed wave 1 while this gate said 'tier-consistent')",
                fix=f"route.common.fab_tier: advanced   # + "
                    f"route.common.fab_overrides pinning via "
                    f"{self.tier['min_via_diameter']}/"
                    f"{self.tier['min_via_drill']} for tier "
                    f"{self.tier['name']}")
            return
        self.note(f"KRT preset {preset!r} is argparse-legal "
                  f"{list(self.KRT_PRESETS)}; pipeline tier is "
                  f"{self.tier['name']} (a DIFFERENT vocabulary)")
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
            # TWO DIFFERENT FACTS, AND COLLAPSING THEM DISARMS THE GATE.
            # "this board declares no fab_tier" is a legacy board and a
            # legitimate exit 0. "I could not work out WHICH nets.yaml is
            # yours" is a zero denominator, and reporting it as the former is
            # how a multi-board project silently turned this whole gate off
            # (MEASURED 2026-07-30 on a synthetic ADR-0007 tree: `nothing to
            # check (legacy board)`, exit 0, with two fully-declared tiers
            # sitting in the tree).
            # ABSENT is a LEGACY board and a legitimate exit 0; AMBIGUOUS is
            # a zero denominator. Only the second disarms the gate silently.
            if self.nets_path is None and not self.nets_note.startswith(
                    "ABSENT:"):
                print(f"{head} — GRADED NOTHING: could not resolve the "
                      f"netclass declaration. {self.nets_note}")
                print(f"  A tier this gate cannot FIND is not a board that "
                      f"declares NO tier, and reporting the first as the "
                      f"second turns every check here off while exiting 0 "
                      f"(canon M-COVER).")
                return 1
            print(f"{head} — no fab_tier declared in {self.nets_note}; "
                  f"nothing to check (legacy board). Declare one to arm "
                  f"this gate.")
            return 0
        t = self.tier
        print(f"{head}  tier={t['name']} (via {t['min_via_diameter']}/"
              f"{t['min_via_drill']}, space {t['min_space']}, "
              f"h2h {t.get('min_hole_to_hole')})")
        print(f"  input: route config <- {self.route_note}")
        print(f"  input: netclasses   <- {self.nets_note}")
        # A GATE MAY NOT GRADE A FILE THAT IS NOT THERE (canon M-COVER).
        # MEASURED 2026-07-30 on smc0985-cooksense, whose route configs live at
        # `03_src/<board>/route.yaml` (ADR-0007) and which therefore has no
        # flat one: the old code set `self.cfg = {}` and ran every route check
        # anyway, so `self.get()` returned DEFAULTS and PF-ROUTE-CLR FAILED the
        # board over `route.common.clearance` — a key nothing had declared, in
        # a file that does not exist. Not a green-over-nothing; a RED over
        # nothing, which is the same defect wearing the other colour, and it
        # sends an agent to fix a value that is not there. The route half is
        # now reported as GRADED NOTHING and the route checks do not run.
        cfg_route = self.cfg is not None
        if cfg_route:
            self.check_clearances()
            self.check_via_geometry()
            self.check_via_aspect_ratio()
            self.check_normalize_vias()
            self.check_hole_to_copper()
            self.check_hole_to_hole()
            self.check_layers()
            self.check_via_site_source()
            self.check_krt_preset()
        self.check_legalize()          # floorplan-driven, needs no route cfg
        if self.explain:
            print("  derivations:")
            for n in self.notes:
                print(n)
        fails = [f for f in self.findings if f.level == "FAIL"]
        warns = [f for f in self.findings if f.level == "WARN"]
        for f in self.findings:
            print(f.render())
        if not cfg_route:
            print(f"tier preflight: GRADED NOTHING about the routing config — "
                  f"{self.route_note}.")
            print(f"  {len(fails)} FAIL / {len(warns)} WARN from the "
                  f"floorplan/toolkit checks only; the 8 route-config checks "
                  f"(PF-ROUTE-CLR, via geometry, hole-to-copper, hole-to-hole, "
                  f"layers, normalize_vias, via_site_source, krt_preset) each "
                  f"graded ZERO parameters.")
            print(f"  This is NOT 'tier-consistent' and it is NOT a pass: this "
                  f"gate exists to refuse a route BEFORE KRT spends hours, and "
                  f"it has not looked at the config that would be routed "
                  f"(canon M-COVER). Name the board with --board, or pass "
                  f"--route-config <path>.")
            return 1
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
    ap.add_argument("--board", default=None,
                    help="on an ADR-0007 MULTI-BOARD project, which board to "
                         "grade (config at 03_src/<board>/). Without it a "
                         "project whose boards each declare a route.yaml is "
                         "REFUSED rather than guessed at")
    a = ap.parse_args(argv)
    try:
        pf = Preflight(a.project_root, route_path=a.route_config,
                       toolkit=a.toolkit, explain=a.explain, board=a.board)
    except FabTierError as e:
        print(f"tier preflight: FAIL — {e}")
        return 1
    return pf.run()


if __name__ == "__main__":
    sys.exit(main())
