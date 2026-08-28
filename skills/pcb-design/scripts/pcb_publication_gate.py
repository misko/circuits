#!/usr/bin/env python3
"""Fail-closed gate for publishing material PCB project changes.

This is the boundary between "the generated board is mechanically green" and
"this design state may be published on the repository's main line".  It grades
every materially changed project and requires each live board to be represented
by a complete sealed release whose independent reviews bind the exact board
bytes.  A zero-project denominator is only a pass when the git diff proves that
no material PCB project path changed, except for a complete tracked project
tree relocated byte/mode-identically from ``projects/<name>`` to the previously
absent ``archived_projects/<name>``.

The archive is part of that proof, not an ungraded destination.  Every committed
change below ``archived_projects/`` is refused unless it is wholly explained by
one such same-name relocation.  This keeps a valid archive move from laundering
an addition, deletion, content edit, or mode edit in any frozen archive.

The enclosure stream is deliberately independent.  Changes lexically rooted
at ``03_src/mechanical`` or ``07_enclosure_releases`` are classified as
enclosure-only and do not put the parent PCB into this gate's reseal/RF-build
denominator.  One exact connector-service authority can join that mechanical
classification, but only when base/head bytes prove its companion child
contract gained exactly one approved allowlist row and nothing else.  This gate
does not validate those changes; the enclosure release gate remains their
authority.  Prefix exemptions remain exact-prefix-only and the connector
allowance is a paired diff proof, so every other path under PCB source,
generated KiCad, fabrication releases, or reviews continues to fail closed
into ordinary PCB publication grading.

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
ENCLOSURE_ONLY_ROOTS = (
    "03_src/mechanical",
    "07_enclosure_releases",
)
CONNECTOR_AUTHORITY_INNER = "03_src/rules/connector_assemblies.yaml"
CONNECTOR_CHILD_CONTRACT_INNER = "03_src/rules/contracts.md"
CANONICAL_CONNECTOR_CONTRACT_ROWS = {
    "| `connector_assemblies.yaml` | go-forward shared connector service contract; binds each receptacle, supported mate, grip/fastening/tool/torque/reaction/cable cell, simultaneous population, operation sequence, and tolerance provenance for the PCB and enclosure consumers. Unknown facts are explicit and compile `INCOMPLETE`, never default dimensions. |",
    "| `connector_assemblies.yaml` | complete receptacle/mate/grip/tool/cable/operation/tolerance contracts for every operated or serviced external interface; compiled by `pcb-design` and allowed to remain explicitly `INCOMPLETE` while hardware and service facts are unknown |",
}
PATH_OUTSIDE_PROJECT = "outside-project"
PATH_BOOKKEEPING = "bookkeeping"
PATH_ENCLOSURE_ONLY = "enclosure-only"
PATH_PCB_MATERIAL = "pcb-material"


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


def _is_at_or_below(inner, root):
    """Return true only for one exact project-relative root and descendants."""
    return inner == root or inner.startswith(f"{root}/")


def classify_project_path(path):
    """Classify one repo-relative path for the PCB publication denominator.

    Ordering is the safety property: the two independent enclosure roots are
    removed explicitly before the broad ``03_src`` PCB-source rule runs.  A
    near-miss such as ``03_src/mechanical-electrical`` therefore remains PCB
    material.  The connector authority and its child contract also remain
    material here; only the base/head paired-diff proof can reclassify them.
    """
    parsed = _project_rel(path)
    if not parsed:
        return PATH_OUTSIDE_PROJECT
    _, inner = parsed
    if any(part == ".." for part in Path(inner).parts):
        return PATH_PCB_MATERIAL
    if any(_is_at_or_below(inner, root) for root in ENCLOSURE_ONLY_ROOTS):
        return PATH_ENCLOSURE_ONLY
    top = inner.split("/", 1)[0]
    if (top in MATERIAL_TOP_LEVEL or inner in MATERIAL_DOCS or
            inner.startswith("01_docs/decisions/")):
        return PATH_PCB_MATERIAL
    return PATH_BOOKKEEPING


def is_material_project_path(path):
    return classify_project_path(path) == PATH_PCB_MATERIAL


def is_enclosure_only_project_path(path):
    return classify_project_path(path) == PATH_ENCLOSURE_ONLY


def affected_projects(paths):
    """Material diff paths -> sorted project-relative directories."""
    return sorted({str(_project_rel(p)[0]) for p in paths
                   if is_material_project_path(p)})


def enclosure_only_projects(paths):
    """Enclosure-only diff paths -> sorted project-relative directories."""
    return sorted({str(_project_rel(p)[0]) for p in paths
                   if is_enclosure_only_project_path(p)})


def _git_blob_text(commit, path, root):
    """Return one tracked UTF-8 text blob, or ``None`` when absent."""
    cp = _git("show", f"{commit}:{Path(path).as_posix()}", root=root)
    if cp.returncode:
        return None
    return cp.stdout


def _git_file_identity(commit, path, root):
    """Return one tracked file's ``(mode, kind, oid)``, or ``None``."""
    rel = Path(path).as_posix()
    cp = _git("ls-tree", "-z", commit, "--", rel, root=root)
    if cp.returncode:
        return None
    matches = []
    for record in cp.stdout.split("\0"):
        if not record:
            continue
        metadata, listed = record.split("\t", 1)
        if listed == rel:
            matches.append(tuple(metadata.split()))
    return matches[0] if len(matches) == 1 else None


def _connector_bundle_enclosure_paths(paths, base, head, root):
    """Prove exact connector-authority + child-contract migration bundles.

    Both paths are PCB material by default.  A project earns the mechanical
    classification only when the authority path changed in the same diff and
    the contract's *entire* byte delta is insertion of exactly one approved
    allowlist row.  A missing/deleted authority, an existing authority edited
    without its sibling, any additional contract byte, or any near-prefix earns
    no allowance.
    """
    changed = set(paths)
    allowed = set()
    for project_rel in _changed_active_projects(paths):
        authority = f"{project_rel}/{CONNECTOR_AUTHORITY_INNER}"
        contract = f"{project_rel}/{CONNECTOR_CHILD_CONTRACT_INNER}"
        if authority not in changed or contract not in changed:
            continue
        base_authority_identity = _git_file_identity(base, authority, root)
        head_authority_identity = _git_file_identity(head, authority, root)
        if (base_authority_identity is not None or
                head_authority_identity is None or
                head_authority_identity[:2] != ("100644", "blob")):
            continue
        base_contract_identity = _git_file_identity(base, contract, root)
        head_contract_identity = _git_file_identity(head, contract, root)
        if (base_contract_identity is None or head_contract_identity is None or
                base_contract_identity[:2] != ("100644", "blob") or
                head_contract_identity[:2] != base_contract_identity[:2]):
            continue
        before = _git_blob_text(base, contract, root)
        after = _git_blob_text(head, contract, root)
        if before is None or after is None:
            continue
        for row in CANONICAL_CONNECTOR_CONTRACT_ROWS:
            added = row + "\n"
            if after.count(added) == 1 and after.replace(added, "", 1) == before:
                allowed.update((authority, contract))
                break
    return allowed


def _changed_active_projects(paths):
    """All changed ``projects/<name>`` roots, including bookkeeping-only ones."""
    roots = set()
    for path in paths:
        parsed = _project_rel(path)
        if parsed:
            roots.add(str(parsed[0]))
    return sorted(roots)


def _archive_change_subject(path):
    """Collapse one archive path to its governed project, or retain root files.

    A changed leaf below ``archived_projects/<name>/`` is accounted once at the
    project-tree boundary.  A direct child such as the archive collection's
    own contract cannot masquerade as a project and is returned verbatim so it
    also fails closed.
    """
    parts = Path(str(path)).parts
    if not parts or parts[0] != "archived_projects":
        return None
    if len(parts) >= 3:
        return (Path(parts[0]) / parts[1]).as_posix()
    return Path(*parts).as_posix()


def _changed_archive_subjects(paths):
    """All independently governed subjects changed below the archive root."""
    return sorted({subject for path in paths
                   if (subject := _archive_change_subject(path)) is not None})


def _tree_identity(commit, path, root):
    """Return a tracked directory's Git tree identity, or ``None`` if absent.

    A tree object recursively binds every tracked pathname, blob byte, and
    executable/symlink mode below the directory.  Query the named commit rather
    than the worktree so an untracked copy cannot satisfy publication coverage.
    """
    rel = Path(path).as_posix().rstrip("/")
    cp = _git("ls-tree", "-z", commit, "--", rel, root=root)
    if cp.returncode:
        raise ValueError(
            f"cannot inspect tracked tree {rel!r} at {commit}: "
            f"{cp.stdout.strip() or 'git ls-tree failed'}")
    matches = []
    for record in cp.stdout.split("\0"):
        if not record:
            continue
        try:
            metadata, listed = record.split("\t", 1)
            mode, kind, oid = metadata.split()
        except ValueError as e:
            raise ValueError(
                f"cannot parse git tree identity for {rel!r} at {commit}") from e
        if listed == rel:
            matches.append((mode, kind, oid))
    if not matches:
        return None
    if len(matches) != 1 or matches[0][1] != "tree":
        raise ValueError(
            f"tracked archive subject {rel!r} at {commit} is not one directory")
    mode, _, oid = matches[0]
    return mode, oid


def _is_exact_archive_relocation(project_rel, base, head, root):
    """Whether one live project was *only* moved into the archive.

    This is deliberately stricter than rename detection.  The old active tree
    must exist only at ``base``; the same-name archive tree must exist only at
    ``head``; and their recursive Git tree identities must match.  Consequently
    content edits, file-mode edits, partial copies, retained active files, an
    overwritten archive, and worktree-only bytes cannot earn the allowance.
    """
    parts = Path(project_rel).parts
    if len(parts) != 2 or parts[0] != "projects":
        raise ValueError(
            f"archive relocation subject is not one project root: {project_rel!r}")
    active = Path(*parts).as_posix()
    archived = (Path("archived_projects") / parts[1]).as_posix()
    base_active = _tree_identity(base, active, root)
    head_archived = _tree_identity(head, archived, root)
    return (
        base_active is not None
        and head_archived is not None
        and _tree_identity(base, archived, root) is None
        and _tree_identity(head, active, root) is None
        and base_active == head_archived
    )


def _diff_names(base, head, root):
    if not base or not head:
        raise ValueError("--base and --head must be supplied together")
    if re.fullmatch(r"0+", base):
        raise ValueError("an all-zero base cannot prove publication coverage")
    # Disable rename pairing so a cross-domain move contributes both its old
    # and new path.  Otherwise moving PCB source into an exempt enclosure root
    # could be reported only by its destination and launder the deletion.
    cp = _git("diff", "--no-renames", "--name-only", "-z",
              "--diff-filter=ACDMRTUXB", base, head, "--",
              "projects", "archived_projects", root=root)
    if cp.returncode:
        raise ValueError(cp.stdout.strip() or "git diff failed")
    return [path for path in cp.stdout.split("\0") if path]


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
    cp = _git("diff", "--no-renames", "--name-only", "-z", commit, head,
              "--", *pathspecs, root=root)
    if cp.returncode:
        return [f"git diff failed: {cp.stdout.strip()}"]
    return [path for path in cp.stdout.split("\0")
            if path and is_material_project_path(path)]


def _working_material_changes(project_rel, root, ignored_new_prefixes=()):
    """Return dirty PCB-material paths outside exact rehearsed outputs.

    ``--release`` grades a mutable candidate in ``07_releases`` before its
    seal commit.  That exact candidate tree is output of the operation being
    rehearsed, so it must not make its own publication check circular.  Keep
    the exception lexical, additive-only, and caller-supplied: a modified or
    deleted tracked release byte, sibling release, predecessor marker,
    near-prefix path, or any live source remains dirty material.
    """
    ignored = tuple(Path(prefix).as_posix().rstrip("/")
                    for prefix in ignored_new_prefixes)

    def is_ignored(status, path):
        return status in {"??", "A "} and any(
            path == prefix or path.startswith(f"{prefix}/")
            for prefix in ignored)

    # Match committed-diff semantics: split renames into deletion + addition.
    # NUL records also keep unusual but legal filenames from bypassing the
    # classifier through porcelain quoting or embedded newlines.
    cp = _git("status", "--porcelain=v1", "-z", "--untracked-files=all",
              "--no-renames", "--", project_rel, root=root)
    if cp.returncode:
        return [f"git status failed: {cp.stdout.strip()}"]
    changed = []
    for record in cp.stdout.split("\0"):
        if not record:
            continue
        status = record[:2]
        path = record[3:]
        if is_material_project_path(path) and not is_ignored(status, path):
            changed.append(path)
    return changed


def _mutable_release_output_prefix(project_rel, release, head, root):
    """Return the exact new candidate prefix eligible for rehearsal.

    An override is output only when it is a new direct child of the project's
    release stream and has no tracked tree at ``head``.  Pointing ``--release``
    at an existing immutable archive therefore grants no worktree exception.
    """
    try:
        candidate = release.relative_to(root)
    except ValueError:
        return None
    expected_parent = Path(project_rel) / "07_releases"
    if candidate.parent != expected_parent:
        return None
    if _tree_identity(head, candidate.as_posix(), root) is not None:
        return None
    return candidate.as_posix()


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
    modes = {
        "docs-only": "--docs-only-supersede",
        "representation-only": "--representation-supersede",
    }
    if mode not in modes:
        return [f"FRESHNESS-MODE: unsupported release_mode {mode!r}"], []
    prior_name = fields.get("supersedes", "").strip()
    if not prior_name or Path(prior_name).name != prior_name:
        return [
            f"FRESHNESS-PREDECESSOR: {mode} release must name one sibling "
            "release directory in `supersedes:`"
        ], []
    prior = release.parent / prior_name
    if not prior.is_dir() or prior.resolve() == release.resolve():
        return [
            f"FRESHNESS-PREDECESSOR: declared predecessor {prior_name!r} "
            "does not resolve to a different sibling release directory"
        ], []
    return [], ["--claim", "design", modes[mode], prior]


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
        ignored_outputs = ()
        if release_override:
            prefix = _mutable_release_output_prefix(
                project_rel, release, head, root)
            ignored_outputs = (prefix,) if prefix else ()
        working = _working_material_changes(
            project_rel, root, ignored_new_prefixes=ignored_outputs)
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

    archive_relocations = []
    archive_findings = []
    try:
        if args.base:
            names = _diff_names(args.base, args.head, root)
            connector_bundle_paths = _connector_bundle_enclosure_paths(
                names, args.base, args.head, root)
            selection_names = [
                path for path in names if path not in connector_bundle_paths
            ]
            selected = affected_projects(selection_names)
            enclosure_paths = [
                path for path in names if is_enclosure_only_project_path(path)
            ]
            enclosure_paths.extend(sorted(connector_bundle_paths))
            enclosure_paths.sort()
            enclosure_projects = sorted({
                str(parsed[0]) for path in enclosure_paths
                if (parsed := _project_rel(path)) is not None
            })
            changed_active = _changed_active_projects(names)
            changed_archives = _changed_archive_subjects(names)
            changed_archive_set = set(changed_archives)
            # Remove projects one at a time only after proving the complete
            # tracked tree is an identity-preserving move.  Candidate discovery
            # uses every changed active project, not only material paths, so a
            # bookkeeping-only tree cannot disappear through a zero denominator.
            archive_relocations = [
                rel for rel in changed_active
                if (Path("archived_projects") / Path(rel).name).as_posix()
                in changed_archive_set
                and _is_exact_archive_relocation(
                    rel, args.base, args.head, root)
            ]
            selected = [
                rel for rel in selected if rel not in archive_relocations
            ]
            allowed_archives = {
                (Path("archived_projects") / Path(rel).name).as_posix()
                for rel in archive_relocations
            }
            for subject in changed_archives:
                if subject not in allowed_archives:
                    archive_findings.append((
                        subject,
                        "ARCHIVE-IMMUTABILITY: archive bytes or modes changed "
                        "without a complete same-name projects/<name> -> "
                        "archived_projects/<name> relocation whose recursive "
                        "Git tree is identical and whose destination was absent "
                        "at the base commit",
                    ))
            # A project deletion with no changed archive destination also needs
            # an explicit finding even if that project carried bookkeeping only.
            for rel in changed_active:
                if rel in archive_relocations:
                    continue
                if (_tree_identity(args.base, rel, root) is not None and
                        _tree_identity(args.head, rel, root) is None):
                    archive_findings.append((
                        rel,
                        "ARCHIVE-RELOCATION: tracked project tree disappeared "
                        "without an exact same-name relocation into a previously "
                        "absent archived_projects/ destination",
                    ))
            check_worktree = False
            print(f"P-PUBLISH coverage: {len(selected)} material project(s) "
                  f"selected from {len(names)} changed path(s); "
                  f"{len(archive_relocations)} exact archive relocation(s); "
                  f"{len(changed_archives)} archive subject(s) changed; "
                  f"{len(enclosure_paths)} enclosure-only path(s) across "
                  f"{len(enclosure_projects)} project(s)")
            for rel in archive_relocations:
                name = Path(rel).name
                print(f"  ARCHIVE {rel} -> archived_projects/{name} "
                      "(tracked tree byte/mode identity proven)")
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

    if archive_findings:
        for subject, finding in archive_findings:
            print(f"  FAIL {subject}: {finding}")
        print(f"P-PUBLISH FAIL: {len(archive_findings)} archive integrity "
              "finding(s)")
        return 1

    if not selected:
        if archive_relocations:
            print(
                "P-PUBLISH PASS: 0 live project(s), 0 board(s) graded; "
                f"{len(archive_relocations)} complete tracked project tree(s) "
                "moved byte/mode-identically into archived_projects/")
            return 0
        if args.base and enclosure_paths:
            print(
                "P-PUBLISH PASS: 0 PCB project(s), 0 board(s) graded; "
                f"{len(enclosure_paths)} enclosure-only path(s) are outside "
                "the PCB reseal/RF-build denominator and remain subject to "
                "the enclosure release gate")
            return 0
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
