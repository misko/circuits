#!/usr/bin/env python3
"""Fail-closed gate for publishing material PCB project changes.

This is the boundary between "the generated board is mechanically green" and
"this design state may be published on the repository's main line".  It grades
every materially changed project and requires each live board to be represented
by a complete sealed release whose independent reviews bind the exact board
bytes.  A zero-project denominator is only a pass when the git diff proves that
no material PCB project path changed.

The gate is intentionally pcbnew-free.  It composes the existing release gates
and adds the publication-only properties they cannot infer from an isolated
release directory: live-source identity, review archive identity, review
artifact binding, and source-commit freshness.

A superseding release declares its freshness shape as structured MANIFEST
data.  Publication must replay that same stronger mode: invoking ordinary
freshness on a legitimate docs-only successor rejects the byte identity that
``--docs-only-supersede`` is specifically designed to prove.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FAB_SCRIPTS = ROOT / "skills" / "jlcpcb-fab" / "scripts"
sys.path.insert(0, str(FAB_SCRIPTS))
import release_index  # noqa: E402


REQUIRED_REVIEWS = (
    "pin_review.md",
    "render_review.md",
    "redteam_topology.md",
    "redteam_layout.md",
)

MATERIAL_TOP_LEVEL = {
    "02_parts", "03_src", "03_tscircuit", "04_kicad",
    # Release and review bytes are publication claims, not bookkeeping. A
    # change to either must re-grade the project even if source is untouched.
    "07_releases", "08_reviews",
}
MATERIAL_DOCS = {
    "01_docs/BRIEF.md",
    "01_docs/ARCHITECTURE.md",
    "01_docs/DETAIL_DESIGN.md",
}


def _run(args, cwd=ROOT):
    return subprocess.run(
        [str(a) for a in args], cwd=str(cwd), text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def _git(*args, root=ROOT):
    return _run(["git", *args], cwd=root)


def _sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _project_rel(path):
    """Return ``(project, inside-project path)`` for a repo-relative path."""
    p = Path(str(path))
    parts = p.parts
    if len(parts) < 3 or parts[0] != "projects":
        return None
    return Path(parts[0]) / parts[1], Path(*parts[2:]).as_posix()


def is_material_project_path(path):
    parsed = _project_rel(path)
    if not parsed:
        return False
    _, inner = parsed
    top = inner.split("/", 1)[0]
    return (top in MATERIAL_TOP_LEVEL or inner in MATERIAL_DOCS or
            inner.startswith("01_docs/decisions/"))


def affected_projects(paths):
    """Material diff paths -> sorted project-relative directories."""
    return sorted({str(_project_rel(p)[0]) for p in paths
                   if is_material_project_path(p)})


def _diff_names(base, head, root):
    if not base or not head:
        raise ValueError("--base and --head must be supplied together")
    if re.fullmatch(r"0+", base):
        raise ValueError("an all-zero base cannot prove publication coverage")
    cp = _git("diff", "--name-only", "--diff-filter=ACDMRTUXB",
              base, head, "--", "projects", root=root)
    if cp.returncode:
        raise ValueError(cp.stdout.strip() or "git diff failed")
    return [line.strip() for line in cp.stdout.splitlines() if line.strip()]


def _manifest_fields(path):
    fields = {}
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    for line in text.splitlines():
        m = re.match(r"^\s*([A-Za-z_]+):\s*([^#\r\n]*?)\s*(?:#.*)?$", line)
        if m:
            fields.setdefault(m.group(1).lower(), m.group(2).strip())
    return fields, text


def _review_field(text, key):
    m = re.search(rf"(?im)^\s*{re.escape(key)}:\s*(.*?)\s*$", text)
    return m.group(1).strip() if m else ""


def _review_board_hash(text):
    direct = _review_field(text, "board_sha256")
    if re.fullmatch(r"[0-9a-fA-F]{64}", direct):
        return direct.lower()
    table = re.search(
        r"(?im)^\s*\|\s*board\s*\|\s*`?([0-9a-f]{64})`?\s*\|\s*$",
        text)
    return table.group(1).lower() if table else ""


def _manifest_board_hash(text, board_name):
    target = f"source/{board_name}"
    for line in text.splitlines():
        m = re.match(r"^\s*(\S+)\s+([0-9a-fA-F]{64})\s*$", line)
        if m and m.group(1) == target:
            return m.group(2).lower()
    return ""


def _is_ancestor(commit, head, root):
    return _git("merge-base", "--is-ancestor", commit, head,
                root=root).returncode == 0


def _material_changes_since(commit, head, project_rel, root):
    pathspecs = [
        f"{project_rel}/01_docs/BRIEF.md",
        f"{project_rel}/01_docs/ARCHITECTURE.md",
        f"{project_rel}/01_docs/DETAIL_DESIGN.md",
        f"{project_rel}/01_docs/decisions",
        f"{project_rel}/02_parts",
        f"{project_rel}/03_src",
        f"{project_rel}/03_tscircuit",
        f"{project_rel}/04_kicad",
    ]
    cp = _git("diff", "--name-only", commit, head, "--", *pathspecs,
              root=root)
    if cp.returncode:
        return [f"git diff failed: {cp.stdout.strip()}"]
    return [line.strip() for line in cp.stdout.splitlines() if line.strip()]


def _working_material_changes(project_rel, root):
    cp = _git("status", "--porcelain=v1", "--untracked-files=all", "--",
              project_rel, root=root)
    if cp.returncode:
        return [f"git status failed: {cp.stdout.strip()}"]
    changed = []
    for line in cp.stdout.splitlines():
        raw = line[3:].strip()
        # Renames are rendered as old -> new; grade the destination.
        path = raw.rsplit(" -> ", 1)[-1]
        if is_material_project_path(path):
            changed.append(path)
    return changed


def _child_gate(script, release, root, *extra):
    cp = _run([sys.executable, root / script, release, *extra], cwd=root)
    if cp.returncode == 0:
        return []
    tail = "\n".join(cp.stdout.splitlines()[-12:])
    return [f"{Path(script).name} failed for {release}:\n{tail}"]


def _freshness_args(fields, release):
    """Return ``(errors, argv)`` for the release's declared freshness shape.

    No declaration means an ordinary material release.  A docs-only release
    must name one existing sibling predecessor by directory name; accepting a
    path, a missing predecessor, or an unknown mode would turn the stronger
    identity assertion into a silent ordinary check.
    """
    mode = fields.get("release_mode", "").strip().lower()
    if not mode:
        return [], ["--claim", "design"]
    if mode != "docs-only":
        return [f"FRESHNESS-MODE: unsupported release_mode {mode!r}"], []
    prior_name = fields.get("supersedes", "").strip()
    if not prior_name or Path(prior_name).name != prior_name:
        return [
            "FRESHNESS-PREDECESSOR: docs-only release must name one sibling "
            "release directory in `supersedes:`"
        ], []
    prior = release.parent / prior_name
    if not prior.is_dir() or prior.resolve() == release.resolve():
        return [
            f"FRESHNESS-PREDECESSOR: declared predecessor {prior_name!r} "
            "does not resolve to a different sibling release directory"
        ], []
    return [], ["--claim", "design", "--docs-only-supersede", prior]


def review_binding_errors(project, release, board_hash, head, root):
    errors = []
    archive = project / "08_reviews"
    archived = {}
    if archive.is_dir():
        for archived_path in archive.rglob("*.md"):
            archived.setdefault(_sha256(archived_path), []).append(archived_path)
    for name in REQUIRED_REVIEWS:
        path = release / "verification" / name
        label = f"{project.name}/{release.name}/verification/{name}"
        if not path.is_file():
            errors.append(f"REVIEW-COVERAGE: missing {label}")
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        verdict = _review_field(text, "design_verdict").split()[0].upper() \
            if _review_field(text, "design_verdict") else ""
        if verdict != "SOUND":
            errors.append(
                f"REVIEW-VERDICT: {label} design_verdict is "
                f"{verdict or 'UNSTATED'}, expected SOUND")
        subject = _review_field(text, "subject")
        if project.name.lower() not in subject.lower():
            errors.append(
                f"REVIEW-SUBJECT: {label} does not name project "
                f"{project.name!r}")
        bound = _review_board_hash(text)
        if bound != board_hash:
            errors.append(
                f"REVIEW-BINDING: {label} binds board SHA256 "
                f"{bound or 'UNSTATED'}, expected {board_hash}")
        source_commit = _review_field(text, "source_commit")
        # Legacy pin/render reviews sometimes predate source_commit headers.
        # Their exact board hash + byte-identical archive copy still binds the
        # reviewed artifact. New review contracts require source_commit; when
        # present here it must remain valid provenance.
        if source_commit:
            if not re.fullmatch(r"[0-9a-fA-F]{40}", source_commit):
                errors.append(
                    f"REVIEW-COMMIT: {label} source_commit is not a full SHA")
            elif not _is_ancestor(source_commit, head, root):
                errors.append(
                    f"REVIEW-COMMIT: {label} source_commit {source_commit} "
                    f"is not an ancestor of {head}")
        matches = archived.get(_sha256(path), [])
        if not matches:
            errors.append(
                f"REVIEW-ARCHIVE: {label} is not byte-identical to any "
                f"tracked review under {project.name}/08_reviews/")
        else:
            # In-repository publication claims must be committed. Fixtures
            # outside this worktree still exercise byte identity.
            try:
                project.relative_to(root)
            except ValueError:
                pass
            else:
                tracked = any(_git("ls-files", "--error-unmatch",
                                   p.relative_to(root).as_posix(),
                                   root=root).returncode == 0 for p in matches)
                if not tracked:
                    errors.append(
                        f"REVIEW-ARCHIVE: {label} matches only untracked "
                        f"review bytes under {project.name}/08_reviews/")
    return errors


def grade_board(project, board, head, root, check_worktree, release_override=None):
    errors = []
    project_rel = project.relative_to(root).as_posix()
    try:
        release = (Path(release_override).resolve() if release_override
                   else release_index.latest_release(project, board))
    except release_index.ReleaseSetError as e:
        return [f"RELEASE-SET: {e}"], None
    if release is None:
        return [f"NO-RELEASE: {project_rel}/{board.name} has no sealed release"], None
    try:
        release.relative_to(project.resolve())
    except ValueError:
        return [f"RELEASE-SCOPE: staging release escapes {project_rel}"], release

    manifest = release / "MANIFEST.txt"
    source_board = release / "source" / board.name
    if not manifest.is_file():
        errors.append(f"MANIFEST: missing {manifest.relative_to(root)}")
        return errors, release
    if not source_board.is_file():
        errors.append(f"RELEASE-SOURCE: missing {source_board.relative_to(root)}")
        return errors, release

    fields, manifest_text = _manifest_fields(manifest)
    commit = fields.get("git_sha", "")
    if not re.fullmatch(r"[0-9a-fA-F]{40}", commit):
        errors.append("MANIFEST-COMMIT: git_sha must be a full 40-character SHA")
    elif not _is_ancestor(commit, head, root):
        errors.append(
            f"MANIFEST-COMMIT: {commit} is not an ancestor of {head}")
    else:
        drift = _material_changes_since(commit, head, project_rel, root)
        if drift:
            errors.append(
                "STALE-RELEASE: material project paths changed after MANIFEST "
                f"git_sha {commit}: {', '.join(drift)}")
    if fields.get("git_dirty", "").lower() != "false":
        errors.append("MANIFEST-DIRTY: git_dirty must be false")

    live_hash = _sha256(board)
    source_hash = _sha256(source_board)
    if live_hash != source_hash:
        errors.append(
            f"LIVE-SOURCE: {board.relative_to(root)} SHA256 {live_hash} differs "
            f"from sealed source SHA256 {source_hash}")
    recorded_hash = _manifest_board_hash(manifest_text, board.name)
    if recorded_hash != source_hash:
        errors.append(
            f"MANIFEST-HASH: source/{board.name} records "
            f"{recorded_hash or 'NO HASH'}, expected {source_hash}")

    if check_worktree:
        working = _working_material_changes(project_rel, root)
        if working:
            errors.append(
                "DIRTY-MATERIAL: uncommitted material paths are outside the "
                f"sealed release: {', '.join(working)}")

    required_args = ()
    if release_override:
        # Mutable staging lives under 06_build rather than 07_releases, so the
        # checker cannot discover the canonical release contract from the
        # staging directory's parent.  Keep one authority by explicitly
        # borrowing this project's existing release contract.
        required_args = ("--contract", str(project / "07_releases/contracts.md"))
    errors.extend(_child_gate(
        "skills/kicad-pcb/scripts/release_required_check.py", release, root,
        *required_args))
    mode_errors, freshness_args = _freshness_args(fields, release)
    errors.extend(mode_errors)
    if not mode_errors:
        errors.extend(_child_gate(
            "skills/jlcpcb-fab/scripts/release_freshness_check.py", release,
            root, *freshness_args))
    errors.extend(_child_gate(
        "skills/kicad-pcb/scripts/rf_contract_check.py", project, root,
        "--require-applicability",
        "--require-review", "schematic", "--require-review", "pcb",
        "--require-review", "fab"))
    errors.extend(review_binding_errors(
        project, release, source_hash, head, root))
    return errors, release


def _parse_args(argv):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--base", help="base git commit for diff-aware CI mode")
    p.add_argument("--head", default="HEAD", help="head commit (default: HEAD)")
    p.add_argument("--project", action="append", default=[],
                   help="project directory to audit explicitly (repeatable)")
    p.add_argument("--release", type=Path,
                   help="mutable staging release to rehearse; requires exactly "
                        "one --project with exactly one live board")
    return p.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)
    root = args.root.resolve()
    if not (root / ".git").exists():
        print(f"P-PUBLISH FAIL: --root is not a git worktree: {root}")
        return 2
    if args.base and args.project:
        print("P-PUBLISH FAIL: choose diff mode (--base/--head) or explicit "
              "audit mode (--project), not both")
        return 2
    if args.release and (args.base or len(args.project) != 1):
        print("P-PUBLISH FAIL: --release requires exactly one --project and no --base")
        return 2
    if not args.base and not args.project:
        print("P-PUBLISH FAIL: provide --base for diff-aware mode or at least "
              "one --project for explicit audit mode")
        return 2

    try:
        if args.base:
            names = _diff_names(args.base, args.head, root)
            selected = affected_projects(names)
            check_worktree = False
            print(f"P-PUBLISH coverage: {len(selected)} material project(s) "
                  f"selected from {len(names)} changed path(s)")
        else:
            selected = []
            for raw in args.project:
                p = Path(raw)
                if p.is_absolute():
                    p = p.resolve().relative_to(root)
                elif p.parts and p.parts[0] != "projects":
                    p = Path("projects") / p
                selected.append(p.as_posix().rstrip("/"))
            selected = sorted(set(selected))
            check_worktree = True
            print(f"P-PUBLISH coverage: {len(selected)} explicitly selected "
                  "project(s)")
    except (ValueError, OSError) as e:
        print(f"P-PUBLISH FAIL: cannot establish diff coverage: {e}")
        return 2

    if not selected:
        print("P-PUBLISH PASS: 0 project(s), 0 board(s) graded; the git diff "
              "contains no material PCB project path")
        return 0

    failures = []
    board_count = 0
    for rel in selected:
        project = root / rel
        if not project.is_dir():
            failures.append((rel, "PROJECT: selected project directory is absent"))
            continue
        boards = sorted((project / "04_kicad").glob("*.kicad_pcb"))
        if not boards:
            failures.append((rel, "BOARD-COVERAGE: no 04_kicad/*.kicad_pcb "
                                  "exists; a material project cannot publish "
                                  "with a zero-board denominator"))
            continue
        if args.release and len(boards) != 1:
            failures.append((rel, "BOARD-COVERAGE: --release rehearsal requires "
                                  "exactly one live board"))
            continue
        for board in boards:
            board_count += 1
            errors, release = grade_board(
                project, board, args.head, root, check_worktree,
                args.release if args.release else None)
            if errors:
                for error in errors:
                    failures.append((f"{rel}/{board.name}", error))
            else:
                print(f"  PASS {rel}/{board.name} -> "
                      f"{release.relative_to(root)}")

    print(f"P-PUBLISH: {len(selected)} project(s), {board_count} board(s) graded")
    if failures:
        for subject, error in failures:
            indented = error.replace("\n", "\n      ")
            print(f"  FAIL {subject}: {indented}")
        print(f"P-PUBLISH FAIL: {len(failures)} finding(s)")
        return 1
    print("P-PUBLISH PASS: every material project is sealed, independently "
          "reviewed, exact-artifact-bound, and fresh")
    return 0


if __name__ == "__main__":
    sys.exit(main())
