#!/usr/bin/env python3
"""T1: pin-audit dossiers use exact authorities and semantic pad aliases."""
import hashlib
import importlib.util
import sys
from harness import Failed, KPY, ROOT, SCRIPTS, contains, main, must_pass, not_contains, run, test, tmpdir

SCRIPT = SCRIPTS / "pin_audit.py"
PROJECT = ROOT / "projects" / "programmable-usb2-hub"

_spec = importlib.util.spec_from_file_location("pin_audit_under_test", SCRIPT)
_pin_audit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_pin_audit)


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


@test("P-AUTH resolves only the local PDF selected by datasheet.sha256")
def t_authority_exact_digest():
    d = tmpdir("pin_authority_")
    exact = d / "exact.pdf"
    adjacent = d / "adjacent.pdf"
    exact.write_bytes(b"exact authority")
    adjacent.write_bytes(b"neighboring family")
    digest = hashlib.sha256(exact.read_bytes()).hexdigest()
    got = _pin_audit.datasheet_path(d, {"sha256": digest})
    if got != str(exact):
        raise Failed(f"digest-selected authority: got {got!r}, want {str(exact)!r}")


@test("P-AUTH rejects a missing digest instead of falling back to the sole PDF",
      kind="known_bad")
def t_authority_missing_digest():
    d = tmpdir("pin_authority_missing_")
    (d / "plausible.pdf").write_bytes(b"not bound")
    try:
        _pin_audit.datasheet_path(d, {})
    except RuntimeError as exc:
        contains(str(exc), "P-AUTH", "typed authority failure")
        return
    raise Failed("missing digest selected the sole PDF")


@test("P-AUTH rejects a mismatched digest instead of falling back to a URL or PDF",
      kind="known_bad")
def t_authority_mismatched_digest():
    d = tmpdir("pin_authority_mismatch_")
    (d / "wrong.pdf").write_bytes(b"wrong revision")
    try:
        _pin_audit.datasheet_path(d, {"sha256": "0" * 64,
                                      "url": "https://example.invalid/right.pdf"})
    except RuntimeError as exc:
        contains(str(exc), "no local PDF matches", "digest mismatch evidence")
        return
    raise Failed("mismatched digest selected adjacent authority")


if __name__ == "__main__":
    sys.exit(main())
