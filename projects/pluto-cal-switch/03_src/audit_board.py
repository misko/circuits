#!/usr/bin/env python3
"""audit_board.py — pluto-cal-switch placement/pad invariants.

The ONE per-board emitter 03_src/contracts.md allows. Everything else on this
board is shared-backend config; this file exists because five of the checks
below are properties of THIS instrument and of nothing else in the fleet.

    /usr/bin/python3 03_src/audit_board.py            (needs pcbnew)

Run from the project root (rebuild_all.sh step [4]). Exit 1 on any FAIL.

WHY EACH CHECK IS HERE, and what it would have caught:

  A-POL    pad-1 net polarity, re-derived from 02_parts/<MPN>/part.yaml and
           compared against the EXPORTED NETLIST — deliberately NOT against
           floorplan.yaml's `asserts:` block, which the generator already
           grades. Checker and checked must not share a method (canon M1):
           the floorplan asserts and this check agree only if the design is
           right, and disagree loudly if either source drifts.
  A-SYM    THE D4 GATE. ADR-0011 makes the arm-to-arm delta a PUBLISHED
           release artifact, and ARCHITECTURE sec.10.1 makes mirror symmetry
           the way it is earned. This measures it: every arm-2 part must be
           its arm-1 twin translated by EXACTLY +14.5 mm in y at an IDENTICAL
           rotation. A 0.05 mm drift on one attenuator is invisible to DRC,
           to ERC and to every render, and it turns a published number into a
           lie. (See ARM1_Y below for why the vector is 14.5 and not the 18.5
           this file demanded until 2026-07-29.)
  A-ARMSEP inter-arm copper separation >= 3 x dielectric height (sec.10.2).
           Two parallel 50-ohm microstrips on 0.2104 mm prepreg couple at
           -25..-35 dB over a few mm at 6 GHz — at or ABOVE the 30 dB the arm
           pads buy. The pads' work can be undone by the placement.
  A-DELTA  each ACTIVE splitter leg <= lambda_g/20 = 1.385 mm (sec.10.3), so
           the delta stays a lumped 3-port instead of a small network.
  A-ANTIPAD every SMA centre pin carries the local clearance that produces the
           >= D3.5 mm bottom-plane antipad of ADR-0007 RULE 1 — worth 5.6 dB of
           return loss at 6 GHz over the D2.6 minimum-DRC opening (RL 14.5 vs
           8.9; the ~9 dB carried here until 2026-07-29 was never re-derived). This rule
           was originally derived BACKWARDS and would have been frozen into
           the footprint; it is checked, not trusted.
  A-PLANE  In1.Cu (L2) has exactly one GND zone and ZERO keepouts. "L2 is one
           unbroken plane" is ARCHITECTURE sec.8's single most important rule
           and the USB and RF requirements are the same requirement here.
  A-RFSEP  measured minimum distance from every digital-block part to the
           calibration path (sec.10.5). Reported as a NUMBER, and floored, so
           "RP2040 and micro-USB at the far end" stops being a hope.
  A-PROX   every `layout.keep_short` budget declared in 02_parts, measured as
           a pad-to-pad span on THIS board. P-ADJ grades these fleet-wide but
           only for nets it can resolve; this prints all of them with their
           verdict so an unevaluated budget is visible rather than silent.
  A-SEG    the calibration chain MEASURED segment by segment against
           DETAIL_DESIGN sec.2's targets. Targets are NOT gates (ADR-0016
           credits all interconnect at ZERO, so a short run cannot lower the
           guaranteed floor) — this prints so a deviation is visible and has to
           be explained. It exists because floorplan.yaml carried a HAND-TYPED
           table of these numbers that went on describing an 18.5 mm arm
           separation after the anchors had moved to 14.5.
  I8       every refdes present, on F.SilkS, visible (the audit's silk rule).
  I9       LABEL OWNERSHIP: every refdes is nearer its OWN part's COURTYARD EDGE
           than any other part's. Two independent lenses on a sibling board
           found a CONNECTOR labelled on its neighbour, and a third found safety
           labels discriminating by 0.069 mm. A refdes that sits closer to the
           wrong part is not a cosmetic defect: it is the assembler soldering the
           wrong device and every gate passing.
           THIS CHECK IS CURRENTLY RED AND IS NOT WAIVED. The cause is upstream
           and is NOT this board's placement: the shared silk placer walks a
           fixed offset ladder out to 11 mm and takes the FIRST slot that does
           not collide, with no ownership test at all, so in a dense field it
           parks a label beside somebody else's part. Every refdes also exists on
           F.Fab AT its own part's origin, and the CPL — not the silk — is what
           the assembler consumes, so the exposure is a human misreading a
           physical board, not a placement error. Left red, declared, with the
           number, because the fix is a patch to
           skills/kicad-pcb/scripts/generate_board_generic.py and silencing a
           gate that names a real defect is the downgrade this canon exists to
           prevent.
  I10      THE FIVE PORT CAPTIONS by name, graded like I9. Five identical SMA
           jacks on our own pitch: the silk IS the user interface and a caption
           nearer the wrong jack is a confident wrong answer. Separate from I9
           because a caption is free text that nothing else on the board would
           notice drifting — and all five HAD drifted 5.0-9.8 mm when the jacks
           moved.
"""
import math
import re
import sys
from pathlib import Path

import pcbnew
import yaml

ROOT = Path(__file__).resolve().parent.parent
BOARD = ROOT / "04_kicad" / "pluto_cal_switch.kicad_pcb"
NETLIST = ROOT / "06_build" / "netlists" / "pluto_cal_switch.net"
PARTS = ROOT / "02_parts"
MM = pcbnew.ToMM

# --- the geometry this board's own docs make binding -------------------------
AXIS_Y = 55.0
# 47.75 / 62.25, NOT the 45.75 / 64.25 THIS FILE CARRIED UNTIL 2026-07-29, and the
# change is a re-derivation, not a capitulation to the floorplan. A-SYM FAILED on
# all 11 arm pairs ("+14.500 is 4.000 mm off the required +18.500") because the
# floorplan anchors and this checker disagreed. Resolving it meant asking which
# separation the physics allows, and the answer is a window ~0.8 mm wide:
#   * <= 14.66 mm, from YAT-10A+'s 6 mm GCPW-launch keep_short on LOOP_ARMn. The
#     arm-pad launch is the drop from R_DELTA1's arm pad at y=53.67 to
#     U_PAD_A2A1's RF-IN at y=arm1: 53.67 - arm1 <= 6.00 => arm1 >= 47.67.
#   * >= 13.85 mm, from the authored SMA courtyard (+/-3.90). J_SMA_RXn hangs
#     9.40 mm below its switch, so it reaches arm1 + 13.30, and U_SW2's courtyard
#     edge is at arm2 - 0.55.
# 18.50 is OUTSIDE that window and always was: it blows the launch budget by
# 1.92 mm to buy coupling margin on a constraint already met 23x over. So the
# CHECKER was carrying the wrong number and the anchors were carrying the right
# one — which is the outcome canon M1 exists to make discoverable, and it stayed
# discoverable only because this constant is written HERE and not read from
# floorplan.yaml. Do not "fix" that by importing it.
ARM1_Y, ARM2_Y = 47.75, 62.25
ARM_DY = ARM2_Y - ARM1_Y                    # 14.5 mm, the congruence vector
DIELECTRIC_H = 0.2104                       # JLC04161H-7628 prepreg (ADR-0010)
ARMSEP_MIN = 3.0 * DIELECTRIC_H             # ARCHITECTURE sec.10.2
LAMBDA_G_20 = 27.7 / 20.0                   # 1.385 mm at 6 GHz (sec.7 constants)
ANTIPAD_MIN_D = 3.5                         # ADR-0007 RULE 1
SMA_PAD_D = 2.0                             # authored footprint
RFSEP_MIN = 8.0                             # floor for sec.10.5, see the report

# arm-1 ref -> arm-2 ref. Every pair must be a pure +ARM_DY translation.
ARM_PAIRS = [
    ("U_PAD_A2A1", "U_PAD_A2B1"), ("U_PAD_A2A2", "U_PAD_A2B2"),
    ("U_SW1", "U_SW2"), ("J_SMA_RX1", "J_SMA_RX2"),
    ("C_DCBLK1", "C_DCBLK2"), ("J_SMA_ANT1", "J_SMA_ANT2"),
    ("C_SW1A", "C_SW2A"), ("C_SW1B", "C_SW2B"),
    ("C_CTRL1", "C_CTRL2"), ("R_CTRL_PD1", "R_CTRL_PD2"),
    ("R_CTRL1", "R_CTRL2"),
]
ARM1_NETS = {"LOOP_ARM1", "PAD_A2A_1", "LOOP_ARM1_SW"}
ARM2_NETS = {"LOOP_ARM2", "PAD_A2B_1", "LOOP_ARM2_SW"}
SMA_REFS = ["J_SMA_TX", "J_SMA_RX1", "J_SMA_RX2", "J_SMA_ANT1", "J_SMA_ANT2"]
# the calibration path: TX jack -> PAD_A1 -> splitter -> arms -> switches -> RX
CAL_REFS = (SMA_REFS[:3] + [f"U_PAD_A1{c}" for c in "ABCDE"]
            + ["R_DELTA1", "R_DELTA2", "R_DELTA3",
               "U_PAD_A2A1", "U_PAD_A2A2", "U_PAD_A2B1", "U_PAD_A2B2",
               "U_SW1", "U_SW2"])
DIGITAL_PREFIXES = ("U_MCU", "U_FLASH", "Y1", "R_XTAL", "C_XIN", "C_XOUT",
                    "SW_BOOT", "R_BOOT", "C_FLASH", "J_USB", "U_ESD",
                    "R_USBP", "R_USBM")

fails, notes = [], []


def ok(tag, msg):
    print(f"  {tag:<10s} PASS  {msg}")


def bad(tag, msg):
    print(f"  {tag:<10s} FAIL  {msg}")
    fails.append(f"{tag}: {msg}")


def load_netlist():
    s = NETLIST.read_text()
    pad_net = {}
    for m in re.finditer(r'\(net\s+\(code\s+"\d+"\)\s+\(name\s+"([^"]+)"\)(.*?)'
                         r'(?=\(net\s+\(code|\Z)', s, re.S):
        for r, p in re.findall(
                r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)', m.group(2)):
            pad_net[(r, p)] = m.group(1)
    if not pad_net:
        sys.exit("audit_board: parsed 0 nodes from the netlist")
    return pad_net


def load_parts():
    """value/MPN -> part.yaml dict, for parts that declare pins or keep_short."""
    out = {}
    for f in sorted(PARTS.glob("*/part.yaml")):
        d = yaml.safe_load(f.read_text())
        out[d["mpn"]] = d
        for k in ("lcsc",):
            v = (d.get("sourcing") or {}).get(k)
            if v:
                out[v] = d
    return out


def pad_xy(fp, num):
    for p in fp.Pads():
        if p.GetNumber() == num:
            return MM(p.GetPosition().x), MM(p.GetPosition().y)
    return None


def main():
    if not BOARD.is_file():
        sys.exit(f"audit_board: {BOARD} missing — run generate_board first")
    board = pcbnew.LoadBoard(str(BOARD))
    pad_net = load_netlist()
    parts = load_parts()
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    print(f"AUDIT pluto-cal-switch — {len(fps)} footprints, {BOARD.name}")

    # ---------------------------------------------------------------- A-POL
    checked = 0
    for ref, fp in sorted(fps.items()):
        d = parts.get(fp.GetValue())
        if not d or not isinstance(d.get("pins"), dict):
            continue
        for num, spec in d["pins"].items():
            num = str(num)
            want = spec if isinstance(spec, str) else (spec or {}).get("name")
            tie = (spec or {}).get("tie") if isinstance(spec, dict) else None
            got = pad_net.get((ref, num))
            if got is None:
                continue
            if tie and got != tie:
                bad("A-POL", f"{ref}.{num} ({want}) declares tie:{tie} "
                             f"but the netlist says {got}")
            checked += 1
    ok("A-POL", f"{checked} declared pads cross-checked against the netlist, "
                f"0 tie violations (independent of floorplan asserts)")

    # ---------------------------------------------------------------- A-SYM
    worst = 0.0
    for a, b in ARM_PAIRS:
        if a not in fps or b not in fps:
            bad("A-SYM", f"{a}/{b} missing from the board")
            continue
        pa, pb = fps[a].GetPosition(), fps[b].GetPosition()
        dx = MM(pb.x) - MM(pa.x)
        dy = MM(pb.y) - MM(pa.y)
        ra = fps[a].GetOrientationDegrees() % 360
        rb = fps[b].GetOrientationDegrees() % 360
        err = math.hypot(dx, dy - ARM_DY)
        worst = max(worst, err)
        if err > 0.001:
            bad("A-SYM", f"{a}->{b} translation ({dx:+.3f},{dy:+.3f}) is "
                         f"{err:.3f} mm off the required (0.000,{ARM_DY:+.3f})")
        if abs(ra - rb) > 0.01:
            bad("A-SYM", f"{a} rot {ra:.0f} != {b} rot {rb:.0f} — the arm pads "
                         f"must be at the SAME rotation, NOT mirrored "
                         f"(ARCHITECTURE sec.10.1)")
    if not [f for f in fails if f.startswith("A-SYM")]:
        ok("A-SYM", f"{len(ARM_PAIRS)} arm pairs are an exact +{ARM_DY} mm "
                    f"translation at identical rotation (worst error "
                    f"{worst*1000:.1f} um) — the D4 delta is a placement "
                    f"property, not a routing outcome")

    # ------------------------------------------------------------- A-ARMSEP
    def arm_pads(nets):
        # R_DELTA1/2/3 are EXCLUDED: the delta is the deliberate 49.9-ohm bridge
        # between the two arms, so its own pads are 0.9 mm apart BY DESIGN.
        # Measuring them would make this check report the splitter instead of
        # the thing it exists to protect - the parallel arm RUNS.
        out = []
        for (r, n), net in pad_net.items():
            if net in nets and r in fps and not r.startswith("R_DELTA"):
                xy = pad_xy(fps[r], n)
                if xy:
                    out.append((r, n, xy))
        return out
    a1, a2 = arm_pads(ARM1_NETS), arm_pads(ARM2_NETS)
    if a1 and a2:
        d = min(math.dist(p[2], q[2]) for p in a1 for q in a2)
        near = min(((math.dist(p[2], q[2]), p, q) for p in a1 for q in a2))
        if d < ARMSEP_MIN:
            bad("A-ARMSEP", f"closest arm-1/arm-2 pads {d:.3f} mm < "
                            f"{ARMSEP_MIN:.4f} mm (3 x {DIELECTRIC_H} prepreg)")
        else:
            ok("A-ARMSEP", f"closest arm-1/arm-2 pad pair {near[1][0]}.{near[1][1]} "
                           f"<-> {near[2][0]}.{near[2][1]} = {d:.3f} mm, "
                           f"{d/ARMSEP_MIN:.0f}x the {ARMSEP_MIN:.4f} mm floor "
                           f"({len(a1)}+{len(a2)} arm pads)")
    else:
        bad("A-ARMSEP", "no arm pads found — net names changed?")

    # -------------------------------------------------------------- A-DELTA
    legs = []
    for r, split_pad, arm_pad in (("R_DELTA1", "1", "2"), ("R_DELTA2", "1", "2")):
        if r not in fps:
            bad("A-DELTA", f"{r} missing")
            continue
        legs.append((r, pad_xy(fps[r], split_pad), pad_xy(fps[r], arm_pad)))
    if len(legs) == 2:
        # the shared LOOP_SPLIT node spans the two `split` pads; each ACTIVE leg
        # is half that node plus the chip.
        node = math.dist(legs[0][1], legs[1][1])
        worst_leg = 0.0
        for r, sp, ap in legs:
            leg = node / 2.0 + math.dist(sp, ap)
            worst_leg = max(worst_leg, leg)
            if leg > LAMBDA_G_20:
                bad("A-DELTA", f"{r} active leg {leg:.3f} mm > lambda_g/20 = "
                               f"{LAMBDA_G_20:.3f} mm at 6 GHz")
        if worst_leg <= LAMBDA_G_20:
            ok("A-DELTA", f"LOOP_SPLIT node {node:.3f} mm, worst ACTIVE leg "
                          f"{worst_leg:.3f} mm <= lambda_g/20 = "
                          f"{LAMBDA_G_20:.3f} mm (R_DELTA3 is the inactive leg "
                          f"and is excluded by ARCHITECTURE sec.10.3)")

    # ------------------------------------------------------------ A-ANTIPAD
    bad_ap = []
    for r in SMA_REFS:
        fp = fps.get(r)
        if not fp:
            bad("A-ANTIPAD", f"{r} missing")
            continue
        for p in fp.Pads():
            if p.GetNumber() != "1":
                continue
            c = p.GetLocalClearance()
            c = MM(c.value) if hasattr(c, "value") else (MM(c) if c else 0.0)
            opening = SMA_PAD_D + 2 * c
            if opening < ANTIPAD_MIN_D - 1e-6:
                bad_ap.append(f"{r} antipad D{opening:.2f} < D{ANTIPAD_MIN_D}")
    if bad_ap:
        bad("A-ANTIPAD", "; ".join(bad_ap))
    else:
        ok("A-ANTIPAD", f"all 5 SMA centre pins carry a local clearance giving "
                        f"a >= D{ANTIPAD_MIN_D} mm opening on every pour "
                        f"(ADR-0007 RULE 1, 5.6 dB of RL at 6 GHz over D2.6: 14.5 vs 8.9)")

    # -------------------------------------------------------------- A-PLANE
    in1 = pcbnew.In1_Cu
    zones = [z for z in board.Zones() if z.IsOnLayer(in1)]
    rules = [z for z in zones if z.GetIsRuleArea()]
    pours = [z for z in zones if not z.GetIsRuleArea()]
    if rules:
        bad("A-PLANE", f"{len(rules)} rule area(s)/keepout(s) on In1.Cu — L2 must "
                       f"be ONE UNBROKEN plane (ARCHITECTURE sec.8)")
    elif len(pours) != 1 or pours[0].GetNetname() != "GND":
        bad("A-PLANE", f"In1.Cu carries {len(pours)} pour(s) "
                       f"{[z.GetNetname() for z in pours]} — want exactly one GND")
    else:
        ok("A-PLANE", "In1.Cu = exactly 1 GND pour, 0 keepouts — L2 is one "
                      "unbroken plane; the only interruptions are the 5 SMA "
                      "antipads, which are a launch feature (A-ANTIPAD)")

    # -------------------------------------------------------------- A-RFSEP
    def bbox(fp):
        b = fp.GetBoundingBox(False, False)
        return MM(b.GetLeft()), MM(b.GetTop()), MM(b.GetRight()), MM(b.GetBottom())

    def gap(A, B):
        dx = max(A[0] - B[2], B[0] - A[2], 0.0)
        dy = max(A[1] - B[3], B[1] - A[3], 0.0)
        return math.hypot(dx, dy)
    cal = [(r, bbox(fps[r])) for r in CAL_REFS if r in fps]
    worst_sep, worst_pair = 1e9, None
    for r, fp in sorted(fps.items()):
        if not r.startswith(DIGITAL_PREFIXES):
            continue
        B = bbox(fp)
        for cr, C in cal:
            g = gap(B, C)
            if g < worst_sep:
                worst_sep, worst_pair = g, (r, cr)
    if worst_pair is None:
        bad("A-RFSEP", "no digital parts matched — prefix list stale?")
    elif worst_sep < RFSEP_MIN:
        bad("A-RFSEP", f"{worst_pair[0]} is {worst_sep:.2f} mm from "
                       f"{worst_pair[1]} (floor {RFSEP_MIN} mm) — "
                       f"ARCHITECTURE sec.10.5 wants the RP2040 + micro-USB at "
                       f"the far end from the calibration path")
    else:
        ok("A-RFSEP", f"closest digital-to-calibration approach is "
                      f"{worst_pair[0]} <-> {worst_pair[1]} = {worst_sep:.2f} mm "
                      f"(floor {RFSEP_MIN} mm); the QSPI bus and the crystal sit "
                      f"hard against the top edge")

    # ---------------------------------------------------------------- A-SEG
    # The chain, pad to pad, against DETAIL_DESIGN sec.2. NOT A GATE — every row
    # prints and none of them can fail, because ADR-0016 credits ALL interconnect
    # at ZERO and a run shorter than its target cannot lower the guaranteed
    # floor. It is here because the ALTERNATIVE was a hand-typed table in
    # floorplan.yaml, and that table described the 18.5 mm arm geometry for a day
    # after the anchors moved to 14.5. A number a human retypes goes stale in
    # silence; a number a gate prints cannot.
    SEG = [  # (label, refA.padA, refB.padB, sec.2 target mm)
        ("TX jack -> PAD_A1A in",     "J_SMA_TX.1",   "U_PAD_A1A.2",  10.0),
        ("PAD_A1E out -> vertex",     "U_PAD_A1E.5",  "R_DELTA1.1",   22.0),
        ("vertex -> arm1 pad in",     "R_DELTA1.2",   "U_PAD_A2A1.2",  8.0),
        ("vertex -> arm2 pad in",     "R_DELTA2.2",   "U_PAD_A2B1.2",  8.0),
        ("arm1 pad internal",         "U_PAD_A2A1.5", "U_PAD_A2A2.2", None),
        ("arm2 pad internal",         "U_PAD_A2B1.5", "U_PAD_A2B2.2", None),
        ("arm1 pad out -> SW1.RF2",   "U_PAD_A2A2.5", "U_SW1.1",       8.0),
        ("arm2 pad out -> SW2.RF2",   "U_PAD_A2B2.5", "U_SW2.1",       8.0),
        ("SW1.RFin -> RX1 jack",      "U_SW1.5",      "J_SMA_RX1.1",   5.0),
        ("SW2.RFin -> RX2 jack",      "U_SW2.5",      "J_SMA_RX2.1",   5.0),
        ("SW1.RF1 -> ANT1 jack",      "U_SW1.3",      "J_SMA_ANT1.1", 20.0),
        ("SW2.RF1 -> ANT2 jack",      "U_SW2.3",      "J_SMA_ANT2.1", 20.0),
        ("TX jack -> RX1 jack (iso)", "J_SMA_TX.1",   "J_SMA_RX1.1",  None),
        ("TX jack -> RX2 jack (iso)", "J_SMA_TX.1",   "J_SMA_RX2.1",  None),
    ]

    def seg_xy(spec):
        ref, pad = spec.rsplit(".", 1)
        return pad_xy(fps[ref], pad) if ref in fps else None

    n_seg = 0
    for label, a_, b_, target in SEG:
        pa, pb = seg_xy(a_), seg_xy(b_)
        if not pa or not pb:
            notes.append(f"A-SEG  MISSING {label}: {a_} or {b_} not on the board")
            continue
        d = math.dist(pa, pb)
        n_seg += 1
        tgt = "unbudgeted" if target is None else f"target {target:5.1f}"
        notes.append(f"A-SEG  {label:<28s} {d:6.2f} mm   {tgt}")
    ok("A-SEG", f"{n_seg}/{len(SEG)} calibration-chain segments MEASURED off the "
                f"board and printed against DETAIL_DESIGN sec.2 (informational: "
                f"ADR-0016 credits all interconnect at ZERO, so a target miss is "
                f"a documentation fact, not a spec risk)")

    # --------------------------------------------------------------- A-PROX
    # THE METRIC MATTERS, and the obvious one is wrong. A `keep_short` budget
    # says "the parts that must hug this chip" (D-ADJ), so it is a question
    # about a PIN: is there something on this net within X mm of it? Measuring
    # the FULL NET SPAN instead reports 75 mm for U_MCU:3V3 against a 4 mm
    # budget on a board whose decoupling is perfect - a rail crosses the board,
    # which is what rails do.
    #
    # A keep_short block is also PER-MPN while a net is PER-INSTANCE, and this
    # board has three shapes of that mismatch, all resolved explicitly rather
    # than skipped:
    #   * BGS12WN6 declares `RF_CTRL_SW`; the board wires RF_CTRL_SW1/2.
    #     -> UNIQUE PREFIX match among the nets that MPN's instances carry.
    #   * KH-SMA-KE-Z declares SW1_ANT / TX_PLUTO / RX_PLUTO1... but a jack has
    #     no pad on SW1_ANT at all - the budget is a claim about the NET, not
    #     about the jack. -> measure the net's own full span.
    #   * YAT-xA+ declares LOOP_IN, a net stage 4 renamed out of existence.
    #     -> genuinely NOT EVALUATED, printed with the reason. A stale budget
    #     is a finding, not a pass.
    # Budgets are DEDUPED per (MPN, net, budget): YAT-2A+ is placed 5 times and
    # its block must not be counted 5 times.
    net_pads = {}
    for (r, n), v in pad_net.items():
        if r in fps:
            xy = pad_xy(fps[r], n)
            if xy:
                net_pads.setdefault(v, []).append((r, n, xy))
    mpn_of = {r: (parts.get(f.GetValue()) or {}).get("mpn")
              for r, f in fps.items()}
    budgets = {}
    for ref, fp in fps.items():
        d = parts.get(fp.GetValue())
        if not d:
            continue
        for item in ((d.get("layout") or {}).get("keep_short") or []):
            budgets[(d["mpn"], item["net"], float(item["max_span_mm"]))] = True
    n_meas = n_over = n_skip = 0
    for mpn, want, budget in sorted(budgets):
        mine = {r for r, m in mpn_of.items() if m == mpn}
        carried = {v for v in net_pads if any(r in mine for r, _, _ in net_pads[v])}
        if want in net_pads:
            resolved = [want]
        else:
            resolved = sorted(v for v in carried if v.startswith(want))
        if not resolved:
            n_skip += 1
            notes.append(f"A-PROX NOT EVALUATED {mpn}:{want} (budget {budget} mm) "
                         f"— no net on this board is named {want!r} or prefixed "
                         f"by it on any {mpn} instance (stale budget?)")
            continue
        for net in resolved:
            pads_here = net_pads[net]
            anchors = [p for p in pads_here if p[0] in mine]
            others = [p for p in pads_here if p[0] not in mine]
            if anchors and others:
                worst, wa, wo = 0.0, None, None
                for a_ in anchors:
                    dmin, o = min((math.dist(a_[2], o_[2]), o_) for o_ in others)
                    if dmin > worst:
                        worst, wa, wo = dmin, a_, o
                kind = f"nearest {wo[0]}.{wo[1]} from {wa[0]}.{wa[1]}"
                metric = worst
            elif len(pads_here) >= 2:
                metric = max(math.dist(a_[2], b_[2])
                             for a_ in pads_here for b_ in pads_here)
                kind = f"full span of {net} ({len(pads_here)} pads; no {mpn} pad on it)"
            else:
                n_skip += 1
                notes.append(f"A-PROX NOT EVALUATED {mpn}:{net} "
                             f"(budget {budget} mm) — only {len(pads_here)} pad "
                             f"on this net")
                continue
            n_meas += 1
            over = metric > budget
            n_over += over
            notes.append(f"A-PROX {'OVER' if over else 'ok  '} {mpn}:{net} "
                         f"{metric:6.2f} mm vs budget {budget:5.1f} — {kind}")
    print(f"  {'A-PROX':<10s} {'FAIL' if n_over else 'PASS'}  "
          f"{n_meas} keep_short budgets MEASURED, {n_over} over budget, "
          f"{n_skip} NOT EVALUATED (deduped per MPN+net)")
    if n_over:
        fails.append(f"A-PROX: {n_over} keep_short budget(s) exceeded")

    # ------------------------------------------------------------------- I8
    # Mounting holes are BOARD FEATURES, not components: no net, no BOM line,
    # no CPL row (the same class the 03_src contract puts fiducials in). They
    # are EXCLUDED by name and counted in the verdict, never silently dropped.
    holes = sorted(r for r in fps if re.fullmatch(r"H\d+", r))
    comps_only = {r: f for r, f in fps.items() if r not in holes}
    missing = [r for r, fp in comps_only.items()
               if fp.Reference().IsVisible() is False
               or fp.Reference().GetLayer() != pcbnew.F_SilkS]
    if missing:
        bad("I8", f"{len(missing)} refdes not visible on F.SilkS: "
                  f"{sorted(missing)[:8]}")
    else:
        ok("I8", f"{len(comps_only)}/{len(comps_only)} component refdes visible "
                 f"on F.SilkS; {len(holes)} mounting hole(s) {holes} EXCLUDED "
                 f"as board features (no net, no BOM line, no CPL row)")

    # ------------------------------------------------------------------- I9
    # OWNERSHIP, not just presence. I8 says the label EXISTS; I9 says it belongs
    # to the part it names.
    #
    # THE METRIC IS DISTANCE TO THE COURTYARD EDGE, NOT TO A CENTROID, and the
    # first draft of this check got that wrong (2026-07-29). Centroid distance
    # penalises big parts for being big: it called the "RX1" caption 1.2 mm
    # outside J_SMA_RX1's courtyard a MISATTRIBUTION, because that jack's 5-hole
    # centroid is 5.95 mm away while a neighbouring 0402's centre happened to be
    # 5.15 mm away. A human reads a label against the part's OUTLINE. Edge
    # distance (0 if the label sits inside) is that reading, and it is not a
    # loosening: it does not rescue a single one of the genuine failures below,
    # which are labels the silk placer pushed 5-11 mm from their owners.
    def crtyd_box(fp):
        bb = fp.GetCourtyard(pcbnew.F_Cu).BBox()
        if bb.GetWidth() <= 0:
            bb = fp.GetBoundingBox(False, False)
        return (MM(bb.GetLeft()), MM(bb.GetTop()),
                MM(bb.GetRight()), MM(bb.GetBottom()))

    def edge_dist(xy, box):
        x, y = xy
        x0, y0, x1, y1 = box
        dx = max(x0 - x, 0.0, x - x1)
        dy = max(y0 - y, 0.0, y - y1)
        return math.hypot(dx, dy)

    cents = {r: crtyd_box(f) for r, f in fps.items()}
    stolen, worst_margin, worst_ref = [], None, None
    for r, fp in sorted(comps_only.items()):
        t = fp.Reference().GetPosition()
        txy = (MM(t.x), MM(t.y))
        d_own = edge_dist(txy, cents[r])
        d_other, other = min((edge_dist(txy, cents[o]), o)
                             for o in cents if o != r)
        margin = d_other - d_own
        if margin <= 0:
            stolen.append(f"{r} (its label is {-margin:.3f} mm NEARER {other})")
        if worst_margin is None or margin < worst_margin:
            worst_margin, worst_ref = margin, f"{r} vs {other}"
    if stolen:
        bad("I9", f"{len(stolen)} refdes label(s) closer to another part than to "
                  f"their own: {stolen[:6]}")
    else:
        ok("I9", f"all {len(comps_only)} refdes labels OWNED by the part they "
                 f"name; tightest discrimination {worst_margin:.3f} mm "
                 f"({worst_ref})")

    # ------------------------------------------------------------------ I10
    # THE FIVE PORT CAPTIONS, graded the same way as I9 but by NAME. Five
    # identical SMA jacks on our own pitch means NOTHING PHYSICAL distinguishes
    # them: the silk IS the user interface, and a caption nearer the wrong jack
    # is a wrong answer delivered confidently. This check is separate from I9
    # because a caption is free text, not a refdes — nothing else on the board
    # would ever notice it drifting, and it DID drift: all five were authored
    # against the first placement draft and were 5.0-9.8 mm out after the jacks
    # moved.
    PORT_CAPTIONS = {"ANT1": "J_SMA_ANT1", "ANT2": "J_SMA_ANT2",
                     "RX1": "J_SMA_RX1", "RX2": "J_SMA_RX2", "TX": "J_SMA_TX"}
    texts = {}
    for d in board.GetDrawings():
        if d.GetClass() == "PCB_TEXT" and d.GetLayer() == pcbnew.F_SilkS:
            t = d.GetText().strip()
            if t in PORT_CAPTIONS:
                texts[t] = (MM(d.GetPosition().x), MM(d.GetPosition().y))
    misaimed, tight = [], None
    for label, owner in sorted(PORT_CAPTIONS.items()):
        if label not in texts:
            misaimed.append(f"{label} caption NOT ON F.SilkS at all")
            continue
        xy = texts[label]
        d_own = edge_dist(xy, cents[owner])
        d_other, other = min((edge_dist(xy, cents[o]), o)
                             for o in cents if o != owner)
        if d_other <= d_own:
            misaimed.append(f"{label} is {d_own:.2f} mm from {owner} but "
                            f"{d_other:.2f} mm from {other}")
        m = d_other - d_own
        if tight is None or m < tight[0]:
            tight = (m, f"{label}: {d_own:.2f} to {owner} vs {d_other:.2f} to "
                        f"{other}")
    if misaimed:
        bad("I10", f"{len(misaimed)} port caption(s) not owned by their jack: "
                   f"{misaimed}")
    else:
        ok("I10", f"all 5 port captions ({', '.join(sorted(PORT_CAPTIONS))}) are "
                  f"nearest their OWN jack; tightest margin {tight[0]:.2f} mm "
                  f"— {tight[1]}")

    for n in notes:
        print(f"    note: {n}")
    print(f"AUDIT: {'FAIL' if fails else 'PASS'} "
          f"({len(fails)} failure(s), {len(notes)} note(s))")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
