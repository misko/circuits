#!/usr/bin/env python3
"""cleanup_redundant_vias — remove vias co-located with a SAME-NET plated
through-hole pad.

KRT sometimes drops a layer-transition via directly on a THT pad when it
escapes that pad on the opposite copper layer. The via is REDUNDANT (the
plated hole already bridges both layers) and JLC flags it as
`holes_co_located` (two drills at one point). Removing it cannot disconnect
anything: the track it served still lands on the THT pad, which is present on
both layers.

Runs AFTER stitch, BEFORE the final generate_rules, on the promoted board.
Idempotent. A via co-located with a DIFFERENT-net pad is a real short and is
NEVER removed (it is left for the DRC to surface).

    /usr/bin/python3 03_src/cleanup_redundant_vias.py [board.kicad_pcb]
"""
import sys, os
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = os.path.join(HERE, "..", "04_kicad", "crow_mic_pod_v2.kicad_pcb")
TOL = pcbnew.FromMM(0.05)   # co-located tolerance


def main():
    bp = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    b = pcbnew.LoadBoard(bp)
    # index THT pads by (net, position)
    tht = []
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and p.GetDrillSize().x > 0:
                tht.append((p.GetNetCode(), p.GetPosition()))
    removed = 0
    for t in list(b.GetTracks()):
        if t.GetClass() != "PCB_VIA":
            continue
        vp = t.GetPosition()
        for nc, pp in tht:
            if abs(vp.x - pp.x) <= TOL and abs(vp.y - pp.y) <= TOL:
                if t.GetNetCode() == nc:
                    b.Remove(t)
                    removed += 1
                # different-net co-location is a SHORT — leave it for DRC
                break
    if removed:
        b.Save(bp)
    print(f"cleanup_redundant_vias: removed {removed} via(s) co-located with "
          f"a same-net THT pad")


if __name__ == "__main__":
    main()
