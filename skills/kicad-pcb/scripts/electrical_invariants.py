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
  pin_on_net    {assert: pin_on_net, pin: "D1.1", net: VIN, adr: "0001", why: ...}
                the named pin must be on the named net (the D1 class).
  series_chain  {assert: series_chain, chain: [BATT_P, F1, Q1, VIN],
                 through: {Q1: [D, S]}, adr: "0001", why: ...}
                consecutive elements share a net in order. A 2-pad part
                bridges the nets on its two pads (inferred); a >2-pad part
                names its bridging pins with `through: {REF: [in, out]}`.
  net_has_part  {assert: net_has_part, net: VIN_S, part_type: capacitor,
                 min: 1, adr: "0007", why: ...}
                the net must carry >= min parts of that type (by refdes
                prefix). The bridge-rail-decoupling class red-team B found.
  part_value    {assert: part_value, part: R_WDPETPD, max: 5.2k,
                 adr: "0011", why: ...}
                the part's VALUE must satisfy min/max/equals (+ tolerance_pct
                on equals). See below — this kind exists because EVERY P0 this
                pipeline found on 2026-07-25 was in a PARAMETER, and the three
                kinds above pin TOPOLOGY.

Every invariant REQUIRES `adr:` (the ADR that emitted it) and `why:`.

`adr:` MUST BE QUOTED — AND THE GATE REJECTS IT WHEN IT IS NOT
-------------------------------------------------------------
A zero-padded ADR reference written BARE is a YAML 1.1 OCTAL literal:

    adr: 0011   ->  the integer 9    ->  re-padded to "0009"
    adr: 0012   ->  the integer 10   ->  re-padded to "0010"
    adr: 0010   ->  the integer 8    ->  re-padded to "0008"
    adr: 0020   ->  the integer 16   ->  re-padded to "0016"
    adr: 0008   ->  the STRING "0008"  (8 is not an octal digit, so the
                                        resolver declines and it survives)

So `adr: 0011` did not skip a check — it SILENTLY SATISFIED ADR 0009, and
E-ADR then reported ADR 0011 as uncited while crediting an ADR that emitted
nothing. That is worse than a skip: a skip is visible in a coverage
denominator, a misresolution is a green verdict about the wrong document.
Whether a given padding survives depends on nothing but which digits it
contains, which is why the rule is written at the width of the CLASS (canon
M-WIDTH): EVERY unquoted zero-padded `adr:` is rejected, including the ones
that happen to survive.

WHY REJECT RATHER THAN COERCE. Coercing to `str()` at parse time cannot work
and would be the silent-wrong-answer again: by the time `yaml.safe_load()`
returns, `0011` IS the integer 9 and `str(9).zfill(4)` is "0009" — the
padding, the only evidence of the author's intent, is already destroyed and
`adr: 9` and `adr: 0011` are indistinguishable. The padding survives ONLY in
the source text, so the check is made on the composed NODE (which carries the
scalar's quoting style), before any value is constructed, and the verdict is a
LoadError naming the line. `adr: 11` and `adr: "0011"` both remain legal.

WHY `part_value` EXISTS — AN INVARIANT THAT PINS EXISTENCE DOES NOT PIN VALUE
----------------------------------------------------------------------------
smc0985-cooksense, 2026-07-25 (commits ab94de3 then 929b089). A safety P0 was
found: WD_PET, the TPS3823 watchdog heartbeat, had no pull-down, so with the
Pi unplugged the supervisor self-pulsed, WD_OK never fell, and the external
COOKING CONTACTOR stayed energised indefinitely. The fix added a pull-down —
AT 100k. TI SLVS165O S6.5 gives I_IL at WDI = 190 uA MAX and the pin SOURCES
it, so the hold resistor is bounded by I_IL x R < V_IL:

    R_max = V_IL / I_IL(max) = (0.3 x 3.3 V) / 190 uA = 0.99 V / 190 uA ~= 5.2k
    1k    -> 0.19 V, 81% margin (TI's own recommended value)
    100k  -> the node sits at ~VDD; THE WATCHDOG IS SILENTLY DISABLED

So the 100k board looked exactly like the fixed board and was not fixed. And
ALL THREE E-INV assertions that landed with that fix — one `net_has_part` plus
two `pin_on_net` — PASS on the 100k netlist. They had to: they assert that a
resistor EXISTS on WD_PET and that its pads are on the right nets, and all of
that is true of the wrong resistor. The commit body states the lesson in one
line: "An invariant that pins a component's EXISTENCE does not pin its VALUE."

`part_value` closes it. Values are read from the netlist's own
`(comp (ref ...) (value ...))` block — the same artifact every other E-INV kind
is graded against — and compared numerically after SI decoding, so `1kOhm`,
`1k`, `1kΩ`, `1K` and `0.001M` are one number and `100k` fails a `max: 5.2k`.

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
# SI value decoding, for `part_value`.
#
# Case matters and is the whole trap: `m` is MILLI and `M` is MEGA, so a
# case-folding parser turns a 4.7M feedback resistor into 4.7 milliohms and
# reports a comfortable pass. Everything else about the notation is noise we
# must absorb, because a fleet netlist really does carry "1kOhm", "1k", "1kΩ",
# "4k7", "0R1", "100nF" and "10uF 25V" for values a human calls the same thing.
_SI = {"p": 1e-12, "n": 1e-9, "u": 1e-6, "µ": 1e-6, "μ": 1e-6, "m": 1e-3,
       "R": 1.0, "r": 1.0, "k": 1e3, "K": 1e3, "M": 1e6, "G": 1e9}
_UNIT_RE = re.compile(r"(ohms?|ohm|Ω|Ω|F|H|V|A|W|%)$", re.I)


def parse_si(text):
    """'100k' -> 100000.0, '4k7' -> 4700.0, '1kOhm' -> 1000.0, '10uF' -> 1e-5.

    Returns None when the string carries no decodable number — which the
    grader reports as a FAILURE, never as a pass. A value it cannot read is
    a value it cannot vouch for.
    """
    if text is None:
        return None
    s = str(text).strip()
    if not s:
        return None
    s = s.split()[0]                      # "10uF 25V" -> "10uF"
    s = s.replace(",", "")
    s = _UNIT_RE.sub("", s)               # strip a trailing unit, keep the SI
    # infix form: 4k7, 0R1, 1M2 — the decimal point IS the multiplier letter
    m = re.fullmatch(r"([0-9]*)([pnuµμmRrkKMG])([0-9]+)", s)
    if m:
        try:
            return float(f"{m.group(1) or '0'}.{m.group(3)}") * _SI[m.group(2)]
        except (ValueError, KeyError):
            return None
    m = re.fullmatch(r"([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)"
                     r"([pnuµμmRrkKMG]?)", s)
    if not m:
        return None
    try:
        return float(m.group(1)) * (_SI[m.group(2)] if m.group(2) else 1.0)
    except (ValueError, KeyError):
        return None


def fmt_si(v):
    for suf, mul in (("G", 1e9), ("M", 1e6), ("k", 1e3), ("", 1.0),
                     ("m", 1e-3), ("u", 1e-6), ("n", 1e-9), ("p", 1e-12)):
        if abs(v) >= mul:
            return f"{v / mul:g}{suf}"
    return f"{v:g}"


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
        self.part_value = {}          # ref -> value string (the `part_value`
                                      # kind; the SAME artifact every other
                                      # E-INV kind is graded against)

        def walk(node):
            if not isinstance(node, list):
                return
            if _head(node) == "net":
                self._add_net(node)
            elif _head(node) == "comp":
                self._add_comp(node)
            for c in node:
                if isinstance(c, list):
                    walk(c)

        for top in tree:
            walk(top)

    def _add_comp(self, node):
        ref = _first_atom(node, "ref")
        if ref is None:
            return
        val = _first_atom(node, "value")
        if val is not None:
            self.part_value[ref] = val

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


#: an UNQUOTED zero-padded scalar — the YAML 1.1 octal hazard. Written at the
#: width of the class (M-WIDTH): `0011`/`0012`/`0020` misresolve, `0008`/`0009`
#: survive only because 8 and 9 are not octal digits. All are rejected, because
#: "which of these is safe" is a fact about the digits, not about the schema.
_PADDED_RE = re.compile(r"0\d+")


def _bare_padded_adr_refs(text):
    """[(line_no, literal, resolves_to)] for every `adr:` whose value is an
    UNQUOTED zero-padded integer.

    Graded on the COMPOSED NODE, not on the constructed value and not on a
    text regex: a composed ScalarNode carries `style` (None == plain/unquoted)
    and its original `value` string, which is the only place the padding still
    exists. `yaml.safe_load()` has already destroyed it — see the module
    docstring — so a check that ran after it would be checking the wrong
    artifact (the adjacent-property error).
    """
    out = []
    try:
        root = yaml.compose(text)
    except yaml.YAMLError:
        return out                      # safe_load below raises its own error
    seen = []

    def walk(node):
        if isinstance(node, yaml.MappingNode):
            for k, v in node.value:
                if (isinstance(k, yaml.ScalarNode) and k.value == "adr"
                        and isinstance(v, yaml.ScalarNode)
                        and v.style is None
                        and _PADDED_RE.fullmatch(v.value)):
                    seen.append((v.start_mark.line + 1, v.value))
                walk(v)
        elif isinstance(node, yaml.SequenceNode):
            for c in node.value:
                walk(c)

    walk(root)
    for line, lit in seen:
        got = yaml.safe_load(f"v: {lit}")["v"]
        if not isinstance(got, int):
            verdict = "SURVIVES"     # not valid octal, stayed a string
        elif _norm_adr(got) == lit:
            verdict = "IDENTITY"     # octal value == decimal value, by luck
        else:
            verdict = "MISRESOLVES"
        out.append((line, lit, _norm_adr(got) if isinstance(got, int) else None,
                    verdict))
    return out


def load_invariants(path):
    """Parse + validate. Raises LoadError with a naming message on any schema
    problem (missing adr/why, unknown assert kind, unknown part_type, an
    UNQUOTED zero-padded `adr:`)."""
    if yaml is None:
        raise LoadError("PyYAML not available")
    raw = Path(path).read_text()

    # Reject the YAML-octal ADR reference BEFORE anything is constructed. This
    # runs first because it is the only check whose evidence safe_load erases.
    padded = _bare_padded_adr_refs(raw)
    if padded:
        wrong = [b for b in padded if b[3] == "MISRESOLVES"]
        bits = []
        for line, lit, resolves, verdict in padded:
            if verdict == "MISRESOLVES":
                bits.append(f"line {line}: `adr: {lit}` SILENTLY BECOMES ADR "
                            f"{resolves} (YAML 1.1 octal) — it satisfies the "
                            f"WRONG ADR instead of failing")
            elif verdict == "SURVIVES":
                bits.append(f"line {line}: `adr: {lit}` survives as a string "
                            f"only because {lit.lstrip('0')[0]} is not an "
                            f"octal digit")
            else:
                bits.append(f"line {line}: `adr: {lit}` still means ADR "
                            f"{resolves} only because its octal and decimal "
                            f"values coincide")
        raise LoadError(
            f"{Path(path).name}: {len(padded)} unquoted zero-padded `adr:` "
            f"reference(s), {len(wrong)} of which resolve to a DIFFERENT ADR "
            f"— QUOTE them (adr: \"0011\") or drop the padding (adr: 11). "
            f"Whether a given one is safe today depends only on its digits, "
            f"so all are rejected (canon M-WIDTH). "
            + "; ".join(bits[:12])
            + ("" if len(bits) <= 12 else
               f"; ... and {len(bits) - 12} more (this list is TRUNCATED at "
               f"12; the count above is the complete one)"))

    data = yaml.safe_load(raw)
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

    kinds = {"pin_on_net", "series_chain", "net_has_part", "part_value"}
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
        elif kind == "part_value":
            if not inv.get("part"):
                raise LoadError(f"invariant #{i} part_value missing 'part:'")
            bounds = [k for k in ("min", "max", "equals") if k in inv]
            if not bounds:
                raise LoadError(
                    f"invariant #{i} part_value on {inv['part']!r} declares no "
                    f"bound — needs at least one of min:/max:/equals:. An "
                    f"invariant that names a part and asserts NOTHING about "
                    f"its value is the exact gap this kind was added to close")
            for k in bounds:
                if parse_si(inv[k]) is None:
                    raise LoadError(
                        f"invariant #{i} part_value {k}: {inv[k]!r} is not a "
                        f"decodable value (SI notation: 5.2k, 4k7, 100nF, "
                        f"0R1; note m=milli and M=mega are DIFFERENT)")
            if "tolerance_pct" in inv and "equals" not in inv:
                raise LoadError(f"invariant #{i} part_value: tolerance_pct is "
                                f"only meaningful with equals:")
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


def _grade_part_value(inv, nl):
    """THE PARAMETER CLASS. Every other kind here pins TOPOLOGY: which parts
    exist and what they connect to. cooksense proved that is not enough — its
    watchdog pull-down was present, on the right two nets, and 100k where the
    datasheet bounds it at 5.2k, and all three topology invariants PASSED on
    that board."""
    ref = str(inv["part"])
    adr = inv["_adr"]
    raw = nl.part_value.get(ref)
    if raw is None:
        if ref not in nl.part_pins:
            return (f"part_value (ADR {adr}): part {ref!r} is not in the "
                    f"netlist at all")
        return (f"part_value (ADR {adr}): {ref} has no value field in the "
                f"netlist — an unreadable value is not a pass")
    got = parse_si(raw)
    if got is None:
        return (f"part_value (ADR {adr}): {ref} value {raw!r} cannot be "
                f"decoded as a number — a value the gate cannot read is a "
                f"value it cannot vouch for")
    why = str(inv.get("why", ""))[:100]
    if "equals" in inv:
        want = parse_si(inv["equals"])
        tol = float(inv.get("tolerance_pct", 0)) / 100.0
        if abs(got - want) > abs(want) * tol + 1e-12:
            band = f" +/-{inv['tolerance_pct']}%" if tol else ""
            return (f"part_value (ADR {adr}): {ref} is {raw} ({fmt_si(got)}), "
                    f"invariant requires {inv['equals']}{band} — {why}")
    if "max" in inv:
        want = parse_si(inv["max"])
        if got > want + 1e-12:
            return (f"part_value (ADR {adr}): {ref} is {raw} ({fmt_si(got)}), "
                    f"invariant requires <= {inv['max']} ({fmt_si(want)}) — "
                    f"{why}")
    if "min" in inv:
        want = parse_si(inv["min"])
        if got < want - 1e-12:
            return (f"part_value (ADR {adr}): {ref} is {raw} ({fmt_si(got)}), "
                    f"invariant requires >= {inv['min']} ({fmt_si(want)}) — "
                    f"{why}")
    return None


_GRADERS = {
    "pin_on_net": _grade_pin_on_net,
    "series_chain": _grade_series_chain,
    "net_has_part": _grade_net_has_part,
    "part_value": _grade_part_value,
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
    # accept BOTH heading conventions: "# 0002 — title" and "# ADR-0002 — title"
    # (the crow boards + usb-hub-3s-v3 use the ADR- prefix; without this, the
    # title was '' -> protection_adrs() found nothing -> E-ADR passed VACUOUSLY
    # fleet-wide, asserting nothing — found by the crow re-audits 2026-07-22).
    m = re.search(r"^#\s*(?:ADR[-\s]?)?(\d{4})\s*[—-]\s*(.+)$", text, re.M)
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
    """(probs, cited_count, total, invp) — protection/topology ADRs not cited
    by any invariant. Empty probs = loop closed (or nothing to close).
    `None` in place of the tuple signals N-A (not a commissioned project).

    RAISES LoadError when the invariants file will not parse. It used to
    swallow it:

        except LoadError:
            cited = set()   # "a broken file cites nothing"

    which is TRUE and is still the wrong verdict. One weak `why:` field turned
    into a report of 10 uncited protection ADRs that never once named the parse
    failure, so the reader chased ten phantom coverage holes instead of one
    typo. Canon M-COVER: **input a gate cannot parse is a FAIL that names
    itself, never a zero.** A zero is a measurement; this was not one.
    """
    dd = Path(proj) / "01_docs" / "decisions"
    if not dd.is_dir():
        return None  # signal N-A
    prot = protection_adrs(dd)
    invp = Path(invariants_path) if invariants_path else \
        Path(proj) / "03_src" / "rules" / "electrical_invariants.yaml"
    if not prot:
        return [], 0, 0, invp  # nothing to close
    cited = set()
    if invp.exists():
        for inv in load_invariants(invp):     # LoadError propagates, by design
            cited.add(inv["_adr"])
    probs = []
    for num, title in prot:
        if num not in cited:
            probs.append(f"ADR {num} ({title[:60]}) is a protection/topology "
                         f"ADR but no invariant cites adr: {num} — the intent "
                         f"loop is not closed (E-ADR)")
    return probs, len(prot) - len(probs), len(prot), invp


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
        try:
            res = adr_coverage(proj, args.invariants or None)
        except LoadError as e:
            # M-COVER: a parse failure NAMES ITSELF. It is never a zero, and it
            # is never re-reported as "every protection ADR is uncited".
            print(f"E-ADR LOAD ERROR: the invariants file will not parse, so "
                  f"E-ADR graded 0 of its ADRs and says so rather than "
                  f"reporting them all uncited: {e}")
            return 2
        if res is None:
            print("E-ADR N-A: no 01_docs/decisions/ (not a commissioned project)")
            return 0
        probs, cited, total, invp = res
        if total == 0:
            print(f"E-ADR OK: 0/0 — no protection/topology ADR under "
                  f"{proj / '01_docs' / 'decisions'}, nothing to close")
            return 0
        if probs:
            print(f"E-ADR FAIL: {cited}/{total} protection/topology ADR(s) "
                  f"cited by an invariant (graded against {invp}):")
            for p in probs:
                print(f"  {p}")
            return 1
        print(f"E-ADR OK: {cited}/{total} protection/topology ADR(s) cited by "
              f"an invariant (graded against {invp})")
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
    print(f"E-INV OK: {len(invs)}/{len(invs)} invariants hold against {netp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
