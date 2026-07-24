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


if __name__ == "__main__":
    sys.exit(main())
