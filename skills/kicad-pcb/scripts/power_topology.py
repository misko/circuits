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

The selected converter's topology must MATCH the derived one:
  - MORE capable than needed (buck_boost where buck suffices) = OVER-ENGINEERING
    -> FAIL. Waiver-able only with an ADR justifying the extra capability
    (e.g. "future 20 V PD"); the waiver is applied by policy_audit's E-TOPO row.
  - LESS capable (buck where boost is required) -> FAIL: cannot meet Vout.

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

BUCK, BOOST, BUCK_BOOST = "BUCK", "BOOST", "BUCK_BOOST"


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


def normalize_type(raw):
    """part.yaml `type:` string -> canonical topology, or None if the type does
    not classify. Buck+boost in any spelling (buck_boost, buck-boost, buckboost,
    pd_source_buckboost_soc) -> BUCK_BOOST; then buck -> BUCK; boost -> BOOST."""
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
    return None


# --------------------------------------------------------------------------
# part resolution — converter <refdes or MPN> -> its part.yaml topology
def _norm_id(s):
    return re.sub(r"[/\-_ .]", "", str(s).lower())


def load_part_index(proj):
    """{normalized mpn/dirname -> (dirname, raw_type)} over 02_parts/*/part.yaml."""
    idx = {}
    for py in sorted(glob.glob(str(Path(proj) / "02_parts" / "*" / "part.yaml"))):
        try:
            y = yaml.safe_load(Path(py).read_text()) or {}
        except Exception:
            continue
        dirname = Path(py).parent.name
        raw_type = y.get("type")
        for key in (y.get("mpn"), dirname):
            if key:
                idx[_norm_id(key)] = (dirname, raw_type)
    return idx


def resolve_converter(converter, part_index):
    """(dirname, canonical_topology). Raises LoadError if the converter cannot
    be resolved to a part.yaml or its type does not classify."""
    hit = part_index.get(_norm_id(converter))
    if hit is None:
        raise LoadError(
            f"converter {converter!r} not found in 02_parts — reference it by "
            f"the part MPN or its 02_parts directory name (known: "
            f"{sorted(set(v[0] for v in part_index.values()))})")
    dirname, raw_type = hit
    topo = normalize_type(raw_type)
    if topo is None:
        raise LoadError(
            f"converter {converter!r} ({dirname}) part.yaml type "
            f"{raw_type!r} does not classify as buck/boost/buck_boost — the "
            f"type field must name the converter topology")
    return dirname, topo


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


def load_rails(path):
    """Parse + validate power_tree.yaml. Raises LoadError naming the offending
    rail on any schema problem (esp. a missing Vout ENVELOPE — the incident)."""
    if yaml is None:
        raise LoadError("PyYAML not available")
    data = yaml.safe_load(Path(path).read_text())
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
           # E-MARGIN floor used for a rail that declares no ir_budget_mohm:
           "ir_floor_mohm": data.get("ir_floor_mohm")}

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
        if not r.get("converter"):
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
        rmargin = _num_opt(r.get("margin"), "margin", name)
        rails.append({
            "name": name, "vin_min": vin_min, "vin_max": vin_max,
            "vout_min": vout_min, "vout_max": vout_max, "iout": iout,
            "eff": eff, "converter": str(r["converter"]),
            "load_uv": load_uv, "ir_budget_mohm": ir_budget, "margin": rmargin,
        })
    return rails, top


# --------------------------------------------------------------------------
# topology grading — returns (verdict, message). verdict in PASS/FAIL.
def grade_rail(rail, part_index):
    required = derive_topology(rail["vin_min"], rail["vin_max"],
                               rail["vout_min"], rail["vout_max"])
    dirname, declared = resolve_converter(rail["converter"], part_index)
    hdr = (f"rail {rail['name']!r} (Vin {rail['vin_min']:g}-{rail['vin_max']:g} V, "
           f"Vout {rail['vout_min']:g}-{rail['vout_max']:g} V): required="
           f"{required}, declared={declared} ({dirname})")

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
    """(I_amps, P_out_W, P_in_W, Vin_min) across all rails sharing the input."""
    if not rails:
        return 0.0, 0.0, 0.0, 0.0
    p_out = sum(r["vout_max"] * r["iout"] for r in rails)
    # each rail's input power is P_out/eff; sum, then divide by the LOWEST
    # Vin_min (worst case = the input current peaks when the battery is low).
    p_in = sum(r["vout_max"] * r["iout"] / r["eff"] for r in rails)
    vin_min = min(r["vin_min"] for r in rails)
    return p_in / vin_min, p_out, p_in, vin_min


_NUM_A = re.compile(r"([\d.]+)\s*A", re.I)


def _first_amps(text):
    m = _NUM_A.search(str(text))
    return float(m.group(1)) if m else None


def find_trunk_declaration(proj, top, rails, nets_override=None):
    """Best-effort: locate a declared input-trunk current and a fuse rating.
    Returns (trunk_current, trunk_class_name, unambiguous, fuse_amps). Any may
    be None. `unambiguous` is True only when the input trunk class is named
    explicitly (input_trunk_class:) or a single netclass matches the input by
    name/nets — the guard that keeps the under-built FAIL from false-firing."""
    netsy = Path(nets_override) if nets_override else \
        Path(proj) / "03_src" / "rules" / "nets.yaml"
    trunk_current = trunk_class = fuse_amps = None
    unambiguous = False
    classes = {}
    if netsy.exists() and yaml:
        try:
            ny = yaml.safe_load(netsy.read_text()) or {}
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

    # fuse rating: an ORDER_README line, or a 'fuse' mention in nets.yaml
    fuse_texts = []
    for pat in ("07_releases/*/ORDER_README*", "07_releases/*/*ORDER*",
                "01_docs/*ORDER*"):
        for fp in glob.glob(str(Path(proj) / pat)):
            fuse_texts.append(Path(fp).read_text(errors="replace"))
    if netsy.exists():
        fuse_texts.append(netsy.read_text(errors="replace"))
    for txt in fuse_texts:
        for line in txt.splitlines():
            if re.search(r"fuse", line, re.I):
                a = _first_amps(line)
                if a is not None:
                    fuse_amps = a
                    break
        if fuse_amps is not None:
            break
    return trunk_current, trunk_class, unambiguous, fuse_amps


# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# E-MARGIN -- output SETPOINT vs load brownout, net of the delivery IR drop
DEFAULT_IR_FLOOR_MOHM = 100.0    # a bare realistic board+connector+cable path
DEFAULT_MARGIN = 0.20            # headroom must beat the IR drop by this much


def grade_margin(rail, ir_floor_mohm):
    """Grade ONE rail's output-setpoint load margin. Returns (verdict, msg);
    verdict in PASS / FAIL / N-A. N-A unless the rail declares
    load_uv_threshold (only a rail feeding a fixed-brownout load has a margin
    to check). vout_min is the WORST-CASE regulated output (lowest the rail
    sits under tolerance), which is what the load actually sees."""
    uv = rail.get("load_uv")
    if uv is None:
        return "N-A", None
    name, vout_min, iout = rail["name"], rail["vout_min"], rail["iout"]
    if iout <= 0:
        return "N-A", None
    headroom = vout_min - uv                        # volts of setpoint margin
    budget_mohm = headroom / iout * 1000.0          # series R the margin buys
    hdr = (f"rail {name!r} (Vout_min {vout_min:g} V, load_UV {uv:g} V, "
           f"Imax {iout:g} A): headroom {headroom * 1000:.0f} mV = "
           f"{budget_mohm:.0f} mOhm total IR budget at {iout:g} A")
    if headroom <= 0:
        return "FAIL", (f"{hdr} -> FAIL: the regulated worst-case output "
                        f"{vout_min:g} V is at/below the load brownout {uv:g} V "
                        f"- dead on arrival, before any IR drop")
    ir_budget = rail.get("ir_budget_mohm")
    margin = rail.get("margin")
    margin = DEFAULT_MARGIN if margin is None else margin
    if ir_budget is not None:
        drop_v = ir_budget / 1000.0 * iout          # volts burned in the path
        need_v = drop_v * (1 + margin)
        if headroom < need_v:
            return "FAIL", (
                f"{hdr} -> FAIL: setpoint headroom {headroom * 1000:.0f} mV < IR "
                f"drop {drop_v * 1000:.0f} mV ({ir_budget:g} mOhm x {iout:g} A) x "
                f"{1 + margin:.2f} margin = {need_v * 1000:.0f} mV - the load "
                f"browns out under IR drop; raise the setpoint or cut delivery "
                f"resistance")
        return "PASS", (f"{hdr} -> PASS: clears IR drop {drop_v * 1000:.0f} mV "
                        f"({ir_budget:g} mOhm x {iout:g} A) x {1 + margin:.2f} "
                        f"margin")
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


def run_margin_check(proj, ptp, nets_override=None):
    """E-MARGIN. Returns (exit_code, lines). Pure - main() prints and exits."""
    rails, top = load_rails(ptp)
    if not rails:
        return 0, ["E-MARGIN N-A: power_tree.yaml has no rails"]
    ir_floor = top.get("ir_floor_mohm")
    ir_floor = DEFAULT_IR_FLOOR_MOHM if ir_floor is None else float(ir_floor)
    graded = [grade_margin(r, ir_floor) for r in rails]
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
            ny = yaml.safe_load(netsy.read_text()) or {}
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


def run_off_check(proj, ptp, nets_override=None):
    """E-OFF. Returns (exit_code, lines). Pure - main() prints and exits."""
    rails, top = load_rails(ptp)
    kind, reason = detect_energy_source(proj, top, nets_override)
    if kind != "battery":
        return 0, [f"E-OFF N-A: no self-contained energy source detected "
                   f"({reason}) - de-energization is by unplugging the input"]
    lines = [f"E-OFF: self-contained energy source detected ({reason})"]
    fails, notes = grade_off_control(top)
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


def run_check(proj, ptp, nets_override=None):
    """Returns (exit_code, lines). Pure — main() prints and exits."""
    lines = []
    rails, top = load_rails(ptp)
    if not rails:
        return 0, ["E-TOPO N-A: power_tree.yaml has no rails"]

    part_index = load_part_index(proj)
    fails = []
    for rail in rails:
        verdict, msg = grade_rail(rail, part_index)
        lines.append(f"  {msg}")
        if verdict == "FAIL":
            fails.append(msg)

    # input-current worst case — always printed
    I, p_out, p_in, vin_min = worst_case_input_current(rails)
    lines.append(
        f"  input-trunk worst case: {I:.1f} A at Vin_min {vin_min:g} V "
        f"(Sum Pout={p_out:g} W / eff = {p_in:.1f} W input / {vin_min:g} V)")

    trunk_current, trunk_class, unambiguous, fuse_amps = \
        find_trunk_declaration(proj, top, rails, nets_override)
    if trunk_current is not None:
        if trunk_current < I * 0.98:
            note = (f"  UNDER-BUILT: declared trunk current {trunk_current:g} A "
                    f"(class {trunk_class!r}) is below the derived worst case "
                    f"{I:.1f} A — copper/fuse cannot carry the load")
            if unambiguous:
                lines.append(note + " -> FAIL")
                fails.append(note.strip())
            else:
                lines.append(note + " (advisory: trunk mapping ambiguous)")
        elif trunk_current > 2 * I:
            lines.append(
                f"  OVER-BUILT (advisory): declared trunk current "
                f"{trunk_current:g} A (class {trunk_class!r}) is >2x the derived "
                f"need {I:.1f} A — over-provisioned (the usb-hub-3s 16A-vs-7A "
                f"class); confirm it is intentional")
        else:
            lines.append(
                f"  trunk current {trunk_current:g} A (class {trunk_class!r}) "
                f"consistent with derived {I:.1f} A")
    if fuse_amps is not None and fuse_amps > 2 * I:
        lines.append(
            f"  OVER-BUILT (advisory): fuse rated {fuse_amps:g} A is >2x the "
            f"derived need {I:.1f} A — over-provisioned")

    if fails:
        lines.insert(0, f"E-TOPO FAIL: {len(fails)}/{len(rails)} rail issue(s):")
        return 1, lines
    lines.insert(0, f"E-TOPO OK: {len(rails)} rail(s) topology-correct")
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
        print(f"{tag} N-A: no {ptp} — the power-tree gate is optional")
        return 0

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
