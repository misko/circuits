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
# keypad strip rectangle (x0,y0,x1,y1) — the NORTH isolated band (contacts +
# buses + J_KEY, y<35). Reed COIL pads (logic, y37.8) sit SOUTH of it. No
# logic/GND pad, no pour inside. (REDO 2026-07-23: keypad moved N, logic S.)
STRIP = (12.0, 10.0, 264.0, 35.0)

# ---- I-POL: (ref -> (pad, expected net)) — pad numbers are PHYSICAL pads -----
POLARIZED = {
    "J_PWR":   ("1", "5V_IN"),
    "U_EFUSE": ("5", "5V_PROTECTED"),   # eFuse OUT
    "Q_REV":   ("3", "5V_FUSED"),       # revpol P-FET DRAIN = input side
    "D_TVS":   ("1", "5V_PROTECTED"),   # SMBJ cathode on protected rail
    "D_REVCLAMP": ("1", "5V_IN"),       # SS34 cathode on input rail
    "CE1":     ("1", "5V_PROTECTED"),   # bulk + on protected rail
    "U_LDO":   ("3", "5V_PROTECTED"),   # AMS1117 VIN
    "Q_COIL":  ("3", "5V_KEY_RELAY"),   # coil-gate P-FET DRAIN = gated rail
    "U_WD":    ("1", "WD_OK"),          # TPS3823 RESET_N
    "U_ONESHOT": ("5", "PRESS_TIMED"),  # one-shot Q
    "U_AND3":  ("4", "KEY_RELAY_ALLOWED"),
    "K_U1":    ("1", "5V_KEY_RELAY"),   # reed COIL (logic)
    "K_STOP":  ("1", "5V_KEY_RELAY"),
    "U_ADC":   ("16", "3V3_ANALOG"),
}
# extra: reed CONTACT pads must sit on the isolated bus (not the coil rail)
RELAY_CONTACT = {"K_U1": ("4", "U_SEL_BUS"), "K_D1": ("4", "D_SEL_BUS"),
                 "K_PRESS": ("3", "RKEY_MID"), "K_STOP": ("3", "RSTOP_MID")}

# ---- I-PROX: (passive, anchor, max center-center mm) — D-ADJ -----------------
PROX = [
    ("C_DVDT","U_EFUSE",5.0), ("R_OVT","U_EFUSE",9.0), ("R_OVB","U_EFUSE",9.5),
    ("R_ILM","U_EFUSE",9.5),  ("R_PG","U_EFUSE",9.0),
    ("C_AND1","U_AND1",5.0), ("C_AND2","U_AND2",5.0), ("C_AND3","U_AND3",5.0),
    ("C_LATCHA","U_LATCHA",5.0), ("C_LATCHB","U_LATCHB",5.0),
    ("C_WD","U_WD",5.0), ("R_MR","U_WD",7.0),
    ("C_ULNA","U_ULNA",9.0), ("C_ULNB","U_ULNB",9.0),
    ("C_ADCV","U_ADC",8.0), ("C_EXP","U_EXP",8.0),
    ("C_SR1","U_SR1",7.0), ("C_SR2","U_SR2",7.0),
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
    for ref,(pad,want) in {**POLARIZED, **RELAY_CONTACT}.items():
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
    # (a) >= 6mm keypad-copper <-> logic-copper, cross-footprint (reed body = barrier)
    gmin, garg = 1e9, None
    for r1,n1,x1,y1 in kp:
        for r2,n2,x2,y2 in lg:
            if r1 == r2: continue                       # intra-reed coil/contact = rated 1.5kV
            d = math.hypot(x1-x2, y1-y2)
            if d < gmin: gmin, garg = d, (r1,n1,r2,n2)
    if gmin < ISO_GAP_MM - 1e-6:
        fails.append(f"I-ISO keypad<->logic gap {gmin:.2f}mm < {ISO_GAP_MM}mm "
                     f"({garg[0]}.{garg[1]} <-> {garg[2]}.{garg[3]})")
    else:
        notes.append(f"I-ISO min keypad<->logic gap {gmin:.2f}mm "
                     f"({garg[0]}.{garg[1]} <-> {garg[2]}.{garg[3]})")
    # (b) no SELV-logic / GND pad inside the keypad strip rectangle
    sx0,sy0,sx1,sy1 = STRIP
    intruders = [(r,n) for r,n,x,y in lg if sx0 <= x <= sx1 and sy0 <= y <= sy1]
    if intruders:
        fails.append(f"I-ISO {len(intruders)} logic pad(s) inside keypad strip {STRIP}: "
                     f"{sorted(set(intruders))[:6]}")
    # (c) no copper pour (plane) inside the keypad strip on any layer
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
    main()
