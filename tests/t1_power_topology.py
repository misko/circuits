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

E-MARGIN + E-OFF (2026-07-23, usb-hub-3s-v3 external review) are power_tree.yaml
siblings of E-TOPO added here. usb-hub-3s-v3 passed BOTH zero-context red-team
reviews with two defects neither flagged: (A) a 4.97V rail feeding a Pi5
(UV ~4.63V) at 5A left only ~68 mOhm for board+connector+cable IR drop
(E-MARGIN); (B) a 3S-LiPo board tied both buck EN pins active with no master
switch idle-drained the pack in storage (E-OFF). RED-VERIFIED (new-gate
variant): the --margin / --off-control MODES did not exist before this change,
so against pre-change power_topology.py the flag is an unrecognized argument
(argparse exit 2) carrying NONE of the asserted failure text -- every E-MARGIN /
E-OFF case below goes RED. Each known-bad is additionally a passing-TOPOLOGY
board broken in exactly one margin/off dimension.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, SCRIPTS, check, contains, main,  # noqa: E402
                     must_fail, must_pass, not_contains, run, test, tmpdir)

PTOP = SCRIPTS / "power_topology.py"

# The real usb-hub-3s converter part.yaml `type:` strings — the paid-for
# evidence this gate calibrates against (read from 02_parts during commission).
IP6559_TYPE = "pd_source_buckboost_soc"   # -> BUCK_BOOST
LM5116_TYPE = "buck_controller"           # -> BUCK


# --------------------------------------------------------------- fixtures
def project(power_tree, parts=None, nets=None):
    """Scratch project tree: 02_parts/<dir>/part.yaml with a `type:`, and
    03_src/rules/power_tree.yaml (+ optional nets.yaml).

    A parts value is either the bare `type:` string, or a dict of part.yaml
    fields (for the LINEAR bounds `dropout_mv:` / `pdiss_max_mw:`)."""
    d = tmpdir("etopo_")
    (d / "03_src" / "rules").mkdir(parents=True)
    for name, spec in (parts or {}).items():
        pd = d / "02_parts" / name
        pd.mkdir(parents=True)
        fields = {"type": spec} if isinstance(spec, str) else dict(spec)
        body = "".join(f"{k}: {v}\n" for k, v in fields.items())
        (pd / "part.yaml").write_text(f"mpn: {name}\n{body}")
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


# ============================ E-MARGIN =====================================
# Output SETPOINT vs load brownout, net of the delivery IR drop. A rail feeding
# a KNOWN load declares load_uv_threshold (ACTIVATES the check); the setpoint
# headroom must buy more series resistance than the delivery path burns at Imax.
def railx(name, vin_min, vin_max, vout_min, vout_max, iout, conv, **extra):
    """rail() plus arbitrary OPTIONAL per-rail fields (load_uv_threshold,
    ir_budget_mohm, margin) appended into the same mapping."""
    s = rail(name, vin_min, vin_max, vout_min, vout_max, iout, conv)
    for k, v in extra.items():
        s += f"    {k}: {v}\n"
    return s


def margin(d):
    return run([KPY, PTOP, d, "--margin"])


def offctl(d):
    return run([KPY, PTOP, d, "--off-control"])


@test("E-MARGIN is N-A when no rail declares load_uv_threshold")
def t_margin_na():
    """Only a rail feeding a fixed-brownout load has a setpoint margin to
    grade; a plain 5V hub rail is N-A, not a false FAIL."""
    d = project(ptree(rail("USB-A", 9.0, 12.6, 5, 5, 7, "LM5116MHX-NOPB")),
                parts={"LM5116MHX-NOPB": LM5116_TYPE})
    r = must_pass(margin(d), "E-MARGIN with no load_uv_threshold")
    contains(r.out, "N-A", "N-A report")


@test("E-MARGIN PASSES a healthy setpoint (5.1V into a Pi5, 60mOhm delivery)")
def t_margin_pass():
    """The corrected form of the incident: a 5.1V setpoint over an assumed
    60mOhm path clears the Pi5 brownout with margin (headroom 470mV vs
    60mOhm x 5A x 1.2 = 360mV)."""
    d = project(ptree(railx("PI5", 9.0, 12.6, 5.1, 5.1, 5, "LM5116MHX-NOPB",
                            load_uv_threshold=4.63, ir_budget_mohm=60)),
                parts={"LM5116MHX-NOPB": LM5116_TYPE})
    r = must_pass(margin(d), "E-MARGIN on a healthy setpoint")
    contains(r.out, "E-MARGIN OK", "clean report")


@test("E-MARGIN FAILS THE INCIDENT (floor mode): 4.97V into a Pi5 at 5A = 68mOhm",
      kind="known_bad")
def t_margin_incident_floor():
    """usb-hub-3s-v3 (2026-07-23, external review): a rail regulated to 4.97V
    fed a Pi5 (UV ~4.63V) at 5A -- only (4.97-4.63)/5A = 68 mOhm TOTAL for
    board+connector+cable, below the 100 mOhm floor a real 5A USB-C delivery
    path exceeds. With only load_uv_threshold declared this is the
    (Vout-UV)-below-a-margin-floor form. Both zero-context reviews computed
    4.97V and neither flagged the margin."""
    d = project(ptree(railx("PI5", 9.0, 12.6, 4.97, 4.97, 5, "LM5116MHX-NOPB",
                            load_uv_threshold=4.63)),
                parts={"LM5116MHX-NOPB": LM5116_TYPE})
    r = must_fail(margin(d), "E-MARGIN on the 4.97V incident", "68 mOhm")
    contains(r.out, "floor", "names the floor it falls under")
    contains(r.out, "raise the setpoint", "prescribes the fix")


@test("E-MARGIN FAILS THE INCIDENT (precise mode): 4.97V, ir_budget 150mOhm",
      kind="known_bad")
def t_margin_incident_precise():
    """Same 4.97V rail, now declaring the real delivery resistance
    (ir_budget_mohm: 150 -- a 2m e-marked 5A USB-C cable + connectors): the IR
    drop is 750mV but the setpoint only has 340mV of headroom, so the Pi browns
    out under load. FAILS even at the default 1.2x margin."""
    d = project(ptree(railx("PI5", 9.0, 12.6, 4.97, 4.97, 5, "LM5116MHX-NOPB",
                            load_uv_threshold=4.63, ir_budget_mohm=150)),
                parts={"LM5116MHX-NOPB": LM5116_TYPE})
    r = must_fail(margin(d), "E-MARGIN precise-mode incident", "browns out")
    contains(r.out, "750 mV", "prints the IR drop at Imax")
    contains(r.out, "68 mOhm", "still surfaces the 68mOhm budget")


@test("E-MARGIN FAILS a setpoint already below the load brownout (dead on arrival)",
      kind="known_bad")
def t_margin_dead_on_arrival():
    """The degenerate case: a 4.5V worst-case output is already under the
    4.63V brownout before ANY IR drop -- headroom is negative."""
    d = project(ptree(railx("PI5", 9.0, 12.6, 4.5, 4.5, 5, "LM5116MHX-NOPB",
                            load_uv_threshold=4.63)),
                parts={"LM5116MHX-NOPB": LM5116_TYPE})
    r = must_fail(margin(d), "E-MARGIN on a sub-brownout setpoint",
                  "dead on arrival")


# ==================== feedback: TOLERANCE WINDOW ===========================
# usb-hub-3s-v3 (2026-07-23, external review): E-MARGIN/E-TOPO accepted
# AUTHOR-DECLARED vout_min/vout_max, and the author computed them from ONLY the
# regulator reference tolerance (Vref +/-1.5%) — omitting the divider
# resistors'. The real USB-C window (R12 4.12k +/-0.1%, R13 1.21k +/-1%, Vref
# 1.215V +/-1.5%) is 5.227-5.479V vs the declared 5.27-5.43V; the gate had no
# way to catch it. The OPTIONAL per-rail feedback: block makes the corners
# COMPUTED. RED-VERIFIED (git-swap, 2026-07-23): against pre-change
# power_topology.py the feedback: key is an UNKNOWN rail field that load_rails
# silently ignores, so the incident fixture PASSES E-TOPO/E-MARGIN — every
# known-bad case below goes RED against the pre-fix gate (verified by swapping
# git HEAD's power_topology.py back in; both t_feedback_understated_* failed,
# then passed with the fixed gate restored).
def fbblock(vref=1.215, vref_tol=1.5, rt=4120, rt_tol=0.1,
            rb=1210, rb_tol=1.0, omit=None):
    """The REAL usb-hub-3s-v3 USB-C divider (R12/R13) as a nested feedback:
    block; `omit` drops one field for the partial-stack known-bad."""
    fields = [("vref", vref), ("vref_tol_pct", vref_tol),
              ("r_top_ohm", rt), ("r_top_tol_pct", rt_tol),
              ("r_bottom_ohm", rb), ("r_bottom_tol_pct", rb_tol)]
    body = "".join(f"      {k}: {v}\n" for k, v in fields if k != omit)
    return "    feedback:\n" + body


@test("E-TOPO/E-MARGIN PASS an HONEST declared window covering the computed "
      "feedback corners (5.22-5.48 over computed 5.227-5.479)")
def t_feedback_honest_pass():
    """The corrected form of the incident: declared window 5.22-5.48V is WIDER
    than the computed tolerance corners 5.227-5.479V -> both modes pass, and
    E-MARGIN grades headroom from the COMPUTED worst-low (5.227V), not the
    declared vout_min (5.22V)."""
    d = project(ptree(railx("USB-C", 9.0, 12.6, 5.22, 5.48, 5,
                            "LM5116MHX-NOPB",
                            load_uv_threshold=4.63, ir_budget_mohm=88)
                      + fbblock()),
                parts={"LM5116MHX-NOPB": LM5116_TYPE})
    r = must_pass(etopo(d), "E-TOPO on an honest feedback window")
    contains(r.out, "5.227-5.479", "prints the computed corner window")
    contains(r.out, "E-TOPO OK", "clean report")
    r = must_pass(margin(d), "E-MARGIN on an honest feedback window")
    contains(r.out, "5.227", "headroom graded from the COMPUTED worst-low")
    contains(r.out, "COMPUTED worst-low", "says the worst-low is computed")
    contains(r.out, "E-MARGIN OK", "clean report")


@test("E-TOPO FAILS THE INCIDENT: declared 5.27-5.43 NARROWER than the "
      "computed feedback corners 5.227-5.479", kind="known_bad")
def t_feedback_understated_topo():
    """THE REAL CASE (usb-hub-3s-v3 USB-C rail, 2026-07-23): vout_min/vout_max
    declared from Vref tolerance alone (5.27-5.43V) with the divider block
    Vref 1.215 +/-1.5%, R12 4.12k +/-0.1%, R13 1.21k +/-1% -> computed
    5.227-5.479V. The declared window under-states BOTH corners; E-TOPO must
    FAIL naming both. RED against pre-fix code (feedback: silently ignored,
    E-TOPO OK)."""
    d = project(ptree(railx("USB-C", 9.0, 12.6, 5.27, 5.43, 5,
                            "LM5116MHX-NOPB") + fbblock()),
                parts={"LM5116MHX-NOPB": LM5116_TYPE})
    r = must_fail(etopo(d), "E-TOPO on the under-stated window",
                  "under-stated tolerance corners")
    contains(r.out, "5.227", "names the computed worst-case LOW corner")
    contains(r.out, "5.479", "names the computed worst-case HIGH corner")
    contains(r.out, "vout_min 5.27 V is ABOVE", "flags the low corner")
    contains(r.out, "vout_max 5.43 V is BELOW", "flags the high corner")


@test("E-MARGIN FAILS the same under-stated window (the headroom everyone "
      "reasons from is fiction)", kind="known_bad")
def t_feedback_understated_margin():
    """Same real fixture via --margin: even though the COMPUTED worst-low
    5.227V still clears the Pi5 brownout over 88 mOhm, the under-stated
    declared window is itself an E-MARGIN FAIL — every downstream consumer of
    the declared corners (TVS standoff, no-load OV) is reasoning from numbers
    the board cannot hold. RED against pre-fix code (feedback: ignored,
    E-MARGIN OK)."""
    d = project(ptree(railx("USB-C", 9.0, 12.6, 5.27, 5.43, 5,
                            "LM5116MHX-NOPB",
                            load_uv_threshold=4.63, ir_budget_mohm=88)
                      + fbblock()),
                parts={"LM5116MHX-NOPB": LM5116_TYPE})
    r = must_fail(margin(d), "E-MARGIN on the under-stated window",
                  "under-stated tolerance corners")
    contains(r.out, "5.227", "names the computed low corner")
    contains(r.out, "5.479", "names the computed high corner")


@test("E-TOPO refuses a PARTIAL feedback block (missing tolerance field)",
      kind="known_bad")
def t_feedback_partial_block():
    """A feedback block missing r_bottom_tol_pct is the incident in disguise
    (a partial tolerance stack under-states the corners) — LOAD ERROR, exit 2,
    never a silent narrower window."""
    d = project(ptree(railx("USB-C", 9.0, 12.6, 5.27, 5.43, 5,
                            "LM5116MHX-NOPB")
                      + fbblock(omit="r_bottom_tol_pct")),
                parts={"LM5116MHX-NOPB": LM5116_TYPE})
    r = must_fail(etopo(d), "E-TOPO on a partial feedback block", "LOAD ERROR")
    contains(r.out, "r_bottom_tol_pct", "names the missing field")


# ============================== E-OFF ======================================
# A self-contained energy source (battery/cell/pack) must document its
# de-energization path (off_control) + stored quiescent draw (quiescent_ua).
@test("E-OFF is N-A for an externally powered board (unplugging de-energizes)")
def t_off_na_external():
    """A USB-bus-powered board has no stored energy to drain -- N-A, not a
    false FAIL demanding a switch."""
    d = project(ptree(rail("OUT", 4.75, 5.25, 3.3, 3.3, 2, "LM5116MHX-NOPB"),
                      top="source_type: usb-c bus power\n"),
                parts={"LM5116MHX-NOPB": LM5116_TYPE})
    r = must_pass(offctl(d), "E-OFF on a USB-powered board")
    contains(r.out, "N-A", "N-A report")


@test("E-OFF PASSES a battery board with a master switch + declared quiescent draw")
def t_off_pass():
    """The corrected form: source_type is a battery, off_control names a master
    disconnect, quiescent_ua is a number."""
    top = ('source_type: 3S-LiPo pack\n'
           'off_control: "SW1 master slide switch in series with VBAT"\n'
           'quiescent_ua: 60\n')
    d = project(ptree(rail("PI5", 9.0, 12.6, 5, 5, 5, "LM5116MHX-NOPB"), top=top),
                parts={"LM5116MHX-NOPB": LM5116_TYPE})
    r = must_pass(offctl(d), "E-OFF on a switched battery board")
    contains(r.out, "E-OFF OK", "clean report")


@test("E-OFF FAILS THE INCIDENT: a battery board with no de-energization declared",
      kind="known_bad")
def t_off_incident():
    """usb-hub-3s-v3 (2026-07-23, external review): a 3S-LiPo board tied both
    buck EN pins active with no master switch -- the controllers idle-drain the
    pack in storage. No review asked how it is de-energized. The board declares
    a battery source but neither off_control nor quiescent_ua."""
    d = project(ptree(rail("PI5", 9.0, 12.6, 5, 5, 5, "LM5116MHX-NOPB"),
                      top="source_type: 3S-LiPo pack\n"),
                parts={"LM5116MHX-NOPB": LM5116_TYPE})
    r = must_fail(offctl(d), "E-OFF on the 3S-LiPo incident", "no off_control")
    contains(r.out, "idle-drain", "explains the pack self-drains")
    contains(r.out, "no quiescent_ua", "also flags the undeclared stored draw")


@test("E-OFF detects the battery via VBAT nets even with no source_type",
      kind="known_bad")
def t_off_incident_via_nets():
    """The detector is not source_type-only: a nets.yaml class carrying VBAT is
    enough to fire E-OFF, so a power_tree that omits source_type still can't
    duck the check."""
    d = project(ptree(rail("PI5", 9.0, 12.6, 5, 5, 5, "LM5116MHX-NOPB")),
                parts={"LM5116MHX-NOPB": LM5116_TYPE},
                nets="classes:\n  PWR_IN:\n    nets: [VBAT, VBAT_F]\n"
                     "    current: \"15 A\"\n")
    r = must_fail(offctl(d), "E-OFF via VBAT nets", "no off_control")
    contains(r.out, "VBAT", "names the battery net that triggered detection")


@test("G-VACUOUS E-OFF: a REAL battery board that declares nothing is N-A, "
      "exit 0 — and declaring nothing is the default",
      kind="vacuity", gate="power_topology.py")
def t_vacuity_E_OFF_is_N_A_on_a_battery_board_that_declares_nothing():
    """THE DECLARED BLIND SPOT (canon G-VACUOUS; the executable half of the
    `VACUITY:` block in power_topology.py's docstring).

    This fixture asserts the gate PASSES while the fact it grades — "a
    self-contained energy source has an off_control and a declared quiescent
    draw" — is FALSE. It PINS the defect; closing it should break this test,
    and the fix is then to convert it to a `known_bad`.

    `detect_energy_source` finds a battery three ways: `source_type:`, a net
    matching VBAT/BATT/PACK, or a battery word in the FILENAME plus FIRST 400
    CHARACTERS of a `01_docs/decisions/*.md`. All three are DECLARATIONS. Miss
    all three and it returns `("unknown", ...)` -> E-OFF N-A, exit 0.

    The fixture is the same 3S-LiPo incident as `t_off_incident`, which FAILS,
    with exactly one thing changed: the `source_type:` line is deleted and the
    rail is named PI5 rather than anything battery-ish. That one deletion turns
    a hard FAIL into a pass — so the gate is stricter on a board that is honest
    about carrying a cell than on one that says nothing, and saying nothing is
    the least-effort path.

    A `01_docs/decisions/` ADR is also written here that mentions the pack, to
    show the 400-character window: the mention sits past it and is not seen."""
    adr = ("# ADR-0003: power source\n\n"
           "## Context\n\n" + ("Filler prose about mechanical fit. " * 12) +
           "\n\n## Decision\n\nThe board is powered from a 3S LiPo pack.\n")
    d = project(ptree(rail("PI5", 9.0, 12.6, 5, 5, 5, "LM5116MHX-NOPB")),
                parts={"LM5116MHX-NOPB": LM5116_TYPE})
    (d / "01_docs" / "decisions").mkdir(parents=True)
    (d / "01_docs" / "decisions" / "0003-power-source.md").write_text(adr)
    check(len(adr.split("3S LiPo")[0]) > 400,
          "the fixture must place the battery mention PAST the 400-char window "
          "the scan reads, or it proves nothing about the window")

    r = must_pass(offctl(d),
                  "E-OFF on a battery board that declares nothing — THE BLIND "
                  "SPOT. If this now FAILS, E-OFF has learned to find an "
                  "undeclared cell: convert this to kind=\"known_bad\"")
    contains(r.out, "N-A", "the verdict is N-A, not a FAIL")
    not_contains(r.out, "no off_control",
                 "the de-energization contract is never reached")

    # THE CONTRAST that makes this a blind spot and not a preference: add back
    # the one declaration and the identical board becomes a hard FAIL.
    d2 = project(ptree(rail("PI5", 9.0, 12.6, 5, 5, 5, "LM5116MHX-NOPB"),
                       top="source_type: 3S-LiPo pack\n"),
                 parts={"LM5116MHX-NOPB": LM5116_TYPE})
    must_fail(offctl(d2), "the SAME board that admits to a battery",
              "no off_control")


@test("E-OFF FAILS an always-on off_control with no ADR reference",
      kind="known_bad")
def t_off_alwayson_no_adr():
    """Always-on is allowed ONLY as an explicit ADR-justified decision; a bare
    always-on (the pack self-drains, undocumented) is a FAIL even though
    quiescent_ua is declared."""
    top = ('source_type: 3S-LiPo pack\n'
           'off_control: "always-on"\n'
           'quiescent_ua: 1200\n')
    d = project(ptree(rail("PI5", 9.0, 12.6, 5, 5, 5, "LM5116MHX-NOPB"), top=top),
                parts={"LM5116MHX-NOPB": LM5116_TYPE})
    r = must_fail(offctl(d), "E-OFF on bare always-on", "no ADR reference")
    contains(r.out, "always-on", "names the offending off_control")


@test("E-OFF PASSES always-on WHEN an ADR justifies it (+ prints self-drain days)")
def t_off_alwayson_with_adr():
    """An always-on decision carrying an ADR reference passes; with
    pack_capacity_mah declared the checker prints the advisory self-drain time
    (5000mAh / 1200uA ~= 174 days)."""
    top = ('source_type: 3S-LiPo pack\n'
           'off_control: "always-on; storage self-drain accepted (ADR-0009)"\n'
           'quiescent_ua: 1200\n'
           'pack_capacity_mah: 5000\n')
    d = project(ptree(rail("PI5", 9.0, 12.6, 5, 5, 5, "LM5116MHX-NOPB"), top=top),
                parts={"LM5116MHX-NOPB": LM5116_TYPE})
    r = must_pass(offctl(d), "E-OFF on ADR-justified always-on")
    contains(r.out, "E-OFF OK", "clean report")
    contains(r.out, "self-drain", "prints the advisory self-drain time")


# ==================================== LINEAR REGULATORS (E-TOPO, 2026-07-27)
# THE DEFECT, reported by the pluto-cal-switch agent. `normalize_type()`
# accepted only buck / boost / buck_boost while `converter:` was REQUIRED on
# every rail, so an LDO-only board had NO legal way to declare its power tree:
# naming the LDO raised
#     "converter 'ME6211C33M5G-N' ... type 'ldo_regulator_fixed_3v3' does not
#      classify as buck/boost/buck_boost"
# and exited 2. THE ONLY ROUTE TO A GREEN E-TOPO WAS TO DELETE power_tree.yaml,
# which returned N-A and exit 0 — a gate grading nothing and printing OK, the
# M-COVER class, inside the gate battery that exists to police it.
#
# MEASURED on the fleet the day it was fixed (E-TOPO run over every project,
# before vs after):
#   pluto-cal-switch            exit 2      -> OK, 1/1 rails, 1/1 converters
#   smc0985-cooksense           N-A exit 0  -> FAIL 0/1 (`rails: []` + a
#                                              `linear_rails:` key the checker
#                                              ignores BY DESIGN, 6 rails)
#   crow-recorder-central       OK exit 0   -> FAIL, 3 of 4 converters ungraded
#   crow-recorder-central-v2    OK exit 0   -> FAIL, 1 of 3 converters ungraded
#   usb-hub-3s                  N-A exit 0  -> FAIL 0/2 — THE BOARD THIS GATE
#                                              WAS WRITTEN FOR has no
#                                              power_tree.yaml, so E-TOPO had
#                                              never once graded the IP6559
#                                              buck-boost that motivated it
# Four boards were reading green over a power tree nothing had looked at.

LDO_TYPE = "ldo_regulator_fixed_3v3"      # the real pluto-cal-switch string
# the real ME6211C33M5G-N numbers: V14 p.8 dropout 120 mV @100 mA, SOT-23 300 mW
ME6211 = {"type": LDO_TYPE, "dropout_mv": 120, "pdiss_max_mw": 300}


@test("E-TOPO PASSES the pluto-cal-switch LDO rail: 4.4-5.25V in, 3.3V out")
def t_linear_pass():
    """THE CALIBRATION for LINEAR, using the real part.yaml `type:` string and
    the real datasheet bounds. Vout_max 3.366 < Vin_min 4.40 ALWAYS, so the
    requirement is STEP-DOWN, and a linear pass element is a legitimate
    implementation of it. Headroom 1034 mV vs a 120 mV dropout; PD
    (5.25-3.234)*0.1 = 202 mW vs a 300 mW package = 67%.
    RED-VERIFIED against pre-fix code (git show 5054b07:...power_topology.py):
    normalize_type() returned None for 'ldo_regulator_fixed_3v3', so this
    exited 2 with a LOAD ERROR and must_pass went RED."""
    d = project(ptree(rail("3V3", 4.40, 5.25, 3.234, 3.366, 0.10,
                           "ME6211C33M5G-N", eff=1.0)),
                parts={"ME6211C33M5G-N": ME6211})
    r = must_pass(etopo(d), "E-TOPO on the pluto LDO rail")
    contains(r.out, "required=BUCK", "still DERIVES the step-down requirement")
    contains(r.out, "declared=LINEAR", "reads the LDO as a linear pass element")
    contains(r.out, "1034 mV", "reports the measured headroom")
    contains(r.out, "202 mW", "reports the measured dissipation")
    contains(r.out, "E-TOPO OK", "clean report")


@test("E-TOPO FAILS a linear regulator with too little headroom (DROPOUT)",
      kind="known_bad")
def t_linear_dropout_fail():
    """The passing rail broken in exactly ONE way: Vin_min drops to 3.40 V, so
    the headroom is 34 mV against a 120 mV dropout and the rail falls out of
    regulation at the low input corner. The topology derivation still says
    BUCK and would still have said PASS — which is the point: this failure
    mode is INVISIBLE to Vin-vs-Vout, so a LINEAR class that only checked
    topology would be a new silent skip."""
    d = project(ptree(rail("3V3", 3.40, 5.25, 3.234, 3.366, 0.10,
                           "ME6211C33M5G-N", eff=1.0)),
                parts={"ME6211C33M5G-N": ME6211})
    r = must_fail(etopo(d), "E-TOPO on an LDO in dropout", "DROPOUT")
    contains(r.out, "required=BUCK",
             "the topology derivation ALONE would have passed this rail")
    contains(r.out, "120 mV", "names the dropout it was graded against")


@test("E-TOPO FAILS a linear regulator that cooks its package (DISSIPATION)",
      kind="known_bad")
def t_linear_dissipation_fail():
    """The passing rail broken in exactly ONE way: 0.30 A instead of 0.10 A.
    PD = (5.25-3.234)*0.3 = 605 mW into a SOT-23 rated 300 mW. Again invisible
    to the topology derivation. This is the boundary the ME6211 part.yaml
    described in PROSE ('ABOVE ~120 mA THIS PART IS WRONG') and which nothing
    could read until dropout_mv/pdiss_max_mw became fields."""
    d = project(ptree(rail("3V3", 4.40, 5.25, 3.234, 3.366, 0.30,
                           "ME6211C33M5G-N", eff=1.0)),
                parts={"ME6211C33M5G-N": ME6211})
    r = must_fail(etopo(d), "E-TOPO on an over-dissipating LDO", "DISSIPATION")
    contains(r.out, "605 mW", "reports the computed dissipation")
    contains(r.out, "300 mW", "names the package rating it exceeded")


@test("E-TOPO FAILS a linear regulator on a rail that needs to STEP UP",
      kind="known_bad")
def t_linear_cannot_boost():
    """A linear pass element cannot step up. 3.0-4.2 V in, 5 V out derives
    BOOST, and an LDO physically cannot deliver it — the cannot-meet-Vout half
    of the verdict, preserved for the new class."""
    d = project(ptree(rail("5V", 3.0, 4.2, 5, 5, 0.1, "ME6211C33M5G-N")),
                parts={"ME6211C33M5G-N": ME6211})
    r = must_fail(etopo(d), "E-TOPO on an LDO asked to boost", "cannot meet")
    contains(r.out, "cannot step up", "explains the physics")


@test("E-TOPO FAILS a linear regulator whose Vin envelope OVERLAPS Vout",
      kind="known_bad")
def t_linear_overlap_is_dropout():
    """Vin 3.0-5.25 V, Vout 3.234-3.366 V: the envelope overlaps, so the
    derivation says BUCK_BOOST. For a linear part that means the input sags
    into and below the output somewhere in the declared range — it drops out.
    This must not be waved through as 'well, it is step-down most of the
    time'."""
    d = project(ptree(rail("3V3", 3.0, 5.25, 3.234, 3.366, 0.1,
                           "ME6211C33M5G-N")),
                parts={"ME6211C33M5G-N": ME6211})
    r = must_fail(etopo(d), "E-TOPO on an LDO with an overlapping Vin",
                  "cannot meet")
    contains(r.out, "BUCK_BOOST", "names the derived requirement")


@test("a LINEAR rail with NO dropout/dissipation bounds is a hard error, not a "
      "pass", kind="known_bad")
def t_linear_unbounded_is_an_error():
    """M-COVER, applied to the fix itself. If a linear rail could be declared
    without bounds, `converter: <any LDO>` would become a NEW route to a green
    E-TOPO over a rail the gate grades nothing about — the same defect one
    level down. The error must NAME both missing fields."""
    d = project(ptree(rail("3V3", 4.40, 5.25, 3.234, 3.366, 0.10,
                           "ME6211C33M5G-N")),
                parts={"ME6211C33M5G-N": LDO_TYPE})     # type only, no bounds
    r = must_fail(etopo(d), "E-TOPO on an unbounded linear rail", "LOAD ERROR")
    contains(r.out, "dropout_mv", "names the first missing field")
    contains(r.out, "pdiss_max_mw", "names the second missing field")


@test("a rail may OVERRIDE the part's package rating with a board derating")
def t_linear_rail_override():
    """`pdiss_max_mw` on the part is the package rating; a board with a hot
    ambient or no copper under the part may state a lower one on the rail.
    The override must be USED, not ignored — 202 mW passes the part's 300 mW
    and must FAIL a rail-declared 150 mW."""
    pt = ("rails:\n"
          "  - name: 3V3\n    vin_min: 4.40\n    vin_max: 5.25\n"
          "    vout_min: 3.234\n    vout_max: 3.366\n    iout_max_A: 0.10\n"
          "    converter: ME6211C33M5G-N\n    eff: 1.0\n"
          "    pdiss_max_mw: 150\n")
    d = project(pt, parts={"ME6211C33M5G-N": ME6211})
    r = must_fail(etopo(d), "E-TOPO with a rail-level derating", "DISSIPATION")
    contains(r.out, "150 mW", "grades against the RAIL's number, not the part's")


@test("the OVER-ENGINEERING verdict is unchanged by the LINEAR class",
      kind="known_bad")
def t_overengineering_survives_linear():
    """The check exists to catch buck_boost-where-buck-suffices (usb-hub-3s,
    2026-07-22). Adding a fourth converter class must not weaken it. This is
    the incident fixture re-asserted AFTER the change: a 5V-only output below
    a 9V floor, with the real IP6559 `type:` string."""
    d = project(ptree(rail("USB-C", 9.0, 12.6, 5, 5, 5, "IP6559-C")),
                parts={"IP6559-C": IP6559_TYPE})
    r = must_fail(etopo(d), "E-TOPO on the IP6559 incident", "over-engineered")
    contains(r.out, "buck suffices", "still names the sufficient topology")
    # ...and a LINEAR part must never be read as over-engineered: it is
    # strictly LESS capable than a buck, so its risk is under-capability.
    d2 = project(ptree(rail("3V3", 4.40, 5.25, 3.234, 3.366, 0.10,
                            "ME6211C33M5G-N", eff=1.0)),
                 parts={"ME6211C33M5G-N": ME6211})
    r2 = must_pass(etopo(d2), "E-TOPO on a linear step-down")
    check("over-engineered" not in r2.out,
          "a linear regulator was reported as over-engineered")


# ------------------- the silent-skip route itself (M-COVER, 2026-07-27) -----
@test("E-TOPO FAILS a project with converters in 02_parts and NO power_tree.yaml",
      kind="known_bad")
def t_no_power_tree_with_converters_fails():
    """THE ROUTE-AROUND. Deleting power_tree.yaml returned "N-A ... the
    power-tree gate is optional" and exit 0 — the gate asked the artifact under
    grade whether there was anything to grade, and believed it. 02_parts is a
    DIFFERENT artifact written by a different stage (canon M1), so it can
    contradict. Measured: usb-hub-3s, the board whose IP6559 buck-boost
    MOTIVATED this gate, has no power_tree.yaml and had never been graded.
    RED-VERIFIED against pre-fix code: exits 0 with 'N-A'."""
    d = project(None, parts={"IP6559-C": IP6559_TYPE,
                             "LM5116MHX-NOPB": LM5116_TYPE})
    r = must_fail(etopo(d), "E-TOPO with no power tree but two converters",
                  "0/2 converters graded")
    contains(r.out, "IP6559-C", "names the ungraded converter")
    contains(r.out, "LM5116MHX-NOPB", "names both, not just the first")


@test("E-TOPO FAILS `rails: []` while 02_parts declares a converter",
      kind="known_bad")
def t_empty_rails_with_converter_fails():
    """The smc0985-cooksense shape: `rails: []` plus a `linear_rails:` key the
    checker ignores BY DESIGN, six documented rails, and "E-TOPO N-A" exit 0.
    An empty rails list is a ZERO DENOMINATOR, which canon M-COVER makes a
    FAIL outright."""
    d = project("rails: []\nlinear_rails:\n  - {name: 3V3, element: AMS1117}\n",
                parts={"AMS1117-3.3": "ldo_3v3_1a"})
    r = must_fail(etopo(d), "E-TOPO on an empty rails list with an LDO present",
                  "0/1 converters graded")
    contains(r.out, "AMS1117-3.3", "names the converter nothing graded")


@test("E-TOPO FAILS when SOME converters are declared and others are not",
      kind="known_bad")
def t_partial_coverage_fails():
    """The crow-recorder-central shape, and the subtler one: two switching
    rails ARE declared and pass, while two LDO rails live only in a COMMENT.
    E-TOPO printed 'OK: 2 rail(s) topology-correct' over half a power tree.
    The verdict must carry the 02_parts denominator, not only the rails it was
    handed."""
    d = project(ptree(rail("3V3", 4.75, 5.25, 3.32, 3.32, 0.4,
                           "AP61102Z6-7")),
                parts={"AP61102Z6-7": "buck_regulator_sync",
                       "TCR2LF18": "ldo",
                       "XC6227C331PR-G": "ldo_regulator_fixed_3v3_low_noise"})
    r = must_fail(etopo(d), "E-TOPO with two undeclared LDOs",
                  "UNGRADED CONVERTERS")
    contains(r.out, "2 of 3", "reports the coverage shortfall as a fraction")
    contains(r.out, "TCR2LF18", "names the first ungraded part")
    contains(r.out, "XC6227C331PR-G", "names the second")


@test("E-TOPO N-A survives when the board genuinely has no converter")
def t_na_is_still_reachable():
    """The check must not become unfailable-in-reverse. A board with no
    converter part at all still gets N-A and exit 0 — and now SAYS what it
    checked to conclude that, with a 0/0 denominator."""
    d = project(None, parts={"AO3401A": "pfet_30v_4a",
                             "TPS259573DSGR": "efuse_ovlo"})
    r = must_pass(etopo(d), "E-TOPO on a converter-free board")
    contains(r.out, "0/0", "prints a denominator even for N-A")
    contains(r.out, "02_parts", "names the artifact it checked to say N-A")


@test("a LINEAR rail's input current is Iout, not Pout/eff/Vin")
def t_linear_input_current_model():
    """A switching rail draws CONSTANT POWER; a linear rail draws CONSTANT
    CURRENT. Running a linear rail through the switching formula understates
    its trunk current by Vout/Vin. pluto-cal-switch's power_tree.yaml carried
    `eff: 1.0` with a comment claiming that made the derived input current
    equal the output current — it does not: 3.3*0.1/4.4 = 0.075 A for a rail
    that draws 0.100 A, 25% light, in the direction that under-sizes copper.
    RED-VERIFIED: pre-fix this rail could not be declared at all, and with the
    switching formula it reports 0.1 A only by accident of rounding, so the
    fixture uses a rail where the two differ in the FIRST decimal."""
    d = project(ptree(rail("3V3", 4.40, 5.25, 3.234, 3.366, 0.50,
                           "ME6211C33M5G-N", eff=1.0)),
                parts={"ME6211C33M5G-N": {"type": LDO_TYPE, "dropout_mv": 120,
                                          "pdiss_max_mw": 2000}})
    r = must_pass(etopo(d), "E-TOPO input-current model for a linear rail")
    # switching formula would give 3.366*0.5/1.0/4.40 = 0.38 A; correct is 0.50
    contains(r.out, "0.5 A at Vin_min",
             "sums Iout directly for a linear rail (0.4 A would be the "
             "constant-power answer)")


# ================ the FUSE number is a CURRENT, not a part-number substring ===
#: the exact line crow-recorder-central-v2 ships at ORDER_README.md:7. The true
#: fuse rating (2 A) is on the same line as two decoys that both end in a digit
#: followed by 'A'.
_INCIDENT_README_LINE = ("AO3401A reverse-polarity FET (Q1) + SMAJ5.0A (D1) "
                         "+ 2A fuse (F_IN).")


@test("E-TOPO reads the FUSE rating, not a part number that ends in a digit "
      "and an A", kind="known_bad")
def t_fuse_rating_is_not_a_part_number():
    """MEASURED 2026-07-27: E-TOPO printed

        OVER-BUILT (advisory): fuse rated 3401 A is >2x the derived need 0.7 A

    on crow-recorder-central-v2. NO SUCH FUSE EXISTS. `_first_amps` was
    `([\\d.]+)\\s*A` with no boundary on either side, so on the shipped
    ORDER_README line above it matched `AO3401A` — the reverse-polarity FET's
    part number — as "3401" + "A". The real rating, 2 A, is four tokens later
    on the SAME LINE, and `SMAJ5.0A` reads as 5.0 A by the identical
    mechanism. This is the adjacent-property error inside a gate's own output:
    it measured a substring NEAR the number it needed.

    A gate that prints nonsense trains its reader to skim, which is how real
    findings get missed — so the assertion is both halves: the true rating is
    read, AND neither decoy is.

    RED-VERIFIED 2026-07-27 by restoring `_NUM_A = re.compile(r"([\\d.]+)\\s*A",
    re.I)`: this test reports `fuse rating: 3401 A read out of a part number
    — got '3401', want '2'`. Restored byte-identical afterwards.
    """
    import importlib
    sys.path.insert(0, str(SCRIPTS))
    pt = importlib.import_module("power_topology")
    got = pt._first_amps(_INCIDENT_README_LINE)
    check(got == 2.0,
          f"fuse rating: {got} A read out of a part number — got {got!r}, "
          f"want 2.0, from: {_INCIDENT_README_LINE}")
    # the decoys, each on its own so the failure names which one leaked
    check(pt._first_amps("AO3401A reverse-polarity FET (Q1)") is None,
          "'AO3401A' read as a current")
    check(pt._first_amps("SMAJ5.0A (D1)") is None, "'SMAJ5.0A' read as a current")
    check(pt._first_amps("F_IN opens at 2 A") == 2.0, "'2 A' must still read")
    check(pt._first_amps("PWR_IN 7 A worst case") == 7.0,
          "a qualified netclass current must still read")
    check(pt._first_amps("2Ah battery") is None,
          "'2Ah' is a charge, not a current")


@test("the fuse advisory NAMES the file and line its number came from")
def t_fuse_advisory_names_its_source():
    """G-INPUT applied to a single number: `fuse rated 3401 A` was
    unfalsifiable from the output alone — nothing said where 3401 came from,
    so a reader could only shrug. The line is now quoted back."""
    d = project(ptree(rail("5V", 11.0, 12.6, 5, 5, 0.2, "LM5116MHX-NOPB")),
                parts={"LM5116MHX-NOPB": "buck"},
                nets="classes:\n  PWR_IN:\n    nets: [VIN]\n"
                     "    current: \"2 A\"\n")
    (d / "01_docs").mkdir(exist_ok=True)
    (d / "01_docs" / "ORDER_NOTES.md").write_text(
        f"# order\n{_INCIDENT_README_LINE}\n")
    r = etopo(d)
    contains(r.out, "fuse rated 2 A", "the true rating from the incident line")
    contains(r.out, "ORDER_NOTES.md",
             "the advisory must name the file it read the number out of")
    contains(r.out, "AO3401A",
             "and quote the LINE, so the reader can check the reading")
    not_contains(r.out, "fuse rated 3401",
                 "the part number must not be reported as the rating")


@test("E-TOPO does not round a sub-amp trunk current to a number that is not "
      "the one it compared", kind="known_bad")
def t_small_trunk_current_is_legible():
    """THE DEFECT (2026-07-28). The derived input-trunk current printed at
    `.1f`, so 0.126 A rendered as `0.1 A` and anything under 0.05 A rendered as
    `0.0 A` — a worst-case trunk current of ZERO, which is exactly the number a
    reader does not question. Every mA-class rail on a low-power board read the
    same, while the DECLARED current on the very same line was already printed
    at `{:g}`: one sentence, two differently-rounded numbers.

    THE FIX KEEPS >= 1 A EXACTLY AS IT WAS, on purpose. A display change that
    moves every figure already quoted in a sealed verification report is not a
    fix; only the band where one decimal has no resolution left changes.

    RED-VERIFIED 2026-07-28 (git-swap, tests/README step 3): with git HEAD's
    power_topology.py swapped back in, the line reads
    `input-trunk worst case: 0.1 A` and this fails on `the derived current is
    printed at full precision: got 0.1 A, want ~0.126 A`.
    """
    d = project(ptree(rail("3V3", 4.5, 5.5, 3.3, 3.3, 0.1, "FAKEBUCK", eff=0.9),
                      rail("1V8", 4.5, 5.5, 1.8, 1.8, 0.1, "FAKEBUCK", eff=0.9)),
                parts={"FAKEBUCK": "buck_converter"})
    r = etopo(d)
    m = re.search(r"input-trunk worst case: ([\d.]+) A", r.out)
    check(m, f"no input-trunk line in:\n{r.out}")
    val = float(m.group(1))
    check(abs(val - 0.126) < 0.003,
          f"the derived current is printed at full precision: got {val} A, "
          f"want ~0.126 A (`.1f` rendered it 0.1)")
    not_contains(r.out, "worst case: 0.1 A",
                 "a sub-amp trunk current flattened to one decimal")
    # the ADJACENT property, re-measured every run: an amp-scale figure must
    # NOT move, or this fix silently rewrites every archived report.
    d2 = project(ptree(rail("USB-A", 9.0, 12.6, 5, 5, 6, "LM5116MHX-NOPB"),
                       rail("USB-C", 9.0, 12.6, 5, 5, 5, "LM5116MHX-NOPB")),
                 parts={"LM5116MHX-NOPB": LM5116_TYPE})
    contains(etopo(d2).out, "worst case: 6.8 A",
             "the amp-scale rendering is unchanged")


@test("E-TOPO's UNDER-BUILT finding cannot quote the SAME number as both the "
      "declared trunk and the derived need", kind="known_bad")
def t_underbuilt_numbers_do_not_collide():
    """The half that makes the formatting a CORRECTNESS bug rather than a
    cosmetic one. The comparison runs on the real float, the report did not:
    a 0.1 A declared trunk against a 0.126 A derived need is a true
    UNDER-BUILT, and at `.1f` the derived side printed `0.1` — so the finding
    read `declared trunk current 0.1 A ... is below the derived worst case
    0.1 A`. A failure whose own evidence says the two quantities are equal is
    a failure a reader will overrule.

    RED-VERIFIED 2026-07-28 (git-swap): pre-fix this fails with `UNDER-BUILT
    quotes the SAME number twice — '0.1' vs '0.1'`.
    """
    d = project(ptree(rail("3V3", 4.5, 5.5, 3.3, 3.3, 0.1, "FAKEBUCK", eff=0.9),
                      rail("1V8", 4.5, 5.5, 1.8, 1.8, 0.1, "FAKEBUCK", eff=0.9),
                      top="input_trunk_class: VIN\n"),
                parts={"FAKEBUCK": "buck_converter"},
                nets="classes:\n  VIN:\n    nets: [VIN]\n"
                     "    current: \"0.1 A\"\n")
    r = etopo(d)
    contains(r.out, "UNDER-BUILT", "the shortfall is found at all")
    m = re.search(r"declared trunk current ([\d.]+) A.*?derived worst "
                  r"case ([\d.]+) A", r.out, re.S)
    check(m, f"UNDER-BUILT finding is not parseable:\n{r.out}")
    check(m.group(1) != m.group(2),
          f"UNDER-BUILT quotes the SAME number twice — {m.group(1)!r} vs "
          f"{m.group(2)!r}; the reader cannot see the shortfall it is about")


if __name__ == "__main__":
    sys.exit(main())
