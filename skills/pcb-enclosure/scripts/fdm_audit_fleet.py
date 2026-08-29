#!/usr/bin/env python3
"""Inventory enclosure-release printables under the current FDM policy.

Only manifest-declared ``meshes/*.stl`` payloads are printables. Verification,
installed-case, collision, STEP-component, and source-reference STLs are never
silently admitted to this denominator. Existing releases are read-only and
remain LEGACY/INCOMPLETE unless their release-local v2 config binds a
reproducible manufacturing audit.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    import fdm_structural_audit as fdm
except ImportError:  # pragma: no cover
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import fdm_structural_audit as fdm


class FleetError(ValueError):
    pass


def _binding(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != {"path", "sha256", "size"}:
        raise FleetError(f"{where}: expected exact path/sha256/size binding")
    path = value["path"]
    digest = value["sha256"]
    size = value["size"]
    if not isinstance(path, str) or not path or path.startswith("/") or \
            "\\" in path or any(part in {"", ".", ".."}
                                 for part in Path(path).parts):
        raise FleetError(f"{where}.path: unsafe relative path")
    if not isinstance(digest, str) or not fdm.HEX64_RE.fullmatch(digest) or \
            isinstance(size, bool) or not isinstance(size, int) or size <= 0:
        raise FleetError(f"{where}: invalid hash/size")
    return {"path": path, "sha256": digest, "size": size}


def _match(root: Path, record: Mapping[str, Any], where: str) -> Path:
    path = (root / record["path"]).resolve(strict=False)
    root_resolved = root.resolve()
    if path == root_resolved or not path.is_relative_to(root_resolved):
        raise FleetError(f"{where}: path escapes release")
    payload = fdm.stable_bytes(path, where)
    if fdm._sha(payload) != record["sha256"] or len(payload) != record["size"]:
        raise FleetError(f"{where}: manifest binding is stale")
    return path


def _release_row(release: Path) -> dict[str, Any]:
    manifest_path = release / "MANIFEST.json"
    manifest = fdm.load_json(manifest_path)
    kind = manifest.get("kind")
    if kind not in {"pcb-enclosure-release-v1", "pcb-enclosure-release-v2"}:
        raise FleetError(f"{release}: unknown release kind {kind!r}")
    payloads = manifest.get("payloads")
    if not isinstance(payloads, list) or not payloads:
        raise FleetError(f"{release}: payload denominator is zero")
    payload_by_path: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(payloads):
        record = _binding(raw, f"{release}.payloads[{index}]")
        if record["path"] in payload_by_path:
            raise FleetError(f"{release}: duplicate payload path")
        payload_by_path[record["path"]] = record
    printables = sorted(
        path for path in payload_by_path
        if path.startswith("meshes/") and path.endswith(".stl") and
        len(Path(path).parts) == 2)
    if not printables:
        raise FleetError(f"{release}: printable denominator is zero")
    for path in printables:
        _match(release, payload_by_path[path], f"{release}/{path}")
    all_stls = sorted(path for path in payload_by_path if path.endswith(".stl"))
    excluded_stls = sorted(set(all_stls) - set(printables))

    policy = "LEGACY"
    status = "INCOMPLETE"
    manufacturing_receipt = None
    if kind == "pcb-enclosure-release-v2":
        replay = manifest.get("replay")
        if not isinstance(replay, Mapping):
            raise FleetError(f"{release}: v2 release lacks replay mapping")
        config_record = _binding(replay.get("config"), f"{release}.replay.config")
        if payload_by_path.get(config_record["path"]) != config_record:
            raise FleetError(f"{release}: replay config differs from payload census")
        config_path = _match(release, config_record, f"{release} replay config")
        config = fdm.load_yaml(config_path)
        subject = config.get("subject")
        if not isinstance(subject, Mapping):
            raise FleetError(f"{release}: v2 config lacks subject")
        cad_record = _binding(subject.get("cad_design"),
                              f"{release}.subject.cad_design")
        if payload_by_path.get(cad_record["path"]) != cad_record:
            raise FleetError(f"{release}: CAD design differs from payload census")
        cad_path = _match(release, cad_record, f"{release} CAD design")
        cad = fdm.load_yaml(cad_path)
        declared = cad.get("cad", {}).get("printable_parts")
        if not isinstance(declared, list) or not declared or \
                len(declared) != len(set(declared)):
            raise FleetError(f"{release}: invalid CAD printable census")
        expected = sorted(f"meshes/{part}.stl" for part in declared)
        if expected != printables:
            raise FleetError(
                f"{release}: release mesh census differs from CAD printables; "
                f"expected={expected}, actual={printables}")
        manufacturing = config.get("manufacturing_audit")
        if manufacturing is not None:
            if not isinstance(manufacturing, Mapping):
                raise FleetError(f"{release}: manufacturing_audit is not a mapping")
            receipt_record = _binding(
                manufacturing.get("receipt"),
                f"{release}.manufacturing_audit.receipt")
            if payload_by_path.get(receipt_record["path"]) != receipt_record:
                raise FleetError(
                    f"{release}: manufacturing receipt differs from payload census")
            receipt_path = _match(
                release, receipt_record, f"{release} manufacturing receipt")
            receipt = fdm.load_json(receipt_path)
            if receipt.get("schema") != 1 or receipt.get("kind") != \
                    fdm.RECEIPT_KIND or receipt.get("status") not in {
                        "FAIL", "INCOMPLETE", "CAD_READY"}:
                raise FleetError(f"{release}: invalid manufacturing receipt")
            # Presence is not certification. Reopen the complete immutable
            # release, including manifest-bound compiler/helper roles, and
            # independently reproduce the manufacturing receipt before giving
            # it the CURRENT_POLICY label.
            try:
                import verify_enclosure_release as release_verify
                verified = release_verify.verify_release(release)
            except Exception as exc:
                raise FleetError(
                    f"{release}: current-policy release does not independently "
                    f"reopen: {exc}") from exc
            replay_result = verified.get("replay", {}).get(
                "manufacturing_audit")
            if not isinstance(replay_result, Mapping):
                raise FleetError(
                    f"{release}: verifier did not consume manufacturing audit")
            policy = "CURRENT_POLICY"
            status = receipt["status"]
            manufacturing_receipt = receipt_record["path"]
    return {
        "release": release.as_posix(), "release_kind": kind,
        "policy": policy, "status": status,
        "printable_count": len(printables), "printables": printables,
        "excluded_stl_count": len(excluded_stls), "excluded_stls": excluded_stls,
        "manufacturing_receipt": manufacturing_receipt,
    }


def audit_fleet(root: Path) -> dict[str, Any]:
    root = root.resolve()
    projects = root / "projects"
    if not projects.is_dir() or projects.is_symlink():
        raise FleetError("fleet root lacks ordinary projects/")
    releases: list[dict[str, Any]] = []
    for stream in sorted(projects.glob("*/07_enclosure_releases")):
        if not stream.is_dir() or stream.is_symlink():
            continue
        for release in sorted(stream.iterdir()):
            if release.is_dir() and not release.is_symlink() and \
                    (release / "MANIFEST.json").is_file():
                releases.append(_release_row(release))
    if not releases:
        raise FleetError("enclosure release denominator is zero")
    printables = sum(row["printable_count"] for row in releases)
    if printables <= 0:
        raise FleetError("fleet printable denominator is zero")
    return {
        "schema": 1, "kind": "pcb-enclosure-fdm-fleet-audit-v1",
        "root": root.as_posix(), "release_count": len(releases),
        "printable_count": printables,
        "current_policy_release_count": sum(
            row["policy"] == "CURRENT_POLICY" for row in releases),
        "legacy_incomplete_release_count": sum(
            row["policy"] == "LEGACY" and row["status"] == "INCOMPLETE"
            for row in releases),
        "excluded_nonprintable_stl_count": sum(
            row["excluded_stl_count"] for row in releases),
        "releases": releases,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        report = audit_fleet(args.root)
        if args.output:
            fdm.write_json(
                args.output, report,
                inputs=[Path(__file__), Path(fdm.__file__)],
                regrade=lambda: audit_fleet(args.root))
    except (FleetError, fdm.AuditError, OSError) as exc:
        print(f"FDM FLEET AUDIT ERROR: {exc}", file=sys.stderr)
        return 1
    print(
        "FDM FLEET AUDIT PASS: "
        f"releases={report['release_count']} "
        f"printables={report['printable_count']} "
        f"current_policy={report['current_policy_release_count']} "
        f"legacy_incomplete={report['legacy_incomplete_release_count']} "
        f"excluded_nonprintable_stls={report['excluded_nonprintable_stl_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
