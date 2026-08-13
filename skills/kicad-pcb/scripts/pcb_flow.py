#!/usr/bin/env python3
"""Fast, bounded orchestration for the generic KiCad PCB workflow.

This is deliberately a thin conductor. Geometry remains owned by the generic
board/routing tools, mechanical convergence remains owned by grind_driver.py,
and order-facing release remains owned by the jlcpcb-fab skill.

Usage:
  pcb_flow.py preflight PROJECT [--board ID|--route-config PATH] [--dry-run]
  pcb_flow.py run PROJECT [--board ID|--route-config PATH] --stage NAME -- CMD
  pcb_flow.py grind PROJECT [--board ID|--route-config PATH] [--max-cycles N]
  pcb_flow.py handoff PROJECT [--board ID|--route-config PATH] [--stage STAGE]
  pcb_flow.py validate PROJECT [--board ID|--route-config PATH]
  pcb_flow.py layout-seal PROJECT [--board ID|--route-config PATH] [--dry-run]
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parent))
from process_runner import run_bounded

try:
    import yaml
except ImportError:  # pragma: no cover - the KiCad interpreter carries yaml
    sys.exit("pcb_flow needs pyyaml")


SCRIPTS = Path(__file__).resolve().parent
FAB_SCRIPTS = SCRIPTS.parent.parent / "jlcpcb-fab" / "scripts"
KPY = "/usr/bin/python3"
MAX_HANDOFF_BYTES = 16 * 1024
EXIT_CONFIG, EXIT_STALE, EXIT_BUDGET = 1, 2, 6
SCHEMA = 2

STAGES = (
    "legacy_unmigrated", "architecture", "sourcing", "schematic",
    "placement", "routing", "grind", "layout_sealed", "fabrication",
    "release_sealed",
)
DEFAULT_SOURCE_ROOTS = ("02_parts", "03_src", "03_tscircuit")
SOURCE_IGNORES = {
    ".DS_Store", "__pycache__", "node_modules", "dist", "build",
}
DEFAULT_TOOL_FILES = (
    "pcb_flow.py", "module_first_check.py", "escape_check.py",
    "tier_preflight.py", "pad_separation.py", "pin_map_check.py",
    "model_coverage_check.py",
    "pre_route_review_check.py", "promoted_route_check.py", "early_design_check.py",
    "via_ampacity_check.py",
    "critical_route_check.py", "placement_gates.py",
    "policy_audit.py", "rf_contract_check.py",
    "grind_driver.py",
    "generate_board_generic.py", "generate_rules_generic.py",
    "route_and_stitch_generic.py", "circuit_json_to_kicad_sch.py",
    "build_provenance.py", "process_runner.py", "artifact_provenance.py",
    "critical_part_facts.py", "project_state.py",
)
DEFAULT_FAB_TOOL_FILES = ("via_process_check.py",)


class FlowError(RuntimeError):
    pass


@dataclass(frozen=True)
class FlowContext:
    root: Path
    route_path: Path
    cfg: dict[str, Any]
    board_id: str
    board: Path
    state_dir: Path
    rebuild: Path

    @property
    def handoff(self) -> Path:
        return self.state_dir / "agent_handoff.yaml"

    @property
    def performance(self) -> Path:
        return self.state_dir / "performance.json"

    @property
    def gate(self) -> Path:
        return self.state_dir / "drc" / "gate.json"

    @property
    def seal(self) -> Path:
        return self.state_dir / "layout_seal.json"

    @property
    def nested(self) -> bool:
        return self.route_path.parent != self.root / "03_src"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _inside(root: Path, value: str | Path, label: str) -> Path:
    path = Path(os.path.expanduser(str(value)))
    path = path.resolve() if path.is_absolute() else (root / path).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise FlowError(f"{label} must stay inside project root: {path}") from exc
    return path


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}
    except (OSError, ValueError, TypeError, yaml.YAMLError) as exc:
        raise FlowError(f"unreadable route config {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise FlowError(f"{path}: root must be a mapping")
    project = data.get("project") or {}
    if not isinstance(project, dict) or not project.get("board"):
        raise FlowError(f"{path}: project.board is required")
    return data


def load_route(root: Path, board_selector: str | None = None,
               route_config: str | None = None) -> tuple[Path, dict[str, Any]]:
    """Resolve one board config; never guess among several nested boards."""
    if route_config:
        path = _inside(root, route_config, "--route-config")
        if not path.is_file():
            raise FlowError(f"no route config: {path}")
        return path, _load_yaml(path)

    default = root / "03_src" / "route.yaml"
    candidates = sorted((root / "03_src").glob("*/route.yaml"))
    if board_selector:
        matches: list[tuple[Path, dict[str, Any]]] = []
        for path in ([default] if default.is_file() else []) + candidates:
            cfg = _load_yaml(path)
            board = Path(str(cfg["project"]["board"])).stem
            names = {path.parent.name, board, str(cfg["project"].get("name", ""))}
            if board_selector in names:
                matches.append((path, cfg))
        if len(matches) != 1:
            found = ", ".join(str(p.relative_to(root)) for p, _ in matches) or "none"
            raise FlowError(f"--board {board_selector!r} matched {found}; use "
                            "--route-config for an exact path")
        return matches[0]

    if default.is_file():
        return default, _load_yaml(default)
    if len(candidates) == 1:
        return candidates[0], _load_yaml(candidates[0])
    if candidates:
        names = ", ".join(p.parent.name for p in candidates)
        raise FlowError(f"multi-board project; choose --board ID from: {names}")
    raise FlowError(f"no route config under {root / '03_src'}")


def flow_cfg(cfg: dict[str, Any], root: Path | None = None) -> dict[str, Any]:
    flow = cfg.get("flow") or {}
    if not isinstance(flow, dict):
        raise FlowError("route.yaml flow must be a mapping")
    for key in ("owner", "copper", "budgets_s", "timeouts_s", "paths", "inputs"):
        if key in flow and not isinstance(flow[key], dict):
            raise FlowError(f"flow.{key} must be a mapping")
    rebuild_args = flow.get("rebuild_args", [])
    if (not isinstance(rebuild_args, list)
            or any(not isinstance(value, str) or not value
                   for value in rebuild_args)):
        raise FlowError("flow.rebuild_args must be a list of non-empty strings")
    copper = flow.get("copper") or {}
    deterministic = set(copper.get("deterministic") or [])
    stochastic = set(copper.get("stochastic") or [])
    overlap = deterministic & stochastic
    if overlap:
        raise FlowError("flow.copper paths cannot be both deterministic and "
                        f"stochastic: {sorted(overlap)}")
    owner = flow.get("owner") or {}
    if owner.get("stage") and owner["stage"] not in STAGES:
        raise FlowError(f"unknown flow.owner.stage {owner['stage']!r}")
    if not isinstance(owner.get("files", []), list):
        raise FlowError("flow.owner.files must be a list")
    if root is not None:
        resolved: list[Path] = []
        for value in owner.get("files", []):
            path = _inside(root, value, "flow.owner.files entry")
            # The promoted route is legitimately absent before the first run;
            # ownership reserves that output path.  Ordinary source/control
            # files must already exist so misspellings still fail closed.
            if not path.exists() and path.suffix != ".kicad_pcb":
                raise FlowError(f"flow.owner.files entry does not exist: {path}")
            resolved.append(path)
        for i, left in enumerate(resolved):
            for right in resolved[i + 1:]:
                if left in right.parents or right in left.parents:
                    raise FlowError("flow.owner.files entries overlap hierarchically: "
                                    f"{left} and {right}")
    return flow


def resolve_context(root: Path, board_selector: str | None = None,
                    route_config: str | None = None) -> FlowContext:
    root = root.resolve()
    route_path, cfg = load_route(root, board_selector, route_config)
    flow = flow_cfg(cfg, root)
    project = cfg["project"]
    board = _inside(root, project["board"], "project.board")
    paths = flow.get("paths") or {}
    nested = route_path.parent != root / "03_src"
    board_id = str(paths.get("board_id") or
                   (route_path.parent.name if nested else project.get("name") or board.stem))
    state_default = Path("06_build") / board_id if nested else Path("06_build")
    state_dir = _inside(root, paths.get("state_dir", state_default),
                        "flow.paths.state_dir")
    rebuild_default = route_path.parent / "rebuild_all.sh"
    rebuild = _inside(root, paths.get("rebuild", rebuild_default),
                      "flow.paths.rebuild")
    ctx = FlowContext(root, route_path, cfg, board_id, board, state_dir, rebuild)
    inputs = flow.get("inputs") or {}
    if nested:
        missing = [key for key in ("include", "parts") if not inputs.get(key)]
        if missing:
            raise FlowError("multi-board flow requires explicit board-scoped "
                            f"flow.inputs.{', flow.inputs.'.join(missing)}")
    return ctx


def _canonical_bytes(path: Path) -> bytes:
    raw = path.read_bytes()
    suffix = path.suffix.lower()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw
    try:
        if suffix in (".yaml", ".yml"):
            value = yaml.safe_load(text)
            return json.dumps(value, sort_keys=True, separators=(",", ":"),
                              ensure_ascii=False).encode()
        if suffix == ".json":
            value = json.loads(text)
            return json.dumps(value, sort_keys=True, separators=(",", ":"),
                              ensure_ascii=False).encode()
    except Exception:
        pass
    normalized = "\n".join(line.rstrip() for line in text.splitlines()) + "\n"
    return normalized.encode()


def _walk_inputs(ctx: FlowContext, values: Iterable[str | Path]) -> list[Path]:
    files: set[Path] = set()
    for value in values:
        base = _inside(ctx.root, value, "flow.inputs entry")
        if not base.exists():
            raise FlowError(f"flow input does not exist: {base}")
        candidates = [base] if base.is_file() else base.rglob("*")
        for path in candidates:
            if not path.is_file():
                continue
            rel_parts = set(path.relative_to(ctx.root).parts)
            if rel_parts & SOURCE_IGNORES or path.name.endswith((".pyc", ".failed")):
                continue
            files.add(path)
    return sorted(files)


def part_files(ctx: FlowContext) -> list[Path]:
    inputs = (flow_cfg(ctx.cfg).get("inputs") or {})
    values = inputs.get("parts")
    if values is not None and not isinstance(values, list):
        raise FlowError("flow.inputs.parts must be a list")
    roots = values or ["02_parts"]
    parts = [p for p in _walk_inputs(ctx, roots) if p.name == "part.yaml"]
    if not parts:
        raise FlowError("preflight found 0 scoped part.yaml files (vacuous P-ESC)")
    return parts


def source_files(ctx: FlowContext) -> list[Path]:
    inputs = (flow_cfg(ctx.cfg).get("inputs") or {})
    values = inputs.get("include")
    if values is not None and not isinstance(values, list):
        raise FlowError("flow.inputs.include must be a list")
    files = set(_walk_inputs(ctx, values or DEFAULT_SOURCE_ROOTS))
    files.update(part_files(ctx))
    for path in (ctx.route_path, ctx.rebuild):
        if path.is_file():
            files.add(path)
    # Board semantics live beside the PCB but are not generated copper bytes.
    for suffix in (".kicad_sch", ".kicad_pro", ".kicad_dru"):
        path = ctx.board.with_suffix(suffix)
        if path.is_file():
            files.add(path)
    # Independent review judgments are layout-seal inputs too. Any edit,
    # replacement, or deletion must stale the witness.
    review_root = ctx.root / "08_reviews"
    if review_root.is_dir():
        files.update(_walk_inputs(ctx, [review_root]))
    files.discard(ctx.board)
    return sorted(files)


def build_source_files(ctx: FlowContext) -> list[Path]:
    """Inputs that can produce board bytes, excluding later review judgments."""
    review_root = ctx.root / "08_reviews"
    return [path for path in source_files(ctx)
            if not path.is_relative_to(review_root)]


def _review_field(text: str, name: str) -> str:
    match = re.search(rf"(?mi)^\s*{re.escape(name)}\s*:\s*(\S+)\s*$", text)
    return match.group(1) if match else ""


def _rf_enabled_for_review_provenance(ctx: FlowContext) -> bool:
    """Read the explicit RF applicability decision; malformed is never false."""
    path = ctx.root / "03_src/rules/rf.yaml"
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise FlowError(f"cannot read RF applicability contract {path}: {exc}") from exc
    rf = data.get("rf") if isinstance(data, dict) and data.get("schema") == 1 else None
    if not isinstance(rf, dict) or not isinstance(rf.get("enabled"), bool):
        raise FlowError(
            "reviewed-commit provenance requires schema-1 rf.yaml with "
            "rf.enabled true or false")
    rationale = rf.get("rationale")
    if not isinstance(rationale, str) or not rationale.strip():
        raise FlowError(
            "reviewed-commit provenance requires a substantive rf.rationale")
    return rf["enabled"]


def reviewed_commit_provenance(ctx: FlowContext, commit: str) -> dict[str, str]:
    """Fail closed unless signed layout bytes and their producers equal COMMIT."""
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise FlowError("--reviewed-commit requires a full 40-character SHA")
    repo_run = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], cwd=ctx.root,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if repo_run.returncode:
        raise FlowError("--reviewed-commit requires a Git worktree")
    repo = Path(repo_run.stdout.strip()).resolve()
    exists = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}^{{commit}}"], cwd=repo,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if exists.returncode:
        raise FlowError(f"reviewed commit {commit} does not identify a commit")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=repo,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if ancestor.returncode:
        raise FlowError(f"reviewed commit {commit} is not an ancestor of HEAD")

    compared = [ctx.board, *build_source_files(ctx)]
    current_set = {path.resolve().relative_to(repo).as_posix()
                   for path in compared}
    inputs = flow_cfg(ctx.cfg).get("inputs") or {}
    include_roots = inputs.get("include") or list(DEFAULT_SOURCE_ROOTS)
    part_roots = inputs.get("parts") or ["02_parts"]

    def committed_under(values: Iterable[str], *, parts_only: bool = False) -> set[str]:
        roots = [_inside(ctx.root, value, "flow input").relative_to(repo).as_posix()
                 for value in values]
        result = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", commit, "--", *roots],
            cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode:
            raise FlowError("cannot enumerate reviewed commit build inputs")
        names = set()
        for name in result.stdout.splitlines():
            path = Path(name)
            if set(path.parts) & SOURCE_IGNORES \
                    or path.name.endswith((".pyc", ".failed")):
                continue
            if parts_only and path.name != "part.yaml":
                continue
            names.add(name)
        return names

    committed_set = committed_under(include_roots)
    committed_set.update(committed_under(part_roots, parts_only=True))
    exact = [ctx.route_path, ctx.rebuild, ctx.board]
    exact.extend(ctx.board.with_suffix(suffix)
                 for suffix in (".kicad_sch", ".kicad_pro", ".kicad_dru"))
    for path in exact:
        rel = path.resolve().relative_to(repo).as_posix()
        exists_at_commit = subprocess.run(
            ["git", "cat-file", "-e", f"{commit}:{rel}"], cwd=repo,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
        if exists_at_commit:
            committed_set.add(rel)
    review_prefix = (ctx.root / "08_reviews").relative_to(repo).as_posix() + "/"
    committed_set = {name for name in committed_set
                     if not name.startswith(review_prefix)}
    if committed_set != current_set:
        missing = sorted(committed_set - current_set)
        added = sorted(current_set - committed_set)
        detail = f"missing={missing[:1]} added={added[:1]}"
        raise FlowError(
            f"reviewed commit declared build-input set differs: {detail}")

    for path in sorted(set(compared)):
        try:
            rel = path.resolve().relative_to(repo).as_posix()
        except ValueError as exc:
            raise FlowError(f"reviewed input is outside the Git worktree: {path}") from exc
        blob = subprocess.run(
            ["git", "show", f"{commit}:{rel}"], cwd=repo,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if blob.returncode:
            raise FlowError(f"reviewed commit lacks declared build input {rel}")
        if blob.stdout != path.read_bytes():
            raise FlowError(f"reviewed commit byte mismatch: {rel}")

    board_hash = hashlib.sha256(ctx.board.read_bytes()).hexdigest()
    schematic = ctx.board.with_suffix(".kicad_sch")
    schematic_hash = (hashlib.sha256(schematic.read_bytes()).hexdigest()
                      if schematic.is_file() else "")
    required = {
        "pin": ("*_pin_review.md", "board_sha256", board_hash),
        "render": ("*_render_review.md", "board_sha256", board_hash),
        "topology": ("*_redteam_topology.md", "board_sha256", board_hash),
        "layout": ("*_redteam_layout.md", "board_sha256", board_hash),
    }
    if _rf_enabled_for_review_provenance(ctx):
        required.update({
            "rf schematic": ("*_rf_schematic.md", "artifact_sha256", schematic_hash),
            "rf pcb": ("*_rf_pcb.md", "artifact_sha256", board_hash),
        })
    review_root = ctx.root / "08_reviews"
    bound: list[str] = []
    for label, (pattern, hash_field, expected_hash) in required.items():
        matches = []
        for path in sorted(review_root.glob(pattern)) if review_root.is_dir() else []:
            text = path.read_text(encoding="utf-8-sig")
            if (_review_field(text, "source_commit") == commit
                    and _review_field(text, hash_field) == expected_hash
                    and _review_field(text, "design_verdict").upper() == "SOUND"):
                matches.append(path.name)
        if not matches:
            raise FlowError(
                f"reviewed commit lacks exact SOUND {label} review coverage")
        bound.append(matches[-1])
    return {"method": "reviewed_commit", "source_commit": commit,
            "reviews": ",".join(bound)}


def tool_files(ctx: FlowContext) -> list[Path]:
    inputs = (flow_cfg(ctx.cfg).get("inputs") or {})
    extra = inputs.get("tools") or []
    if not isinstance(extra, list):
        raise FlowError("flow.inputs.tools must be a list")
    files = {SCRIPTS / name for name in DEFAULT_TOOL_FILES}
    files.update(FAB_SCRIPTS / name for name in DEFAULT_FAB_TOOL_FILES)
    for value in extra:
        path = Path(os.path.expanduser(str(value)))
        path = path.resolve() if path.is_absolute() else (ctx.root / path).resolve()
        if not path.is_file():
            raise FlowError(f"flow.inputs.tools entry does not exist: {path}")
        files.add(path)
    missing = sorted(str(p) for p in files if not p.is_file())
    if missing:
        raise FlowError(f"required flow tool missing: {missing[0]}")
    return sorted(files)


def _aggregate_hash(paths: Iterable[Path], label_root: Path | None = None) -> str:
    h = hashlib.sha256()
    for path in paths:
        if label_root and path.is_relative_to(label_root):
            label = path.relative_to(label_root).as_posix()
        else:
            label = str(path)
        h.update(label.encode() + b"\0")
        h.update(_canonical_bytes(path) + b"\0")
    return "sha256:" + h.hexdigest()


def tree_hash(ctx: FlowContext) -> str:
    return _aggregate_hash(source_files(ctx), ctx.root)


def tools_hash(ctx: FlowContext) -> str:
    # Keep built-in tool labels stable across clones while retaining absolute
    # labels for explicitly declared tools outside this repository.
    return _aggregate_hash(tool_files(ctx), SCRIPTS.parents[2])


def file_hash(path: Path) -> str | None:
    if not path.is_file():
        return None
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def gate_counts(path: Path) -> dict[str, int | None]:
    if not path.is_file():
        return {"violations": None, "unconnected": None, "parity": None}
    try:
        gate = json.loads(path.read_text(encoding="utf-8-sig"))
        return {
            "violations": len(gate.get("violations") or []),
            "unconnected": len(gate.get("unconnected_items") or []),
            "parity": len(gate.get("schematic_parity") or []),
        }
    except (OSError, ValueError, TypeError) as exc:
        raise FlowError(f"unreadable DRC gate {path}: {exc}") from exc


def clean_gate(counts: dict[str, int | None]) -> bool:
    return all(counts[k] == 0 for k in ("violations", "unconnected", "parity"))


def gate_is_fresh(ctx: FlowContext) -> bool:
    if not ctx.gate.is_file() or not ctx.board.is_file():
        return False
    # DRC measures the board under its active project/rule/schematic semantics.
    # Other source/tool changes stale the content hashes, but need not make an
    # otherwise current board measurement impossible to hand off.
    subjects = [ctx.board]
    for suffix in (".kicad_sch", ".kicad_pro", ".kicad_dru"):
        sidecar = ctx.board.with_suffix(suffix)
        if sidecar.is_file():
            subjects.append(sidecar)
    newest = max(path.stat().st_mtime_ns for path in subjects)
    return ctx.gate.stat().st_mtime_ns >= newest


def snapshot(ctx: FlowContext) -> dict[str, str | None]:
    return {
        "source": tree_hash(ctx),
        "board": file_hash(ctx.board),
        "tools": tools_hash(ctx),
        "gate": file_hash(ctx.gate),
    }


def seal_witness_document(ctx: FlowContext,
                          provenance: dict[str, str] | None = None) -> dict[str, Any]:
    witness = {
        "schema": SCHEMA,
        "generated_at": utc_now(),
        "inputs": snapshot(ctx),
        "scope": "PCB layout only",
        "board_id": ctx.board_id,
    }
    if provenance:
        witness["provenance"] = provenance
    return witness


def seal_witness_valid(ctx: FlowContext) -> bool:
    if not ctx.seal.is_file() or not gate_is_fresh(ctx):
        return False
    try:
        witness = json.loads(ctx.seal.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return False
    base = (witness.get("schema") == SCHEMA
            and witness.get("inputs") == snapshot(ctx)
            and clean_gate(gate_counts(ctx.gate)))
    if not base:
        return False
    provenance = witness.get("provenance")
    if isinstance(provenance, dict) \
            and provenance.get("method") == "reviewed_commit":
        try:
            current = reviewed_commit_provenance(
                ctx, str(provenance.get("source_commit", "")))
        except FlowError:
            return False
        return provenance == current
    return provenance is None


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temp.write_text(text)
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def load_perf(ctx: FlowContext) -> dict[str, Any]:
    path = ctx.performance
    if not path.is_file():
        return {"schema": 1, "runs": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise FlowError(f"unreadable performance log {path}: {exc}") from exc
    if data.get("schema") != 1 or not isinstance(data.get("runs"), list):
        raise FlowError(f"unsupported performance log schema in {path}")
    return data


def record_perf(ctx: FlowContext, stage: str, command: list[str], elapsed: float,
                rc: int, budget_s: float | None = None,
                timeout_s: float | None = None) -> None:
    data = load_perf(ctx)
    run = {
        "at": utc_now(), "stage": stage, "seconds": round(elapsed, 3),
        "rc": rc, "command": shlex.join(command),
    }
    if budget_s is not None:
        run["budget_s"] = budget_s
        run["over_budget"] = elapsed > budget_s
    if timeout_s is not None:
        run["timeout_s"] = timeout_s
        run["timed_out"] = rc == 124
    data["runs"].append(run)
    data["runs"] = data["runs"][-200:]
    _atomic_write(ctx.performance, json.dumps(data, indent=2) + "\n")


def run_timed(ctx: FlowContext, stage: str, command: list[str],
              budget_s: float | None = None,
              timeout_s: float | None = None) -> int:
    print(f"[{stage}] $ {shlex.join(command)}", flush=True)
    timeout_s = configured_timeout(ctx.cfg, stage) if timeout_s is None else timeout_s
    if timeout_s is not None and timeout_s <= 0:
        raise FlowError("stage timeout must be positive")
    heartbeat_s = configured_heartbeat(ctx.cfg)
    safe_stage = re.sub(r"[^A-Za-z0-9_.-]+", "_", stage)
    result = run_bounded(
        command, cwd=ctx.root, timeout_s=timeout_s, heartbeat_s=heartbeat_s,
        label=stage, state_path=ctx.state_dir / "pipeline_state" /
        f"{safe_stage}.json")
    elapsed = result.elapsed_s
    record_perf(ctx, stage, command, elapsed, result.returncode, budget_s,
                timeout_s)
    budget = f" / budget {budget_s:g}s" if budget_s is not None else ""
    timeout = f" / timeout {timeout_s:g}s" if timeout_s is not None else ""
    print(f"[{stage}] rc={result.returncode}, {elapsed:.3f}s{budget}{timeout}")
    if result.returncode == 0 and budget_s is not None and elapsed > budget_s:
        print(f"BUDGET EXCEEDED: {stage} took {elapsed:.3f}s > {budget_s:g}s")
        return EXIT_BUDGET
    return result.returncode


def configured_budget(cfg: dict[str, Any], stage: str) -> float | None:
    budgets = ((cfg.get("flow") or {}).get("budgets_s") or {})
    value = budgets.get(stage)
    return float(value) if value is not None else None


def configured_timeout(cfg: dict[str, Any], stage: str) -> float | None:
    """Return a hard deadline, distinct from a performance budget."""
    timeouts = ((cfg.get("flow") or {}).get("timeouts_s") or {})
    value = timeouts.get(stage, timeouts.get("default"))
    try:
        value = float(value) if value is not None else None
    except (TypeError, ValueError) as exc:
        raise FlowError(f"flow.timeouts_s.{stage} must be numeric") from exc
    if value is not None and value <= 0:
        raise FlowError(f"flow.timeouts_s.{stage} must be positive")
    return value


def configured_heartbeat(cfg: dict[str, Any]) -> float:
    value = (cfg.get("flow") or {}).get("heartbeat_s", 10)
    try:
        value = float(value)
    except (TypeError, ValueError) as exc:
        raise FlowError("flow.heartbeat_s must be numeric") from exc
    if value <= 0:
        raise FlowError("flow.heartbeat_s must be positive")
    return value


def preflight_commands(ctx: FlowContext, include_land: bool = True
                       ) -> list[tuple[str, list[str]]]:
    rf_contract = ctx.route_path.parent / "rules" / "rf.yaml"
    commands = [
        ("pre_route_schematic", [
            KPY, str(SCRIPTS / "pre_route_review_check.py"), str(ctx.root),
            "--phase", "schematic"]),
        ("rf_contract", [KPY, str(SCRIPTS / "rf_contract_check.py"),
                         str(ctx.root), "--contract", str(rf_contract),
                         "--require-applicability"]),
        ("tier_preflight", [KPY, str(SCRIPTS / "tier_preflight.py"),
                            str(ctx.root), "--route-config", str(ctx.route_path),
                            "--board", ctx.board_id]),
        ("escape_packages", [KPY, str(SCRIPTS / "escape_check.py"),
                             *map(str, part_files(ctx))]),
    ]
    # Legacy projects remain explicit/unmigrated. Adopted source contracts are
    # hard architecture gates and cannot be bypassed through direct pcb_flow.
    prefix = []
    adopted = any((ctx.root / "03_src/rules" / name).is_file()
                  for name in ("requirements.yaml", "integration.yaml"))
    if adopted:
        circuit = ctx.root / "03_tscircuit/build/circuit.json"
        prefix.extend([
            ("module_first", [KPY, str(SCRIPTS / "module_first_check.py"),
                              str(ctx.root)]),
            ("build_freshness", [KPY, str(SCRIPTS / "build_provenance.py"),
                                 "audit", str(ctx.root)]),
            ("early_design", [KPY, str(SCRIPTS / "early_design_check.py"),
                              str(ctx.root)]),
            ("net_label_survival", [KPY, str(SCRIPTS / "net_label_survival.py"),
                                    str(ctx.root)]),
            ("electrical_invariants", [KPY, str(SCRIPTS / "electrical_invariants.py"),
                                       str(ctx.root)]),
            ("adr_coverage", [KPY, str(SCRIPTS / "electrical_invariants.py"),
                              str(ctx.root), "--adr-coverage"]),
            ("power_topology", [KPY, str(SCRIPTS / "power_topology.py"),
                                str(ctx.root)]),
            ("power_margin", [KPY, str(SCRIPTS / "power_topology.py"),
                              str(ctx.root), "--margin"]),
            ("off_control", [KPY, str(SCRIPTS / "power_topology.py"),
                             str(ctx.root), "--off-control"]),
            ("count_parity", [KPY, str(SCRIPTS / "count_parity.py"),
                              str(ctx.root)]),
            ("circuit_bom", [KPY, str(FAB_SCRIPTS / "bom_source_check.py"),
                             "--circuit-only", str(circuit), "--parts",
                             str(ctx.root / "02_parts")]),
        ])
    commands[0:0] = prefix
    if include_land:
        # Schematic review owns the topology boundary and must remain before
        # any board-artifact/placement gate. Insert the board checks just
        # before package/tier routing preflight, not merely after the prefix.
        first_board = next(i for i, row in enumerate(commands)
                           if row[0] == "escape_packages")
        commands.insert(first_board, ("pin_map", [
            KPY, str(SCRIPTS / "pin_map_check.py"), str(ctx.root),
            "--board", str(ctx.board), "--circuit-json",
            str(ctx.root / "03_tscircuit/build/circuit.json")]))
        critical_facts = ctx.route_path.parent / "rules" / "critical_parts.yaml"
        offset = 1
        if critical_facts.is_file():
            commands.insert(first_board + offset, ("critical_part_facts", [
                KPY, str(SCRIPTS / "critical_part_facts.py"), str(ctx.root),
                "--board", str(ctx.board), "--facts", str(critical_facts)]))
            offset += 1
        commands.insert(first_board + offset, ("placement_clearance", [
            KPY, str(SCRIPTS / "placement_gates.py"), str(ctx.board),
            "--config", str(ctx.root / "03_src/placement_gates.json")]))
        commands.insert(first_board + offset + 1, ("critical_pair_map", [
            KPY, str(SCRIPTS / "critical_route_check.py"), str(ctx.root),
            "--board", str(ctx.board)]))
        commands.insert(first_board + offset + 2, ("escape_lands",
                            [KPY, str(SCRIPTS / "escape_check.py"),
                             "--board", str(ctx.board)]))
        nets = ctx.route_path.parent / "rules" / "nets.yaml"
        commands.insert(first_board + offset + 3, ("pad_separation", [
            KPY, str(SCRIPTS / "pad_separation.py"), str(ctx.board),
            "--project", str(ctx.root), "--nets", str(nets)]))
        commands.insert(first_board + offset + 4, ("placement_policy", [
            KPY, str(SCRIPTS / "policy_audit.py"), str(ctx.root),
            "--board", ctx.board_id, "--skip-drc", "--phase", "placement"]))
        placement_index = next(i for i, row in enumerate(commands)
                               if row[0] == "placement_policy") + 1
        commands.insert(placement_index, ("route_prep", [
            KPY, str(SCRIPTS / "route_and_stitch_generic.py"), "prep",
            str(ctx.route_path)]))
        commands.insert(placement_index + 1, ("pre_route_placement", [
            KPY, str(SCRIPTS / "pre_route_review_check.py"), str(ctx.root),
            "--phase", "placement", "--board", str(ctx.board)]))
    return commands


def cmd_preflight(ctx: FlowContext, dry_run: bool) -> int:
    flow_cfg(ctx.cfg, ctx.root)
    for stage, command in preflight_commands(ctx):
        if dry_run:
            print(f"[{stage}] $ {shlex.join(command)}")
            continue
        rc = run_timed(ctx, stage, command, configured_budget(ctx.cfg, stage))
        if rc:
            return rc
    return 0


def default_stage(ctx: FlowContext, counts: dict[str, int | None]) -> str:
    if not ctx.cfg.get("flow"):
        return "legacy_unmigrated"
    if clean_gate(counts) and seal_witness_valid(ctx):
        return "layout_sealed"
    if any(counts[k] not in (None, 0) for k in counts):
        return "grind"
    return "routing"


def _selector_args(ctx: FlowContext) -> str:
    return f" --board {shlex.quote(ctx.board_id)}" if ctx.nested else ""


def handoff_document(ctx: FlowContext, stage: str | None, blockers: list[str],
                     pending_seal: dict[str, Any] | None = None) -> dict[str, Any]:
    flow = flow_cfg(ctx.cfg, ctx.root)
    if ctx.gate.is_file() and not gate_is_fresh(ctx):
        raise FlowError(f"DRC gate is older than a board/source/tool input: {ctx.gate}; "
                        "re-run DRC before generating a handoff")
    counts = gate_counts(ctx.gate)
    stage = stage or default_stage(ctx, counts)
    if stage not in STAGES:
        raise FlowError(f"unknown stage {stage!r}; choose one of {STAGES}")
    sealed = stage in ("layout_sealed", "fabrication", "release_sealed")
    if sealed and not clean_gate(counts):
        raise FlowError(f"stage {stage} requires DRC 0/0/0, got "
                        f"{counts['violations']}/{counts['unconnected']}/"
                        f"{counts['parity']}")
    if sealed and not (seal_witness_valid(ctx) or
                       (pending_seal and pending_seal.get("inputs") == snapshot(ctx))):
        raise FlowError(f"stage {stage} requires a fresh layout-seal witness "
                        "bound to source, board, tools, and gate")
    owner = flow.get("owner") or {}
    perf = load_perf(ctx).get("runs", [])
    latest: dict[str, float] = {}
    for run in perf:
        latest[str(run.get("stage"))] = float(run.get("seconds", 0))
    combined_blockers = list(dict.fromkeys(
        [*list(flow.get("blockers") or []), *blockers]))
    inputs = snapshot(ctx)
    inputs["board_path"] = (ctx.board.relative_to(ctx.root).as_posix()
                            if ctx.board.is_relative_to(ctx.root) else str(ctx.board))
    select = _selector_args(ctx)
    return {
        "schema": SCHEMA,
        "generated_at": utc_now(),
        "project": ctx.root.name,
        "board_id": ctx.board_id,
        "stage": stage,
        "inputs": inputs,
        "metrics": {"drc": counts, "timing_s": latest},
        "owner": {
            "stage": owner.get("stage", stage),
            "files": owner.get("files", [str(ctx.route_path.relative_to(ctx.root))]),
        },
        "blockers": combined_blockers,
        "commands": {
            "preflight": f"{KPY} skills/kicad-pcb/scripts/pcb_flow.py preflight {ctx.root}{select}",
            "grind": f"{KPY} skills/kicad-pcb/scripts/pcb_flow.py grind {ctx.root}{select}",
            "layout_seal": f"{KPY} skills/kicad-pcb/scripts/pcb_flow.py layout-seal {ctx.root}{select}",
        },
        "scope": "PCB layout only; fabrication/PCBA release gates are not sealed",
    }


def handoff_text(ctx: FlowContext, stage: str | None, blockers: list[str],
                 pending_seal: dict[str, Any] | None = None) -> tuple[str, dict[str, Any]]:
    document = handoff_document(ctx, stage, blockers, pending_seal)
    text = yaml.safe_dump(document, sort_keys=False, width=100)
    size = len(text.encode())
    if size > MAX_HANDOFF_BYTES:
        raise FlowError(f"handoff is {size} bytes; ceiling is {MAX_HANDOFF_BYTES}")
    return text, document


def write_handoff(ctx: FlowContext, stage: str | None,
                  blockers: list[str]) -> Path:
    text, document = handoff_text(ctx, stage, blockers)
    _atomic_write(ctx.handoff, text)
    print(f"handoff -> {ctx.handoff} ({len(text.encode())} bytes, "
          f"stage {document['stage']})")
    return ctx.handoff


def validate_handoff(ctx: FlowContext) -> int:
    path = ctx.handoff
    if not path.is_file():
        print(f"STALE: no handoff {path}")
        return EXIT_STALE
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}
    except Exception as exc:
        print(f"STALE: unreadable handoff: {exc}")
        return EXIT_STALE
    problems: list[str] = []
    if doc.get("schema") != SCHEMA:
        problems.append("unsupported schema")
    inputs = doc.get("inputs") or {}
    current = snapshot(ctx)
    for key, description in (("source", "source hash changed"),
                             ("board", "board hash changed"),
                             ("tools", "tool hash changed"),
                             ("gate", "gate hash changed")):
        if inputs.get(key) != current.get(key):
            problems.append(description)
    if len(path.read_bytes()) > MAX_HANDOFF_BYTES:
        problems.append("handoff exceeds size ceiling")
    if ctx.gate.is_file() and not gate_is_fresh(ctx):
        problems.append("DRC gate is stale")
    if doc.get("board_id") != ctx.board_id:
        problems.append("board selection changed")
    if problems:
        print("STALE handoff: " + "; ".join(problems))
        return EXIT_STALE
    if doc.get("stage") in ("layout_sealed", "fabrication", "release_sealed") \
            and not seal_witness_valid(ctx):
        print("STALE handoff: layout-seal witness missing or stale")
        return EXIT_STALE
    print(f"handoff valid: {path} (stage {doc.get('stage')})")
    return 0


def cmd_grind(ctx: FlowContext, max_cycles: int, dry_run: bool) -> int:
    command = [KPY, str(SCRIPTS / "grind_driver.py"), str(ctx.root),
               "--config", str(ctx.route_path.relative_to(ctx.root)),
               "--max-cycles", str(max_cycles)]
    if dry_run:
        print(f"[grind] $ {shlex.join(command)}")
        return 0
    rc = run_timed(ctx, "grind", command, configured_budget(ctx.cfg, "grind"))
    write_handoff(ctx, None, [])
    return rc


def _failure_handoff(ctx: FlowContext, blocker: str, stage: str | None = None) -> None:
    try:
        write_handoff(ctx, stage, [blocker])
    except FlowError as exc:
        print(f"handoff not written after failure: {exc}", file=sys.stderr)


def cmd_layout_seal(ctx: FlowContext, dry_run: bool,
                    reviewed_commit: str | None = None) -> int:
    # Validate every declarative contract before deleting or writing evidence.
    flow = flow_cfg(ctx.cfg, ctx.root)
    source_files(ctx)
    tool_files(ctx)
    if not ctx.rebuild.is_file():
        raise FlowError(f"layout-seal requires canonical rebuild driver {ctx.rebuild}")
    before = preflight_commands(ctx, include_land=False)
    after = preflight_commands(ctx, include_land=True)
    post_board = [row for row in after if row[0] in (
        "placement_clearance", "critical_pair_map", "escape_lands",
        "pad_separation", "placement_policy")]
    # PR-REVIEW's placement witness is intentionally bound to the exact
    # track-free board. The canonical rebuild grades it before route import.
    # Re-running that checker here, after the driver has added routed copper,
    # compares two different lifecycle artifacts and can never pass. The
    # post-route seal revalidates geometry/policy against the routed board;
    # reviewed-commit recovery separately proves exact final review files.
    post_board.append(("critical_route_connected", [
        KPY, str(SCRIPTS / "critical_route_check.py"), str(ctx.root),
        "--board", str(ctx.board), "--require-connected"]))
    post_board.append(("via_ampacity", [
        KPY, str(SCRIPTS / "via_ampacity_check.py"), str(ctx.board),
        str(ctx.route_path), "--json",
        str(ctx.root / "06_build/verification/via_ampacity.json")]))
    post_board.append(("via_process", [
        KPY, str(FAB_SCRIPTS / "via_process_check.py"), str(ctx.board),
        "--json", str(ctx.root / "06_build/verification/via_process.json")]))
    # Recovery for an already-reviewed immutable commit is intentionally
    # narrower than a generic "skip rebuild" switch. It proves every board
    # producer input and six independent review lenses against an explicit
    # ancestor commit before the canonical producer may be skipped.
    provenance = None
    if reviewed_commit and not dry_run:
        provenance = reviewed_commit_provenance(ctx, reviewed_commit)
    build = [] if reviewed_commit else [
        ("rebuild", ["bash", str(ctx.rebuild),
                     *flow.get("rebuild_args", [])]),
    ]
    commands = before + build + [
        *post_board,
        ("rf_reviews", [
            KPY, str(SCRIPTS / "rf_contract_check.py"), str(ctx.root),
            "--contract", str(ctx.route_path.parent / "rules" / "rf.yaml"),
            "--require-applicability",
            "--require-review", "schematic", "--require-review", "pcb"]),
        ("layout_drc", ["kicad-cli", "pcb", "drc", "--severity-all",
                        "--refill-zones", "--schematic-parity", "--format",
                        "json", "-o", str(ctx.gate), str(ctx.board)]),
    ]
    if dry_run:
        for stage, command in commands:
            print(f"[{stage}] $ {shlex.join(command)}")
        print("dry-run only: PCB layout not sealed; fabrication/PCBA release not sealed")
        return 0
    if ctx.seal.exists():
        ctx.seal.unlink()  # a new failed attempt must not retain an old claim
    for stage, command in commands:
        rc = run_timed(ctx, stage, command, configured_budget(ctx.cfg, stage))
        if rc:
            _failure_handoff(ctx, f"{stage} exited {rc}")
            return rc
    counts = gate_counts(ctx.gate)
    if not clean_gate(counts):
        _failure_handoff(ctx, f"DRC {counts}", "grind")
        print(f"layout seal refused: DRC {counts}")
        return EXIT_CONFIG
    if not gate_is_fresh(ctx):
        raise FlowError("fresh DRC output is older than a board/source/tool input")

    # Prepare both artifacts before publishing either. Publish handoff first;
    # if interrupted before the witness replace, validation safely rejects it.
    if reviewed_commit:
        provenance = reviewed_commit_provenance(ctx, reviewed_commit)
    witness = seal_witness_document(ctx, provenance)
    htext, hdoc = handoff_text(ctx, "layout_sealed", [], pending_seal=witness)
    wtext = json.dumps(witness, indent=2) + "\n"
    _atomic_write(ctx.handoff, htext)
    _atomic_write(ctx.seal, wtext)
    if not seal_witness_valid(ctx):
        ctx.seal.unlink(missing_ok=True)
        raise FlowError("internal error: newly written layout witness is invalid")
    print(f"handoff -> {ctx.handoff} ({len(htext.encode())} bytes, "
          f"stage {hdoc['stage']})")
    method = (f"exact reviewed commit {reviewed_commit}" if reviewed_commit
              else "fresh canonical rebuild")
    print(f"LAYOUT SEALED: {method} + P-BODYCLR + R-PAIRMAP/R-CRITESC + "
          "P-LAND + P-PADSEP + placement review + DRC 0/0/0")
    print("NOT RELEASE SEALED: run the jlcpcb-fab fabrication, assembly, stock, "
          "model, polarity, and staged-release gates before ordering")
    return 0


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="command", required=True)

    def common(p: argparse.ArgumentParser) -> None:
        p.add_argument("project")
        choose = p.add_mutually_exclusive_group()
        choose.add_argument("--board", help="board id/stem in a multi-board project")
        choose.add_argument("--route-config", help="exact project-relative route.yaml")

    for name in ("preflight", "validate", "layout-seal"):
        p = sub.add_parser(name)
        common(p)
        if name != "validate":
            p.add_argument("--dry-run", action="store_true")
        if name == "layout-seal":
            p.add_argument(
                "--reviewed-commit", metavar="SHA",
                help=("recovery path for an exact ancestor commit already "
                      "covered by pin/render/topology/layout and RF reviews; "
                      "all declared build inputs must be byte-identical"))
    p = sub.add_parser("handoff")
    common(p)
    p.add_argument("--stage", choices=STAGES)
    p.add_argument("--blocker", action="append", default=[])
    p = sub.add_parser("grind")
    common(p)
    p.add_argument("--max-cycles", type=int, default=12)
    p.add_argument("--dry-run", action="store_true")
    p = sub.add_parser("run")
    common(p)
    p.add_argument("--stage", required=True)
    p.add_argument("--budget-s", type=float)
    p.add_argument("--timeout-s", type=float,
                   help="hard deadline; kills the command's process group")
    return ap


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    remainder: list[str] = []
    if argv and argv[0] == "run" and "--" in argv:
        cut = argv.index("--")
        remainder, argv = argv[cut + 1:], argv[:cut]
    args = parser().parse_args(argv)
    root = Path(args.project).resolve()
    try:
        ctx = resolve_context(root, args.board, args.route_config)
        if args.command == "preflight":
            return cmd_preflight(ctx, args.dry_run)
        if args.command == "handoff":
            write_handoff(ctx, args.stage, args.blocker)
            return 0
        if args.command == "validate":
            return validate_handoff(ctx)
        if args.command == "grind":
            if args.max_cycles < 1:
                raise FlowError("--max-cycles must be >= 1")
            return cmd_grind(ctx, args.max_cycles, args.dry_run)
        if args.command == "layout-seal":
            return cmd_layout_seal(ctx, args.dry_run, args.reviewed_commit)
        if not remainder:
            raise FlowError("run needs a command after --")
        budget_s = (args.budget_s if args.budget_s is not None
                    else configured_budget(ctx.cfg, args.stage))
        return run_timed(ctx, args.stage, remainder, budget_s,
                         args.timeout_s)
    except FlowError as exc:
        print(f"pcb_flow: {exc}", file=sys.stderr)
        return EXIT_CONFIG


if __name__ == "__main__":
    sys.exit(main())
