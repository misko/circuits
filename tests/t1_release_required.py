#!/usr/bin/env python3
"""A-EVID: the REQUIRED direction of a release contract.

`contracts_audit.py` iterates FILES THAT EXIST and asks "is this permitted?".
Nothing asked "is every required file present?" until this gate. Three releases
were caught by that absence on 2026-07-26 — see release_required_check.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, ROOT, check, contains, main, must_fail,  # noqa: E402
                     must_pass, not_contains, run, test, tmpdir)

TOOL = ROOT / "skills/kicad-pcb/scripts/release_required_check.py"

CONTRACT = """# contract: 07_releases/

## Allowed

| File | What |
|---|---|

```
07_releases/
└── <version>-<YYYY-MM-DD>/
    ├── MANIFEST.txt                REQUIRED — sha256 of EVERY file below
    ├── fab/                        REQUIRED — the JLCPCB order set
    │   ├── bom.csv                 JLC format
    │   └── cpl.csv                 JLC format
    ├── 3d/                         REQUIRED WHERE AVAILABLE — mechanical fit
    │   └── <board>.step            for enclosure checks
    └── verification/               REQUIRED — all evidence
        ├── drc.json                DRC 0/0/0
        └── erc.json                ERC 0 errors
```
"""


def fixture(missing=()):
    d = tmpdir("aevid_")
    (d / "contracts.md").write_text(CONTRACT)
    rel = d / "v1.0-2026-01-01"
    for sub in ("fab", "verification"):
        (rel / sub).mkdir(parents=True, exist_ok=True)
    for rp in ("MANIFEST.txt", "fab/bom.csv", "fab/cpl.csv",
               "verification/drc.json", "verification/erc.json"):
        if rp in missing:
            continue
        (rel / rp).write_text("x\n")
    return rel


@test("A-EVID: a release with every REQUIRED artifact passes")
def t_complete_passes():
    r = must_pass(run([KPY, TOOL, str(fixture())]), "complete release")
    contains(r.out, "A-EVID OK", "grades clean")


@test("A-EVID FAILS a release missing drc.json — the artifact whose absence "
      "hid a real defect", kind="known_bad")
def t_missing_drc_blocks():
    """THE INCIDENT (usb-hub-3s-v3 v1.6, 2026-07-26). It sealed with 13 files
    in verification/ where its contract names ~34 REQUIRED. policy_audit was
    FAIL=0, contracts_audit 187/0, M-REL green — because M-REL asks only
    whether verification/ is NON-EMPTY, and 13 files satisfied that.

    The missing evidence was not bookkeeping. `standalone_archive_drc.json`
    was among the 21 absent files, and it is the detector for exactly the
    defect v1.6 shipped: its fp-lib-table pointed at ${KIPRJMOD}/../03_src/lib,
    a path outside the archive, so 12 footprints would not load for anyone who
    extracted source/. Producing the missing artifact is what found the bug."""
    r = must_fail(run([KPY, TOOL, str(fixture(missing=("verification/drc.json",)))]),
                  "release missing drc.json", "A-EVID FAIL")
    contains(r.out, "verification/drc.json", "names the missing artifact AND its dir")


@test("A-EVID: REQUIRED is inherited by containment — a child of a REQUIRED "
      "directory is required even without the word", kind="known_bad")
def t_required_inherited():
    """The contract marks `fab/` REQUIRED and then lists bom.csv and cpl.csv
    WITHOUT repeating it. Reading only literal markers found 3 required items
    in a contract governing ~30, which would have graded a 13-file release
    complete — the precise failure this gate exists to catch. My first
    implementation did exactly that; this fixture is why it does not now."""
    r = must_fail(run([KPY, TOOL, str(fixture(missing=("fab/cpl.csv",)))]),
                  "missing child of a REQUIRED dir", "A-EVID FAIL")
    contains(r.out, "fab/cpl.csv", "an unmarked child of a REQUIRED dir is required")


@test("A-EVID: 'REQUIRED WHERE AVAILABLE' is reported, never failed")
def t_conditional_not_failed():
    """The tool cannot know whether a 3D model exists upstream. Guessing would
    be the same overreach the ALLOWED-only audit made in reverse — so a
    conditional absence is SURFACED and does not block."""
    r = must_pass(run([KPY, TOOL, str(fixture())]), "conditional absence")
    contains(r.out, "CONDITIONAL absent", "the reader is told, not blocked")


@test("A-EVID reads the MULTI-BOARD root form the TEMPLATE itself carries — "
      "`[<board>-]<version>-<date>/` is a metavariable, not a directory",
      kind="known_bad")
def t_multiboard_root_is_a_placeholder():
    """MEASURED 2026-07-27. The release-root node used to be recognised by
    `startswith("<")`, which covers `<version>-<YYYY-MM-DD>/` and NOT the
    multi-board form `[<board>-]<version>-<YYYY-MM-DD>/` that the canonical
    template gained the same day. The literal string was then prefixed onto
    EVERY artifact path, and the gate reported `31 missing, 0 present` on a
    COMPLETE release — crow-recorder-central-v2 v1.7, in the minute after its
    contract was re-synced from the template.

    A gate that cannot read the CANONICAL contract is broken against every
    project that syncs to it, and it fails on releases that are fine — the
    false-accusation direction, which trains a reader to ignore it.

    RED-VERIFIED by construction: this fixture's contract differs from
    `CONTRACT` in exactly one character run (the root node), and against the
    pre-fix `startswith("<")` filter it reports every artifact missing while
    `t_complete_passes` above, on the identical tree, passes."""
    d = tmpdir("aevid_mb_")
    (d / "contracts.md").write_text(CONTRACT.replace(
        "└── <version>-<YYYY-MM-DD>/",
        "└── [<board>-]<version>-<YYYY-MM-DD>/"))
    rel = d / "demoboard-v1.0-2026-01-01"
    for sub in ("fab", "verification"):
        (rel / sub).mkdir(parents=True, exist_ok=True)
    for rp in ("MANIFEST.txt", "fab/bom.csv", "fab/cpl.csv",
               "verification/drc.json", "verification/erc.json"):
        (rel / rp).write_text("x\n")
    r = must_pass(run([KPY, TOOL, str(rel)]),
                  "a complete release under the multi-board root form")
    contains(r.out, "A-EVID OK", "grades clean")
    not_contains(r.out, "[<board>-]",
                 "the metavariable must never appear inside a looked-for path")

    # and the teeth survive the fix: remove one artifact, it must still FAIL
    (rel / "verification" / "drc.json").unlink()
    rf = must_fail(run([KPY, TOOL, str(rel)]),
                   "multi-board root, missing artifact", "A-EVID FAIL")
    contains(rf.out, "verification/drc.json", "names the artifact AND its dir")


@test("A-EVID FAILS on a contract line it cannot parse — never silently skips",
      kind="known_bad")
def t_unparsed_is_a_failure():
    """`bom_source_check` classified refdes by leading-alpha prefix and
    SILENTLY DROPPED 12 of 26 passive rows while printing PASS. A checker that
    quietly ignores what it does not understand is the defect it exists to
    prevent, so an unreadable contract line counts as a failure."""
    rel = fixture()
    c = rel.parent / "contracts.md"
    c.write_text(c.read_text().replace("└── verification/", "|-- verification/"))
    r = must_fail(run([KPY, TOOL, str(rel)]), "unparsed contract line",
                  "A-EVID FAIL")
    contains(r.out, "UNPARSED", "says which line it could not read")


if __name__ == "__main__":
    sys.exit(main())
