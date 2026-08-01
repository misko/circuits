#!/usr/bin/env python3
"""T1: P-MOD module-first architecture selection contract."""
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, SCRIPTS, check, contains, eq, main, must_fail,  # noqa: E402
                     must_pass, run, test, tmpdir)

GATE = SCRIPTS / "module_first_check.py"
REPO = Path(__file__).resolve().parents[1]


def project(part_type="microcontroller", style="qfn", *, config=True):
    root = tmpdir("t1mod_")
    (root / "02_parts/CTRL").mkdir(parents=True)
    (root / "03_src/rules").mkdir(parents=True)
    (root / "01_docs/decisions").mkdir(parents=True)
    (root / "02_parts/CTRL/part.yaml").write_text(yaml.safe_dump({
        "mpn": "CTRL", "type": part_type,
        "escape": {"style": style, "pitch": 0.5,
                   "tier_required": "jlc_4layer_advanced"},
    }, sort_keys=False))
    if config:
        write_policy(root, [{
            "function": "host control", "part": "CTRL",
            "implementation": "module" if style == "module" else "bare_ic",
            "rationale": "The selected implementation satisfies the locked requirements.",
        }])
    return root


def write_policy(root, selections=None, **extra):
    doc = {"schema": 1, "default": "prefer_module"}
    if selections is not None:
        doc["selections"] = selections
    doc.update(extra)
    (root / "03_src/rules/integration.yaml").write_text(
        yaml.safe_dump(doc, sort_keys=False))


def exception(root):
    adr = root / "01_docs/decisions/0001-bare-controller.md"
    adr.write_text("# Bare controller exception\n\nModules cannot expose the required bus.\n")
    return {
        "binding_requirement": "Expose sixteen synchronous GPIO at the required edge rate.",
        "evidence": "Measured module pin maps expose at most twelve contiguous GPIO.",
        "modules_considered": [{
            "part": "MODULE-A",
            "rejected_because": "Only twelve GPIO are exposed and four required lines are absent.",
            "evidence": "Vendor pinout revision A, pins 1 through 24, checked 2026-07-31.",
        }],
        "adr": "01_docs/decisions/0001-bare-controller.md",
    }


@test("P-MOD accepts a real module and reports its coverage")
def t_module_green():
    root = project("mcu_module", "module")
    r = must_pass(run([KPY, GATE, root]), "module-first module selection")
    contains(r.out, "P-MOD PASS", "verdict")
    contains(r.out, "1/1", "coverage")


@test("P-MOD permits a bare IC only with a measured exception ADR")
def t_bare_exception_green():
    root = project()
    data = yaml.safe_load((root / "03_src/rules/integration.yaml").read_text())
    data["selections"][0]["exception"] = exception(root)
    write_policy(root, data["selections"])
    must_pass(run([KPY, GATE, root]), "evidenced bare-IC exception")


@test("P-MOD rejects an unexplained bare MCU", kind="known_bad")
def t_bare_without_exception_red():
    root = project()
    must_fail(run([KPY, GATE, root]), "unexplained bare MCU", "exception")


@test("P-MOD rejects calling a bare package a module", kind="known_bad")
def t_false_module_red():
    root = project()
    data = yaml.safe_load((root / "03_src/rules/integration.yaml").read_text())
    data["selections"][0]["implementation"] = "module"
    write_policy(root, data["selections"])
    must_fail(run([KPY, GATE, root]), "false module claim", "not a module")


@test("P-MOD rejects an exception with no measured module comparison",
      kind="known_bad")
def t_thin_exception_red():
    root = project()
    thin = exception(root)
    thin["modules_considered"][0]["evidence"] = "catalog"
    data = yaml.safe_load((root / "03_src/rules/integration.yaml").read_text())
    data["selections"][0]["exception"] = thin
    write_policy(root, data["selections"])
    must_fail(run([KPY, GATE, root]), "thin exception evidence", "evidence")


@test("P-MOD rejects an adopted policy that omits a complex subsystem",
      kind="known_bad")
def t_omitted_controller_red():
    root = project()
    write_policy(root, [])
    must_fail(run([KPY, GATE, root]), "omitted controller", "not selected")


@test("P-MOD accepts an explicit no-applicable-functions declaration")
def t_passive_board_green():
    root = project("passive", "passive")
    write_policy(root, [], no_applicable_functions=(
        "This board is a passive interposer with no programmable, radio, power-"
        "control, interface-control, or complex sensing subsystem."))
    must_pass(run([KPY, GATE, root]), "passive-board declaration")


@test("P-MOD distinguishes a legacy project with no policy from a pass",
      kind="known_bad")
def t_unmigrated_red():
    root = project(config=False)
    r = run([KPY, GATE, root])
    eq(r.rc, 3, "unmigrated exit")
    contains(r.out, "UNMIGRATED", "unmigrated verdict")


@test("P-MOD vacuity is bounded to an unrecognized custom type",
      kind="vacuity", gate="module_first_check.py")
def t_vacuity_custom_type():
    root = project("custom_logic_widget", "qfn")
    write_policy(root, [], no_applicable_functions=(
        "No type in the declared module-first scope is present on this board."))
    must_pass(run([KPY, GATE, root]), "unrecognized compute-like custom type")
    check("custom_logic_widget" not in run([KPY, GATE, root]).out,
          "fixture must reproduce the declared blind spot")


@test("new-project templates adopt and invoke P-MOD before generation")
def t_templates_are_wired():
    template = REPO / "skills/pcb-design/templates"
    policy = yaml.safe_load(
        (template / "03_src/rules/integration.yaml").read_text())
    eq(policy["schema"], 1, "template schema")
    eq(policy["default"], "prefer_module", "template default")
    for driver in ("rebuild_all.sh", "rebuild_reuse.sh"):
        text = (template / f"03_src/{driver}").read_text()
        contains(text, "module_first_check.py", f"{driver} P-MOD wiring")
        first_work = "tsx_preflight.py" if driver == "rebuild_all.sh" else "BOARD=$("
        check(text.index("module_first_check.py") < text.index(first_work),
              f"{driver} must grade architecture before board work")


if __name__ == "__main__":
    sys.exit(main())
