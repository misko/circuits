#!/usr/bin/env python3
"""Functional silkscreen labels for human-touched refs (canon P5 /
policy_audit P-SILK-FN; D29). The fleet audit's founding incident was a
battery board with unmarked terminals — this board had every functional
word on F.Fab (unprinted) only: the bare board would ship with an unmarked
5V barrel jack, anonymous debug/injection headers, and unlabeled PTCs/TPs.

For every footprint matching the audit's silk_fn_refs pattern (^(J|F|TP)\\d)
with no board-level silk text within its audit radius, stamp the part's
VALUE string (already the functional word: "DC-005 5V IN", "2A PTC",
"TP 5V", "xSYS DBG TDI/TDO") as F.Silk text beside the body:
  - candidate slots: below, above, left, right of the courtyard bbox;
  - collision-checked (approx char-metric bboxes, same philosophy as the
    audit's S-OCCL) against existing silk texts, all footprints' silk
    refdes, and every footprint courtyard bbox; kept inside the outline;
  - the whole stage is DRC-GUARDED: if the gate DRC (severity-all,
    refill) reports MORE violations than before, the stage reverts.
Idempotent: refs that already have nearby board silk text are skipped, so
the re-run on the promoted artifact is a no-op.
"""
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path
import pcbnew

PCB = str(Path(__file__).parent.parent / "04_kicad" / "crow_recorder_central.kicad_pcb")
TMP = "/tmp/_sf_bak.kicad_pcb"
MM = lambda v: v / 1e6
H = 0.8          # text height mm
TH = 0.15        # stroke
CH_W = 0.85      # approx per-char advance at 0.8mm height
PAT = re.compile(r"^(J|F|TP)[0-9]")
RAD = 9.0        # audit silk_fn_radius_mm


def drc_counts():
    out = "/tmp/_sf_drc.json"
    subprocess.run(["kicad-cli", "pcb", "drc", "--severity-all", "--refill-zones",
                    "--format", "json", "-o", out, PCB],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    d = json.load(open(out))
    return len(d["violations"]), len(d["unconnected_items"])


def bbox_of_text(x, y, s):
    w = len(s) * CH_W
    return (x - w / 2, y - H * 0.75, x + w / 2, y + H * 0.75)


def overlaps(a, b, m=0.25):
    return not (a[2] + m < b[0] or b[2] + m < a[0]
                or a[3] + m < b[1] or b[3] + m < a[1])


def main():
    b = pcbnew.LoadBoard(PCB)
    edges = b.GetBoardEdgesBoundingBox()
    bx0, by0 = MM(edges.GetX()) + 0.8, MM(edges.GetY()) + 0.8
    bx1 = MM(edges.GetX() + edges.GetWidth()) - 0.8
    by1 = MM(edges.GetY() + edges.GetHeight()) - 0.8
    SILKS = (pcbnew.F_SilkS, pcbnew.B_SilkS)

    obstacles = []   # existing bboxes to avoid
    texts = []       # existing board silk text anchors (audit semantics)
    for t in b.GetDrawings():
        if t.GetClass() == "PCB_TEXT" and t.GetLayer() in SILKS:
            texts.append((MM(t.GetPosition().x), MM(t.GetPosition().y)))
            tb = t.GetBoundingBox()
            obstacles.append((MM(tb.GetX()), MM(tb.GetY()),
                              MM(tb.GetX() + tb.GetWidth()),
                              MM(tb.GetY() + tb.GetHeight())))
    for f in b.GetFootprints():
        # BODY-ONLY bbox: including text would import the (unprinted) F.Fab
        # value-text sprawl as phantom obstacles and starve every slot
        fb = f.GetBoundingBox(False, False)
        obstacles.append((MM(fb.GetX()), MM(fb.GetY()),
                          MM(fb.GetX() + fb.GetWidth()),
                          MM(fb.GetY() + fb.GetHeight())))
        # printed footprint texts (refdes + any silk-layer graphics)
        for it in [f.Reference(), f.Value()] + list(f.GraphicalItems()):
            try:
                if it.GetLayer() in SILKS and getattr(it, "IsVisible", lambda: True)():
                    tb = it.GetBoundingBox()
                    obstacles.append((MM(tb.GetX()), MM(tb.GetY()),
                                      MM(tb.GetX() + tb.GetWidth()),
                                      MM(tb.GetY() + tb.GetHeight())))
            except Exception:
                pass

    todo = []
    for f in b.GetFootprints():
        r = f.GetReference()
        if not PAT.match(r):
            continue
        fx, fy = MM(f.GetPosition().x), MM(f.GetPosition().y)
        bbf = f.GetBoundingBox(False, False)
        eff = RAD + math.hypot(MM(bbf.GetWidth()), MM(bbf.GetHeight())) / 2
        if any(math.hypot(tx - fx, ty - fy) < eff for tx, ty in texts):
            continue
        todo.append(f)
    if not todo:
        print("add_silk_fn: nothing to do (all functional refs labeled)")
        return

    bv0, bu0 = drc_counts()
    shutil.copy(PCB, TMP)
    placed, skipped = [], []
    for f in todo:
        labels = [f.GetValue().strip()]
        # dense-cluster fallback: the part-CLASS word alone still satisfies
        # canon P5 (the PORT n banner supplies the channel number)
        first = labels[0].split()[0]
        if len(labels[0].split()) > 1 and len(first) >= 2:
            labels.append(first)
        fx, fy = MM(f.GetPosition().x), MM(f.GetPosition().y)
        bbf = f.GetBoundingBox(False, False)
        x0, y0 = MM(bbf.GetX()), MM(bbf.GetY())
        x1, y1 = MM(bbf.GetX() + bbf.GetWidth()), MM(bbf.GetY() + bbf.GetHeight())
        spot, label = None, labels[0]
        for label in labels:
            w = len(label) * CH_W
            cands = [(fx, y1 + H), (fx, y0 - H),                 # below, above
                     (x0 - w / 2 - H, fy), (x1 + w / 2 + H, fy),  # left, right
                     (fx, y1 + 2.2 * H), (fx, y0 - 2.2 * H)]
            # fallback: grid sweep around the part, nearest-first, still
            # within the audit's counting radius of the part center
            eff = RAD + math.hypot(x1 - x0, y1 - y0) / 2 - 0.5
            grid = [(fx + dx, fy + dy)
                    for dx in [i * 0.8 for i in range(-10, 11)]
                    for dy in [i * 0.8 for i in range(-8, 9)]
                    if math.hypot(dx, dy) > 1.0]
            grid.sort(key=lambda p: math.hypot(p[0] - fx, p[1] - fy))
            cands += [(cx, cy) for cx, cy in grid
                      if math.hypot(cx - fx, cy - fy) < eff]
            for (cx, cy) in cands:
                bb = bbox_of_text(cx, cy, label)
                if bb[0] < bx0 or bb[2] > bx1 or bb[1] < by0 or bb[3] > by1:
                    continue
                if any(overlaps(bb, o) for o in obstacles):
                    continue
                spot = (cx, cy, bb)
                break
            if spot:
                break
        if spot is None:
            skipped.append(f.GetReference())
            continue
        cx, cy, bb = spot
        t = pcbnew.PCB_TEXT(b)
        t.SetText(label)
        t.SetLayer(pcbnew.F_SilkS)
        t.SetPosition(pcbnew.VECTOR2I_MM(round(cx, 3), round(cy, 3)))
        t.SetTextSize(pcbnew.VECTOR2I_MM(H, H))
        t.SetTextThickness(int(TH * 1e6))
        b.Add(t)
        obstacles.append(bb)
        placed.append(f.GetReference())
    b.Save(PCB)
    bv1, bu1 = drc_counts()
    if bv1 > bv0 or bu1 > bu0:
        shutil.copy(TMP, PCB)
        print(f"add_silk_fn: REVERTED (drc {bv0}->{bv1}, unc {bu0}->{bu1})")
        sys.exit(1)
    print(f"add_silk_fn: labeled {len(placed)} refs {placed}")
    if skipped:
        print(f"add_silk_fn: NO ROOM for {skipped} — needs manual placement")
        sys.exit(1)


if __name__ == "__main__":
    main()
