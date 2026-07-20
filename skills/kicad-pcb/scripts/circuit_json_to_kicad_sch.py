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


def _u():
    return str(uuid.uuid4())


def snap(v):
    return round(v / GRID) * GRID


def natkey(s):
    return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', str(s))]


# ------------------------------------------------------------------ model
def load_model(path):
    """Parse circuit.json -> per-component ordered (padname, portname, net) plus
    metadata. Returns (components, flag_host) where components is a list of dicts
    in refdes order. flag_host is (refdes, padname) of the GND pin to carry the
    single PWR_FLAG, or None."""
    d = json.load(open(path))
    comps = {e['source_component_id']: e for e in d
             if e.get('type') == 'source_component'}
    ports = [e for e in d if e.get('type') == 'source_port']
    port_by_id = {p['source_port_id']: p for p in ports}

    # net-key -> net name (first wins; ids are stable within a build)
    key2net = {}
    for e in d:
        if e.get('type') == 'source_net':
            key2net.setdefault(e['subcircuit_connectivity_map_key'], e['name'])

    # base net per port via its connectivity key
    portnet = {p['source_port_id']: key2net.get(p.get('subcircuit_connectivity_map_key'))
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
        components.append({
            "refdes": c['name'],
            "value": comp_value(c),
            "mpn": comp_mpn(c),
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
    body = [
        f'  (symbol (lib_id "{LIB}:{comp["sym"]}") (at {cx:.2f} {cy:.2f} 0) (unit 1)'
        f' (in_bom yes) (on_board yes) (dnp no) (uuid "{_u()}")\n'
        f'    (property "Reference" "{comp["refdes"]}" (at {cx:.2f} {ry:.2f} 0)'
        f' (effects (font (size 1.27 1.27))))\n'
        f'    (property "Value" "{comp["value"]}" (at {cx:.2f} {vy:.2f} 0)'
        f' (effects (font (size 1.27 1.27))))\n'
        f'    (property "Footprint" "" (at {cx:.2f} {cy:.2f} 0) (effects (font (size 1.27 1.27)) hide))\n'
        + (f'    (property "MPN" "{comp["mpn"]}" (at {cx:.2f} {cy:.2f} 0) (effects (font (size 1.0 1.0)) hide))\n'
           if comp["mpn"] else "")
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


def convert(circuit_json, project, title, rev, date):
    components, flag_host = load_model(circuit_json)
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
    a = ap.parse_args()
    project = a.project or os.path.splitext(os.path.basename(a.out))[0]
    title = a.title or project
    content, comps = convert(a.circuit_json, project, title, a.rev, a.date)
    with open(a.out, "w") as f:
        f.write(content + "\n")
    npins = sum(len(c["pins"]) for c in comps)
    print(f"wrote {a.out}: {len(comps)} components, {npins} pins "
          f"(unique symbols, annotated, net-glue global labels)")


if __name__ == "__main__":
    main()
