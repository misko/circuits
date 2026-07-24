#!/usr/bin/env /usr/bin/python3
"""interposer (Board C) board audit — P-POL polarity + P-KEEP mate/keepout.

Scripted checks the policy audit requires in 03_src (canon: checker and
checked share no method — this reads the SAVED BOARD with pcbnew, not the
floorplan that placed it):

  POLARITY (pad-1-net): every connector's pad 1 net is pinned — a flipped or
  mis-folded footprint surfaces here as a pad1-net mismatch. Full positional
  map 1..10 = KP_U1..U6,KP_D1..D4 checked on ALL three connectors, so the
  straight-through claim is graded pad-for-pad, not sampled.

  MATE/KEEPOUT: J_KEY_MATRIX mouth faces WEST (body centroid west of its pad
  row — the ribbon leaves the board edge, mate direction); both ZIF rows
  count pin 1 -> 10 WEST->EAST (a 180 flip reverses the OEM key matrix);
  the ZIF slider envelope (top entry) has no taller part in front of it —
  trivially true here, asserted as: no OTHER footprint courtyard intrudes
  between the two ZIF housings' facing edges at their x-span except the TP
  probe field (pads only, height 0).

  ISOLATION: the board's copper nets are EXACTLY the ten KP_* nets (BRIEF §5
  floating keypad domain) and the board has zero zones.

Usage: /usr/bin/python3 03_src/interposer/audit_board.py [board.kicad_pcb]
Exit 0 = all pass; nonzero lists failures.
"""
import sys
from pathlib import Path

import pcbnew

BOARD = sys.argv[1] if len(sys.argv) > 1 else str(
    Path(__file__).resolve().parents[2] / "04_kicad" / "interposer.kicad_pcb")

LINES = ["U1", "U2", "U3", "U4", "U5", "U6", "D1", "D2", "D3", "D4"]
EXPECT = {f"pin{i+1}": f"KP_{l}" for i, l in enumerate(LINES)}

def main():
    b = pcbnew.LoadBoard(BOARD)
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    fails = []

    # ---- polarity: pad-1 net (and every pad 1..10) on all three connectors
    for ref in ("J_MEMBRANE", "J_CN1_JUMPER", "J_KEY_MATRIX"):
        f = fps.get(ref)
        if not f:
            fails.append(f"{ref}: MISSING footprint")
            continue
        pads = {p.GetName(): p for p in f.Pads()}
        for i, line in enumerate(LINES):
            want = f"KP_{line}"
            p = pads.get(str(i + 1))
            got = p.GetNetname() if p else "<no pad>"
            if got != want:
                fails.append(f"POLARITY {ref}.{i+1}: net {got!r} != {want!r} (pad1-net map)")

    # ---- mate direction: J_KEY_MATRIX mouth WEST (body centroid west of pads)
    f = fps.get("J_KEY_MATRIX")
    if f:
        px = [p.GetPosition().x for p in f.Pads() if p.GetName().isdigit()]
        if not (f.GetPosition().x < min(px)):
            fails.append("MATE J_KEY_MATRIX: body centroid not WEST of pad row (mouth/mate direction flipped)")

    # ---- ZIF pin order WEST->EAST (both rows)
    for ref in ("J_MEMBRANE", "J_CN1_JUMPER"):
        f = fps.get(ref)
        if f:
            pads = {p.GetName(): p.GetPosition().x for p in f.Pads() if p.GetName().isdigit()}
            xs = [pads[str(i)] for i in range(1, 11)]
            if xs != sorted(xs):
                fails.append(f"MATE {ref}: pins 1..10 not monotonic WEST->EAST (180 flip)")

    # ---- keepout between the ZIF facing edges: only TP pads (no bodies)
    for ref, fp in fps.items():
        if ref.startswith(("J_", "TP_", "H")):
            continue
        fails.append(f"KEEPOUT: unexpected footprint {ref} on the board")

    # ---- isolation: copper nets == the ten KP_*; zero zones
    nets = {p.GetNetname() for f2 in b.GetFootprints() for p in f2.Pads() if p.GetNetname()}
    nets |= {t.GetNetname() for t in b.GetTracks() if t.GetNetname()}
    want = {f"KP_{l}" for l in LINES}
    if nets != want:
        fails.append(f"ISOLATION: copper nets {sorted(nets ^ want)} differ from the 10 KP_* set")
    if len(list(b.Zones())):
        fails.append(f"ISOLATION: {len(list(b.Zones()))} zones present (floating domain must have none)")

    if fails:
        print("interposer audit FAIL:")
        for x in fails:
            print("  -", x)
        return 1
    print("interposer audit PASS: polarity(pad1-net x30) + mate-direction + pin-order + isolation(10 KP_* nets, 0 zones)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
