#!/usr/bin/env python3
"""Create a fail-closed PCB project scaffold from the skill-owned templates.

The destination must be a new direct child of an existing projects directory.
This command never follows symlinks and never merges with an existing path.
It resolves the requested schema-1 capability profile through the PCB skill's
reference router before creating the destination.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import sys
from datetime import datetime
from pathlib import Path
from typing import Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[2]
PCB_TEMPLATES = ROOT / "skills/pcb-design/templates"
ENCLOSURE_ASSETS = ROOT / "skills/pcb-enclosure/assets"

sys.path.insert(0, str(SCRIPT_DIR))
from skill_reference_router import (  # noqa: E402
    FIRMWARE,
    SIGNAL_INTEGRITY,
    TARGETS,
    CapabilityProfile,
    RouterValidationError,
    resolve_profile,
)


BRIEF_BEGIN = "<!-- prompt-verbatim-begin -->"
BRIEF_END = "<!-- prompt-verbatim-end -->"
PROJECT_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class CommissionError(ValueError):
    """The requested scaffold is unsafe, invalid, or incomplete."""


def _absolute(path: Path) -> Path:
    """Return an absolute lexical path without resolving symlinks."""
    return Path(os.path.abspath(os.fspath(path)))


def _path_components(path: Path) -> list[Path]:
    absolute = _absolute(path)
    parts = absolute.parts
    current = Path(parts[0])
    result = [current]
    for part in parts[1:]:
        current = current / part
        result.append(current)
    return result


def _require_no_symlink_components(path: Path, label: str) -> Path:
    absolute = _absolute(path)
    for component in _path_components(absolute):
        try:
            mode = component.lstat().st_mode
        except FileNotFoundError as exc:
            raise CommissionError(f"{label}: path does not exist: {component}") from exc
        except OSError as exc:
            raise CommissionError(f"{label}: cannot inspect {component}: {exc}") from exc
        if stat.S_ISLNK(mode):
            raise CommissionError(f"{label}: symlink path component is forbidden: {component}")
    return absolute


def _require_directory(path: Path, label: str) -> Path:
    absolute = _require_no_symlink_components(path, label)
    try:
        mode = absolute.lstat().st_mode
    except OSError as exc:  # pragma: no cover - component walk already reports this
        raise CommissionError(f"{label}: cannot inspect {absolute}: {exc}") from exc
    if not stat.S_ISDIR(mode):
        raise CommissionError(f"{label}: expected an ordinary directory: {absolute}")
    return absolute


def _read_regular_utf8(path: Path, label: str) -> tuple[str, bytes]:
    absolute = _require_no_symlink_components(path, label)
    try:
        mode = absolute.lstat().st_mode
    except OSError as exc:  # pragma: no cover - component walk already reports this
        raise CommissionError(f"{label}: cannot inspect {absolute}: {exc}") from exc
    if not stat.S_ISREG(mode):
        raise CommissionError(f"{label}: expected an ordinary file: {absolute}")
    try:
        data = absolute.read_bytes()
        text = data.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise CommissionError(f"{label}: expected readable UTF-8: {exc}") from exc
    return text, data


def _template_bytes(path: Path) -> bytes:
    _, data = _read_regular_utf8(path, f"template {path.relative_to(ROOT)}")
    return data


def _add_file(
    plan: dict[Path, tuple[bytes, int]],
    destination: Path,
    data: bytes,
    mode: int = 0o644,
) -> None:
    if destination.is_absolute() or ".." in destination.parts:
        raise CommissionError(f"unsafe scaffold path: {destination}")
    if destination in plan:
        raise CommissionError(f"duplicate scaffold path: {destination}")
    plan[destination] = (data, mode)


def _add_template_tree(
    plan: dict[Path, tuple[bytes, int]],
    source_root: Path,
    destination_root: Path,
    *,
    excluded: frozenset[Path] = frozenset(),
) -> None:
    for source in sorted(source_root.rglob("*")):
        if source.is_dir():
            continue
        relative = source.relative_to(source_root)
        if relative in excluded:
            continue
        data = _template_bytes(source)
        source_mode = source.lstat().st_mode
        mode = 0o755 if source_mode & 0o111 else 0o644
        _add_file(plan, destination_root / relative, data, mode)


def _render_brief(template: bytes, project: str, brief_text: str, brief: bytes) -> bytes:
    try:
        text = template.decode("utf-8")
    except UnicodeDecodeError as exc:  # pragma: no cover - template preflight catches this
        raise CommissionError(f"BRIEF template is not UTF-8: {exc}") from exc
    if BRIEF_BEGIN in brief_text or BRIEF_END in brief_text:
        raise CommissionError("brief contains a reserved prompt-verbatim marker")
    if text.count(BRIEF_BEGIN) != 1 or text.count(BRIEF_END) != 1:
        raise CommissionError("BRIEF template must contain exactly one marker pair")
    begin = text.index(BRIEF_BEGIN)
    end = text.index(BRIEF_END)
    if end <= begin:
        raise CommissionError("BRIEF template markers are out of order")

    text = (
        text[:begin + len(BRIEF_BEGIN)]
        + "\n"
        + brief_text
        + "\n"
        + text[end:]
    )
    if text.count("# brief: <board>") != 1:
        raise CommissionError("BRIEF template project placeholder is missing or duplicated")
    text = text.replace("# brief: <board>", f"# brief: {project}", 1)
    hash_line = "prompt_sha256: <fill after pasting the prompt — see 01_docs/contracts.md>"
    if text.count(hash_line) != 1:
        raise CommissionError("BRIEF template prompt hash placeholder is missing or duplicated")
    digest = hashlib.sha256(brief).hexdigest()
    text = text.replace(hash_line, f"prompt_sha256: {digest}", 1)
    return text.encode("utf-8")


def _profile_mapping(args: argparse.Namespace) -> dict[str, object]:
    return {
        "schema": 1,
        "signal_integrity": args.signal_integrity,
        "assembly": args.assembly,
        "firmware": args.firmware,
        "foreign_mating": args.foreign_mating,
        "target": args.target,
    }


def _render_commission_hold(project: str) -> bytes:
    return (
        "# PCB commission hold\n\n"
        f"Project: `{project}`  \n"
        "Stage: `PCB-COMMISSION`  \n"
        "Admission span: `PCB-COMMISSION` → `PCB-ARCHITECTURE` → "
        "`PCB-SOURCING`  \n"
        "Status: `INCOMPLETE`\n\n"
        "This file is a conductor-enforced stop marker. While it exists, both rebuild "
        "conductors refuse to run. The seeded architecture, floorplan, route, "
        "and rule values are schema examples—not adopted product facts.\n\n"
        "Delete this marker only in the same reviewed change that:\n\n"
        "- changes `BRIEF.md` to `agreed` after closing every commission fact lock;\n"
        "- replaces or explicitly adopts every seeded example and placeholder;\n"
        "- records architecture, sourcing, applicability, and required part dossiers;\n"
        "- updates `STATUS.md` truthfully; and\n"
        "- passes the project contracts/schema/source checks named by the PCB skill.\n\n"
        "Removing this file is not itself evidence that those conditions passed. "
        "The reviewed commit and owning gate receipts are the evidence.\n"
    ).encode("utf-8")


def _commission_timestamp() -> str:
    """Return an ISO-8601 commission time, reproducible when requested."""
    raw_epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if raw_epoch is None:
        instant = datetime.now()
    else:
        try:
            epoch = int(raw_epoch)
        except ValueError as exc:
            raise CommissionError("SOURCE_DATE_EPOCH must be a non-negative integer") from exc
        if epoch < 0:
            raise CommissionError("SOURCE_DATE_EPOCH must be a non-negative integer")
        instant = datetime.fromtimestamp(epoch)
    return instant.replace(microsecond=0).isoformat()


def _render_status(template: bytes, timestamp: str) -> bytes:
    try:
        text = template.decode("utf-8")
    except UnicodeDecodeError as exc:  # pragma: no cover - template preflight catches this
        raise CommissionError(f"STATUS template is not UTF-8: {exc}") from exc
    placeholder = "updated: <commissioner writes ISO-8601>"
    if text.count(placeholder) != 1:
        raise CommissionError("STATUS template must contain one commissioner timestamp")
    return text.replace(placeholder, f"updated: {timestamp}", 1).encode("utf-8")


def _render_project_readme(
    project: str,
    profile: dict[str, object],
    *,
    enclosure: bool,
) -> bytes:
    target = str(profile["target"])
    return (
        f"# {project}\n\n"
        "PCB commissioning scaffold. The original request and acceptance criteria "
        "live in [`01_docs/BRIEF.md`](01_docs/BRIEF.md); current work lives in "
        "[`01_docs/STATUS.md`](01_docs/STATUS.md).\n\n"
        "## Capability\n\n"
        f"- target: `{target}`\n"
        f"- signal integrity: `{profile['signal_integrity']}`\n"
        f"- assembly: `{profile['assembly']}`\n"
        f"- firmware: `{profile['firmware']}`\n"
        f"- foreign mating: `{str(profile['foreign_mating']).lower()}`\n"
        f"- enclosure seed: `{str(enclosure).lower()}`\n\n"
        "The machine-readable authority is "
        "[`01_docs/capability-profile.json`](01_docs/capability-profile.json).\n\n"
        "## Start\n\n"
        "Run this from the project root. If this project is outside the circuits "
        "checkout, export `CIRCUITS_ROOT=/absolute/path/to/circuits` first.\n\n"
        "```bash\n"
        "export CIRCUITS_ROOT=\"${CIRCUITS_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null)}\"\n"
        "test -f \"$CIRCUITS_ROOT/skills/pcb-design/SKILL.md\" || { \\\n"
        "  echo \"set CIRCUITS_ROOT to the circuits checkout\" >&2; exit 2; }\n"
        "python3 \"$CIRCUITS_ROOT/skills/pcb-design/scripts/skill_reference_router.py\" \\\n"
        "  --profile \"$PWD/01_docs/capability-profile.json\" \\\n"
        "  --at-stage PCB-COMMISSION --json\n"
        "```\n\n"
        "This is a scaffold, not a passed commission. Read "
        "[`01_docs/COMMISSIONING-HOLD.md`](01_docs/COMMISSIONING-HOLD.md), "
        "preserve the original brief, close its fact locks, and replace or "
        "explicitly adopt every seeded example. Do not run either rebuild "
        "conductor while the hold exists; both fail closed.\n\n"
        "After the separately typed commission, architecture, and sourcing "
        "admission evidence is reviewed and its hold is removed, start "
        "the full conductor with `bash 03_src/rebuild_all.sh`. A fresh run "
        "deliberately stops at evidence and operator checkpoints. After accepting "
        "the exact schematic review checkpoint, continue without rebuilding TSX "
        "using `bash 03_src/rebuild_all.sh --resume-after-schematic-review`. A "
        "sealed release is immutable and does not by itself mean this board was "
        "ordered.\n"
    ).encode("utf-8")


def _build_plan(
    project: str,
    brief_text: str,
    brief: bytes,
    profile_mapping: dict[str, object],
    *,
    foreign_mating: bool,
    enclosure: bool,
) -> dict[Path, tuple[bytes, int]]:
    plan: dict[Path, tuple[bytes, int]] = {}

    contracts = PCB_TEMPLATES / "contracts"
    for source in sorted(path for path in contracts.rglob("*") if path.is_file()):
        relative = source.relative_to(contracts)
        if relative == Path("03_src/mechanical/contracts.md") and not enclosure:
            continue
        destination = Path("contracts.md") if relative == Path("ROOT.contracts.md") else relative
        _add_file(plan, destination, _template_bytes(source))

    _add_template_tree(
        plan,
        PCB_TEMPLATES / "01_docs",
        Path("01_docs"),
        excluded=frozenset({Path("BRIEF.md"), Path("STATUS.md")}),
    )
    _add_template_tree(
        plan,
        PCB_TEMPLATES / "03_src",
        Path("03_src"),
        excluded=(frozenset() if foreign_mating else frozenset({Path("rules/mates.yaml")})),
    )

    brief_template = PCB_TEMPLATES / "01_docs/BRIEF.md"
    _add_file(
        plan,
        Path("01_docs/BRIEF.md"),
        _render_brief(_template_bytes(brief_template), project, brief_text, brief),
    )
    profile = json.dumps(profile_mapping, indent=2, ensure_ascii=False) + "\n"
    _add_file(plan, Path("01_docs/capability-profile.json"), profile.encode("utf-8"))
    _add_file(
        plan,
        Path("01_docs/COMMISSIONING-HOLD.md"),
        _render_commission_hold(project),
    )
    _add_file(
        plan,
        Path("01_docs/STATUS.md"),
        _render_status(
            _template_bytes(PCB_TEMPLATES / "01_docs/STATUS.md"),
            _commission_timestamp(),
        ),
    )
    _add_file(
        plan,
        Path("README.md"),
        _render_project_readme(project, profile_mapping, enclosure=enclosure),
    )
    _add_file(plan, Path(".gitignore"), _template_bytes(PCB_TEMPLATES / "project.gitignore"))

    if enclosure:
        _add_file(
            plan,
            Path("03_src/mechanical/mechanical-intent-v2.yaml"),
            _template_bytes(ENCLOSURE_ASSETS / "mechanical-intent.template.yaml"),
        )
        _add_file(
            plan,
            Path("07_enclosure_releases/contracts.md"),
            _template_bytes(ENCLOSURE_ASSETS / "enclosure-release.contracts.md"),
        )
    return plan


def _write_exclusive(path: Path, data: bytes, mode: int) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, mode)
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            descriptor = -1
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(path, mode, follow_symlinks=False)
    finally:
        if descriptor >= 0:  # pragma: no cover - only an fdopen failure reaches this
            os.close(descriptor)


def commission(args: argparse.Namespace) -> tuple[Path, int, str]:
    if not PROJECT_NAME.fullmatch(args.name):
        raise CommissionError(
            "--name must match [a-z0-9][a-z0-9-]* (one direct-child component)"
        )
    projects_root = _require_directory(args.projects_root, "--projects-root")
    destination = projects_root / args.name
    if os.path.lexists(destination):
        raise CommissionError(f"destination already exists; refusing to merge: {destination}")
    brief_text, brief = _read_regular_utf8(args.brief_file, "--brief-file")

    if args.assembly != "jlcpcb":
        raise CommissionError(
            "the executable scaffold currently supports only --assembly jlcpcb "
            "(the populated PCBA path); other router profiles have no matching conductor"
        )

    profile_mapping = _profile_mapping(args)
    try:
        profile = CapabilityProfile.from_mapping(profile_mapping)
        disclosure_plan = resolve_profile(profile)
    except RouterValidationError as exc:
        raise CommissionError(f"capability profile rejected by skill router: {exc}") from exc

    files = _build_plan(
        args.name,
        brief_text,
        brief,
        profile_mapping,
        foreign_mating=args.foreign_mating,
        enclosure=args.enclosure,
    )

    created = False
    try:
        destination.mkdir(mode=0o755)
        created = True
        os.chmod(destination, 0o755, follow_symlinks=False)
        for relative, (data, mode) in sorted(files.items(), key=lambda item: item[0].as_posix()):
            target = destination / relative
            target.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
            os.chmod(target.parent, 0o755, follow_symlinks=False)
            _write_exclusive(target, data, mode)
    except (OSError, CommissionError) as exc:
        if created and destination.is_dir() and not destination.is_symlink():
            shutil.rmtree(destination)
        if isinstance(exc, CommissionError):
            raise
        raise CommissionError(f"could not create scaffold: {exc}") from exc

    return destination, len(files), str(disclosure_plan["target_stage"])


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", nargs="?",
                        help="lowercase project slug; becomes one direct child")
    parser.add_argument("--name", dest="project_option",
                        help="explicit spelling of the project slug")
    parser.add_argument("--projects-root", type=Path, default=ROOT / "projects",
                        help="existing ordinary directory that will own the new project "
                             "(default: repository projects/)")
    parser.add_argument("--brief-file", type=Path, required=True,
                        help="ordinary UTF-8 file containing the commissioning prompt")
    parser.add_argument("--signal-integrity", choices=sorted(SIGNAL_INTEGRITY),
                        default="ordinary")
    parser.add_argument("--assembly", choices=("jlcpcb",), default="jlcpcb",
                        help="populated JLCPCB PCBA path (the only conductor "
                             "implemented by this commissioner)")
    parser.add_argument("--firmware", choices=sorted(FIRMWARE), default="forbidden")
    parser.add_argument("--target", choices=sorted(TARGETS), default="design")
    parser.add_argument("--foreign-mating", action="store_true",
                        help="seed rules/mates.yaml for hardware designed elsewhere")
    parser.add_argument("--enclosure", action="store_true",
                        help="seed enclosure intent/source/release authorities; "
                             "choose co-design versus derived later when its "
                             "exact PCB authority is known")
    args = parser.parse_args(argv)
    if args.project and args.project_option:
        parser.error("provide the project slug positionally or with --name, not both")
    args.name = args.project or args.project_option
    if not args.name:
        parser.error("a project slug is required")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        _, file_count, target_stage = commission(args)
    except CommissionError as exc:
        print(f"PCB-SCAFFOLD FAIL: {exc}", file=sys.stderr)
        return 2
    print(
        f"PCB-SCAFFOLD OK name={args.name} files={file_count} "
        f"stage=PCB-COMMISSION status=INCOMPLETE target={target_stage}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
