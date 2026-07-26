#!/usr/bin/env python3
"""T1: ROTATION AUTHORITY — canon A-ROT / A-POL / M-PROV.

THE INCIDENT (2026-07-25). In one day this fleet found rotation defects on FIVE
boards — 22 wrong CPL rotations on smc0985-cooksense alone, across two SEALED
releases. Every one had the same root cause:

    ROTATION AUTHORITY WAS INHERITED BY PATTERN-MATCHING A FOOTPRINT *NAME*,
    AND A NAME IS NOT A PART.

Five distinct mechanisms grew out of that root, and each has a test below:
  (a) WRONG KEY       C79924 vs C7719, both SOT-23-5, need 180 vs 270 (8f472e1)
  (b) NEGATED OFFSET  the table was populated FROM jlc_twin.xform(), which used
                      the wrong handedness — canon M1 (e0d735c, 1b69760)
  (c) NO RULE FIRED   C98732 (XT60) / C125121 (opto) matched nothing and
                      silently defaulted to 0.0 (95a8180, 99c739c)
  (d) PARTIAL PREFIX  `^SOT-23` swallowed SOT-23-6, putting TEN safety-chain
                      gates 90 deg out on a cooking interlock (95317d5)
  (e) UNEVIDENCED     `^JST_GH_SM,180` was simply wrong — EIGHT connectors
                      180 deg out on two sealed releases (99c739c)

RED-VERIFICATION (performed 2026-07-25 by restoring the pre-fix resolver body
    for pat, off in name_db:
        if pat.search(fpname):
            return round((board_rot + off) % 360, 1), off, "name"
    return round(board_rot % 360, 1), 0.0, "none"
into jlc_rotation_resolve.resolve(), running `--only=rotation`, and restoring).
Each RED result is recorded in the individual test docstring. The pre-fix code
CANNOT satisfy any of the four `unsourced` tests: it answers with a number and
a non-blocking source in exactly the cases that shipped the defects.
"""
import csv
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (FAB_SCRIPTS, KPY, ROOT, check, contains,  # noqa: E402
                     eq, main, must_fail, must_pass, not_contains, run, test,
                     tmpdir)

sys.path.insert(0, str(FAB_SCRIPTS))
from jlc_rotation_resolve import (SRC_LCSC, SRC_UNSOURCED,  # noqa: E402
                                  cross_check, load_lcsc_rows, load_name_db,
                                  resolve, resolve_rotation)

AUDIT = FAB_SCRIPTS / "jlc_rotation_audit.py"
EXPORT = FAB_SCRIPTS / "export_jlc_package.py"
SYMPROBE = FAB_SCRIPTS / "jlc_footprint_symmetry.py"

# The REAL boards the class bit. Read-only; nothing here ever writes a project.
USB_BOARD = ROOT / "projects/usb-hub-3s-v3/04_kicad/usb_hub_3s_v2.kicad_pcb"

# the historical name-DB rules that decided each incident, verbatim
_SOT23 = [(__import__("re").compile("^SOT-23"), -90.0, "^SOT-23")]
_GH_SM = [(__import__("re").compile("^JST_GH_SM"), 180.0, "^JST_GH_SM")]
_CPELEC = [(__import__("re").compile("^CP_Elec_6.3x7.7"), 180.0,
            "^CP_Elec_6.3x7.7")]


# ======================================================== resolver: clean ===
@test("a MEASURED per-LCSC row is the authority and composes with board rot")
def t_measured_row_wins():
    """C15127 (AO3400A, SOT-23) measures 180. At board rot 90 the CPL cell is
    270, and the source is `lcsc` — the only source that decides anything."""
    r = resolve("SOT-23", 90, "C15127", _SOT23, {"C15127": 180.0})
    eq(r.cpl, 270.0, "C15127 at board-rot 90 + measured 180")
    eq(r.source, SRC_LCSC, "resolution source")
    eq(r.blocking, False, "a measured row does not block")


@test("the shipped per-LCSC table still resolves its recorded incident values")
def t_shipped_table():
    """Reverting the table (e.g. the six 90->270 corrections of e0d735c) must
    re-fail here. These are the values the post-mortems recorded."""
    tbl = {c: r["offset"] for c, r in load_lcsc_rows().items()}
    for code, want in [("C6938291", 270.0),   # XU316 CPU, crow-rv2 v1.3 P0
                       ("C7719", 270.0),      # cooksense U_WD, never was wrong
                       ("C79924", 180.0),     # the other SOT-23-5
                       ("C22046", 180.0),     # the ten safety-chain gates
                       ("C2887273", 0.0),     # cooksense CE1, polarized
                       ("C2982822", 0.0),     # usb-hub C1/C2, polarized
                       ("C98732", 270.0)]:    # the XT60
        check(code in tbl, f"{code} lost its row — the measurement is gone")
        eq(tbl[code], want, f"{code} measured offset")


# =================================================== resolver: known-bad ====
@test("(c) NO RULE FIRED: an unmatched footprint is UNSOURCED, never 0.0",
      kind="known_bad")
def t_no_rule_is_blocking():
    """C98732's XT60 sat on a VENDORED footprint name, so `^AMASS_XT60PW-M`
    (start-anchored) never fired and the offset silently defaulted to 0 —
    usb-hub-3s-v3 v1.4 shipped J1 90 deg off. C125121's opto did the same on
    cooksense, 270 deg off, on the 5kV SAFETY ISOLATION barrier.
    RED against the pre-fix resolver: it returns (0.0, 0.0, 'none') with
    blocking absent entirely, so `r.blocking` raises AttributeError and the
    `source == unsourced` assertion cannot hold."""
    r = resolve("XT60PW-M_EdgeTrim", 0, "C98732", [], {})
    eq(r.source, SRC_UNSOURCED, "an unmatched part's source")
    eq(r.blocking, True, "silence must BLOCK, not default")
    ids = [f[0] for f in r.findings]
    check("ROT-UNSOURCED" in ids, f"no ROT-UNSOURCED finding: {ids}")
    contains(r.findings[0][1], "C98732", "the finding names the code")
    contains(r.findings[0][1], "silently shipped this part at offset 0",
             "the finding says out loud that the old path defaulted quietly")


@test("(d) PARTIAL PREFIX: ^SOT-23 can no longer decide a SOT-23-6",
      kind="known_bad")
def t_partial_prefix_cannot_decide():
    """smc0985-cooksense's ENTIRE hardware safety chain — U_AND1/2/3,
    U_FAULTAND, U_CAND1/2, U_DECUEN, U_DECDEN, U_LATCHG, U_OSCLR, ten
    SN74LVC1G11 in SOT-23-6 — was heading to fab at CPL 270 because the
    broader `^SOT-23` rule (correct for 3-pin SOT-23) matched the 6-pin part.
    Measured offset is 180 on all ten refs (95317d5).
    RED against the pre-fix resolver: `resolve_rotation('SOT-23-6', 0,
    'C22046', _SOT23, {})` returns (270.0, -90.0, 'name') — a confident,
    non-blocking, 90-degrees-wrong answer."""
    cpl, off, src = resolve_rotation("SOT-23-6", 0, "C22046", _SOT23, {})
    eq(src, SRC_UNSOURCED, "a prefix hit must not become authority")
    check(cpl != 270.0,
          "the resolver still returns the name-DB's 270 for SOT-23-6 — that is "
          "the value that would have shipped ten safety-chain gates 90 out")
    # ...and with the MEASURED row present it resolves, to 180.
    cpl2, _o, src2 = resolve_rotation("SOT-23-6", 0, "C22046", _SOT23,
                                      {"C22046": 180.0})
    eq((cpl2, src2), (180.0, SRC_LCSC), "C22046 with its measured row")


@test("(e) UNEVIDENCED RULE: ^JST_GH_SM,180 cannot place a connector",
      kind="known_bad")
def t_unevidenced_rule_cannot_decide():
    """`^JST_GH_SM,180` was never measured and was wrong. It placed EIGHT
    external connectors 180 deg out on cooksense v1.0 AND v1.1 — the whole
    field harness set (99c739c). Measured offset is 0.
    RED against the pre-fix resolver: returns (180.0, 180.0, 'name')."""
    cpl, _o, src = resolve_rotation("JST_GH_SM05B-GHS-TB_1x05-1MP_P1.25mm_"
                                    "Horizontal", 90, "C189896", _GH_SM, {})
    eq(src, SRC_UNSOURCED, "an unevidenced rule must not decide")
    check(cpl != 270.0, "the refuted rule's 180 offset still reaches the CPL")


@test("(a) WRONG KEY: two parts sharing SOT-23-5 keep their own answers",
      kind="known_bad")
def t_wrong_key():
    """C79924 (TLV70018) and C7719 (supervisor) are both `SOT-23-5` and need
    180 and 270. One NAME cannot hold two answers, which is the whole reason
    the per-LCSC table exists. Dropping either row must produce UNSOURCED —
    never the other part's value and never the name DB's -90.
    RED against the pre-fix resolver: the dropped part falls through to
    (270.0, -90.0, 'name'), which is 90 deg wrong for C79924."""
    tbl = {"C79924": 180.0, "C7719": 270.0}
    eq(resolve_rotation("SOT-23-5", 0, "C79924", _SOT23, tbl)[0], 180.0,
       "C79924 CPL")
    eq(resolve_rotation("SOT-23-5", 0, "C7719", _SOT23, tbl)[0], 270.0,
       "C7719 CPL")
    dropped = {"C79924": 180.0}
    _c, _o, src = resolve_rotation("SOT-23-5", 0, "C7719", _SOT23, dropped)
    eq(src, SRC_UNSOURCED, "a part whose row is missing")


@test("(b) an EXACTLY-180 disagreement is named as a HANDEDNESS signature",
      kind="known_bad")
def t_exact_180_is_handedness():
    """THE FREE SIGNAL WE WERE DISCARDING. `formB(a) == formA(-a)` identically
    and both coincide at 0/180, so a negated rotation operator is invisible at
    0/180 and EXACTLY 180 deg wrong at 90/270. An exact-180 disagreement is
    therefore the arithmetic signature of a handedness error (or of an opposite
    pad-1 convention) — it is NEVER 'the DB is stale', which is how it was read
    for weeks (git show e0d735c^). It costs one comparison and was already
    sufficient to catch the incident.
    RED against the pre-fix resolver: cross_check() did not exist and nothing
    compared the measurement to the name DB at all — the list is empty."""
    finds = cross_check(0.0, 180.0, "^CP_Elec_6.3x7.7", "CP_Elec_6.3x7.7",
                        "C2887273")
    eq(len(finds), 1, "one cross-check finding")
    eq(finds[0][0], "ROT-XCHECK-180", "finding id")
    for word in ("NEGATED ROTATION OPERATOR", "handedness", "pcbnew",
                 "PAD-1 CONVENTION", "NEVER 'the DB is stale'"):
        contains(finds[0][1], word, "the exactly-180 finding text")
    # a NON-180 disagreement is a different, lesser finding
    other = cross_check(0.0, 90.0, "^X", "X", "C1")
    eq(other[0][0], "ROT-XCHECK", "a 90-deg disagreement is not the signature")
    # and agreement is silent, so the gate cannot cry wolf
    eq(cross_check(180.0, 180.0, "^X", "X", "C1"), [], "agreement is silent")


# ==================================================== A-POL + M-PROV table ==
def scratch_table(rows, hdr="LCSC,rotation,evidence,polarity\n"):
    d = tmpdir("rot_")
    p = d / "table.csv"
    with open(p, "w", newline="") as f:
        f.write(hdr)
        csv.writer(f, lineterminator="\n").writerows(rows)
    return p


GOOD_ROW = ["C9999999", "180",
            "Measured 2026-07-25 with the pcbnew-verified operator, pads by "
            "NUMBER: offset 180, rms 0.0300mm vs 3.7972mm next best (127x). "
            "Numbering-free channel: JLC's silk chamfer is on the pad-1 end "
            "and ours marks '+' on the pad-1 end.", "two-channel"]


@test("the SHIPPED rotation table passes A-POL + M-PROV")
def t_shipped_table_graded():
    """The live gate over the live authority. Every row must carry a DATED
    measurement with a residual, must not claim this pipeline's own output as
    its source, and must declare its polarity channel."""
    r = must_pass(run([KPY, AUDIT, "--table"]), "rotation table audit")
    contains(r.out, "ROTATION-TABLE OK", "clean verdict")


@test("M-PROV FAILS a row populated from jlc_twin's own jlc_offset",
      kind="known_bad")
def t_mprov_self_populated():
    """THE INCIDENT VERBATIM (e0d735c). Six rows of jlc_lcsc_rotations.csv had
    been populated FROM `jlc_twin.xform()` — the very function they were then
    used to check. The operator was negated, so every consumer inherited the
    same error, each wrong row OVERRODE a correct name-DB entry, and even an
    external reviewer reading the table was misled by it. Canon M1 said
    'checker and checked must not share a method' and could not be checked.
    RED-VERIFIED (new-gate variant): jlc_rotation_audit.py did not exist, so
    NOTHING graded the table's provenance — this fixture had no checker to
    fail. The fixture is the passing GOOD_ROW broken in exactly one way: its
    evidence names jlc_offset as the source."""
    bad = list(GOOD_ROW)
    bad[2] = ("offset taken from jlc_twin's reported jlc_offset on "
              "2026-07-24, rms 0.20mm")
    r = must_fail(run([KPY, AUDIT, "--table", scratch_table([bad])]),
                  "M-PROV on a self-populated row", "M-PROV")
    contains(r.out, "jlc_offset", "names the forbidden provenance")
    contains(r.out, "M1", "cites the canon it enforces")


@test("M-PROV FAILS a row whose evidence is a rationale, not a measurement",
      kind="known_bad")
def t_mprov_rationale():
    """`^JST_GH_SM,180` was an UNEVIDENCED rule and it was simply wrong —
    EIGHT connectors 180 deg out on two sealed releases (99c739c). A waiver
    needs evidence, not rationale (canon M4); so does an authority row."""
    bad = list(GOOD_ROW)
    bad[2] = ("same as C189896, standard for this connector family — should "
              "be 180 by analogy with the other JST parts")
    r = must_fail(run([KPY, AUDIT, "--table", scratch_table([bad])]),
                  "M-PROV on a reasoned row", "M-PROV")
    contains(r.out, "RATIONALE", "says why a rationale is not evidence")


@test("M-PROV FAILS an undated row and a row with no residual figure",
      kind="known_bad")
def t_mprov_undated():
    """'Measured' without a number is a claim; without a date it cannot be
    re-verified against the model it was fitted to."""
    undated = list(GOOD_ROW)
    undated[2] = ("Measured with the pcbnew-verified operator: offset 180, "
                  "rms 0.0300mm vs 3.7972mm next best. Silk chamfer agrees.")
    r = must_fail(run([KPY, AUDIT, "--table", scratch_table([undated])]),
                  "M-PROV undated", "measurement DATE")
    numberless = list(GOOD_ROW)
    numberless[2] = ("Measured 2026-07-25 with the pcbnew-verified operator "
                     "and it fits best at 180. Silk chamfer agrees with it.")
    r2 = must_fail(run([KPY, AUDIT, "--table", scratch_table([numberless])]),
                   "M-PROV numberless", "residual/separation")


@test("A-POL FAILS a POLARIZED row declared n/a — the fit margin is not "
      "confidence", kind="known_bad")
def t_apol_polarized_declared_na():
    """THE PROOF (828db4c). On usb-hub-3s-v3's indicator LEDs C2296/C2297 the
    pad-NUMBER fit returns 180 with a 17.7x margin and is WRONG: JLC numbers
    pad 1 = ANODE (silk diode-glyph apex WEST, silk body chamfered WEST) while
    KiCad's Device:LED is pin1=K and LED_0805_2012Metric chamfers F.Fab at
    pin 1 (also WEST). Both libraries draw the cathode WEST, so the true offset
    is 0 and a 180 row would ship every indicator dark — indistinguishable from
    a bad joint. A pad-number fit structurally CANNOT see a model whose own
    numbering differs from ours; only a numbering-free channel can. The same
    class destroyed parts three times: usb-hub C1/C2 (C2982822) and cooksense
    CE1 (C2887273) both shipped 180 REVERSED, polarized electrolytics across a
    LiPo pack."""
    bad = ["C2296", "180",
           "KT-0805Y amber LED. Measured 2026-07-25 by pad NUMBER: offset 180, "
           "residual 0.1125mm vs 1.9875mm next best = 17.7x margin.", "n/a"]
    r = must_fail(run([KPY, AUDIT, "--table", scratch_table([bad])]),
                  "A-POL on a polarized row declared n/a", "A-POL")
    contains(r.out, "17.7x", "names the margin that was confidently wrong")
    contains(r.out, "two-channel", "names the required declaration")


@test("A-POL FAILS a 'two-channel' row that records no numbering-free channel",
      kind="known_bad")
def t_apol_two_channel_without_channel():
    """RULE 1 of the table: a measurement that is not IN THE ROW does not
    exist. C7719's offset was measured and written only into ANOTHER row's
    evidence prose; the resolver reads rows, not prose, so it sat inert for a
    day while the name DB won (8f472e1). Declaring `two-channel` without
    naming the channel is the same defect."""
    bad = list(GOOD_ROW)
    bad[2] = ("Polarized electrolytic. Measured 2026-07-25 by pad NUMBER: "
              "offset 180, rms 0.0300mm vs 3.7972mm next best (127x).")
    r = must_fail(run([KPY, AUDIT, "--table", scratch_table([bad])]),
                  "A-POL two-channel with no channel", "A-POL")
    contains(r.out, "NUMBERING-FREE", "names what is missing")


@test("A-POL FAILS a 'single-channel' row that does not name the human gate",
      kind="known_bad")
def t_apol_single_channel_without_gate():
    """C98732's XT60 is 2-pad COLLINEAR: the fit distinguishes 90 from 270
    only through pad NUMBERING, and its part.yaml already says 'PAD 1 IS
    NEGATIVE - polarity is a PART FACT' beside a ledger incident (a reversed
    XT60 shipped once). Where no numbering-free channel exists, the row is
    SINGLE-CHANNEL and the JLC order-preview human gate carries it — a row
    that neither has a channel nor names the gate is carried by nothing."""
    bad = list(GOOD_ROW)
    bad[2] = ("2-pad collinear battery connector. Measured 2026-07-25, pads "
              "by NUMBER: rms 0.0000mm @270 vs 5.0912mm next best.")
    bad[3] = "single-channel"
    r = must_fail(run([KPY, AUDIT, "--table", scratch_table([bad])]),
                  "A-POL single-channel with no human gate", "A-POL")
    contains(r.out, "ORDER-PREVIEW", "names the gate that must carry it")


@test("A-POL FAILS a row with no polarity declaration at all", kind="known_bad")
def t_apol_silent():
    """Silence is the failure mode this whole family exists to kill. A blank
    column is not `n/a`; it is nobody having looked."""
    bad = list(GOOD_ROW)
    bad[3] = ""
    r = must_fail(run([KPY, AUDIT, "--table", scratch_table([bad])]),
                  "A-POL on a blank polarity column", "A-POL")
    contains(r.out, "Silence is not a declaration", "says so")


# ================================================== MEASURED 180-symmetry ===
SYM_PROBE = r"""
import json, sys
sys.path.insert(0, sys.argv[2])
import pcbnew
from jlc_footprint_symmetry import symmetry
b = pcbnew.LoadBoard(sys.argv[1])
out = {}
for fp in b.GetFootprints():
    n = str(fp.GetFPID().GetLibItemName())
    if n not in out:
        out[n] = symmetry(fp)
print("JSON" + json.dumps(out))
"""


def probe_symmetry(board):
    d = tmpdir("sym_")
    (d / "p.py").write_text(SYM_PROBE)
    r = must_pass(run([KPY, d / "p.py", board, FAB_SCRIPTS]),
                  "symmetry probe")
    import json
    return json.loads(r.out.split("JSON", 1)[1])


@test("the A-ROT exemption is MEASURED: a chip passive is its own 180 "
      "reflection, a polarized cap is NOT — and only the GRAPHICS separate them",
      kind="known_bad")
def t_symmetry_discriminates():
    """The one exemption A-ROT grants must not be a name rule wearing a
    disguise. It measures the board's OWN footprint: pads AND graphics must map
    onto themselves under 180 deg.

    This is the known-bad half because CP_Elec_6.3x7.7 is the footprint that
    shipped REVERSED on two boards (usb-hub-3s-v3 C1/C2 C2982822; cooksense CE1
    C2887273 — polarized electrolytics across a 9-12.6V 3S pack, which vent).
    THE DISCRIMINATING FACT, measured on the real sealed board: its PADS are
    exactly as symmetric as an R_0603's (both 0.000 mm) — which is precisely
    why a pad-number fit could not see the reversal — and only its GRAPHICS
    (1.812 mm) betray the orientation. An exemption keyed on pads alone would
    have exempted the P0."""
    if not USB_BOARD.exists():
        raise AssertionError(f"missing real board fixture: {USB_BOARD}")
    sym = probe_symmetry(USB_BOARD)
    for fpn in ("R_0603_1608Metric", "C_1210_3225Metric",
                "L_Sunlord_MWSA1206S-6R8"):
        check(sym[fpn]["exempt"],
              f"{fpn} should be exempt (its own 180 reflection): {sym[fpn]}")
    cp = sym["CP_Elec_6.3x7.7"]
    check(not cp["exempt"], f"the POLARIZED cap was exempted: {cp}")
    check(cp["pad_resid"] <= 0.02,
          f"the discriminating claim fails: CP_Elec's pads are NOT symmetric "
          f"({cp['pad_resid']}), so this fixture no longer proves that pad "
          f"symmetry alone would have exempted the P0")
    check(cp["gfx_resid"] > 0.02,
          f"CP_Elec's graphics are symmetric ({cp['gfx_resid']}) — the "
          f"numbering-free channel that catches the reversal is gone")
    for fpn in ("D_SOD-123", "D_SOD-323", "D_SMB"):
        check(not sym[fpn]["exempt"], f"a DIODE was exempted: {sym[fpn]}")
    check(not sym["SOT-23-6"]["exempt"],
          "SOT-23-6 was exempted — that is the ten-safety-gate package")


# ======================================================= the exporter gate ==
@test("A-ROT BLOCKS the fab export on a real board with unsourced rotations, "
      "and leaves NO uploadable package behind", kind="known_bad")
def t_export_blocks():
    """The default must be BLOCKING, not opt-in: 'silence becomes a FAIL
    instead of a default' is the entire point. Run against the real
    usb-hub-3s-v3 board, whose v1.4 shipped C1/C2 180 deg reversed and J1
    90 deg off.

    Two properties, both of which the pre-A-ROT exporter fails:
      1. exit != 0 and the block NAMES the codes;
      2. NO cpl_jlc.csv is left in the outdir — including a STALE one from an
         earlier run. A blocked run that leaves a plausible-looking CPL behind
         is worse than no gate, because the next person uploads it.
    RED-VERIFIED (new-gate variant): the pre-A-ROT exporter has no A-ROT path
    at all — it exits 0 and writes a complete package for this exact board,
    with the unsourced parts silently at the name-DB guess or 0.0."""
    if not USB_BOARD.exists():
        raise AssertionError(f"missing real board fixture: {USB_BOARD}")
    d = tmpdir("exp_")
    stale = d / "cpl_jlc.csv"
    stale.write_text("Designator,Val\nSTALE,1\n")     # a leftover from before
    r = run([KPY, EXPORT, USB_BOARD, d, "--layers", "4"])
    must_fail(r, "fab export with unsourced rotations", "A-ROT BLOCKED")
    contains(r.out, "C473910", "the block names an unsourced code (SOT-23-6)")
    contains(r.out, "D_SOD-123", "the block names an unsourced diode")
    check(not stale.exists(),
          "a BLOCKED export left a stale cpl_jlc.csv behind — the next person "
          "uploads it")
    check(not (d / "bom_jlc.csv").exists(), "a blocked export wrote a BOM")
    worklist = d / "rotations_unsourced.csv"
    check(worklist.exists(), "no worklist written — a block with no worklist "
                             "is a wall, not a gate")
    rows = list(csv.DictReader(open(worklist)))
    check(len(rows) >= 10, f"worklist has only {len(rows)} codes")
    check(all(r_["why_not_exempt"] for r_ in rows),
          "a worklist row does not say WHY its footprint is not exempt")


@test("the escape hatch writes the package, shouts, and still emits the "
      "worklist")
def t_export_escape_hatch():
    """An UNSOURCED-is-blocking change fails existing boards by design, so the
    transition needs a way to PRODUCE the worklist. It is loud, it names the
    count, and it says the package must not be ordered — a quiet escape hatch
    is just the old default with extra steps."""
    d = tmpdir("exp_")
    r = must_pass(run([KPY, EXPORT, USB_BOARD, d, "--layers", "4",
                       "--allow-unsourced-rotations"]),
                  "fab export with the escape hatch")
    contains(r.out, "A-ROT OVERRIDDEN", "the override is loud")
    contains(r.out, "MUST NOT BE ORDERED", "and says what it costs")
    check((d / "cpl_jlc.csv").exists(), "the escape hatch wrote no CPL")
    check((d / "rotations_unsourced.csv").exists(), "no worklist")


@test("A-POL: a SINGLE-CHANNEL part reaches the human gate by NAME")
def t_export_human_gate():
    """C98732's XT60 (usb-hub-3s-v3 J1) is the fleet's one SINGLE-CHANNEL row:
    2-pad collinear, so the fit resolves 90 vs 270 only through pad NUMBERING,
    with a ledger incident behind it. The export must NAME it for the JLC
    order-preview human gate — a fact that lives only in a CSV evidence column
    never reaches the person placing the order."""
    d = tmpdir("exp_")
    r = run([KPY, EXPORT, USB_BOARD, d, "--layers", "4",
             "--allow-unsourced-rotations"])
    contains(r.out, "A-POL SINGLE-CHANNEL", "the human-gate notice")
    contains(r.out, "C98732", "names the code")
    gate = d / "rotation_human_gate.txt"
    check(gate.exists(), "no rotation_human_gate.txt written")
    contains(gate.read_text(), "J1", "the gate file names the ref")


@test("the exporter reports an EXACTLY-180 name-DB disagreement, once")
def t_export_xcheck():
    """usb-hub's C1/C2 (C2982822, measured 0) sit against `^CP_Elec_6.3x7.7`
    = 180. That exact-180 gap is the free signal — and it must be reported
    ONCE, not once per placement, or it becomes noise nobody reads."""
    d = tmpdir("exp_")
    r = run([KPY, EXPORT, USB_BOARD, d, "--layers", "4",
             "--allow-unsourced-rotations"])
    contains(r.out, "ROT-XCHECK-180", "the exact-180 finding")
    eq(r.out.count("ROT-XCHECK-180"), 1,
       "the exact-180 finding count (deduped)")


# ===================================================== the fleet worklist ===
@test("the fleet migration report names boards, codes and refs")
def t_fleet_report():
    """An UNSOURCED-is-blocking change needs a transition, and a transition
    needs a worklist. The report must be per-board and per-code, and must say
    what the advisory name DB would have guessed so the measurement has a
    starting hypothesis (a HINT, never the answer)."""
    r = must_pass(run([KPY, AUDIT, "--fleet"]), "fleet migration report")
    contains(r.out, "FLEET TOTAL", "the total line")
    contains(r.out, "smc0985-cooksense", "the board with 22 wrong rotations")
    contains(r.out, "refs:", "per-code refdes lists")
    check("EXEMPT" not in r.out.upper() or "exempt" in r.out,
          "the report must say the symmetry exemption was applied")


if __name__ == "__main__":
    sys.exit(main())
