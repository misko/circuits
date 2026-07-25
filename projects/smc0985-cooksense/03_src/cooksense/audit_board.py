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

Exit 1 on any FAIL. Run: /usr/bin/python3 03_src/cooksense/audit_board.py
"""
import os, sys, math, json
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
    ("R_HSG","Q_COIL",5.0), ("C_KR","Q_COIL",6.0), ("R_COILENPD","Q_COILDRV",6.0),
    ("R_OS","U_ONESHOT",6.0), ("C_OS","U_ONESHOT",6.0),
    ("C_LDOOUT","U_LDO",8.0),
]

# ---- I-EDGE: (ref, edge, tol_mm) — connector body reaches that board edge ----
EDGE = [
    ("J_PWR","W",4.0), ("J_KEY_MATRIX","W",4.0),
    ("J_THERM_A","S",4.0), ("J_THERM_B","S",4.0), ("J_TC","S",4.0), ("J_PI","S",4.0),
    ("J_LOADCELL","S",4.0), ("J_RH_AMBIENT","S",4.0), ("J_RH_EXHAUST","S",4.0),
    ("J_MODE","E",4.0), ("J_ESTOP","E",4.0), ("J_DOOR","E",4.0),
    ("J_CONTACTOR","E",4.0),
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

    # ---------- report ----------
    for n in notes: print("  note:", n)
    if fails:
        print("AUDIT FAIL")
        for x in fails: print("  ", x)
        sys.exit(1)
    print(f"AUDIT PASS: {len(POLARIZED)+len(RELAY_CONTACT)} polarity, {len(PROX)} proximity, "
          f"{len(EDGE)} edge, I-OUT tightest {owm:.2f}mm (>= {OUT_CLR}), "
          f"I-ISO gap {gmin:.2f}mm (>= {ISO_GAP_MM}), "
          f"0 strip intruders, {len(fps)} silk")


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        selftest()          # known-bad: prove the track-aware I-ISO CAN fail
    main()
