#!/usr/bin/env python3
"""POWER-TREE gate battery (E-TOPO / E-MARGIN / E-OFF) — three mechanical
commission-stage checks DERIVED from 03_src/rules/power_tree.yaml, so
converter topology, output-setpoint load margin, and de-energization are
gated numbers, not things a reviewer has to remember to eyeball.

  E-TOPO  - converter topology DERIVED from Vin-vs-Vout (this file's original
            job).                                        [default invocation]
  E-MARGIN- a regulated rail feeding a KNOWN load must clear the load's
            brownout with real IR headroom.                       [--margin]
  E-OFF   - a self-contained energy source (battery/cell/pack) must document
            its de-energization path + bounded stored quiescent draw.
                                                             [--off-control]

WHY E-TOPO EXISTS
-----------------
usb-hub-3s (2026-07-22) was built with an IP6559 BUCK-BOOST SoC for its USB-C
port plus a 16 A input trunk — but the USB-C output is 5 V ONLY and the battery
is 9-12.6 V, so Vout(5 V) < Vin_min(9 V) ALWAYS: a simple step-down BUCK
suffices. The buck-boost (+ 4 external FETs + 30 V-FET/TVS coordination +
compact hot-loop congestion + a 16 A trunk) existed only to support >5 V PDOs
the spec never required. Root cause: D-SPEC pinned the CURRENT ("5 A compliant")
but never the OUTPUT VOLTAGE RANGE, and the converter TOPOLOGY was interpreted,
not DERIVED from Vin vs Vout. This gate closes that loop.

WHY E-MARGIN EXISTS
-------------------
usb-hub-3s-v3 (2026-07-23, external review): a rail regulated to 4.97 V fed a
Raspberry Pi 5 (undervoltage detect ~4.63 V) at 5 A - leaving only
(4.97-4.63)/5 A ~= 68 mOhm of TOTAL budget for board + connector + cable IR
drop. A real e-marked 5 A USB-C cable + two connector pairs alone exceeds that,
so the Pi browns out under load. BOTH zero-context red-team reviews COMPUTED the
4.97 V setpoint and neither flagged the thin margin. E-MARGIN makes the headroom
a number: for a rail that declares its load's undervoltage threshold, the
setpoint headroom must buy more series resistance than the delivery path will
burn at Imax (with margin). The cable/connector ASSUMPTION is a judgment call
([H], red-team checklist); the arithmetic once assumed is [M] here.

WHY THE feedback: TOLERANCE WINDOW EXISTS (E-TOPO + E-MARGIN)
------------------------------------------------------------
usb-hub-3s-v3 (2026-07-23, external review): the gate accepted AUTHOR-DECLARED
vout_min/vout_max, and the author computed the window from ONLY the regulator
reference tolerance (Vref +/-1.5%) — omitting the feedback DIVIDER resistors'
tolerances. Real window for the USB-C rail (Vref 1.215 +/-1.5%, R12 4.12k
+/-0.1%, R13 1.21k +/-1%): 5.227-5.479 V; declared: 5.27-5.43 V. Every check
downstream of the window (E-MARGIN headroom, the TVS-standoff comparison) was
graded against corners the board cannot hold. The OPTIONAL per-rail
`feedback:` block makes the corners COMPUTED, not declared:

  feedback: {vref, vref_tol_pct, r_top_ohm, r_top_tol_pct,
             r_bottom_ohm, r_bottom_tol_pct,
             r_top_tcr_ppm_per_C, r_bottom_tcr_ppm_per_C,
             resistor_temperature_delta_C}
  vout = vref * (1 + r_top/r_bottom)
  total resistor tolerance = initial tolerance + |TCR| * |delta temperature|
  computed low  = vref_min * (1 + r_top_min / r_bottom_max) + Ifb_min*Rtop_min
  computed high = vref_max * (1 + r_top_max / r_bottom_min) + Ifb_max*Rtop_max

When present: a DECLARED window NARROWER than the computed one is a FAIL in
both E-TOPO and E-MARGIN (the author under-stated the corners), and E-MARGIN
grades headroom from the COMPUTED worst-low, not the declared vout_min.
Absent -> behavior unchanged (declared window taken at face value).

WHY E-OFF EXISTS
----------------
usb-hub-3s-v3 (2026-07-23, external review): a 3S-LiPo board tied both buck EN
pins active with no master switch - so the controllers idle-drain the pack the
whole time it sits in storage. No review asked "how is it de-energized / does it
self-drain?". E-OFF makes a battery board DECLARE its de-energization path
(off_control) and its stored quiescent draw (quiescent_ua); an always-on design
must be an explicit ADR decision, never a silent default. Whether the declared
mechanism actually exists in the netlist, and whether the drain is acceptable
for the pack, are [H] (the mandatory input-protection ADR + the red-team
checklist).

THE PHYSICS (deterministic — this is the whole check)
-----------------------------------------------------
  Vout_max < Vin_min  -> BUCK        (step-down only)
  Vout_min > Vin_max  -> BOOST       (step-up only)
  ranges overlap      -> BUCK_BOOST  (must do both)

That derivation gives the step-down/step-up REQUIREMENT. The converter part
supplies an IMPLEMENTATION of it, and the two are graded against each other:
  - MORE capable than needed (buck_boost where buck suffices) = OVER-ENGINEERING
    -> FAIL. Waiver-able only with an ADR justifying the extra capability
    (e.g. "future 20 V PD"); the waiver is applied by policy_audit's E-TOPO row.
  - LESS capable (buck where boost is required) -> FAIL: cannot meet Vout.

WHY `LINEAR` EXISTS (2026-07-27) — AND WHY IT IS NOT A FOURTH TOPOLOGY
---------------------------------------------------------------------
Until this change `normalize_type()` accepted only buck / boost / buck_boost,
while `converter:` was REQUIRED on every rail. An LDO-only board therefore had
no legal way to declare its power tree at all: naming the LDO raised
"type 'ldo_regulator_fixed_3v3' does not classify as buck/boost/buck_boost"
and exited 2. **The only way to a green E-TOPO was to DELETE power_tree.yaml**,
which returns N-A and exit 0 — a gate silently grading nothing, the exact
M-COVER class this gate battery exists to police, living inside our own gate.

Three fleet boards were already routing around it when this was fixed:
  * smc0985-cooksense       `rails: []` plus a parallel `linear_rails:` key
                            the checker IGNORES BY DESIGN — six documented
                            rails, all ungraded, and E-TOPO printing N-A.
  * crow-recorder-central   two LDO rails (1V8 TCR2LF18, 3V3A XC6227) present
                            only as a comment block; two of four rails graded.
  * crow-recorder-central-v2  the same two rails, the same comment.
`pluto-cal-switch` declared its LDO rail truthfully instead, took the exit 2,
and reported the gap — which is how it got fixed.

A linear regulator is NOT a fourth topology. It is one IMPLEMENTATION of the
step-down requirement, so it is derived and graded like this:

  required BUCK        + LINEAR -> the requirement is met; now grade the two
                                   things that actually kill a linear part
  required BOOST       + LINEAR -> FAIL: a linear regulator cannot step up
  required BUCK_BOOST  + LINEAR -> FAIL: Vin dips into/below Vout, so the part
                                   drops out of regulation somewhere in the
                                   declared envelope

and "the two things that actually kill a linear part" are DROPOUT and
DISSIPATION, both of which the buck/boost derivation is blind to:

  headroom = vin_min - vout_max          must be >= dropout_mv
  PD       = (vin_max - vout_min) * iout must be <= pdiss_max_mw

Both numbers are REQUIRED for a LINEAR rail, from the converter's `part.yaml`
(`dropout_mv:`, `pdiss_max_mw:`) or overridden on the rail. Making them
optional would recreate the defect one level down: a rail that declares a
linear converter and no bounds is a rail this gate cannot grade, and per
canon M-COVER that is a FAIL, not a pass. `pluto-cal-switch` had both numbers
already — as a prose comment nothing could read (PD 195 mW into a SOT-23 rated
300 mW). That is the ADR-0004 shift-left move: prose becomes a field.

The over-engineering verdict is UNCHANGED and still fires: buck_boost where
buck or boost suffices is still a FAIL. LINEAR adds no new over-capability
axis — a linear regulator is strictly less capable than a buck, so its risk is
under-capability, which is what dropout and dissipation measure.

INPUT-CURRENT (advisory, always PRINTED)
----------------------------------------
Worst-case input trunk current = Sum(vout_max * iout_max)/eff / Vin_min across
all rails sharing the input. Always printed so the 16 A-vs-7 A class of mismatch
is visible. If an input trunk class current is declarable UNAMBIGUOUSLY (nets.yaml
netclass named as the input trunk, or `input_trunk_class:` in power_tree.yaml)
and it is MATERIALLY BELOW the derived worst case, that is under-built copper ->
FAIL. A trunk/fuse sized > 2x the derived need is OVER-built -> advisory FLAG
(the usb-hub-3s incident on the current axis), never a false-FAIL.

USAGE
-----
  power_topology.py PROJECT_DIR
      E-TOPO: grade every rail's converter topology in
      PROJECT_DIR/03_src/rules/power_tree.yaml.
      Exit 0 all-pass, 1 on any topology/under-built FAIL, 2 on a load/config
      error (bad schema, missing vout range). No power_tree.yaml -> N-A, exit 0.

  power_topology.py PROJECT_DIR --margin
      E-MARGIN: for every rail that declares load_uv_threshold, grade the
      output-setpoint headroom against the delivery IR drop at Imax. A rail
      declares its worst case with ir_budget_mohm (board+connector+cable series
      resistance); a rail that omits it is graded against the ir_floor_mohm
      floor (default 100 mOhm). Exit 0 pass/N-A, 1 on any FAIL, 2 on a load
      error.

  power_topology.py PROJECT_DIR --off-control
      E-OFF: if a self-contained energy source (battery/cell/pack) is detected
      (source_type:, or VBAT/BATT/PACK nets, or a battery ADR), require
      off_control: + quiescent_ua: to be declared; an always-on off_control with
      no ADR reference is a FAIL. Exit 0 pass/N-A, 1 on any FAIL.

  power_topology.py --derive VIN_MIN VIN_MAX VOUT_MIN VOUT_MAX
      Print the derived topology for an ad-hoc range and exit 0 (calibration).

  --power-tree PATH / --nets PATH   override the auto-located files.

Netlist-independent: reads part.yaml `type:` + the rule YAMLs; runs on any
python3 with PyYAML.

VACUITY: (canon G-VACUOUS — the input class on which this gate PASSES while the
fact it grades is FALSE, fixtured by `t1_power_topology.py`
`t_vacuity_E_OFF_is_N_A_on_a_battery_board_that_declares_nothing`.)

E-OFF grades "a self-contained energy source has an off_control and a declared
quiescent draw". `detect_energy_source` finds that source three ways: the
`source_type:` field of `03_src/rules/power_tree.yaml`, a net matching
VBAT/BATT/PACK, or a battery-ish word in the FILENAME PLUS FIRST 400 CHARACTERS
of a `01_docs/decisions/*.md`. When none hits it returns `("unknown", ...)` and
E-OFF reports **N-A, exit 0**.

So a board that really does carry a cell and declares no `source_type:`, names
its rail something other than VBAT/BATT/PACK, and mentions the cell only past
character 400 of an ADR (or in `BRIEF.md` / `ARCHITECTURE.md`, neither of which
is scanned) gets a silent pass on the whole de-energization contract. The
conservatism is deliberate and the code says so; what is undeclared is that the
escape is REACHABLE BY DEFAULT — declaring nothing is the least effort path.

MEASURED, and this is the correction to a report that had it the other way
round: the ADR scan is `re.search(r"batter|lipo|li[-_ ]?ion|\bcell\b|\bpack\b|
discharge", head, re.I)` and it is NEGATION-BLIND — the sentence "this board has
no battery backup" returns `("battery", "ADR ...")`. That direction makes E-OFF
STRICTER (exit 1 demanding off_control on a USB-only board), so it is a FALSE
FAIL, not a false pass, and it is not this gate's vacuity condition. The
`_BATT_RE` at module level never sees prose at all; it is matched only against
`power_tree.yaml`'s own `source_type:` string.
"""
import argparse
import glob
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - environments here ship PyYAML
    yaml = None

# release ordering has ONE home in this repo (canon M-WIDTH)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]
                       / "jlcpcb-fab" / "scripts"))
import release_index as _relidx                                # noqa: E402

BUCK, BOOST, BUCK_BOOST = "BUCK", "BOOST", "BUCK_BOOST"
#: LINEAR is an IMPLEMENTATION of a step-down requirement, never a derived
#: requirement — derive_topology() can never return it. See the module
#: docstring.
LINEAR = "LINEAR"


class LoadError(Exception):
    """A schema/config problem — distinct from a topology FAIL."""


# --------------------------------------------------------------------------
# topology derivation — the whole physics
def derive_topology(vin_min, vin_max, vout_min, vout_max):
    """Return the REQUIRED converter topology for a rail's Vin/Vout envelope."""
    if vout_max < vin_min:
        return BUCK
    if vout_min > vin_max:
        return BOOST
    return BUCK_BOOST


#: a LINEAR pass element, in the spellings the fleet actually uses:
#: `ldo`, `ldo_regulator_fixed_1v8`, `ldo_regulator_fixed_3v3_low_noise`,
#: `ldo_3v3_1a`, and the long forms. Checked AFTER buck/boost so a
#: hypothetical "ldo_or_buck" part cannot be silently downgraded to linear.
_LINEAR_RE = re.compile(r"ldo|linear|low[-_ ]?dropout", re.I)


def normalize_type(raw):
    """part.yaml `type:` string -> canonical converter class, or None if the
    type does not classify (a load switch, an eFuse, a FET: not converters).

    Buck+boost in any spelling (buck_boost, buck-boost, buckboost,
    pd_source_buckboost_soc) -> BUCK_BOOST; then buck -> BUCK; boost -> BOOST;
    then a LINEAR pass element -> LINEAR. Switching spellings are tested first
    on purpose: BUCK_BOOST/BUCK/BOOST name a CAPABILITY and LINEAR names an
    implementation, so if a string somehow claims both, the capability claim is
    the one that must be graded."""
    if raw is None:
        return None
    s = str(raw).lower()
    has_buck = "buck" in s
    has_boost = "boost" in s
    if has_buck and has_boost:
        return BUCK_BOOST
    if has_buck:
        return BUCK
    if has_boost:
        return BOOST
    if _LINEAR_RE.search(s):
        return LINEAR
    return None


# --------------------------------------------------------------------------
# part resolution — converter <refdes or MPN> -> its part.yaml topology
def _norm_id(s):
    # Exact orderable MPNs routinely contain punctuation that is omitted from
    # filesystem-safe dossier directory names (for example Analog Devices
    # ``LTC3889IUKG#PBF`` lives in ``LTC3889IUKG-PBF``). Identity matching must
    # normalize both through the same alphanumeric form or the rail resolves by
    # MPN but M-COVER falsely reports its directory as an ungraded converter.
    return re.sub(r"[^0-9a-z]", "", str(s).lower())


#: part.yaml facts a LINEAR converter must carry so its rail can be GRADED.
#: Canon P-FACT: a part's own declared facts are executable. `dropout_mv` is
#: the datasheet MAXIMUM dropout at the part's rated output current (the
#: conservative reading — a rail may override it with the number at its own
#: iout_max_A); `pdiss_max_mw` is the package power rating, which a rail may
#: override to state a board-specific derating.
LINEAR_FACTS = ("dropout_mv", "pdiss_max_mw")


def load_part_index(proj):
    """{normalized mpn/dirname -> {dir, type, dropout_mv, pdiss_max_mw}} over
    02_parts/*/part.yaml."""
    idx = {}
    for py in sorted(glob.glob(str(Path(proj) / "02_parts" / "*" / "part.yaml"))):
        try:
            y = yaml.safe_load(Path(py).read_text(encoding="utf-8-sig")) or {}
        except Exception:
            continue
        dirname = Path(py).parent.name
        rec = {"dir": dirname, "type": y.get("type")}
        for f in LINEAR_FACTS:
            rec[f] = y.get(f)
        for key in (y.get("mpn"), dirname):
            if key:
                idx[_norm_id(key)] = rec
    return idx


def resolve_converter(converter, part_index):
    """(dirname, canonical_class, facts). Raises LoadError if the converter
    cannot be resolved to a part.yaml or its type does not classify."""
    hit = part_index.get(_norm_id(converter))
    if hit is None:
        raise LoadError(
            f"converter {converter!r} not found in 02_parts — reference it by "
            f"the part MPN or its 02_parts directory name (known: "
            f"{sorted(set(v['dir'] for v in part_index.values()))})")
    dirname, raw_type = hit["dir"], hit["type"]
    topo = normalize_type(raw_type)
    if topo is None:
        raise LoadError(
            f"converter {converter!r} ({dirname}) part.yaml type "
            f"{raw_type!r} does not classify as buck / boost / buck_boost / "
            f"linear(ldo) — the type field must name the converter class. If "
            f"this part is NOT a converter (a load switch, an eFuse, a "
            f"ferrite, a pass FET) it does not belong on a `rails:` entry: "
            f"such a stage converts nothing and E-TOPO has nothing to derive")
    return dirname, topo, {f: hit.get(f) for f in LINEAR_FACTS}


# --------------------------------------------------------------------------
# schema loading + validation
def _num(v, field, name):
    try:
        return float(v)
    except (TypeError, ValueError):
        raise LoadError(f"rail {name!r} field {field!r}={v!r} is not a number")


def _num_opt(v, field, name):
    """_num, but None passes through (an OPTIONAL numeric field)."""
    return None if v is None else _num(v, field, name)


# OPTIONAL per-rail feedback-divider block. The reference is either symmetric
# (`vref` + `vref_tol_pct`) or the datasheet's exact asymmetric
# (`vref_min` + `vref_max`) range. Divider fields are always required.
FEEDBACK_DIVIDER_FIELDS = ("r_top_ohm", "r_top_tol_pct",
                           "r_bottom_ohm", "r_bottom_tol_pct")
FEEDBACK_TCR_FIELDS = ("r_top_tcr_ppm_per_C", "r_bottom_tcr_ppm_per_C",
                       "resistor_temperature_delta_C")


def _load_feedback(raw, name):
    """Parse + validate a rail's `feedback:` block. None passes through."""
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise LoadError(f"rail {name!r} 'feedback:' must be a mapping with "
                        "divider fields and one complete reference form")
    fb = {}
    for f in FEEDBACK_DIVIDER_FIELDS:
        if f not in raw or raw[f] is None:
            raise LoadError(
                f"rail {name!r} feedback block is missing {f!r} — a "
                f"divider-tolerance window needs ALL of "
                f"{FEEDBACK_DIVIDER_FIELDS}; a "
                f"partial stack under-states the corners (the usb-hub-3s-v3 "
                f"Vref-only window, 2026-07-23)")
        fb[f] = _num(raw[f], f"feedback.{f}", name)
    symmetric = raw.get("vref") is not None or raw.get("vref_tol_pct") is not None
    asymmetric = raw.get("vref_min") is not None or raw.get("vref_max") is not None
    if symmetric == asymmetric:
        raise LoadError(f"rail {name!r} feedback needs exactly one complete "
                        "reference form: vref + vref_tol_pct OR vref_min + vref_max")
    if symmetric:
        for f in ("vref", "vref_tol_pct"):
            if raw.get(f) is None:
                raise LoadError(f"rail {name!r} feedback symmetric reference is missing {f!r}")
            fb[f] = _num(raw[f], f"feedback.{f}", name)
        if not (0 <= fb["vref_tol_pct"] < 100):
            raise LoadError(f"rail {name!r} feedback: vref_tol_pct "
                            f"{fb['vref_tol_pct']:g} must be a percentage in [0, 100)")
        fb["vref_min"] = fb["vref"] * (1 - fb["vref_tol_pct"] / 100.0)
        fb["vref_max"] = fb["vref"] * (1 + fb["vref_tol_pct"] / 100.0)
        fb["reference_form"] = "symmetric"
    else:
        for f in ("vref_min", "vref_max"):
            if raw.get(f) is None:
                raise LoadError(f"rail {name!r} feedback asymmetric reference is missing {f!r}")
            fb[f] = _num(raw[f], f"feedback.{f}", name)
        if fb["vref_min"] > fb["vref_max"]:
            raise LoadError(f"rail {name!r} feedback vref_min exceeds vref_max")
        fb["reference_form"] = "asymmetric"
    for f in ("r_top_tol_pct", "r_bottom_tol_pct"):
        if not (0 <= fb[f] < 100):
            raise LoadError(f"rail {name!r} feedback: {f} {fb[f]:g} must be a "
                            f"percentage in [0, 100)")
    if fb["vref_min"] <= 0 or fb["r_top_ohm"] <= 0 or fb["r_bottom_ohm"] <= 0:
        raise LoadError(f"rail {name!r} feedback reference and divider resistances must be positive")
    tcr_present = [raw.get(f) is not None for f in FEEDBACK_TCR_FIELDS]
    if any(tcr_present) and not all(tcr_present):
        raise LoadError(
            f"rail {name!r} feedback TCR stack needs ALL of "
            f"{FEEDBACK_TCR_FIELDS}; a partial temperature stack under-states "
            "the divider corners")
    for f in FEEDBACK_TCR_FIELDS:
        fb[f] = _num(raw.get(f, 0), f"feedback.{f}", name)
        if fb[f] < 0:
            raise LoadError(f"rail {name!r} feedback: {f} must be nonnegative")
    for side in ("top", "bottom"):
        total_pct = (fb[f"r_{side}_tol_pct"] +
                     fb[f"r_{side}_tcr_ppm_per_C"] *
                     fb["resistor_temperature_delta_C"] / 10000.0)
        if total_pct >= 100:
            raise LoadError(
                f"rail {name!r} feedback: R{side} initial+TCR tolerance "
                f"{total_pct:g}% must be below 100%")
        fb[f"r_{side}_total_tol_pct"] = total_pct
    for f in ("fb_bias_current_min_nA", "fb_bias_current_max_nA"):
        fb[f] = _num(raw.get(f, 0), f"feedback.{f}", name)
    if fb["fb_bias_current_max_nA"] < fb["fb_bias_current_min_nA"]:
        raise LoadError(f"rail {name!r} feedback bias-current range must be ordered")
    if fb["fb_bias_current_min_nA"] or fb["fb_bias_current_max_nA"]:
        for f in ("fb_bias_current_basis", "fb_bias_current_evidence"):
            value = str(raw.get(f, "")).strip()
            if not value:
                raise LoadError(
                    f"rail {name!r} feedback nonzero bias-current range "
                    f"requires {f!r}")
            fb[f] = value
    return fb


def feedback_window(fb):
    """Worst-case (vout_low, vout_high) from the divider tolerance corners.
    vout = vref*(1 + r_top/r_bottom) + i_fb*r_top:
      low  = vref_min * (1 + r_top_min / r_bottom_max)
      high = vref_max * (1 + r_top_max / r_bottom_min)"""
    tt = fb["r_top_total_tol_pct"] / 100.0
    bt = fb["r_bottom_total_tol_pct"] / 100.0
    rt_lo = fb["r_top_ohm"] * (1 - tt)
    rt_hi = fb["r_top_ohm"] * (1 + tt)
    lo = fb["vref_min"] * (1 + rt_lo / (fb["r_bottom_ohm"] * (1 + bt))) \
        + fb["fb_bias_current_min_nA"] * 1e-9 * rt_lo
    hi = fb["vref_max"] * (1 + rt_hi / (fb["r_bottom_ohm"] * (1 - bt))) \
        + fb["fb_bias_current_max_nA"] * 1e-9 * rt_hi
    return lo, hi


def _load_ir_components(raw, total, name):
    """Validate the optional auditable breakdown behind ir_budget_mohm.

    A single scalar can be arithmetically correct while silently excluding a
    connector or cable.  The mapping does not decide which components belong
    in the path—that remains a requirements decision—but it makes the claimed
    denominator visible and prevents its displayed total drifting from what
    E-MARGIN actually grades.
    """
    if raw is None:
        return None
    if total is None:
        raise LoadError(f"rail {name!r} declares ir_budget_components_mohm "
                        "without ir_budget_mohm — the breakdown needs the "
                        "exact total E-MARGIN grades")
    if not isinstance(raw, dict) or not raw:
        raise LoadError(f"rail {name!r} ir_budget_components_mohm must be a "
                        "non-empty mapping of path element -> worst-case mOhm")
    out = {}
    for key, value in raw.items():
        label = str(key).strip()
        if not label:
            raise LoadError(f"rail {name!r} ir_budget_components_mohm has an "
                            "empty path-element label")
        # Adopted externally-claimed rails use the structured form so a bare
        # optimistic scalar cannot masquerade as a worst-case part fact.  The
        # legacy numeric form remains readable for projects that have not yet
        # adopted requirements.yaml; early_design_check.py refuses it on an
        # adopted external path.
        if isinstance(value, dict):
            if "value" not in value:
                raise LoadError(
                    f"rail {name!r} ir_budget_components_mohm.{label} "
                    "mapping is missing 'value'")
            number = _num(value["value"],
                          f"ir_budget_components_mohm.{label}.value", name)
            basis = str(value.get("basis", "")).strip()
            evidence = str(value.get("evidence", "")).strip()
            if not basis or not evidence:
                raise LoadError(
                    f"rail {name!r} ir_budget_components_mohm.{label} "
                    "structured entry requires basis and evidence")
        else:
            number = _num(value, f"ir_budget_components_mohm.{label}", name)
        if number < 0:
            raise LoadError(f"rail {name!r} ir_budget_components_mohm.{label} "
                            f"is negative ({number:g})")
        out[label] = number
    summed = sum(out.values())
    if abs(summed - total) > max(1e-6, abs(total) * 1e-6):
        raise LoadError(f"rail {name!r} ir_budget_components_mohm sums to "
                        f"{summed:g} mOhm but ir_budget_mohm is {total:g} "
                        "mOhm — there may be one displayed path and another "
                        "one graded")
    return out


def _load_upstream_delivery(raw):
    """Load a shared input-path voltage-floor proof.

    Per-output IR budgets run at one output's current.  A fuse fixed-drop and
    aggregate eFuse instead run at the shared trunk current; folding those
    terms into every output rail either assumes an unproved intermediate
    voltage or applies the wrong current.  This block derives that intermediate
    floor once and binds every named consumer rail to it.
    """
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise LoadError("upstream_delivery must be a mapping")
    text_fields = ("source_net", "destination_net", "evidence")
    out = {}
    for field in text_fields:
        value = str(raw.get(field, "")).strip()
        if not value:
            raise LoadError(f"upstream_delivery.{field} is required")
        out[field] = value
    for field in ("source_min_V", "destination_floor_V", "load_current_A"):
        value = _num(raw.get(field), f"upstream_delivery.{field}", "shared input")
        if value <= 0:
            raise LoadError(f"upstream_delivery.{field} must be > 0")
        out[field] = value
    margin = _num(raw.get("margin", 0), "upstream_delivery.margin", "shared input")
    if margin < 0:
        raise LoadError("upstream_delivery.margin must be >= 0")
    out["margin"] = margin
    rails = raw.get("rails")
    if not isinstance(rails, list) or not rails or any(not str(x).strip() for x in rails):
        raise LoadError("upstream_delivery.rails must be a non-empty rail-name list")
    out["rails"] = [str(x).strip() for x in rails]
    if len(set(out["rails"])) != len(out["rails"]):
        raise LoadError("upstream_delivery.rails contains duplicates")

    def components(field):
        values = raw.get(field)
        if not isinstance(values, dict) or not values:
            raise LoadError(f"upstream_delivery.{field} must be a non-empty mapping")
        parsed = {}
        for label, entry in values.items():
            if not str(label).strip() or not isinstance(entry, dict):
                raise LoadError(f"upstream_delivery.{field} entries need a label and mapping")
            if "value" not in entry:
                raise LoadError(f"upstream_delivery.{field}.{label} is missing value")
            value = _num(entry["value"], f"upstream_delivery.{field}.{label}.value", "shared input")
            basis = str(entry.get("basis", "")).strip()
            evidence = str(entry.get("evidence", "")).strip()
            if value < 0 or not basis or not evidence:
                raise LoadError(f"upstream_delivery.{field}.{label} needs non-negative value, basis and evidence")
            parsed[str(label)] = {"value": value, "basis": basis, "evidence": evidence}
        return parsed

    out["fixed_drop_components_mV"] = components("fixed_drop_components_mV")
    out["resistance_components_mohm"] = components("resistance_components_mohm")
    return out


# slack absorbing an honestly-ROUNDED declared corner (0.5 mV), never a
# tolerance term someone actually omitted (those move the corner 10s of mV).
_FB_ROUND_SLACK_V = 0.0005


def grade_feedback_window(rail):
    """(verdict, msg) for a rail's declared-vs-computed vout window. N-A when
    the rail has no feedback block. FAIL when the DECLARED window is NARROWER
    than the tolerance-corner window — the author under-stated the corners
    (the usb-hub-3s-v3 Vref-only incident)."""
    fb = rail.get("feedback")
    if fb is None:
        return "N-A", None
    lo, hi = rail["fb_low"], rail["fb_high"]
    ref = (f"Vref {fb['vref']:g} V +/-{fb['vref_tol_pct']:g}%"
           if fb["reference_form"] == "symmetric" else
           f"Vref {fb['vref_min']:g}-{fb['vref_max']:g} V")
    hdr = (f"rail {rail['name']!r} feedback window: {ref}, "
           f"Ibias {fb['fb_bias_current_min_nA']:g}-{fb['fb_bias_current_max_nA']:g} nA, Rtop {fb['r_top_ohm']:g} "
           f"+/-{fb['r_top_total_tol_pct']:g}% total, Rbot {fb['r_bottom_ohm']:g} "
           f"+/-{fb['r_bottom_total_tol_pct']:g}% total "
           f"(initial tolerance + {fb['resistor_temperature_delta_C']:g} C TCR excursion) "
           f"=> computed worst-case "
           f"{lo:.3f}-{hi:.3f} V vs declared {rail['vout_min']:g}-"
           f"{rail['vout_max']:g} V")
    probs = []
    if rail["vout_min"] > lo + _FB_ROUND_SLACK_V:
        probs.append(f"declared vout_min {rail['vout_min']:g} V is ABOVE the "
                     f"computed worst-case low {lo:.3f} V")
    if rail["vout_max"] < hi - _FB_ROUND_SLACK_V:
        probs.append(f"declared vout_max {rail['vout_max']:g} V is BELOW the "
                     f"computed worst-case high {hi:.3f} V")
    if probs:
        return "FAIL", (
            f"{hdr} -> FAIL under-stated tolerance corners: "
            + "; ".join(probs)
            + " — the declared window omits reference/divider tolerance; "
              "widen vout_min/vout_max to cover the computed corners")
    return "PASS", f"{hdr} -> PASS: declared window covers the corners"


def load_rails(path):
    """Parse + validate power_tree.yaml. Raises LoadError naming the offending
    rail on any schema problem (esp. a missing Vout ENVELOPE — the incident)."""
    if yaml is None:
        raise LoadError("PyYAML not available")
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8-sig"))
    if data is None:
        return [], {}
    if not isinstance(data, dict) or "rails" not in data:
        raise LoadError("power_tree.yaml must be a mapping with a 'rails:' list")
    rails_raw = data.get("rails")
    if not isinstance(rails_raw, list):
        raise LoadError("'rails:' must be a list")
    top = {"input_trunk_class": data.get("input_trunk_class"),
           # E-OFF (de-energization + stored quiescent draw), all OPTIONAL:
           "source_type": data.get("source_type"),
           "off_control": data.get("off_control"),
           "quiescent_ua": data.get("quiescent_ua"),
           "pack_capacity_mah": data.get("pack_capacity_mah"),
           "source_voltage_boundary": data.get("source_voltage_boundary"),
           # E-MARGIN floor used for a rail that declares no ir_budget_mohm:
           "ir_floor_mohm": data.get("ir_floor_mohm"),
           "upstream_delivery": _load_upstream_delivery(
               data.get("upstream_delivery"))}

    rails = []
    for i, r in enumerate(rails_raw):
        if not isinstance(r, dict):
            raise LoadError(f"rail #{i} is not a mapping")
        name = r.get("name", f"#{i}")
        for f in ("vin_min", "vin_max", "vout_min", "vout_max", "iout_max_A"):
            if f not in r or r[f] is None:
                raise LoadError(
                    f"rail {name!r} is missing {f!r} — every power PORT must "
                    f"pin its voltage ENVELOPE (vin_min/vin_max/vout_min/"
                    f"vout_max) and current, not just current (D-SPEC)")
        stage = str(r.get("stage", "conversion")).strip().lower()
        if stage not in ("conversion", "distribution"):
            raise LoadError(f"rail {name!r} stage must be conversion or "
                            f"distribution, got {stage!r}")
        if stage == "conversion" and not r.get("converter"):
            raise LoadError(f"rail {name!r} is missing 'converter:' (the refdes "
                            f"or part MPN of its converter)")
        vin_min = _num(r["vin_min"], "vin_min", name)
        vin_max = _num(r["vin_max"], "vin_max", name)
        vout_min = _num(r["vout_min"], "vout_min", name)
        vout_max = _num(r["vout_max"], "vout_max", name)
        iout = _num(r["iout_max_A"], "iout_max_A", name)
        eff = _num(r.get("eff", 0.9), "eff", name)
        if vin_min > vin_max:
            raise LoadError(f"rail {name!r}: vin_min {vin_min} > vin_max {vin_max}")
        if vout_min > vout_max:
            raise LoadError(f"rail {name!r}: vout_min {vout_min} > vout_max "
                            f"{vout_max}")
        if not (0 < eff <= 1):
            raise LoadError(f"rail {name!r}: eff {eff} must be in (0, 1]")
        if vin_min <= 0 or iout < 0:
            raise LoadError(f"rail {name!r}: vin_min and iout must be positive")
        # OPTIONAL load-margin fields (E-MARGIN): load_uv_threshold ACTIVATES
        # the check for this rail; ir_budget_mohm + margin refine it.
        load_uv = _num_opt(r.get("load_uv_threshold"), "load_uv_threshold", name)
        ir_budget = _num_opt(r.get("ir_budget_mohm"), "ir_budget_mohm", name)
        ir_components = _load_ir_components(
            r.get("ir_budget_components_mohm"), ir_budget, name)
        rmargin = _num_opt(r.get("margin"), "margin", name)
        margin_basis = str(r.get("margin_basis", "")).strip()
        margin_evidence = str(r.get("margin_evidence", "")).strip()
        if bool(margin_basis) != bool(margin_evidence):
            raise LoadError(
                f"rail {name!r} delivery margin provenance needs BOTH "
                "margin_basis and margin_evidence")
        if margin_basis and rmargin is None:
            raise LoadError(
                f"rail {name!r} declares delivery margin provenance but no "
                "numeric margin")
        ss_ceiling = _num_opt(r.get("steady_state_ceiling_V"),
                              "steady_state_ceiling_V", name)
        ss_high_mv = _num_opt(r.get("steady_state_variation_high_mV"),
                              "steady_state_variation_high_mV", name)
        ss_basis = str(r.get("steady_state_variation_basis", "")).strip()
        ss_evidence = str(r.get("steady_state_variation_evidence", "")).strip()
        ss_fields = (ss_ceiling, ss_high_mv, ss_basis, ss_evidence)
        if any(v not in (None, "") for v in ss_fields) and \
                any(v in (None, "") for v in ss_fields):
            raise LoadError(
                f"rail {name!r} steady-state high-side budget needs ALL of "
                "steady_state_ceiling_V, steady_state_variation_high_mV, "
                "steady_state_variation_basis and "
                "steady_state_variation_evidence")
        fb = _load_feedback(r.get("feedback"), name)
        fb_low = fb_high = None
        if fb is not None:
            fb_low, fb_high = feedback_window(fb)
        distribution = None
        if stage == "distribution":
            raw_distribution = r.get("distribution")
            if not isinstance(raw_distribution, dict):
                raise LoadError(f"rail {name!r} distribution stage requires a "
                                "distribution: mapping")
            devices = raw_distribution.get("series_devices")
            if (not isinstance(devices, list) or not devices
                    or any(not str(value).strip() for value in devices)):
                raise LoadError(f"rail {name!r} distribution.series_devices "
                                "must be a non-empty exact-part list")
            resistance = _num(raw_distribution.get("path_resistance_max_mohm"),
                              "distribution.path_resistance_max_mohm", name)
            limit_min = _num(raw_distribution.get("current_limit_min_A"),
                             "distribution.current_limit_min_A", name)
            limit_max = _num(raw_distribution.get("current_limit_max_A"),
                             "distribution.current_limit_max_A", name)
            reverse_policy = str(
                raw_distribution.get("reverse_current_policy", "")).strip()
            if resistance <= 0:
                raise LoadError(f"rail {name!r} distribution path resistance "
                                "must be > 0")
            if limit_min <= 0 or limit_max < limit_min:
                raise LoadError(f"rail {name!r} distribution current-limit "
                                "window must satisfy 0 < min <= max")
            if iout > limit_min + 1e-9:
                raise LoadError(f"rail {name!r} Iout {iout:g} A exceeds the "
                                f"minimum current limit {limit_min:g} A")
            if not reverse_policy:
                raise LoadError(f"rail {name!r} distribution requires a "
                                "reverse_current_policy")
            distribution = {
                "series_devices": [str(value).strip() for value in devices],
                "path_resistance_max_mohm": resistance,
                "current_limit_min_A": limit_min,
                "current_limit_max_A": limit_max,
                "reverse_current_policy": reverse_policy,
            }
            if vout_max > vin_max + 1e-9 or vout_min > vin_max + 1e-9:
                raise LoadError(f"rail {name!r} distribution stage cannot "
                                "raise its input voltage")
            # The same declared resistance is the delivery-path authority for
            # E-MARGIN unless a more detailed component budget is supplied.
            if ir_budget is None:
                ir_budget = resistance
                ir_components = {"protected_distribution_path": resistance}
        rails.append({
            "name": name, "vin_min": vin_min, "vin_max": vin_max,
            "vout_min": vout_min, "vout_max": vout_max, "iout": iout,
            "eff": eff, "stage": stage,
            "converter": (str(r["converter"]) if r.get("converter") else None),
            "distribution": distribution,
            # OPTIONAL cascade ownership. A downstream converter still gets
            # its own Vin/Vout topology grade, but its power is already inside
            # the parent rail's declared load and must not be charged to the
            # board input a second time.
            "input_parent": (str(r["input_parent"]).strip()
                             if r.get("input_parent") else None),
            "load_uv": load_uv, "ir_budget_mohm": ir_budget,
            "ir_budget_components_mohm": ir_components, "margin": rmargin,
            "margin_basis": margin_basis,
            "margin_evidence": margin_evidence,
            "feedback": fb, "fb_low": fb_low, "fb_high": fb_high,
            "steady_state_ceiling_V": ss_ceiling,
            "steady_state_variation_high_mV": ss_high_mv,
            "steady_state_variation_basis": ss_basis,
            "steady_state_variation_evidence": ss_evidence,
            # OPTIONAL LINEAR overrides: the part.yaml number is the package /
            # datasheet figure; a rail may state a board-specific derating (a
            # hot ambient, no copper under the part) or the dropout at ITS own
            # iout_max_A rather than the part's rated maximum.
            "dropout_mv": _num_opt(r.get("dropout_mv"), "dropout_mv", name),
            "pdiss_max_mw": _num_opt(r.get("pdiss_max_mw"), "pdiss_max_mw",
                                     name),
        })

    by_name = {r["name"]: r for r in rails}
    if len(by_name) != len(rails):
        raise LoadError("power_tree.yaml rail names must be unique")
    upstream = top.get("upstream_delivery")
    if upstream:
        missing = sorted(set(upstream["rails"]) - set(by_name))
        if missing:
            raise LoadError(f"upstream_delivery names absent rails: {missing}")
    for rail in rails:
        parent_name = rail.get("input_parent")
        if not parent_name:
            continue
        if parent_name == rail["name"]:
            raise LoadError(f"rail {rail['name']!r} cannot be its own input_parent")
        parent = by_name.get(parent_name)
        if parent is None:
            raise LoadError(f"rail {rail['name']!r} input_parent {parent_name!r} "
                            "does not name another declared rail")
        if rail["vin_min"] > parent["vout_min"] + 1e-9 or \
                rail["vin_max"] < parent["vout_max"] - 1e-9:
            raise LoadError(
                f"rail {rail['name']!r} Vin {rail['vin_min']:g}-"
                f"{rail['vin_max']:g} V does not cover parent {parent_name!r} "
                f"Vout {parent['vout_min']:g}-{parent['vout_max']:g} V")
        seen = {rail["name"]}
        cursor = parent
        while cursor.get("input_parent"):
            next_name = cursor["input_parent"]
            if next_name in seen:
                raise LoadError(f"power-tree input_parent cycle includes {next_name!r}")
            seen.add(next_name)
            cursor = by_name[next_name]
    return rails, top


# --------------------------------------------------------------------------
# topology grading — returns (verdict, message). verdict in PASS/FAIL.
def grade_linear(rail, dirname, facts):
    """Grade a LINEAR rail on the two things the buck/boost derivation cannot
    see. Returns (verdict, msg). The topology requirement is already known to
    be BUCK when this is called.

    DROPOUT   headroom = vin_min - vout_max  >=  dropout_mv
              (worst case: the lowest input against the highest regulated
              output — the corner where a linear part falls out of regulation)
    DISSIPATION  PD = (vin_max - vout_min) * iout  <=  pdiss_max_mw
              (worst case: the highest input against the lowest regulated
              output, at full load — the corner where the package cooks)

    Both bounds are REQUIRED. A LINEAR rail whose part declares neither is a
    rail this gate cannot grade, and per canon M-COVER an ungradeable input is
    a FAIL, never a pass — otherwise `converter: <some LDO>` would become a
    new way to reach a green E-TOPO while grading nothing, which is the defect
    LINEAR was added to remove.
    """
    name, iout = rail["name"], rail["iout"]
    drop_mv = rail.get("dropout_mv")
    drop_mv = facts.get("dropout_mv") if drop_mv is None else drop_mv
    pd_mw = rail.get("pdiss_max_mw")
    pd_mw = facts.get("pdiss_max_mw") if pd_mw is None else pd_mw

    missing = [f for f, v in (("dropout_mv", drop_mv),
                              ("pdiss_max_mw", pd_mw)) if v is None]
    if missing:
        raise LoadError(
            f"rail {name!r} declares the LINEAR converter {dirname} but "
            f"neither 02_parts/{dirname}/part.yaml nor the rail declares "
            f"{missing} — a linear regulator's failure modes are DROPOUT and "
            f"DISSIPATION, and the Vin-vs-Vout derivation is blind to both. "
            f"Declare dropout_mv (datasheet MAX at the rated output current) "
            f"and pdiss_max_mw (the package rating, or a board-specific "
            f"derating on the rail). A rail this gate cannot grade is a FAIL, "
            f"not a pass (canon M-COVER)")
    drop_mv = _num(drop_mv, "dropout_mv", name)
    pd_mw = _num(pd_mw, "pdiss_max_mw", name)

    headroom_mv = (rail["vin_min"] - rail["vout_max"]) * 1000.0
    pd_actual_mw = (rail["vin_max"] - rail["vout_min"]) * iout * 1000.0
    hdr = (f"rail {name!r} LINEAR ({dirname}): headroom "
           f"{headroom_mv:.0f} mV (Vin_min {rail['vin_min']:g} - Vout_max "
           f"{rail['vout_max']:g}) vs dropout {drop_mv:g} mV; PD "
           f"{pd_actual_mw:.0f} mW ((Vin_max {rail['vin_max']:g} - Vout_min "
           f"{rail['vout_min']:g}) x {iout:g} A) vs rating {pd_mw:g} mW "
           f"({pd_actual_mw / pd_mw * 100:.0f}%)")
    probs = []
    if headroom_mv < drop_mv:
        probs.append(f"DROPOUT: only {headroom_mv:.0f} mV of headroom against "
                     f"a {drop_mv:g} mV dropout — the rail falls out of "
                     f"regulation at the low input corner")
    if pd_actual_mw > pd_mw:
        probs.append(f"DISSIPATION: {pd_actual_mw:.0f} mW into a {pd_mw:g} mW "
                     f"package — a linear pass element burns (Vin-Vout)xIout "
                     f"as heat; step down with a switcher or move to a larger "
                     f"package")
    if probs:
        return "FAIL", f"{hdr} -> FAIL {'; '.join(probs)}"
    return "PASS", f"{hdr} -> PASS"


def grade_rail(rail, part_index):
    if rail.get("stage") == "distribution":
        distribution = rail["distribution"]
        missing = [device for device in distribution["series_devices"]
                   if _norm_id(device) not in part_index]
        if missing:
            raise LoadError(
                f"rail {rail['name']!r} distribution devices are absent from "
                f"02_parts: {missing}")
        rail["topo"] = "DISTRIBUTION"
        drop_mv = (distribution["path_resistance_max_mohm"]
                   * rail["iout"])
        return "PASS", (
            f"rail {rail['name']!r} protected distribution: "
            f"{len(distribution['series_devices'])} exact series device(s), "
            f"current limit {distribution['current_limit_min_A']:g}-"
            f"{distribution['current_limit_max_A']:g} A covers "
            f"Iout {rail['iout']:g} A, path drop <= {drop_mv:.0f} mV; "
            f"reverse policy={distribution['reverse_current_policy']} -> PASS")
    required = derive_topology(rail["vin_min"], rail["vin_max"],
                               rail["vout_min"], rail["vout_max"])
    dirname, declared, facts = resolve_converter(rail["converter"], part_index)
    rail["topo"] = declared          # consumed by worst_case_input_current
    hdr = (f"rail {rail['name']!r} (Vin {rail['vin_min']:g}-{rail['vin_max']:g} V, "
           f"Vout {rail['vout_min']:g}-{rail['vout_max']:g} V): required="
           f"{required}, declared={declared} ({dirname})")

    if declared == LINEAR:
        # A linear regulator IMPLEMENTS a step-down requirement and nothing
        # else. Where the envelope needs step-up (BOOST) or both (BUCK_BOOST,
        # i.e. Vin dips into or below Vout somewhere in the declared range) it
        # physically cannot deliver the rail.
        if required != BUCK:
            why = ("a linear regulator cannot step up"
                   if required == BOOST else
                   "the Vin envelope overlaps Vout, so the pass element drops "
                   "out of regulation somewhere in the declared range")
            return "FAIL", (
                f"{hdr} -> FAIL cannot meet Vout range: {why}; the envelope "
                f"requires a {required} converter")
        lverdict, lmsg = grade_linear(rail, dirname, facts)
        return lverdict, f"{hdr} -> step-down requirement MET by a linear pass " \
                         f"element; {lmsg}"

    if declared == required:
        return "PASS", f"{hdr} -> PASS"

    if declared == BUCK_BOOST and required in (BUCK, BOOST):
        suff = "buck" if required == BUCK else "boost"
        unused = "boost" if required == BUCK else "buck"
        cond = ("Vout<Vin_min" if required == BUCK else "Vout>Vin_max")
        return "FAIL", (
            f"{hdr} -> FAIL over-engineered: {dirname} is buck_boost but "
            f"{cond} => {suff} suffices; {unused} unused — justify with ADR "
            f"or re-select")

    return "FAIL", (
        f"{hdr} -> FAIL cannot meet Vout range: {declared} converter cannot "
        f"deliver a {required}-topology rail (Vout {rail['vout_min']:g}-"
        f"{rail['vout_max']:g} V from Vin {rail['vin_min']:g}-{rail['vin_max']:g} V)")


# --------------------------------------------------------------------------
# input-current worst case + trunk-declaration cross-check
def worst_case_input_current(rails):
    """(I_amps, P_out_W, P_in_W, Vin_min) across all rails sharing the input.

    A SWITCHING rail draws CONSTANT POWER: Iin = Pout/eff / Vin, so the input
    current RISES as the input sags. A LINEAR rail draws CONSTANT CURRENT:
    the pass element is in series with the load, so Iin = Iout (+Iq) whatever
    Vin does, and its input power is Vin*Iout, not Vout*Iout/eff.

    Modelling a linear rail with the switching formula UNDER-STATES its trunk
    current by exactly Vout/Vin. pluto-cal-switch's power_tree.yaml wrote
    `eff: 1.0` on its LDO rail with the comment that this "makes the derived
    input-trunk current equal the output current, which is the physically
    correct answer for a linear pass element" — it does not: at Vout 3.3 /
    Vin_min 4.4 it gives 0.075 A for a rail that draws 0.100 A, 25% light.
    A rail carries `topo` once grade_rail() has resolved its converter; a rail
    without one is treated as switching, which is the pre-existing behaviour.
    """
    roots = [r for r in rails if not r.get("input_parent")]
    if not roots:
        return 0.0, 0.0, 0.0, 0.0
    p_out = sum(r["vout_max"] * r["iout"] for r in roots)
    # the LOWEST Vin_min across the tree: the input current of a switching rail
    # peaks when the input sags, so every switching rail is charged at it.
    vin_min = min(r["vin_min"] for r in roots)
    amps = sum(
        r["iout"] if r.get("topo") in (LINEAR, "DISTRIBUTION")
        else r["vout_max"] * r["iout"] / r["eff"] / vin_min
        for r in roots)
    # reported input power, consistent with the current above. For an
    # all-switching tree this is identical to Sum(Pout/eff), unchanged.
    return amps, p_out, amps * vin_min, vin_min


# A CURRENT, NOT A SUBSTRING OF A PART NUMBER. The leading `(?<![0-9A-Za-z.])`
# is the whole fix: without it, `AO3401A` — the reverse-polarity FET on
# crow-recorder-central-v2's ORDER_README line
#
#   "AO3401A reverse-polarity FET (Q1) + SMAJ5.0A (D1) + 2A fuse (F_IN)."
#
# — matched as "3401" + "A", and E-TOPO printed `fuse rated 3401 A is >2x the
# derived need 0.7 A` on a board whose fuse is 2 A and is named on that same
# line (measured 2026-07-27). `SMAJ5.0A` reads as 5.0 A by the same mechanism.
# A gate that prints nonsense trains its reader to skim, which is how real
# findings get missed. The trailing `(?![0-9A-Za-z])` rejects `2Ah`/`3401AB`.
_NUM_A = re.compile(r"(?<![0-9A-Za-z.])([\d.]+)\s*A(?![0-9A-Za-z])", re.I)


def _first_amps(text):
    m = _NUM_A.search(str(text))
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:                      # a bare '.' or '1.2.3'
        return None


def find_trunk_declaration(proj, top, rails, nets_override=None):
    """Best-effort: locate a declared input-trunk current and a fuse rating.
    Returns (trunk_current, trunk_class_name, unambiguous, fuse_amps,
    fuse_source). Any may be None. `fuse_source` is the file and the LINE the
    fuse number was read out of — a number this gate prints must be traceable
    to the text it came from. `unambiguous` is True only when the trunk class
    is named
    explicitly (input_trunk_class:) or a single netclass matches the input by
    name/nets — the guard that keeps the under-built FAIL from false-firing."""
    netsy = Path(nets_override) if nets_override else \
        Path(proj) / "03_src" / "rules" / "nets.yaml"
    trunk_current = trunk_class = fuse_amps = fuse_src = None
    unambiguous = False
    classes = {}
    if netsy.exists() and yaml:
        try:
            ny = yaml.safe_load(netsy.read_text(encoding="utf-8-sig")) or {}
            classes = ny.get("classes", {}) or {}
        except Exception:
            classes = {}

    explicit = top.get("input_trunk_class")
    if explicit and explicit in classes:
        trunk_class = explicit
        trunk_current = _first_amps(classes[explicit].get("current", ""))
        unambiguous = True
    else:
        # heuristic: a class named as the input trunk, or whose nets look like
        # the battery/input rail. Exactly one match == unambiguous.
        INPUT_RE = re.compile(r"(pwr[_-]?in|input|trunk|batt|^vin$)", re.I)
        INPUT_NETS = re.compile(r"^(vin|vbat|batt)", re.I)
        cands = []
        for cname, cbody in classes.items():
            body = cbody or {}
            nets = body.get("nets", []) or []
            if INPUT_RE.search(cname) or any(INPUT_NETS.match(str(n)) for n in nets):
                cands.append((cname, _first_amps(body.get("current", ""))))
        cands = [c for c in cands if c[1] is not None]
        if len(cands) == 1:
            trunk_class, trunk_current = cands[0]
            unambiguous = True
        elif len(cands) > 1:
            trunk_class, trunk_current = cands[0][0], None  # ambiguous -> advisory

    # fuse rating: an ORDER_README line, or a 'fuse' mention in nets.yaml.
    # RELEASE ORDER IS NEWEST-FIRST, not glob order. This used to take
    # whatever the filesystem handed back first across EVERY release of EVERY
    # board in the project, so on a multi-board project it could quote a
    # sibling board's fuse, and on any project it could quote a superseded
    # release's. Ordering comes from release_index (numeric per component,
    # board-grouped); the file the number came from is RETURNED, so a wrong
    # number names its own source instead of floating free.
    fuse_texts = []
    rel_dirs = []
    try:
        _idx = _relidx.index(proj)
        for _b in sorted(_idx):
            rel_dirs += list(reversed(_idx[_b]))
    except Exception:                       # unattributable set -> glob order
        rel_dirs = sorted((Path(proj) / "07_releases").glob("*")) \
            if (Path(proj) / "07_releases").is_dir() else []
    for d in rel_dirs:
        for fp in sorted(list(d.glob("ORDER_README*")) + list(d.glob("*ORDER*"))):
            if fp.is_file():
                fuse_texts.append((fp, fp.read_text(errors="replace")))
    for fp in sorted(glob.glob(str(Path(proj) / "01_docs/*ORDER*"))):
        fuse_texts.append((Path(fp), Path(fp).read_text(errors="replace")))
    if netsy.exists():
        fuse_texts.append((netsy, netsy.read_text(errors="replace")))
    for src, txt in fuse_texts:
        for line in txt.splitlines():
            if re.search(r"fuse", line, re.I):
                a = _first_amps(line)
                if a is not None:
                    fuse_amps, fuse_src = a, f"{src.name}: {line.strip()[:90]}"
                    break
        if fuse_amps is not None:
            break
    return trunk_current, trunk_class, unambiguous, fuse_amps, fuse_src


# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# E-MARGIN -- output SETPOINT vs load brownout, net of the delivery IR drop
DEFAULT_IR_FLOOR_MOHM = 100.0    # a bare realistic board+connector+cable path
DEFAULT_MARGIN = 0.20            # headroom must beat the IR drop by this much


def grade_upstream_delivery(upstream, rails):
    """Derive the shared protected-trunk floor from the admitted source."""
    if upstream is None:
        return "N-A", None
    fixed = sum(v["value"] for v in upstream["fixed_drop_components_mV"].values())
    resistance = sum(v["value"] for v in upstream["resistance_components_mohm"].values())
    nominal_drop_mv = fixed + resistance * upstream["load_current_A"]
    charged_drop_mv = nominal_drop_mv * (1 + upstream["margin"])
    derived = upstream["source_min_V"] - charged_drop_mv / 1000.0
    declared = upstream["destination_floor_V"]
    fixed_text = " + ".join(
        f"{k}={v['value']:g}" for k, v in upstream["fixed_drop_components_mV"].items())
    resistance_text = " + ".join(
        f"{k}={v['value']:g}" for k, v in upstream["resistance_components_mohm"].items())
    hdr = (f"shared {upstream['source_net']}->{upstream['destination_net']}: "
           f"{upstream['source_min_V']:.3f} V - [fixed {fixed_text} mV + "
           f"({resistance_text} mOhm) x {upstream['load_current_A']:g} A] x "
           f"{1 + upstream['margin']:.2f} = {derived:.3f} V derived floor; "
           f"declared {declared:.3f} V")
    problems = []
    if declared > derived + 1e-9:
        problems.append("declared protected floor exceeds the derived worst-low")
    by_name = {r["name"]: r for r in rails}
    for name in upstream["rails"]:
        if by_name[name]["vin_min"] > declared + 1e-9:
            problems.append(
                f"rail {name!r} vin_min {by_name[name]['vin_min']:.3f} V exceeds the declared shared floor")
    if problems:
        return "FAIL", f"{hdr} -> FAIL: " + "; ".join(problems)
    return "PASS", f"{hdr} -> PASS ({upstream['evidence']})"


def grade_margin(rail, ir_floor_mohm):
    """Grade ONE rail's output-setpoint load margin. Returns (verdict, msg);
    verdict in PASS / FAIL / N-A. N-A unless the rail declares
    load_uv_threshold (only a rail feeding a fixed-brownout load has a margin
    to check). vout_min is the WORST-CASE regulated output (lowest the rail
    sits under tolerance), which is what the load actually sees. A rail with a
    feedback: block is graded from the COMPUTED tolerance-corner worst-low
    (fb_low), not the declared vout_min — the declared number is exactly what
    the usb-hub-3s-v3 author got wrong (2026-07-23)."""
    uv = rail.get("load_uv")
    if uv is None:
        return "N-A", None
    name, iout = rail["name"], rail["iout"]
    if rail.get("fb_low") is not None:
        vout_min = rail["fb_low"]
        src = " (COMPUTED worst-low from feedback tolerances)"
    else:
        vout_min = rail["vout_min"]
        src = ""
    if iout <= 0:
        return "N-A", None
    headroom = vout_min - uv                        # volts of setpoint margin
    budget_mohm = headroom / iout * 1000.0          # series R the margin buys
    hdr = (f"rail {name!r} (Vout_min {vout_min:.3f} V{src}, load_UV {uv:g} V, "
           f"Imax {iout:g} A): headroom {headroom * 1000:.0f} mV = "
           f"{budget_mohm:.0f} mOhm total IR budget at {iout:g} A")
    if headroom <= 0:
        return "FAIL", (f"{hdr} -> FAIL: the regulated worst-case output "
                        f"{vout_min:g} V is at/below the load brownout {uv:g} V "
                        f"- dead on arrival, before any IR drop")
    ir_budget = rail.get("ir_budget_mohm")
    margin = rail.get("margin")
    margin = DEFAULT_MARGIN if margin is None else margin
    margin_provenance = ""
    if rail.get("margin_basis"):
        margin_provenance = (
            f" ({rail['margin_basis']}: {rail['margin_evidence']})")
    if ir_budget is not None:
        components = rail.get("ir_budget_components_mohm")
        breakdown = ("; path " + " + ".join(
            f"{key}={value:g}" for key, value in components.items()) + " mOhm"
            if components else "")
        drop_v = ir_budget / 1000.0 * iout          # volts burned in the path
        need_v = drop_v * (1 + margin)
        if headroom < need_v:
            return "FAIL", (
                f"{hdr} -> FAIL: setpoint headroom {headroom * 1000:.0f} mV < IR "
                f"drop {drop_v * 1000:.0f} mV ({ir_budget:g} mOhm{breakdown} x {iout:g} A) x "
                f"{1 + margin:.2f} margin{margin_provenance} = "
                f"{need_v * 1000:.0f} mV - the load "
                f"browns out under IR drop; raise the setpoint or cut delivery "
                f"resistance")
        return "PASS", (f"{hdr} -> PASS: clears IR drop {drop_v * 1000:.0f} mV "
                        f"({ir_budget:g} mOhm{breakdown} x {iout:g} A) x {1 + margin:.2f} "
                        f"margin{margin_provenance}")
    # No declared IR budget: the budget must at least clear the floor (a bare
    # realistic delivery path). This is the (Vout-UV)-below-a-margin-floor form.
    if budget_mohm < ir_floor_mohm:
        return "FAIL", (
            f"{hdr} -> FAIL: only {budget_mohm:.0f} mOhm of IR budget < "
            f"{ir_floor_mohm:g} mOhm floor - a real board+connector+cable "
            f"delivery path exceeds this; raise the setpoint, or declare + "
            f"justify ir_budget_mohm for this rail")
    return "PASS", (f"{hdr} -> PASS: {budget_mohm:.0f} mOhm budget clears the "
                    f"{ir_floor_mohm:g} mOhm floor")


def grade_high_side_margin(rail):
    """Grade an explicitly adopted steady-state high-side variation budget.

    Divider/reference corners are not a complete output-voltage maximum:
    switching ripple and line/load movement are nonzero.  This optional block
    makes that reserved band a number and prevents a computed high corner from
    sitting a few millivolts below an external ceiling while prose calls it
    closed.  Startup/load-step excursions remain a separate transient claim.
    """
    ceiling = rail.get("steady_state_ceiling_V")
    variation_mv = rail.get("steady_state_variation_high_mV")
    if ceiling is None:
        return "N-A", None
    high = rail["fb_high"] if rail.get("fb_high") is not None else rail["vout_max"]
    total = high + variation_mv / 1000.0
    hdr = (f"rail {rail['name']!r} high-side reserve: setpoint corner "
           f"{high:.3f} V + {variation_mv:g} mV steady-state variation = "
           f"{total:.3f} V vs {ceiling:g} V ceiling "
           f"({rail['steady_state_variation_basis']}: "
           f"{rail['steady_state_variation_evidence']})")
    if total > ceiling + 1e-9:
        return "FAIL", (f"{hdr} -> FAIL: no bounded allowance remains for "
                        "ripple/line/load movement; lower the setpoint or "
                        "increase the justified ceiling")
    return "PASS", f"{hdr} -> PASS"


def run_margin_check(proj, ptp, nets_override=None):
    """E-MARGIN. Returns (exit_code, lines). Pure - main() prints and exits."""
    rails, top = load_rails(ptp)
    if not rails:
        return 0, ["E-MARGIN N-A: power_tree.yaml has no rails"]
    ir_floor = top.get("ir_floor_mohm")
    ir_floor = DEFAULT_IR_FLOOR_MOHM if ir_floor is None else float(ir_floor)
    graded = [grade_upstream_delivery(top.get("upstream_delivery"), rails)]
    graded += [grade_margin(r, ir_floor) for r in rails]
    # a declared-vs-computed feedback window that under-states its corners is
    # an E-MARGIN defect too: the headroom everyone reasons from is fiction.
    graded += [grade_feedback_window(r) for r in rails]
    graded += [grade_high_side_margin(r) for r in rails]
    checked = [(v, m) for (v, m) in graded if v != "N-A"]
    if not checked:
        return 0, ["E-MARGIN N-A: no rail declares load_uv_threshold - no "
                   "regulated rail feeds a known fixed-brownout load"]
    lines, fails = [], []
    for v, m in checked:
        lines.append(f"  {m}")
        if v == "FAIL":
            fails.append(m)
    if fails:
        lines.insert(0, f"E-MARGIN FAIL: {len(fails)}/{len(checked)} "
                        f"load-margin issue(s):")
        return 1, lines
    lines.insert(0, f"E-MARGIN OK: {len(checked)} rail(s) clear the load "
                    f"brownout with IR margin")
    return 0, lines


# --------------------------------------------------------------------------
# E-OFF -- de-energization + stored quiescent draw for a self-powered board
_BATT_RE = re.compile(
    r"batt|cell|lipo|li[-_ ]?ion|liion|lifepo|li[-_ ]?po|pack|18650|nimh|"
    r"nicd|coin|cr20\d\d|super[-_ ]?cap|\b[1-9]s\b", re.I)
_EXT_RE = re.compile(
    r"usb|dc[-_ ]?jack|barrel|adapter|mains|wall|external|bench|poe|vbus", re.I)
_BATT_NET_RE = re.compile(r"^(vbat|batt|vcell|cell|pack|vpack|lipo|bms)", re.I)


def detect_energy_source(proj, top, nets_override=None):
    """(kind, reason). kind in 'battery' / 'external' / 'unknown'. source_type:
    is authoritative; else VBAT/BATT/PACK nets in nets.yaml, else a battery ADR
    title/filename. Deliberately conservative (like E-ADR): 'unknown' -> N-A and
    the red-team checklist carries the question."""
    st = str(top.get("source_type") or "")
    if st:
        if _BATT_RE.search(st):
            return "battery", f"source_type: {st!r}"
        if _EXT_RE.search(st):
            return "external", f"source_type: {st!r} (externally powered)"
    if nets_override:
        netsy = Path(nets_override)
    else:
        netsy = Path(proj) / "03_src" / "rules" / "nets.yaml"
    if netsy.exists() and yaml:
        try:
            ny = yaml.safe_load(netsy.read_text(encoding="utf-8-sig")) or {}
            for cname, cbody in (ny.get("classes", {}) or {}).items():
                for n in (cbody or {}).get("nets", []) or []:
                    if _BATT_NET_RE.match(str(n)):
                        return "battery", f"nets.yaml net {n!r}"
        except Exception:
            pass
    for adr in sorted(glob.glob(str(Path(proj) / "01_docs" / "decisions" /
                                    "*.md"))):
        head = Path(adr).name + " " + Path(adr).read_text(errors="replace")[:400]
        if re.search(r"batter|lipo|li[-_ ]?ion|\bcell\b|\bpack\b|discharge",
                     head, re.I):
            return "battery", f"ADR {Path(adr).name}"
    return "unknown", "no source_type / battery nets / battery ADR"


def grade_off_control(top):
    """Grade the declared off_control + quiescent_ua (battery already detected).
    Returns (fails, notes)."""
    fails, notes = [], []
    off = top.get("off_control")
    q = top.get("quiescent_ua")
    if off is None:
        fails.append(
            "no off_control declared - a battery board must document HOW it is "
            "de-energized (master switch / load-switch / EN-gating), or declare "
            "always-on WITH an ADR; else the converters idle-drain the pack in "
            "storage (usb-hub-3s-v3: both buck EN pins tied active, no switch)")
    else:
        s = str(off)
        alwayson = re.search(r"always[-_ ]?on|^none$|no[-_ ]?switch|"
                             r"no[-_ ]?disconnect|self[-_ ]?drain", s, re.I)
        has_adr = re.search(r"adr|decisions/|\b\d{4}\b", s, re.I)
        if alwayson and not has_adr:
            fails.append(
                f"off_control {s!r} is always-on with no ADR reference - a "
                f"self-draining storage state must be an explicit ADR-justified "
                f"decision, not a default")
        else:
            notes.append(f"off_control: {s!r}")
    if q is None:
        fails.append(
            "no quiescent_ua declared - the stored/shutdown draw must be a "
            "NUMBER so pack self-drain time is computable")
    else:
        notes.append(f"quiescent_ua: {q}")
    return fails, notes


def grade_source_voltage_boundary(top, rails):
    """A battery rail's admitted lower voltage must have an owner.

    Converter UVLO well below a project Vin floor does not protect the pack.
    The boundary may be enforced on-board or assigned to a named external BMS,
    but it may not exist only as a calculation input.
    """
    raw = top.get("source_voltage_boundary")
    if not isinstance(raw, dict):
        return [
            "no source_voltage_boundary declared - a battery design must "
            "assign its minimum operating voltage to an on-board supervisor "
            "or a named external BMS/disconnect"
        ], []
    fails, notes = [], []
    try:
        floor = float(raw.get("minimum_operating_V"))
    except (TypeError, ValueError):
        floor = 0.0
        fails.append("source_voltage_boundary.minimum_operating_V must be a positive number")
    enforcement = str(raw.get("enforcement", "")).strip()
    evidence = str(raw.get("evidence", "")).strip()
    if enforcement not in {"on_board", "external_required"}:
        fails.append("source_voltage_boundary.enforcement must be on_board or external_required")
    if not evidence:
        fails.append("source_voltage_boundary.evidence is required")
    if enforcement == "external_required" and not str(raw.get("required_device", "")).strip():
        fails.append("external_required source boundary must name required_device")
    if floor > 0 and rails:
        rail_floor = min(r["vin_min"] for r in rails)
        if abs(floor - rail_floor) > 1e-6:
            fails.append(
                f"source boundary {floor:g} V differs from the lowest rail "
                f"vin_min {rail_floor:g} V")
    if not fails:
        owner = str(raw.get("required_device", "")).strip() or "on-board circuit"
        notes.append(f"source minimum: {floor:g} V, {enforcement}, owner={owner!r}")
    return fails, notes


def run_off_check(proj, ptp, nets_override=None):
    """E-OFF. Returns (exit_code, lines). Pure - main() prints and exits."""
    rails, top = load_rails(ptp)
    kind, reason = detect_energy_source(proj, top, nets_override)
    if kind != "battery":
        return 0, [f"E-OFF N-A: no self-contained energy source detected "
                   f"({reason}) - de-energization is by unplugging the input"]
    lines = [f"E-OFF: self-contained energy source detected ({reason})"]
    fails, notes = grade_off_control(top)
    boundary_fails, boundary_notes = grade_source_voltage_boundary(top, rails)
    fails += boundary_fails
    notes += boundary_notes
    for n in notes:
        lines.append(f"  {n}")
    q = top.get("quiescent_ua")
    cap = top.get("pack_capacity_mah")
    if q not in (None, 0) and cap:
        try:
            days = float(cap) / (float(q) / 1000.0) / 24.0
            lines.append(f"  stored self-drain: {float(cap):g} mAh / {float(q):g}"
                         f" uA ~= {days:.0f} days to flat (advisory - acceptable "
                         f"for storage/shipping?)")
        except (TypeError, ValueError, ZeroDivisionError):
            pass
    for f in fails:
        lines.append(f"  -> FAIL: {f}")
    if fails:
        lines.insert(0, f"E-OFF FAIL: {len(fails)} de-energization issue(s):")
        return 1, lines
    lines.insert(0, "E-OFF OK: de-energization path (off_control) + stored draw "
                    "(quiescent_ua) both declared")
    return 0, lines


# --------------------------------------------------------------------------
def find_power_tree(proj, override=None):
    if override:
        return Path(override)
    return Path(proj) / "03_src" / "rules" / "power_tree.yaml"


def converter_census(part_index):
    """[(dirname, raw_type, class)] for every 02_parts entry whose `type:`
    classifies as a converter — the INDEPENDENT evidence that E-TOPO has
    something to grade.

    This is canon M1 applied to E-TOPO's own N-A: until now the gate asked
    `power_tree.yaml` whether there was anything to check, and believed the
    answer. Deleting the file, or writing `rails: []`, therefore produced
    "E-TOPO N-A" and exit 0 on a board full of regulators. `02_parts/` is a
    different artifact, written by a different stage, so it can contradict.
    """
    out = []
    for rec in {id(v): v for v in part_index.values()}.values():
        cls = normalize_type(rec.get("type"))
        if cls is not None:
            out.append((rec["dir"], rec.get("type"), cls))
    return sorted(out)


def _ungraded_converters(part_index, rails):
    """Converter parts in 02_parts that NO rail names. The M-COVER denominator
    for E-TOPO: `N converters graded / M present`."""
    named = {_norm_id(r["converter"]) for r in rails if r.get("converter")}
    return [c for c in converter_census(part_index)
            if _norm_id(c[0]) not in named]


def no_rails_verdict(proj, ptp_exists, part_index):
    """(exit_code, lines) for a project with no power_tree.yaml, or one whose
    `rails:` list is empty. N-A is only legitimate when the board HAS NO
    CONVERTER."""
    conv = converter_census(part_index)
    where = ("power_tree.yaml has no rails" if ptp_exists
             else "there is no 03_src/rules/power_tree.yaml")
    if not conv:
        return 0, [f"E-TOPO N-A: 0/0 — {where}, and 02_parts declares no "
                   f"buck/boost/buck_boost/linear converter, so there is "
                   f"genuinely nothing to derive (checked against "
                   f"{proj}/02_parts, not against the power tree's own "
                   f"say-so)"]
    listing = ", ".join(f"{d} (type: {t!r} -> {c})" for d, t, c in conv)
    return 1, [
        f"E-TOPO FAIL: 0/{len(conv)} converters graded — {where}, but "
        f"02_parts declares {len(conv)}: {listing}",
        f"  Every one of those rails is UNGRADED: no Vin/Vout envelope, no "
        f"derived topology, no dropout or dissipation bound. An absent or "
        f"empty power tree is how a board reaches a green E-TOPO while the "
        f"gate looks at nothing (canon M-COVER), and until 2026-07-27 it was "
        f"the ONLY way to declare an LDO-only board, because normalize_type() "
        f"rejected every linear part. It no longer is: declare each rail with "
        f"`converter:` naming the part, and a linear regulator is graded on "
        f"its dropout and dissipation instead of a switching topology.",
    ]


def run_check(proj, ptp, nets_override=None):
    """Returns (exit_code, lines). Pure — main() prints and exits."""
    lines = []
    rails, top = load_rails(ptp)
    part_index = load_part_index(proj)
    if not rails:
        return no_rails_verdict(proj, True, part_index)

    fails = []
    for rail in rails:
        verdict, msg = grade_rail(rail, part_index)
        lines.append(f"  {msg}")
        if verdict == "FAIL":
            fails.append(msg)
        # declared-vs-computed feedback tolerance window (when declared)
        fverdict, fmsg = grade_feedback_window(rail)
        if fverdict != "N-A":
            lines.append(f"  {fmsg}")
            if fverdict == "FAIL":
                fails.append(fmsg)

    # input-current worst case — always printed
    def _a(x):
        """Amps/watts at 3 significant figures.

        `.1f` printed a derived need of 0.15 A as `0.1 A` and anything under
        0.05 A as `0.0 A` — a worst-case trunk current of ZERO, which is
        exactly the number a reader does not question. It also silently
        widened the UNDER-BUILT margin it was reporting: the comparison is
        done on the real float, so the printed number disagreed with the
        verdict beside it. Low-power boards are the whole point of this gate's
        `.1f`-era blind spot: every mA-class rail rendered the same.

        At or above 1 A the existing one-decimal form is kept EXACTLY, so no
        sealed verification report's quoted number moves and no existing
        assertion changes meaning — a display fix that rewrites every archived
        figure is not a fix. Below 1 A, where one decimal has no resolution
        left, it goes to 3 significant figures.
        """
        return f"{x:.1f}" if abs(x) >= 1 else f"{x:.3g}"

    I, p_out, p_in, vin_min = worst_case_input_current(rails)
    lines.append(
        f"  input-trunk worst case: {_a(I)} A at Vin_min {vin_min:g} V "
        f"(Sum Pout={p_out:g} W / eff = {_a(p_in)} W input / {vin_min:g} V)")

    trunk_current, trunk_class, unambiguous, fuse_amps, fuse_src = \
        find_trunk_declaration(proj, top, rails, nets_override)
    if trunk_current is not None:
        if trunk_current < I * 0.98:
            note = (f"  UNDER-BUILT: declared trunk current {trunk_current:g} A "
                    f"(class {trunk_class!r}) is below the derived worst case "
                    f"{_a(I)} A — copper/fuse cannot carry the load")
            if unambiguous:
                lines.append(note + " -> FAIL")
                fails.append(note.strip())
            else:
                lines.append(note + " (advisory: trunk mapping ambiguous)")
        elif trunk_current > 2 * I:
            lines.append(
                f"  OVER-BUILT (advisory): declared trunk current "
                f"{trunk_current:g} A (class {trunk_class!r}) is >2x the derived "
                f"need {_a(I)} A — over-provisioned (the usb-hub-3s 16A-vs-7A "
                f"class); confirm it is intentional")
        else:
            lines.append(
                f"  trunk current {trunk_current:g} A (class {trunk_class!r}) "
                f"consistent with derived {_a(I)} A")
    if fuse_amps is not None and fuse_amps > 2 * I:
        lines.append(
            f"  OVER-BUILT (advisory): fuse rated {fuse_amps:g} A is >2x the "
            f"derived need {_a(I)} A — over-provisioned "
            f"[read from {fuse_src}]")

    # M-COVER: a converter part that no rail names is a converter this gate did
    # not grade, and the verdict must say so rather than count only the rails
    # it was handed. This is the partial form of the empty-power-tree defect —
    # three of four crow-recorder-central rails were declared and the two LDOs
    # were left in a COMMENT, so E-TOPO printed a confident verdict over half
    # the tree.
    ungraded = _ungraded_converters(part_index, rails)
    n_conv = len(converter_census(part_index))
    if ungraded:
        listing = ", ".join(f"{d} (type: {t!r} -> {c})" for d, t, c in ungraded)
        msg = (f"UNGRADED CONVERTERS: {len(ungraded)} of {n_conv} converter "
               f"part(s) in 02_parts are named by no rail: {listing} — declare "
               f"a rail for each, or remove the part")
        lines.append(f"  {msg}")
        fails.append(msg)

    graded = len(rails) - len([f for f in fails if f.startswith("rail ")])
    if fails:
        lines.insert(0, f"E-TOPO FAIL: {len(fails)} issue(s) over "
                        f"{len(rails)} declared rail(s) / {n_conv} converter "
                        f"part(s) in 02_parts:")
        return 1, lines
    lines.insert(0, f"E-TOPO OK: {graded}/{len(rails)} rail(s) "
                    f"topology-correct, covering {n_conv}/{n_conv} converter "
                    f"part(s) in 02_parts")
    return 0, lines


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="POWER-TREE gate (E-TOPO / E-MARGIN / E-OFF)")
    ap.add_argument("project", nargs="?")
    ap.add_argument("--power-tree", default="")
    ap.add_argument("--nets", default="")
    ap.add_argument("--margin", action="store_true",
                    help="grade E-MARGIN (output setpoint vs load brownout)")
    ap.add_argument("--off-control", dest="off_control", action="store_true",
                    help="grade E-OFF (de-energization + stored quiescent draw)")
    ap.add_argument("--derive", nargs=4, type=float,
                    metavar=("VIN_MIN", "VIN_MAX", "VOUT_MIN", "VOUT_MAX"),
                    help="print the derived topology for an ad-hoc range")
    args = ap.parse_args(argv)

    if args.derive is not None:
        vmn, vmx, omn, omx = args.derive
        topo = derive_topology(vmn, vmx, omn, omx)
        print(f"Vin {vmn:g}-{vmx:g} V, Vout {omn:g}-{omx:g} V -> {topo}")
        return 0

    if not args.project:
        ap.error("PROJECT_DIR is required (or use --derive)")
    proj = Path(args.project)
    ptp = find_power_tree(proj, args.power_tree or None)
    tag = ("E-MARGIN" if args.margin else
           "E-OFF" if args.off_control else "E-TOPO")
    if not ptp.exists():
        if args.margin or args.off_control:
            # E-MARGIN/E-OFF genuinely have no input without the file; their
            # activating fields live only there.
            print(f"{tag} N-A: no {ptp} — the power-tree gate is optional")
            return 0
        # E-TOPO does NOT get to take the file's absence as proof there is
        # nothing to grade: 02_parts is an independent artifact and can
        # contradict it (canon M1). Deleting power_tree.yaml was the ONLY way
        # an LDO-only board could reach a green E-TOPO before 2026-07-27.
        rc, lines = no_rails_verdict(proj, False, load_part_index(proj))
        for ln in lines:
            print(ln)
        return rc

    try:
        if args.margin:
            rc, lines = run_margin_check(proj, ptp, args.nets or None)
        elif args.off_control:
            rc, lines = run_off_check(proj, ptp, args.nets or None)
        else:
            rc, lines = run_check(proj, ptp, args.nets or None)
    except LoadError as e:
        print(f"{tag} LOAD ERROR: {e}")
        return 2
    for ln in lines:
        print(ln)
    return rc


if __name__ == "__main__":
    sys.exit(main())
