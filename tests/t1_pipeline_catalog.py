#!/usr/bin/env python3
"""T1: strict, non-executing catalog of observed legacy pipeline stages."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import check, eq, main, test  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skills" / "pcb-design" / "scripts"))

from pipeline_catalog import (CatalogValidationError, LegacyPipelineCatalog,  # noqa: E402
                              LegacyStageBinding)


DRIVER = b"#!/bin/sh\nexit 0\n"


def spec(stage_id, *, cost="cheap", lifecycle="schematic", requires=(),
         produces=()):
    return {
        "schema": 1,
        "id": stage_id,
        "owner": "pcb-design",
        "lifecycle": lifecycle,
        "cost": cost,
        "work_class": "local",
        "timeout_s": 60,
        "requires": list(sorted(requires)),
        "produces": list(sorted(produces)),
        "blocks": [],
        "invalidated_by": [],
    }


def binding(sequence, key, stage, *, deps=(), argv=None, builtin=None,
            applicability="APPLIES", reason=None, authority="exit",
            authority_binding=None, paths=()):
    accepted = ([] if applicability == "NOT_APPLICABLE"
                else list(stage["produces"]))
    return {
        "schema": 1,
        "sequence": sequence,
        "legacy_key": key,
        "spec": stage,
        "dependencies": list(sorted(deps)),
        "argv": argv,
        "shell_builtin": builtin,
        "cwd": ".",
        "applicability": applicability,
        "applicability_reason": reason,
        "authority": authority,
        "authority_binding": authority_binding,
        "accepted_output_symbols": accepted,
        "accepted_output_paths": list(sorted(paths)),
    }


def catalog_mapping():
    schematic = spec("P-SCHEMA", produces=("schematic_ready",))
    erc_raw = spec(
        "P-ERC-RAW", cost="bounded", requires=("schematic_ready",),
        produces=("erc_report",))
    erc_verdict = spec(
        "P-ERC-VERDICT", requires=("erc_report",),
        produces=("erc_pass",))
    rf_review = spec(
        "P-RF-REVIEW", cost="review", lifecycle="layout_seal",
        requires=("erc_pass",), produces=("rf_review",))
    return {
        "schema": 1,
        "project_slug": "example-board",
        "driver_relative_path": "03_src/rebuild.sh",
        "driver_sha256": hashlib.sha256(DRIVER).hexdigest(),
        "entrypoint": "rebuild",
        "mode": "full",
        "bindings": [
            binding(
                1, "schematic", schematic,
                argv=["/usr/bin/python3", "generate.py", "$(literal)", ";"],
                paths=("04_kicad/example.kicad_sch",)),
            binding(
                2, "erc-raw", erc_raw, deps=("P-SCHEMA",),
                argv=["kicad-cli", "sch", "erc", "--format", "json"],
                authority="postcheck", authority_binding="erc-verdict",
                paths=("06_build/erc.json",)),
            binding(
                3, "erc-verdict", erc_verdict, deps=("P-ERC-RAW",),
                argv=["/usr/bin/python3", "-c", "grade_report()"]),
            binding(
                4, "rf-review-na", rf_review, deps=("P-ERC-VERDICT",),
                builtin="not_applicable", applicability="NOT_APPLICABLE",
                reason="the subject declares no RF paths"),
        ],
    }


def rejects(mutator, expected, what):
    source = catalog_mapping()
    mutator(source)
    try:
        LegacyPipelineCatalog.from_mapping(source)
    except CatalogValidationError as exc:
        check(expected in str(exc),
              f"{what}: {exc!s} does not contain {expected!r}")
    else:
        raise AssertionError(f"{what}: malformed catalog SHOULD HAVE FAILED")


@test("catalog round-trips exact schema-1 mappings and canonical JSON")
def t_roundtrip():
    source = catalog_mapping()
    catalog = LegacyPipelineCatalog.from_mapping(source)
    eq(catalog.to_mapping(), source, "catalog mapping")
    encoded = catalog.to_json()
    eq(encoded, json.dumps(source, sort_keys=True, separators=(",", ":")),
       "canonical JSON bytes")
    eq(LegacyPipelineCatalog.from_json(encoded), catalog, "JSON round-trip")


@test("catalog derives a StageRegistry and observed order without execution")
def t_registry_and_order():
    catalog = LegacyPipelineCatalog.from_mapping(catalog_mapping())
    eq(catalog.observed_stage_ids(),
       ("P-SCHEMA", "P-ERC-RAW", "P-ERC-VERDICT", "P-RF-REVIEW"),
       "legacy observation order")
    plan = catalog.stage_registry().resolve()
    eq(tuple(item.id for item in plan), catalog.observed_stage_ids(),
       "semantic registry order")


@test("argv remains literal data and is never normalized as a shell command")
def t_argv_is_data():
    catalog = LegacyPipelineCatalog.from_mapping(catalog_mapping())
    argv = catalog.bindings[0].argv
    eq(argv, ("/usr/bin/python3", "generate.py", "$(literal)", ";"),
       "literal argv evidence")
    check(catalog.bindings[0].shell_builtin is None, "argv became a builtin")


@test("explicit shell builtin, N/A reason, and zero accepted outputs survive")
def t_na_builtin():
    catalog = LegacyPipelineCatalog.from_mapping(catalog_mapping())
    row = catalog.bindings[-1]
    eq(row.shell_builtin, "not_applicable", "builtin token")
    eq(row.applicability_reason, "the subject declares no RF paths", "N/A reason")
    eq(row.accepted_output_symbols, (), "N/A accepted symbols")
    eq(row.accepted_output_paths, (), "N/A accepted paths")


@test("postcheck and ignored-until authority point only to later bindings")
def t_deferred_authority():
    source = catalog_mapping()
    source["bindings"][0]["authority"] = "ignored_until"
    source["bindings"][0]["authority_binding"] = "erc-verdict"
    catalog = LegacyPipelineCatalog.from_mapping(source)
    eq(catalog.bindings[0].authority_binding, "erc-verdict", "authority boundary")
    eq(catalog.bindings[1].authority, "postcheck", "postcheck semantics")


@test("catalog checks exact driver bytes without reading or executing a path")
def t_driver_digest():
    catalog = LegacyPipelineCatalog.from_mapping(catalog_mapping())
    check(catalog.driver_matches(DRIVER), "exact driver bytes did not match")
    check(not catalog.driver_matches(DRIVER + b"# changed\n"),
          "changed driver bytes matched")


@test("catalog REFUSES unknown fields, schemas, and duplicate JSON keys",
      kind="known_bad")
def t_exact_schema():
    rejects(lambda x: x.update(extra="hidden"), "unknown=['extra']",
            "catalog unknown field")
    rejects(lambda x: x.update(schema=2), "only schema 1",
            "catalog future schema")
    rejects(lambda x: x["bindings"][0].update(command="shell string"),
            "unknown=['command']", "binding unknown field")
    text = LegacyPipelineCatalog.from_mapping(catalog_mapping()).to_json()
    duplicate = text.replace('"schema":1', '"schema":1,"schema":1', 1)
    try:
        LegacyPipelineCatalog.from_json(duplicate)
    except CatalogValidationError as exc:
        check("duplicate JSON field" in str(exc), "duplicate key diagnosis")
    else:
        raise AssertionError("duplicate JSON field was accepted")


@test("catalog REFUSES absolute, escaping, non-normal, and host paths",
      kind="known_bad")
def t_paths():
    for value, expected in (
        ("/tmp/rebuild.sh", "absolute paths"),
        ("../rebuild.sh", "non-escaping"),
        ("03_src/../rebuild.sh", "non-escaping"),
        ("03_src\\rebuild.sh", "backslashes"),
        ("03_src//rebuild.sh", "normalized POSIX"),
        (".", "not a file path"),
    ):
        rejects(lambda x, value=value: x.update(driver_relative_path=value),
                expected, f"driver path {value!r}")
    rejects(lambda x: x["bindings"][0].update(cwd="../other"),
            "non-escaping", "escaping cwd")
    rejects(lambda x: x["bindings"][0].update(
        accepted_output_paths=["06_build/../release.zip"]),
        "non-escaping", "escaping output path")


@test("catalog REFUSES shell strings and ambiguous command evidence",
      kind="known_bad")
def t_command_union():
    rejects(lambda x: x["bindings"][0].update(argv="tool --flag"),
            "argv must be a JSON list", "shell command string")
    rejects(lambda x: x["bindings"][0].update(shell_builtin="source"),
            "exactly one", "argv plus builtin")
    rejects(lambda x: x["bindings"][0].update(argv=None),
            "exactly one", "missing command evidence")
    rejects(lambda x: x["bindings"][0].update(argv=[]),
            "must contain an executable", "empty argv")


@test("catalog REFUSES duplicate keys, stage ids, and sequence drift",
      kind="known_bad")
def t_sequence_identity():
    rejects(lambda x: x["bindings"][1].update(sequence=1),
            "unique, contiguous", "duplicate sequence")
    rejects(lambda x: x["bindings"][1].update(sequence=3),
            "unique, contiguous", "sequence gap")
    rejects(lambda x: x["bindings"][1].update(legacy_key="schematic"),
            "legacy_key values must be unique", "duplicate legacy key")
    rejects(lambda x: x["bindings"][1]["spec"].update(id="P-SCHEMA"),
            "StageSpec ids must be unique", "duplicate stage id")


@test("catalog REFUSES unordered, unknown, later, or omitted dependencies",
      kind="known_bad")
def t_dependencies():
    source = catalog_mapping()
    source["bindings"][2]["dependencies"] = ["P-SCHEMA", "P-ERC-RAW"]
    try:
        LegacyPipelineCatalog.from_mapping(source)
    except CatalogValidationError as exc:
        check("sorted and unique" in str(exc), "unsorted dependency diagnosis")
    else:
        raise AssertionError("unsorted dependencies were accepted")
    rejects(lambda x: x["bindings"][1].update(dependencies=["P-MISSING"]),
            "is unknown", "unknown dependency")
    rejects(lambda x: x["bindings"][0].update(dependencies=["P-ERC-RAW"]),
            "must precede", "future dependency")
    rejects(lambda x: x["bindings"][1].update(dependencies=[]),
            "internal producer P-SCHEMA", "omitted data producer")


@test("catalog REFUSES output claims inconsistent with applicability or spec",
      kind="known_bad")
def t_outputs():
    rejects(lambda x: x["bindings"][0].update(accepted_output_symbols=[]),
            "must equal StageSpec.produces", "missing accepted symbol")
    rejects(lambda x: x["bindings"][0].update(
        accepted_output_symbols=["invented_output"]),
        "must equal StageSpec.produces", "invented accepted symbol")
    rejects(lambda x: x["bindings"][-1].update(
        accepted_output_paths=["06_build/skipped.json"]),
        "cannot accept output", "N/A output path")
    rejects(lambda x: x["bindings"][0].update(
        accepted_output_paths=["z/report", "a/report"]),
        "sorted and unique", "unordered output paths")


@test("catalog REFUSES applicability excuses and malformed authority links",
      kind="known_bad")
def t_applicability_authority():
    rejects(lambda x: x["bindings"][-1].update(applicability_reason=" "),
            "requires a reason", "blank N/A reason")
    rejects(lambda x: x["bindings"][0].update(applicability_reason="maybe"),
            "APPLIES requires null", "APPLIES excuse")
    rejects(lambda x: x["bindings"][0].update(authority_binding="erc-verdict"),
            "exit authority requires null", "exit authority reference")
    rejects(lambda x: x["bindings"][0].update(
        authority="postcheck", authority_binding="missing"),
        "is unknown", "unknown postcheck")
    rejects(lambda x: x["bindings"][2].update(
        authority="ignored_until", authority_binding="schematic"),
        "must refer to a later binding", "backward authority")


@test("catalog REFUSES malformed slugs, tokens, digests, and non-byte checks",
      kind="known_bad")
def t_scalar_types():
    rejects(lambda x: x.update(project_slug="Example Board"),
            "project_slug", "project slug")
    rejects(lambda x: x.update(entrypoint="rebuild all"),
            "entrypoint", "entrypoint token")
    rejects(lambda x: x.update(mode="FULL"), "mode", "mode token")
    rejects(lambda x: x.update(driver_sha256="A" * 64),
            "64 lowercase", "driver digest")
    catalog = LegacyPipelineCatalog.from_mapping(catalog_mapping())
    try:
        catalog.driver_matches("not bytes")
    except CatalogValidationError as exc:
        check("exact bytes" in str(exc), "driver byte type diagnosis")
    else:
        raise AssertionError("decoded driver text was accepted as exact bytes")


if __name__ == "__main__":
    raise SystemExit(main())
