#!/usr/bin/env python3
"""T1: the skill-owned 03_src rebuild driver TEMPLATES.

WHY THIS SUITE EXISTS (2026-07-23): the deterministic promoted-chain rebuild
driver was independently rewritten by THREE boards (usb-hub-3s-v2 and -v3
`rebuild_fast.sh`, crow-recorder-central-v2 `rebuild_reuse.sh`) — a canon M8
two-strike violation. The pattern is now the skill-owned template
`skills/pcb-design/templates/03_src/rebuild_reuse.sh`. These are PROPERTY
assertions on the template text + `bash -n` — never byte-golden, and never an
execution of a real board rebuild (that is the --slow e2e tier's job).

The properties pinned here are each a paid-for incident:
  * generate_rules runs BEFORE import (canon R1) and LAST again after stitch
    (pcbnew saves clobber .kicad_pro netclasses — 2026-07-17, `ae93b4b`).
  * the DRC gate carries --severity-all --refill-zones --schematic-parity on
    ONE invocation (violations are classified at full severity, zones are
    refilled, and parity actually runs).
  * the pinned .kicad_sch is copied beside the board BEFORE the DRC call —
    without it --schematic-parity SILENTLY SKIPS (crow-rv2 finding,
    routing.md M-REPRO entry, 2026-07-23).
  * rebuild_reuse.sh never invokes tsci/tsci-build — `tsci build` is
    non-deterministic (~2900-line UUID/ordering churn in the regenerated
    .kicad_sch, measured on crow-rv2); the committed sch is PINNED canonical.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (ROOT, check, contains, main, not_contains, run,  # noqa: E402
                     test)

TPL_DIR = ROOT / "skills" / "pcb-design" / "templates" / "03_src"
REUSE = TPL_DIR / "rebuild_reuse.sh"
ALL = TPL_DIR / "rebuild_all.sh"


def drc_gate_ok(txt):
    """True iff a single kicad-cli DRC invocation carries all three flags.
    Continuation-line aware (the templates split the command with '\\')."""
    joined = txt.replace("\\\n", " ")
    for m in re.finditer(r'kicad-cli\s+pcb\s+drc[^\n]*', joined):
        line = m.group(0)
        if all(f in line for f in
               ("--severity-all", "--refill-zones", "--schematic-parity")):
            return True
    return False


def rules_last_after_stitch(txt):
    """True iff the LAST generate_rules_generic call comes after the LAST
    stitch call, and one generate_rules call precedes the import."""
    rules = [m.start() for m in re.finditer(r'generate_rules_generic', txt)]
    stitch = [m.start() for m in re.finditer(r'route_and_stitch_generic\.py"?\s+stitch', txt)]
    imp = [m.start() for m in re.finditer(r'route_and_stitch_generic\.py"?\s+import', txt)]
    if not (rules and stitch and imp):
        return False
    return rules[-1] > stitch[-1] and rules[0] < imp[0]


# ---------------------------------------------------------- clean cases
@test("rebuild_reuse.sh template: bash -n clean, and so is rebuild_all.sh")
def t_syntax():
    for f in (REUSE, ALL):
        r = run(["bash", "-n", f])
        check(r.rc == 0, f"bash -n {f.name} failed:\n{r.out[-1500:]}")


@test("rebuild_reuse.sh: ONE DRC invocation carries --severity-all "
      "--refill-zones --schematic-parity")
def t_drc_flags():
    check(drc_gate_ok(REUSE.read_text()),
          "no single kicad-cli pcb drc line carries all three gate flags")


@test("rebuild_reuse.sh: generate_rules before import (R1) AND last after "
      "stitch (netclass clobber)")
def t_rules_ordering():
    check(rules_last_after_stitch(REUSE.read_text()),
          "generate_rules ordering violated: need one call before import and "
          "the final call after stitch")


@test("rebuild_reuse.sh: pinned .kicad_sch is copied beside the board BEFORE "
      "the DRC gate (else --schematic-parity silently skips)")
def t_sch_beside_board():
    txt = REUSE.read_text()
    cp = re.search(r'^\s*cp\s+"?\$SCH"?\s+"04_kicad/\$BOARD\.kicad_sch"', txt, re.M)
    drc = re.search(r'^\s*kicad-cli pcb drc', txt, re.M)   # the invocation, not the header comment
    check(cp and drc and cp.start() < drc.start(),
          "the pinned sch copy is missing or comes after the DRC invocation")


@test("rebuild_reuse.sh: never invokes tsci (the non-deterministic stage is "
      "skipped; the committed .kicad_sch is pinned canonical)")
def t_no_tsci():
    txt = REUSE.read_text()
    check(not re.search(r'^\s*[^#\n]*\btsci\b', txt, re.M),
          "rebuild_reuse.sh invokes tsci — that stage is non-deterministic "
          "and belongs to rebuild_all.sh only")
    contains(txt, "PINNED", "header (must document the pinned-sch fact)")
    contains(txt, "rebuild_all.sh", "header (must say when to use which driver)")


@test("rebuild_reuse.sh: board name is DERIVED from floorplan.yaml project.name "
      "(no hand-edited BOARD= constant)")
def t_board_derived():
    txt = REUSE.read_text()
    check(re.search(r'^BOARD=\$\(', txt, re.M),
          "BOARD is not derived from config")
    contains(txt, "project", "derivation (must read the project block)")
    check(not re.search(r'^BOARD=[A-Za-z0-9_]+\s*$', txt, re.M),
          "template carries a hardcoded BOARD= constant")


# ------------------------------------------------------- known-bad cases
@test("the ordering assertion has TEETH: rules-before-stitch is rejected",
      kind="known_bad")
def t_kb_ordering_teeth():
    """Prove rules_last_after_stitch is not a rubber stamp: feed it the
    template with the final generate_rules call moved BEFORE stitch (the
    exact 2026-07-17 netclass-clobber shape) and it must reject."""
    txt = REUSE.read_text()
    lines = txt.splitlines(keepends=True)
    rules_idx = [i for i, l in enumerate(lines)
                 if "generate_rules_generic" in l and not l.lstrip().startswith("#")]
    stitch_idx = [i for i, l in enumerate(lines)
                  if re.search(r'route_and_stitch_generic\.py"?\s+stitch', l)]
    check(rules_idx and stitch_idx, "template lost its rules/stitch steps")
    bad = lines[:]
    rules_line = bad.pop(rules_idx[-1])
    bad.insert(stitch_idx[0] - 1, rules_line)   # final rules call now precedes stitch
    mutated = "".join(bad)
    check(mutated != txt, "mutation did not change the template")
    check(not rules_last_after_stitch(mutated),
          "the ordering check ACCEPTED generate_rules before stitch — it is blind")


@test("the DRC-flag assertion has TEETH: a dropped --schematic-parity is "
      "rejected", kind="known_bad")
def t_kb_drc_flag_teeth():
    """--schematic-parity was SILENTLY missing from two boards' fast drivers
    until crow-rv2's rewrite noticed it never ran. The check must reject a
    gate line without it."""
    txt = REUSE.read_text()
    mutated = txt.replace("--schematic-parity", "")
    check(mutated != txt, "mutation did not change the template")
    check(not drc_gate_ok(mutated),
          "the DRC-flag check ACCEPTED a gate without --schematic-parity")


if __name__ == "__main__":
    sys.exit(main())
