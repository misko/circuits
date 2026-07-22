#!/usr/bin/env python3
"""DRC-guarded NECKING of power segments at fine-pitch / parallel-escape
approaches (D25; BRIEF clusters A/B/C — the 18 residual sub-0.09 clearance
items clearance_nudge could not shift):
  B  a 0.50mm 5V trace physically cannot clear the AP61102 (U10/U11,
     SOT-563 0.5mm pitch) adjacent GND pad at any legal position;
  A  the 0.40mm 3V3 east-central trunk runs parallel-and-too-close to the
     RST_N / MCLK_B / I2C_SCL / I2C_SDA fine escapes (F.Cu + In3.Cu);
  C  the 0.40mm 3V3 tap crowds the MCLK_A escape near R61 (tile-0).
ROOT CAUSE: the router held the netclass ampacity floor width through
corridors where the floor width + 0.09mm cannot geometrically fit. FIX per
the skill's sub-floor-tap doctrine: neck the POWER segment locally to
NECK_W (0.20mm) and drop a named rule area 'pwr_neck' over exactly the
necked copper, which generate_rules.py's scoped width_*_neck DRU rules
exempt (same pattern as 'xu316_taps'). Ampacity margin math lives in the
DRU comment (generate_rules.py): 5V per-buck VIN branch <=0.45A on a <1mm
neck, 3V3 trunk <=0.40A -> ~3.8C rise on the longest ~16mm neck.
Every edit is applied under the DRC guard: kept only if the TOTAL violation
count strictly drops and unconnected does not rise, else reverted.
Runs after clearance_nudge, before trim_dangling.
"""
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, os.path.expanduser("~/.claude/skills/kicad-pcb/scripts"))
import pcbnew

PCB = str(Path(__file__).parent.parent / "04_kicad" / "crow_array_central.kicad_pcb")
TMP = "/tmp/_na_bak.kicad_pcb"
NM = 1e6
NECK_W = 0.20          # mm; > the 0.15 scoped DRU floor, <= all cluster needs
POWER_NETS = {"5V", "5V_P", "5V_IN", "3V3", "0V9", "1V8", "3V3A"}


def drc():
    out = Path("/tmp/_na_drc.json")
    subprocess.run(["kicad-cli", "pcb", "drc", "--severity-all", "--refill-zones",
                    "--format", "json", "-o", str(out), PCB],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    d = json.load(open(out))
    return len(d["violations"]), len(d["unconnected_items"]), d


def clearance_items(d):
    out = []
    for v in d["violations"]:
        if v["type"] != "clearance":
            continue
        its = v.get("items", [])
        if len(its) != 2:
            continue
        parsed = []
        for it in its:
            desc, p = it.get("description", ""), it.get("pos", {})
            net = desc.split("[", 1)[1].split("]", 1)[0] if "[" in desc else ""
            kind = ("track" if desc.startswith("Track")
                    else "via" if "Via" in desc else "pad")
            # disambiguators: two wide segments can share the reported
            # endpoint (pos) — the description's length + layer pin the
            # actual offender (both live ties hit, U6/U10)
            length = None
            if "length" in desc:
                try:
                    length = float(desc.split("length ")[1].split(" mm")[0])
                except Exception:
                    pass
            layer = None
            if " on " in desc:
                layer = desc.split(" on ")[1].split(",")[0].split(" -")[0].strip()
            parsed.append({"kind": kind, "net": net, "x": p.get("x"), "y": p.get("y"),
                           "length": length, "layer": layer})
        out.append((parsed[0], parsed[1]))
    return out


def sig(a, b):
    return (a["net"], round(a["x"] or 0, 2), round(a["y"] or 0, 2),
            b["net"], round(b["x"] or 0, 2), round(b["y"] or 0, 2))


def nearest_wide_seg(b, netname, mx, my, length=None, layer=None):
    """Nearest not-yet-necked track segment of `netname` to (mx,my).
    `length`/`layer` (from the DRC item description) disambiguate endpoint
    ties: two wide segments sharing the reported endpoint both sit at
    distance 0, and the wrong pick gets reverted by the guard forever."""
    net = b.FindNet(netname)
    if not net:
        return None
    nc = net.GetNetCode()
    best, bd = None, 1e9
    for t in b.GetTracks():
        if t.GetClass() != "PCB_TRACK" or t.GetNetCode() != nc:
            continue
        if t.GetWidth() / NM <= NECK_W + 0.005:
            continue  # already necked; necking again cannot help
        if layer and b.GetLayerName(t.GetLayer()) != layer:
            continue
        ax, ay = t.GetStart().x / NM, t.GetStart().y / NM
        bx, by = t.GetEnd().x / NM, t.GetEnd().y / NM
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        if length is not None and abs(math.sqrt(L2) - length) > 0.02:
            continue
        u = 0 if L2 == 0 else max(0, min(1, ((mx - ax) * dx + (my - ay) * dy) / L2))
        d2 = (mx - ax - u * dx) ** 2 + (my - ay - u * dy) ** 2
        if d2 < bd:
            bd, best = d2, t
    return best if bd < 0.30 ** 2 else None


def add_neck_area(b, seg, halfw):
    """Named rule area 'pwr_neck' hugging the necked segment (all Cu layers,
    non-blocking) — the generate_rules.py width_*_neck exemption scope.
    Copies the generate_board.py 'xu316_taps' rule-area pattern."""
    ax, ay = seg.GetStart().x / NM, seg.GetStart().y / NM
    bx, by = seg.GetEnd().x / NM, seg.GetEnd().y / NM
    dx, dy = bx - ax, by - ay
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L          # along
    nx, ny = -uy, ux                 # normal
    e = halfw                        # inflate: covers the copper + margin
    corners = [(ax - ux * e + nx * e, ay - uy * e + ny * e),
               (bx + ux * e + nx * e, by + uy * e + ny * e),
               (bx + ux * e - nx * e, by + uy * e - ny * e),
               (ax - ux * e - nx * e, ay - uy * e - ny * e)]
    ra = pcbnew.ZONE(b)
    ra.SetIsRuleArea(True)
    ra.SetZoneName("pwr_neck")
    for setter in ("SetDoNotAllowTracks", "SetDoNotAllowVias", "SetDoNotAllowPads",
                   "SetDoNotAllowZoneFills", "SetDoNotAllowCopperPour",
                   "SetDoNotAllowFootprints"):
        fn = getattr(ra, setter, None)
        if fn is not None:
            fn(False)
    ra.SetLayerSet(pcbnew.LSET.AllCuMask())
    ra.Outline().NewOutline()
    for x, y in corners:
        ra.Outline().Append(pcbnew.VECTOR2I_MM(round(x, 4), round(y, 4)))
    b.Add(ra)


def neck_seg(mover_net, mover_pos, length=None, layer=None):
    """Edit fn: neck mover_net's nearest wide segment to NECK_W and scope a
    'pwr_neck' rule area over it. Returns a label or None."""
    def edit():
        b = pcbnew.LoadBoard(PCB)
        seg = nearest_wide_seg(b, mover_net, *mover_pos, length=length, layer=layer)
        if seg is None:
            return None
        w0 = seg.GetWidth() / NM
        Lmm = math.hypot(seg.GetEnd().x - seg.GetStart().x,
                         seg.GetEnd().y - seg.GetStart().y) / NM
        add_neck_area(b, seg, NECK_W / 2 + 0.05)
        seg.SetWidth(int(round(NECK_W * NM)))
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        b.Save(PCB)
        return (f"neck {mover_net}@({mover_pos[0]:.1f},{mover_pos[1]:.1f}) "
                f"{w0:.2f}->{NECK_W:.2f}mm L={Lmm:.1f}mm")
    return edit


def guarded(edit_fn):
    bv, bu, _ = drc()
    shutil.copy(PCB, TMP)
    label = edit_fn()
    if not label:
        shutil.copy(TMP, PCB)
        return None
    av, au, _ = drc()
    if av < bv and au <= bu:
        return f"{label}  [v {bv}->{av}]"
    shutil.copy(TMP, PCB)
    return None


bv0, bu0, d0 = drc()
print(f"neck_approaches start: violations={bv0} unconnected={bu0}")
skip = set()
for _ in range(40):
    bv, bu, d = drc()
    items = [(A, B) for (A, B) in clearance_items(d)
             if sig(A, B) not in skip
             and any(m["kind"] == "track" and m["net"] in POWER_NETS
                     for m in (A, B))]
    if not items:
        break
    A, B = items[0]
    done = None
    # neck the POWER track (the ampacity-floored mover); if the pair is
    # power-vs-power, try both sides
    for m in (A, B):
        if m["kind"] != "track" or m["net"] not in POWER_NETS:
            continue
        res = guarded(neck_seg(m["net"], (m["x"], m["y"]),
                               length=m.get("length"), layer=m.get("layer")))
        if res:
            done = res
            break
    if done:
        print(f"  {done}")
    else:
        skip.add(sig(A, B))
        print(f"  SKIP {sig(A, B)} (no strict improvement)")

bv1, bu1, _ = drc()
print(f"neck_approaches end: violations {bv0}->{bv1}; unconnected {bu0}->{bu1}")
