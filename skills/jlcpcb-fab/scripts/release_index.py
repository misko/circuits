#!/usr/bin/env python3
"""release_index.py — the ONE home for "which release is THIS BOARD's latest?".

A LIBRARY, not a gate: it prints no verdict and grades nothing. It answers two
questions that four tools were each answering their own way, and getting wrong
in two distinct ways. Both were silent WRONG ANSWERS, not missing features.

  1. **WHICH BOARD does a release directory belong to?**
  2. **WHICH of that board's releases is the LATEST?**

WHY IT EXISTS — two measured defects of one class:

  * **`rels[-1]` across a MULTI-BOARD project.** `smc0985-cooksense/07_releases/`
    holds two boards::

        cooksense-v1.0-2026-07-23   cooksense-v1.1-2026-07-24
        cooksense-v1.3-2026-07-26   cooksense-v1.4-2026-07-26
        interposer-v1.0-2026-07-24

    Under any ordering whose leading component is the board prefix,
    `interposer-…` lands LAST, so "the latest release" resolved to the
    INTERPOSER while `policy_audit.py` was grading the COOKSENSE board
    (`04_kicad/*.kicad_pcb` sorted -> `cooksense.kicad_pcb`). M-REL, M-BOM,
    A-POP and A-BODY each graded the interposer archive and reported it under
    a cooksense audit; M-REL additionally demanded `SUPERSEDED.md` on
    `cooksense-v1.4`, the LIVE cooksense release, which blocked the v1.5 seal.
    Measured 2026-07-27. "The last directory" is a property ADJACENT to "this
    board's latest release" — the adjacent-property error (canon M-IMPORT).

  * **TEXT version ordering.** `v1.10` sorts BEFORE `v1.9` because '1' < '9'.
    The first double-digit minor in this fleet (usb-hub-3s-v3 v1.10,
    2026-07-27) made M-REL grade the superseded release and demand a
    `SUPERSEDED.md` on the live one. Ordering is NUMERIC PER COMPONENT here,
    exactly once, so no consumer can re-derive it differently (canon M-WIDTH:
    every consumer of release ordering, not the one that was caught).

WHAT "AUTHORITATIVE" MEANS HERE. A board's identity comes from the boards the
project actually BUILDS — the stems of `04_kicad/*.kicad_pcb` — not from a
hardcoded name list, and not from a bare regex over directory names. Names are
compared as SLUGS, because `04_kicad` spells a board `crow_recorder_central_v2`
and its release dirs spell it `crow-recorder-central-v2`; separator style and
case are presentation, not identity.

WHAT HAPPENS WHEN IT CANNOT TELL (canon M-COVER). A directory set it cannot
attribute is UNPARSEABLE INPUT, and unparseable input is a failure, never a
silent pick. `ReleaseSetError` names the offending directory and is raised for:

  * a release dir whose name does not parse as `[<board>-]v<N>[.<N>...]-<date>`;
  * a board-prefixed dir naming a board this project does not build;
  * a BARE `v1.0-<date>` dir in a project that builds more than one board
    (it names no board, and more than one is possible);
  * a request for "the latest" with no board named, when more than one board
    has releases.

Callers turn that into their own verdict. This module refuses to guess.
"""
import re
from pathlib import Path

#: Release dir name -> (board-prefix, version). Two shapes ship in this fleet:
#:   bare            v1.2-2026-07-23
#:   board-prefixed  cooksense-v1.1-2026-07-24 / crow-recorder-central-v2-v1.0-…
#: The greedy board group makes the LAST v-token before the date the release
#: version, so a board whose own name ends in -v2 (crow-recorder-central-v2)
#: parses as board='crow-recorder-central-v2', ver=1.0 — not ver=2.
#: HISTORY: the original regex was `^v(...)` only, so EVERY board-prefixed
#: release silently skipped release_freshness_check's stale-artifact check
#: (2026-07-24) — the same silent-skip class as the M-REL glob bug.
_NAME_RE = re.compile(r"^(?:(?P<board>.+)-)?v(?P<ver>\d+(?:\.\d+)*)(?=-|$)")


class ReleaseSetError(Exception):
    """The release directory set cannot be attributed to boards.

    Raised rather than resolved: this is the input a gate must refuse.
    """


def slug(name):
    """Board name -> comparison slug: lowercase, `_`/whitespace -> `-`.

    `crow_recorder_central_v2` (the .kicad_pcb stem) and
    `crow-recorder-central-v2` (the release prefix) are ONE board.
    """
    return re.sub(r"[\s_]+", "-", str(name).strip()).strip("-").lower()


def parse_release_name(dirname):
    """`'cooksense-v1.10-2026-07-26'` -> `('cooksense', (1, 10))`, else None.

    The board component is the RAW prefix (un-slugged), so a caller echoing it
    back prints the spelling that is on disk.
    """
    m = _NAME_RE.match(str(dirname))
    if not m:
        return None
    return (m.group("board") or "",
            tuple(int(x) for x in m.group("ver").split(".")))


def _version_key(dirname):
    """Back-compat alias for `parse_release_name` — the name
    `release_freshness_check.py` and `policy_audit.py` already import."""
    return parse_release_name(dirname)


def same_board(a, b):
    """Do two release dir names name the same board series?"""
    ka, kb = parse_release_name(a), parse_release_name(b)
    if ka is None or kb is None:
        return False
    return slug(ka[0]) == slug(kb[0])


def board_slugs(project):
    """The boards this project BUILDS: slugged stems of 04_kicad/*.kicad_pcb.

    Empty when the project has no `04_kicad/` yet (a scratch tree, or a board
    commissioned but not generated). Callers must read empty as "no declared
    identity", not as "no boards" — see `index()`.
    """
    kd = Path(project) / "04_kicad"
    if not kd.is_dir():
        return []
    return sorted({slug(p.stem) for p in kd.glob("*.kicad_pcb")})


def index(project, releases_root=None):
    """-> {board_slug: [Path, ...]}, each list ordered OLDEST -> NEWEST.

    The key is `''` only when the project declares no boards at all AND its
    release dirs are bare — one anonymous series (scratch trees, and every
    pre-ADR-0007 project whose releases are `v1.0-<date>`).

    Raises `ReleaseSetError`, naming the directory it could not attribute.
    """
    project = Path(project)
    root = Path(releases_root) if releases_root else project / "07_releases"
    declared = board_slugs(project)
    out = {}
    if not root.is_dir():
        return out
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        key = parse_release_name(d.name)
        if key is None:
            raise ReleaseSetError(
                f"{root}/{d.name} does not parse as a release directory "
                f"([<board>-]v<N>[.<N>...]-<date>); the release set cannot be "
                f"attributed to a board and a gate may not pick one anyway "
                f"(canon M-COVER)")
        pfx = slug(key[0])
        if pfx:
            if declared and pfx not in declared:
                raise ReleaseSetError(
                    f"{root}/{d.name} names board {pfx!r}, which this project "
                    f"does not build (04_kicad declares {declared}); the "
                    f"release cannot be attributed, so it is refused rather "
                    f"than guessed (canon M-COVER)")
        else:
            if len(declared) > 1:
                raise ReleaseSetError(
                    f"{root}/{d.name} names NO board, but this project builds "
                    f"{len(declared)}: {declared}; a bare release name is "
                    f"unattributable here (canon M-COVER)")
            pfx = declared[0] if declared else ""
        out.setdefault(pfx, []).append(d)
    for k in out:
        out[k].sort(key=lambda p: (parse_release_name(p.name)[1], p.name))
    return out


def releases_for_board(project, board=None, releases_root=None):
    """This BOARD's release series, oldest -> newest (`[]` if it has none).

    `board` may be a board name, a `.kicad_pcb` path, or None. None is legal
    only when exactly one board has releases; otherwise the caller is asking a
    question this tree does not answer, and gets `ReleaseSetError`.
    """
    idx = index(project, releases_root)
    if board is not None:
        want = slug(Path(str(board)).stem
                    if str(board).endswith(".kicad_pcb") else board)
        if want in idx:
            return list(idx[want])
        # One anonymous (bare-named) series in a project declaring at most one
        # board: that series IS this board's, whatever the directories call it
        # (crow-mic-pod, usb-hub-3s, usb-hub-3s-v3 all ship bare names).
        if list(idx) == [""] and len(board_slugs(project)) <= 1:
            return list(idx[""])
        return []
    if not idx:
        return []
    if len(idx) > 1:
        raise ReleaseSetError(
            f"{Path(project)}/07_releases holds releases for {len(idx)} "
            f"boards ({sorted(idx)}); 'the latest release' is ambiguous until "
            f"a board is named, and picking the last directory is what shipped "
            f"the cooksense/interposer defect (canon M-COVER)")
    return list(next(iter(idx.values())))


def latest_release(project, board=None, releases_root=None):
    """This board's newest release directory, or None if it has none."""
    rels = releases_for_board(project, board, releases_root)
    return rels[-1] if rels else None


def earlier_releases(release_dir, releases_root):
    """Sibling dirs of the SAME board with a strictly-LOWER version.

    ANY earlier one, not only the immediate predecessor — a stale artifact can
    be inherited from any ancestor. Used by `release_freshness_check` check (a),
    which grades a sealed archive from its own path with no project tree
    required, so board attribution here is by release-name prefix alone.
    """
    release_dir = Path(release_dir)
    me = parse_release_name(release_dir.name)
    if me is None:
        return []
    out = []
    for sib in sorted(Path(releases_root).iterdir()):
        if not sib.is_dir() or sib.resolve() == release_dir.resolve():
            continue
        v = parse_release_name(sib.name)
        if v is not None and slug(v[0]) == slug(me[0]) and v[1] < me[1]:
            out.append(sib)
    return out
