#!/usr/bin/env python3
"""T1: generate_rules.py + rules_audit.py + bom_seed.py.

generate_rules is a pure GENERATOR — it never validated its own output, so
"test the checker" here meant building the checker: `rules_audit.py` reads
`rules/nets.yaml` back against the generated `.kicad_pro`/`.kicad_dru` and
enforces the ampacity intent that until now no code read at all.
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, ROOT, SCRIPTS, check, contains, eq, main,  # noqa: E402
                     must_fail, must_pass, project_copy, run, test, tmpdir)

RULES_AUDIT = SCRIPTS / "rules_audit.py"
LC = ROOT / "archived_projects" / "cook-loadcell"
PY = sys.executable or "python3"


def rules_project():
    """A scratch cook-loadcell with a fresh .kicad_pro, then generate_rules."""
    d = tmpdir("rules_")
    proj = project_copy("cook-loadcell", d / "proj")
    shutil.copy(LC / "04_kicad" / "cook_loadcell.kicad_pro", proj / "04_kicad")
    must_pass(run([PY, "03_src/generate_rules.py"], cwd=proj), "generate_rules")
    return proj


def set_nets_yaml(proj, mutate):
    import yaml
    p = proj / "03_src" / "rules" / "nets.yaml"
    spec = yaml.safe_load(p.read_text())
    mutate(spec)
    p.write_text(yaml.safe_dump(spec))
    must_pass(run([PY, "03_src/generate_rules.py"], cwd=proj), "generate_rules (mutated)")
    return proj


# ---------------------------------------------------------- clean cases
@test("generate_rules writes every nets.yaml class into .kicad_pro AND .kicad_dru")
def t_rules_written():
    proj = rules_project()
    pro = json.loads((proj / "04_kicad" / "cook_loadcell.kicad_pro").read_text())
    names = {c["name"] for c in pro["net_settings"]["classes"]}
    check({"BRIDGE", "PWR"} <= names,
          f"netclasses missing from .kicad_pro: {sorted(names)}")
    widths = {c["name"]: c.get("track_width") for c in pro["net_settings"]["classes"]}
    eq(widths.get("BRIDGE"), 0.5, "BRIDGE track_width")
    eq(widths.get("PWR"), 0.4, "PWR track_width")
    # nets must be ROUTED to their class, not merely declared
    pats = {(e["netclass"], e["pattern"]) for e in pro["net_settings"]["netclass_patterns"]}
    check(("BRIDGE", "E_PLUS") in pats, "E_PLUS not patterned to BRIDGE")
    check(("PWR", "5V") in pats, "5V not patterned to PWR")
    dru = (proj / "04_kicad" / "cook_loadcell.kicad_dru").read_text()
    contains(dru, "A.NetClass == 'BRIDGE'", ".kicad_dru")
    contains(dru, "(min 0.50mm)", ".kicad_dru BRIDGE width")


@test("rules_audit PASSes on a correctly generated project")
def t_rules_audit_clean():
    proj = rules_project()
    r = must_pass(run([PY, RULES_AUDIT, proj]), "rules_audit clean")
    contains(r.out, "RULES AUDIT: PASS", "rules_audit verdict")


GEN_RULES = SCRIPTS / "generate_rules_generic.py"


@test("SHARED generate_rules_generic PRESERVES a foreign pad_rescue_stubs rule "
      "through its wholesale .kicad_dru rewrite (gap #1/#3 collision)")
def t_generate_rules_preserves_foreign():
    """generate_rules runs LAST and rewrites .kicad_dru wholesale; stitch's
    pad_rescue stub-floor exemption (a `pad_rescue_stubs` insideArea rule) is
    written EARLIER. Without preservation the rewrite clobbers it and the
    plane-drop via stubs fail track_width again — the exact collision between
    the clean-room 3S run's shared-generate_rules (gap #1) and stub-floor
    scoping (gap #3). Verified RED against the pre-preservation wholesale write
    (which drops the rule) — 2026-07-20.

    NO BOARD FILE HERE, deliberately: this is the ORIGINAL preservation
    contract, and with no `.kicad_pcb` to index there is no subject to
    re-derive, so retirement (2026-07-31) cannot apply and preservation is
    unconditional. That is the documented degradation — no evidence, no
    retirement. The three tests below supply a board and exercise the
    decision itself."""
    d = tmpdir("grforeign_")
    proj = project_copy("cook-loadcell", d / "proj")
    shutil.copy(LC / "04_kicad" / "cook_loadcell.kicad_pro", proj / "04_kicad")
    dru = proj / "04_kicad" / "cook_loadcell.kicad_dru"
    # step 5: generate_rules runs first, creating the dru
    must_pass(run([PY, GEN_RULES, proj]), "generate_rules_generic (first)")
    # step 8: simulate stitch having appended the exemption
    dru.write_text(dru.read_text().rstrip() + "\n"
                   "(rule pad_rescue_stubs\n"
                   "  (condition \"A.insideArea('pad_rescue_stubs')\")\n"
                   "  (constraint track_width (min 0.300mm)))\n")
    # step 9: the SHARED emitter, run LAST, must not clobber it
    must_pass(run([PY, GEN_RULES, proj]), "generate_rules_generic (last)")
    txt = dru.read_text()
    contains(txt, "(rule pad_rescue_stubs", "foreign rule survived rewrite")
    contains(txt, "A.NetClass == 'BRIDGE'", "netclass rules still regenerated")
    # foreign rule must be LAST (KiCad last-match precedence keeps the exemption)
    check(txt.rstrip().endswith("mm)))") and
          txt.index("pad_rescue_stubs") > txt.index("BRIDGE"),
          "pad_rescue_stubs must be emitted AFTER the netclass rules")


# ------------------------------------------- retiring a preserved rule (G-VACUOUS-DRU)
# Preservation used to be ONE-WAY: `foreign_dru_rules` carried any rule it did
# not own forward on every run and nothing ever retired one, so a rule outlived
# the geometry it was written for. Measured on the fleet 2026-07-31: 6 boards
# carry a `pad_rescue_stubs` rule; 4 have live subjects (crow-recorder-central-v2
# 377 members, usb-hub-3s-v3 44, pluto-cal-switch 41, pluto-rx2-8way 5) and 2
# have NO rule area on the board at all (crow-mic-pod-v2, programmable-usb2-hub),
# because stitch's `_scope_stub_floor` emits the area only `if stub_boxes` and
# those boards' plane pads all take a via-in-pad barrel.
#
# So the decision is PER BOARD and the fixtures come in BOTH polarities: a blanket
# delete would pass the retirement test and drop four live exemptions, re-opening
# the clean-room 3S stub-floor collision.
FOREIGN_RULE = ("(rule pad_rescue_stubs\n"
                "  (condition \"A.insideArea('pad_rescue_stubs') "
                "&& (A.NetName == '5V')\")\n"
                "  (constraint track_width (min 0.300mm)))\n")

#: a permissive rule area, the shape `route_and_stitch_generic._add_rule_area`
#: saves. Injected as TEXT so the fixture needs no pcbnew.
RULE_AREA = """	(zone
		(layers "F.Cu" "B.Cu")
		(uuid "aaaaaaaa-0000-4000-8000-{tag:012d}")
		(name "{name}")
		(hatch edge 0.5)
		(keepout
			(tracks allowed)
			(vias allowed)
			(pads allowed)
			(copperpour allowed)
			(footprints allowed)
		)
		(polygon
			(pts
				(xy {x0} {y0}) (xy {x1} {y0}) (xy {x1} {y1}) (xy {x0} {y1})
			)
		)
	)
"""


def _first_seg(pcb_text, net):
    """(x0, y0, x1, y1) of the first F.Cu segment carrying `net` — the copper
    the fixture's rule area will be drawn around."""
    import re
    flat = re.sub(r"\s+", " ", pcb_text)
    m = re.search(r"\(segment \(start ([\d.-]+) ([\d.-]+)\) \(end ([\d.-]+) "
                  r"([\d.-]+)\) \(width [\d.]+\) \(layer \"F\.Cu\"\) "
                  r"\(net \"" + net + r"\"\)", flat)
    check(m is not None, f"fixture board has no F.Cu {net} segment to wrap")
    return tuple(float(m.group(i)) for i in (1, 2, 3, 4))


def foreign_retirement_project(box):
    """Scratch cook-loadcell WITH its board, driven through the real rebuild
    order: generate_rules (step 5) -> stitch appends its exemption (step 8) ->
    generate_rules LAST (step 9). `box` is the rule area to inject, or None for
    "no rule area at all". Returns (dru text, step-9 stdout)."""
    d = tmpdir("grretire_")
    proj = project_copy("cook-loadcell", d / "proj",
                        board=LC / "04_kicad" / "cook_loadcell.kicad_pcb")
    shutil.copy(LC / "04_kicad" / "cook_loadcell.kicad_pro", proj / "04_kicad")
    pcb = proj / "04_kicad" / "cook_loadcell.kicad_pcb"
    dru = proj / "04_kicad" / "cook_loadcell.kicad_dru"
    must_pass(run([PY, GEN_RULES, proj]), "generate_rules_generic (step 5)")
    if box is not None:
        txt = pcb.read_text(encoding="utf-8-sig").rstrip()
        check(txt.endswith(")"), "board file does not end in a close paren")
        pcb.write_text(txt[:-1] + RULE_AREA.format(
            name="pad_rescue_stubs", tag=1,
            x0=box[0], y0=box[1], x1=box[2], y1=box[3]) + ")\n")
    dru.write_text(dru.read_text().rstrip() + "\n" + FOREIGN_RULE)
    r = must_pass(run([PY, GEN_RULES, proj]), "generate_rules_generic (step 9)")
    return dru.read_text(), r.out


@test("generate_rules KEEPS a preserved rule whose insideArea still has "
      "members — the exemption a blanket delete would drop", kind="known_bad")
def t_foreign_rule_with_members_is_kept():
    """FIXTURE A, and the one that constrains the FIX rather than the defect.
    The rule area is drawn around a real F.Cu `5V` segment, so the rule has a
    subject and must survive step 9 exactly as before.

    RED-VERIFIED against the obvious wrong fix. Retiring `pad_rescue_stubs`
    wherever it looks stale — a blanket delete, or a membership test that
    ignores the area and only asks whether the pass re-ran — passes the two
    retirement tests below and FAILS here, which is the whole point: on the
    2026-07-31 fleet that fix would have dropped four live exemptions
    (377/44/41/5 members) and re-opened the stub-floor collision preservation
    exists to prevent. Confirmed by replacing `members()`'s body with
    `return 0`: this test goes RED, the two below stay green."""
    x0, y0, x1, y1 = _first_seg(
        (LC / "04_kicad" / "cook_loadcell.kicad_pcb").read_text(
            encoding="utf-8-sig"), "5V")
    txt, out = foreign_retirement_project(
        (min(x0, x1) - 0.5, min(y0, y1) - 0.5,
         max(x0, x1) + 0.5, max(y0, y1) + 0.5))
    contains(txt, "(rule pad_rescue_stubs", "live foreign rule was dropped")
    contains(out, "board item(s) still match it, kept",
             "the KEEP decision must be spoken, with its count")
    check("RETIRED" not in out, f"nothing may be retired here:\n{out}")
    # still LAST, so KiCad last-match precedence keeps the exemption winning
    check(txt.index("pad_rescue_stubs") > txt.index("BRIDGE"),
          "kept rule must still be emitted after the netclass rules")


@test("generate_rules RETIRES a preserved rule whose rule area survives on the "
      "board but is EMPTY — the case name-existence cannot see", kind="known_bad")
def t_foreign_rule_with_empty_area_is_retired():
    """FIXTURE B, the sharp one. The rule area IS on the board, so every name in
    the condition resolves and `rules_audit`'s A-FIRE and `gate_contract_audit`'s
    dead-name check both pass it. It is still dead: the area is drawn over bare
    laminate at (5,5)-(8,8), outside the fixture board's copper bbox
    (22.7-64.7 x 21.9-62.2 mm), so ZERO items match and DRC reports nothing for
    it by construction.

    RED against the pre-2026-07-31 emitter, whose `foreign_dru_rules` returned
    every unowned rule unconditionally — swap that one-line comprehension back
    in and the rule survives, this assertion fails."""
    txt, out = foreign_retirement_project((5.0, 5.0, 8.0, 8.0))
    check("(rule pad_rescue_stubs" not in txt,
          f"vacuous foreign rule survived the rewrite:\n{txt}")
    contains(out, "RETIRED foreign rule 'pad_rescue_stubs'",
             "the retirement must be spoken, not silent")
    contains(out, "0 board items match its condition",
             "the count that justified the retirement must be printed")
    contains(txt, "A.NetClass == 'BRIDGE'", "netclass rules still regenerated")


@test("generate_rules RETIRES a preserved rule whose rule area is gone from the "
      "board entirely — the fleet's own two instances", kind="known_bad")
def t_foreign_rule_with_no_area_is_retired():
    """The shape crow-mic-pod-v2 and programmable-usb2-hub are actually in on
    2026-07-31: `pad_rescue` is configured in `03_src/route.yaml` and stitch
    served every plane pad with a via-in-pad barrel, so `_scope_stub_floor`
    emitted no boxes and saved no rule area — while the `.kicad_dru` rule from
    an earlier run rode along on every rebuild. Same RED as above."""
    txt, out = foreign_retirement_project(None)
    check("(rule pad_rescue_stubs" not in txt,
          f"foreign rule with no rule area survived:\n{txt}")
    contains(out, "RETIRED foreign rule 'pad_rescue_stubs'", "spoken retirement")


@test("a preserved rule the emitter cannot fully evaluate is KEPT, and says so "
      "— retirement needs a positively derived zero")
def t_foreign_rule_not_derivable_is_kept():
    """The safety direction. `dru_subject.members` returns None rather than 0
    for anything past its model — here a `clearance` constraint, whose subjects
    include pads and courtyards that a text parse of the board would have to
    reconstruct a footprint transform to place. Under-retiring leaves a dead
    rule that `gate_contract_audit --dru` still grades; over-retiring silently
    deletes a live exemption, and only one of those is recoverable."""
    d = tmpdir("grnoderiv_")
    proj = project_copy("cook-loadcell", d / "proj",
                        board=LC / "04_kicad" / "cook_loadcell.kicad_pcb")
    shutil.copy(LC / "04_kicad" / "cook_loadcell.kicad_pro", proj / "04_kicad")
    dru = proj / "04_kicad" / "cook_loadcell.kicad_dru"
    must_pass(run([PY, GEN_RULES, proj]), "generate_rules_generic (step 5)")
    dru.write_text(dru.read_text().rstrip() + "\n"
                   "(rule hand_barrier\n"
                   "  (condition \"A.insideArea('nowhere_at_all')\")\n"
                   "  (constraint clearance (min 2.0mm)))\n")
    r = must_pass(run([PY, GEN_RULES, proj]), "generate_rules_generic (step 9)")
    contains(dru.read_text(), "(rule hand_barrier",
             "an underivable rule must be KEPT")
    contains(r.out, "NOT DERIVABLE", "the emitter must say why it kept it")


def generic_rules_project(mutate=None):
    """A scratch cook-loadcell driven by the SHARED emitter (fab_tier:
    jlc_2layer_default is declared in its nets.yaml). `mutate` edits the
    nets.yaml spec before generation; returns (proj, Run)."""
    import yaml
    d = tmpdir("grgen_")
    proj = project_copy("cook-loadcell", d / "proj")
    shutil.copy(LC / "04_kicad" / "cook_loadcell.kicad_pro", proj / "04_kicad")
    if mutate:
        p = proj / "03_src" / "rules" / "nets.yaml"
        spec = yaml.safe_load(p.read_text())
        mutate(spec)
        p.write_text(yaml.safe_dump(spec))
    return proj, run([PY, GEN_RULES, proj])


@test("generate_rules_generic PURGES kicad-cli droppings instead of aborting "
      "(the bespoke rmstray, promoted)")
def t_rules_purges_kicadcli_droppings():
    """2026-07-23, crow-rv2: every `kicad-cli pcb drc` / stitch-gate run drops
    a stray `<board>.kicad_pcb.kicad_pro` (+ `.kicad_prl`) beside the board,
    and generate_rules' one-board-file contract then ABORTS the rebuild. The
    board carried a bespoke `rmstray()` purge in its rebuild driver (M8
    two-strike: every fleet driver would need it). Promoted: the shared
    emitter now purges the unambiguous double-extension droppings itself.
    RED-verified test-first: FAILED against the pre-fix emitter with
    '>1 .kicad_pro in ...' before the purge landed."""
    d = tmpdir("grstray_")
    proj = project_copy("cook-loadcell", d / "proj")
    shutil.copy(LC / "04_kicad" / "cook_loadcell.kicad_pro", proj / "04_kicad")
    stray_pro = proj / "04_kicad" / "cook_loadcell.kicad_pcb.kicad_pro"
    stray_prl = proj / "04_kicad" / "cook_loadcell.kicad_pcb.kicad_prl"
    stray_pro.write_text("{}")
    stray_prl.write_text("{}")
    r = must_pass(run([PY, GEN_RULES, proj]),
                  "generate_rules_generic with planted kicad-cli droppings")
    check(not stray_pro.exists() and not stray_prl.exists(),
          "the kicad-cli droppings survived the run")
    contains(r.out, "stray", "purge notice")


@test("generate_rules_generic still ABORTS on a genuine second .kicad_pro "
      "(the purge must not blind the one-board-file contract)", kind="known_bad")
def t_kb_rules_second_pro_still_aborts():
    """The purge is scoped to the double-extension `*.kicad_pcb.kicad_pro`
    droppings ONLY. A real second project file is still ambiguity the
    contract must reject — a gate that cannot fail is worthless."""
    d = tmpdir("grtwo_")
    proj = project_copy("cook-loadcell", d / "proj")
    shutil.copy(LC / "04_kicad" / "cook_loadcell.kicad_pro", proj / "04_kicad")
    (proj / "04_kicad" / "other_board.kicad_pro").write_text("{}")
    must_fail(run([PY, GEN_RULES, proj]),
              "generate_rules_generic with two genuine .kicad_pro", ">1 .kicad_pro")


@test("TIER-AWARE clamp: a declared fab_tier replaces the hardcoded 0.25mm "
      "floor with the tier's real min_track")
def t_tier_clamp_uses_tier_floor():
    """The legacy emitter silently lifted every width to 0.25mm even when the
    declared tier's published floor is 0.127mm — a 0.15mm class was quietly
    routed at 0.25. With fab_tier declared, a legal 0.15mm width must survive
    to the .kicad_dru verbatim."""
    proj, r = generic_rules_project(
        lambda s: s["classes"]["PWR"].update({"min_width": "0.15mm"}))
    must_pass(r, "generate_rules_generic with a sub-0.25 legal width")
    dru = (proj / "04_kicad" / "cook_loadcell.kicad_dru").read_text()
    contains(dru, "(min 0.15mm)", "tier-legal width must not be clamped")


@test("NO tier declared: the historic 0.25mm clamp still applies (legacy)")
def t_tier_clamp_fallback():
    def drop_tier(s):
        s.pop("fab_tier", None)
        s["classes"]["PWR"]["min_width"] = "0.15mm"
    proj, r = generic_rules_project(drop_tier)
    must_pass(r, "generate_rules_generic without a tier")
    dru = (proj / "04_kicad" / "cook_loadcell.kicad_dru").read_text()
    contains(dru, "(min 0.25mm)", "legacy clamp must still lift 0.15 to 0.25")


SF = {"zone": "sw_pour_zone", "nets": ["5V"], "min_width": "0.3mm",
      "why": "sense taps ride the pour-fed trunk inside the island; the "
             "current path is the pour (clean-room 3S append_sw_floor)"}


@test("scoped_floors emits a last-match insideArea relaxation, net-scoped, "
      "idempotent across the rules-LAST rerun")
def t_scoped_floors_emitted():
    """The clean-room 3S board hand-appended this exact rule with a bespoke
    append_sw_floor.py (canon M8 second strike after cook-hub's u7_taps);
    it is now nets.yaml config."""
    proj, r = generic_rules_project(
        lambda s: s.update({"scoped_floors": [dict(SF)]}))
    must_pass(r, "generate_rules_generic with scoped_floors")
    dru_p = proj / "04_kicad" / "cook_loadcell.kicad_dru"
    txt = dru_p.read_text()
    contains(txt, "A.insideArea('sw_pour_zone')", "scoped rule condition")
    contains(txt, "A.NetName == '5V'", "net scope clause")
    contains(txt, "(min 0.3mm)", "relaxed floor")
    # last-match precedence: the relaxation must come AFTER the netclass rules
    check(txt.index("scoped_sw_pour_zone") > txt.index("PWR_width"),
          "scoped floor must be emitted after the netclass floors")
    # rules-LAST rerun must not duplicate it through foreign-rule preservation
    must_pass(run([PY, GEN_RULES, proj]), "generate_rules_generic rerun")
    eq(dru_p.read_text().count("scoped_sw_pour_zone"), 1,
       "scoped floor duplicated on rerun")


DP = {"width": 0.2, "gap": 0.2, "max_uncoupled": 5}  # fixture tier jlc_2layer_default: min_track 0.127


@test("a class `diff_pair:` emits netclass dims + an ACTIVE .kicad_dru "
      "diff_pair_gap rule + board diff_pair_dimensions")
def t_diff_pair_emitted():
    """External review F2 (crow-recorder-central-v2 v1.0, 2026-07-24): USB-HS
    90ohm was neither constrained nor demonstrated — diff_pair_dimensions sat
    [] and no gap rule existed, so DRC gated nothing. The diff_pair key must
    land in all three places or it is documentation, not a rule.
    RED-verified against the pre-fix emitter (git stash 2026-07-24): old code
    exits 0, emits diff_pair_gap 0.25 hardcode, no _diffpair rule, no
    diff_pair_dimensions."""
    proj, r = generic_rules_project(
        lambda s: s["classes"]["PWR"].update({"diff_pair": dict(DP)}))
    must_pass(r, "generate_rules_generic with a diff_pair class")
    txt = (proj / "04_kicad" / "cook_loadcell.kicad_dru").read_text()
    contains(txt, "PWR_diffpair", "diff-pair rule emitted")
    contains(txt, "diff_pair_gap (min 0.195mm) (opt 0.2mm)", "gap constraint")
    contains(txt, "diff_pair_uncoupled (max 5", "uncoupled cap")
    pro = json.loads((proj / "04_kicad" / "cook_loadcell.kicad_pro").read_text())
    dims = pro["board"]["design_settings"]["diff_pair_dimensions"]
    eq(dims, [{"gap": 0.2, "via_gap": 0.2, "width": 0.2}],
       "board diff_pair_dimensions")
    cls = {c["name"]: c for c in pro["net_settings"]["classes"]}
    eq(cls["PWR"]["diff_pair_gap"], 0.2, "netclass diff_pair_gap")
    eq(cls["PWR"]["diff_pair_width"], 0.2, "netclass diff_pair_width")


@test("a diff_pair with no `gap` is a generation error (an unenforced pair "
      "gates nothing)", kind="known_bad")
def t_kb_diff_pair_no_gap():
    bad = {k: v for k, v in DP.items() if k != "gap"}
    proj, r = generic_rules_project(
        lambda s: s["classes"]["PWR"].update({"diff_pair": bad}))
    must_fail(r, "diff_pair without gap", "gap")


@test("a diff_pair gap below the tier's min_space FAILS naming the tier",
      kind="known_bad")
def t_kb_diff_pair_gap_below_tier():
    proj, r = generic_rules_project(
        lambda s: s["classes"]["PWR"].update(
            {"diff_pair": dict(DP, gap=0.05)}))
    must_fail(r, "diff_pair gap below tier min_space", "min_space")


@test("a scoped_floors entry with no `why` is a generation error (canon M4)",
      kind="known_bad")
def t_kb_scoped_floor_no_why():
    """A floor relaxation copied without its evidence is an inherited defect
    — the waiver-provenance incident (canon M4), applied at generation time."""
    bad = {k: v for k, v in SF.items() if k != "why"}
    proj, r = generic_rules_project(
        lambda s: s.update({"scoped_floors": [bad]}))
    must_fail(r, "scoped floor without evidence", "why")
    contains(r.out, "M4", "the error must cite the evidence canon")


@test("a scoped_floors min_width below the tier's min_track FAILS naming "
      "the tier", kind="known_bad")
def t_kb_scoped_floor_below_tier():
    """scoped_floors may relax a NETCLASS floor, never the FAB's: no scope
    makes a 0.1mm track manufacturable at a 0.127mm-min_track tier."""
    proj, r = generic_rules_project(
        lambda s: s.update({"scoped_floors": [dict(SF, min_width="0.1mm")]}))
    must_fail(r, "scoped floor below the fab floor", "jlc_2layer_default")


# --------------------------------------------------- scoped CLEARANCES
# pluto-rx2-8way, 2026-07-30: routed, promoted, 88/28/0 — and 49 of the 88 are
# ONE missing capability. A 0.36mm RF arm cannot leave the PE42482A-X land at
# the board's 0.2mm clearance (MEASURED on a 20-point width x clearance sweep:
# 0.145 routes 11/11, 0.15 routes 6/11), so the wave routes at 0.14 and the
# copper lands 0.166..0.194mm from GND. The board declares 0.2 UP from the
# 0.09 tier floor deliberately — on it clearance is ISOLATION — so the answer
# is a LAUNCH-LOCAL scoped clearance, the exact parallel of scoped_floors'
# width relaxation, which the emitter could not say.
SC = {"zone": "rf_launch", "nets": ["5V"], "clearance": "0.14mm",
      "why": "measured 2026-07-30 (20-point sweep on r0): a 0.36mm arm cannot "
             "leave the PE42482A-X land at 0.2mm — 0.145 routes 11/11, 0.15 "
             "routes 6/11; the wave routes at 0.14 so the DRC floor must not "
             "sit above the router's own budget"}


@test("scoped_clearances emits a BOUNDED last-match clearance relaxation "
      "(both items inside the area, one side on a named net), idempotent "
      "across the rules-LAST rerun")
def t_scoped_clearances_emitted():
    """RED-VERIFIED against the pre-fix emitter, measured 2026-07-30: the key
    is IGNORED — generate_rules_generic exits 0, prints its usual
    `2 netclasses + 10 patterns -> cook_loadcell.kicad_pro; 2 width rules ->
    cook_loadcell.kicad_dru` line, and the
    .kicad_dru contains no `scoped_clr_` rule and no `clearance` constraint at
    all, because `scoped_floors` was emitted as `track_width` ONLY."""
    proj, r = generic_rules_project(
        lambda s: s.update({"scoped_clearances": [dict(SC)]}))
    must_pass(r, "generate_rules_generic with scoped_clearances")
    dru_p = proj / "04_kicad" / "cook_loadcell.kicad_dru"
    txt = dru_p.read_text()
    contains(txt, "scoped_clr_rf_launch", "the scoped clearance rule")
    contains(txt, "(constraint clearance (min 0.14mm))",
             "a CLEARANCE constraint, not a track_width one")
    # BOUNDED: both items must be in the area, or the relaxation leaks to a
    # pair whose second item is anywhere on the board
    contains(txt, "A.insideArea('rf_launch') && B.insideArea('rf_launch')",
             "both sides bounded to the region")
    # symmetric net clause: the relaxed net may be either side of the pair
    contains(txt, "A.NetName == '5V' || B.NetName == '5V'",
             "the named net on either side of the pair")
    # last-match precedence, and the netclass width floors are untouched
    check(txt.index("scoped_clr_rf_launch") > txt.index("PWR_width"),
          "scoped clearance must be emitted after the netclass rules")
    contains(txt, "(min 0.4mm)", "netclass width floors are unchanged")
    must_pass(run([PY, GEN_RULES, proj]), "generate_rules_generic rerun")
    eq(dru_p.read_text().count("scoped_clr_rf_launch"), 1,
       "scoped clearance duplicated on rerun")


@test("a scoped_clearances entry with no `why` is a generation error — an "
      "isolation relaxation with no evidence has NO other gate behind it",
      kind="known_bad")
def t_kb_scoped_clearance_no_why():
    """`why` is REQUIRED here for a STRONGER reason than on scoped_floors: a
    width relaxation is still bounded below by ampacity, which A-AMP grades
    independently from `current:`, so a bad one has a second reader. A
    clearance relaxation has NO downstream grader at all — DRC simply stops
    reporting what the rule permits, and the board that needs one
    (pluto-rx2-8way) sells ISOLATION between nine arms. Silent is exactly the
    failure mode. RED-VERIFIED: pre-fix the key is ignored and the emitter
    exits 0 (measured 2026-07-30)."""
    bad = {k: v for k, v in SC.items() if k != "why"}
    proj, r = generic_rules_project(
        lambda s: s.update({"scoped_clearances": [bad]}))
    must_fail(r, "scoped clearance without evidence", "why")
    contains(r.out, "M4", "the error must cite the evidence canon")
    contains(r.out, "ISOLATION", "and name what is being relaxed")


@test("a scoped_clearances entry with no `nets` is a generation error — "
      "isolation is a property of a PAIR, and 'everything in this box' is "
      "not an isolation argument", kind="known_bad")
def t_kb_scoped_clearance_no_nets():
    """Unlike scoped_floors, where `nets` is optional (a width floor with no
    net scope still only lowers a width), an unscoped clearance relaxation
    licenses EVERY pair inside the area — including pairs the author never
    considered. RED-VERIFIED: pre-fix, exit 0 (2026-07-30)."""
    bad = {k: v for k, v in SC.items() if k != "nets"}
    proj, r = generic_rules_project(
        lambda s: s.update({"scoped_clearances": [bad]}))
    must_fail(r, "scoped clearance with no net scope", "nets")


@test("a scoped_clearances value below the tier's min_space FAILS naming the "
      "tier — a scope relaxes a NETCLASS floor, never the FAB's",
      kind="known_bad")
def t_kb_scoped_clearance_below_tier():
    """0.1mm at jlc_2layer_default (min_space 0.127): no rule area makes an
    unetchable gap etchable. RED-VERIFIED: pre-fix, exit 0 (2026-07-30)."""
    proj, r = generic_rules_project(
        lambda s: s.update({"scoped_clearances": [dict(SC, clearance="0.1mm")]}))
    must_fail(r, "scoped clearance below the fab floor", "jlc_2layer_default")
    contains(r.out, "min_space", "the tier field is named")


@test("a scoped_clearances entry with no `zone` is a generation error "
      "(an unbounded relaxation is a board-wide one)", kind="known_bad")
def t_kb_scoped_clearance_no_zone():
    bad = {k: v for k, v in SC.items() if k != "zone"}
    proj, r = generic_rules_project(
        lambda s: s.update({"scoped_clearances": [bad]}))
    must_fail(r, "scoped clearance with no zone", "zone")


@test("an EXPLICIT class width below the declared tier's min_track FAILS "
      "naming the tier", kind="known_bad")
def t_kb_width_below_tier_floor():
    """Pre-fix, `w = max(w, 0.25)` silently CLAMPED a 0.1mm width — the board
    routed at a width the config never said. With a declared tier the width is
    physically unmanufacturable and must be a hard error naming the tier.
    RED-verified against the pre-fix emitter (git stash; the old code exits 0
    and emits 0.25mm) — 2026-07-21."""
    proj, r = generic_rules_project(
        lambda s: s["classes"]["PWR"].update({"min_width": "0.1mm"}))
    must_fail(r, "generate_rules_generic on a sub-tier-floor width",
              "jlc_2layer_default")
    contains(r.out, "min_track", "the failure must cite the tier floor")


@test("default_clearance below the tier's min_space FAILS naming the tier",
      kind="known_bad")
def t_kb_default_clearance_below_tier_floor():
    """`default_clearance:` (2026-07-23) lets a board route the whole surface at
    the tier's real min_space (e.g. 0.15mm on JLC 2-layer, 6mil) instead of the
    conservative 0.2mm baked Default-netclass clearance — crow-mic-pod-v2's RJ45
    south-contact escape needed it. A value BELOW the tier's min_space is
    unmanufacturable and must be a hard error naming the tier, not a silent
    accept. RED-verified against the pre-fix emitter, which ignored the key
    entirely and exited 0 — 2026-07-23."""
    proj, r = generic_rules_project(
        lambda s: s.update({"default_clearance": 0.05}))
    must_fail(r, "generate_rules_generic on a sub-tier default_clearance",
              "jlc_2layer_default")
    contains(r.out, "min_space", "the failure must cite the tier's min_space floor")


@test("default_clearance/default_track_width accept an 'mm'-suffixed STRING "
      "(mm() unit-strip), not just a bare float")
def t_default_overrides_mm_string():
    """Every other width in nets.yaml is written as an 'mm'-suffixed string
    (the classes[].min_width convention, which already flows through mm()).
    The Default-class default_clearance/default_track_width overrides
    (2026-07-23) went through float() directly, so a board that spelled them
    the SAME '0.15mm' way crashed the emitter with a ValueError before it could
    emit anything. mm() unit-strips them. GREEN: a legal '0.15mm' pair is parsed
    to 0.15 and reaches the Default netclass in the .kicad_pro. RED-verified
    against the pre-mm() emitter (HEAD), where float('0.15mm') raised and the
    run exited nonzero — 2026-07-23."""
    proj, r = generic_rules_project(
        lambda s: s.update({"default_clearance": "0.15mm",
                            "default_track_width": "0.15mm"}))
    must_pass(r, "generate_rules_generic with mm-suffixed Default overrides")
    pro = json.loads((proj / "04_kicad" / "cook_loadcell.kicad_pro").read_text())
    dfl = [c for c in pro["net_settings"]["classes"] if c["name"] == "Default"][0]
    check(abs(dfl.get("clearance", -1) - 0.15) < 1e-9,
          f"default_clearance not parsed from '0.15mm': {dfl.get('clearance')}")
    check(abs(dfl.get("track_width", -1) - 0.15) < 1e-9,
          f"default_track_width not parsed from '0.15mm': {dfl.get('track_width')}")


@test("a TYPO'd fab_tier is a hard error, not silently no-tier",
      kind="known_bad")
def t_kb_tier_typo():
    """A typo'd tier silently disabling every capability floor is the failure
    mode tier-derived defaults exist to stop."""
    proj, r = generic_rules_project(
        lambda s: s.update({"fab_tier": "jlc_2layer_defualt"}))
    must_fail(r, "generate_rules_generic on a typo'd tier", "jlc_2layer_defualt")


# ------------------------------------------------------- known-bad cases
@test("rules_audit FAILS when a declared current exceeds its width (ampacity)",
      kind="known_bad")
def t_ampacity_floor():
    """`current: 5A` with `min_width: 0.2mm`. generate_rules happily emits a
    0.25mm netclass and exits 0 — nothing read `current:` before this gate."""
    proj = rules_project()
    set_nets_yaml(proj, lambda s: s["classes"]["PWR"].update(
        {"current": "5A", "min_width": "0.2mm"}))
    r = run([PY, RULES_AUDIT, proj])
    must_fail(r, "rules_audit on an undersized power net", "A-AMP PWR")
    contains(r.out, "carries 5.0A", "ampacity failure detail")


@test("rules_audit FAILS on a current it cannot read (A-AMP was silent)",
      kind="known_bad")
def t_kb_ampacity_unreadable_is_a_fail():
    """THE SILENCER. `parse_amps` returned a bare None for BOTH "absent" and
    "present but unparseable", and the caller filed None under OKS as
    "n/a (no current: declared)". Measured 2026-07-27: that message was wrong
    100% of the times it fired, because ZERO net classes fleet-wide declare no
    current — every None was a real value the gate could not read. A-AMP graded
    10 of 57 declared currents; usb-hub-3s-v3's PWR_IN 7 A, PWR_RAIL 6 A and
    SWITCH_NODE 7 A were all silenced by the qualifier alone, and the single
    class it did grade FAILED.

    RED-verified: restoring the old one-line `parse_amps` makes this fixture
    PASS, which is the bug.
    """
    proj = rules_project()
    set_nets_yaml(proj, lambda s: s["classes"]["PWR"].update(
        {"current": "uA-level sense", "min_width": "0.2mm"}))
    r = run([PY, RULES_AUDIT, proj])
    must_fail(r, "rules_audit on an unreadable current", "A-AMP PWR")
    contains(r.out, "NEVER CHECKED", "the failure names the real consequence")


@test("rules_audit reads a QUALIFIED current instead of discarding it")
def t_ampacity_qualified_prose_is_parsed():
    """"7 A worst case" is the real fleet spelling. The old parser lowercased
    and stripped every letter 'a' anywhere, turning it into "7  worst cse"."""
    proj = rules_project()
    set_nets_yaml(proj, lambda s: s["classes"]["PWR"].update(
        {"current": "7 A worst case", "min_width": "0.2mm"}))
    r = run([PY, RULES_AUDIT, proj])
    must_fail(r, "rules_audit on 7 A over 0.2mm", "A-AMP PWR")
    contains(r.out, "carries 7.0A", "the qualified magnitude is read")


@test("rules_audit accepts an EXPLICIT signal exemption")
def t_ampacity_signal_exemption():
    """A class with no ampacity obligation must SAY so. Silence is not a
    declaration, and it is now distinguishable from an unreadable value."""
    proj = rules_project()
    set_nets_yaml(proj, lambda s: s["classes"]["PWR"].update(
        {"current": "signal", "min_width": "0.3mm"}))
    r = run([PY, RULES_AUDIT, proj])
    must_pass(r, "rules_audit on a declared-signal class")
    contains(r.out, "exempt by declaration", "the exemption is explicit")


@test("rules_audit reports A-AMP COVERAGE, not just a verdict")
def t_ampacity_reports_coverage():
    """Canon M-COVER. 47 of 57 declarations were silently ungraded and nobody
    could see it, because nothing ever printed a ratio."""
    proj = rules_project()
    r = run([PY, RULES_AUDIT, proj])
    contains(r.out, "coverage A-AMP:", "A-AMP declares its denominator")


@test("rules_audit REFUSES a pour_fed waiver with no evidence", kind="known_bad")
def t_kb_pour_fed_without_evidence():
    """A-AMP measures the narrowest TRACK, but a plane-fed net does not conduct
    through a track — on such a class the metric is adjacent to the property.
    That is excusable only by a DECLARED, EVIDENCED exemption; a bare
    `pour_fed: true` is a rationale, and canon M4 wants evidence."""
    proj = rules_project()
    set_nets_yaml(proj, lambda s: s["classes"]["PWR"].update(
        {"current": "7 A worst case", "min_width": "0.2mm", "pour_fed": True}))
    r = run([PY, RULES_AUDIT, proj])
    must_fail(r, "rules_audit on a bare pour_fed", "no evidence")


@test("rules_audit accepts pour_fed WITH the measurement")
def t_pour_fed_with_evidence():
    proj = rules_project()
    set_nets_yaml(proj, lambda s: s["classes"]["PWR"].update(
        {"current": "7 A worst case", "min_width": "0.3mm",
         "pour_fed": "F.Cu+B.Cu pour, 10403.45 mm2 measured; tracks are taps"}))
    r = run([PY, RULES_AUDIT, proj])
    must_pass(r, "rules_audit on an evidenced pour_fed class")
    contains(r.out, "carried by POUR", "the exemption names its mechanism")


@test("rules_audit FAILS when .kicad_pro and .kicad_dru disagree on width",
      kind="known_bad")
def t_pro_dru_disagree():
    """generate_rules clamps the netclass to max(min_width, 0.25) but writes
    the RAW min_width into the DRU. `0.1mm` therefore produces a 0.25mm
    netclass and a 0.10mm DRC floor — router and DRC enforce different
    numbers and nothing noticed."""
    proj = rules_project()
    set_nets_yaml(proj, lambda s: s["classes"]["PWR"].update({"min_width": "0.1mm"}))
    r = run([PY, RULES_AUDIT, proj])
    must_fail(r, "rules_audit on a pro/dru width disagreement", "A-AGREE PWR")


@test("rules_audit FAILS when a class's nets never get a netclass pattern",
      kind="known_bad")
def t_unpatterned_net():
    """A net listed under a class but absent from netclass_patterns routes
    as Default — the rule exists on paper and nowhere in KiCad."""
    proj = rules_project()
    pro_p = proj / "04_kicad" / "cook_loadcell.kicad_pro"
    pro = json.loads(pro_p.read_text())
    pro["net_settings"]["netclass_patterns"] = [
        e for e in pro["net_settings"]["netclass_patterns"] if e["pattern"] != "E_PLUS"]
    pro_p.write_text(json.dumps(pro, indent=2))
    r = run([PY, RULES_AUDIT, proj])
    must_fail(r, "rules_audit with an unpatterned net", "A-CLASS BRIDGE")
    contains(r.out, "'E_PLUS'", "the dropped net should be named")


def write_board(proj, areas=()):
    """A minimal .kicad_pcb carrying exactly the named zones. A-FIRE reads
    board TEXT (it needs no pcbnew), so the fixture can state the one fact
    under test — which rule areas exist — and nothing else."""
    zones = "".join(
        f'\n\t(zone\n\t\t(layers "F.Cu")\n\t\t(name "{n}")\n'
        f'\t\t(keepout\n\t\t\t(tracks not_allowed)\n\t\t)\n\t)' for n in areas)
    p = proj / "04_kicad" / "fixture.kicad_pcb"
    p.write_text('(kicad_pcb (version 20241229) (generator "test")' + zones + "\n)\n")
    return p


# ------------------------------------------------------------- A-FIRE
# "a gate that cannot fail is worthless" applied to the DRU itself: a rule
# whose condition can never be true reads as enforcement and enforces nothing.
# Both fixtures below are the SEALED shapes, measured 2026-07-25 —
# crow-mic-pod-v2 v1.0 shipped one of each in the same .kicad_dru.

@test("rules_audit PASSES a DRU whose every rule can fire")
def t_fire_clean():
    proj = rules_project()
    r = run([PY, RULES_AUDIT, proj])
    contains(r.out, "A-FIRE all", "A-FIRE should report on a clean DRU")
    check("FAIL  A-FIRE" not in r.out, f"A-FIRE false positive:\n{r.out}")


@test("rules_audit FAILS on a DRU rule conditioning on a netclass that does "
      "not exist (crow-mic-pod-v2 v1.0 'AUDIO_width')", kind="known_bad")
def t_kb_fire_dead_netclass():
    """The sealed shape. nets.yaml DROPPED the AUDIO class (its 0.25mm floor
    collided with KRT's 0.2498mm imported width) but the generated DRU kept
    the AUDIO_width rule. The board then carried 3 tracks at 0.2498mm —
    0.0002mm under the floor that rule names — and DRC reported 0.

    Every OTHER check in rules_audit iterates over the classes nets.yaml
    declares, so a rule naming a dropped class was graded by nothing."""
    proj = rules_project()
    dru = next(iter((proj / "04_kicad").glob("*.kicad_dru")))
    dru.write_text(dru.read_text() + "\n(rule \"AUDIO_width\"\n"
                   "  (condition \"A.NetClass == 'AUDIO'\")\n"
                   "  (constraint track_width (min 0.25mm)))\n")
    r = run([PY, RULES_AUDIT, proj])
    must_fail(r, "rules_audit on a DRU rule naming a nonexistent netclass",
              "A-FIRE")
    contains(r.out, "'AUDIO'", "the dead netclass should be named")
    contains(r.out, "CANNOT FIRE", "the finding should say why it matters")
    # RED-VERIFY: the finding comes from A-FIRE and nothing else
    r2 = run([PY, RULES_AUDIT, proj, "--_disable-fire"])
    must_pass(r2, "the same fixture with A-FIRE disabled")


@test("rules_audit FAILS on a DRU rule conditioning on a rule area absent "
      "from the board (the fleet's 'pad_rescue_stubs')", kind="known_bad")
def t_kb_fire_dead_area():
    """Measured on three sealed boards: crow-mic-pod-v2 v1.0, usb-hub-3s and
    usb-hub-3s-v2 all ship an insideArea('pad_rescue_stubs') rule with no
    such rule area on the board. usb-hub-3s-v3 has the area and passes, so
    the check discriminates rather than flagging the name."""
    proj = rules_project()
    dru = next(iter((proj / "04_kicad").glob("*.kicad_dru")))
    dru.write_text(dru.read_text() + "\n(rule pad_rescue_stubs\n"
                   "  (condition \"A.insideArea('pad_rescue_stubs') && "
                   "(A.NetName == 'GND')\")\n"
                   "  (constraint track_width (min 0.300mm)))\n")
    write_board(proj, areas=["some_other_area"])
    r = run([PY, RULES_AUDIT, proj])
    must_fail(r, "rules_audit on a DRU rule naming an absent rule area",
              "A-FIRE")
    contains(r.out, "pad_rescue_stubs", "the dead area should be named")
    r2 = run([PY, RULES_AUDIT, proj, "--_disable-fire"])
    must_pass(r2, "the same fixture with A-FIRE disabled")


@test("A-FIRE resolves insideArea() against real rule areas, so a LIVE area "
      "rule passes")
def t_fire_live_area():
    """Discrimination, not name-matching: the same rule text that FAILS in
    t_kb_fire_dead_area PASSES once the board actually carries the area."""
    proj = rules_project()
    dru = next(iter((proj / "04_kicad").glob("*.kicad_dru")))
    dru.write_text(dru.read_text() + "\n(rule stubs\n"
                   "  (condition \"A.insideArea('my_area')\")\n"
                   "  (constraint track_width (min 0.300mm)))\n")
    write_board(proj, areas=["my_area"])
    r = run([PY, RULES_AUDIT, proj])
    check("A-FIRE" not in r.out or "FAIL  A-FIRE" not in r.out,
          f"A-FIRE flagged a rule area that IS on the board:\n{r.out}")


@test("rules_audit sees generate_rules_generic.py, not just generate_rules.py")
def t_order_generic_backend():
    """A-ORDER's pattern matched only `generate_rules.py`, so every
    generic-backend board got 'the DRC gate runs with no generate_rules.py
    before it' while its rebuild_all.sh was in fact correct. A false positive
    that trains readers to ignore the check is how the REAL ordering defect
    would get through (measured on crow-mic-pod-v2, 2026-07-25)."""
    sys.path.insert(0, str(SCRIPTS))
    import importlib
    ra = importlib.import_module("rules_audit")
    d = tmpdir("order_")
    good = d / "rebuild_ok.sh"
    good.write_text("#!/bin/sh\n$PY $SK/generate_rules_generic.py .\n"
                    "kicad-cli pcb drc --severity-all b.kicad_pcb\n")
    eq(ra.rebuild_order_fails(good), [],
       "the generic generator running last must satisfy A-ORDER")
    bad = d / "rebuild_bad.sh"
    bad.write_text("#!/bin/sh\n$PY $SK/generate_rules_generic.py .\n"
                   "$PY 03_src/stitch.py\n"
                   "kicad-cli pcb drc --severity-all b.kicad_pcb\n")
    check(ra.rebuild_order_fails(bad),
          "a board-writing step after the generic generator must still FAIL")


@test("rules_audit FAILS when generate_rules never ran", kind="known_bad")
def t_rules_not_run():
    d = tmpdir("rules_")
    proj = project_copy("cook-loadcell", d / "proj")
    (proj / "04_kicad").mkdir(exist_ok=True)
    # a bare project file with only the Default class
    (proj / "04_kicad" / "cook_loadcell.kicad_pro").write_text(json.dumps(
        {"net_settings": {"classes": [{"name": "Default", "track_width": 0.25}],
                          "netclass_patterns": []}}))
    r = run([PY, RULES_AUDIT, proj])
    must_fail(r, "rules_audit on an ungenerated project", "A-CLASS")


# ----------------------------------------------------------------- BOM
@test("bom_seed resolves a fully mapped BOM")
def t_bom_clean():
    d = tmpdir("bom_")
    proj = project_copy("cook-loadcell", d / "proj")
    fab = proj / "06_build" / "fab"
    fab.mkdir(parents=True, exist_ok=True)
    shutil.copy(LC / "06_build" / "fab" / "bom_jlc.csv", fab)
    r = must_pass(run([KPY, "03_src/bom_seed.py"], cwd=proj), "bom_seed clean")
    txt = (fab / "bom_jlc.csv").read_text()
    check("LCSC" in txt.splitlines()[0], "bom_seed dropped the LCSC column")


@test("bom_seed FAILS loudly on an unmapped BOM line", kind="known_bad")
def t_bom_unmapped():
    """A part nobody taught it about must stop the fab package, not sail
    through with a blank LCSC code."""
    d = tmpdir("bom_")
    proj = project_copy("cook-loadcell", d / "proj")
    fab = proj / "06_build" / "fab"
    fab.mkdir(parents=True, exist_ok=True)
    src = (LC / "06_build" / "fab" / "bom_jlc.csv").read_text().splitlines()
    hdr = src[0]
    ncol = len(hdr.split(","))
    row = ["47u bulk", "C99", "C_1206_3216Metric"] + [""] * (ncol - 3)
    (fab / "bom_jlc.csv").write_text("\n".join(src + [",".join(row)]) + "\n")
    r = run([KPY, "03_src/bom_seed.py"], cwd=proj)
    must_fail(r, "bom_seed on an unmapped line", "UNRESOLVED BOM LINES")
    contains(r.out, "C99", "the unmapped designator should be named")


@test("bom_seed FAILS when the fab BOM has not been exported", kind="known_bad")
def t_bom_missing():
    d = tmpdir("bom_")
    proj = project_copy("cook-loadcell", d / "proj")
    r = run([KPY, "03_src/bom_seed.py"], cwd=proj)
    must_fail(r, "bom_seed with no BOM at all", "missing")


if __name__ == "__main__":
    sys.exit(main())
