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

import dru_subject
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


def foreign_dru_rules(dru_path, generated_names, pcb_path=None):
    """Rules already in the .kicad_dru that generate_rules does NOT own — e.g.
    the `pad_rescue_stubs` insideArea sub-floor that stitch appends. generate_rules
    runs LAST and rewrites the dru wholesale; without this it would CLOBBER that
    exemption and the plane-drop via stubs would fail track_width again (the exact
    collision the clean-room 3S run's stub-floor fix would otherwise lose to
    generate_rules-LAST). Preserve them, and emit them AFTER our netclass rules so
    KiCad last-match precedence keeps the exemption winning inside its area.

    Returns `(kept_blocks, decisions)`, decisions being [(name, members, kept)]
    with `members` None for "not derivable".

    PRESERVATION IS NOT UNCONDITIONAL (2026-07-31). It used to be one-way — a
    rule, once preserved, was preserved forever — so a rule outlived the
    geometry it was written for and became a predicate that can never fire
    (G-VACUOUS-DRU). The measured instance: stitch's `_scope_stub_floor` emits
    the `pad_rescue_stubs` rule area and its `.kicad_dru` rule together, but
    only `if stub_boxes`; on a board whose plane pads all take a via-in-pad
    barrel there are no boxes, the rule area is absent from the saved board,
    and the rule from an earlier run rode along regardless. Fleet at the time:
    6 boards carried the rule, 4 with live subjects (25/16/6/2 members) and 2
    with NO rule area on the board at all.

    So each run RE-DERIVES the subject and retires a rule with a positively
    derived ZERO — never silently: every decision is printed with the count
    that justified it. `dru_subject.members` returns None rather than 0 for
    anything it cannot fully evaluate, and None means KEEP, so the failure
    mode is a dead rule surviving (which `gate_contract_audit.py --dru` then
    grades) and never a live exemption being dropped."""
    p = Path(dru_path)
    if not p.is_file():
        return [], []
    foreign = [(name, blk)
               for name, blk in extract_rules(p.read_text(encoding="utf-8-sig"))
               if name and name not in generated_names]
    if not foreign:
        return [], []

    inv = None
    if pcb_path is not None and Path(pcb_path).is_file():
        try:
            inv = dru_subject.index_board(pcb_path)
        except Exception as e:                                # noqa: BLE001
            print(f"generate_rules_generic: could not index {Path(pcb_path).name} "
                  f"for foreign-rule subjects ({e}) — preserving all "
                  f"{len(foreign)} foreign rule(s) unretired")

    kept, decisions = [], []
    for name, blk in foreign:
        n = None if inv is None else dru_subject.members(blk, inv)
        keep = n is None or n > 0
        decisions.append((name, n, keep))
        if keep:
            kept.append(blk)
    return kept, decisions


def report_foreign_decisions(decisions, board):
    """SAY IT OUT LOUD. A rule vanishing from a generated file with no line of
    output is how a preserved exemption would be lost without anyone noticing —
    the same silence that let the vacuous ones survive."""
    for name, n, keep in decisions:
        if keep and n is None:
            print(f"generate_rules_generic: preserved foreign rule {name!r} "
                  f"— subject NOT DERIVABLE from {board}.kicad_pcb, kept "
                  f"(retirement needs a positively derived zero)")
        elif keep:
            print(f"generate_rules_generic: preserved foreign rule {name!r} "
                  f"— {n} board item(s) still match it, kept")
        else:
            print(f"generate_rules_generic: RETIRED foreign rule {name!r} "
                  f"— 0 board items match its condition on "
                  f"{board}.kicad_pcb, so it can never fire "
                  f"(G-VACUOUS-DRU). Re-emit it by re-running the pass that "
                  f"owns it (e.g. stitch's pad_rescue stub_scope)")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    root = Path(argv[0]).resolve() if argv else Path.cwd()
    src = root / "03_src"
    ki = root / "04_kicad"
    nets_path = src / "rules" / "nets.yaml"
    if not nets_path.is_file():
        sys.exit(f"generate_rules_generic: no {nets_path}")

    nets = yaml.safe_load(nets_path.read_text(encoding="utf-8-sig")) or {}
    classes = nets.get("classes") or {}
    try:
        tier = resolve_tier(root)
    except FabTierError as e:
        sys.exit(f"generate_rules_generic: {e}")

    # PURGE kicad-cli droppings first (promoted from crow-rv2's bespoke
    # rmstray, 2026-07-23 / canon M8): every `kicad-cli pcb drc` and stitch
    # gate drops a stray `<board>.kicad_pcb.kicad_pro` (+ `.kicad_prl`) beside
    # the board, which then trips the one-board-file abort below and kills the
    # rebuild. The DOUBLE extension makes them unambiguous tool droppings —
    # only those are purged; a genuine second `.kicad_pro` still aborts
    # (pinned by t1_rules_bom.py: t_rules_purges_kicadcli_droppings, RED-
    # verified against this pre-purge code, + t_kb_rules_second_pro_still_aborts).
    for stray in list(ki.glob("*.kicad_pcb.kicad_pro")) + list(ki.glob("*.kicad_pcb.kicad_prl")):
        stray.unlink()
        print(f"generate_rules_generic: purged stray kicad-cli dropping {stray.name}")

    pros = sorted(ki.glob("*.kicad_pro"))
    if not pros:
        sys.exit(f"generate_rules_generic: no .kicad_pro in {ki}")
    if len(pros) > 1:
        sys.exit(f"generate_rules_generic: >1 .kicad_pro in {ki} — one board file "
                 f"(contract 04_kicad): {[p.name for p in pros]}")
    pro = pros[0]
    board = pro.stem
    dru = ki / f"{board}.kicad_dru"

    proj = json.loads(pro.read_text(encoding="utf-8-sig"))
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
    # OPTIONAL nets.yaml top-level overrides for the Default class (2026-07-23):
    # a board on a tighter fab tier may set `default_clearance:`/`default_track_width:`
    # to route the whole board at the tier's real floor (e.g. 0.15mm on JLC 2-layer)
    # instead of the conservative 0.2mm baked default. Absent -> unchanged, so no
    # other board is affected. Must stay >= the tier floors (min_space / min_track).
    default = dict(default)
    if nets.get("default_clearance") is not None:
        dc = mm(nets["default_clearance"])
        floor = float(tier["min_space"]) if tier else 0.0
        if dc < floor:
            sys.exit(f"generate_rules_generic: default_clearance {dc}mm < fab tier "
                     f"'{tier['name']}' min_space {floor}mm")
        default["clearance"] = dc
    if nets.get("default_track_width") is not None:
        dw = mm(nets["default_track_width"])
        floor = float(tier["min_track"]) if tier else 0.0
        if dw < floor:
            sys.exit(f"generate_rules_generic: default_track_width {dw}mm < fab tier "
                     f"'{tier['name']}' min_track {floor}mm")
        default["track_width"] = dw

    out_classes = [default]
    patterns = []
    diff_dims = []
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
        # OPTIONAL controlled-impedance diff-pair geometry (2026-07-24,
        # crow-recorder-central-v2 v1.1 / external-review F2: USB HS 90ohm was
        # neither constrained nor demonstrated — diff_pair_dimensions sat []).
        #   diff_pair: {width: 0.125, gap: 0.15, via_gap: 0.15,
        #               max_uncoupled: 5}   # mm; via_gap/max_uncoupled optional
        # Emits: netclass diff_pair_width/gap/via_gap, a .kicad_dru
        # diff_pair_gap (+ optional diff_pair_uncoupled) rule, and the board
        # design_settings.diff_pair_dimensions entry — so the rule is ACTIVE
        # in DRC, not just documented. NB KiCad only pairs nets by name suffix
        # (P/N, +/-, _P/_N): a class declaring diff_pair whose nets cannot
        # pair silently gates nothing — keep net names pairable.
        dp = c.get("diff_pair") or {}
        dp_w = mm(dp.get("width")) or w
        dp_gap = mm(dp.get("gap"))
        dp_via_gap = mm(dp.get("via_gap")) or dp_gap or 0.25
        dp_unc = mm(dp.get("max_uncoupled"))
        if dp and dp_gap is None:
            sys.exit(f"generate_rules_generic: class {name} diff_pair has no "
                     f"`gap` — a diff-pair class without its solved gap "
                     f"enforces nothing")
        if dp and tier is not None:
            if dp_w < float(tier["min_track"]):
                sys.exit(f"generate_rules_generic: class {name} diff_pair "
                         f"width {dp_w}mm < fab tier '{tier['name']}' "
                         f"min_track {tier['min_track']}mm")
            if dp_gap < float(tier["min_space"]):
                sys.exit(f"generate_rules_generic: class {name} diff_pair "
                         f"gap {dp_gap}mm < fab tier '{tier['name']}' "
                         f"min_space {tier['min_space']}mm")
        out_classes.append({
            "name": name, "clearance": clr, "track_width": w,
            "via_diameter": via_d, "via_drill": via_dr,
            "microvia_diameter": 0.3, "microvia_drill": 0.2,
            "diff_pair_gap": dp_gap if dp else 0.25,
            "diff_pair_width": dp_w,
            "diff_pair_via_gap": dp_via_gap if dp else 0.25,
            "wire_width": 6, "bus_width": 12, "line_style": 0,
            "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)",
        })
        for net in c.get("nets") or []:
            patterns.append({"netclass": name, "pattern": net})
        dru_rules.append(
            f'(rule "{name}_width"\n'
            f'  (condition "A.NetClass == \'{name}\'")\n'
            f'  (constraint track_width (min {w}mm)))')
        if dp:
            gap_rule = (
                f'(rule "{name}_diffpair"\n'
                f'  (condition "A.NetClass == \'{name}\'")\n'
                f'  (constraint diff_pair_gap (min {round(dp_gap-0.005,3)}mm) '
                f'(opt {dp_gap}mm))')
            if dp_unc is not None:
                gap_rule += (f'\n  (constraint diff_pair_uncoupled '
                             f'(max {dp_unc}mm))')
            dru_rules.append(gap_rule + ')')
            diff_dims.append({"gap": dp_gap, "via_gap": dp_via_gap,
                              "width": dp_w})

    ns["classes"] = out_classes
    ns["netclass_patterns"] = patterns
    ns.setdefault("meta", {"version": 4})
    if diff_dims:
        # board design_settings.diff_pair_dimensions — the routing/tuning UI's
        # diff-pair table AND the reviewable declaration that the geometry was
        # SOLVED (external-review F2: [] here read as "impedance undemonstrated")
        bds = proj.setdefault("board", {}).setdefault("design_settings", {})
        bds["diff_pair_dimensions"] = sorted(
            diff_dims, key=lambda d: (d["width"], d["gap"]))

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
    # SCOPED CLEARANCES (2026-07-30, pluto-rx2-8way). The width relaxation
    # above has a CLEARANCE twin and the emitter could not say it, so a routed,
    # promoted board sat on 49 DRC findings that are ONE missing capability:
    #   scoped_clearances:
    #     - {zone: rf_launch, nets: [ANT1, ...], clearance: 0.14,
    #        why: "<measurement>"}
    # MEASURED REQUIREMENT: a 0.36mm RF arm cannot leave the PE42482A-X land at
    # that board's 0.2mm clearance — a 20-point width x clearance sweep on r0
    # routes 11/11 at 0.145 and 6/11 at 0.15. The board declares 0.2 UP from
    # its 0.09 tier floor ON PURPOSE (on it clearance is ISOLATION, not a
    # routability tax), so lowering the board-wide floor is the wrong answer
    # and a LAUNCH-LOCAL relaxation is the right one. pluto-cal-switch had
    # already done the width half of this by hand with three permissive rule
    # areas (canon M8 two-strike shape).
    #
    # A SEPARATE LIST, NOT A FIELD ON scoped_floors, and that is a judgement:
    # the two validate against DIFFERENT tier floors (min_track vs min_space),
    # emit different constraints, and mean different things — width is bounded
    # below by ampacity, which A-AMP grades from `current:` independently, while
    # an isolation relaxation has NO downstream grader at all. Merging them
    # would make every required key conditional ("min_width required unless
    # clearance is present"), which is how a required key stops being required.
    #
    # BOUNDED ON BOTH SIDES. Clearance is a property of a PAIR, so the
    # condition requires A **and** B insideArea: a one-sided condition would
    # license a pair whose second item is anywhere on the board. The net clause
    # is symmetric (A.NetName or B.NetName) because the relaxed net can be
    # either member of the pair — the pluto case is an RF arm against an SMA
    # PTH ground post, and which of the two KiCad calls `A` is not ours to
    # assume. CAVEAT worth knowing before drawing the area: KiCad's insideArea
    # is true for an item that OVERLAPS the area, not only one contained by it,
    # so the bound is on the ITEMS and not on their point of closest approach.
    # Draw the region tightly.
    #
    # `nets` is REQUIRED here though it is optional for scoped_floors: "every
    # pair inside this box" is not an isolation argument. `why` is REQUIRED for
    # a STRONGER reason than the width case (canon M4) — nothing downstream
    # re-derives an isolation gap, DRC simply stops reporting what the rule
    # permits, so an unexplained one is silent by construction.
    clr_rules, clr_names = [], set()
    for i, sc in enumerate(nets.get("scoped_clearances") or []):
        sc = sc or {}
        zone = sc.get("zone")
        if not zone:
            sys.exit(f"generate_rules_generic: scoped_clearances[{i}] has no "
                     f"`zone` — an unbounded clearance relaxation is a "
                     f"BOARD-WIDE one; name the rule area it is local to")
        scv = mm(sc.get("clearance"))
        if scv is None:
            sys.exit(f"generate_rules_generic: scoped_clearances[{i}] "
                     f"(zone {zone}) has no `clearance`")
        cnets = sc.get("nets") or []
        if not cnets:
            sys.exit(f"generate_rules_generic: scoped_clearances[{i}] "
                     f"(zone {zone}) has no `nets` — clearance is a property "
                     f"of a PAIR, and 'every pair inside this area' is not an "
                     f"isolation argument. Name the nets whose isolation is "
                     f"being reduced (`nets` is optional for scoped_floors "
                     f"because a width floor has no counterparty)")
        if not str(sc.get("why") or "").strip():
            sys.exit(f"generate_rules_generic: scoped_clearances[{i}] "
                     f"(zone {zone}) has no `why` — a clearance relaxation is "
                     f"a waived ISOLATION rule and needs EVIDENCE, not intent "
                     f"(canon M4). Unlike a width relaxation it has NO "
                     f"downstream grader: DRC simply stops reporting what this "
                     f"rule permits")
        if tier is not None and scv < float(tier["min_space"]):
            sys.exit(f"generate_rules_generic: scoped_clearances[{i}] "
                     f"(zone {zone}) clearance {scv}mm is below fab tier "
                     f"'{tier['name']}' min_space {tier['min_space']}mm — a "
                     f"scope relaxes a NETCLASS floor, never the FAB's")
        rname = f"scoped_clr_{zone}"
        while rname in clr_names:
            rname += "_"
        clr_names.add(rname)
        clause = " || ".join(f"A.NetName == '{n}' || B.NetName == '{n}'"
                             for n in cnets)
        cond = (f"A.insideArea('{zone}') && B.insideArea('{zone}') "
                f"&& ({clause})")
        clr_rules.append(
            f'(rule "{rname}"\n'
            f'  (condition "{cond}")\n'
            f'  (constraint clearance (min {scv}mm)))')
    dru_rules += scoped_rules + clr_rules

    # PRESERVE foreign rules (e.g. stitch's pad_rescue_stubs sub-floor) so this
    # wholesale rewrite does not clobber them — emit them LAST for precedence.
    generated_names = ({f"{name}_width" for name in classes}
                       | {f"{name}_diffpair" for name in classes}
                       | scoped_names | clr_names)
    foreign, decisions = foreign_dru_rules(dru, generated_names,
                                           ki / f"{board}.kicad_pcb")
    report_foreign_decisions(decisions, board)
    retired = [d for d in decisions if not d[2]]

    pro.write_text(json.dumps(proj, indent=2) + "\n")
    dru.write_text("\n".join(dru_rules + foreign) + "\n")
    print(f"generate_rules_generic: {len(out_classes)-1} netclasses + "
          f"{len(patterns)} patterns -> {pro.name}; "
          f"{len(dru_rules)-1-len(clr_rules)} width rules"
          + (f" + {len(clr_rules)} scoped clearance rules" if clr_rules else "")
          + (f" + {len(foreign)} preserved foreign rules" if foreign else "")
          + (f" + {len(retired)} retired ({', '.join(d[0] for d in retired)})"
             if retired else "")
          + f" -> {dru.name}")


if __name__ == "__main__":
    main()
