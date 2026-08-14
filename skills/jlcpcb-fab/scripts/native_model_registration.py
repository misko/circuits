#!/usr/bin/env python3
"""Grade native 3D-body registration against independent footprint geometry.

This is deliberately separate from ``twin_overlay.py``.  The twin overlay
answers whether rendered pixels agree with the mounted catalog mesh.  This
gate answers whether a provenance-bound native model agrees with the
footprint's F.Fab body, courtyard, and drilled attachment field.
"""

from __future__ import annotations

import argparse
import hashlib
import math
import os
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont
import pcbnew

from twin_overlay import board_extent_px, extract_body


ORANGE = (255, 165, 0)
GREEN = (0, 255, 0)
MAGENTA = (255, 0, 255)
CYAN = (0, 255, 255)
BLUE = (0, 150, 255)
WHITE = (255, 255, 255)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mm_box(box):
    return (
        box.GetLeft() / 1e6,
        box.GetTop() / 1e6,
        box.GetRight() / 1e6,
        box.GetBottom() / 1e6,
    )


def union_boxes(boxes):
    return (
        min(box[0] for box in boxes),
        min(box[1] for box in boxes),
        max(box[2] for box in boxes),
        max(box[3] for box in boxes),
    )


def fab_bbox(fp):
    boxes = [
        mm_box(item.GetBoundingBox())
        for item in fp.GraphicalItems()
        if item.GetLayer() == pcbnew.F_Fab and item.GetClass() != "PCB_TEXT"
    ]
    return union_boxes(boxes) if boxes else None


def courtyard_bbox(fp):
    courtyard = fp.GetCourtyard(pcbnew.F_CrtYd)
    return mm_box(courtyard.BBox()) if courtyard.OutlineCount() else None


def resolve_model(board_path: Path, token: str) -> Path:
    value = token.replace("${KIPRJMOD}", str(board_path.parent))
    return Path(os.path.expandvars(os.path.expanduser(value))).resolve()


def render(board: Path, output: Path, width: int, height: int) -> None:
    command = [
        "kicad-cli", "pcb", "render", "--width", str(width), "--height",
        str(height), "--quality", "basic", "--side", "top", "-o",
        str(output), str(board),
    ]
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise SystemExit(f"native render failed ({result.returncode}): {board}")


def px_box(box, x_of, y_of):
    return (
        round(x_of(box[0])), round(y_of(box[1])),
        round(x_of(box[2])), round(y_of(box[3])),
    )


def measured_mm(box, mm_x, mm_y):
    return (mm_x(box[0]), mm_y(box[1]), mm_x(box[2]), mm_y(box[3]))


def centre_delta(a, b):
    return math.hypot(
        (a[0] + a[2] - b[0] - b[2]) / 2,
        (a[1] + a[3] - b[1] - b[3]) / 2,
    )


def outward(measured, expected):
    return max(
        0.0,
        expected[0] - measured[0], expected[1] - measured[1],
        measured[2] - expected[2], measured[3] - expected[3],
    )


def excursion(body, courtyard):
    return max(
        0.0,
        courtyard[0] - body[0], courtyard[1] - body[1],
        body[2] - courtyard[2], body[3] - courtyard[3],
    )


def parse_refs(value: str):
    refs = []
    for token in value.split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            left, right = token.split("-", 1)
            prefix = "".join(ch for ch in left if not ch.isdigit())
            start = int(left[len(prefix):])
            if not right.startswith(prefix):
                right = prefix + right
            stop = int(right[len(prefix):])
            refs.extend(f"{prefix}{number}" for number in range(start, stop + 1))
        else:
            refs.append(token)
    return refs


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("board")
    parser.add_argument("outdir")
    parser.add_argument("--refs", required=True,
                        help="comma list and/or same-prefix range, e.g. J2-J10")
    parser.add_argument("--model-sha256", required=True)
    parser.add_argument("--fit-tol-mm", type=float, default=1.0)
    parser.add_argument("--courtyard-tol-mm", type=float, default=0.25)
    parser.add_argument("--search-margin-mm", type=float, default=8.0)
    parser.add_argument("--width", type=int, default=2400)
    parser.add_argument("--height", type=int, default=1600)
    args = parser.parse_args(argv)

    board_path = Path(args.board).resolve()
    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    refs = parse_refs(args.refs)
    original_sha = sha256(board_path)
    board = pcbnew.LoadBoard(str(board_path))
    if board is None:
        raise SystemExit(f"could not load {board_path}")

    edge = mm_box(board.GetBoardEdgesBoundingBox())
    rows = []
    for ref in refs:
        fp = board.FindFootprintByReference(ref)
        if fp is None:
            raise SystemExit(f"missing registration ref {ref}")
        models = list(fp.Models())
        if len(models) != 1:
            raise SystemExit(f"{ref}: expected exactly one native model, found {len(models)}")
        model_path = resolve_model(board_path, models[0].m_Filename)
        if not model_path.is_file():
            raise SystemExit(f"{ref}: native model does not resolve: {model_path}")
        model_sha = sha256(model_path)
        if model_sha.lower() != args.model_sha256.lower():
            raise SystemExit(
                f"{ref}: model SHA mismatch: {model_sha}, wanted {args.model_sha256}"
            )
        fab = fab_bbox(fp)
        courtyard = courtyard_bbox(fp)
        if fab is None or courtyard is None:
            raise SystemExit(f"{ref}: F.Fab body and F.CrtYd are both required")
        pads = []
        for pad in fp.Pads():
            if pad.GetDrillSizeX() <= 0:
                continue
            position = pad.GetPosition()
            pads.append((pad.GetNumber(), position.x / 1e6, position.y / 1e6))
        if not pads:
            raise SystemExit(f"{ref}: no drilled attachment pads")
        rows.append({
            "ref": ref, "fp": fp, "model": model_path, "model_sha": model_sha,
            "fab": fab, "courtyard": courtyard, "pads": pads,
        })

    populated_png = outdir / "native_top.png"
    bare_board = outdir / "native_bare.kicad_pcb"
    bare_png = outdir / "native_bare_top.png"
    render(board_path, populated_png, args.width, args.height)
    bare = pcbnew.LoadBoard(str(board_path))
    for fp in bare.GetFootprints():
        fp.Models().clear()
    bare.Save(str(bare_board))
    render(bare_board, bare_png, args.width, args.height)
    if sha256(board_path) != original_sha:
        raise SystemExit("source board changed during native registration render")

    image = Image.open(populated_png).convert("RGB")
    bare_image = Image.open(bare_png).convert("RGB")
    extent = board_extent_px(bare_image)
    if extent is None:
        raise SystemExit("could not calibrate the rendered board extent")
    min_x, min_y, max_x, max_y = extent
    scale_x = (max_x - min_x + 1) / (edge[2] - edge[0])
    scale_y = (max_y - min_y + 1) / (edge[3] - edge[1])
    anisotropy = scale_x / scale_y
    if abs(anisotropy - 1.0) > 0.02:
        raise SystemExit(f"render anisotropy {anisotropy:.4f} exceeds 0.02")
    x_of = lambda value: min_x + (value - edge[0]) * scale_x
    y_of = lambda value: min_y + (value - edge[1]) * scale_y
    mm_x = lambda value: edge[0] + (value - min_x) / scale_x
    mm_y = lambda value: edge[1] + (value - min_y) / scale_y

    expected_px = {row["ref"]: px_box(row["fab"], x_of, y_of) for row in rows}
    failures = []
    overlay = image.copy()
    draw = ImageDraw.Draw(overlay)
    draw.rectangle(px_box(edge, x_of, y_of), outline=BLUE, width=3)
    for row in rows:
        expected = row["fab"]
        courtyard = row["courtyard"]
        margin = args.search_margin_mm
        search = (
            expected[0] - margin, expected[1] - margin,
            expected[2] + margin, expected[3] + margin,
        )
        window = px_box(search, x_of, y_of)
        centre = (
            round(x_of((expected[0] + expected[2]) / 2)),
            round(y_of((expected[1] + expected[3]) / 2)),
        )
        blocked = [
            box for ref, box in expected_px.items() if ref != row["ref"]
        ]
        measured = extract_body(
            image.load(), image.size, window, centre, blocked=blocked,
            protect=expected_px[row["ref"]], bare_px=bare_image.load(),
        )
        if measured is None:
            failures.append(f"{row['ref']}: native body pixels were not measured")
            continue
        measured_px, pixel_count, touched = measured
        body = measured_mm(measured_px, mm_x, mm_y)
        delta = centre_delta(body, expected)
        body_outward = outward(body, expected)
        courtyard_outward = excursion(body, courtyard)
        pad_results = []
        for number, x, y in row["pads"]:
            inside = body[0] <= x <= body[2] and body[1] <= y <= body[3]
            margin_to_body = min(x - body[0], y - body[1], body[2] - x, body[3] - y)
            pad_results.append((number, inside, margin_to_body, x, y))
        if delta > args.fit_tol_mm:
            failures.append(f"{row['ref']}: body/F.Fab centre delta {delta:.3f} mm")
        if body_outward > args.fit_tol_mm:
            failures.append(f"{row['ref']}: body exceeds F.Fab by {body_outward:.3f} mm")
        if courtyard_outward > args.courtyard_tol_mm:
            failures.append(
                f"{row['ref']}: body exceeds F.CrtYd by {courtyard_outward:.3f} mm"
            )
        if touched:
            failures.append(f"{row['ref']}: body measurement touched search window")
        missed = [number for number, inside, *_ in pad_results if not inside]
        if missed:
            failures.append(f"{row['ref']}: drilled pad centres outside body: {missed}")
        row.update({
            "body": body, "body_px": measured_px, "pixels": pixel_count,
            "centre_delta": delta, "body_outward": body_outward,
            "courtyard_outward": courtyard_outward, "pad_results": pad_results,
        })

        draw.rectangle(px_box(courtyard, x_of, y_of), outline=ORANGE, width=4)
        draw.rectangle(px_box(expected, x_of, y_of), outline=GREEN, width=4)
        draw.rectangle(measured_px, outline=MAGENTA, width=4)
        for number, _inside, _pad_margin, x, y in pad_results:
            px, py = round(x_of(x)), round(y_of(y))
            radius = max(5, round(0.22 * (scale_x + scale_y)))
            draw.ellipse((px-radius, py-radius, px+radius, py+radius),
                         outline=CYAN, width=3)
            if number == "1":
                draw.line((px-radius, py, px+radius, py), fill=CYAN, width=3)
                draw.line((px, py-radius, px, py+radius), fill=CYAN, width=3)

        crop_box = px_box((courtyard[0]-2, courtyard[1]-2,
                           courtyard[2]+2, courtyard[3]+2), x_of, y_of)
        crop_box = (max(0, crop_box[0]), max(0, crop_box[1]),
                    min(image.width, crop_box[2]), min(image.height, crop_box[3]))
        overlay.crop(crop_box).save(outdir / f"native_overlay_{row['ref']}.png")

    legend = (
        "Native model registration: ORANGE F.CrtYd | GREEN F.Fab expected | "
        "PINK measured native-model pixels | CYAN drilled pads | BLUE PCB edge"
    )
    draw.rectangle((12, 12, min(image.width-12, 1420), 58), fill=(0, 0, 0))
    draw.text((22, 23), legend, fill=WHITE)
    overlay_path = outdir / "native_top_registration_overlay.png"
    overlay.save(overlay_path)

    report_path = outdir / "native_model_registration.md"
    lines = [
        f"# Native model physical registration — `{populated_png.name}`",
        "",
        f"board_sha256: {original_sha}",
        f"a-render_verdict: {'FAIL' if failures else 'PASS'}",
        "registration_kind: P-MODEL-REG",
        "render_source: exact project board with provenance-bound native models",
        f"model_sha256: {args.model_sha256}",
        f"calibration_px_per_mm: {scale_x:.4f} x, {scale_y:.4f} y",
        f"anisotropy: {anisotropy:.4f}",
        f"fit_tolerance_mm: {args.fit_tol_mm:.3f}",
        f"courtyard_containment_tolerance_mm: {args.courtyard_tol_mm:.3f}",
        f"overlay: {overlay_path.name}",
        "",
        "Orange is F.CrtYd; green is the independent F.Fab body envelope; "
        "pink is the populated-minus-bare native-model pixel envelope; cyan "
        "is the drilled attachment field. Pink/green agreement alone is not "
        "enough: both must also register to the footprint and courtyard.",
        "",
        "| ref | centre delta mm | measured beyond F.Fab mm | measured beyond courtyard mm | drilled centres inside | min pad margin mm |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        if "body" not in row:
            lines.append(f"| {row['ref']} | N/A | N/A | N/A | 0/{len(row['pads'])} | N/A |")
            continue
        inside = sum(result[1] for result in row["pad_results"])
        minimum = min(result[2] for result in row["pad_results"])
        lines.append(
            f"| {row['ref']} | {row['centre_delta']:.3f} | "
            f"{row['body_outward']:.3f} | {row['courtyard_outward']:.3f} | "
            f"{inside}/{len(row['pad_results'])} | {minimum:.3f} |"
        )
    lines += ["", "## Failures", ""]
    lines += [f"- {finding}" for finding in failures] or ["- none"]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        f"P-MODEL-REG {'FAIL' if failures else 'PASS'}: "
        f"{len(rows)} native model instance(s), {sum(len(r['pads']) for r in rows)} "
        f"drilled attachment centres -> {report_path}"
    )
    for finding in failures:
        print(f"  FAIL {finding}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
