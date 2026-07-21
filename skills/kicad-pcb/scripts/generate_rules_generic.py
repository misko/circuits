#!/usr/bin/env python3
"""generate_rules_generic — the SHARED netclass/DRU emitter.

Reads <project>/03_src/rules/nets.yaml and MERGES netclasses into
<project>/04_kicad/<board>.kicad_pro (net_settings.classes +
net_settings.netclass_patterns) and writes width floors into the matching
`.kicad_dru`. It NEVER rewrites the .kicad_pro wholesale — it loads the JSON,
edits only net_settings, and writes it back, so the design_settings.rules
floors that generate_board_generic wrote survive (canon: generators merge, they
do not clobber — a clobbered .kicad_pro loses the DRC severity policy).

WHY SHARED (2026-07-20). Every board hand-wrote an identical ~90-line
generate_rules.py; the 03_src contract even called it "the ONLY per-board
emitter". A clean-room run proved the logic is 100% board-independent — it only
ever reads nets.yaml and globs the one .kicad_pro — so it belongs in the skill,
not copied into every board. A board now carries CONFIG (rules/nets.yaml), not
this emitter.

Emitted format is exactly what rules_audit.py validates:
  .kicad_pro net_settings.classes[]           -> {name, track_width, clearance, ...}
  .kicad_pro net_settings.netclass_patterns[] -> {netclass, pattern}  (pattern = net name)
  .kicad_dru  (rule "<CLASS>_width" (condition "A.NetClass=='<CLASS>'")
                 (constraint track_width (min <W>mm)))
pro track_width == dru min for every class (A-AGREE). Widths in nets.yaml are
pre-sized >= IPC-2221 requirement for the declared current (A-AMP).

Run LAST in the rebuild chain (pcbnew saves clobber .kicad_pro netclasses) AND
before route-prep (canon R1 — the route input must carry the netclasses).

usage: generate_rules_generic.py <project-root>   (dir containing 03_src/ and 04_kicad/)
       generate_rules_generic.py                   (cwd is the project root)
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import yaml
except ImportError:
    sys.exit("generate_rules_generic needs pyyaml")

from fab_tier_util import FabTierError, resolve as resolve_tier


def mm(v):
    if v is None:
        return None
    s = str(v).strip().lower().replace("mm", "").strip()
    return round(float(s), 3)


def extract_rules(text):
    """Parse a .kicad_dru into [(name, block_text), ...] by paren-depth scan.
    Handles quoted `(rule "X_width" ...)` and bare `(rule pad_rescue_stubs ...)`."""
    out = []
    i = 0
    while True:
        j = text.find("(rule", i)
        if j < 0:
            break
        depth, k = 0, j
        while k < len(text):
            if text[k] == "(":
                depth += 1
            elif text[k] == ")":
                depth -= 1
                if depth == 0:
                    k += 1
                    break
            k += 1
        block = text[j:k]
        m = re.match(r'\(rule\s+"?([^"\s()]+)"?', block)
        out.append((m.group(1) if m else "", block))
        i = k
    return out


def foreign_dru_rules(dru_path, generated_names):
    """Rules already in the .kicad_dru that generate_rules does NOT own — e.g.
    the `pad_rescue_stubs` insideArea sub-floor that stitch appends. generate_rules
    runs LAST and rewrites the dru wholesale; without this it would CLOBBER that
    exemption and the plane-drop via stubs would fail track_width again (the exact
    collision the clean-room 3S run's stub-floor fix would otherwise lose to
    generate_rules-LAST). Preserve them, and emit them AFTER our netclass rules so
    KiCad last-match precedence keeps the exemption winning inside its area."""
    p = Path(dru_path)
    if not p.is_file():
        return []
    return [blk for name, blk in extract_rules(p.read_text())
            if name and name not in generated_names]


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    root = Path(argv[0]).resolve() if argv else Path.cwd()
    src = root / "03_src"
    ki = root / "04_kicad"
    nets_path = src / "rules" / "nets.yaml"
    if not nets_path.is_file():
        sys.exit(f"generate_rules_generic: no {nets_path}")

    nets = yaml.safe_load(nets_path.read_text()) or {}
    classes = nets.get("classes") or {}
    try:
        tier = resolve_tier(root)
    except FabTierError as e:
        sys.exit(f"generate_rules_generic: {e}")

    pros = sorted(ki.glob("*.kicad_pro"))
    if not pros:
        sys.exit(f"generate_rules_generic: no .kicad_pro in {ki}")
    if len(pros) > 1:
        sys.exit(f"generate_rules_generic: >1 .kicad_pro in {ki} — one board file "
                 f"(contract 04_kicad): {[p.name for p in pros]}")
    pro = pros[0]
    board = pro.stem
    dru = ki / f"{board}.kicad_dru"

    proj = json.loads(pro.read_text())
    ns = proj.setdefault("net_settings", {})

    # keep any existing Default class, replace the rest with ours
    existing = {c.get("name"): c for c in ns.get("classes") or []}
    default = existing.get("Default", {
        "name": "Default", "clearance": 0.2, "track_width": 0.2,
        "via_diameter": 0.6, "via_drill": 0.3,
        "microvia_diameter": 0.3, "microvia_drill": 0.2,
        "diff_pair_gap": 0.25, "diff_pair_width": 0.2, "diff_pair_via_gap": 0.25,
        "wire_width": 6, "bus_width": 12, "line_style": 0,
        "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)",
    })

    out_classes = [default]
    patterns = []
    dru_rules = ['(version 1)']
    for name, c in classes.items():
        c = c or {}
        w = mm(c.get("min_width"))
        if w is None:
            sys.exit(f"generate_rules_generic: class {name} has no min_width")
        # CAPABILITY-DERIVED floor. With a declared fab_tier the fab's real
        # min_track is the floor, and an EXPLICIT width below it is an ERROR
        # (a silent clamp routes at a width the config never said — the pro/dru
        # disagreement incident, but between config and copper). Without a
        # tier, keep the historic conservative 0.25mm clamp verbatim.
        if tier is not None:
            floor = float(tier["min_track"])
            if w < floor:
                sys.exit(
                    f"generate_rules_generic: class {name} min_width {w}mm is "
                    f"below fab tier '{tier['name']}' min_track {floor}mm — no "
                    f"process at that tier makes it. Raise the width, or raise "
                    f"fab_tier (D-TIER); scoped_floors relaxations must also "
                    f"stay >= the tier floor")
        else:
            w = max(w, 0.25)
        clr = mm(c.get("clearance")) or 0.2
        via_d = mm(c.get("via_diameter")) or 0.6
        via_dr = mm(c.get("via_drill")) or 0.3
        out_classes.append({
            "name": name, "clearance": clr, "track_width": w,
            "via_diameter": via_d, "via_drill": via_dr,
            "microvia_diameter": 0.3, "microvia_drill": 0.2,
            "diff_pair_gap": 0.25, "diff_pair_width": w, "diff_pair_via_gap": 0.25,
            "wire_width": 6, "bus_width": 12, "line_style": 0,
            "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)",
        })
        for net in c.get("nets") or []:
            patterns.append({"netclass": name, "pattern": net})
        dru_rules.append(
            f'(rule "{name}_width"\n'
            f'  (condition "A.NetClass == \'{name}\'")\n'
            f'  (constraint track_width (min {w}mm)))')

    ns["classes"] = out_classes
    ns["netclass_patterns"] = patterns
    ns.setdefault("meta", {"version": 4})

    # SCOPED FLOORS (canon M8 two-strike promotion, 2026-07-21). Second board
    # needing a hand-appended insideArea width relaxation: cook-hub's u7_taps,
    # then the clean-room 3S's append_sw_floor.py (sense taps riding a pour-fed
    # SWITCH_NODE class inside 'sw_pour_zone'). The relaxation is now CONFIG:
    #   scoped_floors:
    #     - {zone: sw_pour_zone, nets: [SW], min_width: 0.3, why: "<evidence>"}
    # Emitted AFTER the netclass rules so KiCad LAST-MATCH precedence lets the
    # relaxation win only inside the named zone/rule-area (net-scoped when
    # `nets` is given — an unrelated thin net crossing the area keeps its own
    # floor, the stub-floor scoping lesson from 17f3c30). `why` is REQUIRED:
    # a floor relaxation without evidence is an inherited defect (canon M4).
    scoped_rules, scoped_names = [], set()
    for i, sf in enumerate(nets.get("scoped_floors") or []):
        sf = sf or {}
        zone = sf.get("zone")
        if not zone:
            sys.exit(f"generate_rules_generic: scoped_floors[{i}] has no "
                     f"`zone` — name the board zone/rule area it relaxes")
        sw = mm(sf.get("min_width"))
        if sw is None:
            sys.exit(f"generate_rules_generic: scoped_floors[{i}] "
                     f"(zone {zone}) has no min_width")
        if not str(sf.get("why") or "").strip():
            sys.exit(f"generate_rules_generic: scoped_floors[{i}] "
                     f"(zone {zone}) has no `why` — a scoped floor is a "
                     f"waived ampacity/width rule and needs EVIDENCE, not "
                     f"just intent (canon M4)")
        if tier is not None and sw < float(tier["min_track"]):
            sys.exit(f"generate_rules_generic: scoped_floors[{i}] "
                     f"(zone {zone}) min_width {sw}mm is below fab tier "
                     f"'{tier['name']}' min_track {tier['min_track']}mm — "
                     f"no scope makes that manufacturable")
        rname = f"scoped_{zone}"
        while rname in scoped_names:
            rname += "_"
        scoped_names.add(rname)
        cond = f"A.insideArea('{zone}')"
        snets = sf.get("nets") or []
        if snets:
            clause = " || ".join(f"A.NetName == '{n}'" for n in snets)
            cond += f" && ({clause})"
        scoped_rules.append(
            f'(rule "{rname}"\n'
            f'  (condition "{cond}")\n'
            f'  (constraint track_width (min {sw}mm)))')
    dru_rules += scoped_rules

    # PRESERVE foreign rules (e.g. stitch's pad_rescue_stubs sub-floor) so this
    # wholesale rewrite does not clobber them — emit them LAST for precedence.
    generated_names = {f"{name}_width" for name in classes} | scoped_names
    foreign = foreign_dru_rules(dru, generated_names)

    pro.write_text(json.dumps(proj, indent=2) + "\n")
    dru.write_text("\n".join(dru_rules + foreign) + "\n")
    print(f"generate_rules_generic: {len(out_classes)-1} netclasses + "
          f"{len(patterns)} patterns -> {pro.name}; {len(dru_rules)-1} width "
          f"rules"
          + (f" + {len(foreign)} preserved foreign rules" if foreign else "")
          + f" -> {dru.name}")


if __name__ == "__main__":
    main()
