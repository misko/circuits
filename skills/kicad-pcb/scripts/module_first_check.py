#!/usr/bin/env python3
"""P-MOD: enforce the module-first architecture contract.

Graded input: ``PROJECT/03_src/rules/integration.yaml`` and every used
``PROJECT/02_parts/*/part.yaml`` dossier.  An adopted project must account for
each complex subsystem as a real module or as an evidenced bare-IC exception.
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
    r"usb[_ -]?(?:hub|pd)?[_ -]?controller|ethernet[_ -]?(?:phy|controller)|"
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


def _exception_errors(root: Path, label: str, value: Any) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label}: bare_ic requires an exception mapping"]
    errors = []
    if not _text(value.get("binding_requirement"), 30):
        errors.append(f"{label}: exception.binding_requirement needs the binding "
                      "requirement a module cannot meet")
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
                errors.append(f"{at}.rejected_because needs a binding mismatch")
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

    if policy.get("schema") != 1:
        findings.append("integration.yaml schema must be 1")
    if policy.get("default") != "prefer_module":
        findings.append("integration.yaml default must be prefer_module")
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
    graded = modules = bare = 0
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
            errors = _exception_errors(root, at, selection.get("exception"))
            findings.extend(errors)
            if not errors and not part.is_module:
                bare += 1
        else:
            findings.append(f"{at}.implementation must be module or bare_ic")
        graded += 1

    omitted = [part.mpn for part in scoped if part.path not in chosen]
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
            "bare": bare, "findings": findings}


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
          f"bare_exceptions={result['bare']}; input: {result['config']}")
    for finding in result["findings"]:
        print(f"  {finding}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
