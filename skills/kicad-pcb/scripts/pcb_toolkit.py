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
board edges, or rule areas. collides() also exempts SAME-NET items by
design; the one constraint that must not be exempted that way is
hole-to-hole, which therefore lives in its own net-independent check
(hole_to_hole_ok, applied by via_site_ok). Zones are handled by refill-after-edit; edge
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


def apply_via_protection(via, protection, path="via_protection"):
    """Apply explicit per-via IPC-4761 fill/cap intent.

    KiCad's board setup values are only defaults. Via-in-pad work needs an
    item-level declaration so ordinary routing/stitch vias do not inherit an
    expensive or fabricator-incompatible Type VII process. ``None`` means
    inherit the board default; an explicit false value means opt this via out.
    """
    if protection is None:
        return via
    if not isinstance(protection, dict):
        raise ValueError(f"{path} must be a mapping")
    unknown = sorted(set(protection) - {"capping", "filling"})
    if unknown:
        raise ValueError(f"{path} has unknown key(s): {unknown}; "
                         "known: ['capping', 'filling']")
    if not protection:
        raise ValueError(f"{path} must declare capping and/or filling")

    def enabled(value, item_path):
        if isinstance(value, bool):
            return value
        if isinstance(value, str) and value.strip().lower() in ("yes", "no"):
            return value.strip().lower() == "yes"
        raise ValueError(f"{item_path} must be a boolean (yes/no)")

    if "capping" in protection:
        cap = enabled(protection["capping"], f"{path}.capping")
        via.SetCappingMode(pcbnew.CAPPING_MODE_CAPPED if cap
                           else pcbnew.CAPPING_MODE_NOT_CAPPED)
    if "filling" in protection:
        fill = enabled(protection["filling"], f"{path}.filling")
        via.SetFillingMode(pcbnew.FILLING_MODE_FILLED if fill
                           else pcbnew.FILLING_MODE_NOT_FILLED)
    return via


class Toolkit:
    def __init__(self, board, clearance_mm=0.11, hole_to_hole_mm=None):
        self.board = board
        self.clr = pcbnew.FromMM(clearance_mm)
        # HOLE-TO-HOLE floor, in mm. Default: the BOARD'S OWN design setting
        # (m_HoleToHoleMin), which `generate_rules_generic` writes from the
        # declared fab tier BEFORE routing (canon R1) and which is the exact
        # number `kicad-cli pcb drc` judges against — so the site check and
        # the gate cannot drift apart. Pass an explicit value to override.
        # (A board opened with no .kicad_pro beside it falls back to KiCad's
        # own 0.25mm default, which is the tier floor for advanced-option
        # boards and a floor, never a ceiling, for standard ones.)
        if hole_to_hole_mm is None:
            hole_to_hole_mm = MM(board.GetDesignSettings().m_HoleToHoleMin)
        self.h2h = float(hole_to_hole_mm)
        self._index = None
        self._index_sig = None
        self._index_frozen = False

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
        # A verified A* search probes thousands of cells without mutating the
        # board.  Recounting every track and pad for every cell turned a
        # sub-second graph search into minutes on 3k-track boards.  The A*
        # wrapper freezes only for the duration of one non-mutating search;
        # it invalidates unconditionally on exit before any later caller can
        # observe a board change through stale boxes.
        if self._index_frozen and self._index is not None:
            return self._index
        sig = self._sig()
        if self._index is None or sig != self._index_sig:
            def pad_limits(p):
                local = p.GetLocalClearance()
                try:
                    mask_f = (p.GetSolderMaskExpansion(pcbnew.F_Cu)
                              if p.IsOnLayer(pcbnew.F_Mask) else 0)
                    mask_b = (p.GetSolderMaskExpansion(pcbnew.B_Cu)
                              if p.IsOnLayer(pcbnew.B_Mask) else 0)
                except TypeError:
                    local_mask = p.GetLocalSolderMaskMargin()
                    mask_f = local_mask if p.IsOnLayer(pcbnew.F_Mask) else 0
                    mask_b = local_mask if p.IsOnLayer(pcbnew.B_Mask) else 0
                return (int(local or 0), int(mask_f or 0), int(mask_b or 0))

            self._index = [
                (t.GetBoundingBox(), t, True, 0, 0, 0)
                for t in self.board.GetTracks()
            ]
            for f in self.board.GetFootprints():
                for p in f.Pads():
                    local, mask_f, mask_b = pad_limits(p)
                    self._index.append(
                        (p.GetBoundingBox(), p, False,
                         local, mask_f, mask_b))
            self._index_sig = sig
        return self._index

    # ---------------------------------------------------------------- checks
    def collides(self, x1, y1, x2, y2, width, netcode, layer, clr=None,
                 respect_pad_mask=False):
        """First colliding item (exact shapes) for a segment probe, or None.

        A pad's local clearance is part of its realized geometry contract, not
        a DRC-only annotation.  The stitcher used to probe every foreign pad
        at only the caller's common clearance, so a grid via could pass this
        predicate and then fail KiCad against a fiducial's wider local copper
        keepout.  Via probes may additionally request the realized solder-mask
        expansion on outer layers; traces remain free to run beneath mask.
        """
        probe = pcbnew.SHAPE_SEGMENT(_vec(x1, y1), _vec(x2, y2),
                                     pcbnew.FromMM(width))
        clr = self.clr if clr is None else pcbnew.FromMM(clr)
        xlo = min(pcbnew.FromMM(x1), pcbnew.FromMM(x2))
        xhi = max(pcbnew.FromMM(x1), pcbnew.FromMM(x2))
        ylo = min(pcbnew.FromMM(y1), pcbnew.FromMM(y2))
        yhi = max(pcbnew.FromMM(y1), pcbnew.FromMM(y2))
        for bb, item, is_track, local_clearance, mask_f, mask_b in self._get_index():
            item_clr = clr
            if not is_track:
                item_clr = max(item_clr, local_clearance)
                if respect_pad_mask and layer in (pcbnew.F_Cu, pcbnew.B_Cu):
                    item_clr = max(
                        item_clr,
                        mask_f if layer == pcbnew.F_Cu else mask_b)
            margin = (int(pcbnew.FromMM(width) / 2) + item_clr
                      + pcbnew.FromMM(0.05))
            lox, hix = xlo - margin, xhi + margin
            loy, hiy = ylo - margin, yhi + margin
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
                        probe.Collide(item.GetEffectiveShape(layer), item_clr):
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
                                      max(item_clr, pcbnew.FromMM(0.2))):
                    return item
        return None

    def hole_sites(self, skip=()):
        """(x_mm, y_mm, drill_radius_mm) for every DRILLED hole on the board —
        vias and drilled (THT/NPTH) pads. `skip` is an iterable of items to
        ignore, for the caller that is about to MOVE one of them.

        Positions are read LIVE off the items; the bbox index is used only as
        the item list (its cached boxes go stale when a via is nudged, and a
        stale box must not decide a spacing question)."""
        dead = {i.m_Uuid.AsString() for i in skip}
        out = []
        for _bb, item, is_track, _local, _mask_f, _mask_b in self._get_index():
            if is_track:
                if type(item).__name__ != "PCB_VIA":
                    continue
                d = item.GetDrillValue()
            else:
                d = item.GetDrillSizeX()
            if d <= 0 or item.m_Uuid.AsString() in dead:
                continue
            p = item.GetPosition()
            out.append((MM(p.x), MM(p.y), MM(d) / 2.0))
        return out

    def hole_to_hole_ok(self, x, y, drill, floor=None, skip=()):
        """Is a new `drill`-mm hole at (x, y) clear of every OTHER drilled
        hole on the board, drill EDGE to drill EDGE, by at least `floor` mm?

        NET-INDEPENDENT ON PURPOSE — and that is why it could not live inside
        `collides()`. Every other test in this toolkit exempts same-net items,
        because same-net COPPER is allowed to touch. Two DRILLS are not: the
        floor is MECHANICAL (adjacent barrels break out into each other on the
        drill), and KiCad's `hole_to_hole` DRC rule applies it across nets and
        within one net alike. Skipping same-net holes here is exactly how two
        5VA tap vias landed 0.259mm apart on a 0.4995mm floor and shipped a
        DRC violation nothing in the stitch objected to (usb-hub-3s-v3,
        2026-07-25 — see hole_to_hole in via_site_ok).

        A hole COINCIDENT with the probe (within 1um) is the probe, not a
        neighbour: re-checking a site that already holds a via must answer
        "yes, a via fits here". Stacked same-net vias are `dedupe_vias`'
        business; a coincident DIFFERENT-net via is already a hard refusal in
        `collides()` (zero-distance copper)."""
        f = self.h2h if floor is None else float(floor)
        if f <= 0 or drill <= 0:
            return True
        r = drill / 2.0
        for hx, hy, hr in self.hole_sites(skip):
            d = math.hypot(x - hx, y - hy)
            if d <= 1e-3:                      # the probe IS this hole
                continue
            if d - (r + hr) < f - 1e-9:
                return False
        return True

    def via_site_ok(self, x, y, netcode, size=0.45, drill=0.2,
                    hole_to_copper=0.205, layers=None,
                    hole_to_hole=None, skip=()):
        """Barrel clearance, hole-to-copper on every layer, AND hole-to-hole.

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
        (e.g. a blind/buried via that does NOT span the full stack).

        HOLE-TO-HOLE is checked LAST and is the only test here that does not
        exempt same-net items — see `hole_to_hole_ok`. `skip` names holes to
        ignore (the via a caller is about to move out of the way)."""
        if layers is None:
            layers = tuple(self.board.GetEnabledLayers().CuStack())
        for lay in layers:
            if self.collides(
                    x, y, x, y, size, netcode, lay,
                    respect_pad_mask=(lay in (pcbnew.F_Cu, pcbnew.B_Cu))):
                return False
            if self.collides(x, y, x, y, drill, netcode, lay,
                             clr=hole_to_copper):
                return False
        return self.hole_to_hole_ok(x, y, drill, floor=hole_to_hole, skip=skip)

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

    def add_via(self, x, y, net, size=0.45, drill=0.2, protection=None,
                protection_path="via_protection"):
        v = pcbnew.PCB_VIA(self.board)
        v.SetPosition(_vec(x, y))
        v.SetWidth(pcbnew.FromMM(size)); v.SetDrill(pcbnew.FromMM(drill))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(net)
        apply_via_protection(v, protection, protection_path)
        self.board.Add(v)
        return v

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
                       window=4.0, attempts=8, exempt_r=0.3,
                       via_size=0.45, via_drill=0.2, layers=None,
                       hole_to_copper=None):
        """Run one A* search against a stable cached obstacle index."""
        self._get_index()
        self._index_frozen = True
        try:
            return self._verified_astar(
                netname, p1, p2, width, grid=grid, viacost=viacost,
                window=window, attempts=attempts, exempt_r=exempt_r,
                via_size=via_size, via_drill=via_drill, layers=layers,
                hole_to_copper=hole_to_copper)
        finally:
            self._index_frozen = False
            # The implementation may have emitted tracks/vias.  Invalidating
            # on both success and failure keeps the historic auto-rebuild
            # guarantee without another O(N) signature walk here.
            self._index = None
            self._index_sig = None

    def _verified_astar(self, netname, p1, p2, width, grid=0.1, viacost=25,
                        window=4.0, attempts=8, exempt_r=0.3,
                        via_size=0.45, via_drill=0.2, layers=None,
                        hole_to_copper=None):
        """Two-layer grid A* whose EMITTED path is re-verified segment by
        segment (exact shapes); failing nodes are blocked and the search
        retries. Endpoint exemption is for the search only — verification
        has no exemptions, which is the entire point.

        `layers` selects one or two copper layers and defaults to `(F.Cu,
        B.Cu)`.  Supplying e.g. `(In2.Cu, B.Cu)` lets a reviewed escape use
        an existing inner-layer corridor; `(B.Cu,)` constrains the search to
        one layer and emits no transition vias.  Both retain the same exact
        collision verification.

        `via_size`/`via_drill` are the geometry of the LAYER-CHANGE vias this
        emits — CHECKED and PLACED with the same numbers. They default to the
        historic 0.45/0.2, which is below a standard-tier floor: callers that
        know their tier must pass it, or the site is cleared for a hole the
        board never gets. usb-hub-3s-v3 (2026-07-25) shipped exactly that —
        the escape tap's A* cleared a site at drill 0.2 (hole gap 0.500 vs a
        0.4995 floor, PASS), emitted the via, and a post-stitch drill floor
        then opened it to 0.3, closing the gap to 0.450: a hole_to_hole
        violation created by a check that was run against the wrong drill."""
        layer_ids = tuple(layers or (pcbnew.F_Cu, pcbnew.B_Cu))
        if not 1 <= len(layer_ids) <= 2 or len(set(layer_ids)) != len(layer_ids):
            raise ValueError("verified_astar layers must name one or two distinct layers")
        n_layers = len(layer_ids)
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
                                              layer_ids[il], width)
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
                moves = [(1, 0, 0, 1), (-1, 0, 0, 1),
                         (0, 1, 0, 1), (0, -1, 0, 1),
                         (1, 1, 0, 1.4), (1, -1, 0, 1.4),
                         (-1, 1, 0, 1.4), (-1, -1, 0, 1.4)]
                if n_layers == 2:
                    moves.append((0, 0, 1, viacost))
                for dx, dy, dl, c in moves:
                    nxt = (ix + dx, iy + dy, (il + dl) % n_layers)
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
                              layer_ids[b[2]], width):
                    bad.append(path[min(i + 1, len(path) - 1)])
            for i in range(1, len(path)):
                if path[i][2] != path[i - 1][2]:
                    vx, vy = xy(path[i])
                    kw = ({"hole_to_copper": hole_to_copper}
                          if hole_to_copper is not None else {})
                    if not self.via_site_ok(vx, vy, nc, size=via_size,
                                            drill=via_drill, **kw):
                        bad.append(path[i])
            if bad:
                extra.update(bad)
                continue
            for i in range(1, len(path)):
                if path[i][2] != path[i - 1][2]:
                    self.add_via(*xy(path[i]), net,
                                 size=via_size, drill=via_drill)
            for i in range(len(pts) - 1):
                a, b = pts[i], pts[i + 1]
                if abs(a[0] - b[0]) < 1e-9 and abs(a[1] - b[1]) < 1e-9:
                    continue
                self.add_seg(a[0], a[1], b[0], b[1], net,
                             layer_ids[b[2]], width)
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
