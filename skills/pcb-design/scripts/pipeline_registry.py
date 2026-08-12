#!/usr/bin/env python3
"""Validated stage registry and non-authoritative shadow-plan comparison.

This module deliberately does not execute commands.  During migration it
turns typed ``StageSpec`` declarations into a deterministic dependency plan
and compares that plan with the order observed from the legacy pipeline.
Only a later, measured migration decision may make the plan authoritative.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from pipeline_contract import COSTS, LIFECYCLES, StageSpec


class RegistryValidationError(ValueError):
    """Stage declarations cannot form a complete deterministic plan."""


_LIFECYCLE_ORDER = {
    name: index for index, name in enumerate((
        "commission", "architecture", "sourcing", "schematic", "placement",
        "routing", "layout_seal", "fabrication", "release_staging",
        "release_seal", "publication", "first_article", "production",
    ))
}
_COST_ORDER = {
    name: index for index, name in enumerate((
        "cheap", "bounded", "external", "review", "operator",
    ))
}

# Keep the registry's ordering vocabulary tied to the public contract.  These
# assertions fail at import if a future schema edit forgets to update planning.
if set(_LIFECYCLE_ORDER) != set(LIFECYCLES):  # pragma: no cover - schema guard
    raise RuntimeError("pipeline registry lifecycle order is incomplete")
if set(_COST_ORDER) != set(COSTS):  # pragma: no cover - schema guard
    raise RuntimeError("pipeline registry cost order is incomplete")


@dataclass(frozen=True)
class ShadowPlanComparison:
    """Exact comparison between a declarative plan and one observed run."""

    expected: tuple[str, ...]
    observed: tuple[str, ...]
    missing: tuple[str, ...]
    unexpected: tuple[str, ...]
    first_divergence: int | None

    @property
    def matches(self) -> bool:
        return self.expected == self.observed

    def to_mapping(self) -> dict[str, object]:
        return {
            "matches": self.matches,
            "expected": list(self.expected),
            "observed": list(self.observed),
            "missing": list(self.missing),
            "unexpected": list(self.unexpected),
            "first_divergence": self.first_divergence,
        }


class StageRegistry:
    """Closed set of typed stages with single-producer data dependencies."""

    def __init__(self, specs: Iterable[StageSpec]) -> None:
        material = tuple(specs)
        if not material:
            raise RegistryValidationError("registry must declare at least one stage")
        if any(not isinstance(spec, StageSpec) for spec in material):
            raise RegistryValidationError("registry accepts only StageSpec values")

        self._by_id: dict[str, StageSpec] = {}
        self._producer: dict[str, str] = {}
        self._required_symbols: set[str] = set()
        for spec in material:
            if spec.id in self._by_id:
                raise RegistryValidationError(f"duplicate stage id: {spec.id}")
            self._by_id[spec.id] = spec
            self._required_symbols.update(spec.requires)
            overlap = set(spec.requires) & set(spec.produces)
            if overlap:
                raise RegistryValidationError(
                    f"{spec.id}: stage requires its own output(s): "
                    + ", ".join(sorted(overlap)))
            for symbol in spec.produces:
                prior = self._producer.get(symbol)
                if prior is not None:
                    raise RegistryValidationError(
                        f"output {symbol!r} has multiple producers: "
                        f"{prior}, {spec.id}")
                self._producer[symbol] = spec.id

        # Validate the complete declaration for cycles without requiring every
        # external fact to have an in-registry producer.
        self._topological_order(set(self._by_id), allow_external=True,
                                available=frozenset())

    @property
    def stages(self) -> tuple[StageSpec, ...]:
        return tuple(self._by_id[key] for key in sorted(self._by_id))

    def get(self, stage_id: str) -> StageSpec:
        try:
            return self._by_id[stage_id]
        except KeyError as exc:
            raise RegistryValidationError(f"unknown stage id: {stage_id}") from exc

    def _closure(self, targets: set[str], available: frozenset[str]) -> set[str]:
        selected: set[str] = set()
        pending = list(targets)
        while pending:
            stage_id = pending.pop()
            if stage_id in selected:
                continue
            spec = self.get(stage_id)
            selected.add(stage_id)
            for symbol in spec.requires:
                if symbol in available:
                    continue
                producer = self._producer.get(symbol)
                if producer is None:
                    raise RegistryValidationError(
                        f"{stage_id}: requirement {symbol!r} has no producer "
                        "and is not declared available")
                pending.append(producer)
        return selected

    def _topological_order(
        self,
        selected: set[str],
        *,
        available: frozenset[str],
        allow_external: bool,
    ) -> tuple[StageSpec, ...]:
        dependencies: dict[str, set[str]] = {}
        for stage_id in selected:
            spec = self._by_id[stage_id]
            dependencies[stage_id] = set()
            for symbol in spec.requires:
                if symbol in available:
                    continue
                producer = self._producer.get(symbol)
                if producer in selected:
                    dependencies[stage_id].add(producer)
                elif producer is None and not allow_external:
                    raise RegistryValidationError(
                        f"{stage_id}: requirement {symbol!r} is unavailable")

        def priority(stage_id: str) -> tuple[int, int, str]:
            spec = self._by_id[stage_id]
            # Dependencies are the hard constraint.  Among runnable work,
            # cheap stages go first; lifecycle then supplies a stable tie-break.
            return (_COST_ORDER[spec.cost],
                    _LIFECYCLE_ORDER[spec.lifecycle], spec.id)

        remaining = set(selected)
        ordered: list[StageSpec] = []
        while remaining:
            ready = sorted(
                (stage_id for stage_id in remaining
                 if not (dependencies[stage_id] & remaining)),
                key=priority,
            )
            if not ready:
                cycle = ", ".join(sorted(remaining))
                raise RegistryValidationError(
                    f"stage dependency cycle among: {cycle}")
            # Select one stage, then recompute.  A cheap stage unblocked by
            # this choice must be allowed to overtake already-ready network or
            # review work; batching the whole ready set would silently lose
            # the cheap-first guarantee.
            stage_id = ready[0]
            ordered.append(self._by_id[stage_id])
            remaining.remove(stage_id)
        return tuple(ordered)

    def resolve(
        self,
        target_stage_ids: Sequence[str] | None = None,
        *,
        available: Iterable[str] = (),
    ) -> tuple[StageSpec, ...]:
        """Resolve target dependency closure and schedule cheap runnable work.

        ``available`` names typed facts supplied by the subject or environment;
        everything else must have exactly one selected producer.  Resolving all
        stages therefore requires callers to declare every external input.
        """

        facts = frozenset(available)
        if any(not isinstance(item, str) or not item for item in facts):
            raise RegistryValidationError(
                "available facts must be non-empty symbolic strings")
        unused = facts - self._required_symbols
        if unused:
            raise RegistryValidationError(
                "available fact(s) are not required by this registry: "
                + ", ".join(sorted(unused)))
        targets = (set(self._by_id) if target_stage_ids is None
                   else set(target_stage_ids))
        if not targets:
            raise RegistryValidationError("at least one target stage is required")
        selected = self._closure(targets, facts)
        return self._topological_order(
            selected, available=facts, allow_external=False)

    def compare_shadow(
        self,
        observed_stage_ids: Sequence[str],
        target_stage_ids: Sequence[str] | None = None,
        *,
        available: Iterable[str] = (),
    ) -> ShadowPlanComparison:
        """Compare without executing, promoting, or changing a legacy run."""

        expected = tuple(
            spec.id for spec in self.resolve(target_stage_ids, available=available))
        observed = tuple(observed_stage_ids)
        expected_set = set(expected)
        observed_set = set(observed)
        limit = min(len(expected), len(observed))
        divergence = next(
            (index for index in range(limit)
             if expected[index] != observed[index]),
            None,
        )
        if divergence is None and len(expected) != len(observed):
            divergence = limit
        return ShadowPlanComparison(
            expected=expected,
            observed=observed,
            missing=tuple(item for item in expected if item not in observed_set),
            unexpected=tuple(item for item in observed if item not in expected_set),
            first_divergence=divergence,
        )


__all__ = [
    "RegistryValidationError", "ShadowPlanComparison", "StageRegistry",
]
