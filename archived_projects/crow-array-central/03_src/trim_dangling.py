#!/usr/bin/env python3
"""DRC-guarded trim of track_dangling loose copper (KRT rip-up spurs: the
audio diff-pair stubs VA*/VB*, plus leftover I2C_SDA/0V9/3V3 escape spurs).
Runs LAST, after clearance surgery.

SUBPROCESS-PER-REMOVAL: repeated pcbnew.LoadBoard in one process hits a SWIG
wrapper corruption (iterator poisoning after Remove; kicad-pcb skill), so the
ORCHESTRATOR (this script, default mode — needs no pcbnew) spawns a fresh
python subprocess (`--remove NET X Y`) for every single removal; each child
does exactly one load -> remove -> refill -> save and exits.

CONNECTIVITY GUARD (BRIEF: some dangling stubs are load-bearing): each stub is
removed on a throwaway copy of the board state; the removal is KEPT only if
track_dangling strictly drops AND unconnected does NOT rise AND total
violations strictly drop (removing a stub that is a pad's only copper would
orphan the pad -> unconnected rises -> reverted, stub stays). One stub at a
time, re-reading DRC between removals (removing one can expose or cure
another).

CLIP-TO-PAD fallback: 10 of the 11 spurs are KRT through-pin routes — the
track enters at a junction, crosses its TSSOP/TQFP pad MID-SEGMENT, and
overshoots past it (probe 2026-07-18: U2/U3 PCM1865 + U1 XU316 pins, e.g.
VA3M (78.2,59.5)->(76.0,59.5) with U2.28 at 76.86). Whole-segment removal
orphans the pad (guard rejects); the cure is CLIPPING the dangling end back
to the covered pad's center — feed junction + pad contact kept, loose
overshoot gone. Which end dangles is not derivable from the report alone
(both ends can show touching copper), so the orchestrator tries near end
then far end and lets the DRC guard pick the survivor.
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

PCB = str(Path(__file__).parent.parent / "04_kicad" / "crow_array_central.kicad_pcb")
TMP = "/tmp/_td_bak.kicad_pcb"
NM = 1e6


def drc():
    out = Path("/tmp/_td_drc.json")
    subprocess.run(["kicad-cli", "pcb", "drc", "--severity-all", "--refill-zones",
                    "--format", "json", "-o", str(out), PCB],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    d = json.load(open(out))
    dang = [v for v in d["violations"] if v["type"] == "track_dangling"]
    return len(d["violations"]), len(d["unconnected_items"]), len(dang), dang


# ---------------- child mode: ONE edit per process --------------------------
def _load():
    import os
    sys.path.insert(0, os.path.expanduser("~/.claude/skills/kicad-pcb/scripts"))
    import pcbnew
    return pcbnew, pcbnew.LoadBoard(PCB)


def _find(b, net, x, y):
    best, bd = None, 1e9
    for t in b.GetTracks():
        if t.GetClass() != "PCB_TRACK" or t.GetNetname() != net:
            continue
        for p in (t.GetStart(), t.GetEnd()):
            d = (p.x / NM - x) ** 2 + (p.y / NM - y) ** 2
            if d < bd:
                bd, best = d, t
    return (best, bd) if best is not None and bd <= 0.05 ** 2 else (None, bd)


def child_remove(net, x, y):
    """Remove the dangling track of `net` with an endpoint nearest (x,y).
    Fresh process = fresh SWIG state; exit 0 on success, 3 on no-match."""
    pcbnew, b = _load()
    best, _ = _find(b, net, x, y)
    if best is None:
        return 3
    b.Remove(best)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.Save(PCB)
    return 0


def child_clip(net, x, y, end):
    """Clip a segment of `net` with an endpoint near (x,y): move its
    `end` ('near'|'far' relative to (x,y)) endpoint back to the same-net
    anchor the segment crosses mid-run — a covered PAD center (projection
    kept on-axis) or a tangentially-touched VIA center (snap; solidifies
    marginal 0.21mm-off-axis grazes like VB3P's). The reported pos can be a
    junction shared by several segments (a tie), so every tied segment is a
    candidate. Exit 0 ok, 3 no-match/no-anchor."""
    import math
    pcbnew, b = _load()
    nc_net = b.FindNet(net)
    if not nc_net:
        return 3
    nc = nc_net.GetNetCode()
    cands = []
    for t in b.GetTracks():
        if t.GetClass() != "PCB_TRACK" or t.GetNetCode() != nc:
            continue
        d = min((t.GetStart().x / NM - x) ** 2 + (t.GetStart().y / NM - y) ** 2,
                (t.GetEnd().x / NM - x) ** 2 + (t.GetEnd().y / NM - y) ** 2)
        if d <= 0.05 ** 2:
            cands.append((d, t))
    cands.sort(key=lambda z: z[0])
    for _, seg in cands:
        ax, ay = seg.GetStart().x / NM, seg.GetStart().y / NM
        bx, by = seg.GetEnd().x / NM, seg.GetEnd().y / NM
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        if L2 == 0:
            continue
        halfw = seg.GetWidth() / NM / 2
        anchor = None
        for fp in b.GetFootprints():
            for p in fp.Pads():
                if p.GetNetCode() != nc:
                    continue
                px, py = p.GetPosition().x / NM, p.GetPosition().y / NM
                u = ((px - ax) * dx + (py - ay) * dy) / L2
                if not (0.05 < u < 0.95):
                    continue
                if math.hypot(ax + u * dx - px, ay + u * dy - py) < 0.25:
                    anchor = (ax + u * dx, ay + u * dy)  # on-axis projection
                    break
            if anchor:
                break
        if anchor is None:
            for t in b.GetTracks():
                if t.GetClass() != "PCB_VIA" or t.GetNetCode() != nc:
                    continue
                px, py = t.GetPosition().x / NM, t.GetPosition().y / NM
                u = ((px - ax) * dx + (py - ay) * dy) / L2
                if not (0.05 < u < 0.98):
                    continue
                reach = halfw + t.GetWidth() / NM / 2 + 0.02
                if math.hypot(ax + u * dx - px, ay + u * dy - py) < reach:
                    anchor = (px, py)  # snap onto the via center
                    break
        if anchor is None:
            continue
        start_is_near = ((ax - x) ** 2 + (ay - y) ** 2
                         <= (bx - x) ** 2 + (by - y) ** 2)
        clip_start = start_is_near if end == "near" else not start_is_near
        tgt = pcbnew.VECTOR2I_MM(round(anchor[0], 4), round(anchor[1], 4))
        if clip_start:
            seg.SetStart(tgt)
        else:
            seg.SetEnd(tgt)
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        b.Save(PCB)
        return 0
    return 3


# ---------------- orchestrator (default) -----------------------------------
def orchestrate():
    bv0, bu0, bd0, _ = drc()
    print(f"trim_dangling start: violations={bv0} unconnected={bu0} dangling={bd0}")
    skip = set()
    for _ in range(40):
        bv, bu, bd, dang = drc()
        if bd == 0:
            break
        target = None
        for v in dang:
            it = v["items"][0]
            desc, p = it.get("description", ""), it.get("pos", {})
            net = desc.split("[", 1)[1].split("]", 1)[0] if "[" in desc else ""
            key = (net, round(p.get("x") or 0, 2), round(p.get("y") or 0, 2))
            if key not in skip:
                target = (net, p.get("x"), p.get("y"), key)
                break
        if target is None:
            break
        net, x, y, key = target
        if not net or x is None or y is None:
            skip.add(key)
            continue
        # fallback ladder: full removal, then clip-to-pad at the reported
        # end, then at the other end — the DRC guard picks the survivor
        attempts = (["--remove", net, str(x), str(y)],
                    ["--clip", net, str(x), str(y), "near"],
                    ["--clip", net, str(x), str(y), "far"])
        done = None
        for args in attempts:
            shutil.copy(PCB, TMP)
            r = subprocess.run([sys.executable, __file__] + args,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if r.returncode != 0:
                shutil.copy(TMP, PCB)
                continue
            av, au, ad, _ = drc()
            if ad < bd and au <= bu and av < bv:
                done = f"{args[0]} {net}@({x:.1f},{y:.1f})  [dang {bd}->{ad}]"
                break
            shutil.copy(TMP, PCB)
        if done:
            print(f"  {done}")
        else:
            skip.add(key)
            print(f"  KEPT {net}@({x:.1f},{y:.1f}) (no guarded edit improved)")

    bv1, bu1, bd1, _ = drc()
    print(f"trim_dangling end: violations {bv0}->{bv1}; unconnected {bu0}->{bu1}; "
          f"dangling {bd0}->{bd1}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--remove", nargs=3, metavar=("NET", "X", "Y"),
                    help="child mode: remove one dangling track and exit")
    ap.add_argument("--clip", nargs=4, metavar=("NET", "X", "Y", "END"),
                    help="child mode: clip one dangling overshoot to its "
                         "covered pad center (END = near|far) and exit")
    a = ap.parse_args()
    if a.remove:
        sys.exit(child_remove(a.remove[0], float(a.remove[1]), float(a.remove[2])))
    if a.clip:
        sys.exit(child_clip(a.clip[0], float(a.clip[1]), float(a.clip[2]),
                            a.clip[3]))
    orchestrate()
