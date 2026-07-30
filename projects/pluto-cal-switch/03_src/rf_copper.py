#!/usr/bin/env python3
"""rf_copper — the calibration chain's copper: a PLANNER, not an emitter.

    /usr/bin/python3 03_src/rf_copper.py <board.kicad_pcb>          # verify
    /usr/bin/python3 03_src/rf_copper.py <board.kicad_pcb> --emit    # + YAML

This file PLANS and VERIFIES geometry and prints it as a `stitch.seed_stubs:`
block for `03_src/route.yaml`. **IT NEVER WRITES COPPER.** The copper is placed
by the SHARED backend from that config, so the whole recipe for this board's
chain is expressible in `route.yaml` and a rebuild replays it through the normal
prep -> route -> import -> stitch path (canon M3). That is exactly the division
`stitch.seed_stubs` was promoted for: its own docstring cites usb-hub-3s's
`03_src/plan_seed_stubs.py` (the PLANNER, bespoke, per board) plus
`add_seed_stubs.py` (the EMITTER, now the shared `p_seed_stubs` pass). This is
the planner half.

A first version of this file wrote tracks into the route-prep board directly.
That produced identical copper and was still WRONG: a chain whose recipe is not
in `route.yaml` is a canon-M3 violation wearing a green gate, because the next
rebuild reproduces the board only if somebody remembers the extra step.

BESPOKE TO THIS BOARD, DELIBERATELY (canon M8, two-strike promotion). One
strike. `pluto-rx2-8way`'s radial star does not need this — its nine arms are a
rotational fan with no shared splitter and no per-net transform problem — and
nothing else in the fleet publishes a phase delta. Promote to
`skills/kicad-pcb/scripts/` only when a SECOND board needs it, and not before.

===========================================================================
WHY THE ARMS ARE NOT ROUTED
===========================================================================
This board's release artifact IS a number: BRIEF D4 / ADR-0011 ship the routed
electrical length of each loopback arm and the arm-to-arm DELTA, converted to
picoseconds against a constant pinned to the ordered stackup, so the Pluto's
calibration can software-offset a KNOWN quantity. At 6 GHz on JLC04161H-7628
phase runs at 13.25 deg/mm (lambda_g 27.17 mm, t_pd 6.135 ps/mm, eps_eff
3.383), so ONE MILLIMETRE of unmatched copper is the size of a whole phase
budget.

KRT IS STOCHASTIC BY CONTRACT (its own CLAUDE.md: "outputs carry per-run random
UUIDs", and `route_and_stitch_generic.race` exists precisely because two runs of
the same board differ measurably). Two independently-routed arms will not match,
and re-running the pipeline would silently change the published picoseconds. So
the arms are not routed at all: they are CONSTRUCTED, and their congruence is an
arithmetic property of the construction rather than an outcome to be measured
and hoped for. `copper_length_audit.py` (canon R-LEN) then grades the result off
the shipped bytes with an independent s-expression reader, and
`length_match.RF_LOOP_D4.pin` in `03_src/rules/nets.yaml` FAILS if it ever moves.

KRT still routes everything else, and it treats this copper as OBSTACLES
(`track_cells`, `segment_blocked_cells_array`) — pre-laid tracks are respected,
never clobbered. That is why this pass runs on the route-prep output, before the
first wave.

===========================================================================
THE TRANSFORM IS PER-NET, AND THAT IS THE WHOLE FINDING OF THIS FILE
===========================================================================
`03_src/audit_board.py` A-SYM reports, at PASS, "11 arm pairs are an exact
+14.5 mm translation at identical rotation (worst error 0.0 um)", and its own
message calls ARM_DY the congruence vector. Building arm 2 as arm 1 translated
by (0, +14.5) is the obvious move, and it is WRONG. So is building it as a
reflection. MEASURED off the placed board:

  * every arm part whose pads sit at y = 47.750 / 62.250 is congruent under
    BOTH maps, but only by coincidence: 62.250 = 2*55.000 - 47.750, so for
    those pads the reflection y -> 110.0 - y and the translation +14.5 ARE THE
    SAME MAP. That is the entire population A-SYM grades, which is why A-SYM
    cannot see the difference.
  * THE SPLITTER RESISTORS ARE REFLECTED, NOT TRANSLATED.
        LOOP_ARM1  R_DELTA1.2 (64.000, 53.670)   R_DELTA3.1 (62.400, 54.550)
        LOOP_ARM2  R_DELTA2.2 (64.000, 56.330)   R_DELTA3.2 (62.400, 55.450)
    +14.5 sends 53.670 -> 68.170, where there is no pad. y -> 110.0 - y sends
    53.670 -> 56.330 and 54.550 -> 55.450, exactly. ADR-0011's own words are
    "mirror images about the splitter axis".
  * THE SWITCHES ARE TRANSLATED, NOT REFLECTED. U_SW1 sits at y 47.950 and
    U_SW2 at 62.450: +14.5, where a reflection would give 62.050. Their pin-1
    lands still coincide (47.750 -> 62.250 under both), but the SECOND PAD ROW
    does not: U_SW1.6 is at 48.150 and U_SW2.6 at 62.650, while a reflection
    would put arm 2's neighbour at 61.850 — on the OTHER SIDE of the land the
    arm has to enter. A reflected arm-2 entry point lands 0.010 mm from
    U_SW2.6 against a 0.150 mm floor. Measured, refused, and the reason this
    file has a `xf` column.

The cause is structural, not an error: ADR-0011 sec.3 REQUIRES the arm passives
at identical rotation (mirrored fillets and pick orientation turn mounting
inductance into calibration error), which forces translation, while the delta
splitter forces reflection. The two symmetries coexist because every part
between them happens to have a pad set symmetric about the arm axis. The switch
is the sole exception.

SO THE CONSTRUCTION USES A DIFFERENT ISOMETRY PER NET, chosen so the image
lands on the pads arm 2 actually has:

    LOOP_ARM1  -> LOOP_ARM2       REFLECT   (the splitter end)
    PAD_A2A_1  -> PAD_A2B_1       TRANSLATE (either; they coincide)
    LOOP_ARM1_SW -> LOOP_ARM2_SW  TRANSLATE (the switch end)

Both are isometries, so the SUM of the member lengths is equal to the
nanometre either way, which is the only property the published delta depends
on. All arithmetic is done in INTEGER NANOMETRES (reflection is
y' = 110_000_000 - y) so the equality is exact, not rounded: the two members
agree bit for bit, and the pin in nets.yaml is 0.000 mm with 0.010 mm of
tolerance.

===========================================================================
WHAT IS VERIFIED BEFORE ANY COPPER IS WRITTEN (refuse whole, never shave)
===========================================================================
  1. LANDING — every path terminal lies inside the declared `REF.PAD`, and
     that pad is on the path's net. A terminal that misses its land, or a
     ref/pad that does not exist, is a hard error. (This is what would have
     caught the reflected switch entry as a WRONG PAD rather than as a DRC
     finding three steps later.)
  2. CLEARANCE — every segment of BOTH channels is probed against the live
     board's exact copper via `pcb_toolkit.Toolkit.collides` at the board's
     0.15 mm floor, plus an explicit drilled-hole probe at the 0.25 mm
     hole_clearance floor (Toolkit's own hole probe floors at 0.20). Arm 2 is
     checked against the REAL board, never assumed from arm 1's result — the
     switch finding above is exactly what that check is for.
  3. WIDTH — every segment is at or above its netclass floor, except where a
     `scoped_floors:` rule area in `03_src/rules/nets.yaml` licenses a taper,
     and then the whole necked segment must lie INSIDE that rule area.
  4. GEOMETRY — F.Cu only, zero vias, zero arcs. ADR-0011 forbids a layer
     change in either arm; `no_vias: true` in the length_match block grades
     the result independently.
  5. CONGRUENCE — the two members' total lengths are compared in nanometres
     and must be EQUAL. Not "within tolerance": equal.
  6. GRID — every coordinate survives `p_seed_stubs`'s `round(v, 3)` (it
     quantises to 1 um). Checked here, because a coordinate that moves at
     emit time is a coordinate whose congruence was never real.

`p_seed_stubs` then re-checks (1), (2) and idempotence AGAINST THE POST-ROUTE
BOARD when it places the copper, and REFUSES whole on any collision. So the
geometry is verified twice against two different board states — here against
the track-free board, there against the routed one — which is the point of
splitting the planner from the emitter.

Nothing here is measured by the same method that grades it (canon M1): this
file writes through pcbnew, `copper_length_audit.py` reads the saved text with
its own scanner, and `kicad-cli pcb drc` is the arbiter of clearance.
"""
import argparse
import math
import re
import sys
from pathlib import Path

import pcbnew
import yaml

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent
sys.path.insert(0, str(PROJ.parent.parent / "skills" / "kicad-pcb" / "scripts"))
from pcb_toolkit import Toolkit                                  # noqa: E402

NM = 1_000_000                    # nm per mm (KiCad's internal unit)
MIRROR_Y_NM = 110_000_000         # y' = MIRROR_Y - y : reflection about y=55.000
ARM_DY_NM = 14_500_000           # (0, +14.5 mm) : the A-SYM congruence vector
CLR_MM = 0.15                     # nets.yaml default_clearance
HOLE_CLR_MM = 0.20                # floorplan.yaml design_rules.hole_clearance
#: extra margin on the User.2 corridors reserved from KRT, beyond half-width +
#: clearance. 0.125 mm = one KRT grid step (0.1) plus a rounding allowance.
KEEPOUT_SLACK = 0.125


def mm2nm(v):
    """mm -> integer nm. round(), not int(): 47.75*1e6 is 47749999.999… in
    binary floating point and int() would truncate a pad landing by 1 nm."""
    return int(round(float(v) * NM))


# ===========================================================================
# THE DECLARATION. Every coordinate is a PAD CENTRE or a corner chosen against
# a measured clearance; the derivations are in the comments beside them.
# ===========================================================================
#   net1  : the channel-1 net
#   net2  : the channel-2 net, or None for a single-channel run
#   xf    : "R" reflect (y -> 110.0-y) | "T" translate (+14.5 mm) | None
#   w     : track width in mm
#   pts   : the polyline, channel-1 coordinates, mm
#   ends  : (REF.PAD at pts[0], REF.PAD at pts[-1]); None where the polyline
#           joins another polyline of the same net rather than landing
#   ends2 : the same for channel 2, DECLARED rather than derived. Deriving it
#           by refdes substitution is what a first draft of this file did, and
#           the board refused it immediately: R_DELTA3 is ONE part bridging
#           both arms, so arm 1 lands on its pad 1 and arm 2 on its pad 2 —
#           the PAD NUMBER changes, not the refdes. Declaring both sides means
#           check (1) grades a stated intent instead of a guess.
PATHS = [
    # ---------------------------------------------------------------- antenna
    # jack centre pin straight to the DC block. 13.300 mm, which is what A-SEG
    # measures pad-to-pad, so the run is exactly the placement's own budget.
    dict(net1="RX_ANT1", net2="RX_ANT2", xf="T", w=0.36,
         pts=[(32.350, 47.750), (45.650, 47.750)],
         ends=("J_SMA_ANT1.1", "C_DCBLK1.1"),
         ends2=("J_SMA_ANT2.1", "C_DCBLK2.1")),
    # DC block to the switch RF1 land. The landing is NOT the pad centre:
    # U_SW1.3 is a 0.250 mm land with GND (pad 2) 0.400 mm east and 3V3_SW
    # (pad 4) 0.400 mm south, and a 0.35 mm track's round end-cap (r 0.175)
    # centred on the pad centre would sit 0.100 mm from both. Landing at
    # (52.250, 47.650) — inside the land, 0.025 mm from its west and north
    # edges — puts both at 0.375 mm centre-to-edge = 0.200 mm of clearance.
    # The 0.100 mm of slope over 5.7 mm is 1.0 deg of trace angle.
    dict(net1="SW1_ANT", net2="SW2_ANT", xf="T", w=0.36,
         pts=[(46.550, 47.750), (52.250, 47.650)],
         ends=("C_DCBLK1.2", "U_SW1.3"),
         ends2=("C_DCBLK2.2", "U_SW2.3")),
    # ------------------------------------------------------- switch RFC -> RX
    # THE ONE TAPER ON THE RF CHAIN. U_SW1.5 is the BGS12WN6's RFC port and the
    # MIDDLE pad of its second row: 3V3_SW at -0.400 mm and RF_CTRL_SW1 at
    # +0.400 mm in x, both 0.250 mm lands. Widest track that can land on it at
    # 0.15 mm clearance is 0.250 mm (w/2 <= 0.275 - 0.150) against RF50's
    # 0.350 mm floor — see nets.yaml scoped_floors for the measurement and the
    # impedance argument. 0.22 mm realizes 0.165 mm. The neck is 0.450 mm long
    # = lambda_g/61 at 6 GHz, and it lies entirely inside the `taper_u_sw1`
    # rule area (y 47.98..49.20), which is what licenses it in the .kicad_dru.
    dict(net1="RX_PLUTO1", net2="RX_PLUTO2", xf="T", w=0.22,
         pts=[(52.750, 48.150), (52.750, 48.600)],
         ends=("U_SW1.5", None), ends2=("U_SW2.5", None)),
    # back to the impedance width for the remaining 8.550 mm. At y = 48.600 the
    # 0.35 mm cap is 0.251 mm from the pad-4/pad-6 corners.
    dict(net1="RX_PLUTO1", net2="RX_PLUTO2", xf="T", w=0.36,
         pts=[(52.750, 48.600), (52.750, 57.150)],
         ends=(None, "J_SMA_RX1.1"), ends2=(None, "J_SMA_RX2.1")),
    # ------------------------------------------------- the resistive splitter
    # LOOP_SPLIT is ONE net feeding BOTH arms, so its own copper is a
    # differential term on the published delta if it is not symmetric. It is
    # therefore built as a T on the axis: one run west along y = 55.000 (the
    # axis itself, and U_PAD_A1E.5 sits exactly on it) to the vertex at
    # x = 64.000, then two 0.430 mm stubs of EQUAL length north and south into
    # R_DELTA1.1 and R_DELTA2.1. The axis run threads the 0.400 mm gap between
    # those two same-net lands (pad edges 54.800 and 55.200) and needs no
    # clearance there at all. This is a branch vertex, which is why LOOP_SPLIT
    # is NOT a member of the length_match group — the group starts at
    # R_DELTAn.2, where each arm becomes its own net.
    dict(net1="LOOP_SPLIT", net2=None, xf=None, w=0.36,
         pts=[(69.503, 55.000), (64.000, 55.000), (64.000, 54.570)],
         ends=("U_PAD_A1E.5", "R_DELTA1.1")),
    dict(net1="LOOP_SPLIT", net2=None, xf=None, w=0.36,
         pts=[(64.000, 55.000), (64.000, 55.430)],
         ends=(None, "R_DELTA2.1")),
    # ------------------------------------------------------ THE MATCHED ARMS
    # LOOP_ARMn is a THREE-pad net: R_DELTA3 (the delta's bridge leg, ADR-0003)
    # lands on it as well as R_DELTAn.2 and U_PAD_A2x1.2. It is laid as a DAISY
    # CHAIN — bridge -> series resistor -> attenuator — so the copper graph has
    # ZERO branch vertices and `topology: chain` is satisfiable; a T here would
    # make the whole group R-LEN-UNREACHED, because "the length" of a branching
    # net is genuinely ambiguous and the gate refuses to guess.
    #
    # The dogleg is FORCED, not stylistic: U_PAD_A2A1.2 (64.000, 47.750) has
    # GND lands directly above AND below it spanning the same x 63.600..64.400
    # (pads 1 and 3, 0.650 mm away), so the ONLY approach is from due east, and
    # x >= 64.725 is the first vertical corridor that clears them at 0.15 mm.
    # x = 64.900 gives 0.325 mm, matching the 0.325 mm the horizontal entry has
    # to pads 1 and 3 — the whole approach is uniformly clear. The corners are
    # 45 deg mitres rather than square: a 45 deg entry straight into the land
    # would pass 0.071 mm from pad 1's corner and is refused by check (2).
    dict(net1="LOOP_ARM1", net2="LOOP_ARM2", xf="R", w=0.36,
         pts=[(62.400, 54.550),    # R_DELTA3.1, the bridge leg
              (64.000, 53.670),    # R_DELTA1.2, passed THROUGH (same net)
              (64.500, 53.670),
              (64.900, 53.270),    # 45 deg mitre
              (64.900, 48.150),
              (64.500, 47.750),    # 45 deg mitre, clears pad 1 by 0.424 mm
              (64.000, 47.750)],   # U_PAD_A2A1.2
         ends=("R_DELTA3.1", "U_PAD_A2A1.2"),
         ends2=("R_DELTA3.2", "U_PAD_A2B1.2")),
    # between the two YAT chips of the 11.9 dB arm attenuator. Straight.
    dict(net1="PAD_A2A_1", net2="PAD_A2B_1", xf="T", w=0.36,
         pts=[(62.126, 47.750), (60.927, 47.750)],
         ends=("U_PAD_A2A1.5", "U_PAD_A2A2.2"),
         ends2=("U_PAD_A2B1.5", "U_PAD_A2B2.2")),
    # attenuator out to switch RF2. Lands at (53.250, 47.650) for the same
    # reason SW1_ANT lands off-centre, mirrored in x: GND (pad 2) is 0.400 mm
    # WEST and RF_CTRL_SW1 (pad 6) 0.400 mm south, so the pad's south-east
    # corner is the only clear entry — 0.200 mm to both. THIS IS THE NET WHOSE
    # TRANSFORM MUST BE THE TRANSLATION: reflected, the entry would land at
    # y 62.340, which is 0.010 mm from U_SW2.6.
    dict(net1="LOOP_ARM1_SW", net2="LOOP_ARM2_SW", xf="T", w=0.36,
         pts=[(59.053, 47.750), (53.250, 47.650)],
         ends=("U_PAD_A2A2.5", "U_SW1.1"),
         ends2=("U_PAD_A2B2.5", "U_SW2.1")),
    # ----------------------------------- the pre-split PAD_A1 cascade + TX
    # Five MCLP-6 chips in a row on the axis, pin 2 to pin 5, all at y=55.000
    # with their GND lands 0.650 mm off-axis: straight 0.35 mm runs, 1.126 mm
    # each. Single-channel — common-mode to both arms by construction, since
    # this copper is upstream of the splitter vertex.
    dict(net1="PAD_A1_4", net2=None, xf=None, w=0.36,
         pts=[(71.377, 55.000), (72.503, 55.000)],
         ends=("U_PAD_A1E.2", "U_PAD_A1D.5")),
    dict(net1="PAD_A1_3", net2=None, xf=None, w=0.36,
         pts=[(74.377, 55.000), (75.503, 55.000)],
         ends=("U_PAD_A1D.2", "U_PAD_A1C.5")),
    dict(net1="PAD_A1_2", net2=None, xf=None, w=0.36,
         pts=[(77.377, 55.000), (78.503, 55.000)],
         ends=("U_PAD_A1C.2", "U_PAD_A1B.5")),
    dict(net1="PAD_A1_1", net2=None, xf=None, w=0.36,
         pts=[(80.377, 55.000), (81.503, 55.000)],
         ends=("U_PAD_A1B.2", "U_PAD_A1A.5")),
    # the TX launch: 10.003 mm on the axis, threading J_SMA_TX's own GND
    # barrels 1.665 mm either side.
    dict(net1="TX_PLUTO", net2=None, xf=None, w=0.36,
         pts=[(83.377, 55.000), (93.380, 55.000)],
         ends=("U_PAD_A1A.2", "J_SMA_TX.1")),
]

#: the two length_match members, as the gate declares them. Used only to REPORT
#: the constructed lengths; the gate itself re-measures off the saved bytes.
MEMBERS = {"ARM1": ["LOOP_ARM1", "PAD_A2A_1", "LOOP_ARM1_SW"],
           "ARM2": ["LOOP_ARM2", "PAD_A2B_1", "LOOP_ARM2_SW"]}


class Refuse(RuntimeError):
    """A verification failure. Nothing is written; the board is untouched."""


# ---------------------------------------------------------------- transforms
def xform(pts_nm, kind):
    if kind == "R":
        return [(x, MIRROR_Y_NM - y) for x, y in pts_nm]
    if kind == "T":
        return [(x, y + ARM_DY_NM) for x, y in pts_nm]
    raise Refuse(f"unknown transform {kind!r}")


def poly_len_nm(pts_nm):
    """Polyline length. math.dist on integers is exact to double precision;
    at these magnitudes (< 1e8 nm) that is far below 1 nm of error."""
    return sum(math.dist(pts_nm[i], pts_nm[i + 1])
               for i in range(len(pts_nm) - 1))


# ------------------------------------------------------------------- the rules
def netclass_floors():
    """min_width per net from 03_src/rules/nets.yaml, plus the scoped_floors
    relaxations as (net -> [(rule_area_name, min_width)])."""
    doc = yaml.safe_load((PROJ / "03_src" / "rules" / "nets.yaml")
                         .read_text(encoding="utf-8-sig"))
    num = lambda v: float(re.sub(r"[^0-9.]", "", str(v)))       # noqa: E731
    floors, scoped = {}, {}
    for c in (doc.get("classes") or {}).values():
        for n in c["nets"]:
            floors[n] = num(c["min_width"])
    for sf in doc.get("scoped_floors") or []:
        for n in sf.get("nets") or []:
            scoped.setdefault(n, []).append((sf["zone"], num(sf["min_width"])))
    return floors, scoped


def rule_areas(board):
    out = {}
    for z in board.Zones():
        if z.GetIsRuleArea() and z.GetZoneName():
            bb = z.GetBoundingBox()
            out[z.GetZoneName()] = (bb.GetLeft(), bb.GetTop(),
                                    bb.GetRight(), bb.GetBottom())
    return out


# ---------------------------------------------------------------- verification
def pad_of(board, spec, netname):
    ref, num = spec.split(".", 1)
    fp = board.FindFootprintByReference(ref)
    if fp is None:
        raise Refuse(f"{spec}: no footprint {ref} on the board")
    for p in fp.Pads():
        if p.GetNumber() != num:
            continue
        if p.GetNetname() != netname:
            raise Refuse(f"{spec} is on net {p.GetNetname()!r}, not "
                         f"{netname!r} — a landing must never bridge nets")
        if pcbnew.F_Cu not in p.GetLayerSet().Seq():
            raise Refuse(f"{spec} has no F.Cu copper; the arms are F.Cu only")
        return p
    raise Refuse(f"{spec}: footprint {ref} has no pad {num!r}")


def check_landing(board, spec, netname, pt_nm, tag):
    """The terminal must be INSIDE its land. `HitTest` on the pad's own shape,
    not a bbox: a rounded-rect land's corner is not its bounding corner."""
    p = pad_of(board, spec, netname)
    v = pcbnew.VECTOR2I(int(pt_nm[0]), int(pt_nm[1]))
    if not p.HitTest(v, 0):
        c = p.GetPosition()
        raise Refuse(
            f"{tag}: terminal ({pt_nm[0] / NM:.4f}, {pt_nm[1] / NM:.4f}) is "
            f"NOT inside {spec} (land centre {c.x / NM:.4f}, {c.y / NM:.4f}) "
            f"— a landing that misses its pad is an OPEN, not a near miss")
    return p


def hole_probe(tk, board, a_nm, b_nm, w_mm, netcode):
    """Explicit drilled-hole clearance at THIS board's 0.25 mm floor.
    Toolkit.collides probes holes at max(clr, 0.20) and this board's
    design_rules.hole_clearance is 0.25, so its own probe would be 0.05 mm
    looser than the gate — the 'a screen looser than the gate it feeds' shape
    route.yaml already records twice."""
    probe = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(int(a_nm[0]), int(a_nm[1])),
                                 pcbnew.VECTOR2I(int(b_nm[0]), int(b_nm[1])),
                                 pcbnew.FromMM(w_mm))
    clr = pcbnew.FromMM(HOLE_CLR_MM)
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetDrillSizeX() <= 0 or p.GetNetCode() == netcode:
                continue
            if probe.Collide(p.GetEffectiveHoleShape(), clr):
                return f"{f.GetReference()}.{p.GetNumber()} (drilled hole)"
    return None


def verify_path(board, tk, spec, chan, floors, scoped, areas):
    """Everything checked for ONE channel of ONE declared path. Returns its
    length in nm. Raises Refuse on the first failure — never shaves."""
    net_name = spec["net1"] if chan == 1 else spec["net2"]
    tag = f"{net_name} (channel {chan}, w {spec['w']})"
    net = board.FindNet(net_name)
    if net is None:
        raise Refuse(f"{tag}: the board has no net {net_name!r} "
                     f"(canon M-ENTRY / E-NETREF K12)")
    nc = net.GetNetCode()

    pts_nm = [(mm2nm(x), mm2nm(y)) for x, y in spec["pts"]]
    if chan == 2:
        pts_nm = xform(pts_nm, spec["xf"])
    # (6) GRID: p_seed_stubs does round(v, 3) on every coordinate, so a value
    # off the 1 um grid would be MOVED between here and the board and the
    # congruence proved below would be a proof about different geometry.
    for x, y in pts_nm:
        if x % 1000 or y % 1000:
            raise Refuse(f"{tag}: ({x / NM}, {y / NM}) is not on the 1 um grid "
                         f"that stitch.seed_stubs quantises to")

    # (1) LANDING
    ends = spec["ends"] if chan == 1 else spec["ends2"]
    for idx, end in ((0, ends[0]), (-1, ends[1])):
        if end is None:
            continue
        check_landing(board, end, net_name, pts_nm[idx], tag)

    # (3) WIDTH vs the netclass floor, with the scoped relaxation
    floor = floors.get(net_name)
    if floor is None:
        raise Refuse(f"{tag}: no netclass declares this net — an RF run at the "
                     f"0.25 mm Default width is an IMPEDANCE defect")
    if spec["w"] + 1e-9 < floor:
        lic = scoped.get(net_name) or []
        ok = [(z, mw) for z, mw in lic
              if spec["w"] + 1e-9 >= mw and z in areas]
        if not ok:
            raise Refuse(f"{tag}: width {spec['w']} is under the netclass "
                         f"floor {floor} and no scoped_floors rule area "
                         f"licenses it")
        # the WHOLE necked polyline must sit inside the licensing area, or the
        # .kicad_dru relaxation does not cover the copper it was written for
        for zname, _mw in ok:
            x0, y0, x1, y1 = areas[zname]
            if all(x0 <= x <= x1 and y0 <= y <= y1 for x, y in pts_nm):
                break
        else:
            raise Refuse(
                f"{tag}: the taper is licensed by {[z for z, _ in ok]} but the "
                f"necked polyline is not wholly inside any of them — a "
                f"relaxation that does not contain its own copper is a DRC "
                f"finding waiting to happen")

    # (2) CLEARANCE, both copper and holes, against the LIVE board
    for i in range(len(pts_nm) - 1):
        a, b = pts_nm[i], pts_nm[i + 1]
        seg = (a[0] / NM, a[1] / NM, b[0] / NM, b[1] / NM)
        hit = tk.collides(*seg, spec["w"], nc, pcbnew.F_Cu, clr=CLR_MM)
        if hit is not None:
            raise Refuse(
                f"{tag}: segment {i} ({seg[0]:.3f},{seg[1]:.3f})->"
                f"({seg[2]:.3f},{seg[3]:.3f}) collides with "
                f"{_describe(hit)} at the {CLR_MM} mm floor. THIS IS A "
                f"PLACEMENT OR TRANSFORM FINDING, not a reason to shave the "
                f"geometry.")
        hh = hole_probe(tk, board, a, b, spec["w"], nc)
        if hh is not None:
            raise Refuse(f"{tag}: segment {i} is under {HOLE_CLR_MM} mm from "
                         f"{hh}")
    return poly_len_nm(pts_nm)


def _describe(item):
    cls = type(item).__name__
    if cls == "PAD":
        return f"pad {item.GetParentFootprint().GetReference()}." \
               f"{item.GetNumber()} (net {item.GetNetname() or '<none>'})"
    return f"{cls} on net {item.GetNetname() or '<none>'}"


# --------------------------------------------------------------------- driver
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("board")
    ap.add_argument("--emit", action="store_true",
                    help="print the stitch.seed_stubs: YAML block for route.yaml")
    a = ap.parse_args(argv)

    board = pcbnew.LoadBoard(a.board)
    tk = Toolkit(board, clearance_mm=CLR_MM)
    floors, scoped = netclass_floors()
    areas = rule_areas(board)

    rf_nets = set()
    for s in PATHS:
        rf_nets.add(s["net1"])
        if s["net2"]:
            rf_nets.add(s["net2"])

    have = {t.GetNetname() for t in board.GetTracks()} & rf_nets
    if have:
        print(f"rf_copper: NOTE — {len(have)} RF net(s) already carry copper "
              f"on this board ({', '.join(sorted(have))}); the clearance probes "
              f"below therefore include it (same-net copper is not a "
              f"conflict, and p_seed_stubs skips an identical stub).")

    # (4) GEOMETRY is structural: PATHS declares F.Cu polylines and no via
    # emitter exists in this file. Stated, not merely true.
    per_net = {}
    n_seg = 0
    for s in PATHS:
        chans = [1] + ([2] if s["net2"] else [])
        lens = {}
        for ch in chans:
            lens[ch] = verify_path(board, tk, s, ch, floors, scoped, areas)
            name = s["net1"] if ch == 1 else s["net2"]
            per_net[name] = per_net.get(name, 0) + lens[ch]
            n_seg += len(s["pts"]) - 1
        if len(chans) == 2 and lens[1] != lens[2]:
            raise Refuse(
                f"{s['net1']}/{s['net2']}: the transform {s['xf']!r} is not an "
                f"isometry on this path — {lens[1]} nm vs {lens[2]} nm. A "
                f"length-changing transform destroys the published delta.")

    # (5) CONGRUENCE of the two graded members, in nanometres
    tot = {m: sum(per_net[n] for n in nets) for m, nets in MEMBERS.items()}
    if tot["ARM1"] != tot["ARM2"]:
        raise Refuse(f"member totals differ: ARM1 {tot['ARM1']} nm vs ARM2 "
                     f"{tot['ARM2']} nm — the construction did not hold")

    print(f"rf_copper: VERIFIED {len(PATHS)} declared path(s), "
          f"{n_seg} segment(s), {len(rf_nets)} net(s), 0 vias, F.Cu only")
    for n in sorted(per_net):
        print(f"    {n:<14s} {per_net[n] / NM:9.4f} mm")
    d = abs(tot["ARM1"] - tot["ARM2"])
    print(f"  D4 MEMBERS: ARM1 {tot['ARM1'] / NM:.6f} mm   "
          f"ARM2 {tot['ARM2'] / NM:.6f} mm   "
          f"SPREAD {d / NM:.6f} mm = {d / NM * 6.135:.4f} ps = "
          f"{d / NM * 13.25:.4f} deg at 6 GHz")

    if not a.emit:
        return 0

    # ---- the stitch.seed_stubs: block. NOTHING IS WRITTEN TO THE BOARD. ----
    print("\n# ---8<--- paste into 03_src/route.yaml under stitch: ---8<---")
    print("  seed_stubs:")
    print(f"    clearance: {CLR_MM}")
    print("    stubs:")
    for s in PATHS:
        for ch in [1] + ([2] if s["net2"] else []):
            name = s["net1"] if ch == 1 else s["net2"]
            ends = s["ends"] if ch == 1 else s["ends2"]
            pin = ends[1] or ends[0]
            pts = [(mm2nm(x), mm2nm(y)) for x, y in s["pts"]]
            if ch == 2:
                pts = xform(pts, s["xf"])
            fmt = ", ".join(f"[{x / NM:.3f}, {y / NM:.3f}]" for x, y in pts)
            print(f"      - {{net: {name}, pin: {pin},")
            print(f"         segments: [{{layer: F.Cu, width: {s['w']}, "
                  f"pts: [{fmt}]}}]}}")
    print("# ---8<--- end ---8<---")

    # ---- prep.keepouts.rects. DERIVED, not hand-drawn: the first hand-drawn
    # set was up to 0.07 mm too small in places and `p_seed_stubs` REFUSED four
    # of twenty-one stubs where a wave had crossed a corridor. Each rect is one
    # polyline's exact bounding box + KEEPOUT_PAD, so a corridor cannot be
    # under-reserved by arithmetic I did in my head.
    print("\n# ---8<--- paste into 03_src/route.yaml under prep.keepouts: ---8<---")
    print("    rects:")
    for s in PATHS:
        for ch in [1] + ([2] if s["net2"] else []):
            name = s["net1"] if ch == 1 else s["net2"]
            pts = [(mm2nm(x), mm2nm(y)) for x, y in s["pts"]]
            if ch == 2:
                pts = xform(pts, s["xf"])
            pad = s["w"] / 2 + CLR_MM + KEEPOUT_SLACK
            x0 = min(x for x, _ in pts) / NM - pad
            x1 = max(x for x, _ in pts) / NM + pad
            y0 = min(y for _, y in pts) / NM - pad
            y1 = max(y for _, y in pts) / NM + pad
            print(f"      - {{x0: {x0:.3f}, y0: {y0:.3f}, "
                  f"x1: {x1:.3f}, y1: {y1:.3f}}}   # {name}")
    print("# ---8<--- end ---8<---")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Refuse as e:
        print(f"rf_copper REFUSED: {e}", file=sys.stderr)
        sys.exit(1)
