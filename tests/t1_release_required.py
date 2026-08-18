#!/usr/bin/env python3
"""A-EVID: the REQUIRED direction of a release contract.

`contracts_audit.py` iterates FILES THAT EXIST and asks "is this permitted?".
Nothing asked "is every required file present?" until this gate. Three releases
were caught by that absence on 2026-07-26 — see release_required_check.py.
"""
import json
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


# ------------------------------------------- the PRODUCER side of A-EVID ---
EXPORT = ROOT / "skills/jlcpcb-fab/scripts/export_jlc_package.py"
USB_BOARD = ROOT / "projects/usb-hub-3s-v3/04_kicad/usb_hub_3s_v2.kicad_pcb"


@test("A-EVID producer side: the fab exporter's OWN filenames satisfy the "
      "contract — no hand-copy in between", kind="known_bad")
def t_exporter_emits_contract_names():
    """A-EVID grades the ARCHIVE. Nothing graded the PRODUCER, and the producer
    was wrong: `export_jlc_package.py` wrote `fab/bom_jlc.csv` and
    `fab/cpl_jlc.csv` while this contract — and all 34 sealed releases —
    require `fab/bom.csv` and `fab/cpl.csv`. Every seal bridged the two names
    by HAND-COPYING, which is what kept the mismatch invisible for the fleet's
    whole history.

    IT IS NOT COSMETIC. `release_freshness_check.py` resolves A-STOCK and A-BUY
    through `fab/bom.csv`. On pluto-rx2-8way-v2's staged archive the hand-copy
    did not happen, so both gates reached a ZERO DENOMINATOR and emitted NOTES
    ("no coded, placed line to grade" / "sourcing UNGRADED — 0 line(s)
    measured") rather than failures — two gates that exist BECAUSE five sealed
    releases shipped failing stock evidence, silent over an empty set. Adding
    only the two correctly-named copies flipped them to `11 graded line(s),
    verdict=PASS` / `SOURCING: CLEAR`.

    So this test runs the REAL exporter and copies its output into a release
    WITHOUT RENAMING ANYTHING — the property is that no rename is needed.

    RED-VERIFIED 2026-07-31: `bom_path = out / "bom_jlc.csv"` and
    `open(out / "cpl_jlc.csv", ...)` swapped back into the exporter and this
    test run — the exporter still exits 0, but the `must_pass` on
    `release_required_check` FAILS with
    `MISSING required artifact: fab/bom.csv` and `... fab/cpl.csv`, i.e. RED on
    exactly the two rows. Fix restored, test re-run green.

    The known-bad half is the CONTRAST at the end: put the exporter's output
    back under the legacy names and the same check must FAIL, so this test
    cannot pass by grading nothing."""
    if not USB_BOARD.exists():
        raise AssertionError(f"missing real board fixture: {USB_BOARD}")
    d = tmpdir("aevid_prod_")
    fab = d / "fabout"
    must_pass(run([KPY, EXPORT, str(USB_BOARD), str(fab), "--layers", "4"]),
              "export_jlc_package (real board)")
    artifact_index = fab / "artifact_index.json"
    check(artifact_index.is_file(),
          "exporter wrote no authoritative artifact_index.json")
    roles = set(json.loads(artifact_index.read_text())["roles"])
    check({"gerber_archive", "bom", "cpl", "drill"} <= roles,
          f"artifact index is missing required roles: {sorted(roles)}")

    rel = fixture(missing=("fab/bom.csv", "fab/cpl.csv"))
    for name in ("bom.csv", "cpl.csv"):
        src = fab / name
        check(src.exists(),
              f"the exporter wrote no {name} — the contract requires "
              f"fab/{name}, so a release cannot be assembled without a rename")
        (rel / "fab" / name).write_bytes(src.read_bytes())
    r = must_pass(run([KPY, TOOL, str(rel)]),
                  "A-EVID over a release assembled from the exporter's own "
                  "filenames, unrenamed")
    contains(r.out, "A-EVID OK", "grades clean")

    # CONTRAST (the known-bad): the pre-fix producer's names, nothing else
    # changed. A-EVID must FAIL, naming both rows.
    for cur, legacy in (("bom.csv", "bom_jlc.csv"), ("cpl.csv", "cpl_jlc.csv")):
        (rel / "fab" / cur).rename(rel / "fab" / legacy)
    rf = must_fail(run([KPY, TOOL, str(rel)]),
                   "A-EVID over the pre-fix producer's filenames", "A-EVID FAIL")
    contains(rf.out, "fab/bom.csv", "names the required BOM row")
    contains(rf.out, "fab/cpl.csv", "names the required CPL row")


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
