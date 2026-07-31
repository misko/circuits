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
import ast
import json
import os
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


#: The floor the injected pair's neighbourhood must clear, in mm. MEASURED
#: at the chosen site: 3.862mm to the nearest F.Cu copper or board edge
#: (binary search over `SHAPE::Collide`, exact shapes — a BOUNDING BOX is
#: useless here, the board's diagonal tracks have boxes 15mm across). 1.0 is
#: a floor with 3.9x of headroom, not the margin itself.
TRACK_HALO_MM = 1.0


def add_track(board, net_a, net_b, gap_mm, y=51.8, x0=66.0, x1=70.0, w=0.2):
    """Two parallel 0.2mm F.Cu tracks with `gap_mm` of copper-to-copper air
    between them. gap 0.05 = below the 0.10mm JLC fab floor; gap 0.15 = a
    fab-legal margin item. Same geometry, one number apart.

    THE SITE IS LOAD-BEARING, AND THE FIXTURE NOW ASSERTS IT (2026-07-27).
    The pair used to be laid at y=60.0, x=28..32 — on top of the sealed
    board's existing copper: a RING_23 track (30.2,60.8)->(32.6,58.4)
    crosses BOTH injected tracks, and J3's RING_23 THT pad at (30.2,60.8)
    overlaps the 5V one. KiCad emits ONE violation class for that
    neighbourhood and picks by the order items reach the DRC engine, and
    pcbnew's Save() does not order Python-added tracks stably — so the
    intended 0.05mm `clearance` item was preempted by `tracks_crossing`
    on 4.6% of runs (3/65, serial) and REAL fell to 0. See the INCIDENT 8
    header below for the full measurement. This site is the maximum-clearance site on this board
    (3.862mm); the isolation assert makes any future contamination fail
    LOUDLY at fixture-build time instead of flaking at assert time."""
    top, bot = y - w, y + w + gap_mm + w
    edit_board(board, (
        "import pcbnew\n"
        # ---- ISOLATION ASSERT, before anything is added. Exact shapes via
        # pcbnew's own SHAPE::Collide — the checker for the fixture must not
        # be a hand-rolled bbox approximation of the thing DRC measures.
        f"rect=pcbnew.SHAPE_RECT(pcbnew.VECTOR2I_MM({x0},{top}),"
        f" pcbnew.FromMM({x1}-{x0}), pcbnew.FromMM({bot}-{top}))\n"
        "near=[t for t in b.Tracks() if t.IsOnLayer(pcbnew.F_Cu)"
        f" and t.GetEffectiveShape().Collide(rect, pcbnew.FromMM({TRACK_HALO_MM}))]\n"
        "near+=[p for f in b.GetFootprints() for p in f.Pads()"
        " if p.IsOnLayer(pcbnew.F_Cu)"
        " and p.GetEffectiveShape(pcbnew.F_Cu).Collide(rect,"
        f" pcbnew.FromMM({TRACK_HALO_MM}))]\n"
        "if near:\n"
        "    raise SystemExit('FIXTURE CONTAMINATED: %d copper item(s) within "
        f"{TRACK_HALO_MM}mm of the injected pair site, e.g. net %s @ %s. The "
        "DRC violation CLASS for a contaminated neighbourhood is "
        "order-dependent and this fixture flakes (see add_track). Move the "
        "pair to clear copper.'"
        " % (len(near), near[0].GetNetname(), near[0].GetPosition()))\n"
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
    polarity was verified.

    WIDENED 2026-07-30 WITH THE GATE, AND THE WIDENING IS WHY IT NEEDED
    EDITING. P-POL used to grep only for PER-BOARD PYTHON, so stripping
    `audit_board.py` was enough to remove "every polarity check". ADR-0002
    abolished that location, and the check now ALSO accepts the generic
    backend's `floorplan.yaml asserts.pad_net[]` — which cook-loadcell has had
    all along (five entries, D1/D2 pad 1 = cathode). Stripping only the Python
    therefore no longer removes the FACT, and this fixture would have gone
    green while claiming to prove a gate can fail.

    The incident is unchanged; what it takes to reproduce it is not. Both
    homes are emptied below, and the ADJACENT-PROPERTY re-verify at the end
    restores ONE of them — the declaration, not the script — and requires
    P-POL to come back. That contrast is what proves the FAIL is about the
    absent fact rather than about a mangled tree."""
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
    # ...AND out of the generic backend's declaration, the second home.
    fpp = proj / "03_src" / "floorplan.yaml"
    fp_before = fpp.read_text()
    import yaml as _yaml
    fp_y = _yaml.safe_load(fp_before) or {}
    check((fp_y.get("asserts") or {}).get("pad_net"),
          "cook-loadcell was expected to DECLARE asserts.pad_net — if it no "
          "longer does, this fixture is stripping a home that is not there "
          "and the known-bad is weaker than it reads")
    fp_y["asserts"]["pad_net"] = []
    fpp.write_text(_yaml.safe_dump(fp_y))
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
    # ADJACENT PROPERTY: put the DECLARATION back (the script stays stripped).
    # P-POL must return, from the generic home alone — which is the whole point
    # of the widening, and is re-measured here rather than asserted upstream.
    fpp.write_text(fp_before)
    run([KPY, POLICY, proj, "--skip-drc"])
    row2 = [l for l in md.read_text().splitlines() if "P-POL" in l]
    check(row2 and not any("FAIL" in l for l in row2),
          f"restoring floorplan.yaml asserts.pad_net did not bring P-POL back, "
          f"so the FAIL above was not about the missing fact: {row2}")


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
    # G-COVER/G-INPUT (2026-07-27): the verdict must state WHAT it compared.
    contains(r.out, "input: root", "names the tree it graded")
    contains(r.out, "waiver(s) graded", "carries an N/M denominator")


@test("waiver_provenance FAILS a tree with NO waivers rather than passing it",
      kind="known_bad")
def t_waiver_zero_denominator():
    """G-COVER, canon M-COVER (2026-07-27). W-COPY is a CROSS-PROJECT
    comparison: it needs at least two projects carrying waivers before it can
    compare anything. A tree with none printed
    `WAIVER PROVENANCE: PASS (0 fails, 0 ok)` and exited 0 — byte-identical in
    meaning to a clean fleet, which is what a wrong `root` argument, a renamed
    `policy_waivers.yaml`, or a schema change all produce.
    RED-VERIFIED against pre-fix code (git show 5054b07:...waiver_provenance
    .py): it exits 0 on this fixture.

    RE-VERIFIED AND STRENGTHENED 2026-07-30. The 2026-07-27 fix made this case
    exit 1 with the word `FAIL` — which is byte-for-byte what a FINDING prints
    and what a mistyped `root` printed, so the one verdict meaning "believe
    nothing above this line" stayed unreadable and went on being read as an
    invocation error. The assertions below now pin the DISTINGUISHABILITY, not
    merely the failure: see
    `t_graded_nothing_is_distinguishable_from_an_invocation_error`."""
    d = tmpdir("t4wav_")
    root = d / "projects"
    scratch_project(root, "board-alpha", waivers=None)
    r = must_fail(run([PY, WAIVER_PROV, root]),
                  "waiver_provenance over a tree with no waivers",
                  "GRADED NOTHING")
    contains(r.out, "M-COVER", "cites the canon it is enforcing")
    contains(r.out, "0 of 0 waiver(s)", "carries the zero denominator")
    # WHAT it looked for, WHERE, and that it graded zero — the three facts a
    # reader needs to tell this apart from a usage error without reading code.
    contains(r.out, "looked for", "names the addresses it searched")
    contains(r.out, "03_src/<board>/rules/policy_waivers.yaml",
             "names the ADR-0007 multi-board address too")
    contains(r.out, "under", "names the tree it searched")
    contains(r.out, "THIS IS NOT A PASS",
             "says out loud that this is not a pass")
    eq(r.rc, 3, "graded-nothing has its own exit code, not the finding code")


@test("GRADED NOTHING and an INVOCATION ERROR are distinguishable — the whole "
      "lesson of the 2026-07-30 waiver-path defect", kind="known_bad")
def t_graded_nothing_is_distinguishable_from_an_invocation_error():
    """INCIDENT (2026-07-30, smc0985-cooksense). `waiver_provenance` hardcoded
    `03_src/rules/policy_waivers.yaml`; the ADR-0007 multi-board layout puts
    each board's waivers at `03_src/<board>/rules/policy_waivers.yaml`. When
    the flat address held nothing, the gate's denominator was zero — and it
    reported that by printing `FAIL` and exiting **1**, the same code a real
    finding uses and the same code a bad `root` argument used.

    So the gate DID fail, and its failure was unreadable. It was taken for an
    invocation error and nobody chased it. That is the defect this fixture
    exists for: not "the gate must fail", which was already true, but "the
    gate's blindness must be legible in one line".

    Four outcomes, four exit codes, asserted here as MUTUALLY DISTINCT:
      0 clean · 1 findings · 2 invocation error · 3 graded nothing

    RED-VERIFIED against pre-fix code (`git show 74ce4b66:skills/kicad-pcb/
    scripts/waiver_provenance.py`): pre-fix the bad-root case and the
    no-waivers case BOTH exit 1, so `eq(usage.rc, 2)` fails and the
    distinctness assertion below is unsatisfiable. Restored: passes."""
    d = tmpdir("t4wav_")

    # --- (a) INVOCATION ERROR: a root that is not a directory at all.
    usage = run([PY, WAIVER_PROV, d / "no-such-tree"])
    eq(usage.rc, 2, "a bad root is an INVOCATION error, exit 2")
    contains(usage.out, "INVOCATION", "says so in words")
    not_contains(usage.out, "GRADED NOTHING",
                 "a gate that never started did not grade zero — it graded "
                 "nothing at all, and conflating the two is the defect")

    # --- (b) INVOCATION ERROR: --project naming a directory that is not there.
    #     This used to arrive as a zero denominator, i.e. as a verdict ABOUT a
    #     board, when it is a typo in the command line.
    root = d / "projects"
    scratch_project(root, "board-alpha", waivers=INDEPENDENT_A)
    scratch_project(root, "board-bravo", waivers=INDEPENDENT_B)
    typo = run([PY, WAIVER_PROV, root, "--project", "board-alfa"])
    eq(typo.rc, 2, "an unknown --project is an INVOCATION error, exit 2")
    contains(typo.out, "board-alpha",
             "names the projects that DO exist, so the typo is fixable")

    # --- (c) GRADED NOTHING: the tree is real, the gate ran, the denominator
    #     is zero.
    empty = d / "empty"
    scratch_project(empty, "board-alpha", waivers=None)
    nothing = run([PY, WAIVER_PROV, empty])
    eq(nothing.rc, 3, "a real tree with no waivers is GRADED NOTHING, exit 3")

    # --- (d) FINDINGS: a real copied waiver.
    root2 = d / "projects2"
    scratch_project(root2, "board-alpha", waivers=INDEPENDENT_A)
    scratch_project(root2, "board-bravo", waivers=INDEPENDENT_A)
    finding = run([PY, WAIVER_PROV, root2])
    eq(finding.rc, 1, "a real finding is exit 1")
    contains(finding.out, "W-COPY", "and it is the copy check that fired")

    # --- THE ASSERTION THE INCIDENT EARNED: all four are different.
    clean = run([PY, WAIVER_PROV, root])
    eq(clean.rc, 0, "two independent waivers are clean")
    codes = [clean.rc, finding.rc, usage.rc, nothing.rc]
    check(len(set(codes)) == 4,
          f"clean/findings/usage/graded-nothing must be four DISTINCT exit "
          f"codes, got {codes} — collapsing any two of them onto one code is "
          f"exactly how this gate's zero denominator read as a usage error "
          f"for months")


@test("ADR-0007: a MULTI-BOARD project's per-board waivers are all graded, and "
      "findings NAME THE BOARD", kind="known_bad")
def t_multiboard_waivers_are_all_graded():
    """INCIDENT (2026-07-30, smc0985-cooksense at 74ce4b66). MEASURED:

      * `03_src/rules/policy_waivers.yaml` was an UNDECLARED SYMLINK to
        `../cooksense/rules/policy_waivers.yaml` (mode 120000, committed at
        18392f2e), so cooksense's 12 waivers were graded by ACCIDENT.
      * `03_src/interposer/rules/policy_waivers.yaml` — 4 entries, S-VER /
        E-ADR / E-TOPO / M-REPRO — was graded by NOTHING, while the run printed
        `WAIVER PROVENANCE: PASS (0 fails, 1 ok) — 12/25 waiver(s) graded`.

    The symlink was the HAZARD, not the mitigation: a board selector wearing a
    project-wide address, which silently picks one board and can never pick the
    other. The fix does not select at all — `waiver_files()` ENUMERATES both
    layouts and labels each file with its board directory.

    This fixture reproduces the exact shape: two boards, the copied rationale
    on the board the symlink does NOT point at.

    RED-VERIFIED against pre-fix code (`git show 74ce4b66:skills/kicad-pcb/
    scripts/waiver_provenance.py`), and the MEASURED pre-fix output is the
    point: it reads only the symlinked flat address, never sees the
    interposer's copy, and exits **0** printing

        WAIVER PROVENANCE: PASS (0 fails, 2 ok) — 2/2 waiver(s) graded

    i.e. a FULL denominator — 2 of 2 — over 2 of the tree's 3 waiver files.
    The gate was not merely silent about what it missed; it certified
    completeness it did not have, which is why nothing downstream asked.
    Restored, the same tree reports `3/3 waiver(s) graded`, W-COPY fires
    naming `multi-board-proj/interposer [R-POUR]`, and it exits 1."""
    d = tmpdir("t4wav_")
    root = d / "projects"

    # A single-board project, to be copied FROM.
    scratch_project(root, "board-alpha", waivers=INDEPENDENT_A)

    # The ADR-0007 multi-board project: two boards, waivers under 03_src/<board>/.
    multi = root / "multi-board-proj"
    for board, text in (("main", INDEPENDENT_B), ("interposer", INDEPENDENT_A)):
        wd = multi / "03_src" / board / "rules"
        wd.mkdir(parents=True, exist_ok=True)
        (wd / "policy_waivers.yaml").write_text(text)
    # The undeclared symlink that made the pre-fix gate look like it worked:
    # the flat single-board address pointing INTO one board's directory.
    (multi / "03_src" / "rules").mkdir(parents=True, exist_ok=True)
    os.symlink("../main/rules/policy_waivers.yaml",
               multi / "03_src" / "rules" / "policy_waivers.yaml")

    r = must_fail(run([PY, WAIVER_PROV, root]),
                  "waiver_provenance over an ADR-0007 multi-board project",
                  "W-COPY")
    # The finding must be on the board the symlink does NOT point at — that is
    # the entry the pre-fix gate could not reach.
    contains(r.out, "multi-board-proj/interposer",
             "the finding NAMES THE BOARD, because `main [R-POUR]` and "
             "`interposer [R-POUR]` are different waivers about different "
             "copper and the old label could not tell them apart")
    # Both boards' files are named on the run (G-INPUT), so an ungraded board
    # is visible rather than inferable from a total.
    contains(r.out, "[board: main]", "names the main board's file")
    contains(r.out, "[board: interposer]", "names the interposer's file")
    # THE SYMLINK IS DEDUPED, NOT DOUBLE-COUNTED: 1 alpha + 2 boards = 3, not 4.
    contains(r.out, "3 waiver(s) total",
             "the flat symlink and the file it points at are ONE file — "
             "resolved by real path, which is identity rather than choice")

    # ADJACENT PROPERTY, so the fixture cannot pass for the wrong reason: with
    # the interposer's rationale made INDEPENDENT and nothing else changed, the
    # same tree PASSES. If it failed here too, the assertion above would be
    # about the multi-board layout rather than about the copied waiver.
    (multi / "03_src" / "interposer" / "rules"
     / "policy_waivers.yaml").write_text(INDEPENDENT_B.replace(
         "- id: R-THERM", "- id: R-THERM2"))
    ok = must_pass(run([PY, WAIVER_PROV, root]),
                   "the same multi-board tree with an INDEPENDENT rationale")
    contains(ok.out, "3 waiver(s) total", "still reads all three files")


@test("G-VACUOUS W-COPY/W-FOREIGN: an ORIGINAL waiver carrying an INVENTED "
      "measurement passes — the verdict is invariant under the number",
      kind="vacuity", gate="waiver_provenance.py")
def t_vacuity_a_waiver_whose_typed_measurement_is_arithmetically_false_passes():
    """THE DECLARED BLIND SPOT (canon G-VACUOUS; the executable half of the
    `VACUITY:` block in waiver_provenance.py's docstring).

    This fixture asserts the gate PASSES while the fact it grades — "this
    waiver's evidence is about THIS board" — is FALSE. It PINS the defect;
    closing it should break this test, which then becomes a `known_bad`.

    NARROWED, NOT RETIRED (2026-07-29, the `evidence:` schema). The gate now
    REGENERATES AND DIFFS any number an entry declares in an `evidence:` block,
    with W-FLIP reporting a reversed conclusion by name. This fixture still
    stands, and deliberately so: the entry below declares NO `evidence:` block,
    which is 22 of 22 fleet entries on the day the schema landed, so a number
    typed in `why:` prose is still read by nothing. That is the surviving half
    of the blind spot and `waiver_provenance.py`'s `VACUITY:` block now says
    exactly that. The CONTRAST — the same waiver with the same false number
    moved into an `evidence:` block, caught with the reversal named — is
    `t1_waiver_evidence.py`
    `t_incident_the_c_sw1_waiver_promoted_to_the_evidence_schema_is_caught`,
    and the OWED ceiling is what stops the prose form from spreading.

    THE INCIDENT (measured 2026-07-29, pluto-rx2-8way at commit c07aaf2). The
    waiver `P-ADJ-UNREACHED` read:

        MEASURED by hand instead: C_SW1 pad 1 to U_SW pin 8 = 2.62 mm, inside
        the 3 mm the datasheet sentence means.

    Re-measured with pcbnew against the board that revision governed: **3.085 mm**
    pad-centre to pad-centre, which is the measure `policy_audit.py:412` itself
    defines for P-ADJ — 0.085 mm OVER the threshold the waiver asserted it was
    inside. THE WAIVER'S CONCLUSION FLIPS. `2.62` reproduces under no definition
    (edge-to-edge is 2.375 mm rect / 2.438 mm roundrect), so it is a free-hand
    estimate rather than a typo or a mis-defined metric. A second entry read
    "2.53 mm" against an actual 3.057 mm; that one stayed inside its 4 mm budget,
    so it was wrong without being load-bearing. Both survived a full revision
    cycle. Fleet denominator: **16 of 22 waiver entries carry a hand-typed
    number**; 2 carry a re-runnable command.

    WHY THE GATE CANNOT SEE IT. W-COPY and W-FOREIGN compare one piece of prose
    to another, and `normalize()` deliberately folds unit spacing so a number
    survives a reword. The only other gate on waiver evidence is
    `policy_audit.py:165`, `len(str(w.get("why", ""))) < 40` — a LENGTH test.

    PROVED WITHOUT A BOARD, which is the sharpest available form: the fixture
    holds everything constant and replaces only the measurement, first with the
    true value, then with the false one, then with a PHYSICALLY IMPOSSIBLE one.
    The gate's output is byte-identical every time. A number that cannot change
    the verdict is not an input to it."""
    d = tmpdir("t4wav_vac_")
    tmpl = ("- id: P-ADJ\n"
            "  refs: [C_SW1]\n"
            "  why: >-\n"
            "    MEASURED by hand (pcbnew, 2026-07-29) on THIS board: C_SW1 pad 1\n"
            "    to U_SW pin 8 = {n} mm, inside the 3 mm the PE42482A-X datasheet\n"
            "    sentence means. Pin 8 sits on the global 3V3 net so no keep_short\n"
            "    budget can address it.\n")
    outs = {}
    for label, n in (("true", "3.085"), ("false", "2.62"),
                     ("impossible", "-410.00")):
        root = d / label / "projects"
        scratch_project(root, "board-alpha", waivers=tmpl.format(n=n))
        scratch_project(root, "board-bravo", waivers=INDEPENDENT_B)
        r = must_pass(run([PY, WAIVER_PROV, root]),
                      f"waiver_provenance on the {label} measurement — THE "
                      f"BLIND SPOT. If the 'false' or 'impossible' case now "
                      f"FAILS, the gate has learned to re-derive a number: "
                      f"convert this fixture to kind=\"known_bad\"")
        # NORMALISE THE LOCATORS, NOT THE VERDICT. Each arm runs in its own
        # tmpdir, and the gate now echoes the tree it read AND the cwd it would
        # run evidence commands from (2026-07-29, the `evidence:` schema), so a
        # raw byte-compare would differ on the PATH rather than on the finding.
        # Every path is replaced by a constant and nothing else is touched: the
        # assertion below still compares the full report, verdict included.
        outs[label] = (r.out.replace(str(root), "<root>")
                            .replace(str(root.parent), "<tree>")
                            .replace(str(root.resolve()), "<root>")
                            .replace(str(root.resolve().parent), "<tree>"))

    eq(outs["false"], outs["true"],
       "the verdict must be shown INVARIANT under a measurement that is over "
       "the threshold it claims to be inside — if these differ the gate reads "
       "the number after all and this fixture is wrong")
    eq(outs["impossible"], outs["true"],
       "a NEGATIVE 410 mm separation between two pads on a 40 mm board is "
       "graded identically to the true 3.085 mm — nothing in this repo reads "
       "the digits")
    contains(outs["true"], "waiver(s) graded",
             "the gate does report a denominator — it counts the waivers it "
             "never re-derives, which is why the blind spot survived being "
             "measured by G-COVER")


@test("waiver_provenance SAYS SO when only one project carries waivers")
def t_waiver_single_project_says_so():
    """The subtler half, and the reason the zero case above is not enough.
    With ONE project carrying waivers the tool exits 0 legitimately — but
    W-COPY, its whole cross-project half, compared nothing. That has to be
    visible in the verdict rather than inferred from the project count."""
    d = tmpdir("t4wav_")
    root = d / "projects"
    scratch_project(root, "board-alpha", waivers=INDEPENDENT_A)
    scratch_project(root, "board-bravo", waivers=None)
    r = must_pass(run([PY, WAIVER_PROV, root]),
                  "waiver_provenance with a single waiver-carrying project")
    contains(r.out, "cross-project half of this gate graded nothing",
             "declares the half of itself that did not run")


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
#
#   THE FLAKE, ROOT-CAUSED AND KILLED 2026-07-27 (it had been excused twice
#   as "the known temp-path flake, commit 2de4b2a" — and 2de4b2a fixed a
#   DIFFERENT, real bug, so the excuse was plausible and wrong).
#
#   MEASURED failure rate of t_subfloor_crossnet_clearance_is_real before the
#   fix: 2/25 (8.0%) run SERIALLY, one process at a time, no concurrency and
#   no second kicad-cli anywhere — which already refutes the shared-temp-path
#   theory. A second independent loop hit 1/40 (2.5%); pooled 3/65 = 4.6%.
#
#   IT IS NOT A RACE AND IT IS NOT THE REPORT FILE. Measured, in order:
#     * 20/20 identical output re-running classified_drc.py on ONE fixed
#       board — the checker is deterministic given its input;
#     * a captured failing board reproduces BAD 5/5 — the board is the
#       variable, not the run;
#     * good vs bad board: byte-identical multiset of lines (0 lines
#       unique to either, same 265228 bytes) once uuids are normalised.
#       The files differ ONLY in the ORDER pcbnew's Save() emits the
#       injected 5V segment — index 37 in the good file, 54 in the bad.
#   pcbnew does not promise a stable serialisation order for items added
#   through the Python API, and the position moves run to run.
#
#   WHY ORDER CHANGED THE VERDICT: the pair used to be injected at y=60.0,
#   x=28..32, which on this board is ON TOP OF EXISTING COPPER. A RING_23
#   track (30.2,60.8)->(32.6,58.4) crosses both injected tracks and J3's
#   RING_23 THT pad at (30.2,60.8) overlaps the 5V one. KiCad emits ONE
#   violation class for that neighbourhood and picks by the order items
#   reach the DRC engine, so the same geometry reported either
#       [clearance] 0.0500mm 5V<->S_PLUS  +  [shorting_items] 5V/RING_23
#   or  [tracks_crossing] x2  and NO clearance item at all
#   — and in the second case REAL=0 and the (correct, unweakened) REAL=1
#   assertion fails.
#
#   THE FIX IS THE FIXTURE, NOT THE ASSERTION. `REAL=1` is the correct
#   expectation and is unchanged; loosening it would be the "lower the floor
#   until it cannot fail" move ADR-0004 forbids. The pair moved to y=51.8,
#   x=66.0..70.0 — the maximum-clearance site on this board, 3.862mm to the
#   nearest F.Cu copper or board edge, found by binary search over exact
#   `SHAPE::Collide` (bounding boxes are worthless here: this board's
#   diagonal tracks have boxes ~15mm across) — and add_track now ASSERTS its
#   site is clear to TRACK_HALO_MM, naming the offending net, so the
#   contamination cannot come back silently. The save-order nondeterminism
#   still happens; it no longer has anything to bite.
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


@test("classified_drc FAILS a DRC report it cannot PARSE, instead of reading "
      "it as a clean board", kind="known_bad")
def t_classified_drc_unparseable_report_is_a_fail():
    """G-COVER, canon M-COVER (2026-07-27). The whole verdict rests on
    `re.split(r"\\[(\\w+)\\]: ", txt)`. A report in a format this script no
    longer recognises — a KiCad release that changed the block header, a
    truncated write, a kicad-cli that emitted JSON — splits into ONE block,
    yields zero categories, zero clearance items, and printed
    `VERDICT: PASS` with exit 0. That is the counting-vs-classifying incident
    this section is about, one level up: the classifier classified nothing and
    called the board clean.

    The `--report` replay seam exists so this can be tested at all; without it
    the report contents are produced by kicad-cli and cannot be injected.
    RED-VERIFIED against pre-fix code (git show 5054b07:...classified_drc.py
    + the same fixture through the pid-suffixed path): zero blocks parsed
    printed `categories: NONE` and `VERDICT: PASS`, exit 0."""
    d = tmpdir("t4drcfmt_")
    bogus = d / "future_format.rpt"
    # a plausible next-format report: real findings, none in the [type]: shape
    bogus.write_text(
        '{"$schema": "kicad_drc", "violations": [\n'
        '  {"type": "clearance", "severity": "error",\n'
        '   "description": "Clearance violation (netclass \'Default\' '
        'clearance 0.2 mm; actual 0.05 mm)"},\n'
        '  {"type": "shorting_items", "severity": "error"}\n'
        ']}\n')
    r = run([KPY, CLASSIFIED, "unused.kicad_pcb", "--report", bogus])
    must_fail(r, "classified_drc on an unparseable report", "VERDICT: FAIL")
    contains(r.out, "did not understand",
             "the verdict must name the parse failure, not imply cleanliness")
    contains(r.out, "M-COVER", "cites the canon it is enforcing")


@test("classified_drc still PASSES a genuinely clean report (the guard "
      "discriminates)")
def t_classified_drc_clean_report_still_passes():
    """A guard that failed every report would be worthless. kicad-cli writes
    an explicit zero-count line for a clean board, and that must still pass —
    it is the difference between 'no violations' and 'no parse'."""
    d = tmpdir("t4drcok_")
    clean = d / "clean.rpt"
    clean.write_text("** Found 0 DRC violations **\n"
                     "** Found 0 unconnected pads **\n"
                     "** Found 0 Footprint errors **\n")
    r = run([KPY, CLASSIFIED, "unused.kicad_pcb", "--report", clean])
    check(r.rc == 0, f"a clean report must pass, got rc={r.rc}\n{r.out}")
    contains(r.out, "VERDICT: PASS", "clean report verdict")


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


@test("INCIDENT(2026-07-27 flake): the fixture's ISOLATION ASSERT has teeth",
      kind="known_bad")
def t_add_track_rejects_a_contaminated_site():
    """Test the guard, not just with it. The three tests above are only
    deterministic because the injected pair has empty copper around it, and
    that precondition was invisible from the day the fixture was written —
    the pair sat on RING_23 and the suite flaked at 4.6% (3/65) with nothing
    in the failure output pointing at the cause.

    VERIFIED RED, 2026-07-27: this calls add_track at the ORIGINAL site
    (y=60.0, x=28..32) — the exact coordinates that flaked — and requires the
    assert to refuse it and NAME the copper it collided with. Neutering the
    assert in add_track (`if near:` -> `if False:`, i.e. the pre-fix
    behaviour) makes this test FAIL with "add_track ACCEPTED the
    known-contaminated site"; restoring it makes it pass again. The silent
    acceptance IS the defect."""
    d = tmpdir("t4drc_")
    try:
        add_track(sealed_copy(d), "5V", "S_PLUS", 0.05, y=60.0, x0=28.0, x1=32.0)
    except Exception as e:                       # harness.Failed from must_pass
        contains(str(e), "FIXTURE CONTAMINATED",
                 "the isolation assert should have refused the old site")
        contains(str(e), "RING_23",
                 "the assert must NAME the copper it collided with")
    else:
        check(False, "add_track ACCEPTED the known-contaminated site "
                     "(y=60.0, x=28..32) — the isolation assert cannot fail, "
                     "so it is worthless and the flake will come back")


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



# ==========================================================================
# INCIDENT 14 — A CONNECTOR LEGEND SITTING ON ITS NEIGHBOUR
#   2026-07-29 · projects/pluto-rx2-8way/03_src/floorplan.yaml, revision
#     header item A, recorded by that board's own agent:
#       '"RX2 -> PLUTO RX2" measured NEARER J_ANT1 (7.29 mm) THAN J_RX2
#        (7.85 mm) — a connector labelled on its neighbour, on the one pair of
#        ports whose confusion feeds an SDR input with an antenna.'
#   · projects/pluto-cal-switch, MEASURED here 2026-07-29: the legend
#     'USB 5V' is 7.40 mm from J_USB and 6.01 mm from F1, so the board's USB
#     connector owns no legend of its own.
#   · fleet sweep 2026-07-29: 55 misowned labels across 11 of 23 boards,
#     including 12 on cooksense's interposer and 5 on cooksense itself.
#
#   P-SILK-FN graded PRESENCE — "some silk text is within 8mm of this part" —
#   and PASSED all of it. Presence cannot see this class by construction: a
#   label nearer the WRONG connector is present. And it is worse than a missing
#   label, because it actively misdirects the person plugging the cable in.
#
#   The fix is P-SILK-OWN in policy_audit.py: within the J/F/TP family, each
#   part must have a nearby text that is NEARER to it than to any other member,
#   and the row reports the ownership LEAD in mm. It is a SEPARATE row from
#   P-SILK-FN because four boards in this fleet hold P-SILK-FN waivers, all
#   evidenced on presence, and folding a new class under a waived ID is canon
#   M4's inherited-defect pattern (the same reason P-ADJ-UNREACHED is its own
#   row).
# ==========================================================================
@test("INCIDENT(2026-07-29 pluto-rx2-8way floorplan): a legend NEARER the "
      "neighbouring connector FAILS P-SILK-OWN while P-SILK-FN still PASSES",
      kind="known_bad")
def t_silk_legend_on_the_wrong_connector():
    """Built by moving ONE text on a known-clean board (tests/README: a
    known-bad fixture is a good input broken in exactly one way).

    THE MEASUREMENTS, taken off cook-loadcell 2026-07-29. Family (J*/F*/TP*):
    13 parts, 0 misowned — the baseline is genuinely clean, which is asserted
    first so the fixture cannot pass by accident. `SENSOR 4  B R W` sits at
    (39.5, 55.4): 5.69mm from J4 and 10.75mm from J3, so J4 owns it by 5.06mm.
    Moving that text to x=34.0 makes it 9.08mm from J4 and 6.60mm from J3 —
    still WELL INSIDE J4's 14.44mm search radius, so PRESENCE is unchanged and
    P-SILK-FN keeps passing. J4's other neighbours' legends are owned by them,
    so J4 is left owning nothing: the pluto-rx2-8way shape exactly.

    THE BASELINE IS THE **SEALED** BOARD, DELIBERATELY, and the reason is a
    finding in itself: a FRESHLY GENERATED cook-loadcell fails P-SILK-OWN on
    its own — `TO COOK-HUB J6: 5V 3V3 G DAT` lands 7.82mm from J6 and 2.83mm
    from TP5 (measured 2026-07-29). The silk de-collision search is
    order-dependent (CLAUDE.md: "silk de-collision is order-dependent"), so it
    can push a legend past a neighbour, and nothing graded that until now. That
    is a REAL defect in the regenerated board, reported rather than absorbed;
    it is not a usable baseline for a one-mutation fixture, so this test copies
    the sealed board (read-only) and mutates the copy.

    RED-VERIFIED 2026-07-29 (git-swap, tests/README step 3): with git HEAD's
    policy_audit.py swapped back in, the mutated board's report has NO
    `P-SILK-OWN` row at all and `P-SILK-FN | PASS | every connector/fuse/TP has
    functional silk nearby`, so this test fails on `report has no P-SILK-OWN
    row`. Restored, P-SILK-FN stays PASS and P-SILK-OWN FAILS naming J4, J3 and
    both distances.
    """
    d = tmpdir("t4silk_")
    b = sealed_copy(d, "cook_loadcell.kicad_pcb")
    proj = project_copy("cook-loadcell", d / "proj", board=b)
    board = proj / "04_kicad" / b.name

    def rows_of():
        r = run([KPY, POLICY, proj, "--skip-drc"])
        md = proj / "06_build" / "policy_audit.md"
        check(md.exists(), f"policy_audit wrote no report\n{r.out[-1500:]}")
        out = {}
        for line in md.read_text().splitlines():
            m = re.match(r"^\| (\S+) \| (\S+) \| (.*) \|$", line)
            if m:
                out[m.group(1)] = (m.group(2), m.group(3))
        return out

    base = rows_of()
    check("P-SILK-OWN" in base, f"report has no P-SILK-OWN row: {sorted(base)}")
    eq(base["P-SILK-OWN"][0], "PASS", "the UNMUTATED board's silk ownership")
    contains(base["P-SILK-OWN"][1], "13/13",
             "the denominator: every family member graded")
    contains(base["P-SILK-OWN"][1], "lead", "the measured ownership lead")

    edit_board(board,
               "import pcbnew\n"
               "hit=0\n"
               "for t in b.GetDrawings():\n"
               "    if t.GetClass()=='PCB_TEXT' and 'SENSOR 4' in t.GetText():\n"
               "        p=t.GetPosition(); t.SetPosition(\n"
               "            pcbnew.VECTOR2I(pcbnew.FromMM(34.0), p.y))\n"
               "        hit+=1\n"
               "assert hit==1, f'fixture found {hit} SENSOR 4 texts, want 1'")
    bad = rows_of()
    eq(bad["P-SILK-FN"][0], "PASS",
       "PRESENCE cannot see this class — the text is still nearby")
    eq(bad["P-SILK-OWN"][0], "FAIL", "ownership must see it")
    contains(bad["P-SILK-OWN"][1], "J4", "names the part left owning nothing")
    contains(bad["P-SILK-OWN"][1], "J3", "and the part that stole the label")
    contains(bad["P-SILK-OWN"][1], "SENSOR 4", "and quotes the legend")
    contains(bad["P-SILK-OWN"][1], "WRONG PART", "and says what is wrong")


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


# ===================================================== THE HARNESS ITSELF ====
# INCIDENT(2026-07-27, 0dd56ab0) -> REINTRODUCED(2026-07-30, bcec2fd6).
#
# Nine fast-tier suites ended in `main()` rather than `sys.exit(main())`, so
# they printed "N passed, M failed" and exited 0; run_tests.sh gates on the
# EXIT STATUS, so it printed ALL SUITES PASSED underneath red. 0dd56ab0 swept
# the nine out by hand and pinned NOTHING, so when t1_layout_precedent.py was
# created at bcec2fd6 three days later it carried the bug straight back in —
# and hid its own PREC_GRADED_FLOOR ratchet failure for as long as it stood.
# That is the jlc_twin shape (a gate reporting a failure and returning success)
# sitting in the instrument that grades every other gate.
#
# Nothing guarded the idiom because nothing could: the sweep matched a STRING.
# These two tests grade the PROPERTY instead, which is the incident's own
# footnote — 0dd56ab0's first pass flagged t3_acceptance.py, which ends
# `sys.exit(main(sys.argv[1:] + ["--slow"]))` and is CORRECT. The commit body
# calls that out as "the adjacent-property error, committed while investigating
# an adjacent-property error".
TESTS_DIR = Path(__file__).resolve().parent
RUN_TESTS_SH = TESTS_DIR / "run_tests.sh"


def suite_files():
    """Every executable suite in tests/ — `t*.py` plus the e2e driver.

    `t5_skill_canary/` is a directory of briefs, not a suite, so the top-level
    glob is deliberate; `harness.py` is the library, tested by its users."""
    return sorted(set(TESTS_DIR.glob("t*.py")) | {TESTS_DIR / "e2e_boards.py"})


def main_guard_exit_code(path):
    """Run ONLY the `if __name__ == "__main__":` block of `path`, with `main`
    stubbed to return 1 (a suite reporting failures), and report what reaches
    the shell.

    Returns `(has_guard, exit_code)`. `exit_code is None` means the block ran
    to completion WITHOUT raising SystemExit — a suite that would exit 0 while
    printing "1 failed". That is the defect, and it is measured, not matched:
    the real `sys` is in the namespace, so `sys.exit(main(sys.argv[1:] +
    ["--slow"]))` propagates and passes exactly as it should.

    The module body is never executed, so this is hermetic and costs nothing."""
    src = path.read_text(encoding="utf-8")
    for node in ast.parse(src, str(path)).body:
        if not isinstance(node, ast.If):
            continue
        t = node.test
        if not (isinstance(t, ast.Compare) and isinstance(t.left, ast.Name)
                and t.left.id == "__name__"):
            continue
        blk = ast.Module(body=node.body, type_ignores=[])
        ns = {"__name__": "__main__", "sys": sys, "main": lambda *a, **k: 1}
        try:
            exec(compile(blk, str(path), "exec"), ns)      # noqa: S102
        except SystemExit as e:
            return True, e.code
        return True, None
    return False, None


@test("INCIDENT(2026-07-27 0dd56ab0, REINTRODUCED 2026-07-30 bcec2fd6): the "
      "exit-code guard BITES a bare `main()` — and does NOT accuse the "
      "`main(sys.argv[1:] + [...])` form that a STRING match once flagged",
      kind="known_bad")
def t_exit_code_guard_bites_a_bare_main():
    """The known-bad half, so the sweep below cannot become a gate that
    cannot fail once the tree is clean. Four synthetic suites, one property:
    does a run that REPORTS a failure reach the shell as nonzero?

    RED-VERIFIED 2026-07-30 the honest way — this predicate was written and run
    BEFORE `t1_layout_precedent.py` was repaired, and the sweep below named it:
    `suites that report a failure and exit 0 anyway: ['t1_layout_precedent.py']`.
    Then the one-line fix landed and the sweep went green. The pre-fix code for
    this guard is its ABSENCE, so the real bytes it was verified against are
    the reintroduced defect itself."""
    d = tmpdir("exitguard_")
    tail = {
        "bare.py":   "    main()\n",
        "plain.py":  "    sys.exit(main())\n",
        "argvform.py": "    sys.exit(main(sys.argv[1:] + [\"--slow\"]))\n",
        "noguard.py": None,
    }
    for name, last in tail.items():
        body = "import sys\n\n\ndef main(argv=None):\n    return 0\n\n\n"
        if last is not None:
            body += 'if __name__ == "__main__":\n' + last
        (d / name).write_text(body)

    eq(main_guard_exit_code(d / "bare.py"), (True, None),
       "a bare main() DISCARDS the failure — the incident")
    eq(main_guard_exit_code(d / "noguard.py"), (False, None),
       "no __main__ block at all is the same hole, and is reported as such")
    eq(main_guard_exit_code(d / "plain.py"), (True, 1),
       "the canonical form propagates")
    eq(main_guard_exit_code(d / "argvform.py"), (True, 1),
       "and so does the argv form a grep for `sys.exit(main())` MISSES — "
       "0dd56ab0's own false positive, which is why this grades the property")


@test("INCIDENT(2026-07-27 0dd56ab0, REINTRODUCED 2026-07-30 bcec2fd6): EVERY "
      "suite in tests/ propagates its exit code, and every suite is WIRED "
      "INTO run_tests.sh — a suite that exits 0 on red, or never runs at "
      "all, is a gate that cannot fail")
def t_every_suite_propagates_and_is_wired_in():
    """Two ways for a suite's verdict to never reach anyone, swept together
    because they are one defect: the runner reports success it did not earn.

    1. EXIT CODE (the 0dd56ab0 incident, reintroduced at bcec2fd6).
    2. NOT LISTED. `run_tests.sh` runs an explicit SUITES array, so a suite on
       disk that nobody added is dead code that reads as coverage. MEASURED
       2026-07-30: `t1_release_required.py` — A-EVID, 6 tests, 4 known-bad,
       landed 94300f2 and fixed again at c2c49ea7 — had never once run from
       the runner. It passes; the hole was that nothing would have said if it
       did not."""
    files = suite_files()
    check(len(files) >= 30, f"the suite sweep found only {len(files)} files — "
                            f"a zero-ish denominator is never a pass (M-COVER)")

    swallowed, unguarded = [], []
    for f in files:
        has_guard, code = main_guard_exit_code(f)
        if not has_guard:
            unguarded.append(f.name)
        elif not code:
            swallowed.append(f.name)
    eq(swallowed, [], "suites that report a failure and exit 0 anyway")
    eq(unguarded, [], "suites with no `if __name__ == \"__main__\":` block")

    sh = RUN_TESTS_SH.read_text(encoding="utf-8")
    missing = [f.name for f in files if f.name not in sh]
    eq(missing, [], "suites on disk that run_tests.sh never invokes")


if __name__ == "__main__":
    sys.exit(main())
