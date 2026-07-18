"""schwriter2 — envelope-driven schematic LAYOUT ENGINE for generated KiCad sheets.

The author declares STRUCTURE only (symbols, cells with nets, regions, rows,
chains); the engine computes every coordinate. Design principle (canon S6 /
S-OCCL): text envelopes are the schematic's courtyards. Every text emitted
(label plates, refs, values, captions, pin stubs/numbers) contributes to a
cell's envelope; ALL positions derive from envelopes, so collisions are
impossible by construction — and an internal S-OCCL gate (the exact model
policy_audit.py uses) asserts zero before the file is written.

Wire tiers:
  T1 auto     — within a row, a right-side pin of cell k facing a left-side
                pin of cell k+1 at the same y with the same net becomes a
                straight tip-to-tip wire; the right cell's label is
                suppressed (exactly ONE label stays per wire — the global
                label is the net glue; suppressing both orphans the wire
                into an auto-named island: 16 parity conflicts, 2026-07-17).
  T2 declared — chain("R23.2", "R26.1") forces adjacency, vertically offsets
                the right cell so the pins align, and wires them (nets must
                already match — a wrong chain is a build error, not a lie).
  T3          — every other connected pin gets a global label at its tip.

Safety invariants enforced in code (each cost hours on 2026-07-17):
  * wire endpoints EXACTLY on pin tips (body edge + 2.54), all on 1.27 grid;
  * no wire span passes over a third pin tip or another wire endpoint at the
    same y (KiCad T-junctions connect);
  * parens balanced; every net keeps >= 1 global label;
  * no_connect flags emitted at every explicit-None pin tip;
  * internal S-OCCL == 0 (plates + ref/value texts, justify-aware, re-parsed
    from the EMITTED text with policy_audit.py's own regex model);
  * regions packed disjoint on the sheet, hard-fail if the paper overflows.

Symbol machinery (lib_symbol grammar, pin maps) is carried over verbatim from
the verified elt generator (KiCad 7 dialect, re-validated on KiCad 10).
"""

import datetime
import math
import os
import re
import subprocess
import uuid

GRID = 1.27
PIN_LEN = 2.54
CH_W, CH_H = 1.05, 2.2      # global-label plate model (policy_audit S-OCCL)
PROP_W = 0.82               # per-char width factor for property texts
CELL_MARGIN = 0.4           # per-side inflation => 0.8mm envelope margin
CELL_GAP = 1.0              # extra gap between adjacent cell envelopes
ROW_GAP = 1.5               # gap between row envelopes
REGION_GAP = 6.0            # gap between packed regions
BOX_MARGIN = 1.5            # section rectangle margin around region bounds
PAPERS = {"A2": (594.0, 420.0), "A3": (420.0, 297.0), "A1": (841.0, 594.0)}


def _u():
    return str(uuid.uuid4())


def snap(v):
    return round(v / GRID) * GRID


def snap_up(v):
    return math.ceil(v / GRID - 1e-9) * GRID


# ------------------------------------------------------------------ symbols
def lib_symbol(name, w, h, pins, ref="U"):
    """Verbatim from the verified elt generator (crowsync provenance)."""
    x0, y0 = -w / 2, -h / 2
    out = [f'    (symbol "elt:{name}" (in_bom yes) (on_board yes)']
    out.append(f'      (property "Reference" "{ref}" (at 0 {h/2+1.27:.2f} 0) (effects (font (size 1.27 1.27))))')
    out.append(f'      (property "Value" "{name}" (at 0 {-h/2-1.27:.2f} 0) (effects (font (size 1.27 1.27))))')
    out.append(f'      (symbol "{name}_0_1"')
    out.append(f'        (rectangle (start {x0:.2f} {y0:.2f}) (end {w/2:.2f} {h/2:.2f})'
               f' (stroke (width 0.254) (type default)) (fill (type background)))')
    out.append("      )")
    out.append(f'      (symbol "{name}_1_1"')
    for num, pname, side, slot in pins:
        y = h / 2 - 2.54 * (slot + 1)
        if side == "L":
            px, ang = x0 - 2.54, 0
        else:
            px, ang = w / 2 + 2.54, 180
        out.append(
            f'        (pin passive line (at {px:.2f} {y:.2f} {ang}) (length 2.54)'
            f' (name "{pname}" (effects (font (size 1.27 1.27))))'
            f' (number "{num}" (effects (font (size 1.27 1.27)))))'
        )
    out.append("      )")
    out.append("    )")
    return "\n".join(out), {num: (side, h / 2 - 2.54 * (slot + 1)) for num, _, side, slot in pins}


class Cell:
    """One part instance: body + pins + nets + text plates = one envelope."""

    def __init__(self, eng, sym, ref, value, nets, caption=None):
        self.eng, self.sym, self.ref, self.value = eng, sym, ref, value
        self.nets, self.caption = dict(nets), caption
        self.pm, self.w, self.h = eng.pinmaps[sym]
        for p in nets:
            assert p in self.pm, f"{ref}: pin {p} not in symbol {sym}"
        assert set(nets) == set(self.pm), (
            f"{ref}: nets dict must cover every pin of {sym} "
            f"(missing {set(self.pm) - set(nets)}, extra {set(nets) - set(self.pm)})")
        self.small = eng.small_syms is None or sym in eng.small_syms
        self.dy = 0.0           # vertical offset within the row (chains)
        self.x = self.y = None  # absolute center, set by layout
        self.suppressed = set()  # pins whose label a wire replaced

    # -- local geometry -------------------------------------------------
    def pin_local(self, pin):
        """(tip_x, y, side) in cell-local coords (y down, center origin)."""
        side, py = self.pm[pin]
        tip = -(self.w / 2 + PIN_LEN) if side == "L" else self.w / 2 + PIN_LEN
        return tip, -py, side

    def _texts(self):
        """(kind, text, ax, ay, size, justify) — the audit's property model."""
        ry, vy = -self.h / 2 - 1.6, self.h / 2 + 1.8
        vsz = 0.9 if self.small else 1.27
        if self.small:
            # ref right-justified at the top-LEFT corner; value left-justified
            # from the body's left edge (S-OCCL fix 2026-07-17: the two text
            # families extend in opposite directions, disjoint by construction)
            out = [("Reference", self.ref, -self.w / 2 - 0.6, ry, 1.0, "right"),
                   ("Value", self.value, -self.w / 2, vy, vsz, "left")]
        else:
            out = [("Reference", self.ref, 0.0, ry, 1.27, None),
                   ("Value", self.value, 0.0, vy, vsz, None)]
        if self.caption:
            out.append(("Caption", self.caption, 0.0, vy + 2.54, 1.27, None))
        return out

    @staticmethod
    def _text_box(text, ax, ay, size, justify):
        wid = len(text) * size * PROP_W
        if justify == "right":
            return (ax - wid, ay - size * 0.9, ax, ay + size * 0.9)
        if justify == "left":
            return (ax, ay - size * 0.9, ax + wid, ay + size * 0.9)
        return (ax - wid / 2, ay - size * 0.9, ax + wid / 2, ay + size * 0.9)

    def boxes(self):
        """Local envelope boxes (body, pin stubs, plates, texts)."""
        out = [(-self.w / 2, -self.h / 2, self.w / 2, self.h / 2)]
        for pin, net in self.nets.items():
            tip, y, side = self.pin_local(pin)
            edge = -self.w / 2 if side == "L" else self.w / 2
            out.append((min(edge, tip) - 0.3, y - 0.9, max(edge, tip) + 0.3, y + 0.9))
            if net is not None and pin not in self.suppressed:
                wl = (len(net) + 2) * CH_W
                if side == "L":
                    out.append((tip - wl, y - CH_H / 2, tip, y + CH_H / 2))
                else:
                    out.append((tip, y - CH_H / 2, tip + wl, y + CH_H / 2))
        for _k, txt, ax, ay, sz, j in self._texts():
            out.append(self._text_box(txt, ax, ay, sz, j))
        return out

    def bbox(self):
        bs = self.boxes()
        return (min(b[0] for b in bs), min(b[1] for b in bs),
                max(b[2] for b in bs), max(b[3] for b in bs))


class Region:
    def __init__(self, title):
        self.title = title
        self.rows = []          # list[list[Cell]]
        self.x = self.y = None  # top-left of content bounds
        self.bounds = None      # absolute (x0,y0,x1,y1) incl. title


class Schematic:
    """Declare symbols, regions, rows, chains; emit() computes the layout."""

    def __init__(self, project, title, paper="A2", comment=None,
                 rev=None, date=None, small_syms=None,
                 sheet_margin=14.0, sheet_reserved_bottom=24.0):
        self.project, self.title, self.paper = project, title, paper
        self.comment = comment
        self.rev = rev or "dev"
        self.date = date or datetime.date.today().isoformat()
        self.symbols, self.pinmaps = {}, {}
        self.small_syms = small_syms  # set of symbol names treated "small"
        self.regions, self.chains = [], []
        self.cells = {}              # ref -> Cell
        self.sym_fp, self.ref_fp = {}, {}
        self.no_bom_syms = set()     # symbols excluded from BOM (parity: TP)
        self.sheet_margin = sheet_margin
        self.sheet_reserved_bottom = sheet_reserved_bottom
        self.wires = []              # absolute (x1, x2, y, net)
        self._root_uuid = str(uuid.uuid4())

    # -- declaration API ------------------------------------------------
    def defsym(self, name, w, h, pins, ref="U"):
        s, pm = lib_symbol(name, w, h, pins, ref)
        self.symbols[name] = s
        self.pinmaps[name] = (pm, w, h)

    def region(self, title):
        self.regions.append(Region(title))
        return self.regions[-1]

    def cell(self, sym, ref, value, nets, caption=None):
        assert ref not in self.cells, f"duplicate ref {ref}"
        c = Cell(self, sym, ref, value, nets, caption)
        self.cells[ref] = c
        return c

    def row(self, *specs):
        """Add a row of cells to the CURRENT region.
        Each spec: (sym, ref, value, nets[, caption]) tuple or a Cell."""
        assert self.regions, "declare a region() before row()"
        cells = []
        for s in specs:
            cells.append(s if isinstance(s, Cell) else self.cell(*s))
        self.regions[-1].rows.append(cells)
        return cells

    def place(self, sym, ref, value, nets, caption=None):
        return self.cell(sym, ref, value, nets, caption)

    def chain(self, a, b):
        """T2: force adjacency + straight wire between 'REF.PIN' endpoints."""
        self.chains.append((a, b))

    # -- helpers --------------------------------------------------------
    @staticmethod
    def _parse(spec):
        ref, pin = spec.split(".", 1)
        return ref, pin

    def _cell_pos_in_rows(self, ref):
        for reg in self.regions:
            for row in reg.rows:
                for i, c in enumerate(row):
                    if c.ref == ref:
                        return row, i
        raise AssertionError(f"chain endpoint {ref} not placed in any row")

    # -- layout ---------------------------------------------------------
    def _resolve_wires(self):
        """Chains (T2) then per-row facing-pin auto wires (T1).
        Returns per-row wire lists [(ci, pinA, cj, pinB, net)]."""
        row_wires = {}          # id(row) -> list
        wired_pins = set()      # (ref, pin)
        # T2 declared chains: adjacency assert + vertical alignment + wire
        for sa, sb in self.chains:
            ra, pa = self._parse(sa)
            rb, pb = self._parse(sb)
            rowA, ia = self._cell_pos_in_rows(ra)
            rowB, ib = self._cell_pos_in_rows(rb)
            assert rowA is rowB and ib == ia + 1, (
                f"chain {sa}->{sb}: cells must be adjacent left-to-right in one row")
            A, B = rowA[ia], rowA[ib]
            na, nb = A.nets[pa], B.nets[pb]
            assert na is not None and na == nb, (
                f"chain {sa}->{sb}: nets differ ({na} vs {nb}) — chains may not re-net")
            _, ya, sidea = A.pin_local(pa)
            _, yb, sideb = B.pin_local(pb)
            assert sidea == "R" and sideb == "L", (
                f"chain {sa}->{sb}: needs a right-side pin facing a left-side pin")
            B.dy = snap(A.dy + ya - yb)
            assert abs((A.dy + ya) - (B.dy + yb)) < 1e-6, \
                f"chain {sa}->{sb}: pin ys not grid-alignable"
            row_wires.setdefault(id(rowA), []).append((ia, pa, ib, pb, na))
            wired_pins.add((ra, pa))
            wired_pins.add((rb, pb))
        # T1 auto: same net, facing sides, same y after offsets
        for reg in self.regions:
            for row in reg.rows:
                for i in range(len(row) - 1):
                    A, B = row[i], row[i + 1]
                    for pa, na in A.nets.items():
                        if na is None or (A.ref, pa) in wired_pins:
                            continue
                        _, ya, sa = A.pin_local(pa)
                        if sa != "R":
                            continue
                        for pb, nb in B.nets.items():
                            if nb != na or (B.ref, pb) in wired_pins:
                                continue
                            _, yb, sb = B.pin_local(pb)
                            if sb != "L" or abs((A.dy + ya) - (B.dy + yb)) > 0.01:
                                continue
                            row_wires.setdefault(id(row), []).append((i, pa, i + 1, pb, na))
                            wired_pins.add((A.ref, pa))
                            wired_pins.add((B.ref, pb))
                            break
        # exactly ONE label per wire: suppress the right cell's plate
        for wl in row_wires.values():
            for (_ia, _pa, ib_, pb_, _n) in wl:
                pass
        for reg in self.regions:
            for row in reg.rows:
                for (_ia, _pa, ib_, pb_, _n) in row_wires.get(id(row), []):
                    row[ib_].suppressed.add(pb_)
        return row_wires

    @staticmethod
    def _inflate(bs, m):
        return [(b[0] - m, b[1] - m, b[2] + m, b[3] + m) for b in bs]

    def _row_layout(self, row, wires):
        """Relative x per cell (cell 0 at 0) from envelope-half pitches."""
        rel = [0.0]
        wired_pairs = {(w[0], w[2]): w for w in wires}
        for i in range(len(row) - 1):
            A, B = row[i], row[i + 1]
            ba = self._inflate(A.boxes(), CELL_MARGIN)
            bb = self._inflate(B.boxes(), CELL_MARGIN)
            need = 0.0
            for a in ba:
                for b in bb:
                    if a[1] + A.dy < b[3] + B.dy and b[1] + B.dy < a[3] + A.dy:
                        need = max(need, a[2] - b[0] + CELL_GAP)
            # wired pair: keep the wire at least one grid long
            w = wired_pairs.get((i, i + 1))
            if w is not None:
                ta, _, _ = A.pin_local(w[1])
                tb, _, _ = B.pin_local(w[3])
                need = max(need, ta - tb + PIN_LEN)
            rel.append(rel[-1] + snap_up(need))
        return rel

    def _layout(self):
        row_wires = self._resolve_wires()
        # per-region relative layout
        for reg in self.regions:
            tw = 1.9 * len(reg.title)
            cursor = 2.0 * 0.9 * 2 + ROW_GAP        # below the title text
            reg._rows_rel = []
            width = tw
            for row in reg.rows:
                rel = self._row_layout(row, row_wires.get(id(row), []))
                bbs = [c.bbox() for c in row]
                miny = min(c.dy + bb[1] for c, bb in zip(row, bbs))
                maxy = max(c.dy + bb[3] for c, bb in zip(row, bbs))
                minx = rel[0] + bbs[0][0]
                maxx = max(r + bb[2] for r, bb in zip(rel, bbs))
                base = snap_up(cursor - miny)
                reg._rows_rel.append((row, rel, minx, base))
                width = max(width, maxx - minx)
                cursor = base + maxy + ROW_GAP
            reg._w, reg._h = width, cursor - ROW_GAP
        # shelf-pack regions on the sheet, declaration order
        pw, ph = PAPERS[self.paper]
        m = self.sheet_margin
        limit_x, limit_y = pw - m, ph - m - self.sheet_reserved_bottom
        cx, cy, shelf_h = m, m, 0.0
        for reg in self.regions:
            if cx > m and cx + reg._w > limit_x:
                cx, cy = m, cy + shelf_h + REGION_GAP
                shelf_h = 0.0
            assert cx + reg._w <= limit_x, (
                f"region '{reg.title}' width {reg._w:.0f} exceeds the {self.paper} sheet")
            assert cy + reg._h <= limit_y, (
                f"sheet overflow: region '{reg.title}' bottom "
                f"{cy + reg._h:.0f} > {limit_y:.0f} on {self.paper}")
            reg.x, reg.y = snap(cx), snap(cy)
            shelf_h = max(shelf_h, reg._h)
            cx += reg._w + REGION_GAP
            # absolute cell centers
            for row, rel, minx, base in reg._rows_rel:
                x0 = snap_up(reg.x - (minx - rel[0]))
                for c, r in zip(row, rel):
                    c.x = snap(x0 + r)
                    c.y = snap(reg.y + base + c.dy)
            reg.bounds = (reg.x, reg.y, reg.x + reg._w, reg.y + reg._h)
        # absolute wires
        for reg in self.regions:
            for row, _rel, _minx, _base in reg._rows_rel:
                for (ia, pa, ib, pb, net) in row_wires.get(id(row), []):
                    A, B = row[ia], row[ib]
                    ta, ya, _ = A.pin_local(pa)
                    tb, yb, _ = B.pin_local(pb)
                    y = A.y + ya
                    assert abs(y - (B.y + yb)) < 1e-6, "wire endpoints y mismatch"
                    self.wires.append((A.x + ta, B.x + tb, y, net))

    # -- safety gates ---------------------------------------------------
    def _check_wires(self):
        tips = []
        for c in self.cells.values():
            if c.x is None:
                continue
            for pin in c.nets:
                tx, ty, _ = c.pin_local(pin)
                tips.append((c.x + tx, c.y + ty, c.ref, pin))
        endpoints = set()
        for (x1, x2, y, _n) in self.wires:
            for v in (x1, x2, y):
                assert abs(v / GRID - round(v / GRID)) < 1e-6, \
                    f"wire coord {v} off the 1.27 grid"
            assert x2 - x1 >= PIN_LEN - 1e-6, f"wire at y={y} too short"
            endpoints.add((round(x1, 2), round(y, 2)))
            endpoints.add((round(x2, 2), round(y, 2)))
        tipset = {(round(x, 2), round(y, 2)) for x, y, _r, _p in tips}
        for ep in endpoints:
            assert ep in tipset, f"wire endpoint {ep} is not on a pin tip"
        for (x1, x2, y, n) in self.wires:
            for (tx, ty, r, p) in tips:
                if abs(ty - y) < 0.01 and x1 + 0.01 < tx < x2 - 0.01:
                    raise AssertionError(
                        f"wire {n} at y={y} passes over pin tip {r}.{p} — T-junction")
            for (ox1, ox2, oy, on) in self.wires:
                if (ox1, ox2, oy) == (x1, x2, y):
                    continue
                if abs(oy - y) < 0.01 and not (ox2 <= x1 + 0.01 or x2 - 0.01 <= ox1):
                    raise AssertionError(
                        f"collinear wire overlap at y={y}: {n} vs {on}")

    @staticmethod
    def _soccl(content):
        """policy_audit.py's exact S-OCCL model, re-parsed from emitted text."""
        items = []
        for m in re.finditer(r'\(global_label "([^"]+)".{0,80}?\(at ([-\d.]+) ([-\d.]+) (\d+)\)', content):
            txt, gx, gy, ang = m.group(1), float(m.group(2)), float(m.group(3)), int(m.group(4))
            wlen = (len(txt) + 2) * CH_W
            if ang == 180:
                items.append((gx - wlen, gy - CH_H / 2, gx, gy + CH_H / 2, f"label {txt}"))
            else:
                items.append((gx, gy - CH_H / 2, gx + wlen, gy + CH_H / 2, f"label {txt}"))
        for im_ in re.finditer(r'\(symbol \(lib_id[^\n]*\n(.{0,1200}?)\(pin ', content, re.S):
            blk = im_.group(1)
            for pm in re.finditer(r'\(property "(Reference|Value)" "([^"]+)" \(at ([-\d.]+) ([-\d.]+) \d+\)\s*\(effects \(font \(size ([\d.]+) [\d.]+\)\)(?: \(justify (\w+)\))?', blk):
                kind, txt = pm.group(1), pm.group(2)
                gx, gy = float(pm.group(3)), float(pm.group(4))
                fs, just = float(pm.group(5)), pm.group(6)
                if "hide" in blk[pm.end():pm.end() + 60]:
                    continue
                w = len(txt) * fs * PROP_W
                if just == "right":
                    box = (gx - w, gy - fs * 0.9, gx, gy + fs * 0.9)
                elif just == "left":
                    box = (gx, gy - fs * 0.9, gx + w, gy + fs * 0.9)
                else:
                    box = (gx - w / 2, gy - fs * 0.9, gx + w / 2, gy + fs * 0.9)
                items.append(box + (f"{kind} {txt}",))
        occl = []
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                a, b = items[i], items[j]
                if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                    occl.append(f"{a[4]} x {b[4]}")
        return occl

    # -- emission -------------------------------------------------------
    def _emit_cell(self, c):
        x, y, w, h = c.x, c.y, c.w, c.h
        ry, vy = y - h / 2 - 1.6, y + h / 2 + 1.8
        vsz = 0.9 if c.small else 1.27
        fp = self.ref_fp.get(c.ref, self.sym_fp.get(c.sym, ""))
        in_bom = "no" if c.sym in self.no_bom_syms else "yes"
        body = [
            f'  (symbol (lib_id "elt:{c.sym}") (at {x:.2f} {y:.2f} 0) (unit 1)'
            f' (in_bom {in_bom}) (on_board yes) (dnp no) (uuid "{_u()}")\n'
            + (f'    (property "Reference" "{c.ref}" (at {x - w/2 - 0.6:.2f} {ry:.2f} 0)'
               f' (effects (font (size 1.0 1.0)) (justify right)))\n' if c.small else
               f'    (property "Reference" "{c.ref}" (at {x:.2f} {ry:.2f} 0) (effects (font (size 1.27 1.27))))\n')
            + (f'    (property "Value" "{c.value}" (at {x - w/2:.2f} {vy:.2f} 0)'
               f' (effects (font (size {vsz} {vsz})) (justify left)))\n' if c.small else
               f'    (property "Value" "{c.value}" (at {x:.2f} {vy:.2f} 0) (effects (font (size {vsz} {vsz}))))\n')
            + f'    (property "Footprint" "{fp}" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))\n'
            + "\n".join(f'    (pin "{n}" (uuid "{_u()}"))' for n in c.pm)
            + f'\n    (instances (project "{self.project}" (path "/{self._root_uuid}" (reference "{c.ref}") (unit 1))))\n  )'
        ]
        labels = []
        for pin, net in c.nets.items():
            tip, py, side = c.pin_local(pin)
            ex, ey = x + tip, y + py
            if net is None:
                body.append(f'  (no_connect (at {ex:.2f} {ey:.2f}) (uuid "{_u()}"))')
                continue
            if pin in c.suppressed:
                continue
            ang, just = (180, "right") if side == "L" else (0, "left")
            labels.append(
                f'  (global_label "{net}" (shape passive) (at {ex:.2f} {ey:.2f} {ang})'
                f' (fields_autoplaced) (effects (font (size 1.27 1.27)) (justify {just})) (uuid "{_u()}"))')
        if c.caption:
            body.append(f'  (text "{c.caption}" (at {x:.2f} {vy + 2.54:.2f} 0)'
                        f' (effects (font (size 1.27 1.27))) (uuid "{_u()}"))')
        return body, labels

    def emit(self):
        """Layout + gates; returns the .kicad_sch content string."""
        self._layout()
        self._check_wires()
        body, labels = [], []
        for reg in self.regions:
            body.append(f'  (text "{reg.title}" (at {reg.x:.2f} {reg.y + 1.8:.2f} 0)'
                        f' (effects (font (size 2.0 2.0) bold) (justify left)) (uuid "{_u()}"))')
        for c in self.cells.values():
            assert c.x is not None, f"{c.ref} declared but never placed in a row"
            b, l = self._emit_cell(c)
            body.extend(b)
            labels.extend(l)
        for (x1, x2, y, _n) in self.wires:
            body.append(f'  (wire (pts (xy {x1:.2f} {y:.2f}) (xy {x2:.2f} {y:.2f}))'
                        f' (stroke (width 0)) (uuid "{_u()}"))')
        # every net keeps >= 1 global label (net glue for wires; parity)
        nets = {n for c in self.cells.values() for n in c.nets.values() if n}
        labeled = {m.group(1) for m in re.finditer(r'\(global_label "([^"]+)"', "\n".join(labels))}
        assert nets <= labeled, f"nets without any label: {sorted(nets - labeled)}"
        rects = []
        for reg in self.regions:
            x0, y0, x1, y1 = reg.bounds
            rects.append(
                f'  (rectangle (start {x0 - BOX_MARGIN:.2f} {y0 - BOX_MARGIN:.2f})'
                f' (end {x1 + BOX_MARGIN:.2f} {y1 + BOX_MARGIN:.2f})'
                f' (stroke (width 0.35) (type solid) (color 120 120 130 0.7))'
                f' (fill (type none)) (uuid "{_u()}"))')
        sch = ['(kicad_sch (version 20230121) (generator schwriter2)',
               f'  (uuid "{self._root_uuid}")',
               f'  (paper "{self.paper}")',
               f'  (title_block (title "{self.title}") (date "{self.date}") (rev "{self.rev}")']
        if self.comment:
            sch.append(f'    (comment 1 "{self.comment}"))')
        else:
            sch.append('  )')
        sch.append("  (lib_symbols")
        sch.extend(self.symbols.values())
        sch.append("  )")
        sch.extend(labels)
        sch.extend(body)
        sch.extend(rects)
        sch.append('  (sheet_instances (path "/" (page "1")))')
        sch.append(")")
        content = "\n".join(sch)
        assert content.count("(") == content.count(")"), (
            content.count("("), content.count(")"))
        occl = self._soccl(content)
        assert not occl, f"internal S-OCCL: {len(occl)} text occlusions: {occl[:8]}"
        return content

    # -- side files ------------------------------------------------------
    def write_symbol_lib(self, path):
        lib = ['(kicad_symbol_lib (version 20231120) (generator schwriter2)']
        for name, s in self.symbols.items():
            lib.append(s.replace(f'(symbol "elt:{name}"', f'(symbol "{name}"', 1))
        lib.append(')')
        path.write_text("\n".join(lib) + "\n")

    @staticmethod
    def sym_lib_table(libname, uri):
        return ('(sym_lib_table\n  (version 7)\n'
                f'  (lib (name "{libname}")(type "KiCad")(uri "{uri}")(options "")(descr "project symbols"))\n)\n')

    def fp_lib_table(self, extra_libs=None, std="/usr/share/kicad/footprints"):
        """extra_libs: {libname: uri} for project-vendored footprint libs."""
        extra_libs = extra_libs or {}
        libs = sorted({fp.split(":")[0] for fp in self.sym_fp.values()}
                      | set(self.ref_fp and {fp.split(":")[0] for fp in self.ref_fp.values()} or set())
                      | {"MountingHole"} | set(extra_libs))
        rows = ['(fp_lib_table', '  (version 7)']
        for l in libs:
            if l in extra_libs:
                rows.append(f'  (lib (name "{l}")(type "KiCad")(uri "{extra_libs[l]}")(options "")(descr "project footprints"))')
            else:
                rows.append(f'  (lib (name "{l}")(type "KiCad")(uri "{std}/{l}.pretty")(options "")(descr "system"))')
        rows.append(')')
        return "\n".join(rows) + "\n"

    @staticmethod
    def rev_from_git(cwd, env_var, tag_glob):
        try:
            return (os.environ.get(env_var)
                    or subprocess.run(["git", "describe", "--tags", "--match",
                                       tag_glob, "--abbrev=0"],
                                      capture_output=True, text=True,
                                      cwd=str(cwd)).stdout.strip()
                    or "dev")
        except Exception:
            return "dev"

    # -- reporting -------------------------------------------------------
    def net_map(self):
        out = {}
        for c in self.cells.values():
            for pin, net in c.nets.items():
                if net is not None:
                    out.setdefault(net, set()).add((c.ref, pin))
        return out
