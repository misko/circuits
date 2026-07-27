#!/usr/bin/env python3
"""F-PAYLOAD: the shipped zip is a GRADED artifact, not merely a hashed one.

usb-hub-3s-v3 shipped v1.6, v1.7 and v1.8 with NO COPPER POUR on any layer —
44287.91 mm2 of missing copper — and every gate was green, because
`kicad-cli pcb drc --refill-zones` refills the zones IN MEMORY and therefore
returns 0/0/0 on a board whose saved file has no fill. Nothing in this repo had
ever opened the zip that becomes copper.

RED-VERIFICATION. Two bugs were found in `fab_payload_census.py` DURING its own
development, both by running it against the fleet, and both are the repo's
signature adjacent-property error. Each has a named test below that goes RED
against the pre-fix code:

  * `t_keepout_zones_are_not_pours` — the first draft counted KEEPOUT/rule-area
    zones as pours and so reported crow-recorder-central-v2's In2.Cu and In3.Cu
    (0 pours, 6 keepouts each) as shipping bare. A false P0 on a good board.
  * `t_zone_token_is_not_a_prefix` — `text.find("(zone")` prefix-matches
    `(zone_connect 2)`; on crow-recorder that admitted 64 phantom zones.

The real sealed releases are used as fixtures where the incident IS the
fixture — v1.8 is a permanent, immutable, honest known-bad this project already
paid for, and it can never silently "get fixed" out from under the test.
"""
import subprocess
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, ROOT, check, contains, main, must_fail,  # noqa: E402
                     must_pass, not_contains, run, test, tmpdir)

TOOL = ROOT / "skills/jlcpcb-fab/scripts/fab_payload_census.py"

V18 = ROOT / "projects/usb-hub-3s-v3/07_releases/v1.8-2026-07-26"
CRV2 = (ROOT / "projects/crow-recorder-central-v2/07_releases"
        / "crow-recorder-central-v2-v1.5-2026-07-25")
INTERP = (ROOT / "projects/smc0985-cooksense/07_releases"
          / "interposer-v1.0-2026-07-24")

GERBER_HEAD = "%TF.FileFunction,{func}*%\n%FSLAX46Y46*%\n%MOMM*%\n"
REGION = "G36*\nX0Y0D02*\nX1000Y0D01*\nX1000Y1000D01*\nG37*\n"


def _zip(dirpath, stem, layers):
    """layers: {suffix: (FileFunction, n_regions)} -> a minimal gerber zip."""
    fab = dirpath / "fab"
    fab.mkdir(parents=True, exist_ok=True)
    zp = fab / f"{stem}_gerbers.zip"
    with zipfile.ZipFile(zp, "w") as z:
        for suf, (func, n) in layers.items():
            body = GERBER_HEAD.format(func=func) + REGION * n + "M02*\n"
            z.writestr(f"{stem}-{suf}.gbr", body)
    return zp


def _board(dirpath, stem, zones):
    """zones: list of (layer, is_keepout) -> a minimal .kicad_pcb."""
    src = dirpath / "source"
    src.mkdir(parents=True, exist_ok=True)
    body = ['(kicad_pcb (version 20240108)']
    for layer, ko in zones:
        ko_s = '(keepout (tracks not_allowed) (pads not_allowed))' if ko else ''
        body.append(f'  (zone (net 0) (layers "{layer}") {ko_s} '
                    f'(polygon (pts (xy 0 0) (xy 10 0) (xy 10 10))))')
    body.append('  (zone_connect 2)')       # the prefix-match trap, verbatim
    body.append(')')
    p = src / f"{stem}.kicad_pcb"
    p.write_text("\n".join(body))
    return p


def _fixture(zones, layers, stem="fx"):
    d = tmpdir("fpay_")
    _board(d, stem, zones)
    _zip(d, stem, layers)
    return d


# ---------------------------------------------------------------- the incident

@test("fpay_v18_zero_pour_is_caught", kind="known_bad")
def t_v18_zero_pour_is_caught():
    """THE INCIDENT. usb-hub v1.8 must FAIL — 4 copper layers, 0 G36 each."""
    r = must_fail(run([KPY, TOOL, V18]), "F-PAYLOAD on usb-hub v1.8")
    for lay in ("F.Cu", "B.Cu", "In1.Cu", "In2.Cu"):
        contains(r.out, f"F-POUR {lay}", "per-layer finding")
    contains(r.out, "NO POUR", "verdict names the property")


@test("fpay_v18_identical_planes_are_caught", kind="known_bad")
def t_v18_identical_planes_are_caught():
    """F-IDENT: an L2 GND plane and an L3 VIN plane cannot be the same bytes."""
    r = must_fail(run([KPY, TOOL, V18]), "F-IDENT on usb-hub v1.8")
    contains(r.out, "F-IDENT", "F-IDENT fires")
    contains(r.out, "18921B", "the measured size is reported")


@test("fpay_good_release_passes")
def t_good_release_passes():
    """crow-recorder v1.5 ships real pour and must PASS — the gate must not
    simply fail everything, which is how a gate 'catches' without discriminating."""
    r = must_pass(run([KPY, TOOL, CRV2]), "F-PAYLOAD on crow-recorder v1.5")
    contains(r.out, "F-POUR F.Cu 4 zone(s) -> 104 G36", "measured pour census")


# ------------------------------------------------- the two self-inflicted bugs

@test("fpay_keepout_zones_are_not_pours", kind="known_bad")
def t_keepout_zones_are_not_pours():
    """RED against the pre-fix code, which counted keepouts as pours.

    A layer holding ONLY rule areas legitimately has 0 regions. The first draft
    of this checker reported crow-recorder's In2.Cu/In3.Cu (0 pours, 6 keepouts)
    as shipping bare — a false P0 on a good board. Verified RED by removing the
    `if "(keepout" in blk: continue` guard: this fixture then FAILS.
    """
    d = _fixture(zones=[("F.Cu", False), ("In2.Cu", True), ("In2.Cu", True)],
                 layers={"F_Cu": ("Copper,L1,Top", 2),
                         "In2_Cu": ("Copper,L3,Inr", 0)})
    r = must_pass(run([KPY, TOOL, d]), "keepout-only layer with 0 regions")
    not_contains(r.out, "NO POUR", "keepout-only layer must not be flagged")
    contains(r.out, "F-POUR F.Cu 1 zone(s) -> 2 G36", "the real pour is still graded")


@test("fpay_zone_token_is_not_a_prefix")
def t_zone_token_is_not_a_prefix():
    """A REGRESSION GUARD, not a known-bad — and the distinction is the point.

    `text.find("(zone")` prefix-matches `(zone_connect 2)`, and on
    crow-recorder-central-v2 that admitted 64 phantom blocks. The token-boundary
    guard in `sexp_blocks` is correct and is kept.

    BUT IT IS NOT LOAD-BEARING, and this test does NOT prove it is. RED
    verification was attempted and FAILED TO GO RED: with the guard removed this
    fixture still passes, because a `(zone_connect 2)` block carries no
    `(layers ...)` declaration and is therefore already discarded by
    `if not m: continue`. The 64 phantoms were admitted and then harmlessly
    dropped; they never skewed the census.

    Claiming this as a known-bad would be a gate asserting a discrimination it
    does not have — the exact defect this suite exists to prevent. It is
    labelled `clean` and the overclaim is recorded here instead of being quietly
    dropped.
    """
    d = _fixture(zones=[("F.Cu", False)], layers={"F_Cu": ("Copper,L1,Top", 3)})
    r = must_pass(run([KPY, TOOL, d]), "board containing (zone_connect 2)")
    contains(r.out, "F-POUR F.Cu 1 zone(s) -> 3 G36", "exactly one real zone counted")


# --------------------------------------------------------- discrimination both ways

@test("fpay_pour_declared_but_absent_fails", kind="known_bad")
def t_pour_declared_but_absent_fails():
    d = _fixture(zones=[("F.Cu", False)], layers={"F_Cu": ("Copper,L1,Top", 0)})
    must_fail(run([KPY, TOOL, d]), "1 pour zone, 0 regions", expect="NO POUR")


@test("fpay_regions_without_a_zone_fails", kind="known_bad")
def t_regions_without_a_zone_fails():
    """The reverse error: copper in the payload the board never declared."""
    d = _fixture(zones=[], layers={"F_Cu": ("Copper,L1,Top", 5)})
    must_fail(run([KPY, TOOL, d]), "regions with no zone",
              expect="declares no zone on this layer")


# ------------------------------------------------------------ pourless is DECLARED

@test("fpay_pourless_undeclared_fails", kind="known_bad")
def t_pourless_undeclared_fails():
    """A deliberately pourless board and one that LOST its zones are the same
    bytes. The interposer is genuinely pourless and must still fail undeclared."""
    must_fail(run([KPY, TOOL, INTERP]), "undeclared pourless board",
              expect="nothing declares it pourless")


@test("fpay_pourless_declared_with_reason_passes")
def t_pourless_declared_with_reason_passes():
    d = tmpdir("fpay_pl_")
    a = d / "assembly.yaml"
    a.write_text('pourless: "keypad domain floats; BRIEF S4/S7 forbid a plane"\n')
    r = must_pass(run([KPY, TOOL, INTERP, "--assembly", a]),
                  "declared pourless with a reason")
    contains(r.out, "pourless by declaration", "the reason is echoed")


@test("fpay_pourless_without_reason_is_refused", kind="known_bad")
def t_pourless_without_reason_is_refused():
    """Canon: a waiver needs EVIDENCE, not assertion. `pourless: true` is a
    rationale-free waiver and must be refused."""
    d = tmpdir("fpay_pl2_")
    a = d / "assembly.yaml"
    a.write_text("pourless: true\n")
    must_fail(run([KPY, TOOL, INTERP, "--assembly", a]),
              "bare `pourless: true`", expect="NO REASON")


# ------------------------------------------------------------------- coverage

@test("fpay_emits_a_coverage_denominator")
def t_emits_a_coverage_denominator():
    """Canon G-COVER: a verdict without a denominator hides its own blind spot."""
    r = must_pass(run([KPY, TOOL, CRV2]), "F-PAYLOAD on a good release")
    contains(r.out, "coverage F-POUR:", "F-POUR declares coverage")
    contains(r.out, "coverage F-IDENT:", "F-IDENT declares coverage")


@test("fpay_unclassifiable_copper_layer_fails", kind="known_bad")
def t_unclassifiable_copper_layer_fails():
    """NEVER SILENTLY SKIP. A copper gerber this parser cannot map to a board
    layer is a FAIL — `row_kind` printed PASS while dropping 12 of 26 rows."""
    d = _fixture(zones=[("F.Cu", False)],
                 layers={"F_Cu": ("Copper,L1,Top", 2),
                         "Weird_Cu": ("Copper,L9,Inr", 1)})
    must_fail(run([KPY, TOOL, d]), "unclassifiable copper layer",
              expect="F-LAYER")


if __name__ == "__main__":
    sys.exit(main())
