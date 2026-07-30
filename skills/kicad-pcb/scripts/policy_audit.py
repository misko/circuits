#!/usr/bin/env python3
"""Portfolio policy auditor — runs every machine-checkable policy from
references/design-policies.md against one project and emits a graded report.

usage: /usr/bin/python3 policy_audit.py PROJECT_DIR [--config PATH] [--skip-drc]

Grades per check ID: PASS / FAIL / WAIVED / N-A / HUMAN.
Report -> PROJECT_DIR/06_build/policy_audit.md (+ stdout summary).
Exit 1 if any FAIL.

Optional config (PROJECT_DIR/03_src/rules/policy_audit.json):
  { "plane_regions": [{"layer":"B.Cu","ref":"U3","radius_mm":3,"max_len_mm":5}],
    "therm_pad_area_mm2": 4.0, "therm_min_vias": 2, "therm_search_mm": 1.0,
    "silk_fn_refs": "^(J|F|TP)[0-9]", "silk_fn_radius_mm": 8.0,
    "route_pro_glob": "06_build/route/*.kicad_pro" }
Waivers (PROJECT_DIR/03_src/rules/policy_waivers.yaml): YAML list of
  {id: <CHECK-ID>, refs: [...], why: "<evidence>"} — same evidence rules as
twin adjudications; a waiver without a why is itself a FAIL.

Run with the KiCad-bundled python (/usr/bin/python3, pcbnew importable).
"""
import argparse
import glob
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

import pcbnew

try:
    import yaml
except ImportError:
    yaml = None

MM = pcbnew.ToMM


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def cell(text):
    """One markdown table cell. A newline would split the row across lines and
    an unescaped '|' would invent a column, so a detail string containing
    either silently changes the SHAPE of the table it is reported in."""
    return str(text).replace("\r", " ").replace("\n", " ").replace("|", "\\|")


GRADES = ("PASS", "FAIL", "WAIVED", "HUMAN", "N-A")


def parse_report(text):
    """(rows, stated_summary) read back out of a rendered policy_audit.md.

    The INDEPENDENT reading of the report (canon M1): it re-derives the grade
    counts from the published table instead of trusting the counter that
    wrote the headline. Only rows whose Grade cell is exactly one of GRADES
    are counted, so a spliced or wrapped line is a MISSING row rather than a
    silently miscounted one."""
    rows, stated = [], None
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r"^Summary:\s*(.*)$", s)
        if m:
            stated = {}
            for part in m.group(1).split(","):
                k, _, v = part.partition("=")
                if v.strip().isdigit():
                    stated[k.strip()] = int(v.strip())
            continue
        # a row must be a COMPLETE markdown row: both delimiters present. The
        # sealed corruption left a head fragment ending mid-detail and an
        # orphan tail starting mid-line; accepting either would have counted
        # the wreckage as a row and hidden the shortfall.
        if not (s.startswith("|") and s.endswith("|")) or set(s) <= set("|- "):
            continue
        cols = [c.strip() for c in s.strip("|").split("|")]
        if len(cols) >= 3 and cols[1] in GRADES:
            rows.append((cols[0], cols[1]))
    return rows, stated


def report_inconsistencies(text, n_rows, counts):
    """Everything that must hold between a written report and the grading run
    that produced it. Empty list = the file on disk says what we graded."""
    bad = []
    got_rows, stated = parse_report(text)
    if len(got_rows) != n_rows:
        bad.append(f"table has {len(got_rows)} gradeable row(s) but "
                   f"{n_rows} check(s) were graded — {n_rows - len(got_rows)} "
                   f"row(s) are missing or malformed on disk")
    got = {}
    for _cid, g in got_rows:
        got[g] = got.get(g, 0) + 1
    if got != counts:
        bad.append(f"grades counted FROM THE TABLE {got} != grades graded "
                   f"{counts}")
    if stated is None:
        bad.append("no `Summary:` line in the written report")
    elif stated != counts:
        bad.append(f"the report's own `Summary:` line says {stated} but the "
                   f"run graded {counts}")
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--config", default="")
    ap.add_argument("--skip-drc", action="store_true",
                    help="skip the kicad-cli ERC/DRC runs (fast re-grade)")
    ap.add_argument("--board", default="",
                    help="which board of a MULTI-BOARD project to grade "
                         "(04_kicad stem, e.g. 'interposer'); default is the "
                         "first, which is what the release scope follows")
    args = ap.parse_args()
    proj = Path(args.project).resolve()
    cfgp = Path(args.config) if args.config else proj / "03_src/rules/policy_audit.json"
    cfg = json.loads(cfgp.read_text(encoding="utf-8-sig")) if cfgp.exists() else {}
    build = proj / "06_build"
    build.mkdir(exist_ok=True)

    boards = sorted(glob.glob(str(proj / "04_kicad" / "*.kicad_pcb")))
    schs = sorted(glob.glob(str(proj / "04_kicad" / "*.kicad_sch")))
    # WHICH BOARD IS UNDER AUDIT. A project may build several
    # (smc0985-cooksense builds `cooksense` and `interposer`), and every check
    # below — including the RELEASE scope — must grade the SAME one. `--board`
    # names it; without it the first is graded, exactly as before.
    if args.board:
        _want = re.sub(r"[\s_]+", "-", args.board.strip()).strip("-").lower()
        _hit = [b for b in boards
                if re.sub(r"[\s_]+", "-", Path(b).stem).strip("-").lower()
                == _want]
        if not _hit:
            sys.exit(f"policy_audit: --board {args.board!r} matches none of "
                     f"{[Path(b).stem for b in boards]}")
        boards = _hit + [b for b in boards if b not in _hit]
        schs = [s for s in schs
                if re.sub(r"[\s_]+", "-", Path(s).stem).strip("-").lower()
                == _want] or schs
    board_p = boards[0] if boards else None
    sch_p = schs[0] if schs else None
    board_name = Path(board_p).stem if board_p else None

    waivers = []
    wp = proj / "03_src/rules/policy_waivers.yaml"
    if wp.exists() and yaml:
        waivers = yaml.safe_load(wp.read_text(encoding="utf-8-sig")) or []
    waived_ids = {}
    for w in waivers:
        if w.get("id"):
            waived_ids.setdefault(w["id"], []).append(w)

    rows = []  # (id, grade, detail)

    def grade(cid, ok, detail_pass, detail_fail):
        if ok:
            rows.append((cid, "PASS", detail_pass))
        elif cid in waived_ids:
            ws = waived_ids[cid]
            bad = [w for w in ws if len(str(w.get("why", ""))) < 40]
            if bad:
                rows.append((cid, "FAIL", f"waiver without evidence: {bad}"))
            else:
                rows.append((cid, "WAIVED", f"{detail_fail} — waived: "
                            f"{ws[0]['why'][:90]}..."))
        else:
            rows.append((cid, "FAIL", detail_fail))

    # ---------------- schematic ----------------
    erc_errors, erc_warns, nc_errors = None, None, None
    if sch_p and not args.skip_drc:
        out = build / "policy_erc.json"
        sh(["kicad-cli", "sch", "erc", "--severity-all", "--format", "json",
            "-o", str(out), sch_p])
        if out.exists():
            d = json.loads(out.read_text(encoding="utf-8-sig"))
            viols = [v for s in d.get("sheets", []) for v in s.get("violations", [])]
            erc_errors = sum(1 for v in viols if v.get("severity") == "error")
            erc_warns = len(viols) - erc_errors
            nc_errors = sum(1 for v in viols if v.get("type") == "pin_not_connected")
    if erc_errors is None:
        rows.append(("S-ERC", "N-A", "no schematic or --skip-drc"))
        rows.append(("S-NC", "N-A", "no ERC data"))
    else:
        grade("S-ERC", erc_errors == 0,
              f"0 errors ({erc_warns} warnings)",
              f"{erc_errors} errors, {erc_warns} warnings at severity-all")
        grade("S-NC", nc_errors == 0,
              "all floats no_connect-flagged",
              f"{nc_errors} pin_not_connected — sanctioned floats not flagged")

    board = pcbnew.LoadBoard(board_p) if board_p else None
    if board:
        copper_nets = {t.GetNetname() for t in board.GetTracks()}
        auto = sorted(n for n in copper_nets if n.startswith("Net-("))
        grade("S-NET", not auto, f"{len(copper_nets)} routed nets, all named",
              f"auto-named nets on copper: {auto[:6]}")
    else:
        rows.append(("S-NET", "N-A", "no board"))

    # ---- S-VER reads the KEY, not the first place the word appears ---------
    # It used to grep the raw text for the first literal `verified:` and read
    # 300 characters from there. `part.yaml` is a YAML document that TALKS
    # ABOUT ITSELF: `gotchas:` entries cross-reference "see verified:", a
    # `sha256:` value says "no PDF is vendored; see verified:", and comments
    # write "# Footprint match verified: ...". Any of those that sorts before
    # the real key SHADOWS it, and S-VER then grades a sentence that is not
    # the citation. Measured 2026-07-28 over all 557 fleet part.yaml: 15 files
    # where the grep and the parsed key disagree — 4 shadowed by a `#`
    # comment, 11 by an earlier quoted string. The 300-char window was the
    # second half of the same mistake: a citation past that cut-off read as
    # absent. `yaml.safe_load` + `y["verified"]` has neither failure mode.
    weak, tot, unparsed = [], 0, []
    for py in sorted(glob.glob(str(proj / "02_parts" / "*" / "part.yaml"))):
        name = Path(py).parent.name
        y = None
        if yaml:
            try:
                y = yaml.safe_load(Path(py).read_text(encoding="utf-8-sig")) or {}
            except Exception as exc:
                y = None
                why = str(exc).splitlines()[0][:80]
        if y is None:
            # canon M-COVER: input the gate cannot parse is a FAIL that names
            # itself, never a silently-skipped zero. NOT PINNED BY A FIXTURE
            # and deliberately said so: an unparseable part.yaml never reaches
            # here today, because P-LAYOUT's unguarded `yaml.safe_load` below
            # raises first and takes the whole audit down. That is loud rather
            # than silent, so it is not this change's defect — it is reported
            # in the commit body as its own job. The branch stands as the
            # backstop for the no-PyYAML case and for when that is fixed.
            tot += 1
            unparsed.append(f"{name} ({'no PyYAML' if not yaml else why})")
            continue
        # 2-pad passives need no figure citation (no pinout to mirror)
        npins = len(y.get("pins") or {})
        if npins and npins <= 2:
            continue
        v = y.get("verified")
        note = v if isinstance(v, str) else (
            "" if v is None else yaml.safe_dump(v, allow_unicode=True))
        tot += 1
        if not note.strip():
            weak.append(name + " (missing)")
            continue
        if not re.search(r"(fig(ure)?\.?\s*[\dA-Z-]|table\s*[\d-]|p\.?\s*\d|page\s*\d|drawing)",
                         note, re.I):
            weak.append(name)
    if tot:
        bad = weak + unparsed
        detail = f"weak/missing figure citations: {weak[:8]} ({len(weak)}/{tot})"
        if unparsed:
            detail += (f"; UNPARSEABLE part.yaml (not graded, not passed): "
                       f"{unparsed[:4]} ({len(unparsed)}/{tot})")
        grade("S-VER", not bad, f"{tot}/{tot} verified: cite figure/page",
              detail)
    else:
        rows.append(("S-VER", "N-A", "no 02_parts entries"))

    # P-ESC / P-TIER: package escape feasibility vs the declared fab tier
    # (D-ESC/D-TIER made mechanical — the clean-room 3S stall 2026-07-20:
    # a 0.5mm QFN at standard tier, discovered as drill_out_of_range at DRC)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import escape_check as ec
    part_yamls = sorted(glob.glob(str(proj / "02_parts" / "*" / "part.yaml")))
    if part_yamls and yaml:
        tiers = ec.load_tiers()
        probs = []
        for py in part_yamls:
            try:
                probs += ec.check_part(py, tiers)
            except Exception as e:
                probs.append(f"{Path(py).parent.name}: unreadable escape "
                             f"block ({e})")
        grade("P-ESC", not probs,
              f"{len(part_yamls)} parts: escape blocks agree with escape_check",
              "; ".join(probs[:4]))
        netsy = proj / "03_src/rules/nets.yaml"
        declared = None
        if netsy.exists():
            declared = (yaml.safe_load(netsy.read_text(encoding="utf-8-sig")) or {}).get("fab_tier")
        if not netsy.exists():
            rows.append(("P-TIER", "N-A", "no 03_src/rules/nets.yaml yet"))
        elif declared not in tiers:
            grade("P-TIER", False, "",
                  f"nets.yaml fab_tier '{declared}' is not a tier in "
                  f"fab_tiers.yaml — declare the ordering tier (D-TIER)")
        else:
            drank = tiers[declared]["rank"]
            over = []
            for py in part_yamls:
                y = yaml.safe_load(Path(py).read_text(encoding="utf-8-sig")) or {}
                tr = (y.get("escape") or {}).get("tier_required")
                if tr in tiers and tiers[tr]["rank"] > drank:
                    over.append(f"{y.get('mpn', Path(py).parent.name)} "
                                f"needs {tr}")
            grade("P-TIER", not over,
                  f"all parts escape at declared fab_tier '{declared}'",
                  f"parts exceed fab_tier '{declared}': {over[:4]} — "
                  f"re-select the part, OR raise fab_tier + write the tier "
                  f"ADR (D-TIER) + the ORDER_README line from fab_tiers.yaml")
    else:
        rows.append(("P-ESC", "N-A", "no 02_parts entries"))
        rows.append(("P-TIER", "N-A", "no 02_parts entries"))

    # P-LAYOUT / P-ADJ: datasheet LAYOUT-section compliance — the THIRD part.yaml
    # dimension, after verified: (pinout, S-VER) and escape: (package, P-ESC).
    # Motivating incident (usb-hub-3s-v2 TPS25740A, 2026-07-22): pinout + escape
    # were both verified, but the datasheet Layout section (TI SLVSDG8B §11 /
    # EVM SLVUAP7A: place the pass FET + sense R + VBUS caps HARD against the
    # power-stage pin edge, Kelvin-sensed) was never read. The floorplan put the
    # FET row 7mm north across a channel, so four QFN escapes could not coexist —
    # surfaced only after ~8 routing rebuilds. These gates move it to PARTS +
    # PLACEMENT. P-LAYOUT: in-scope parts (multi-pin actives + power/sense
    # discretes) must carry a layout: block citing the Layout section / reference
    # design + a keep_short/adjacency/notes budget. P-ADJ: the board must honour
    # each layout keep_short net-span budget (warn+waiver via grade()).
    LAYOUT_SCOPE = re.compile(r'fet|mosfet|current_sense|shunt|crystal|'
                              r'oscillator|inductor', re.I)
    if part_yamls and yaml:
        scoped, missing, bad = 0, [], []
        for py in part_yamls:
            y = yaml.safe_load(Path(py).read_text(encoding="utf-8-sig")) or {}
            npins = len(y.get("pins") or {})
            if not (npins > 2 or LAYOUT_SCOPE.search(str(y.get("type", "")))):
                continue
            scoped += 1
            name = Path(py).parent.name
            lay = y.get("layout")
            if not lay:
                missing.append(name)
            elif not lay.get("source"):
                bad.append(f"{name}: layout: has no source (cite the datasheet "
                           f"Layout section / reference design / app note)")
            elif not (lay.get("keep_short") or lay.get("adjacency")
                      or lay.get("notes")):
                bad.append(f"{name}: layout: declares no keep_short/adjacency/notes")
        if scoped:
            grade("P-LAYOUT", not (missing or bad),
                  f"{scoped} in-scope parts carry a datasheet layout: block",
                  f"read the Layout section + reference design and add a layout: "
                  f"block — missing ({len(missing)}): {missing[:6]}"
                  f"{'...' if len(missing) > 6 else ''}; "
                  f"malformed ({len(bad)}): {bad[:3]}")
        else:
            rows.append(("P-LAYOUT", "N-A", "no in-scope (IC / power-sense) parts"))

        # P-ADJ: board placement vs each layout budget — keep_short AND
        # adjacency.
        #
        # TWO DEFECTS FIXED HERE 2026-07-29, found independently by two board
        # agents from opposite directions, and they are the same defect: the
        # gate reported a verdict it had not earned.
        #
        # (a) IT MEASURED THE WRONG DISTANCE. The span was the MAXIMUM PAD PAIR
        # OVER THE WHOLE NET, which is not what a `keep_short` sentence means.
        # A datasheet decoupling sentence is about a PIN and its NEAREST
        # QUALIFYING PARTNER ("100 nF close to EACH IOVDD pin", "1 uF close to
        # VREG_VOUT"), so the number that grades it is the anchor pin's
        # distance to the nearest pad that serves it. The whole-net maximum has
        # a property that by itself disqualifies it as a placement metric:
        # ADDING A CORRECTLY-PLACED BULK CAPACITOR MAKES THE BUDGET SCORE
        # WORSE, because the new pad extends the net's span. Measured:
        #   * pluto-cal-switch RP2040:3V3 reported 72.96mm against 4mm — 3V3 is
        #     a poured rail crossing the board. The ANCHOR metric on the same
        #     44 budgets is 44/44 PASS, worst 2.60mm (U_MCU.26 -> C_IO3.1).
        #   * pluto-rx2-8way RP2040:DVDD_1V1 reported 13.167mm against 10mm off
        #     a 6-pad net. The anchor metric says 8.79mm (U_MCU.23 ->
        #     C_MCU7.1): inside the budget, and it REPORTS the tight pair
        #     instead of burying it under a board-scale number.
        # It does NOT soften the incident P-ADJ was built for: usb-hub-3s-v2's
        # TPS25740A RSNS still FAILS, 7.34mm (U1.19 -> Q6.5) against 5mm, where
        # the whole-net figure was 10.18mm. And ABM8-272-T3's `GND <= 3mm` on
        # pluto-rx2-8way still FAILS — 3.23mm (Y_XTAL.4 -> C_XTAL1.2) instead
        # of 67.24mm, which was the board's DIAGONAL and not the crystal's
        # anything. A budget nobody can act on is not enforcement.
        # THE ANCHOR IS STATED, ALWAYS (the PASS detail names the graded pair):
        # an unstated anchor is a hidden assumption. `anchor_pins:` lets the
        # author name the pin(s) explicitly when the sentence is about one pair.
        #
        # (b) IT NEVER READ `layout.adjacency` AT ALL. Refdes-pair budgets were
        # in the schema, in the part.yaml files, and graded by NOTHING — while
        # LOOKING covered, which is worse than an absent field. The live
        # example, with its number: USBLC6-2SC6 requires U_ESD within 2.0mm of
        # J_USB because ST DocID11265 sec 2.2 turns 6nH per 10mm into a 17V
        # clamp firing at 305V; pluto-rx2-8way's floorplan sat at ~8mm and no
        # gate objected, so the board's agent had to hand-measure it.
        # An adjacency budget is graded as the COPPER GAP between the two
        # parts' pads on each shared net (pad edge to pad edge = the track
        # length the 6nH/10mm arithmetic applies to), worst shared net wins.
        # POURED nets are excluded from that measurement and said to be: two
        # parts on a plane are joined BY THE PLANE, and a pad-gap does not
        # measure a pour connection (it is R-THERM/stitch work).
        if board:
            zone_nets = {z.GetNetname() for z in board.Zones()
                         if z.GetNetname()}
            fp_by_id, fp_by_ref, netpads = {}, {}, {}
            for f in board.GetFootprints():
                fp_by_id.setdefault(f.GetFPIDAsString(), []).append(f)
                fp_by_ref[f.GetReference()] = f
                for p in f.Pads():
                    n = p.GetNetname()
                    if n:
                        netpads.setdefault(n, []).append((p, f))

            def _span(p1, p2):
                """Pad-CENTRE to pad-centre, mm — the `max_span_mm` measure."""
                a = p1.GetPosition()
                b = p2.GetPosition()
                return math.hypot(MM(a.x - b.x), MM(a.y - b.y))

            def _gap(p1, p2):
                """Pad-EDGE to pad-edge, mm — the `max_mm` adjacency measure,
                i.e. how much copper must actually be run between the two.
                Axis-aligned pad boxes; KiCad's pad bbox is rotation-aware.
                CROSS-CHECKED against a hand measurement made by a different
                agent with a different tool (canon M1): this returns 1.689mm
                for J_USB.A6 -> U_ESD.1 on pluto-rx2-8way, the same 1.689 that
                board's floorplan records for D+/D-."""
                b1, b2 = p1.GetBoundingBox(), p2.GetBoundingBox()
                dx = max(0, b1.GetLeft() - b2.GetRight(),
                         b2.GetLeft() - b1.GetRight())
                dy = max(0, b1.GetTop() - b2.GetBottom(),
                         b2.GetTop() - b1.GetBottom())
                return MM(int(math.hypot(dx, dy)))

            def _ref(p, f):
                return f"{f.GetReference()}.{p.GetNumber()}"

            # graded_ks / graded_adj are SEPARATE ROWS, for the reason
            # P-ADJ-UNREACHED is a separate row: both pluto boards already hold
            # a P-ADJ waiver whose evidence is a list of MEASURED keep_short
            # spans, and adjacency findings are a different class. Folding them
            # in would have let rx2's waiver absorb two brand-new violations
            # (U_LDO~C_LDO 4.88mm of 3, U_LDO~C_LDI 10.78mm of 3) in total
            # silence on their first run — canon M4's inherited-defect pattern,
            # measured, not hypothesised.
            unreached, graded_ks, graded_adj = [], [], []
            viol_ks, viol_adj = [], []
            n_ks = n_adj = 0
            for py in part_yamls:
                y = yaml.safe_load(Path(py).read_text(encoding="utf-8-sig")) or {}
                lay = y.get("layout") or {}
                pname = Path(py).parent.name
                if not isinstance(lay, dict):
                    unreached.append(
                        f"{pname}: layout: is not a mapping "
                        f"({type(lay).__name__}) — no budget in it can be read")
                    lay = {}
                # THE DECLARING PART'S FOOTPRINTS, resolved by footprint id —
                # the only refdes<->part relation a part.yaml carries. Where an
                # id is shared (two 0402 resistor MPNs, two YAT attenuator
                # values), the intersection with the budgeted NET disambiguates
                # it: only R_USBP is on USB_DP_MCU. Identity is by REFDES, not
                # by object, so nothing depends on SWIG proxy lifetimes.
                own = fp_by_id.get(str(y.get("footprint")), [])
                own_refs = {f.GetReference() for f in own}

                # ---------------- keep_short: pin -> nearest partner ---------
                for ks in (lay.get("keep_short") or []):
                    n_ks += 1
                    # A MALFORMED BUDGET IS UNREACHED, NEVER A CRASH. Measured
                    # 2026-07-29: `adjacency:` in the wild is mostly FREE PROSE
                    # (~40 string entries on usb-hub-3s-v3, 5 on archived
                    # crow-mic-pod), which crashed the first version of this
                    # loop with `'str' object has no attribute 'get'`. A crash
                    # is the WORST available verdict — the wrapper reads the
                    # non-zero exit as "the gate objected" while a human reads
                    # the traceback as a broken test rather than an ungraded
                    # board (fa22228's BOM post-mortem, same lesson).
                    if not isinstance(ks, dict):
                        unreached.append(
                            f"{pname}: keep_short entry is not a mapping "
                            f"({str(ks)[:60]!r}) — a budget needs `net:` + "
                            f"`max_span_mm:`; prose belongs under notes:; "
                            f"graded NOTHING")
                        continue
                    try:
                        mx = float(ks.get("max_span_mm", 6))
                    except (TypeError, ValueError):
                        unreached.append(
                            f"{pname}: keep_short {ks.get('net')!r} has a "
                            f"non-numeric max_span_mm "
                            f"({ks.get('max_span_mm')!r}) — graded NOTHING")
                        continue
                    net = ks.get("net")
                    pts = netpads.get(net) or []
                    want = [str(p) for p in (ks.get("anchor_pins") or [])]
                    if len(pts) < 2:
                        # ---- UNREACHED, not skipped (canon M-COVER) --------
                        # A declared budget whose net carries fewer than two
                        # pads on this board is graded by NOTHING, and the
                        # `continue` said so to no one: P-ADJ then reported
                        # PASS over a budget it never evaluated. The usual
                        # cause is a NET NAME that does not exist here —
                        # renamed, or copied from the datasheet's reference
                        # design — which is exactly the case where a silent
                        # pass is most misleading, because the budget looks
                        # honoured and was never even looked up. P-FACT
                        # already reports its unreached assertions this way;
                        # this is the same rule.
                        unreached.append(
                            f"{pname}: keep_short net "
                            f"{net!r} has {len(pts)} pad(s) on this board "
                            f"(needs 2) — budget {mx}mm graded NOTHING")
                        continue
                    if not own:
                        unreached.append(
                            f"{pname}: keep_short net {net!r} — the declaring "
                            f"part's footprint {y.get('footprint')!r} is on no "
                            f"footprint of this board, so the ANCHOR PIN "
                            f"cannot be resolved; budget {mx}mm graded NOTHING")
                        continue
                    anchors = [(p, f) for p, f in pts
                               if f.GetReference() in own_refs
                               and (not want or str(p.GetNumber()) in want)]
                    if not anchors:
                        # M-ENTRY: the budget names a net the declaring part
                        # does not touch. Real and common — a series element
                        # splits the node (RP2040's USB_DP is USB_DP_MCU after
                        # the 27R; ABM8's XOUT is the crystal side of R_XTAL) —
                        # and the whole-net metric graded it anyway, off pads
                        # belonging to entirely different parts.
                        unreached.append(
                            f"{pname}: keep_short net {net!r} — "
                            f"{[f.GetReference() for f in own]} carries "
                            f"{'no pad ' + str(want) if want else 'NO pad'} on "
                            f"it, so the budget's own part is not in it; "
                            f"budget {mx}mm graded NOTHING")
                        continue
                    worst = None
                    for p, f in anchors:
                        cand = [(q, g) for q, g in pts
                                if g.GetReference() != f.GetReference()]
                        if not cand:
                            continue
                        # key=, not a tuple: a tie would otherwise fall
                        # through to comparing SWIG pad objects and raise.
                        q, g = min(cand, key=lambda t: _span(p, t[0]))
                        d = _span(p, q)
                        if worst is None or d > worst[0]:
                            worst = (d, _ref(p, f), _ref(q, g))
                    if worst is None:
                        unreached.append(
                            f"{pname}: keep_short net {net!r} has pads ONLY on "
                            f"the declaring part "
                            f"({[f.GetReference() for f in own]}) — there is no "
                            f"partner pin to be near; budget {mx}mm graded "
                            f"NOTHING")
                        continue
                    d, a_ref, b_ref = worst
                    label = (f"{pname}:{net} {a_ref}->{b_ref} {d:.2f}mm of "
                             f"{mx}mm")
                    graded_ks.append((mx - d, label))
                    if d > mx + 1e-6:
                        viol_ks.append(f"{label} EXCEEDED "
                                       f"({str(ks.get('why', ''))[:60]})")

                # ---------------- adjacency: refdes pair -> copper gap -------
                for ad in (lay.get("adjacency") or []):
                    n_adj += 1
                    if not isinstance(ad, dict):
                        # see the keep_short note above: on this fleet the
                        # STRING form is the common one, and it is a real
                        # finding (a placement constraint no gate can read),
                        # not an exception.
                        unreached.append(
                            f"{pname}: adjacency entry is PROSE, not a graded "
                            f"budget ({str(ad)[:60]!r}) — write it as "
                            f"{{refdes: [A, B], max_mm: N, why: ...}} or move "
                            f"it to notes:; graded NOTHING")
                        continue
                    pair = ad.get("refdes") or [ad.get("a"), ad.get("b")]
                    pair = [str(r) for r in pair if r]
                    mx = ad.get("max_mm", ad.get("max_span_mm"))
                    if len(pair) != 2 or mx is None:
                        unreached.append(
                            f"{pname}: adjacency {ad!r} names "
                            f"{len(pair)} refdes and "
                            f"{'no' if mx is None else 'a'} limit — an "
                            f"adjacency budget needs exactly two refdes and a "
                            f"max_mm; graded NOTHING")
                        continue
                    mx = float(mx)
                    absent = [r for r in pair if r not in fp_by_ref]
                    if absent:
                        unreached.append(
                            f"{pname}: adjacency {pair[0]}/{pair[1]} — "
                            f"{absent} is on no footprint of this board "
                            f"(renamed, or copied from the reference design); "
                            f"budget {mx}mm graded NOTHING")
                        continue
                    fa, fb = fp_by_ref[pair[0]], fp_by_ref[pair[1]]
                    pa = [p for p in fa.Pads() if p.GetNetname()]
                    pb = [p for p in fb.Pads() if p.GetNetname()]
                    shared = ({p.GetNetname() for p in pa}
                              & {p.GetNetname() for p in pb})
                    poured = sorted(shared & zone_nets)
                    live = sorted(shared - zone_nets)
                    if not live:
                        unreached.append(
                            f"{pname}: adjacency {pair[0]}/{pair[1]} — "
                            + (f"their only shared net(s) {poured} carry a "
                               f"pour, and a pad gap does not measure a pour "
                               f"connection (stitch/R-THERM work)"
                               if poured else
                               f"they share no net, so there is no copper "
                               f"whose length this budget bounds")
                            + f"; budget {mx}mm graded NOTHING")
                        continue
                    worst = None
                    for net in live:
                        pairs = [(x, z) for x in pa
                                 if x.GetNetname() == net
                                 for z in pb if z.GetNetname() == net]
                        p, q = min(pairs, key=lambda t: _gap(*t))
                        d = _gap(p, q)
                        if worst is None or d > worst[0]:
                            worst = (d, net, _ref(p, fa), _ref(q, fb))
                    d, net, a_ref, b_ref = worst
                    label = (f"{pname}:{pair[0]}~{pair[1]} on {net} "
                             f"{a_ref}->{b_ref} gap {d:.2f}mm of {mx}mm")
                    graded_adj.append((mx - d, label))
                    if d > mx + 1e-6:
                        viol_adj.append(f"{label} EXCEEDED "
                                        f"({str(ad.get('why', ''))[:60]})")

            tot = len(graded_ks) + len(graded_adj) + len(unreached)

            def _adj_row(cid, kind, declared, graded_, viol_):
                """One measured-budget row. A ZERO DENOMINATOR IS A FAIL, NEVER
                A PASS (canon M-COVER): with every budget unreached the old code
                printed `PASS | 0/N budgets reached`, which is the shape this
                whole family of defects is named after. Nothing DECLARED is
                N-A — a different statement, and an honest one."""
                if not declared:
                    rows.append((cid, "N-A",
                                 f"no layout.{kind} budgets declared in "
                                 f"02_parts"))
                    return
                tightest = min(graded_)[1] if graded_ else "nothing"
                grade(cid, bool(graded_) and not viol_,
                      f"every MEASURABLE layout.{kind} budget is honoured — "
                      f"{len(graded_)}/{declared} declared budgets graded; "
                      f"tightest margin: {tightest}",
                      (f"datasheet layout.{kind} budgets exceeded: "
                       f"{viol_[:5]} ({len(viol_)}/{len(graded_)} graded) — "
                       f"re-place per the part's layout: block (targets HARD "
                       f"against the chip), or waive with the measured pair + "
                       f"why ({cid})"
                       if viol_ else
                       f"{cid} GRADED NOTHING: 0 of {declared} declared "
                       f"{kind} budgets were measurable, so this row has no "
                       f"denominator (canon M-COVER) — see P-ADJ-UNREACHED "
                       f"for each"))

            _adj_row("P-ADJ", "keep_short", n_ks, graded_ks, viol_ks)
            _adj_row("P-ADJ-PAIR", "adjacency", n_adj, graded_adj, viol_adj)
            # ---- ITS OWN ROW, deliberately, not folded into P-ADJ ----------
            # Both boards that carry keep_short budgets already hold a P-ADJ
            # waiver, and each names THREE measured span violations as its
            # evidence. Reporting "never graded" under the same ID would let
            # those waivers absorb 57 findings of a DIFFERENT CLASS without
            # anyone writing a word about them — a waiver silently widening
            # past its evidence is canon M4's inherited-defect pattern, and it
            # is the failure this gate exists to stop, not to reproduce.
            grade("P-ADJ-UNREACHED", not unreached,
                  f"every declared layout budget resolved to something this "
                  f"board can be measured against "
                  f"({len(graded_ks) + len(graded_adj)}/{tot})",
                  f"budgets DECLARED but graded by NOTHING: {unreached[:5]} "
                  f"({len(unreached)}/{tot}) — the net/refdes does not name "
                  f"a measurable pair on this board (renamed, split by a "
                  f"series element, or copied from the datasheet's reference "
                  f"design). Fix the name, name the pins with anchor_pins:, or "
                  f"drop the budget; a budget nothing evaluates is not a pass")
        else:
            rows.append(("P-ADJ", "N-A", "no board"))
            rows.append(("P-ADJ-PAIR", "N-A", "no board"))
    else:
        rows.append(("P-LAYOUT", "N-A", "no 02_parts entries"))
        rows.append(("P-ADJ", "N-A", "no 02_parts entries"))
        rows.append(("P-ADJ-PAIR", "N-A", "no 02_parts entries"))

    # S-OCCL: schematic text occlusions — global-label plates vs each other
    # and vs symbol Reference/Value property texts (approx bboxes; the same
    # ground-truth-geometry philosophy as the board silk de-collision).
    if sch_p:
        stxt = Path(sch_p).read_text(encoding="utf-8-sig")
        items = []  # (x0,y0,x1,y1,desc)
        CH_W, CH_H = 1.05, 2.2   # per-char width, line height @1.27mm font
        for m in re.finditer(r'\(global_label "([^"]+)".{0,80}?\(at ([-\d.]+) ([-\d.]+) (\d+)\)', stxt):
            txt, gx, gy, ang = m.group(1), float(m.group(2)), float(m.group(3)), int(m.group(4))
            wlen = (len(txt) + 2) * CH_W
            if ang == 180:   # plate extends left of anchor
                items.append((gx - wlen, gy - CH_H / 2, gx, gy + CH_H / 2,
                              f"label {txt}"))
            else:
                items.append((gx, gy - CH_H / 2, gx + wlen, gy + CH_H / 2,
                              f"label {txt}"))
        # INSTANCE properties only — lib_symbols prototypes all sit at the
        # same local coords and generate pure false positives
        for im_ in re.finditer(r'\(symbol \(lib_id[^\n]*\n(.{0,1200}?)\(pin ',
                               stxt, re.S):
            blk = im_.group(1)
            for pm in re.finditer(r'\(property "(Reference|Value)" "([^"]+)" \(at ([-\d.]+) ([-\d.]+) \d+\)\s*\(effects \(font \(size ([\d.]+) [\d.]+\)\)(?: \(justify (\w+)\))?', blk):
                kind, txt, gx, gy, fs, just = (pm.group(1), pm.group(2),
                                               float(pm.group(3)),
                                               float(pm.group(4)),
                                               float(pm.group(5)), pm.group(6))
                if "hide" in blk[pm.end():pm.end() + 60]:
                    continue
                w = len(txt) * fs * 0.82
                if just == "right":
                    box = (gx - w, gy - fs * 0.9, gx, gy + fs * 0.9)
                elif just == "left":
                    box = (gx, gy - fs * 0.9, gx + w, gy + fs * 0.9)
                else:
                    box = (gx - w / 2, gy - fs * 0.9, gx + w / 2, gy + fs * 0.9)
                items.append(box + (f"{kind} {txt}",))
        occl = []
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                a, b = items[i], items[j]
                if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                    occl.append(f"{a[4]} x {b[4]}")
        thr = int(cfg.get("soccl_max", 0))
        grade("S-OCCL", len(occl) <= thr,
              f"{len(occl)} text occlusions (<= {thr})",
              f"{len(occl)} schematic text occlusions: {occl[:6]}")
    else:
        rows.append(("S-OCCL", "N-A", "no schematic"))
    rows.append(("S5", "HUMAN", "design-math spot-check per review protocol"))
    rows.append(("S6", "HUMAN", "schematic readability graded in render review"))
    rows.append(("S7", "HUMAN", "decoupling-adjacency graded in render review"))

    # ---------------- placement ----------------
    drc = None
    if board_p and not args.skip_drc:
        out = build / "policy_drc.json"
        sh(["kicad-cli", "pcb", "drc", "--severity-all", "--refill-zones",
            "--schematic-parity", "--format", "json", "-o", str(out), board_p])
        if out.exists():
            drc = json.loads(out.read_text(encoding="utf-8-sig"))
    if drc is not None:
        court = [v for v in drc["violations"] if "courtyard" in v.get("type", "")]
        grade("P-CRT", not court, "0 courtyard findings",
              f"{len(court)} courtyard findings")
        nv, nu, npar = (len(drc["violations"]), len(drc["unconnected_items"]),
                        len(drc.get("schematic_parity", [])))
        grade("R-DRC", nv == 0 and nu == 0 and npar == 0,
              "0/0/0 at severity-all",
              f"{nv} violations / {nu} unconnected / {npar} parity")
    else:
        rows.append(("P-CRT", "N-A", "no DRC run"))
        rows.append(("R-DRC", "N-A", "no DRC run"))

    audit_src = ""
    ab = proj / "03_src" / "audit_board.py"
    if ab.exists():
        audit_src = ab.read_text(encoding="utf-8-sig")
        for extra in glob.glob(str(proj / "03_src" / "rules" / "audit*.json")):
            audit_src += Path(extra).read_text(encoding="utf-8-sig")
    if board is None:
        rows.append(("P-POL", "N-A", "no board yet"))
        rows.append(("P-KEEP", "N-A", "no board yet"))
    else:
        has_pol = bool(re.search(r"polarit|pad.?1.*net|pad1.*=", audit_src, re.I))
        pol_alt = bool(re.search(r"polarity_audit",
                       (proj / "03_src" / "generate_schematic.py").read_text(encoding="utf-8-sig")
                       if (proj / "03_src" / "generate_schematic.py").exists() else ""))
        grade("P-POL", has_pol or pol_alt,
              "polarity machine-check present (pad-1 nets vs part facts)",
              "no scripted pad-1-net polarity check anywhere in 03_src")
        has_keep = bool(re.search(r"mate|keepout|screw|antenna|edge", audit_src, re.I))
        grade("P-KEEP", has_keep,
              "mate/keepout checks present in project audit",
              "no scripted mate-direction/keepout checks in 03_src")

    if board:
        SILKS = (pcbnew.F_SilkS, pcbnew.B_SilkS)
        missing = []
        # Read the evidence-backed silk waiver from where generate_board WRITES
        # it — the board's own dir (04_kicad, a non-regenerable artifact per the
        # 04_kicad contract) — NOT the disposable 06_build tree. 06_build stays
        # only as a legacy fallback (drift-review 2026-07-22: a load-bearing
        # gate input must not live in a `rm -rf`-safe tree).
        wv = Path(board_p).parent / "refdes_waiver.json"
        if not wv.exists():
            wv = proj / "06_build" / "refdes_waiver.json"
        waived_refs = set(json.loads(wv.read_text(encoding="utf-8-sig"))) if wv.exists() else set()
        for f in board.GetFootprints():
            r = f.GetReference()
            # EXEMPT BY ATTRIBUTE, NOT BY REFDES PREFIX. This read
            # `r.startswith("H")`, i.e. it decided "does this part need a silk
            # refdes?" from the first letter of a name — so it exempted every H*
            # part (a HEADER would have walked straight through) and exempted
            # nothing else. It fired on usb-hub-3s-v3's FID1-FID3 the moment
            # fiducials became expressible, and a fiducial has no silk refdes ON
            # PURPOSE: silk beside the dot destroys the optical contrast the
            # fiducial exists to provide. FP_BOARD_ONLY is the attribute that
            # actually says "board feature, not a placed part", and mounting
            # holes already carry it — so this is strictly wider AND stricter.
            # Same root as canon A-ROT's name-DB post-mortem: A NAME IS NOT A
            # PART FACT.
            if (f.GetAttributes() & pcbnew.FP_BOARD_ONLY) or r in waived_refs:
                continue
            ref = f.Reference()
            if ref.GetLayer() not in SILKS or not ref.IsVisible():
                missing.append(r)
        grade("P-SILK-REF", not missing,
              "all refdes on visible silk",
              f"{len(missing)} refdes not on silk: {missing[:8]}")

        # `^(J|F|TP)[0-9]` required a DIGIT immediately after the prefix, so on
        # every board in this fleet that names touchpoints `J_DOOR` / `TP_ESTOP`
        # rather than `J1` / `TP1`, P-SILK-FN graded almost NOTHING and reported
        # PASS. MEASURED on cooksense 2026-07-28: 36 human touchpoints (13
        # connectors, 12 test points, mounting holes, 1 fuse) and the pattern
        # matched exactly ONE — `F1`. A gate that grades 1 of 36 and can only
        # pass is the `jlc_twin`-exited-0-on-11-unverified-parts class named in
        # CLAUDE.md, and it is what let a connector-labelling P0 through green.
        # `_` is now an accepted separator. `FB1` (ferrite) and `FID1`
        # (fiducial) still do NOT match, because neither a digit nor an
        # underscore follows their prefix letter — checked, not assumed.
        #
        # AND IT GRADED PRESENCE, NOT OWNERSHIP (fixed 2026-07-29). "Some silk
        # text is within 8mm of J_RX2" is not the property P5 wants; the
        # property is that the label belongs to THAT part rather than to its
        # neighbour, and a label nearer the wrong connector is worse than no
        # label at all — it actively misdirects the person plugging the cable
        # in. Three lenses on three boards found labels on the wrong part
        # while this check said PASS. The measured instance, from
        # pluto-rx2-8way's own floorplan header: the legend "RX2 -> PLUTO RX2"
        # sat 7.29mm from J_ANT1 and 7.85mm from J_RX2 — nearer the ANTENNA
        # jack than the SDR input it names, on the one pair of ports whose
        # confusion feeds an SDR receiver with an antenna. Presence passed it.
        # So each family member must have at least one nearby text that is
        # NEARER to it than to any other member of the same family, and the
        # row reports the LEAD in mm (how much nearer), because a 0.1mm lead is
        # a coin toss dressed as a pass.
        pat = re.compile(cfg.get("silk_fn_refs", r"^(J|F|TP)([0-9]|_)"))
        rad = float(cfg.get("silk_fn_radius_mm", 8.0))
        texts = [(MM(t.GetPosition().x), MM(t.GetPosition().y),
                  t.GetShownText(True, 0) if hasattr(t, "GetShownText")
                  else t.GetText())
                 for t in board.GetDrawings()
                 if t.GetClass() == "PCB_TEXT" and t.GetLayer() in SILKS]
        fam = []
        for f in board.GetFootprints():
            if not pat.match(f.GetReference()):
                continue
            bb = f.GetBoundingBox(False, False)
            # search radius scales with the part: big connectors get their
            # label near an edge of the body, not the centroid
            fam.append((f.GetReference(),
                        MM(f.GetPosition().x), MM(f.GetPosition().y),
                        rad + math.hypot(MM(bb.GetWidth()),
                                         MM(bb.GetHeight())) / 2))
        unlabeled, misowned, leads = [], [], []
        for r, fx, fy, eff in fam:
            near = [(math.hypot(tx - fx, ty - fy), tx, ty, txt)
                    for tx, ty, txt in texts
                    if math.hypot(tx - fx, ty - fy) < eff]
            if not near:
                unlabeled.append(r)
                continue
            best = None      # (lead, dist, text) over texts THIS part owns
            stolen = []
            for d, tx, ty, txt in sorted(near):
                rival = sorted((math.hypot(tx - ox, ty - oy), orf)
                               for orf, ox, oy, _e in fam if orf != r)
                # a one-member family owns everything nearby by default; the
                # lead is capped so the report carries a number and not `inf`
                rd, rref = rival[0] if rival else (d + 99.9, "no rival")
                if rd < d:
                    stolen.append(f"{r}: silk {txt[:22]!r} is {d:.2f}mm from "
                                  f"{r} but {rd:.2f}mm from {rref}")
                elif best is None or (rd - d) > best[0]:
                    best = (rd - d, d, txt)
            if best is None:
                misowned.append(stolen[0] if stolen else
                                f"{r}: no owned silk text")
            else:
                leads.append((best[0], f"{r} owns {best[2][:22]!r} by "
                                       f"{best[0]:.2f}mm"))
        thinnest = min(leads)[1] if leads else "nothing"
        grade("P-SILK-FN", not unlabeled,
              f"every connector/fuse/TP has functional silk nearby — "
              f"{len(fam)} in the {pat.pattern!r} family graded",
              f"no functional silk text within {rad}mm(+body) of: "
              f"{unlabeled[:10]} ({len(unlabeled)}/{len(fam)})")
        # ---- OWNERSHIP IS ITS OWN ROW, for P-ADJ-UNREACHED's reason --------
        # FOUR boards in this fleet hold a P-SILK-FN waiver (cooksense live,
        # plus lipo3s-tsc / usb-power-3s / xt60-usb-supply-rerun archived), and
        # every one of them is evidenced on PRESENCE — "these refs carry no
        # separate legend, here is why". Ownership is a different class, and
        # measured on the fleet 2026-07-29 it is not a small one: 55 misowned
        # labels across 11 of 23 boards, including 12 on cooksense's interposer
        # and 5 on cooksense itself. Reporting them under P-SILK-FN would have
        # let those four waivers swallow the lot on the first run — canon M4's
        # inherited-defect pattern, which is what the P-ADJ-UNREACHED split
        # exists to prevent. It is also separately WAIVABLE on purpose: a
        # single legend deliberately covering a BANK ("PTC" over ten fuses on
        # crow-array-central) is a real authoring choice, and it needs to say so
        # with its measurement rather than be silently graded green.
        if fam:
            grade("P-SILK-OWN", not misowned,
                  f"every {pat.pattern!r} part's nearest legend is ITS OWN — "
                  f"{len(leads)}/{len(fam)} own a label; thinnest ownership "
                  f"lead: {thinnest}",
                  f"LABEL ON THE WRONG PART ({len(misowned)}/{len(fam)}): "
                  f"{misowned[:6]} — a legend nearer another {pat.pattern!r} "
                  f"part misdirects whoever plugs the cable in. MOVE it (do "
                  f"not add a second), or waive with the measured pair of "
                  f"distances + why it is one legend for a bank")
        else:
            rows.append(("P-SILK-OWN", "N-A",
                         f"no {pat.pattern!r} parts on this board"))

        cu = board.GetCopperLayerCount()
        if cu >= 4:
            in1 = board.GetLayerID("In1.Cu")
            in1_tracks = sum(1 for t in board.GetTracks()
                             if t.GetClass() == "PCB_TRACK" and t.GetLayer() == in1)
            grade("P-PLANE", in1_tracks == 0,
                  "In1 carries only its plane (0 tracks)",
                  f"{in1_tracks} tracks on In1 reference plane")
        else:
            rows.append(("P-PLANE", "N-A", "2-layer: see R-PLANE regions"))

        regions = cfg.get("plane_regions", [])
        if regions:
            bad = []
            for rg in regions:
                lay = board.GetLayerID(rg["layer"])
                anchor = board.FindFootprintByReference(rg["ref"])
                if not anchor:
                    continue
                axc, ayc = MM(anchor.GetPosition().x), MM(anchor.GetPosition().y)
                tot_len = 0.0
                for t in board.GetTracks():
                    if t.GetClass() != "PCB_TRACK" or t.GetLayer() != lay:
                        continue
                    if t.GetNetname() == "GND":
                        continue
                    mx = (MM(t.GetStart().x) + MM(t.GetEnd().x)) / 2
                    my = (MM(t.GetStart().y) + MM(t.GetEnd().y)) / 2
                    if math.hypot(mx - axc, my - ayc) < rg["radius_mm"]:
                        tot_len += MM(int(t.GetLength()))
                if tot_len > rg["max_len_mm"]:
                    bad.append(f"{rg['ref']}@{rg['layer']}: {tot_len:.1f}mm "
                               f"signal in plane (max {rg['max_len_mm']})")
            grade("R-PLANE", not bad, "named-region plane continuity OK",
                  "; ".join(bad))
        else:
            rows.append(("R-PLANE", "N-A" if cu >= 4 else "HUMAN",
                         "no plane_regions configured"
                         + ("" if cu >= 4 else " — configure for 2-layer boards")))

        # R-POUR: nets in HIGH-CURRENT netclasses (track width >= 0.5mm,
        # excluding Default) must be carried by pours or hold a waiver.
        # Name-matching alone flagged codec-internal VCC pin nets — the
        # netclass is the design's own declaration of what carries current.
        znets = {z.GetNetname() for z in board.Zones()}
        pwr = set()
        prof = Path(board_p).with_suffix(".kicad_pro")
        if prof.exists():
            pro = json.loads(prof.read_text(encoding="utf-8-sig"))
            ns = pro.get("net_settings", {})
            pats = ns.get("netclass_patterns", [])
            for cl in ns.get("classes", []):
                if cl.get("name") == "Default":
                    continue
                if float(cl.get("track_width", 0)) < 0.5:
                    continue
                cl_pats = [p["pattern"] for p in pats
                           if p.get("netclass") == cl["name"]]
                for n in copper_nets:
                    for cp in cl_pats:
                        if re.fullmatch(cp.replace("*", ".*"), n):
                            pwr.add(n)
        nopour = sorted(pwr - znets)
        grade("R-POUR", not nopour,
              f"high-current-class nets all poured ({len(pwr)} nets)",
              f"high-current-class nets with no pour: {nopour[:6]}")

        # R-THERM: only meaningful where an internal plane exists to sink
        # into (>=4 layers), and only for multi-pin parts (a 2-pad
        # electrolytic's big pads are terminals, not thermal pads)
        area_min = float(cfg.get("therm_pad_area_mm2", 4.0))
        min_vias = int(cfg.get("therm_min_vias", 2))
        search = float(cfg.get("therm_search_mm", 1.0))
        vias = [(MM(t.GetPosition().x), MM(t.GetPosition().y), t.GetNetname())
                for t in board.GetTracks() if t.GetClass() == "PCB_VIA"]
        cold = []
        for f in (board.GetFootprints() if cu >= 4 else []):
            if len([p for p in f.Pads() if p.GetNumber()]) <= 2:
                continue
            for p in f.Pads():
                if p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                    continue
                w, h = MM(p.GetSizeX()), MM(p.GetSizeY())
                if w * h < area_min or not p.GetNetname():
                    continue
                px, py = MM(p.GetPosition().x), MM(p.GetPosition().y)
                n = sum(1 for vx, vy, vn in vias
                        if vn == p.GetNetname()
                        and abs(vx - px) < w / 2 + search
                        and abs(vy - py) < h / 2 + search)
                if n < min_vias:
                    cold.append(f"{f.GetReference()}.{p.GetNumber()}({n})")
        if cu >= 4:
            grade("R-THERM", not cold,
                  f"all pads >={area_min}mm2 have >={min_vias} nearby same-net vias",
                  f"underserved power pads: {cold[:8]}")
        else:
            rows.append(("R-THERM", "N-A",
                         "2-layer: no internal plane to sink into"))
    else:
        for cid in ("P-SILK-REF", "P-SILK-FN", "P-SILK-OWN", "P-PLANE",
                    "R-PLANE",
                    "R-POUR", "R-THERM"):
            rows.append((cid, "N-A", "no board"))

    # R-RULES: routing-input project must contain the netclasses
    rp_glob = cfg.get("route_pro_glob", "")
    cands = (glob.glob(str(proj / rp_glob)) if rp_glob else
             glob.glob(str(proj / "06_build/route/*.kicad_pro"))
             + glob.glob(str(proj / "03_src/route/*.kicad_pro")))
    if cands:
        ok, det = False, ""
        for c in sorted(cands)[:1]:
            pro = json.loads(Path(c).read_text(encoding="utf-8-sig"))
            classes = pro.get("net_settings", {}).get("classes", [])
            names = [cl.get("name") for cl in classes]
            ok = len(classes) > 1
            det = f"{Path(c).name}: classes={names}"
        # ...AND every rule in the shipped .kicad_dru must be ABLE to fire.
        # A rule conditioning on a netclass the project does not define, or on
        # a rule area not on the board, enforces NOTHING while reading as
        # enforcement — and DRC still reports 0, so the green number is partly
        # vacuous for exactly the nets that rule names. Measured on
        # crow-mic-pod-v2 v1.0: 2 of its 4 rules dead, and the board carries 3
        # tracks 0.0002mm under the floor the dead rule was written to enforce.
        # Same ID rather than a new one: "the generated rules are the rules
        # that are actually in force" is what R-RULES already means.
        try:
            import rules_audit as _ra
            _dru = next(iter(sorted((proj / "04_kicad").glob("*.kicad_dru"))), None)
            _pro = next(iter(sorted((proj / "04_kicad").glob("*.kicad_pro"))), None)
            _pcb = next(iter(sorted((proj / "04_kicad").glob("*.kicad_pcb"))), None)
            if _dru and _pro:
                _cls = {c.get("name") for c in
                        (json.loads(_pro.read_text(encoding="utf-8-sig")).get("net_settings") or {})
                        .get("classes") or []}
                _fire = _ra.unfireable_rules(
                    _dru.read_text(encoding="utf-8-sig"), _cls,
                    _pcb.read_text(encoding="utf-8-sig") if _pcb else "",
                    _pcb.name if _pcb else "the board")
                if _fire:
                    ok = False
                    det = f"{len(_fire)} rule(s) CANNOT FIRE: " + \
                          "; ".join(f[:150] for f in _fire[:2])
        except Exception as e:                       # never mask the base check
            det += f" (A-FIRE sub-check unavailable: {e})"
        grade("R-RULES", ok, det, det if "CANNOT FIRE" in det else
              f"route-input has only Default class ({det})")
    else:
        rows.append(("R-RULES", "N-A", "no route-input .kicad_pro found"))
    rows.append(("R4", "HUMAN", "escape-first routing order — design review "
                 "(feasibility itself is machine-checked: P-ESC/P-TIER)"))
    has_len = bool(re.search(r"length|spread", audit_src, re.I))
    rows.append(("R-LEN", "PASS" if has_len else "N-A",
                 "length-spread audit present in 03_src" if has_len
                 else "no timing-critical nets declared"))

    # ---------------- electrical (the netlist must match INTENT) ----------
    # E-INV/E-ADR: the D1 reverse-polarity defect (usb-hub-3s v1.0) passed ERC,
    # DRC, parity, twin AND pin review — every artifact was consistently wrong
    # TOGETHER; only intent-vs-netlist disagreed. electrical_invariants.py makes
    # ADR intent executable against the exported netlist.
    einv = Path(__file__).resolve().parent / "electrical_invariants.py"
    invp = proj / "03_src" / "rules" / "electrical_invariants.yaml"
    if not invp.exists():
        rows.append(("E-INV", "N-A", "no 03_src/rules/electrical_invariants.yaml"))
    else:
        r = sh([sys.executable, str(einv), str(proj)])
        detail = (r.stdout + r.stderr).strip().replace("\n", " ")[:200]
        grade("E-INV", r.returncode == 0,
              detail or "invariants hold against the netlist",
              detail or "electrical_invariants check failed")
    # E-ADR: every protection/topology ADR must be cited by an invariant
    dec = proj / "01_docs" / "decisions"
    if not dec.is_dir():
        rows.append(("E-ADR", "N-A", "no 01_docs/decisions/"))
    else:
        r = sh([sys.executable, str(einv), str(proj), "--adr-coverage"])
        detail = (r.stdout + r.stderr).strip().replace("\n", " ")[:200]
        if "N-A" in detail:
            rows.append(("E-ADR", "N-A", detail))
        else:
            grade("E-ADR", r.returncode == 0,
                  detail or "protection ADRs all cited by an invariant",
                  detail or "a protection/topology ADR emitted no invariant")

    # E-TOPO: converter TOPOLOGY must be DERIVED from Vin-vs-Vout, not
    # interpreted. usb-hub-3s (2026-07-22): an IP6559 BUCK-BOOST + 16A trunk on
    # a 5V-only USB-C port where Vout(5) < Vin_min(9) ALWAYS => a plain buck
    # suffices; the buck-boost existed only for >5V PDOs the spec never pinned.
    ptop = Path(__file__).resolve().parent / "power_topology.py"
    ptp = proj / "03_src" / "rules" / "power_tree.yaml"
    if not ptp.exists():
        rows.append(("E-TOPO", "N-A", "no 03_src/rules/power_tree.yaml"))
    else:
        r = sh([sys.executable, str(ptop), str(proj)])
        detail = (r.stdout + r.stderr).strip().replace("\n", " ")[:200]
        grade("E-TOPO", r.returncode == 0,
              detail or "every rail's converter topology matches Vin-vs-Vout",
              detail or "a converter topology does not match the derived one "
              "(over-engineered or cannot-meet)")

    # E-MARGIN: a regulated rail feeding a KNOWN load must clear the load's
    # brownout with real IR headroom. usb-hub-3s-v3 (2026-07-23): a 4.97V rail
    # fed a Pi5 (UV ~4.63V) at 5A -> only ~68 mOhm for board+connector+cable IR
    # drop; both zero-context reviews COMPUTED 4.97V, neither flagged the margin.
    if not ptp.exists():
        rows.append(("E-MARGIN", "N-A", "no 03_src/rules/power_tree.yaml"))
    else:
        r = sh([sys.executable, str(ptop), str(proj), "--margin"])
        detail = (r.stdout + r.stderr).strip().replace("\n", " ")[:200]
        if "N-A" in detail:
            rows.append(("E-MARGIN", "N-A", detail))
        else:
            grade("E-MARGIN", r.returncode == 0,
                  detail or "every load-margin rail clears its brownout with IR "
                  "margin",
                  detail or "an output setpoint leaves too little headroom for "
                  "the delivery IR drop at Imax")

    # E-OFF: a self-contained energy source (battery/cell/pack) must document
    # its de-energization path + bounded stored quiescent draw. usb-hub-3s-v3
    # (2026-07-23): a 3S-LiPo board tied both buck EN pins active with no master
    # switch -> the controllers idle-drain the pack in storage; no review asked.
    if not ptp.exists():
        rows.append(("E-OFF", "N-A", "no 03_src/rules/power_tree.yaml"))
    else:
        r = sh([sys.executable, str(ptop), str(proj), "--off-control"])
        detail = (r.stdout + r.stderr).strip().replace("\n", " ")[:200]
        if "N-A" in detail:
            rows.append(("E-OFF", "N-A", detail))
        else:
            grade("E-OFF", r.returncode == 0,
                  detail or "de-energization path + stored quiescent draw both "
                  "declared for the battery source",
                  detail or "a battery board declares no de-energization path / "
                  "stored quiescent draw (idle self-drain)")

    # ---------------- meta ----------------
    reb = proj / "03_src" / "rebuild_all.sh"
    if reb.exists():
        deps = re.findall(r"(0[36]_\w+/[\w./-]+\.kicad_pcb)", reb.read_text(encoding="utf-8-sig"))
        untracked, absent = [], []
        def tracked(path):
            return sh(["git", "ls-files", "--error-unmatch", str(path)],
                      cwd=str(proj)).returncode == 0
        for d in set(deps):
            # a 06_build dep counts as tracked when its PROMOTED 03_src/route
            # counterpart is committed (canon M3: 06_build copy is a cache)
            promoted = proj / "03_src" / "route" / Path(d).name
            if promoted.exists() and tracked(promoted):
                continue
            if not (proj / d).exists():
                absent.append(d)
                continue
            if not tracked(proj / d):
                untracked.append(d)
        if untracked:
            grade("M-REPRO", False, "",
                  f"rebuild depends on UNTRACKED artifacts: {untracked}")
        elif absent and board is None:
            rows.append(("M-REPRO", "N-A",
                         f"not yet routed (inputs pending: {absent})"))
        else:
            grade("M-REPRO", not absent,
                  "all rebuild inputs git-tracked",
                  f"rebuild inputs MISSING from tree: {absent}")
    else:
        rows.append(("M-REPRO", "FAIL", "no rebuild_all.sh"))

    # RELEASE SELECTION IS SCOPED TO THE BOARD UNDER AUDIT. Not to the last
    # directory in 07_releases — that is a property ADJACENT to the one this
    # gate names, and the difference is the whole defect class:
    #
    #  (a) MULTI-BOARD PROJECT. smc0985-cooksense/07_releases/ holds
    #      cooksense-v1.0…v1.4 AND interposer-v1.0. Under any order whose
    #      leading component is the board prefix, `interposer-…` lands last, so
    #      `rels[-1]` resolved to the INTERPOSER while everything above graded
    #      the COOKSENSE board. M-REL, M-BOM, A-POP and A-BODY all reported on
    #      the wrong archive, and M-REL demanded SUPERSEDED.md on
    #      cooksense-v1.4 — the LIVE release — which blocked the v1.5 seal.
    #      Measured 2026-07-27.
    #  (b) TEXT VERSION ORDER. "v1.10-…" sorts before "v1.9-…" because
    #      '1' < '9'. usb-hub-3s-v3 v1.10 (2026-07-27) had M-REL grade the
    #      superseded release and accuse the live one of being superseded.
    #
    # Both live in ONE place now — release_index.py, imported rather than
    # re-implemented, so no consumer of release ordering can disagree with
    # another (the same ONE-loader arrangement M-BOM has with bom_source_check
    # below). Board identity comes from the .kicad_pcb this audit LOADED, so
    # the release scope cannot drift from the board every other check graded.
    #
    # A release set it cannot attribute is a FAIL, never a silent pick
    # (canon M-COVER): an unparseable dir name, a prefix naming a board this
    # project does not build, or a bare name in a multi-board project.
    _jlc_scripts = (Path(__file__).resolve().parent.parent.parent
                    / "jlcpcb-fab" / "scripts")
    sys.path.insert(0, str(_jlc_scripts))
    import release_index as _relidx  # noqa: E402

    _reldir = proj / "07_releases"
    _all_reldirs = sorted(p for p in _reldir.glob("*") if p.is_dir()) \
        if _reldir.is_dir() else []
    _rel_error, latest = None, None
    try:
        rels = [str(p) for p in
                _relidx.releases_for_board(proj, board_name)]
    except _relidx.ReleaseSetError as e:
        rels, _rel_error = [], str(e)
    if _rel_error:
        grade("M-REL", False, "",
              f"release set UNRESOLVABLE, so no release was graded: "
              f"{_rel_error}")
        latest = None
    elif rels:
        latest = Path(rels[-1])
        man = latest / "MANIFEST.txt"
        probs = []
        if man.exists():
            mt = man.read_text(encoding="utf-8-sig")
            m = re.search(r"git_sha:\s*([^\s]+)", mt)
            sha = m.group(1) if m else ""
            if not re.fullmatch(r"[0-9a-f]{7,40}", sha):
                probs.append(f"git_sha not an exact commit: '{sha}'")
            elif sh(["git", "cat-file", "-e", sha], cwd=str(proj)).returncode != 0:
                probs.append(f"git_sha {sha} not in repo")
            # M-REL reads the manifest's SELF-REPORT. Two known weaknesses, both
            # met on usb-hub-3s-v3 v1.6 (2026-07-26):
            #
            # (a) BRITTLE FORMAT, fixed here. This matched two LITERAL spellings,
            #     so a stamp with six spaces failed a gate whose CONTENT was
            #     exactly right, and the message said "git_dirty not false" —
            #     pointing at the fact when the defect was the whitespace. It
            #     fails closed, which is the safe direction, but it cost a seal
            #     attempt and sent the reader hunting the wrong thing.
            #
            # (b) NOT YET FIXED, and the deeper one: this greps TEXT THE RELEASE
            #     WROTE ABOUT ITSELF. release_git_dirty.py scopes the real check
            #     to <project>/ + skills/ and emitted `true` for v1.6 (a peer's
            #     uncommitted generator edit), yet the manifest says `false` and
            #     M-REL PASSES, because it never asks the tool. A gate that
            #     validates its subject's self-report proves nothing (canon M1).
            #     The durable fix is to re-derive the flag at audit time against
            #     the manifest's own recorded git_sha and FAIL on disagreement.
            #     Deliberately not landed mid-flight with four agents in the tree;
            #     it must arrive with a known-bad fixture that goes RED against a
            #     hand-edited manifest.
            if not re.search(r"git_dirty:\s*false\b", mt, re.I):
                m_gd = re.search(r"git_dirty:\s*(\S+)", mt)
                probs.append(f"git_dirty is {m_gd.group(1)!r}, not false"
                             if m_gd else "no git_dirty line in MANIFEST")
            # (c) THE FLEET SHIPS TWO TABLE LAYOUTS AND THIS READ ONLY ONE.
            #     `'  '<path>  <hash>` is what crow-recorder-central-v2,
            #     crow-mic-pod-v2 and cooksense write; usb-hub-3s-v3 writes
            #     sha256sum order, `<hash>  <path>`. The pattern below used to
            #     require two leading spaces and path-first, so it matched
            #     ZERO of usb-hub-3s-v3's 76 entries — M-REL reported
            #     "provenance + hashes verify" on that board for all ten of its
            #     releases while verifying nothing. MEASURED 2026-07-27:
            #     66 / 80 / 57 entries matched on the other three boards, 0 on
            #     this one. A denominator that silently goes to zero is the
            #     M-COVER shape, so both layouts are read AND an empty table is
            #     now a FAIL in its own right.
            _hashed = 0
            for hm in re.finditer(
                    r"^(?:\s+(?P<p1>[\w./-]+)\s+(?P<h1>[0-9a-f]{16,64})"
                    r"|(?P<h2>[0-9a-f]{16,64})\s+(?P<p2>[\w./-]+))\s*$",
                    mt, re.M):
                rel_p = hm.group("p1") or hm.group("p2")
                want = hm.group("h1") or hm.group("h2")
                fp = latest / rel_p
                _hashed += 1
                if not fp.exists():
                    probs.append(f"missing hashed file {rel_p}")
                    continue
                h = sh(["sha256sum", str(fp)]).stdout.split()[0]
                if not h.startswith(want):
                    probs.append(f"sha256 mismatch {rel_p}")
            _n_files = sum(1 for p in latest.rglob("*")
                           if p.is_file() and p.name != "MANIFEST.txt")
            if _hashed == 0 and _n_files and "sha256:" in mt:
                probs.append(
                    f"sha256 table yielded ZERO readable entries against "
                    f"{_n_files} file(s) on disk — a gate that verifies "
                    f"nothing must not report that hashes verify (M-COVER)")
        else:
            probs.append("no MANIFEST.txt")
        # The CHANGELOG is a PROJECT document, so it is checked against EVERY
        # release directory, not just this board's series — scoping it to the
        # audited board would drop the sibling board's entries from coverage
        # unless someone remembered to run the audit again with --board.
        cl = proj / "01_docs" / "CHANGELOG.md"
        for rd in _all_reldirs:
            if cl.exists() and rd.name not in cl.read_text(encoding="utf-8-sig"):
                probs.append(f"CHANGELOG missing entry for {rd.name}")
        # SUPERSEDED.md, by contrast, is a WITHIN-SERIES claim: only THIS
        # board's earlier releases are superseded by THIS board's latest.
        for rd in rels[:-1]:
            if not (Path(rd) / "SUPERSEDED.md").exists():
                probs.append(f"{Path(rd).name} lacks SUPERSEDED.md")
        if not (latest / "verification").is_dir() or \
                not any((latest / "verification").iterdir()):
            probs.append("verification/ empty")
        grade("M-REL", not probs,
              f"{latest.name}: provenance + hashes verify "
              f"(board {board_name!r}: {len(rels)} of {len(_all_reldirs)} "
              f"release dir(s) in 07_releases)",
              "; ".join(probs[:6]))
    elif _all_reldirs:
        rows.append(("M-REL", "N-A",
                     f"no release for board {board_name!r} "
                     f"({len(_all_reldirs)} dir(s) in 07_releases belong to "
                     f"other boards)"))
    else:
        rows.append(("M-REL", "N-A", "no releases yet"))

    # M-BOM: the ORDERABLE BOM's per-refdes LCSC code must EQUAL the source's
    # (circuit.json) — a merged row (2 refdes, 2 source codes, 1 line), a
    # substituted code, or a blank code where the source has one is silent BOM
    # corruption. usb-hub-3s-v3 v1.1 shipped 25V input caps for 50V because the
    # exporter grouped by value+footprint and collapsed C77102 onto C77100.
    # The check RE-DERIVES from the source independently of how the BOM was made
    # (canon M1), so it bites carry-over/hand-edit corruption too. Leg C adds
    # SEMANTIC value consistency: each R/C row's catalog value is resolved
    # (BOM MPN column -> vendored part.yaml dir name -> the vetted
    # jlcpcb-fab/references/lcsc_passives_ledger.yaml, catalog-verified once
    # per code) and FAILS a value that disagrees with the label (usb-hub-3s-v3
    # v1.2 shipped C2933210=3.74k labeled 4.12k), flagging a row no source
    # resolves rather than passing it — all offline.
    jlc_scripts = Path(__file__).resolve().parent.parent.parent / "jlcpcb-fab" / "scripts"
    cjs = (glob.glob(str(proj / "03_tscircuit" / "build" / "circuit.json"))
           or glob.glob(str(proj / "03_tscircuit" / "dist" / "**" / "circuit.json"),
                        recursive=True))
    # the orderable artifact: prefer THIS BOARD's latest sealed release, else
    # the build. An UNRESOLVABLE release set falls through to neither — the
    # gate says so rather than quietly grading 06_build as if it were sealed.
    fab_bom = next((b for b in
                    [str(latest / "fab" / "bom.csv") if latest else "",
                     str(proj / "06_build" / "fab" / "bom.csv"),
                     str(proj / "06_build" / "fab" / "bom_jlc.csv")]
                    if b and Path(b).exists()), None)
    if _rel_error:
        rows.append(("M-BOM", "FAIL",
                     f"cannot identify the orderable BOM: {_rel_error}"))
    elif not cjs or not fab_bom:
        rows.append(("M-BOM", "N-A", "no circuit.json source or no fab BOM"))
    else:
        try:
            sys.path.insert(0, str(jlc_scripts))
            import bom_source_check as _bsc
            refdes_code = _bsc.refdes_codes_from_circuit(cjs[0])
            vendored = _bsc.vendored_primary_codes(proj / "02_parts")
            # refdes DECLARED not_assembled are EXPECTED off the assembly BOM
            # (canon A-POP) — without this, leg B reports DROPPED on exactly
            # the rows a correct assembly.yaml says to remove, which pressures
            # the operator into putting an unsourceable row back on the BOM.
            unpop = _bsc.load_not_assembled(proj / "03_src/rules/assembly.yaml")
            probs = _bsc.check(_bsc.read_bom(fab_bom), refdes_code, vendored,
                               None, unpop)
            grade("M-BOM", not probs,
                  f"{Path(fab_bom).parent.parent.name}/fab/bom.csv: "
                  f"every LCSC == source ({sum(1 for v in refdes_code.values() if v)} coded)",
                  f"{len(probs)} BOM-vs-source defect(s): " + " || ".join(probs[:3]))
        except Exception as e:
            rows.append(("M-BOM", "FAIL", f"bom_source_check errored: {e}"))

    # A-POP: the population set is DECLARED, not emergent (canon A-POP; PCBA
    # is the deliverable). Grades the ORDERABLE artifacts — the latest sealed
    # release when there is one, else the staged 06_build/fab set — and
    # re-derives {board} - {CPL} from the BOARD text and the CPL bytes, never
    # from the exporter that produced them (canon M1). Until 2026-07-25
    # nothing in this repo had ever read a cpl.csv back, and cooksense v1.1
    # sealed 13 blank-LCSC parts onto its CPL past every gate.
    _asm_target = str(latest) if latest else str(proj)
    _fab_ready = (rels or (proj / "06_build" / "fab" / "cpl_jlc.csv").exists()
                  or (proj / "06_build" / "fab" / "cpl.csv").exists())
    if _rel_error:
        rows.append(("A-POP", "FAIL",
                     f"cannot identify the orderable CPL: {_rel_error}"))
    elif not _fab_ready:
        rows.append(("A-POP", "N-A", "no CPL exported yet"))
    else:
        r = sh([sys.executable, str(jlc_scripts / "assembly_coverage.py"),
                _asm_target])
        head = [l for l in (r.stdout + r.stderr).splitlines()
                if l.strip().startswith(("UNDECLARED", "DECLARED", "POS-ATTR",
                                         "UNCODED", "CPL-NO", "BAD-REASON",
                                         "NO-EVIDENCE", "CONSIGN",
                                         "MANIFEST-", "NO-ASSEMBLY"))]
        grade("A-POP", r.returncode == 0,
              f"{Path(_asm_target).name}: "
              + next((l.strip() for l in r.stdout.splitlines()
                      if l.startswith("A-POP:")), "PASS"),
              f"{len(head)} finding(s): " + " || ".join(h.strip()[:120]
                                                        for h in head[:3]))

    # M-DEPEND: a SEALED release may not depend on a mutable fact it does not
    # carry. This is the ONE release-scoped row that deliberately grades ALL of
    # the project's sealed releases and not just `latest` — the victims of a
    # `git rm` in `02_parts/` are the OLD releases, and v1.6 does not stop being
    # orderable because v1.7 exists. cooksense v1.7's work removed
    # `02_parts/ULN2803ADWR/` (legitimately — ADR-0023 replaced the driver) and
    # the immutable, byte-unchanged `cooksense-v1.6-2026-07-27` flipped F-MPN
    # PASS -> FAIL on row 56 (C9683), then flipped BACK when the dossier was
    # restored, with nothing recording that it had been red. The trigger is not
    # only a deletion: `02_parts/MCP23017-E-SS` was EDITED. Offline, no pcbnew,
    # no git — it grades STATE, which is what reaches an already-committed
    # deletion (2 of 33 fleet releases are broken that way today).
    _reldirs_any = bool(_all_reldirs)
    if not _reldirs_any:
        rows.append(("M-DEPEND", "N-A", "no releases yet"))
    else:
        r = sh([sys.executable, str(jlc_scripts / "sealed_dependency_check.py"),
                str(proj)] + (["--board", board_name] if board_name else []))
        head = [l.strip() for l in (r.stdout + r.stderr).splitlines()
                if l.startswith(("M-DEPEND ORPHAN", "M-DEPEND UNPINNED"))]
        cov = next((l.strip() for l in r.stdout.splitlines()
                    if l.startswith("M-DEPEND coverage:")), "no coverage line")
        grade("M-DEPEND", r.returncode == 0, cov,
              f"{len(head)} sealed row(s) whose MPN authority the live tree can "
              f"no longer supply: " + " || ".join(h[:150] for h in head[:3]))

    # A-BODY: every CPL placement ends up with a 3D body a renderer can load
    # (canon A-BODY). OFFLINE, like A-STOCK — it grades the EVIDENCE the
    # release ships, because a gate that needs the network is a gate that gets
    # skipped. The header jlc_twin writes is what makes the file falsifiable:
    # usb-hub-3s-v3 v1.5's copy was HAND-WRITTEN and stated the gap was zero
    # while 7 of 108 placements rendered nothing, so a missing/unparseable
    # counter is a FAIL, not a skip.
    _mm = None
    for _c in ([latest / "verification" / "missing_models.txt"] if latest
               else []) \
            + [proj / "06_build" / "twin" / "missing_models.txt",
               proj / "06_build" / "verification" / "missing_models.txt"]:
        if _c.exists():
            _mm = _c
            break
    if _rel_error:
        rows.append(("A-BODY", "FAIL",
                     f"cannot identify the release to read bodies from: "
                     f"{_rel_error}"))
    elif _mm is None:
        rows.append(("A-BODY", "N-A", "no twin run / missing_models.txt yet"))
    else:
        _t = _mm.read_text(encoding="utf-8-sig")
        _m = re.search(r"bodies mounted:\s*(\d+)\s*/\s*(\d+)", _t)
        if "GENERATED by jlc_twin" not in _t or not _m:
            grade("A-BODY", False, "",
                  f"{_mm.parent.parent.name}/{_mm.name} carries no generated "
                  f"`bodies mounted: N/M` header — it was hand-authored or "
                  f"predates the NO-BODY gate, so its counters grade nothing")
        else:
            _got, _want = int(_m.group(1)), int(_m.group(2))
            grade("A-BODY", _got == _want,
                  f"{_mm.parent.parent.name}: bodies mounted {_got}/{_want} "
                  f"(generated)",
                  f"{_want - _got} of {_want} CPL placements have NO 3D body: "
                  + ", ".join(l.split("\t")[0] for l in _t.splitlines()
                              if l and not l.startswith("#"))[:200])

    # M-JRNL / M-LEARN: per-stage diary + harvest sources (canon M9). Scoped
    # to commissioned projects (01_docs exists) — scratch/test trees exempt.
    docs = proj / "01_docs"
    if docs.is_dir():
        started = bool(boards) or (proj / "03_src" / "route").is_dir()
        jrn = [j for j in sorted((docs / "journal").glob("*.md"))
               if j.name != "contracts.md"] if (docs / "journal").is_dir() else []
        entries = sum(1 for j in jrn if "## " in j.read_text(encoding="utf-8-sig"))
        if not started:
            rows.append(("M-JRNL", "N-A", "no board/route artifacts yet"))
        else:
            grade("M-JRNL", entries > 0,
                  f"{len(jrn)} stage journals, {entries} with entries",
                  "design is generating artifacts but 01_docs/journal/ has no "
                  "stage entries — every start/iteration/finish must journal "
                  "(canon M9)")
        if rels or _all_reldirs:
            lrn = [l for l in sorted((docs / "learnings").glob("*.md"))
                   if l.name != "contracts.md"] if (docs / "learnings").is_dir() else []
            grade("M-LEARN", bool(lrn),
                  f"{len(lrn)} stage learnings files",
                  "released with no 01_docs/learnings/<stage>.md — completion "
                  "requires the harvest source (canon M9)")
        else:
            rows.append(("M-LEARN", "N-A", "no release yet"))
    else:
        rows.append(("M-JRNL", "N-A", "no 01_docs (not a commissioned project)"))
        rows.append(("M-LEARN", "N-A", "no 01_docs"))

    adjp = proj / "03_src/rules/twin_adjudications.yaml"
    if adjp.exists() and yaml:
        entries = yaml.safe_load(adjp.read_text(encoding="utf-8-sig")) or []
        thin = [e.get("lcsc") for e in entries
                if len(str(e.get("why", ""))) < 40]
        grade("M-WAIV", not thin, f"{len(entries)} adjudications, all evidenced",
              f"adjudications without evidence: {thin}")
    else:
        rows.append(("M-WAIV", "N-A", "no adjudication file"))
    rows.append(("M1", "HUMAN", "independent-reference coverage — release review"))
    rows.append(("M6", "HUMAN", "authoritative-source discipline — encoded in protocols"))

    # ---------------- report ----------------
    counts = {}
    for _, g, _ in rows:
        counts[g] = counts.get(g, 0) + 1
    summary = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
    # NAME THE BOARD GRADED. A multi-board project produces one report per
    # board, and the release-scoped rows (M-REL/M-BOM/A-POP/A-BODY) only mean
    # anything once the reader knows which board this run was about.
    _board_line = (f"Board graded: {board_name} "
                   + (f"(of {len(boards)} in 04_kicad: "
                      f"{', '.join(sorted(Path(b).stem for b in boards))}; "
                      f"select with --board)" if len(boards) > 1 else "")
                   ) if board_name else "Board graded: none (no 04_kicad board)"
    lines = [f"# Policy audit — {proj.name}", "",
             f"Generated by policy_audit.py; canon: design-policies.md", "",
             _board_line, "",
             "| ID | Grade | Detail |", "|---|---|---|"]
    for cid, g, det in rows:
        lines.append(f"| {cid} | {g} | {cell(det)} |")
    lines += ["", "Summary: " + summary]
    text = "\n".join(lines) + "\n"

    # WRITE ATOMICALLY, AND ONLY AFTER stdout IS FLUSHED. Both halves are
    # load-bearing — crow-mic-pod-v2 v1.0 sealed a policy_audit.md with a
    # 51-byte splice at offset 387 that DELETED the P-TIER row and left its
    # tail orphaned on the next line, so the file's own Summary (PASS=23)
    # could not be reconstructed from its own table (PASS=22). The MANIFEST
    # hash verified: it was GENERATED corrupt, then faithfully hashed.
    #
    # MECHANISM (measured 2026-07-25): the report is written to a path that
    # was ALSO this process's redirected stdout. `import pcbnew` writes to
    # that fd at C level, advancing the SHARED file offset to 387; write_text
    # then wrote the whole report from offset 0 through its own fd; and at
    # interpreter exit Python's block-buffered stdout flushed its 51-byte
    # summary line at offset 387 — INTO the finished report.
    #
    # A read-back placed here would NOT have caught it: the splice happens at
    # process exit, after any check we could run. So the fix is structural.
    # os.replace() installs a NEW inode, so a stale fd still pointing at the
    # old one cannot reach the published file no matter when it flushes.
    sys.stdout.flush()
    sys.stderr.flush()
    dest = build / "policy_audit.md"
    tmp = dest.with_suffix(".md.tmp")
    tmp.write_text(text)
    os.replace(tmp, dest)

    # SELF-CONSISTENCY: the Summary must be reconstructable FROM THE TABLE AS
    # WRITTEN, re-read off disk — not from the in-memory counts that produced
    # it. A summary computed from `rows` can only ever agree with itself; that
    # is what let the corrupt file ship with a headline nobody could derive.
    bad = report_inconsistencies(dest.read_text(encoding="utf-8-sig"), len(rows), counts)
    if bad:
        print(f"policy_audit: REPORT CORRUPT — {dest}", file=sys.stderr)
        for b in bad:
            print(f"  {b}", file=sys.stderr)
        sys.exit(2)

    print(f"{proj.name}: " + summary)
    for cid, g, det in rows:
        if g == "FAIL":
            print(f"  FAIL {cid}: {det[:110]}")
    sys.exit(1 if counts.get("FAIL") else 0)


if __name__ == "__main__":
    main()
