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
LC = ROOT / "projects" / "cook-loadcell"
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
    (which drops the rule) — 2026-07-20."""
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
