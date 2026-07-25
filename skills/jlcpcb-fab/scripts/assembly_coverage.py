#!/usr/bin/env python3
"""A-POP — the population set is DECLARED, not emergent.

    assembly_coverage.py TARGET [--assembly PATH] [--json OUT]

`TARGET` is a sealed release directory (`07_releases/<ver>-<date>/`, read
READ-ONLY) or a project directory (`04_kicad/` + `06_build/fab/`).

WHY THIS EXISTS. "Which parts does JLC actually place?" had no machine home.
It was an emergent property of three artifacts that nothing compared:

  * the BOARD's `exclude_from_pos_files` attributes,
  * `fab/cpl.csv` (what the machine is told to place),
  * and a PROSE `not_assembled:` sentence in the release MANIFEST.

Measured on sealed bytes (2026-07-25):

  cooksense v1.1  — 13 CPL placement rows whose BOM line carries a BLANK
    LCSC (J_TC + the twelve K_* Standex reed relays). JLC was told to place
    12 parts the MANIFEST declares not_assembled, and to source a 13th
    (J_TC) declared nowhere at all. Every gate green.
  cooksense interposer v1.0 — a blank-LCSC BOM row whose refs are ALSO on
    the CPL, no `not_assembled:` line anywhere, and a disposition that is
    PROSE telling a human to delete rows before uploading.
  crow-recorder-central-v2 v1.3 — MANIFEST `not_assembled: ... U1 (XU316
    consign)` while U1 sits ON the CPL. Consigned means YOU ship the part
    and JLC PLACES it: a sourcing class, not a population class.

INDEPENDENCE (canon M1). The population delta is computed from the BOARD's
own text and the CPL bytes — never from `export_jlc_package.py`'s filter
logic, which is what produced the CPL in the first place. `read_footprints()`
below parses the `.kicad_pcb` s-expression directly, so this checker needs no
pcbnew and shares no oracle with the exporter. (Cross-checked against pcbnew
on a real sealed board: 195/195 footprints agree on refdes, footprint name,
orientation, layer, pad count and attribute flags — 0 mismatches. That
agreement is asserted as a test, so the parser cannot rot into a second,
quieter bug.)

FAILS
  NO-ASSEMBLY-DECL       no `03_src/rules/assembly.yaml` while the board has
                         unpopulated parts — "not assembled" with no decision
                         record is a free outcome, which is the whole defect.
  UNDECLARED-UNPOPULATED a board footprint absent from the CPL that no
                         `not_assembled:` entry and no declared
                         `exempt_prefixes:` accounts for.
  DECLARED-BUT-PLACED    a ref declared not-assembled that is still ON the
                         CPL — the declaration and the machine instruction
                         disagree, and the machine wins.
  DECLARED-NOT-EXCLUDED  a declared-unpopulated ref whose board footprint
                         does NOT carry `exclude_from_pos_files` — it will
                         come back onto the CPL at the next export.
  POS-ATTR-VS-CPL        the BOARD says exclude-from-pos but the shipped CPL
                         places it anyway: the CPL predates the board.
  UNCODED-ON-CPL         a BOM row with a BLANK LCSC whose refs are on the
                         CPL (the cooksense 13) — JLC cannot source it.
  CPL-NO-BOM-ROW         a placed designator with no BOM line at all.
  BAD-REASON / NO-EVIDENCE / CONSIGN-AS-UNPOPULATED
                         schema failures in `assembly.yaml` itself.
  MANIFEST-UNDECLARED    a release with unpopulated parts and no MANIFEST
                         `not_assembled:` line.
  MANIFEST-DRIFT         the MANIFEST's `not_assembled:` set differs from
                         `assembly.yaml`'s — it is GENERATED from that file,
                         never hand-written in two places.

Exit 0 = the population set is fully declared; 1 = at least one FAIL.
Plain python3 (NO pcbnew).
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:                                   # pragma: no cover
    yaml = None

# `reason:` is a CLOSED vocabulary (03_src/rules/assembly.yaml). If none fits,
# the honest answer is that the part must be re-specified to a placeable one.
REASONS = {"not_in_catalog", "consign", "user_supplied", "dnp_by_design",
           "mechanical", "test_point"}


# ----------------------------------------------------------------- board
def _match_paren(text, i):
    """Index of the ')' closing the '(' at index i (string-aware)."""
    depth, n, in_str = 0, len(text), False
    while i < n:
        c = text[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return n - 1


def _children(text, start):
    """(head, span_text) for each DIRECT child list of the node opening at
    `start`. Nested lists are skipped wholesale, so a pad's `(at ...)` can
    never masquerade as the footprint's own `(at ...)`."""
    i, n, in_str = start + 1, len(text), False
    while i < n:
        c = text[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            i += 1
            continue
        if c == "(":
            j = _match_paren(text, i)
            m = re.match(r"\(\s*([A-Za-z_0-9]+)", text[i:j + 1])
            yield (m.group(1) if m else ""), text[i:j + 1]
            i = j + 1
            continue
        if c == ")":
            return
        i += 1


def _atoms(span):
    """Tokens of a flat s-expr `(head a "b c" 3)` -> ['head','a','b c','3']."""
    return [a or b for a, b in
            re.findall(r'"((?:[^"\\]|\\.)*)"|([^\s()"]+)', span[1:-1])]


def read_footprints(path):
    """Every footprint on a `.kicad_pcb`, parsed from the FILE TEXT.

    -> [{ref, value, fp, layer, rot, pads, attrs}] where `pads` is the set of
    pad NUMBERS and `attrs` the `(attr ...)` flag words.

    No pcbnew: this is the INDEPENDENT reading of the board (canon M1). The
    exporter reads the same facts through the pcbnew API, so a checker that
    imported pcbnew would be re-asking the exporter's own oracle.
    """
    text = Path(path).read_text()
    out = []
    for m in re.finditer(r"\(footprint\s", text):
        i = m.start()
        end = _match_paren(text, i)
        head = _atoms(text[i:min(i + 400, end + 1)] + ")")
        fpid = head[1] if len(head) > 1 else ""
        rec = {"ref": "", "value": "", "fp": fpid.split(":")[-1],
               "layer": "", "rot": 0.0, "pads": set(), "attrs": set()}
        for kind, span in _children(text, i):
            if kind == "at":
                a = _atoms(span)
                rec["rot"] = float(a[3]) if len(a) > 3 else 0.0
            elif kind == "layer" and not rec["layer"]:
                a = _atoms(span)
                rec["layer"] = a[1] if len(a) > 1 else ""
            elif kind == "attr":
                rec["attrs"] = set(_atoms(span)[1:])
            elif kind == "property":
                a = _atoms(span)
                if len(a) > 2 and a[1] == "Reference":
                    rec["ref"] = a[2]
                elif len(a) > 2 and a[1] == "Value":
                    rec["value"] = a[2]
            elif kind == "pad":
                a = _atoms(span)
                if len(a) > 1 and a[1]:
                    rec["pads"].add(a[1])
        if rec["ref"]:
            out.append(rec)
    return out


# ------------------------------------------------------------- artifacts
def read_cpl(path):
    """[(designator, rotation_deg_or_None, layer)] from a JLC CPL."""
    rows = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            ref = (r.get("Designator") or "").strip()
            if not ref:
                continue
            try:
                rot = float((r.get("Rotation") or "0").strip())
            except ValueError:
                rot = None
            rows.append((ref, rot, (r.get("Layer") or "").strip()))
    return rows


def read_bom_rows(path):
    """[(lcsc, [refs])] — BOM LINES, so a blank-code line is one finding."""
    out = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            refs = [d.strip() for d in (r.get("Designator") or "").split(",")
                    if d.strip()]
            if refs:
                out.append(((r.get("LCSC") or "").strip(), refs))
    return out


# ------------------------------------------------------------- discovery
def discover(target):
    """(board, cpl, bom, project_root) for a release dir or a project dir.
    Sealed releases are opened READ-ONLY."""
    t = Path(target).resolve()
    board = cpl = bom = None
    if (t / "fab").is_dir() and (t / "source").is_dir():          # release
        board = next(iter(sorted((t / "source").glob("*.kicad_pcb"))), None)
        for name in ("cpl.csv", "cpl_jlc.csv"):
            if (t / "fab" / name).is_file():
                cpl = t / "fab" / name
                break
        for name in ("bom.csv", "bom_jlc.csv"):
            if (t / "fab" / name).is_file():
                bom = t / "fab" / name
                break
        root = t.parent.parent                       # projects/<board>/
    else:                                                          # project
        board = next(iter(sorted((t / "04_kicad").glob("*.kicad_pcb"))), None)
        fab = t / "06_build" / "fab"
        for name in ("cpl_jlc.csv", "cpl.csv"):
            if (fab / name).is_file():
                cpl = fab / name
                break
        for name in ("bom_jlc.csv", "bom.csv"):
            if (fab / name).is_file():
                bom = fab / name
                break
        root = t
    return board, cpl, bom, root


def load_assembly(path):
    if not path or not Path(path).is_file() or not yaml:
        return {}
    return yaml.safe_load(Path(path).read_text()) or {}


_RANGE = re.compile(r"^([A-Za-z_][A-Za-z_]*?)(\d+)(?:\.\.|-)(?:[A-Za-z_]*)(\d+)$")


def expand_refs(text):
    """Refdes tokens out of a MANIFEST prose line, expanding the two range
    shapes the fleet actually writes: `K_U1..6` and `J3-J10`."""
    refs = set()
    for tok in re.findall(r"[A-Za-z_][A-Za-z_0-9]*(?:(?:\.\.|-)[A-Za-z_0-9]+)?",
                          text):
        m = _RANGE.match(tok)
        if m:
            pre, a, b = m.group(1), int(m.group(2)), int(m.group(3))
            if b >= a and b - a < 200:
                refs |= {f"{pre}{i}" for i in range(a, b + 1)}
                continue
        refs.add(tok)
    return refs


def manifest_not_assembled(path):
    """(declared_refs, raw_line) from a release MANIFEST, or (None, '') when
    the MANIFEST states nothing — absence is a DIFFERENT finding than drift."""
    if not path or not Path(path).is_file():
        return None, ""
    for line in Path(path).read_text().splitlines():
        if re.match(r"\s*not_assembled\s*:", line):
            body = line.split(":", 1)[1]
            # strip parenthetical prose ("(12x Standex DIP05-1A72-12L")
            body = re.sub(r"\([^)]*\)?", " ", body)
            return expand_refs(body), line.strip()
    return None, ""


# ------------------------------------------------------------------ gate
def check(fps, cpl_rows, bom_rows, asm, manifest_refs, have_assembly):
    """-> (fails, notes, summary). Pure; unit-testable without files."""
    fails, notes = [], []
    by_ref = {f["ref"]: f for f in fps}
    board_refs = set(by_ref)
    cpl_refs = {r[0] for r in cpl_rows}
    codes = {}
    for code, refs in bom_rows:
        for r in refs:
            codes[r] = code

    exempt = [str(p) for p in (asm.get("exempt_prefixes") or [])]
    declared, entry_of = set(), {}
    for e in (asm.get("not_assembled") or []):
        refs = [str(r) for r in (e.get("refs") or [])]
        declared |= set(refs)
        for r in refs:
            entry_of[r] = e
        if str(e.get("reason") or "") not in REASONS:
            fails.append(
                f"  BAD-REASON: not_assembled entry {refs[:4]} has reason="
                f"{e.get('reason')!r}, outside the closed vocabulary "
                f"{sorted(REASONS)} — if none fits, the part must be "
                f"re-specified to a placeable one")
        elif e.get("reason") == "consign":
            fails.append(
                f"  CONSIGN-AS-UNPOPULATED: {refs[:4]} is listed under "
                f"not_assembled with reason=consign, but a CONSIGNED part is "
                f"POPULATED — you ship it, JLC PLACES it. It belongs in "
                f"`consigned:` and stays ON the CPL (crow-recorder-central-v2 "
                f"v1.3 declared its placed U1 'not_assembled' this way)")
        if len(str(e.get("evidence") or "")) < 20:
            fails.append(
                f"  NO-EVIDENCE: not_assembled entry {refs[:4]} carries no "
                f"dated `evidence:` measurement — 'hand-solder' is a sourcing "
                f"wall you PROVE you hit (the catalog query and its result), "
                f"never a style (canon M4)")
        if not str(e.get("disposition") or "").strip():
            fails.append(
                f"  NO-EVIDENCE: not_assembled entry {refs[:4]} carries no "
                f"`disposition:` — what happens to the unplaced part is part "
                f"of the decision record")
    consigned = {str(r) for e in (asm.get("consigned") or [])
                 for r in (e.get("refs") or [])}
    both = sorted(declared & consigned)
    if both:
        fails.append(
            f"  CONSIGN-AS-UNPOPULATED: {both} appear in BOTH `consigned:` "
            f"and `not_assembled:` — consigned parts are PLACED; a ref cannot "
            f"be both populated and not")

    # ---- the core set identity: {board} - {CPL} == declared (mod exempt)
    unpopulated = sorted(board_refs - cpl_refs)
    unexplained = sorted(
        r for r in unpopulated
        if r not in declared
        and not any(r.startswith(p) for p in exempt))
    if unpopulated and not have_assembly:
        fails.append(
            f"  NO-ASSEMBLY-DECL: {len(unpopulated)} board footprint(s) are "
            f"absent from the CPL and there is no 03_src/rules/assembly.yaml "
            f"declaring who is placed and why not — an unpopulated part is a "
            f"DEFECT WITH A DECISION RECORD, never a free outcome")
    if unexplained:
        fails.append(
            f"  UNDECLARED-UNPOPULATED: {len(unexplained)} board footprint(s) "
            f"absent from the CPL with no assembly.yaml entry and no declared "
            f"exempt prefix: {', '.join(unexplained[:24])}"
            + (" ..." if len(unexplained) > 24 else ""))
    placed_but_declared = sorted(declared & cpl_refs)
    if placed_but_declared:
        fails.append(
            f"  DECLARED-BUT-PLACED: {len(placed_but_declared)} ref(s) are "
            f"declared not_assembled yet appear ON the CPL — JLC is being "
            f"told to place them: {', '.join(placed_but_declared[:24])}")
    for r in sorted(declared & board_refs):
        if "exclude_from_pos_files" not in by_ref[r]["attrs"]:
            fails.append(
                f"  DECLARED-NOT-EXCLUDED: {r} is declared not_assembled but "
                f"its board footprint has no `exclude_from_pos_files` "
                f"attribute — the next export puts it straight back on the CPL")
    for r in sorted(declared - board_refs):
        fails.append(
            f"  UNDECLARED-UNPOPULATED: assembly.yaml declares {r} "
            f"not_assembled but no such footprint exists on the board")

    # ---- board attribute vs the CPL actually shipped
    attr_but_placed = sorted(
        r for r in cpl_refs
        if r in by_ref and "exclude_from_pos_files" in by_ref[r]["attrs"])
    if attr_but_placed:
        fails.append(
            f"  POS-ATTR-VS-CPL: {len(attr_but_placed)} ref(s) carry "
            f"`exclude_from_pos_files` on the BOARD yet are placed by the "
            f"shipped CPL — the CPL does not match the board it claims to "
            f"come from: {', '.join(attr_but_placed[:24])}")

    # ---- a placed part JLC cannot source
    uncoded_placed = sorted({r for code, refs in bom_rows if not code
                             for r in refs} & cpl_refs)
    if uncoded_placed:
        fails.append(
            f"  UNCODED-ON-CPL: {len(uncoded_placed)} ref(s) have a BLANK "
            f"LCSC on their BOM line yet appear on the CPL — JLC is told to "
            f"place a part it has no code to source: "
            f"{', '.join(uncoded_placed)}")
    no_row = sorted(cpl_refs - set(codes))
    if no_row:
        fails.append(
            f"  CPL-NO-BOM-ROW: {len(no_row)} placed designator(s) have no BOM "
            f"line at all: {', '.join(no_row[:24])}")

    # ---- the MANIFEST line is GENERATED from assembly.yaml, not re-typed
    if manifest_refs is None:
        if unpopulated:
            fails.append(
                "  MANIFEST-UNDECLARED: the release MANIFEST carries no "
                "`not_assembled:` line while the board has unpopulated parts "
                "— the population decision must be visible in the order "
                "paperwork")
    else:
        stray = sorted(manifest_refs & cpl_refs)
        if stray:
            fails.append(
                f"  DECLARED-BUT-PLACED: the MANIFEST's not_assembled: line "
                f"names {len(stray)} ref(s) that are ON the CPL: "
                f"{', '.join(stray[:24])}")
        if have_assembly:
            miss = sorted(declared - manifest_refs)
            extra = sorted(manifest_refs - declared - cpl_refs)
            if miss or extra:
                fails.append(
                    f"  MANIFEST-DRIFT: the MANIFEST's not_assembled: set "
                    f"disagrees with assembly.yaml (missing from MANIFEST: "
                    f"{miss[:12]}; not in assembly.yaml: {extra[:12]}) — the "
                    f"MANIFEST line is GENERATED from assembly.yaml, never "
                    f"hand-written in two places")

    hist = {}
    for _ref, _rot, layer in cpl_rows:
        hist[layer or "?"] = hist.get(layer or "?", 0) + 1
    summary = {"board": len(board_refs), "cpl": len(cpl_refs),
               "unpopulated": len(unpopulated), "declared": len(declared),
               "consigned": len(consigned), "exempt_prefixes": exempt,
               "sides": hist, "unexplained": unexplained}
    return fails, notes, summary


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="A-POP: the population set is DECLARED, not emergent")
    ap.add_argument("target")
    ap.add_argument("--assembly", default="")
    ap.add_argument("--board", default="")
    ap.add_argument("--cpl", default="")
    ap.add_argument("--bom", default="")
    ap.add_argument("--manifest", default="")
    ap.add_argument("--json", default="", metavar="OUT")
    # RED-VERIFY hooks (tests only): neuter ONE family of findings so a
    # known-bad fixture is shown to pass when — and only when — that family is
    # disabled, proving the finding came from that check and nothing else.
    ap.add_argument("--_disable-setid", action="store_true",
                    help="neuter the board-vs-CPL set identity checks")
    ap.add_argument("--_disable-uncoded", action="store_true")
    args = ap.parse_args(argv)

    board, cpl, bom, root = discover(args.target)
    board = Path(args.board) if args.board else board
    cpl = Path(args.cpl) if args.cpl else cpl
    bom = Path(args.bom) if args.bom else bom
    asm_p = (Path(args.assembly) if args.assembly
             else root / "03_src" / "rules" / "assembly.yaml")
    man_p = (Path(args.manifest) if args.manifest
             else Path(args.target) / "MANIFEST.txt")

    print(f"== A-POP assembly_coverage: {Path(args.target).name} ==")
    if not board or not Path(board).is_file():
        print("FATAL: no .kicad_pcb found (pass --board)", file=sys.stderr)
        return 2
    if not cpl or not Path(cpl).is_file():
        print("FATAL: no cpl.csv found (pass --cpl)", file=sys.stderr)
        return 2
    if not bom or not Path(bom).is_file():
        print("FATAL: no bom.csv found (pass --bom)", file=sys.stderr)
        return 2

    asm = load_assembly(asm_p)
    fails, notes, summary = check(
        read_footprints(board), read_cpl(cpl), read_bom_rows(bom), asm,
        manifest_not_assembled(man_p)[0], Path(asm_p).is_file())

    if args._disable_setid:
        fails = [f for f in fails
                 if not any(k in f for k in ("UNDECLARED-UNPOPULATED",
                                             "DECLARED-BUT-PLACED",
                                             "POS-ATTR-VS-CPL",
                                             "NO-ASSEMBLY-DECL"))]
    if args._disable_uncoded:
        fails = [f for f in fails if "UNCODED-ON-CPL" not in f]

    print(f"  board={summary['board']} footprints, cpl={summary['cpl']} "
          f"placements, unpopulated={summary['unpopulated']} "
          f"(declared={summary['declared']}, consigned={summary['consigned']}, "
          f"exempt_prefixes={summary['exempt_prefixes']})")
    print("  placement histogram: "
          + ", ".join(f"{k}={v}" for k, v in sorted(summary["sides"].items())))
    for n in notes:
        print(n)
    for f in fails:
        print(f)
    if args.json:
        Path(args.json).write_text(json.dumps(
            {"target": str(args.target), "summary": summary, "fails": fails},
            indent=1) + "\n")
    if fails:
        print(f"A-POP: FAIL ({len(fails)} finding(s))")
        return 1
    print("A-POP: PASS (every unpopulated part is declared with evidence)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
