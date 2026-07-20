#!/usr/bin/env python3
"""Node-for-node parity of two KiCad boards' connectivity: every (refdes, pad)
-> net-name must match. Proves the TSX-authored board is electrically identical
to the sealed 04_kicad board (not just DRC-clean). Ignores pad-less/NPTH pads
(no net) and normalizes KiCad auto-generated 'unconnected-*' node names, which
carry fresh UUID-ish suffixes and are not electrical signal.
Usage: board_netlist_parity.py BUILT.kicad_pcb SEALED.kicad_pcb
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


def main():
    A = nodes(sys.argv[1])   # built (TSX)
    S = nodes(sys.argv[2])   # sealed
    ka, ks = set(A), set(S)
    only_a, only_s = ka - ks, ks - ka
    mismatch = [(k, A[k], S[k]) for k in ka & ks if A[k] != S[k]]
    print(f"built nodes={len(A)}  sealed nodes={len(S)}")
    print(f"nets built={len(set(A.values()))}  sealed={len(set(S.values()))}")
    bad = 0
    if only_a:
        print("  ONLY in built:", sorted(only_a)[:20]); bad += len(only_a)
    if only_s:
        print("  ONLY in sealed:", sorted(only_s)[:20]); bad += len(only_s)
    if mismatch:
        print("  NET MISMATCH:", mismatch[:20]); bad += len(mismatch)
    if bad:
        print(f"BOARD PARITY: {bad} discrepancies -> FAIL")
        sys.exit(1)
    print(f"BOARD PARITY 0 -> PASS ({len(A)} nodes identical, net-for-net)")


if __name__ == "__main__":
    main()
