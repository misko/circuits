#!/usr/bin/env python3
"""RF-SOLVER: run only declared pending local RF jobs, bounded and cached.

Usage: rf_solver.py PROJECT [--contract PATH] [--out DIR]

Every job is a direct argv list (never a shell string), declares its input and
output files, substitutes ``{project}`` and ``{output_dir}``, requires the
local/network-disabled work policy, streams output, emits heartbeats, and
terminates the whole process group at its hard deadline. The policy is
declarative because this host cannot create a network namespace; it must not
be described as an OS sandbox. Locked cross-sections return N-A.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path, PurePosixPath

import yaml

HERE = Path(__file__).resolve().parent
PCB_DESIGN_SCRIPTS = HERE.parents[1] / "pcb-design" / "scripts"
sys.path.insert(0, str(PCB_DESIGN_SCRIPTS))
sys.path.insert(0, str(HERE))
from pipeline_artifacts import ArtifactBundleTransaction
from process_runner import run_bounded
from rf_bundle import fresh_bundle

VERSION = "1"


class SolverError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}
    except (OSError, TypeError, ValueError, yaml.YAMLError) as exc:
        raise SolverError(f"cannot read RF contract {path}: {exc}") from exc
    if (not isinstance(value, dict) or value.get("schema") != 1
            or not isinstance(value.get("rf"), dict)):
        raise SolverError("rf.yaml must carry schema: 1 and an rf mapping")
    return value


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _inside(project: Path, value: str, label: str) -> Path:
    path = (project / value).resolve()
    try:
        path.relative_to(project)
    except ValueError as exc:
        raise SolverError(f"{label} must stay inside the project") from exc
    return path


def _output_name(value: str) -> str:
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise SolverError(f"solver output must be a safe relative path: {value!r}")
    if path.as_posix() in {"stdout.txt", "process.json", "bundle.json"}:
        raise SolverError(f"solver output name is reserved: {value!r}")
    return path.as_posix()


def _job_bundle(project: Path, contract_path: Path, job: dict,
                out_root: Path) -> Path:
    ident = str(job.get("id", "")).strip()
    if not ident or not all(char.isalnum() or char in "._-" for char in ident):
        raise SolverError(f"invalid solver job id {ident!r}")
    if job.get("work_class") != "local_compute" or job.get("network") is not False:
        raise SolverError(f"{ident}: only network:false local_compute is allowed")
    command = job.get("command")
    if (not isinstance(command, list) or not command
            or any(not isinstance(value, str) or not value for value in command)):
        raise SolverError(f"{ident}: command must be a non-empty argv list")
    try:
        timeout = float(job["timeout_s"])
        heartbeat = float(job["heartbeat_s"])
    except (KeyError, TypeError, ValueError) as exc:
        raise SolverError(f"{ident}: timeout_s/heartbeat_s must be numeric") from exc
    if not 1 <= timeout <= 300 or not 1 <= heartbeat <= min(30, timeout):
        raise SolverError(f"{ident}: timeout/heartbeat are outside bounded limits")
    raw_inputs = job.get("inputs")
    if not isinstance(raw_inputs, list) or not raw_inputs:
        raise SolverError(f"{ident}: inputs must be a non-empty list")
    inputs = {"rf.yaml": contract_path}
    for index, value in enumerate(raw_inputs):
        if not isinstance(value, str) or not value:
            raise SolverError(f"{ident}: inputs[{index}] must be a path")
        path = _inside(project, value, f"{ident}.inputs[{index}]")
        if not path.is_file():
            raise SolverError(f"{ident}: missing input {path}")
        inputs[f"job-inputs/{index}-{path.name}"] = path
    raw_outputs = job.get("outputs")
    if not isinstance(raw_outputs, list) or not raw_outputs:
        raise SolverError(f"{ident}: outputs must be a non-empty list")
    output_names = [_output_name(value) for value in raw_outputs]
    if len(set(output_names)) != len(output_names):
        raise SolverError(f"{ident}: outputs contain duplicates")
    bundle = out_root / ident
    subject_value = {"job": job, "input_hashes": {
        name: _hash(path.read_bytes()) for name, path in sorted(inputs.items())}}
    semantic = (json.dumps(subject_value, sort_keys=True,
                           separators=(",", ":")) + "\n").encode()
    raw = b"\0".join(path.read_bytes() for path in inputs.values())
    subject = {"semantic_sha256": _hash(semantic), "raw_sha256": _hash(raw)}
    outputs = {name: None for name in output_names}
    outputs.update({"stdout.txt": None, "process.json": None})
    bundle.parent.mkdir(parents=True, exist_ok=True)
    producer = f"rf_solver.py {ident}"
    if fresh_bundle(bundle, subject, inputs, set(outputs), producer=producer,
                    producer_version=VERSION):
        print(f"RF-SOLVER {ident}: cached exact bundle {bundle}")
        return bundle
    txn = ArtifactBundleTransaction(
        bundle, producer=producer, producer_version=VERSION,
        subject=subject, inputs=inputs, outputs=outputs)

    def produce(staging: Path):
        argv = [value.replace("{project}", str(project))
                .replace("{output_dir}", str(staging)) for value in command]
        env = dict(os.environ)
        env["RF_SOLVER_OUTPUT_DIR"] = str(staging)
        env["RF_SOLVER_NETWORK_POLICY"] = "disabled"
        result = run_bounded(
            argv, cwd=project, env=env, timeout_s=timeout,
            heartbeat_s=heartbeat, label=f"rf-solver-{ident}",
            state_path=staging / "process.json")
        retained = result.output or (f"command completed with returncode "
                                     f"{result.returncode}\n")
        (staging / "stdout.txt").write_text(retained)
        return result.returncode

    return txn.publish(produce).path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("project", type=Path)
    ap.add_argument("--contract", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args(argv)
    project = args.project.resolve()
    contract_path = (args.contract.resolve() if args.contract else
                     project / "03_src/rules/rf.yaml")
    out_root = (args.out.resolve() if args.out else project / "06_build/rf/solver")
    try:
        contract = _load(contract_path)
        rf = contract["rf"]
        if not isinstance(rf.get("enabled"), bool):
            raise SolverError("rf.enabled must be true or false")
        if not rf["enabled"]:
            print(f"RF-SOLVER input: {contract_path}")
            print("RF-SOLVER coverage: 1/1 applicability; RF disabled, N-A")
            print("RF-SOLVER PASS")
            return 0
        pending = {str(row.get("id")) for row in rf.get("cross_sections") or []
                   if isinstance(row, dict)
                   and row.get("status", "locked") == "pending_solver"}
        if not pending:
            print(f"RF-SOLVER input: {contract_path}")
            print("RF-SOLVER coverage: 0/0 pending cross-sections; N-A")
            print("RF-SOLVER PASS")
            return 0
        analysis = rf.get("analysis") or {}
        jobs = analysis.get("solver_jobs") or [] if isinstance(analysis, dict) else []
        if not isinstance(jobs, list) or not jobs:
            raise SolverError("pending cross-sections require solver_jobs")
        covered = [str(section) for job in jobs if isinstance(job, dict)
                   for section in job.get("cross_section_ids") or []]
        if set(covered) != pending or len(covered) != len(set(covered)):
            raise SolverError(f"solver jobs must cover pending set exactly; "
                              f"covered={sorted(covered)}, pending={sorted(pending)}")
        bundles = [_job_bundle(project, contract_path, job, out_root) for job in jobs]
    except Exception as exc:
        print(f"RF-SOLVER input: {contract_path}")
        print("RF-SOLVER coverage: 0/1 pending-job set")
        print(f"RF-SOLVER FAIL: {exc}")
        return 1
    print(f"RF-SOLVER coverage: {len(covered)}/{len(pending)} pending "
          "cross-sections; all jobs complete")
    print("RF-SOLVER bundles: " + ", ".join(str(path) for path in bundles))
    print("RF-SOLVER PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
