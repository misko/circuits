#!/usr/bin/env python3
"""T1: exact source-line parsing of dedicated, opaque pipeline xtrace."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import check, eq, main, test  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skills" / "pcb-design" / "scripts"))
from pipeline_xtrace import (DriverLine, XTraceValidationError,  # noqa: E402
                             parse_xtrace)


PROJECT = "/observed/work/project-copy"
REPO = "/observed/work/repository"
DIGEST = "a" * 64
DRIVER = "project/03_src/rebuild_all.sh"


def trace(*records):
    return "\n".join(records) + "\n"


def record(line, command, source=f"{PROJECT}/03_src/rebuild_all.sh"):
    return f"+PIPELINE_TRACE:{source}:{line}: {command}"


def parse(text, mapping, **changes):
    args = {
        "project_root": PROJECT,
        "repo_root": REPO,
        "expected_driver_sha256": DIGEST,
        "trace_driver_sha256": DIGEST,
        "trace_complete": True,
    }
    args.update(changes)
    return parse_xtrace(text, mapping, **args)


def rejects(fn, expected, what):
    try:
        fn()
    except XTraceValidationError as exc:
        check(expected in str(exc),
              f"{what}: {exc!s} does not contain {expected!r}")
    else:
        raise AssertionError(f"{what}: malformed trace SHOULD HAVE FAILED")


@test("parser uses exact source lines, ignores declared setup and preserves opaque shell text")
def t_clean_trace():
    mapping = {
        (DRIVER, 42): "P-CHECK",
        (DRIVER, 55): "P-BUILD",
    }
    commands = {
        42: "python check.py --value 'a;b' --literal '$(touch /tmp/never)'",
        43: "echo 'GATE FAILED; $(still-text)'",
        44: "exit 1",
        50: "mkdir -p 06_build",
        55: "env --chdir=03_tscircuit tsci build src/board.tsx",
    }
    observed = parse(
        trace(*(record(line, command) for line, command in commands.items())),
        mapping,
        ignored_lines=((DRIVER, 50),),
        failure_handlers={(DRIVER, 43): "P-CHECK", (DRIVER, 44): "P-CHECK"})
    eq(observed.observed_stage_ids, ("P-CHECK", "P-BUILD"),
       "consecutive handler records collapse into initiating stage")
    eq(observed.collapsed_duplicate_count, 2, "handler duplicate count")
    eq(observed.ignored_record_count, 1, "declared setup count")
    check(observed.fully_mapped, "clean trace retained unmapped records")
    # The payload is tested exactly through an unmapped record below; matching
    # source identity never tokenizes or interprets it.


@test("only consecutive duplicates collapse; a later repeated stage is preserved")
def t_nonconsecutive_repeat():
    mapping = {
        (DRIVER, 10): "P-ONE",
        (DRIVER, 20): "P-TWO",
    }
    observed = parse(trace(
        record(10, "first invocation"),
        record(10, "same invocation handler"),
        record(20, "middle invocation"),
        record(10, "intentional later rerun"),
    ), mapping)
    eq(observed.observed_stage_ids, ("P-ONE", "P-TWO", "P-ONE"),
       "non-consecutive stage identity")
    eq(observed.collapsed_duplicate_count, 1, "only adjacent duplicate collapsed")


@test("unmapped executable lines are returned exactly, never shell-evaluated",
      kind="known_bad")
def t_unmapped_opaque():
    command = "unknown --arg='one;two' --payload=$(echo MUST_NOT_RUN)"
    observed = parse(trace(record(77, command)), {})
    check(not observed.fully_mapped, "unmapped executable was accepted as mapped")
    eq(len(observed.unmapped_executable), 1, "unmapped denominator")
    eq(observed.unmapped_executable[0].location, DriverLine(DRIVER, 77),
       "unmapped exact source location")
    eq(observed.unmapped_executable[0].command, command,
       "semicolon and command substitution remain opaque text")


@test("parser refuses stale driver identity and truncated or empty capture",
      kind="known_bad")
def t_provenance_failures():
    good = trace(record(10, "run"))
    mapping = {(DRIVER, 10): "P-ONE"}
    rejects(lambda: parse(
        good, mapping, trace_driver_sha256="b" * 64),
        "digest differs", "stale traced driver")
    rejects(lambda: parse(good, mapping, trace_complete=False),
            "close witness is absent", "capture-declared truncation")
    rejects(lambda: parse(good.rstrip("\n"), mapping),
            "final newline is absent", "text truncation")
    rejects(lambda: parse("", mapping), "trace is empty", "empty file")
    rejects(lambda: parse("ordinary bash output only\n", mapping),
            "no dedicated", "no dedicated records")


@test("failure handlers require an explicit map and an observed initiating stage",
      kind="known_bad")
def t_handler_failures():
    handler = trace(record(43, "echo failure"))
    # No map: report it as unmapped rather than inventing a stage from text.
    unmapped = parse(handler, {})
    eq(len(unmapped.unmapped_executable), 1, "unmapped handler line")
    eq(unmapped.observed_stage_ids, (), "handler text invented no stage")

    rejects(lambda: parse(
        handler, {}, failure_handlers={(DRIVER, 43): "P-CHECK"}),
        "does not follow", "handler preceding initiation")

    intervening = trace(
        record(42, "check"), record(55, "build"), record(43, "echo failure"))
    rejects(lambda: parse(
        intervening, {(DRIVER, 42): "P-CHECK", (DRIVER, 55): "P-BUILD"},
        failure_handlers={(DRIVER, 43): "P-CHECK"}),
        "does not follow", "handler reaching across another stage")


@test("parser rejects malformed dedicated records, ambiguous maps and foreign sources",
      kind="known_bad")
def t_contract_failures():
    rejects(lambda: parse(
        "+PIPELINE_TRACE:/driver:missing-line command\n", {}),
        "malformed dedicated", "malformed record")
    rejects(lambda: parse(
        trace(record(10, "run")), {(DRIVER, 10): "P-ONE"},
        ignored_lines=((DRIVER, 10),)),
        "multiple dispositions", "mapped and ignored line")
    rejects(lambda: parse(
        trace(record(10, "run", source="/outside/rebuild_all.sh")), {}),
        "outside supplied", "foreign trace source")
    rejects(lambda: parse(
        trace(record(10, "run")), {("03_src/rebuild_all.sh", 10): "P-ONE"}),
        "must begin project/ or repo/", "unscoped mapping key")


if __name__ == "__main__":
    raise SystemExit(main())
