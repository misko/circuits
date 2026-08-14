#!/usr/bin/env python3
"""Refuse newly-added ordinary vias whose centres land in SMD pads.

The comparison is intentionally between consecutive route-wave boards.  Vias
that were already present in the input (for example, a source-owned filled and
capped exposed-pad field) are outside this gate's ownership; a router-created
via is not.  This keeps the policy executable without outlawing explicitly
reviewed source geometry.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

import pcbnew


def _via_signature(via):
    pos = via.GetPosition()
    return via.GetNetname(), int(pos.x), int(pos.y)


def newly_added_vias(before, after):
    """Return output vias not matched by net+position in the input board."""
    remaining = Counter(_via_signature(v) for v in before.GetTracks()
                        if v.GetClass() == "PCB_VIA")
    added = []
    for via in after.GetTracks():
        if via.GetClass() != "PCB_VIA":
            continue
        sig = _via_signature(via)
        if remaining[sig]:
            remaining[sig] -= 1
        else:
            added.append(via)
    return added


def copper_smd_pads(board):
    """Pre-index undrilled copper lands once for all new-via probes."""
    copper_layers = [layer for layer in board.GetEnabledLayers().Seq()
                     if pcbnew.IsCopperLayer(layer)]
    pads = []
    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            # An undrilled F.Mask/F.Paste-only aperture is not a copper land.
            # `drill == 0` alone therefore overstates the forbidden set.
            if (pad.GetDrillSize().x > 0
                    or not any(pad.IsOnLayer(layer) for layer in copper_layers)):
                continue
            pads.append((footprint, pad, pad.GetBoundingBox()))
    return pads


def smd_pad_hits(pads, pos):
    """All indexed undrilled component lands whose copper contains ``pos``."""
    hits = []
    for footprint, pad, bbox in pads:
        if not bbox.Contains(pos) or not pad.HitTest(pos):
            continue
        hits.append({
            "ref": footprint.GetReference(),
            "pad": pad.GetNumber(),
            "pad_net": pad.GetNetname(),
        })
    return hits


def inspect(before_path, after_path):
    before = pcbnew.LoadBoard(str(before_path))
    after = pcbnew.LoadBoard(str(after_path))
    findings = []
    pads = copper_smd_pads(after)
    for via in newly_added_vias(before, after):
        hits = smd_pad_hits(pads, via.GetPosition())
        if not hits:
            continue
        pos = via.GetPosition()
        findings.append({
            "via_net": via.GetNetname(),
            "x_mm": round(pos.x / 1e6, 6),
            "y_mm": round(pos.y / 1e6, 6),
            # KiCad 9/10's via diameter is layer-aware; the no-argument
            # overload asserts noisily on some versions. This policy handles
            # ordinary through vias, for which F.Cu is authoritative.
            "size_mm": round(via.GetWidth(pcbnew.F_Cu) / 1e6, 6),
            "drill_mm": round(via.GetDrillValue() / 1e6, 6),
            "pads": hits,
        })
    return findings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("before", type=Path)
    ap.add_argument("after", type=Path)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()
    findings = inspect(args.before, args.after)
    report = {
        "schema": 1,
        "before": str(args.before),
        "after": str(args.after),
        "new_via_in_pad": findings,
        "verdict": "FAIL" if findings else "PASS",
    }
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if findings:
        print(f"new via-in-pad: {len(findings)} router-created via(s) REFUSED")
        for finding in findings:
            pads = ", ".join(
                f"{p['ref']}.{p['pad']}[{p['pad_net']}]"
                for p in finding["pads"])
            print(f"  {finding['via_net']} via "
                  f"({finding['x_mm']},{finding['y_mm']}) "
                  f"{finding['size_mm']}/{finding['drill_mm']} mm in {pads}")
        return 1
    print("new via-in-pad: PASS (0 router-created vias in SMD lands)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
