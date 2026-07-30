#!/usr/bin/env python3
"""T2: tier_preflight.py — the 'tool config == declared fab tier' route gate.

Provenance: crow-recorder-central-v2 (2026-07-23) burned ~60% of its routing
stage on four config-vs-tier defects (01_docs journal, routing): the
generate_rules 0.2mm clearance hardcode (500+158 phantom findings), F/B-only
via-site checking (200 shorting + 501 clearance), normalize_vias' 0.6/0.3
fallback (323/323 tier vias resized), and try_via's hole_to_copper=0.205
default vs the 0.15 board floor (a FALSE placement wall — 7 of 8 "stuck"
pads had legal sites). Each known-bad fixture below reproduces one of those
classes as CONFIG and asserts the gate REFUSES it with the named check and a
computed copy-paste fix.

RED evidence: this is a NEW gate, so red == every known_bad fixture here
fails it by construction (the harness counts them). The route-entry wiring
is red-verified structurally: `t_route_wiring_refuses` proves cmd_route dies
at the preflight BEFORE its old first failure point ("r0 missing"), and
`t_skip_preflight_hatch` shows the identical command reaching that old
failure point when the gate is bypassed — i.e. exactly the pre-wiring
behavior, which is what an unwired cmd_route would do on the broken config.

Everything is hermetic: fixtures are scratch project trees; the board file
is a minimal .kicad_pcb TEXT (the preflight parses the layer table as text,
no pcbnew) and no real project is written.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, ROOT, SCRIPTS, check, contains, main,  # noqa: E402
                     must_fail, must_pass, not_contains, run, test, tmpdir)

TP = SCRIPTS / "tier_preflight.py"
RS = SCRIPTS / "route_and_stitch_generic.py"


def board_text(layers=6):
    names = ["F.Cu"] + [f"In{i}.Cu" for i in range(1, layers - 1)] + ["B.Cu"]
    rows = "\n".join(f'\t\t({i * 2} "{n}" signal)'
                     for i, n in enumerate(names))
    return ("(kicad_pcb\n\t(version 20240108)\n\t(generator \"t2\")\n"
            f"\t(layers\n{rows}\n\t)\n)\n")


def scratch(mut_route=None, mut_nets=None, mut_fp=None, layers=6,
            hole_clr=0.15, with_nets=True):
    """A tier-CONSISTENT jlc_6layer_smallvia project tree (mirrors the fixed
    crow-rv2 values). Known-bad fixtures are this GOOD tree broken in
    exactly one way (tests/README.md discipline)."""
    import yaml
    d = tmpdir("t2tp_")
    (d / "03_src" / "rules").mkdir(parents=True)
    (d / "04_kicad").mkdir()
    (d / "04_kicad" / "x.kicad_pcb").write_text(board_text(layers))
    (d / "04_kicad" / "x.kicad_pro").write_text(json.dumps(
        {"board": {"design_settings": {"rules":
                                       {"min_hole_clearance": hole_clr}}}}))
    route = {
        "project": {"name": "x", "board": "04_kicad/x.kicad_pcb"},
        "route": {
            "common": {"layers": ["F.Cu", "In2.Cu", "In3.Cu", "B.Cu"],
                       "clearance": 0.10},
            "waves": [{"name": "sig", "nets": ["A"]}],
        },
        "stitch": {
            "clearance": 0.10,
            "via": {"spacing": 0.6, "pth_margin": 0.3,
                    "tiers": [{"size": 0.30, "drill": 0.15,
                               "hole_to_copper": 0.155}]},
            "passes": ["normalize_vias", "hole_to_hole", "pad_rescue",
                       "island_rescue", "fill", "gate"],
            "normalize_vias": {"size": 0.30, "drill": 0.15,
                               "below_width": 0.29},
            "hole_to_hole": {"min_gap": 0.2},
            "pad_rescue": {"nets": [{"net": "GND", "layer": "In1.Cu"},
                                    {"net": "GND", "layer": "In4.Cu"}]},
            "island_rescue": {"layers": ["F.Cu", "In1.Cu", "In4.Cu",
                                         "B.Cu"]},
        },
    }
    nets = {"fab_tier": "jlc_6layer_smallvia",
            "default_clearance": "0.10mm",
            "classes": {"PWR": {"min_width": "0.4mm", "clearance": "0.10mm",
                                "nets": ["A"]}}}
    fp = {"project": {"output": "04_kicad/x.kicad_pcb"},
          "board": {"layers": layers},
          "placement": {"legalize": {"clearance": 0.45}},
          "design_rules": {"hole_clearance": hole_clr}}
    if mut_route:
        mut_route(route)
    if mut_nets:
        mut_nets(nets)
    if mut_fp:
        mut_fp(fp)
    (d / "03_src" / "route.yaml").write_text(yaml.safe_dump(route))
    if with_nets:
        (d / "03_src" / "rules" / "nets.yaml").write_text(
            yaml.safe_dump(nets))
    (d / "03_src" / "floorplan.yaml").write_text(yaml.safe_dump(fp))
    return d


def preflight(d, *extra):
    return run([KPY, TP, d, *extra])


# ------------------------------------------------------------------ clean
@test("tier_preflight passes a tier-consistent 6L small-via config")
def t_pass():
    r = must_pass(preflight(scratch()), "consistent config")
    contains(r.out, "0 FAIL / 0 WARN", "verdict")
    contains(r.out, "jlc_6layer_smallvia", "tier named")


@test("tier_preflight --explain prints the derivation behind each check")
def t_explain():
    r = must_pass(preflight(scratch(), "--explain"), "explain mode")
    contains(r.out, "derivations:", "derivation block")
    contains(r.out, "hole floor 0.15", "hole-floor derivation")
    contains(r.out, "copper stack", "layer-stack derivation")


@test("tier_preflight is a no-op on a board with no declared fab_tier "
      "(legacy behavior preserved)")
def t_no_tier():
    d = scratch(with_nets=False)
    r = must_pass(preflight(d), "no-tier project")
    contains(r.out, "no fab_tier declared", "legacy note")


# -------------------------------------------------------------- known bad
@test("PF-HTC FAILS the crow-rv2 case: tiers without hole_to_copper on a "
      "0.15 hole-floor board (0.205 default = FALSE placement wall)",
      kind="known_bad")
def t_htc_crow():
    """THE incident (2026-07-23): try_via built its via tier as {size,drill}
    only, via_site_ok fell back to 0.205, 0.055mm stricter than the board's
    0.15 hole_clearance floor. 7 of 8 'unstitchable' GND pads had DRC-legal
    sites 0.2-0.8mm away; misdiagnosed as a placement D-BACK."""
    d = scratch(mut_route=lambda r: r["stitch"]["via"]["tiers"][0].pop(
        "hole_to_copper"))
    r = must_fail(preflight(d), "crow htc case", "PF-HTC")
    contains(r.out, "FALSE placement wall", "defect named")
    contains(r.out, "0.155", "computed tier-correct value (0.15 + 5um)")


@test("PF-HTC FAILS an explicit hole_to_copper below the board hole floor",
      kind="known_bad")
def t_htc_explicit_underfloor():
    d = scratch(mut_route=lambda r: r["stitch"]["via"]["tiers"][0].update(
        {"hole_to_copper": 0.10}))
    r = must_fail(preflight(d), "explicit sub-floor htc", "PF-HTC")
    contains(r.out, "DRC hole_clearance check rejects", "direction named")


@test("PF-LAYER FAILS wrong via-site/rescue layer coverage: island_rescue "
      "blind to a declared In4.Cu plane", kind="known_bad")
def t_layer_cover():
    """Config twin of crow-rv2 defect 2 (F/B-only via_site_ok, 200 shorting
    + 501 clearance): a rescue pass scanning fewer layers than the board's
    planes strands those planes' pads invisibly."""
    d = scratch(mut_route=lambda r: r["stitch"]["island_rescue"].update(
        {"layers": ["F.Cu", "B.Cu"]}))
    r = must_fail(preflight(d), "plane not covered", "PF-LAYER")
    contains(r.out, "In1.Cu", "missing plane layer named")
    contains(r.out, "fix:", "computed union printed")


@test("PF-LAYER FAILS a config naming a copper layer the board lacks "
      "(In3.Cu routing on a 4-layer board)", kind="known_bad")
def t_layer_exist():
    def fix4(route):
        route["stitch"]["pad_rescue"]["nets"] = [
            {"net": "GND", "layer": "In1.Cu"}]
        route["stitch"]["island_rescue"]["layers"] = ["F.Cu", "In1.Cu",
                                                      "B.Cu"]
    d = scratch(layers=4, mut_route=fix4)
    r = must_fail(preflight(d), "In3.Cu on 4 layers", "PF-LAYER")
    contains(r.out, "'In3.Cu'", "offending layer named")


@test("PF-RULES-CLR FAILS classes riding the generate_rules 0.2 clearance "
      "hardcode while the router routes tighter (crow defect 1)",
      kind="known_bad")
def t_rules_hardcode():
    """crow-rv2 2026-07-23: every class rode an unexamined hardcoded 0.2mm
    while KRT routed at 0.13 -> 500 then 158 phantom clearance findings."""
    def strip(nets):
        nets.pop("default_clearance")
        nets["classes"]["PWR"].pop("clearance")
    d = scratch(mut_nets=strip)
    r = must_fail(preflight(d), "hardcoded DRC clearance", "PF-RULES-CLR")
    contains(r.out, "HARDCODED 0.2", "hardcode named")
    contains(r.out, "default_clearance: 0.1", "computed explicit value")


@test("PF-ROUTE-CLR FAILS a router clearance below the explicit DRC "
      "clearance", kind="known_bad")
def t_route_clr():
    d = scratch(mut_route=lambda r: r["route"]["common"].update(
        {"clearance": 0.13}),
        mut_nets=lambda n: (n.update({"default_clearance": "0.2mm"}),
                            n["classes"]["PWR"].update(
                                {"clearance": "0.2mm"})))
    r = must_fail(preflight(d), "router under DRC clearance", "PF-ROUTE-CLR")
    contains(r.out, "0.13", "effective router clearance")
    contains(r.out, "0.2", "DRC clearance")


@test("PF-NORM FAILS normalize_vias riding its 0.6/0.3 fallback on a "
      "0.30-via tier (crow defect 3: 323/323 vias resized)",
      kind="known_bad")
def t_normalize_default():
    d = scratch(mut_route=lambda r: r["stitch"].update(
        {"normalize_vias": {}}))
    r = must_fail(preflight(d), "normalize_vias fallback", "PF-NORM")
    contains(r.out, "323/323", "measured incident cited")
    contains(r.out, "below_width: 0.29", "computed tier-correct block")


@test("PF-VIA-FLOOR FAILS an explicit via size below the tier floor",
      kind="known_bad")
def t_via_floor():
    d = scratch(mut_route=lambda r: r["route"]["common"].update(
        {"via_size": 0.25, "via_drill": 0.15}))
    r = must_fail(preflight(d), "sub-floor via", "PF-VIA-FLOOR")
    contains(r.out, "route.common.via_size", "param named")


@test("PF-H2H FAILS a hole_to_hole repair gap below the tier floor",
      kind="known_bad")
def t_h2h():
    d = scratch(mut_route=lambda r: r["stitch"]["hole_to_hole"].update(
        {"min_gap": 0.15}))
    must_fail(preflight(d), "sub-floor h2h", "PF-H2H")


@test("PF-VIASITE FAILS a pcb_toolkit whose via_site_ok regressed to a "
      "hardcoded F/B layer pair (crow defect 2, code side)",
      kind="known_bad")
def t_viasite_regressed():
    d = scratch()
    bad = d / "pcb_toolkit_old.py"
    # the PRE-60f0a13 shape: layers default hardcoded to the outer pair
    bad.write_text(
        "class Toolkit:\n"
        "    def via_site_ok(self, x, y, netcode, size=0.45, drill=0.2,\n"
        "                    hole_to_copper=0.205,\n"
        "                    layers=(pcbnew.F_Cu, pcbnew.B_Cu)):\n"
        "        for lay in layers:\n"
        "            pass\n"
        "        return True\n")
    r = must_fail(preflight(d, "--toolkit", bad), "regressed toolkit",
                  "PF-VIASITE")
    contains(r.out, "200 shorting", "measured incident cited")


@test("a typo'd fab_tier is a HARD preflight failure, never a silent skip",
      kind="known_bad")
def t_tier_typo():
    d = scratch(mut_nets=lambda n: n.update({"fab_tier": "jlc_9layer_nope"}))
    must_fail(preflight(d), "tier typo", "fab_tier")


@test("PF-KRT FAILS a route.common.fab_tier outside KRT's {standard,advanced} "
      "— the PIPELINE tier name copied into a KRT-preset slot", kind="known_bad")
def t_krt_preset_not_a_krt_choice():
    """MEASURED, pluto-rx2-8way 2026-07-29. `route.common.fab_tier` was
    `jlc_4layer_advanced` — the board's real, correct PIPELINE tier
    (fab_tiers.yaml), one level down in a slot that means KRT's own
    `--fab-tier` PRESET, whose argparse `choices` are exactly
    {standard, advanced}. route.py exited 2 on the FIRST wave, so nothing
    routed at all — while this gate printed
    `tier preflight: 0 FAIL / 0 WARN — config is tier-consistent` over it.

    The pre-fix check read the value ONLY to compare it to the literal
    'advanced' and `return`ed silently on anything else: a gate that passed a
    value it never validated. RED-VERIFIED against the pre-fix
    `check_krt_preset` (swap `if preset != "advanced": return` back to the top
    and drop the choices test): this fixture exits 0 with
    `0 FAIL / 0 WARN — config is tier-consistent`, measured 2026-07-29."""
    d = scratch(mut_route=lambda r: r["route"]["common"].update(
        {"fab_tier": "jlc_6layer_smallvia"}))
    r = must_fail(preflight(d), "pipeline tier name in the KRT preset slot",
                  "PF-KRT")
    contains(r.out, "not one of KRT's --fab-tier choices", "the reason")
    contains(r.out, "['standard', 'advanced']", "the legal set is printed")
    contains(r.out, "PIPELINE tier name", "and the confusion is named")
    contains(r.out, "exits 2", "with the measured consequence")
    contains(r.out, "fix: route.common.fab_tier: advanced", "a copy-paste fix")
    not_contains(r.out, "config is tier-consistent",
                 "the verdict line must NOT claim consistency")


@test("PF-KRT PASSES the legal 'advanced' preset when fab_overrides pins the "
      "tier via floor, and both legal choices are accepted")
def t_krt_preset_legal_values():
    """The other side of the known-bad above: `advanced` is a legal KRT choice
    and must not be blocked by the new validation. It still WARNs unpinned (the
    crow-rv2 0.25-via escalation), so the pinned form is the clean case."""
    d = scratch(mut_route=lambda r: r["route"]["common"].update(
        {"fab_tier": "advanced", "fab_overrides": "/tmp/ov.txt"}))
    r = must_pass(preflight(d, "--explain"), "advanced + pinned overrides")
    contains(r.out, "0 FAIL / 0 WARN", "clean verdict")
    contains(r.out, "argparse-legal", "the derivation records the check ran")
    d2 = scratch(mut_route=lambda r: r["route"]["common"].update(
        {"fab_tier": "standard"}))
    r2 = must_pass(preflight(d2), "standard preset")
    contains(r2.out, "0 FAIL", "standard is legal too")
    # and an unpinned 'advanced' is still the crow-rv2 WARN, not a FAIL
    d3 = scratch(mut_route=lambda r: r["route"]["common"].update(
        {"fab_tier": "advanced"}))
    r3 = must_pass(preflight(d3), "advanced unpinned")
    contains(r3.out, "WARN route.common.fab_tier",
             "the pre-existing PF-KRT WARN is preserved")
    contains(r3.out, "33 vias at 0.25mm", "with its measured incident")


def _wave_clearance_scratch():
    """pluto-rx2-8way's shape, minimised: the board declares its clearance UP
    (0.2mm = ISOLATION, not a routability tax) everywhere a reader looks —
    route.common, both netclasses, stitch — and then ONE wave overrides it
    down to 0.14 to get the RF launch out of a QFN land."""
    return scratch(
        mut_route=lambda r: (
            r["route"]["common"].update({"clearance": 0.2}),
            r["route"]["waves"].__setitem__(
                0, {"name": "rf", "nets": ["A"], "clearance": 0.14}),
            r["stitch"].update({"clearance": 0.2})),
        mut_nets=lambda n: (n.update({"default_clearance": "0.2mm"}),
                            n["classes"]["PWR"].update({"clearance": "0.2mm"})))


@test("PF-ROUTE-CLR FAILS a per-WAVE clearance override under the DRC floor — "
      "the gate must read EVERY place the value can be set, not just "
      "route.common", kind="known_bad")
def t_route_clr_per_wave():
    """MEASURED, pluto-rx2-8way 2026-07-30. `route.common.clearance: 0.2` (and
    every netclass at 0.2, and stitch at 0.2) with wave `rf` overriding
    `clearance: 0.14` to escape the PE42482A-X land. The board then routed and
    landed 49 clearance findings at 0.166..0.194mm against the 0.2 floor — the
    EXACT mismatch PF-ROUTE-CLR exists to catch, one YAML level below where it
    was looking.

    RED-VERIFIED against the pre-fix `eff_route_clearance` (which read only
    `route.common.clearance` and returned a single number): this fixture exits
    0 printing

        tier preflight: 0 FAIL / 0 WARN — config is tier-consistent

    measured 2026-07-30. Third instance of one shape on this board in three
    days: PF-KRT read `fab_tier` without validating it (t_krt_preset_* above);
    this read `clearance` without reading everywhere it can be set."""
    r = must_fail(preflight(_wave_clearance_scratch()),
                  "wave clearance under the DRC floor", "PF-ROUTE-CLR")
    contains(r.out, "route.waves[rf].clearance", "the WAVE scope is named")
    contains(r.out, "0.14", "the effective wave clearance")
    contains(r.out, "0.2", "the DRC clearance it is under")
    not_contains(r.out, "config is tier-consistent",
                 "the verdict must not claim consistency")


@test("tier_preflight grades clearance PER SCOPE: a legal common with one "
      "illegal wave names the WAVE, and the derivation lists every scope")
def t_route_clr_scopes_are_graded_separately():
    """The collapse this fix refuses: reporting one number over a config that
    has several is how the defect happened. --explain must enumerate the
    scopes, and a config whose waves all inherit must still grade exactly the
    common scope (no duplicate findings)."""
    r = must_fail(preflight(_wave_clearance_scratch(), "--explain"),
                  "per-scope grading", "PF-ROUTE-CLR")
    contains(r.out, "route clearance scopes:", "the scope list is derived")
    contains(r.out, "route.common.clearance=0.2", "common scope listed")
    contains(r.out, "route.waves[rf].clearance=0.14", "wave scope listed")
    # exactly ONE PF-ROUTE-CLR finding: the common scope is legal here
    check(r.out.count("PF-ROUTE-CLR") == 1,
          f"one finding for the one illegal scope (got "
          f"{r.out.count('PF-ROUTE-CLR')})")
    # and the clean tree (waves inherit) stays clean
    r2 = must_pass(preflight(scratch(), "--explain"), "inheriting waves")
    contains(r2.out, "0 FAIL / 0 WARN", "clean verdict")
    contains(r2.out, "route.waves[sig]: inherits", "inheritance is derived")


@test("PF-ROUTE-CLR FAILS a wave clearance below the FAB TIER floor, which "
      "no netclass can waive", kind="known_bad")
def t_route_clr_wave_under_tier():
    """A wave at 0.05 on jlc_6layer_smallvia (min_space 0.09): sub-tier copper
    is unmakeable, not merely DRC-illegal. RED-VERIFIED against the pre-fix
    code: `0 FAIL / 0 WARN — config is tier-consistent`, measured 2026-07-30."""
    d = scratch(mut_route=lambda r: r["route"]["waves"].__setitem__(
        0, {"name": "rf", "nets": ["A"], "clearance": 0.05}))
    r = must_fail(preflight(d), "sub-tier wave clearance", "PF-ROUTE-CLR")
    contains(r.out, "below fab tier", "the tier bound is named")
    contains(r.out, "route.waves[rf].clearance", "the wave scope is named")


@test("tier_preflight FAILS the frozen crow-array-pod archive "
      "(PF-RULES-CLR latent mismatch — the reason its e2e run uses "
      "--skip-preflight)", kind="known_bad")
def t_flags_archived_pod():
    """Pins the rationale in t2_route_stitch._e2e: the archived (read-only)
    pod board routes at 0.15 clearance under a hardcoded-0.2 netclass DRC
    default. It shipped 0/0/0 only because the sparse 2-layer route never
    packed to 0.2 — the mismatch is real and must stay visible."""
    pod = ROOT / "archived_projects" / "crow-array-pod"
    if not pod.is_dir():
        return  # archive layout changed; nothing to pin
    must_fail(preflight(pod), "archived pod", "PF-RULES-CLR")


# --------------------------------------------------- route-entry wiring
@test("cmd_route REFUSES to route on a preflight failure (gate runs FIRST, "
      "before any prep/KRT state is even looked at)", kind="known_bad")
def t_route_wiring_refuses():
    d = scratch(mut_route=lambda r: r["stitch"]["via"]["tiers"][0].pop(
        "hole_to_copper"))
    r = must_fail(run([KPY, RS, "route", d / "03_src" / "route.yaml"]),
                  "route on broken config", "tier preflight FAILED")
    contains(r.out, "PF-HTC", "the finding is shown to the router user")
    # gate ordering: it must die BEFORE the old first failure ("r0 missing")
    not_contains(r.out, "run `prep` first", "preflight ran first")


@test("--skip-preflight bypasses the gate LOUDLY and restores the "
      "pre-wiring behavior")
def t_skip_preflight_hatch():
    d = scratch(mut_route=lambda r: r["stitch"]["via"]["tiers"][0].pop(
        "hole_to_copper"))
    r = run([KPY, RS, "route", d / "03_src" / "route.yaml",
             "--skip-preflight"])
    contains(r.out, "WARNING: --skip-preflight", "loud warning")
    # identical command now reaches the OLD first failure point — i.e. the
    # unwired cmd_route behavior (this is the wiring test's red evidence)
    contains(r.out, "run `prep` first", "route proceeded past the gate")
    check(r.rc != 0, "still fails later (no prep ran) — but past the gate")


if __name__ == "__main__":
    sys.exit(main())
