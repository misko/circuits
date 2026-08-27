#!/usr/bin/env python3
"""Validate governed Markdown engineering reports and their local evidence links."""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import unquote, urlsplit

import yaml


REPORT_NAME = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
LINK = re.compile(
    r"(?P<image>!)?\[(?P<label>[^\]]*)\]"
    r"\((?P<target><[^>]+>|[^\s)]+)(?:\s+[\"'][^\"']*[\"'])?\)"
)
RAW_HTML = re.compile(
    r"<(?:script|style|iframe|object|embed|img|table|div|span|p|a|h[1-6])\b",
    re.IGNORECASE,
)
REQUIRED_FIELDS = {
    "schema", "kind", "report_id", "title", "subtitle", "project", "date",
    "status", "evidence_status",
}
REQUIRED_SECTIONS = (
    "Executive conclusion",
    "Question and scope",
    "Evidence boundary",
    "Findings",
    "Recommendations",
    "Validation plan",
    "Source register",
)
EVIDENCE_LABELS = ("MEASURED", "DATASHEET", "CITED", "INFERRED", "PROPOSED", "OWED")


class ReportError(ValueError):
    """The report or one of its declared local subjects is invalid."""


class UniqueLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def _unique_mapping(loader: UniqueLoader, node: yaml.Node, deep: bool = False) -> dict[Any, Any]:
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ReportError(f"duplicate frontmatter key: {key!r}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _unique_mapping,
)


def _absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _regular_file(path: Path, label: str) -> Path:
    path = _absolute(path)
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        try:
            info = current.lstat()
        except OSError as exc:
            raise ReportError(f"{label}: cannot inspect {current}: {exc}") from exc
        if stat.S_ISLNK(info.st_mode):
            raise ReportError(f"{label}: symlinks are forbidden: {current}")
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode):
        raise ReportError(f"{label}: expected an ordinary file: {path}")
    if info.st_nlink != 1:
        raise ReportError(f"{label}: hard-linked files are forbidden: {path}")
    return path


def _read_stable_utf8(path: Path, label: str) -> str:
    path = _regular_file(path, label)
    before = path.stat()
    try:
        data = path.read_bytes()
        text = data.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ReportError(f"{label}: expected readable UTF-8: {exc}") from exc
    after = path.stat()
    identity = lambda item: (item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns)
    if identity(before) != identity(after) or len(data) != after.st_size:
        raise ReportError(f"{label}: file changed while being read: {path}")
    return text


def _git_root(report: Path) -> Path:
    process = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=report.parent,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=20,
    )
    if process.returncode:
        raise ReportError(f"report is not inside a Git worktree: {process.stderr.strip()}")
    return _absolute(Path(process.stdout.strip()))


def _is_tracked(root: Path, path: Path) -> bool:
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError:
        return False
    process = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", relative],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=20,
    )
    return process.returncode == 0


def _frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        raise ReportError("missing YAML frontmatter")
    closing = text.find("\n---\n", 4)
    if closing < 0:
        raise ReportError("unterminated YAML frontmatter")
    raw = text[4:closing]
    try:
        mapping = yaml.load(raw, Loader=UniqueLoader)
    except (yaml.YAMLError, ReportError) as exc:
        raise ReportError(f"invalid frontmatter: {exc}") from exc
    if not isinstance(mapping, dict):
        raise ReportError("frontmatter must be a mapping")
    keys = set(mapping)
    if keys != REQUIRED_FIELDS:
        raise ReportError(
            f"frontmatter fields differ: missing={sorted(REQUIRED_FIELDS - keys)} "
            f"extra={sorted(keys - REQUIRED_FIELDS)}"
        )
    return mapping, text[closing + 5:]


def _date_text(value: Any) -> str:
    if isinstance(value, dt.date) and not isinstance(value, dt.datetime):
        return value.isoformat()
    if isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        try:
            return dt.date.fromisoformat(value).isoformat()
        except ValueError as exc:
            raise ReportError(f"frontmatter date is invalid: {value}") from exc
    raise ReportError("frontmatter date must be YYYY-MM-DD")


def _validate_metadata(report: Path, mapping: dict[str, Any], body: str) -> None:
    if not REPORT_NAME.fullmatch(report.name):
        raise ReportError("report filename must be YYYY-MM-DD-<lower-kebab-slug>.md")
    if report.parent.name != "reports" or report.parent.parent.name != "01_docs":
        raise ReportError("report must be a direct child of 01_docs/reports")
    if mapping["schema"] != 1 or mapping["kind"] != "pcb-human-report":
        raise ReportError("frontmatter schema/kind must be 1/pcb-human-report")
    if mapping["report_id"] != report.stem:
        raise ReportError("frontmatter report_id must equal the filename stem")
    date = _date_text(mapping["date"])
    if not report.stem.startswith(date + "-"):
        raise ReportError("frontmatter date must equal the filename date prefix")
    project = report.parents[2].name
    if mapping["project"] != project:
        raise ReportError(f"frontmatter project must equal project folder {project!r}")
    if mapping["status"] not in {"DRAFT", "REVIEWED", "SUPERSEDED"}:
        raise ReportError("frontmatter status is outside the closed vocabulary")
    if mapping["evidence_status"] not in {"INCOMPLETE", "MIXED", "MEASURED"}:
        raise ReportError("frontmatter evidence_status is outside the closed vocabulary")
    for field in ("title", "subtitle"):
        if not isinstance(mapping[field], str) or not mapping[field].strip():
            raise ReportError(f"frontmatter {field} must be a non-empty string")
    for heading in REQUIRED_SECTIONS:
        if not re.search(rf"^## {re.escape(heading)}[ \t]*$", body, re.MULTILINE):
            raise ReportError(f"missing required section: {heading}")
    if not any(
        f"**{label}:**" in body or f"**{label}**" in body
        for label in EVIDENCE_LABELS
    ):
        raise ReportError("report never uses the governed evidence vocabulary")
    if mapping["evidence_status"] == "MEASURED" and (
        "**PROPOSED**" in body or "**PROPOSED:**" in body or
        "**OWED**" in body or "**OWED:**" in body
    ):
        raise ReportError("MEASURED report still contains PROPOSED or OWED claims")
    if RAW_HTML.search(body):
        raise ReportError("raw HTML is forbidden in project reports")


def audit(report: Path, *, allow_untracked: bool = False) -> dict[str, int]:
    report = _regular_file(report, "report")
    text = _read_stable_utf8(report, "report")
    mapping, body = _frontmatter(text)
    _validate_metadata(report, mapping, body)
    root = _git_root(report)
    if not allow_untracked and not _is_tracked(root, report):
        raise ReportError(f"report is not tracked: {report.relative_to(root)}")

    counts = {"local_links": 0, "remote_links": 0, "images": 0}
    for match in LINK.finditer(body):
        raw = match.group("target")
        target = raw[1:-1] if raw.startswith("<") and raw.endswith(">") else raw
        split = urlsplit(target)
        is_image = bool(match.group("image"))
        if is_image:
            counts["images"] += 1
        if split.scheme or split.netloc:
            if split.scheme != "https" or not split.netloc:
                raise ReportError(f"external links must use HTTPS: {target}")
            if is_image:
                raise ReportError(f"remote images are forbidden: {target}")
            counts["remote_links"] += 1
            continue
        if target.startswith("#"):
            continue
        path_text = unquote(split.path)
        if not path_text:
            continue
        candidate = _absolute(report.parent / path_text)
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise ReportError(f"local link escapes the repository: {target}") from exc
        candidate = _regular_file(candidate, f"local link {target!r}")
        if not allow_untracked and not _is_tracked(root, candidate):
            raise ReportError(f"local link target is not tracked: {candidate.relative_to(root)}")
        counts["local_links"] += 1
    return counts


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument(
        "--allow-untracked",
        action="store_true",
        help="authoring-only: validate ordinary local bytes before Git staging",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        counts = audit(args.report, allow_untracked=args.allow_untracked)
    except ReportError as exc:
        print(f"REPORT-AUDIT FAIL: {exc}", file=sys.stderr)
        return 1
    print(
        "REPORT-AUDIT PASS: reports=1 "
        f"local_links={counts['local_links']} remote_links={counts['remote_links']} "
        f"images={counts['images']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
