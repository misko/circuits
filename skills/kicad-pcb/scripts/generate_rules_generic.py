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
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("generate_rules_generic needs pyyaml")


def mm(v):
    if v is None:
        return None
    s = str(v).strip().lower().replace("mm", "").strip()
    return round(float(s), 3)


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

    pro.write_text(json.dumps(proj, indent=2) + "\n")
    dru.write_text("\n".join(dru_rules) + "\n")
    print(f"generate_rules_generic: {len(out_classes)-1} netclasses + "
          f"{len(patterns)} patterns -> {pro.name}; {len(dru_rules)-1} width "
          f"rules -> {dru.name}")


if __name__ == "__main__":
    main()
