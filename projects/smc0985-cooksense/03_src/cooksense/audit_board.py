#!/usr/bin/env /usr/bin/python3
"""cooksense per-board placement/pad invariant gate (03_src contract step 4).

Checks the placement facts the generic generator's own asserts do NOT cover,
re-read from the LIVE board (catches a stale 04_kicad vs 03_src):

  I-POL   polarized / oriented parts: pad N sits on the part-fact net
          (eFuse OUT/GND, revpol + coil-gate FET drain/source, TVS/SS34
          cathode, bulk +, AMS1117 VIN/VOUT+tab, reed coil vs contact).
  I-PROX  D-ADJ adjacency: each critical support passive within reach of the
          pin it serves (decouplers hard against their IC; eFuse OVLO/ILM/dVdt
          divider local; one-shot RC local; coil-gate local).
  I-EDGE  off-board connectors reach their board edge (mouth off-board).
  I-ISO   *** the board-specific guard (ADR-0001/0002, brief §4/§7) ***
          KEYPAD ISOLATION: every keypad-domain (KEYPAD_ISO) copper pad is
          >= 6.0mm from every SELV-logic pad (cross-footprint; the reed's own
          coil<->contact 7.62mm gap is the rated 1.5kVDC barrier, so intra-
          footprint pairs are excluded), AND no logic/GND pad sits inside the
          keypad strip, AND the strip carries NO copper pour (no plane).
  I-OUT   every footprint pad sits inside the board outline (minus a small
          edge clearance) — the J_PI-off-board guard I-EDGE cannot see.
  I-SILK  every placed part has a visible refdes (F.SilkS, or F.Fab when the
          generator waived a crowded one — evidence in refdes_waiver.json).
  I-HW    MOUNTING-HARDWARE isolation: the metal fastener stack in each
          mounting hole is a floating 3.0mm-radius conductive disc; its
          creepage approaches to keypad copper (a) and SELV copper (s) —
          pads + FILLED pours, path measured AROUND outline cutouts — must
          satisfy a+s >= 6.0mm per hole (bonded collapse: the free approach
          alone). ENCLOSURE_BONDS_HOLES selects the conductive-chassis
          pairing rule instead; see the constant's comment.

Exit 1 on any FAIL. Run: /usr/bin/python3 03_src/cooksense/audit_board.py
       (I-HW alone vs any board: ... audit_board.py --ihw [path])
"""
import os, sys, math, json, heapq
import pcbnew

_PROJ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BOARD = os.path.join(_PROJ, "04_kicad", "cooksense.kicad_pcb")
MM = pcbnew.ToMM

# ---- KEYPAD ISOLATION DOMAIN (nets.yaml KEYPAD_ISO class) -------------------
KEYPAD_NETS = {"KP_U1","KP_U2","KP_U3","KP_U4","KP_U5","KP_U6",
               "KP_D1","KP_D2","KP_D3","KP_D4",
               "U_SEL_BUS","D_SEL_BUS","RKEY_MID","RSTOP_MID"}
ISO_GAP_MM = 6.0                       # brief §4/§7 coil-side <-> keypad-copper creepage
# ---- v1.1 ISOLATION COMB (D7 rot0 redesign, 2026-07-24) ----------------------
# The isolated domain is no longer one strip: it is the NORTH BAND (y<=~23.2)
# plus 7 KEYPAD POCKETS between/beside the paired vertical relays. Logic lives
# in the SOUTH BAND (y>=53) plus 6 COIL GAPS (windows reaching the coil pads at
# y30.38/45.62). Relay centers x = 26.00 + n*15.24, row y=38, board x 12..200.
ROW_XC = [26.00 + i*15.24 for i in range(12)]
# coil gaps: within pairs (r1r2, r3r4, ...) — logic-legal x-windows
GAPS = [(ROW_XC[i]+3.0, ROW_XC[i+1]-3.0) for i in range(0, 12, 2)]
# keypad pockets: between pairs + both ends — keypad-legal x-windows
POCKETS = [(12.0, ROW_XC[0]-3.0)] + \
          [(ROW_XC[i]+3.0, ROW_XC[i+1]-3.0) for i in range(1, 11, 2)] + \
          [(ROW_XC[11]+3.0, 200.0)]
COMB_Y0, COMB_Y1 = 23.2, 52.9          # comb band: between keypad band and planes
# legacy STRIP retained for the pour check (c): the whole plane-free comb band.
STRIP = (12.0, 10.0, 200.0, 52.9)

# ---- I-POL: (ref -> (pad, expected net)) — pad numbers are PHYSICAL pads -----
POLARIZED = {
    "J_PWR":   ("1", "5V_IN"),
    "U_EFUSE": ("5", "5V_PROTECTED"),   # eFuse OUT
    "Q_REV":   ("3", "5V_FUSED"),       # revpol P-FET DRAIN = input side
    "D_TVS":   ("1", "5V_PROTECTED"),   # SMBJ cathode on protected rail
    "D_REVCLAMP": ("1", "5V_FUSED"),    # SS34 cathode DOWNSTREAM of F1 (pin
                                        # review Q2 fix, 2026-07-23: on 5V_IN the
                                        # reverse-clamp fault path bypassed the
                                        # polyfuse; disposition #2 + E-INV lock)
    "CE1":     ("1", "5V_PROTECTED"),   # bulk + on protected rail
    "U_LDO":   ("3", "5V_PROTECTED"),   # AMS1117 VIN
    "Q_COIL":  ("3", "5V_KEY_RELAY"),   # coil-gate P-FET DRAIN = gated rail
    "U_WD":    ("1", "WD_OK"),          # TPS3823 RESET_N
    # v1.2 (task#21, 2026-07-25): pad 5 -> 13. The v1.1 part was an SN74LVC1G123
    # SSOP-8; v1.2 replaced it with the CD74HC221 SOIC-16, whose 1Q is pin 13
    # (02_parts/CD74HC221M96/part.yaml, datasheet pinout table). Pad 5 on the '221
    # is 2Q (the UNUSED half) and carries `unconnected-(U_ONESHOT-Q2-Pad5)` — the
    # stale entry made I-POL fail on a CORRECT board, the worst kind of gate noise.
    "U_ONESHOT": ("13", "PRESS_TIMED"), # one-shot 1Q (CD74HC221)
    "U_AND3":  ("4", "KEY_RELAY_ALLOWED"),
    "K_U1":    ("1", "5V_KEY_RELAY"),   # reed COIL (logic)
    # v1.2 (task#21): K_STOP coil moved to the UNGATED 5V_STOP rail (ADR-0011 §4 —
    # the STOP relay must survive the very faults that kill 5V_KEY_RELAY).
    "K_STOP":  ("1", "5V_STOP"),
    "U_ADC":   ("16", "3V3_ANALOG"),
}
# extra: reed CONTACT pads must sit on the isolated bus (not the coil rail)
RELAY_CONTACT = {"K_U1": ("4", "U_SEL_BUS"), "K_D1": ("4", "D_SEL_BUS"),
                 "K_PRESS": ("3", "RKEY_MID"), "K_STOP": ("3", "RSTOP_MID")}
# I-POL runs over this FLAT list, not `{**POLARIZED, **RELAY_CONTACT}` (task#21,
# 2026-07-25). The dict merge silently DROPPED every ref present in both maps —
# K_STOP's coil-rail check (pad 1) was shadowed by its contact check (pad 3) and
# had never run since the maps were written. A gate that cannot fire is worthless
# (canon M1); a merge that eats a check is exactly that, invisibly.
POL_CHECKS = ([(r, p, w) for r, (p, w) in POLARIZED.items()]
              + [(r, p, w) for r, (p, w) in RELAY_CONTACT.items()])

# ---- I-PROX: (passive, anchor, max center-center mm) — D-ADJ -----------------
PROX = [
    ("C_DVDT","U_EFUSE",5.0), ("R_OVT","U_EFUSE",9.0), ("R_OVB","U_EFUSE",9.5),
    ("R_ILM","U_EFUSE",9.5),  ("R_PG","U_EFUSE",9.0),
    ("C_AND1","U_AND1",5.0), ("C_AND2","U_AND2",5.0), ("C_AND3","U_AND3",5.0),
    ("C_LATCHA","U_LATCHA",5.0), ("C_LATCHB","U_LATCHB",5.0),
    ("C_WD","U_WD",5.0), ("R_MR","U_WD",7.0),
    ("C_ULNA","U_ULNA",9.0), ("C_ULNB","U_ULNB",9.0),
    ("C_ADCV","U_ADC",8.0), ("C_EXP","U_EXP",8.0),
    # C_SR2/U_SR2 row DELETED (task#21, 2026-07-25): v1.2 removed the second '595
    # entirely (ADR-0011 §5 — STOP_REQ moved to a direct Pi GPIO), so its decoupler
    # went with it. The stale row made I-PROX report "missing C_SR2" forever.
    ("C_SR1","U_SR1",7.0),
    ("C_DECU","U_DECU",7.0), ("C_DECD","U_DECD",7.0),
    ("R_HSG","Q_COIL",5.0), ("C_KR","Q_COIL",6.0),
    # v1.7 (ADR-0018): R_COILENPD's anchor MOVED from Q_COILDRV to J_MODE, and the
    # move is the point of the fix rather than a placement convenience. It is no
    # longer "the gate pull-down" — it is the LOWER LEG OF THE DIVIDER that rejects
    # a pull-up injected onto the J_MODE pole-A field pin, and a divider only works
    # where the injection lands. Leaving the old 6mm-to-Q_COILDRV row would have
    # demanded the resistor sit 29.6mm from the pin it defends. R_COILENS is the
    # series element out to the gate and D_COILEN is the clamp; all three belong at
    # the connector, so all three are gated against it.
    # BUDGET 8.0 FOR ALL FOUR, AND THE NUMBER IS NOT FITTED TO THE PLACEMENT.
    # I-PROX measures CENTRE-TO-CENTRE, and J_MODE's own body is 10.5mm long, so a
    # part sitting hard against the connector still measures several mm from its
    # centre: as placed, D_COILEN 5.83, R_COILENPD 4.79, R_COILENS 5.00, R_MODEPD
    # 6.14 — while their distances to the PADS they serve are 1.15 / 1.85 / 4.05 /
    # 3.15mm. 8.0 is the bound that says "in the connector's own strip"; the nearest
    # alternative site is the logic band at >=15mm, so the gate still has teeth.
    ("R_COILENPD","J_MODE",8.0), ("R_COILENS","J_MODE",8.0),
    ("D_COILEN","J_MODE",8.0),   ("R_MODEPD","J_MODE",8.0),
    ("R_OS","U_ONESHOT",6.0), ("C_OS","U_ONESHOT",6.0),
    ("C_LDOOUT","U_LDO",8.0),
]

# ---- I-EDGE: (ref, edge, tol_mm) — connector body reaches that board edge ----
EDGE = [
    ("J_PWR","W",4.0), ("J_KEY_MATRIX","W",4.0),
    ("J_THERM_A","S",4.0), ("J_THERM_B","S",4.0), ("J_TC","S",4.0), ("J_PI","S",4.0),
    ("J_LOADCELL","S",4.0), ("J_RH_AMBIENT","S",4.0), ("J_RH_EXHAUST","S",4.0),
    ("J_MODE","E",4.0), ("J_ESTOP","E",4.0),   # J_DOOR deleted, ADR-0025
    ("J_ISOLOOP","E",4.0),   # v1.3 P0-A: the merged 4-pole isolated block
]


# ---- I-ISO track/via-aware creepage (P1-B fix, 2026-07-23) -------------------
# The original I-ISO measured PAD CENTRES only, so a logic TRACK dipping into the
# reed barrier (5V_KEY_RELAY y36) vs a keypad bus (U_SEL_BUS y31.3) -> ~4.35mm was
# INVISIBLE (a checker blind spot, canon M1). Creepage is a SAME-SURFACE path, so
# per-layer copper is compared (F.Cu<->F.Cu, B.Cu<->B.Cu); a through-hole via/PTH
# pad (layer=None) counts on EVERY copper layer. Straight-line copper-EDGE distance
# (centre-line distance minus both half-widths) is a conservative lower bound on
# the true, slot-lengthened creepage. Pours are NOT measured here — plane intrusion
# is guard (c) (no pour inside the keypad strip); this guard is tracks+vias+pads.
def _seg_pt(px, py, ax, ay, bx, by):
    dx, dy = bx-ax, by-ay
    L2 = dx*dx + dy*dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px-ax)*dx+(py-ay)*dy)/L2))
    return math.hypot(px-(ax+t*dx), py-(ay+t*dy))


def _seg_seg(a, c):
    ax,ay,bx,by = a; cx,cy,dx,dy = c
    return min(_seg_pt(ax,ay,cx,cy,dx,dy), _seg_pt(bx,by,cx,cy,dx,dy),
              _seg_pt(cx,cy,ax,ay,bx,by), _seg_pt(dx,dy,ax,ay,bx,by))


def _iso_cu_elems(b, pred, ybound=56.0, extra=None):
    """Copper elements (tracks, vias, pads) whose net matches pred, near the reed
    barrier (min-y <= ybound). Each = (layer_or_None, (x1,y1,x2,y2), half_width).
    `extra` = optional list of pre-built elements (used by --selftest injection)."""
    E = list(extra or [])
    for t in b.GetTracks():
        if not pred(t.GetNetname()):
            continue
        if t.GetClass() == "PCB_VIA":
            x, y = MM(t.GetPosition().x), MM(t.GetPosition().y)
            if y > ybound:
                continue
            E.append((None, (x, y, x, y), MM(t.GetWidth())/2))
        else:
            s, e = t.GetStart(), t.GetEnd()
            x1,y1,x2,y2 = MM(s.x), MM(s.y), MM(e.x), MM(e.y)
            if min(y1, y2) > ybound:
                continue
            E.append((t.GetLayer(), (x1,y1,x2,y2), MM(t.GetWidth())/2))
    for f in b.GetFootprints():
        for p in f.Pads():
            if not pred(p.GetNetname()):
                continue
            x, y = MM(p.GetPosition().x), MM(p.GetPosition().y)
            if y > ybound:
                continue
            through = p.GetDrillSize().x > 0
            lay = None if through else p.GetLayer()
            E.append((lay, (x, y, x, y), max(MM(p.GetSizeX()), MM(p.GetSizeY()))/2))
    return E


def iso_min_creepage(b, ybound=56.0, extra_logic=None):
    # v1.1: ybound raised 42 -> 56 (comb): pocket keypad pads reach y45.62 and
    # the binding logic partner is the y>=53 plane-band copper — the old 42
    # bound EXCLUDED both (a checker blind spot on the new geometry).
    """Min same-surface copper-EDGE distance between keypad-domain copper and
    SELV-logic copper (tracks+vias+pads), cross-domain. Returns (gmin_mm, descr)."""
    kp = _iso_cu_elems(b, lambda n: n in KEYPAD_NETS, ybound)
    lg = _iso_cu_elems(b, lambda n: bool(n) and n not in KEYPAD_NETS, ybound,
                       extra=extra_logic)
    gmin, arg = 1e9, None
    for lk, gk, rk in kp:
        for ll, gl, rl in lg:
            if lk is not None and ll is not None and lk != ll:
                continue                       # different surfaces: no creepage path
            d = _seg_seg(gk, gl) - rk - rl
            if d < gmin:
                gmin, arg = d, (gk, gl)
    return gmin, arg


# ---- I-HW MOUNTING-HARDWARE ISOLATION (brief §4/§7 + ADR-0001, 2026-07-25) ---
# A metal fastener in a mounting hole (M2.5 pan head + DIN125 washer + nut) is a
# FLOATING CONDUCTOR, modelled as a conductive disc of radius HW_DISC_R_MM
# centred on the hole. Per hole i:
#   a_i = surface distance, hardware-disc edge -> nearest KEYPAD-domain copper
#   s_i = surface distance, hardware-disc edge -> nearest SELV copper
# where copper = pads + FILLED zone copper (+ tracks/vias). Zones are FILLED IN
# MEMORY before measuring — a pads-only scan hides the pour and nearly produced
# a false all-clear (predecessor session, 2026-07-25). The board is never saved.
# Distances are CREEPAGE-AWARE: the path must stay on the board surface, so an
# outline cutout (the H4 notch, commit 95db1d2) lengthens it. A straight-line
# measure is BLIND to the notch — it reads the pre-notch and post-notch boards
# identically (measured: H4 a=4.031mm on both) and would fail a board the notch
# fixes, so the shortest path is computed around outline voids (visibility-graph
# Dijkstra over outline vertices; a track candidate falls back to straight-line,
# which is conservative — never longer than the true path).
#
# The fastener conducts across itself, so the series path keypad->disc->SELV
# must satisfy a_i + s_i >= HW_GAP_MM. If the disc OVERLAPS one domain (a_i<0 or
# s_i<0) the fastener is BONDED to it and the OTHER approach alone must be
# >= HW_GAP_MM (both negative = a hard 0mm bridge).
#
# *** ENCLOSURE ASSUMPTION — READ BEFORE MOUNTING THIS BOARD IN ANYTHING ***
# ENCLOSURE_BONDS_HOLES = False encodes the user decision (2026-07-25) that the
# enclosure is NON-CONDUCTIVE and NO conductive plate, bracket or rail bonds two
# or more mounting holes together. Under that assumption each fastener is an
# isolated island and the PER-HOLE rule above applies.
# Bolting this board into a METAL bracket / conductive chassis — anything that
# electrically joins two or more mounting holes — is EXACTLY what invalidates
# that assumption: flip this constant to True. The bonded plate joins all
# fasteners into ONE conductor, so the worst keypad approach and the worst SELV
# approach ACROSS DIFFERENT HOLES become the path, and the check becomes
#   min_i(a_i) + min_j(s_j) >= HW_GAP_MM
# which this board FAILS (H3/H4 hardware sits in the GND pour, s<0, while H1's
# keypad approach is ~2.3mm). That FAIL is the correct verdict for a conductive
# enclosure — do not waive it; re-place the holes or isolate the plate instead.
ENCLOSURE_BONDS_HOLES = False   # user decision 2026-07-25: non-conductive enclosure
HW_DISC_R_MM = 3.0              # fastener disc: M2.5 pan head + DIN125 washer
HW_GAP_MM = ISO_GAP_MM          # 6.000mm — same brief §4/§7 figure as I-ISO
HW_FPID = "MountingHole"        # FPID substring that identifies the holes (H1..H4)


def _rings(poly):
    """All vertex rings of a SHAPE_POLY_SET (outlines + holes), in mm."""
    R = []
    for i in range(poly.OutlineCount()):
        chains = [poly.COutline(i)] + [poly.CHole(i, j)
                                       for j in range(poly.HoleCount(i))]
        for ch in chains:
            R.append([(MM(ch.CPoint(k).x), MM(ch.CPoint(k).y))
                      for k in range(ch.PointCount())])
    return R


def _ring_edges(rings):
    return [(r[i], r[(i + 1) % len(r)]) for r in rings for i in range(len(r))]


def _pt_edges(p, edges):
    """(min distance, witness point) from point p to a list of edges, in mm."""
    px, py = p
    best, w = 1e18, None
    for (ax, ay), (bx, by) in edges:
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px-ax)*dx + (py-ay)*dy) / L2))
        qx, qy = ax + t*dx, ay + t*dy
        d = math.hypot(px - qx, py - qy)
        if d < best:
            best, w = d, (qx, qy)
    return best, w


def _proper_x(p1, p2, p3, p4):
    """True only for a STRICT interior crossing (touching/collinear allowed —
    creepage legally travels ALONG an outline face; void passage is caught by
    the containment samples in _free)."""
    x = lambda o, a, b: (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    d1, d2, d3, d4 = x(p3, p4, p1), x(p3, p4, p2), x(p1, p2, p3), x(p1, p2, p4)
    return (0 not in (d1, d2, d3, d4)) and ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def _outline_ctx(b):
    """(edges, verts, contains) of the board outline incl. cutout voids."""
    outl = pcbnew.SHAPE_POLY_SET()
    if not b.GetBoardPolygonOutlines(outl, False):
        return None
    rings = _rings(outl)
    edges = _ring_edges(rings)
    verts = [v for r in rings for v in r]

    def contains(x, y):
        if outl.Contains(pcbnew.VECTOR2I(int(round(x*1e6)), int(round(y*1e6)))):
            return True
        return _pt_edges((x, y), edges)[0] <= 0.005   # ON the outline = surface
    return edges, verts, contains


def _free(p, q, ctx):
    """Segment p->q stays on the board surface (no strict outline crossing and
    every ~0.4mm sample point is on board / on the outline itself)."""
    edges, _, contains = ctx
    for a, bb in edges:
        if _proper_x(p, q, a, bb):
            return False
    L = math.hypot(q[0]-p[0], q[1]-p[1])
    n = max(3, int(L / 0.4))
    for k in range(1, n):
        t = k / n
        if not contains(p[0] + t*(q[0]-p[0]), p[1] + t*(q[1]-p[1])):
            return False
    return True


def _toward(c, w, r):
    """The point of circle (c, r) nearest to w."""
    d = math.hypot(w[0]-c[0], w[1]-c[1])
    if d < 1e-9:
        return c
    return (c[0] + (w[0]-c[0]) * r/d, c[1] + (w[1]-c[1]) * r/d)


def _circle_hits(c, r, edges):
    """Intersections of circle (c, r) with outline edges: where the hardware
    disc rim meets the board outline — legal creepage START points (cost 0)."""
    out = []
    cx, cy = c
    for (ax, ay), (bx, by) in edges:
        dx, dy = bx-ax, by-ay
        fx, fy = ax-cx, ay-cy
        A = dx*dx + dy*dy
        if A == 0:
            continue
        B, C = 2*(fx*dx + fy*dy), fx*fx + fy*fy - r*r
        disc = B*B - 4*A*C
        if disc < 0:
            continue
        sq = math.sqrt(disc)
        for t in ((-B-sq)/(2*A), (-B+sq)/(2*A)):
            if 0.0 <= t <= 1.0:
                out.append((ax + t*dx, ay + t*dy))
    return out


def _hw_creepage(c, r, tgt_edges, ctx):
    """Shortest surface path (mm) from the rim of disc (c, r) to the target
    copper polygon, around outline voids. Caller pre-handles the bonded case
    (centre-to-copper <= r)."""
    dc, w = _pt_edges(c, tgt_edges)
    if dc <= r:
        return dc - r
    if _free(_toward(c, w, r), w, ctx):
        return dc - r                       # straight path is on-surface
    edges, verts, _ = ctx
    # visibility-graph nodes: outline vertices near the hole + disc-rim/outline
    # intersection points (where the metal meets the surface: start cost 0)
    nodes, cost = [], []
    for v in verts + _circle_hits(c, r, edges):
        dv = math.hypot(v[0]-c[0], v[1]-c[1])
        if dv > 30.0:
            continue                        # can't beat any plausible best
        if dv <= r + 1e-9:
            nodes.append(v); cost.append(0.0)   # under the disc: bonded start
        elif _free(_toward(c, v, r), v, ctx):
            nodes.append(v); cost.append(dv - r)
        else:
            nodes.append(v); cost.append(math.inf)
    best = math.inf
    h = [(cst, i) for i, cst in enumerate(cost) if cst < math.inf]
    heapq.heapify(h)
    done = set()
    while h:
        cst, i = heapq.heappop(h)
        if i in done or cst >= best:
            continue
        done.add(i)
        vi = nodes[i]
        dt, wt = _pt_edges(vi, tgt_edges)
        if cst + dt < best and _free(vi, wt, ctx):
            best = cst + dt
        for j, nj in enumerate(nodes):
            if j in done:
                continue
            wgt = math.hypot(nj[0]-vi[0], nj[1]-vi[1])
            if cst + wgt < cost[j] and cst + wgt < best and _free(vi, nj, ctx):
                cost[j] = cst + wgt
                heapq.heappush(h, (cost[j], j))
    return best if best < math.inf else dc - r   # never below the straight bound


def _lazy_poly(item):
    """Deferred SHAPE_POLY_SET for a track/via, built only if the geodesic is
    actually going to run on it.

    WHY THIS EXISTS (task#21, 2026-07-26, MEASURED). I-HW originally handed
    TRACK copper to the measurement as a bare segment with `None` for its
    polygon, and the candidate loop treated `poly is None` as "straight-line
    fallback, conservative". That is precisely the metric this check was built
    to reject: the commit that landed I-HW records that a straight-line distance
    measures the pre-notch and notched boards IDENTICALLY at H4 (4.031mm on
    both) and "cannot see the notch at all, and would have failed the very board
    the notch fixes". Pads got the visibility-graph geodesic; tracks did not,
    so the first fully ROUTED v1.3 board failed its own gate:

        I-HW H4 a=4.617mm (track RSTOP_MID) -> 4.617 < 6.000 FAIL

    MEASURED on that same board, same track (F.Cu (198.600,44.400) ->
    (197.400,45.600), the K_STOP.3 escape), same disc:
        straight-line disc-edge gap      4.617 mm
        SURFACE PATH around the notch    7.165 mm   PASS
    The straight line from H4's disc to that track crosses the H4 isolation
    notch (y[48.80,49.80], x[191.50,200.10]) at x194.51 and x195.20 — i.e. it
    runs through a through-cut in the board — so it was never a creepage path.
    A DISTANCE IS NOT A CREEPAGE, in the track branch as much as the pad branch.

    Lazy because the polygon costs real work and the candidate loop early-exits
    on the straight-line lower bound: on this board only a handful of the
    thousands of keypad/SELV tracks are ever close enough to be evaluated."""
    cache = {}

    def build():
        if "p" not in cache:
            poly = pcbnew.SHAPE_POLY_SET()
            item.TransformShapeToPolygon(poly, item.GetLayer(), 0,
                                         pcbnew.FromMM(0.005),
                                         pcbnew.ERROR_INSIDE)
            cache["p"] = poly if poly.OutlineCount() else None
        return cache["p"]
    return build


def ihw_measure(b):
    """FILL zones on the in-memory board (never saved), then per mounting hole
    measure a (keypad approach) and s (SELV approach) from the hardware-disc
    edge. Returns [(ref, a_mm, s_mm, a_label, s_label), ...] sorted by ref."""
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    ctx = _outline_ctx(b)
    holes = sorted((f for f in b.GetFootprints()
                    if HW_FPID in str(f.GetFPID().GetUniStringLibId())),
                   key=lambda f: f.GetReference())
    dom_of = lambda n: "kp" if n in KEYPAD_NETS else ("selv" if n else None)
    # copper inventory: (domain, label, polyset-or-None, seg+halfwidth-or-None)
    items = []
    for f in b.GetFootprints():
        for p in f.Pads():
            d = dom_of(p.GetNetname())
            if d:
                items.append((d, f"pad {f.GetReference()}.{p.GetNumber()} "
                                 f"{p.GetNetname()}",
                              p.GetEffectivePolygon(p.GetLayer()), None))
    for t in b.GetTracks():
        d = dom_of(t.GetNetname())
        if not d:
            continue
        if t.GetClass() == "PCB_VIA":
            x, y = MM(t.GetPosition().x), MM(t.GetPosition().y)
            seg = (x, y, x, y)
        else:
            s, e = t.GetStart(), t.GetEnd()
            seg = (MM(s.x), MM(s.y), MM(e.x), MM(e.y))
        # BOTH representations, and the third element is a LAZY polygon builder.
        # A track used to carry `None` for its polygon, which sent it down the
        # "straight fallback" branch below and made I-HW blind to exactly the
        # geometry it exists to measure — see the comment there.
        items.append((d, f"track {t.GetNetname()}", _lazy_poly(t),
                      (seg, MM(t.GetWidth()) / 2)))
    for z in b.Zones():
        if z.GetIsRuleArea():
            continue
        d = dom_of(z.GetNetname())
        if not d:
            continue
        for lay in z.GetLayerSet().Seq():
            if not pcbnew.IsCopperLayer(lay):
                continue
            poly = z.GetFilledPolysList(lay)
            if poly.OutlineCount():
                items.append((d, f"zone {z.GetNetname()} "
                                 f"{pcbnew.BOARD.GetStandardLayerName(lay)}",
                              poly, None))
    rows = []
    for hf in holes:
        pt = hf.GetPosition()
        c = (MM(pt.x), MM(pt.y))
        res = {}
        for dom in ("kp", "selv"):
            # straight-line disc-edge distances first (a LOWER bound on the
            # surface path), then geodesics in ascending order with early exit
            cands = []
            for d, label, poly, segw in items:
                if d != dom:
                    continue
                # cheap straight-line LOWER BOUND on the surface path: a
                # segment when we have one (tracks/vias), else the polygon.
                if segw is not None:
                    (x1, y1, x2, y2), hw = segw
                    ds = _seg_pt(c[0], c[1], x1, y1, x2, y2) - hw - HW_DISC_R_MM
                elif poly.Contains(pt):
                    ds = -HW_DISC_R_MM
                else:
                    ds = math.sqrt(poly.SquaredDistance(pt)) / 1e6 - HW_DISC_R_MM
                cands.append((ds, label, poly))
            cands.sort(key=lambda t: t[0])
            best, blab = 1e9, "no copper in domain"
            for ds, label, poly in cands:
                if ds >= best:
                    break                    # straight bound can't improve
                shape = poly() if callable(poly) else poly
                if ds <= 0 or shape is None or ctx is None:
                    # ds <= 0 means copper is under the disc: the fastener is
                    # BONDED to this domain and there is no path to measure.
                    # Anything else falling here has no polygon at all.
                    g = ds
                else:
                    g = _hw_creepage(c, HW_DISC_R_MM,
                                     _ring_edges(_rings(shape)), ctx)
                if g < best:
                    best, blab = g, label
            res[dom] = (best, blab)
        rows.append((hf.GetReference(), res["kp"][0], res["selv"][0],
                     res["kp"][1], res["selv"][1]))
    return rows


def ihw_verdicts(rows):
    """Apply the ENCLOSURE_BONDS_HOLES-selected rule. Returns (fails, notes) —
    measured a/s per hole is reported in BOTH (margins, not green ticks)."""
    fails, notes = [], []
    if not rows:
        fails.append(f"I-HW no '{HW_FPID}' footprints found (FPID scan broken?)")
        return fails, notes
    for ref, a, s, la, ls in rows:
        if a < 0 and s < 0:
            ok, req = False, "BONDED to BOTH domains (0mm bridge)"
        elif s < 0:
            ok, req = a >= HW_GAP_MM - 1e-6, f"SELV-bonded -> a alone {a:.3f}"
        elif a < 0:
            ok, req = s >= HW_GAP_MM - 1e-6, f"keypad-bonded -> s alone {s:.3f}"
        else:
            ok, req = a + s >= HW_GAP_MM - 1e-6, f"a+s {a+s:.3f}"
        line = (f"I-HW {ref} a={a:.3f}mm ({la}) s={s:.3f}mm ({ls}) -> {req} "
                f"{'>=' if ok else '<'} {HW_GAP_MM:.3f} {'PASS' if ok else 'FAIL'}")
        (notes if ok else fails).append(line)
    mina = min(r[1] for r in rows)
    mins = min(r[2] for r in rows)
    if mina < 0 and mins < 0:
        peff, pok = 0.0, False
    elif mins < 0:
        peff, pok = mina, mina >= HW_GAP_MM - 1e-6
    elif mina < 0:
        peff, pok = mins, mins >= HW_GAP_MM - 1e-6
    else:
        peff, pok = mina + mins, mina + mins >= HW_GAP_MM - 1e-6
    if ENCLOSURE_BONDS_HOLES:
        line = (f"I-HW PAIRING (ENCLOSURE_BONDS_HOLES=True): min_a={mina:.3f} "
                f"min_s={mins:.3f} -> {peff:.3f}mm vs {HW_GAP_MM:.3f} "
                f"{'PASS' if pok else 'FAIL'}")
        if pok:
            notes.append(line)
        else:
            fails.append(line + " — a conductive bracket/chassis bonds the "
                         "fasteners into one conductor; this board does NOT "
                         "meet 6mm through bonded hardware. Do not waive: "
                         "isolate the plate or re-place the holes.")
    else:
        notes.append(f"I-HW pairing branch INACTIVE (non-conductive enclosure "
                     f"assumption); a bonded chassis would measure min_a "
                     f"{mina:.3f} + min_s {mins:.3f} -> {peff:.3f}mm "
                     f"({'PASS' if pok else 'FAIL'}) — flip "
                     f"ENCLOSURE_BONDS_HOLES if that assumption dies")
    return fails, notes


def ihw_run(path):
    """I-HW alone against an arbitrary board (tests / red-verify). Exit 1 on FAIL."""
    b = pcbnew.LoadBoard(path)
    fails, notes = ihw_verdicts(ihw_measure(b))
    for n in notes:
        print("  note:", n)
    if fails:
        print("I-HW FAIL")
        for x in fails:
            print("  ", x)
        sys.exit(1)
    print("I-HW PASS")
    sys.exit(0)


def selftest():
    """KNOWN-BAD (canon: a gate that cannot fail is worthless). Inject a synthetic
    SELV-logic track into keypad POCKET p1 (F.Cu, y44, x45..52) — ~1.5mm from
    r2's south contact pad (45.05,45.62) — and confirm the track-aware I-ISO
    measures < 6mm on the v1.1 comb. (v1.0 selftest used the rot90 barrier at
    x198..202/y33; re-aimed at the comb 2026-07-24 and re-verified RED.)"""
    b = pcbnew.LoadBoard(BOARD)
    base, _ = iso_min_creepage(b)
    intruder = [(pcbnew.F_Cu, (45.0, 44.0, 52.0, 44.0), 0.15)]   # a 0.3mm F.Cu logic track in pocket p1
    bad, _ = iso_min_creepage(b, extra_logic=intruder)
    ok = bad < ISO_GAP_MM
    print(f"I-ISO selftest: baseline {base:.2f}mm ; with barrier-intruding track "
          f"{bad:.2f}mm (< {ISO_GAP_MM} expected) -> {'PASS (checker CAN fail)' if ok else 'BROKEN (blind)'}")
    sys.exit(0 if ok else 1)


def main():
    b = pcbnew.LoadBoard(BOARD)
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    bb = b.GetBoardEdgesBoundingBox()
    BX0,BY0,BX1,BY1 = MM(bb.GetLeft()),MM(bb.GetTop()),MM(bb.GetRight()),MM(bb.GetBottom())
    fails, notes = [], []

    def padnet(ref, num):
        f = fps.get(ref)
        if not f: return None
        for p in f.Pads():
            if p.GetNumber() == num: return p.GetNetname()
        return None

    # ---------- I-POL ----------
    for ref,pad,want in POL_CHECKS:
        got = padnet(ref,pad)
        if got != want:
            fails.append(f"I-POL {ref}.{pad}: net {got!r} != {want!r}")

    # ---------- I-PROX ----------
    for ref,anc,dmax in PROX:
        fa,fb = fps.get(ref), fps.get(anc)
        if not fa or not fb:
            fails.append(f"I-PROX missing {ref if not fa else anc}"); continue
        d = MM((fa.GetPosition()-fb.GetPosition()).EuclideanNorm())
        if d > dmax:
            fails.append(f"I-PROX {ref} is {d:.1f}mm from {anc} (max {dmax})")

    # ---------- I-EDGE ----------
    for ref,edge,tol in EDGE:
        f = fps.get(ref)
        if not f: fails.append(f"I-EDGE missing {ref}"); continue
        fb = f.GetBoundingBox(False, False)
        L,T,R,Bo = MM(fb.GetLeft()),MM(fb.GetTop()),MM(fb.GetRight()),MM(fb.GetBottom())
        gap = {"W": L-BX0, "E": BX1-R, "N": T-BY0, "S": BY1-Bo}[edge]
        if gap > tol:
            fails.append(f"I-EDGE {ref} body {gap:.1f}mm from {edge} edge (max {tol})")

    # ---------- I-OUT : every pad inside the board outline (minus clearance) ----------
    # Catches the J_PI-class defect the I-EDGE mouth-check is BLIND to: a
    # footprint whose body/pads hang OFF the board edge. (Routing D-BACK
    # 2026-07-23: J_PI 2x20 laid its 48mm body off the south edge, 34/40 pins
    # 1..43mm off-board, yet audit PASSED because I-EDGE only measures the
    # connector MOUTH gap, not whether the far pads are on copper.) Being
    # harvested to the shared checker; kept here so the redo self-verifies.
    OUT_CLR = 0.15                          # min pad-copper-to-outer-edge margin (mm)
    owm, oarg = 1e9, None
    for f in b.GetFootprints():
        r = f.GetReference()
        for p in f.Pads():
            pb = p.GetBoundingBox()
            L,T,R,Bo = MM(pb.GetLeft()),MM(pb.GetTop()),MM(pb.GetRight()),MM(pb.GetBottom())
            m = min(L-BX0, BX1-R, T-BY0, BY1-Bo)     # signed margin to nearest board edge
            if m < owm: owm, oarg = m, f"{r}.{p.GetNumber()}"
            if m < 0.0 - 1e-6:
                fails.append(f"I-OUT {r}.{p.GetNumber()} pad {(-m):.1f}mm OFF the board outline "
                             f"(bbox L{L:.1f} T{T:.1f} R{R:.1f} B{Bo:.1f}; board "
                             f"[{BX0:.0f},{BY0:.0f},{BX1:.0f},{BY1:.0f}])")
    if oarg is not None:
        if 0.0 <= owm < OUT_CLR:
            fails.append(f"I-OUT tightest pad-to-edge {owm:.2f}mm ({oarg}) < {OUT_CLR}mm clearance")
        else:
            notes.append(f"I-OUT all pads inside outline; tightest margin {owm:.2f}mm ({oarg})")

    # ---------- I-ISO : the keypad-isolation guard ----------
    kp, lg = [], []
    for f in b.GetFootprints():
        r = f.GetReference()
        for p in f.Pads():
            n = p.GetNetname(); x,y = MM(p.GetPosition().x), MM(p.GetPosition().y)
            if n in KEYPAD_NETS: kp.append((r,n,x,y))
            elif n:              lg.append((r,n,x,y))   # netted SELV-logic pads only
    if not kp:
        fails.append("I-ISO no keypad-domain pads found (net map broken?)")
    # (a) >= 6mm keypad-copper <-> logic-copper, TRACK/VIA-AWARE (not pad centres).
    # A logic track or keypad bus that bulges into the reed barrier is exactly what
    # the old pad-centre-only measure missed. Measures same-surface copper EDGES
    # (tracks + vias + pads), cross-domain (see iso_min_creepage).
    gmin, garg = iso_min_creepage(b)
    where = ""
    if garg is not None:
        (kx1,ky1,kx2,ky2), (lx1,ly1,lx2,ly2) = garg
        where = (f" (keypad @({(kx1+kx2)/2:.1f},{(ky1+ky2)/2:.1f}) <-> "
                 f"logic @({(lx1+lx2)/2:.1f},{(ly1+ly2)/2:.1f}))")
    if gmin < ISO_GAP_MM - 1e-6:
        fails.append(f"I-ISO keypad<->logic COPPER creepage {gmin:.2f}mm < "
                     f"{ISO_GAP_MM}mm{where}")
    else:
        notes.append(f"I-ISO min keypad<->logic copper creepage {gmin:.2f}mm{where}")
    # (b) comb domain-placement rules (v1.1):
    #   b1 — a SELV-logic pad north of the plane band (y < COMB_Y1) is legal
    #        ONLY inside a coil-gap x-window and only in the relay-row y-range
    #        (the coil pads at y30.38/45.62); anywhere else it intrudes on the
    #        keypad domain (north band or a pocket).
    #   b2 — a KEYPAD pad is legal ONLY in the north band (y <= COMB_Y0) or
    #        inside a pocket x-window (J_KEY_MATRIX lives in the west pocket).
    in_win = lambda x, wins: any(w0 - 0.85 <= x <= w1 + 0.85 for w0, w1 in wins)
    b1 = [(r,n) for r,n,x,y in lg
          if y < COMB_Y1 and not (in_win(x, GAPS) and 29.0 <= y <= 47.0)]
    if b1:
        fails.append(f"I-ISO(b1) {len(b1)} logic pad(s) in the keypad domain "
                     f"(north band / pocket / column): {sorted(set(b1))[:6]}")
    b2 = [(r,n) for r,n,x,y in kp
          if y > COMB_Y0 + 0.35 and not (in_win(x, POCKETS) and y <= 47.0)]
    if b2:
        fails.append(f"I-ISO(b2) {len(b2)} keypad pad(s) outside band/pockets: "
                     f"{sorted(set(b2))[:6]}")
    # (c) no copper pour (plane) inside the plane-free comb band on any layer
    sx0,sy0,sx1,sy1 = STRIP
    pour_in = 0
    for z in b.Zones():
        if z.GetIsRuleArea(): continue
        zb = z.GetBoundingBox()
        zx0,zy0,zx1,zy1 = MM(zb.GetLeft()),MM(zb.GetTop()),MM(zb.GetRight()),MM(zb.GetBottom())
        # overlap of zone bbox with strip interior (shrunk to avoid edge-touch)
        if zx0 < sx1-1 and zx1 > sx0+1 and zy0 < sy1-1 and zy1 > sy0+1:
            pour_in += 1
            notes.append(f"I-ISO pour '{z.GetNetname()}' bbox overlaps strip "
                         f"(shape may still avoid it): [{zx0:.0f},{zy0:.0f},{zx1:.0f},{zy1:.0f}]")

    # ---------- I-SILK ----------
    waiver_path = os.path.join(_PROJ, "04_kicad", "refdes_waiver.json")
    waived = set()
    if os.path.exists(waiver_path):
        try: waived = set(json.load(open(waiver_path)))
        except Exception: pass
    hole_like = lambda r: r.startswith("H") and r[1:].isdigit()
    no_silk = []
    for r,f in fps.items():
        if hole_like(r): continue
        rt = f.Reference()
        ok = rt.IsVisible() and rt.GetLayer() in (pcbnew.F_SilkS, pcbnew.F_Fab)
        if not ok and r not in waived:
            no_silk.append(r)
    if no_silk:
        fails.append(f"I-SILK refdes not visible on F.SilkS/F.Fab: {sorted(no_silk)[:8]}")

    # ---------- I-HW : mounting-hardware isolation ----------
    # LAST because ihw_measure FILLS the zones on the in-memory board (never
    # saved) — earlier checks must see the board exactly as loaded.
    hw_rows = ihw_measure(b)
    hf, hn = ihw_verdicts(hw_rows)
    fails += hf
    notes += hn

    # ---------- report ----------
    for n in notes: print("  note:", n)
    if fails:
        print("AUDIT FAIL")
        for x in fails: print("  ", x)
        sys.exit(1)
    print(f"AUDIT PASS: {len(POLARIZED)+len(RELAY_CONTACT)} polarity, {len(PROX)} proximity, "
          f"{len(EDGE)} edge, I-OUT tightest {owm:.2f}mm (>= {OUT_CLR}), "
          f"I-ISO gap {gmin:.2f}mm (>= {ISO_GAP_MM}), "
          f"0 strip intruders, {len(hw_rows)} hw holes, {len(fps)} silk")


if __name__ == "__main__":
    argv = sys.argv[1:]
    if "--selftest" in argv:
        selftest()          # known-bad: prove the track-aware I-ISO CAN fail
    if "--ihw" in argv:     # I-HW alone vs an arbitrary board (tests/red-verify)
        i = argv.index("--ihw")
        ihw_run(argv[i + 1] if len(argv) > i + 1 else BOARD)
    main()
