#!/usr/bin/env python3
"""T1: the POWER-TREE TOPOLOGY gate (E-TOPO) — power_topology.py.

Motivating incident (2026-07-22, usb-hub-3s): the board shipped an IP6559
BUCK-BOOST SoC (+ 4 external FETs + 30V-FET/TVS coordination + compact hot-loop
congestion + a 16A input trunk) for its USB-C port. But the battery is
9-12.6V and the USB-C output is 5V ONLY, so Vout(5) < Vin_min(9) ALWAYS: a
plain step-down BUCK sufficed. The buck-boost existed only for >5V PDOs the
spec never required. Root cause: D-SPEC pinned the CURRENT ("5A compliant")
but never the OUTPUT VOLTAGE RANGE, and converter topology was INTERPRETED,
not DERIVED from Vin-vs-Vout. E-TOPO makes topology a mechanical check.

RED-VERIFIED (new-gate variant, per tests/README "Adding a regression"):
power_topology.py did not exist before this change — the suite cannot be run
against pre-fix code because the gate could not exist. Instead each known-bad
fixture is a PASSING fixture broken in exactly ONE way, and the test asserts
the checker fails for the RIGHT reason (over-engineered vs cannot-meet vs a
schema/envelope error vs an under-built trunk). THE INCIDENT itself (IP6559
buck_boost on a 5V-only rail) is pinned as the primary known-bad, using the
real part.yaml `type:` string (pd_source_buckboost_soc) as paid-for evidence.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, SCRIPTS, contains, main, must_fail,  # noqa: E402
                     must_pass, run, test, tmpdir)

PTOP = SCRIPTS / "power_topology.py"

# The real usb-hub-3s converter part.yaml `type:` strings — the paid-for
# evidence this gate calibrates against (read from 02_parts during commission).
IP6559_TYPE = "pd_source_buckboost_soc"   # -> BUCK_BOOST
LM5116_TYPE = "buck_controller"           # -> BUCK


# --------------------------------------------------------------- fixtures
def project(power_tree, parts=None, nets=None):
    """Scratch project tree: 02_parts/<dir>/part.yaml with a `type:`, and
    03_src/rules/power_tree.yaml (+ optional nets.yaml)."""
    d = tmpdir("etopo_")
    (d / "03_src" / "rules").mkdir(parents=True)
    for name, ptype in (parts or {}).items():
        pd = d / "02_parts" / name
        pd.mkdir(parents=True)
        (pd / "part.yaml").write_text(f"mpn: {name}\ntype: {ptype}\n")
    if power_tree is not None:
        (d / "03_src" / "rules" / "power_tree.yaml").write_text(power_tree)
    if nets is not None:
        (d / "03_src" / "rules" / "nets.yaml").write_text(nets)
    return d


def rail(name, vin_min, vin_max, vout_min, vout_max, iout, conv, eff=None):
    e = f"    eff: {eff}\n" if eff is not None else ""
    return (f"  - name: {name}\n"
            f"    vin_min: {vin_min}\n    vin_max: {vin_max}\n"
            f"    vout_min: {vout_min}\n    vout_max: {vout_max}\n"
            f"    iout_max_A: {iout}\n    converter: {conv}\n{e}")


def ptree(*rails, top=""):
    return top + "rails:\n" + "".join(rails)


def etopo(d, *extra):
    return run([KPY, PTOP, d, *extra])


# ------------------------------------------------------------ clean cases
@test("E-TOPO PASSES the usb-hub-3s USB-A rail: 9-12.6V in, 5V out, LM5116 buck")
def t_lm5116_buck_pass():
    """THE CALIBRATION (correct case): a fixed 5V output below a 9V floor needs
    only step-down; the LM5116 buck is exactly right."""
    d = project(ptree(rail("USB-A", 9.0, 12.6, 5, 5, 7, "LM5116MHX-NOPB")),
                parts={"LM5116MHX-NOPB": LM5116_TYPE})
    r = must_pass(etopo(d), "E-TOPO on the LM5116 buck rail")
    contains(r.out, "required=BUCK", "derives buck")
    contains(r.out, "declared=BUCK", "reads the LM5116 as buck")
    contains(r.out, "E-TOPO OK", "clean report")


@test("E-TOPO PASSES a full-PD rail (5-20V out overlaps Vin) with a buck_boost")
def t_full_pd_buckboost_pass():
    """A genuine 5-20V PD output overlaps the 9-12.6V input, so buck_boost is
    REQUIRED and a buck_boost part is correct — NOT over-engineering."""
    d = project(ptree(rail("USB-C-PD", 9.0, 12.6, 5, 20, 5, "IP6559-C")),
                parts={"IP6559-C": IP6559_TYPE})
    r = must_pass(etopo(d), "E-TOPO on a real buck_boost need")
    contains(r.out, "required=BUCK_BOOST", "derives buck_boost from the overlap")
    contains(r.out, "E-TOPO OK", "clean report")


@test("E-TOPO is N-A (exit 0) when there is no power_tree.yaml")
def t_na_no_file():
    d = project(None)
    r = must_pass(etopo(d), "E-TOPO with no power_tree.yaml")
    contains(r.out, "N-A", "N-A report")


@test("E-TOPO --derive prints the topology table (buck / boost / buck_boost)")
def t_derive_table():
    """The whole physics, ad-hoc: Vout_max<Vin_min=>BUCK, Vout_min>Vin_max=>
    BOOST, overlap=>BUCK_BOOST."""
    cases = [((9, 12.6, 5, 5), "BUCK"),
             ((3.0, 4.2, 5, 5), "BOOST"),
             ((9, 12.6, 5, 20), "BUCK_BOOST")]
    for (a, b, c, e), want in cases:
        r = must_pass(run([KPY, PTOP, "--derive", a, b, c, e]),
                      f"--derive {a},{b},{c},{e}")
        # BUCK_BOOST contains BUCK/BOOST; assert the exact arrow target
        contains(r.out, f"-> {want}", f"derive {a}-{b}/{c}-{e} => {want}")


# ------------------------------------------------------------ known-bad
@test("E-TOPO FAILS THE INCIDENT: IP6559 buck_boost on a 5V-only 9-12.6V rail",
      kind="known_bad")
def t_incident_over_engineered():
    """usb-hub-3s 2026-07-22: a buck_boost where a buck suffices. Also verifies
    the input-current print (30W+25W=55W -> ~6.8A at 9V) and the OVER-BUILT
    advisory contrasting the board's ~16A trunk (nets.yaml PWR_IN 15.5A)."""
    d = project(
        ptree(rail("USB-A", 9.0, 12.6, 5, 5, 6, "LM5116MHX-NOPB"),
              rail("USB-C", 9.0, 12.6, 5, 5, 5, "IP6559-C"),
              top="input_trunk_class: PWR_IN\n"),
        parts={"LM5116MHX-NOPB": LM5116_TYPE, "IP6559-C": IP6559_TYPE},
        nets="classes:\n  PWR_IN:\n    nets: [VBAT, VIN]\n"
             "    current: \"15.5 A worst case\"\n")
    r = must_fail(etopo(d), "E-TOPO on the IP6559 incident", "over-engineered")
    contains(r.out, "IP6559-C", "names the over-capable part")
    contains(r.out, "buck suffices", "explains buck suffices")
    contains(r.out, "6.8 A", "prints the derived worst-case input current")
    contains(r.out, "OVER-BUILT", "flags the ~16A trunk as over-provisioned")


@test("E-TOPO FAILS a cannot-meet case: 3.0-4.2V in, 5V out, a BUCK declared",
      kind="known_bad")
def t_cannot_meet_boost():
    """The under-capable direction: a 3S-cell-low input below a 5V output needs
    step-UP; a buck cannot deliver it."""
    d = project(ptree(rail("BOOSTED", 3.0, 4.2, 5, 5, 3, "LM5116MHX-NOPB")),
                parts={"LM5116MHX-NOPB": LM5116_TYPE})
    r = must_fail(etopo(d), "E-TOPO on a boost need with a buck part",
                  "cannot meet Vout")
    contains(r.out, "required=BOOST", "derives boost from Vout>Vin_max")


@test("E-TOPO refuses a rail missing its Vout ENVELOPE (schema error, exit 2)",
      kind="known_bad")
def t_missing_vout_range():
    """The root cause encoded as a schema gate: a rail that pins current but not
    the output voltage range must fail to load — D-SPEC demands the envelope."""
    pt = ("rails:\n"
          "  - name: USB-C\n    vin_min: 9.0\n    vin_max: 12.6\n"
          "    vout_min: 5\n    iout_max_A: 5\n"        # vout_max MISSING
          "    converter: IP6559-C\n")
    d = project(pt, parts={"IP6559-C": IP6559_TYPE})
    r = must_fail(etopo(d), "E-TOPO on a missing vout envelope", "LOAD ERROR")
    contains(r.out, "vout_max", "names the missing envelope field")
    contains(r.out, "ENVELOPE", "explains the D-SPEC envelope requirement")


@test("E-TOPO FAILS an under-declared input trunk current (under-built copper)",
      kind="known_bad")
def t_under_declared_trunk():
    """Same 55W tree deriving ~6.8A, but nets.yaml PWR_IN declares only 3A and
    input_trunk_class names it unambiguously -> the copper/fuse cannot carry
    the load, so this is a FAIL, not just an advisory."""
    d = project(
        ptree(rail("USB-A", 9.0, 12.6, 5, 5, 6, "LM5116MHX-NOPB"),
              rail("USB-C", 9.0, 12.6, 5, 5, 5, "LM5116MHX-NOPB"),
              top="input_trunk_class: PWR_IN\n"),
        parts={"LM5116MHX-NOPB": LM5116_TYPE},
        nets="classes:\n  PWR_IN:\n    nets: [VBAT, VIN]\n"
             "    current: \"3 A\"\n")
    r = must_fail(etopo(d), "E-TOPO under-declared trunk", "UNDER-BUILT")
    contains(r.out, "3", "names the declared trunk current")
    contains(r.out, "6.8", "names the derived worst case it falls short of")


@test("E-TOPO refuses a converter whose part.yaml type does not classify",
      kind="known_bad")
def t_type_unclassifiable():
    """The converter part.yaml `type:` must name buck/boost/buck_boost; a type
    the checker cannot classify (e.g. sepic) is a load error, never a silent
    pass."""
    d = project(ptree(rail("R", 9.0, 12.6, 5, 5, 3, "SEPICPART")),
                parts={"SEPICPART": "sepic_controller"})
    r = must_fail(etopo(d), "E-TOPO on an unclassifiable type", "LOAD ERROR")
    contains(r.out, "does not classify", "explains the type must classify")


if __name__ == "__main__":
    sys.exit(main())
