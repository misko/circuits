#!/usr/bin/env python3
"""gate_contract_audit.py — canon G-*: a gate on the gates.

    gate_contract_audit.py [--root DIR] [--json OUT] [--enforce LIST]

WHY THIS EXISTS. `contracts_audit.py` governs FOLDERS. Nothing governed the
CHECKERS, so five of them shipped unable to fail on the property they name, and
a five-release fleet audit (2026-07-26/27) found two boards not orderable with
every gate green. Measured on this repo at the time of writing:

  * A-AMP graded **10 of 57** declared net-class currents fleet-wide. Any
    qualifier ("7 A worst case", "6 A / 5 A", "~1.5A pulsed") makes `parse_amps`
    return None, and rules_audit.py:336 then files it under OKS with the text
    "n/a (no current: declared)". ZERO net classes actually declare no current,
    so that message is wrong 100% of the times it fires. usb-hub-3s-v3 ships
    PWR_IN 7 A, PWR_RAIL 6 A and SWITCH_NODE 7 A — all silenced; the one class
    it does grade, VBUS, FAILS.
  * `bom_source_check.row_kind()` classifies by the whole leading-alpha run, so
    `RS1/RS2` (the 10 mOhm shunts setting BOTH buck current limits) and `CE1`
    (the only electrolytic, which shipped REVERSED in v1.0/v1.1) exit leg C
    while the tool prints PASS.
  * `labeled_resistance("10mOhm")` returns 1.0e7 — the multiplier is uppercased
    before lookup, so milli decodes as mega.

None of those is a bad line of code. They are one SHAPE: a checker permitted to
report success over input it did not understand.

THE THREE OBLIGATIONS. A script that prints a verdict must:

  G-INPUT   name the artifact it graded, so a reader can tell whether it read
            the SHIPPED bytes or a reconstruction (canon M6). policy_audit ran
            against a `06_build` shadow tree and reported 79 warnings where the
            sealed archive has 102; bom_source_check graded a filename that does
            not exist in the release.
  G-COVER   emit `N graded / M total`. A verdict with no denominator hides its
            own blind spot, and every instance above is invisible without one.
  G-RED     have a fixture in tests/ that makes it FAIL. A gate that has never
            been observed to fail is a claim, not a control.

THIS SCRIPT IS ITSELF A GATE AND MUST OBEY ITS OWN CONTRACT. It reports its
coverage, it names its input, and t1_gate_contract.py holds its known-bads. Its
acceptance test is adversarial: on first run against this repo it MUST flag a
large number of scripts. A gate-on-gates that comes back clean on a codebase
independently measured as riddled is decoration, and should be deleted rather
than trusted.
"""
import argparse
import ast
import json
import re
import sys

try:
    import yaml
except ImportError:            # G-SELFCON degrades to N-A, never a false OK
    yaml = None
from pathlib import Path

#: a script "prints a verdict" if it emits PASS/FAIL/OK as a result word.
VERDICT_RE = re.compile(r"""print\(\s*f?["'][^"']*\b(PASS|FAIL)\b""", re.X)
VERDICT_RE2 = re.compile(r"""["']\s*(PASS|FAIL)\b""")

#: a coverage denominator: "N/M", "graded N of M", "coverage ...".
COVERAGE_RE = re.compile(
    r"coverage|"
    r"\{[^{}]*\}\s*/\s*\{[^{}]*\}|"          # f"{n}/{m}"
    r"\bof\s+\{?len\(|"                       # "of {len(rows)}"
    r"\bgraded\b[^\n]*\bof\b|"
    r"\d+\s*/\s*\{",
    re.I)

#: naming the graded artifact — a path argument or an explicit echo.
#: `--root` / `--project` / `--releases-root` were added after this check
#: FALSE-FAILED `fleet_regrade.py`, which prints the full path of every release
#: it grades — more explicitly than most gates here. The regex is a PROXY for
#: "names what it graded", and a proxy that rejects a tool doing the thing
#: properly is the adjacent-property error this repo keeps paying for.
#: Widened on that principle, not to make one tool pass: any of these options
#: selects the artifact set under grade.
INPUT_RE = re.compile(
    r"add_argument\(\s*[\"'](?!--)|"          # a positional path arg
    r"add_argument\(\s*[\"']--(release|releases-root|root|project|board|pcb|"
    r"zip|fab|bom|cpl|dir|archive|manifest|src|source|input)|"
    r"graded against|read from|input:",
    re.I)

SKIP_BASENAMES = {
    # generators and libraries, not checkers — they produce, they do not grade.
    "pcb_toolkit.py", "fab_tier_util.py", "schwriter2.py", "grind_driver.py",
    "audit_template.py", "circuit_json_to_kicad_pcb.py",
    "circuit_json_to_kicad_sch.py", "generate_board_generic.py",
    "generate_rules_generic.py", "route_and_stitch_generic.py",
    "import_krt.py", "export_fab_jlc.py", "export_jlc_package.py",
    "pcb_status.py", "jlc_rotation_measure.py", "jlc_rotation_resolve.py",
}


def prints_verdict(text):
    return bool(VERDICT_RE.search(text) or VERDICT_RE2.search(text))


def has_red_fixture(name, tests_dir):
    """Some tests/*.py must INVOKE this script AND use must_fail.

    A BARE NAME MATCH IS NOT ENOUGH, and this check shipped with that hole: the
    first version searched for the stem anywhere in the file, so the sentence
    "found by fleet_regrade.py" inside an unrelated test's DOCSTRING satisfied
    G-RED for fleet_regrade. A gate could claim a fixture it does not have —
    a gate-on-gates that cannot fail on the property it names, which is the
    exact defect class it exists to police.

    The first fix over-corrected the other way: requiring the literal path
    `scripts/<stem>.py` false-failed 16 gates that DO have real suites but bind
    through the harness idiom `SCRIPTS / "<stem>.py"` — t1_bom_source.py really
    does exercise bom_source_check.py. Matching a QUOTED filename covers both
    binding forms and still excludes prose, because a docstring sentence writes
    the name bare.

    Still a proxy. A test could quote a name it never runs. But a proxy that
    rejects prose and accepts both real idioms is the honest middle; the
    alternative is parsing call graphs to grade a docstring.
    """
    stem = Path(name).stem
    pat = re.compile(rf"""["'][^"']*{re.escape(stem)}\.py["']""")
    for t in sorted(tests_dir.glob("t*.py")):
        body = t.read_text(errors="replace")
        if pat.search(body) and "must_fail" in body:
            return t.name
    return None


def audit(root, enforce=None):
    root = Path(root)
    tests_dir = root / "tests"
    scripts = sorted(root.glob("skills/*/scripts/*.py"))
    rows, unparsed = [], []
    for p in scripts:
        if p.name in SKIP_BASENAMES:
            continue
        try:
            text = p.read_text()
            ast.parse(text)                 # a file we cannot parse is a FAIL
        except Exception as e:
            unparsed.append(f"{p.relative_to(root)}: {e}")
            continue
        if not prints_verdict(text):
            continue
        rows.append({
            "script": str(p.relative_to(root)),
            "cover": bool(COVERAGE_RE.search(text)),
            "input": bool(INPUT_RE.search(text)),
            "red": has_red_fixture(p.name, tests_dir),
        })

    want = set(enforce or ["G-COVER", "G-INPUT", "G-RED"])
    fails = []
    for r in rows:
        if "G-COVER" in want and not r["cover"]:
            fails.append(f"G-COVER {r['script']}: prints a verdict with no "
                         f"`N/M` coverage denominator — it can report success "
                         f"over input it did not understand")
        if "G-INPUT" in want and not r["input"]:
            fails.append(f"G-INPUT {r['script']}: never names the artifact it "
                         f"graded — a reader cannot tell shipped bytes from a "
                         f"reconstruction (canon M6)")
        if "G-RED" in want and not r["red"]:
            fails.append(f"G-RED {r['script']}: no tests/ fixture makes it "
                         f"FAIL — it has never been observed to gate")
    return {"root": str(root), "gates": rows, "fails": fails,
            "unparsed": unparsed,
            "coverage": f"{len(rows)}/{len(rows)} verdict-printing scripts "
                        f"audited ({len(scripts)} scripts scanned, "
                        f"{len(SKIP_BASENAMES)} generator/library names skipped)"}



# --------------------------------------------------------------- G-SELFCON
# ADR-0007. A rule file can contradict ITSELF, and then no board can satisfy it.
# fab_tiers.yaml declares min_silk_text_height 0.45 AND min_silk_stroke 0.15 on
# every tier, while KiCad clamps a text stroke to <= 0.25 x height: 0.45 mm text
# can reach at most 0.1125 mm of stroke, so the two floors cannot both be met.
# smc0985-cooksense then shipped six SAFETY designators below the stroke floor —
# J_ESTOP, J_DOOR, J_MODE among them — and the waiver written the same day
# called 0.13 acceptable. Nothing could have passed; nothing said so.
KICAD_STROKE_OVER_HEIGHT = 0.25      # KiCad's own clamp on stroke vs text height


def check_self_consistency(refs_dir):
    """Cross-FIELD checks on the rule files themselves. Returns (fails, n)."""
    fails, n = [], 0
    ft = Path(refs_dir) / "fab_tiers.yaml"
    if not ft.exists() or yaml is None:
        return fails, n
    doc = yaml.safe_load(ft.read_text()) or {}
    for tier, d in sorted((doc.get("tiers") or {}).items()):
        if not isinstance(d, dict):
            continue
        h, s = d.get("min_silk_text_height"), d.get("min_silk_stroke")
        if h is None or s is None:
            continue
        n += 1
        reachable = float(h) * KICAD_STROKE_OVER_HEIGHT
        if float(s) > reachable + 1e-9:
            fails.append(
                f"G-SELFCON fab_tiers.yaml[{tier}]: min_silk_stroke "
                f"{s} mm is UNREACHABLE at min_silk_text_height {h} mm — "
                f"KiCad clamps stroke to <= {KICAD_STROKE_OVER_HEIGHT} x height, "
                f"so the most this text can plot is {reachable:.4f} mm. "
                f"No board can satisfy both floors; raise the height to "
                f">= {float(s)/KICAD_STROKE_OVER_HEIGHT:.2f} mm or lower the "
                f"stroke to <= {reachable:.4f} mm")
    return fails, n


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[3]))
    ap.add_argument("--json", default=None)
    ap.add_argument("--enforce", default=None,
                    help="comma list, e.g. G-COVER,G-INPUT (default: all)")
    a = ap.parse_args(argv)

    enforce = a.enforce.split(",") if a.enforce else None
    r = audit(a.root, enforce)
    if a.json:
        Path(a.json).write_text(json.dumps(r, indent=2) + "\n")

    print(f"  coverage: {r['coverage']}")
    for u in r["unparsed"]:
        print(f"  FAIL G-PARSE {u}")
    for f in r["fails"]:
        print(f"  FAIL {f}")

    sc_fails, sc_n = check_self_consistency(
        Path(__file__).resolve().parent.parent / "references")
    print(f"  G-SELFCON: {sc_n} rule-file cross-field pair(s) graded")
    for f in sc_fails:
        print(f"  FAIL {f}")

    bad = len(r["fails"]) + len(r["unparsed"]) + len(sc_fails)
    if bad:
        print(f"G-CONTRACT FAIL: {bad} obligation(s) unmet across "
              f"{len(r['gates'])} verdict-printing script(s)")
        return 1
    print(f"G-CONTRACT OK: {len(r['gates'])} verdict-printing script(s) "
          f"meet G-INPUT/G-COVER/G-RED; {sc_n} rule-file pair(s) self-consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
