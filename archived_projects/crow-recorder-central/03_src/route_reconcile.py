#!/usr/bin/env python3
"""Adaptive routing reconciliation for crow-recorder-central.

KRT's wave router is nondeterministic run-to-run: a handful of dense
XU316-escape nets straggle, but WHICH ones varies. A hard-coded fix list
is fragile, so this driver instead:

  1. finds the still-unrouted NON-GND nets (KRT check_connected),
  2. routes each on a FINE grid (0.05mm, 0.15mm track = the 0.127 floor);
     if it fails, parses KRT's own "blocking copper belongs to net(s) ..."
     hint and retries ripping AND re-routing those blockers (each ripped
     net is in --nets so nothing is dropped),
  3. loops until clean or no progress.

GND is not a target (In1 plane + F/In2/B pours + stitch vias). Run after
route_waves.sh; produces the clean final.kicad_pcb in place.

Usage: /path/to/KRT/.venv/bin/python route_reconcile.py BOARD [--passes N]
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

KRT = Path(os.path.expanduser("~/gits/KiCadRoutingTools"))
PY = str(KRT / ".venv" / "bin" / "python")
# GND is a plane; power rails are routed to completion in the power waves
# (power-first on 6L) — this reconciler handles the SIGNAL stragglers only
# (mixing power widths with signal rip-up breaks the ripped signals).
PLANE = {"GND", "5V", "5V_P", "5V_IN", "3V3", "0V9", "1V8", "3V3A"}


def net_width(net):
    return "0.15"
COMMON = ["--via-size", "0.6", "--via-drill", "0.3", "--fab-tier", "standard",
          "--no-stub-layer-swap",   # escape vias land in diverged space, not
          "--keepout", "--keepout-layer", "User.2",   # at the 0.4mm pad pitch
          "--layers", "F.Cu", "In2.Cu", "In3.Cu", "B.Cu"]


def unrouted_signal_nets(board):
    """Authoritative unrouted-net detection via KiCad DRC (KRT's own
    check_connected under-reports: totally-unrouted 2-pad nets appear only
    in a summary list, and its connectivity model is looser than KiCad's).
    """
    import json
    rep = str(Path(board).with_name("_rc_drc.json"))
    subprocess.run(["kicad-cli", "pcb", "drc", "--severity-all",
                    "--format", "json", "-o", rep, board],
                   capture_output=True, text=True)
    d = json.load(open(rep))
    nets = set()
    for x in d.get("unconnected_items", []):
        for it in x.get("items", []):
            m = re.search(r"\[([A-Za-z0-9_+\-]+)\]", it.get("description", ""))
            if m:
                nets.add(m.group(1))
    return sorted(n for n in nets if n not in PLANE)


def route(inp, outp, nets, rip=None, grid="0.05", tw=None):
    # width = the widest floor among the nets being routed (power keeps its
    # ampacity floor; a mixed rip re-routes the ripped power net wide too).
    if tw is None:
        tw = max((net_width(n) for n in list(nets) + list(rip or [])),
                 key=float)
    cmd = [PY, str(KRT / "route.py"), inp, "--output", outp,
           "--grid-step", grid, "--clearance", "0.13", "--track-width", tw,
           "--max-iterations", "2000000", "--max-ripup", "120"] + COMMON
    if rip:
        cmd += ["--rip-existing-nets"] + rip
    cmd += ["--nets"] + nets
    r = subprocess.run(cmd, capture_output=True, text=True)
    blockers = set()
    for m in re.finditer(r"blocking copper belongs to pre-existing net\(s\) (.+?)\(committed",
                         r.stdout, re.S):
        blockers |= set(re.findall(r"'([A-Za-z0-9_]+)'", m.group(1)))
    ok = False
    for m in re.finditer(r"JSON_SUMMARY: (\{.*\})", r.stdout):
        d = json.loads(m.group(1))
        ok = not d.get("failed_single") and not d.get("failed_multipoint")
    return ok, sorted(b for b in blockers if b not in PLANE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("board")
    ap.add_argument("--passes", type=int, default=8)
    a = ap.parse_args()
    board = a.board
    tmp = str(Path(board).with_name("_rc_tmp.kicad_pcb"))
    for p in range(a.passes):
        left = unrouted_signal_nets(board)
        print(f"pass {p}: {len(left)} unrouted signal nets: {left}")
        if not left:
            print("RECONCILE: clean")
            return 0
        progressed = False
        for net in left:
            # try fine grid alone, then rip the blockers KRT names
            ok, blk = route(board, tmp, [net])
            if not ok and blk:
                ok, _ = route(board, tmp, [net] + blk, rip=blk)
            if ok:
                os.replace(tmp, board)
                progressed = True
                print(f"  routed {net}" + (f" (ripped {blk})" if blk else ""))
        if not progressed:
            # per-net oscillation (competing same-corridor nets, e.g. the
            # beeper-gate bus): try routing the whole remaining set TOGETHER
            # with rip of itself so KRT arbitrates them jointly.
            ok = False
            for g in ("0.1", "0.05"):     # fine grid weaves adjacent-pin conflicts
                ok, _ = route(board, tmp, left, rip=left, grid=g)
                if ok:
                    os.replace(tmp, board)
                    print(f"  joint-routed {left} (grid {g})")
                    break
            if ok:
                continue
            print(f"RECONCILE: STUCK with {left}")
            return 1
    left = unrouted_signal_nets(board)
    print("RECONCILE: clean" if not left else f"RECONCILE: STUCK {left}")
    return 0 if not left else 1


if __name__ == "__main__":
    sys.exit(main())
