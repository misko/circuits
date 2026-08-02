#!/usr/bin/env python3
"""P-MOD: enforce a complexity-weighted module-first architecture contract.

Graded input: ``PROJECT/03_src/rules/integration.yaml`` and every used
``PROJECT/02_parts/*/part.yaml`` dossier.  An adopted project must account for
each complex subsystem as a real module or as an explicit bare-IC decision.
Bare ICs below the configured external-support threshold need a measured
support inventory and rationale. At or above it they additionally need an
evidenced module trade study.
An absent integration file is UNMIGRATED (exit 3), never a pass.

VACUITY: P-MOD passes a project whose programmable device uses a custom
``type:`` string outside the conservative scope vocabulary and whose policy
declares no applicable functions.  The checker cannot infer arbitrary product
semantics from an unconstrained type string.  Fixtured by
``t1_module_first.py::t_vacuity_custom_type``; the visible bound is the
recognized type vocabulary below plus the printed coverage denominator.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - repository KiCad Python has PyYAML
    sys.exit("module_first_check needs pyyaml")


# Intentionally conservative: these are subsystem classes for which buying a
# proven integration is often cheaper than designing the support circuitry.
# Avoid bare "controller", which would accidentally scope tiny supervisors and
# every power switch; name the complex class in part.yaml instead.
COMPLEX_TYPE_RE = re.compile(
    r"microcontroller|(?:^|[_ -])mcu(?:$|[_ -])|processor|(?:^|[_ -])soc(?:$|[_ -])|"
    r"fpga|cpld|wireless|wi-?fi|bluetooth|radio|gnss|cellular|"
    r"usb(?:[_ -][a-z0-9]+)*[_ -]controller|ethernet[_ -]?(?:phy|controller)|"
    r"buck[_ -]?controller|boost[_ -]?controller|power[_ -]?controller|"
    r"precision[_ -]?(?:adc|dac|afe)|analog[_ -]?front[_ -]?end|transceiver|"
    r"module",
    re.I,
)


@dataclass(frozen=True)
class Part:
    path: Path
    name: str
    mpn: str
    data: dict[str, Any]

    @property
    def type_text(self) -> str:
        return str(self.data.get("type") or "")

    @property
    def is_module(self) -> bool:
        style = str((self.data.get("escape") or {}).get("style") or "")
        return style.lower() == "module" or bool(re.search(
            r"(?:^|[_ -])module(?:$|[_ -])", self.type_text, re.I))

    @property
    def in_scope(self) -> bool:
        return bool(COMPLEX_TYPE_RE.search(self.type_text)) or self.is_module


def _text(value: Any, minimum: int = 20) -> bool:
    return len(str(value or "").strip()) >= minimum


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}
    except (OSError, ValueError, TypeError, yaml.YAMLError) as exc:
        raise ValueError(f"{path}: unreadable YAML ({exc})") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be a mapping")
    return value


def _artifact_refdes(root: Path) -> set[str]:
    """Read independently generated source refdes when circuit.json is fresh.

    P-MOD runs before generation, so a stale prior build must not make a newly
    authored support ref impossible to introduce. Freshness is intentionally
    coarse here; canonical build freshness gates provide the cryptographic
    binding later in the pipeline.
    """
    path = root / "03_tscircuit/build/circuit.json"
    if not path.is_file():
        return set()
    source = root / "03_tscircuit/src"
    source_files = list(source.rglob("*.tsx")) if source.is_dir() else []
    if source_files and path.stat().st_mtime_ns <= max(
            item.stat().st_mtime_ns for item in source_files):
        return set()
    try:
        import json
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError, TypeError):
        return set()
    if not isinstance(data, list):
        return set()
    return {
        str(item.get("name"))
        for item in data
        if isinstance(item, dict)
        and item.get("type") == "source_component"
        and item.get("name")
    }


def _parts(root: Path) -> tuple[list[Part], list[str]]:
    parts, errors = [], []
    for path in sorted((root / "02_parts").glob("*/part.yaml")):
        try:
            data = _load_yaml(path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        parts.append(Part(path, path.parent.name,
                          str(data.get("mpn") or path.parent.name), data))
    return parts, errors


def _authoring_text(root: Path) -> str:
    """Return live declarative authoring text used to reject false retirement.

    Historical dossiers remain necessary to resolve immutable release archives,
    but they must not be an escape hatch for a part that is still present in the
    live design.  The TSX source is authoritative at this stage; generated build
    and KiCad artifacts are deliberately excluded because they may still reflect
    the pre-backtrack design until the next canonical rebuild.
    """
    source = root / "03_tscircuit/src"
    chunks: list[str] = []
    for path in sorted(source.rglob("*.tsx")) if source.is_dir() else []:
        try:
            chunks.append(path.read_text(encoding="utf-8-sig"))
        except OSError:
            continue
    return "\n".join(chunks)


def _identity_tokens(part: Part) -> set[str]:
    tokens = {part.mpn}
    sourcing = part.data.get("sourcing") or {}
    if isinstance(sourcing, dict):
        lcsc = sourcing.get("lcsc")
        if lcsc:
            tokens.add(str(lcsc))
    return {token for token in tokens if token.strip()}


def _exception_errors(root: Path, label: str, value: Any) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label}: bare_ic requires an exception mapping"]
    errors = []
    if not _text(value.get("decision_rationale") or value.get("binding_requirement"), 30):
        errors.append(f"{label}: exception.decision_rationale needs the total-"
                      "complexity reason for retaining the bare IC")
    if not _text(value.get("evidence"), 30):
        errors.append(f"{label}: exception.evidence needs measured/cited evidence")
    adr = value.get("adr")
    if not adr:
        errors.append(f"{label}: exception.adr is required")
    else:
        path = (root / str(adr)).resolve()
        decisions = (root / "01_docs/decisions").resolve()
        try:
            path.relative_to(decisions)
        except ValueError:
            errors.append(f"{label}: exception.adr must live under 01_docs/decisions")
        else:
            if not path.is_file():
                errors.append(f"{label}: exception.adr does not exist: {adr}")
    candidates = value.get("modules_considered")
    if not isinstance(candidates, list) or not candidates:
        errors.append(f"{label}: exception.modules_considered needs at least one module")
    else:
        for index, candidate in enumerate(candidates):
            at = f"{label}: modules_considered[{index}]"
            if not isinstance(candidate, dict):
                errors.append(f"{at} must be a mapping")
                continue
            if not str(candidate.get("part") or "").strip():
                errors.append(f"{at}.part is required")
            if not _text(candidate.get("rejected_because"), 30):
                errors.append(f"{at}.rejected_because needs a concrete tradeoff")
            if not _text(candidate.get("evidence"), 30):
                errors.append(f"{at}.evidence needs a measured/cited comparison")
    return errors


def evaluate(project: str | Path) -> dict[str, Any]:
    root = Path(project).resolve()
    config = root / "03_src/rules/integration.yaml"
    if not config.is_file():
        return {"status": "unmigrated", "root": root, "config": config,
                "total": 0, "graded": 0, "modules": 0, "bare": 0,
                "findings": []}
    findings: list[str] = []
    try:
        policy = _load_yaml(config)
    except ValueError as exc:
        return {"status": "adopted", "root": root, "config": config,
                "total": 0, "graded": 0, "modules": 0, "bare": 0,
                "findings": [str(exc)]}

    schema = policy.get("schema")
    if schema not in {1, 2}:
        findings.append("integration.yaml schema must be 1 or 2")
    expected_default = "prefer_module" if schema == 1 else "complexity_weighted"
    if policy.get("default") != expected_default:
        findings.append(f"integration.yaml default must be {expected_default}")
    threshold = 0
    if schema == 2:
        threshold = policy.get("module_support_threshold", 10)
        if not isinstance(threshold, int) or isinstance(threshold, bool) or threshold < 1:
            findings.append("integration.yaml module_support_threshold must be a positive integer")
            threshold = 10
    selections = policy.get("selections")
    if not isinstance(selections, list):
        findings.append("integration.yaml selections must be a list")
        selections = []

    parts, part_errors = _parts(root)
    findings.extend(part_errors)
    scoped = [part for part in parts if part.in_scope]
    aliases: dict[str, list[Part]] = {}
    for part in parts:
        for alias in {part.name, part.mpn}:
            aliases.setdefault(alias, []).append(part)

    chosen: set[Path] = set()
    historical: set[Path] = set()
    authoring_text = _authoring_text(root)

    historical_rows = policy.get("historical_dossiers", [])
    if not isinstance(historical_rows, list):
        findings.append("integration.yaml historical_dossiers must be a list")
        historical_rows = []
    for index, row in enumerate(historical_rows):
        at = f"historical_dossiers[{index}]"
        if not isinstance(row, dict):
            findings.append(f"{at} must be a mapping")
            continue
        part_name = str(row.get("part") or "").strip()
        matches = aliases.get(part_name, [])
        if len(matches) != 1:
            findings.append(f"{at}.part {part_name!r} resolves to "
                            f"{len(matches)} part dossiers")
            continue
        part = matches[0]
        if not part.in_scope:
            findings.append(f"{at}: {part.mpn} is not a complex subsystem dossier")
            continue
        if part.path in historical:
            findings.append(f"{at}: {part.mpn} is declared historical more than once")
            continue
        if not _text(row.get("reason"), 30):
            findings.append(f"{at}.reason must explain why the dossier is retained")
            continue
        present = sorted(token for token in _identity_tokens(part)
                         if token in authoring_text)
        if present:
            findings.append(f"{at}: {part.mpn} is still present in live TSX source "
                            f"via exact identity token(s) {present}")
            continue
        historical.add(part.path)
    artifact_refs = _artifact_refdes(root)
    graded = modules = bare = bare_simple = 0
    for index, selection in enumerate(selections):
        at = f"selections[{index}]"
        if not isinstance(selection, dict):
            findings.append(f"{at} must be a mapping")
            continue
        function = selection.get("function")
        part_name = str(selection.get("part") or "").strip()
        if not _text(function, 8):
            findings.append(f"{at}.function must name the subsystem")
        matches = aliases.get(part_name, [])
        if len(matches) != 1:
            findings.append(f"{at}.part {part_name!r} resolves to "
                            f"{len(matches)} part dossiers")
            continue
        part = matches[0]
        if not part.in_scope:
            findings.append(f"{at}: {part.mpn} type {part.type_text!r} is not a "
                            "declared complex subsystem")
            continue
        if part.path in chosen:
            findings.append(f"{at}: {part.mpn} is selected more than once")
            continue
        if part.path in historical:
            findings.append(f"{at}: {part.mpn} cannot be both selected and historical")
            continue
        chosen.add(part.path)
        if not _text(selection.get("rationale"), 30):
            findings.append(f"{at}: rationale must explain total-complexity fit")
        implementation = selection.get("implementation")
        if implementation == "module":
            if not part.is_module:
                findings.append(f"{at}: {part.mpn} is not a module according to "
                                "part.yaml type / escape.style")
            else:
                modules += 1
        elif implementation == "bare_ic":
            if part.is_module:
                findings.append(f"{at}: {part.mpn} is a module, not a bare_ic")
            errors: list[str] = []
            if schema == 1:
                errors = _exception_errors(root, at, selection.get("exception"))
            else:
                refs = selection.get("support_refs")
                if not isinstance(refs, list) or not refs:
                    errors.append(f"{at}: support_refs needs the bare IC's external support inventory")
                    refs = []
                clean = [str(ref).strip() for ref in refs if str(ref).strip()]
                if len(clean) != len(refs) or len(set(clean)) != len(clean):
                    errors.append(f"{at}: support_refs must be non-empty unique refdes")
                if artifact_refs:
                    missing = sorted(set(clean) - artifact_refs)
                    if missing:
                        errors.append(f"{at}: support_refs absent from circuit.json: {missing}")
                if len(clean) >= threshold:
                    errors.extend(_exception_errors(root, at, selection.get("exception")))
                elif not errors:
                    bare_simple += 1
            findings.extend(errors)
            if not errors and not part.is_module:
                bare += 1
        else:
            findings.append(f"{at}.implementation must be module or bare_ic")
        graded += 1

    omitted = [part.mpn for part in scoped
               if part.path not in chosen and part.path not in historical]
    if omitted:
        findings.append(f"complex subsystem part(s) not selected: {omitted}")
    declaration = policy.get("no_applicable_functions")
    if declaration:
        if selections:
            findings.append("no_applicable_functions cannot coexist with selections")
        if scoped:
            findings.append("no_applicable_functions is false: scoped parts exist")
        if not _text(declaration, 30):
            findings.append("no_applicable_functions needs an explanatory sentence")
    elif not selections and not scoped:
        findings.append("declare no_applicable_functions when the board has no "
                        "module-first subsystem")

    return {"status": "adopted", "root": root, "config": config,
            "total": len(scoped), "graded": graded, "modules": modules,
            "bare": bare, "bare_simple": bare_simple,
            "historical": len(historical), "findings": findings}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="P-MOD module-first gate")
    parser.add_argument("project", help="commissioned project root graded against")
    args = parser.parse_args(argv)
    result = evaluate(args.project)
    if result["status"] == "unmigrated":
        print(f"P-MOD UNMIGRATED: input: {result['config']} — no module-first "
              "policy; legacy project not graded")
        return 3
    ok = not result["findings"]
    verdict = "PASS" if ok else "FAIL"
    print(f"P-MOD {verdict}: {result['graded']}/{result['total']} complex "
          f"subsystem(s) graded; modules={result['modules']} "
          f"bare={result['bare']} simple_bare={result.get('bare_simple', 0)} "
          f"historical={result.get('historical', 0)}; input: {result['config']}")
    for finding in result["findings"]:
        print(f"  {finding}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
