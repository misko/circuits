#!/usr/bin/env python3
"""Strict commissioning and evidence contracts for pcb-enclosure schema v2.

Schema v1 remains owned by ``enclosure_common.py``.  This module is an
additive v2 seam: it validates a hash-bound mechanical-intent document, exact
release subjects, installed-part authority, independent fastener roles,
assembly motion, clearance cases, and an extensible physical-test census.

It deliberately does not generate geometry.  A CAD adapter may consume a
validated v2 configuration, but it must not silently weaken these contracts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import types
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment failure
    raise SystemExit("pcb-enclosure v2 needs PyYAML") from exc

try:
    from enclosure_common import (  # type: ignore
        atomic_output,
        EnclosureError as V1EnclosureError,
        load_json as load_json_strict,
        load_bound_config as load_bound_config_v1,
        read_stable_bytes,
        run_bounded,
        sha256_file as sha256_file_v1,
        stable_file_digest as stable_file_digest_v1,
    )
except ImportError:  # pragma: no cover - package-style import seam
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from enclosure_common import (  # type: ignore
        atomic_output,
        EnclosureError as V1EnclosureError,
        load_json as load_json_strict,
        load_bound_config as load_bound_config_v1,
        read_stable_bytes,
        run_bounded,
        sha256_file as sha256_file_v1,
        stable_file_digest as stable_file_digest_v1,
    )


CONFIG_KIND = "pcb-enclosure-config-v2"
INTENT_KIND = "pcb-enclosure-mechanical-intent-v2"
PHYSICAL_KIND = "pcb-enclosure-physical-evidence-v2"
VALIDATION_KIND = "pcb-enclosure-v2-validation"
V2_VALIDATOR_ROLE = "compose"
V2_VALIDATOR_SOURCE_PATH = "skills/pcb-enclosure/scripts/enclosure_v2.py"
V2_VALIDATOR_RELEASE_PATH = "tooling/enclosure_v2.py"
CONNECTOR_RECEIPT_KIND = "connector-assembly-contract-receipt"
CONNECTOR_COMPILER_ROLE = "connector_assembly_contract"
CONNECTOR_COMPILER_SOURCE_PATH = (
    "skills/pcb-design/scripts/connector_assembly_contract.py")
CONNECTOR_COMPILER_RELEASE_PATH = "tooling/connector_assembly_contract.py"
CONNECTOR_RELEASE_PROJECT_ROOT = "source/connector-assembly"
FDM_AUDIT_COMPILER_ROLE = "fdm_structural_audit"
FDM_AUDIT_COMPILER_SOURCE_PATH = (
    "skills/pcb-enclosure/scripts/fdm_structural_audit.py")
FDM_AUDIT_COMPILER_RELEASE_PATH = "tooling/fdm_structural_audit.py"
COLLISION_BUILDER_ROLE = "collision_builder"
COLLISION_BUILDER_SOURCE_PATH = (
    "skills/pcb-enclosure/scripts/build_collision.py")
COLLISION_BUILDER_RELEASE_PATH = "tooling/build_collision.py"
STEP_INSPECTOR_ROLE = "step_inspector"
STEP_INSPECTOR_SOURCE_PATH = "skills/pcb-enclosure/scripts/inspect_step.py"
STEP_INSPECTOR_RELEASE_PATH = "tooling/inspect_step.py"
PROCESS_RUNNER_SOURCE_PATH = "skills/kicad-pcb/scripts/process_runner.py"
PIPELINE_RUNTIME_SOURCE_PATH = "skills/pcb-design/scripts/pipeline_runtime.py"
SERVICE_INTERFACE_DISPOSITIONS = frozenset({"opening", "service_opening"})

# Closed synthetic fixtures may replace this outer-process seam. Production
# leaves it None: receipt validation and pinned BRep replay then happen in a
# fresh interpreter whose imports resolve only beside the selected builder.
_COLLISION_PROCESS_RUNNER: Any = None

READINESS = ("INCOMPLETE", "CAD_READY", "PRINT_VERIFIED",
             "THERMALLY_VERIFIED")
RESULT_STATUSES = {"FAIL", *READINESS}
READINESS_RANK = {status: index for index, status in enumerate(READINESS)}
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[_.-][a-z0-9]+)*$")
CUSTOM_TEST_RE = re.compile(
    r"^custom\.[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)+$")

AUTHORITY_GRADES = {
    "vendor_authoritative",
    "measured_unit",
    "derived_measurement",
    "conservative_candidate",
    "first_article_observation",
    "inspiration_only",
}
AUTHORITY_REQUIRED_EXCLUSIONS = {
    "vendor_authoritative": {"physical_fit"},
    "measured_unit": {"physical_fit"},
    "derived_measurement": {"physical_fit"},
    "conservative_candidate": {"exact_geometry", "physical_fit"},
    "first_article_observation": {
        "exact_geometry", "clearance", "physical_fit",
        "manufacturing_dimensions",
    },
    "inspiration_only": {
        "exact_geometry", "clearance", "physical_fit",
        "manufacturing_dimensions",
    },
}
BUILTIN_PHYSICAL_TYPES = {
    "insert_coupon",
    "board_drop_in",
    "board_support_clearance",
    "all_interfaces_mated",
    "thermal_soak",
    "lid_off_pcb_retention",
    "case_closure_independence",
    "accessory_insertion_removal",
    "accessory_retention_rattle",
    "cable_strain_clearance",
}
SERVICE_DIMENSION_BASES = {
    "conservative_candidate",
    "physical_observation",
    "unknown",
}
SERVICE_NONNUMERIC_BASES = {"physical_observation", "unknown"}
INTERFACE_SIDE_AXES = {
    # KiCad board coordinates are x-right/y-down.  Keep the semantic edge
    # convention aligned with connector_orientation_gate.py: north is the
    # minimum-Y edge and south is the maximum-Y edge.
    "north": [0.0, -1.0, 0.0],
    "south": [0.0, 1.0, 0.0],
    "east": [1.0, 0.0, 0.0],
    "west": [-1.0, 0.0, 0.0],
    "top": [0.0, 0.0, 1.0],
    "bottom": [0.0, 0.0, -1.0],
}


def _connector_compiler_module(
        expected_binding: Any, *, release_root: Path | None = None,
        release_binding: Any = None):
    """Load the exact receipt-bound compiler bytes as the sole schema authority.

    Import machinery reopens a path after a caller inspects it.  That permits a
    transient file replacement to execute bytes other than the compiler named
    by the receipt.  Capture one stable byte subject, compare it to the receipt
    first, execute those same bytes, and make the imported compiler report that
    captured identity during its deterministic recompile.
    """
    expected = _exact(expected_binding, {"path", "sha256", "size"},
                      "connector receipt compiler binding")
    if expected["path"] != CONNECTOR_COMPILER_SOURCE_PATH:
        raise V2Error(
            "connector receipt compiler binding does not name the canonical "
            f"compiler {CONNECTOR_COMPILER_SOURCE_PATH}")

    if release_root is None:
        if release_binding is not None:
            raise V2Error(
                "connector release compiler binding requires a release root")
        repo_root = Path(__file__).resolve().parents[3]
        path = repo_root / CONNECTOR_COMPILER_SOURCE_PATH
        reported_binding = dict(expected)
    else:
        if release_binding is None:
            raise V2Error(
                "connector release replay requires a manifest-bound compiler")
        release_item = _exact(
            release_binding, {"path", "sha256", "size"},
            "release connector compiler binding")
        if release_item["path"] != CONNECTOR_COMPILER_RELEASE_PATH:
            raise V2Error(
                "release connector compiler binding must name the exact "
                f"release path {CONNECTOR_COMPILER_RELEASE_PATH}")
        loaded_release_binding = validate_file_binding(
            release_item, release_root,
            "release connector compiler binding")
        if (loaded_release_binding["sha256"], loaded_release_binding["size"]) != \
                (expected["sha256"], expected["size"]):
            raise V2Error(
                "release connector compiler identity differs from the exact "
                "compiler identity recorded by the receipt")
        path = loaded_release_binding["path"]
        # The connector receipt owns the canonical source identity.  The
        # release manifest owns where those exact bytes are reopened.  Keep
        # compilation deterministic by reporting the former back to the
        # compiler while executing only the latter.
        reported_binding = dict(expected)
    try:
        payload = read_stable_bytes(path, "connector assembly compiler")
    except V1EnclosureError as exc:
        raise V2Error(f"cannot load connector assembly compiler: {exc}") from exc
    loaded_binding = {
        "path": path,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "size": len(payload),
    }
    if (expected["sha256"], expected["size"]) != \
            (loaded_binding["sha256"], loaded_binding["size"]):
        raise V2Error(
            "connector receipt compiler identity differs from the exact "
            "compiler bytes loaded for regrade")
    module = types.ModuleType("pcb_design_connector_assembly_contract")
    module.__file__ = str(path)
    module.__package__ = None
    try:
        code = compile(payload, str(path), "exec", dont_inherit=True)
        exec(code, module.__dict__)
    except Exception as exc:  # pragma: no cover - trusted runtime boundary
        raise V2Error(f"cannot load connector assembly compiler: {exc}") from exc
    if not hasattr(module, "load_and_compile"):
        raise V2Error("connector assembly compiler lacks load_and_compile API")
    # The compiler normally reopens __file__ to bind its own identity.  Use the
    # exact bytes already loaded, so a second path read cannot mix authorities.
    module._compiler_binding = lambda: dict(reported_binding)
    return module, loaded_binding


def _fdm_audit_compiler_module(
        expected_binding: Any, expected_helper_binding: Any, *,
        release_root: Path | None = None, release_binding: Any = None,
        release_helper_binding: Any = None):
    """Load the exact receipt-bound FDM compiler from stable captured bytes."""
    expected = _exact(expected_binding, {"path", "sha256", "size"},
                      "FDM audit receipt compiler binding")
    if expected["path"] != FDM_AUDIT_COMPILER_SOURCE_PATH:
        raise V2Error(
            "FDM audit receipt compiler does not name the canonical source "
            f"path {FDM_AUDIT_COMPILER_SOURCE_PATH}")
    if release_root is None:
        if release_binding is not None or release_helper_binding is not None:
            raise V2Error("release FDM bindings require a release root")
        path = Path(__file__).resolve().parents[3] / FDM_AUDIT_COMPILER_SOURCE_PATH
        helper_path = Path(__file__).resolve().parents[3] / \
            "skills/pcb-enclosure/scripts/enclosure_common.py"
    else:
        if release_binding is None or release_helper_binding is None:
            raise V2Error(
                "release manufacturing-audit replay requires manifest-bound "
                "compiler and enclosure_common helper roles")
        release_item = _exact(
            release_binding, {"path", "sha256", "size"},
            "release FDM audit compiler binding")
        if release_item["path"] != FDM_AUDIT_COMPILER_RELEASE_PATH:
            raise V2Error(
                "release FDM audit compiler must use exact path "
                f"{FDM_AUDIT_COMPILER_RELEASE_PATH}")
        loaded_release = validate_file_binding(
            release_item, release_root, "release FDM audit compiler binding")
        if (loaded_release["sha256"], loaded_release["size"]) != \
                (expected["sha256"], expected["size"]):
            raise V2Error(
                "release FDM audit compiler identity differs from receipt")
        path = loaded_release["path"]
        helper_item = _exact(
            release_helper_binding, {"path", "sha256", "size"},
            "release FDM schema helper binding")
        if helper_item["path"] != "tooling/enclosure_common.py":
            raise V2Error(
                "release FDM schema helper must use tooling/enclosure_common.py")
        helper_loaded = validate_file_binding(
            helper_item, release_root, "release FDM schema helper binding")
        helper_path = helper_loaded["path"]
    try:
        payload = read_stable_bytes(path, "FDM structural audit compiler")
    except V1EnclosureError as exc:
        raise V2Error(f"cannot load FDM audit compiler: {exc}") from exc
    actual = {"path": path, "sha256": hashlib.sha256(payload).hexdigest(),
              "size": len(payload)}
    if (actual["sha256"], actual["size"]) != \
            (expected["sha256"], expected["size"]):
        raise V2Error("FDM audit compiler bytes differ from receipt")
    expected_helper = _exact(
        expected_helper_binding, {"path", "sha256", "size"},
        "FDM audit receipt enclosure_common binding")
    if expected_helper["path"] != \
            "skills/pcb-enclosure/scripts/enclosure_common.py":
        raise V2Error("FDM audit helper has noncanonical source path")
    try:
        helper_payload = read_stable_bytes(
            helper_path, "FDM audit schema-v1 helper")
    except V1EnclosureError as exc:
        raise V2Error(f"cannot load FDM audit schema helper: {exc}") from exc
    helper_actual = {
        "path": helper_path, "sha256": hashlib.sha256(helper_payload).hexdigest(),
        "size": len(helper_payload)}
    if (helper_actual["sha256"], helper_actual["size"]) != \
            (expected_helper["sha256"], expected_helper["size"]):
        raise V2Error("FDM audit enclosure_common helper differs from receipt")
    module = types.ModuleType("pcb_enclosure_fdm_structural_audit")
    module.__file__ = str(path)
    module.__package__ = None
    try:
        code = compile(payload, str(path), "exec", dont_inherit=True)
        exec(code, module.__dict__)
    except Exception as exc:  # pragma: no cover - trusted runtime boundary
        raise V2Error(f"cannot load FDM audit compiler: {exc}") from exc
    for api in ("audit_paths", "audit_paths_with_contract"):
        if not hasattr(module, api):
            raise V2Error(f"FDM audit compiler lacks {api} API")
    # The receipt owns the canonical source identity even when its exact bytes
    # are virtualized below release-local tooling/.
    module._compiler_binding = lambda module_path=None: dict(expected)
    module._helper_binding = lambda module_path=None: dict(expected_helper)
    return module, actual, helper_actual


def _collision_builder_authority(
        expected_binding: Any, expected_helper_binding: Any,
        expected_inspector_binding: Any, expected_process_runner_binding: Any,
        expected_pipeline_runtime_binding: Any, *,
        release_root: Path | None = None, release_binding: Any = None,
        release_helper_binding: Any = None,
        release_inspector_binding: Any = None,
        release_process_runner_binding: Any = None,
        release_pipeline_runtime_binding: Any = None):
    """Select exact builder/helper bytes without importing either in-process."""
    expected = _exact(expected_binding, {"path", "sha256", "size"},
                      "collision receipt builder binding")
    if expected["path"] != COLLISION_BUILDER_SOURCE_PATH:
        raise V2Error(
            "collision receipt builder does not name canonical source path "
            f"{COLLISION_BUILDER_SOURCE_PATH}")
    if release_root is None:
        if any(item is not None for item in (
                release_binding, release_helper_binding,
                release_inspector_binding, release_process_runner_binding,
                release_pipeline_runtime_binding)):
            raise V2Error("release collision closure requires a release root")
        path = Path(__file__).resolve().parents[3] / \
            COLLISION_BUILDER_SOURCE_PATH
        helper_path = Path(__file__).resolve().parents[3] / \
            "skills/pcb-enclosure/scripts/enclosure_common.py"
        inspector_path = Path(__file__).resolve().parents[3] / \
            STEP_INSPECTOR_SOURCE_PATH
        process_runner_path = Path(__file__).resolve().parents[3] / \
            PROCESS_RUNNER_SOURCE_PATH
        pipeline_runtime_path = Path(__file__).resolve().parents[3] / \
            PIPELINE_RUNTIME_SOURCE_PATH
    else:
        if any(item is None for item in (
                release_binding, release_helper_binding,
                release_inspector_binding, release_process_runner_binding,
                release_pipeline_runtime_binding)):
            raise V2Error(
                "release manufacturing collision requires manifest-bound "
                "builder, inspector, helper, and bounded-runtime roles")
        item = _exact(
            release_binding, {"path", "sha256", "size"},
            "release collision builder binding")
        if item["path"] != COLLISION_BUILDER_RELEASE_PATH:
            raise V2Error(
                "release collision builder must use exact path "
                f"{COLLISION_BUILDER_RELEASE_PATH}")
        loaded = validate_file_binding(
            item, release_root, "release collision builder binding")
        if (loaded["sha256"], loaded["size"]) != \
                (expected["sha256"], expected["size"]):
            raise V2Error(
                "release collision builder identity differs from receipt")
        path = loaded["path"]
        helper_item = _exact(
            release_helper_binding, {"path", "sha256", "size"},
            "release collision enclosure_common binding")
        if helper_item["path"] != "tooling/enclosure_common.py":
            raise V2Error(
                "release collision helper must use tooling/enclosure_common.py")
        helper_path = validate_file_binding(
            helper_item, release_root,
            "release collision enclosure_common binding")["path"]
        release_tools = (
            (release_inspector_binding, STEP_INSPECTOR_RELEASE_PATH,
             "release collision STEP inspector"),
            (release_process_runner_binding, "tooling/process_runner.py",
             "release collision process runner"),
            (release_pipeline_runtime_binding, "tooling/pipeline_runtime.py",
             "release collision pipeline runtime"),
        )
        loaded_tools = []
        for raw, expected_path, where in release_tools:
            item = _exact(raw, {"path", "sha256", "size"}, where)
            if item["path"] != expected_path:
                raise V2Error(f"{where} must use exact path {expected_path}")
            loaded_tools.append(validate_file_binding(item, release_root, where))
        inspector_path, process_runner_path, pipeline_runtime_path = [
            item["path"] for item in loaded_tools]
    try:
        payload = read_stable_bytes(path, "collision builder")
    except V1EnclosureError as exc:
        raise V2Error(f"cannot load collision builder: {exc}") from exc
    actual = {"path": path, "sha256": hashlib.sha256(payload).hexdigest(),
              "size": len(payload)}
    if (actual["sha256"], actual["size"]) != \
            (expected["sha256"], expected["size"]):
        raise V2Error("collision builder bytes differ from receipt")
    expected_helper = _exact(
        expected_helper_binding, {"path", "sha256", "size"},
        "collision receipt enclosure_common binding")
    if expected_helper["path"] != \
            "skills/pcb-enclosure/scripts/enclosure_common.py":
        raise V2Error(
            "collision receipt helper has noncanonical source path")
    try:
        helper_payload = read_stable_bytes(
            helper_path, "collision enclosure_common helper")
    except V1EnclosureError as exc:
        raise V2Error(f"cannot load collision helper: {exc}") from exc
    helper_actual = {
        "path": helper_path,
        "sha256": hashlib.sha256(helper_payload).hexdigest(),
        "size": len(helper_payload),
    }
    if (helper_actual["sha256"], helper_actual["size"]) != \
            (expected_helper["sha256"], expected_helper["size"]):
        raise V2Error("collision enclosure_common bytes differ from receipt")
    authorities = {
        "builder": (expected, actual),
        "enclosure_common": (expected_helper, helper_actual),
        "step_inspector": (
            _exact(expected_inspector_binding, {"path", "sha256", "size"},
                   "collision receipt step_inspector binding"),
            {"path": inspector_path, "sha256": sha256_file(inspector_path),
             "size": inspector_path.stat().st_size}),
        "process_runner": (
            _exact(expected_process_runner_binding,
                   {"path", "sha256", "size"},
                   "collision receipt process_runner binding"),
            {"path": process_runner_path,
             "sha256": sha256_file(process_runner_path),
             "size": process_runner_path.stat().st_size}),
        "pipeline_runtime": (
            _exact(expected_pipeline_runtime_binding,
                   {"path", "sha256", "size"},
                   "collision receipt pipeline_runtime binding"),
            {"path": pipeline_runtime_path,
             "sha256": sha256_file(pipeline_runtime_path),
             "size": pipeline_runtime_path.stat().st_size}),
    }
    canonical_paths = {
        "step_inspector": STEP_INSPECTOR_SOURCE_PATH,
        "process_runner": PROCESS_RUNNER_SOURCE_PATH,
        "pipeline_runtime": PIPELINE_RUNTIME_SOURCE_PATH,
    }
    for name in ("step_inspector", "process_runner", "pipeline_runtime"):
        expected_item, loaded_item = authorities[name]
        if expected_item["path"] != canonical_paths[name]:
            raise V2Error(f"collision {name} has noncanonical source path")
        if (expected_item["sha256"], expected_item["size"]) != \
                (loaded_item["sha256"], loaded_item["size"]):
            raise V2Error(f"collision {name} bytes differ from receipt")
    return {name: loaded for name, (_, loaded) in authorities.items()}


def _run_collision_process(command: Sequence[str], *, cwd: Path,
                           timeout_s: float = 1200.0) -> None:
    """Use the shared bounded runtime for fresh helper-hermetic replay."""
    try:
        result = run_bounded(
            command, cwd=cwd, timeout_s=timeout_s,
            max_output_bytes_per_stream=1_000_000)
    except V1EnclosureError as exc:
        raise V2Error(f"collision replay process failed: {exc}") from exc
    if result.returncode != 0:
        raise V2Error(
            f"collision replay process exited {result.returncode}; "
            f"output tail:\n{result.stdout[-4000:]}")


class V2Error(ValueError):
    """A v2 document is malformed, ambiguous, or contradictory."""


class StrictLoader(yaml.SafeLoader):
    """YAML loader which rejects duplicate mapping keys."""


def _construct_mapping(loader: StrictLoader, node: yaml.MappingNode,
                       deep: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise V2Error(
                f"duplicate YAML key {key!r} at line "
                f"{key_node.start_mark.line + 1}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


StrictLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.load(read_stable_bytes(
            path, f"schema-v2 YAML input {path}").decode("utf-8"),
            Loader=StrictLoader)
    except (OSError, yaml.YAMLError, UnicodeError) as exc:
        raise V2Error(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise V2Error(f"{path}: expected a YAML mapping")
    return value


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = load_json_strict(path)
    except V1EnclosureError as exc:
        raise V2Error(f"cannot read {path}: {exc}") from exc
    return value


def sha256_file(path: Path) -> str:
    return sha256_file_v1(path)


def semantic_sha256(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _mapping(value: Any, where: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise V2Error(f"{where}: expected mapping")
    return value


def _exact(value: Any, fields: Iterable[str], where: str) -> Mapping[str, Any]:
    item = _mapping(value, where)
    expected = set(fields)
    actual = set(item)
    if actual != expected:
        raise V2Error(
            f"{where}: fields differ; missing={sorted(expected - actual)}, "
            f"unknown={sorted(actual - expected)}")
    return item


def _exact_optional(value: Any, required: Iterable[str], optional: Iterable[str],
                    where: str) -> Mapping[str, Any]:
    """Require a closed field set while permitting additive compatibility rows."""
    item = _mapping(value, where)
    required_set = set(required)
    optional_set = set(optional)
    actual = set(item)
    missing = required_set - actual
    unknown = actual - required_set - optional_set
    if missing or unknown:
        raise V2Error(
            f"{where}: fields differ; missing={sorted(missing)}, "
            f"unknown={sorted(unknown)}")
    return item


def _string(value: Any, where: str, *, nonempty: bool = True) -> str:
    if not isinstance(value, str) or (nonempty and not value.strip()):
        raise V2Error(f"{where}: expected {'non-empty ' if nonempty else ''}string")
    return value


def _identifier(value: Any, where: str) -> str:
    result = _string(value, where)
    if not ID_RE.fullmatch(result):
        raise V2Error(f"{where}: expected normalized lower-case identifier")
    return result


def _enum(value: Any, choices: Iterable[str], where: str) -> str:
    result = _string(value, where)
    allowed = set(choices)
    if result not in allowed:
        raise V2Error(f"{where}: expected one of {sorted(allowed)}")
    return result


def _boolean(value: Any, where: str) -> bool:
    if not isinstance(value, bool):
        raise V2Error(f"{where}: expected boolean")
    return value


def _number(value: Any, where: str, *, positive: bool = False,
            nonnegative: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise V2Error(f"{where}: expected number")
    result = float(value)
    if not math.isfinite(result):
        raise V2Error(f"{where}: expected finite number")
    if positive and result <= 0:
        raise V2Error(f"{where}: expected > 0")
    if nonnegative and result < 0:
        raise V2Error(f"{where}: expected >= 0")
    return result


def _vec(value: Any, count: int, where: str, *, nonzero: bool = False) -> list[float]:
    if not isinstance(value, list) or len(value) != count:
        raise V2Error(f"{where}: expected {count}-element list")
    result = [_number(axis, f"{where}[{index}]")
              for index, axis in enumerate(value)]
    if nonzero and math.sqrt(sum(axis * axis for axis in result)) <= 1e-12:
        raise V2Error(f"{where}: vector must be nonzero")
    return result


def _unique_ids(rows: Any, where: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(rows, list) or (not rows and not allow_empty):
        qualifier = "possibly empty" if allow_empty else "non-empty"
        raise V2Error(f"{where}: expected {qualifier} list")
    result: list[str] = []
    for index, value in enumerate(rows):
        ident = _identifier(value, f"{where}[{index}]")
        if ident in result:
            raise V2Error(f"{where}: duplicate identifier {ident}")
        result.append(ident)
    return result


def _unique_strings(rows: Any, where: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(rows, list) or (not rows and not allow_empty):
        qualifier = "possibly empty" if allow_empty else "non-empty"
        raise V2Error(f"{where}: expected {qualifier} list")
    result: list[str] = []
    for index, value in enumerate(rows):
        text = _string(value, f"{where}[{index}]")
        if text in result:
            raise V2Error(f"{where}: duplicate value {text}")
        result.append(text)
    return result


def _row_ids(rows: Any, where: str, *, allow_empty: bool = False) -> set[str]:
    if not isinstance(rows, list) or (not rows and not allow_empty):
        qualifier = "possibly empty" if allow_empty else "non-empty"
        raise V2Error(f"{where}: expected {qualifier} list")
    result: set[str] = set()
    for index, row in enumerate(rows):
        item = _mapping(row, f"{where}[{index}]")
        ident = _identifier(item.get("id"), f"{where}[{index}].id")
        if ident in result:
            raise V2Error(f"{where}: duplicate id {ident}")
        result.add(ident)
    return result


def _safe_relative_path(value: Any, root: Path, where: str) -> Path:
    text = _string(value, where)
    path = Path(text)
    if path.is_absolute() or "\\" in text or any(
            part in {"", ".", ".."} for part in path.parts):
        raise V2Error(
            f"{where}: path must be normalized, relative, and traversal-free")
    base = root.resolve()
    cursor = base
    for part in path.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise V2Error(f"{where}: symlink paths are not accepted")
    resolved = (base / path).resolve(strict=False)
    if not resolved.is_relative_to(base):
        raise V2Error(f"{where}: path escapes root")
    return resolved


def validate_file_binding(value: Any, root: Path, where: str) -> dict[str, Any]:
    item = _exact(value, {"path", "sha256", "size"}, where)
    path = _safe_relative_path(item["path"], root, f"{where}.path")
    digest = _string(item["sha256"], f"{where}.sha256")
    if not HEX64_RE.fullmatch(digest):
        raise V2Error(f"{where}.sha256: expected lowercase 64-hex")
    size = item["size"]
    if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
        raise V2Error(f"{where}.size: expected positive integer")
    try:
        _, info, actual_hash = stable_file_digest_v1(path, where)
    except V1EnclosureError as exc:
        raise V2Error(str(exc)) from exc
    actual_size = info.st_size
    if actual_size != size or actual_hash != digest:
        raise V2Error(f"{where}: bound size/hash differs from actual file")
    return {"path": path, "sha256": digest, "size": size}


def _load_bound_json_bytes(value: Any, root: Path,
                           where: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Parse and bind one stable JSON byte subject without a second path read."""
    item = _exact(value, {"path", "sha256", "size"}, where)
    path = _safe_relative_path(item["path"], root, f"{where}.path")
    digest = _string(item["sha256"], f"{where}.sha256")
    if not HEX64_RE.fullmatch(digest):
        raise V2Error(f"{where}.sha256: expected lowercase 64-hex")
    size = item["size"]
    if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
        raise V2Error(f"{where}.size: expected positive integer")
    try:
        payload = read_stable_bytes(path, where)
    except V1EnclosureError as exc:
        raise V2Error(str(exc)) from exc
    if len(payload) != size or hashlib.sha256(payload).hexdigest() != digest:
        raise V2Error(f"{where}: bound size/hash differs from actual file")

    def reject_duplicate_keys(
            pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, child in pairs:
            if key in result:
                raise V2Error(f"{where}: duplicate JSON key {key!r}")
            result[key] = child
        return result

    try:
        parsed = json.loads(payload.decode("utf-8"),
                            object_pairs_hook=reject_duplicate_keys)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise V2Error(f"{where}: cannot parse JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise V2Error(f"{where}: expected a JSON object")
    return parsed, {"path": path, "sha256": digest, "size": size}


def _validate_cabled_parts(rows: Any) -> list[dict[str, Any]]:
    ids = _row_ids(rows, "intent.requirements.cabled_parts", allow_empty=True)
    result = []
    for index, raw in enumerate(rows):
        where = f"intent.requirements.cabled_parts[{index}]"
        row = _exact(raw, {
            "id", "part", "cable_pre_attached", "threading_permitted",
            "bending_permitted", "disconnecting_permitted",
        }, where)
        _identifier(row["id"], f"{where}.id")
        _identifier(row["part"], f"{where}.part")
        for field in ("cable_pre_attached", "threading_permitted",
                      "bending_permitted", "disconnecting_permitted"):
            _boolean(row[field], f"{where}.{field}")
        if row["cable_pre_attached"] and row["threading_permitted"]:
            raise V2Error(
                f"{where}: a pre-attached cable may not be authorized for threading; "
                "model a full-part insertion path")
        result.append(dict(row))
    if len(ids) != len(result):  # defensive; _row_ids already rejects duplicates
        raise V2Error("intent.requirements.cabled_parts: duplicate rows")
    parts = [row["part"] for row in result]
    if len(parts) != len(set(parts)):
        raise V2Error("intent.requirements.cabled_parts: duplicate part")
    return result


def validate_mechanical_intent(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the standalone v2 mechanical commissioning authority."""
    top = _exact(value, {
        "schema", "kind", "name", "desired_release", "requirements",
        "states", "operations", "unknowns", "excluded_claims",
    }, "intent")
    if top["schema"] != 2 or isinstance(top["schema"], bool):
        raise V2Error("intent.schema: expected 2")
    if top["kind"] != INTENT_KIND:
        raise V2Error(f"intent.kind: expected {INTENT_KIND!r}")
    _identifier(top["name"], "intent.name")

    desired = _exact(top["desired_release"], {"lifecycle", "readiness"},
                     "intent.desired_release")
    _enum(desired["lifecycle"], {"draft", "immutable"},
          "intent.desired_release.lifecycle")
    _enum(desired["readiness"], set(READINESS) - {"INCOMPLETE"},
          "intent.desired_release.readiness")

    requirements = _exact(top["requirements"], {
        "pcb_retained_with_lid_removed", "cabled_parts",
    }, "intent.requirements")
    _boolean(requirements["pcb_retained_with_lid_removed"],
             "intent.requirements.pcb_retained_with_lid_removed")
    if not requirements["pcb_retained_with_lid_removed"]:
        raise V2Error(
            "intent.requirements.pcb_retained_with_lid_removed: schema v2 "
            "requires independent lid-off PCB retention")
    cabled_parts = _validate_cabled_parts(requirements["cabled_parts"])

    state_ids = _row_ids(top["states"], "intent.states")
    purposes: list[str] = []
    state_map: dict[str, Mapping[str, Any]] = {}
    for index, raw in enumerate(top["states"]):
        where = f"intent.states[{index}]"
        row = _exact(raw, {
            "id", "purpose", "present_parts", "secured_fastener_groups",
            "enclosure_closed", "pcb_retained",
        }, where)
        ident = _identifier(row["id"], f"{where}.id")
        purpose = _enum(row["purpose"], {
            "initial", "insertion", "lid_removed", "installed", "service",
            "removal",
        }, f"{where}.purpose")
        purposes.append(purpose)
        _unique_ids(row["present_parts"], f"{where}.present_parts",
                    allow_empty=True)
        _unique_ids(row["secured_fastener_groups"],
                    f"{where}.secured_fastener_groups", allow_empty=True)
        _boolean(row["enclosure_closed"], f"{where}.enclosure_closed")
        _boolean(row["pcb_retained"], f"{where}.pcb_retained")
        if purpose == "lid_removed" and row["enclosure_closed"]:
            raise V2Error(f"{where}: lid_removed state cannot be closed")
        if purpose == "installed" and not row["enclosure_closed"]:
            raise V2Error(f"{where}: installed state must be closed")
        state_map[ident] = row
    for required_purpose in ("lid_removed", "installed"):
        if purposes.count(required_purpose) != 1:
            raise V2Error(
                f"intent.states: expected exactly one {required_purpose} state")

    operation_ids = _row_ids(top["operations"], "intent.operations")
    operation_map: dict[str, Mapping[str, Any]] = {}
    for index, raw in enumerate(top["operations"]):
        where = f"intent.operations[{index}]"
        row = _exact(raw, {
            "id", "kind", "from_state", "to_state", "moving_parts",
            "direction", "travel_mm", "cable_condition",
            "threading_permitted", "bending_permitted",
            "disconnecting_permitted", "clearance_case",
        }, where)
        ident = _identifier(row["id"], f"{where}.id")
        kind = _enum(row["kind"], {"linear_insert", "linear_remove"},
                     f"{where}.kind")
        source = _identifier(row["from_state"], f"{where}.from_state")
        target = _identifier(row["to_state"], f"{where}.to_state")
        if source not in state_ids or target not in state_ids:
            raise V2Error(f"{where}: from/to state is not declared")
        if source == target:
            raise V2Error(f"{where}: from_state and to_state must differ")
        moving = _unique_ids(row["moving_parts"], f"{where}.moving_parts")
        _vec(row["direction"], 3, f"{where}.direction", nonzero=True)
        _number(row["travel_mm"], f"{where}.travel_mm", positive=True)
        _enum(row["cable_condition"],
              {"pre_attached", "detached", "not_applicable"},
              f"{where}.cable_condition")
        for field in ("threading_permitted", "bending_permitted",
                      "disconnecting_permitted"):
            _boolean(row[field], f"{where}.{field}")
        _identifier(row["clearance_case"], f"{where}.clearance_case")

        before = set(state_map[source]["present_parts"])
        after = set(state_map[target]["present_parts"])
        changed = after - before if kind == "linear_insert" else before - after
        opposite = before - after if kind == "linear_insert" else after - before
        if opposite:
            raise V2Error(
                f"{where}: {kind} also changes parts in the opposite direction: "
                f"{sorted(opposite)}")
        if changed != set(moving):
            raise V2Error(
                f"{where}: moving_parts {sorted(moving)} do not equal state delta "
                f"{sorted(changed)}")
        operation_map[ident] = row

    for cabled in cabled_parts:
        moving_ops = [row for row in operation_map.values()
                      if cabled["part"] in row["moving_parts"]]
        if not moving_ops:
            raise V2Error(
                f"intent cabled part {cabled['part']}: no linear operation declared")
        if cabled["cable_pre_attached"] and not any(
                row["kind"] == "linear_insert" for row in moving_ops):
            raise V2Error(
                f"intent cabled part {cabled['part']}: no insertion operation")
        expected_condition = ("pre_attached" if cabled["cable_pre_attached"]
                              else "detached")
        for row in moving_ops:
            if row["cable_condition"] != expected_condition:
                raise V2Error(
                    f"intent operation {row['id']}: cable condition contradicts "
                    f"cabled part {cabled['part']}")
            for field in ("threading_permitted", "bending_permitted",
                          "disconnecting_permitted"):
                if row[field] != cabled[field]:
                    raise V2Error(
                        f"intent operation {row['id']}: {field} contradicts "
                        f"cabled part {cabled['part']}")

    unknown_ids = _row_ids(top["unknowns"], "intent.unknowns", allow_empty=True)
    for index, raw in enumerate(top["unknowns"]):
        where = f"intent.unknowns[{index}]"
        row = _exact(raw, {"id", "scope", "question", "blocks_readiness"}, where)
        _identifier(row["id"], f"{where}.id")
        _identifier(row["scope"], f"{where}.scope")
        _string(row["question"], f"{where}.question")
        _enum(row["blocks_readiness"],
              {"CAD_READY", "PRINT_VERIFIED", "THERMALLY_VERIFIED"},
              f"{where}.blocks_readiness")
    if len(unknown_ids) != len(top["unknowns"]):
        raise V2Error("intent.unknowns: duplicate ids")
    excluded = _unique_ids(top["excluded_claims"], "intent.excluded_claims",
                           allow_empty=True)
    if len(excluded) != len(set(excluded)):
        raise V2Error("intent.excluded_claims: duplicate claim")
    return dict(value)


def _validate_external_subjects(rows: Any, root: Path) -> tuple[dict[str, Any],
                                                               dict[str, Any]]:
    ids = _row_ids(rows, "config.external_subjects", allow_empty=True)
    result: dict[str, Any] = {}
    bindings: dict[str, Any] = {}
    for index, raw in enumerate(rows):
        where = f"config.external_subjects[{index}]"
        row = _exact(raw, {"id", "role", "source", "authority"}, where)
        ident = _identifier(row["id"], f"{where}.id")
        _identifier(row["role"], f"{where}.role")
        bindings[ident] = validate_file_binding(
            row["source"], root, f"{where}.source")
        authority = _exact(row["authority"],
                           {"grade", "basis", "excluded_claims"},
                           f"{where}.authority")
        grade = _enum(authority["grade"], AUTHORITY_GRADES,
                      f"{where}.authority.grade")
        _string(authority["basis"], f"{where}.authority.basis")
        excluded = set(_unique_ids(
            authority["excluded_claims"],
            f"{where}.authority.excluded_claims", allow_empty=True))
        missing = AUTHORITY_REQUIRED_EXCLUSIONS[grade] - excluded
        if missing:
            raise V2Error(
                f"{where}.authority.excluded_claims: grade {grade} must "
                f"exclude {sorted(missing)}")
        result[ident] = dict(row)
    if len(ids) != len(result):
        raise V2Error("config.external_subjects: duplicate ids")
    return result, bindings


def _validate_scopes(rows: Any) -> dict[str, Mapping[str, Any]]:
    ids = _row_ids(rows, "config.verification_scopes")
    result: dict[str, Mapping[str, Any]] = {}
    for index, raw in enumerate(rows):
        where = f"config.verification_scopes[{index}]"
        row = _exact(raw, {"id", "description", "required", "depends_on"}, where)
        ident = _identifier(row["id"], f"{where}.id")
        _string(row["description"], f"{where}.description")
        _boolean(row["required"], f"{where}.required")
        deps = _unique_ids(row["depends_on"], f"{where}.depends_on",
                           allow_empty=True)
        if ident in deps:
            raise V2Error(f"{where}.depends_on: scope cannot depend on itself")
        result[ident] = row
    for ident, row in result.items():
        missing = set(row["depends_on"]) - ids
        if missing:
            raise V2Error(
                f"config verification scope {ident}: unknown dependencies "
                f"{sorted(missing)}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(ident: str) -> None:
        if ident in visiting:
            raise V2Error("config.verification_scopes: dependency cycle")
        if ident in visited:
            return
        visiting.add(ident)
        for dep in result[ident]["depends_on"]:
            visit(dep)
        visiting.remove(ident)
        visited.add(ident)

    for ident in result:
        visit(ident)
    return result


def _validate_installed_parts(rows: Any, scopes: Mapping[str, Any],
                              external: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    _row_ids(rows, "config.installed_parts")
    result: dict[str, Mapping[str, Any]] = {}
    role_count: dict[str, int] = {}
    for index, raw in enumerate(rows):
        where = f"config.installed_parts[{index}]"
        row = _exact(raw, {"id", "role", "source", "scopes"}, where)
        ident = _identifier(row["id"], f"{where}.id")
        role = _enum(row["role"],
                     {"pcb", "base", "lid", "panel", "accessory", "hardware"},
                     f"{where}.role")
        role_count[role] = role_count.get(role, 0) + 1
        source = _exact(row["source"], {"kind", "id"}, f"{where}.source")
        source_kind = _enum(source["kind"],
                            {"subject", "generated", "external_subject"},
                            f"{where}.source.kind")
        source_id = _identifier(source["id"], f"{where}.source.id")
        if source_kind == "subject" and not (role == "pcb" and source_id == "pcb"):
            raise V2Error(
                f"{where}.source: only the pcb installed part may use subject:pcb")
        if source_kind == "external_subject" and source_id not in external:
            raise V2Error(f"{where}.source: unknown external subject {source_id}")
        part_scopes = _unique_ids(row["scopes"], f"{where}.scopes")
        missing = set(part_scopes) - set(scopes)
        if missing:
            raise V2Error(f"{where}.scopes: unknown scopes {sorted(missing)}")
        result[ident] = row
    for singular in ("pcb", "base", "lid"):
        if role_count.get(singular, 0) != 1:
            raise V2Error(
                f"config.installed_parts: expected exactly one {singular} part")
    return result


def _normalize(vec: Sequence[float]) -> tuple[float, float, float]:
    length = math.sqrt(sum(axis * axis for axis in vec))
    return tuple(axis / length for axis in vec)  # type: ignore[return-value]


def _cross(a: Sequence[float], b: Sequence[float]) -> tuple[float, float, float]:
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _norm(vec: Sequence[float]) -> float:
    return math.sqrt(sum(axis * axis for axis in vec))


def _parallel_axis_distance(first: Mapping[str, Any],
                            second: Mapping[str, Any]) -> float | None:
    a = _normalize(first["direction"])
    b = _normalize(second["direction"])
    if _norm(_cross(a, b)) > 1e-6:
        return None
    delta = [second["origin_mm"][index] - first["origin_mm"][index]
             for index in range(3)]
    return _norm(_cross(delta, a))


def _validate_fasteners(rows: Any, policy: Mapping[str, Any],
                        parts: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    _row_ids(rows, "config.fastener_groups")
    result: dict[str, Mapping[str, Any]] = {}
    roles: dict[str, list[str]] = {role: [] for role in
                                   ("board_retention", "case_closure", "accessory")}
    axes_by_group: dict[str, list[Mapping[str, Any]]] = {}
    part_ids = set(parts)
    pcb = next(ident for ident, row in parts.items() if row["role"] == "pcb")
    base = next(ident for ident, row in parts.items() if row["role"] == "base")
    lid = next(ident for ident, row in parts.items() if row["role"] == "lid")
    accessory_parts = {ident for ident, row in parts.items()
                       if row["role"] == "accessory"}

    for index, raw in enumerate(rows):
        where = f"config.fastener_groups[{index}]"
        row = _exact(raw, {
            "id", "role", "axes", "retained_parts", "hardware",
        }, where)
        ident = _identifier(row["id"], f"{where}.id")
        role = _enum(row["role"], roles, f"{where}.role")
        roles[role].append(ident)
        axis_ids = _row_ids(row["axes"], f"{where}.axes")
        axes = []
        for ai, raw_axis in enumerate(row["axes"]):
            axis_where = f"{where}.axes[{ai}]"
            axis = _exact(raw_axis, {"id", "origin_mm", "direction"}, axis_where)
            _identifier(axis["id"], f"{axis_where}.id")
            _vec(axis["origin_mm"], 3, f"{axis_where}.origin_mm")
            _vec(axis["direction"], 3, f"{axis_where}.direction", nonzero=True)
            axes.append(axis)
        if len(axis_ids) != len(axes):
            raise V2Error(f"{where}.axes: duplicate ids")
        retained = set(_unique_ids(row["retained_parts"], f"{where}.retained_parts"))
        missing = retained - part_ids
        if missing:
            raise V2Error(f"{where}.retained_parts: unknown parts {sorted(missing)}")
        hardware = _exact(row["hardware"], {
            "thread", "screw_length_mm", "minimum_engagement_mm",
            "minimum_tip_clearance_mm",
        }, f"{where}.hardware")
        _string(hardware["thread"], f"{where}.hardware.thread")
        _number(hardware["screw_length_mm"],
                f"{where}.hardware.screw_length_mm", positive=True)
        _number(hardware["minimum_engagement_mm"],
                f"{where}.hardware.minimum_engagement_mm", positive=True)
        _number(hardware["minimum_tip_clearance_mm"],
                f"{where}.hardware.minimum_tip_clearance_mm", nonnegative=True)
        if role == "board_retention":
            if not {pcb, base}.issubset(retained) or lid in retained:
                raise V2Error(
                    f"{where}: board_retention must retain pcb+base and must not "
                    "retain the lid")
        elif role == "case_closure":
            if not {base, lid}.issubset(retained) or pcb in retained:
                raise V2Error(
                    f"{where}: case_closure must retain base+lid and must not "
                    "retain the PCB")
        elif not (retained & accessory_parts) or not (base in retained or lid in retained):
            raise V2Error(
                f"{where}: accessory group must retain an accessory and base or lid")
        result[ident] = row
        axes_by_group[ident] = axes

    if not roles["board_retention"] or not roles["case_closure"]:
        raise V2Error(
            "config.fastener_groups: board_retention and case_closure are required")
    tolerance = policy["axis_disjoint_tolerance_mm"]
    for board_group in roles["board_retention"]:
        for case_group in roles["case_closure"]:
            for board_axis in axes_by_group[board_group]:
                for case_axis in axes_by_group[case_group]:
                    distance = _parallel_axis_distance(board_axis, case_axis)
                    if distance is not None and distance <= tolerance + 1e-12:
                        raise V2Error(
                            "config.fastener_groups: board_retention and "
                            f"case_closure axes overlap within {tolerance:g} mm "
                            f"({board_group}:{board_axis['id']} vs "
                            f"{case_group}:{case_axis['id']})")
    return result


def _validate_clearance_cases(rows: Any, scopes: Mapping[str, Any],
                              parts: Mapping[str, Any],
                              operations: Mapping[str, Any],
                              cabled: Mapping[str, Any],
                              states: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    _row_ids(rows, "config.clearance_cases")
    result: dict[str, Mapping[str, Any]] = {}
    operation_cases: dict[str, str] = {}
    for index, raw in enumerate(rows):
        where = f"config.clearance_cases[{index}]"
        row = _exact(raw, {
            "id", "scope", "operation", "opening_id", "moving_parts",
            "obstacles", "envelope_basis", "method", "minimum_clearance_mm",
        }, where)
        ident = _identifier(row["id"], f"{where}.id")
        scope = _identifier(row["scope"], f"{where}.scope")
        if scope not in scopes:
            raise V2Error(f"{where}.scope: unknown scope {scope}")
        operation = _identifier(row["operation"], f"{where}.operation")
        if operation not in operations:
            raise V2Error(f"{where}.operation: unknown operation {operation}")
        if operation in operation_cases:
            raise V2Error(
                f"config.clearance_cases: operation {operation} has multiple cases")
        operation_cases[operation] = ident
        _identifier(row["opening_id"], f"{where}.opening_id")
        moving = set(_unique_ids(row["moving_parts"], f"{where}.moving_parts"))
        obstacles = set(_unique_ids(row["obstacles"], f"{where}.obstacles"))
        unknown = (moving | obstacles) - set(parts)
        if unknown:
            raise V2Error(f"{where}: unknown parts {sorted(unknown)}")
        if moving & obstacles:
            raise V2Error(f"{where}: moving parts cannot also be obstacles")
        if moving != set(operations[operation]["moving_parts"]):
            raise V2Error(
                f"{where}.moving_parts: differs from operation {operation}")
        source_state = states[operations[operation]["from_state"]]
        expected_obstacles = set(source_state["present_parts"]) - moving
        if obstacles != expected_obstacles:
            raise V2Error(
                f"{where}.obstacles: must exactly equal every non-moving part "
                f"present in source state; expected={sorted(expected_obstacles)}, "
                f"actual={sorted(obstacles)}")
        basis = _enum(row["envelope_basis"],
                      {"full_part", "conservative_body", "cable_only"},
                      f"{where}.envelope_basis")
        _enum(row["method"], {"linear_sweep_exact", "linear_sweep_envelope"},
              f"{where}.method")
        _number(row["minimum_clearance_mm"],
                f"{where}.minimum_clearance_mm", nonnegative=True)
        for part in moving:
            constraint = cabled.get(part)
            if constraint and not constraint["threading_permitted"] and \
                    basis != "full_part":
                raise V2Error(
                    f"{where}.envelope_basis: no-threading cabled part {part} "
                    "requires full_part, never cable_only or a partial body")
        result[ident] = row
    expected_by_operation = {
        ident: row["clearance_case"] for ident, row in operations.items()}
    if set(operation_cases) != set(expected_by_operation):
        raise V2Error(
            "config.clearance_cases: every linear operation needs exactly one case")
    for operation, case_id in expected_by_operation.items():
        if operation_cases[operation] != case_id:
            raise V2Error(
                f"config clearance operation {operation}: intent names {case_id}, "
                f"config supplies {operation_cases[operation]}")
    return result


def _positive_vec_or_none(value: Any, count: int, where: str) -> list[float] | None:
    if value is None:
        return None
    if not isinstance(value, list) or len(value) != count:
        raise V2Error(f"{where}: expected null or {count}-element list")
    return [_number(axis, f"{where}[{index}]", positive=True)
            for index, axis in enumerate(value)]


def _nonnegative_vec_or_none(value: Any, count: int,
                             where: str) -> list[float] | None:
    if value is None:
        return None
    if not isinstance(value, list) or len(value) != count:
        raise V2Error(f"{where}: expected null or {count}-element list")
    return [_number(axis, f"{where}[{index}]", nonnegative=True)
            for index, axis in enumerate(value)]


def _validate_service_solid(value: Any, where: str) -> dict[str, Any]:
    row = _exact(value, {"basis", "envelope_mm"}, where)
    basis = _enum(row["basis"], SERVICE_DIMENSION_BASES, f"{where}.basis")
    envelope = _positive_vec_or_none(row["envelope_mm"], 3,
                                     f"{where}.envelope_mm")
    if (envelope is None) != (basis in SERVICE_NONNUMERIC_BASES):
        raise V2Error(
            f"{where}: physical_observation/unknown require a null envelope; "
            "dimension-bearing bases require a positive 3-D envelope")
    return dict(row)


def _validate_service_cable(value: Any, where: str) -> dict[str, Any]:
    row = _exact(value, {
        "basis", "diameter_mm", "straight_run_mm", "exit_direction",
    }, where)
    basis = _enum(row["basis"], SERVICE_DIMENSION_BASES, f"{where}.basis")
    diameter = row["diameter_mm"]
    if diameter is not None:
        _number(diameter, f"{where}.diameter_mm", positive=True)
    straight_run = row["straight_run_mm"]
    if straight_run is not None:
        _number(straight_run, f"{where}.straight_run_mm", nonnegative=True)
    direction = row["exit_direction"]
    if direction is not None:
        _vec(direction, 3, f"{where}.exit_direction", nonzero=True)
    numeric = diameter is not None and straight_run is not None and \
        direction is not None
    if numeric != (basis not in SERVICE_NONNUMERIC_BASES):
        raise V2Error(
            f"{where}: physical_observation/unknown require null cable values; "
            "dimension-bearing bases require diameter, straight run, and a "
            "nonzero exit direction")
    return dict(row)


def _validate_service_bend(value: Any, where: str) -> dict[str, Any]:
    row = _exact(value, {"basis", "minimum_radius_mm", "swept_envelope_mm"},
                 where)
    basis = _enum(row["basis"], SERVICE_DIMENSION_BASES, f"{where}.basis")
    radius = row["minimum_radius_mm"]
    if radius is not None:
        _number(radius, f"{where}.minimum_radius_mm", positive=True)
    swept = _positive_vec_or_none(row["swept_envelope_mm"], 3,
                                  f"{where}.swept_envelope_mm")
    numeric = radius is not None and swept is not None
    if numeric != (basis not in SERVICE_NONNUMERIC_BASES):
        raise V2Error(
            f"{where}: physical_observation/unknown require null bend values; "
            "dimension-bearing bases require radius and swept envelope")
    return dict(row)


def _validate_service_sweep(value: Any, operations: Mapping[str, Any],
                            where: str) -> dict[str, Any]:
    row = _exact(value, {"basis", "method", "operation"}, where)
    basis = _enum(row["basis"], {
        "conservative_candidate", "physical_observation", "unknown",
    }, f"{where}.basis")
    method = _enum(row["method"], {
        "linear_sweep_envelope", "physical_test", "not_modeled",
    }, f"{where}.method")
    operation = row["operation"]
    if operation is not None:
        operation = _identifier(operation, f"{where}.operation")
        if operation not in operations:
            raise V2Error(f"{where}.operation: unknown operation {operation}")
    expected_basis = {
        "linear_sweep_envelope": "conservative_candidate",
        "physical_test": "physical_observation",
    }
    if method == "not_modeled":
        if operation is not None or basis not in {
                "physical_observation", "unknown"}:
            raise V2Error(
                f"{where}: not_modeled requires null operation and an "
                "observation/unknown basis")
    else:
        if operation is None or basis != expected_basis[method]:
            raise V2Error(
                f"{where}: {method} requires a declared operation and "
                f"basis {expected_basis[method]}")
    return dict(row)


def _validate_service_allowances(value: Any, where: str) -> dict[str, Any]:
    row = _exact(value, {
        "basis", "process_per_side_mm", "assembly_per_side_mm",
    }, where)
    basis = _enum(row["basis"], {
        "conservative_candidate", "physical_observation", "unknown",
    }, f"{where}.basis")
    process = _nonnegative_vec_or_none(
        row["process_per_side_mm"], 3, f"{where}.process_per_side_mm")
    assembly = _nonnegative_vec_or_none(
        row["assembly_per_side_mm"], 3, f"{where}.assembly_per_side_mm")
    numeric = process is not None and assembly is not None
    if numeric != (basis not in SERVICE_NONNUMERIC_BASES):
        raise V2Error(
            f"{where}: physical_observation/unknown require null allowances; "
            "candidate bases require process and assembly vectors")
    return dict(row)


def _validate_service_envelopes(rows: Any, scopes: Mapping[str, Any],
                                interfaces: Sequence[Mapping[str, Any]],
                                operations: Mapping[str, Any],
                                states: Mapping[str, Any],
                                external: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the full connector-to-cable service-envelope checklist.

    The top-level field is additive for compatibility with already-published
    schema-v2 documents. Once present, however, it must cover every edge or
    top-side service interface whose v1 disposition is ``opening`` or
    ``service_opening`` exactly once.
    """
    if rows is None:
        return {}
    _row_ids(rows, "config.service_envelopes")
    interface_map = {row["id"]: row for row in interfaces}
    required = {ident for ident, row in interface_map.items()
                if row["disposition"] in SERVICE_INTERFACE_DISPOSITIONS}
    result: dict[str, Any] = {}
    covered: set[str] = set()
    simultaneous_groups: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(rows):
        where = f"config.service_envelopes[{index}]"
        row = _exact(raw, {
            "id", "interface_id", "scope", "simultaneous_group",
            "mated_in_states", "mated_during_operations",
            "observation_subject", "connector_body", "mated_plug",
            "strain_relief", "cable", "bend",
            "installation_sweep", "allowances",
        }, where)
        ident = _identifier(row["id"], f"{where}.id")
        interface_id = _identifier(row["interface_id"],
                                   f"{where}.interface_id")
        if interface_id not in required:
            raise V2Error(
                f"{where}.interface_id: {interface_id} is not a declared "
                "connector/service opening")
        if interface_id in covered:
            raise V2Error(
                f"config.service_envelopes: duplicate interface {interface_id}")
        covered.add(interface_id)
        scope = _identifier(row["scope"], f"{where}.scope")
        if scope not in scopes:
            raise V2Error(f"{where}.scope: unknown scope {scope}")
        if not scopes[scope]["required"]:
            raise V2Error(
                f"{where}.scope: service-envelope scopes must be required")
        simultaneous_group = _identifier(
            row["simultaneous_group"], f"{where}.simultaneous_group")
        mated_states = set(_unique_ids(
            row["mated_in_states"], f"{where}.mated_in_states"))
        if not mated_states:
            raise V2Error(f"{where}.mated_in_states: expected non-empty list")
        unknown_states = mated_states - set(states)
        if unknown_states:
            raise V2Error(
                f"{where}.mated_in_states: unknown states "
                f"{sorted(unknown_states)}")
        mated_operations = set(_unique_ids(
            row["mated_during_operations"],
            f"{where}.mated_during_operations", allow_empty=True))
        unknown_operations = mated_operations - set(operations)
        if unknown_operations:
            raise V2Error(
                f"{where}.mated_during_operations: unknown operations "
                f"{sorted(unknown_operations)}")
        for operation_id in mated_operations:
            operation = operations[operation_id]
            endpoints = {operation["from_state"], operation["to_state"]}
            if not endpoints.issubset(mated_states):
                raise V2Error(
                    f"{where}.mated_during_operations: {operation_id} does not "
                    "remain mated in both endpoint states")
            if operation["cable_condition"] != "pre_attached":
                raise V2Error(
                    f"{where}.mated_during_operations: {operation_id} must "
                    "declare cable_condition pre_attached")
            if operation["threading_permitted"]:
                raise V2Error(
                    f"{where}.mated_during_operations: {operation_id} cannot "
                    "thread a cable that remains mated")
            if operation["disconnecting_permitted"]:
                raise V2Error(
                    f"{where}.mated_during_operations: {operation_id} cannot "
                    "permit disconnecting while the interface remains mated")
        signature = {
            "scope": scope,
            "mated_in_states": frozenset(mated_states),
            "mated_during_operations": frozenset(mated_operations),
        }
        previous = simultaneous_groups.get(simultaneous_group)
        if previous is None:
            simultaneous_groups[simultaneous_group] = signature
        else:
            for field in (
                    "scope", "mated_in_states", "mated_during_operations"):
                if signature[field] != previous[field]:
                    raise V2Error(
                        f"{where}.simultaneous_group: members of "
                        f"{simultaneous_group} must share identical {field}")
        observation_subject = row["observation_subject"]
        if observation_subject is not None:
            observation_subject = _identifier(
                observation_subject, f"{where}.observation_subject")
            if observation_subject not in external:
                raise V2Error(
                    f"{where}.observation_subject: unknown external subject "
                    f"{observation_subject}")
        _validate_service_solid(row["connector_body"],
                                f"{where}.connector_body")
        _validate_service_solid(row["mated_plug"], f"{where}.mated_plug")
        _validate_service_solid(row["strain_relief"],
                                f"{where}.strain_relief")
        _validate_service_cable(row["cable"], f"{where}.cable")
        _validate_service_bend(row["bend"], f"{where}.bend")
        _validate_service_sweep(row["installation_sweep"], operations,
                                f"{where}.installation_sweep")
        _validate_service_allowances(row["allowances"],
                                     f"{where}.allowances")
        bases = {
            row["connector_body"]["basis"], row["mated_plug"]["basis"],
            row["strain_relief"]["basis"], row["cable"]["basis"],
            row["bend"]["basis"], row["installation_sweep"]["basis"],
            row["allowances"]["basis"],
        }
        has_observation = "physical_observation" in bases
        if has_observation:
            if observation_subject is None or external[observation_subject][
                    "authority"]["grade"] != "first_article_observation":
                raise V2Error(
                    f"{where}.observation_subject: physical_observation rows "
                    "require a bound first_article_observation external subject")
        elif observation_subject is not None:
            raise V2Error(
                f"{where}.observation_subject: no physical_observation basis "
                "uses this subject")
        result[ident] = dict(row)
    if covered != required:
        raise V2Error(
            "config.service_envelopes: once declared, coverage must equal every "
            f"connector/service opening; missing={sorted(required - covered)}, "
            f"extra={sorted(covered - required)}")
    return result


def _service_envelope_candidate_dimensions_complete(
        row: Mapping[str, Any]) -> bool:
    solids = (row["connector_body"], row["mated_plug"], row["strain_relief"])
    if any(solid["envelope_mm"] is None for solid in solids):
        return False
    if row["cable"]["diameter_mm"] is None:
        return False
    if row["cable"]["straight_run_mm"] is None or \
            row["cable"]["exit_direction"] is None:
        return False
    if row["bend"]["minimum_radius_mm"] is None or \
            row["bend"]["swept_envelope_mm"] is None:
        return False
    if row["installation_sweep"]["method"] not in {
            "linear_sweep_exact", "linear_sweep_envelope"}:
        return False
    allowances = row["allowances"]
    return allowances["process_per_side_mm"] is not None and \
        allowances["assembly_per_side_mm"] is not None


def _load_shared_connector_receipt(value: Any, root: Path,
                                   where: str, *,
                                   release_compiler: Any = None
                                   ) -> tuple[dict[str, Any],
                                              dict[str, Any],
                                              dict[str, Any]]:
    """Reopen and independently recompile the pcb-design connector receipt."""
    receipt, binding = _load_bound_json_bytes(value, root, where)
    top = _exact(receipt, {
        "schema", "kind", "status", "inputs", "semantic_sha256",
        "subject_sha256", "assemblies", "simultaneous_groups", "unknowns",
        "summary",
    }, f"{where}.receipt")
    if top["schema"] != 1 or isinstance(top["schema"], bool):
        raise V2Error(f"{where}.receipt.schema: expected 1")
    if top["kind"] != CONNECTOR_RECEIPT_KIND:
        raise V2Error(
            f"{where}.receipt.kind: expected {CONNECTOR_RECEIPT_KIND!r}")
    _enum(top["status"], {"PASS", "INCOMPLETE"},
          f"{where}.receipt.status")
    for field in ("semantic_sha256", "subject_sha256"):
        digest = _string(top[field], f"{where}.receipt.{field}")
        if not HEX64_RE.fullmatch(digest):
            raise V2Error(
                f"{where}.receipt.{field}: expected lowercase 64-hex")
    inputs = _exact(top["inputs"], {
        "contract", "compiler", "evidence_files",
    }, f"{where}.receipt.inputs")
    input_root = (root / CONNECTOR_RELEASE_PROJECT_ROOT
                  if release_compiler is not None else root)
    contract_binding = validate_file_binding(
        inputs["contract"], input_root,
        f"{where}.receipt.inputs.contract")
    evidence_bindings = []
    if not isinstance(inputs["evidence_files"], list):
        raise V2Error(f"{where}.receipt.inputs.evidence_files: expected list")
    for index, raw_evidence in enumerate(inputs["evidence_files"]):
        evidence_where = \
            f"{where}.receipt.inputs.evidence_files[{index}]"
        evidence = _exact(raw_evidence, {
            "id", "kind", "path", "sha256", "size",
        }, evidence_where)
        # The connector compiler owns id/kind semantics.  The enclosure
        # consumer independently reopens the exact file identity without
        # pretending those two receipt fields are part of a generic binding.
        evidence_bindings.append(validate_file_binding({
            "path": evidence["path"],
            "sha256": evidence["sha256"],
            "size": evidence["size"],
        }, input_root, evidence_where))
    if not isinstance(top["assemblies"], list) or not top["assemblies"]:
        raise V2Error(f"{where}.receipt.assemblies: expected non-empty list")
    if not isinstance(top["simultaneous_groups"], list):
        raise V2Error(
            f"{where}.receipt.simultaneous_groups: expected list")
    if not isinstance(top["unknowns"], list):
        raise V2Error(f"{where}.receipt.unknowns: expected list")

    # The shared compiler is the only schema authority. Recompiling here closes
    # the fake/stale-receipt seam without cloning its many connector fields into
    # the enclosure skill.
    if release_compiler is None:
        compiler, loaded_compiler = _connector_compiler_module(
            inputs["compiler"])
    else:
        compiler, loaded_compiler = _connector_compiler_module(
            inputs["compiler"], release_root=root,
            release_binding=release_compiler)
    try:
        valid, findings = compiler.validate_receipt(receipt, input_root)
    except Exception as exc:
        raise V2Error(
            f"{where}.receipt: shared connector regrade failed: {exc}") from exc
    if not valid:
        raise V2Error(
            f"{where}.receipt: shared connector regrade failed: "
            f"{'; '.join(findings)}")

    def require_unchanged(binding_row: Mapping[str, Any], label: str) -> None:
        """Reopen an input after regrade so a mid-grade edit cannot pass."""
        try:
            current = read_stable_bytes(
                binding_row["path"], f"{label} post-regrade")
        except V1EnclosureError as exc:
            raise V2Error(
                f"{where}.receipt: {label} changed during regrade: {exc}") \
                from exc
        if (len(current) != binding_row["size"] or
                hashlib.sha256(current).hexdigest() !=
                binding_row["sha256"]):
            raise V2Error(
                f"{where}.receipt: {label} changed during regrade")

    # A checkout edit after the first binding check must not leave a successful
    # report for receipt, contract, evidence, or compiler bytes that are no
    # longer the named authorities.
    require_unchanged(binding, "connector receipt")
    require_unchanged(contract_binding, "connector contract")
    for index, evidence_binding in enumerate(evidence_bindings):
        require_unchanged(
            evidence_binding, f"connector evidence file {index}")
    require_unchanged({
        "path": loaded_compiler["path"],
        "sha256": loaded_compiler["sha256"],
        "size": loaded_compiler["size"],
    }, "connector compiler")
    protected_inputs = {
        "contract": contract_binding,
        "evidence_files": evidence_bindings,
        "compiler": {
            "path": loaded_compiler["path"],
            "sha256": loaded_compiler["sha256"],
            "size": loaded_compiler["size"],
        },
    }
    return dict(receipt), binding, protected_inputs


def _validate_interface_assemblies(value: Any, root: Path,
                                   scopes: Mapping[str, Any],
                                   interfaces: Sequence[Mapping[str, Any]],
                                   operations: Mapping[str, Any],
                                   states: Mapping[str, Any], *,
                                   release_compiler: Any = None
                                   ) -> dict[str, Any]:
    """Bind serviced openings to shared profiles without restating dimensions."""
    if value is None:
        return {}
    top = _exact(value, {
        "receipt", "mappings", "non_enclosure_refs", "group_state_bindings",
    }, "config.interface_assemblies")
    receipt, binding, input_bindings = _load_shared_connector_receipt(
        top["receipt"], root, "config.interface_assemblies.receipt",
        release_compiler=release_compiler)

    assemblies: dict[str, Mapping[str, Any]] = {}
    ref_to_assembly: dict[str, str] = {}
    ref_groups: dict[str, set[str]] = {}
    ref_axes: dict[str, list[float]] = {}
    for index, raw in enumerate(receipt["assemblies"]):
        where = f"connector_receipt.assemblies[{index}]"
        assembly = _mapping(raw, where)
        ident = _identifier(assembly.get("id"), f"{where}.id")
        if ident in assemblies:
            raise V2Error(f"connector receipt has duplicate assembly {ident}")
        instances = assembly.get("instances")
        if not isinstance(instances, list) or not instances:
            raise V2Error(f"{where}.instances: expected non-empty list")
        for ii, raw_instance in enumerate(instances):
            iw = f"{where}.instances[{ii}]"
            instance = _exact(raw_instance, {
                "ref", "mating_axis_board", "simultaneous_group_ids",
            }, iw)
            ref = _string(instance["ref"], f"{iw}.ref")
            if ref in ref_to_assembly:
                raise V2Error(
                    f"connector receipt ref {ref} appears in multiple assemblies")
            axis = _vec(instance["mating_axis_board"], 3,
                        f"{iw}.mating_axis_board", nonzero=True)
            groups = set(_unique_ids(
                instance["simultaneous_group_ids"],
                f"{iw}.simultaneous_group_ids", allow_empty=True))
            ref_to_assembly[ref] = ident
            ref_groups[ref] = groups
            ref_axes[ref] = axis
        assemblies[ident] = assembly

    group_members: dict[str, set[str]] = {}
    group_serviceable: dict[str, set[str]] = {}
    group_required_states: dict[str, str] = {}
    for index, raw in enumerate(receipt["simultaneous_groups"]):
        where = f"connector_receipt.simultaneous_groups[{index}]"
        group = _exact(raw, {
            "id", "members", "required_state", "serviceable_member_refs",
        }, where)
        ident = _identifier(group["id"], f"{where}.id")
        if ident in group_members:
            raise V2Error(f"connector receipt has duplicate group {ident}")
        members = set(_unique_strings(group["members"], f"{where}.members"))
        serviceable = set(_unique_strings(
            group["serviceable_member_refs"],
            f"{where}.serviceable_member_refs"))
        required_state = _identifier(
            group["required_state"], f"{where}.required_state")
        if not serviceable.issubset(members):
            raise V2Error(
                f"{where}.serviceable_member_refs: must be group members")
        group_members[ident] = members
        group_serviceable[ident] = serviceable
        group_required_states[ident] = required_state

    non_enclosure_refs: dict[str, dict[str, str]] = {}
    if not isinstance(top["non_enclosure_refs"], list):
        raise V2Error(
            "config.interface_assemblies.non_enclosure_refs: expected list")
    for index, raw in enumerate(top["non_enclosure_refs"]):
        where = f"config.interface_assemblies.non_enclosure_refs[{index}]"
        row = _exact(raw, {"ref", "disposition", "reason"}, where)
        ref = _string(row["ref"], f"{where}.ref")
        if ref not in ref_to_assembly:
            raise V2Error(f"{where}.ref: unknown connector receipt ref {ref}")
        if ref in non_enclosure_refs:
            raise V2Error(
                "config.interface_assemblies.non_enclosure_refs: duplicate "
                f"connector ref {ref}")
        disposition = _enum(
            row["disposition"], {"no_enclosure_interface"},
            f"{where}.disposition")
        reason = _string(row["reason"], f"{where}.reason")
        non_enclosure_refs[ref] = {
            "ref": ref, "disposition": disposition, "reason": reason,
        }

    group_state_bindings: dict[str, dict[str, Any]] = {}
    if not isinstance(top["group_state_bindings"], list):
        raise V2Error(
            "config.interface_assemblies.group_state_bindings: expected list")
    for index, raw in enumerate(top["group_state_bindings"]):
        where = f"config.interface_assemblies.group_state_bindings[{index}]"
        row = _exact(raw, {"group_id", "enclosure_state_ids"}, where)
        group_id = _identifier(row["group_id"], f"{where}.group_id")
        if group_id in group_state_bindings:
            raise V2Error(
                "config.interface_assemblies.group_state_bindings: duplicate "
                f"group {group_id}")
        if group_id not in group_members:
            raise V2Error(f"{where}.group_id: unknown connector group {group_id}")
        enclosure_states = set(_unique_ids(
            row["enclosure_state_ids"], f"{where}.enclosure_state_ids"))
        unknown_states = enclosure_states - set(states)
        if unknown_states:
            raise V2Error(
                f"{where}.enclosure_state_ids: unknown states "
                f"{sorted(unknown_states)}")
        group_state_bindings[group_id] = {
            "group_id": group_id,
            "connector_required_state": group_required_states[group_id],
            "enclosure_state_ids": sorted(enclosure_states),
        }

    interface_map = {row["id"]: row for row in interfaces}
    required = {ident for ident, row in interface_map.items()
                if row["disposition"] in SERVICE_INTERFACE_DISPOSITIONS}
    _row_ids(top["mappings"], "config.interface_assemblies.mappings",
             allow_empty=True)
    result: dict[str, Any] = {}
    covered: set[str] = set()
    group_signatures: dict[str, dict[str, Any]] = {}
    covered_refs: set[str] = set()
    for index, raw in enumerate(top["mappings"]):
        where = f"config.interface_assemblies.mappings[{index}]"
        row = _exact(raw, {
            "id", "assembly_id", "interface_ids", "scope",
            "mated_in_states", "mated_during_operations",
        }, where)
        ident = _identifier(row["id"], f"{where}.id")
        assembly_id = _identifier(row["assembly_id"],
                                  f"{where}.assembly_id")
        if assembly_id not in assemblies:
            raise V2Error(
                f"{where}.assembly_id: unknown shared assembly {assembly_id}")
        interface_ids = set(_unique_ids(
            row["interface_ids"], f"{where}.interface_ids"))
        unknown_interfaces = interface_ids - required
        if unknown_interfaces:
            raise V2Error(
                f"{where}.interface_ids: not connector/service openings "
                f"{sorted(unknown_interfaces)}")
        duplicates = covered & interface_ids
        if duplicates:
            raise V2Error(
                "config.interface_assemblies.mappings: duplicate opening "
                f"coverage {sorted(duplicates)}")
        scope = _identifier(row["scope"], f"{where}.scope")
        if scope not in scopes:
            raise V2Error(f"{where}.scope: unknown scope {scope}")
        if not scopes[scope]["required"]:
            raise V2Error(
                f"{where}.scope: connector assembly scopes must be required")
        mated_states = set(_unique_ids(
            row["mated_in_states"], f"{where}.mated_in_states"))
        unknown_states = mated_states - set(states)
        if unknown_states:
            raise V2Error(
                f"{where}.mated_in_states: unknown states "
                f"{sorted(unknown_states)}")
        mated_operations = set(_unique_ids(
            row["mated_during_operations"],
            f"{where}.mated_during_operations", allow_empty=True))
        unknown_operations = mated_operations - set(operations)
        if unknown_operations:
            raise V2Error(
                f"{where}.mated_during_operations: unknown operations "
                f"{sorted(unknown_operations)}")
        for operation_id in mated_operations:
            operation = operations[operation_id]
            endpoints = {operation["from_state"], operation["to_state"]}
            if not endpoints.issubset(mated_states):
                raise V2Error(
                    f"{where}.mated_during_operations: {operation_id} must "
                    "remain mated in both endpoint states")
            if operation["cable_condition"] != "pre_attached" or \
                    operation["threading_permitted"] or \
                    operation["disconnecting_permitted"]:
                raise V2Error(
                    f"{where}.mated_during_operations: {operation_id} requires "
                    "pre_attached, no-threading, no-disconnect service")

        mapping_refs: set[str] = set()
        mapping_groups: set[str] = set()
        for interface_id in interface_ids:
            interface = interface_map[interface_id]
            ref = _string(interface["ref"],
                          f"config cad interface {interface_id}.ref")
            if ref_to_assembly.get(ref) != assembly_id:
                raise V2Error(
                    f"{where}: interface {interface_id} ref {ref} is not an "
                    f"instance of shared assembly {assembly_id}")
            side = _string(interface["side"],
                           f"config cad interface {interface_id}.side")
            expected_axis = INTERFACE_SIDE_AXES.get(side)
            if expected_axis is None:
                raise V2Error(
                    f"{where}: interface {interface_id} has unsupported service "
                    f"side {side!r}")
            axis_error = math.sqrt(sum(
                (actual - expected) ** 2
                for actual, expected in zip(ref_axes[ref], expected_axis)))
            if axis_error > 1e-6:
                raise V2Error(
                    f"{where}: interface {interface_id} ref {ref} mating axis "
                    f"contradicts enclosure side {side}")
            mapping_refs.add(ref)
            mapping_groups.update(ref_groups[ref])
        covered_refs.update(mapping_refs)
        signature = {
            "scope": scope,
            "mated_in_states": frozenset(mated_states),
            "mated_during_operations": frozenset(mated_operations),
        }
        for group_id in mapping_groups:
            if group_id not in group_members:
                raise V2Error(
                    f"{where}: instance names undeclared simultaneous group "
                    f"{group_id}")
            previous = group_signatures.get(group_id)
            if previous is None:
                group_signatures[group_id] = signature
            elif previous != signature:
                raise V2Error(
                    f"{where}: simultaneous group {group_id} members must "
                    "share scope, states, and operations")
        covered.update(interface_ids)
        result[ident] = dict(row)

    if covered != required:
        raise V2Error(
            "config.interface_assemblies.mappings: coverage must equal every "
            f"connector/service opening; missing={sorted(required - covered)}, "
            f"extra={sorted(covered - required)}")
    duplicate_accounting = covered_refs & set(non_enclosure_refs)
    if duplicate_accounting:
        raise V2Error(
            "config.interface_assemblies: connector refs cannot be both "
            "mapped and dispositioned as having no enclosure interface; "
            f"duplicates={sorted(duplicate_accounting)}")
    touched_groups: set[str] = set()
    for group_id, serviceable in group_serviceable.items():
        touched = group_members[group_id] & covered_refs
        if not touched:
            continue
        touched_groups.add(group_id)
        if not group_members[group_id].issubset(covered_refs):
            raise V2Error(
                f"config.interface_assemblies: simultaneous group {group_id} "
                "omits a populated member from enclosure association")
        if not serviceable.issubset(covered_refs):  # defensive subset detail
            raise V2Error(
                f"config.interface_assemblies: simultaneous group {group_id} "
                "omits a required serviceable member")
    accounted_refs = covered_refs | set(non_enclosure_refs)
    receipt_refs = set(ref_to_assembly)
    if accounted_refs != receipt_refs:
        raise V2Error(
            "config.interface_assemblies: mapped refs plus explicit "
            "non_enclosure_refs must equal every connector receipt instance; "
            f"missing={sorted(receipt_refs - accounted_refs)}, "
            f"extra={sorted(accounted_refs - receipt_refs)}")
    if set(group_state_bindings) != touched_groups:
        raise V2Error(
            "config.interface_assemblies.group_state_bindings: coverage must "
            f"equal every mapped simultaneous group; missing="
            f"{sorted(touched_groups - set(group_state_bindings))}, extra="
            f"{sorted(set(group_state_bindings) - touched_groups)}")
    for group_id, binding_row in group_state_bindings.items():
        signature_states = group_signatures[group_id]["mated_in_states"]
        bound_states = set(binding_row["enclosure_state_ids"])
        if not bound_states.issubset(signature_states):
            raise V2Error(
                "config.interface_assemblies.group_state_bindings: group "
                f"{group_id} binds an enclosure state in which its mappings "
                "are not all declared mated")
    return {
        "receipt": receipt,
        "receipt_binding": binding,
        "input_bindings": input_bindings,
        "mappings": result,
        "non_enclosure_refs": non_enclosure_refs,
        "group_state_bindings": group_state_bindings,
    }


def _physical_type(value: Any, where: str) -> str:
    result = _string(value, where)
    if result not in BUILTIN_PHYSICAL_TYPES and not CUSTOM_TEST_RE.fullmatch(result):
        raise V2Error(
            f"{where}: expected a built-in type or namespaced custom.<owner>.<test>")
    return result


def _validate_physical_specs(rows: Any, scopes: Mapping[str, Any],
                             parts: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    _row_ids(rows, "config.physical_tests")
    result: dict[str, Mapping[str, Any]] = {}
    for index, raw in enumerate(rows):
        where = f"config.physical_tests[{index}]"
        row = _exact(raw, {"id", "type", "scope", "required_for", "subject_parts"},
                     where)
        ident = _identifier(row["id"], f"{where}.id")
        _physical_type(row["type"], f"{where}.type")
        scope = _identifier(row["scope"], f"{where}.scope")
        if scope not in scopes:
            raise V2Error(f"{where}.scope: unknown scope {scope}")
        _enum(row["required_for"], {"PRINT_VERIFIED", "THERMALLY_VERIFIED"},
              f"{where}.required_for")
        subject_parts = set(_unique_ids(row["subject_parts"],
                                        f"{where}.subject_parts"))
        missing = subject_parts - set(parts)
        if missing:
            raise V2Error(f"{where}.subject_parts: unknown parts {sorted(missing)}")
        result[ident] = row
    return result


def _enforce_physical_obligations(specs: Mapping[str, Mapping[str, Any]],
                                  policy: Mapping[str, Any],
                                  parts: Mapping[str, Any],
                                  cabled: Mapping[str, Any],
                                  service_envelopes: Mapping[str, Any],
                                  interface_assemblies: Mapping[str, Any]) -> None:
    """Ensure service and prewired claims acquire physical acceptance tests."""
    by_type: dict[str, list[Mapping[str, Any]]] = {}
    for row in specs.values():
        by_type.setdefault(row["type"], []).append(row)

    def require(test_type: str, subject_parts: set[str]) -> None:
        candidates = [row for row in by_type.get(test_type, [])
                      if row["required_for"] == "PRINT_VERIFIED" and
                      subject_parts.issubset(set(row["subject_parts"]))]
        if not candidates:
            raise V2Error(
                "config.physical_tests: represented service/assembly intent "
                f"requires PRINT_VERIFIED test {test_type} covering "
                f"{sorted(subject_parts)}")

    def require_scope(test_type: str, scope: str) -> None:
        candidates = [row for row in by_type.get(test_type, [])
                      if row["required_for"] == "PRINT_VERIFIED" and
                      row["scope"] == scope]
        if not candidates:
            raise V2Error(
                "config.physical_tests: connector service-envelope intent "
                f"requires PRINT_VERIFIED test {test_type} in scope {scope}")

    pcb = next(ident for ident, row in parts.items() if row["role"] == "pcb")
    base = next(ident for ident, row in parts.items() if row["role"] == "base")
    lid = next(ident for ident, row in parts.items() if row["role"] == "lid")
    if policy["pcb_retained_with_lid_removed"]:
        require("lid_off_pcb_retention", {base, pcb})
        require("case_closure_independence", {base, lid, pcb})
    for part, constraint in cabled.items():
        if constraint["cable_pre_attached"] and not constraint["threading_permitted"]:
            require("accessory_insertion_removal", {part})
            require("accessory_retention_rattle", {part})
            require("cable_strain_clearance", {part})
    for row in service_envelopes.values():
        require_scope("all_interfaces_mated", row["scope"])
        require_scope("cable_strain_clearance", row["scope"])
    for row in interface_assemblies.get("mappings", {}).values():
        require_scope("all_interfaces_mated", row["scope"])
        require_scope("cable_strain_clearance", row["scope"])


def _validate_manufacturing_audit(
        value: Any, root: Path, cad_design_path: Path,
        cad_design: Mapping[str, Any], scopes: Mapping[str, Any],
        physical_tests: Mapping[str, Mapping[str, Any]], *,
        release_fdm_compiler: Any = None,
        release_fdm_helper: Any = None,
        release_collision_builder: Any = None,
        release_step_inspector: Any = None,
        release_process_runner: Any = None,
        release_pipeline_runtime: Any = None,
        release_collision_subject_validator: Any = None,
        ) -> dict[str, Any] | None:
    """Regrade one exact FDM receipt and bind its scope/test semantics."""
    if value is None:
        return None
    top = _exact(value, {
        "contract", "receipt", "generation", "collision",
        "collision_subject", "meshes",
    },
                 "config.manufacturing_audit")
    contract_binding = validate_file_binding(
        top["contract"], root, "config.manufacturing_audit.contract")
    receipt, receipt_binding = _load_bound_json_bytes(
        top["receipt"], root, "config.manufacturing_audit.receipt")
    generation, generation_binding = _load_bound_json_bytes(
        top["generation"], root, "config.manufacturing_audit.generation")
    collision, collision_binding = _load_bound_json_bytes(
        top["collision"], root, "config.manufacturing_audit.collision")
    collision_builder_expected = _mapping(
        collision.get("builder"), "manufacturing collision receipt.builder")
    collision_helper_expected = _mapping(
        collision.get("enclosure_common"),
        "manufacturing collision receipt.enclosure_common")
    collision_inspector_expected = _mapping(
        collision.get("step_inspector"),
        "manufacturing collision receipt.step_inspector")
    collision_process_expected = _mapping(
        collision.get("process_runner"),
        "manufacturing collision receipt.process_runner")
    collision_pipeline_expected = _mapping(
        collision.get("pipeline_runtime"),
        "manufacturing collision receipt.pipeline_runtime")
    collision_release_root = root if release_collision_builder is not None else None
    collision_authorities = _collision_builder_authority(
            collision_builder_expected, collision_helper_expected,
            collision_inspector_expected, collision_process_expected,
            collision_pipeline_expected,
            release_root=collision_release_root,
            release_binding=release_collision_builder,
            release_helper_binding=(
                release_fdm_helper if collision_release_root is not None
                else None),
            release_inspector_binding=release_step_inspector,
            release_process_runner_binding=release_process_runner,
            release_pipeline_runtime_binding=release_pipeline_runtime)
    collision_builder_loaded = collision_authorities["builder"]
    collision_helper_loaded = collision_authorities["enclosure_common"]
    collision_runner = _COLLISION_PROCESS_RUNNER or _run_collision_process
    try:
        collision_runner([
            "/usr/bin/python3", "-B", str(collision_builder_loaded["path"]),
            "--replay-receipt", str(collision_binding["path"]),
        ], cwd=collision_binding["path"].parent)
    except (OSError, V1EnclosureError) as exc:
        raise V2Error(f"manufacturing collision replay failed: {exc}") from exc
    replayed_collision, _ = _load_bound_json_bytes(
        top["collision"], root, "config.manufacturing_audit.collision")
    if replayed_collision != collision:
        raise V2Error(
            "manufacturing collision differs from exact builder replay")
    if generation.get("schema") != 1 or generation.get("kind") != \
            "pcb-enclosure-generation-v1":
        raise V2Error("manufacturing generation receipt has wrong schema/kind")
    installed_case = generation.get("installed_case")
    if not isinstance(installed_case, Mapping):
        raise V2Error(
            "manufacturing generation receipt lacks installed_case evidence")
    if collision.get("schema") != 1 or collision.get("kind") != \
            "pcb-enclosure-collision-v1":
        raise V2Error("manufacturing collision receipt has wrong schema/kind")
    if collision.get("status") != "COMPLETE":
        raise V2Error("manufacturing collision receipt must be COMPLETE")
    collision_inputs = _mapping(
        collision.get("inputs"), "manufacturing collision receipt.inputs")
    collision_interface = _exact(
        collision_inputs.get("interface"), {"path", "sha256", "size"},
        "manufacturing collision receipt.inputs.interface")
    cad_interface = _mapping(
        cad_design.get("subject", {}).get("interface"),
        "schema-v1 CAD subject.interface")
    if (collision_interface["sha256"], collision_interface["size"]) != \
            (cad_interface.get("sha256"), cad_interface.get("size")):
        raise V2Error(
            "manufacturing collision interface identity differs from the "
            "audited schema-v1 CAD subject interface")
    collision_step = _exact(
        collision_inputs.get("step"), {"path", "sha256", "size"},
        "manufacturing collision receipt.inputs.step")
    cad_step = _mapping(
        cad_design.get("subject", {}).get("step"),
        "schema-v1 CAD subject.step")
    collision_subject_raw = _mapping(
        top["collision_subject"], "config.manufacturing_audit.collision_subject")
    collision_subject_mode = collision_subject_raw.get("mode")
    collision_subject_bindings: dict[str, Any] = {}
    if collision_subject_mode == "subject_step":
        _exact(collision_subject_raw, {"mode"},
               "config.manufacturing_audit.collision_subject")
        if (collision_step["sha256"], collision_step["size"]) != \
                (cad_step.get("sha256"), cad_step.get("size")):
            raise V2Error(
                "subject_step collision STEP differs from audited CAD subject")
    elif collision_subject_mode == "external_composition":
        external_subject = _exact(collision_subject_raw, {
            "mode", "receipt", "parent_step", "interface",
            "supplement_step", "augmentation_receipt", "validator",
        }, "config.manufacturing_audit.collision_subject")
        for field in ("receipt", "parent_step", "interface",
                      "supplement_step", "augmentation_receipt", "validator"):
            collision_subject_bindings[field] = validate_file_binding(
                external_subject[field], root,
                f"config.manufacturing_audit.collision_subject.{field}")
        for field, cad_record in (("parent_step", cad_step),
                                  ("interface", cad_interface)):
            binding = collision_subject_bindings[field]
            if (binding["sha256"], binding["size"]) != \
                    (cad_record.get("sha256"), cad_record.get("size")):
                raise V2Error(
                    f"external collision {field} differs from audited CAD subject")
        if (collision_subject_bindings["interface"]["sha256"],
                collision_subject_bindings["interface"]["size"]) != \
                (collision_interface["sha256"], collision_interface["size"]):
            raise V2Error(
                "external collision interface differs from collision receipt")
        if (collision_subject_bindings["parent_step"]["sha256"],
                collision_subject_bindings["parent_step"]["size"]) == \
                (collision_step["sha256"], collision_step["size"]) or \
                (collision_subject_bindings["supplement_step"]["sha256"],
                 collision_subject_bindings["supplement_step"]["size"]) == \
                (collision_step["sha256"], collision_step["size"]):
            raise V2Error(
                "external composition output must differ from each input STEP")
        composition_receipt = load_json(
            collision_subject_bindings["receipt"]["path"])

        def has_binding(value: Any) -> bool:
            if isinstance(value, Mapping):
                if set(value) >= {"sha256", "size"} and \
                        (value.get("sha256"), value.get("size")) == \
                        (collision_step["sha256"], collision_step["size"]):
                    return True
                return any(has_binding(item) for item in value.values())
            if isinstance(value, list):
                return any(has_binding(item) for item in value)
            return False

        if not has_binding(composition_receipt):
            raise V2Error(
                "external composition receipt does not bind collision STEP")
        validator_loaded = collision_subject_bindings["validator"]
        if release_collision_subject_validator is not None:
            release_validator = _exact(
                release_collision_subject_validator,
                {"path", "sha256", "size"},
                "release external collision validator")
            if release_validator["path"] != \
                    "tooling/compose_obstruction_step.py" or \
                    (release_validator["sha256"], release_validator["size"]) != \
                    (validator_loaded["sha256"], validator_loaded["size"]):
                raise V2Error(
                    "release obstruction_compositor differs from config validator")
            validator_loaded = validate_file_binding(
                release_validator, root,
                "release external collision validator")
        elif release_collision_builder is not None:
            raise V2Error(
                "release external composition requires obstruction_compositor")
        try:
            collision_runner([
                "/usr/bin/python3", "-B", str(validator_loaded["path"]),
                "--replay-receipt",
                str(collision_subject_bindings["receipt"]["path"]),
            ], cwd=collision_subject_bindings["receipt"]["path"].parent)
        except (OSError, V1EnclosureError) as exc:
            raise V2Error(
                f"external collision composition replay failed: {exc}") from exc
    else:
        raise V2Error(
            "config.manufacturing_audit.collision_subject.mode: expected "
            "subject_step|external_composition")
    collision_generation = _exact(
        collision_inputs.get("generation"), {"path", "sha256", "size"},
        "manufacturing collision receipt.inputs.generation")
    expected_local_generation = {
        "path": generation_binding["path"].name,
        "sha256": generation_binding["sha256"],
        "size": generation_binding["size"],
    }
    if dict(collision_generation) != expected_local_generation:
        raise V2Error(
            "manufacturing collision receipt binds a different generation "
            "receipt")
    if collision_inputs.get("assembled_case_mesh") != installed_case:
        raise V2Error(
            "manufacturing collision assembled case differs from generation")
    collision_result = _mapping(
        collision.get("result"), "manufacturing collision receipt.result")
    volume = collision_result.get("exact_brep_volume_mm3")
    if collision_result.get("classification") != "EMPTY" or \
            isinstance(volume, bool) or not isinstance(volume, (int, float)) or \
            not math.isfinite(volume) or volume != 0:
        raise V2Error(
            "manufacturing collision receipt must prove EMPTY exact BRep "
            "intersection with zero volume")
    if not isinstance(top["meshes"], list) or not top["meshes"]:
        raise V2Error("config.manufacturing_audit.meshes: denominator is zero")
    mesh_bindings: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(top["meshes"]):
        where = f"config.manufacturing_audit.meshes[{index}]"
        row = _exact(raw, {"part", "path", "sha256", "size"}, where)
        part = _string(row["part"], f"{where}.part")
        if not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", part):
            raise V2Error(f"{where}.part: invalid printable selector")
        if part in mesh_bindings:
            raise V2Error("config.manufacturing_audit.meshes: duplicate part")
        mesh_bindings[part] = validate_file_binding(
            {key: row[key] for key in ("path", "sha256", "size")},
            root, where)
    printable_parts = set(cad_design["cad"]["printable_parts"])
    if set(mesh_bindings) != printable_parts:
        raise V2Error(
            "config.manufacturing_audit.meshes: census differs from CAD "
            f"printables; missing={sorted(printable_parts - set(mesh_bindings))}, "
            f"unknown={sorted(set(mesh_bindings) - printable_parts)}")
    if receipt.get("schema") != 1 or receipt.get("kind") != \
            "pcb-enclosure-fdm-structural-audit-v1":
        raise V2Error("manufacturing audit receipt has wrong schema/kind")
    inputs = _mapping(receipt.get("inputs"),
                      "manufacturing audit receipt.inputs")
    expected_compiler = _exact(
        inputs.get("compiler"), {"path", "sha256", "size"},
        "manufacturing audit receipt.inputs.compiler")
    expected_helper = _exact(
        inputs.get("enclosure_common"), {"path", "sha256", "size"},
        "manufacturing audit receipt.inputs.enclosure_common")
    release_root = root if release_fdm_compiler is not None or \
        release_fdm_helper is not None else None
    module, compiler_loaded, helper_loaded = _fdm_audit_compiler_module(
        expected_compiler, expected_helper, release_root=release_root,
        release_binding=release_fdm_compiler,
        release_helper_binding=release_fdm_helper)
    try:
        computed, contract = module.audit_paths_with_contract(
            contract_binding["path"], cad_design_path,
            generation_binding["path"],
            {part: binding["path"] for part, binding in mesh_bindings.items()},
            root=root, compiler_path=compiler_loaded["path"],
            helper_path=helper_loaded["path"])
    except Exception as exc:
        if isinstance(exc, V2Error):
            raise
        raise V2Error(f"manufacturing audit regrade failed: {exc}") from exc
    if computed != receipt:
        raise V2Error(
            "manufacturing audit receipt is stale or does not reproduce from "
            "the exact contract/generation/mesh/compiler inputs")
    status = receipt.get("status")
    if status not in {"FAIL", "INCOMPLETE", "CAD_READY"} or \
            receipt.get("maximum_claim") != "CAD_READY" or \
            receipt.get("physical_evidence_consumed") is not False:
        raise V2Error("manufacturing audit receipt has invalid claim boundary")
    if status == "FAIL":
        raise V2Error("manufacturing audit records FAIL")

    for attachment_id, attachment in contract["attachments"].items():
        scope = attachment["scope"]
        if scope not in scopes:
            raise V2Error(
                f"manufacturing attachment {attachment_id}: unknown v2 scope {scope}")
        if not scopes[scope]["required"]:
            raise V2Error(
                f"manufacturing attachment {attachment_id}: scope {scope} "
                "must be required")
        exception_id = attachment["exception_id"]
        if exception_id is None:
            continue
        flexure = contract["flexure_exceptions"][exception_id]
        test_id = flexure["physical_test_id"]
        test = physical_tests.get(test_id)
        if test is None:
            raise V2Error(
                f"manufacturing flexure {exception_id}: physical test "
                f"{test_id} is absent")
        if test["scope"] != scope or test["required_for"] != "PRINT_VERIFIED":
            raise V2Error(
                f"manufacturing flexure {exception_id}: physical test must be "
                f"PRINT_VERIFIED in scope {scope}")

    # Reopen every declared binding after computation so a transient edit
    # cannot be hidden by restoring only the receipt bytes.
    validate_file_binding(top["contract"], root,
                          "config.manufacturing_audit.contract")
    _load_bound_json_bytes(top["receipt"], root,
                           "config.manufacturing_audit.receipt")
    _load_bound_json_bytes(top["generation"], root,
                           "config.manufacturing_audit.generation")
    _load_bound_json_bytes(top["collision"], root,
                           "config.manufacturing_audit.collision")
    try:
        collision_runner([
            "/usr/bin/python3", "-B", str(collision_builder_loaded["path"]),
            "--validate-receipt", str(collision_binding["path"]),
        ], cwd=collision_binding["path"].parent)
    except (OSError, V1EnclosureError) as exc:
        raise V2Error(
            f"manufacturing collision post-regrade reopen failed: {exc}") \
            from exc
    reopened_collision, _ = _load_bound_json_bytes(
        top["collision"], root, "config.manufacturing_audit.collision")
    if reopened_collision != collision:
        raise V2Error("manufacturing collision changed after regrade")
    if collision_subject_mode == "external_composition":
        for field in ("receipt", "parent_step", "interface",
                      "supplement_step", "augmentation_receipt", "validator"):
            validate_file_binding(
                collision_subject_raw[field], root,
                f"config.manufacturing_audit.collision_subject.{field}")
    for index, raw in enumerate(top["meshes"]):
        validate_file_binding(
            {key: raw[key] for key in ("path", "sha256", "size")}, root,
            f"config.manufacturing_audit.meshes[{index}]")
    return {
        "status": status, "receipt": receipt, "contract": contract,
        "collision": collision,
        "bindings": {
            "contract": contract_binding, "receipt": receipt_binding,
            "generation": generation_binding, "collision": collision_binding,
            "meshes": mesh_bindings,
            "collision_builder": collision_builder_loaded,
            "collision_enclosure_common": collision_helper_loaded,
            "collision_step_inspector": collision_authorities["step_inspector"],
            "collision_process_runner": collision_authorities["process_runner"],
            "collision_pipeline_runtime":
                collision_authorities["pipeline_runtime"],
            "collision_subject": collision_subject_bindings,
            "compiler": compiler_loaded, "enclosure_common": helper_loaded,
        },
    }


def _collect_hex64(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, Mapping):
        for item in value.values():
            found.update(_collect_hex64(item))
    elif isinstance(value, list):
        for item in value:
            found.update(_collect_hex64(item))
    elif isinstance(value, str) and HEX64_RE.fullmatch(value):
        found.add(value)
    return found


def _manifest_subjects(path: Path) -> dict[str, str]:
    """Read exact path/hash pairs from structured or legacy manifests.

    PCB releases predate schema v2 and may use an audited ``MANIFEST.txt``
    rather than YAML/JSON. A hash occurring under another path is not authority
    for the selected PCB or STEP.
    """
    try:
        text = read_stable_bytes(
            path, f"release manifest {path}").decode("utf-8")
    except (OSError, UnicodeError) as exc:
        raise V2Error(f"cannot read release manifest {path}: {exc}") from exc
    found: dict[str, str] = {}

    def add(raw_path: Any, raw_hash: Any) -> None:
        if not isinstance(raw_path, str) or not isinstance(raw_hash, str) or \
                not HEX64_RE.fullmatch(raw_hash):
            return
        candidate = Path(raw_path)
        if candidate.is_absolute() or "\\" in raw_path or any(
                part in {"", ".", ".."} for part in candidate.parts):
            return
        normalized = candidate.as_posix()
        previous = found.get(normalized)
        if previous is not None and previous != raw_hash:
            raise V2Error(
                f"release manifest contradicts itself for {normalized!r}")
        found[normalized] = raw_hash

    for line in text.splitlines():
        # Historical release streams use both a path-first census and the
        # standard ``sha256sum`` hash-first form.  Accept only the two exact,
        # whitespace-delimited shapes; in either case authority remains bound
        # to the selected relative path as well as the digest.
        path_first = re.match(r"^\s*(\S+)\s+([0-9a-f]{64})\s*$", line)
        if path_first:
            add(path_first.group(1), path_first.group(2))
            continue
        hash_first = re.match(r"^\s*([0-9a-f]{64})\s{2}(\S+)\s*$", line)
        if hash_first:
            add(hash_first.group(2), hash_first.group(1))
    try:
        structured = yaml.load(text, Loader=StrictLoader)
    except yaml.YAMLError:
        structured = None

    def walk(value: Any) -> None:
        if isinstance(value, Mapping):
            add(value.get("path", value.get("name")), value.get("sha256"))
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(structured)
    if not found:
        raise V2Error("release manifest contains no path-bound SHA-256 census")
    return found


def _v1_fastener_bridge(cad_design: Mapping[str, Any],
                        cad_loaded: Mapping[str, Any],
                        fasteners: Mapping[str, Mapping[str, Any]]) -> None:
    """Prove that schema-v2 independent screw roles exist in bound v1 CAD."""
    v1 = cad_design["fasteners"]
    if v1["strategy"] != "separate_perimeter":
        raise V2Error(
            "config.subject.cad_design: schema-v2 independent PCB retention "
            "requires v1 fasteners.strategy=separate_perimeter")
    by_role: dict[str, list[Mapping[str, Any]]] = {
        "board_retention": [], "case_closure": [], "accessory": []}
    for row in fasteners.values():
        by_role[row["role"]].append(row)
    if len(by_role["board_retention"]) != 1 or \
            len(by_role["case_closure"]) != 1:
        raise V2Error(
            "config.fastener_groups: bound v1 CAD requires exactly one "
            "board_retention and one case_closure group")

    interface = cad_loaded["interface"]
    positions: dict[str, list[list[float]]] = {}
    for row in interface["board"]["mounting_holes"]:
        positions.setdefault(row["ref"], []).append(row["position_mm"])
    expected_board: list[tuple[float, float]] = []
    for ref in v1["board_holes"]:
        matches = positions.get(ref, [])
        if len(matches) != 1:
            raise V2Error(
                f"config.subject.cad_design: board fastener ref {ref} is not unique")
        expected_board.append((float(matches[0][0]), float(matches[0][1])))
    expected_case = [(float(row[0]), float(row[1]))
                     for row in v1["case_holes_mm"]]

    def actual_xy(group: Mapping[str, Any], where: str) -> list[tuple[float, float]]:
        result = []
        for axis in group["axes"]:
            direction = _normalize(axis["direction"])
            if abs(direction[0]) > 1e-9 or abs(direction[1]) > 1e-9 or \
                    direction[2] < 1 - 1e-9:
                raise V2Error(f"{where}: v1 adapter screw axes must point +Z")
            result.append((float(axis["origin_mm"][0]),
                           float(axis["origin_mm"][1])))
        return result

    def same_points(actual: Sequence[tuple[float, float]],
                    expected: Sequence[tuple[float, float]]) -> bool:
        if len(actual) != len(expected):
            return False
        remaining = list(expected)
        for point in actual:
            matches = [index for index, candidate in enumerate(remaining)
                       if math.dist(point, candidate) <= 1e-6]
            if len(matches) != 1:
                return False
            remaining.pop(matches[0])
        return not remaining

    board_group = by_role["board_retention"][0]
    case_group = by_role["case_closure"][0]
    if not same_points(actual_xy(board_group, "board_retention group"),
                       expected_board):
        raise V2Error(
            "config.fastener_groups: board_retention axes differ from bound v1 CAD")
    if not same_points(actual_xy(case_group, "case_closure group"), expected_case):
        raise V2Error(
            "config.fastener_groups: case_closure axes differ from bound v1 CAD")
    expected_hardware = {
        "board_retention": {
            "thread": v1["thread"],
            "screw_length_mm": float(v1["screw"]["board_length_mm"]),
            "minimum_engagement_mm": float(
                v1["screw"]["minimum_engagement_mm"]),
            "minimum_tip_clearance_mm": float(
                v1["screw"]["minimum_tip_clearance_mm"]),
        },
        "case_closure": {
            "thread": v1["thread"],
            "screw_length_mm": float(v1["screw"]["lid_length_mm"]),
            "minimum_engagement_mm": float(
                v1["screw"]["minimum_engagement_mm"]),
            "minimum_tip_clearance_mm": float(
                v1["screw"]["minimum_tip_clearance_mm"]),
        },
    }
    for role, group in (("board_retention", board_group),
                        ("case_closure", case_group)):
        if group["hardware"] != expected_hardware[role]:
            raise V2Error(
                f"config.fastener_groups: {role} hardware differs from bound v1 CAD")


def _state_and_motion_cross_checks(intent: Mapping[str, Any],
                                   parts: Mapping[str, Any],
                                   fasteners: Mapping[str, Any],
                                   policy: Mapping[str, Any]) -> None:
    part_ids = set(parts)
    group_ids = set(fasteners)
    installed_part_ids = set(parts)
    pcb = next(ident for ident, row in parts.items() if row["role"] == "pcb")
    lid = next(ident for ident, row in parts.items() if row["role"] == "lid")
    board_groups = {ident for ident, row in fasteners.items()
                    if row["role"] == "board_retention"}
    closure_groups = {ident for ident, row in fasteners.items()
                      if row["role"] == "case_closure"}
    for state in intent["states"]:
        unknown_parts = set(state["present_parts"]) - part_ids
        unknown_groups = set(state["secured_fastener_groups"]) - group_ids
        if unknown_parts:
            raise V2Error(
                f"intent state {state['id']}: unknown parts {sorted(unknown_parts)}")
        if unknown_groups:
            raise V2Error(
                f"intent state {state['id']}: unknown fastener groups "
                f"{sorted(unknown_groups)}")
        if state["pcb_retained"] and pcb not in state["present_parts"]:
            raise V2Error(
                f"intent state {state['id']}: PCB cannot be retained when absent")
        if state["pcb_retained"] and not board_groups.issubset(
                state["secured_fastener_groups"]):
            raise V2Error(
                f"intent state {state['id']}: pcb_retained requires every "
                "board_retention group secured")
        if state["purpose"] == "installed":
            if set(state["present_parts"]) != installed_part_ids:
                raise V2Error(
                    "intent installed state must contain every installed part")
            if not closure_groups.issubset(state["secured_fastener_groups"]):
                raise V2Error(
                    "intent installed state lacks secured case_closure group(s)")
            if set(state["secured_fastener_groups"]) != group_ids:
                raise V2Error(
                    "intent installed state must secure every installed "
                    "fastener group")
        if state["purpose"] == "lid_removed":
            if lid in state["present_parts"]:
                raise V2Error("intent lid_removed state still contains the lid")
            if closure_groups & set(state["secured_fastener_groups"]):
                raise V2Error(
                    "intent lid_removed state still secures case_closure hardware")
            required = policy["pcb_retained_with_lid_removed"]
            if required and (not state["pcb_retained"] or
                             not board_groups.issubset(
                                 state["secured_fastener_groups"])):
                raise V2Error(
                    "intent lid_removed state does not retain the PCB with its "
                    "independent board_retention fasteners")

    for operation in intent["operations"]:
        missing = set(operation["moving_parts"]) - part_ids
        if missing:
            raise V2Error(
                f"intent operation {operation['id']}: unknown parts {sorted(missing)}")


def validate_config_v2(value: Mapping[str, Any], root: Path, *,
                       release_connector_compiler: Any = None,
                       release_fdm_compiler: Any = None,
                       release_fdm_helper: Any = None,
                       release_collision_builder: Any = None,
                       release_step_inspector: Any = None,
                       release_process_runner: Any = None,
                       release_pipeline_runtime: Any = None,
                       release_collision_subject_validator: Any = None,
                       ) -> dict[str, Any]:
    """Validate and cross-bind one complete schema-v2 configuration.

    ``release_connector_compiler`` is reserved for the immutable-release
    verifier.  When present, connector contract/evidence resolution moves to
    the fixed release-local virtual project root and the compiler is selected
    by its exact manifest binding.  Ordinary project validation leaves it
    unset and retains the canonical live compiler/project contract guard.
    """
    top = _exact_optional(value, {
        "schema", "kind", "name", "mode", "subject", "external_subjects",
        "verification_scopes", "installed_parts", "fastener_policy",
        "fastener_groups", "clearance_cases", "physical_tests",
    }, {"service_envelopes", "interface_assemblies", "manufacturing_audit"},
        "config")
    if top["schema"] != 2 or isinstance(top["schema"], bool):
        raise V2Error("config.schema: expected 2")
    if top["kind"] != CONFIG_KIND:
        raise V2Error(f"config.kind: expected {CONFIG_KIND!r}")
    name = _identifier(top["name"], "config.name")
    mode = _enum(top["mode"], {"co_design", "derived"}, "config.mode")

    subject = _exact(top["subject"], {
        "release", "release_manifest", "pcb", "step", "interface",
        "mechanical_intent", "cad_design",
    }, "config.subject")
    _string(subject["release"], "config.subject.release")
    bindings: dict[str, Any] = {}
    for field in ("pcb", "step", "interface", "mechanical_intent", "cad_design"):
        bindings[field] = validate_file_binding(
            subject[field], root, f"config.subject.{field}")
    if mode == "derived":
        if subject["release_manifest"] is None:
            raise V2Error(
                "config.subject.release_manifest: required for derived mode")
        bindings["release_manifest"] = validate_file_binding(
            subject["release_manifest"], root,
            "config.subject.release_manifest")
        try:
            manifest_subjects = _manifest_subjects(
                bindings["release_manifest"]["path"])
        except V2Error as exc:
            raise V2Error(
                f"config.subject.release_manifest: invalid manifest: {exc}") from exc
        manifest_root = bindings["release_manifest"]["path"].parent
        absent: list[str] = []
        for field in ("pcb", "step"):
            try:
                relative = bindings[field]["path"].relative_to(
                    manifest_root).as_posix()
            except ValueError:
                absent.append(field)
                continue
            if manifest_subjects.get(relative) != bindings[field]["sha256"]:
                absent.append(field)
        if absent:
            raise V2Error(
                "config.subject.release_manifest: does not bind configured "
                f"subject paths and hashes for {absent}")
    elif subject["release_manifest"] is not None:
        raise V2Error(
            "config.subject.release_manifest: co_design mode must use null")

    intent = validate_mechanical_intent(load_yaml(bindings["mechanical_intent"]["path"]))
    if intent["name"] != name:
        raise V2Error(
            "config.subject.mechanical_intent: intent.name differs from config.name")

    try:
        cad_design, cad_loaded = load_bound_config_v1(
            bindings["cad_design"]["path"], root)
    except V1EnclosureError as exc:
        raise V2Error(f"config.subject.cad_design: invalid bound v1 design: {exc}") \
            from exc
    if cad_design["name"] != name:
        raise V2Error(
            "config.subject.cad_design: v1 config.name differs from v2 config.name")
    if cad_design["mode"] != mode:
        raise V2Error(
            "config.subject.cad_design: v1/v2 modes differ")
    if cad_design["subject"]["release"] != subject["release"]:
        raise V2Error(
            "config.subject.cad_design: v1/v2 release identifiers differ")
    for field in ("release_manifest", "pcb", "step", "interface"):
        if cad_design["subject"].get(field) != subject[field]:
            raise V2Error(
                f"config.subject.cad_design: v1/v2 {field} bindings differ")

    external, external_bindings = _validate_external_subjects(
        top["external_subjects"], root)
    bindings["external_subjects"] = external_bindings
    scopes = _validate_scopes(top["verification_scopes"])
    parts = _validate_installed_parts(top["installed_parts"], scopes, external)
    policy = _exact(top["fastener_policy"], {
        "axis_disjoint_tolerance_mm", "pcb_retained_with_lid_removed",
    }, "config.fastener_policy")
    _number(policy["axis_disjoint_tolerance_mm"],
            "config.fastener_policy.axis_disjoint_tolerance_mm", positive=True)
    _boolean(policy["pcb_retained_with_lid_removed"],
             "config.fastener_policy.pcb_retained_with_lid_removed")
    if not policy["pcb_retained_with_lid_removed"]:
        raise V2Error(
            "config.fastener_policy.pcb_retained_with_lid_removed: schema v2 "
            "requires true")
    if policy["pcb_retained_with_lid_removed"] != \
            intent["requirements"]["pcb_retained_with_lid_removed"]:
        raise V2Error(
            "config/intent disagree on pcb_retained_with_lid_removed")
    fasteners = _validate_fasteners(top["fastener_groups"], policy, parts)
    _v1_fastener_bridge(cad_design, cad_loaded, fasteners)

    operation_map = {row["id"]: row for row in intent["operations"]}
    state_map = {row["id"]: row for row in intent["states"]}
    cabled = {row["part"]: row
              for row in intent["requirements"]["cabled_parts"]}
    clearances = _validate_clearance_cases(
        top["clearance_cases"], scopes, parts, operation_map, cabled, state_map)
    service_envelopes = _validate_service_envelopes(
        top.get("service_envelopes"), scopes, cad_design["interfaces"],
        operation_map, state_map, external)
    interface_assemblies = _validate_interface_assemblies(
        top.get("interface_assemblies"), root, scopes,
        cad_design["interfaces"], operation_map, state_map,
        release_compiler=release_connector_compiler)
    if service_envelopes and interface_assemblies:
        raise V2Error(
            "config: service_envelopes and interface_assemblies are mutually "
            "exclusive; shared profiles may not be restated inline")
    if interface_assemblies:
        bindings["connector_assembly_receipt"] = \
            interface_assemblies["receipt_binding"]
        bindings["connector_assembly_inputs"] = \
            interface_assemblies["input_bindings"]
    physical = _validate_physical_specs(top["physical_tests"], scopes, parts)
    _enforce_physical_obligations(
        physical, policy, parts, cabled, service_envelopes,
        interface_assemblies)
    manufacturing_audit = _validate_manufacturing_audit(
        top.get("manufacturing_audit"), root, bindings["cad_design"]["path"],
        cad_design, scopes, physical,
        release_fdm_compiler=release_fdm_compiler,
        release_fdm_helper=release_fdm_helper,
        release_collision_builder=release_collision_builder,
        release_step_inspector=release_step_inspector,
        release_process_runner=release_process_runner,
        release_pipeline_runtime=release_pipeline_runtime,
        release_collision_subject_validator=
            release_collision_subject_validator)
    if manufacturing_audit:
        bindings["manufacturing_audit"] = manufacturing_audit["bindings"]
    _state_and_motion_cross_checks(intent, parts, fasteners, policy)

    for unknown in intent["unknowns"]:
        if unknown["scope"] not in scopes:
            raise V2Error(
                f"intent unknown {unknown['id']}: scope {unknown['scope']} absent")
    for cabled_part in cabled:
        if cabled_part not in parts:
            raise V2Error(
                f"intent cabled part {cabled_part}: absent from installed parts")

    service_declared = "service_envelopes" in top or \
        "interface_assemblies" in top
    has_edge_openings = any(
        row["disposition"] in SERVICE_INTERFACE_DISPOSITIONS
        for row in cad_design["interfaces"])
    ceilings = scope_readiness_ceilings(
        scopes, parts, external, intent["unknowns"], service_envelopes,
        interface_assemblies=interface_assemblies,
        service_envelopes_declared=service_declared,
        edge_openings_present=has_edge_openings,
        manufacturing_audit=manufacturing_audit,
        manufacturing_audit_declared="manufacturing_audit" in top)
    return {
        "config": dict(value),
        "intent": intent,
        "cad_design": cad_design,
        "cad_design_loaded": cad_loaded,
        "bindings": bindings,
        "scopes": scopes,
        "parts": parts,
        "fastener_groups": fasteners,
        "clearance_cases": clearances,
        "service_envelopes": service_envelopes,
        "interface_assemblies": interface_assemblies,
        "manufacturing_audit": manufacturing_audit,
        "physical_tests": physical,
        "scope_readiness_ceilings": ceilings,
    }


def scope_readiness_ceilings(scopes: Mapping[str, Any],
                             parts: Mapping[str, Any],
                             external: Mapping[str, Any],
                             unknowns: Sequence[Mapping[str, Any]],
                             service_envelopes: Mapping[str, Any] | None = None,
                             interface_assemblies: Mapping[str, Any] | None = None,
                             *, service_envelopes_declared: bool = True,
                             edge_openings_present: bool = False,
                             manufacturing_audit: Mapping[str, Any] | None = None,
                             manufacturing_audit_declared: bool = True,
                             ) -> dict[str, str]:
    """Return conservative per-scope ceilings imposed by authority/unknowns."""
    ceilings = {ident: "THERMALLY_VERIFIED" for ident in scopes}

    def lower(scope: str, status: str) -> None:
        current = ceilings[scope]
        if status == "INCOMPLETE" or (
                current != "INCOMPLETE" and
                READINESS_RANK[status] < READINESS_RANK[current]):
            ceilings[scope] = status

    for part in parts.values():
        source = part["source"]
        if source["kind"] != "external_subject":
            continue
        grade = external[source["id"]]["authority"]["grade"]
        ceiling = {
            "vendor_authoritative": "THERMALLY_VERIFIED",
            "measured_unit": "THERMALLY_VERIFIED",
            "derived_measurement": "CAD_READY",
            "conservative_candidate": "CAD_READY",
            "first_article_observation": "INCOMPLETE",
            "inspiration_only": "INCOMPLETE",
        }[grade]
        for scope in part["scopes"]:
            lower(scope, ceiling)
    for unknown in unknowns:
        blocker = unknown["blocks_readiness"]
        ceiling = {
            "CAD_READY": "INCOMPLETE",
            "PRINT_VERIFIED": "CAD_READY",
            "THERMALLY_VERIFIED": "PRINT_VERIFIED",
        }[blocker]
        lower(unknown["scope"], ceiling)
    # The additive service checklist intentionally has no external-geometry or
    # sweep-receipt binding yet.  Even a numerically complete conservative row
    # therefore remains an INCOMPLETE scope until IMP-242 lands that authority.
    for service in (service_envelopes or {}).values():
        lower(service["scope"], "INCOMPLETE")
    # Shared connector receipts close the duplicated-dimension and PCB-service
    # contract gaps. The current enclosure v2 tool still does not execute their
    # full plug/tool/cable solids against generated enclosure geometry, so each
    # mapped scope remains INCOMPLETE until a governing service verifier lands.
    for mapping in (interface_assemblies or {}).get("mappings", {}).values():
        lower(mapping["scope"], "INCOMPLETE")
    # Structural backward compatibility keeps older v2 configs valid, but an
    # omitted checklist may not preserve readiness for a serviced opening.
    # Every scope in the authoritative required closure is capped until the
    # service census is authored explicitly.
    if not service_envelopes_declared and edge_openings_present:
        for scope in required_scope_closure(scopes):
            lower(scope, "INCOMPLETE")
    # Structural backward compatibility validates legacy v2 configurations,
    # but does not retroactively certify them under the current FDM policy.
    # A present audit with missing slicer/toolpath evidence is likewise an
    # honest INCOMPLETE ceiling, never an inferred printability pass.
    if not manufacturing_audit_declared or manufacturing_audit is None or \
            manufacturing_audit["status"] == "INCOMPLETE":
        for scope in required_scope_closure(scopes):
            lower(scope, "INCOMPLETE")
    return ceilings


def aggregate_status(scope_statuses: Mapping[str, str],
                     required_scopes: Iterable[str],
                     *, ceilings: Mapping[str, str] | None = None) -> str:
    """Conservatively aggregate required scopes; FAIL and unknowns dominate."""
    required = list(required_scopes)
    if len(required) != len(set(required)):
        raise V2Error("required_scopes: duplicate scope")
    if not required:
        raise V2Error("required_scopes: denominator is zero")
    unknown_rows = set(scope_statuses) - set(required)
    if unknown_rows:
        raise V2Error(f"scope_statuses: undeclared scopes {sorted(unknown_rows)}")
    for scope, status in scope_statuses.items():
        if status not in RESULT_STATUSES:
            raise V2Error(f"scope {scope}: invalid status {status!r}")
    if ceilings is not None:
        unknown_ceilings = set(ceilings) - set(required)
        if unknown_ceilings:
            raise V2Error(
                f"ceilings: undeclared scopes {sorted(unknown_ceilings)}")
        for scope, ceiling in ceilings.items():
            if ceiling not in READINESS:
                raise V2Error(f"scope {scope}: invalid ceiling {ceiling!r}")
    missing = set(required) - set(scope_statuses)
    if missing:
        return "INCOMPLETE"
    statuses = []
    for scope in required:
        status = scope_statuses[scope]
        if status == "FAIL":
            return "FAIL"
        ceiling = ceilings.get(scope) if ceilings is not None else None
        if ceiling is not None:
            if ceiling == "INCOMPLETE":
                status = "INCOMPLETE"
            elif status != "INCOMPLETE" and \
                    READINESS_RANK[status] > READINESS_RANK[ceiling]:
                status = ceiling
        statuses.append(status)
    if "INCOMPLETE" in statuses:
        return "INCOMPLETE"
    return min(statuses, key=lambda status: READINESS_RANK[status])


def required_scope_closure(scopes: Mapping[str, Mapping[str, Any]]) -> list[str]:
    """Return required scopes plus every transitive dependency."""
    required = {ident for ident, row in scopes.items() if row["required"]}
    pending = list(required)
    while pending:
        ident = pending.pop()
        for dependency in scopes[ident]["depends_on"]:
            if dependency not in required:
                required.add(dependency)
                pending.append(dependency)
    return [ident for ident in scopes if ident in required]


def validate_physical_evidence_v2(value: Mapping[str, Any],
                                  loaded: Mapping[str, Any]) -> dict[str, Any]:
    """Validate an exact, extensible v2 physical-test census."""
    top = _exact(value, {"schema", "kind", "config_semantic_sha256", "tests"},
                 "physical_evidence")
    if top["schema"] != 2 or isinstance(top["schema"], bool):
        raise V2Error("physical_evidence.schema: expected 2")
    if top["kind"] != PHYSICAL_KIND:
        raise V2Error(f"physical_evidence.kind: expected {PHYSICAL_KIND!r}")
    digest = _string(top["config_semantic_sha256"],
                     "physical_evidence.config_semantic_sha256")
    if not HEX64_RE.fullmatch(digest):
        raise V2Error(
            "physical_evidence.config_semantic_sha256: expected lowercase 64-hex")
    expected_hash = semantic_sha256(loaded["config"])
    if digest != expected_hash:
        raise V2Error("physical evidence is stale for this v2 config")
    evidence_ids = _row_ids(top["tests"], "physical_evidence.tests")
    specs = loaded["physical_tests"]
    if evidence_ids != set(specs):
        raise V2Error(
            "physical_evidence.tests: census differs; "
            f"missing={sorted(set(specs) - evidence_ids)}, "
            f"unknown={sorted(evidence_ids - set(specs))}")
    normalized: dict[str, Any] = {}
    failed: list[str] = []
    pending: list[str] = []
    for index, raw in enumerate(top["tests"]):
        where = f"physical_evidence.tests[{index}]"
        row = _exact(raw, {"id", "type", "scope", "status", "evidence"}, where)
        ident = _identifier(row["id"], f"{where}.id")
        _physical_type(row["type"], f"{where}.type")
        _identifier(row["scope"], f"{where}.scope")
        status = _enum(row["status"], {"PASS", "FAIL", "NOT_RUN"},
                       f"{where}.status")
        evidence = _string(row["evidence"], f"{where}.evidence")
        spec = specs[ident]
        if row["type"] != spec["type"] or row["scope"] != spec["scope"]:
            raise V2Error(
                f"{where}: type/scope differs from config physical-test spec")
        if status == "FAIL":
            failed.append(ident)
        elif status == "NOT_RUN":
            pending.append(ident)
        normalized[ident] = {"status": status, "evidence": evidence,
                             "required_for": spec["required_for"]}
    if failed:
        status = "FAIL"
    else:
        print_rows = [ident for ident, spec in specs.items()
                      if spec["required_for"] == "PRINT_VERIFIED"]
        thermal_rows = [ident for ident, spec in specs.items()
                        if spec["required_for"] == "THERMALLY_VERIFIED"]
        print_ok = all(normalized[ident]["status"] == "PASS"
                       for ident in print_rows)
        thermal_ok = all(normalized[ident]["status"] == "PASS"
                         for ident in thermal_rows)
        if print_ok and thermal_ok and thermal_rows:
            status = "THERMALLY_VERIFIED"
        elif print_ok:
            status = "PRINT_VERIFIED"
        else:
            status = "INCOMPLETE"
    return {"status": status, "failed": failed, "pending": pending,
            "tests": normalized}


def _binding_for_report(binding: Any, root: Path) -> Any:
    """Normalize every reopened authority path relative to the declared root.

    Validation reports are copied into release workspaces. Absolute build or
    staging paths would make otherwise identical evidence location-dependent
    and, worse, can describe authorities other than the copied release bytes.
    """
    if isinstance(binding, Mapping):
        return {key: _binding_for_report(value, root)
                for key, value in binding.items()}
    if isinstance(binding, (list, tuple)):
        return [_binding_for_report(value, root) for value in binding]
    if isinstance(binding, Path):
        try:
            return binding.resolve(strict=True).relative_to(
                root.resolve(strict=True)).as_posix()
        except (OSError, ValueError):
            # Project validation selects exact repository-owned compilers
            # outside the project root. Represent those by their canonical
            # source identifiers, never by checkout-specific absolute paths.
            repository_root = Path(__file__).resolve().parents[3]
            canonical_sources = {
                CONNECTOR_COMPILER_SOURCE_PATH,
                FDM_AUDIT_COMPILER_SOURCE_PATH,
                COLLISION_BUILDER_SOURCE_PATH,
                STEP_INSPECTOR_SOURCE_PATH,
                PROCESS_RUNNER_SOURCE_PATH,
                PIPELINE_RUNTIME_SOURCE_PATH,
                "skills/pcb-enclosure/scripts/enclosure_common.py",
            }
            for relative in canonical_sources:
                candidate = repository_root / relative
                try:
                    if candidate.resolve(strict=True) == binding.resolve(strict=True):
                        return relative
                except OSError:
                    continue
            raise V2Error(
                "validation-report binding escapes the declared root and is "
                "not a canonical shared tool")
    return binding


def config_validation_report(
        raw: Mapping[str, Any], loaded: Mapping[str, Any], root: Path, *,
        validator_path: Path | None = None) -> dict[str, Any]:
    """Build the one canonical, relocation-stable config validation report."""
    validator_path = validator_path or Path(__file__)
    try:
        validator_payload = read_stable_bytes(
            validator_path, "schema-v2 validation compiler")
    except V1EnclosureError as exc:
        raise V2Error(str(exc)) from exc
    cad_design = _mapping(loaded.get("cad_design"), "loaded.cad_design")
    interfaces = cad_design.get("interfaces")
    if not isinstance(interfaces, list):
        raise V2Error("loaded.cad_design.interfaces: expected list")
    service_envelopes = _mapping(
        loaded.get("service_envelopes"), "loaded.service_envelopes")
    interface_assemblies = _mapping(
        loaded.get("interface_assemblies"), "loaded.interface_assemblies")
    mappings = _mapping(
        interface_assemblies.get("mappings", {}),
        "loaded.interface_assemblies.mappings")
    non_enclosure = _mapping(
        interface_assemblies.get("non_enclosure_refs", {}),
        "loaded.interface_assemblies.non_enclosure_refs")
    opening_count = sum(
        row["disposition"] in SERVICE_INTERFACE_DISPOSITIONS
        for row in interfaces)
    return {
        "schema": 2,
        "kind": VALIDATION_KIND,
        "status": "VALID",
        "binding_path_base": ".",
        "validator": {
            "path": V2_VALIDATOR_SOURCE_PATH,
            "sha256": hashlib.sha256(validator_payload).hexdigest(),
            "size": len(validator_payload),
        },
        "config_semantic_sha256": semantic_sha256(raw),
        "bindings": _binding_for_report(loaded["bindings"], root),
        "scope_readiness_ceilings": loaded["scope_readiness_ceilings"],
        "service_envelope_coverage": {
            "legacy_omitted": (
                "service_envelopes" not in raw and
                "interface_assemblies" not in raw),
            "legacy_readiness_capped": (
                "service_envelopes" not in raw and
                "interface_assemblies" not in raw and opening_count > 0),
            "declared": len(service_envelopes),
            "shared_mappings": len(mappings),
            "shared_non_enclosure_refs": len(non_enclosure),
            "shared_receipt_status": interface_assemblies.get(
                "receipt", {}).get("status"),
            "required_edge_openings": opening_count,
            "candidate_dimension_census_complete": sum(
                _service_envelope_candidate_dimensions_complete(row)
                for row in service_envelopes.values()),
        },
    }


def validate_config_validation_report(
        report: Mapping[str, Any], raw: Mapping[str, Any],
        loaded: Mapping[str, Any], root: Path, *,
        validator_path: Path | None = None) -> dict[str, Any]:
    """Require a carried report to equal an independently rebuilt report."""
    expected = config_validation_report(
        raw, loaded, root, validator_path=validator_path)
    if report != expected:
        raise V2Error(
            "v2 validation report differs from the canonical fresh regrade")
    return expected


def _write_or_print(value: Mapping[str, Any], output: Path | None,
                    *, inputs: Iterable[Path] = ()) -> None:
    payload = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if output is None:
        sys.stdout.write(payload)
    else:
        try:
            with atomic_output(output, where="schema-v2 report",
                               inputs=inputs) as (_, stream):
                stream.write(payload.encode("utf-8"))
        except V1EnclosureError as exc:
            raise V2Error(str(exc)) from exc


def _bound_input_paths(loaded: Mapping[str, Any]) -> list[Path]:
    """Collect every reopened file so reports cannot overwrite an authority."""
    result: list[Path] = []

    def walk(value: Any) -> None:
        if isinstance(value, Mapping):
            for child in value.values():
                walk(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                walk(child)
        elif isinstance(value, Path):
            result.append(value)

    walk(loaded.get("bindings", {}))
    return result


def _cli_validate_config(args: argparse.Namespace) -> int:
    raw = load_yaml(args.config)
    loaded = validate_config_v2(raw, args.root)
    report = config_validation_report(raw, loaded, args.root)
    _write_or_print(
        report, args.output,
        inputs=[args.config, *_bound_input_paths(loaded)])
    return 0


def mechanical_intent_validation_report(
        raw: Mapping[str, Any]) -> dict[str, Any]:
    """Return the canonical, location-independent intent validation report."""
    validate_mechanical_intent(raw)
    return {
        "schema": 2, "kind": VALIDATION_KIND, "status": "VALID",
        "intent_semantic_sha256": semantic_sha256(raw),
    }


def _cli_validate_intent(args: argparse.Namespace) -> int:
    raw = load_yaml(args.intent)
    _write_or_print(
        mechanical_intent_validation_report(raw), args.output,
        inputs=[args.intent])
    return 0


def _cli_validate_evidence(args: argparse.Namespace) -> int:
    raw_config = load_yaml(args.config)
    loaded = validate_config_v2(raw_config, args.root)
    summary = validate_physical_evidence_v2(load_yaml(args.evidence), loaded)
    _write_or_print(
        {"schema": 2, "kind": VALIDATION_KIND, **summary}, args.output,
        inputs=[args.evidence, args.config, *_bound_input_paths(loaded)])
    return 1 if summary["status"] == "FAIL" else 0


def _cli_aggregate(args: argparse.Namespace) -> int:
    raw = load_json(args.input)
    top = _exact(raw, {"required_scopes", "scope_statuses", "ceilings"},
                 "aggregate_input")
    required = _unique_ids(top["required_scopes"],
                           "aggregate_input.required_scopes")
    statuses = _mapping(top["scope_statuses"], "aggregate_input.scope_statuses")
    ceilings = _mapping(top["ceilings"], "aggregate_input.ceilings")
    status = aggregate_status(statuses, required, ceilings=ceilings)
    _write_or_print({"schema": 2, "kind": VALIDATION_KIND, "status": status},
                    args.output, inputs=[args.input])
    return 1 if status == "FAIL" else 0


def aggregate_config_report(
        raw: Mapping[str, Any], loaded: Mapping[str, Any]) -> dict[str, Any]:
    """Derive the canonical scoped verdict from validated config authority."""
    top = _exact(raw, {"scope_statuses"}, "aggregate_config_input")
    required = required_scope_closure(loaded["scopes"])
    statuses = _mapping(top["scope_statuses"],
                        "aggregate_config_input.scope_statuses")
    status = aggregate_status(
        statuses, required, ceilings=loaded["scope_readiness_ceilings"])
    return {
        "schema": 2,
        "kind": VALIDATION_KIND,
        "status": status,
        "required_scopes": required,
        "scope_readiness_ceilings": loaded["scope_readiness_ceilings"],
    }


def _cli_aggregate_config(args: argparse.Namespace) -> int:
    raw = load_json(args.input)
    loaded = validate_config_v2(load_yaml(args.config), args.root)
    report = aggregate_config_report(raw, loaded)
    _write_or_print(report, args.output,
        inputs=[args.input, args.config, *_bound_input_paths(loaded)])
    status = report["status"]
    if status == "FAIL":
        return 1
    if status == "INCOMPLETE":
        return 2
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate pcb-enclosure mechanical schema v2 contracts")
    sub = parser.add_subparsers(dest="command", required=True)

    intent = sub.add_parser("validate-intent", help="validate mechanical intent")
    intent.add_argument("intent", type=Path)
    intent.add_argument("--output", type=Path)
    intent.set_defaults(func=_cli_validate_intent)

    config = sub.add_parser("validate-config", help="validate and bind v2 config")
    config.add_argument("config", type=Path)
    config.add_argument("--root", type=Path, required=True)
    config.add_argument("--output", type=Path)
    config.set_defaults(func=_cli_validate_config)

    evidence = sub.add_parser("validate-evidence", help="validate v2 physical evidence")
    evidence.add_argument("evidence", type=Path)
    evidence.add_argument("--config", type=Path, required=True)
    evidence.add_argument("--root", type=Path, required=True)
    evidence.add_argument("--output", type=Path)
    evidence.set_defaults(func=_cli_validate_evidence)

    aggregate = sub.add_parser(
        "aggregate",
        help="diagnostic aggregate with caller-supplied applicability/ceilings")
    aggregate.add_argument("input", type=Path)
    aggregate.add_argument("--output", type=Path)
    aggregate.set_defaults(func=_cli_aggregate)

    aggregate_config = sub.add_parser(
        "aggregate-config",
        help="authoritatively aggregate scopes/ceilings from a validated config")
    aggregate_config.add_argument("input", type=Path)
    aggregate_config.add_argument("--config", type=Path, required=True)
    aggregate_config.add_argument("--root", type=Path, required=True)
    aggregate_config.add_argument("--output", type=Path)
    aggregate_config.set_defaults(func=_cli_aggregate_config)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except V2Error as exc:
        print(f"PCB ENCLOSURE V2 FAIL: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
