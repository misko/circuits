#!/usr/bin/env python3
"""Project P-MODEL-REG orchestrator with tuple-cached atomic evidence."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import time
from types import SimpleNamespace

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
PCB_PIPELINE = SCRIPT_DIR.parents[1] / "pcb-design" / "scripts"
sys.path.insert(0, str(PCB_PIPELINE))
sys.path.insert(0, str(SCRIPT_DIR))

from pipeline_artifacts import ArtifactBundleTransaction, ArtifactError  # noqa: E402
from pipeline_contract import StageResult  # noqa: E402
import native_model_registration as native  # noqa: E402


STAGE_ID = "P-MODEL-REG"
OUTPUT_SYMBOL = "model_registration_bundle"
INDEX_KIND = "model-registration-index-v1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z")


def write_json_atomic(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{time.time_ns():x}")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def parse_refs(group_id: str, value):
    if isinstance(value, list):
        refs = [str(ref).strip() for ref in value]
    elif isinstance(value, str):
        refs = native.parse_refs(value)
    else:
        raise ValueError(f"P-MODEL-REG {group_id}: refs must be non-empty")
    if (not refs or any(not ref for ref in refs) or
            len(refs) != len(set(refs)) or
            any(any(char not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-"
                    for char in ref) for ref in refs)):
        raise ValueError(f"P-MODEL-REG {group_id}: refs must be safe and unique")
    return sorted(refs, key=native.ref_sort_key)


def normalized_group(group_id: str, group):
    refs = parse_refs(group_id, group.get("refs"))
    model_sha = str(group.get("model_sha256", "")).lower()
    if len(model_sha) != 64 or any(ch not in "0123456789abcdef" for ch in model_sha):
        raise ValueError(f"P-MODEL-REG {group_id}: invalid model_sha256")
    orientation = group.get("orientation")
    mount_side = None
    if orientation is not None:
        if not isinstance(orientation, dict):
            raise ValueError(f"P-MODEL-REG {group_id}: orientation must be a mapping")
        mount_side = str(orientation.get("mount_side", "")).strip().lower()
        if mount_side not in ("front", "back"):
            raise ValueError(
                f"P-MODEL-REG {group_id}: orientation.mount_side must be front or back")
    values = {
        "refs": refs,
        "model_sha256": model_sha,
        "registration_datum": str(
            group.get("registration_datum", "drilled_centres")).strip(),
        "fit_tolerance_mm": float(group.get("fit_tolerance_mm", 1.0)),
        "courtyard_containment_tolerance_mm": float(
            group.get("courtyard_containment_tolerance_mm", 0.25)),
        "search_margin_mm": float(group.get("search_margin_mm", 8.0)),
        "render_width": int(group.get("render_width", 2400)),
        "render_height": int(group.get("render_height", 1600)),
        "authority": str(group.get("authority", "")),
        "mount_side": mount_side,
        "mount_side_min_fraction": float(
            group.get("mount_side_min_fraction", 0.75)),
    }
    if values["registration_datum"] not in native.REGISTRATION_DATUMS:
        raise ValueError(
            f"P-MODEL-REG {group_id}: registration_datum must be one of "
            f"{sorted(native.REGISTRATION_DATUMS)}")
    for name in ("fit_tolerance_mm", "courtyard_containment_tolerance_mm",
                 "search_margin_mm"):
        if not math.isfinite(values[name]) or values[name] < 0:
            raise ValueError(f"P-MODEL-REG {group_id}: {name} must be finite and non-negative")
    if values["render_width"] < 320 or values["render_height"] < 240:
        raise ValueError(f"P-MODEL-REG {group_id}: render dimensions are too small")
    if not 0.5 <= values["mount_side_min_fraction"] <= 1.0:
        raise ValueError(
            f"P-MODEL-REG {group_id}: mount_side_min_fraction must be within [0.5, 1.0]")
    contract = {"schema": 1, "group_id": group_id, **values}
    values["contract_sha256"] = canonical_sha(contract)
    return values


def tuple_for(board: Path, values):
    _board, rows = native.collect_source_rows(
        board, values["refs"], values["model_sha256"],
        values["registration_datum"])
    args = SimpleNamespace(
        fit_tol_mm=values["fit_tolerance_mm"],
        courtyard_tol_mm=values["courtyard_containment_tolerance_mm"],
        search_margin_mm=values["search_margin_mm"],
        width=values["render_width"], height=values["render_height"],
        contract_sha256=values["contract_sha256"],
        tool_identity=native.tool_identity(),
        registration_datum=values["registration_datum"],
        mount_side=values["mount_side"],
        mount_side_min_fraction=values["mount_side_min_fraction"],
    )
    return native.registration_tuple(rows, values["refs"], args), rows


def declared_outputs(refs, model_suffix, mount_side=None):
    names = {
        "model_registration_receipt.json": None,
        "native_bare.kicad_pcb": None,
        "native_bare_top.png": None,
        "native_coupon.kicad_pcb": None,
        "native_model_registration.md": None,
        "native_model" + model_suffix.lower(): None,
        "native_top.png": None,
        "native_top_registration_overlay.png": None,
    }
    names.update({f"native_overlay_{ref}.png": None for ref in refs})
    if mount_side:
        names.update({
            "native_side_front.png": None,
            "native_side_right.png": None,
        })
    return names


def validate_receipt(receipt, tuple_value, refs, output_names) -> None:
    expected_top = {"schema", "kind", "tuple", "refs", "measurements", "evidence"}
    if not isinstance(receipt, dict) or set(receipt) != expected_top:
        raise ValueError("model receipt fields differ from schema 1")
    if receipt["schema"] != 1 or receipt["kind"] != native.RECEIPT_KIND:
        raise ValueError("model receipt schema/kind is unsupported")
    expected_tuple = {
        "footprint_sha256", "model_sha256", "transform_sha256",
        "contract_sha256", "tool_identity",
    }
    if not isinstance(receipt["tuple"], dict) or set(receipt["tuple"]) != expected_tuple:
        raise ValueError("model receipt tuple fields differ")
    if receipt["tuple"] != tuple_value:
        raise ValueError("model receipt tuple does not match current subject")
    if receipt["refs"] != refs:
        raise ValueError("model receipt refs are stale or unordered")
    measurements = receipt["measurements"]
    expected_measurement = {
        "ref", "attachment_centres_graded", "attachment_centres_total",
        "centre_delta_mm", "fab_outward_mm", "courtyard_outward_mm",
    }
    if (not isinstance(measurements, list) or
            [item.get("ref") for item in measurements
             if isinstance(item, dict)] != refs):
        raise ValueError("model receipt measurement denominator differs")
    for item in measurements:
        if not isinstance(item, dict) or set(item) != expected_measurement:
            raise ValueError("model receipt measurement fields differ")
        graded = item["attachment_centres_graded"]
        total = item["attachment_centres_total"]
        if (not isinstance(graded, int) or isinstance(graded, bool) or
                not isinstance(total, int) or isinstance(total, bool) or
                total <= 0 or graded != total):
            raise ValueError("model receipt attachment denominator is incomplete")
        for name in ("centre_delta_mm", "fab_outward_mm", "courtyard_outward_mm"):
            value = item[name]
            if (not isinstance(value, (int, float)) or isinstance(value, bool) or
                    not math.isfinite(value) or value < 0):
                raise ValueError(f"model receipt {name} is not a finite measurement")
    evidence = receipt["evidence"]
    if (not isinstance(evidence, list) or not evidence or
            evidence != sorted(set(evidence))):
        raise ValueError("model receipt evidence must be sorted and unique")
    for name in evidence:
        path = PurePosixPath(name)
        if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
            raise ValueError("model receipt evidence path is unsafe")
        if name not in output_names:
            raise ValueError(f"model receipt evidence is undeclared: {name}")


def accepted_cache_valid(path: Path, tuple_value, refs, output_names) -> bool:
    try:
        manifest = json.loads((path / "bundle.json").read_text(encoding="utf-8"))
        if manifest.get("schema") != 1 or manifest.get("status") != "PASS":
            return False
        if set(manifest.get("outputs", {})) != set(output_names):
            return False
        actual = {
            artifact.relative_to(path).as_posix()
            for artifact in path.rglob("*") if artifact.is_file()
        }
        if actual != set(output_names) | {"bundle.json"}:
            return False
        for name, record in manifest["outputs"].items():
            artifact = path / name
            if (not artifact.is_file() or artifact.stat().st_size != record.get("size") or
                    digest(artifact) != record.get("sha256")):
                return False
        receipt = json.loads(
            (path / "model_registration_receipt.json").read_text(encoding="utf-8"))
        validate_receipt(receipt, tuple_value, refs, output_names)
        return manifest.get("subject", {}).get("semantic_sha256") == native.tuple_cache_key(
            tuple_value)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return False


def engine_command(engine: Path, board: Path, outdir: Path, values, tuple_value):
    command = [
        sys.executable, str(engine), str(board), str(outdir),
        "--refs", ",".join(values["refs"]),
        "--model-sha256", values["model_sha256"],
        "--registration-datum", values["registration_datum"],
        "--fit-tol-mm", str(values["fit_tolerance_mm"]),
        "--courtyard-tol-mm", str(values["courtyard_containment_tolerance_mm"]),
        "--search-margin-mm", str(values["search_margin_mm"]),
        "--width", str(values["render_width"]),
        "--height", str(values["render_height"]),
        "--contract-sha256", tuple_value["contract_sha256"],
        "--tool-identity", tuple_value["tool_identity"],
    ]
    if values["mount_side"]:
        command += [
            "--mount-side", values["mount_side"],
            "--mount-side-min-fraction", str(values["mount_side_min_fraction"]),
        ]
    return command


def run_group(project: Path, board: Path, config_path: Path, build: Path,
              engine: Path, group_id: str, values, tuple_value, rows, run_id: str):
    accepted = build / group_id
    outputs = declared_outputs(
        values["refs"], rows[0]["model"].suffix, values["mount_side"])
    if accepted_cache_valid(accepted, tuple_value, values["refs"], outputs):
        print(f"P-MODEL-REG CACHE-HIT: {group_id} {native.tuple_cache_key(tuple_value)}")
        return accepted, True, None

    attempt = build / "failed_attempts" / f"{group_id}-{run_id}"
    attempt.mkdir(parents=True, exist_ok=False)
    model = rows[0]["model"]
    raw_subject = canonical_sha({
        "board": digest(board), "config": digest(config_path),
        "engine": digest(engine), "twin_overlay": digest(engine.with_name("twin_overlay.py")),
        "model": digest(model),
    })
    transaction = ArtifactBundleTransaction(
        accepted,
        producer="native-model-registration",
        producer_version=tuple_value["tool_identity"],
        subject={
            "semantic_sha256": native.tuple_cache_key(tuple_value),
            "raw_sha256": raw_subject,
        },
        inputs={
            "source/board.kicad_pcb": board,
            "contract/model_registration.yaml": config_path,
            "model/native.step": model,
            "tool/native_model_registration.py": engine,
            "tool/twin_overlay.py": engine.with_name("twin_overlay.py"),
        },
        outputs=outputs,
        run_id=run_id,
    )

    command = engine_command(engine, board, attempt, values, tuple_value)

    def produce(staging):
        result = subprocess.run(command, text=True, capture_output=True)
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        if result.returncode:
            (attempt / "invocation.log").write_text(
                result.stdout + result.stderr, encoding="utf-8")
            return result.returncode
        for name in outputs:
            source = attempt / name
            if not source.is_file():
                return 97
            shutil.copy2(source, staging / name)
        return 0

    def reopen(_staging, opened):
        validate_receipt(
            opened["model_registration_receipt.json"], tuple_value,
            values["refs"], outputs,
        )

    try:
        transaction.publish(produce, reopen_validator=reopen)
    except ArtifactError as exc:
        return attempt, False, str(exc)
    shutil.rmtree(attempt)
    try:
        attempt.parent.rmdir()
    except OSError:
        pass
    return accepted, False, None


def group_index(project: Path, rows_out):
    groups = []
    for group_id, values, tuple_value, report, passed, _cached in sorted(
            rows_out, key=lambda row: row[0]):
        if not passed:
            raise ValueError(f"cannot index failed registration group {group_id}")
        manifest = report.parent / "bundle.json"
        if not manifest.is_file():
            raise ValueError(f"registration group {group_id} has no accepted manifest")
        groups.append({
            "id": group_id,
            "refs": values["refs"],
            "tuple": tuple_value,
            "tuple_cache_key": native.tuple_cache_key(tuple_value),
            "manifest": manifest.relative_to(project).as_posix(),
            "manifest_sha256": digest(manifest),
            "manifest_size": manifest.stat().st_size,
        })
    return groups


def validate_index(project: Path, index, expected) -> None:
    expected_fields = {
        "schema", "kind", "stage_id", "run_id", "subject", "groups",
    }
    if not isinstance(index, dict) or set(index) != expected_fields:
        raise ValueError("model registration index fields differ from schema 1")
    if index != expected:
        raise ValueError("model registration index disagrees with final aggregate state")
    ids = [group["id"] for group in index["groups"]]
    if ids != sorted(set(ids)):
        raise ValueError("model registration index group ids are not sorted and unique")
    expected_group_fields = {
        "id", "refs", "tuple", "tuple_cache_key", "manifest",
        "manifest_sha256", "manifest_size",
    }
    for group in index["groups"]:
        if set(group) != expected_group_fields:
            raise ValueError(f"model registration index group differs: {group.get('id')}")
        manifest = project.joinpath(*PurePosixPath(group["manifest"]).parts)
        if (not manifest.is_file() or manifest.stat().st_size != group["manifest_size"] or
                digest(manifest) != group["manifest_sha256"]):
            raise ValueError(f"indexed group manifest changed: {group['id']}")
        document = json.loads(manifest.read_text(encoding="utf-8"))
        if (document.get("schema") != 1 or document.get("status") != "PASS" or
                document.get("subject", {}).get("semantic_sha256") !=
                group["tuple_cache_key"]):
            raise ValueError(f"indexed group manifest subject differs: {group['id']}")
        receipt_path = manifest.parent / "model_registration_receipt.json"
        receipt_record = document.get("outputs", {}).get(
            "model_registration_receipt.json", {})
        if (not receipt_path.is_file() or digest(receipt_path) !=
                receipt_record.get("sha256") or receipt_path.stat().st_size !=
                receipt_record.get("size")):
            raise ValueError(f"indexed group receipt is not manifest-bound: {group['id']}")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if receipt.get("tuple") != group["tuple"] or receipt.get("refs") != group["refs"]:
            raise ValueError(f"indexed group tuple/refs differ: {group['id']}")


def publish_aggregate(project: Path, output: Path, board: Path,
                      config_path: Path, engine: Path, run_id: str,
                      subject, rows_out):
    accepted = output.parent / "model_registration_bundle"
    groups = group_index(project, rows_out)
    index = {
        "schema": 1,
        "kind": INDEX_KIND,
        "stage_id": STAGE_ID,
        "run_id": run_id,
        "subject": subject,
        "groups": groups,
    }
    inputs = {
        "source/board.kicad_pcb": board,
        "contract/model_registration.yaml": config_path,
        "legacy/model_registration.md": output,
        "tool/model_registration_gate.py": Path(__file__).resolve(),
        "tool/native_model_registration.py": engine,
        "tool/twin_overlay.py": engine.with_name("twin_overlay.py"),
    }
    for group in groups:
        manifest = project.joinpath(*PurePosixPath(group["manifest"]).parts)
        inputs[f"groups/{group['id']}/bundle.json"] = manifest
        inputs[f"groups/{group['id']}/model_registration_receipt.json"] = (
            manifest.parent / "model_registration_receipt.json")
    transaction = ArtifactBundleTransaction(
        accepted,
        producer="model-registration-aggregate",
        producer_version="model-registration-index-v1:" + digest(Path(__file__).resolve()),
        subject=subject,
        inputs=inputs,
        outputs={
            "model_registration.md": None,
            "model_registration_index.json": None,
        },
        run_id=run_id,
        retain_failed=True,
    )

    def produce(staging):
        shutil.copy2(output, staging / "model_registration.md")
        (staging / "model_registration_index.json").write_text(
            json.dumps(index, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )

    def reopen(_staging, opened):
        validate_index(project, opened["model_registration_index.json"], index)
        if opened["model_registration.md"] != output.read_text(encoding="utf-8"):
            raise ValueError("accepted aggregate report differs from legacy report")

    published = transaction.publish(produce, reopen_validator=reopen)
    return published.path


def emit_stage(path: Path, *, run_id: str, semantic: str, raw: str,
               applicability: str, reason, status: str, started: str,
               elapsed: float, graded: int, total: int, outputs, findings) -> None:
    result = StageResult(
        stage_id=STAGE_ID, run_id=run_id,
        subject={"semantic_sha256": semantic, "raw_sha256": raw},
        applicability=applicability, applicability_reason=reason, status=status,
        started_at=started, finished_at=utc_now(), elapsed_s=elapsed,
        graded=graded, total=total, outputs=outputs, findings=findings,
        resume=None,
    )
    write_json_atomic(path, result.to_mapping())


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project")
    parser.add_argument("--board", required=True)
    parser.add_argument("--out", default="06_build/pre_route/model_registration.md")
    parser.add_argument("--stage-out")
    args = parser.parse_args(argv)

    started_clock = time.monotonic()
    started = utc_now()
    project = Path(args.project).resolve()
    board = (project / args.board).resolve()
    output = (project / args.out).resolve()
    stage_output = ((project / args.stage_out).resolve() if args.stage_out else
                    output.with_suffix(".stage.json"))
    config_path = project / "03_src/rules/model_registration.yaml"
    run_id = (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" +
              f"{time.time_ns():x}"[-12:])
    if not config_path.is_file():
        identity = canonical_sha({"stage": STAGE_ID, "reason": "no contract"})
        raw = digest(board) if board.is_file() else identity
        emit_stage(
            stage_output, run_id=run_id, semantic=identity, raw=raw,
            applicability="NOT_APPLICABLE",
            reason="no 03_src/rules/model_registration.yaml",
            status="NOT_APPLICABLE", started=started,
            elapsed=time.monotonic() - started_clock, graded=0, total=0,
            outputs=[], findings=[],
        )
        print("P-MODEL-REG N-A: no 03_src/rules/model_registration.yaml")
        return 0
    config = yaml.safe_load(config_path.read_text(encoding="utf-8-sig")) or {}
    if config.get("schema") != 1:
        raise SystemExit("P-MODEL-REG schema must be 1")
    groups = config.get("groups")
    if not isinstance(groups, list) or not groups:
        raise SystemExit("P-MODEL-REG groups must be a non-empty list")
    if not board.is_file():
        raise SystemExit(f"P-MODEL-REG board does not exist: {board}")

    engine = SCRIPT_DIR / "native_model_registration.py"
    build = project / "06_build/pre_route/native_registration"
    build.mkdir(parents=True, exist_ok=True)
    seen_ids = set()
    seen_refs = {}
    prepared = []
    for index, group in enumerate(groups):
        if not isinstance(group, dict):
            raise SystemExit(f"P-MODEL-REG groups[{index}] must be a mapping")
        group_id = str(group.get("id", "")).strip()
        if (not group_id or group_id in seen_ids or
                any(char not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-"
                    for char in group_id)):
            raise SystemExit(f"P-MODEL-REG invalid/duplicate group id: {group_id!r}")
        seen_ids.add(group_id)
        try:
            values = normalized_group(group_id, group)
            for ref in values["refs"]:
                prior = seen_refs.get(ref)
                if prior is not None:
                    raise ValueError(
                        f"P-MODEL-REG ref {ref} appears in both {prior} and {group_id}")
                seen_refs[ref] = group_id
            tuple_value, rows = tuple_for(board, values)
        except ValueError as exc:
            raise SystemExit(str(exc))
        prepared.append((group_id, values, tuple_value, rows))

    semantic = canonical_sha(sorted([
        {"id": group_id, "refs": values["refs"], "tuple": tuple_value}
        for group_id, values, tuple_value, _rows in prepared
    ], key=lambda item: item["id"]))
    rows_out = []
    findings = []
    graded = 0
    for group_id, values, tuple_value, rows in prepared:
        path, cached, error = run_group(
            project, board, config_path, build, engine, group_id, values,
            tuple_value, rows, run_id,
        )
        report = path / "native_model_registration.md"
        passed = error is None and report.is_file()
        if passed:
            graded += 1
        else:
            findings.append({"group": group_id, "error": error or "missing report",
                             "diagnostics": path.relative_to(project).as_posix()})
        rows_out.append((group_id, values, tuple_value, report, passed, cached))

    failed = graded != len(prepared)
    output.parent.mkdir(parents=True, exist_ok=True)
    aggregate_manifest = output.parent / "model_registration_bundle/bundle.json"
    aggregate_relative = aggregate_manifest.relative_to(project).as_posix()
    bundle_label = "aggregate_bundle_unavailable" if failed else "accepted_bundle"
    lines = [
        "# Project native model physical registration",
        "",
        f"board_sha256: {digest(board)}",
        f"a-render_verdict: {'FAIL' if failed else 'PASS'}",
        "registration_kind: P-MODEL-REG",
        f"config_sha256: {digest(config_path)}",
        f"stage_receipt: {stage_output.relative_to(project).as_posix()}",
        f"{bundle_label}: {aggregate_relative}",
        "",
        "This aggregate is independent physical-registration evidence. Each "
        "group uses an origin-centred coupon and compares native-model pixels "
        "with F.Fab, F.CrtYd, and each group's declared drilled-centre or "
        "all-pad-centre datum. Catalog-twin "
        "renderer fidelity is a separate gate.",
        "",
        "| group | refs | tuple cache key | group report | result |",
        "|---|---|---|---|---|",
    ]
    for group_id, values, tuple_value, report, passed, cached in rows_out:
        relative = report.relative_to(project).as_posix()
        result = "CACHE-HIT" if cached and passed else ("PASS" if passed else "FAIL")
        lines.append(
            f"| {group_id} | {','.join(values['refs'])} | "
            f"`{native.tuple_cache_key(tuple_value)}` | `{relative}` | {result} |")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")

    raw_inputs = {
        "board": digest(board), "config": digest(config_path),
        "gate": digest(Path(__file__).resolve()), "engine": digest(engine),
        "twin_overlay": digest(engine.with_name("twin_overlay.py")),
        "legacy_report": digest(output),
    }
    for group_id, _values, _tuple_value, report, passed, _cached in rows_out:
        manifest = report.parent / "bundle.json"
        if passed and manifest.is_file():
            raw_inputs[f"group:{group_id}"] = digest(manifest)
    raw = canonical_sha(raw_inputs)
    subject = {"semantic_sha256": semantic, "raw_sha256": raw}

    aggregate_bundle = None
    if not failed:
        try:
            aggregate_bundle = publish_aggregate(
                project, output, board, config_path, engine, run_id, subject,
                rows_out,
            )
        except (ArtifactError, OSError, TypeError, ValueError,
                json.JSONDecodeError) as exc:
            failed = True
            findings.append({"aggregate": OUTPUT_SYMBOL, "error": str(exc)})
            output.write_text(
                output.read_text(encoding="utf-8").replace(
                    "a-render_verdict: PASS", "a-render_verdict: FAIL", 1),
                encoding="utf-8",
            )
            output.write_text(
                output.read_text(encoding="utf-8").replace(
                    "accepted_bundle:", "aggregate_bundle_failed:", 1),
                encoding="utf-8",
            )
            raw_inputs["legacy_report"] = digest(output)
            raw = canonical_sha(raw_inputs)

    emit_stage(
        stage_output, run_id=run_id, semantic=semantic, raw=raw,
        applicability="APPLIES", reason=None,
        status="FAIL" if failed else "PASS", started=started,
        elapsed=time.monotonic() - started_clock, graded=graded,
        total=len(prepared), outputs=[] if failed else [OUTPUT_SYMBOL],
        findings=findings,
    )
    if aggregate_bundle is not None:
        print(f"P-MODEL-REG accepted aggregate -> {aggregate_bundle}")
    print(
        f"P-MODEL-REG {'FAIL' if failed else 'PASS'}: {graded}/{len(prepared)} "
        f"group(s) graded -> {output}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
