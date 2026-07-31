#!/usr/bin/env python3
"""circuit_json_to_kicad_sch — OUR native converter from tscircuit's canonical
`circuit.json` intermediate to an ANNOTATED KiCad `.kicad_sch`, bypassing
tscircuit's own `kicad_sch` exporter.

WHY this exists (ADR-0001 Phase 2). tscircuit's native `tsci export -f kicad_sch`
has two proven, fidelity-killing bugs on real boards:
  1. Symbol-id collision — a chip's schematic symbol id is derived as
     `Device:U_chip_<footprintName>`; a hand-authored `<footprint>` has no name,
     so EVERY custom-footprint chip collapses to bare `Device:U_chip`. With >=2
     such many-pin chips (e.g. an ESP32 module + a USB-C jack) both reference one
     shared symbol and each TRUNCATES TO 2 PINS, silently dropping the rest.
  2. No symbol annotation — the exported sheet is un-annotated, so
     `kicad-cli sch export netlist` builds 0 nets from it.

`circuit.json` carries the FULL connectivity model (source_component / source_port /
source_net / source_trace + the pcb_* pad geometry) that measured node-for-node
parity on all three Phase-1 boards. We render THAT model into a native, annotated
sheet where every component gets a UNIQUE per-refdes lib_symbol (collision
impossible by construction) and connectivity is glued with ONE global_label per pin
carrying the net name (schwriter2's net-glue rule) — the netlister joins by
label-name = exact parity. GND pins render as power ground symbols with a single
PWR_FLAG so ERC's power-driven check stays at zero.

Emission machinery (lib_symbol grammar, power symbols, instance/label s-exprs) is
reused from `schwriter2.py` in this same scripts dir — the proven KiCad 7/10 dialect.

BACKEND-READY (ADR-0001 Phase 2/3 completion). The output is directly consumable
by the full KiCad backend (generate_board -> rules -> KRT -> DRC --schematic-parity)
with NO per-board adapter — the five Phase-3 adapter transforms are folded in here:
  1. CANONICAL NET NAMES. tscircuit can't author a leading-digit net name, so a
     rail is authored with a documented author-prefix `N` (`5V`->`N5V`,
     `3V3`->`N3V3`, `12V`->`N12V`). `canon_net` strips that guard prefix and emits
     the canonical KiCad name on the global labels; an optional per-board
     `03_tscircuit/net_aliases.txt` (auto-discovered) covers anything the convention
     misses.
  2. FOOTPRINT FPIDs. Each symbol's Footprint field is filled from a baked-in
     COMMODITY token->FPID map (circuit.json class-disambiguates: `res0603` vs
     `0603`) with a per-board override seeded from `02_parts/*/part.yaml`
     (MPN/LCSC -> footprint, auto-discovered) that WINS for specialty parts.
  3. NO MPN FIELD (KiCad footprints carry none -> footprint_symbol_field_mismatch).
  4. TP BOM ATTRS. Test-point symbols are `in_bom no` (matching the KiCad
     TestPoint footprint) with a concise `TP` Value that won't clip the board edge.
Proven: cook-loadcell drives the whole backend to DRC 0/0/0 + board parity 0 from
this output ALONE (evidence snapshot: examples/tsx-backend-proof/).

Connectivity resolution (validated node-for-node vs the sealed KiCad boards):
  * NET per port: group by `source_net.subcircuit_connectivity_map_key`
    (each source_port carries the same key); a port with no keyed net is a
    no-connect. Then PROPAGATE through `internally_connected_source_port_ids`
    (split shields / thermal pads) so every member of an internal group shares
    the one resolved net.
  * PAD NAME per port: the first `pcb_smtpad`/`pcb_plated_hole` `port_hints` entry
    that is NOT an auto-alias (`unnamed_*`); fall back to the pin_number. This is
    the exact KiCad pad name, so the exported netlist nodes match the sealed board.
  * Duplicate pads that share a pad name (internally-connected shields, split
    thermal pads) collapse to ONE symbol pin — matching how the KiCad netlist
    dedupes them.

Usage:
  circuit_json_to_kicad_sch.py <circuit.json> -o <out.kicad_sch> [--project NAME]
                               [--title T] [--rev R]
"""
import argparse
import datetime
import json
import math
import os
import re
import sys
import uuid

# reuse the proven emission machinery
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schwriter2 as sw  # noqa: E402

GRID = 1.27
PIN_LEN = 2.54
CH_W = 1.05          # global-label plate per-char width (schwriter2 S-OCCL model)
LIB = "elt"

# ------------------------------------------------------------------ FPID map
# Commodity tscircuit-footprinter TOKEN -> canonical KiCad FPID ("lib:name").
# circuit.json (cad_component.footprinter_string) class-disambiguates passives:
# a resistor emits `res0603`, a capacitor the bare `0603` — so R-vs-C is decided
# by the token itself, no per-class table needed. Specialty parts (connectors,
# ICs) are NOT here; they resolve from the project's 02_parts/*/part.yaml
# override (MPN/LCSC -> footprint), which takes precedence over this map.
COMMODITY_FP = {
    # resistors (circuit.json emits res<size> for a <resistor>)
    "res0402": "Resistor_SMD:R_0402_1005Metric",
    "res0603": "Resistor_SMD:R_0603_1608Metric",
    "res0805": "Resistor_SMD:R_0805_2012Metric",
    "res1206": "Resistor_SMD:R_1206_3216Metric",
    "res1210": "Resistor_SMD:R_1210_3225Metric",
    # capacitors (bare size token == capacitor in circuit.json)
    "0402": "Capacitor_SMD:C_0402_1005Metric",
    "0603": "Capacitor_SMD:C_0603_1608Metric",
    "0805": "Capacitor_SMD:C_0805_2012Metric",
    "1206": "Capacitor_SMD:C_1206_3216Metric",
    "1210": "Capacitor_SMD:C_1210_3225Metric",
    # discrete semiconductors / SOT-SOD packages
    "sot23": "Package_TO_SOT_SMD:SOT-23",
    "sot23_3": "Package_TO_SOT_SMD:SOT-23",
    "sot23_5": "Package_TO_SOT_SMD:SOT-23-5",
    "sot23_6": "Package_TO_SOT_SMD:SOT-23-6",
    "sot223": "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
    "sod323": "Diode_SMD:D_SOD-323",
    "sod123": "Diode_SMD:D_SOD-123",
    "sma": "Diode_SMD:D_SMA",
    "smb": "Diode_SMD:D_SMB",
    # SO / SOIC packages
    "soic8_p1.27mm": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
    "soic14_p1.27mm": "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
    "soic16_p1.27mm": "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
    # pin headers / connectors
    "pinrow2": "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
    "pinrow3": "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
    "pinrow4": "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
    "pinrow5": "Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical",
    "pinrow6": "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical",
    "pinrow7": "Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical",
    "pinrow8": "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical",
    "pinrow3_p2.5mm": "Connector_JST:JST_XH_B3B-XH-A_1x03_P2.50mm_Vertical",
    "pinrow5_p2.5mm": "Connector_JST:JST_XH_B5B-XH-A_1x05_P2.50mm_Vertical",
    # jumpers / test points
    "solderjumper2_bridged12": "Jumper:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm",
    "smtpad_circle_d1.5": "TestPoint:TestPoint_Pad_D1.5mm",
    "testpoint_pad": "TestPoint:TestPoint_Pad_D1.5mm",
}


def _u():
    return str(uuid.uuid4())


# ------------------------------------------------------------------ net names
def canon_net(name, aliases):
    """Emit the CANONICAL KiCad net name from the tscircuit-authored one.

    tscircuit's `net.` selector can't author a name starting with a digit, so a
    rail is authored with a documented author-prefix `N` (`5V`->`N5V`,
    `3V3`->`N3V3`, `12V`->`N12V`). Rule: an alias file wins first; otherwise
    strip a single leading `N` that guards a digit-leading rail. `NRST`/`NC`/
    `NRESET` (N + non-digit) are left untouched."""
    if name is None:
        return None
    if name in aliases:
        return aliases[name]
    if len(name) >= 2 and name[0] == "N" and name[1].isdigit():
        return name[1:]
    return name


def load_aliases(path):
    """Optional per-board `03_tscircuit/net_aliases.txt`: one `TSNAME CANONICAL`
    per line (`=` or `->` also accepted); `#` starts a comment. For rails the
    default convention can't reach."""
    al = {}
    if not path or not os.path.isfile(path):
        return al
    for line in open(path):
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        parts = re.split(r"\s*(?:=|->|\s)\s*", line, maxsplit=1)
        if len(parts) == 2 and parts[0] and parts[1]:
            al[parts[0].strip()] = parts[1].strip()
    return al


# ------------------------------------------------------------------ FPID lookup
def load_part_overrides(parts_dir):
    """Per-board FPID override seeded from `02_parts/*/part.yaml` — the project's
    source of truth for the real KiCad footprint per part. Keyed by every handle
    circuit.json might carry (LCSC/JLC code, MPN, part folder name) -> FPID.
    YAML-free line parse so the converter needs no external deps."""
    ov = {}
    if not parts_dir or not os.path.isdir(parts_dir):
        return ov
    for name in sorted(os.listdir(parts_dir)):
        p = os.path.join(parts_dir, name, "part.yaml")
        if not os.path.isfile(p):
            continue
        txt = open(p).read()
        # a KiCad FPID is a single whitespace-free `lib:name` token, so grab the
        # first token after `footprint:` — this cleanly drops any trailing YAML
        # `# inline comment` (which may itself contain quotes and would otherwise
        # corrupt the emitted s-expr).
        m = re.search(r"^footprint:\s*(\S+)", txt, re.M)
        if not m:
            continue
        fp = m.group(1).strip("\"'")
        keys = {name}
        mm = re.search(r"^mpn:\s*(.+?)\s*(?:#.*)?$", txt, re.M)
        if mm:
            keys.add(mm.group(1).strip().strip("\"'"))
        for code in re.findall(r"(?:lcsc|jlc|jlcpcb):\s*([A-Za-z0-9]+)", txt):
            keys.add(code)
        for k in keys:
            ov.setdefault(k, fp)
    return ov


def load_part_ties(parts_dir):
    """Per-board EXTRA-PIN map seeded from `02_parts/*/part.yaml` `pins:` blocks.

    A pin annotated `tie: <net>` is one that tscircuit's footprint token CANNOT
    express — the classic case is an exposed thermal pad (EP / pad 9 of a
    WSON-8-1EP): the tsx authors the part on a pad-only token (`dfn8`), so the EP
    never reaches circuit.json, the schematic symbol omits it, and the board pad
    ends up floating — invisible to DRC/parity. When such a pad is absent from
    circuit.json, `load_model` EMITS an additional symbol pin for it on `<net>`
    so the exported netlist carries it and schematic-parity stays 0.

    Returns {handle -> [(pad, func, net), ...]}, keyed by every handle
    circuit.json might carry (LCSC/JLC code, MPN, part folder name) — mirroring
    `load_part_overrides`. YAML-free line parse (no external deps), SCOPED to the
    top-level `pins:` block so a `tie:`-lookalike elsewhere can never trigger it.
    The part.yaml pin KEY is the KiCad pad name (e.g. `9` for the EP)."""
    ties = {}
    if not parts_dir or not os.path.isdir(parts_dir):
        return ties
    for name in sorted(os.listdir(parts_dir)):
        p = os.path.join(parts_dir, name, "part.yaml")
        if not os.path.isfile(p):
            continue
        txt = open(p).read()
        # isolate the top-level `pins:` block (up to the next unindented key)
        pm = re.search(r'^pins:[^\n]*\n(.*?)(?=^\S|\Z)', txt, re.M | re.S)
        if not pm:
            continue
        entries = []
        for line in pm.group(1).splitlines():
            # a pin is `  <pad>: {name: X, tie: NET, ...}` (inline flow map);
            # a bare `  8: GND` has no dict and thus no tie.
            m = re.match(r'\s*([A-Za-z0-9_]+):\s*\{(.*)\}\s*(?:#.*)?$', line)
            if not m:
                continue
            pad, bodytxt = m.group(1), m.group(2)
            tm = re.search(r'\btie:\s*([A-Za-z0-9_]+)', bodytxt)
            if not tm:
                continue
            fn = re.search(r'\bname:\s*([A-Za-z0-9_]+)', bodytxt)
            entries.append((pad, fn.group(1) if fn else pad, tm.group(1)))
        if not entries:
            continue
        keys = {name}
        mm = re.search(r'^mpn:\s*(.+?)\s*(?:#.*)?$', txt, re.M)
        if mm:
            keys.add(mm.group(1).strip().strip("\"'"))
        for code in re.findall(r'(?:lcsc|jlc|jlcpcb):\s*([A-Za-z0-9]+)', txt):
            keys.add(code)
        for k in keys:
            ties.setdefault(k, entries)
    return ties


def resolve_fpid(token, codes, overrides):
    """FPID for one component: the per-board 02_parts override (specialty parts)
    wins over the baked-in commodity token map; empty string if neither knows it
    (a blank Footprint the backend's hard-error will then surface, by design)."""
    for c in codes:
        if c and c in overrides:
            return overrides[c]
    if token and token in COMMODITY_FP:
        return COMMODITY_FP[token]
    return ""


def _discover_up(start, names, is_dir):
    d = os.path.dirname(os.path.abspath(start))
    for _ in range(5):
        for nm in names:
            cand = os.path.join(d, nm)
            if (os.path.isdir(cand) if is_dir else os.path.isfile(cand)):
                return cand
        nd = os.path.dirname(d)
        if nd == d:
            break
        d = nd
    return None


def snap(v):
    return round(v / GRID) * GRID


def natkey(s):
    return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', str(s))]


# ------------------------------------------------------------------ model
def load_model(path, aliases=None, overrides=None, return_ports=False, ties=None):
    """Parse circuit.json -> per-component ordered (padname, portname, net) plus
    metadata. Returns (components, flag_host) where components is a list of dicts
    in refdes order. flag_host is (refdes, padname) of the GND pin to carry the
    single PWR_FLAG, or None.

    With return_ports=True, ALSO returns a third value `portinfo`: a dict
    source_port_id -> {"refdes", "pad", "net", "func", "cid"} exposing the exact
    per-source_port resolution (KiCad pad name, canonical net, function label)
    that the LAYOUT-preserving mode (convert_layout) needs to wire tscircuit's
    schematic geometry to KiCad pins WITHOUT re-deriving connectivity — so the
    wired sheet inherits v1's node-for-node parity by construction.

    Net names are CANONICALIZED (`canon_net`) and each component carries a
    resolved KiCad FPID (`fpid`) so the emitted sheet is backend-ready with no
    downstream adapter."""
    aliases = aliases or {}
    overrides = overrides or {}
    ties = ties or {}
    d = json.load(open(path, encoding="utf-8-sig"))
    comps = {e['source_component_id']: e for e in d
             if e.get('type') == 'source_component'}
    ports = [e for e in d if e.get('type') == 'source_port']
    port_by_id = {p['source_port_id']: p for p in ports}

    # source_component_id -> tscircuit footprinter token (from cad_component)
    tok_by_comp = {e['source_component_id']: e.get('footprinter_string')
                   for e in d if e.get('type') == 'cad_component'}

    # net-key -> net name (first wins; ids are stable within a build)
    key2net = {}
    for e in d:
        if e.get('type') == 'source_net':
            key2net.setdefault(e['subcircuit_connectivity_map_key'], e['name'])

    # base net per port via its connectivity key, canonicalized to KiCad names
    portnet = {p['source_port_id']:
               canon_net(key2net.get(p.get('subcircuit_connectivity_map_key')), aliases)
               for p in ports}
    # propagate through internal connections (split shields / thermal pads)
    for c in comps.values():
        for grp in c.get('internally_connected_source_port_ids', []):
            found = next((portnet.get(sid) for sid in grp if portnet.get(sid)), None)
            if found:
                for sid in grp:
                    if portnet.get(sid) is None:
                        portnet[sid] = found

    # source_port -> pcb pad port_hints (for the true KiCad pad name)
    pcbport_by_src = {e['source_port_id']: e for e in d if e.get('type') == 'pcb_port'}
    padhints = {}
    for e in d:
        if e.get('type') in ('pcb_smtpad', 'pcb_plated_hole') and e.get('pcb_port_id'):
            padhints[e['pcb_port_id']] = e.get('port_hints') or []

    def pad_name(p):
        pp = pcbport_by_src.get(p['source_port_id'])
        ph = padhints.get(pp['pcb_port_id']) if pp else None
        for h in (ph or []):
            if h and not str(h).startswith('unnamed_'):
                return str(h)
        return str(p['pin_number'])

    # group ports per component, collapse duplicate pad names to one pin
    ports_by_comp = {}
    for p in ports:
        ports_by_comp.setdefault(p['source_component_id'], []).append(p)

    portinfo = {}
    components = []
    for cid, c in comps.items():
        plist = ports_by_comp.get(cid, [])
        if not plist:
            continue  # non-electrical (e.g. a mounting-hole <chip> with no pads)
        refdes = c['name']
        pins = {}  # padname -> {"port": portname, "net": net}
        for p in plist:
            pad = pad_name(p)
            net = portnet[p['source_port_id']]
            portinfo[p['source_port_id']] = {
                "refdes": refdes, "pad": pad, "net": net,
                "func": p.get('name') or pad, "cid": cid,
                "pin_number": p.get('pin_number')}
            if pad not in pins:
                pins[pad] = {"port": p.get('name') or pad, "net": net}
            elif pins[pad]["net"] is None and net is not None:
                pins[pad]["net"] = net  # a connected duplicate wins over an NC one
        ordered = sorted(pins.items(), key=lambda kv: natkey(kv[0]))
        is_tp = c.get('ftype') == 'simple_test_point' or refdes.startswith('TP')
        codes = [code for v in (c.get('supplier_part_numbers') or {}).values()
                 for code in (v or [])]
        pin_tuples = [(pad, v["port"], v["net"]) for pad, v in ordered]
        # EXTRA PINS from 02_parts `tie:` annotations. A tie pad tscircuit's
        # footprint can't express (an exposed thermal pad) is ABSENT from
        # circuit.json, so emit a symbol pin for it here on its canonical net —
        # the ONLY way parity/DRC ever see it. Additive & idempotent: a tie pad
        # that DID reach circuit.json (already in `pins`) is left untouched, so
        # the in-circuit thermal-pad collapse path above is never disturbed.
        tie_entries = next((ties[k] for k in codes + [refdes] if k in ties), None)
        if tie_entries:
            have = set(pins)
            for tpad, tfunc, tnet in tie_entries:
                if tpad in have:
                    continue
                pin_tuples.append((tpad, tfunc, canon_net(tnet, aliases)))
                have.add(tpad)
        components.append({
            "refdes": refdes,
            # a test point's tscircuit default Value (`simple_test_point`, 18ch)
            # renders as footprint silk clipped by the board edge -> concise "TP".
            "value": "TP" if is_tp else comp_value(c),
            "is_tp": is_tp,
            "fpid": resolve_fpid(tok_by_comp.get(cid), codes, overrides),
            "pins": pin_tuples,
        })
    components.sort(key=lambda c: natkey(c["refdes"]))

    # single PWR_FLAG host: first GND pin in refdes order
    flag_host = None
    for c in components:
        for pad, _pn, net in c["pins"]:
            if net == "GND":
                flag_host = (c["refdes"], pad)
                break
        if flag_host:
            break
    if return_ports:
        return components, flag_host, portinfo
    return components, flag_host


def comp_value(c):
    if c.get('ftype') == 'simple_resistor' and c.get('display_resistance'):
        return c['display_resistance']
    if c.get('ftype') == 'simple_capacitor' and c.get('display_capacitance'):
        return c['display_capacitance']
    mpn = comp_mpn(c)
    return mpn or c.get('ftype') or c['name']


def comp_mpn(c):
    sp = c.get('supplier_part_numbers') or {}
    for vendor in ('jlcpcb',):
        if sp.get(vendor):
            return sp[vendor][0]
    for v in sp.values():
        if v:
            return v[0]
    return ""


# ------------------------------------------------------------------ layout
def build_symbol(comp):
    """Synthesize a unique N-pin box lib_symbol for one component, split
    half-left / half-right in pad order. Returns (symname, text, pinmap, w, h)."""
    refdes = comp["refdes"]
    symname = "SYM_" + re.sub(r'[^A-Za-z0-9_]', '_', refdes)
    pads = comp["pins"]
    n = len(pads)
    nL = (n + 1) // 2
    pin_specs = []
    for i, (pad, portname, _net) in enumerate(pads):
        side = "L" if i < nL else "R"
        slot = i if side == "L" else i - nL
        # KiCad pin NAME shows the source-port function; NUMBER is the pad name
        label = re.sub(r'[\s"()]+', '_', str(portname)) or pad
        pin_specs.append((str(pad), label, side, slot))
    nR = n - nL
    rows = max(nL, nR, 1)
    h = 2.54 * (rows + 1)
    longest = max([len(str(p)) for p, _l, _s, _sl in pin_specs] +
                  [len(comp["value"]), len(refdes)] + [4])
    # w MUST be an even multiple of the 1.27 grid so w/2 (and thus every pin-tip
    # x = cx +/- (w/2 + 2.54)) is exact to 2 decimals AND on-grid. Otherwise
    # KiCad rounds cx and the pin's local x independently and the pin tip lands
    # ~0.01mm off its global label -> pin_not_connected + label_dangling ERRORS.
    half_units = max(5, math.ceil(longest * 1.6 / 2.54))
    w = 2 * half_units * GRID
    text, pinmap = sw.lib_symbol(symname, w, h, pin_specs, ref=refdes[0], lib=LIB)
    return symname, text, pinmap, w, h


def layout(components):
    """Assign each component a center (cx, cy) on a collision-free grid packed
    into rows. Since ALL connectivity is by global-label NAME (never geometry),
    spacing only needs to keep pin TIPS from coinciding; we budget full label
    envelopes so nothing overlaps and rendering stays legible."""
    ROW_BUDGET = 900.0   # mm; wrap a row past this content width
    GAP = 12.0
    ROW_GAP = 14.0
    MARGIN = 20.0
    placed = []
    x = MARGIN
    y = MARGIN
    row_h = 0.0
    for comp in components:
        symname, text, pinmap, w, h = build_symbol(comp)
        # label reach on each side
        maxlab = 0.0
        for pad, _pn, net in comp["pins"]:
            if net:
                maxlab = max(maxlab, (len(net) + 2) * CH_W)
        half = w / 2 + PIN_LEN + maxlab + 2.0
        full_w = 2 * half
        full_h = h + 8.0  # ref/value text above & below
        if x > MARGIN and x + full_w > MARGIN + ROW_BUDGET:
            x = MARGIN
            y += row_h + ROW_GAP
            row_h = 0.0
        cx = snap(x + half)
        cy = snap(y + full_h / 2)
        placed.append({**comp, "sym": symname, "symtext": text,
                       "pinmap": pinmap, "w": w, "h": h, "cx": cx, "cy": cy})
        x += full_w + GAP
        row_h = max(row_h, full_h)
    # paper size to content
    right = max((p["cx"] + p["w"] / 2 + PIN_LEN +
                 max([(len(net) + 2) * CH_W for _pd, _pn, net in p["pins"] if net] + [0])
                 for p in placed), default=200) + MARGIN
    bottom = y + row_h + MARGIN
    return placed, right, bottom


# ------------------------------------------------------------------ emit
_PWR_SYMS = {}


def power_syms():
    """The GND / PWR_FLAG lib_symbol texts this module emits — one home, so
    `glyph_box` measures the SAME bytes the sheet carries."""
    if not _PWR_SYMS:
        _PWR_SYMS.update(sw.power_lib_symbols(LIB))
    return _PWR_SYMS


def emit_power(project, root_uuid, sym, ref, value, x, y, ang):
    return (
        f'  (symbol (lib_id "{LIB}:{sym}") (at {x:.3f} {y:.3f} {ang}) (unit 1)'
        f' (in_bom no) (on_board yes) (dnp no) (uuid "{_u()}")\n'
        f'    (property "Reference" "{ref}" (at {x:.3f} {y:.3f} 0) (effects (font (size 1.27 1.27)) hide))\n'
        f'    (property "Value" "{value}" (at {x:.3f} {y:.3f} 0) (effects (font (size 1.27 1.27)) hide))\n'
        f'    (property "Footprint" "" (at {x:.3f} {y:.3f} 0) (effects (font (size 1.27 1.27)) hide))\n'
        f'    (pin "1" (uuid "{_u()}"))\n'
        f'    (instances (project "{project}" (path "/{root_uuid}"'
        f' (reference "{ref}") (unit 1))))\n  )')


def emit_component(comp, project, root_uuid, flag_host, pwr_counter):
    cx, cy, w, h = comp["cx"], comp["cy"], comp["w"], comp["h"]
    pinmap = comp["pinmap"]
    # grid mode splits every symbol's pins half-LEFT / half-RIGHT, so its ground
    # triangles hang sideways from tips that are already PIN_LEN outside the
    # body and `prop_rows` skips all of them — this call is a measured no-op
    # here (both grid-mode boards emit byte-identical property rows) and exists
    # so the rule is a property of the MODULE rather than of one emitter.
    gpads, gtips, gsides, gnets = [], {}, {}, {}
    for pad, _pn, net in comp["pins"]:
        side, pmy = pinmap[str(pad)]
        gpads.append(str(pad))
        gtips[str(pad)] = (cx + (-(w / 2 + PIN_LEN) if side == "L"
                                 else (w / 2 + PIN_LEN)), cy + (-pmy))
        gsides[str(pad)] = "left" if side == "L" else "right"
        gnets[str(pad)] = net
    ry, vy = prop_rows(cx, cy, w, h,
                       attached_glyph_boxes(
                           gpads, gtips, gsides, gnets,
                           str(flag_host[1]) if flag_host
                           and flag_host[0] == comp["refdes"] else None),
                       gap_above=1.6, gap_below=1.8)
    # TP symbols track the KiCad TestPoint footprint's exclude-from-BOM default
    # (footprint_symbol_mismatch on the BOM attr otherwise). No MPN field is
    # emitted at all: KiCad library footprints carry none, so a symbol MPN
    # field trips footprint_symbol_field_mismatch — sourcing lives in 02_parts.
    in_bom = "no" if comp["is_tp"] else "yes"
    body = [
        f'  (symbol (lib_id "{LIB}:{comp["sym"]}") (at {cx:.2f} {cy:.2f} 0) (unit 1)'
        f' (in_bom {in_bom}) (on_board yes) (dnp no) (uuid "{_u()}")\n'
        f'    (property "Reference" "{comp["refdes"]}" (at {cx:.2f} {ry:.2f} 0)'
        f' (effects (font (size 1.27 1.27))))\n'
        f'    (property "Value" "{comp["value"]}" (at {cx:.2f} {vy:.2f} 0)'
        f' (effects (font (size 1.27 1.27))))\n'
        f'    (property "Footprint" "{comp["fpid"]}" (at {cx:.2f} {cy:.2f} 0) (effects (font (size 1.27 1.27)) hide))\n'
        + "\n".join(f'    (pin "{pad}" (uuid "{_u()}"))' for pad, _pn, _net in comp["pins"])
        + f'\n    (instances (project "{project}" (path "/{root_uuid}"'
        f' (reference "{comp["refdes"]}") (unit 1))))\n  )'
    ]
    labels = []
    for pad, _pn, net in comp["pins"]:
        side, pmy = pinmap[str(pad)]
        tip = -(w / 2 + PIN_LEN) if side == "L" else (w / 2 + PIN_LEN)
        ex, ey = cx + tip, cy + (-pmy)
        if net is None:
            body.append(f'  (no_connect (at {ex:.2f} {ey:.2f}) (uuid "{_u()}"))')
            continue
        if net == "GND":
            pwr_counter[0] += 1
            ang = 270 if side == "L" else 90
            body.append(emit_power(project, root_uuid, "GND",
                                   f'#PWR{pwr_counter[0]:02d}', "GND", ex, ey, ang))
            if flag_host == (comp["refdes"], pad):
                body.append(emit_power(project, root_uuid, "PWR_FLAG",
                                       "#FLG01", "PWR_FLAG", ex, ey, 0))
            continue
        ang, just = (180, "right") if side == "L" else (0, "left")
        labels.append(
            f'  (global_label "{net}" (shape passive) (at {ex:.2f} {ey:.2f} {ang})'
            f' (fields_autoplaced) (effects (font (size 1.27 1.27)) (justify {just}))'
            f' (uuid "{_u()}"))')
    return body, labels


def convert(circuit_json, project, title, rev, date, aliases=None, overrides=None,
            ties=None):
    components, flag_host = load_model(circuit_json, aliases, overrides, ties=ties)
    placed, pw, ph = layout(components)
    root_uuid = _u()

    # unique lib_symbol per component + the two power symbols
    lib_syms = dict(sw.power_lib_symbols(LIB))
    for comp in placed:
        lib_syms[comp["sym"]] = comp["symtext"]

    body, labels = [], []
    pwr_counter = [0]
    for comp in placed:
        b, l = emit_component(comp, project, root_uuid, flag_host, pwr_counter)
        body.extend(b)
        labels.extend(l)

    sch = [
        '(kicad_sch (version 20230121) (generator circuit_json_to_kicad_sch)',
        f'  (uuid "{root_uuid}")',
        f'  (paper "User" {pw:.2f} {ph:.2f})',
        f'  (title_block (title "{title}") (date "{date}") (rev "{rev}")',
        '  )',
        '  (lib_symbols',
    ]
    sch.extend(lib_syms.values())
    sch.append('  )')
    sch.extend(labels)
    sch.extend(body)
    sch.append('  (sheet_instances (path "/" (page "1")))')
    sch.append(')')
    content = "\n".join(sch)
    assert content.count("(") == content.count(")"), \
        (content.count("("), content.count(")"))
    return content, components


# ==================================================================== LAYOUT v2
# LAYOUT-PRESERVING mode (ADR-0002 Phase A). Instead of v1's one-label-per-pin
# grid, consume tscircuit's OWN schematic layout that circuit.json already
# carries — schematic_component (center/size/rotation), schematic_port (pin
# geometry), schematic_trace (drawn wire routes) and schematic_net_label (the
# rail/global-net labels tscircuit chose) — and emit a WIRED, readable native
# sheet: KiCad `(wire ...)` where tscircuit drew a trace, a KiCad label where
# tscircuit used a net label, ground power symbols on GND. Connectivity is
# still keyed to v1's authoritative per-pin canonical-net model (load_model),
# so the drawn wires never change the netlist — a self-healing safety pass adds
# a name label to any pin a wire didn't reach, and RAISES LayoutFallback on a
# genuine cross-net short so the caller falls back to v1's grid for that board
# (never worse than v1). Result: S6 "label-blob" retired, parity preserved.

L_S = 12.7            # tscircuit schematic-unit -> KiCad mm (0.2u pin pitch -> 2.54mm)
L_G = 0.635           # snap grid: coords are ~0.05u multiples -> land near 0.635mm
L_M = 25.4           # sheet margin (mm)
L_PORT_TOL2 = 0.06 ** 2   # nearest-port match radius^2 in tscircuit units

# ----------------------------------------------------- direction vocabulary
# ONE home for "a side name -> what KiCad actually draws". Throughout this
# module a `side` is THE DIRECTION A THING REACHES, away from the body it
# belongs to: a pin on the symbol's left reaches left, and the label on that
# pin must reach left too (v1's grid emitter has always meant this — see
# `emit_component`, where side "L" gets (180, "right")).
#
# MEASURED 2026-07-31 against kicad-cli 10.0.4, from RENDERED SVG INK rather
# than from derivation (canon M1 — the emitter must not grade its own angles):
#   a global_label's ANGLE selects only the AXIS. KiCad normalises the
#   180-degree component away, and `justify` ALONE selects the sense:
#       (0|180, left)  -> plate reaches RIGHT     (90|270, left)  -> UP
#       (0|180, right) -> plate reaches LEFT      (90|270, right) -> DOWN
#   an `elt:GND` instance's body points DOWN at 0, RIGHT at 90, UP at 180,
#   LEFT at 270.
#
# Two rows below were WRONG until that measurement and both shipped:
#   * LABEL_ANG_JUST['bottom'] was (270, 'left'), which renders UP, not down.
#   * GND_ANG['top']/['bottom'] were 0/180, i.e. each pointed the ground symbol
#     back INTO the body it hangs off.
LABEL_ANG_JUST = {'left': (180, 'right'), 'right': (0, 'left'),
                  'top': (90, 'left'), 'bottom': (270, 'right')}
GND_ANG = {'left': 270, 'right': 90, 'top': 180, 'bottom': 0}

#: the same four side names as UNIT REACH VECTORS on a y-DOWN KiCad sheet.
#: This is `LABEL_ANG_JUST` read as geometry, and `tests/t1_converter.py
#: t_kicad_direction_table_is_measured` closes the loop every run: the
#: (angle, justify) each side maps to is measured from rendered ink and must
#: reach exactly this way.
SIDE_REACH = {'left': (-1, 0), 'right': (1, 0), 'top': (0, -1), 'bottom': (0, 1)}
_PERP_OF = {'left': (0, -1), 'right': (0, 1), 'top': (1, 0), 'bottom': (-1, 0)}

# tscircuit's `anchor_side` names the EDGE OF THE LABEL PLATE that the anchor
# sits on — the OPPOSITE of the direction the plate reaches. See
# `label_plate_side`.
_ANCHOR_OPPOSITE = {'left': 'right', 'right': 'left',
                    'top': 'bottom', 'bottom': 'top'}

#: gap from the nearest thing already drawn on that side of a symbol to a
#: property text's anchor.
PROP_GAP = 2.2

# ------------------------------------------------ MEASURED text geometry
# Everything below is MEASURED from `kicad-cli sch export svg` INK on probe
# sheets KiCad renders itself (kicad-cli 10.0.4, 2026-07-31), never derived and
# never copied from another module — canon M1, and the brief's standing rule
# that two geometry constants in this repo were recently found wrong in
# OPPOSITE directions. `tests/t1_converter.py t_text_geometry_is_measured`
# re-derives the whole of it on every run.
#
# WHY IT COULD NOT BE INHERITED. The converter's own shipped plate model is
# `(len + 2) * CH_W` with `CH_W = 1.05`, i.e. every character the same width.
# KiCad's stroke font is PROPORTIONAL: measured over 95 characters the advance
# is an exact k/21 of the font size with k from 8 (`` ` ``) to 28 (`m`), a 3.5x
# spread. The flat model is 0.77 mm too WIDE for `IIII` and 6.48 mm too NARROW
# for a 20-character name of capitals — and too narrow is the dangerous
# direction, because a de-collision search built on it would place a plate the
# search calls clear and KiCad draws straight through its neighbour.
#
#: plate extent ALONG the reach = PLATE_BASE + the advance of every character.
#: MEASURED: 1.3341 mm with ZERO spread over all 95 characters (the arrow point
#: plus both margins), at the 1.27 mm font size this module always emits.
PLATE_BASE = 1.3341
#: plate extent ACROSS the reach. MEASURED: 2.5408 mm with ZERO spread over 56
#: plates (7 name lengths x 8 (angle, justify) combinations).
PLATE_CROSS = 2.5408
#: KiCad newstroke advance per character, in TWENTY-FIRSTS of the font size —
#: the font's em is 21 units, so every one of the 95 measured advances is an
#: exact integer and the table is lossless. An unmeasured character takes the
#: WIDEST measured advance, so a name this table has never seen can only make
#: the placer more cautious, never less (canon M-COVER in a geometry model).
ADV21 = {}
for _k, _cs in {8: "`", 10: "!',.:;Iij", 11: "l", 12: "^ft", 13: "r",
                14: "()[\\]{}", 15: "~", 16: " \"*JT_vy", 17: "Lksxz",
                18: "?AFVYce", 19: "Eabdghnopqu", 20: "$0123456789SXZ|",
                21: "#BCDGKPR", 22: "/HNOQUw", 24: "%MW", 26: "&+-<=>",
                27: "@", 28: "m"}.items():
    for _c in _cs:
        ADV21[_c] = _k
ADV21_MAX = max(ADV21.values())
#: property (Reference/Value) text ink extent ABOVE and BELOW its anchor, as a
#: fraction of the font size. MEASURED 0.5441 / 0.5520 (the lower figure is the
#: descender case, `C_SW2`); rounded OUTWARD so the model never under-reaches.
PROP_UP, PROP_DN = 0.545, 0.553
#: a `no_connect` marker is an X of this HALF-extent. MEASURED 0.6096 mm,
#: identical at all three probe sites.
NC_HALF = 0.6096
#: font size every label and property this module emits is drawn at.
FONT = 1.27


def text_span(s, size=FONT):
    """Ink width of a stroke-font run, mm. Sum of the per-character advances —
    a strict UPPER bound on the rendered ink, because the final character's
    trailing side bearing is advanced over but never drawn (MEASURED: 10 `W`s
    advance 14.514 mm and ink 14.151 mm)."""
    return sum(ADV21.get(c, ADV21_MAX) for c in s) * size / 21.0


def plate_span(name, size=FONT):
    """Extent of a global_label's plate ALONG its reach, mm."""
    return PLATE_BASE * size / FONT + text_span(name, size)


def plate_box(name, x, y, side, size=FONT):
    """The rectangle a global_label's plate occupies, from its ANCHOR, given
    the DIRECTION IT REACHES (this module's side vocabulary)."""
    ux, uy = SIDE_REACH[side]
    reach = plate_span(name, size)
    half = PLATE_CROSS * size / FONT / 2.0
    if ux:
        return (min(x, x + ux * reach), y - half,
                max(x, x + ux * reach), y + half)
    return (x - half, min(y, y + uy * reach),
            x + half, max(y, y + uy * reach))


def prop_box(txt, x, y, size=FONT, just=None):
    """The rectangle a Reference/Value text occupies. A property with no
    `justify` is CENTRED on its anchor (MEASURED — unlike a global_label,
    whose absent justify renders as `left`)."""
    w = text_span(txt, size)
    up, dn = PROP_UP * size, PROP_DN * size
    if just == "left":
        return (x, y - up, x + w, y + dn)
    if just == "right":
        return (x - w, y - up, x, y + dn)
    return (x - w / 2, y - up, x + w / 2, y + dn)


def sym_xf(lx, ly, ang):
    """Symbol-LOCAL (y-up) -> sheet OFFSET from the instance origin (y-down):
    rotate CCW by `ang` in symbol space, then negate y for the sheet.

    Re-measured from rendered ink on every test run with an ASYMMETRIC probe
    rectangle, so a wrong handedness cannot pass — `tests/t1_converter.py
    t_glyph_geometry_is_measured` (canon M1: the emitter must not
    grade its own transform)."""
    if ang == 0:
        return (lx, -ly)
    if ang == 90:
        return (-ly, -lx)
    if ang == 180:
        return (-lx, ly)
    if ang == 270:
        return (ly, lx)
    raise ValueError(f"unmodelled symbol rotation {ang}")


_RE_XY_PT = re.compile(r"\(xy ([-\d.]+) ([-\d.]+)\)")


def glyph_box(symtext, x, y, ang):
    """Sheet-space bbox of a power symbol's DRAWN glyph, placed at (x, y, ang).

    MEASURED out of the lib_symbol text this module itself emits (schwriter2's
    `power_lib_symbols`) rather than copied as a constant, so a redrawn ground
    triangle moves this with it. Only `(xy ...)` graphic points are read; the
    hidden Reference/Value anchors and the zero-length pin draw nothing."""
    pts = [(float(a), float(b)) for a, b in _RE_XY_PT.findall(symtext)]
    if not pts:
        raise ValueError("power lib_symbol draws no graphics")
    off = [sym_xf(px, py, ang) for px, py in pts]
    xs = [x + p[0] for p in off]
    ys = [y + p[1] for p in off]
    return (min(xs), min(ys), max(xs), max(ys))


def prop_rows(ix, iy, w, h, glyph_boxes, gap_above=PROP_GAP, gap_below=None):
    """(reference_y, value_y) for a symbol instance — the ONE home for where a
    property text is anchored, above and below the body.

    THE DEFECT THIS REPLACES (MEASURED 2026-07-31, fleet-wide). The rows were
    `iy -/+ h/2 +/- 2.2` and nothing else: a blind offset from the body edge
    that took no account of what is ALREADY drawn on that side of the symbol.
    A pin whose net is GND carries an `elt:GND` hanging off its TIP in the
    direction that pin REACHES (GND_ANG), so on a VERTICALLY placed 2-pin
    passive the bottom pin's ground triangle occupies exactly the strip the
    Value is written into — the triangle spans 2.54 mm below a tip that sits at
    the body edge, and the Value was anchored 2.2 mm below that same edge.
    Measured on pluto-rx2-8way-v2: R_PD1's "10kΩ" run spans x 114.122-118.288 /
    y 95.507-96.853 and #PWR52's lower vertex sits at (116.205, 96.52), inside
    it. 160 of the fleet's 341 S-OCCL findings were this one class — 151 of them
    exactly this 2-pin shape, 9 an IC with a bottom-side GND pin.

    A glyph is only allowed to displace a property when it can actually reach
    it: the property is CENTRED on `ix`, so a glyph whose x-range misses the
    body entirely is skipped. That is what keeps the HORIZONTAL case a strict
    no-op — a left/right pin's triangle hangs sideways from a tip already
    outside the body, and 166 grounded horizontal passives in this fleet do not
    move by so much as a micron (measured)."""
    top = iy - h / 2
    bot = iy + h / 2
    for (bx0, by0, bx1, by1) in glyph_boxes:
        if bx1 <= ix - w / 2 or bx0 >= ix + w / 2:
            continue                       # not under the centred property
        top = min(top, by0)
        bot = max(bot, by1)
    return top - gap_above, bot + (gap_above if gap_below is None else gap_below)


def label_plate_side(nlabel, pin_reach=None):
    """Which way a tscircuit `schematic_net_label`'s PLATE reaches, named in
    this module's side vocabulary (see LABEL_ANG_JUST). `pin_reach` is the
    reach of the pin the label sits on, if any — used only when the label's
    own geometry cannot decide.

    DERIVED FROM GEOMETRY, not from the enum. `center` is the plate's centre
    and `anchor_position` is where it attaches, so `center - anchor` IS the
    direction tscircuit drew it — true at every rotation, and independent of
    what any field is called.

    THE DEFECT THIS REPLACES (fleet-wide, every board, 2026-07-31). The caller
    passed `anchor_side` straight into LABEL_ANG_JUST. `anchor_side` names the
    label EDGE the anchor sits on, which is the REVERSE of the reach the table
    expects, so the plate fired back across the body it hangs off. MEASURED
    over all 7 live boards: 1504 of 1504 labels have `anchor_side` exactly
    opposite `center - anchor_position`, in all four orientations, 0 missing
    `center`, 0 degenerate. Consequence on a HORIZONTALLY placed 2-pin part:
    both plates fire INWARD and a 7.62 mm pin span cannot hold two
    (len+2)*1.05 mm plates -- 15.75 mm for `RX1_TAP_MID` -- at ANY placement on
    ANY board, so it was never a placement problem. pluto-rx2-8way-v2's shipped
    `schematic.pdf` composited `N3V3_MOD` (U_MCU pin 21) onto U_SW's RF2 row:
    the human-readable deliverable said the 3V3 rail was wired to an RF port.

    Only THREE of the four orientations rendered wrong, and the fourth is the
    interesting one: `anchor_side: bottom` (true reach UP) mapped to
    (270, 'left'), which KiCad renders UP -- correct by CANCELLATION between
    this defect and the broken LABEL_ANG_JUST['bottom'] row above. That is why
    the two fixes have to land together: repairing either one alone breaks the
    ~155 fleet labels the pair of them was accidentally getting right.
    """
    a = nlabel.get('anchor_position') or {}
    c = nlabel.get('center') or {}
    try:
        dx = float(c['x']) - float(a['x'])
        dy = float(c['y']) - float(a['y'])
    except (KeyError, TypeError, ValueError):
        dx = dy = 0.0
    if max(abs(dx), abs(dy)) > 1e-9:
        if abs(dx) >= abs(dy):
            return 'right' if dx > 0 else 'left'
        # tscircuit y is UP and T() flips it, so a plate ABOVE the anchor in
        # tscircuit is above it on the KiCad sheet too -> side 'top'.
        return 'top' if dy > 0 else 'bottom'
    # Degenerate/absent geometry (`center` == `anchor_position`, or no
    # `center` at all). Never reached on any board in the fleet today
    # (0/1504), but a label with no plate extent must not silently take a
    # default direction. Prefer the PIN the label sits on — a label on a pin
    # reaches the way the pin does, which is the same rule the self-healing
    # safety labels use — and only then invert the enum.
    if pin_reach in LABEL_ANG_JUST:
        return pin_reach
    return _ANCHOR_OPPOSITE.get(nlabel.get('anchor_side'), 'left')


class LayoutFallback(Exception):
    """Raised when tscircuit's schematic geometry can't be imported without a
    cross-net short — the caller falls back to v1's label grid for this board."""


def _rhu(v, g):
    return math.floor(v / g + 0.5) * g


def _side_of(port, cx, cy):
    """left/right/top/bottom for a schematic_port, from its declared side or,
    failing that, from its offset relative to the component center."""
    s = port.get('side_of_component') or port.get('facing_direction')
    if s in ('left', 'right', 'top', 'bottom'):
        return s
    dx = port['center']['x'] - cx
    dy = port['center']['y'] - cy
    if abs(dx) >= abs(dy):
        return 'left' if dx < 0 else 'right'
    return 'top' if dy > 0 else 'bottom'   # tscircuit y-up: +dy is above


def lib_symbol_geo(name, w, h, pins, ref="U", lib=LIB, hide_numbers=False):
    """A UNIQUE per-refdes box lib_symbol whose pins sit at EXPLICIT local
    positions (so their KiCad tips land on tscircuit's schematic_port centers
    and drawn wires attach). pins: (number, pinname, lx, ly, ang, length).
    hide_numbers: drop pad-number text (conventional for 2-pin passives) to
    keep the wired sheet legible — parity keys on the number, not its glyph."""
    hn = ' (pin_numbers hide)' if hide_numbers else ''
    out = [f'    (symbol "{lib}:{name}"{hn} (in_bom yes) (on_board yes)']
    out.append(f'      (property "Reference" "{ref}" (at 0 {h/2+2.54:.3f} 0) (effects (font (size 1.27 1.27))))')
    out.append(f'      (property "Value" "{name}" (at 0 {-h/2-2.54:.3f} 0) (effects (font (size 1.27 1.27))))')
    out.append(f'      (symbol "{name}_0_1"')
    out.append(f'        (rectangle (start {-w/2:.3f} {-h/2:.3f}) (end {w/2:.3f} {h/2:.3f})'
               f' (stroke (width 0.254) (type default)) (fill (type background)))')
    out.append("      )")
    out.append(f'      (symbol "{name}_1_1"')
    for num, pname, lx, ly, ang, length in pins:
        # blank out uninformative pin names (tscircuit's default `pin1`/`pin2`
        # on passives/connectors) with KiCad's "~" no-name token so the wired
        # sheet stays legible; keep real function names (VSUP, DVDD, ...).
        if re.fullmatch(r'(pin)?\d+', pname or '') or pname == str(num):
            pname = "~"
        out.append(
            f'        (pin passive line (at {lx:.3f} {ly:.3f} {ang}) (length {length:.3f})'
            f' (name "{pname}" (effects (font (size 1.0 1.0))))'
            f' (number "{num}" (effects (font (size 1.0 1.0)))))')
    out.append("      )")
    out.append("    )")
    return "\n".join(out)


class UF:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[ra] = rb


def _on_segment(px, py, x1, y1, x2, y2, eps=1e-4):
    """True if (px,py) lies strictly between the segment endpoints (collinear)."""
    cross = (x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)
    if abs(cross) > eps:
        return False
    dot = (px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)
    L2 = (x2 - x1) ** 2 + (y2 - y1) ** 2
    return L2 > eps and eps < dot < L2 - eps


# ==================================================== label de-collision (S11)
#: search step, mm. 1.27 is half the 2.54 mm pin pitch and two units of this
#: module's own L_G = 0.635 snap grid, so every candidate anchor lands exactly
#: on the grid the wires and pin tips already live on.
DC_STEP = 1.27
#: how far the search may go, in steps: outward ALONG the reach, and sideways
#: ACROSS it. Chosen at SATURATION, not tuned to a number — the bound must sit
#: past the point where it decides anything, which is the only honest place to
#: put one.
#:
#: RE-MEASURED 2026-07-31 WHEN WIRES ENTERED THE OBSTACLE MODEL, because a
#: saturation point is a property of the obstacle set and not of the ladder.
#: The shipped (6, 10) was at saturation against symbol ink alone and is
#: nowhere near it against ink that includes 681 wires. MEASURED over the six
#: layout-mode sheets, S-OCCL after regeneration
#: (crow-mic-pod / crow-recorder / cal-switch / rx2-8way / rx2-8way-v2 /
#: interposer):
#:      (4, 6)    2 sheets do not convert at all
#:      (6, 10)   0 /  9 / 15 / 5 / 0 / 3
#:      (8, 14)   0 /  8 /  9 / 1 / 0 / 3
#:      (10, 20)  0 /  7 /  2 / 1 / 0 / 3
#:      (14, 28)  0 /  7 /  1 / 1 / 0 / 3
#:      (20, 40)  0 /  7 /  1 / 1 / 0 / 3   <- BYTE-IDENTICAL to (14, 28)
#: so (14, 28) is the first bound that decides nothing. pluto-rx2-8way-v2 is
#: byte-identical at EVERY bound in that table, (4, 6) included: its sheet does
#: not depend on this constant at all.
DC_MAX_ALONG, DC_MAX_CROSS = 14, 28
#: two objects are in CONTACT when they overlap by more than this.
#:
#: MEASURED, not inherited and not chosen. Every plate-vs-anything overlap this
#: model finds across the six layout-mode sheets was tabulated: 108 at exactly
#: zero, 205 at exactly 0.0004 or 0.0008 mm, then NOTHING until 0.0677 mm, and
#: the rest above 0.2 mm. The 0.0004/0.0008 cluster is arithmetic, not
#: crowding: PLATE_CROSS is 2.5408 mm and pins sit on a 2.540 mm pitch, so two
#: labels on ADJACENT pins of one symbol overlap by 0.0008 mm and a label
#: against the neighbouring pin LINE by half of that. Every schematic in this
#: fleet already looks like that and always will.
#: So the threshold sits in the empty two-decade gap between the two clusters:
#: 12x above the abutment, 6.8x below the smallest real overlap on the fleet,
#: and 1/25 of the 0.254 mm stroke width — small enough that nothing it
#: forgives could be seen by a human, large enough that the grid's own
#: arithmetic is not mistaken for a defect.
DC_TOUCH = 0.01
#: how close a new wire end may come to a connection point it is not part of.
DC_NET_TOL = 0.01
#: bounded re-derivation rounds (see `place_labels`). Bounded, so an
#: oscillating pair terminates rather than spinning; the loop also stops the
#: moment a round changes nothing.
DC_ROUNDS = 8


class LabelPlacementError(Exception):
    """No legal placement exists for a global_label.

    A HARD ERROR that NAMES the label, never a silent drop and never a fallback
    — canon S11 and the same rule the silkscreen `_place_owned` search has
    carried since a board shipped with no reference designators on it at all.
    Deliberately NOT a `LayoutFallback`: falling back to `--mode grid` would
    answer "this label cannot be placed legibly" with a different sheet, which
    is not an answer.
    """


def _hit_box(a, b, eps=DC_TOUCH):
    return (min(a[2], b[2]) - max(a[0], b[0]) > eps and
            min(a[3], b[3]) - max(a[1], b[1]) > eps)


def _seg_in_box(p, q, box):
    """Length of segment p->q lying inside an axis-aligned box (Liang-Barsky).

    A pin is a LINE, not a rectangle: asking how much of it the text actually
    covers is what makes a plate's own attachment point score exactly zero."""
    x0, y0, x1, y1 = box
    dx, dy = q[0] - p[0], q[1] - p[1]
    t0, t1 = 0.0, 1.0
    for pp, qq in ((-dx, p[0] - x0), (dx, x1 - p[0]),
                   (-dy, p[1] - y0), (dy, y1 - p[1])):
        if abs(pp) < 1e-12:
            if qq < 0:
                return 0.0
        else:
            r = qq / pp
            if pp < 0:
                if r > t1:
                    return 0.0
                t0 = max(t0, r)
            else:
                if r < t0:
                    return 0.0
                t1 = min(t1, r)
    return max(0.0, t1 - t0) * math.hypot(dx, dy)


def _symbol_ink(placed, flag_host, comp_by_ref):
    """Every piece of NON-TEXT ink the symbol instances draw, each tagged with
    the refdes that owns it: bodies, pin lines, ground/flag glyphs, no-connect
    markers. -> ([(box, desc, owner)], [((p, q), desc, owner)]).

    The owner tag exists because S-OCCL exempts a text from its OWN symbol's
    body/pins/glyphs (`towner == oowner` in `sch_occlusion.occlusions`) and the
    property search below has to make exactly that exemption — a Reference
    written across its own symbol's pin is not a finding and must not be
    chased off the sheet by one. A LABEL plate takes no such exemption: its own
    pin is reported, deliberately (`t_attachment_is_not_an_occlusion`).
    """
    boxes, segs = [], []
    for comp in placed:
        ref = comp["refdes"]
        ix, iy = comp["inst"]
        w, h = comp["w"], comp["h"]
        boxes.append(((ix - w / 2, iy - h / 2, ix + w / 2, iy + h / 2),
                      f"body {ref}", ref))
        nets = {p: comp_pin_net(comp_by_ref, ref, p)
                for p in comp["tips"]}
        for num, _pn, lx, ly, pang, plen in comp["pins_geo"]:
            tip = comp["tips"][str(num)]
            # the (at) point IS the tip; the pin runs from there toward the
            # body along `pang` in symbol-LOCAL (y-up) space.
            ex = lx + plen * math.cos(math.radians(pang))
            ey = ly + plen * math.sin(math.radians(pang))
            end = (ix + ex, iy - ey)
            segs.append(((tip, end), f"pin {ref}.{num}", ref))
            net = nets.get(str(num))
            if net is None:
                boxes.append(((tip[0] - NC_HALF, tip[1] - NC_HALF,
                               tip[0] + NC_HALF, tip[1] + NC_HALF),
                              f"no_connect {ref}.{num}", ref))
            elif net == "GND":
                side = comp["sides"][str(num)]
                # the GND triangle is a SEPARATE `#PWRnn` symbol instance on the
                # emitted sheet, so S-OCCL gives it a different owner from the
                # pin it hangs off and a property IS graded against it. Tagged
                # here with a `#` owner that no refdes can equal, so the
                # exemption cannot leak onto it.
                boxes.append((glyph_box(power_syms()["GND"], tip[0], tip[1],
                                        GND_ANG[side]), f"glyph {ref}.{num}",
                              f"#PWR:{ref}.{num}"))
                if flag_host == (ref, str(num)):
                    boxes.append((glyph_box(power_syms()["PWR_FLAG"],
                                            tip[0], tip[1], 0),
                                  f"flag {ref}.{num}", f"#FLG:{ref}.{num}"))
    return boxes, segs


def _prop_boxes(placed, prop_anchors):
    """[(box, desc, owner)] for every Reference/Value row actually drawn."""
    out = []
    for comp in placed:
        ref = comp["refdes"]
        (rx, ry), (vx, vy) = prop_anchors[ref]
        for txt, tx, ty, kind in ((ref, rx, ry, "Reference"),
                                  (comp["value"], vx, vy, "Value")):
            if txt:
                out.append((prop_box(str(txt), tx, ty), f"{kind} {txt}", ref))
    return out


def _obstacles(placed, prop_anchors, flag_host, comp_by_ref):
    """Every non-label piece of ink a label plate must stay off: symbol bodies,
    pin lines, the Reference/Value rows, the ground/flag glyphs, no-connect
    markers. Returns ([(box, desc)], [((p, q), desc)]).

    WIRES ARE NOT HERE. They are ink a plate must stay off just as much as a
    pin line is, but a label is ATTACHED to one — see `place_labels`, which adds
    them per-candidate with the attachment exemption this signature cannot
    express.
    """
    boxes, segs = _symbol_ink(placed, flag_host, comp_by_ref)
    boxes = [(b, d) for b, d, _o in boxes]
    segs = [(s, d) for s, d, _o in segs]
    boxes += [(b, d) for b, d, _o in _prop_boxes(placed, prop_anchors)]
    return boxes, segs


# ------------------------------------------- property rows vs wires (S11-PROP)
#: how far a property row may be displaced, in DC_STEP units: OUTWARD (further
#: from its own body) and SIDEWAYS. Chosen at SATURATION exactly as
#: DC_MAX_ALONG/DC_MAX_CROSS are. MEASURED over the six layout-mode sheets,
#: S-OCCL after regeneration: (4, 4) leaves pluto-rx2-8way at 6 findings, and
#: (6, 6), (8, 8) and (12, 12) give BYTE-IDENTICAL sheets on all six (5 there,
#: and unchanged on the other five). So the bound decides nothing at (6, 6).
DC_PROP_OUT, DC_PROP_CROSS = 6, 6


def _prop_ladder(out_max, cross_max):
    """The property search ladder, FIXED order, cheapest first with (0, 0)
    always first — so a row with nothing on it does not move at all.

    At equal cost the OUTWARD step is preferred, which is the opposite
    preference from `_candidates()` and for the opposite reason. A label is
    read by the pin at the blunt end of its plate, so keeping its reach
    envelope still is what preserves the reading. A property is read by being
    CENTRED OVER THE SYMBOL IT NAMES, so keeping `x` on the body's centre line
    is what preserves that one; the sideways step is the fallback, taken only
    when nothing directly outward is clear.
    """
    out = []
    for cost in range(out_max + cross_max + 1):
        for o in range(out_max + 1):
            for c in range(cross_max + 1):
                if o + c != cost:
                    continue
                for s in ((0,) if c == 0 else (1, -1)):
                    out.append((o, c * s))
    return out


_DC_PROP_LADDER = _prop_ladder(DC_PROP_OUT, DC_PROP_CROSS)


def _box_gap2(box, other):
    """Squared distance between two axis-aligned boxes (0 if they touch)."""
    dx = max(other[0] - box[2], box[0] - other[2], 0.0)
    dy = max(other[1] - box[3], box[1] - other[3], 0.0)
    return dx * dx + dy * dy


def prop_is_nearest(box, ref, bodies):
    """THE TRUTH GUARD on a displaced property row: is `box` still STRICTLY
    nearest to the body of the symbol it names?

    A Reference is read as naming the symbol it sits closest to. Stepping one
    sideways to dodge a wire is a legibility repair; stepping it past the
    midpoint to the next symbol makes the sheet say something FALSE, and a
    prettier sheet that is less true is the one outcome this whole pass exists
    to avoid — the precedent is `ANT2`/`3V3_MOD` compositing into `N3V3_MOD2`.

    Module-level rather than a closure so a test can neutralise it and
    re-measure what it was holding off (`t1_converter.py
    t_prop_move_never_drifts_to_a_neighbour`)."""
    mine = _box_gap2(box, bodies[ref])
    return all(mine < _box_gap2(box, bx) for r, bx in bodies.items() if r != ref)


def place_props(placed, prop_anchors, flag_host, comp_by_ref, segs):
    """Displace the Reference/Value rows that a WIRE (or anything else) is
    drawn through. -> {refdes: ((rx, ry), (vx, vy))}, moved_count.

    WHY A ROW NEEDS THIS AT ALL, and why `prop_rows`' y-only nudge cannot do it.
    `prop_rows` pushes a row past whatever hangs off the body on that side; it
    is a one-dimensional answer, and a wire leaving a pin along the body's own
    centre line is a two-dimensional problem. MEASURED on pluto-rx2-8way-v2's
    `04_kicad`: 9 of its 13 S-OCCL findings are exactly that shape — a
    vertically placed passive whose top pin carries a wire straight up through
    the Reference written above it (`C_BULK` at x 52.070, row y 121.625, wire
    (52.070,107.315)-(52.070,122.555) covering the whole 1.392 mm tall run).
    Stepping the row further out never clears a wire that is 15 mm long; only
    stepping ACROSS it does.

    WHAT THIS REFUSES, and it is the same shape of refusal as `place_labels`.
    A Reference is understood to name the symbol it is centred over, so:

      * a row never crosses its own body — the Reference stays ABOVE the
        instance origin and the Value BELOW it, always;
      * a displaced row must stay STRICTLY NEAREST to its own symbol's body.
        A `C_BULK` that drifts closer to `R_PD3` than to `C_BULK` would be a
        prettier sheet that says something false, which is the one outcome this
        pass exists to avoid. The candidate is rejected, not shipped.

    A row with no legal placement is LEFT WHERE `prop_rows` PUT IT rather than
    raising: unlike a label plate, a property row occluding a wire is a
    legibility defect and not a connectivity one, and S-OCCL is the gate that
    reports it. Deliberately different from `LabelPlacementError`, which guards
    a fact about the NET.
    """
    sym_boxes, sym_segs = _symbol_ink(placed, flag_host, comp_by_ref)
    bodies = {c["refdes"]: (c["inst"][0] - c["w"] / 2, c["inst"][1] - c["h"] / 2,
                            c["inst"][0] + c["w"] / 2, c["inst"][1] + c["h"] / 2)
              for c in placed}
    wires = [(a, b) for a, b, _n in segs]
    # (refdes, kind) -> (text, home anchor, outward unit y)
    items = {}
    for comp in placed:
        ref = comp["refdes"]
        (rx, ry), (vx, vy) = prop_anchors[ref]
        items[(ref, "Reference")] = (str(ref), (rx, ry), -1.0)
        if comp["value"]:
            items[(ref, "Value")] = (str(comp["value"]), (vx, vy), 1.0)
    order = sorted(items)
    pos = {k: (0, 0) for k in order}

    def anchor(k, off):
        _txt, (hx, hy), uy = items[k]
        return (round(hx + off[1] * DC_STEP, 3),
                round(hy + uy * off[0] * DC_STEP, 3))

    def box_of(k, off):
        txt, _home, _uy = items[k]
        ax, ay = anchor(k, off)
        return prop_box(txt, ax, ay)

    def clashes(k, off):
        ref = k[0]
        b = box_of(k, off)
        for ob, desc, owner in sym_boxes:
            if owner == ref:
                continue          # its own body / no-connect (canon: S-OCCL too)
            if _hit_box(b, ob):
                return desc
        for (p, q), desc, owner in sym_segs:
            if owner == ref:
                continue          # its own pin line
            if _seg_in_box(p, q, b) > DC_TOUCH:
                return desc
        for (p, q) in wires:
            if _seg_in_box(p, q, b) > DC_TOUCH:
                return f"wire ({p[0]:g},{p[1]:g})-({q[0]:g},{q[1]:g})"
        for j in order:
            if j != k and _hit_box(b, box_of(j, pos[j])):
                return f"{j[1]} {items[j][0]}"
        return None

    def legal(k, off):
        return prop_is_nearest(box_of(k, off), k[0], bodies)

    for _rnd in range(DC_ROUNDS):
        todo = [k for k in order if clashes(k, pos[k]) is not None]
        if not todo:
            break
        progressed = False
        for k in todo:
            got = next((o for o in _DC_PROP_LADDER
                        if clashes(k, o) is None and legal(k, o)), None)
            if got is None or got == pos[k]:
                continue
            pos[k] = got
            progressed = True
        if not progressed:
            break

    out, moved = {}, 0
    for comp in placed:
        ref = comp["refdes"]
        rk, vk = (ref, "Reference"), (ref, "Value")
        rp = anchor(rk, pos[rk])
        vp = anchor(vk, pos[vk]) if vk in items else prop_anchors[ref][1]
        moved += sum(1 for k in (rk, vk) if k in pos and pos[k] != (0, 0))
        out[ref] = (rp, vp)
    return out, moved


def _candidates():
    """The search ladder, in a FIXED order — same input, same sheet, always.

    Cheapest first (`(0, 0)` is always tried first, so a label with no
    collision never moves at all); at equal cost prefer the sideways step,
    because an outward step lengthens the label's reach into whatever lies
    beyond it while a sideways one keeps the reach envelope exactly where the
    author put it; `+cross` before `-cross` purely to break the tie."""
    out = []
    for cost in range(DC_MAX_ALONG + DC_MAX_CROSS + 1):
        for a in range(DC_MAX_ALONG + 1):
            for c in range(DC_MAX_CROSS + 1):
                if a + c != cost:
                    continue
                for s in ((0,) if c == 0 else (1, -1)):
                    out.append((a, c * s))
    return out


_DC_LADDER = _candidates()


def _stub(anchor, side, along, cross, cross_first=True):
    """The wire path from a label's ORIGINAL anchor to a displaced one. Both
    corner orders reach the same end point and are BOTH tried, in this order:

      * ACROSS FIRST is preferred, because it does not lengthen the label's
        reach — the plate's far edge stays exactly where the author put it;
      * OUTWARD FIRST is the fallback, and it is not a nicety. A label
        anchored on a pin of a multi-pin symbol sits in a COLUMN of pin tips
        2.54 mm apart, so a sideways wire leaving that anchor runs straight
        through its neighbours and is (rightly) refused every time. One step
        out of the column first, and the same sideways move is free. MEASURED
        on pluto-rx2-8way-v2: `ANT2` and `3V3_MOD` both sit in such a column,
        and across-first alone cannot place either of them.
    """
    ux, uy = SIDE_REACH[side]
    px, py = _PERP_OF[side]
    legs = ([(px * cross, py * cross), (ux * along, uy * along)] if cross_first
            else [(ux * along, uy * along), (px * cross, py * cross)])
    pts = [anchor]
    for dx, dy in legs:
        if dx or dy:
            pts.append((round(pts[-1][0] + dx, 3), round(pts[-1][1] + dy, 3)))
    return pts


def _near(a, b, tol=DC_NET_TOL):
    return abs(a[0] - b[0]) < tol and abs(a[1] - b[1]) < tol


def _pt_on_wire(pt, a, b, tol=DC_NET_TOL):
    """Does `pt` lie ON segment a-b, ENDPOINTS INCLUDED?

    The endpoints are the whole point. A global_label sitting anywhere along a
    wire is attached to it by `kicad-cli sch export netlist` — that is the same
    mid-segment attachment the `3V3_ANALOG` merge above turns on — so a
    displaced label whose new anchor happens to land mid-span on some OTHER
    net's wire silently merges the two. MEASURED before this check existed:
    72 nodes moved on crow-recorder-central-v2, 24 on pluto-cal-switch and 4 on
    pluto-rx2-8way (`U_MCU.51` read `DVDD_1V1` where it had read `QSPI_SD3`),
    while every stub still satisfied the connection-POINT rules — because a
    point in the MIDDLE of a wire is not a connection point.
    """
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    if L2 <= 1e-12:
        return _near(pt, a, tol)
    t = max(0.0, min(1.0, ((pt[0] - a[0]) * dx + (pt[1] - a[1]) * dy) / L2))
    return math.hypot(pt[0] - (a[0] + t * dx), pt[1] - (a[1] + t * dy)) <= tol


def _stub_plan(path, wires, conn_pts, tips, home, net):
    """The wire segments a displacement must ADD, or None if it cannot be made
    without risking a change of connectivity.

    THE CHEAP CASE FIRST, and it is most of them: if the step runs ALONG a wire
    of the label's OWN net that already covers it, the label simply slides down
    that wire and NOTHING is added. A global_label sitting mid-wire is attached
    by KiCad's netlister exactly as one sitting on a pin tip is — the same fact
    that made the `3V3_ANALOG` merge above possible — so this is a free move,
    and on this fleet it is the move most labels need, because the direction a
    crowded label wants to escape in is usually the direction its own wire
    already runs.

    Where a wire really has to be added the rules are blunt, because a wire
    that merges two nets is a far worse outcome than a label that does not
    move: nothing already on the sheet may touch the new segment or sit at its
    far end (only `home`, the point it leaves from, may), and it may not run
    collinear-and-overlapping with any wire. A transverse CROSSING is allowed —
    KiCad joins crossing wires only where a junction dot says so.
    """
    emit = []
    for k in range(len(path) - 1):
        p, q = path[k], path[k + 1]
        covered = False
        for (a, b, wnet) in wires:
            if not _collinear_overlap(p, q, a, b):
                continue
            if wnet != net:
                return None                      # would join a foreign net
            if _contains(a, b, p) and _contains(a, b, q):
                covered = True                   # a free ride on our own wire
            else:
                return None                      # partial overlap: don't guess
        if covered:
            continue
        for pt in conn_pts:
            if _near(pt, home):
                continue
            if _on_segment(pt[0], pt[1], p[0], p[1], q[0], q[1], eps=DC_NET_TOL):
                return None
            if _near(pt, q):
                return None
        emit.append((p, q))
    # NOTHING the label now touches may belong to a foreign net. Every corner
    # of the path, and above all the far end where the label itself lands, is
    # tested against every wire on the sheet — not merely against connection
    # POINTS, because a label anchored mid-span is attached just as firmly as
    # one anchored on an endpoint.
    for pt in path[1:]:
        for (a, b, wnet) in wires:
            if wnet != net and _pt_on_wire(pt, a, b):
                return None
    # ...and it must not land ON another pin's connection point, which would
    # read as naming that pin — the one thing this pass must never do.
    for t in tips:
        if _near(t, path[-1]) and not _near(t, home):
            return None
    return emit


def _contains(a, b, p, eps=1e-6):
    """Does the segment a-b contain the (already collinear) point p?"""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    if L2 <= eps:
        return False
    t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2
    return -eps <= t <= 1 + eps


def _collinear_overlap(p, q, a, b, eps=1e-6):
    """Do segments p-q and a-b lie on one line and share more than a point?"""
    dx, dy = q[0] - p[0], q[1] - p[1]
    for pt in (a, b):
        if abs((pt[0] - p[0]) * dy - (pt[1] - p[1]) * dx) > eps * 1e3:
            return False
    L2 = dx * dx + dy * dy
    if L2 <= eps:
        return False
    ts = sorted(((pt[0] - p[0]) * dx + (pt[1] - p[1]) * dy) / L2 for pt in (a, b))
    return min(ts[1], 1.0) - max(ts[0], 0.0) > eps


# ============================================ two nets as one conductor (S12)
# THE SHEET MAY NOT DRAW TWO NETS AS ONE CONDUCTOR. Everything above this line
# guards a POINT against a wire — a pin tip on a foreign wire (the `_on_segment`
# drop in `convert_layout`), a label anchor on a foreign wire (`_pt_on_wire`).
# Nothing ever compared a WIRE against a WIRE, so two nets routed onto the same
# line were drawn as one unbroken conductor and every gate stayed green.
#
# MEASURED 2026-07-31, pluto-rx2-8way-v2 `04_kicad`: `SW_V3` runs
# (89.535,157.480)->(89.535,128.270) and `SEL_V4` runs
# (89.535,168.275)->(89.535,153.035). Same x, 4.4450 mm of shared ink, and the
# union of vertical ink at x=89.535 is one unbroken 40.005 mm run carrying two
# nets — with the `SW_V3` plate anchored mid-run at (89.535,140.335), on the
# part a reader would call SEL_V4.
#
# WHY NO EXISTING GUARD FIRES, and it is not that they are weak. Canon S10 says
# "kicad-cli merges wires whose endpoint touches a foreign wire or that overlap
# collinearly". THAT CLAUSE IS FALSE, MEASURED against kicad-cli 10.0.4 on a
# purpose-built probe sheet (scratchpad/probe, four cases, netlist exit 0):
#     dotless T (endpoint on a foreign wire's interior)  -> SEPARATE nets
#     collinear overlap, no junction                     -> SEPARATE nets
#     junction dot at the touch point                    -> MERGED   (control)
#     shared ENDPOINT, no junction                       -> MERGED   (control)
# So the netlist is RIGHT and every netlist-shaped gate (S-NETMERGE, parity,
# count) is honestly green. The defect is confined to the drawn sheet, which is
# the one artifact a human reads at bring-up — and S10's false clause is
# precisely why no wire-geometry gate was ever built: the canon asserted the
# netlist gate already covered it.
#
# THE DOT IS NOT AVAILABLE AS A REMEDY FOR THE DIFFERENT-NET CASE. A junction
# at a different-net touch point does not annotate the ambiguity, it CREATES the
# short (control case 3 above). So different-net contact is resolved by removing
# drawn ink — never by dotting it. Same-net contact is the opposite: there the
# dot is the truth, and its absence is what leaves the sheet ambiguous.
def wire_net_ambiguity(segs, junctions):
    """Every place `segs` draws two DIFFERENT nets as one conductor.

    `segs` is [(a, b, net)]; `junctions` a set of (x, y) keys.
    -> (overlaps, tees, same_net_tees)
       overlaps      [(i, j)]      collinear, different nets, shared ink
       tees          [(i, j, pt)]  endpoint of i strictly inside j, different
                                   nets, no junction dot at pt
       same_net_tees [(i, j, pt)]  the same geometry within ONE net and no dot —
                                   not a lie, but drawn ambiguously; the caller
                                   dots these rather than dropping them.
    """
    overlaps, tees, same_tees = [], [], []
    n = len(segs)
    for i in range(n):
        ai, bi, ni = segs[i]
        for j in range(i + 1, n):
            aj, bj, nj = segs[j]
            if ni != nj and _collinear_overlap(ai, bi, aj, bj):
                overlaps.append((i, j))
    for i in range(n):
        ai, bi, ni = segs[i]
        for pt in (ai, bi):
            for j in range(n):
                if i == j:
                    continue
                aj, bj, nj = segs[j]
                if not _on_segment(pt[0], pt[1], aj[0], aj[1], bj[0], bj[1]):
                    continue
                if (round(pt[0], 3), round(pt[1], 3)) in junctions:
                    continue
                (tees if ni != nj else same_tees).append((i, j, pt))
    return overlaps, tees, same_tees


def disambiguate_wires(segs, junctions):
    """Drop the fewest drawn segments that leaves no two nets sharing ink.

    Greedy over the conflict graph — repeatedly drop the segment in the most
    conflicts (ties broken on the segment's own coordinates, so the choice is
    deterministic and the sheet is reproducible). Dropping is the right verb
    rather than trimming: a dropped wire costs the reader a drawn route, and
    the self-healing label pass still names every pin, so connectivity is
    preserved exactly. A TRIMMED wire would leave a free end whose position was
    chosen by this function rather than by the layout, which is a new invention
    on the sheet -- and inventing geometry is how the defect above got here.

    -> (kept_segs, dropped_count)
    """
    keep = list(range(len(segs)))
    dropped = 0
    for _ in range(len(segs) + 1):
        live = [segs[i] for i in keep]
        ov, te, _same = wire_net_ambiguity(live, junctions)
        if not ov and not te:
            break
        deg = {}
        for a, b in ov:
            deg[a] = deg.get(a, 0) + 1
            deg[b] = deg.get(b, 0) + 1
        for a, b, _pt in te:
            deg[a] = deg.get(a, 0) + 1
            deg[b] = deg.get(b, 0) + 1
        worst = max(deg, key=lambda k: (deg[k], live[k][0], live[k][1], live[k][2]))
        keep.pop(worst)
        dropped += 1
    return [segs[i] for i in keep], dropped


def sheet_wire_ambiguity(content):
    """The same question asked of EMITTED SHEET TEXT, by a reader that shares
    no state with the emitter — the backstop for canon M1. Parses `(wire ...)`
    and `(junction ...)` out of the finished s-expression and attributes a net
    to each wire by the global_label plates its connected component carries,
    exactly as a human tracing the ink would. -> list of human-readable strings.
    """
    wires = [((float(a), float(b)), (float(c), float(d))) for a, b, c, d in
             re.findall(r"\(wire \(pts \(xy ([-\d.]+) ([-\d.]+)\) "
                        r"\(xy ([-\d.]+) ([-\d.]+)\)\)", content)]
    juncs = {(round(float(x), 3), round(float(y), 3)) for x, y in
             re.findall(r"\(junction \(at ([-\d.]+) ([-\d.]+)\)", content)}
    labels = [(nm, (float(x), float(y))) for nm, x, y in
              re.findall(r'\(global_label "([^"]+)" \(shape \w+\) '
                         r'\(at ([-\d.]+) ([-\d.]+)', content)]
    # components under the rule KiCad actually implements: shared ENDPOINTS
    # only (MEASURED — see the header above), so a dotless T or an overlap
    # leaves the two sides in DIFFERENT components, which is the whole point.
    uf = UF()
    for a, b in wires:
        uf.union(key_pt(a), key_pt(b))
    names = {}
    for nm, p in labels:
        for a, b in wires:
            if _pt_on_wire(p, a, b):
                names.setdefault(uf.find(key_pt(a)), set()).add(nm)
                break

    def net_of(i):
        s = names.get(uf.find(key_pt(wires[i][0])))
        return "+".join(sorted(s)) if s else None

    out = []
    for i in range(len(wires)):
        for j in range(i + 1, len(wires)):
            ni, nj = net_of(i), net_of(j)
            if ni and nj and ni != nj and _collinear_overlap(
                    wires[i][0], wires[i][1], wires[j][0], wires[j][1]):
                out.append(f"collinear overlap {ni} / {nj} at {wires[i]}")
    for i in range(len(wires)):
        for pt in wires[i]:
            for j in range(len(wires)):
                if i == j or key_pt(pt) in juncs:
                    continue
                aj, bj = wires[j]
                if not _on_segment(pt[0], pt[1], aj[0], aj[1], bj[0], bj[1]):
                    continue
                ni, nj = net_of(i), net_of(j)
                if ni and nj and ni != nj:
                    out.append(f"dotless T {ni} into {nj} at {pt}")
    return sorted(set(out))


def key_pt(p):
    return (round(p[0], 3), round(p[1], 3))


def _wire_hits(box, anchor_pt, reach, wires, tol=1e-6):
    """The first wire in `wires` that is drawn ACROSS `box`, or None.

    THE ATTACHMENT EXEMPTION, and it is the whole reason this is not just one
    more entry in `_obstacles`. A global_label attaches at a wire END and its
    plate STARTS at that same point, so the wire it belongs to lies on the
    plate's base edge and Liang-Barsky charges up to a full PLATE_CROSS of it
    as "inside". Charging a plate for the wire it is attached to would move
    every label on every wired sheet.

    TWO CONDITIONS, AND BOTH ARE LOAD-BEARING.

    THE ANCHOR MUST BE THE WIRE'S ENDPOINT, NOT MERELY ON IT. A plate anchored
    MID-SPAN has its own conductor drawn straight through the name from BOTH
    sides, which is a real defect and is what `SW_V1`, `SW_V4`, `SEL_V1` and
    `RX1_MAIN` shipped on pluto-rx2-8way-v2.

    AND THE WIRE MUST NOT LEAVE FORWARD. A wire running from the anchor INTO
    the half-space the plate reaches into is drawn down the plate's own
    centreline, through the letters — MEASURED on the shipped `two_resistors`
    fixture at 2.7819 mm of conductor through `MID` in KiCad's own render, a
    finding both this model and S-OCCL forgave in their first draft. Only a
    wire arriving from BEHIND, or PERPENDICULAR (the base-edge case the
    exemption exists for), is the attachment.

    This is the same rule `sch_occlusion.occlusions` grades by, stated
    independently here because the emitter must not import its own grader
    (canon M1) — `t1_converter.py t_no_ink_is_drawn_through_any_text` pins the
    two against each other in rendered ink.
    """
    for (p, q) in wires:
        if anchor_pt is not None:
            fwd = None
            for a, b in ((p, q), (q, p)):
                if (abs(anchor_pt[0] - a[0]) < tol
                        and abs(anchor_pt[1] - a[1]) < tol):
                    fwd = (b[0] - a[0]) * reach[0] + (b[1] - a[1]) * reach[1]
                    break
            if fwd is not None and fwd <= tol:
                continue
        if _seg_in_box(p, q, box) > DC_TOUCH:
            return f"wire ({p[0]:g},{p[1]:g})-({q[0]:g},{q[1]:g})"
    return None


def place_labels(cands, placed, prop_rows_by_ref, flag_host, comp_by_ref,
                 segs, junctions, pin_tip):
    """De-collide every global_label this module places. Canon S11.

    THE CONTRACT, and it is as much about what this REFUSES as what it does.
    A label's REACH DIRECTION is the fact the sheet is read by — a plate is
    understood to belong to the pin at its blunt end and to name the net
    running out of it — so the search never changes `side`, never flips a label
    onto the far side of its pin, and never re-anchors it on a different pin or
    a different net. The only freedoms are to step the anchor OUTWARD along the
    reach it already has, or SIDEWAYS across it, carrying a wire with it so the
    label stays electrically exactly where it was.

    A label with no legal placement raises `LabelPlacementError` NAMING it. It
    is never dropped, never silently left overlapping, and never answered by
    falling back to a different emitter.

    TWO OBSTACLE CLASSES, SPLIT BY THEIR REMEDY (2026-07-31, with wires).
    Everything the pass could see before wires — a symbol body, a pin line, a
    Reference/Value row, a ground glyph, another PLATE — is HARD: a plate lying
    on one of those is how `ANT2 x 3V3_MOD` composited into `N3V3_MOD2`, a
    sheet that reads as a different NET, and there is no degree of that worth
    shipping. Unplaceable against the hard set still raises, exactly as before.

    A WIRE IS SOFT, and the asymmetry is the point rather than an escape hatch.
    A plate drawn over a conductor is illegible; it cannot compose into another
    NAME, because a wire carries no glyphs. Its remedy is `sch_occlusion`'s
    S-OCCL row, which is per-board and thresholded precisely because "text
    crowding is a matter of degree" (that module's own words). So the search
    tries hardest to clear wires and, where a sheet's own layout makes that
    impossible, leaves the plate WHERE THE AUTHOR PUT IT and lets S-OCCL report
    it — rather than converting a legibility finding into a build failure.

    MEASURED, and this is why the split is not a convenience: with wires HARD,
    four of the six layout-mode fleet sheets stop converting at all —
    crow-recorder-central-v2 (7 labels), pluto-cal-switch (4), pluto-rx2-8way
    (4) and interposer (2), every one of them a `QSPI_*`-style plate reaching
    across an 80 mm vertical bus that no offset in any bound can escape (the
    ladder was re-run at (10, 16) and the same labels stay stuck). Those are
    sealed boards whose sheets are already graded and already carry the
    finding; a hard error there answers "this plate is hard to read" with "this
    board cannot be built".

    Returns (labels, stubs, extra_junctions, moved, on_wire) where `labels` is
    [(net, x, y, side)], `stubs` is [((p, q), net)] and `on_wire` counts the
    plates left lying on a conductor for S-OCCL to report.
    """
    boxes, obsegs = _obstacles(placed, prop_rows_by_ref, flag_host, comp_by_ref)
    base_wires = [(a, b) for a, b, _n in segs]
    prop_ink = [(b, d) for b, d, _o in _prop_boxes(placed, prop_rows_by_ref)]
    base_tips = sorted({(round(t[0], 3), round(t[1], 3)) for t in pin_tip.values()})
    base_pts = set(base_tips) | set(junctions) | {
        (round(v[0], 3), round(v[1], 3)) for a, b, _n in segs for v in (a, b)}

    # DETERMINISTIC ORDER. Tie-broken all the way down to the net name and then
    # the index, so two labels at one coordinate can never swap between runs.
    order = sorted(range(len(cands)),
                   key=lambda i: (cands[i][2], cands[i][1], cands[i][0], i))
    pos = {i: (0, 0) for i in range(len(cands))}      # (along, cross) in STEPS
    plan = {}                                        # i -> [(p, q), ...] added

    def anchor(i, off):
        _net, x, y, side = cands[i]
        ux, uy = SIDE_REACH[side]
        px, py = _PERP_OF[side]
        a, c = off[0] * DC_STEP, off[1] * DC_STEP
        return (round(x + ux * a + px * c, 3), round(y + uy * a + py * c, 3))

    def box_of(i, off):
        net, _x, _y, side = cands[i]
        ax, ay = anchor(i, off)
        return plate_box(net, ax, ay, side)

    def drawn_wires(exclude):
        """Every wire the sheet will actually carry — the imported segments plus
        the stubs already planned — with one label's own stub taken out, so a
        label is never blocked by the wire it is standing on the end of."""
        return base_wires + [pq for j, adds in plan.items() if j != exclude
                             for pq in adds]

    def clashes_hard(i, off):
        """The obstacle set as it stood before wires — the one whose remedy is
        never "leave it and report it"."""
        b = box_of(i, off)
        for ob, desc in boxes:
            if _hit_box(b, ob):
                return desc
        for (p, q), desc in obsegs:
            if _seg_in_box(p, q, b) > DC_TOUCH:
                return desc
        for j in range(len(cands)):
            if j != i and _hit_box(b, box_of(j, pos[j])):
                return f"label {cands[j][0]}"
        return None

    def on_wire(i, off):
        """WIRES. Ink of exactly the same kind as a pin line, and until this
        landed the search had never seen one: `_obstacles` was built from symbol
        geometry alone, so a plate could be moved OFF a Reference row and ONTO a
        conductor and the pass called it placed."""
        return _wire_hits(box_of(i, off), anchor(i, off),
                          SIDE_REACH[cands[i][3]], drawn_wires(i))

    def clashes(i, off):
        return clashes_hard(i, off) or on_wire(i, off)

    def stub_occludes(i, off, add):
        """Would the wire this displacement ADDS be drawn through a text?

        The rounds re-derive every label's clash set, so a stub laid across
        SOME OTHER label is eventually answered by moving that label. Nothing
        re-derives the PROPERTY rows — they are settled before this pass — so a
        stub across a Reference would be a finding this pass created and no
        later step could see. Both are checked here, which makes the rule
        simply: a stub never becomes an occluder."""
        for (p, q) in add:
            for ob, desc in prop_ink:
                if _seg_in_box(p, q, ob) > DC_TOUCH:
                    return desc
            for j in range(len(cands)):
                jb = box_of(j, off if j == i else pos[j])
                ja = anchor(j, off if j == i else pos[j])
                if _wire_hits(jb, ja, SIDE_REACH[cands[j][3]],
                              [(p, q)]) is not None:
                    return f"label {cands[j][0]}"
        return None

    def world(exclude):
        """Wires and connection points as they stand, with one label's own
        contribution taken out — so a label is never blocked by itself."""
        w = list(segs)
        pts = set(base_pts)
        for j, adds in plan.items():
            if j == exclude:
                continue
            for (p, q) in adds:
                w.append((p, q, cands[j][0]))
                pts.add(p)
                pts.add(q)
        for j in range(len(cands)):
            if j != exclude:
                pts.add(anchor(j, pos[j]))
        return w, sorted(pts)

    def best_offset(i):
        """The cheapest offset that clears EVERYTHING; failing that, the
        cheapest that clears the HARD set and is legal electrically.

        The ladder is walked once, in its fixed order, and the FIRST hard-clear
        offset with a legal stub is remembered as the fallback — which for a
        label that was already hard-clear at home is `(0, 0)`, so a plate the
        wire model cannot rescue keeps exactly the placement the pre-wire pass
        gave it. That is what makes this addition unable to move a board's
        S-OCCL count UP.
        """
        net, x, y, side = cands[i]
        home = (round(x, 3), round(y, 3))
        w, pts = world(i)

        def stub_for(off):
            """The cheapest legal corner order for `off`, or None if neither
            can be laid without risking connectivity."""
            for cross_first in (True, False):
                path = _stub(home, side, off[0] * DC_STEP, off[1] * DC_STEP,
                             cross_first)
                add = ([] if len(path) == 1
                       else _stub_plan(path, w, pts, base_tips, home, net))
                if add is not None:
                    return add
                if len(path) < 3:
                    break        # a single leg has only one corner order
            return None

        soft = None
        for off in _DC_LADDER:
            if clashes_hard(i, off) is not None:
                continue
            dirty = on_wire(i, off) is not None
            if dirty and soft is not None:
                continue      # a cheaper hard-clear fallback is already held
            add = stub_for(off)
            if add is None:
                continue
            # A STUB IS ALSO INK, and a displacement that lays its own wire
            # across a plate or a Reference has moved the finding rather than
            # removed it. Soft, for the same reason a plate on a wire is soft:
            # both are legibility, and neither can make the sheet say a
            # different NET.
            if not dirty and stub_occludes(i, off, add) is None:
                return off, add
            if soft is None:
                soft = (off, add)
        return soft

    # ROUND-BASED, and the rounds are what make it work rather than a nicety.
    # Where two labels collide with each other, EITHER may move; a single
    # greedy pass tries only the one its ordering reaches first, and if that
    # one happens to be the boxed-in half it fails on a pair the other half
    # could have resolved in one step (MEASURED: `3V3_MOD x ANT2` on
    # pluto-rx2-8way-v2 does exactly this). Re-deriving the clash set each
    # round lets the freer label take the step, and a label whose counterparty
    # moved away is re-offered `(0, 0)` first and settles back home.
    for _rnd in range(DC_ROUNDS):
        todo = [i for i in order if clashes(i, pos[i]) is not None]
        if not todo:
            break
        progressed = False
        for i in todo:
            got = best_offset(i)
            if got is None or got[0] == pos[i]:
                continue
            pos[i], plan[i] = got[0], got[1]
            if got[0] == (0, 0):
                plan.pop(i, None)
            progressed = True
        if not progressed:
            break

    stuck = [i for i in order if clashes_hard(i, pos[i]) is not None]
    if stuck:
        i = stuck[0]
        net, x, y, side = cands[i]
        raise LabelPlacementError(
            f"global_label {net!r} at ({x:.3f}, {y:.3f}) reaching {side}: no "
            f"legal placement — it occludes {clashes_hard(i, pos[i])} and every one "
            f"of the {len(_DC_LADDER)} offsets in the search is blocked too "
            f"({len(stuck)} label(s) stuck: "
            f"{', '.join(sorted(cands[j][0] for j in stuck[:6]))}). Its reach "
            f"direction is load-bearing (canon S11) so it may not be turned "
            f"around, and re-anchoring it on another pin would change what the "
            f"sheet says. Fix the tscircuit schematic layout.")

    stubs, extra_junc, moved = [], [], 0
    for i in order:
        if pos[i] == (0, 0):
            continue
        moved += 1
        net = cands[i][0]
        home = (round(cands[i][1], 3), round(cands[i][2], 3))
        for (p, q) in plan.get(i, []):
            stubs.append(((p, q), net))
        # leaving from the MIDDLE of an existing wire is a T, and KiCad joins a
        # T only where a junction dot says so.
        if plan.get(i) and any(_on_segment(home[0], home[1], a[0], a[1], b[0], b[1])
                               for a, b, _n in segs):
            extra_junc.append(home)

    left_on_wire = sorted(cands[i][0] for i in order if on_wire(i, pos[i]))
    out = []
    for i, (net, _x, _y, side) in enumerate(cands):
        ax, ay = anchor(i, pos[i])
        out.append((net, ax, ay, side))
    return out, stubs, extra_junc, moved, left_on_wire


def convert_layout(circuit_json, project, title, rev, date, aliases=None, overrides=None,
                   ties=None):
    """Layout-preserving emitter. Returns (content, components, stats). Raises
    LayoutFallback if geometry can't be imported without a cross-net short."""
    aliases = aliases or {}
    overrides = overrides or {}
    d = json.load(open(circuit_json, encoding="utf-8-sig"))
    components, flag_host, portinfo = load_model(circuit_json, aliases, overrides,
                                                 return_ports=True, ties=ties)
    comp_by_ref = {c["refdes"]: c for c in components}
    scomp = [e for e in d if e.get('type') == 'schematic_component']
    sport = [e for e in d if e.get('type') == 'schematic_port']
    strace = [e for e in d if e.get('type') == 'schematic_trace']
    snlabel = [e for e in d if e.get('type') == 'schematic_net_label']
    if not scomp or not sport:
        raise LayoutFallback("no schematic_component/schematic_port geometry")
    key2net = {}
    for e in d:
        if e.get('type') == 'source_net':
            key2net.setdefault(e['subcircuit_connectivity_map_key'], e['name'])

    ports_of_scomp = {}
    for p in sport:
        ports_of_scomp.setdefault(p['schematic_component_id'], []).append(p)

    # ---- bounds over all schematic geometry -> transform
    xs, ys = [], []
    for c in scomp:
        cx, cy = c['center']['x'], c['center']['y']
        w, h = c['size']['width'], c['size']['height']
        xs += [cx - w / 2, cx + w / 2]
        ys += [cy - h / 2, cy + h / 2]
    for p in sport:
        xs.append(p['center']['x'])
        ys.append(p['center']['y'])
    for t in strace:
        for e in t['edges']:
            xs += [e['from']['x'], e['to']['x']]
            ys += [e['from']['y'], e['to']['y']]
    for n in snlabel:
        xs.append(n['anchor_position']['x'])
        ys.append(n['anchor_position']['y'])
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)

    def T(x, y):
        # y flip: tscircuit y-up -> KiCad y-down. snap to L_G grid (consistently
        # from the same source coord) so pin tips and wire ends coincide exactly.
        return (round(_rhu((x - minx) * L_S + L_M, L_G), 3),
                round(_rhu((maxy - y) * L_S + L_M, L_G), 3))

    def key(pt):
        return (round(pt[0], 3), round(pt[1], 3))

    # ---- build one symbol per schematic_component; record pin tips
    lib_syms = dict(sw.power_lib_symbols(LIB))
    placed = []                 # emitted symbol instances (dicts)
    pin_tip = {}                # (refdes, pad) -> (x, y)
    tip_net = {}                # (x, y) -> net (for short filtering; incl GND/None)
    pin_side = {}               # (refdes, pad) -> side
    portid2tip = {}             # source_port_id -> (x, y) of its KiCad pin tip
    for c in scomp:
        cid = c['source_component_id']
        cx, cy = c['center']['x'], c['center']['y']
        meta = None
        # find refdes via any of this component's ports
        cports = ports_of_scomp.get(c['schematic_component_id'], [])
        if not cports:
            continue
        refdes = portinfo[cports[0]['source_port_id']]['refdes']
        meta = comp_by_ref.get(refdes)
        if meta is None:
            continue
        inst = T(cx, cy)
        w_mm = max(c['size']['width'] * L_S, 2.54)
        h_mm = max(c['size']['height'] * L_S, 2.54)
        # group this component's schematic_ports by KiCad pad name (collapse
        # internally-connected duplicate pads to one pin, matching v1/parity)
        by_pad = {}
        for p in cports:
            pi = portinfo[p['source_port_id']]
            by_pad.setdefault(pi['pad'], []).append(p)
        pins_geo = []
        tips = {}
        for pad, plist in sorted(by_pad.items(), key=lambda kv: natkey(kv[0])):
            rep = min(plist, key=lambda p: (p.get('pin_number') or 0))
            pi = portinfo[rep['source_port_id']]
            net = pi['net']
            # a connected duplicate wins over an NC one
            for p in plist:
                if portinfo[p['source_port_id']]['net'] is not None:
                    net = portinfo[p['source_port_id']]['net']
                    break
            tip = T(rep['center']['x'], rep['center']['y'])
            # KiCad LIB-SYMBOL space is y-UP but the sheet is y-DOWN: a symbol
            # instance flips local y (sheet_y = inst_y - local_y). So the pin's
            # local coords must be (tip_x - inst_x, inst_y - tip_y) for its KiCad
            # tip to land exactly on the sheet coordinate T(port) where the wires
            # and labels are drawn.
            lx = round(tip[0] - inst[0], 3)
            lib_y = round(inst[1] - tip[1], 3)
            if abs(lx) >= abs(lib_y):
                if lx < 0:
                    side, ang, length = 'left', 0, max(-lx - w_mm / 2, 1.27)
                else:
                    side, ang, length = 'right', 180, max(lx - w_mm / 2, 1.27)
            else:
                if lib_y > 0:
                    side, ang, length = 'top', 270, max(lib_y - h_mm / 2, 1.27)
                else:
                    side, ang, length = 'bottom', 90, max(-lib_y - h_mm / 2, 1.27)
            pname = re.sub(r'[\s"()]+', '_', str(pi['func'])) or str(pad)
            pins_geo.append((str(pad), pname, lx, lib_y, ang, length))
            pin_tip[(refdes, pad)] = tip
            tips[str(pad)] = tip
            pin_side[(refdes, pad)] = side
            tip_net.setdefault(key(tip), set()).add(net)
            for p in plist:
                portid2tip[p['source_port_id']] = tip
        # EXTRA PINS: a model pin with NO schematic_port geometry is a 02_parts
        # `tie:` pad (an exposed thermal pad tscircuit's footprint can't express).
        # load_model already added it to meta["pins"] on its net; give it a
        # synthetic slot along the box's bottom edge so the symbol/instance emit
        # the pin and its GND power symbol (or self-healing label) — carrying it
        # into the netlist exactly like a geometric pin.
        xtra = 0
        for pad, func, net in meta["pins"]:
            if str(pad) in tips:
                continue
            length = 2.54
            lx = round(xtra * 2.54, 3)
            lib_y = round(-(h_mm / 2 + length), 3)
            tip = (round(inst[0] + lx, 3), round(inst[1] - lib_y, 3))
            pname = re.sub(r'[\s"()]+', '_', str(func)) or str(pad)
            pins_geo.append((str(pad), pname, lx, lib_y, 90, length))
            pin_tip[(refdes, str(pad))] = tip
            tips[str(pad)] = tip
            pin_side[(refdes, str(pad))] = 'bottom'
            tip_net.setdefault(key(tip), set()).add(net)
            xtra += 1
        symname = "SYM_" + re.sub(r'[^A-Za-z0-9_]', '_', refdes)
        lib_syms[symname] = lib_symbol_geo(symname, w_mm, h_mm, pins_geo,
                                           ref=refdes[0], lib=LIB,
                                           hide_numbers=len(pins_geo) <= 2)
        placed.append({**meta, "sym": symname, "inst": inst,
                       "w": w_mm, "h": h_mm, "pins_geo": pins_geo, "tips": tips,
                       "sides": {str(k): pin_side[(refdes, k)] for k in tips}})

    # ---- wires from schematic_trace routes (GND excluded -> power symbols)
    def resolve_vertex(pt):
        best, bd = None, 1e18
        for p in sport:
            dd = (p['center']['x'] - pt['x']) ** 2 + (p['center']['y'] - pt['y']) ** 2
            if dd < bd:
                bd, best = dd, p
        if bd <= L_PORT_TOL2 and best['source_port_id'] in portid2tip:
            return portid2tip[best['source_port_id']]
        return T(pt['x'], pt['y'])

    raw_segs = []               # (a, b, net)
    junctions = set()
    for t in strace:
        net = canon_net(key2net.get(t['subcircuit_connectivity_map_key']), aliases)
        if net is None or net == "GND":
            continue
        for e in t['edges']:
            a = resolve_vertex(e['from'])
            b = resolve_vertex(e['to'])
            if key(a) == key(b):
                continue
            raw_segs.append((a, b, net))
        for j in (t.get('junctions') or []):
            junctions.add(key(T(j['x'], j['y'])))

    # ---- safety filter: drop any segment that would short a foreign net
    all_tips = list(tip_net.items())
    segs = []
    dropped = 0
    for a, b, net in raw_segs:
        bad = False
        for ep in (a, b):
            nets = tip_net.get(key(ep))
            if nets and any(nn not in (None, net) for nn in nets):
                bad = True
                break
        if not bad:
            for tk, nets in all_tips:
                if key(a) == tk or key(b) == tk:
                    continue
                if any(nn not in (None, net) for nn in nets) and \
                   _on_segment(tk[0], tk[1], a[0], a[1], b[0], b[1]):
                    bad = True
                    break
        if bad:
            dropped += 1
        else:
            segs.append((a, b, net))

    # ---- ...and the wire-vs-wire half of that same filter (canon S12).
    # The loop above tests a foreign PIN TIP against this segment. Two nets can
    # share ink with no pin tip anywhere near the shared part — which is exactly
    # what pluto-rx2-8way-v2 shipped. See `wire_net_ambiguity` for the measured
    # KiCad behaviour that makes this a DRAWING defect rather than a netlist one.
    segs, amb_dropped = disambiguate_wires(segs, junctions)
    dropped += amb_dropped

    # ---- candidate labels from schematic_net_label (GND excluded)
    tip_reach = {}              # sheet coord -> the reach of the pin sitting there
    for (_rd, _pd), _t in pin_tip.items():
        tip_reach.setdefault(key(_t), pin_side[(_rd, _pd)])
    cand_labels = []            # (net, x, y, side) — `side` is the REACH
    for n in snlabel:
        net = canon_net(n['text'], aliases)
        if net is None or net == "GND":
            continue
        x, y = T(n['anchor_position']['x'], n['anchor_position']['y'])
        # the SIDE is the direction the plate REACHES, derived from the label's
        # own geometry — never `anchor_side`, which names the opposite edge and
        # inverted every label on every board until 2026-07-31.
        side = label_plate_side(n, tip_reach.get(key((x, y))))
        if side not in SIDE_REACH:
            side = 'left'
        cand_labels.append((net, x, y, side))

    # ---- prune dangling wires: iteratively drop any segment with a FREE end
    # (an endpoint not on a pin tip / junction / net label and not shared with
    # another kept segment). A free wire end is a KiCad `wire_dangling` ERC
    # ERROR — a trace stub whose far end reached nothing after import. Peeling
    # them never drops connectivity a pin needs (the pin keeps its GND symbol /
    # net label / other wires; the self-healing pass still names every pin).
    anchors = set(tip_net.keys()) | set(junctions)
    anchors |= {key((x, y)) for (_n, x, y, _s) in cand_labels}
    pruned = 0
    changed = True
    while changed:
        changed = False
        endpt_count = {}
        for a, b, _n in segs:
            endpt_count[key(a)] = endpt_count.get(key(a), 0) + 1
            endpt_count[key(b)] = endpt_count.get(key(b), 0) + 1
        kept = []
        for a, b, n in segs:
            free = ((key(a) not in anchors and endpt_count[key(a)] < 2) or
                    (key(b) not in anchors and endpt_count[key(b)] < 2))
            if free:
                changed = True
                pruned += 1
            else:
                kept.append((a, b, n))
        segs = kept

    # ---- union-find: pins + kept wire endpoints + label coords + junctions
    uf = UF()
    for k in tip_net:
        uf.find(k)
    for a, b, _net in segs:
        uf.union(key(a), key(b))
    for k in junctions:
        uf.find(k)
    for net, x, y, _s in cand_labels:
        uf.find(key((x, y)))
        # A label sitting MID-SEGMENT is electrically ON that wire — KiCad's
        # netlister attaches it, so it must join the wire's root here too.
        # Without this union the label is a singleton root and the label-name
        # guard below cannot see the merge at all. The pin-tip half of this
        # rule already existed (the `_on_segment` drop above); this is the
        # label half, and the label half is the one that shipped a defect.
        for a, b, _n in segs:
            if key((x, y)) in (key(a), key(b)):
                break
            if _on_segment(x, y, a[0], a[1], b[0], b[1]):
                uf.union(key((x, y)), key(a))
                break
    # roots -> {pin_nets, label_names}
    root_pin_nets = {}
    root_label_names = {}
    pin_root = {}
    for (refdes, pad), tip in pin_tip.items():
        net = comp_pin_net(comp_by_ref, refdes, pad)
        r = uf.find(key(tip))
        pin_root[(refdes, pad)] = r
        if net is not None:
            root_pin_nets.setdefault(r, set()).add(net)
    for net, x, y, _s in cand_labels:
        r = uf.find(key((x, y)))
        root_label_names.setdefault(r, set()).add(net)

    # ---- short detection: a root that carries two different pin nets
    for r, nets in root_pin_nets.items():
        real = {n for n in nets if n and n != "GND"}
        if len(real) >= 2:
            raise LayoutFallback(
                f"cross-net short after import: root joins nets {sorted(real)} "
                f"({dropped} segs already dropped)")

    # ---- ...and a root that carries two different LABEL NAMES ---------------
    # THE MERGE HAPPENS AT EXPORT, AND IT HAPPENS ON LABELS (2026-07-28,
    # smc0985-cooksense rebuild). The guard above asks whether a root joins two
    # PIN nets, which is the short a human would draw. `kicad-cli sch export
    # netlist` does not care: two global labels on ONE electrical root merge
    # their nets whether or not a second pin is involved.
    #
    # MEASURED: tscircuit's auto-layout put the `3V3_ANALOG` global label at
    # (275.59, 365.76) — MID-SEGMENT on a `3V3` wire running (275.59, 401.32)
    # to (275.59, 355.60). One root, two label names, ONE pin net. The pin
    # guard saw nothing, the converter dropped 3 segments, DECLARED SUCCESS,
    # and the exported netlist had 191 nets with no `3V3_ANALOG` anywhere.
    # That would have re-merged the analog rail into the digital one and
    # silently undone the v1.3 P1-1 fix. `net_label_survival.py` caught it at
    # 161/162 — a human noticing one number, on a gate that runs later.
    #
    # Raising here means the board auto-falls back to `--mode grid`, which is
    # the whole point of LayoutFallback: a layout that cannot be imported
    # without merging nets is not a layout to import.
    #
    # GND is excluded on the same grounds as above — it is the one name that
    # legitimately reaches every root.
    for r, names in root_label_names.items():
        real = {n for n in names if n and n != "GND"}
        if len(real) >= 2:
            raise LayoutFallback(
                f"cross-net LABEL merge after import: root carries labels "
                f"{sorted(real)} — these merge into one net at "
                f"`kicad-cli sch export netlist` even though no second pin is "
                f"involved ({dropped} segs already dropped)")

    # ---- emit candidate labels only if they name a real (pin-bearing) root
    emit_labels = []
    named_roots = set()
    for net, x, y, side in cand_labels:
        r = uf.find(key((x, y)))
        if r in root_pin_nets and net in root_pin_nets[r]:
            emit_labels.append((net, x, y, side))
            named_roots.add(r)

    # ---- self-healing safety labels: name any pin-root a label didn't cover
    safety = 0
    covered = set(named_roots)
    for (refdes, pad), tip in sorted(pin_tip.items()):
        net = comp_pin_net(comp_by_ref, refdes, pad)
        if net is None or net == "GND":
            continue
        r = pin_root[(refdes, pad)]
        if r in covered:
            continue
        # `pin_side` is already a REACH ('left' == the pin sticks out to the
        # left), so it feeds the shared table directly. Note every synthetic
        # tie-pad pin is side 'bottom' — the row that rendered UP until the
        # LABEL_ANG_JUST fix above.
        side = pin_side[(refdes, pad)]
        emit_labels.append((net, tip[0], tip[1], side))
        covered.add(r)
        safety += 1

    # ---- LABEL DE-COLLISION (canon S11). Every property row is resolved
    # first, because a Reference/Value is one of the things a plate has to
    # stay off — and the rows themselves move to clear the ground glyphs of
    # their own pins (`prop_rows`), so they must be settled before, not during.
    prop_rows_by_ref = {}
    for comp in placed:
        pads = [num for num, _pn, _lx, _ly, _a, _l in comp["pins_geo"]]
        nets = {p: comp_pin_net(comp_by_ref, comp["refdes"], p) for p in pads}
        ry, vy = prop_rows(
            comp["inst"][0], comp["inst"][1], comp["w"], comp["h"],
            attached_glyph_boxes(pads, comp["tips"], comp["sides"], nets,
                                 str(flag_host[1]) if flag_host
                                 and flag_host[0] == comp["refdes"] else None))
        ix = comp["inst"][0]
        prop_rows_by_ref[comp["refdes"]] = ((ix, ry), (ix, vy))
    # ...and then off whatever the SHEET draws through them — above all the
    # wires, which `prop_rows` has no way to see (it is a y-only offset from the
    # body). Settled BEFORE the labels, because a plate has to stay off a
    # property row and the row must therefore already be where it will be drawn.
    prop_rows_by_ref, prop_moved = place_props(
        placed, prop_rows_by_ref, flag_host, comp_by_ref, segs)
    emit_labels, stubs, extra_junc, moved, on_wire = place_labels(
        emit_labels, placed, prop_rows_by_ref, flag_host, comp_by_ref,
        segs, junctions, pin_tip)
    segs = segs + [(p, q, net) for (p, q), net in stubs]
    junctions = junctions | {key(j) for j in extra_junc}

    # ---- FINAL wire-geometry verdict on the set actually about to be drawn
    # (canon S12). The stub planner already refuses to lay a stub collinear with
    # a foreign wire, so this normally finds nothing — but "normally" is not a
    # gate, and this is the last point at which the segment list is still the
    # thing that gets emitted.
    ov, te, same_te = wire_net_ambiguity(segs, junctions)
    if ov or te:
        det = ([f"{segs[i][2]}/{segs[j][2]} collinear at {segs[i][0]}"
                for i, j in ov[:4]] +
               [f"{segs[i][2]} tees into {segs[j][2]} at {p}"
                for i, j, p in te[:4]])
        raise LayoutFallback(
            f"{len(ov)} collinear different-net overlap(s) and {len(te)} "
            f"dotless different-net T-event(s) survive stub planning — this "
            f"sheet would draw two nets as one conductor: {det}")
    # A SAME-net T with no dot is not a lie, but it is unreadable: the reader
    # cannot tell it from the different-net case, which is the one that matters.
    # Here the dot is the truth (both sides are one net either way), so it is
    # added rather than the ink being dropped.
    for _i, _j, _p in same_te:
        junctions = junctions | {key(_p)}

    # ================================================================= emit
    root_uuid = _u()
    body, labels, wires, juncs = [], [], [], []
    pwr = [0]
    for comp in placed:
        b = _emit_layout_component(comp, project, root_uuid, flag_host, pwr,
                                   comp_by_ref, prop_rows_by_ref[comp["refdes"]])
        body.extend(b)
    for net, x, y, side in emit_labels:
        ang, just = LABEL_ANG_JUST[side]
        labels.append(
            f'  (global_label "{net}" (shape passive) (at {x:.3f} {y:.3f} {ang})'
            f' (fields_autoplaced) (effects (font (size 1.27 1.27)) (justify {just}))'
            f' (uuid "{_u()}"))')
    for a, b, _net in segs:
        wires.append(f'  (wire (pts (xy {a[0]:.3f} {a[1]:.3f}) (xy {b[0]:.3f} {b[1]:.3f}))'
                     f' (stroke (width 0) (type default)) (uuid "{_u()}"))')
    seg_endpts = set()
    for a, b, _net in segs:
        seg_endpts.add(key(a))
        seg_endpts.add(key(b))
    for (jx, jy) in sorted(junctions):
        if (jx, jy) in seg_endpts:   # drop junctions orphaned by wire pruning
            juncs.append(f'  (junction (at {jx:.3f} {jy:.3f}) (diameter 0) (color 0 0 0 0)'
                         f' (uuid "{_u()}"))')

    pw = round(_rhu((maxx - minx) * L_S + 2 * L_M + 40, L_G), 2)
    ph = round(_rhu((maxy - miny) * L_S + 2 * L_M + 20, L_G), 2)
    sch = [
        '(kicad_sch (version 20230121) (generator circuit_json_to_kicad_sch)',
        f'  (uuid "{root_uuid}")',
        f'  (paper "User" {pw:.2f} {ph:.2f})',
        f'  (title_block (title "{title}") (date "{date}") (rev "{rev}")',
        '  )',
        '  (lib_symbols',
    ]
    sch.extend(lib_syms.values())
    sch.append('  )')
    sch.extend(labels)
    sch.extend(wires)
    sch.extend(juncs)
    sch.extend(body)
    sch.append('  (sheet_instances (path "/" (page "1")))')
    sch.append(')')
    content = "\n".join(sch)
    assert content.count("(") == content.count(")"), \
        (content.count("("), content.count(")"))
    stats = {"wires": len(segs), "labels": len(emit_labels),
             "tsc_labels": len(emit_labels) - safety, "safety_labels": safety,
             "junctions": len(juncs), "dropped_segs": dropped,
             "pruned_segs": pruned, "moved_labels": moved,
             "stub_segs": len(stubs), "moved_props": prop_moved,
             "labels_on_wire": on_wire}
    return content, components, stats


def comp_pin_net(comp_by_ref, refdes, pad):
    c = comp_by_ref.get(refdes)
    if not c:
        return None
    for p, _pn, net in c["pins"]:
        if p == pad:
            return net
    return None


def attached_glyph_boxes(pins, tips, sides, nets, flag_pad=None):
    """Sheet-space bboxes of the power glyphs a component's OWN pins carry.

    A GND pin gets an `elt:GND` at its tip, rotated by GND_ANG[side] so the
    triangle hangs AWAY from the body; the PWR_FLAG host additionally gets a
    flag, always emitted at angle 0 (it points UP on the sheet at every pin
    side, so it is NOT symmetric with the ground symbol and gets its own box).
    """
    pw = power_syms()
    out = []
    for pad in pins:
        if nets.get(pad) != "GND":
            continue
        ex, ey = tips[pad]
        out.append(glyph_box(pw["GND"], ex, ey, GND_ANG[sides[pad]]))
        if pad == flag_pad:
            out.append(glyph_box(pw["PWR_FLAG"], ex, ey, 0))
    return out


def _emit_layout_component(comp, project, root_uuid, flag_host, pwr, comp_by_ref,
                           rows):
    """Emit one symbol instance at its tscircuit center + the per-pin GND power
    symbols / no_connect flags (nets are carried by wires + labels).

    `rows` is the (reference_y, value_y) pair `convert_layout` already resolved
    — ONE home, so the de-collision search and the emitter cannot disagree
    about where a property text is."""
    ix, iy = comp["inst"]
    (rx, ry), (vx, vy) = rows
    in_bom = "no" if comp["is_tp"] else "yes"
    out = [
        f'  (symbol (lib_id "{LIB}:{comp["sym"]}") (at {ix:.3f} {iy:.3f} 0) (unit 1)'
        f' (in_bom {in_bom}) (on_board yes) (dnp no) (uuid "{_u()}")\n'
        f'    (property "Reference" "{comp["refdes"]}" (at {rx:.3f} {ry:.3f} 0)'
        f' (effects (font (size 1.27 1.27))))\n'
        f'    (property "Value" "{comp["value"]}" (at {vx:.3f} {vy:.3f} 0)'
        f' (effects (font (size 1.27 1.27))))\n'
        f'    (property "Footprint" "{comp["fpid"]}" (at {ix:.3f} {iy:.3f} 0)'
        f' (effects (font (size 1.27 1.27)) hide))\n'
        + "\n".join(f'    (pin "{num}" (uuid "{_u()}"))'
                    for num, _pn, _lx, _ly, _a, _l in comp["pins_geo"])
        + f'\n    (instances (project "{project}" (path "/{root_uuid}"'
        f' (reference "{comp["refdes"]}") (unit 1))))\n  )'
    ]
    # GND power symbols + NC flags at their true KiCad pin tips (T(port) sheet
    # coords — NOT inst+local, which is in the flipped lib-symbol space)
    for num, _pn, _lx, _ly, _ang, _length in comp["pins_geo"]:
        net = comp_pin_net(comp_by_ref, comp["refdes"], num)
        ex, ey = comp["tips"][num]
        side = comp["sides"][num]
        if net is None:
            out.append(f'  (no_connect (at {ex:.3f} {ey:.3f}) (uuid "{_u()}"))')
        elif net == "GND":
            pwr[0] += 1
            pang = GND_ANG[side]
            out.append(emit_power(project, root_uuid, "GND",
                                  f'#PWR{pwr[0]:02d}', "GND", ex, ey, pang))
            if flag_host == (comp["refdes"], num):
                out.append(emit_power(project, root_uuid, "PWR_FLAG",
                                      "#FLG01", "PWR_FLAG", ex, ey, 0))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("circuit_json")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--project", default=None)
    ap.add_argument("--title", default=None)
    ap.add_argument("--rev", default="dev")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--parts-dir", default=None,
                    help="02_parts/ dir for per-board FPID overrides "
                         "(default: auto-discover next to the project)")
    ap.add_argument("--net-aliases", default=None,
                    help="net_aliases.txt for names the strip-N convention misses "
                         "(default: auto-discover 03_tscircuit/net_aliases.txt)")
    ap.add_argument("--mode", choices=["layout", "grid"], default="layout",
                    help="layout (default, ADR-0002 Phase A): consume tscircuit's "
                         "schematic layout -> a WIRED, readable sheet. grid: v1's "
                         "one-label-per-pin fallback. layout auto-falls-back to "
                         "grid if the trace geometry can't import without a short.")
    a = ap.parse_args()
    project = a.project or os.path.splitext(os.path.basename(a.out))[0]
    title = a.title or project

    parts_dir = a.parts_dir or _discover_up(a.circuit_json, ["02_parts"], True)
    alias_path = a.net_aliases or _discover_up(a.circuit_json, ["net_aliases.txt"], False)
    overrides = load_part_overrides(parts_dir)
    ties = load_part_ties(parts_dir)
    aliases = load_aliases(alias_path)

    stats = None
    mode = a.mode
    if mode == "layout":
        try:
            content, comps, stats = convert_layout(
                a.circuit_json, project, title, a.rev, a.date, aliases, overrides,
                ties)
        except LayoutFallback as e:
            print(f"LAYOUT FALLBACK -> grid for {os.path.basename(a.out)}: {e}",
                  file=sys.stderr)
            mode = "grid"
        except LabelPlacementError as e:
            # NOT a fallback (canon S11): answering "this label cannot be placed
            # legibly" with a different sheet is not an answer. Fail, name it,
            # and write nothing.
            print(f"LABEL PLACEMENT FAILED for {os.path.basename(a.out)}: {e}",
                  file=sys.stderr)
            return 3
    if mode == "grid":
        content, comps = convert(a.circuit_json, project, title, a.rev, a.date,
                                 aliases, overrides, ties)

    # ---- canon S12, asked of the FINISHED SHEET TEXT and asked in EVERY mode.
    # The in-flight check above runs on the emitter's own segment list, which is
    # the emitter grading itself (canon M1). This one re-reads the s-expression
    # that is about to be written, attributes nets the way a reader does — by
    # the label plates a connected run of ink carries — and is the only check
    # here that the grid path passes through too.
    #
    # HARD, and never a fallback: answering "this sheet draws two nets as one
    # conductor" with a different sheet is what `LayoutFallback` is for, and by
    # this point the fallback has already been taken. Nothing is written.
    bad = sheet_wire_ambiguity(content)
    if bad:
        print(f"WIRE AMBIGUITY (S12) in {os.path.basename(a.out)} "
              f"[MODE={mode}]: {len(bad)} place(s) draw two nets as one "
              f"conductor; nothing written", file=sys.stderr)
        for line in bad[:12]:
            print(f"  {line}", file=sys.stderr)
        return 4

    with open(a.out, "w") as f:
        f.write(content + "\n")
    npins = sum(len(c["pins"]) for c in comps)
    nfp = sum(1 for c in comps if c["fpid"])
    if stats is not None:
        print(f"wrote {a.out} [MODE=layout, WIRED]: {len(comps)} components "
              f"({nfp} with FPID), {npins} pins; {stats['wires']} wires, "
              f"{stats['tsc_labels']} tscircuit labels + {stats['safety_labels']} "
              f"safety labels, {stats['junctions']} junctions "
              f"({stats['dropped_segs']} segs dropped as cross-net); "
              f"de-collision moved {stats['moved_labels']} of "
              f"{stats['labels']} labels on {stats['stub_segs']} stub segs, "
              f"{stats['moved_props']} property rows")
        if stats["labels_on_wire"]:
            # NAMED, never counted-and-summarised: this is the residue S-OCCL
            # will report, and the operator has to be able to find it on the
            # sheet without re-deriving it.
            print(f"  {len(stats['labels_on_wire'])} plate(s) left lying on a "
                  f"conductor — no offset in the search clears them and the "
                  f"sheet's own layout is the fix: "
                  f"{', '.join(stats['labels_on_wire'])}")
    else:
        print(f"wrote {a.out} [MODE=grid, label-glue fallback]: {len(comps)} "
              f"components ({nfp} with FPID), {npins} pins")
    print(f"  overrides: {len(overrides)} keys from {parts_dir or '(none)'}; "
          f"aliases: {len(aliases)} from {alias_path or '(none)'}; "
          f"tie-parts: {len(ties)} keys")
    return 0


if __name__ == "__main__":
    sys.exit(main())
