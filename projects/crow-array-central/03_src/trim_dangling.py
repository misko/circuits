#!/usr/bin/env python3
"""DRC-guarded trim of track_dangling loose copper (KRT rip-up spurs: the
audio diff-pair stubs VA*/VB*, plus leftover I2C_SDA/0V9/3V3 escape spurs).
Runs LAST, after clearance surgery.

CONNECTIVITY GUARD (BRIEF: some dangling stubs are load-bearing): each stub is
removed on a throwaway copy, refilled and DRC'd; the removal is KEPT only if
track_dangling strictly drops AND unconnected does NOT rise (removing a stub
that is a pad's only copper would orphan the pad -> unconnected rises -> the
removal is reverted and the stub stays). One stub at a time, re-reading DRC
between removals (removing one can expose or cure another).
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, os.path.expanduser("~/.claude/skills/kicad-pcb/scripts"))
import pcbnew

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


def remove_at(net, x, y):
    """Remove the dangling track of `net` whose an endpoint is nearest (x,y)."""
    try:
        return _remove_at(net, x, y)
    except Exception as e:
        print(f"    (remove_at error {net}@({x},{y}): {e})")
        return False


def _remove_at(net, x, y):
    b = pcbnew.LoadBoard(PCB)
    best, bd = None, 1e9
    for t in b.GetTracks():
        if t.GetClass() != "PCB_TRACK" or t.GetNetname() != net:
            continue
        for p in (t.GetStart(), t.GetEnd()):
            d = (p.x / NM - x) ** 2 + (p.y / NM - y) ** 2
            if d < bd:
                bd, best = d, t
    if best is None or bd > 0.05 ** 2:
        return False
    b.Remove(best)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.Save(PCB)
    return True


bv0, bu0, bd0, _ = drc()
print(f"trim_dangling start: violations={bv0} unconnected={bu0} dangling={bd0}")
skip = set()
removed = 0
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
    shutil.copy(PCB, TMP)
    if not remove_at(net, x, y):
        shutil.copy(TMP, PCB)
        skip.add(key)
        continue
    av, au, ad, _ = drc()
    if ad < bd and au <= bu and av < bv:
        removed += 1
        print(f"  trimmed {net}@({x:.1f},{y:.1f})  [dang {bd}->{ad}]")
    else:
        shutil.copy(TMP, PCB)
        skip.add(key)
        print(f"  KEPT {net}@({x:.1f},{y:.1f}) (load-bearing: u {bu}->{au}, v {bv}->{av})")

bv1, bu1, bd1, _ = drc()
print(f"trim_dangling end: violations {bv0}->{bv1}; unconnected {bu0}->{bu1}; dangling {bd0}->{bd1}")
