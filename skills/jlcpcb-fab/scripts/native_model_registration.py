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
import json
import math
import os
from pathlib import Path
import re
import shutil
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
RECEIPT_KIND = "model-registration-receipt-v1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha(value) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def tool_identity() -> str:
    sources = [Path(__file__).resolve(), Path(__file__).with_name("twin_overlay.py")]
    identity = canonical_sha({path.name: sha256(path) for path in sources})
    return f"native-model-registration-v2:{identity}"


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


def _rounded(value: float) -> float:
    return round(float(value), 6)


def _rounded_box(box):
    return [_rounded(value) for value in box]


def normalized_footprint_projection(fp):
    """Return only the footprint datums that this registration gate grades.

    Board position, board rotation, refdes, UUID and unrelated graphics are
    intentionally absent.  Moving an instance therefore reuses the same
    physical-registration receipt, while any F.Fab, courtyard or drilled
    attachment-field change invalidates it.
    """
    clone = pcbnew.Cast_to_FOOTPRINT(fp.Duplicate(False))
    clone.SetOrientationDegrees(0.0)
    clone.SetPosition(pcbnew.VECTOR2I(0, 0))
    fab_items = []
    for item in clone.GraphicalItems():
        if item.GetLayer() != pcbnew.F_Fab or item.GetClass() == "PCB_TEXT":
            continue
        fab_items.append({
            "class": item.GetClass(),
            "bbox_mm": _rounded_box(mm_box(item.GetBoundingBox())),
        })
    pads = []
    for pad in clone.Pads():
        if pad.GetDrillSizeX() <= 0:
            continue
        position = pad.GetPosition()
        pads.append({
            "number": str(pad.GetNumber()),
            "position_mm": [_rounded(position.x / 1e6),
                            _rounded(position.y / 1e6)],
            "drill_mm": [_rounded(pad.GetDrillSizeX() / 1e6),
                         _rounded(pad.GetDrillSizeY() / 1e6)],
        })
    courtyard = courtyard_bbox(clone)
    if not fab_items or courtyard is None or not pads:
        raise ValueError("F.Fab, F.CrtYd and drilled pads are required")
    return {
        "side": "front" if fp.GetLayer() == pcbnew.F_Cu else "back",
        "fab": sorted(fab_items, key=lambda item: canonical_sha(item)),
        "courtyard_bbox_mm": _rounded_box(courtyard),
        "drilled_pads": sorted(pads, key=lambda item: (item["number"],
                                                        item["position_mm"])),
    }


def model_transform_projection(model):
    return {
        "offset": [_rounded(model.m_Offset.x), _rounded(model.m_Offset.y),
                   _rounded(model.m_Offset.z)],
        "rotation": [_rounded(model.m_Rotation.x),
                     _rounded(model.m_Rotation.y),
                     _rounded(model.m_Rotation.z)],
        "scale": [_rounded(model.m_Scale.x), _rounded(model.m_Scale.y),
                  _rounded(model.m_Scale.z)],
        "opacity": _rounded(model.m_Opacity),
    }


def registration_contract(refs, args):
    return {
        "refs": sorted(refs, key=ref_sort_key),
        "fit_tolerance_mm": _rounded(args.fit_tol_mm),
        "courtyard_containment_tolerance_mm": _rounded(args.courtyard_tol_mm),
        "search_margin_mm": _rounded(args.search_margin_mm),
        "render_width": int(args.width),
        "render_height": int(args.height),
    }


def registration_tuple(rows, refs, args):
    footprint_hashes = {
        canonical_sha(normalized_footprint_projection(row["fp"]))
        for row in rows
    }
    transform_hashes = {
        canonical_sha(model_transform_projection(list(row["fp"].Models())[0]))
        for row in rows
    }
    model_hashes = {row["model_sha"] for row in rows}
    if len(footprint_hashes) != 1:
        raise ValueError("declared refs do not share one registration footprint")
    if len(transform_hashes) != 1:
        raise ValueError("declared refs do not share one native-model transform")
    if len(model_hashes) != 1:
        raise ValueError("declared refs do not share one native model")
    contract_hash = args.contract_sha256 or canonical_sha(
        registration_contract(refs, args))
    identity = args.tool_identity or tool_identity()
    return {
        "footprint_sha256": next(iter(footprint_hashes)),
        "model_sha256": next(iter(model_hashes)),
        "transform_sha256": next(iter(transform_hashes)),
        "contract_sha256": contract_hash,
        "tool_identity": identity,
    }


def tuple_cache_key(tuple_value) -> str:
    return canonical_sha(tuple_value)


def _add_edge(board, start, end) -> None:
    edge = pcbnew.PCB_SHAPE(board)
    edge.SetShape(pcbnew.SHAPE_T_SEGMENT)
    edge.SetLayer(pcbnew.Edge_Cuts)
    edge.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(start[0]),
                                 pcbnew.FromMM(start[1])))
    edge.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(end[0]),
                               pcbnew.FromMM(end[1])))
    edge.SetWidth(pcbnew.FromMM(0.05))
    board.Add(edge)


def build_origin_coupon(rows, output: Path, search_margin_mm: float) -> str:
    """Build a deterministic, origin-centred board containing only subjects."""
    coupon = pcbnew.BOARD()
    model_name = "native_model" + rows[0]["model"].suffix.lower()
    shutil.copy2(rows[0]["model"], output.parent / model_name)
    normalized = []
    for row in rows:
        fp = pcbnew.Cast_to_FOOTPRINT(row["fp"].Duplicate(False))
        fp.SetOrientationDegrees(0.0)
        fp.SetPosition(pcbnew.VECTOR2I(0, 0))
        fp.ClearAllNets()
        for index, model in enumerate(fp.Models()):
            model.m_Filename = "${KIPRJMOD}/" + model_name
            fp.Models()[index] = model
        normalized.append((row["ref"], fp, courtyard_bbox(fp)))

    count = len(normalized)
    columns = max(1, math.ceil(math.sqrt(count)))
    row_count = math.ceil(count / columns)
    maximum_width = max(box[2] - box[0] for _, _, box in normalized)
    maximum_height = max(box[3] - box[1] for _, _, box in normalized)
    pitch_x = maximum_width + 2 * (search_margin_mm + 2.0)
    pitch_y = maximum_height + 2 * (search_margin_mm + 2.0)
    placed_boxes = []
    for index, (_ref, fp, box) in enumerate(normalized):
        column = index % columns
        row_number = index // columns
        x = (column - (columns - 1) / 2.0) * pitch_x
        y = (row_number - (row_count - 1) / 2.0) * pitch_y
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
        coupon.Add(fp)
        placed_boxes.append(courtyard_bbox(fp))

    margin = search_margin_mm + 3.0
    left = min(box[0] for box in placed_boxes) - margin
    top = min(box[1] for box in placed_boxes) - margin
    right = max(box[2] for box in placed_boxes) + margin
    bottom = max(box[3] for box in placed_boxes) + margin
    _add_edge(coupon, (left, top), (right, top))
    _add_edge(coupon, (right, top), (right, bottom))
    _add_edge(coupon, (right, bottom), (left, bottom))
    _add_edge(coupon, (left, bottom), (left, top))
    pcbnew.SaveBoard(str(output), coupon)
    return model_name


def resolve_model(board_path: Path, token: str) -> Path:
    value = token.replace("${KIPRJMOD}", str(board_path.parent))
    return Path(os.path.expandvars(os.path.expanduser(value))).resolve()


def collect_source_rows(board_path: Path, refs, wanted_model_sha: str):
    board = pcbnew.LoadBoard(str(board_path))
    if board is None:
        raise ValueError(f"could not load {board_path}")
    rows = []
    for ref in refs:
        fp = board.FindFootprintByReference(ref)
        if fp is None:
            raise ValueError(f"missing registration ref {ref}")
        models = list(fp.Models())
        if len(models) != 1:
            raise ValueError(
                f"{ref}: expected exactly one native model, found {len(models)}")
        model_path = resolve_model(board_path, models[0].m_Filename)
        if not model_path.is_file():
            raise ValueError(f"{ref}: native model does not resolve: {model_path}")
        model_sha = sha256(model_path)
        if model_sha.lower() != wanted_model_sha.lower():
            raise ValueError(
                f"{ref}: model SHA mismatch: {model_sha}, wanted {wanted_model_sha}")
        fab = fab_bbox(fp)
        courtyard = courtyard_bbox(fp)
        if fab is None or courtyard is None:
            raise ValueError(f"{ref}: F.Fab body and F.CrtYd are both required")
        pads = []
        for pad in fp.Pads():
            if pad.GetDrillSizeX() <= 0:
                continue
            position = pad.GetPosition()
            pads.append((pad.GetNumber(), position.x / 1e6, position.y / 1e6))
        if not pads:
            raise ValueError(f"{ref}: no drilled attachment pads")
        rows.append({
            "ref": ref, "fp": fp, "model": model_path, "model_sha": model_sha,
            "fab": fab, "courtyard": courtyard, "pads": pads,
        })
    return board, rows


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


def ref_sort_key(value: str):
    return tuple(
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", value)
    )


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
    parser.add_argument("--contract-sha256")
    parser.add_argument("--tool-identity")
    args = parser.parse_args(argv)

    board_path = Path(args.board).resolve()
    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    refs = parse_refs(args.refs)
    if not refs or len(refs) != len(set(refs)):
        raise SystemExit("refs must be non-empty and unique")
    refs = sorted(refs, key=ref_sort_key)
    if args.contract_sha256 and (len(args.contract_sha256) != 64 or any(
            char not in "0123456789abcdef" for char in args.contract_sha256.lower())):
        raise SystemExit("contract-sha256 must be lowercase SHA-256")
    if args.tool_identity is not None and not args.tool_identity.strip():
        raise SystemExit("tool-identity must be non-empty")
    original_sha = sha256(board_path)
    try:
        _source_board, rows = collect_source_rows(
            board_path, refs, args.model_sha256)
    except ValueError as exc:
        raise SystemExit(str(exc))

    try:
        tuple_value = registration_tuple(rows, refs, args)
    except ValueError as exc:
        raise SystemExit(str(exc))

    coupon_board = outdir / "native_coupon.kicad_pcb"
    build_origin_coupon(rows, coupon_board, args.search_margin_mm)
    board = pcbnew.LoadBoard(str(coupon_board))
    if board is None:
        raise SystemExit(f"could not load generated coupon {coupon_board}")
    coupon_rows = []
    by_ref = {row["ref"]: row for row in rows}
    for ref in refs:
        fp = board.FindFootprintByReference(ref)
        if fp is None:
            raise SystemExit(f"generated coupon is missing registration ref {ref}")
        source = by_ref[ref]
        fab = fab_bbox(fp)
        courtyard = courtyard_bbox(fp)
        pads = []
        for pad in fp.Pads():
            if pad.GetDrillSizeX() <= 0:
                continue
            position = pad.GetPosition()
            pads.append((pad.GetNumber(), position.x / 1e6, position.y / 1e6))
        coupon_rows.append({
            "ref": ref, "fp": fp, "model": source["model"],
            "model_sha": source["model_sha"], "fab": fab,
            "courtyard": courtyard, "pads": pads,
        })
    rows = coupon_rows
    edge = mm_box(board.GetBoardEdgesBoundingBox())

    populated_png = outdir / "native_top.png"
    bare_board = outdir / "native_bare.kicad_pcb"
    bare_png = outdir / "native_bare_top.png"
    render(coupon_board, populated_png, args.width, args.height)
    bare = pcbnew.LoadBoard(str(coupon_board))
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
        f"coupon_sha256: {sha256(coupon_board)}",
        f"a-render_verdict: {'FAIL' if failures else 'PASS'}",
        "registration_kind: P-MODEL-REG",
        "render_source: origin-centred per-tuple coupon with provenance-bound native models",
        f"model_sha256: {args.model_sha256}",
        f"footprint_registration_datum_sha256: {tuple_value['footprint_sha256']}",
        f"model_transform_sha256: {tuple_value['transform_sha256']}",
        f"registration_contract_sha256: {tuple_value['contract_sha256']}",
        f"tuple_cache_key: {tuple_cache_key(tuple_value)}",
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

    evidence = sorted([
        "native_bare_top.png",
        "native_top.png",
        "native_top_registration_overlay.png",
        *[f"native_overlay_{row['ref']}.png" for row in rows
          if "body" in row],
    ])
    measurements = []
    for row in sorted(rows, key=lambda item: ref_sort_key(item["ref"])):
        pad_results = row.get("pad_results", [])
        measurements.append({
            "ref": row["ref"],
            "attachment_centres_graded": sum(
                1 for _number, inside, *_rest in pad_results if inside),
            "attachment_centres_total": len(row["pads"]),
            "centre_delta_mm": (_rounded(row["centre_delta"])
                                if "centre_delta" in row else None),
            "fab_outward_mm": (_rounded(row["body_outward"])
                               if "body_outward" in row else None),
            "courtyard_outward_mm": (_rounded(row["courtyard_outward"])
                                     if "courtyard_outward" in row else None),
        })
    receipt = {
        "schema": 1,
        "kind": RECEIPT_KIND,
        "tuple": tuple_value,
        "refs": sorted(refs, key=ref_sort_key),
        "measurements": measurements,
        "evidence": evidence,
    }
    (outdir / "model_registration_receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
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
