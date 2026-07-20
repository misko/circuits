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
     `tscircuit/net_aliases.txt` (auto-discovered) covers anything the convention
     misses.
  2. FOOTPRINT FPIDs. Each symbol's Footprint field is filled from a baked-in
     COMMODITY token->FPID map (circuit.json class-disambiguates: `res0603` vs
     `0603`) with a per-board override seeded from `02_parts/*/part.yaml`
     (MPN/LCSC -> footprint, auto-discovered) that WINS for specialty parts.
  3. NO MPN FIELD (KiCad footprints carry none -> footprint_symbol_field_mismatch).
  4. TP BOM ATTRS. Test-point symbols are `in_bom no` (matching the KiCad
     TestPoint footprint) with a concise `TP` Value that won't clip the board edge.
Proven: cook-loadcell drives the whole backend to DRC 0/0/0 + board parity 0 from
this output ALONE (projects/cook-loadcell/tscircuit/backend_proof/build_from_tsx.sh).

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
    """Optional per-board `tscircuit/net_aliases.txt`: one `TSNAME CANONICAL`
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
def load_model(path, aliases=None, overrides=None):
    """Parse circuit.json -> per-component ordered (padname, portname, net) plus
    metadata. Returns (components, flag_host) where components is a list of dicts
    in refdes order. flag_host is (refdes, padname) of the GND pin to carry the
    single PWR_FLAG, or None.

    Net names are CANONICALIZED (`canon_net`) and each component carries a
    resolved KiCad FPID (`fpid`) so the emitted sheet is backend-ready with no
    downstream adapter."""
    aliases = aliases or {}
    overrides = overrides or {}
    d = json.load(open(path))
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

    components = []
    for cid, c in comps.items():
        plist = ports_by_comp.get(cid, [])
        if not plist:
            continue  # non-electrical (e.g. a mounting-hole <chip> with no pads)
        pins = {}  # padname -> {"port": portname, "net": net}
        for p in plist:
            pad = pad_name(p)
            net = portnet[p['source_port_id']]
            if pad not in pins:
                pins[pad] = {"port": p.get('name') or pad, "net": net}
            elif pins[pad]["net"] is None and net is not None:
                pins[pad]["net"] = net  # a connected duplicate wins over an NC one
        ordered = sorted(pins.items(), key=lambda kv: natkey(kv[0]))
        refdes = c['name']
        is_tp = c.get('ftype') == 'simple_test_point' or refdes.startswith('TP')
        codes = [code for v in (c.get('supplier_part_numbers') or {}).values()
                 for code in (v or [])]
        components.append({
            "refdes": refdes,
            # a test point's tscircuit default Value (`simple_test_point`, 18ch)
            # renders as footprint silk clipped by the board edge -> concise "TP".
            "value": "TP" if is_tp else comp_value(c),
            "is_tp": is_tp,
            "fpid": resolve_fpid(tok_by_comp.get(cid), codes, overrides),
            "pins": [(pad, v["port"], v["net"]) for pad, v in ordered],
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
        f'  (symbol (lib_id "{LIB}:{sym}") (at {x:.2f} {y:.2f} {ang}) (unit 1)'
        f' (in_bom no) (on_board yes) (dnp no) (uuid "{_u()}")\n'
        f'    (property "Reference" "{ref}" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))\n'
        f'    (property "Value" "{value}" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))\n'
        f'    (property "Footprint" "" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))\n'
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


def convert(circuit_json, project, title, rev, date, aliases=None, overrides=None):
    components, flag_host = load_model(circuit_json, aliases, overrides)
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
                         "(default: auto-discover tscircuit/net_aliases.txt)")
    a = ap.parse_args()
    project = a.project or os.path.splitext(os.path.basename(a.out))[0]
    title = a.title or project

    parts_dir = a.parts_dir or _discover_up(a.circuit_json, ["02_parts"], True)
    alias_path = a.net_aliases or _discover_up(a.circuit_json, ["net_aliases.txt"], False)
    overrides = load_part_overrides(parts_dir)
    aliases = load_aliases(alias_path)

    content, comps = convert(a.circuit_json, project, title, a.rev, a.date,
                             aliases, overrides)
    with open(a.out, "w") as f:
        f.write(content + "\n")
    npins = sum(len(c["pins"]) for c in comps)
    nfp = sum(1 for c in comps if c["fpid"])
    print(f"wrote {a.out}: {len(comps)} components ({nfp} with FPID), {npins} pins "
          f"(unique symbols, annotated, canonical nets, net-glue global labels)")
    print(f"  overrides: {len(overrides)} keys from {parts_dir or '(none)'}; "
          f"aliases: {len(aliases)} from {alias_path or '(none)'}")


if __name__ == "__main__":
    main()
