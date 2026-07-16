#!/usr/bin/env python3
"""schwriter — declarative KiCad schematic writer (label-only connectivity).

Paradigm (see skills/kicad-pcb/references/schematic-generation.md):
one Python component/net table is the single source of truth. This module
turns that table into a `.kicad_sch` (KiCad 7 s-expr dialect, parsed fine
by KiCad 10) with:

  * embedded `lib_symbols` — one simple box symbol per distinct
    (value, footprint, pinset); pin NUMBER is the PHYSICAL PAD string
    (may be non-numeric: "A1", "SH", "EP"), pin NAME is the function name,
    all pins electrical type "passive" (no ERC noise);
  * connectivity by GLOBAL LABELS ONLY — every pin endpoint carries a
    global label with the pin's net name, placed EXACTLY on the endpoint,
    oriented away from the body. No wires. Graphics can never lie about
    connectivity; the netlist is fully determined by the input table;
  * parts laid out in named sections (grid inside a dashed rectangle with
    a title), generous pitch so refdes/value/label texts don't collide;
  * deterministic UUIDs (uuid5 of ref/pad strings under a fixed
    namespace) so regeneration diffs are reviewable.

Contract: every pin MUST name a net. Deliberate no-connects use the
"NC_<ref>_<pad>" convention. After every regeneration run the netlist
parity check:

    kicad-cli sch export netlist -o out.net board.kicad_sch
    verify_netlist_parity("out.net", sch)   # node-for-node equality

A parse yielding zero nets is a hard error (KiCad 7 -> 10 changed the
netlist to pretty-printed multi-line s-exprs; same-line regexes silently
match nothing — this module uses a real tokenizer).

Library only: NO board-specific data lives here.
"""

import os
import uuid

# Fixed namespace: deterministic UUIDs across regenerations.
_NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

GRID = 1.27          # KiCad wire/pin grid, mm
A3_W, A3_H = 420.0, 297.0
PAPER = {"A4": (297.0, 210.0), "A3": (420.0, 297.0), "A2": (594.0, 420.0)}
_MARGIN_L, _MARGIN_T = 20.0, 20.0     # keep clear of the sheet frame
_MARGIN_R, _MARGIN_B = 20.0, 30.0     # bottom also clears the title block
_FONT = 1.27
_CHAR_W = 1.1        # approx mm per character at 1.27 font


def _uid(*parts):
    return str(uuid.uuid5(_NS, "schwriter:" + ":".join(str(p) for p in parts)))


def _n(x):
    """Format a number the way KiCad likes (no trailing zeros)."""
    s = f"{x:.4f}".rstrip("0").rstrip(".")
    return s if s not in ("-0", "") else "0"


def _q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _snap(x, g=GRID):
    return round(round(x / g) * g, 4)


def _sanitize(name):
    out = "".join(c if (c.isalnum() or c in "._-") else "_" for c in str(name))
    return out or "SYM"


class Part:
    """One physical component.

    pins: ordered dict  pad_number(str) -> {"name": str, "net": str,
                                            "side": "L"|"R" (optional)}
    Pad numbers are PHYSICAL pads from the part datasheet / part.yaml.
    Every pin must carry an explicit net ("NC_<ref>_<pad>" for no-connects).
    """

    def __init__(self, ref, value, footprint_fpid, pins, pin_len=2.54,
                 datasheet=""):
        if not ref:
            raise ValueError("Part needs a non-empty ref")
        if not pins:
            raise ValueError(f"{ref}: a part needs at least one pin")
        self.ref = str(ref)
        self.value = str(value)
        self.footprint = str(footprint_fpid)
        self.pin_len = _snap(pin_len)
        self.datasheet = str(datasheet)
        self.pins = {}
        for pad, info in pins.items():
            pad = str(pad)
            if pad in self.pins:
                raise ValueError(f"{ref}: duplicate pad {pad!r}")
            name = str(info.get("name", pad))
            net = info.get("net")
            if not net:
                raise ValueError(
                    f"{ref} pad {pad}: no net. Nets are explicit; use "
                    f"'NC_{ref}_{pad}' for a deliberate no-connect.")
            side = info.get("side")
            if side not in (None, "L", "R"):
                raise ValueError(f"{ref} pad {pad}: side must be 'L' or 'R'")
            self.pins[pad] = {"name": name, "net": str(net), "side": side}
        self._assign_sides()
        self._geometry()

    def _assign_sides(self):
        pads = list(self.pins)
        unassigned = [p for p in pads if self.pins[p]["side"] is None]
        n_left = sum(1 for p in pads if self.pins[p]["side"] == "L")
        n_right = sum(1 for p in pads if self.pins[p]["side"] == "R")
        # Split unassigned pins: first half left, second half right (DIP-ish),
        # biased to keep the two sides balanced with any explicit pins.
        total = len(pads)
        want_left = max(0, (total + 1) // 2 - n_left)
        for i, p in enumerate(unassigned):
            self.pins[p]["side"] = "L" if i < want_left else "R"
        _ = n_right

    def _geometry(self):
        """Compute body size and per-pin symbol-frame coordinates (+y up)."""
        # KiCad draws the pad number over the pin stem; a long number
        # ("B12", "EP") overruns a short stem and collides with the global
        # label anchored at the tip. Widen the stem to fit the number.
        max_pad_chars = max(len(p) for p in self.pins)
        need = max_pad_chars * _CHAR_W + 1.8
        if need > self.pin_len:
            self.pin_len = _snap(need + GRID / 2, GRID) or GRID
        left = [p for p in self.pins if self.pins[p]["side"] == "L"]
        right = [p for p in self.pins if self.pins[p]["side"] == "R"]
        pitch = 2.54
        rows = max(len(left), len(right), 1)
        name_l = max([len(self.pins[p]["name"]) for p in left] or [0])
        name_r = max([len(self.pins[p]["name"]) for p in right] or [0])
        w = max(10.16, _snap((name_l + name_r) * _CHAR_W + 6.0, 2.54))
        self.body_w = w
        self.body_h = _snap(rows * pitch + 2.54, 2.54)
        self.pin_xy = {}       # pad -> (x, y) of pin ENDPOINT, symbol frame
        for side, pads in (("L", left), ("R", right)):
            n = len(pads)
            for i, p in enumerate(pads):
                y = _snap(((n - 1) / 2.0 - i) * pitch)
                x = -(w / 2 + self.pin_len) if side == "L" else (w / 2 + self.pin_len)
                self.pin_xy[p] = (_snap(x), y)
        # nets that hang off each side (for label clearance)
        self.lbl_l = max([len(self.pins[p]["net"]) for p in left] or [0])
        self.lbl_r = max([len(self.pins[p]["net"]) for p in right] or [0])

    def symbol_key(self):
        pinset = tuple(sorted((p, d["name"], d["side"]) for p, d in self.pins.items()))
        return (self.value, self.footprint, self.pin_len, pinset)

    # full cell the part needs on the sheet (body + pins + labels + refdes)
    def cell_w(self):
        lbl = 3.0 + _CHAR_W * max(self.lbl_l, self.lbl_r)
        return self.body_w + 2 * (self.pin_len + lbl) + 6.0

    def cell_h(self):
        return self.body_h + 12.0     # refdes above + value below


class Schematic:
    def __init__(self, title="", paper="A3"):
        self.title = title
        self.paper = paper
        self.sections = []            # [{"title": str, "parts": [Part], "cols": int|None}]
        self._refs = set()

    def add_section(self, title, cols=None):
        self.sections.append({"title": title, "parts": [], "cols": cols})

    def add_part(self, part, section=None):
        if part.ref in self._refs:
            raise ValueError(f"duplicate ref {part.ref}")
        self._refs.add(part.ref)
        if section is not None:
            for s in self.sections:
                if s["title"] == section:
                    s["parts"].append(part)
                    return
            self.add_section(section)
            self.sections[-1]["parts"].append(part)
        else:
            if not self.sections:
                self.add_section("PARTS")
            self.sections[-1]["parts"].append(part)

    def parts(self):
        return [p for s in self.sections for p in s["parts"]]

    # ---------------- layout ----------------

    def _layout(self):
        """Place sections in a left-to-right flow, parts in a grid inside.
        Returns (placements {ref:(x,y)}, boxes [(x1,y1,x2,y2,title)])."""
        if not self.parts():
            raise ValueError("schematic has zero parts")
        sheet_w, sheet_h = PAPER[self.paper]
        placements, boxes = {}, []
        pad, title_h, gap = 4.0, 6.5, 8.0
        cx, cy, row_h = _MARGIN_L, _MARGIN_T, 0.0
        for sec in self.sections:
            parts = sec["parts"]
            if not parts:
                continue
            n = len(parts)
            cols = sec["cols"] or max(1, int(n ** 0.5 + 0.999))
            cw = max(p.cell_w() for p in parts)
            ch = max(p.cell_h() for p in parts)
            ch = max(ch, 15.0)        # >=10mm passive pitch rule, generous
            rows = (n + cols - 1) // cols
            box_w = cols * cw + 2 * pad
            box_h = rows * ch + 2 * pad + title_h
            if cx + box_w > sheet_w - _MARGIN_R:      # wrap to next band
                cx, cy = _MARGIN_L, cy + row_h + gap
                row_h = 0.0
            if cx + box_w > sheet_w - _MARGIN_R or cy + box_h > sheet_h - _MARGIN_B:
                raise ValueError(
                    f"section {sec['title']!r} ({box_w:.0f}x{box_h:.0f}mm) "
                    f"does not fit on the {self.paper} sheet — split it or "
                    f"reduce cols")
            for i, p in enumerate(parts):
                r, c = divmod(i, cols)
                x = _snap(cx + pad + c * cw + cw / 2, 2.54)
                y = _snap(cy + title_h + pad + r * ch + ch / 2, 2.54)
                placements[p.ref] = (x, y)
            boxes.append((cx, cy, cx + box_w, cy + box_h, sec["title"]))
            cx += box_w + gap
            row_h = max(row_h, box_h)
        return placements, boxes

    # ---------------- emission ----------------

    def _emit_lib_symbol(self, name, proto):
        w2, h2 = proto.body_w / 2, proto.body_h / 2
        out = [f'    (symbol "schwriter:{name}" (pin_names (offset 0.508)) '
               f'(in_bom yes) (on_board yes)']
        props = [("Reference", "U", (0, h2 + 1.27), False),
                 ("Value", proto.value, (0, -h2 - 1.27), False),
                 ("Footprint", proto.footprint, (0, -h2 - 3.81), True),
                 ("Datasheet", proto.datasheet, (0, -h2 - 6.35), True)]
        for i, (k, v, (px, py), hide) in enumerate(props):
            h = " hide" if hide else ""
            out.append(f'      (property {_q(k)} {_q(v)} (at {_n(px)} {_n(py)} 0) '
                       f'(effects (font (size {_FONT} {_FONT})){h}))')
            _ = i
        out.append(f'      (symbol "{name}_0_1"')
        out.append(f'        (rectangle (start {_n(-w2)} {_n(h2)}) '
                   f'(end {_n(w2)} {_n(-h2)}) '
                   f'(stroke (width 0.254) (type default)) '
                   f'(fill (type background)))')
        out.append('      )')
        out.append(f'      (symbol "{name}_1_1"')
        for pad, info in proto.pins.items():
            x, y = proto.pin_xy[pad]
            ang = 0 if info["side"] == "L" else 180
            out.append(
                f'        (pin passive line (at {_n(x)} {_n(y)} {ang}) '
                f'(length {_n(proto.pin_len)})\n'
                f'          (name {_q(info["name"])} (effects (font (size {_FONT} {_FONT}))))\n'
                f'          (number {_q(pad)} (effects (font (size {_FONT} {_FONT}))))\n'
                f'        )')
        out.append('      )')
        out.append('    )')
        return "\n".join(out)

    def _emit_instance(self, part, sym_name, x0, y0, root_uuid):
        w2, h2 = part.body_w / 2, part.body_h / 2
        out = [f'  (symbol (lib_id "schwriter:{sym_name}") '
               f'(at {_n(x0)} {_n(y0)} 0) (unit 1)\n'
               f'    (in_bom yes) (on_board yes) '
               f'(uuid "{_uid("sym", part.ref)}")']
        # property positions are ABSOLUTE sheet coords (sheet +y is DOWN)
        props = [("Reference", part.ref, (x0, y0 - h2 - 2.0), False),
                 ("Value", part.value, (x0, y0 + h2 + 2.0), False),
                 ("Footprint", part.footprint, (x0, y0 + h2 + 4.5), True),
                 ("Datasheet", part.datasheet, (x0, y0 + h2 + 7.0), True)]
        for k, v, (px, py), hide in props:
            h = " hide" if hide else ""
            out.append(f'    (property {_q(k)} {_q(v)} (at {_n(px)} {_n(py)} 0) '
                       f'(effects (font (size {_FONT} {_FONT})){h}))')
        for pad in part.pins:
            out.append(f'    (pin {_q(pad)} (uuid "{_uid("pin", part.ref, pad)}"))')
        out.append(f'    (instances (project "" (path "/{root_uuid}" '
                   f'(reference {_q(part.ref)}) (unit 1))))')
        out.append('  )')
        return "\n".join(out)

    def _emit_label(self, part, pad, x0, y0):
        info = part.pins[pad]
        sx, sy = part.pin_xy[pad]
        # symbol frame +y up -> sheet frame +y down
        x, y = _snap(x0 + sx), _snap(y0 - sy)
        if info["side"] == "L":
            ang, justify = 180, "right"      # text extends leftward, away from body
        else:
            ang, justify = 0, "left"
        u = _uid("lbl", part.ref, pad)
        return (f'  (global_label {_q(info["net"])} (shape input) '
                f'(at {_n(x)} {_n(y)} {ang}) '
                f'(effects (font (size {_FONT} {_FONT})) (justify {justify}))\n'
                f'    (uuid "{u}")\n'
                f'    (property "Intersheetrefs" "${{INTERSHEETREFS}}" '
                f'(at {_n(x)} {_n(y)} 0) '
                f'(effects (font (size {_FONT} {_FONT})) hide))\n'
                f'  )')

    def write(self, path):
        if not self.parts():
            raise ValueError("schematic has zero parts")
        placements, boxes = self._layout()
        # dedupe symbols by (value, footprint, pin_len, pinset)
        sym_names, protos = {}, {}
        for p in self.parts():
            key = p.symbol_key()
            if key not in sym_names:
                base = _sanitize(p.value)[:24]
                sym_names[key] = f"{base}_{_uid('libsym', repr(key))[:8]}"
                protos[key] = p
        root_uuid = _uid("root", self.title)
        out = ['(kicad_sch (version 20230121) (generator schwriter)',
               f'  (uuid "{root_uuid}")', f'  (paper "{self.paper}")']
        if self.title:
            out.append(f'  (title_block (title {_q(self.title[:60])}))')
        out.append('  (lib_symbols')
        for key in sym_names:
            out.append(self._emit_lib_symbol(sym_names[key], protos[key]))
        out.append('  )')
        # section boxes + titles
        for (x1, y1, x2, y2, title) in boxes:
            u = _uid("rect", title, x1, y1)
            out.append(f'  (rectangle (start {_n(x1)} {_n(y1)}) '
                       f'(end {_n(x2)} {_n(y2)})\n'
                       f'    (stroke (width 0.1524) (type dash)) '
                       f'(fill (type none)) (uuid "{u}")\n  )')
            out.append(f'  (text {_q(title)} (at {_n(x1 + 2)} {_n(y1 + 4)} 0)\n'
                       f'    (effects (font (size 2.5 2.5) bold) (justify left))\n'
                       f'    (uuid "{_uid("txt", title, x1, y1)}")\n  )')
        # symbol instances + their pin labels
        for p in self.parts():
            x0, y0 = placements[p.ref]
            out.append(self._emit_instance(p, sym_names[p.symbol_key()], x0, y0,
                                           root_uuid))
            for pad in p.pins:
                out.append(self._emit_label(p, pad, x0, y0))
        out.append('  (sheet_instances (path "/" (page "1")))')
        out.append(')')
        text = "\n".join(out) + "\n"
        with open(path, "w") as f:
            f.write(text)
        return path


# ---------------- verification ----------------

def netmap(schematic):
    """{net: set((ref, pad))} straight from the input table."""
    m = {}
    for p in schematic.parts():
        for pad, info in p.pins.items():
            m.setdefault(info["net"], set()).add((p.ref, pad))
    return m


def _tokenize(text):
    toks, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c in "()":
            toks.append(c)
            i += 1
        elif c == '"':
            j, buf = i + 1, []
            while j < n and text[j] != '"':
                if text[j] == "\\" and j + 1 < n:
                    buf.append(text[j + 1])
                    j += 2
                else:
                    buf.append(text[j])
                    j += 1
            toks.append("".join(buf))
            i = j + 1
        elif c.isspace():
            i += 1
        else:
            j = i
            while j < n and not text[j].isspace() and text[j] not in '()"':
                j += 1
            toks.append(text[i:j])
            i = j
    return toks


def _parse_sexpr(toks, pos=0):
    if toks[pos] != "(":
        return toks[pos], pos + 1
    node, pos = [], pos + 1
    while toks[pos] != ")":
        child, pos = _parse_sexpr(toks, pos)
        node.append(child)
    return node, pos + 1


def parse_kicad_netlist(path):
    """Parse a KiCad netlist export (v7 one-line or v10 pretty-printed —
    real s-expr walk, never a same-line regex). Returns {net: set((ref,pin))}.
    Zero nets parsed is a HARD ERROR (format-drift guard)."""
    with open(path) as f:
        toks = _tokenize(f.read())
    if not toks:
        raise ValueError(f"{path}: empty netlist file")
    tree, _ = _parse_sexpr(toks)
    nets = {}
    def walk(node):
        if not isinstance(node, list) or not node:
            return
        if node[0] == "net":
            name, nodes = None, []
            for item in node[1:]:
                if isinstance(item, list) and item:
                    if item[0] == "name":
                        name = item[1]
                    elif item[0] == "node":
                        ref = pin = None
                        for f2 in item[1:]:
                            if isinstance(f2, list) and len(f2) >= 2:
                                if f2[0] == "ref":
                                    ref = f2[1]
                                elif f2[0] == "pin":
                                    pin = f2[1]
                        nodes.append((ref, pin))
            if name is not None:
                nets.setdefault(name, set()).update(nodes)
        else:
            for item in node[1:]:
                walk(item)
    walk(tree)
    if not nets:
        raise ValueError(f"{path}: parsed ZERO nets — netlist format drift "
                         f"or empty export; refusing to 'pass'")
    return nets


def verify_netlist_parity(kicad_netlist_path, schematic, pin_remap=None):
    """Node-for-node equality of KiCad's exported netlist vs netmap().
    pin_remap: optional {(ref, old_pad): new_pad} for expected package
    changes. Raises AssertionError with a full diff on any mismatch."""
    expected = {}
    for net, nodes in netmap(schematic).items():
        remapped = set()
        for ref, pad in nodes:
            if pin_remap and (ref, pad) in pin_remap:
                pad = pin_remap[(ref, pad)]
            remapped.add((ref, pad))
        expected[net] = remapped
    actual = parse_kicad_netlist(kicad_netlist_path)
    errs = []
    for net in sorted(set(expected) | set(actual)):
        e, a = expected.get(net), actual.get(net)
        if e is None:
            errs.append(f"  net {net!r}: in KiCad netlist only, nodes {sorted(a)}")
        elif a is None:
            errs.append(f"  net {net!r}: missing from KiCad netlist, "
                        f"expected {sorted(e)}")
        elif e != a:
            errs.append(f"  net {net!r}: expected {sorted(e)}, got {sorted(a)}"
                        f" (missing {sorted(e - a)}, extra {sorted(a - e)})")
    if errs:
        raise AssertionError("netlist parity FAILED:\n" + "\n".join(errs))
    n_nodes = sum(len(v) for v in expected.values())
    return f"netlist parity PASS: {len(expected)} nets, {n_nodes} nodes"


if __name__ == "__main__":
    import subprocess, sys, tempfile
    tmp = tempfile.mkdtemp(prefix="schwriter_selftest_")
    sch = Schematic(title="schwriter self-test")
    sch.add_section("POWER IN")
    sch.add_part(Part("J1", "XT60PW-M", "lib:XT60PW-M", {
        "1": {"name": "VBAT+", "net": "VBAT"},
        "2": {"name": "GND", "net": "GND"},
    }), section="POWER IN")
    sch.add_part(Part("F1", "5A_FUSE", "lib:Fuse_1206", {
        "1": {"name": "IN", "net": "VBAT"},
        "2": {"name": "OUT", "net": "VBAT_F"},
    }), section="POWER IN")
    sch.add_section("REGULATOR")
    sch.add_part(Part("U1", "MP2338", "lib:SOIC-8-EP", {
        "1": {"name": "EN", "net": "VBAT_F", "side": "L"},
        "2": {"name": "VIN", "net": "VBAT_F", "side": "L"},
        "3": {"name": "SW", "net": "SW1", "side": "R"},
        "4": {"name": "GND", "net": "GND", "side": "L"},
        "5": {"name": "FB", "net": "FB1", "side": "R"},
        "6": {"name": "BST", "net": "BST1", "side": "R"},
        "7": {"name": "VCC", "net": "VCC_INT", "side": "R"},
        "8": {"name": "NC", "net": "NC_U1_8", "side": "L"},
        "EP": {"name": "EP", "net": "GND", "side": "L"},
    }), section="REGULATOR")
    for i, (net_a, net_b) in enumerate(
            [("SW1", "V5"), ("V5", "GND"), ("FB1", "GND"), ("BST1", "SW1")]):
        sch.add_part(Part(f"C{i+1}" if i != 0 else "L1",
                          "10uF" if i else "4.7uH",
                          "lib:C_0805" if i else "lib:L_5x5",
                          {"1": {"name": "1", "net": net_a},
                           "2": {"name": "2", "net": net_b}}),
                     section="REGULATOR")
    sch.add_section("USB OUT")
    sch.add_part(Part("J2", "USB_C_RECEPT", "lib:USB_C_16P", {
        "A1": {"name": "GND", "net": "GND", "side": "L"},
        "A4": {"name": "VBUS", "net": "V5", "side": "L"},
        "A5": {"name": "CC1", "net": "CC1", "side": "R"},
        "B12": {"name": "GND", "net": "GND", "side": "L"},
        "B5": {"name": "CC2", "net": "CC2", "side": "R"},
        "SH": {"name": "SHIELD", "net": "GND", "side": "L"},
    }), section="USB OUT")
    sch.add_part(Part("R1", "5.1k", "lib:R_0603",
                      {"1": {"name": "1", "net": "CC1"},
                       "2": {"name": "2", "net": "GND"}}), section="USB OUT")
    sch.add_part(Part("R2", "5.1k", "lib:R_0603",
                      {"1": {"name": "1", "net": "CC2"},
                       "2": {"name": "2", "net": "GND"}}), section="USB OUT")

    sch_path = os.path.join(tmp, "selftest.kicad_sch")
    net_path = os.path.join(tmp, "selftest.net")
    svg_dir = os.path.join(tmp, "svg")
    sch.write(sch_path)
    print("wrote", sch_path)
    subprocess.run(["kicad-cli", "sch", "export", "netlist",
                    "-o", net_path, sch_path], check=True)
    print(verify_netlist_parity(net_path, sch))
    subprocess.run(["kicad-cli", "sch", "export", "svg",
                    "-o", svg_dir, sch_path], check=True)
    print("svg exported to", svg_dir)
    sys.exit(0)
