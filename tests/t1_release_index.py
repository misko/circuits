#!/usr/bin/env python3
"""T1: RELEASE SELECTION — which release belongs to which board, and which of
them is newest (`skills/jlcpcb-fab/scripts/release_index.py`).

THE DEFECT CLASS: release selection picks the WRONG release and says nothing.
Three instances, all silent wrong answers rather than missing features:

  1. **`rels[-1]` across a MULTI-BOARD project.** `smc0985-cooksense` builds
     TWO boards and its `07_releases/` holds both series::

         cooksense-v1.0-2026-07-23 … cooksense-v1.4-2026-07-26
         interposer-v1.0-2026-07-24

     Under any order whose leading component is the board prefix,
     `interposer-…` lands LAST, so "the latest release" resolved to the
     INTERPOSER while `policy_audit.py` was grading the COOKSENSE board
     (`04_kicad/*.kicad_pcb` sorted -> `cooksense.kicad_pcb`). M-REL, M-BOM,
     A-POP and A-BODY reported on the wrong archive, and M-REL demanded
     `SUPERSEDED.md` on `cooksense-v1.4` — the LIVE cooksense release — which
     blocked a v1.5 seal. MEASURED in the tree, 2026-07-27.
  2. **TEXT version order**: `v1.10` < `v1.9` because '1' < '9'
     (usb-hub-3s-v3 v1.10, 2026-07-27). Fixed in policy_audit but re-derived
     independently in `shopping_list.newest_release_boms`, which still
     compared `d.name > prev[0]` — so the class was closed at its INSTANCE,
     not at its WIDTH (canon M-WIDTH). Pinned here at the width.
  3. `_version_key`'s `^v` regex opted every board-prefixed release out of
     release_freshness's stale check (2026-07-24). Closed; `t_prefixed_names_
     parse` keeps it closed at the shared implementation.

RED-VERIFICATION (procedure: tests/README.md §Adding a regression). The
pre-fix selection is the two-line expression policy_audit shipped::

    rels = sorted((str(p) for p in _reldir.glob("*")
                   if p.is_dir() and re.match(r"(?:.+-)?v\\d", p.name)),
                  key=lambda s: (_version_key(Path(s).name) or ("", ()), s))
    latest = Path(rels[-1])

`t_the_pre_fix_selector_is_reproduced_and_wrong` runs THAT EXPRESSION against
the real, unmodified `07_releases/` tree in this repo and asserts it returns
the interposer — so the red side is not a claim in a docstring, it is measured
on every run. Measured 2026-07-27 on the tree as sealed:

    pre-fix  latest = interposer-v1.0-2026-07-24   (board graded: cooksense)
    fixed    latest = cooksense-v1.4-2026-07-26
    pre-fix  rels[:-1] demanded SUPERSEDED.md on 4 dirs, incl. cooksense-v1.4
    fixed    rels[:-1] demands it on 3, all of which have it

The policy_audit end-to-end halves live in `t1_audit.py`
(`t_mrel_scopes_to_the_board_under_audit` and the two unattributable cases),
each red-verified by restoring that expression in the script itself.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (ROOT, check, contains, eq, main, test,  # noqa: E402
                     tmpdir)

sys.path.insert(0, str(ROOT / "skills" / "jlcpcb-fab" / "scripts"))
import release_index as ri  # noqa: E402

COOK = ROOT / "projects" / "smc0985-cooksense"          # READ-ONLY, immutable


def _proj(boards, releases):
    """A scratch project: `boards` are 04_kicad/<name>.kicad_pcb stems (a
    minimal but genuinely loadable board), `releases` are 07_releases/ dirs."""
    d = tmpdir("relidx_")
    if boards:
        (d / "04_kicad").mkdir(parents=True)
        for b in boards:
            (d / "04_kicad" / f"{b}.kicad_pcb").write_text(MINI_PCB)
    for r in releases:
        (d / "07_releases" / r).mkdir(parents=True)
    return d


MINI_PCB = """(kicad_pcb (version 20221018) (generator test)
  (general (thickness 1.6))
  (paper "A4")
  (layers
    (0 "F.Cu" signal)
    (31 "B.Cu" signal)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (44 "Edge.Cuts" user)
  )
  (setup)
)
"""


# --------------------------------------------------- version ordering (M-WIDTH)
@test("release versions order NUMERICALLY per component, not as text")
def t_numeric_version_order():
    names = ["v1.9-2026-07-27", "v1.10-2026-07-27", "v1.2-2026-07-23",
             "v2.0-2026-07-28"]
    got = sorted(names, key=lambda n: ri.parse_release_name(n)[1])
    eq(got, ["v1.2-2026-07-23", "v1.9-2026-07-27", "v1.10-2026-07-27",
             "v2.0-2026-07-28"], "numeric release order")
    # and the text order this replaces is measurably different
    check(sorted(names) != got,
          "the fixture cannot distinguish text order from numeric order — "
          "it proves nothing")


@test("board-prefixed release names parse, and a board ending in -v2 keeps "
      "its own version")
def t_prefixed_names_parse():
    eq(ri.parse_release_name("cooksense-v1.10-2026-07-26"),
       ("cooksense", (1, 10)), "prefixed name")
    # the 2026-07-24 `^v` regex bug: these used to parse as None and silently
    # skip release_freshness's stale-artifact check.
    eq(ri.parse_release_name("crow-recorder-central-v2-v1.0-2026-07-23"),
       ("crow-recorder-central-v2", (1, 0)), "board name ending in -v2")
    eq(ri.parse_release_name("v1.0-2026-07-21"), ("", (1, 0)), "bare name")
    eq(ri.parse_release_name("not-a-release"), None, "unparseable name")


@test("04_kicad underscores and release-dir hyphens are ONE board")
def t_slug_bridges_the_separator():
    eq(ri.slug("crow_recorder_central_v2"), "crow-recorder-central-v2",
       "slug")
    check(ri.same_board("crow-recorder-central-v2-v1.0-2026-07-23",
                        "crow-recorder-central-v2-v1.5-2026-07-25"),
          "two releases of one board read as different boards")
    check(not ri.same_board("cooksense-v1.4-2026-07-26",
                            "interposer-v1.0-2026-07-24"),
          "two DIFFERENT boards read as one series")


# ------------------------------------------------- the real cooksense tree
@test("the REAL two-board cooksense tree resolves to COOKSENSE's latest, not "
      "the last directory")
def t_cooksense_resolves_to_cooksense():
    """The free fixture: this layout exists in the tree today and produced the
    wrong answer. Opened READ-ONLY (07_releases is immutable).

    RE-DERIVED 2026-07-27, and the reason is the point. This test used to
    assert the literal names `cooksense-v1.4-2026-07-26` and
    `interposer-v1.0-2026-07-24`. It went RED hours later when interposer v1.1
    sealed -- not because resolution broke, but because A RELEASE NAME IS A
    GOLDEN VALUE. `tests/README.md` says assert PROPERTIES, never file bytes,
    and a hardcoded release directory is exactly a golden file wearing a
    different hat: every future seal of either board breaks it, and the next
    author's cheapest move is to bump the string, which teaches nothing.

    Worse, it hid a real failure for as long as it did: this suite ended in
    `main()` rather than `sys.exit(main())`, so it reported "2 failed" and
    exited 0, and run_tests.sh printed ALL SUITES PASSED over it.

    What actually matters here -- and what is asserted below -- is the
    SEPARATION property: each board's series contains only that board's
    releases, its latest is drawn from its own series, and the two series are
    disjoint. That is true of every future release of either board."""
    boards = ri.board_slugs(COOK)
    eq(boards, ["cooksense", "interposer"], "declared boards, read from 04_kicad")

    series = {b: [p.name for p in ri.releases_for_board(COOK, b)] for b in boards}
    for b, names in series.items():
        check(names, f"{b} has no releases at all -- fixture premise gone")
        check(all(ri.slug(n).rsplit("-v", 1)[0] == b for n in names),
              f"{b}'s series is contaminated with another board: {names}")
        latest = ri.latest_release(COOK, b)
        check(latest.name in names,
              f"{b}'s latest {latest.name} is not from its own series: {names}")
        check(latest.name == max(names, key=lambda n: ri._version_key(n)[1]),
              f"{b}'s latest is not the highest version in its series: {names}")

    check(not (set(series["cooksense"]) & set(series["interposer"])),
          "the two boards' release series overlap -- they are separate boards")
    # the defect in one line: the LAST directory by name is NOT cooksense's latest
    last_dir = sorted(p.name for p in (COOK / "07_releases").glob("*-v*"))[-1]
    check(last_dir != ri.latest_release(COOK, "cooksense").name,
          "this tree no longer exhibits the two-board hazard -- the fixture's "
          f"premise is gone and it proves nothing (last dir = {last_dir})")


@test("THE PRE-FIX SELECTOR, run against the real tree, picks the INTERPOSER",
      kind="known_bad")
def t_the_pre_fix_selector_is_reproduced_and_wrong():
    """The red side, MEASURED rather than asserted. This is verbatim the
    expression `policy_audit.py` shipped until 2026-07-27 — already numeric
    (the v1.10 fix), and still wrong, because the version tuple is the SECOND
    component of a key whose first component is the board prefix.

    Measured on the sealed tree at the time of writing: pre-fix latest =
    interposer-v1.0-2026-07-24 while the board under audit is cooksense; and
    rels[:-1] demands SUPERSEDED.md on 4 dirs including cooksense-v1.4, the
    LIVE release.

    RE-DERIVED 2026-07-27, hours later, when interposer v1.1 sealed and this
    known-bad went red. Its own failure message had predicted this in advance
    -- "the tree changed, so this fixture proves nothing until it is
    re-derived" -- and that is exactly what happened, which is the argument
    for writing such a message rather than an opaque `eq`.

    The lesson is the same one `fleet_regrade.py` was built on: some defects
    were always wrong, others BECOME wrong. A fixture pinned to a release NAME
    decays on the next seal. So the assertion is now the INVARIANT the defect
    consists of -- the pre-fix selector picks a release belonging to a
    DIFFERENT board than the one being graded -- which stays true for every
    future release of either board, and fails loudly if the two-board hazard
    ever stops existing in this tree.
    """
    reldir = COOK / "07_releases"
    prefix_rels = sorted(
        (str(p) for p in reldir.glob("*")
         if p.is_dir() and re.match(r"(?:.+-)?v\d", p.name)),
        key=lambda s: (ri._version_key(Path(s).name) or ("", ()), s))
    pre_fix_latest = Path(prefix_rels[-1]).name
    graded = sorted(p.stem for p in (COOK / "04_kicad").glob("*.kicad_pcb"))[0]
    check(ri.slug(pre_fix_latest).rsplit("-v", 1)[0] != graded,
          f"the pre-fix selector no longer reproduces the defect: it picked "
          f"{pre_fix_latest}, which belongs to the graded board {graded!r}. "
          f"The tree changed, so this fixture proves nothing until it is "
          f"re-derived.")
    check(pre_fix_latest != ri.latest_release(COOK, graded).name,
          f"pre-fix and fixed selectors now AGREE ({pre_fix_latest}) — the "
          f"known-bad has stopped being bad and must be re-derived")

    board = sorted(p.stem for p in (COOK / "04_kicad").glob("*.kicad_pcb"))[0]
    eq(board, "cooksense", "the board policy_audit grades (boards[0])")
    check(ri.slug(pre_fix_latest).split("-v1")[0] != board,
          "the pre-fix pick and the graded board must DISAGREE for this "
          "fixture to be the defect")

    # the superseded demand: pre-fix hits the LIVE cooksense release
    pre_demand = [Path(p).name for p in prefix_rels[:-1]]
    check("cooksense-v1.4-2026-07-26" in pre_demand,
          f"pre-fix SUPERSEDED demand did not reach the live release: "
          f"{pre_demand}")
    post_demand = [p.name for p in ri.releases_for_board(COOK, "cooksense")[:-1]]
    check("cooksense-v1.4-2026-07-26" not in post_demand,
          f"the FIXED selector still demands SUPERSEDED.md on the live "
          f"cooksense release: {post_demand}")
    # NOT a hardcoded count. `eq(len(pre_demand), 4)` stood here and decayed
    # the moment interposer v1.1 sealed -- the same golden-value rot as the
    # release NAMES above. The property is that the pre-fix selector demands
    # strictly MORE than the fixed one (it sweeps both boards' series), and
    # that the surplus is exactly what does not belong to the graded board.
    check(len(pre_demand) > len(post_demand),
          f"pre-fix must over-demand; it swept both boards: "
          f"pre={pre_demand} post={post_demand}")
    surplus = set(pre_demand) - set(post_demand)
    check(surplus, "pre-fix and fixed demand sets are identical — the "
                   "two-board hazard is gone and this fixture is inert")
    check(all(ri.slug(n).rsplit("-v", 1)[0] != "cooksense" or
              n == ri.latest_release(COOK, "cooksense").name for n in surplus),
          f"the surplus should be the OTHER board's releases plus cooksense's "
          f"own LIVE one, and is not: {sorted(surplus)}")
    for n in post_demand:
        check((COOK / "07_releases" / n / "SUPERSEDED.md").is_file(),
              f"{n} is demanded and does not have SUPERSEDED.md")


# ------------------------------------- cannot determine => FAIL, never guess
@test("'the latest release' with NO board named REFUSES on a multi-board "
      "project", kind="known_bad")
def t_unnamed_board_on_a_multi_board_project_refuses():
    """canon M-COVER: an ambiguous directory set is unparseable input, and a
    gate may not pick one anyway. The alternative — returning the last
    directory — is exactly the defect."""
    d = _proj(["boarda", "boardb"],
              ["boarda-v1.0-2026-01-01", "boarda-v1.1-2026-01-02",
               "boardb-v1.0-2026-01-03"])
    try:
        got = ri.latest_release(d)
    except ri.ReleaseSetError as e:
        contains(str(e), "ambiguous", "the refusal must say why")
        contains(str(e), "boarda", "and name the candidates")
        return
    raise AssertionError(
        f"SHOULD HAVE REFUSED but returned {got} — this is the silent pick")


@test("a release naming a board the project does NOT build is REFUSED",
      kind="known_bad")
def t_unknown_board_prefix_refuses():
    d = _proj(["boarda"], ["boarda-v1.0-2026-01-01", "ghost-v1.0-2026-01-02"])
    try:
        ri.index(d)
    except ri.ReleaseSetError as e:
        contains(str(e), "ghost", "the refusal must NAME the stray dir")
        contains(str(e), "boarda", "and the boards actually built")
        return
    raise AssertionError("SHOULD HAVE REFUSED an unattributable release dir")


@test("a BARE release name in a multi-board project is REFUSED",
      kind="known_bad")
def t_bare_name_in_a_multi_board_project_refuses():
    """`v1.0-<date>` names no board. With one board that is unambiguous (most
    of this fleet ships that form); with two it is not, and guessing is what
    the cooksense defect was."""
    d = _proj(["boarda", "boardb"], ["v1.0-2026-01-01"])
    try:
        ri.index(d)
    except ri.ReleaseSetError as e:
        contains(str(e), "NO board", "the refusal must say what is missing")
        return
    raise AssertionError("SHOULD HAVE REFUSED a bare name in a 2-board project")


@test("a directory that is not a release at all is REFUSED, not ignored",
      kind="known_bad")
def t_unparseable_dir_refuses():
    d = _proj(["boarda"], ["boarda-v1.0-2026-01-01", "scratch-notes"])
    try:
        ri.index(d)
    except ri.ReleaseSetError as e:
        contains(str(e), "scratch-notes", "must name the dir it choked on")
        return
    raise AssertionError("SHOULD HAVE REFUSED an unparseable release dir")


# --------------------------------------------------- the shapes that DO work
@test("every shipped naming shape in this fleet resolves, and to one board "
      "each")
def t_the_whole_fleet_resolves():
    """COVERAGE, stated (canon M-COVER): the fleet ships bare names
    (crow-mic-pod, usb-hub-3s, usb-hub-3s-v3), board-prefixed names
    (crow-mic-pod-v2, crow-recorder-central-v2), a board whose own name ends
    in -v2, a project whose .kicad_pcb stem does NOT match its directory
    (usb-hub-3s-v3 builds `usb_hub_3s_v2.kicad_pcb`), and one two-board
    project. All of them are resolved here, read-only, with a denominator."""
    projects = sorted(p for p in (ROOT / "projects").glob("*") if p.is_dir())
    resolved = with_rels = 0
    for p in projects:
        idx = ri.index(p)                       # raises if unattributable
        resolved += 1
        if idx:
            with_rels += 1
            for b, dirs in idx.items():
                vers = [ri.parse_release_name(x.name)[1] for x in dirs]
                check(vers == sorted(vers),
                      f"{p.name}/{b}: series not in ascending version order: "
                      f"{[x.name for x in dirs]}")
    eq(resolved, len(projects),
       f"projects resolved (of {len(projects)} in projects/)")
    check(with_rels >= 7,
          f"only {with_rels} projects have releases — the denominator is too "
          f"small for this to be a fleet claim")


@test("a project with ONE board and bare release names resolves to that board")
def t_bare_names_with_one_board():
    d = _proj(["usb_hub_3s_v2"], ["v1.9-2026-07-27", "v1.10-2026-07-27"])
    eq(ri.latest_release(d, "usb_hub_3s_v2").name, "v1.10-2026-07-27",
       "bare series, one board, double-digit minor")
    eq(ri.latest_release(d).name, "v1.10-2026-07-27",
       "and with no board named (only one series exists)")


@test("a board with no releases returns [] — not another board's series")
def t_board_without_releases():
    d = _proj(["boarda", "boardb"], ["boarda-v1.0-2026-01-01"])
    eq(ri.releases_for_board(d, "boardb"), [], "boardb has no releases")
    eq(ri.latest_release(d, "boardb"), None, "and no latest")
    eq(ri.latest_release(d, "boarda").name, "boarda-v1.0-2026-01-01",
       "boarda's own")


@test("earlier_releases stays inside the board series")
def t_earlier_releases_scoped():
    rels = COOK / "07_releases"
    got = [p.name for p in
           ri.earlier_releases(rels / "cooksense-v1.4-2026-07-26", rels)]
    check("interposer-v1.0-2026-07-24" not in got,
          f"the interposer leaked into cooksense's predecessors: {got}")
    eq(len(got), 3, "cooksense-v1.4's predecessors")


if __name__ == "__main__":
    sys.exit(main())
