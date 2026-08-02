#!/usr/bin/env python3
"""T1: pin-audit dossiers use exact authorities and semantic pad aliases."""
import sys
from harness import KPY, ROOT, SCRIPTS, contains, main, must_pass, not_contains, run, test, tmpdir

SCRIPT = SCRIPTS / "pin_audit.py"
PROJECT = ROOT / "projects" / "programmable-usb2-hub"


@test("pin dossier resolves exact digest PDF and excludes aliased shell pads from winding",
      kind="known_bad")
def t_exact_pdf_alias_and_winding():
    out = tmpdir("pin_audit_")
    must_pass(run([
        KPY, SCRIPT,
        PROJECT / "04_kicad" / "programmable_usb2_hub.kicad_pcb",
        PROJECT / "06_build" / "fab" / "bom.csv",
        PROJECT / "02_parts", out, "--refs", "J2,U4",
    ]), "generate focused dossiers")
    j2 = (out / "J2.md").read_text()
    contains(j2, "**CCW (top view)**", "shell lands cannot reverse contact winding")
    contains(j2, "| SHIELD | GND |", "semantic SH alias resolves to physical pad 5")
    contains(j2, "fused: `true`", "intentional physical collapse is explicit")
    not_contains(j2, "part.yaml pins with NO pad", "resolved alias is not a join gap")
    u4 = (out / "U4.md").read_text()
    contains(u4, "AP63200Q-AP63205Q.pdf", "digest-selected automotive authority")
    not_contains(u4, "AP63200-AP63205.pdf", "generic variant PDF is not reviewed")


if __name__ == "__main__":
    sys.exit(main())
