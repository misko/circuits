#!/usr/bin/env python3
"""Build a complete, release-bound mechanical STEP without editing the PCB release."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from contextlib import ExitStack
from pathlib import Path
from typing import Any

import pcbnew

SCRIPT_DIR = Path(__file__).resolve().parent
if (SCRIPT_DIR / "enclosure_common.py").is_file():
    ENCLOSURE_TOOLS = SCRIPT_DIR
else:
    ENCLOSURE_TOOLS = (
        SCRIPT_DIR.parents[3] / "skills" / "pcb-enclosure" / "scripts")
if str(ENCLOSURE_TOOLS) not in sys.path:
    sys.path.insert(0, str(ENCLOSURE_TOOLS))

from enclosure_common import (  # noqa: E402
    EnclosureError,
    load_json,
    run_bounded,
    stable_file_digest,
    stable_input_snapshot,
    validate_output_path,
    write_json,
)

KIND = "usb-hub-v1.12-obstruction-augmentation-v1"
TOP_KEYS = {"schema", "kind", "parent", "files", "models", "provenance"}
MODEL_KEYS = {
    "catalog", "value", "refs", "model", "footprint", "offset", "rotation",
    "scale",
}


def require_keys(value: dict[str, Any], expected: set[str], where: str) -> None:
    if set(value) != expected:
        raise EnclosureError(
            f"{where}: expected keys {sorted(expected)}, got {sorted(value)}")


def finite_vector(value: Any, where: str) -> list[float]:
    if not isinstance(value, list) or len(value) != 3 or any(
            isinstance(item, bool) or not isinstance(item, (int, float)) or
            not math.isfinite(item) for item in value):
        raise EnclosureError(f"{where}: expected three finite numbers")
    return [float(item) for item in value]


def resolve_binding(root: Path, raw: Any, where: str) -> tuple[Path, dict[str, Any]]:
    if not isinstance(raw, dict) or set(raw) != {"path", "sha256", "size"}:
        raise EnclosureError(f"{where}: invalid file binding")
    rel = raw["path"]
    if not isinstance(rel, str) or Path(rel).is_absolute() or ".." in Path(rel).parts:
        raise EnclosureError(f"{where}: unsafe relative path")
    path = root / rel
    absolute, info, digest = stable_file_digest(path, where)
    if digest != raw["sha256"] or info.st_size != raw["size"]:
        raise EnclosureError(f"{where}: hash/size mismatch")
    return absolute, {"path": rel, "sha256": digest, "size": info.st_size}


def vec(values: list[float]) -> pcbnew.VECTOR3D:
    return pcbnew.VECTOR3D(values[0], values[1], values[2])


def build(project_root: Path, manifest_path: Path, output_dir: Path) -> dict[str, Any]:
    project_root = project_root.resolve()
    manifest = load_json(manifest_path)
    require_keys(manifest, TOP_KEYS, "augmentation manifest")
    if manifest["schema"] != 1 or manifest["kind"] != KIND:
        raise EnclosureError("augmentation manifest: unsupported schema/kind")
    parent = manifest["parent"]
    if not isinstance(parent, dict) or set(parent) != {"release", "pcb", "step"}:
        raise EnclosureError("augmentation manifest: invalid parent")
    if parent["release"] != "v1.12-2026-07-28":
        raise EnclosureError("augmentation manifest: unexpected parent release")
    pcb_path, pcb_binding = resolve_binding(project_root, parent["pcb"], "parent PCB")
    step_path, step_binding = resolve_binding(project_root, parent["step"], "parent STEP")

    files = manifest["files"]
    if not isinstance(files, list) or not files:
        raise EnclosureError("augmentation manifest: files must be non-empty")
    file_bindings: dict[str, dict[str, Any]] = {}
    file_paths: dict[str, Path] = {}
    for index, raw in enumerate(files):
        path, binding = resolve_binding(project_root, raw, f"authority file[{index}]")
        if binding["path"] in file_bindings:
            raise EnclosureError("augmentation manifest: duplicate authority file")
        file_bindings[binding["path"]] = binding
        file_paths[binding["path"]] = path

    models = manifest["models"]
    if not isinstance(models, list) or len(models) != 8:
        raise EnclosureError("augmentation manifest: expected eight catalog models")
    registrations: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(models):
        if not isinstance(raw, dict):
            raise EnclosureError(f"model[{index}]: expected mapping")
        require_keys(raw, MODEL_KEYS, f"model[{index}]")
        if raw["catalog"] != raw["value"] or not isinstance(raw["catalog"], str):
            raise EnclosureError(f"model[{index}]: catalog/value mismatch")
        refs = raw["refs"]
        if not isinstance(refs, list) or not refs or any(
                not isinstance(ref, str) or not ref for ref in refs):
            raise EnclosureError(f"model[{index}]: invalid refs")
        if raw["model"] not in file_paths or raw["footprint"] not in file_paths:
            raise EnclosureError(f"model[{index}]: authority file is not bound")
        registration = {
            "catalog": raw["catalog"],
            "model": raw["model"],
            "footprint": raw["footprint"],
            "offset": finite_vector(raw["offset"], f"model[{index}].offset"),
            "rotation": finite_vector(raw["rotation"], f"model[{index}].rotation"),
            "scale": finite_vector(raw["scale"], f"model[{index}].scale"),
        }
        for ref in refs:
            if ref in registrations:
                raise EnclosureError(f"augmentation manifest: duplicate ref {ref}")
            registrations[ref] = registration
    expected_refs = {
        "F2", "J1", "J2", "J3", "J4", "J5", "Q1", "Q2", "Q3", "Q4",
        "Q5", "Q6", "U3", "U4", "U5", "SW1",
    }
    if set(registrations) != expected_refs:
        raise EnclosureError("augmentation manifest: reference census mismatch")

    output_dir.mkdir(parents=True, exist_ok=True)
    board_output = validate_output_path(
        output_dir / "supplemental-obstructions.kicad_pcb", where="mechanical board output",
        root=output_dir, inputs=[pcb_path, step_path, manifest_path, *file_paths.values()])
    step_output = validate_output_path(
        output_dir / "supplemental-obstructions.step", where="mechanical STEP output",
        root=output_dir, inputs=[pcb_path, step_path, manifest_path, *file_paths.values()])
    receipt_output = validate_output_path(
        output_dir / "obstruction-augmentation.json", where="augmentation receipt",
        root=output_dir, inputs=[pcb_path, step_path, manifest_path, *file_paths.values()])

    with ExitStack() as stack:
        pcb_snapshot, snap_pcb = stack.enter_context(
            stable_input_snapshot(pcb_path, "parent PCB"))
        model_snapshots: dict[str, Path] = {}
        for rel, path in sorted(file_paths.items()):
            snapshot, _ = stack.enter_context(
                stable_input_snapshot(path, f"authority file {rel}"))
            model_snapshots[rel] = snapshot
        board = pcbnew.LoadBoard(str(pcb_snapshot))
        for ref, registration in sorted(registrations.items()):
            footprint = board.FindFootprintByReference(ref)
            if footprint is None:
                raise EnclosureError(f"parent PCB: missing reference {ref}")
            if footprint.GetValue() != registration["catalog"]:
                raise EnclosureError(
                    f"parent PCB: {ref} value {footprint.GetValue()!r} does not match "
                    f"{registration['catalog']!r}")
            model = pcbnew.FP_3DMODEL()
            model.m_Filename = str(model_snapshots[registration["model"]])
            model.m_Offset = vec(registration["offset"])
            model.m_Rotation = vec(registration["rotation"])
            model.m_Scale = vec(registration["scale"])
            footprint.Models().clear()
            footprint.Models().push_back(model)
        pcbnew.SaveBoard(str(board_output), board)
        component_filter = ",".join(sorted(registrations))
        execution_command = [
            "/usr/bin/kicad-cli", "pcb", "export", "step", "--force",
            "--subst-models", "--no-board-body", "--component-filter",
            component_filter, "--output", str(step_output), str(board_output),
        ]
        completed = run_bounded(execution_command, timeout_s=600, check=True)
        command = [
            *execution_command[:-2], step_output.name, board_output.name,
        ]
        if not step_output.is_file() or step_output.stat().st_size == 0:
            raise EnclosureError("mechanical STEP export did not produce output")
        if snap_pcb["sha256"] != pcb_binding["sha256"]:
            raise EnclosureError("parent PCB snapshot mismatch")

    manifest_abs, manifest_info, manifest_digest = stable_file_digest(
        manifest_path, "augmentation manifest")
    board_abs, board_info, board_digest = stable_file_digest(
        board_output, "mechanical board output")
    step_abs, step_info, step_digest = stable_file_digest(
        step_output, "mechanical STEP output")
    receipt = {
        "schema": 1,
        "kind": "usb-hub-v1.12-obstruction-augmentation-receipt-v1",
        "status": "COMPLETE",
        "scope": "supplemental_obstruction_solids",
        "parent": {"release": parent["release"], "pcb": pcb_binding, "step": step_binding},
        "authority_manifest": {
            "path": manifest_abs.name, "sha256": manifest_digest,
            "size": manifest_info.st_size,
        },
        "authority_files": [file_bindings[key] for key in sorted(file_bindings)],
        "installed_refs": sorted(registrations),
        "outputs": {
            "board": {"path": board_abs.name, "sha256": board_digest, "size": board_info.st_size},
            "step": {"path": step_abs.name, "sha256": step_digest, "size": step_info.st_size},
        },
        "export": {
            "command": command,
            "returncode": completed.returncode,
            "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
            "stderr_sha256": hashlib.sha256(completed.stderr.encode()).hexdigest(),
        },
        "limitations": manifest["provenance"]["limitations"],
    }
    write_json(receipt_output, receipt, inputs=[manifest_path, pcb_path, step_path], root=output_dir)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = build(args.project_root, args.manifest, args.output_dir)
    except (EnclosureError, OSError, RuntimeError) as exc:
        print(f"OBSTRUCTION STEP FAIL: {exc}", file=sys.stderr)
        return 1
    print(
        f"OBSTRUCTION STEP COMPLETE: {len(receipt['installed_refs'])} supplemented refs; "
        f"{receipt['outputs']['step']['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
