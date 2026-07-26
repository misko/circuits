#!/usr/bin/env python3
"""rules_audit — validate GENERATED design rules against the intent that
produced them (`03_src/rules/nets.yaml`).

    python3 rules_audit.py PROJECT_DIR
    python3 rules_audit.py --nets rules/nets.yaml --pro b.kicad_pro --dru b.kicad_dru

WHY. `generate_rules.py` is a pure generator: it reads nets.yaml and writes
`.kicad_pro` + `.kicad_dru` without validating either side. Three real gaps
came out of auditing it, and each one ships a board whose copper does not
match its stated intent:

  A-CLASS  a class declared in nets.yaml never reaches the .kicad_pro
           netclass list (typo in the generator's key, or an empty `nets:`
           list) — the rule exists on paper and nowhere in KiCad.
  A-AGREE  the .kicad_pro netclass width and the .kicad_dru track_width
           constraint DISAGREE. generate_rules clamps the netclass to
           max(min_width, 0.25) but writes the raw min_width into the DRU,
           so `min_width: 0.1mm` silently yields a 0.25mm netclass and a
           0.10mm DRC floor. The router obeys one, DRC checks the other.
  A-ORDER  `generate_rules.py` is not the LAST thing to touch the project
           before the DRC gate in `03_src/rebuild_all.sh`. pcbnew saves
           rewrite `.kicad_pro`, so ANY board-writing step scheduled after
           the rules generator can drop the netclasses and their width
           floors on the floor — the gate then measures a board whose
           rules are gone, and passes. Every project's contracts.md line 5
           has said "generate_rules.py — ALWAYS LAST before DRC" since
           usb-power-3s; nothing read the rebuild script to check.

  A-AMP    the declared `current:` is not backed by the declared width.
           nets.yaml documents an ampacity intent per class; until now NO
           CODE READ IT. `current: 5A` next to `min_width: 0.2mm` generated
           a happy 0.25mm netclass and exited 0.

  A-FIRE   a rule in the `.kicad_dru` CANNOT FIRE, because its condition
           names a netclass that is not in the `.kicad_pro`, or a rule area
           that is not on the board. This is the "gate that cannot fail"
           class: the rule reads as enforcement, DRC reports 0, and nothing
           was ever checked. Every OTHER check here iterates over the
           classes DECLARED IN nets.yaml, so a DRU rule naming a class that
           nets.yaml no longer declares was examined by nothing at all —
           which is exactly how the surviving copies below were made.

           MEASURED on sealed bytes (2026-07-25), three boards:
             crow-mic-pod-v2 v1.0 — 2 of its 4 rules dead. `AUDIO_width`
               conditions on NetClass 'AUDIO'; the .kicad_pro defines only
               Default/BEEP/PWR because nets.yaml DELIBERATELY dropped the
               AUDIO class (its 0.25mm floor collided with KRT's 0.2498mm
               imported width) — and the DRU rule was left behind. The
               board carries 3 tracks at 0.2498mm, 0.0002mm under the floor
               that dead rule names, and DRC reports 0. The rule was
               removed from the class list to make DRC pass and its text
               was never removed with it.
             usb-hub-3s v1.x, usb-hub-3s-v2 — `pad_rescue_stubs` rule with
               no such rule area on the board.
           A dead rule is not cosmetic: it is the difference between a
           floor that is enforced and a floor that is merely written down.

Ampacity uses IPC-2221 external-layer constants (k=0.048, b=0.44, c=0.725)
at a default 10 C rise on 1 oz copper. Conservative on purpose: this is a
floor that says "this trace is not obviously undersized", not a thermal
simulation. Declare `delta_t:` / `copper_oz:` / `layer: internal` per class
to move it.

Exit 0 when every check passes, 1 on any FAIL.
"""
import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("rules_audit needs pyyaml")

# IPC-2221A: A_mils2 = (I / (k * dT^b)) ** (1/c)
IPC = {"external": 0.048, "internal": 0.024}
B, C = 0.44, 0.725
OZ_MILS = 1.378          # 1 oz/ft^2 finished copper thickness


def required_width_mm(current_a, delta_t=10.0, layer="external", oz=1.0):
    k = IPC["internal" if str(layer).startswith("int") else "external"]
    area_mils2 = (float(current_a) / (k * delta_t ** B)) ** (1.0 / C)
    width_mils = area_mils2 / (OZ_MILS * float(oz))
    return width_mils * 0.0254


def parse_mm(v):
    """'0.4mm' / '0.4' / 0.4 -> 0.4"""
    if v is None:
        return None
    s = str(v).strip().lower().replace("mm", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def parse_amps(v):
    if v is None:
        return None
    s = str(v).strip().lower().replace("a", "").strip()
    if s.endswith("m"):          # 500mA
        try:
            return float(s[:-1]) / 1000.0
        except ValueError:
            return None
    try:
        return float(s)
    except ValueError:
        return None


def dru_widths(text):
    """rule name -> (netclass, min track width mm)"""
    out = {}
    for m in re.finditer(r'\(rule\s+(\S+)(.*?)(?=\(rule\s|\Z)', text, re.S):
        name, body = m.group(1), m.group(2)
        nc = re.search(r"A\.NetClass\s*==\s*'([^']+)'", body)
        w = re.search(r"constraint\s+track_width\s*\(min\s+([0-9.]+)mm\)", body)
        if nc and w:
            out[nc.group(1)] = float(w.group(1))
    return out


def dru_rules(text):
    """[(rule_name, body)] for every `(rule NAME ...)` in a .kicad_dru."""
    return [(m.group(1).strip('"'), m.group(2))
            for m in re.finditer(r'\(rule\s+(\S+)(.*?)(?=\(rule\s|\Z)',
                                 text, re.S)]


def board_area_names(board_text):
    """Every named `(zone ...)` on a .kicad_pcb — rule areas AND copper
    pours, because `insideArea('X')` resolves against any zone named X."""
    names = set()
    for m in re.finditer(r"\(zone\b", board_text):
        # scan forward to this zone's own `(name "...")`, stopping at the
        # next zone so a later zone's name cannot be attributed to this one
        seg = board_text[m.end():m.end() + 4000]
        seg = seg.split("(zone")[0]
        n = re.search(r'\(name\s+"([^"]*)"\)', seg)
        if n and n.group(1):
            names.add(n.group(1))
    return names


def unfireable_rules(dru_text, pro_class_names, board_text, board_name):
    """A-FIRE — a rule whose condition can never be true enforces nothing.

    Returns a list of findings. A condition is checked only when we have the
    artifact that could refute it: `NetClass` always (the .kicad_pro is
    required), `insideArea` only when a board was supplied. Silence about an
    unreadable artifact is deliberate — a checker that guesses is the defect
    it is looking for.
    """
    fails = []
    known_classes = set(pro_class_names) | {"Default"}
    areas = board_area_names(board_text) if board_text else None
    for name, body in dru_rules(dru_text):
        # strip comments so a commented-out condition is not graded
        live = re.sub(r"#[^\n]*", "", body)
        for cls in re.findall(r"\b[AB]\.NetClass\s*==\s*'([^']+)'", live):
            if cls not in known_classes:
                fails.append(
                    f"A-FIRE rule {name!r}: conditions on NetClass {cls!r}, "
                    f"which is not a netclass in the project "
                    f"({sorted(known_classes)}) — the rule CANNOT FIRE and "
                    f"enforces nothing, while reading as if it does")
        if areas is None:
            continue
        for area in re.findall(r"\b[AB]\.insideArea\('([^']+)'\)", live):
            if area not in areas:
                fails.append(
                    f"A-FIRE rule {name!r}: conditions on "
                    f"insideArea({area!r}), and no zone/rule area of that "
                    f"name exists on {board_name} "
                    f"({len(areas)} named area(s): {sorted(areas)[:4]}) — "
                    f"the rule CANNOT FIRE and enforces nothing")
    return fails


DRC_GATE_RE = re.compile(r"kicad-cli\s+pcb\s+drc")
# BOTH backends: the generic one is `generate_rules_generic.py`. A pattern that
# matched only `generate_rules.py` reported "the DRC gate runs with no
# generate_rules.py before it" on EVERY generic-backend board whose
# rebuild_all.sh was in fact correct — a false positive that taught readers to
# ignore A-ORDER, which is how a real ordering defect would have gotten through
# (measured on crow-mic-pod-v2, whose rebuild_all.sh:38 runs the generic
# generator LAST and was flagged anyway; 2026-07-25).
RULES_RE = re.compile(r"generate_rules(?:_generic)?\.py")
# A-ORDER's concern is a step that WRITES the board (a pcbnew save clobbers the
# netclasses). These do not: they are the generator itself, and read-only
# CHECKERS that belong exactly here — between the last generate_rules and the
# DRC gate — because they grade the rules DRC is about to be measured against.
# Flagging a checker for standing where it must stand would force it out of the
# one position where it is useful.
READONLY_AFTER_RULES = {
    "generate_rules.py", "generate_rules_generic.py",   # the generator
    "rules_audit.py",                                   # A-FIRE/A-CLASS/A-AGREE
}
# A script invocation, ignoring inline heredoc python (`python3 - <<'PYEOF'`),
# which reads the DRC json and cannot touch the board.
SCRIPT_RE = re.compile(r"(?<![-\w])([\w./$\"{}]*\.py)\b")


def rebuild_order_fails(path):
    """A-ORDER — see the incident in this module's docstring.

    THE CONTRACT (every project's 03_src/contracts.md, line 5):
    "generate_rules.py — ALWAYS LAST before DRC (pcbnew saves clobber
    .kicad_pro netclasses)". A board-writing step scheduled after the rules
    generator can drop the netclasses, and the DRC gate then measures a
    board with no width floors and reports 0/0/0.

    So: between the LAST generate_rules.py and the `kicad-cli pcb drc` gate
    there must be NO other script invocation.
    """
    path = Path(path)
    if not path.is_file():
        return []
    lines = path.read_text().splitlines()
    gate = next((i for i, l in enumerate(lines) if DRC_GATE_RE.search(l)), None)
    if gate is None:
        return []                       # no DRC gate in this chain: not our call
    rules = [i for i, l in enumerate(lines[:gate]) if RULES_RE.search(l)]
    if not rules:
        return [f"A-ORDER {path.name}: the DRC gate runs with no "
                f"generate_rules.py before it — the board is graded against "
                f"whatever rules happened to survive the last pcbnew save"]
    after = []
    for i in range(rules[-1] + 1, gate):
        line = lines[i].strip()
        if not line or line.startswith("#") or line.startswith("<<"):
            continue
        for m in SCRIPT_RE.finditer(line):
            name = m.group(1)
            if Path(name).name in READONLY_AFTER_RULES:
                continue
            after.append(f"{name} (line {i + 1})")
    if after:
        return [f"A-ORDER {path.name}: {len(after)} step(s) run AFTER the last "
                f"generate_rules.py and before the DRC gate — a pcbnew save "
                f"there clobbers the netclasses the gate is supposed to "
                f"enforce: {after[:5]}"]
    return []


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("project", nargs="?", help="project dir (finds the rest)")
    ap.add_argument("--nets")
    ap.add_argument("--pro")
    ap.add_argument("--dru")
    ap.add_argument("--board", help=".kicad_pcb — supplies the rule-area "
                                    "names A-FIRE resolves insideArea() against")
    ap.add_argument("--delta-t", type=float, default=10.0)
    # RED-VERIFY hook (tests only): neuter A-FIRE so a known-bad fixture is
    # shown to pass when — and only when — that family is disabled.
    ap.add_argument("--_disable-fire", action="store_true",
                    help=argparse.SUPPRESS)
    a = ap.parse_args(argv)

    board = Path(a.board) if a.board else None
    if a.project:
        p = Path(a.project)
        nets = Path(a.nets) if a.nets else p / "03_src" / "rules" / "nets.yaml"
        pros = sorted((p / "04_kicad").glob("*.kicad_pro"))
        drus = sorted((p / "04_kicad").glob("*.kicad_dru"))
        pcbs = sorted((p / "04_kicad").glob("*.kicad_pcb"))
        pro = Path(a.pro) if a.pro else (pros[0] if pros else None)
        dru = Path(a.dru) if a.dru else (drus[0] if drus else None)
        board = board or (pcbs[0] if pcbs else None)
    else:
        nets, pro, dru = Path(a.nets), Path(a.pro), Path(a.dru) if a.dru else None

    if not nets or not nets.is_file():
        print(f"FAIL A-SRC: nets.yaml not found at {nets}")
        return 1
    if not pro or not pro.is_file():
        print(f"FAIL A-SRC: .kicad_pro not found at {pro}")
        return 1

    spec = yaml.safe_load(nets.read_text()) or {}
    classes = spec.get("classes") or {}
    proj = json.loads(pro.read_text())
    ns = proj.get("net_settings") or {}
    pro_classes = {c.get("name"): c for c in ns.get("classes") or []}
    patterns = ns.get("netclass_patterns") or []
    pat_by_class = {}
    for e in patterns:
        pat_by_class.setdefault(e.get("netclass"), set()).add(e.get("pattern"))
    dtext = dru.read_text() if dru and dru.is_file() else ""
    dwidths = dru_widths(dtext)

    fails, oks = [], []

    for name, c in classes.items():
        c = c or {}
        want_w = parse_mm(c.get("min_width"))

        # A-CLASS: the class must actually exist in the generated project
        if name not in pro_classes:
            fails.append(f"A-CLASS {name}: declared in nets.yaml but absent "
                         f"from {pro.name} netclasses "
                         f"({sorted(pro_classes)})")
            continue
        got_w = parse_mm(pro_classes[name].get("track_width"))
        oks.append(f"A-CLASS {name} present (track_width {got_w}mm)")

        # every net in the class must be routed to it by a pattern
        for net in c.get("nets") or []:
            if net not in pat_by_class.get(name, set()):
                fails.append(f"A-CLASS {name}: net {net!r} has no "
                             f"netclass_pattern — it will route as Default")

        # A-AGREE: .kicad_pro and .kicad_dru must not disagree
        if name in dwidths:
            if abs(dwidths[name] - (got_w or 0)) > 1e-6:
                fails.append(
                    f"A-AGREE {name}: {pro.name} netclass width "
                    f"{got_w}mm != {dru.name} track_width min "
                    f"{dwidths[name]}mm — the router and DRC will "
                    f"enforce different floors")
            else:
                oks.append(f"A-AGREE {name} pro/dru agree at {got_w}mm")
        elif want_w is not None and dtext:
            fails.append(f"A-AGREE {name}: no track_width rule in {dru.name}")

        # A-AMP: the declared current must be backed by the declared width
        cur = parse_amps(c.get("current"))
        if cur is None:
            oks.append(f"A-AMP {name} n/a (no current: declared)")
            continue
        need = required_width_mm(cur, c.get("delta_t", a.delta_t),
                                 c.get("layer", "external"),
                                 c.get("copper_oz", 1.0))
        eff = min([w for w in (want_w, got_w, dwidths.get(name)) if w is not None]
                  or [0.0])
        if eff + 1e-9 < need:
            fails.append(
                f"A-AMP {name}: carries {cur}A but the narrowest enforced "
                f"width is {eff}mm; IPC-2221 needs >= {need:.3f}mm "
                f"(dT={c.get('delta_t', a.delta_t)}C, "
                f"{c.get('copper_oz', 1.0)}oz, {c.get('layer', 'external')})")
        else:
            oks.append(f"A-AMP {name} {cur}A ok at {eff}mm (need {need:.3f}mm)")

    if len(pro_classes) <= 1:
        fails.append(f"A-CLASS: {pro.name} has no netclass beyond Default — "
                     f"generate_rules did not run, or nets.yaml is empty")

    # A-FIRE: every rule in the DRU must be ABLE to fire. Deliberately NOT
    # scoped to nets.yaml's classes — a rule naming a class nets.yaml dropped
    # is precisely the case every other check above walks straight past.
    if dtext and not a._disable_fire:
        btext = board.read_text() if board and board.is_file() else ""
        fire = unfireable_rules(dtext, set(pro_classes), btext,
                                board.name if board else "the board")
        fails.extend(fire)
        n_rules = len(dru_rules(dtext))
        if not fire:
            oks.append(f"A-FIRE all {n_rules} {dru.name} rule(s) can fire"
                       + ("" if btext else
                          " (netclass conditions only — no --board, so "
                          "insideArea() was NOT graded)"))

    # A-ORDER: generate_rules must be the last thing to touch the project
    # before the DRC gate. See rebuild_order_fails() for the incident.
    if a.project:
        reb = Path(a.project) / "03_src" / "rebuild_all.sh"
        order_fails = rebuild_order_fails(reb)
        fails.extend(order_fails)
        if reb.is_file() and not order_fails:
            oks.append("A-ORDER generate_rules runs last before the DRC gate")

    for o in oks:
        print("  ok  ", o)
    for f in sorted(set(fails)):
        print("FAIL ", f)
    print("RULES AUDIT:", "FAIL" if fails else "PASS",
          f"({len(set(fails))} fails, {len(oks)} checks)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
