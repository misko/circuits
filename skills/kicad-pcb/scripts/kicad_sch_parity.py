#!/usr/bin/env python3
"""kicad_sch_parity — node-for-node netlist parity between a converter-produced
`.kicad_sch` (via `kicad-cli sch export netlist --format kicadsexpr`) and the
selected exact KiCad reference board (via pcbnew). Companion gate to
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

`--padmap` accepts BOTH the legacy inline form (`'U2:4=2,U9:5=3'`) and the raw
text of a board's `03_tscircuit/parity_padmap.txt` (gen_tscircuit.sh passes the
WHOLE file): `#` comments, blank lines, and the documented per-line form
`<ref>  pin<N>=<realpad>` all parse; `pin<N>` is aliased to bare `<N>` (tsx
portHints are numeric in the netlist). Tokens this gate cannot decode (the
tsx_preflight-only formats, e.g. `SM05B-GHS-TB MP GND` or `J5: A1 A4 ...`)
are SKIPPED with a stderr note — never a crash. FIX 2026-07-23: the old
parser did `tok.split("=")` on comma-split tokens and raised
`ValueError: not enough values to unpack` on any comment/preflight line,
killing the parity subgate on BOTH active boards (cooksense journal ~L416;
crow-rv2 routing.md M-REPRO entry). Pinned by
`t1_converter.py::t_sch_parity_padmap_file`, which was written FIRST and
verified RED against this script's pre-fix version (the exact ValueError
traceback), then green after this parser landed — swap-back procedure per
tests/README.md.

Usage: kicad_sch_parity.py <board> <netlist.net> <sealed.kicad_pcb> [--padmap ...]
"""
import argparse
import collections
import re
import sys
from pathlib import Path

DEFAULT_NETMAP = {'N3V3': '3V3', 'N5V': '5V', 'N5V_A': '5V_A', 'N5V_C': '5V_C'}

# a decodable mapping token: optional '<ref>:' or '<ref> ' prefix, then pin=pad
_PADTOK = re.compile(r'^(?:([A-Za-z0-9_.+-]+)[\s:]+)?'
                     r'([A-Za-z0-9_.+-]+)=([A-Za-z0-9_.+-]+)$')


def parse_padmap(text):
    """Tolerant --padmap parser (see module docstring for the 2026-07-23
    ValueError incident this replaces). Returns {(ref, pin): realpad}; a
    'pin<N>' pin also registers its bare-'<N>' alias. The map is applied to
    BOTH sides of the comparison (a pad rename is an IDENTITY between two
    names for the same physical pad): which naming each side carries varies
    per board — usb-hub converters emit the real alphanumeric pad (dual
    portHints) onto an alphanumeric board footprint, while crow-rv2's
    vendored J2 footprint (USB4105_..._num) kept the NUMERIC tsx pads.
    Renaming only the converter side (the pre-fix behaviour) MANUFACTURED
    7 phantom J2 diffs on crow-rv2 (measured 2026-07-23:
    CC2/GND/USB_DM/USB_DP/VBUS + the A8/B8-vs-6/14 no-connect pair — every
    one an 'A6'-vs-'4' same-net rename); canonicalizing both sides to the
    file's RHS name collapses them and cannot swap names past each other.
    Undecodable tokens are collected and reported once on stderr, never
    fatal."""
    padmap, skipped = {}, []
    for line in (text or "").splitlines():
        line = line.split('#', 1)[0].strip()
        if not line:
            continue
        for tok in filter(None, (t.strip() for t in line.split(','))):
            m = _PADTOK.match(tok)
            if not m or not m.group(1):
                skipped.append(tok)
                continue
            ref, pin, pad = m.groups()
            if pin.lower().startswith('pin') and pin[3:]:
                pin = pin[3:]                       # tsx portHints are numeric
                padmap.setdefault((ref, 'pin' + pin), pad)
            padmap[(ref, pin)] = pad
    if skipped:
        print(f"padmap: skipped {len(skipped)} non-parity token(s) "
              f"(tsx_preflight-only formats): {skipped[:5]}"
              f"{' ...' if len(skipped) > 5 else ''}", file=sys.stderr)
    return padmap


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


def kicad_nodes(path, padmap):
    import pcbnew
    b = pcbnew.LoadBoard(path)
    net2nodes = collections.defaultdict(set)
    nc = set()
    for f in b.GetFootprints():
        for p in f.Pads():
            if not p.GetPadName():
                continue
            ref, pad = f.GetReference(), p.GetPadName()
            pad = padmap.get((ref, pad), pad)   # canonicalize BOTH sides (see parse_padmap)
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
    padmap = parse_padmap(a.padmap)

    nn, nnc = parse_netlist(a.net_path, DEFAULT_NETMAP, padmap)
    kn, knc = kicad_nodes(a.pcb_path, padmap)
    allnets = set(nn) | set(kn)
    disc = 0
    print(f"=== {a.board} netlist parity (converter kicad_sch vs exact KiCad reference) ===")
    # G-INPUT: name both artifacts by path, so a reader can tell the sealed
    # board from a 06_build reconstruction (canon M-SHIP).
    print(f"input: netlist = {Path(a.net_path).resolve()}")
    print(f"input: board   = {Path(a.pcb_path).resolve()}")
    print(f"converter nets={len(nn)}  kicad nets={len(kn)}")

    # G-COVER: a zero denominator is a FAIL. Two sides that each parse to no
    # nets agree perfectly, and `PARITY 0 (PASS)` over nothing is the exact
    # gate-grading-nothing shape (canon M-COVER). A parser that silently
    # stopped matching — the class that truncated many-pin chips to 2 pins
    # (Device:U_chip, 2026-07-19) — lands here.
    if not allnets:
        print("REAL DISCREPANCIES: 0/0 nets — NEITHER side parsed a single "
              "net, so nothing was compared. A zero denominator is a FAIL, "
              "never a pass -> FAIL")
        sys.exit(1)

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
    verdict = (f"PARITY 0 (PASS) over {len(allnets)} nets / {na} nodes"
               if disc == 0 else "FAIL")
    print(f"REAL DISCREPANCIES: {disc}/{len(allnets)} nets  ->  {verdict}")
    sys.exit(1 if disc else 0)


if __name__ == "__main__":
    main()
