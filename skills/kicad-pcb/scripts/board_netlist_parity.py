#!/usr/bin/env python3
"""Node-for-node parity of two KiCad boards' connectivity: every (refdes, pad)
-> net-name must match. Proves the TSX-authored board is electrically identical
to the selected exact KiCad reference (not just DRC-clean). Ignores pad-less/NPTH pads
(no net) and normalizes KiCad auto-generated 'unconnected-*' node names, which
carry fresh UUID-ish suffixes and are not electrical signal.
Usage: board_netlist_parity.py BUILT.kicad_pcb REFERENCE.kicad_pcb

G-INPUT / G-COVER (canon M-COVER, 2026-07-27). This printed `BOARD PARITY 0 ->
PASS` with no denominator and without naming either file, so two EMPTY boards
compared equal and read as a clean parity run — the `jlc_twin` exit-0 shape.
It now names both paths and reports `N graded / M total` nodes, and a ZERO
node census is a FAIL, never a pass: a board with no nodes has not been proven
identical to anything.
"""
import re
import sys
import pcbnew


def nodes(path):
    b = pcbnew.LoadBoard(path)
    m = {}
    for f in b.GetFootprints():
        ref = f.GetReference()
        for p in f.Pads():
            if p.GetDrillSize().x > 0 and p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                continue
            net = p.GetNetname()
            if not net:
                continue
            # collapse auto 'unconnected-(REF-PIN-PadN)' to a stable token
            if net.startswith("unconnected-") or net.startswith("Net-"):
                net = "<float>"
            m[(ref, p.GetNumber())] = net
    return m


def _listing(items, cap=20):
    """A truncated sample that SAYS it is truncated and gives the full count.
    A bare `[:20]` reports a partial list as if it were the whole finding."""
    shown = sorted(items)[:cap]
    if len(items) <= cap:
        return f"{shown}"
    return f"{shown} ... and {len(items) - cap} more ({len(items)} total)"


def main():
    built_path, sealed_path = sys.argv[1], sys.argv[2]
    A = nodes(built_path)    # built (TSX)
    S = nodes(sealed_path)   # sealed
    # G-INPUT: name the artifacts, so a reader can tell a sealed board from a
    # 06_build reconstruction (canon M-SHIP).
    print(f"input: built  = {built_path}")
    print(f"input: sealed = {sealed_path}")
    ka, ks = set(A), set(S)
    only_a, only_s = ka - ks, ks - ka
    mismatch = [(k, A[k], S[k]) for k in ka & ks if A[k] != S[k]]
    total = len(ka | ks)
    print(f"built nodes={len(A)}  sealed nodes={len(S)}")
    print(f"nets built={len(set(A.values()))}  sealed={len(set(S.values()))}")

    # G-COVER: a zero denominator is a FAIL. Two empty boards used to compare
    # equal and print PASS.
    if total == 0:
        print("BOARD PARITY: 0/0 nodes — NEITHER board has a single netted "
              "pad, so nothing was compared. A zero denominator is a FAIL, "
              "never a pass (canon M-COVER) -> FAIL")
        sys.exit(1)

    bad = 0
    if only_a:
        print("  ONLY in built:", _listing(only_a)); bad += len(only_a)
    if only_s:
        print("  ONLY in sealed:", _listing(only_s)); bad += len(only_s)
    if mismatch:
        print("  NET MISMATCH:", _listing(mismatch)); bad += len(mismatch)
    if bad:
        print(f"BOARD PARITY: {total - bad}/{total} nodes agree, {bad} "
              f"discrepancies -> FAIL")
        sys.exit(1)
    print(f"BOARD PARITY 0 -> PASS ({len(A)}/{total} nodes identical, "
          f"net-for-net)")


if __name__ == "__main__":
    main()
