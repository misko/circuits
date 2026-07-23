"""Exact-collision PCB editing toolkit (import as a library, or vendor).

Every function that ADDS copper verifies it against KiCad's own effective
shapes first — a wrong edit is a refusal, not a DRC surprise. Distilled
from the SPF power-board endgame (2026-07), where circular pad
approximations and unverified stubs both produced real crossings.

Usage (KiCad-bundled python):
    import os, sys
    import pcbnew
    sys.path.insert(0, os.path.expanduser("~/.claude/skills/kicad-pcb/scripts"))
    from pcb_toolkit import Toolkit
    tk = Toolkit(pcbnew.LoadBoard("board.kicad_pcb"), clearance_mm=0.11)
    tk.joinpath("BST_B", (83.35, 92.75), (85.53, 92.03), width=0.2)
    tk.board.Save(...)

KNOWN GAPS (deliberate — cover them with the process): collides() checks
tracks, vias, flashed pads, and drilled-pad HOLES, but NOT zone fills,
board edges, or rule areas. Zones are handled by refill-after-edit; edge
and everything else by the classified-DRC green check that is MANDATORY
after every edit, including your own fixes. verified_astar treats both
endpoints as F.Cu — pass B.Cu-side points through a via first. Save/reload
after any Remove/Delete before further work.
"""
import math
import heapq

import pcbnew

MM = pcbnew.ToMM


def _vec(x, y):
    return pcbnew.VECTOR2I_MM(float(x), float(y))


class Toolkit:
    def __init__(self, board, clearance_mm=0.11):
        self.board = board
        self.clr = pcbnew.FromMM(clearance_mm)
        self._index = None
        self._index_sig = None

    # ------------------------------------------------------------ bbox index
    # A conservative bbox prefilter makes collides() ~100x faster on a full
    # board (exactness unchanged — bbox-rejected items cannot collide). The
    # index AUTO-REBUILDS when the board's track/pad counts change: a cache
    # built before board.Add(footprint) once made a new part's own pads
    # invisible to probes and shipped a short (SPF power board D8, 2026-07).
    def _sig(self):
        return (len(list(self.board.GetTracks())),
                sum(len(f.Pads()) for f in self.board.GetFootprints()))

    def _get_index(self):
        sig = self._sig()
        if self._index is None or sig != self._index_sig:
            self._index = (
                [(t.GetBoundingBox(), t, True)
                 for t in self.board.GetTracks()] +
                [(p.GetBoundingBox(), p, False)
                 for f in self.board.GetFootprints() for p in f.Pads()])
            self._index_sig = sig
        return self._index

    # ---------------------------------------------------------------- checks
    def collides(self, x1, y1, x2, y2, width, netcode, layer, clr=None):
        """First colliding item (exact shapes) for a segment probe, or None."""
        probe = pcbnew.SHAPE_SEGMENT(_vec(x1, y1), _vec(x2, y2),
                                     pcbnew.FromMM(width))
        clr = self.clr if clr is None else pcbnew.FromMM(clr)
        pad = int(pcbnew.FromMM(width) / 2) + clr + pcbnew.FromMM(0.05)
        lox = min(pcbnew.FromMM(x1), pcbnew.FromMM(x2)) - pad
        hix = max(pcbnew.FromMM(x1), pcbnew.FromMM(x2)) + pad
        loy = min(pcbnew.FromMM(y1), pcbnew.FromMM(y2)) - pad
        hiy = max(pcbnew.FromMM(y1), pcbnew.FromMM(y2)) + pad
        for bb, item, is_track in self._get_index():
            if (bb.GetRight() < lox or bb.GetLeft() > hix or
                    bb.GetBottom() < loy or bb.GetTop() > hiy):
                continue
            if item.GetNetCode() == netcode:
                continue
            if is_track:
                if (type(item).__name__ == "PCB_TRACK" and
                        item.GetLayer() != layer):
                    continue
                if probe.Collide(item.GetEffectiveShape(), clr):
                    return item
            else:
                if item.FlashLayer(layer) and \
                        probe.Collide(item.GetEffectiveShape(layer), clr):
                    return item
                # unflashed pads still have HOLES (review finding: a trace
                # could be routed over an unflashed THT hole unchecked).
                # Holes are checked at HOLE-TO-COPPER clearance, not track
                # clearance: DRC's min_hole_clearance (0.2) is wider than
                # the routing clearance, and probing at track clearance let
                # a tap pass 0.14mm from a J5 NPTH that DRC then rejected
                # (usb-hub-3s, 2026-07-21 — twice, on both alignment holes).
                if item.GetDrillSizeX() > 0 and \
                        probe.Collide(item.GetEffectiveHoleShape(),
                                      max(clr, pcbnew.FromMM(0.2))):
                    return item
        return None

    def via_site_ok(self, x, y, netcode, size=0.45, drill=0.2,
                    hole_to_copper=0.205, layers=None):
        """Barrel clearance AND hole-to-copper on every layer.

        `layers` DEFAULTS to the board's FULL copper stack (via
        board.GetEnabledLayers().CuStack()), not just F.Cu/B.Cu — a
        standard through-hole via (the only kind add_via emits) physically
        occupies EVERY copper layer between F.Cu and B.Cu, including
        In*.Cu. The old hardcoded (F_Cu, B_Cu) default silently skipped
        inner layers, so a via checked "ok" while landing inside 0.02mm of
        a same-spot In2.Cu/In3.Cu track — 200 shorting_items + 501
        clearance findings on a 6-layer board whose signal routing lives on
        In2.Cu/In3.Cu (crow-recorder-central-v2, 2026-07-23), invisible to
        this check and to `quick` (pre-fill) alike, only surfacing at the
        full kicad-cli DRC gate. Pass an explicit `layers=` to override
        (e.g. a blind/buried via that does NOT span the full stack)."""
        if layers is None:
            layers = tuple(self.board.GetEnabledLayers().CuStack())
        for lay in layers:
            if self.collides(x, y, x, y, size, netcode, lay):
                return False
            if self.collides(x, y, x, y, drill, netcode, lay,
                             clr=hole_to_copper):
                return False
        return True

    def all_blockers(self, x1, y1, x2, y2, width, netcode, layer):
        """Distinct blocking items on a path — feed the rip-single-blocker
        workflow (rip track-only blocker nets, join, re-route them)."""
        hits, probe = set(), pcbnew.SHAPE_SEGMENT(
            _vec(x1, y1), _vec(x2, y2), pcbnew.FromMM(width))
        for t in self.board.GetTracks():
            if t.GetNetCode() == netcode:
                continue
            if type(t).__name__ == "PCB_TRACK" and t.GetLayer() != layer:
                continue
            if probe.Collide(t.GetEffectiveShape(), self.clr):
                hits.add(("track", t.GetNetname()))
        for f in self.board.GetFootprints():
            for p in f.Pads():
                if p.GetNetCode() == netcode or not p.FlashLayer(layer):
                    continue
                if probe.Collide(p.GetEffectiveShape(layer), self.clr):
                    hits.add(("pad", f"{f.GetReference()}.{p.GetNumber()}"
                                     f":{p.GetNetname()}"))
        return hits

    # ------------------------------------------------------------- additions
    def add_seg(self, x1, y1, x2, y2, net, layer, width):
        t = pcbnew.PCB_TRACK(self.board)
        t.SetStart(_vec(x1, y1)); t.SetEnd(_vec(x2, y2))
        t.SetWidth(pcbnew.FromMM(width)); t.SetLayer(layer); t.SetNet(net)
        self.board.Add(t)

    def add_via(self, x, y, net, size=0.45, drill=0.2):
        v = pcbnew.PCB_VIA(self.board)
        v.SetPosition(_vec(x, y))
        v.SetWidth(pcbnew.FromMM(size)); v.SetDrill(pcbnew.FromMM(drill))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(net)
        self.board.Add(v)

    def joinpath(self, netname, p1, p2, width, layer=pcbnew.F_Cu,
                 widths_fallback=(0.2, 0.15)):
        """Direct / L / Z-scan join between two same-net points. Every
        candidate segment is exact-checked; returns the width used or None."""
        net = self.board.FindNet(netname)
        nc = net.GetNetCode()
        for w in (width,) + tuple(x for x in widths_fallback if x < width):
            cands = [[p1, p2], [p1, (p1[0], p2[1]), p2],
                     [p1, (p2[0], p1[1]), p2]]
            lox, hix = min(p1[0], p2[0]) - 1.5, max(p1[0], p2[0]) + 1.5
            for i in range(int((hix - lox) / 0.1) + 1):
                xt = lox + 0.1 * i
                cands.append([p1, (xt, p1[1]), (xt, p2[1]), p2])
            loy, hiy = min(p1[1], p2[1]) - 1.5, max(p1[1], p2[1]) + 1.5
            for i in range(int((hiy - loy) / 0.1) + 1):
                yt = loy + 0.1 * i
                cands.append([p1, (p1[0], yt), (p2[0], yt), p2])
            for pts in cands:
                if all(self.collides(*pts[i], *pts[i + 1], w, nc, layer)
                       is None for i in range(len(pts) - 1)):
                    for i in range(len(pts) - 1):
                        self.add_seg(*pts[i], *pts[i + 1], net, layer, w)
                    return w
        return None

    def verified_astar(self, netname, p1, p2, width, grid=0.1, viacost=25,
                       window=4.0, attempts=8, exempt_r=0.3):
        """Two-layer grid A* whose EMITTED path is re-verified segment by
        segment (exact shapes); failing nodes are blocked and the search
        retries. Endpoint exemption is for the search only — verification
        has no exemptions, which is the entire point."""
        F, Bc = pcbnew.F_Cu, pcbnew.B_Cu
        net = self.board.FindNet(netname)
        nc = net.GetNetCode()
        x0, y0 = min(p1[0], p2[0]) - window, min(p1[1], p2[1]) - window
        x1, y1 = max(p1[0], p2[0]) + window, max(p1[1], p2[1]) + window
        NX, NY = int((x1 - x0) / grid) + 1, int((y1 - y0) / grid) + 1
        extra = set()

        def seg_ok(ax, ay, bx, by, lay, w):
            return self.collides(ax, ay, bx, by, w, nc, lay) is None

        for _ in range(attempts):
            cache = {}

            def blk(ix, iy, il):
                k = (ix, iy, il)
                if k in extra:
                    return True
                if k not in cache:
                    cx, cy = x0 + ix * grid, y0 + iy * grid
                    if (math.hypot(cx - p1[0], cy - p1[1]) < exempt_r or
                            math.hypot(cx - p2[0], cy - p2[1]) < exempt_r):
                        cache[k] = False
                    else:
                        cache[k] = not seg_ok(cx, cy, cx, cy,
                                              F if il == 0 else Bc, width)
                return cache[k]

            s = (round((p1[0] - x0) / grid), round((p1[1] - y0) / grid), 0)
            g = (round((p2[0] - x0) / grid), round((p2[1] - y0) / grid), 0)
            pq, came, dist = [(0, s, None)], {}, {s: 0}
            found = False
            while pq:
                d, cur, prev = heapq.heappop(pq)
                if cur in came:
                    continue
                came[cur] = prev
                if cur == g:
                    found = True
                    break
                ix, iy, il = cur
                for dx, dy, dl, c in ((1, 0, 0, 1), (-1, 0, 0, 1),
                                      (0, 1, 0, 1), (0, -1, 0, 1),
                                      (1, 1, 0, 1.4), (1, -1, 0, 1.4),
                                      (-1, 1, 0, 1.4), (-1, -1, 0, 1.4),
                                      (0, 0, 1, viacost)):
                    nxt = (ix + dx, iy + dy, (il + dl) % 2)
                    if not (0 <= nxt[0] < NX and 0 <= nxt[1] < NY):
                        continue
                    if nxt in came or blk(*nxt):
                        continue
                    nd = d + c
                    if nd < dist.get(nxt, 1e18):
                        dist[nxt] = nd
                        heapq.heappush(
                            pq, (nd + abs(nxt[0] - g[0]) + abs(nxt[1] - g[1]),
                                 nxt, cur))
            if not found:
                return False
            path = [g]
            while came[path[-1]] is not None:
                path.append(came[path[-1]])
            path.reverse()

            def xy(n):
                return (x0 + n[0] * grid, y0 + n[1] * grid)

            pts = ([(p1[0], p1[1], 0)] +
                   [(*xy(n), n[2]) for n in path[1:-1]] +
                   [(p2[0], p2[1], path[-2][2] if len(path) > 1 else 0)])
            bad = []
            for i in range(len(pts) - 1):
                a, b = pts[i], pts[i + 1]
                if not seg_ok(a[0], a[1], b[0], b[1],
                              F if b[2] == 0 else Bc, width):
                    bad.append(path[min(i + 1, len(path) - 1)])
            for i in range(1, len(path)):
                if path[i][2] != path[i - 1][2]:
                    vx, vy = xy(path[i])
                    if not self.via_site_ok(vx, vy, nc):
                        bad.append(path[i])
            if bad:
                extra.update(bad)
                continue
            for i in range(1, len(path)):
                if path[i][2] != path[i - 1][2]:
                    self.add_via(*xy(path[i]), net)
            for i in range(len(pts) - 1):
                a, b = pts[i], pts[i + 1]
                if abs(a[0] - b[0]) < 1e-9 and abs(a[1] - b[1]) < 1e-9:
                    continue
                self.add_seg(a[0], a[1], b[0], b[1], net,
                             F if b[2] == 0 else Bc, width)
            return True
        return False

    # ------------------------------------------------------------- placement
    def ring_search(self, fp, target, others_margin=0.1, edge=None,
                    holes=None, screw_r=3.2, rmax=15.0, check_copper=True):
        """Legal spot for footprint `fp` near `target` (x, y). Checks ALL
        THREE legality layers: footprint bboxes, screw-head keepouts, and
        copper under the new location (the one everyone forgets)."""
        b = fp.GetBoundingBox(False, False)
        hw = (MM(b.GetRight()) - MM(b.GetLeft())) / 2 + 0.25
        hh = (MM(b.GetBottom()) - MM(b.GetTop())) / 2 + 0.25
        others = []
        for f in self.board.GetFootprints():
            if f is fp or f.GetReference().startswith("H"):
                continue
            o = f.GetBoundingBox(False, False)
            others.append((MM(o.GetLeft()), MM(o.GetTop()),
                           MM(o.GetRight()), MM(o.GetBottom())))
        holes = holes or [
            (MM(f.GetPosition().x), MM(f.GetPosition().y))
            for f in self.board.GetFootprints()
            if f.GetReference().startswith("H")]
        for ring in [0.5 * k for k in range(1, int(rmax / 0.5))]:
            for ang in range(0, 360, 15):
                x = target[0] + ring * math.cos(math.radians(ang))
                y = target[1] + ring * math.sin(math.radians(ang))
                if edge and not (edge[0] + hw < x < edge[2] - hw and
                                 edge[1] + hh < y < edge[3] - hh):
                    continue
                if any(max(abs(x - hx), abs(y - hy)) < screw_r + max(hw, hh)
                       for hx, hy in holes):
                    continue
                if any(not (x + hw < o[0] - others_margin or
                            x - hw > o[2] + others_margin or
                            y + hh < o[1] - others_margin or
                            y - hh > o[3] + others_margin) for o in others):
                    continue
                if check_copper:
                    probe = pcbnew.SHAPE_SEGMENT(
                        _vec(x - hw, y), _vec(x + hw, y),
                        pcbnew.FromMM(2 * hh))
                    blocked = False
                    for t in self.board.GetTracks():
                        if probe.Collide(t.GetEffectiveShape(), self.clr):
                            blocked = True
                            break
                    if blocked:
                        continue
                return (x, y)
        return None
