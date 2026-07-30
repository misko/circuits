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
    raw = Path(path).read_text(encoding="utf-8-sig")

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
    doc_supplies = {}
    if isinstance(data, dict):
        doc_supplies = {str(k): float(v)
                        for k, v in (data.get("supplies") or {}).items()}
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

    kinds = {"pin_on_net", "series_chain", "net_has_part", "part_value",
             "node_level"}          # node_level: ADR-0007
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
        inv["_supplies"] = doc_supplies          # ADR-0007 node_level
        inv.setdefault("_parts_dir", None)
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
        elif kind == "node_level":
            # ADR-0007. The kind that asserts the OUTCOME rather than the
            # mechanism: E-INV once passed 136/136 while asserting that a
            # divider's RESISTORS EXISTED, on a node sitting at 0.833 V against
            # a 2.640 V threshold. Existence was true; the claim was dead.
            for f in ("net", "receiver", "must_be"):
                if not inv.get(f):
                    raise LoadError(f"invariant #{i} node_level missing '{f}:'")
            if inv["must_be"] not in ("logic_high", "logic_low"):
                raise LoadError(f"invariant #{i} node_level must_be must be "
                                f"'logic_high' or 'logic_low', got "
                                f"{inv['must_be']!r}")
            ds = inv.get("driver_state", "released")
            if ds not in ("released", "contended"):
                raise LoadError(f"invariant #{i} node_level driver_state must "
                                f"be 'released' or 'contended', got {ds!r}")
            if ds == "contended":
                for f in ("aggressor", "defender"):
                    if not inv.get(f):
                        raise LoadError(
                            f"invariant #{i} node_level driver_state:contended "
                            f"needs '{f}:' — a contention verdict that does not "
                            f"name BOTH drivers is not reproducible")
            if "." not in str(inv["receiver"]):
                raise LoadError(f"invariant #{i} node_level receiver must be "
                                f"REF.PIN, got {inv['receiver']!r}")
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



# ---------------------------------------------------------------- node_level
# ADR-0007. Grade the LEVEL a node actually reaches against the threshold of the
# pin that reads it. This is NOT SPICE and must not be read as one: it resolves
# a series-resistive path to each rail from DATASHEET CORNER values and answers
# "is this level GUARANTEED by the published limits", which is the question the
# three findings that motivated it all turned on. Where a fact is missing it
# reports UNREACHED rather than assuming one (canon M-COVER).

def _load_part_electrical(parts_dir):
    """LCSC code OR MPN -> the dossier's `electrical:` block.

    The netlist's `value` field carries the LCSC on this pipeline and
    `sourcing.lcsc` is the other half of the join — but that is only true of
    parts this pipeline SOURCES. A SELF-SUPPLIED part has no LCSC to carry, so
    its netlist value is its MPN, and an LCSC-only join silently misses it.

    cooksense 2026-07-29: the 13 reed relays carry `DIP05-1A72-13L` as their
    netlist value, so every `node_level` assert on the coil driver came back
    UNREACHED — and the one that mattered had already been computed by hand and
    shown to PASS at +0.494 V where the superseded driver FAILED. The gate could
    not express the very margin the board was re-spun to fix. Joining on `mpn:`
    and on the dossier DIRECTORY NAME closes it.

    Rejected alternative, recorded because it looks tempting: forcing the join
    by adding the MPN to `sourcing.alternates:`. That field means SUBSTITUTE,
    and this relay is DO-NOT-SUBSTITUTE — its isolation geometry is the safety
    argument. Overloading a sourcing field to fix a lookup would have put a
    false substitution claim into the dossier.
    """
    out = {}
    if not parts_dir or not Path(parts_dir).is_dir() or yaml is None:
        return out
    sourced, named = {}, {}
    for py in sorted(Path(parts_dir).glob("*/part.yaml")):
        try:
            d = yaml.safe_load(py.read_text(encoding="utf-8-sig")) or {}
        except Exception:
            continue
        el = d.get("electrical")
        if not el:
            continue
        mpn = d.get("mpn")
        ent = {"mpn": mpn or py.parent.name, "el": el}
        src = d.get("sourcing") or {}
        if src.get("lcsc"):
            sourced.setdefault(str(src["lcsc"]), ent)
        for a in (src.get("alternates") or []):
            # alternates entries are EITHER a bare string OR a {lcsc:, mpn:}
            # mapping — BOTH forms occur in the tree and the 02_parts contract's
            # own example shows the bare one. Reading only one form is a silent
            # skip inside a lookup authority.
            vals = ([v for k, v in a.items() if k in ("lcsc", "mpn") and v]
                    if isinstance(a, dict) else [a])
            for v in vals:
                sourced.setdefault(str(v), ent)
        for extra in (mpn, py.parent.name):
            if extra:
                named.setdefault(str(extra), ent)
    # PRECEDENCE IS EXPLICIT, not glob order: a SOURCING code always wins over a
    # key derived from an MPN or a directory name, so widening the join cannot
    # shadow a real LCSC lookup with some other dossier's name.
    out.update(named)
    out.update(sourced)
    return out


def _pin_facts(elec, code, pin):
    """Facts for one pin: explicit entry, else the part's defaults."""
    ent = elec.get(code)
    if not ent:
        return None, None
    el = ent["el"]
    pins = {str(k): v for k, v in (el.get("pins") or {}).items()}
    facts = dict(el.get("defaults") or {})
    facts.update(pins.get(str(pin)) or {})
    return ent["mpn"], facts


def _resistive_path(nl, start_net, target_nets, elec, max_depth=6):
    """Sum series resistance from `start_net` to the nearest of `target_nets`,
    walking ONLY through 2-pin parts that carry a decodable value. Returns
    (ohms, path) or (None, reason). Refuses on branching rather than guessing —
    a wrong number here would be worse than no number."""
    seen = {start_net}
    frontier = [(start_net, 0.0, [])]
    for _ in range(max_depth):
        nxt = []
        for net, acc, path in frontier:
            for (ref, pin, _f) in nl.pins_of_net.get(net, []):
                pins = nl.part_pins.get(ref) or {}
                if len(pins) != 2:
                    continue
                # RESISTORS ONLY. The first run of this walker traversed
                # `CE1=220u` — a 220 uF bulk capacitor — because parse_si
                # happily decodes "220u" and CE1 is a 2-pin part, and it
                # reported a confident WRONG path. A DC series path may only
                # go through resistance.
                if refdes_prefix(ref) not in TYPE_PREFIX["resistor"]:
                    continue
                val = parse_si(nl.part_value.get(ref, ""))
                if val is None:
                    continue
                other = [p for p in pins if str(p) != str(pin)]
                if len(other) != 1:
                    continue
                onet = pins[other[0]].get("net")
                if not onet or onet in seen:
                    continue
                if onet in target_nets:
                    return acc + val, path + [f"{ref}={fmt_si(val)}"]
                seen.add(onet)
                nxt.append((onet, acc + val, path + [f"{ref}={fmt_si(val)}"]))
        frontier = nxt
        if not frontier:
            break
    return None, "no series-resistive path found within depth %d" % max_depth


def _grade_node_level(inv, nl, parts_dir=None, supplies=None):
    adr = inv["_adr"]
    net = str(inv["net"])
    recv = str(inv["receiver"])
    rref, _, rpin = recv.partition(".")
    want = inv["must_be"]
    ds = inv.get("driver_state", "released")
    supplies = supplies or {}

    if net not in nl.pins_of_net:
        return (f"node_level (ADR {adr}): net {net!r} is not in the netlist")
    if (rref, rpin) not in nl.net_of_pin:
        return (f"node_level (ADR {adr}): receiver {recv} is not in the netlist")
    if nl.net_of_pin[(rref, rpin)] != net:
        return (f"node_level (ADR {adr}): receiver {recv} is on net "
                f"{nl.net_of_pin[(rref, rpin)]!r}, not the asserted {net!r}")

    elec = _load_part_electrical(parts_dir)
    rcode = nl.part_value.get(rref, "")
    rmpn, rf = _pin_facts(elec, rcode, rpin)
    if not rf or ("v_ih_min" not in rf and "v_ih_min_frac_vdd" not in rf):
        return (f"UNREACHED node_level (ADR {adr}): receiver {recv} "
                f"(code {rcode!r}) declares no input thresholds — add an "
                f"`electrical:` block to its 02_parts dossier. Reported "
                f"UNREACHED, not passed (canon M-COVER)")

    vdd = float(rf.get("vdd", supplies.get(rf.get("vdd_net", "3V3"), 3.3)))
    vih = float(rf["v_ih_min"]) if "v_ih_min" in rf else vdd * float(rf["v_ih_min_frac_vdd"])
    vil = float(rf["v_il_max"]) if "v_il_max" in rf else vdd * float(rf.get("v_il_max_frac_vdd", 0.2))

    if ds == "released":
        gnd = {n for n in nl.pins_of_net if n.upper() in ("GND", "AGND", "DGND")}
        rails = {n: v for n, v in supplies.items() if n in nl.pins_of_net}
        if not rails:
            return (f"UNREACHED node_level (ADR {adr}): no supply rail voltages "
                    f"declared — add `supplies:` to the invariants file")
        r_dn, p_dn = _resistive_path(nl, net, gnd, elec)
        best = None
        for rail, vsup in rails.items():
            r_up, p_up = _resistive_path(nl, net, {rail}, elec)
            if isinstance(r_up, float) and (best is None or r_up < best[0]):
                best = (r_up, rail, float(vsup), p_up)
        if best is None:
            # THE MIRROR OF THE PULL-UP CASE BELOW, and its absence was an
            # asymmetry rather than a limit. With no resistive path to any rail
            # but a resistive path to GND, a released node is pulled DOWN — that
            # is exactly what a RESTRICTIVE DEFAULT is (cooksense ADR-0019 adds
            # eleven of them, and ADR-0025's unfitted safety inputs are the
            # same shape: the pull-down alone holds the node, measured at
            # 1.15 mV against V_T-(min) 0.500 V). The pull-up half was special-
            # cased from the start and this half was not, so every
            # restrictive-default node in the fleet graded UNREACHED and the one
            # assert a board most wanted to write could not be written.
            if isinstance(r_dn, float):
                v = 0.0
                detail = (f"no resistive path to any declared rail, pulled to "
                          f"GND through {fmt_si(r_dn)} [{' + '.join(p_dn)}] "
                          f"-> {v:.3f} V (restrictive default)")
                ok = (v >= vih) if want == "logic_high" else (v <= vil)
                if ok:
                    return None
                thr = (f"V_IH(min) {vih:.3f} V" if want == "logic_high"
                       else f"V_IL(max) {vil:.3f} V")
                return (f"node_level (ADR {adr}): {net} reads {v:.3f} V at "
                        f"{recv}, required {want.replace('_', ' ')} against "
                        f"{thr} — {detail}. {inv.get('why', '')[:70]}")
            return (f"UNREACHED node_level (ADR {adr}): no series-RESISTIVE "
                    f"path from {net!r} to any declared rail, and none to GND "
                    f"either — the node is held by nothing this gate can see. "
                    f"A DC path may not run through a capacitor or an "
                    f"inductor, so this is refused rather than guessed")
        r_up, rail, vsup, p_up = best
        if isinstance(r_dn, float):
            v = vsup * r_dn / (r_up + r_dn)
            detail = (f"{vsup:.3f} V via {rail} through {fmt_si(r_up)} "
                      f"[{' + '.join(p_up)}] over {fmt_si(r_dn)} "
                      f"[{' + '.join(p_dn)}] -> {v:.3f} V")
        else:
            # No resistive path to GND: with every open-drain driver released
            # the node is simply pulled to the rail. This is the ordinary
            # pull-up case and must NOT be reported as unresolvable.
            v = vsup
            detail = (f"{vsup:.3f} V via {rail} through {fmt_si(r_up)} "
                      f"[{' + '.join(p_up)}], no resistive path to GND "
                      f"-> pulled to the rail, {v:.3f} V")
    else:
        acode = nl.part_value.get(str(inv["aggressor"]).split(".")[0], "")
        dcode = nl.part_value.get(str(inv["defender"]).split(".")[0], "")
        _, af = _pin_facts(elec, acode, str(inv["aggressor"]).partition(".")[2])
        _, df = _pin_facts(elec, dcode, str(inv["defender"]).partition(".")[2])
        if not af or not df or "r_on_ohm_max" not in (af or {}) or "r_on_ohm_max" not in (df or {}):
            return (f"UNREACHED node_level (ADR {adr}): contention needs "
                    f"`r_on_ohm_max` on BOTH {inv['aggressor']} and "
                    f"{inv['defender']}; one or both dossiers lack it")
        ra, rd = float(af["r_on_ohm_max"]), float(df["r_on_ohm_max"])
        vsup = float(af.get("vdd", vdd))
        v = vsup * rd / (ra + rd)
        detail = (f"aggressor {inv['aggressor']} r_on<={fmt_si(ra)} vs defender "
                  f"{inv['defender']} r_on<={fmt_si(rd)} at {vsup:.3f} V "
                  f"-> {v:.3f} V")

    ok = (v >= vih) if want == "logic_high" else (v <= vil)
    if ok:
        return None
    thr = f"V_IH(min) {vih:.3f} V" if want == "logic_high" else f"V_IL(max) {vil:.3f} V"
    return (f"node_level (ADR {adr}): {net} reads {v:.3f} V at {recv}, "
            f"required {want.replace('_', ' ')} against {thr} — {detail}. "
            f"{inv.get('why', '')[:70]}")


_GRADERS["node_level"] = _grade_node_level     # ADR-0007; registered here
# because the dict literal above is defined before the grader body.


def _check_declared_supplies(nl, invs):
    """Every net named in `supplies:` must EXIST in the netlist.

    The trap this closes, found on cooksense 2026-07-29: the invariants file
    declared `supplies: {N3V3: 3.3}` — the tsx AUTHOR-PREFIX form — and no net
    called `N3V3` exists in the netlist. `_grade_node_level` filters `supplies`
    to nets it can see, so the 3V3 rail was silently INVISIBLE to every
    node_level grade on the board. A misnamed rail does not announce itself: it
    either downgrades a grade to UNREACHED for the wrong reason, or lets a
    DIFFERENT rail win the shortest-path search and reports a confident wrong
    voltage. Declared-but-absent is a source-file defect, so it is graded at
    full width (canon M-WIDTH) whenever `supplies:` is present at all — not
    only when a node_level assert happens to consult the rail.
    """
    declared = {}
    for inv in invs:
        declared.update(inv.get("_supplies") or {})
    if not declared:
        return []
    nets = set(nl.pins_of_net)
    upper = {n.upper(): n for n in nets}
    out = []
    for name in sorted(declared):
        if name in nets:
            continue
        # near-miss: the author-prefix form, and case
        cands = [c for c in (upper.get(name.upper()),
                             upper.get(name.upper().lstrip("N")),
                             upper.get("N" + name.upper())) if c]
        hint = (f" Did you mean {cands[0]!r}?" if cands else
                " No net with a similar name exists either.")
        out.append(f"supplies: declared rail net {name!r} is NOT in the "
                   f"netlist, so every node_level assert that would consult "
                   f"it is graded without it.{hint}")
    return out


def check_invariants(nl, invs):
    """Grade all invariants; return list of failure strings (empty = all pass)."""
    fails = _check_declared_supplies(nl, invs)
    for inv in invs:
        g = _GRADERS[inv["assert"]]
        if inv["assert"] == "node_level":
            f = g(inv, nl, inv.get("_parts_dir"), inv.get("_supplies"))
        else:
            f = g(inv, nl)
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


def _adr_status(text):
    """The ADR's front-matter `status:`, lowercased, comment stripped.

    Read from the `---` FRONT MATTER ONLY. The word `status:` occurs in ADR
    PROSE ("its status: superseded") often enough that a whole-file grep is a
    liability — the S-VER defect verbatim, where a cross-reference inside a
    comment shadowed the real key.
    """
    m = re.match(r"\s*---\s*\n(.*?)\n---\s*$", text, re.S | re.M)
    if not m:
        return ""
    s = re.search(r"^status:\s*(.+)$", m.group(1), re.M)
    if not s:
        return ""
    # `status: accepted    # proposed | accepted | rejected | superseded-by-0012`
    # is the TEMPLATE's own placeholder line and appears on 10 live ADRs. The
    # value is `accepted`; the vocabulary reminder after the `#` is a comment
    # and must never be read as the status.
    return re.split(r"\s+#", s.group(1))[0].strip().lower()


def protection_adrs(decisions_dir):
    """[(number, title)] for every ADR whose title/tags mark it
    protection|topology|input-protection.

    EXCLUDED: `0000-example` (the template), and any ADR whose front-matter
    `status:` starts with `superseded`.

    WHY THE STATUS READ (2026-07-28, declared gap O8b). E-ADR demanded an
    invariant from every protection/topology ADR ever written, including ones
    whose decision NO LONGER EXISTS. pluto-cal-switch ADR-0006 (SMA->SMP
    adapters on the Pluto) was reversed outright by ADR-0015 (SMA cables, five
    true SMA jacks); there is no topology left to assert, and E-ADR reported
    FAIL 11/12 for a hole that cannot be filled. The gap was DECLARED rather
    than gamed by retagging the ADR, which is the right call and also why the
    fix belongs here: retagging would have hidden a live ADR's protection tag
    to silence a checker, and the next reader would have inherited a lie.

    A superseded ADR's invariants do not vanish — they moved to its successor,
    which is itself graded. What is dropped is the DEMAND on a decision that
    was withdrawn.
    """
    out = []
    for f in sorted(Path(decisions_dir).glob("*.md")):
        if f.name == "contracts.md" or f.name.startswith("0000"):
            continue
        m = re.match(r"(\d{4})", f.name)
        if not m:
            continue
        text = f.read_text(encoding="utf-8-sig")
        if _adr_status(text).startswith("superseded"):
            continue
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
    for _iv in invs:                       # ADR-0007: dossiers hold the facts
        if _iv.get("_parts_dir") is None:
            _iv["_parts_dir"] = str(Path(proj) / "02_parts")
    if not invs:
        print("E-INV N-A: electrical_invariants.yaml has no invariants")
        return 0

    netp = find_netlist(proj, args.netlist or None)
    if netp is None or not netp.exists():
        print("E-INV LOAD ERROR: no exported netlist found "
              "(looked in 06_build/netlists/*.net, 04_kicad/*.net)")
        return 2

    nl = Netlist(netp.read_text(encoding="utf-8-sig"))
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
