#!/usr/bin/env python3
"""T1: FIXTURE DISCRIMINATION — canon M-DISC.

    A FIXTURE THAT CANNOT DISCRIMINATE THE FAILURE IT GUARDS IS NOT A FIXTURE.

THE INCIDENT (2026-07-25, 1b69760 then 9066ebd). `jlc_twin.xform()` used the
wrong handedness. The bug had FIVE COPIES and fixing one was mistaken for
fixing it. Every copy measured **0.000000 mm at both 0 and 180**, because

    formB(a) == formA(-a)   IDENTICALLY

and both equal the identity's own reflection at 0 and 180. So a rotation
fixture that samples only 0 and 180 passes the bug — silently, forever — and
five copies survived review across weeks. 48 of 400 cached JLC footprints (12%)
carry rot_z 90/270; 12 of one board's 102 fitted refs sit at fit offset 270.
The cost was 22 wrong CPL rotations on one board, a CORRECT sealed release
"fixed" into a wrong one, and a true 14.37 mm mis-mount adjudicated away.

THE RULE THIS SUITE ENFORCES, in two halves:

  (1) SAMPLE OUTSIDE {0, 180}. Every declared rotation-fixture set must carry
      at least one 90 or 270 case. A set of all-zeros proves nothing about a
      sign, and the repo had exactly that: the tscircuit converter's ten
      `"rotation"` fixture values were ALL 0, while
      `circuit_json_to_kicad_pcb.py` applies `korient = (-tsc_rotation) % 360`
      — a NEGATION, the exact shape of the bug, with no fixture able to see it.

  (2) PROVE THE SET DISCRIMINATES. Sampling 90 is necessary, not sufficient:
      the ASSERTION must also be one the wrong form fails. `discriminates()`
      below takes the two candidate forms and the sample set and requires a
      NONZERO separation. `t1_jlc_twin.t_xform_matches_pcbnew` already makes
      this demand about itself; M-DISC generalises it, and this suite proves
      the demand has teeth by showing a {0, 180} set is REJECTED.

Corollary from the same incident, recorded in canon and not machine-checkable:
match a suspect site on the FRAMES it maps between, never on the expression —
`board_to_local()`'s literal text is identical to the bug and is a LEGITIMATE
inverse, so "fix everything that looks like this" would have broken it.
"""
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (FIXTURES, KPY, ROOT, check, contains, eq,  # noqa: E402
                     main, must_pass, run, test, tmpdir)

SCRIPTS = ROOT / "skills" / "kicad-pcb" / "scripts"


# ------------------------------------------------------------ the operators
def form_verified(x, y, deg):
    """KiCad's OWN rotation of a footprint-local point (y-down, CCW). Verified
    against pcbnew itself — pad.GetFPRelativePosition() pushed through this
    form vs pad.GetPosition() — exact to 0.000000 mm over 72 pads."""
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return (x * c + y * s, -x * s + y * c)


def form_negated(x, y, deg):
    """The PRE-FIX `xform()` form. `form_negated(p, a) == form_verified(p, -a)`
    identically, which is the whole reason five copies of it survived."""
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return (x * c - y * s, x * s + y * c)


def discriminates(formA, formB, angles, probe=(1.0, 0.0)):
    """Largest separation between two candidate forms over a sample set.

    0.0 means the fixture set CANNOT tell them apart — every assertion it can
    make is satisfied by both, so it proves nothing about which one ships.
    This is the generalised form of the assertion
    `t1_jlc_twin.t_xform_matches_pcbnew` already makes about itself.
    """
    worst = 0.0
    for a in angles:
        pa, pb = formA(probe[0], probe[1], a), formB(probe[0], probe[1], a)
        worst = max(worst, math.hypot(pa[0] - pb[0], pa[1] - pb[1]))
    return worst


# ------------------------------------------------- the declared registry
# Every rotation-bearing fixture set in this repo, and how to read its angles.
# DECLARED rather than discovered: a scan that looks for "rotation" would go
# quiet the moment someone renames a key, and a gate that can go quiet by
# accident is the class this whole suite exists to kill. Adding a rotation
# fixture set without adding it here is caught by nothing — which is why the
# registry itself is asserted non-empty and its readers are asserted to have
# actually found values.
def _t0_rotations():
    """tscircuit converter fixtures: `"rotation": N` in circuit.json.

    These feed `circuit_json_to_kicad_pcb.py`, whose placement operator is
    `korient = (-tsc_rotation) % 360` — a NEGATION, i.e. exactly the shape of
    the xform() bug, and the reason this set must not be all-zeros."""
    vals = []
    for f in sorted((FIXTURES / "t0").rglob("circuit.json")):
        for m in re.finditer(r'"rotation"\s*:\s*(-?[\d.]+)', f.read_text()):
            vals.append((f.relative_to(ROOT), float(m.group(1))))
    return vals


def _twin_probe_rotations():
    """t1_jlc_twin's pcbnew rotation probe: the angles its fixture board places
    footprints at (added by 1b69760 as part of the handedness fix)."""
    txt = (ROOT / "tests" / "t1_jlc_twin.py").read_text()
    vals = []
    # the probe board places its footprints from a literal angle list
    for m in re.finditer(r"SetOrientationDegrees\(\[([-\d.,\s]+)\]", txt):
        for tok in m.group(1).split(","):
            if tok.strip():
                vals.append((Path("tests/t1_jlc_twin.py"), float(tok)))
    for m in re.finditer(r"SetOrientationDegrees\((-?[\d.]+)\)", txt):
        vals.append((Path("tests/t1_jlc_twin.py"), float(m.group(1))))
    return vals


REGISTRY = [
    ("tscircuit converter (t0 circuit.json)", _t0_rotations),
    ("jlc_twin pcbnew rotation probe", _twin_probe_rotations),
]


def off_axis(vals):
    return [v for v in vals if round(v[1]) % 180 != 0]


# ==================================================================== clean
@test("M-DISC: the discrimination assertion itself has teeth — a {0,180} "
      "sample set CANNOT tell the two handedness forms apart", kind="known_bad")
def t_discriminator_has_teeth():
    """THE FACT THE WHOLE RULE RESTS ON, measured rather than asserted.
    `formB(a) == formA(-a)` identically, and at 0 and 180 the negation is a
    no-op, so the two forms are MATHEMATICALLY IDENTICAL there. This is the
    known-bad case for the discriminator: if a future edit made
    `discriminates()` return nonzero for a {0,180} set, the whole registry
    check below would start passing vacuously."""
    sep = discriminates(form_verified, form_negated, [0, 180])
    check(sep < 1e-12,
          f"a 0/180-only fixture set reports separation {sep} — it should be "
          f"EXACTLY zero. The two forms coincide there; if this is nonzero the "
          f"discriminator is measuring something other than the handedness")
    for a in (90, 270):
        sep = discriminates(form_verified, form_negated, [a])
        check(sep > 1.0,
              f"a {a}-deg sample separates the two forms by only {sep} — the "
              f"one angle class that CAN see the bug no longer does")
    # ...and the signature: at 90/270 the two forms are exactly 180 apart
    for a in (90, 270):
        pa = form_verified(1.0, 0.0, a)
        pb = form_negated(1.0, 0.0, a)
        check(abs(pa[0] + pb[0]) < 1e-12 and abs(pa[1] + pb[1]) < 1e-12,
              f"at {a} deg the two forms are no longer exact negations "
              f"({pa} vs {pb}) — the 'always perfect or upside down, never "
              f"noise' signature that made this bug invisible")


@test("M-DISC: every declared rotation-fixture set carries a 90 or 270 case")
def t_registry_samples_off_axis():
    """Half (1) of the rule. A set of all-zeros passes a negated operator.
    The tscircuit converter set was EXACTLY that — ten `"rotation"` values,
    all 0 — while `circuit_json_to_kicad_pcb.py` applies
    `korient = (-tsc_rotation) % 360`."""
    check(REGISTRY, "the rotation-fixture registry is empty")
    for name, reader in REGISTRY:
        vals = reader()
        check(vals, f"{name}: the registry reader found NO rotation values at "
                    f"all — a reader that silently returns nothing turns this "
                    f"gate off without anyone noticing")
        off = off_axis(vals)
        check(off, f"{name}: all {len(vals)} rotation samples are 0 or 180 "
                   f"({sorted({v[1] for v in vals})}). A 0/180-only fixture "
                   f"set is satisfied by BOTH handedness forms and proves "
                   f"nothing — add a 90 or 270 case (canon M-DISC). Files: "
                   f"{sorted({str(v[0]) for v in vals})[:4]}")


@test("M-DISC: the tscircuit placement operator's own fixture separates the "
      "two forms — the fixture is proven, not assumed", kind="known_bad")
def t_tsx_placement_fixture_discriminates():
    """Half (2). `circuit_json_to_kicad_pcb.py` maps tscircuit's y-up CCW frame
    to KiCad's with `korient = (-tsc_rotation) % 360`. That negation is
    CORRECT — and it is the exact literal text of the xform() bug, so the only
    thing separating "right" from "wrong" here is a fixture that can see the
    difference. Before this suite the repo had none: all ten t0 rotation
    values were 0, where the two candidate mappings agree exactly.

    Asserted as a PROPERTY of the fixture, not of the operator: the rotated
    fixture's own angles must produce a nonzero separation between
    `(-rot) % 360` and `(+rot) % 360`. RED-VERIFIED by restricting the angle
    list to (0, 180): the separation collapses to 0.0 and this test FAILS."""
    vals = [v[1] for v in _t0_rotations()]
    off = [a for a in vals if round(a) % 180 != 0]
    check(off, "the t0 fixture set still has no off-axis rotation")
    sep = max(abs(((-a) % 360) - (a % 360)) for a in off)
    check(sep > 0,
          f"the t0 rotation samples {sorted(set(off))} cannot separate "
          f"korient=(-rot)%360 from korient=(+rot)%360")


@test("M-DISC: the rotated-placement fixture is a VALID converter input and "
      "its angles are EXACTLY-180 discriminating", kind="known_bad")
def t_rotated_placement_fixture():
    """The fixture half (1) demands, and the proof that it is real rather than
    decorative.

    `circuit_json_to_kicad_pcb.py` maps tscircuit's y-up CCW frame to KiCad's
    with `korient = (-tsc_rotation) % 360`. That negation is CORRECT — and it
    is the exact literal text of the xform() bug, so the only thing separating
    "right" from "wrong" here is a fixture that can see the difference. Before
    this fixture the repo had none: every `"rotation"` value in tests/fixtures/
    t0 was 0, where the two candidate mappings agree EXACTLY, and the t0
    fixtures did not declare `pcb_component` elements at all — so the
    PLACEMENT bridge had no fixture whatsoever.

    Two properties are asserted, neither of them about the operator (which is
    not this suite's to grade) but about the FIXTURE's power to discriminate:
      1. it carries an off-axis angle, and at that angle the two candidate
         mappings differ by EXACTLY 180 — the incident signature, "always
         perfect or upside down, never noise";
      2. at its 0/180 angles the two mappings AGREE, which is the direct
         demonstration that the pre-existing all-zero fixture set proved
         nothing.
    It is also run through the real converter, so it is a fixture the pipeline
    accepts rather than a JSON blob nobody consumes."""
    fx = FIXTURES / "t0" / "rotated_placement" / "circuit.json"
    check(fx.exists(), f"missing rotated-placement fixture: {fx}")
    data = json.loads(fx.read_text())
    rots = {e["pcb_component_id"]: e.get("rotation", 0)
            for e in data if e.get("type") == "pcb_component"}
    check(rots, "the fixture declares no pcb_component elements — the "
                "PLACEMENT bridge is what it exists to cover")
    check(any(round(r) % 180 != 0 for r in rots.values()),
          f"the rotated-placement fixture carries only on-axis angles: {rots}")

    for tsc in sorted(set(rots.values())):
        want = (-tsc) % 360           # the shipped mapping
        wrong = (+tsc) % 360          # its negation, the bug's shape
        if round(tsc) % 180 == 0:
            eq(want, wrong, f"at {tsc} deg the two mappings must AGREE — that "
                            f"is exactly why an all-0/180 fixture set proves "
                            f"nothing about a sign")
        else:
            eq((want - wrong) % 360, 180.0,
               f"at {tsc} deg the two mappings must differ by EXACTLY 180 "
               f"(the incident signature)")

    r = must_pass(run([KPY, SCRIPTS / "circuit_json_to_kicad_sch.py", fx,
                       "-o", tmpdir("rotfx_") / "rot.kicad_sch"]),
                  "the converter on the rotated-placement fixture")
    contains(r.out, "4 components", "the fixture reaches the converter intact")


if __name__ == "__main__":
    sys.exit(main())
