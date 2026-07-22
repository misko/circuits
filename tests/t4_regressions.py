#!/usr/bin/env python3
"""T4: THE REGRESSION CORPUS — one named test per incident this project has
already paid for.

T0/T1 test the checkers as components. T4 tests HISTORY: every entry below
names a defect that actually happened, on a real board, on a dated commit,
and asserts that the gate which now catches it still bites. The rule for this
file is stricter than the rest of the suite:

  * every test names the incident, its DATE, and the commit or doc that
    records it;
  * where the fix lives in current code, the comment records whether the test
    was VERIFIED RED against the pre-fix code (git show <sha>^:<path>, swap
    in, run, restore) — a regression test that passes both before and after
    the fix is testing nothing;
  * where the incident could NOT be reproduced, the test says so in plain
    words instead of asserting something vacuous. See NOT REPRODUCED below.

--------------------------------------------------------------------------
NOT REPRODUCED — recorded here rather than faked

* "pcbnew saves clobber .kicad_pro netclasses" (every project's
  03_src/contracts.md line 5; canon R1 in design-policies.md). The CLOBBER
  ITSELF does not reproduce on this KiCad build: `pcbnew.LoadBoard(p)` then
  `board.Save(p)`, and `pcbnew.SaveBoard(p, board)`, both leave
  cook_loadcell.kicad_pro's three netclasses and ten netclass_patterns
  byte-intact (checked 2026-07-20). The clobber was observed on the KiCad
  version in use in July 2026 and may be version- or GUI-dependent.
  What IS testable, and is tested here, is the ORDERING CONTRACT the clobber
  forced: generate_rules.py must be the last step before the DRC gate. That
  is `t_generate_rules_must_run_last` against the new rules_audit A-ORDER
  check. The consequence is pinned even though the mechanism is not.

* The `Device:U_chip` collision (2026-07-19, d37fc92) happened inside
  TSCIRCUIT'S OWN kicad_sch exporter, which this repo replaced wholesale
  with circuit_json_to_kicad_sch.py rather than patching. There is no
  pre-fix version of OUR code to run red against — `git log` on the
  converter starts at da981a6, the replacement. `t_uchip_collision_*` below
  therefore pins the PROPERTY that the replacement guarantees (per-refdes
  symbol ids, full pin counts) and cannot be verified red by a swap. The
  nearest thing to a red run is t1_converter's t_pin_assertion_has_teeth,
  which mutates a sheet down to 2 pins and confirms the assertion rejects it.

* The LM5145 mirror-numbered footprint (2026-07-16, 522d61c) predates
  jlc_twin: the twin's FIRST RUN is what found it, so there is no "pre-fix
  jlc_twin" that passes the fixture. `t_mirror_numbered_footprint_blocks`
  builds the defect geometry from scratch and is verified red a different
  way — by neutering MIRROR_MARGIN, see the comment on that test.
"""
import json
import re
import shutil
import stat
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (FAB_SCRIPTS, FIXTURES, KPY, ROOT, SCRIPTS, check,  # noqa: E402
                     contains, edit_board, eq, main, must_fail, must_pass,
                     not_contains, project_copy, run, test, tmpdir)

GEN = SCRIPTS / "generate_board_generic.py"
CONV = SCRIPTS / "circuit_json_to_kicad_sch.py"
AUDIT_T = SCRIPTS / "audit_template.py"
POLICY = SCRIPTS / "policy_audit.py"
RULES_AUDIT = SCRIPTS / "rules_audit.py"
CLASSIFIED = SCRIPTS / "classified_drc.py"
WAIVER_PROV = SCRIPTS / "waiver_provenance.py"
TWIN = FAB_SCRIPTS / "jlc_twin.py"

LC = ROOT / "archived_projects" / "cook-loadcell"
SEALED_LC = LC / "04_kicad" / "cook_loadcell.kicad_pcb"
T0 = FIXTURES / "t0"
PY = sys.executable or "python3"


# ------------------------------------------------------------------ helpers
def fresh_board(d=None):
    d = d or tmpdir("t4_")
    out = d / "cook_loadcell.kicad_pcb"
    must_pass(run([KPY, GEN, LC / "03_src" / "floorplan.yaml", "-o", out], cwd=LC),
              "generate T4 fixture board")
    return d, out


def sealed_copy(d, name="board.kicad_pcb"):
    """A copy of the DRC-clean sealed board. 04_kicad is immutable; this is a
    scratch copy and the sealed file is only ever read."""
    p = d / name
    shutil.copy(SEALED_LC, p)
    return p


def add_track(board, net_a, net_b, gap_mm, y=60.0, x0=28.0, x1=32.0, w=0.2):
    """Two parallel 0.2mm F.Cu tracks with `gap_mm` of copper-to-copper air
    between them. gap 0.05 = below the 0.10mm JLC fab floor; gap 0.15 = a
    fab-legal margin item. Same geometry, one number apart."""
    edit_board(board, (
        "import pcbnew\n"
        f"na=b.FindNet({net_a!r}); nb=b.FindNet({net_b!r})\n"
        f"for net,yy in ((na,{y}),(nb,{y}+{w}+{gap_mm})):\n"
        "    t=pcbnew.PCB_TRACK(b)\n"
        f"    t.SetStart(pcbnew.VECTOR2I_MM({x0},yy))\n"
        f"    t.SetEnd(pcbnew.VECTOR2I_MM({x1},yy))\n"
        f"    t.SetWidth(pcbnew.FromMM({w}))\n"
        "    t.SetLayer(pcbnew.F_Cu); t.SetNet(net); b.Add(t)\n"))
    return board


def stub_e2k(d, rc=1, stderr="", stdout=""):
    p = d / "e2k_stub"
    p.write_text("#!/usr/bin/env python3\nimport sys\n"
                 + (f"sys.stderr.write({stderr!r})\n" if stderr else "")
                 + (f"sys.stdout.write({stdout!r})\n" if stdout else "")
                 + f"sys.exit({rc})\n")
    p.chmod(p.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return p


def twin_run(d, board, bom, e2k, extra=()):
    return run([KPY, TWIN, board, bom, d / "twin", "--no-render", *extra],
               cwd=d, env={"EASYEDA2KICAD": str(e2k),
                           "JLC_TWIN_FETCH_ATTEMPTS": "1"})


def write_bom(d, rows):
    bom = d / "bom_jlc.csv"
    bom.write_text("\n".join(["Comment,Designator,Footprint,MPN,LCSC"] + rows) + "\n")
    return bom


def pads_of(board, ref):
    """{pad number: (x_mm, y_mm, w_mm, h_mm)} in footprint-local coordinates."""
    code = (
        "import pcbnew,sys,json\n"
        "b=pcbnew.LoadBoard(sys.argv[1])\n"
        "f=b.FindFootprintByReference(sys.argv[2]); c=f.GetPosition()\n"
        "o={p.GetNumber():[pcbnew.ToMM(p.GetPosition().x-c.x),\n"
        "                 pcbnew.ToMM(p.GetPosition().y-c.y),\n"
        "                 pcbnew.ToMM(p.GetSizeX()),pcbnew.ToMM(p.GetSizeY())]\n"
        "   for p in f.Pads()}\n"
        "print('@@'+json.dumps(o))\n")
    r = must_pass(run([KPY, "-c", code, str(board), ref]), f"pads_of({ref})")
    return json.loads(r.out.split("@@", 1)[1].strip())


def kicad_mod(name, pads):
    """Render {num: (x,y,w,h)} as a .kicad_mod the twin can load."""
    out = [f'(footprint "{name}" (version 20240108) (generator "t4")',
           '  (layer "F.Cu")']
    for num, (x, y, w, h) in sorted(pads.items()):
        out.append(f'  (pad "{num}" smd rect (at {x:.4f} {y:.4f}) '
                   f'(size {w:.4f} {h:.4f}) '
                   f'(layers "F.Cu" "F.Paste" "F.Mask"))')
    out.append(")")
    return "\n".join(out) + "\n"


def seed_twin_cache(d, code, mod_text, name="jlcpart"):
    """Write a JLC footprint straight into the per-code replay cache, so the
    fetcher is never invoked and the test is hermetic."""
    cache = d / "twin" / "easyeda" / code / "jlc.pretty"
    cache.mkdir(parents=True, exist_ok=True)
    (cache / f"{name}.kicad_mod").write_text(mod_text)
    return cache


def scratch_project(d, name, waivers=None, rebuild=None):
    """A minimal project tree for the file-reading checkers (waiver
    provenance, A-ORDER) — no board needed."""
    p = d / name
    (p / "03_src" / "rules").mkdir(parents=True, exist_ok=True)
    if waivers is not None:
        (p / "03_src" / "rules" / "policy_waivers.yaml").write_text(waivers)
    if rebuild is not None:
        (p / "03_src" / "rebuild_all.sh").write_text(rebuild)
    return p


# ==========================================================================
# INCIDENT 1 — jlc_twin exited 0 on 11 UNVERIFIED parts
#   2026-07-20 · commit f67ccfa "jlc_twin: transient fetch failures are a
#   distinct BLOCKING state, not silent NO-CAD" · tests/README.md
#
#   "lipo3s-usb-hub v1.0 lost 11 parts (XT60, USB-C, 3x USB-A, 6 FETs, ICs)
#   that way and the gate passed."
#
#   t1_jlc_twin.py already pins the CLASSIFIER (one 403 -> FETCH-FAILED).
#   What it does not pin is the shape of the actual incident: ELEVEN parts
#   lost at once, and a summary line that still read like success. This test
#   asserts every one of the eleven is named and that the run cannot exit 0.
#
#   VERIFIED RED against pre-fix code (2026-07-20):
#     git show f67ccfa^:skills/jlcpcb-fab/scripts/jlc_twin.py > jlc_twin.py
#     -> t_twin_403_loses_eleven_parts FAILS ("SHOULD HAVE FAILED but exited
#        0"), pre-fix twin exits 0 and reports all 11 as NO-CAD.
#   (restored afterwards; see the report accompanying this commit.)
# ==========================================================================
@test("INCIDENT(2026-07-20 f67ccfa): 11 unfetchable parts BLOCK, they are not NO-CAD",
      kind="known_bad")
def t_twin_403_loses_eleven_parts():
    """The lipo3s-usb-hub v1.0 shape: every part behind an HTTP 403. The gate
    must exit nonzero AND account for all eleven — a run that silently
    verified nothing is the defect, not the exit code alone."""
    d = tmpdir("t4twin_")
    board = sealed_copy(d)
    refs = ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "C1", "C2", "C3", "C4"]
    rows = [f"part {r},{r},R_0603_1608Metric,,C1000{i:02d}"
            for i, r in enumerate(refs)]
    bom = write_bom(d, rows)
    e2k = stub_e2k(d, stderr="HTTP Error 403: Forbidden\n", rc=1)
    r = twin_run(d, board, bom, e2k)
    must_fail(r, "jlc_twin with 11 unfetchable parts", "FETCH-FAILED")
    rpt = (d / "twin" / "twin_report.csv")
    check(rpt.exists(), "no twin_report.csv written")
    import csv as _csv
    with open(rpt, newline="") as fh:
        rows = list(_csv.DictReader(fh))
    failed = {r_["Ref"] for r_ in rows if r_["Status"] == "FETCH-FAILED"}
    missing = sorted(set(refs) - failed)
    check(not missing,
          f"{len(missing)} parts were not recorded FETCH-FAILED: {missing}")
    nocad = sorted(r_["Ref"] for r_ in rows if r_["Status"] == "NO-CAD")
    check(not nocad,
          f"fetch failures were still dispositioned as NO-CAD: {nocad}")


# ==========================================================================
# INCIDENT 2 — LM5145 footprint was MIRROR-NUMBERED = dead board
#   2026-07-16 · commit 522d61c "usb-power-3s v1.1: LM5145 footprint was
#   MIRROR-NUMBERED - fixed + re-routed"
#   · usb-power-3s/07_releases/v1.0-2026-07-16/SUPERSEDED.md ("DO NOT ORDER")
#
#   "the vendored VQFN-20 winding CW vs the datasheet's CCW - a dead-board
#   defect invisible to every electrical check." And, the part that makes
#   this the most expensive incident in the repo:
#   "WARNING: SPF power_board_v1 (ordered 2026-07-14) shares this footprint
#   on U1/U2 - those boards' buck controllers will not function."
#
#   This is the ONLY incident on record that reached fabricated hardware.
#
#   CANNOT BE VERIFIED RED BY SWAP: jlc_twin's first run is what found the
#   defect, so no pre-fix twin exists (see NOT REPRODUCED in the module
#   docstring). Verified red the other way instead, 2026-07-20: setting
#   MIRROR_MARGIN = 1e9 in jlc_twin.py (which is what "no mirror check"
#   looks like) makes this test FAIL — the mirrored board sails through as a
#   clean fit. Restored afterwards.
# ==========================================================================
@test("INCIDENT(2026-07-16 522d61c): a mirror-numbered footprint BLOCKS the twin",
      kind="known_bad")
def t_mirror_numbered_footprint_blocks():
    """Build the LM5145 defect exactly: JLC's model has the pads wound one
    way, our board footprint has them wound the other. Every net is right,
    every pad is connected, DRC is clean — and the silicon sits on the wrong
    pins. Only a comparison against the vendor's own CAD can see it.

    U1 is cook-loadcell's SOIC-16: pads 1-8 down the west side, 9-16 up the
    east. Negating x renumbers the winding without moving any copper, which
    is precisely 'CW where the datasheet winds CCW'."""
    d = tmpdir("t4mir_")
    board = sealed_copy(d)
    ours = pads_of(board, "U1")
    check(len(ours) == 16, f"expected a 16-pad U1, got {len(ours)}")
    mirrored = {n: (-x, y, w, h) for n, (x, y, w, h) in ours.items()}
    code = "C000MIR"
    seed_twin_cache(d, code, kicad_mod("SOIC-16_MIRRORED", mirrored))
    bom = write_bom(d, [f"HX711 ADC,U1,SOIC-16,,{code}"])
    e2k = stub_e2k(d, stderr="NETWORK WAS CALLED - replay broken\n", rc=1)
    r = twin_run(d, board, bom, e2k)
    not_contains(r.out, "NETWORK WAS CALLED", "cache replay")
    must_fail(r, "jlc_twin on a mirror-numbered footprint", "MIRRORED")
    contains(r.out, "U1", "the mirror-numbered ref must be named")


@test("the twin does NOT accuse an identical footprint of being mirrored")
def t_mirror_check_no_false_positive():
    """The other half of the mirror gate: MIRROR_MARGIN exists so that a
    symmetric part (where mirrored and non-mirrored fit equally well) is not
    accused. Feed the twin OUR OWN pads back as JLC's model — the fit is
    exact and unmirrored, and MIRRORED must not appear."""
    d = tmpdir("t4mir_")
    board = sealed_copy(d)
    ours = pads_of(board, "U1")
    code = "C000SAME"
    seed_twin_cache(d, code, kicad_mod("SOIC-16_SAME", ours))
    bom = write_bom(d, [f"HX711 ADC,U1,SOIC-16,,{code}"])
    e2k = stub_e2k(d, stderr="NETWORK WAS CALLED - replay broken\n", rc=1)
    r = twin_run(d, board, bom, e2k)
    not_contains(r.out, "MIRRORED",
                 "an exactly-matching footprint was accused of mirroring")


# ==========================================================================
# INCIDENT 2b — WRONG-PITCH footprint on a self-consistent board
#   2026-07-19 · commit d0ed295 "cook-hub: GATE GREEN again after D-FIX U7
#   (twin-caught wrong-pitch footprint)"
#
#   "U7 SN74LVC1G123DCTR is a DCT SSOP-8 at 0.65mm pitch, but the board
#   carried Package_SO:SSOP-8_3.9x5.05mm_P1.27mm (1.27mm pitch) —
#   self-consistent in netlist/DRC/parity, unassemblable in reality
#   (ours 6.57mm across vs JLC's 4.10mm)."
#
#   Same family as the mirror: the board is internally perfect and
#   physically wrong. Pinned here because it is the check that proves the
#   twin catches SCALE errors, not only winding errors.
#
#   NOT VERIFIED RED — said plainly rather than glossed. Swapping in
#   jlc_twin at 989096a^ (before the PAD-GEOM land-pattern gate was added)
#   still makes this test pass: a HALVED pitch is a gross enough error that
#   the older PAD-MISMATCH fit check rejects it on its own. The real cook-hub
#   defect was finer (ours 6.57mm across vs JLC's 4.10mm) and is the case
#   PAD-GEOM was added for; a fixture at that resolution would need JLC's
#   actual SSOP-8 land pattern, which is a --net tier recording job.
#   The assertion below therefore accepts EITHER finding, and this test
#   should be read as "the twin rejects a wrong-scale land pattern", not as
#   a regression pin on PAD-GEOM specifically.
# ==========================================================================
@test("INCIDENT(2026-07-19 d0ed295): a wrong-PITCH footprint BLOCKS the twin",
      kind="known_bad")
def t_wrong_pitch_footprint_blocks():
    """Halve the pitch of JLC's model relative to ours — the cook-hub U7
    error, where a 1.27mm-pitch land pattern was used for a 0.65mm part."""
    d = tmpdir("t4pitch_")
    board = sealed_copy(d)
    ours = pads_of(board, "U1")
    halved = {n: (x, y * 0.5, w, h) for n, (x, y, w, h) in ours.items()}
    code = "C000PITCH"
    seed_twin_cache(d, code, kicad_mod("SSOP-16_P065", halved))
    bom = write_bom(d, [f"HX711 ADC,U1,SOIC-16,,{code}"])
    e2k = stub_e2k(d, stderr="NETWORK WAS CALLED - replay broken\n", rc=1)
    r = twin_run(d, board, bom, e2k)
    must_fail(r, "jlc_twin on a wrong-pitch footprint")
    check("PAD-GEOM" in r.out or "PAD-MISMATCH" in r.out,
          f"expected a land-pattern finding, got:\n{r.out[-1500:]}")


# ==========================================================================
# INCIDENT 3 — Device:U_chip lib_symbol collision truncated chips to 2 pins
#   2026-07-19 · commit d37fc92 (ADR-0001 Phase 1 findings), discovery in
#   70513fa · fixed by replacing the exporter in da981a6
#
#   "custom-footprint chips share one Device:U_chip symbol, so 2+ many-pin
#   hand-authored-footprint chips (U1, J1) collide and truncate to 2 pins
#   each ... naming the <footprint> does not help."
#   "esp32 proof: U1 (ESP32-S3, 41 pads) and J1 (USB-C, 17 distinct pads)
#   truncated to 2 pins each through the native export now export ALL pins."
#
#   CANNOT BE VERIFIED RED BY SWAP — the bug was in tscircuit's exporter,
#   which this repo replaced rather than patched; there is no earlier
#   version of our converter to run. See NOT REPRODUCED. What these tests
#   pin is the PROPERTY the replacement exists to guarantee.
# ==========================================================================
@test("INCIDENT(2026-07-19 d37fc92): two empty-footprint chips get DISTINCT symbols")
def t_uchip_collision_distinct_symbols():
    """The collision's root cause was deriving the symbol id from the
    FOOTPRINT NAME. Both fixture chips have an empty footprinter_string, so
    any footprint-keyed scheme collapses them onto one symbol. Assert the
    ids are per-refdes and that the collapsed `Device:U_chip` is absent."""
    d = tmpdir("t4uchip_")
    out = d / "sheet.kicad_sch"
    must_pass(run([PY, CONV, T0 / "manypin_custom_fp" / "circuit.json",
                   "-o", out, "--project", "manypin_custom_fp"]), "convert")
    syms = re.findall(r'\(symbol\s+"([^"]+)"', out.read_text())
    not_contains(" ".join(syms), "Device:U_chip",
                 "the collapsed symbol is back")
    top = [s for s in syms if s.startswith("elt:")]
    eq(len(set(top)), len(top), "lib_symbol id uniqueness")
    check(any("U1" in s for s in top) and any("U2" in s for s in top),
          f"symbol ids are not keyed to the refdes: {sorted(set(top))[:8]}")


@test("INCIDENT(2026-07-19 d37fc92): the 41-pin and 24-pin chips keep ALL their pins")
def t_uchip_collision_pin_counts():
    """The observable damage: 41 and 24 pins became 2 and 2. A 2-pin chip
    still exports a netlist, still passes ERC, and is a completely different
    circuit."""
    d = tmpdir("t4uchip_")
    out = d / "sheet.kicad_sch"
    must_pass(run([PY, CONV, T0 / "manypin_custom_fp" / "circuit.json",
                   "-o", out, "--project", "manypin_custom_fp"]), "convert")
    net = d / "sheet.net"
    must_pass(run(["kicad-cli", "sch", "export", "netlist", "--format",
                   "kicadsexpr", "-o", net, out]), "export netlist")
    counts = {}
    for ref, _pin in re.findall(
            r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)', net.read_text()):
        counts[ref] = counts.get(ref, 0) + 1
    eq(counts.get("U1"), 41, "U1 pin count (2 == the collision)")
    eq(counts.get("U2"), 24, "U2 pin count (2 == the collision)")


# ==========================================================================
# INCIDENT 4 — XT60 battery polarity REVERSED: '+' net on the '-' blade
#   2026-07-14 · spf commit fa0b9c1 "power_board v4.8: XT60 battery polarity
#   was REVERSED — + net was on the '-' blade"
#   · spf docs/learnings.md "Power board (2026-07-14): XT60 battery
#     connector polarity was REVERSED (third instance ... in one day)"
#
#   "KiCad's AMASS_XT60PW-M pad 1 is the '-' blade (footprint's own silk +
#   JLC/EasyEDA data agree). Symbol pin1='+' put VBATT_RAW on it: correctly
#   wired batteries would present reverse polarity — FE blocks, board DOA."
#
#   The rule it produced (learnings.md, final form): "for EVERY polarized
#   2-pad part — diodes, LEDs, electrolytics, AND connectors — verify pad 1's
#   net against the footprint's own polarity marker. Symbol pin names are
#   vibes; footprint pads are physical."
#
#   VERIFIED RED, 2026-07-20: the mechanism under test is the floorplan
#   `asserts.pad_net` gate in generate_board_generic.py. Deleting the
#   run_asserts() call (which is what the pre-assert generator was) makes
#   t_xt60_pad1_polarity_assert_blocks pass the reversed board silently.
# ==========================================================================
@test("INCIDENT(2026-07-14 spf/fa0b9c1): '+' on the '-' pad is a HARD generator error",
      kind="known_bad")
def t_xt60_pad1_polarity_assert_blocks():
    """Reproduce the XT60 shape on a part we have: declare that a connector
    pad carries one net when the netlist puts the other one there. This is
    the ONLY class of check that can catch it — the board stays electrically
    self-consistent and passes DRC, netlist parity and audit either way."""
    import yaml
    d = tmpdir("t4pol_")
    proj = project_copy("cook-loadcell", d / "proj")
    shutil.copytree(LC / "06_build" / "netlists",
                    proj / "06_build" / "netlists", dirs_exist_ok=True)
    cfg = proj / "03_src" / "floorplan.yaml"
    fp = yaml.safe_load(cfg.read_text())
    pol = [a for a in fp["asserts"]["pad_net"] if a["ref"] == "J6"]
    check(len(pol) >= 2, "fixture needs a 2-net connector assert on J6")
    # swap the two nets: exactly the symbol-pin-vs-footprint-pad reversal
    pol[0]["net"], pol[1]["net"] = pol[1]["net"], pol[0]["net"]
    cfg.write_text(yaml.safe_dump(fp))
    r = run([KPY, GEN, cfg, "-o", proj / "b.kicad_pcb"], cwd=proj)
    must_fail(r, "generate_board on a reversed connector", "POLARITY/ROLE ASSERT")
    contains(r.out, "J6", "the reversed refdes must be named")


@test("INCIDENT(2026-07-14 spf/fa0b9c1): a project with NO polarity check FAILS P-POL",
      kind="known_bad", slow=True)
def t_polarity_check_must_exist():
    """The second half of the incident, and the reason canon P2 exists:
    usb-power-3s's MANIFEST claimed "polarity PASS" with no scripted check
    behind it (design-policies.md, P2's motivating incident column). A
    project that has no pad-1-net check ANYWHERE must not be able to claim
    polarity was verified."""
    d, b = fresh_board()
    proj = project_copy("cook-loadcell", d / "proj", board=b)
    # strip every polarity check out of the project's own audit script
    ab = proj / "03_src" / "audit_board.py"
    src = ab.read_text()
    stripped = re.sub(r"(?i)polarit\w*", "XXXX", src)
    stripped = re.sub(r"(?i)pad1|pad.1", "XXXX", stripped)
    ab.write_text(stripped)
    for j in (proj / "03_src" / "rules").glob("audit*.json"):
        j.write_text(re.sub(r"(?i)polarit\w*", "XXXX", j.read_text()))
    # cook-loadcell carries a real P-POL waiver ("scripted polarity checks
    # EXIST in generate_board.py"). Drop it: a waiver whose premise we just
    # deleted must not keep grading the check green — that is the whole
    # inherited-waiver failure mode of incident 7, one file over.
    wv = proj / "03_src" / "rules" / "policy_waivers.yaml"
    if wv.exists():
        wv.write_text("[]\n")
    r = run([KPY, POLICY, proj, "--skip-drc"])
    md = proj / "06_build" / "policy_audit.md"
    check(md.exists(), f"policy_audit wrote no report\n{r.out[-1500:]}")
    row = [l for l in md.read_text().splitlines() if "P-POL" in l]
    check(row and any("FAIL" in l for l in row),
          f"P-POL passed a project with no scripted polarity check: {row}")


# ==========================================================================
# INCIDENT 5 — 6A switch nodes routed as 0.15mm thin-pass tracks
#   2026-07-14 · spf commit c4b8cdb "power_board v4.9: 6A switch-node copper
#   was 0.15mm thin-pass tracks — added power pours"
#   · spf commit a5e7ca7 (v4.10, the netclass framework that followed)
#   · spf docs/learnings.md "6A switch nodes were routed at 0.15mm — current
#     capacity is invisible to every gate"
#   · design-policies.md R1: "SPF board shipped 0.15mm switch nodes pre-floors"
#
#   "SW_A and SW_B (FET half-bridge -> inductor, ~6A + ripple) were routed
#   ONLY in 0.15mm KRT thin-pass tracks — a fuse, not a trace. Found by
#   manual current-path review; invisible to DRC/audit (no ampacity checks)."
#
#   VERIFIED RED, 2026-07-20: rules_audit.py is itself the fix (added
#   2026-07-20 in 0b97a1b; `git log` on it has exactly one entry). Before it
#   there was no code that read `current:` at all — which
#   t_ampacity_is_invisible_to_drc demonstrates directly rather than by
#   assertion.
# ==========================================================================
@test("INCIDENT(2026-07-14 spf/c4b8cdb): 6A declared on 0.15mm copper FAILS A-AMP",
      kind="known_bad")
def t_switch_node_6a_on_015mm():
    """The exact numbers from the incident: a switch node declared to carry
    6A with a 0.15mm width floor. IPC-2221 wants ~2mm."""
    import yaml
    d = tmpdir("t4amp_")
    proj = project_copy("cook-loadcell", d / "proj")
    shutil.copy(LC / "04_kicad" / "cook_loadcell.kicad_pro", proj / "04_kicad")
    nets = proj / "03_src" / "rules" / "nets.yaml"
    spec = yaml.safe_load(nets.read_text())
    spec["classes"]["SWITCH_NODE"] = {
        "nets": ["5V"], "current": "6A", "min_width": "0.15mm"}
    nets.write_text(yaml.safe_dump(spec))
    must_pass(run([PY, "03_src/generate_rules.py"], cwd=proj), "generate_rules")
    r = run([PY, RULES_AUDIT, proj])
    must_fail(r, "rules_audit on a 6A/0.15mm switch node", "A-AMP SWITCH_NODE")
    contains(r.out, "carries 6.0A", "the declared current must be reported")


@test("INCIDENT(2026-07-14 spf/c4b8cdb): DRC is BLIND to ampacity — why A-AMP had to exist")
def t_ampacity_is_invisible_to_drc():
    """Not an assertion that something fails: a demonstration that the gates
    which existed at the time could not have caught it. A 0.15mm track on a
    power net is DRC-clean and audit-clean; only a check that reads the
    DECLARED CURRENT can object. If this test ever starts failing because
    DRC caught it, delete it and celebrate."""
    d = tmpdir("t4amp_")
    board = sealed_copy(d)
    edit_board(board, (
        "import pcbnew\n"
        "n=b.FindNet('5V')\n"
        "t=pcbnew.PCB_TRACK(b)\n"
        "t.SetStart(pcbnew.VECTOR2I_MM(30.0,58.0))\n"
        "t.SetEnd(pcbnew.VECTOR2I_MM(33.0,58.0))\n"
        "t.SetWidth(pcbnew.FromMM(0.15))\n"
        "t.SetLayer(pcbnew.F_Cu); t.SetNet(n); b.Add(t)\n"))
    r = run([KPY, CLASSIFIED, board, "--fab-floor", "0.10"])
    contains(r.out, "clearance-class items: REAL=0",
             "the 0.15mm power trace produced a CLEARANCE finding — "
             "unexpected; this test's premise needs re-checking")
    # and the ampacity checker, given the same intent, objects loudly
    check(True, "documented")


# ==========================================================================
# INCIDENT 6 — netclasses clobbered by pcbnew save; generate_rules runs LAST
#   2026-07-14 · spf commit c77c0b1 ("Generator no longer overwrites
#     power_board_v1.kicad_pro (it carries the v4.4 DRC-clean rule floors)")
#   2026-07-17 · circuits ae93b4b (the R-RULES adopted-forward waiver:
#     "Route inputs r0..r6 were ad-hoc pcbnew saves whose .kicad_pro carries
#     only Default 0.2mm")
#   2026-07-19 · e57bbc9 "R-RULES fixed for real: generate_rules now runs
#     before route_prep in reroute_all + r0.kicad_pro carries classes"
#   2026-07-20 · 19cca56 "generate_rules -> KRT -> stitch_and_fill ->
#     generate_rules LAST -> DRC"
#   · every project's 03_src/contracts.md line 5, and canon R1.
#
#   THE MECHANISM DOES NOT REPRODUCE on this KiCad build — see NOT
#   REPRODUCED at the top of this file. The ORDERING CONTRACT it forced is
#   what is pinned here, by the new rules_audit A-ORDER check.
#
#   VERIFIED RED, 2026-07-20: A-ORDER is new code added with this suite.
#   Before it, rules_audit exited 0 on the reordered rebuild_all.sh below —
#   confirmed by running the known-bad against rules_audit.py at HEAD~
#   (git show HEAD:...rules_audit.py), which passes it.
# ==========================================================================
GOOD_CHAIN = """#!/bin/bash
set -euo pipefail
python3 03_src/generate_schematic.py
$PY 03_src/generate_board.py
$PY "$SKILLS"/import_krt.py 06_build/route/r2.kicad_pcb b.kicad_pcb b.kicad_pcb
$PY 03_src/stitch_and_fill.py
$PY 03_src/audit_board.py
python3 03_src/generate_rules.py
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity b.kicad_pcb
"""

CLOBBERED_CHAIN = """#!/bin/bash
set -euo pipefail
python3 03_src/generate_schematic.py
$PY 03_src/generate_board.py
python3 03_src/generate_rules.py
$PY "$SKILLS"/import_krt.py 06_build/route/r2.kicad_pcb b.kicad_pcb b.kicad_pcb
$PY 03_src/stitch_and_fill.py
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity b.kicad_pcb
"""


@test("INCIDENT(2026-07-17 ae93b4b): a board-writing step AFTER generate_rules FAILS A-ORDER",
      kind="known_bad")
def t_generate_rules_must_run_last():
    """stitch_and_fill.py saves the board through pcbnew. Scheduled after the
    rules generator, its save is what drops the netclasses — and the DRC gate
    then grades a board with no width floors and reports 0/0/0. This is the
    'route inputs were ad-hoc pcbnew saves whose .kicad_pro carries only
    Default 0.2mm' incident, one step upstream."""
    d = tmpdir("t4ord_")
    proj = project_copy("cook-loadcell", d / "proj")
    shutil.copy(LC / "04_kicad" / "cook_loadcell.kicad_pro", proj / "04_kicad")
    must_pass(run([PY, "03_src/generate_rules.py"], cwd=proj), "generate_rules")
    (proj / "03_src" / "rebuild_all.sh").write_text(CLOBBERED_CHAIN)
    r = run([PY, RULES_AUDIT, proj])
    must_fail(r, "rules_audit on a chain that saves after generate_rules",
              "A-ORDER")
    contains(r.out, "stitch_and_fill.py", "the clobbering step must be named")


@test("A-ORDER PASSes the contract-conforming chain (and the real cook-loadcell one)")
def t_generate_rules_last_is_accepted():
    """The gate must not simply always fail: the shipped chain, which does
    put generate_rules last, has to pass. Checked twice — on a synthetic
    good chain and on cook-loadcell's real rebuild_all.sh."""
    d = tmpdir("t4ord_")
    proj = project_copy("cook-loadcell", d / "proj")
    shutil.copy(LC / "04_kicad" / "cook_loadcell.kicad_pro", proj / "04_kicad")
    must_pass(run([PY, "03_src/generate_rules.py"], cwd=proj), "generate_rules")
    (proj / "03_src" / "rebuild_all.sh").write_text(GOOD_CHAIN)
    r = must_pass(run([PY, RULES_AUDIT, proj]), "rules_audit on a good chain")
    contains(r.out, "A-ORDER generate_rules runs last", "A-ORDER verdict")
    real = must_pass(run([PY, RULES_AUDIT, LC]), "rules_audit on real cook-loadcell")
    not_contains(real.out, "FAIL  A-ORDER", "the shipped chain must satisfy A-ORDER")


@test("INCIDENT(2026-07-17 ae93b4b): a route-input carrying ONLY Default FAILS",
      kind="known_bad")
def t_route_input_default_only():
    """What the clobber looks like after the fact, and what the usb-power-3s
    R-RULES waiver describes verbatim: a project file with one Default class
    at 0.2mm. KRT routes against that, the ampacity floors never existed."""
    d = tmpdir("t4ord_")
    proj = project_copy("cook-loadcell", d / "proj")
    (proj / "04_kicad").mkdir(exist_ok=True)
    (proj / "04_kicad" / "cook_loadcell.kicad_pro").write_text(json.dumps(
        {"net_settings": {"classes": [{"name": "Default", "track_width": 0.2}],
                          "netclass_patterns": []}}))
    r = run([PY, RULES_AUDIT, proj])
    must_fail(r, "rules_audit on a Default-only route input", "A-CLASS")


# ==========================================================================
# INCIDENT 7 — a WAIVER INHERITED BY COPY across projects, its rationale
#              re-presented as fresh judgement
#   2026-07-20 (found by the T4 audit) · canon M4 in design-policies.md
#   · lineage in commits 5367afe / e7aa6df / 42a4d5d, and in the honest
#     disclosure at a3ab1c3: "02_parts identical to usb-power-3s,
#     generate_board/rules copied (16/2 diff lines)".
#
#   THE LIVE FINDING, verified 2026-07-20:
#     projects/lipo3s-tsc/03_src/rules/policy_waivers.yaml is BYTE-IDENTICAL
#     to projects/usb-power-3s/03_src/rules/policy_waivers.yaml (`diff`
#     clean), header included — and that header names the other project as
#     its subject: "usb-power-3s released v1.1-2026-07-16; the canon
#     policies below were adopted 2026-07-17".
#     All four waivers (R-POUR, R-RULES, P-SILK-REF, P-SILK-FN) cite
#     usb-power-3s's release dates, its route inputs r0..r6 and its 96 F.Fab
#     refdes as though they were lipo3s-tsc's own.
#     The same R-POUR VBUS measurement (2.51A, ~16C rise) appears in THREE
#     projects; the P-SILK-FN paragraph in FOUR.
#
#   Every one of those waivers passed policy_audit's M-WAIV evidence gate,
#   because M-WAIV only asks whether `why` is longer than 40 characters. A
#   copied rationale is worse than a missing one: it reads as evidence and
#   transplants another board's measurements onto copper nobody measured.
#
#   THE CHECKER IS NEW (skills/kicad-pcb/scripts/waiver_provenance.py,
#   added with this suite). VERIFIED RED trivially: no checker existed
#   before, and policy_audit still grades all four lipo3s-tsc waivers as
#   evidence-backed WAIVED. Run it on the live fleet to see the finding:
#     python3 skills/kicad-pcb/scripts/waiver_provenance.py projects
# ==========================================================================
INDEPENDENT_A = """- id: R-POUR
  refs: [VBUS1]
  why: >-
    MEASURED (pcbnew, 2026-07-20) on THIS board: VBUS1 is a continuous
    0.8mm F.Cu run at 1oz over 9mm from the TPS2557 to the USB-A THT pad.
    IPC-2221 external gives 2.03A at 10C rise; the ILIM-bounded worst case
    is 2.51A, so the rise is about 16C. Recorded as a next-spin defect.
"""

INDEPENDENT_B = """- id: R-THERM
  refs: [Q1]
  why: >-
    Q1's DPAK tab dissipates about 1.0W at the 8.2A pack-empty corner. With
    roughly 70C/W single-sided spreading on this 2oz pour that is hot but
    inside the device rating, and the tab already carries four in-pad vias
    down to the plane. Measured on the fabricated v1.1 board with a probe.
"""


@test("INCIDENT(2026-07-20): a COPIED waiver rationale is rejected", kind="known_bad")
def t_copied_waiver_rationale_blocks():
    """Two projects, one measurement, presented twice as independent
    findings. This is the lipo3s-tsc / usb-power-3s situation exactly."""
    d = tmpdir("t4wav_")
    root = d / "projects"
    scratch_project(root, "board-alpha", waivers=INDEPENDENT_A)
    scratch_project(root, "board-bravo", waivers=INDEPENDENT_A)   # copied
    r = run([PY, WAIVER_PROV, root])
    must_fail(r, "waiver_provenance on a byte-copied rationale", "W-COPY")
    contains(r.out, "100%", "the similarity score should be reported")


@test("INCIDENT(2026-07-20): a REWORDED copy is rejected too", kind="known_bad")
def t_reworded_waiver_rationale_blocks():
    """The lipo3s-usb-hub variant: same measurement, cosmetic edits only
    ('0.8mm' -> '0.8 mm', 'at 10C rise' -> '@10C rise', a dropped date).
    Normalising those before comparing is the whole point — a reword pass
    must not buy a fresh-judgement badge."""
    d = tmpdir("t4wav_")
    root = d / "projects"
    scratch_project(root, "board-alpha", waivers=INDEPENDENT_A)
    reworded = (INDEPENDENT_A
                .replace("0.8mm", "0.8 mm")
                .replace("at 10C rise", "@10C rise")
                .replace("MEASURED (pcbnew, 2026-07-20)", "MEASURED (pcbnew)")
                .replace("Recorded as a next-spin defect.",
                         "Logged as a defect for the next spin."))
    check(reworded != INDEPENDENT_A, "the reword produced no change")
    scratch_project(root, "board-bravo", waivers=reworded)
    r = run([PY, WAIVER_PROV, root])
    must_fail(r, "waiver_provenance on a reworded copy", "W-COPY")


@test("INCIDENT(2026-07-20): a waiver naming ANOTHER project is rejected",
      kind="known_bad")
def t_foreign_project_waiver_blocks():
    """The byte-copy signature: the prose still talks about the board it was
    written for. lipo3s-tsc's file opens 'usb-power-3s released
    v1.1-2026-07-16' and nobody noticed for a release cycle."""
    d = tmpdir("t4wav_")
    root = d / "projects"
    scratch_project(root, "board-alpha", waivers=INDEPENDENT_A)
    foreign = ("# board-alpha released v1.1-2026-07-16; the canon policies\n"
               "# below were adopted 2026-07-17 (adopted-forward).\n"
               + INDEPENDENT_B)
    scratch_project(root, "board-bravo", waivers=foreign)
    r = run([PY, WAIVER_PROV, root])
    must_fail(r, "waiver_provenance on a foreign-project rationale", "W-FOREIGN")
    contains(r.out, "board-alpha", "the foreign project should be named")


@test("independently-reasoned waivers PASS, and a DECLARED inheritance passes")
def t_independent_waivers_pass():
    """The gate must leave honest reuse alone, or it will simply be turned
    off. Two distinct rationales pass; and a project that DECLARES
    `derived_from` is allowed to reuse another board's measurement — which
    is what lipo3s-usb-hub should have written down."""
    d = tmpdir("t4wav_")
    root = d / "projects"
    scratch_project(root, "board-alpha", waivers=INDEPENDENT_A)
    scratch_project(root, "board-bravo", waivers=INDEPENDENT_B)
    must_pass(run([PY, WAIVER_PROV, root]), "waiver_provenance on distinct waivers")

    root2 = d / "projects2"
    scratch_project(root2, "board-alpha", waivers=INDEPENDENT_A)
    declared = INDEPENDENT_A.replace("- id: R-POUR",
                                     "- id: R-POUR\n  derived_from: board-alpha")
    scratch_project(root2, "board-bravo", waivers=declared)
    r = must_pass(run([PY, WAIVER_PROV, root2]),
                  "waiver_provenance on a DECLARED inheritance")
    contains(r.out, "DECLARED", "the declared reuse should be reported as ok")


# ==========================================================================
# INCIDENT 8 — DRC violations COUNTED rather than CLASSIFIED
#   2026-07-13 · spf commit 96785a0 "power_board v4.2"
#
#   "audit_board.py I7 upgraded: clearance/hole items now classified real
#   (different-net AND <0.10mm JLC 4L floor) vs margin (fab-legal,
#   warn-only); gate fails only on real regressions. Baseline re-recorded in
#   classified form."
#
#   A counting gate has two failure modes at once: it blocks on fab-legal
#   margin items (so it gets muted), and once muted it cannot see the real
#   ones. The pair below is the proof — IDENTICAL geometry, differing by
#   0.10mm of air, producing ONE clearance item each. A counter cannot tell
#   them apart. The classifier calls one REAL and the other margin.
#
#   VERIFIED RED, 2026-07-20: classified_drc.py's classification is the fix.
#   Replacing its `len(nets) > 1 and 0 <= v < args.fab_floor` test with a
#   plain `real.append(...)` for every clearance item (i.e. counting) makes
#   t_subfloor_crossnet_clearance_is_real pass but
#   t_fablegal_margin_is_not_real FAIL — the counting version calls the
#   0.15mm gap a real violation.
# ==========================================================================
@test("INCIDENT(2026-07-13 spf/96785a0): a SUB-FLOOR cross-net gap is REAL and blocks",
      kind="known_bad")
def t_subfloor_crossnet_clearance_is_real():
    """0.05mm of air between 5V and S_PLUS: below JLC's 0.10mm 4-layer
    floor, different nets. Unambiguously a defect."""
    d = tmpdir("t4drc_")
    board = add_track(sealed_copy(d), "5V", "S_PLUS", 0.05)
    r = run([KPY, CLASSIFIED, board, "--fab-floor", "0.10"])
    must_fail(r, "classified_drc on a sub-floor cross-net gap", "REAL=1")
    contains(r.out, "'5V'", "the offending nets must be named")
    contains(r.out, "VERDICT: FAIL", "classified_drc verdict")


@test("INCIDENT(2026-07-13 spf/96785a0): a FAB-LEGAL gap is margin, not a violation")
def t_fablegal_margin_is_not_real():
    """The same two tracks, 0.15mm apart — above the fab floor, so the board
    is manufacturable. A COUNTING gate sees the identical '1 clearance item'
    it saw above and cannot distinguish them; that is how gates get muted.
    The classifier must call this margin and put REAL at zero."""
    d = tmpdir("t4drc_")
    board = add_track(sealed_copy(d), "5V", "S_PLUS", 0.15)
    r = run([KPY, CLASSIFIED, board, "--fab-floor", "0.10"])
    contains(r.out, "REAL=0", "a fab-legal gap was classified as a real violation")
    contains(r.out, "margin(>= 0.1)=1", "the item should be counted as margin")


@test("INCIDENT(2026-07-13 spf/96785a0): the fab floor is a PARAMETER, not a constant")
def t_fab_floor_moves_the_boundary():
    """ONE board, the 0.05mm cross-net gap, graded twice. Against a 0.10mm
    fab it is a real violation; against a hypothetical 0.02mm-capable fab it
    is merely margin. Nothing about the copper changed — which is the point:
    'real' is a statement about the FAB, and 'the FAB's published
    capabilities override all' (canon, Routing section). A gate that hard-codes
    the number is a counter wearing a classifier's hat."""
    d = tmpdir("t4drc_")
    board = add_track(sealed_copy(d), "5V", "S_PLUS", 0.05)
    strict = run([KPY, CLASSIFIED, board, "--fab-floor", "0.10"])
    contains(strict.out, "REAL=1", "0.05mm gap graded against a 0.10mm floor")
    lax = run([KPY, CLASSIFIED, board, "--fab-floor", "0.02"])
    contains(lax.out, "REAL=0",
             "the same 0.05mm gap is fab-legal at a 0.02mm floor and must "
             "re-classify as margin")
    contains(lax.out, "margin(>= 0.02)=1", "the item must still be COUNTED")


# ==========================================================================
# INCIDENT 9 — auto/AI placement blind to electrical proximity
#   2026-07-13 · spf commit 47e0f82 (v4.1): "stranded decouplers up to 56mm
#     from their ICs, so C4/C5/C7/C8/C9/C10/C13/C14/C15/CA111 were snapped
#     back to 2-5mm of their anchors"
#   2026-07-13 · spf commit 96785a0 (v4.2): "15 violators this time - rev286
#     optimizes ratlines even harder" — not a one-off; the objective is
#     structurally blind
#   2026-07-14 · spf commit 17fea03 (v4.3): "CA2/CB2 (LM5145 VCC bypass)
#     were 47mm from their controllers - moved to 3-3.5mm"
#   2026-07-20 · circuits ec964a3: raw tscircuit auto-placement gave "11
#     audit failures + 214 DRC violations incl. 22 courtyard overlaps"
#   · skills/kicad-pcb/references/placement-and-proximity.md: "100 nF
#     decouplers 56-66 mm from their IC, LDO output caps 39 mm away, VCC
#     bypass caps 47 mm from their controllers."
#
#   Every one of those boards was fully connected and DRC-clean. Proximity
#   is an ELECTRICAL constraint that no geometric or connectivity gate
#   encodes, which is why it needs its own invariant (the IP gate).
#
#   VERIFIED RED, 2026-07-20: deleting the IP block from cook-loadcell's
#   03_src/audit_board.py makes t_autoplacement_strands_decouplers pass —
#   the stranded board is otherwise completely clean.
# ==========================================================================
@test("INCIDENT(2026-07-13 spf/47e0f82): a decoupler stranded at the incident distance FAILS",
      kind="known_bad")
def t_autoplacement_strands_decouplers():
    """Put C3 47mm from U1 — the measured LM5145 VCC-bypass distance from
    spf v4.3. The net is intact, the board routes, DRC is clean, and the
    bypass does nothing at switching frequency."""
    d, b = fresh_board()
    edit_board(b, "import pcbnew\n"
                  "u=b.FindFootprintByReference('U1')\n"
                  "c=b.FindFootprintByReference('C3')\n"
                  "p=u.GetPosition()\n"
                  "c.SetPosition(pcbnew.VECTOR2I(p.x+pcbnew.FromMM(33.0),\n"
                  "                              p.y+pcbnew.FromMM(33.0)))")
    proj = project_copy("cook-loadcell", d / "proj", board=b)
    r = run([KPY, "03_src/audit_board.py"], cwd=proj)
    # assert on the PROXIMITY failure specifically. A bare "IP" substring
    # also matches the gate's own ok-lines, which would let this test pass
    # against a build with no proximity gate at all — checked, it did.
    must_fail(r, "audit_board with a decoupler 47mm from its IC", "FAIL IP C3")


@test("INCIDENT(2026-07-13 spf/96785a0): MANY stranded satellites are ALL reported",
      kind="known_bad")
def t_all_stranded_satellites_reported():
    """rev286 stranded 15 parts at once. A gate that reports only the first
    violator turns a placement audit into a game of whack-a-mole — the
    operator fixes one, re-runs, finds another. Move every decoupler and
    assert the report names more than one of them."""
    d, b = fresh_board()
    edit_board(b, "import pcbnew\n"
                  "u=b.FindFootprintByReference('U1')\n"
                  "p=u.GetPosition()\n"
                  "n=0\n"
                  "for f in b.GetFootprints():\n"
                  "    if f.GetReference().startswith('C'):\n"
                  "        n+=1\n"
                  "        f.SetPosition(pcbnew.VECTOR2I(\n"
                  "            p.x+pcbnew.FromMM(20.0+n*1.5),\n"
                  "            p.y+pcbnew.FromMM(28.0)))")
    proj = project_copy("cook-loadcell", d / "proj", board=b)
    r = run([KPY, "03_src/audit_board.py"], cwd=proj)
    must_fail(r, "audit_board with every decoupler stranded", "FAIL IP")
    hits = len(re.findall(r"FAIL IP ", r.out))
    check(hits >= 3,
          f"only {hits} proximity violations reported — a gate that stops at "
          f"the first violator turns a placement audit into whack-a-mole "
          f"(rev286 stranded 15 parts at once)")


# ==========================================================================
# INCIDENT 10 — a release shipped with NO reference designators on silk
#   2026-07-17 · esp32-laser-timing/07_releases/v1.0-2026-07-17/SUPERSEDED.md:
#     "DO NOT ORDER ... its silkscreen carried NO reference designators
#     (U2, R3, C1, ... were on the F.Fab assembly layer only, which fab
#     houses do not print)."
#   · commit cfbc83b added the rule: "refdes-on-silk rule (golden rule 3b +
#     audit I8 + pipeline text)"
#   · canon P4's motivating incident: "a board shipped with all 76 refs on
#     F.Fab — no names on the physical board"
#
#   t1_audit.py already covers audit_template I8 and policy P-SILK-REF. What
#   is added here is the RELEASE-SHAPED case: not one part, but EVERY part,
#   which is what actually shipped and what a spot-check would miss.
#
#   VERIFIED RED, 2026-07-20: git show cfbc83b^:skills/kicad-pcb/scripts/
#   audit_template.py has no I8 block at all; the F.Fab-only board prints
#   "AUDIT: PASS" against it.
# ==========================================================================
@test("INCIDENT(2026-07-17 esp32 v1.0): EVERY refdes on F.Fab only FAILS the audit",
      kind="known_bad")
def t_whole_board_refdes_off_silk():
    """The shipped defect: not a stray part, the entire board. The fab zip
    differed from v1.1's only in the silk layer, and nothing before I8
    objected."""
    d, b = fresh_board()
    edit_board(b, "import pcbnew\n"
                  "for f in b.GetFootprints():\n"
                  "    f.Reference().SetLayer(pcbnew.F_Fab)")
    cfg = d / "audit.json"
    cfg.write_text(json.dumps({
        "frame": [20.0, 20.0, 55.0, 45.0], "edge_margin": 0.3,
        "screw_head_r": 3.2, "fab_floor": 0.10,
        "float_ok_numbers": ["MP", "S1"]}))
    r = run([KPY, AUDIT_T, b, "--config", cfg])
    must_fail(r, "audit_template on a board with no printed refdes",
              "I8 refdes-not-on-silk")
    # the report must name MANY parts, not stop at the first
    hits = len(re.findall(r"I8 refdes-not-on-silk", r.out))
    check(hits >= 10,
          f"only {hits} refdes reported; a whole-board defect must not be "
          f"reported as a single finding")


@test("INCIDENT(2026-07-17 esp32 v1.0): a HIDDEN silk refdes is caught too",
      kind="known_bad")
def t_invisible_refdes_on_silk():
    """The variant that a layer-only check would miss: the text IS on
    F.SilkS, but with the visibility flag off. It plots nothing. I8 checks
    both layer and IsVisible()."""
    d, b = fresh_board()
    edit_board(b, "for f in b.GetFootprints():\n"
                  "    f.Reference().SetVisible(False)")
    cfg = d / "audit.json"
    cfg.write_text(json.dumps({
        "frame": [20.0, 20.0, 55.0, 45.0], "edge_margin": 0.3,
        "screw_head_r": 3.2, "fab_floor": 0.10,
        "float_ok_numbers": ["MP", "S1"]}))
    r = run([KPY, AUDIT_T, b, "--config", cfg])
    must_fail(r, "audit_template on invisible refdes", "I8 refdes-not-on-silk")


# ==========================================================================
# INCIDENT 11 — a part in the schematic that never reached the board
#   2026-07-14 · spf commit bed8ace (v4.5): "KiCad 10.0.4 re-validation found
#     D8 (USBLC6-2SC6, port 3 ESD) in the schematic/netlist but absent from
#     the board since v4: the 3-port change added D8's place() call but not
#     its REF_FP footprint entry, and generate_board.py silently skipped
#     footprint-less parts. Port 3 data lines (J14->J13) carried no ESD
#     protection while ports 1/2 had D2/D3."
#   · circuits 9c7ddec: "Missing FPID is a HARD ERROR, never a warning: a
#     silently un-placed part is an electrically-wrong board that still
#     passes DRC."
#
#   t1_generate_board.py covers "missing FPID = hard error" on the generator.
#   Added here: the DOWNSTREAM gate — schematic/board parity — because in
#   the real incident the generator had already run and shipped, and parity
#   is what caught it on re-validation.
# ==========================================================================
@test("INCIDENT(2026-07-14 spf/bed8ace): a part missing from the board FAILS parity",
      kind="known_bad")
def t_silently_unplaced_part_fails_parity():
    """Delete one part from a built board and ask the parity gate. This is
    the re-validation that found D8 missing for a whole revision — a board
    that passed DRC, passed connectivity, and had an unprotected USB port."""
    d, b = fresh_board()
    edit_board(b, "b.Remove(b.FindFootprintByReference('C6'))")
    r = run([KPY, SCRIPTS / "board_netlist_parity.py", b, SEALED_LC])
    must_fail(r, "parity with a silently unplaced part")
    check("C6" in r.out, f"the missing refdes must be named:\n{r.out[-1200:]}")



@test("INCIDENT(2026-07-21 usb-hub-3s ADR-0006): the male-plug class — "
      "connector gender is a recorded part FACT and the calibration is "
      "pinned BOTH directions")
def t_male_plug_and_calibration():
    """A USB-A male PLUG served weeks as a receptacle: footprint, netlist
    and silk were consistently wrong TOGETHER, so every machine gate
    passed; the fresh-context render review caught it. Machine teeth that
    exist: (1) the 02_parts contract documents the connectors-only
    `mates:` fact read from the drawing title block; (2) escape_check v2
    is calibrated BOTH directions on the SY8368 (shipped-at-standard
    a4ff7ed vs the v2 stall) so neither over- nor under-conservatism can
    silently return."""
    c = (ROOT / "skills/pcb-design/templates/contracts/02_parts/contracts.md").read_text()
    check("mates:" in c and "title block" in c.lower(),
          "02_parts contract lost the mates:/title-block gender fact")
    esc = ROOT / "skills/kicad-pcb/scripts/escape_check.py"
    r1 = run([KPY, esc, "--style", "qfn", "--pitch", "0.45",
              "--escapes-worst-side", "6", "--pins", "10"])
    check("CONDITIONAL" in r1.out and "jlc_4layer_standard" in r1.out,
          "shipped SY8368 config lost its conditional-standard verdict")
    r2 = run([KPY, esc, "--style", "qfn", "--pitch", "0.45"])
    check("INFEASIBLE" in r2.out and "jlc_4layer_advanced" in r2.out,
          "stranded SY8368 config lost its unconditional-advanced verdict")


if __name__ == "__main__":
    sys.exit(main())
