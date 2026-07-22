#!/usr/bin/env python3
"""ELECTRICAL-INVARIANTS (phase E1, netlist-only) — make DESIGN INTENT
machine-checkable against the exported netlist.

WHY THIS EXISTS
---------------
The D1 reverse-polarity defect (usb-hub-3s v1.0, 2026-07-21) passed ERC, DRC,
netlist parity, jlc_twin AND pin review — because every artifact was
consistently WRONG TOGETHER. The symbol, footprint, netlist and board all
agreed that D1's cathode sat on VBAT_F; only the DESIGN INTENT (the diode is
the reverse-polarity block feeding VIN) disagreed, and intent was not
executable. Our gates prove self-consistency, not that the netlist matches
what the ADRs decided.

This gate closes that loop: a protection/topology ADR emits machine-checkable
assertions in `03_src/rules/electrical_invariants.yaml`, and this checker
grades them against the netlist the board actually exports.

THREE NETLIST-CHECKABLE ASSERTION KINDS (E1)
--------------------------------------------
  pin_on_net    {assert: pin_on_net, pin: "D1.1", net: VIN, adr: 0001, why: ...}
                the named pin must be on the named net (the D1 class).
  series_chain  {assert: series_chain, chain: [BATT_P, F1, Q1, VIN],
                 through: {Q1: [D, S]}, adr: 0001, why: ...}
                consecutive elements share a net in order. A 2-pad part
                bridges the nets on its two pads (inferred); a >2-pad part
                names its bridging pins with `through: {REF: [in, out]}`.
  net_has_part  {assert: net_has_part, net: VIN_S, part_type: capacitor,
                 min: 1, adr: 0007, why: ...}
                the net must carry >= min parts of that type (by refdes
                prefix). The bridge-rail-decoupling class red-team B found.

Every invariant REQUIRES `adr:` (the ADR that emitted it) and `why:`.

Geometric assertion kinds (clamp_le_rating, kelvin_within, ...) are DEFERRED
to a future E2 — they need footprint/geometry, not just the netlist.

USAGE
-----
  electrical_invariants.py PROJECT_DIR
      Grade every invariant in PROJECT_DIR/03_src/rules/electrical_invariants.yaml
      against the netlist (06_build/netlists/*.net or 04_kicad/*.net).
      Exit 0 all-pass, 1 on any failed assertion (naming the assertion + the
      actual net found), 2 on a load/config error (bad schema, no netlist).
      No invariants file -> N-A, exit 0.

  electrical_invariants.py PROJECT_DIR --adr-coverage
      E-ADR loop-closing check: every protection/topology ADR under
      01_docs/decisions/ must have at least one invariant citing its number.
      Exit 1 naming any protection ADR that emitted no invariant.

  --netlist PATH / --invariants PATH   override the auto-located files.

Netlist-only: no pcbnew import, runs on any python3 with PyYAML.
"""
import argparse
import glob
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - environments here all ship PyYAML
    yaml = None


# --------------------------------------------------------------------------
# refdes-prefix -> part type. netlist-only classification (canon: the netlist
# is authoritative; we do not need 02_parts to know a C is a capacitor).
TYPE_PREFIX = {
    "capacitor": {"C"},
    "resistor": {"R"},
    "inductor": {"L"},
    "ferrite": {"FB"},
    "diode": {"D"},
    "led": {"LED", "D"},
    "transistor": {"Q"},
    "fuse": {"F"},
    "ic": {"U"},
    "connector": {"J"},
    "crystal": {"Y", "X"},
    "testpoint": {"TP"},
}

# protection/topology ADRs are the ones that MUST close the loop (E-ADR).
PROT_RE = re.compile(r"(protection|topology|input[- ]protection|"
                     r"reverse[- ]polarity)", re.I)


class LoadError(Exception):
    """A schema/config problem — distinct from an assertion failure."""


# --------------------------------------------------------------------------
# s-expression netlist parser (the KiCad `(export ... (nets (net ...)))` form)
def _tokenize(s):
    toks, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        if c in "()":
            toks.append(c)
            i += 1
        elif c.isspace():
            i += 1
        elif c == '"':
            j, buf = i + 1, []
            while j < n and s[j] != '"':
                if s[j] == "\\" and j + 1 < n:
                    buf.append(s[j + 1])
                    j += 2
                else:
                    buf.append(s[j])
                    j += 1
            toks.append(("STR", "".join(buf)))
            i = j + 1
        else:
            j = i
            while j < n and not s[j].isspace() and s[j] not in "()":
                j += 1
            toks.append(("SYM", s[i:j]))
            i = j
    return toks


def _build(toks):
    """toks -> nested python lists. STR/SYM atoms become str; STR is tagged
    so a quoted "net" head never gets mistaken for the `net` keyword."""
    pos = 0

    def parse():
        nonlocal pos
        assert toks[pos] == "("
        pos += 1
        node = []
        while pos < len(toks) and toks[pos] != ")":
            t = toks[pos]
            if t == "(":
                node.append(parse())
            else:
                kind, val = t
                node.append((val, kind))  # (text, "SYM"|"STR")
                pos += 1
        pos += 1  # consume ")"
        return node

    out = []
    while pos < len(toks):
        if toks[pos] == "(":
            out.append(parse())
        else:
            pos += 1
    return out


def _head(node):
    """The keyword head of a list node, only if it is a bare SYM."""
    if isinstance(node, list) and node and isinstance(node[0], tuple) \
            and node[0][1] == "SYM":
        return node[0][0]
    return None


def _first_atom(node, key):
    """Value of the first (key VALUE ...) child list, as plain text."""
    for c in node:
        if isinstance(c, list) and _head(c) == key and len(c) >= 2 \
                and isinstance(c[1], tuple):
            return c[1][0]
    return None


class Netlist:
    """net<->pin map + part<->pins map, parsed from an exported .net."""

    def __init__(self, text):
        tree = _build(_tokenize(text))
        self.net_of_pin = {}          # (ref, pin) -> netname
        self.pins_of_net = {}         # netname -> [(ref, pin, func)]
        self.part_pins = {}           # ref -> {pin: {"net":.., "func":..}}

        def walk(node):
            if not isinstance(node, list):
                return
            if _head(node) == "net":
                self._add_net(node)
            for c in node:
                if isinstance(c, list):
                    walk(c)

        for top in tree:
            walk(top)

    def _add_net(self, node):
        name = _first_atom(node, "name")
        if name is None:
            return
        self.pins_of_net.setdefault(name, [])
        for c in node:
            if isinstance(c, list) and _head(c) == "node":
                ref = _first_atom(c, "ref")
                pin = _first_atom(c, "pin")
                func = _first_atom(c, "pinfunction") or ""
                if ref is None or pin is None:
                    continue
                self.net_of_pin[(ref, pin)] = name
                self.pins_of_net[name].append((ref, pin, func))
                self.part_pins.setdefault(ref, {})[pin] = {
                    "net": name, "func": func}

    # ------- resolution helpers -------
    def pin_net(self, ref, ident):
        """net at REF's pin identified by number, exact pinfunction, or a
        pinfunction with its trailing _<n> stripped (D_5 -> D)."""
        pins = self.part_pins.get(ref, {})
        ident = str(ident)
        if ident in pins:
            return pins[ident]["net"]
        for info in pins.values():
            if info["func"] == ident:
                return info["net"]
        for info in pins.values():
            base = re.sub(r"_?\d+$", "", info["func"])
            if base and base == ident:
                return info["net"]
        return None

    def refs_on_net(self, net):
        return {r for (r, _p, _f) in self.pins_of_net.get(net, [])}


def refdes_prefix(ref):
    m = re.match(r"[A-Za-z]+", ref)
    return m.group(0) if m else ""


# --------------------------------------------------------------------------
# invariant loading + validation
def _norm_adr(v):
    s = str(v).strip()
    if re.fullmatch(r"\d+", s):
        return s.zfill(4)
    return s


def load_invariants(path):
    """Parse + validate. Raises LoadError with a naming message on any schema
    problem (missing adr/why, unknown assert kind, unknown part_type)."""
    if yaml is None:
        raise LoadError("PyYAML not available")
    data = yaml.safe_load(Path(path).read_text())
    if data is None:
        return []
    if isinstance(data, dict):
        invs = data.get("invariants")
        if invs is None:
            raise LoadError("electrical_invariants.yaml has no top-level "
                            "'invariants:' list")
    elif isinstance(data, list):
        invs = data
    else:
        raise LoadError("electrical_invariants.yaml must be a mapping with an "
                        "'invariants:' list")
    if not isinstance(invs, list):
        raise LoadError("'invariants:' must be a list")

    kinds = {"pin_on_net", "series_chain", "net_has_part"}
    for i, inv in enumerate(invs):
        if not isinstance(inv, dict):
            raise LoadError(f"invariant #{i} is not a mapping")
        kind = inv.get("assert")
        if kind not in kinds:
            raise LoadError(f"invariant #{i}: unknown or missing assert kind "
                            f"{kind!r} (E1 supports {sorted(kinds)}; geometric "
                            f"kinds are deferred to E2)")
        if "adr" not in inv or str(inv.get("adr", "")).strip() == "":
            raise LoadError(f"invariant #{i} (assert={kind}) is missing the "
                            f"required 'adr:' field — every invariant must "
                            f"cite the ADR that emitted it")
        if len(str(inv.get("why", "")).strip()) < 5:
            raise LoadError(f"invariant #{i} (assert={kind}, adr={inv['adr']}) "
                            f"is missing a substantive 'why:'")
        inv["_adr"] = _norm_adr(inv["adr"])
        if kind == "pin_on_net":
            for f in ("pin", "net"):
                if not inv.get(f):
                    raise LoadError(f"invariant #{i} pin_on_net missing '{f}:'")
        elif kind == "series_chain":
            if not isinstance(inv.get("chain"), list) or len(inv["chain"]) < 2:
                raise LoadError(f"invariant #{i} series_chain needs a 'chain:' "
                                f"list of >= 2 elements")
        elif kind == "net_has_part":
            if not inv.get("net"):
                raise LoadError(f"invariant #{i} net_has_part missing 'net:'")
            pt = inv.get("part_type")
            if pt not in TYPE_PREFIX:
                raise LoadError(f"invariant #{i} net_has_part unknown "
                                f"part_type {pt!r} (known: "
                                f"{sorted(TYPE_PREFIX)})")
    return invs


# --------------------------------------------------------------------------
# grading — returns a failure string, or None if the assertion holds
def _grade_pin_on_net(inv, nl):
    pin = str(inv["pin"])
    ref, _, p = pin.partition(".")
    want = str(inv["net"])
    got = nl.net_of_pin.get((ref, p))
    adr = inv["_adr"]
    if got is None:
        return (f"pin_on_net (ADR {adr}): pin {pin} is not present in the "
                f"netlist — cannot be on {want}")
    if got != want:
        return (f"pin_on_net (ADR {adr}): {pin} is on net {got!r}, "
                f"invariant requires {want!r} — {inv.get('why', '')[:80]}")
    return None


def _grade_series_chain(inv, nl):
    chain = [str(e) for e in inv["chain"]]
    through = {str(k): v for k, v in (inv.get("through") or {}).items()}
    adr = inv["_adr"]
    cur = None
    for elem in chain:
        is_part = elem in nl.part_pins
        is_net = elem in nl.pins_of_net
        if is_part:
            if elem in through:
                pair = through[elem]
                if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                    return (f"series_chain (ADR {adr}): through[{elem}] must be "
                            f"[in, out], got {pair!r}")
                ent, ext = str(pair[0]), str(pair[1])
                enet, xnet = nl.pin_net(elem, ent), nl.pin_net(elem, ext)
                if enet is None or xnet is None:
                    return (f"series_chain (ADR {adr}): {elem} has no pin "
                            f"{ent!r}/{ext!r} (through: map names them)")
                if cur is not None and enet != cur:
                    return (f"series_chain (ADR {adr}): expected {elem}.{ent} "
                            f"on net {cur!r} but it is on {enet!r}")
                cur = xnet
            else:
                pins = nl.part_pins[elem]
                nets = [info["net"] for info in pins.values()]
                if len(pins) != 2:
                    return (f"series_chain (ADR {adr}): {elem} has {len(pins)} "
                            f"pads — add a through: map naming its two bridging "
                            f"pins")
                if cur is None:
                    return (f"series_chain (ADR {adr}): must start with a "
                            f"source net (2-pad part {elem} first is ambiguous)")
                if cur not in nets:
                    return (f"series_chain (ADR {adr}): {elem} does not connect "
                            f"to net {cur!r} (its pads are on {sorted(set(nets))})")
                other = [x for x in nets if x != cur]
                cur = other[0] if other else cur
        elif is_net:
            if cur is not None and cur != elem:
                return (f"series_chain (ADR {adr}): chain names net {elem!r} but "
                        f"the preceding element reaches {cur!r} — the link is "
                        f"broken")
            cur = elem
        else:
            return (f"series_chain (ADR {adr}): unknown element {elem!r} — "
                    f"neither a net nor a refdes in the netlist")
    return None


def _grade_net_has_part(inv, nl):
    net = str(inv["net"])
    ptype = inv["part_type"]
    mn = int(inv.get("min", 1))
    adr = inv["_adr"]
    if net not in nl.pins_of_net:
        return (f"net_has_part (ADR {adr}): net {net!r} is not present in the "
                f"netlist")
    prefixes = TYPE_PREFIX[ptype]
    matched = sorted(r for r in nl.refs_on_net(net)
                     if refdes_prefix(r) in prefixes)
    if len(matched) < mn:
        return (f"net_has_part (ADR {adr}): net {net!r} carries {len(matched)} "
                f"{ptype}(s) {matched}, needs >= {mn} — "
                f"{inv.get('why', '')[:80]}")
    return None


_GRADERS = {
    "pin_on_net": _grade_pin_on_net,
    "series_chain": _grade_series_chain,
    "net_has_part": _grade_net_has_part,
}


def check_invariants(nl, invs):
    """Grade all invariants; return list of failure strings (empty = all pass)."""
    fails = []
    for inv in invs:
        f = _GRADERS[inv["assert"]](inv, nl)
        if f:
            fails.append(f)
    return fails


# --------------------------------------------------------------------------
# E-ADR: protection/topology ADRs must be cited by at least one invariant
def _adr_title(text):
    m = re.search(r"^#\s*(\d{4})\s*[—-]\s*(.+)$", text, re.M)
    return m.group(2).strip() if m else ""


def _adr_tags(text):
    m = re.search(r"^tags:\s*(.+)$", text, re.M)
    return m.group(1) if m else ""


def protection_adrs(decisions_dir):
    """[(number, title)] for every ADR whose title/tags mark it
    protection|topology|input-protection (0000-example excluded)."""
    out = []
    for f in sorted(Path(decisions_dir).glob("*.md")):
        if f.name == "contracts.md" or f.name.startswith("0000"):
            continue
        m = re.match(r"(\d{4})", f.name)
        if not m:
            continue
        text = f.read_text()
        title = _adr_title(text)
        if PROT_RE.search(title) or PROT_RE.search(_adr_tags(text)):
            out.append((m.group(1), title))
    return out


def adr_coverage(proj, invariants_path=None):
    """Return list of problem strings: protection/topology ADRs not cited by
    any invariant. Empty list = loop closed (or nothing to close)."""
    dd = Path(proj) / "01_docs" / "decisions"
    if not dd.is_dir():
        return None  # signal N-A
    prot = protection_adrs(dd)
    if not prot:
        return []  # nothing to close
    invp = Path(invariants_path) if invariants_path else \
        Path(proj) / "03_src" / "rules" / "electrical_invariants.yaml"
    cited = set()
    if invp.exists():
        try:
            for inv in load_invariants(invp):
                cited.add(inv["_adr"])
        except LoadError:
            cited = set()  # a broken file cites nothing
    probs = []
    for num, title in prot:
        if num not in cited:
            probs.append(f"ADR {num} ({title[:60]}) is a protection/topology "
                         f"ADR but no invariant cites adr: {num} — the intent "
                         f"loop is not closed (E-ADR)")
    return probs


# --------------------------------------------------------------------------
def find_netlist(proj, override=None):
    if override:
        return Path(override)
    for pat in ("06_build/netlists/*.net", "04_kicad/*.net"):
        hits = sorted(glob.glob(str(Path(proj) / pat)))
        if hits:
            return Path(hits[0])
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description="ELECTRICAL-INVARIANTS gate (E1)")
    ap.add_argument("project")
    ap.add_argument("--netlist", default="")
    ap.add_argument("--invariants", default="")
    ap.add_argument("--adr-coverage", action="store_true",
                    help="grade E-ADR (protection ADRs must emit an invariant)")
    args = ap.parse_args(argv)
    proj = Path(args.project)

    if args.adr_coverage:
        probs = adr_coverage(proj, args.invariants or None)
        if probs is None:
            print("E-ADR N-A: no 01_docs/decisions/ (not a commissioned project)")
            return 0
        if probs:
            print("E-ADR FAIL:")
            for p in probs:
                print(f"  {p}")
            return 1
        print("E-ADR OK: every protection/topology ADR is cited by an invariant")
        return 0

    invp = Path(args.invariants) if args.invariants else \
        proj / "03_src" / "rules" / "electrical_invariants.yaml"
    if not invp.exists():
        print(f"E-INV N-A: no {invp} — the intent gate is optional")
        return 0

    try:
        invs = load_invariants(invp)
    except LoadError as e:
        print(f"E-INV LOAD ERROR: {e}")
        return 2
    if not invs:
        print("E-INV N-A: electrical_invariants.yaml has no invariants")
        return 0

    netp = find_netlist(proj, args.netlist or None)
    if netp is None or not netp.exists():
        print("E-INV LOAD ERROR: no exported netlist found "
              "(looked in 06_build/netlists/*.net, 04_kicad/*.net)")
        return 2

    nl = Netlist(netp.read_text())
    fails = check_invariants(nl, invs)
    if fails:
        print(f"E-INV FAIL: {len(fails)}/{len(invs)} invariants violated "
              f"(netlist {netp.name}):")
        for f in fails:
            print(f"  {f}")
        return 1
    print(f"E-INV OK: {len(invs)} invariants hold against {netp.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
