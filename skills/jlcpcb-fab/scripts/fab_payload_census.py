#!/usr/bin/env python3
"""fab_payload_census.py — canon F-*: grade the bytes that ACTUALLY SHIP.

    fab_payload_census.py <release-dir> [--json OUT]

WHY THIS EXISTS. usb-hub-3s-v3 shipped THREE sealed releases (v1.6, v1.7, v1.8)
whose gerbers contain NO COPPER POUR ON ANY LAYER — 51 zones on the board, 0
`filled_polygon` blocks in the saved file, G36 region count 0 on F_Cu, In1_Cu,
In2_Cu and B_Cu. Missing copper: 44287.91 mm2. Every gate was green.

The reason every gate was green is canon M6, which this script exists to enforce:

    `kicad-cli pcb drc --refill-zones` REFILLS THE ZONES IN MEMORY. It therefore
    returns 0/0/0 on a board whose SAVED file has no fill at all. The MANIFEST's
    stranded-copper check refilled in memory too. Nothing in this repository has
    ever opened the zip that gets uploaded and turned into copper.

The fab payload was a HASHED artifact, never a GRADED one. A sha256 proves the
bytes did not change in transit; it says nothing about whether they are right.

THE DIAGNOSTIC THAT NAMES IT. In the v1.8 zip, `In1_Cu.g1` and `In2_Cu.g2` are
byte-identical apart from `%TF.FileFunction,Copper,L2` vs `L3` — 18921 bytes
each. That is impossible for an L2 GND plane and an L3 VIN plane, and it is
explained by both files containing ONLY the layer-independent PTH flash list.
Two different planes cannot serialise to the same bytes. F-IDENT is that check.

WHAT MAKES THIS AN INDEPENDENT CHANNEL (canon M1). The board side is parsed from
`.kicad_pcb` TEXT and the payload side from the GERBER TEXT. Neither uses pcbnew,
so this gate cannot inherit the in-memory-refill blindness that produced the
defect: pcbnew is the tool whose behaviour is under test.

COVERAGE IS PART OF THE VERDICT (canon G-COVER). Every check reports
`N graded / M total`. A layer this parser cannot classify is a FAIL, never a
skip — `bom_source_check`'s row_kind silently dropped 12 of 26 rows while
printing PASS, and that is the failure mode being avoided here.
"""
import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

#: gerber filename stem suffix -> KiCad board layer name.
LAYER_FROM_FILE = {"F_Cu": "F.Cu", "B_Cu": "B.Cu"}
for _i in range(1, 31):
    LAYER_FROM_FILE[f"In{_i}_Cu"] = f"In{_i}.Cu"

FILEFUNC_RE = re.compile(r"%TF\.FileFunction,([^*]*)\*%")


def sexp_blocks(text, head):
    """Yield the full balanced-paren source of every `(head ...)` block.

    A regex cannot do this: zones contain nested `(pts (xy ...))` lists, and a
    non-greedy match stops at the first inner `)`. Getting this wrong would
    undercount zones, which would make the gate agree with a bare board.
    """
    tok = f"({head}"
    i = 0
    while True:
        i = text.find(tok, i)
        if i < 0:
            return
        # TOKEN boundary, not prefix. `(zone` prefix-matches `(zone_connect 2)`
        # and on crow-recorder-central-v2 that admitted 64 phantom blocks.
        # HONESTY NOTE: this guard is correct but NOT load-bearing — RED
        # verification was attempted and did not go red, because a
        # `(zone_connect 2)` block has no `(layers ...)` and is already dropped
        # downstream. Kept as hygiene; see t1_fab_payload.py for why it is
        # labelled a regression guard rather than a known-bad.
        nxt = text[i + len(tok):i + len(tok) + 1]
        if nxt not in ("", " ", "\t", "\n", "\r", "("):
            i += 1
            continue
        depth, j, in_str = 0, i, False
        while j < len(text):
            ch = text[j]
            if ch == '"' and text[j - 1] != "\\":
                in_str = not in_str
            elif not in_str:
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        break
            j += 1
        yield text[i:j + 1]
        i = j + 1


def board_zone_census(pcb_text):
    """copper layer -> (POUR zone count, filled_polygon count), saved file only.

    KEEPOUT / RULE-AREA ZONES ARE EXCLUDED, and that distinction is the whole
    correctness of this gate. A rule area is serialised as a `(zone ...)` with a
    `(keepout ...)` block and has NO FILL BY DESIGN. Counting them as pours made
    a first draft of this checker report crow-recorder-central-v2's In2.Cu and
    In3.Cu as shipping bare — they carry 0 pours and 6 keepouts each, so 0 G36
    regions is CORRECT. Measuring "zones" when the property is "pour zones" is
    the same adjacent-property error that produced 7 phantom stranded islands.
    """
    census = {}
    for blk in sexp_blocks(pcb_text, "zone"):
        if "(keepout" in blk:
            continue                       # rule area: no fill is correct
        m = re.search(r'\(layers?\s+((?:"[^"]+"\s*)+)\)', blk)
        if not m:
            continue
        fills = len(re.findall(r"\(filled_polygon\b", blk))
        for n in re.findall(r'"([^"]+)"', m.group(1)):
            if not n.endswith(".Cu"):
                continue
            z, f = census.get(n, (0, 0))
            census[n] = (z + 1, f + fills)
    return census


def payload_census(zip_path):
    """(layer -> G36 count, layer -> sha-ish size, unclassified filenames)."""
    g36, blobs, unknown = {}, {}, []
    with zipfile.ZipFile(zip_path) as z:
        for name in sorted(z.namelist()):
            raw = z.read(name)
            body = raw.decode("utf8", "replace")
            m = FILEFUNC_RE.search(body)
            func = m.group(1) if m else ""
            if not func.startswith("Copper"):
                continue                   # mask/paste/silk/profile: not our property
            stem = Path(name).stem
            layer = None
            for suf, lay in LAYER_FROM_FILE.items():
                if stem.endswith(suf):
                    layer = lay
                    break
            if layer is None:
                unknown.append(f"{name} ({func})")
                continue
            g36[layer] = body.count("G36*")
            blobs[layer] = (len(raw), func, raw)
    return g36, blobs, unknown


def load_pourless(rel, explicit):
    """The `pourless:` declaration, or None.

    A board with no copper pour is legitimate — the cooksense interposer forbids
    a plane in the keypad zone (BRIEF S4/S7) and correctly ships 0 zones. But a
    DELIBERATELY pourless board and a board that LOST its zones are the same
    bytes, so the design must say which it is. Per canon, a waiver needs
    evidence rather than rationale: a bare `pourless: true` is refused and the
    declaration must carry a reason.
    """
    cands = [Path(explicit)] if explicit else [
        rel / "source" / "assembly.yaml",
        rel.parent.parent / "03_src" / "rules" / "assembly.yaml",
    ]
    for p in cands:
        if not p.is_file():
            continue
        try:
            import yaml
            d = yaml.safe_load(p.read_text()) or {}
        except Exception:
            continue
        v = d.get("pourless")
        if v is None:
            continue
        if isinstance(v, str) and v.strip():
            return (str(p), v.strip())
        if isinstance(v, dict) and str(v.get("reason", "")).strip():
            return (str(p), str(v["reason"]).strip())
        return (str(p), None)              # declared, but with no reason
    return None


def check(release_dir, assembly=None):
    rel = Path(release_dir)
    fab = rel / "fab"
    src = rel / "source"
    zips = sorted(fab.glob("*_gerbers.zip"))
    pcbs = sorted(src.glob("*.kicad_pcb"))
    r = {"release": str(rel), "fails": [], "oks": [], "coverage": {}}

    if not zips:
        r["fails"].append(f"F-SRC: no *_gerbers.zip in {fab}")
        return r
    if not pcbs:
        r["fails"].append(f"F-SRC: no *.kicad_pcb in {src}")
        return r

    board = board_zone_census(pcbs[0].read_text())
    g36, blobs, unknown = payload_census(zips[0])

    for u in unknown:
        r["fails"].append(f"F-LAYER: copper gerber this parser cannot classify: {u}")

    # ---- F-POUR: a copper layer carrying zones MUST carry regions in the zip.
    graded = 0
    for layer, (nz, nfill) in sorted(board.items()):
        if layer not in g36:
            r["fails"].append(
                f"F-POUR {layer}: board declares {nz} zone(s) but the payload "
                f"has no gerber for this layer")
            continue
        graded += 1
        n = g36[layer]
        if n == 0:
            r["fails"].append(
                f"F-POUR {layer}: board declares {nz} zone(s) "
                f"({nfill} filled_polygon in the saved file) but the SHIPPED "
                f"gerber has 0 G36 regions — this layer ships with NO POUR")
        else:
            r["oks"].append(f"F-POUR {layer} {nz} zone(s) -> {n} G36 region(s)")
    r["coverage"]["F-POUR"] = f"{graded}/{len(board)} zone-bearing copper layers"

    # A copper layer with regions but no zone is equally wrong, in reverse.
    for layer, n in sorted(g36.items()):
        if n and layer not in board:
            r["fails"].append(
                f"F-POUR {layer}: payload has {n} G36 region(s) but the board "
                f"declares no zone on this layer")

    # ---- F-IDENT: two different copper functions cannot serialise identically.
    # Compare with the FileFunction line REMOVED. The v1.8 defect is two files
    # whose only difference IS that line (`Copper,L2` vs `Copper,L3`, 18921 B
    # each) — comparing raw bytes finds them "distinct" and misses the whole
    # point. The property is identical CONTENT under different declared function.
    seen = {}
    for layer, (size, func, raw) in sorted(blobs.items()):
        key = FILEFUNC_RE.sub("", raw.decode("utf8", "replace"))
        if key in seen:
            other_layer, other_func = seen[key]
            r["fails"].append(
                f"F-IDENT: {layer} ({func}) and {other_layer} ({other_func}) "
                f"are BYTE-IDENTICAL at {size}B — two different copper layers "
                f"cannot have the same content; this is the signature of a "
                f"payload carrying only the layer-independent flash list")
        else:
            seen[key] = (layer, func)
    r["coverage"]["F-IDENT"] = f"{len(blobs)}/{len(blobs)} copper gerbers compared"
    if len(blobs) and not any(f.startswith("F-IDENT") for f in r["fails"]):
        r["oks"].append(f"F-IDENT {len(blobs)} copper gerbers all distinct")

    if not board:
        decl = load_pourless(rel, assembly)
        if decl and decl[1]:
            r["oks"].append(
                f"F-POUR pourless by declaration ({Path(decl[0]).name}): {decl[1]}")
        elif decl:
            r["fails"].append(
                f"F-POUR: `pourless:` is declared in {decl[0]} but carries NO "
                f"REASON. A waiver needs evidence, not assertion — state why "
                f"this board has no pour.")
        else:
            r["fails"].append(
                "F-POUR: the board declares NO copper zone at all, and nothing "
                "declares it pourless. A deliberately pourless board and a "
                "board that LOST its zones are the same bytes — add "
                "`pourless: \"<reason>\"` to assembly.yaml if this is intended.")
    return r


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("release_dir")
    ap.add_argument("--json", default=None)
    ap.add_argument("--assembly", default=None,
                    help="assembly.yaml carrying a `pourless:` declaration")
    a = ap.parse_args(argv)

    r = check(a.release_dir, a.assembly)
    if a.json:
        Path(a.json).write_text(json.dumps(r, indent=2, default=str) + "\n")

    for k, v in sorted(r["coverage"].items()):
        print(f"  coverage {k}: {v}")
    for o in r["oks"]:
        print(f"  ok   {o}")
    for f in r["fails"]:
        print(f"  FAIL {f}")

    if r["fails"]:
        print(f"F-PAYLOAD FAIL: {len(r['fails'])} finding(s), "
              f"{len(r['oks'])} ok")
        return 1
    print(f"F-PAYLOAD OK: {len(r['oks'])} check(s) passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
