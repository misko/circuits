#!/usr/bin/env python3
"""T1: declarative stage registry and non-authoritative shadow planning."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import check, eq, main, test  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skills" / "pcb-design" / "scripts"))
from pipeline_contract import StageSpec  # noqa: E402
from pipeline_registry import RegistryValidationError, StageRegistry  # noqa: E402


def spec(stage_id, *, cost="cheap", lifecycle="schematic", requires=(), produces=()):
    return StageSpec(
        id=stage_id,
        owner="pcb-design",
        lifecycle=lifecycle,
        cost=cost,
        work_class="network" if cost == "external" else "local",
        timeout_s=30,
        requires=tuple(sorted(requires)),
        produces=tuple(sorted(produces)),
        blocks=(),
        invalidated_by=(),
    )


def fixture_registry():
    return StageRegistry((
        spec("P-SCHEMA", produces=("schema_valid",)),
        spec("P-FETCH", cost="external", lifecycle="sourcing",
             requires=("part_codes",), produces=("catalog_facts",)),
        spec("P-BUILD", cost="bounded", requires=("schema_valid",),
             produces=("generated_schematic",)),
        spec("P-REVIEW", cost="review", requires=("generated_schematic",),
             produces=("schematic_review",)),
    ))


@test("registry resolves dependencies and orders cheap runnable work first")
def t_resolve():
    registry = fixture_registry()
    plan = registry.resolve(available=("part_codes",))
    eq(tuple(item.id for item in plan),
       ("P-SCHEMA", "P-BUILD", "P-FETCH", "P-REVIEW"),
       "deterministic cheap-first plan")


@test("targeted shadow plan contains only the required closure")
def t_target_closure():
    registry = fixture_registry()
    plan = registry.resolve(("P-REVIEW",), available=("part_codes",))
    eq(tuple(item.id for item in plan),
       ("P-SCHEMA", "P-BUILD", "P-REVIEW"), "review closure")


@test("shadow comparison reports exact agreement without executing stages")
def t_shadow_agreement():
    registry = fixture_registry()
    expected = ("P-SCHEMA", "P-BUILD", "P-FETCH", "P-REVIEW")
    comparison = registry.compare_shadow(expected, available=("part_codes",))
    check(comparison.matches, "equal shadow plan did not match")
    eq(comparison.first_divergence, None, "agreement divergence")


@test("shadow comparison REFUSES a reordered legacy observation", kind="known_bad")
def t_shadow_order_mismatch():
    registry = fixture_registry()
    observed = ("P-FETCH", "P-SCHEMA", "P-BUILD", "P-REVIEW")
    comparison = registry.compare_shadow(observed, available=("part_codes",))
    check(not comparison.matches, "reordered legacy plan was accepted")
    eq(comparison.first_divergence, 0, "first order divergence")


@test("registry REFUSES an unresolved requirement", kind="known_bad")
def t_missing_requirement():
    registry = fixture_registry()
    try:
        registry.resolve(("P-FETCH",))
    except RegistryValidationError as exc:
        check("has no producer" in str(exc), "missing requirement diagnosis")
    else:
        raise AssertionError("unresolved external fact entered the plan")


@test("registry REFUSES multiple producers for one fact", kind="known_bad")
def t_duplicate_producer():
    try:
        StageRegistry((
            spec("P-ONE", produces=("same_fact",)),
            spec("P-TWO", produces=("same_fact",)),
        ))
    except RegistryValidationError as exc:
        check("multiple producers" in str(exc), "producer collision diagnosis")
    else:
        raise AssertionError("ambiguous fact producer was accepted")


@test("registry REFUSES a dependency cycle", kind="known_bad")
def t_cycle():
    try:
        StageRegistry((
            spec("P-ONE", requires=("fact_two",), produces=("fact_one",)),
            spec("P-TWO", requires=("fact_one",), produces=("fact_two",)),
        ))
    except RegistryValidationError as exc:
        check("cycle" in str(exc), "cycle diagnosis")
    else:
        raise AssertionError("cyclic registry was accepted")


if __name__ == "__main__":
    raise SystemExit(main())
