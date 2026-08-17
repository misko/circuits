#!/usr/bin/env python3
"""Prove connector access orientation and publish focused human-review views.

The existing P-MODEL-REG gate proves that a model is registered to its land.
This gate adds the semantic fact that pixels and symmetric holes cannot infer:
which model direction is the connector mouth/access direction.  That fact is
authored once from the manufacturer drawing/STEP, transformed through the
model and footprint frames, checked against Edge.Cuts, and then presented in
fixed exact-board cameras with coordinate-selected crops for explicit human
approval. Image differences never select or grade the target connector.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont
import pcbnew
import yaml

from twin_overlay import board_extent_px

KIND = "connector-orientation-receipt-v1"
APPROVAL_KIND = "connector-orientation-approval-v1"
TOOL_VERSION = "connector-orientation-gate-v1"
CAMERAS = ("top", "left", "right", "front", "back")
CARDINAL_CAMERA = {
    (-1, 0): "left", (1, 0): "right",
    (0, -1): "back", (0, 1): "front",
}
EDGE_FACES = {
    "x0": {"name": "west", "axis": (-1.0, 0.0, 0.0)},
    "x1": {"name": "east", "axis": (1.0, 0.0, 0.0)},
    "y0": {"name": "north", "axis": (0.0, -1.0, 0.0)},
    "y1": {"name": "south", "axis": (0.0, 1.0, 0.0)},
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_sha(value) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z")


def tool_identity() -> str:
    try:
        version = subprocess.run(
            ["kicad-cli", "--version"], text=True, capture_output=True,
            check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        version = "kicad-cli-unavailable"
    return f"{TOOL_VERSION}:{canonical_sha({'script': digest(Path(__file__)), 'kicad': version})}"


def vec3(value, where: str):
    if (not isinstance(value, list) or len(value) != 3 or
            any(not isinstance(item, (int, float)) or isinstance(item, bool)
                or not math.isfinite(float(item)) for item in value)):
        raise ValueError(f"{where} must be a finite three-number vector")
    vector = tuple(float(item) for item in value)
    length = math.sqrt(sum(item * item for item in vector))
    if length <= 1e-9:
        raise ValueError(f"{where} must be non-zero")
    return tuple(item / length for item in vector)


def dot(a, b) -> float:
    return sum(x * y for x, y in zip(a, b))


def rotate_xyz(vector, rotation_deg, scale=(1.0, 1.0, 1.0)):
    x, y, z = (vector[index] * scale[index] for index in range(3))
    rx, ry, rz = (math.radians(float(value)) for value in rotation_deg)
    y, z = y * math.cos(rx) - z * math.sin(rx), y * math.sin(rx) + z * math.cos(rx)
    x, z = x * math.cos(ry) + z * math.sin(ry), -x * math.sin(ry) + z * math.cos(ry)
    x, y = x * math.cos(rz) - y * math.sin(rz), x * math.sin(rz) + y * math.cos(rz)
    length = math.sqrt(x*x + y*y + z*z)
    if length <= 1e-9:
        raise ValueError("model transform collapses an orientation axis")
    return (x/length, y/length, z/length)


def footprint_to_board(vector, fp):
    x, y, z = vector
    if fp.GetLayer() == pcbnew.B_Cu:
        x = -x
        z = -z
    theta = math.radians(fp.GetOrientationDegrees())
    # KiCad's footprint coordinates are y-down.  pcbnew therefore realizes a
    # positive footprint angle with the y-down operator below (confirmed from
    # actual pad positions at 90 and 270 degrees), not the conventional
    # Cartesian y-up matrix.  The two forms coincide at 0/180, which is why a
    # connector suite containing only those rotations did not expose the bug.
    return (
        x * math.cos(theta) + y * math.sin(theta),
        -x * math.sin(theta) + y * math.cos(theta),
        z,
    )


def board_outline(board):
    polygons = pcbnew.SHAPE_POLY_SET()
    if not board.GetBoardPolygonOutlines(polygons, False) or polygons.OutlineCount() != 1:
        raise ValueError("orientation gate requires one closed Edge.Cuts outline")
    outline = polygons.Outline(0)
    points = [(outline.CPoint(i).x / 1e6, outline.CPoint(i).y / 1e6)
              for i in range(outline.PointCount())]
    if len(points) < 3:
        raise ValueError("Edge.Cuts outline has fewer than three points")
    return points


def point_in_polygon(point, polygon) -> bool:
    x, y = point
    inside = False
    j = len(polygon) - 1
    for i, (xi, yi) in enumerate(polygon):
        xj, yj = polygon[j]
        if ((yi > y) != (yj > y) and
                x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def ray_segment_distance(origin, direction, a, b):
    ox, oy = origin
    dx, dy = direction
    ax, ay = a
    sx, sy = b[0] - ax, b[1] - ay
    determinant = dx * sy - dy * sx
    if abs(determinant) < 1e-10:
        return None
    qx, qy = ax - ox, ay - oy
    t = (qx * sy - qy * sx) / determinant
    u = (qx * dy - qy * dx) / determinant
    if t >= -1e-8 and -1e-8 <= u <= 1 + 1e-8:
        return max(0.0, t)
    return None


def first_outline_hit(origin, direction, polygon):
    distances = []
    for index, start in enumerate(polygon):
        distance = ray_segment_distance(
            origin, direction, start, polygon[(index + 1) % len(polygon)])
        if distance is not None:
            distances.append(distance)
    distances = [value for value in distances if value > 1e-6]
    if not distances:
        raise ValueError("access ray does not intersect Edge.Cuts")
    return min(distances)


def edge_name(point, polygon, tolerance=0.35):
    xs = [value[0] for value in polygon]
    ys = [value[1] for value in polygon]
    candidates = {
        "west": abs(point[0] - min(xs)), "east": abs(point[0] - max(xs)),
        "north": abs(point[1] - min(ys)), "south": abs(point[1] - max(ys)),
    }
    name, distance = min(candidates.items(), key=lambda item: item[1])
    return name if distance <= tolerance else "non-cardinal"


def resolve_model(board_path: Path, filename: str) -> Path:
    value = filename.replace("${KIPRJMOD}", str(board_path.parent))
    for key, replacement in os.environ.items():
        value = value.replace("${" + key + "}", replacement)
    return Path(os.path.expandvars(os.path.expanduser(value))).resolve()


def normalized_orientation(group):
    raw = group.get("orientation")
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError(f"{group.get('id')}.orientation must be a mapping")
    required = {
        "authority", "mount_side", "footprint_access_axis_local",
        "model_access_axis_local", "model_up_axis_local",
        "mating_plane_offset_mm", "edge_offset_range_mm", "key_pad",
    }
    missing = sorted(required - set(raw))
    if missing:
        raise ValueError(f"{group.get('id')}.orientation missing {missing}")
    mount_side = str(raw["mount_side"]).lower()
    if mount_side not in ("front", "back"):
        raise ValueError("orientation mount_side must be front or back")
    edge_range = raw["edge_offset_range_mm"]
    if (not isinstance(edge_range, list) or len(edge_range) != 2 or
            any(not isinstance(value, (int, float)) or isinstance(value, bool)
                or not math.isfinite(float(value)) for value in edge_range) or
            float(edge_range[0]) > float(edge_range[1])):
        raise ValueError("edge_offset_range_mm must be [minimum, maximum]")
    angle = float(raw.get("angular_tolerance_deg", 1.0))
    if not math.isfinite(angle) or angle < 0 or angle > 20:
        raise ValueError("angular_tolerance_deg must be between 0 and 20")
    plane = float(raw["mating_plane_offset_mm"])
    if not math.isfinite(plane) or plane <= 0:
        raise ValueError("mating_plane_offset_mm must be positive")
    authority = str(raw["authority"]).strip()
    if not authority:
        raise ValueError("orientation authority must be non-empty")
    if not str(raw["key_pad"]).strip():
        raise ValueError("orientation key_pad must be non-empty")
    z_range = raw.get("model_z_offset_range_mm", [-0.25, 0.25])
    if (not isinstance(z_range, list) or len(z_range) != 2 or
            any(not isinstance(value, (int, float)) or isinstance(value, bool)
                or not math.isfinite(float(value)) for value in z_range) or
            float(z_range[0]) > float(z_range[1])):
        raise ValueError("model_z_offset_range_mm must be [minimum, maximum]")
    return {
        "authority": authority,
        "mount_side": mount_side,
        "footprint_access_axis_local": vec3(
            raw["footprint_access_axis_local"], "footprint_access_axis_local"),
        "model_access_axis_local": vec3(
            raw["model_access_axis_local"], "model_access_axis_local"),
        "model_up_axis_local": vec3(raw["model_up_axis_local"],
                                    "model_up_axis_local"),
        "mating_plane_offset_mm": plane,
        "edge_offset_range_mm": [float(edge_range[0]), float(edge_range[1])],
        "key_pad": str(raw["key_pad"]),
        "angular_tolerance_deg": angle,
        "model_z_offset_range_mm": [float(z_range[0]), float(z_range[1])],
    }


def placement_projection(board, refs, polygon):
    rows = []
    for ref in refs:
        fp = board.FindFootprintByReference(ref)
        models = []
        for model in fp.Models():
            models.append({
                "filename": model.m_Filename,
                "offset": [model.m_Offset.x, model.m_Offset.y, model.m_Offset.z],
                "rotation": [model.m_Rotation.x, model.m_Rotation.y,
                             model.m_Rotation.z],
                "scale": [model.m_Scale.x, model.m_Scale.y, model.m_Scale.z],
            })
        position = fp.GetPosition()
        rows.append({
            "ref": fp.GetReference(),
            "position_mm": [round(position.x / 1e6, 6),
                            round(position.y / 1e6, 6)],
            "rotation_deg": round(fp.GetOrientationDegrees(), 6),
            "side": "front" if fp.GetLayer() == pcbnew.F_Cu else "back",
            "models": models,
        })
    return {"outline_mm": polygon, "placements": rows}


def grade_ref(fp, board_path: Path, orientation, edge_face, model_sha, polygon):
    failures = []
    models = list(fp.Models())
    if len(models) != 1:
        raise ValueError(f"{fp.GetReference()}: expected exactly one 3D model")
    model = models[0]
    model_path = resolve_model(board_path, model.m_Filename)
    if not model_path.is_file() or digest(model_path) != model_sha:
        failures.append("native model identity differs from the registration contract")
    side = "front" if fp.GetLayer() == pcbnew.F_Cu else "back"
    if side != orientation["mount_side"]:
        failures.append(f"mount side is {side}, expected {orientation['mount_side']}")

    rotation = (model.m_Rotation.x, model.m_Rotation.y, model.m_Rotation.z)
    scale = (model.m_Scale.x, model.m_Scale.y, model.m_Scale.z)
    model_access = rotate_xyz(orientation["model_access_axis_local"], rotation, scale)
    model_up = rotate_xyz(orientation["model_up_axis_local"], rotation, scale)
    footprint_access = orientation["footprint_access_axis_local"]
    cosine = math.cos(math.radians(orientation["angular_tolerance_deg"]))
    model_alignment = dot(model_access, footprint_access)
    up_alignment = dot(model_up, (0.0, 0.0, 1.0))
    if model_alignment < cosine:
        failures.append(f"model access axis disagrees with footprint ({model_alignment:.6f})")
    if up_alignment < cosine:
        failures.append(f"model up axis is inverted/rolled ({up_alignment:.6f})")
    if scale[0] * scale[1] * scale[2] <= 0:
        failures.append("model scale is mirrored or degenerate")
    z_min, z_max = orientation["model_z_offset_range_mm"]
    if not z_min <= model.m_Offset.z <= z_max:
        failures.append(
            f"model Z offset {model.m_Offset.z:.6f} outside [{z_min}, {z_max}]")

    board_access = footprint_to_board(footprint_access, fp)
    expected_axis = EDGE_FACES[edge_face["edge"]]["axis"]
    expected_edge = EDGE_FACES[edge_face["edge"]]["name"]
    board_alignment = dot(board_access, expected_axis)
    if board_alignment < cosine:
        failures.append(f"board access axis disagrees with contract ({board_alignment:.6f})")
    if abs(board_access[2]) > 1e-6:
        failures.append("edge connector access axis is not in the PCB plane")

    origin = (fp.GetPosition().x / 1e6, fp.GetPosition().y / 1e6)
    direction = (board_access[0], board_access[1])
    if not point_in_polygon(origin, polygon):
        failures.append("footprint origin is outside Edge.Cuts")
        edge_distance = math.nan
        hit = (math.nan, math.nan)
        actual_edge = "unknown"
        signed_offset = math.nan
    else:
        edge_distance = first_outline_hit(origin, direction, polygon)
        hit = (origin[0] + edge_distance * direction[0],
               origin[1] + edge_distance * direction[1])
        actual_edge = edge_name(hit, polygon)
        signed_offset = orientation["mating_plane_offset_mm"] - edge_distance
        if actual_edge != expected_edge:
            failures.append(f"access ray exits {actual_edge}, expected {expected_edge}")
        low, high = orientation["edge_offset_range_mm"]
        if not low <= signed_offset <= high:
            failures.append(
                f"mating-plane signed edge offset {signed_offset:.3f} mm "
                f"outside [{low:.3f}, {high:.3f}]")
        after = (hit[0] + direction[0] * 0.05,
                 hit[1] + direction[1] * 0.05)
        if point_in_polygon(after, polygon):
            failures.append("access ray does not leave the board after Edge.Cuts")

    pads = [pad for pad in fp.Pads() if str(pad.GetNumber()) == orientation["key_pad"]]
    if len(pads) != 1:
        failures.append(
            f"key pad {orientation['key_pad']} has denominator {len(pads)}, expected 1")
    return {
        "ref": fp.GetReference(),
        "access_axis_board": [round(value, 6) for value in board_access],
        "edge_face": edge_face,
        "expected_access_axis_board": [round(value, 6) for value in expected_axis],
        "board_axis_alignment": round(board_alignment, 6),
        "model_axis_alignment": round(model_alignment, 6),
        "model_up_alignment": round(up_alignment, 6),
        "edge": actual_edge,
        "edge_distance_mm": None if not math.isfinite(edge_distance) else round(edge_distance, 6),
        "mating_plane_edge_offset_mm": None if not math.isfinite(signed_offset) else round(signed_offset, 6),
        "key_pad": orientation["key_pad"],
        "failures": failures,
    }


def render(board: Path, output: Path, camera: str, width: int, height: int):
    result = subprocess.run([
        "kicad-cli", "pcb", "render", "--output", str(output),
        "--width", str(width), "--height", str(height), "--side", camera,
        "--quality", "basic", "--background", "opaque", str(board),
    ], text=True, capture_output=True)
    if result.returncode:
        raise ValueError(f"3D render failed for {camera}: {result.stderr or result.stdout}")


def top_geometry_bbox(populated: Path, fp, polygon):
    """Project exact footprint geometry; image diff never selects the ref."""
    image = Image.open(populated).convert("RGB")
    extent = board_extent_px(image)
    if extent is None:
        raise ValueError("top render has no measurable board region")
    xs = [point[0] for point in polygon]
    ys = [point[1] for point in polygon]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    ex0, ey0, ex1, ey1 = extent
    sx = (ex1 - ex0 + 1) / (x1 - x0)
    sy = (ey1 - ey0 + 1) / (y1 - y0)
    if abs(sx / sy - 1.0) > 0.03:
        raise ValueError(f"top render anisotropy {sx / sy:.4f} exceeds 0.03")
    box = fp.GetBoundingBox(False, False)
    bx0, by0 = box.GetX() / 1e6, box.GetY() / 1e6
    bx1, by1 = bx0 + box.GetWidth() / 1e6, by0 + box.GetHeight() / 1e6
    return (
        round(ex0 + (bx0 - x0) * sx), round(ey0 + (by0 - y0) * sy),
        round(ex0 + (bx1 - x0) * sx), round(ey0 + (by1 - y0) * sy),
    )


def side_board_span(image):
    """Find the projected board strip without using target-model pixels."""
    best = None
    y_start, y_stop = int(image.height * 0.35), int(image.height * 0.65)
    pixels = image.load()
    for y in range(y_start, y_stop):
        xs = []
        for x in range(image.width):
            r, g, b = pixels[x, y]
            if r < 125 and g < 135 and b < 105 and g > r - 20:
                xs.append(x)
        if len(xs) < 30:
            continue
        span = xs[-1] - xs[0] + 1
        density = len(xs) / span
        if density < 0.55:
            continue
        score = (span, density)
        if best is None or score > best[0]:
            best = (score, xs[0], xs[-1], y)
    if best is None:
        raise ValueError("side render has no measurable board strip")
    return best[1], best[2], best[3]


def side_geometry_window(populated: Path, fp, polygon, camera):
    """Select a side-view review window from board coordinates and camera."""
    image = Image.open(populated).convert("RGB")
    span0, span1, board_y = side_board_span(image)
    xs = [point[0] for point in polygon]
    ys = [point[1] for point in polygon]
    box = fp.GetBoundingBox(False, False)
    if camera in ("left", "right"):
        low, high = min(ys), max(ys)
        item0, item1 = box.GetY() / 1e6, (box.GetY() + box.GetHeight()) / 1e6
        reverse = camera == "right"
    else:
        low, high = min(xs), max(xs)
        item0, item1 = box.GetX() / 1e6, (box.GetX() + box.GetWidth()) / 1e6
        reverse = camera == "back"

    def project(value):
        fraction = (value - low) / (high - low)
        return span1 - fraction * (span1 - span0) if reverse else \
            span0 + fraction * (span1 - span0)

    projected = sorted((project(item0), project(item1)))
    vertical = max(120, int(image.height * 0.13))
    return (round(projected[0]), board_y - vertical,
            round(projected[1]), board_y + vertical)


def font(size: int):
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                 "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"):
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def focused_view(populated: Path, output: Path, ref: str, label: str,
                 metadata: str, detail: str, geometry_box, axis=None,
                 draw_box=True):
    image = Image.open(populated).convert("RGB")
    box = geometry_box
    if box is None:
        raise ValueError(f"{ref} has no measurable pixels in {label} view")
    width = box[2] - box[0]
    height = box[3] - box[1]
    margin = max(70, int(max(width, height) * 0.75))
    crop_box = (max(0, box[0] - margin), max(0, box[1] - margin),
                min(image.width, box[2] + margin), min(image.height, box[3] + margin))
    crop = image.crop(crop_box)
    header = 112
    canvas_width = max(1000, crop.width)
    crop_x = (canvas_width - crop.width) // 2
    canvas = Image.new("RGB", (canvas_width, crop.height + header), (12, 12, 12))
    canvas.paste(crop, (crop_x, header))
    draw = ImageDraw.Draw(canvas)
    draw.text((18, 12), f"{ref} — {label}", fill=(255, 255, 255), font=font(30))
    draw.text((18, 51), metadata, fill=(180, 220, 255), font=font(16))
    draw.text((18, 78), detail, fill=(210, 210, 210), font=font(15))
    local = (box[0] - crop_box[0] + crop_x, box[1] - crop_box[1] + header,
             box[2] - crop_box[0] + crop_x, box[3] - crop_box[1] + header)
    if draw_box:
        draw.rectangle(local, outline=(255, 0, 255), width=4)
    if axis is not None:
        cx = (local[0] + local[2]) / 2
        cy = (local[1] + local[3]) / 2
        length = max(65, min(130, max(width, height)))
        ex, ey = cx + axis[0] * length, cy + axis[1] * length
        draw.line((cx, cy, ex, ey), fill=(0, 255, 80), width=8)
        angle = math.atan2(ey-cy, ex-cx)
        for offset in (-0.55, 0.55):
            draw.line((ex, ey, ex-24*math.cos(angle+offset),
                       ey-24*math.sin(angle+offset)), fill=(0, 255, 80), width=8)
        draw.text((max(5, ex-95), max(header, ey-42)), "OUTSIDE / CABLE",
                  fill=(0, 255, 80), font=font(18))
    canvas.save(output)
    return box


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True,
                               allow_nan=False) + "\n", encoding="utf-8")


def validate_approval(path: Path, subject_sha: str, refs, evidence):
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return False, "approval is absent or unreadable"
    required = {"schema", "kind", "verdict", "subject_sha256", "refs",
                "reviewer", "confirmed_at", "evidence_sha256"}
    if not isinstance(value, dict) or set(value) != required:
        return False, "approval fields differ from schema 1"
    if (value["schema"] != 1 or value["kind"] != APPROVAL_KIND or
            value["verdict"] != "APPROVED"):
        return False, "approval vocabulary is invalid"
    if value["subject_sha256"] != subject_sha or value["refs"] != refs:
        return False, "approval subject or denominator is stale"
    if value["evidence_sha256"] != evidence:
        return False, "approved review images changed"
    if not str(value["reviewer"]).strip() or not str(value["confirmed_at"]).strip():
        return False, "approval reviewer/time is empty"
    return True, "approved"


def orientation_report(verdict, subject_sha, board_sha, measurements,
                       review_groups, failures, notes):
    report = [
        "# Connector orientation review", "",
        f"machine_verdict: {verdict}",
        f"subject_sha256: {subject_sha}",
        f"board_sha256: {board_sha}", "",
        "| ref | board access axis | edge | edge distance mm | mating-plane edge offset mm | model/footprint alignment | verdict |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for row in measurements:
        report.append(
            f"| {row['ref']} | {row['access_axis_board']} | {row['edge']} | "
            f"{row['edge_distance_mm']} | {row['mating_plane_edge_offset_mm']} | "
            f"{row['model_axis_alignment']:.6f} | "
            f"{'FAIL' if row['failures'] else 'PASS'} |")
    report += ["", "## Human-review representatives", "",
               "| representative | machine-graded refs | tuple |",
               "|---|---|---|"]
    for group in review_groups:
        report.append(
            f"| {group['representative']} | {', '.join(group['refs'])} | "
            f"`{group['signature_sha256'][:16]}` |")
    report += ["", "## Machine findings", ""]
    report += [f"- {finding}" for finding in failures] or ["- none"]
    report += ["", "## Machine notes", ""]
    report += [f"- {note}" for note in notes] or ["- none"]
    report += ["", "## Human confirmation", "",
               "Review every present image. Each ref requires `top`, `outside`, and "
               "`inside`; orthogonal profiles are included when the target is not "
               "occluded by another connector. Approve only when the visible mouth/"
               "access direction, mounting side, keying, and cable approach agree "
               "with the intended physical use."]
    return "\n".join(report) + "\n"


def promote_output(work: Path, outdir: Path) -> None:
    """Publish diagnostics while retaining the most recent accepted bundle."""
    if outdir.is_dir():
        try:
            prior = json.loads(
                (outdir / "orientation_receipt.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            prior = {}
        if prior.get("verdict") == "PASS":
            preserved = outdir.with_name(outdir.name + ".last_pass")
            if preserved.exists():
                shutil.rmtree(preserved)
            shutil.copytree(outdir, preserved)
        shutil.rmtree(outdir)
    work.replace(outdir)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project")
    parser.add_argument("--board", required=True)
    parser.add_argument("--config", default="03_src/rules/model_registration.yaml")
    parser.add_argument("--floorplan", default="03_src/floorplan.yaml")
    parser.add_argument("--outdir", default="06_build/pre_route/orientation")
    parser.add_argument("--approval", default="08_reviews/connector_orientation.yaml")
    parser.add_argument("--width", type=int, default=2400)
    parser.add_argument("--height", type=int, default=1600)
    parser.add_argument("--machine-only", action="store_true")
    parser.add_argument("--approve-reviewer",
                        help="write approval only after explicit human confirmation")
    args = parser.parse_args(argv)

    project = Path(args.project).resolve()
    board_path = (project / args.board).resolve()
    config_path = (project / args.config).resolve()
    floorplan_path = (project / args.floorplan).resolve()
    outdir = (project / args.outdir).resolve()
    approval_path = (project / args.approval).resolve()
    if (not board_path.is_file() or not config_path.is_file() or
            not floorplan_path.is_file()):
        raise SystemExit(
            "orientation gate requires the board, model_registration.yaml, and floorplan.yaml")
    if args.width < 800 or args.height < 600:
        raise SystemExit("orientation review renders must be at least 800x600")
    try:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        if not isinstance(config, dict) or config.get("schema") != 1:
            raise ValueError("model_registration.yaml schema must be 1")
        floorplan = yaml.safe_load(floorplan_path.read_text(encoding="utf-8"))
        if not isinstance(floorplan, dict):
            raise ValueError("floorplan.yaml must be a mapping")
        edge_faces = {}
        for index, row in enumerate(
                ((floorplan.get("asserts") or {}).get("edge_faces") or [])):
            if not isinstance(row, dict) or not str(row.get("ref", "")).strip():
                raise ValueError(f"floorplan edge_faces[{index}] must name ref")
            ref = str(row["ref"])
            edge = str(row.get("edge", ""))
            if edge not in EDGE_FACES:
                raise ValueError(
                    f"floorplan edge_faces[{index}] edge must be one of {sorted(EDGE_FACES)}")
            if ref in edge_faces:
                raise ValueError(f"floorplan edge_faces declares {ref} twice")
            edge_faces[ref] = {
                "edge": edge,
                "min_offset_mm": float(row.get("min_offset_mm", 0.0)),
            }
        board = pcbnew.LoadBoard(str(board_path))
        polygon = board_outline(board)
        declared = {}
        contracts = []
        for group in config.get("groups", []):
            orientation = normalized_orientation(group)
            if orientation is None:
                continue
            refs = group.get("refs")
            if not isinstance(refs, list) or not refs:
                raise ValueError(f"{group.get('id')}: orientation refs must be a list")
            model_sha = str(group.get("model_sha256", "")).lower()
            if len(model_sha) != 64:
                raise ValueError(f"{group.get('id')}: model_sha256 is invalid")
            contracts.append({"id": str(group.get("id")), "refs": refs,
                              "model_sha256": model_sha, "orientation": orientation})
            for ref in refs:
                if ref in declared:
                    raise ValueError(f"orientation ref {ref} is declared twice")
                declared[str(ref)] = (orientation, edge_faces.get(str(ref)), model_sha)
        exemptions = config.get("orientation_exemptions", [])
        if not isinstance(exemptions, list):
            raise ValueError("orientation_exemptions must be a list")
        exempt = set()
        for row in exemptions:
            if (not isinstance(row, dict) or not isinstance(row.get("refs"), list)
                    or not str(row.get("why", "")).strip()):
                raise ValueError("every orientation exemption needs refs and why")
            exempt.update(str(ref) for ref in row["refs"])
        connector_refs = sorted(fp.GetReference() for fp in board.GetFootprints()
                                if fp.GetReference().startswith("J"))
        missing = sorted(set(connector_refs) - set(declared) - exempt)
        unknown = sorted((set(declared) | exempt) - set(connector_refs))
        if missing or unknown:
            raise ValueError(f"orientation denominator mismatch: missing={missing}, unknown={unknown}")
        missing_edges = sorted(
            ref for ref, (_orientation, face, _sha) in declared.items()
            if face is None)
        undeclared_edges = sorted(set(edge_faces) - set(declared))
        if missing_edges or undeclared_edges:
            raise ValueError(
                "orientation/floorplan authority mismatch: "
                f"orientation_without_edge={missing_edges}, "
                f"edge_without_orientation={undeclared_edges}")
        refs = sorted(declared)
        if not refs:
            print("P-ORIENT N/A: no non-exempt orientation-sensitive connectors")
            return 0

        measurements = []
        failures = []
        notes = []
        for ref in refs:
            fp = board.FindFootprintByReference(ref)
            row = grade_ref(fp, board_path, *declared[ref], polygon)
            measurements.append(row)
            failures.extend(f"{ref}: {finding}" for finding in row["failures"])
        review_buckets = {}
        for ref in refs:
            fp = board.FindFootprintByReference(ref)
            orientation, edge_face, model_sha = declared[ref]
            model = list(fp.Models())[0]
            signature = canonical_sha({
                "orientation": orientation,
                "edge_face": edge_face,
                "model_sha256": model_sha,
                "footprint_rotation_deg": round(fp.GetOrientationDegrees(), 6),
                "mount_side": "front" if fp.GetLayer() == pcbnew.F_Cu else "back",
                "model_offset": [model.m_Offset.x, model.m_Offset.y, model.m_Offset.z],
                "model_rotation": [model.m_Rotation.x, model.m_Rotation.y,
                                   model.m_Rotation.z],
                "model_scale": [model.m_Scale.x, model.m_Scale.y, model.m_Scale.z],
            })
            review_buckets.setdefault(signature, []).append(ref)
        review_groups = [
            {"signature_sha256": signature, "representative": group_refs[0],
             "refs": group_refs}
            for signature, group_refs in sorted(review_buckets.items(),
                                                 key=lambda item: item[1][0])
        ]
        identity = tool_identity()
        subject_value = {
            "schema": 1,
            "tool_identity": identity,
            "placement": placement_projection(board, refs, polygon),
            "contract": contracts,
            "edge_faces": {ref: edge_faces[ref] for ref in refs},
        }
        subject_sha = canonical_sha(subject_value)
        observed_board_sha = digest(board_path)

        work = outdir.with_name(outdir.name + ".work")
        if work.exists():
            shutil.rmtree(work)
        if failures:
            work.mkdir(parents=True)
            receipt = {
                "schema": 1, "kind": KIND, "verdict": "FAIL",
                "subject_sha256": subject_sha,
                "observed_board_sha256": observed_board_sha,
                "config_sha256": digest(config_path),
                "floorplan_sha256": digest(floorplan_path),
                "tool_identity": identity, "refs": refs,
                "review_groups": review_groups, "measurements": measurements,
                "failures": failures, "notes": notes, "evidence": {},
            }
            write_json(work / "orientation_receipt.json", receipt)
            (work / "orientation_review.md").write_text(
                orientation_report("FAIL", subject_sha, observed_board_sha,
                                   measurements, review_groups, failures, notes),
                encoding="utf-8")
            promote_output(work, outdir)
            for finding in failures:
                print(f"P-ORIENT finding: {finding}")
            print(f"P-ORIENT FAIL: {len(measurements)}/{len(refs)} refs measured, "
                  f"{len(failures)} geometry finding(s); rendering skipped; see "
                  f"{outdir / 'orientation_review.md'}")
            return 1
        views = work / "views"
        renders = work / "renders"
        for directory in (views, renders):
            directory.mkdir(parents=True, exist_ok=True)
        populated = {}
        total_renders = len(CAMERAS)
        render_index = 0
        for camera in CAMERAS:
            path = renders / f"populated_{camera}.png"
            render_index += 1
            print(f"P-ORIENT render {render_index}/{total_renders}: populated {camera}",
                  flush=True)
            render(board_path, path, camera, args.width, args.height)
            populated[camera] = path

        view_paths = []
        measurements_by_ref = {row["ref"]: row for row in measurements}
        for review_group in review_groups:
            ref = review_group["representative"]
            measurement = measurements_by_ref[ref]
            axis = measurement["access_axis_board"]
            edge = measurement["edge_face"]["edge"]
            source_fp = board.FindFootprintByReference(ref)
            top_box = top_geometry_bbox(populated["top"], source_fp, polygon)
            cardinal = (int(round(axis[0])), int(round(axis[1])))
            outside = CARDINAL_CAMERA.get(cardinal)
            if outside is None:
                failures.append(f"{ref}: access axis is not cardinal enough to select cameras")
                continue
            inside = {"left":"right", "right":"left", "front":"back", "back":"front"}[outside]
            profiles = ("front", "back") if outside in ("left", "right") else ("left", "right")
            selections = [
                ("top", "top", "TOP — green arrow is authored access direction",
                 (axis[0], axis[1]), True),
                ("outside", outside, f"OUTSIDE / CABLE — camera={outside}",
                 None, False),
                ("inside", inside, f"INSIDE / REAR — camera={inside}",
                 None, False),
            ]
            if len(review_group["refs"]) == 1:
                selections += [
                    ("profile_a", profiles[0], f"PROFILE A — camera={profiles[0]}",
                     None, False),
                    ("profile_b", profiles[1], f"PROFILE B — camera={profiles[1]}",
                     None, False),
                ]
            else:
                notes.append(
                    f"{ref}: orthogonal profiles omitted for repeated tuple "
                    f"{review_group['refs']} because edge-row instances can occlude one another")
            for suffix, camera, label, arrow, draw_box in selections:
                output = views / f"{ref}_{suffix}.png"
                try:
                    geometry = top_box if camera == "top" else \
                        side_geometry_window(populated[camera], source_fp,
                                             polygon, camera)
                    detail = (
                        "Exact-board 3D; magenta box is exact footprint geometry "
                        "(P-MODEL-REG owns body bbox)" if camera == "top" else
                        "Exact-board 3D; crop is board-coordinate selected; no "
                        "pixel-derived body box")
                    focused_view(populated[camera], output, ref, label,
                                 f"EDGE={edge}  CAMERA={camera}  SUBJECT={subject_sha[:16]}",
                                 detail, geometry, arrow, draw_box)
                    view_paths.append(output)
                except ValueError as exc:
                    failures.append(str(exc))

        if failures:
            verdict = "FAIL"
        else:
            verdict = "PASS"
        receipt = {
            "schema": 1,
            "kind": KIND,
            "verdict": verdict,
            "subject_sha256": subject_sha,
            "observed_board_sha256": observed_board_sha,
            "config_sha256": digest(config_path),
            "floorplan_sha256": digest(floorplan_path),
            "tool_identity": identity,
            "refs": refs,
            "review_groups": review_groups,
            "measurements": measurements,
            "failures": failures,
            "notes": notes,
            "evidence": {},
        }
        for path in sorted(view_paths):
            relative = path.relative_to(work).as_posix()
            receipt["evidence"][relative] = digest(path)
        write_json(work / "orientation_receipt.json", receipt)
        (work / "orientation_review.md").write_text(
            orientation_report(verdict, subject_sha, observed_board_sha,
                               measurements, review_groups, failures, notes),
            encoding="utf-8")
        promote_output(work, outdir)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"P-ORIENT FAIL: {exc}")
        return 1

    if failures:
        print(f"P-ORIENT FAIL: {len(measurements)}/{len(refs)} refs measured, "
              f"{len(failures)} finding(s); see {outdir / 'orientation_review.md'}")
        return 1

    evidence = receipt["evidence"]
    if args.approve_reviewer:
        approval = {
            "schema": 1, "kind": APPROVAL_KIND, "verdict": "APPROVED",
            "subject_sha256": subject_sha, "refs": refs,
            "reviewer": args.approve_reviewer.strip(), "confirmed_at": utc_now(),
            "evidence_sha256": evidence,
        }
        approval_path.parent.mkdir(parents=True, exist_ok=True)
        approval_path.write_text(yaml.safe_dump(approval, sort_keys=False),
                                 encoding="utf-8")
    approved, reason = validate_approval(
        approval_path, subject_sha, refs, evidence)
    if args.machine_only:
        print(f"P-ORIENT MACHINE PASS: {len(refs)}/{len(refs)} refs; human={reason}")
        return 0
    if not approved:
        print(f"P-ORIENT REVIEW REQUIRED: machine {len(refs)}/{len(refs)} PASS; {reason}; "
              f"review {outdir / 'orientation_review.md'}")
        return 2
    print(f"P-ORIENT PASS: machine {len(refs)}/{len(refs)}, human {len(refs)}/{len(refs)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
