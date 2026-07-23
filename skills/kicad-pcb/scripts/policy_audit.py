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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--config", default="")
    ap.add_argument("--skip-drc", action="store_true",
                    help="skip the kicad-cli ERC/DRC runs (fast re-grade)")
    args = ap.parse_args()
    proj = Path(args.project).resolve()
    cfgp = Path(args.config) if args.config else proj / "03_src/rules/policy_audit.json"
    cfg = json.loads(cfgp.read_text()) if cfgp.exists() else {}
    build = proj / "06_build"
    build.mkdir(exist_ok=True)

    boards = sorted(glob.glob(str(proj / "04_kicad" / "*.kicad_pcb")))
    schs = sorted(glob.glob(str(proj / "04_kicad" / "*.kicad_sch")))
    board_p = boards[0] if boards else None
    sch_p = schs[0] if schs else None

    waivers = []
    wp = proj / "03_src/rules/policy_waivers.yaml"
    if wp.exists() and yaml:
        waivers = yaml.safe_load(wp.read_text()) or []
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
            d = json.loads(out.read_text())
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

    weak, tot = [], 0
    for py in sorted(glob.glob(str(proj / "02_parts" / "*" / "part.yaml"))):
        txt = Path(py).read_text()
        # 2-pad passives need no figure citation (no pinout to mirror)
        npins = 0
        if yaml:
            try:
                y = yaml.safe_load(txt) or {}
                npins = len(y.get("pins") or {})
            except Exception:
                npins = 0
        if npins and npins <= 2:
            continue
        m = re.search(r'verified:\s*["\']?(.{0,300})', txt, re.S)
        if not m:
            weak.append(Path(py).parent.name + " (missing)")
            tot += 1
            continue
        tot += 1
        note = m.group(1)
        if not re.search(r"(fig(ure)?\.?\s*[\dA-Z-]|table\s*[\d-]|p\.?\s*\d|page\s*\d|drawing)",
                         note, re.I):
            weak.append(Path(py).parent.name)
    if tot:
        grade("S-VER", not weak, f"{tot}/{tot} verified: cite figure/page",
              f"weak/missing figure citations: {weak[:8]} ({len(weak)}/{tot})")
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
            declared = (yaml.safe_load(netsy.read_text()) or {}).get("fab_tier")
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
                y = yaml.safe_load(Path(py).read_text()) or {}
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
            y = yaml.safe_load(Path(py).read_text()) or {}
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

        # P-ADJ: board net-spans vs each layout keep_short budget
        if board:
            netpads = {}
            for f in board.GetFootprints():
                for p in f.Pads():
                    n = p.GetNetname()
                    if n:
                        netpads.setdefault(n, []).append(
                            (MM(p.GetPosition().x), MM(p.GetPosition().y)))
            viol = []
            for py in part_yamls:
                y = yaml.safe_load(Path(py).read_text()) or {}
                for ks in ((y.get("layout") or {}).get("keep_short") or []):
                    net, mx = ks.get("net"), float(ks.get("max_span_mm", 6))
                    pts = netpads.get(net) or []
                    if len(pts) < 2:
                        continue
                    span = max(math.hypot(a[0] - b[0], a[1] - b[1])
                               for a in pts for b in pts)
                    if span > mx + 1e-6:
                        viol.append(f"{net} span {span:.1f}mm > {mx}mm "
                                    f"({ks.get('why', '')})")
            grade("P-ADJ", not viol,
                  "board honours every layout keep_short net-span budget",
                  f"datasheet layout budgets exceeded: {viol[:5]} — re-place per "
                  f"the part's layout: block (targets HARD against the chip), or "
                  f"waive with the measured span + why (P-ADJ)")
        else:
            rows.append(("P-ADJ", "N-A", "no board"))
    else:
        rows.append(("P-LAYOUT", "N-A", "no 02_parts entries"))
        rows.append(("P-ADJ", "N-A", "no 02_parts entries"))

    # S-OCCL: schematic text occlusions — global-label plates vs each other
    # and vs symbol Reference/Value property texts (approx bboxes; the same
    # ground-truth-geometry philosophy as the board silk de-collision).
    if sch_p:
        stxt = Path(sch_p).read_text()
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
            drc = json.loads(out.read_text())
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
        audit_src = ab.read_text()
        for extra in glob.glob(str(proj / "03_src" / "rules" / "audit*.json")):
            audit_src += Path(extra).read_text()
    if board is None:
        rows.append(("P-POL", "N-A", "no board yet"))
        rows.append(("P-KEEP", "N-A", "no board yet"))
    else:
        has_pol = bool(re.search(r"polarit|pad.?1.*net|pad1.*=", audit_src, re.I))
        pol_alt = bool(re.search(r"polarity_audit",
                       (proj / "03_src" / "generate_schematic.py").read_text()
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
        waived_refs = set(json.loads(wv.read_text())) if wv.exists() else set()
        for f in board.GetFootprints():
            r = f.GetReference()
            if r.startswith("H") or r in waived_refs:
                continue
            ref = f.Reference()
            if ref.GetLayer() not in SILKS or not ref.IsVisible():
                missing.append(r)
        grade("P-SILK-REF", not missing,
              "all refdes on visible silk",
              f"{len(missing)} refdes not on silk: {missing[:8]}")

        pat = re.compile(cfg.get("silk_fn_refs", r"^(J|F|TP)[0-9]"))
        rad = float(cfg.get("silk_fn_radius_mm", 8.0))
        texts = [(MM(t.GetPosition().x), MM(t.GetPosition().y))
                 for t in board.GetDrawings()
                 if t.GetClass() == "PCB_TEXT" and t.GetLayer() in SILKS]
        unlabeled = []
        for f in board.GetFootprints():
            r = f.GetReference()
            if not pat.match(r):
                continue
            fx, fy = MM(f.GetPosition().x), MM(f.GetPosition().y)
            bb = f.GetBoundingBox(False, False)
            # search radius scales with the part: big connectors get their
            # label near an edge of the body, not the centroid
            eff = rad + math.hypot(MM(bb.GetWidth()), MM(bb.GetHeight())) / 2
            if not any(math.hypot(tx - fx, ty - fy) < eff for tx, ty in texts):
                unlabeled.append(r)
        grade("P-SILK-FN", not unlabeled,
              "every connector/fuse/TP has functional silk nearby",
              f"no functional silk text within {rad}mm of: {unlabeled[:10]}")

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
            pro = json.loads(prof.read_text())
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
        for cid in ("P-SILK-REF", "P-SILK-FN", "P-PLANE", "R-PLANE",
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
            pro = json.loads(Path(c).read_text())
            classes = pro.get("net_settings", {}).get("classes", [])
            names = [cl.get("name") for cl in classes]
            ok = len(classes) > 1
            det = f"{Path(c).name}: classes={names}"
        grade("R-RULES", ok, det, f"route-input has only Default class ({det})")
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
        deps = re.findall(r"(0[36]_\w+/[\w./-]+\.kicad_pcb)", reb.read_text())
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

    rels = sorted(glob.glob(str(proj / "07_releases" / "v*")))
    if rels:
        latest = Path(rels[-1])
        man = latest / "MANIFEST.txt"
        probs = []
        if man.exists():
            mt = man.read_text()
            m = re.search(r"git_sha:\s*([^\s]+)", mt)
            sha = m.group(1) if m else ""
            if not re.fullmatch(r"[0-9a-f]{7,40}", sha):
                probs.append(f"git_sha not an exact commit: '{sha}'")
            elif sh(["git", "cat-file", "-e", sha], cwd=str(proj)).returncode != 0:
                probs.append(f"git_sha {sha} not in repo")
            if "git_dirty:    false" not in mt and "git_dirty: false" not in mt:
                probs.append("git_dirty not false")
            for hm in re.finditer(r"^  ([\w./-]+)\s+([0-9a-f]{16,64})\s*$",
                                  mt, re.M):
                fp = latest / hm.group(1)
                if not fp.exists():
                    probs.append(f"missing hashed file {hm.group(1)}")
                    continue
                h = sh(["sha256sum", str(fp)]).stdout.split()[0]
                if not h.startswith(hm.group(2)):
                    probs.append(f"sha256 mismatch {hm.group(1)}")
        else:
            probs.append("no MANIFEST.txt")
        cl = proj / "01_docs" / "CHANGELOG.md"
        for rd in rels:
            name = Path(rd).name
            if cl.exists() and name not in cl.read_text():
                probs.append(f"CHANGELOG missing entry for {name}")
        for rd in rels[:-1]:
            if not (Path(rd) / "SUPERSEDED.md").exists():
                probs.append(f"{Path(rd).name} lacks SUPERSEDED.md")
        if not (latest / "verification").is_dir() or \
                not any((latest / "verification").iterdir()):
            probs.append("verification/ empty")
        grade("M-REL", not probs, f"{latest.name}: provenance + hashes verify",
              "; ".join(probs[:6]))
    else:
        rows.append(("M-REL", "N-A", "no releases yet"))

    # M-BOM: the ORDERABLE BOM's per-refdes LCSC code must EQUAL the source's
    # (circuit.json) — a merged row (2 refdes, 2 source codes, 1 line), a
    # substituted code, or a blank code where the source has one is silent BOM
    # corruption. usb-hub-3s-v3 v1.1 shipped 25V input caps for 50V because the
    # exporter grouped by value+footprint and collapsed C77102 onto C77100.
    # The check RE-DERIVES from the source independently of how the BOM was made
    # (canon M1), so it bites carry-over/hand-edit corruption too.
    jlc_scripts = Path(__file__).resolve().parent.parent.parent / "jlcpcb-fab" / "scripts"
    cjs = (glob.glob(str(proj / "03_tscircuit" / "build" / "circuit.json"))
           or glob.glob(str(proj / "03_tscircuit" / "dist" / "**" / "circuit.json"),
                        recursive=True))
    # the orderable artifact: prefer the latest sealed release, else the build
    fab_bom = next((b for b in
                    [str(latest / "fab" / "bom.csv") if rels else "",
                     str(proj / "06_build" / "fab" / "bom.csv"),
                     str(proj / "06_build" / "fab" / "bom_jlc.csv")]
                    if b and Path(b).exists()), None)
    if not cjs or not fab_bom:
        rows.append(("M-BOM", "N-A", "no circuit.json source or no fab BOM"))
    else:
        try:
            sys.path.insert(0, str(jlc_scripts))
            import bom_source_check as _bsc
            refdes_code = _bsc.refdes_codes_from_circuit(cjs[0])
            vendored = _bsc.vendored_primary_codes(proj / "02_parts")
            probs = _bsc.check(_bsc.read_bom(fab_bom), refdes_code, vendored)
            grade("M-BOM", not probs,
                  f"{Path(fab_bom).parent.parent.name}/fab/bom.csv: "
                  f"every LCSC == source ({sum(1 for v in refdes_code.values() if v)} coded)",
                  f"{len(probs)} BOM-vs-source defect(s): " + " || ".join(probs[:3]))
        except Exception as e:
            rows.append(("M-BOM", "FAIL", f"bom_source_check errored: {e}"))

    # M-JRNL / M-LEARN: per-stage diary + harvest sources (canon M9). Scoped
    # to commissioned projects (01_docs exists) — scratch/test trees exempt.
    docs = proj / "01_docs"
    if docs.is_dir():
        started = bool(boards) or (proj / "03_src" / "route").is_dir()
        jrn = [j for j in sorted((docs / "journal").glob("*.md"))
               if j.name != "contracts.md"] if (docs / "journal").is_dir() else []
        entries = sum(1 for j in jrn if "## " in j.read_text())
        if not started:
            rows.append(("M-JRNL", "N-A", "no board/route artifacts yet"))
        else:
            grade("M-JRNL", entries > 0,
                  f"{len(jrn)} stage journals, {entries} with entries",
                  "design is generating artifacts but 01_docs/journal/ has no "
                  "stage entries — every start/iteration/finish must journal "
                  "(canon M9)")
        if rels:
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
        entries = yaml.safe_load(adjp.read_text()) or []
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
    lines = [f"# Policy audit — {proj.name}", "",
             f"Generated by policy_audit.py; canon: design-policies.md", "",
             "| ID | Grade | Detail |", "|---|---|---|"]
    for cid, g, det in rows:
        lines.append(f"| {cid} | {g} | {det} |")
    lines += ["", "Summary: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))]
    (build / "policy_audit.md").write_text("\n".join(lines) + "\n")
    print(f"{proj.name}: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    for cid, g, det in rows:
        if g == "FAIL":
            print(f"  FAIL {cid}: {det[:110]}")
    sys.exit(1 if counts.get("FAIL") else 0)


if __name__ == "__main__":
    main()
