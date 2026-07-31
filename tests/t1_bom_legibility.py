#!/usr/bin/env python3
"""t1_bom_legibility.py — canon F-LEGIBLE (ADR-0006).

A fab artifact is graded as its RECIPIENT will parse it, not as we wrote it.
Every BOM check this repo owned before this one asked "is this value CORRECT?";
none asked whether JLC can PARSE the file. crow-recorder-central-v2 v1.5's BOM
was uploaded and the parts "were not being picked up by their web processing".

EVERY KNOWN-BAD HERE IS A SEALED RELEASE, not a synthetic. ADR-0006 measured
that the defects supply their own fixtures, and re-measured on landing:
**25 of 26 sealed `fab/bom.csv` fail at least one of F-MPN/F-WORDS/F-ENCODE**
(the ADR said 23; the two it missed are `crow-recorder-central/v1.0` — 139 blank
MPN, no encoding defect because it has no `Ω` — and `usb-hub-3s/v1.0`, which has
NO MPN COLUMN AT ALL and so was excluded from the ADR's own 914/1205 denominator
rather than counted as the worst case it is). Only `crow-mic-pod/v1.0` passes.

RED-VERIFICATION of the EXPORTER half is recorded per test: the pre-ADR-0006
`export_jlc_package.py` was restored from git and each exporter test confirmed
to FAIL against it, then the fix restored. See each docstring.
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (FAB_SCRIPTS, KPY, ROOT, check, contains,  # noqa: E402
                     eq, main, must_fail, must_pass, not_contains, run, test,
                     tmpdir)

sys.path.insert(0, str(FAB_SCRIPTS))
from bom_legibility_check import (MpnAuthority, comment_defect,  # noqa: E402
                                  encoding_verdict, legible_comment,
                                  load_part_mpns, read_echo)

CHECK = FAB_SCRIPTS / "bom_legibility_check.py"
EXPORT = FAB_SCRIPTS / "export_jlc_package.py"

RELEASES = ROOT / "projects"
#: the board whose BOM JLC could not process — the ADR's own incident
CROW_V15 = (RELEASES / "crow-recorder-central-v2/07_releases"
            / "crow-recorder-central-v2-v1.5-2026-07-25")
CROW_BOARD = (RELEASES / "crow-recorder-central-v2/04_kicad"
              / "crow_recorder_central_v2.kicad_pcb")
#: the one release with a COMPLETE side-file, and the three that drifted from it
USB_V15 = RELEASES / "usb-hub-3s-v3/07_releases/v1.5-2026-07-25"
USB_V18 = RELEASES / "usb-hub-3s-v3/07_releases/v1.8-2026-07-26"
USB_BOARD = (RELEASES / "usb-hub-3s-v3/04_kicad/usb_hub_3s_v2.kicad_pcb")
#: ARCHIVED 2026-07-28 — superseded by their -v2/-v3 successors and moved to
#: archived_projects/, which the archive contract keeps precisely so boards can
#: go on serving as FROZEN regression fixtures. These two are fixtures; the
#: sealed releases are immutable, so only the path moved.
ARCHIVED = ROOT / "archived_projects"
#: the release that ships NO MPN column at all
HUB_V10 = ARCHIVED / "usb-hub-3s/07_releases/v1.0-2026-07-21"
#: the one sealed BOM that passes all three checks today
CLEAN_REL = ARCHIVED / "crow-mic-pod/07_releases/v1.0-2026-07-21"


def bom_csv(path, rows, bom_marker=False, header="Comment,Designator,"
                                                 "Footprint,MPN,LCSC"):
    """A scratch BOM built by hand — used only where a SEALED one cannot make
    the point (an empty file, an F-ECHO table JLC would have produced)."""
    text = header + "\n" + "\n".join(rows) + ("\n" if rows else "")
    path.write_bytes((b"\xef\xbb\xbf" if bom_marker else b"")
                     + text.encode("utf-8"))
    return path


# ================================================== the authority, in unit ==
@test("the MPN authority prefers the dossier's `mpn:` FIELD over its DIRECTORY")
def t_mpn_field_beats_dirname():
    """ADR-0006 says "the DIRECTORY NAME IS THE MPN". MEASURED over this
    fleet's dossiers that is true for most and FALSE for every MPN containing a
    slash, which cannot appear in a path: `02_parts/SMD2920-700/` declares
    `mpn: SMD2920-700/16N` and `02_parts/LM5116MHX-NOPB/` declares
    `mpn: LM5116MHX/NOPB`. Shipping the directory name for those puts a string
    that IS NOT THE PART NUMBER in the column whose entire job is to be the
    exact part number — the adjacent-property error, in the fix itself."""
    parts = RELEASES / "usb-hub-3s-v3/02_parts"
    table = load_part_mpns(parts)
    check(table, f"no dossiers resolved from {parts}")
    hits = {code: r for code, r in table.items() if "/" in r.mpn}
    check(hits, "no slash-bearing MPN in this fleet — fixture premise gone")
    for code, r in hits.items():
        dirname = r.source.split("/", 1)[1].replace(" (alt)", "")
        check(r.mpn != dirname,
              f"{code}: resolver returned the DIRECTORY name {dirname!r} "
              f"instead of the declared mpn: field")
        check(r.mpn.replace("/", "-") == dirname or dirname in r.mpn,
              f"{code}: {r.mpn!r} is unrelated to its dir {dirname!r}")


@test("the MPN authority READS both `alternates:` schema forms, and NEVER "
      "invents an MPN for the bare one", kind="known_bad")
def t_bare_alternates_are_not_silently_skipped():
    """A SILENT SKIP INSIDE THE AUTHORITY ITSELF, live for this file's whole
    existence. `load_part_mpns` read `alternates:` as `{lcsc:, mpn:}` mappings
    and `continue`d past anything else. MEASURED 2026-07-29 across the fleet's
    dossiers: **351 alternates are BARE STRINGS and 2 are mappings** — and one of
    those two had been written an hour earlier to work around this bug. The bare
    form is what the `02_parts` contract's own example shows
    (`alternates: [C2650259, C3188678]`) and what `electrical_invariants.py`
    reads, so the tree spoke the documented dialect and the MPN authority
    understood 0.6% of it without a word. That is the `jlc_twin`-exits-0 shape:
    a clean run over a fact nobody checked.

    AND THE OBVIOUS FIX IS WORSE THAN THE BUG, which is the second half of what
    this pins. Keying a bare alternate to the PARENT dossier's `mpn:` — as the
    mapping branch already does when `mpn:` is omitted — writes a FALSE part
    number into the column whose entire job is to be the exact part number. The
    measured case is `02_parts/MCP23017-E-SS`, whose alternate `C47023` is
    `MCP23017-E/SO`: a SOIC-28W part needing a different footprint, not the
    SSOP-28 the dossier is about. So a bare alternate resolves a KNOWN CODE with
    an UNDECLARED MPN: never returned by `resolve()`, reachable by
    `known_without_mpn()` for the diagnosis, and COUNTED in `describe()`.

    RED-VERIFIED 2026-07-29 against `git show HEAD:...bom_legibility_check.py`
    restored in place: `known_without_mpn` does not exist (AttributeError), and
    `load_part_mpns` over a dossier whose only sourcing is a bare alternate
    returns `{}` — 0 codes, no warning. Fix restored: the code is keyed, its MPN
    is empty, and `describe()` says how many such entries there are.

    THE THIRD THING IT PINS is a bug the FIX introduced and the suite caught:
    `C79924` (crow-recorder-central-v2 U9) is both its own dossier's
    `sourcing.lcsc` AND a bare alternate of another dossier. Registered with
    `setdefault` in filesystem order the empty-MPN placeholder landed first and
    permanently shadowed the real answer — a fix for a silent skip introducing a
    silent skip, on a row that had been resolving correctly. Precedence is by
    INFORMATION CONTENT now, and that is asserted on the real tree below."""
    import yaml as _yaml

    # --- the fleet premise: the bare form is the DOMINANT form, not an edge case
    bare, mapping = [], []
    for y in sorted((ROOT / "projects").glob("*/02_parts/*/part.yaml")):
        d = _yaml.safe_load(y.read_text(encoding="utf-8-sig")) or {}
        if not isinstance(d, dict):
            continue
        for alt in ((d.get("sourcing") or {}).get("alternates") or []):
            (mapping if isinstance(alt, dict) else bare).append((y, alt))
    check(len(bare) > len(mapping),
          f"{len(bare)} bare vs {len(mapping)} mapping-form alternates — the "
          f"premise of this test (the bare form is what the fleet actually "
          f"writes) has changed; RE-MEASURE before editing it")

    # --- a bare alternate is READ, and carries NO MPN
    d = tmpdir("altschema_")
    p = d / "PART-A"
    p.mkdir()
    (p / "part.yaml").write_text(
        "mpn: PART-A\nsourcing:\n  lcsc: C111111\n"
        "  alternates: [C222222, 'C333333 (a note about the part)',\n"
        "               'PCM1864DBTR']\n")
    table = load_part_mpns(d)
    eq(table["C111111"].mpn, "PART-A", "the dossier's own code must resolve")
    for code in ("C222222", "C333333"):
        check(code in table,
              f"{code} is declared as a BARE alternate and the MPN authority "
              f"cannot see it — 351 of the fleet's 353 alternates are this "
              f"shape, and every one was invisible")
        eq(table[code].mpn, "",
           f"{code} was given an MPN it does not have. A bare alternate declares "
           f"NO part number, and inheriting the parent's puts a string that is "
           f"NOT the part number in the MPN column (C47023 is MCP23017-E/SO, "
           f"not the -E/SS its dossier is about)")
    eq(sorted(table), ["C111111", "C222222", "C333333"],
       "the bare entry that names NO LCSC code (`PCM1864DBTR`) must key "
       "nothing — a free-text note is not a code, and guessing at one would be "
       "the same invention as inheriting the parent MPN")

    auth = MpnAuthority(d)
    eq(auth.resolve("C222222"), None,
       "resolve() returned an MPN-LESS entry, so every consumer now believes "
       "the authority named a part number for a code it cannot name")
    check(auth.known_without_mpn("C222222"),
          "the code is neither resolvable NOR reportable — that is the silent "
          "skip again, just moved")
    contains(auth.describe(), "BARE",
             "the authority must COUNT the entries it could only half-read "
             "(canon M-COVER)")

    # --- a code that is BOTH a real sourcing.lcsc and someone's bare alternate
    # must resolve to the REAL MPN, whatever order the dossiers are read in
    crow = MpnAuthority(RELEASES / "crow-recorder-central-v2/02_parts")
    hit = crow.resolve("C79924")
    check(hit and hit.mpn,
          "C79924 (U9) is its own dossier's sourcing.lcsc AND a bare alternate "
          "elsewhere; an empty-MPN placeholder has shadowed the real answer, "
          "which BREAKS a row that used to resolve")


@test("F-WORDS refuses the three measured shapes and NOTHING ELSE")
def t_comment_defect_is_narrow():
    """A legibility test that over-reaches is worse than none: widening it to
    'looks like it has no unit' would start rejecting `AON6403`, `XT60PW-M`,
    `SS12D07VG6-087` — legitimate part names, and exactly the MPN fallback this
    change ships. Refuse blank / an LCSC code / a `simple_*` placeholder."""
    for bad in ("", "   ", "C82317", "C1525", "simple_inductor", "simple_chip"):
        check(comment_defect(bad) is not None, f"F-WORDS accepted {bad!r}")
    for good in ("1nF", "4.12kOhm", "10uF 50V", "AON6403", "XT60PW-M",
                 "SS12D07VG6-087", "0402WGF1603TCE", "LM5116MHX/NOPB",
                 "Chip_LED_0805", "100nF / 1uF"):
        eq(comment_defect(good), None, f"F-WORDS rejected legitimate {good!r}")


@test("no dossier hides its LCSC in a bare top-level `lcsc:` — the F-MPN "
      "authority reads ONE home")
def t_dossier_lcsc_has_one_home():
    """MEASURED 2026-07-27, and it is a COVERAGE hole, not a style point. The
    `02_parts/` contract's schema is `sourcing: {lcsc: C…}` and
    `load_part_mpns()` reads exactly that. SIX of 204 dossiers declared a bare
    top-level `lcsc:` instead — five on crow-recorder-central-v2 (including
    C79924/U9, C237284/L2, C3716677/the four beads, C882626/L1) — so their
    parts were INVISIBLE to the MPN authority even though the repo knew the
    answer, and F-MPN condemned their rows as unresolvable. `bom_source_check`
    leg C and `shopping_list` read the same one home and were equally blind;
    only `part_facts_check` tolerated both, which is how the drift survived.

    Fixed at the SOURCE (the six dossiers), not by teaching the resolver a
    second home — a second home for a fact that already has one is the whole
    subject of ADR-0006. This test is what stops the seventh one appearing.

    RED-VERIFIED 2026-07-27: with the six pre-fix dossiers stashed back in
    (`git stash push projects/*/02_parts`), this file reports 18 passed /
    2 failed and this test names all six paths. Restored: 20 / 0."""
    import yaml as _yaml
    bare = []
    for y in sorted((ROOT / "projects").glob("*/02_parts/*/part.yaml")):
        d = _yaml.safe_load(y.read_text()) or {}
        if isinstance(d, dict) and d.get("lcsc") and not (
                isinstance(d.get("sourcing"), dict)
                and d["sourcing"].get("lcsc")):
            bare.append(str(y.relative_to(ROOT)))
    check(not bare,
          f"{len(bare)} dossier(s) declare a bare top-level `lcsc:`, which the "
          f"F-MPN authority does not read — move it into the `sourcing:` "
          f"block the 02_parts contract mandates: {bare}")


@test("an UNCODED row falls back to its FOOTPRINT, and a CODED one never does")
def t_footprint_fallback_is_narrow():
    """The last legible fact the SOURCE holds about a row JLC will never match
    on. crow-recorder-central-v2 ships JP_INJ and J_DBG `dnp_by_design` with a
    deliberately BLANK LCSC (declared with evidence in assembly.yaml) and a
    board Value of `simple_chip` — a tscircuit placeholder that cannot be
    fixed without regenerating the board, i.e. without moving copper on a
    sealed design. `PinHeader_1x03_P2.54mm_Vertical` is something a human can
    read and check; a blank is not.

    The narrowness is the point: the fallback fires ONLY when the authority
    resolved nothing, so it can never launder a coded row's Comment. A coded
    row either carries its MPN or FAILS F-MPN."""
    from bom_legibility_check import MpnRes  # noqa: PLC0415
    eq(legible_comment("simple_chip", None, "PinHeader_1x03_P2.54mm_Vertical"),
       "PinHeader_1x03_P2.54mm_Vertical", "uncoded row keeps nothing legible")
    eq(legible_comment("simple_chip", None, ""), "",
       "with no footprint either there is nothing to say — still blank")
    res = MpnRes("TLV70018DDCR", "", "02_parts/TLV70018DDCR")
    eq(legible_comment("simple_chip", res, "SOT-23-5"), "TLV70018DDCR",
       "a RESOLVED row must use its MPN, never the footprint")
    eq(legible_comment("1nF", None, "C_0402_1005Metric"), "1nF",
       "a legible board Value always wins")


@test("every fab-CSV reader in the fleet tolerates the UTF-8 byte-order-mark "
      "F-ENCODE now puts on the BOM", kind="known_bad")
def t_readers_survive_the_bom_marker():
    """THE DEFECT F-LEGIBLE'S OWN FIX CREATED, caught while cutting the first
    release that carries the marker.

    ADR-0006 chose a UTF-8 byte-order-mark as the F-ENCODE remedy. `csv`
    folds it into the FIRST HEADER NAME, so a reader that opens the file as
    plain utf-8 sees a column called `\\ufeffComment` and `row.get("Comment")`
    returns None on EVERY row. MEASURED 2026-07-27 on crow-recorder-central-v2
    v1.6's staged BOM: `bom_source_check` leg C went from **25/25 R/C rows
    value-graded to 0/25**, reported as 25 COVERAGE-GAP lines and STILL A
    PASS. Fourteen reader sites across four skills had the same shape.

    Both halves are asserted: the BEHAVIOUR (the same BOM, marked and unmarked,
    must grade identically) and the SHAPE (no fab-CSV `open()` may omit the
    encoding), because behaviour alone would not stop the fifteenth site.

    RED-VERIFIED 2026-07-27: with the fourteen `encoding="utf-8-sig"` arguments
    reverted, this test reports the coverage disagreement (25/25 vs 0/25) and
    lists the offending call sites."""
    import re
    d = tmpdir("bommark_")
    src = (CROW_V15 / "fab" / "bom.csv").read_bytes()
    check(not src.startswith(b"\xef\xbb\xbf"), "fixture already marked")
    plain, marked = d / "plain.csv", d / "marked.csv"
    plain.write_bytes(src)
    marked.write_bytes(b"\xef\xbb\xbf" + src)
    src_check = FAB_SCRIPTS / "bom_source_check.py"
    cj = RELEASES / "crow-recorder-central-v2/03_tscircuit/build/circuit.json"
    out = {}
    for name, p in (("plain", plain), ("marked", marked)):
        r = run([KPY, src_check, p, cj, "--parts",
                 RELEASES / "crow-recorder-central-v2/02_parts"])
        m = re.search(r"coverage leg C: (\d+)/(\d+)", r.out)
        out[name] = m.group(0) if m else f"(no coverage line)\n{r.out}"
    eq(out["marked"], out["plain"],
       "the SAME BOM grades differently with a byte-order-mark — a reader is "
       "seeing '\\ufeffComment' instead of 'Comment'")
    contains(out["plain"], "/25", "fixture premise: 25 R/C rows are gradeable")

    # the shape: any open() of something named bom/cpl must name the encoding
    OPEN = re.compile(r"\bopen\(\s*[^)]*\b(?:bom|cpl)\w*\b[^)]*\)")
    offenders = []
    for py in sorted((ROOT / "skills").rglob("*.py")):
        for m in OPEN.finditer(py.read_text()):
            if "utf-8-sig" not in m.group(0) and '"w"' not in m.group(0):
                offenders.append(f"{py.relative_to(ROOT)}: {m.group(0)[:70]}")
    check(not offenders,
          f"{len(offenders)} fab-CSV open() call(s) do not name "
          f"encoding='utf-8-sig', so a byte-order-marked BOM silently loses "
          f"its first column: {offenders}")


@test("F-ENCODE is INDIFFERENT to how the ambiguity is removed")
def t_encode_indifferent():
    """ADR-0006: "the fix is a BOM marker or ASCII `Ohm`, and the check is
    indifferent to which". A check that mandated one would be a style rule
    wearing a gate's docstring. What must FAIL is the state 23 of 26 sealed
    BOMs are in: valid UTF-8, carrying non-ASCII, with nothing to tell a cp936
    reader it is wrong."""
    ok, why = encoding_verdict("Comment\n4.12kOhm\n".encode("utf-8"))
    check(ok, f"ASCII 'Ohm' rejected: {why}")
    ok, why = encoding_verdict(b"\xef\xbb\xbf" + "Comment\n4.12kΩ\n"
                               .encode("utf-8"))
    check(ok, f"UTF-8 BOM marker rejected: {why}")
    ok, why = encoding_verdict("Comment\n4.12kΩ\n".encode("utf-8"))
    check(not ok, "bare non-ASCII UTF-8 with no BOM marker PASSED — that is "
                  "the exact state of 23 of 26 sealed BOMs")
    contains(why, "cp936", "the failure names the recipient's codepage")


# =============================================== the SEALED known-bads ======
@test("the SEALED crow-recorder-central-v2 v1.5 BOM FAILS all three checks",
      kind="known_bad")
def t_sealed_crow_v15_fails():
    """THE INCIDENT. This is the BOM that was uploaded to JLCPCB and whose parts
    "were not being picked up by their web processing". Sealed bytes, opened
    read-only (canon M-SHIP). It must fail on all three axes at once:
    F-ENCODE (303 `Ω` fleet-wide, no BOM marker), F-MPN (47 coded rows, every
    MPN blank), F-WORDS (24 of 49 Comments are an LCSC code or `simple_*`)."""
    r = must_fail(run([KPY, CHECK, CROW_V15]), "F-LEGIBLE on the sealed v1.5")
    for cid in ("F-ENCODE", "F-MPN", "F-WORDS"):
        contains(r.out, f"FAIL {cid}", f"{cid} finding on the incident BOM")
    contains(r.out, "coverage F-MPN", "the verdict carries an N/M denominator")
    contains(r.out, "simple_", "F-WORDS names the generator placeholder")


@test("a sealed BOM with NO MPN COLUMN AT ALL is a FAIL, never a skip",
      kind="known_bad")
def t_no_mpn_column_is_a_fail():
    """usb-hub-3s v1.0 ships `Comment,Designator,Footprint,LCSC` — no MPN
    column. ADR-0006's own headline (914/1205 blank MPN) EXCLUDES this file's
    48 rows, because a column that does not exist has no blanks to count: the
    true fleet figure is 962/1205. A denominator that shrinks when the defect
    gets worse is the M-COVER failure shape, so the missing column gets its own
    named finding rather than 48 silent passes."""
    r = must_fail(run([KPY, CHECK, HUB_V10]), "F-LEGIBLE on a column-less BOM")
    contains(r.out, "NO MPN COLUMN", "the missing column is named")
    contains(r.out, "never a skip", "and is stated as a FAIL, not a skip")


@test("the two match paths DISAGREE on usb-hub-3s-v3 v1.5-v1.8's SW1",
      kind="known_bad")
def t_sidefile_drift_is_caught():
    """THE FIND THIS GATE MADE ON LANDING, and the ADR's thesis in one row.
    v1.5-v1.8 ship `MPN = 'SS12D07VG6 087'` (a SPACE) for C2939728 while
    `02_parts/SS12D07VG6-087/part.yaml` declares `SS12D07VG6-087` (a HYPHEN).
    That is the hand-maintained side-file having drifted from the dossier, on
    the ONE board that ever maintained it — which is why F-MPN requires the two
    paths to AGREE and does not merely require the column to be non-empty. A
    check that only tested "is it blank?" would pass this."""
    r = must_fail(run([KPY, CHECK, USB_V18]), "F-LEGIBLE on v1.8")
    contains(r.out, "DISAGREE", "the two-path disagreement is named")
    contains(r.out, "SS12D07VG6", "and names the part")
    contains(r.out, "C2939728", "and its code")


@test("a BOM with ZERO data rows is a FAIL (M-COVER), not a clean bill",
      kind="known_bad")
def t_empty_bom_fails():
    """A gate may not pass while grading nothing. Header-only is the shape a
    truncated export produces, and it is the shape that would let this whole
    family be silenced by deleting rows."""
    d = tmpdir("bomleg_")
    p = bom_csv(d / "bom.csv", [], bom_marker=True)
    must_fail(run([KPY, CHECK, p]), "F-LEGIBLE on an empty BOM", "ZERO data rows")


@test("a coded row that resolves NO MPN FAILS — never a silent blank",
      kind="known_bad")
def t_unresolvable_code_fails():
    """`mpn_map.get(code, "")` is the defect ADR-0006 names: a miss produced a
    blank column with no warning, the `row_kind` shape canon M-COVER forbids.
    C0000001 exists in no dossier and no ledger; the row must be REFUSED, and
    the finding must say the code, not just 'a row'.

    AMENDED 2026-07-29 (the M-SHIP verdict split). This fixture's row carries a
    BLANK MPN as well as an unresolvable code, so it now exercises the
    SELF-CONTAINED half of the split — a coded row with no MPN is a defect in the
    SHIPPED BYTES and is graded without consulting any authority, which is why it
    stays a FAIL even where immutability forbids a fix. The halves it no longer
    covers are pinned separately by `t_sealed_unresolvable_is_ungraded`:
    unresolvable + a NON-BLANK MPN on an immutable target is UNGRADEABLE, and the
    same bytes on a MUTABLE target are still a FAIL."""
    d = tmpdir("bomleg_")
    p = bom_csv(d / "bom.csv", ["1nF,C1,C_0402,,C0000001"], bom_marker=True)
    r = must_fail(run([KPY, CHECK, p]), "F-LEGIBLE on an unresolvable code",
                  "resolves NO MPN")
    contains(r.out, "C0000001", "the finding names the code")


@test("F-ECHO FAILS a JLC resolved table that SUBSTITUTED our code",
      kind="known_bad")
def t_echo_catches_substitution():
    """THE ONLY THING THAT WOULD HAVE CAUGHT C82317 -> C131025. Our source said
    C82317 for crow-recorder-central-v2's U5 in three places — part.yaml, the
    .tsx and the shipped BOM — and JLC's resolved output said C131025. All
    three of our own checks agree with each other and are blind to it, because
    they all read the document the way WE wrote it (canon M1).
    SYNTHETIC BY NECESSITY, and this is the one place in this file where that
    is true: JLC's resolved table is produced inside their UI by a human and no
    copy of it lives in this repo. The CODES are the real ones."""
    d = tmpdir("bomleg_")
    p = bom_csv(d / "bom.csv", ["ES9018K2M,U5,QFN-28,ES9018K2M,C82317"],
                bom_marker=True)
    echo = d / "jlc_resolved.csv"
    echo.write_text("Designator,LCSC,JLC Matched Part\nU5,C82317,C131025\n")
    r = must_fail(run([KPY, CHECK, p, "--echo", echo]), "F-ECHO substitution",
                  "F-ECHO SUBSTITUTION")
    contains(r.out, "C131025", "the finding names what JLC resolved to")
    contains(r.out, "C82317", "and what we asked for")


@test("F-ECHO FAILS when NOT ONE of our codes appears in the resolved table",
      kind="known_bad")
def t_echo_zero_overlap_fails():
    """A zero denominator is a FAIL, not a clean bill — the same rule the rest
    of this family obeys. Pointing --echo at the wrong file must not read as
    'no substitutions found'."""
    d = tmpdir("bomleg_")
    p = bom_csv(d / "bom.csv", ["1nF,C1,C_0402,0402B102K500NT,C1523"],
                bom_marker=True)
    echo = d / "other.csv"
    echo.write_text("Designator,LCSC,JLC Matched Part\nQ9,C999999,C999999\n")
    must_fail(run([KPY, CHECK, p, "--echo", echo]), "F-ECHO on a foreign table",
              "F-ECHO")


@test("F-ECHO PASSES a resolved table that changed nothing")
def t_echo_clean():
    """The gate must be able to say OK, or nobody will run it."""
    d = tmpdir("bomleg_")
    p = bom_csv(d / "bom.csv", ["1nF,C1,C_0402,0402B102K500NT,C1523"],
                bom_marker=True)
    echo = d / "jlc_resolved.csv"
    echo.write_text("Designator,LCSC,JLC Matched Part\nC1,C1523,C1523\n")
    r = must_pass(run([KPY, CHECK, p, "--echo", echo]), "F-ECHO clean")
    contains(r.out, "coverage F-ECHO", "the echo verdict has a denominator")


# ====================== a SEAL MUST BE RE-DERIVABLE FROM THE SEALED BYTES ===
#: the live release whose verdict MOVED under it, twice, in one session
COOK_V16 = (RELEASES / "smc0985-cooksense/07_releases"
            / "cooksense-v1.6-2026-07-27")


def moved_on_tree(tag="mship_"):
    """(empty 02_parts, empty ledger) — the dossier tree AS IT WILL LOOK once the
    next revision has legitimately moved on.

    This is the PERTURBATION, and it is not a hypothetical: `cooksense-v1.6` was
    sealed 2026-07-27, and on 2026-07-29 the live v1.7 work removed the
    `ULN2803ADWR` dossier (v1.7 genuinely has no ULN2803) and later restored it.
    Emptying both external authorities is the same event with the timing taken
    out of it, and it is an INDEPENDENT method (canon M1): it does not ask the
    gate whether it is coupled to mutable source, it makes the coupling
    observable from outside.
    """
    d = tmpdir(tag)
    (d / "02_parts").mkdir()
    (d / "empty_ledger.yaml").write_text("{}\n")
    return d / "02_parts", d / "empty_ledger.yaml"


def sealed_scratch(rows, tag="sealed_", stock=None,
                   header="Comment,Designator,Footprint,MPN,LCSC"):
    """A scratch directory SHAPED LIKE a sealed release — `07_releases/<dir>/`
    with `fab/bom.csv` and optionally `verification/stock_check.csv`.

    Synthetic by necessity, and narrowly so: the two verdict classes being
    discriminated differ by whether the graded artifact MAY BE EDITED, and there
    is no sealed release in this repo that carries an unresolvable code together
    with a non-blank MPN (MEASURED 2026-07-29: 0 of 33). Building the case by
    hand is the only way to prove the branch exists — and it is built from the
    GOOD case broken in exactly one way, per tests/README.
    """
    d = tmpdir(tag) / "07_releases" / "board-v9.9-2026-01-01"
    (d / "fab").mkdir(parents=True)
    (d / "verification").mkdir()
    bom_csv(d / "fab" / "bom.csv", rows, bom_marker=True, header=header)
    if stock:
        (d / "verification" / "stock_check.csv").write_text(
            "Comment,Designator,Footprint,LCSC,qty,status,code,type,stock,mpn,"
            "pkg,price\n" + "".join(stock))
    return d


@test("a SEALED release's F-LEGIBLE verdict does not move when the dossier tree "
      "moves on", kind="known_bad")
def t_sealed_verdict_is_rederivable():
    """THE DEFECT, and it is measured in both directions on ONE release.

    `cooksense-v1.6-2026-07-27` is sealed and immutable. On 2026-07-29 16:15
    F-LEGIBLE FAILED it on row 39 (U_EXP, C506653) and row 56 (U_ULNA/U_ULNB,
    C9683); hours later, with not one byte of the release changed, it PASSED it
    again. What moved was `02_parts/`: the live v1.7 work removed the
    `ULN2803ADWR` dossier and then restored it. A verdict that moves under an
    immutable artifact is not evidence about that artifact, and the self-healing
    direction is the worse of the two — a red that repairs itself for an
    unrelated reason is a red nobody records.

    The property asserted is REPRODUCIBILITY, not the verdict: graded normally
    and graded with BOTH external authorities emptied, the same sealed bytes must
    not produce a different PASS/FAIL. The release carries its own code->MPN map
    (`verification/stock_check.csv`, JLC's catalog recorded at the seal, already
    a REQUIRED release artifact) and that is what makes the answer re-derivable.

    RED-VERIFIED 2026-07-29 with `git show HEAD:...bom_legibility_check.py`
    restored in place: the perturbed run exits **1 with 55 findings** against the
    unperturbed run's **0**, including `FAIL F-MPN row 39 (U_EXP): LCSC C506653
    resolves NO MPN from any authority` — i.e. the pre-fix gate condemns a sealed
    release for the state of a tree it does not contain. Fix restored: 0 and 0.
    MEASURED fleet-wide the same way: **9 of 33 sealed releases flipped
    PASS -> FAIL under this perturbation — every release that passed F-LEGIBLE at
    all, four of them LIVE — and 0 of 33 do now.**"""
    parts, ledger = moved_on_tree()
    plain = must_pass(run([KPY, CHECK, COOK_V16]), "v1.6 graded as things stand")
    moved = run([KPY, CHECK, COOK_V16, "--parts", parts, "--ledger", ledger])
    check(moved.rc == 0,
          f"the SEALED cooksense v1.6 FAILS once the dossier tree has moved on "
          f"(rc={moved.rc}). 07_releases is IMMUTABLE — no edit to this release "
          f"could ever clear that finding, so the verdict is about our tree and "
          f"not about the release:\n{moved.out[-2500:]}")
    for code, ref in (("C506653", "U_EXP"), ("C9683", "U_ULNA")):
        contains(moved.out, code,
                 f"the {ref} row ({code}) — one of the two the moved tree "
                 f"orphaned — must still be accounted for by name")
    contains(moved.out, "verification/stock_check.csv",
             "the answer must come from the map sealed INSIDE the release")
    # and it must not read as a clean bill: the equality check really did not run
    not_contains(moved.out, "F-LEGIBLE OK",
                 "a run that could not cross-check 54 rows against a "
                 "hand-verified authority reported itself as OK")
    contains(moved.out, "NOT-REDERIVABLE-FROM-SHIPPED-BYTES",
             "the verdict must carry the token a fleet sweep greps for")
    contains(plain.out, "F-LEGIBLE OK",
             "premise: v1.6 passes cleanly while its dossiers are in reach")


@test("the release-carried map is an EXISTENCE authority and is consulted LAST")
def t_release_map_is_existence_not_equality():
    """MEASURED, not assumed, and the measurement is why the ORDER is pinned.

    JLC's `componentModelEn` — the `mpn` column `jlc_stock_check.py` records — is
    a catalog DESCRIPTION, and it is not the manufacturer part number on 7 of the
    156 rows fleet-wide that have one: `436500224` for Molex `43650-0224`,
    `SMAJ5.0A-13-F` for `SMAJ5.0A`, `2.54-2*20PFemale longPC104` for
    `2.54-2*20PPC104`. Consulting it FIRST would have turned those 7 rows on four
    sealed releases — cooksense v1.5/v1.6 and crow-recorder-central-v2
    v1.6/v1.7, two of them LIVE — into false DISAGREE FAILures, which is the
    same harm as the defect being fixed, arriving from the other side.

    So: dossier -> ledger -> release-carried, and a release-carried hit is
    flagged so no caller can grade equality on it. This test fails if anyone
    reorders the resolution or drops the flag."""
    parts = RELEASES / "smc0985-cooksense/02_parts"
    auth = MpnAuthority(parts, None, COOK_V16)
    check(auth.release, "no release-carried map read from v1.6's stock_check.csv")
    eq(auth.resolve("C9683").mpn, "ULN2803ADWR",
       "the release's own sealed record must resolve the code the moved tree "
       "orphaned")

    # the divergences are real and must be REACHED THROUGH the dossier, not
    # through JLC's description
    diverge = {c: r for c, r in auth.release.items()
               if c in auth.parts and auth.parts[c].mpn != r.mpn}
    check(diverge,
          "no code where JLC's catalog description differs from the dossier's "
          "MPN — the premise of this ordering is gone, RE-MEASURE before "
          "changing the resolution order")
    for code in diverge:
        res = auth.resolve(code)
        eq(res.mpn, auth.parts[code].mpn,
           f"{code}: resolution reached JLC's catalog DESCRIPTION "
           f"{auth.release[code].mpn!r} instead of the hand-verified dossier "
           f"MPN — that is 7 false DISAGREE failures across four sealed "
           f"releases, two of them live")
        check(not MpnAuthority.release_carried(res),
              f"{code} resolved from the dossier but is flagged release-carried")
    check(MpnAuthority.release_carried(auth.release["C9683"]),
          "a release-carried resolution is not flagged as one, so a caller "
          "cannot refuse to grade equality on it")


@test("a SEALED row whose MPN CONTRADICTS its code still FAILS — immutability "
      "is not an excuse", kind="known_bad")
def t_sealed_contradiction_still_fails():
    """THE OTHER HALF OF THE DISCRIMINATION, and the class F-LEGIBLE was built
    for. A check that only ever fires one way ranks nothing.

    Two shapes, both graded on a target that MAY NOT BE EDITED, both still FAIL:

      1. the MPN DISAGREES with the authority. This is the usb-hub-3s-v3
         `SS12D07VG6 087`-vs-`SS12D07VG6-087` side-file drift, pinned on real
         sealed bytes by `t_sidefile_drift_is_caught`; here it is pinned on a
         target that also carries its OWN release map, to prove the map cannot
         launder a contradiction.
      2. a BLANK MPN on a coded row. Self-contained — it needs no authority at
         all, which is exactly why immutability can never excuse it. It is what
         JLC leaves at 'No Part Selected' and it is the v1.2 incident.

    RED-VERIFIED 2026-07-29 by inverting the fix in place — resolving the
    release-carried map FIRST, which is what the obvious implementation would do.
    This test goes RED with "does not contain 'DISAGREE'": C1523 resolves from
    the release's own map, which says exactly what the BOM says, so the
    contradiction is graded as existence-only and the finding disappears. Reduced
    to that one row alone the inverted gate EXITS 0 and prints
    NOT-REDERIVABLE-FROM-SHIPPED-BYTES (measured); in this two-row fixture the
    run still fails, but only on the OTHER row's blank MPN — which is precisely
    the shape of a laundered defect, a real finding hidden behind an unrelated
    one. Order restored: DISAGREE is back and the fixture is RED-for-the-right-
    reason again.
    """
    stock = ["1nF,C1,C_0402,C1523,1,OK,C1523,base,9000,WRONG-PART,0402,0.01\n"]
    d = sealed_scratch(["1nF,C1,C_0402,WRONG-PART,C1523",
                        "10uF,C2,C_0805,,C15850"], stock=stock)
    r = must_fail(run([KPY, CHECK, d]), "F-LEGIBLE on a sealed contradiction")
    contains(r.out, "DISAGREE",
             "a shipped MPN that contradicts the hand-verified authority must "
             "FAIL even on immutable bytes")
    contains(r.out, "C1523", "and the finding names the code")
    contains(r.out, "BLANK MPN",
             "a coded row with no MPN is a defect in the SHIPPED BYTES and "
             "needs no authority to see")
    not_contains(r.out, "NOT-REDERIVABLE-FROM-SHIPPED-BYTES",
                 "a real contradiction was downgraded to 'not gradeable' — the "
                 "whole point of the discrimination is that it does not do this")


@test("a SEALED row that resolves from NOTHING is UNGRADEABLE — never OK, and "
      "never a FAIL against bytes nobody may fix", kind="known_bad")
def t_sealed_unresolvable_is_ungraded():
    """THE NEW VERDICT CLASS. `07_releases/` is IMMUTABLE (CLAUDE.md), so a
    release sealed before `stock_check.csv` carried an `mpn` column can NEVER
    gain one, and a FAIL against it is a verdict with no remedy — it says
    'somebody fix this' about bytes nobody is permitted to touch. It is equally
    not an OK: the two-path agreement check did not run.

    So it is a THIRD verdict, and it must be impossible to mistake for either.
    What this pins: exit 0 (no defect was found — the row ships a legible
    Comment, an MPN and a code), the word UNGRADEABLE, the code, the DENOMINATOR
    (canon M-COVER), the grep token, and the ABSENCE of 'F-LEGIBLE OK'.

    RED-VERIFIED 2026-07-29 against `git show HEAD:...bom_legibility_check.py`
    restored in place: the pre-fix gate exits **1** on this fixture with
    `FAIL F-MPN row 1 (U1): LCSC C0000001 resolves NO MPN from any authority`,
    so `check(r.rc == 0)` fails and the token is absent. Fix restored: exit 0
    with the ungraded verdict.

    THE ASYMMETRY IS THE PRINCIPLE, and its other half is pinned below: the same
    BOM on a MUTABLE target is still a FAIL, because there a remedy exists."""
    row = "MCP23017-E/SS,U1,SSOP-28,MCP23017-E/SS,C0000001"
    d = sealed_scratch([row], tag="sealed_ungr_")
    r = run([KPY, CHECK, d])
    check(r.rc == 0,
          f"an unresolvable code on an IMMUTABLE release exited {r.rc} — a FAIL "
          f"against bytes nobody may edit is a verdict with no remedy, and it "
          f"is how ordinary progress on the next revision retro-fails a sealed "
          f"release:\n{r.out[-2000:]}")
    contains(r.out, "UNGRADEABLE", "the new class names itself")
    contains(r.out, "C0000001", "and names the code it could not resolve")
    contains(r.out, "NOT-REDERIVABLE-FROM-SHIPPED-BYTES",
             "the verdict carries the token the fleet sweep greps for")
    contains(r.out, "not re-derivable from the shipped bytes",
             "and the coverage line states the denominator (canon M-COVER)")
    not_contains(r.out, "F-LEGIBLE OK",
                 "an ungraded row was folded into OK — the `row_kind` silent "
                 "default canon M-COVER forbids")

    # the SAME bytes on a MUTABLE target: a remedy exists, so it is a FAIL and
    # the exporter keeps blocking before anything is ever sealed.
    loose = tmpdir("mutable_ungr_")
    p = bom_csv(loose / "bom.csv", [row], bom_marker=True)
    r2 = must_fail(run([KPY, CHECK, p]),
                   "F-LEGIBLE on an unresolvable code in a MUTABLE target",
                   "resolves NO MPN")
    contains(r2.out, "add the dossier's `sourcing.lcsc`",
             "a mutable target must be told the remedy that exists for it")


@test("a sealed release whose OWN map covers the orphaned code is CORROBORATED, "
      "and says so without claiming an equality check it did not run")
def t_release_map_corroborates():
    """The clean half of the new class, and the reason it has two sub-classes
    rather than one. `cooksense-v1.6` is the real instance (above); this pins the
    behaviour on a fixture built one way from the good case, so it survives the
    day cooksense v1.6 leaves the LIVE set.

    CORROBORATED is a weaker claim than OK and must READ that way: the code named
    a real, catalog-resolvable part with a manufacturer part number ON THE DAY OF
    THE SEAL, on JLC's own evidence, sealed inside the archive. Whether our MPN
    string EQUALS theirs is not graded, because their string is a description
    (see `t_release_map_is_existence_not_equality`)."""
    stock = ["ULN2803ADWR,U1,SOIC-18W,C9683,1,OK,C9683,expand,2315,"
             "ULN2803ADWR,SOIC-18-300mil,6.22\n"]
    d = sealed_scratch(["ULN2803ADWR,U1,SOIC-18W,ULN2803ADWR,C9683"],
                       tag="sealed_corr_", stock=stock)
    r = run([KPY, CHECK, d])
    check(r.rc == 0, f"a corroborated release FAILED (rc={r.rc}):\n{r.out}")
    contains(r.out, "CORROBORATES", "the sub-class names itself")
    contains(r.out, "1 corroborated by the release's own sealed",
             "and is COUNTED with its denominator (canon M-COVER)")
    not_contains(r.out, "F-LEGIBLE OK",
                 "corroboration is not the two-path equality check and must "
                 "not read as though it were")


# ================================================= the EXPORTER, end to end =
def detached_board(tag="expleg_"):
    """The real crow-recorder board, COPIED out of its project so that
    `find_parts_dir` finds no `02_parts/` — the authority is then the ledger
    alone and every IC on the board resolves NOTHING.

    WHY NOT JUST POINT AT THE PROJECT. Until 2026-07-27 this family's block
    fixture WAS the project board, because five of its coded rows resolved no
    MPN. Those five were then FIXED at the source (four dossiers moved a bare
    `lcsc:` into the `sourcing:` block the 02_parts contract mandates; Y1's
    NDK crystal gained a catalog-verified ledger row) and the fixture went
    green — a known-bad that evaporates the moment the defect it guards is
    repaired proves nothing afterwards, which is the exact failure c1af621
    recorded for `fleet_regrade`. Detaching the board makes the fixture
    depend on the RESOLVER's behaviour, not on any board's repair state.
    Rotations are overridden because A-ROT blocks FIRST and this fixture is
    about F-LEGIBLE."""
    d = tmpdir(tag)
    (d / "out").mkdir()
    board = d / CROW_BOARD.name
    board.write_bytes(CROW_BOARD.read_bytes())
    return board, d / "out"


CROW_TSC = RELEASES / "crow-recorder-central-v2/03_tscircuit"


@test("the exporter BLOCKS when a coded row resolves NO MPN, and leaves "
      "NOTHING uploadable", kind="known_bad")
def t_export_blocks_illegible():
    """THE ADR'S INCIDENT BOARD, with its MPN authority taken away. 23 of
    crow-recorder-central-v2's coded rows resolve no MPN from the ledger alone
    — that is the state EIGHT of nine boards shipped in for the fleet's whole
    history, because the exporter read a hand-maintained side-file only one
    project ever created. Each is a FAIL, never a blank, and the block must
    leave no plausible-looking package behind — the A-ROT lesson: a blocked
    run that leaves an uploadable file is worse than no gate, because the next
    person uploads it.

    RED-VERIFIED 2026-07-27: `git show HEAD:skills/jlcpcb-fab/scripts/
    export_jlc_package.py` restored in place, this test run — the pre-fix
    exporter has no F-LEGIBLE path at all, exits 0 and writes a COMPLETE
    BOM with a 100%-blank MPN column, so `must_fail` fails. Fix restored
    and the test re-run green.

    The stale sweep is asserted over BOTH the contract names (bom.csv /
    cpl.csv, written since 2026-07-31) AND the legacy bom_jlc.csv /
    cpl_jlc.csv: after a producer rename the LEGACY file is the likelier
    one to be uploaded by hand, so leaving it would re-open the exact
    hole this assertion closes."""
    if not CROW_BOARD.exists():
        raise AssertionError(f"missing real board fixture: {CROW_BOARD}")
    board, out = detached_board()
    stales = [out / n for n in ("bom.csv", "bom_jlc.csv",
                                "cpl.csv", "cpl_jlc.csv")]
    for stale in stales:
        stale.write_text("Comment,Designator\nSTALE,X1\n")
    r = run([KPY, EXPORT, board, out, "--layers", "4",
             "--lcsc-source", CROW_TSC, "--allow-unsourced-rotations"])
    must_fail(r, "fab export with an illegible BOM", "F-LEGIBLE BLOCKED")
    contains(r.out, "no 02_parts/<MPN>/part.yaml declares this code",
             "the block says what would fix it")
    contains(r.out, "F-MPN C6938291", "and names an unresolvable code (U1)")
    for stale in stales:
        check(not stale.exists(),
              f"a BLOCKED export left a stale {stale.name} behind — the next "
              "person uploads it")


@test("the exporter's F-LEGIBLE escape hatch is LOUD and still writes")
def t_export_escape_hatch():
    """A blocking change needs a transition, and a quiet escape hatch is just
    the old default with extra steps. Mirrors --allow-unsourced-rotations."""
    board, out = detached_board()
    r = must_pass(run([KPY, EXPORT, board, out, "--layers", "4",
                       "--lcsc-source", CROW_TSC,
                       "--allow-unsourced-rotations",
                       "--allow-illegible-bom"]), "escape-hatch export")
    contains(r.out, "F-LEGIBLE OVERRIDDEN", "the override is loud")
    contains(r.out, "MUST NOT BE ORDERED", "and says what it costs")
    check((out / "bom.csv").exists(), "the escape hatch wrote no BOM")


@test("the incident board's OWN export now PASSES F-LEGIBLE end to end")
def t_crow_export_is_legible_now():
    """The other side of the known-bad above, and the reason
    crow-recorder-central-v2 v1.6 exists. WITH its `02_parts/` in reach, all 47
    coded rows resolve and all 49 Comments read. Two of those 49 rows are the
    uncoded `dnp_by_design` pin headers JP_INJ and J_DBG, whose board Value is
    the tscircuit placeholder `simple_chip`: they are legible only because of
    the FOOTPRINT fallback, and the board cannot be regenerated to fix the
    Value without moving copper on a sealed design."""
    d = tmpdir("expleg_crow_")
    must_pass(run([KPY, EXPORT, CROW_BOARD, d, "--layers", "6"]),
              "export of the incident board")
    g = must_pass(run([KPY, CHECK, d / "bom.csv", "--parts",
                       RELEASES / "crow-recorder-central-v2/02_parts"]),
                  "independent F-LEGIBLE grading of the incident board")
    contains(g.out, "coverage F-MPN: 47/47", "every coded row resolved")
    contains(g.out, "coverage F-WORDS: 49/49", "every Comment reads")
    contains(d.joinpath("bom.csv").read_text(encoding="utf-8-sig"),
             "PinHeader_1x03_P2.54mm_Vertical,JP_INJ",
             "the uncoded strap row falls back to its footprint")


@test("the exporter's own output PASSES the independent checker, MPN and all")
def t_export_output_is_legible():
    """usb-hub-3s-v3 is the one board that ever maintained the retired
    side-file, and v1.5-v1.8 still shipped 3-4 F-MPN findings from it. Reading
    `02_parts/` instead resolves ALL 46 coded rows, and the SW1 space-vs-hyphen
    drift disappears because there is only one home for the fact now.

    The grader is `bom_legibility_check.py` run as a SUBPROCESS against the
    written bytes — it re-derives every MPN from the dossiers and compares
    against the file, so the exporter does not get to grade itself (canon M1).

    RED-VERIFIED 2026-07-27 against the restored pre-fix exporter: it writes a
    100%-blank MPN column and no UTF-8 byte-order-mark, so this test fails on
    both F-MPN and F-ENCODE. Fix restored, test re-run green."""
    d = tmpdir("expleg_")
    r = must_pass(run([KPY, EXPORT, USB_BOARD, d, "--layers", "4"]),
                  "fab export of a fully-dossiered board")
    contains(r.out, "F-LEGIBLE OK", "the exporter's own verdict")
    bom = d / "bom.csv"
    check(bom.exists(), "no BOM written")
    raw = bom.read_bytes()
    check(raw.startswith(b"\xef\xbb\xbf"),
          "the BOM ships with NO UTF-8 byte-order-mark — a cp936 reader "
          "renders the ohm sign as mojibake (23 of 26 sealed BOMs)")
    g = must_pass(run([KPY, CHECK, bom, "--parts",
                       RELEASES / "usb-hub-3s-v3/02_parts"]),
                  "independent F-LEGIBLE grading of the fresh export")
    contains(g.out, "coverage F-MPN: 46/46", "every coded row resolved")
    contains(g.out, "F-LEGIBLE OK", "the independent verdict")
    contains(bom.read_text(encoding="utf-8-sig"), "SS12D07VG6-087",
             "SW1's MPN comes from the dossier (hyphen), not the drifted "
             "side-file (space)")


@test("the retired lcsc_mpn_map.csv is IGNORED, loudly, and its DRIFT measured")
def t_sidefile_is_retired():
    """ADR-0006: `lcsc_mpn_map.csv` is RETIRED as an input; an override belongs
    in the part's own part.yaml, which is the one home. Deleting the read
    silently would leave the file lying in outdirs looking authoritative, so
    the exporter says it was not read AND names every code where the side-file
    disagrees with the dossier — the drift, made visible at the moment it stops
    mattering."""
    d = tmpdir("expleg_")
    (d / "lcsc_mpn_map.csv").write_text(
        "LCSC,MPN\nC2939728,SS12D07VG6 087\n")
    r = must_pass(run([KPY, EXPORT, USB_BOARD, d, "--layers", "4"]),
                  "export with a leftover side-file")
    contains(r.out, "RETIRED as an input", "the side-file is announced dead")
    contains(r.out, "DRIFT C2939728", "and its drift is named")
    contains(d.joinpath("bom.csv").read_text(encoding="utf-8-sig"),
             "SS12D07VG6-087", "the dossier won")


@test("the exporter writes the F-ECHO worklist beside the A-POL rotation gate")
def t_export_writes_echo_gate():
    """A fact that lives only in a script's docstring never reaches the person
    placing the order — the same reasoning that made the exporter reproduce
    A-POL's single-channel codes into rotation_human_gate.txt. F-ECHO is
    human-gated by decision (ADR-0006 rules out a JLCPCB API integration), so
    the export must hand the human the exact list to compare."""
    d = tmpdir("expleg_")
    must_pass(run([KPY, EXPORT, USB_BOARD, d, "--layers", "4"]), "export")
    gate = d / "bom_echo_gate.txt"
    check(gate.exists(), "no bom_echo_gate.txt written")
    text = gate.read_text()
    contains(text, "C82317", "the gate cites the substitution incident")
    contains(text, "--echo", "and tells the human how to run the diff")
    codes = [l.split("\t")[0] for l in text.splitlines() if l.startswith("C")
             and "\t" in l]
    eq(len(codes), 46, "one worklist line per coded BOM line")


# ================================================== the fleet, as measured ==
@test("25 of 26 sealed BOMs FAIL F-LEGIBLE — the fixtures are free",
      kind="known_bad")
def t_fleet_measurement():
    """ADR-0006 predicted "23 of 26 sealed BOMs fail at least one check today".
    MEASURED on landing: 25 of 26. The two the ADR missed are named in this
    file's module docstring. This test pins the MEASUREMENT, not the
    prediction — and it is a known_bad because what it asserts is that the
    gate BITES on real shipped bytes rather than only on scratch fixtures.

    It is written as a FLOOR (>= 20 failing, and the one clean release really
    passing) rather than an equality: a new sealed release must not silently
    weaken it, and re-grading a fixed board must not break it."""
    rels = sorted(RELEASES.glob("*/07_releases/*/fab/bom.csv"))
    check(len(rels) >= 26, f"only {len(rels)} sealed BOMs found — fixture "
                           f"corpus shrank; re-measure before editing this")
    failed = []
    for b in rels:
        p = subprocess.run([KPY, str(CHECK), str(b.parent.parent)],
                           capture_output=True, text=True)
        if p.returncode:
            failed.append(f"{b.parts[-4]}")
    check(len(failed) >= 20,
          f"only {len(failed)}/{len(rels)} sealed BOMs fail F-LEGIBLE — either "
          f"the fleet was fixed (update this number) or the gate stopped "
          f"biting")
    must_pass(run([KPY, CHECK, CLEAN_REL]),
              "crow-mic-pod v1.0 is the ONE sealed BOM that passes all three "
              "checks; if it now fails, the gate over-reached")


if __name__ == "__main__":
    sys.exit(main())
