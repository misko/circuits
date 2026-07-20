#!/usr/bin/env python3
"""kicad_sch_parity — node-for-node netlist parity between a converter-produced
`.kicad_sch` (via `kicad-cli sch export netlist --format kicadsexpr`) and the
sealed KiCad `04_kicad` board (via pcbnew). Companion gate to
`circuit_json_to_kicad_sch.py` under ADR-0001 Phase 2.

Normalization applied to the CONVERTER side (the KiCad fab-of-record is the truth):
  * NET renames — leading-digit power-rail names tscircuit can't select on
    (`3V3`->`N3V3`, `5V`->`N5V`, and `_A`/`_C` variants). Universal + safe:
    no real KiCad net carries the `N`-prefixed form.
  * PAD renames (`--padmap 'U2:4=2,...'`) — documented per-board footprint
    pad-name deltas where tscircuit's footprinter and the KiCad land pattern
    name the SAME physical pad differently (e.g. the AMS1117 SOT-223 tab:
    tscircuit `sot223` pad '4' == KiCad merged pad '2'; same net both sides).

Virtual power/flag symbols (`#PWR*` / `#FLG*`) are excluded. Pins that are
unconnected on BOTH sides (KiCad `unconnected-*` auto-nets; our `no_connect`
flags) are compared as a set, not as named nets. Exit code 0 == parity 0.

Usage: kicad_sch_parity.py <board> <netlist.net> <sealed.kicad_pcb> [--padmap ...]
"""
import argparse
import collections
import re
import sys

DEFAULT_NETMAP = {'N3V3': '3V3', 'N5V': '5V', 'N5V_A': '5V_A', 'N5V_C': '5V_C'}


def parse_netlist(path, netmap, padmap):
    txt = open(path).read()
    net2nodes = collections.defaultdict(set)
    nc = set()
    for m in re.finditer(r'\(net\b(.*?)(?=\(net\b|\Z)', txt, re.S):
        blk = m.group(1)
        nm = re.search(r'\(name "([^"]*)"\)', blk)
        if not nm:
            continue
        net = nm.group(1)
        for nd in re.finditer(r'\(node\s+\(ref "([^"]+)"\)\s+\(pin "([^"]+)"\)', blk):
            ref, pin = nd.group(1), nd.group(2)
            if ref.startswith('#'):
                continue
            pin = padmap.get((ref, pin), pin)
            if net.startswith('unconnected-') or net == '':
                nc.add((ref, pin))
            else:
                net2nodes[netmap.get(net, net)].add((ref, pin))
    return net2nodes, nc


def kicad_nodes(path):
    import pcbnew
    b = pcbnew.LoadBoard(path)
    net2nodes = collections.defaultdict(set)
    nc = set()
    for f in b.GetFootprints():
        for p in f.Pads():
            if not p.GetPadName():
                continue
            ref, pad = f.GetReference(), p.GetPadName()
            nn = p.GetNetname()
            if nn.startswith('unconnected-') or nn == '':
                nc.add((ref, pad))
            else:
                net2nodes[nn].add((ref, pad))
    return net2nodes, nc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("board")
    ap.add_argument("net_path")
    ap.add_argument("pcb_path")
    ap.add_argument("--padmap", default="", help="e.g. 'U2:4=2,U9:5=3'")
    a = ap.parse_args()
    padmap = {}
    for tok in filter(None, (t.strip() for t in a.padmap.split(","))):
        refpin, newpin = tok.split("=")
        ref, pin = refpin.split(":")
        padmap[(ref, pin)] = newpin

    nn, nnc = parse_netlist(a.net_path, DEFAULT_NETMAP, padmap)
    kn, knc = kicad_nodes(a.pcb_path)
    allnets = set(nn) | set(kn)
    disc = 0
    print(f"=== {a.board} netlist parity (converter kicad_sch vs sealed 04_kicad) ===")
    print(f"converter nets={len(nn)}  kicad nets={len(kn)}")
    for n in sorted(allnets):
        xa, xb = nn.get(n, set()), kn.get(n, set())
        if xa != xb:
            disc += 1
            print(f"  DIFF {n!r}: only_converter={sorted(xa - xb)} "
                  f"only_kicad={sorted(xb - xa)}")
    if nnc != knc:
        disc += 1
        print(f"  NO-CONNECT DIFF: only_converter={sorted(nnc - knc)} "
              f"only_kicad={sorted(knc - nnc)}")
    na = sum(len(v) for v in nn.values())
    nb = sum(len(v) for v in kn.values())
    print(f"connected nodes: converter={na} kicad={nb}   "
          f"no-connects: converter={len(nnc)} kicad={len(knc)}")
    print(f"REAL DISCREPANCIES: {disc}  ->  "
          f"{'PARITY 0 (PASS)' if disc == 0 else 'FAIL'}")
    sys.exit(1 if disc else 0)


if __name__ == "__main__":
    main()
