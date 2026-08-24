#!/usr/bin/env python3
"""Compose one hash-bound acceptance receipt for routed PCB copper.

``quick`` mode grades mutation safety: route-base inheritance when supplied,
critical connectivity/topology, route ownership, and every realized via.
``full`` mode additionally grades declared length groups, reference planes,
series-via ampacity, and native KiCad DRC/parity.  The compositor owns no
engineering predicate; it calls the existing domain checkers and records their
structured results under one promotion decision.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any

import yaml

import copper_length_audit
import critical_route_check
import realized_via_aspect_check
import reference_plane_check
import route_acceptance_core
import route_ownership_preflight
import via_ampacity_check
from tier_preflight import board_scoped
from process_runner import run_bounded

PCB_PIPELINE = Path(__file__).resolve().parents[2] / "pcb-design" / "scripts"
if str(PCB_PIPELINE) not in sys.path:
    sys.path.insert(0, str(PCB_PIPELINE))
from pipeline_stage_evidence import require_safe_output_layout  # noqa: E402


def _record(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {"path": str(path.resolve()),
            "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8")
    os.replace(temporary, path)


def _status(verdict: str, detail: str, **evidence: Any) -> dict[str, Any]:
    return {"status": verdict, "detail": detail, **evidence}


def _critical_nets(route_cfg: dict[str, Any]) -> list[str]:
    pairs = ((route_cfg.get("route") or {}).get("preflight_critical_pairs")
             or [])
    return sorted({str(row[key]) for row in pairs if isinstance(row, dict)
                   for key in ("p", "n") if row.get(key)})


def _required_checks(mode: str, critical_nets: list[str],
                     route_cfg: dict[str, Any],
                     prepared: Path | None) -> list[str]:
    """Derive promotion applicability from the exact route capability.

    A missing declaration is not allowed to decide its own applicability.  In
    particular, a board that declares critical pairs requires realized length
    and adjacent-reference-plane evidence in full mode even when the leaf
    checker reports ``N-A`` because its configuration is absent.
    """
    required = {"realized_via_aspect"}
    if critical_nets:
        required.update({"critical_connectivity", "simple_conductor"})
    route = route_cfg.get("route") or {}
    if route.get("ownership"):
        required.add("route_ownership")
    if prepared is not None:
        required.add("route_base")
    if mode == "full":
        required.add("native_drc")
        if critical_nets:
            required.update({"critical_copper_length", "reference_plane"})
        if route_cfg.get("via_ampacity"):
            required.add("via_ampacity")
    return sorted(required)


def _admission(checks: dict[str, dict[str, Any]],
               required_checks: list[str]) -> tuple[str, dict[str, int], list[str]]:
    """Preserve schema-1 authority while observing the shared core in shadow.

    Until an explicit promotion canary transfers authority, a shared-core
    disagreement is evidence only: it cannot loosen *or tighten* the legacy
    verdict.  The CLI records only a pending sibling request; a separately
    budgeted canary may call ``_shadow_admission``.
    """
    missing = sorted(set(required_checks) - set(checks))
    required_not_pass = sorted(
        name for name in required_checks
        if name in checks and checks[name].get("status") != "PASS")
    statuses = [str(row.get("status")) for row in checks.values()]
    if missing or any(status == "INCOMPLETE" for status in statuses) or any(
            checks[name].get("status") == "N-A" for name in required_not_pass):
        legacy_verdict = "INCOMPLETE"
    elif any(status == "FAIL" for status in statuses):
        legacy_verdict = "REJECTED"
    else:
        legacy_verdict = "ACCEPTED"
    coverage = {
        "pass": sum(status == "PASS" for status in statuses),
        "non_applicable": sum(status == "N-A" for status in statuses),
        "fail": sum(status == "FAIL" for status in statuses),
        "incomplete": sum(status == "INCOMPLETE" for status in statuses),
        "required": len(required_checks),
        "required_pass": sum(
            checks.get(name, {}).get("status") == "PASS"
            for name in required_checks),
        "total": len(checks),
    }
    coverage["passing"] = coverage["pass"]

    return legacy_verdict, coverage, sorted(set(missing + required_not_pass))


def _shadow_admission(checks: dict[str, dict[str, Any]],
                      required_checks: list[str], mode: str) -> dict[str, Any]:
    """Derive the shared-core comparison without joining receipt authority."""
    try:
        decision = route_acceptance_core.admit(
            "final" if mode == "full" else "wave", {
                **checks,
                "_meta": {"required_checks": sorted(set(required_checks) | {
                    name for name, row in checks.items()
                    if str(row.get("status")) != "N-A"
                })},
            })
        return {
            "schema": 1, "kind": "route-acceptance-shadow-v1",
            "authority": "SHADOW", "status": "OBSERVED",
            "decision": decision,
        }
    except Exception as exc:
        return {
            "schema": 1, "kind": "route-acceptance-shadow-v1",
            "authority": "SHADOW", "status": "INCOMPLETE",
            "detail": str(exc),
        }


def _pending_shadow_admission(receipt: dict[str, Any]) -> dict[str, Any]:
    """Describe a shared-core comparison without executing it in this run."""

    return {
        "schema": 1, "kind": "route-acceptance-shadow-v1",
        "authority": "SHADOW", "status": "INCOMPLETE",
        "subject": receipt.get("subject"),
        "requested": {
            "mode": receipt.get("mode"),
            "required_checks": receipt.get("required_checks"),
            "detail": "run shared-core admission in a separate bounded task",
        },
    }


def _simple_conductor(project: Path, board: Path,
                      critical_nets: list[str],
                      route_cfg: dict[str, Any]) -> dict[str, Any]:
    if not critical_nets:
        return {"status": "N-A", "detail": "no critical nets declared",
                "nets": []}
    nets, layers, text = copper_length_audit.read_copper(board)
    plated = copper_length_audit.read_plated_pads(text)
    failures, rows = [], []
    raw_allow = ((route_cfg.get("route") or {})
                 .get("critical_branch_allowlist") or [])
    allowlist: list[dict[str, Any]] = []
    for index, item in enumerate(raw_allow):
        if not isinstance(item, dict):
            failures.append(
                f"critical_branch_allowlist[{index}] must be a mapping")
            continue
        try:
            net = str(item["net"])
            at = item["at"]
            x_mm, y_mm = float(at[0]), float(at[1])
            layer = str(item["layer"])
            degree = int(item["degree"])
            why = str(item["why"]).strip()
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            failures.append(
                f"critical_branch_allowlist[{index}] is malformed: {exc}")
            continue
        if net not in critical_nets:
            failures.append(
                f"critical_branch_allowlist[{index}] names non-critical net "
                f"{net}")
            continue
        if degree < 3 or not why:
            failures.append(
                f"critical_branch_allowlist[{index}] requires degree >= 3 "
                "and non-empty why")
            continue
        allowlist.append({"index": index, "net": net, "x_mm": x_mm,
                          "y_mm": y_mm, "layer": layer,
                          "degree": degree, "why": why,
                          "matched": False})
    for name in critical_nets:
        if name not in nets:
            failures.append(f"{name}: no realized copper")
            continue
        geometry = copper_length_audit.net_geometry(
            nets[name], layers, None, plated.get(name, ()))
        row = {key: geometry[key] for key in (
            "n_seg", "n_via", "n_branch", "n_cyclic", "n_comp", "n_end")}
        row["net"] = name
        row["branch_vertices"] = geometry.get("branch_vertices") or []
        row["allowed_branch_vertices"] = []
        rows.append(row)
        for vertex in row["branch_vertices"]:
            matches = [item for item in allowlist
                       if item["net"] == name
                       and item["layer"] == vertex["layer"]
                       and item["degree"] == vertex["degree"]
                       and abs(item["x_mm"] - vertex["x_mm"]) <= 0.001
                       and abs(item["y_mm"] - vertex["y_mm"]) <= 0.001]
            if len(matches) != 1:
                failures.append(
                    f"{name}: unapproved branch degree {vertex['degree']} at "
                    f"({vertex['x_mm']:.6f},{vertex['y_mm']:.6f}) "
                    f"{vertex['layer']}")
                continue
            matches[0]["matched"] = True
            row["allowed_branch_vertices"].append({
                key: matches[0][key]
                for key in ("x_mm", "y_mm", "layer", "degree", "why")})
        if geometry["n_cyclic"]:
            failures.append(
                f"{name}: {geometry['n_cyclic']} cyclic component(s)")
    for item in allowlist:
        if not item["matched"]:
            failures.append(
                f"stale critical_branch_allowlist[{item['index']}]: "
                f"{item['net']} degree {item['degree']} at "
                f"({item['x_mm']:.6f},{item['y_mm']:.6f}) {item['layer']} "
                "matches no realized branch")
    return {
        "status": "FAIL" if failures else "PASS",
        "detail": f"{len(rows)}/{len(critical_nets)} critical net(s) graded",
        "nets": rows, "failures": failures,
    }


def _route_paths(project: Path, board_name: str | None = None) -> tuple[Path, Path]:
    route, route_note = board_scoped(
        project, "route.yaml", board_name)
    nets, nets_note = board_scoped(
        project, "rules/nets.yaml", board_name)
    if route is None or not route.is_file():
        raise ValueError(f"route contract unresolved: {route_note}")
    if nets is None or not nets.is_file():
        raise ValueError(f"net rules unresolved: {nets_note}")
    return route.resolve(), nets.resolve()


def _run(command: list[str], cwd: Path) -> tuple[int, str]:
    completed = run_bounded(
        command, cwd=cwd, timeout_s=600, heartbeat_s=10,
        label="route-acceptance-gate-child", echo=False)
    return completed.returncode, completed.output


def grade(project: Path, board: Path, *, mode: str,
          prepared: Path | None = None, board_name: str | None = None,
          drc_json: Path | None = None, kicad_cli: str = "kicad-cli") -> dict[str, Any]:
    project, board = project.resolve(), board.resolve()
    route_path, nets_path = _route_paths(project, board_name)
    route_cfg = yaml.safe_load(route_path.read_text(encoding="utf-8-sig")) or {}
    critical_nets = _critical_nets(route_cfg)
    checks: dict[str, dict[str, Any]] = {}

    if prepared is not None:
        script = Path(__file__).resolve().parent / "promoted_route_check.py"
        rc, output = _run(["/usr/bin/python3", str(script), "--prepared",
                           str(prepared.resolve()), "--chain", str(board),
                           "--process-config", str(route_path)], project)
        checks["route_base"] = _status(
            "PASS" if rc == 0 else "FAIL" if rc == 1 else "INCOMPLETE",
            output[-4000:].strip() or f"exit {rc}")
    else:
        checks["route_base"] = _status(
            "N-A", "no prepared-board inheritance subject supplied")

    try:
        notes = critical_route_check.check(
            project, board, require_connected=True,
            route_path=route_path, nets_path=nets_path)
        checks["critical_connectivity"] = _status(
            "PASS", f"{len(critical_nets)} critical net(s) connected",
            notes=notes)
    except Exception as exc:
        checks["critical_connectivity"] = _status("FAIL", str(exc))

    checks["simple_conductor"] = _simple_conductor(
        project, board, critical_nets, route_cfg)

    try:
        board_nets, pad_counts = route_ownership_preflight._load_board_facts(board)
        nets_cfg = yaml.safe_load(nets_path.read_text(encoding="utf-8-sig")) or {}
        ownership = route_ownership_preflight.audit_config(
            route_cfg, pad_counts=pad_counts, board_nets=board_nets,
            nets_cfg=nets_cfg)
        checks["route_ownership"] = _status(
            ownership["verdict"],
            f"{len(ownership['findings'])} ownership finding(s)",
            report=ownership)
    except Exception as exc:
        checks["route_ownership"] = _status("INCOMPLETE", str(exc))

    try:
        via_aspect = realized_via_aspect_check.inspect(
            board, project, board_name)
        checks["realized_via_aspect"] = _status(
            via_aspect["verdict"],
            f"{via_aspect['coverage']['graded']}/"
            f"{via_aspect['coverage']['total']} via(s) graded",
            report=via_aspect)
    except Exception as exc:
        checks["realized_via_aspect"] = _status("INCOMPLETE", str(exc))

    if mode == "full":
        try:
            length = copper_length_audit.grade(project, str(board))
            if not length["n_group"]:
                length_status = "N-A"
            elif length["fails"] or length["unreached"]:
                length_status = "FAIL"
            else:
                length_status = "PASS"
            checks["critical_copper_length"] = _status(
                length_status,
                f"{length['n_measured']}/{length['n_member']} member path(s) measured",
                report=length)
        except Exception as exc:
            checks["critical_copper_length"] = _status("INCOMPLETE", str(exc))

        try:
            plane = reference_plane_check.inspect(board, nets_path)
            checks["reference_plane"] = _status(
                plane["verdict"],
                f"{len(plane.get('checks') or {})} reference-plane declaration(s)",
                report=plane)
        except Exception as exc:
            checks["reference_plane"] = _status("INCOMPLETE", str(exc))

        try:
            failures, report, note = via_ampacity_check.check(board, route_path)
            checks["via_ampacity"] = _status(
                "N-A" if note else "FAIL" if failures else "PASS",
                note or f"{len(report['transfers'])} transfer bank(s) graded",
                report=report or {})
        except Exception as exc:
            checks["via_ampacity"] = _status("INCOMPLETE", str(exc))

        drc_json = (drc_json or
                    project / "06_build/verification/route_acceptance_drc.json")
        drc_json = drc_json.resolve()
        drc_json.parent.mkdir(parents=True, exist_ok=True)
        checks["native_drc"] = route_acceptance_core.run_native_drc(
            board, drc_json, profile="final", kicad_cli=kicad_cli,
            cwd=project, timeout=600)

    required_checks = _required_checks(
        mode, critical_nets, route_cfg, prepared)
    verdict, coverage, required_not_pass = _admission(
        checks, required_checks)
    inputs = {"board": _record(board), "route": _record(route_path),
              "nets": _record(nets_path)}
    if prepared is not None:
        inputs["prepared"] = _record(prepared.resolve())
    return {
        "schema": 1, "kind": "route-acceptance-receipt-v1",
        "mode": mode, "verdict": verdict, "subject": inputs["board"],
        "inputs": inputs, "checks": checks,
        "required_checks": required_checks,
        "required_not_pass": required_not_pass,
        "coverage": coverage,
    }


def verify(receipt_path: Path) -> tuple[bool, list[str]]:
    failures = []
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return False, [f"receipt cannot be read: {exc}"]
    if receipt.get("schema") != 1 or receipt.get("kind") != "route-acceptance-receipt-v1":
        failures.append("unsupported receipt schema/kind")
    if receipt.get("verdict") not in {"ACCEPTED", "REJECTED", "INCOMPLETE"}:
        failures.append("invalid receipt verdict")
    for name, record in sorted((receipt.get("inputs") or {}).items()):
        path = Path(str(record.get("path") or ""))
        if not path.is_file() or _record(path) != record:
            failures.append(f"input moved or changed: {name}")
    checks = receipt.get("checks") or {}
    native_evidence = (checks.get("native_drc") or {}).get("evidence") or {}
    if native_evidence.get("path"):
        path = Path(str(native_evidence["path"]))
        if (not path.is_file() or
                hashlib.sha256(path.read_bytes()).hexdigest() !=
                native_evidence.get("sha256")):
            failures.append("native DRC evidence moved or changed")
    native_subject = (checks.get("native_drc") or {}).get("subject") or {}
    if native_subject and native_subject != (receipt.get("inputs") or {}).get("board"):
        failures.append("native DRC subject differs from receipt board")
    if "native_drc" in checks:
        native = checks.get("native_drc") or {}
        binding_valid, binding_failures = \
            route_acceptance_core.verify_native_drc_binding(
                native)
        if not binding_valid:
            failures.extend(binding_failures)
        if native_evidence.get("path") and Path(str(native_evidence["path"])).is_file():
            regraded = route_acceptance_core.classify_native_drc_result(
                returncode=native.get("process_exit"),
                report_path=Path(str(native_evidence["path"])),
                profile=str(native.get("profile") or "final"),
                evidence_fresh=True, evidence_complete=True)
            for field in ("status", "counts", "finding_signatures"):
                if native.get(field) != regraded.get(field):
                    failures.append(
                        f"native DRC {field} differs from reopened report")
            try:
                rebound = route_acceptance_core.bind_native_drc_result(
                    regraded, (receipt.get("inputs") or {}).get("board") or {})
                if rebound.get("binding") != native.get("binding"):
                    failures.append(
                        "native DRC binding differs after report reclassification")
            except Exception as exc:
                failures.append(f"native DRC cannot be rebound: {exc}")
    try:
        route_record = (receipt.get("inputs") or {})["route"]
        route_path = Path(str(route_record["path"]))
        route_cfg = yaml.safe_load(
            route_path.read_text(encoding="utf-8-sig")) or {}
        expected_required = _required_checks(
            str(receipt.get("mode")), _critical_nets(route_cfg), route_cfg,
            Path("prepared") if "prepared" in (receipt.get("inputs") or {})
            else None)
        if receipt.get("required_checks") != expected_required:
            failures.append("required-check applicability differs from exact route contract")
        expected_verdict, expected_coverage, expected_not_pass = _admission(
            checks, expected_required)
        if receipt.get("verdict") != expected_verdict:
            failures.append("receipt verdict disagrees with check statuses/applicability")
        if receipt.get("coverage") != expected_coverage:
            failures.append("receipt coverage disagrees with check statuses")
        if receipt.get("required_not_pass") != expected_not_pass:
            failures.append("required-not-pass list disagrees with check statuses")
    except Exception as exc:
        failures.append(f"cannot re-derive route applicability: {exc}")
    return not failures, failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    grade_parser = sub.add_parser("grade")
    grade_parser.add_argument("project", type=Path)
    grade_parser.add_argument("--board", type=Path, required=True)
    grade_parser.add_argument("--mode", choices=("quick", "full"), default="full")
    grade_parser.add_argument("--prepared", type=Path)
    grade_parser.add_argument("--board-name")
    grade_parser.add_argument("--drc-json", type=Path)
    grade_parser.add_argument("--json", type=Path, required=True)
    grade_parser.add_argument("--kicad-cli", default="kicad-cli")
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("receipt", type=Path)
    args = parser.parse_args(argv)
    if args.command == "verify":
        valid, failures = verify(args.receipt)
        for failure in failures:
            print(f"  FAIL {failure}")
        print(f"ROUTE-ACCEPTANCE RECEIPT {'PASS' if valid else 'FAIL'}")
        return 0 if valid else 1
    shadow_path = args.json.with_name(f"{args.json.stem}.shadow.json")
    output_paths = {"receipt": args.json, "shadow": shadow_path}
    if args.mode == "full":
        output_paths["native_drc"] = (
            args.drc_json or args.project /
            "06_build/verification/route_acceptance_drc.json")
    try:
        route_input, nets_input = _route_paths(args.project.resolve(),
                                                args.board_name)
        protected_paths = {
            "project": args.project, "board": args.board,
            "route": route_input, "nets": nets_input,
        }
        if args.prepared:
            protected_paths["prepared"] = args.prepared
        require_safe_output_layout(output_paths,
                                   protected_paths=protected_paths)
    except (OSError, ValueError) as exc:
        print(f"ROUTE-ACCEPTANCE INCOMPLETE: {exc}")
        return 2
    try:
        receipt = grade(
            args.project, args.board, mode=args.mode, prepared=args.prepared,
            board_name=args.board_name, drc_json=args.drc_json,
            kicad_cli=args.kicad_cli)
    except Exception as exc:
        print(f"ROUTE-ACCEPTANCE INCOMPLETE: {exc}")
        return 2
    try:
        require_safe_output_layout(
            output_paths,
            protected_paths={
                "project": args.project,
                **{f"input_{name}": Path(record["path"])
                   for name, record in (receipt.get("inputs") or {}).items()},
            },
        )
    except ValueError as exc:
        print(f"ROUTE-ACCEPTANCE INCOMPLETE: {exc}")
        return 2
    # A receipt becomes canonical only after an independent reopen verifies
    # its exact bytes.  A failed fresh check must not leave an ACCEPTED-looking
    # file at the caller's authoritative path.
    provisional = args.json.with_name(
        f".{args.json.name}.verify-{uuid.uuid4().hex}")
    _atomic_json(provisional, receipt)
    try:
        verified, verification_failures = verify(provisional)
    except Exception as exc:
        verified, verification_failures = False, [
            f"independent receipt verification raised: {exc}"]
    if not verified:
        provisional.unlink(missing_ok=True)
        for failure in verification_failures:
            print(f"  FAIL {failure}")
        print("ROUTE-ACCEPTANCE INCOMPLETE: freshly written receipt did not "
              "survive independent verification")
        return 2
    os.replace(provisional, args.json)
    try:
        _atomic_json(shadow_path, _pending_shadow_admission(receipt))
    except Exception as exc:
        # Shadow diagnostics cannot invalidate the independently verified
        # authoritative receipt already published above.  This small sibling
        # write is synchronous; it performs no engineering check or child
        # process and has only ordinary output-filesystem latency.
        print(f"ROUTE-ACCEPTANCE SHADOW INCOMPLETE: {exc}")
    coverage = receipt["coverage"]
    print(f"ROUTE-ACCEPTANCE {receipt['verdict']}: "
          f"{coverage['pass']} PASS / {coverage['non_applicable']} N-A / "
          f"{coverage['fail']} FAIL / {coverage['incomplete']} INCOMPLETE; "
          f"required {coverage['required_pass']}/{coverage['required']} PASS; "
          f"receipt={args.json.resolve()}")
    return {"ACCEPTED": 0, "REJECTED": 1, "INCOMPLETE": 2}[receipt["verdict"]]


if __name__ == "__main__":
    raise SystemExit(main())
