#!/usr/bin/env python3
"""POWER-TREE TOPOLOGY gate (E-TOPO) — make converter-topology selection a
mechanical commission-stage check DERIVED from Vin-vs-Vout, not interpreted.

WHY THIS EXISTS
---------------
usb-hub-3s (2026-07-22) was built with an IP6559 BUCK-BOOST SoC for its USB-C
port plus a 16 A input trunk — but the USB-C output is 5 V ONLY and the battery
is 9-12.6 V, so Vout(5 V) < Vin_min(9 V) ALWAYS: a simple step-down BUCK
suffices. The buck-boost (+ 4 external FETs + 30 V-FET/TVS coordination +
compact hot-loop congestion + a 16 A trunk) existed only to support >5 V PDOs
the spec never required. Root cause: D-SPEC pinned the CURRENT ("5 A compliant")
but never the OUTPUT VOLTAGE RANGE, and the converter TOPOLOGY was interpreted,
not DERIVED from Vin vs Vout. This gate closes that loop.

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
      Grade every rail in PROJECT_DIR/03_src/rules/power_tree.yaml.
      Exit 0 all-pass, 1 on any topology/under-built FAIL, 2 on a load/config
      error (bad schema, missing vout range). No power_tree.yaml -> N-A, exit 0.

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
    top = {"input_trunk_class": data.get("input_trunk_class")}

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
        rails.append({
            "name": name, "vin_min": vin_min, "vin_max": vin_max,
            "vout_min": vout_min, "vout_max": vout_max, "iout": iout,
            "eff": eff, "converter": str(r["converter"]),
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
    ap = argparse.ArgumentParser(description="POWER-TREE TOPOLOGY gate (E-TOPO)")
    ap.add_argument("project", nargs="?")
    ap.add_argument("--power-tree", default="")
    ap.add_argument("--nets", default="")
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
    if not ptp.exists():
        print(f"E-TOPO N-A: no {ptp} — the topology gate is optional")
        return 0

    try:
        rc, lines = run_check(proj, ptp, args.nets or None)
    except LoadError as e:
        print(f"E-TOPO LOAD ERROR: {e}")
        return 2
    for ln in lines:
        print(ln)
    return rc


if __name__ == "__main__":
    sys.exit(main())
