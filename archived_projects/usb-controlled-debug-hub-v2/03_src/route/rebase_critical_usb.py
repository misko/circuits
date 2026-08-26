#!/usr/bin/env python3
"""Rebase the authenticated critical USB copper onto a regenerated r0 board."""

from pathlib import Path
import argparse
import math
import shutil
import zlib
import pcbnew


USB_NETS = {
    "P1_HUB_P", "P1_HUB_N", "P2_HUB_P", "P2_HUB_N",
    "P3_HUB_P", "P3_HUB_N", "P4_HUB_P", "P4_HUB_N",
    "UP_HUB_P", "UP_HUB_N",
}


def point_mm(point):
    return (pcbnew.ToMM(point.x), pcbnew.ToMM(point.y))


def close_point(a, b, tolerance_mm):
    ax, ay = point_mm(a)
    bx, by = point_mm(b)
    return math.hypot(ax - bx, ay - by) <= tolerance_mm


def same_track(a, b, tolerance_mm):
    return (
        a.GetClass() == b.GetClass() == "PCB_TRACK"
        and a.GetNetname() == b.GetNetname()
        and a.GetLayer() == b.GetLayer()
        and abs(pcbnew.ToMM(a.GetWidth() - b.GetWidth())) <= tolerance_mm
        and (
            (close_point(a.GetStart(), b.GetStart(), tolerance_mm)
             and close_point(a.GetEnd(), b.GetEnd(), tolerance_mm))
            or
            (close_point(a.GetStart(), b.GetEnd(), tolerance_mm)
             and close_point(a.GetEnd(), b.GetStart(), tolerance_mm))
        )
    )


def same_via(a, b, tolerance_mm):
    return (
        a.GetClass() == b.GetClass() == "PCB_VIA"
        and a.GetNetname() == b.GetNetname()
        and close_point(a.GetPosition(), b.GetPosition(), tolerance_mm)
        and abs(pcbnew.ToMM(a.GetDrillValue() - b.GetDrillValue())) <= tolerance_mm
        and abs(pcbnew.ToMM(a.GetWidth(pcbnew.F_Cu)
                           - b.GetWidth(pcbnew.F_Cu))) <= tolerance_mm
    )


def equivalent(a, b, tolerance_mm):
    return same_track(a, b, tolerance_mm) or same_via(a, b, tolerance_mm)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base", type=Path)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--tolerance-mm", type=float, default=0.002)
    args = parser.parse_args()

    base = pcbnew.LoadBoard(str(args.base))
    source = pcbnew.LoadBoard(str(args.source))
    # Duplicate() allocates fresh KIID values. Seed KiCad's generator so an
    # unchanged base/source pair produces a byte-identical authenticated PCB.
    seed_material = f"{args.base.resolve()}::{args.source.resolve()}::critical-usb"
    pcbnew.KIID.SeedGenerator(zlib.crc32(seed_material.encode()) & 0xFFFFFFFF)
    base_items = list(base.GetTracks())
    added = 0
    retained = 0

    for item in source.GetTracks():
        if item.GetNetname() not in USB_NETS:
            continue
        if any(equivalent(item, existing, args.tolerance_mm)
               for existing in base_items):
            retained += 1
            continue
        duplicate = item.Duplicate()
        duplicate.SetNet(base.FindNet(item.GetNetname()))
        base.Add(duplicate)
        base_items.append(duplicate)
        added += 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    pcbnew.SaveBoard(str(args.output), base)
    # KiCad resolves custom rules and project settings from sidecars sharing
    # the board stem. A rebased PCB with stale sidecars can therefore fail a
    # rule that the regenerated r0 correctly scopes. Keep the authenticated
    # checkpoint's complete board context synchronized with its base.
    for suffix in (".kicad_dru", ".kicad_pro", ".kicad_prl"):
        source_sidecar = args.base.with_suffix(suffix)
        output_sidecar = args.output.with_suffix(suffix)
        if source_sidecar.exists():
            shutil.copy2(source_sidecar, output_sidecar)
    print(f"rebased critical USB copper: {added} added, {retained} retained")


if __name__ == "__main__":
    main()
