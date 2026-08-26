#!/usr/bin/env python3
"""T1: USB v4 placement-review preparation preserves review authority."""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import check, eq, main, test  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT / "archived_projects" / "usb-hub-3s-v4"
ADAPTER = PROJECT / "03_src" / "prepare_placement_review.sh"
FULL = PROJECT / "03_src" / "rebuild_all.sh"
REUSE = PROJECT / "03_src" / "rebuild_reuse.sh"


def adapter_source() -> str:
    return ADAPTER.read_text(encoding="utf-8")


def validate_adapter(source: str) -> None:
    """Reject authority escalation, mutable requests, and unbounded tools."""
    if "SOUND" in source:
        raise ValueError("placement producer contains the human acceptance token")
    if "a-render_verdict: INCOMPLETE" not in source:
        raise ValueError("A-RENDER request is not explicitly incomplete")
    if 'REQUEST_DIR="$REQUEST_ROOT/$SUBJECT_ID"' not in source:
        raise ValueError("review request is not content-addressed")
    if "immutable request was modified" not in source:
        raise ValueError("existing immutable request is not hash-checked")
    if 'mv -T "$TMP_DIR" "$REQUEST_DIR"' not in source:
        raise ValueError("complete request is not atomically published")
    if "08_reviews" in source:
        raise ValueError("producer addresses the tracked human-witness directory")

    deadlines = re.findall(
        r"timeout --foreground --kill-after=5s (\d+)s\s+"
        r"(?:\\\s*)?(?:\"\$PY\"|kicad-cli)", source)
    eq(tuple(deadlines), ("60", "90", "90"),
       "promoted check plus two render deadlines")


def subject_identity_keys(source: str) -> tuple[str, ...]:
    match = re.search(
        r'identity = \{\n(?P<body>.*?)\n\}\n'
        r'payload = json\.dumps\(identity', source, re.S)
    check(match is not None, "semantic subject identity block missing")
    return tuple(re.findall(r'^    "([a-z0-9_]+)":',
                            match.group("body"), re.M))


@test("USB placement review producer is incomplete and immutable by construction")
def t_clean_adapter_contract():
    source = adapter_source()
    validate_adapter(source)
    eq(source.count('f"prep_r0_semantic_sha256: {prep_semantic_hash}"'), 1,
       "A-RENDER prepared-r0 identity header")


@test("USB review subject identity excludes process-only raw config bytes")
def t_semantic_subject_identity():
    eq(subject_identity_keys(adapter_source()), (
        "schema",
        "board_sha256",
        "prepared_r0_semantic_sha256",
        "placement_drc_semantic_sha256",
        "parts_sha256",
        "design_rules_sha256",
    ), "human-review invalidation set")


@test("USB boundary pointer is truthful for admissible and incomplete outcomes")
def t_pointer_dual_outcome():
    source = adapter_source()
    check("write_current_pointer ALREADY_ADMISSIBLE" in source,
          "already-admissible run does not replace a stale pointer")
    check('if status == "INCOMPLETE":' in source,
          "incomplete pointer does not name commissioned artifacts conditionally")
    check('elif status != "ALREADY_ADMISSIBLE":' in source,
          "pointer status vocabulary is not closed")
    already = source.index("write_current_pointer ALREADY_ADMISSIBLE")
    request = source.index('if [ -d "$REQUEST_DIR" ]')
    check(already < request,
          "admissible evidence incorrectly enters commission/request handling")


@test("Both USB drivers prepare the exact review request before the authority gate")
def t_driver_order():
    for path in (FULL, REUSE):
        source = path.read_text(encoding="utf-8")
        prep = source.index("route_and_stitch_generic.py\" prep")
        commission = source.index("placement_review_prepare", prep)
        authority = source.index("pre_route_review_check.py\" . --phase placement",
                                 commission)
        check(prep < commission < authority,
              f"{path.name} placement-review order")
        window = source[commission - 80:commission + 180]
        check("pcb_flow.py" in window or "run_stage" in window,
              f"{path.name} commission lacks bounded runner")


@test("USB review request producer REFUSES an acceptance-token mutation",
      kind="known_bad")
def t_acceptance_mutation_refused():
    broken = adapter_source().replace(
        "a-render_verdict: INCOMPLETE", "a-render-verdict: SOUND", 1)
    try:
        validate_adapter(broken)
    except ValueError as exc:
        check("acceptance token" in str(exc), f"acceptance diagnosis: {exc}")
    else:
        raise AssertionError("acceptance-emitting producer SHOULD HAVE FAILED")


@test("USB review request producer REFUSES an unbounded-render mutation",
      kind="known_bad")
def t_unbounded_render_refused():
    broken = adapter_source().replace(
        "timeout --foreground --kill-after=5s 90s ", "", 1)
    try:
        validate_adapter(broken)
    except AssertionError as exc:
        check("deadlines" in str(exc), f"deadline diagnosis: {exc}")
    else:
        raise AssertionError("unbounded render producer SHOULD HAVE FAILED")


@test("USB review request producer REFUSES a mutable stable-directory mutation",
      kind="known_bad")
def t_mutable_request_refused():
    broken = adapter_source().replace(
        'REQUEST_DIR="$REQUEST_ROOT/$SUBJECT_ID"',
        'REQUEST_DIR="$REQUEST_ROOT/current"', 1)
    try:
        validate_adapter(broken)
    except ValueError as exc:
        check("content-addressed" in str(exc), f"immutability diagnosis: {exc}")
    else:
        raise AssertionError("mutable request producer SHOULD HAVE FAILED")


if __name__ == "__main__":
    raise SystemExit(main())
