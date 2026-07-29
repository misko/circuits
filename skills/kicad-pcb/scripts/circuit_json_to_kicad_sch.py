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
    ry, vy = cy - h / 2 - 1.6, cy + h / 2 + 1.8
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

    # ---- candidate labels from schematic_net_label (GND excluded)
    cand_labels = []            # (net, x, y, ang, just)
    for n in snlabel:
        net = canon_net(n['text'], aliases)
        if net is None or net == "GND":
            continue
        x, y = T(n['anchor_position']['x'], n['anchor_position']['y'])
        side = n.get('anchor_side') or 'left'
        ang, just = {'left': (180, 'right'), 'right': (0, 'left'),
                     'top': (90, 'left'), 'bottom': (270, 'left')}.get(side, (0, 'left'))
        cand_labels.append((net, x, y, ang, just))

    # ---- prune dangling wires: iteratively drop any segment with a FREE end
    # (an endpoint not on a pin tip / junction / net label and not shared with
    # another kept segment). A free wire end is a KiCad `wire_dangling` ERC
    # ERROR — a trace stub whose far end reached nothing after import. Peeling
    # them never drops connectivity a pin needs (the pin keeps its GND symbol /
    # net label / other wires; the self-healing pass still names every pin).
    anchors = set(tip_net.keys()) | set(junctions)
    anchors |= {key((x, y)) for (_n, x, y, _a, _j) in cand_labels}
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
    for net, x, y, _a, _j in cand_labels:
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
    for net, x, y, _a, _j in cand_labels:
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
    for net, x, y, ang, just in cand_labels:
        r = uf.find(key((x, y)))
        if r in root_pin_nets and net in root_pin_nets[r]:
            emit_labels.append((net, x, y, ang, just))
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
        side = pin_side[(refdes, pad)]
        ang, just = {'left': (180, 'right'), 'right': (0, 'left'),
                     'top': (90, 'left'), 'bottom': (270, 'left')}.get(side, (0, 'left'))
        emit_labels.append((net, tip[0], tip[1], ang, just))
        covered.add(r)
        safety += 1

    # ================================================================= emit
    root_uuid = _u()
    body, labels, wires, juncs = [], [], [], []
    pwr = [0]
    for comp in placed:
        b = _emit_layout_component(comp, project, root_uuid, flag_host, pwr,
                                   comp_by_ref)
        body.extend(b)
    for net, x, y, ang, just in emit_labels:
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
             "junctions": len(juncs), "dropped_segs": dropped, "pruned_segs": pruned}
    return content, components, stats


def comp_pin_net(comp_by_ref, refdes, pad):
    c = comp_by_ref.get(refdes)
    if not c:
        return None
    for p, _pn, net in c["pins"]:
        if p == pad:
            return net
    return None


def _emit_layout_component(comp, project, root_uuid, flag_host, pwr, comp_by_ref):
    """Emit one symbol instance at its tscircuit center + the per-pin GND power
    symbols / no_connect flags (nets are carried by wires + labels)."""
    ix, iy = comp["inst"]
    ry = iy - comp["h"] / 2 - 2.2
    vy = iy + comp["h"] / 2 + 2.2
    in_bom = "no" if comp["is_tp"] else "yes"
    out = [
        f'  (symbol (lib_id "{LIB}:{comp["sym"]}") (at {ix:.3f} {iy:.3f} 0) (unit 1)'
        f' (in_bom {in_bom}) (on_board yes) (dnp no) (uuid "{_u()}")\n'
        f'    (property "Reference" "{comp["refdes"]}" (at {ix:.3f} {ry:.3f} 0)'
        f' (effects (font (size 1.27 1.27))))\n'
        f'    (property "Value" "{comp["value"]}" (at {ix:.3f} {vy:.3f} 0)'
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
            pang = {'left': 270, 'right': 90, 'top': 0, 'bottom': 180}[side]
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
    if mode == "grid":
        content, comps = convert(a.circuit_json, project, title, a.rev, a.date,
                                 aliases, overrides, ties)
    with open(a.out, "w") as f:
        f.write(content + "\n")
    npins = sum(len(c["pins"]) for c in comps)
    nfp = sum(1 for c in comps if c["fpid"])
    if stats is not None:
        print(f"wrote {a.out} [MODE=layout, WIRED]: {len(comps)} components "
              f"({nfp} with FPID), {npins} pins; {stats['wires']} wires, "
              f"{stats['tsc_labels']} tscircuit labels + {stats['safety_labels']} "
              f"safety labels, {stats['junctions']} junctions "
              f"({stats['dropped_segs']} segs dropped as cross-net)")
    else:
        print(f"wrote {a.out} [MODE=grid, label-glue fallback]: {len(comps)} "
              f"components ({nfp} with FPID), {npins} pins")
    print(f"  overrides: {len(overrides)} keys from {parts_dir or '(none)'}; "
          f"aliases: {len(aliases)} from {alias_path or '(none)'}; "
          f"tie-parts: {len(ties)} keys")


if __name__ == "__main__":
    main()
